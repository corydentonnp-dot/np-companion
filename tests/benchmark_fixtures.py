"""
Benchmark Fixtures — 18 Synthetic Patient Profiles

Provides PATIENTS dict (patient_id → patient_data) and EXPECTED dict
(patient_id → expected results per engine) for benchmark testing of
the billing, care gap, and monitoring engines.

All data is synthetic — no PHI. Patient IDs use BM_ prefix.
"""

from datetime import date, timedelta


# =====================================================================
# Helper to build ISO date strings relative to today
# =====================================================================
def _days_ago(n):
    return (date.today() - timedelta(days=n)).isoformat()


# =====================================================================
# 18 Synthetic Patient Profiles
# =====================================================================

PATIENTS = {

    # ------------------------------------------------------------------
    # 1. Medicare 68F — 4 chronic conditions (CCM, AWV, screening baseline)
    # ------------------------------------------------------------------
    'BM_MEDICARE_68F': {
        'mrn': 'BM001', 'patient_age': 68, 'age': 68,
        'sex': 'female', 'patient_sex': 'F',
        'insurer_type': 'medicare', 'insurer': 'medicare',
        'visit_type': 'office_visit', 'user_id': 1,
        'visit_date': date.today(),
        'diagnoses': [
            {'icd10_code': 'I10', 'diagnosis_name': 'Essential hypertension', 'status': 'active'},
            {'icd10_code': 'E11.65', 'diagnosis_name': 'Type 2 diabetes with hyperglycemia', 'status': 'active'},
            {'icd10_code': 'N18.3', 'diagnosis_name': 'CKD stage 3', 'status': 'active'},
            {'icd10_code': 'E78.5', 'diagnosis_name': 'Hyperlipidemia', 'status': 'active'},
        ],
        'medications': [
            {'name': 'Lisinopril 20mg', 'drug_name': 'Lisinopril 20mg', 'frequency': 'daily', 'status': 'active'},
            {'name': 'Metformin 1000mg', 'drug_name': 'Metformin 1000mg', 'frequency': 'twice daily', 'status': 'active'},
            {'name': 'Atorvastatin 40mg', 'drug_name': 'Atorvastatin 40mg', 'frequency': 'daily', 'status': 'active'},
        ],
        'vitals': {'systolic_bp': 138, 'diastolic_bp': 84, 'bmi': 31.2, 'weight_lbs': 185, 'height_in': 65},
        'lab_results': [],
        'immunizations': [],
        'social_history': {},
        'awv_history': {'last_awv_date': None},
        'last_awv_date': None,
        'active_chronic_conditions': 4, 'chronic_conditions_count': 4,
        'ccm_minutes_this_month': 25,
        'prior_encounters_count': 8,
        'is_pregnant': False,
        'risk_factors': ['overweight'],
        'known_diagnoses': ['I10', 'E11.65', 'N18.3', 'E78.5'],
        'dob': '10/01/1957',
    },

    # ------------------------------------------------------------------
    # 2. Medicare 72M — post-discharge with MDD (TCM, BHI, CCM stacking)
    # ------------------------------------------------------------------
    'BM_MEDICARE_72M': {
        'mrn': 'BM002', 'patient_age': 72, 'age': 72,
        'sex': 'male', 'patient_sex': 'M',
        'insurer_type': 'medicare', 'insurer': 'medicare',
        'visit_type': 'office_visit', 'user_id': 1,
        'visit_date': date.today(),
        'diagnoses': [
            {'icd10_code': 'I25.10', 'diagnosis_name': 'CAD', 'status': 'active'},
            {'icd10_code': 'I50.9', 'diagnosis_name': 'Heart failure', 'status': 'active'},
            {'icd10_code': 'J44.1', 'diagnosis_name': 'COPD with exacerbation', 'status': 'active'},
            {'icd10_code': 'F33.1', 'diagnosis_name': 'Major depressive disorder, recurrent, moderate', 'status': 'active'},
        ],
        'medications': [
            {'name': 'Metoprolol 50mg', 'drug_name': 'Metoprolol 50mg', 'frequency': 'twice daily', 'status': 'active'},
            {'name': 'Furosemide 40mg', 'drug_name': 'Furosemide 40mg', 'frequency': 'daily', 'status': 'active'},
            {'name': 'Sertraline 100mg', 'drug_name': 'Sertraline 100mg', 'frequency': 'daily', 'status': 'active'},
            {'name': 'Albuterol inhaler', 'drug_name': 'Albuterol inhaler', 'frequency': 'PRN', 'status': 'active'},
        ],
        'vitals': {'systolic_bp': 145, 'diastolic_bp': 90, 'bmi': 28.5},
        'lab_results': [],
        'immunizations': [],
        'social_history': {'smoking_status': 'former'},
        'awv_history': {'last_awv_date': _days_ago(400)},
        'last_awv_date': _days_ago(400),
        'active_chronic_conditions': 4, 'chronic_conditions_count': 4,
        'ccm_minutes_this_month': 30,
        'prior_encounters_count': 12,
        'is_pregnant': False,
        'discharge_date': _days_ago(5),
        'risk_factors': [],
        'known_diagnoses': ['I25.10', 'I50.9', 'J44.1', 'F33.1'],
        'dob': '03/15/1953',
    },

    # ------------------------------------------------------------------
    # 3. Commercial 44F — depression/anxiety (BHI, screening, no AWV)
    # ------------------------------------------------------------------
    'BM_COMMERCIAL_44F': {
        'mrn': 'BM003', 'patient_age': 44, 'age': 44,
        'sex': 'female', 'patient_sex': 'F',
        'insurer_type': 'commercial', 'insurer': 'commercial',
        'visit_type': 'office_visit', 'user_id': 1,
        'visit_date': date.today(),
        'diagnoses': [
            {'icd10_code': 'F33.0', 'diagnosis_name': 'Major depressive disorder, recurrent, mild', 'status': 'active'},
            {'icd10_code': 'F41.1', 'diagnosis_name': 'Generalized anxiety disorder', 'status': 'active'},
        ],
        'medications': [
            {'name': 'Escitalopram 10mg', 'drug_name': 'Escitalopram 10mg', 'frequency': 'daily', 'status': 'active'},
        ],
        'vitals': {'systolic_bp': 118, 'diastolic_bp': 72, 'bmi': 24.1},
        'lab_results': [],
        'immunizations': [],
        'social_history': {},
        'awv_history': {'last_awv_date': None},
        'last_awv_date': None,
        'active_chronic_conditions': 2, 'chronic_conditions_count': 2,
        'ccm_minutes_this_month': 0,
        'prior_encounters_count': 4,
        'is_pregnant': False,
        'risk_factors': [],
        'known_diagnoses': ['F33.0', 'F41.1'],
        'dob': '06/20/1981',
    },

    # ------------------------------------------------------------------
    # 4. Medicaid 28M — asthma + substance use (alcohol/STI screen)
    # ------------------------------------------------------------------
    'BM_MEDICAID_28M': {
        'mrn': 'BM004', 'patient_age': 28, 'age': 28,
        'sex': 'male', 'patient_sex': 'M',
        'insurer_type': 'medicaid', 'insurer': 'medicaid',
        'visit_type': 'office_visit', 'user_id': 1,
        'visit_date': date.today(),
        'diagnoses': [
            {'icd10_code': 'J45.20', 'diagnosis_name': 'Mild intermittent asthma', 'status': 'active'},
            {'icd10_code': 'F10.10', 'diagnosis_name': 'Alcohol use disorder, mild', 'status': 'active'},
        ],
        'medications': [
            {'name': 'Albuterol inhaler', 'drug_name': 'Albuterol inhaler', 'frequency': 'PRN', 'status': 'active'},
        ],
        'vitals': {'systolic_bp': 122, 'diastolic_bp': 78, 'bmi': 25.0},
        'lab_results': [],
        'immunizations': [],
        'social_history': {'alcohol_use': 'heavy', 'sexual_activity': 'active'},
        'awv_history': {'last_awv_date': None},
        'last_awv_date': None,
        'active_chronic_conditions': 2, 'chronic_conditions_count': 2,
        'ccm_minutes_this_month': 0,
        'prior_encounters_count': 2,
        'is_pregnant': False,
        'risk_factors': [],
        'known_diagnoses': ['J45.20', 'F10.10'],
        'dob': '11/05/1997',
    },

    # ------------------------------------------------------------------
    # 5. Medicare Advantage 75F — osteoporosis, CKD4 (DEXA, fall risk)
    # ------------------------------------------------------------------
    'BM_MEDICARE_ADV_75F': {
        'mrn': 'BM005', 'patient_age': 75, 'age': 75,
        'sex': 'female', 'patient_sex': 'F',
        'insurer_type': 'medicare', 'insurer': 'medicare_advantage',
        'visit_type': 'office_visit', 'user_id': 1,
        'visit_date': date.today(),
        'diagnoses': [
            {'icd10_code': 'M81.0', 'diagnosis_name': 'Osteoporosis without fracture', 'status': 'active'},
            {'icd10_code': 'I10', 'diagnosis_name': 'Essential hypertension', 'status': 'active'},
            {'icd10_code': 'E11.65', 'diagnosis_name': 'Type 2 diabetes', 'status': 'active'},
            {'icd10_code': 'N18.4', 'diagnosis_name': 'CKD stage 4', 'status': 'active'},
        ],
        'medications': [
            {'name': 'Alendronate 70mg', 'drug_name': 'Alendronate 70mg', 'frequency': 'weekly', 'status': 'active'},
            {'name': 'Amlodipine 10mg', 'drug_name': 'Amlodipine 10mg', 'frequency': 'daily', 'status': 'active'},
            {'name': 'Insulin glargine', 'drug_name': 'Insulin glargine', 'frequency': 'daily', 'status': 'active'},
        ],
        'vitals': {'systolic_bp': 150, 'diastolic_bp': 88, 'bmi': 26.0},
        'lab_results': [],
        'immunizations': [],
        'social_history': {},
        'awv_history': {'last_awv_date': _days_ago(400)},
        'last_awv_date': _days_ago(400),
        'active_chronic_conditions': 4, 'chronic_conditions_count': 4,
        'ccm_minutes_this_month': 22,
        'prior_encounters_count': 10,
        'is_pregnant': False,
        'risk_factors': [],
        'known_diagnoses': ['M81.0', 'I10', 'E11.65', 'N18.4'],
        'dob': '02/14/1950',
    },

    # ------------------------------------------------------------------
    # 6. Pediatric 8M — well-child visit
    # ------------------------------------------------------------------
    'BM_PEDIATRIC_8M': {
        'mrn': 'BM006', 'patient_age': 8, 'age': 8,
        'sex': 'male', 'patient_sex': 'M',
        'insurer_type': 'commercial', 'insurer': 'commercial',
        'visit_type': 'well_child', 'user_id': 1,
        'visit_date': date.today(),
        'diagnoses': [],
        'medications': [],
        'vitals': {'systolic_bp': 98, 'diastolic_bp': 62, 'bmi': 16.5, 'weight_lbs': 55, 'height_in': 50},
        'lab_results': [],
        'immunizations': ['DTaP', 'IPV', 'MMR', 'Varicella'],
        'social_history': {},
        'awv_history': {'last_awv_date': None},
        'last_awv_date': None,
        'active_chronic_conditions': 0, 'chronic_conditions_count': 0,
        'ccm_minutes_this_month': 0,
        'prior_encounters_count': 1,
        'is_pregnant': False,
        'risk_factors': [],
        'known_diagnoses': [],
        'dob': '07/10/2017',
    },

    # ------------------------------------------------------------------
    # 7. Pediatric 2F — developmental delay
    # ------------------------------------------------------------------
    'BM_PEDIATRIC_2F': {
        'mrn': 'BM007', 'patient_age': 2, 'age': 2,
        'sex': 'female', 'patient_sex': 'F',
        'insurer_type': 'medicaid', 'insurer': 'medicaid',
        'visit_type': 'well_child', 'user_id': 1,
        'visit_date': date.today(),
        'diagnoses': [
            {'icd10_code': 'R62.0', 'diagnosis_name': 'Delayed milestone', 'status': 'active'},
        ],
        'medications': [],
        'vitals': {'weight_lbs': 24, 'height_in': 33},
        'lab_results': [],
        'immunizations': ['HepB', 'DTaP', 'IPV'],
        'social_history': {},
        'awv_history': {'last_awv_date': None},
        'last_awv_date': None,
        'active_chronic_conditions': 0, 'chronic_conditions_count': 0,
        'ccm_minutes_this_month': 0,
        'prior_encounters_count': 3,
        'is_pregnant': False,
        'risk_factors': [],
        'known_diagnoses': ['R62.0'],
        'dob': '01/15/2024',
    },

    # ------------------------------------------------------------------
    # 8. Pregnant 32F — normal pregnancy (exclusions, prenatal gaps)
    # ------------------------------------------------------------------
    'BM_PREGNANT_32F': {
        'mrn': 'BM008', 'patient_age': 32, 'age': 32,
        'sex': 'female', 'patient_sex': 'F',
        'insurer_type': 'commercial', 'insurer': 'commercial',
        'visit_type': 'office_visit', 'user_id': 1,
        'visit_date': date.today(),
        'diagnoses': [
            {'icd10_code': 'Z34.00', 'diagnosis_name': 'Normal pregnancy, unspecified trimester', 'status': 'active'},
        ],
        'medications': [
            {'name': 'Prenatal vitamins', 'drug_name': 'Prenatal vitamins', 'frequency': 'daily', 'status': 'active'},
        ],
        'vitals': {'systolic_bp': 112, 'diastolic_bp': 70, 'bmi': 27.0},
        'lab_results': [],
        'immunizations': [],
        'social_history': {},
        'awv_history': {'last_awv_date': None},
        'last_awv_date': None,
        'active_chronic_conditions': 0, 'chronic_conditions_count': 0,
        'ccm_minutes_this_month': 0,
        'prior_encounters_count': 5,
        'is_pregnant': True,
        'risk_factors': [],
        'known_diagnoses': ['Z34.00'],
        'dob': '09/12/1993',
    },

    # ------------------------------------------------------------------
    # 9. Dual-eligible 80M — cognitive decline (payer routing, cognitive)
    # ------------------------------------------------------------------
    'BM_DUAL_ELIGIBLE_80M': {
        'mrn': 'BM009', 'patient_age': 80, 'age': 80,
        'sex': 'male', 'patient_sex': 'M',
        'insurer_type': 'medicare', 'insurer': 'medicare',
        'visit_type': 'office_visit', 'user_id': 1,
        'visit_date': date.today(),
        'diagnoses': [
            {'icd10_code': 'I50.9', 'diagnosis_name': 'Heart failure', 'status': 'active'},
            {'icd10_code': 'E11.65', 'diagnosis_name': 'Type 2 diabetes', 'status': 'active'},
            {'icd10_code': 'J44.1', 'diagnosis_name': 'COPD', 'status': 'active'},
            {'icd10_code': 'G31.84', 'diagnosis_name': 'Mild cognitive impairment', 'status': 'active'},
        ],
        'medications': [
            {'name': 'Lisinopril 10mg', 'drug_name': 'Lisinopril 10mg', 'frequency': 'daily', 'status': 'active'},
            {'name': 'Metformin 500mg', 'drug_name': 'Metformin 500mg', 'frequency': 'twice daily', 'status': 'active'},
            {'name': 'Donepezil 10mg', 'drug_name': 'Donepezil 10mg', 'frequency': 'daily', 'status': 'active'},
        ],
        'vitals': {'systolic_bp': 155, 'diastolic_bp': 85, 'bmi': 27.0},
        'lab_results': [],
        'immunizations': [],
        'social_history': {},
        'awv_history': {'last_awv_date': _days_ago(380)},
        'last_awv_date': _days_ago(380),
        'active_chronic_conditions': 4, 'chronic_conditions_count': 4,
        'ccm_minutes_this_month': 20,
        'prior_encounters_count': 15,
        'is_pregnant': False,
        'risk_factors': [],
        'known_diagnoses': ['I50.9', 'E11.65', 'J44.1', 'G31.84'],
        'dob': '05/22/1945',
    },

    # ------------------------------------------------------------------
    # 10. Tobacco 55M — heavy smoker (cessation, lung LDCT, counseling)
    # ------------------------------------------------------------------
    'BM_TOBACCO_55M': {
        'mrn': 'BM010', 'patient_age': 55, 'age': 55,
        'sex': 'male', 'patient_sex': 'M',
        'insurer_type': 'medicare', 'insurer': 'medicare',
        'visit_type': 'office_visit', 'user_id': 1,
        'visit_date': date.today(),
        'diagnoses': [
            {'icd10_code': 'J44.1', 'diagnosis_name': 'COPD with exacerbation', 'status': 'active'},
            {'icd10_code': 'I10', 'diagnosis_name': 'Essential hypertension', 'status': 'active'},
            {'icd10_code': 'F17.210', 'diagnosis_name': 'Nicotine dependence, cigarettes', 'status': 'active'},
        ],
        'medications': [
            {'name': 'Tiotropium', 'drug_name': 'Tiotropium', 'frequency': 'daily', 'status': 'active'},
            {'name': 'Lisinopril 20mg', 'drug_name': 'Lisinopril 20mg', 'frequency': 'daily', 'status': 'active'},
        ],
        'vitals': {'systolic_bp': 142, 'diastolic_bp': 88, 'bmi': 29.0},
        'lab_results': [],
        'immunizations': [],
        'social_history': {'smoking_status': 'current', 'pack_years': 30},
        'awv_history': {'last_awv_date': None},
        'last_awv_date': None,
        'active_chronic_conditions': 3, 'chronic_conditions_count': 3,
        'ccm_minutes_this_month': 0,
        'prior_encounters_count': 6,
        'is_pregnant': False,
        'risk_factors': ['heavy_smoker', 'current_smoker'],
        'known_diagnoses': ['J44.1', 'I10', 'F17.210'],
        'dob': '08/03/1970',
    },

    # ------------------------------------------------------------------
    # 11. Obese 42F — BMI 38, prediabetes (obesity counseling, DM screen)
    # ------------------------------------------------------------------
    'BM_OBESE_42F': {
        'mrn': 'BM011', 'patient_age': 42, 'age': 42,
        'sex': 'female', 'patient_sex': 'F',
        'insurer_type': 'commercial', 'insurer': 'commercial',
        'visit_type': 'office_visit', 'user_id': 1,
        'visit_date': date.today(),
        'diagnoses': [
            {'icd10_code': 'E66.01', 'diagnosis_name': 'Morbid obesity', 'status': 'active'},
            {'icd10_code': 'R73.03', 'diagnosis_name': 'Prediabetes', 'status': 'active'},
            {'icd10_code': 'I10', 'diagnosis_name': 'Essential hypertension', 'status': 'active'},
        ],
        'medications': [
            {'name': 'Metformin 500mg', 'drug_name': 'Metformin 500mg', 'frequency': 'daily', 'status': 'active'},
            {'name': 'Lisinopril 10mg', 'drug_name': 'Lisinopril 10mg', 'frequency': 'daily', 'status': 'active'},
        ],
        'vitals': {'systolic_bp': 135, 'diastolic_bp': 82, 'bmi': 38.0, 'weight_lbs': 230, 'height_in': 66},
        'lab_results': [],
        'immunizations': [],
        'social_history': {},
        'awv_history': {'last_awv_date': None},
        'last_awv_date': None,
        'active_chronic_conditions': 3, 'chronic_conditions_count': 3,
        'ccm_minutes_this_month': 0,
        'prior_encounters_count': 3,
        'is_pregnant': False,
        'risk_factors': ['overweight', 'obese'],
        'known_diagnoses': ['E66.01', 'R73.03', 'I10'],
        'dob': '04/18/1983',
    },

    # ------------------------------------------------------------------
    # 12. Clozapine 45M — schizophrenia (REMS, WBC/ANC monitoring, BHI)
    # ------------------------------------------------------------------
    'BM_CLOZAPINE_45M': {
        'mrn': 'BM012', 'patient_age': 45, 'age': 45,
        'sex': 'male', 'patient_sex': 'M',
        'insurer_type': 'medicaid', 'insurer': 'medicaid',
        'visit_type': 'office_visit', 'user_id': 1,
        'visit_date': date.today(),
        'diagnoses': [
            {'icd10_code': 'F20.9', 'diagnosis_name': 'Schizophrenia', 'status': 'active'},
        ],
        'medications': [
            {'name': 'Clozapine 300mg', 'drug_name': 'Clozapine 300mg', 'rxcui': '2626', 'frequency': 'daily', 'status': 'active'},
        ],
        'vitals': {'systolic_bp': 125, 'diastolic_bp': 80, 'bmi': 30.0},
        'lab_results': [],
        'immunizations': [],
        'social_history': {},
        'awv_history': {'last_awv_date': None},
        'last_awv_date': None,
        'active_chronic_conditions': 1, 'chronic_conditions_count': 1,
        'ccm_minutes_this_month': 0,
        'prior_encounters_count': 6,
        'is_pregnant': False,
        'risk_factors': [],
        'known_diagnoses': ['F20.9'],
        'dob': '12/01/1980',
    },

    # ------------------------------------------------------------------
    # 13. Warfarin + Methotrexate 70F — AFib (INR, hepatotoxicity)
    # ------------------------------------------------------------------
    'BM_WARFARIN_70F': {
        'mrn': 'BM013', 'patient_age': 70, 'age': 70,
        'sex': 'female', 'patient_sex': 'F',
        'insurer_type': 'medicare', 'insurer': 'medicare',
        'visit_type': 'office_visit', 'user_id': 1,
        'visit_date': date.today(),
        'diagnoses': [
            {'icd10_code': 'I48.91', 'diagnosis_name': 'Atrial fibrillation', 'status': 'active'},
            {'icd10_code': 'M06.9', 'diagnosis_name': 'Rheumatoid arthritis', 'status': 'active'},
        ],
        'medications': [
            {'name': 'Warfarin 5mg', 'drug_name': 'Warfarin 5mg', 'rxcui': '11289', 'frequency': 'daily', 'status': 'active'},
            {'name': 'Methotrexate 15mg', 'drug_name': 'Methotrexate 15mg', 'rxcui': '6851', 'frequency': 'weekly', 'status': 'active'},
        ],
        'vitals': {'systolic_bp': 130, 'diastolic_bp': 78, 'bmi': 24.5},
        'lab_results': [],
        'immunizations': [],
        'social_history': {},
        'awv_history': {'last_awv_date': _days_ago(400)},
        'last_awv_date': _days_ago(400),
        'active_chronic_conditions': 2, 'chronic_conditions_count': 2,
        'ccm_minutes_this_month': 20,
        'prior_encounters_count': 10,
        'is_pregnant': False,
        'risk_factors': [],
        'known_diagnoses': ['I48.91', 'M06.9'],
        'dob': '07/30/1955',
    },

    # ------------------------------------------------------------------
    # 14. Lithium 35M — bipolar (lithium level + renal + thyroid)
    # ------------------------------------------------------------------
    'BM_LITHIUM_35M': {
        'mrn': 'BM014', 'patient_age': 35, 'age': 35,
        'sex': 'male', 'patient_sex': 'M',
        'insurer_type': 'commercial', 'insurer': 'commercial',
        'visit_type': 'office_visit', 'user_id': 1,
        'visit_date': date.today(),
        'diagnoses': [
            {'icd10_code': 'F31.9', 'diagnosis_name': 'Bipolar disorder', 'status': 'active'},
        ],
        'medications': [
            {'name': 'Lithium 900mg', 'drug_name': 'Lithium 900mg', 'rxcui': '6468', 'frequency': 'daily', 'status': 'active'},
        ],
        'vitals': {'systolic_bp': 120, 'diastolic_bp': 76, 'bmi': 26.0},
        'lab_results': [],
        'immunizations': [],
        'social_history': {},
        'awv_history': {'last_awv_date': None},
        'last_awv_date': None,
        'active_chronic_conditions': 1, 'chronic_conditions_count': 1,
        'ccm_minutes_this_month': 0,
        'prior_encounters_count': 4,
        'is_pregnant': False,
        'risk_factors': [],
        'known_diagnoses': ['F31.9'],
        'dob': '03/22/1990',
    },

    # ------------------------------------------------------------------
    # 15. Healthy 25F — well visit, minimal triggers
    # ------------------------------------------------------------------
    'BM_HEALTHY_25F': {
        'mrn': 'BM015', 'patient_age': 25, 'age': 25,
        'sex': 'female', 'patient_sex': 'F',
        'insurer_type': 'commercial', 'insurer': 'commercial',
        'visit_type': 'office_visit', 'user_id': 1,
        'visit_date': date.today(),
        'diagnoses': [],
        'medications': [],
        'vitals': {'systolic_bp': 110, 'diastolic_bp': 68, 'bmi': 22.0},
        'lab_results': [],
        'immunizations': [],
        'social_history': {},
        'awv_history': {'last_awv_date': None},
        'last_awv_date': None,
        'active_chronic_conditions': 0, 'chronic_conditions_count': 0,
        'ccm_minutes_this_month': 0,
        'prior_encounters_count': 1,
        'is_pregnant': False,
        'risk_factors': [],
        'known_diagnoses': [],
        'dob': '11/30/2000',
    },

    # ------------------------------------------------------------------
    # 16. Post-discharge 60M — ACS, stent (TCM capture window)
    # ------------------------------------------------------------------
    'BM_POST_DISCHARGE_60M': {
        'mrn': 'BM016', 'patient_age': 60, 'age': 60,
        'sex': 'male', 'patient_sex': 'M',
        'insurer_type': 'medicare', 'insurer': 'medicare',
        'visit_type': 'office_visit', 'user_id': 1,
        'visit_date': date.today(),
        'diagnoses': [
            {'icd10_code': 'I21.4', 'diagnosis_name': 'Acute NSTEMI', 'status': 'active'},
            {'icd10_code': 'Z95.5', 'diagnosis_name': 'Presence of coronary stent', 'status': 'active'},
            {'icd10_code': 'I10', 'diagnosis_name': 'Essential hypertension', 'status': 'active'},
            {'icd10_code': 'E78.5', 'diagnosis_name': 'Hyperlipidemia', 'status': 'active'},
        ],
        'medications': [
            {'name': 'Aspirin 81mg', 'drug_name': 'Aspirin 81mg', 'frequency': 'daily', 'status': 'active'},
            {'name': 'Clopidogrel 75mg', 'drug_name': 'Clopidogrel 75mg', 'frequency': 'daily', 'status': 'active'},
            {'name': 'Atorvastatin 80mg', 'drug_name': 'Atorvastatin 80mg', 'frequency': 'daily', 'status': 'active'},
            {'name': 'Metoprolol 25mg', 'drug_name': 'Metoprolol 25mg', 'frequency': 'twice daily', 'status': 'active'},
        ],
        'vitals': {'systolic_bp': 130, 'diastolic_bp': 80, 'bmi': 28.0},
        'lab_results': [],
        'immunizations': [],
        'social_history': {},
        'awv_history': {'last_awv_date': None},
        'last_awv_date': None,
        'active_chronic_conditions': 4, 'chronic_conditions_count': 4,
        'ccm_minutes_this_month': 0,
        'prior_encounters_count': 2,
        'is_pregnant': False,
        'discharge_date': _days_ago(3),
        'risk_factors': [],
        'known_diagnoses': ['I21.4', 'Z95.5', 'I10', 'E78.5'],
        'dob': '01/10/1965',
    },

    # ------------------------------------------------------------------
    # 17. Telehealth 50F — HTN + anxiety (virtual visit codes)
    # ------------------------------------------------------------------
    'BM_TELEHEALTH_50F': {
        'mrn': 'BM017', 'patient_age': 50, 'age': 50,
        'sex': 'female', 'patient_sex': 'F',
        'insurer_type': 'commercial', 'insurer': 'commercial',
        'visit_type': 'telehealth', 'user_id': 1,
        'visit_date': date.today(),
        'diagnoses': [
            {'icd10_code': 'I10', 'diagnosis_name': 'Essential hypertension', 'status': 'active'},
            {'icd10_code': 'F41.1', 'diagnosis_name': 'Generalized anxiety disorder', 'status': 'active'},
        ],
        'medications': [
            {'name': 'Amlodipine 5mg', 'drug_name': 'Amlodipine 5mg', 'frequency': 'daily', 'status': 'active'},
            {'name': 'Buspirone 10mg', 'drug_name': 'Buspirone 10mg', 'frequency': 'twice daily', 'status': 'active'},
        ],
        'vitals': {'systolic_bp': 132, 'diastolic_bp': 82, 'bmi': 25.5},
        'lab_results': [],
        'immunizations': [],
        'social_history': {},
        'awv_history': {'last_awv_date': None},
        'last_awv_date': None,
        'active_chronic_conditions': 2, 'chronic_conditions_count': 2,
        'ccm_minutes_this_month': 0,
        'prior_encounters_count': 5,
        'is_pregnant': False,
        'risk_factors': [],
        'known_diagnoses': ['I10', 'F41.1'],
        'dob': '05/15/1975',
    },

    # ------------------------------------------------------------------
    # 18. Complex 85M — 8 chronic conditions, 14 meds (stress test)
    # ------------------------------------------------------------------
    'BM_COMPLEX_MULTI_85M': {
        'mrn': 'BM018', 'patient_age': 85, 'age': 85,
        'sex': 'male', 'patient_sex': 'M',
        'insurer_type': 'medicare', 'insurer': 'medicare',
        'visit_type': 'office_visit', 'user_id': 1,
        'visit_date': date.today(),
        'diagnoses': [
            {'icd10_code': 'I10', 'diagnosis_name': 'Essential hypertension', 'status': 'active'},
            {'icd10_code': 'E11.65', 'diagnosis_name': 'Type 2 diabetes', 'status': 'active'},
            {'icd10_code': 'I50.9', 'diagnosis_name': 'Heart failure', 'status': 'active'},
            {'icd10_code': 'I48.91', 'diagnosis_name': 'Atrial fibrillation', 'status': 'active'},
            {'icd10_code': 'N18.4', 'diagnosis_name': 'CKD stage 4', 'status': 'active'},
            {'icd10_code': 'J44.1', 'diagnosis_name': 'COPD', 'status': 'active'},
            {'icd10_code': 'G31.84', 'diagnosis_name': 'Mild cognitive impairment', 'status': 'active'},
            {'icd10_code': 'M81.0', 'diagnosis_name': 'Osteoporosis', 'status': 'active'},
        ],
        'medications': [
            {'name': 'Lisinopril 20mg', 'drug_name': 'Lisinopril 20mg', 'frequency': 'daily', 'status': 'active'},
            {'name': 'Metformin 1000mg', 'drug_name': 'Metformin 1000mg', 'frequency': 'twice daily', 'status': 'active'},
            {'name': 'Insulin glargine', 'drug_name': 'Insulin glargine', 'frequency': 'daily', 'status': 'active'},
            {'name': 'Furosemide 40mg', 'drug_name': 'Furosemide 40mg', 'frequency': 'daily', 'status': 'active'},
            {'name': 'Warfarin 5mg', 'drug_name': 'Warfarin 5mg', 'rxcui': '11289', 'frequency': 'daily', 'status': 'active'},
            {'name': 'Carvedilol 25mg', 'drug_name': 'Carvedilol 25mg', 'frequency': 'twice daily', 'status': 'active'},
            {'name': 'Tiotropium', 'drug_name': 'Tiotropium', 'frequency': 'daily', 'status': 'active'},
            {'name': 'Albuterol inhaler', 'drug_name': 'Albuterol inhaler', 'frequency': 'PRN', 'status': 'active'},
            {'name': 'Donepezil 10mg', 'drug_name': 'Donepezil 10mg', 'frequency': 'daily', 'status': 'active'},
            {'name': 'Alendronate 70mg', 'drug_name': 'Alendronate 70mg', 'frequency': 'weekly', 'status': 'active'},
            {'name': 'Atorvastatin 40mg', 'drug_name': 'Atorvastatin 40mg', 'frequency': 'daily', 'status': 'active'},
            {'name': 'Omeprazole 20mg', 'drug_name': 'Omeprazole 20mg', 'frequency': 'daily', 'status': 'active'},
            {'name': 'Gabapentin 300mg', 'drug_name': 'Gabapentin 300mg', 'frequency': 'three times daily', 'status': 'active'},
            {'name': 'Sertraline 50mg', 'drug_name': 'Sertraline 50mg', 'frequency': 'daily', 'status': 'active'},
        ],
        'vitals': {'systolic_bp': 160, 'diastolic_bp': 92, 'bmi': 30.5},
        'lab_results': [],
        'immunizations': [],
        'social_history': {'smoking_status': 'former'},
        'awv_history': {'last_awv_date': _days_ago(400)},
        'last_awv_date': _days_ago(400),
        'active_chronic_conditions': 8, 'chronic_conditions_count': 8,
        'ccm_minutes_this_month': 45,
        'prior_encounters_count': 20,
        'is_pregnant': False,
        'risk_factors': ['overweight'],
        'known_diagnoses': ['I10', 'E11.65', 'I50.9', 'I48.91', 'N18.4', 'J44.1', 'G31.84', 'M81.0'],
        'dob': '12/25/1940',
    },
}


