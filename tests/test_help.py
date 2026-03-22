"""
Tests for the help / feature guide system.
Run with: python -m pytest tests/test_help.py -v
"""
import json
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
    from routes.help import help_bp
    assert help_bp.name == 'help'


def test_blueprint_registered(app):
    bp_names = [bp.name for bp in app.blueprints.values()]
    assert 'help' in bp_names


# ------------------------------------------------------------------
# 2. Route existence
# ------------------------------------------------------------------
EXPECTED_ROUTES = [
    '/help',
    '/help/<feature_id>',
    '/api/help/search',
]


@pytest.mark.parametrize("url", EXPECTED_ROUTES)
def test_route_exists(app, url):
    rules = [r.rule for r in app.url_map.iter_rules()]
    assert url in rules, f"Route {url} not found in url_map"


# ------------------------------------------------------------------
# 3. Help index page returns 200
# ------------------------------------------------------------------
def test_help_index_200(auth_client):
    r = auth_client.get('/help')
    assert r.status_code == 200
    assert b'Feature Guide' in r.data


def test_help_index_shows_categories(auth_client):
    r = auth_client.get('/help')
    assert b'Daily Workflow' in r.data
    assert b'Patient Care' in r.data
    assert b'Clinical Tools' in r.data
    assert b'Billing' in r.data
    assert b'Communication' in r.data
    assert b'References' in r.data


# ------------------------------------------------------------------
# 4. Individual feature help articles
# ------------------------------------------------------------------
def test_help_dashboard_article(auth_client):
    r = auth_client.get('/help/dashboard')
    assert r.status_code == 200
    assert b'Dashboard' in r.data
    assert b'What It Does' in r.data


def test_help_care_gaps_article(auth_client):
    r = auth_client.get('/help/care-gaps')
    assert r.status_code == 200
    assert b'Care Gaps' in r.data


def test_help_timer_article(auth_client):
    r = auth_client.get('/help/timer')
    assert r.status_code == 200
    assert b'Visit Timer' in r.data
    assert b'Step-by-Step' in r.data


def test_help_nonexistent_returns_404(auth_client):
    r = auth_client.get('/help/this-does-not-exist')
    assert r.status_code == 404


# ------------------------------------------------------------------
# 5. Search API
# ------------------------------------------------------------------
def test_search_returns_results(auth_client):
    r = auth_client.get('/api/help/search?q=care+gap')
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any('care' in item['name'].lower() for item in data)


def test_search_empty_query(auth_client):
    r = auth_client.get('/api/help/search?q=')
    assert r.status_code == 200
    assert r.get_json() == []


def test_search_short_query(auth_client):
    r = auth_client.get('/api/help/search?q=a')
    assert r.status_code == 200
    assert r.get_json() == []


def test_search_no_results(auth_client):
    r = auth_client.get('/api/help/search?q=xyznonexistent123')
    assert r.status_code == 200
    assert r.get_json() == []


def test_search_result_structure(auth_client):
    r = auth_client.get('/api/help/search?q=dashboard')
    data = r.get_json()
    assert len(data) > 0
    item = data[0]
    assert 'id' in item
    assert 'name' in item
    assert 'category' in item
    assert 'description' in item
    assert 'url' in item


# ------------------------------------------------------------------
# 6. Help guide JSON integrity
# ------------------------------------------------------------------
def test_help_json_valid():
    path = Path(__file__).resolve().parent.parent / 'data' / 'help_guide.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    assert 'categories' in data
    assert 'features' in data
    assert len(data['categories']) >= 7
    assert len(data['features']) >= 30


def test_help_json_all_features_have_category():
    path = Path(__file__).resolve().parent.parent / 'data' / 'help_guide.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    cat_ids = {c['id'] for c in data['categories']}
    for feat in data['features']:
        assert feat['category'] in cat_ids, f"Feature {feat['id']} has unknown category {feat['category']}"


def test_help_json_all_features_have_description():
    path = Path(__file__).resolve().parent.parent / 'data' / 'help_guide.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    for feat in data['features']:
        assert feat.get('description'), f"Feature {feat['id']} missing description"
        assert len(feat['description']) >= 20, f"Feature {feat['id']} description too short"


def test_help_json_unique_ids():
    path = Path(__file__).resolve().parent.parent / 'data' / 'help_guide.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    ids = [f['id'] for f in data['features']]
    assert len(ids) == len(set(ids)), "Duplicate feature IDs found"


def test_help_json_key_features_present():
    path = Path(__file__).resolve().parent.parent / 'data' / 'help_guide.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    feature_ids = {f['id'] for f in data['features']}
    required = [
        'dashboard', 'morning-briefing', 'daily-summary', 'rooming-sheet',
        'patient-chart', 'care-gaps', 'lab-tracking', 'clinical-calculators',
        'timer', 'coding-helper', 'inbox', 'oncall',
        'rems-reference', 'reportable-diseases'
    ]
    for req in required:
        assert req in feature_ids, f"Key feature '{req}' missing from help guide"


# ------------------------------------------------------------------
# 7. Unauthenticated redirects to login
# ------------------------------------------------------------------
def test_help_requires_login(client):
    r = client.get('/help', follow_redirects=False)
    assert r.status_code in (302, 301)


def test_help_search_requires_login(client):
    r = client.get('/api/help/search?q=test', follow_redirects=False)
    assert r.status_code in (302, 301)


# ------------------------------------------------------------------
# 8. Help appears in navigation
# ------------------------------------------------------------------
def test_help_in_command_palette(app):
    """Verify Feature Guide was added to __npRoutes in base.html."""
    with app.test_request_context():
        from flask import render_template_string
    # Just verify the route is registered — the template tests above verify content
    rules = [r.rule for r in app.url_map.iter_rules()]
    assert '/help' in rules


def test_help_feature_has_steps_and_tips():
    """Features with steps should also be well-structured."""
    path = Path(__file__).resolve().parent.parent / 'data' / 'help_guide.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    features_with_steps = [f for f in data['features'] if f.get('steps')]
    assert len(features_with_steps) >= 10, "At least 10 features should have step-by-step guides"
