"""
CareCompanion -- VIIS Batch Lookup Service
File: app/services/viis_batch.py

Phase VIIS-2 + VIIS-3 -- Automated batch VIIS lookups with care gap auto-close.

Provides:
  - get_viis_eligible_patients(user_id, app) -- find patients needing VIIS check
  - run_viis_batch(user_id, app)             -- nightly batch for tomorrow's schedule
  - run_viis_single(mrn, user_id, app)       -- manual single-patient check
  - process_single_patient(...)              -- persist results + auto-close gaps
"""

import asyncio
import hashlib
import json
import logging
import random
import re
from datetime import date, datetime, timedelta, timezone

import config

logger = logging.getLogger('carecompanion.viis_batch')

# ── Vaccine name -> care gap type mapping (fuzzy) ────────────────
# Each tuple: (search_terms, gap_type)
VACCINE_GAP_MAP = [
    (['influenza', 'flu'], 'flu_vaccine'),
    (['covid', 'sars-cov', 'moderna', 'pfizer', 'bivalent'], 'covid_vaccine'),
    (['zoster', 'shingrix'], 'shingrix'),
    (['tdap', 'tetanus', 'adacel', 'boostrix', 'diphtheria'], 'tdap'),
    (['pneumo', 'prevnar', 'ppsv23', 'pcv20', 'pcv15', 'pneumovax'], 'pneumococcal'),
]


def _match_vaccine_to_gap_type(vaccine_name):
    """Map a VIIS vaccine name to a care gap type using fuzzy matching.

    Returns the gap_type string or None if no match found.
    """
    name_lower = vaccine_name.lower()
    for search_terms, gap_type in VACCINE_GAP_MAP:
        for term in search_terms:
            if term in name_lower:
                return gap_type
    return None


def _hash_mrn(mrn):
    """HIPAA-safe MRN hash for logging."""
    return hashlib.sha256(mrn.encode()).hexdigest()[:12]


def get_viis_eligible_patients(user_id, app):
    """Find patients on tomorrow's schedule who need a VIIS check.

    Eligibility criteria:
    1. On tomorrow's schedule
    2. Have at least one open vaccine-related care gap
    3. No successful VIISCheck in the last N days (config.VIIS_CHECK_INTERVAL_DAYS)

    Returns list of dicts: [{mrn, first_name, last_name, dob}, ...]
    """
    from models.schedule import Schedule
    from models.patient import PatientRecord
    from models.caregap import CareGap
    from models.viis import VIISCheck
    from models.user import User

    # Read interval from user prefs (fall back to config)
    with app.app_context():
        user = User.query.get(user_id)
    interval_days = int(user.get_pref('viis_check_interval_days',
                        getattr(config, 'VIIS_CHECK_INTERVAL_DAYS', 365))) if user else 365
    cutoff = datetime.now(timezone.utc) - timedelta(days=interval_days)
    tomorrow = date.today() + timedelta(days=1)

    # Vaccine-related gap types
    vaccine_gap_types = [
        'flu_vaccine', 'covid_vaccine', 'shingrix', 'tdap', 'pneumococcal',
    ]

    with app.app_context():
        # Step 1: Get tomorrow's scheduled patient MRNs
        appts = Schedule.query.filter_by(
            user_id=user_id, appointment_date=tomorrow
        ).all()
        scheduled_mrns = list({a.patient_mrn for a in appts if a.patient_mrn})

        if not scheduled_mrns:
            logger.info('VIIS batch: no patients scheduled for tomorrow')
            return []

        # Step 2: Filter to patients with open vaccine care gaps
        patients_with_gaps = set()
        for mrn in scheduled_mrns:
            open_vaccine_gaps = CareGap.query.filter(
                CareGap.user_id == user_id,
                CareGap.mrn == mrn,
                CareGap.gap_type.in_(vaccine_gap_types),
                CareGap.status == 'open',
                CareGap.is_addressed == False,
            ).first()
            if open_vaccine_gaps:
                patients_with_gaps.add(mrn)

        if not patients_with_gaps:
            logger.info('VIIS batch: no patients with open vaccine care gaps')
            return []

        # Step 3: Exclude patients checked recently
        eligible = []
        for mrn in patients_with_gaps:
            recent_check = VIISCheck.query.filter(
                VIISCheck.user_id == user_id,
                VIISCheck.mrn == mrn,
                VIISCheck.checked_at >= cutoff,
                VIISCheck.status.in_(['found', 'not_found']),
            ).first()
            if recent_check:
                continue  # Checked recently, skip

            # Get patient record for name/DOB
            record = PatientRecord.query.filter_by(
                user_id=user_id, mrn=mrn
            ).first()
            if not record or not record.patient_name or not record.patient_dob:
                continue

            # Parse name
            name = record.patient_name.strip()
            parts = name.split(',') if ',' in name else name.rsplit(' ', 1)
            if len(parts) >= 2:
                last_name = parts[0].strip()
                first_name = parts[1].strip().split()[0] if parts[1].strip() else ''
            else:
                last_name = name
                first_name = ''

            if not first_name or not last_name:
                continue

            # Format DOB
            dob = (record.patient_dob or '').strip()
            if len(dob) == 8 and dob.isdigit():
                dob = f"{dob[:4]}-{dob[4:6]}-{dob[6:8]}"

            eligible.append({
                'mrn': mrn,
                'first_name': first_name,
                'last_name': last_name,
                'dob': dob,
            })

        logger.info(
            'VIIS batch: %d eligible of %d scheduled (%d with gaps)',
            len(eligible), len(scheduled_mrns), len(patients_with_gaps),
        )
        return eligible


