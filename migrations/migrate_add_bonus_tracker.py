"""
Migration: Add bonus_tracker table.
Phase 17.2 — BonusTracker model for provider bonus structure and receipt tracking.
Idempotent — safe to re-run.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'carecompanion.db')


def run():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS bonus_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            provider_name VARCHAR(200) DEFAULT 'Cory Denton, FNP',
            start_date DATE DEFAULT '2026-03-02',
            base_salary REAL DEFAULT 115000.0,
            quarterly_threshold REAL DEFAULT 105000.0,
            bonus_multiplier REAL DEFAULT 0.25,
            deficit_resets_annually BOOLEAN DEFAULT 1,
            monthly_receipts TEXT DEFAULT '{}',
            collection_rates TEXT DEFAULT '{"medicare": 0.67, "medicaid": 0.60, "commercial": 0.57, "self_pay": 0.35}',
            projected_first_bonus_quarter VARCHAR(10),
            projected_first_bonus_date DATE,
            threshold_confirmed BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    try:
        c.execute("CREATE INDEX IF NOT EXISTS idx_bonus_tracker_user_id ON bonus_tracker(user_id)")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()
    print("Migration complete: bonus_tracker table created.")


if __name__ == '__main__':
    run()
