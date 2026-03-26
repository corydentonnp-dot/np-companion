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

## PART 3 — Comprehensive Interactive Element Audit

> **Protocol:** For each item, attempt it. If it fails, try once more. If it fails again, log it and move on. Never let two failed attempts block forward progress.
> **2-Strike Rule:** Every task gets exactly 2 attempts. Log failure with element ID, URL, and error message, then continue.
> **Test Credentials:** `CORY` / `ASDqwe123` | Test MRN: `62815` | Test MRN (rich): `90001`

---

### PW-0: Global Navigation (base.html — runs on EVERY page)

**URL:** Any page while logged in

**Sidebar links — test each navigates correctly:**
- [ ] CareCompanion logo → `/dashboard`
- [ ] Dashboard → `/dashboard`
- [ ] Patients → `/patients`
- [ ] Inbox → `/inbox`
- [ ] Timer → `/timer`
- [ ] Billing → `/billing/log`
- [ ] Care Gaps → `/caregap`
- [ ] Orders → `/orders`
- [ ] Lab Track → `/labtrack`
- [ ] On-Call → `/oncall`
- [ ] Tools → `/tools`
- [ ] Calculators → `/calculators`
- [ ] Metrics → `/metrics`
- [ ] Bonus → `/bonus`
- [ ] Messages → `/messages`
- [ ] Notifications → `/notifications`
- [ ] Settings → `/settings`
- [ ] Admin (admin-only) → `/admin`

**Header / Global Controls:**
- [ ] Dark mode toggle switches theme and persists on reload
- [ ] Auto-lock timer displays and counts down
- [ ] Agent status indicator shows correct state
- [ ] Priority 1 badge (if visible) links to relevant page
- [ ] User display name shown in header

**Console check after navigation:**
- [ ] Zero `SyntaxError` or `TypeError` errors
- [ ] Zero 404s for static assets

---

### PW-1: Login & Authentication

**URL:** `/login`

**Form: Login (POST /login)**
- [ ] Username field (`#username`) — type `CORY`, verify accepted
- [ ] Password field (`#password`) — type `ASDqwe123`, verify accepted
- [ ] Password show/hide toggle button — click, verify password becomes visible; click again, hidden
- [ ] Sign In button — click with valid creds → should redirect to `/dashboard`
- [ ] Sign In button shows "Signing in…" loading state while submitting (disable + text change)

**Error handling:**
- [ ] Submit with blank username → error message appears (not 500)
- [ ] Submit with wrong password → "Invalid credentials" message appears
- [ ] Submit wrong password 5× → lockout message appears (rate limiting)
- [ ] Add `?next=http://evil.com` to URL → after login, redirects to `/dashboard` not external URL

**URL:** `/register`
- [ ] Registration form renders (or shows "disabled" message if not active)
- [ ] If active: username, password, confirm password, role fields present
- [ ] Submit with mismatched passwords → validation error

**URL:** `/onboarding`
- [ ] Onboarding wizard renders step 1
- [ ] Next button advances to step 2

**URL:** `/settings` (profile section)

**Form: Profile (POST /settings/profile)**
- [ ] Display name field — edit, save → persists on reload
- [ ] Email field — edit, save → persists on reload
- [ ] Username field — read-only (cannot change)
- [ ] Role field — read-only

**Form: Change Password (POST /settings/password)**
- [ ] Current password field
- [ ] New password field
- [ ] Confirm password field
- [ ] Submit with wrong current password → error message
- [ ] Submit with mismatched new passwords → validation error
- [ ] Submit with valid inputs → success flash message

**Form: Set PIN (POST /settings/pin)**
- [ ] 4-digit PIN input
- [ ] Set PIN button → success message

**URL:** `/settings/account`
- [ ] Account page loads with correct role label
- [ ] Any editable fields present → test save

**URL:** `/settings/notifications`
- [ ] Notification settings form renders
- [ ] Toggle each notification type checkbox
- [ ] Save button → success flash message
- [ ] Reload page → verify saved state persists

---

### PW-2: Dashboard

**URL:** `/dashboard`

