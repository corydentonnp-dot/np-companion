# Patient Getter Plan

**Date:** March 16, 2026  
**Status:** Implementation Started  
**Goal:** Simplify schedule scraping by reading patient data directly from the DOM instead of clicking into each patient's detail page.  
**Architecture:** Connect to real Google Chrome via CDP (Chrome DevTools Protocol) instead of headless Playwright Chromium.

---

## The Problem with the Current Approach

The existing scraper (`scrapers/netpractice.py`) works like this:

1. Log into webPRACTICE via Playwright
2. Replay user-recorded navigation steps to reach the schedule page
3. Parse schedule rows by regex-matching body text for `TIME  NAME (MRN)` patterns
4. **Click each patient name** → read the detail page → press Back → repeat
5. Store everything in the database

**Step 4 is the bottleneck.** For a 25-patient day, that's 25 click-wait-read-back cycles through a hospital web app that wasn't designed for speed. Each cycle is ~3-5 seconds. The whole scrape takes 1-2 minutes and is fragile — if a single page.go_back() fails, the rest of the scrape breaks.

The setup wizard was designed to let users record those navigation steps, but the webPRACTICE UI is complex enough that the wizard itself became a hard problem.

---

## What Chrome F12 Revealed

Inspecting the provider's daily schedule page in Chrome DevTools shows that **most of the data we need is already in the schedule page DOM** — no clicking required.

### DOM Structure of a Patient Row

```html
<tr>
  <td class="schtime">
    <font style="font-weight:bold" color="#0000FF">09:15A</font>
  </td>
  <td title="PHYSICAL"
      onclick="jsModApt('48','a/642','2','09:15','PE','1','GUTHRIE, JESSICA','28800','6')"
      class="schSlot"
      style="color:#000000;background-color:#FF99CC;">
    <nobr>
      <img src="/_mnpstatic/images/verifyStatus_green.png"
           title="Passed verification on 03-13-2026 with HK">
      "&nbsp;GUTHRIE, JESSICA (55288)" -- $0
    </nobr>
  </td>
</tr>
```

### Data Available Without Clicking

| Data Point | Where It Lives | CSS Selector / Extraction Method |
|---|---|---|
| **Appointment time** | `td.schtime font` inner text | `page.query_selector_all('td.schtime font')` |
| **Patient name** | `td.schSlot nobr` text content (e.g., `GUTHRIE, JESSICA (55288)`) | Regex: `([A-Z\s'-]+,\s*[A-Z\s'-]+)\s*\((\d+)\)` |
| **Patient MRN** | In parentheses in the same `nobr` text (e.g., `55288`) | Same regex, group 2 |
| **Appointment type description** | `td.schSlot` `title` attribute (e.g., `"PHYSICAL"`) | `element.get_attribute('title')` |
| **Appointment type code** | `jsModApt()` 5th parameter (e.g., `'PE'`) | Regex on onclick |
| **Units** | `jsModApt()` 6th parameter | Same regex on onclick |
| **Verification status** | `img` title inside `nobr` (e.g., `"Passed verification on 03-13-2026 with HK"`) | `img[src*="verifyStatus"]` title attribute |
| **Background color** | Inline style on `td.schSlot` (e.g., `#FF99CC`) | `element.get_attribute('style')` — color-codes visit types |
| **Provider ID** | `jsModApt()` 2nd parameter (e.g., `67642`) | Same regex on onclick |
| **Row/slot index** | `jsModApt()` 9th parameter — position in schedule grid | Same regex on onclick |

### Confirmed Visit Type Color Mapping

| Background Color | Visit Type | Example |
|---|---|---|
| `#FF99CC` | Physical / Established | PHYSICAL/EST (PE) |
| `#99FFFF` | General Visit | L BREAST PAIN (GV) |
| `#FFFF99` | Acute Visit | ACUTE VISIT (AV) |
| `#FF0000` | **Blocked / Doctor Off** | DOCTOR OFF (no code) |
| `#66CCCC` | Follow-Up | 2 WEEK FOLLOW UP (no code) |

### Blocked Appointment Detection

