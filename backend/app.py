from flask import Flask
from flask_cors import CORS

from routes.auth import auth_routes
from routes.expenses import expense_routes
from routes.categories import category_routes

app = Flask(__name__)
CORS(app)

app.register_blueprint(auth_routes)
app.register_blueprint(expense_routes)
app.register_blueprint(category_routes)

if __name__ == "__main__":
    app.run(debug=True)