**Schedule widget:**
- [ ] "Yesterday ←" button → updates schedule to previous day
- [ ] "Today" button → resets to today
- [ ] "→ Tomorrow" button → shows next day's schedule
- [ ] Grid/Table view toggle → switches layout, persists in localStorage on reload
- [ ] "Add to Schedule" button → opens add patient modal
  - [ ] MRN search typeahead — type `62815`, verify patient appears in dropdown
  - [ ] Keyboard nav: ArrowDown selects, Enter confirms
  - [ ] Submit → patient added to schedule
  - [ ] Duplicate MRN on same day → error (not silent duplicate)
- [ ] Scrape Tomorrow button → changes to "Scraping…" state; resets after 60s timeout
- [ ] Drag-and-drop patient card to reorder (if grid mode)
- [ ] Patient row click → navigates to patient chart

**Widgets:**
- [ ] Tier toggles (Action / Awareness / Review) → collapse/expand sections
- [ ] "Accept high-priority billing" batch button → fires request
- [ ] Dismiss anomaly button → hides anomaly card
- [ ] My Patients "All" tab → shows all imported patients
- [ ] My Patients "Claimed" tab → shows only claimed patients
- [ ] TCM alert dismiss button (X) → banner dismissed
- [ ] Manage Widgets button (header) → opens widget management UI

**Agent / polling:**
- [ ] Agent status indicator updates → verify no console errors from polling (10s interval)
- [ ] Priority 1 badge count matches visible P1 patients

---

### PW-3: Patient Roster

**URL:** `/patients`

**Roster:**
- [ ] "All Patients" tab → shows all imported patients
- [ ] "My Patients" tab → shows only claimed patients
- [ ] Search field (`#roster-search`) — type partial name → list filters live
- [ ] Search by MRN — type `62815` → correct patient shown
- [ ] Column sort: Name header click → sorts A→Z; click again → Z→A
- [ ] Column sort: DOB header → sorts chronologically
- [ ] Patient row click → navigates to `/patient/62815`

**URL:** `/patient/62815`

**Chart header:**
- [ ] Patient name, DOB, MRN, age, sex all visible
- [ ] Portal status badge visible
- [ ] Cell phone displayed

**Tabs — click each, verify content loads:**
- [ ] Overview tab → medications, problems, allergies visible
- [ ] Labs tab → lab results list or "none on file"
- [ ] Billing tab → billing opportunities for this patient
- [ ] Notes tab → progress notes list
- [ ] Calculators tab → calculator widget

**Inline actions:**
- [ ] "Claim Patient" button → POST, patient now shows in "My Patients"
- [ ] "Edit Demographics" toggle → reveals inline form with name/DOB/phone/email fields
  - [ ] Edit a field, save → data updates
  - [ ] Cancel → reverts to original
- [ ] ICD-10 Lookup button → opens modal
  - [ ] Search field — type "diabetes" → results appear
  - [ ] Click result → code populated in field
  - [ ] Close modal → modal dismissed
- [ ] "Add Diagnosis" button → opens ICD-10 lookup modal
- [ ] "Copy Diagnoses" button → opens column picker modal
  - [ ] Select columns via checkboxes
  - [ ] Copy → clipboard contains formatted text
- [ ] Medication item double-click → inline edit activates
- [ ] Medication filter tabs (Active / Inactive / All) → filters list
- [ ] Chart view mode dropdown → change to Compact → layout updates

**URL:** `/patient/62815/detail`
- [ ] Refresh button → reloads patient info card
- [ ] "View full chart" link → navigates to `/patient/62815`

**Unknown MRN:**
- [ ] Navigate to `/patient/00000` → 404 or empty state (not 500)

---

### PW-4: Inbox

**URL:** `/inbox`

**Tabs:**
- [ ] Inbox tab → message list loads
- [ ] Held Items tab → held messages list
- [ ] Audit Log tab → audit entries list
- [ ] Digest tab → digest period buttons visible

**Per message:**
- [ ] Click message row → detail view expands
- [ ] Hold button → hold reason dropdown appears
  - [ ] Select hold reason from dropdown
  - [ ] Confirm → message moves to Held Items tab
- [ ] Resolve button → POST, message removed from inbox
- [ ] Unread count badge matches visible unread items

**Digest tab:**
- [ ] 8h button → digest for last 8 hours loads
- [ ] 24h button → digest for last 24 hours
- [ ] 72h button → digest for last 72 hours
- [ ] 168h button → weekly digest

**Polling:**
- [ ] Wait 60s without action → `/api/inbox-status` is called, no console errors

---

### PW-5: Timer

**URL:** `/timer`