From the screenshots, blocked slots (DOCTOR OFF) have:
- `title="DOCTOR OFF"`
- Empty visit type code (param 5 of jsModApt is `''`)
- Patient name = `"OFF, DR"` (or similar `OFF, *` pattern)
- Background color `#FF0000` (bright red)
- No verification image
- Should be **excluded** from patient schedule, but can be noted as blocked time

### The `jsModApt()` Function Parameters (Confirmed from 5 screenshots)

```javascript
jsModApt('48', '67642', '2', '08:00', 'PE', '1', 'FAILLA, SALV___', '28800', '1')
//        │      │       │     │       │      │     │                  │        │
//        │      │       │     │       │      │     │                  │        └─ row index (slot position in schedule grid)
//        │      │       │     │       │      │     │                  └─ 28800 = seconds since midnight for 08:00, likely schedule day start
//        │      │       │     │       │      │     └─ patient full name (LASTNAME, FIRST...) or "OFF, DR" for blocked
//        │      │       │     │       │      └─ units (scheduling slots) — always '1' in observed data
//        │      │       │     │       └─ visit type code: PE=Physical, GV=General Visit, AV=Acute Visit, ''=blocked/other
//        │      │       │     └─ appointment time (24h format)
//        │      │       └─ unknown (always '2' — maybe view type?)
//        │      └─ provider ID (67642 — consistent across all rows for one provider)
//        └─ resource/facility ID (always '48')
```

**Confirmed consistent across all 5 rows examined.**

### Schedule Page DOM Structure (from Image 5 — first appointment)

```html
<div class="sch_blockscroll">
  <table border="0" cellpadding="0" cellspacing="1" width="100%" style="table-layout:fixed">
    <!-- outer table -->
  </table>
  <table id="schblock62" border="0" cellpadding="0" cellspacing="0" width="100%"
         style="background-color:#F6F6F6;border-bottom:1px solid #C5C9E6;table-layout:fixed;">
    <colgroup>...</colgroup>
    <tbody>
      <tr>
        <td class="schtime">...</td>   <!-- time cell -->
        <td title="PHYSICAL/EST" onclick="jsModApt(...)" class="schSlot" style="...">
          ...                            <!-- appointment cell -->
        </td>
      </tr>
      <!-- more rows -->
    </tbody>
  </table>
</div>
```

**Key:** Each provider gets their own `table#schblock{N}`. The `{N}` may be a provider or resource identifier. Multiple providers on one page = multiple `schblock` tables inside `sch_blockscroll`.

---

## What's NOT in the Schedule DOM

These fields are **only** on the detail page (accessed by clicking the patient):

- **Reason for visit** (e.g., "COUGHING + CONG")
- **Patient DOB**
- **Patient phone number**
- **Comment / scheduling notes**
- **Entered by** (who booked it)
- **Status** (e.g., "TEXT SENT (TS)")
- **Location** (e.g., "FAMILY PRACT ASSOC (2)")
- **New Patient flag** (Y/N)

---

## The New Plan: DOM-First Scraping via Chrome CDP

### Architecture: Connect to Real Chrome, Not Headless

NetPractice only runs in Chrome, and Chrome is already installed in the office. Instead of launching a separate headless Chromium (which could get blocked or behave differently), we **connect Playwright to the real Chrome browser** via the Chrome DevTools Protocol (CDP).

**How it works:**
1. Chrome must be started with `--remote-debugging-port=9222` (a startup shortcut handles this)
2. Playwright connects via `browser_type.connect_over_cdp('http://localhost:9222')`
3. The scraper opens a new tab, does its work, closes the tab — the user's other Chrome tabs are untouched
4. This is the same Chrome instance the user already uses for NetPractice

**Benefits:**
- No separate browser to install or manage
- NetPractice sees a real Chrome, not headless Chromium
- Session cookies from manual browsing persist
- Can inspect the page the user is already looking at

### Strategy: Get 80% of the data from the DOM, click only when needed

**Phase A — DOM-only scrape (fast, no clicking)**

1. Log in (same as now — this part works fine)
2. Navigate to the schedule page (same nav steps OR a direct URL if we can find one)
3. Query all `td.schSlot` elements on the page
4. For each slot, extract:
   - Time from the adjacent `td.schtime`
   - Patient name and MRN from the `nobr` text
   - Visit type from the `title` attribute
   - Visit type code from the `onclick` `jsModApt()` parameters
   - Verification status from the `img` title
   - Background color (encodes visit type category)
