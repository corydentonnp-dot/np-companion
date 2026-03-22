# NP Companion — UI Overhaul Plan (Phase 44)

> **Version**: 1.0 — March 21, 2026
> **Scope**: 9 interconnected UX systems transforming NP Companion from a clinical tool into a desktop-class application
> **Prerequisite**: All Phases 0-43 complete (360 tests passing)

---

## Executive Summary

Nine coordinated UI/UX systems that work together to make NP Companion feel like a native desktop application rather than a web page. Every feature builds on existing patterns (CSS variables, grid layout, modal system, AI panel, bookmarks bar, free-form widgets, command palette) while introducing interactions no competing EHR companion tool offers.

| # | System | One-Line Description |
|---|--------|---------------------|
| 1 | Context Sub-Panel | Collapsible page-specific nav/filter/stat panel; sidebar collapses to icon rail |
| 2 | Popup Taskbar | Modals minimize to a bottom taskbar instead of closing; state preserved |
| 3 | Split View | Side-by-side page viewing within one window |
| 4 | Picture-in-Picture Widgets | Pop out any widget into a floating window that persists across pages |
| 5 | Smart Bookmarks | Chrome-style drag-to-bookmark with folders |
| 6 | Breadcrumb Trail | Visual history of last 5 pages with contextual badges |
| 7 | Type-Ahead Filtering | Start typing on any list page to instantly filter — no search box click needed |
| 8 | Page Transitions | User-selectable animated transitions (None/Fade/Slide/Zoom/Subtle) |
| 9 | AI Enhancements | Workflow coach, natural language nav, writing assistant, contextual help popovers |

### Design Principles

- **3-Click Rule**: Any page reachable from any other page in max 3 clicks (sidebar + sub-panel Quick Nav + action)
- **No Lost Work**: Click outside a popup → minimizes to taskbar, all data preserved. Never discard user input.
- **Progressive Disclosure**: Sub-panel declutters pages; PiP/split-view let power users expand their workspace.
- **Session Memory**: Minimized modals, PiP widgets, split state, bookmarks — all persist for app session. Transition preference + bookmark folders + split pane count persist across sessions.
- **HIPAA Compliant AI**: AI features use only app metadata (page types, feature names, counts, categories) — never patient names, MRNs, or PHI. Users provide their own API key unless office admin supplies one.

---

## System 1 — Context Sub-Panel

### Design
- **What**: Collapsible panel (220px) at the left edge of the content area on every sidebar-linked page except Dashboard
- **Sidebar behavior**: Collapses to icon-only rail (60px) when sub-panel is present
- **Dashboard exception**: Full 240px sidebar with labels, no sub-panel
- **Default state**: Open; user can collapse via chevron toggle
- **State persistence**: Per-page via `localStorage['subpanel:{page_id}']`
- **Quick Nav section**: Every sub-panel includes 3-5 cross-links to related pages at the bottom (enforces 3-click rule)

### Implementation Steps

#### Phase 1A — CSS Foundation

1. **`.has-subpanel` grid variant** in `static/css/main.css`
   - Grid: `var(--sidebar-collapsed) auto 1fr` → areas: `sidebar subpanel main`
   - Sub-panel: 220px, `var(--bg-card)` bg, `1px solid var(--border-color)` right border
   - `.subpanel-collapsed`: width 0, overflow hidden, CSS transition 200ms
   - Icon-only rail: reuse existing tablet `@media` styles but scoped to `.has-subpanel`

2. **`.context-panel` component CSS**
   - `.context-panel`: width, bg, border, padding 12px, overflow-y auto, transition width
   - `.context-panel-header`: title + collapse toggle chevron
   - `.context-panel-section`: grouped items with label + content
   - `.cp-link` / `.cp-stat` / `.cp-filter` / `.cp-action`: nav links, stat badges, filter controls, action buttons
   - `.cp-quick-nav`: bottom section with cross-page links, subtle separator above

3. **Responsive rules**
   - Below 768px: sub-panel hidden entirely, content falls back to inline
   - 768-1024: sub-panel renders alongside icon-only sidebar

#### Phase 1B — Base Template

4. **`{% block subpanel %}` in `templates/base.html`**
   - `<aside class="context-panel" id="context-panel">{% block subpanel %}{% endblock %}</aside>` between sidebar and `.content-area`

5. **Sub-panel toggle JS** in `base.html`
   - Detect content → add `.has-subpanel` to `.app-layout`
   - Read `localStorage['subpanel:' + pageId]` → apply `.subpanel-collapsed` if stored
   - Toggle button saves state, toggles class
   - Dashboard: never add `.has-subpanel`

6. **Verify `page_id`** in every template (`{% block page_id %}`)

