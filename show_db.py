"""Shows what is stored in the StudySnap database. Run: python show_db.py"""
import sqlite3
import os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "studysnap.db")

if not os.path.exists(DB):
    print("Database not found. Run the app once (python app.py) and register a user first.")
    raise SystemExit

conn = sqlite3.connect(DB)

print("\n=== USERS TABLE ===")
rows = conn.execute("SELECT user_id, name, email, password FROM users").fetchall()
print("%-8s %-15s %-25s %s" % ("user_id", "name", "email", "password (hashed)"))
for r in rows:
    print("%-8s %-15s %-25s %s..." % (r[0], r[1], r[2], r[3][:30]))
if not rows:
    print("(empty)")

print("\n=== TASKS TABLE ===")
rows = conn.execute("SELECT task_id, title, subject, due_date, status, user_id FROM tasks").fetchall()
print("%-8s %-28s %-10s %-12s %-10s %s" % ("task_id", "title", "subject", "due_date", "status", "user_id"))
for r in rows:
    print("%-8s %-28s %-10s %-12s %-10s %s" % (r[0], r[1][:27], r[2][:9], r[3] or "-", r[4], r[5]))
if not rows:
    print("(empty)")
print()
conn.close()
