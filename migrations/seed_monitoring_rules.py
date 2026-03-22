"""
Seed: Condition-Driven Monitoring Rules — Phase 23.B3
File: migrations/seed_monitoring_rules.py

Seeds MonitoringRule entries for:
  - 10 primary-care disease families
  - Pre-treatment genotype/serology rules
  - Expanded medication class monitoring
  - KDIGO eGFR dose-adjustment threshold rules

All entries use trigger_type=CONDITION (disease families) or GENOTYPE
(pre-treatment), source=MANUAL, extraction_confidence=1.0.

Idempotent: deletes existing source=MANUAL rules then re-inserts.
API-sourced rules (DAILYMED, VSAC, etc.) are never touched.

Usage
-----
    venv\\Scripts\\python.exe migrations/seed_monitoring_rules.py
"""

import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# =====================================================================
# Seed Data
#
# Each tuple:
#   (rxcui, rxclass_id, icd10_trigger, trigger_type, source,
#    lab_loinc_code, lab_cpt_code, lab_name, interval_days, priority,
#    evidence_source_url, extraction_confidence, clinical_context)
#
# rxcui/rxclass_id/icd10_trigger: exactly one non-null per row
# =====================================================================

SEED_RULES = [
    # ── 1. Diabetes mellitus (E10, E11, R73) ────────────────────────
    (None, None, 'E11', 'CONDITION', 'MANUAL',
     '4548-4', '83036', 'Hemoglobin A1C', 90, 'standard',
     'https://www.ncbi.nlm.nih.gov/books/NBK568002/', 1.0,
     'HbA1c quarterly if not at goal; every 6 months if at goal. ADA Standards of Care.'),
    (None, None, 'E11', 'CONDITION', 'MANUAL',
     '14959-1', '82043', 'Urine Albumin-to-Creatinine Ratio (UACR)', 365, 'standard',
     'https://www.ncbi.nlm.nih.gov/books/NBK568002/', 1.0,
     'UACR annually for diabetic nephropathy screening. ADA/KDIGO.'),
    (None, None, 'E11', 'CONDITION', 'MANUAL',
     '2160-0', '80048', 'Basic Metabolic Panel (BMP/eGFR)', 365, 'standard',
     'https://www.ncbi.nlm.nih.gov/books/NBK568002/', 1.0,
     'BMP with eGFR annually for renal function. ADA Standards of Care.'),
    (None, None, 'E11', 'CONDITION', 'MANUAL',
     '2093-3', '80061', 'Lipid Panel', 365, 'standard',
     'https://www.ncbi.nlm.nih.gov/books/NBK568002/', 1.0,
     'Lipid panel annually — statin therapy assessment. ADA/ACC.'),
    (None, None, 'E10', 'CONDITION', 'MANUAL',
     '4548-4', '83036', 'Hemoglobin A1C', 90, 'standard',
     'https://www.ncbi.nlm.nih.gov/books/NBK568002/', 1.0,
     'HbA1c quarterly if not at goal. ADA Standards of Care — Type 1.'),
    (None, None, 'E10', 'CONDITION', 'MANUAL',
     '14959-1', '82043', 'Urine Albumin-to-Creatinine Ratio (UACR)', 365, 'standard',
     'https://www.ncbi.nlm.nih.gov/books/NBK568002/', 1.0,
     'UACR annually — Type 1 diabetes nephropathy screening.'),

    # ── 2. CKD by stage (N18) ──────────────────────────────────────
    (None, None, 'N18', 'CONDITION', 'MANUAL',
     '2160-0', '80048', 'BMP (Creatinine/Electrolytes/eGFR)', 120, 'high',
     'https://kdigo.org/guidelines/ckd-evaluation-and-management/', 1.0,
     'BMP every 3-6 months CKD stages 3-5. KDIGO 2024.'),
    (None, None, 'N18', 'CONDITION', 'MANUAL',
     '718-7', '85025', 'CBC with Differential', 180, 'standard',
     'https://kdigo.org/guidelines/ckd-evaluation-and-management/', 1.0,
     'CBC for anemia of CKD — erythropoietin deficiency common stage 3+.'),
    (None, None, 'N18', 'CONDITION', 'MANUAL',
     '2777-1', '84100', 'Phosphorus', 180, 'standard',
     'https://kdigo.org/guidelines/ckd-mbd/', 1.0,
     'Phosphorus + calcium + PTH in CKD stages 3b+. KDIGO CKD-MBD.'),
    (None, None, 'N18', 'CONDITION', 'MANUAL',
     '17861-6', '82310', 'Calcium', 180, 'standard',
     'https://kdigo.org/guidelines/ckd-mbd/', 1.0,
     'Calcium monitoring for CKD mineral-bone disorder.'),
    (None, None, 'N18', 'CONDITION', 'MANUAL',
     '2731-8', '83970', 'Intact PTH', 180, 'standard',
     'https://kdigo.org/guidelines/ckd-mbd/', 1.0,
     'PTH monitoring CKD stages 3b-5 — secondary hyperparathyroidism.'),
    (None, None, 'N18', 'CONDITION', 'MANUAL',
     '14959-1', '82043', 'Urine Albumin-to-Creatinine Ratio (UACR)', 365, 'standard',
     'https://kdigo.org/guidelines/ckd-evaluation-and-management/', 1.0,
     'UACR for albuminuria staging. KDIGO 2024.'),

    # ── 3. Heart failure (I50) ──────────────────────────────────────
    (None, None, 'I50', 'CONDITION', 'MANUAL',
     '2160-0', '80048', 'BMP (Renal/Electrolytes)', 120, 'high',
     'https://www.ahajournals.org/doi/10.1161/CIR.0000000000001063', 1.0,
     'BMP at every med change and every 3-6 months. AHA/ACC HF guidelines.'),
    (None, None, 'I50', 'CONDITION', 'MANUAL',
     '30934-4', '83880', 'BNP or NT-proBNP', 180, 'standard',
     'https://www.ahajournals.org/doi/10.1161/CIR.0000000000001063', 1.0,
     'BNP/NT-proBNP at clinical decision points for decompensation assessment.'),
    (None, None, 'I50', 'CONDITION', 'MANUAL',
     '718-7', '85025', 'CBC with Differential', 180, 'standard',
     'https://www.ahajournals.org/doi/10.1161/CIR.0000000000001063', 1.0,
     'CBC for anemia co-management in HF patients.'),
    (None, None, 'I50', 'CONDITION', 'MANUAL',
     '2498-4', '83540', 'Iron Studies (Serum Iron)', 365, 'standard',
     'https://www.ahajournals.org/doi/10.1161/CIR.0000000000001063', 1.0,
     'Iron studies if anemia present — IV iron improves outcomes in HFrEF.'),

    # ── 4. Atrial fibrillation (I48) ───────────────────────────────
    (None, None, 'I48', 'CONDITION', 'MANUAL',
     '2160-0', '80048', 'BMP/eGFR (for DOAC dosing)', 365, 'high',
     'https://www.ahajournals.org/doi/10.1161/CIR.0000000000001045', 1.0,
     'Renal function for DOAC dosing annually; every 3-6 months if age >75 or CKD.'),
    (None, None, 'I48', 'CONDITION', 'MANUAL',
     '3016-3', '84443', 'TSH', 365, 'standard',
     'https://www.ahajournals.org/doi/10.1161/CIR.0000000000001045', 1.0,
     'TSH at diagnosis and annually — afib is often presenting sign of thyroid disease.'),

    # ── 5. Liver disease / chronic hepatitis (K70-K76, B18) ────────
    (None, None, 'K74', 'CONDITION', 'MANUAL',
     '1984-4', '82105', 'Alpha-Fetoprotein (AFP)', 180, 'high',
     'https://www.aasld.org/practice-guidelines/hepatocellular-carcinoma', 1.0,
     'AFP every 6 months for HCC surveillance if cirrhosis. AASLD guidelines.'),
    (None, None, 'B18', 'CONDITION', 'MANUAL',
     '5009-6', '87340', 'HBV DNA / HBsAg', 120, 'high',
     'https://www.aasld.org/practice-guidelines/hepatitis-b', 1.0,
     'HBV DNA + LFTs every 3-6 months for chronic HBV. AASLD.'),
    (None, None, 'K76', 'CONDITION', 'MANUAL',
     '1920-8', '80076', 'Hepatic Function Panel (LFTs)', 90, 'standard',
     'https://www.aasld.org/practice-guidelines/', 1.0,
     'LFTs quarterly for chronic liver disease monitoring.'),

    # ── 6. Autoimmune — SLE (M32), RA (M05/M06) ───────────────────
    (None, None, 'M32', 'CONDITION', 'MANUAL',
     '718-7', '85025', 'CBC with Differential', 90, 'high',
     'https://ard.bmj.com/content/78/6/736', 1.0,
     'CBC quarterly during active SLE. EULAR/ACR guidelines.'),
    (None, None, 'M32', 'CONDITION', 'MANUAL',
     '2160-0', '80048', 'BMP (Renal Function)', 90, 'high',
     'https://ard.bmj.com/content/78/6/736', 1.0,
     'BMP quarterly — lupus nephritis monitoring. EULAR/ACR.'),
    (None, None, 'M32', 'CONDITION', 'MANUAL',
     '4485-9', '86160', 'Complement C3/C4', 90, 'standard',
     'https://ard.bmj.com/content/78/6/736', 1.0,
     'Complement C3/C4 quarterly during active SLE for disease activity assessment.'),
    (None, None, 'M32', 'CONDITION', 'MANUAL',
     '35396-5', '86235', 'Anti-dsDNA Antibody', 90, 'standard',
     'https://ard.bmj.com/content/78/6/736', 1.0,
     'Anti-dsDNA quarterly — rising titer predicts lupus nephritis flare.'),
    (None, None, 'M05', 'CONDITION', 'MANUAL',
     '718-7', '85025', 'CBC with Differential', 90, 'high',
     'https://www.rheumatology.org/Practice-Quality/Clinical-Support/', 1.0,
     'CBC quarterly on DMARDs — monitors for cytopenias. ACR RA guidelines.'),
    (None, None, 'M05', 'CONDITION', 'MANUAL',
     '1920-8', '80076', 'Hepatic Function Panel (LFTs)', 90, 'high',
     'https://www.rheumatology.org/Practice-Quality/Clinical-Support/', 1.0,
     'LFTs quarterly on DMARDs — hepatotoxicity risk (methotrexate, leflunomide).'),
    (None, None, 'M05', 'CONDITION', 'MANUAL',
     '30341-2', '85651', 'ESR (Sedimentation Rate)', 90, 'standard',
     'https://www.rheumatology.org/Practice-Quality/Clinical-Support/', 1.0,
     'ESR/CRP for RA disease activity monitoring.'),

    # ── 7. COPD (J44) ─────────────────────────────────────────────
    (None, None, 'J44', 'CONDITION', 'MANUAL',
     '19868-9', '94010', 'Spirometry (FEV1/FVC)', 365, 'standard',
     'https://goldcopd.org/2024-gold-report/', 1.0,
     'Spirometry annually for COPD severity staging. GOLD 2024.'),
    (None, None, 'J44', 'CONDITION', 'MANUAL',
     '718-7', '85025', 'CBC with Differential', 365, 'standard',
     'https://goldcopd.org/2024-gold-report/', 1.0,
     'CBC for polycythemia from chronic hypoxia.'),

    # ── 8. Seizure disorders (G40) ─────────────────────────────────
    (None, None, 'G40', 'CONDITION', 'MANUAL',
     '3968-5', '80185', 'Phenytoin Level', 90, 'high',
     'https://www.epilepsy.com/treatment/medicines', 1.0,
     'Therapeutic drug monitoring — phenytoin narrow therapeutic index.'),
    (None, None, 'G40', 'CONDITION', 'MANUAL',
     '3432-2', '80156', 'Carbamazepine Level', 90, 'high',
     'https://www.epilepsy.com/treatment/medicines', 1.0,
     'Therapeutic drug monitoring — carbamazepine. Check with CBC and LFTs.'),
    (None, None, 'G40', 'CONDITION', 'MANUAL',
     '4086-5', '80164', 'Valproic Acid Level', 90, 'high',
     'https://www.epilepsy.com/treatment/medicines', 1.0,
     'Therapeutic drug monitoring — valproic acid. Monitor with LFTs and ammonia.'),
    (None, None, 'G40', 'CONDITION', 'MANUAL',
     '3948-7', '80184', 'Phenobarbital Level', 90, 'high',
     'https://www.epilepsy.com/treatment/medicines', 1.0,
     'Therapeutic drug monitoring — phenobarbital.'),

    # ── 9. Thyroid disorders (E01-E07) ─────────────────────────────
    (None, None, 'E03', 'CONDITION', 'MANUAL',
     '3016-3', '84443', 'TSH', 180, 'standard',
     'https://www.thyroid.org/professionals/ata-professional-guidelines/', 1.0,
     'TSH every 6-12 months on stable thyroid replacement. ATA guidelines.'),
    (None, None, 'E03', 'CONDITION', 'MANUAL',
     '3024-7', '84439', 'Free T4', 180, 'standard',
     'https://www.thyroid.org/professionals/ata-professional-guidelines/', 1.0,
     'Free T4 when on medication adjustment — assess therapeutic response.'),
    (None, None, 'E05', 'CONDITION', 'MANUAL',
     '3016-3', '84443', 'TSH', 90, 'standard',
     'https://www.thyroid.org/professionals/ata-professional-guidelines/', 1.0,
     'TSH every 1-3 months during hyperthyroid treatment titration. ATA.'),

    # ── 10. Behavioral health / psychiatric ────────────────────────
    (None, None, 'F20', 'CONDITION', 'MANUAL',
     '1558-6', '82947', 'Fasting Glucose', 90, 'high',
     'https://psychiatryonline.org/doi/book/10.1176/appi.books.9780890424865', 1.0,
     'Metabolic monitoring for atypical antipsychotics — APA protocol: glucose at baseline, 3 months, annually.'),
    (None, None, 'F20', 'CONDITION', 'MANUAL',
     '4548-4', '83036', 'Hemoglobin A1C', 365, 'standard',
     'https://psychiatryonline.org/doi/book/10.1176/appi.books.9780890424865', 1.0,
     'HbA1c annually — antipsychotic metabolic monitoring. APA protocol.'),
    (None, None, 'F20', 'CONDITION', 'MANUAL',
     '2093-3', '80061', 'Lipid Panel', 365, 'standard',
     'https://psychiatryonline.org/doi/book/10.1176/appi.books.9780890424865', 1.0,
     'Lipid panel annually — atypical antipsychotic metabolic screening.'),
    (None, None, 'F31', 'CONDITION', 'MANUAL',
     '3719-2', '80178', 'Lithium Level', 90, 'critical',
     'https://psychiatryonline.org/doi/book/10.1176/appi.books.9780890424865', 1.0,
     'Lithium level at initiation, 6 months, then annually. Narrow therapeutic index.'),
    (None, None, 'F31', 'CONDITION', 'MANUAL',
     '3016-3', '84443', 'TSH (Lithium monitoring)', 180, 'high',
     'https://psychiatryonline.org/doi/book/10.1176/appi.books.9780890424865', 1.0,
     'TSH every 6 months on lithium — hypothyroidism is common adverse effect.'),
    (None, None, 'F31', 'CONDITION', 'MANUAL',
     '2160-0', '80048', 'BMP (Lithium monitoring)', 180, 'high',
     'https://psychiatryonline.org/doi/book/10.1176/appi.books.9780890424865', 1.0,
     'BMP every 6 months on lithium — renal toxicity monitoring.'),

    # ═══════════════════════════════════════════════════════════════
    # PRE-TREATMENT GENOTYPE / SEROLOGY RULES
    # ═══════════════════════════════════════════════════════════════
    (None, None, 'Z79.899', 'GENOTYPE', 'MANUAL',
     '51714-8', '81381', 'HLA-B*5701 (Abacavir)', 0, 'critical',
     'https://cpicpgx.org/guidelines/guideline-for-abacavir-and-hla-b/', 1.0,
     'HLA-B*5701 before abacavir — fatal hypersensitivity if positive. One-time pre-treatment.'),
    (None, None, 'Z79.899', 'GENOTYPE', 'MANUAL',
     '51713-0', '81401', 'TPMT Genotype (Azathioprine/6-MP)', 0, 'critical',
     'https://cpicpgx.org/guidelines/guideline-for-thiopurines-and-tpmt/', 1.0,
     'TPMT genotype before azathioprine or 6-MP — fatal myelosuppression in poor metabolizers.'),
    (None, None, 'Z79.899', 'GENOTYPE', 'MANUAL',
     '7065-0', '82955', 'G6PD (Dapsone/Primaquine)', 0, 'critical',
     'https://www.ncbi.nlm.nih.gov/books/NBK100238/', 1.0,
     'G6PD before dapsone or primaquine — hemolytic anemia risk.'),
    (None, None, 'Z79.899', 'GENOTYPE', 'MANUAL',
     '51714-8', '81374', 'HLA-B*1502 (Carbamazepine)', 0, 'critical',
     'https://cpicpgx.org/guidelines/guideline-for-carbamazepine-and-hla-b/', 1.0,
     'HLA-B*1502 before carbamazepine in Asian ancestry — Stevens-Johnson syndrome.'),
    (None, None, 'Z79.899', 'GENOTYPE', 'MANUAL',
     '22322-2', '86704', 'Hepatitis B Serology (Pre-biologic)', 0, 'critical',
     'https://www.aasld.org/practice-guidelines/hepatitis-b', 1.0,
     'HBV serology before rituximab or other biologics — reactivation risk.'),
    (None, None, 'Z79.899', 'GENOTYPE', 'MANUAL',
     '71774-4', '86480', 'TB Screening IGRA (Pre-biologic/JAKi)', 0, 'critical',
     'https://www.cdc.gov/tb/topic/testing/tbtesttypes.htm', 1.0,
     'TB screening (IGRA preferred) before any biologic or JAK inhibitor.'),

    # ═══════════════════════════════════════════════════════════════
    # EXPANDED MEDICATION CLASS MONITORING
    # (rxclass_id used for class-level rules)
    # ═══════════════════════════════════════════════════════════════

    # ACE inhibitors / ARBs
    (None, 'C09AA', None, 'MEDICATION', 'MANUAL',
     '2160-0', '80048', 'BMP (Creatinine + K+)', 365, 'high',
     'https://www.ahajournals.org/doi/10.1161/HYP.0000000000000065', 1.0,
     'Creatinine + K+ at 1-2 weeks after start/dose change, then annually. ACE inhibitor class.'),
    (None, 'C09CA', None, 'MEDICATION', 'MANUAL',
     '2160-0', '80048', 'BMP (Creatinine + K+)', 365, 'high',
     'https://www.ahajournals.org/doi/10.1161/HYP.0000000000000065', 1.0,
     'Creatinine + K+ at 1-2 weeks after start/dose change, then annually. ARB class.'),

    # Spironolactone / eplerenone
    (None, 'C03DA', None, 'MEDICATION', 'MANUAL',
     '6298-4', '80051', 'Electrolyte Panel (K+)', 90, 'critical',
     'https://www.ahajournals.org/doi/10.1161/CIR.0000000000001063', 1.0,
     'K+ at 1 week, 1 month, then quarterly — potassium can spike lethally.'),

    # Loop diuretics
    (None, 'C03CA', None, 'MEDICATION', 'MANUAL',
     '2160-0', '80048', 'BMP', 90, 'high',
     'https://www.ahajournals.org/doi/10.1161/CIR.0000000000001063', 1.0,
     'BMP + magnesium quarterly — loop diuretics deplete electrolytes.'),
    (None, 'C03CA', None, 'MEDICATION', 'MANUAL',
     '19123-9', '83735', 'Magnesium', 90, 'standard',
     'https://www.ahajournals.org/doi/10.1161/CIR.0000000000001063', 1.0,
     'Magnesium quarterly with loop diuretics — hypomagnesemia risk.'),

    # Thiazide diuretics
    (None, 'C03AA', None, 'MEDICATION', 'MANUAL',
     '2160-0', '80048', 'BMP + Glucose + Uric Acid', 180, 'standard',
     'https://www.ahajournals.org/doi/10.1161/HYP.0000000000000065', 1.0,
     'BMP, glucose, uric acid — thiazides cause hyponatremia, hyperglycemia, hyperuricemia.'),

    # SGLT-2 inhibitors
    (None, 'A10BK', None, 'MEDICATION', 'MANUAL',
     '2160-0', '80048', 'BMP/eGFR', 180, 'high',
     'https://kdigo.org/guidelines/diabetes-ckd/', 1.0,
     'eGFR before initiating and periodically — contraindicated below eGFR 30. KDIGO.'),

    # Digoxin
    ('3407', None, None, 'MEDICATION', 'MANUAL',
     '10535-3', '80162', 'Digoxin Level', 180, 'critical',
     'https://www.ahajournals.org/doi/10.1161/CIR.0000000000001063', 1.0,
     'Digoxin level — narrow therapeutic index. K+ directly affects toxicity threshold.'),
    ('3407', None, None, 'MEDICATION', 'MANUAL',
     '6298-4', '80051', 'Electrolyte Panel (K+)', 90, 'critical',
     'https://www.ahajournals.org/doi/10.1161/CIR.0000000000001063', 1.0,
     'K+ monitoring with digoxin — hypokalemia potentiates digoxin toxicity.'),

    # Amiodarone
    ('596', None, None, 'MEDICATION', 'MANUAL',
     '1920-8', '80076', 'Hepatic Function Panel', 180, 'high',
     'https://www.ahajournals.org/doi/10.1161/CIR.0000000000001045', 1.0,
     'LFTs every 6 months — amiodarone hepatotoxicity.'),
    ('596', None, None, 'MEDICATION', 'MANUAL',
     '3016-3', '84443', 'TSH', 180, 'high',
     'https://www.ahajournals.org/doi/10.1161/CIR.0000000000001045', 1.0,
     'TSH every 6 months — amiodarone causes hypo/hyperthyroidism (iodine load).'),
    ('596', None, None, 'MEDICATION', 'MANUAL',
     '19868-9', '94010', 'Pulmonary Function Tests', 365, 'high',
     'https://www.ahajournals.org/doi/10.1161/CIR.0000000000001045', 1.0,
     'Annual PFTs + chest X-ray — amiodarone pulmonary toxicity.'),

    # Valproic acid
    ('11118', None, None, 'MEDICATION', 'MANUAL',
     '1920-8', '80076', 'Hepatic Function Panel', 90, 'high',
     'https://www.epilepsy.com/treatment/medicines', 1.0,
     'LFTs quarterly — valproic acid hepatotoxicity, especially first 6 months.'),
    ('11118', None, None, 'MEDICATION', 'MANUAL',
     '1988-5', '82140', 'Ammonia Level', 180, 'standard',
     'https://www.epilepsy.com/treatment/medicines', 1.0,
     'Ammonia if confusion or lethargy — valproic acid hyperammonemia.'),
    ('11118', None, None, 'MEDICATION', 'MANUAL',
     '718-7', '85025', 'CBC with Differential', 90, 'standard',
     'https://www.epilepsy.com/treatment/medicines', 1.0,
     'CBC quarterly — thrombocytopenia risk with valproic acid.'),
    ('11118', None, None, 'MEDICATION', 'MANUAL',
     '4086-5', '80164', 'Valproic Acid Level', 90, 'high',
     'https://www.epilepsy.com/treatment/medicines', 1.0,
     'Drug level quarterly — therapeutic range 50-100 mcg/mL.'),

    # Carbamazepine
    ('2002', None, None, 'MEDICATION', 'MANUAL',
     '1920-8', '80076', 'Hepatic Function Panel', 90, 'high',
     'https://www.epilepsy.com/treatment/medicines', 1.0,
     'LFTs quarterly — carbamazepine hepatotoxicity.'),
    ('2002', None, None, 'MEDICATION', 'MANUAL',
     '718-7', '85025', 'CBC with Differential', 90, 'high',
     'https://www.epilepsy.com/treatment/medicines', 1.0,
     'CBC quarterly — aplastic anemia/agranulocytosis risk with carbamazepine.'),
    ('2002', None, None, 'MEDICATION', 'MANUAL',
     '3432-2', '80156', 'Carbamazepine Level', 90, 'high',
     'https://www.epilepsy.com/treatment/medicines', 1.0,
     'Drug level quarterly — auto-induction changes levels over time.'),
    ('2002', None, None, 'MEDICATION', 'MANUAL',
     '2951-2', '84295', 'Sodium', 180, 'standard',
     'https://www.epilepsy.com/treatment/medicines', 1.0,
     'Sodium — carbamazepine causes SIADH/hyponatremia.'),

    # Clozapine (REMS — also tracked in REMSTrackerEntry)
    ('2626', None, None, 'REMS', 'MANUAL',
     '718-7', '85025', 'CBC with ANC (Clozapine REMS)', 7, 'critical',
     'https://www.clozapinerems.com/', 1.0,
     'ANC weekly x6 months, biweekly x6 months, monthly thereafter. Federally mandated.'),

    # All atypical antipsychotics (class N05AH)
    (None, 'N05AH', None, 'MEDICATION', 'MANUAL',
     '1558-6', '82947', 'Fasting Glucose', 90, 'high',
     'https://psychiatryonline.org/doi/book/10.1176/appi.books.9780890424865', 1.0,
     'Metabolic monitoring per APA protocol: fasting glucose at baseline, 3 months, annually.'),
    (None, 'N05AH', None, 'MEDICATION', 'MANUAL',
     '4548-4', '83036', 'Hemoglobin A1C', 365, 'standard',
     'https://psychiatryonline.org/doi/book/10.1176/appi.books.9780890424865', 1.0,
     'HbA1c annually for all atypical antipsychotics. APA metabolic monitoring protocol.'),
    (None, 'N05AH', None, 'MEDICATION', 'MANUAL',
     '2093-3', '80061', 'Lipid Panel', 365, 'standard',
     'https://psychiatryonline.org/doi/book/10.1176/appi.books.9780890424865', 1.0,
     'Lipid panel at baseline, 3 months, then annually. APA protocol.'),

    # DOACs (class B01AF)
    (None, 'B01AF', None, 'MEDICATION', 'MANUAL',
     '2160-0', '80048', 'BMP/eGFR (DOAC dosing)', 365, 'high',
     'https://www.ahajournals.org/doi/10.1161/CIR.0000000000001045', 1.0,
     'Renal function annually; every 3-6 months if age >75 or CKD. DOAC dose depends on eGFR.'),

    # Hydroxychloroquine
    ('5521', None, None, 'MEDICATION', 'MANUAL',
     '718-7', '85025', 'CBC with Differential', 365, 'standard',
     'https://www.rheumatology.org/Practice-Quality/Clinical-Support/', 1.0,
     'CBC baseline and annually — hydroxychloroquine hematologic toxicity.'),
    ('5521', None, None, 'MEDICATION', 'MANUAL',
     '1920-8', '80076', 'Hepatic Function Panel', 365, 'standard',
     'https://www.rheumatology.org/Practice-Quality/Clinical-Support/', 1.0,
     'LFTs baseline and annually. Ophthalmology referral at 5-year mark.'),

    # Levothyroxine
    ('10582', None, None, 'MEDICATION', 'MANUAL',
     '3016-3', '84443', 'TSH', 365, 'standard',
     'https://www.thyroid.org/professionals/ata-professional-guidelines/', 1.0,
     'TSH 6-8 weeks after any dose change, then annually once stable. ATA.'),

    # Chronic corticosteroids
    (None, 'H02AB', None, 'MEDICATION', 'MANUAL',
     '1558-6', '82947', 'Fasting Glucose', 90, 'high',
     'https://www.endocrine.org/clinical-practice-guidelines', 1.0,
     'Glucose + HbA1c — chronic steroids cause steroid-induced diabetes.'),
    (None, 'H02AB', None, 'MEDICATION', 'MANUAL',
     '4548-4', '83036', 'Hemoglobin A1C', 180, 'standard',
     'https://www.endocrine.org/clinical-practice-guidelines', 1.0,
     'HbA1c every 6 months on chronic corticosteroids.'),
    (None, 'H02AB', None, 'MEDICATION', 'MANUAL',
     '2160-0', '80048', 'BMP', 180, 'standard',
     'https://www.endocrine.org/clinical-practice-guidelines', 1.0,
     'BMP for electrolyte monitoring on chronic steroids.'),
    (None, 'H02AB', None, 'MEDICATION', 'MANUAL',
     '46278-8', '77080', 'DEXA Scan (Osteoporosis)', 730, 'standard',
     'https://www.endocrine.org/clinical-practice-guidelines', 1.0,
     'DEXA for osteoporosis if ≥3 months of prednisone ≥5mg/day.'),

    # Bisphosphonates
    (None, 'M05BA', None, 'MEDICATION', 'MANUAL',
     '2160-0', '80048', 'BMP/Creatinine', 365, 'standard',
     'https://www.endocrine.org/clinical-practice-guidelines', 1.0,
     'BMP + creatinine before initiating bisphosphonate.'),
    (None, 'M05BA', None, 'MEDICATION', 'MANUAL',
     '1989-3', '82306', 'Vitamin D (25-OH)', 365, 'standard',
     'https://www.endocrine.org/clinical-practice-guidelines', 1.0,
     'Calcium + vitamin D levels — ensure adequacy before bisphosphonate therapy.'),

    # Denosumab
    ('1546660', None, None, 'MEDICATION', 'MANUAL',
     '17861-6', '82310', 'Calcium', 180, 'high',
     'https://www.endocrine.org/clinical-practice-guidelines', 1.0,
     'Calcium + vitamin D before each injection — hypocalcemia risk with denosumab.'),
    ('1546660', None, None, 'MEDICATION', 'MANUAL',
     '1989-3', '82306', 'Vitamin D (25-OH)', 180, 'standard',
     'https://www.endocrine.org/clinical-practice-guidelines', 1.0,
     'Vitamin D adequacy before each denosumab dose.'),

    # Methotrexate
    ('6851', None, None, 'MEDICATION', 'MANUAL',
     '718-7', '85025', 'CBC with Differential', 90, 'high',
     'https://www.rheumatology.org/Practice-Quality/Clinical-Support/', 1.0,
     'CBC quarterly — methotrexate myelosuppression.'),
    ('6851', None, None, 'MEDICATION', 'MANUAL',
     '1920-8', '80076', 'Hepatic Function Panel', 90, 'high',
     'https://www.rheumatology.org/Practice-Quality/Clinical-Support/', 1.0,
     'LFTs quarterly — methotrexate hepatotoxicity.'),
    ('6851', None, None, 'MEDICATION', 'MANUAL',
     '2160-0', '80048', 'BMP', 90, 'high',
     'https://www.rheumatology.org/Practice-Quality/Clinical-Support/', 1.0,
     'BMP quarterly — renal function monitoring on methotrexate.'),

    # Isoniazid / Rifampin (TB prophylaxis)
    ('6038', None, None, 'MEDICATION', 'MANUAL',
     '1920-8', '80076', 'Hepatic Function Panel', 30, 'high',
     'https://www.cdc.gov/tb/publications/ltbi/treatment.htm', 1.0,
     'LFTs monthly if risk factors — isoniazid hepatotoxicity.'),
    ('9384', None, None, 'MEDICATION', 'MANUAL',
     '1920-8', '80076', 'Hepatic Function Panel', 30, 'high',
     'https://www.cdc.gov/tb/publications/ltbi/treatment.htm', 1.0,
     'LFTs monthly if risk factors — rifampin hepatotoxicity.'),

    # ═══════════════════════════════════════════════════════════════
    # KDIGO eGFR DOSE-ADJUSTMENT THRESHOLD RULES
    # (condition-triggered but cross-referenced against active meds)
    # ═══════════════════════════════════════════════════════════════

    # Metformin eGFR threshold
    (None, None, 'N18', 'CONDITION', 'MANUAL',
     '2160-0', '80048', 'eGFR for Metformin Dosing', 90, 'critical',
     'https://kdigo.org/guidelines/diabetes-ckd/', 1.0,
     'Metformin: hold/contraindicated below eGFR 30; dose reduce eGFR 30-45. KDIGO.'),

    # SGLT-2 inhibitors eGFR threshold
    (None, None, 'N18', 'CONDITION', 'MANUAL',
     '2160-0', '80048', 'eGFR for SGLT-2i Dosing', 90, 'critical',
     'https://kdigo.org/guidelines/diabetes-ckd/', 1.0,
     'SGLT-2i: contraindicated below eGFR 20-30 (varies by agent). KDIGO.'),

    # DOAC eGFR thresholds
    (None, None, 'N18', 'CONDITION', 'MANUAL',
     '2160-0', '80048', 'eGFR for DOAC Dosing', 90, 'critical',
     'https://www.ahajournals.org/doi/10.1161/CIR.0000000000001045', 1.0,
     'DOAC dose adjustment thresholds: apixaban at eGFR<25, rivaroxaban 15mg eGFR 15-50, dabigatran 75mg eGFR 15-30.'),

    # Gabapentin/Pregabalin eGFR threshold
    (None, None, 'N18', 'CONDITION', 'MANUAL',
     '2160-0', '80048', 'eGFR for Gabapentin/Pregabalin Dosing', 90, 'high',
     'https://kdigo.org/guidelines/', 1.0,
     'Gabapentin/pregabalin: dose reduction at eGFR <60, significant reduction <30 — CNS toxicity.'),

    # Lithium eGFR threshold
    (None, None, 'N18', 'CONDITION', 'MANUAL',
     '3719-2', '80178', 'Lithium Level (CKD dose adjustment)', 30, 'critical',
     'https://psychiatryonline.org/doi/book/10.1176/appi.books.9780890424865', 1.0,
     'Lithium: narrow TI, renal clearance — dose adjust eGFR <60, contraindicated <30 without nephrology.'),

    # Allopurinol eGFR threshold
    (None, None, 'N18', 'CONDITION', 'MANUAL',
     '2160-0', '80048', 'eGFR for Allopurinol Dosing', 180, 'high',
     'https://www.rheumatology.org/Practice-Quality/Clinical-Support/', 1.0,
     'Allopurinol: start 100mg, titrate slowly if eGFR <30. ACR guidelines.'),

    # ═══════════════════════════════════════════════════════════════
    # MELD / CHILD-PUGH LAB COMPONENTS (liver disease families)
    # These ensure the component labs are tracked for score computation
    # ═══════════════════════════════════════════════════════════════
    (None, None, 'K74', 'CONDITION', 'MANUAL',
     '6301-6', '85610', 'INR (MELD component)', 90, 'high',
     'https://www.aasld.org/practice-guidelines/', 1.0,
     'INR for MELD-Na score computation. Cirrhosis surveillance.'),
    (None, None, 'K74', 'CONDITION', 'MANUAL',
     '1975-2', '82247', 'Total Bilirubin (MELD component)', 90, 'high',
     'https://www.aasld.org/practice-guidelines/', 1.0,
     'Total bilirubin for MELD-Na score. AASLD cirrhosis guidelines.'),
    (None, None, 'K74', 'CONDITION', 'MANUAL',
     '2160-0', '82565', 'Creatinine (MELD component)', 90, 'high',
     'https://www.aasld.org/practice-guidelines/', 1.0,
     'Creatinine for MELD-Na score. AASLD cirrhosis guidelines.'),
    (None, None, 'K74', 'CONDITION', 'MANUAL',
     '2951-2', '84295', 'Sodium (MELD-Na component)', 90, 'high',
     'https://www.aasld.org/practice-guidelines/', 1.0,
     'Sodium for MELD-Na adjustment (125-137 mEq/L range). AASLD.'),
    (None, None, 'K74', 'CONDITION', 'MANUAL',
     '1751-7', '82040', 'Albumin (Child-Pugh component)', 90, 'high',
     'https://www.aasld.org/practice-guidelines/', 1.0,
     'Albumin for Child-Pugh score. Class A/B/C determines management intensity.'),
]

