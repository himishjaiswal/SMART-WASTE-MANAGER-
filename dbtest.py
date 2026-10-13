import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Sumit@123",
    database="waste_db"
)
cur = db.cursor()
cur.execute("SELECT request_id, arrival_time, burst_time, priority FROM waste_request")
for row in cur.fetchall():
    print(row)