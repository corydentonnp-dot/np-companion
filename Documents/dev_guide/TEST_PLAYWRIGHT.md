# CareCompanion — Playwright MCP Browser Testing Guide

**Version:** 1.0 — 03-25-26  
**Purpose:** Step-by-step guide for setting up AI-driven browser testing via Playwright MCP, plus a 16-phase audit plan covering all pages in CareCompanion.

---

## PART 1 — Fresh Machine Setup

### What is This?

VS Code Copilot Agent can directly control a real browser (take screenshots, click, fill forms, check console errors) via the Playwright MCP server. This gives the AI eyes — it can see exactly what the app looks like, find visual bugs, and fix them without you describing them.

Requirements: Node.js (for Playwright), Python 3.11, Git, VS Code with GitHub Copilot.

---

### Step 1 — Install Prerequisites (in order)

**1. Python 3.11**
- Download: https://www.python.org/downloads/release/python-3110/
- Scroll to "Files" → download **Windows installer (64-bit)**
- ⚠️ On the FIRST installer screen: check **"Add Python to PATH"** before clicking Install

**2. Git**
- Download: https://git-scm.com/download/win
- Click the first link, run installer, click Next through everything

**3. Node.js (LTS)**
- Download: https://nodejs.org/en/download
- Download the **LTS version**, run installer, defaults are fine
- Playwright MCP server runs via Node — this is required

**4. VS Code**
- Download: https://code.visualstudio.com/
- Install with defaults

---

### Step 2 — Clone the Project

Open **PowerShell** (Start menu → search PowerShell). Run these one at a time:

```powershell
cd C:\Users\coryd\Documents
git clone https://github.com/corydentonnp-dot/np-companion.git NP_Companion
cd NP_Companion
```

