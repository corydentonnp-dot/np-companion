"""
CareCompanion — Comprehensive Test Patient Seeder

Generates 35 fake patients covering ALL billing detectors (26),
all care gap rules (20), all payer types, pediatric scenarios,
edge cases, and false-positive controls.

Usage:
    venv\\Scripts\\python.exe scripts/seed_test_data.py
    venv\\Scripts\\python.exe scripts/seed_test_data.py --clear

Or import and call:
    seed_all_test_data(user_id)
    clear_test_data(user_id)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# Helper builders — keep patient definitions compact
# ---------------------------------------------------------------------------

def _med(name, dosage='', instructions='', generic='', start='01/01/2025',
         status='Active', rxnorm=''):
    """Build a medication dict matching CDA table column format."""
    label = f'{name}, [RxNorm: {rxnorm}]' if rxnorm else name
    return {
        'Medication': label,
        'Generic Name': generic,
        'Instructions': instructions,
        'Dosage': dosage,
        'Start Date': start,
        'Status': status,
        'Date Inactivated': '--',
    }


def _dx(problem, icd10='', status='Active', started='01/01/2024'):
    """Build a diagnosis dict matching CDA table column format."""
    label = f'{problem} [ICD10: {icd10}]' if icd10 else problem
    return {
        'Problem': label,
        'Problem Status': status,
        'Date Started': started,
        'Date Resolved': '--',
        'Date Inactivated': '--',
    }


def _allergy(substance, reaction='--', severity='--'):
    return {
        'Substance': substance,
        'Reaction': reaction,
        'Severity': severity,
        'Status': 'Active',
    }


def _imm(vaccine, date=''):
    return {'Vaccine': vaccine, 'Date': date, 'Status': 'Completed'}


def _vitals(encounter='03/01/2026 10:00:00', height='', weight='', bmi='',
            bp_sys='', bp_dia='', hr='', o2='', temp='', rr=''):
    return {
        'Encounter': encounter,
        'Height (in)': height,
        'Weight (lb)': weight,
        'BMI (kg/m2)': bmi,
        'BP Sys (mmHg)': bp_sys,
        'BP Dias (mmHg)': bp_dia,
        'Heart Rate (/min)': hr,
        'O2 % BldC Oximetry': o2,
        'Body Temperature': temp,
        'Respiratory Rate (/min)': rr,
    }


def _patient(mrn, name, dob, sex, insurer, meds=None, diagnoses=None,
             allergies=None, immunizations=None, vitals=None):
    """Build a complete patient dict for store_parsed_summary()."""
    return {
        'patient_mrn': mrn,
        'patient_name': name,
        'patient_dob': dob,
        'patient_sex': sex,
        'insurer_type': insurer,
        'medications': meds or [],
        'diagnoses': diagnoses or [],
        'allergies': allergies or [],
        'immunizations': immunizations or [],
        'vitals': vitals or [],
        'lab_results': [],
        'social_history': [],
        'encounter_reason': [],
        'instructions': [],
        'goals': [],
        'health_concerns': [],
        'patient_demographics': [],
        'insurance': [],
    }


# ======================================================================
# 35 Fake Patients — Coverage Matrix
# ======================================================================
#
# Billing detectors hit:
#   awv (1,6,21,30,35), ccm (1,4,5,13,15,21,24,25,28,30,34,35),
#   bhi (5,11,15,17,21,26), cocm (17), chronic_monitoring (4,5,34),
#   tcm (18), rpm (4,16,24,34), cognitive (6,21,28), tobacco (10,20),
#   alcohol (8), obesity (3,8,11,16,20,34), pediatric (14,22,33),
#   vaccine_admin (14,22,33), screening (19,27), sdoh (26),
#   sti (19,27), telehealth (31), g2211 (31), em_addons (31),
#   prolonged (21,24,35), preventive (all via care gaps),
#   procedures (misc), acp (28), counseling (misc), care_gaps (all)
#
# Care gap rules hit:
#   All 20 USPSTF rules are triggered by at least 2 patients.
#
# Payer types: Medicare (1,2,6,10,13,18,24,28,30,35),
#   Commercial (3,4,7,8,12,16,19,20,23,29,32),
#   Medicaid (9,14,22,27,33), Medicare Advantage (5,15,25,31,34)
#
# False-positive control: 90029 (healthy, acute-only visit)
# ======================================================================

FAKE_PATIENTS = [
    # ------------------------------------------------------------------
    # 90001 — Margaret Wilson, 67F, Medicare
    # AWV, CCM (4 chronic), DEXA, mammogram, colonoscopy, pneumococcal,
    # fall risk, depression, shingrix, flu, COVID, tdap
    # ------------------------------------------------------------------
    _patient('90001', 'Margaret Wilson', '19580412', 'F', 'medicare',
        meds=[
            _med('lisinopril 10 mg tablet', '10 mg', 'Take once daily', rxnorm='314076'),
            _med('metformin 500 mg tablet', '500 mg', 'Take twice daily', rxnorm='861004'),
            _med('atorvastatin 20 mg tablet', '20 mg', 'Take at bedtime', rxnorm='259255'),
            _med('alendronate 70 mg tablet', '70 mg', 'Take weekly on empty stomach', rxnorm='824868'),
        ],
        diagnoses=[
            _dx('Essential hypertension', 'I10'),
            _dx('Type 2 diabetes mellitus without complications', 'E11.9'),
            _dx('Hyperlipidemia, unspecified', 'E78.5'),
            _dx('Age-related osteoporosis without fracture', 'M81.0'),
        ],
        allergies=[_allergy('Penicillin', 'Rash', 'Moderate')],
        immunizations=[
            _imm('Influenza vaccine', '10/15/2024'),
        ],
        vitals=[_vitals(height='64', weight='155', bmi='26.6',
                        bp_sys='142', bp_dia='84', hr='76', o2='97')],
    ),

    # ------------------------------------------------------------------
    # 90002 — Robert Thompson, 65M, Medicare
    # Lung LDCT (former heavy smoker), AAA screen, colonoscopy,
    # pneumococcal, fall risk, flu
    # ------------------------------------------------------------------
    _patient('90002', 'Robert Thompson', '19600918', 'M', 'medicare',
        meds=[
            _med('tiotropium 18 mcg capsule', '18 mcg', 'Inhale once daily', rxnorm='274535'),
            _med('amlodipine 5 mg tablet', '5 mg', 'Take once daily', rxnorm='329528'),
        ],
        diagnoses=[
            _dx('Chronic obstructive pulmonary disease with acute exacerbation', 'J44.1'),
            _dx('Essential hypertension', 'I10'),
            _dx('Nicotine dependence, cigarettes', 'F17.210'),
            _dx('Personal history of nicotine dependence', 'Z87.891'),
        ],
        allergies=[_allergy('Aspirin', 'GI upset', 'Mild')],
        immunizations=[],
        vitals=[_vitals(height='70', weight='185', bmi='26.5',
                        bp_sys='148', bp_dia='90', hr='82', o2='93')],
    ),

    # ------------------------------------------------------------------
    # 90003 — Maria Garcia, 35F, Commercial
    # Cervical pap, cervical pap/HPV, depression, diabetes screen
    # (overweight), lipid screening, mammogram (age 40 - not yet)
    # ------------------------------------------------------------------
    _patient('90003', 'Maria Garcia', '19900605', 'F', 'commercial',
        meds=[
            _med('buspirone 10 mg tablet', '10 mg', 'Take twice daily', rxnorm='104894'),
            _med('norgestimate-ethinyl estradiol tablet', '', 'Take once daily', rxnorm='749762'),
        ],
        diagnoses=[
            _dx('Generalized anxiety disorder', 'F41.1'),
            _dx('Morbid obesity due to excess calories', 'E66.01'),
        ],
        allergies=[],
        immunizations=[
            _imm('COVID-19 vaccine', '09/01/2025'),
            _imm('Tdap vaccine', '03/10/2023'),
        ],
        vitals=[_vitals(height='63', weight='210', bmi='37.2',
                        bp_sys='128', bp_dia='78', hr='80', o2='98')],
    ),

    # ------------------------------------------------------------------
    # 90004 — James Chen, 55M, Commercial
    # CCM (3 chronic), chronic monitoring, RPM candidate, colonoscopy,
    # lipid, diabetes, shingrix
    # ------------------------------------------------------------------
    _patient('90004', 'James Chen', '19700303', 'M', 'commercial',
        meds=[
            _med('insulin glargine 100 units/mL', '30 units', 'Inject at bedtime', rxnorm='261551'),
            _med('metformin 1000 mg tablet', '1000 mg', 'Take twice daily', rxnorm='861004'),
            _med('losartan 50 mg tablet', '50 mg', 'Take once daily', rxnorm='979480'),
            _med('empagliflozin 10 mg tablet', '10 mg', 'Take once daily', rxnorm='1545684'),
        ],
        diagnoses=[
            _dx('Type 2 diabetes with diabetic CKD', 'E11.65'),
            _dx('Chronic kidney disease, stage 3', 'N18.3'),
            _dx('Essential hypertension', 'I10'),
        ],
        allergies=[_allergy('Sulfonamides', 'Anaphylaxis', 'Severe')],
        immunizations=[
            _imm('Influenza vaccine', '10/01/2025'),
            _imm('Shingrix dose 1', '06/15/2025'),
        ],
        vitals=[_vitals(height='68', weight='190', bmi='28.9',
                        bp_sys='136', bp_dia='82', hr='78', o2='97')],
    ),

    # ------------------------------------------------------------------
    # 90005 — Patricia Davis, 70F, Medicare Advantage
    # CCM (4+ chronic), BHI (depression), chronic monitoring,
    # mammogram, colonoscopy, fall risk, DEXA
    # ------------------------------------------------------------------
    _patient('90005', 'Patricia Davis', '19550814', 'F', 'medicare_advantage',
        meds=[
            _med('warfarin 5 mg tablet', '5 mg', 'Take once daily', rxnorm='855318'),
            _med('metoprolol succinate 50 mg tablet', '50 mg', 'Take once daily', rxnorm='866924'),
            _med('furosemide 40 mg tablet', '40 mg', 'Take once daily', rxnorm='197417'),
            _med('lisinopril 20 mg tablet', '20 mg', 'Take once daily', rxnorm='314077'),
            _med('sertraline 100 mg tablet', '100 mg', 'Take once daily', rxnorm='312940'),
        ],
        diagnoses=[
            _dx('Heart failure, unspecified', 'I50.9'),
            _dx('Atrial fibrillation', 'I48.91'),
            _dx('Essential hypertension', 'I10'),
            _dx('Major depressive disorder, single episode, moderate', 'F32.1'),
        ],
        allergies=[
            _allergy('Codeine', 'Nausea/vomiting', 'Moderate'),
            _allergy('Latex', 'Contact dermatitis', 'Mild'),
        ],
        immunizations=[
            _imm('Influenza vaccine', '10/20/2025'),
            _imm('Pneumococcal PCV20', '04/15/2024'),
        ],
        vitals=[_vitals(height='62', weight='170', bmi='31.1',
                        bp_sys='130', bp_dia='76', hr='68', o2='95')],
    ),

    # ------------------------------------------------------------------
    # 90006 — David Williams, 80M, Medicare
    # Cognitive assessment, fall risk, pneumococcal, AWV
    # ------------------------------------------------------------------
    _patient('90006', 'David Williams', '19450701', 'M', 'medicare',
        meds=[
            _med('donepezil 10 mg tablet', '10 mg', 'Take at bedtime', rxnorm='997221'),
            _med('tamsulosin 0.4 mg capsule', '0.4 mg', 'Take once daily', rxnorm='313988'),
            _med('amlodipine 10 mg tablet', '10 mg', 'Take once daily', rxnorm='329526'),
            _med('acetaminophen 500 mg tablet', '500 mg', 'Take every 6 hours as needed', rxnorm='313782'),
        ],
        diagnoses=[
            _dx('Unspecified dementia without behavioral disturbance', 'F03.90'),
            _dx('Essential hypertension', 'I10'),
            _dx('Benign prostatic hyperplasia', 'N40.0'),
            _dx('Primary osteoarthritis, right knee', 'M17.11'),
        ],
        allergies=[_allergy('Ibuprofen', 'GI bleeding', 'Severe')],
        immunizations=[
            _imm('Influenza vaccine', '10/01/2025'),
            _imm('Shingrix dose 1', '01/15/2025'),
            _imm('Shingrix dose 2', '04/15/2025'),
        ],
        vitals=[_vitals(height='69', weight='175', bmi='25.8',
                        bp_sys='150', bp_dia='78', hr='72', o2='96')],
    ),

    # ------------------------------------------------------------------
    # 90007 — Linda Brown, 43F, Commercial
    # Mammogram (40+), cervical pap, depression screen
    # ------------------------------------------------------------------
    _patient('90007', 'Linda Brown', '19820220', 'F', 'commercial',
        meds=[
            _med('levothyroxine 75 mcg tablet', '75 mcg', 'Take on empty stomach daily', rxnorm='895994'),
            _med('sumatriptan 50 mg tablet', '50 mg', 'Take as needed for migraine', rxnorm='313991'),
        ],
        diagnoses=[
            _dx('Hypothyroidism, unspecified', 'E03.9'),
            _dx('Migraine, unspecified, not intractable', 'G43.909'),
        ],
        allergies=[_allergy('Erythromycin', 'Nausea', 'Mild')],
        immunizations=[
            _imm('Tdap vaccine', '05/10/2022'),
            _imm('COVID-19 vaccine', '08/15/2025'),
        ],
        vitals=[_vitals(height='65', weight='145', bmi='24.1',
                        bp_sys='120', bp_dia='74', hr='70', o2='99')],
    ),

    # ------------------------------------------------------------------
    # 90008 — Michael Johnson, 50M, Commercial
    # Alcohol screening, shingrix (50+), colonoscopy (45+), lipid,
    # obesity counseling
    # ------------------------------------------------------------------
    _patient('90008', 'Michael Johnson', '19750515', 'M', 'commercial',
        meds=[
            _med('naltrexone 50 mg tablet', '50 mg', 'Take once daily', rxnorm='197446'),
            _med('thiamine 100 mg tablet', '100 mg', 'Take once daily', rxnorm='316151'),
        ],
        diagnoses=[
            _dx('Alcohol use disorder, moderate', 'F10.20'),
            _dx('Nonalcoholic steatohepatitis', 'K76.0'),
            _dx('Morbid obesity due to excess calories', 'E66.01'),
        ],
        allergies=[],
        immunizations=[],
        vitals=[_vitals(height='71', weight='265', bmi='37.0',
                        bp_sys='138', bp_dia='88', hr='86', o2='96')],
    ),

    # ------------------------------------------------------------------
    # 90009 — Jennifer Martinez, 25F, Medicaid
    # Cervical pap (21+), depression, HIV screen, flu, covid, tdap
    # ------------------------------------------------------------------
    _patient('90009', 'Jennifer Martinez', '20000115', 'F', 'medicaid',
        meds=[
            _med('albuterol 90 mcg/actuation inhaler', '', 'Inhale 2 puffs every 4-6h prn', rxnorm='801092'),
            _med('fluticasone 110 mcg/actuation inhaler', '', 'Inhale 2 puffs twice daily', rxnorm='896188'),
            _med('buspirone 5 mg tablet', '5 mg', 'Take twice daily', rxnorm='104894'),
        ],
        diagnoses=[
            _dx('Mild intermittent asthma, uncomplicated', 'J45.20'),
            _dx('Generalized anxiety disorder', 'F41.1'),
        ],
        allergies=[_allergy('Cats', 'Wheezing', 'Moderate')],
        immunizations=[
            _imm('Influenza vaccine', '11/01/2025'),
        ],
        vitals=[_vitals(height='64', weight='130', bmi='22.3',
                        bp_sys='112', bp_dia='68', hr='74', o2='98')],
    ),

    # ------------------------------------------------------------------
    # 90010 — William Anderson, 75M, Medicare
    # Lung LDCT (active smoker), AAA (male smoker 65-75), tobacco
    # cessation, CCM, colonoscopy, fall risk, pneumococcal
    # ------------------------------------------------------------------
    _patient('90010', 'William Anderson', '19500410', 'M', 'medicare',
        meds=[
            _med('gabapentin 300 mg capsule', '300 mg', 'Take three times daily', rxnorm='310429'),
            _med('metformin 500 mg tablet', '500 mg', 'Take twice daily', rxnorm='861004'),
            _med('lisinopril 20 mg tablet', '20 mg', 'Take once daily', rxnorm='314077'),
        ],
        diagnoses=[
            _dx('Type 2 diabetes mellitus without complications', 'E11.9'),
            _dx('Peripheral neuropathy, unspecified', 'G63'),
            _dx('Essential hypertension', 'I10'),
            _dx('Nicotine dependence, cigarettes', 'F17.210'),
        ],
        allergies=[_allergy('Morphine', 'Itching', 'Mild')],
        immunizations=[],
        vitals=[_vitals(height='72', weight='180', bmi='24.4',
                        bp_sys='152', bp_dia='88', hr='78', o2='94')],
    ),

    # ------------------------------------------------------------------
    # 90011 — Susan Taylor, 37F, Commercial
    # BHI (depression), cervical pap/HPV (30+), diabetes screen
    # (overweight), depression screen, lipid
    # ------------------------------------------------------------------
    _patient('90011', 'Susan Taylor', '19880328', 'F', 'commercial',
        meds=[
            _med('duloxetine 60 mg capsule', '60 mg', 'Take once daily', rxnorm='596926'),
            _med('topiramate 50 mg tablet', '50 mg', 'Take twice daily', rxnorm='38404'),
        ],
        diagnoses=[
            _dx('Major depressive disorder, recurrent, moderate', 'F33.1'),
            _dx('Morbid obesity due to excess calories', 'E66.01'),
            _dx('Prediabetes', 'R73.03'),
        ],
        allergies=[_allergy('Latex', 'Hives', 'Moderate')],
        immunizations=[
            _imm('COVID-19 vaccine', '07/20/2025'),
        ],
        vitals=[_vitals(height='66', weight='220', bmi='35.5',
                        bp_sys='124', bp_dia='80', hr='82', o2='98')],
    ),

    # ------------------------------------------------------------------
    # 90012 — Thomas Harris, 60M, Commercial
    # Colonoscopy (45+), lipid, shingrix (50+), depression screen
    # ------------------------------------------------------------------
    _patient('90012', 'Thomas Harris', '19650122', 'M', 'commercial',
        meds=[
            _med('allopurinol 300 mg tablet', '300 mg', 'Take once daily', rxnorm='197319'),
            _med('colchicine 0.6 mg tablet', '0.6 mg', 'Take as needed for flares', rxnorm='197445'),
            _med('lisinopril 10 mg tablet', '10 mg', 'Take once daily', rxnorm='314076'),
            _med('rosuvastatin 10 mg tablet', '10 mg', 'Take at bedtime', rxnorm='859747'),
        ],
        diagnoses=[
            _dx('Gout, unspecified', 'M10.9'),
            _dx('Essential hypertension', 'I10'),
            _dx('Hyperlipidemia, unspecified', 'E78.5'),
        ],
        allergies=[],
        immunizations=[
            _imm('Tdap vaccine', '02/12/2020'),
        ],
        vitals=[_vitals(height='71', weight='200', bmi='27.9',
                        bp_sys='134', bp_dia='82', hr='74', o2='97')],
    ),

    # ------------------------------------------------------------------
    # 90013 — Barbara Clark, 85F, Medicare
    # CCM (4+ chronic), fall risk, DEXA, mammogram, pneumococcal,
    # cognitive screening, prolonged service
    # ------------------------------------------------------------------
    _patient('90013', 'Barbara Clark', '19400610', 'F', 'medicare',
        meds=[
            _med('furosemide 80 mg tablet', '80 mg', 'Take twice daily', rxnorm='197417'),
            _med('epoetin alfa 10000 units/mL', '', 'Inject subcutaneous weekly', rxnorm='205923'),
            _med('ferrous sulfate 325 mg tablet', '325 mg', 'Take once daily', rxnorm='310325'),
            _med('carvedilol 12.5 mg tablet', '12.5 mg', 'Take twice daily', rxnorm='200031'),
            _med('hydralazine 25 mg tablet', '25 mg', 'Take three times daily', rxnorm='197770'),
        ],
        diagnoses=[
            _dx('Chronic systolic heart failure', 'I50.22'),
            _dx('Chronic kidney disease, stage 4', 'N18.4'),
            _dx('Anemia, unspecified', 'D64.9'),
            _dx('Essential hypertension', 'I10'),
        ],
        allergies=[
            _allergy('ACE inhibitors', 'Angioedema', 'Severe'),
            _allergy('Shellfish', 'Anaphylaxis', 'Severe'),
        ],
        immunizations=[
            _imm('Influenza vaccine', '10/05/2025'),
            _imm('Pneumococcal PCV20', '03/20/2023'),
        ],
        vitals=[_vitals(height='60', weight='140', bmi='27.3',
                        bp_sys='158', bp_dia='72', hr='64', o2='93')],
    ),

    # ------------------------------------------------------------------
    # 90014 — Christopher Lee, 10M, Medicaid
    # Pediatric, well-child, vaccine admin
    # ------------------------------------------------------------------
    _patient('90014', 'Christopher Lee', '20150820', 'M', 'medicaid',
        meds=[
            _med('methylphenidate 10 mg tablet', '10 mg', 'Take every morning', rxnorm='312961'),
            _med('montelukast 5 mg chewable tablet', '5 mg', 'Take at bedtime', rxnorm='997501'),
            _med('albuterol 90 mcg/actuation inhaler', '', 'Inhale 2 puffs prn', rxnorm='801092'),
        ],
        diagnoses=[
            _dx('Attention-deficit hyperactivity disorder, predominantly inattentive type', 'F90.0'),
            _dx('Mild intermittent asthma, uncomplicated', 'J45.20'),
        ],
        allergies=[_allergy('Peanuts', 'Anaphylaxis', 'Severe')],
        immunizations=[
            _imm('Influenza vaccine', '10/15/2025'),
            _imm('Tdap vaccine', '08/20/2025'),
            _imm('IPV vaccine', '08/20/2025'),
        ],
        vitals=[_vitals(height='54', weight='72', bmi='17.3',
                        bp_sys='100', bp_dia='64', hr='88', o2='99')],
    ),

    # ------------------------------------------------------------------
    # 90015 — Elizabeth White, 53F, Medicare Advantage
    # BHI (depression), CCM, DEXA, shingrix, mammogram, cervical
    # pap/HPV, colonoscopy
    # ------------------------------------------------------------------
    _patient('90015', 'Elizabeth White', '19720415', 'F', 'medicare_advantage',
        meds=[
            _med('methotrexate 2.5 mg tablet', '2.5 mg', 'Take weekly as directed', rxnorm='105585'),
            _med('folic acid 1 mg tablet', '1 mg', 'Take once daily', rxnorm='315966'),
            _med('denosumab 60 mg/mL syringe', '', 'Inject subcutaneous every 6 months', rxnorm='993449'),
            _med('escitalopram 10 mg tablet', '10 mg', 'Take once daily', rxnorm='596926'),
        ],
        diagnoses=[
            _dx('Rheumatoid arthritis, unspecified', 'M06.9'),
            _dx('Age-related osteoporosis without fracture', 'M81.0'),
            _dx('Major depressive disorder, single episode, unspecified', 'F32.9'),
        ],
        allergies=[_allergy('NSAIDs', 'GI bleed', 'Severe')],
        immunizations=[
            _imm('Influenza vaccine', '10/10/2025'),
        ],
        vitals=[_vitals(height='65', weight='142', bmi='23.6',
                        bp_sys='118', bp_dia='72', hr='72', o2='98')],
    ),

    # ------------------------------------------------------------------
    # 90016 — Daniel Robinson, 57M, Commercial
    # RPM (CPAP monitoring), obesity counseling, colonoscopy, diabetes
    # screen (overweight), shingrix
    # ------------------------------------------------------------------
    _patient('90016', 'Daniel Robinson', '19680901', 'M', 'commercial',
        meds=[
            _med('lisinopril 20 mg tablet', '20 mg', 'Take once daily', rxnorm='314077'),
            _med('hydrochlorothiazide 25 mg tablet', '25 mg', 'Take once daily', rxnorm='310798'),
        ],
        diagnoses=[
            _dx('Obstructive sleep apnea', 'G47.33'),
            _dx('Morbid obesity due to excess calories', 'E66.01'),
            _dx('Essential hypertension', 'I10'),
        ],
        allergies=[],
        immunizations=[
            _imm('Tdap vaccine', '06/12/2019'),
        ],
        vitals=[_vitals(height='70', weight='285', bmi='40.9',
                        bp_sys='144', bp_dia='92', hr='84', o2='94')],
    ),

    # ------------------------------------------------------------------
    # 90017 — Nancy Walker, 40F, Commercial
    # BHI, CoCM, mammogram (40+), cervical pap, depression screen
    # ------------------------------------------------------------------
    _patient('90017', 'Nancy Walker', '19850707', 'F', 'commercial',
        meds=[
            _med('lithium carbonate 300 mg capsule', '300 mg', 'Take twice daily', rxnorm='197872'),
            _med('lamotrigine 100 mg tablet', '100 mg', 'Take once daily', rxnorm='197694'),
            _med('omeprazole 20 mg capsule', '20 mg', 'Take before breakfast', rxnorm='198053'),
        ],
        diagnoses=[
            _dx('Bipolar disorder, unspecified', 'F31.9'),
            _dx('Gastroesophageal reflux disease without esophagitis', 'K21.0'),
        ],
        allergies=[_allergy('Carbamazepine', 'Stevens-Johnson syndrome', 'Severe')],
        immunizations=[
            _imm('COVID-19 vaccine', '09/01/2025'),
        ],
        vitals=[_vitals(height='67', weight='158', bmi='24.7',
                        bp_sys='116', bp_dia='72', hr='68', o2='99')],
    ),

    # ------------------------------------------------------------------
    # 90018 — Matthew Hall, 70M, Medicare
    # TCM (transitional care — post-hospital), CCM, fall risk,
    # colonoscopy, shingrix
    # ------------------------------------------------------------------
    _patient('90018', 'Matthew Hall', '19550315', 'M', 'medicare',
        meds=[
            _med('furosemide 40 mg tablet', '40 mg', 'Take twice daily', rxnorm='197417'),
            _med('digoxin 0.125 mg tablet', '0.125 mg', 'Take once daily', rxnorm='197604'),
            _med('metformin 500 mg tablet', '500 mg', 'Take twice daily', rxnorm='861004'),
            _med('apixaban 5 mg tablet', '5 mg', 'Take twice daily', rxnorm='1364430'),
        ],
        diagnoses=[
            _dx('Heart failure, unspecified', 'I50.9'),
            _dx('Type 2 diabetes mellitus without complications', 'E11.9'),
            _dx('Atrial fibrillation', 'I48.91'),
        ],
        allergies=[_allergy('Warfarin', 'Excessive bleeding', 'Severe')],
        immunizations=[
            _imm('Influenza vaccine', '10/15/2025'),
        ],
        vitals=[_vitals(height='68', weight='195', bmi='29.7',
                        bp_sys='146', bp_dia='82', hr='72', o2='95')],
    ),

    # ------------------------------------------------------------------
    # 90019 — Karen Young, 33F, Commercial
    # STI screening, cervical pap/HPV (30+), HIV screen, depression
    # ------------------------------------------------------------------
    _patient('90019', 'Karen Young', '19920225', 'F', 'commercial',
        meds=[
            _med('norgestimate-ethinyl estradiol tablet', '', 'Take once daily', rxnorm='749762'),
        ],
        diagnoses=[],
        allergies=[],
        immunizations=[
            _imm('Tdap vaccine', '01/15/2023'),
        ],
        vitals=[_vitals(height='66', weight='140', bmi='22.6',
                        bp_sys='110', bp_dia='70', hr='72', o2='99')],
    ),

    # ------------------------------------------------------------------
    # 90020 — Steven King, 47M, Commercial
    # Tobacco cessation, obesity counseling, colonoscopy (45+),
    # diabetes screen (overweight)
    # ------------------------------------------------------------------
    _patient('90020', 'Steven King', '19780810', 'M', 'commercial',
        meds=[
            _med('duloxetine 60 mg capsule', '60 mg', 'Take once daily', rxnorm='596926'),
            _med('nicotine 14 mg/24hr patch', '', 'Apply one patch daily', rxnorm='198045'),
        ],
        diagnoses=[
            _dx('Chronic low back pain', 'M54.5'),
            _dx('Nicotine dependence, cigarettes', 'F17.210'),
            _dx('Morbid obesity due to excess calories', 'E66.01'),
        ],
        allergies=[_allergy('Tramadol', 'Seizure', 'Severe')],
        immunizations=[],
        vitals=[_vitals(height='69', weight='240', bmi='35.4',
                        bp_sys='140', bp_dia='90', hr='80', o2='96')],
    ),

    # ------------------------------------------------------------------
    # 90021 — Dorothy Wright, 77F, Medicare
    # CCM, BHI, fall risk, DEXA, cognitive, pneumococcal, AWV,
    # prolonged service (complex case)
    # ------------------------------------------------------------------
    _patient('90021', 'Dorothy Wright', '19480620', 'F', 'medicare',
        meds=[
            _med('carbidopa-levodopa 25-100 mg tablet', '', 'Take three times daily', rxnorm='197439'),
            _med('sertraline 50 mg tablet', '50 mg', 'Take once daily', rxnorm='312940'),
            _med('calcium carbonate 600 mg tablet', '600 mg', 'Take twice daily', rxnorm='318076'),
            _med('amlodipine 5 mg tablet', '5 mg', 'Take once daily', rxnorm='329528'),
        ],
        diagnoses=[
            _dx("Parkinson's disease", 'G20'),
            _dx('Major depressive disorder, recurrent, mild', 'F33.0'),
            _dx('Age-related osteoporosis without fracture', 'M81.0'),
            _dx('Essential hypertension', 'I10'),
        ],
        allergies=[_allergy('Metoclopramide', 'Dystonia', 'Severe')],
        immunizations=[
            _imm('Influenza vaccine', '10/01/2025'),
            _imm('Pneumococcal PCV20', '05/10/2024'),
        ],
        vitals=[_vitals(height='61', weight='125', bmi='23.6',
                        bp_sys='136', bp_dia='70', hr='66', o2='96')],
    ),

    # ------------------------------------------------------------------
    # 90022 — Andrew Lopez, 17M, Medicaid
    # Pediatric, HIV screen (15+), depression screen, vaccine admin
    # ------------------------------------------------------------------
    _patient('90022', 'Andrew Lopez', '20080430', 'M', 'medicaid',
        meds=[
            _med('insulin lispro 100 units/mL', '', 'Inject per sliding scale before meals', rxnorm='261542'),
            _med('insulin glargine 100 units/mL', '20 units', 'Inject at bedtime', rxnorm='261551'),
        ],
        diagnoses=[
            _dx('Type 1 diabetes mellitus without complications', 'E10.9'),
        ],
        allergies=[
            _allergy('Tree nuts', 'Anaphylaxis', 'Severe'),
            _allergy('Latex', 'Hives', 'Moderate'),
        ],
        immunizations=[
            _imm('Influenza vaccine', '10/20/2025'),
            _imm('Meningococcal vaccine', '08/01/2025'),
            _imm('HPV vaccine dose 2', '06/15/2025'),
        ],
        vitals=[_vitals(height='66', weight='145', bmi='23.4',
                        bp_sys='118', bp_dia='72', hr='76', o2='99')],
    ),

    # ------------------------------------------------------------------
    # 90023 — Carol Scott, 63F, Commercial
    # Mammogram (high priority — breast cancer hx), cervical pap,
    # colonoscopy, depression, shingrix
    # ------------------------------------------------------------------
    _patient('90023', 'Carol Scott', '19620914', 'F', 'commercial',
        meds=[
            _med('tamoxifen 20 mg tablet', '20 mg', 'Take once daily', rxnorm='312260'),
            _med('lisinopril 10 mg tablet', '10 mg', 'Take once daily', rxnorm='314076'),
            _med('lorazepam 0.5 mg tablet', '0.5 mg', 'Take as needed for anxiety', rxnorm='197901'),
        ],
        diagnoses=[
            _dx('Personal history of breast cancer', 'Z85.3'),
            _dx('Essential hypertension', 'I10'),
            _dx('Generalized anxiety disorder', 'F41.1'),
        ],
        allergies=[_allergy('Ciprofloxacin', 'Tendon pain', 'Moderate')],
        immunizations=[
            _imm('COVID-19 vaccine', '08/01/2025'),
        ],
        vitals=[_vitals(height='64', weight='152', bmi='26.1',
                        bp_sys='130', bp_dia='78', hr='74', o2='98')],
    ),

    # ------------------------------------------------------------------
    # 90024 — Mark Green, 73M, Medicare
    # CCM (complex — 4+ dx), RPM, prolonged service, fall risk,
    # pneumococcal
    # ------------------------------------------------------------------
    _patient('90024', 'Mark Green', '19520827', 'M', 'medicare',
        meds=[
            _med('epoetin alfa 10000 units/mL', '', 'Inject three times weekly', rxnorm='205923'),
            _med('insulin glargine 100 units/mL', '40 units', 'Inject at bedtime', rxnorm='261551'),
            _med('iron sucrose 20 mg/mL IV', '', 'Infuse per dialysis protocol', rxnorm='284194'),
            _med('sevelamer 800 mg tablet', '800 mg', 'Take with each meal', rxnorm='313536'),
            _med('calcitriol 0.25 mcg capsule', '0.25 mcg', 'Take once daily', rxnorm='197414'),
            _med('amlodipine 10 mg tablet', '10 mg', 'Take once daily', rxnorm='329526'),
        ],
        diagnoses=[
            _dx('End stage renal disease on dialysis', 'N18.6'),
            _dx('Type 2 diabetes with diabetic CKD', 'E11.65'),
            _dx('Anemia in chronic kidney disease', 'D63.1'),
            _dx('Essential hypertension', 'I10'),
        ],
        allergies=[
            _allergy('Vancomycin', 'Red man syndrome', 'Moderate'),
            _allergy('Iodine contrast', 'Anaphylaxis', 'Severe'),
        ],
        immunizations=[
            _imm('Influenza vaccine', '10/01/2025'),
            _imm('Hepatitis B vaccine', '03/15/2024'),
        ],
        vitals=[_vitals(height='67', weight='165', bmi='25.8',
                        bp_sys='162', bp_dia='86', hr='80', o2='95')],
    ),

    # ------------------------------------------------------------------
    # 90025 — Sandra Adams, 45F, Medicare Advantage
    # CCM, colonoscopy (45+), mammogram, cervical pap, depression,
    # lipid
    # ------------------------------------------------------------------
    _patient('90025', 'Sandra Adams', '19800118', 'F', 'medicare_advantage',
        meds=[
            _med('hydroxychloroquine 200 mg tablet', '200 mg', 'Take twice daily', rxnorm='979092'),
            _med('prednisone 5 mg tablet', '5 mg', 'Take once daily', rxnorm='312617'),
            _med('lisinopril 10 mg tablet', '10 mg', 'Take once daily', rxnorm='314076'),
            _med('mycophenolate 500 mg tablet', '500 mg', 'Take twice daily', rxnorm='313393'),
        ],
        diagnoses=[
            _dx('Systemic lupus erythematosus', 'M32.9'),
            _dx('Chronic kidney disease, stage 2', 'N18.2'),
            _dx('Essential hypertension', 'I10'),
        ],
        allergies=[_allergy('Sulfa drugs', 'Rash', 'Moderate')],
        immunizations=[
            _imm('Influenza vaccine', '10/15/2025'),
            _imm('COVID-19 vaccine', '07/01/2025'),
        ],
        vitals=[_vitals(height='63', weight='138', bmi='24.4',
                        bp_sys='126', bp_dia='76', hr='74', o2='98')],
    ),

    # ------------------------------------------------------------------
    # 90026 — Paul Mitchell, 38M, Commercial
    # SDOH screening, BHI, diabetes screen, lipid
    # ------------------------------------------------------------------
    _patient('90026', 'Paul Mitchell', '19870510', 'M', 'commercial',
        meds=[
            _med('metformin 500 mg tablet', '500 mg', 'Take twice daily', rxnorm='861004'),
            _med('sertraline 100 mg tablet', '100 mg', 'Take once daily', rxnorm='312940'),
        ],
        diagnoses=[
            _dx('Type 2 diabetes mellitus without complications', 'E11.9'),
            _dx('Major depressive disorder, recurrent, moderate', 'F33.1'),
            _dx('Homelessness', 'Z59.00'),
            _dx('Food insecurity', 'Z59.41'),
        ],
        allergies=[],
        immunizations=[],
        vitals=[_vitals(height='68', weight='160', bmi='24.3',
                        bp_sys='130', bp_dia='82', hr='80', o2='98')],
    ),

    # ------------------------------------------------------------------
    # 90027 — Angela Turner, 30F, Medicaid
    # STI screening, substance use, HIV (positive), depression,
    # cervical pap/HPV
    # ------------------------------------------------------------------
    _patient('90027', 'Angela Turner', '19950302', 'F', 'medicaid',
        meds=[
            _med('buprenorphine-naloxone 8-2 mg sublingual film', '', 'Dissolve under tongue daily', rxnorm='1431076'),
            _med('ledipasvir-sofosbuvir 90-400 mg tablet', '', 'Take once daily x 12 weeks', rxnorm='1591876'),
            _med('bictegravir-emtricitabine-TAF tablet', '', 'Take once daily', rxnorm='2049106'),
        ],
        diagnoses=[
            _dx('Opioid dependence, in remission', 'F11.20'),
            _dx('Chronic hepatitis C', 'B18.2'),
            _dx('HIV disease', 'B20'),
        ],
        allergies=[_allergy('Methadone', 'QTc prolongation', 'Severe')],
        immunizations=[
            _imm('Hepatitis A vaccine', '01/10/2025'),
            _imm('Hepatitis B vaccine', '01/10/2025'),
        ],
        vitals=[_vitals(height='65', weight='120', bmi='20.0',
                        bp_sys='108', bp_dia='66', hr='78', o2='98')],
    ),

    # ------------------------------------------------------------------
    # 90028 — Kenneth Phillips, 82M, Medicare
    # Cognitive assessment, CCM, fall risk, ACP (advance care planning),
    # pneumococcal
    # ------------------------------------------------------------------
    _patient('90028', 'Kenneth Phillips', '19430115', 'M', 'medicare',
        meds=[
            _med('memantine 10 mg tablet', '10 mg', 'Take twice daily', rxnorm='997220'),
            _med('donepezil 10 mg tablet', '10 mg', 'Take at bedtime', rxnorm='997221'),
            _med('glipizide 5 mg tablet', '5 mg', 'Take before breakfast', rxnorm='310488'),
            _med('lisinopril 10 mg tablet', '10 mg', 'Take once daily', rxnorm='314076'),
        ],
        diagnoses=[
            _dx("Alzheimer's disease, unspecified", 'G30.9'),
            _dx('Type 2 diabetes mellitus without complications', 'E11.9'),
            _dx('Essential hypertension', 'I10'),
            _dx('Urinary incontinence, unspecified', 'R32'),
        ],
        allergies=[_allergy('Fluoroquinolones', 'Confusion', 'Moderate')],
        immunizations=[
            _imm('Influenza vaccine', '10/01/2025'),
            _imm('Pneumococcal PPSV23', '04/15/2019'),
        ],
        vitals=[_vitals(height='68', weight='160', bmi='24.3',
                        bp_sys='140', bp_dia='72', hr='68', o2='96')],
    ),

    # ------------------------------------------------------------------
    # 90029 — Jessica Campbell, 27F, Commercial
    # *** FALSE-POSITIVE CONTROL — healthy, acute URI visit ***
    # Should NOT trigger CCM, BHI, RPM, etc.
    # Should trigger: cervical pap, depression screen, HIV, flu, COVID,
    # tdap (all universal screens)
    # ------------------------------------------------------------------
    _patient('90029', 'Jessica Campbell', '19980425', 'F', 'commercial',
        meds=[],
        diagnoses=[
            _dx('Acute upper respiratory infection', 'J06.9', status='Active',
                started='03/15/2026'),
        ],
        allergies=[],
        immunizations=[
            _imm('COVID-19 vaccine', '06/15/2025'),
            _imm('Tdap vaccine', '09/01/2020'),
        ],
        vitals=[_vitals(height='67', weight='135', bmi='21.2',
                        bp_sys='114', bp_dia='68', hr='72', o2='99',
                        temp='100.2')],
    ),

    # ------------------------------------------------------------------
    # 90030 — George Evans, 67M, Medicare
    # AWV, CCM, fall risk, colonoscopy, pneumococcal, shingrix
    # ------------------------------------------------------------------
    _patient('90030', 'George Evans', '19580330', 'M', 'medicare',
        meds=[
            _med('leuprolide 22.5 mg injection', '', 'Inject every 3 months', rxnorm='197688'),
            _med('tamsulosin 0.4 mg capsule', '0.4 mg', 'Take once daily', rxnorm='313988'),
            _med('amlodipine 5 mg tablet', '5 mg', 'Take once daily', rxnorm='329528'),
        ],
        diagnoses=[
            _dx('Malignant neoplasm of prostate', 'C61'),
            _dx('Essential hypertension', 'I10'),
            _dx('Benign prostatic hyperplasia', 'N40.0'),
        ],
        allergies=[_allergy('Bactrim', 'Rash', 'Mild')],
        immunizations=[
            _imm('Influenza vaccine', '10/10/2025'),
        ],
        vitals=[_vitals(height='71', weight='190', bmi='26.5',
                        bp_sys='138', bp_dia='80', hr='76', o2='97')],
    ),

    # ------------------------------------------------------------------
    # 90031 — Betty Stewart, 73F, Medicare Advantage
    # Telehealth visit, E/M add-ons (G2211), fall risk, DEXA,
    # mammogram, shingrix
    # ------------------------------------------------------------------
    _patient('90031', 'Betty Stewart', '19520912', 'F', 'medicare_advantage',
        meds=[
            _med('losartan 50 mg tablet', '50 mg', 'Take once daily', rxnorm='979480'),
            _med('buspirone 10 mg tablet', '10 mg', 'Take twice daily', rxnorm='104894'),
            _med('trazodone 50 mg tablet', '50 mg', 'Take at bedtime', rxnorm='312127'),
        ],
        diagnoses=[
            _dx('Essential hypertension', 'I10'),
            _dx('Generalized anxiety disorder', 'F41.1'),
            _dx('Insomnia, unspecified', 'G47.00'),
        ],
        allergies=[_allergy('Zolpidem', 'Sleepwalking', 'Moderate')],
        immunizations=[
            _imm('COVID-19 vaccine', '07/20/2025'),
        ],
        vitals=[_vitals(height='62', weight='155', bmi='28.4',
                        bp_sys='134', bp_dia='76', hr='70', o2='97')],
    ),

    # ------------------------------------------------------------------
    # 90032 — Edward Morgan, 42M, Commercial
    # Chronic monitoring, lipid, depression screen
    # ------------------------------------------------------------------
    _patient('90032', 'Edward Morgan', '19830618', 'M', 'commercial',
        meds=[
            _med('losartan 50 mg tablet', '50 mg', 'Take once daily', rxnorm='979480'),
            _med('febuxostat 40 mg tablet', '40 mg', 'Take once daily', rxnorm='860975'),
        ],
        diagnoses=[
            _dx('Chronic kidney disease, stage 3a', 'N18.31'),
            _dx('Essential hypertension', 'I10'),
            _dx('Gout, unspecified', 'M10.9'),
        ],
        allergies=[],
        immunizations=[
            _imm('Tdap vaccine', '03/10/2024'),
            _imm('COVID-19 vaccine', '09/01/2025'),
        ],
        vitals=[_vitals(height='72', weight='195', bmi='26.4',
                        bp_sys='132', bp_dia='84', hr='76', o2='98')],
    ),

    # ------------------------------------------------------------------
    # 90033 — Lily Phillips, 7F, Medicaid
    # Pediatric well-child, vaccine admin
    # ------------------------------------------------------------------
    _patient('90033', 'Lily Phillips', '20181205', 'F', 'medicaid',
        meds=[
            _med('montelukast 4 mg chewable tablet', '4 mg', 'Take at bedtime', rxnorm='997501'),
            _med('albuterol 90 mcg/actuation inhaler', '', 'Inhale 2 puffs prn', rxnorm='801092'),
            _med('hydrocortisone 1% cream', '', 'Apply to affected areas twice daily'),
        ],
        diagnoses=[
            _dx('Childhood asthma, mild intermittent', 'J45.20'),
            _dx('Atopic dermatitis', 'L30.9'),
        ],
        allergies=[_allergy('Eggs', 'Hives', 'Mild')],
        immunizations=[
            _imm('Influenza vaccine', '10/20/2025'),
            _imm('DTaP vaccine', '09/01/2023'),
            _imm('IPV vaccine', '09/01/2023'),
            _imm('MMR vaccine', '12/05/2022'),
        ],
        vitals=[_vitals(height='47', weight='50', bmi='16.0',
                        bp_sys='94', bp_dia='58', hr='92', o2='99')],
    ),

    # ------------------------------------------------------------------
    # 90034 — Richard Cooper, 55M, Medicare Advantage
    # CCM (5+ chronic!), chronic monitoring, RPM, colonoscopy,
    # shingrix, diabetes screen, obesity counseling
    # ------------------------------------------------------------------
    _patient('90034', 'Richard Cooper', '19700225', 'M', 'medicare_advantage',
        meds=[
            _med('sacubitril-valsartan 97-103 mg tablet', '', 'Take twice daily', rxnorm='1656340'),
            _med('metoprolol succinate 100 mg tablet', '100 mg', 'Take once daily', rxnorm='866924'),
            _med('tiotropium 18 mcg capsule', '18 mcg', 'Inhale once daily', rxnorm='274535'),
            _med('empagliflozin 10 mg tablet', '10 mg', 'Take once daily', rxnorm='1545684'),
            _med('metformin 1000 mg tablet', '1000 mg', 'Take twice daily', rxnorm='861004'),
            _med('furosemide 40 mg tablet', '40 mg', 'Take once daily', rxnorm='197417'),
        ],
        diagnoses=[
            _dx('Heart failure, unspecified', 'I50.9'),
            _dx('Chronic obstructive pulmonary disease with acute exacerbation', 'J44.1'),
            _dx('Type 2 diabetes mellitus without complications', 'E11.9'),
            _dx('Chronic kidney disease, stage 3', 'N18.3'),
            _dx('Morbid obesity due to excess calories', 'E66.01'),
        ],
        allergies=[
            _allergy('ACE inhibitors', 'Cough', 'Moderate'),
            _allergy('Penicillin', 'Anaphylaxis', 'Severe'),
        ],
        immunizations=[
            _imm('Influenza vaccine', '10/15/2025'),
        ],
        vitals=[_vitals(height='69', weight='260', bmi='38.4',
                        bp_sys='148', bp_dia='88', hr='78', o2='92')],
    ),

    # ------------------------------------------------------------------
    # 90035 — Helen Bailey, 79F, Medicare
    # DEXA, fall risk, CCM, AWV, mammogram, pneumococcal,
    # prolonged service (complex)
    # ------------------------------------------------------------------
    _patient('90035', 'Helen Bailey', '19460710', 'F', 'medicare',
        meds=[
            _med('teriparatide 250 mcg/mL pen', '', 'Inject 20 mcg subcutaneous daily', rxnorm='310706'),
            _med('levothyroxine 100 mcg tablet', '100 mcg', 'Take on empty stomach daily', rxnorm='895994'),
            _med('amlodipine 5 mg tablet', '5 mg', 'Take once daily', rxnorm='329528'),
            _med('calcium carbonate 600 mg + vitamin D3 tablet', '', 'Take twice daily'),
        ],
        diagnoses=[
            _dx('Age-related osteoporosis with pathological fracture, vertebra', 'M80.08XA'),
            _dx('Essential hypertension', 'I10'),
            _dx('Hypothyroidism, unspecified', 'E03.9'),
        ],
        allergies=[_allergy('Bisphosphonates', 'Esophageal irritation', 'Moderate')],
        immunizations=[
            _imm('Influenza vaccine', '10/05/2025'),
            _imm('Shingrix dose 1', '01/20/2025'),
            _imm('Shingrix dose 2', '04/20/2025'),
            _imm('Pneumococcal PCV20', '06/15/2024'),
        ],
        vitals=[_vitals(height='60', weight='118', bmi='23.0',
                        bp_sys='142', bp_dia='74', hr='72', o2='96')],
    ),
]

# All test MRNs for cleanup
TEST_MRNS = ['62815'] + [str(90000 + i) for i in range(1, 36)]


# ======================================================================
# Seed from reference XML (MRN 62815)
# ======================================================================

def seed_patient_from_xml(user_id):
    """Parse the reference XML and store MRN 62815 data in the DB."""
    from agent.clinical_summary_parser import parse_clinical_summary, store_parsed_summary
    from models.patient import PatientRecord

    xml_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'Documents', 'demo_patients',
        'ClinicalSummary_PatientId_62815_20260317_142334.xml'
    )

    if not os.path.isfile(xml_path):
        print(f'  XML not found: {xml_path}')
        return False

    existing = PatientRecord.query.filter_by(user_id=user_id, mrn='62815').first()
    if existing and existing.last_xml_parsed:
        print('  MRN 62815 already seeded — skipping')
        return True

    parsed = parse_clinical_summary(xml_path)
    if not parsed.get('patient_mrn'):
        print('  Failed to parse XML — no MRN found')
        return False

    store_parsed_summary(user_id, '62815', parsed)
    print(f'  Seeded MRN 62815 (TEST, TEST) — '
          f'{len(parsed.get("medications", []))} meds, '
          f'{len(parsed.get("diagnoses", []))} dx, '
          f'{len(parsed.get("allergies", []))} allergies, '
          f'{len(parsed.get("vitals", []))} vitals, '
          f'{len(parsed.get("immunizations", []))} immunizations')
    return True


# ======================================================================
# Seed 35 fake patients
# ======================================================================

def seed_fake_patients(user_id):
    """Insert all 35 fake patients into the DB via store_parsed_summary()."""
    from agent.clinical_summary_parser import store_parsed_summary
    from models.patient import PatientRecord

    seeded = 0
    skipped = 0

    for p in FAKE_PATIENTS:
        mrn = p['patient_mrn']
        existing = PatientRecord.query.filter_by(user_id=user_id, mrn=mrn).first()
        if existing and existing.last_xml_parsed:
            print(f'  MRN {mrn} already seeded — skipping')
            skipped += 1
            continue

        store_parsed_summary(user_id, mrn, p)
        seeded += 1
        print(f'  Seeded MRN {mrn} ({p["patient_name"]}) — '
              f'{len(p["medications"])} meds, '
              f'{len(p["diagnoses"])} dx, '
              f'{len(p["allergies"])} allergies')

    print(f'  Done: {seeded} seeded, {skipped} skipped')
    return seeded


# ======================================================================
# Public API
# ======================================================================

def seed_all_test_data(user_id):
    """Seed MRN 62815 from XML + 35 fake patients + pricing demo data."""
    print('Seeding test patient data...')
    seed_patient_from_xml(user_id)
    count = seed_fake_patients(user_id)
    pricing_count = seed_pricing_demo_data()
    print(f'Complete — seeded {count} fake patients + MRN 62815 (XML) + {pricing_count} pricing cache entries.')
    return f'Seeded MRN 62815 (XML) + {count} fake patients (90001-90035) + {pricing_count} pricing entries.'


# ======================================================================
# Phase 29 — Pricing Demo Data
# ======================================================================

# Pre-computed pricing data for demo patients (hardcoded, not API-sourced)
PRICING_DEMO_DATA = {
    # Patient 90001 — Margaret Wilson (Medicare)
    'lisinopril': {
        'source': 'cost_plus', 'price': 3.60, 'price_display': '$3.60/month',
        'direct_url': 'https://costplusdrugs.com/medications/lisinopril-10mg-tablet/',
        'badge_color': 'green',
    },
    'metformin': {
        'source': 'cost_plus', 'price': 3.90, 'price_display': '$3.90/month',
        'direct_url': 'https://costplusdrugs.com/medications/metformin-500mg-tablet/',
        'badge_color': 'green',
    },
    'atorvastatin': {
        'source': 'cost_plus', 'price': 4.50, 'price_display': '$4.50/month',
        'direct_url': 'https://costplusdrugs.com/medications/atorvastatin-20mg-tablet/',
        'badge_color': 'green',
    },
    'alendronate': {
        'source': 'goodrx', 'price': 38.00, 'price_display': '$38.00/month',
        'direct_url': 'https://www.goodrx.com/alendronate',
        'badge_color': 'yellow',
        'attribution_text': 'Powered by GoodRx',
    },
    # Patient 90002 — Robert Thompson (Medicare)
    'amlodipine': {
        'source': 'cost_plus', 'price': 3.00, 'price_display': '$3.00/month',
        'direct_url': 'https://costplusdrugs.com/medications/amlodipine-5mg-tablet/',
        'badge_color': 'green',
    },
    'tiotropium': {
        'source': 'goodrx', 'price': 350.00, 'price_display': '$350.00/month',
        'direct_url': 'https://www.goodrx.com/tiotropium',
        'badge_color': 'red',
        'attribution_text': 'Powered by GoodRx',
        'assistance_programs': [
            {'program_name': 'Boehringer Ingelheim Cares Foundation',
             'eligibility_summary': 'Income-based; uninsured or underinsured patients',
             'application_url': 'https://www.needymeds.org/pap/boehringer',
             'source': 'needymeds'},
        ],
    },
    # Patient 90003 — Maria Garcia (Commercial)
    'buspirone': {
        'source': 'cost_plus', 'price': 5.40, 'price_display': '$5.40/month',
        'direct_url': 'https://costplusdrugs.com/medications/buspirone-10mg-tablet/',
        'badge_color': 'green',
    },
    # MedRef common drugs
    'eliquis': {
        'source': 'goodrx', 'price': 580.00, 'price_display': '$580.00/month',
        'direct_url': 'https://www.goodrx.com/eliquis',
        'badge_color': 'red',
        'attribution_text': 'Powered by GoodRx',
        'assistance_programs': [
            {'program_name': 'Bristol-Myers Squibb Patient Assistance',
             'eligibility_summary': 'Income-based; uninsured patients',
             'application_url': 'https://www.needymeds.org/pap/bms',
             'source': 'needymeds'},
        ],
    },
    'jardiance': {
        'source': 'goodrx', 'price': 560.00, 'price_display': '$560.00/month',
        'direct_url': 'https://www.goodrx.com/jardiance',
        'badge_color': 'red',
        'attribution_text': 'Powered by GoodRx',
    },
    'ozempic': {
        'source': 'goodrx', 'price': 935.00, 'price_display': '$935.00/month',
        'direct_url': 'https://www.goodrx.com/ozempic',
        'badge_color': 'red',
        'attribution_text': 'Powered by GoodRx',
        'assistance_programs': [
            {'program_name': 'Novo Nordisk Patient Assistance Program',
             'eligibility_summary': 'Income-based; uninsured or underinsured',
             'application_url': 'https://www.needymeds.org/pap/novonordisk',
             'source': 'needymeds'},
        ],
    },
}


def seed_pricing_demo_data():
    """
    Phase 29 — Seed pre-computed pricing data into the API cache for demo mode.
    Uses CacheManager.set() so the pricing service finds cached results
    without needing live API keys. Entries are marked as demo/hardcoded.
    """
    from models import db
    from app.services.api.cache_manager import CacheManager
    from datetime import datetime, timezone

    cm = CacheManager(db)
    seeded = 0

    for drug_name, data in PRICING_DEMO_DATA.items():
        cache_entry = {
            'demo_data': True,
            'source': data['source'],
            'price': data['price'],
            'price_display': data['price_display'],
            'direct_url': data.get('direct_url', ''),
            'badge_color': data.get('badge_color'),
            'attribution_text': data.get('attribution_text', ''),
            'assistance_programs': data.get('assistance_programs', []),
            'cached_at': datetime.now(timezone.utc).isoformat(),
        }

        # Seed under cost_plus api_name for Cost Plus sources
        if data['source'] == 'cost_plus':
            cm.set('cost_plus', f'name:{drug_name.lower()}', cache_entry, ttl_days=90)
            seeded += 1
        # Seed under goodrx api_name for GoodRx sources
        elif data['source'] == 'goodrx':
            cm.set('goodrx', f'search:{drug_name.lower()}', cache_entry, ttl_days=90)
            seeded += 1

        # Also seed assistance programs under drug_assistance
        if data.get('assistance_programs'):
            cm.set('drug_assistance', f'programs:{drug_name.lower()}', {
                'demo_data': True,
                'programs': data['assistance_programs'],
            }, ttl_days=90)
            seeded += 1

    print(f'  Seeded {seeded} pricing cache entries for {len(PRICING_DEMO_DATA)} drugs (demo mode)')
    return seeded


def clear_test_data(user_id):
    """Remove all test patient data for the given user."""
    from models import db
    from models.patient import (
        PatientRecord, PatientVitals, PatientMedication,
        PatientDiagnosis, PatientAllergy, PatientImmunization,
        PatientNoteDraft,
    )

    count = 0
    for model in [PatientVitals, PatientMedication, PatientDiagnosis,
                  PatientAllergy, PatientImmunization, PatientNoteDraft,
                  PatientRecord]:
        deleted = model.query.filter(
            model.user_id == user_id,
            model.mrn.in_(TEST_MRNS)
        ).delete(synchronize_session=False)
        count += deleted

    db.session.commit()
    msg = f'Cleared {count} test data rows for {len(TEST_MRNS)} MRNs.'
    print(msg)
    return msg


if __name__ == '__main__':
    import argparse
    from app import create_app

    parser = argparse.ArgumentParser(description='Seed or clear test patient data')
    parser.add_argument('--clear', action='store_true', help='Remove all test data')
    parser.add_argument('--user-id', type=int, default=1, help='User ID (default: 1)')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        if args.clear:
            clear_test_data(args.user_id)
        else:
            seed_all_test_data(args.user_id)
