from flask import Flask, request, session, redirect, url_for, jsonify, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")
# Absolute path so the database is found no matter where the server starts the app
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "studysnap.db")


# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS tasks (
        task_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        subject TEXT NOT NULL,
        due_date TEXT,
        status TEXT NOT NULL DEFAULT 'Pending',
        user_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id))""")
    conn.commit()
    conn.close()


# ---------- PAGE TEMPLATE ----------
PAGE = """
<!doctype html>
<html><head><title>StudySnap</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
 body{font-family:Arial;max-width:650px;margin:30px auto;padding:0 15px;background:#f4f6fb}
 h1{color:#3b4cca} .box{background:#fff;padding:18px;border-radius:10px;margin-bottom:15px;box-shadow:0 1px 4px #0002}
 input,button{padding:9px;margin:4px 0;width:100%;box-sizing:border-box;font-size:15px}
 button{background:#3b4cca;color:#fff;border:0;border-radius:6px;cursor:pointer}
 .err{color:#c0392b;font-weight:bold} .ok{color:#27ae60;font-weight:bold}
 .task{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #ddd;padding:8px 0}
 .done{text-decoration:line-through;color:#888}
 .small{width:auto;padding:6px 10px;margin-left:5px} .del{background:#c0392b}
 a{color:#3b4cca}
</style></head><body>
<h1>StudySnap</h1>
{% if message %}<p class="{{ 'ok' if ok else 'err' }}">{{ message }}</p>{% endif %}

{% if page == 'login' %}
<div class="box"><h2>Login</h2>
<form method="post" action="/login">
 <input name="email" placeholder="Email">
 <input name="password" type="password" placeholder="Password">
 <button>Login</button></form>
 <p>New here? <a href="/register">Register</a> | <a href="/forgot">Forgot password?</a></p></div>

{% elif page == 'forgot' %}
<div class="box"><h2>Forgot Password</h2>
<form method="post" action="/forgot">
 <input name="email" placeholder="Registered email">
 <input name="new_password" type="password" placeholder="New password (min 6 characters)">
 <input name="confirm_password" type="password" placeholder="Confirm new password">
 <button>Reset Password</button></form>
 <p><a href="/login">Back to login</a></p></div>

{% elif page == 'register' %}
<div class="box"><h2>Register</h2>
<form method="post" action="/register">
 <input name="name" placeholder="Full name">
 <input name="email" placeholder="Email">
 <input name="password" type="password" placeholder="Password (min 6 characters)">
 <button>Create account</button></form>
 <p>Already registered? <a href="/login">Login</a></p></div>

{% elif page == 'dashboard' %}
<div class="box"><b>Hello, {{ name }}!</b> <a href="/logout" style="float:right">Logout</a></div>
<div class="box"><h2>Add Task</h2>
<form method="post" action="/add">
 <input name="title" placeholder="Task (e.g. Finish IoT assignment)">
 <input name="subject" placeholder="Subject (e.g. IoT)">
 <input name="due_date" type="date">
 <button>Add Task</button></form></div>
<div class="box"><h2>My Tasks</h2>
{% if tasks|length == 0 %}<p>No tasks yet. Add one above.</p>{% endif %}
{% for t in tasks %}
 <div class="task">
  <div class="{{ 'done' if t['status']=='Completed' else '' }}">
   <b>{{ t['title'] }}</b><br><small>{{ t['subject'] }} | Due: {{ t['due_date'] or 'N/A' }} | {{ t['status'] }}</small>
  </div>
  <div>
   {% if t['status'] != 'Completed' %}
   <form method="post" action="/complete/{{ t['task_id'] }}" style="display:inline"><button class="small">Done</button></form>
   {% endif %}
   <form method="post" action="/delete/{{ t['task_id'] }}" style="display:inline"><button class="small del">Delete</button></form>
  </div>
 </div>
{% endfor %}</div>
{% endif %}
</body></html>
"""


def show(page, message=None, ok=False, **kw):
    return render_template_string(PAGE, page=page, message=message, ok=ok, **kw)


def logged_in():
    return "user_id" in session


# ---------- WEB PAGES ----------
@app.route("/")
def home():
    return redirect(url_for("dashboard" if logged_in() else "login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return show("register")
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    # input validation
    if not name or not email or not password:
        return show("register", "All fields are required.")
    if "@" not in email or "." not in email:
        return show("register", "Enter a valid email address.")
    if len(password) < 6:
        return show("register", "Password must be at least 6 characters.")
    conn = get_db()
    try:
        conn.execute("INSERT INTO users (name,email,password) VALUES (?,?,?)",
                     (name, email, generate_password_hash(password)))
        conn.commit()
    except sqlite3.IntegrityError:
        return show("register", "This email is already registered.")
    finally:
        conn.close()
    return show("login", "Registration successful. Please login.", ok=True)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return show("login")
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not email or not password:
        return show("login", "Email and password are required.")
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    if user and check_password_hash(user["password"], password):
        session["user_id"] = user["user_id"]
        session["name"] = user["name"]
        return redirect(url_for("dashboard"))
    return show("login", "Invalid email or password.")


@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "GET":
        return show("forgot")
    email = request.form.get("email", "").strip().lower()
    new_password = request.form.get("new_password", "")
    confirm = request.form.get("confirm_password", "")
    # input validation
    if not email or not new_password or not confirm:
        return show("forgot", "All fields are required.")
    if len(new_password) < 6:
        return show("forgot", "Password must be at least 6 characters.")
    if new_password != confirm:
        return show("forgot", "Passwords do not match.")
    conn = get_db()
    user = conn.execute("SELECT user_id FROM users WHERE email=?", (email,)).fetchone()
    if not user:
        conn.close()
        return show("forgot", "No account found with this email.")
    conn.execute("UPDATE users SET password=? WHERE email=?",
                 (generate_password_hash(new_password), email))
    conn.commit()
    conn.close()
    return show("login", "Password reset successful. Please login.", ok=True)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if not logged_in():
        return redirect(url_for("login"))
    conn = get_db()
    tasks = conn.execute("SELECT * FROM tasks WHERE user_id=? ORDER BY task_id DESC",
                         (session["user_id"],)).fetchall()
    conn.close()
    return show("dashboard", name=session["name"], tasks=tasks)


def dashboard_with_message(msg):
    conn = get_db()
    tasks = conn.execute("SELECT * FROM tasks WHERE user_id=? ORDER BY task_id DESC",
                         (session["user_id"],)).fetchall()
    conn.close()
    return show("dashboard", msg, name=session["name"], tasks=tasks)


@app.route("/add", methods=["POST"])
def add_task():
    if not logged_in():
        return redirect(url_for("login"))
    title = request.form.get("title", "").strip()
    subject = request.form.get("subject", "").strip()
    due_date = request.form.get("due_date", "").strip()
    if not title or not subject:
        return dashboard_with_message("Title and subject are required.")
    if len(title) > 100:
        return dashboard_with_message("Title is too long (max 100 characters).")
    conn = get_db()
    conn.execute("INSERT INTO tasks (title,subject,due_date,user_id) VALUES (?,?,?,?)",
                 (title, subject, due_date, session["user_id"]))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))


@app.route("/complete/<int:task_id>", methods=["POST"])
def complete_task(task_id):
    if not logged_in():
        return redirect(url_for("login"))
    conn = get_db()
    # authorization: only the owner can change their own task
    conn.execute("UPDATE tasks SET status='Completed' WHERE task_id=? AND user_id=?",
                 (task_id, session["user_id"]))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    if not logged_in():
        return redirect(url_for("login"))
    conn = get_db()
    conn.execute("DELETE FROM tasks WHERE task_id=? AND user_id=?",
                 (task_id, session["user_id"]))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))


# ---------- REST API (JSON) ----------
@app.route("/api/tasks", methods=["GET"])
def api_get_tasks():
    if not logged_in():
        return jsonify({"error": "Login required"}), 401
    conn = get_db()
    rows = conn.execute("SELECT * FROM tasks WHERE user_id=?", (session["user_id"],)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows]), 200


@app.route("/api/tasks", methods=["POST"])
def api_add_task():
    if not logged_in():
        return jsonify({"error": "Login required"}), 401
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    subject = str(data.get("subject", "")).strip()
    if not title or not subject:
        return jsonify({"error": "title and subject are required"}), 400
    conn = get_db()
    cur = conn.execute("INSERT INTO tasks (title,subject,due_date,user_id) VALUES (?,?,?,?)",
                       (title, subject, data.get("due_date", ""), session["user_id"]))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return jsonify({"message": "Task added", "task_id": new_id}), 201


@app.route("/api/tasks/<int:task_id>/complete", methods=["PUT"])
def api_complete_task(task_id):
    if not logged_in():
        return jsonify({"error": "Login required"}), 401
    conn = get_db()
    cur = conn.execute("UPDATE tasks SET status='Completed' WHERE task_id=? AND user_id=?",
                       (task_id, session["user_id"]))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"message": "Task completed"}), 200


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def api_delete_task(task_id):
    if not logged_in():
        return jsonify({"error": "Login required"}), 401
    conn = get_db()
    cur = conn.execute("DELETE FROM tasks WHERE task_id=? AND user_id=?",
                       (task_id, session["user_id"]))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"message": "Task deleted"}), 200


# ---------- ERROR HANDLING ----------
@app.errorhandler(404)
def not_found(e):
    return show("login", "Page not found."), 404


@app.errorhandler(500)
def server_error(e):
    return show("login", "Something went wrong. Please try again."), 500


init_db()

if __name__ == "__main__":
    app.run(debug=True)
