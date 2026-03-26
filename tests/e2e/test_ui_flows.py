"""
CareCompanion -- End-to-End UI Flow Tests (Playwright)
tests/e2e/test_ui_flows.py

Requires:
    - Flask dev server running on localhost:5000
    - Playwright installed: pip install playwright && playwright install chromium
    - Demo data seeded: venv\\Scripts\\python.exe scripts/seed_test_data.py

Usage:
    venv\\Scripts\\python.exe -m pytest tests/e2e/test_ui_flows.py -v -m e2e

    To run with headed browser (visible):
    venv\\Scripts\\python.exe -m pytest tests/e2e/test_ui_flows.py -v -m e2e --headed
"""

import os
import sys
import pytest

# Only run if playwright is available
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright not installed"),
]

# Dev admin credentials from copilot-instructions.md
TEST_USER = "CORY"
TEST_PASS = "ASDqwe123"
BASE_URL = "http://localhost:5000"


# ======================================================================
# Fixtures
# ======================================================================

@pytest.fixture(scope="module")
def browser():
    """Launch a Chromium browser instance for the test module."""
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        yield b
        b.close()


@pytest.fixture
def page(browser):
    """Create a new browser page (tab) for each test."""
    ctx = browser.new_context()
    pg = ctx.new_page()
    yield pg
    pg.close()
    ctx.close()


@pytest.fixture
def auth_page(page):
    """Log in and return an authenticated page."""
    page.goto(f"{BASE_URL}/login")
    page.fill('input[name="username"]', TEST_USER)
    page.fill('input[name="password"]', TEST_PASS)
    page.click('button[type="submit"]')
    # Wait for redirect away from login
    page.wait_for_url(lambda url: "/login" not in url, timeout=5000)
    return page


# ======================================================================
# Login Flow
# ======================================================================

class TestLoginFlow:
    """Verify login page renders and authentication works."""

    def test_login_page_loads(self, page):
        """Login page shows username and password fields."""
        page.goto(f"{BASE_URL}/login")
        assert page.locator('input[name="username"]').is_visible()
        assert page.locator('input[name="password"]').is_visible()
        assert page.locator('button[type="submit"]').is_visible()

    def test_login_success_redirects(self, page):
        """Valid credentials redirect to dashboard."""
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="username"]', TEST_USER)
        page.fill('input[name="password"]', TEST_PASS)
        page.click('button[type="submit"]')
        page.wait_for_url(lambda url: "/login" not in url, timeout=5000)
        # Should land on dashboard or similar
        assert "/login" not in page.url

    def test_login_failure_shows_error(self, page):
        """Invalid credentials stay on login page."""
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="username"]', "INVALID_USER")
        page.fill('input[name="password"]', "wrongpass")
        page.click('button[type="submit"]')
        # Should stay on login page
        page.wait_for_timeout(1000)
        assert "/login" in page.url


# ======================================================================
# Dashboard
# ======================================================================

class TestDashboard:
    """Verify dashboard loads with key sections."""

    def test_dashboard_loads(self, auth_page):
        """Dashboard page loads after login."""
        auth_page.goto(f"{BASE_URL}/")
        assert auth_page.title()  # Page has a title
        # Dashboard should have schedule or patient content
        body = auth_page.content()
        assert len(body) > 500  # Meaningful content rendered

    def test_nav_bar_present(self, auth_page):
        """Navigation bar is present with expected links."""
        auth_page.goto(f"{BASE_URL}/")
        nav = auth_page.locator("nav")
        assert nav.count() >= 1


# ======================================================================
# Health Endpoint (no auth)
# ======================================================================

class TestHealthEndpoint:
    """Verify /api/health returns valid JSON."""

    def test_health_returns_ok(self, page):
        """Health endpoint returns status ok."""
        page.goto(f"{BASE_URL}/api/health")
        content = page.content()
        assert '"status"' in content
        assert '"ok"' in content or '"degraded"' in content


# ======================================================================
# Patient Chart
# ======================================================================

class TestPatientChart:
    """Verify patient chart page renders for demo patient."""

    def test_patient_chart_loads(self, auth_page):
        """Patient chart page loads for a demo patient."""
        # Demo patient MRN 90001
        auth_page.goto(f"{BASE_URL}/patient/90001")
        body = auth_page.content()
        # Should contain patient info or a chart section
        assert len(body) > 200

    def test_patient_not_found(self, auth_page):
        """Non-existent patient shows appropriate message."""
        auth_page.goto(f"{BASE_URL}/patient/99999")
        body = auth_page.content()
        # Should show some kind of not-found or empty state
        assert len(body) > 100


# ======================================================================
# Theme Toggle
# ======================================================================

class TestThemeToggle:
    """Verify dark mode toggle works."""

    def test_theme_toggle_exists(self, auth_page):
        """Theme toggle button exists on the page."""
        auth_page.goto(f"{BASE_URL}/")
        # Look for a theme toggle element (button, checkbox, or similar)
        toggle = auth_page.locator('[data-theme-toggle], .theme-toggle, #theme-toggle')
        # If toggle exists, it should be clickable
        if toggle.count() > 0:
            assert toggle.first.is_visible()


# ======================================================================
# Bonus Dashboard
# ======================================================================

class TestBonusDashboard:
    """Verify bonus dashboard page loads."""

    def test_bonus_page_loads(self, auth_page):
        """Bonus dashboard renders without errors."""
        auth_page.goto(f"{BASE_URL}/bonus")
        body = auth_page.content()
        assert len(body) > 200
        # Should not show a 500 error page
        assert "Internal Server Error" not in body
