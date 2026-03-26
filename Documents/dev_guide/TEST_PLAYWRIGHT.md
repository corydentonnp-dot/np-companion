# CareCompanion — Playwright MCP Browser Testing Guide

**Version:** 3.0 — 03-26-26
**Purpose:** Step-by-step guide for AI-driven browser testing via Playwright MCP. **Pass 1** (PW-0 through PW-22): functional audit of every interactive element. **Pass 2** (PW-23 through PW-25): visual/UX audit for aesthetics, hierarchy, balance, and theme resilience. **Pass 3** (PW-26 through PW-41): real-life end-to-end workflow testing with unattended overnight session support.

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
- [x] Height field — type `68` (inches)
- [x] Weight field — type `185` (lbs)
- [x] Calculate button → BMI result appears
- [x] Valid result: should be ~28.1
- [ ] Clear/Reset → fields clear

**URL:** `/calculators/egfr`
- [ ] Age, sex, creatinine, race fields → fill in values
- [ ] Calculate → eGFR result appears

**URL:** `/calculators/chads2`
- [ ] Checkbox items (CHF, HTN, Age≥75, Diabetes, Stroke/TIA) → check several
- [ ] Score updates automatically or on Calculate click

**URL:** `/calculators/wells-dvt`
- [x] Checkbox items → check several
- [x] Calculate → pre-test probability result appears

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

### PW-17: CCM Registry

**URL:** `/ccm/registry`

**Registry table:**
- [ ] Enrolled patients list renders (or empty state message)
- [ ] Status badge per patient (Active / Disenrolled) visible
- [ ] Total enrolled count displayed

**Enrollment:**
- [ ] "Enroll Patient" button → opens enrollment form/modal
  - [ ] MRN field — type `62815`
  - [ ] Enrollment date picker → select today
  - [ ] Qualifying conditions checkboxes → check at least 2
  - [ ] Save → POST `/ccm/enroll`, patient added to registry
  - [ ] Cancel → modal closes, no changes
- [ ] Duplicate enrollment attempt → error message (not 500)

**Per-patient actions:**
- [ ] "Log Time" button → opens time logging form
  - [ ] Minutes field — type `20`
  - [ ] Activity dropdown — select "Care coordination"
  - [ ] Date field — select today
  - [ ] Notes textarea — type brief note
  - [ ] Submit → POST `/ccm/{id}/log-time`, time entry saved
- [ ] "Disenroll" button → confirmation prompt → confirmed → status changes to Disenrolled
- [ ] CCM history expand → shows all logged time entries for patient
- [ ] Monthly billing total visible per patient (sum of logged minutes)

**URL:** `/api/patient/62815/ccm-status`
- [ ] Returns JSON with enrollment status, total minutes this month, qualifying conditions

---

### PW-18: Help Center

**URL:** `/help`

**Help index:**
- [ ] Feature guide cards render (or "no guides available" message)
- [ ] Search field (`#help-search`) — type "billing" → results filter to billing-related guides
- [ ] Clear search → all guides visible
- [ ] Category grouping visible (Getting Started, Clinical, Billing, Admin, etc.)

**URL:** `/help/{feature_id}` (click first available guide)
- [ ] Guide content renders with formatted markdown
- [ ] Table of contents sidebar (if long guide) → anchor links work
- [ ] Back to Help link → navigates to `/help`
- [ ] "Was this helpful?" feedback buttons → POST, feedback recorded

**URL:** `/api/help/search?q=timer`
- [ ] Returns JSON array of matching help items
- [ ] Empty query returns all items (or error message)

---

### PW-19: Campaigns & ROI

**URL:** `/campaigns`

**Campaign list:**
- [ ] Active campaigns render (or empty state)
- [ ] Campaign card shows: name, target gap type, patient count, start/end dates
- [ ] "New Campaign" button → opens creation form
  - [ ] Campaign name field — type "Spring AWV Outreach"
  - [ ] Gap type dropdown — select "AWV"
  - [ ] Target population filter (age range, sex, payer) → set criteria
  - [ ] Start date / End date pickers → set date range
  - [ ] Create → POST, campaign created and appears in list
- [ ] Campaign detail click → opens detail view
  - [ ] Patient list for this campaign visible
  - [ ] Contacted / Scheduled / Completed status per patient
  - [ ] Mark Contacted button (per patient) → POST, status updates
  - [ ] Mark Scheduled button → POST, status updates with appointment date

**URL:** `/admin/billing-roi`
- [ ] ROI dashboard renders (admin-only — non-admin redirected)
- [ ] Revenue impact charts render (not blank canvas)
- [ ] Campaign comparison table visible
- [ ] Date range filter → change dates → data refreshes

---

### PW-20: Admin Extended

**URL:** `/admin/med-catalog`

**Medication catalog:**
- [ ] Drug list table renders with columns: Drug Name, Class, Monitoring Required, Status
- [ ] Search field — type "metformin" → table filters
- [ ] "Add Override" button → opens override form
  - [ ] Drug name field — type drug name
  - [ ] Override type dropdown — select type
  - [ ] Notes textarea — type justification
  - [ ] Save → POST, override appears in list
- [ ] Edit button (per drug) → inline edit activates
- [ ] Toggle monitoring required → POST, flag updates
- [ ] Bulk actions checkbox → select multiple → bulk action dropdown (Enable / Disable / Delete)

**URL:** `/admin/rules-registry`

**Rules table:**
- [ ] Monitoring rules tab → monitoring rules list
- [ ] Care gap rules tab → care gap rules list
- [ ] Each rule row shows: Name, Type, Condition, Enabled toggle, Test button
- [ ] Enabled toggle (per rule) → POST `/api/toggle-monitoring-rule/{id}` or `/api/toggle-caregap-rule/{id}`
- [ ] "Test Rule" button (per rule) → POST `/api/test-monitoring-rule/{id}`, result appears in toast/modal
- [ ] "Add Rule" button → opens rule builder form
  - [ ] Rule name, type, conditions, actions fields → fill all
  - [ ] Save → POST, rule added to list
- [ ] Edit button (per rule) → opens pre-filled form
- [ ] Delete button (per rule) → confirm → rule removed

**URL:** `/admin/benchmarks`
- [ ] Benchmark dashboard renders
- [ ] "Run Benchmarks" button → POST `/admin/benchmarks/run`, progress indicator shown
- [ ] Results table shows: Metric, Current Value, Target, Delta, Status
- [ ] "Select Patients" link → `/admin/benchmarks/patients`
  - [ ] Patient selection criteria form → set filters → submit → patient count updates

**URL:** `/admin/sitemap`
- [ ] Full site map renders with all routes grouped by blueprint
- [ ] Each route shows: URL, method, auth required, role required

---

### PW-21: AI Assistant

**AI Panel (global — available on any page):**

- [ ] AI panel toggle button (in header or taskbar) → panel opens/slides in
- [ ] HIPAA acknowledgment prompt appears on first use
  - [ ] "I Acknowledge" button → POST `/api/ai/acknowledge-hipaa`, panel becomes usable
  - [ ] "Cancel" → panel closes without acknowledging
- [ ] Chat input field — type "What care gaps does patient 62815 have?"
  - [ ] Submit → POST `/api/ai/chat`, response streams into panel
  - [ ] Response renders formatted markdown
