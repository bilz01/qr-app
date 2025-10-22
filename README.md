# QR Verification (Flask + MySQL)

Small Flask app that verifies short QR codes (8-char UUID prefixes). The app provides a web verification UI and a JSON API, logs all scans to MySQL, and exposes protected admin pages for logs and analytics.

Quick summary
- Web verification: `/verify/<qr_id>` → human-friendly HTML (`templates/verification.html`)
- API verification: `/api/verify/<qr_id>` → JSON response
- Admin pages (HTTP Basic auth): `/api/access_logs`, `/api/access_stats`, `/api/qr_codes`
- QR generator CLI: `qr_generator.py` (inserts DB row and writes PNG to `qr_codes/`)

Prerequisites
- Python 3.10+ (3.11 recommended)
- MySQL server
- Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Configuration
- Copy `.env.example` to `.env` and update values (or export env vars directly).
- Key env vars:
  - `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
  - `ADMIN_CREDENTIALS` — comma-separated `user:pass` pairs (e.g. `admin:ChangeMe`)
  - `BASE_URL` — used by `qr_generator.py` when embedding verification URL into QR images

Initialize database
- Use `DB-setup.txt` to create the schema in your MySQL instance:

```powershell
mysql -u root -p < DB-setup.txt
```

Run locally
- Quick run for development (binds to 0.0.0.0:5040):

```powershell
python .\app.py
```

Run with Docker Compose (recommended for local testing)

```powershell
docker-compose up --build
```

This will start a MySQL service and the Flask app. The compose file sets DB credentials and mounts the code for live edits.

Admin pages
- The admin endpoints are protected by HTTP Basic auth. Use any user configured in `ADMIN_CREDENTIALS`.
- Access logs support pagination via `?page=` and `?per_page=` query params.

QR generation
- Run the interactive generator (creates DB row and PNG):

```powershell
python .\qr_generator.py
```

Deployment notes
- `setup-help.txt` contains example systemd unit and nginx proxy snippet. The app expects to be served under the `/qr-app/` prefix in production by the nginx snippet provided.
- Secrets are read from environment (or `.env` at startup). Do not commit production secrets to the repo.

Where to look in the code
- `app.py` — routes, DB access, logging, admin pages.
- `qr_generator.py` — interactive CLI to create QR codes and PNG images.
- `templates/` — Jinja2 templates including new admin pages (`access_logs.html`, `access_stats.html`, `qr_codes.html`).

If you want I can:
- Add a Docker Compose dev setup with MySQL for easy local testing.
- Add unit tests (pytest) with a small MySQL test container.
- Improve UI styling for admin pages.