**Session controls:**
- [ ] "I'm Leaving" / "Back at Desk" F2F toggle → POST `/api/timer/f2f-toggle`, state updates
- [ ] Active session shows elapsed time counter ticking
- [ ] Complex flag button → toggles visual prominence of session
- [ ] Billing level dropdown (per session) — select 99214 → saves, persists on reload
- [ ] Visit type selector — select Telehealth → updates session type
- [ ] Delete session button → confirmation prompt → confirmed → session removed
- [ ] Note prompt button → prompt or modal appears

**Manual Entry:**
- [ ] "Manual Entry" toggle button → reveals hidden form
  - [ ] Patient MRN field — type `62815`
  - [ ] Call time datetime field
  - [ ] End time datetime field
  - [ ] Submit → new session appears in list
  - [ ] Close toggle → form hides

**E&M Calculator widget:**
- [ ] Collapsible toggle → expands/collapses calculator
- [ ] MDM complexity dropdown → select Moderate
- [ ] Total minutes input → enter 25
- [ ] Calculate → result appears

**AWV Checklist:**
- [ ] If AWV visit type selected → checklist appears
- [ ] Checklist items checkable

**Polling:**
- [ ] Status updates every 3s → no console errors

**URL:** `/timer/room-widget` (no login required)
- [ ] Widget loads WITHOUT authentication (no redirect to login)
- [ ] Room states visible
- [ ] Room toggle endpoint responding

---

### PW-6: Billing Suite

**URL:** `/billing/log`

**Filters:**
- [ ] Start date input — enter 01/01/2026
- [ ] End date input — enter 03/31/2026
- [ ] Billing level dropdown — select 99214
- [ ] Submit filter → table updates
- [ ] Clear filters → table resets

**Table:**
- [ ] Column header sort: Date → sorts chronologically
- [ ] Column header sort: Amount → sorts numerically
- [ ] Row detail toggle (expand button) → reveals detail row
- [ ] "Why?" / anomaly badge → opens anomaly side panel
  - [ ] Side panel opens with guidance text
  - [ ] Close panel button → panel dismisses
- [ ] Patient name link → navigates to patient chart
- [ ] Rationale textarea (per session) → type text, submit → saved

**URL:** `/billing/review`
- [ ] Each pending claim row visible
- [ ] Capture button (per row) → POST, row removed from pending
- [ ] Dismiss button (per row) → POST, row removed

**URL:** `/billing/em-calculator`
- [ ] MDM complexity dropdown → select all options in sequence
- [ ] Total minutes input → type 30
- [ ] Calculate button → recommended code appears

**URL:** `/billing/monthly`
- [ ] Month picker → select previous month → charts update
- [ ] Previous month navigation button → charts update
- [ ] Next month navigation button → charts update
- [ ] 3 charts render (not blank): E&M distribution, prior month comparison, 6-month trend

**URL:** `/billing/opportunity-report`
- [ ] Month selector → change month → report refreshes
- [ ] Charts render (not blank)

**URL:** `/billing/benchmarks`
- [ ] Month navigation buttons → data updates
- [ ] Benchmark toggle checkbox → shows/hides comparison lines on chart
- [ ] Chart renders 7-month trend

**URL:** `/billing/why-not`
- [ ] Missed opportunity list renders or "none" message

**URL:** `/billing/monthly-revenue`
- [ ] Revenue chart renders (not blank canvas)

---

### PW-7: Care Gaps

**URL:** `/caregap`

**Navigation:**
- [ ] Date navigation: "← Yesterday" button → shows previous day's gaps
- [ ] "Today" button → resets to today
- [ ] "Tomorrow →" button → shows next day

**Per gap:**
- [ ] Gap row expand toggle → reveals detail
- [ ] "Address Now" button → reveals documentation form
  - [ ] Pre-filled documentation textarea visible
  - [ ] "Mark Addressed" submit → gap moves to addressed section
  - [ ] Cancel button → form hides
- [ ] "Copy Doc" button → clipboard copy + modal/feedback appears
- [ ] "Decline" button → POST, gap marked declined
- [ ] "N/A" button → POST, gap marked not applicable

**URL:** `/caregap/panel`
- [ ] Summary tab → summary counts visible
- [ ] Spreadsheet tab → full patient table visible
- [ ] Claimed tab → claimed-only patients visible
- [ ] Filter form: min_age=40, max_age=65, sex=Female → submit → table filters
- [ ] Clear filters link → table resets
- [ ] CSV Export button (full names) → file downloads
- [ ] Outreach link per gap type → navigates to outreach view

