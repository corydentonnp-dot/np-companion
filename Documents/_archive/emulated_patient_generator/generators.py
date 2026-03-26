"""
generators.py — All randomization and generation logic.
Returns structured dicts that cda_builder.py converts to XML.
"""

import random
import uuid
from datetime import date, datetime, timedelta
from data import (
    RELIGIONS, LANGUAGES, GENERATIONAL_SUFFIXES, RACES, MARITAL_STATUSES,
    BIOLOGICAL_SEX, GENDER_IDENTITY, SEXUAL_ORIENTATION,
    PAYERS, ALLERGIES, ALL_DIAGNOSES, MEDICATIONS, LAB_TESTS, LAB_PANELS,
    VACCINES, PROCEDURES,
    SMOKING_STATUSES, ALCOHOL_USE, DRUG_USE, EXERCISE, OCCUPATIONS,
    FAMILY_HISTORY_CONDITIONS, FAMILY_MEMBERS,
    STREET_NAMES, CITIES_STATES,
    FIRST_NAMES_MALE, FIRST_NAMES_FEMALE, LAST_NAMES,
    DIAGNOSES,
)

# SOCIAL_HISTORY_OPTIONS not defined in data.py — use empty dict as fallback
try:
    from data import SOCIAL_HISTORY_OPTIONS
except ImportError:
    SOCIAL_HISTORY_OPTIONS = {}


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def rnd_date(start_year, end_year):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def rnd_date_before(reference: date, min_days=30, max_days=3650):
    """Return a random date before `reference`."""
    delta = random.randint(min_days, max_days)
    return reference - timedelta(days=delta)


def rnd_date_after(reference: date, min_days=1, max_days=365):
    """Return a random date after `reference`."""
    delta = random.randint(min_days, max_days)
    return reference + timedelta(days=delta)


def fmt(d: date) -> str:
    return d.strftime("%Y%m%d")


def fmt_display(d: date) -> str:
    return d.strftime("%m/%d/%Y")


def phone_number():
    area = random.choice([
        "804", "757", "540", "703", "571", "434", "276", "336", "919", "980",
        "410", "240", "443", "301", "202", "404", "770", "678", "615", "901",
        "305", "813", "407", "904", "312", "773", "317", "216", "614"
    ])
    return f"tel:+1({area})-{random.randint(200,999):03d}-{random.randint(1000,9999):04d}"


def phone_display(phone_uri: str) -> str:
    return phone_uri.replace("tel:+1", "").strip()


def build_mrn():
    return f"T{random.randint(10000, 99999)}"


def new_uuid():
    return str(uuid.uuid4())


def pick(lst):
    return random.choice(lst)


def picks(lst, n):
    return random.sample(lst, min(n, len(lst)))


# ---------------------------------------------------------------------------
# COMPLEXITY SETTINGS
# ---------------------------------------------------------------------------
COMPLEXITY = {
    "Simple": {
        "num_diagnoses": (1, 3), "num_meds": (0, 3), "num_allergies": (0, 2),
        "num_lab_panels": (1, 2), "num_encounters": (1, 3),
        "num_immunizations": (2, 5), "num_procedures": (0, 2),
        "num_family_hx": (1, 3), "notes_detail": "brief",
    },
    "Moderate": {
        "num_diagnoses": (3, 7), "num_meds": (3, 8), "num_allergies": (1, 3),
        "num_lab_panels": (3, 5), "num_encounters": (4, 10),
        "num_immunizations": (4, 8), "num_procedures": (2, 5),
        "num_family_hx": (3, 6), "notes_detail": "moderate",
    },
    "Complex": {
        "num_diagnoses": (7, 18), "num_meds": (8, 20), "num_allergies": (2, 5),
        "num_lab_panels": (5, 12), "num_encounters": (10, 30),
        "num_immunizations": (5, 12), "num_procedures": (4, 12),
        "num_family_hx": (5, 10), "notes_detail": "full",
    },
}


def rnd_range(complexity_key, field):
    lo, hi = COMPLEXITY[complexity_key][field]
    return random.randint(lo, hi)


# ---------------------------------------------------------------------------
# AGE-APPROPRIATE FILTERING
# ---------------------------------------------------------------------------
def age_appropriate_diagnoses(age, sex, all_dx):
    filtered = []
    for dx in all_dx:
        cat = dx["category"]
        icd = dx["icd10"]
        # Exclude pediatric dx for adults
        if age >= 18 and cat == "Pediatric / Developmental":
            if "Well child" in dx["display"] or "RSV" in dx["display"]:
                continue
        # Exclude geriatric-specific for young patients
        if age < 60 and cat == "Geriatric":
            continue
        # Exclude OB/GYN for males
        if sex == "M" and cat == "Obstetrics / Gynecology":
            continue
        # Exclude prostate for females
        if sex == "F" and "Prostate" in dx["display"]:
            continue
        # Exclude pediatric vaccines / conditions for adults
        if age >= 18 and icd in ("Z00.121",):
            continue
        # Age-gate some conditions
        if age < 40 and cat == "Geriatric":
            continue
        if age < 50 and "Alzheimer" in dx["display"]:
            continue
        if age < 10 and cat in ("Oncology", "Cardiovascular"):
            continue
        filtered.append(dx)
    return filtered


