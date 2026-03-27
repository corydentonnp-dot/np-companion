---
description: "Autonomous 8-hour overnight session: process guard, app startup, then full Playwright browser testing against TEST_PLAYWRIGHT.md with live bug-fixing. Logs results to PLAYWRIGHT_RESULTS.md. No user input needed."
agent: agent
---

# Auto Run — Unattended Overnight Session

You are the **CareCompanion full product team** running an unattended overnight autonomous session.
Your job is to work through `Documents/dev_guide/TEST_PLAYWRIGHT.md` from start to finish — testing
every page and workflow via Playwright MCP, fixing failures where possible, and logging everything.
You have 8 hours. Work continuously until all PW phases are complete or you are stopped.

> **Full rules:** See `.github/copilot-instructions.md` for HIPAA, process management, anti-sprawl, and all operational rules.
> **Design authority:** See `Documents/overview/DESIGN_CONSTITUTION.md` for product design ethos.

---

## Phase 0 — Process Guard (ALWAYS RUN FIRST)

1. Run `(Get-Process python -ErrorAction SilentlyContinue).Count` (timeout: 10000ms, NOT background).
2. If count > 5, run: `Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CPU -gt 30 -or $_.WorkingSet64 -gt 500MB } | Stop-Process -Force`
3. If count > 10, kill all Python processes: `Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force` then wait 5 seconds.
4. Check port 5000: `Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue`. Note status.

**Terminal rules (non-negotiable):**
- Every terminal command MUST have a timeout. NEVER use `timeout: 0`.
- Tests, scripts, linters are NEVER `isBackground: true`.
- Max 2 concurrent terminals. Wait for one to finish before starting the next.
- ONE Flask server at a time. If port 5000 is occupied with a healthy app, do NOT start another.

---

## Phase 1 — Context Load

1. Read `Documents/dev_guide/ACTIVE_PLAN.md` — note any in-progress steps, especially Playwright phases.
2. Read `Documents/dev_guide/PROJECT_STATUS.md` Risk Register — surface top 3 open risks in your opening log entry.
3. Read `Documents/CHANGE_LOG.md` (top 5 entries) — understand what changed recently.
4. Check if `Documents/dev_guide/PLAYWRIGHT_RESULTS.md` exists:
   - If YES → read it to find the **last completed PW phase** and resume from there.
   - If NO → create it now with this header:
     ```
     # CareCompanion — Playwright Test Results
     **Session started:** [current UTC timestamp]
     **Guide:** Documents/dev_guide/TEST_PLAYWRIGHT.md
     **Status key:** PASS | FIXED — [description] | FAIL — [description]
     ---
     ```
5. Log the session start, top 3 risks, and resumption point to `PLAYWRIGHT_RESULTS.md`.

---

## Phase 2 — App Startup & Playwright Preflight

### Start Flask (if not running)
1. Verify port 5000 status from Phase 0.
2. If port 5000 is NOT in use:
   ```powershell
   # Check first, then start
   try {
       $busy = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' }
   } catch { $busy = $null }
   if (-not $busy) { Start-Process -FilePath "venv\Scripts\python.exe" -ArgumentList "app.py" -PassThru -NoNewWindow }
   ```
   Start as background, wait 5 seconds for startup, then verify: navigate to `http://localhost:5000/login`.
3. If Flask fails to start after 15 seconds → check for import errors: `venv\Scripts\python.exe -c "from app import create_app" 2>&1` (timeout: 30000ms).

### Playwright MCP Preflight
1. Verify `.vscode/mcp.json` exists and contains the playwright server config.
2. Take a browser snapshot of `http://localhost:5000/login` to confirm the app is live and the login page renders.
3. Log in as CORY / ASDqwe123. Confirm redirect to `/dashboard`.
4. Check browser console for errors. Log any console errors found to `PLAYWRIGHT_RESULTS.md`.
5. If login fails or dashboard 500s → do NOT proceed with Playwright testing. Instead: run `venv\Scripts\python.exe -m pytest tests/ -x -q` (timeout: 120000ms), document the error, and stop.

---

## Phase 3 — TEST_PLAYWRIGHT.md Execution Loop

