import csv
import io
import json
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.ai_service import analyze_incident
from app.auth import get_password_hash, verify_password
from app.models import AIAnalysis, AuditLog, Incident, User
from app.time_utils import utc_isoformat, utc_now_naive

ALLOWED_ROLES = {"admin", "security_analyst", "incident_responder", "viewer"}

def ensure_seed_data(db: Session):
    default_users = [
        {"username": "admin", "email": "admin@cybersoc.io", "full_name": "Platform Admin", "password": "Admin123!", "role": "admin"},
        {"username": "analyst", "email": "analyst@cybersoc.io", "full_name": "Security Analyst", "password": "Analyst123!", "role": "security_analyst"},
        {"username": "responder", "email": "responder@cybersoc.io", "full_name": "Incident Responder", "password": "Responder123!", "role": "incident_responder"},
        {"username": "viewer", "email": "viewer@cybersoc.io", "full_name": "Platform Viewer", "password": "Viewer123!", "role": "viewer"},
    ]
    for account in default_users:
        if not db.query(User).filter(User.username == account["username"]).first():
            user = User(
                username=account["username"],
                email=account["email"],
                full_name=account["full_name"],
                hashed_password=get_password_hash(account["password"]),
                role=account["role"],
            )
            db.add(user)
    db.commit()


