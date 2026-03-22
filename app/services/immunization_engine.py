"""
CareCompanion — Immunization Series Engine
File: app/services/immunization_engine.py

Phase 24.3 — Multi-dose vaccine series tracking engine.
Defines CDC-based schedules for 8 vaccine groups:
  Shingrix, HepB, HepA, HPV, COVID, RSV, MenACWY, MenB

Provides:
  - populate_patient_series(mrn_hash, user_id)  — scan PatientImmunization
    records and create/update ImmunizationSeries entries
  - get_series_gaps(mrn_hash, user_id, age, today)  — return incomplete
    series with open dose windows
  - get_seasonal_alerts(age, today)  — flu window + age-eligible alerts
"""

import logging
from datetime import date, timedelta

from models import db
from models.immunization import ImmunizationSeries
from models.patient import PatientImmunization

logger = logging.getLogger(__name__)

# ── CDC-based series definitions ──────────────────────────────────
# Each entry: (vaccine_group, cpt, total_doses, age_min, age_max,
#              dose_intervals_days, dose_window_end_days, seasonal,
#              season_start_month, season_end_month, vaccine_names_regex)
SERIES_DEFINITIONS = [
    {
        'group': 'Shingrix',
        'cpt': '90750',
        'total_doses': 2,
        'age_min': 50,
        'age_max': 999,
        'dose_intervals': [0, 60],       # dose 2 ≥ 2 months after dose 1
        'dose_windows': [0, 180],        # dose 2 within 6 months ideally
        'match_names': ['shingrix', 'zoster', 'herpes zoster'],
    },
    {
        'group': 'HepB',
        'cpt': '90739',
        'total_doses': 2,                # Heplisav-B is 2-dose
        'age_min': 18,
        'age_max': 999,
        'dose_intervals': [0, 28],       # dose 2 ≥ 28 days
        'dose_windows': [0, 120],
        'match_names': ['heplisav', 'hepatitis b', 'hepb', 'engerix', 'recombivax'],
    },
    {
        'group': 'HepA',
        'cpt': '90632',
        'total_doses': 2,
        'age_min': 1,
        'age_max': 999,
        'dose_intervals': [0, 180],      # dose 2 ≥ 6 months
        'dose_windows': [0, 365],
        'match_names': ['hepatitis a', 'hepa', 'havrix', 'vaqta'],
    },
    {
        'group': 'HPV',
        'cpt': '90651',
        'total_doses': 3,                # 3-dose if started ≥15y; 2 if 9-14
        'age_min': 9,
        'age_max': 45,
        'dose_intervals': [0, 60, 120],  # dose 2 at 2mo, dose 3 at 6mo from dose 1
        'dose_windows': [0, 120, 365],
        'match_names': ['gardasil', 'hpv', 'human papilloma'],
    },
    {
        'group': 'COVID',
        'cpt': '91318',
        'total_doses': 1,                # updated annual dose; series=1 per season
        'age_min': 6,                    # months in practice, but 6y for adult panel
        'age_max': 999,
        'dose_intervals': [0],
        'dose_windows': [0],
        'match_names': ['covid', 'sars-cov', 'moderna', 'pfizer', 'novavax'],
        'seasonal': True,
        'season_start': 9,               # Sep
        'season_end': 3,                 # Mar
    },
    {
        'group': 'RSV',
        'cpt': '90680',
        'total_doses': 1,
        'age_min': 60,
        'age_max': 999,
        'dose_intervals': [0],
        'dose_windows': [0],
        'match_names': ['rsv', 'arexvy', 'abrysvo'],
    },
    {
        'group': 'MenACWY',
        'cpt': '90734',
        'total_doses': 2,
        'age_min': 11,
        'age_max': 55,
        'dose_intervals': [0, 240],      # booster at 16 (~5 years)
        'dose_windows': [0, 365],
        'match_names': ['menactra', 'menveo', 'menacwy', 'meningococcal'],
    },
    {
        'group': 'MenB',
        'cpt': '90620',
        'total_doses': 2,
        'age_min': 16,
        'age_max': 23,
        'dose_intervals': [0, 28],
        'dose_windows': [0, 180],
        'match_names': ['bexsero', 'trumenba', 'meningococcal b', 'menb'],
    },
]

# Seasonal-only alerts (not tied to ImmunizationSeries records)
SEASONAL_ALERTS = [
    {
        'group': 'Influenza',
        'alert': 'Annual flu vaccine recommended (Sep–Mar window)',
        'age_min': 6,
        'age_max': 999,
        'season_start': 9,
        'season_end': 3,
        'match_names': ['influenza', 'flu shot', 'fluzone', 'fluarix', 'flublok'],
    },
    {
        'group': 'Pneumococcal',
        'alert': 'PCV20 or PCV15+PPSV23 recommended for adults ≥65',
        'age_min': 65,
        'age_max': 999,
        'match_names': ['pneumovax', 'prevnar', 'pneumococcal', 'pcv20', 'pcv15', 'ppsv23'],
    },
]


def _match_vaccine(vaccine_name, match_names):
    """Check if a vaccine name matches any of the expected patterns."""
    lower = (vaccine_name or '').lower()
    return any(m in lower for m in match_names)