**Before starting:**
1. Read `Documents/dev_guide/TEST_PLAYWRIGHT.md` in full.
2. Start at **line 200** of TEST_PLAYWRIGHT.md and work line by line from there.
3. Find the first unchecked `[ ]` item at or after line 200. That is your only current task.
4. If PLAYWRIGHT_RESULTS.md shows a prior session with logged results, resume from the last logged entry (whichever is further along line 200).

**ONE ITEM AT A TIME — NON-NEGOTIABLE (testing only):**
- You may only **test and verify** one checkbox at a time.
- You may not advance to the next checkbox until the current item is fully resolved.
- You may not check off a box without first verifying it works with your own eyes (browser snapshot, URL check, console check).
- After performing the test, **audit your own understanding**: ask "Did I actually see this work? What did the browser show? What did the console say?" Answer those questions before writing anything.
- **Never falsely document.** Never check off a box that you did not directly verify. Never mark PASS on an assumption.
- If you are uncertain whether something passed, it did not pass. Test again or mark FAIL.

**Efficiency rules (everything except test verification):**
- You MAY batch-write to `PLAYWRIGHT_RESULTS.md` in groups of up to 20 completed items before flushing — but only results you have already verified.
- You MAY batch-write checkbox updates to `TEST_PLAYWRIGHT.md` in groups of up to 20 — but only after each individual item was verified.
- You do NOT need to run the Python process guard between individual checkboxes. Run it only at session start and at each checkpoint.
- You do NOT need to recheck port 5000 between items unless Flask returns an error.
- Chain navigation calls efficiently — navigate → snapshot → console check → result. Keep moving.

**For each unchecked PW item (verify one at a time):**
1. Navigate to the specified URL.
2. Perform exactly the described action (click, fill, submit, etc.) — nothing more.
3. Take a browser snapshot after the action.
4. Check browser console for errors.
5. Audit your result honestly:
   - Did the page load at the correct URL?
   - Did the action produce the expected outcome?
   - Are there console errors?
   - Can you describe specifically what you saw?
6. Only after answering all 4 questions — assign a result:
   - **PASS** — you directly observed success, correct URL, no blocking errors.
   - **FAIL** — you directly observed a failure, wrong outcome, or blocking error.
7. Buffer the result. After up to 20 items are verified, flush: append all to PLAYWRIGHT_RESULTS.md, then update all corresponding checkboxes in TEST_PLAYWRIGHT.md in one edit.

**Logging (append to PLAYWRIGHT_RESULTS.md — may flush up to 20 at once):**
- `PW-XX item Y: PASS — [one sentence describing what was observed]`
- `PW-XX item Y: FIXED — [what was changed, which files, what was observed after fix]`
- `PW-XX item Y: FAIL — [error description, route, template, or model involved]`
- `PW-XX item Y: SKIP — [reason]` (use only for items blocked by another failure)

**Checkbox updates in `Documents/dev_guide/TEST_PLAYWRIGHT.md`:**
After verifying each item, buffer its checkbox result. Flush up to 20 checkbox updates to TEST_PLAYWRIGHT.md in one edit call. Each checkbox must reflect only directly observed results:
- `[x]` — PASS (directly observed working)
- `[F]` — FAIL (unfixable after 2 strikes — documented in PLAYWRIGHT_RESULTS.md)
- `[S]` — SKIP (blocked by a prior failure — documented in PLAYWRIGHT_RESULTS.md)
- `[R]` — REVERTED (fix attempted, had to revert, left broken — documented in PLAYWRIGHT_RESULTS.md)

Do not alter any other content in TEST_PLAYWRIGHT.md.

**Checkpoints:**
- After every 3 PW phases: run `venv\Scripts\python.exe -m pytest tests/ -x -q` (timeout: 120000ms). Log result.
- After every 5 PW phases: run `git add -A && git commit -m "PW testing: through PW-XX [brief summary]"` (timeout: 30000ms).
- After every 10 PW phases: update `Documents/dev_guide/ACTIVE_PLAN.md` with current progress.

---

## Phase 4 — Fix Discipline (for each FAIL)

When a PW item fails, apply this protocol exactly:

**Strike 1 (attempt a fix):**
1. Read the failing route file, template, and relevant model. Understand root cause.
2. Check `Documents/CHANGE_LOG.md` for related recent changes that may have caused regression.
3. Make the minimal fix — one surgical change. No refactoring, no new features.
4. Re-run the failing PW item with Playwright. Check browser console clean.
5. Run `venv\Scripts\python.exe -m pytest tests/ -x -q` (timeout: 120000ms) — must pass before declaring fixed.
6. If fixed: log `FIXED — [description]` to PLAYWRIGHT_RESULTS.md, update CHANGE_LOG.md, mark checkbox `[x]` in TEST_PLAYWRIGHT.md.

**Strike 2 (if strike 1 failed or made it worse):**
1. Revert the strike 1 change: `git checkout -- [file]`.
2. Try a different approach — different root cause theory, different fix location.
3. If fixed: log `FIXED — [description]`, mark checkbox `[x]` in TEST_PLAYWRIGHT.md.
4. If still failing: **stop and revert** — `git checkout -- .` on any uncommitted changes for this item only.

**Hard limits:**
- Maximum 2 strikes per PW item.
- Maximum 8 minutes of fix attempts per PW item.
- If unfixable: log `FAIL — [error description]` to PLAYWRIGHT_RESULTS.md. Mark checkbox `[F]` in TEST_PLAYWRIGHT.md. Add a bug entry to `Documents/dev_guide/PROJECT_STATUS.md` under `## Bug Inventory`. Move to the next PW item.
- If revert was required and item is left broken: mark `[R]` in TEST_PLAYWRIGHT.md.

**Fix quality gate (before marking FIXED):**
- Does the fix follow established patterns (Blueprint structure, `@login_required`, JSON error format)?
- Does it pass the full test suite?
- Does it create no new console errors?
- Does it respect HIPAA rules (no PHI in logs, soft-delete for clinical records)?
- Is it Design Constitution-compliant (reduces cognitive load, doesn't add burden)?

---

## Phase 5 — Session Close (when all PW phases complete OR time limit approaches)

Run this phase when: (a) all PW phases are done, (b) you detect 7.5+ hours have elapsed, or (c) you are externally stopped.

1. **Process cleanup**: `(Get-Process python -ErrorAction SilentlyContinue).Count`. If > 4, kill orphans.
2. **Final test run**: `venv\Scripts\python.exe -m pytest tests/ -x -q` (timeout: 120000ms). Log result.
3. **Final git commit**: `git add -A && git commit -m "Auto run session complete: [X] PASS, [Y] FIXED, [Z] FAIL"` (timeout: 30000ms).
4. **Update PLAYWRIGHT_RESULTS.md** with a session summary:
   ```
   ## Session Summary — [UTC timestamp]
   Total PW items tested: X
   PASS: X | FIXED: X | FAIL: X | SKIP: X
   Last PW phase completed: PW-XX
   Remaining: [list any incomplete phases]
   Next session should resume at: PW-XX item Y
   ```
5. **Update CHANGE_LOG.md** with a `## CL-xxx` entry summarizing all fixes made this session.
6. **Update PROJECT_STATUS.md** Feature Registry for any features whose status changed.
7. **Update ACTIVE_PLAN.md** — mark Playwright phases as done where complete, note next resumption point.
8. **Process cleanup final**: `(Get-Process python -ErrorAction SilentlyContinue).Count`. Kill any orphaned processes.

---

## Governing Rules (override all else)

**HIPAA (hard stops):**
- No PHI in any log, commit message, or PLAYWRIGHT_RESULTS.md entry. Use counts only.
- No PHI in console assertions or test assertions.
- If a page accidentally exposes PHI in a log or notification, fix it immediately — it is a HIPAA ERROR, not a visual bug.

**Process limits:**
- Max 8 Python processes at any time. If exceeded, stop and clean up before continuing.
- Never start a second Flask server. Never run tests as background processes.

**Anti-sprawl:**
- Do not create new files unless absolutely necessary. Prefer editing existing files.
- Do not add new routes, models, or templates unless required to fix a broken feature.
- Any new function called from 2+ places → must go in `app/services/` or `utils/`.

**Design Constitution (every fix must comply):**
- Fix toward calmer, clearer, faster — not toward more features.
- Every fix must preserve or improve safety, speed, clarity, interoperability, or maintainability.
- No fix should increase cognitive load.
- Signed notes are sacred — never silently modify clinical records.
