from flask import Blueprint, request, jsonify
from db import supabase

auth_routes = Blueprint('auth', __name__)


@auth_routes.route('/register', methods=['POST'])
def register():
    data = request.json

    response = supabase.table("users").insert({
        "username": data["username"],
        "email": data["email"],
        "password": data["password"]
    }).execute()

    return jsonify({
        "message": "User registered",
        "data": response.data
    })



@auth_routes.route('/login', methods=['POST'])
def login():
    data = request.json

    response = supabase.table("users") \
        .select("*") \
        .eq("email", data["email"]) \
        .eq("password", data["password"]) \
        .execute()

    if response.data:
        return jsonify({
            "message": "Login successful",
            "user": response.data[0]
        })
    else:
        return jsonify({"message": "Invalid credentials"}), 401
