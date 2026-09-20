from flask import Blueprint, jsonify, session

from backend.config import Config
from backend.db import get_db
from backend.geolocation import lookup_ip


admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def is_admin_user(user):
    return bool(
        Config.ADMIN_EMAIL
        and user
        and user["email"].strip().lower() == Config.ADMIN_EMAIL
    )


@admin_bp.route("/users", methods=["GET"])
def list_users():
    if not Config.ADMIN_EMAIL or not session.get("user_id"):
        return jsonify({"error": "Admin access is not configured."}), 403

    db = get_db()
    admin = db.execute(
        "SELECT email FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()
    if not is_admin_user(admin):
        return jsonify({"error": "Admin access required."}), 403

    users = db.execute(
        """
        SELECT id, username, email, signup_ip, signup_town, signup_country,
               signup_state, created_at
        FROM users ORDER BY created_at DESC
        """
    ).fetchall()
    user_data = []
    for user in users:
        item = dict(user)
        item.update({
            "town": item.pop("signup_town") or "Unavailable",
            "country": item.pop("signup_country") or "Unavailable",
            "state": item.pop("signup_state") or "Unavailable",
        })
        if item["town"] == "Unavailable" or item["country"] == "Unavailable":
            item.update(lookup_ip(item.get("signup_ip")))
        user_data.append(item)
    return jsonify({"users": user_data}), 200


@admin_bp.route("/logins", methods=["GET"])
def list_logins():
    if not Config.ADMIN_EMAIL or not session.get("user_id"):
        return jsonify({"error": "Admin access is not configured."}), 403

    db = get_db()
    admin = db.execute(
        "SELECT email FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()
    if not is_admin_user(admin):
        return jsonify({"error": "Admin access required."}), 403

    logins = db.execute(
        """
           SELECT login_events.id, users.username, users.email,
               login_events.ip_address, login_events.town,
               login_events.country, login_events.state, login_events.logged_in_at
        FROM login_events
        JOIN users ON users.id = login_events.user_id
        ORDER BY login_events.logged_in_at DESC, login_events.id DESC
        LIMIT 100
        """
    ).fetchall()
    login_data = []
    for login in logins:
        item = dict(login)
        if item.get("town") == "Unavailable" or item.get("country") == "Unavailable":
            item.update(lookup_ip(item.get("ip_address")))
        login_data.append(item)
    return jsonify({"logins": login_data}), 200