Repository: QR Verification (Flask + MySQL)

This file gives concise, actionable guidance for AI coding agents (Copilot-style) working on this repository.

Key files
- `app.py` — main Flask application, public verification routes and protected admin API routes.
- `qr_generator.py` — CLI utility that inserts a record into MySQL and writes PNG files under `qr_codes/`.
- `wsgi.py` — thin entrypoint for WSGI hosts (calls `app` from `app.py`).
- `DB-setup.txt` — SQL schema for `qr_codes` and `api_access_logs` tables; use it to initialize local dev DB.
- `setup-help.txt` — deployment hints (systemd unit, nginx reverse-proxy snippet) and QR generator usage.
- `templates/` — Jinja2 templates used by routes (see `index.html` and `verification.html`).

Big picture (what to know fast)
- Simple Flask app serving two verification interfaces: web (`/verify/<qr_id>`) and JSON API (`/api/verify/<qr_id>`).
- All scans are recorded to `api_access_logs` via `log_access(...)` in `app.py`. Admin endpoints read these logs and compute statistics.
- QR codes are short UUID prefixes (first 8 chars) stored in `qr_codes.qr_id` and also saved as PNGs in `qr_codes/` by `qr_generator.py`.
- The app expects to run behind an nginx prefix `/qr-app/` in production; `setup-help.txt` contains a working proxy snippet and a systemd service example.

Auth & secrets
- Admin endpoints use HTTP Basic auth implemented in `app.py` with a hard-coded `ADMIN_USERS` map (passwords hashed with Werkzeug). If modifying auth, update both `app.py` and deployment docs.
- DB credentials are hard-coded in `db_config` in both `app.py` and `qr_generator.py`. For non-local work, prefer adding environment variable support rather than committing secrets.

Developer workflows & commands
- Initialize DB locally: run the SQL in `DB-setup.txt` (MySQL). Example: mysql -u root -p < DB-setup.txt
- Run locally for development: python app.py (listens on 0.0.0.0:5040 by default). Or use `python -m flask run --host=0.0.0.0 --port=5040` with FLASK_APP=app.py.
- Generate a QR (interactive): python qr_generator.py — it inserts into DB and writes PNGs to `qr_codes/`.
- Run with WSGI servers: `wsgi.py` provides the `app` object for gunicorn/uwsgi. Example: gunicorn -w 4 wsgi:app -b 0.0.0.0:5040

Patterns & project-specific conventions
- QR IDs: created as str(uuid.uuid4())[:8] in `qr_generator.py`. Expect 8-character unique IDs across `qr_codes.qr_id`.
- Verification URL: `https://<host>/qr-app/verify/<qr_id>` — `qr_generator.generate_qr_code` uses base_url default `https://www.nid-library.com/qr-app` and writes that URL into the QR image.
- Logging: `log_access(qr_id, endpoint, http_method, status_code)` both records request metadata and calls remote IP geolocation (ipapi.co) for non-local IPs.
- Templates: `verification.html` expects variables `status`, `qr_id`, and conditionally `description` and `created_at` for valid codes.

Integration points & external dependencies
- MySQL (mysql-connector-python) — confirm local Docker or local MySQL instance for dev. Use `DB-setup.txt` to create tables.
- External IP geolocation: `http://ipapi.co/<ip>/json/` (network call, short timeout); in offline tests, it falls back to Unknown.
- qrcode & Pillow — used by `qr_generator.py` to render PNG images.

Careful/quirks discovered
- Secrets in source: DB passwords and admin passwords are hard-coded. Don't commit production secrets — update to env vars before shipping.
- Proxy-prefix awareness: `qr_generator.generate_qr_code` embeds a base URL with `/qr-app` prefix. If you change the app prefix, update generator and nginx config.
- `api_access_logs.qr_id` is a FK to `qr_codes.qr_id` and uses ON DELETE SET NULL. When adding migrations, keep types/lengths consistent (VARCHAR(100)).

Examples to copy/paste
- Verify endpoint (web): GET /verify/abcd1234 → renders `verification.html` with description and created_at when found.
- API verify (JSON): GET /api/verify/abcd1234 → {status, qr_id, description, created_at, valid}
- Admin stats: GET /api/access_stats (requires basic auth header)

If you modify behavior
- Update `templates/` when changing the data passed to render_template(). Search for render_template calls in `app.py`.
- If you add new background tasks that write logs, reuse `log_access(...)` semantics to keep columns consistent.

Where to look next
- `app.py` for all request handling and DB queries.
- `qr_generator.py` for the QR lifecycle (create DB row + generate PNG).
- `DB-setup.txt` for canonical schema.

If anything here is unclear or you want extra samples (eg. a unit test scaffold or environment variable wiring), tell me which area to expand.
