"""
Generate rich test patient CDA XML files for CareCompanion testing.

Run: venv\\Scripts\\python.exe scripts/generate_test_xmls.py

Generates 7 clinically diverse patients covering:
  - USPSTF screenings, billing capture, lab tracking, care gaps
  - CCM/TCM eligibility, risk scores, calculators
  - Drug safety, formulary gaps, clinical guidelines
  - Note generator, prior notes, immunization series gaps
"""
import os
import sys
from datetime import datetime

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'Documents', 'xml_test_patients'
)

PRACTICE_NAME = "Family Practice Associates of Chesterfield"
PRACTICE_ADDR = """<streetAddressLine>13911 St Francis Blvd, Suite 101</streetAddressLine>
        <city>Midlothian</city>
        <state>VA</state>
        <postalCode>23114</postalCode>
        <country>US</country>"""
PRACTICE_PHONE = "tel:+1(804)-423-9913"
NPI_ROOT = "2.16.840.1.113883.4.6"
ORG_NPI = "1306884820"


def _header(patient_id, given, family, gender_code, gender_display, dob,
            addr_street, addr_city, addr_state, addr_zip, phone,
            race_code="2106-3", race_display="White",
            ethnic_code="2186-5", ethnic_display="Not Hispanic or Latino",
            marital_code="M", marital_display="Married",
            language="en"):
    """Generate CDA header with patient demographics."""
    return f"""<?xml version="1.0"?>
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
  <title>{PRACTICE_NAME} Clinical Summary</title>
  <effectiveTime value="202603171423-0400" />
  <confidentialityCode code="N" displayName="Normal" codeSystem="2.16.840.1.113883.5.25" codeSystemName="Confidentiality" />
  <languageCode code="en-US" />
  <setId root="00000000-0000-0000-0000-{patient_id:012d}" extension="AmazingCharts" />
  <versionNumber value="1" />
  <recordTarget>
    <patientRole>
      <id root="2.16.840.1.113883.3.1167.2799" extension="{patient_id}" />
      <addr use="HP">
        <streetAddressLine>{addr_street}</streetAddressLine>
        <city>{addr_city}</city>
        <state>{addr_state}</state>
        <postalCode>{addr_zip}</postalCode>
        <country nullFlavor="NI" />
        <useablePeriod xsi:type="IVL_TS"><low value="20260317" /></useablePeriod>
      </addr>
      <telecom use="HP" value="tel:+1{phone}" />
      <patient>
        <name use="L">
          <given>{given}</given>
          <family>{family}</family>
        </name>
        <administrativeGenderCode code="{gender_code}" codeSystem="2.16.840.1.113883.5.1" displayName="{gender_display}" codeSystemName="AdministrativeGender" />
        <birthTime value="{dob}" />
        <maritalStatusCode code="{marital_code}" displayName="{marital_display}" codeSystem="2.16.840.1.113883.5.2" />
        <religiousAffiliationCode nullFlavor="NI" />
        <raceCode code="{race_code}" displayName="{race_display}" codeSystem="2.16.840.1.113883.6.238" codeSystemName="Race &amp; Ethnicity - CDC" />
        <ethnicGroupCode code="{ethnic_code}" displayName="{ethnic_display}" codeSystem="2.16.840.1.113883.6.238" codeSystemName="Race &amp; Ethnicity - CDC" />
        <languageCommunication>
          <languageCode code="{language}" />
        </languageCommunication>
      </patient>
      <providerOrganization>
        <id root="2.16.840.1.113883.3.1167" extension="AmazingCharts" />
        <name>{PRACTICE_NAME}</name>
        <telecom use="WP" value="{PRACTICE_PHONE}" />
        <addr use="WP">{PRACTICE_ADDR}</addr>
      </providerOrganization>
    </patientRole>
  </recordTarget>
  <author>
    <time value="202603171423-0400" />
    <assignedAuthor>
      <id root="{NPI_ROOT}" extension="1891645123" assigningAuthorityName="National Provider Identifier" />
      <addr use="WP">{PRACTICE_ADDR}</addr>
      <telecom use="WP" value="{PRACTICE_PHONE}" />
      <assignedPerson><name><given>Cory</given><family>Denton</family><suffix>FNP</suffix></name></assignedPerson>
      <representedOrganization>
        <name>{PRACTICE_NAME}</name>
        <telecom use="WP" value="{PRACTICE_PHONE}" />
        <addr use="WP">{PRACTICE_ADDR}</addr>
      </representedOrganization>
    </assignedAuthor>
  </author>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="{NPI_ROOT}" extension="{ORG_NPI}" assigningAuthorityName="National Provider Identifier" />
        <name>{PRACTICE_NAME}</name>
        <telecom use="WP" value="{PRACTICE_PHONE}" />
        <addr use="WP">{PRACTICE_ADDR}</addr>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
  <documentationOf typeCode="DOC">
    <serviceEvent classCode="PCPR">
      <effectiveTime><low value="{dob}" /><high value="20260317" /></effectiveTime>
      <performer typeCode="PRF">
        <time><low value="20250101" /></time>
        <assignedEntity>
          <id extension="1891645123" root="{NPI_ROOT}" assigningAuthorityName="National Provider Identifier" />
          <addr use="WP">{PRACTICE_ADDR}</addr>
          <telecom use="WP" value="{PRACTICE_PHONE}" />
          <assignedPerson><name><given>Cory</given><family>Denton</family><suffix>FNP</suffix></name></assignedPerson>
          <representedOrganization>
            <id root="2.16.840.1.113883.3.1167.2799" />
            <name>{PRACTICE_NAME}</name>
            <addr use="WP">{PRACTICE_ADDR}</addr>
          </representedOrganization>
        </assignedEntity>
      </performer>
    </serviceEvent>
  </documentationOf>
  <componentOf>
    <encompassingEncounter>
      <id root="00000000-0000-0000-0000-{patient_id:012d}" extension="{ORG_NPI}" />
      <code code="AMB" codeSystem="2.16.840.1.113883.5.4" codeSystemName="ActCode" displayName="Ambulatory" />
      <effectiveTime><low value="202603171000-0400" /></effectiveTime>
      <location>
        <healthCareFacility>
          <id root="2.16.840.1.113883.19" extension="{ORG_NPI}" />
          <location>
            <name>{PRACTICE_NAME}</name>
            <addr use="WP">{PRACTICE_ADDR}</addr>
          </location>
        </healthCareFacility>
      </location>
    </encompassingEncounter>
  </componentOf>
  <component>
    <structuredBody>
"""


def _section(loinc_code, title, table_html):
    """Wrap a section with LOINC code and table content."""
    return f"""      <component>
        <section>
          <code code="{loinc_code}" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC" displayName="{title}" />
          <title>{title.upper()}</title>
          <text>
            <table xmlns:xsd="http://www.w3.org/2001/XMLSchema">
{table_html}
            </table>
          </text>
        </section>
      </component>
"""


def _table(headers, rows):
    """Build HTML table from headers and rows."""
    hdr = "              <thead><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead>\n"
    body = "              <tbody>\n"
    for row in rows:
        body += "                <tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>\n"
    body += "              </tbody>"
    return hdr + body


def _footer():
    return """    </structuredBody>
  </component>
</ClinicalDocument>
"""


def _social_section(text_content):
    """Social history uses plain text, not table format."""
    return f"""      <component>
        <section>
          <code code="29762-2" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC" displayName="Social History" />
          <title>SOCIAL HISTORY</title>
          <text>{text_content}</text>
        </section>
      </component>
"""


def _insurance_section(rows):
    """Insurance section with table."""
    headers = ["Payer", "Policy Type", "Member ID", "Group"]
    return _section("48768-6", "Insurance", _table(headers, rows))


def _notes_section(notes):
    """Encounter notes section with LOINC 11506-3."""
    headers = ["Date", "Provider", "Note Type", "Note Text", "Location"]
    rows = []
    for n in notes:
        rows.append([n['date'], n['provider'], n['type'], n['text'], n['location']])
    return _section("11506-3", "Progress Notes", _table(headers, rows))


# ============================================================
# PATIENT DEFINITIONS
# ============================================================