def age_appropriate_meds(age, sex, diagnoses_list, all_meds):
    """Return medications plausible for this patient's diagnoses."""
    diag_names = " ".join([d["display"].lower() for d in diagnoses_list])
    relevant = []
    always_possible = []
    for med in all_meds:
        name = med["name"].lower()
        generic = med["generic"].lower()
        # Exclude clearly inapplicable
        if sex == "M" and any(x in name for x in ["tamoxifen", "anastrozole", "ibrance", "pap"]):
            continue
        if sex == "F" and "testosterone" in name:
            continue
        if age < 18 and any(x in name for x in ["metformin", "warfarin", "statin"]):
            continue
        if age >= 18 and "suspension" in name and age >= 18:
            continue
        # Age-gate controlled substances
        if age < 18 and any(x in generic for x in ["amphetamine", "opioid", "oxycodone",
                                                     "hydrocodone", "morphine"]):
            continue
        always_possible.append(med)
    return always_possible


def age_appropriate_labs(age, sex, diagnoses_list, lab_panels_dict):
    """Return lab panels plausible for this patient."""
    diag_names = " ".join([d["display"].lower() for d in diagnoses_list])
    panels = []
    # Always offer basic panels
    base = ["CBC", "BMP", "Lipid Panel", "Thyroid"]
    for p in base:
        panels.append(p)
    if "diabetes" in diag_names or "glucose" in diag_names:
        panels.append("Diabetes Monitoring")
    if any(x in diag_names for x in ["hepatitis", "liver", "cirrhosis", "alcohol"]):
        panels.append("LFT")
        panels.append("Hepatitis Panel")
    if any(x in diag_names for x in ["anemia", "iron", "fatigue", "b12"]):
        panels.append("Iron Studies")
        panels.append("Vitamins")
    if any(x in diag_names for x in ["lupus", "rheumatoid", "autoimmune"]):
        panels.append("Autoimmune Panel")
        panels.append("Inflammatory Markers")
    if any(x in diag_names for x in ["heart failure", "cardiac", "bnp"]):
        panels.append("Cardiac Markers")
    if any(x in diag_names for x in ["clot", "dvt", "embolism", "coagulation", "warfarin"]):
        panels.append("Coagulation")
    if any(x in diag_names for x in ["hiv", "aids"]):
        panels.append("HIV Monitoring")
    if age >= 50 and sex == "M":
        panels.append("Tumor Markers – Male")
    if age >= 21 and sex == "F":
        panels.append("Tumor Markers – Female")
    if age >= 15:
        panels.append("STI Panel")
    if any(x in diag_names for x in ["lithium", "bipolar"]):
        panels.append("Drug Levels – Lithium")
    if any(x in diag_names for x in ["seizure", "epilepsy", "phenytoin"]):
        panels.append("Drug Levels – Phenytoin")
    if any(x in diag_names for x in ["sepsis", "infection", "procalcitonin"]):
        panels.append("Sepsis Markers")
    if sex == "F":
        panels.append("Sex Hormones – Female")
    else:
        panels.append("Sex Hormones – Male")
    # Deduplicate
    seen = set()
    result = []
    for p in panels:
        if p not in seen and p in lab_panels_dict:
            seen.add(p)
            result.append(p)
    return result


def age_appropriate_vaccines(age, sex):
    from data import VACCINES
    result = []
    for v in VACCINES:
        name = v["name"].lower()
        # Infant vaccines only for infants
        if age >= 2 and any(x in name for x in ["dtap", "rotavirus", "hib", "pcv13"]):
            result.append(v)
            continue
        if age < 1 and any(x in name for x in ["dtap", "rotavirus", "hib", "pcv13"]):
            result.append(v)
            continue
        # Shingrix 50+
        if "shingrix" in name and age < 50:
            continue
        # HPV up to 26 (or 45)
        if "hpv" in name and age > 45:
            continue
        # Meningococcal for teens/college
        if "menacwy" in name and age > 25:
            continue
        # RSV 60+
        if "rsvvaccine" in name.replace(" ","") and age < 60:
            continue
        # Pneumococcal 65+
        if ("pneumococcal conjugate pcv15" in name or "ppsv23" in name) and age < 65:
            continue
        result.append(v)
    return result