# =====================================================================
# Expected Results Per Patient
#
# Each entry defines minimum expectations for correctness checks.
# Format:
#   billing:    must_include_categories (detector CATEGORY strings)
#   caregaps:   must_include_types (gap_type strings from CareGapRule)
#   monitoring: must_include_labs (lab_name strings from MonitoringRule)
#
# Range bounds (min/max) are intentionally loose to avoid brittleness
# as detectors evolve. The key invariant is "these categories/types
# MUST appear" and "these MUST NOT appear."
# =====================================================================

EXPECTED = {

    'BM_MEDICARE_68F': {
        'billing': {
            'min_opportunities': 2,
            'max_opportunities': 20,
            'must_include_categories': ['awv', 'ccm'],
            'must_exclude_categories': ['pediatric'],
        },
        'caregaps': {
            'min_gaps': 2,
            'max_gaps': 15,
            'must_include_types': ['depression_screen'],
            'must_exclude_types': [],
        },
        'monitoring': {
            'min_rules': 0,
            'must_include_labs': [],
        },
    },

    'BM_MEDICARE_72M': {
        'billing': {
            'min_opportunities': 2,
            'max_opportunities': 20,
            'must_include_categories': ['ccm'],
            'must_exclude_categories': ['pediatric'],
        },
        'caregaps': {
            'min_gaps': 1,
            'max_gaps': 15,
            'must_include_types': ['depression_screen'],
            'must_exclude_types': [],
        },
        'monitoring': {
            'min_rules': 0,
            'must_include_labs': [],
        },
    },

    'BM_COMMERCIAL_44F': {
        'billing': {
            'min_opportunities': 0,
            'max_opportunities': 15,
            'must_include_categories': [],
            'must_exclude_categories': ['pediatric'],
        },
        'caregaps': {
            'min_gaps': 1,
            'max_gaps': 15,
            'must_include_types': ['depression_screen'],
            'must_exclude_types': [],
        },
        'monitoring': {
            'min_rules': 0,
            'must_include_labs': [],
        },
    },

    'BM_MEDICAID_28M': {
        'billing': {
            'min_opportunities': 0,
            'max_opportunities': 15,
            'must_include_categories': [],
            'must_exclude_categories': ['pediatric'],
        },
        'caregaps': {
            'min_gaps': 1,
            'max_gaps': 15,
            'must_include_types': ['depression_screen'],
            'must_exclude_types': [],
        },
        'monitoring': {
            'min_rules': 0,
            'must_include_labs': [],
        },
    },

    'BM_MEDICARE_ADV_75F': {
        'billing': {
            'min_opportunities': 2,
            'max_opportunities': 20,
            'must_include_categories': ['ccm'],
            'must_exclude_categories': ['pediatric'],
        },
        'caregaps': {
            'min_gaps': 2,
            'max_gaps': 15,
            'must_include_types': ['depression_screen'],
            'must_exclude_types': [],
        },
        'monitoring': {
            'min_rules': 0,
            'must_include_labs': [],
        },
    },

    'BM_PEDIATRIC_8M': {
        'billing': {
            'min_opportunities': 0,
            'max_opportunities': 10,
            'must_include_categories': [],
            'must_exclude_categories': ['ccm'],
        },
        'caregaps': {
            'min_gaps': 0,
            'max_gaps': 10,
            'must_include_types': [],
            'must_exclude_types': [],
        },
        'monitoring': {
            'min_rules': 0,
            'must_include_labs': [],
        },
    },

    'BM_PEDIATRIC_2F': {
        'billing': {
            'min_opportunities': 0,
            'max_opportunities': 10,
            'must_include_categories': [],
            'must_exclude_categories': ['awv', 'ccm'],
        },
        'caregaps': {
            'min_gaps': 0,
            'max_gaps': 10,
            'must_include_types': [],
            'must_exclude_types': [],
        },
        'monitoring': {
            'min_rules': 0,
            'must_include_labs': [],
        },
    },

    'BM_PREGNANT_32F': {
        'billing': {
            'min_opportunities': 0,
            'max_opportunities': 10,
            'must_include_categories': [],
            'must_exclude_categories': ['ccm', 'pediatric'],
        },
        'caregaps': {
            'min_gaps': 1,
            'max_gaps': 15,
            'must_include_types': ['depression_screen'],
            'must_exclude_types': [],
        },
        'monitoring': {
            'min_rules': 0,
            'must_include_labs': [],
        },
    },

    'BM_DUAL_ELIGIBLE_80M': {
        'billing': {
            'min_opportunities': 2,
            'max_opportunities': 25,
            'must_include_categories': ['ccm'],
            'must_exclude_categories': ['pediatric'],
        },
        'caregaps': {
            'min_gaps': 2,
            'max_gaps': 15,
            'must_include_types': ['depression_screen', 'fall_risk'],
            'must_exclude_types': [],
        },
        'monitoring': {
            'min_rules': 0,
            'must_include_labs': [],
        },
    },

    'BM_TOBACCO_55M': {
        'billing': {
            'min_opportunities': 1,
            'max_opportunities': 20,
            'must_include_categories': [],
            'must_exclude_categories': ['pediatric'],
        },
        'caregaps': {
            'min_gaps': 1,
            'max_gaps': 15,
            'must_include_types': ['depression_screen'],
            'must_exclude_types': [],
        },
        'monitoring': {
            'min_rules': 0,
            'must_include_labs': [],
        },
    },

    'BM_OBESE_42F': {
        'billing': {
            'min_opportunities': 0,
            'max_opportunities': 15,
            'must_include_categories': [],
            'must_exclude_categories': ['pediatric'],
        },
        'caregaps': {
            'min_gaps': 2,
            'max_gaps': 15,
            'must_include_types': ['depression_screen'],
            'must_exclude_types': [],
        },
        'monitoring': {
            'min_rules': 0,
            'must_include_labs': [],
        },
    },

    'BM_CLOZAPINE_45M': {
        'billing': {
            'min_opportunities': 0,
            'max_opportunities': 15,
            'must_include_categories': [],
            'must_exclude_categories': ['ccm', 'pediatric'],
        },
        'caregaps': {
            'min_gaps': 1,
            'max_gaps': 15,
            'must_include_types': ['depression_screen'],
            'must_exclude_types': [],
        },
        'monitoring': {
            'min_rules': 0,
            'must_include_labs': [],
        },
    },

    'BM_WARFARIN_70F': {
        'billing': {
            'min_opportunities': 1,
            'max_opportunities': 20,
            'must_include_categories': ['ccm'],
            'must_exclude_categories': ['pediatric'],
        },
        'caregaps': {
            'min_gaps': 2,
            'max_gaps': 15,
            'must_include_types': ['depression_screen'],
            'must_exclude_types': [],
        },
        'monitoring': {
            'min_rules': 0,
            'must_include_labs': [],
        },
    },

    'BM_LITHIUM_35M': {
        'billing': {
            'min_opportunities': 0,
            'max_opportunities': 15,
            'must_include_categories': [],
            'must_exclude_categories': ['ccm', 'pediatric'],
        },
        'caregaps': {
            'min_gaps': 1,
            'max_gaps': 15,
            'must_include_types': ['depression_screen'],
            'must_exclude_types': [],
        },
        'monitoring': {
            'min_rules': 0,
            'must_include_labs': [],
        },
    },

    'BM_HEALTHY_25F': {
        'billing': {
            'min_opportunities': 0,
            'max_opportunities': 10,
            'must_include_categories': [],
            'must_exclude_categories': ['ccm', 'pediatric'],
        },
        'caregaps': {
            'min_gaps': 1,
            'max_gaps': 15,
            'must_include_types': ['depression_screen'],
            'must_exclude_types': [],
        },
        'monitoring': {
            'min_rules': 0,
            'must_include_labs': [],
        },
    },

    'BM_POST_DISCHARGE_60M': {
        'billing': {
            'min_opportunities': 1,
            'max_opportunities': 20,
            'must_include_categories': [],
            'must_exclude_categories': ['pediatric'],
        },
        'caregaps': {
            'min_gaps': 1,
            'max_gaps': 15,
            'must_include_types': ['depression_screen'],
            'must_exclude_types': [],
        },
        'monitoring': {
            'min_rules': 0,
            'must_include_labs': [],
        },
    },

    'BM_TELEHEALTH_50F': {
        'billing': {
            'min_opportunities': 0,
            'max_opportunities': 15,
            'must_include_categories': [],
            'must_exclude_categories': ['pediatric'],
        },
        'caregaps': {
            'min_gaps': 1,
            'max_gaps': 15,
            'must_include_types': ['depression_screen'],
            'must_exclude_types': [],
        },
        'monitoring': {
            'min_rules': 0,
            'must_include_labs': [],
        },
    },

    'BM_COMPLEX_MULTI_85M': {
        'billing': {
            'min_opportunities': 3,
            'max_opportunities': 30,
            'must_include_categories': ['ccm'],
            'must_exclude_categories': ['pediatric'],
        },
        'caregaps': {
            'min_gaps': 2,
            'max_gaps': 20,
            'must_include_types': ['depression_screen', 'fall_risk'],
            'must_exclude_types': [],
        },
        'monitoring': {
            'min_rules': 0,
            'must_include_labs': [],
        },
    },
}