def patient_31306():
    """Margaret Thompson, 72F — Elderly Medicare, AWV, CCM eligible."""
    xml = _header(
        31306, "Margaret", "Thompson", "F", "Female", "19540315",
        "4521 Winding Creek Dr", "Midlothian", "VA", "23112",
        "(804)-555-7201", race_code="2106-3", race_display="White",
        marital_code="W", marital_display="Widowed"
    )

    # Allergies
    xml += _section("48765-2", "Allergies and Adverse Reactions", _table(
        ["Substance", "Reaction", "Severity", "Status"],
        [
            ["Sulfonamides [RxNorm: 10171]", "Rash", "moderate", "active"],
            ["Codeine [RxNorm: 2670]", "Nausea/Vomiting", "mild", "active"],
            ["Iodinated Contrast [RxNorm: 358793]", "Anaphylaxis", "severe", "active"],
        ]
    ))

    # Medications
    xml += _section("10160-0", "Medications", _table(
        ["Medication", "Generic Name", "Instructions", "Dosage", "Start Date", "Status"],
        [
            ["lisinopril 20 mg tablet [RxNorm: 314076]", "lisinopril", "Take 1 tablet by mouth daily", "20 mg", "01/15/2020", "active"],
            ["metformin 1000 mg tablet [RxNorm: 861004]", "metformin", "Take 1 tablet by mouth twice daily", "1000 mg", "03/10/2019", "active"],
            ["atorvastatin 40 mg tablet [RxNorm: 259255]", "atorvastatin", "Take 1 tablet by mouth at bedtime", "40 mg", "06/01/2018", "active"],
            ["alendronate 70 mg tablet [RxNorm: 151558]", "alendronate", "Take 1 tablet by mouth weekly on empty stomach", "70 mg", "09/15/2022", "active"],
            ["omeprazole 20 mg capsule [RxNorm: 198053]", "omeprazole", "Take 1 capsule by mouth daily before breakfast", "20 mg", "02/20/2021", "active"],
            ["sertraline 100 mg tablet [RxNorm: 312938]", "sertraline", "Take 1 tablet by mouth daily", "100 mg", "11/01/2020", "active"],
            ["amlodipine 5 mg tablet [RxNorm: 197361]", "amlodipine", "Take 1 tablet by mouth daily", "5 mg", "04/15/2021", "active"],
            ["aspirin 81 mg tablet [RxNorm: 243670]", "aspirin", "Take 1 tablet by mouth daily", "81 mg", "01/01/2018", "active"],
            ["vitamin D3 2000 IU tablet [RxNorm: 392263]", "cholecalciferol", "Take 1 tablet by mouth daily", "2000 IU", "03/01/2023", "active"],
            ["hydrochlorothiazide 25 mg tablet [RxNorm: 310798]", "hydrochlorothiazide", "Take 1 tablet by mouth daily", "25 mg", "01/15/2020", "inactive"],
        ]
    ))

    # Diagnoses
    xml += _section("11450-4", "Problems", _table(
        ["Problem", "Problem Status", "Date Started", "Date Resolved"],
        [
            ["Essential hypertension [ICD10: I10]", "active", "03/15/2015", ""],
            ["Type 2 diabetes mellitus without complications [ICD10: E11.9]", "active", "06/22/2018", ""],
            ["Chronic kidney disease stage 3 [ICD10: N18.3]", "active", "09/10/2022", ""],
            ["Postmenopausal osteoporosis without fracture [ICD10: M81.0]", "active", "01/20/2022", ""],
            ["Mixed hyperlipidemia [ICD10: E78.2]", "active", "04/08/2017", ""],
            ["Gastroesophageal reflux disease [ICD10: K21.0]", "active", "11/15/2020", ""],
            ["Major depressive disorder recurrent moderate [ICD10: F33.1]", "active", "08/01/2019", ""],
            ["Obesity BMI 30-34.9 [ICD10: E66.01]", "active", "06/22/2018", ""],
            ["Vitamin D deficiency [ICD10: E55.9]", "active", "03/01/2023", ""],
            ["Chronic pain syndrome [ICD10: G89.29]", "active", "05/10/2021", ""],
            ["Urinary tract infection [ICD10: N39.0]", "resolved", "01/05/2026", "01/19/2026"],
        ]
    ))

    # Vitals
    xml += _section("8716-3", "Vital Signs", _table(
        ["Encounter", "Height (in)", "Weight (lb)", "BMI (kg/m2)", "BP Sys (mmHg)", "BP Dias (mmHg)", "Heart Rate (/min)", "O2 % BldC Oximetry", "Body Temperature", "Respiratory Rate (/min)"],
        [
            ["03/10/2026", "63", "185", "32.8", "142", "88", "76", "97", "98.2", "16"],
            ["12/15/2025", "63", "188", "33.3", "148", "92", "80", "96", "98.4", "18"],
            ["09/20/2025", "63", "190", "33.7", "150", "90", "78", "97", "98.6", "16"],
        ]
    ))

    # Lab Results
    xml += _section("30954-2", "Lab Results", _table(
        ["Test Name", "Result", "Units", "Flag", "Date"],
        [
            ["Hemoglobin A1c [LOINC: 4548-4]", "7.8", "%", "H", "03/05/2026"],
            ["Hemoglobin A1c [LOINC: 4548-4]", "7.5", "%", "H", "09/15/2025"],
            ["Glucose fasting [LOINC: 1558-6]", "142", "mg/dL", "H", "03/05/2026"],
            ["Creatinine [LOINC: 2160-0]", "1.6", "mg/dL", "H", "03/05/2026"],
            ["eGFR [LOINC: 48642-3]", "38", "mL/min/1.73m2", "L", "03/05/2026"],
            ["BUN [LOINC: 3094-0]", "28", "mg/dL", "H", "03/05/2026"],
            ["Potassium [LOINC: 2823-3]", "4.8", "mmol/L", "normal", "03/05/2026"],
            ["Sodium [LOINC: 2951-2]", "138", "mmol/L", "normal", "03/05/2026"],
            ["Total Cholesterol [LOINC: 2093-3]", "224", "mg/dL", "H", "03/05/2026"],
            ["LDL Cholesterol [LOINC: 2089-1]", "138", "mg/dL", "H", "03/05/2026"],
            ["HDL Cholesterol [LOINC: 2085-9]", "48", "mg/dL", "normal", "03/05/2026"],
            ["Triglycerides [LOINC: 2571-8]", "190", "mg/dL", "H", "03/05/2026"],
            ["TSH [LOINC: 3016-3]", "3.2", "mIU/L", "normal", "03/05/2026"],
            ["Vitamin D 25-OH [LOINC: 1989-3]", "22", "ng/mL", "L", "03/05/2026"],
            ["Urine Albumin/Creatinine Ratio [LOINC: 9318-7]", "65", "mg/g", "H", "03/05/2026"],
            ["CBC WBC [LOINC: 6690-2]", "7.2", "10*3/uL", "normal", "03/05/2026"],
            ["Hemoglobin [LOINC: 718-7]", "12.1", "g/dL", "normal", "03/05/2026"],
            ["Platelet Count [LOINC: 777-3]", "210", "10*3/uL", "normal", "03/05/2026"],
        ]
    ))

    # Immunizations
    xml += _section("11369-6", "Immunizations", _table(
        ["Vaccine", "Date", "Status"],
        [
            ["Influenza vaccine 2025-2026", "10/15/2025", "completed"],
            ["Pneumococcal PCV20 (Prevnar 20)", "03/10/2024", "completed"],
            ["Shingrix (Zoster) Dose 1", "06/15/2024", "completed"],
            ["COVID-19 Vaccine 2024-2025 (Pfizer)", "10/01/2024", "completed"],
            ["Tdap (Boostrix)", "08/20/2020", "completed"],
            ["Influenza vaccine 2024-2025", "10/10/2024", "completed"],
        ]
    ))

    # Social History
    xml += _social_section(
        "Tobacco: Former smoker (quit 2010, 1 ppd x 20 yrs = 20 pk yrs). "
        "Alcohol: Occasional wine with dinner (1-2 glasses/week). "
        "Employment: Retired school teacher. "
        "Marital Status: Widowed (husband passed 2021). "
        "Lives alone, daughter visits weekly. "
        "Exercise: Walks 20 minutes 3x/week."
    )

    # Insurance
    xml += _insurance_section([
        ["Medicare Part B", "Medicare", "1EG4-TE5-MK72", "N/A"],
        ["AARP Medicare Supplement Plan G", "Supplemental", "SUP-887421", "GRP-44521"],
    ])

    # Encounter Notes
    xml += _notes_section([
        {
            "date": "03/10/2026", "provider": "Cory Denton, FNP",
            "type": "Progress Note", "location": PRACTICE_NAME,
            "text": "CC: Follow-up DM, HTN, CKD\nHPI: 72yo female presents for chronic disease management. Reports good medication compliance. Occasional HA in mornings. Denies chest pain, SOB, edema.\nA1c improved to 7.8% from 8.2%. Creatinine stable at 1.6. eGFR 38 (Stage 3b CKD). BP elevated today 142/88.\nAssessment:\n# Type 2 DM (E11.9): A1c trending down. Continue metformin 1000mg BID.\n# HTN (I10): Suboptimal control. Increase amlodipine to 10mg daily.\n# CKD Stage 3 (N18.3): Stable. Continue ACE inhibitor. Recheck BMP in 3 months.\n# Osteoporosis (M81.0): Continue alendronate. DEXA due 2027.\n# Depression (F33.1): PHQ-9 = 8 (mild). Stable on sertraline 100mg.\nPlan: Labs in 3 months. RTC 3 months. Shingrix dose 2 due. Discussed colon cancer screening — patient will schedule colonoscopy."
        },
        {
            "date": "12/15/2025", "provider": "Cory Denton, FNP",
            "type": "Progress Note", "location": PRACTICE_NAME,
            "text": "CC: Chronic disease follow-up\nHPI: Reports increased fatigue, occasional nocturia x2. No dysuria. Diet compliance fair — admits to holiday indulgences.\nA1c 7.5%. BP 148/92. Weight up 2 lbs.\nAssessment:\n# DM2: A1c slightly improved. Reinforce dietary counseling.\n# HTN: Adding HCTZ 12.5mg. Monitor K+ in 2 weeks.\n# CKD: Urine albumin/creat ratio 55 — microalbuminuria. Continue ACE.\n# Depression: Stable. PHQ-9 = 6.\nPlan: BMP + K in 2 weeks. Follow-up 3 months."
        },
        {
            "date": "01/05/2026", "provider": "Patricia Lavinus, NP",
            "type": "Acute Visit", "location": PRACTICE_NAME,
            "text": "CC: Dysuria x 3 days, urgency, frequency\nHPI: 72yo with h/o CKD presents with UTI symptoms. No fever, no flank pain.\nUA: Positive nitrites, leukocyte esterase 3+, bacteria many. Culture sent.\nAssessment: Uncomplicated UTI (N39.0) in setting of CKD.\nPlan: Nitrofurantoin 100mg BID x 5 days (renal-dose appropriate for eGFR >30). Increase fluids. Follow-up if not improved in 48 hours."
        },
        {
            "date": "09/15/2025", "provider": "Cory Denton, FNP",
            "type": "Annual Wellness Visit", "location": PRACTICE_NAME,
            "text": "ANNUAL WELLNESS VISIT (AWV) — G0439\nHPI: 72yo female here for AWV. No acute complaints.\nPreventive Review:\n- Mammogram: Last 01/2024. Due 01/2025 — OVERDUE\n- Colonoscopy: Last 2018. Due 2028 (or stool test annually) — OVERDUE for stool test\n- Bone Density: Last 2022. Next due 2024 — Schedule DEXA\n- Lung Cancer Screen: Former smoker 20 pack-years, quit <15 years ago. ELIGIBLE for LDCT\n- Depression Screen: PHQ-9 completed today = 6\n- Fall Risk: Timed Up and Go = 12 seconds (normal)\n- Cognitive: Mini-Cog normal\n- Advance Directive: Completed, copy in chart\nVaccines: Flu given today. Shingrix dose 2 needed (dose 1 was 06/2024).\nPlan: Order mammogram, FIT test, DEXA scan, LDCT chest. RTC 3 months for chronic disease f/u."
        },
    ])

    xml += _footer()
    return xml