**URL:** `/caregap/outreach` (or `/caregap/panel/outreach?gap_type=...`)
- [ ] Patient list renders
- [ ] View Gaps link per patient → navigates to patient care gap view
- [ ] Export CSV button → file downloads

**URL:** `/caregap/patient/62815`
- [ ] "Personalized" toggle → filters to relevant gaps
- [ ] "All Applicable" toggle → shows all gaps
- [ ] Print Patient Handout link → opens print view
- [ ] Address Now / Copy Doc / Decline / N/A buttons (same as daily view)
- [ ] "Reopen" button (on addressed gaps) → reopens gap

---

### PW-8: Orders & Order Sets

**URL:** `/orders`

**Order set cards:**
- [ ] "New Order Set" button → opens builder modal
  - [ ] Search field — type "CBC" → items appear in list
  - [ ] Click item → moves to selected panel
  - [ ] Click again → removed from selected
  - [ ] "Clear all" button → selection cleared
  - [ ] Category tabs (All, Recent, Favorites) → filter items
  - [ ] Execute button → opens execution confirmation
    - [ ] Confirmation checkbox — check it
    - [ ] Execute button → fires POST `/orders/{id}/execute`
    - [ ] Cancel button → modal closes
  - [ ] Close modal → builder dismissed
- [ ] Edit button (per existing set) → opens builder with set pre-loaded
- [ ] Share/Unshare button (per set) → toggle icon updates
- [ ] Delete button (per set) → confirm prompt → delete confirmed → set removed
- [ ] History link (per set) → history modal opens
  - [ ] Past executions listed
  - [ ] Close modal → dismissed

**Interrupted banner (if present):**
- [ ] Resume button → reopens interrupted set
- [ ] Dismiss button → banner disappears

**URL:** `/orders/master`
- [ ] Order list table renders
- [ ] Add Order form: order_name, order_tab, category fields → fill all → submit → new row appears
- [ ] Delete button (per order) → confirm → order removed

---

### PW-9: Lab Track

**URL:** `/labtrack`

**Add Tracking form:**
- [ ] MRN field — type `62815`
- [ ] Lab name field — type "CBC" → autocomplete suggestions appear → select one
- [ ] Interval field — type `90` (days)
- [ ] Panel dropdown — select a panel
- [ ] Submit → new tracking row appears in list
- [ ] "Seed Standard Panels" button → POST, standard panels added for patient

**Lab Reference Modal:**
- [ ] Open lab reference button → modal appears
- [ ] Filter/search in modal → results narrow
- [ ] Select lab → populates lab name field
- [ ] Close modal → dismissed

**Patient rows:**
- [ ] Click patient row → navigates to `/labtrack/62815`

**URL:** `/labtrack/62815`
- [ ] Lab tracking rows visible for patient
- [ ] Edit button (per row) → reveals edit form
  - [ ] Interval days field — change value
  - [ ] Threshold fields (critical_low, alert_low, alert_high, critical_high) — enter values
  - [ ] Notes textarea — type text
  - [ ] Save Changes → form submits, row updates
- [ ] "+ Result" button (per row) → reveals add result form
  - [ ] Result value field — type `11.2`
  - [ ] Result date field — select today
  - [ ] Add Result→ submits, new result appears in trend
- [ ] Trend chart renders for each lab (not blank canvas)
- [ ] Alert/critical threshold lines visible on chart

---

### PW-10: On-Call

**URL:** `/oncall`

**Filters:**
- [ ] All status link → shows all notes
- [ ] Pending link → filters to pending
- [ ] Entered link → filters to entered
- [ ] Not Needed link → filters to not-needed

**Per note:**
- [ ] Note expansion toggle → reveals detail
- [ ] Callback Done button (if pending callback) → POST, callback marked complete

**Buttons:**
- [ ] "New Call" button / link → navigates to `/oncall/new`
- [ ] "Handoff" button → generates/navigates to handoff page

**URL:** `/oncall/new`

