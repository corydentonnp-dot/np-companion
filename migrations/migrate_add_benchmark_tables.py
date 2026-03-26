"""
Migration: Add benchmark_run and benchmark_result tables.
Engine benchmark testing — tracks correctness and performance over time.
Idempotent — safe to re-run.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'carecompanion.db')


def run():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS benchmark_run (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            engine_filter VARCHAR(50) NOT NULL DEFAULT 'all',
            patient_filter VARCHAR(100) NOT NULL DEFAULT 'all',
            total_tests INTEGER NOT NULL DEFAULT 0,
            passed_tests INTEGER NOT NULL DEFAULT 0,
            failed_tests INTEGER NOT NULL DEFAULT 0,
            total_duration_ms REAL NOT NULL DEFAULT 0.0,
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            finished_at DATETIME,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS benchmark_result (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            patient_id VARCHAR(100) NOT NULL,
            engine VARCHAR(50) NOT NULL,
            test_name VARCHAR(200) NOT NULL,
            passed BOOLEAN NOT NULL,
            explanation TEXT DEFAULT '',
            duration_ms REAL NOT NULL DEFAULT 0.0,
            actual_summary TEXT DEFAULT '{}',
            tested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES benchmark_run(id)
        )
    """)

    try:
        c.execute("CREATE INDEX IF NOT EXISTS idx_benchmark_run_user_id ON benchmark_run(user_id)")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("CREATE INDEX IF NOT EXISTS idx_benchmark_result_run_id ON benchmark_result(run_id)")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("CREATE INDEX IF NOT EXISTS ix_benchmark_result_patient_engine ON benchmark_result(patient_id, engine)")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()
    print("Migration complete: benchmark_run and benchmark_result tables created.")


if __name__ == '__main__':
    run()