# ---------------------------------------------------------------------------
# GENERATE PATIENT DEMOGRAPHICS
# ---------------------------------------------------------------------------
def generate_demographics(overrides: dict = None) -> dict:
    """
    Generate a full demographics dict. `overrides` can contain any keys
    to fix (e.g., from the GUI form).
    """
    o = overrides or {}

    # Sex
    sex_tuple = o.get("sex_tuple") or pick(BIOLOGICAL_SEX)
    sex_code, sex_display = sex_tuple if isinstance(sex_tuple, tuple) else sex_tuple

    # Name
    first = o.get("first_name") or (
        pick(FIRST_NAMES_MALE) if sex_code == "M" else pick(FIRST_NAMES_FEMALE)
    )
    last = o.get("last_name") or pick(LAST_NAMES)
    # Middle name (optional)
    use_middle = random.random() < 0.6
    if use_middle:
        middle = (pick(FIRST_NAMES_MALE) if sex_code == "M"
                  else pick(FIRST_NAMES_FEMALE))[0] + "."
    else:
        middle = None
    # Suffix
    suffix = o.get("name_suffix") or ""

    # DOB / Age
    if "dob" in o and o["dob"]:
        dob = o["dob"] if isinstance(o["dob"], date) else (
            datetime.strptime(o["dob"], "%Y-%m-%d").date()
        )
    elif "age" in o and o["age"]:
        target_age = int(o["age"])
        dob = date.today() - timedelta(days=target_age * 365 + random.randint(0, 364))
    else:
        target_age = random.randint(0, 101)
        dob = date.today() - timedelta(days=target_age * 365 + random.randint(0, 364))
    age = (date.today() - dob).days // 365

    # MRN
    mrn = o.get("mrn") or build_mrn()
    if not mrn.startswith("T"):
        mrn = "T" + mrn

    # Address
    street_num = random.randint(100, 9999)
    street = pick(STREET_NAMES)
    city_tuple = pick(CITIES_STATES)
    city, state, zip_code = (
        o.get("city", city_tuple[0]),
        o.get("state", city_tuple[1]),
        o.get("zip", city_tuple[2]),
    )
    address = f"{street_num} {street}"

    # Phones
    home_phone = o.get("home_phone") or phone_number()
    cell_phone = o.get("cell_phone") or phone_number()
    work_phone = phone_number() if random.random() < 0.4 else None
    alt_phone = phone_number() if random.random() < 0.2 else None

    # Demographics
    race_tuple = pick(RACES)
    marital_tuple = pick(MARITAL_STATUSES) if age >= 18 else ("Single", "S")
    religion = pick(RELIGIONS)
    lang_name = o.get("language") or pick(list(LANGUAGES.keys()))
    lang_code = LANGUAGES.get(lang_name, "en")
    race_display, race_code = race_tuple

    # Gender identity (optional, ~70% of patients have it recorded)
    gender_id = None
    if random.random() < 0.7 and age >= 13:
        gender_id = pick(GENDER_IDENTITY)

    # Sexual orientation (optional, ~40%)
    sexual_orient = None
    if random.random() < 0.4 and age >= 18:
        sexual_orient = pick(SEXUAL_ORIENTATION)

    return {
        "mrn": mrn,
        "first": first,
        "middle": middle,
        "last": last,
        "suffix": suffix,
        "dob": dob,
        "age": age,
        "sex_code": sex_code,
        "sex_display": sex_display if isinstance(sex_display, str) else sex_tuple[1],
        "gender_identity": gender_id,
        "sexual_orientation": sexual_orient,
        "address": address,
        "city": city,
        "state": state,
        "zip": zip_code,
        "home_phone": home_phone,
        "cell_phone": cell_phone,
        "work_phone": work_phone,
        "alt_phone": alt_phone,
        "race_display": race_display,
        "race_code": race_code,
        "marital_display": marital_tuple[0] if isinstance(marital_tuple, tuple) else marital_tuple,
        "marital_code": marital_tuple[1] if isinstance(marital_tuple, tuple) else "UNK",
        "religion": religion,
        "language": lang_name,
        "lang_code": lang_code,
        "doc_uuid": new_uuid(),
        "set_uuid": new_uuid(),
        "encounter_uuid": new_uuid(),
    }