**New Note form (POST /oncall/new):**
- [ ] Chief complaint field + microphone button → speak or type → text populated
- [ ] Call time datetime field → set to specific time
- [ ] Patient identifier field → type test identifier
- [ ] Recommendation textarea + microphone button → type text
- [ ] Note content textarea + microphone button → type text
- [ ] Callback promised radio: select "Yes" → callback_by datetime field appears
  - [ ] Set callback_by to a future time
  - [ ] Select "No" → callback_by field hides
- [ ] Documentation status radio: select "Pending"
- [ ] Save Note button → submits form → redirects to oncall list
- [ ] Back link → navigates to `/oncall`

**URL:** `/oncall/<id>` (first available note)
- [ ] Note detail renders
- [ ] Edit Note expandable `<details>` → click → edit form reveals
  - [ ] Chief complaint, recommendation, note content all editable
  - [ ] Save Changes → form submits, note updates
- [ ] Mark Entered button (if applicable) → POST, status updates
- [ ] Callback Done button (if applicable) → POST
- [ ] Export for AC link → navigates to export view

**URL:** `/oncall/handoff/<token>` (public, no auth)
- [ ] Page loads WITHOUT login redirect
- [ ] Handoff summary renders
- [ ] Print button → triggers browser print (window.print())

---

### PW-11: Clinical Tools

**URL:** `/tools`
- [ ] All tool cards visible
- [ ] Each card click → navigates to correct sub-page:
  - [ ] ICD-10 Coding → `/coding`
  - [ ] Prior Auth → `/pa`
  - [ ] Med Reference → `/medref`
  - [ ] Tickler → `/tickler`
  - [ ] Referral → `/referral`
  - [ ] Reformatter → `/reformatter`

**URL:** `/coding`
- [ ] Search field (`#code-search`) — type "hypertension" → results appear (debounced 300ms)
- [ ] Star/favorite button (per result) → POST `/coding/favorite`, icon toggles
- [ ] Copy button (per result) → clipboard copy, feedback shown
- [ ] "Specify" button (per result) → fetches more specific codes
- [ ] Click favorited code → searches it again

**URL:** `/pa`
- [ ] MRN field — type `62815`, lookup button → patient fields populated
- [ ] Drug name autocomplete — type "metformin" → suggestions appear → select one
- [ ] Payer dropdown — select a payer
- [ ] ICD-10 code field → open lookup modal → search → select code
- [ ] Payer Contact Details `<details>` element → click header → expands
- [ ] Add Failed Alternative button → new input row appears
  - [ ] Type alternative drug name
  - [ ] Add another → second row appears
  - [ ] × button → row removed
- [ ] Clinical justification textarea → type text
- [ ] Generate PA button → POST `/pa/generate`, narrative appears in output panel
- [ ] Copy Narrative button → clipboard copy
- [ ] Submit PA button → POST `/pa`
- [ ] History button → PA history modal opens
  - [ ] Past PAs listed with timeline
  - [ ] Close modal
- [ ] Approve/Deny/Appeal buttons (on existing PAs) → status updates

**URL:** `/pa/library`
- [ ] Shared PA records visible
- [ ] Import button (per record) → POST `/pa/{id}/import`, PA copied to my list

**URL:** `/reformatter`
- [ ] Step 1: Paste Note textarea → paste test clinical note text
- [ ] API validation checkbox → toggle on/off
- [ ] Process button → submits, advances to Step 2
- [ ] Step 2: Flagged items appear
  - [ ] "Keep" button (per flag) → flag resolved as keep
  - [ ] "Add to Template" button (per flag) → flag resolved as add
  - [ ] "Discard" button (per flag) → flag resolved as discard
  - [ ] Next button → advances to Step 3
- [ ] Step 3: Reformatted text in textarea
  - [ ] Copy button → clipboard copy
  - [ ] Submit button → POST `/reformatter/submit`
- [ ] Step indicator pills 1 / 2 / 3 → clickable to jump back

**URL:** `/dot-phrases`
- [ ] Search field (`#search-input`) — type partial phrase → list filters live
- [ ] Category tabs (All, Custom, HPI, etc.) — click each → list filters
- [ ] "Export as AHK" link → file downloads
- [ ] "+ Add Dot Phrase" button → modal opens
  - [ ] Abbreviation field — type `.test`
  - [ ] Category dropdown — select category
  - [ ] Expansion textarea — type expansion text
  - [ ] Placeholder buttons ({patient_name}, {date}, {provider_name}) → insert at cursor
  - [ ] Preview updates live as you type
  - [ ] Save button → modal closes, new phrase appears in list