def patient_43461():
    """Marcus Williams, 32M — Psych/behavioral health, smoker, CCM candidate."""
    xml = _header(
        43461, "Marcus", "Williams", "M", "Male", "19940815",
        "2847 Oak Ridge Ln", "Chesterfield", "VA", "23832",
        "(804)-555-3318", race_code="2054-5", race_display="Black or African American",
        marital_code="M", marital_display="Married"
    )

    xml += _section("48765-2", "Allergies and Adverse Reactions", _table(
        ["Substance", "Reaction", "Severity", "Status"],
        [
            ["Lamictal (lamotrigine) [RxNorm: 28439]", "Stevens-Johnson Syndrome", "severe", "active"],
            ["Wellbutrin (bupropion) [RxNorm: 42347]", "Seizures", "severe", "active"],
        ]
    ))

    xml += _section("10160-0", "Medications", _table(
        ["Medication", "Generic Name", "Instructions", "Dosage", "Start Date", "Status"],
        [
            ["aripiprazole 5 mg tablet [RxNorm: 352381]", "aripiprazole", "Take 1 tablet by mouth once daily", "5 mg", "08/15/2024", "active"],
            ["amphetamine-dextroamphetamine 10 mg tablet [RxNorm: 884520]", "amphetamine/dextroamphetamine", "Take 1 tablet by mouth daily at 2pm", "10 mg", "03/10/2025", "active"],
            ["buspirone 10 mg tablet [RxNorm: 104894]", "buspirone", "Take 1 tablet by mouth once daily", "10 mg", "06/01/2024", "active"],
            ["tadalafil 10 mg tablet [RxNorm: 358263]", "tadalafil", "Take 1 tablet by mouth as needed", "10 mg", "09/01/2025", "active"],
            ["esomeprazole 40 mg capsule [RxNorm: 261273]", "esomeprazole", "Take 1 capsule by mouth daily before breakfast", "40 mg", "04/15/2024", "active"],
            ["fluoxetine 20 mg capsule [RxNorm: 310384]", "fluoxetine", "Take 1 capsule by mouth daily", "20 mg", "02/01/2024", "active"],
            ["topiramate 25 mg tablet [RxNorm: 38404]", "topiramate", "Take 1 tablet by mouth at bedtime", "25 mg", "07/01/2024", "active"],
            ["trazodone 50 mg tablet [RxNorm: 38404]", "trazodone", "Take 1 tablet by mouth at bedtime for sleep", "50 mg", "05/15/2024", "active"],
            ["nicotine patch 21 mg [RxNorm: 636225]", "nicotine", "Apply 1 patch daily", "21 mg", "02/15/2026", "active"],
        ]
    ))

    xml += _section("11450-4", "Problems", _table(
        ["Problem", "Problem Status", "Date Started"],
        [
            ["Bipolar II disorder [ICD10: F31.81]", "active", "01/15/2022"],
            ["Generalized anxiety disorder [ICD10: F41.1]", "active", "03/20/2021"],
            ["Major depressive disorder recurrent [ICD10: F33.1]", "active", "03/20/2021"],
            ["Attention deficit disorder with hyperactivity [ICD10: F90.2]", "active", "11/05/2024"],
            ["Tobacco use disorder [ICD10: F17.210]", "active", "08/15/2024"],
            ["Gastroesophageal reflux disease [ICD10: K21.0]", "active", "04/15/2024"],
            ["Erectile dysfunction [ICD10: N52.9]", "active", "09/01/2025"],
            ["Insomnia disorder [ICD10: G47.00]", "active", "05/15/2024"],
        ]
    ))

    xml += _section("8716-3", "Vital Signs", _table(
        ["Encounter", "Height (in)", "Weight (lb)", "BMI (kg/m2)", "BP Sys (mmHg)", "BP Dias (mmHg)", "Heart Rate (/min)", "O2 % BldC Oximetry", "Body Temperature", "Respiratory Rate (/min)"],
        [
            ["03/05/2026", "70", "195", "28.0", "128", "82", "74", "98", "98.4", "16"],
            ["12/10/2025", "70", "192", "27.5", "124", "78", "72", "99", "98.6", "14"],
        ]
    ))

    xml += _section("30954-2", "Lab Results", _table(
        ["Test Name", "Result", "Units", "Flag", "Date"],
        [
            ["CBC WBC [LOINC: 6690-2]", "6.8", "10*3/uL", "normal", "03/01/2026"],
            ["Hemoglobin [LOINC: 718-7]", "15.2", "g/dL", "normal", "03/01/2026"],
            ["CMP Glucose [LOINC: 2345-7]", "92", "mg/dL", "normal", "03/01/2026"],
            ["Hepatic Function Panel ALT [LOINC: 1742-6]", "32", "U/L", "normal", "03/01/2026"],
            ["Hepatic Function Panel AST [LOINC: 1920-8]", "28", "U/L", "normal", "03/01/2026"],
            ["Lipid Panel Total Cholesterol [LOINC: 2093-3]", "198", "mg/dL", "normal", "03/01/2026"],
            ["Lipid Panel LDL [LOINC: 2089-1]", "118", "mg/dL", "normal", "03/01/2026"],
            ["TSH [LOINC: 3016-3]", "2.1", "mIU/L", "normal", "03/01/2026"],
            ["Urine Drug Screen [LOINC: 19295-5]", "Positive amphetamine (prescribed)", "qualitative", "normal", "03/01/2026"],
        ]
    ))

    xml += _section("11369-6", "Immunizations", _table(
        ["Vaccine", "Date", "Status"],
        [
            ["Influenza vaccine 2025-2026", "11/01/2025", "completed"],
            ["COVID-19 Vaccine 2024-2025 (Moderna)", "10/15/2024", "completed"],
            ["Tdap (Adacel)", "06/22/2020", "completed"],
            ["Hepatitis B series (3 doses)", "01/15/2015", "completed"],
        ]
    ))

    xml += _social_section(
        "Tobacco: Current every day smoker (1 ppd x 10 yrs = 10 pk yrs, Start Date: 08/15/2014). "
        "Nicotine patch started 02/15/2026 for cessation attempt. "
        "Alcohol: No. "
        "Illicit Drug Use: No (prescribed stimulant). "
        "Employment: Construction foreman. "
        "Marital Status: Married, wife supportive. "
        "Exercise: Active job, walks job sites daily."
    )

    xml += _insurance_section([
        ["Anthem Blue Cross Blue Shield", "Commercial PPO", "ANT-554821", "GRP-CONSTR-110"],
    ])

    xml += _notes_section([
        {
            "date": "03/05/2026", "provider": "Cory Denton, FNP",
            "type": "Progress Note", "location": PRACTICE_NAME,
            "text": "CC: Follow-up bipolar, ADHD, tobacco cessation\nHPI: 32yo male here for med management. Psychiatrist co-manages bipolar/mood. Reports stable mood on Abilify 5mg. ADHD controlled with Adderall — wife confirms improved focus at work. Smoking cessation going well — down to 5 cigs/day from 1 ppd since starting patch.\nDenies SI/HI. Sleep improved with trazodone. Anxiety manageable with buspirone.\nPHQ-9: 8 (mild). GAD-7: 6 (mild).\nAssessment:\n# Bipolar II (F31.81): Stable. Psych manages Abilify dosage.\n# ADHD (F90.2): Well controlled. Continue Adderall 10mg daily.\n# Tobacco use (F17.210): Progress on cessation. Continue NRT patch. Target quit date: 04/01/2026.\n# Anxiety (F41.1): Stable on buspirone.\nPlan: Continue all meds. Liver panel in 3 months (monitoring topiramate). Follow-up 3 months. Smoking cessation support call in 2 weeks."
        },
        {
            "date": "12/10/2025", "provider": "Cory Denton, FNP",
            "type": "Progress Note", "location": PRACTICE_NAME,
            "text": "CC: Psych med follow-up + new complaint of insomnia\nHPI: Difficulty falling asleep. Tried melatonin without benefit. Mood otherwise stable.\nAssessment:\n# Insomnia (G47.00): Add trazodone 50mg QHS.\n# Bipolar II: Stable.\n# ADHD: Review stimulant timing — moved to 2pm to avoid evening activation.\nPlan: Start trazodone. Recheck in 3 months. Sleep hygiene handout given."
        },
    ])

    xml += _footer()
    return xml


