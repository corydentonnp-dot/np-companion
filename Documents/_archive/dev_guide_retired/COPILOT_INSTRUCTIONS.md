# CareCompanion â€” Copilot Instructions

## Identity

Locally-hosted Flask clinical workflow app for a family NP. Automates tasks in **Amazing Charts** (desktop EHR) and **NetPractice** (web scheduler). Runs on Windows 11 Pro. Developer is a non-programmer â€” all code must be clearly commented, simple, and explicit.

---

## Workflow Rules

1. **Before ANY work:** Read ALL files in `Documents/dev_guide/`.
2. **Plan first:** Draft plan â†’ write to `RUNNING_PLAN.md` â†’ wait for approval.
3. **One step at a time:** Complete â†’ confirm â†’ update `RUNNING_PLAN.md` â†’ next.
4. **After every prompt:** Update `CHANGELOG.md` (new `## CL#` at top) AND both tracking tables in `Documents/dev_guide/CARECOMPANION_DEVELOPMENT_GUIDE.md`.

---

## HIPAA â€” Hard Rules (Override Everything)

- **No PHI in notifications.** Pushover gets counts only. Never names, MRNs, DOBs, diagnoses.
- **No PHI in logs.** Use `hashlib.sha256(mrn.encode()).hexdigest()[:12]` for logging.
- **No PHI leaves local network.** Outbound calls carry only clinical vocab (drug names, codes, age/sex).
- **MRN display:** `{{ mrn[-4:] }}` in all UI. Full MRN only in DB and audit log.
- **Soft-delete clinical records.** Use `is_archived`/`is_resolved` flags. Never `db.session.delete()`.
- **Audit every patient action** via `log_access()`.
- **Reformatter discards:** Log to `ReformatLog.discarded_items` JSON BEFORE removing from state.

---

## Tech Constraints

| Use | Never Use |
|-----|-----------|
| Python 3.11 | Python 3.12+ syntax |
| Flask + Jinja + SQLAlchemy + SQLite | Cloud DBs, cloud storage |
| Vanilla HTML/CSS/JS (ES6+) | React, Vue, Angular, npm, Tailwind, Bootstrap |
| `config.py` for settings | `python-dotenv`, env vars |
| `datetime.now(timezone.utc)` | `datetime.utcnow()` |
| `redirect(url_for('mod.index'))` | `redirect(request.referrer)` |
| `get_cached_or_fetch()` from `utils/api_client.py` | Raw `requests.get()` to external APIs |

---

## Flask Patterns

**App factory** in `app.py` â†’ `create_app()`. Blueprints in `routes/`.

```python
# Every route file:
module_bp = Blueprint('module', __name__)

@module_bp.route('/path')
@login_required
def index():
    items = Model.query.filter_by(user_id=current_user.id).all()  # ALWAYS scope to user
    return render_template('module.html', items=items)
```

- `@login_required` on ALL routes except `/login`, `/timer/room-widget`, `/oncall/handoff/<token>`.
- `@require_role('admin')` for `/admin/*`. `@require_role('provider')` for billing/metrics/oncall.
- JSON endpoints: `{"success": bool, "data": ..., "error": str|None}`.
- Shared data: `is_shared=True` readable by all, editable by author only.
- All timestamps: UTC via `datetime.now(timezone.utc)`.

**Error handling in routes:**
```python
except Exception as e:
    db.session.rollback()
    app.logger.error(f"Error in module.action: {str(e)}")
    return jsonify({"success": False, "error": "Operation failed"}), 500
```

---

## Agent Architecture

`agent.py` and `app.py` are **separate processes**. Communicate via SQLite + `data/active_user.json`. Agent exposes status on port 5001. Every agent job wrapped in try/except â€” exceptions logged, never crash the process.

**AC State Detection** (check before any automation):
```
not_running â†’ login_screen â†’ home_screen â†’ chart_open
```
Detect via `win32gui.EnumWindows()` + title bar regex: `LASTNAME, FIRSTNAME  (DOB: M/D/YYYY; ID: XXXXX)`

---

## Amazing Charts Automation

**Ground truth:** `Documents/ac_interface_reference/Amazing charts interface/..md files/ac_interface_reference_v4.md` â€” READ FIRST for any AC work.

### OCR-First Rule
```python
# CORRECT â€” OCR primary, coordinates fallback
find_and_click('Export Clinical Summary', fallback_xy=config.EXPORT_CLIN_SUM_MENU_XY)

# WRONG â€” hardcoded coordinates
pyautogui.click(*config.EXPORT_CLIN_SUM_MENU_XY)
```

### Automation Checklist
1. Verify AC is foreground window before any click.
2. Screenshot before executing any order set.
3. `time.sleep(0.5)` minimum between actions.
4. Stop immediately on failure â€” log what completed and what didn't.
5. Use keyboard shortcuts when possible (see `AC_SHORTCUTS` dict in codebase).
6. Handle "Resurrect Note" dialog before proceeding.

### Clinical Summary Export â€” Two Phases
- **Phase 1:** Open charts for ALL patients (search â†’ verify â†’ open â†’ template â†’ save).
- **Phase 2:** Export XML for ALL patients (home screen only, no charts open, always select "Full Patient Record").
- Never export while a chart window is open.

---

## OCR Rules

Use `agent/ocr_helpers.py` for all OCR. Always preprocess (grayscale â†’ 2x upscale â†’ contrast). Validate MRN: `re.match(r'^\d{6,10}$', text.strip())`. MRN capture targets AC title bar (top 60px of window rect).

---

## Frontend

- CSS custom properties in `:root` â€” use project palette (navy, teal, gold, etc.).
- Dark mode via `[data-theme="dark"]`.
- All templates extend `base.html`.
- Live updates via `fetch()` polling (10s intervals). No WebSockets.

---

## NetPractice / Playwright

- Load saved session before navigating. Check for Google redirect.
- Never automate Google login â€” set `needs_reauth=True` + Pushover alert instead.

---

## API Integration

- All calls through `utils/api_client.py` â†’ `get_cached_or_fetch()`.
- Cache tables: `lookup_key`, `response` (JSON text), `fetched_at`, `expires_at`.
- Offline: stale cache â†’ hardcoded fallback â†’ "not available". Never block page loads.
- Outbound data: only drug names, RXCUI, ICD-10, LOINC, CPT codes, age/sex. Never patient identifiers.

---

## Multi-User

Roles: `provider` (full), `ma` (dashboard/orders/caregap/medref), `admin` (everything + `/admin/*`). Agent reads `data/active_user.json` for current provider attribution.

---

## Notifications

All through `agent/notifier.py`. Priorities: `-1` quiet, `0` normal, `1` high (bypasses quiet hours), `2` emergency (requires ack).

---

## Testing

`AC_MOCK_MODE = True` in config.py runs agent against screenshots instead of live AC. Test patient: MRN 62815, TEST TEST, DOB 10/1/1980, 45F. Run: `venv\Scripts\python.exe tests/test_agent_mock.py`.

---

## Never Commit

`config.py`, `data/`, `.env`, `*.pkl`, `*.log`, `venv/`

---

## Dev Admin (Change Before Deploy)

Username: `CORY` / Password: `ASDqwe123`