#### Phase 1C — 15 Page Sub-Panels (parallel, independent after 1B)

Each page gets `{% block subpanel %}` with relocated filters/stats/actions + Quick Nav cross-links:

| Step | Page | Template | Sub-Panel Content | Quick Nav |
|------|------|----------|------------------|-----------|
| 7 | My Patients | `patient_roster.html` | Search, Claimed/Unclaimed filter, care gap filter, stats, Upload XML | Care Gaps, Lab Track, Timer |
| 8 | Timer | `timer.html` | 5-stat card, E&M distribution, Export CSV | Billing Tasks, Bonus, Patients |
| 9 | Inbox | `inbox.html` | Tab nav (Inbox/Held/Audit/Digest), digest period, summary stats | Notifications, On-Call, Orders |
| 10 | On-Call | `oncall.html` | New Call/Handoff buttons, status filters, callback count | Inbox, Notifications, Patients |
| 11 | Orders | `orders.html` | Tab nav (My Sets/Community), actions, search | Lab Track, Patients, Monitoring |
| 12 | Lab Track | `labtrack.html` | Stat cards, add tracking/panel, status filter | Care Gaps, Monitoring, Patients |
| 13 | Care Gaps | `caregap.html` | Date nav (←Today→), gap count, type filter, print handout | Preventive, Lab Track, Patients |
| 14 | Bonus Tracker | `bonus_dashboard.html` | Quarter label, $ progress, Calibrate/History | Timer, Billing Tasks, CCM |
| 15 | TCM Watch | `tcm_watch.html` | Quick-add form, status summary, status filter | CCM, Patients, Billing Tasks |
| 16 | CCM Registry | `ccm_registry.html` | Stats cards, enroll link, status filter | TCM, Bonus, Patients |
| 17 | Monitoring | `monitoring_calendar.html` | Priority/trigger/source filters, stats, REMS alerts | Lab Track, Care Gaps, Orders |
| 18 | Preventive Gaps | `care_gaps_preventive.html` | Stats, compliance filter, Export CSV | Care Gaps, Lab Track, Monitoring |
| 19 | Billing Tasks | `staff_billing_tasks.html` | Role tabs, timing toggles, task counts | Timer, Bonus, Orders |
| 20 | Notifications | `notifications.html` | Type filter, Mark All Read, unread count | Inbox, On-Call, Patients |
| 21 | Patient Chart | `patient_chart.html` | 7-tab vertical nav, patient summary (name/MRN/DOB/age), quick actions (Refresh/Generate Note/Upload XML), care gap alerts, overdue labs, risk scores, specialist list, Edit Mode toggle | Patients, Care Gaps, Lab Track |

---

## System 2 — Popup Taskbar

### Design
- **What**: All non-blocking modals can be minimized to a shared bottom bar (same row as AI panel) instead of being closed/discarded
- **Taskbar layout**: Tabs left-aligned, AI panel far-right. Tabs are side-by-side in minimized order, equal-width flex sizing
- **Tab labels**: "Patient Name — Modal Title" if patient context available, otherwise just modal title
- **Click-outside behavior** (non-blocking modals):
  - Click a **link** → save state → minimize to taskbar → follow the link
  - Click **non-link area** → save state → minimize to taskbar → focus clicked area
- **State preservation**: All form inputs, selections, scroll positions frozen on minimize. Persists for entire app session until user explicitly saves, closes, or advances through the modal workflow
- **Restore**: Click taskbar tab → modal reopens with all data intact
- **Close**: Click X on tab → discard state, remove tab, fully close modal
- **Blocking exceptions** (cannot minimize, require explicit action): `#hipaa-modal`, `#lock-overlay`, `#p1-modal-overlay`, `#deact-modal` — marked with `data-blocking="true"`

### Implementation Steps

22. **Taskbar CSS** in `static/css/main.css`
    - `.popup-taskbar`: fixed bottom, `display: flex`, same row as `#ai-panel`
    - `.popup-taskbar-tab`: flex `1 1 0`, min-width 120px, max-width 240px, text-overflow ellipsis
    - `.tab-label` + `.tab-close`: label text and X button
    - Slide-up 200ms animation for minimize/restore
    - Responsive: below 480px tabs condense to icon-only

23. **`#popup-taskbar` container** in `templates/base.html` — positioned before `#ai-panel`

24. **`ModalTaskbar` JS class** in `base.html`:
    - `minimize(modalEl)` — captures form state (all inputs/selects/textareas/contenteditable + scrollTop), hides modal, creates tab
    - `restore(tabId)` — reopens modal, restores state, removes tab
    - `close(tabId)` — discards state, removes tab
    - `getLabel(modalEl)` — checks `data-patient-name`, scans `.patient-name`/`.chart-header`/MRN field → "First Last — Title" or just title
    - Internal `_tabs` Map → `{ modalEl, state, label }`
    - Equal-width recalculation on add/remove

