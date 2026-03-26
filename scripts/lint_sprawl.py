"""
lint_sprawl.py — CareCompanion Anti-Sprawl Linter
Checks for code architecture violations per the Anti-Sprawl Guardrails.

Exit codes:
  0 = no ERRORs found (warnings may still be present)
  1 = one or more ERRORs found

Run: venv\Scripts\python.exe scripts/lint_sprawl.py
"""
import os
import re
import sys

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROUTES_DIR = os.path.join(PROJECT_ROOT, "routes")
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "templates")

# Route files larger than this → WARN
MAX_ROUTE_LINES = 800

# Clinical models that must never be hard-deleted
CLINICAL_MODELS = [
    "Patient",
    "Encounter",
    "Note",
    "Order",
    "Medication",
]

# Routes explicitly exempted from @login_required
LOGIN_EXEMPT_ROUTES = [
    "login",
    "register",
    "room-widget",
    "room_widget",
    "face/room-toggle",
    "face_room_toggle",
    "handoff",
    "oncall/handoff",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def route_files():
    """Yield (path, filename) for all .py files in routes/."""
    for fname in os.listdir(ROUTES_DIR):
        if fname.endswith(".py") and not fname.startswith("__"):
            yield os.path.join(ROUTES_DIR, fname), fname


def template_files():
    """Yield (path, filename) for all .html files under templates/."""
    for dirpath, _dirs, files in os.walk(TEMPLATES_DIR):
        for fname in files:
            if fname.endswith(".html"):
                yield os.path.join(dirpath, fname), fname


def read_file(path):
    """Read file, return list of lines (1-indexed-safe, i.e. lines[0] = first line)."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.readlines()
    except OSError as exc:
        print(f"  [SKIP] Cannot read {path}: {exc}")
        return []


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_route_file_size(errors, warnings):
    """WARN if any route file exceeds MAX_ROUTE_LINES."""
    for path, fname in route_files():
        lines = read_file(path)
        if len(lines) > MAX_ROUTE_LINES:
            warnings.append(
                f"WARN  routes/{fname}: {len(lines)} lines "
                f"(max {MAX_ROUTE_LINES}) — split this file"
            )


def check_cross_route_imports(errors, warnings):
    """ERROR if any routes/ file imports from another routes/ module."""
    # Pattern: from routes.something import OR from routes import something
    cross_import_re = re.compile(
        r"^\s*from\s+routes\.\w+\s+import|^\s*import\s+routes\.\w+",
        re.MULTILINE,
    )
    for path, fname in route_files():
        lines = read_file(path)
        for lineno, line in enumerate(lines, 1):
            if cross_import_re.match(line):
                # Skip commented lines
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                errors.append(
                    f"ERROR routes/{fname}:{lineno}: cross-route import: {stripped}"
                )


def check_agent_pyautogui_imports(errors, warnings):
    """ERROR if any routes/ file imports from agent.pyautogui* or pyautogui_runner.

    Exceptions:
    - Lines with '# lint-ok: pyautogui' suppression comment are skipped.
    - 'import pyautogui' inside a try/except ImportError block is a WARN, not ERROR,
      since graceful fallback is already handled at that call site.
    """
    agent_import_re = re.compile(
        r"^\s*from\s+agent\.pyautogui|^\s*import\s+agent\.pyautogui"
        r"|^\s*from\s+agent\s+import\s+.*pyautogui",
        re.MULTILINE,
    )
    pyautogui_direct_re = re.compile(
        r"^\s*import\s+pyautogui|^\s*from\s+pyautogui\s+import",
        re.MULTILINE,
    )
    for path, fname in route_files():
        lines = read_file(path)
        for lineno, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Support lint-ok suppression comment
            if "# lint-ok" in line:
                continue
            if agent_import_re.match(line):
                errors.append(
                    f"ERROR routes/{fname}:{lineno}: agent/pyautogui import in route "
                    f"(use async DB queue — pending B5): {stripped}"
                )
            elif pyautogui_direct_re.match(line):
                # Check if we're inside a try block (look back for 'try:')
                start = max(0, lineno - 6)
                ctx = "".join(lines[start : lineno - 1])
                if re.search(r"\btry\s*:", ctx):
                    warnings.append(
                        f"WARN  routes/{fname}:{lineno}: pyautogui import inside try block "
                        f"(ImportError handled, but desktop code in routes — pending B5): {stripped}"
                    )
                else:
                    errors.append(
                        f"ERROR routes/{fname}:{lineno}: pyautogui import in route "
                        f"(use async DB queue — pending B5): {stripped}"
                    )


def check_clinical_hard_deletes(errors, warnings):
    """ERROR if db.session.delete() is called on a CLINICAL model instance.

    Clinical models: Patient, Encounter, Note, Order, Medication.
    Non-clinical objects (bookmarks, order templates, timer entries, etc.) are allowed.

    Detection: look for the variable's assignment from a clinical model query
    within the preceding 40 lines of the same function.
    """
    # These are the CLINICAL model class names that must not be hard-deleted
    clinical_model_names = {
        "Patient", "Encounter", "Note", "Order", "Medication",
        "ClinicalNote", "NoteTemplate",
    }
    # Build a pattern to match clinical model queries (e.g. "Patient.query." or "Patient.get(")
    clinical_query_re = re.compile(
        r"\b(" + "|".join(clinical_model_names) + r")\b.*?(?:\.query\.|db\.session\.get)"
    )
    delete_re = re.compile(r"db\.session\.delete\s*\(\s*(\w+)\s*\)")

    for path, fname in route_files():
        lines = read_file(path)
        for lineno, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Check for lint-ok suppression comment
            if "# lint-ok" in line:
                continue
            m = delete_re.search(line)
            if not m:
                continue
            var_name = m.group(1)
            # Look back up to 40 lines for this variable being assigned from a clinical model
            start = max(0, lineno - 41)
            surrounding = lines[start : lineno - 1]
            assignment_context = "".join(surrounding)
            # Check if the variable appears in a clinical model query in the surrounding scope
            if clinical_query_re.search(assignment_context):
                # Extra check: does the variable name appear in that context?
                var_assignment_re = re.compile(
                    rf"\b{re.escape(var_name)}\s*=.*(?:" +
                    "|".join(clinical_model_names) + r")"
                )
                if var_assignment_re.search(assignment_context):
                    errors.append(
                        f"ERROR routes/{fname}:{lineno}: db.session.delete({var_name}) on "
                        f"clinical model — use soft-delete (is_archived/is_resolved): {stripped}"
                    )


def check_missing_login_required(errors, warnings):
    """WARN if a @app.route or blueprint @*.route decorator is not preceded by @login_required."""
    route_decorator_re = re.compile(r"^\s*@\w+\.route\s*\(")
    login_required_re = re.compile(r"@login_required")
    exempt_re = re.compile(
        r"(?:login|register|room[_-]widget|handoff|face[_/]room[_-]toggle|oncall/handoff)",
        re.IGNORECASE,
    )

    for path, fname in route_files():
        lines = read_file(path)
        i = 0
        while i < len(lines):
            line = lines[i]
            if route_decorator_re.match(line):
                # Check if this route URL contains an exemption
                if exempt_re.search(line):
                    i += 1
                    continue
                # Look backward up to 10 lines for @login_required in the decorator block
                start = max(0, i - 10)
                surrounding = "".join(lines[start : i + 1])
                if not login_required_re.search(surrounding):
                    # Look forward until def line to get function name
                    func_name = ""
                    for j in range(i + 1, min(i + 8, len(lines))):
                        def_match = re.search(r"def\s+(\w+)", lines[j])
                        if def_match:
                            func_name = def_match.group(1)
                            break
                    warnings.append(
                        f"WARN  routes/{fname}:{i+1}: route '{func_name}' "
                        f"may be missing @login_required"
                    )
            i += 1


def check_template_inline_scripts(errors, warnings):
    """WARN if any template has an inline <script> block > 50 lines."""
    script_open_re = re.compile(r"<script\b[^>]*>", re.IGNORECASE)
    script_close_re = re.compile(r"</script>", re.IGNORECASE)

    for path, fname in template_files():
        lines = read_file(path)
        in_script = False
        script_start = 0
        script_line_count = 0

        for lineno, line in enumerate(lines, 1):
            if not in_script and script_open_re.search(line):
                in_script = True
                script_start = lineno
                script_line_count = 1
            elif in_script:
                script_line_count += 1
                if script_close_re.search(line):
                    in_script = False
                    if script_line_count > 50:
                        # Get a relative template path for readability
                        rel = os.path.relpath(path, TEMPLATES_DIR)
                        warnings.append(
                            f"WARN  templates/{rel}:{script_start}: "
                            f"inline <script> block is {script_line_count} lines "
                            f"(max 50) — extract to static/js/"
                        )
                    script_line_count = 0
                    script_start = 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    errors = []
    warnings = []

    print("=" * 60)
    print("CareCompanion Anti-Sprawl Linter")
    print("=" * 60)

    print("\n[1] Route file size check (max 800 lines)...")
    check_route_file_size(errors, warnings)

    print("[2] Cross-route import check (from routes.X in routes/)...")
    check_cross_route_imports(errors, warnings)

    print("[3] Agent/pyautogui import check in routes/...")
    check_agent_pyautogui_imports(errors, warnings)

    print("[4] Hard-delete check on clinical models...")
    check_clinical_hard_deletes(errors, warnings)

    print("[5] Missing @login_required check...")
    check_missing_login_required(errors, warnings)

    print("[6] Inline <script> block size check in templates...")
    check_template_inline_scripts(errors, warnings)

    print()
    print("-" * 60)
    if errors:
        print(f"ERRORS ({len(errors)}):")
        for msg in errors:
            print(f"  {msg}")
    else:
        print("ERRORS (0): None found.")

    print()
    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for msg in warnings:
            print(f"  {msg}")
    else:
        print("WARNINGS (0): None found.")

    print("-" * 60)
    error_count = len(errors)
    warn_count = len(warnings)
    print(f"\nResult: {error_count} error(s), {warn_count} warning(s)")

    if errors:
        print("FAILED — fix ERROR-level findings before continuing.")
        sys.exit(1)
    else:
        print("PASSED — no ERROR-level violations found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
