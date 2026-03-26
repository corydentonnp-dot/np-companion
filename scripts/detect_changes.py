"""
CareCompanion -- Detect Changes & Suggest Tests
scripts/detect_changes.py

Reads `git diff --name-only` (or a supplied list of paths) and prints
the test files/directories that should be run for the changed sources.

Usage:
    # Auto-detect from git working tree
    venv\\Scripts\\python.exe scripts/detect_changes.py

    # Against a specific commit
    venv\\Scripts\\python.exe scripts/detect_changes.py --ref HEAD~3

    # Explicit file list (one per line on stdin)
    echo routes/bonus.py | venv\\Scripts\\python.exe scripts/detect_changes.py --stdin

Exit codes:
    0 = found relevant tests
    1 = no changes detected
    2 = error (git not available, etc.)
"""

import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ======================================================================
# File-to-Test mapping (mirrors Documents/dev_guide/qa/FILE_TO_BLOCKS.md)
# ======================================================================

FILE_TO_BLOCKS = {
    # Routes
    "routes/auth.py": ["tests/test_auth.py"],
    "routes/admin.py": ["tests/test_admin.py", "tests/test_admin_panel.py"],
    "routes/agent_api.py": ["tests/test_agent_api.py"],
    "routes/bonus.py": ["tests/test_bonus_dashboard.py"],
    "routes/calculator.py": ["tests/test_calculators.py"],
    "routes/caregap.py": ["tests/test_caregap_engine.py", "tests/test_caregap_comprehensive.py"],
    "routes/ccm.py": ["tests/test_ccm.py"],
    "routes/dashboard.py": ["tests/test_dashboard_schedule.py"],
    "routes/inbox.py": ["tests/test_inbox_monitor.py"],
    "routes/intelligence.py": ["tests/test_morning_briefing.py"],
    "routes/labtrack.py": ["tests/test_labtrack.py"],
    "routes/medref.py": ["tests/test_medref.py"],
    "routes/message.py": ["tests/test_messages.py"],
    "routes/monitoring.py": ["tests/test_monitoring_calendar.py"],
    "routes/oncall.py": ["tests/test_oncall.py"],
    "routes/orders.py": ["tests/test_orders.py"],
    "routes/patient.py": ["tests/test_patient_chart.py"],
    "routes/revenue.py": ["tests/test_revenue.py"],
    "routes/telehealth.py": ["tests/test_telehealth.py"],
    "routes/timer.py": ["tests/test_timer.py"],
    "routes/tools.py": ["tests/test_tools.py"],
    # Models
    "models/billing.py": ["tests/test_billing_engine.py", "tests/test_billing_unit.py"],
    "models/bonus.py": ["tests/test_bonus_dashboard.py"],
    "models/patient.py": ["tests/test_patient_chart.py", "tests/test_clinical_summary.py"],
    "models/caregap.py": ["tests/test_caregap_engine.py"],
    "models/monitoring.py": ["tests/test_monitoring_rules.py", "tests/test_monitoring_calendar.py"],
    # Billing engine
    "billing_engine/engine.py": ["tests/test_billing_engine.py"],
    "billing_engine/base.py": ["tests/test_billing_engine.py", "tests/test_billing_unit.py"],
    "billing_engine/scoring.py": ["tests/test_billing_unit.py"],
    "billing_engine/payer_routing.py": ["tests/test_billing_engine.py", "tests/test_billing_unit.py"],
    "billing_engine/rules.py": ["tests/test_billing_rules.py"],
    # Agent
    "agent/clinical_summary_parser.py": ["tests/test_clinical_summary.py"],
    "agent/caregap_engine.py": ["tests/test_caregap_engine.py"],
    "agent/mrn_reader.py": ["tests/test_mrn_reader.py"],
    "agent/note_reformatter.py": ["tests/test_note_reformatter.py"],
    # Services
    "app/services/bonus_calculator.py": ["tests/test_bonus_dashboard.py"],
    "app/services/calculator_engine.py": ["tests/test_calculators.py"],
    "app/services/billing_rules.py": ["tests/test_billing_rules.py"],
    # Global (changes trigger full suite)
    "app/__init__.py": ["tests/"],
    "config.py": ["tests/"],
    "models/__init__.py": ["tests/"],
}

