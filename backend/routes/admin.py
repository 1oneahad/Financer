from flask import Blueprint, request, jsonify
from db import supabase
from routes.audit_logs import log_audit_action
from routes.budgets import _end_date_for_period, _period_from_dates, normalize_budget_rows
from routes.common import is_positive_amount, is_positive_int, looks_like_date, parse_limit


admin_routes = Blueprint("admin", __name__)
VALID_ROLES = {"basic", "premium", "admin"}


def _public_user(user):
    return {
        "user_id": user.get("user_id"),
        "username": user.get("username"),
        "email": user.get("email"),
        "role": user.get("role"),
        "created_at": user.get("created_at"),
    }


def _ids(values):
    result = []
    for value in values:
        if is_positive_int(value):
            result.append(int(value))
    return sorted(set(result))


def _row_map(table, key, ids, columns="*"):
    clean_ids = _ids(ids)
    if not clean_ids:
        return {}

    response = supabase.table(table).select(columns).in_(key, clean_ids).execute()
    return {int(row[key]): row for row in (response.data or []) if row.get(key) is not None}


def _user_label(user_id, users):
    user = users.get(int(user_id)) if is_positive_int(user_id) else None
    if not user:
        return f"Deleted user #{user_id}" if user_id else "System"
    return f"{user.get('username') or user.get('email') or 'User'} ({user.get('role', 'user')})"


def _category_label(category_id, categories):
    category = categories.get(int(category_id)) if is_positive_int(category_id) else None
    return category.get("name") if category else f"Deleted category #{category_id}"


def _format_audit_target(log, users, categories, targets):
    table = log.get("target_table")
    target_id = log.get("target_id")
    row = targets.get(table, {}).get(int(target_id)) if is_positive_int(target_id) else None

    if not row:
        return {
            "id": target_id,
            "table": table,
            "label": f"{table} #{target_id}",
            "detail": "Target record no longer exists",
            "exists": False,
        }

    if table == "users":
        return {
            "id": target_id,
            "table": table,
            "label": row.get("username") or row.get("email") or f"User #{target_id}",
            "detail": f"{row.get('email', 'No email')} - {row.get('role', 'user')}",
            "exists": True,
        }

    if table == "categories":
        created_by = row.get("created_by")
        return {
            "id": target_id,
            "table": table,
            "label": row.get("name") or f"Category #{target_id}",
            "detail": "Default category" if row.get("is_default") else f"Created by {_user_label(created_by, users)}",
            "exists": True,
        }

    if table == "expenses":
        return {
            "id": target_id,
            "table": table,
            "label": f"{row.get('amount')} on {row.get('expense_date')}",
            "detail": f"{_user_label(row.get('user_id'), users)} - {_category_label(row.get('category_id'), categories)}",
            "exists": True,
        }

    if table == "budgets":
        budget = normalize_budget_rows([row])[0]
        return {
            "id": target_id,
            "table": table,
            "label": f"{budget.get('amount_limit')} {budget.get('period', 'budget')}",
            "detail": f"{_user_label(budget.get('user_id'), users)} - {_category_label(budget.get('category_id'), categories)}",
            "exists": True,
        }

    if table == "reports":
        return {
            "id": target_id,
            "table": table,
            "label": row.get("report_type") or f"Report #{target_id}",
            "detail": f"{_user_label(row.get('user_id'), users)} - {row.get('date_from')} to {row.get('date_to')}",
            "exists": True,
        }

    return {
        "id": target_id,
        "table": table,
        "label": f"{table} #{target_id}",
        "detail": "No formatter available for this target type",
        "exists": True,
    }


def _get_admin_user(admin_user_id):
    if not is_positive_int(admin_user_id):
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


