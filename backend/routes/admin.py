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


@admin_routes.route('/admin/expenses', methods=['GET'])
def list_expenses():
    admin_user_id = request.args.get('admin_user_id')
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    try:
        resp = supabase.table('expenses').select('*').order('expense_date', desc=True).execute()
        return jsonify(resp.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_routes.route('/admin/expenses/<expense_id>', methods=['DELETE'])
def admin_delete_expense(expense_id):
    data = request.get_json(silent=True) or {}
    admin_user_id = data.get('admin_user_id') or request.args.get('admin_user_id')
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    if not _valid_id(expense_id):
        return jsonify({'message': 'expense_id must be a positive integer'}), 400

    try:
        existing = supabase.table('expenses').select('*').eq('expense_id', expense_id).limit(1).execute()
        if not existing.data:
            return jsonify({'message': 'expense not found'}), 404

        resp = supabase.table('expenses').delete().eq('expense_id', expense_id).execute()
        log_audit_action(admin_user_id, 'DELETE', 'expenses', expense_id)
        return jsonify({'message': 'Expense deleted', 'deleted': resp.data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_routes.route('/admin/expenses/<expense_id>', methods=['PUT'])
def admin_update_expense(expense_id):
    data = request.get_json(silent=True) or {}
    admin_user_id = data.get('admin_user_id')
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    if not _valid_id(expense_id):
        return jsonify({'message': 'expense_id must be a positive integer'}), 400

    updates = {}
    for key in ('amount', 'category_id', 'notes', 'expense_date', 'user_id'):
        if key in data:
            updates[key] = data[key]

    if not updates:
        return jsonify({'message': 'At least one field required to update'}), 400

    try:
        resp = supabase.table('expenses').update(updates).eq('expense_id', expense_id).execute()
        log_audit_action(admin_user_id, 'UPDATE', 'expenses', expense_id)
        return jsonify({'message': 'Expense updated', 'data': resp.data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_routes.route('/admin/categories', methods=['GET'])
def admin_list_categories():
    admin_user_id = request.args.get('admin_user_id')
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    try:
        resp = supabase.table('categories').select('*').order('category_id').execute()
        return jsonify(resp.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_routes.route('/admin/categories/<category_id>', methods=['DELETE'])
def admin_delete_category(category_id):
    data = request.get_json(silent=True) or {}
    admin_user_id = data.get('admin_user_id') or request.args.get('admin_user_id')
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    if not _valid_id(category_id):
        return jsonify({'message': 'category_id must be a positive integer'}), 400

    try:
        existing = supabase.table('categories').select('*').eq('category_id', category_id).limit(1).execute()
        if not existing.data:
            return jsonify({'message': 'category not found'}), 404
        resp = supabase.table('categories').delete().eq('category_id', category_id).execute()
        log_audit_action(admin_user_id, 'DELETE', 'categories', category_id)
        return jsonify({'message': 'Category deleted', 'deleted': resp.data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_routes.route('/admin/categories/<category_id>', methods=['PUT'])
def admin_update_category(category_id):
    data = request.get_json(silent=True) or {}
    admin_user_id = data.get('admin_user_id')
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    if not _valid_id(category_id):
        return jsonify({'message': 'category_id must be a positive integer'}), 400

    updates = {}
    for key in ('name', 'description', 'is_default', 'created_by'):
        if key in data:
            updates[key] = data[key]

    if not updates:
        return jsonify({'message': 'At least one field required to update'}), 400

    try:
        resp = supabase.table('categories').update(updates).eq('category_id', category_id).execute()
        log_audit_action(admin_user_id, 'UPDATE', 'categories', category_id)
        return jsonify({'message': 'Category updated', 'data': resp.data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_routes.route('/admin/budgets', methods=['GET'])
def admin_list_budgets():
    admin_user_id = request.args.get('admin_user_id')
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    try:
        resp = supabase.table('budgets').select('*').order('start_date', desc=True).execute()
        return jsonify(resp.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_routes.route('/admin/budgets/<budget_id>', methods=['DELETE'])
def admin_delete_budget(budget_id):
    data = request.get_json(silent=True) or {}
    admin_user_id = data.get('admin_user_id') or request.args.get('admin_user_id')
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    if not _valid_id(budget_id):
        return jsonify({'message': 'budget_id must be a positive integer'}), 400

    try:
        existing = supabase.table('budgets').select('*').eq('budget_id', budget_id).limit(1).execute()
        if not existing.data:
            return jsonify({'message': 'budget not found'}), 404
        resp = supabase.table('budgets').delete().eq('budget_id', budget_id).execute()
        log_audit_action(admin_user_id, 'DELETE', 'budgets', budget_id)
        return jsonify({'message': 'Budget deleted', 'deleted': resp.data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_routes.route('/admin/reports', methods=['GET'])
def admin_list_reports():
    admin_user_id = request.args.get('admin_user_id')
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    try:
        resp = supabase.table('reports').select('*').order('generated_at', desc=True).execute()
        return jsonify(resp.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_routes.route('/admin/reports/<report_id>', methods=['DELETE'])
def admin_delete_report(report_id):
    data = request.get_json(silent=True) or {}
    admin_user_id = data.get('admin_user_id') or request.args.get('admin_user_id')
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    if not _valid_id(report_id):
        return jsonify({'message': 'report_id must be a positive integer'}), 400

    try:
        existing = supabase.table('reports').select('*').eq('report_id', report_id).limit(1).execute()
        if not existing.data:
            return jsonify({'message': 'report not found'}), 404
        resp = supabase.table('reports').delete().eq('report_id', report_id).execute()
        log_audit_action(admin_user_id, 'DELETE', 'reports', report_id)
        return jsonify({'message': 'Report deleted', 'deleted': resp.data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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