"""Central config loader — loads environment variables and .env (optional).

This module intentionally keeps defaults inline so the app works without a .env
for quick local dev. For production, provide a .env file or real environment vars.
"""
import os
from pathlib import Path

try:
    # python-dotenv is optional at import time; if missing, we still use os.environ
    from dotenv import load_dotenv
    env_path = Path('.') / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except Exception:
    pass

# DB defaults
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'mypassword')
DB_NAME = os.getenv('DB_NAME', 'qr_verification')

# Admin credentials — comma separated user:pass pairs
ADMIN_CREDENTIALS = os.getenv('ADMIN_CREDENTIALS', 'bilal:Bilal@8010,nidadmin:Bilal@8010')

# Base URL used when generating QR images
BASE_URL = os.getenv('BASE_URL', 'https://www.nid-library.com/qr-app')