- [ ] Edit button (per phrase) → modal opens pre-filled
  - [ ] Edit text → Save → phrase updates
- [ ] Delete button (per phrase) → confirm prompt → phrase removed
- [ ] Import button → import modal opens
  - [ ] Paste AHK hotstrings in textarea
  - [ ] Import → phrases added
  - [ ] Cancel → modal closes

**URL:** `/macros`
- [ ] Macros list renders
- [ ] Search or filter works
- [ ] Add macro → form works
- [ ] Delete macro → confirm → removed

**URL:** `/rems-reference` (or `/rems`)
- [ ] Drug list or search renders
- [ ] Search field — type drug name → filters list
- [ ] Drug card click → detail view expands

**URL:** `/reportable-diseases` (or `/reportable-diseases-reference`)
- [ ] Disease list renders
- [ ] Search field → filters list

**URL:** `/result-templates` (or `/tools/templates`)
- [ ] Tab navigation: My Templates / Shared / System → each shows content
- [ ] Category filter dropdown → filters list
- [ ] "+ New Template" button → modal opens
  - [ ] Name field — type name
  - [ ] Category dropdown — select
  - [ ] Template body textarea — type text with `{placeholder}`
  - [ ] Save → modal closes, template in list
- [ ] Preview button (eye icon, per template) → preview modal opens
  - [ ] Close → dismissed
- [ ] Edit button (pencil, per template) → modal opens pre-filled
- [ ] Share/Unshare button (lock icon) → toggle
- [ ] Delete (trash icon) → confirm → removed
- [ ] Fork button (shared/system templates) → POST, copy added to My Templates
- [ ] Mark Legally Reviewed button → POST, flag set

**URL:** `/medref`
- [ ] Drug search input — type "lisinopril" → drug card populates in right panel
- [ ] Clear button → right panel clears
- [ ] Quick filter: Pregnancy toggle → shows pregnancy safety info
- [ ] Quick filter: Renal toggle → shows renal dosing info
- [ ] Quick filter: Hepatic toggle → shows hepatic info
- [ ] FDA label sections (collapsible headers) → click to expand/collapse
- [ ] Pricing card → async-loads with Fresh/Aging/Stale badge
- [ ] Recent search history links → click → same drug card loads

**URL:** `/tickler`
- [ ] Tickler cards visible (or empty state)
- [ ] "+ Add Tickler" button → modal opens
  - [ ] Patient display field — type patient name
  - [ ] MRN field (optional) — type `62815`
  - [ ] Due date picker → select tomorrow
  - [ ] Priority dropdown → select Urgent
  - [ ] Assigned To dropdown → select user
  - [ ] Recurring checkbox → check → recurrence_days field appears
    - [ ] Type `30` (monthly)
    - [ ] Uncheck → field hides
  - [ ] Notes textarea → type text
  - [ ] Add Tickler button → POST, card appears in list
- [ ] Complete button (per card) → POST `/tickler/{id}/complete`, card removed
- [ ] Snooze button (per card) → prompt for days → POST `/tickler/{id}/snooze`, card updates due date

**URL:** `/referral`
- [ ] Specialty dropdown (`#ref-specialty`) → select Cardiology
- [ ] Dynamic specialty fields appear based on selection
- [ ] Reason field → type reason
- [ ] Patient description field → type description
- [ ] Urgency dropdown → select Urgent
- [ ] Relevant history textarea → type text
- [ ] Findings textarea → type text
- [ ] Medications textarea → type text
- [ ] Generate Letter button → spinner → letter text appears in right panel
- [ ] Copy button → clipboard copy, feedback shown
- [ ] Mark Received button (per existing referral in log) → POST `/referral/{id}/received`

---

### PW-12: Calculators

**URL:** `/calculators`
- [ ] Search field (`#calc-search`) — type "bmi" → BMI card visible, others hidden
- [ ] Clear search → all cards visible
- [ ] Category tabs (All, Cardiology, Infectious, Pediatric, etc.) → each filters correctly
- [ ] Calculator card click → navigates to correct detail page

**URL:** `/calculators/bmi`
- [ ] Height field — type `68` (inches)
- [ ] Weight field — type `185` (lbs)
- [ ] Calculate button → BMI result appears
- [ ] Valid result: should be ~28.1
- [ ] Clear/Reset → fields clear

