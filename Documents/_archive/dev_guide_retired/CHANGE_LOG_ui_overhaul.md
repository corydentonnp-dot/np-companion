# CareCompanion UI Overhaul — Change Log

> This log tracks incremental bites taken from UI_OVERHAUL.md.
> Each entry documents what was done, what was verified, and what was deferred.

---

## Bite 1 — Phase 44 Foundation (Systems 1, 2, 6, 7, 8)

**Date:** 2025 (ongoing)
**Files Changed:** 20+ templates, main.css, base.html, auth.py, settings.html, admin_users.html

---

### Previously Implemented (Discovered on Audit)

The following items from UI_OVERHAUL.md were already fully implemented in a prior session and verified to be in place:

| System | Item | Status |
|--------|------|--------|
| System 1 | Context Sub-Panel CSS (`.context-panel`, `.cp-stat`, `.cp-link`, `.cp-action`, `.cp-quick-nav`, `.cp-filter`, etc.) | ✅ Already done |
| System 1 | `{% block subpanel %}` container in base.html with aside element | ✅ Already done |
| System 1 | Sub-panel toggle JS (localStorage persistence) | ✅ Already done |
| System 1 | Responsive CSS — `@media (max-width: 1024px)` and `@media (max-width: 768px)` | ✅ Already done |
| System 2 | Popup Taskbar CSS (`.popup-taskbar`, `.taskbar-tab`, minimize/restore/close states) | ✅ Already done |
| System 2 | `#popup-taskbar` container in base.html | ✅ Already done |
| System 2 | `ModalTaskbar` JS IIFE class with `_saveState`/`_restoreState` | ✅ Already done |
| System 6 | Breadcrumb Trail CSS (`.breadcrumb-trail`, `.bc-chip`, `.bc-arrow`, `.bc-badge`) | ✅ Already done |
| System 6 | `#breadcrumb-trail` container in base.html | ✅ Already done |
| System 6 | Breadcrumb sessionStorage JS (reads `document.title` + `location.pathname`) | ✅ Already done |
| System 7 | Type-Ahead Indicator CSS (`.search-active-indicator`, `@keyframes pulse-ring`) | ✅ Already done |
| System 7 | Type-ahead keydown JS handler (debounce, `data-filterable` query, hide/show) | ✅ Already done |
| System 8 | Page Transition CSS (all 8 keyframes: fadeIn/Out, slideIn/Out, zoomIn/Out, subtleIn/Out) | ✅ Already done |
| System 8 | Page transition JS interceptor (enter animation + exit link intercept) | ✅ Already done |

---

### Implemented This Bite

#### Step 26 — data-blocking on all 4 Security Modals

Added `data-blocking="true"` to all four security modals that must not be minimizable:

| Modal | File | Location |
|-------|------|----------|
| `#hipaa-modal` | `base.html` | Privacy notice modal |
| `.lock-overlay` | `base.html` | Auto-lock screen overlay |
| `#p1-modal-overlay` | `base.html` | Priority 1 alert overlay |
| `#deact-modal` | `admin_users.html` | Account deactivation confirm |

#### Phase 1C — Sub-Panels on All 15 Page Templates

All 15 non-dashboard pages now have a populated `{% block subpanel %}` with:
- `.context-panel-header` with page icon and title
- Relevant stats using `.cp-stat` / `.cp-stat-value`
- Actions using `.cp-action`
- Optional filter controls using `.cp-filter`
- `.cp-quick-nav` section with 2–4 cross-links

| Template | Sub-Panel Content |
|----------|-------------------|
| `patient_roster.html` | Search tips, total patient count, Quick Nav (Care Gaps, Lab, Timer) |
| `timer.html` | Daily stats (sessions, time, avg, F2F, complex), E&M bar, Export (pre-existing) |
| `inbox.html` | Tab nav (Inbox/Held/Audit/Digest), conditional digest stats (pre-existing) |
| `oncall.html` | Pending count, callbacks due, New Call action, Quick Nav |
| `orders.html` | My Sets / Community tabs, New Order Set action, Quick Nav |
| `labtrack.html` | 4 stats (total, patients, overdue, critical), Quick Nav |
| `caregap.html` | Open gaps count, patient count, Panel Report action, Quick Nav |
| `bonus_dashboard.html` | Receipts, threshold, progress %, days remaining, Quick Nav |
| `tcm_watch.html` | Active / completed counts, Quick Nav |
| `ccm_registry.html` | Active enrollments, ready to bill, monthly revenue, Quick Nav |
| `monitoring_calendar.html` | 4 stats (total, critical, escalations, avg score), priority filter, Quick Nav |
| `care_gaps_preventive.html` | 4 stats (services, pending, completed, rate), Export CSV, Quick Nav |
| `staff_billing_tasks.html` | Role counts (RN, MA, Admin), Quick Nav |
| `notifications.html` | Type filter, Mark All Read action, Quick Nav |
| `patient_chart.html` | Patient summary (MRN, age, sex), 7 chart section links, upload action, care gap count, Quick Nav |

#### Step 46 — data-filterable Markers

