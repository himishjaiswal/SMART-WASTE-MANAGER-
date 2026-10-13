from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

app = Flask(__name__)
app.secret_key = "ecotech_secret"      # needed for login sessions


def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Sumit@123",
        database="waste_db"
    )


@app.route("/")
def home():
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        cur = db.cursor()

        # check if email is already used
        cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            db.close()
            return render_template("register.html", error="Email already registered")

        hashed = generate_password_hash(password)
        cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                    (name, email, hashed))
        db.commit()
        db.close()
        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT user_id, name, password, role FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        db.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["name"] = user[1]
            session["role"] = user[3]
            return redirect("/dashboard")

        return render_template("login.html", error="Wrong email or password")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("dashboard.html", name=session["name"])


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)