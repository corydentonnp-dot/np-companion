"""
CareCompanion — Structured API Cache Models
File: models/api_cache.py

Typed cache tables for external API responses.  Each model stores
structured lookup data from a specific public health / medical API,
reducing redundant network calls and enabling offline access.

Existing cache models live elsewhere:
  - RxNormCache, Icd10Cache  → models/patient.py
  - BillingRuleCache          → models/billing.py

This file adds the remaining 10 structured caches specified in the
API Integration Plan.
"""

from datetime import datetime, timezone
from models import db


# ── RxClass (NIH RxNav) ────────────────────────────────────────────
class RxClassCache(db.Model):
    """Drug → therapeutic class mappings from the RxClass API."""
    __tablename__ = 'rxclass_cache'

    id         = db.Column(db.Integer, primary_key=True)
    rxcui      = db.Column(db.String(20), nullable=False, index=True)
    class_id   = db.Column(db.String(50), nullable=False)
    class_name = db.Column(db.String(300), default='')
    class_type = db.Column(db.String(50), default='')   # ATC, EPC, VA, MeSH
    source     = db.Column(db.String(30), default='rxclass_api')
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        db.UniqueConstraint('rxcui', 'class_id', name='uq_rxclass_rxcui_classid'),
    )

    def __repr__(self):
        return f'<RxClassCache {self.rxcui} → {self.class_name}>'


# ── OpenFDA Drug Labels ────────────────────────────────────────────
class FdaLabelCache(db.Model):
    """FDA-approved prescribing information summaries."""
    __tablename__ = 'fda_label_cache'

    id               = db.Column(db.Integer, primary_key=True)
    rxcui            = db.Column(db.String(20), nullable=False, unique=True, index=True)
    spl_id           = db.Column(db.String(80), default='')
    brand_name       = db.Column(db.String(300), default='')
    warnings_summary = db.Column(db.Text, default='')
    boxed_warning    = db.Column(db.Text, default='')
    contra_summary   = db.Column(db.Text, default='')
    source           = db.Column(db.String(30), default='openfda_api')
    created_at       = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<FdaLabelCache {self.rxcui} {self.brand_name}>'


# ── OpenFDA FAERS (Adverse Event Reports) ──────────────────────────
class FaersCache(db.Model):
    """Aggregated adverse-event report data from FDA FAERS."""
    __tablename__ = 'faers_cache'

    id             = db.Column(db.Integer, primary_key=True)
    rxcui          = db.Column(db.String(20), nullable=False, unique=True, index=True)
    total_reports  = db.Column(db.Integer, default=0)
    serious_count  = db.Column(db.Integer, default=0)
    top_reactions  = db.Column(db.JSON, default=list)   # [{reaction, count}, …]
    report_period  = db.Column(db.String(50), default='')  # e.g. '2020-01–2024-12'
    source         = db.Column(db.String(30), default='openfda_api')
    created_at     = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<FaersCache {self.rxcui} reports={self.total_reports}>'


# ── OpenFDA Drug Recalls ──────────────────────────────────────────
class RecallCache(db.Model):
    """FDA drug enforcement / recall records."""
    __tablename__ = 'recall_cache'

    id                  = db.Column(db.Integer, primary_key=True)
    recall_id           = db.Column(db.String(50), nullable=False, unique=True, index=True)
    product_description = db.Column(db.Text, default='')
    reason              = db.Column(db.Text, default='')
    status              = db.Column(db.String(30), default='')   # Ongoing, Completed, Terminated
    classification      = db.Column(db.String(20), default='')   # Class I / II / III
    recall_date         = db.Column(db.DateTime, nullable=True)
    source              = db.Column(db.String(30), default='openfda_api')
    created_at          = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<RecallCache {self.recall_id} {self.classification}>'


# ── LOINC (via FHIR / NIH) ────────────────────────────────────────
class LoincCache(db.Model):
    """LOINC code → lab test metadata."""
    __tablename__ = 'loinc_cache'

    id           = db.Column(db.Integer, primary_key=True)
    loinc_code   = db.Column(db.String(20), nullable=False, unique=True, index=True)
    component    = db.Column(db.String(300), default='')   # e.g. 'Glucose'
    system_type  = db.Column(db.String(100), default='')   # e.g. 'Ser/Plas'
    method       = db.Column(db.String(200), default='')
    display_name = db.Column(db.String(300), default='')
    source       = db.Column(db.String(30), default='loinc_api')
    created_at   = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<LoincCache {self.loinc_code} {self.display_name}>'