def process_single_patient(mrn, result, user_id, batch_run_id, app):
    """Persist VIIS lookup results and auto-close matching care gaps.

    Parameters
    ----------
    mrn : str
        Patient MRN.
    result : dict
        VIISScraper.lookup_patient() result dict.
    user_id : int
        Current user.
    batch_run_id : int or None
        VIISBatchRun.id (None for manual checks).
    app : Flask app instance.

    Returns
    -------
    dict with keys: status, immunization_count, gaps_closed
    """
    from models import db
    from models.viis import VIISCheck
    from models.patient import PatientImmunization
    from models.caregap import CareGap

    with app.app_context():
        success = result.get('success', False)
        immunizations = result.get('immunizations', [])

        # Determine status
        if not success:
            status = 'error'
        elif immunizations:
            status = 'found'
        else:
            status = 'not_found'

        # Create VIISCheck record
        check = VIISCheck(
            user_id=user_id,
            mrn=mrn,
            status=status,
            immunization_count=len(immunizations),
            error_message=result.get('error', '') if status == 'error' else None,
            checked_at=datetime.now(timezone.utc),
            raw_response=json.dumps(result, default=str),
            batch_run_id=batch_run_id,
        )
        db.session.add(check)
        db.session.flush()  # Get check.id for FK

        gaps_closed = 0

        # Persist immunization records and auto-close gaps
        for imm in immunizations:
            vaccine_name = imm.get('vaccine', '').strip()
            date_str = imm.get('date_given', '').strip()
            if not vaccine_name:
                continue

            # Parse date_given
            date_given = None
            for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y', '%m/%d/%y']:
                try:
                    date_given = datetime.strptime(date_str, fmt)
                    break
                except (ValueError, TypeError):
                    continue

            # Deduplicate: check if this exact record already exists
            existing = PatientImmunization.query.filter_by(
                mrn=mrn,
                vaccine_name=vaccine_name,
                date_given=date_given,
                source='viis',
            ).first()

            if not existing:
                new_imm = PatientImmunization(
                    user_id=user_id,
                    mrn=mrn,
                    vaccine_name=vaccine_name,
                    date_given=date_given,
                    source='viis',
                    viis_check_id=check.id,
                )
                db.session.add(new_imm)

            # Auto-close matching care gaps (VIIS-3)
            gap_type = _match_vaccine_to_gap_type(vaccine_name)
            if gap_type:
                open_gaps = CareGap.query.filter(
                    CareGap.user_id == user_id,
                    CareGap.mrn == mrn,
                    CareGap.gap_type == gap_type,
                    CareGap.status == 'open',
                    CareGap.is_addressed == False,
                ).all()

                for gap in open_gaps:
                    gap.is_addressed = True
                    gap.addressed_date = date_given or datetime.now(timezone.utc)
                    date_display = date_given.strftime('%m/%d/%Y') if date_given else 'unknown date'
                    gap.notes = (gap.notes or '') + f'\nAuto-closed: VIIS record ({vaccine_name}) from {date_display}'
                    gaps_closed += 1

        # Update multi-dose series if applicable (VIIS-3.4)
        _update_immunization_series(mrn, user_id, immunizations, app)

        db.session.commit()
        logger.info(
            'VIIS: processed MRN %s -- status=%s, imm=%d, gaps_closed=%d',
            _hash_mrn(mrn), status, len(immunizations), gaps_closed,
        )

        return {
            'status': status,
            'immunization_count': len(immunizations),
            'gaps_closed': gaps_closed,
        }


