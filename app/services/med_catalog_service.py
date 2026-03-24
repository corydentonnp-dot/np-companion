"""
CareCompanion — MedCatalogService
File: app/services/med_catalog_service.py

Phase MM-2.1: Medication catalog management — seeding, auto-cataloging,
paginated queries, stats, and refresh.

Public API
----------
seed_catalog_common_meds()
seed_catalog_from_patients(user_id)
auto_catalog_new_medication(drug_name, rxcui)
get_catalog_page(filters, sort, page, per_page)
refresh_catalog_entry(entry_id)
get_catalog_stats()
"""

import logging
from datetime import datetime, timezone

from models import db
from models.monitoring import (
    MedicationCatalogEntry, MonitoringRule, MonitoringRuleOverride,
)

logger = logging.getLogger(__name__)


# ── Common PCP medications seed list (~100 top meds) ───────────────
# Each tuple: (display_name, normalized_name, ingredient_name, drug_class, rxcui)
COMMON_PCP_MEDS = [
    # Diabetes
    ('Metformin', 'metformin', 'metformin', 'Biguanides', '6809'),
    ('Glipizide', 'glipizide', 'glipizide', 'Sulfonylureas', '4821'),
    ('Glyburide', 'glyburide', 'glyburide', 'Sulfonylureas', '4815'),
    ('Glimepiride', 'glimepiride', 'glimepiride', 'Sulfonylureas', '25789'),
    ('Empagliflozin', 'empagliflozin', 'empagliflozin', 'SGLT2 Inhibitors', '1545653'),
    ('Dapagliflozin', 'dapagliflozin', 'dapagliflozin', 'SGLT2 Inhibitors', '1488564'),
    ('Canagliflozin', 'canagliflozin', 'canagliflozin', 'SGLT2 Inhibitors', '1373458'),
    ('Sitagliptin', 'sitagliptin', 'sitagliptin', 'DPP-4 Inhibitors', '593411'),
    ('Linagliptin', 'linagliptin', 'linagliptin', 'DPP-4 Inhibitors', '1100699'),
    ('Pioglitazone', 'pioglitazone', 'pioglitazone', 'Thiazolidinediones', '33738'),
    ('Semaglutide', 'semaglutide', 'semaglutide', 'GLP-1 Receptor Agonists', '1991302'),
    ('Liraglutide', 'liraglutide', 'liraglutide', 'GLP-1 Receptor Agonists', '475968'),
    ('Dulaglutide', 'dulaglutide', 'dulaglutide', 'GLP-1 Receptor Agonists', '1551291'),
    ('Insulin Glargine', 'insulin glargine', 'insulin glargine', 'Insulins', '274783'),
    ('Insulin Lispro', 'insulin lispro', 'insulin lispro', 'Insulins', '86009'),
    ('Insulin Aspart', 'insulin aspart', 'insulin aspart', 'Insulins', '86002'),

    # Cardiovascular
    ('Lisinopril', 'lisinopril', 'lisinopril', 'ACE Inhibitors', '29046'),
    ('Enalapril', 'enalapril', 'enalapril', 'ACE Inhibitors', '3827'),
    ('Ramipril', 'ramipril', 'ramipril', 'ACE Inhibitors', '35296'),
    ('Losartan', 'losartan', 'losartan', 'ARBs', '52175'),
    ('Valsartan', 'valsartan', 'valsartan', 'ARBs', '69749'),
    ('Olmesartan', 'olmesartan', 'olmesartan', 'ARBs', '321064'),
    ('Amlodipine', 'amlodipine', 'amlodipine', 'Calcium Channel Blockers', '17767'),
    ('Nifedipine', 'nifedipine', 'nifedipine', 'Calcium Channel Blockers', '7417'),
    ('Diltiazem', 'diltiazem', 'diltiazem', 'Calcium Channel Blockers', '3443'),
    ('Metoprolol', 'metoprolol', 'metoprolol', 'Beta Blockers', '6918'),
    ('Atenolol', 'atenolol', 'atenolol', 'Beta Blockers', '1202'),
    ('Carvedilol', 'carvedilol', 'carvedilol', 'Beta Blockers', '20352'),
    ('Propranolol', 'propranolol', 'propranolol', 'Beta Blockers', '8787'),
    ('Hydrochlorothiazide', 'hydrochlorothiazide', 'hydrochlorothiazide', 'Thiazide Diuretics', '5487'),
    ('Chlorthalidone', 'chlorthalidone', 'chlorthalidone', 'Thiazide Diuretics', '2409'),
    ('Furosemide', 'furosemide', 'furosemide', 'Loop Diuretics', '4603'),
    ('Spironolactone', 'spironolactone', 'spironolactone', 'Potassium-Sparing Diuretics', '9997'),
    ('Atorvastatin', 'atorvastatin', 'atorvastatin', 'Statins', '83367'),
    ('Rosuvastatin', 'rosuvastatin', 'rosuvastatin', 'Statins', '301542'),
    ('Simvastatin', 'simvastatin', 'simvastatin', 'Statins', '36567'),
    ('Pravastatin', 'pravastatin', 'pravastatin', 'Statins', '42463'),
    ('Ezetimibe', 'ezetimibe', 'ezetimibe', 'Cholesterol Absorption Inhibitors', '341248'),
    ('Fenofibrate', 'fenofibrate', 'fenofibrate', 'Fibrates', '8703'),
    ('Hydralazine', 'hydralazine', 'hydralazine', 'Vasodilators', '5470'),
    ('Isosorbide Mononitrate', 'isosorbide mononitrate', 'isosorbide mononitrate', 'Nitrates', '29046'),
    ('Digoxin', 'digoxin', 'digoxin', 'Cardiac Glycosides', '3407'),

    # Thyroid
    ('Levothyroxine', 'levothyroxine', 'levothyroxine', 'Thyroid Hormones', '10582'),
    ('Methimazole', 'methimazole', 'methimazole', 'Antithyroid Agents', '6835'),
    ('Propylthiouracil', 'propylthiouracil', 'propylthiouracil', 'Antithyroid Agents', '8794'),

    # Anticoagulation
    ('Warfarin', 'warfarin', 'warfarin', 'Vitamin K Antagonists', '11289'),
    ('Apixaban', 'apixaban', 'apixaban', 'Direct Oral Anticoagulants', '1364430'),
    ('Rivaroxaban', 'rivaroxaban', 'rivaroxaban', 'Direct Oral Anticoagulants', '1114195'),
    ('Dabigatran', 'dabigatran', 'dabigatran', 'Direct Oral Anticoagulants', '1037042'),
    ('Edoxaban', 'edoxaban', 'edoxaban', 'Direct Oral Anticoagulants', '1599538'),
    ('Enoxaparin', 'enoxaparin', 'enoxaparin', 'Low Molecular Weight Heparins', '67108'),
    ('Clopidogrel', 'clopidogrel', 'clopidogrel', 'Antiplatelet Agents', '32968'),

    # Pain / Neuro
    ('Gabapentin', 'gabapentin', 'gabapentin', 'Anticonvulsants', '25480'),
    ('Pregabalin', 'pregabalin', 'pregabalin', 'Anticonvulsants', '187832'),
    ('Carbamazepine', 'carbamazepine', 'carbamazepine', 'Anticonvulsants', '2002'),
    ('Valproic Acid', 'valproic acid', 'valproic acid', 'Anticonvulsants', '11118'),
    ('Phenytoin', 'phenytoin', 'phenytoin', 'Anticonvulsants', '8183'),
    ('Topiramate', 'topiramate', 'topiramate', 'Anticonvulsants', '38404'),
    ('Lamotrigine', 'lamotrigine', 'lamotrigine', 'Anticonvulsants', '28439'),
    ('Levetiracetam', 'levetiracetam', 'levetiracetam', 'Anticonvulsants', '39998'),
    ('Duloxetine', 'duloxetine', 'duloxetine', 'SNRIs', '72625'),
    ('Tramadol', 'tramadol', 'tramadol', 'Opioid Analgesics', '10689'),

    # Psychiatry
    ('Sertraline', 'sertraline', 'sertraline', 'SSRIs', '36437'),
    ('Escitalopram', 'escitalopram', 'escitalopram', 'SSRIs', '321988'),
    ('Fluoxetine', 'fluoxetine', 'fluoxetine', 'SSRIs', '4493'),
    ('Paroxetine', 'paroxetine', 'paroxetine', 'SSRIs', '32937'),
    ('Citalopram', 'citalopram', 'citalopram', 'SSRIs', '2556'),
    ('Venlafaxine', 'venlafaxine', 'venlafaxine', 'SNRIs', '39786'),
    ('Bupropion', 'bupropion', 'bupropion', 'Aminoketones', '42347'),
    ('Mirtazapine', 'mirtazapine', 'mirtazapine', 'Tetracyclic Antidepressants', '15996'),
    ('Trazodone', 'trazodone', 'trazodone', 'Serotonin Modulators', '10737'),
    ('Aripiprazole', 'aripiprazole', 'aripiprazole', 'Atypical Antipsychotics', '89013'),
    ('Quetiapine', 'quetiapine', 'quetiapine', 'Atypical Antipsychotics', '51272'),
    ('Olanzapine', 'olanzapine', 'olanzapine', 'Atypical Antipsychotics', '61381'),
    ('Risperidone', 'risperidone', 'risperidone', 'Atypical Antipsychotics', '35636'),
    ('Buspirone', 'buspirone', 'buspirone', 'Anxiolytics', '1827'),
    ('Hydroxyzine', 'hydroxyzine', 'hydroxyzine', 'Antihistamines', '5553'),

    # Immunosuppressive / Rheumatology
    ('Methotrexate', 'methotrexate', 'methotrexate', 'Antimetabolites', '6851'),
    ('Hydroxychloroquine', 'hydroxychloroquine', 'hydroxychloroquine', 'Antimalarials', '5521'),
    ('Sulfasalazine', 'sulfasalazine', 'sulfasalazine', 'Aminosalicylates', '9524'),
    ('Leflunomide', 'leflunomide', 'leflunomide', 'Pyrimidine Synthesis Inhibitors', '27169'),
    ('Azathioprine', 'azathioprine', 'azathioprine', 'Purine Antagonists', '1256'),
    ('Mycophenolate', 'mycophenolate', 'mycophenolate mofetil', 'Immunosuppressants', '68149'),
    ('Tacrolimus', 'tacrolimus', 'tacrolimus', 'Calcineurin Inhibitors', '42316'),
    ('Cyclosporine', 'cyclosporine', 'cyclosporine', 'Calcineurin Inhibitors', '3008'),

    # High-Risk Medications
    ('Lithium', 'lithium', 'lithium carbonate', 'Mood Stabilizers', '6448'),
    ('Clozapine', 'clozapine', 'clozapine', 'Atypical Antipsychotics', '2626'),
    ('Isotretinoin', 'isotretinoin', 'isotretinoin', 'Retinoids', '6064'),
    ('Amiodarone', 'amiodarone', 'amiodarone', 'Antiarrhythmics', '703'),
    ('Allopurinol', 'allopurinol', 'allopurinol', 'Xanthine Oxidase Inhibitors', '519'),
    ('Colchicine', 'colchicine', 'colchicine', 'Gout Agents', '2683'),

    # Respiratory
    ('Montelukast', 'montelukast', 'montelukast', 'Leukotriene Modifiers', '88249'),
    ('Theophylline', 'theophylline', 'theophylline', 'Methylxanthines', '10438'),

    # GI
    ('Omeprazole', 'omeprazole', 'omeprazole', 'Proton Pump Inhibitors', '7646'),
    ('Pantoprazole', 'pantoprazole', 'pantoprazole', 'Proton Pump Inhibitors', '40790'),

    # Misc
    ('Prednisone', 'prednisone', 'prednisone', 'Corticosteroids', '8640'),
    ('Doxycycline', 'doxycycline', 'doxycycline', 'Tetracyclines', '3640'),
    ('Amoxicillin', 'amoxicillin', 'amoxicillin', 'Penicillins', '723'),
    ('Trimethoprim-Sulfamethoxazole', 'trimethoprim-sulfamethoxazole', 'trimethoprim/sulfamethoxazole', 'Sulfonamides', '10831'),
]


