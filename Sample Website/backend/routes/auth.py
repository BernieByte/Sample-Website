from flask import Blueprint, jsonify, request, session

from backend.db import get_db
from backend.utils import hash_password, verify_password


auth_bp = Blueprint("auth", __name__, url_prefix="/api")


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
        },
    }), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully."}), 200


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