- [ ] Follow-up question — type another message → conversation continues
- [ ] "Clear Chat" button → conversation history cleared
- [ ] Panel close button → panel dismissed, conversation preserved for re-open

**URL:** `/api/ai/hipaa-status`
- [ ] Returns JSON with `acknowledged: true/false`, `acknowledged_at` timestamp

**Admin toggle:**
- [ ] Navigate to `/admin/users` → AI toggle per user → disable AI for a user
- [ ] Log in as that user → AI panel should show "AI disabled by administrator" message

---

### PW-22: Telehealth & Communication Log

**URL:** `/patient/62815` (Communications tab or section)

**Communication log:**
- [ ] Communication history list renders (or "no communications" empty state)
- [ ] "Log Communication" button → opens form
  - [ ] Type dropdown — select "Phone Call" / "Video Visit" / "Portal Message" / "Text"
  - [ ] Date/time field → select datetime
  - [ ] Duration minutes field — type `15`
  - [ ] Summary textarea — type brief summary
  - [ ] Follow-up needed checkbox → check
  - [ ] Save → POST `/api/patient/62815/communication-log`, entry appears in list
- [ ] Each entry shows: Type icon, date, duration, summary preview
- [ ] Entry click → expands to show full summary + follow-up status
- [ ] "Mark Follow-up Complete" button (on entries with follow-up) → POST, status updates

**URL:** `/api/patient/62815/communications`
- [ ] Returns JSON array of communication entries sorted by date desc

---

## PASS 2 — Visual & UX Audit

> **Run this AFTER Pass 1 (PW-0 through PW-22) is complete.** Every page must function correctly before evaluating aesthetics. Pass 2 uses screenshots to evaluate layout, hierarchy, balance, and theme resilience.

---

### PW-23: Information Hierarchy Audit

> **Method:** For each page below, screenshot at **1920x1080**. Evaluate: "Can a provider get what they need in < 2 seconds without scrolling?" The **Primary Zone** (top ~600px) must contain the critical data. **Secondary** is one click/scroll away. **Tertiary** is in modals/expandable sections.

**23-A. Dashboard (`/dashboard`)**

| Zone | Must contain |
|------|-------------|
| **Primary** (visible, no scroll) | Today's schedule (patient names + times), active timer status, P1 alert badge count, agent status indicator |
| **Secondary** (sub-panel or 1 scroll) | Billing anomalies, TCM alerts, widget management, scrape controls |
| **Tertiary** (modal/expandable) | Add-to-schedule modal, anomaly detail panel, patient chart links |

- [ ] Screenshot at 1920x1080 — schedule widget fully visible without scrolling
- [ ] P1 badge visible in header area (not buried below fold)
- [ ] Agent status indicator visible without scrolling
- [ ] No critical info hidden behind a collapsed section that defaults to closed
- [ ] Empty state: if no appointments, message visible — not blank white void

**23-B. Patient Chart (`/patient/62815`)**

| Zone | Must contain |
|------|-------------|
| **Primary** | Patient name + MRN + age/sex + allergy badge, active medications (top 5-10), active diagnoses (top 5-10) |
| **Secondary** | Full medication list, full diagnosis list, lab results, vitals, sub-panel quick nav |
| **Tertiary** | ICD-10 lookup modal, edit demographics form, diagnosis copy modal, PiP pop-outs |

- [ ] Screenshot at 1920x1080 — patient header (name, MRN, age, sex, allergies) fully visible
- [ ] Medication section visible without scrolling (at least first 5 items)
- [ ] Diagnosis section visible without scrolling (at least first 5 items)
- [ ] Sub-panel quick-nav links visible for jumping to sections
- [ ] Allergy badge prominently colored (not same weight as regular text)

**23-C. Billing Log (`/billing/log`)**

| Zone | Must contain |
|------|-------------|
| **Primary** | Filter controls (date range + level + status), first 8-10 table rows with Date/MRN/Level/RVU/Status |
| **Secondary** | Anomaly side panel, row detail expansion, rationale textarea |
| **Tertiary** | Export PDF, E&M Calculator link, Monthly Report link |

- [ ] Screenshot at 1920x1080 — filters AND first 8+ data rows visible together
- [ ] Table headers visually distinct (navy background, white text)
- [ ] Anomaly flags (warning badges) visible in table without hovering
- [ ] Action buttons (Detail, Export) visible but not competing with data columns

**23-D. Care Gaps Daily (`/caregap`)**

| Zone | Must contain |
|------|-------------|
| **Primary** | Today's date, patient count with gaps, first 5-8 gap rows (patient name + gap type + status) |
| **Secondary** | Address Now form, documentation textarea, date navigation buttons |
| **Tertiary** | Panel view link, outreach link, CSV export |

- [ ] Screenshot at 1920x1080 — date navigation + first 5 gap rows visible
- [ ] Gap status badges color-coded (addressed=green, open=gold, declined=gray)
- [ ] Action buttons (Address Now, Copy Doc, Decline) visible per row without horizontal scroll

**23-E. Timer (`/timer`)**

| Zone | Must contain |
|------|-------------|
| **Primary** | Active session card (patient, elapsed time, F2F time, recording badge), daily stats (session count, total time) |
| **Secondary** | E&M distribution bar, previous sessions list, billing level dropdown |
| **Tertiary** | Manual entry form, AWV checklist, E&M calculator widget |

- [ ] Screenshot at 1920x1080 — active session card fully visible with live timer
- [ ] Daily stats row (Sessions, Total Time, Avg, F2F) visible without scrolling
- [ ] F2F toggle button prominently placed near active session (not buried)

**23-F. Inbox (`/inbox`)**

| Zone | Must contain |
|------|-------------|
| **Primary** | Unread count badge, first 8-10 message rows (sender, subject, date, priority), tab navigation |
| **Secondary** | Message detail view, hold/resolve buttons, hold reason dropdown |
| **Tertiary** | Digest tab, audit log tab |

- [ ] Screenshot at 1920x1080 — tab bar + first 8 messages visible together
- [ ] Unread count prominently displayed (badge, not just text)
- [ ] Priority indicators visible in message rows (color or icon)

---

### PW-24: Visual Balance & Spacing

> **Method:** Screenshot each page at 1920x1080. Evaluate the rubric below. Each item is a yes/no visual check.

**Card & Layout Balance:**
- [ ] Dashboard: widget cards are evenly spaced — no lopsided whitespace gaps
- [ ] Patient chart: sections (meds, dx, labs) have equal visual weight when populated
- [ ] Billing log: filter row and table occupy balanced proportions (filters ~15%, table ~85%)
- [ ] Care gaps: gap rows are uniform height — no jagged row boundaries
- [ ] Timer: stat blocks are evenly distributed across the grid row

**Typography Hierarchy:**
- [ ] Page titles (H1) are visibly larger than section headers (H2)
- [ ] Section headers are visibly larger than body text
- [ ] Labels (`form-label--sm`) are visibly smaller/lighter than input values
- [ ] Badge text is smaller than surrounding body text
- [ ] Stat values (`stat-value--md`) are the largest text on stat blocks

**Color Consistency:**
- [ ] Info badges use teal consistently across all pages
- [ ] Warning/anomaly badges use gold consistently
- [ ] Danger/error badges use red consistently
- [ ] Success/complete badges use green consistently
- [ ] Primary action buttons are teal on every page
- [ ] Secondary/cancel buttons are outlined gray on every page
- [ ] Sidebar active link highlighted in teal

