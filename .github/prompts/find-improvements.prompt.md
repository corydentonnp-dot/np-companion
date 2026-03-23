---
description: "Find UX and usability improvements — audit templates, routes, and JS for interaction quality, accessibility, loading states, empty states, and user workflow friction."
agent: agent
argument-hint: "Optional: scope to a specific area (e.g. 'patient chart', 'billing pages', 'accessibility only', 'forms')"
---

# Find Usability Improvements

You are running a **user interaction and program usability audit** on CareCompanion. Your goal is to find concrete, actionable improvements that will make the app easier, faster, and more pleasant for the clinical user to operate during a busy workday.

**Output:** A prioritized improvement list grouped by category. Each item includes the file, the problem, and a specific fix recommendation. Do NOT implement fixes — only report them.

If the user provided a scope argument, narrow the audit to that area only. Otherwise, audit the full application.

## Phase 0 — Context Load

1. Run the process guard: `(Get-Process python -ErrorAction SilentlyContinue).Count` (timeout: 10000ms).
2. Read `Documents/dev_guide/PROJECT_STATUS.md` (Feature Registry) to understand what's built.
3. Read `templates/base.html` to understand the app shell, nav, and shared UX patterns.
4. Read `static/js/main.js` overview (search for key function names) to understand client-side behavior.
5. Read `static/css/main.css` overview (search for `:root`, `focus`, `@media`, `empty`, `spinner`) to understand styling patterns.

## Phase 1 — Loading States & Feedback

**Problem pattern:** The user clicks something and nothing visibly happens for 1-3 seconds. They click again, causing duplicate submissions or confusion.

Audit every template and route that performs async work:

1. **Missing loading indicators** — Search templates for `fetch(` and `XMLHttpRequest` calls. For each one, check: is there a spinner, "Loading…" text, or button disabled state shown during the request? Report any that have no visual feedback.
2. **Missing button disable on submit** — Search forms with `method="POST"` for submission without disabling the submit button. Double-click = double submission risk.
3. **Page-level loading** — When Flask routes take time (e.g., API enrichment, billing engine), is there any indication the page is loading? Check for slow routes in `routes/patient.py` (chart load), `routes/intelligence.py` (morning briefing), `routes/caregap.py` (panel rebuild).
4. **Skeleton/placeholder content** — Check if widgets or data panels show placeholder content while loading, or if they just appear empty until data arrives.

**Report format per finding:**
```
- [file.html] [line ~N]: fetch('/api/...') has no loading indicator → Add spinner inside [container element] during request
```

## Phase 2 — Empty States & Zero-Data Experience

**Problem pattern:** A new user or a page with no data shows a blank white area with no guidance.

1. **Check every data table and list view** — For each template that displays a list (tables, card grids, ul/ol from loops), check if there's a `{% if not items %}` or `{% else %}` block that shows a helpful empty state.
2. **Verify the reusable `_empty_state.html` macro** — Read it, then search for templates that SHOULD use it but render nothing when data is empty.
3. **First-run experience** — Check the dashboard, My Patients, Orders, Lab Track, and Care Gaps pages for what a brand-new user with zero data would see. Is there guidance on what to do first?
4. **Search results** — When a search/filter returns zero results, is there a "No results found" message? Check patient search, command palette, order browser, calculator picker, medication search.
5. **Null field display** — Check patient chart fields. When a value is None/empty (e.g., no phone, no DOB, no allergies), does it show "—" or "Not recorded" or just nothing?

**Report format:**
```
- [file.html]: {{ items }} loop has no empty state → Add {% else %} block with empty_state macro: "No [items] yet. [Action to take.]"
```

## Phase 3 — Form Usability & Validation

**Problem pattern:** The user fills out a form, submits, and gets a generic error — or worse, loses their input on failed validation.

1. **Client-side validation** — Search forms for `required`, `pattern`, `min`, `max`, `type="email"`, etc. Report forms that rely solely on server-side validation with no client hints.
2. **Inline error messages** — After a failed form submission, does the user see which specific field is wrong? Or just a generic flash message? Check POST routes that redirect back with `flash('Error', 'error')`.
3. **Input preservation on error** — When a form submission fails (validation, duplicate, etc.), are the previously entered values preserved? Search for forms that POST and redirect vs. forms that re-render with the old values.
4. **Autofocus** — Check if the primary input on each page has `autofocus` set. The user shouldn't have to click the first field on pages they navigate to frequently (search bars, new entry forms).
5. **Input types** — Search for inputs that should use specific HTML5 types: date pickers (`type="date"`), number spinners (`type="number"`), telephone (`type="tel"`), time pickers (`type="time"`). Report any that use `type="text"` when a more specific type would help.
6. **Placeholders and labels** — Check that form inputs have either a visible `<label>` or at minimum a descriptive `placeholder`. Report unlabeled inputs.

## Phase 4 — Navigation & Workflow Efficiency

**Problem pattern:** The user takes 3 clicks to reach something they use 50 times per day, or they get lost and can't find their way back.

