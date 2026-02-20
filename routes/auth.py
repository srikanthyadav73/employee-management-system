from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from extensions import mongo
from models.user import User

auth_bp = Blueprint("auth", __name__)

# ------------------ LOGIN ------------------
@auth_bp.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user_data = mongo.db.users.find_one({"email": email})

        if user_data and check_password_hash(user_data["password"], password):
            user = User(user_data)
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid Email or Password")

    return render_template("auth/login.html")


# ------------------ LOGOUT ------------------
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
