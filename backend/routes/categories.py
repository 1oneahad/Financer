from flask import Blueprint, request, jsonify
from db import supabase

category_routes = Blueprint('categories', __name__)


@category_routes.route('/categories', methods=['GET'])
def get_categories():
    response = supabase.table("categories").select("*").execute()
    return jsonify(response.data)



@category_routes.route('/add-category', methods=['POST'])
def add_category():
    data = request.json

    response = supabase.table("categories").insert({
        "name": data["name"],
        "description": data.get("description", ""),
        "is_default": False,
        "created_by": data.get("user_id")
    }).execute()

    return jsonify({
        "message": "Category added",
        "data": response.data
    })