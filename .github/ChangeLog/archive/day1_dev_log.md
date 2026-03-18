# NP Companion — Day 1 Development Log
**Date:** March 15–16, 2026  
**Phases Covered:** Phase 1 (Foundation) + Phase 2 (Data Layer — partial)

---

## Summary of All Features Built on Day 1

### Phase 1 — Foundation

| Feature ID | Feature | Status |
|:---:|---|---|
| F1 | Project Skeleton (app.py, base.html, main.css, main.js) | ✅ Built |
| F1a | Multi-User Accounts (User model, login, register, roles) | ✅ Built |
| F1b | Role-Based Access (@require_role, sidebar filtering, /admin/users) | ✅ Built |
| F1c | Dark Mode / Light Mode (toggle, localStorage + server persist) | ✅ Built |
| F1d | Notification Preferences (/settings/notifications) | ✅ Built |
| F1e | Session Timeout & Auto-Lock (PIN overlay, /api/verify-pin) | ✅ Built |
| F1f | Audit Trail (/admin/audit-log, after_request hook) | ✅ Built |
| F2 | Database Schema (15+ tables, all model files) | ✅ Built |
| F3 | Background Agent (agent.py, heartbeat loop, crash recovery) | ✅ Built |
| F3a | Agent Health Monitor (green/yellow/red dot, /api/agent-status) | ✅ Built |
| F3b | Per-Provider Agent Profiles (active_user.json tracking) | ✅ Built |
| F3c | Crash Recovery & Resume (incomplete session detection) | ✅ Built |

### Phase 2 — Data Layer (partial)

| Feature ID | Feature | Status |
|:---:|---|---|
| F4 | NetPractice Schedule Scraper (Playwright, CGM webPRACTICE) | ✅ Built |
| F4a | New Patient Flag (gold NEW badge in Today View) | ✅ Built |
| F4b | Visit Duration Estimator (pace calculation, likely end time) | ✅ Built |
| F4c | Double-Booking & Gap Detector (anomaly warnings) | ✅ Built |
| F4e | Re-Auth Watchdog (banner + Pushover flag) | ✅ Built |

### Additional Features (not in original dev guide but requested during build)

| Feature | Status |
|---|---|
| Admin Dashboard Hub (/admin with 6 tool cards) | ✅ Built |
| Admin Sitemap (/admin/sitemap — lists all routes) | ✅ Built |
| Setup Wizard (/setup — role-based onboarding) | ✅ Built |
| Setup Button in header (gold gear icon with count badge) | ✅ Built |
| Amazing Charts Credential Storage (Fernet-encrypted) | ✅ Built |
| Work PC Password Storage (Fernet-encrypted, optional) | ✅ Built |
| Dashboard Date Navigation (Yesterday/Today/Tomorrow) | ✅ Built |
| NetPractice Admin Settings (/admin/netpractice) | ✅ Built |
| NetPractice Setup Wizard (/admin/netpractice/wizard) | ⚠️ Needs Redesign — see Day 2 notes |

---

## Baby Steps: How to Test Everything

### STEP 1: Start the App

1. Open VS Code
2. Press Ctrl+` (backtick) to open the terminal
3. Type these commands one at a time, pressing Enter after each:
```powershell
cd C:\Users\coryd\Documents\NP_Companion
venv\Scripts\activate
python app.py
```
4. You should see something like: `* Running on http://0.0.0.0:5000`
5. Open Chrome and go to: **http://localhost:5000**

---

### STEP 2: Login Page (F1, F1a)

- [ ] You see the NP Companion login page
- [ ] Type your username (CORY) and password, then click "Log In"
- [ ] You are taken to the Dashboard page
- [ ] Your name appears in the top-right corner of the header

---

### STEP 3: Sidebar Navigation (F1, F1b)

- [ ] The left sidebar shows these modules: Dashboard, Timer, Inbox, On-Call, Orders, Med Ref, Lab Track, Care Gaps, Metrics, Tools
- [ ] At the bottom there's an "Admin" section (only if you're logged in as admin)
- [ ] Clicking Settings (gear icon at bottom) goes to /settings/account
- [ ] Clicking Log Out logs you out and returns to the login page

---

### STEP 4: Role-Based Access (F1b)

1. Log out
2. Click "Register" and create a new account with a different username (e.g., "TestMA")
3. Log in as CORY (admin)
4. Go to Admin → User Management
5. Find the TestMA user and change their role to "ma"
6. Log out and log in as TestMA
- [ ] TestMA can see: Dashboard, Orders, Med Ref, Care Gaps
- [ ] TestMA CANNOT see: Timer, Inbox, On-Call, Lab Track, Metrics, Tools, Admin

