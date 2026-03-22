# CareCompanion — Billing Capture Engine: Master Implementation Prompt

**Context:** CareCompanion is a locally-hosted Flask + SQLAlchemy + SQLite clinical workflow tool for a family practice office in Chesterfield, Virginia. It integrates with Amazing Charts EHR (v12.3.1) via FHIR Clinical Summary XML exports and a NetPractice/WebPractice schedule scraper. The application runs on the provider's workstation at `localhost:5000` with a background agent on `localhost:5001`. See `README.md`, `ABOUT.md`, `PROJECT_STATUS.md`, and `init.prompt.md` for full architecture and coding conventions.

**Goal:** Build a Billing Capture Engine that analyzes patient data at pre-visit, during-visit, and post-visit to detect every billable add-on, preventive service, screening, immunization, care management opportunity, and modifier that the practice is eligible to bill but may not be capturing. The engine must surface these as actionable alerts in the provider dashboard with documentation checklists.

---

## Architecture Requirements

### Data Sources Available

- **Patient Demographics:** Age, sex, DOB, insurance/payer type (Medicare Part B, Medicare Advantage, Medicaid, private commercial) — from AC Clinical Summary XML
- **Problem List:** Active ICD-10 codes — from AC Clinical Summary XML
- **Medication List:** Active medications with drug name, dose, frequency — from AC Clinical Summary XML
- **Lab Results:** Result values, dates, LOINC codes — from AC Clinical Summary XML
- **Immunization Records:** Vaccine name, date administered, CVX codes — from AC Clinical Summary XML
- **Vitals:** BMI, BP, weight, height — from AC Clinical Summary XML
- **Social History:** Tobacco use, alcohol use, substance use, sexual activity — from AC Clinical Summary XML (where documented)
- **Visit History:** CPT codes billed, dates of service, visit types — from AC billing data or CareCompanion encounter log
- **Appointment Schedule:** Today's patients, appointment type (new, established, preventive, acute, follow-up) — from NetPractice scraper
- **Encounter Timer:** Start/stop time tracking per visit — from CareCompanion

### Models to Create or Extend

Create a `BillingOpportunity` model and related tables:

```python
class BillingOpportunity(db.Model):
    """Detected billing opportunity for a patient encounter."""
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    encounter_id = db.Column(db.Integer, db.ForeignKey('encounter.id'), nullable=True)
    category = db.Column(db.String(50), nullable=False)  # e.g., 'AWV', 'SCREENING', 'IMMUNIZATION', 'CCM', 'ADD_ON'
    opportunity_code = db.Column(db.String(20), nullable=False)  # internal identifier
    cpt_codes = db.Column(db.String(200), nullable=False)  # comma-separated CPT/HCPCS
    description = db.Column(db.String(500), nullable=False)
    estimated_revenue = db.Column(db.Float, nullable=True)
    payer_type = db.Column(db.String(20), nullable=False)  # 'medicare', 'private', 'medicaid', 'all'
    modifier = db.Column(db.String(10), nullable=True)  # e.g., '33', '25'
    priority = db.Column(db.String(10), nullable=False)  # 'high', 'medium', 'low'
    status = db.Column(db.String(20), default='detected')  # 'detected', 'accepted', 'dismissed', 'billed'
    detection_reason = db.Column(db.Text, nullable=False)  # human-readable explanation
    documentation_checklist = db.Column(db.Text, nullable=True)  # JSON array of required documentation items
    detected_at = db.Column(db.DateTime, default=func.now())
    actioned_at = db.Column(db.DateTime, nullable=True)
    actioned_by = db.Column(db.String(100), nullable=True)

class BillingRule(db.Model):
    """Configurable billing detection rule."""
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    opportunity_code = db.Column(db.String(20), nullable=False, unique=True)
    description = db.Column(db.String(500), nullable=False)
    cpt_codes = db.Column(db.String(200), nullable=False)
    payer_types = db.Column(db.String(100), nullable=False)  # JSON array
    estimated_revenue = db.Column(db.Float, nullable=True)
    modifier = db.Column(db.String(10), nullable=True)
    rule_logic = db.Column(db.Text, nullable=False)  # JSON rule definition
    documentation_checklist = db.Column(db.Text, nullable=True)  # JSON array
    is_active = db.Column(db.Boolean, default=True)
    frequency_limit = db.Column(db.String(50), nullable=True)  # 'annual', 'monthly', 'once', 'per_visit', 'per_pregnancy'
    last_updated = db.Column(db.DateTime, default=func.now())
```

### Engine Architecture

Create a `billing_engine/` package:

```
billing_engine/
├── __init__.py
├── engine.py              ← Main orchestrator: runs all detectors against a patient
├── detectors/
│   ├── __init__.py
│   ├── awv.py             ← Annual Wellness Visit detection
│   ├── em_addons.py       ← G2211, 99417, prolonged services, modifier 25
│   ├── ccm.py             ← Chronic Care Management (99490, 99491, 99439, PCM)
│   ├── tcm.py             ← Transitional Care Management (99495, 99496)
│   ├── bhi.py             ← Behavioral Health Integration (99484, 99492-99494)
│   ├── screenings.py      ← All screening instruments (PHQ-9, GAD-7, AUDIT-C, etc.)
│   ├── preventive_labs.py ← Preventive lab screenings (lipid, A1C, HCV, HIV, STI, CRC, etc.)
│   ├── immunizations.py   ← Immunization gap detection (all ACIP-recommended vaccines)
│   ├── counseling.py      ← Counseling & education codes (obesity, tobacco, MNT, CVD IBT, etc.)
│   ├── care_mgmt.py       ← RPM, RTM, MDPP, care plan oversight
│   ├── procedures.py      ← In-office procedure add-ons (EKG, spirometry, POCT, injections, venipuncture, neb)
│   ├── chronic_monitoring.py  ← Chronic disease lab monitoring (A1C, lipid, TSH, renal, CBC, INR, LFTs, UACR, Vit D)
│   ├── telehealth.py      ← Telephone E/M, online digital E/M, interprofessional consults
│   ├── sdoh.py            ← SDOH screening, IPV screening, HRA
│   ├── pediatric.py       ← Bright Futures well-child, lead, anemia, dyslipidemia, fluoride varnish, vision, hearing
│   └── misc.py            ← After-hours premium, modifier 25 prompts, PrEP, folic acid, statin counseling, etc.
├── rules.py               ← Rule definitions (seed data for BillingRule table)
└── utils.py               ← Shared helpers (age calc, payer check, date math, ICD-10 matchers)
```

---

## Complete Billing Rule Definitions

Each detector must implement a `detect(patient, encounter=None)` method that returns a list of `BillingOpportunity` instances. Below is the exhaustive rule set organized by detector module.

---

### `awv.py` — Annual Wellness Visit Detection

#### Rule: AWV_INITIAL
- **Codes:** G0438
- **Payer:** Medicare
- **Eligibility:** Medicare Part B beneficiary AND >12 months since Part B effective date AND no G0438 or G0439 billed in past 12 months AND no IPPE (G0402) in past 12 months
- **Revenue:** $175
- **Frequency:** Annual
- **Cost-share waived:** Yes (copay + deductible)
- **Detection logic:** `patient.payer == 'medicare' AND NOT has_claim(patient, ['G0438', 'G0439'], within_months=12) AND NOT has_claim(patient, ['G0402'], within_months=12) AND months_since_part_b_enrollment(patient) > 12`
- **Documentation checklist:** ["Health Risk Assessment (HRA) completed", "Review of functional ability and safety", "Detection of cognitive impairment screening", "Personalized prevention plan created/updated", "Screening schedule list provided", "Advance directive discussion documented"]
- **Notes:** First AWV only — use G0439 for subsequent. Can pair with G2211 if longitudinal relationship criteria met.

#### Rule: AWV_SUBSEQUENT
- **Codes:** G0439
- **Payer:** Medicare
- **Eligibility:** Medicare Part B beneficiary AND has had prior AWV (G0438 or G0439) or IPPE (G0402) AND no AWV in past 12 months
- **Revenue:** $130
- **Frequency:** Annual
- **Cost-share waived:** Yes
- **Detection logic:** `patient.payer == 'medicare' AND has_ever_claim(patient, ['G0438', 'G0439', 'G0402']) AND NOT has_claim(patient, ['G0438', 'G0439'], within_months=12)`
- **Documentation checklist:** ["Updated HRA", "Updated prevention plan", "Updated screening schedule", "Cognitive assessment performed", "Advance care planning discussion documented"]

#### Rule: IPPE_WELCOME_MEDICARE
- **Codes:** G0402
- **Payer:** Medicare
- **Eligibility:** New Medicare Part B beneficiary within first 12 months of Part B coverage AND no prior IPPE
- **Revenue:** $175
- **Frequency:** Once
- **Cost-share waived:** Yes
- **Detection logic:** `patient.payer == 'medicare' AND months_since_part_b_enrollment(patient) <= 12 AND NOT has_ever_claim(patient, ['G0402'])`
- **Documentation checklist:** ["Medical/surgical history review", "Depression risk factor review", "Functional ability/safety review", "EKG performed or ordered", "Education/counseling provided", "Referral list provided"]

#### Rule: ACP_WITH_AWV
- **Codes:** 99497 (first 30 min), 99498 (each additional 30 min)
- **Payer:** Medicare
- **Eligibility:** Any Medicare patient at AWV visit — especially patients >65 without advance directive on file
- **Revenue:** $85
- **Frequency:** Annual (with AWV)
- **Cost-share waived:** Yes (ONLY when billed with AWV — standard cost-sharing if standalone)
- **Detection logic:** `encounter.visit_type in ['AWV', 'IPPE'] AND (NOT patient.has_advance_directive OR patient.age >= 65)`
- **Documentation checklist:** ["Voluntary ACP discussion documented", "Topics: advance directives, healthcare proxy, living will, code status", "Start/stop time documented (time-based code)", "Patient preferences recorded"]
- **Notes:** Zero cost-share ONLY with AWV. Time-based — must document start/stop.

#### Rule: PROLONGED_PREVENTIVE
- **Codes:** G0513 (first 30 min beyond typical), G0514 (each additional 30 min)
- **Payer:** Medicare
- **Eligibility:** Medicare patient whose preventive visit (AWV/IPPE) extends beyond typical time
- **Revenue:** $45
- **Frequency:** Per qualifying visit
- **Cost-share waived:** Yes
- **Detection logic:** `encounter.visit_type in ['AWV', 'IPPE'] AND encounter.duration_minutes > awv_typical_time + 30`
- **Documentation checklist:** ["Total time documented", "Activities during extended time described"]

