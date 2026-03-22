"""
Migration: Add missing indexes on foreign key columns.

These FK columns are used in JOIN and WHERE clauses but were defined
without index=True, causing sequential scans on larger tables.
"""

import sqlite3
import os


def run(db_path):
    """Add indexes on foreign key columns that lack them."""
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    indexes = [
        ("ix_audit_log_user_id", "audit_log", "user_id"),
        ("ix_patient_records_claimed_by", "patient_records", "claimed_by"),
        ("ix_agent_error_log_user_id", "agent_error_log", "user_id"),
        ("ix_calculator_result_user_id", "calculator_result", "user_id"),
        ("ix_oncall_notes_forwarded_to", "oncall_notes", "forwarded_to"),
        ("ix_handoff_links_user_id", "handoff_links", "user_id"),
        ("ix_order_executions_user_id", "order_executions", "user_id"),
        ("ix_result_templates_copied_from", "result_templates", "copied_from_id"),
        ("ix_practice_bookmark_created_by", "practice_bookmark", "created_by"),
        ("ix_care_gaps_addressed_by", "care_gaps", "addressed_by"),
        ("ix_patient_medications_reviewed_by", "patient_medications", "reviewed_by"),
        ("ix_order_sets_shared_by", "order_sets", "shared_by_user_id"),
        ("ix_order_sets_forked_from", "order_sets", "forked_from_id"),
        ("ix_order_set_versions_saved_by", "order_set_versions", "saved_by_user_id"),
        ("ix_ticklers_assigned_to", "ticklers", "assigned_to_user_id"),
    ]

    for idx_name, table, column in indexes:
        try:
            cursor.execute(
                f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({column})"
            )
        except sqlite3.OperationalError:
            # Table may not exist yet on fresh installs
            pass

    conn.commit()
    conn.close()
