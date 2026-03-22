# CareCompanion — Revenue Optimization System: Complete Copilot Planning Prompt

---

## STEP 0 — READ THESE FILES COMPLETELY BEFORE DOING ANYTHING ELSE

Read all of the following files in full before producing a single word of
planning output. Do not skim. Do not summarize and proceed. Read every line.

```
docs/init.prompt.md
docs/CareCompanion_Development_Guide.md
docs/carecompanion_api_intelligence_plan.md
docs/CareCompanion_Billing_Master_List.csv
PROJECT_STATUS.md
PROJECT_STATUS_BILLING.md       (if it exists)
app/models.py                   (or equivalent — find the model definitions)
app/billing_engine/             (entire directory — every file)
app/routes/                     (entire directory — every file)
app/services/                   (entire directory — every file)
app/templates/                  (entire directory — note every existing template)
```

After reading, confirm your understanding by answering these specific
questions before starting the plan:

1. What models currently exist in the billing engine layer? List every class.
2. What detector modules currently exist under billing_engine/detectors/?
   For each one, list whether it is a stub, partially implemented, or complete.
3. What routes currently exist? Is there an existing /bonus route? An existing
   /billing route? An existing /dashboard route?
4. What is the current state of the BillingOpportunity model — does it exist,
   and if so, what fields does it have?
5. What is the current state of the morning briefing pipeline? Where does it
   live and what does it currently do at run time?
6. Does a BonusTracker model exist anywhere in the codebase?
7. What is the current AC Clinical Summary XML parser's output structure?
   Specifically: does it currently extract problem list ICD-10 codes, medication
   list, immunization records, and lab results, or only a subset?

Do not produce the plan until all seven questions are answered.

---

## PROVIDER FINANCIAL CONTEXT — REQUIRED FOR ALL CALCULATIONS

This is not a generic billing tool. Every feature must be evaluated against a
specific financial situation.

**Provider:** Cory Denton, FNP  
**Practice:** Family Practice Associates of Chesterfield, Midlothian, Virginia  
**Start date:** March 2, 2026  
**Base salary:** $115,000/year  
**Bonus formula:** (Quarterly Receipts − $105,000) × 0.25 = Quarterly Bonus  
**Deficit rule:** Quarterly shortfalls accumulate cumulatively. A Q1 deficit
reduces Q2 bonus eligibility. The running deficit does not zero out each quarter.

**CRITICAL UNKNOWN — FLAG THIS IN THE PLAN:**  
Verify whether the cumulative deficit resets to zero on January 1 each year or
carries across calendar years indefinitely. This single fact changes the entire
financial projection model. The plan must include a step where the provider
manually confirms this with the practice administrator, and the BonusTracker
model must support both behaviors with a configurable flag:
`deficit_resets_annually: bool = True`.

**Start date impact:**  
Q1 2026 contains approximately 22 working days (March 2 – March 31).
Projected Q1 2026 receipts: $4,000–$8,000.
Projected cumulative deficit entering Q2 2026: $97,000–$101,000.
Without billing optimization, the mathematical first bonus quarter is Q3 2027
or later. The revenue optimization system exists entirely to compress this
timeline. Every feature specification must include a `bonus_impact_estimate`
that answers: "How many additional dollars of quarterly receipts does this
generate, and by how many weeks does it move the first bonus quarter forward?"

---

## PART 1 — BILLING DETECTION ENGINE (109 CODES, 17 CATEGORIES)

The complete billing rule definitions are stored in:
`docs/CareCompanion_Billing_Master_List.csv`

The full detection logic for all 109 codes across all 17 categories is
specified in `docs/BILLING_CAPTURE_PROMPT.md`. That file is the authoritative
source for every rule, every CPT/HCPCS code, every eligibility criterion,
every documentation checklist, and every revenue estimate.

**DO NOT restate the rules here.** Read that file. Treat it as the complete
specification for Part 1. The plan for Part 1 must:

### 1A — Audit the existing billing_engine/ directory
For every detector module that exists, document its current state:
- What rules are implemented vs stubbed vs missing
- What data fields from the AC Clinical Summary XML it currently accesses
- What it would need to be complete

For every detector module that does NOT exist, note it as "to be created."

### 1B — AC XML Data Layer Completeness Audit
The detectors require the following data to function. For each field, document
whether the current AC Clinical Summary XML parser already extracts it:

| Required Field | Used By | Currently Extracted? |
|---|---|---|
| Patient DOB / Age | All | ? |
| Patient sex | Preventive labs, peds | ? |
| Insurance/payer type | All | ? |
| Part B enrollment date | AWV, IPPE | ? |
| Active ICD-10 problem list | CCM, TCM, BHI, monitoring | ? |
| Medication list with drug names | Chronic monitoring | ? |
| Immunization history with dates | Immunizations | ? |
| Lab results with dates and values | Monitoring, preventive labs | ? |
| BMI and vitals | Obesity counseling, AWV | ? |
| Tobacco/alcohol social history | Screenings, counseling | ? |
| Visit history (CPT codes billed) | AWV, CCM frequency | ? |
| Advance directive status | AWV, ACP | ? |
| Discharge history | TCM | ? |
| Gestational age / pregnancy status | OB-related codes | ? |

For every field not currently extracted, the plan must include a step to add
it to the XML parser before the dependent detector is built.

### 1C — Detection priority sequence
Build detectors in this exact order, which is ranked by:
(estimated quarterly receipt impact) ÷ (implementation hours):

