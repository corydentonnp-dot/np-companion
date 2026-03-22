"""
CareCompanion — Phase 25 Tests: BHI / Telehealth + Communication Logging
File: tests/test_bhi_telehealth.py
Phase 25.6  —  15 tests

Usage:
    venv\\Scripts\\python.exe tests/test_bhi_telehealth.py
"""

import os, sys, re, json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

passed, failed = [], []


def _read(relpath):
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base, relpath), encoding="utf-8") as f:
        return f.read()


def run_tests():
    total = 15

    # ---- 1. CommunicationLog model has required columns ----
    label = "[1/15] CommunicationLog model columns"
    try:
        src = _read("models/telehealth.py")
        required = [
            "patient_mrn_hash", "user_id", "communication_type",
            "cumulative_minutes", "clinical_decision_made", "resulted_in_visit",
            "billable_code", "billing_status", "start_datetime",
        ]
        missing = [c for c in required if c not in src]
        assert not missing, f"Missing columns: {missing}"
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 2. CommunicationLog table exists in DB ----
    label = "[2/15] communication_log table in DB"
    try:
        from app import create_app
        from models import db
        app = create_app()
        with app.app_context():
            from sqlalchemy import inspect as sqla_inspect
            tables = sqla_inspect(db.engine).get_table_names()
            assert "communication_log" in tables, f"Table missing. Tables: {tables}"
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 3. Migration file exists ----
    label = "[3/15] Migration file exists"
    try:
        assert os.path.isfile(
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "migrations", "migrate_add_communication_log.py")
        )
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 4. Telehealth engine aggregation function exists ----
    label = "[4/15] get_telehealth_fields function"
    try:
        src = _read("app/services/telehealth_engine.py")
        assert "def get_telehealth_fields" in src
        assert "phone_encounter_minutes" in src
        assert "portal_message_minutes_7day" in src
        assert "behavioral_dx_minutes" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 5. Telehealth routes exist ----
    label = "[5/15] Telehealth routes (POST + GET)"
    try:
        src = _read("routes/telehealth.py")
        assert "communication-log" in src
        assert "methods=['POST']" in src or 'methods=["POST"]' in src
        assert "def get_communications" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 6. Blueprint registered ----
    label = "[6/15] Telehealth blueprint in app/__init__.py"
    try:
        src = _read("app/__init__.py")
        assert "routes.telehealth" in src
        assert "telehealth_bp" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 7. Telehealth detector expects phone_encounter_minutes ----
    label = "[7/15] Telehealth detector reads phone_encounter_minutes"
    try:
        src = _read("billing_engine/detectors/telehealth.py")
        assert "phone_encounter_minutes" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 8. BHI detector reads behavioral_dx_minutes ----
    label = "[8/15] BHI detector reads behavioral_dx_minutes"
    try:
        src = _read("billing_engine/detectors/bhi.py")
        assert "behavioral_dx_minutes" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 9. api_scheduler wires telehealth fields into patient_data ----
    label = "[9/15] api_scheduler populates telehealth fields"
    try:
        src = _read("app/services/api_scheduler.py")
        assert "get_telehealth_fields" in src
        assert "tele_fields" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 10. agent_service wires telehealth fields into patient_data ----
    label = "[10/15] agent_service populates telehealth fields"
    try:
        src = _read("agent_service.py")
        assert "get_telehealth_fields" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 11. Phone E/M code tiers (99441-99443) ----
    label = "[11/15] Telehealth detector phone code tiers"
    try:
        src = _read("billing_engine/detectors/telehealth.py")
        assert "99441" in src
        assert "99442" in src
        assert "99443" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 12. Portal E/M code tiers (99421-99423) ----
    label = "[12/15] Telehealth detector portal code tiers"
    try:
        src = _read("billing_engine/detectors/telehealth.py")
        assert "99421" in src
        assert "99422" in src
        assert "99423" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 13. 24hr face-to-face exclusion ----
    label = "[13/15] Phone E/M face-to-face exclusion"
    try:
        src = _read("billing_engine/detectors/telehealth.py")
        assert "resulted_in_visit" in src or "phone_resulted_in_visit_24hr" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 14. Quick-log widget in patient chart ----
    label = "[14/15] Telehealth quick-log widget in patient_chart.html"
    try:
        src = _read("templates/patient_chart.html")
        assert "telehealth-log" in src
        assert "tele-start-btn" in src or "teleTimerToggle" in src
        assert "communication-log" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- 15. Stopwatch timer JS + save function ----
    label = "[15/15] Timer JS: teleTimerToggle + teleSave"
    try:
        src = _read("templates/patient_chart.html")
        assert "teleTimerToggle" in src
        assert "teleSave" in src
        assert "_teleStart" in src
        assert "cumulative_minutes" in src
        passed.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

    # ---- Summary ----
    print(f"\n{'='*60}")
    print(f"Phase 25 — BHI / Telehealth Tests: {len(passed)}/{total} passed")
    print(f"{'='*60}")
    for p in passed:
        print(f"  PASS  {p}")
    for f in failed:
        print(f"  FAIL  {f}")
    print()
    return len(failed) == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
