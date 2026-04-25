from flask import Blueprint, request, jsonify
from db import supabase
from routes.audit_logs import log_audit_action


budget_routes = Blueprint("budgets", __name__)


@budget_routes.route("/add-budget", methods=["POST"])
def add_budget():
    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    category_id = data.get("category_id")
    amount_limit = data.get("amount_limit")
    period = data.get("period")
    start_date = data.get("start_date")

    if not user_id or not category_id or amount_limit is None or not period or not start_date:
        return jsonify({"message": "user_id, category_id, amount_limit, period, and start_date are required"}), 400

    if period not in {"weekly", "monthly"}:
        return jsonify({"message": "period must be weekly or monthly"}), 400

    try:
        response = supabase.table("budgets").insert({
            "user_id": user_id,
            "category_id": category_id,
            "amount_limit": amount_limit,
            "period": period,
            "start_date": start_date,
        }).execute()

        created_budget = response.data[0] if response.data else {}
        log_audit_action(user_id, "INSERT", "budgets", created_budget.get("budget_id"))

        return jsonify({
            "message": "Budget added",
            "data": response.data,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@budget_routes.route("/budgets/<user_id>", methods=["GET"])
def get_budgets(user_id):
    response = supabase.table("budgets") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("start_date", desc=True) \
        .execute()

    return jsonify(response.data)



@budget_routes.route("/update-budget/<budget_id>", methods=["PUT"])
def update_budget(budget_id):
    data = request.get_json(silent=True) or {}

    updates = {}
    for key in ("category_id", "amount_limit", "period", "start_date"):
        if key in data:
            updates[key] = data[key]

    if not updates:
        return jsonify({"message": "At least one updatable field is required"}), 400

    if "period" in updates and updates["period"] not in {"weekly", "monthly"}:
        return jsonify({"message": "period must be weekly or monthly"}), 400

    try:
        response = supabase.table("budgets") \
            .update(updates) \
            .eq("budget_id", budget_id) \
            .execute()

        updated_budget = response.data[0] if response.data else {}
        audit_user_id = data.get("user_id", updated_budget.get("user_id"))
        log_audit_action(audit_user_id, "UPDATE", "budgets", budget_id)

        return jsonify({
            "message": "Budget updated",
            "data": response.data,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@budget_routes.route("/delete-budget/<budget_id>", methods=["DELETE"])
def delete_budget(budget_id):
    data = request.get_json(silent=True) or {}

    response = supabase.table("budgets") \
        .delete() \
        .eq("budget_id", budget_id) \
        .execute()

    deleted_budget = response.data[0] if response.data else {}
    audit_user_id = data.get("user_id", deleted_budget.get("user_id"))
    log_audit_action(audit_user_id, "DELETE", "budgets", budget_id)

    return jsonify({
        "message": "Budget deleted",
        "data": response.data,
    })
