"""
CareCompanion — Insurer Classifier

Classifies raw insurance/payer text extracted from CDA XML (or manual
entry) into canonical payer buckets consumed by the billing engine's
payer routing module.

Categories:
  "medicare"              — Original Medicare Part B
  "medicare_advantage"    — Medicare Advantage (Part C / MA plans)
  "medicaid"              — Medicaid / CHIP / state programmes
  "commercial"            — Employer / marketplace / private payer
  "unknown"               — Could not classify

The classifier uses keyword matching against known payer name patterns.
No external API calls required.
"""

import re

# ---------- keyword → category rules (checked in priority order) ----------

_MEDICARE_PATTERNS = [
    r'\bmedicare\b',
    r'\bhicn\b',
    r'\bmbi\b',          # Medicare Beneficiary Identifier
    r'\bpart\s*b\b',
    r'\bcms\b',
    r'\brailroad\s*retire',  # RRMA covered under Medicare
]

_MEDICARE_ADVANTAGE_PATTERNS = [
    r'\bmedicare\s*advantage\b',
    r'\bpart\s*c\b',
    r'\bma[-\s]plan\b',
    r'\bhumana\s*gold\b',
    r'\baetna\s*medicare\b',
    r'\bunitedhealth.*medicare\b',
    r'\banthem.*medicare\b',
    r'\bsilverscript\b',
    r'\bwellcare\s*medicare\b',
    r'\bcentene.*medicare\b',
    r'\bkiser.*medicare\b',      # Kaiser Permanente Medicare
    r'\bkaise.*senior\b',
]

_MEDICAID_PATTERNS = [
    r'\bmedicaid\b',
    r'\bchip\b',
    r'\bmedallion\b',             # Virginia Medicaid managed care
    r'\bfamilycare\b',
    r'\bstarhealth\b',            # Texas STAR Health
    r'\bstar\s*plus\b',
    r'\bsooner\s*care\b',         # Oklahoma
    r'\bmedi[-\s]?cal\b',         # California Medicaid
    r'\bbadger\s*care\b',         # Wisconsin
    r'\bpeach\s*care\b',          # Georgia
    r'\bhoosier\s*health\b',     # Indiana
    r'\ball\s*kids\b',            # Illinois
    r'\bmasshealth\b',            # Massachusetts
    r'\bhusky\b',                 # Connecticut
    r'\btenncare\b',              # Tennessee
]

_COMMERCIAL_INDICATORS = [
    r'\baetna\b',
    r'\banthem\b',
    r'\bbcbs\b',
    r'\bblue\s*cross\b',
    r'\bblue\s*shield\b',
    r'\bcigna\b',
    r'\bunited\s*health\w*\b',
    r'\buhc\b',
    r'\bhumana\b',
    r'\bkaise\b',   # Kaiser
    r'\bmetlife\b',
    r'\bguardian\b',
    r'\bhartford\b',
    r'\bprincipal\b',
    r'\btricare\b',
    r'\bwellcare\b',
    r'\bambetter\b',
    r'\bcentene\b',
    r'\bmolina\b',
    r'\bmagellan\b',
    r'\bcarelon\b',
    r'\bcaremore\b',
    r'\bhealth\s*net\b',
    r'\bempire\b',
    r'\bregence\b',
    r'\bpremera\b',
    r'\bcaption\s*health\b',
    r'\bgeisinger\b',
    r'\bhighmark\b',
    r'\bindependence\b',
    r'\bpriority\s*health\b',
    r'\bselecthealth\b',
    r'\btufts\b',
    r'\bflorida\s*blue\b',
    r'\bhorizon\b',
]


def classify_insurer(raw_text: str) -> str:
    """
    Classify raw payer/insurance text into a canonical category.

    Parameters
    ----------
    raw_text : str
        Free-text payer name, plan name, or insurance description
        extracted from CDA XML or entered manually.

    Returns
    -------
    str
        One of: "medicare", "medicare_advantage", "medicaid",
        "commercial", "unknown".
    """
    if not raw_text or not raw_text.strip():
        return 'unknown'

    text = raw_text.lower().strip()

    # Medicare Advantage must be checked BEFORE generic Medicare
    for pattern in _MEDICARE_ADVANTAGE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return 'medicare_advantage'

    for pattern in _MEDICARE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return 'medicare'

    for pattern in _MEDICAID_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return 'medicaid'

    for pattern in _COMMERCIAL_INDICATORS:
        if re.search(pattern, text, re.IGNORECASE):
            return 'commercial'

    return 'unknown'
