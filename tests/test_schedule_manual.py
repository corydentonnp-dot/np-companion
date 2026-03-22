"""
Tests for manual schedule entry endpoints:
  - POST /api/schedule/add
  - DELETE /api/schedule/<id>
  - POST /api/schedule/parse-text

Uses the Flask test client with an authenticated session.
"""

import json
import os
import sys
from datetime import date

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from models.schedule import Schedule


def _make_app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app


def _auth_client(app):
    """Return a test client with an authenticated session."""
    client = app.test_client()
    with app.app_context():
        from models.user import User
        user = (
            User.query.filter_by(is_active_account=True)
            .order_by(User.id.asc())
            .first()
        )
        if not user:
            raise RuntimeError('No active user found — create one first')
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
    return client, user.id


def run_tests():
    passed = []
    failed = []

    app = _make_app()
    client, user_id = _auth_client(app)

    # ----------------------------------------------------------------
    # POST /api/schedule/add — valid
    # ----------------------------------------------------------------
    print('[1/9] POST /api/schedule/add — valid add...')
    try:
        resp = client.post('/api/schedule/add', json={
            'patient_name': 'TEST, PATIENT',
            'patient_mrn': '99999',
            'appointment_time': '10:30',
            'visit_type': 'Office Visit',
            'duration_minutes': 15,
        })
        data = resp.get_json()
        assert resp.status_code == 200, f'Expected 200, got {resp.status_code}'
        assert data['success'] is True, 'success should be True'
        assert 'id' in data, 'response should contain id'
        created_id = data['id']
        passed.append('add valid')
        print('  PASS')
    except Exception as e:
        failed.append(f'add valid: {e}')
        print(f'  FAIL  {e}')
        created_id = None

    # ----------------------------------------------------------------
    # POST /api/schedule/add — missing required fields
    # ----------------------------------------------------------------
    print('[2/9] POST /api/schedule/add — missing fields...')
    try:
        resp = client.post('/api/schedule/add', json={
            'patient_name': '',
            'patient_mrn': '',
            'appointment_time': '',
        })
        assert resp.status_code == 400, f'Expected 400, got {resp.status_code}'
        data = resp.get_json()
        assert data['success'] is False
        assert len(data['errors']) >= 3, f'Expected 3+ errors, got {len(data["errors"])}'
        passed.append('add missing fields')
        print('  PASS')
    except Exception as e:
        failed.append(f'add missing fields: {e}')
        print(f'  FAIL  {e}')

    # ----------------------------------------------------------------
    # POST /api/schedule/add — invalid time format
    # ----------------------------------------------------------------
    print('[3/9] POST /api/schedule/add — invalid time...')
    try:
        resp = client.post('/api/schedule/add', json={
            'patient_name': 'TEST, BAD',
            'patient_mrn': '11111',
            'appointment_time': 'not-a-time',
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert any('HH:MM' in e for e in data.get('errors', [])), 'Should mention HH:MM'
        passed.append('add invalid time')
        print('  PASS')
    except Exception as e:
        failed.append(f'add invalid time: {e}')
        print(f'  FAIL  {e}')

    # ----------------------------------------------------------------
    # DELETE /api/schedule/<id> — delete manual entry
    # ----------------------------------------------------------------
    print('[4/9] DELETE manual entry...')
    try:
        if created_id:
            resp = client.delete(f'/api/schedule/{created_id}')
            data = resp.get_json()
            assert resp.status_code == 200, f'Expected 200, got {resp.status_code}'
            assert data['success'] is True
            passed.append('delete manual')
            print('  PASS')
        else:
            failed.append('delete manual: no created_id to delete')
            print('  SKIP  (no id)')
    except Exception as e:
        failed.append(f'delete manual: {e}')
        print(f'  FAIL  {e}')

    # ----------------------------------------------------------------
    # DELETE /api/schedule/<id> — reject scraped entry
    # ----------------------------------------------------------------
    print('[5/9] DELETE scraped entry → 403...')
    try:
        # Create a scraped entry directly in the DB
        with app.app_context():
            scraped = Schedule(
                user_id=user_id,
                patient_name='SCRAPED, PATIENT',
                patient_mrn='88888',
                appointment_date=date.today(),
                appointment_time='09:00',
                entered_by='netpractice',
                status='scheduled',
            )
            db.session.add(scraped)
            db.session.commit()
            scraped_id = scraped.id

        resp = client.delete(f'/api/schedule/{scraped_id}')
        assert resp.status_code == 403, f'Expected 403, got {resp.status_code}'
        data = resp.get_json()
        assert data['success'] is False
        passed.append('delete scraped → 403')
        print('  PASS')

        # Clean up
        with app.app_context():
            Schedule.query.filter_by(id=scraped_id).delete()
            db.session.commit()
    except Exception as e:
        failed.append(f'delete scraped: {e}')
        print(f'  FAIL  {e}')

    # ----------------------------------------------------------------
    # DELETE /api/schedule/<id> — not found
    # ----------------------------------------------------------------
    print('[6/9] DELETE non-existent → 404...')
    try:
        resp = client.delete('/api/schedule/999999')
        assert resp.status_code == 404
        passed.append('delete not found → 404')
        print('  PASS')
    except Exception as e:
        failed.append(f'delete not found: {e}')
        print(f'  FAIL  {e}')

    # ----------------------------------------------------------------
    # POST /api/schedule/parse-text — well-formatted
    # ----------------------------------------------------------------
    print('[7/9] POST /api/schedule/parse-text — good text...')
    try:
        text = (
            '9:00 AM  SMITH, JOHN  (54321)  FU\n'
            '9:30 AM  DOE, JANE  (12345)  NP - cough\n'
            '10:00 AM  BROWN, BOB  (99887)  PE'
        )
        resp = client.post('/api/schedule/parse-text', json={'text': text})
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['success'] is True
        assert len(data['parsed']) == 3, f'Expected 3 rows, got {len(data["parsed"])}'
        # Check first entry
        first = data['parsed'][0]
        assert 'SMITH' in first['patient_name'] and 'JOHN' in first['patient_name'], f'Name: {first["patient_name"]}'
        assert first['patient_mrn'] == '54321', f'MRN: {first["patient_mrn"]}'
        assert first['time'] == '9:00', f'Time: {first["time"]}'
        assert first['confidence'] == 'high', f'Confidence: {first["confidence"]}'
        passed.append('parse-text good')
        print('  PASS')
    except Exception as e:
        failed.append(f'parse-text good: {e}')
        print(f'  FAIL  {e}')

    # ----------------------------------------------------------------
    # POST /api/schedule/parse-text — empty text
    # ----------------------------------------------------------------
    print('[8/9] POST /api/schedule/parse-text — empty...')
    try:
        resp = client.post('/api/schedule/parse-text', json={'text': ''})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['success'] is False
        passed.append('parse-text empty → 400')
        print('  PASS')
    except Exception as e:
        failed.append(f'parse-text empty: {e}')
        print(f'  FAIL  {e}')

    # ----------------------------------------------------------------
    # POST /api/schedule/parse-text — no recognizable data
    # ----------------------------------------------------------------
    print('[9/9] POST /api/schedule/parse-text — gibberish...')
    try:
        resp = client.post('/api/schedule/parse-text', json={'text': 'hello world\nfoo bar baz'})
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['success'] is True
        assert len(data['parsed']) == 0, f'Expected 0 rows, got {len(data["parsed"])}'
        passed.append('parse-text gibberish → 0 rows')
        print('  PASS')
    except Exception as e:
        failed.append(f'parse-text gibberish: {e}')
        print(f'  FAIL  {e}')

    # ---- Summary ----
    print(f'\n=== Schedule Manual Tests: {len(passed)} passed, {len(failed)} failed ===')
    if failed:
        for f in failed:
            print(f'  FAIL: {f}')
    return passed, failed


if __name__ == '__main__':
    passed, failed = run_tests()
    sys.exit(1 if failed else 0)
