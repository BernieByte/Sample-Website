import os
import sqlite3
from flask import g

from .config import Config


class Database:
    def __init__(self, connection, postgres=False):
        self.connection = connection
        self.postgres = postgres

    def execute(self, query, parameters=()):
        if self.postgres:
            query = query.replace("?", "%s")
        return self.connection.execute(query, parameters)

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()


def get_db():
    if "db" not in g:
        if Config.DATABASE_URL:
            import psycopg
            from psycopg.rows import dict_row

            database_url = Config.DATABASE_URL.replace("postgres://", "postgresql://", 1)
            g.db = Database(
                psycopg.connect(database_url, row_factory=dict_row),
                postgres=True,
            )
        else:
            conn = sqlite3.connect(Config.DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            g.db = Database(conn)
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    if not Config.DATABASE_URL:
        os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)

    with app.app_context():
        db = get_db()

        if db.postgres:
            db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    signup_ip TEXT,
                    signup_town TEXT,
                    signup_country TEXT,
                    signup_state TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS password_resets (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
                    token_hash TEXT NOT NULL UNIQUE,
                    expires_at TIMESTAMP NOT NULL,
                    used_at TIMESTAMP NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS login_events (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
                    ip_address TEXT,
                    logged_in_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    signup_ip TEXT,
                    signup_town TEXT,
                    signup_country TEXT,
                    signup_state TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL DEFAULT '',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS password_resets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    expires_at TEXT NOT NULL,
                    used_at TEXT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS login_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    ip_address TEXT,
                    logged_in_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)

        if db.postgres:
            db.execute("ALTER TABLE login_events ADD COLUMN IF NOT EXISTS ip_address TEXT")
            db.execute("ALTER TABLE login_events ADD COLUMN IF NOT EXISTS town TEXT")
            db.execute("ALTER TABLE login_events ADD COLUMN IF NOT EXISTS country TEXT")
            db.execute("ALTER TABLE login_events ADD COLUMN IF NOT EXISTS state TEXT")
            db.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS signup_ip TEXT")
            db.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS signup_town TEXT")
            db.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS signup_country TEXT")
            db.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS signup_state TEXT")
        else:
            try:
                db.execute("ALTER TABLE login_events ADD COLUMN ip_address TEXT")
            except Exception:
                pass

            try:
                db.execute("ALTER TABLE users ADD COLUMN signup_ip TEXT")
            except Exception:
                pass

            for column in ("town", "country", "state"):
                try:
                    db.execute(f"ALTER TABLE login_events ADD COLUMN {column} TEXT")
                except Exception:
                    pass
            for column in ("signup_town", "signup_country", "signup_state"):
                try:
                    db.execute(f"ALTER TABLE users ADD COLUMN {column} TEXT")
                except Exception:
                    pass

        db.commit()

    app.teardown_appcontext(close_db)
