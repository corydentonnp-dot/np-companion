# CareCompanion -- Test Data Catalog

> **Generated:** 03-24-26
> **Purpose:** Documents all test data available for QA sessions, including demo patients, seed data, and edge cases.
> **Source:** `scripts/seed_test_data.py` creates all demo data. Run via `venv\Scripts\python.exe scripts/seed_test_data.py`.

---

## Demo Patients (MRN 90001-90035)

### Full Patient Roster

| MRN | Name | Age | Sex | Insurer | Key Conditions |
|-----|------|-----|-----|---------|----------------|
| 90001 | Margaret Wilson | 67 | F | Medicare | HTN, T2DM, HLD, osteoporosis (AWV, CCM) |
| 90002 | Robert Thompson | 65 | M | Medicare | COPD, HTN, nicotine dependence (lung LDCT, AAA) |
| 90003 | Maria Garcia | 35 | F | Commercial | Anxiety, morbid obesity (cervical pap, diabetes screen) |
| 90004 | James Chen | 55 | M | Commercial | T2DM w/ CKD3, HTN (CCM, chronic monitoring, RPM) |
| 90005 | Patricia Davis | 70 | F | Medicare Adv | CHF, AFib, HTN, depression (CCM, BHI) |
| 90006 | David Williams | 80 | M | Medicare | Dementia, HTN, BPH, OA (cognitive, AWV) |
| 90007 | Linda Brown | 43 | F | Commercial | Hypothyroid, migraine (mammogram, cervical pap) |
| 90008 | Michael Johnson | 50 | M | Commercial | Alcohol use disorder, NASH, morbid obesity |
| 90009 | Jennifer Martinez | 25 | F | Medicaid | Asthma, anxiety (cervical pap, HIV, depression) |
| 90010 | William Anderson | 75 | M | Medicare | T2DM, neuropathy, active smoker (lung LDCT, tobacco) |
| 90011 | Susan Taylor | 37 | F | Commercial | MDD, morbid obesity, prediabetes (BHI) |
| 90012 | Thomas Harris | 60 | M | Commercial | Gout, HTN, HLD (colonoscopy, lipid) |
| 90013 | Barbara Clark | 85 | F | Medicare | CHF, CKD4, anemia (CCM complex) |
| 90014 | Christopher Lee | 10 | M | Medicaid | PEDIATRIC -- ADHD, asthma (well-child, vaccines) |
| 90015 | Elizabeth White | 53 | F | Medicare Adv | RA, osteoporosis, depression (BHI, CCM) |
| 90016 | Daniel Robinson | 57 | M | Commercial | Sleep apnea, morbid obesity (RPM, obesity) |
| 90017 | Nancy Walker | 40 | F | Commercial | Bipolar, GERD (BHI, CoCM, mammogram) |
| 90018 | Matthew Hall | 70 | M | Medicare | CHF, T2DM, AFib (TCM post-hospital) |
| 90019 | Karen Young | 33 | F | Commercial | Healthy -- on OCP only (STI, cervical pap) |
| 90020 | Steven King | 47 | M | Commercial | Chronic back pain, smoker, obese (tobacco, obesity) |
| 90021 | Dorothy Wright | 77 | F | Medicare | Parkinson's, depression, osteoporosis (CCM, BHI, cognitive) |
| 90022 | Andrew Lopez | 17 | M | Medicaid | PEDIATRIC -- T1DM (HIV screen 15+, vaccines) |
| 90023 | Carol Scott | 63 | F | Commercial | Breast cancer history, anxiety (high-priority mammogram) |
| 90024 | Mark Green | 73 | M | Medicare | COMPLEX -- ESRD, T2DM, CKD, anemia (CCM, RPM, prolonged) |
| 90025 | Sandra Adams | 45 | F | Medicare Adv | SLE, CKD2, HTN (CCM, colonoscopy) |
| 90026 | Paul Mitchell | 38 | M | Commercial | T2DM, MDD, SDOH: homelessness, food insecurity |
| 90027 | Angela Turner | 30 | F | Medicaid | Opioid dependence, Hep C, HIV+ (substance use) |
| 90028 | Kenneth Phillips | 82 | M | Medicare | Alzheimer's, T2DM, HTN (cognitive, ACP) |
| 90029 | Jessica Campbell | 27 | F | Commercial | FALSE-POSITIVE CONTROL -- healthy, acute URI only |
| 90030 | George Evans | 67 | M | Medicare | Prostate cancer, HTN, BPH (AWV) |
| 90031 | Betty Stewart | 73 | F | Medicare Adv | HTN, anxiety (telehealth, G2211, E/M add-ons) |
| 90032 | Edward Morgan | 42 | M | Commercial | CKD3a, HTN, gout (chronic monitoring) |
| 90033 | Lily Phillips | 7 | F | Medicaid | PEDIATRIC -- asthma, atopic dermatitis |
| 90034 | Richard Cooper | 55 | M | Medicare Adv | MOST COMPLEX -- CHF, COPD, T2DM, CKD3, obesity |
| 90035 | Helen Bailey | 79 | F | Medicare | Osteoporosis, HTN, hypothyroid (AWV, CCM) |