25. **Rewire modal backdrops** in `base.html` global JS:
    - Replace `backdrop.click → display:none` with `backdrop.click → ModalTaskbar.minimize(modal)`
    - Click on `<a>` or inside `<a>` → also follow `href` after minimize
    - Non-link click → minimize + propagate focus
    - Guard: skip minimize if `data-blocking="true"`

26. **Add `data-blocking="true"`** to 4 security modals in `base.html`

---

## System 3 — Split View

### Design
- **What**: View two pages side-by-side within the same window. Compare patients, view chart + care gaps, etc.
- **Activation**: Two methods:
  - **Ctrl+click** any link → opens in right pane
  - **Split button** in header (visible on every page) → opens split, lets user pick what to load
- **Default**: Single pane on app start. Default split is 2 panes unless user has configured otherwise.
- **Pane count**: User-configurable in Settings (2-4 panes). Preference persists across sessions via `current_user.set_pref('split_max_panes', n)`. Default is 2 on first activation.
- **Pane sizing**: Draggable divider between panes. Equal split by default.
- **Close split**: X button on secondary pane, or Ctrl+click same link to collapse back to single
- **Each pane is independent**: Own URL, own sub-panel state, own scroll position
- **Interaction with other systems**: Sub-panel appears in each pane independently. PiP widgets float above all panes. Taskbar is global.

### Implementation Steps

27. **Split view CSS** in `static/css/main.css`
    - `.app-layout.split-view`: grid adjusts to `1fr auto 1fr` for content area (primary | divider | secondary)
    - `.split-pane`: independent scrollable content container
    - `.split-divider`: 4px draggable handle, cursor: col-resize
    - `.split-header`: small bar inside each pane showing URL/page title + close button
    - Multi-pane: grid repeats `1fr auto` for each additional pane
    - Responsive: below 1024px, split disabled — single pane only

28. **Split button in header** — add to `templates/base.html` header bar:
    - Icon: split-screen icon (two rectangles side by side)
    - Click: creates secondary pane, loads command-palette-style picker for URL
    - Tooltip: "Split View (Ctrl+Click any link)"

29. **`SplitViewManager` JS class** in `base.html`:
    - `open(url, paneIndex)` — loads URL via fetch into pane (or iframe for full page isolation)
    - `close(paneIndex)` — removes pane, collapses back
    - `resize(paneIndex, width)` — drag handler for divider
    - Ctrl+click interceptor: prevent default, call `SplitViewManager.open(href, nextPane)`
    - Pane count limit: read from `localStorage['splitMaxPanes']` or user pref

30. **User preference**: Add `split_max_panes` to user preferences (default: 2, range: 2-4). Configurable in Settings page. Persists across sessions.

---

## System 4 — Picture-in-Picture Widgets

### Design
- **What**: Pop out any patient chart widget (or select data from other pages) into a floating mini-window that persists as the user navigates to different pages
- **Scope**: Patient chart widgets (Medications, Diagnoses, Labs, Vitals, Allergies, etc.) + select sections from other pages (care gap list, lab tracking table, active timer)
- **Activation**: Small "pop-out" icon on each eligible widget/section header
- **Behavior**:
  - Detaches widget from page flow into a floating, draggable, resizable window
  - Window has a title bar (widget name + patient name if applicable), drag handle, resize handle, minimize button, close button
  - Persists across page navigation — stays floating over whatever page the user is on
  - Data stays frozen at time of pop-out (snapshot) — refresh button to re-fetch
  - Multiple PiP windows can coexist
- **Z-index**: Above page content, below modals and AI panel
- **Session persistence**: PiP windows persist for app session. Closing the window discards it.

### Implementation Steps

31. **PiP CSS** in `static/css/main.css`
    - `.pip-window`: fixed position, draggable, resizable, min 200x150, max 600x500
    - `.pip-header`: title + patient name, drag handle, minimize/close buttons
    - `.pip-body`: cloned widget content, overflow-y auto
    - `.pip-resize-handle`: bottom-right corner resize
    - Z-index: 8000 (above content, below modals at 9000+)
    - Shadow: deeper than cards, lighter than modals
    - `.pip-minimized`: collapses to title-bar only

32. **Pop-out button** on eligible widgets:
    - Add `.pip-eligible` class to chart widgets and select page sections
    - Small icon button (⧉ or arrow-out-of-box icon) in widget header
    - On click: clones widget content, creates `.pip-window`, removes from page flow