# ---------------------------------------------------------------------------
# GENERATE SOCIAL HISTORY
# ---------------------------------------------------------------------------
def generate_social_history(demo: dict) -> dict:
    age = demo["age"]
    sex_code = demo["sex_code"]
    smoking = pick(SMOKING_STATUSES)
    alcohol = pick(ALCOHOL_USE)
    drugs = pick(DRUG_USE)
    exercise = pick(EXERCISE)
    occupation = pick(OCCUPATIONS)
    if age < 16:
        occupation = "Student"
    elif age > 70 and random.random() < 0.7:
        occupation = "Retired"
    # Diet
    diet_options = [
        "No specific dietary restrictions reported",
        "Low-sodium diet for hypertension", "Diabetic diet — carbohydrate counting",
        "Vegetarian diet", "Vegan diet", "Low-fat diet",
        "Gluten-free diet (celiac)", "Low-potassium diet (CKD)",
        "High-protein diet / bariatric", "Mediterranean diet",
    ]
    diet = pick(diet_options)
    return {
        "smoking": smoking,
        "alcohol": alcohol,
        "drugs": drugs,
        "exercise": exercise,
        "occupation": occupation,
        "diet": diet,
    }


# ---------------------------------------------------------------------------
# GENERATE FAMILY HISTORY
# ---------------------------------------------------------------------------
def generate_family_history(n: int) -> list:
    """Returns list of {member, condition, age_at_onset, deceased}."""
    result = []
    members_used = []
    for _ in range(n):
        member = pick(FAMILY_MEMBERS)
        while member in members_used and len(members_used) < len(FAMILY_MEMBERS):
            member = pick(FAMILY_MEMBERS)
        members_used.append(member)
        condition = pick(FAMILY_HISTORY_CONDITIONS)
        age_onset = random.randint(40, 80) if "cancer" in condition.lower() else random.randint(35, 75)
        deceased = random.random() < 0.3
        deceased_age = age_onset + random.randint(0, 20) if deceased else None
        result.append({
            "member": member,
            "condition": condition,
            "age_onset": age_onset,
            "deceased": deceased,
            "deceased_age": deceased_age,
        })
    return result


# ---------------------------------------------------------------------------
# GENERATE ALLERGIES
# ---------------------------------------------------------------------------
def generate_allergies(n: int) -> list:
    selected = picks(ALLERGIES, n)
    result = []
    for a in selected:
        reaction = pick(a["reactions"])
        severity_tuple = pick(a["severities"])
        status = "Active" if random.random() < 0.8 else "Inactive"
        onset = rnd_date(2000, 2025)
        result.append({
            "name": a["name"],
            "rxnorm": a["rxnorm"],
            "snomed": a["snomed"],
            "reaction": reaction,
            "severity": severity_tuple[0],
            "severity_code": severity_tuple[1],
            "status": status,
            "onset": onset,
            "uuid": new_uuid(),
            "obs_uuid": new_uuid(),
            "react_uuid": new_uuid(),
        })
    return result


# ---------------------------------------------------------------------------
# GENERATE PROBLEMS
# ---------------------------------------------------------------------------
def generate_problems(demo: dict, n: int) -> list:
    age = demo["age"]
    sex_code = demo["sex_code"]
    pool = age_appropriate_diagnoses(age, sex_code, ALL_DIAGNOSES)
    selected = picks(pool, n)
    result = []
    today = date.today()
    for dx in selected:
        # Onset date relative to age
        if age > 5:
            earliest = today - timedelta(days=age * 365 - 365)
            latest = today - timedelta(days=30)
            onset = earliest + timedelta(days=random.randint(0, (latest - earliest).days))
        else:
            onset = today - timedelta(days=random.randint(30, age * 365 + 1))
        status = "Active" if random.random() < 0.8 else "Inactive"
        resolved = None
        if status == "Inactive":
            resolved = onset + timedelta(days=random.randint(30, 730))
        result.append({
            "display": dx["display"],
            "icd10": dx["icd10"],
            "snomed": dx["snomed"],
            "category": dx["category"],
            "onset": onset,
            "status": status,
            "resolved": resolved,
            "act_uuid": new_uuid(),
            "obs_uuid": new_uuid(),
        })
    return result


# ---------------------------------------------------------------------------
# GENERATE MEDICATIONS
# ---------------------------------------------------------------------------
def generate_medications(demo: dict, n: int, problems: list) -> list:
    age = demo["age"]
    sex_code = demo["sex_code"]
    pool = age_appropriate_meds(age, sex_code, problems, MEDICATIONS)
    random.shuffle(pool)
    selected = pool[:n]
    result = []
    today = date.today()
    for med in selected:
        start_offset = random.randint(30, 365 * 5)
        start = today - timedelta(days=start_offset)
        active = random.random() < 0.75
        end = None
        if not active:
            end = start + timedelta(days=random.randint(7, 365))
        result.append({
            "name": med["name"],
            "rxnorm": med["rxnorm"],
            "generic": med["generic"],
            "sig": med["sig"],
            "dose": med["dose"],
            "unit": med["unit"],
            "qty": med["qty"],
            "rf": med["rf"],
            "start": start,
            "end": end,
            "active": active,
            "uuid": new_uuid(),
            "product_uuid": new_uuid(),
        })
    return result


