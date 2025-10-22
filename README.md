# QR Verification (Flask + MySQL)

Small Flask app that verifies short QR codes (8-char UUID prefixes). The app provides a web verification UI and a JSON API, logs all scans to MySQL, and exposes protected admin pages for logs and analytics.

## Quick summary
- Web verification: `/verify/<qr_id>` → human-friendly HTML (`templates/verification.html`)
- API verification: `/api/verify/<qr_id>` → JSON response
- Admin pages (HTTP Basic auth): `/api/access_logs`, `/api/access_stats`, `/api/qr_codes`
- QR generator CLI: `qr_generator.py` (inserts DB row and writes PNG to `qr_codes/`)

## Setup options

### Option 1: Docker Compose (recommended for local testing)
Prerequisites:
- Docker and Docker Compose

1. Clone the repo and start services:
```powershell
git clone https://github.com/bilz01/qr-app.git
cd qr-app
docker-compose up --build
```

This will:
- Start MySQL (port 3306, credentials in docker-compose.yml)
- Initialize DB schema automatically
- Start Flask app with Gunicorn (port 5040)
- Mount code for live development

2. Generate QR codes using the container:
```powershell
# Run generator in the web container
docker-compose exec web python qr_generator.py
```

### Option 2: Local Python + MySQL
Prerequisites:
- Python 3.10+ (3.11 recommended)
- MySQL server

1. Install dependencies:
```powershell
python -m pip install -r requirements.txt
```

2. Configure environment:
- Copy `.env.example` to `.env` and update values (or export env vars directly).
- Key env vars:
  - `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
  - `ADMIN_CREDENTIALS` — comma-separated `user:pass` pairs (e.g. `admin:ChangeMe`)
  - `BASE_URL` — used by `qr_generator.py` when embedding verification URL into QR images

3. Initialize database:
```powershell
mysql -u root -p < DB-setup.txt
```

4. Start the app:
```powershell
python .\app.py
```

## Using the app

### Generate QR codes
1. With Docker:
```powershell
docker-compose exec web python qr_generator.py
```

2. Or locally:
```powershell
python .\qr_generator.py
```

The generator will:
- Prompt for a description
- Generate a unique 8-char ID
- Save to MySQL
- Create a QR PNG in `qr_codes/`

### Access the app
1. Public endpoints (no auth needed):
- Verify via web: http://localhost:5040/verify/<qr_id>
- Verify via API: http://localhost:5040/api/verify/<qr_id>

2. Admin pages (HTTP Basic auth required):
- Access logs: http://localhost:5040/api/access_logs
  - Support pagination: `?page=N&per_page=100`
  - Filter by QR: `?qr_id=abc123`
- Usage stats: http://localhost:5040/api/access_stats
- QR code list: http://localhost:5040/api/qr_codes

Default admin credentials (Docker):
- Username: `admin`
- Password: `adminpass`

## Production deployment
- `setup-help.txt` contains example systemd unit and nginx proxy snippet. The app expects to be served under the `/qr-app/` prefix in production by the nginx snippet provided.
- Secrets are read from environment (or `.env` at startup). Do not commit production secrets to the repo.

## Project structure
- `app.py` — routes, DB access, logging, admin pages.
- `qr_generator.py` — interactive CLI to create QR codes and PNG images.
- `docker/` — Docker-related files (MySQL init scripts).
- `templates/` — Jinja2 templates including new admin pages (`access_logs.html`, `access_stats.html`, `qr_codes.html`).

## Development notes
1. Running with Docker:
- Code changes are reflected live (host volume mount)
- MySQL data persists in docker volume
- Override configs: create `docker-compose.override.yml`

2. Running locally:
- Use `python -m flask run` with `FLASK_APP=app.py` for auto-reload
- Configure via `.env` or environment variables

3. Database:
- MySQL schema in `DB-setup.txt` and `docker/mysql-init/`
- Foreign key: `api_access_logs.qr_id` → `qr_codes.qr_id`

4. Adding features:
- Update `templates/` when changing page data
- Use `log_access()` for new background tasks
- Don't commit secrets (use env vars)
