from flask import Blueprint, request, jsonify
from db import supabase


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

    try:
        limit = max(1, min(int(limit_raw), 500))
    except ValueError:
        return jsonify({"message": "limit must be a number"}), 400

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
    response = supabase.table("audit_log") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("action_time", desc=True) \
        .limit(200) \
        .execute()

    return jsonify(response.data)

