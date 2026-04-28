from collections import defaultdict
from flask import Blueprint, request, jsonify
from db import supabase
from routes.audit_logs import log_audit_action


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

    try:
        expenses_response = supabase.table("expenses") \
            .select("expense_id, category_id, amount, expense_date, notes") \
            .eq("user_id", user_id) \
            .gte("expense_date", date_from) \
            .lte("expense_date", date_to) \
            .execute()

        expenses = expenses_response.data or []
        total_amount = round(sum(_to_float(item.get("amount")) for item in expenses), 2)
        expense_count = len(expenses)

        if report_type == "by_category":
            grouped_totals = defaultdict(float)
            for item in expenses:
                grouped_totals[item.get("category_id")] += _to_float(item.get("amount"))

            breakdown = [
                {
                    "category_id": category_id,
                    "total_amount": round(amount, 2),
                }
                for category_id, amount in grouped_totals.items()
            ]

            summary = {
                "total_amount": total_amount,
                "expense_count": expense_count,
                "category_breakdown": breakdown,
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