# ---------------------------------------------------------------------------
# GENERATE LAB RESULTS
# ---------------------------------------------------------------------------
def _generate_lab_value(test_key: str, scenario: str = "normal") -> tuple:
    """
    Returns (value, interpretation_code, flag_text)
    scenario: "normal" | "abnormal_low" | "abnormal_high" | "critical_low" | "critical_high"
    """
    t = LAB_TESTS.get(test_key)
    if not t:
        return ("UNK", "N", "Normal")

    lo, hi = t["normal"]

    if scenario == "normal":
        if lo == hi == 0.0:
            val = 0.0  # e.g., negative result
        else:
            val = round(random.uniform(lo, hi), 2)
        interp = "N"
        flag = "Normal"

    elif scenario == "abnormal_low":
        crit = t.get("critical_low")
        floor = (crit * 1.1) if crit else (lo * 0.5)
        val = round(random.uniform(floor, lo * 0.98), 2)
        interp = "L"
        flag = "Low"

    elif scenario == "abnormal_high":
        crit = t.get("critical_high")
        ceiling = (crit * 0.9) if crit else (hi * 2)
        val = round(random.uniform(hi * 1.02, ceiling), 2)
        interp = "H"
        flag = "High"

    elif scenario == "critical_low":
        crit = t.get("critical_low")
        if crit is None:
            return _generate_lab_value(test_key, "abnormal_low")
        val = round(random.uniform(crit * 0.5, crit * 0.9), 2)
        interp = "LL"
        flag = "Critical Low"

    elif scenario == "critical_high":
        crit = t.get("critical_high")
        if crit is None:
            return _generate_lab_value(test_key, "abnormal_high")
        val = round(random.uniform(crit * 1.05, crit * 2.0), 2)
        interp = "HH"
        flag = "Critical High"

    else:
        val = round(random.uniform(lo, hi), 2)
        interp = "N"
        flag = "Normal"

    return (str(val), interp, flag)


def generate_lab_results(demo: dict, num_panels: int, problems: list) -> list:
    """Returns list of lab result sets, each representing one ordered panel."""
    from data import LAB_PANELS
    age = demo["age"]
    sex_code = demo["sex_code"]
    avail_panels = age_appropriate_labs(age, sex_code, problems, LAB_PANELS)
    selected_panels = picks(avail_panels, num_panels)

    # Distribution weights: 60% normal, 25% abnormal, 10% critical
    def pick_scenario():
        r = random.random()
        if r < 0.60:
            return "normal"
        elif r < 0.80:
            return "abnormal_high"
        elif r < 0.92:
            return "abnormal_low"
        elif r < 0.96:
            return "critical_high"
        else:
            return "critical_low"

    result_sets = []
    today = date.today()
    for panel_name in selected_panels:
        test_keys = LAB_PANELS.get(panel_name, [])
        panel_date = today - timedelta(days=random.randint(1, 365 * 3))
        results = []
        for key in test_keys:
            if key not in LAB_TESTS:
                continue
            test = LAB_TESTS[key]
            scenario = pick_scenario()
            val, interp, flag = _generate_lab_value(key, scenario)
            results.append({
                "key": key,
                "loinc": test["loinc"],
                "name": test["name"],
                "value": val,
                "unit": test["unit"],
                "normal_low": test["normal"][0],
                "normal_high": test["normal"][1],
                "interpretation": interp,
                "flag": flag,
                "obs_uuid": new_uuid(),
            })
        result_sets.append({
            "panel_name": panel_name,
            "panel_date": panel_date,
            "organizer_uuid": new_uuid(),
            "results": results,
        })
    return result_sets


# ---------------------------------------------------------------------------
# GENERATE IMMUNIZATIONS
# ---------------------------------------------------------------------------
def generate_immunizations(demo: dict, n: int) -> list:
    age = demo["age"]
    sex_code = demo["sex_code"]
    pool = age_appropriate_vaccines(age, sex_code)
    selected = picks(pool, n)
    result = []
    today = date.today()
    for v in selected:
        admin_date = today - timedelta(days=random.randint(30, 365 * 10))
        if admin_date.year < 1990:
            admin_date = date(random.randint(1990, 2024), random.randint(1, 12), random.randint(1, 28))
        result.append({
            "name": v["name"],
            "cvx": v["cvx"],
            "admin_date": admin_date,
            "uuid": new_uuid(),
        })
    return result