# ── UMLS (Unified Medical Language System) ─────────────────────────
class UmlsCache(db.Model):
    """UMLS Concept Unique Identifier → preferred name / type."""
    __tablename__ = 'umls_cache'

    id            = db.Column(db.Integer, primary_key=True)
    cui           = db.Column(db.String(20), nullable=False, unique=True, index=True)
    preferred_name = db.Column(db.String(400), default='')
    semantic_type = db.Column(db.String(200), default='')
    source_vocab  = db.Column(db.String(50), default='')   # e.g. 'SNOMEDCT_US'
    source        = db.Column(db.String(30), default='umls_api')
    created_at    = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<UmlsCache {self.cui} {self.preferred_name}>'


# ── HealthFinder.gov ───────────────────────────────────────────────
class HealthFinderCache(db.Model):
    """Patient education topics from HealthFinder.gov."""
    __tablename__ = 'healthfinder_cache'

    id           = db.Column(db.Integer, primary_key=True)
    topic_id     = db.Column(db.String(30), nullable=False, unique=True, index=True)
    title        = db.Column(db.String(300), default='')
    category     = db.Column(db.String(100), default='')
    url          = db.Column(db.String(500), default='')
    last_updated = db.Column(db.DateTime, nullable=True)
    source       = db.Column(db.String(30), default='healthfinder_api')
    created_at   = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<HealthFinderCache {self.topic_id} {self.title}>'


# ── PubMed (NCBI E-Utilities) ─────────────────────────────────────
class PubmedCache(db.Model):
    """PubMed article metadata."""
    __tablename__ = 'pubmed_cache'

    id            = db.Column(db.Integer, primary_key=True)
    pmid          = db.Column(db.String(20), nullable=False, unique=True, index=True)
    title         = db.Column(db.Text, default='')
    abstract_text = db.Column(db.Text, default='')
    authors       = db.Column(db.String(500), default='')
    pub_date      = db.Column(db.DateTime, nullable=True)
    journal       = db.Column(db.String(300), default='')
    mesh_terms    = db.Column(db.JSON, default=list)
    source        = db.Column(db.String(30), default='pubmed_api')
    created_at    = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<PubmedCache {self.pmid} {self.title[:40]}>'


# ── MedlinePlus ───────────────────────────────────────────────────
class MedlinePlusCache(db.Model):
    """Patient-friendly health topic summaries from MedlinePlus."""
    __tablename__ = 'medlineplus_cache'

    id       = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.String(30), nullable=False, unique=True, index=True)
    title    = db.Column(db.String(300), default='')
    url      = db.Column(db.String(500), default='')
    summary  = db.Column(db.Text, default='')
    language = db.Column(db.String(10), default='en')
    source   = db.Column(db.String(30), default='medlineplus_api')
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<MedlinePlusCache {self.topic_id} {self.title}>'


# ── CDC Immunization Schedule ─────────────────────────────────────
class CdcImmunizationCache(db.Model):
    """Vaccine schedule data from the CDC immunization API."""
    __tablename__ = 'cdc_immunization_cache'

    id                   = db.Column(db.Integer, primary_key=True)
    vaccine_code         = db.Column(db.String(20), nullable=False, unique=True, index=True)
    vaccine_name         = db.Column(db.String(200), default='')
    schedule_description = db.Column(db.Text, default='')
    min_age              = db.Column(db.String(30), default='')   # e.g. '6 months'
    max_age              = db.Column(db.String(30), default='')   # e.g. '65 years'
    source               = db.Column(db.String(30), default='cdc_api')
    created_at           = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<CdcImmunizationCache {self.vaccine_code} {self.vaccine_name}>'


# ── VSAC (Value Set Authority Center) ─────────────────────────────
class VsacValueSetCache(db.Model):
    """Expanded VSAC value sets — groups of codes defining clinical concepts."""
    __tablename__ = 'vsac_value_set_cache'

    id         = db.Column(db.Integer, primary_key=True)
    oid        = db.Column(db.String(100), nullable=False, unique=True, index=True)
    name       = db.Column(db.String(400), default='')
    codes_json = db.Column(db.Text, default='[]')   # JSON array of {code, system, display}
    code_count = db.Column(db.Integer, default=0)
    source     = db.Column(db.String(30), default='vsac_api')
    cached_at  = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<VsacValueSetCache {self.oid} {self.name}>'


# ── NLM Conditions (Clinical Tables) ──────────────────────────────
class NlmConditionsCache(db.Model):
    """Cached condition search results from NLM Clinical Tables API."""
    __tablename__ = 'nlm_conditions_cache'

    id          = db.Column(db.Integer, primary_key=True)
    search_term = db.Column(db.String(300), nullable=False, unique=True, index=True)
    conditions  = db.Column(db.JSON, default=list)   # [{name, icd10_codes}, …]
    result_count = db.Column(db.Integer, default=0)
    source      = db.Column(db.String(30), default='nlm_conditions_api')
    cached_at   = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<NlmConditionsCache "{self.search_term}" ({self.result_count} results)>'
