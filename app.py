from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "civicconnect-secret-key"

# -----------------------------
# Configuration
# -----------------------------

DATABASE = "civicconnect.db"
UPLOAD_FOLDER = os.path.join("static", "uploads")

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp"
}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB maximum

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# -----------------------------
# Database Helper
# -----------------------------

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# Check File Extension
# -----------------------------

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


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

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not name or not email or not password:
            return "Please fill all fields."

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO users (name, email, password)
                VALUES (?, ?, ?)
                """,
                (name, email, password)
            )

            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return "Email already registered."

        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# -----------------------------
# Citizen Login
# -----------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db_connection()

        user = conn.execute(
            """
            SELECT * FROM users
            WHERE email = ? AND password = ?
            """,
            (email, password)
        ).fetchone()

        conn.close()

        if user:

            session.clear()

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            session["role"] = "citizen"

            return redirect(url_for("home"))

        return "Invalid email or password."

    return render_template("login.html")


# -----------------------------
# Admin Login
# -----------------------------

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if (
            email == "admin@civicconnect.com"
            and password == "admin123"
        ):

            session.clear()

            session["admin"] = True
            session["role"] = "admin"
            session["admin_email"] = email

            return redirect(url_for("admin_dashboard"))

        return "Invalid admin email or password."

    return render_template("admin_login.html")


# -----------------------------
# Report Issue
# -----------------------------

@app.route("/report", methods=["GET", "POST"])
def report_issue():

    # Citizen must be logged in
    if session.get("role") != "citizen":
        return redirect(url_for("login"))

    if request.method == "POST":

        category = request.form.get("category", "").strip()
        location = request.form.get("location", "").strip()
        description = request.form.get("description", "").strip()

        image_filename = None

        # -------------------------
        # Handle Image Upload
        # -------------------------

        image = request.files.get("image")

        if image and image.filename:

            if allowed_file(image.filename):

                original_name = secure_filename(image.filename)

                # Add user ID to filename to reduce duplicate names
                user_id = session.get("user_id")

                image_filename = f"{user_id}_{original_name}"

                image_path = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    image_filename
                )

                image.save(image_path)

            else:
                return "Invalid image format. Please upload PNG, JPG, JPEG, GIF or WEBP."

        # -------------------------
        # Validate Form
        # -------------------------

        if not category or not location or not description:
            return "Please fill all required fields."

        # -------------------------
        # Save Issue
        # -------------------------

        conn = get_db_connection()

        conn.execute(
            """
            INSERT INTO issues
            (category, location, description, status, image)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                category,
                location,
                description,
                "Pending",
                image_filename
            )
        )

        conn.commit()
        conn.close()

        return redirect(url_for("my_issues"))

    return render_template("report_issue.html")


# -----------------------------
# View My Issues
# -----------------------------

@app.route("/issues")
def my_issues():

    if session.get("role") != "citizen":
        return redirect(url_for("login"))

    conn = get_db_connection()

    issues = conn.execute(
        """
        SELECT *
        FROM issues
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "my_issues.html",
        issues=issues
    )


# -----------------------------
# Admin Dashboard
# -----------------------------

@app.route("/admin")
def admin_dashboard():

    # Only admin can access
    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))

    conn = get_db_connection()

    issues = conn.execute(
        """
        SELECT *
        FROM issues
        ORDER BY id DESC
        """
    ).fetchall()

    # Statistics
    total = conn.execute(
        "SELECT COUNT(*) FROM issues"
    ).fetchone()[0]

    pending = conn.execute(
        "SELECT COUNT(*) FROM issues WHERE status = 'Pending'"
    ).fetchone()[0]

    in_progress = conn.execute(
        "SELECT COUNT(*) FROM issues WHERE status = 'In Progress'"
    ).fetchone()[0]

    resolved = conn.execute(
        "SELECT COUNT(*) FROM issues WHERE status = 'Resolved'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "admin_dashboard.html",
        issues=issues,
        total=total,
        pending=pending,
        in_progress=in_progress,
        resolved=resolved
    )


# -----------------------------
# Update Issue Status
# -----------------------------

@app.route("/update_status/<int:issue_id>", methods=["POST"])
def update_status(issue_id):

    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))

    status = request.form.get("status")

    allowed_statuses = [
        "Pending",
        "In Progress",
        "Resolved"
    ]

    if status not in allowed_statuses:
        return "Invalid status."

    conn = get_db_connection()

    conn.execute(
        """
        UPDATE issues
        SET status = ?
        WHERE id = ?
        """,
        (status, issue_id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin_dashboard"))


# -----------------------------
# Logout
# -----------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# -----------------------------
# Run Application
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True)