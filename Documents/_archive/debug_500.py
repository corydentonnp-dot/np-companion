"""Quick script to reproduce and debug the 500 errors in test_phase7.py."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
app = create_app()
app.config['TESTING'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True

with app.app_context():
    from models.user import User
    from models import db

    user = User.query.filter_by(is_active_account=True).order_by(User.id.asc()).first()
    if not user:
        print("No active user!")
        sys.exit(1)
    uid = user.id
    print(f"User: {user.username} (id={uid})")

    c = app.test_client()
    with c.session_transaction() as sess:
        sess['_user_id'] = str(uid)

    # Test 1: Pin menu
    print("\n--- Test: POST /api/prefs/pin-menu ---")
    try:
        r = c.post('/api/prefs/pin-menu',
                    data=json.dumps({'label': 'Test Pin', 'url': '/timer', 'icon': 'x'}),
                    content_type='application/json')
        print(f"Status: {r.status_code}")
        print(f"Body: {r.data.decode()[:300]}")
    except Exception as e:
        print(f"Exception: {e}")

    # Test 2: Add bookmark
    print("\n--- Test: POST /api/bookmarks/personal ---")
    try:
        r = c.post('/api/bookmarks/personal',
                    data=json.dumps({'label': 'Google', 'url': 'https://google.com'}),
                    content_type='application/json')
        print(f"Status: {r.status_code}")
        print(f"Body: {r.data.decode()[:300]}")
    except Exception as e:
        print(f"Exception: {e}")

    # Test 3: Patient generator
    print("\n--- Test: POST /api/patient-generator/generate ---")
    try:
        r = c.post('/api/patient-generator/generate',
                    data=json.dumps({'count': 1, 'complexity': 'Simple'}),
                    content_type='application/json')
        print(f"Status: {r.status_code}")
        print(f"Body: {r.data.decode()[:300]}")
    except Exception as e:
        print(f"Exception: {e}")

    # Test 4: Dismiss What's New
    print("\n--- Test: POST /api/settings/dismiss-whats-new ---")
    try:
        r = c.post('/api/settings/dismiss-whats-new',
                    content_type='application/json')
        print(f"Status: {r.status_code}")
        print(f"Body: {r.data.decode()[:300]}")
    except Exception as e:
        print(f"Exception: {e}")

    print("\nDone.")