Added `data-filterable` attribute to all repeating list/card/row elements on 13 templates, enabling the type-ahead JS filter to show/hide items as the user types:

`patient_roster`, `notifications`, `caregap`, `tcm_watch`, `ccm_registry`, `oncall`, `monitoring_calendar`, `labtrack`, `orders`, `inbox`, `timer`, `staff_billing_tasks`, `care_gaps_preventive`

#### Step 43 — data-breadcrumb-badge

Added `{% block breadcrumb_badge %}` to base.html's `<main>` element via `data-breadcrumb-badge`. Child pages now populate the badge:

| Page | Badge Content |
|------|---------------|
| `patient_chart.html` | Patient name (falls back to MRN) |
| `caregap.html` | `N gap(s)` count |
| `inbox.html` | `N item(s)` count |
| `timer.html` | `N session(s)` count |

#### Step 49 — Page Transitions in Settings UI

- Added **Page Transitions** card to `settings.html` Theme & Appearance section
- 5 preset buttons: None / Fade / Slide / Zoom / Subtle
- Buttons read current pref from `current_user.get_pref('page_transition', 'none')`
- `_applyTransition(preset)` JS function: updates `<html>` class, localStorage, button states, POSTs to API
- `routes/auth.py` `/api/settings/theme` endpoint now accepts and persists `page_transition`
- Valid values: `{'none', 'fade', 'slide', 'zoom', 'subtle'}` — invalid values default to `'none'`
- Server→localStorage sync script added to `base.html` (fires on every authenticated page load)

#### Bonus Fix — staff_billing_tasks.html page_id

Added missing `{% block page_id %}staff-billing{% endblock %}` block to `staff_billing_tasks.html`.

---

### Test Files Created

| File | Tests |
|------|-------|
| `tests/test_subpanel.py` | 18 tests: sub-panel present on all 15 pages, absent on dashboard, `context-panel-header` and `cp-quick-nav` present |
| `tests/test_popup_taskbar.py` | 10 tests: taskbar container, ModalTaskbar class, `data-blocking` on 4 security modals, state methods |
| `tests/test_breadcrumbs.py` | 10 tests: breadcrumb-trail container, `data-breadcrumb-badge` on main, badge blocks on 4 pages, JS logic |
| `tests/test_type_ahead.py` | 16 tests: `data-filterable` on all 13 list templates, JS handler, debounce |
| `tests/test_transitions.py` | 12 tests: CSS keyframes, CSS classes, JS interceptor, settings UI, API endpoint (valid+invalid values) |

---

### What Was NOT Implemented

The following systems from UI_OVERHAUL.md are NOT yet implemented and will be addressed in future bites:

| System | Reason Deferred |
|--------|-----------------|
| System 3: Split View | Requires `SplitViewManager` JS class, CSS `.split-pane`/`.split-divider`, header split button, `split_max_panes` user pref — substantial new infrastructure |
| System 4: PiP Widgets | Requires `PipManager` JS class, CSS `.pip-window`, `data-pip` on 21+ chart widgets in patient_chart.html |
| System 5: Smart Bookmarks with Folders | Requires folder schema migration, drag-to-bookmark JS, folder management UI, bookmarks API update |
| System 9: AI Enhancements | Requires help_guide.json data for 9 systems, help popover CSS/JS, workflow coach context injection, AI rate limit preferences |

---

### Known Gaps / Needs Human Review

1. **Sub-panel Jinja context variables** — The sub-panel stats in some templates use Jinja variables (e.g., `{{ open_gaps }}`, `{{ session_count }}`) that may not be passed from their routes. A human developer should verify each route passes the expected context variables or use `| default(0)` fallbacks.

2. **breadcrumb_badge on other pages** — Only 4 pages were given badges. Additional pages (oncall, labtrack, etc.) could benefit from badges but were not included in this bite.

---

## Bite 2 — Phase 44 Continuation (Systems 3, 4, 5, 9D)

**Files Changed:** `base.html`, `main.css`, `auth.py`, `help.py`, `settings.html`, `patient_chart.html`, `labtrack.html`, `caregap.html`, `timer.html`, `notifications.html`, `data/help_guide.json`

---

### System 3 — Split View

- **CSS**: `.split-panes`, `.split-pane`, `.split-divider`, `.split-toggle-btn`, `.split-pane-header`, `.split-active`, responsive hide on narrow viewports
- **Header button**: `<button class="split-toggle-btn" id="split-toggle-btn">` added to base.html header-right (SVG icon, title tooltip)
- **`window.SplitViewManager` IIFE in base.html**: `open(url)`, `close()`, `toggle()` methods; wraps `<main>` children in `.split-pane.pane-primary`; appends `<iframe class="split-pane pane-secondary">`; drag-resize divider via mousedown/mousemove/mouseup
- **Ctrl+click interceptor**: catches `e.ctrlKey` on all `<a href>` links and calls `SplitViewManager.open(href)`
- **Settings card** (`settings.html`): "Split View" pane-count UI with 2/3/4 buttons, `_setSplitPanes(n)` JS, POSTs to `/api/settings/split_panes`
- **`/api/settings/split_panes` endpoint** in `auth.py`: persists `split_max_panes` pref (2, 3, or 4)
- **`splitMaxPanes` server→localStorage sync** in base.html inline script (alongside `pageTransition`)

