from flask import Blueprint, request, jsonify
from db import supabase

expense_routes = Blueprint('expenses', __name__)


@expense_routes.route('/add-expense', methods=['POST'])
def add_expense():
    data = request.json

    response = supabase.table("expenses").insert({
        "user_id": data["user_id"],
        "category_id": data["category_id"],
        "amount": data["amount"],
        "expense_date": data["expense_date"],
        "notes": data.get("notes", "")
    }).execute()

    return jsonify({
        "message": "Expense added",
        "data": response.data
    })



@expense_routes.route('/expenses/<user_id>', methods=['GET'])
def get_expenses(user_id):
    response = supabase.table("expenses") \
        .select("*") \
        .eq("user_id", user_id) \
        .execute()

    return jsonify(response.data)



@expense_routes.route('/delete-expense/<expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    response = supabase.table("expenses") \
        .delete() \
        .eq("expense_id", expense_id) \
        .execute()

    return jsonify({
        "message": "Expense deleted",
        "data": response.data
    })



@expense_routes.route('/update-expense/<expense_id>', methods=['PUT'])
def update_expense(expense_id):
    data = request.json

    response = supabase.table("expenses") \
        .update({
            "amount": data["amount"],
            "category_id": data["category_id"],
            "notes": data.get("notes", "")
        }) \
        .eq("expense_id", expense_id) \
        .execute()

    return jsonify({
        "message": "Expense updated",
        "data": response.data
    })


