from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import time

app = Flask(__name__)
app.secret_key = "ecotech_secret"      # needed for login sessions

# the route starts when the server starts
route_start = time.time()

# base pickup time in minutes for each waste type
base_time = {"General": 3, "Wet": 5, "Hazardous": 8}

# priority of each waste type (1 = most urgent)
priority_of = {"Hazardous": 1, "General": 2, "Wet": 2}

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

    db = get_db()
    cur = db.cursor()

    # stops the user can choose from (not the depot or dump site)
    cur.execute("SELECT stop_id, stop_name FROM stop WHERE stop_name NOT IN ('Depot', 'Dump Site')")
    stops = cur.fetchall()

    # this user's requests, joined with the stop name
    cur.execute("""SELECT r.request_id, s.stop_name, r.waste_type, r.quantity_kg,
                          r.arrival_time, r.burst_time, r.priority, r.status
                   FROM waste_request r JOIN stop s ON r.stop_id = s.stop_id
                   WHERE r.user_id = %s ORDER BY r.request_id DESC""",
                (session["user_id"],))
    requests = cur.fetchall()
    db.close()

    return render_template("dashboard.html", name=session["name"],
                           stops=stops, requests=requests)


@app.route("/request", methods=["POST"])
def make_request():
    if "user_id" not in session:
        return redirect("/login")

    stop_id = request.form["stop_id"]
    waste_type = request.form["waste_type"]
    quantity = int(request.form["quantity"])

    if quantity <= 0:
        return redirect("/dashboard")

    # system fills the OS fields, the user does not enter them
    arrival = int((time.time() - route_start) / 60)    # minutes since route started
    burst = base_time[waste_type] + quantity // 20     # pickup time in minutes
    priority = priority_of[waste_type]

    db = get_db()
    cur = db.cursor()
    cur.execute("""INSERT INTO waste_request
                   (user_id, stop_id, waste_type, quantity_kg, priority, arrival_time, burst_time)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (session["user_id"], stop_id, waste_type, quantity, priority, arrival, burst))
    db.commit()
    db.close()
    return redirect("/dashboard")

    
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)