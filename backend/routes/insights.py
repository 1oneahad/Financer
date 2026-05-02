from collections import defaultdict
from datetime import date, timedelta

from flask import Blueprint, jsonify

from db import supabase


insight_routes = Blueprint("insights", __name__)


def _valid_id(value):
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False


def _parse_date(value):
    return date.fromisoformat(str(value))


def _month_range(for_date=None):
    current = for_date or date.today()
    start = current.replace(day=1)
    if start.month == 12:
        next_month = date(start.year + 1, 1, 1)
    else:
        next_month = date(start.year, start.month + 1, 1)
    return start, next_month - timedelta(days=1)


def _get_user(user_id):
    return supabase.table("users") \
        .select("user_id, username, email, role") \
        .eq("user_id", user_id) \
        .limit(1) \
        .execute()


def _load_categories():
    response = supabase.table("categories").select("category_id, name").execute()
    return {row["category_id"]: row["name"] for row in (response.data or [])}


@insight_routes.route("/insights/spent-by-category/<user_id>", methods=["GET"])
def spent_by_category(user_id):
    if not _valid_id(user_id):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    user = _get_user(user_id)
    if not user.data:
        return jsonify({"message": "user not found"}), 404

    month_start, month_end = _month_range()
    categories = _load_categories()

    expenses = supabase.table("expenses") \
        .select("category_id, amount, expense_date") \
        .eq("user_id", user_id) \
        .gte("expense_date", month_start.isoformat()) \
        .lte("expense_date", month_end.isoformat()) \
        .execute()

    totals = defaultdict(float)
    for item in expenses.data or []:
        totals[item["category_id"]] += float(item.get("amount") or 0)

    items = []
    for category_id, total in totals.items():
        items.append({
            "category_id": category_id,
            "category_name": categories.get(category_id, f"Category {category_id}"),
            "total_spent": round(total, 2),
        })

    items.sort(key=lambda row: row["total_spent"], reverse=True)

    return jsonify({
        "user_id": int(user_id),
        "username": user.data[0]["username"],
        "month": month_start.strftime("%Y-%m"),
        "total_spent": round(sum(item["total_spent"] for item in items), 2),
        "items": items,
    })


@insight_routes.route("/insights/total-monthly/<user_id>", methods=["GET"])
def total_monthly(user_id):
    if not _valid_id(user_id):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    user = _get_user(user_id)
    if not user.data:
        return jsonify({"message": "user not found"}), 404

    month_start, month_end = _month_range()
    expenses = supabase.table("expenses") \
        .select("amount") \
        .eq("user_id", user_id) \
        .gte("expense_date", month_start.isoformat()) \
        .lte("expense_date", month_end.isoformat()) \
        .execute()

    total = round(sum(float(row.get("amount") or 0) for row in (expenses.data or [])), 2)

    return jsonify({
        "user_id": int(user_id),
        "username": user.data[0]["username"],
        "month": month_start.strftime("%Y-%m"),
        "spent_monthly": total,
        "expense_count": len(expenses.data or []),
    })


@insight_routes.route("/insights/budget-vs-actual/<user_id>", methods=["GET"])
def budget_vs_actual(user_id):
    if not _valid_id(user_id):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    user = _get_user(user_id)
    if not user.data:
        return jsonify({"message": "user not found"}), 404

    categories = _load_categories()
    budgets = supabase.table("budgets") \
        .select("budget_id, category_id, amount_limit, period, start_date") \
        .eq("user_id", user_id) \
        .order("start_date", desc=True) \
        .execute()

    expenses = supabase.table("expenses") \
        .select("category_id, amount, expense_date") \
        .eq("user_id", user_id) \
        .execute()

    expense_rows = expenses.data or []
    rows = []

    for budget in budgets.data or []:
        start_date = _parse_date(budget["start_date"])
        if budget["period"] == "monthly":
            budget_start = start_date.replace(day=1)
            if budget_start.month == 12:
                next_month = date(budget_start.year + 1, 1, 1)
            else:
                next_month = date(budget_start.year, budget_start.month + 1, 1)
            budget_end = next_month - timedelta(days=1)
        else:
            budget_start = start_date
            budget_end = start_date + timedelta(days=6)

        spent = 0.0
        for expense in expense_rows:
            if int(expense["category_id"]) != int(budget["category_id"]):
                continue
            expense_date = _parse_date(expense["expense_date"])
            if budget_start <= expense_date <= budget_end:
                spent += float(expense.get("amount") or 0)

        amount_limit = float(budget["amount_limit"])
        remaining = round(amount_limit - spent, 2)

        rows.append({
            "budget_id": budget["budget_id"],
            "category_id": budget["category_id"],
            "category_name": categories.get(budget["category_id"], f"Category {budget['category_id']}"),
            "period": budget["period"],
            "start_date": budget["start_date"],
            "amount_limit": round(amount_limit, 2),
            "total_spent": round(spent, 2),
            "remaining": remaining,
            "over_budget": remaining < 0,
        })

    return jsonify({
        "user_id": int(user_id),
        "username": user.data[0]["username"],
        "items": rows,
    })


@insight_routes.route("/insights/recent-transactions/<user_id>", methods=["GET"])
def recent_transactions(user_id):
    if not _valid_id(user_id):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    user = _get_user(user_id)
    if not user.data:
        return jsonify({"message": "user not found"}), 404

    categories = _load_categories()
    expenses = supabase.table("expenses") \
        .select("expense_id, category_id, amount, expense_date, notes, created_at") \
        .eq("user_id", user_id) \
        .order("expense_date", desc=True) \
        .limit(10) \
        .execute()

    items = []
    for expense in expenses.data or []:
        items.append({
            "expense_id": expense["expense_id"],
            "category_id": expense["category_id"],
            "category_name": categories.get(expense["category_id"], f"Category {expense['category_id']}"),
            "amount": round(float(expense.get("amount") or 0), 2),
            "expense_date": expense["expense_date"],
            "notes": expense.get("notes") or "",
        })

    return jsonify({
        "user_id": int(user_id),
        "username": user.data[0]["username"],
        "items": items,
    })