**URL:** `/calculators/egfr`
- [ ] Age, sex, creatinine, race fields → fill in values
- [ ] Calculate → eGFR result appears

**URL:** `/calculators/chads2`
- [ ] Checkbox items (CHF, HTN, Age≥75, Diabetes, Stroke/TIA) → check several
- [ ] Score updates automatically or on Calculate click

**URL:** `/calculators/wells-dvt`
- [ ] Checkbox items → check several
- [ ] Calculate → pre-test probability result appears

**URL:** `/calculators/heart-score`
- [ ] Dropdown/radio items for each HEART component
- [ ] Calculate → score + risk category appears

**URL:** `/calculators/gcs`
- [ ] Eye/Verbal/Motor response dropdowns → select options
- [ ] Total GCS score calculated

**URL:** `/calculators/apgar`
- [ ] 5 component dropdowns/radios → select each
- [ ] Total APGAR calculated

**For all remaining calculators** (`wells-pe`, `qtc`, `map`, `ibw`, `corrected-calcium`, `sofa`, `curb65`, `alvarado`, `pediatric-dosing`, `steroid-taper`, `phenytoin`, `warfarin`):
- [ ] Page renders with all input fields labeled
- [ ] Known-good inputs → Calculate → result appears (not blank, not 500)
- [ ] Invalid input (letters in number field) → validation error shown
- [ ] "Save result" (if present) → POST, result saved to history

---

### PW-13: Admin Panel

**URL:** `/admin` (admin account required)
- [ ] All sub-section cards visible and linked
- [ ] Non-admin account → should be redirected (403 or to dashboard)

**URL:** `/admin/users`
- [ ] User list renders with roles visible
- [ ] Role change dropdown → select new role → confirm password field appears
  - [ ] Enter admin password → submit → role updates
- [ ] AI toggle button (per user) → POST, toggle state flips
- [ ] Deactivate button (per user) → mode selection appears
  - [ ] "Deactivate now" option selected
  - [ ] Confirm → user deactivated
- [ ] Reset Password button (per user) → temp password field shown → Send button
- [ ] Change Username button (per user) → hidden form reveals
  - [ ] New username + confirm password → submit → username updates

**URL:** `/admin/audit-log`
- [ ] Audit entries render
- [ ] No PHI visible in log entries (check: no real names, MRNs only hashed)

**URL:** `/admin/db-health`
- [ ] DB health check loads table counts
- [ ] No error states

**URL:** `/admin/feature-flags` (or equivalent)
- [ ] Feature flag list renders
- [ ] Toggle a flag → POST, state updates

**URL:** `/admin/backup`
- [ ] Backup trigger button → POST, success message (file created)
- [ ] List of existing backups visible

**URL:** `/admin/api-cache`
- [ ] Cached entries table renders
- [ ] Purge all / purge expired buttons → POST, cache cleared
- [ ] Row count updates after purge

**URL:** `/admin/notification-test`
- [ ] Test notification button → POST, Pushover message sent (check phone)

**URL:** `/admin/reformat-log`
- [ ] Discarded items log renders
- [ ] Each entry shows item content (not PHI) and discard reason

**URL:** `/admin/claim-rules`
- [ ] Billing rule list renders
- [ ] Each rule shows code, description, enabled state

**URL:** `/admin/config`
- [ ] All config sections render (Screen & OCR, Notifications, Inbox, Timer, etc.)
- [ ] Bool select → change True→False → Save → persists on reload
- [ ] Number input → change value → Save → persists
- [ ] Cancel link → returns to admin dashboard without saving

---

### PW-14: Monitoring, Briefing & Messaging

**URL:** `/monitoring-calendar`
- [ ] Calendar grid renders with correct month
- [ ] Month navigation (previous/next) → calendar updates
- [ ] Day cell click → detail for that day loads

**URL:** `/morning-briefing`
- [ ] Page loads with today's sections
- [ ] All data cards render (not blank)

**URL:** `/commute-briefing`
- [ ] Page loads with patient/task summary
- [ ] All sections present

**URL:** `/notifications`
- [ ] Notification history list renders
- [ ] Mark as read button (per notification) → POST, read_at timestamp set → visual state changes

**URL:** `/messages`
- [ ] Conversation list renders (or empty state)
- [ ] Click conversation → message thread loads
- [ ] "New Message" button / link → navigates to `/messages/new`