# ---------------------------------------------------------------------------
# GENERATE PROCEDURES
# ---------------------------------------------------------------------------
def generate_procedures(demo: dict, n: int, problems: list) -> list:
    from data import PROCEDURES as PROC_LIST
    diag_names = " ".join([d["display"].lower() for d in problems])
    pool = list(PROC_LIST)
    # Weight toward relevant procedures
    selected = picks(pool, n)
    result = []
    today = date.today()
    for proc in selected:
        proc_date = today - timedelta(days=random.randint(14, 365 * 5))
        result.append({
            "name": proc["name"],
            "cpt": proc["cpt"],
            "date": proc_date,
            "uuid": new_uuid(),
        })
    return result


# ---------------------------------------------------------------------------
# GENERATE VITAL SIGNS HISTORY
# ---------------------------------------------------------------------------
def generate_vitals(demo: dict, num_encounters: int) -> list:
    age = demo["age"]
    sex_code = demo["sex_code"]
    vitals_history = []
    today = date.today()
    for i in range(num_encounters):
        enc_date = today - timedelta(days=i * random.randint(30, 120))
        # Height (stable after ~20)
        if sex_code == "M":
            height_cm = round(random.gauss(177, 7), 1)  # ~5'10"
        else:
            height_cm = round(random.gauss(163, 6), 1)  # ~5'4"
        # Weight varies
        if age < 2:
            weight_kg = round(random.uniform(3, 13), 1)
        elif age < 10:
            weight_kg = round(random.uniform(15, 40), 1)
        elif age < 18:
            weight_kg = round(random.uniform(45, 80), 1)
        else:
            weight_kg = round(random.gauss(85, 20), 1)
        bmi = round(weight_kg / (height_cm / 100) ** 2, 1) if height_cm > 0 else None
        # BP
        systolic = random.randint(110, 165)
        diastolic = random.randint(65, 100)
        hr = random.randint(60, 105)
        spo2 = random.randint(94, 100)
        temp_c = round(random.gauss(37.0, 0.4), 1)
        rr = random.randint(14, 22)
        vitals_history.append({
            "date": enc_date,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "bmi": bmi,
            "systolic": systolic,
            "diastolic": diastolic,
            "hr": hr,
            "spo2": spo2,
            "temp_c": temp_c,
            "rr": rr,
            "organizer_uuid": new_uuid(),
        })
    return vitals_history


# ---------------------------------------------------------------------------
# GENERATE INSURANCE
# ---------------------------------------------------------------------------
def generate_insurance(demo: dict) -> list:
    age = demo["age"]
    payers = []
    # Age-based logic
    if age >= 65:
        payers.append(pick([p for p in PAYERS if "Medicare" in p["name"]]))
        if random.random() < 0.4:
            payers.append(pick([p for p in PAYERS if p["name"] not in
                               ["Medicare Part B", "Medicare Advantage (Humana)"]]))
    elif age < 18:
        payers.append(pick([p for p in PAYERS if p["name"] in
                           ["CHIP (Children's Health Insurance)", "Medicaid (Virginia)",
                            "Anthem Blue Cross Blue Shield", "UnitedHealthcare"]]))
    elif random.random() < 0.1:
        payers.append({"name": "Self-Pay / Uninsured", "type": "Self-Pay"})
    else:
        payers.append(pick(PAYERS))
        if random.random() < 0.2:
            secondary = pick(PAYERS)
            if secondary["name"] != payers[0]["name"]:
                payers.append(secondary)

    result = []
    for p in payers:
        member_id = f"MBR{random.randint(100000000, 999999999)}"
        group_num = f"GRP-{random.randint(1000, 9999)}-{random.randint(100, 999)}"
        eff_date = date.today() - timedelta(days=random.randint(90, 1460))
        result.append({
            "name": p["name"],
            "type": p["type"],
            "member_id": member_id,
            "group_num": group_num,
            "eff_date": eff_date,
        })
    return result


# ---------------------------------------------------------------------------
# GENERATE CARE TEAM
# ---------------------------------------------------------------------------
PROVIDERS = [
    {"first": "Cory", "last": "Denton", "suffix": "FNP", "npi": "1891645123", "role": "PCP"},
    {"first": "Gretchen", "last": "Lockard", "suffix": "MD", "npi": "1023069796", "role": "Family Medicine"},
    {"first": "Raymond G.", "last": "Decker", "suffix": "MD", "npi": "1972594828", "role": "Family Medicine"},
    {"first": "Donald", "last": "Yeatts", "suffix": "MD", "npi": "1114959392", "role": "Family Medicine"},
    {"first": "Ashley", "last": "Morsberger", "suffix": "FNP", "npi": "1457184004", "role": "Family Medicine"},
    {"first": "Ambrish M.", "last": "Patel", "suffix": "PA-C", "npi": "1710110457", "role": "Family Medicine"},
    {"first": "Robert M.", "last": "Buchanan", "suffix": "DO", "npi": "1235540824", "role": "Family Medicine"},
    {"first": "Kelley", "last": "Flowers-Frazier", "suffix": "PA-C", "npi": "1922716042", "role": "Family Medicine"},
]