def _update_immunization_series(mrn, user_id, immunizations, app):
    """Update ImmunizationSeries entries for multi-dose vaccines from VIIS data."""
    from models.immunization import ImmunizationSeries
    from billing_engine.shared import hash_mrn

    mrn_hash = hash_mrn(mrn)

    for imm in immunizations:
        vaccine_name = imm.get('vaccine', '').lower()
        date_str = imm.get('date_given', '')

        # Parse date
        dose_date = None
        for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y', '%m/%d/%y']:
            try:
                dose_date = datetime.strptime(date_str, fmt).date()
                break
            except (ValueError, TypeError):
                continue

        if not dose_date:
            continue

        # Match to series group
        series_group = None
        if any(t in vaccine_name for t in ['shingrix', 'zoster']):
            series_group = 'Shingrix'
        elif any(t in vaccine_name for t in ['heplisav', 'hepatitis b', 'hepb', 'engerix']):
            series_group = 'HepB'
        elif any(t in vaccine_name for t in ['hepatitis a', 'hepa', 'havrix', 'vaqta']):
            series_group = 'HepA'

        if not series_group:
            continue

        # Find existing series
        series = ImmunizationSeries.query.filter_by(
            patient_mrn_hash=mrn_hash,
            user_id=user_id,
            vaccine_group=series_group,
        ).first()

        if series:
            # Update dose count if this date is newer
            if not series.dose_date or dose_date > series.dose_date:
                series.dose_number = min(series.dose_number + 1, series.total_doses)
                series.dose_date = dose_date
                if series.dose_number >= series.total_doses:
                    series.series_status = 'complete'
                else:
                    series.series_status = 'in_progress'