```powershell
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

```powershell
# Run all migrations in order
Get-ChildItem migrations\*.py | Sort-Object Name | ForEach-Object {
    Write-Host "Running $($_.Name)..."
    venv\Scripts\python.exe $_.FullName
}
```

```powershell
code .
```

---

### Step 3 — VS Code Extension Setup

When VS Code opens, it may show: *"Do you want to install recommended extensions?"* → click **Install All**.

This installs:
- GitHub Copilot + Copilot Chat
- GitDoc (auto-sync on save)
- Python + Pylance

If the popup doesn't appear: press `Ctrl+Shift+X`, search each one manually.

**Sign into GitHub Copilot** when prompted (use the `corydentonnp-dot` GitHub account).

---

### Step 4 — Verify MCP Config Exists

The `.vscode/mcp.json` file is committed to the repo and should be present after cloning. Verify it exists:

```powershell
Get-Content .vscode\mcp.json
```

Expected output:
```json
{
  "servers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

If the file is missing, create it:

```powershell
New-Item -Path .vscode -ItemType Directory -Force
Set-Content .vscode\mcp.json '{
  "servers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}'
```

---

### Step 5 — Enable Agent Mode in Copilot Chat

1. Press `Ctrl+Shift+P` → type `Developer: Reload Window` → press Enter
2. Open Copilot Chat: `Ctrl+Alt+I`
3. Switch the dropdown from **Ask** to **Agent** mode
4. Click the **tools icon** (wrench) — you should see Playwright tools listed:
   - `browser_navigate`, `browser_screenshot`, `browser_click`, `browser_fill_form`, `browser_snapshot`, etc.

If tools don't appear after reload, restart VS Code completely.

---

### Step 6 — First Download (Auto)

The first time Copilot uses a Playwright browser tool, it automatically downloads `@playwright/mcp` and Chromium (~30 seconds total). After that it's instant (cached).

To trigger the first run:
1. Start Flask: `.\run.ps1`
2. In Copilot Chat (Agent mode), type: *"Navigate to localhost:5000 and take a screenshot"*
3. Wait ~30 seconds on first run — you'll see download progress in the terminal
4. A screenshot of the login page should appear in the chat

---

### Step 7 — Verify Everything Works

Run this checklist:

- [ ] `node -v` shows v18+ or v20+ or v22+ or v24+
- [ ] `python --version` shows 3.11.x
- [ ] `git --version` shows any version
- [ ] `.vscode/mcp.json` exists with playwright config
- [ ] VS Code Copilot Chat is in **Agent** mode
- [ ] Playwright tools appear in the tools list
- [ ] Flask starts with `.\run.ps1`
- [ ] First screenshot navigation succeeds

---

## PART 2 — Execution Protocol

### Before Starting Any Phase

1. Start Flask: `.\run.ps1` (check port 5000 isn't occupied first: `Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue`)
2. In Copilot Chat (Agent mode), say: *"Navigate to localhost:5000/login and take a screenshot"*
3. Log in as `CORY` / `ASDqwe123`
4. You are now ready to run audit phases

### Per-Page Workflow (for each URL in a phase)

1. **Navigate** to the URL
2. **Screenshot** — get a visual
3. **Check console** — look for JS errors, 404s, failed fetch calls
4. **Check layout** — alignment, overflow, truncation, empty states, loading states
5. **Check dark mode** — add `?theme=dark` or toggle via settings
6. **Fix** anything found — one fix at a time
7. **Re-navigate + screenshot** — confirm fix didn't break anything
8. **Log** fixes to `CHANGE_LOG.md`

### Session Protocol

- Run one phase per Copilot session unless phases are short (< 3 pages)
- After every 2–3 fixes, run `venv\Scripts\python.exe -m pytest tests/ -x -q` to catch regressions
- After completing a phase, mark it ✅ in this file

### After All Phases Complete

1. Run full test suite: `venv\Scripts\python.exe -m pytest tests/ -v`
2. Full dark mode pass of every page
3. Mobile viewport pass: set browser to 375×812 and re-run PW-16 checks
4. Log a `## CL-xxx` entry in `CHANGE_LOG.md` summarizing all Playwright audit fixes

---

## PART 3 — 16-Phase Audit Plan

---

### PW-1: Login & Account Flows

**URLs:**
- `/login`
- `/register`
- `/onboarding`
- `/settings`
- `/settings/account`
- `/settings/notifications`

**Check Items:**
- [ ] Login form renders with correct labels and placeholder text
- [ ] Password show/hide toggle works
- [ ] Sign In button shows loading state on submit
- [ ] Invalid credentials show error message (not a 500)
- [ ] Rate limiting activates after 5 failed attempts (lockout message appears)
- [ ] `next` redirect param is validated — external URLs are rejected
- [ ] Register page (if active) completes flow without errors
- [ ] Settings page loads all tabs: Profile, Account, Notifications, Appearance
- [ ] Notification settings save and persist on reload
- [ ] Account page shows correct role label
- [ ] No console errors on any of these pages
- [ ] Dark mode renders correctly on all pages

---

### PW-2: Dashboard

**URLs:**
- `/dashboard`

**Check Items:**
- [ ] Dashboard loads without console errors
- [ ] All widget sections render (Today's Schedule, Priority Patients, Agent Status, etc.)
- [ ] Schedule widget shows today's appointments or "no appointments" message
- [ ] Priority 1 patient alert badge shows/hides correctly
- [ ] Agent status indicator reflects actual agent state
- [ ] Setup banner (if incomplete) renders and links work
- [ ] Quick-action buttons navigate to correct pages
- [ ] All cards have proper padding — no content clipping
- [ ] Dark mode renders all widget backgrounds correctly
- [ ] Polling (every 10s) does not flood console with errors
- [ ] Page load time is acceptable (< 3 seconds)

---

### PW-3: Patient Roster & Chart

**URLs:**
- `/patients`
- `/patient/<mrn>` (use MRN 62815 — test patient)
- `/patient/<mrn>/detail`

**Check Items:**
- [ ] Patient list table renders with all columns visible
- [ ] Search/filter fields work and filter results live
- [ ] Sorting by name, DOB, last visit works
- [ ] Clicking a patient row navigates to patient chart
- [ ] Patient chart header shows: name, DOB, MRN, age, sex, portal status, cell
- [ ] Chart tabs all load: Summary, Orders, Labs, Billing, Notes, etc.
- [ ] Active medications list renders (or shows "none on file")
- [ ] Problem list renders
- [ ] Allergy list renders
- [ ] Add note / add order buttons are present and functional
- [ ] No PHI in browser console logs
- [ ] Dark mode on patient chart — all sections readable

---

### PW-4: Inbox

**URLs:**
- `/inbox`

**Check Items:**
- [ ] Inbox loads message list without errors
- [ ] Unread count badge matches visible unread items
- [ ] Clicking a message opens detail view
- [ ] Reply / Archive / Delete actions work (verify soft-delete — no db.session.delete)
- [ ] Filter by type (labs, refills, messages) narrows list correctly
- [ ] Empty inbox state shows helpful message (not a blank page)
- [ ] Pagination or infinite scroll works if list is long
- [ ] No console errors on load or on message open
- [ ] Dark mode inbox — unread items still visually distinct

---

### PW-5: Timer

**URLs:**
- `/timer`
- `/timer/room-widget`

**Check Items:**
- [ ] Timer page loads with all room slots visible
- [ ] Start/stop timer works correctly per room
- [ ] Timer persists across page refresh (or resets gracefully)
- [ ] Room names render correctly
- [ ] Room widget (unauthenticated view) loads without login redirect
- [ ] Room widget shows current room state
- [ ] Room-toggle endpoint works from widget
- [ ] No console errors on either page
- [ ] Dark mode on timer — room cards distinguishable

---

### PW-6: Billing Suite

**URLs:**
- `/billing`
- `/billing/review`
- `/billing/log`
- `/billing/monthly`
- `/billing/opportunity-report`
- `/billing/em-calculator`
- `/billing/benchmarks`
- `/billing/why-not`
- `/billing/monthly-revenue`

**Check Items:**
- [ ] Main billing page loads claim list or "no claims" state
- [ ] Billing review shows pending claims with patient details
- [ ] E/M calculator renders all fields and computes MDM correctly
- [ ] Billing log table shows historical entries with correct columns
- [ ] Monthly summary shows totals, breakdowns, and charts (no blank chart containers)
- [ ] Opportunity report generates without errors
- [ ] Benchmarks page shows comparison data or "insufficient data" state
- [ ] Why-Not page lists missed billing opportunities
- [ ] Revenue page shows monthly totals chart
- [ ] All dollar values formatted correctly ($X,XXX.XX)
- [ ] No console errors on any billing page
- [ ] Role check: non-provider role should be redirected or see limited view
- [ ] Dark mode on all billing pages — especially chart backgrounds

---

### PW-7: Care Gaps

**URLs:**
- `/caregap`
- `/caregap/panel`
- `/caregap/outreach`
- `/caregap/patient/<mrn>` (use 62815)

**Check Items:**
- [ ] Care gap overview loads with summary counts
- [ ] Panel view shows patient list with gap indicators
- [ ] Filters (by gap type, status, priority) work correctly
- [ ] Outreach tab shows scheduled/completed outreach
- [ ] Patient-level care gap detail shows all gaps for that patient
- [ ] "Mark resolved" action works and updates state (soft-resolve, not delete)
- [ ] Bulk actions (if present) work correctly
- [ ] Empty state handled correctly for each view
- [ ] No console errors
- [ ] Dark mode renderable

---

### PW-8: Orders & Order Sets

**URLs:**
- `/orders`
- `/orders/master`

**Check Items:**
- [ ] Orders page loads active orders list
- [ ] Order master list shows all available order templates
- [ ] Creating a new order from template works
- [ ] Order detail view shows all fields
- [ ] Status updates (pending → signed → complete) work
- [ ] Refill order flow functions end-to-end
- [ ] Search/filter in order master finds items
- [ ] No console errors
- [ ] Dark mode on order cards and tables

---

### PW-9: Lab Track

**URLs:**
- `/labtrack`
- `/labtrack/patient/<mrn>` (use 62815)

**Check Items:**
- [ ] Lab track overview shows pending/overdue labs
- [ ] Patient lab history shows in correct chronological order
- [ ] Lab result entry form works
- [ ] Critical value flagging displays visually
- [ ] Sort/filter by lab type, date, status works
- [ ] Patient-specific view shows only their labs
- [ ] Empty state ("no labs on file") renders cleanly
- [ ] No console errors
- [ ] Dark mode — critical flags still visually prominent

---

### PW-10: On-Call

**URLs:**
- `/oncall`
- `/oncall/new`
- `/oncall/view/<id>` (use first available ID)
- `/oncall/handoff/<token>` (use a test token)

**Check Items:**
- [ ] On-call list loads past/current calls
- [ ] New call form renders all required fields
- [ ] Creating a new on-call record works
- [ ] Viewing an existing record shows all fields
- [ ] Handoff page loads WITHOUT login (it's a public token page)
- [ ] Handoff page shows only safe information (no PHI beyond what's needed)
- [ ] Print/export handoff works
- [ ] No console errors
- [ ] Dark mode on all views

---

### PW-11: Clinical Tools

**URLs:**
- `/tools`
- `/tools/reformatter`
- `/pa`
- `/pa/library`
- `/dot-phrases`
- `/macros`
- `/rems`
- `/reportable-diseases`
- `/result-templates`
- `/medref`
- `/tickler`
- `/referral`
- `/coding`

**Check Items:**
- [ ] Tools hub page renders all tool cards with correct links
- [ ] Reformatter: paste zone works, output renders cleanly, discard log is written before removal
- [ ] PA tool: new PA request form works, library shows saved PAs
- [ ] Dot-phrases: list renders, search works, create/edit/delete work
- [ ] Macros: list renders, macro expansion works in text areas
- [ ] REMS: database loads, search by drug works
- [ ] Reportable diseases: list renders, search works
- [ ] Result templates: list renders, template preview works
- [ ] MedRef: drug lookup works, results display correctly
- [ ] Tickler: active ticklers list renders, add/resolve work
- [ ] Referral: form works, saved referrals list renders
- [ ] Coding: ICD-10 / CPT lookup works
- [ ] No console errors on any tool page
- [ ] Dark mode on all tool pages

---

### PW-12: Calculators

**URLs:**
- `/calculators`
- `/calculators/<key>` for each: (audit all 19)
  - `bmi`, `egfr`, `chads2`, `wells-dvt`, `wells-pe`, `heart-score`,
    `pediatric-dosing`, `steroid-taper`, `phenytoin`, `warfarin`,
    `qtc`, `map`, `ibw`, `corrected-calcium`, `sofa`, `curb65`,
    `alvarado`, `apgar`, `gcs`

**Check Items (for each calculator):**
- [ ] Calculator page renders all input fields with correct labels
- [ ] Sample inputs produce correct known output
- [ ] Invalid inputs show validation error (not a 500)
- [ ] Result section appears after calculation
- [ ] "Save result" (if present) persists to DB and appears in history
- [ ] Back to calculators list link works
- [ ] No console errors
- [ ] Dark mode renders calculator form correctly

---

### PW-13: Admin Panel

**URLs:**
- `/admin`
- `/admin/users`
- `/admin/user/<id>`
- `/admin/audit-log`
- `/admin/db-health`
- `/admin/feature-flags`
- `/admin/backup`
- `/admin/migrations`
- `/admin/reports`
- `/admin/settings`
- `/admin/api-cache`
- `/admin/notification-test`
- `/admin/reformat-log`
- `/admin/claim-rules`
- `/admin/system`

**Check Items:**
- [ ] Admin index loads with all sub-section links
- [ ] User list shows all users with roles
- [ ] User detail allows role change and password reset
- [ ] Audit log shows recent access events (no PHI in log entries)
- [ ] DB health check shows table row counts and any issues
- [ ] Feature flags page shows toggle state
- [ ] Backup triggers correctly (check for file creation)
- [ ] API cache shows cached entries and allows manual purge
- [ ] Notification test sends a test Pushover message
- [ ] Reformat log shows discarded items history
- [ ] Claim rules page shows billing rule list
- [ ] Non-admin user should be redirected away (403 or redirect)
- [ ] No console errors on any admin page
- [ ] Dark mode across all admin pages

---

### PW-14: Monitoring, Briefing & Messaging

**URLs:**
- `/monitoring-calendar`
- `/morning-briefing`
- `/commute-briefing`
- `/notifications`
- `/messages`
- `/messages/new`

**Check Items:**
- [ ] Monitoring calendar renders calendar grid correctly
- [ ] Morning briefing page loads with today's data sections
- [ ] Commute briefing loads and shows relevant patient/task summary
- [ ] Notifications page shows system notification history
- [ ] Messages list renders conversations
- [ ] New message form works — recipient search, subject, body
- [ ] Send action works and message appears in sent/list
- [ ] No PHI in notification payloads visible in console
- [ ] No console errors
- [ ] Dark mode on all pages

---

### PW-15: Metrics & Benchmarks

**URLs:**
- `/metrics`
- `/metrics/weekly`
- `/benchmarks`
- `/bonus`

**Check Items:**
- [ ] Metrics page loads with chart containers (not blank)
- [ ] Line/bar charts render actual data (not empty axes)
- [ ] Weekly metrics drill-down works
- [ ] Benchmarks page shows peer comparison data or "insufficient data" state
- [ ] Bonus tracker shows current progress toward targets
- [ ] Date range filters work and update charts
- [ ] Export (if present) generates a file
- [ ] Role check: MA role should not see these pages (redirected)
- [ ] No console errors
- [ ] Dark mode — chart colors visible on dark background

---

### PW-16: Cross-Cutting Checks

Run these checks AFTER completing PW-1 through PW-15.

**A. Dark Mode — Global Pass**
- [ ] Toggle dark mode from settings
- [ ] Navigate every major page — verify no white flash, no unreadable text, no invisible icons
- [ ] All card/table backgrounds switch properly
- [ ] All button states (hover, active, disabled) visible in dark

**B. Mobile Viewport (375×812)**
- [ ] Set browser viewport: 375px wide × 812px tall
- [ ] Navigate: dashboard, patient chart, billing, inbox, calculators
- [ ] No horizontal scroll on any page
- [ ] Navigation menu collapses to hamburger or equivalent
- [ ] Tables scroll horizontally (not overflow-hidden)
- [ ] Modals fit within viewport

**C. Auth Enforcement**
- [ ] Log out, then try to navigate directly to `/dashboard`, `/patients`, `/billing`, `/admin`
- [ ] All routes redirect to `/login` with a `next` param
- [ ] After login, redirect returns to the intended page
- [ ] Public routes still load without login: `/timer/room-widget`, `/oncall/handoff/<token>`

**D. Flash Messages**
- [ ] Trigger a success action (save settings, create record)
- [ ] Flash message appears and disappears after timeout (or on next page load)
- [ ] Error flash messages are visually distinct from success
- [ ] Flash messages visible in dark mode

**E. Console Cleanliness**
- [ ] Navigate all 6 critical pages: dashboard, patient chart, billing, inbox, admin, tools
- [ ] Zero `SyntaxError`, `TypeError`, or `Uncaught` errors
- [ ] Zero 404s for static assets (CSS, JS, icons, favicon)
- [ ] Zero failed fetch calls with HTML response parsed as JSON

**F. Favicon & Static Assets**
- [ ] Favicon appears in browser tab on every page
- [ ] All linked CSS files load (no 404)
- [ ] All linked JS files load (no 404)
- [ ] No mixed content warnings

**G. Sortable Tables**
- [ ] Patient list sort by name, DOB, last visit
- [ ] Billing log sort by date, amount, code
- [ ] Lab track sort by date, type, status
- [ ] Sort direction arrow toggles on repeat click

**H. API Polling (10s intervals)**
- [ ] Logged in: polling runs silently with no console errors
- [ ] Logged out (login page): polling is suppressed — no 302 → JSON parse errors
- [ ] Polling gracefully handles network errors (no crash, just silent retry)

---

## PART 4 — Phase Completion Tracker

Mark each phase ✅ as it is completed and verified.

| Phase | Focus Area | Status | Date Completed |
|-------|------------|--------|----------------|
| PW-1  | Login & Account Flows | ⬜ Not Started | — |
| PW-2  | Dashboard | ⬜ Not Started | — |
| PW-3  | Patient Roster & Chart | ⬜ Not Started | — |
| PW-4  | Inbox | ⬜ Not Started | — |
| PW-5  | Timer | ⬜ Not Started | — |
| PW-6  | Billing Suite | ⬜ Not Started | — |
| PW-7  | Care Gaps | ⬜ Not Started | — |
| PW-8  | Orders & Order Sets | ⬜ Not Started | — |
| PW-9  | Lab Track | ⬜ Not Started | — |
| PW-10 | On-Call | ⬜ Not Started | — |
| PW-11 | Clinical Tools | ⬜ Not Started | — |
| PW-12 | Calculators | ⬜ Not Started | — |
| PW-13 | Admin Panel | ⬜ Not Started | — |
| PW-14 | Monitoring & Messaging | ⬜ Not Started | — |
| PW-15 | Metrics & Benchmarks | ⬜ Not Started | — |
| PW-16 | Cross-Cutting Checks | ⬜ Not Started | — |

**Progress:** 0/16 phases complete

---

## PART 5 — Quick Reference

### Common Playwright Commands (Copilot Agent Mode)

| What you want | What to type in Copilot Chat |
|---------------|------------------------------|
| See a page | *"Navigate to localhost:5000/dashboard and screenshot"* |
| Check errors | *"Check the browser console for errors on this page"* |
| Test a form | *"Fill in the login form with CORY / ASDqwe123 and submit"* |
| Test dark mode | *"Click the dark mode toggle and screenshot"* |
| Test mobile | *"Resize browser to 375x812 and screenshot the dashboard"* |
| Fix and verify | *"Fix the console error, then navigate back and confirm it's gone"* |
| Full phase audit | *"Run PW-2: navigate to the dashboard, screenshot, check console, and report all issues"* |

### Key Test Credentials
- **Admin login:** `CORY` / `ASDqwe123`
- **Test patient MRN:** 62815 (TEST TEST, DOB 10/01/1980, 45F)
- **Flask port:** 5000
- **Agent port:** 5001

### File Paths for Fixes
- Routes: `routes/<blueprint>.py`
- Templates: `templates/<blueprint>/`
- Shared JS: `static/js/main.js`
- Global CSS: `static/css/main.css`
- Base template: `templates/base.html`

### After Every Fix
1. Syntax check: `venv\Scripts\python.exe -c "import py_compile; py_compile.compile('routes/<file>.py', doraise=True); print('OK')"`
2. Re-navigate and screenshot
3. Check console is clean
4. Log to `Documents/CHANGE_LOG.md`