def patient_45534():
    """Robert Chen, 55M — Metabolic syndrome, ASCVD risk, lung cancer screening."""
    xml = _header(
        45534, "Robert", "Chen", "M", "Male", "19710622",
        "3300 N Central Ave", "Phoenix", "AZ", "85004",
        "(804)-555-5554", race_code="2028-9", race_display="Asian",
        ethnic_code="2186-5", ethnic_display="Not Hispanic or Latino"
    )

    xml += _section("48765-2", "Allergies and Adverse Reactions", _table(
        ["Substance", "Reaction", "Severity", "Status"],
        [
            ["ACE Inhibitors (lisinopril) [RxNorm: 29046]", "Persistent dry cough", "moderate", "active"],
            ["Shellfish", "Anaphylaxis, throat swelling", "severe", "active"],
            ["Erythromycin [RxNorm: 4053]", "GI upset, diarrhea", "mild", "active"],
        ]
    ))

    xml += _section("10160-0", "Medications", _table(
        ["Medication", "Generic Name", "Instructions", "Dosage", "Start Date", "Status"],
        [
            ["losartan 100 mg tablet [RxNorm: 979480]", "losartan", "Take 1 tablet by mouth daily", "100 mg", "06/15/2020", "active"],
            ["rosuvastatin 20 mg tablet [RxNorm: 859747]", "rosuvastatin", "Take 1 tablet by mouth at bedtime", "20 mg", "01/10/2021", "active"],
            ["metformin 500 mg tablet [RxNorm: 861007]", "metformin", "Take 1 tablet by mouth twice daily", "500 mg", "09/01/2023", "active"],
            ["pantoprazole 40 mg tablet [RxNorm: 261270]", "pantoprazole", "Take 1 tablet by mouth daily before breakfast", "40 mg", "03/15/2022", "active"],
            ["aspirin 81 mg tablet [RxNorm: 243670]", "aspirin", "Take 1 tablet by mouth daily", "81 mg", "01/10/2021", "active"],
            ["fish oil 1000 mg capsule [RxNorm: 1246283]", "omega-3 fatty acids", "Take 1 capsule by mouth twice daily", "1000 mg", "06/01/2023", "active"],
            ["lisinopril 10 mg tablet [RxNorm: 314077]", "lisinopril", "Take 1 tablet by mouth daily", "10 mg", "01/01/2019", "inactive"],
        ]
    ))

    xml += _section("11450-4", "Problems", _table(
        ["Problem", "Problem Status", "Date Started"],
        [
            ["Essential hypertension [ICD10: I10]", "active", "08/20/2017"],
            ["Mixed hyperlipidemia [ICD10: E78.2]", "active", "08/20/2017"],
            ["Prediabetes [ICD10: R73.03]", "active", "09/01/2023"],
            ["Morbid obesity BMI 35-39.9 [ICD10: E66.01]", "active", "01/15/2020"],
            ["Obstructive sleep apnea [ICD10: G47.33]", "active", "04/10/2021"],
            ["Gastroesophageal reflux disease [ICD10: K21.0]", "active", "03/15/2022"],
            ["Nicotine dependence in remission [ICD10: F17.211]", "active", "05/01/2021"],
            ["Benign prostatic hyperplasia [ICD10: N40.0]", "active", "11/20/2025"],
        ]
    ))

    xml += _section("8716-3", "Vital Signs", _table(
        ["Encounter", "Height (in)", "Weight (lb)", "BMI (kg/m2)", "BP Sys (mmHg)", "BP Dias (mmHg)", "Heart Rate (/min)", "O2 % BldC Oximetry", "Body Temperature", "Respiratory Rate (/min)"],
        [
            ["03/12/2026", "70", "245", "35.2", "148", "92", "82", "95", "98.4", "16"],
            ["12/01/2025", "70", "248", "35.6", "144", "90", "80", "95", "98.2", "18"],
            ["09/15/2025", "70", "252", "36.2", "152", "94", "84", "94", "98.6", "16"],
        ]
    ))

    xml += _section("30954-2", "Lab Results", _table(
        ["Test Name", "Result", "Units", "Flag", "Date"],
        [
            ["Hemoglobin A1c [LOINC: 4548-4]", "6.2", "%", "H", "03/08/2026"],
            ["Glucose fasting [LOINC: 1558-6]", "118", "mg/dL", "H", "03/08/2026"],
            ["Total Cholesterol [LOINC: 2093-3]", "238", "mg/dL", "H", "03/08/2026"],
            ["LDL Cholesterol [LOINC: 2089-1]", "155", "mg/dL", "H", "03/08/2026"],
            ["HDL Cholesterol [LOINC: 2085-9]", "38", "mg/dL", "L", "03/08/2026"],
            ["Triglycerides [LOINC: 2571-8]", "225", "mg/dL", "H", "03/08/2026"],
            ["Creatinine [LOINC: 2160-0]", "1.1", "mg/dL", "normal", "03/08/2026"],
            ["eGFR [LOINC: 48642-3]", "78", "mL/min/1.73m2", "normal", "03/08/2026"],
            ["PSA [LOINC: 2857-1]", "3.8", "ng/mL", "normal", "03/08/2026"],
            ["TSH [LOINC: 3016-3]", "1.8", "mIU/L", "normal", "03/08/2026"],
            ["ALT [LOINC: 1742-6]", "42", "U/L", "H", "03/08/2026"],
            ["AST [LOINC: 1920-8]", "38", "U/L", "normal", "03/08/2026"],
            ["CBC WBC [LOINC: 6690-2]", "8.1", "10*3/uL", "normal", "03/08/2026"],
            ["Hemoglobin [LOINC: 718-7]", "14.8", "g/dL", "normal", "03/08/2026"],
            ["Uric Acid [LOINC: 3084-1]", "7.8", "mg/dL", "H", "03/08/2026"],
        ]
    ))

    xml += _section("11369-6", "Immunizations", _table(
        ["Vaccine", "Date", "Status"],
        [
            ["Influenza vaccine 2025-2026", "10/20/2025", "completed"],
            ["COVID-19 Vaccine 2024-2025 (Moderna)", "10/01/2024", "completed"],
            ["Tdap (Boostrix)", "03/15/2018", "completed"],
            ["Hepatitis B series", "05/10/2010", "completed"],
            ["Pneumococcal PCV20", "09/15/2025", "completed"],
        ]
    ))

    xml += _social_section(
        "Tobacco: Former smoker (quit 05/2021, 1.5 ppd x 20 yrs = 30 pk yrs). "
        "Alcohol: Social drinker (2-3 beers on weekends). "
        "Employment: IT Project Manager. Sedentary job. "
        "Marital Status: Married. "
        "Exercise: Minimal, walks dog 15 minutes daily. "
        "Diet: High carb, frequent fast food. Discussed dietary counseling. "
        "CPAP: Uses nightly, compliance 85% per data download."
    )

    xml += _insurance_section([
        ["Cigna", "Commercial PPO", "CIG-882341", "GRP-TECHCO-200"],
    ])

    xml += _notes_section([
        {
            "date": "03/12/2026", "provider": "Cory Denton, FNP",
            "type": "Progress Note", "location": PRACTICE_NAME,
            "text": "CC: Follow-up metabolic syndrome, HTN, lipids\nHPI: 55yo male with metabolic syndrome. Reports good CPAP compliance but admits poor diet. Weight stable at 245 lbs. Denies CP, SOB, edema.\nBP still elevated 148/92 despite losartan 100mg. LDL 155 despite rosuvastatin 20mg.\nAssessment:\n# HTN (I10): Uncontrolled. Add chlorthalidone 12.5mg daily. Goal <130/80.\n# Hyperlipidemia (E78.2): LDL at goal? No — target <100 given ASCVD risk. Increase rosuvastatin to 40mg.\n# Prediabetes (R73.03): A1c 6.2%. Continue metformin 500mg BID. Weight loss counseling.\n# OSA (G47.33): CPAP compliant. Reorder supplies.\n# Lung Cancer Screening: Former smoker 30 pack-years, quit <15 yrs ago. Age 55. ELIGIBLE for annual LDCT. Ordered.\n# BPH (N40.0): New AUA score 12 (moderate). Start tamsulosin 0.4mg QHS if symptomatic.\nPlan: Add chlorthalidone, increase rosuvastatin. LDCT chest ordered. BMP in 2 weeks. Colonoscopy overdue — ordered. RTC 3 months."
        },
        {
            "date": "09/15/2025", "provider": "Cory Denton, FNP",
            "type": "Annual Wellness Visit", "location": PRACTICE_NAME,
            "text": "ANNUAL WELLNESS VISIT — G0439\n55yo male here for AWV.\nPreventive:\n- Colorectal: Last colonoscopy 2016. Due 2026 — Schedule.\n- Lung Cancer: LDCT eligible (30py, quit 4yr ago). Not yet done.\n- PSA: 3.8 ng/mL — discussed shared decision making. Will recheck annually.\n- Depression: PHQ-9 = 4 (minimal).\n- Diabetes screen: A1c 6.2%.\n- Hepatitis C: Screened negative 2023.\n- HIV: Screened negative 2020.\nVaccines: Flu today. PCV20 given (age 55 with DM risk).\nFall risk: Low. Functional status: Independent.\nAdvance Directive: Not completed — discussed. Patient will consider."
        },
        {
            "date": "06/10/2025", "provider": "Gretchen Lockard, MD",
            "type": "Progress Note", "location": PRACTICE_NAME,
            "text": "CC: New onset nocturia, weak stream\nHPI: 54yo male reports waking 2-3x/night to urinate for 2 months. Weak stream, hesitancy. No hematuria, no dysuria.\nDRE: Mildly enlarged, smooth, no nodules.\nAssessment: BPH (N40.0). AUA score 12.\nPlan: Watchful waiting for now. Recheck PSA (was 3.2 last year). Lifestyle modifications. Return if worsening."
        },
    ])

    xml += _footer()
    return xml