class MedCatalogService:
    """Medication catalog management service."""

    def __init__(self, db_session=None):
        self._db = db_session or db

    # ================================================================
    # 1. Seeding — common PCP meds
    # ================================================================

    def seed_catalog_common_meds(self) -> int:
        """
        Insert ~100 common PCP medications into MedicationCatalogEntry.
        Idempotent: skips existing entries matched by normalized_name.
        Returns count of newly created entries.
        """
        created = 0
        for display, normalized, ingredient, drug_class, rxcui in COMMON_PCP_MEDS:
            existing = MedicationCatalogEntry.query.filter_by(
                normalized_name=normalized
            ).first()
            if existing:
                continue

            # Check if monitoring rules exist for this rxcui
            has_rules = MonitoringRule.query.filter_by(
                rxcui=rxcui, is_active=True
            ).first() is not None

            entry = MedicationCatalogEntry(
                display_name=display,
                normalized_name=normalized,
                rxcui=rxcui,
                ingredient_name=ingredient,
                drug_class=drug_class,
                source_origin='seeded',
                source_confidence=1.0,
                status='active' if has_rules else 'unmapped',
                is_active=True,
            )
            self._db.session.add(entry)
            created += 1

        try:
            self._db.session.commit()
            logger.info("Seeded %d common PCP medications into catalog", created)
        except Exception:
            self._db.session.rollback()
            raise

        return created

    # ================================================================
    # 2. Seeding — from local patient data
    # ================================================================

    def seed_catalog_from_patients(self, user_id: int) -> int:
        """
        Scan PatientMedication table, group by normalized name,
        create/update MedicationCatalogEntry rows with patient counts.
        Returns count of new entries created.
        """
        from models.patient import PatientMedication

        # Get active patient meds grouped by normalized name
        meds = (
            PatientMedication.query
            .filter_by(status='active')
            .all()
        )

        # Group by lowercased drug name
        med_groups = {}
        for med in meds:
            key = (med.drug_name or '').strip().lower()
            if not key:
                continue
            if key not in med_groups:
                med_groups[key] = {
                    'display_name': med.drug_name,
                    'rxcui': med.rxnorm_cui or '',
                    'count': 0,
                }
            med_groups[key]['count'] += 1

        created = 0
        for normalized, info in med_groups.items():
            existing = MedicationCatalogEntry.query.filter_by(
                normalized_name=normalized
            ).first()

            if existing:
                # Update patient count
                existing.local_patient_count = info['count']
                existing.last_seen_at = datetime.now(timezone.utc)
                if existing.source_origin == 'seeded':
                    existing.source_origin = 'local_patient'
                continue

            has_rules = False
            if info['rxcui']:
                has_rules = MonitoringRule.query.filter_by(
                    rxcui=info['rxcui'], is_active=True
                ).first() is not None

            entry = MedicationCatalogEntry(
                display_name=info['display_name'],
                normalized_name=normalized,
                rxcui=info['rxcui'],
                source_origin='local_patient',
                source_confidence=0.8,
                status='active' if has_rules else 'pending_review',
                local_patient_count=info['count'],
                is_active=True,
            )
            self._db.session.add(entry)
            created += 1

        try:
            self._db.session.commit()
            logger.info(
                "Imported %d new medications from patient data "
                "(updated counts for existing)",
                created
            )
        except Exception:
            self._db.session.rollback()
            raise

        return created

    # ================================================================
    # 3. Auto-catalog on XML import
    # ================================================================

    def auto_catalog_new_medication(
        self, drug_name: str, rxcui: str = None
    ) -> MedicationCatalogEntry | None:
        """
        Called during clinical summary XML import.
        Creates catalog entry if not already present.
        Returns the entry (new or existing).
        """
        normalized = (drug_name or '').strip().lower()
        if not normalized:
            return None

        existing = MedicationCatalogEntry.query.filter_by(
            normalized_name=normalized
        ).first()
        if existing:
            existing.local_patient_count = (existing.local_patient_count or 0) + 1
            existing.last_seen_at = datetime.now(timezone.utc)
            return existing

        has_rules = False
        if rxcui:
            has_rules = MonitoringRule.query.filter_by(
                rxcui=rxcui, is_active=True
            ).first() is not None

        entry = MedicationCatalogEntry(
            display_name=drug_name,
            normalized_name=normalized,
            rxcui=rxcui or '',
            source_origin='local_patient',
            source_confidence=0.7,
            status='active' if has_rules else 'pending_review',
            local_patient_count=1,
            is_active=True,
        )
        self._db.session.add(entry)
        return entry

    # ================================================================
    # 4. Paginated catalog query
    # ================================================================

    def get_catalog_page(
        self,
        filters: dict = None,
        sort: str = 'display_name',
        page: int = 1,
        per_page: int = 50,
    ) -> dict:
        """
        Return paginated catalog entries with computed effective_interval.

        Filters:
          status — str filter on status column
          has_rules — bool (True = only with rules, False = only without)
          source — str filter on source_origin
          search — text search on display_name/ingredient_name
          drug_class — str filter on drug_class
          low_confidence — bool (True = confidence < 0.5)
          overridden — bool (True = entries with overrides)

        Returns dict with keys: items, total, page, per_page, pages
        """
        filters = filters or {}
        q = MedicationCatalogEntry.query

        # Apply filters
        if filters.get('status'):
            q = q.filter_by(status=filters['status'])
        if filters.get('source'):
            q = q.filter_by(source_origin=filters['source'])
        if filters.get('drug_class'):
            q = q.filter_by(drug_class=filters['drug_class'])
        if filters.get('search'):
            term = f"%{filters['search']}%"
            q = q.filter(
                db.or_(
                    MedicationCatalogEntry.display_name.ilike(term),
                    MedicationCatalogEntry.ingredient_name.ilike(term),
                    MedicationCatalogEntry.rxcui.ilike(term),
                )
            )
        if filters.get('low_confidence'):
            q = q.filter(MedicationCatalogEntry.source_confidence < 0.5)
        if filters.get('is_active') is not None:
            q = q.filter_by(is_active=filters['is_active'])

        # Sorting
        sort_map = {
            'display_name': MedicationCatalogEntry.display_name,
            'drug_class': MedicationCatalogEntry.drug_class,
            'status': MedicationCatalogEntry.status,
            'patient_count': MedicationCatalogEntry.local_patient_count.desc(),
            'confidence': MedicationCatalogEntry.source_confidence,
            'last_seen': MedicationCatalogEntry.last_seen_at.desc(),
        }
        order = sort_map.get(sort, MedicationCatalogEntry.display_name)
        q = q.order_by(order)

        total = q.count()
        pages = max(1, (total + per_page - 1) // per_page)
        items = q.offset((page - 1) * per_page).limit(per_page).all()

        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': pages,
        }

    # ================================================================
    # 5. Refresh a single catalog entry
    # ================================================================

    def refresh_catalog_entry(self, entry_id: int) -> dict:
        """
        Re-fetch API data for a catalog entry:
        1. Re-lookup RxNorm (ingredient, class)
        2. Trigger MonitoringRuleEngine.refresh_rules_for_medication()
        3. Update last_refreshed_at
        """
        entry = MedicationCatalogEntry.query.get(entry_id)
        if not entry:
            return {'success': False, 'error': 'Entry not found'}

        # Try RxNorm re-lookup
        try:
            from app.services.api.rxnorm import RxNormService
            rxnorm = RxNormService(self._db)
            info = rxnorm.get_drug_info(entry.display_name)
            if info:
                entry.rxcui = info.get('rxcui', entry.rxcui)
                entry.ingredient_name = info.get('ingredient', entry.ingredient_name)
                entry.ingredient_rxcui = info.get('ingredient_rxcui', entry.ingredient_rxcui)
        except Exception as exc:
            logger.debug("RxNorm refresh failed for %s: %s", entry.display_name, exc)

        # Try RxClass re-lookup
        try:
            from app.services.api.rxclass import RxClassService
            rxclass = RxClassService(self._db)
            if entry.rxcui:
                classes = rxclass.get_classes_for_drug(entry.rxcui)
                if classes:
                    entry.drug_class = classes[0].get(
                        'className',
                        classes[0].get('rxclassMinConceptItem', {}).get('className', entry.drug_class)
                    )
        except Exception as exc:
            logger.debug("RxClass refresh failed for %s: %s", entry.display_name, exc)

        # Trigger rule engine refresh
        try:
            from app.services.monitoring_rule_engine import MonitoringRuleEngine
            engine = MonitoringRuleEngine(self._db)
            rules = engine.refresh_rules_for_medication(
                drug_name=entry.display_name, rxcui=entry.rxcui
            )
            if rules:
                entry.status = 'active'
                entry.source_confidence = max(
                    entry.source_confidence,
                    max(r.extraction_confidence for r in rules if hasattr(r, 'extraction_confidence'))
                )
        except Exception as exc:
            logger.debug("Rule refresh failed for %s: %s", entry.display_name, exc)

        entry.last_refreshed_at = datetime.now(timezone.utc)

        try:
            self._db.session.commit()
        except Exception:
            self._db.session.rollback()
            raise

        return {'success': True, 'entry_id': entry_id}

    # ================================================================
    # 6. Catalog statistics
    # ================================================================

    def get_catalog_stats(self) -> dict:
        """
        Summary counts for the catalog dashboard.
        """
        total = MedicationCatalogEntry.query.filter_by(is_active=True).count()

        # Entries that have at least one monitoring rule via rxcui
        with_rules = (
            self._db.session.query(MedicationCatalogEntry.id)
            .filter(MedicationCatalogEntry.is_active == True)
            .filter(MedicationCatalogEntry.rxcui != '')
            .filter(MedicationCatalogEntry.rxcui != None)
            .join(MonitoringRule, MonitoringRule.rxcui == MedicationCatalogEntry.rxcui)
            .filter(MonitoringRule.is_active == True)
            .distinct()
            .count()
        )

        without_rules = total - with_rules

        overridden = (
            self._db.session.query(MonitoringRuleOverride.id)
            .filter(MonitoringRuleOverride.override_active == True)
            .distinct()
            .count()
        )

        status_counts = {}
        for status_val in ['active', 'pending_review', 'unmapped', 'inactive', 'suppressed']:
            status_counts[status_val] = (
                MedicationCatalogEntry.query
                .filter_by(status=status_val, is_active=True)
                .count()
            )

        low_confidence = (
            MedicationCatalogEntry.query
            .filter(MedicationCatalogEntry.source_confidence < 0.5)
            .filter_by(is_active=True)
            .count()
        )

        return {
            'total': total,
            'with_rules': with_rules,
            'without_rules': without_rules,
            'overridden': overridden,
            'low_confidence': low_confidence,
            'by_status': status_counts,
        }
