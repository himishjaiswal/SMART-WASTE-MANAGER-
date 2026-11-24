from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import time
import subprocess

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


def is_admin():
    return session.get("role") == "admin"

def choose_algorithm(rows):
    # rows = list of (id, arrival, burst, priority)
    priorities = [r[3] for r in rows]
    bursts = [r[2] for r in rows]

    if 1 in priorities:
        return "PRIORITY"          # an urgent request is waiting
    if max(bursts) - min(bursts) > 5:
        return "SJF"               # burst times differ a lot
    return "FCFS"                  # otherwise first come first served


def run_scheduler():
    db = get_db()
    cur = db.cursor()
    try:
        # lock the pending rows so another run cannot take them at the same time
        cur.execute("""SELECT request_id, arrival_time, burst_time, priority
                       FROM waste_request WHERE status = 'Pending' FOR UPDATE""")
        rows = cur.fetchall()

        if len(rows) == 0:
            db.rollback()
            return None

        # aging: every 10 minutes a request has waited, its priority number drops by 1
        # (a smaller number is more urgent, and it never goes below 1)
        now = int((time.time() - route_start) / 60)
        aged_rows = []
        for r in rows:
            waited = now - r[1]                      # minutes since it arrived
            if waited < 0:
                waited = 0                           # arrival clock reset after a restart
            new_priority = max(1, r[3] - waited // 10)
            aged_rows.append((r[0], r[1], r[2], new_priority))
        rows = aged_rows

        algo = choose_algorithm(rows)
        quantum = 2

        # make the input text for the C program
        text = algo + "\n" + str(quantum) + "\n" + str(len(rows)) + "\n"
        for r in rows:
            text = text + str(r[0]) + " " + str(r[1]) + " " + str(r[2]) + " " + str(r[3]) + "\n"

        result = subprocess.run(["scheduler/scheduler.exe"],
                                input=text, capture_output=True, text=True)

        # save every result line
        for line in result.stdout.strip().split("\n"):
            p = line.split()
            rid = int(p[0])
            cur.execute("""INSERT INTO schedule_result
                           (request_id, algorithm, start_time, completion_time, waiting_time, turnaround_time)
                           VALUES (%s, %s, %s, %s, %s, %s)""",
                        (rid, algo, int(p[1]), int(p[2]), int(p[3]), int(p[4])))
            cur.execute("UPDATE waste_request SET status = 'Scheduled' WHERE request_id = %s", (rid,))

        db.commit()      # save everything together
        return algo
    except Exception:
        db.rollback()    # something failed, so undo everything
        raise
    finally:
        db.close()

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

    cur.execute("SELECT stop_id, stop_name FROM stop WHERE stop_name NOT IN ('Depot', 'Dump Site')")
    stops = cur.fetchall()

    if is_admin():
        # admin sees every user's requests
        cur.execute("""SELECT r.request_id, s.stop_name, r.waste_type, r.quantity_kg,
                              r.arrival_time, r.burst_time, r.priority, r.status, u.name
                       FROM waste_request r
                       JOIN stop s ON r.stop_id = s.stop_id
                       JOIN users u ON r.user_id = u.user_id
                       ORDER BY r.request_id DESC""")
    else:
        # normal user sees only their own requests
        cur.execute("""SELECT r.request_id, s.stop_name, r.waste_type, r.quantity_kg,
                              r.arrival_time, r.burst_time, r.priority, r.status, u.name
                       FROM waste_request r
                       JOIN stop s ON r.stop_id = s.stop_id
                       JOIN users u ON r.user_id = u.user_id
                       WHERE r.user_id = %s
                       ORDER BY r.request_id DESC""", (session["user_id"],))
    requests = cur.fetchall()
    db.close()

    return render_template("dashboard.html", name=session["name"],
                           stops=stops, requests=requests, role=session["role"])


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

@app.route("/run_scheduler", methods=["POST"])
def run_scheduler_route():
    if "user_id" not in session:
        return redirect("/login")
    if not is_admin():
        return redirect("/dashboard")

    run_scheduler()
    return redirect("/results")


@app.route("/results")
def results():
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()
    cur.execute("""SELECT r.request_id, s.stop_name, r.waste_type, r.priority,
                          sr.algorithm, sr.start_time, sr.completion_time,
                          sr.waiting_time, sr.turnaround_time, r.status
                   FROM schedule_result sr
                   JOIN waste_request r ON sr.request_id = r.request_id
                   JOIN stop s ON r.stop_id = s.stop_id
                   ORDER BY sr.result_id DESC""")
    rows = cur.fetchall()
    db.close()
    return render_template("results.html", rows=rows, role=session["role"],
                           msg=request.args.get("msg"))

@app.route("/start/<int:req_id>", methods=["POST"])
def start_request(req_id):
    if "user_id" not in session:
        return redirect("/login")
    if not is_admin():
        return redirect("/dashboard")

    db = get_db()
    cur = db.cursor()
    try:
        # lock the request and check it is Scheduled
        cur.execute("SELECT status, quantity_kg FROM waste_request WHERE request_id = %s FOR UPDATE", (req_id,))
        row = cur.fetchone()
        if row is None or row[0] != "Scheduled":
            db.rollback()
            return redirect("/results")

        # lock order is always: vehicle first, then worker
        # pick the smallest free vehicle that can carry this load
        cur.execute("""SELECT vehicle_id FROM vehicle
                       WHERE available = TRUE AND capacity_kg >= %s
                       ORDER BY capacity_kg LIMIT 1 FOR UPDATE""", (row[1],))
        vehicle = cur.fetchone()
        cur.execute("SELECT worker_id FROM worker WHERE available = TRUE LIMIT 1 FOR UPDATE")
        worker = cur.fetchone()

        if vehicle is None or worker is None:
            db.rollback()          # nothing free that fits, request stays Scheduled
            return redirect("/results?msg=No free vehicle or worker fits this request")

        cur.execute("INSERT INTO assignment (request_id, worker_id, vehicle_id) VALUES (%s, %s, %s)",
                    (req_id, worker[0], vehicle[0]))
        cur.execute("UPDATE vehicle SET available = FALSE WHERE vehicle_id = %s", (vehicle[0],))
        cur.execute("UPDATE worker SET available = FALSE WHERE worker_id = %s", (worker[0],))
        cur.execute("UPDATE waste_request SET status = 'In Progress' WHERE request_id = %s", (req_id,))

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return redirect("/results")


@app.route("/complete/<int:req_id>", methods=["POST"])
def complete_request(req_id):
    if "user_id" not in session:
        return redirect("/login")
    if not is_admin():
        return redirect("/dashboard")

    db = get_db()
    cur = db.cursor()
    try:
        # lock the request and check it is really In Progress
        cur.execute("SELECT status FROM waste_request WHERE request_id = %s FOR UPDATE", (req_id,))
        row = cur.fetchone()
        if row is None or row[0] != "In Progress":
            db.rollback()
            return redirect("/results")

        # find which worker and vehicle were given to this request
        cur.execute("""SELECT assignment_id, worker_id, vehicle_id FROM assignment
                       WHERE request_id = %s AND finished_at IS NULL""", (req_id,))
        a = cur.fetchone()
        if a is None:
            db.rollback()
            return redirect("/results")

        # same lock order as start: vehicle first, then worker
        cur.execute("UPDATE vehicle SET available = TRUE WHERE vehicle_id = %s", (a[2],))
        cur.execute("UPDATE worker SET available = TRUE WHERE worker_id = %s", (a[1],))
        cur.execute("UPDATE assignment SET finished_at = NOW() WHERE assignment_id = %s", (a[0],))
        cur.execute("UPDATE waste_request SET status = 'Completed' WHERE request_id = %s", (req_id,))

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return redirect("/results")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)