def run_viis_batch(user_id, app):
    """Run a full VIIS batch lookup for tomorrow's eligible patients.

    Creates a VIISBatchRun, iterates patients with human-like delays,
    and sends a Pushover notification on completion.

    Parameters
    ----------
    user_id : int
    app : Flask app instance

    Returns
    -------
    VIISBatchRun.id or None on complete failure
    """
    from models import db
    from models.viis import VIISBatchRun
    from models.user import User

    # Check user preference (fall back to config)
    with app.app_context():
        user = User.query.get(user_id)
    if user:
        enabled = user.get_pref('viis_batch_enabled',
                    getattr(config, 'VIIS_BATCH_ENABLED', False))
    else:
        enabled = getattr(config, 'VIIS_BATCH_ENABLED', False)
    if not enabled:
        logger.info('VIIS batch disabled for user %d', user_id)
        return None

    with app.app_context():
        # Check for abandoned batch run to resume
        stale_run = VIISBatchRun.query.filter_by(
            user_id=user_id, status='running'
        ).first()

        if stale_run:
            logger.info('VIIS batch: resuming stale run %d', stale_run.id)
            batch_run = stale_run
        else:
            eligible = get_viis_eligible_patients(user_id, app)
            batch_run = VIISBatchRun(
                user_id=user_id,
                total_eligible=len(eligible),
                status='running',
            )
            db.session.add(batch_run)
            db.session.commit()

            if not eligible:
                batch_run.status = 'completed'
                batch_run.completed_at = datetime.now(timezone.utc)
                db.session.commit()
                logger.info('VIIS batch: no eligible patients, marking complete')
                return batch_run.id

        # Get eligible patients (re-fetch if resuming)
        eligible = get_viis_eligible_patients(user_id, app)
        batch_run.total_eligible = len(eligible)

        # If resuming, skip already-processed patients
        resume_from = batch_run.last_mrn_processed
        if resume_from:
            skip = True
            filtered = []
            for p in eligible:
                if skip and p['mrn'] == resume_from:
                    skip = False
                    continue  # Skip the already-processed one
                if not skip:
                    filtered.append(p)
            eligible = filtered
            logger.info('VIIS batch: resuming after MRN %s, %d remaining',
                        _hash_mrn(resume_from), len(eligible))

        # Instantiate scraper
        try:
            from scrapers.viis import VIISScraper
            scraper = VIISScraper(app)
        except ImportError:
            logger.error('VIIS batch: scraper not available')
            batch_run.status = 'failed'
            batch_run.completed_at = datetime.now(timezone.utc)
            db.session.commit()
            return batch_run.id

        # Process each patient with human-like delays
        delay_min = int(user.get_pref('viis_delay_min',
                        getattr(config, 'VIIS_DELAY_MIN', 5))) if user else 5
        delay_max = int(user.get_pref('viis_delay_max',
                        getattr(config, 'VIIS_DELAY_MAX', 15))) if user else 15
        auth_retried = False

        for patient in eligible:
            mrn = patient['mrn']

            try:
                result = asyncio.run(scraper.lookup_patient(
                    first_name=patient['first_name'],
                    last_name=patient['last_name'],
                    dob=patient['dob'],
                ))

                # Detect auth failure and retry once
                error_msg = result.get('error', '').lower()
                if not result.get('success') and 'login' in error_msg and not auth_retried:
                    logger.warning('VIIS batch: auth failure, retrying login...')
                    auth_retried = True
                    result = asyncio.run(scraper.lookup_patient(
                        first_name=patient['first_name'],
                        last_name=patient['last_name'],
                        dob=patient['dob'],
                    ))

                # If still failing on auth after retry, mark partial and stop
                if not result.get('success') and 'login' in error_msg and auth_retried:
                    logger.error('VIIS batch: auth failed after retry, stopping batch')
                    batch_run.status = 'partial'
                    batch_run.completed_at = datetime.now(timezone.utc)
                    batch_run.total_errors += 1
                    db.session.commit()
                    _send_viis_notification(batch_run, error='Session expired after retry')
                    return batch_run.id

                # Process this patient's results
                outcome = process_single_patient(mrn, result, user_id, batch_run.id, app)

                # Update batch counters
                batch_run.total_checked += 1
                batch_run.last_mrn_processed = mrn
                if outcome['status'] == 'found':
                    batch_run.total_found += 1
                elif outcome['status'] == 'not_found':
                    batch_run.total_not_found += 1
                else:
                    batch_run.total_errors += 1
                batch_run.gaps_closed += outcome.get('gaps_closed', 0)
                db.session.commit()

            except Exception as e:
                logger.warning('VIIS batch: error on MRN %s: %s', _hash_mrn(mrn), e)
                batch_run.total_checked += 1
                batch_run.total_errors += 1
                batch_run.last_mrn_processed = mrn
                db.session.commit()

            # Human-like delay between lookups
            if patient != eligible[-1]:
                delay = random.uniform(delay_min, delay_max)
                import time
                time.sleep(delay)

        # Batch complete
        batch_run.status = 'completed'
        batch_run.completed_at = datetime.now(timezone.utc)
        db.session.commit()

        _send_viis_notification(batch_run)
        logger.info(
            'VIIS batch complete: %d/%d checked, %d found, %d not found, '
            '%d errors, %d gaps closed',
            batch_run.total_checked, batch_run.total_eligible,
            batch_run.total_found, batch_run.total_not_found,
            batch_run.total_errors, batch_run.gaps_closed,
        )
        return batch_run.id