def populate_patient_series(mrn_hash, user_id):
    """
    Scan PatientImmunization records and create/update ImmunizationSeries.
    Returns count of series updated.
    """
    imms = (
        PatientImmunization.query
        .filter_by(user_id=user_id, mrn=mrn_hash)
        .order_by(PatientImmunization.date_given.asc())
        .all()
    )

    updated = 0
    for sdef in SERIES_DEFINITIONS:
        group = sdef['group']
        matching = [i for i in imms if _match_vaccine(i.vaccine_name, sdef['match_names'])]
        doses = len(matching)
        last_date = matching[-1].date_given.date() if matching and matching[-1].date_given else None

        # Find or create series entry
        series = ImmunizationSeries.query.filter_by(
            patient_mrn_hash=mrn_hash,
            user_id=user_id,
            vaccine_group=group,
        ).first()

        if not series:
            if doses == 0:
                continue  # No doses and no record — skip until relevant
            series = ImmunizationSeries(
                patient_mrn_hash=mrn_hash,
                user_id=user_id,
                vaccine_group=group,
                vaccine_cpt=sdef['cpt'],
                total_doses=sdef['total_doses'],
                age_min=sdef['age_min'],
                age_max=sdef['age_max'],
                seasonal=sdef.get('seasonal', False),
                season_start_month=sdef.get('season_start'),
                season_end_month=sdef.get('season_end'),
            )
            db.session.add(series)

        series.dose_number = doses
        series.dose_date = last_date

        # Compute next dose window
        if doses >= sdef['total_doses']:
            series.series_status = 'complete'
            series.next_dose_due_date = None
            series.next_dose_window_end = None
        elif last_date and doses < len(sdef.get('dose_intervals', [])):
            interval = sdef['dose_intervals'][doses]
            window_end = sdef['dose_windows'][doses] if doses < len(sdef.get('dose_windows', [])) else interval + 180
            series.next_dose_due_date = last_date + timedelta(days=interval)
            series.next_dose_window_end = last_date + timedelta(days=window_end)
            if date.today() > series.next_dose_window_end:
                series.series_status = 'overdue'
            else:
                series.series_status = 'in_progress'
        elif doses > 0:
            # Doses exist but beyond defined intervals — mark in progress
            series.series_status = 'in_progress'
            series.next_dose_due_date = last_date + timedelta(days=180)
            series.next_dose_window_end = last_date + timedelta(days=365)
        else:
            series.series_status = 'not_started'

        updated += 1

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception('Failed to update immunization series for %s', mrn_hash)
        return 0

    return updated


def get_series_gaps(mrn_hash, user_id, age, ref_date=None):
    """
    Return incomplete series with open dose windows for a patient.
    Returns list of dicts with gap info for morning briefing / chart flags.
    """
    today = ref_date or date.today()
    gaps = []

    entries = (
        ImmunizationSeries.query
        .filter_by(patient_mrn_hash=mrn_hash, user_id=user_id)
        .filter(ImmunizationSeries.series_status.in_(['in_progress', 'overdue', 'not_started']))
        .all()
    )

    for entry in entries:
        if age < entry.age_min or age > entry.age_max:
            continue

        # Skip seasonal vaccines outside their window
        if entry.seasonal:
            if entry.season_start_month and entry.season_end_month:
                if not _in_season(today.month, entry.season_start_month, entry.season_end_month):
                    continue

        gaps.append({
            'vaccine_group': entry.vaccine_group,
            'doses_received': entry.dose_number,
            'total_doses': entry.total_doses,
            'next_dose_due': str(entry.next_dose_due_date) if entry.next_dose_due_date else 'now',
            'window_end': str(entry.next_dose_window_end) if entry.next_dose_window_end else '',
            'status': entry.series_status,
            'overdue': entry.series_status == 'overdue',
            'cpt': entry.vaccine_cpt,
        })

    # Also check age-eligible series definitions that the patient has NO record for
    existing_groups = {e.vaccine_group for e in entries}
    for sdef in SERIES_DEFINITIONS:
        if sdef['group'] in existing_groups:
            continue
        if age < sdef['age_min'] or age > sdef['age_max']:
            continue
        if sdef.get('seasonal') and not _in_season(today.month, sdef.get('season_start', 1), sdef.get('season_end', 12)):
            continue
        gaps.append({
            'vaccine_group': sdef['group'],
            'doses_received': 0,
            'total_doses': sdef['total_doses'],
            'next_dose_due': 'now',
            'window_end': '',
            'status': 'not_started',
            'overdue': False,
            'cpt': sdef['cpt'],
        })

    return gaps


def get_seasonal_alerts(age, ref_date=None):
    """
    Return seasonal immunization alerts (flu, pneumococcal) based on
    current date and patient age.
    """
    today = ref_date or date.today()
    alerts = []

    for sa in SEASONAL_ALERTS:
        if age < sa['age_min'] or age > sa['age_max']:
            continue
        # Check season window if defined
        s_start = sa.get('season_start')
        s_end = sa.get('season_end')
        if s_start and s_end:
            if not _in_season(today.month, s_start, s_end):
                continue
        alerts.append({
            'group': sa['group'],
            'alert': sa['alert'],
            'priority': 'standard',
        })

    return alerts


def _in_season(current_month, start_month, end_month):
    """Check if current_month falls within a season window (wraps around year)."""
    if start_month <= end_month:
        return start_month <= current_month <= end_month
    else:
        # Wraps around year-end (e.g., Sep=9 to Mar=3)
        return current_month >= start_month or current_month <= end_month
