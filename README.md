# Financer

---

A Personal Expense Tracking Web Application
<img width="1976" height="1274" alt="Untitled Diagram" src="https://cdn.ph4ntom.org/2026/04/bxHbyFbuTK.png" />

---

## Backend

#### Environment
- Supabase credentials go inside `backend/.env`:

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```


#### Starting
- Creating a venv and installing dependencies, then run the backend:
```powershell
cd backend
python -m venv venv
backend\venv\Scripts\Activate
pip install -r requirements.txt
python app.py
```

By default the Flask server binds to `http://127.0.0.1:5000`.

#### Curl Examples

1) Register
```bash
curl -X POST http://127.0.0.1:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"Password123"}'
```

2) Login
```bash
curl -X POST http://127.0.0.1:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"Password123"}'
```

3) Add category (use the `user_id` returned from registration)
```bash
curl -X POST http://127.0.0.1:5000/add-category \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"name":"Food","description":"Meals and snacks"}'
```

4) Add expense
```bash
curl -X POST http://127.0.0.1:5000/add-expense \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"category_id":1,"amount":12.5,"expense_date":"2026-04-28","notes":"Lunch"}'
```

5) List expenses for a user
```bash
curl http://127.0.0.1:5000/expenses/1
```

6) Delete an expense
```bash
curl -X DELETE http://127.0.0.1:5000/delete-expense/1 \
  -H "Content-Type: application/json" \
  -d '{"user_id":1}'
```

---