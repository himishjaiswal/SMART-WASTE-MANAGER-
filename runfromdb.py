import subprocess
import mysql.connector

def choose_algorithm(rows):
    # rows = list of (id, arrival, burst, priority)
    priorities = [r[3] for r in rows]
    bursts = [r[2] for r in rows]

    if 1 in priorities:
        return "PRIORITY"          # an urgent request is waiting
    if max(bursts) - min(bursts) > 5:
        return "SJF"               # burst times differ a lot
    return "FCFS"                  # otherwise first come first served

# 1. read the pending requests from MySQL
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Sumit@123",
    database="waste_db"
)
cur = db.cursor()
cur.execute("""SELECT request_id, arrival_time, burst_time, priority
               FROM waste_request WHERE status = 'Pending'""")
rows = cur.fetchall()
db.close()

print("Pending requests from database:")
for r in rows:
    print(r)

# 2. build the input text for the C program
algo = choose_algorithm(rows)
print("\nAlgorithm chosen by system:", algo)
quantum = 2
input_text = algo + "\n" + str(quantum) + "\n" + str(len(rows)) + "\n"
for r in rows:
    input_text = input_text + str(r[0]) + " " + str(r[1]) + " " + str(r[2]) + " " + str(r[3]) + "\n"

# 3. run the C program
result = subprocess.run(["scheduler/scheduler.exe"],
                        input=input_text,
                        capture_output=True,
                        text=True)

# 4. turn the output lines into Python data
print("\nResult (id, start, completion, waiting, turnaround):")
for line in result.stdout.strip().split("\n"):
    parts = line.split()
    print(parts)


# 5. save the results back in MySQL
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Sumit@123",
    database="waste_db"
)
cur = db.cursor()

for line in result.stdout.strip().split("\n"):
    p = line.split()
    req_id = int(p[0])
    cur.execute("""INSERT INTO schedule_result
                   (request_id, algorithm, start_time, completion_time, waiting_time, turnaround_time)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (req_id, algo, int(p[1]), int(p[2]), int(p[3]), int(p[4])))
    cur.execute("UPDATE waste_request SET status = 'Scheduled' WHERE request_id = %s", (req_id,))

db.commit()
db.close()
print("\nResults saved in schedule_result")