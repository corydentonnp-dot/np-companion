---
applyTo: "agent/**/*.py"
---

# Agent Boundary Rules

## Desktop-Only Zone
The `agent/` directory is the ONLY place where desktop automation packages may be imported:
- `pyautogui`, `win32gui`, `win32con`, `pytesseract`, `pyperclip`, `pystray`, `psutil`
- These imports MUST NEVER appear in `routes/`, `models/`, `utils/`, `billing_engine/`, or `adapters/`.

## Error Handling
- Every agent job MUST be wrapped in try/except — exceptions are logged, never crash the process.
- Use `app.logger.error()` or agent-specific logging, never `print()`.
- No PHI in log messages — hash MRNs with `hashlib.sha256(mrn.encode()).hexdigest()[:12]`.

## Amazing Charts Automation
- OCR-first: `find_and_click('text', fallback_xy=config.COORDINATES)` — never hardcoded coordinates alone.
- Verify AC is the foreground window before ANY click.
- Screenshot before executing any order set.
- `time.sleep(0.5)` minimum between actions.
- Stop immediately on failure — log what completed vs. what didn't.
- Handle "Resurrect Note" dialog before proceeding.
- Check AC state (`not_running → login_screen → home_screen → chart_open`) before automation.

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
