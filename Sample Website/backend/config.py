import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "byte_nest.db")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "replace-with-strong-secret-key")
    DATABASE_PATH = DB_PATH
    JSON_SORT_KEYS = False
