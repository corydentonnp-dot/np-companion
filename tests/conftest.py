# conftest.py -- pytest configuration and shared fixtures for CareCompanion tests
#
# Provides: app, client, db_session, auth_client, admin_client, demo_patients,
#           billing_engine, sample_patient_data fixtures.
#
# test_phase7.py is a standalone script (run via `python tests/test_phase7.py`).
# It runs all tests at module level and calls sys.exit(), which crashes pytest's
# collection phase. Exclude it from pytest discovery.

import os
import sys

import pytest

# Ensure project root is on sys.path so imports work
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

collect_ignore = ['test_phase7.py']


# ======================================================================
# App fixture -- session-scoped Flask app with test config
# ======================================================================
@pytest.fixture(scope='session')
def app():
    """Create a Flask app instance configured for testing."""
    from app import create_app
    test_app = create_app(testing=True)
    test_app.config['TESTING'] = True
    test_app.config['WTF_CSRF_ENABLED'] = False
    test_app.config['LOGIN_DISABLED'] = False

    with test_app.app_context():
        from models import db
        db.create_all()
        yield test_app


# ======================================================================
# DB session fixture -- function-scoped with transaction rollback
# ======================================================================
@pytest.fixture(scope='function')
def db_session(app):
    """Provide a DB session that rolls back after each test.

    Compatible with Flask-SQLAlchemy 3.x + SQLAlchemy 2.0.
    Uses a NESTED SAVEPOINT so that route-level db.session.commit()
    calls release the savepoint instead of committing the outer txn.
    The outer transaction is rolled back on teardown so no test data
    persists between tests.
    """
    from models import db
    from sqlalchemy.orm import sessionmaker, scoped_session
    from sqlalchemy import event

    # 1. Open a connection and begin the OUTER transaction (never committed)
    connection = db.engine.connect()
    transaction = connection.begin()

    # 2. Begin a NESTED savepoint inside the outer transaction
    nested = connection.begin_nested()

    # 3. Build a session bound to this connection, joining the outer txn
    session_factory = sessionmaker(bind=connection, expire_on_commit=False)
    session = scoped_session(session_factory)

    # 4. When the session commits (e.g. route calls db.session.commit()),
    #    the nested savepoint is released. Re-open a new savepoint so
    #    subsequent operations still happen inside the outer transaction.
    @event.listens_for(session, 'after_transaction_end')
    def restart_savepoint(sess, trans):
        nonlocal nested
        if trans.nested and not trans._parent.nested:
            nested = connection.begin_nested()

    old_session = db.session
    db.session = session

    yield session

    # 5. Teardown: rollback outer transaction so nothing persists
    session.remove()
    event.remove(session, 'after_transaction_end', restart_savepoint)
    transaction.rollback()
    connection.close()
    db.session = old_session


# ======================================================================
# Client fixture -- Flask test client
# ======================================================================
@pytest.fixture(scope='function')
def client(app):
    """Flask test client for making requests."""
    with app.test_client() as c:
        yield c


# ======================================================================
# Authenticated client -- logs in as test provider
# ======================================================================
@pytest.fixture(scope='function')
def auth_client(app, db_session):
    """Flask test client pre-authenticated as provider user."""
    from flask_bcrypt import generate_password_hash
    from models.user import User

    # Create or fetch test provider
    user = db_session.query(User).filter_by(username='testprovider').first()
    if not user:
        user = User(
            username='testprovider',
            password_hash=generate_password_hash('testpass123').decode('utf-8'),
            display_name='Test Provider',
            role='provider',
        )
        db_session.add(user)
        db_session.flush()

    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
        c._test_user = user
        yield c


# ======================================================================
# Admin client -- logs in as admin user
# ======================================================================
@pytest.fixture(scope='function')
def admin_client(app, db_session):
    """Flask test client pre-authenticated as admin user."""
    from flask_bcrypt import generate_password_hash
    from models.user import User

    user = db_session.query(User).filter_by(username='testadmin').first()
    if not user:
        user = User(
            username='testadmin',
            password_hash=generate_password_hash('adminpass123').decode('utf-8'),
            display_name='Test Admin',
            role='admin',
        )
        db_session.add(user)
        db_session.flush()

    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
        c._test_user = user
        yield c


