"""
NP Companion — CGM webPRACTICE Schedule Scraper

File location: np-companion/scrapers/netpractice.py

Uses Playwright to connect to Google Chrome (via CDP) and read the
day's appointment schedule directly from the DOM.

How it works (DOM-first approach):
  1. Connect to Chrome via Chrome DevTools Protocol (CDP) on port 9222
     — falls back to launching headless Chromium if Chrome isn't available
  2. Load saved session cookies (skip login if still valid)
  3. If login is needed: fill Client Number + Username + Password → Log In
  4. Replay the user's recorded navigation steps to reach the schedule page
  5. Read ALL appointments from the DOM in one pass using CSS selectors:
     - td.schSlot  → patient name, MRN, visit type, type code, units
     - td.schtime  → appointment time
     - No clicking into individual patients required
  6. Filter out blocked slots (DOCTOR OFF, etc.)
  7. Save all collected appointments to the database
  8. Save cookies for next run

Chrome CDP setup:
  Chrome must be started with: --remote-debugging-port=9222
  Create a desktop shortcut targeting:
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222

Session persistence:
  - Cookies are saved to data/np_session.pkl after each successful run.
  - On startup it loads saved cookies so it doesn't re-login every time.
  - If login fails, it sets a "needs_reauth" flag in data/np_reauth.json
    and sends a Pushover notification.

The scraper is called from the background agent (agent.py) on a schedule.

Usage:
    from scrapers.netpractice import NetPracticeScraper
    scraper = NetPracticeScraper(app)
    asyncio.run(scraper.scrape_today(user_id=1))
"""

import asyncio
import json
import logging
import os
import pickle
import re
from datetime import date, datetime, timedelta, timezone

logger = logging.getLogger('np_companion.scraper')


