# CyberSOC Incident Response Platform

CyberSOC is a React/Vite frontend with a FastAPI API and SQLite persistence. It includes incident tracking, role-based authorization, append-only audit logging, dashboard metrics, and a local rule-based Demo AI incident analyzer. AI analysis runs locally and does not call an external AI provider.

## Local development

Use Python 3.12 for the backend and Node.js 20 or newer for the frontend.

1. Install the backend requirements in the Python 3.12 environment:

   ```powershell
   Set-Location backend
   py -3.12 -m pip install -r requirements.txt
   py -3.12 -m uvicorn app.main:app --reload
   ```

2. In another terminal, start the frontend:

   ```powershell
   Set-Location frontend
   npm ci
   npm run dev
   ```

3. Open http://localhost:5173. Vite proxies `/api` requests to the backend on port 8000. The backend uses the stable `backend/incident_platform.db` path regardless of its working directory unless `DATABASE_URL` is explicitly set.

Timestamps are stored in SQLite as UTC values, with legacy timezone-naive values interpreted as UTC. API timestamps include the UTC `Z` suffix; the frontend converts them to `Asia/Kolkata` and displays IST. Backend deployments install the `tzdata` package so the IANA timezone database is available on Windows as well as Linux.

For local development only, demo accounts are created by default:

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin123!` |
| Security Analyst | `analyst` | `Analyst123!` |
| Incident Responder | `responder` | `Responder123!` |
| Viewer | `viewer` | `Viewer123!` |

Do not use these demo credentials in a shared or production environment. Public registration creates Viewer accounts; administrators assign other roles from user management.

## Backend tests

Run the API tests from the backend directory:

```powershell
py -3.12 -m pytest -q
```

Tests create isolated temporary SQLite databases and do not use the development database.

## Docker Compose deployment

Docker Engine and the Docker Compose plugin are required.

1. Copy `.env.example` to `.env`.
2. Set `SECRET_KEY` to a cryptographically random value and set a unique `BOOTSTRAP_ADMIN_PASSWORD`. Choose a unique bootstrap username and email. Keep `.env` private and out of version control.
3. Start the stack:

   ```powershell
   docker compose up --build -d
   ```

4. Visit http://localhost:8080. The API health check is available at http://localhost:8000/health.
5. Inspect service status and logs with `docker compose ps` and `docker compose logs -f`.
6. Stop the services with `docker compose down`. The named `soc_data` volume preserves SQLite data; `docker compose down -v` removes that data and should only be used when intentionally resetting the deployment.

The Compose configuration disables demo account seeding and creates the administrator from the bootstrap settings on first startup. It persists the database in the `soc_data` named volume and serves the frontend through Nginx, which proxies API requests to FastAPI. Incident analysis uses local Python keyword and pattern rules and requires no AI-provider key or external service. For a deployment behind HTTPS, set `AUTH_COOKIE_SECURE=true` in `.env`; keep it `false` only for local HTTP development.

Authentication uses short-lived access tokens and rotating, hashed refresh sessions stored in the `auth_sessions` table. The refresh credential is an HttpOnly, SameSite=Lax cookie. Set `AUTH_COOKIE_SECURE=true` when the browser connects over HTTPS. On startup, the backend creates this table if it is missing; existing user, incident, AI-analysis, and audit-log tables and rows are not dropped or recreated.

Before exposing this service to the public internet, terminate TLS at a trusted reverse proxy, restrict network access to the API port as appropriate, rotate all bootstrap credentials, and configure backups and monitoring for the persistent volume. SQLite is intended for a single-instance deployment; use a managed database and migration strategy before scaling the API horizontally.

## Configuration

The backend reads settings from environment variables (or a local `.env` file):

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy database URL; defaults to a local SQLite database. |
| `SECRET_KEY` | JWT signing secret; replace the development default for deployment. |
| `SEED_DEMO_DATA` | Creates the four local demo accounts when `true`; Compose sets this to `false`. |
| `BOOTSTRAP_ADMIN_USERNAME` | Optional first administrator username; set all three bootstrap values or none. |
| `BOOTSTRAP_ADMIN_EMAIL` | Email for the first administrator. |
| `BOOTSTRAP_ADMIN_PASSWORD` | Password for the first administrator. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime before refresh; defaults to 480 minutes. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Maximum refresh-session lifetime; defaults to 30 days. |
| `AUTH_COOKIE_SECURE` | Set to `true` when the browser-facing connection uses HTTPS; defaults to `false` for local HTTP development. |