---

### `em_addons.py` — E/M Visit Add-Ons

#### Rule: G2211_COMPLEXITY
- **Codes:** G2211
- **Payer:** Medicare
- **Eligibility:** Medicare patient at E/M visit (99202-99215) where the visit addresses a condition managed in an ongoing longitudinal relationship AND patient has ≥1 chronic condition managed by the practice
- **Revenue:** $16
- **Frequency:** Per qualifying E/M visit
- **Detection logic:** `patient.payer == 'medicare' AND encounter.cpt_code in ['99202'-'99215'] AND patient.chronic_condition_count >= 1 AND encounter.is_established_relationship`
- **Documentation checklist:** ["Ongoing longitudinal relationship documented", "Condition requires continuing management decision-making", "Medical decision-making complexity documented", "Relationship continuity noted"]
- **Notes:** CANNOT bill with modifier 25 E/M. CANNOT bill with preventive visits (AWV, wellness exam). ~$16/visit but extremely high volume — flag on EVERY qualifying Medicare E/M.

#### Rule: PROLONGED_SERVICES_OFFICE
- **Codes:** 99417
- **Payer:** Medicare / Private
- **Eligibility:** Patient visit time exceeds highest-level E/M threshold (99205: >74 min or 99215: >54 min total time)
- **Revenue:** $65 per 15-min unit
- **Frequency:** Per qualifying visit (multiple units allowed)
- **Detection logic:** `(encounter.cpt_code == '99215' AND encounter.total_time_minutes > 54) OR (encounter.cpt_code == '99205' AND encounter.total_time_minutes > 74)`
- **Documentation checklist:** ["Highest-level E/M billed first (99205 or 99215)", "Total time on date of encounter documented", "Each 15-min increment documented"]
- **Notes:** Each unit = 15 min beyond threshold. Some private payers use 99354-99355 instead — check payer.

#### Rule: MODIFIER_25_PROMPT
- **Codes:** Modifier 25 on E/M code
- **Payer:** Medicare / Private
- **Eligibility:** Visit where both a problem-based E/M AND a procedure or preventive service are performed on the same date
- **Revenue:** Varies (full E/M reimbursement that would otherwise be lost)
- **Frequency:** Per qualifying visit
- **Detection logic:** `encounter.has_procedure OR encounter.visit_type == 'preventive' AND encounter.has_separate_problem_addressed`
- **Documentation checklist:** ["Separate and distinct reason for E/M documented", "Separate HPI for the distinct problem", "Separate exam elements for the distinct problem", "Separate MDM for the distinct problem"]

---

### `ccm.py` — Chronic Care Management

#### Rule: CCM_STANDARD
- **Codes:** 99490
- **Payer:** Medicare
- **Eligibility:** Medicare patient with ≥2 chronic conditions expected to last ≥12 months that place patient at significant risk of death, exacerbation, or functional decline AND patient consent on file AND no CCM claim in current calendar month
- **Revenue:** $62/month
- **Frequency:** Monthly
- **Detection logic:** `patient.payer == 'medicare' AND count_qualifying_chronic_conditions(patient) >= 2 AND patient.ccm_consent == True AND NOT has_claim(patient, ['99490', '99491'], within_current_month=True)`
- **Qualifying chronic ICD-10 code families (non-exhaustive):** E08-E13 (diabetes), I10-I16 (hypertension), I25 (chronic ischemic heart disease), I50 (heart failure), J44 (COPD), J45 (asthma), N18 (CKD), M05-M06 (RA), M15-M19 (osteoarthritis), F32-F33 (depression), F41 (anxiety), G20 (Parkinson's), G30 (Alzheimer's), K70-K77 (chronic liver disease), E78 (hyperlipidemia — when managed chronically)
- **Documentation checklist:** ["Written patient consent obtained and documented", "Comprehensive care plan established/updated", "20+ min clinical staff time in calendar month documented (time log)", "Care coordination activities described", "Medication list reviewed"]
- **Notes:** Only one provider can bill CCM per patient per month. MA/RN time counts toward the 20 min. Patient must consent verbally or in writing. Big revenue multiplier across the panel — flag every eligible patient.

#### Rule: CCM_COMPLEX
- **Codes:** 99491
- **Payer:** Medicare
- **Eligibility:** Same as 99490 but ≥60 min clinical staff time per month with provider personally performing substantial portion
- **Revenue:** $130/month
- **Frequency:** Monthly
- **Detection logic:** `ccm_eligible(patient) AND ccm_monthly_time(patient) >= 60 AND provider_personal_time(patient) >= substantial_threshold`
- **Documentation checklist:** ["Same as 99490", "Provider personally performed substantial care management activities", "60+ min total clinical staff time documented"]

#### Rule: CCM_ADDITIONAL_30
- **Codes:** 99439
- **Payer:** Medicare
- **Eligibility:** Patient already qualifying for 99490 with additional 30-min increments of clinical staff time (up to 2 units)
- **Revenue:** $47/unit (max 2)
- **Frequency:** Monthly
- **Detection logic:** `has_claim(patient, ['99490'], within_current_month=True) AND ccm_monthly_time(patient) >= 50`