5. Save to database — this gives us **time, name, MRN, visit type** for every patient in one page load

**Result:** Full schedule in ~2 seconds instead of 1-2 minutes. No clicking, no Back button issues.

**Phase B — Selective detail clicks (optional, for enrichment)**

Only click into a patient when we actually need detail-page-only data:
- New patients (first time seeing a name) → get DOB, phone, reason
- Complex visit types (physicals, new patients) → get reason and comment
- Dashboard anomaly detection → needs duration (can estimate from units × 15 min)

This turns 25 detail clicks into maybe 3-5 targeted ones.

### Duration Calculation Without Clicking

The `units` field from `jsModApt()` param 6 tells us how many scheduling slots the appointment uses. Standard slot = 15 minutes. So:
- units = 1 → 15 min (follow-up)
- units = 2 → 30 min (physical, new patient)
- units = 3 → 45 min (extended visit)

This is enough for the dashboard's anomaly detection (back-to-back complex visits, gap detection, etc.).

### New Patient Detection Without Clicking

Currently the scraper checks the detail page's "New Patient: Y/N" flag. With DOM-only scraping, we can:
1. **Compare against historical data** — if the patient name + MRN has never appeared in our `schedules` table, flag as new (this logic already exists in `_store_appointments`)
2. **Color coding** — webPRACTICE may use a specific background color for new patients. Once we identify the color, it's instant.

---

## Implementation Plan

### Step 1: Add a DOM parsing method to the scraper

Add `_parse_schedule_dom(page)` alongside the existing `_parse_schedule_rows(page)`. The DOM parser uses CSS selectors instead of regex on body text:

```python
async def _parse_schedule_dom(self, page):
    """Parse schedule using DOM selectors instead of body text regex."""
    appointments = []
    
    slots = await page.query_selector_all('td.schSlot')
    for slot in slots:
        # Get visit type from title attribute
        visit_type = await slot.get_attribute('title') or ''
        
        # Get onclick params
        onclick = await slot.get_attribute('onclick') or ''
        params = self._parse_jsmodapt(onclick)
        
        # Get patient name + MRN from inner text
        text = await slot.inner_text()
        name, mrn = self._extract_name_mrn(text)
        
        # Get time from sibling td.schtime
        row = await slot.evaluate_handle('el => el.parentElement')
        time_td = await row.query_selector('td.schtime')
        time_text = await time_td.inner_text() if time_td else ''
        
        if name:  # Skip empty slots
            appointments.append({
                'time': time_text.strip(),
                'patient_name': name,
                'patient_mrn': mrn,
                'visit_type': visit_type,
                'visit_type_code': params.get('type_code', ''),
                'units': params.get('units', 1),
                'duration_minutes': params.get('units', 1) * 15,
            })
    
    return appointments
```

### Step 2: Parse `jsModApt()` parameters

```python
def _parse_jsmodapt(self, onclick_str):
    """Extract structured data from jsModApt('48','a/642','2','09:15','PE','1','NAME','28800','6')"""
    match = re.search(r"jsModApt\((.+?)\)", onclick_str)
    if not match:
        return {}
    # Split on comma, strip quotes
    parts = [p.strip().strip("'\"") for p in match.group(1).split(',')]
    if len(parts) >= 7:
        return {
            'resource_id': parts[0],
            'appointment_id': parts[1],
            'provider_id': parts[2],
            'time': parts[3],
            'type_code': parts[4],
            'units': int(parts[5]) if parts[5].isdigit() else 1,
            'patient_name': parts[6],
            'param_8': parts[7] if len(parts) > 7 else '',
            'param_9': parts[8] if len(parts) > 8 else '',
        }
    return {}
```

### Step 3: Simplify the wizard

The wizard no longer needs to record a complex sequence of clicks to get from login to the schedule page. Instead:

**Option A — Direct URL navigation**  
If the schedule page has a predictable URL pattern (many webPRACTICE pages do), we can skip the wizard entirely. Try capturing the schedule page URL from the browser address bar and test if navigating to it directly after login works.

