---
applyTo: "agent/**/*.py"
---

# Agent Boundary Rules

## Desktop-Only Zone
The `agent/` directory is the ONLY place where desktop automation packages may be imported:
- `pyautogui`, `win32gui`, `win32con`, `win32api`, `pytesseract`, `pyperclip`, `pystray`, `psutil`, `pywinauto`, `comtypes`
- These imports MUST NEVER appear in `routes/`, `models/`, `utils/`, `billing_engine/`, or `adapters/`.

## Error Handling
- Every agent job MUST be wrapped in try/except — exceptions are logged, never crash the process.
- Use `app.logger.error()` or agent-specific logging, never `print()`.
- No PHI in log messages — hash MRNs with `hashlib.sha256(mrn.encode()).hexdigest()[:12]`.

## Amazing Charts Automation
- **Preferred:** `smart_find_and_click('text', fallback_xy=config.COORDINATES)` from `agent/ac_interact.py` — tries UIA → OCR → coordinates.
- **Legacy (still valid):** `find_and_click('text', fallback_xy=config.COORDINATES)` from `agent/ocr_helpers.py` — OCR → coordinates.
- Never use hardcoded coordinates alone.
- Verify AC is the foreground window before ANY click (except Win32 message clicks which don't require foreground).
- Screenshot before executing any order set.
- `time.sleep(0.5)` minimum between actions.
- Stop immediately on failure — log what completed vs. what didn't.
- Handle "Resurrect Note" dialog before proceeding.
- Check AC state (`not_running → login_screen → home_screen → chart_open`) before automation.

## UIA + Win32 Interaction (3-tier)
- **Tier 1 (UIA):** `uia_helpers.py` finds controls by name/automation_id, `win32_actions.py` clicks via Win32 messages.
- **Tier 2 (OCR):** `ocr_helpers.py` finds elements by visible text, `pyautogui` clicks at screen coordinates.
- **Tier 3 (Legacy):** Fallback to hardcoded (x,y) coordinates from `config.py`.
- Use `ac_interact.py` `smart_find_and_click()` / `smart_type_text()` / `smart_navigate_menu()` for new automation.
- Run `uia_probe.py` against AC to discover which controls are UIA-accessible before writing automation.

## OCR
- Always preprocess: grayscale → 2x upscale → contrast.
- Validate MRN: `re.match(r'^\d{6,10}$', text.strip())`.
- MRN capture targets AC title bar (top 60px of window rect).
- Use `agent/ocr_helpers.py` for all OCR operations.

## Communication
- Agent (`agent_service.py`, port 5001) and Flask (`app.py`, port 5000) are separate processes.
- Communicate via SQLite + `data/active_user.json`.
- Never import Flask app objects directly into agent code.

## SaaS Boundary
- Agent code will NOT exist in the SaaS version — it is desktop-only.
- All data the agent produces must flow through `adapters/` to be SaaS-portable.
- Never put business logic in agent code that should live in routes or utils.

## Process & Resource Management
- **Every `subprocess.run()` call MUST include `timeout=60`** (or an appropriate value). Never omit the timeout arg.
- **Every `subprocess.Popen()` call MUST be tracked** — store the `Popen` object and call `.wait(timeout=N)` or `.terminate()` when done.
- **Never use `os.system()` or `os.popen()`** — use `subprocess.run()` with timeout instead.
- **APScheduler jobs MUST use `max_instances=1` and `coalesce=True`** to prevent overlapping runs.
- **Every agent job wrapped in `safe_job()` MUST catch and log exceptions** — never let a failed job spawn retries that pile up.
- **Thread cleanup:** All daemon threads must be joined or cleaned up on agent shutdown via `AgentService.stop()`.
- **If a subprocess hangs past its timeout, `.kill()` it** — never leave zombie processes running.
- **Log process creation/destruction:** When spawning any subprocess, log the PID so it can be cleaned up on crash recovery.
