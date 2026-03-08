DROP TABLE IF EXISTS sim_responses;
DROP TABLE IF EXISTS pre_sim_responses;

CREATE TABLE pre_sim_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pq1 TEXT NOT NULL,
    pq1_correct INTEGER NOT NULL,
    pq2 TEXT NOT NULL,
    pq2_correct INTEGER NOT NULL,
    pq3 TEXT NOT NULL,
    pq3_correct INTEGER NOT NULL,
    pq4 TEXT NOT NULL,
    pq4_correct INTEGER NOT NULL,
    pq5 TEXT NOT NULL,
    pq5_correct INTEGER NOT NULL
);

CREATE TABLE sim_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pq1 TEXT NOT NULL,
    pq1_correct INTEGER NOT NULL,
    pq2 TEXT NOT NULL,
    pq2_correct INTEGER NOT NULL,
    pq3 TEXT NOT NULL,
    pq3_correct INTEGER NOT NULL,
    pq4 TEXT NOT NULL,
    pq4_correct INTEGER NOT NULL,
    pq5 TEXT NOT NULL,
    pq5_correct INTEGER NOT NULL
);

