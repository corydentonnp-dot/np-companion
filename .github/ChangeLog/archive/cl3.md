# Changelog — CL3: NetPractice Admin, Setup Wizard & CGM webPRACTICE Scraper

**Date:** 2025-07-14  
**Phase:** Phase 2 — Data Layer  
**Features:** F4 NetPractice Schedule Scraper, Admin Config, Per-User Credentials

---

## What Changed

### 1. Per-User Encrypted NetPractice Credentials (models/user.py)
- Added 4 new columns to the User model:
  - `np_username_enc` — Fernet-encrypted webPRACTICE username
  - `np_password_enc` — Fernet-encrypted webPRACTICE password
  - `np_provider_name` — Provider display name as shown in webPRACTICE (e.g. "ASHLEY MORSBERGER FNP (45)")
  - `nav_steps` (JSON) — Recorded navigation steps for the scraper to replay
- Added encryption helpers: `set_np_credentials()`, `get_np_username()`, `get_np_password()`, `has_np_credentials()`
- Added `nav_steps` property with JSON getter/setter
- Credentials encrypted at rest using Fernet (SHA-256 hash of SECRET_KEY)

### 2. Schedule Model Updates (models/schedule.py)
- Added 7 new columns from the appointment detail page:
  - `patient_mrn`, `patient_phone`, `reason`, `units`, `location`, `comment`, `entered_by`

### 3. Admin NetPractice Settings Page (routes/netpractice_admin.py + templates/admin_netpractice.html)
- New blueprint: `np_admin_bp` with 6 routes
- Admin page at `/admin/netpractice` to configure:
  - webPRACTICE URL
  - Client Number
  - Scrape time  
  - Max appointment hour
- Provider setup status table showing each user's credential/step status
- Settings stored in `data/np_settings.json`

### 4. Setup Wizard (templates/np_setup_wizard.html)
- Interactive page at `/admin/netpractice/wizard`
- Default steps pre-loaded: Click "Schedule" → Click "Review Patient Appointments"
- Users can add/remove/reorder steps
- Each step has: action type, target text, wait condition, description
- Save button POSTs to `/api/netpractice/save-steps`
- Test button saves steps then runs a login dry-run

### 5. Account Settings — NP Credentials Card (templates/settings_account.html)
- Added "NetPractice Login" card to account settings
- Fields: Username, Password, Provider Name
- Credentials are encrypted before storage

### 6. CGM webPRACTICE Scraper Rewrite (scrapers/netpractice.py)
- Complete rewrite for the actual CGM webPRACTICE interface (was previously placeholder code assuming Google auth)
- Login: fills Client Number + Username + Password → clicks Log In
- Navigation: replays user's recorded nav steps to reach schedule page
- Schedule parsing: regex-based extraction of "TIME LASTNAME, FIRSTNAME (MRN)" patterns
- Detail collection: clicks each patient → reads appointment detail fields → browser back
- Fields collected: visit type, reason, status, location, units, DOB, phone, new patient flag, entered by
- Cookie persistence: saves/loads Playwright cookies for session reuse
- Date navigation: forward/back arrow clicking for tomorrow's scrape

### 7. Wiring & Config
- Registered `np_admin_bp` blueprint in app.py
- Added "NetPractice" link (monitor icon) to admin sidebar in base.html
- Updated config.py with real webPRACTICE URL and client number
- Added `/api/netpractice/` to audit skip paths
- Installed `cryptography` package; generated `requirements.txt`
- Database migration: `migrate_add_np_columns.py` adds all new columns

---

## Verification Checkpoints

### Checkpoint 1 — Start the App
```powershell
cd C:\Users\coryd\Documents\NP_Companion
venv\Scripts\python.exe app.py
```
- The server should start on http://localhost:5000 with no errors.

### Checkpoint 2 — Check Admin Sidebar
1. Open http://localhost:5000 in Chrome
2. Log in with your admin account
3. Look at the left sidebar under the "Admin" section
4. You should see: Users, Audit Log, Agent, **NetPractice**, Restart Server

### Checkpoint 3 — Admin NetPractice Page
1. Click "NetPractice" in the admin sidebar
2. You should see:
   - Connection Settings form with URL pre-filled, client number field
   - Scrape time and max appointment hour fields
   - Provider Setup Status table listing all users
   - Quick Actions section with wizard and test buttons

### Checkpoint 4 — Save NP Settings
1. On the admin NetPractice page, enter:
   - URL: `https://wppm2.cgmus.com/scripts/npm7.mar?wlapp=npm7&MGWCHD=p`
   - Client Number: `2034`
2. Click "Save Settings"
3. Should flash "NetPractice settings saved."

### Checkpoint 5 — Account Settings NP Credentials
1. Click Settings (gear icon) in the sidebar footer
2. Scroll to the bottom — you should see a "NetPractice Login" card
3. Enter a username, password, and provider name
4. Click "Save Credentials"
5. Should flash "NetPractice credentials saved."
6. Reload page — username and provider name should be pre-filled, password shows placeholder

### Checkpoint 6 — Setup Wizard
1. Go to Admin → NetPractice → click "Run Setup Wizard"
2. You should see:
   - Prerequisites checklist (green ✓ or red ✗)
   - "How the Scraper Navigation Works" explanation
   - Two default steps pre-loaded (Schedule, Review Patient Appointments)
3. Click "Save Navigation Steps" — should show green success message
4. Add a step, remove a step, verify the numbering updates correctly

### Checkpoint 7 — Database Migration (if first run after update)
```powershell
cd C:\Users\coryd\Documents\NP_Companion
venv\Scripts\python.exe migrate_add_np_columns.py
```
- Should report "+ Added" for each new column, or "= already exists" if already run

### Checkpoint 8 — Verify Database Columns
```powershell
cd C:\Users\coryd\Documents\NP_Companion
venv\Scripts\python.exe -c "import sqlite3; conn=sqlite3.connect('data/npcompanion.db'); c=conn.cursor(); c.execute('PRAGMA table_info(users)'); print([r[1] for r in c.fetchall()]); c.execute('PRAGMA table_info(schedules)'); print([r[1] for r in c.fetchall()])"
```
- Users should include: `np_username_enc`, `np_password_enc`, `np_provider_name`, `nav_steps`
- Schedules should include: `patient_mrn`, `patient_phone`, `reason`, `units`, `location`, `comment`, `entered_by`

---

## Files Created
- `routes/netpractice_admin.py` — Admin blueprint (6 routes)
- `templates/admin_netpractice.html` — Admin settings page
- `templates/np_setup_wizard.html` — Setup wizard interface
- `migrate_add_np_columns.py` — One-time schema migration
- `requirements.txt` — Frozen package list

## Files Modified
- `models/user.py` — NP credential columns + encryption helpers + nav steps
- `models/schedule.py` — 7 new columns for detail page data
- `scrapers/netpractice.py` — Complete rewrite for CGM webPRACTICE
- `routes/auth.py` — Added `set_np_credentials` handler
- `templates/settings_account.html` — NP credentials card
- `templates/base.html` — NetPractice admin sidebar link
- `app.py` — Blueprint registration + audit skip paths
- `config.py` — webPRACTICE URL + client number

## Key Decisions
- **Fernet encryption** for NP credentials at rest (not hashed — we need to decrypt them for the scraper)
- **Per-user nav steps** stored as JSON — each provider can have different navigation paths
- **Regex-based schedule parsing** rather than CSS selectors — CGM webPRACTICE uses non-standard HTML
- **Browser back** (`page.go_back()`) to return from detail page — matches the Alt+Back pattern
- **Detail fields extracted via text pattern matching** — resilient to layout changes
