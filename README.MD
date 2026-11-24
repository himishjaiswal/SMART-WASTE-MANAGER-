# Smart Waste Collection Management System (Team EcoTech)

Waste pickup requests are treated like OS processes. A vehicle is the CPU.
The system picks FCFS, SJF or Priority scheduling automatically and assigns
a vehicle and worker using MySQL transactions.

## Tech
Python Flask, MySQL, C (scheduler), HTML/CSS

## Setup
1. Install Python, MySQL and gcc.
2. `pip install flask mysql-connector-python`
3. Run `schema.sql` in MySQL.
4. Compile the scheduler: `cd scheduler` then `gcc scheduler.c -o scheduler`
5. Put your MySQL password in `get_db()` in `app.py`.
6. Run `python app.py` and open http://127.0.0.1:5000
7. To make an admin: `UPDATE users SET role='admin' WHERE email='your@email';`

## Features
- Register and login with hashed passwords
- Request form (arrival, burst time and priority calculated automatically)
- Automatic algorithm selection, aging against starvation
- Admin-only Run scheduler, Start and Complete
- Capacity check and multiple vehicles
- Transactions, row locking (FOR UPDATE), fixed lock order against deadlock

## Team
- Himish Jaiswal: integration and assignment
- Sumit Singh Sajwan: C scheduler and algorithms
- Gaganpreet Singh: database, admin and testing