"""
CareCompanion — Base Adapter Interface & ClinicalData Schema

Defines the abstract interface that every data adapter must implement,
and the standardized ClinicalData dictionary schema that all downstream
consumers (billing engine, care gap engine, templates) rely on.

The schema mirrors the existing PatientRecord / PatientMedication /
PatientDiagnosis / PatientLabResult / PatientVitals / PatientAllergy /
PatientImmunization / PatientSocialHistory model columns exactly, so
store_parsed_summary() and the billing engine receive identical data
regardless of source.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict


# ======================================================================
# Standardized sub-record schemas
# ======================================================================

class MedicationRecord(TypedDict, total=False):
    """One medication entry — matches PatientMedication columns."""
    drug_name: str
    rxnorm_cui: str
    dosage: str
    frequency: str
    status: str            # 'active' | 'inactive'
    start_date: Optional[datetime]


class DiagnosisRecord(TypedDict, total=False):
    """One diagnosis entry — matches PatientDiagnosis columns."""
    diagnosis_name: str
    icd10_code: str
    status: str            # 'active' | 'resolved'
    diagnosis_category: str  # 'acute' | 'chronic'
    onset_date: Optional[datetime]


class AllergyRecord(TypedDict, total=False):
    """One allergy entry — matches PatientAllergy columns."""
    allergen: str
    reaction: str
    severity: str


class ImmunizationRecord(TypedDict, total=False):
    """One immunization entry — matches PatientImmunization columns."""
    vaccine_name: str
    date_given: Optional[datetime]


class LabResultRecord(TypedDict, total=False):
    """One lab result — matches PatientLabResult columns."""
    test_name: str
    loinc_code: str
    result_value: str
    result_units: str
    result_date: Optional[datetime]
    result_flag: str       # 'normal' | 'abnormal' | 'critical'
    source: str            # 'xml_import' | 'fhir' | 'manual'


class VitalRecord(TypedDict, total=False):
    """One vital sign measurement — matches PatientVitals columns."""
    vital_name: str        # e.g. 'BP Systolic', 'Weight', 'BMI'
    vital_value: str
    vital_unit: str
    measured_at: Optional[datetime]


class SocialHistoryRecord(TypedDict, total=False):
    """Social history — matches PatientSocialHistory columns."""
    tobacco_status: str    # 'current' | 'former' | 'never' | 'unknown'
    tobacco_pack_years: Optional[float]
    alcohol_status: str    # 'current' | 'former' | 'never' | 'unknown'
    alcohol_frequency: str
    substance_use_status: str
    sexual_activity: str


class ClinicalData(TypedDict, total=False):
    """
    The canonical data format for one patient.

    Every adapter converts its source format (CDA XML, FHIR JSON, CSV)
    into this schema. Every consumer (billing engine, care gap engine,
    store_parsed_summary, templates) reads from this schema.

    Keys match the existing parse_clinical_summary() return dict so that
    store_parsed_summary() works without changes.
    """
    # Demographics
    patient_name: str
    patient_mrn: str
    patient_dob: str          # 'YYYY-MM-DD' normalized
    patient_sex: str          # 'M' | 'F'
    insurer_type: str         # 'medicare' | 'medicaid' | 'commercial' | 'unknown'

    # Clinical sections — lists of standardized sub-records
    medications: List[MedicationRecord]
    diagnoses: List[DiagnosisRecord]
    allergies: List[AllergyRecord]
    immunizations: List[ImmunizationRecord]
    lab_results: List[LabResultRecord]
    vitals: List[VitalRecord]
    social_history: List[SocialHistoryRecord]

    # Metadata
    source: str               # 'cda_xml' | 'fhir' | 'csv' | 'manual'
    fetched_at: str           # ISO 8601 timestamp

    # ----- Legacy CDA-specific keys (for backward compat) -----
    # These are populated by CdaXmlAdapter to keep store_parsed_summary()
    # working unchanged. FhirAdapter populates the typed lists above
    # and a shim converts them to legacy format if needed.
    encounter_reason: list
    instructions: list
    goals: list
    health_concerns: list
    insurance: list


# ======================================================================
# Abstract Base Adapter
# ======================================================================

class BaseAdapter(ABC):
    """
    Abstract interface for all data adapters.

    Subclasses implement the fetch methods. Each returns standardized
    data that can be passed directly to store_parsed_summary() or to
    the billing/care-gap engines.
    """

    @abstractmethod
    def fetch_patient(self, mrn: str) -> ClinicalData:
        """
        Fetch full clinical record for one patient.

        Parameters
        ----------
        mrn : str
            Medical Record Number (or FHIR Patient resource ID).

        Returns
        -------
        ClinicalData
            Standardized clinical data dict.
        """
        ...

    @abstractmethod
    def fetch_schedule(self, date_str: str, provider_id: str = None) -> list:
        """
        Fetch appointments for a given date.

        Parameters
        ----------
        date_str : str
            Date in YYYY-MM-DD format.
        provider_id : str, optional
            Filter to a specific provider.

        Returns
        -------
        list of dict
            Each dict has: patient_name, mrn, appointment_time,
            visit_type, duration_minutes.
        """
        ...

    def fetch_patients_bulk(self, mrns: List[str]) -> List[ClinicalData]:
        """
        Fetch clinical data for multiple patients.

        Default implementation calls fetch_patient() in a loop.
        FHIR adapter overrides with batch queries.
        """
        return [self.fetch_patient(mrn) for mrn in mrns]

    @staticmethod
    def empty_clinical_data() -> ClinicalData:
        """Return an empty ClinicalData dict with all keys initialized."""
        return ClinicalData(
            patient_name='',
            patient_mrn='',
            patient_dob='',
            patient_sex='',
            insurer_type='unknown',
            medications=[],
            diagnoses=[],
            allergies=[],
            immunizations=[],
            lab_results=[],
            vitals=[],
            social_history=[],
            source='',
            fetched_at=datetime.now(timezone.utc).isoformat(),
            encounter_reason=[],
            instructions=[],
            goals=[],
            health_concerns=[],
            insurance=[],
        )

    @staticmethod
    def to_legacy_parsed(data: 'ClinicalData') -> dict:
        """
        Convert standardized ClinicalData to the legacy dict format
        expected by store_parsed_summary().

        The legacy format uses CDA column-header keys ('Medication',
        'Problem', 'Substance', etc.) whereas ClinicalData uses
        normalized field names ('drug_name', 'diagnosis_name', etc.).

        This shim lets the FHIR adapter feed data into the existing
        store_parsed_summary() without modifying that function.
        """
        result = {
            'patient_name': data.get('patient_name', ''),
            'patient_mrn': data.get('patient_mrn', ''),
            'patient_dob': data.get('patient_dob', ''),
            'patient_sex': data.get('patient_sex', ''),
            'insurer_type': data.get('insurer_type', 'unknown'),
            'encounter_reason': data.get('encounter_reason', []),
            'instructions': data.get('instructions', []),
            'goals': data.get('goals', []),
            'health_concerns': data.get('health_concerns', []),
            'insurance': data.get('insurance', []),
        }

        # Medications → legacy CDA row format
        result['medications'] = [
            {
                'Medication': m.get('drug_name', ''),
                'Dosage': m.get('dosage', ''),
                'Instructions': m.get('frequency', ''),
                'Status': m.get('status', 'active'),
                'Start Date': (m['start_date'].strftime('%m/%d/%Y')
                               if m.get('start_date') else ''),
            }
            for m in data.get('medications', [])
        ]

        # Diagnoses → legacy CDA row format
        result['diagnoses'] = [
            {
                'Problem': (
                    f"{d.get('diagnosis_name', '')} ({d['icd10_code']})"
                    if d.get('icd10_code')
                    else d.get('diagnosis_name', '')
                ),
                'Problem Status': d.get('status', 'active'),
                'Date Started': (d['onset_date'].strftime('%m/%d/%Y')
                                 if d.get('onset_date') else ''),
            }
            for d in data.get('diagnoses', [])
        ]

        # Allergies → legacy CDA row format
        result['allergies'] = [
            {
                'Substance': a.get('allergen', ''),
                'Reaction': a.get('reaction', ''),
                'Severity': a.get('severity', ''),
            }
            for a in data.get('allergies', [])
        ]

        # Immunizations → legacy CDA row format
        result['immunizations'] = [
            {
                'Vaccine': i.get('vaccine_name', ''),
                'Date': (i['date_given'].strftime('%m/%d/%Y')
                         if i.get('date_given') else ''),
            }
            for i in data.get('immunizations', [])
        ]

        # Lab results → legacy CDA row format
        result['lab_results'] = [
            {
                'Test Name': (
                    f"{lr.get('test_name', '')} [LOINC:{lr['loinc_code']}]"
                    if lr.get('loinc_code')
                    else lr.get('test_name', '')
                ),
                'Result': lr.get('result_value', ''),
                'Units': lr.get('result_units', ''),
                'Flag': lr.get('result_flag', 'normal'),
                'Date': (lr['result_date'].strftime('%m/%d/%Y')
                         if lr.get('result_date') else ''),
            }
            for lr in data.get('lab_results', [])
        ]

        # Vitals → legacy CDA row format (single row with all vitals)
        vitals_rows = data.get('vitals', [])
        if vitals_rows:
            # Group by measured_at timestamp into encounter rows
            encounters = {}
            for v in vitals_rows:
                key = str(v.get('measured_at', ''))
                if key not in encounters:
                    encounters[key] = {'Encounter': key}
                name = v.get('vital_name', '')
                value = v.get('vital_value', '')
                unit = v.get('vital_unit', '')
                # Map back to CDA column headers
                col_map = {
                    'Height': f'Height ({unit})',
                    'Weight': f'Weight ({unit})',
                    'BMI': f'BMI ({unit})',
                    'BP Systolic': f'BP Sys ({unit})',
                    'BP Diastolic': f'BP Dias ({unit})',
                    'Heart Rate': f'Heart Rate ({unit})',
                    'O2 Sat': f'O2 % BldC Oximetry',
                    'Temperature': 'Body Temperature',
                    'Respiratory Rate': f'Respiratory Rate ({unit})',
                }
                col_header = col_map.get(name, name)
                encounters[key][col_header] = value
            result['vitals'] = list(encounters.values())
        else:
            result['vitals'] = []

        # Social history → legacy text format
        result['social_history'] = [
            {'text': f"Tobacco: {sh.get('tobacco_status', 'unknown')}, "
                     f"Alcohol: {sh.get('alcohol_status', 'unknown')}"}
            for sh in data.get('social_history', [])
        ]

        return result