**Priority 1 — Build first (highest ROI per hour):**
- `em_addons.py`: G2211 on every qualifying Medicare E/M visit. This is the
  single highest-volume opportunity — flag on 100% of Medicare established
  patient visits where criteria are met. Also: Modifier-25 prompt whenever
  both a preventive/procedure AND a separate problem-based E/M occur same day.
  Also: 99417 prolonged service detection when encounter timer exceeds
  99215 (>54 min) or 99205 (>74 min).
- `awv.py`: Full AWV detection — G0402 (IPPE), G0438 (initial), G0439
  (subsequent), 99497 (ACP add-on at zero cost-share), G0444 (depression
  screen, subsequent AWV only), G0442+G0443 (alcohol screen), G0446 (CVD IBT),
  G0447 (obesity IBT if BMI≥30), 96127 (additional screening instruments).
- `procedures.py`: Venipuncture (36415) whenever blood drawn in-office.
  Injection administration (96372) whenever any injection given. Immunization
  administration codes (90471/90472/G0008/G0009) whenever vaccine given.
  These are passive — they apply to nearly every encounter and require no
  clinical decision.
- `screenings.py`: PHQ-9/PHQ-2 (96127), GAD-7 (96127), AUDIT-C (G0442/99408),
  DAST-10 (99408). Flag when not performed in past 12 months at any adult visit.

**Priority 2 — Build second (high ROI, moderate complexity):**
- `ccm.py`: CCM eligibility detection across the panel (99490, 99491, 99439,
  PCM 99424). Focus first on eligibility flagging and consent tracking. Time
  logging infrastructure is secondary.
- `tcm.py`: TCM discharge detection (99495, 99496). Requires a TCM watch list
  that actively monitors the AC inbox and fax queue for discharge documents.
  The 2-business-day contact rule is the most critical — it must generate a
  same-day alert when a discharge is detected.
- `preventive_labs.py`: All 14 preventive screening lab rules — lipid, A1C,
  HCV, HBV, HIV, STI, CRC, cervical, mammography referral, DEXA referral,
  AAA referral, lung cancer screening counseling, TB screening, bacteriuria.
- `chronic_monitoring.py`: All 9 chronic disease monitoring rules — A1C,
  lipid on statin, TSH, BMP/CMP for nephrotoxic meds, CBC for hematologic meds,
  INR for warfarin, LFTs for hepatotoxic meds, UACR for diabetics, Vitamin D.
- `counseling.py`: Tobacco cessation (99406/99407 up to 8 sessions/year),
  obesity IBT (G0447), CVD behavioral therapy (G0446).

**Priority 3 — Build third (moderate ROI, higher complexity):**
- `immunizations.py`: All 11 immunization gap rules. Series completion tracking.
- `bhi.py`: BHI (99484), CoCM (99492-99494). Requires behavioral health
  infrastructure and monthly time logging.
- `telehealth.py`: Telephone E/M (99441-99443), online digital E/M (99421-99423).
  Requires integration with the encounter timer and portal message tracker.
- `sdoh.py`: SDOH assessment (96160/96161), IPV screening.

**Priority 4 — Build last (refinements):**
- `pediatric.py`: Full Bright Futures engine — well-child schedules, lead,
  anemia, dyslipidemia, fluoride varnish, vision, hearing, maternal depression.
- `misc.py`: After-hours premium, care plan oversight, PrEP, GDM screening,
  perinatal depression, statin counseling, folic acid.

### 1D — Model specifications

The plan must specify the exact SQLAlchemy model definitions for:

**BillingRule** — stores the rule library (seed data, not per-patient):
```
id, category, opportunity_code (unique), description, cpt_codes (JSON list),
payer_types (JSON list), estimated_revenue_national, modifier, rule_logic (JSON),
documentation_checklist (JSON array of strings), is_active, frequency_limit
('annual'|'monthly'|'once'|'per_visit'|'per_discharge'), last_updated
```

**BillingOpportunity** — stores per-patient detections:
```
id, patient_id (FK), encounter_id (FK nullable), rule_id (FK to BillingRule),
category, opportunity_code, cpt_codes, description, estimated_revenue,
bonus_impact_dollars (float — calculated from BonusTracker),
bonus_impact_days (int — days forward movement in first-bonus projection),
payer_type, modifier, priority ('high'|'medium'|'low'), status
('detected'|'accepted'|'dismissed'|'billed'), detection_reason (text),
documentation_checklist (JSON), detected_at, actioned_at, dismissed_reason
```

**BillingRuleCache** — stores external fee schedule data:
```
id, cpt_code, description, national_rate_2025, national_rate_2026,
virginia_mac_rate, payer_type, rvu_work, rvu_pe, rvu_mp, last_updated
```

### 1E — DHS Code List Integration

A supplementary code list `docs/2026_DHS_Code_List_Addendum.csv` has been
provided. This is the 2026 CMS Designated Health Services (Stark Law) code list
effective January 1, 2026. The plan must:

1. Import this file into the BillingRuleCache table as a reference during
   initial setup
2. Cross-reference the clinical lab codes (80000 series) against the
   chronic_monitoring.py and preventive_labs.py detectors to confirm all
   billable lab codes are in scope
3. Flag any detector that references a code NOT on the 2026 DHS list so it
   can be reviewed for Stark Law self-referral compliance (relevant if the
   practice ever has ownership arrangements)

---

## PART 2 — BONUS DASHBOARD MODULE

### 2A — BonusTracker Model

