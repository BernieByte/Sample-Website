from flask import Blueprint, jsonify, session

from backend.config import Config
from backend.db import get_db


admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.route("/users", methods=["GET"])
def list_users():
    if not Config.ADMIN_EMAIL or not session.get("user_id"):
        return jsonify({"error": "Admin access is not configured."}), 403

    db = get_db()
    admin = db.execute(
        "SELECT email FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()
    if not admin or admin["email"].lower() != Config.ADMIN_EMAIL:
        return jsonify({"error": "Admin access required."}), 403

    users = db.execute(
        "SELECT id, username, email, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    return jsonify({"users": [dict(user) for user in users]}), 200