---

### STEP 5: Dark Mode (F1c)

- [ ] Click the moon/sun icon in the top-right header
- [ ] The entire app switches to dark mode (dark backgrounds, light text)
- [ ] Refresh the page (F5) — dark mode is still active (persists)
- [ ] Click the icon again — switches back to light mode

---

### STEP 6: Account Settings (F1a)

- [ ] Go to Settings → Account (/settings/account)
- [ ] You can change your display name
- [ ] You can change your password
- [ ] You can set a 4-digit PIN
- [ ] You see cards for Amazing Charts Credentials and Work PC Password

---

### STEP 7: Notification Preferences (F1d)

- [ ] Go to Settings → Notifications (/settings/notifications)
- [ ] You see toggles for: Pushover enabled, weekend alerts
- [ ] You see dropdowns for: inbox check interval
- [ ] You see time pickers for: quiet hours start/end
- [ ] You see checkboxes for notification types (labs, radiology, messages, etc.)
- [ ] Save your changes — they persist after refresh

---

### STEP 8: Auto-Lock (F1e)

- [ ] Wait 5 minutes without touching your mouse or keyboard (or temporarily set lock timeout to 1 minute in preferences)
- [ ] A full-screen overlay appears with a PIN entry box
- [ ] Enter the correct 4-digit PIN — the overlay disappears
- [ ] Enter 3 wrong PINs — you are required to fully log in again

---

### STEP 9: Admin Dashboard

- [ ] Click "Admin" in the sidebar
- [ ] You see a hub page with 6 cards: Users, Audit Log, NetPractice, Agent, Site Map, Restart Server
- [ ] Click "User Management" — see all registered users
- [ ] Click "Audit Log" — see recent activity log entries
- [ ] Click "Site Map" — see all routes in the app listed by blueprint
- [ ] Click back to Admin Dashboard

---

### STEP 10: Site Map

- [ ] Go to Admin → Site Map (/admin/sitemap)
- [ ] You see routes grouped by blueprint name (admin_hub, auth, dashboard, etc.)
- [ ] Each route shows its URL, HTTP methods (colored GET/POST badges), and endpoint name

---

### STEP 11: Dashboard / Today View (F4)