def generate_care_team(n: int = 2) -> list:
    selected = picks(PROVIDERS, min(n, len(PROVIDERS)))
    result = []
    for p in selected:
        start = date.today() - timedelta(days=random.randint(90, 1825))
        result.append({
            "first": p["first"],
            "last": p["last"],
            "suffix": p["suffix"],
            "npi": p["npi"],
            "role": p["role"],
            "start": start,
            "uuid": new_uuid(),
            "act_uuid": new_uuid(),
        })
    return result


# ---------------------------------------------------------------------------
# GENERATE PROGRESS NOTES
# ---------------------------------------------------------------------------
_BRIEF_HPI_TEMPLATES = [
    "Patient presents for {reason}. Reports {duration} history of {symptom}. Denies fever, chills, or shortness of breath.",
    "Here for {reason}. Symptoms have been {duration}. {symptom} noted by patient. No acute distress at this time.",
    "Established patient presenting with {reason}. {symptom} for {duration}. Review of systems otherwise negative.",
]
_MODERATE_HPI_ADD = [
    " Associated with {assoc}.",
    " Aggravated by {aggravator}, relieved by {reliever}.",
    " Patient rates pain {pain_scale}/10 at its worst.",
]
REASONS = ["follow-up", "medication refill", "annual wellness visit", "acute illness", "chronic disease management"]
SYMPTOMS = ["intermittent headaches", "fatigue", "shortness of breath on exertion",
            "joint stiffness", "chest tightness", "abdominal discomfort", "dizziness", "palpitations",
            "lower back pain", "ankle swelling", "excessive thirst", "blurred vision"]
DURATIONS = ["2-week", "one-month", "several-week", "3-month", "chronic", "acute-onset"]
ASSOC = ["nausea", "diaphoresis", "light-headedness", "decreased appetite"]
AGGRAVATORS = ["exertion", "stress", "lying flat", "certain foods", "cold weather"]
RELIEVERS = ["rest", "NSAIDs", "positional change", "warm compress", "breathing exercises"]


def generate_progress_note(demo: dict, problems: list, meds: list,
                             allergies: list, social_hx: dict,
                             family_hx: list, vitals: dict,
                             detail: str = "moderate") -> dict:
    age = demo["age"]
    sex_word = "He" if demo["sex_code"] == "M" else "She"
    reason = pick(REASONS)
    symptom = pick(SYMPTOMS)
    duration = pick(DURATIONS)

    # Chief complaint
    cc = f'"{reason.capitalize()}" — {symptom} × {duration}'

    # HPI
    hpi_lines = [
        f"Patient is a {age}-year-old {demo['sex_display'].lower()} presenting for {reason}.",
        f"{sex_word} reports a {duration} history of {symptom}.",
    ]
    if detail in ("moderate", "full"):
        assoc = pick(ASSOC)
        aggrav = pick(AGGRAVATORS)
        reliever = pick(RELIEVERS)
        pain = random.randint(2, 9)
        hpi_lines += [
            f"Associated with {assoc}.",
            f"Symptoms aggravated by {aggrav} and relieved by {reliever}.",
            f"Patient rates discomfort {pain}/10 at its worst.",
        ]
    if detail == "full":
        hpi_lines += [
            "Review of systems: No recent fever. No chest pain at rest. No significant weight loss.",
            "Medication compliance reviewed — patient reports adherence to all current medications.",
        ]

    # PMH
    pmh_items = [f"{d['display']} ({d['icd10']})" for d in problems]

    # Family Hx
    fhx_lines = [f"{f['member']}: {f['condition']}" +
                 (f" (onset age {f['age_onset']})" if f.get("age_onset") else "") +
                 (" [deceased]" if f.get("deceased") else "")
                 for f in family_hx]

    # Social Hx
    social_lines = [
        f"[Tobacco: {social_hx['smoking'][0]}]",
        f"Alcohol: {social_hx['alcohol']}",
        f"Illicit drug use: {social_hx['drugs']}",
        f"Occupation: {social_hx['occupation']}",
        f"Exercise: {social_hx['exercise']}",
        f"Diet: {social_hx['diet']}",
    ]

    # Physical Exam
    exam_lines = [
        f"- General: {pick(['well-appearing, no acute distress', 'mildly fatigued, alert and oriented', 'comfortable at rest', 'appears stated age, in no distress'])}",
        f"- Vitals: BP {vitals['systolic']}/{vitals['diastolic']} mmHg, HR {vitals['hr']} bpm, "
        f"RR {vitals['rr']}/min, SpO2 {vitals['spo2']}%, Temp {vitals['temp_c']}°C",
    ]
    if detail in ("moderate", "full"):
        exam_lines += [
            f"- HEENT: {pick(['normocephalic/atraumatic, PERRL, oropharynx clear', 'anicteric, TMs intact bilaterally, no oral lesions', 'mucous membranes moist'])}",
            f"- Neck: {pick(['supple, no LAD, no JVD', 'no thyromegaly, no lymphadenopathy'])}",
            f"- CV: {pick(['regular rate and rhythm, no murmurs', 'RRR, S1/S2 present, no S3/S4 appreciated'])}",
            f"- Resp: {pick(['clear to auscultation bilaterally, no wheezes or crackles', 'diminished breath sounds at bases bilaterally', 'bilateral expiratory wheezes'])}",
            f"- Abdomen: {pick(['soft, non-tender, non-distended, normoactive bowel sounds', 'mild tenderness to palpation in epigastric region', 'no hepatosplenomegaly'])}",
            f"- Extremities: {pick(['no edema, no cyanosis, pulses intact', '2+ pitting edema bilateral ankles', 'warm and well-perfused'])}",
            f"- Neuro: {pick(['alert and oriented x4, no focal deficits', 'cranial nerves II-XII grossly intact'])}",
        ]

    # A&P
    ap_lines = []
    for dx in problems[:min(3, len(problems))]:
        note_options = [
            f"Continue current management. Monitor closely.",
            f"Adjust therapy as needed. Labs ordered.",
            f"Patient counseled on lifestyle modifications.",
            f"Referral placed to appropriate specialist.",
            f"Medication regimen reviewed and optimized.",
        ]
        ap_lines.append(f"# {dx['display']} ({dx['icd10']}): {pick(note_options)}")

    return {
        "cc": cc,
        "hpi": "\n".join(hpi_lines),
        "pmh": "; ".join(pmh_items) if pmh_items else "None reported",
        "family_hx": "\n".join(fhx_lines) if fhx_lines else "Non-contributory",
        "social_hx": "\n".join(social_lines),
        "allergies_summary": "; ".join([f"{a['name']} ({a['reaction']})" for a in allergies]) if allergies else "NKDA",
        "exam": "\n".join(exam_lines),
        "assessment_plan": "\n".join(ap_lines),
        "note_uuid": new_uuid(),
    }


