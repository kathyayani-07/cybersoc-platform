# Project completion checklist

## Existing product and verification

- [x] FastAPI backend starts and `/health` returns HTTP 200.
- [x] Vite frontend starts and serves the login application.
- [x] Authenticated browser incident create/detail workflow completed against an isolated SQLite database.
- [x] Browser incident update, investigation note, demo AI analysis, and dashboard reflection verified.
- [x] Browser incident creation shows success, navigates to the incident list, and displays the saved incident and assigned analyst.
- [x] Browser verifies expired-session redirect and a visible message when the incident API is unreachable.
- [x] Incident pagination displays ten rows per page, numbers rows continuously across pages, reports the total, and enables/disables navigation at boundaries.
- [x] Backend pagination returns ten records on page one and the remaining record on page two for an 11-incident set; invalid page bounds are rejected.
- [x] Live browser pagination verified against the existing 11 incidents: page one has 10 rows, page two has one row numbered 11, and Next/Previous work with correct boundary states.
- [x] Reports aggregate all incidents from the database, with data-derived totals by status, severity, and priority; live report totals verified against all 11 existing incidents.
- [x] Authenticated CSV export returns all 11 existing incidents with the requested fields; CSV escaping for commas, quotes, and embedded line breaks is covered by automated tests.
- [x] Automated backend API tests pass (11 tests), including incident creation, persisted assigned analyst/notes, required-field validation, pagination boundaries, report aggregates, and CSV export.
- [x] Public registration is restricted to the Viewer role; role changes remain administrator-controlled.
- [x] Local development demo accounts are documented; deployment bootstrap settings avoid shipping seeded demo passwords.
- [x] Backend/frontend Dockerfiles, Compose services, Nginx API proxy, persistent SQLite volume, and health check configuration added; bootstrap-admin startup was separately verified with demo seeding disabled.
- [x] Local development and deployment instructions added in `README.md`.
- [x] Password-hashing dependency pinned to a passlib-compatible bcrypt version; runtime warning and hash/verify behavior checked after dependency installation.

## Validation limitations / follow-up

- [ ] Run the Docker Compose stack and verify container health; Docker is not installed in the current environment, so container execution could not be validated.
- [ ] Configure production TLS, backups, and monitoring before public deployment.
- [ ] Consider PostgreSQL and schema migrations before running multiple API instances.
- [ ] Replace legacy `datetime.utcnow()` usage and review upstream AnyIO/JWT deprecation warnings before a future dependency/runtime upgrade.
