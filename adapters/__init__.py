"""
CareCompanion — Data Adapters Package

Provides a unified interface for ingesting patient clinical data from
multiple sources (HL7 CDA XML, FHIR R4 API, CSV import, manual entry).

The adapter layer decouples data collection from business logic so the
billing engine, care gap engine, and all downstream consumers never need
to know *where* data came from — only that it conforms to the
standardized ClinicalData schema.

Architecture:
  BaseAdapter (abstract)
    ├── CdaXmlAdapter     — parses HL7 CDA Clinical Summary XML files
    ├── FhirAdapter        — fetches from FHIR R4 API via SMART on FHIR
    ├── CsvAdapter         — bulk import from spreadsheets (future)
    └── ManualAdapter      — web UI manual entry (future)

Usage:
    from adapters import get_adapter
    adapter = get_adapter(practice)       # auto-selects by practice.ehr_type
    data = adapter.fetch_patient('12345') # returns ClinicalData dict
"""

from adapters.base import BaseAdapter, ClinicalData
from adapters.cda_xml import CdaXmlAdapter
from adapters.fhir_r4 import FhirAdapter

__all__ = [
    'BaseAdapter',
    'ClinicalData',
    'CdaXmlAdapter',
    'FhirAdapter',
    'get_adapter',
]


def get_adapter(practice=None, adapter_type=None, **kwargs):
    """
    Factory: return the correct adapter for a practice or explicit type.

    Parameters
    ----------
    practice : Practice model instance, optional
        If provided, adapter is chosen based on practice.ehr_type and
        FHIR credentials are loaded from the practice record.
    adapter_type : str, optional
        Force a specific adapter: 'cda_xml', 'fhir', 'csv', 'manual'.
    **kwargs
        Passed through to the adapter constructor.

    Returns
    -------
    BaseAdapter subclass instance
    """
    if adapter_type:
        atype = adapter_type.lower()
    elif practice:
        # Map EHR type to adapter
        ehr = (practice.ehr_type or '').lower()
        if ehr in ('amazing_charts', 'ac'):
            # AC can use either CDA XML (desktop) or FHIR (cloud)
            if getattr(practice, 'fhir_endpoint_url', None):
                atype = 'fhir'
            else:
                atype = 'cda_xml'
        else:
            # All other EHRs use FHIR
            atype = 'fhir'
    else:
        atype = 'cda_xml'  # default for local desktop use

    if atype == 'cda_xml':
        return CdaXmlAdapter(**kwargs)
    elif atype == 'fhir':
        fhir_kwargs = dict(kwargs)
        if practice:
            fhir_kwargs.setdefault('fhir_base_url', practice.fhir_endpoint_url)
            fhir_kwargs.setdefault('client_id', practice.fhir_client_id)
            fhir_kwargs.setdefault('client_secret', practice.fhir_client_secret)
            ehr_type = (practice.ehr_type or 'generic').lower()
            fhir_kwargs.setdefault('ehr_type', ehr_type)
        return FhirAdapter(**fhir_kwargs)
    else:
        raise ValueError(f"Unknown adapter type: {atype!r}")
