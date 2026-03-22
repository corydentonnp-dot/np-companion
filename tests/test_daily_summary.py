"""
Tests for daily summary, rooming sheet, REMS reference, and reportable diseases.
Run with: python -m pytest tests/test_daily_summary.py -v
"""
import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest


# ------------------------------------------------------------------
# Fixture: Flask test app + client
# ------------------------------------------------------------------
@pytest.fixture
def app():
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client, app):
    """Client with a logged-in session."""
    with app.app_context():
        from models import db
        from models.user import User
        user = User.query.first()
        uid = user.id if user else 1
    with client.session_transaction() as sess:
        sess['_user_id'] = str(uid)
    return client


# ------------------------------------------------------------------
# 1. Blueprint import and registration
# ------------------------------------------------------------------
def test_blueprint_imports():
    from routes.daily_summary import daily_summary_bp
    assert daily_summary_bp.name == 'daily_summary'


def test_blueprint_registered(app):
    bp_names = [bp.name for bp in app.blueprints.values()]
    assert 'daily_summary' in bp_names


# ------------------------------------------------------------------
# 2. Route existence (all 6 endpoints)
# ------------------------------------------------------------------
EXPECTED_ROUTES = [
    '/daily-summary',
    '/daily-summary/print',
    '/daily-summary/rooming',
    '/daily-summary/rooming/print',
    '/reference/rems',
    '/reference/reportable-diseases',
]


@pytest.mark.parametrize("url", EXPECTED_ROUTES)
def test_route_exists(app, url):
    rules = [r.rule for r in app.url_map.iter_rules()]
    assert url in rules, f"Route {url} not found in url_map"


# ------------------------------------------------------------------
# 3. Authenticated access returns 200 (not 500)
# ------------------------------------------------------------------
def test_daily_summary_200(auth_client):
    r = auth_client.get('/daily-summary')
    assert r.status_code == 200
    assert b'Daily Provider Summary' in r.data


def test_daily_summary_print_200(auth_client):
    r = auth_client.get('/daily-summary/print')
    assert r.status_code == 200
    assert b'window.print()' in r.data


def test_rooming_sheet_200(auth_client):
    r = auth_client.get('/daily-summary/rooming')
    assert r.status_code == 200
    assert b'Rooming Staff Sheet' in r.data


def test_rooming_sheet_print_200(auth_client):
    r = auth_client.get('/daily-summary/rooming/print')
    assert r.status_code == 200
    assert b'window.print()' in r.data


def test_rems_reference_200(auth_client):
    r = auth_client.get('/reference/rems')
    assert r.status_code == 200
    assert b'REMS Medication Database' in r.data


def test_reportable_diseases_200(auth_client):
    r = auth_client.get('/reference/reportable-diseases')
    assert r.status_code == 200
    assert b'Reportable Infectious Disease Guide' in r.data


# ------------------------------------------------------------------
# 4. Date parameter handling
# ------------------------------------------------------------------
def test_daily_summary_date_param(auth_client):
    r = auth_client.get('/daily-summary?date=2025-01-15')
    assert r.status_code == 200
    assert b'January 15, 2025' in r.data


def test_daily_summary_invalid_date(auth_client):
    r = auth_client.get('/daily-summary?date=not-a-date')
    assert r.status_code == 200  # falls back to today


# ------------------------------------------------------------------
# 5. REMS database JSON integrity
# ------------------------------------------------------------------
def test_rems_json_valid():
    path = Path(__file__).resolve().parent.parent / 'data' / 'rems_database.json'
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert len(data) >= 20, f"Expected 20+ REMS programs, got {len(data)}"
    for prog in data:
        assert 'program_name' in prog
        assert 'medications' in prog
        assert 'requirements' in prog
        assert 'status' in prog


def test_rems_json_has_key_programs():
    path = Path(__file__).resolve().parent.parent / 'data' / 'rems_database.json'
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    names = [p['program_name'] for p in data]
    assert any('iPLEDGE' in n for n in names), "Missing iPLEDGE"
    assert any('Clozapine' in n for n in names), "Missing Clozapine"
    assert any('Opioid' in n for n in names), "Missing Opioid Analgesic REMS"
    assert any('TIRF' in n for n in names), "Missing TIRF REMS"
    assert any('Tysabri' in n or 'TOUCH' in n or 'Natalizumab' in n for n in names), "Missing Tysabri/TOUCH"


