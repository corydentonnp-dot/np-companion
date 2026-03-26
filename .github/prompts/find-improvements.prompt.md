---
description: Find UX and usability improvements across templates, routes, and JS.
agent: agent
argument-hint: Optional scope (e.g. patient chart, billing, accessibility)
---

# Find Improvements

Run a targeted usability audit and report actionable improvements without implementing code changes.

## Output Contract

Return prioritized findings grouped by severity. For each finding include:
- file
- issue summary
- concrete fix recommendation

## 0. Context Load

1. Process guard check for Python process count.
2. Read `Documents/dev_guide/PROJECT_STATUS.md`.
3. Review shared shell files:
- `templates/base.html`
- `static/js/main.js`
- `static/css/main.css`

## 1. Loading and Feedback

Identify missing user feedback for async or long-running operations:
- fetch/XHR calls without spinner/loading text
- submit buttons not disabled during request
- slow pages with no loading state
- panels that appear blank while data is loading

## 2. Empty States

Find views that show blank output when data is empty:
- table/list loops without explicit empty-state branch
- first-run pages lacking guidance
- search/filter no-results cases with no message
- null fields displayed as empty instead of clear placeholders

## 3. Forms and Validation

Check form usability and recoverability:
- missing client-side validation attributes
- generic errors without field-level guidance
- user input lost on failed POST
- missing autofocus on frequent-entry pages
- incorrect input types (text vs date/number/tel/time)
- unlabeled fields

## 4. Navigation Efficiency

Look for workflow friction:
- missing back links on deep pages
- inconsistent breadcrumb behavior
- high-frequency actions requiring too many clicks
- poor post-action landing behavior
- broken keyboard tab flow

## 5. Accessibility Quick Audit

Flag common issues:
- focus ring suppression
- clickable non-button elements without role/tabindex
- missing image alt attributes
- color-only status cues
- dynamic content updates without aria-live
- modal focus trap/escape issues

## 6. Error Recovery

Evaluate resilience:
- async calls without catch handling
- missing timeout/fallback behavior for external dependencies
- poor session-expiry user flow
- no stale-data freshness indicators where needed
- destructive actions without recovery pattern

## 7. Visual Consistency

Audit UI consistency:
- inline-styled one-off buttons
- unstyled or inconsistent tables
- inconsistent panel/card spacing and hierarchy
- icon-system inconsistency
- typography overrides outside scale

## 8. Report Format

Use this structure:

- Summary counts by severity
- Critical findings
- High-priority findings
- Medium findings
- Low/polish findings
- Quick wins (<5 minutes)
- Larger efforts needing planning

Severity guidance:
- Critical: blocks workflow, data-loss risk
- High: major daily friction
- Medium: noticeable but workable
- Low: polish only
