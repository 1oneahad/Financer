from flask import Blueprint, request, jsonify
from db import supabase
from routes.audit_logs import log_audit_action

expense_routes = Blueprint('expenses', __name__)


@expense_routes.route('/add-expense', methods=['POST'])
def add_expense():
    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    category_id = data.get("category_id")
    amount = data.get("amount")
    expense_date = data.get("expense_date")

    if not user_id or not category_id or amount is None or not expense_date:
        return jsonify({"message": "user_id, category_id, amount, and expense_date are required"}), 400

    try:
        response = supabase.table("expenses").insert({
            "user_id": user_id,
            "category_id": category_id,
            "amount": amount,
            "expense_date": expense_date,
            "notes": data.get("notes", "")
        }).execute()

        created = response.data[0] if response.data else {}
        log_audit_action(user_id, "INSERT", "expenses", created.get("expense_id"))

        return jsonify({
            "message": "Expense added",
            "data": response.data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@expense_routes.route('/expenses/<user_id>', methods=['GET'])
def get_expenses(user_id):
    try:
        response = supabase.table("expenses") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("expense_date", desc=True) \
            .execute()

        return jsonify(response.data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@expense_routes.route('/expense/<expense_id>', methods=['GET'])
def get_expense(expense_id):
    response = supabase.table("expenses") \
        .select("*") \
        .eq("expense_id", expense_id) \
        .limit(1) \
        .execute()

    if not response.data:
        return jsonify({"message": "Expense not found"}), 404

    return jsonify(response.data[0])




@expense_routes.route('/delete-expense/<expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    data = request.get_json(silent=True) or {}

    response = supabase.table("expenses") \
        .delete() \
        .eq("expense_id", expense_id) \
        .execute()

    deleted = response.data[0] if response.data else {}
    audit_user_id = data.get("user_id", deleted.get("user_id"))
    log_audit_action(audit_user_id, "DELETE", "expenses", expense_id)

    return jsonify({
        "message": "Expense deleted",
        "data": response.data
    })




@expense_routes.route('/update-expense/<expense_id>', methods=['PUT'])
def update_expense(expense_id):
    data = request.get_json(silent=True) or {}

    updates = {}
    for key in ("amount", "category_id", "notes", "expense_date"):
        if key in data:
            updates[key] = data[key]

    if not updates:
        return jsonify({"message": "At least one updatable field is required"}), 400

    try:
        response = supabase.table("expenses") \
            .update(updates) \
            .eq("expense_id", expense_id) \
            .execute()

        updated = response.data[0] if response.data else {}
        audit_user_id = data.get("user_id", updated.get("user_id"))
        log_audit_action(audit_user_id, "UPDATE", "expenses", expense_id)

        return jsonify({
            "message": "Expense updated",
            "data": response.data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


