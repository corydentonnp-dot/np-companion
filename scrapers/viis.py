"""
CareCompanion — Virginia Immunization Information System (VIIS) Scraper
File: scrapers/viis.py

Uses Playwright to automate login and patient lookup on the Virginia
Immunization Information System (VIIS) portal.

Architecture follows the same pattern as scrapers/pdmp.py:
  1. Connect to Chrome via CDP or launch headless Chromium
  2. Login with stored credentials (VIIS_USERNAME, VIIS_PASSWORD from config.py)
  3. Search for patient by name + DOB
  4. Extract immunization history from results page
  5. Return structured data for display in the patient chart

HIPAA note: Patient name and DOB are sent to the VIIS portal (this is
a state-authorized clinical lookup, required by Virginia law for
immunization reporting).

Usage:
    from scrapers.viis import VIISScraper
    scraper = VIISScraper(app)
    result = asyncio.run(scraper.lookup_patient(
        first_name='John', last_name='Smith', dob='1960-01-15'
    ))
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger('carecompanion.viis')


class VIISScraper:
    """
    Playwright-based scraper for Virginia Immunization Information System.

    Parameters
    ----------
    app : Flask app instance
        Needed to read config values.
    """

    def __init__(self, app):
        self.app = app
        self._cookie_file = os.path.join(app.root_path, 'data', 'viis_session.pkl')
        self._cdp_port = app.config.get('CHROME_CDP_PORT', 9222)
        self._url = app.config.get('VIIS_URL', 'https://viis.virginia.gov')
        self._username = app.config.get('VIIS_USERNAME', '')
        self._password = app.config.get('VIIS_PASSWORD', '')

    async def lookup_patient(self, first_name, last_name, dob):
        """
        Look up a patient's immunization history in VIIS.

        Parameters
        ----------
        first_name : str
        last_name : str
        dob : str
            Date of birth in YYYY-MM-DD format.

        Returns
        -------
        dict with:
            'success': bool
            'immunizations': list of dicts (vaccine, date, manufacturer, lot, site, provider)
            'error': str
            'checked_at': ISO timestamp
        """
        if not self._username or not self._password:
            return {
                'success': False,
                'immunizations': [],
                'error': 'VIIS credentials not configured in config.py',
                'checked_at': datetime.now(timezone.utc).isoformat(),
            }

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return {
                'success': False,
                'immunizations': [],
                'error': 'Playwright not installed',
                'checked_at': datetime.now(timezone.utc).isoformat(),
            }

        result = {
            'success': False,
            'immunizations': [],
            'error': '',
            'checked_at': datetime.now(timezone.utc).isoformat(),
        }

        async with async_playwright() as pw:
            browser = None
            try:
                cdp_url = f'http://127.0.0.1:{self._cdp_port}'
                try:
                    browser = await pw.chromium.connect_over_cdp(cdp_url)
                    logger.info('VIIS: connected via Chrome CDP')
                except Exception:
                    # Auto-launch Chrome debug profile and retry
                    try:
                        from utils.chrome_launcher import ensure_chrome_debug
                        import asyncio
                        exe = self.app.config.get('CHROME_EXE_PATH', '')
                        pdir = self.app.config.get('CHROME_DEBUG_PROFILE_DIR', '')
                        if exe and pdir and ensure_chrome_debug(exe, pdir, self._cdp_port):
                            await asyncio.sleep(3)
                            try:
                                browser = await pw.chromium.connect_over_cdp(cdp_url)
                                logger.info('VIIS: connected via CDP after auto-launch')
                            except Exception:
                                browser = None
                    except ImportError:
                        pass
                    if browser is None:
                        browser = await pw.chromium.launch(headless=True)
                        logger.info('VIIS: launched headless Chromium')

                context = await browser.new_context()
                await self._load_cookies(context)

                page = await context.new_page()
                page.set_default_timeout(15000)

                # Navigate to VIIS
                await page.goto(self._url, wait_until='domcontentloaded')

                # Login if needed
                if await self._needs_login(page):
                    await self._do_login(page)

                # Search for patient
                await self._search_patient(page, first_name, last_name, dob)

                # Extract immunization history
                immunizations = await self._extract_immunizations(page)

                await self._save_cookies(context)

                result['success'] = True
                result['immunizations'] = immunizations

            except Exception as e:
                logger.warning('VIIS lookup failed: %s', str(e))
                result['error'] = str(e)
            finally:
                if browser:
                    try:
                        await browser.close()
                    except Exception:
                        pass

        return result

    async def _needs_login(self, page):
        """Check if the current page is a login page."""
        url = page.url.lower()
        content = await page.content()
        return 'login' in url or 'sign in' in content.lower() or 'username' in content.lower()

    async def _do_login(self, page):
        """Fill login form and submit."""
        logger.info('VIIS: logging in as %s', self._username)

        # Username field
        for sel in ['input[name*="user" i]', 'input[id*="user" i]', 'input[type="text"]:first-of-type']:
            el = page.locator(sel).first
            if await el.count() > 0:
                await el.fill(self._username)
                break

        # Password field
        pwd_sel = 'input[type="password"]'
        await page.fill(pwd_sel, self._password)

        # Submit
        for sel in ['button[type="submit"]', 'input[type="submit"]',
                     'button:has-text("Log In")', 'button:has-text("Sign In")', 'button:has-text("Submit")']:
            el = page.locator(sel).first
            if await el.count() > 0:
                await el.click()
                break

        await page.wait_for_load_state('domcontentloaded')
        await page.wait_for_timeout(2000)

        if await self._needs_login(page):
            raise Exception('VIIS login failed — check credentials')

        logger.info('VIIS: login successful')

    async def _search_patient(self, page, first_name, last_name, dob):
        """Navigate to patient search and fill the form."""
        await page.wait_for_timeout(1000)

        # Try to find patient search page link/nav
        for sel in ['a:has-text("Patient")', 'a:has-text("Search")', 'a:has-text("Client")']:
            el = page.locator(sel).first
            if await el.count() > 0:
                await el.click()
                await page.wait_for_load_state('domcontentloaded')
                break

        await page.wait_for_timeout(1000)

        # Fill search fields
        for sel in ['input[name*="last" i]', 'input[id*="last" i]']:
            el = page.locator(sel).first
            if await el.count() > 0:
                await el.fill(last_name)
                break

        for sel in ['input[name*="first" i]', 'input[id*="first" i]']:
            el = page.locator(sel).first
            if await el.count() > 0:
                await el.fill(first_name)
                break

        # DOB
        for sel in ['input[name*="dob" i]', 'input[name*="birth" i]', 'input[type="date"]']:
            el = page.locator(sel).first
            if await el.count() > 0:
                try:
                    d = datetime.strptime(dob, '%Y-%m-%d')
                    await el.fill(d.strftime('%m/%d/%Y'))
                except ValueError:
                    await el.fill(dob)
                break

        # Submit search
        for sel in ['button[type="submit"]', 'button:has-text("Search")', 'input[type="submit"]']:
            el = page.locator(sel).first
            if await el.count() > 0:
                await el.click()
                break

        await page.wait_for_load_state('domcontentloaded')
        await page.wait_for_timeout(3000)

    async def _extract_immunizations(self, page):
        """Extract immunization records from results page."""
        immunizations = []

        try:
            await page.wait_for_timeout(2000)

            # Click into patient record if needed (search may return a list)
            patient_links = await page.query_selector_all('a[href*="patient"], a[href*="client"], tr[onclick]')
            if patient_links:
                await patient_links[0].click()
                await page.wait_for_load_state('domcontentloaded')
                await page.wait_for_timeout(2000)

            # Look for immunization history link
            for sel in ['a:has-text("Immunization")', 'a:has-text("Vaccination")', 'a:has-text("History")']:
                el = page.locator(sel).first
                if await el.count() > 0:
                    await el.click()
                    await page.wait_for_load_state('domcontentloaded')
                    await page.wait_for_timeout(2000)
                    break

            # Extract table rows
            rows = await page.query_selector_all('table tbody tr, .imm-row, .vaccination-row')

            for row in rows:
                try:
                    cells = await row.query_selector_all('td')
                    if len(cells) < 2:
                        continue

                    cell_texts = []
                    for cell in cells:
                        text = (await cell.inner_text()).strip()
                        cell_texts.append(text)

                    imm = {
                        'vaccine': cell_texts[0] if len(cell_texts) > 0 else '',
                        'date_given': cell_texts[1] if len(cell_texts) > 1 else '',
                        'manufacturer': cell_texts[2] if len(cell_texts) > 2 else '',
                        'lot_number': cell_texts[3] if len(cell_texts) > 3 else '',
                        'site': cell_texts[4] if len(cell_texts) > 4 else '',
                        'provider': cell_texts[5] if len(cell_texts) > 5 else '',
                    }
                    immunizations.append(imm)
                except Exception:
                    continue

            logger.info('VIIS: extracted %d immunization(s)', len(immunizations))

        except Exception as e:
            logger.warning('VIIS extraction failed: %s', e)

        return immunizations

    async def _load_cookies(self, context):
        """Load saved cookies from JSON file."""
        if not os.path.exists(self._cookie_file):
            return
        try:
            with open(self._cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
        except (json.JSONDecodeError, ValueError):
            logger.warning('VIIS: corrupt cookie file, removing')
            os.remove(self._cookie_file)
        except Exception:
            pass

    async def _save_cookies(self, context):
        """Save current cookies to JSON file."""
        try:
            cookies = await context.cookies()
            os.makedirs(os.path.dirname(self._cookie_file), exist_ok=True)
            with open(self._cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f)
        except Exception:
            pass

    async def health_check(self):
        """Quick check: can we reach the VIIS portal?"""
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(self._url, timeout=10000)
                title = await page.title()
                await browser.close()
                return {'reachable': True, 'title': title, 'url': self._url}
        except Exception as e:
            return {'reachable': False, 'error': str(e), 'url': self._url}