**Legacy test patient:** MRN 62815, TEST TEST, DOB 10/1/1980, 45F

---

## Payer Distribution

| Payer Type | Count | MRNs |
|-----------|-------|------|
| Medicare | 10 | 90001, 90002, 90006, 90010, 90013, 90018, 90024, 90028, 90030, 90035 |
| Commercial | 11 | 90003, 90004, 90007, 90008, 90012, 90016, 90019, 90020, 90023, 90029, 90032 |
| Medicaid | 5 | 90009, 90014, 90022, 90027, 90033 |
| Medicare Advantage | 5 | 90005, 90015, 90025, 90031, 90034 |

---

## Edge-Case Patients for Targeted Testing

| MRN | Use Case | Why It Matters |
|-----|----------|----------------|
| 90029 | False-positive control | Healthy patient with acute URI -- no billing detector should trigger chronic codes |
| 90024 | Most complex male | ESRD, 6 meds, 4 severe diagnoses -- tests billing stacking, CCM, RPM |
| 90034 | Highest chronic burden | 5 chronic conditions, 6 meds -- tests max billing opportunity count |
| 90026 | SDOH screening | Homelessness + food insecurity Z-codes -- tests SDOH detector |
| 90027 | Infectious disease | HIV+, Hep C, OUD on MAT -- tests STI, substance use detectors |
| 90014 | Pediatric (10y) | Well-child, vaccine admin -- tests pediatric detector |
| 90022 | Pediatric (17y) | T1DM, HIV screen age 15+ -- tests adolescent screening |
| 90033 | Pediatric (7y) | Asthma, atopic dermatitis -- tests youngest pediatric |
| 90028 | Cognitive/ACP | Alzheimer's -- tests cognitive assessment + advance care planning |
| 90018 | TCM trigger | Post-hospitalization -- tests transitional care management timing |
| 90031 | Telehealth/G2211 | Telehealth + E/M add-ons -- tests G2211 and modifier logic |

---

## Billing Detector Coverage

All 27 detectors are triggered by at least one demo patient:

| Detector | Primary Test MRNs |
|----------|-------------------|
| AWV | 90001, 90002, 90006, 90010, 90021, 90030, 90035 |
| CCM | 90001, 90004, 90005, 90013, 90015, 90021, 90024, 90025, 90034 |
| BHI | 90005, 90011, 90015, 90017, 90021, 90026 |
| CoCM | 90017 |
| TCM | 90018 |
| RPM | 90004, 90016, 90024, 90034 |
| G2211 | 90031 |
| Tobacco | 90002, 90010, 90020 |
| Alcohol | 90008 |
| Obesity | 90003, 90008, 90016, 90020 |
| Cognitive | 90006, 90021, 90028 |
| ACP | 90028 |
| SDOH | 90026 |
| STI | 90019, 90027 |
| Pediatric | 90014, 90022, 90033 |
| Screening | 90003, 90009, 90019 |
| Preventive | 90007, 90012, 90023 |
| Telehealth | 90031 |
| Prolonged | 90021, 90024, 90035 |
| EMAddons | 90031 |
| VaccineAdmin | 90014, 90022, 90033 |
| ChronicMonitoring | 90004, 90032 |
| CareGaps | all patients with missing screenings |
| Counseling | 90003, 90020 |
| Procedures | various |
| Calculator | various |
| Misc | various |

---

## Pre-Cached API Data

Drug pricing data is pre-seeded so pricing tests work without live APIs:

| Source | Drugs | Status |
|--------|-------|--------|
| Cost Plus | lisinopril ($3.60), metformin ($3.90), atorvastatin ($4.50), amlodipine ($3.00), buspirone ($5.40) | Cached |
| GoodRx | alendronate ($38), tiotropium ($350), eliquis ($580), jardiance ($560), ozempic ($935) | Cached |
| Assistance | tiotropium (Boehringer), eliquis (BMS), ozempic (Novo Nordisk) | Cached |

---

## Data Seeded Per Patient

Each demo patient gets these model rows via `store_parsed_summary()`:
- `PatientRecord` with demographics, insurer, PCP
- `PatientVitals` with height, weight, BP, BMI
- `PatientMedication` with all condition-appropriate meds
- `PatientDiagnosis` with ICD-10 codes
- `PatientAllergy` (patient-specific)
- `PatientImmunization` (age-appropriate vaccine history)

Additional seed data:
- `BillingOpportunity` rows for each patient (from billing engine evaluation)
- `CareGap` rows for all 20+ USPSTF rules
- `Schedule` rows for some patients (daily appointments)
- `CCMEnrollment` for patients with 2+ chronic conditions
- `TCMWatchEntry` for MRN 90018
- `MonitoringSchedule` for patients on monitored medications
- `BonusTracker` initial row

---

## How to Reseed

```powershell
# Full reseed (drops and recreates all demo data)
venv\Scripts\python.exe scripts/seed_test_data.py

# Verify seed worked
venv\Scripts\python.exe -c "from app import create_app; app = create_app(); ctx = app.app_context(); ctx.push(); from models.patient import PatientRecord; print(f'Patients: {PatientRecord.query.count()}')"
```
