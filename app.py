from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import date, datetime, timedelta

app = Flask(__name__)
app.secret_key = "super-secret-key"

def get_db():
    return sqlite3.connect("db.sqlite3")

def init_db():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS diary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        content TEXT,
        UNIQUE(user_id, date)
    )
    """)

    db.commit()

init_db()

def get_diary(user_id, d):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "SELECT content FROM diary WHERE user_id=? AND date=?",
        (user_id, d)
    )
    row = cur.fetchone()
    return row[0] if row else ""

# ---------- AUTH ----------

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "SELECT id FROM users WHERE username=? AND password=?",
            (request.form["username"], request.form["password"])
        )
        user = cur.fetchone()
        if user:
            session["user_id"] = user[0]
            return redirect("/view")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO users(username,password) VALUES (?,?)",
            (request.form["username"], request.form["password"])
        )
        db.commit()
        return redirect("/")
    return render_template("register.html")

# ---------- VIEW (READ ONLY) ----------

@app.route("/view")
def view():
    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]
    d = request.args.get("date")

    if not d:
        d = date.today().isoformat()

    content = get_diary(user_id, d)

    d_obj = datetime.strptime(d, "%Y-%m-%d").date()
    prev_day = (d_obj - timedelta(days=1)).isoformat()

    today = date.today()
    next_day = None
    if d_obj < today:
        next_day = (d_obj + timedelta(days=1)).isoformat()

    return render_template(
        "view.html",
        date=d,
        content=content,
        prev_day=prev_day,
        next_day=next_day
    )

# ---------- EDIT ----------

@app.route("/edit")
def edit():
    if "user_id" not in session:
        return redirect("/")

    d = request.args.get("date")
    user_id = session["user_id"]
    content = get_diary(user_id, d)

    return render_template("edit.html", date=d, content=content)

@app.route("/save", methods=["POST"])
def save():
    user_id = session["user_id"]
    d = request.form["date"]
    content = request.form["content"]

    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO diary(user_id, date, content)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, date)
        DO UPDATE SET content=excluded.content
    """, (user_id, d, content))
    db.commit()

    return redirect(f"/view?date={d}")

if __name__ == "__main__":
    app.run()
