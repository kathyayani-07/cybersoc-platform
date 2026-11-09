import csv
import io

from datetime import timedelta

from app import ai_service
from app.auth import create_access_token
from app.database import get_db
from app.main import app
from app.models import AIAnalysis


def login(client, username="admin", password="Admin123!"):
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def new_incident(title="Test suspicious login"):
    return {
        "title": title,
        "description": "Suspicious login from an unfamiliar endpoint.",
        "category": "Credential Security",
        "severity": "High",
        "priority": "High",
        "status": "New",
        "affected_asset": "test-workstation",
    }


def test_health_and_login(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    headers = login(client)
    current_user = client.get("/api/auth/me", headers=headers)
    assert current_user.status_code == 200
    assert current_user.json()["role"] == "admin"

    bad_login = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "incorrect"},
    )
    assert bad_login.status_code == 401


def test_admin_users_are_authenticated_and_refresh_sessions_rotate(client):
    assert client.get("/api/admin/users").status_code == 401

    login_response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Admin123!"},
    )
    assert login_response.status_code == 200
    old_refresh = client.cookies.get("cyber_refresh")
    assert old_refresh

    expired_access = create_access_token({"sub": "admin"}, expires_delta=timedelta(seconds=-1))
    refreshed = client.post(
        "/api/auth/refresh",
        headers={"Authorization": f"Bearer {expired_access}"},
    )
    assert refreshed.status_code == 200
    new_refresh = client.cookies.get("cyber_refresh")
    assert new_refresh and new_refresh != old_refresh

    users = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {refreshed.json()['access_token']}"},
    )
    assert users.status_code == 200
    admin = next(user for user in users.json()["items"] if user["username"] == "admin")
    assert admin["role"] == "admin"

    replay = client.post("/api/auth/refresh", cookies={"cyber_refresh": old_refresh})
    assert replay.status_code == 401


def test_logout_is_audited_and_revokes_refresh_session(client):
    headers = login(client)

    response = client.post("/api/auth/logout", headers=headers)
    assert response.status_code == 204
    assert client.post("/api/auth/refresh").status_code == 401

    logs = client.get("/api/admin/audit-logs", headers=headers).json()["items"]
    actions = [item["action"] for item in logs]
    assert "user_login" in actions
    assert "user_logout" in actions
    assert all(item["created_at"].endswith("Z") for item in logs)


def test_public_registration_cannot_assign_privileged_role(client):
    registration = client.post(
        "/api/auth/register",
        json={
            "username": "self-promoted",
            "email": "self-promoted@example.com",
            "password": "SafeTestPassword123!",
            "role": "admin",
        },
    )

    assert registration.status_code == 200
    assert registration.json()["user"]["role"] == "viewer"
    headers = {"Authorization": f"Bearer {registration.json()['access_token']}"}
    assert client.get("/api/admin/users", headers=headers).status_code == 403
    assert client.get("/api/admin/audit-logs", headers=headers).status_code == 403
    assert client.post("/api/incidents", json=new_incident(), headers=headers).status_code == 403
    admin_headers = login(client)
    audit_actions = [
        item["action"]
        for item in client.get("/api/admin/audit-logs", headers=admin_headers).json()["items"]
    ]
    assert "user_registered" in audit_actions