Create a new SQLAlchemy model:

```python
class BonusTracker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider_name = db.Column(db.String(100), default='Cory Denton, FNP')
    start_date = db.Column(db.Date, default=date(2026, 3, 2))
    base_salary = db.Column(db.Float, default=115000.0)
    quarterly_threshold = db.Column(db.Float, default=105000.0)
    bonus_multiplier = db.Column(db.Float, default=0.25)
    deficit_resets_annually = db.Column(db.Boolean, default=True)
    # Manually entered quarterly receipt totals
    receipts_2026_q1 = db.Column(db.Float, default=0.0)
    receipts_2026_q2 = db.Column(db.Float, default=0.0)
    receipts_2026_q3 = db.Column(db.Float, default=0.0)
    receipts_2026_q4 = db.Column(db.Float, default=0.0)
    # Monthly receipt entries for granular tracking (JSON: {2026-03: 2100.00, ...})
    monthly_receipts = db.Column(db.Text, default='{}')
    # Payer-specific collection rates for pipeline predictor (JSON)
    collection_rates = db.Column(db.Text, default='{"medicare": 0.75, "medicaid": 0.60, "commercial": 0.70, "self_pay": 0.35}')
    # Cached projections (recalculated nightly)
    projected_first_bonus_quarter = db.Column(db.String(10), nullable=True)  # e.g., "2027-Q3"
    projected_first_bonus_date = db.Column(db.Date, nullable=True)
    last_projection_updated = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
```

### 2B — Bonus Dashboard Route and Template

New route: `GET /bonus` and `POST /bonus/entry`

The dashboard template must include the following components, in this layout
order from top to bottom:

**Component 1 — Current Quarter Status Bar**
- Large progress bar: "Q[X] 2026: $[receipts] of $105,000 threshold"
- Color coding: red if <50% of threshold with <50% of quarter remaining,
  yellow if tracking to miss by <$20,000, green if on track to exceed
- Days remaining in current quarter
- Daily receipt rate needed to hit threshold: `(threshold - receipts_to_date) / business_days_remaining`
- Current daily receipt run rate (30-day rolling average)
- Status message: "At current pace: WILL EXCEED / WILL MISS by $X"

**Component 2 — Cumulative Deficit Tracker**
This is the number that actually controls bonus eligibility. Display it
prominently with context:
- "Cumulative deficit: $[X,XXX]"
- "This means you need receipts totaling $[threshold + deficit] in a single
  quarter before earning any bonus"
- Visual timeline showing each quarter's contribution to / drawdown from deficit
- Red annotation at the projected first bonus quarter

**Component 3 — First Bonus Quarter Projection**
Linear extrapolation engine:
1. Calculate trailing receipt growth rate: (Q_current / Q_prior) - 1
2. Project forward until projected_quarterly_receipts > threshold + remaining_deficit
3. Display: "At current growth trajectory: First bonus expected [Quarter Year]"
4. Show two scenarios side by side:
   - Scenario A: Current pace (no billing optimization)
   - Scenario B: Current pace + estimated annual impact of all accepted
     BillingOpportunities (from the billing engine)
5. Display the difference: "Billing optimization moves your first bonus from
   [Q] to [Q] — [X] quarters earlier"

**Component 4 — Receipt Pipeline Predictor**
"Charges submitted in the last 60 days that have not yet converted to receipts:
$[sum]. At your [payer_mix_adjusted] collection rate of [X]%, expected receipts
arriving this quarter: $[estimated]."

Formula:
- Pull sum of charges from the last 60 days (from AC billing data or manual entry)
- Multiply by payer-weighted average collection rate
- Apply 30-60 day lag — show as "expected within 30 days" vs "expected within 60 days"
- Display the number as an addition to the progress bar in Component 1

**Component 5 — CCM Enrollment Impact Calculator**
"You currently have [X] eligible CCM patients identified. [Y] are enrolled.
Enrolling the next [Z] eligible patients would add $[monthly × 3] to your Q[X]
receipts. This reduces your Q[X] deficit gap from $[current] to $[projected]."

This must pull live data from the billing engine's CCM detector output.

**Component 6 — Monthly Receipt Entry Form**
Simple form: select month, enter receipt amount. Triggers recalculation of all
projections. Include a note field. Store in the monthly_receipts JSON field.
Also include a "Collection rate calibration" section where the provider can
update payer-specific collection rates as real data accumulates.

**Component 7 — Quarter-End Surge Mode Panel**
This panel is HIDDEN unless both conditions are true:
- Less than 30 calendar days remain in the current quarter
- The gap between current receipts + pipeline estimate and the cumulative
  threshold is less than $25,000

When active, this panel replaces the standard morning briefing billing section
with a prioritized intervention list:
- "You are $[X] from earning your first bonus"
- "Reachable opportunities in the next [N] business days:"
  - Open TCM windows (discharge within 30 days, face-to-face not yet completed)
  - Medicare patients not yet seen this quarter with overdue AWV
  - CCM-eligible patients not yet enrolled (first month billable immediately)
  - Patients with G2211-eligible visits not yet scheduled
  - Overdue chronic monitoring labs that can be drawn in-office today
- Total reachable revenue estimate
- "If you complete all of the above: Gap closes to $[X]"

### 2C — Bonus Impact Number on All Billing Cards

Every existing and future `BillingOpportunity` display card must show a
bonus-impact annotation below the revenue estimate. The format is:

```
Estimated revenue: $16/visit
Toward Q2 deficit: Reduces gap by $16 (of $98,400 remaining)
First bonus impact: +0.3 days earlier if applied to all qualifying visits today
```

Implementation:
- The `BillingOpportunity` model gains two new fields: `bonus_impact_dollars`
  and `bonus_impact_days`
- These are computed by a `BonusImpactCalculator` service that reads the current
  `BonusTracker` state and calculates the marginal contribution of accepting
  this opportunity
- The fields are recalculated every time BonusTracker is updated
- Display is handled in the base billing card template via a new
  `{% if bonus_tracker %}` block that is conditionally shown

---

## PART 3 — DOCUMENTATION PHRASE LIBRARY

### Purpose

Every billing code has documentation requirements that insurers audit. Using
precise, compliant language is not gaming the system — it is accurately
documenting what was done in language that adjudication systems recognize.
Vague documentation of excellent care gets downgraded or denied. Specific
documentation of the same care gets paid.

### 3A — PhraseLibrary Model

```python
class DocumentationPhrase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    opportunity_code = db.Column(db.String(20), nullable=False)  # FK to BillingRule
    cpt_code = db.Column(db.String(20), nullable=False)
    phrase_category = db.Column(db.String(50), nullable=False)
    # 'assessment', 'plan', 'hpi', 'mdm', 'time', 'history', 'exam'
    phrase_title = db.Column(db.String(200), nullable=False)
    phrase_text = db.Column(db.Text, nullable=False)
    payer_specific = db.Column(db.String(20), nullable=True)  # None = all payers
    clinical_context = db.Column(db.String(200), nullable=True)  # When to use
    required_elements = db.Column(db.Text, nullable=True)  # JSON — must be present
    is_active = db.Column(db.Boolean, default=True)
```

### 3B — Seed Data: Required Phrases by Code

The following phrases must be seeded into the database on first run. Each
entry must be implementable as a one-click insertion into the Amazing Charts
Assessment or Plan section via the existing AC automation layer.

**G2211 — Longitudinal Relationship (Assessment section):**
```
"I serve as this patient's continuing focal point for all needed healthcare 
services. This visit addressed [CONDITION], which represents a serious and/or 
complex chronic condition requiring ongoing, longitudinal primary care 
management and care coordination."
```
Note: Do not use on same claim as modifier 25 E/M or preventive visits.

**99214 upcode from 99213 — MDM Documentation (MDM section):**
```
"Medical decision-making of moderate complexity: Today's encounter addressed 
[2-3 conditions], including [LIST]. Multiple management options were considered. 
New prescription with monitoring requirements ordered: [DRUG]. Outside records 
reviewed. Risk of complications or morbidity without treatment: moderate."
```

**99215 — High-Complexity MDM (MDM section):**
```
"Medical decision-making of high complexity: Addressed [CONDITION(S)] with 
threat to life or bodily function requiring urgent evaluation. Data reviewed 
includes: [labs/imaging/outside records]. Extensive analysis of potential 
treatment options given [COMPLICATING FACTORS]. Independent interpretation 
of [test/image] performed. Risk: drug therapy requiring intensive monitoring, 
or possible hospitalization if condition worsens."
```

**Time-based billing (when using total time instead of MDM):**
```
"Total time on date of encounter including face-to-face assessment, ordering 
and reviewing results, care coordination with [specialist/pharmacy], medication 
management review, and documentation: [XX] minutes."
```

**AWV — Minimum Documentation Block (Plan section):**
```
"Annual Wellness Visit performed. Health Risk Assessment completed. Reviewed: 
functional ability, activities of daily living, home and fall safety (Timed 
Get Up and Go: [X] sec), depression screening (PHQ-2: [X/X]), cognitive 
assessment (Mini-Cog: [X/5]), advance directive status ([has/does not have]), 
medication reconciliation (reviewed and updated), and personalized prevention 
plan established/updated. Screening schedule provided to patient."
```

**ACP/99497 — Advance Care Planning (separate note section):**
```
"Voluntary advance care planning discussion conducted with [patient/patient 
and family] for [30] minutes (start: [HH:MM], end: [HH:MM]). Topics discussed: 
values and goals, healthcare proxy designation, advance directive/living will, 
code status preferences. Patient [has/does not have] existing advance directive 
on file. [Patient agreed to complete/Patient has completed] advance directive. 
Documentation provided."
```
Note: Must document start and stop time. Patient participation must be voluntary.

**CCM Monthly Note (separate CCM note, not progress note):**
```
"Chronic Care Management services provided this calendar month: [XX] minutes 
total clinical staff time. Activities: medication management review ([date]), 
care plan review and update ([date]), coordination of care with [specialist/
pharmacy/lab] regarding [issue], patient/caregiver communication re: [topic] 
([date], [XX] min). Current CCM care plan on file, last updated [date]. 
Patient consent for CCM services on file ([date])."
```

**TCM — Contact Within 2 Business Days (required documentation):**
```
"Transitional Care Management: Interactive contact with [patient/caregiver] 
made within 2 business days of discharge from [facility] on [discharge date]. 
Contact date: [DATE]. Contact time: [HH:MM]. Contact method: [phone/video/
secure message]. Discussion: discharge medications reconciled, follow-up 
appointments scheduled, warning symptoms reviewed, care plan modifications 
post-hospitalization. Face-to-face visit [scheduled for / completed on] 
[date] — within [7/14]-day window."
```
Note: The date, time, and method of the 2-business-day contact are REQUIRED.
This is the single most audited element of TCM claims.

