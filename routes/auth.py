from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask import session
from flask_login import login_user, logout_user
from werkzeug.security import check_password_hash
from extensions import mongo
from models.user import User 
from flask_login import login_required
import random
from flask import session
from flask_mail import Message
from datetime import datetime
from extensions import mail
from flask import current_app
from bson.objectid import ObjectId
 # your User(UserMixin) wrapper that maps mongo doc to User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user_doc = mongo.db.employees.find_one({"email": email})
        if not user_doc:
            user_doc = mongo.db.users.find_one({"email": email})

        if not user_doc:
            flash("Invalid credentials.", "danger")
            return redirect(url_for("auth.login"))

        if check_password_hash(user_doc.get("password", ""), password):

            # ✅ Generate OTP
            otp = str(random.randint(100000, 999999))

            # ✅ Store in session
            session["otp"] = otp
            session["temp_user_id"] = str(user_doc["_id"])

            # ✅ Send Email
            msg = Message(
                subject="Your Login OTP",
                sender=current_app.config["MAIL_USERNAME"],
                recipients=[email]
            )
            msg.body = f"Your OTP is {otp}. It will expire in 5 minutes."

            mail.send(msg)

            return redirect(url_for("auth.verify_otp"))

        flash("Invalid credentials.", "danger")
        return redirect(url_for("auth.login"))

    return render_template("auth/login.html")


@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        entered_otp = request.form.get("otp")
        stored_otp = session.get("otp")
        user_id = session.get("temp_user_id")
        otp_expiry = session.get("otp_expiry")

        # Basic validation
        if not user_id or not stored_otp:
            flash("Session expired. Please login again.", "danger")
            return redirect(url_for("auth.login"))

        # 🔥 Check expiry
        if otp_expiry and datetime.utcnow() > datetime.fromisoformat(otp_expiry):
            flash("OTP expired. Please login again.", "danger")
            return redirect(url_for("auth.login"))

        # 🔥 Check OTP match
        if entered_otp == stored_otp:

            # Fetch user from both collections
            user_doc = mongo.db.users.find_one({"_id": ObjectId(user_id)})
            if not user_doc:
                user_doc = mongo.db.employees.find_one({"_id": ObjectId(user_id)})

            if not user_doc:
                flash("User not found.", "danger")
                return redirect(url_for("auth.login"))

            user = User(user_doc)
            login_user(user)

            # Clear session temp data
            session.pop("otp", None)
            session.pop("temp_user_id", None)
            session.pop("otp_expiry", None)

            return redirect(url_for("dashboard"))

        flash("Invalid OTP", "danger")

    return render_template("auth/verify_otp.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for("auth.login"))
