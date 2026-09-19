from flask import Blueprint, redirect, render_template, session, url_for


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