**TCM — Face-to-Face Visit Note Element (MDM section):**
```
"Transitional Care Management face-to-face visit, [7/14] days post-discharge 
from [FACILITY]. Discharge date: [DATE]. Interactive contact completed [DATE] 
(within 2 business days). Medication reconciliation performed and documented. 
Post-discharge care plan reviewed. Patient understanding of warning signs 
confirmed. [High/Moderate] medical decision-making complexity."
```

**Modifier 25 — Separate E/M Documentation (required when billing E/M + procedure):**
```
"Separate and significant evaluation and management service performed today 
in addition to [PROCEDURE CODE/preventive service]. Chief complaint for this 
separate E/M: [COMPLAINT]. This problem is distinct from the primary reason 
for [procedure/preventive service] and required its own history, examination, 
and independent medical decision-making."
```

**99406/99407 Tobacco Cessation (Plan section):**
```
"Tobacco cessation counseling provided: [3-10 minutes (99406) / >10 minutes 
(99407)]. Session [X] of up to 8 covered sessions per year. Discussed: 
health risks of continued tobacco use, benefits of cessation, cessation 
strategies (behavioral, pharmacotherapy options including [NRT/varenicline/
bupropion]), relapse prevention. Patient's readiness to quit: [pre-contemplation/
contemplation/preparation/action]. Referral to [1-800-QUIT-NOW/local program]: 
[yes/discussed]. Next session: [scheduled/offered]."
```

**96127 Screening Instrument (when billing per instrument):**
```
"[PHQ-9/GAD-7/AUDIT-C/DAST-10/Edinburgh/ASQ] administered and scored. 
Instrument: [NAME]. Score: [NUMERIC SCORE/MAX POSSIBLE]. Clinical 
interpretation: [NEGATIVE/POSITIVE/BORDERLINE]. Follow-up plan: [PLAN]. 
This screening was conducted as a separately identifiable service."
```

**G0447 Obesity IBT (Plan section):**
```
"Intensive behavioral therapy for obesity provided today. Current BMI: [X]. 
Counseling addressed: dietary assessment, physical activity barriers and goals, 
behavior change strategies, motivational enhancement. Session [X] — frequency: 
[weekly (sessions 1-13) / biweekly (sessions 14-22) / monthly (sessions 23-26)]. 
Patient demonstrated [understanding/commitment to] behavior modification goals."
```

**G0446 CVD Risk Reduction (Plan section):**
```
"Intensive behavioral therapy for cardiovascular disease prevention provided 
today. Addressed: aspirin appropriateness assessment, diet modification 
counseling for CVD risk reduction, physical activity recommendations for 
cardiovascular benefit. Annual session."
```

**99417 Prolonged Services (time documentation):**
```
"Total time on date of service: [XX] minutes. This exceeds the time threshold 
for [99215 (54 min) / 99205 (74 min)]. The additional [XX] minutes beyond 
threshold is claimed as prolonged service under 99417. Time breakdown: 
history/exam [XX] min, reviewing records/data [XX] min, care coordination 
[XX] min, documentation [XX] min."
```

### 3C — Phrase Library Integration

The phrase library must be integrated into CareCompanion at the following touch points:

1. **Pre-Visit Prep Panel:** When a billing opportunity is flagged, the relevant
   phrase template appears as an expandable section labeled "Documentation
   language — click to copy." A single button copies it to clipboard.

2. **During-Encounter Alert Bar:** When an opportunity is accepted during visit,
   the phrase appears with an "Insert into AC" button that uses the existing
   AC PyAutoGUI automation to paste the text into the appropriate Amazing Charts
   note section (Assessment or Plan, depending on phrase_category).

3. **Post-Visit Summary:** Any opportunity that was accepted but whose
   documentation phrase was not used generates a reminder: "Remember to document
   [code] language in your note before signing."

4. **Phrase Customization:** The provider can edit any phrase in the library
   via `/settings/phrases`. Edited phrases are marked `is_customized=True` and
   are preserved across application updates.

---

## PART 4 — TCM DISCHARGE WATCH ENGINE

TCM is the single highest-value time-sensitive opportunity in the system.
99496 = $280 per qualifying discharge. Missing the 2-business-day contact
window means the code cannot be billed. This requires a proactive monitoring
system, not a reactive one.

### 4A — TCM Watch List

New model: `TCMWatchEntry`
```
id, patient_id (FK), patient_name, discharge_date, discharge_facility,
discharge_summary_received (bool), two_day_contact_deadline (date),
two_day_contact_completed (bool), two_day_contact_date, two_day_contact_method,
fourteen_day_visit_deadline (date), face_to_face_completed (bool),
face_to_face_date, tcm_code_eligible ('99495'|'99496'|'expired'),
tcm_billed (bool), status ('active'|'contact_overdue'|'visit_overdue'|
'complete'|'expired'|'dismissed'), created_at, notes
```

### 4B — Discharge Detection Sources

The system must check three sources daily for new discharges:

**Source 1 — AC Inbox monitor:**
The existing inbox monitoring service already watches for new chart items.
Add a pattern match for: discharge summary, hospital summary, SNF discharge,
observation discharge. When a document matching these patterns is detected,
create a new `TCMWatchEntry` with a 2-business-day contact alert.

**Source 2 — Morning briefing manual entry:**
In the morning briefing dashboard, add a section: "Did any patients discharge
over the weekend/since your last session?" with a quick-add form: patient name,
facility, discharge date. This covers gaps when the fax isn't monitored on weekends.

