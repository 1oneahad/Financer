from collections import defaultdict
from flask import Blueprint, request, jsonify
from db import supabase
from routes.audit_logs import log_audit_action
from datetime import date


report_routes = Blueprint("reports", __name__)
VALID_REPORT_TYPES = {"monthly_summary", "by_category", "date_range"}


def _to_float(value):
    return float(value)


def _valid_id(value):
    return int(value) > 0


def _looks_like_date(value):
    return isinstance(value, str) and len(value.strip()) == 10 and value.count("-") == 2


@report_routes.route("/generate-report", methods=["POST"])
def generate_report():
    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    report_type = data.get("report_type")
    date_from = data.get("date_from")
    date_to = data.get("date_to")

    if not user_id or not report_type or not date_from or not date_to:
        return jsonify({"message": "user_id, report_type, date_from, and date_to are required"}), 400

    if not _valid_id(user_id):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    if report_type not in VALID_REPORT_TYPES:
        return jsonify({"message": "Invalid report_type"}), 400

    if not _looks_like_date(date_from) or not _looks_like_date(date_to):
        return jsonify({"message": "date_from and date_to must look like YYYY-MM-DD"}), 400

    if date_from > date_to:
        return jsonify({"message": "date_from must be before or equal to date_to"}), 400

    # enforce free-tier report limit: basic users can generate up to 3 reports per calendar month
    try:
        user_resp = supabase.table("users").select("user_id, role").eq("user_id", user_id).limit(1).execute()
        user_role = (user_resp.data[0].get("role") if user_resp.data else "basic")
    except Exception:
        user_role = "basic"

    if user_role != "premium" and user_role != "admin":
        # count reports generated this month
        today = date.today()
        month_start = today.replace(day=1).isoformat()
        # last day of month: simple way to count reports where generated_at >= month_start
        reports_count_resp = supabase.table("reports").select("report_id") \
            .eq("user_id", user_id) \
            .gte("generated_at", month_start) \
            .execute()
        reports_count = len(reports_count_resp.data or [])
        if reports_count >= 3:
            return jsonify({"message": "Basic accounts are limited to 3 reports per month"}), 403

    try:
        # load expenses for the requested date range (used by several views)
        expenses_response = supabase.table("expenses") \
            .select("expense_id, category_id, amount, expense_date, notes, created_at") \
            .eq("user_id", user_id) \
            .gte("expense_date", date_from) \
            .lte("expense_date", date_to) \
            .execute()

        expenses = expenses_response.data or []
        total_amount = round(sum(_to_float(item.get("amount")) for item in expenses), 2)
        expense_count = len(expenses)

        # spent by category view
        grouped_totals = defaultdict(float)
        for item in expenses:
            grouped_totals[item.get("category_id")] += _to_float(item.get("amount"))

        category_breakdown = [
            {"category_id": category_id, "total_amount": round(amount, 2)}
            for category_id, amount in grouped_totals.items()
        ]

        # recent transactions view (top 10 in range)
        recent_transactions = sorted(expenses, key=lambda r: r.get("expense_date"), reverse=True)[:10]

        # budgets: approximate budget vs actual for budgets belonging to the user
        budgets_resp = supabase.table("budgets") \
            .select("budget_id, category_id, amount_limit, period, start_date") \
            .eq("user_id", user_id) \
            .order("start_date", desc=True) \
            .execute()

        budget_rows = []
        for budget in budgets_resp.data or []:
            # determine budget window
            try:
                from datetime import date as _d, timedelta as _td
                b_start = _d.fromisoformat(str(budget["start_date"]))
            except Exception:
                b_start = None

            if budget.get("period") == "monthly" and b_start:
                b_window_start = b_start.replace(day=1)
                if b_window_start.month == 12:
                    next_month = _d(b_window_start.year + 1, 1, 1)
                else:
                    next_month = _d(b_window_start.year, b_window_start.month + 1, 1)
                b_window_end = next_month - _td(days=1)
            elif b_start:
                b_window_start = b_start
                b_window_end = b_start + _td(days=6)
            else:
                b_window_start = None
                b_window_end = None

            spent = 0.0
            if b_window_start and b_window_end:
                for e in expenses:
                    try:
                        from datetime import date as _d2
                        ed = _d2.fromisoformat(str(e.get("expense_date")))
                    except Exception:
                        continue
                    if int(e.get("category_id")) != int(budget.get("category_id")):
                        continue
                    if b_window_start <= ed <= b_window_end:
                        spent += float(e.get("amount") or 0)

            amount_limit = float(budget.get("amount_limit") or 0)
            remaining = round(amount_limit - spent, 2)

            budget_rows.append({
                "budget_id": budget.get("budget_id"),
                "category_id": budget.get("category_id"),
                "period": budget.get("period"),
                "start_date": budget.get("start_date"),
                "amount_limit": round(amount_limit, 2),
                "total_spent": round(spent, 2),
                "remaining": remaining,
            })

        # prepare summary depending on requested type
        if report_type == "by_category":
            summary = {
                "total_amount": total_amount,
                "expense_count": expense_count,
                "category_breakdown": category_breakdown,
            }

        elif report_type == "monthly_summary":
            average = round(total_amount / expense_count, 2) if expense_count else 0
            summary = {
                "total_amount": total_amount,
                "expense_count": expense_count,
                "average_expense": average,
            }

        else:
            summary = {
                "total_amount": total_amount,
                "expense_count": expense_count,
                "expenses": expenses,
            }

        views = {
            "spent_by_category": {"items": category_breakdown, "total_amount": total_amount},
            "recent_transactions": recent_transactions,
            "budget_vs_actual": {"items": budget_rows},
        }

        report_response = supabase.table("reports").insert({
            "user_id": user_id,
            "report_type": report_type,
            "date_from": date_from,
            "date_to": date_to,
        }).execute()

        report_record = report_response.data[0] if report_response.data else {}
        log_audit_action(user_id, "INSERT", "reports", report_record.get("report_id"))

        return jsonify({
            "message": "Report generated",
            "report": report_record,
            "summary": summary,
            "views": views,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@report_routes.route("/reports/<user_id>", methods=["GET"])
def get_reports(user_id):
    if not _valid_id(user_id):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    response = supabase.table("reports") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("generated_at", desc=True) \
        .execute()

    return jsonify(response.data)


@report_routes.route("/delete-report/<report_id>", methods=["DELETE"])
def delete_report(report_id):
    data = request.get_json(silent=True) or {}

    if not _valid_id(report_id):
        return jsonify({"message": "report_id must be a positive integer"}), 400

    response = supabase.table("reports") \
        .delete() \
        .eq("report_id", report_id) \
        .execute()

    deleted_report = response.data[0] if response.data else {}
    audit_user_id = data.get("user_id", deleted_report.get("user_id"))
    log_audit_action(audit_user_id, "DELETE", "reports", report_id)

    return jsonify({
        "message": "Report deleted",
        "data": response.data,
    })
