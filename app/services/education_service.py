"""
CareCompanion — Education Service

Medication education message drafting.
Extracted from routes/intelligence.py (Band 3 B1.17).
"""

import logging
from datetime import datetime, timezone

from models import db
from models.patient import PatientRecord

logger = logging.getLogger(__name__)


def build_pricing_paragraph(drug_name):
    """
    Build a pricing information paragraph for a drug.

    Returns a string paragraph or empty string if no pricing found.
    Calls PricingService to look up Cost Plus Drugs / GoodRx / PAP data.
    """
    if not drug_name:
        return ''
    try:
        from app.services.pricing_service import PricingService
        svc = PricingService(db)
        pricing = svc.get_pricing(
            rxcui=None, ndc=None,
            drug_name=drug_name.split()[0],
            strength=None,
        )
        parts = []
        if pricing.get('source') == 'cost_plus' and pricing.get('price_monthly_estimate') is not None:
            parts.append(
                f"Pricing information: This medication may be available at Cost Plus Drugs pharmacy "
                f"for approximately ${pricing['price_monthly_estimate']:.2f}/month. "
                f"Visit: {pricing.get('direct_url', 'https://costplusdrugs.com')}"
            )
        elif pricing.get('source') == 'goodrx' and pricing.get('price_monthly_estimate') is not None:
            parts.append(
                f"Pricing information: You may be able to save on this medication using a GoodRx discount. "
                f"Estimated price: ${pricing['price_monthly_estimate']:.2f}/month. "
                f"Visit: {pricing.get('direct_url', 'https://www.goodrx.com')}"
            )
        programs = pricing.get('assistance_programs') or []
        if programs:
            prog = programs[0]
            parts.append(
                f"Financial assistance may be available for this medication. "
                f"Visit {prog.get('application_url', '')} for eligibility information."
            )
        return '\n'.join(parts)
    except Exception:
        return ''


def auto_draft_education_message(user_id, mrn, new_meds):
    """
    Create draft DelayedMessage records for each new medication detected.

    Called from clinical_summary_parser._trigger_new_med_education().
    Does NOT auto-send — creates drafts for provider review.

    Parameters
    ----------
    user_id : int
    mrn : str
    new_meds : list[dict]
        Each: {'drug_name': str, 'rxcui': str, 'start_date': str}

    Returns
    -------
    int
        Number of drafts created.
    """
    from models.message import DelayedMessage
    from models.notification import Notification

    if not new_meds:
        return 0

    record = PatientRecord.query.filter_by(user_id=user_id, mrn=mrn).first()
    recipient = record.patient_name if record and record.patient_name else mrn

    # Check for existing pending drafts to avoid duplicates
    existing_pending = DelayedMessage.query.filter_by(
        user_id=user_id, status='pending',
    ).all()
    existing_drug_names = set()
    for msg in existing_pending:
        content_lower = (msg.message_content or '').lower()
        if 'new medication education' in content_lower:
            for line in (msg.message_content or '').split('\n'):
                if line.startswith('Regarding: '):
                    existing_drug_names.add(line[len('Regarding: '):].strip().lower())

    drafts_created = 0
    for med in new_meds:
        drug_name = med.get('drug_name', '').strip()
        if not drug_name:
            continue
        if drug_name.lower() in existing_drug_names:
            continue

        body_parts = [f"New Medication Education: {drug_name}"]
        body_parts.append(f"Regarding: {drug_name}")
        if med.get('start_date'):
            body_parts.append(f"Started: {med['start_date']}")

        pricing_para = build_pricing_paragraph(drug_name)
        if pricing_para:
            body_parts.append(f"\n{pricing_para}")

        body_parts.append("\n— Auto-drafted by CareCompanion (review before sending)")

        draft = DelayedMessage(
            user_id=user_id,
            recipient_identifier=recipient,
            message_content="\n".join(body_parts),
            scheduled_send_at=datetime.now(timezone.utc),
            status='pending',
        )
        db.session.add(draft)
        drafts_created += 1

    if drafts_created > 0:
        mrn_tail = mrn
        notif = Notification(
            user_id=user_id,
            message=(
                f"\U0001f4cb {drafts_created} new medication education "
                f"draft{'s' if drafts_created != 1 else ''} created for {mrn_tail}"
            ),
            priority=2,
        )
        db.session.add(notif)
        db.session.commit()

    return drafts_created