#### Rule: PCM_PRINCIPAL_CARE
- **Codes:** 99424 (first 30 min), 99425 (each additional 30 min)
- **Payer:** Medicare
- **Eligibility:** Medicare patient with 1 complex chronic condition requiring ongoing management (does NOT meet 2-condition CCM threshold or management is focused on a single dominant condition)
- **Revenue:** $70/month
- **Frequency:** Monthly
- **Detection logic:** `patient.payer == 'medicare' AND has_complex_single_chronic(patient) AND NOT has_claim(patient, ['99490', '99491'], within_current_month=True)`
- **Notes:** Cannot bill both PCM and CCM for same patient in same month.

---

### `tcm.py` — Transitional Care Management

#### Rule: TCM_HIGH
- **Codes:** 99496
- **Payer:** Medicare / Private
- **Eligibility:** Patient discharged from hospital, SNF, observation, or partial hospitalization within past 30 days AND high MDM complexity
- **Revenue:** $280
- **Frequency:** Per discharge episode (30-day period)
- **Detection logic:** `patient.has_recent_discharge(within_days=30) AND NOT has_claim(patient, ['99495', '99496'], within_days=30)`
- **Documentation checklist:** ["Contact within 2 business days of discharge (phone or electronic) — DATE AND TIME LOGGED", "Face-to-face visit within 7 calendar days of discharge", "Medication reconciliation performed and documented", "Care coordination for 30-day period documented", "High-complexity MDM documented"]
- **Notes:** EXTREMELY high-value code. The 2-business-day contact is the most commonly missed requirement. Requires proactive discharge tracking from inbox/fax.

#### Rule: TCM_MODERATE
- **Codes:** 99495
- **Payer:** Medicare / Private
- **Eligibility:** Same as 99496 but moderate MDM complexity
- **Revenue:** $220
- **Frequency:** Per discharge episode
- **Detection logic:** Same as TCM_HIGH but with moderate MDM. Also: if 7-day window for 99496 was missed, patient is still eligible for 99495 if seen within 14 days.
- **Documentation checklist:** ["Same as 99496 but face-to-face within 14 calendar days", "Moderate-complexity MDM"]

---

### `bhi.py` — Behavioral Health Integration

#### Rule: BHI_GENERAL
- **Codes:** 99484
- **Payer:** Medicare
- **Eligibility:** Medicare patient with active behavioral health condition (ICD-10 F-codes) AND ≥20 min clinical staff time per month for BH care management
- **Revenue:** $50/month
- **Detection logic:** `patient.payer == 'medicare' AND has_active_dx(patient, icd10_prefix=['F10'-'F19', 'F20'-'F48']) AND bhi_monthly_time(patient) >= 20`
- **Documentation checklist:** ["Initial BH assessment documented", "BH care plan established", "20+ min/month BH care manager time logged", "Validated screening tool administered (PHQ-9, GAD-7)", "Treatment adjustment documented if indicated"]
- **Notes:** Cannot bill same month as CoCM (99492-99494). Lower bar than CoCM.

#### Rule: COCM_INITIAL
- **Codes:** 99492
- **Payer:** Medicare
- **Revenue:** $165/month (initial)
- **Detection logic:** `bhi_eligible(patient) AND practice.has_cocm_infrastructure AND cocm_monthly_time(patient) >= 36 AND patient.cocm_enrollment_month == current_month`

#### Rule: COCM_SUBSEQUENT
- **Codes:** 99493
- **Revenue:** $130/month (subsequent)

#### Rule: COCM_ADDITIONAL_30
- **Codes:** 99494
- **Revenue:** $65/month (add-on)

---

### `screenings.py` — Screening Instruments

Implement detection for each screening below. Each produces a `BillingOpportunity` when criteria are met.

| Rule Code | Instrument | CPT/HCPCS | Payer | Eligible Population | Detection Logic | Revenue | Frequency |
|---|---|---|---|---|---|---|---|
| SCREEN_DEPRESSION | PHQ-9/PHQ-2 | 96127 (Private); G0444 (Medicare annual) | All | All adults | No screening in past 12 months OR at every visit if flagged | $8 | Per admin (up to 2/visit) |
| SCREEN_ANXIETY | GAD-7 | 96127 | All | Adults with risk factors | Anxiety risk factors on problem list; pair with PHQ-9 as 2nd unit | $8 | Per admin |
| SCREEN_DEVELOPMENTAL | ASQ-3, M-CHAT | 96110 | Private | Children at 9, 18, 24, 30 months | Age matches Bright Futures milestone | $10 | Per milestone |
| SCREEN_BEHAVIORAL_PEDS | PSC, CRAFFT | 96127 | Private | Children/adolescents at preventive visits | Age 0-21 at preventive visit | $8 | Per visit |
| SCREEN_ALCOHOL | AUDIT-C/CAGE | G0442/G0443 (Medicare); 99408/99409 (Private) | All | All adults 18+ | No alcohol screening in past 12 months | $20 | Annual |
| SCREEN_SUBSTANCE | DAST-10/NIDA | 99408, 99409 | Private | Adults 18+ | No SUD screening on file | $30 | Annual |
| SCREEN_TOBACCO | Cessation counseling | 99406, 99407 | All | All tobacco users | Active tobacco use in social history | $18 | Per session (up to 8/year Medicare) |
| SCREEN_COGNITIVE | MMSE/MoCA/Mini-Cog | 96127 or 99483 | All | AWV patients; memory complaints | AWV encounter OR cognitive complaints | $8-$280 | Annual |
| SCREEN_MATERNAL_DEPRESSION | Edinburgh/PHQ-9 | 96127 | Private | Postpartum women at well-baby visits; pregnant women | Patient is pregnant or postpartum <12 months | $8 | Per visit |

