from flask import Blueprint, request, jsonify
from db import supabase
from routes.audit_logs import log_audit_action
from routes.common import is_positive_amount, is_positive_int, looks_like_date

expense_routes = Blueprint("expenses", __name__)


@expense_routes.route("/add-expense", methods=["POST"])
def add_expense():
    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    category_id = data.get("category_id")
    amount = data.get("amount")
    expense_date = data.get("expense_date")

    if not user_id or not category_id or amount is None or not expense_date:
        return jsonify({"message": "user_id, category_id, amount, and expense_date are required"}), 400

    if not is_positive_int(user_id):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    if not is_positive_int(category_id):
        return jsonify({"message": "category_id must be a positive integer"}), 400

    if not is_positive_amount(amount):
        return jsonify({"message": "amount must be greater than 0"}), 400

    if not looks_like_date(expense_date):
        return jsonify({"message": "expense_date must look like YYYY-MM-DD"}), 400

    notes = data.get("notes", "")
    if notes is not None and not isinstance(notes, str):
        return jsonify({"message": "notes must be text"}), 400

    try:
        response = supabase.table("expenses").insert({
            "user_id": int(user_id),
            "category_id": int(category_id),
            "amount": float(amount),
            "expense_date": expense_date,
            "notes": notes or "",
        }).execute()

        created = response.data[0] if response.data else {}
        log_audit_action(int(user_id), "INSERT", "expenses", created.get("expense_id"))

        return jsonify({
            "message": "Expense added",
            "data": response.data,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@expense_routes.route("/expenses/<user_id>", methods=["GET"])
def get_expenses(user_id):
    if not is_positive_int(user_id):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    response = supabase.table("expenses") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("expense_date", desc=True) \
        .execute()

    return jsonify(response.data)


@expense_routes.route("/expense/<expense_id>", methods=["GET"])
def get_expense(expense_id):
    if not is_positive_int(expense_id):
        return jsonify({"message": "expense_id must be a positive integer"}), 400

    response = supabase.table("expenses") \
        .select("*") \
        .eq("expense_id", expense_id) \
        .limit(1) \
        .execute()

    if not response.data:
        return jsonify({"message": "Expense not found"}), 404

    return jsonify(response.data[0])

@expense_routes.route("/delete-expense/<expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    data = request.get_json(silent=True) or {}

    if not is_positive_int(expense_id):
        return jsonify({"message": "expense_id must be a positive integer"}), 400

    existing = supabase.table("expenses") \
        .select("*") \
        .eq("expense_id", expense_id) \
        .limit(1) \
        .execute()

    if not existing.data:
        return jsonify({"message": "Expense not found"}), 404

    response = supabase.table("expenses") \
        .delete() \
        .eq("expense_id", expense_id) \
        .execute()

    deleted = existing.data[0]
    audit_user_id = data.get("user_id", deleted.get("user_id"))
    log_audit_action(audit_user_id, "DELETE", "expenses", expense_id)

    return jsonify({
        "message": "Expense deleted",
        "data": response.data,
    })


@expense_routes.route("/update-expense/<expense_id>", methods=["PUT"])
def update_expense(expense_id):
    data = request.get_json(silent=True) or {}

    if not is_positive_int(expense_id):
        return jsonify({"message": "expense_id must be a positive integer"}), 400

    updates = {}
    for key in ("amount", "category_id", "notes", "expense_date"):
        if key in data:
            if key == "amount" and not is_positive_amount(data.get("amount")):
                return jsonify({"message": "amount must be greater than 0"}), 400
            if key == "category_id" and not is_positive_int(data.get("category_id")):
                return jsonify({"message": "category_id must be a positive integer"}), 400
            if key == "expense_date" and not looks_like_date(data.get("expense_date")):
                return jsonify({"message": "expense_date must look like YYYY-MM-DD"}), 400
            if key == "notes" and data.get("notes") is not None and not isinstance(data.get("notes"), str):
                return jsonify({"message": "notes must be text"}), 400
            updates[key] = data[key]

    if "amount" in updates:
        updates["amount"] = float(updates["amount"])
    if "category_id" in updates:
        updates["category_id"] = int(updates["category_id"])

    if not updates:
        return jsonify({"message": "At least one updatable field is required"}), 400

    response = supabase.table("expenses") \
        .update(updates) \
        .eq("expense_id", expense_id) \
        .execute()

    updated = response.data[0] if response.data else {}
    audit_user_id = data.get("user_id", updated.get("user_id"))
    log_audit_action(audit_user_id, "UPDATE", "expenses", expense_id)

    return jsonify({
        "message": "Expense updated",
        "data": response.data,
    })


