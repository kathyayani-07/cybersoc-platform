from __future__ import annotations

from fastapi import Cookie, Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    create_refresh_session,
    get_current_user,
    get_optional_current_user,
    require_roles,
    revoke_refresh_session,
    rotate_refresh_session,
)
from app.config import settings
from app.crud import (
    add_investigation_note,
    analyze_and_save_incident,
    compute_dashboard_metrics,
    compute_incident_reports,
    create_incident,
    create_user,
    ensure_bootstrap_admin,
    ensure_seed_data,
    export_incidents_csv,
    get_incident_by_id,
    get_incidents,
    list_audit_logs,
    list_users,
    log_action,
    update_incident,
    update_user_role,
    authenticate_user,
)
from app.database import Base, SessionLocal, engine, get_db
from app.models import Incident, User
from app.time_utils import utc_isoformat
from app.schemas import (
    AnalysisRequest,
    AnalysisResult,
    IncidentCreate,
    IncidentOut,
    IncidentUpdate,
    LoginRequest,
    Token,
    UserCreate,
    UserOut,
)

Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    if settings.seed_demo_data:
        ensure_seed_data(db)
    bootstrap_admin_settings = (
        settings.bootstrap_admin_username,
        settings.bootstrap_admin_email,
        settings.bootstrap_admin_password,
    )
    if any(bootstrap_admin_settings) and not all(bootstrap_admin_settings):
        raise RuntimeError("Set all bootstrap administrator settings or leave all of them empty.")
    if all(bootstrap_admin_settings):
        ensure_bootstrap_admin(db, *bootstrap_admin_settings)

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="cyber_refresh",
        value=refresh_token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/auth",
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}


@app.post("/api/auth/register", response_model=Token)
def register_user(payload: UserCreate, response: Response, db: Session = Depends(get_db)):
    user = create_user(db, payload.model_dump(exclude={"role"}) | {"role": "viewer"})
    access_token = create_access_token({"sub": user.username})
    set_refresh_cookie(response, create_refresh_session(db, user))
    log_action(db, user, "user_registered", "Viewer account registered")
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@app.post("/api/auth/login", response_model=Token)
def login_user(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token({"sub": user.username})
    set_refresh_cookie(response, create_refresh_session(db, user))
    log_action(db, user, "user_login", "User logged in")
    return {"access_token": token, "token_type": "bearer", "user": user}


@app.post("/api/auth/refresh", response_model=Token)
def refresh_authentication(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias="cyber_refresh"),
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    if refresh_token:
        rotated = rotate_refresh_session(db, refresh_token)
        if rotated is None:
            expired = JSONResponse(
                status_code=401,
                content={"detail": "Session expired. Please log in again."},
            )
            expired.delete_cookie("cyber_refresh", path="/api/auth", samesite="lax")
            return expired
        refresh_token, user = rotated
    elif current_user:
        user = current_user
        refresh_token = create_refresh_session(db, user)
    else:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")

    set_refresh_cookie(response, refresh_token)
    return {
        "access_token": create_access_token({"sub": user.username}),
        "token_type": "bearer",
        "user": user,
    }


@app.post("/api/auth/logout", status_code=204)
def logout_user(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias="cyber_refresh"),
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    session_user = revoke_refresh_session(db, refresh_token) if refresh_token else None
    audit_user = session_user or current_user
    if audit_user:
        log_action(db, audit_user, "user_logout", "User logged out")
    response.delete_cookie("cyber_refresh", path="/api/auth", samesite="lax")
    response.status_code = 204
    return response


@app.get("/api/auth/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/api/dashboard/overview")
def dashboard_overview(db: Session = Depends(get_db)):
    return compute_dashboard_metrics(db)


def _serialize_incident_timestamps(incident: Incident) -> dict:
    data = {
        column.name: getattr(incident, column.name)
        for column in incident.__table__.columns
    }
    for field in ("detection_timestamp", "last_updated", "resolution_timestamp"):
        data[field] = utc_isoformat(data[field])
    return data


@app.get("/api/incidents")
def list_incidents(
    db: Session = Depends(get_db),
    query: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None),
    sort: str = "-id",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=10),
):
    result = get_incidents(db, query=query, severity=severity, status=status, sort=sort, page=page, page_size=page_size)
    result["items"] = [_serialize_incident_timestamps(item) for item in result["items"]]
    return result


@app.post("/api/incidents", response_model=IncidentOut)
def create_incident_route(
    payload: IncidentCreate,
    current_user: User = Depends(require_roles("admin", "security_analyst", "incident_responder")),
    db: Session = Depends(get_db),
):
    incident = create_incident(db, payload.model_dump(), current_user)
    return incident


@app.get("/api/incidents/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    return get_incident_by_id(db, incident_id)


@app.put("/api/incidents/{incident_id}", response_model=IncidentOut)
def update_incident_route(
    incident_id: int,
    payload: IncidentUpdate,
    current_user: User = Depends(require_roles("admin", "security_analyst", "incident_responder")),
    db: Session = Depends(get_db),
):
    return update_incident(db, incident_id, payload.model_dump(exclude_unset=True), current_user)


@app.post("/api/incidents/{incident_id}/notes")
def add_note(
    incident_id: int,
    note: str,
    current_user: User = Depends(require_roles("admin", "security_analyst", "incident_responder")),
    db: Session = Depends(get_db),
):
    return {"incident": add_investigation_note(db, incident_id, note, current_user)}


@app.get("/api/alerts")
def get_alerts(db: Session = Depends(get_db)):
    from app.models import Incident

    incidents = db.query(Incident).order_by(Incident.last_updated.desc()).limit(20).all()
    return {"items": [{
        "id": item.id,
        "title": item.title,
        "severity": item.severity,
        "status": item.status,
        "last_updated": utc_isoformat(item.last_updated),
    } for item in incidents]}


@app.post("/api/ai/analyze", response_model=AnalysisResult)
def run_ai_analysis(payload: AnalysisRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return analyze_and_save_incident(db, payload.description, payload.log_text, current_user, payload.incident_id)


@app.get("/api/reports")
def reports(db: Session = Depends(get_db)):
    result = compute_incident_reports(db)
    result["items"] = [_serialize_incident_timestamps(item) for item in result["items"]]
    return result


@app.get("/api/admin/users")
def admin_users(current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return {"items": list_users(db)}


@app.put("/api/admin/users/{user_id}/role")
def update_role(user_id: int, role: str, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    user = update_user_role(db, user_id, role)
    log_action(db, current_user, "updated_user_role", f"Changed role for {user.username} to {role}")
    return {"status": "ok", "user": UserOut.model_validate(user)}


@app.get("/api/admin/audit-logs")
def audit_logs(current_user: User = Depends(require_roles("admin", "security_analyst")), db: Session = Depends(get_db)):
    return {
        "items": [
            {
                "id": item.id,
                "user_id": item.user_id,
                "action": item.action,
                "details": item.details,
                "created_at": utc_isoformat(item.created_at),
            }
            for item in list_audit_logs(db)
        ]
    }


@app.get("/api/incidents/export/csv")
def export_csv(current_user: User = Depends(require_roles("admin", "security_analyst", "incident_responder")), db: Session = Depends(get_db)):
    csv_text = export_incidents_csv(db)
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="incident_export.csv"'},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