**Source 3 — Scheduled reminder for known hospitalizations:**
If the provider previously flagged a patient as hospitalized (via the
encounter notes or a manual flag), generate a TCM watch entry when the
expected discharge date arrives.

### 4C — TCM Alert Behavior

The TCM alert must be:
- **Critical priority** (highest alert level in the system)
- Displayed at the TOP of the morning briefing, above all other content
- Displayed as a banner on the Today View whenever an active TCM watch entry
  exists within 1 business day of the contact deadline
- Color-coded: yellow = 2 days remaining, red = deadline today, gray = overdue
  (missed window, code no longer billable — document anyway for care quality)

---

## PART 5 — CCM ENROLLMENT AND TIME TRACKING ENGINE

CCM is the highest-value recurring monthly revenue in the system.
Each enrolled patient generates $62/month in receipts without requiring
a face-to-face visit. 20 enrolled patients = $1,240/month = $3,720/quarter.

### 5A — CCM Patient Registry Model

New model: `CCMEnrollment`
```
id, patient_id (FK), enrollment_date, consent_date, consent_method,
consent_document_location, care_plan_date, care_plan_location,
qualifying_conditions (JSON — ICD-10 codes), monthly_time_goal (int, default=20),
status ('enrolled'|'eligible_not_enrolled'|'declined'|'disenrolled'),
disenrollment_date, disenrollment_reason, billing_provider,
last_billed_month (date), total_billed_months (int)
```

New model: `CCMTimeEntry`
```
id, enrollment_id (FK), patient_id (FK), entry_date, duration_minutes,
activity_type ('care_plan_review'|'medication_management'|'coordination'|
'patient_communication'|'caregiver_communication'|'provider_review'),
staff_name, staff_role ('provider'|'rn'|'ma'|'care_coordinator'),
activity_description, is_billable (bool, default=True)
```

### 5B — CCM Workflow Integration

1. **Eligibility Detection:** The `ccm.py` detector flags every patient with ≥2
   qualifying chronic conditions as CCM-eligible. This creates a pending entry
   in the CCM Patient Registry with status `eligible_not_enrolled`.

2. **Enrollment Prompt:** At the pre-visit prep panel, if a patient is
   `eligible_not_enrolled`, show a one-click action: "Enroll in CCM — requires
   consent today." This triggers a documentation checklist: verbal/written
   consent, care plan establishment, billing provider selection.

3. **Monthly Time Tracker:** For enrolled patients, a sidebar panel in the
   patient chart view shows: "CCM time this month: [X] of 20 minutes."
   A quick-add button logs time entries in 5-minute increments with activity type.
   When 20 minutes is reached: "CCM billable this month — 99490 ready."
   When 50 minutes is reached: "99439 add-on also billable."

4. **End-of-Month Alert:** On the last business day of each month, the morning
   briefing shows a CCM billing readiness list: all enrolled patients, their
   monthly time, and whether they are ready to bill. Patients NOT reaching
   20 minutes are shown with a yellow flag.

5. **CCM Billing Roster Export:** A printable/exportable list formatted for
   submission to the billing department, showing: patient name, MRN, month,
   code (99490/99491/99439), time logged, qualifying conditions, consent date.

---

## PART 6 — CHRONIC MONITORING LAB CALENDAR

The chronic monitoring engine does more than flag overdue labs — it generates
a proactive lab scheduling calendar that ensures labs arrive before visits,
not after.

### 6A — Monitoring Schedule Model

New model: `MonitoringSchedule`
```
id, patient_id (FK), lab_code (CPT), lab_name, monitoring_rule_code,
clinical_indication (ICD-10), last_performed_date, next_due_date,
interval_days (int), priority ('urgent'|'routine'|'annual'),
status ('current'|'due_soon'|'overdue'|'ordered'|'resulted'),
order_placed_date, result_received_date, last_result_value,
last_result_units, last_result_flag ('normal'|'abnormal'|'critical')
```

### 6B — Lab Scheduling Intelligence

The lab calendar must do the following:

1. **Pre-Visit Proactive Ordering:** At the morning briefing, for every
   patient scheduled today who has a lab coming due within 30 days, show:
   "Consider ordering [LAB] today — due [DATE] for [INDICATION]."
   Pre-visit lab ordering means results are available at the next visit.

2. **In-Visit Lab Pairing:** When a patient with an active monitoring
   schedule is seen, the during-encounter panel shows: "Labs due this visit:
   [LIST]." Ordering them during the visit generates a venipuncture charge
   (36415) if drawn in-office.

3. **Overdue Lab Alert:** Patients with overdue monitoring labs who have NOT
   been seen in 30+ days generate a proactive outreach flag: "Overdue labs —
   consider phone or portal contact."

4. **Billing Cross-Reference:** Every monitoring lab is tagged with its CPT
   billing code and revenue estimate. The lab calendar display shows:
   "Drawing these labs today adds approximately $[X] in charges."

---

## PART 7 — PREVENTIVE SERVICE COMPLETION TRACKER

Beyond individual billing flags, the system must maintain a lifetime
preventive service record for every patient — not just what is overdue today,
but the entire longitudinal screening history.

### 7A — Preventive Service Record Model