- [ ] Go to Dashboard (/dashboard)
- [ ] You see a date bar with the current date
- [ ] You see "Yesterday / Today / Tomorrow" navigation buttons
- [ ] Click Yesterday — the date changes and the URL updates
- [ ] Click Tomorrow — same behavior
- [ ] You see a Duration Estimator bar (Appointments, New Patients, Booked hrs, Pace, End Time)
- [ ] You see a Patient Schedule table (or "No appointments loaded" message if scraper hasn't run)

---

### STEP 12: Setup Wizard

- [ ] Look in the header bar for a gold gear icon with a number badge
- [ ] Click it — you're taken to /setup
- [ ] You see a checklist of setup tasks based on your role
- [ ] Completed tasks have a green checkmark
- [ ] Incomplete tasks have numbered forms to fill out
- [ ] Fill out a task, submit — the count updates

---

### STEP 13: NetPractice Settings (Admin-only)

- [ ] Go to Admin → NetPractice Settings (/admin/netpractice)
- [ ] You see the webPRACTICE URL and Client Number fields
- [ ] You see a "Navigation Wizard" link to record click paths (**wizard needs redesign — see Day 2 notes**)
- [ ] You see scrape time and interval settings

---

### STEP 14: Agent Status (F3a)

- [ ] In the header, you see two small status dots (left side)
- [ ] Left dot = Agent status (likely red/grey since agent.py is not running)
- [ ] Right dot = NetPractice auth status
- [ ] Go to Admin → Background Agent (/admin/agent)
- [ ] You see agent health details (heartbeat, uptime, events, errors)

---

### STEP 15: Error Pages

- [ ] Go to http://localhost:5000/nonexistent-page
- [ ] You see a custom 404 error page (not the ugly default Flask one)

---

## PowerShell Verification Script

Open a **second terminal** (don't stop the running Flask server!) and run:

```powershell
cd C:\Users\coryd\Documents\NP_Companion
venv\Scripts\python.exe -c "
from app import create_app
app = create_app()
app.config['TESTING'] = True

print('=== NP Companion Day 1 Verification ===')
print()

# Check all database tables exist
with app.app_context():
    from models import db
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    expected = ['users', 'audit_log', 'time_logs', 'inbox_snapshots', 'inbox_items',
                'oncall_notes', 'order_sets', 'order_items', 'medication_entries',
                'lab_tracks', 'lab_results', 'care_gaps', 'ticklers', 'delayed_messages',
                'reformat_logs', 'agent_logs', 'agent_errors', 'schedules']
    print(f'Database tables: {len(tables)} found')
    missing = [t for t in expected if t not in tables]
    if missing:
        print(f'  MISSING tables: {missing}')
    else:
        print(f'  All {len(expected)} expected tables present!')
    print()

# Check all pages load correctly
with app.test_client() as client:
    with app.app_context():
        from models.user import User
        user = User.query.filter_by(username='CORY').first()
        if not user:
            print('ERROR: No user named CORY found. Create one first.')
            exit()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)

    pages = {
        'Dashboard': '/dashboard',
        'Dashboard (yesterday)': '/dashboard?date=2026-03-15',
        'Dashboard (tomorrow)': '/dashboard?date=2026-03-17',
        'Settings - Account': '/settings/account',
        'Settings - Notifications': '/settings/notifications',
        'Setup Wizard': '/setup',
        'Admin Hub': '/admin',
        'Admin - Users': '/admin/users',
        'Admin - Audit Log': '/admin/audit-log',
        'Admin - Agent': '/admin/agent',
        'Admin - NetPractice': '/admin/netpractice',
        'Admin - NP Wizard': '/admin/netpractice/wizard',
        'Admin - Sitemap': '/admin/sitemap',
        'API - Setup Status': '/api/setup-status',
        'API - Agent Status': '/api/agent-status',
        'API - Auth Status': '/api/auth-status',
        'API - Notifications': '/api/notifications',
        'API - Schedule': '/api/schedule?date=2026-03-16',
        'Timer (placeholder)': '/timer',
        'Inbox (placeholder)': '/inbox',
        'On-Call (placeholder)': '/oncall',
        'Orders (placeholder)': '/orders',
        'Med Ref (placeholder)': '/medref',
        'Lab Track (placeholder)': '/labtrack',
        'Care Gaps (placeholder)': '/caregap',
        'Metrics (placeholder)': '/metrics',
        'Tools (placeholder)': '/tools',
    }

    passed = 0
    failed = 0
    for name, url in pages.items():
        try:
            r = client.get(url)
            if r.status_code == 200:
                print(f'  PASS  {name} ({url})')
                passed += 1
            else:
                print(f'  FAIL  {name} ({url}) -> {r.status_code}')
                failed += 1
        except Exception as e:
            print(f'  ERROR {name} ({url}) -> {e}')
            failed += 1

    print()
    print(f'Results: {passed} passed, {failed} failed out of {len(pages)} pages')

    # Test 404 error page
    r = client.get('/this-does-not-exist')
    print(f'404 page: {\"PASS\" if r.status_code == 404 else \"FAIL\"}')

    # Test login required redirect
    with app.test_client() as anon_client:
        r = anon_client.get('/dashboard')
        print(f'Login redirect: {\"PASS\" if r.status_code == 302 else \"FAIL\"}')

print()
print('=== Verification Complete ===')
"
```

---

## Gap Analysis: Dev Guide vs What Was Built

### Features FROM the Dev Guide That Were Successfully Built

| Dev Guide Feature | Status | Notes |
|---|---|---|
| **F1: Project skeleton** (app.py, base.html, CSS, JS) | ✅ Done | All 4 files exist and work |
| **F1a: Multi-user accounts** (User model, login, register) | ✅ Done | Full CRUD, 3 test users exist |
| **F1b: Role-based access** (@require_role, sidebar filtering) | ✅ Done | provider/ma/admin roles enforced |
| **F1c: Dark mode** (toggle + persistence) | ✅ Done | localStorage + server-side save |
| **F1d: Notification preferences** (/settings/notifications) | ✅ Done | All settings from dev guide present |
| **F1e: Auto-lock** (5-min timeout, PIN overlay) | ✅ Done | PIN hash, 3-strike lockout, configurable timeout |
| **F1f: Audit trail** (after_request hook, /admin/audit-log) | ✅ Done | Filters by user, date, module |
| **F2: Database schema** (all model files) | ✅ Done | 18 tables (15 original + 3 extras) |
| **F3: Background agent** (agent.py) | ✅ Built | Heartbeat, crash recovery, main loop |
| **F3a: Agent health monitor** (status dot in header) | ✅ Done | Green/yellow/red dot + /admin/agent page |
| **F3b: Per-provider agent profiles** (active_user.json) | ✅ Done | Written on login/logout |
| **F3c: Crash recovery** (incomplete session detection) | ✅ Done | Detects orphaned time logs on startup |
| **F4: NetPractice schedule scraper** (Playwright) | ✅ Built | CGM webPRACTICE login + navigation |
| **F4a: New patient flag** (gold NEW badge) | ✅ Done | Badge in Today View, count in stats bar |
| **F4b: Duration estimator** (pace/end time prediction) | ✅ Done | Shows in dashboard header bar |
| **F4c: Double-booking & gap detector** | ✅ Done | Anomaly alerts card in dashboard |
| **F4e: Re-auth watchdog** (banner + Pushover flag) | ✅ Done | Banner in dashboard, auth-status dot |

### Features FROM the Dev Guide That Are MISSING or INCOMPLETE

These need to be added in a future session:

| Dev Guide Feature | Status | What's Missing |
|---|---|---|
| **F3: System tray icon** (pystray with blue "NP" icon) | ❌ Missing | agent.py runs as a console script only — no pystray tray icon, no right-click menu (Open, Pause, Resume, Check Inbox, View Status, Quit) |
| **F3: HTTP status on port 5001** | ❌ Missing | Dev guide says agent exposes status via HTTP on port 5001. Currently agent status is read from DB heartbeats only, no HTTP server in agent.py |
| **F3: APScheduler integration** | ❌ Missing | agent.py uses a simple while-loop with time.sleep(), not APScheduler BackgroundScheduler |
| **F3: agent/scheduler.py file** | ❌ Missing | Dev guide says create agent/scheduler.py; no agent/ folder exists yet. Jobs are inline placeholders in agent.py |
| **F3: agent_startup.xml** | ❌ Missing | No Windows Task Scheduler XML file for auto-starting agent at Windows login |
| **F3c: Popup for incomplete sessions** | ⚠️ Partial | Crash recovery detects incomplete sessions but auto-closes them instead of popping up a notification asking the provider to confirm end time |

### Placeholder Modules (Sidebar links exist, pages say "Coming Soon")

These 9 modules appear in the sidebar as clickable links. Each one loads a page, but the page only shows a placeholder message. They are shells waiting for later phases:

| Module | URL | Builds In |
|---|---|---|
| Timer | /timer | Phase 4 |
| Inbox | /inbox | Phase 2 (F5) |
| On-Call | /oncall | Phase 3 (F7) |
| Orders | /orders | Phase 3 (F8) |
| Med Ref | /medref | Phase 3 (F10) |
| Lab Track | /labtrack | Phase 4 (F11) |
| Care Gaps | /caregap | Phase 5 (F15) |
| Metrics | /metrics | Phase 4 (F13) |
| Tools | /tools | Phase 7 |

---

## Priority Action Items for Day 2

### Must Fix (Missing from Dev Guide)
1. **Add pystray system tray icon to agent.py** — blue circle with "NP" text, right-click menu (Open, Pause, Resume, Check Inbox, View Status, Quit)
2. **Add APScheduler** to agent.py — Replace the simple while-loop with BackgroundScheduler for proper job scheduling
3. **Create agent/scheduler.py** — Move job definitions into their own file per the dev guide folder structure
4. **Create agent_startup.xml** — Windows Task Scheduler XML for auto-starting agent at login
5. **Add HTTP status endpoint on port 5001** — The dev guide says the agent should expose a simple HTTP endpoint

### Must Redesign: NetPractice Setup Wizard
The current NP Setup Wizard (/admin/netpractice/wizard) records manual text-based click instructions.
This **needs to be completely redesigned** as a smart keyboard/mouse recorder:

**New Wizard Design:**
- The wizard should act as a **keyboard & mouse recorder** that captures the user's actual navigation through NetPractice
- Instead of following exact pixel coordinates, it should **identify what was clicked based on image/icon recognition and surrounding visual features** (e.g. "clicked the 'Schedule' menu item" not "clicked at 450, 320")
- This makes the recorded path work even if the NetPractice page layout shifts slightly
- Must have a **start/stop keystroke command** (e.g. Ctrl+Shift+R to start recording, same to stop)
- Should display a small **instructional overlay** during recording that does NOT interfere with the NetPractice page underneath (maybe a thin banner at the top or a floating badge in the corner)
- The recorded navigation path gets **saved per-user** as their personal access pattern to reach their schedule
- The scraper then replays this recorded path instead of hard-coded navigation steps

**Why redesign:** The original text-based step recording is fragile and requires the user to manually describe each click. A visual recorder that understands UI elements will be more reliable and user-friendly.

### Nice to Have
6. **Manual scrape button** on dashboard — User requested but not yet implemented
7. **Scrape progress indicator** — Show when the scraper is running and its status

### Completed End-of-Day-1
- **restart.bat** — Full restart script: kills all Python, runs test.py, starts server, opens Chrome to dashboard. Opens Notepad error log on failure.
- **test.py** — Permanent verification test suite: checks 18 DB tables, 27 pages, 404 page, login redirect
- **DEBUG mode + error display** — config.py DEBUG=True shows full tracebacks on 500/404 pages during development. Also logs errors to data/error.log. Set DEBUG=False before going live.

---

## Complete File Inventory

### Files Created on Day 1

| File | Purpose |
|------|---------|
| app.py | Flask app factory + blueprint registration |
| agent.py | Background agent (console script, no tray yet) |
| config.py | Machine-specific settings |
| utils.py | log_access() helper |
| models/__init__.py | SQLAlchemy instance + model imports |
| models/user.py | User accounts, credentials, setup tracking |
| models/audit.py | AuditLog model |
| models/agent.py | AgentLog + AgentError models |
| models/timelog.py | Time tracking records |
| models/inbox.py | InboxSnapshot + InboxItem |
| models/oncall.py | OnCallNote model |
| models/orderset.py | OrderSet + OrderItem |
| models/medication.py | MedicationEntry model |
| models/labtrack.py | LabTrack + LabResult |
| models/caregap.py | CareGap model |
| models/tickler.py | Tickler model |
| models/message.py | DelayedMessage model |
| models/reformatter.py | ReformatLog model |
| models/schedule.py | Schedule model |
| routes/__init__.py | Package init |
| routes/auth.py | Login, register, settings, setup, audit log |
| routes/admin.py | Admin hub, sitemap, server restart |
| routes/dashboard.py | Today View with date nav + anomaly detection |
| routes/agent_api.py | Agent status API + admin agent page |
| routes/netpractice_admin.py | NP settings + setup wizard |
| routes/timer.py | Placeholder |
| routes/inbox.py | Placeholder |
| routes/oncall.py | Placeholder |
| routes/orders.py | Placeholder |
| routes/medref.py | Placeholder |
| routes/labtrack.py | Placeholder |
| routes/caregap.py | Placeholder |
| routes/metrics.py | Placeholder |
| routes/tools.py | Placeholder |
| scrapers/__init__.py | Package init |
| scrapers/netpractice.py | CGM webPRACTICE Playwright scraper |
| templates/base.html | Master layout (sidebar, header, auto-lock) |
| templates/login.html | Login page |
| templates/register.html | Registration page |
| templates/dashboard.html | Today View with patient schedule |
| templates/settings_account.html | Account settings |
| templates/settings_notifications.html | Notification preferences |
| templates/setup.html | Role-based onboarding wizard |
| templates/admin_dashboard.html | Admin hub with tool cards |
| templates/admin_users.html | User management page |
| templates/admin_audit_log.html | Audit log viewer |
| templates/admin_netpractice.html | NetPractice settings |
| templates/admin_sitemap.html | Site map page |
| templates/np_setup_wizard.html | Navigation recording wizard |
| templates/errors/404.html | Custom 404 page |
| templates/errors/500.html | Custom 500 page |
| templates/timer.html | Placeholder |
| templates/inbox.html | Placeholder |
| templates/oncall.html | Placeholder |
| templates/orders.html | Placeholder |
| templates/medref.html | Placeholder |
| templates/labtrack.html | Placeholder |
| templates/caregap.html | Placeholder |
| templates/metrics.html | Placeholder |
| templates/tools.html | Placeholder |
| static/css/main.css | All styles + dark mode |
| static/js/main.js | 9 init functions |
| migrate_add_ac_columns.py | DB migration (already run) |
| .github/ChangeLog/cl1.md | CL1: Database schema |
| .github/ChangeLog/cl2.md | CL2: Agent health + active user |
| .github/ChangeLog/cl3.md | CL3: NetPractice scraper |
| .github/ChangeLog/cl4.md | CL4: Admin hub + setup wizard |