@admin_routes.route("/admin/audit-logs", methods=["GET"])
def admin_audit_logs():
    admin_user_id = request.args.get("admin_user_id")
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    limit, limit_error = parse_limit(request.args.get("limit", "100"))
    if limit_error:
        return jsonify({"message": limit_error}), 400

    logs_response = supabase.table("audit_log") \
        .select("*") \
        .order("action_time", desc=True) \
        .limit(limit) \
        .execute()

    logs = logs_response.data or []
    user_ids = [log.get("user_id") for log in logs if log.get("user_id")]

    target_ids_by_table = {}
    for log in logs:
        target_ids_by_table.setdefault(log.get("target_table"), []).append(log.get("target_id"))

    targets = {
        "users": _row_map("users", "user_id", target_ids_by_table.get("users", []), "user_id, username, email, role"),
        "categories": _row_map("categories", "category_id", target_ids_by_table.get("categories", []), "category_id, name, is_default, created_by"),
        "expenses": _row_map("expenses", "expense_id", target_ids_by_table.get("expenses", []), "expense_id, user_id, category_id, amount, expense_date, notes"),
        "budgets": _row_map("budgets", "budget_id", target_ids_by_table.get("budgets", []), "budget_id, user_id, category_id, amount_limit, start_date, end_date"),
        "reports": _row_map("reports", "report_id", target_ids_by_table.get("reports", []), "report_id, user_id, report_type, date_from, date_to, generated_at"),
    }

    for table_targets in targets.values():
        for row in table_targets.values():
            user_ids.extend([row.get("user_id"), row.get("created_by")])

    users = _row_map("users", "user_id", user_ids, "user_id, username, email, role")
    categories = _row_map("categories", "category_id", [
        row.get("category_id")
        for table_targets in targets.values()
        for row in table_targets.values()
    ], "category_id, name")

    enriched_logs = []
    for log in logs:
        enriched_logs.append({
            **log,
            "actor": {
                "id": log.get("user_id"),
                "label": _user_label(log.get("user_id"), users),
            },
            "target": _format_audit_target(log, users, categories, targets),
        })

    return jsonify(enriched_logs)


@admin_routes.route("/admin/users", methods=["GET"])
def list_users():
    admin_user_id = request.args.get("admin_user_id")
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    response = supabase.table("users") \
        .select("user_id, username, email, role, created_at") \
        .order("user_id") \
        .execute()

    return jsonify(response.data)


@admin_routes.route('/admin/expenses', methods=['GET'])
def list_expenses():
    admin_user_id = request.args.get('admin_user_id')
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    resp = supabase.table('expenses').select('*').order('expense_date', desc=True).execute()
    return jsonify(resp.data)


@admin_routes.route('/admin/expenses/<expense_id>', methods=['DELETE'])
def admin_delete_expense(expense_id):
    data = request.get_json(silent=True) or {}
    admin_user_id = data.get('admin_user_id') or request.args.get('admin_user_id')
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    if not is_positive_int(expense_id):
        return jsonify({'message': 'expense_id must be a positive integer'}), 400

    existing = supabase.table('expenses').select('*').eq('expense_id', expense_id).limit(1).execute()
    if not existing.data:
        return jsonify({'message': 'expense not found'}), 404

    resp = supabase.table('expenses').delete().eq('expense_id', expense_id).execute()
    log_audit_action(admin_user_id, 'DELETE', 'expenses', expense_id)
    return jsonify({'message': 'Expense deleted', 'deleted': resp.data})


@admin_routes.route('/admin/expenses/<expense_id>', methods=['PUT'])
def admin_update_expense(expense_id):
    data = request.get_json(silent=True) or {}
    admin_user_id = data.get('admin_user_id')
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    if not is_positive_int(expense_id):
        return jsonify({'message': 'expense_id must be a positive integer'}), 400

    updates = {}
    for key in ('amount', 'category_id', 'notes', 'expense_date', 'user_id'):
        if key in data:
            if key in {'category_id', 'user_id'} and not is_positive_int(data.get(key)):
                return jsonify({"message": f"{key} must be a positive integer"}), 400
            if key == 'amount' and not is_positive_amount(data.get('amount')):
                return jsonify({'message': 'amount must be greater than 0'}), 400
            if key == 'expense_date' and not looks_like_date(data.get('expense_date')):
                return jsonify({'message': 'expense_date must look like YYYY-MM-DD'}), 400
            if key == 'notes' and data.get('notes') is not None and not isinstance(data.get('notes'), str):
                return jsonify({'message': 'notes must be text'}), 400
            updates[key] = data[key]

    if not updates:
        return jsonify({'message': 'At least one field required to update'}), 400

    if 'amount' in updates:
        updates['amount'] = float(updates['amount'])
    for key in ('category_id', 'user_id'):
        if key in updates:
            updates[key] = int(updates[key])

    resp = supabase.table('expenses').update(updates).eq('expense_id', expense_id).execute()
    log_audit_action(admin_user_id, 'UPDATE', 'expenses', expense_id)
    return jsonify({'message': 'Expense updated', 'data': resp.data})