**Documentation checklist (all screenings):** ["Validated screening instrument identified by name", "Score documented numerically", "Brief clinical interpretation documented", "Follow-up plan documented if positive", "Time documented if time-based code"]

---

### `preventive_labs.py` — Preventive Lab Screenings

| Rule Code | Service | CPT/HCPCS (Medicare / Private) | Eligible Population | Detection Logic | Revenue | Frequency | Modifier |
|---|---|---|---|---|---|---|---|
| PREV_LIPID | CVD Screening (Lipid Panel) | 80061, 82465, 83718, 84478 | Medicare: no CVD symptoms; Private: adults with risk factors | No lipid panel per interval (5yr Medicare, varies Private) | $35 | Per interval | 33 (private) |
| PREV_DIABETES | Diabetes Screening | 82947, 82950, 82951 (Medicare); 82947/83036 (Private) | Age 40-70, BMI ≥25 (Private); risk factors (Medicare) | No glucose/A1C per USPSTF interval AND BMI ≥25 AND age 40-70 | $20 | Every 3 years | 33 (private) |
| PREV_HCV | Hepatitis C Screening | G0472 (Medicare); 86803, 87520-87522 (Private) | Adults 18-79 (USPSTF); Medicare: high-risk + birth cohort 1945-1965 | No HCV screening on record AND age 18-79 | $30 | One-time | 33 (private) |
| PREV_HBV | Hepatitis B Screening | 86704, 86706, 87340, 87341 | Pregnant women; high-risk persons | Pregnant without HBV screen OR high-risk without screen | $25 | One-time/per pregnancy | 33 (private) |
| PREV_HIV | HIV Screening | 80081 (Medicare); 86689, 86701-86703, 87389-87391, 87534-87539, 87806 (Private) | Ages 15-65; all pregnant women; high-risk any age | No HIV screening on record AND age 15-65 | $25 | One-time (annual high-risk) | 33 (private) |
| PREV_STI | STI Screening (CT/GC/Syphilis) | Various (87490-87491, 87590-87591, 86592-86593, 86780) | Women ≤24 sexually active; pregnant women; high-risk persons | Risk criteria met AND no screening per interval | $40 | Annual/per pregnancy | 33 (private) |
| PREV_CRC | Colorectal Cancer Screening | 82270/82274/81528 (FIT/Cologuard); G0104-G0121 (Medicare scopes); 45330-45398 (Private) | Adults 45-75 | No CRC screening per method-specific interval | $25 | Varies by method | 33 (private) |
| PREV_LUNG | Lung Cancer Screening (LDCT) | G0296 (counseling), G0297 (LDCT) — Medicare; N/A (Private) | Age 50-80, ≥30 pack-year smoking, current/quit <15y | Smoking pack-years ≥30 AND age 50-80 AND (current smoker OR quit <15y) AND no LDCT in 12mo | $0 (order) | Annual | 33 (private) |
| PREV_CERVICAL | Cervical Cancer Screening (Pap/HPV) | G0123-G0148, P3000-P3001, Q0091 (Medicare); 88141-88175 (Private) | Women 21-65 | Female AND age 21-65 AND no cervical screen per interval (3yr Pap, 5yr HPV/co-test) | $30 | Every 3-5 years | 33 (private) |
| PREV_MAMMO | Screening Mammography | 77063, 77067 (Medicare); 77065-77067 (Private) | Women ≥40 | Female AND age ≥40 AND no mammogram in 1-2 years | $0 (referral) | Annual/biennial | 33 (private) |
| PREV_DEXA | Bone Density Screening | 76977, 77078, 77080, 77081, 77085 | Women ≥65; postmenopausal <65 with risk factors; glucocorticoid patients | Female ≥65 without DEXA OR postmenopausal <65 with FRAX risk OR on glucocorticoids | $0 (referral) | Every 2 years | 33 (private) |
| PREV_AAA | AAA Screening (Ultrasound) | 76706 | Men 65-75 who have ever smoked | Male AND age 65-75 AND ever-smoker AND no prior AAA screening | $0 (referral) | One-time | 33 (private) |
| PREV_TB | Tuberculosis Screening | 86480, 86481, 86580 | Adults at increased risk (immigrants, homeless, healthcare workers, immunocompromised) | TB risk factors in social history AND no recent TB screening | $15 | Per risk assessment | 33 (private) |
| PREV_BACTERIURIA | Bacteriuria Screening (Pregnant) | 87081, 87084, 87086, 87088 | Pregnant women at 12-16 weeks or first prenatal visit | Pregnant AND no urine culture on file | $20 | Per pregnancy | 33 (private) |

---

### `immunizations.py` — Immunization Gap Detection

For each vaccine below, detect patients who are DUE or OVERDUE based on CDC/ACIP schedules. Use the CDC Immunization Schedule API when available, with a local fallback table.

