from collections import defaultdict
from flask import Blueprint, request, jsonify
from db import supabase
from routes.audit_logs import log_audit_action
from routes.budgets import normalize_budget_rows
from routes.common import is_positive_int, looks_like_date, to_float
from datetime import date


report_routes = Blueprint("reports", __name__)
VALID_REPORT_TYPES = {"monthly_summary", "by_category", "date_range"}
BASIC_REPORT_MONTHLY_LIMIT = 3


def _current_month_bounds():
    today = date.today()
    month_start = today.replace(day=1)

    if month_start.month == 12:
        next_month_start = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month_start = month_start.replace(month=month_start.month + 1)

    return month_start.isoformat(), next_month_start.isoformat()


def _get_user_role(user_id):
    response = supabase.table("users") \
        .select("user_id, role") \
        .eq("user_id", user_id) \
        .limit(1) \
        .execute()

    if not response.data:
        return None

    return response.data[0].get("role")


def _count_reports_generated_this_month(user_id):
    month_start, next_month_start = _current_month_bounds()
    response = supabase.table("reports") \
        .select("report_id") \
        .eq("user_id", user_id) \
        .gte("generated_at", month_start) \
        .lt("generated_at", next_month_start) \
        .execute()

    return len(response.data or [])


def _category_map():
    response = supabase.table("categories").select("category_id, name").execute()
    return {row.get("category_id"): row.get("name") for row in (response.data or [])}


def _load_expenses(user_id, date_from, date_to):
    response = supabase.table("expenses") \
        .select("expense_id, category_id, amount, expense_date, notes, created_at") \
        .eq("user_id", user_id) \
        .gte("expense_date", date_from) \
        .lte("expense_date", date_to) \
        .execute()

    return response.data or []


def _category_breakdown(expenses, categories):
    grouped_totals = defaultdict(float)
    for item in expenses:
        grouped_totals[item.get("category_id")] += to_float(item.get("amount"))

    rows = []
    for category_id, amount in grouped_totals.items():
        rows.append({
            "category_id": category_id,
            "category_name": categories.get(category_id, f"Category {category_id}"),
            "total_amount": round(amount, 2),
        })

    rows.sort(key=lambda row: row["total_amount"], reverse=True)
    return rows


def _recent_transactions(expenses, categories, limit=10):
    rows = sorted(expenses, key=lambda row: row.get("expense_date"), reverse=True)[:limit]
    for expense in rows:
        expense["category_name"] = categories.get(expense.get("category_id"), f"Category {expense.get('category_id')}")
        expense["amount"] = round(to_float(expense.get("amount")), 2)
    return rows


def _budget_rows(user_id, expenses, categories):
    budgets_resp = supabase.table("budgets") \
        .select("budget_id, category_id, amount_limit, start_date, end_date") \
        .eq("user_id", user_id) \
        .order("start_date", desc=True) \
        .execute()

    budget_rows = []
    for budget in normalize_budget_rows(budgets_resp.data):
        try:
            b_start = date.fromisoformat(str(budget["start_date"]))
            b_window_end = date.fromisoformat(str(budget["end_date"]))
        except Exception:
            b_start = None
            b_window_end = None

        spent = 0.0
        if b_start and b_window_end:
            for expense in expenses:
                try:
                    expense_date = date.fromisoformat(str(expense.get("expense_date")))
                except Exception:
                    continue
                if int(expense.get("category_id")) != int(budget.get("category_id")):
                    continue
                if b_start <= expense_date <= b_window_end:
                    spent += to_float(expense.get("amount"))

        amount_limit = to_float(budget.get("amount_limit"))
        remaining = round(amount_limit - spent, 2)
        budget_rows.append({
            "budget_id": budget.get("budget_id"),
            "category_id": budget.get("category_id"),
            "category_name": categories.get(budget.get("category_id"), f"Category {budget.get('category_id')}"),
            "period": budget.get("period"),
            "start_date": budget.get("start_date"),
            "amount_limit": round(amount_limit, 2),
            "total_spent": round(spent, 2),
            "remaining": remaining,
            "over_budget": remaining < 0,
        })

    return budget_rows


