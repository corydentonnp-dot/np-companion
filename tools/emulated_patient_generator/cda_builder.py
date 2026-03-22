"""
cda_builder.py — Converts a patient dict from generators.py into HL7 CDA XML.
Uses only stdlib xml.etree — no lxml required.
"""

import xml.etree.ElementTree as ET
from datetime import date, datetime
import uuid


HL7 = "urn:hl7-org:v3"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
SDTC = "urn:hl7-org:sdtc"

ET.register_namespace("", HL7)
ET.register_namespace("xsi", XSI)
ET.register_namespace("sdtc", SDTC)


def _tag(local):
    return f"{{{HL7}}}{local}"


def fmt(d) -> str:
    if isinstance(d, date):
        return d.strftime("%Y%m%d")
    return str(d)


def fmt_disp(d) -> str:
    if isinstance(d, date):
        return d.strftime("%m/%d/%Y")
    return str(d)


def sub(parent, tag_name, attrib=None, text=None):
    attrib = attrib or {}
    el = ET.SubElement(parent, _tag(tag_name), attrib)
    if text:
        el.text = text
    return el


def new_uuid():
    return str(uuid.uuid4())


def build_addr(parent, address, city, state, zip_code, use="HP"):
    addr = sub(parent, "addr", {"use": use})
    sub(addr, "streetAddressLine", text=address)
    sub(addr, "city", text=city)
    sub(addr, "state", text=state)
    sub(addr, "postalCode", text=zip_code)
    sub(addr, "country", text="US")
    return addr


def build_org_addr(parent, use="WP"):
    addr = sub(parent, "addr", {"use": use})
    sub(addr, "streetAddressLine", text="13911 St Francis Blvd, Suite 101")
    sub(addr, "city", text="Midlothian")
    sub(addr, "state", text="VA")
    sub(addr, "postalCode", text="23114")
    sub(addr, "country", text="US")


def build_provider_block(parent, provider: dict):
    person = sub(parent, "assignedPerson")
    name = sub(person, "name")
    given_parts = provider["first"].split()
    for gp in given_parts:
        sub(name, "given", text=gp)
    sub(name, "family", text=provider["last"])
    sub(name, "suffix", text=provider["suffix"])
    org = sub(parent, "representedOrganization")
    sub(org, "name", text="Family Practice Associates of Chesterfield")
    sub(org, "telecom", {"use": "WP", "value": "tel:+1(804)-423-9913"})
    build_org_addr(org, "WP")


def build_author_block(parent, provider: dict, time_val: str):
    author = sub(parent, "author")
    sub(author, "time", {"value": time_val})
    aa = sub(author, "assignedAuthor")
    sub(aa, "id", {"root": "2.16.840.1.113883.4.6",
                   "extension": provider["npi"],
                   "assigningAuthorityName": "National Provider Identifier"})
    build_org_addr(aa, "WP")
    sub(aa, "telecom", {"use": "WP", "value": "tel:+1(804)-423-9913"})
    build_provider_block(aa, provider)


def _section_header(component, loinc, title, templates):
    section = sub(component, "section")
    for t in templates:
        if isinstance(t, tuple):
            sub(section, "templateId", {"root": t[0], "extension": t[1]})
        else:
            sub(section, "templateId", {"root": t})
    sub(section, "code", {"code": loinc, "codeSystem": "2.16.840.1.113883.6.1",
                           "codeSystemName": "LOINC", "displayName": title})
    sub(section, "title", text=title)
    return section


