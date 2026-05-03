from flask import Blueprint, request, jsonify
from db import supabase
from routes.audit_logs import log_audit_action
from routes.common import is_positive_int

category_routes = Blueprint("categories", __name__)


def _get_user_role(user_id):
    response = supabase.table("users") \
        .select("user_id, role") \
        .eq("user_id", user_id) \
        .limit(1) \
        .execute()

    if not response.data:
        return None

    return response.data[0].get("role")


@category_routes.route("/categories", methods=["GET"])
def get_categories():
    user_id = request.args.get("user_id")
    query = supabase.table("categories").select("*")

    if user_id is not None:
        if not is_positive_int(user_id):
            return jsonify({"message": "user_id must be a positive integer"}), 400
        query = query.or_(f"is_default.eq.true,created_by.eq.{int(user_id)}")

    response = query.order("category_id").execute()
    return jsonify(response.data)

@category_routes.route("/add-category", methods=["POST"])
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

    if not is_positive_int(created_by):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    role = _get_user_role(created_by)
    if role not in ("premium", "admin"):
        return jsonify({"message": "premium access required to add categories"}), 403

    try:
        is_default = role == "admin"
        response = supabase.table("categories").insert({
            "name": name,
            "description": data.get("description") or "",
            "is_default": is_default,
            "created_by": created_by,
        }).execute()

        created = response.data[0] if response.data else {}
        log_audit_action(int(created_by), "INSERT", "categories", created.get("category_id"))

        return jsonify({
            "message": "Category added",
            "data": response.data,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@category_routes.route("/update-category/<category_id>", methods=["PUT"])
def update_category(category_id):
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")

    if not is_positive_int(category_id):
        return jsonify({"message": "category_id must be a positive integer"}), 400
    if not is_positive_int(user_id):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    role = _get_user_role(user_id)
    if role not in ("premium", "admin"):
        return jsonify({"message": "premium access required to update categories"}), 403

    existing = supabase.table("categories") \
        .select("*") \
        .eq("category_id", category_id) \
        .limit(1) \
        .execute()

    if not existing.data:
        return jsonify({"message": "Category not found"}), 404

    category = existing.data[0]
    if category.get("is_default"):
        return jsonify({"message": "System categories cannot be edited here"}), 403
    if int(category.get("created_by") or 0) != int(user_id):
        return jsonify({"message": "You can only update your own categories"}), 403

    updates = {}
    for key in ("name", "description"):
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

    response = supabase.table("categories") \
        .update(updates) \
        .eq("category_id", category_id) \
        .execute()

    log_audit_action(user_id, "UPDATE", "categories", category_id)

    return jsonify({
        "message": "Category updated",
        "data": response.data,
    })


@category_routes.route("/delete-category/<category_id>", methods=["DELETE"])
def delete_category(category_id):
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")

    if not is_positive_int(category_id):
        return jsonify({"message": "category_id must be a positive integer"}), 400
    if not is_positive_int(user_id):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    role = _get_user_role(user_id)
    if role not in ("premium", "admin"):
        return jsonify({"message": "premium access required to delete categories"}), 403

    existing = supabase.table("categories") \
        .select("*") \
        .eq("category_id", category_id) \
        .limit(1) \
        .execute()

    if not existing.data:
        return jsonify({"message": "Category not found"}), 404

    deleted = existing.data[0]
    if deleted.get("is_default"):
        return jsonify({"message": "System categories cannot be deleted here"}), 403
    if int(deleted.get("created_by") or 0) != int(user_id):
        return jsonify({"message": "You can only delete your own categories"}), 403

    response = supabase.table("categories") \
        .delete() \
        .eq("category_id", category_id) \
        .execute()

    log_audit_action(user_id, "DELETE", "categories", category_id)

    return jsonify({
        "message": "Category deleted",
        "data": response.data,
    })