def _build_report_details(user_id, report_type, date_from, date_to):
    categories = _category_map()
    expenses = _load_expenses(user_id, date_from, date_to)
    total_amount = round(sum(to_float(item.get("amount")) for item in expenses), 2)
    expense_count = len(expenses)
    average_expense = round(total_amount / expense_count, 2) if expense_count else 0
    category_breakdown = _category_breakdown(expenses, categories)
    recent_transactions = _recent_transactions(expenses, categories)
    budget_rows = _budget_rows(user_id, expenses, categories)

    top_category = category_breakdown[0] if category_breakdown else None
    summary = {
        "total_amount": total_amount,
        "expense_count": expense_count,
        "average_expense": average_expense,
        "top_category": top_category,
        "category_breakdown": category_breakdown,
    }

    if report_type == "date_range":
        summary["expenses"] = expenses

    return {
        "summary": summary,
        "views": {
            "spent_by_category": {"items": category_breakdown, "total_amount": total_amount},
            "recent_transactions": recent_transactions,
            "budget_vs_actual": {"items": budget_rows},
        },
    }


@report_routes.route("/generate-report", methods=["POST"])
def generate_report():
    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    report_type = data.get("report_type")
    date_from = data.get("date_from")
    date_to = data.get("date_to")

    if not user_id or not report_type or not date_from or not date_to:
        return jsonify({"message": "user_id, report_type, date_from, and date_to are required"}), 400

    if not is_positive_int(user_id):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    if report_type not in VALID_REPORT_TYPES:
        return jsonify({"message": "Invalid report_type"}), 400

    if not looks_like_date(date_from) or not looks_like_date(date_to):
        return jsonify({"message": "date_from and date_to must look like YYYY-MM-DD"}), 400

    if date_from > date_to:
        return jsonify({"message": "date_from must be before or equal to date_to"}), 400

    try:
        user_role = _get_user_role(user_id)
        if user_role is None:
            return jsonify({"message": "user_id not found"}), 404

        if user_role == "basic":
            reports_count = _count_reports_generated_this_month(user_id)
            if reports_count >= BASIC_REPORT_MONTHLY_LIMIT:
                return jsonify({
                    "message": "Basic accounts are limited to 3 reports per month",
                    "limit": BASIC_REPORT_MONTHLY_LIMIT,
                    "used": reports_count,
                }), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    try:
        details = _build_report_details(user_id, report_type, date_from, date_to)

        report_response = supabase.table("reports").insert({
            "user_id": user_id,
            "report_type": report_type,
            "date_from": date_from,
            "date_to": date_to,
        }).execute()

        report_record = report_response.data[0] if report_response.data else {}
        log_audit_action(int(user_id), "INSERT", "reports", report_record.get("report_id"))

        return jsonify({
            "message": "Report generated",
            "report": report_record,
            "summary": details["summary"],
            "views": details["views"],
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@report_routes.route("/reports/<user_id>", methods=["GET"])
def get_reports(user_id):
    if not is_positive_int(user_id):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    response = supabase.table("reports") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("generated_at", desc=True) \
        .execute()

    reports = []
    for report in response.data or []:
        details = _build_report_details(
            report.get("user_id"),
            report.get("report_type"),
            report.get("date_from"),
            report.get("date_to"),
        )
        reports.append({
            **report,
            "summary": details["summary"],
            "views": details["views"],
        })

    return jsonify(reports)


@report_routes.route("/delete-report/<report_id>", methods=["DELETE"])
def delete_report(report_id):
    data = request.get_json(silent=True) or {}

    if not is_positive_int(report_id):
        return jsonify({"message": "report_id must be a positive integer"}), 400

    existing = supabase.table("reports") \
        .select("*") \
        .eq("report_id", report_id) \
        .limit(1) \
        .execute()

    if not existing.data:
        return jsonify({"message": "Report not found"}), 404

    response = supabase.table("reports") \
        .delete() \
        .eq("report_id", report_id) \
        .execute()

    deleted_report = existing.data[0]
    audit_user_id = data.get("user_id", deleted_report.get("user_id"))
    log_audit_action(audit_user_id, "DELETE", "reports", report_id)

    return jsonify({
        "message": "Report deleted",
        "data": response.data,
    })