33. **`PipManager` JS class** in `base.html`:
    - `create(sourceEl, options)` — clones content, creates floating window, positions it
    - `destroy(pipId)` — removes window
    - `minimize(pipId)` — collapses to title bar
    - `restore(pipId)` — expands back
    - `refresh(pipId)` — re-fetches source data (AJAX to page endpoint)
    - Drag/resize handlers using existing free_widgets.js patterns (mousedown/mousemove/mouseup)
    - Internal `_windows` Map → `{ element, sourceUrl, position, size, minimized }`
    - On page navigation: PiP windows persist (they're in the base template, not page-specific)

34. **Eligible sections** (mark with `data-pip="true"` + `data-pip-title="Widget Name"`):
    - All patient chart widgets (21 total)
    - Lab tracking table (labtrack page)
    - Care gap list (caregap page)
    - Active timer display (timer page)
    - Notification feed (notifications page)

---

## System 5 — Smart Bookmarks with Folders

### Design
- **What**: Upgrade bookmarks from flat chip list to Chrome-style bookmarks bar with drag-to-add and nested folders
- **Drag-to-bookmark**: Drag ANY link in the app (sidebar, sub-panel, page content, modal links) to the bookmarks bar to pin it
- **Folders**: Chrome-style dropdown folders on the bar. Click folder → dropdown showing contents. Drag bookmarks into/out of folders.
- **Folder depth**: One level (folders on bar, items inside folders — no folders inside folders)
- **Persists**: via existing user preferences system (`current_user.set_pref('bookmarks', data)`)

### Implementation Steps

35. **Bookmark folder CSS** in `static/css/main.css`
    - `.bookmark-folder`: chip with folder icon + label + dropdown arrow
    - `.bookmark-folder-dropdown`: absolute positioned dropdown, z-index 7000
    - `.bookmark-folder-dropdown .bookmark-chip`: items inside folder
    - Drop target highlighting: `.bookmark-bar.drag-over`, `.bookmark-folder.drag-over`

36. **Drag-to-bookmark JS** in `base.html`:
    - Make all `<a>` elements with `href` attribute draggable (set `draggable="true"` dynamically or use dragstart listener)
    - Bookmarks bar listens for `dragover` + `drop` events
    - On drop: extract `href` + text content → create bookmark
    - Folder drop targets: dropping on a folder adds to that folder
    - Drag between positions: reorder by dragging chips left/right

37. **Folder management**:
    - Right-click bookmarks bar → "New Folder" option (reuse existing context menu pattern)
    - Right-click folder → Rename, Delete
    - Right-click bookmark → Remove, Move to Folder
    - Drag bookmark onto folder → moves into folder
    - Drag bookmark out of folder dropdown → moves to bar top level

38. **Data model update**: Bookmarks stored as JSON array where each item is either `{ type: 'link', label, url, emoji }` or `{ type: 'folder', label, children: [...links] }`. Update `/api/bookmarks/personal` to handle folders.

39. **Migration**: Existing flat bookmarks automatically wrapped in the new schema (all become top-level links).

---

## System 6 — Breadcrumb Trail

### Design
- **What**: Thin strip below the bookmarks bar showing the last 5 visited pages as clickable chips
- **Placement**: Below bookmarks bar, above page content. Always visible. Indiscrete — small text, muted colors, doesn't compete with main content.
- **Context badges**: Each chip shows mini-context (patient name if on chart, gap count on care gaps, timer duration if timer was running)
- **Behavior**: Click any chip to navigate back to that page. Current page is highlighted.
- **Storage**: `sessionStorage['breadcrumbs']` — array of `{ url, label, badge, timestamp }`
- **No duplicates**: If a page is already in the trail, it moves to the front instead of duplicating

### Implementation Steps

40. **Breadcrumb CSS** in `static/css/main.css`
    - `.breadcrumb-trail`: flex row, gap 4px, padding 2px 12px, font-size 0.75rem, color `var(--text-muted)`
    - `.breadcrumb-chip`: subtle rounded pill, background `var(--bg-elevated)`, border `var(--border-color)`
    - `.breadcrumb-chip.active`: slightly brighter background or underline
    - `.breadcrumb-chip .bc-badge`: tiny badge (font-size 0.65rem) showing context info
    - Max 5 chips; older ones removed
    - Responsive: hidden below 768px

41. **Breadcrumb container** in `templates/base.html`:
    - `<nav class="breadcrumb-trail" id="breadcrumb-trail"></nav>` after bookmarks bar

42. **Breadcrumb JS** in `base.html`:
    - On page load: read `sessionStorage['breadcrumbs']`, add current page to front
    - Extract badge context: check `data-breadcrumb-badge` attribute on `<main>` element (set by each template)
    - Render chips with click handlers → `window.location = chip.url`
    - Deduplicate: if URL exists, remove old entry, add to front
    - Cap at 5 entries

43. **Badge context per page** — each template sets `data-breadcrumb-badge` on its main content:
    - Patient chart: patient name
    - Care gaps: gap count
    - Timer: running duration
    - Inbox: unread count
    - Other pages: page title only (no badge)

---

## System 7 — Type-Ahead Filtering

### Design
- **What**: On any list/table page, start typing to instantly filter visible items — no need to click into a search box first
- **Behavior**: Keystrokes captured at the page level (when no input/textarea is focused). Characters appear in a floating search indicator. Rows/items that don't match are hidden.
- **Clear**: Escape clears the filter. Backspace removes last character.
- **Visual**: Small floating badge near the top of the content area showing the current filter text
- **Scope**: All pages with data tables or list views

### Implementation Steps

44. **Type-ahead CSS** in `static/css/main.css`
    - `.type-ahead-indicator`: fixed or absolute position, top-right of content area, subtle pill with current filter text
    - Background `var(--bg-card)`, border, font-size 0.8rem, opacity 0 when empty, transition opacity
    - `.type-ahead-match`: highlight class for matching text in rows (optional yellow highlight)

45. **Type-ahead JS** in `base.html`:
    - Keydown listener on `document` — if `event.target` is not an input/textarea/select/contenteditable, capture printable characters
    - Build filter string, show in `.type-ahead-indicator`
    - Query all `[data-filterable]` elements on the page → hide those whose text doesn't contain the filter
    - Escape → clear filter, show all
    - Backspace → remove last character
    - Debounce: 100ms after last keystroke before filtering (for fast typists)

46. **Mark filterable elements** in each list/table template:
    - Add `data-filterable` to each `<tr>` or `.card` or list item that should be searchable
    - Content text used for matching (case-insensitive)

---

## System 8 — Page Transitions

### Design
- **What**: Smooth animated transitions when navigating between pages. User-selectable preset. Persists across sessions.
- **Presets**: None (instant), Fade (opacity cross-fade), Slide (directional slide left/right), Zoom (slight scale), Subtle (combined fade + tiny slide)
- **Duration**: 150-200ms per transition. Fast enough to not impede workflow.
- **Setting**: Dropdown in Settings page. Saved to `current_user.set_pref('page_transition', preset)` and `localStorage['pageTransition']`.
- **Implementation**: CSS `@keyframes` + `View Transition API` (with fallback for older browsers)

### Implementation Steps

47. **Transition CSS** in `static/css/main.css`:
    - `@keyframes fade-in`, `@keyframes fade-out`: opacity 0→1, 1→0
    - `@keyframes slide-in-right`, `@keyframes slide-out-left`: translateX transitions
    - `@keyframes zoom-in`, `@keyframes zoom-out`: scale(0.98)→scale(1) with opacity
    - `@keyframes subtle-in`, `@keyframes subtle-out`: combined fade + translateY(4px)
    - Applied via `.page-transition-{preset}` class on `.main-content`
    - `[data-transition="none"]`: no animation

48. **Transition JS** in `base.html`:
    - Read `localStorage['pageTransition']` or user pref
    - On page load: apply enter animation to `.main-content`
    - Intercept navigation (link clicks, sidebar clicks): apply exit animation → wait for animation end → navigate
    - Fallback: if View Transition API unavailable, use class-based animations
    - Settings integration: update `localStorage` and `current_user.set_pref` when changed

49. **Settings UI**: Add "Page Transition" dropdown to Settings page with 5 options. Live preview on selection.

---

## System 9 — AI Enhancements

### Design Principles
- **HIPAA compliant**: AI receives ONLY app metadata — page types, feature names, route paths, counts, categories. NEVER patient names, MRNs, DOBs, or any PHI.
- **API key model**: Users provide their own Claude API key in Settings, OR the office admin/developer provides an office-wide key. No key = AI features disabled.
- **Rate limiting**: Configurable in user settings — max requests per hour/day. Prevents runaway API costs.
- **Proactive suggestions**: ONLY if rate limits allow. If not implementable within cost constraints, defer to future phase and keep AI as chat-only.

### 9A — AI Workflow Coach

The AI assistant knows the app inside and out. Users can ask workflow questions and get step-by-step guidance with clickable links.

50. **Inject app knowledge** into AI context:
    - Load `data/help_guide.json` (40+ features, 7 categories) as system context
    - Load route map (`window.__npRoutes`) as available destinations
    - AI can reference features by name and provide clickable links

51. **Workflow response format**:
    - AI returns numbered steps with `[page links]` that become clickable in the chat panel
    - Pattern: "1. Go to [Care Gaps](/caregap) → 2. Click the patient row → 3. Address the gap"
    - Links rendered as actual clickable `<a>` tags in AI message bubbles

### 9B — AI Natural Language Navigation

Ask "where do I track labs?" and AI navigates you there.

52. **Navigation intent detection**:
    - AI parses natural language → matches to routes from `window.__npRoutes`
    - Returns a "Navigate" action button in chat → clicking it navigates to the matched page
    - No PHI involved — searches app structure only

### 9C — AI Writing Assistant

Small AI sparkle icon (✦) next to text input areas. Click for context-aware suggestions.

53. **AI writing icon placement**:
    - Add `.ai-assist-icon` (small sparkle ✦ button) next to textareas and contenteditable fields app-wide
    - Only appears when user has a valid API key configured
    - Icon is subtle — does not auto-trigger, only activates on click

54. **Context-aware suggestions**:
    - Based on the field's context (determined by `data-ai-context` attribute):
      - **Note/dot phrase editors**: Suggest clinical phrasing, prior authorization language, CPT billing support language
      - **Order set descriptions**: Suggest order set descriptions based on the set name
      - **Text compositions**: Suggest completions, AHK-style commonly-typed phrase expansions based on user's historical typing patterns and office-common phrases
    - AI icon click → small popover with 2-3 suggestions + "Custom prompt" input
    - Suggestions inserted at cursor position on click

55. **Rate limiting implementation**:
    - User setting: `ai_rate_limit_hourly` (default: 20), `ai_rate_limit_daily` (default: 100)
    - Track usage in `sessionStorage` (hourly) and `localStorage` (daily, resets at midnight)
    - When limit approached: show subtle warning. When exceeded: disable AI icon, show "Rate limit reached" tooltip
    - Admin can override limits for office-wide keys

### 9D — Help Popovers (? Icons)

56. **Help icon placement**:
    - Small `?` circle icon on each page header, widget header, and major feature section
    - **Hover**: Shows 2-line summary tooltip (from `help_guide.json` short description)
    - **Click**: Opens floating popover card with full feature description + "Read more →" link to `/help/{feature_id}`

57. **Help popover CSS**:
    - `.help-popover`: absolute positioned card, max-width 300px, z-index 8500
    - Arrow pointing to the `?` icon (CSS triangle)
    - `.help-popover-title`, `.help-popover-body`, `.help-popover-link`
    - Auto-dismiss: click outside or press Escape

58. **Help popover JS**:
    - `?` icons have `data-help-id="{feature_id}"` attribute
    - On hover: fetch short description from `help_guide.json` (preloaded), show tooltip
    - On click: show popover with full description + link
    - Popover follows the minimizable-to-taskbar pattern? — No, help popovers are lightweight, just dismiss on click-outside

---

## Files Modified / Created

### Modified Files
| File | Changes |
|------|---------|
| `static/css/main.css` | Sub-panel grid + styles, popup taskbar styles, split view grid, PiP window styles, bookmark folder styles, breadcrumb trail styles, type-ahead indicator, page transition keyframes, AI icon + help popover styles |
| `static/js/main.js` | Modal backdrop rewire to ModalTaskbar, drag-to-bookmark on all links, type-ahead keydown handler, breadcrumb sessionStorage, transition interceptor |
| `templates/base.html` | `{% block subpanel %}`, `#popup-taskbar` container, `#breadcrumb-trail` container, split view header button, ModalTaskbar class, SplitViewManager class, PipManager class, bookmark drag handlers, type-ahead JS, transition loader, help popover handler, AI writing icon init, `data-blocking` on 4 security modals |
| `templates/dashboard.html` | Verify no subpanel block; add `data-filterable` to roster items |
| `templates/patient_roster.html` | Move search/filters into subpanel; add PiP eligibility; add filterable markers |
| `templates/timer.html` | Move stats/export into subpanel; mark timer display as PiP-eligible |
| `templates/inbox.html` | Move tab nav + digest into subpanel; add filterable markers |
| `templates/oncall.html` | Move filters/actions into subpanel; add filterable markers |
| `templates/orders.html` | Move tabs/actions into subpanel; add filterable markers |
| `templates/labtrack.html` | Move stats/actions into subpanel; mark table as PiP-eligible + filterable |
| `templates/caregap.html` | Move date nav/stats into subpanel; mark gap list as PiP-eligible + filterable |
| `templates/bonus_dashboard.html` | Move quarter/stats into subpanel |
| `templates/tcm_watch.html` | Move form/summary into subpanel; add filterable markers |
| `templates/ccm_registry.html` | Move stats/enroll into subpanel; add filterable markers |
| `templates/monitoring_calendar.html` | Move filters/stats into subpanel |
| `templates/care_gaps_preventive.html` | Move stats/export into subpanel; add filterable markers |
| `templates/staff_billing_tasks.html` | Move role/timing filters into subpanel; add filterable markers |
| `templates/notifications.html` | Move type filter/mark-read into subpanel; mark feed as PiP-eligible + filterable |
| `templates/patient_chart.html` | Move 7-tab nav into subpanel; add PiP buttons on all 21 widgets; add AI assist icons on text fields |
| `models/user.py` | Add `split_max_panes`, `page_transition`, `ai_rate_limit_hourly`, `ai_rate_limit_daily` preference keys |
| `routes/dashboard.py` (or settings route) | Add split pane count + transition preference endpoints |
| `routes/help.py` | Expose help_guide.json data for popover AJAX fetches |
| `data/help_guide.json` | Add entries for all 9 new systems |

### New Files
| File | Purpose |
|------|---------|
| `tests/test_subpanel.py` | Sub-panel present on 15 pages, absent on dashboard, content verification |
| `tests/test_popup_taskbar.py` | Taskbar container, `data-blocking` on 4 modals, non-blocking minimizable |
| `tests/test_split_view.py` | Split view CSS classes, header button, pane count preference |
| `tests/test_pip_widgets.py` | PiP eligibility markers, PipManager JS referenced |
| `tests/test_bookmarks_folders.py` | Folder schema, drag-to-bookmark API, migration |
| `tests/test_breadcrumbs.py` | Breadcrumb container, badge context attributes |
| `tests/test_type_ahead.py` | Filterable markers on list pages |
| `tests/test_transitions.py` | Transition CSS keyframes, preference endpoint |
| `tests/test_ai_enhancements.py` | AI icon placement, rate limit config, help popovers, workflow response format |
| `Documents/overview/UI_OVERHAUL.md` | This document |

---

## Implementation Order & Dependencies

```
Phase 1 (Foundation)     — Systems 1 + 2 (sub-panel + taskbar)
  ├─ 1A: CSS foundation (sub-panel + taskbar)          [no deps]
  ├─ 1B: Base template (subpanel block + toggle JS)    [depends 1A]
  ├─ 1B2: Taskbar system (ModalTaskbar + rewire)       [depends 1A, parallel with 1B]
  └─ 1C: 15 page sub-panels                           [depends 1B]

Phase 2 (Navigation)     — Systems 5 + 6 + 7 (bookmarks + breadcrumbs + type-ahead)
  ├─ 2A: Smart bookmarks (drag + folders)              [no deps on Phase 1]
  ├─ 2B: Breadcrumb trail                              [no deps on Phase 1]
  └─ 2C: Type-ahead filtering                          [no deps on Phase 1]
  (Phase 2 can run in parallel with Phase 1C)

Phase 3 (Advanced Layout) — Systems 3 + 4 (split view + PiP)
  ├─ 3A: Split view                                    [depends Phase 1A for grid]
  └─ 3B: PiP widgets                                   [depends Phase 1A for z-index layering]
  (Phase 3 can start after Phase 1A completes)

Phase 4 (Polish)          — Systems 8 + 9 (transitions + AI)
  ├─ 4A: Page transitions                              [no deps, standalone CSS+JS]
  ├─ 4B: AI enhancements                               [depends Phase 1B for sub-panel help icons]
  └─ 4C: Help popovers                                 [depends 4B for help data integration]

Phase 5 (Testing + Docs)
  ├─ 5A: Write all test files                          [depends all phases]
  ├─ 5B: Manual verification checklist                 [depends 5A]
  └─ 5C: Documentation updates                         [depends 5B]
```

### Parallelization Summary
- **Phase 1A + 2A + 2B + 2C + 4A** can all start simultaneously (no interdependencies)
- **Phase 1B + 1B2** start after 1A
- **Phase 1C** starts after 1B
- **Phase 3A + 3B** start after 1A
- **Phase 4B + 4C** start after 1B
- **Phase 5** after everything else

---

## Verification Plan

### Automated Tests
1. `python -m pytest tests/test_subpanel.py -v`
2. `python -m pytest tests/test_popup_taskbar.py -v`
3. `python -m pytest tests/test_split_view.py -v`
4. `python -m pytest tests/test_pip_widgets.py -v`
5. `python -m pytest tests/test_bookmarks_folders.py -v`
6. `python -m pytest tests/test_breadcrumbs.py -v`
7. `python -m pytest tests/test_type_ahead.py -v`
8. `python -m pytest tests/test_transitions.py -v`
9. `python -m pytest tests/test_ai_enhancements.py -v`
10. `python -m pytest tests/ -q` — full regression
11. `python test.py` — main suite (127/127)

### Manual Verification — Sub-Panel + Taskbar
- Dashboard: full sidebar, no sub-panel
- Non-dashboard pages: icon rail + sub-panel with correct content
- Sub-panel toggle: open/collapse, persists via localStorage
- Sub-panel Quick Nav: cross-links reach related pages
- 3-click rule: pick any two random pages → reachable in ≤3 clicks
- Modal click-outside → minimizes to taskbar tab
- Taskbar tab label: "Patient Name — Title" when applicable
- Restore tab → modal reopens with all form data intact
- Close tab (X) → discards modal permanently
- Multiple minimized tabs → equal-width, side-by-side
- Click link while modal open → minimizes + navigates
- Blocking modals (HIPAA/lock/P1/deactivation) → cannot minimize
- Mobile (<768px) → sub-panel hidden

### Manual Verification — Split View + PiP
- Ctrl+click link → opens in split pane
- Split header button → opens split picker
- Close secondary pane → returns to single view
- Drag divider → resize panes
- Settings → change max panes (2-4) → persists
- Pop out patient chart widget → floating PiP window
- Navigate to different page → PiP stays visible
- PiP drag/resize → works
- PiP minimize/restore/close → works
- Multiple PiP windows → coexist

### Manual Verification — Bookmarks + Breadcrumbs + Type-Ahead
- Drag any link to bookmarks bar → creates bookmark
- Right-click bar → New Folder → create folder
- Drag bookmark into folder → moves into folder dropdown
- Click folder → dropdown shows contents
- Breadcrumb trail: shows last 5 pages below bookmarks bar
- Breadcrumb badges: patient name on chart, gap count on care gaps
- Click breadcrumb chip → navigates back
- Start typing on patient roster → instant filter (no search box click)
- Escape → clears filter
- Filter works on all list pages

### Manual Verification — Transitions + AI
- Settings → select transition preset → live preview
- Navigate between pages → selected animation plays
- Set to "None" → instant transitions
- Preference persists across app restart
- AI sparkle icon next to text fields → click opens suggestions popover
- AI workflow question → step-by-step with clickable links
- "Where do I find X?" → AI navigates to correct page
- Rate limit warning appears when approaching limit
- Help `?` hover → 2-line tooltip
- Help `?` click → popover card with "Read more" link

---

## Key Decisions Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Sub-panel width | 220px | Narrower than sidebar (240px) — feels subordinate |
| Sub-panel persistence | localStorage per page | Server pref unnecessary for layout state |
| Popup taskbar position | Shared bar with AI panel | No new UI chrome; tabs left, AI right |
| Blocking modal exceptions | HIPAA, lock, P1, deactivation | Security/compliance requires explicit action |
| Split pane count | User-configurable 2-4, default 2 | Power users get flexibility; sane default on first use |
| Split pane default on app open | Single pane | Don't surprise users; split only on explicit action |
| PiP scope | Chart widgets + select other pages | Core need is chart widgets; extend selectively |
| Bookmark folders | One level deep (Chrome-style) | Avoids complexity of nested trees |
| Breadcrumb style | Indiscrete, muted colors | Should not compete with navigation or content |
| Type-ahead activation | Any keystroke when no input focused | Most natural — just start typing |
| Page transitions | 5 presets, user-selectable, persistent | Users have control; no forced animations |
| AI proactive suggestions | Defer to future if rate limiting proves difficult | Cost control is critical; chat-only is MVP |
| AI writing icon | All text fields, click-only | Non-intrusive; user initiates |
| AI API key model | User provides own, or admin provides office key | HIPAA compliance; cost sharing |
| Help popovers | Hover = tooltip, Click = popover card | Progressive disclosure without page navigation |
| Status bar | Not added | Header already shows sufficient context |
| Focus/Zen mode | Not added | Users need nav always visible in clinical setting |
| Command palette actions | Not added | Clicks-only interaction model preferred |

---

## Scope Exclusions

- **Pages from top menu only** (Tools > Tickler, Tools > CS Tracker, etc.): No sub-panel. Can opt-in later via `{% block subpanel %}`.
- **Help page** (`/help`): Already has its own sidebar navigation. Excluded from sub-panel system.
- **WebSocket real-time updates**: Current polling model (60s) stays. WebSocket upgrade is a separate initiative.
- **Multi-window (OS-level)**: Not supported. Split view and PiP provide in-window multi-tasking.
- **Undo/redo system**: Not in scope. Would require significant architecture changes.
- **Mobile-first redesign**: This overhaul targets desktop/tablet. Mobile gets graceful degradation (hidden sub-panels, single pane, stacked taskbar).
