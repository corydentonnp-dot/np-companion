"""
NP Companion — Virginia PDMP (PMP AWARxE) Scraper
File: scrapers/pdmp.py

Uses Playwright to automate login and patient lookup on the Virginia
Prescription Drug Monitoring Program portal (virginia.pmpaware.net).

Architecture follows the same pattern as scrapers/netpractice.py:
  1. Connect to Chrome via CDP or launch headless Chromium
  2. Login with stored credentials (email + password from config.py)
  3. Search for patient by name + DOB
  4. Extract prescription history from results page
  5. Return structured data for display in the CS Tracker

Session cookies are persisted to avoid re-login on every check.

HIPAA note: Patient name and DOB are sent to the PDMP portal (this is
a state-authorized clinical lookup, not a third-party API). No data is
logged beyond what the PDMP portal itself records.

Usage:
    from scrapers.pdmp import PDMPScraper
    scraper = PDMPScraper(app)
    result = asyncio.run(scraper.lookup_patient(
        first_name='John', last_name='Smith', dob='1960-01-15'
    ))
"""

import asyncio
import json
import logging
import os
import pickle
from datetime import date, datetime, timezone

logger = logging.getLogger('np_companion.pdmp')


class PDMPScraper:
    """
    Playwright-based scraper for Virginia PMP AWARxE portal.

    Parameters
    ----------
    app : Flask app instance
        Needed to read config values (PDMP_EMAIL, PDMP_PASSWORD, PDMP_URL).
    """

    def __init__(self, app):
        self.app = app
        self._cookie_file = os.path.join(app.root_path, 'data', 'pdmp_session.pkl')
        self._cdp_port = app.config.get('CHROME_CDP_PORT', 9222)
        self._url = app.config.get('PDMP_URL', 'https://virginia.pmpaware.net')
        self._email = app.config.get('PDMP_EMAIL', '')
        self._password = app.config.get('PDMP_PASSWORD', '')

    async def lookup_patient(self, first_name, last_name, dob):
        """
        Look up a patient in the Virginia PDMP.

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
            'prescriptions': list of dicts (drug, date, prescriber, pharmacy, quantity, days_supply)
            'error': str (if failed)
            'checked_at': ISO timestamp
        """
        if not self._email or not self._password:
            return {
                'success': False,
                'prescriptions': [],
                'error': 'PDMP credentials not configured in config.py',
                'checked_at': datetime.now(timezone.utc).isoformat(),
            }

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return {
                'success': False,
                'prescriptions': [],
                'error': 'Playwright not installed',
                'checked_at': datetime.now(timezone.utc).isoformat(),
            }

        result = {
            'success': False,
            'prescriptions': [],
            'error': '',
            'checked_at': datetime.now(timezone.utc).isoformat(),
        }

        async with async_playwright() as pw:
            browser = None
            try:
                # Try CDP first (attach to existing Chrome)
                try:
                    browser = await pw.chromium.connect_over_cdp(
                        f'http://127.0.0.1:{self._cdp_port}'
                    )
                    logger.info('PDMP: connected via Chrome CDP')
                except Exception:
                    browser = await pw.chromium.launch(headless=True)
                    logger.info('PDMP: launched headless Chromium')

                context = await browser.new_context()

                # Load saved cookies if available
                await self._load_cookies(context)

                page = await context.new_page()
                page.set_default_timeout(15000)

                # Navigate to PDMP portal
                await page.goto(self._url + '/login', wait_until='domcontentloaded')

                # Check if already logged in (cookie session valid)
                if '/login' in page.url:
                    await self._do_login(page)

                # Navigate to patient search
                await page.goto(self._url + '/rx-search', wait_until='domcontentloaded')

                # Fill patient search form
                await self._search_patient(page, first_name, last_name, dob)

                # Extract prescription data from results
                prescriptions = await self._extract_prescriptions(page)

                # Save cookies for next time
                await self._save_cookies(context)

                result['success'] = True
                result['prescriptions'] = prescriptions

            except Exception as e:
                error_msg = str(e)
                logger.warning('PDMP lookup failed: %s', error_msg)
                result['error'] = error_msg

            finally:
                if browser:
                    try:
                        await browser.close()
                    except Exception:
                        pass

        return result

    async def _do_login(self, page):
        """Fill login form and submit."""
        logger.info('PDMP: logging in as %s', self._email)

        # Fill email
        email_sel = 'input[type="email"], input[name="email"], input[id*="email"], input[name="username"]'
        await page.wait_for_selector(email_sel, timeout=10000)
        await page.fill(email_sel, self._email)

        # Fill password
        pwd_sel = 'input[type="password"], input[name="password"]'
        await page.fill(pwd_sel, self._password)

        # Submit
        submit_sel = 'button[type="submit"], input[type="submit"], button:has-text("Log In"), button:has-text("Sign In")'
        await page.click(submit_sel)
        await page.wait_for_load_state('domcontentloaded')

        # Verify login succeeded
        await page.wait_for_timeout(2000)
        if '/login' in page.url:
            raise Exception('PDMP login failed — check credentials')

        logger.info('PDMP: login successful')

    async def _search_patient(self, page, first_name, last_name, dob):
        """Fill and submit the patient search form."""
        # Wait for search form
        await page.wait_for_timeout(1000)

        # Try common selector patterns for PMP AWARxE
        try:
            # Last name field
            for sel in ['input[name*="last" i]', 'input[id*="last" i]', 'input[placeholder*="Last" i]']:
                el = page.locator(sel).first
                if await el.count() > 0:
                    await el.fill(last_name)
                    break

            # First name field
            for sel in ['input[name*="first" i]', 'input[id*="first" i]', 'input[placeholder*="First" i]']:
                el = page.locator(sel).first
                if await el.count() > 0:
                    await el.fill(first_name)
                    break

            # DOB field
            for sel in ['input[name*="dob" i]', 'input[name*="birth" i]', 'input[id*="dob" i]',
                        'input[type="date"]', 'input[placeholder*="DOB" i]', 'input[placeholder*="birth" i]']:
                el = page.locator(sel).first
                if await el.count() > 0:
                    # Format DOB as MM/DD/YYYY for the form
                    try:
                        d = datetime.strptime(dob, '%Y-%m-%d')
                        formatted_dob = d.strftime('%m/%d/%Y')
                    except ValueError:
                        formatted_dob = dob
                    await el.fill(formatted_dob)
                    break

            # Submit search
            for sel in ['button[type="submit"]', 'button:has-text("Search")',
                        'input[type="submit"]', 'button:has-text("Submit")']:
                el = page.locator(sel).first
                if await el.count() > 0:
                    await el.click()
                    break

            await page.wait_for_load_state('domcontentloaded')
            await page.wait_for_timeout(3000)

        except Exception as e:
            logger.warning('PDMP search form fill failed: %s', e)
            raise

    async def _extract_prescriptions(self, page):
        """Extract prescription data from the results page."""
        prescriptions = []

        try:
            # Wait for results table to appear
            await page.wait_for_timeout(2000)

            # Try common table selectors for PMP AWARxE results
            rows = await page.query_selector_all('table tbody tr, .rx-row, .prescription-row')

            if not rows:
                # Try getting text content and parsing
                content = await page.content()
                if 'no results' in content.lower() or 'no records' in content.lower():
                    logger.info('PDMP: no prescriptions found for patient')
                    return []

                # Try alternate selectors
                rows = await page.query_selector_all('tr[data-rx], .data-row, table.results tr')

            for row in rows:
                try:
                    cells = await row.query_selector_all('td')
                    if len(cells) < 3:
                        continue

                    # Extract cell text — order varies by portal version
                    cell_texts = []
                    for cell in cells:
                        text = (await cell.inner_text()).strip()
                        cell_texts.append(text)

                    # Build prescription record — map by position
                    # Typical PMP AWARxE columns: Date, Drug, Qty, Days, Prescriber, Pharmacy
                    rx = {
                        'date_filled': cell_texts[0] if len(cell_texts) > 0 else '',
                        'drug_name': cell_texts[1] if len(cell_texts) > 1 else '',
                        'quantity': cell_texts[2] if len(cell_texts) > 2 else '',
                        'days_supply': cell_texts[3] if len(cell_texts) > 3 else '',
                        'prescriber': cell_texts[4] if len(cell_texts) > 4 else '',
                        'pharmacy': cell_texts[5] if len(cell_texts) > 5 else '',
                    }
                    prescriptions.append(rx)

                except Exception:
                    continue

            logger.info('PDMP: extracted %d prescription(s)', len(prescriptions))

        except Exception as e:
            logger.warning('PDMP extraction failed: %s', e)

        return prescriptions

    async def _load_cookies(self, context):
        """Load saved cookies from pickle file."""
        if not os.path.exists(self._cookie_file):
            return
        try:
            with open(self._cookie_file, 'rb') as f:
                cookies = pickle.load(f)
            await context.add_cookies(cookies)
            logger.debug('PDMP: loaded %d saved cookies', len(cookies))
        except Exception:
            pass

    async def _save_cookies(self, context):
        """Save current cookies to pickle file."""
        try:
            cookies = await context.cookies()
            os.makedirs(os.path.dirname(self._cookie_file), exist_ok=True)
            with open(self._cookie_file, 'wb') as f:
                pickle.dump(cookies, f)
            logger.debug('PDMP: saved %d cookies', len(cookies))
        except Exception:
            pass

    async def health_check(self):
        """Quick check: can we reach the PDMP portal?"""
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(self._url, timeout=10000)
                title = await page.title()
                await browser.close()
                return {
                    'reachable': True,
                    'title': title,
                    'url': self._url,
                }
        except Exception as e:
            return {
                'reachable': False,
                'error': str(e),
                'url': self._url,
            }
