"""Temporary script to debug unauthenticated request behavior."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

a = create_app()
a.config['TESTING'] = True
a.config['WTF_CSRF_ENABLED'] = False
a.config['LOGIN_DISABLED'] = False

with a.app_context():
    from models import db
    db.create_all()
    c = a.test_client()

    r1 = c.post('/api/billing/opportunity/1/capture')
    print(f'POST capture: {r1.status_code}')

    r2 = c.post('/api/billing/opportunity/1/dismiss')
    print(f'POST dismiss: {r2.status_code}')

    r3 = c.get('/api/patient/62815/billing-opportunities')
    print(f'GET billing: {r3.status_code}')
