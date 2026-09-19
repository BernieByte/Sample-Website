import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "byte_nest.db")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "replace-with-strong-secret-key")
    DATABASE_URL = os.environ.get("DATABASE_URL")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:5000").rstrip("/")
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_FROM = os.environ.get("SMTP_FROM", SMTP_USERNAME)
    DATABASE_PATH = DB_PATH
    JSON_SORT_KEYS = False