**Empty States:**
- [ ] Dashboard with no schedule → shows "No appointments scheduled" message (not blank)
- [ ] Patient chart with no medications → shows "No medications on file" (not blank)
- [ ] Inbox with no messages → shows "Inbox is empty" (not blank)
- [ ] Billing log with no entries for date range → shows "No entries found" (not blank)
- [ ] Lab track with no tracked labs → shows "No labs being tracked" (not blank)
- [ ] Care gaps with no gaps today → shows "No care gaps for today" (not blank)

**Button Prominence:**
- [ ] Primary actions (Save, Submit, Create) are teal filled buttons
- [ ] Destructive actions (Delete, Remove) are red filled buttons
- [ ] Secondary actions (Cancel, Back, Clear) are outlined or text-only
- [ ] No page has two equally-weighted primary buttons competing for attention

**Form Layout:**
- [ ] Labels are positioned above inputs (not floating randomly)
- [ ] Required field indicators (asterisk or visual cue) are present where applicable
- [ ] Input focus ring visible when tabbing through form fields (teal glow)
- [ ] Form groups have consistent vertical spacing

---

### PW-25: Theme Resilience Matrix

> **Method:** For each theme, set it via Settings or URL parameter, then screenshot 3 high-density pages: Dashboard, Patient Chart, Billing Log. Verify readability and visual integrity.

**Test matrix (10 themes x 3 pages = 30 screenshots):**

| Theme | Dashboard | Patient Chart | Billing Log |
|-------|-----------|--------------|-------------|
| Light (default) | [ ] | [ ] | [ ] |
| Dark | [ ] | [ ] | [ ] |
| Modern | [ ] | [ ] | [ ] |
| Fancy | [ ] | [ ] | [ ] |
| Retro | [ ] | [ ] | [ ] |
| Minimalist | [ ] | [ ] | [ ] |
| Nature | [ ] | [ ] | [ ] |
| Ocean | [ ] | [ ] | [ ] |
| Sunset | [ ] | [ ] | [ ] |
| Nord | [ ] | [ ] | [ ] |

