"""
Generate rich CDA XML demo patient files for CareCompanion testing.

Produces 15 fully detailed test patients with realistic clinical data
including allergies, medications, problems, vitals, labs, immunizations,
social history, insurance, and multi-visit progress notes.

Usage:
    python scripts/generate_demo_patients.py

Output:
    Documents/demo_patients/ClinicalSummary_PatientId_XXXXX_20260325_100000.xml
"""

import os
import sys

# --- Output directory ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'Documents', 'demo_patients')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================================================================
# Patient profiles -- each is a dict with all clinical sections
# MRNs start at 90001 to avoid collision with existing 5-digit MRNs
# =========================================================================
PATIENTS = [
    # ------------------------------------------------------------------
    # 1) Robert James Mitchell -- 68M, COPD/CHF/AFib, Medicare
    # ------------------------------------------------------------------
    {
        'mrn': '90001',
        'given': 'Robert',
        'family': 'Mitchell',
        'gender_code': 'M',
        'gender_display': 'Male',
        'birth': '19571105',
        'marital': 'M',
        'marital_display': 'Married',
        'race_code': '2106-3',
        'race_display': 'White',
        'ethnic_code': '2186-5',
        'ethnic_display': 'Not Hispanic or Latino',
        'street': '1247 Oak Hollow Lane',
        'city': 'Midlothian',
        'state': 'VA',
        'zip': '23112',
        'phone': '+1(804)-555-1001',
        'allergies': [
            ('Aspirin [RxNorm: 1191]', 'GI Bleeding', 'severe', 'active'),
            ('ACE Inhibitors [RxNorm: 18867]', 'Angioedema', 'severe', 'active'),
            ('Latex', 'Contact dermatitis', 'moderate', 'active'),
        ],
        'medications': [
            ('warfarin 5 mg tablet [RxNorm: 855332]', 'warfarin', 'Take 1 tablet by mouth daily', '5 mg', '03/15/2022', 'active'),
            ('metoprolol tartrate 50 mg tablet [RxNorm: 866924]', 'metoprolol', 'Take 1 tablet by mouth twice daily', '50 mg', '01/10/2020', 'active'),
            ('furosemide 40 mg tablet [RxNorm: 310429]', 'furosemide', 'Take 1 tablet by mouth daily', '40 mg', '06/01/2021', 'active'),
            ('potassium chloride 20 mEq tablet [RxNorm: 628958]', 'potassium chloride', 'Take 1 tablet by mouth daily', '20 mEq', '06/01/2021', 'active'),
            ('tiotropium 18 mcg inhaler [RxNorm: 1112935]', 'tiotropium', 'Inhale 1 puff daily', '18 mcg', '09/15/2019', 'active'),
            ('albuterol 90 mcg inhaler [RxNorm: 245314]', 'albuterol', 'Inhale 2 puffs every 4-6 hours as needed', '90 mcg', '09/15/2019', 'active'),
            ('rosuvastatin 20 mg tablet [RxNorm: 859747]', 'rosuvastatin', 'Take 1 tablet by mouth at bedtime', '20 mg', '04/20/2018', 'active'),
            ('digoxin 0.125 mg tablet [RxNorm: 197604]', 'digoxin', 'Take 1 tablet by mouth daily', '0.125 mg', '03/15/2022', 'active'),
            ('pantoprazole 40 mg tablet [RxNorm: 261257]', 'pantoprazole', 'Take 1 tablet by mouth daily before breakfast', '40 mg', '11/01/2020', 'active'),
        ],
        'problems': [
            ('Chronic obstructive pulmonary disease [ICD10: J44.1]', 'active', '09/15/2019', ''),
            ('Congestive heart failure [ICD10: I50.9]', 'active', '06/01/2021', ''),
            ('Atrial fibrillation [ICD10: I48.91]', 'active', '03/15/2022', ''),
            ('Essential hypertension [ICD10: I10]', 'active', '05/20/2015', ''),
            ('Mixed hyperlipidemia [ICD10: E78.2]', 'active', '04/20/2018', ''),
            ('Gastroesophageal reflux disease [ICD10: K21.0]', 'active', '11/01/2020', ''),
            ('Tobacco use disorder [ICD10: F17.210]', 'active', '01/01/2010', ''),
            ('Benign prostatic hyperplasia [ICD10: N40.0]', 'active', '08/15/2023', ''),
            ('COPD exacerbation [ICD10: J44.1]', 'resolved', '12/01/2025', '12/20/2025'),
            ('Community acquired pneumonia [ICD10: J18.9]', 'resolved', '12/01/2025', '12/20/2025'),
        ],
        'vitals': [
            ('03/20/2026', '70', '210', '30.1', '138', '82', '88', '93', '98.4', '20'),
            ('12/01/2025', '70', '215', '30.8', '144', '86', '102', '89', '100.8', '24'),
            ('09/15/2025', '70', '208', '29.8', '132', '80', '82', '95', '98.2', '18'),
            ('06/10/2025', '70', '212', '30.4', '140', '84', '86', '94', '98.6', '18'),
        ],
        'labs': [
            ('INR [LOINC: 6301-6]', '2.4', '', 'normal', '03/18/2026'),
            ('INR [LOINC: 6301-6]', '3.6', '', 'H', '12/05/2025'),
            ('BNP [LOINC: 42637-9]', '380', 'pg/mL', 'H', '03/18/2026'),
            ('BNP [LOINC: 42637-9]', '890', 'pg/mL', 'H', '12/01/2025'),
            ('Creatinine [LOINC: 2160-0]', '1.3', 'mg/dL', 'H', '03/18/2026'),
            ('eGFR [LOINC: 48642-3]', '55', 'mL/min/1.73m2', 'normal', '03/18/2026'),
            ('Potassium [LOINC: 2823-3]', '4.5', 'mmol/L', 'normal', '03/18/2026'),
            ('Digoxin level [LOINC: 10535-3]', '1.1', 'ng/mL', 'normal', '03/18/2026'),
            ('Total Cholesterol [LOINC: 2093-3]', '195', 'mg/dL', 'normal', '03/18/2026'),
            ('LDL Cholesterol [LOINC: 2089-1]', '110', 'mg/dL', 'normal', '03/18/2026'),
            ('HDL Cholesterol [LOINC: 2085-9]', '38', 'mg/dL', 'L', '03/18/2026'),
            ('CBC WBC [LOINC: 6690-2]', '11.2', '10*3/uL', 'H', '12/01/2025'),
            ('CBC WBC [LOINC: 6690-2]', '7.8', '10*3/uL', 'normal', '03/18/2026'),
            ('Hemoglobin [LOINC: 718-7]', '13.0', 'g/dL', 'normal', '03/18/2026'),
            ('TSH [LOINC: 3016-3]', '2.8', 'mIU/L', 'normal', '03/18/2026'),
            ('PSA [LOINC: 2857-1]', '3.8', 'ng/mL', 'normal', '03/18/2026'),
        ],
        'immunizations': [
            ('Influenza vaccine 2025-2026', '10/05/2025', 'completed'),
            ('Pneumococcal PCV20 (Prevnar 20)', '09/15/2024', 'completed'),
            ('COVID-19 Vaccine 2024-2025 (Pfizer)', '10/10/2024', 'completed'),
            ('Tdap (Boostrix)', '04/15/2016', 'completed'),
            ('Shingrix (Zoster) Dose 1', '03/20/2025', 'completed'),
            ('Shingrix (Zoster) Dose 2', '06/20/2025', 'completed'),
        ],
        'social_history': 'Tobacco: Active smoker (1 ppd x 40 yrs = 40 pack-years). Alcohol: 2-3 beers daily. Employment: Retired electrician. Marital Status: Married. Lives with wife. Exercise: Limited by dyspnea, walks to mailbox. Home oxygen: 2L NC continuous.',
        'insurance': [
            ('Medicare Part B', 'Medicare', '1AB2-CD3-EF45', 'N/A'),
            ('Anthem Medicare Advantage', 'Medicare Advantage', 'MA-901234', 'GRP-55123'),
        ],
        'notes': [
            ('03/20/2026', 'Cory Denton, FNP', 'Progress Note',
             'CC: Follow-up CHF, COPD, Afib.\nHPI: 68yo male here for chronic disease management. Reports stable dyspnea on exertion -- can walk about 100 feet before needing rest. No orthopnea or PND. 2-pillow sleeper. Weights stable at home. Continues to smoke 1 ppd despite counseling.\nPE: Lungs -- diminished bilaterally, scattered expiratory wheezes. CV -- irregularly irregular, no murmur. 1+ pitting edema bilateral ankles.\nAssessment:\n# CHF (I50.9): Stable NYHA Class III. BNP improved from 890 to 380. Continue furosemide, digoxin. Check BMP.\n# Afib (I48.91): Rate controlled, HR 88. INR 2.4 therapeutic. Continue warfarin 5mg.\n# COPD (J44.1): FEV1 42% predicted. Tiotropium + PRN albuterol. Smoking cessation counseled -- declined NRT again.\n# BPH (N40.0): Nocturia x3. Discussed tamsulosin. Will start 0.4mg qhs.\n# HTN (I10): BP 138/82. Acceptable given CHF meds.\nPlan: Continue current regimen. Add tamsulosin 0.4mg qhs. INR in 2 weeks. Pulmonology referral for PFTs. Smoking cessation pamphlet given. Return 3 months.'),
            ('12/01/2025', 'Gretchen Lockard, MD', 'Acute Visit',
             'CC: Worsening SOB, productive cough x 5 days, fever.\nHPI: 68yo with COPD/CHF presents with acute worsening of dyspnea. Yellow-green sputum, fever to 101.4 at home. Unable to complete ADLs without stopping.\nPE: T 100.8, HR 102, RR 24, O2 89% on RA. Lungs -- bilateral rhonchi, right base crackles. CV -- irregularly irregular, tachycardic. 2+ pedal edema.\nCXR: Right lower lobe infiltrate, mild pulmonary congestion.\nAssessment:\n# COPD exacerbation with community-acquired pneumonia\n# Acute on chronic systolic HF -- volume overloaded\nPlan: Admit to observation. IV azithromycin + ceftriaxone. Increase furosemide to 80mg IV BID. Nebs q4h. O2 titrate to 90-92%. Hold warfarin, bridge with heparin drip. Telemetry monitoring.'),
            ('09/15/2025', 'Cory Denton, FNP', 'Annual Wellness Visit',
             'ANNUAL WELLNESS VISIT -- G0439\n68yo male here for AWV.\nPreventive:\n- Lung cancer screening: LDCT ordered (30+ pack-years, active smoker).\n- AAA screening: Not done -- discuss ultrasound.\n- Colorectal cancer: Colonoscopy 2021, next 2031.\n- Depression: PHQ-9 = 8 (mild).\n- Fall risk: Timed Up and Go = 14 sec (borderline).\n- Advance Directive: Updated, on file.\n- Bone density: DEXA not indicated (male, no fracture risk).\nVaccines: Flu given. Shingrix dose 1 given.\nHealth Risk Assessment completed. Cognitive screen normal (Mini-Cog 4/5).'),
        ],
    },
    # ------------------------------------------------------------------
    # 2) Maria Elena Garcia -- 42F, Lupus/CKD, Hispanic, Medicaid
    # ------------------------------------------------------------------
    {
        'mrn': '90002',
        'given': 'Maria',
        'family': 'Garcia',
        'gender_code': 'F',
        'gender_display': 'Female',
        'birth': '19831220',
        'marital': 'M',
        'marital_display': 'Married',
        'race_code': '2106-3',
        'race_display': 'White',
        'ethnic_code': '2135-2',
        'ethnic_display': 'Hispanic or Latino',
        'street': '3892 Magnolia Court',
        'city': 'Chester',
        'state': 'VA',
        'zip': '23831',
        'phone': '+1(804)-555-1002',
        'allergies': [
            ('Sulfonamides [RxNorm: 10171]', 'Stevens-Johnson Syndrome', 'severe', 'active'),
            ('NSAIDs [RxNorm: 7258]', 'Renal impairment', 'severe', 'active'),
        ],
        'medications': [
            ('hydroxychloroquine 200 mg tablet [RxNorm: 979092]', 'hydroxychloroquine', 'Take 1 tablet by mouth twice daily', '200 mg', '06/15/2018', 'active'),
            ('mycophenolate 500 mg tablet [RxNorm: 835829]', 'mycophenolate', 'Take 2 tablets by mouth twice daily', '1000 mg', '09/01/2020', 'active'),
            ('prednisone 5 mg tablet [RxNorm: 312617]', 'prednisone', 'Take 1 tablet by mouth daily', '5 mg', '06/15/2018', 'active'),
            ('losartan 100 mg tablet [RxNorm: 979480]', 'losartan', 'Take 1 tablet by mouth daily', '100 mg', '03/10/2021', 'active'),
            ('amlodipine 10 mg tablet [RxNorm: 197361]', 'amlodipine', 'Take 1 tablet by mouth daily', '10 mg', '03/10/2021', 'active'),
            ('ergocalciferol 50000 IU capsule [RxNorm: 904416]', 'ergocalciferol', 'Take 1 capsule weekly', '50000 IU', '01/15/2023', 'active'),
            ('calcium carbonate 600 mg tablet [RxNorm: 215459]', 'calcium carbonate', 'Take 1 tablet by mouth twice daily', '600 mg', '01/15/2023', 'active'),
            ('escitalopram 10 mg tablet [RxNorm: 352741]', 'escitalopram', 'Take 1 tablet by mouth daily', '10 mg', '11/01/2022', 'active'),
        ],
        'problems': [
            ('Systemic lupus erythematosus [ICD10: M32.9]', 'active', '06/15/2018', ''),
            ('Lupus nephritis class IV [ICD10: M32.14]', 'active', '09/01/2020', ''),
            ('Chronic kidney disease stage 3a [ICD10: N18.31]', 'active', '09/01/2020', ''),
            ('Essential hypertension [ICD10: I10]', 'active', '03/10/2021', ''),
            ('Vitamin D deficiency [ICD10: E55.9]', 'active', '01/15/2023', ''),
            ('Generalized anxiety disorder [ICD10: F41.1]', 'active', '11/01/2022', ''),
            ('Iron deficiency anemia [ICD10: D50.9]', 'active', '06/01/2024', ''),
            ('Raynaud phenomenon [ICD10: I73.00]', 'active', '06/15/2018', ''),
            ('SLE flare [ICD10: M32.9]', 'resolved', '11/15/2025', '12/20/2025'),
        ],
        'vitals': [
            ('03/15/2026', '63', '142', '25.2', '128', '78', '76', '98', '98.2', '16'),
            ('11/15/2025', '63', '148', '26.2', '152', '94', '88', '97', '100.4', '18'),
            ('08/20/2025', '63', '140', '24.8', '124', '76', '72', '99', '98.4', '14'),
        ],
        'labs': [
            ('Creatinine [LOINC: 2160-0]', '1.4', 'mg/dL', 'H', '03/10/2026'),
            ('eGFR [LOINC: 48642-3]', '48', 'mL/min/1.73m2', 'L', '03/10/2026'),
            ('Urine Protein/Creatinine Ratio [LOINC: 9318-7]', '850', 'mg/g', 'H', '03/10/2026'),
            ('C3 Complement [LOINC: 4485-9]', '72', 'mg/dL', 'L', '03/10/2026'),
            ('C4 Complement [LOINC: 4498-2]', '10', 'mg/dL', 'L', '03/10/2026'),
            ('dsDNA Antibody [LOINC: 5130-0]', '45', 'IU/mL', 'H', '03/10/2026'),
            ('ESR [LOINC: 30341-2]', '42', 'mm/hr', 'H', '03/10/2026'),
            ('CRP [LOINC: 1988-5]', '1.8', 'mg/dL', 'H', '03/10/2026'),
            ('Hemoglobin [LOINC: 718-7]', '10.8', 'g/dL', 'L', '03/10/2026'),
            ('Ferritin [LOINC: 2276-4]', '12', 'ng/mL', 'L', '03/10/2026'),
            ('Iron [LOINC: 2498-4]', '35', 'mcg/dL', 'L', '03/10/2026'),
            ('TIBC [LOINC: 2500-7]', '420', 'mcg/dL', 'H', '03/10/2026'),
            ('Vitamin D 25-OH [LOINC: 1989-3]', '18', 'ng/mL', 'L', '03/10/2026'),
            ('CBC WBC [LOINC: 6690-2]', '3.8', '10*3/uL', 'L', '03/10/2026'),
            ('Platelet Count [LOINC: 777-3]', '135', '10*3/uL', 'L', '03/10/2026'),
        ],
        'immunizations': [
            ('Influenza vaccine 2025-2026', '10/15/2025', 'completed'),
            ('COVID-19 Vaccine 2024-2025 (Moderna)', '09/20/2024', 'completed'),
            ('Tdap (Boostrix)', '06/15/2018', 'completed'),
            ('Hepatitis B series (3 doses)', '01/01/2019', 'completed'),
            ('Pneumococcal PCV20 (Prevnar 20)', '08/20/2025', 'completed'),
        ],
        'social_history': 'Tobacco: Never smoker. Alcohol: None. Employment: Part-time medical receptionist. Marital Status: Married, 2 children (ages 8 and 12). Bilingual English/Spanish. Exercise: Limited by fatigue, tries yoga 2x/week. Sun exposure: Avoids -- photosensitive. Support: Strong family network.',
        'insurance': [
            ('Virginia Medicaid', 'Medicaid', 'MCD-223456', 'N/A'),
        ],
        'notes': [
            ('03/15/2026', 'Cory Denton, FNP', 'Progress Note',
             'CC: Follow-up SLE, lupus nephritis, CKD.\nHPI: 42yo Hispanic female with SLE and class IV lupus nephritis. Recovered from flare in Nov -- completed pulse methylprednisolone. Currently on maintenance mycophenolate 2g/day + HCQ + prednisone 5mg. Reports improved energy, no joint pain, no rash. Occasional Raynaud episodes in cold weather.\nLabs: Cr 1.4 (stable), eGFR 48, proteinuria improving (850 from 1200). Complements low but stable. dsDNA elevated but trending down.\nPE: Afebrile. No malar rash. Joints -- no synovitis. Lungs clear. CV RRR. No edema.\nAssessment:\n# Lupus nephritis (M32.14): Improving on mycophenolate. Continue current dose.\n# CKD 3a (N18.31): Cr stable 1.4. Continue losartan for nephroprotection.\n# Anemia (D50.9): Hgb 10.8, ferritin 12. Start ferrous sulfate 325mg BID. Recheck in 6 weeks.\n# HTN (I10): BP 128/78 at goal. Continue losartan + amlodipine.\n# Vit D deficiency: Level 18. Continue ergocalciferol 50K weekly.\nPlan: Continue immunosuppression. Add iron. Nephrology follow-up in 6 weeks. Ophthalmology due for HCQ screening (annual). Labs 6 weeks.'),
            ('11/15/2025', 'Gretchen Lockard, MD', 'Acute Visit',
             'CC: Joint pain, facial rash, fever x 3 days.\nHPI: 42yo with SLE presents with classic flare symptoms. Butterfly rash returned, polyarthritis affecting hands/wrists/knees. Low-grade fever 100.4. Dark urine noted.\nPE: Malar rash present. Synovitis bilateral MCPs, wrists, knees. Oral ulcers x2 on buccal mucosa. Lungs clear. No edema.\nLabs: Cr up from 1.2 to 1.8, proteinuria 1200 mg/g, C3/C4 both low, dsDNA 120 IU/mL, WBC 2.9.\nAssessment: SLE flare with nephritis activity.\nPlan: Pulse methylprednisolone 1g IV x 3 days then taper. Increase mycophenolate to 3g/day temporarily. Urgent nephrology consult. Hold losartan temporarily if Cr continues rising. Weekly labs.'),
            ('08/20/2025', 'Cory Denton, FNP', 'Annual Wellness Visit',
             'ANNUAL WELLNESS VISIT\n42yo female with SLE.\nPreventive:\n- Cervical cancer: Pap + HPV co-test 2023. Next due 2028.\n- Breast cancer: Mammogram baseline age 40 done 2023. Due 2025 -- ordered.\n- Colorectal: Not yet due (age 42). Will start at 45.\n- Depression: PHQ-9 = 12 (moderate). Continue escitalopram. Counseling referral offered.\n- Bone density: DEXA ordered -- chronic steroid use.\n- Ophthalmology: HCQ screening annual -- due now.\n- Vaccines: Flu given. PCV20 given (immunocompromised).\nAdvance Directive: Discussed, patient will complete.'),
        ],
    },
    # ------------------------------------------------------------------
    # 3) James Edward Williams -- 55M, DM1 with complications, pump user
    # ------------------------------------------------------------------
    {
        'mrn': '90003',
        'given': 'James',
        'family': 'Williams',
        'gender_code': 'M',
        'gender_display': 'Male',
        'birth': '19700808',
        'marital': 'D',
        'marital_display': 'Divorced',
        'race_code': '2054-5',
        'race_display': 'Black or African American',
        'ethnic_code': '2186-5',
        'ethnic_display': 'Not Hispanic or Latino',
        'street': '7721 Crestview Drive',
        'city': 'Richmond',
        'state': 'VA',
        'zip': '23225',
        'phone': '+1(804)-555-1003',
        'allergies': [
            ('Lisinopril [RxNorm: 29046]', 'Cough', 'mild', 'active'),
            ('Metformin [RxNorm: 6809]', 'Lactic acidosis risk', 'severe', 'active'),
        ],
        'medications': [
            ('insulin lispro via pump [RxNorm: 731277]', 'insulin lispro', 'Continuous subcutaneous infusion per pump settings', 'variable', '08/01/2015', 'active'),
            ('losartan 100 mg tablet [RxNorm: 979480]', 'losartan', 'Take 1 tablet by mouth daily', '100 mg', '05/10/2018', 'active'),
            ('atorvastatin 80 mg tablet [RxNorm: 259255]', 'atorvastatin', 'Take 1 tablet by mouth at bedtime', '80 mg', '05/10/2018', 'active'),
            ('amlodipine 10 mg tablet [RxNorm: 197361]', 'amlodipine', 'Take 1 tablet by mouth daily', '10 mg', '11/20/2020', 'active'),
            ('pregabalin 75 mg capsule [RxNorm: 604024]', 'pregabalin', 'Take 1 capsule by mouth three times daily', '75 mg', '03/01/2022', 'active'),
            ('duloxetine 60 mg capsule [RxNorm: 596926]', 'duloxetine', 'Take 1 capsule by mouth daily', '60 mg', '03/01/2022', 'active'),
            ('semaglutide 1 mg injection [RxNorm: 1991302]', 'semaglutide', 'Inject 1 mg subcutaneously once weekly', '1 mg', '01/15/2025', 'active'),
            ('fenofibrate 145 mg tablet [RxNorm: 859419]', 'fenofibrate', 'Take 1 tablet by mouth daily', '145 mg', '08/20/2023', 'active'),
        ],
        'problems': [
            ('Type 1 diabetes mellitus with diabetic CKD [ICD10: E10.22]', 'active', '01/15/1985', ''),
            ('Diabetic retinopathy bilateral [ICD10: E10.319]', 'active', '06/01/2019', ''),
            ('Diabetic peripheral neuropathy [ICD10: E10.42]', 'active', '03/01/2022', ''),
            ('Chronic kidney disease stage 3b [ICD10: N18.32]', 'active', '05/10/2018', ''),
            ('Essential hypertension [ICD10: I10]', 'active', '05/10/2018', ''),
            ('Mixed hyperlipidemia [ICD10: E78.2]', 'active', '05/10/2018', ''),
            ('Obesity BMI 35-39.9 [ICD10: E66.01]', 'active', '01/15/2020', ''),
            ('Major depressive disorder single episode [ICD10: F32.1]', 'active', '03/01/2022', ''),
            ('Erectile dysfunction [ICD10: N52.9]', 'active', '09/15/2023', ''),
            ('Hypoglycemia [ICD10: E10.649]', 'resolved', '02/10/2026', '02/10/2026'),
        ],
        'vitals': [
            ('03/18/2026', '71', '248', '34.6', '134', '82', '78', '98', '98.2', '16'),
            ('12/10/2025', '71', '255', '35.6', '142', '88', '80', '97', '98.6', '16'),
            ('09/10/2025', '71', '260', '36.3', '148', '90', '82', '97', '98.4', '18'),
        ],
        'labs': [
            ('Hemoglobin A1c [LOINC: 4548-4]', '7.2', '%', 'H', '03/15/2026'),
            ('Hemoglobin A1c [LOINC: 4548-4]', '7.8', '%', 'H', '09/10/2025'),
            ('Creatinine [LOINC: 2160-0]', '1.8', 'mg/dL', 'H', '03/15/2026'),
            ('eGFR [LOINC: 48642-3]', '42', 'mL/min/1.73m2', 'L', '03/15/2026'),
            ('Urine Albumin/Creatinine Ratio [LOINC: 9318-7]', '180', 'mg/g', 'H', '03/15/2026'),
            ('Total Cholesterol [LOINC: 2093-3]', '198', 'mg/dL', 'normal', '03/15/2026'),
            ('LDL Cholesterol [LOINC: 2089-1]', '95', 'mg/dL', 'normal', '03/15/2026'),
            ('HDL Cholesterol [LOINC: 2085-9]', '35', 'mg/dL', 'L', '03/15/2026'),
            ('Triglycerides [LOINC: 2571-8]', '340', 'mg/dL', 'H', '03/15/2026'),
            ('Potassium [LOINC: 2823-3]', '5.0', 'mmol/L', 'normal', '03/15/2026'),
            ('CBC WBC [LOINC: 6690-2]', '6.5', '10*3/uL', 'normal', '03/15/2026'),
            ('Hemoglobin [LOINC: 718-7]', '12.8', 'g/dL', 'L', '03/15/2026'),
            ('Vitamin D 25-OH [LOINC: 1989-3]', '32', 'ng/mL', 'normal', '03/15/2026'),
            ('TSH [LOINC: 3016-3]', '4.2', 'mIU/L', 'normal', '03/15/2026'),
        ],
        'immunizations': [
            ('Influenza vaccine 2025-2026', '10/01/2025', 'completed'),
            ('COVID-19 Vaccine 2024-2025 (Moderna)', '09/15/2024', 'completed'),
            ('Pneumococcal PCV20 (Prevnar 20)', '06/15/2024', 'completed'),
            ('Tdap (Boostrix)', '09/10/2020', 'completed'),
            ('Hepatitis B series (3 doses)', '01/01/2000', 'completed'),
        ],
        'social_history': 'Tobacco: Never smoker. Alcohol: Rare, 1-2 drinks/month. Employment: IT project manager, sedentary job. Marital Status: Divorced, lives alone. Exercise: Walks 15 min 3x/week, limited by neuropathy. Diet: Carb counting with pump, struggles with portion control. Support: Diabetes support group monthly.',
        'insurance': [
            ('Anthem Blue Cross', 'Commercial PPO', 'ANT-990003', 'GRP-TECH-500'),
        ],
        'notes': [
            ('03/18/2026', 'Cory Denton, FNP', 'Progress Note',
             'CC: DM1 management, weight loss update.\nHPI: 55yo AA male with DM1 x 41 years on insulin pump. Started semaglutide 1mg Jan 2025 for weight/insulin resistance. Down 12 lbs (260->248). A1c improved 7.8->7.2. Reports 1 hypoglycemic episode Feb 2026 (BG 52, treated with glucose tabs). CGM shows TIR 72%.\nPump settings: Basal reduced 15% since starting semaglutide. ICR 1:8, CF 1:35.\nPE: BMI 34.6 (was 36.3). Feet -- diminished monofilament bilateral, pedal pulses 1+. No ulcers.\nAssessment:\n# DM1 (E10.22): A1c 7.2 improving. Continue pump + semaglutide. Review CGM data -- adjust basal overnight.\n# CKD 3b (N18.32): Cr 1.8, eGFR 42, UACR 180. Continue losartan. Nephrology co-manages.\n# Neuropathy (E10.42): Pain controlled on pregabalin + duloxetine.\n# Hyperlipidemia: LDL at goal. TG still 340. Fenofibrate adequate dose.\n# Obesity: 12 lbs lost. Target another 20 lbs.\n# Retinopathy: Annual ophthalmology visit due -- scheduled.\nPlan: Continue all meds. CGM download next visit. Nephrology 3 months. Ophthalmology annual. A1c in 3 months.'),
            ('09/10/2025', 'Cory Denton, FNP', 'Annual Wellness Visit',
             'ANNUAL WELLNESS VISIT -- G0439\n55yo male with DM1, CKD.\nPreventive:\n- Colorectal: Cologuard 2024 negative. Next 2027.\n- Depression: PHQ-9 = 10 (moderate). Continue duloxetine.\n- Diabetic foot exam: Monofilament diminished. Podiatry referral.\n- Diabetic eye exam: Retinopathy stable per ophthalmology 06/2025.\n- Immunizations: Flu given. PCV20 given 2024.\n- PSA: Discussed, patient declines (informed refusal documented).\nAdvance Directive: On file, updated.'),
        ],
    },
    # ------------------------------------------------------------------
    # 4) Patricia Ann O'Brien -- 78F, post-hip fracture, osteoporosis, dementia
    # ------------------------------------------------------------------
    {
        'mrn': '90004',
        'given': 'Patricia',
        'family': 'OBrien',
        'gender_code': 'F',
        'gender_display': 'Female',
        'birth': '19471022',
        'marital': 'W',
        'marital_display': 'Widowed',
        'race_code': '2106-3',
        'race_display': 'White',
        'ethnic_code': '2186-5',
        'ethnic_display': 'Not Hispanic or Latino',
        'street': '502 Willowbrook Place',
        'city': 'Midlothian',
        'state': 'VA',
        'zip': '23113',
        'phone': '+1(804)-555-1004',
        'allergies': [
            ('Opioids [RxNorm: 27384]', 'Confusion/Delirium', 'severe', 'active'),
            ('Fluoroquinolones [RxNorm: 372832]', 'Tendon rupture risk', 'severe', 'active'),
            ('Shellfish', 'Hives', 'moderate', 'active'),
        ],
        'medications': [
            ('donepezil 10 mg tablet [RxNorm: 312935]', 'donepezil', 'Take 1 tablet by mouth at bedtime', '10 mg', '03/15/2024', 'active'),
            ('memantine 10 mg tablet [RxNorm: 312113]', 'memantine', 'Take 1 tablet by mouth twice daily', '10 mg', '09/01/2024', 'active'),
            ('alendronate 70 mg tablet [RxNorm: 151558]', 'alendronate', 'Take 1 tablet by mouth weekly on empty stomach', '70 mg', '02/01/2026', 'active'),
            ('calcium carbonate 600 mg + D3 400 IU [RxNorm: 215459]', 'calcium/vitamin D', 'Take 1 tablet by mouth twice daily', '600 mg/400 IU', '02/01/2026', 'active'),
            ('acetaminophen 500 mg tablet [RxNorm: 198440]', 'acetaminophen', 'Take 2 tablets by mouth three times daily as needed', '1000 mg', '02/01/2026', 'active'),
            ('levothyroxine 75 mcg tablet [RxNorm: 966202]', 'levothyroxine', 'Take 1 tablet by mouth daily on empty stomach', '75 mcg', '06/20/2019', 'active'),
            ('metoprolol succinate 25 mg tablet [RxNorm: 866924]', 'metoprolol', 'Take 1 tablet by mouth daily', '25 mg', '08/10/2020', 'active'),
            ('sertraline 50 mg tablet [RxNorm: 312938]', 'sertraline', 'Take 1 tablet by mouth daily', '50 mg', '03/15/2024', 'active'),
        ],
        'problems': [
            ('Alzheimer disease dementia moderate [ICD10: G30.1]', 'active', '03/15/2024', ''),
            ('Postmenopausal osteoporosis with pathological fracture [ICD10: M80.08]', 'active', '01/15/2026', ''),
            ('Status post right hip ORIF [ICD10: Z96.641]', 'active', '01/20/2026', ''),
            ('Hypothyroidism [ICD10: E03.9]', 'active', '06/20/2019', ''),
            ('Essential hypertension [ICD10: I10]', 'active', '08/10/2020', ''),
            ('Major depressive disorder recurrent [ICD10: F33.1]', 'active', '03/15/2024', ''),
            ('Fall risk [ICD10: R29.6]', 'active', '01/15/2026', ''),
            ('Urinary incontinence [ICD10: R32]', 'active', '09/01/2025', ''),
            ('Right hip fracture [ICD10: S72.001A]', 'resolved', '01/15/2026', '02/15/2026'),
        ],
        'vitals': [
            ('03/22/2026', '62', '128', '23.4', '126', '72', '68', '97', '98.0', '16'),
            ('02/15/2026', '62', '122', '22.3', '118', '68', '72', '96', '98.2', '18'),
            ('09/15/2025', '62', '135', '24.7', '132', '76', '70', '98', '98.4', '14'),
        ],
        'labs': [
            ('TSH [LOINC: 3016-3]', '3.4', 'mIU/L', 'normal', '03/20/2026'),
            ('Free T4 [LOINC: 3024-7]', '1.1', 'ng/dL', 'normal', '03/20/2026'),
            ('Vitamin D 25-OH [LOINC: 1989-3]', '35', 'ng/mL', 'normal', '03/20/2026'),
            ('Calcium [LOINC: 17861-6]', '9.4', 'mg/dL', 'normal', '03/20/2026'),
            ('CBC WBC [LOINC: 6690-2]', '6.2', '10*3/uL', 'normal', '03/20/2026'),
            ('Hemoglobin [LOINC: 718-7]', '11.8', 'g/dL', 'L', '03/20/2026'),
            ('Creatinine [LOINC: 2160-0]', '0.9', 'mg/dL', 'normal', '03/20/2026'),
            ('Vitamin B12 [LOINC: 2132-9]', '320', 'pg/mL', 'normal', '03/20/2026'),
            ('Folate [LOINC: 2284-8]', '12', 'ng/mL', 'normal', '03/20/2026'),
        ],
        'immunizations': [
            ('Influenza vaccine 2025-2026', '10/20/2025', 'completed'),
            ('Pneumococcal PCV20 (Prevnar 20)', '09/15/2025', 'completed'),
            ('COVID-19 Vaccine 2024-2025 (Pfizer)', '10/15/2024', 'completed'),
            ('Shingrix (Zoster) Dose 1', '03/15/2024', 'completed'),
            ('Shingrix (Zoster) Dose 2', '06/15/2024', 'completed'),
            ('Tdap (Boostrix)', '06/20/2019', 'completed'),
        ],
        'social_history': 'Tobacco: Never smoker. Alcohol: None. Employment: Retired librarian. Marital Status: Widowed (husband died 2020). Lives with daughter who is primary caregiver. Exercise: PT 3x/week for hip rehab, home exercises daily. ADLs: Needs assistance bathing, dressing. Drives: No longer drives. Wandering risk: Yes, door alarms installed.',
        'insurance': [
            ('Medicare Part B', 'Medicare', '2FG5-HI6-JK78', 'N/A'),
            ('Humana Medicare Supplement Plan F', 'Supplemental', 'HUM-554321', 'GRP-66789'),
        ],
        'notes': [
            ('03/22/2026', 'Cory Denton, FNP', 'Progress Note',
             'CC: Post-hip fracture follow-up, dementia management.\nHPI: 78yo female, 2 months s/p right hip ORIF after mechanical fall at home. PT 3x/week, progressing well. Now walking with rolling walker. Pain controlled with scheduled acetaminophen. Daughter reports increased confusion at night (sundowning). MMSE today 18/30 (was 20/30 in Sept). Donepezil + memantine continued.\nPE: Surgical site well-healed. ROM right hip 0-100 degrees flexion. Gait -- slow, steady with walker. No TTP spine. Oriented x2 (person, place). Clock draw: 2/5.\nAssessment:\n# Alzheimer dementia (G30.1): Progressive decline. MMSE 18. Continue donepezil/memantine. Caregiver education on sundowning -- consistent routine, night light, no caffeine after noon.\n# s/p Hip fracture (Z96.641): Healing well. Continue PT. Fall prevention: remove throw rugs, grab bars installed.\n# Osteoporosis (M80.08): Started alendronate + calcium/D post-fracture. Vit D level now 35 (was 22).\n# HTN (I10): BP 126/72. Metoprolol appropriate -- not over-treating.\n# Depression (F33.1): Daughter reports less tearfulness on sertraline. PHQ-9 difficult to administer (cognitive limitations).\nPlan: Continue all meds. PT continue 6 more weeks. Home safety re-evaluation. Consider adult day program for socialization. Caregiver support group info given. Return 6 weeks. Advance directive review with daughter.'),
            ('01/15/2026', 'Gretchen Lockard, MD', 'Acute Visit',
             'CC: Fall at home, right hip pain, unable to bear weight.\nHPI: 78yo with dementia found on floor by daughter at 6 AM. Uncertain how long she was down. Complains of right hip pain. Unable to stand.\nPE: Right leg shortened and externally rotated. TTP right groin. Neurovascular intact distally.\nXR: Right femoral neck fracture, displaced.\nAssessment: Right hip fracture (S72.001A). Osteoporosis likely contributing.\nPlan: Orthopedic consult -- ORIF performed 01/20/2026. Post-op course uncomplicated. Discharged to SNF for rehab 01/25/2026. Start osteoporosis treatment after surgical healing (6 weeks). DEXA ordered. PT/OT daily at SNF.'),
        ],
    },
    # ------------------------------------------------------------------
    # 5) David Michael Chen -- 34M, anxiety/ADHD/migraine, young professional
    # ------------------------------------------------------------------
    {
        'mrn': '90005',
        'given': 'David',
        'family': 'Chen',
        'gender_code': 'M',
        'gender_display': 'Male',
        'birth': '19911115',
        'marital': 'S',
        'marital_display': 'Single',
        'race_code': '2028-9',
        'race_display': 'Asian',
        'ethnic_code': '2186-5',
        'ethnic_display': 'Not Hispanic or Latino',
        'street': '1100 Monument Avenue Apt 4B',
        'city': 'Richmond',
        'state': 'VA',
        'zip': '23220',
        'phone': '+1(804)-555-1005',
        'allergies': [
            ('Amoxicillin [RxNorm: 723]', 'Rash', 'mild', 'active'),
        ],
        'medications': [
            ('lisdexamfetamine 50 mg capsule [RxNorm: 854838]', 'lisdexamfetamine', 'Take 1 capsule by mouth each morning', '50 mg', '09/01/2022', 'active'),
            ('escitalopram 20 mg tablet [RxNorm: 352741]', 'escitalopram', 'Take 1 tablet by mouth daily', '20 mg', '03/15/2023', 'active'),
            ('sumatriptan 100 mg tablet [RxNorm: 313197]', 'sumatriptan', 'Take 1 tablet at onset of migraine, may repeat x1 in 2 hours', '100 mg', '06/01/2020', 'active'),
            ('topiramate 50 mg tablet [RxNorm: 38404]', 'topiramate', 'Take 1 tablet by mouth at bedtime', '50 mg', '01/10/2025', 'active'),
            ('melatonin 3 mg tablet', 'melatonin', 'Take 1 tablet by mouth at bedtime', '3 mg', '09/01/2022', 'active'),
        ],
        'problems': [
            ('Attention deficit hyperactivity disorder combined [ICD10: F90.2]', 'active', '09/01/2022', ''),
            ('Generalized anxiety disorder [ICD10: F41.1]', 'active', '03/15/2023', ''),
            ('Migraine without aura [ICD10: G43.009]', 'active', '06/01/2020', ''),
            ('Insomnia [ICD10: G47.00]', 'active', '09/01/2022', ''),
            ('Seasonal allergic rhinitis [ICD10: J30.2]', 'active', '04/01/2019', ''),
            ('Acute pharyngitis [ICD10: J02.9]', 'resolved', '02/05/2026', '02/15/2026'),
        ],
        'vitals': [
            ('03/10/2026', '69', '165', '24.4', '118', '74', '68', '99', '98.4', '14'),
            ('09/15/2025', '69', '162', '23.9', '116', '72', '72', '99', '98.6', '14'),
        ],
        'labs': [
            ('CBC WBC [LOINC: 6690-2]', '6.8', '10*3/uL', 'normal', '03/05/2026'),
            ('Hemoglobin [LOINC: 718-7]', '15.2', 'g/dL', 'normal', '03/05/2026'),
            ('TSH [LOINC: 3016-3]', '1.8', 'mIU/L', 'normal', '03/05/2026'),
            ('Comprehensive Metabolic Panel [LOINC: 24323-8]', 'normal', '', 'normal', '03/05/2026'),
            ('Vitamin D 25-OH [LOINC: 1989-3]', '42', 'ng/mL', 'normal', '03/05/2026'),
            ('Lipid Panel [LOINC: 24331-1]', 'TC 185, LDL 108, HDL 55, TG 110', '', 'normal', '03/05/2026'),
        ],
        'immunizations': [
            ('Influenza vaccine 2025-2026', '10/10/2025', 'completed'),
            ('COVID-19 Vaccine 2024-2025 (Pfizer)', '09/25/2024', 'completed'),
            ('Tdap (Boostrix)', '09/01/2022', 'completed'),
            ('Hepatitis B series (3 doses)', '01/01/2010', 'completed'),
            ('MMR (2 doses)', '01/01/1992', 'completed'),
        ],
        'social_history': 'Tobacco: Never smoker. Alcohol: Social, 3-4 drinks/weekend. Cannabis: Occasional edibles for sleep. Employment: Software engineer, high-stress startup. Marital Status: Single, lives alone. Exercise: Rock climbing 2x/week, runs 3x/week. Screen time: 10+ hours/day.',
        'insurance': [
            ('Cigna', 'Commercial HMO', 'CIG-905005', 'GRP-TECH-200'),
        ],
        'notes': [
            ('03/10/2026', 'Cory Denton, FNP', 'Progress Note',
             'CC: ADHD med check, migraine frequency.\nHPI: 34yo male here for scheduled ADHD/anxiety follow-up. Vyvanse 50mg working well for focus. Reports anxiety improved on escitalopram 20mg -- fewer panic episodes. Migraines decreased from 8/month to 3/month since starting topiramate in January. Uses sumatriptan PRN for breakthrough. Sleep improved with melatonin + sleep hygiene.\nScreening: PHQ-9 = 6 (mild). GAD-7 = 8 (mild). ASRS consistent with ongoing ADHD.\nPE: Vitals normal. BP 118/74. Well-appearing, calm affect.\nAssessment:\n# ADHD (F90.2): Stable on Vyvanse 50. No appetite issues, weight stable. Continue.\n# GAD (F41.1): Improved. Continue escitalopram 20.\n# Migraine (G43.009): Topiramate effective. Down to 3/month. Continue.\n# Insomnia (G47.00): Improved with melatonin + sleep hygiene.\nPlan: Continue all meds. Vyvanse Rx (30-day supply, no refills per policy). Return 3 months. Headache diary continue. Consider referral to therapist for CBT if anxiety plateaus.'),
            ('09/15/2025', 'Cory Denton, FNP', 'Annual Wellness Visit',
             'ANNUAL WELLNESS VISIT\n34yo healthy male.\nPreventive:\n- Depression: PHQ-9 = 8 (mild). On treatment.\n- STI screening: Discussed. Patient declines (monogamous relationship ended, currently abstinent).\n- Testicular self-exam: Counseled.\n- Substance use: AUDIT-C = 3 (low risk). Cannabis occasional -- counseled.\n- Immunizations: Flu given. All up to date.\n- Labs: TSH, CMP, lipids, Vit D -- all normal.'),
        ],
    },
    # ------------------------------------------------------------------
    # 6) Susan Marie Foster -- 62F, breast cancer survivor, fibromyalgia
    # ------------------------------------------------------------------
    {
        'mrn': '90006',
        'given': 'Susan',
        'family': 'Foster',
        'gender_code': 'F',
        'gender_display': 'Female',
        'birth': '19631215',
        'marital': 'M',
        'marital_display': 'Married',
        'race_code': '2106-3',
        'race_display': 'White',
        'ethnic_code': '2186-5',
        'ethnic_display': 'Not Hispanic or Latino',
        'street': '8845 Brookfield Lane',
        'city': 'Chesterfield',
        'state': 'VA',
        'zip': '23832',
        'phone': '+1(804)-555-1006',
        'allergies': [
            ('Tramadol [RxNorm: 10689]', 'Seizure', 'severe', 'active'),
            ('Erythromycin [RxNorm: 4053]', 'GI upset', 'moderate', 'active'),
        ],
        'medications': [
            ('anastrozole 1 mg tablet [RxNorm: 261513]', 'anastrozole', 'Take 1 tablet by mouth daily', '1 mg', '06/01/2023', 'active'),
            ('duloxetine 60 mg capsule [RxNorm: 596926]', 'duloxetine', 'Take 1 capsule by mouth daily', '60 mg', '01/15/2022', 'active'),
            ('pregabalin 150 mg capsule [RxNorm: 604024]', 'pregabalin', 'Take 1 capsule by mouth twice daily', '150 mg', '01/15/2022', 'active'),
            ('alendronate 70 mg tablet [RxNorm: 151558]', 'alendronate', 'Take 1 tablet weekly on empty stomach', '70 mg', '09/01/2023', 'active'),
            ('calcium/vitamin D 600mg/400IU [RxNorm: 215459]', 'calcium/vitamin D', 'Take 1 tablet twice daily', '600 mg/400 IU', '09/01/2023', 'active'),
            ('lisinopril 10 mg tablet [RxNorm: 314076]', 'lisinopril', 'Take 1 tablet by mouth daily', '10 mg', '05/20/2020', 'active'),
            ('zolpidem 5 mg tablet [RxNorm: 312236]', 'zolpidem', 'Take 1 tablet by mouth at bedtime as needed', '5 mg', '01/15/2022', 'active'),
        ],
        'problems': [
            ('Personal history of breast cancer [ICD10: Z85.3]', 'active', '03/15/2023', ''),
            ('Fibromyalgia [ICD10: M79.7]', 'active', '01/15/2022', ''),
            ('Insomnia [ICD10: G47.00]', 'active', '01/15/2022', ''),
            ('Osteopenia [ICD10: M85.80]', 'active', '09/01/2023', ''),
            ('Essential hypertension [ICD10: I10]', 'active', '05/20/2020', ''),
            ('Aromatase inhibitor arthralgia [ICD10: M25.50]', 'active', '09/01/2023', ''),
            ('Hot flashes [ICD10: N95.1]', 'active', '06/01/2023', ''),
            ('Left breast cancer Stage IIA ER+ PR+ HER2- [ICD10: C50.912]', 'resolved', '03/15/2023', '06/15/2023'),
        ],
        'vitals': [
            ('03/12/2026', '65', '158', '26.3', '128', '78', '72', '98', '98.4', '14'),
            ('09/10/2025', '65', '155', '25.8', '124', '76', '70', '99', '98.6', '14'),
        ],
        'labs': [
            ('CBC WBC [LOINC: 6690-2]', '5.8', '10*3/uL', 'normal', '03/08/2026'),
            ('Hemoglobin [LOINC: 718-7]', '13.2', 'g/dL', 'normal', '03/08/2026'),
            ('Comprehensive Metabolic Panel [LOINC: 24323-8]', 'normal', '', 'normal', '03/08/2026'),
            ('Vitamin D 25-OH [LOINC: 1989-3]', '38', 'ng/mL', 'normal', '03/08/2026'),
            ('ESR [LOINC: 30341-2]', '18', 'mm/hr', 'normal', '03/08/2026'),
            ('ANA [LOINC: 8061-4]', 'Negative', '', 'normal', '01/15/2022'),
            ('TSH [LOINC: 3016-3]', '2.1', 'mIU/L', 'normal', '03/08/2026'),
        ],
        'immunizations': [
            ('Influenza vaccine 2025-2026', '10/12/2025', 'completed'),
            ('COVID-19 Vaccine 2024-2025 (Moderna)', '10/01/2024', 'completed'),
            ('Shingrix (Zoster) Dose 1', '01/15/2025', 'completed'),
            ('Shingrix (Zoster) Dose 2', '04/15/2025', 'completed'),
            ('Tdap (Boostrix)', '05/15/2020', 'completed'),
        ],
        'social_history': 'Tobacco: Never smoker. Alcohol: 1 glass wine with dinner occasionally. Employment: Middle school teacher, full-time. Marital Status: Married 35 years. 3 adult children. Exercise: Walks 30 min daily, water aerobics 2x/week. Stress: Moderate -- managing cancer survivorship anxiety.',
        'insurance': [
            ('Anthem Blue Cross', 'Commercial PPO', 'ANT-906006', 'GRP-EDU-100'),
        ],
        'notes': [
            ('03/12/2026', 'Cory Denton, FNP', 'Progress Note',
             'CC: Fibromyalgia flare, cancer survivorship follow-up.\nHPI: 62yo female, 3 years post left lumpectomy + radiation for stage IIA ER+/PR+/HER2- breast cancer. On anastrozole x 3 years (planned 5-year course). Oncology last visit 01/2026 -- NED. Reports fibromyalgia flare this month: widespread pain, fatigue, poor sleep. Fibromyalgia Impact Questionnaire score 58 (moderate-severe). Joint pain may be mixed fibro + aromatase inhibitor arthralgia.\nPE: 18-point tender point exam: 14/18 positive. Joints -- no effusion, full ROM. Breast exam: surgical site well-healed, no masses.\nAssessment:\n# Fibromyalgia (M79.7): Flare. Duloxetine + pregabalin at good doses. Add PT referral for aquatic therapy. Sleep hygiene review.\n# Breast cancer survivorship (Z85.3): NED. Anastrozole continue. Mammogram due 06/2026.\n# AI arthralgia (M25.50): Contributing to fibro flare. Consider switching to letrozole if intolerable.\n# Osteopenia (M85.80): On alendronate + calcium/D. DEXA due 09/2026.\n# Insomnia: Zolpidem PRN. Discussed CBT-I as alternative.\nPlan: PT referral. Continue meds. Mammogram ordered. DEXA in 6 months. Oncology 6 months. Return 6 weeks for pain reassessment.'),
        ],
    },
    # ------------------------------------------------------------------
    # 7) Thomas Raymond Jackson -- 72M, Parkinson's, falls, polypharmacy
    # ------------------------------------------------------------------
    {
        'mrn': '90007',
        'given': 'Thomas',
        'family': 'Jackson',
        'gender_code': 'M',
        'gender_display': 'Male',
        'birth': '19531230',
        'marital': 'M',
        'marital_display': 'Married',
        'race_code': '2054-5',
        'race_display': 'Black or African American',
        'ethnic_code': '2186-5',
        'ethnic_display': 'Not Hispanic or Latino',
        'street': '3310 Riverdale Road',
        'city': 'Richmond',
        'state': 'VA',
        'zip': '23234',
        'phone': '+1(804)-555-1007',
        'allergies': [
            ('Metoclopramide [RxNorm: 6915]', 'Worsens Parkinsonism', 'severe', 'active'),
            ('Haloperidol [RxNorm: 5093]', 'Neuroleptic sensitivity', 'severe', 'active'),
        ],
        'medications': [
            ('carbidopa-levodopa 25-100 mg tablet [RxNorm: 197748]', 'carbidopa/levodopa', 'Take 1 tablet by mouth four times daily', '25/100 mg', '06/15/2021', 'active'),
            ('ropinirole 2 mg tablet [RxNorm: 73178]', 'ropinirole', 'Take 1 tablet by mouth three times daily', '2 mg', '01/10/2023', 'active'),
            ('rivastigmine 9.5 mg patch [RxNorm: 860092]', 'rivastigmine', 'Apply 1 patch daily', '9.5 mg/24h', '09/01/2024', 'active'),
            ('carbidopa-levodopa ER 50-200 mg [RxNorm: 197748]', 'carbidopa/levodopa ER', 'Take 1 tablet at bedtime', '50/200 mg', '06/15/2021', 'active'),
            ('tamsulosin 0.4 mg capsule [RxNorm: 373480]', 'tamsulosin', 'Take 1 capsule by mouth at bedtime', '0.4 mg', '03/20/2024', 'active'),
            ('polyethylene glycol 17 g powder [RxNorm: 198093]', 'polyethylene glycol', 'Mix 1 capful in 8 oz water daily', '17 g', '06/15/2021', 'active'),
            ('vitamin D3 2000 IU tablet [RxNorm: 392263]', 'cholecalciferol', 'Take 1 tablet daily', '2000 IU', '01/01/2024', 'active'),
        ],
        'problems': [
            ('Parkinson disease [ICD10: G20]', 'active', '06/15/2021', ''),
            ('Parkinson disease dementia [ICD10: G31.83]', 'active', '09/01/2024', ''),
            ('Orthostatic hypotension [ICD10: I95.1]', 'active', '01/10/2023', ''),
            ('Neurogenic bladder [ICD10: N31.9]', 'active', '03/20/2024', ''),
            ('Chronic constipation [ICD10: K59.00]', 'active', '06/15/2021', ''),
            ('REM sleep behavior disorder [ICD10: G47.52]', 'active', '06/15/2021', ''),
            ('Benign prostatic hyperplasia [ICD10: N40.0]', 'active', '03/20/2024', ''),
            ('Fall risk [ICD10: R29.6]', 'active', '01/10/2023', ''),
            ('Vitamin D insufficiency [ICD10: E55.9]', 'active', '01/01/2024', ''),
            ('Cellulitis left shin [ICD10: L03.116]', 'resolved', '02/01/2026', '02/15/2026'),
        ],
        'vitals': [
            ('03/19/2026', '68', '172', '26.2', '128/78 seated; 108/64 standing', '', '64', '97', '98.2', '16'),
            ('12/05/2025', '68', '175', '26.6', '130', '80', '66', '97', '98.4', '14'),
            ('09/01/2025', '68', '178', '27.1', '134', '82', '68', '98', '98.6', '16'),
        ],
        'labs': [
            ('CBC WBC [LOINC: 6690-2]', '7.0', '10*3/uL', 'normal', '03/15/2026'),
            ('Hemoglobin [LOINC: 718-7]', '14.0', 'g/dL', 'normal', '03/15/2026'),
            ('Comprehensive Metabolic Panel [LOINC: 24323-8]', 'normal', '', 'normal', '03/15/2026'),
            ('Vitamin D 25-OH [LOINC: 1989-3]', '30', 'ng/mL', 'normal', '03/15/2026'),
            ('PSA [LOINC: 2857-1]', '2.1', 'ng/mL', 'normal', '03/15/2026'),
            ('Urinalysis [LOINC: 24357-6]', 'normal', '', 'normal', '03/15/2026'),
        ],
        'immunizations': [
            ('Influenza vaccine 2025-2026', '10/08/2025', 'completed'),
            ('COVID-19 Vaccine 2024-2025 (Pfizer)', '10/20/2024', 'completed'),
            ('Pneumococcal PCV20 (Prevnar 20)', '06/01/2024', 'completed'),
            ('Shingrix (Zoster) complete', '03/15/2023', 'completed'),
            ('Tdap (Boostrix)', '09/01/2021', 'completed'),
        ],
        'social_history': 'Tobacco: Former smoker (quit 1995, 10 pack-years). Alcohol: None. Employment: Retired postal worker. Marital Status: Married 48 years. Lives with wife. Exercise: PT 2x/week. Uses rolling walker. Home: Single-story, grab bars installed. Caregiver: Wife, with home health aide 3 days/week. Driving: Stopped 2024.',
        'insurance': [
            ('Medicare Part B', 'Medicare', '3GH7-IJ8-KL90', 'N/A'),
            ('United Healthcare Medicare Advantage', 'Medicare Advantage', 'UHC-770987', 'GRP-RETIREE'),
        ],
        'notes': [
            ('03/19/2026', 'Cory Denton, FNP', 'Progress Note',
             'CC: Parkinson follow-up, increased freezing.\nHPI: 72yo AA male with PD x 5 years, Hoehn and Yahr Stage 3. Reports increased freezing episodes, especially doorways and turning. 2 falls in past month (no injury). Wife reports more vivid dreams and occasional talking in sleep (RBD). Cognitive decline -- rivastigmine patch started 6 months ago. MMSE 22/30 today. Orthostatic symptoms: dizzy on standing, better if rises slowly.\nPE: Masked facies. Pill-rolling tremor bilateral (L>R). Rigidity -- cogwheel bilateral UE. Gait: festinating, freezing at turns. Postural instability -- retropulsion on pull test. Orthostatics confirmed: 128/78 seated, 108/64 standing at 3 min.\nAssessment:\n# Parkinson disease (G20): Stage 3. Wearing off before next dose. Add extra Sinemet dose (now 5x/day q3h while awake). Consider entacapone if still wearing off.\n# PD Dementia (G31.83): MMSE 22. Rivastigmine continued. Small improvement per wife.\n# Orthostatic hypotension (I95.1): Symptomatic. Increase fluid/salt intake. Consider fludrocortisone 0.1 mg if persists. Compression stockings.\n# Falls (R29.6): 2 falls this month. PT reassessment. OT home eval. Consider hip protectors.\n# Constipation: MiraLax daily, adequate. BM every 1-2 days.\nPlan: Add Sinemet dose. PT/OT referrals. Orthostatic precautions handout. Neurology in 2 months. Return 6 weeks.'),
        ],
    },
    # ------------------------------------------------------------------
    # 8) Emily Rose Taylor -- 28F, pregnancy, gestational diabetes
    # ------------------------------------------------------------------
    {
        'mrn': '90008',
        'given': 'Emily',
        'family': 'Taylor',
        'gender_code': 'F',
        'gender_display': 'Female',
        'birth': '19970503',
        'marital': 'M',
        'marital_display': 'Married',
        'race_code': '2106-3',
        'race_display': 'White',
        'ethnic_code': '2186-5',
        'ethnic_display': 'Not Hispanic or Latino',
        'street': '6625 Autumn Glen Way',
        'city': 'Moseley',
        'state': 'VA',
        'zip': '23120',
        'phone': '+1(804)-555-1008',
        'allergies': [
            ('No Known Allergies', '', '', 'active'),
        ],
        'medications': [
            ('prenatal vitamin tablet [RxNorm: 208945]', 'prenatal multivitamin', 'Take 1 tablet by mouth daily', '1 tablet', '06/01/2025', 'active'),
            ('insulin glargine 100 units/mL [RxNorm: 261551]', 'insulin glargine', 'Inject 12 units subcutaneously at bedtime', '12 units', '01/20/2026', 'active'),
            ('insulin aspart 100 units/mL [RxNorm: 1160696]', 'insulin aspart', 'Inject per sliding scale before meals', 'variable', '01/20/2026', 'active'),
            ('ondansetron 4 mg tablet [RxNorm: 312087]', 'ondansetron', 'Take 1 tablet by mouth every 8 hours as needed for nausea', '4 mg', '08/15/2025', 'inactive'),
        ],
        'problems': [
            ('Pregnancy 32 weeks [ICD10: Z3A.32]', 'active', '07/15/2025', ''),
            ('Gestational diabetes mellitus [ICD10: O24.419]', 'active', '01/15/2026', ''),
            ('Hyperemesis gravidarum resolved [ICD10: O21.1]', 'resolved', '08/01/2025', '11/01/2025'),
            ('Iron deficiency anemia of pregnancy [ICD10: O99.012]', 'active', '12/01/2025', ''),
            ('Anxiety related to pregnancy [ICD10: O99.342]', 'active', '07/15/2025', ''),
        ],
        'vitals': [
            ('03/20/2026', '66', '172', '27.8', '122', '76', '82', '99', '98.4', '16'),
            ('02/20/2026', '66', '168', '27.1', '118', '74', '80', '99', '98.2', '16'),
            ('01/15/2026', '66', '162', '26.2', '116', '72', '78', '99', '98.6', '14'),
        ],
        'labs': [
            ('Hemoglobin A1c [LOINC: 4548-4]', '5.8', '%', 'normal', '01/15/2026'),
            ('Glucose 1-hour [LOINC: 1558-6]', '192', 'mg/dL', 'H', '01/15/2026'),
            ('Glucose 3-hour GTT fasting [LOINC: 1558-6]', '98', 'mg/dL', 'H', '01/18/2026'),
            ('Glucose 3-hour GTT 1hr [LOINC: 1558-6]', '205', 'mg/dL', 'H', '01/18/2026'),
            ('Glucose 3-hour GTT 2hr [LOINC: 1558-6]', '178', 'mg/dL', 'H', '01/18/2026'),
            ('Glucose 3-hour GTT 3hr [LOINC: 1558-6]', '145', 'mg/dL', 'H', '01/18/2026'),
            ('Hemoglobin [LOINC: 718-7]', '10.5', 'g/dL', 'L', '03/15/2026'),
            ('Ferritin [LOINC: 2276-4]', '8', 'ng/mL', 'L', '03/15/2026'),
            ('CBC WBC [LOINC: 6690-2]', '10.2', '10*3/uL', 'normal', '03/15/2026'),
            ('Platelet Count [LOINC: 777-3]', '245', '10*3/uL', 'normal', '03/15/2026'),
            ('Group B Strep [LOINC: 72607-5]', 'Pending', '', '', '03/20/2026'),
            ('Blood Type [LOINC: 882-1]', 'A positive', '', 'normal', '07/20/2025'),
            ('Antibody Screen [LOINC: 890-4]', 'Negative', '', 'normal', '07/20/2025'),
        ],
        'immunizations': [
            ('Influenza vaccine 2025-2026', '10/15/2025', 'completed'),
            ('Tdap (Boostrix) - prenatal', '02/20/2026', 'completed'),
            ('COVID-19 Vaccine 2024-2025 (Pfizer)', '09/01/2024', 'completed'),
        ],
        'social_history': 'Tobacco: Never smoker. Alcohol: None (pregnant). Employment: Elementary school teacher, maternity leave starting April. Marital Status: Married 2 years. G1P0. Exercise: Prenatal yoga 2x/week, walks daily. Support: Husband supportive, parents nearby.',
        'insurance': [
            ('Anthem Blue Cross', 'Commercial PPO', 'ANT-908008', 'GRP-EDU-100'),
        ],
        'notes': [
            ('03/20/2026', 'Cory Denton, FNP', 'Progress Note',
             'CC: Prenatal visit 32 weeks, GDM management.\nHPI: 28yo G1P0 at 32w0d. GDM diagnosed at 28 weeks. On insulin glargine 12 units qhs + aspart sliding scale. BG logs: fasting 88-102, post-meal peaks 120-145. No hypoglycemia. Reports good fetal movement. No contractions, leaking, bleeding.\nPE: Fundal height 32 cm (appropriate). FHR 148 by doppler. Edema: trace bilateral ankles. BP 122/76.\nAssessment:\n# Pregnancy 32 wks (Z3A.32): Uncomplicated aside from GDM. Growth ultrasound ordered 34 weeks.\n# GDM (O24.419): Well-controlled on current insulin. Continue home BG monitoring QID.\n# Anemia (O99.012): Hgb 10.5, ferritin 8. Start IV iron infusion series (oral not tolerated).\n# Anxiety: Mild. Discussed birth plan. Supportive counseling.\nPlan: IV iron infusion x 3 (weekly). Growth US 34 weeks. GBS culture done today. BG logs at next visit. NST starting 36 weeks. Next visit 2 weeks.'),
        ],
    },
    # ------------------------------------------------------------------
    # 9) William Henry Brooks -- 58M, liver cirrhosis, alcohol use disorder
    # ------------------------------------------------------------------
    {
        'mrn': '90009',
        'given': 'William',
        'family': 'Brooks',
        'gender_code': 'M',
        'gender_display': 'Male',
        'birth': '19671112',
        'marital': 'D',
        'marital_display': 'Divorced',
        'race_code': '2106-3',
        'race_display': 'White',
        'ethnic_code': '2186-5',
        'ethnic_display': 'Not Hispanic or Latino',
        'street': '2404 Huguenot Road',
        'city': 'Richmond',
        'state': 'VA',
        'zip': '23235',
        'phone': '+1(804)-555-1009',
        'allergies': [
            ('Acetaminophen [RxNorm: 161]', 'Hepatotoxicity risk', 'severe', 'active'),
            ('NSAIDs [RxNorm: 7258]', 'GI bleeding risk', 'severe', 'active'),
        ],
        'medications': [
            ('furosemide 40 mg tablet [RxNorm: 310429]', 'furosemide', 'Take 1 tablet by mouth daily', '40 mg', '08/01/2024', 'active'),
            ('spironolactone 100 mg tablet [RxNorm: 312600]', 'spironolactone', 'Take 1 tablet by mouth daily', '100 mg', '08/01/2024', 'active'),
            ('lactulose 10 g/15 mL solution [RxNorm: 197971]', 'lactulose', 'Take 30 mL by mouth 2-3 times daily, titrate to 2-3 soft BMs', '20 g', '08/01/2024', 'active'),
            ('rifaximin 550 mg tablet [RxNorm: 859419]', 'rifaximin', 'Take 1 tablet by mouth twice daily', '550 mg', '11/01/2024', 'active'),
            ('nadolol 40 mg tablet [RxNorm: 197748]', 'nadolol', 'Take 1 tablet by mouth daily', '40 mg', '08/01/2024', 'active'),
            ('naltrexone 50 mg tablet [RxNorm: 197382]', 'naltrexone', 'Take 1 tablet by mouth daily', '50 mg', '06/15/2024', 'active'),
            ('thiamine 100 mg tablet [RxNorm: 312611]', 'thiamine', 'Take 1 tablet by mouth daily', '100 mg', '06/15/2024', 'active'),
            ('folic acid 1 mg tablet [RxNorm: 310539]', 'folic acid', 'Take 1 tablet by mouth daily', '1 mg', '06/15/2024', 'active'),
        ],
        'problems': [
            ('Alcoholic cirrhosis of liver [ICD10: K70.30]', 'active', '08/01/2024', ''),
            ('Portal hypertension [ICD10: K76.6]', 'active', '08/01/2024', ''),
            ('Esophageal varices without bleeding [ICD10: I85.00]', 'active', '09/15/2024', ''),
            ('Ascites [ICD10: R18.8]', 'active', '08/01/2024', ''),
            ('Alcohol use disorder severe in early remission [ICD10: F10.21]', 'active', '06/15/2024', ''),
            ('Hepatic encephalopathy [ICD10: K72.90]', 'active', '11/01/2024', ''),
            ('Thrombocytopenia [ICD10: D69.6]', 'active', '08/01/2024', ''),
            ('Malnutrition [ICD10: E46]', 'active', '08/01/2024', ''),
            ('Hepatic encephalopathy episode [ICD10: K72.90]', 'resolved', '01/05/2026', '01/15/2026'),
        ],
        'vitals': [
            ('03/18/2026', '72', '185', '25.1', '108', '66', '58', '96', '98.0', '16'),
            ('01/05/2026', '72', '192', '26.0', '100', '60', '54', '95', '97.8', '18'),
            ('10/15/2025', '72', '180', '24.4', '112', '68', '62', '97', '98.4', '16'),
        ],
        'labs': [
            ('Total Bilirubin [LOINC: 1975-2]', '3.2', 'mg/dL', 'H', '03/15/2026'),
            ('Direct Bilirubin [LOINC: 1968-7]', '1.8', 'mg/dL', 'H', '03/15/2026'),
            ('Albumin [LOINC: 1751-7]', '2.8', 'g/dL', 'L', '03/15/2026'),
            ('INR [LOINC: 6301-6]', '1.6', '', 'H', '03/15/2026'),
            ('Creatinine [LOINC: 2160-0]', '1.1', 'mg/dL', 'normal', '03/15/2026'),
            ('Sodium [LOINC: 2951-2]', '132', 'mmol/L', 'L', '03/15/2026'),
            ('Platelet Count [LOINC: 777-3]', '68', '10*3/uL', 'L', '03/15/2026'),
            ('AST [LOINC: 1920-8]', '85', 'U/L', 'H', '03/15/2026'),
            ('ALT [LOINC: 1742-6]', '52', 'U/L', 'H', '03/15/2026'),
            ('Ammonia [LOINC: 1988-5]', '48', 'umol/L', 'H', '03/15/2026'),
            ('AFP [LOINC: 1834-1]', '8.2', 'ng/mL', 'normal', '03/15/2026'),
            ('Hemoglobin [LOINC: 718-7]', '11.2', 'g/dL', 'L', '03/15/2026'),
            ('CBC WBC [LOINC: 6690-2]', '4.5', '10*3/uL', 'normal', '03/15/2026'),
        ],
        'immunizations': [
            ('Influenza vaccine 2025-2026', '10/20/2025', 'completed'),
            ('Hepatitis A vaccine (2 doses)', '09/01/2024', 'completed'),
            ('Hepatitis B series (3 doses)', '12/01/2024', 'completed'),
            ('Pneumococcal PCV20 (Prevnar 20)', '09/01/2024', 'completed'),
            ('COVID-19 Vaccine 2024-2025 (Pfizer)', '10/15/2024', 'completed'),
        ],
        'social_history': 'Tobacco: Former smoker (quit 2024, 25 pack-years). Alcohol: In early remission -- last drink June 2024. Previous consumption: 12-18 beers/day x 20 years. Attends AA 3x/week. Employment: Unemployed/disabled. Marital Status: Divorced (2022). Lives in sober-living facility. Children: 2 adult children, limited contact. Support: AA sponsor, therapist weekly.',
        'insurance': [
            ('Virginia Medicaid', 'Medicaid', 'MCD-990009', 'N/A'),
        ],
        'notes': [
            ('03/18/2026', 'Cory Denton, FNP', 'Progress Note',
             'CC: Cirrhosis follow-up, hepatology co-management.\nHPI: 58yo male with alcoholic cirrhosis (Child-Pugh B, MELD 16). Sober since June 2024 on naltrexone. Reports compliance with lactulose -- 2-3 BMs daily, no confusion episodes since January admission. Abdomen: moderate ascites, last paracentesis 02/2026 (3L removed). Weight 185 (down from 192 after para). No melena, hematemesis. Eating better -- sees nutritionist monthly.\nPE: Jaundice mild. Spider angiomata on chest. Abdomen: distended, fluid wave present, nontender. No asterixis. Oriented x3. Extremities: 1+ pretibial edema.\nAssessment:\n# Cirrhosis (K70.30): Child-Pugh B (score 8). MELD 16. Continue diuretics. Hepatology transplant evaluation in progress.\n# Ascites (R18.8): Moderate. Sodium restriction <2g/day. May need paracentesis in 4 weeks.\n# HE (K72.90): Stable on lactulose + rifaximin. No episodes x 2 months.\n# Varices (I85.00): EGD 09/2024 showed grade II. Nadolol for prophylaxis. Repeat EGD due 09/2026.\n# AUD (F10.21): 21 months sober. Continue naltrexone, AA, therapy.\n# Malnutrition: Albumin 2.8. High-protein diet. Nutritionist.\n# HCC surveillance: AFP 8.2 normal. Liver US q6 months -- due 06/2026.\nPlan: Continue all meds. Paracentesis if symptomatic. Hepatology transplant eval. Liver US 06/2026. Labs monthly. Return 4 weeks.'),
        ],
    },
    # ------------------------------------------------------------------
    # 10) Linda Kay Morrison -- 50F, rheumatoid arthritis, on biologics
    # ------------------------------------------------------------------
    {
        'mrn': '90010',
        'given': 'Linda',
        'family': 'Morrison',
        'gender_code': 'F',
        'gender_display': 'Female',
        'birth': '19750620',
        'marital': 'M',
        'marital_display': 'Married',
        'race_code': '2106-3',
        'race_display': 'White',
        'ethnic_code': '2186-5',
        'ethnic_display': 'Not Hispanic or Latino',
        'street': '9101 Timber Ridge Lane',
        'city': 'Midlothian',
        'state': 'VA',
        'zip': '23112',
        'phone': '+1(804)-555-1010',
        'allergies': [
            ('Penicillins [RxNorm: 7980]', 'Hives', 'moderate', 'active'),
            ('Methotrexate [RxNorm: 6851]', 'Liver toxicity', 'severe', 'active'),
        ],
        'medications': [
            ('adalimumab 40 mg injection [RxNorm: 352056]', 'adalimumab', 'Inject 40 mg subcutaneously every other week', '40 mg', '03/01/2023', 'active'),
            ('leflunomide 20 mg tablet [RxNorm: 197584]', 'leflunomide', 'Take 1 tablet by mouth daily', '20 mg', '03/01/2023', 'active'),
            ('prednisone 5 mg tablet [RxNorm: 312617]', 'prednisone', 'Take 1 tablet by mouth daily', '5 mg', '01/15/2023', 'active'),
            ('folic acid 1 mg tablet [RxNorm: 310539]', 'folic acid', 'Take 1 tablet by mouth daily', '1 mg', '03/01/2023', 'active'),
            ('omeprazole 20 mg capsule [RxNorm: 198053]', 'omeprazole', 'Take 1 capsule daily before breakfast', '20 mg', '01/15/2023', 'active'),
            ('amlodipine 5 mg tablet [RxNorm: 197361]', 'amlodipine', 'Take 1 tablet by mouth daily', '5 mg', '09/01/2024', 'active'),
        ],
        'problems': [
            ('Rheumatoid arthritis [ICD10: M06.9]', 'active', '01/15/2023', ''),
            ('Essential hypertension [ICD10: I10]', 'active', '09/01/2024', ''),
            ('Gastroesophageal reflux disease [ICD10: K21.0]', 'active', '01/15/2023', ''),
            ('Steroid-induced osteopenia [ICD10: M81.8]', 'active', '03/01/2024', ''),
            ('Latent tuberculosis [ICD10: R76.11]', 'active', '02/15/2023', ''),
            ('RA flare [ICD10: M06.9]', 'resolved', '11/01/2025', '12/15/2025'),
        ],
        'vitals': [
            ('03/15/2026', '64', '148', '25.4', '126', '78', '74', '99', '98.4', '14'),
            ('11/01/2025', '64', '145', '24.9', '132', '82', '80', '98', '99.8', '18'),
            ('08/15/2025', '64', '146', '25.1', '124', '76', '72', '99', '98.6', '14'),
        ],
        'labs': [
            ('ESR [LOINC: 30341-2]', '22', 'mm/hr', 'normal', '03/10/2026'),
            ('CRP [LOINC: 1988-5]', '0.6', 'mg/dL', 'normal', '03/10/2026'),
            ('RF [LOINC: 11572-5]', '85', 'IU/mL', 'H', '01/15/2023'),
            ('Anti-CCP [LOINC: 53027-9]', '120', 'U/mL', 'H', '01/15/2023'),
            ('CBC WBC [LOINC: 6690-2]', '6.5', '10*3/uL', 'normal', '03/10/2026'),
            ('Hemoglobin [LOINC: 718-7]', '13.0', 'g/dL', 'normal', '03/10/2026'),
            ('Hepatic Function Panel [LOINC: 24325-3]', 'AST 28, ALT 22, Alk Phos 65', '', 'normal', '03/10/2026'),
            ('Creatinine [LOINC: 2160-0]', '0.8', 'mg/dL', 'normal', '03/10/2026'),
            ('QuantiFERON-TB [LOINC: 71774-4]', 'Positive', '', 'H', '02/15/2023'),
            ('Vitamin D 25-OH [LOINC: 1989-3]', '34', 'ng/mL', 'normal', '03/10/2026'),
        ],
        'immunizations': [
            ('Influenza vaccine 2025-2026', '10/15/2025', 'completed'),
            ('COVID-19 Vaccine 2024-2025 (Moderna)', '09/15/2024', 'completed'),
            ('Pneumococcal PCV20 (Prevnar 20)', '03/01/2023', 'completed'),
            ('Hepatitis B series (3 doses)', '06/01/2023', 'completed'),
            ('Tdap (Boostrix)', '03/15/2020', 'completed'),
            ('Shingrix (Zoster) - contraindicated while on biologic', '', 'deferred'),
        ],
        'social_history': 'Tobacco: Never smoker. Alcohol: Rare. Employment: Paralegal, full-time. Marital Status: Married, 2 teenagers. Exercise: Gentle yoga 3x/week, swimming 1x/week. Diet: Anti-inflammatory diet. Stress: Moderate -- managing chronic disease while working.',
        'insurance': [
            ('Anthem Blue Cross', 'Commercial PPO', 'ANT-901010', 'GRP-LAW-300'),
        ],
        'notes': [
            ('03/15/2026', 'Cory Denton, FNP', 'Progress Note',
             'CC: RA follow-up, biologics monitoring.\nHPI: 50yo female with seropositive RA (RF+, CCP+) on adalimumab + leflunomide. Recovered from flare Nov 2025 -- added short burst prednisone, now tapered to 5mg maintenance. Current DAS28: 2.8 (low disease activity). Reports morning stiffness 20 min (was 90 min during flare). Hand grip improved. No injection site reactions with adalimumab.\nPE: Hands -- mild MCP synovitis bilateral, improved. No swan-neck deformities. Wrists -- full ROM, no effusion. Knees -- no effusion.\nAssessment:\n# RA (M06.9): Low disease activity on current regimen. Continue adalimumab q2 weeks + leflunomide.\n# Latent TB (R76.11): Completed 4-month rifampin course 2023. No active TB symptoms. Chest XR 2025 stable.\n# Osteopenia (M81.8): Chronic prednisone. DEXA due 2026. Continue calcium/D counseling.\n# HTN (I10): BP 126/78 on amlodipine. At goal.\n# GERD (K21.0): Controlled on omeprazole.\nPlan: Continue adalimumab, leflunomide, prednisone 5mg. Taper prednisone to 2.5mg over 4 weeks if stable. Labs q3 months (CBC, CMP, ESR/CRP). Rheumatology annual visit due. DEXA ordered. Return 3 months.'),
        ],
    },
    # ------------------------------------------------------------------
    # 11) Anthony Paul Russo -- 45M, morbid obesity, sleep apnea, pre-DM
    # ------------------------------------------------------------------
    {
        'mrn': '90011',
        'given': 'Anthony',
        'family': 'Russo',
        'gender_code': 'M',
        'gender_display': 'Male',
        'birth': '19800915',
        'marital': 'M',
        'marital_display': 'Married',
        'race_code': '2106-3',
        'race_display': 'White',
        'ethnic_code': '2186-5',
        'ethnic_display': 'Not Hispanic or Latino',
        'street': '4488 Providence Road',
        'city': 'Midlothian',
        'state': 'VA',
        'zip': '23114',
        'phone': '+1(804)-555-1011',
        'allergies': [
            ('No Known Drug Allergies', '', '', 'active'),
        ],
        'medications': [
            ('semaglutide 2.4 mg injection [RxNorm: 1991302]', 'semaglutide', 'Inject 2.4 mg subcutaneously once weekly', '2.4 mg', '01/01/2026', 'active'),
            ('CPAP therapy', 'CPAP', 'Nightly use, pressure 12 cm H2O', 'N/A', '06/01/2024', 'active'),
            ('omeprazole 40 mg capsule [RxNorm: 198053]', 'omeprazole', 'Take 1 capsule by mouth daily before breakfast', '40 mg', '03/15/2023', 'active'),
            ('montelukast 10 mg tablet [RxNorm: 997001]', 'montelukast', 'Take 1 tablet by mouth at bedtime', '10 mg', '04/01/2022', 'active'),
        ],
        'problems': [
            ('Morbid obesity BMI 45+ [ICD10: E66.01]', 'active', '01/01/2020', ''),
            ('Obstructive sleep apnea [ICD10: G47.33]', 'active', '06/01/2024', ''),
            ('Prediabetes [ICD10: R73.03]', 'active', '09/15/2025', ''),
            ('Gastroesophageal reflux disease [ICD10: K21.0]', 'active', '03/15/2023', ''),
            ('Asthma mild persistent [ICD10: J45.30]', 'active', '04/01/2022', ''),
            ('Nonalcoholic fatty liver disease [ICD10: K76.0]', 'active', '09/15/2025', ''),
            ('Knee osteoarthritis bilateral [ICD10: M17.0]', 'active', '01/01/2024', ''),
        ],
        'vitals': [
            ('03/15/2026', '71', '312', '43.5', '132', '84', '78', '96', '98.6', '16'),
            ('01/01/2026', '71', '328', '45.7', '138', '88', '82', '95', '98.4', '18'),
            ('09/15/2025', '71', '335', '46.7', '142', '90', '84', '94', '98.6', '18'),
        ],
        'labs': [
            ('Hemoglobin A1c [LOINC: 4548-4]', '6.2', '%', 'H', '03/10/2026'),
            ('Hemoglobin A1c [LOINC: 4548-4]', '6.4', '%', 'H', '09/15/2025'),
            ('Glucose fasting [LOINC: 1558-6]', '108', 'mg/dL', 'H', '03/10/2026'),
            ('Total Cholesterol [LOINC: 2093-3]', '218', 'mg/dL', 'H', '03/10/2026'),
            ('LDL Cholesterol [LOINC: 2089-1]', '142', 'mg/dL', 'H', '03/10/2026'),
            ('HDL Cholesterol [LOINC: 2085-9]', '34', 'mg/dL', 'L', '03/10/2026'),
            ('Triglycerides [LOINC: 2571-8]', '210', 'mg/dL', 'H', '03/10/2026'),
            ('ALT [LOINC: 1742-6]', '55', 'U/L', 'H', '03/10/2026'),
            ('AST [LOINC: 1920-8]', '42', 'U/L', 'H', '03/10/2026'),
            ('Hemoglobin [LOINC: 718-7]', '15.5', 'g/dL', 'normal', '03/10/2026'),
            ('TSH [LOINC: 3016-3]', '2.5', 'mIU/L', 'normal', '03/10/2026'),
        ],
        'immunizations': [
            ('Influenza vaccine 2025-2026', '10/10/2025', 'completed'),
            ('COVID-19 Vaccine 2024-2025 (Moderna)', '09/20/2024', 'completed'),
            ('Tdap (Boostrix)', '06/15/2018', 'completed'),
            ('Hepatitis B series (3 doses)', '01/01/2005', 'completed'),
        ],
        'social_history': 'Tobacco: Never smoker. Alcohol: 1-2 beers/weekend. Employment: Restaurant owner/chef, long hours on feet. Marital Status: Married, 3 children ages 5-12. Exercise: Walking 20 min 4x/week since starting semaglutide (previously sedentary). Diet: Working with nutritionist since Jan, Mediterranean diet approach.',
        'insurance': [
            ('Anthem Blue Cross', 'Commercial PPO', 'ANT-901111', 'GRP-SELF-400'),
        ],
        'notes': [
            ('03/15/2026', 'Cory Denton, FNP', 'Progress Note',
             'CC: Weight management follow-up, pre-diabetes.\nHPI: 45yo male with morbid obesity (BMI 43.5, down from 46.7). Started Wegovy (semaglutide 2.4mg) January 2026. Lost 23 lbs in 10 weeks. Tolerating well -- mild nausea first 2 weeks, resolved. Appetite significantly reduced. CPAP compliance 85% (>4h/night). Snoring improved per wife. Knees less painful with weight loss.\nPE: BMI 43.5. No acanthosis nigricans. Lungs clear. CV RRR. Abdomen obese, nontender. Knees -- crepitus bilateral, no effusion.\nAssessment:\n# Morbid obesity (E66.01): Excellent progress -- 23 lbs lost. Continue semaglutide. Goal: 10% total body weight loss.\n# Pre-diabetes (R73.03): A1c improved 6.4->6.2. Continue lifestyle modification. Recheck 3 months.\n# OSA (G47.33): CPAP compliant. Repeat sleep study when BMI <40 to reassess pressure.\n# NAFLD (K76.0): ALT/AST mildly elevated. Expected to improve with weight loss. FibroScan ordered.\n# Hyperlipidemia: LDL 142. Start atorvastatin 20mg.\n# OA knees: Improving with weight loss. Continue walking.\nPlan: Continue semaglutide. Start atorvastatin 20mg. FibroScan. Nutritionist monthly. Labs 3 months. Return 3 months.'),
        ],
    },
    # ------------------------------------------------------------------
    # 12) Dorothy Mae Washington -- 85F, CHF, CKD Stage 4, goals of care
    # ------------------------------------------------------------------
    {
        'mrn': '90012',
        'given': 'Dorothy',
        'family': 'Washington',
        'gender_code': 'F',
        'gender_display': 'Female',
        'birth': '19400301',
        'marital': 'W',
        'marital_display': 'Widowed',
        'race_code': '2054-5',
        'race_display': 'Black or African American',
        'ethnic_code': '2186-5',
        'ethnic_display': 'Not Hispanic or Latino',
        'street': '7202 Jahnke Road',
        'city': 'Richmond',
        'state': 'VA',
        'zip': '23225',
        'phone': '+1(804)-555-1012',
        'allergies': [
            ('Digoxin [RxNorm: 3407]', 'Toxicity/Bradycardia', 'severe', 'active'),
            ('Vancomycin [RxNorm: 11124]', 'Red man syndrome', 'moderate', 'active'),
        ],
        'medications': [
            ('furosemide 80 mg tablet [RxNorm: 310429]', 'furosemide', 'Take 1 tablet by mouth twice daily', '80 mg', '03/01/2025', 'active'),
            ('carvedilol 12.5 mg tablet [RxNorm: 200031]', 'carvedilol', 'Take 1 tablet by mouth twice daily', '12.5 mg', '06/15/2023', 'active'),
            ('sacubitril-valsartan 49-51 mg tablet [RxNorm: 1656340]', 'sacubitril/valsartan', 'Take 1 tablet by mouth twice daily', '49/51 mg', '06/15/2023', 'active'),
            ('spironolactone 25 mg tablet [RxNorm: 312600]', 'spironolactone', 'Take 1 tablet by mouth daily', '25 mg', '06/15/2023', 'active'),
            ('sodium bicarbonate 650 mg tablet [RxNorm: 312293]', 'sodium bicarbonate', 'Take 2 tablets by mouth three times daily', '1300 mg', '01/01/2025', 'active'),
            ('epoetin alfa 10000 units injection [RxNorm: 105442]', 'epoetin alfa', 'Inject 10000 units subcutaneously weekly', '10000 units', '01/01/2025', 'active'),
            ('metolazone 2.5 mg tablet [RxNorm: 197770]', 'metolazone', 'Take 1 tablet by mouth as needed for edema flare', '2.5 mg', '03/01/2025', 'active'),
        ],
        'problems': [
            ('Heart failure with reduced ejection fraction [ICD10: I50.22]', 'active', '06/15/2023', ''),
            ('Chronic kidney disease stage 4 [ICD10: N18.4]', 'active', '01/01/2025', ''),
            ('Anemia of chronic kidney disease [ICD10: D63.1]', 'active', '01/01/2025', ''),
            ('Type 2 diabetes mellitus without complications [ICD10: E11.9]', 'active', '04/15/2010', ''),
            ('Essential hypertension [ICD10: I10]', 'active', '01/01/2000', ''),
            ('Metabolic acidosis [ICD10: E87.2]', 'active', '01/01/2025', ''),
            ('Diastolic dysfunction [ICD10: I50.32]', 'active', '06/15/2023', ''),
            ('Macular degeneration bilateral [ICD10: H35.30]', 'active', '09/01/2022', ''),
            ('CHF exacerbation [ICD10: I50.22]', 'resolved', '02/10/2026', '02/20/2026'),
        ],
        'vitals': [
            ('03/22/2026', '61', '145', '27.4', '118', '68', '62', '95', '97.8', '18'),
            ('02/10/2026', '61', '158', '29.8', '100', '58', '54', '91', '97.4', '22'),
            ('12/10/2025', '61', '148', '28.0', '122', '72', '64', '96', '98.2', '16'),
        ],
        'labs': [
            ('Creatinine [LOINC: 2160-0]', '3.2', 'mg/dL', 'H', '03/20/2026'),
            ('eGFR [LOINC: 48642-3]', '18', 'mL/min/1.73m2', 'L', '03/20/2026'),
            ('BUN [LOINC: 3094-0]', '58', 'mg/dL', 'H', '03/20/2026'),
            ('Potassium [LOINC: 2823-3]', '5.4', 'mmol/L', 'H', '03/20/2026'),
            ('Bicarbonate [LOINC: 1963-8]', '18', 'mmol/L', 'L', '03/20/2026'),
            ('BNP [LOINC: 42637-9]', '1250', 'pg/mL', 'H', '02/10/2026'),
            ('BNP [LOINC: 42637-9]', '580', 'pg/mL', 'H', '03/20/2026'),
            ('Hemoglobin A1c [LOINC: 4548-4]', '7.0', '%', 'H', '03/20/2026'),
            ('Hemoglobin [LOINC: 718-7]', '9.8', 'g/dL', 'L', '03/20/2026'),
            ('Albumin [LOINC: 1751-7]', '3.0', 'g/dL', 'L', '03/20/2026'),
            ('Phosphorus [LOINC: 2777-1]', '5.8', 'mg/dL', 'H', '03/20/2026'),
        ],
        'immunizations': [
            ('Influenza vaccine 2025-2026', '10/01/2025', 'completed'),
            ('Pneumococcal PCV20 (Prevnar 20)', '01/15/2024', 'completed'),
            ('COVID-19 Vaccine 2024-2025 (Pfizer)', '10/20/2024', 'completed'),
            ('Tdap (Boostrix)', '06/10/2018', 'completed'),
            ('Shingrix (Zoster) complete', '09/01/2022', 'completed'),
        ],
        'social_history': 'Tobacco: Never smoker. Alcohol: None. Employment: Retired nurse. Marital Status: Widowed (husband passed 2018). Lives with son and daughter-in-law. Home health aide 5 days/week. Wheelchair bound for distances, uses walker at home. Church active (attends via livestream). DNR/DNI -- completed MOLST on file. No dialysis per patient preference.',
        'insurance': [
            ('Medicare Part B', 'Medicare', '4KL9-MN1-OP23', 'N/A'),
            ('AARP Medicare Supplement Plan G', 'Supplemental', 'SUP-112233', 'GRP-44521'),
        ],
        'notes': [
            ('03/22/2026', 'Cory Denton, FNP', 'Progress Note',
             'CC: CHF/CKD follow-up post-hospitalization.\nHPI: 85yo AA female with HFrEF (EF 25%) and CKD Stage 4 (eGFR 18). Hospitalized 02/10-02/20 for acute CHF exacerbation. Came in with 13 lbs fluid gain, O2 91%, BNP 1250. IV diuresis x 5 days. Now dry weight 145 lbs. Reports dyspnea with minimal exertion (going to bathroom). No orthopnea with 3 pillows. Appetite poor. Vision declining (macular degeneration).\nGoals of care discussion: Patient reaffirms no dialysis, no intubation. DNR/DNI. Wants comfort-focused care. Son present and agrees.\nPE: Frail. Lungs -- bibasilar crackles, mild. CV -- S3 gallop, no murmur. JVP 8 cm. Trace pedal edema (improved from 3+).\nAssessment:\n# HFrEF (I50.22): EF 25%. Guideline-directed therapy: carvedilol, Entresto, spironolactone. BNP improved 1250->580. Close to dry weight.\n# CKD 4 (N18.4): eGFR 18, declining. K+ 5.4 -- monitor closely. Bicarb 18 -- continue sodium bicarbonate. No dialysis per goals.\n# Anemia (D63.1): Hgb 9.8. Epoetin weekly. Target Hgb 10-11.\n# DM2 (E11.9): A1c 7.0 -- acceptable given age/comorbidities. Less aggressive target OK.\n# Goals of care: DNR/DNI, no dialysis, comfort-focused. MOLST current.\nPlan: Continue all meds. Daily weights. Fluid restriction 1.5L/day. Sodium <2g. Palliative care referral for symptom management. Nephrology aware of no-dialysis preference. Home health to monitor daily. Return 2 weeks or PRN.'),
        ],
    },
    # ------------------------------------------------------------------
    # 13) Kevin Scott Martinez -- 16M, asthma/sports physical, pediatric-ish
    # ------------------------------------------------------------------
    {
        'mrn': '90013',
        'given': 'Kevin',
        'family': 'Martinez',
        'gender_code': 'M',
        'gender_display': 'Male',
        'birth': '20091018',
        'marital': 'S',
        'marital_display': 'Single',
        'race_code': '2106-3',
        'race_display': 'White',
        'ethnic_code': '2135-2',
        'ethnic_display': 'Hispanic or Latino',
        'street': '5510 Bailey Bridge Road',
        'city': 'Midlothian',
        'state': 'VA',
        'zip': '23112',
        'phone': '+1(804)-555-1013',
        'allergies': [
            ('Peanuts', 'Anaphylaxis', 'severe', 'active'),
            ('Tree Nuts', 'Anaphylaxis', 'severe', 'active'),
        ],
        'medications': [
            ('fluticasone-salmeterol 250-50 mcg inhaler [RxNorm: 896188]', 'fluticasone/salmeterol', 'Inhale 1 puff twice daily', '250/50 mcg', '09/01/2023', 'active'),
            ('albuterol 90 mcg inhaler [RxNorm: 245314]', 'albuterol', 'Inhale 2 puffs every 4-6 hours as needed. Use 15 min before exercise.', '90 mcg', '06/01/2020', 'active'),
            ('montelukast 10 mg tablet [RxNorm: 997001]', 'montelukast', 'Take 1 tablet by mouth at bedtime', '10 mg', '09/01/2023', 'active'),
            ('epinephrine auto-injector 0.3 mg [RxNorm: 997274]', 'epinephrine', 'Use IM in outer thigh for anaphylaxis. Carry at all times.', '0.3 mg', '01/01/2020', 'active'),
            ('cetirizine 10 mg tablet [RxNorm: 197585]', 'cetirizine', 'Take 1 tablet by mouth daily', '10 mg', '04/01/2023', 'active'),
        ],
        'problems': [
            ('Moderate persistent asthma [ICD10: J45.40]', 'active', '06/01/2020', ''),
            ('Peanut allergy [ICD10: Z91.010]', 'active', '01/01/2012', ''),
            ('Tree nut allergy [ICD10: Z91.010]', 'active', '01/01/2012', ''),
            ('Allergic rhinitis [ICD10: J30.9]', 'active', '04/01/2023', ''),
            ('Exercise-induced bronchospasm [ICD10: J45.990]', 'active', '09/01/2023', ''),
            ('ADHD predominantly inattentive [ICD10: F90.0]', 'active', '09/01/2024', ''),
            ('Asthma exacerbation [ICD10: J45.41]', 'resolved', '10/15/2025', '10/25/2025'),
        ],
        'vitals': [
            ('03/10/2026', '67', '145', '22.7', '112', '68', '72', '99', '98.6', '14'),
            ('10/15/2025', '66', '140', '22.6', '118', '72', '88', '94', '99.2', '18'),
            ('08/15/2025', '66', '138', '22.3', '110', '66', '70', '99', '98.4', '14'),
        ],
        'labs': [
            ('CBC WBC [LOINC: 6690-2]', '8.2', '10*3/uL', 'normal', '03/05/2026'),
            ('Hemoglobin [LOINC: 718-7]', '14.8', 'g/dL', 'normal', '03/05/2026'),
            ('IgE Total [LOINC: 19113-0]', '450', 'IU/mL', 'H', '09/01/2023'),
            ('Peanut IgE [LOINC: 6206-7]', '85', 'kU/L', 'H', '09/01/2023'),
        ],
        'immunizations': [
            ('Influenza vaccine 2025-2026', '10/05/2025', 'completed'),
            ('COVID-19 Vaccine 2024-2025 (Pfizer)', '09/10/2024', 'completed'),
            ('Tdap (Boostrix)', '10/01/2024', 'completed'),
            ('Meningococcal MenACWY (Menactra)', '10/01/2024', 'completed'),
            ('HPV (Gardasil 9) Dose 1', '10/01/2024', 'completed'),
            ('HPV (Gardasil 9) Dose 2', '04/01/2025', 'completed'),
            ('MMR (2 doses)', '01/01/2010', 'completed'),
            ('Hepatitis B series (3 doses)', '01/01/2010', 'completed'),
        ],
        'social_history': 'Tobacco: Never. Alcohol: None. Drugs: None. School: 10th grade, B+ average. Sports: Varsity soccer, JV basketball. Lives with both parents and younger sister (age 12). Wears medical alert bracelet for nut allergy. EpiPen kept in school nurse office and coaches bag. Screen time: 3-4 hrs/day.',
        'insurance': [
            ('Anthem Blue Cross', 'Commercial PPO (parent plan)', 'ANT-901313', 'GRP-FAM-300'),
        ],
        'notes': [
            ('03/10/2026', 'Cory Denton, FNP', 'Progress Note',
             'CC: Sports physical, asthma check.\nHPI: 16yo Hispanic male here for spring soccer pre-participation physical. Asthma well-controlled on Advair + montelukast. Uses albuterol before practice, rarely needs rescue in between. Last exacerbation Oct 2025 during cold (required prednisone burst 5 days). Carries EpiPen at all times for peanut/tree nut anaphylaxis -- no exposures this year. ADHD -- started in fall, parent reports improved school focus but not on medication (behavioral strategies only so far).\nPE: Well-developed, well-nourished adolescent. HEENT normal. Lungs clear, no wheeze. CV RRR, no murmur, no clicks. MSK -- full ROM all joints. Tanner stage 4.\nSports clearance: CLEARED for full participation.\nAssessment:\n# Asthma (J45.40): Well-controlled, ACT score 22. Continue Advair + montelukast. Pre-exercise albuterol.\n# Peanut/tree nut allergy: EpiPen current (expires 08/2026). School action plan updated.\n# ADHD (F90.0): Behavioral strategies partially effective. Parent considering medication trial if grades slip. Will reassess in 3 months.\n# Allergic rhinitis: Cetirizine daily, well-controlled.\nPlan: Sports clearance form completed. EpiPen Rx renewed. Allergy action plan updated for school. ADHD follow-up 3 months. Flu vaccine in fall. HPV dose 2 given 04/2025 -- series complete for 2-dose schedule.'),
        ],
    },
    # ------------------------------------------------------------------
    # 14) Barbara Jean Nelson -- 66F, COPD on oxygen, lung cancer screening
    # ------------------------------------------------------------------
    {
        'mrn': '90014',
        'given': 'Barbara',
        'family': 'Nelson',
        'gender_code': 'F',
        'gender_display': 'Female',
        'birth': '19590710',
        'marital': 'D',
        'marital_display': 'Divorced',
        'race_code': '2106-3',
        'race_display': 'White',
        'ethnic_code': '2186-5',
        'ethnic_display': 'Not Hispanic or Latino',
        'street': '1833 Courthouse Road',
        'city': 'Chesterfield',
        'state': 'VA',
        'zip': '23832',
        'phone': '+1(804)-555-1014',
        'allergies': [
            ('Amoxicillin [RxNorm: 723]', 'Diarrhea', 'mild', 'active'),
            ('Latex', 'Contact dermatitis', 'moderate', 'active'),
        ],
        'medications': [
            ('tiotropium-olodaterol 2.5-2.5 mcg inhaler [RxNorm: 1720839]', 'tiotropium/olodaterol', 'Inhale 2 puffs daily', '2.5/2.5 mcg', '03/01/2024', 'active'),
            ('budesonide-formoterol 160-4.5 mcg inhaler [RxNorm: 790275]', 'budesonide/formoterol', 'Inhale 2 puffs twice daily', '160/4.5 mcg', '03/01/2024', 'active'),
            ('albuterol 90 mcg inhaler [RxNorm: 245314]', 'albuterol', 'Inhale 2 puffs every 4-6 hours as needed', '90 mcg', '01/01/2020', 'active'),
            ('home oxygen 2L nasal cannula', 'supplemental oxygen', 'Use continuously, increase to 4L with exertion', '2-4 L/min', '06/15/2025', 'active'),
            ('azithromycin 250 mg tablet [RxNorm: 261085]', 'azithromycin', 'Take 1 tablet by mouth MWF (chronic)', '250 mg', '06/15/2025', 'active'),
            ('losartan 50 mg tablet [RxNorm: 979480]', 'losartan', 'Take 1 tablet by mouth daily', '50 mg', '09/01/2022', 'active'),
            ('sertraline 100 mg tablet [RxNorm: 312938]', 'sertraline', 'Take 1 tablet by mouth daily', '100 mg', '01/15/2024', 'active'),
            ('nicotine patch 14 mg [RxNorm: 312130]', 'nicotine', 'Apply 1 patch daily', '14 mg', '03/01/2026', 'active'),
        ],
        'problems': [
            ('Chronic obstructive pulmonary disease severe [ICD10: J44.1]', 'active', '01/01/2020', ''),
            ('Chronic respiratory failure with hypoxemia [ICD10: J96.11]', 'active', '06/15/2025', ''),
            ('Tobacco use disorder [ICD10: F17.210]', 'active', '01/01/1980', ''),
            ('Essential hypertension [ICD10: I10]', 'active', '09/01/2022', ''),
            ('Major depressive disorder recurrent [ICD10: F33.1]', 'active', '01/15/2024', ''),
            ('Osteoporosis [ICD10: M81.0]', 'active', '03/15/2023', ''),
            ('Lung nodule 8mm right upper lobe [ICD10: R91.1]', 'active', '09/15/2025', ''),
            ('COPD exacerbation [ICD10: J44.1]', 'resolved', '01/20/2026', '02/05/2026'),
        ],
        'vitals': [
            ('03/18/2026', '63', '118', '20.9', '128', '78', '82', '92 on 2L', '98.2', '20'),
            ('01/20/2026', '63', '115', '20.4', '140', '86', '98', '87 on RA', '101.2', '26'),
            ('09/15/2025', '63', '120', '21.3', '130', '80', '80', '91 on 2L', '98.4', '18'),
        ],
        'labs': [
            ('CBC WBC [LOINC: 6690-2]', '9.5', '10*3/uL', 'normal', '03/15/2026'),
            ('Hemoglobin [LOINC: 718-7]', '14.2', 'g/dL', 'normal', '03/15/2026'),
            ('Comprehensive Metabolic Panel [LOINC: 24323-8]', 'normal', '', 'normal', '03/15/2026'),
            ('Sputum culture [LOINC: 630-4]', 'Normal flora', '', 'normal', '01/25/2026'),
            ('ABG pH [LOINC: 2744-1]', '7.36', '', 'normal', '09/15/2025'),
            ('ABG pCO2 [LOINC: 2019-8]', '48', 'mmHg', 'H', '09/15/2025'),
            ('ABG pO2 [LOINC: 2703-7]', '62', 'mmHg', 'L', '09/15/2025'),
            ('Vitamin D 25-OH [LOINC: 1989-3]', '24', 'ng/mL', 'L', '03/15/2026'),
            ('DEXA T-score lumbar [LOINC: 80941-3]', '-2.8', '', 'L', '03/15/2023'),
        ],
        'immunizations': [
            ('Influenza vaccine 2025-2026', '10/10/2025', 'completed'),
            ('Pneumococcal PCV20 (Prevnar 20)', '03/01/2024', 'completed'),
            ('COVID-19 Vaccine 2024-2025 (Pfizer)', '10/05/2024', 'completed'),
            ('Shingrix (Zoster) complete', '06/01/2023', 'completed'),
            ('Tdap (Boostrix)', '09/01/2022', 'completed'),
        ],
        'social_history': 'Tobacco: Active smoker -- currently 1/2 ppd, down from 1 ppd. Started age 21. Approximately 35 pack-years. On nicotine patch, trying to quit. Alcohol: Former heavy drinker, quit 2020. Employment: Disabled/SSDI since 2023. Marital Status: Divorced x 2. Lives alone, daughter checks daily. Home oxygen via concentrator + portable tanks. Exercise: Very limited by dyspnea. Can walk ~50 feet.',
        'insurance': [
            ('Medicare Part B', 'Medicare', '5QR2-ST3-UV45', 'N/A'),
            ('Virginia Medicaid (dual eligible)', 'Medicaid', 'MCD-901414', 'N/A'),
        ],
        'notes': [
            ('03/18/2026', 'Cory Denton, FNP', 'Progress Note',
             'CC: COPD follow-up, lung nodule surveillance, smoking cessation.\nHPI: 66yo female with severe COPD (GOLD Stage III, FEV1 38%). On triple inhaler therapy + chronic azithromycin + home O2. Last exacerbation Jan 2026 (prednisone burst + augmentin). Lung nodule 8mm RUL found on LDCT screening Sept 2025 -- follow-up CT due now. Currently smoking 1/2 ppd -- down from 1 ppd. Started nicotine patch 14mg. Motivated to quit. Reports increased depression during exacerbation, stable now on sertraline.\nPulm Rehab: Completed 12-week program. Functional capacity improved. 6MWT: 200m (was 150m).\nPE: Barrel chest. Lungs -- diffuse expiratory wheezes, prolonged expiration. No crackles. O2 92% on 2L. CV RRR. Cachexic.\nAssessment:\n# COPD severe (J44.1): FEV1 38%. Triple therapy + azithromycin prophylaxis. Pulm rehab complete.\n# Lung nodule (R91.1): 8mm RUL. Follow-up CT chest ordered today per Lung-RADS guidelines.\n# Smoking cessation (F17.210): Reduced to 1/2 ppd. Nicotine patch 14mg. Discussed adding bupropion -- patient amenable. Start 150mg daily x 3 days then BID.\n# Respiratory failure (J96.11): Stable on 2L. ABG showed compensated respiratory acidosis.\n# Osteoporosis (M81.0): On calcium/D. Consider bisphosphonate after dental clearance.\n# Depression (F33.1): Stable on sertraline. PHQ-9 = 8.\nPlan: CT chest ordered. Start bupropion for smoking cessation. Pulmonology 2 months. Return 6 weeks. Advance directive discussion -- patient open, will complete next visit.'),
        ],
    },
    # ------------------------------------------------------------------
    # 15) Michael Joseph Anderson -- 40M, healthy, AWV, minimal history
    # ------------------------------------------------------------------
    {
        'mrn': '90015',
        'given': 'Michael',
        'family': 'Anderson',
        'gender_code': 'M',
        'gender_display': 'Male',
        'birth': '19851225',
        'marital': 'M',
        'marital_display': 'Married',
        'race_code': '2106-3',
        'race_display': 'White',
        'ethnic_code': '2186-5',
        'ethnic_display': 'Not Hispanic or Latino',
        'street': '10250 Iron Bridge Road',
        'city': 'Chester',
        'state': 'VA',
        'zip': '23831',
        'phone': '+1(804)-555-1015',
        'allergies': [
            ('No Known Allergies', '', '', 'active'),
        ],
        'medications': [
            ('cetirizine 10 mg tablet [RxNorm: 197585]', 'cetirizine', 'Take 1 tablet by mouth daily as needed for allergies', '10 mg', '04/01/2024', 'active'),
            ('ibuprofen 400 mg tablet [RxNorm: 197806]', 'ibuprofen', 'Take 1 tablet every 6 hours as needed for headache', '400 mg', '01/01/2025', 'active'),
        ],
        'problems': [
            ('Seasonal allergic rhinitis [ICD10: J30.2]', 'active', '04/01/2024', ''),
            ('Tension headache [ICD10: G44.209]', 'active', '01/01/2025', ''),
            ('Upper respiratory infection [ICD10: J06.9]', 'resolved', '01/10/2026', '01/20/2026'),
        ],
        'vitals': [
            ('03/15/2026', '72', '190', '25.8', '122', '78', '68', '99', '98.6', '14'),
            ('01/10/2026', '72', '188', '25.5', '120', '76', '74', '99', '99.0', '16'),
        ],
        'labs': [
            ('Comprehensive Metabolic Panel [LOINC: 24323-8]', 'All normal', '', 'normal', '03/10/2026'),
            ('Lipid Panel [LOINC: 24331-1]', 'TC 198, LDL 118, HDL 52, TG 140', '', 'normal', '03/10/2026'),
            ('CBC WBC [LOINC: 6690-2]', '7.2', '10*3/uL', 'normal', '03/10/2026'),
            ('Hemoglobin [LOINC: 718-7]', '15.5', 'g/dL', 'normal', '03/10/2026'),
            ('TSH [LOINC: 3016-3]', '1.9', 'mIU/L', 'normal', '03/10/2026'),
            ('Hemoglobin A1c [LOINC: 4548-4]', '5.2', '%', 'normal', '03/10/2026'),
        ],
        'immunizations': [
            ('Influenza vaccine 2025-2026', '10/15/2025', 'completed'),
            ('COVID-19 Vaccine 2024-2025 (Pfizer)', '09/20/2024', 'completed'),
            ('Tdap (Boostrix)', '01/15/2022', 'completed'),
            ('Hepatitis B series (3 doses)', '01/01/2005', 'completed'),
            ('MMR (2 doses)', '01/01/1986', 'completed'),
        ],
        'social_history': 'Tobacco: Never smoker. Alcohol: Social, 2-3 drinks/weekend. Employment: Firefighter/EMT. Marital Status: Married, 2 children ages 3 and 6. Exercise: CrossFit 4x/week, runs 2x/week. Diet: High protein. Annual fire department physical required.',
        'insurance': [
            ('Anthem Blue Cross', 'Commercial PPO', 'ANT-901515', 'GRP-COUNTY-200'),
        ],
        'notes': [
            ('03/15/2026', 'Cory Denton, FNP', 'Annual Wellness Visit',
             'ANNUAL WELLNESS VISIT -- G0438 (initial)\n40yo healthy male, firefighter/EMT. First AWV.\nPreventive:\n- Colorectal screening: Age 40 -- discuss options at 45. Family history negative.\n- Depression: PHQ-9 = 2 (minimal).\n- ASCVD risk: 10-year risk 3.2% (low). No statin indicated.\n- Diabetes screening: A1c 5.2% normal.\n- Testicular self-exam: Counseled.\n- Skin cancer: Counsel on sun protection (outdoor occupation exposure).\n- Immunizations: All up to date.\n- Hearing/Vision: Normal per fire department physical.\nPE: Fit, muscular male. BMI 25.8. BP 122/78. No abnormalities on comprehensive exam.\nAssessment: Healthy male, no chronic conditions. Well-controlled allergic rhinitis.\nPlan: Continue healthy lifestyle. Labs reviewed -- all normal. Colorectal screening in 5 years. Return annually or PRN. HPV vaccine -- age >26, not indicated.'),
        ],
    },
]