def patient_62602():
    """Kristy Test, 42F — Post-hospital discharge, TCM candidate."""
    xml = _header(
        62602, "Kristy", "Anderson", "F", "Female", "19830101",
        "1234 Testing Street", "Midlothian", "VA", "23112",
        "(804)-555-4565", race_code="2106-3", race_display="White",
        marital_code="S", marital_display="Never Married"
    )

    xml += _section("48765-2", "Allergies and Adverse Reactions", _table(
        ["Substance", "Reaction", "Severity", "Status"],
        [
            ["Penicillin [RxNorm: 7980]", "Hives, urticaria", "moderate", "active"],
            ["Latex", "Contact dermatitis", "mild", "active"],
            ["Ibuprofen [RxNorm: 5640]", "GI bleeding", "severe", "active"],
        ]
    ))

    xml += _section("10160-0", "Medications", _table(
        ["Medication", "Generic Name", "Instructions", "Dosage", "Start Date", "Status"],
        [
            ["albuterol 90 mcg inhaler [RxNorm: 245314]", "albuterol", "Inhale 2 puffs every 4-6 hours as needed", "90 mcg", "05/10/2020", "active"],
            ["fluticasone 250 mcg inhaler [RxNorm: 896188]", "fluticasone", "Inhale 1 puff twice daily", "250 mcg", "05/10/2020", "active"],
            ["escitalopram 10 mg tablet [RxNorm: 351249]", "escitalopram", "Take 1 tablet by mouth daily", "10 mg", "09/01/2024", "active"],
            ["ferrous sulfate 325 mg tablet [RxNorm: 310323]", "ferrous sulfate", "Take 1 tablet by mouth twice daily with food", "325 mg", "01/15/2026", "active"],
            ["azithromycin 250 mg tablet [RxNorm: 141961]", "azithromycin", "Take 2 tablets day 1, then 1 tablet daily x 4 days", "250 mg", "03/08/2026", "active"],
            ["montelukast 10 mg tablet [RxNorm: 352027]", "montelukast", "Take 1 tablet by mouth at bedtime", "10 mg", "06/20/2023", "active"],
            ["loratadine 10 mg tablet [RxNorm: 311368]", "loratadine", "Take 1 tablet by mouth daily", "10 mg", "04/01/2024", "active"],
            ["spironolactone 25 mg tablet [RxNorm: 198224]", "spironolactone", "Take 1 tablet by mouth daily", "25 mg", "09/01/2024", "inactive"],
        ]
    ))

    xml += _section("11450-4", "Problems", _table(
        ["Problem", "Problem Status", "Date Started", "Date Resolved"],
        [
            ["Moderate persistent asthma [ICD10: J45.40]", "active", "03/15/2018", ""],
            ["Generalized anxiety disorder [ICD10: F41.1]", "active", "09/01/2024", ""],
            ["Iron deficiency anemia [ICD10: D50.9]", "active", "01/15/2026", ""],
            ["Community-acquired pneumonia [ICD10: J18.9]", "active", "03/05/2026", ""],
            ["Allergic rhinitis [ICD10: J30.9]", "active", "04/01/2024", ""],
            ["Vitamin B12 deficiency [ICD10: E53.8]", "active", "01/15/2026", ""],
            ["Acute bronchitis [ICD10: J20.9]", "resolved", "11/10/2025", "11/24/2025"],
        ]
    ))

    xml += _section("8716-3", "Vital Signs", _table(
        ["Encounter", "Height (in)", "Weight (lb)", "BMI (kg/m2)", "BP Sys (mmHg)", "BP Dias (mmHg)", "Heart Rate (/min)", "O2 % BldC Oximetry", "Body Temperature", "Respiratory Rate (/min)"],
        [
            ["03/15/2026", "65", "140", "23.3", "118", "72", "88", "96", "99.2", "20"],
            ["03/08/2026", "65", "138", "23.0", "112", "70", "92", "94", "100.8", "22"],
            ["01/15/2026", "65", "142", "23.6", "116", "74", "76", "98", "98.4", "16"],
        ]
    ))

    xml += _section("30954-2", "Lab Results", _table(
        ["Test Name", "Result", "Units", "Flag", "Date"],
        [
            ["CBC WBC [LOINC: 6690-2]", "12.4", "10*3/uL", "H", "03/08/2026"],
            ["Hemoglobin [LOINC: 718-7]", "10.2", "g/dL", "L", "03/08/2026"],
            ["Hematocrit [LOINC: 4544-3]", "31.5", "%", "L", "03/08/2026"],
            ["MCV [LOINC: 787-2]", "72", "fL", "L", "03/08/2026"],
            ["Platelet Count [LOINC: 777-3]", "310", "10*3/uL", "normal", "03/08/2026"],
            ["Iron [LOINC: 2498-4]", "28", "ug/dL", "L", "01/15/2026"],
            ["Ferritin [LOINC: 2276-4]", "8", "ng/mL", "L", "01/15/2026"],
            ["TIBC [LOINC: 2500-7]", "450", "ug/dL", "H", "01/15/2026"],
            ["CRP [LOINC: 1988-5]", "4.8", "mg/dL", "H", "03/08/2026"],
            ["Procalcitonin [LOINC: 33959-8]", "0.15", "ng/mL", "normal", "03/08/2026"],
            ["BMP Glucose [LOINC: 2345-7]", "95", "mg/dL", "normal", "03/08/2026"],
            ["BMP Creatinine [LOINC: 2160-0]", "0.8", "mg/dL", "normal", "03/08/2026"],
            ["Vitamin B12 [LOINC: 2132-9]", "180", "pg/mL", "L", "01/15/2026"],
            ["Chest X-ray", "Bilateral lower lobe infiltrates", "--", "abnormal", "03/08/2026"],
        ]
    ))

    xml += _section("11369-6", "Immunizations", _table(
        ["Vaccine", "Date", "Status"],
        [
            ["Influenza vaccine 2025-2026", "10/05/2025", "completed"],
            ["COVID-19 Vaccine 2024-2025 (Pfizer)", "10/01/2024", "completed"],
            ["Tdap (Adacel)", "07/15/2019", "completed"],
            ["Hepatitis B series (3 doses)", "06/01/2010", "completed"],
            ["HPV series (Gardasil 9) complete", "08/15/2010", "completed"],
        ]
    ))

    xml += _social_section(
        "Tobacco: Never smoker. "
        "Alcohol: Occasional wine (1-2 glasses/week). "
        "Illicit Drug Use: No. "
        "Employment: Graphic designer, remote work. "
        "Marital Status: Single. "
        "Lives alone with 2 cats. "
        "Exercise: Yoga 2x/week, hiking on weekends when feeling well."
    )

    xml += _insurance_section([
        ["Aetna", "Commercial HMO", "AET-771234", "GRP-DESIGN-50"],
    ])

    xml += _notes_section([
        {
            "date": "03/15/2026", "provider": "Cory Denton, FNP",
            "type": "TCM Follow-up", "location": PRACTICE_NAME,
            "text": "TCM FOLLOW-UP — 99496 (High complexity)\nCC: Post-discharge follow-up, day 7 after hospital discharge\nHPI: 42yo female discharged 03/08/2026 from Bon Secours St. Francis for community-acquired pneumonia. Completed 3 days IV ceftriaxone in hospital, transitioned to azithromycin 250mg x 5 days (day 5 today). Reports improved cough, less fatigue. Still some mild dyspnea with exertion. No fever in 4 days.\nHospital Discharge Summary reviewed. Discharge diagnoses: CAP, asthma exacerbation, iron deficiency anemia.\nMedication Reconciliation: Verified all discharge meds. Added azithromycin to med list. Confirmed ongoing ferrous sulfate for anemia.\nVitals: T 99.2, BP 118/72, HR 88, RR 20, O2 96% RA (improved from 94% at discharge).\nLungs: Diminished bases bilaterally, scattered rhonchi clearing with cough. No wheezing today.\nAssessment:\n# CAP (J18.9): Improving on oral antibiotics. Complete course.\n# Asthma (J45.40): Stable. Continue maintenance inhaler.\n# Iron deficiency anemia (D50.9): Continue iron supplementation. Recheck CBC in 4 weeks. Consider IV iron if Hgb not improving.\n# B12 deficiency (E53.8): Start B12 1000mcg PO daily.\nPlan: Complete azithromycin. Recheck CXR in 4-6 weeks. CBC in 4 weeks. Follow-up 2 weeks for clinical reassessment. Call if worsening SOB, fever, or hemoptysis."
        },
        {
            "date": "01/15/2026", "provider": "Patricia Lavinus, NP",
            "type": "Progress Note", "location": PRACTICE_NAME,
            "text": "CC: Fatigue x 6 weeks, hair loss, dizziness\nHPI: 42yo female reports progressive fatigue, hair thinning, lightheadedness when standing. Menstrual cycles regular but heavy (7 days, changing pad every 2 hours).\nLabs: Hgb 10.2 (low), Ferritin 8 (very low), MCV 72 (microcytic). B12 180 (borderline low).\nAssessment:\n# Iron deficiency anemia (D50.9): Likely from menorrhagia.\n# B12 deficiency (E53.8): Borderline, supplement.\nPlan: Start ferrous sulfate 325mg BID with vitamin C. B12 supplementation. GYN referral for menorrhagia evaluation. Recheck CBC in 8 weeks."
        },
        {
            "date": "09/20/2025", "provider": "Cory Denton, FNP",
            "type": "Annual Wellness Visit", "location": PRACTICE_NAME,
            "text": "ANNUAL WELLNESS VISIT — G0439\n42yo female here for AWV.\nPreventive Review:\n- Cervical cancer: Pap + HPV co-test last 2023. Next due 2028.\n- Breast cancer: Mammogram last 2024. Due 2025 — Schedule.\n- Colorectal: Not yet due (starts age 45). Due in 3 years.\n- Depression: PHQ-9 = 7 (mild). Started escitalopram.\n- Anxiety: GAD-7 = 9 (mild-moderate). Counseling referral offered.\nVaccines: Flu given today. All series complete.\nFunctional: Independent, active.\nAdvance Directive: Not completed."
        },
    ])

    xml += _footer()
    return xml


