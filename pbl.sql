CREATE DATABASE IF NOT EXISTS waste_db;
USE waste_db;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(80) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('user','admin') DEFAULT 'user'
);

CREATE TABLE stop (
    stop_id INT AUTO_INCREMENT PRIMARY KEY,
    stop_name VARCHAR(60) NOT NULL,
    seq_no INT NOT NULL,
    dist_from_prev INT DEFAULT 0
);

CREATE TABLE vehicle (
    vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_no VARCHAR(20) NOT NULL,
    capacity_kg INT NOT NULL,
    current_load INT DEFAULT 0,
    available BOOLEAN DEFAULT TRUE
);

CREATE TABLE worker (
    worker_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    available BOOLEAN DEFAULT TRUE
);

CREATE TABLE waste_request (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    stop_id INT NOT NULL,
    waste_type VARCHAR(30) NOT NULL,
    quantity_kg INT NOT NULL CHECK (quantity_kg > 0),
    priority INT NOT NULL,
    arrival_time INT NOT NULL,
    burst_time INT NOT NULL,
    status ENUM('Pending','Scheduled','In Progress','Completed') DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (stop_id) REFERENCES stop(stop_id)
);

CREATE TABLE schedule_result (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    request_id INT NOT NULL,
    algorithm VARCHAR(20) NOT NULL,
    start_time INT,
    completion_time INT,
    waiting_time INT,
    turnaround_time INT,
    FOREIGN KEY (request_id) REFERENCES waste_request(request_id)
);

CREATE TABLE assignment (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    request_id INT NOT NULL,
    worker_id INT NOT NULL,
    vehicle_id INT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP NULL,
    FOREIGN KEY (request_id) REFERENCES waste_request(request_id),
    FOREIGN KEY (worker_id) REFERENCES worker(worker_id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicle(vehicle_id)
);

INSERT INTO stop (stop_name, seq_no, dist_from_prev) VALUES
('Depot', 1, 0), ('ISBT', 2, 4), ('Subhash Nagar', 3, 3),
('Clement Town', 4, 6), ('Dump Site', 5, 8);

INSERT INTO vehicle (vehicle_no, capacity_kg) VALUES
('UK07-1234', 500), ('UK07-5678', 800), ('UK07-9012', 300);

INSERT INTO worker (name) VALUES ('Ramesh'), ('Suresh'), ('Mahesh'), ('Dinesh');