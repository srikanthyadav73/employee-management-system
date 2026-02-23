from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensions import mongo
from bson.objectid import ObjectId
from utils.decorators import role_required
from flask_login import current_user 
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId 
from datetime import datetime


employee_bp = Blueprint("employee", __name__)

# -------- VIEW ALL EMPLOYEES --------
@employee_bp.route("/employees")
@login_required
def list_employees():
    search_query = request.args.get("search")
    page = int(request.args.get("page", 1))
    per_page = 5

    query = {}

    if search_query:
        query["name"] = {"$regex": search_query, "$options": "i"}

    total_employees = mongo.db.employees.count_documents(query)

    employees = list(
        mongo.db.employees.find(query)
        .skip((page - 1) * per_page)
        .limit(per_page)
    )

    total_pages = (total_employees + per_page - 1) // per_page

    return render_template(
        "employees/list.html",
        employees=employees,
        page=page,
        total_pages=total_pages,
        search_query=search_query
    )


# -------- ADD EMPLOYEE --------
@employee_bp.route("/employees/add", methods=["GET", "POST"])
@login_required
@role_required("admin")
def add_employee():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        department = request.form.get("department")
        role = request.form.get("role")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not password or password != confirm_password:
            flash("Passwords are empty or do not match.", "danger")
            return redirect(url_for("employee.add_employee"))

        # Hash password
        hashed = generate_password_hash(password, method="pbkdf2:sha256") # defaults to pbkdf2:sha256

        mongo.db.employees.insert_one({
            "name": name,
            "email": email,
            "department": department,
            "role": role,
            "password": hashed,   # store hash, not plaintext
            "created_at": datetime.utcnow()
        })

        flash("Employee Added Successfully!", "success")
        return redirect(url_for("employee.list_employees"))

    return render_template("employees/add.html")
# -------- DELETE EMPLOYEE --------
@employee_bp.route("/employees/delete/<id>")
@login_required
@role_required("admin")
def delete_employee(id):
    mongo.db.employees.delete_one({"_id": ObjectId(id)})
    flash("Employee deleted successfully!", "danger")
    return redirect(url_for("employee.list_employees"))
# -------- EDIT EMPLOYEE --------
@employee_bp.route("/employees/edit/<id>", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_employee(id):
    employee = mongo.db.employees.find_one({"_id": ObjectId(id)})

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        department = request.form.get("department")
        role = request.form.get("role")

        mongo.db.employees.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "name": name,
                "email": email,
                "department": department,
                "role": role
            }}
        )
        flash("Employee updated successfully!", "success")
        return redirect(url_for("employee.list_employees"))

    return render_template("employees/edit.html", employee=employee)
# -------- VIEW EMPLOYEE PROFILE (ADMIN ONLY) --------
@employee_bp.route("/employees/view/<id>")
@login_required
@role_required("admin")
def view_employee(id):
    employee = mongo.db.employees.find_one({"_id": ObjectId(id)})
    return render_template("employees/profile.html", employee=employee)
# -------- CHANGE PASSWORD --------
@employee_bp.route("/profile/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        employee = mongo.db.employees.find_one({"email": current_user.email})

        if not employee:
            flash("Employee not found.")
            return redirect(url_for("employee.my_profile"))

        if not check_password_hash(employee.get("password", ""), old_password):
            flash("Old password is incorrect.")
            return redirect(url_for("employee.change_password"))

        if new_password != confirm_password:
            flash("New passwords do not match.")
            return redirect(url_for("employee.change_password"))

        mongo.db.employees.update_one(
            {"email": current_user.email},
            {"$set": {"password": generate_password_hash(new_password)}}
        )

        flash("Password updated successfully!")
        return redirect(url_for("employee.my_profile"))

    return render_template("employees/change_password.html")
# -------- MY PROFILE --------
@employee_bp.route("/profile")
@login_required
def my_profile():
    employee = mongo.db.employees.find_one({"email": current_user.email})

    if not employee:
        employee = {
            "name": current_user.username,
            "email": current_user.email,
            "department": "N/A",
            "role": current_user.role
        }

    return render_template("employees/profile.html", employee=employee)
