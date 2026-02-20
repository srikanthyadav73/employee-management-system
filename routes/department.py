from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required
from extensions import mongo
from datetime import datetime
from utils.decorators import role_required

department_bp = Blueprint("department", __name__)

@department_bp.route("/departments")
@login_required
@role_required("admin", "manager")
def list_departments():
    departments = list(mongo.db.departments.find())
    return render_template("departments/list.html", departments=departments)


@department_bp.route("/departments/add", methods=["GET", "POST"])
@login_required
@role_required("admin", "manager")
def add_department():
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")

        mongo.db.departments.insert_one({
            "name": name,
            "description": description,
            "created_at": datetime.utcnow()
        })

        return redirect(url_for("department.list_departments"))

    return render_template("departments/add.html")