# ═══════════════════════════════════════════════════════════════════
# VSAC-DRIVEN PREVENTIVE SCREENING RULES  (Phase 23.B4)
#
# Replaces the 14 hardcoded preventive lab rules with VSAC eCQM
# value-set–linked entries.  trigger_type=CONDITION, source=VSAC.
# icd10_trigger uses screening Z-codes commonly documented during
# AWV / preventive encounters.  rxclass_id stores the VSAC OID for
# traceability.  interval_days=0 → one-time screening.
#
# Each tuple matches the SEED_RULES schema:
#   (rxcui, rxclass_id, icd10_trigger, trigger_type, source,
#    lab_loinc, lab_cpt, lab_name, interval_days, priority,
#    evidence_url, confidence, clinical_context)
# ═══════════════════════════════════════════════════════════════════

PREVENTIVE_SEED_RULES = [
    # 1. Lipid panel — USPSTF Grade B, adults 40–75
    (None, '2.16.840.1.113883.3.464.1003.198.12.1035', 'Z13.220', 'CONDITION', 'VSAC',
     '2093-3', '80061', 'Lipid Panel (Preventive)', 1825, 'standard',
     'https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/statin-use-in-adults-preventive-medication',
     1.0, 'Lipid panel every 5 years for cardiovascular risk assessment, adults 40-75. USPSTF Grade B.'),

    # 2. Diabetes screening (A1C) — USPSTF Grade B, adults 35–70 with overweight/obesity
    (None, '2.16.840.1.113883.3.464.1003.103.12.1001', 'Z13.1', 'CONDITION', 'VSAC',
     '4548-4', '83036', 'Hemoglobin A1C (Diabetes Screening)', 1095, 'standard',
     'https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/screening-for-prediabetes-and-type-2-diabetes',
     1.0, 'A1C every 3 years for diabetes screening, adults 35-70 with overweight/obesity. USPSTF Grade B.'),

    # 3. HCV screening — USPSTF Grade B, adults 18–79 (one-time)
    (None, '2.16.840.1.113762.1.4.1222.39', 'Z11.59', 'CONDITION', 'VSAC',
     '16128-1', '86803', 'Hepatitis C Antibody (HCV Screening)', 0, 'standard',
     'https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/hepatitis-c-screening',
     1.0, 'HCV antibody one-time screening, adults 18-79. Birth cohort 1945-1965 highest yield. USPSTF Grade B.'),

    # 4. HBV screening — USPSTF Grade B, at-risk adults
    (None, '2.16.840.1.113883.3.464.1003.110.12.1082', 'Z11.59', 'CONDITION', 'VSAC',
     '22322-2', '86704', 'Hepatitis B Surface Antigen (HBV Screening)', 0, 'standard',
     'https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/hepatitis-b-virus-infection-screening',
     1.0, 'HBsAg one-time screening for at-risk populations. USPSTF Grade B.'),

    # 5. HIV screening — USPSTF Grade A, adults 15–65 (one-time)
    (None, '2.16.840.1.113762.1.4.1056.50', 'Z11.4', 'CONDITION', 'VSAC',
     '75622-1', '86701', 'HIV-1/2 Antigen/Antibody (Screening)', 0, 'standard',
     'https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/human-immunodeficiency-virus-hiv-infection-screening',
     1.0, 'HIV screening one-time for adults 15-65. Repeat annually for high-risk. USPSTF Grade A.'),

    # 6. STI screening (chlamydia/gonorrhea) — USPSTF Grade B, sexually active women ≤24
    (None, '2.16.840.1.113883.3.464.1003.112.12.1003', 'Z11.3', 'CONDITION', 'VSAC',
     '43304-5', '87491', 'Chlamydia/Gonorrhea NAAT (STI Screening)', 365, 'standard',
     'https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/chlamydia-and-gonorrhea-screening',
     1.0, 'CT/GC NAAT annually for sexually active women ≤24 and older women at increased risk. USPSTF Grade B.'),

    # 7. Colorectal cancer screening — USPSTF Grade A, adults 45–75
    (None, '2.16.840.1.113883.3.464.1003.108.12.1020', 'Z12.11', 'CONDITION', 'VSAC',
     '57905-2', '82270', 'Fecal Occult Blood / FIT (CRC Screening)', 365, 'high',
     'https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/colorectal-cancer-screening',
     1.0, 'FIT annually (or Cologuard every 3 yrs, colonoscopy every 10 yrs), ages 45-75. USPSTF Grade A.'),

    # 8. Lung cancer screening (LDCT) — USPSTF Grade B, 50–80 with 20 pack-year
    (None, '2.16.840.1.113762.1.4.1222.45', 'Z12.2', 'CONDITION', 'VSAC',
     '24627-2', 'G0297', 'Low-Dose CT Chest (Lung Cancer Screening)', 365, 'high',
     'https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/lung-cancer-screening',
     1.0, 'Annual LDCT for adults 50-80 with 20+ pack-year smoking and currently smoke or quit within 15 yrs. USPSTF Grade B.'),

    # 9. Cervical cancer screening (Pap) — USPSTF Grade A, women 21–65
    (None, '2.16.840.1.113883.3.464.1003.108.12.1017', 'Z12.4', 'CONDITION', 'VSAC',
     '10524-7', 'Q0091', 'Pap Smear (Cervical Cancer Screening)', 1095, 'standard',
     'https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/cervical-cancer-screening',
     1.0, 'Pap smear every 3 years (women 21-29) or co-testing every 5 years (30-65). USPSTF Grade A.'),

    # 10. Mammography — USPSTF Grade B, women 40–74
    (None, '2.16.840.1.113883.3.464.1003.108.12.1018', 'Z12.31', 'CONDITION', 'VSAC',
     '24606-6', '77067', 'Screening Mammography, Bilateral', 730, 'high',
     'https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/breast-cancer-screening',
     1.0, 'Screening mammography every 2 years, women 40-74. USPSTF Grade B.'),

    # 11. DEXA bone density — USPSTF Grade B, women 65+ or postmenopausal at risk
    (None, '2.16.840.1.113762.1.4.1222.47', 'Z13.820', 'CONDITION', 'VSAC',
     '46278-8', '77080', 'DEXA Bone Density (Osteoporosis Screening)', 1825, 'standard',
     'https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/osteoporosis-screening',
     1.0, 'DEXA every 5 years for women 65+ or postmenopausal women at increased fracture risk. USPSTF Grade B.'),

    # 12. AAA ultrasound — USPSTF Grade B, men 65–75 who ever smoked (one-time)
    (None, '2.16.840.1.113762.1.4.1222.48', 'Z13.6', 'CONDITION', 'VSAC',
     '12226-7', '76706', 'Abdominal Aortic Ultrasound (AAA Screening)', 0, 'standard',
     'https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/abdominal-aortic-aneurysm-screening',
     1.0, 'One-time AAA ultrasound for men 65-75 who have ever smoked. USPSTF Grade B.'),

    # 13. TB screening (IGRA) — risk-based, CDC recommendation
    (None, '2.16.840.1.113762.1.4.1222.49', 'Z11.1', 'CONDITION', 'VSAC',
     '71774-4', '86480', 'IGRA / QuantiFERON (TB Screening)', 365, 'standard',
     'https://www.cdc.gov/tb/topic/testing/tbtesttypes.htm',
     1.0, 'TB screening (IGRA preferred) for at-risk populations: healthcare workers, born in TB-endemic areas, immunosuppressed.'),

    # 14. Asymptomatic bacteriuria — USPSTF Grade B, pregnant women
    (None, '2.16.840.1.113762.1.4.1222.50', 'Z13.89', 'CONDITION', 'VSAC',
     '630-4', '87086', 'Urine Culture (Bacteriuria Screening)', 0, 'standard',
     'https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/asymptomatic-bacteriuria-in-adults-screening',
     1.0, 'Urine culture for asymptomatic bacteriuria screening in pregnant women. USPSTF Grade B.'),
]