| Rule Code | Vaccine | CPT (Vaccine) | Admin Code | Eligible Population | Series / Schedule | Revenue Est. |
|---|---|---|---|---|---|---|
| IMM_FLU | Influenza | 90654-90689 | 90471/G0008 | All patients ≥6mo, annually Sept-March | Annual | $30 |
| IMM_PNEUMO | Pneumococcal (PCV20/PPSV23) | 90670, 90732 | 90471/G0009 | Adults ≥65; 19-64 with risk conditions | Per ACIP (PCV20 preferred) | $50 |
| IMM_SHINGRIX | Shingles (Shingrix) | 90750 | 90471 | Adults ≥50 | 2-dose series (2-6mo apart) | $200 |
| IMM_TDAP | Tdap/Td | 90714, 90715 | 90471 | All adults q10y; pregnant women 27-36wk each pregnancy | Every 10 years / per pregnancy | $35 |
| IMM_HPV | HPV (Gardasil 9) | 90651 | 90471 | Ages 9-26 (routine); 27-45 (shared decision) | 2-3 dose series | $250 |
| IMM_HEPB | Hepatitis B | 90739-90747 | 90471/G0010 | All unvaccinated adults (ACIP 2022 universal); Medicare: at risk | 2-3 dose series | $60 |
| IMM_HEPA | Hepatitis A | 90632-90636 | 90471 | Children 12-23mo; adults at risk | 2-dose series | $40 |
| IMM_COVID | COVID-19 | Per current CPT | 90471 | Per current ACIP | Per ACIP schedule | $40 |
| IMM_RSV | RSV (Abrysvo/Arexvy) | Per current CPT | 90471 | Adults ≥60 (shared decision); pregnant 32-36wk | Single dose / per pregnancy | $200 |
| IMM_MENACWY | Meningococcal (MenACWY) | 90620, 90621, 90733, 90734 | 90471 | Adolescents 11-12 + 16 booster; at-risk adults | Per ACIP | $75 |
| IMM_MENB | Meningococcal B | 90620, 90621 | 90471 | Ages 16-23 (shared decision); at-risk | 2-3 dose series | $75 |

**Always bill BOTH the vaccine product code AND the administration code. This is one of the most common billing misses.**

**Track series completion** — flag patients who received dose 1 but are overdue for dose 2/3.

---

### `counseling.py` — Counseling & Education Codes

| Rule Code | Service | CPT/HCPCS | Payer | Population | Detection Logic | Revenue | Frequency |
|---|---|---|---|---|---|---|---|
| COUNS_OBESITY_ADULT | Obesity Counseling (Adult) | G0447 (Medicare IBT); 97802-97804 (Private) | All | BMI ≥30 | BMI ≥30 on most recent vitals | $30 | Multiple sessions/year |
| COUNS_OBESITY_PEDS | Obesity Counseling (Pediatric) | 97802-97804 | Private | Children ≥6 with BMI ≥95th %ile | BMI ≥95th percentile | $30 | Multiple sessions |
| COUNS_MNT | Medical Nutrition Therapy | 97802-97804; G0270/G0271 | Medicare | Diabetes, CKD, post-transplant (36mo) | Diabetes (E11.x) or CKD (N18.x) without MNT referral | $50 | 3hr initial, 2hr subsequent |
| COUNS_DSMT | Diabetes Self-Management | G0108, G0109 | Medicare | Diabetics with physician order | Diabetes dx without DSMT in past 12mo | $0 (referral) | 10hr initial + 2hr/yr |
| COUNS_CVD_IBT | CVD Behavioral Therapy | G0446 | Medicare | All competent Medicare beneficiaries with CVD risk | CVD risk factors (HTN, HLD, obesity, DM, smoking) | $25 | Annual |
| COUNS_TOBACCO | Tobacco Cessation | 99406/99407 | All | All tobacco users | Active tobacco use in social history | $18 | Up to 8 sessions/yr (Medicare) |
| COUNS_BREASTFEED | Breastfeeding Support | 99401-99404 | Private | Pregnant/nursing women | Pregnant or postpartum patient | $0 (part of visit) | As needed |
| COUNS_FALLS | Falls Prevention | 97110, 97112, 97116, 97530 | Private | Adults ≥65 at increased fall risk | Age ≥65 AND fall risk factors (polypharmacy, prior falls, balance issues) | $35 | As needed |

---

### `procedures.py` — In-Office Procedure Add-Ons

| Rule Code | Procedure | CPT | Population | Detection Logic | Revenue |
|---|---|---|---|---|---|
| PROC_EKG | 12-Lead EKG | 93000/93005/93010 | IPPE patients; cardiac symptoms; QTc-prolonging meds | IPPE encounter OR new cardiac symptoms OR on QTc-prolonging medication | $25 |
| PROC_SPIROMETRY | Spirometry | 94010/94060 | COPD/asthma patients; new respiratory symptoms | COPD/asthma dx without spirometry in 12mo OR new respiratory presentation | $35 |
| PROC_POCT | Point-of-Care Testing | 87880, 87804, 81002, 81025, 82962, 82270, etc. | Acute visit patients | Visit type = acute AND common POCT-indicated presentations (URI, UTI, etc.) | $12/test |
| PROC_VENIPUNCTURE | Venipuncture | 36415/36416 | Any in-office blood draw | Lab orders placed AND drawn in-office | $3 |
| PROC_INJECTION_ADMIN | Injection Administration | 96372 (therapeutic); 90471/90472 (vaccine) | Any injection encounter | Injection performed (B12, Depo, steroid, toradol, vaccine) | $25 |
| PROC_NEBULIZER | Nebulizer Treatment | 94640 | Acute bronchospasm/asthma/COPD exacerbation | In-office nebulizer administered | $20 |
| PROC_PULSE_OX | Pulse Oximetry | 94760/94761 | Respiratory complaints | Pulse ox performed during acute respiratory visit | $8 |