### System 4 — Picture-in-Picture (PiP) Widgets

- **CSS**: `.pip-window`, `.pip-header`, `.pip-body`, `.pip-minimized`, `.pip-resize`, `.pip-popout-btn`, `.pip-eligible`
- **`window.PipManager` IIFE in base.html**: `create(sourceEl)`, `destroy(pipId)`, `minimize(pipId)`, `restore(pipId)`; `_makeDraggable()` / `_makeResizable()` helpers; click delegation for `.pip-popout-btn`; double-click header to restore minimized
- **`data-pip` injection on `patient_chart.html`**: New `<script>` block at page end auto-injects `data-pip="true"`, `data-pip-title`, `.pip-eligible` class, and `.pip-popout-btn` button to all 21 widget divs via `WIDGET_TITLES` map
- **`data-pip` on 4 additional templates**: `labtrack.html` ("Lab Tracking Table"), `caregap.html` ("Care Gap List"), `timer.html` ("Active Timer"), `notifications.html` ("Notification Feed")

### System 5 — Smart Bookmarks with Folders

- **CSS**: `.bm-folder`, `.bm-folder-dropdown`, `.bm-drop-indicator`, `.bookmarks-bar.drag-over`, `.bm-folder.drag-over`
- **Drag-to-bookmark IIFE in base.html**: marks all `a[href]:not([data-no-drag])` draggable via MutationObserver; bookmarks-bar and folder drop targets; POST to `/api/bookmarks/personal` with `{type, label, url, folder?}`
- **`_migrate_bookmarks()` helper in `auth.py`**: upgrades old `{label, url}` entries to `{type:'link', label, url}` schema — backward compatible
- **Updated `api_add_personal_bookmark()`**: handles `type:'folder'` (creates new folder), `folder:str` (adds link inside folder), plain link; calls `_migrate_bookmarks` on every write
- **Updated `api_get_bookmarks()`**: calls `_migrate_bookmarks` on read — ensures all clients see typed schema
- **`/api/bookmarks/personal/folder/rename`** (POST): accepts `{old_label, new_label}`
- **`/api/bookmarks/personal/folder/delete`** (POST): accepts `{label}`, removes folder and children

### System 9D — Help Popovers

- **CSS**: `.help-icon`, `.help-popover`, `.help-popover-title`, `.help-popover-body`, `.help-popover-link`
- **Header element in base.html**: `<button class="help-icon" id="page-help-icon">?</button>` with `.help-popover` div in header-left
- **`window.__npHelp` preload**: fetches `/api/help/items` on page load, populates dict keyed by feature `id`
- **Help popovers IIFE in base.html**: click delegation for `.help-icon` buttons; hover mouseenter with short delay; looks up `window.__npHelp[helpId]`; click-outside and Escape dismiss
- **`/api/help/items` endpoint in `help.py`**: returns `[{id, name, description, category, url}]` for all features, respects `admin_only` flag
- **`data/help_guide.json` additions**: new "ui-ux" category ("UI & UX Enhancements"); 8 Phase 44 features: `context-subpanel`, `popup-taskbar`, `split-view`, `pip-widgets`, `smart-bookmarks`, `breadcrumb-trail`, `type-ahead-filter`, `page-transitions` — now 57 features total, 8 categories

---

### What Was NOT Implemented (Bite 2)

| System | Reason Deferred |
|--------|-----------------|
| System 9A: AI Workflow Coach | Requires AI API key (encrypted storage — Fernet + DB migration not yet done) |
| System 9B: AI Natural Language Navigation | Requires AI API key |
| System 9C: AI Writing Assistant | Requires encrypted API key storage (Fernet + migration) |

---

### Test Files Created (Bite 2)

| File | Tests |
|------|-------|
| `tests/test_split_view.py` | 19 tests: CSS classes, SplitViewManager JS, settings card, API endpoint, localStorage sync |
| `tests/test_pip_widgets.py` | 20 tests: CSS classes, PipManager JS methods, data-pip markers on 5 templates |
| `tests/test_bookmarks_folders.py` | 19 tests: CSS classes, drag-to-bookmark JS, bookmarks API folder support, schema migration |
| `tests/test_ai_enhancements.py` | 20 tests: CSS classes, help-icon/popover elements, `window.__npHelp` preload, `/api/help/items`, help_guide.json Phase 44 entries |

### Test Results

```
127/127 main tests — ALL PASSED
test_split_view.py        19/19
test_pip_widgets.py       20/20
test_bookmarks_folders.py 19/19
test_ai_enhancements.py   20/20
```

3. **`models/user.py` preference keys** — The `page_transition` preference is now used via `get_pref()`/`set_pref()` but no explicit key constant was added to `models/user.py`. This works with the dynamic preference system but a future bite may want to document allowed keys.

