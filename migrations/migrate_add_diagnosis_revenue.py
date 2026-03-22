"""
Migration: Add DiagnosisRevenueProfile table + BillingOpportunity scoring columns
+ seed from Priority ICD10 CSV.

Phase 18.2 — Idempotent.
"""

import csv
import os
import re
import sqlite3


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "carecompanion.db")
CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "Documents", "billing_resources",
    "calendar_year_dx_revenue_priority_icd10.csv",
)


def _parse_dollar(val):
    """Parse '$1,234.56' → 1234.56"""
    if not val:
        return 0.0
    return float(re.sub(r'[,$]', '', val.strip()))


def _parse_pct(val):
    """Parse '17.96%' → 0.1796"""
    if not val:
        return 0.0
    return float(val.strip().replace('%', '')) / 100


def run():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # --- 1. Create diagnosis_revenue_profile table ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS diagnosis_revenue_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icd10_code TEXT NOT NULL UNIQUE,
            icd10_description TEXT,
            encounters_annual INTEGER DEFAULT 0,
            billed_annual REAL DEFAULT 0.0,
            received_annual REAL DEFAULT 0.0,
            adjusted_annual REAL DEFAULT 0.0,
            adjustment_rate REAL DEFAULT 0.0,
            revenue_per_encounter REAL DEFAULT 0.0,
            retention_score REAL DEFAULT 0.0,
            priority_tier TEXT,
            frequency_score REAL DEFAULT 0.0,
            payment_score REAL DEFAULT 0.0
        )
    """)

    # Index on icd10_code
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_drp_icd10
        ON diagnosis_revenue_profile (icd10_code)
    """)

    # --- 2. Add scoring columns to billing_opportunity (idempotent) ---
    existing = {row[1] for row in c.execute("PRAGMA table_info(billing_opportunity)").fetchall()}
    new_cols = [
        ("expected_net_dollars", "REAL"),
        ("bonus_impact_dollars", "REAL"),
        ("bonus_impact_days", "REAL"),
        ("opportunity_score", "REAL"),
        ("urgency_score", "REAL"),
        ("implementation_priority", "TEXT"),
    ]
    for col_name, col_type in new_cols:
        if col_name not in existing:
            c.execute(f"ALTER TABLE billing_opportunity ADD COLUMN {col_name} {col_type}")
            print(f"  Added billing_opportunity.{col_name}")

    # --- 3. Seed from CSV ---
    if not os.path.exists(CSV_PATH):
        print(f"  CSV not found at {CSV_PATH} — skipping seed")
        conn.commit()
        conn.close()
        return

    seeded = 0
    with open(CSV_PATH, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_icd = row.get('ICD & Description', '').strip()
            if not raw_icd:
                continue

            # ICD code is everything before the first space
            parts = raw_icd.split(' ', 1)
            icd10_code = parts[0].strip()
            icd10_desc = parts[1].strip() if len(parts) > 1 else ''

            encounters = int(row.get('Encounters', '0').strip() or 0)
            billed = _parse_dollar(row.get('$ Billed ', ''))
            received = _parse_dollar(row.get('$ Recieved', ''))
            adjusted = _parse_dollar(row.get('$ adjusted', ''))
            adj_rate = _parse_pct(row.get('% adjust', ''))
            rev_per_enc = _parse_dollar(row.get('$/ Encounter', ''))
            freq_score = float(row.get('Frequency Score', '0').strip() or 0)
            payment_score = float(row.get('Payment Score', '0').strip() or 0)
            retention = _parse_pct(row.get('Retention Score', ''))
            tier = row.get('Teir', '').strip()

            c.execute("""
                INSERT INTO diagnosis_revenue_profile
                    (icd10_code, icd10_description, encounters_annual,
                     billed_annual, received_annual, adjusted_annual,
                     adjustment_rate, revenue_per_encounter, retention_score,
                     priority_tier, frequency_score, payment_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(icd10_code) DO UPDATE SET
                    icd10_description=excluded.icd10_description,
                    encounters_annual=excluded.encounters_annual,
                    billed_annual=excluded.billed_annual,
                    received_annual=excluded.received_annual,
                    adjusted_annual=excluded.adjusted_annual,
                    adjustment_rate=excluded.adjustment_rate,
                    revenue_per_encounter=excluded.revenue_per_encounter,
                    retention_score=excluded.retention_score,
                    priority_tier=excluded.priority_tier,
                    frequency_score=excluded.frequency_score,
                    payment_score=excluded.payment_score
            """, (icd10_code, icd10_desc, encounters, billed, received,
                  adjusted, adj_rate, rev_per_enc, retention, tier,
                  freq_score, payment_score))
            seeded += 1

    conn.commit()
    conn.close()
    print(f"  Seeded {seeded} ICD-10 revenue profiles from CSV")


if __name__ == '__main__':
    run()
    print("Migration complete.")