def build_cda(patient: dict) -> str:
    """Main entry point. Returns pretty-ish XML string."""
    demo = patient["demo"]
    today = date.today()
    now_str = datetime.now().strftime("%Y%m%d%H%M%S")
    enc_time = now_str + "-0400"
    default_provider = {
        "first": "Cory", "last": "Denton", "suffix": "FNP",
        "npi": "1891645123", "role": "PCP"
    }

    # ---- Root ----
    root = ET.Element(_tag("ClinicalDocument"), {
        f"{{{XSI}}}schemaLocation": f"{HL7} CDA.xsd",
        "xmlns:sdtc": SDTC,
        "xmlns:xsi": XSI,
    })
    sub(root, "realmCode", {"code": "US"})
    sub(root, "typeId", {"root": "2.16.840.1.113883.1.3", "extension": "POCD_HD000040"})
    for r, e in [
        ("2.16.840.1.113883.10.20.22.1.1", "2015-08-01"),
        ("2.16.840.1.113883.10.20.22.1.1", None),
        ("2.16.840.1.113883.10.20.22.1.2", "2015-08-01"),
        ("2.16.840.1.113883.10.20.22.1.2", None),
    ]:
        attrs = {"root": r}
        if e:
            attrs["extension"] = e
        sub(root, "templateId", attrs)
    sub(root, "id", {"root": "2.16.840.1.113883.3.1167", "extension": "AmazingCharts"})
    sub(root, "code", {"code": "34133-9", "codeSystem": "2.16.840.1.113883.6.1",
                        "codeSystemName": "LOINC",
                        "displayName": "Summarization of episode note"})
    sub(root, "title",
        text="Family Practice Associates of Chesterfield Clinical Summary — TEST PATIENT")
    sub(root, "effectiveTime", {"value": enc_time})
    sub(root, "confidentialityCode", {
        "code": "N", "displayName": "Normal",
        "codeSystem": "2.16.840.1.113883.5.25", "codeSystemName": "Confidentiality"
    })
    sub(root, "languageCode", {"code": demo.get("lang_code", "en-US").split(",")[0]})
    sub(root, "setId", {"root": demo.get("set_uuid", new_uuid()), "extension": "AmazingCharts"})
    sub(root, "versionNumber", {"value": "1"})

    # ---- recordTarget ----
    rt = sub(root, "recordTarget")
    pr = sub(rt, "patientRole")
    sub(pr, "id", {"root": "2.16.840.1.113883.3.1167.TEST", "extension": demo["mrn"]})
    build_addr(pr, demo["address"], demo["city"], demo["state"], demo["zip"], "HP")
    sub(pr, "telecom", {"use": "HP", "value": demo["home_phone"]})
    if demo.get("cell_phone"):
        sub(pr, "telecom", {"use": "MC", "value": demo["cell_phone"]})
    if demo.get("work_phone"):
        sub(pr, "telecom", {"use": "WP", "value": demo["work_phone"]})
    if demo.get("alt_phone"):
        sub(pr, "telecom", {"use": "AS", "value": demo["alt_phone"]})
    pat = sub(pr, "patient")
    pname = sub(pat, "name", {"use": "L"})
    sub(pname, "given", text=demo["first"])
    if demo.get("middle"):
        sub(pname, "given", text=demo["middle"])
    sub(pname, "family", text=demo["last"])
    if demo.get("suffix"):
        sub(pname, "suffix", text=demo["suffix"])
    sub(pat, "administrativeGenderCode", {
        "code": demo["sex_code"],
        "codeSystem": "2.16.840.1.113883.5.1",
        "displayName": demo.get("sex_display", demo["sex_code"]),
        "codeSystemName": "AdministrativeGender"
    })
    sub(pat, "birthTime", {"value": fmt(demo["dob"])})
    sub(pat, "maritalStatusCode", {
        "code": demo.get("marital_code", "UNK"),
        "displayName": demo.get("marital_display", "Unknown"),
        "codeSystem": "2.16.840.1.113883.5.2"
    })
    # Religion
    rel_code = sub(pat, "religiousAffiliationCode")
    if demo.get("religion") and demo["religion"] not in ("Declined to specify", "Agnostic", "Atheist / No Religious Affiliation"):
        rel_code.set("displayName", demo["religion"])
        rel_code.set("nullFlavor", "OTH")
    else:
        rel_code.set("nullFlavor", "NI")
    # Race
    rc = sub(pat, "raceCode", {
        "displayName": demo.get("race_display", "Unknown"),
        "codeSystem": "2.16.840.1.113883.6.238"
    })
    if demo.get("race_code") and demo["race_code"] != "UNK":
        rc.set("code", demo["race_code"])
    else:
        rc.set("nullFlavor", "UNK")
    sub(pat, "ethnicGroupCode", {"nullFlavor": "UNK"})
    # Gender identity (sdtc extension)
    if demo.get("gender_identity"):
        gi_display, gi_code = demo["gender_identity"]
        gi = ET.SubElement(pat, f"{{{SDTC}}}genderCode", {
            "code": gi_code,
            "codeSystem": "2.16.840.1.113883.6.96",
            "displayName": gi_display,
            "codeSystemName": "SNOMED CT"
        })
    # Language
    lang_comm = sub(pat, "languageCommunication")
    lang_el = sub(lang_comm, "languageCode")
    lang_code_val = demo.get("lang_code", "en").split(",")[0]
    lang_el.set("code", lang_code_val)
    is_bilingual = "," in demo.get("lang_code", "en")
    if is_bilingual:
        sub(lang_comm, "preferenceInd", {"value": "true"})
        # Second language
        lang_comm2 = sub(pat, "languageCommunication")
        lang_el2 = sub(lang_comm2, "languageCode")
        lang_el2.set("code", demo["lang_code"].split(",")[1])
        sub(lang_comm2, "preferenceInd", {"value": "false"})
    # Provider org
    po = sub(pr, "providerOrganization")
    sub(po, "id", {"root": "2.16.840.1.113883.3.1167", "extension": "AmazingCharts"})
    sub(po, "name", text="Family Practice Associates of Chesterfield")
    sub(po, "telecom", {"use": "WP", "value": "tel:+1(804)-423-9913"})
    build_org_addr(po, "WP")

    # ---- author ----
    build_author_block(root, default_provider, enc_time)

    # ---- custodian ----
    cust = sub(root, "custodian")
    ac = sub(cust, "assignedCustodian")
    rco = sub(ac, "representedCustodianOrganization")
    sub(rco, "id", {"root": "2.16.840.1.113883.4.6", "extension": "1306884820",
                     "assigningAuthorityName": "National Provider Identifier"})
    sub(rco, "name", text="Family Practice Associates of Chesterfield")
    sub(rco, "telecom", {"use": "WP", "value": "tel:+1(804)-423-9913"})
    build_org_addr(rco, "WP")

    # ---- documentationOf ----
    dof = sub(root, "documentationOf", {"typeCode": "DOC"})
    se = sub(dof, "serviceEvent", {"classCode": "PCPR"})
    se_time = sub(se, "effectiveTime")
    dob_str = fmt(demo["dob"])
    sub(se_time, "low", {"value": dob_str})
    sub(se_time, "high", {"value": fmt(today)})
    for ct_member in patient.get("care_team", [default_provider]):
        perf = sub(se, "performer", {"typeCode": "PRF"})
        perf_time = sub(perf, "time")
        sub(perf_time, "low", {"value": fmt(ct_member.get("start", today))})
        ae = sub(perf, "assignedEntity")
        npi = ct_member.get("npi", "1891645123")
        sub(ae, "id", {"extension": npi, "root": "2.16.840.1.113883.4.6",
                        "assigningAuthorityName": "National Provider Identifier"})
        build_org_addr(ae, "WP")
        sub(ae, "telecom", {"use": "WP", "value": "tel:+1(804)-423-9913"})
        build_provider_block(ae, ct_member)

    # ---- componentOf ----
    cof = sub(root, "componentOf")
    ee = sub(cof, "encompassingEncounter")
    sub(ee, "id", {"root": demo.get("encounter_uuid", new_uuid()), "extension": "1306884820"})
    sub(ee, "code", {"code": "AMB", "codeSystem": "2.16.840.1.113883.5.4",
                      "codeSystemName": "ActCode", "displayName": "Ambulatory"})
    ee_time = sub(ee, "effectiveTime")
    sub(ee_time, "low", {"value": enc_time})
    rp = sub(ee, "responsibleParty")
    rp_ae = sub(rp, "assignedEntity")
    sub(rp_ae, "id", {"extension": default_provider["npi"],
                       "root": "2.16.840.1.113883.4.6",
                       "assigningAuthorityName": "National Provider Identifier"})
    build_org_addr(rp_ae)
    sub(rp_ae, "telecom", {"use": "WP", "value": "tel:+1(804)-423-9913"})
    rp_org = sub(rp_ae, "representedOrganization")
    sub(rp_org, "name", text="Family Practice Associates of Chesterfield")
    ep = sub(ee, "encounterParticipant", {"typeCode": "ATND"})
    ep_time = sub(ep, "time")
    sub(ep_time, "low", {"value": enc_time})
    ep_ae = sub(ep, "assignedEntity")
    sub(ep_ae, "id", {"extension": default_provider["npi"], "root": "2.16.840.1.113883.4.6"})
    build_org_addr(ep_ae)
    sub(ep_ae, "telecom", {"use": "WP", "value": "tel:+1(804)-423-9913"})
    ep_person = sub(ep_ae, "assignedPerson")
    ep_name = sub(ep_person, "name")
    sub(ep_name, "given", text="Cory")
    sub(ep_name, "family", text="Denton")
    sub(ep_name, "suffix", text="FNP")
    loc = sub(ee, "location")
    hcf = sub(loc, "healthCareFacility")
    sub(hcf, "id", {"root": "2.16.840.1.113883.19", "extension": "1306884820"})
    hcf_loc = sub(hcf, "location")
    sub(hcf_loc, "name", text="Family Practice Associates of Chesterfield")
    build_org_addr(hcf_loc, "WP")

    # ============================================================
    # STRUCTURED BODY
    # ============================================================
    comp = sub(root, "component")
    body = sub(comp, "structuredBody")

    # ---- REASON FOR VISIT ----
    pn = patient.get("progress_note", {})
    c = sub(body, "component")
    s = _section_header(c, "29299-5", "REASON FOR VISIT",
                         [("2.16.840.1.113883.10.20.22.2.12",)])
    txt = sub(s, "text")
    tbl = sub(txt, "table")
    thead = sub(tbl, "thead")
    tr_h = sub(thead, "tr")
    sub(tr_h, "th", text="Reason for Visit / Chief Complaint")
    tbody = sub(tbl, "tbody")
    tr_b = sub(tbody, "tr")
    sub(tr_b, "td", text=pn.get("cc", "Follow-up"))

    # ---- ALLERGIES ----
    c = sub(body, "component")
    s = _section_header(c, "48765-2", "ALLERGIES AND ADVERSE REACTIONS",
                         [("2.16.840.1.113883.10.20.22.2.6.1", "2015-08-01"),
                          ("2.16.840.1.113883.10.20.22.2.6.1",)])
    txt = sub(s, "text")
    tbl = sub(txt, "table")
    thead = sub(tbl, "thead")
    tr_h = sub(thead, "tr")
    for h in ["Substance", "Reaction", "Severity", "Status"]:
        sub(tr_h, "th", text=h)
    tbody = sub(tbl, "tbody")
    allergies = patient.get("allergies", [])
    if not allergies:
        tr = sub(tbody, "tr")
        sub(tr, "td", text="No Known Drug Allergies")
        for _ in range(3):
            sub(tr, "td", text="--")
    else:
        for i, a in enumerate(allergies, 1):
            tr = sub(tbody, "tr", {"ID": f"ALGSUMMARY_{i}"})
            sub(tr, "td", {"ID": f"ALGSUB_{i}"}, text=a["name"])
            sub(tr, "td", {"ID": f"ALGREACT_{i}"}, text=a["reaction"])
            sub(tr, "td", {"ID": f"ALGSEV_{i}"}, text=a["severity"])
            sub(tr, "td", {"ID": f"ALGSTATUS_{i}"}, text=a["status"])
            entry = sub(s, "entry", {"typeCode": "DRIV"})
            act = sub(entry, "act", {"classCode": "ACT", "moodCode": "EVN"})
            sub(act, "templateId", {"root": "2.16.840.1.113883.10.20.22.4.30",
                                     "extension": "2015-08-01"})
            sub(act, "id", {"root": a["uuid"]})
            sub(act, "code", {"code": "48765-2", "codeSystem": "2.16.840.1.113883.6.1"})
            sub(act, "statusCode", {"code": "active" if a["status"] == "Active" else "completed"})
            eff = sub(act, "effectiveTime")
            sub(eff, "low", {"value": fmt(a["onset"])})
            er = sub(act, "entryRelationship", {"typeCode": "SUBJ"})
            obs = sub(er, "observation", {"classCode": "OBS", "moodCode": "EVN"})
            sub(obs, "templateId", {"root": "2.16.840.1.113883.10.20.22.4.7",
                                     "extension": "2014-06-09"})
            sub(obs, "id", {"root": a["obs_uuid"]})
            sub(obs, "code", {"code": "ASSERTION", "codeSystem": "2.16.840.1.113883.5.4"})
            sub(obs, "statusCode", {"code": "completed"})
            obs_eff = sub(obs, "effectiveTime")
            sub(obs_eff, "low", {"value": fmt(a["onset"])})
            sub(obs, "value", {
                f"{{{XSI}}}type": "CD",
                "code": "419199007",
                "codeSystem": "2.16.840.1.113883.6.96",
                "displayName": "Allergy to Substance",
                "codeSystemName": "SNOMED CT"
            })
            part = sub(obs, "participant", {"typeCode": "CSM"})
            pr_role = sub(part, "participantRole", {"classCode": "MANU"})
            pe = sub(pr_role, "playingEntity", {"classCode": "MMAT"})
            sub(pe, "code", {"code": a["rxnorm"], "codeSystem": "2.16.840.1.113883.6.88",
                              "codeSystemName": "RXNORM", "displayName": a["name"]})

    # ---- MEDICATIONS ----
    c = sub(body, "component")
    s = _section_header(c, "10160-0", "MEDICATIONS",
                         [("2.16.840.1.113883.10.20.22.2.1.1", "2014-06-09")])
    txt = sub(s, "text")
    tbl = sub(txt, "table")
    thead = sub(tbl, "thead")
    tr_h = sub(thead, "tr")
    for h in ["Medication", "Generic", "Sig", "Start Date", "Status", "Date Inactivated"]:
        sub(tr_h, "th", text=h)
    tbody = sub(tbl, "tbody")
    meds = patient.get("medications", [])
    if not meds:
        tr = sub(tbody, "tr")
        sub(tr, "td", text="No current medications on file")
        for _ in range(5):
            sub(tr, "td", text="--")
    else:
        for i, m in enumerate(meds, 1):
            tr = sub(tbody, "tr")
            sub(tr, "td", {"ID": f"Med{i}"}, text=m["name"])
            sub(tr, "td", text=m["generic"])
            sub(tr, "td", {"ID": f"MedicationSig_{i}"}, text=m["sig"])
            sub(tr, "td", text=fmt_disp(m["start"]))
            sub(tr, "td", text="Active" if m["active"] else "Inactive")
            sub(tr, "td", text=fmt_disp(m["end"]) if m.get("end") else "--")
            entry = sub(s, "entry", {"typeCode": "DRIV"})
            sa = sub(entry, "substanceAdministration",
                     {"classCode": "SBADM", "moodCode": "EVN"})
            sub(sa, "templateId", {"root": "2.16.840.1.113883.10.20.22.4.16",
                                    "extension": "2014-06-09"})
            sub(sa, "id", {"root": m["uuid"]})
            txt_ref = sub(sa, "text")
            sub(txt_ref, "reference", {"value": f"#MedicationSig_{i}"})
            sub(sa, "statusCode", {"code": "completed"})
            eff = sub(sa, "effectiveTime", {f"{{{XSI}}}type": "IVL_TS"})
            sub(eff, "low", {"value": fmt(m["start"])})
            sub(eff, "high", {"value": fmt(m["end"])} if m.get("end") else {"nullFlavor": "UNK"})
            sub(sa, "doseQuantity", {"value": str(m["dose"]), "unit": m["unit"]})
            consumable = sub(sa, "consumable")
            mp = sub(consumable, "manufacturedProduct", {"classCode": "MANU"})
            sub(mp, "templateId", {"root": "2.16.840.1.113883.10.20.22.4.23",
                                    "extension": "2014-06-09"})
            sub(mp, "id", {"root": m["product_uuid"]})
            mm = sub(mp, "manufacturedMaterial")
            rxnorm = m.get("rxnorm", "UNK")
            rxnorm = rxnorm if rxnorm.isdigit() else "UNK"
            code_el = sub(mm, "code", {
                "code": rxnorm, "codeSystem": "2.16.840.1.113883.6.88",
                "codeSystemName": "RXNORM", "displayName": m["name"]
            })
            ot = sub(code_el, "originalText")
            sub(ot, "reference", {"value": f"#Med{i}"})

    # ---- PROBLEMS ----
    c = sub(body, "component")
    s = _section_header(c, "11450-4", "PROBLEMS",
                         [("2.16.840.1.113883.10.20.22.2.5.1", "2015-08-01"),
                          ("2.16.840.1.113883.10.20.22.2.5.1",)])
    txt = sub(s, "text")
    tbl = sub(txt, "table")
    thead = sub(tbl, "thead")
    tr_h = sub(thead, "tr")
    for h in ["Problem", "Status", "Date Started", "Date Resolved", "Date Inactivated"]:
        sub(tr_h, "th", text=h)
    tbody = sub(tbl, "tbody")
    problems = patient.get("problems", [])
    if not problems:
        tr = sub(tbody, "tr")
        sub(tr, "td", text="No active problems on file")
        for _ in range(4):
            sub(tr, "td", text="--")
    else:
        for i, dx in enumerate(problems, 1):
            tr = sub(tbody, "tr", {"ID": f"PROBSUMMARY_{i}"})
            label = f"{dx['display']} [ICD-10: {dx['icd10']}]"
            sub(tr, "td", {"ID": f"PROBKIND_{i}"}, text=label)
            sub(tr, "td", {"ID": f"PROBSTATUS_{i}"}, text=dx["status"])
            sub(tr, "td", text=fmt_disp(dx["onset"]))
            sub(tr, "td", text=fmt_disp(dx["resolved"]) if dx.get("resolved") else "NA")
            sub(tr, "td", text="NA")
            entry = sub(s, "entry", {"typeCode": "DRIV"})
            act = sub(entry, "act", {"classCode": "ACT", "moodCode": "EVN"})
            sub(act, "templateId", {"root": "2.16.840.1.113883.10.20.22.4.3",
                                     "extension": "2015-08-01"})
            sub(act, "id", {"root": dx["act_uuid"]})
            sub(act, "code", {"code": "CONC", "codeSystem": "2.16.840.1.113883.5.6",
                               "displayName": "Concern"})
            sub(act, "statusCode",
                {"code": "active" if dx["status"] == "Active" else "completed"})
            act_eff = sub(act, "effectiveTime")
            sub(act_eff, "low", {"value": fmt(dx["onset"])})
            er = sub(act, "entryRelationship", {"typeCode": "SUBJ"})
            obs = sub(er, "observation", {"classCode": "OBS", "moodCode": "EVN"})
            sub(obs, "templateId", {"root": "2.16.840.1.113883.10.20.22.4.4",
                                     "extension": "2015-08-01"})
            sub(obs, "id", {"root": dx["obs_uuid"]})
            sub(obs, "code", {"code": "282291009", "codeSystem": "2.16.840.1.113883.6.96",
                               "displayName": "Diagnosis"})
            sub(obs, "statusCode", {"code": "completed"})
            obs_eff = sub(obs, "effectiveTime")
            sub(obs_eff, "low", {"value": fmt(dx["onset"])})
            # Use SNOMED if available, else ICD-10 translation
            if dx.get("snomed") and dx["snomed"] != "UNK":
                sub(obs, "value", {
                    f"{{{XSI}}}type": "CD",
                    "code": dx["snomed"],
                    "codeSystem": "2.16.840.1.113883.6.96",
                    "displayName": dx["display"],
                    "codeSystemName": "SNOMED CT"
                })
            else:
                val_el = sub(obs, "value", {
                    f"{{{XSI}}}type": "CD",
                    "codeSystem": "2.16.840.1.113883.6.96",
                    "nullFlavor": "OTH"
                })
                sub(val_el, "translation", {
                    "code": dx["icd10"],
                    "displayName": dx["display"],
                    "codeSystem": "2.16.840.1.113883.6.3",
                    "codeSystemName": "ICD-10"
                })
            status_er = sub(obs, "entryRelationship", {"typeCode": "REFR"})
            status_obs = sub(status_er, "observation",
                              {"classCode": "OBS", "moodCode": "EVN"})
            sub(status_obs, "templateId", {"root": "2.16.840.1.113883.10.20.22.4.6"})
            sub(status_obs, "code", {"code": "33999-4", "codeSystem": "2.16.840.1.113883.6.1",
                                      "displayName": "Status"})
            sub(status_obs, "statusCode", {"code": "completed"})
            status_code = "55561003" if dx["status"] == "Active" else "73425007"
            status_display = dx["status"]
            sub(status_obs, "value", {
                f"{{{XSI}}}type": "CD",
                "code": status_code,
                "codeSystem": "2.16.840.1.113883.6.96",
                "displayName": status_display,
                "codeSystemName": "SNOMED CT"
            })

    # ---- SOCIAL HISTORY ----
    c = sub(body, "component")
    s = _section_header(c, "29762-2", "SOCIAL HISTORY",
                         [("2.16.840.1.113883.10.20.22.2.17", "2015-08-01"),
                          ("2.16.840.1.113883.10.20.22.2.17",)])
    social = patient.get("social_hx", {})
    txt = sub(s, "text")
    tbl = sub(txt, "table")
    thead = sub(tbl, "thead")
    tr_h = sub(thead, "tr")
    for h in ["Observation", "Description"]:
        sub(tr_h, "th", text=h)
    tbody = sub(tbl, "tbody")
    sh_rows = [
        ("Smoking Status", social.get("smoking", ("Unknown",))[0]
         if isinstance(social.get("smoking"), tuple) else str(social.get("smoking", "Unknown"))),
        ("Alcohol Use", social.get("alcohol", "Not reported")),
        ("Drug Use", social.get("drugs", "Not reported")),
        ("Occupation", social.get("occupation", "Not reported")),
        ("Exercise", social.get("exercise", "Not reported")),
        ("Diet", social.get("diet", "Not reported")),
        ("Birth Sex", demo.get("sex_display", "Unknown")),
        ("Religion", demo.get("religion", "Not reported")),
        ("Language(s)", demo.get("language", "English")),
    ]
    if demo.get("sexual_orientation"):
        so_display, _ = demo["sexual_orientation"]
        sh_rows.append(("Sexual Orientation", so_display))
    if demo.get("gender_identity"):
        gi_display, _ = demo["gender_identity"]
        sh_rows.append(("Gender Identity", gi_display))
    for obs_name, obs_val in sh_rows:
        tr = sub(tbody, "tr")
        sub(tr, "td", text=obs_name)
        sub(tr, "td", text=obs_val)
    # Tobacco entry
    smoking_tuple = social.get("smoking", ("Never smoker", "266919005"))
    if isinstance(smoking_tuple, (list, tuple)) and len(smoking_tuple) == 2:
        smk_display, smk_code = smoking_tuple
    else:
        smk_display, smk_code = str(smoking_tuple), "266919005"
    entry = sub(s, "entry", {"typeCode": "DRIV"})
    obs = sub(entry, "observation", {"classCode": "OBS", "moodCode": "EVN"})
    sub(obs, "templateId", {"root": "2.16.840.1.113883.10.20.22.4.78",
                             "extension": "2014-06-09"})
    sub(obs, "id", {"root": new_uuid()})
    sub(obs, "code", {"code": "72166-2", "codeSystem": "2.16.840.1.113883.6.1",
                       "displayName": "Tobacco smoking status"})
    sub(obs, "statusCode", {"code": "completed"})
    sub(obs, "value", {
        f"{{{XSI}}}type": "CD",
        "code": smk_code,
        "codeSystem": "2.16.840.1.113883.6.96",
        "displayName": smk_display
    })
    # Birth sex entry
    entry2 = sub(s, "entry", {"typeCode": "DRIV"})
    obs2 = sub(entry2, "observation", {"classCode": "OBS", "moodCode": "EVN"})
    sub(obs2, "templateId", {"root": "2.16.840.1.113883.10.20.22.4.200",
                              "extension": "2016-06-01"})
    sub(obs2, "code", {"code": "76689-9", "codeSystem": "2.16.840.1.113883.6.1",
                        "displayName": "Sex Assigned At Birth"})
    sub(obs2, "statusCode", {"code": "completed"})
    sub(obs2, "value", {
        f"{{{XSI}}}type": "CD",
        "code": demo["sex_code"],
        "codeSystem": "2.16.840.1.113883.5.1",
        "displayName": demo.get("sex_display", demo["sex_code"])
    })

    # ---- VITAL SIGNS ----
    c = sub(body, "component")
    s = _section_header(c, "8716-3", "VITAL SIGNS",
                         [("2.16.840.1.113883.10.20.22.2.4.1", "2015-08-01")])
    txt = sub(s, "text")
    tbl = sub(txt, "table")
    thead = sub(tbl, "thead")
    tr_h = sub(thead, "tr")
    for h in ["Encounter Date", "Ht (in)", "Wt (lb)", "BMI", "BP Sys", "BP Dias",
              "HR", "SpO2%", "Temp °F", "RR"]:
        sub(tr_h, "th", text=h)
    tbody = sub(tbl, "tbody")
    vit_history = patient.get("vitals_history", [])
    for v in vit_history:
        tr = sub(tbody, "tr")
        sub(tr, "td", text=fmt_disp(v["date"]))
        ht_in = round(v["height_cm"] / 2.54, 1) if v.get("height_cm") else "--"
        wt_lb = round(v["weight_kg"] * 2.205, 1) if v.get("weight_kg") else "--"
        sub(tr, "td", text=str(ht_in))
        sub(tr, "td", text=str(wt_lb))
        sub(tr, "td", text=str(v.get("bmi", "--")))
        sub(tr, "td", text=str(v.get("systolic", "--")))
        sub(tr, "td", text=str(v.get("diastolic", "--")))
        sub(tr, "td", text=str(v.get("hr", "--")))
        sub(tr, "td", text=str(v.get("spo2", "--")))
        temp_f = round(v["temp_c"] * 9 / 5 + 32, 1) if v.get("temp_c") else "--"
        sub(tr, "td", text=str(temp_f))
        sub(tr, "td", text=str(v.get("rr", "--")))
    # Structured vital sign entries (most recent only for brevity)
    if vit_history:
        v = vit_history[0]
        entry = sub(s, "entry")
        org = sub(entry, "organizer", {"classCode": "CLUSTER", "moodCode": "EVN"})
        sub(org, "templateId", {"root": "2.16.840.1.113883.10.20.22.4.26"})
        sub(org, "id", {"root": v["organizer_uuid"]})
        sub(org, "code", {"code": "46680005", "codeSystem": "2.16.840.1.113883.6.96",
                           "displayName": "VITAL SIGNS"})
        sub(org, "statusCode", {"code": "completed"})
        sub(org, "effectiveTime", {"value": fmt(v["date"])})
        vital_pairs = [
            ("8302-2", "HEIGHT", str(v.get("height_cm", "")), "cm"),
            ("29463-7", "WEIGHT", str(v.get("weight_kg", "")), "kg"),
            ("39156-5", "BMI", str(v.get("bmi", "")), "kg/m2"),
            ("8480-6", "BP SYSTOLIC", str(v.get("systolic", "")), "mm[Hg]"),
            ("8462-4", "BP DIASTOLIC", str(v.get("diastolic", "")), "mm[Hg]"),
            ("8867-4", "Heart Rate", str(v.get("hr", "")), "/min"),
            ("59408-5", "O2 % SpO2", str(v.get("spo2", "")), "%"),
            ("8310-5", "Body Temperature", str(v.get("temp_c", "")), "Cel"),
            ("9279-1", "Respiratory Rate", str(v.get("rr", "")), "/min"),
        ]
        for loinc_code, disp, val, unit in vital_pairs:
            comp_el = sub(org, "component")
            obs = sub(comp_el, "observation", {"classCode": "OBS", "moodCode": "EVN"})
            sub(obs, "templateId", {"root": "2.16.840.1.113883.10.20.22.4.27",
                                     "extension": "2014-06-09"})
            sub(obs, "id", {"root": new_uuid()})
            sub(obs, "code", {"code": loinc_code, "codeSystem": "2.16.840.1.113883.6.1",
                               "displayName": disp})
            sub(obs, "statusCode", {"code": "completed"})
            sub(obs, "effectiveTime", {"value": fmt(v["date"])})
            if val and val != "None":
                sub(obs, "value", {f"{{{XSI}}}type": "PQ", "value": val, "unit": unit})
            else:
                sub(obs, "value", {f"{{{XSI}}}type": "PQ", "nullFlavor": "NI"})

    # ---- RESULTS (LAB) ----
    c = sub(body, "component")
    s = _section_header(c, "30954-2", "RESULTS",
                         [("2.16.840.1.113883.10.20.22.2.3.1", "2015-08-01"),
                          ("2.16.840.1.113883.10.20.22.2.3.1",)])
    txt = sub(s, "text")
    labs = patient.get("labs", [])
    if not labs:
        sub(txt, "paragraph", text="No laboratory results on file.")
    else:
        for panel in labs:
            tbl = sub(txt, "table")
            cap = sub(tbl, "caption", text=f"{panel['panel_name']} — {fmt_disp(panel['panel_date'])}")
            thead = sub(tbl, "thead")
            tr_h = sub(thead, "tr")
            for h in ["Test", "Result", "Units", "Ref Range", "Flag", "Date"]:
                sub(tr_h, "th", text=h)
            tbody = sub(tbl, "tbody")
            for r in panel["results"]:
                tr = sub(tbody, "tr")
                sub(tr, "td", text=r["name"])
                sub(tr, "td", text=r["value"])
                sub(tr, "td", text=r["unit"])
                ref = f"{r['normal_low']} – {r['normal_high']}"
                sub(tr, "td", text=ref)
                sub(tr, "td", text=r["flag"])
                sub(tr, "td", text=fmt_disp(panel["panel_date"]))
            entry = sub(s, "entry")
            org = sub(entry, "organizer", {"classCode": "BATTERY", "moodCode": "EVN"})
            sub(org, "templateId", {"root": "2.16.840.1.113883.10.20.22.4.1",
                                     "extension": "2015-08-01"})
            sub(org, "id", {"root": panel["organizer_uuid"]})
            sub(org, "code", {"code": "26436-6", "codeSystem": "2.16.840.1.113883.6.1",
                               "displayName": panel["panel_name"]})
            sub(org, "statusCode", {"code": "completed"})
            sub(org, "effectiveTime", {"value": fmt(panel["panel_date"])})
            for r in panel["results"]:
                comp_el = sub(org, "component")
                obs = sub(comp_el, "observation", {"classCode": "OBS", "moodCode": "EVN"})
                sub(obs, "templateId", {"root": "2.16.840.1.113883.10.20.22.4.2",
                                         "extension": "2015-08-01"})
                sub(obs, "id", {"root": r["obs_uuid"]})
                sub(obs, "code", {"code": r["loinc"], "codeSystem": "2.16.840.1.113883.6.1",
                                   "displayName": r["name"]})
                sub(obs, "statusCode", {"code": "completed"})
                sub(obs, "effectiveTime", {"value": fmt(panel["panel_date"])})
                try:
                    float_val = float(r["value"])
                    sub(obs, "value", {
                        f"{{{XSI}}}type": "PQ",
                        "value": r["value"],
                        "unit": r["unit"]
                    })
                except (ValueError, TypeError):
                    sub(obs, "value", {
                        f"{{{XSI}}}type": "ST",
                        "value": r["value"]
                    })
                interp_code = r.get("interpretation", "N")
                sub(obs, "interpretationCode", {
                    "code": interp_code,
                    "codeSystem": "2.16.840.1.113883.5.83",
                    "displayName": r.get("flag", "Normal")
                })
                rr_el = sub(obs, "referenceRange")
                orr = sub(rr_el, "observationRange")
                rr_val = sub(orr, "value", {f"{{{XSI}}}type": "IVL_PQ"})
                sub(rr_val, "low", {"value": str(r["normal_low"]), "unit": r["unit"]})
                sub(rr_val, "high", {"value": str(r["normal_high"]), "unit": r["unit"]})

    # ---- IMMUNIZATIONS ----
    c = sub(body, "component")
    s = _section_header(c, "11369-6", "IMMUNIZATIONS",
                         [("2.16.840.1.113883.10.20.22.2.2.1", "2014-06-09"),
                          ("2.16.840.1.113883.10.20.22.2.2.1",)])
    txt = sub(s, "text")
    imms = patient.get("immunizations", [])
    if not imms:
        txt.text = "No known immunization history."
    else:
        tbl = sub(txt, "table")
        thead = sub(tbl, "thead")
        tr_h = sub(thead, "tr")
        for h in ["Vaccine", "Date", "CVX Code"]:
            sub(tr_h, "th", text=h)
        tbody = sub(tbl, "tbody")
        for imm in imms:
            tr = sub(tbody, "tr")
            sub(tr, "td", text=imm["name"])
            sub(tr, "td", text=fmt_disp(imm["admin_date"]))
            sub(tr, "td", text=imm["cvx"])
            entry = sub(s, "entry")
            sa = sub(entry, "substanceAdministration",
                     {"classCode": "SBADM", "moodCode": "EVN", "negationInd": "false"})
            sub(sa, "templateId", {"root": "2.16.840.1.113883.10.20.22.4.52",
                                    "extension": "2015-08-01"})
            sub(sa, "id", {"root": imm["uuid"]})
            sub(sa, "statusCode", {"code": "completed"})
            sub(sa, "effectiveTime", {"value": fmt(imm["admin_date"])})
            consumable = sub(sa, "consumable")
            mp = sub(consumable, "manufacturedProduct", {"classCode": "MANU"})
            sub(mp, "templateId", {"root": "2.16.840.1.113883.10.20.22.4.54",
                                    "extension": "2014-06-09"})
            mm = sub(mp, "manufacturedMaterial")
            sub(mm, "code", {"code": imm["cvx"],
                              "codeSystem": "2.16.840.1.113883.12.292",
                              "displayName": imm["name"]})
            sub(mp, "manufacturerOrganization", {"nullFlavor": "UNK"})

    # ---- PROCEDURES ----
    c = sub(body, "component")
    s = _section_header(c, "47519-4", "PROCEDURES",
                         [("2.16.840.1.113883.10.20.22.2.7.1", "2014-06-09"),
                          ("2.16.840.1.113883.10.20.22.2.7.1",)])
    txt = sub(s, "text")
    procs = patient.get("procedures", [])
    if not procs:
        txt.text = "No procedures information available."
    else:
        tbl = sub(txt, "table")
        thead = sub(tbl, "thead")
        tr_h = sub(thead, "tr")
        for h in ["Procedure", "CPT Code", "Date"]:
            sub(tr_h, "th", text=h)
        tbody = sub(tbl, "tbody")
        for proc in procs:
            tr = sub(tbody, "tr")
            sub(tr, "td", text=proc["name"])
            sub(tr, "td", text=proc["cpt"])
            sub(tr, "td", text=fmt_disp(proc["date"]))
            entry = sub(s, "entry")
            proc_el = sub(entry, "procedure", {"classCode": "PROC", "moodCode": "EVN"})
            sub(proc_el, "templateId", {"root": "2.16.840.1.113883.10.20.22.4.14",
                                         "extension": "2014-06-09"})
            sub(proc_el, "id", {"root": proc["uuid"]})
            sub(proc_el, "code", {"code": proc["cpt"],
                                   "codeSystem": "2.16.840.1.113883.6.12",
                                   "codeSystemName": "CPT",
                                   "displayName": proc["name"]})
            sub(proc_el, "statusCode", {"code": "completed"})
            sub(proc_el, "effectiveTime", {"value": fmt(proc["date"])})

    # ---- INSURANCE PROVIDERS ----
    c = sub(body, "component")
    s = _section_header(c, "48768-6", "INSURANCE PROVIDERS",
                         [("2.16.840.1.113883.10.20.22.2.18",),
                          ("2.16.840.1.113883.10.20.22.2.18", "2015-08-01")])
    txt = sub(s, "text")
    ins_list = patient.get("insurance", [])
    if not ins_list:
        txt.text = "Payer Unknown"
    else:
        tbl = sub(txt, "table")
        thead = sub(tbl, "thead")
        tr_h = sub(thead, "tr")
        for h in ["Payer", "Plan Type", "Member ID", "Group Number", "Effective Date"]:
            sub(tr_h, "th", text=h)
        tbody = sub(tbl, "tbody")
        for ins in ins_list:
            tr = sub(tbody, "tr")
            sub(tr, "td", text=ins["name"])
            sub(tr, "td", text=ins["type"])
            sub(tr, "td", text=ins.get("member_id", "--"))
            sub(tr, "td", text=ins.get("group_num", "--"))
            sub(tr, "td", text=fmt_disp(ins.get("eff_date", date.today())))

    # ---- PLAN OF CARE ----
    c = sub(body, "component")
    s = _section_header(c, "18776-5", "PLAN OF CARE",
                         [("2.16.840.1.113883.10.20.22.2.10",)])
    txt = sub(s, "text")
    txt.text = pn.get("assessment_plan", "Plan to be determined at follow-up.")

    # ---- PROGRESS NOTE ----
    c = sub(body, "component")
    s = _section_header(c, "11506-3", "Progress Notes",
                         [("2.16.840.1.113883.10.20.22.2.65", "2016-11-01")])
    note_txt = sub(s, "text")
    note_list = sub(note_txt, "list")
    note_item = sub(note_list, "item")

    def add_para(parent, label, content):
        p = sub(parent, "paragraph")
        p.text = f"{label}: {content}" if label else content

    add_para(note_item, "Chief Complaint", pn.get("cc", ""))
    add_para(note_item, "History of Present Illness", "\n" + pn.get("hpi", ""))
    add_para(note_item, "Past Medical History", pn.get("pmh", ""))
    add_para(note_item, "Family History", "\n" + pn.get("family_hx", ""))
    add_para(note_item, "Social History", "\n" + pn.get("social_hx", ""))
    add_para(note_item, "Allergies", pn.get("allergies_summary", "NKDA"))
    add_para(note_item, "Physical Examination", "\n" + pn.get("exam", ""))
    add_para(note_item, "Assessment & Plan", "\n" + pn.get("assessment_plan", ""))

    note_entry = sub(s, "entry")
    note_act = sub(note_entry, "act", {"classCode": "ACT", "moodCode": "EVN"})
    sub(note_act, "templateId", {"root": "2.16.840.1.113883.10.20.22.4.202",
                                  "extension": "2016-11-01"})
    sub(note_act, "code", {"code": "11506-3", "codeSystem": "2.16.840.1.113883.6.1",
                            "displayName": "Progress Note"})
    sub(note_act, "statusCode", {"code": "completed"})
    sub(note_act, "effectiveTime", {"value": enc_time})
    build_author_block(note_act, default_provider, enc_time)

    # ---- CARE TEAMS ----
    c = sub(body, "component")
    s = _section_header(c, "85847-2", "PATIENT CARE TEAMS",
                         [("2.16.840.1.113883.10.20.22.2.500", "2019-07-01")])
    txt = sub(s, "text")
    ct = sub(txt, "list")
    team_item = sub(ct, "item")
    sub(team_item, "content", {"ID": "CareTeamName1"},
        text="Family Practice Associates of Chesterfield Care Team (Active)")
    ct_tbl = sub(team_item, "table")
    ct_thead = sub(ct_tbl, "thead")
    ct_tr_h = sub(ct_thead, "tr")
    for h in ["Member", "Role", "Status", "Date", "Contact"]:
        sub(ct_tr_h, "th", text=h)
    ct_tbody = sub(ct_tbl, "tbody")
    for m in patient.get("care_team", []):
        ct_tr = sub(ct_tbody, "tr")
        sub(ct_tr, "td", text=f"{m['last']}, {m['first']}, {m['suffix']}")
        sub(ct_tr, "td", text=m.get("role", "Primary Care"))
        sub(ct_tr, "td", text="Active")
        sub(ct_tr, "td", text=f"({fmt_disp(m['start'])} - )")
        sub(ct_tr, "td",
            text="13911 St Francis Blvd Suite 101\nMidlothian VA 23114\n804-423-9913")

    # ---- Serialize ----
    ET.indent(root, space="  ")
    xml_str = ET.tostring(root, encoding="unicode", xml_declaration=False)
    header = '<?xml version="1.0" encoding="UTF-8"?>\n<!-- TEST PATIENT — NO REAL PHI -->\n'
    return header + xml_str