def run_viis_single(mrn, user_id, app):
    """Run a single VIIS check for one patient (manual trigger).

    Returns dict with check results or error info.
    """
    from models.patient import PatientRecord

    with app.app_context():
        record = PatientRecord.query.filter_by(
            user_id=user_id, mrn=mrn
        ).first()

        if not record or not record.patient_name:
            return {'success': False, 'error': 'Patient record not found'}

        # Parse name
        name = record.patient_name.strip()
        parts = name.split(',') if ',' in name else name.rsplit(' ', 1)
        if len(parts) >= 2:
            last_name = parts[0].strip()
            first_name = parts[1].strip().split()[0] if parts[1].strip() else ''
        else:
            last_name = name
            first_name = ''

        dob = (record.patient_dob or '').strip()
        if len(dob) == 8 and dob.isdigit():
            dob = f"{dob[:4]}-{dob[4:6]}-{dob[6:8]}"

        if not first_name or not last_name or not dob:
            return {'success': False, 'error': 'Patient name or DOB incomplete'}

        try:
            from scrapers.viis import VIISScraper
            scraper = VIISScraper(app)
            result = asyncio.run(scraper.lookup_patient(first_name, last_name, dob))
        except Exception as e:
            logger.warning('VIIS single check failed for MRN %s: %s', _hash_mrn(mrn), e)
            result = {
                'success': False,
                'immunizations': [],
                'error': str(e),
                'checked_at': datetime.now(timezone.utc).isoformat(),
            }

        # Persist results
        outcome = process_single_patient(mrn, result, user_id, None, app)
        return {
            'success': result.get('success', False),
            'immunizations': result.get('immunizations', []),
            'status': outcome['status'],
            'immunization_count': outcome['immunization_count'],
            'gaps_closed': outcome['gaps_closed'],
            'checked_at': result.get('checked_at', datetime.now(timezone.utc).isoformat()),
        }


def _send_viis_notification(batch_run, error=None):
    """Send Pushover notification with batch results (counts only, no PHI)."""
    try:
        from agent.notifier import _send_pushover

        user_key = getattr(config, 'PUSHOVER_USER_KEY', '')
        api_token = getattr(config, 'PUSHOVER_API_TOKEN', '')
        if not user_key or not api_token:
            return

        if error:
            msg = (
                f'VIIS batch failed after {batch_run.total_checked}/'
                f'{batch_run.total_eligible} patients: {error}'
            )
            _send_pushover(user_key, api_token,
                           title='VIIS Pre-Visit Check Failed',
                           message=msg, priority=0, sound='pushover')
        else:
            parts = [
                f'{batch_run.total_checked}/{batch_run.total_eligible} checked',
                f'{batch_run.total_found} found',
                f'{batch_run.total_not_found} not found',
            ]
            if batch_run.total_errors:
                parts.append(f'{batch_run.total_errors} errors')
            if batch_run.gaps_closed:
                parts.append(f'{batch_run.gaps_closed} gaps closed')
            msg = 'VIIS pre-visit: ' + ', '.join(parts)
            _send_pushover(user_key, api_token,
                           title='VIIS Pre-Visit Check Complete',
                           message=msg, priority=-1, sound='none')
    except Exception as e:
        logger.warning('VIIS notification failed: %s', e)
