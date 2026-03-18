# Changelog — CL4
**Date:** 2026-03-16 01:20 AM  
**Phase:** Phase 1 (Foundation) + Phase 2 (Data Layer kick-off)  
**Summary:** Admin hub consolidation, dashboard date navigation, role-based setup wizard, Amazing Charts & PC credential storage, site map page, Windows compatibility fix

---

## Changes Made

### 1. Fixed Dashboard 500 Error
- **File:** `templates/dashboard.html`
- **Issue:** Invalid Jinja syntax `{% if not config.NETPRACTICE_URL if config is defined else true %}` caused an Internal Server Error on every dashboard load.
- **Fix:** Replaced with static setup-prompt text pointing users to /admin/netpractice.

### 2. Admin Dashboard Hub (NEW)
- **File:** `routes/admin.py` (new), `templates/admin_dashboard.html` (new)
- Admin sidebar consolidated from 5 separate links → single "Admin" link
- Hub page shows 6 cards: User Management, Audit Log, NetPractice Settings, Background Agent, Site Map, Restart Server
- Each card has icon, title, and description

### 3. Admin Sidebar Consolidation
- **File:** `templates/base.html`
- Removed 5 individual admin sidebar items (Users, Audit Log, Agent, NetPractice, Restart Server)
- Replaced with single "Admin" link pointing to `/admin` hub

### 4. Site Map Page (NEW)
- **File:** `templates/admin_sitemap.html` (new), route in `routes/admin.py`
- Lists all registered routes grouped by blueprint
- Shows URL pattern, HTTP methods (color-coded badges), and endpoint name
- Accessible at `/admin/sitemap`

### 5. Dashboard Date Navigation
- **File:** `templates/dashboard.html`, `routes/dashboard.py`
- Added Yesterday / Today / Tomorrow navigation buttons above patient list
- Dashboard accepts `?date=YYYY-MM-DD` parameter for any date
- Patient table now shows columns: Time, Patient, MRN (masked ••XXXX), Reason, Status
- Added `/api/schedule?date=YYYY-MM-DD` JSON endpoint

### 6. Role-Based Setup Wizard (NEW)
- **File:** `templates/setup.html` (new), route in `routes/auth.py`
- Shows task checklist based on user role:
  - **Providers/Admins:** Display Name, NP Credentials, NP Nav Steps, AC Credentials
  - **MAs:** Display Name only
- Inline forms for each incomplete task — no page reloads needed
- PC password is optional (shown as bonus task)
- Shows "🎉 Setup Complete!" when all required tasks are done
- Records `setup_completed_at` timestamp when finished

### 7. Setup Button in Header
- **File:** `templates/base.html`, `static/js/main.js`, `static/css/main.css`
- Gold gear icon button appears in header between clock and notification bell
- Badge shows count of incomplete setup tasks
- Polls `/api/setup-status` every 60 seconds
- Disappears when setup is complete

### 8. Amazing Charts Credential Storage
- **File:** `models/user.py`, `routes/auth.py`, `templates/settings_account.html`
- New encrypted columns: `ac_username_enc`, `ac_password_enc`
- Fernet encryption using SHA-256 hash of SECRET_KEY (same pattern as NP credentials)
- Accessible from both Setup Wizard and Settings > Account page

### 9. Work PC Password Storage (Optional)
- **File:** `models/user.py`, `routes/auth.py`, `templates/settings_account.html`
- New encrypted column: `pc_password_enc`
- Optional — shown in settings for convenience only
- Useful for remote login automation scenarios

### 10. Database Migration
- **File:** `migrate_add_ac_columns.py` (new, already run)
- Added 4 new columns to `users` table:
  - `ac_username_enc` (Text)
  - `ac_password_enc` (Text)
  - `pc_password_enc` (Text)
  - `setup_completed_at` (DateTime)

### 11. Windows Strftime Compatibility Fix
- **File:** `templates/dashboard.html`
- `%-d` (Linux-only no-padding format) replaced with `%d` + Jinja `.replace(' 0', ' ')` pattern
- Fixed 4 instances across date navigation labels

---

## Files Created
| File | Purpose |
|------|---------|
| `routes/admin.py` | Admin hub, site map, server restart routes |
| `templates/admin_dashboard.html` | Admin hub page with card links |
| `templates/admin_sitemap.html` | Developer site map listing all routes |
| `templates/setup.html` | Role-based onboarding wizard |
| `migrate_add_ac_columns.py` | DB migration (already run) |