def test_incident_create_update_filter_and_dashboard(client):
    headers = login(client)
    incident_payload = new_incident()
    incident_payload["assigned_analyst"] = "analyst@example.com"
    incident_payload["investigation_notes"] = "Initial triage note"
    created = client.post("/api/incidents", json=incident_payload, headers=headers)
    assert created.status_code == 200
    incident_id = created.json()["id"]
    assert created.json()["assigned_analyst"] == "analyst@example.com"
    assert created.json()["investigation_notes"] == "Initial triage note"
    assert created.json()["detection_timestamp"].endswith("Z")

    detail = client.get(f"/api/incidents/{incident_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["title"] == "Test suspicious login"
    assert detail.json()["assigned_analyst"] == "analyst@example.com"
    assert detail.json()["investigation_notes"] == "Initial triage note"

    update = client.put(
        f"/api/incidents/{incident_id}",
        json={"status": "Investigating", "assigned_analyst": "responder@example.com"},
        headers=headers,
    )
    assert update.status_code == 200
    assert update.json()["status"] == "Investigating"
    assert update.json()["last_updated"].endswith("Z")
    listed = client.get("/api/incidents", headers=headers).json()["items"][0]
    assert listed["last_updated"].endswith("Z")
    dashboard = client.get("/api/dashboard/overview", headers=headers).json()
    assert dashboard["recent_activity"][0]["last_updated"].endswith("Z")
    logs = client.get("/api/admin/audit-logs", headers=headers).json()["items"]
    actions = [item["action"] for item in logs]
    assert "assigned_incident" in actions
    assert "changed_incident_status" in actions

    filtered = client.get(
        "/api/incidents",
        params={"query": "test-workstation", "severity": "High"},
        headers=headers,
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
    assert filtered.json()["items"][0]["id"] == incident_id

    dashboard = client.get("/api/dashboard/overview", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["total_incidents"] == 1
    assert dashboard.json()["under_investigation"] == 1
    assert dashboard.json()["high_severity_incidents"] == 1
    resolved = client.put(
        f"/api/incidents/{incident_id}",
        json={"status": "Resolved"},
        headers=headers,
    )
    assert resolved.status_code == 200
    assert resolved.json()["resolution_timestamp"].endswith("Z")
    logs = client.get("/api/admin/audit-logs", headers=headers).json()["items"]
    assert any(item["action"] == "resolved_incident" for item in logs)


def test_incident_offset_timestamps_are_stored_and_returned_as_utc(client):
    headers = login(client)
    response = client.post(
        "/api/incidents",
        headers=headers,
        json={
            **new_incident("IST input timestamp"),
            "detection_timestamp": "2026-11-06T12:22:00+05:30",
            "last_updated": "2026-11-06T12:22:00+05:30",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["detection_timestamp"] == "2026-11-06T06:52:00Z"
    assert body["last_updated"] == "2026-11-06T06:52:00Z"

    listed = client.get("/api/incidents", headers=headers).json()["items"][0]
    assert listed["detection_timestamp"] == "2026-11-06T06:52:00Z"
    reported = client.get("/api/reports", headers=headers).json()["items"][0]
    assert reported["last_updated"] == "2026-11-06T06:52:00Z"


def test_dashboard_trend_groups_by_indian_calendar_date(client):
    headers = login(client)
    response = client.post(
        "/api/incidents",
        headers=headers,
        json={
            **new_incident("IST trend boundary"),
            "detection_timestamp": "2026-11-05T20:00:00Z",
        },
    )
    assert response.status_code == 200
    trend = client.get("/api/dashboard/overview", headers=headers).json()["incident_trend"]
    assert {"date": "2026-11-06", "count": 1} in trend


def test_incident_create_rejects_missing_required_fields(client):
    headers = login(client)
    invalid_payload = new_incident()
    invalid_payload.pop("category")

    response = client.post("/api/incidents", json=invalid_payload, headers=headers)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "category"


def test_incident_pagination_returns_ten_then_remaining_record(client):
    headers = login(client)
    for index in range(11):
        response = client.post(
            "/api/incidents",
            json=new_incident(f"Pagination incident {index + 1:02d}"),
            headers=headers,
        )
        assert response.status_code == 200

    first_page = client.get(
        "/api/incidents",
        params={"page": 1, "page_size": 10},
        headers=headers,
    )
    second_page = client.get(
        "/api/incidents",
        params={"page": 2, "page_size": 10},
        headers=headers,
    )

    assert first_page.status_code == 200
    assert first_page.json()["total"] == 11
    assert first_page.json()["page"] == 1
    assert first_page.json()["page_size"] == 10
    assert len(first_page.json()["items"]) == 10
    assert second_page.status_code == 200
    assert second_page.json()["total"] == 11
    assert second_page.json()["page"] == 2
    assert len(second_page.json()["items"]) == 1
    assert second_page.json()["items"][0]["title"] == "Pagination incident 01"


def test_incident_pagination_rejects_invalid_page_values(client):
    headers = login(client)
    assert client.get("/api/incidents", params={"page": 0}, headers=headers).status_code == 422
    assert client.get("/api/incidents", params={"page_size": 11}, headers=headers).status_code == 422


def test_reports_include_all_incidents_and_grouped_counts(client):
    headers = login(client)
    values = [
        ("Report incident 1", "New", "High", "High"),
        ("Report incident 2", "Resolved", "Critical", "Medium"),
        ("Report incident 3", "New", "Low", "Low"),
        ("Report incident 4", "Acknowledged", "High", "High"),
        ("Report incident 5", "New", "Medium", "Medium"),
        ("Report incident 6", "Contained", "Critical", "High"),
        ("Report incident 7", "Investigating", "Low", "Low"),
        ("Report incident 8", "Closed", "Medium", "Medium"),
        ("Report incident 9", "New", "High", "High"),
        ("Report incident 10", "New", "Low", "Low"),
        ("Report incident 11", "New", "Critical", "Critical"),
    ]
    for title, status, severity, priority in values:
        response = client.post(
            "/api/incidents",
            json={
                **new_incident(title),
                "status": status,
                "severity": severity,
                "priority": priority,
            },
            headers=headers,
        )
        assert response.status_code == 200

    report_response = client.get("/api/reports", headers=headers)
    assert report_response.status_code == 200
    report = report_response.json()
    assert report["total_incidents"] == 11
    assert len(report["items"]) == 11
    assert report["status_counts"] == {
        "New": 6,
        "Resolved": 1,
        "Acknowledged": 1,
        "Contained": 1,
        "Investigating": 1,
        "Closed": 1,
    }
    assert report["severity_counts"] == {"High": 3, "Critical": 3, "Low": 3, "Medium": 2}
    assert report["priority_counts"] == {"High": 4, "Medium": 3, "Low": 3, "Critical": 1}


def test_csv_export_contains_all_fields_and_escapes_special_characters(client):
    headers = login(client)
    payload = new_incident('CSV "quoted", title\nsecond line')
    payload.update({
        "category": 'Threat, "category"',
        "description": 'First line, with comma\nSecond line says "verify"',
        "assigned_analyst": "analyst@example.com",
    })
    created = client.post("/api/incidents", json=payload, headers=headers)
    assert created.status_code == 200

    response = client.get("/api/incidents/export/csv", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "incident_export.csv" in response.headers["content-disposition"]
    rows = list(csv.DictReader(io.StringIO(response.text)))
    assert len(rows) == 1
    row = rows[0]
    assert row["id"] == str(created.json()["id"])
    assert row["title"] == payload["title"]
    assert row["category"] == payload["category"]
    assert row["description"] == payload["description"]
    assert row["assigned_analyst"] == "analyst@example.com"
    assert row["created_at"]
    assert row["updated_at"]


def test_viewer_cannot_mutate_incidents_or_manage_users(client):
    admin_headers = login(client)
    created = client.post("/api/incidents", json=new_incident(), headers=admin_headers)
    incident_id = created.json()["id"]
    viewer_headers = login(client, "viewer", "Viewer123!")

    update = client.put(
        f"/api/incidents/{incident_id}",
        json={"status": "Closed"},
        headers=viewer_headers,
    )
    assert update.status_code == 403
    assert client.get("/api/admin/users", headers=viewer_headers).status_code == 403


def test_local_demo_analysis_uses_submitted_evidence_and_persists_result(client):
    headers = login(client)
    incident = client.post("/api/incidents", json=new_incident(), headers=headers).json()
    before_count = client.get("/api/incidents", headers=headers).json()["total"]
    submitted_description = "A phishing email delivered a suspicious attachment."
    submitted_log = "EDR detected process execution from 192.0.2.15 at evil.example."
    response = client.post(
        "/api/ai/analyze",
        headers=headers,
        json={
            "description": submitted_description,
            "log_text": submitted_log,
            "incident_id": incident["id"],
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["provider"] == "Demo AI"
    assert result["classification"] == "Phishing"
    assert result["suggested_severity"] == "High"
    assert response.json()["saved"] is True
    assert response.json()["timestamp"].endswith("Z")
    assert "phishing" in result["executive_summary"].lower()
    assert any("evil.example" in indicator for indicator in result["indicators_of_compromise"])
    assert any("192.0.2.15" in indicator for indicator in result["indicators_of_compromise"])
    assert result["containment_recommendations"]
    assert result["rationale"]
    assert client.get(f"/api/incidents/{incident['id']}", headers=headers).json()["status"] == "New"
    assert client.get("/api/incidents", headers=headers).json()["total"] == before_count
    test_db_generator = app.dependency_overrides[get_db]()
    test_db = next(test_db_generator)
    try:
        saved = test_db.query(AIAnalysis).filter(AIAnalysis.incident_id == incident["id"]).one()
        assert saved.provider == "Demo AI"
        assert "Phishing" in saved.analysis_json
    finally:
        test_db_generator.close()


def test_local_demo_rules_classify_all_requested_attack_patterns():
    cases = (
        ("Repeated brute-force password failures", "10 failed logins", "Brute-Force / Credential Attack", "High"),
        ("Suspicious login from an unknown location", "login from 198.51.100.8", "Suspicious Login", "Medium"),
        ("Malware detected on endpoint", "trojan process found", "Malware Activity", "High"),
        ("Unauthorized access and privilege escalation", "admin account compromised", "Unauthorized Access", "Critical"),
        ("SQL injection attempt", "GET /search?q=' OR 1=1 --", "SQL Injection", "High"),
        ("External port scan detected", "TCP SYN scan of ports 22, 80 and 443", "Port Scanning", "Medium"),
        ("Data exfiltration detected", "2GB of customer data exfiltrated to remote host", "Data Exfiltration", "Critical"),
        ("Phishing email reported", "Suspicious attachment delivered to employee", "Phishing", "High"),
    )
    for description, log_text, classification, severity in cases:
        result = ai_service.analyze_incident(description, log_text)
        assert result["provider"] == "Demo AI"
        assert result["classification"] == classification
        assert result["suggested_severity"] == severity

    sql_error = ai_service.analyze_incident(
        "Application SQL injection attempt.",
        "Attacker sent UNION SELECT username FROM accounts; SQL error returned.",
    )
    assert sql_error["classification"] == "SQL Injection"
    assert sql_error["suggested_severity"] == "High"

    benign = ai_service.analyze_incident("Routine maintenance completed.")
    assert benign["classification"] == "Unclassified Security Event"
    assert benign["suggested_severity"] == "Low"

    escalated = ai_service.analyze_incident(
        "SQL injection attempt",
        "Successful exploit succeeded and database dump created",
    )
    assert escalated["suggested_severity"] == "Critical"


def test_ai_analysis_rejects_empty_evidence_and_bad_incident_id(client):
    headers = login(client)
    empty = client.post("/api/ai/analyze", headers=headers, json={"description": "  ", "log_text": "\n"})
    assert empty.status_code == 422
    assert "Enter an incident description or a security log excerpt." in str(empty.json()["detail"])

    bad_id = client.post(
        "/api/ai/analyze",
        headers=headers,
        json={"description": "port scan", "incident_id": 0},
    )
    assert bad_id.status_code == 422

def test_admin_can_change_role_and_audit_action_is_recorded(client):
    headers = login(client)
    users = client.get("/api/admin/users", headers=headers).json()["items"]
    viewer = next(user for user in users if user["username"] == "viewer")

    response = client.put(
        f"/api/admin/users/{viewer['id']}/role",
        params={"role": "incident_responder"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["user"]["role"] == "incident_responder"

    audit = client.get("/api/admin/audit-logs", headers=headers)
    assert audit.status_code == 200
    assert any(item["action"] == "updated_user_role" for item in audit.json()["items"])