def build_xml(p):
    """Build a complete CDA XML string for a patient dict."""
    mrn = p['mrn']
    # Helper to escape XML characters
    def esc(text):
        if not text:
            return ''
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))

    # Build allergy rows
    allergy_rows = ''
    for a in p['allergies']:
        allergy_rows += f'                <tr><td>{esc(a[0])}</td><td>{esc(a[1])}</td><td>{esc(a[2])}</td><td>{esc(a[3])}</td></tr>\n'

    # Build medication rows
    med_rows = ''
    for m in p['medications']:
        med_rows += f'                <tr><td>{esc(m[0])}</td><td>{esc(m[1])}</td><td>{esc(m[2])}</td><td>{esc(m[3])}</td><td>{esc(m[4])}</td><td>{esc(m[5])}</td></tr>\n'

    # Build problem rows
    prob_rows = ''
    for pr in p['problems']:
        prob_rows += f'                <tr><td>{esc(pr[0])}</td><td>{esc(pr[1])}</td><td>{esc(pr[2])}</td><td>{esc(pr[3])}</td></tr>\n'

    # Build vital rows
    vital_rows = ''
    for v in p['vitals']:
        vital_rows += f'                <tr><td>{esc(v[0])}</td><td>{esc(v[1])}</td><td>{esc(v[2])}</td><td>{esc(v[3])}</td><td>{esc(v[4])}</td><td>{esc(v[5])}</td><td>{esc(v[6])}</td><td>{esc(v[7])}</td><td>{esc(v[8])}</td><td>{esc(v[9])}</td></tr>\n'

    # Build lab rows
    lab_rows = ''
    for l in p['labs']:
        lab_rows += f'                <tr><td>{esc(l[0])}</td><td>{esc(l[1])}</td><td>{esc(l[2])}</td><td>{esc(l[3])}</td><td>{esc(l[4])}</td></tr>\n'

    # Build immunization rows
    imm_rows = ''
    for i in p['immunizations']:
        imm_rows += f'                <tr><td>{esc(i[0])}</td><td>{esc(i[1])}</td><td>{esc(i[2])}</td></tr>\n'

    # Build insurance rows
    ins_rows = ''
    for ins in p['insurance']:
        ins_rows += f'                <tr><td>{esc(ins[0])}</td><td>{esc(ins[1])}</td><td>{esc(ins[2])}</td><td>{esc(ins[3])}</td></tr>\n'

    # Build progress note rows
    note_rows = ''
    for n in p['notes']:
        note_rows += f'                <tr><td>{esc(n[0])}</td><td>{esc(n[1])}</td><td>{esc(n[2])}</td><td>{esc(n[3])}</td><td>Family Practice Associates of Chesterfield</td></tr>\n'

    xml = f'''<?xml version="1.0"?>
<?xml-stylesheet type='text/xsl' href='CDA.xsl'?>
<ClinicalDocument xmlns:sdtc="urn:hl7-org:sdtc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="urn:hl7-org:v3">
  <realmCode code="US" />
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040" />
  <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01" />
  <templateId root="2.16.840.1.113883.10.20.22.1.1" />
  <templateId root="2.16.840.1.113883.10.20.22.1.2" extension="2015-08-01" />
  <templateId root="2.16.840.1.113883.10.20.22.1.2" />
  <id root="2.16.840.1.113883.3.1167" extension="AmazingCharts" />
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC" displayName="Summarization of episode note" />
  <title>Family Practice Associates of Chesterfield Clinical Summary</title>
  <effectiveTime value="202603251000-0400" />
  <confidentialityCode code="N" displayName="Normal" codeSystem="2.16.840.1.113883.5.25" codeSystemName="Confidentiality" />
  <languageCode code="en-US" />
  <setId root="00000000-0000-0000-0000-0000000{mrn}" extension="AmazingCharts" />
  <versionNumber value="1" />
  <recordTarget>
    <patientRole>
      <id root="2.16.840.1.113883.3.1167.2799" extension="{mrn}" />
      <addr use="HP">
        <streetAddressLine>{esc(p['street'])}</streetAddressLine>
        <city>{esc(p['city'])}</city>
        <state>{esc(p['state'])}</state>
        <postalCode>{esc(p['zip'])}</postalCode>
        <country nullFlavor="NI" />
        <useablePeriod xsi:type="IVL_TS"><low value="20260325" /></useablePeriod>
      </addr>
      <telecom use="HP" value="tel:{esc(p['phone'])}" />
      <patient>
        <name use="L">
          <given>{esc(p['given'])}</given>
          <family>{esc(p['family'])}</family>
        </name>
        <administrativeGenderCode code="{p['gender_code']}" codeSystem="2.16.840.1.113883.5.1" displayName="{p['gender_display']}" codeSystemName="AdministrativeGender" />
        <birthTime value="{p['birth']}" />
        <maritalStatusCode code="{p['marital']}" displayName="{p['marital_display']}" codeSystem="2.16.840.1.113883.5.2" />
        <religiousAffiliationCode nullFlavor="NI" />
        <raceCode code="{p['race_code']}" displayName="{p['race_display']}" codeSystem="2.16.840.1.113883.6.238" codeSystemName="Race &amp; Ethnicity - CDC" />
        <ethnicGroupCode code="{p['ethnic_code']}" displayName="{p['ethnic_display']}" codeSystem="2.16.840.1.113883.6.238" codeSystemName="Race &amp; Ethnicity - CDC" />
        <languageCommunication>
          <languageCode code="en" />
        </languageCommunication>
      </patient>
      <providerOrganization>
        <id root="2.16.840.1.113883.3.1167" extension="AmazingCharts" />
        <name>Family Practice Associates of Chesterfield</name>
        <telecom use="WP" value="tel:+1(804)-423-9913" />
        <addr use="WP"><streetAddressLine>13911 St Francis Blvd, Suite 101</streetAddressLine>
        <city>Midlothian</city>
        <state>VA</state>
        <postalCode>23114</postalCode>
        <country>US</country></addr>
      </providerOrganization>
    </patientRole>
  </recordTarget>
  <author>
    <time value="202603251000-0400" />
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="1891645123" assigningAuthorityName="National Provider Identifier" />
      <addr use="WP"><streetAddressLine>13911 St Francis Blvd, Suite 101</streetAddressLine>
        <city>Midlothian</city>
        <state>VA</state>
        <postalCode>23114</postalCode>
        <country>US</country></addr>
      <telecom use="WP" value="tel:+1(804)-423-9913" />
      <assignedPerson><name><given>Cory</given><family>Denton</family><suffix>FNP</suffix></name></assignedPerson>
      <representedOrganization>
        <name>Family Practice Associates of Chesterfield</name>
        <telecom use="WP" value="tel:+1(804)-423-9913" />
        <addr use="WP"><streetAddressLine>13911 St Francis Blvd, Suite 101</streetAddressLine>
        <city>Midlothian</city>
        <state>VA</state>
        <postalCode>23114</postalCode>
        <country>US</country></addr>
      </representedOrganization>
    </assignedAuthor>
  </author>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="2.16.840.1.113883.4.6" extension="1306884820" assigningAuthorityName="National Provider Identifier" />
        <name>Family Practice Associates of Chesterfield</name>
        <telecom use="WP" value="tel:+1(804)-423-9913" />
        <addr use="WP"><streetAddressLine>13911 St Francis Blvd, Suite 101</streetAddressLine>
        <city>Midlothian</city>
        <state>VA</state>
        <postalCode>23114</postalCode>
        <country>US</country></addr>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
  <documentationOf typeCode="DOC">
    <serviceEvent classCode="PCPR">
      <effectiveTime><low value="{p['birth']}" /><high value="20260325" /></effectiveTime>
      <performer typeCode="PRF">
        <time><low value="20250101" /></time>
        <assignedEntity>
          <id extension="1891645123" root="2.16.840.1.113883.4.6" assigningAuthorityName="National Provider Identifier" />
          <addr use="WP"><streetAddressLine>13911 St Francis Blvd, Suite 101</streetAddressLine>
        <city>Midlothian</city>
        <state>VA</state>
        <postalCode>23114</postalCode>
        <country>US</country></addr>
          <telecom use="WP" value="tel:+1(804)-423-9913" />
          <assignedPerson><name><given>Cory</given><family>Denton</family><suffix>FNP</suffix></name></assignedPerson>
          <representedOrganization>
            <id root="2.16.840.1.113883.3.1167.2799" />
            <name>Family Practice Associates of Chesterfield</name>
            <addr use="WP"><streetAddressLine>13911 St Francis Blvd, Suite 101</streetAddressLine>
        <city>Midlothian</city>
        <state>VA</state>
        <postalCode>23114</postalCode>
        <country>US</country></addr>
          </representedOrganization>
        </assignedEntity>
      </performer>
    </serviceEvent>
  </documentationOf>
  <componentOf>
    <encompassingEncounter>
      <id root="00000000-0000-0000-0000-0000000{mrn}" extension="1306884820" />
      <code code="AMB" codeSystem="2.16.840.1.113883.5.4" codeSystemName="ActCode" displayName="Ambulatory" />
      <effectiveTime><low value="202603251000-0400" /></effectiveTime>
      <location>
        <healthCareFacility>
          <id root="2.16.840.1.113883.19" extension="1306884820" />
          <location>
            <name>Family Practice Associates of Chesterfield</name>
            <addr use="WP"><streetAddressLine>13911 St Francis Blvd, Suite 101</streetAddressLine>
        <city>Midlothian</city>
        <state>VA</state>
        <postalCode>23114</postalCode>
        <country>US</country></addr>
          </location>
        </healthCareFacility>
      </location>
    </encompassingEncounter>
  </componentOf>
  <component>
    <structuredBody>
      <component>
        <section>
          <code code="48765-2" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC" displayName="Allergies and Adverse Reactions" />
          <title>ALLERGIES AND ADVERSE REACTIONS</title>
          <text>
            <table xmlns:xsd="http://www.w3.org/2001/XMLSchema">
              <thead><tr><th>Substance</th><th>Reaction</th><th>Severity</th><th>Status</th></tr></thead>
              <tbody>
{allergy_rows}              </tbody>
            </table>
          </text>
        </section>
      </component>
      <component>
        <section>
          <code code="10160-0" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC" displayName="Medications" />
          <title>MEDICATIONS</title>
          <text>
            <table xmlns:xsd="http://www.w3.org/2001/XMLSchema">
              <thead><tr><th>Medication</th><th>Generic Name</th><th>Instructions</th><th>Dosage</th><th>Start Date</th><th>Status</th></tr></thead>
              <tbody>
{med_rows}              </tbody>
            </table>
          </text>
        </section>
      </component>
      <component>
        <section>
          <code code="11450-4" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC" displayName="Problems" />
          <title>PROBLEMS</title>
          <text>
            <table xmlns:xsd="http://www.w3.org/2001/XMLSchema">
              <thead><tr><th>Problem</th><th>Problem Status</th><th>Date Started</th><th>Date Resolved</th></tr></thead>
              <tbody>
{prob_rows}              </tbody>
            </table>
          </text>
        </section>
      </component>
      <component>
        <section>
          <code code="8716-3" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC" displayName="Vital Signs" />
          <title>VITAL SIGNS</title>
          <text>
            <table xmlns:xsd="http://www.w3.org/2001/XMLSchema">
              <thead><tr><th>Encounter</th><th>Height (in)</th><th>Weight (lb)</th><th>BMI (kg/m2)</th><th>BP Sys (mmHg)</th><th>BP Dias (mmHg)</th><th>Heart Rate (/min)</th><th>O2 % BldC Oximetry</th><th>Body Temperature</th><th>Respiratory Rate (/min)</th></tr></thead>
              <tbody>
{vital_rows}              </tbody>
            </table>
          </text>
        </section>
      </component>
      <component>
        <section>
          <code code="30954-2" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC" displayName="Lab Results" />
          <title>LAB RESULTS</title>
          <text>
            <table xmlns:xsd="http://www.w3.org/2001/XMLSchema">
              <thead><tr><th>Test Name</th><th>Result</th><th>Units</th><th>Flag</th><th>Date</th></tr></thead>
              <tbody>
{lab_rows}              </tbody>
            </table>
          </text>
        </section>
      </component>
      <component>
        <section>
          <code code="11369-6" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC" displayName="Immunizations" />
          <title>IMMUNIZATIONS</title>
          <text>
            <table xmlns:xsd="http://www.w3.org/2001/XMLSchema">
              <thead><tr><th>Vaccine</th><th>Date</th><th>Status</th></tr></thead>
              <tbody>
{imm_rows}              </tbody>
            </table>
          </text>
        </section>
      </component>
      <component>
        <section>
          <code code="29762-2" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC" displayName="Social History" />
          <title>SOCIAL HISTORY</title>
          <text>{esc(p['social_history'])}</text>
        </section>
      </component>
      <component>
        <section>
          <code code="48768-6" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC" displayName="Insurance" />
          <title>INSURANCE</title>
          <text>
            <table xmlns:xsd="http://www.w3.org/2001/XMLSchema">
              <thead><tr><th>Payer</th><th>Policy Type</th><th>Member ID</th><th>Group</th></tr></thead>
              <tbody>
{ins_rows}              </tbody>
            </table>
          </text>
        </section>
      </component>
      <component>
        <section>
          <code code="11506-3" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC" displayName="Progress Notes" />
          <title>PROGRESS NOTES</title>
          <text>
            <table xmlns:xsd="http://www.w3.org/2001/XMLSchema">
              <thead><tr><th>Date</th><th>Provider</th><th>Note Type</th><th>Note Text</th><th>Location</th></tr></thead>
              <tbody>
{note_rows}              </tbody>
            </table>
          </text>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>'''
    return xml


def main():
    count = 0
    for p in PATIENTS:
        xml = build_xml(p)
        filename = f"ClinicalSummary_PatientId_{p['mrn']}_20260325_100000.xml"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(xml)
        count += 1
        print(f'  Created: {filename} ({p["given"]} {p["family"]}, MRN {p["mrn"]})')

    print(f'\nDone. Generated {count} patient XML files in {OUTPUT_DIR}')


if __name__ == '__main__':
    main()
