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
            (name, email, password),
        )

        conn.commit()
        conn.close()

        return "Registration Successful!"

    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)