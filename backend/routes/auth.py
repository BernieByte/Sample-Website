import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request, session

from backend.config import Config
from backend.db import get_db
from backend.mail import send_password_reset_email
from backend.utils import hash_password, verify_password


auth_bp = Blueprint("auth", __name__, url_prefix="/api")


def hash_reset_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required."}), 400

    db = get_db()
    existing_user = db.execute(
        "SELECT id FROM users WHERE username = ? OR email = ?",
        (username, email),
    ).fetchone()

    if existing_user:
        return jsonify({"error": "User with this username or email already exists."}), 409

    db.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
        (username, email, hash_password(password)),
    )
    db.commit()

    user = db.execute(
        "SELECT id, username, email FROM users WHERE username = ?",
        (username,),
    ).fetchone()

    session["user_id"] = user["id"]
    return jsonify({
        "message": "Account created successfully.",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "is_admin": bool(Config.ADMIN_EMAIL and user["email"].lower() == Config.ADMIN_EMAIL),
        },
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    login_value = (data.get("login") or data.get("username_or_email") or "").strip()
    password = data.get("password") or ""

    if not login_value or not password:
        return jsonify({"error": "Email or username and password are required."}), 400

    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?",
        (login_value, login_value),
    ).fetchone()

    if not user or not verify_password(password, user["password_hash"]):
        return jsonify({"error": "Invalid username/email or password."}), 401

    session["user_id"] = user["id"]
    return jsonify({
        "message": "Logged in successfully.",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "is_admin": bool(Config.ADMIN_EMAIL and user["email"].lower() == Config.ADMIN_EMAIL),
        },
    }), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully."}), 200


@auth_bp.route("/password/change", methods=["POST"])
def change_password():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Authentication required."}), 401

    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or ""
    if not current_password or len(new_password) < 8:
        return jsonify({"error": "Enter your current password and a new password of at least 8 characters."}), 400

    db = get_db()
    user = db.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user or not verify_password(current_password, user["password_hash"]):
        return jsonify({"error": "Current password is incorrect."}), 401

    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new_password), user_id))
    db.commit()
    return jsonify({"message": "Password changed successfully."}), 200


@auth_bp.route("/password-reset/request", methods=["POST"])
def request_password_reset():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "Email is required."}), 400

    db = get_db()
    user = db.execute("SELECT id, email FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        return jsonify({"message": "If an account exists, a reset link will be sent shortly."}), 200
    if not all((Config.SMTP_HOST, Config.SMTP_USERNAME, Config.SMTP_PASSWORD, Config.SMTP_FROM)):
        return jsonify({"error": "Password reset email is not configured yet."}), 503

    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_reset_token(raw_token)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
    db.execute("DELETE FROM password_resets WHERE user_id = ? OR expires_at <= CURRENT_TIMESTAMP", (user["id"],))
    db.execute(
        "INSERT INTO password_resets (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
        (user["id"], token_hash, expires_at),
    )
    db.commit()
    try:
        send_password_reset_email(user["email"], raw_token)
    except Exception:
        db.execute("DELETE FROM password_resets WHERE token_hash = ?", (token_hash,))
        db.commit()
        return jsonify({"error": "Unable to send the reset email right now."}), 503

    return jsonify({"message": "If an account exists, a reset link will be sent shortly."}), 200


@auth_bp.route("/password-reset/confirm", methods=["POST"])
def confirm_password_reset():
    data = request.get_json(silent=True) or {}
    token = data.get("token") or ""
    new_password = data.get("new_password") or ""
    if not token or len(new_password) < 8:
        return jsonify({"error": "A valid reset link and a new password of at least 8 characters are required."}), 400

    db = get_db()
    reset = db.execute(
        "SELECT id, user_id FROM password_resets WHERE token_hash = ? AND used_at IS NULL AND expires_at > CURRENT_TIMESTAMP",
        (hash_reset_token(token),),
    ).fetchone()
    if not reset:
        return jsonify({"error": "This reset link is invalid or expired."}), 400

    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new_password), reset["user_id"]))
    db.execute("UPDATE password_resets SET used_at = CURRENT_TIMESTAMP WHERE id = ?", (reset["id"],))
    db.commit()
    return jsonify({"message": "Password reset successfully. You can now log in."}), 200


@auth_bp.route("/me", methods=["GET"])
def me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated."}), 401

    db = get_db()
    user = db.execute(
        "SELECT id, username, email FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()

    if not user:
        session.clear()
        return jsonify({"error": "User not found."}), 404

    return jsonify({
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
        }
    }), 200