# ======================================================================
# Demo patients -- 5 representative patients from the 35-patient set
# ======================================================================
@pytest.fixture(scope='session')
def demo_patients():
    """Return a list of 5 representative demo patient dicts for testing.

    Covers: Medicare (67F), Commercial (55M), Medicaid pediatric (10M),
    Medicare Advantage complex (55M), and false-positive control (27F).
    """
    return [
        {
            'mrn': '90001', 'first_name': 'Margaret', 'last_name': 'Wilson',
            'age': 67, 'sex': 'F', 'insurer': 'Medicare',
            'insurer_type': 'medicare',
            'diagnoses': ['I10', 'E11.9', 'E78.5', 'M81.0'],
            'notes': 'HTN, T2DM, HLD, osteoporosis -- AWV + CCM candidate',
        },
        {
            'mrn': '90004', 'first_name': 'James', 'last_name': 'Chen',
            'age': 55, 'sex': 'M', 'insurer': 'Blue Cross',
            'insurer_type': 'commercial',
            'diagnoses': ['E11.22', 'N18.3', 'I10'],
            'notes': 'T2DM w/ CKD3 -- CCM + chronic monitoring + RPM',
        },
        {
            'mrn': '90014', 'first_name': 'Christopher', 'last_name': 'Lee',
            'age': 10, 'sex': 'M', 'insurer': 'Virginia Medicaid',
            'insurer_type': 'medicaid',
            'diagnoses': ['F90.0', 'J45.20'],
            'notes': 'PEDIATRIC -- ADHD + asthma, well-child + vaccines',
        },
        {
            'mrn': '90034', 'first_name': 'Richard', 'last_name': 'Cooper',
            'age': 55, 'sex': 'M', 'insurer': 'Humana',
            'insurer_type': 'medicare_advantage',
            'diagnoses': ['I50.9', 'J44.1', 'E11.9', 'N18.3', 'E66.01'],
            'notes': 'MOST COMPLEX -- 5 chronic conditions, CCM + RPM',
        },
        {
            'mrn': '90029', 'first_name': 'Jessica', 'last_name': 'Campbell',
            'age': 27, 'sex': 'F', 'insurer': 'Aetna',
            'insurer_type': 'commercial',
            'diagnoses': ['J06.9'],
            'notes': 'FALSE POSITIVE CONTROL -- healthy, acute URI only',
        },
    ]


# ======================================================================
# Billing engine fixture
# ======================================================================
@pytest.fixture(scope='function')
def billing_engine(app, db_session):
    """Create a BillingCaptureEngine instance for testing."""
    from billing_engine.engine import BillingCaptureEngine
    engine = BillingCaptureEngine(db=db_session)
    return engine


# ======================================================================
# Sample patient data -- dict matching BillingCaptureEngine.evaluate() schema
# ======================================================================
@pytest.fixture(scope='function')
def sample_patient_data():
    """Return a patient_data dict matching the evaluate() schema.

    This is a Medicare 67F with 4 chronic conditions -- should trigger
    AWV, CCM, and multiple screening detectors.
    """
    from datetime import date, timedelta
    return {
        'mrn': '90001',
        'patient_name': 'Margaret Wilson',
        'age': 67,
        'sex': 'F',
        'dob': '1958-03-15',
        'insurer': 'Medicare',
        'insurer_type': 'medicare',
        'diagnoses': [
            {'code': 'I10', 'description': 'Essential hypertension'},
            {'code': 'E11.9', 'description': 'Type 2 diabetes without complications'},
            {'code': 'E78.5', 'description': 'Hyperlipidemia, unspecified'},
            {'code': 'M81.0', 'description': 'Age-related osteoporosis without fracture'},
        ],
        'medications': [
            {'name': 'lisinopril', 'dose': '20mg', 'frequency': 'daily'},
            {'name': 'metformin', 'dose': '1000mg', 'frequency': 'twice daily'},
            {'name': 'atorvastatin', 'dose': '40mg', 'frequency': 'daily'},
            {'name': 'alendronate', 'dose': '70mg', 'frequency': 'weekly'},
        ],
        'vitals': {
            'bp_systolic': 138, 'bp_diastolic': 82,
            'weight_lbs': 165, 'height_in': 64, 'bmi': 28.3,
        },
        'last_awv_date': None,
        'last_visit_date': (date.today() - timedelta(days=90)).isoformat(),
        'visit_type': 'office',
        'face_to_face_minutes': 35,
        'ccm_enrolled': True,
        'ccm_minutes_this_month': 25,
        'user_id': 1,
    }