def patient_62815():
    """Test (demo) patient, 45F — DM, hyperlipidemia, COVID follow-up."""
    xml = _header(
        62815, "DEMO", "TESTPATIENT", "F", "Female", "19801001",
        "9999 Sample Blvd", "Midlothian", "VA", "23112",
        "(804)-320-3999", race_code="2106-3", race_display="White",
        marital_code="M", marital_display="Married"
    )

    xml += _section("48765-2", "Allergies and Adverse Reactions", _table(
        ["Substance", "Reaction", "Severity", "Status"],
        [
            ["Penicillins [RxNorm: 7980]", "Anaphylaxis", "severe", "active"],
            ["Sulfa drugs [RxNorm: 10171]", "Rash", "moderate", "active"],
            ["Morphine [RxNorm: 7052]", "Respiratory depression", "severe", "active"],
        ]
    ))

    xml += _section("10160-0", "Medications", _table(
        ["Medication", "Generic Name", "Instructions", "Dosage", "Start Date", "Status"],
        [
            ["metformin 1000 mg tablet [RxNorm: 861004]", "metformin", "Take 1 tablet by mouth twice daily", "1000 mg", "06/01/2020", "active"],
            ["atorvastatin 40 mg tablet [RxNorm: 259255]", "atorvastatin", "Take 1 tablet by mouth at bedtime", "40 mg", "06/01/2020", "active"],
            ["lisinopril 20 mg tablet [RxNorm: 314076]", "lisinopril", "Take 1 tablet by mouth daily", "20 mg", "08/15/2019", "active"],
            ["metoprolol succinate 50 mg tablet [RxNorm: 866924]", "metoprolol", "Take 1 tablet by mouth daily", "50 mg", "03/10/2022", "active"],
            ["albuterol 90 mcg inhaler [RxNorm: 245314]", "albuterol", "Inhale 2 puffs as needed for wheezing", "90 mcg", "01/05/2026", "active"],
            ["vitamin D3 2000 IU tablet [RxNorm: 392263]", "cholecalciferol", "Take 1 tablet daily", "2000 IU", "09/01/2023", "active"],
            ["glipizide 5 mg tablet [RxNorm: 310489]", "glipizide", "Take 1 tablet by mouth before breakfast", "5 mg", "01/15/2024", "active"],
            ["gabapentin 300 mg capsule [RxNorm: 310429]", "gabapentin", "Take 1 capsule by mouth three times daily", "300 mg", "05/01/2023", "active"],
        ]
    ))

    xml += _section("11450-4", "Problems", _table(
        ["Problem", "Problem Status", "Date Started", "Date Resolved"],
        [
            ["Type 2 diabetes mellitus without complications [ICD10: E11.9]", "active", "06/01/2020", ""],
            ["Hyperlipidemia due to type 2 diabetes mellitus [ICD10: E11.69]", "active", "06/01/2020", ""],
            ["Essential hypertension [ICD10: I10]", "active", "08/15/2019", ""],
            ["Chronic low back pain [ICD10: M54.5]", "active", "05/01/2023", ""],
            ["Peripheral neuropathy [ICD10: G62.9]", "active", "05/01/2023", ""],
            ["Vitamin D deficiency [ICD10: E55.9]", "active", "09/01/2023", ""],
            ["Obesity BMI 30-34.9 [ICD10: E66.01]", "active", "06/01/2020", ""],
            ["COVID-19 [ICD10: U07.1]", "resolved", "01/02/2026", "01/15/2026"],
            ["Acute sinusitis [ICD10: J01.90]", "resolved", "01/02/2026", "01/15/2026"],
            ["Wheeze [ICD10: R06.2]", "resolved", "01/02/2026", "01/15/2026"],
        ]
    ))

    xml += _section("8716-3", "Vital Signs", _table(
        ["Encounter", "Height (in)", "Weight (lb)", "BMI (kg/m2)", "BP Sys (mmHg)", "BP Dias (mmHg)", "Heart Rate (/min)", "O2 % BldC Oximetry", "Body Temperature", "Respiratory Rate (/min)"],
        [
            ["03/15/2026", "64", "198", "34.0", "136", "84", "78", "97", "98.4", "16"],
            ["01/05/2026", "64", "195", "33.5", "142", "86", "90", "93", "100.2", "20"],
            ["09/01/2025", "64", "200", "34.3", "138", "82", "76", "98", "98.6", "14"],
        ]
    ))

    xml += _section("30954-2", "Lab Results", _table(
        ["Test Name", "Result", "Units", "Flag", "Date"],
        [
            ["Hemoglobin A1c [LOINC: 4548-4]", "8.2", "%", "H", "03/10/2026"],
            ["Hemoglobin A1c [LOINC: 4548-4]", "7.9", "%", "H", "09/01/2025"],
            ["Glucose fasting [LOINC: 1558-6]", "156", "mg/dL", "H", "03/10/2026"],
            ["Total Cholesterol [LOINC: 2093-3]", "210", "mg/dL", "H", "03/10/2026"],
            ["LDL Cholesterol [LOINC: 2089-1]", "128", "mg/dL", "H", "03/10/2026"],
            ["HDL Cholesterol [LOINC: 2085-9]", "42", "mg/dL", "L", "03/10/2026"],
            ["Triglycerides [LOINC: 2571-8]", "200", "mg/dL", "H", "03/10/2026"],
            ["Creatinine [LOINC: 2160-0]", "1.0", "mg/dL", "normal", "03/10/2026"],
            ["eGFR [LOINC: 48642-3]", "72", "mL/min/1.73m2", "normal", "03/10/2026"],
            ["Potassium [LOINC: 2823-3]", "4.2", "mmol/L", "normal", "03/10/2026"],
            ["Vitamin D 25-OH [LOINC: 1989-3]", "28", "ng/mL", "L", "03/10/2026"],
            ["Urine Microalbumin [LOINC: 14957-5]", "45", "mg/L", "H", "03/10/2026"],
            ["CBC WBC [LOINC: 6690-2]", "7.5", "10*3/uL", "normal", "03/10/2026"],
            ["Hemoglobin [LOINC: 718-7]", "13.5", "g/dL", "normal", "03/10/2026"],
        ]
    ))

    xml += _section("11369-6", "Immunizations", _table(
        ["Vaccine", "Date", "Status"],
        [
            ["Influenza vaccine 2025-2026", "10/10/2025", "completed"],
            ["COVID-19 Vaccine 2024-2025 (Pfizer)", "09/20/2024", "completed"],
            ["Tdap (Boostrix)", "05/15/2018", "completed"],
            ["Hepatitis B series (3 doses)", "03/01/2005", "completed"],
            ["Shingrix (Zoster) Dose 1", "09/01/2025", "completed"],
        ]
    ))

    xml += _social_section(
        "Tobacco: Never smoker. "
        "Alcohol: No. "
        "Employment: Homemaker. "
        "Marital Status: Married. "
        "Exercise: Walks 30 minutes daily. "
        "Diet: Trying to follow diabetic diet, struggles with carb control."
    )

    xml += _insurance_section([
        ["Anthem Blue Cross", "Commercial PPO", "ANT-662815", "GRP-FAM-300"],
    ])

    xml += _notes_section([
        {
            "date": "03/15/2026", "provider": "Cory Denton, FNP",
            "type": "Progress Note", "location": PRACTICE_NAME,
            "text": "CC: Follow-up DM, HTN. Post-COVID recovery check.\nHPI: 45yo female here for chronic disease management. Recovered from COVID in January. Lingering fatigue but improving. No more cough or SOB. Asthma back to baseline.\nA1c 8.2% — worsening. Admits poor dietary compliance during illness. Weight 198 (down from 200).\nAssessment:\n# DM2 (E11.9): A1c worsening. Increase glipizide to 10mg. Consider adding GLP-1 agonist. Diabetes educator referral.\n# HTN (I10): BP 136/84 — improved. Continue current regimen.\n# Hyperlipidemia (E11.69): LDL 128. Continue atorvastatin 40mg.\n# Peripheral neuropathy (G62.9): Gabapentin helping. No dose change.\n# Obesity (E66.01): Discussed weight management. GLP-1 agonist would address both DM and weight.\n# Vitamin D deficiency: Recheck in 3 months.\nPlan: Increase glipizide. Diabetes education referral. A1c in 3 months. Consider semaglutide at next visit. Shingrix dose 2 due (dose 1 was 09/2025). Mammogram overdue — ordered."
        },
        {
            "date": "01/05/2026", "provider": "Gretchen Lockard, MD",
            "type": "Acute Visit", "location": PRACTICE_NAME,
            "text": "CC: Cough, sore throat, sinus pressure x 3 days\nHPI: 45yo with DM presents with URI symptoms. Husband also ill. Yellow mucus, slight sinus pressure, sore throat, cough productive. No SOB at rest but mild with exertion.\nCOVID rapid: POSITIVE. Flu rapid: NEGATIVE.\nPE: Fatigued but nontoxic. Bilateral TM normal. Nasal turbinates edematous. Pharynx no erythema. Shotty cervical adenopathy. Lungs: occasional expiratory wheeze bilaterally.\nAssessment:\n# COVID-19 (U07.1): Start Paxlovid — stop atorvastatin during treatment (interaction).\n# Wheeze (R06.2): Start albuterol inhaler QID.\n# Acute sinusitis (J01.90): Likely viral/COVID-related.\n# Hyperlipidemia (E11.69): Patient immunocompromised (DM) — aggressive treatment warranted.\nPlan: Paxlovid x 5 days. Hold statin. Albuterol PRN. Rest, fluids. Call if worsening SOB. Follow-up 10 days."
        },
        {
            "date": "09/01/2025", "provider": "Cory Denton, FNP",
            "type": "Annual Wellness Visit", "location": PRACTICE_NAME,
            "text": "ANNUAL WELLNESS VISIT — G0439\n45yo female here for AWV.\nPreventive:\n- Cervical cancer: Pap + HPV co-test 2023. Next 2028.\n- Breast cancer: Mammogram 2024. Due 2025 — order.\n- Colorectal: Approaching age 45. Discussed options — will do FIT test.\n- Depression: PHQ-9 = 5 (minimal).\n- Diabetes eye exam: Last 2024. Due 2025 — scheduled with ophthalmology.\n- Foot exam: Monofilament normal bilateral. Pedal pulses 2+.\n- Shingrix: Age 45, started dose 1 today.\n- Osteoporosis: Not yet due.\nVaccines: Flu, Shingrix dose 1 given.\nAdvance Directive: Completed."
        },
    ])

    xml += _footer()
    return xml