1. **Back navigation** — For detail/sub-pages (patient chart → risk tools, care gaps → patient detail, billing → why not), is there a clear "← Back" link? Check templates that are 2+ levels deep.
2. **Breadcrumb coverage** — Check if `base.html` breadcrumbs work on all sub-pages. Search for pages that set breadcrumb data vs. pages that show no trail.
3. **Frequent-action shortcuts** — Identify the 10 most-used actions (by clinical workflow: open patient, view schedule, start timer, check inbox, review billing, view labs, check care gaps). How many clicks does each take from the dashboard? Report any that take more than 2 clicks.
4. **Contextual actions** — On the patient chart, when viewing a specific widget, are related actions accessible? (e.g., from medications → refill check, from diagnoses → billing suggestions, from vitals → calculator).
5. **After-action landing** — After completing an action (save order, submit form, delete item), where does the user land? Check for POST-redirect patterns. Report any that land the user somewhere unexpected.
6. **Tab order** — Check templates with multiple interactive elements. Is the tab order logical? Report any with `tabindex` values that skip around or interactive elements that are unreachable by tab.

## Phase 5 — Accessibility Quick-Check

**Problem pattern:** Screen reader users, keyboard-only users, or users with visual impairments can't use parts of the app.

1. **Focus suppression** — Search CSS for `outline: none` or `outline: 0` on `:focus` (NOT `:focus-visible`). These remove the visible focus ring for keyboard users. Report each instance.
2. **Clickable non-buttons** — Search templates for `onclick=` on `<div>`, `<span>`, `<td>`, or `<tr>` elements. These need `role="button"` and `tabindex="0"` to be keyboard-accessible. Report each.
3. **Images without alt text** — Search for `<img` tags without `alt=` attributes.
4. **Color-only indicators** — Search for status badges, alerts, or indicators that use ONLY color to convey meaning (no text, no icon). Report each — they need a secondary indicator for colorblind users.
5. **ARIA on dynamic content** — Search for areas that update via JavaScript (`innerHTML`, `textContent`, `.html()`) that lack `aria-live` regions. Dynamically updated content is invisible to screen readers without live regions.
6. **Modal trap** — Check modals: can the user `Escape` out? Is focus trapped inside (prevent tabbing behind the modal)? Check `base.html` modal patterns.

## Phase 6 — Error Recovery & Resilience

**Problem pattern:** Something fails (network, API, bad input) and the user is stuck or confused.

1. **Fetch error handling** — For every `fetch()` call, check: is there a `.catch()` or `try/catch`? Does it show the user a helpful message on failure? Or does it silently fail?
2. **Timeout handling** — For API-dependent features (RxNorm enrichment, ICD-10 lookup, NetPractice scrape), what happens when the API is slow or down? Check for timeout parameters and fallback UI.
3. **Session expiration** — What happens when the user's Flask session expires mid-workflow? Do they get a helpful redirect to login, or a 500 error?
4. **Stale data indicators** — For cached data (drug info, ICD-10 codes, schedule), is there any indicator of when it was last refreshed? Check for "Last updated" timestamps.
5. **Destructive action recovery** — After deleting something, is there any undo? Check if soft-deleted items have a "restore" option.

## Phase 7 — Visual Consistency & Polish

**Problem pattern:** Pages feel inconsistent — different spacing, button styles, table formats, header patterns.

1. **Button style consistency** — Search templates for button patterns. Are they using consistent classes (`btn`, `btn-sm`, `btn-outline`, etc.) or are there inline-styled buttons? Report any one-off `style=` buttons.
2. **Table style consistency** — Search for `<table` tags. Are they using consistent classes or are some unstyled? Report tables without the standard table class.
3. **Card/panel consistency** — Check if detail panels, widget cards, and info boxes use the same border-radius, shadow, padding pattern or if each page invents its own.
4. **Icon usage** — Are icons used consistently? Check for mixed emoji + SVG + icon font usage. Report pages that use a different icon system than the rest of the app.
5. **Typography** — Check for inline font-size overrides that deviate from the base typography scale. Report headers that use `style="font-size:..."` instead of appropriate heading tags.
6. **Spacing** — Check for inconsistent margin/padding patterns between pages at the same level of the hierarchy.

## Phase 8 — Prioritized Report

Present the complete findings as a prioritized list:

```
# Usability Improvement Report — [DATE]

## Summary
- [N] improvements found across [N] categories
- [N] Critical (blocks workflow or causes data loss)
- [N] High (significant friction, affects daily use)
- [N] Medium (noticeable annoyance, workaround exists)
- [N] Low (polish item, nice to have)

## 🔴 Critical
1. [Finding] — [File] — [Specific fix recommendation]

## 🟠 High Priority
1. ...

## 🟡 Medium Priority
1. ...

## 🟢 Low Priority (Polish)
1. ...

## Quick Wins (< 5 minutes each)
- [ ] [Finding] → [One-line fix description]
- [ ] ...

## Larger Efforts (need planning)
- [ ] [Finding] → [What needs to happen, estimated scope]
- [ ] ...
```

**Severity guide:**
- **Critical** — Data loss risk, broken workflow, user cannot complete a task
- **High** — Significant daily friction (missing loading states on slow pages, no empty states on primary views, lost form data on error)
- **Medium** — Noticeable but workable (missing back buttons, inconsistent styles, weak validation)
- **Low** — Polish (icon inconsistency, typography tweaks, minor accessibility gaps in unused features)

**Do NOT report:**
- Issues that require external dependencies (npm, React, Tailwind)
- Issues in admin-only pages (low traffic, low priority)
- Issues in agent/ code (not user-facing)
- Issues in test files
- Theoretical security issues (those belong in the HIPAA audit, not here)