**URL:** `/messages/new`
- [ ] Recipient field — search for user → autocomplete appears
- [ ] Subject field — type subject
- [ ] Body textarea → type message
- [ ] Send button → POST, message sent → redirects to thread
- [ ] Cancel → back to messages list

---

### PW-15: Metrics & Benchmarks

**URL:** `/metrics`
- [ ] Page loads with chart containers (not blank `<canvas>`)
- [ ] Line/bar charts render actual data (not empty axes)
- [ ] Date range filter (if present) → change range → charts update
- [ ] Export button (if present) → file downloads
- [ ] MA role check: log in as MA → should be redirected

**URL:** `/metrics/weekly`
- [ ] Weekly drill-down renders
- [ ] Week navigation buttons → previous/next week → data updates

**URL:** `/benchmarks`
- [ ] Benchmark comparison data renders (or "insufficient data" message)
- [ ] Month selector (if present) → change → data refreshes

**URL:** `/bonus`
- [ ] All 7 bonus sections render
- [ ] Confirm threshold button → POST `/bonus/confirm-threshold`
- [ ] CCM calculator: CCM count input → change number → result updates dynamically
- [ ] Monthly receipt form: month input + amount input → Submit → receipt added to table
- [ ] Quick nav links (Timer, Billing Tasks, CCM Registry) → navigate correctly

---

### PW-16: Cross-Cutting Checks

**A. Dark Mode — Full Pass**
- [ ] Toggle dark mode (settings or top nav)
- [ ] Navigate each critical page: dashboard, patient chart, billing, inbox, admin, tools
- [ ] No white flash on navigation
- [ ] No unreadable text (white on white / black on black)
- [ ] Buttons, badges, modals all visible in dark
- [ ] Charts readable on dark background
- [ ] Toggle back to light → layout correct

**B. Mobile Viewport (375×812)**

*Use Playwright: resize browser to 375×812 before starting this section*
- [ ] Dashboard: no horizontal scroll, all widgets stack vertically
- [ ] Patient chart: tabs accessible, no overflow
- [ ] Billing log: table scrolls horizontally (not clipped)
- [ ] Inbox: message list usable
- [ ] Calculators: form fits viewport
- [ ] Navigation menu: accessible (hamburger or collapsible)
- [ ] Modals: fit within viewport

**C. Auth Enforcement**
- [ ] Log out → navigate to `/dashboard` → redirected to `/login?next=/dashboard`
- [ ] Navigate to `/patients` → redirected to login
- [ ] Navigate to `/billing/log` → redirected to login
- [ ] Navigate to `/admin` → redirected to login (or 403)
- [ ] After login with `next` param → redirected to originally intended page
- [ ] `/timer/room-widget` → loads WITHOUT login
- [ ] `/oncall/handoff/<token>` → loads WITHOUT login

**D. Flash Messages**
- [ ] Trigger a success action (save settings) → green flash message appears
- [ ] Trigger a validation error → red/orange flash appears
- [ ] Flash messages visible in dark mode
- [ ] Flash message dismisses on next navigation

**E. Console Cleanliness — Final Pass**

*Navigate each page, open browser console, verify:*
- [ ] `/dashboard` → zero errors
- [ ] `/patient/62815` → zero errors
- [ ] `/billing/log` → zero errors
- [ ] `/inbox` → zero errors
- [ ] `/admin` → zero errors
- [ ] `/tools` → zero errors
- [ ] Zero 404s for any `.css`, `.js`, or image assets
- [ ] Zero "Unexpected token '<'" (HTML parsed as JSON)
- [ ] Zero failed fetch calls

**F. Static Assets**
- [ ] Favicon appears in browser tab on every page
- [ ] All CSS files load (check Network tab, no 404)
- [ ] All JS files load (no 404)
- [ ] No mixed-content warnings

**G. Sortable Table Headers**
- [ ] Patient roster: Name, DOB headers → click sorts, click again reverses
- [ ] Billing log: Date, Amount, Code → click sorts
- [ ] Lab track: Date, Type, Status → click sorts
- [ ] Sort arrow indicator toggles direction

**H. API Polling Behavior**
- [ ] While logged in: `/api/notifications-status`, `/api/agent-status`, `/api/setup-status` all return 200 with JSON (not 302 HTML redirect)
- [ ] On login page (data-user-id="0"): polling is suppressed — verify no console errors from polling calls

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
