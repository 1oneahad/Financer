from datetime import date, timedelta

from flask import Blueprint, request, jsonify
from db import supabase
from routes.audit_logs import log_audit_action
from routes.common import is_positive_amount, is_positive_int, looks_like_date, parse_date


budget_routes = Blueprint("budgets", __name__)


def _end_date_for_period(start_date, period):
    parsed_start = parse_date(start_date)

    if period == "weekly":
        return (parsed_start + timedelta(days=6)).isoformat()

    if parsed_start.month == 12:
        next_month = date(parsed_start.year + 1, 1, 1)
    else:
        next_month = date(parsed_start.year, parsed_start.month + 1, 1)

    return (next_month - timedelta(days=1)).isoformat()


def _period_from_dates(start_date, end_date):
    try:
        parsed_start = parse_date(start_date)
        parsed_end = parse_date(end_date)
    except (TypeError, ValueError):
        return None

    if parsed_end == parsed_start + timedelta(days=6):
        return "weekly"

    if parsed_end == parse_date(_end_date_for_period(start_date, "monthly")):
        return "monthly"

    return "custom"


def normalize_budget_row(row):
    normalized = dict(row)
    if not normalized.get("period"):
        normalized["period"] = _period_from_dates(normalized.get("start_date"), normalized.get("end_date"))
    return normalized


def normalize_budget_rows(rows):
    return [normalize_budget_row(row) for row in rows or []]


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

    if not is_positive_int(user_id):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    if not is_positive_int(category_id):
        return jsonify({"message": "category_id must be a positive integer"}), 400

    if not is_positive_amount(amount_limit):
        return jsonify({"message": "amount_limit must be greater than 0"}), 400

    if period not in {"weekly", "monthly"}:
        return jsonify({"message": "period must be weekly or monthly"}), 400

    if not looks_like_date(start_date):
        return jsonify({"message": "start_date must look like YYYY-MM-DD"}), 400

    try:
        end_date = _end_date_for_period(start_date, period)
        response = supabase.table("budgets").insert({
            "user_id": int(user_id),
            "category_id": int(category_id),
            "amount_limit": float(amount_limit),
            "start_date": start_date,
            "end_date": end_date,
        }).execute()

        created_budget = normalize_budget_row(response.data[0]) if response.data else {}
        log_audit_action(int(user_id), "INSERT", "budgets", created_budget.get("budget_id"))

        return jsonify({
            "message": "Budget added",
            "data": normalize_budget_rows(response.data),
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@budget_routes.route("/budgets/<user_id>", methods=["GET"])
def get_budgets(user_id):
    if not is_positive_int(user_id):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    response = supabase.table("budgets") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("start_date", desc=True) \
        .execute()

    return jsonify(normalize_budget_rows(response.data))



@budget_routes.route("/update-budget/<budget_id>", methods=["PUT"])
def update_budget(budget_id):
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")

    if not is_positive_int(budget_id):
        return jsonify({"message": "budget_id must be a positive integer"}), 400
    if not is_positive_int(user_id):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    existing = supabase.table("budgets") \
        .select("*") \
        .eq("budget_id", budget_id) \
        .limit(1) \
        .execute()

    if not existing.data:
        return jsonify({"message": "Budget not found"}), 404

    if int(existing.data[0].get("user_id")) != int(user_id):
        return jsonify({"message": "You can only update your own budgets"}), 403

    updates = {}
    period = data.get("period")
    for key in ("category_id", "amount_limit", "start_date"):
        if key in data:
            if key == "category_id" and not is_positive_int(data.get("category_id")):
                return jsonify({"message": "category_id must be a positive integer"}), 400
            if key == "amount_limit" and not is_positive_amount(data.get("amount_limit")):
                return jsonify({"message": "amount_limit must be greater than 0"}), 400
            if key == "start_date" and not looks_like_date(data.get("start_date")):
                return jsonify({"message": "start_date must look like YYYY-MM-DD"}), 400
            updates[key] = data[key]

    if period is not None and period not in {"weekly", "monthly"}:
        return jsonify({"message": "period must be weekly or monthly"}), 400

    if period is not None or "start_date" in updates:
        current_row = existing.data[0]
        next_start_date = updates.get("start_date", current_row.get("start_date"))
        next_period = period or _period_from_dates(current_row.get("start_date"), current_row.get("end_date"))

        if next_period not in {"weekly", "monthly"}:
            return jsonify({"message": "period must be provided when updating a custom budget window"}), 400

        updates["end_date"] = _end_date_for_period(next_start_date, next_period)

    if not updates:
        return jsonify({"message": "At least one updatable field is required"}), 400

    if "category_id" in updates:
        updates["category_id"] = int(updates["category_id"])
    if "amount_limit" in updates:
        updates["amount_limit"] = float(updates["amount_limit"])

    response = supabase.table("budgets") \
        .update(updates) \
        .eq("budget_id", budget_id) \
        .execute()

    updated_budget = normalize_budget_row(response.data[0]) if response.data else {}
    log_audit_action(user_id, "UPDATE", "budgets", budget_id)

    return jsonify({
        "message": "Budget updated",
        "data": normalize_budget_rows(response.data),
    })


@budget_routes.route("/delete-budget/<budget_id>", methods=["DELETE"])
def delete_budget(budget_id):
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")

    if not is_positive_int(budget_id):
        return jsonify({"message": "budget_id must be a positive integer"}), 400
    if not is_positive_int(user_id):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    existing = supabase.table("budgets") \
        .select("*") \
        .eq("budget_id", budget_id) \
        .limit(1) \
        .execute()

    if not existing.data:
        return jsonify({"message": "Budget not found"}), 404

    deleted_budget = existing.data[0]
    if int(deleted_budget.get("user_id")) != int(user_id):
        return jsonify({"message": "You can only delete your own budgets"}), 403

    response = supabase.table("budgets") \
        .delete() \
        .eq("budget_id", budget_id) \
        .execute()

    log_audit_action(user_id, "DELETE", "budgets", budget_id)

    return jsonify({
        "message": "Budget deleted",
        "data": response.data,
    })