class NetPracticeScraper:
    """
    Playwright-based scraper for CGM webPRACTICE scheduling system.

    Connects to Chrome via CDP (Chrome DevTools Protocol) to read the
    schedule DOM directly.  Falls back to headless Chromium if Chrome
    CDP is unavailable.

    Parameters
    ----------
    app : Flask app instance
        Needed to read config values and access the database.
    """

    # Patterns used to identify blocked/non-patient slots
    BLOCKED_TITLES = {'DOCTOR OFF', 'LUNCH', 'MEETING', 'BLOCKED', 'BLOCK'}
    BLOCKED_NAME_PREFIXES = ('OFF,',)

    def __init__(self, app):
        self.app = app
        self.cookie_file = os.path.join(
            app.root_path,
            app.config.get('SESSION_COOKIE_FILE', 'data/np_session.pkl'),
        )
        self._reauth_file = os.path.join(app.root_path, 'data', 'np_reauth.json')
        self._settings_file = os.path.join(app.root_path, 'data', 'np_settings.json')
        self._cdp_port = app.config.get('CHROME_CDP_PORT', 9222)

    # ------------------------------------------------------------------
    # Settings reader
    # ------------------------------------------------------------------

    def _read_settings(self):
        """Read global NP settings from data/np_settings.json."""
        if not os.path.exists(self._settings_file):
            return {
                'netpractice_url': self.app.config.get('NETPRACTICE_URL', ''),
                'client_number': '',
                'scrape_time': '18:00',
                'max_appointment_hour': '19:00',
            }
        try:
            with open(self._settings_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {
                'netpractice_url': '',
                'client_number': '',
                'scrape_time': '18:00',
                'max_appointment_hour': '19:00',
            }

    # ==================================================================
    # Public methods
    # ==================================================================

    async def scrape_today(self, user_id):
        """Scrape today's schedule and store in the database."""
        await self._scrape_date(user_id, date.today())

    async def scrape_tomorrow(self, user_id):
        """Scrape tomorrow's schedule (called by nightly prep job)."""
        await self._scrape_date(user_id, date.today() + timedelta(days=1))

    async def health_check(self):
        """
        Quick check: can we reach webPRACTICE and is our session valid?

        Returns dict with keys: reachable, authenticated, connection_type, error
        """
        settings = self._read_settings()
        np_url = settings.get('netpractice_url', '')

        if not np_url:
            return {
                'reachable': False,
                'authenticated': False,
                'connection_type': None,
                'error': 'NetPractice URL not configured',
            }

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return {
                'reachable': False,
                'authenticated': False,
                'connection_type': None,
                'error': 'Playwright not installed',
            }

        try:
            async with async_playwright() as pw:
                browser, context, conn_type = await self._connect_browser(pw)
                page = await context.new_page()

                try:
                    await page.goto(np_url, timeout=15000)
                    needs_login = await self._is_login_page(page)

                    if needs_login:
                        self._set_reauth_flag(True)

                    return {
                        'reachable': True,
                        'authenticated': not needs_login,
                        'connection_type': conn_type,
                        'error': None,
                    }
                finally:
                    await page.close()
                    if conn_type == 'headless':
                        await browser.close()

        except Exception as e:
            logger.error(f'NetPractice health check failed: {e}')
            return {
                'reachable': False,
                'authenticated': False,
                'connection_type': None,
                'error': str(e),
            }

    async def clear_session(self):
        """Delete the saved cookie file and set reauth flag."""
        if os.path.exists(self.cookie_file):
            os.remove(self.cookie_file)
        self._set_reauth_flag(True)

    # ==================================================================
    # Re-auth flag helpers (read by Flask app for the header indicator)
    # ==================================================================

    def get_reauth_status(self):
        """Return re-auth state from data/np_reauth.json."""
        if not os.path.exists(self._reauth_file):
            return {
                'needs_reauth': False,
                'last_checked': None,
                'status': 'unknown',
            }
        try:
            with open(self._reauth_file, 'r') as f:
                data = json.load(f)
            return data
        except (json.JSONDecodeError, OSError):
            return {
                'needs_reauth': False,
                'last_checked': None,
                'status': 'unknown',
            }

    def _set_reauth_flag(self, needs_reauth):
        """Write the re-auth flag to disk so Flask can read it."""
        data = {
            'needs_reauth': needs_reauth,
            'last_checked': datetime.now(timezone.utc).isoformat(),
            'status': 'needs_reauth' if needs_reauth else 'ok',
        }
        os.makedirs(os.path.dirname(self._reauth_file), exist_ok=True)
        with open(self._reauth_file, 'w') as f:
            json.dump(data, f)

    # ==================================================================
    # Cookie management
    # ==================================================================

    async def _load_cookies(self, context):
        """Load saved cookies into a Playwright browser context."""
        if not os.path.exists(self.cookie_file):
            return
        try:
            with open(self.cookie_file, 'rb') as f:
                cookies = pickle.load(f)
            await context.add_cookies(cookies)
            logger.info('Loaded saved webPRACTICE session cookies')
        except Exception as e:
            logger.warning(f'Could not load session cookies: {e}')

    async def _save_cookies(self, context):
        """Save current cookies to disk for next run."""
        try:
            cookies = await context.cookies()
            os.makedirs(os.path.dirname(self.cookie_file), exist_ok=True)
            with open(self.cookie_file, 'wb') as f:
                pickle.dump(cookies, f)
            logger.info('Saved webPRACTICE session cookies')
        except Exception as e:
            logger.warning(f'Could not save session cookies: {e}')

    # ==================================================================
    # Login detection and login form filling
    # ==================================================================

    async def _is_login_page(self, page):
        """
        Check if the current page is the CGM webPRACTICE login form.
        Returns True if we see a password field (meaning login is needed).
        """
        try:
            password_field = page.locator('input[type="password"]')
            count = await password_field.count()
            return count > 0
        except Exception:
            return False

    async def _login(self, page, np_user, np_pass, client_number):
        """
        Fill in the CGM webPRACTICE login form and submit.

        The login page has three fields:
          - Client Number (pre-filled with the practice's number)
          - Username
          - Password
        And a "Log In" submit button.

        Returns True if login appeared successful, False otherwise.
        """
        logger.info('Filling webPRACTICE login form...')

        try:
            # Fill Client Number if configured
            if client_number:
                # Try multiple selector strategies for the client field
                client_field = page.locator(
                    'input[name*="lient" i]'  # matches "Client", "client_number", etc.
                ).first
                if await client_field.count():
                    await client_field.fill('')
                    await client_field.fill(client_number)
                    logger.info('Filled client number field')

            # Fill Username — look for text input near "Username" label
            user_field = page.locator(
                'input[name*="ser" i]'  # matches "User", "username", "UserName"
            ).first
            if await user_field.count():
                await user_field.fill(np_user)
                logger.info('Filled username field')
            else:
                # Fallback: try the first visible text input that isn't client number
                text_inputs = page.locator('input[type="text"]')
                count = await text_inputs.count()
                for i in range(count):
                    inp = text_inputs.nth(i)
                    name = await inp.get_attribute('name') or ''
                    if 'lient' not in name.lower():
                        await inp.fill(np_user)
                        logger.info('Filled username via fallback text input')
                        break

            # Fill Password
            pass_field = page.locator('input[type="password"]').first
            if await pass_field.count():
                await pass_field.fill(np_pass)
                logger.info('Filled password field')

            # Click the Log In button
            submit_btn = page.locator(
                'input[type="submit"], button[type="submit"]'
            ).first
            if await submit_btn.count():
                await submit_btn.click()
                logger.info('Clicked login button')
            else:
                # Fallback: press Enter on the password field
                await pass_field.press('Enter')
                logger.info('Pressed Enter to submit login form')

            # Wait for navigation after login
            await page.wait_for_load_state('networkidle', timeout=15000)

            # Check that we're past the login page
            still_on_login = await self._is_login_page(page)
            if still_on_login:
                logger.error('Still on login page after submitting — credentials may be wrong')
                return False

            logger.info('Login successful')
            return True

        except Exception as e:
            logger.error(f'Login failed: {e}')
            return False

    def _resolve_nav_value(self, value, provider_name):
        """
        Replace supported placeholders in a nav step value.

        Supported tokens:
          - {{NP_PROVIDER_NAME}}
          - {NP_PROVIDER_NAME}
          - [[NP_PROVIDER_NAME]]
          - $NP_PROVIDER_NAME
        """
        if not isinstance(value, str):
            return value

        if not provider_name:
            return value

        resolved = value
        tokens = (
            '{{NP_PROVIDER_NAME}}',
            '{NP_PROVIDER_NAME}',
            '[[NP_PROVIDER_NAME]]',
            '$NP_PROVIDER_NAME',
        )
        for token in tokens:
            resolved = resolved.replace(token, provider_name)
        return resolved

    def _normalize_nav_selector(self, selector):
        """Normalize recorder-style selectors to Playwright selector syntax."""
        if not isinstance(selector, str):
            return selector

        if selector.startswith('xpath//'):
            # Recorder exports selectors like "xpath///*[@id=...]".
            return f'xpath={selector[len("xpath"):]}'
        return selector

    def _all_click_contexts(self, page):
        """
        Return page + all child frames so clicks can work in framed UIs.
        """
        contexts = [page]
        try:
            contexts.extend([f for f in page.frames if f != page.main_frame])
        except Exception:
            pass
        return contexts

    async def _click_text_in_any_context(self, page, text_target):
        """Click text in page or any child frame."""
        for ctx in self._all_click_contexts(page):
            try:
                candidate = ctx.get_by_text(text_target, exact=False).first
                if await candidate.count():
                    await candidate.click()
                    return True

                link = ctx.locator('a').filter(has_text=text_target).first
                if await link.count():
                    await link.click()
                    return True
            except Exception:
                continue
        return False

    async def _click_selector_in_any_context(self, page, selector):
        """Click a CSS/XPath selector in page or any child frame."""
        selector = self._normalize_nav_selector(selector)
        for ctx in self._all_click_contexts(page):
            try:
                element = ctx.locator(selector).first
                if await element.count():
                    await element.click()
                    return True
            except Exception:
                continue
        return False

    async def _wait_for_any_context(self, page, wait_for, timeout_ms=10000):
        """Wait for text or selector across page + frames."""
        if wait_for.startswith('text='):
            expected_text = wait_for[5:]
            for ctx in self._all_click_contexts(page):
                try:
                    await ctx.get_by_text(expected_text, exact=False).first.wait_for(
                        state='visible', timeout=timeout_ms
                    )
                    return True
                except Exception:
                    continue
            return False

        selector = self._normalize_nav_selector(wait_for)
        for ctx in self._all_click_contexts(page):
            try:
                await ctx.locator(selector).first.wait_for(
                    state='visible', timeout=timeout_ms
                )
                return True
            except Exception:
                continue
        return False

    # ==================================================================
    # Navigation step replay
    # ==================================================================

    async def _replay_nav_steps(self, page, steps, provider_name=''):
        """
        Replay the user's recorded navigation steps to reach the schedule.

        Each step is a dict with:
          - action: "click_text", "click", "wait", "navigate"
          - target: the text to click or URL to navigate to
          - wait_for: optional text or selector to wait for after the action
          - description: human-readable description (for logging)

        Returns True if all steps succeeded, False on failure.
        """
        if not steps:
            logger.warning('No navigation steps defined — cannot reach schedule')
            return False

        for step in steps:
            action = step.get('action', 'click_text')
            raw_target = step.get('target', '')
            raw_wait_for = step.get('wait_for', '')
            target = self._resolve_nav_value(raw_target, provider_name)
            wait_for = self._resolve_nav_value(raw_wait_for, provider_name)
            desc = self._resolve_nav_value(
                step.get('description', f'{action}: {target}'),
                provider_name,
            )
            order = step.get('order', '?')

            logger.info(f'Nav step {order}: {desc}')

            try:
                if action == 'click_text':
                    clicked = await self._click_text_in_any_context(page, target)
                    if not clicked:
                        logger.error(f'Could not find text "{target}" to click')
                        return False

                elif action == 'click':
                    # Allow recorder-style text selectors in "click" mode too.
                    if isinstance(target, str) and target.startswith('aria/'):
                        label = target[5:].split('[', 1)[0].strip()
                        if label:
                            clicked = await self._click_text_in_any_context(page, label)
                            if not clicked:
                                logger.error(f'Could not find aria target "{target}"')
                                return False
                        else:
                            logger.error(f'Invalid aria target "{target}"')
                            return False
                    elif isinstance(target, str) and target.startswith('text/'):
                        text_target = target[5:].strip()
                        clicked = await self._click_text_in_any_context(page, text_target)
                        if not clicked:
                            logger.error(f'Could not find text target "{target}"')
                            return False
                    else:
                        clicked = await self._click_selector_in_any_context(page, target)
                        if not clicked:
                            logger.error(f'Could not find element "{target}"')
                            return False

                elif action == 'navigate':
                    # Go to a specific URL
                    await page.goto(target, timeout=15000)

                elif action == 'wait':
                    # Just wait for something to appear
                    pass  # handled below by wait_for

                # Wait for the expected result after the action
                if wait_for:
                    try:
                        ok = await self._wait_for_any_context(page, wait_for, timeout_ms=10000)
                        if not ok:
                            raise RuntimeError('condition not visible in page or frames')
                    except Exception as wait_err:
                        logger.warning(
                            f'Wait condition "{wait_for}" not met after step {order}: {wait_err}'
                        )
                        # Don't fail — the step may have worked anyway
                else:
                    # Default: wait for network to settle
                    await page.wait_for_load_state('networkidle', timeout=10000)

            except Exception as e:
                logger.error(f'Navigation step {order} failed: {e}')
                return False

        logger.info('All navigation steps completed')
        return True

    # ==================================================================
    # Date navigation (for scraping tomorrow or other dates)
    # ==================================================================

    async def _navigate_to_date(self, page, target_date):
        """
        Navigate the schedule calendar to a specific date.

        If target_date is today, no navigation needed (schedule defaults to today).
        Otherwise, click the forward/back buttons or use the calendar widget.

        The webPRACTICE calendar has:
          - A "Today" button
          - Forward (>) and back (<) arrows for day-by-day navigation
        """
        today = date.today()

        if target_date == today:
            logger.info('Target date is today — no calendar navigation needed')
            return True

        delta_days = (target_date - today).days

        if abs(delta_days) > 7:
            logger.warning(
                f'Target date is {abs(delta_days)} days away — '
                f'only nearby dates are supported via arrow navigation'
            )

        try:
            if delta_days > 0:
                # Click the forward arrow for each day
                for i in range(delta_days):
                    # Look for a forward/next day button
                    forward_btn = page.get_by_text('>', exact=True).first
                    if not await forward_btn.count():
                        forward_btn = page.locator(
                            'a:has-text(">"), input[value=">"], '
                            'button:has-text(">")'
                        ).first
                    if await forward_btn.count():
                        await forward_btn.click()
                        await page.wait_for_load_state('networkidle', timeout=10000)
                    else:
                        logger.error('Could not find forward calendar button')
                        return False
            else:
                # Click the back arrow for each day
                for i in range(abs(delta_days)):
                    back_btn = page.get_by_text('<', exact=True).first
                    if not await back_btn.count():
                        back_btn = page.locator(
                            'a:has-text("<"), input[value="<"], '
                            'button:has-text("<")'
                        ).first
                    if await back_btn.count():
                        await back_btn.click()
                        await page.wait_for_load_state('networkidle', timeout=10000)
                    else:
                        logger.error('Could not find back calendar button')
                        return False

            logger.info(f'Navigated calendar to {target_date}')
            return True

        except Exception as e:
            logger.error(f'Date navigation failed: {e}')
            return False

    # ==================================================================
    # Schedule parsing — DOM-first approach (reads everything in one pass)
    # ==================================================================

    async def _parse_schedule_dom(self, page, max_hour_str):
        """
        Parse the schedule page by reading CSS selectors directly from the DOM.

        Each appointment row is a <tr> containing:
          - td.schtime  → time in <font> tag (e.g. "08:45A")
          - td.schSlot  → patient data in title, onclick, and inner text

        The onclick attribute contains jsModApt() with structured params:
          jsModApt('resource','provider_id','?','HH:MM','type_code','units','NAME','day_start','row')

        Returns a list of dicts with appointment data.
        Blocked slots (DOCTOR OFF, etc.) are excluded from the patient list
        but returned separately.
        """
        try:
            max_hour = int(max_hour_str.split(':')[0])
        except (ValueError, AttributeError, IndexError):
            max_hour = 19

        appointments = []
        blocked_slots = []

        # Find all schedule rows: each <tr> inside a table with id starting with "schblock"
        rows = await page.query_selector_all('table[id^="schblock"] tbody tr')

        if not rows:
            # Fallback: try finding rows by the td classes directly
            rows = await page.query_selector_all('tr:has(td.schSlot)')

        logger.info(f'Found {len(rows)} schedule rows in DOM')

        for row in rows:
            try:
                # Get the time cell
                time_td = await row.query_selector('td.schtime')
                slot_td = await row.query_selector('td.schSlot')

                if not slot_td:
                    continue  # Not a schedule row

                # --- Extract time ---
                time_text = ''
                if time_td:
                    font_el = await time_td.query_selector('font')
                    if font_el:
                        time_text = (await font_el.inner_text()).strip()
                    else:
                        time_text = (await time_td.inner_text()).strip()

                # Check max hour cutoff
                appt_hour = self._parse_time_to_hour(time_text)
                if appt_hour is not None and appt_hour >= max_hour:
                    logger.info(f'Stopping at {time_text} — past max hour {max_hour_str}')
                    break

                # --- Extract visit type from title attribute ---
                visit_type = (await slot_td.get_attribute('title')) or ''

                # --- Extract onclick params ---
                onclick = (await slot_td.get_attribute('onclick')) or ''
                params = self._parse_jsmodapt(onclick)

                # --- Extract patient name + MRN from inner text ---
                slot_text = (await slot_td.inner_text()).strip()
                name, mrn = self._extract_name_mrn(slot_text)

                # --- Extract background color (encodes visit type category) ---
                style = (await slot_td.get_attribute('style')) or ''
                bg_color = self._extract_bg_color(style)

                # --- Extract verification status ---
                verify_img = await slot_td.query_selector('img[src*="verifyStatus"]')
                verification = ''
                if verify_img:
                    verification = (await verify_img.get_attribute('title')) or ''

                # --- Check if this is a blocked slot ---
                is_blocked = self._is_blocked_slot(visit_type, name, params)

                appt_data = {
                    'time': time_text,
                    'patient_name': name if not is_blocked else '',
                    'patient_mrn': mrn if not is_blocked else '',
                    'visit_type': visit_type,
                    'visit_type_code': params.get('type_code', ''),
                    'units': params.get('units', 1),
                    'duration_minutes': params.get('units', 1) * 15,
                    'provider_id': params.get('provider_id', ''),
                    'bg_color': bg_color,
                    'verification': verification,
                    'row_index': params.get('row_index', ''),
                    'is_blocked': is_blocked,
                    'blocked_reason': visit_type if is_blocked else '',
                }

                if is_blocked:
                    blocked_slots.append(appt_data)
                    logger.debug(f'Blocked slot at {time_text}: {visit_type}')
                elif name:
                    appointments.append(appt_data)
                # Skip rows with no patient name and not blocked (empty slots)

            except Exception as e:
                logger.warning(f'Error parsing schedule row: {e}')
                continue

        logger.info(
            f'Parsed {len(appointments)} patients + {len(blocked_slots)} blocked slots '
            f'from DOM (max hour: {max_hour_str})'
        )
        return appointments, blocked_slots

    # ------------------------------------------------------------------
    # jsModApt() parameter parser
    # ------------------------------------------------------------------

    def _parse_jsmodapt(self, onclick_str):
        """
        Extract structured data from the jsModApt onclick handler.

        Format: jsModApt('48','67642','2','08:00','PE','1','FAILLA, SALV','28800','1')
                          res  prov    ?   time    code units name          daystart row

        Returns a dict with named fields, or empty dict if parsing fails.
        """
        match = re.search(r"jsModApt\((.+?)\)", onclick_str)
        if not match:
            return {}

        # Split on commas, strip quotes and whitespace
        parts = [p.strip().strip("'\"") for p in match.group(1).split(',')]

        if len(parts) >= 7:
            units_raw = parts[5]
            return {
                'resource_id': parts[0],
                'provider_id': parts[1],
                'param_3': parts[2],
                'time': parts[3],
                'type_code': parts[4],
                'units': int(units_raw) if units_raw.isdigit() else 1,
                'patient_name': parts[6],
                'day_start_seconds': parts[7] if len(parts) > 7 else '',
                'row_index': parts[8] if len(parts) > 8 else '',
            }
        return {}

    # ------------------------------------------------------------------
    # Name + MRN extraction from slot text
    # ------------------------------------------------------------------

    def _extract_name_mrn(self, text):
        """
        Extract patient name and MRN from the schedule slot text.

        The text looks like: " FORDEN, BRANDY (36234)"
        or sometimes: "OFF, DR (41657)"

        Returns (name, mrn) tuple. Both empty strings if no match.
        """
        # Remove non-breaking spaces and extra whitespace
        text = text.replace('\xa0', ' ').strip()

        # Match: NAME, NAME (MRN)
        match = re.search(r'([A-Z][A-Z\s\.\'\-]+,\s*[A-Z][A-Z\s\.\'\-]*)\s*\((\d+)\)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip(), match.group(2).strip()

        return '', ''

    # ------------------------------------------------------------------
    # Background color extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_bg_color(style_str):
        """Extract background-color hex value from inline style string."""
        match = re.search(r'background-color:\s*([#\w]+)', style_str, re.IGNORECASE)
        return match.group(1) if match else ''

    # ------------------------------------------------------------------
    # Blocked slot detection
    # ------------------------------------------------------------------

    def _is_blocked_slot(self, visit_type, patient_name, params):
        """
        Determine if a schedule slot is a blocked/non-patient entry.

        Blocked indicators:
        - title is "DOCTOR OFF", "LUNCH", "MEETING", "BLOCKED", etc.
        - Patient name starts with "OFF," (e.g. "OFF, DR")
        - Empty visit type code with name pattern "OFF, *"
        """
        # Check title against known blocked types
        if visit_type.upper() in self.BLOCKED_TITLES:
            return True

        # Check name pattern
        name_upper = patient_name.upper().strip()
        for prefix in self.BLOCKED_NAME_PREFIXES:
            if name_upper.startswith(prefix):
                return True

        return False

    def _parse_time_to_hour(self, time_str):
        """
        Convert a webPRACTICE time string to 24-hour format hour.
        Examples: "8:00A" → 8, "1:30P" → 13, "12:00P" → 12
        """
        try:
            time_str = time_str.strip().upper()
            is_pm = time_str.endswith('P')
            is_am = time_str.endswith('A')
            numeric = time_str.rstrip('AP')
            parts = numeric.split(':')
            hour = int(parts[0])

            if is_pm and hour != 12:
                hour += 12
            elif is_am and hour == 12:
                hour = 0

            return hour
        except (ValueError, IndexError):
            return None

    # ==================================================================
    # Optional: Click patient for detail enrichment (only when needed)
    # ==================================================================

    async def _enrich_patient_details(self, page, patient_info):
        """
        Click a patient's name on the schedule page, read the detail page,
        then go back.  Only call this for patients where we need extra data
        (e.g. new patients, physicals) — NOT for every patient.

        The detail page shows: DOB, Phone, Reason, Comment, Status,
        Location, New Patient Y/N, Entered By.

        Returns a dict with extracted fields (empty dict on failure).
        """
        details = {}
        name = patient_info.get('patient_name', '')
        mrn = patient_info.get('patient_mrn', '')

        try:
            if mrn:
                link = page.get_by_text(f'({mrn})', exact=False).first
            else:
                link = page.get_by_text(name, exact=False).first

            if not await link.count():
                logger.warning(f'Could not find clickable link for patient: {name}')
                return details

            await link.click()
            await page.wait_for_load_state('networkidle', timeout=10000)

            page_text = await page.inner_text('body')
            details = self._extract_detail_fields(page_text)

            await page.go_back(timeout=10000)
            await page.wait_for_load_state('networkidle', timeout=10000)

            logger.info(f'Enriched details for: {name} (MRN: {mrn})')

        except Exception as e:
            logger.error(f'Error enriching details for {name}: {e}')
            try:
                await page.go_back(timeout=5000)
                await page.wait_for_load_state('networkidle', timeout=5000)
            except Exception:
                pass

        return details

    def _extract_detail_fields(self, page_text):
        """
        Parse the appointment detail page text to extract all fields.

        Returns a dict of extracted fields.
        """
        fields = {}

        def find_field(label):
            pattern = re.compile(
                rf'{re.escape(label)}\s*[:\s]\s*(.+?)(?:\n|$)',
                re.IGNORECASE
            )
            match = pattern.search(page_text)
            return match.group(1).strip() if match else ''

        fields['visit_type'] = find_field('Type of Visit')
        fields['status'] = find_field('Status')
        fields['reason'] = find_field('Reason')
        fields['location'] = find_field('Location')
        fields['comment'] = find_field('Comment')
        fields['provider_name'] = find_field('Doctor')
        fields['patient_dob'] = find_field('Date of Birth')
        fields['patient_phone'] = find_field('Phone')

        units_str = find_field('Units')
        try:
            fields['units'] = int(units_str) if units_str else 1
        except ValueError:
            fields['units'] = 1

        new_patient = find_field('New Patient')
        fields['is_new_patient_flag'] = new_patient.upper().startswith('Y')

        fields['patient_number'] = find_field('Patient Number')

        entered_match = re.search(
            r'Entered by\s+(.+?)\s+on\s+\d',
            page_text,
            re.IGNORECASE
        )
        fields['entered_by'] = entered_match.group(1).strip() if entered_match else ''

        return fields

    # ==================================================================
    # Browser connection — Chrome CDP preferred, headless fallback
    # ==================================================================

    async def _connect_browser(self, pw):
        """
        Connect to Chrome via CDP if available, otherwise launch headless Chromium.

        Returns (browser, context, connection_type) tuple.
        connection_type is 'cdp' or 'headless'.
        """
        # Try Chrome CDP first
        cdp_url = f'http://127.0.0.1:{self._cdp_port}'
        try:
            browser = await pw.chromium.connect_over_cdp(cdp_url)
            # CDP gives us the default context (the user's existing Chrome)
            contexts = browser.contexts
            if contexts:
                context = contexts[0]
            else:
                context = await browser.new_context()
            logger.info(f'Connected to Chrome via CDP on port {self._cdp_port}')
            return browser, context, 'cdp'
        except Exception as e:
            logger.info(f'Chrome CDP not available ({e}) — launching headless Chromium')

        # Fallback: launch headless Chromium
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        await self._load_cookies(context)
        return browser, context, 'headless'

    # ==================================================================
    # Core scraping logic — DOM-first approach
    # ==================================================================

    async def _scrape_date(self, user_id, target_date):
        """
        Scrape all appointments for a given date and save to the database.

        Steps:
        1. Load user's credentials and nav steps from database
        2. Connect to Chrome via CDP (or launch headless Chromium)
        3. Navigate to webPRACTICE URL
        4. If login page shown → fill Client Number/Username/Password and submit
        5. Replay user's navigation steps to reach the schedule page
        6. Navigate to the target date if needed
        7. Parse the entire schedule DOM in one pass (no per-patient clicking)
        8. Optionally enrich new/complex patients with detail page clicks
        9. Save all collected appointments to database
        10. Save cookies for next run
        """
        settings = self._read_settings()
        np_url = settings.get('netpractice_url', '')
        client_number = settings.get('client_number', '')
        max_hour = settings.get('max_appointment_hour', '19:00')

        if not np_url:
            logger.warning('NetPractice URL not configured — skipping scrape')
            return

        # Load user's credentials and nav steps from the database
        with self.app.app_context():
            from models.user import User
            user = User.query.get(user_id)
            if not user:
                logger.error(f'User {user_id} not found')
                return
            if not user.has_np_credentials():
                logger.warning(f'User {user.username} has no NP credentials — skipping')
                return

            np_user = user.get_np_username()
            np_pass = user.get_np_password()
            nav_steps = user.nav_steps
            provider_name = user.np_provider_name or ''

        if not nav_steps:
            logger.warning(f'User {user_id} has no navigation steps configured — skipping')
            return

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error('Playwright not installed — cannot scrape')
            return

        logger.info(f'Starting schedule scrape for {target_date} (user {user_id})')

        try:
            async with async_playwright() as pw:
                browser, context, conn_type = await self._connect_browser(pw)
                page = await context.new_page()

                try:
                    # Step 1: Go to webPRACTICE
                    await page.goto(np_url, timeout=20000)
                    await page.wait_for_load_state('networkidle', timeout=15000)

                    # Step 2: Check if we need to log in
                    needs_login = await self._is_login_page(page)
                    if needs_login:
                        logger.info('Login page detected — entering credentials')
                        login_ok = await self._login(page, np_user, np_pass, client_number)
                        if not login_ok:
                            logger.error('Login failed — setting reauth flag')
                            self._set_reauth_flag(True)
                            return
                    else:
                        logger.info('Session still valid — skipping login')

                    self._set_reauth_flag(False)

                    # Step 3: Replay navigation steps to reach schedule page
                    nav_ok = await self._replay_nav_steps(page, nav_steps, provider_name)
                    if not nav_ok:
                        logger.error('Navigation to schedule page failed')
                        if conn_type == 'headless':
                            await self._save_cookies(context)
                        return

                    # Step 4: Navigate to the target date if not today
                    date_ok = await self._navigate_to_date(page, target_date)
                    if not date_ok:
                        logger.error('Could not navigate to target date')
                        if conn_type == 'headless':
                            await self._save_cookies(context)
                        return

                    # Step 5: Verify we're on the right schedule page
                    if provider_name:
                        body_text = await page.inner_text('body')
                        if provider_name.upper() not in body_text.upper():
                            logger.warning(
                                f'Provider name "{provider_name}" not found on schedule page'
                            )

                    # Step 6: Parse the ENTIRE schedule from the DOM in one pass
                    appointments, blocked_slots = await self._parse_schedule_dom(page, max_hour)
                    logger.info(
                        f'DOM parse complete: {len(appointments)} patients, '
                        f'{len(blocked_slots)} blocked slots'
                    )

                    # Step 7: Build appointment records for database
                    raw_appointments = []
                    for appt in appointments:
                        raw_appointments.append({
                            'time': appt.get('time', ''),
                            'patient_name': appt.get('patient_name', ''),
                            'patient_mrn': appt.get('patient_mrn', ''),
                            'visit_type': appt.get('visit_type', ''),
                            'visit_type_code': appt.get('visit_type_code', ''),
                            'units': appt.get('units', 1),
                            'duration_minutes': appt.get('duration_minutes', 15),
                            'provider_name': provider_name,
                            'bg_color': appt.get('bg_color', ''),
                            'verification': appt.get('verification', ''),
                            # Fields that require detail page click (empty for now)
                            'patient_dob': '',
                            'patient_phone': '',
                            'reason': '',
                            'location': '',
                            'status': 'scheduled',
                            'comment': '',
                            'entered_by': '',
                            'is_new_patient_flag': False,
                        })

                    # Step 8: Save cookies (headless mode only — CDP shares Chrome's cookies)
                    if conn_type == 'headless':
                        await self._save_cookies(context)

                finally:
                    # Close the tab we opened, not the whole browser
                    await page.close()
                    if conn_type == 'headless':
                        await browser.close()

            # Step 9: Store in database
            self._store_appointments(user_id, target_date, raw_appointments)
            logger.info(
                f'Scrape complete: {len(raw_appointments)} appointments for {target_date}'
            )

        except Exception as e:
            logger.error(f'Schedule scrape failed for {target_date}: {e}')

    # ==================================================================
    # Database storage
    # ==================================================================

    def _store_appointments(self, user_id, target_date, raw_appointments):
        """
        Save scraped appointments to the database.

        - Deletes existing rows for that user + date (full replace strategy)
        - Detects new patients by checking if the name has appeared before
          AND by reading the "New Patient: Y/N" flag from the detail page
        """
        with self.app.app_context():
            from models import db
            from models.schedule import Schedule

            # Remove old rows for this date so we always have fresh data
            Schedule.query.filter_by(
                user_id=user_id,
                appointment_date=target_date,
            ).delete()
            db.session.flush()

            # Get all patient names this user has previously seen
            past_names = set(
                row[0].strip().lower()
                for row in db.session.query(Schedule.patient_name)
                .filter(
                    Schedule.user_id == user_id,
                    Schedule.appointment_date < target_date,
                    Schedule.patient_name != '',
                )
                .distinct()
                .all()
            )

            for appt in raw_appointments:
                name = appt.get('patient_name', '').strip()
                # New patient if: detail page says "Y" OR name never seen before
                is_new = appt.get('is_new_patient_flag', False)
                if not is_new and name:
                    is_new = name.lower() not in past_names

                # Convert time format from "10:00A" to "10:00 AM" for consistency
                raw_time = appt.get('time', '')

                schedule_row = Schedule(
                    user_id=user_id,
                    appointment_date=target_date,
                    appointment_time=raw_time,
                    patient_name=name,
                    patient_mrn=appt.get('patient_mrn', ''),
                    patient_dob=appt.get('patient_dob', ''),
                    patient_phone=appt.get('patient_phone', ''),
                    visit_type=appt.get('visit_type', ''),
                    visit_type_code=appt.get('visit_type_code', ''),
                    reason=appt.get('reason', ''),
                    duration_minutes=appt.get('duration_minutes', appt.get('units', 1) * 15),
                    units=appt.get('units', 1),
                    provider_name=appt.get('provider_name', ''),
                    location=appt.get('location', ''),
                    status=appt.get('status', 'scheduled'),
                    comment=appt.get('comment', ''),
                    entered_by=appt.get('entered_by', ''),
                    is_new_patient=is_new,
                    bg_color=appt.get('bg_color', ''),
                    verification=appt.get('verification', ''),
                    anomaly_flags='[]',
                )
                db.session.add(schedule_row)

            db.session.commit()

            # F15a: Evaluate care gaps for each scraped patient
            self._evaluate_care_gaps_for_appointments(user_id, raw_appointments)

    # ==================================================================
    # F15a: Care Gap Evaluation after schedule scrape
    # ==================================================================

    def _evaluate_care_gaps_for_appointments(self, user_id, appointments):
        """
        After scraping the schedule, evaluate care gaps for each patient.
        Creates new CareGap records for gaps not already tracked.
        """
        try:
            from agent.caregap_engine import evaluate_and_persist_gaps
            from models.patient import PatientDiagnosis

            for appt in appointments:
                mrn = appt.get('patient_mrn', '')
                if not mrn:
                    continue

                # Build patient_data for the engine
                dob = appt.get('patient_dob', '')
                patient_name = appt.get('patient_name', '')

                # Get known diagnoses from parsed clinical summaries
                diagnoses = []
                try:
                    diag_records = PatientDiagnosis.query.filter_by(
                        user_id=user_id, mrn=mrn, status='active'
                    ).all()
                    diagnoses = [d.diagnosis_name for d in diag_records]
                except Exception:
                    pass

                patient_data = {
                    'mrn': mrn,
                    'dob': dob,
                    'age': None,  # engine calculates from dob
                    'sex': '',    # populated from clinical data if available
                    'patient_name': patient_name,
                    'known_diagnoses': diagnoses,
                }

                evaluate_and_persist_gaps(user_id, mrn, patient_data, self.app)

            logger.info(
                'Care gap evaluation complete for %d patients (user %d)',
                len(appointments), user_id,
            )
        except Exception as e:
            logger.warning('Care gap evaluation failed: %s', e)

    # ==================================================================
    # Live MRN extraction — read MRN from whichever NP page is open
    # ==================================================================

    async def get_current_patient_mrn(self):
        """
        Connect to the user's running Chrome via CDP and extract the
        patient MRN from whatever NetPractice page is currently open.

        Checks all pages/tabs for known NP URL patterns and scrapes
        the DOM for a patient ID field. Returns (mrn, name) or (None, None).
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.debug('Playwright not installed — NP MRN extraction unavailable')
            return None, None

        try:
            async with async_playwright() as pw:
                cdp_url = f'http://127.0.0.1:{self._cdp_port}'
                browser = await pw.chromium.connect_over_cdp(cdp_url)
                contexts = browser.contexts
                if not contexts:
                    return None, None

                for ctx in contexts:
                    for page in ctx.pages:
                        url = page.url or ''
                        # Only inspect NP / webPRACTICE pages
                        if 'cgmus.com' not in url and 'webpractice' not in url.lower():
                            continue

                        # Try to find patient ID in page text
                        text = await page.inner_text('body')
                        mrn_match = re.search(
                            r'(?:Patient\s+ID|ID)[:\s#]*(\d{3,})', text
                        )
                        name_match = re.search(
                            r'([A-Z][A-Z\s.\'-]+,\s*[A-Z][A-Z\s.\'-]+)',
                            text
                        )
                        if mrn_match:
                            mrn = mrn_match.group(1)
                            name = name_match.group(1).strip() if name_match else ''
                            return mrn, name

                return None, None
        except Exception as e:
            logger.debug(f'NP MRN extraction failed: {e}')
            return None, None