# ---------------------------------------------------------------------------
# TOP-LEVEL PATIENT GENERATOR
# ---------------------------------------------------------------------------
def generate_patient(overrides: dict = None, complexity: str = "Moderate") -> dict:
    """
    Returns a complete patient dict ready for cda_builder.build_cda().
    `overrides`: any demographic fields from the GUI form.
    `complexity`: "Simple" | "Moderate" | "Complex"
    """
    demo = generate_demographics(overrides)
    age = demo["age"]
    sex_code = demo["sex_code"]

    n_dx = rnd_range(complexity, "num_diagnoses")
    n_med = rnd_range(complexity, "num_meds")
    n_allergy = rnd_range(complexity, "num_allergies")
    n_labs = rnd_range(complexity, "num_lab_panels")
    n_enc = rnd_range(complexity, "num_encounters")
    n_imm = rnd_range(complexity, "num_immunizations")
    n_proc = rnd_range(complexity, "num_procedures")
    n_fhx = rnd_range(complexity, "num_family_hx")
    detail = COMPLEXITY[complexity]["notes_detail"]

    problems = generate_problems(demo, n_dx)
    medications = generate_medications(demo, n_med, problems)
    allergies = generate_allergies(n_allergy)
    labs = generate_lab_results(demo, n_labs, problems)
    immunizations = generate_immunizations(demo, n_imm)
    procedures = generate_procedures(demo, n_proc, problems)
    vitals_history = generate_vitals(demo, n_enc)
    social_hx = generate_social_history(demo)
    family_hx = generate_family_history(n_fhx)
    insurance = generate_insurance(demo)
    care_team = generate_care_team(random.randint(1, 3))

    latest_vitals = vitals_history[0] if vitals_history else {
        "systolic": 120, "diastolic": 80, "hr": 72, "spo2": 98,
        "temp_c": 37.0, "rr": 16,
    }

    progress_note = generate_progress_note(
        demo, problems, medications, allergies, social_hx,
        family_hx, latest_vitals, detail
    )

    return {
        "demo": demo,
        "social_hx": social_hx,
        "family_hx": family_hx,
        "problems": problems,
        "medications": medications,
        "allergies": allergies,
        "labs": labs,
        "immunizations": immunizations,
        "procedures": procedures,
        "vitals_history": vitals_history,
        "insurance": insurance,
        "care_team": care_team,
        "progress_note": progress_note,
        "complexity": complexity,
        "generated_at": datetime.now().isoformat(),
    }
