from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("civicconnect.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, password)
        )

        conn.commit()
        conn.close()

        return "Registration Successful!"

    return render_template("register.html")

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
            return "Login Successful!"
        else:
            return "Invalid Email or Password"

    return render_template("login.html")

@app.route("/report", methods=["GET", "POST"])
def report_issue():
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

        return "Issue Report Submitted Successfully!"

    return render_template("report_issue.html")

@app.route("/issues")
def my_issues():
    conn = sqlite3.connect("civicconnect.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM issues")
    issues = cursor.fetchall()

    conn.close()

    return render_template("my_issues.html", issues=issues)

@app.route("/admin")
def admin_dashboard():
    conn = sqlite3.connect("civicconnect.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM issues")
    issues = cursor.fetchall()

    conn.close()

    return render_template("admin_dashboard.html", issues=issues)

@app.route("/update_status/<int:issue_id>", methods=["POST"])
def update_status(issue_id):
    status = request.form["status"]

    conn = sqlite3.connect("civicconnect.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE issues SET status=? WHERE id=?",
        (status, issue_id)
    )

    conn.commit()
    conn.close()

    return admin_dashboard()

if __name__ == "__main__":
    app.run(debug=True)