"""
CareCompanion — DailyMed API Service
File: app/services/api/dailymed.py

Queries NLM DailyMed for FDA-approved drug labeling, medication
guides, and REMS program flags. Supplements OpenFDA labels with
manufacturer-specific medication guides (especially useful for
generics where OpenFDA data may be incomplete).

Phase 23 additions: SPL section parsing for automated monitoring
requirement extraction (regex + LLM fallback).  Populates
MonitoringRule entries dynamically from drug labeling text.

Base URL: https://dailymed.nlm.nih.gov/dailymed/services/v2
Auth: None required
Rate limit: No documented limit — cache aggressively as courtesy

Dependencies:
- app/services/api/base_client.py (BaseAPIClient)
- app/api_config.py (DAILYMED_BASE_URL, DAILYMED_CACHE_TTL_DAYS)
- models/api_cache.py (LoincCache, RxClassCache)
- models/monitoring.py (MonitoringRule)

CareCompanion features that rely on this module:
- Patient Education (NEW-E) — medication guide links
- Drug Safety Panel (NEW-A) — REMS program alerts
- Phase 23 — Dynamic monitoring rule extraction from SPL text
"""

import json
import logging
import os
import re
import time
import urllib.request as _urllib_req
import urllib.error as _urllib_err
from html import unescape as _html_unescape

from app.api_config import DAILYMED_BASE_URL, DAILYMED_CACHE_TTL_DAYS
from app.services.api.base_client import BaseAPIClient, APIUnavailableError
from models.api_cache import LoincCache, RxClassCache

# ── SPL section codes (LOINC) containing monitoring language ───────
_MONITORING_SECTION_CODES = {
    '43685-7': 'Warnings and Precautions',
    '34073-7': 'Drug Interactions',
    '34076-0': 'Information for Patients',
    '42232-9': 'Precautions',
    '34084-4': 'Adverse Reactions',
}

# ── Drug classes known to require multi-lab monitoring ─────────────
# LLM fallback fires only when regex yields ≤1 result AND the drug
# belongs to one of these ATC/EPC classes (via RxClassCache lookup).
_HIGH_MONITORING_CLASSES = frozenset({
    'C09AA', 'C09CA',   # ACE inhibitors, ARBs
    'N05AH',             # Atypical antipsychotics
    'N03AG',             # Valproic acid derivatives
    'C01BD',             # Antiarrhythmics (amiodarone)
    'B01AF',             # DOACs
    'L04AX',             # Immunosuppressants
    'H02AB',             # Corticosteroids
    'M05BA',             # Bisphosphonates
    'A10BK',             # SGLT-2 inhibitors
    'C03DA',             # K-sparing diuretics (spironolactone)
    'C01AA',             # Cardiac glycosides (digoxin)
    'C03CA',             # Loop diuretics
    'C03AA',             # Thiazide diuretics
    'N03AF',             # Carbamazepine class
    'N05AH03',           # Olanzapine
})

# ── Interval keyword → days mapping ───────────────────────────────
_INTERVAL_MAP = {
    'weekly': 7, 'every week': 7, 'every 1 week': 7,
    'biweekly': 14, 'bi-weekly': 14, 'every 2 weeks': 14,
    'every two weeks': 14,
    'monthly': 30, 'every month': 30, 'every 4 weeks': 28,
    'every 2 months': 60, 'every 3 months': 90,
    'quarterly': 90, 'every 4 months': 120,
    'every 6 months': 180, 'semiannually': 180, 'semi-annually': 180,
    'annually': 365, 'every year': 365, 'every 12 months': 365,
    'at baseline': 0, 'before initiating': 0,
    'prior to initiation': 0, 'prior to starting': 0,
    'periodically': 180, 'periodic': 180,
    'regularly': 180, 'routine': 180,
}

