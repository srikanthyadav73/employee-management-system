from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensions import mongo
from bson.objectid import ObjectId
from utils.decorators import role_required
from flask_login import current_user
from werkzeug.security import generate_password_hash


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

        # Insert into employees collection
        mongo.db.employees.insert_one({
            "name": name,
            "email": email,
            "department": department,
            "role": role
        })

        # ALSO create login account in users collection
        mongo.db.users.insert_one({
            "username": name,
            "email": email,
            "password": generate_password_hash("123456"),  # default password
            "role": role
        })

        flash("Employee Added & Login Created!")
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
# -------- MY PROFILE --------
@employee_bp.route("/profile")
@login_required
def my_profile():
    # First try to find in employees collection
    employee = mongo.db.employees.find_one({"email": current_user.email})

    # If not found and user is admin or manager
    if not employee:
        employee = {
            "name": current_user.username,
            "email": current_user.email,
            "department": "N/A",
            "role": current_user.role
        }

    return render_template("employees/profile.html", employee=employee)