**Option B — Minimal wizard**  
The wizard only needs to record enough steps to get from "just logged in" to "schedule page is visible." That's probably 2-3 clicks max. No more per-patient recording. The current wizard UI can handle this.

### Step 4: Update the `_scrape_date` method

Replace the slow click-each-patient loop:

```python
# OLD: parse body text, then click each patient (slow)
patient_rows = await self._parse_schedule_rows(page, max_hour)
for patient_info in patient_rows:
    details = await self._click_patient_and_read_details(page, patient_info)

# NEW: parse DOM in one shot (fast)
appointments = await self._parse_schedule_dom(page)
```

### Step 5: Verify with real data

Before committing to the new approach, we need to verify a few things by examining the live schedule page:

- [ ] Confirm `td.schSlot` and `td.schtime` CSS classes are consistent across all rows
- [ ] Confirm `jsModApt()` parameter positions are consistent
- [ ] Check if empty/open slots have `td.schSlot` or use a different class
- [ ] Check what blocked/cancelled appointments look like in the DOM
- [ ] Confirm the schedule page URL — can we navigate to it directly?
- [ ] Check if multiple providers' schedules show on the same page or require switching

---

## What This Means for the Setup Wizard

The wizard redesign (keyboard/mouse recorder with image recognition) can be **deferred or eliminated entirely**. The DOM-first approach means:

| Old Requirement | New Reality |
|---|---|
| Record complex click sequence to reach schedule | Just need login + 2-3 nav clicks (or direct URL) |
| Record per-patient click sequence | Not needed — DOM has the data |
| Image recognition for screen elements | Not needed — CSS selectors are reliable |
| Keyboard/mouse recorder overlay | Not needed |
| Handle arbitrary webPRACTICE layouts | Just need the schedule page CSS classes confirmed |

The wizard simplifies to: **"Enter your NP credentials, and we'll handle the rest."**

However, the **navigation wizard is still needed** to get from the login page to the correct provider's schedule page. The user noted that:
- Different providers may have different schedule pages
- The schedule view supports 7-day and 30-day views
- The wizard should record the clicks needed to reach the correct schedule for a given provider

### Multi-Day Scraping (Friday Batch + Nightly Updates)

webPRACTICE supports 7-day and 30-day schedule views. This enables a powerful workflow:

1. **Friday evening batch scrape:** Switch to 7-day view, scrape Mon-Fri of next week in one pass
2. **Nightly quick update:** Switch back to 1-day view, scrape just tomorrow for any changes
3. **Result:** The dashboard has schedule data ready before the provider even arrives Monday morning

This requires the wizard to also record how to switch between 1-day/7-day/30-day views (likely a dropdown or button on the schedule page). The multi-day DOM structure probably keeps the same `td.schSlot` / `td.schtime` classes but adds date headers between day groups.

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| webPRACTICE changes CSS classes | Low (enterprise medical software doesn't change often) | CSS selectors are in config, easy to update |
| `jsModApt()` params change order | Very low | We validate by cross-checking name from params vs. DOM text |
| Some patients don't have onclick | Low | Fall back to text parsing for those rows |
| Chrome not started with CDP flag | Medium | restart.bat ensures Chrome starts with `--remote-debugging-port=9222` |
| Session expires mid-scrape | Low | Whole scrape is one page read now — takes 2 seconds |
| Multi-day view has different DOM | Medium | Need to verify with F12 on 7-day view; may need a separate parser |

---

## Next Steps

1. ~~Examine more rows~~ — **DONE** — 5 different appointment types confirmed consistent DOM structure
2. **Capture the schedule page URL** — Check if it's bookmarkable/directly navigable (still needed)
3. ~~Build `_parse_schedule_dom()`~~ — **DONE** — Scraper rewritten with DOM-first parsing
4. **Set up Chrome CDP** — Create a Chrome shortcut with `--remote-debugging-port=9222` for the office PC
5. **Test with one live scrape** — Run against real NetPractice with the new scraper
6. **Simplify the wizard UI** — Reduce to credentials + minimal nav steps to reach schedule
7. **Test 7-day / 30-day views** — F12 the multi-day schedule to confirm DOM structure
8. **Friday batch scraper** — Add method to scrape multiple days in one pass