@admin_routes.route('/admin/categories', methods=['GET'])
def admin_list_categories():
    admin_user_id = request.args.get('admin_user_id')
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    resp = supabase.table('categories').select('*').order('category_id').execute()
    return jsonify(resp.data)


@admin_routes.route('/admin/categories/<category_id>', methods=['DELETE'])
def admin_delete_category(category_id):
    data = request.get_json(silent=True) or {}
    admin_user_id = data.get('admin_user_id') or request.args.get('admin_user_id')
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    if not is_positive_int(category_id):
        return jsonify({'message': 'category_id must be a positive integer'}), 400

    existing = supabase.table('categories').select('*').eq('category_id', category_id).limit(1).execute()
    if not existing.data:
        return jsonify({'message': 'category not found'}), 404
    resp = supabase.table('categories').delete().eq('category_id', category_id).execute()
    log_audit_action(admin_user_id, 'DELETE', 'categories', category_id)
    return jsonify({'message': 'Category deleted', 'deleted': resp.data})


@admin_routes.route('/admin/categories/<category_id>', methods=['PUT'])
def admin_update_category(category_id):
    data = request.get_json(silent=True) or {}
    admin_user_id = data.get('admin_user_id')
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    if not is_positive_int(category_id):
        return jsonify({'message': 'category_id must be a positive integer'}), 400

    updates = {}
    for key in ('name', 'description', 'is_default', 'created_by'):
        if key in data:
            if key == 'name':
                if not isinstance(data.get('name'), str) or len(data.get('name').strip()) < 2:
                    return jsonify({'message': 'name must be at least 2 characters'}), 400
                updates[key] = data.get('name').strip()
                continue
            if key == 'description' and data.get('description') is not None and not isinstance(data.get('description'), str):
                return jsonify({'message': 'description must be text'}), 400
            if key == 'is_default' and not isinstance(data.get('is_default'), bool):
                return jsonify({'message': 'is_default must be true or false'}), 400
            if key == 'created_by' and data.get('created_by') is not None and not is_positive_int(data.get('created_by')):
                return jsonify({'message': 'created_by must be a positive integer or null'}), 400
            updates[key] = data[key]

    if not updates:
        return jsonify({'message': 'At least one field required to update'}), 400

    resp = supabase.table('categories').update(updates).eq('category_id', category_id).execute()
    log_audit_action(admin_user_id, 'UPDATE', 'categories', category_id)
    return jsonify({'message': 'Category updated', 'data': resp.data})


@admin_routes.route('/admin/budgets', methods=['GET'])
def admin_list_budgets():
    admin_user_id = request.args.get('admin_user_id')
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    resp = supabase.table('budgets').select('*').order('start_date', desc=True).execute()
    return jsonify(normalize_budget_rows(resp.data))


@admin_routes.route('/admin/budgets/<budget_id>', methods=['DELETE'])
def admin_delete_budget(budget_id):
    data = request.get_json(silent=True) or {}
    admin_user_id = data.get('admin_user_id') or request.args.get('admin_user_id')
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    if not is_positive_int(budget_id):
        return jsonify({'message': 'budget_id must be a positive integer'}), 400

    existing = supabase.table('budgets').select('*').eq('budget_id', budget_id).limit(1).execute()
    if not existing.data:
        return jsonify({'message': 'budget not found'}), 404
    resp = supabase.table('budgets').delete().eq('budget_id', budget_id).execute()
    log_audit_action(admin_user_id, 'DELETE', 'budgets', budget_id)
    return jsonify({'message': 'Budget deleted', 'deleted': resp.data})