# ── Common lab name → (loinc_code, cpt_code, display_name) ────────
# Fallback when LoincCache has no match.  Covers the labs most
# frequently referenced in drug labeling monitoring language.
_COMMON_LAB_MAP = {
    'cbc': ('85025', '85025', 'CBC with Differential'),
    'complete blood count': ('85025', '85025', 'CBC with Differential'),
    'anc': ('26499-4', '85025', 'Absolute Neutrophil Count'),
    'absolute neutrophil count': ('26499-4', '85025', 'ANC'),
    'basic metabolic panel': ('80048', '80048', 'Basic Metabolic Panel'),
    'bmp': ('80048', '80048', 'Basic Metabolic Panel'),
    'comprehensive metabolic panel': ('80053', '80053', 'CMP'),
    'cmp': ('80053', '80053', 'CMP'),
    'hepatic function panel': ('80076', '80076', 'Hepatic Function Panel'),
    'hepatic function': ('80076', '80076', 'Hepatic Function Panel'),
    'liver function': ('80076', '80076', 'Hepatic Function Panel'),
    'liver function tests': ('80076', '80076', 'Hepatic Function Panel'),
    'lft': ('80076', '80076', 'Hepatic Function Panel'),
    'lfts': ('80076', '80076', 'Hepatic Function Panel'),
    'renal function': ('80048', '80048', 'Renal Function Panel'),
    'kidney function': ('80048', '80048', 'Renal Function Panel'),
    'tsh': ('84443', '84443', 'TSH'),
    'thyroid stimulating hormone': ('84443', '84443', 'TSH'),
    'thyroid function': ('84443', '84443', 'TSH'),
    'hemoglobin a1c': ('4548-4', '83036', 'Hemoglobin A1C'),
    'hba1c': ('4548-4', '83036', 'Hemoglobin A1C'),
    'a1c': ('4548-4', '83036', 'Hemoglobin A1C'),
    'glycated hemoglobin': ('4548-4', '83036', 'Hemoglobin A1C'),
    'lipid panel': ('80061', '80061', 'Lipid Panel'),
    'lipids': ('80061', '80061', 'Lipid Panel'),
    'fasting lipids': ('80061', '80061', 'Lipid Panel'),
    'potassium': ('2823-3', '80051', 'Potassium'),
    'serum potassium': ('2823-3', '80051', 'Potassium'),
    'creatinine': ('2160-0', '82565', 'Creatinine'),
    'serum creatinine': ('2160-0', '82565', 'Creatinine'),
    'egfr': ('33914-3', '80048', 'eGFR'),
    'glomerular filtration rate': ('33914-3', '80048', 'eGFR'),
    'urine albumin-creatinine ratio': ('14959-1', '82043', 'UACR'),
    'uacr': ('14959-1', '82043', 'UACR'),
    'microalbumin': ('14959-1', '82043', 'Urine Microalbumin'),
    'bnp': ('42637-9', '83880', 'BNP'),
    'nt-probnp': ('33762-6', '83880', 'NT-proBNP'),
    'iron studies': ('2498-4', '83540', 'Iron Studies'),
    'serum iron': ('2498-4', '83540', 'Serum Iron'),
    'inr': ('6301-6', '85610', 'INR'),
    'pt/inr': ('6301-6', '85610', 'INR'),
    'afp': ('1834-1', '82105', 'AFP'),
    'alpha-fetoprotein': ('1834-1', '82105', 'AFP'),
    'phosphorus': ('2777-1', '84100', 'Phosphorus'),
    'calcium': ('17861-6', '82310', 'Calcium'),
    'serum calcium': ('17861-6', '82310', 'Calcium'),
    'pth': ('2731-8', '83970', 'PTH'),
    'parathyroid hormone': ('2731-8', '83970', 'PTH'),
    'magnesium': ('19123-9', '83735', 'Magnesium'),
    'glucose': ('2345-7', '82947', 'Glucose'),
    'fasting glucose': ('2345-7', '82947', 'Fasting Glucose'),
    'blood glucose': ('2345-7', '82947', 'Glucose'),
    'uric acid': ('3084-1', '84550', 'Uric Acid'),
    'esr': ('30341-2', '85651', 'ESR'),
    'erythrocyte sedimentation rate': ('30341-2', '85651', 'ESR'),
    'crp': ('1988-5', '86140', 'CRP'),
    'c-reactive protein': ('1988-5', '86140', 'CRP'),
    'ammonia': ('1925-7', '82140', 'Ammonia'),
    'sodium': ('2951-2', '84295', 'Sodium'),
    'serum sodium': ('2951-2', '84295', 'Sodium'),
    'free t4': ('3024-7', '84439', 'Free T4'),
    'thyroxine': ('3024-7', '84439', 'Free T4'),
    'vitamin d': ('1989-3', '82306', 'Vitamin D'),
    '25-hydroxyvitamin d': ('1989-3', '82306', 'Vitamin D'),
    'digoxin level': ('10535-3', '80162', 'Digoxin Level'),
    'digoxin': ('10535-3', '80162', 'Digoxin Level'),
    'lithium level': ('14334-7', '80178', 'Lithium Level'),
    'lithium': ('14334-7', '80178', 'Lithium Level'),
    'phenytoin level': ('3968-5', '80185', 'Phenytoin Level'),
    'phenytoin': ('3968-5', '80185', 'Phenytoin Level'),
    'carbamazepine level': ('3432-2', '80156', 'Carbamazepine Level'),
    'valproic acid level': ('4086-5', '80164', 'Valproic Acid Level'),
    'valproic acid': ('4086-5', '80164', 'Valproic Acid Level'),
    'lamotrigine level': ('25127-0', '80175', 'Lamotrigine Level'),
    'phenobarbital level': ('3948-7', '80184', 'Phenobarbital Level'),
    'urinalysis': ('24356-8', '81001', 'Urinalysis'),
    'complement c3': ('4485-9', '86160', 'Complement C3'),
    'complement c4': ('4498-2', '86160', 'Complement C4'),
    'c3': ('4485-9', '86160', 'Complement C3'),
    'c4': ('4498-2', '86160', 'Complement C4'),
    'anti-dsdna': ('35209-9', '86235', 'Anti-dsDNA Antibody'),
    'albumin': ('1751-7', '82040', 'Albumin'),
    'serum albumin': ('1751-7', '82040', 'Albumin'),
    'bilirubin': ('1975-2', '82247', 'Total Bilirubin'),
    'total bilirubin': ('1975-2', '82247', 'Total Bilirubin'),
    'pregnancy test': ('2106-3', '81025', 'Pregnancy Test'),
    'hcg': ('2106-3', '81025', 'Pregnancy Test (HCG)'),
    'electrolytes': ('80051', '80051', 'Electrolyte Panel'),
    'pulmonary function': ('94010', '94010', 'Pulmonary Function Test'),
    'pft': ('94010', '94010', 'Pulmonary Function Test'),
    'spirometry': ('94010', '94010', 'Spirometry'),
    'chest x-ray': ('71046', '71046', 'Chest X-Ray'),
    'dexa': ('77080', '77080', 'DEXA Bone Density'),
    'bone density': ('77080', '77080', 'DEXA Bone Density'),
}

# ── Regex patterns for monitoring extraction ──────────────────────
_RE_STRIP_HTML = re.compile(r'<[^>]+>')

