from flask import Blueprint, request, jsonify
from db import supabase
from routes.audit_logs import log_audit_action

category_routes = Blueprint('categories', __name__)


def _valid_id(value):
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False


def _get_user_role(user_id):
    response = supabase.table("users") \
        .select("user_id, role") \
        .eq("user_id", user_id) \
        .limit(1) \
        .execute()

    if not response.data:
        return None

    return response.data[0].get("role")


@category_routes.route('/categories', methods=['GET'])
def get_categories():
    response = supabase.table("categories") \
        .select("*") \
        .order("category_id") \
        .execute()

    return jsonify(response.data)




@category_routes.route('/add-category', methods=['POST'])
def add_category():
    data = request.get_json(silent=True) or {}

    name = data.get("name")
    if not name:
        return jsonify({"message": "name is required"}), 400

    name = name.strip() if isinstance(name, str) else name
    if not name or len(name) < 2:
        return jsonify({"message": "name must be at least 2 characters"}), 400

    created_by = data.get("user_id")
    if created_by is None:
        return jsonify({"message": "user_id is required to add a category"}), 400

    if not _valid_id(created_by):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    if _get_user_role(created_by) != "premium":
        return jsonify({"message": "premium access required to add categories"}), 403

    try:
        response = supabase.table("categories").insert({
            "name": name,
            "description": data.get("description", ""),
            "is_default": data.get("is_default", False),
            "created_by": created_by,
        }).execute()

        created = response.data[0] if response.data else {}
        log_audit_action(created_by, "INSERT", "categories", created.get("category_id"))

        return jsonify({
            "message": "Category added",
            "data": response.data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@category_routes.route('/update-category/<category_id>', methods=['PUT'])
def update_category(category_id):
    data = request.get_json(silent=True) or {}

    if not _valid_id(category_id):
        return jsonify({"message": "category_id must be a positive integer"}), 400

    updates = {}
    for key in ("name", "description", "is_default"):
        if key in data:
            if key == "name" and isinstance(data.get("name"), str):
                value = data.get("name").strip()
                if not value or len(value) < 2:
                    return jsonify({"message": "name must be at least 2 characters"}), 400
                updates[key] = value
                continue
            updates[key] = data[key]

    if not updates:
        return jsonify({"message": "At least one updatable field is required"}), 400

    try:
        response = supabase.table("categories") \
            .update(updates) \
            .eq("category_id", category_id) \
            .execute()

        updated = response.data[0] if response.data else {}
        audit_user_id = data.get("user_id", updated.get("created_by"))
        log_audit_action(audit_user_id, "UPDATE", "categories", category_id)

        return jsonify({
            "message": "Category updated",
            "data": response.data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@category_routes.route('/delete-category/<category_id>', methods=['DELETE'])
def delete_category(category_id):
    data = request.get_json(silent=True) or {}

    if not _valid_id(category_id):
        return jsonify({"message": "category_id must be a positive integer"}), 400

    response = supabase.table("categories") \
        .delete() \
        .eq("category_id", category_id) \
        .execute()

    deleted = response.data[0] if response.data else {}
    audit_user_id = data.get("user_id", deleted.get("created_by"))
    log_audit_action(audit_user_id, "DELETE", "categories", category_id)

    return jsonify({
        "message": "Category deleted",
        "data": response.data
    })