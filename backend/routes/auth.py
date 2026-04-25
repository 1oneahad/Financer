from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from db import supabase

auth_routes = Blueprint('auth', __name__)


def _public_user(user):
    return {key: value for key, value in user.items() if key != "password"}


def _verify_password(stored_password, plain_password):
    if not stored_password:
        return False

    if "$" in stored_password:
        try:
            return check_password_hash(stored_password, plain_password)
        except ValueError:
            return False

    return stored_password == plain_password


@auth_routes.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"message": "username, email, and password are required"}), 400

    password_hash = generate_password_hash(password)

    try:
        response = supabase.table("users").insert({
            "username": username,
            "email": email,
            "password": password_hash
        }).execute()

        created_user = response.data[0] if response.data else {}

        return jsonify({
            "message": "User registered",
            "data": _public_user(created_user)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@auth_routes.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "email and password are required"}), 400

    try:
        response = supabase.table("users") \
            .select("*") \
            .eq("email", email) \
            .limit(1) \
            .execute()

        if not response.data:
            return jsonify({"message": "Invalid credentials"}), 401

        user = response.data[0]
        stored_password = user.get("password", "")

        if not _verify_password(stored_password, password):
            return jsonify({"message": "Invalid credentials"}), 401

        # If an older plain-text password matched, upgrade it to a hash.
        if stored_password == password:
            supabase.table("users").update({
                "password": generate_password_hash(password)
            }).eq("user_id", user["user_id"]).execute()

        return jsonify({
            "message": "Login successful",
            "user": _public_user(user)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