# ------------------------------------------------------------------
# 6. Reportable diseases JSON integrity
# ------------------------------------------------------------------
def test_diseases_json_valid():
    path = Path(__file__).resolve().parent.parent / 'data' / 'reportable_diseases.json'
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert len(data) >= 25, f"Expected 25+ conditions, got {len(data)}"
    for d in data:
        assert 'condition' in d
        assert 'nationally_notifiable' in d
        assert 'provider_obligations' in d
        assert 'reporting_timeframe' in d


def test_diseases_json_has_key_conditions():
    path = Path(__file__).resolve().parent.parent / 'data' / 'reportable_diseases.json'
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    conditions = [d['condition'] for d in data]
    assert any('Active' in c and ('TB' in c or 'Tuberculosis' in c) for c in conditions), "Missing active TB"
    assert any('Latent' in c and ('TB' in c or 'Tuberculosis' in c) for c in conditions), "Missing latent TB"
    assert any('HIV' in c for c in conditions), "Missing HIV"
    assert any('Syphilis' in c for c in conditions), "Missing Syphilis"
    assert any('Hepatitis B' in c for c in conditions), "Missing Hepatitis B"
    assert any('Measles' in c for c in conditions), "Missing Measles"


# ------------------------------------------------------------------
# 7. Screening tool mapping
# ------------------------------------------------------------------
def test_screening_tools_mapping():
    from routes.daily_summary import SCREENING_TOOLS
    assert 'depression_screen' in SCREENING_TOOLS
    assert 'alcohol_screen' in SCREENING_TOOLS
    assert 'fall_risk' in SCREENING_TOOLS
    assert 'tool' in SCREENING_TOOLS['depression_screen']
    assert 'action' in SCREENING_TOOLS['depression_screen']


def test_rooming_tasks_by_visit():
    from routes.daily_summary import ROOMING_TASKS_BY_VISIT
    assert '_default' in ROOMING_TASKS_BY_VISIT
    assert 'AV' in ROOMING_TASKS_BY_VISIT  # Annual Wellness Visit
    assert 'PE' in ROOMING_TASKS_BY_VISIT  # Physical Exam
    assert 'NP' in ROOMING_TASKS_BY_VISIT  # New Patient
    assert len(ROOMING_TASKS_BY_VISIT['AV']) > len(ROOMING_TASKS_BY_VISIT['_default'])


# ------------------------------------------------------------------
# 8. Helper functions
# ------------------------------------------------------------------
def test_split_name():
    from routes.daily_summary import _split_name
    assert _split_name('SMITH, JOHN') == ('JOHN', 'SMITH')
    assert _split_name('John Smith') == ('John', 'Smith')
    assert _split_name('') == ('', '')
    assert _split_name(None) == ('', '')


def test_estimate_age():
    from routes.daily_summary import _estimate_age
    assert _estimate_age('01/01/2000') is not None
    assert _estimate_age('') is None
    assert _estimate_age('invalid') is None
    assert _estimate_age(None) is None


# ------------------------------------------------------------------
# 9. Clozapine REMS removal note
# ------------------------------------------------------------------
def test_clozapine_rems_removal_noted():
    path = Path(__file__).resolve().parent.parent / 'data' / 'rems_database.json'
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    clozapine = [p for p in data if 'Clozapine' in p['program_name']][0]
    assert clozapine['status'] != 'active', "Clozapine REMS should be marked as removed"
    assert 'June' in (clozapine.get('status_detail') or ''), "Should note June 2025 removal"


# ------------------------------------------------------------------
# 10. Latent TB LTBI guidance present
# ------------------------------------------------------------------
def test_latent_tb_guidance():
    path = Path(__file__).resolve().parent.parent / 'data' / 'reportable_diseases.json'
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    ltbi = [d for d in data if 'Latent' in d['condition']][0]
    assert ltbi['nationally_notifiable'] is False, "LTBI is NOT nationally notifiable"
    obligations = ' '.join(ltbi['provider_obligations']).lower()
    assert 'varies' in obligations or 'state' in obligations, "Should note LTBI reporting varies by state"