def ensure_bootstrap_admin(db: Session, username: str, email: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if user:
        if user.email != email or user.role != "admin":
            raise RuntimeError("The configured bootstrap administrator conflicts with an existing user.")
        return user

    if db.query(User).filter(User.email == email).first():
        raise RuntimeError("The configured bootstrap administrator email is already in use.")

    return create_user(
        db,
        {
            "username": username,
            "email": email,
            "password": password,
            "role": "admin",
        },
    )


def log_action(db: Session, user: User | None, action: str, details: str = ""):
    db.add(AuditLog(user_id=user.id if user else None, action=action, details=details))
    db.commit()


def create_user(db: Session, payload: dict) -> User:
    if payload["role"] not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role selected.")
    if db.query(User).filter(User.username == payload["username"]).first():
        raise HTTPException(status_code=400, detail="Username already exists.")
    if db.query(User).filter(User.email == payload["email"]).first():
        raise HTTPException(status_code=400, detail="Email already registered.")
    user = User(
        username=payload["username"],
        email=payload["email"],
        full_name=payload.get("full_name"),
        hashed_password=get_password_hash(payload["password"]),
        role=payload["role"],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active or not verify_password(password, user.hashed_password):
        return None
    return user


def create_incident(db: Session, payload: dict, creator: User):
    incident = Incident(
        title=payload["title"],
        description=payload["description"],
        category=payload["category"],
        severity=payload.get("severity", "Medium"),
        priority=payload.get("priority", "Medium"),
        status=payload.get("status", "New"),
        detection_source=payload.get("detection_source", "Manual"),
        affected_asset=payload.get("affected_asset", "Unknown"),
        reported_by=payload.get("reported_by", "System"),
        assigned_analyst=payload.get("assigned_analyst"),
        detection_timestamp=payload.get("detection_timestamp") or utc_now_naive(),
        last_updated=payload.get("last_updated") or utc_now_naive(),
        resolution_timestamp=payload.get("resolution_timestamp"),
        investigation_notes=payload.get("investigation_notes") or "",
        evidence_references=payload.get("evidence_references") or "",
        recommended_response_actions=payload.get("recommended_response_actions") or "",
        owner_id=creator.id,
        created_by=creator.id,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    log_action(db, creator, "created_incident", f"Incident #{incident.id} created")
    return incident


def get_incidents(db: Session, query: str | None = None, severity: str | None = None, status: str | None = None, sort: str = "-id", page: int = 1, page_size: int = 10):
    items = db.query(Incident)
    if query:
        search = f"%{query}%"
        items = items.filter(or_(Incident.title.ilike(search), Incident.description.ilike(search), Incident.affected_asset.ilike(search)))
    if severity:
        items = items.filter(Incident.severity == severity)
    if status:
        items = items.filter(Incident.status == status)
    if sort == "-id":
        items = items.order_by(Incident.id.desc())
    elif sort == "id":
        items = items.order_by(Incident.id.asc())
    elif sort == "severity":
        items = items.order_by(Incident.severity.desc())
    else:
        items = items.order_by(Incident.last_updated.desc())

    total = items.count()
    page_items = items.offset((page - 1) * page_size).limit(page_size).all()
    return {"items": page_items, "page": page, "page_size": page_size, "total": total}


def compute_incident_reports(db: Session):
    incidents = db.query(Incident).order_by(Incident.id.desc()).all()

    def counts_by(field: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for incident in incidents:
            value = getattr(incident, field) or "Unspecified"
            counts[value] = counts.get(value, 0) + 1
        return counts

    return {
        "total_incidents": len(incidents),
        "status_counts": counts_by("status"),
        "severity_counts": counts_by("severity"),
        "priority_counts": counts_by("priority"),
        "items": incidents,
    }


def get_incident_by_id(db: Session, incident_id: int):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return incident



def update_incident(db: Session, incident_id: int, payload: dict, user: User):
    incident = get_incident_by_id(db, incident_id)

    if user.role == "viewer":
        raise HTTPException(status_code=403, detail="Viewer role cannot modify incidents.")

    old_status = incident.status
    old_assigned_analyst = incident.assigned_analyst
    old_values = {field: getattr(incident, field) for field in payload if hasattr(incident, field)}

    for field, value in payload.items():
        if value is not None and hasattr(incident, field):
            setattr(incident, field, value)

    # Save the resolution timestamp when status becomes Resolved
    if incident.status == "Resolved" and old_status != "Resolved":
        if not incident.resolution_timestamp:
            incident.resolution_timestamp = utc_now_naive()

    # Clear the timestamp if the incident is reopened
    elif incident.status != "Resolved" and old_status == "Resolved":
        incident.resolution_timestamp = None

    incident.last_updated = utc_now_naive()

    db.commit()
    db.refresh(incident)

    if incident.assigned_analyst != old_assigned_analyst:
        assignee = incident.assigned_analyst or "Unassigned"
        log_action(db, user, "assigned_incident", f"Incident #{incident.id} assigned to {assignee}")
    if incident.status != old_status:
        log_action(
            db,
            user,
            "resolved_incident" if incident.status == "Resolved" else "changed_incident_status",
            f"Incident #{incident.id} status changed from {old_status} to {incident.status}",
        )
    if any(getattr(incident, field) != value for field, value in old_values.items()):
        log_action(db, user, "updated_incident", f"Incident #{incident.id} details were updated")

    return incident


def add_investigation_note(db: Session, incident_id: int, note: str, user: User):
    incident = get_incident_by_id(db, incident_id)
    if user.role == "viewer":
        raise HTTPException(status_code=403, detail="Viewer role cannot modify incidents.")
    if incident.investigation_notes:
        incident.investigation_notes += "\n"
    incident.investigation_notes += f"[{utc_isoformat(utc_now_naive())}] {user.username}: {note}"
    incident.last_updated = utc_now_naive()
    db.commit()
    db.refresh(incident)
    log_action(db, user, "added_note", f"Incident #{incident.id} note added")
    return incident


def delete_incident(db: Session, incident_id: int, user: User):
    incident = get_incident_by_id(db, incident_id)
    if user.role == "viewer":
        raise HTTPException(status_code=403, detail="Viewer role cannot delete incidents.")
    db.delete(incident)
    db.commit()
    log_action(db, user, "deleted_incident", f"Incident #{incident_id} was removed")
    return True


def compute_dashboard_metrics(db: Session):
    total = db.query(func.count(Incident.id)).scalar() or 0
    open_count = db.query(func.count(Incident.id)).filter(Incident.status != "Resolved", Incident.status != "Closed").scalar() or 0
    critical = db.query(func.count(Incident.id)).filter(Incident.severity == "Critical").scalar() or 0
    high = db.query(func.count(Incident.id)).filter(Incident.severity == "High").scalar() or 0
    under_investigation = db.query(func.count(Incident.id)).filter(Incident.status == "Investigating").scalar() or 0
    resolved = db.query(func.count(Incident.id)).filter(Incident.status == "Resolved").scalar() or 0

    recent_alerts = db.query(Incident).order_by(Incident.last_updated.desc()).limit(5).all()
    recent_activity = db.query(Incident).order_by(Incident.last_updated.desc()).limit(6).all()
    trend = db.query(Incident).filter(Incident.detection_timestamp.isnot(None)).all()

    severity_distribution = {
        "Critical": critical,
        "High": high,
        "Medium": db.query(func.count(Incident.id)).filter(Incident.severity == "Medium").scalar() or 0,
        "Low": db.query(func.count(Incident.id)).filter(Incident.severity == "Low").scalar() or 0,
    }
    status_distribution = {
        "New": db.query(func.count(Incident.id)).filter(Incident.status == "New").scalar() or 0,
        "Acknowledged": db.query(func.count(Incident.id)).filter(Incident.status == "Acknowledged").scalar() or 0,
        "Investigating": db.query(func.count(Incident.id)).filter(Incident.status == "Investigating").scalar() or 0,
        "Contained": db.query(func.count(Incident.id)).filter(Incident.status == "Contained").scalar() or 0,
        "Resolved": db.query(func.count(Incident.id)).filter(Incident.status == "Resolved").scalar() or 0,
        "Closed": db.query(func.count(Incident.id)).filter(Incident.status == "Closed").scalar() or 0,
    }

    incidents = db.query(Incident).all()
    acknowledged = [i for i in incidents if i.detection_timestamp and i.last_updated]
    if acknowledged:
        mean_ack = sum((i.last_updated - i.detection_timestamp).total_seconds() / 3600 for i in acknowledged if i.last_updated and i.detection_timestamp) / len(acknowledged)
        mean_resolve = sum((i.resolution_timestamp - i.detection_timestamp).total_seconds() / 3600 for i in incidents if i.resolution_timestamp and i.detection_timestamp) / max(1, len([i for i in incidents if i.resolution_timestamp and i.detection_timestamp]))
    else:
        mean_ack = 0
        mean_resolve = 0

    return {
        "total_incidents": total,
        "open_incidents": open_count,
        "critical_incidents": critical,
        "high_severity_incidents": high,
        "under_investigation": under_investigation,
        "resolved_incidents": resolved,
        "recent_alerts": [
            {"id": item.id, "title": item.title, "severity": item.severity, "status": item.status, "last_updated": utc_isoformat(item.last_updated)}
            for item in recent_alerts
        ],
        "recent_activity": [
            {"id": item.id, "title": item.title, "status": item.status, "severity": item.severity, "last_updated": utc_isoformat(item.last_updated)}
            for item in recent_activity
        ],
        "incident_trend": [
            {
                "date": (
                    item.detection_timestamp.replace(tzinfo=ZoneInfo("UTC"))
                    .astimezone(ZoneInfo("Asia/Kolkata"))
                    .strftime("%Y-%m-%d")
                    if item.detection_timestamp
                    else "unknown"
                ),
                "count": 1,
            }
            for item in trend
        ],
        "severity_distribution": severity_distribution,
        "status_distribution": status_distribution,
        "mean_time_to_acknowledge_hours": round(mean_ack, 2),
        "mean_time_to_resolve_hours": round(mean_resolve, 2),
    }


def analyze_and_save_incident(db: Session, description: str, log_text: str | None, user: User, incident_id: int | None = None):
    analysis = analyze_incident(description, log_text)
    analysis_data = dict(analysis)
    analysis_json = json.dumps(analysis_data)
    saved = False
    if incident_id:
        incident = get_incident_by_id(db, incident_id)
        incident.ai_analysis_results = analysis_json
        incident.last_updated = utc_now_naive()
        db.add(AIAnalysis(incident_id=incident_id, provider=analysis_data["provider"], analysis_json=analysis_json))
        saved = True
    db.commit()
    log_action(db, user, "ai_analysis", f"AI analyzed incident {incident_id or 'new'}")
    analysis_data["saved"] = saved
    return analysis_data


def list_users(db: Session):
    return db.query(User).all()


def update_user_role(db: Session, user_id: int, role: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role.")
    user.role = role
    db.commit()
    return user


def export_incidents_csv(db: Session):
    incidents = db.query(Incident).order_by(Incident.id.asc()).all()
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow([
        "id", "title", "category", "severity", "priority", "status",
        "detection_source", "affected_asset", "reported_by", "assigned_analyst",
        "description", "created_at", "updated_at", "resolution_timestamp",
    ])
    for incident in incidents:
        writer.writerow([
            incident.id,
            incident.title,
            incident.category,
            incident.severity,
            incident.priority,
            incident.status,
            incident.detection_source,
            incident.affected_asset,
            incident.reported_by,
            incident.assigned_analyst,
            incident.description,
            utc_isoformat(incident.detection_timestamp) or "",
            utc_isoformat(incident.last_updated) or "",
            utc_isoformat(incident.resolution_timestamp) or "",
        ])
    return output.getvalue()


def list_audit_logs(db: Session):
    return db.query(AuditLog).order_by(AuditLog.id.desc()).all()
