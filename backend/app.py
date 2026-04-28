from flask import Flask
from flask_cors import CORS

from routes.auth import auth_routes
from routes.expenses import expense_routes
from routes.categories import category_routes
from routes.budgets import budget_routes
from routes.reports import report_routes
from routes.audit_logs import audit_log_routes
from routes.admin import admin_routes

app = Flask(__name__)
CORS(app)

app.register_blueprint(auth_routes)
app.register_blueprint(expense_routes)
app.register_blueprint(category_routes)
app.register_blueprint(budget_routes)
app.register_blueprint(report_routes)
app.register_blueprint(audit_log_routes)
app.register_blueprint(admin_routes)

if __name__ == "__main__":
    app.run(debug=True)