---

### `chronic_monitoring.py` — Chronic Disease Lab Monitoring

| Rule Code | Lab | CPT | Population | Detection Logic (Overdue) | Interval |
|---|---|---|---|---|---|
| MON_A1C | HbA1c | 83036 | Diabetics; pre-diabetics | Diabetes dx AND no A1C in 3-6mo; Pre-DM AND no A1C in 12mo | 3-6mo / 12mo |
| MON_LIPID | Lipid Panel | 80061 | Patients on statins; hyperlipidemia | On statin OR HLD dx AND no lipid panel in 12mo | Annual |
| MON_TSH | TSH | 84443 | On levothyroxine; thyroid disorders | On thyroid med AND no TSH in 6-12mo | 6-12mo |
| MON_RENAL | BMP/CMP | 80048/80053 | On metformin, ACEi/ARB, diuretics, lithium; CKD | On nephrotoxic med AND no BMP/CMP in 6-12mo | 6-12mo |
| MON_CBC | CBC | 85025/85027 | On methotrexate, carbamazepine, clozapine, etc. | On hematologic-monitoring med AND no CBC per schedule | Per drug schedule |
| MON_INR | INR | 85610 | On warfarin | On warfarin AND no INR per interval (weekly to monthly) | Weekly-monthly |
| MON_LFT | Hepatic Function Panel | 80076 | On hepatotoxic meds; chronic liver disease | On hepatotoxic med AND no LFTs per schedule | Per drug schedule |
| MON_UACR | Urine Albumin/Creatinine Ratio | 82043/82570 | Diabetics; CKD | Diabetes dx AND no UACR in 12mo | Annual |
| MON_VITD | Vitamin D Level | 82306 | On vitamin D supplementation; osteoporosis; CKD | On vitamin D supp AND no level in 12mo (must have clinical indication — not a universal screen) | Annual |

---

### `telehealth.py` — Telehealth & Communication

| Rule Code | Service | CPT | Population | Detection Logic | Revenue |
|---|---|---|---|---|---|
| TELE_PHONE_EM | Telephone E/M | 99441 (5-10min), 99442 (11-20min), 99443 (21-30min) | Established patients | Phone encounter >5 min with clinical decision-making; NOT resulting in visit within 24hr | $45 |
| TELE_DIGITAL_EM | Online Digital E/M (Portal) | 99421 (5-10min/7d), 99422 (11-20min), 99423 (21+min) | Established patients | Patient-initiated portal messages requiring >5 min cumulative clinical time over 7 days | $40 |
| TELE_INTERPROF | Interprofessional Consultation | 99452 | PCP consulting specialist | Provider documents specialist phone/electronic consultation, ≥16 min prep + communication time | $40 |

---

### `sdoh.py` — Social Determinants & Risk Assessment

| Rule Code | Service | CPT | Population | Detection Logic | Revenue |
|---|---|---|---|---|---|
| SDOH_SCREEN | SDOH Assessment | 96160/96161 | All patients | No SDOH screening on file; new patient visit or annual preventive | $8 |
| SDOH_IPV | IPV Screening | Part of preventive visit | Women of reproductive age | Female, reproductive age, at preventive visit | $0 (supports visit coding) |
| SDOH_HRA | Health Risk Assessment | Part of AWV | Medicare AWV patients | AWV encounter — auto-include; verify HRA completed | $0 (required for AWV compliance) |

---

### `pediatric.py` — Pediatric / Bright Futures Add-Ons

| Rule Code | Service | CPT | Population | Detection Logic | Revenue |
|---|---|---|---|---|---|
| PEDS_WELLCHILD | Well-Child Visit | 99381-99384/99391-99394 | All children per Bright Futures schedule | Age matches Bright Futures periodicity AND no well-child in appropriate interval | $150 |
| PEDS_LEAD | Lead Screening | 83655 + 36415/36416 | Children at 12 and 24 months; Medicaid children | Age 12mo or 24mo at well visit; Medicaid = mandatory | $10 |
| PEDS_ANEMIA | Anemia Screening | 85014/85018 + 36415/36416 | Infants at 12 months | Age 12mo at well visit | $8 |
| PEDS_DYSLIPIDEMIA | Dyslipidemia Screening | 80061 + 36415/36416 | Ages 9-11 (once) and 17-21 (once) | Age 9-11 without lipid screen OR age 17-21 without lipid screen | $25 |
| PEDS_FLUORIDE | Fluoride Varnish | 99188 | Children with teeth through age 5 | Age ≤5 AND teeth present at well visit | $25 |
| PEDS_VISION | Vision Screening | 99173/99174/99177 | Children 3-5 (USPSTF); per Bright Futures schedule | Age matches screening milestone AND no vision screen | $10 |
| PEDS_HEARING | Hearing Screening | 92551/92552/92567 | Per Bright Futures: 4, 5, 6, 8, 10y; once 11-14, 15-17, 18-21 | Age matches Bright Futures hearing milestone | $15 |
| PEDS_MATERNAL_DEPRESSION | Maternal Depression at Well-Baby | 96127 | Mothers at well-baby visits | Patient age <12mo at well-baby visit — screen mother | $8 |

---

### `misc.py` — Often Overlooked / Miscellaneous

