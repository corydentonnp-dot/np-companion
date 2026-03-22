"""
CareCompanion — API Services Package
File: app/services/api/__init__.py

One module per external API. All modules inherit from BaseAPIClient
(base_client.py) which handles retry logic, rate limiting, and offline
fallback behavior. All caching goes through CacheManager (cache_manager.py).

Available services:
- rxnorm         — Drug name normalization (RxNorm / RxCUI)
- rxclass        — Drug class mapping (ATC, EPC, VA class)
- openfda_labels — FDA prescribing information (indications, warnings, interactions)
- openfda_recalls — Active FDA drug recalls
- openfda_adverse_events — FAERS adverse event reports
- icd10          — ICD-10-CM code search and lookup
- loinc          — Lab test identification and reference ranges
- umls           — Medical ontology crosswalk (ICD-10 ↔ SNOMED ↔ RxNorm)
- healthfinder   — USPSTF preventive care recommendations (AHRQ HealthFinder)
- cdc_immunizations — CDC adult immunization schedules
- cms_pfs        — CMS Physician Fee Schedule (billing code rates)
- pubmed         — NCBI PubMed literature search
- medlineplus    — NLM MedlinePlus patient education content
- open_meteo     — Weather data for morning briefing

CareCompanion features that rely on this package:
- Medication Reference (F10), Drug Safety Panel, Interaction Checker
- Lab Value Tracker (F11), Lab Panel Grouping (F11d)
- Care Gap Tracker (F15), Immunization Gap Detection
- Coding Suggester (F17), Note Reformatter (F31)
- Morning Briefing (F22), Pre-Visit Note Prep (F9)
- Billing Opportunity Engine (Phase 10 Addendum)
- PA Generator (F26)
"""