# Detector files all map to billing engine tests
DETECTOR_PREFIX = "billing_engine/detectors/"


def get_changed_files_git(ref=None):
    """Get changed files from git diff. Returns list of relative paths."""
    cmd = ["git", "diff", "--name-only"]
    if ref:
        cmd.append(ref)
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=ROOT, timeout=30,
        )
        if result.returncode != 0:
            print(f"[ERROR] git diff failed: {result.stderr.strip()}", file=sys.stderr)
            return None
        files = [f.strip() for f in result.stdout.strip().splitlines() if f.strip()]
        # Also include staged changes
        staged = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True, text=True, cwd=ROOT, timeout=30,
        )
        if staged.returncode == 0:
            files.extend(f.strip() for f in staged.stdout.strip().splitlines() if f.strip())
        return list(set(files))
    except FileNotFoundError:
        print("[ERROR] git not found on PATH.", file=sys.stderr)
        return None
    except subprocess.TimeoutExpired:
        print("[ERROR] git diff timed out.", file=sys.stderr)
        return None


def resolve_tests(changed_files):
    """Map changed source files to test targets. Returns deduplicated set."""
    tests = set()
    full_suite = False

    for filepath in changed_files:
        # Normalize path separators
        filepath = filepath.replace("\\", "/")

        # Direct match in mapping
        if filepath in FILE_TO_BLOCKS:
            targets = FILE_TO_BLOCKS[filepath]
            for t in targets:
                if t == "tests/":
                    full_suite = True
                else:
                    tests.add(t)
            continue

        # Billing detector files -> billing engine tests
        if filepath.startswith(DETECTOR_PREFIX):
            tests.add("tests/test_billing_engine.py")
            continue

        # Test files changed -> run themselves
        if filepath.startswith("tests/") and filepath.endswith(".py"):
            tests.add(filepath)
            continue

        # Template changes -> e2e tests if they exist
        if filepath.startswith("templates/"):
            e2e_path = os.path.join(ROOT, "tests", "e2e", "test_ui_flows.py")
            if os.path.exists(e2e_path):
                tests.add("tests/e2e/test_ui_flows.py")
            continue

        # Static files -> e2e only
        if filepath.startswith("static/"):
            e2e_path = os.path.join(ROOT, "tests", "e2e", "test_ui_flows.py")
            if os.path.exists(e2e_path):
                tests.add("tests/e2e/test_ui_flows.py")
            continue

        # Migration files -> db integrity check
        if filepath.startswith("migrations/"):
            tests.add("scripts/db_integrity_check.py")
            continue

    return tests, full_suite


def main():
    parser = argparse.ArgumentParser(description="Detect changed files and suggest tests")
    parser.add_argument("--ref", help="Git ref to diff against (default: working tree)")
    parser.add_argument("--stdin", action="store_true", help="Read file list from stdin")
    args = parser.parse_args()

    # Get changed files
    if args.stdin:
        changed = [line.strip() for line in sys.stdin if line.strip()]
    else:
        changed = get_changed_files_git(args.ref)
        if changed is None:
            sys.exit(2)

    if not changed:
        print("[INFO] No changed files detected.")
        sys.exit(1)

    print(f"[INFO] {len(changed)} changed file(s):")
    for f in sorted(changed):
        print(f"  - {f}")

    # Resolve to tests
    tests, full_suite = resolve_tests(changed)

    print()
    if full_suite:
        print("[RESULT] Global file changed -- run FULL test suite:")
        print("  venv\\Scripts\\python.exe -m pytest tests/ -v")
    elif tests:
        print(f"[RESULT] Run these {len(tests)} test target(s):")
        for t in sorted(tests):
            print(f"  - {t}")
        # Print the pytest command
        targets = " ".join(sorted(tests))
        print(f"\n  venv\\Scripts\\python.exe -m pytest {targets} -v")
    else:
        print("[RESULT] No mapped tests for the changed files.")
        print("  Consider running smoke_test.py as a sanity check:")
        print("  venv\\Scripts\\python.exe scripts/smoke_test.py")

    sys.exit(0)


if __name__ == "__main__":
    main()
