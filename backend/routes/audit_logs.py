from flask import Blueprint, request, jsonify
from db import supabase
from routes.common import is_positive_int, parse_limit


audit_log_routes = Blueprint("audit_logs", __name__)


def log_audit_action(user_id, action, target_table, target_id):
    try:
        payload = {
            "action": action,
            "target_table": target_table,
            "target_id": target_id,
        }

        if user_id is not None:
            payload["user_id"] = user_id

        supabase.table("audit_log").insert(payload).execute()
    except Exception:
        pass


@audit_log_routes.route("/audit-logs", methods=["GET"])
def get_audit_logs():
    user_id = request.args.get("user_id")
    action = request.args.get("action")
    target_table = request.args.get("target_table")
    limit_raw = request.args.get("limit", "100")

    if user_id and not is_positive_int(user_id):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    if action and action not in {"INSERT", "UPDATE", "DELETE"}:
        return jsonify({"message": "action must be INSERT, UPDATE, or DELETE"}), 400

    if target_table and not isinstance(target_table, str):
        return jsonify({"message": "target_table must be text"}), 400

    limit, limit_error = parse_limit(limit_raw)
    if limit_error:
        return jsonify({"message": limit_error}), 400

    query = supabase.table("audit_log").select("*")

    if user_id:
        query = query.eq("user_id", user_id)
    if action:
        query = query.eq("action", action)
    if target_table:
        query = query.eq("target_table", target_table)

    response = query.order("action_time", desc=True).limit(limit).execute()
    return jsonify(response.data)



@audit_log_routes.route("/audit-logs/user/<user_id>", methods=["GET"])
def get_user_audit_logs(user_id):
    if not is_positive_int(user_id):
        return jsonify({"message": "user_id must be a positive integer"}), 400

    response = supabase.table("audit_log") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("action_time", desc=True) \
        .limit(200) \
        .execute()

    return jsonify(response.data)

