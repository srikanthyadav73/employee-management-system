from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"])

        # Handle both admin and employee
        self.username = user_data.get("username") or user_data.get("name")
        self.email = user_data.get("email")
        self.role = user_data.get("role", "employee")