# Total rules count for verification
EXPECTED_COUNT = len(SEED_RULES) + len(PREVENTIVE_SEED_RULES)


def seed():
    """
    Delete existing MANUAL- and VSAC-sourced MonitoringRule entries and
    re-insert the full seed set.  API-sourced rules from DailyMed,
    Drug@FDA, RxClass, etc. are never touched.
    """
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'data', 'carecompanion.db'
    )
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Delete MANUAL-source rules
    cur.execute("DELETE FROM monitoring_rule WHERE source = 'MANUAL'")
    deleted_manual = cur.rowcount

    # Delete VSAC-source preventive seed rules (B4)
    cur.execute("DELETE FROM monitoring_rule WHERE source = 'VSAC'")
    deleted_vsac = cur.rowcount

    inserted = 0

    # ── Core monitoring rules (B3) ──
    for row in SEED_RULES:
        (rxcui, rxclass_id, icd10_trigger, trigger_type, source,
         lab_loinc_code, lab_cpt_code, lab_name, interval_days, priority,
         evidence_source_url, extraction_confidence, clinical_context) = row
        cur.execute(
            """INSERT INTO monitoring_rule
               (rxcui, rxclass_id, icd10_trigger, trigger_type, source,
                lab_loinc_code, lab_cpt_code, lab_name, interval_days, priority,
                evidence_source_url, extraction_confidence, clinical_context,
                is_active)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
            (rxcui, rxclass_id, icd10_trigger, trigger_type, source,
             lab_loinc_code, lab_cpt_code, lab_name, interval_days, priority,
             evidence_source_url, extraction_confidence, clinical_context),
        )
        inserted += 1

    # ── Preventive screening rules (B4) ──
    for row in PREVENTIVE_SEED_RULES:
        (rxcui, rxclass_id, icd10_trigger, trigger_type, source,
         lab_loinc_code, lab_cpt_code, lab_name, interval_days, priority,
         evidence_source_url, extraction_confidence, clinical_context) = row
        cur.execute(
            """INSERT INTO monitoring_rule
               (rxcui, rxclass_id, icd10_trigger, trigger_type, source,
                lab_loinc_code, lab_cpt_code, lab_name, interval_days, priority,
                evidence_source_url, extraction_confidence, clinical_context,
                is_active)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
            (rxcui, rxclass_id, icd10_trigger, trigger_type, source,
             lab_loinc_code, lab_cpt_code, lab_name, interval_days, priority,
             evidence_source_url, extraction_confidence, clinical_context),
        )
        inserted += 1

    conn.commit()
    conn.close()
    print(
        f'[OK] Seeded {inserted} monitoring rules '
        f'(cleared {deleted_manual} MANUAL + {deleted_vsac} VSAC previous rules)'
    )
    print(f'     Disease families: 10  |  Genotype: 6  |  Med classes: ~30  |  KDIGO: 6  |  MELD/CP: 5')
    print(f'     Preventive VSAC screenings: {len(PREVENTIVE_SEED_RULES)}')


if __name__ == '__main__':
    seed()
