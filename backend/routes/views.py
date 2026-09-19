from flask import Blueprint, redirect, render_template, session, url_for

from backend.config import Config
from backend.db import get_db
from backend.routes.admin import is_admin_user


views_bp = Blueprint("views", __name__)


@views_bp.route("/")
def home():
    return render_template("index.html")


@views_bp.route("/login")
def login_page():
    if "user_id" in session:
        return redirect(url_for("views.dashboard"))
    return render_template("templates/login.html")


@views_bp.route("/signup")
def signup_page():
    if "user_id" in session:
        return redirect(url_for("views.dashboard"))
    return render_template("templates/signup.html")


@views_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("views.login_page"))
    return render_template("templates/dashboard.html")


@views_bp.route("/admin")
def admin_page():
    if "user_id" not in session:
        return redirect(url_for("views.login_page"))

    db = get_db()
    user = db.execute(
        "SELECT email FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()
    if not Config.ADMIN_EMAIL or not is_admin_user(user):
        return redirect(url_for("views.dashboard"))

    return render_template("templates/admin.html")