# Pattern 1: "Monitor/Check/Obtain [lab] [timing]"
_RE_MONITOR_ACTION = re.compile(
    r'(?:monitor|check|measure|assess|evaluate|obtain|order|perform|test|determine)\s+'
    r'(?:(?:serum|blood|urine|plasma|fasting|baseline)\s+)?'
    r'([\w\s\-/(),.]+?)'
    r'(?:\s+(?:levels?|concentrations?|counts?|values?|tests?|panels?))?'
    r'\s+'
    r'((?:at\s+)?baseline|'
    r'(?:prior\s+to|before)\s+(?:initiating|starting|treatment|therapy)|'
    r'(?:every|each)\s+\d+\s+(?:days?|weeks?|months?|years?)|'
    r'weekly|biweekly|bi-weekly|monthly|quarterly|semi-?annually|annually|'
    r'periodic(?:ally)?|regular(?:ly)?|routine(?:ly)?|'
    r'\d+\s*(?:-|to)\s*\d+\s+(?:days?|weeks?|months?)\s+(?:after|following))',
    re.IGNORECASE,
)

# Pattern 2: "[Lab] should be monitored [timing]"
_RE_PASSIVE_MONITOR = re.compile(
    r'([\w\s\-/(),.]+?)\s+'
    r'(?:should|must|needs?\s+to)\s+be\s+'
    r'(?:monitored|checked|measured|assessed|evaluated|obtained|tested)\s*'
    r'((?:at\s+)?baseline|'
    r'(?:prior\s+to|before)\s+(?:initiating|starting|treatment|therapy)|'
    r'(?:every|each)\s+\d+\s+(?:days?|weeks?|months?|years?)|'
    r'weekly|biweekly|bi-weekly|monthly|quarterly|semi-?annually|annually|'
    r'periodic(?:ally)?|regular(?:ly)?|routine(?:ly)?)',
    re.IGNORECASE,
)

# Pattern 3: "Recommend [timing] monitoring of [lab]"
_RE_RECOMMEND_MONITOR = re.compile(
    r'(?:recommend|suggest|advise)\w*\s+'
    r'((?:weekly|monthly|quarterly|annually|periodic|regular|routine|'
    r'(?:every|each)\s+\d+\s+(?:days?|weeks?|months?|years?))[\w\s]*?)\s+'
    r'(?:monitoring|testing|measurement|evaluation|assessment)\s+of\s+'
    r'([\w\s\-/(),.]+)',
    re.IGNORECASE,
)

# Interval extraction from free text
_RE_INTERVAL_EXACT = re.compile(
    r'every\s+(\d+)\s+(days?|weeks?|months?|years?)', re.IGNORECASE
)
_RE_INTERVAL_RANGE = re.compile(
    r'(\d+)\s*(?:-|to)\s*(\d+)\s+(weeks?|months?)\s+(?:after|following)',
    re.IGNORECASE,
)

# ── Hardcoded REMS program definitions ────────────────────────────
# Federally mandated programs with exact requirements.  Poor
# candidates for dynamic extraction — requirements are precise and
# well-known.  Dict keyed by lowercase drug name stem.
_REMS_PROGRAMS = {
    'clozapine': {
        'program_name': 'Clozapine REMS',
        'requirements': [
            {
                'type': 'ANC_CHECK',
                'description': (
                    'ANC required before each dispense. '
                    'ANC < 1500/\u00b5L (general) or < 1000/\u00b5L (BEN) = '
                    'dispense hold. Weekly \u00d7 6 mo \u2192 biweekly \u00d7 '
                    '6 mo \u2192 monthly thereafter.'
                ),
                'phase_schedule': {
                    'weekly':   {'interval_days': 7,  'duration_days': 180},
                    'biweekly': {'interval_days': 14, 'duration_days': 180},
                    'monthly':  {'interval_days': 30, 'duration_days': None},
                },
                'initial_phase': 'weekly',
            },
        ],
    },
    'isotretinoin': {
        'program_name': 'iPLEDGE',
        'requirements': [
            {
                'type': 'PREGNANCY_TEST',
                'description': (
                    'Monthly pregnancy test required for females of '
                    'reproductive potential before each 30-day prescription.'
                ),
                'phase_schedule': {
                    'monthly': {'interval_days': 30, 'duration_days': None},
                },
                'initial_phase': 'monthly',
            },
            {
                'type': 'REGISTRY_ENROLLMENT',
                'description': (
                    'Patient and prescriber must be enrolled in iPLEDGE '
                    'registry. Monthly confirmation of counseling and '
                    'contraception compliance.'
                ),
                'phase_schedule': {
                    'monthly': {'interval_days': 30, 'duration_days': None},
                },
                'initial_phase': 'monthly',
            },
        ],
    },
    'thalidomide': {
        'program_name': 'THALOMID REMS',
        'requirements': [
            {
                'type': 'PREGNANCY_TEST',
                'description': (
                    'Monthly pregnancy test required. 30-day dispense limit. '
                    'Mandatory patient registry enrollment.'
                ),
                'phase_schedule': {
                    'monthly': {'interval_days': 30, 'duration_days': None},
                },
                'initial_phase': 'monthly',
            },
            {
                'type': 'REGISTRY_ENROLLMENT',
                'description': (
                    'Patient, prescriber, and pharmacy must be enrolled in '
                    'THALOMID REMS program.'
                ),
                'phase_schedule': {
                    'monthly': {'interval_days': 30, 'duration_days': None},
                },
                'initial_phase': 'monthly',
            },
        ],
    },
    'lenalidomide': {
        'program_name': 'THALOMID REMS',
        'requirements': [
            {
                'type': 'PREGNANCY_TEST',
                'description': (
                    'Monthly pregnancy test required. 30-day dispense limit. '
                    'Mandatory patient registry enrollment.'
                ),
                'phase_schedule': {
                    'monthly': {'interval_days': 30, 'duration_days': None},
                },
                'initial_phase': 'monthly',
            },
            {
                'type': 'REGISTRY_ENROLLMENT',
                'description': (
                    'Patient, prescriber, and pharmacy must be enrolled in '
                    'Lenalidomide REMS program.'
                ),
                'phase_schedule': {
                    'monthly': {'interval_days': 30, 'duration_days': None},
                },
                'initial_phase': 'monthly',
            },
        ],
    },
}

