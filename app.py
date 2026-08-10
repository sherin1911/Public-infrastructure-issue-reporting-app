from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "civicconnect_secret_key"

# -----------------------------
# Home
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")

# -----------------------------
# Citizen Registration
# -----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("civicconnect.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Email already registered!"

        conn.close()
        return redirect(url_for("login"))

    return render_template("register.html")

# -----------------------------
# Citizen Login
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("civicconnect.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            session["user_email"] = email
            return redirect(url_for("home"))
        else:
            return "Invalid Email or Password"

    return render_template("login.html")

# -----------------------------
# Admin Login
# -----------------------------
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if email == "admin@civicconnect.com" and password == "admin123":
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            return "Invalid Admin Credentials"

    return render_template("admin_login.html")

# -----------------------------
# Logout
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# -----------------------------
# Report Issue
# -----------------------------
@app.route("/report", methods=["GET", "POST"])
def report_issue():
    if "user_email" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        category = request.form["category"]
        location = request.form["location"]
        description = request.form["description"]

        conn = sqlite3.connect("civicconnect.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO issues (category, location, description) VALUES (?, ?, ?)",
            (category, location, description)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("my_issues"))

    return render_template("report_issue.html")

# -----------------------------
# My Reported Issues
# -----------------------------
@app.route("/issues")
def my_issues():
    if "user_email" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("civicconnect.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM issues ORDER BY id DESC")
    issues = cursor.fetchall()

    conn.close()

    return render_template("my_issues.html", issues=issues)

# -----------------------------
# Admin Dashboard
# -----------------------------
@app.route("/admin")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect("civicconnect.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM issues ORDER BY id DESC")
    issues = cursor.fetchall()

    conn.close()

    return render_template("admin_dashboard.html", issues=issues)

# -----------------------------
# Update Issue Status
# -----------------------------
@app.route("/update_status/<int:issue_id>", methods=["POST"])
def update_status(issue_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    status = request.form["status"]

    conn = sqlite3.connect("civicconnect.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE issues SET status=? WHERE id=?",
        (status, issue_id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin_dashboard"))

# -----------------------------
# Run Application
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)