New model: `PreventiveServiceRecord`
```
id, patient_id (FK), service_code (FK to BillingRule.opportunity_code),
service_name, cpt_hcpcs_code, service_date, next_due_date, result_summary,
performed_by ('practice'|'specialist'|'patient_reported'|'unknown'),
billing_status ('billed'|'referred'|'patient_declined'|'not_applicable'),
payer_at_time_of_service, notes
```

### 7B — Care Gap Dashboard

A `/care-gaps` route displays the complete preventive service status for
every patient, organized by:

1. **Today's Schedule — Preventive Opportunities:**
   For each patient today, every eligible preventive service not yet done
   this year, sorted by revenue impact.

2. **Panel-Wide Gaps:**
   Aggregated view: "Of your [X] Medicare patients, [Y] are overdue for AWV —
   estimated revenue if all were completed: $[Z]." Same for each service type.

3. **HEDIS/Quality Metric Tracker:**
   Many preventive services are also quality metrics (HEDIS measures) that
   affect Medicare Advantage star ratings and value-based care bonuses. Track:
   - Diabetes A1C control (<8%) — HEDIS CDC
   - Breast cancer screening rates — HEDIS BCS
   - Colorectal cancer screening — HEDIS COL
   - Depression screening and follow-up — HEDIS DSF
   - Hypertension control (<140/90) — HEDIS CBP
   These are tracked separately from billing but surface in the care gap
   dashboard as both quality and revenue opportunities.

---

## PART 8 — REVENUE REPORTING AND BONUS PROJECTION DASHBOARD

### 8A — Monthly Revenue Report

A `/reports/revenue/[year]/[month]` route generates a monthly billing
intelligence report showing:

- **Detected opportunities:** Count and estimated revenue by category
- **Captured opportunities:** Count and estimated revenue by category
- **Capture rate by category:** (captured / detected) × 100%
- **Revenue gap:** Estimated revenue left on the table this month
- **Running bonus impact:** How much this month's captured revenue moved the
  bonus trajectory
- **Top missed opportunities:** The 10 highest-value dismissed or not-actioned
  opportunities with their reasons

### 8B — Quarterly Projection Model

The first-bonus-quarter projection engine (defined in Part 2, Component 3)
must be surfaced in three places:

1. The /bonus dashboard (detailed, with scenario comparison)
2. The morning briefing (one-line summary: "Q3 2027 projected first bonus
   at current pace / Q2 2027 with full billing optimization")
3. The monthly revenue report footer (updated projection with that month's
   data incorporated)

### 8C — Annual Billing Opportunity Value Report

Once per year (or on demand), generate a report showing:

- Estimated annual revenue impact of each billing category if fully implemented
- Current capture rate per category
- Dollar difference between current state and full capture
- Prioritized recommendation list: "Implementing CCM for the next 10 eligible
  patients would add $7,440/year in receipts and move your first bonus quarter
  from Q3 2027 to Q2 2027."

---

## PART 9 — IMMUNIZATION SERIES COMPLETION ENGINE

Immunizations are unique because they involve series — a patient who received
dose 1 of Shingrix but not dose 2 is a time-sensitive opportunity that
generates $200+ in revenue when the series is completed.

### 9A — Series Tracking Logic

The `immunizations.py` detector must track not just whether a vaccine is
due, but WHERE IN THE SERIES the patient is, and when the next dose window opens:

For each multi-dose series:
- Shingrix (Zoster): Dose 1 administered → flag dose 2 due in 2-6 months
- Hepatitis B (Engerix-B 2-dose adult): Dose 1 → dose 2 at 1 month
- Hepatitis A: Dose 1 → dose 2 at 6-18 months
- HPV: Dose 1 → dose 2 at 1-2 months, dose 3 at 6 months (3-dose schedule)
- COVID: Per current ACIP schedule

The series tracker displays:
"[Patient Name] — Shingrix series in progress. Dose 1: [DATE]. Dose 2 window:
[DATE RANGE]. Schedule at next available appointment."

### 9B — Recall System Integration

The immunization engine must generate patient recall flags for:
- Patients with incomplete series where the next dose window is NOW open
- Patients overdue for annual flu vaccination (September–March)
- Patients who are newly 50, 60, or 65 and newly eligible for age-gated vaccines

These generate entries in the existing reminder/follow-up system.

---

## PART 10 — PORTAL MESSAGE AND TELEPHONE TIME TRACKING

Online digital E/M (99421-99423) and telephone E/M (99441-99443) are among
the most consistently underbilled codes in primary care. Every substantive
patient-initiated portal message and every clinical phone call that exceeds
5 minutes and does not result in a face-to-face visit within 24 hours is
potentially billable.

### 10A — Communication Log Model

New model: `CommunicationLog`
```
id, patient_id (FK), communication_type ('portal_message'|'telephone'|'video'),
initiated_by ('patient'|'provider'|'staff'), start_datetime, end_datetime,
cumulative_minutes (int — for portal messages, aggregated over 7 days),
clinical_decision_made (bool), resulted_in_visit (bool), resulted_in_visit_date,
billable_code (nullable — 99421/99422/99423 or 99441/99442/99443),
billing_status ('pending_review'|'billed'|'not_billable'|'below_threshold'),
notes
```

### 10B — Detection Logic

**Portal messages:** Aggregate all messages in a 7-day window. If cumulative
clinical time exceeds 5 minutes and the patient did not have a face-to-face
visit within 24 hours of the first message:
- 5-10 min: 99421 ($20)
- 11-20 min: 99422 ($34)
- >20 min: 99423 ($50)

**Telephone calls:** If call duration exceeds 5 minutes AND call involved
medical decision-making AND patient was not seen within 24 hours:
- 5-10 min: 99441 ($25)
- 11-20 min: 99442 ($40)
- 21-30 min: 99443 ($65)

The timer integration must make it easy for the provider to log time spent
on messages and calls without disrupting clinical workflow.

---

## PART 11 — IMPLEMENTATION PLAN AND SEQUENCING

The plan must produce a phased implementation sequence for everything above,
organized as follows:

### Phase 1 (Weeks 1-2): Foundation and Immediate High-Value Codes
- BonusTracker model + /bonus dashboard (basic version: manual entry + display)
- BillingRule + BillingOpportunity models (confirm or create)
- G2211 detector (em_addons.py) — flags on every Medicare E/M
- Modifier-25 prompt (em_addons.py) — flags same-day E/M + procedure/preventive
- AWV detector (awv.py) — G0402/G0438/G0439 + basic add-on stack
- Venipuncture detector (procedures.py) — 36415 on every in-office blood draw
- Injection administration detector (procedures.py) — 96372 + 90471/90472
- Phrase library model + seed data for G2211, modifier-25, AWV, TCM
- Bonus impact number on all existing billing cards
- **Estimated bonus impact: $3,000-6,000/quarter in captured receipts**

### Phase 2 (Weeks 3-4): Recurring Monthly Revenue
- CCM enrollment engine (ccm.py + CCMEnrollment + CCMTimeEntry models)
- TCM discharge watch (tcm.py + TCMWatchEntry + discharge detection)
- All screening instrument detectors (screenings.py) — 96127, G0444, G0442
- Chronic monitoring lab calendar (chronic_monitoring.py + MonitoringSchedule)
- Tobacco cessation detector (counseling.py) — 99406/99407
- PHQ/GAD/AUDIT phrase templates
- CCM enrollment impact calculator in /bonus dashboard
- **Estimated bonus impact: $5,000-12,000/quarter (especially CCM)**

### Phase 3 (Weeks 5-6): Preventive Service Gap Engine
- All preventive lab screening detectors (preventive_labs.py — 14 rules)
- Preventive service record model + /care-gaps dashboard
- Immunization gap detection + series tracking (immunizations.py)
- Full AWV add-on stack (ACP, CVD IBT, obesity IBT, EKG, SDOH)
- Quarter-end surge mode in /bonus dashboard
- **Estimated bonus impact: $2,000-4,000/quarter in previously missed codes**

### Phase 4 (Weeks 7-8): Behavioral Health, Telehealth, Pediatrics
- BHI/CoCM workflow (bhi.py)
- Communication log + telephone/portal E/M tracking (telehealth.py)
- Pediatric Bright Futures engine (pediatric.py)
- SDOH screening detector (sdoh.py)
- Care plan oversight (misc.py — home health patients)
- **Estimated bonus impact: $1,000-3,000/quarter**

### Phase 5 (Weeks 9-10): Reporting and Intelligence
- Monthly revenue report (/reports/revenue/)
- Annual billing opportunity value report
- Bonus projection model with dual-scenario display
- HEDIS/quality metric tracker in care gaps dashboard
- Phrase library UI for customization (/settings/phrases)
- First-bonus-quarter projection in morning briefing
- **Impact: Visibility into the full revenue opportunity and trajectory**

---

## PART 12 — DEMO MODE SPECIFICATIONS

The full system must be demonstrable without live AC data. Update the
existing demo data layer to include:

- 5 demo patients representing the primary demographic groups:
  1. Medicare patient (68F): HTN + DM2 + CKD3 + HLD — triggers CCM, AWV
     overdue, G2211 on every visit, UACR due, multiple screening gaps
  2. Medicare patient (72M): CAD + HFrEF + COPD + depression — triggers TCM
     (recent hospital discharge), BHI, CCM, Shingrix dose 2 due
  3. Commercial patient (44F): Obesity (BMI 34) + anxiety + tobacco — triggers
     G0447, 99407, GAD-7, modifier-25 scenario
  4. Medicaid patient (28F): ADHD + pregnancy 26wk — triggers GDM screening,
     bacteriuria, Tdap this pregnancy, prenatal depression screening
  5. Self-pay patient (55M): HTN + pre-diabetes + tobacco — triggers 99406,
     diabetes screening, lipid panel, ASCVD risk calculation, statin counseling

- Pre-populated BonusTracker data showing Q1 2026 with $6,000 receipts
  (22 working days from March 2 start) and the resulting cumulative deficit
- Demo billing opportunities pre-detected for all 5 patients
- Demo phrase library fully populated
- Demo TCM watch entry showing a "2-day contact deadline: TODAY" alert

---

## OUTPUT FORMAT

Produce the plan in the following structure:

1. **Audit Summary** (answers to the 7 pre-plan questions from Step 0)
2. **Data Layer Gap Analysis** (AC XML parser completeness table)
3. **Phased Implementation Plan** (Phases 1-5 as specified above)
   - For each phase: list every file to be created or modified, describe
     every change, and provide an effort estimate in hours
4. **Model Definitions** (complete SQLAlchemy class definitions for every
   new model)
5. **Dependency Map** (which phases depend on which other phases; which are
   blocked on API key approval vs buildable in demo mode immediately)
6. **Sequencing Recommendation** (recommended order if the provider has
   limited development time and wants maximum bonus impact per hour invested)

Do not write any code. Produce only the plan. When complete, ask for
confirmation before beginning implementation.