## Files Modified
| File | Changes |
|------|---------|
| `models/user.py` | AC/PC credential columns + encrypt/decrypt + setup tracking methods |
| `app.py` | Registered admin_bp, added /api/setup-status to audit skip paths |
| `routes/auth.py` | Setup wizard route, API endpoint, AC/PC credential handlers |
| `routes/dashboard.py` | Date param support, api_schedule endpoint |
| `templates/dashboard.html` | Fixed Jinja error, date nav, patient table, strftime fix |
| `templates/base.html` | Admin sidebar → single link, setup button in header |
| `templates/settings_account.html` | Setup Wizard link, AC credentials card, PC password card |
| `static/js/main.js` | initSetupStatus() polling function |
| `static/css/main.css` | .setup-btn and .setup-badge styles |

---

## Verification Checkpoints

### Checkpoint 1: Start the app
```powershell
cd C:\Users\coryd\Documents\NP_Companion
venv\Scripts\python.exe app.py
```
Open Chrome to http://localhost:5000 and log in as CORY.

### Checkpoint 2: Dashboard loads without errors
- Visit http://localhost:5000/dashboard
- ✅ Page loads with no 500 error
- ✅ You see "Yesterday / Today / Tomorrow" date buttons
- ✅ Patient table shows headers: Time, Patient, MRN, Reason, Status
- ✅ Clicking Yesterday/Tomorrow changes the date; Today returns to current date

### Checkpoint 3: Admin sidebar is a single link
- ✅ Left sidebar shows only one "Admin" item (not 5 separate ones)
- ✅ Clicking it opens the Admin Dashboard hub page
- ✅ Hub shows 6 cards: Users, Audit Log, NetPractice, Agent, Site Map, Restart

### Checkpoint 4: Site Map
- ✅ From Admin hub, click "Site Map" card
- ✅ See all routes listed by blueprint (auth, dashboard, admin, etc.)
- ✅ Each route shows URL, HTTP methods (GET/POST badges), and endpoint name

### Checkpoint 5: Setup Wizard
- ✅ In the header bar, you see a gold gear icon (⚙) with a number badge
- ✅ Click it → goes to /setup page
- ✅ Shows a task checklist with completed items checked (✓) and incomplete numbered
- ✅ Incomplete tasks have inline forms to fill out
- ✅ After filling all required fields, page shows "🎉 Setup Complete!"

### Checkpoint 6: AC Credentials in Settings
- ✅ Go to Settings > Account
- ✅ See "Amazing Charts Credentials" card
- ✅ Enter a test username/password → save → see "✓ Saved" badge
- ✅ See "Work PC Password" card (optional)

### Checkpoint 7: Setup button disappears when complete
- ✅ After completing all setup tasks, the gold gear icon in the header disappears
- ✅ (May take up to 60 seconds for the polling to update)

---

## Automated Verification Script
```powershell
cd C:\Users\coryd\Documents\NP_Companion
venv\Scripts\python.exe -c "
from app import create_app
app = create_app()
app.config['TESTING'] = True
with app.test_client() as client:
    with app.app_context():
        from models.user import User
        user = User.query.filter_by(username='CORY').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
    pages = ['/dashboard', '/dashboard?date=2026-03-15', '/setup', '/admin', '/admin/sitemap', '/api/setup-status', '/api/schedule?date=2026-03-16', '/settings/account']
    for page in pages:
        r = client.get(page)
        status = 'PASS' if r.status_code == 200 else f'FAIL ({r.status_code})'
        print(f'{page}: {status}')
"
```
Expected: all 8 pages show PASS.

---

## Features Update v1.4

**What's New:**

- **Admin Dashboard** — All admin tools are now in one place. Click "Admin" in the sidebar to see a hub page with links to User Management, Audit Log, NetPractice Settings, Agent Status, Site Map, and Server Restart.

- **Site Map** — A new page listing every page in the app, organized by section. Helpful for finding features you forgot about.

- **Dashboard Date Navigation** — Your patient schedule now has Yesterday/Today/Tomorrow buttons so you can quickly check who was seen yesterday or who's coming tomorrow.

- **Setup Wizard** — New users (or existing users who haven't finished setup) will see a gold gear icon in the header. Click it to walk through getting everything configured: your name, NetPractice login, how to navigate to your schedule, and your Amazing Charts login.

- **Amazing Charts Credentials** — The app can now securely store your Amazing Charts username and password (encrypted, never leaves your computer). This will be used for future automation features.

- **Work PC Password** — Optionally store your Windows login password for remote access scenarios. Encrypted the same way as other credentials.

- **Bug Fix** — Fixed a crash that happened when opening the dashboard.