| Rule Code | Service | CPT | Population | Detection Logic | Revenue |
|---|---|---|---|---|---|
| MISC_AFTER_HOURS | After-Hours Premium | 99050/99051/99053 | Patients seen outside regular hours | Encounter time falls outside defined office hours (M-F 8a-5p) | $30 |
| MISC_CARE_PLAN_OVERSIGHT | Care Plan Oversight | 99339/99340 | Medicare patients with active home health/hospice | Patient receiving home health AND ≥15 min/month provider oversight time | $75 |
| MISC_PREP | PrEP Management | E/M + labs | HIV-negative patients at high HIV risk | HIV risk factors AND on or candidate for PrEP medication | $0 (drives quarterly visits + labs) |
| MISC_GDM_SCREENING | Gestational Diabetes Screening | 82947-82952 | Pregnant women at 24-28 weeks | Pregnant AND gestational age 24-28wk AND no GDM screen | $20 |
| MISC_PERINATAL_DEPRESSION | Perinatal Depression Prevention | 96161 | Pregnant/postpartum at increased risk | Pregnant or postpartum <12mo with depression risk factors | $10 |
| MISC_STATIN_COUNSELING | Statin Preventive Medication | Pharmacy benefit | Adults 40-75, ≥10% 10yr ASCVD risk, no CVD history | 10yr ASCVD risk ≥10% (calculate from lipids + risk factors) AND not on statin | $0 (supports care gap) |
| MISC_FOLIC_ACID | Folic Acid Counseling | Pharmacy benefit | Women of reproductive age | Female, reproductive age, not on folic acid | $0 (supports care gap) |

---

## Payer Routing Logic

All detectors must check patient payer type before generating an opportunity:

```python
def get_payer_context(patient):
    """Return payer-specific billing context."""
    if patient.payer_type == 'medicare_b':
        return {
            'use_g_codes': True,       # G0438, G0439, G0442, G0444, G0446, G0447, G0472, G0476, etc.
            'use_modifier_33': False,   # Medicare uses G-codes instead of modifier 33
            'admin_codes': {'flu': 'G0008', 'pneumo': 'G0009', 'hepb': 'G0010'},
            'awv_eligible': True,
            'ccm_eligible': True,
            'tcm_eligible': True,
            'g2211_eligible': True,
        }
    elif patient.payer_type in ['private', 'commercial']:
        return {
            'use_g_codes': False,       # Use CPT codes
            'use_modifier_33': True,    # Modifier 33 for ACA preventive services
            'admin_codes': {'flu': '90471', 'pneumo': '90471', 'hepb': '90471'},
            'awv_eligible': False,      # No AWV for private — use 99385-99397
            'ccm_eligible': False,      # Some private payers cover CCM, but not standard
            'tcm_eligible': True,       # Most private payers cover TCM
            'g2211_eligible': False,    # Medicare-only code
        }
    elif patient.payer_type == 'medicaid':
        return {
            'use_g_codes': False,
            'use_modifier_33': False,
            'mandatory_lead_screening': True,
            'epsdt_eligible': patient.age < 21,
        }
```

---

## Dashboard Integration

Surface billing opportunities in the pre-visit briefing and during-encounter dashboard:

1. **Pre-Visit Panel:** Show all detected opportunities for today's patients sorted by priority (high → low) and estimated revenue. Group by category. Include one-click "Accept" (mark for billing) and "Dismiss" (with reason) actions.

2. **During-Encounter Alert Bar:** At the top of the active encounter view, show a compact alert bar with count of open opportunities and top-priority items. Clicking expands to full checklist view.

3. **Post-Visit Summary:** After encounter close, show any opportunities that were detected but not actioned. Prompt provider to accept or dismiss.

4. **Monthly Billing Report:** Aggregate all detected, accepted, dismissed, and billed opportunities with revenue totals by category. Compare detected vs captured to show the revenue gap.

---

## Revenue Estimation

For the monthly billing report, calculate estimated annual revenue impact per category using the formulas in the `Category Summary` sheet of the attached `CareCompanion_Billing_Master_List.xlsx`. Key high-value targets:

- **CCM (99490):** $62/patient/month × eligible_patient_count × 12
- **G2211:** $16/visit × medicare_em_visit_count_per_year
- **AWV (G0439):** $130/visit × medicare_patients_without_awv
- **TCM (99496):** $280/discharge × annual_discharges_detected
- **Immunizations:** vaccine_margin + admin_fee × doses_administered
- **Screening instruments (96127):** $8 × 2_units × patient_visits_per_year

---

## Implementation Priority

Build in this order:

1. **Phase 1 (highest ROI, lowest complexity):** AWV detection, G2211 auto-suggest, screening instrument prompts (PHQ-9, GAD-7, AUDIT-C), immunization gap detection, modifier 25 prompts, venipuncture/injection admin capture
2. **Phase 2 (high ROI, moderate complexity):** CCM eligibility flagging + time tracking, TCM discharge detection, preventive lab gap engine, chronic disease monitoring labs, tobacco cessation tracking
3. **Phase 3 (moderate ROI, higher complexity):** BHI/CoCM workflow, telephone/digital E/M time tracking, RPM infrastructure, pediatric Bright Futures engine, SDOH screening prompts
4. **Phase 4 (refinements):** Portal message time analysis, care plan oversight tracking, after-hours premium detection, revenue reporting dashboard, payer-specific routing optimization