def patient_62816():
    """Tyler Johnson, 8M — Pediatric well-child, ADHD, asthma."""
    xml = _header(
        62816, "Tyler", "Johnson", "M", "Male", "20180315",
        "13911 St Francis Blvd", "Midlothian", "VA", "23114",
        "(804)-555-4567", race_code="2106-3", race_display="White",
        marital_code="S", marital_display="Never Married",
        language="en"
    )

    xml += _section("48765-2", "Allergies and Adverse Reactions", _table(
        ["Substance", "Reaction", "Severity", "Status"],
        [
            ["Amoxicillin [RxNorm: 723]", "Rash (maculopapular)", "mild", "active"],
            ["Peanuts", "Hives, lip swelling", "moderate", "active"],
        ]
    ))

    xml += _section("10160-0", "Medications", _table(
        ["Medication", "Generic Name", "Instructions", "Dosage", "Start Date", "Status"],
        [
            ["methylphenidate 10 mg tablet [RxNorm: 1091166]", "methylphenidate", "Take 1 tablet by mouth every morning", "10 mg", "09/01/2025", "active"],
            ["albuterol 90 mcg inhaler [RxNorm: 245314]", "albuterol", "Inhale 2 puffs every 4-6 hours as needed for wheezing", "90 mcg", "03/15/2023", "active"],
            ["fluticasone 44 mcg inhaler [RxNorm: 896006]", "fluticasone", "Inhale 1 puff twice daily", "44 mcg", "03/15/2023", "active"],
            ["cetirizine 5 mg chewable tablet [RxNorm: 1014677]", "cetirizine", "Take 1 tablet by mouth daily", "5 mg", "04/01/2025", "active"],
            ["triamcinolone 0.1% cream [RxNorm: 106259]", "triamcinolone", "Apply thin layer to affected areas twice daily", "0.1%", "06/10/2024", "active"],
            ["EpiPen Jr 0.15 mg auto-injector [RxNorm: 310146]", "epinephrine", "Inject IM into outer thigh for anaphylaxis", "0.15 mg", "01/15/2025", "active"],
        ]
    ))

    xml += _section("11450-4", "Problems", _table(
        ["Problem", "Problem Status", "Date Started"],
        [
            ["Mild intermittent asthma [ICD10: J45.20]", "active", "03/15/2023"],
            ["Attention deficit hyperactivity disorder combined [ICD10: F90.2]", "active", "09/01/2025"],
            ["Atopic dermatitis eczema [ICD10: L20.9]", "active", "06/10/2024"],
            ["Peanut allergy [ICD10: Z91.010]", "active", "01/15/2025"],
            ["Obesity BMI 95th percentile [ICD10: E66.01]", "active", "03/10/2026"],
        ]
    ))

    xml += _section("8716-3", "Vital Signs", _table(
        ["Encounter", "Height (in)", "Weight (lb)", "BMI (kg/m2)", "BP Sys (mmHg)", "BP Dias (mmHg)", "Heart Rate (/min)", "O2 % BldC Oximetry", "Body Temperature", "Respiratory Rate (/min)"],
        [
            ["03/10/2026", "50", "72", "20.3", "102", "66", "88", "99", "98.6", "20"],
            ["09/15/2025", "49", "68", "19.8", "100", "64", "84", "99", "98.4", "18"],
        ]
    ))

    xml += _section("30954-2", "Lab Results", _table(
        ["Test Name", "Result", "Units", "Flag", "Date"],
        [
            ["CBC WBC [LOINC: 6690-2]", "8.5", "10*3/uL", "normal", "03/05/2026"],
            ["Hemoglobin [LOINC: 718-7]", "12.8", "g/dL", "normal", "03/05/2026"],
            ["Lead Level [LOINC: 5671-3]", "2.1", "ug/dL", "normal", "03/05/2026"],
            ["Glucose random [LOINC: 2345-7]", "92", "mg/dL", "normal", "03/05/2026"],
            ["Lipid Panel Total Cholesterol [LOINC: 2093-3]", "175", "mg/dL", "normal", "03/05/2026"],
            ["Lipid Panel LDL [LOINC: 2089-1]", "105", "mg/dL", "normal", "03/05/2026"],
        ]
    ))

    xml += _section("11369-6", "Immunizations", _table(
        ["Vaccine", "Date", "Status"],
        [
            ["DTaP dose 5", "03/15/2023", "completed"],
            ["IPV dose 4", "03/15/2023", "completed"],
            ["MMR dose 2", "03/15/2023", "completed"],
            ["Varicella dose 2", "03/15/2023", "completed"],
            ["Influenza vaccine 2025-2026", "10/01/2025", "completed"],
            ["Hepatitis A dose 2", "09/15/2020", "completed"],
            ["Hepatitis B dose 3", "09/15/2018", "completed"],
            ["COVID-19 Vaccine 2024-2025 (Pfizer Peds)", "10/15/2024", "completed"],
        ]
    ))

    xml += _social_section(
        "Lives with: Both parents and older sister (age 12). "
        "Grade: 2nd grade, Robious Elementary. "
        "Academic performance: Improved since starting ADHD medication. "
        "Physical activity: Soccer team, swimming lessons. "
        "Screen time: Limited to 1 hour/day per parents. "
        "Diet: Picky eater. Avoids all nuts. Carries EpiPen to school. "
        "Development: Meeting milestones. "
        "Safety: Car booster seat, bike helmet, swim supervision."
    )

    xml += _insurance_section([
        ["Anthem HealthKeepers", "Medicaid Managed Care", "MCD-880921", "N/A"],
    ])

    xml += _notes_section([
        {
            "date": "03/10/2026", "provider": "Cory Denton, FNP",
            "type": "Well-Child Visit", "location": PRACTICE_NAME,
            "text": "WELL-CHILD VISIT — 8 years old\nCC: Annual checkup, ADHD medication follow-up\nHPI: 8yo male here with mother for annual well-child visit. Overall doing well. ADHD medication (Ritalin 10mg) working — teacher reports improved focus and completion of assignments. No behavioral issues. Appetite slightly reduced (common ADHD med side effect). Asthma well-controlled — using inhaler only 1x/month with exercise.\nGrowth: Height 50in (50th %ile), Weight 72 lbs (85th %ile), BMI 20.3 (95th %ile — obese range).\nDevelopment: Reading at grade level. Social skills appropriate. No behavioral concerns.\nPE: HEENT normal. Heart RRR no murmur. Lungs clear. Abdomen soft. Tanner stage 1. Neurological normal.\nVision: 20/25 OU. Hearing: Passed bilateral.\nAssessment:\n# ADHD (F90.2): Well controlled on methylphenidate 10mg. Appetite monitoring.\n# Asthma (J45.20): Well controlled. Continue fluticasone maintenance, albuterol PRN.\n# Eczema (L20.9): Mild flare on arms. Continue triamcinolone cream.\n# Obesity (E66.01): BMI 95th %ile. Discussed nutrition, activity. Goal: no weight gain as height increases.\n# Peanut allergy (Z91.010): EpiPen not expired. Renewed prescription.\nImmunizations: All UTD. HPV series starts at age 11. Tdap booster at age 11.\nPlan: Recheck in 6 months for weight, ADHD. Annual labs. Continue current meds."
        },
        {
            "date": "09/15/2025", "provider": "Patricia Lavinus, NP",
            "type": "ADHD Evaluation", "location": PRACTICE_NAME,
            "text": "CC: Academic difficulty, inattention, hyperactivity\nHPI: 7yo male referred by teacher for ADHD evaluation. Parent reports difficulty sitting still, not completing homework, easily distracted. Symptoms present for >12 months in >2 settings (home and school).\nVanderbilt Assessment Scales: Parent score 38 (>75th %ile inattentive + hyperactive). Teacher score 42.\nAssessment: ADHD Combined type (F90.2).\nPlan: Start methylphenidate 5mg QAM. Increase to 10mg in 2 weeks if tolerated. Weight/BP monitoring. Behavioral strategies handout. Follow-up 4 weeks."
        },
    ])

    xml += _footer()
    return xml