**Per-screenshot checks:**
- [ ] All text readable (no white-on-white, no black-on-black)
- [ ] Buttons visible and distinguishable from background
- [ ] Table headers distinct from table body
- [ ] Card borders/shadows visible (cards don't blend into page background)
- [ ] Sidebar navigation items readable
- [ ] Badges still color-coded (not all same color)
- [ ] Input fields have visible borders
- [ ] Modal overlays dim the background (not transparent)
- [ ] Charts/graphs: axes and labels readable against chart background
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

## PASS 3 — Real-Life Workflow Testing (Unattended / Overnight)

> **Run this AFTER Pass 1 and Pass 2 are complete.** Pass 1 confirms every button works. Pass 2 confirms the UI looks right. Pass 3 confirms the **entire application works end-to-end** by simulating real clinical workflows — uploading patient data, managing care gaps, running billing, creating on-call handoffs, and more.
>
> **Key difference from Pass 1:** Pass 1 clicks a button and checks if it responds. Pass 3 performs a complete workflow (e.g., upload XML → verify parsed data → address a care gap created from that data → verify billing opportunity generated) and validates the full chain of cause and effect.
>
> **Designed for unattended 8-12 hour overnight sessions.** Every phase snapshots the database before starting and restores after completing. Copilot operates autonomously with strict safety guardrails — no code edits, no destructive operations, no external notifications.

---

### Unattended Session Safety Protocol

These rules are **mandatory** for any Pass 3 execution. They protect the database, prevent real notifications, and ensure the codebase is untouched.

#### Pre-Flight Checklist (run before starting ANY Pass 3 phase)

```
1. Verify Flask is running on port 5000:
   Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue

2. Snapshot the database:
   venv\Scripts\python.exe scripts/db_snapshot.py --action snapshot

3. Seed test data (if not already seeded):
   Navigate to /admin/tools → click "Seed Test Data" button
   Or: POST http://localhost:5000/admin/tools/seed-test-data

4. Verify Pushover notifications are DISABLED:
   Open config.py → confirm PUSHOVER_USER_KEY = "" and PUSHOVER_API_TOKEN = ""
   If keys are set, temporarily blank them for the overnight run.

5. Verify AC_MOCK_MODE:
   Open config.py → confirm AC_MOCK_MODE = True (or False is OK — Pass 3 never triggers AC automation)

6. Verify test patient exists:
   Navigate to /patient/62815 → should show patient chart (upload XML first if empty)
```

#### Per-Phase Snapshot/Restore Cycle

Every PW phase in Pass 3 follows this pattern:

```
[SNAPSHOT] → venv\Scripts\python.exe scripts/db_snapshot.py --action snapshot
[EXECUTE]  → Run all steps in the phase
[VERIFY]   → Check expected state changes
[RESTORE]  → venv\Scripts\python.exe scripts/db_snapshot.py --action restore
```

**Exception:** PW-41 (Cross-Workflow Integration) does NOT restore after completing. It leaves the final state intact so the user can inspect results in the morning.

#### Heartbeat Logging

During unattended execution, write a timestamp to `data/test_heartbeat.txt` every 5 minutes:

```
Set-Content -Path data/test_heartbeat.txt -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss UTC') - Phase PW-XX in progress"
```

The user can check this file remotely (or on return) to verify the session is still running and which phase it reached.

#### Max-Error Abort Rule

- If **5 consecutive test steps fail** within a single phase → **stop that phase**, log the failures, restore DB, and move to the next phase.
- If **3 entire phases fail in a row** → **stop the entire Pass 3 run**, restore DB, and log a summary of what succeeded and what failed.
- Never retry a failed step more than twice (consistent with the 2-strike rule from Pass 1).

#### Hard Safety Rules (Override Everything)

| Rule | Detail |
|------|--------|
| **No code edits** | Never modify `.py`, `.html`, `.css`, `.js`, or config files during Pass 3. Read-only interaction only. |
| **No destructive admin tools** | Never call `purge-reimport-xml`, `sever-all-patients`, or `clear-test-data` during unattended runs. |
| **No raw SQL** | Never execute `DELETE FROM`, `DROP TABLE`, or any raw SQL. All data changes go through Flask routes. |
| **Test data only** | Only interact with MRN `62815` and seeded patients `90001`-`90015`. Never touch real patient data. |
| **No external notifications** | Pushover keys must be empty. If a workflow triggers a notification path, verify it was suppressed (no HTTP call made). |
| **No git operations** | Never commit, push, stash, or branch during Pass 3. The codebase stays frozen. |
| **No file creation** | Never create new files (scripts, fixtures, helpers). Use only existing routes and tools. |

#### Recovery Procedure

If something goes wrong during an unattended run:

```
1. Restore database to last snapshot:
   venv\Scripts\python.exe scripts/db_snapshot.py --action restore

2. List all available snapshots:
   venv\Scripts\python.exe scripts/db_snapshot.py --action list

3. Verify application still works:
   Navigate to localhost:5000/login → login → dashboard loads

4. Check heartbeat file for last successful phase:
   Get-Content data/test_heartbeat.txt
```

#### Morning Review Checklist

After an overnight run, the user should check:

- [ ] `data/test_heartbeat.txt` — what phase was last active?
- [ ] Copilot Chat history — scroll through to see pass/fail per phase
- [ ] `data/backups/snapshots/` — verify snapshots were created (one per phase)
- [ ] Database state — if PW-41 ran, inspect the final state at `/dashboard`, `/billing/log`, `/caregap/62815`
- [ ] Console output — any unhandled errors or crashes?

---

### Overnight Run Orchestration

To start a full Pass 3 unattended run, paste this into Copilot Chat (Agent mode):

> *"Run Pass 3 of TEST_PLAYWRIGHT.md. Execute phases PW-26 through PW-41 sequentially. Before each phase, snapshot the database. After each phase, verify results then restore the database (except PW-41 — leave that state intact). Write a heartbeat timestamp to data/test_heartbeat.txt every 5 minutes. If 5 consecutive steps fail in a phase, skip to the next. If 3 phases fail in a row, stop and log a summary. Never edit any code files. Only interact with test patients (MRN 62815, 90001-90015)."*

For a single phase:

> *"Run PW-27 from Pass 3 of TEST_PLAYWRIGHT.md. Snapshot DB first, execute all steps, verify results, then restore DB."*

---

### PW-26: Login & Auth Lifecycle

> **Goal:** Verify the complete authentication cycle — successful login, failed login, rate limiting, logout, session persistence — as a real user would experience during a clinical day.

**Pre-condition:** DB snapshot taken. Flask running on port 5000.

**26-A. Successful Login**
- [ ] Navigate to `/login`
- [ ] Fill username `CORY`, password `ASDqwe123`
- [ ] Click Sign In → verify redirect to `/dashboard`
- [ ] Verify URL is `/dashboard` (not `/login`)
- [ ] Screenshot dashboard — confirm it rendered with content

**26-B. Session Persistence**
- [ ] From dashboard, navigate to `/patients` → verify page loads (not redirected to login)
- [ ] Navigate to `/timer` → verify page loads
- [ ] Navigate to `/billing/log` → verify page loads
- [ ] Navigate to `/admin` → verify admin panel loads (CORY is admin)

**26-C. Logout**
- [ ] Navigate to `/logout` → verify redirect to `/login`
- [ ] Navigate to `/dashboard` → verify redirect to `/login` (session cleared)

**26-D. Failed Login**
- [ ] Navigate to `/login`
- [ ] Fill username `CORY`, password `wrongpassword`
- [ ] Click Sign In → verify stays on `/login`
- [ ] Verify flash message contains "Invalid" (case-insensitive)

**26-E. Rate Limiting**
- [ ] Submit wrong password 4 more times (total 5 failed attempts)
- [ ] On 5th failure, verify lockout message appears (mentions "locked" or "attempts")
- [ ] Wait 10 seconds, then login with correct password → verify it works (lockout is temporary)

**26-F. Re-login & Verify**
- [ ] Login with `CORY` / `ASDqwe123` → verify dashboard loads
- [ ] Verify user display name appears in header

**Verification:** All 6 sub-steps pass. No 500 errors. Rate limiting engages at 5 attempts and releases.

---

### PW-27: XML Patient Upload & Parse

> **Goal:** Upload a CDA XML clinical summary and verify all 6 clinical sections are parsed and displayed on the patient chart. This is the foundation for many downstream workflows (care gaps, billing, lab tracking).

**Pre-condition:** DB snapshot taken. Demo XML file exists at `Documents/demo_patients/ClinicalSummary_PatientId_62815_20260317_142334.xml`.

**27-A. Upload XML**
- [ ] Login as CORY
- [ ] Navigate to `/patient/62815`
- [ ] Find the "Upload XML" button or file input
- [ ] Upload `Documents/demo_patients/ClinicalSummary_PatientId_62815_20260317_142334.xml`
- [ ] Verify success response (flash message or JSON `{"success": true}`)

**27-B. Verify Medications Populated**
- [ ] Navigate to `/patient/62815`
- [ ] Click the Overview or Medications tab
- [ ] Verify at least 1 medication is listed (not "No medications on file")
- [ ] Screenshot the medications section

**27-C. Verify Diagnoses Populated**
- [ ] On the same patient chart, check the Diagnoses/Problems section
- [ ] Verify at least 1 diagnosis with an ICD-10 code is listed
- [ ] Verify diagnoses are classified as Acute or Chronic

**27-D. Verify Allergies Populated**
- [ ] Check the Allergies section
- [ ] Verify at least 1 allergy is listed (or "NKDA" if the XML has none)

**27-E. Verify Immunizations Populated**
- [ ] Check the Immunizations section
- [ ] Verify at least 1 immunization record is listed

**27-F. Verify Vitals Populated**
- [ ] Check the Vitals section
- [ ] Verify at least 1 set of vitals (BP, HR, weight, etc.) is listed

**27-G. Verify Care Gaps Auto-Evaluated**
- [ ] Navigate to `/caregap/62815`
- [ ] Verify care gap entries exist (the upload triggers `_auto_evaluate_care_gaps()`)
- [ ] Screenshot the care gaps page — should show open gaps based on patient demographics/diagnoses

**Verification:** Patient chart at `/patient/62815` shows data in all 6 clinical sections. Care gaps page shows auto-evaluated gaps. No 500 errors during upload.

**Safety note:** The upload route does `DELETE` existing clinical data before re-importing. This is why DB snapshot is critical before this phase.

---

### PW-28: Inbox Lifecycle

> **Goal:** Verify the inbox hold/resolve workflow. Inbox items are normally created by the agent OCR scanner — for testing, we use seeded data from `seed_test_data`.

**Pre-condition:** DB snapshot taken. Test data seeded via `/admin/tools/seed-test-data`.

**28-A. View Inbox**
- [ ] Login as CORY
- [ ] Navigate to `/inbox`
- [ ] Verify the inbox page loads without errors
- [ ] Check if any items are listed. If empty, note this and skip to verification step.
- [ ] Screenshot the inbox

**28-B. Check API Status**
- [ ] Navigate to `/api/inbox-status` (or fetch via Playwright)
- [ ] Verify JSON response has `total_unresolved`, `critical`, `held` fields
- [ ] Note the counts for comparison after hold/resolve

**28-C. Hold an Item** (if items exist)
- [ ] Click on the first inbox item to expand it
- [ ] Click the "Hold" button
- [ ] Enter a hold reason (e.g., "Awaiting lab results")
- [ ] Confirm → verify item moves to Held Items tab
- [ ] Click the "Held Items" tab → verify the held item appears there

**28-D. Resolve an Item** (if items exist)
- [ ] Navigate back to the Inbox tab
- [ ] Click on an item (different from the held one)
- [ ] Click "Resolve" → verify item disappears from the inbox list
- [ ] Check `/api/inbox-status` → verify `total_unresolved` decreased by 1

**28-E. Verify Digest**
- [ ] Click the "Digest" tab
- [ ] Click the "24h" button → verify digest content loads (or "no items" message)

**Verification:** Hold moves item to held tab. Resolve removes item from inbox. API counts reflect changes. No 500 errors.

---

### PW-29: Timer & Manual Entry

> **Goal:** Create a manual time entry, verify it appears in the timer list and billing log, and annotate it with an E&M level.

**Pre-condition:** DB snapshot taken.

**29-A. Create Manual Entry**
- [ ] Login as CORY
- [ ] Navigate to `/timer`
- [ ] Click "Manual Entry" toggle to reveal the form
- [ ] Fill in:
  - Patient MRN: `62815`
  - Start time: today at 09:00
  - End time: today at 09:30
  - Visit type: `office_visit`
- [ ] Submit → verify new 30-minute session appears in the timer list
- [ ] Screenshot the timer page showing the new entry

**29-B. Annotate E&M Level**
- [ ] Find the new entry in the timer list
- [ ] Select billing level `99214` from the dropdown (or click annotate)
- [ ] Verify the level is saved (persists on page reload)

**29-C. Verify in Billing Log**
- [ ] Navigate to `/billing/log`
- [ ] Verify the entry for MRN 62815 appears with:
  - Correct date (today)
  - Duration approximately 30 minutes
  - Billing level 99214
- [ ] Screenshot the billing log showing the entry

**29-D. Verify Timer Status API**
- [ ] Navigate to (or fetch) `/api/timer-status`
- [ ] Verify JSON response returns without errors

**Verification:** Manual entry created, annotated with 99214, visible in timer list AND billing log. No 500 errors.

---

### PW-30: E&M Calculator

> **Goal:** Verify the E&M billing calculator returns correct code recommendations for known inputs.

**Pre-condition:** DB snapshot taken.

**30-A. Navigate to Calculator**
- [ ] Login as CORY
- [ ] Navigate to `/billing/em-calculator`
- [ ] Verify the form renders with MDM dropdown and minutes input

**30-B. Calculate — Moderate MDM, 35 Minutes**
- [ ] Select MDM complexity: `Moderate`
- [ ] Enter total minutes: `35`
- [ ] Click Calculate
- [ ] Verify result shows:
  - MDM-based code (should be `99214`)
  - Time-based code (35 min → should be `99215`)
  - RVU values for comparison
- [ ] Screenshot the result

**30-C. Calculate — Low MDM, 15 Minutes**
- [ ] Select MDM complexity: `Low`
- [ ] Enter total minutes: `15`
- [ ] Click Calculate
- [ ] Verify result shows `99213` for MDM-based
- [ ] Verify time-based recommendation

**30-D. Calculate — High MDM, 55 Minutes**
- [ ] Select MDM complexity: `High`
- [ ] Enter total minutes: `55`
- [ ] Click Calculate
- [ ] Verify result shows `99215` for MDM-based
- [ ] Verify time-based comparison

**30-E. JSON Endpoint**
- [ ] POST to `/billing/em-calculate-json` with `{"mdm_level": "moderate", "total_minutes": 35}`
- [ ] Verify JSON response contains `suggested_code`, `rvu`, and comparison data

**Verification:** Calculator returns differentiated MDM-based and time-based recommendations. JSON endpoint matches form results. No 500 errors.

---

### PW-31: Care Gap Lifecycle

> **Goal:** Find an open care gap, address it with documentation, verify the status change, then reopen it.

**Pre-condition:** DB snapshot taken. Patient 62815 has care gaps (run PW-27 first, or ensure XML was uploaded previously).

**31-A. View Open Gaps**
- [ ] Login as CORY
- [ ] Navigate to `/caregap/62815`
- [ ] Verify at least one open gap is listed
- [ ] Note the gap name and ID for tracking
- [ ] Screenshot the open gaps list

**31-B. Address a Gap**
- [ ] Click "Address Now" on the first open gap
- [ ] Verify the documentation form appears
- [ ] Enter documentation snippet: `"Discussed with patient. AWV performed today. Screening ordered."`
- [ ] Submit → verify the gap status changes to "Addressed"
- [ ] Verify the gap moves from the Open section to the Addressed section

**31-C. Verify Status Change**
- [ ] Reload `/caregap/62815`
- [ ] Confirm the addressed gap shows with a checkmark or "Addressed" badge
- [ ] Verify the documentation snippet is visible in the gap detail

**31-D. Reopen the Gap**
- [ ] Find the addressed gap
- [ ] Click "Reopen" button (or change status to "open")
- [ ] Verify the gap returns to the Open section
- [ ] Reload page to confirm persistence

**31-E. Decline a Gap**
- [ ] Find a different open gap
- [ ] Click "Decline" → verify status changes to "Declined"
- [ ] Click "N/A" on another gap → verify status changes to "Not Applicable"

**Verification:** Address changes gap to "addressed" with documentation snippet. Reopen reverts to "open". Decline and N/A set correct statuses. All changes persist on reload. No 500 errors.

---

### PW-32: Order Set CRUD

> **Goal:** Create an order set, add items, execute it (mock mode), view history, and clean up.

**Pre-condition:** DB snapshot taken.

**32-A. Create Order Set**
- [ ] Login as CORY
- [ ] Navigate to `/orders`
- [ ] Click "New Order Set" → builder modal opens
- [ ] Enter name: `E2E Test AWV Orders`
- [ ] Select visit type: `AWV`
- [ ] Save → verify the order set appears in the list

**32-B. Add Items**
- [ ] Click Edit on `E2E Test AWV Orders`
- [ ] Add item: `CBC` (Labs tab)
- [ ] Add item: `CMP` (Labs tab)
- [ ] Add item: `TSH` (Labs tab)
- [ ] Verify all 3 items appear in the order set
- [ ] Screenshot the order set with items

**32-C. Execute Order Set**
- [ ] Click Execute on the order set
- [ ] Verify execution confirmation or status indicator appears
- [ ] Note: In mock mode, this creates an `OrderExecution` record without triggering AC automation

**32-D. View History**
- [ ] Navigate to `/orders/<id>/history` (or click History button)
- [ ] Verify at least 1 execution record exists with timestamp
- [ ] Verify items are listed in the execution record

**32-E. Clean Up**
- [ ] Navigate back to `/orders`
- [ ] Click Delete on `E2E Test AWV Orders`
- [ ] Confirm deletion → verify the order set is removed from the list

**Verification:** Order set created with 3 items, executed, history recorded, and deleted. No 500 errors.

---

### PW-33: On-Call Handoff

> **Goal:** Create an on-call note, generate a shareable handoff link, verify it works without authentication, and verify de-identification.

**Pre-condition:** DB snapshot taken.

**33-A. Create On-Call Note**
- [ ] Login as CORY
- [ ] Navigate to `/oncall/new`
- [ ] Fill in:
  - Call time: today at 22:30
  - Patient identifier: `Knee pain patient` (NOT an MRN — HIPAA)
  - Chief complaint: `Acute knee pain after fall`
  - Recommendation: `Ice, elevate, ibuprofen 600mg. Follow up in AM if not improving.`
  - Callback promised: Yes
  - Documentation status: `pending`
- [ ] Submit → verify redirect to `/oncall` or note detail page
- [ ] Verify the note appears in the on-call list

**33-B. Generate Handoff Link**
- [ ] Navigate to `/oncall/handoff`
- [ ] Click "Share Handoff" button
- [ ] Verify a link is generated with a token (URL like `/oncall/handoff/<token>`)
- [ ] Copy the handoff URL

**33-C. Verify Unauthenticated Access**
- [ ] Open the handoff URL in a **new browser context** (no cookies/session)
- [ ] Verify the page loads WITHOUT requiring login
- [ ] Verify the handoff summary is visible with chief complaints and statuses

**33-D. Verify De-Identification**
- [ ] On the handoff page, verify:
  - [ ] No patient MRNs are displayed
  - [ ] No full patient names are displayed
  - [ ] Only clinical shorthand identifiers are shown (e.g., "Knee pain patient")
  - [ ] Chief complaints and recommendations are visible
- [ ] Screenshot the handoff page

**33-E. Update Note Status**
- [ ] Return to authenticated session
- [ ] Navigate to the on-call note
- [ ] Change status from `pending` to `entered`
- [ ] Verify status update persists on reload

**Verification:** Note created, handoff link generated, accessible without auth, de-identified content only, status updates work. No 500 errors. No PHI leakage on handoff page.

---

### PW-34: Lab Tracking & Alerts

> **Goal:** Add lab tracking for a patient, record results at normal/alert/critical levels, and verify threshold detection and trend data.

**Pre-condition:** DB snapshot taken. Patient 62815 exists.

**34-A. Add Lab Tracking**
- [ ] Login as CORY
- [ ] Navigate to `/labtrack`
- [ ] Click "Add Tracking" or "Add Lab"
- [ ] Fill in:
  - MRN: `62815`
  - Lab name: `HbA1c`
  - Interval: `90` days
  - Alert high: `7.0`
  - Critical high: `10.0`
- [ ] Submit → verify tracking entry created
- [ ] Navigate to `/labtrack/62815` → verify HbA1c tracking appears

**34-B. Add Normal Result**
- [ ] Find the HbA1c tracking entry
- [ ] Click "Add Result"
- [ ] Enter value: `6.2`, date: today
- [ ] Submit → verify result appears with normal styling (no alert)

**34-C. Add Alert-Level Result**
- [ ] Add another result: value `8.5`, date: today
- [ ] Verify result appears with alert/warning styling (value exceeds `alert_high` of 7.0)

**34-D. Add Critical Result**
- [ ] Add another result: value `12.0`, date: today
- [ ] Verify flash message contains "CRITICAL VALUE" (value exceeds `critical_high` of 10.0)
- [ ] Screenshot the flash message or alert indicator
- [ ] Note: If Pushover keys are empty (as required by pre-flight), no external notification is sent

**34-E. Verify Trend Data**
- [ ] Navigate to `/labtrack/62815/trend/HbA1c` (or click the trend chart)
- [ ] Verify JSON response contains 3 data points: 6.2, 8.5, 12.0
- [ ] Verify trend direction is "rising"
- [ ] If chart renders, verify all 3 points are plotted

**Verification:** Lab tracking created. Normal, alert, and critical results recorded with appropriate visual indicators. Trend endpoint returns all 3 data points. Critical flash message displayed. No 500 errors.

---

### PW-35: Schedule & Dashboard Integration

> **Goal:** Add a schedule entry and verify it appears on the dashboard, in the schedule API, and in patient search.

**Pre-condition:** DB snapshot taken.

**35-A. Add Schedule Entry**
- [ ] Login as CORY
- [ ] POST to `/api/schedule/add` (via Playwright evaluate or via the dashboard "Add to Schedule" modal):
  ```json
  {
    "patient_name": "TEST, DEMO",
    "patient_mrn": "62815",
    "appointment_time": "09:00",
    "appointment_date": "<today's date YYYY-MM-DD>",
    "visit_type": "Office Visit",
    "duration_minutes": 15
  }
  ```
- [ ] Verify success response

**35-B. Verify Dashboard Shows Appointment**
- [ ] Navigate to `/dashboard`
- [ ] Verify the schedule section shows an appointment for MRN 62815 at 09:00
- [ ] Verify patient name "TEST, DEMO" is visible
- [ ] Screenshot the dashboard schedule section

**35-C. Verify Schedule API**
- [ ] Navigate to (or fetch) `/api/schedule?date=<today>`
- [ ] Verify JSON response includes an entry with MRN `62815`
- [ ] Verify `appointment_time` and `visit_type` match what was submitted

**35-D. Verify Patient Search**
- [ ] Navigate to (or fetch) `/api/patient-search?q=62815`
- [ ] Verify JSON response includes a result for MRN 62815
- [ ] Verify response contains patient name

**35-E. Verify Duplicate Detection**
- [ ] POST the same schedule entry again (same MRN + date)
- [ ] Verify error response about duplicate appointment

**Verification:** Schedule entry created, visible on dashboard, returned by API, patient searchable. Duplicate detection works. No 500 errors.

---

### PW-36: Notification Lifecycle

> **Goal:** Send notifications at different priority levels, verify delivery via API, acknowledge a P1 alert, and verify read-all functionality.

**Pre-condition:** DB snapshot taken. Logged in as admin (CORY).

**36-A. Send P1 Notification**
- [ ] POST to `/admin/send-notification`:
  ```json
  {
    "user_id": 1,
    "message": "E2E Test: Critical lab result for patient",
    "priority": 1
  }
  ```
- [ ] Verify success response

**36-B. Verify P1 Appears**
- [ ] Navigate to (or fetch) `/api/notifications/p1`
- [ ] Verify the notification appears with message "E2E Test: Critical lab result for patient"
- [ ] Verify `priority` is 1

**36-C. Acknowledge P1**
- [ ] POST to `/api/notifications/<id>/acknowledge`
- [ ] Verify success response
- [ ] Fetch `/api/notifications/p1` again → verify the notification is no longer in the P1 list

**36-D. Send P2 Notification**
- [ ] POST to `/admin/send-notification`:
  ```json
  {
    "user_id": 1,
    "message": "E2E Test: New lab results available",
    "priority": 2
  }
  ```
- [ ] Verify success response

**36-E. Read All**
- [ ] POST to `/api/notifications/read-all`
- [ ] Verify success response
- [ ] Fetch `/api/notifications` → verify all notifications have `is_read: true`

**36-F. Verify Counts**
- [ ] Fetch `/api/notifications/p3-count`
- [ ] Verify count reflects current unread state (should be 0 after read-all)

**Verification:** P1 notification sent and received. Acknowledgment removes from P1 list. Read-all marks all read. Counts accurate. No 500 errors.

---

### PW-37: CCM Enrollment & Billing

> **Goal:** Enroll a patient in Chronic Care Management, log time entries to meet the 20-minute billing threshold, verify the billing roster, then disenroll.

**Pre-condition:** DB snapshot taken. Patient 62815 exists.

**37-A. Enroll Patient**
- [ ] Login as CORY
- [ ] Navigate to `/ccm/registry`
- [ ] Click "Enroll" or navigate to enrollment form
- [ ] Fill in:
  - MRN: `62815`
  - Consent method: `verbal`
  - Conditions: HTN (I10), T2DM (E11.9)
- [ ] Submit → verify enrollment created with status `active`

**37-B. Log Time — First Entry**
- [ ] Find the enrollment for MRN 62815
- [ ] Click "Log Time"
- [ ] Enter: 15 minutes, activity type: `care_coordination`, staff: `CORY`, description: `Reviewed medications with pharmacy`
- [ ] Submit → verify response shows `monthly_total: 15`

**37-C. Log Time — Second Entry**
- [ ] Log another entry: 10 minutes, activity type: `care_coordination`, description: `Follow-up call to patient`
- [ ] Submit → verify response shows `monthly_total: 25` (15 + 10 = 25, above 20-min threshold)

**37-D. Verify Billing Roster**
- [ ] Navigate to `/ccm/billing-roster`
- [ ] Verify patient 62815 appears in the billable list (monthly_total >= 20 minutes)
- [ ] Verify estimated revenue shows `$62` (per CCM billing rate)
- [ ] Screenshot the billing roster

**37-E. Verify Monthly Summary**
- [ ] Navigate to `/ccm/<enrollment_id>/monthly-summary`
- [ ] Verify JSON or page shows 2 time entries totaling 25 minutes

**37-F. Disenroll**
- [ ] Click "Disenroll" for MRN 62815
- [ ] Confirm → verify status changes to `disenrolled`
- [ ] Verify patient no longer appears on active enrollment list at `/ccm/registry`

**Verification:** Patient enrolled, 25 minutes logged across 2 entries, billing roster includes patient at $62, monthly summary shows entries, disenrollment works. No 500 errors.

---

### PW-38: Delayed Messages

> **Goal:** Create a delayed message scheduled for the future, verify it appears in the pending list, then cancel it.

**Pre-condition:** DB snapshot taken.

**38-A. Create Delayed Message**
- [ ] Login as CORY
- [ ] Navigate to `/messages/new`
- [ ] Fill in:
  - Recipient identifier: `62815`
  - Message content: `Follow-up reminder: please return for fasting labs`
  - Scheduled send at: tomorrow at 08:00 (future datetime)
- [ ] Submit → verify redirect to `/messages` with success flash

**38-B. Verify Pending**
- [ ] Navigate to `/messages`
- [ ] Verify the new message appears with status `pending`
- [ ] Verify scheduled time shows tomorrow at 08:00
- [ ] Screenshot the messages list

**38-C. Verify API**
- [ ] Fetch `/api/messages/pending`
- [ ] Verify JSON includes the new message with correct scheduled time

**38-D. Cancel Message**
- [ ] Click "Cancel" on the pending message
- [ ] Confirm → verify status changes to `cancelled`
- [ ] Verify the message still shows in the list but with `cancelled` status
- [ ] Fetch `/api/messages/pending` → verify cancelled message is NOT included

**Verification:** Message created with future schedule, appears as pending, cancellation changes status. API reflects changes. No 500 errors.

---

### PW-39: Clinical Tools Suite

> **Goal:** Exercise the main clinical tools — controlled substance tracker, ICD-10 coding helper, clinical calculators, and prior authorization generator.

**Pre-condition:** DB snapshot taken.

**39-A. Controlled Substance Tracker — Add Entry**
- [ ] Navigate to `/cs-tracker`
- [ ] Click "Add Entry" or "Add Prescription"
- [ ] Fill in:
  - Drug name: `Oxycodone 5mg`
  - MRN: `62815`
  - DEA Schedule: `II`
- [ ] Submit → verify entry created

**39-B. CS Tracker — Record Fill**
- [ ] Find the Oxycodone entry
- [ ] Click "Record Fill" (or similar)
- [ ] Enter fill date: today
- [ ] Submit → verify fill recorded, next fill date calculated

**39-C. CS Tracker — PDMP Check**
- [ ] Click "PDMP Check" on the entry
- [ ] Verify PDMP check date updates to today
- [ ] Verify no errors (the check records a date, not an actual PDMP query)

**39-D. ICD-10 Coding Search**
- [ ] Navigate to `/coding`
- [ ] Search for `hypertension` → verify results include I10 and related codes
- [ ] Click on `I10 - Essential (primary) hypertension` → verify code detail appears

**39-E. ICD-10 Add Favorite**
- [ ] Click "Add to Favorites" on the I10 code
- [ ] Verify it appears in the favorites section
- [ ] Reload page → verify favorite persists

**39-F. Calculator — BMI**
- [ ] Navigate to `/calculators/bmi` (or `/calculators` then click BMI)
- [ ] Enter height: `66` inches, weight: `180` lbs
- [ ] Click Compute → verify BMI result is approximately `29.1` (overweight)
- [ ] Verify interpretation text appears (e.g., "Overweight")

**39-G. Prior Authorization — Generate**
- [ ] Navigate to `/pa`
- [ ] Click "Generate New PA" (or similar)
- [ ] Fill in required fields (medication, diagnosis, insurance info)
- [ ] Submit → verify PA letter generated with clinical justification text
- [ ] Screenshot the generated PA

**Verification:** CS entry created with fill and PDMP check. ICD-10 search returns results, favorites saved. BMI calculator returns correct value. PA letter generated. No 500 errors.

---

### PW-40: Admin Operations

> **Goal:** Verify admin panel access, user management, configuration, and test data seeding.

**Pre-condition:** DB snapshot taken. Logged in as CORY (admin role).

**40-A. Admin Panel Access**
- [ ] Navigate to `/admin`
- [ ] Verify admin dashboard loads with system stats
- [ ] Screenshot the admin panel

**40-B. User Management**
- [ ] Navigate to `/admin/users`
- [ ] Verify user list shows at least CORY with admin role
- [ ] Verify role badges are displayed correctly
- [ ] Note: Do NOT change any user roles or passwords during unattended testing

**40-C. System Configuration**
- [ ] Navigate to `/admin/config`
- [ ] Verify configuration form loads with current settings
- [ ] Note: Do NOT save any config changes during unattended testing — view only

**40-D. Care Gap Rules**
- [ ] Navigate to `/admin/caregap-rules`
- [ ] Verify rules list loads with at least 5 rules
- [ ] Verify each rule shows: name, criteria, age range, frequency

**40-E. Admin Tools Page**
- [ ] Navigate to `/admin/tools`
- [ ] Verify the tools page loads with seed/clear buttons
- [ ] Click "Seed Test Data" → verify success message
- [ ] Navigate to `/patients` → verify seeded patients appear (MRN 90001-90015 range)

**40-F. Verify Seeded Data**
- [ ] Navigate to `/patient/90001` → verify chart loads with clinical data
- [ ] Navigate to `/patient/90005` → verify chart loads
- [ ] Navigate to `/caregap` → verify care gaps exist for seeded patients

**Verification:** Admin panel, user list, config, and tools pages all load. Test data seeded and visible across patient roster, charts, and care gaps. No 500 errors. No config changes persisted.

---

### PW-41: Cross-Workflow Integration (Full Clinical Day Simulation)

> **Goal:** Simulate a complete clinical day workflow, chaining multiple features together to verify they interact correctly. This is the integration test — each step depends on the previous step's state.
>
> **IMPORTANT:** This phase does NOT restore the database after completion. The final state is left intact for morning inspection.

**Pre-condition:** DB snapshot taken (for safety, in case manual restore is needed). Test data seeded.

**41-A. Morning Login**
- [ ] Navigate to `/login`
- [ ] Login as `CORY` / `ASDqwe123`
- [ ] Verify redirect to `/dashboard`
- [ ] Screenshot: "Morning dashboard state"

**41-B. Review Schedule**
- [ ] On the dashboard, check today's schedule
- [ ] Add patient 62815 to today's schedule at 10:00 (Office Visit) if not present
- [ ] Verify the appointment appears

**41-C. Open Patient Chart**
- [ ] Click on patient 62815 in the schedule (or navigate to `/patient/62815`)
- [ ] Verify chart loads with clinical data
- [ ] Screenshot: "Patient chart at start of visit"

**41-D. Review Care Gaps**
- [ ] Navigate to `/caregap/62815`
- [ ] Review open care gaps
- [ ] Address one gap with documentation: `"Discussed during office visit. AWV components completed."`
- [ ] Verify gap status changes to "addressed"

**41-E. Create Timer Entry**
- [ ] Navigate to `/timer`
- [ ] Create manual entry: MRN 62815, 10:00-10:40 (40 min), office_visit
- [ ] Verify entry appears in timer list

**41-F. Annotate Billing**
- [ ] Annotate the timer entry with billing level `99215` (40 min + moderate MDM)
- [ ] Verify annotation saved

**41-G. Check Billing Log**
- [ ] Navigate to `/billing/log`
- [ ] Verify the entry for MRN 62815 today shows:
  - Duration: ~40 min
  - Level: 99215
- [ ] Screenshot: "Billing log after annotation"

**41-H. Create On-Call Note**
- [ ] Navigate to `/oncall/new`
- [ ] Create note: "Follow-up call patient" / "Check lab results from this morning" / Callback: Yes
- [ ] Verify note created

**41-I. Generate Handoff**
- [ ] Navigate to `/oncall/handoff`
- [ ] Generate handoff link
- [ ] Verify link is generated

**41-J. Logout**
- [ ] Navigate to `/logout`
- [ ] Verify redirect to login page
- [ ] Screenshot: "End of clinical day"

**41-K. Final State Verification (leave DB as-is)**
- [ ] Re-login as CORY
- [ ] Navigate to `/dashboard` → verify schedule shows today's patients
- [ ] Navigate to `/billing/log` → verify today's billing entry exists
- [ ] Navigate to `/caregap/62815` → verify addressed gap persists
- [ ] Navigate to `/oncall` → verify on-call note exists
- [ ] Screenshot: "Final verification — all workflow artifacts present"

**Verification:** The full chain — login → schedule → patient → care gap → timer → billing → on-call → handoff → logout — completes without errors. All state changes persist across the workflow. DB is left intact for user inspection.

---

## PART 4 — Phase Completion Tracker

Mark each phase ✅ as it is completed and verified.

| Phase | Pass | Focus Area | Status | Date Completed |
|-------|------|------------|--------|----------------|
| PW-0  | 1 | Global Navigation | ⬜ Not Started | — |
| PW-1  | 1 | Login & Account Flows | ⬜ Not Started | — |
| PW-2  | 1 | Dashboard | ⬜ Not Started | — |
| PW-3  | 1 | Patient Roster & Chart | ⬜ Not Started | — |
| PW-4  | 1 | Inbox | ⬜ Not Started | — |
| PW-5  | 1 | Timer | ⬜ Not Started | — |
| PW-6  | 1 | Billing Suite | ⬜ Not Started | — |
| PW-7  | 1 | Care Gaps | ⬜ Not Started | — |
| PW-8  | 1 | Orders & Order Sets | ⬜ Not Started | — |
| PW-9  | 1 | Lab Track | ⬜ Not Started | — |
| PW-10 | 1 | On-Call | ⬜ Not Started | — |
| PW-11 | 1 | Clinical Tools | ⬜ Not Started | — |
| PW-12 | 1 | Calculators | ⬜ Not Started | — |
| PW-13 | 1 | Admin Panel | ⬜ Not Started | — |
| PW-14 | 1 | Monitoring & Messaging | ⬜ Not Started | — |
| PW-15 | 1 | Metrics & Benchmarks | ⬜ Not Started | — |
| PW-16 | 1 | Cross-Cutting Checks | ⬜ Not Started | — |
| PW-17 | 1 | CCM Registry | ⬜ Not Started | — |
| PW-18 | 1 | Help Center | ⬜ Not Started | — |
| PW-19 | 1 | Campaigns & ROI | ⬜ Not Started | — |
| PW-20 | 1 | Admin Extended (Med Catalog, Rules, Benchmarks) | ⬜ Not Started | — |
| PW-21 | 1 | AI Assistant | ⬜ Not Started | — |
| PW-22 | 1 | Telehealth & Communication Log | ⬜ Not Started | — |
| PW-23 | 2 | Information Hierarchy Audit | ⬜ Not Started | — |
| PW-24 | 2 | Visual Balance & Spacing | ⬜ Not Started | — |
| PW-25 | 2 | Theme Resilience Matrix | ⬜ Not Started | — |
| PW-26 | 3 | Login & Auth Lifecycle | ⬜ Not Started | — |
| PW-27 | 3 | XML Patient Upload & Parse | ⬜ Not Started | — |
| PW-28 | 3 | Inbox Lifecycle | ⬜ Not Started | — |
| PW-29 | 3 | Timer & Manual Entry | ⬜ Not Started | — |
| PW-30 | 3 | E&M Calculator | ⬜ Not Started | — |
| PW-31 | 3 | Care Gap Lifecycle | ⬜ Not Started | — |
| PW-32 | 3 | Order Set CRUD | ⬜ Not Started | — |
| PW-33 | 3 | On-Call Handoff | ⬜ Not Started | — |
| PW-34 | 3 | Lab Tracking & Alerts | ⬜ Not Started | — |
| PW-35 | 3 | Schedule & Dashboard Integration | ⬜ Not Started | — |
| PW-36 | 3 | Notification Lifecycle | ⬜ Not Started | — |
| PW-37 | 3 | CCM Enrollment & Billing | ⬜ Not Started | — |
| PW-38 | 3 | Delayed Messages | ⬜ Not Started | — |
| PW-39 | 3 | Clinical Tools Suite | ⬜ Not Started | — |
| PW-40 | 3 | Admin Operations | ⬜ Not Started | — |
| PW-41 | 3 | Cross-Workflow Integration | ⬜ Not Started | — |

**Pass 1** = Functional (click every button, verify every route)
**Pass 2** = Visual/UX (screenshot-based aesthetic evaluation)
**Pass 3** = Real-Life Workflow (end-to-end scenario simulation, unattended overnight support)

**Progress:** 0/42 phases complete

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
| Hierarchy check | *"Screenshot the dashboard at 1920x1080. Is the schedule visible without scrolling? Is the P1 badge visible?"* |
| Theme test | *"Switch to the Ocean theme, then screenshot the dashboard, patient chart, and billing log"* |
| Balance check | *"Screenshot the patient chart. Are medication and diagnosis sections evenly weighted? Any blank voids?"* |
| Upload XML & verify | *"Run PW-27: Upload the demo XML for MRN 62815, then verify all 6 clinical sections are populated on the patient chart"* |
| Workflow test | *"Run PW-31: Navigate to care gaps for 62815, address one gap with documentation, verify status changes, then reopen it"* |
| Full clinical day | *"Run PW-41: Simulate a full clinical day — login, schedule, patient chart, care gap, timer, billing, on-call, logout"* |
| Overnight run | *"Run Pass 3 phases PW-26 through PW-41 sequentially. Snapshot DB before each, restore after each except PW-41."* |
| Single workflow | *"Run PW-34 from Pass 3: Add HbA1c tracking for 62815, record normal/alert/critical results, verify trend data"* |

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