@admin_routes.route('/admin/budgets/<budget_id>', methods=['PUT'])
def admin_update_budget(budget_id):
    data = request.get_json(silent=True) or {}
    admin_user_id = data.get('admin_user_id')
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    if not is_positive_int(budget_id):
        return jsonify({'message': 'budget_id must be a positive integer'}), 400

    existing = None
    if 'period' in data or 'start_date' in data:
        existing = supabase.table('budgets').select('*').eq('budget_id', budget_id).limit(1).execute()
        if not existing.data:
            return jsonify({'message': 'budget not found'}), 404

    updates = {}
    period = data.get('period')
    for key in ('user_id', 'category_id', 'amount_limit', 'start_date'):
        if key in data:
            if key in {'user_id', 'category_id'} and not is_positive_int(data.get(key)):
                return jsonify({'message': f'{key} must be a positive integer'}), 400
            if key == 'amount_limit' and not is_positive_amount(data.get('amount_limit')):
                return jsonify({'message': 'amount_limit must be greater than 0'}), 400
            if key == 'start_date' and not looks_like_date(data.get('start_date')):
                return jsonify({'message': 'start_date must look like YYYY-MM-DD'}), 400
            updates[key] = data[key]

    if period is not None and period not in {'weekly', 'monthly'}:
        return jsonify({'message': 'period must be weekly or monthly'}), 400

    if period is not None or 'start_date' in updates:
        current_row = existing.data[0]
        next_start_date = updates.get('start_date', current_row.get('start_date'))
        next_period = period or _period_from_dates(current_row.get('start_date'), current_row.get('end_date'))

        if next_period not in {'weekly', 'monthly'}:
            return jsonify({'message': 'period must be provided when updating a custom budget window'}), 400

        updates['end_date'] = _end_date_for_period(next_start_date, next_period)

    if not updates:
        return jsonify({'message': 'At least one field required to update'}), 400

    for key in ('user_id', 'category_id'):
        if key in updates:
            updates[key] = int(updates[key])
    if 'amount_limit' in updates:
        updates['amount_limit'] = float(updates['amount_limit'])

    resp = supabase.table('budgets').update(updates).eq('budget_id', budget_id).execute()
    log_audit_action(admin_user_id, 'UPDATE', 'budgets', budget_id)
    return jsonify({'message': 'Budget updated', 'data': normalize_budget_rows(resp.data)})


@admin_routes.route('/admin/reports', methods=['GET'])
def admin_list_reports():
    admin_user_id = request.args.get('admin_user_id')
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    resp = supabase.table('reports').select('*').order('generated_at', desc=True).execute()
    return jsonify(resp.data)


@admin_routes.route('/admin/reports/<report_id>', methods=['DELETE'])
def admin_delete_report(report_id):
    data = request.get_json(silent=True) or {}
    admin_user_id = data.get('admin_user_id') or request.args.get('admin_user_id')
    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    if not is_positive_int(report_id):
        return jsonify({'message': 'report_id must be a positive integer'}), 400

    existing = supabase.table('reports').select('*').eq('report_id', report_id).limit(1).execute()
    if not existing.data:
        return jsonify({'message': 'report not found'}), 404
    resp = supabase.table('reports').delete().eq('report_id', report_id).execute()
    log_audit_action(admin_user_id, 'DELETE', 'reports', report_id)
    return jsonify({'message': 'Report deleted', 'deleted': resp.data})


@admin_routes.route("/admin/users/<user_id>/role", methods=["PUT"])
def update_user_role(user_id):
    data = request.get_json(silent=True) or {}
    admin_user_id = data.get("admin_user_id")

    _, error = _get_admin_user(admin_user_id)
    if error:
        return jsonify(error[0]), error[1]

    if not is_positive_int(user_id):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    role = data.get("role")
    role = role.strip().lower() if isinstance(role, str) else role
    if role not in VALID_ROLES:
        return jsonify({"message": "role must be basic, premium, or admin"}), 400

    if int(user_id) == int(admin_user_id) and role != "admin":
        return jsonify({"message": "You cannot remove your own admin role while logged in."}), 400

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

    if not is_positive_int(user_id):
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
