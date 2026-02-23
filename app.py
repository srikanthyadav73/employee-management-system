# ================= IMPORTS =================
from flask import Flask, render_template
from flask_login import LoginManager, login_required, current_user
from bson.objectid import ObjectId

from models.user import User
from utils.decorators import role_required
from flask import redirect, url_for
from flask_mail import Mail
# Import Blueprints
from routes.auth import auth_bp
from routes.employee import employee_bp
from routes.department import department_bp
from collections import defaultdict
from extensions import mongo, mail




# ================= APP CONFIG =================
app = Flask(__name__)

app.config["SECRET_KEY"] = "supersecretkey"
app.config["MONGO_URI"] = "mongodb://localhost:27017/employee_db"

app.config["SECRET_KEY"] = "supersecretkey"
app.config["MONGO_URI"] = "mongodb://localhost:27017/employee_db"
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "srikanthyadavgorla72@gmail.com"
app.config["MAIL_PASSWORD"] = "cpybgjjlunrcpwwy"

# Initialize Extensions
mongo.init_app(app)
mail.init_app(app)



# ================= LOGIN MANAGER =================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    from bson.objectid import ObjectId

    # Check users collection
    user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})

    # If not found, check employees collection
    if not user_data:
        user_data = mongo.db.employees.find_one({"_id": ObjectId(user_id)})

    if user_data:
        return User(user_data)

    return None


# ================= DASHBOARD =================

@app.route("/dashboard")
@login_required
def dashboard():
    total_users = mongo.db.users.count_documents({})
    total_employees = mongo.db.employees.count_documents({})
    total_departments = mongo.db.departments.count_documents({})

    from collections import defaultdict

    employees = list(mongo.db.employees.find())
    dept_count = defaultdict(int)

    for emp in employees:
        dept_count[emp.get("department", "Other")] += 1

    dept_labels = list(dept_count.keys())
    dept_values = list(dept_count.values())

    return render_template(
        "dashboard.html",
        username=current_user.username,
        role=current_user.role,
        total_users=total_users,
        total_employees=total_employees,
        total_departments=total_departments,
        dept_labels=dept_labels,
        dept_values=dept_values
    )

# ================= HOME ROUTE =================

@app.route("/")
def home():
    return redirect(url_for("auth.login"))

# ================= REGISTER BLUEPRINTS =================
app.register_blueprint(auth_bp)
app.register_blueprint(employee_bp)
app.register_blueprint(department_bp)

# ================= RUN APP =================
if __name__ == "__main__":
    app.run(debug=True)
5