def patient_63039():
    """Sarah Mitchell, 46F — Chronic pain, mental health, obesity, care gaps."""
    xml = _header(
        63039, "Sarah", "Mitchell", "F", "Female", "19800101",
        "7825 Irongate Dr", "Chesterfield", "VA", "23832",
        "(804)-555-9182", race_code="2106-3", race_display="White",
        marital_code="D", marital_display="Divorced"
    )

    xml += _section("48765-2", "Allergies and Adverse Reactions", _table(
        ["Substance", "Reaction", "Severity", "Status"],
        [
            ["NSAIDs (ibuprofen, naproxen) [RxNorm: 5640]", "GI bleeding", "severe", "active"],
            ["Tramadol [RxNorm: 10689]", "Seizures", "severe", "active"],
            ["Amitriptyline [RxNorm: 704]", "Cardiac arrhythmia", "severe", "active"],
            ["Latex", "Hives", "mild", "active"],
        ]
    ))

    xml += _section("10160-0", "Medications", _table(
        ["Medication", "Generic Name", "Instructions", "Dosage", "Start Date", "Status"],
        [
            ["duloxetine 60 mg capsule [RxNorm: 596926]", "duloxetine", "Take 1 capsule by mouth daily", "60 mg", "05/01/2023", "active"],
            ["gabapentin 300 mg capsule [RxNorm: 310429]", "gabapentin", "Take 1 capsule by mouth three times daily", "300 mg", "05/01/2023", "active"],
            ["cyclobenzaprine 10 mg tablet [RxNorm: 197364]", "cyclobenzaprine", "Take 1 tablet by mouth at bedtime", "10 mg", "08/15/2023", "active"],
            ["sumatriptan 50 mg tablet [RxNorm: 313176]", "sumatriptan", "Take 1 tablet at onset of migraine, may repeat x1 in 2 hours", "50 mg", "11/01/2022", "active"],
            ["omeprazole 20 mg capsule [RxNorm: 198053]", "omeprazole", "Take 1 capsule by mouth daily before breakfast", "20 mg", "05/01/2023", "active"],
            ["topiramate 50 mg tablet [RxNorm: 199283]", "topiramate", "Take 1 tablet by mouth at bedtime for migraine prevention", "50 mg", "03/10/2024", "active"],
            ["methocarbamol 750 mg tablet [RxNorm: 197945]", "methocarbamol", "Take 1 tablet by mouth three times daily as needed", "750 mg", "01/15/2024", "active"],
            ["vitamin D3 5000 IU capsule [RxNorm: 392263]", "cholecalciferol", "Take 1 capsule by mouth daily", "5000 IU", "06/01/2025", "active"],
            ["acetaminophen 500 mg tablet [RxNorm: 198440]", "acetaminophen", "Take 2 tablets by mouth every 6 hours as needed for pain (max 3000mg/day)", "500 mg", "05/01/2023", "active"],
        ]
    ))

    xml += _section("11450-4", "Problems", _table(
        ["Problem", "Problem Status", "Date Started"],
        [
            ["Chronic low back pain [ICD10: M54.5]", "active", "01/15/2020"],
            ["Major depressive disorder recurrent moderate [ICD10: F33.1]", "active", "03/20/2019"],
            ["Morbid obesity BMI 35-39.9 [ICD10: E66.01]", "active", "01/15/2020"],
            ["Fibromyalgia [ICD10: M79.7]", "active", "08/15/2023"],
            ["Gastroesophageal reflux disease [ICD10: K21.0]", "active", "05/01/2023"],
            ["Migraine without aura [ICD10: G43.009]", "active", "11/01/2022"],
            ["Prediabetes [ICD10: R73.03]", "active", "06/01/2025"],
            ["Vitamin D deficiency [ICD10: E55.9]", "active", "06/01/2025"],
            ["Generalized anxiety disorder [ICD10: F41.1]", "active", "03/20/2019"],
            ["Cervicalgia [ICD10: M54.2]", "active", "01/15/2020"],
            ["Iron deficiency without anemia [ICD10: E61.1]", "active", "06/01/2025"],
        ]
    ))

    xml += _section("8716-3", "Vital Signs", _table(
        ["Encounter", "Height (in)", "Weight (lb)", "BMI (kg/m2)", "BP Sys (mmHg)", "BP Dias (mmHg)", "Heart Rate (/min)", "O2 % BldC Oximetry", "Body Temperature", "Respiratory Rate (/min)"],
        [
            ["03/08/2026", "64", "210", "36.0", "132", "84", "78", "98", "98.4", "16"],
            ["12/01/2025", "64", "215", "36.9", "134", "86", "80", "98", "98.2", "16"],
            ["06/01/2025", "64", "218", "37.4", "138", "88", "82", "98", "98.6", "14"],
        ]
    ))

    xml += _section("30954-2", "Lab Results", _table(
        ["Test Name", "Result", "Units", "Flag", "Date"],
        [
            ["Hemoglobin A1c [LOINC: 4548-4]", "5.8", "%", "normal", "03/01/2026"],
            ["Glucose fasting [LOINC: 1558-6]", "108", "mg/dL", "H", "03/01/2026"],
            ["Total Cholesterol [LOINC: 2093-3]", "215", "mg/dL", "H", "03/01/2026"],
            ["LDL Cholesterol [LOINC: 2089-1]", "132", "mg/dL", "H", "03/01/2026"],
            ["HDL Cholesterol [LOINC: 2085-9]", "52", "mg/dL", "normal", "03/01/2026"],
            ["Triglycerides [LOINC: 2571-8]", "155", "mg/dL", "H", "03/01/2026"],
            ["TSH [LOINC: 3016-3]", "4.8", "mIU/L", "normal", "03/01/2026"],
            ["Vitamin D 25-OH [LOINC: 1989-3]", "18", "ng/mL", "L", "03/01/2026"],
            ["ESR [LOINC: 4537-7]", "35", "mm/hr", "H", "03/01/2026"],
            ["CRP [LOINC: 1988-5]", "2.8", "mg/dL", "H", "03/01/2026"],
            ["Creatinine [LOINC: 2160-0]", "0.9", "mg/dL", "normal", "03/01/2026"],
            ["CBC WBC [LOINC: 6690-2]", "6.9", "10*3/uL", "normal", "03/01/2026"],
            ["Hemoglobin [LOINC: 718-7]", "12.5", "g/dL", "normal", "03/01/2026"],
            ["Ferritin [LOINC: 2276-4]", "15", "ng/mL", "L", "03/01/2026"],
            ["Iron [LOINC: 2498-4]", "45", "ug/dL", "L", "03/01/2026"],
            ["ANA [LOINC: 8061-4]", "Negative", "--", "normal", "06/01/2025"],
            ["Rheumatoid Factor [LOINC: 11572-5]", "Negative", "--", "normal", "06/01/2025"],
        ]
    ))

    xml += _section("11369-6", "Immunizations", _table(
        ["Vaccine", "Date", "Status"],
        [
            ["Influenza vaccine 2024-2025", "10/20/2024", "completed"],
            ["COVID-19 Vaccine 2023-2024 (Moderna)", "10/01/2023", "completed"],
            ["Tdap (Adacel)", "06/10/2015", "completed"],
        ]
    ))

    xml += _social_section(
        "Tobacco: Never smoker. "
        "Alcohol: None (avoids due to medications). "
        "Illicit Drug Use: None. "
        "Employment: Disability since 2021 (chronic pain). Previously retail manager. "
        "Marital Status: Divorced (2018). "
        "Children: 2 children (ages 14, 11) — shared custody. "
        "Exercise: Limited due to pain. Works with PT 1x/week. Pool therapy when able. "
        "Mental Health: Sees therapist biweekly. Support group monthly. "
        "Diet: Trying Mediterranean diet for inflammation. Struggles with emotional eating."
    )

    xml += _insurance_section([
        ["Virginia Medicaid Fee-for-Service", "Medicaid", "MCD-630390", "N/A"],
    ])

    xml += _notes_section([
        {
            "date": "03/08/2026", "provider": "Cory Denton, FNP",
            "type": "Progress Note", "location": PRACTICE_NAME,
            "text": "CC: Chronic pain follow-up, depression check, weight management\nHPI: 46yo female with fibromyalgia, chronic back pain, depression, obesity. Reports pain levels 6/10 average (improved from 8/10). Duloxetine helping mood and pain. Gabapentin TID providing some relief. Migraines reduced to 2x/month from weekly since adding topiramate. Weight down 5 lbs (210 from 215).\nPHQ-9: 12 (moderate depression — improved from 16). GAD-7: 10 (moderate anxiety).\nPain Assessment: Widespread musculoskeletal pain. Worst in lower back and shoulders. Morning stiffness 45 minutes. Poor sleep quality.\nPE: Tender points positive 14/18 (fibromyalgia). Lumbar ROM reduced. No radiculopathy. Straight leg raise negative bilaterally.\nAssessment:\n# Fibromyalgia (M79.7): Improving. Continue duloxetine + gabapentin.\n# Chronic low back pain (M54.5): Stable. Continue PT. No opioids.\n# Depression (F33.1): PHQ-9 improving. Continue duloxetine 60mg. Therapy ongoing.\n# Obesity (E66.01): Lost 5 lbs. Continue dietary counseling. Consider GLP-1 agonist.\n# Prediabetes (R73.03): A1c 5.8% — borderline. Weight loss is key intervention.\n# Vitamin D deficiency: Level 18 — increase to 5000 IU daily. Recheck 3 months.\n# Migraine (G43.009): Improved on topiramate. Continue.\n\nCare Gaps: Flu vaccine overdue. COVID booster overdue. Tdap overdue (last 2015 — 11 years). Mammogram not done since 2023. Cervical screen due.\n\nPlan: Continue all meds. Order mammogram. Schedule Pap. Administer flu and COVID vaccines today. Tdap at next visit. Labs in 3 months. PT continue. Follow-up 3 months."
        },
        {
            "date": "12/01/2025", "provider": "Cory Denton, FNP",
            "type": "Progress Note", "location": PRACTICE_NAME,
            "text": "CC: Worsening depression, pain flare\nHPI: Reports increased stress with holiday season and custody issues. PHQ-9 = 16 (moderately severe). Pain 8/10. Not sleeping.\nAssessment: Depression worsening, pain flare.\nPlan: Increase duloxetine to 60mg (from 30mg). Add cyclobenzaprine 10mg QHS for muscle spasm. Urgent therapy appointment scheduled. If not improving in 2 weeks, consider psychiatric referral. Safety plan reviewed — denies SI/HI."
        },
        {
            "date": "06/01/2025", "provider": "Cory Denton, FNP",
            "type": "Progress Note", "location": PRACTICE_NAME,
            "text": "CC: New complaint of fatigue, weight gain, joint pain\nHPI: 45yo female with chronic pain reports new onset fatigue worse than usual, weight up 10 lbs in 3 months, diffuse joint pain and morning stiffness. Concerned about autoimmune disease.\nLabs ordered: CBC, CMP, TSH, ESR, CRP, ANA, RF, Vitamin D, Iron studies, A1c\nResults: TSH 4.8 (upper normal), Vitamin D 18 (low), Ferritin 15 (low), ESR 35 (elevated), CRP 2.8 (elevated), ANA negative, RF negative, A1c 5.8% (prediabetes).\nAssessment:\n# Prediabetes (R73.03): New diagnosis. Lifestyle modification.\n# Vitamin D deficiency (E55.9): Start supplementation.\n# Iron deficiency without anemia (E61.1): Low ferritin. Start iron.\n# Elevated inflammatory markers: No autoimmune etiology identified. Likely related to obesity/fibromyalgia.\nPlan: Start Vitamin D 5000 IU, ferrous sulfate 325mg daily. Dietary counseling. Recheck labs 3 months."
        },
    ])

    xml += _footer()
    return xml


# ============================================================
# MAIN — Generate all files
# ============================================================
PATIENTS = {
    31306: patient_31306,
    43461: patient_43461,
    45534: patient_45534,
    62602: patient_62602,
    62815: patient_62815,
    62816: patient_62816,
    63039: patient_63039,
}

if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for pid, gen_func in PATIENTS.items():
        xml_content = gen_func()
        timestamp = "20260317_142334"
        fname = f"ClinicalSummary_PatientId_{pid}_{timestamp}.xml"
        fpath = os.path.join(OUTPUT_DIR, fname)

        # Remove old files for this patient
        for existing in os.listdir(OUTPUT_DIR):
            if existing.startswith(f"ClinicalSummary_PatientId_{pid}_"):
                os.remove(os.path.join(OUTPUT_DIR, existing))
                print(f"  Removed old: {existing}")

        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        print(f"Generated: {fname}")

    print(f"\nAll {len(PATIENTS)} test patient XMLs generated in:\n  {OUTPUT_DIR}")
