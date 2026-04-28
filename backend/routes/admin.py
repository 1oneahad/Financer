from flask import Blueprint, request, jsonify
from db import supabase
from routes.audit_logs import log_audit_action


admin_routes = Blueprint("admin", __name__)
VALID_ROLES = {"basic", "premium", "admin"}


def _valid_id(value):
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False


def _public_user(user):
    return {
        "user_id": user.get("user_id"),
        "username": user.get("username"),
        "email": user.get("email"),
        "role": user.get("role"),
        "created_at": user.get("created_at"),
    }


def _get_admin_user(admin_user_id):
    if not _valid_id(admin_user_id):
        return None, ({"message": "admin_user_id must be a positive integer"}, 400)

    response = supabase.table("users") \
        .select("user_id, username, role") \
        .eq("user_id", admin_user_id) \
        .limit(1) \
        .execute()

    if not response.data:
        return None, ({"message": "admin_user_id not found"}, 404)

    admin_user = response.data[0]
    if admin_user.get("role") != "admin":
        return None, ({"message": "admin access required"}, 403)

    return admin_user, None


@admin_routes.route("/admin/users", methods=["GET"])
def list_users():
    admin_user_id = request.args.get("admin_user_id")
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    try:
        response = supabase.table("users") \
            .select("user_id, username, email, role, created_at") \
            .order("user_id") \
            .execute()

        return jsonify(response.data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_routes.route("/admin/users/<user_id>/role", methods=["PUT"])
def update_user_role(user_id):
    data = request.get_json(silent=True) or {}
    admin_user_id = data.get("admin_user_id")

    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    if not _valid_id(user_id):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    role = data.get("role")
    if role not in VALID_ROLES:
        return jsonify({"message": "role must be basic, premium, or admin"}), 400

    existing = supabase.table("users") \
        .select("user_id, username, email, role") \
        .eq("user_id", user_id) \
        .limit(1) \
        .execute()

    if not existing.data:
        return jsonify({"message": "user_id not found"}), 404

    try:
        response = supabase.table("users") \
            .update({"role": role}) \
            .eq("user_id", user_id) \
            .execute()

        updated_user = response.data[0] if response.data else existing.data[0]
        log_audit_action(admin_user_id, "UPDATE", "users", user_id)

        return jsonify({
            "message": "User role updated",
            "data": _public_user(updated_user),
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_routes.route("/admin/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    data = request.get_json(silent=True) or {}
    admin_user_id = data.get("admin_user_id")

    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    if not _valid_id(user_id):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    existing = supabase.table("users") \
        .select("user_id, username, email, role") \
        .eq("user_id", user_id) \
        .limit(1) \
        .execute()

    if not existing.data:
        return jsonify({"message": "user_id not found"}), 404

    try:
        response = supabase.table("users") \
            .delete() \
            .eq("user_id", user_id) \
            .execute()

        log_audit_action(admin_user_id, "DELETE", "users", user_id)

        return jsonify({
            "message": "User deleted",
            "data": _public_user(existing.data[0]),
            "deleted": response.data,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500