# Generic opioid REMS applies to all ER/LA opioids — matched by class
_OPIOID_REMS = {
    'program_name': 'Opioid Analgesic REMS',
    'requirements': [
        {
            'type': 'PATIENT_COUNSELING',
            'description': (
                'Ensure patient receives Medication Guide and counseling '
                'on safe use, serious risks, and proper storage/disposal.'
            ),
            'phase_schedule': {
                'monthly': {'interval_days': 30, 'duration_days': None},
            },
            'initial_phase': 'monthly',
        },
        {
            'type': 'NALOXONE_COPRESCRIBE',
            'description': (
                'Consider prescribing naloxone. Document discussion of '
                'overdose risk and naloxone availability.'
            ),
            'phase_schedule': {
                'monthly': {'interval_days': 90, 'duration_days': None},
            },
            'initial_phase': 'monthly',
        },
    ],
}

# Drug names that trigger the generic opioid REMS
_OPIOID_REMS_DRUGS = frozenset({
    'oxycontin', 'oxycodone er', 'morphine er', 'morphine sulfate er',
    'fentanyl patch', 'fentanyl transdermal', 'methadone',
    'hydromorphone er', 'oxymorphone er', 'tapentadol er',
})

logger = logging.getLogger(__name__)


class DailyMedService(BaseAPIClient):
    """
    Service for the NLM DailyMed API v2.

    Provides access to FDA-approved drug labeling including medication
    guides and REMS program information.
    """

    def __init__(self, db):
        super().__init__(
            api_name="dailymed",
            base_url=DAILYMED_BASE_URL,
            db=db,
            ttl_days=DAILYMED_CACHE_TTL_DAYS,
        )

    def get_drug_label(self, drug_name: str) -> dict:
        """
        Search DailyMed for drug labeling by name.

        Returns
        -------
        dict with keys:
            setid (str or None) — SPL Set ID for the label
            title (str or None) — Label title (drug name + dosage form)
            has_medication_guide (bool)
            rems (bool) — whether a REMS program exists
            _stale (bool)
        """
        try:
            data = self._get("/spls.json", params={"drug_name": drug_name, "pagesize": "1"})
            results = (data.get("data") or [])
            if not results:
                return {"setid": None, "title": None, "has_medication_guide": False,
                        "rems": False, "_stale": data.get("_stale", False)}
            first = results[0]
            setid = first.get("setid", "")
            title = first.get("title", "")
            return {
                "setid": setid,
                "title": title,
                "has_medication_guide": bool(first.get("medication_guide")),
                "rems": bool(first.get("rems")),
                "_stale": data.get("_stale", False),
            }
        except APIUnavailableError:
            logger.warning("DailyMed unavailable for drug: %s", drug_name)
            return {"setid": None, "title": None, "has_medication_guide": False,
                    "rems": False, "_stale": True}

    def get_medication_guide(self, setid: str) -> dict:
        """
        Retrieve the medication guide for a specific SPL Set ID.

        Returns
        -------
        dict with keys:
            guide_url (str or None) — URL to the medication guide PDF
            guide_text (str or None) — Plain text excerpt if available
            _stale (bool)
        """
        if not setid:
            return {"guide_url": None, "guide_text": None, "_stale": False}
        try:
            data = self._get(f"/spls/{setid}/media.json")
            media_list = data.get("data") or []
            guide_url = None
            for media in media_list:
                mime = (media.get("mime_type") or "").lower()
                name = (media.get("name") or "").lower()
                if "pdf" in mime or "medication_guide" in name or "medguide" in name:
                    guide_url = media.get("url")
                    break
            return {
                "guide_url": guide_url,
                "guide_text": None,
                "_stale": data.get("_stale", False),
            }
        except APIUnavailableError:
            logger.warning("DailyMed medication guide unavailable for setid: %s", setid)
            return {"guide_url": None, "guide_text": None, "_stale": True}

    def check_rems_program(self, drug_name: str) -> dict:
        """
        Check whether a REMS (Risk Evaluation and Mitigation Strategy) program
        exists for the given drug. REMS drugs require additional safety monitoring.

        Returns
        -------
        dict with keys:
            has_rems (bool)
            rems_detail (str or None) — brief description if available
            _stale (bool)
        """
        try:
            data = self._get("/spls.json", params={"drug_name": drug_name, "pagesize": "1"})
            results = (data.get("data") or [])
            if not results:
                return {"has_rems": False, "rems_detail": None,
                        "_stale": data.get("_stale", False)}
            first = results[0]
            rems = bool(first.get("rems"))
            detail = first.get("rems", "") if rems else None
            if detail is True:
                detail = f"REMS program active for {drug_name}"
            return {
                "has_rems": rems,
                "rems_detail": detail if isinstance(detail, str) else None,
                "_stale": data.get("_stale", False),
            }
        except APIUnavailableError:
            logger.warning("DailyMed REMS check unavailable for drug: %s", drug_name)
            return {"has_rems": False, "rems_detail": None, "_stale": True}

    # ================================================================
    # Phase 23 — SPL monitoring requirement extraction (B1)
    # ================================================================

    @staticmethod
    def _strip_html(html_text: str) -> str:
        """Remove HTML tags and decode entities to plain text."""
        text = _RE_STRIP_HTML.sub(' ', html_text)
        text = _html_unescape(text)
        return re.sub(r'\s+', ' ', text).strip()

    def _fetch_spl_sections(self, setid: str,
                            drug_name: str = None,
                            rxcui: str = None) -> dict:
        """
        Fetch monitoring-relevant label sections for a drug.

        Priority:
        1. OpenFDA Labels API — returns structured JSON sections
           (warnings_and_cautions, drug_interactions, adverse_reactions)
        2. DailyMed ``/sections.json`` fallback

        Returns
        -------
        dict  {section_code: plain_text, ...}
        """
        sections = {}

        # Map OpenFDA field names → SPL LOINC section codes
        _OPENFDA_TO_LOINC = {
            'warnings_and_cautions': '43685-7',
            'drug_interactions': '34073-7',
            'adverse_reactions': '34084-4',
        }

        # --- Attempt 1: OpenFDA Labels API (reliable JSON) ----------------
        try:
            from app.services.api.openfda_labels import OpenFDALabelsService
            openfda_svc = OpenFDALabelsService(self.cache.db)
            if rxcui:
                label = openfda_svc.get_label_by_rxcui(rxcui)
            elif drug_name:
                label = openfda_svc.get_label_by_name(drug_name)
            else:
                label = {}

            label_sections = label.get('label_sections') or {}
            for fda_name, code in _OPENFDA_TO_LOINC.items():
                text = label_sections.get(fda_name, '')
                if text:
                    sections[code] = self._strip_html(text)

            if sections:
                return sections
        except Exception as e:
            logger.debug("OpenFDA sections unavailable: %s", e)

        # --- Attempt 2: DailyMed /sections.json ---------------------------
        try:
            data = self._get("/sections.json", params={"setid": setid})
            for sec in data.get("data") or []:
                code = sec.get("section_code") or sec.get("code") or ""
                text = sec.get("section_text") or sec.get("text") or ""
                if code in _MONITORING_SECTION_CODES and text:
                    sections[code] = self._strip_html(text)
        except (APIUnavailableError, KeyError, TypeError):
            logger.warning("DailyMed sections unavailable for setid: %s", setid)

        return sections

    @staticmethod
    def _extract_interval(text: str) -> int:
        """
        Parse a monitoring-frequency description into interval days.

        Tries exact-match keywords first, then numeric regex patterns.
        Defaults to 180 (semi-annual) if nothing matches.
        """
        lower = text.lower().strip()

        # Try keyword map first
        for phrase, days in _INTERVAL_MAP.items():
            if phrase in lower:
                return days

        # Try "every N {unit}" pattern
        m = _RE_INTERVAL_EXACT.search(lower)
        if m:
            n = int(m.group(1))
            unit = m.group(2).lower().rstrip('s')
            multiplier = {'day': 1, 'week': 7, 'month': 30, 'year': 365}
            return n * multiplier.get(unit, 30)

        # Try "N-M weeks/months after" range pattern → use start
        m = _RE_INTERVAL_RANGE.search(lower)
        if m:
            n = int(m.group(1))
            unit = m.group(3).lower().rstrip('s')
            multiplier = {'week': 7, 'month': 30}
            return n * multiplier.get(unit, 30)

        return 180  # safe default: semi-annual

    def _regex_extract_monitoring(self, text: str) -> list:
        """
        Pattern-match monitoring language in SPL text.

        Processes per-sentence to prevent non-greedy capture groups
        from spanning across sentence boundaries.

        Returns
        -------
        list of dicts  {lab_text, interval_text, context_sentence}
        """
        if not text:
            return []

        matches = []
        seen_labs = set()

        # Split into sentences for bounded regex matching
        sentences = re.split(r'(?<=[.;!?])\s+', text)

        def _add_match(lab: str, interval: str, context: str):
            lab_clean = lab.strip().strip('.,;:').strip()
            if len(lab_clean) < 2 or len(lab_clean) > 80:
                return
            key = lab_clean.lower()
            if key in seen_labs:
                return
            seen_labs.add(key)
            matches.append({
                'lab_text': lab_clean,
                'interval_text': interval.strip(),
                'context_sentence': context.strip()[:300],
            })

        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue

            # Pattern 1: "Monitor/Check [lab] [timing]"
            for m in _RE_MONITOR_ACTION.finditer(sent):
                _add_match(m.group(1), m.group(2), sent)

            # Pattern 2: "[Lab] should be monitored [timing]"
            for m in _RE_PASSIVE_MONITOR.finditer(sent):
                _add_match(m.group(1), m.group(2), sent)

            # Pattern 3: "Recommend [timing] monitoring of [lab]"
            for m in _RE_RECOMMEND_MONITOR.finditer(sent):
                _add_match(m.group(2), m.group(1), sent)

        return matches

    def _normalize_lab_to_loinc(self, lab_text: str) -> tuple:
        """
        Resolve free-text lab name to (loinc_code, cpt_code, lab_name).

        Priority: 1) ``_COMMON_LAB_MAP`` exact match, 2) LoincCache
        keyword search on ``component`` / ``display_name``.

        Returns ``(None, None, None)`` if unresolvable.
        """
        key = lab_text.strip().lower()

        # 1) Static fallback map (fast, covers 90%+ of SPL mentions)
        if key in _COMMON_LAB_MAP:
            return _COMMON_LAB_MAP[key]

        # Partial match — check map keys that start with / contain the text
        for map_key, val in _COMMON_LAB_MAP.items():
            if key in map_key or map_key in key:
                return val

        # 2) LoincCache keyword search
        try:
            from flask import current_app
            with current_app.app_context():
                pass  # Already in context if this runs during request
        except (RuntimeError, ImportError):
            pass  # Running outside request — LoincCache query may still work

        try:
            words = [w for w in key.split() if len(w) > 2]
            if not words:
                return (None, None, None)
            # Search component and display_name for any matching word
            for word in words:
                pattern = f'%{word}%'
                hit = LoincCache.query.filter(
                    (LoincCache.component.ilike(pattern))
                    | (LoincCache.display_name.ilike(pattern))
                ).first()
                if hit:
                    return (hit.loinc_code, hit.loinc_code, hit.display_name or lab_text)
        except Exception:
            logger.debug("LoincCache lookup failed for: %s", lab_text)

        return (None, None, None)

    def _is_high_monitoring_class(self, rxcui: str) -> bool:
        """
        Check whether an RxCUI belongs to a drug class known to require
        multi-lab monitoring (via the structured RxClassCache table).
        """
        if not rxcui:
            return False
        try:
            cached_classes = RxClassCache.query.filter_by(rxcui=rxcui).all()
            for c in cached_classes:
                cid = (c.class_id or '').upper()
                if cid in _HIGH_MONITORING_CLASSES:
                    return True
                # Also match prefix (e.g., "N05AH03" starts with "N05AH")
                for hmc in _HIGH_MONITORING_CLASSES:
                    if cid.startswith(hmc) or hmc.startswith(cid):
                        return True
        except Exception:
            logger.debug("RxClassCache lookup error for rxcui=%s", rxcui)
        return False

    def _llm_extract_monitoring(self, text: str, drug_name: str) -> list:
        """
        LLM fallback: send SPL section text to Claude for structured
        monitoring extraction.  Only fires when regex yields ≤1 result
        for a known high-monitoring-class drug.

        Returns list of dicts with keys:
            lab_loinc_code, lab_cpt_code, lab_name, interval_days,
            priority, clinical_context
        """
        api_key = os.getenv('ANTHROPIC_API_KEY', '')
        if not api_key:
            logger.debug("No ANTHROPIC_API_KEY — skipping LLM extraction")
            return []

        # Truncate text to avoid excessive token usage (keep first 4000 chars)
        excerpt = text[:4000] if len(text) > 4000 else text

        system_prompt = (
            "You are a clinical pharmacology expert.  Extract ALL laboratory "
            "monitoring requirements from the following drug labeling text.  "
            "Return ONLY a JSON array (no markdown, no commentary).  Each "
            "element must have exactly these keys: lab_loinc_code (string, "
            "LOINC code or empty string if unknown), lab_cpt_code (string, "
            "CPT code or empty string), lab_name (string, human-readable "
            "lab test name), interval_days (integer, monitoring interval in "
            "days; use 0 for baseline/pre-treatment), priority (string, one "
            "of: critical, high, standard, low), clinical_context (string, "
            "brief clinical rationale ≤100 chars)."
        )
        user_msg = (
            f"Drug: {drug_name}\n\n"
            f"Labeling text:\n{excerpt}"
        )

        payload = json.dumps({
            'model': 'claude-3-5-haiku-latest',
            'max_tokens': 2048,
            'system': system_prompt,
            'messages': [{'role': 'user', 'content': user_msg}],
        }).encode()

        req = _urllib_req.Request(
            'https://api.anthropic.com/v1/messages',
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
            },
        )

        try:
            with _urllib_req.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                raw_text = data['content'][0]['text'].strip()

            # Parse JSON from response (strip markdown fences if present)
            raw_text = re.sub(r'^```(?:json)?\s*', '', raw_text)
            raw_text = re.sub(r'\s*```$', '', raw_text)
            results = json.loads(raw_text)

            if not isinstance(results, list):
                return []

            # Validate and normalise each entry
            valid = []
            for item in results:
                if not isinstance(item, dict):
                    continue
                lab_name = item.get('lab_name', '')
                if not lab_name:
                    continue
                # Fill in LOINC/CPT from our map if LLM left blank
                loinc = item.get('lab_loinc_code', '')
                cpt = item.get('lab_cpt_code', '')
                if not loinc or not cpt:
                    mapped = self._normalize_lab_to_loinc(lab_name)
                    loinc = loinc or (mapped[0] or '')
                    cpt = cpt or (mapped[1] or '')
                valid.append({
                    'lab_loinc_code': loinc,
                    'lab_cpt_code': cpt,
                    'lab_name': lab_name,
                    'interval_days': int(item.get('interval_days', 180)),
                    'priority': item.get('priority', 'standard'),
                    'clinical_context': str(
                        item.get('clinical_context', '')
                    )[:200],
                })
            return valid

        except (_urllib_err.HTTPError, _urllib_err.URLError) as e:
            logger.warning("LLM monitoring extraction failed: %s", e)
            return []
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning("LLM response parse error: %s", e)
            return []

    def extract_monitoring_requirements(
        self, drug_name: str, rxcui: str = None
    ) -> list:
        """
        Public method: extract all monitoring requirements for a drug
        from its FDA-approved labeling (SPL).

        Implements a 3-step pipeline:
        1. Fetch SPL sections via DailyMed API
        2. Regex extraction (confidence 0.8)
        3. LLM fallback if regex yields ≤1 result and drug is in a
           known high-monitoring class (confidence 0.9)

        Parameters
        ----------
        drug_name : str
            Drug name for DailyMed search.
        rxcui : str, optional
            RxNorm CUI — used for high-monitoring-class check.

        Returns
        -------
        list of dicts, each with:
            lab_loinc_code, lab_cpt_code, lab_name, interval_days,
            priority, clinical_context, extraction_confidence
        """
        # Step 0: Get SPL setid
        label = self.get_drug_label(drug_name)
        setid = label.get('setid')
        if not setid:
            logger.info("No DailyMed SPL found for: %s", drug_name)
            return []

        # Step 1: Fetch monitoring-relevant sections
        sections = self._fetch_spl_sections(setid, drug_name=drug_name,
                                            rxcui=rxcui)
        if not sections:
            logger.info("No SPL sections found for setid: %s", setid)
            return []

        # Combine all section text for extraction
        combined_text = ' '.join(sections.values())

        # Step 2: Regex extraction
        raw_matches = self._regex_extract_monitoring(combined_text)
        results = []
        seen_loinc = set()

        for match in raw_matches:
            loinc, cpt, name = self._normalize_lab_to_loinc(match['lab_text'])
            if not loinc:
                continue
            if loinc in seen_loinc:
                continue
            seen_loinc.add(loinc)

            interval = self._extract_interval(match['interval_text'])
            results.append({
                'lab_loinc_code': loinc,
                'lab_cpt_code': cpt or loinc,
                'lab_name': name or match['lab_text'],
                'interval_days': interval,
                'priority': 'high' if interval <= 30 else 'standard',
                'clinical_context': match.get('context_sentence', '')[:200],
                'extraction_confidence': 0.8,
            })

        # Step 3: LLM fallback — only for high-monitoring-class drugs
        #         where regex found ≤1 requirement
        if len(results) <= 1 and self._is_high_monitoring_class(rxcui):
            logger.info(
                "Regex found %d results for %s (high-monitoring class) "
                "— invoking LLM fallback", len(results), drug_name
            )
            llm_results = self._llm_extract_monitoring(combined_text, drug_name)
            for item in llm_results:
                if item['lab_loinc_code'] in seen_loinc:
                    continue
                seen_loinc.add(item['lab_loinc_code'])
                item['extraction_confidence'] = 0.9
                results.append(item)

        # Build evidence URL
        evidence_url = (
            f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={setid}"
        )
        for r in results:
            r['evidence_source_url'] = evidence_url

        logger.info(
            "Extracted %d monitoring requirements for %s (setid=%s)",
            len(results), drug_name, setid,
        )
        return results

    # ================================================================
    # Phase 23 — REMS compliance engine (B5)
    # ================================================================

    @staticmethod
    def _get_rems_program(drug_name: str) -> dict | None:
        """
        Return the hardcoded REMS program definition for a drug, or
        None if no REMS program is defined.
        """
        key = drug_name.strip().lower()

        # Direct match
        if key in _REMS_PROGRAMS:
            return _REMS_PROGRAMS[key]

        # Substring match — "clozapine 100mg" → "clozapine"
        for stem, program in _REMS_PROGRAMS.items():
            if stem in key or key in stem:
                return program

        # Opioid REMS — class-level match
        for opioid in _OPIOID_REMS_DRUGS:
            if opioid in key or key in opioid:
                return _OPIOID_REMS

        return None

    def create_rems_entries(
        self,
        patient_mrn_hash: str,
        user_id: int,
        drug_name: str,
        rxcui: str = '',
    ) -> list:
        """
        Create REMSTrackerEntry records for a patient on a REMS drug.

        Checks DailyMed for REMS status, then uses hardcoded program
        definitions to create structured tracker entries.  Idempotent:
        skips if an active entry already exists for this patient+drug+type.

        Parameters
        ----------
        patient_mrn_hash : str
            SHA-256 hashed MRN (HIPAA-safe).
        user_id : int
            Provider user ID (FK → User).
        drug_name : str
            Drug name as it appears on the medication list.
        rxcui : str, optional
            RxNorm CUI for the drug.

        Returns
        -------
        list of REMSTrackerEntry
            Newly created entries (empty if already exists or no REMS).
        """
        from models.monitoring import REMSTrackerEntry
        from models import db as _db
        from datetime import date

        # Step 1: Confirm REMS status via DailyMed API
        rems_info = self.check_rems_program(drug_name)

        # Step 2: Get hardcoded program definition
        program = self._get_rems_program(drug_name)

        # If DailyMed says no REMS and we have no hardcoded definition, skip
        if not rems_info.get('has_rems') and program is None:
            return []

        # If DailyMed says REMS but we have no hardcoded definition,
        # create a generic LAB_MONITORING entry
        if program is None:
            program = {
                'program_name': rems_info.get('rems_detail') or f'REMS for {drug_name}',
                'requirements': [
                    {
                        'type': 'LAB_MONITORING',
                        'description': (
                            f'REMS program active for {drug_name}. '
                            f'Consult drug documentation for specific requirements.'
                        ),
                        'phase_schedule': {
                            'monthly': {'interval_days': 30, 'duration_days': None},
                        },
                        'initial_phase': 'monthly',
                    },
                ],
            }

        created = []
        today = date.today()

        for req in program['requirements']:
            # Idempotency: skip if active entry already exists
            existing = REMSTrackerEntry.query.filter_by(
                patient_mrn_hash=patient_mrn_hash,
                drug_name=drug_name,
                requirement_type=req['type'],
                status='active',
            ).first()
            if existing:
                continue

            initial_phase = req['initial_phase']
            phase_info = req['phase_schedule'].get(initial_phase, {})
            interval = phase_info.get('interval_days', 30)

            entry = REMSTrackerEntry(
                patient_mrn_hash=patient_mrn_hash,
                user_id=user_id,
                drug_name=drug_name,
                rxcui=rxcui,
                rems_program_name=program['program_name'],
                requirement_type=req['type'],
                requirement_description=req['description'],
                interval_days=interval,
                current_phase=initial_phase,
                phase_start_date=today,
                last_completed_date=None,
                next_due_date=today,  # immediately due on creation
                is_compliant=True,
                escalation_level=0,
                status='active',
            )
            _db.session.add(entry)
            created.append(entry)

        if created:
            try:
                _db.session.commit()
                logger.info(
                    "Created %d REMS entries for %s (%s)",
                    len(created), drug_name, program['program_name'],
                )
            except Exception as e:
                _db.session.rollback()
                logger.error("REMS entry creation failed: %s", e)
                return []

        return created

    @staticmethod
    def update_rems_escalation(entry) -> int:
        """
        Update the escalation level of a REMSTrackerEntry based on
        current date vs next_due_date.

        Returns the new escalation_level (0–3).

        Escalation scheme:
          0 = on track (due date > 3 days from now)
          1 = due within 3 days
          2 = overdue (past due date)
          3 = critical hold (>7 days overdue — dispense should be blocked)
        """
        from datetime import date
        today = date.today()
        due = entry.next_due_date

        if not due or entry.status != 'active':
            return entry.escalation_level

        days_until = (due - today).days

        if days_until > 3:
            new_level = 0
        elif days_until >= 0:
            new_level = 1
        elif days_until >= -7:
            new_level = 2
        else:
            new_level = 3

        entry.escalation_level = new_level
        entry.is_compliant = (new_level <= 1)
        return new_level

    @staticmethod
    def advance_rems_phases() -> int:
        """
        Nightly job: auto-advance REMS phase schedules for drugs with
        multi-phase monitoring (e.g., clozapine weekly→biweekly→monthly).

        Checks all active REMSTrackerEntry records.  For entries where
        ``phase_start_date + phase duration`` has passed, advances to
        the next phase and updates ``interval_days`` and
        ``next_due_date`` accordingly.

        Returns the number of entries whose phase was advanced.
        """
        from models.monitoring import REMSTrackerEntry
        from models import db as _db
        from datetime import date, timedelta

        today = date.today()
        advanced = 0

        entries = REMSTrackerEntry.query.filter_by(status='active').all()
        for entry in entries:
            program = _REMS_PROGRAMS.get(entry.drug_name.lower())
            if not program:
                # Try substring match
                for stem, prog in _REMS_PROGRAMS.items():
                    if stem in entry.drug_name.lower():
                        program = prog
                        break
            if not program:
                continue

            # Find the matching requirement
            req = None
            for r in program['requirements']:
                if r['type'] == entry.requirement_type:
                    req = r
                    break
            if not req:
                continue

            schedule = req['phase_schedule']
            current = entry.current_phase
            if current not in schedule:
                continue

            phase_info = schedule[current]
            duration = phase_info.get('duration_days')
            if duration is None:
                continue  # terminal phase — no advancement

            if not entry.phase_start_date:
                continue

            # Check if current phase duration has elapsed
            phase_end = entry.phase_start_date + timedelta(days=duration)
            if today < phase_end:
                continue  # not yet time to advance

            # Find the next phase
            phases = list(schedule.keys())
            try:
                idx = phases.index(current)
            except ValueError:
                continue
            if idx + 1 >= len(phases):
                continue  # already at last phase

            next_phase = phases[idx + 1]
            next_info = schedule[next_phase]

            entry.current_phase = next_phase
            entry.phase_start_date = today
            entry.interval_days = next_info['interval_days']

            # Recalculate next_due_date from last completion
            if entry.last_completed_date:
                entry.next_due_date = (
                    entry.last_completed_date
                    + timedelta(days=next_info['interval_days'])
                )
            else:
                entry.next_due_date = today

            advanced += 1
            logger.info(
                "REMS phase advanced: %s %s %s → %s (interval now %d days)",
                entry.drug_name, entry.requirement_type,
                current, next_phase, next_info['interval_days'],
            )

        if advanced:
            try:
                _db.session.commit()
            except Exception as e:
                _db.session.rollback()
                logger.error("REMS phase advancement commit failed: %s", e)
                return 0

        return advanced

    @staticmethod
    def bulk_update_rems_escalation() -> dict:
        """
        Nightly job: update escalation levels for all active REMS entries.

        Returns dict with counts: {total, level_0, level_1, level_2, level_3}.
        """
        from models.monitoring import REMSTrackerEntry
        from models import db as _db
        from datetime import date

        today = date.today()
        entries = REMSTrackerEntry.query.filter_by(status='active').all()

        counts = {'total': len(entries), 'level_0': 0, 'level_1': 0,
                  'level_2': 0, 'level_3': 0}

        for entry in entries:
            new_level = DailyMedService.update_rems_escalation(entry)
            counts[f'level_{new_level}'] += 1

        try:
            _db.session.commit()
        except Exception as e:
            _db.session.rollback()
            logger.error("REMS escalation bulk update failed: %s", e)

        return counts
