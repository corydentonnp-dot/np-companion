"""
CareCompanion — Billing Opportunity Stack Classifier
File: billing_engine/stack_classifier.py
Phase 21.8

Classifies each opportunity_code into a stacking tier that gates
how and when it is displayed:

  STRONG_STANDALONE  — High value solo; always show (AWV, TCM face-to-face, CCM monthly)
  STRONG_STACK       — High value in combination; show prominently (G2211, screening, ACP with AWV)
  STACK_ONLY         — Low value alone; show only within qualifying stack (venipuncture, pulse ox)
  CONDITIONAL        — Show only when condition is met (G0447 if BMI documented, 99417 if time exceeds threshold)
  SUPPRESS           — Negative expected value or excessive denial risk; hide from UI

Classification gates display:
  - SUPPRESS → hidden entirely
  - STACK_ONLY → shown only within a qualifying stack context
  - CONDITIONAL → shown only when condition evaluates to true
  - STRONG_STACK / STRONG_STANDALONE → always shown
"""


# Classification map: opportunity_code → (tier, condition_description|None)
CLASSIFICATIONS = {
    # ── STRONG_STANDALONE — always show, high value solo ──
    "AWV":                  ("STRONG_STANDALONE", None),
    "CCM":                  ("STRONG_STANDALONE", None),
    "PCM_PRINCIPAL_CARE":   ("STRONG_STANDALONE", None),
    "TCM":                  ("STRONG_STANDALONE", None),
    "PREVENTIVE_EM":        ("STRONG_STANDALONE", None),
    "BHI":                  ("STRONG_STANDALONE", None),
    "COCM_INITIAL":         ("STRONG_STANDALONE", None),
    "COCM_SUBSEQUENT":      ("STRONG_STANDALONE", None),
    "RPM":                  ("STRONG_STANDALONE", None),

    # ── STRONG_STACK — high value in combination ──
    "G2211":                ("STRONG_STACK", None),
    "CARE_GAP_SCREENING":   ("STRONG_STACK", None),
    "ACP_STANDALONE":       ("STRONG_STACK", None),
    "TOBACCO_CESSATION":    ("STRONG_STACK", None),
    "ALCOHOL_SCREENING":    ("STRONG_STACK", None),
    "COGNITIVE_ASSESSMENT":  ("STRONG_STACK", None),
    "MODIFIER_25_PROMPT":   ("STRONG_STACK", None),
    "STI_SCREENING":        ("STRONG_STACK", None),
    "VACCINE_ADMIN":        ("STRONG_STACK", None),
    "TELE_PHONE_EM":        ("STRONG_STACK", None),
    "TELE_DIGITAL_EM":      ("STRONG_STACK", None),

    # ── STACK_ONLY — low standalone value, show within stacks only ──
    "PROC_VENIPUNCTURE":    ("STACK_ONLY", None),
    "PROC_PULSE_OX":        ("STACK_ONLY", None),
    "PROC_INJECTION_ADMIN": ("STACK_ONLY", None),
    "MON_LIPID":            ("STACK_ONLY", None),
    "MON_TSH":              ("STACK_ONLY", None),
    "MON_RENAL":            ("STACK_ONLY", None),
    "MON_CBC":              ("STACK_ONLY", None),
    "MON_INR":              ("STACK_ONLY", None),
    "MON_LFT":              ("STACK_ONLY", None),
    "MON_UACR":             ("STACK_ONLY", None),
    "MON_VITD":             ("STACK_ONLY", None),
    "MON_A1C":              ("STACK_ONLY", None),

    # ── CONDITIONAL — show only when condition met ──
    "OBESITY_NUTRITION":    ("CONDITIONAL", "BMI >= 30 documented in chart"),
    "PROLONGED_SERVICE":    ("CONDITIONAL", "Total encounter time exceeds 54 min (99214) or 74 min (99215)"),
    "PROLONGED_PREVENTIVE": ("CONDITIONAL", "AWV or preventive visit exceeds time threshold"),
    "PROC_EKG":             ("CONDITIONAL", "Cardiac symptom or screening indication present"),
    "PROC_SPIROMETRY":      ("CONDITIONAL", "Respiratory symptom or COPD/asthma indication"),
    "PROC_NEBULIZER":       ("CONDITIONAL", "Acute respiratory distress or exacerbation"),

    # ── Counseling / SDOH — conditional on clinical context ──
    "COUNS_FALLS":          ("CONDITIONAL", "Age >= 65 or fall risk factors present"),
    "COUNS_CVD_IBT":        ("CONDITIONAL", "CVD risk factors documented"),
    "COUNS_DSMT":           ("CONDITIONAL", "Diabetes diagnosis and education not completed"),
    "COUNS_CONTRACEPTION":  ("CONDITIONAL", "Reproductive age female"),

    # Pediatric codes — conditional on age
    "PEDS_WELLCHILD":       ("CONDITIONAL", "Patient age < 18"),
    "PEDS_LEAD":            ("CONDITIONAL", "Age 1-2 or high-risk"),
    "PEDS_ANEMIA":          ("CONDITIONAL", "Age 9-12 months"),
    "PEDS_FLUORIDE":        ("CONDITIONAL", "Age 6 months to 5 years"),
    "PEDS_VISION":          ("CONDITIONAL", "Age 3-5 years"),
    "PEDS_HEARING":         ("CONDITIONAL", "Newborn or risk factors"),

    # Screening codes — conditional on population
    "SCREEN_DEVELOPMENTAL": ("CONDITIONAL", "Age 9, 18, or 30 months"),
    "SCREEN_SUBSTANCE":     ("CONDITIONAL", "Age >= 12"),
    "SCREEN_MATERNAL_DEPRESSION": ("CONDITIONAL", "Postpartum < 12 months"),
    "SDOH_IPV":             ("CONDITIONAL", "Reproductive age or risk factors"),
    "SDOH_HRA":             ("CONDITIONAL", "Medicare AWV visit"),
}

# Tiers ordered by display priority
TIER_PRIORITY = {
    "STRONG_STANDALONE": 1,
    "STRONG_STACK": 2,
    "CONDITIONAL": 3,
    "STACK_ONLY": 4,
    "SUPPRESS": 5,
}


class StackClassifier:
    """
    Classifies billing opportunities into display tiers.

    Usage:
        classifier = StackClassifier()
        tier, condition = classifier.classify('G2211')
        if classifier.should_display('PROC_VENIPUNCTURE', in_stack=False):
            # Don't show — STACK_ONLY without a stack
    """

    def __init__(self, custom_overrides=None):
        """
        Args:
            custom_overrides: optional dict of {opportunity_code: (tier, condition)}
                to override default classifications
        """
        self.classifications = dict(CLASSIFICATIONS)
        if custom_overrides:
            self.classifications.update(custom_overrides)

    def classify(self, opportunity_code):
        """
        Return (tier, condition_description) for an opportunity code.
        Unknown codes default to STRONG_STACK (show by default — safe).
        """
        return self.classifications.get(opportunity_code, ("STRONG_STACK", None))

    def get_tier(self, opportunity_code):
        """Return just the tier string."""
        tier, _ = self.classify(opportunity_code)
        return tier

    def get_condition(self, opportunity_code):
        """Return the condition string (None if unconditional)."""
        _, condition = self.classify(opportunity_code)
        return condition

    def should_display(self, opportunity_code, in_stack=False, condition_met=True,
                       expected_net_value=None, denial_risk=None):
        """
        Determine if an opportunity should be displayed.

        Args:
            opportunity_code: the code to evaluate
            in_stack: whether this code is part of a qualifying stack
            condition_met: whether the conditional requirement is satisfied
            expected_net_value: ENR value (suppressed if negative)
            denial_risk: denial probability (suppressed if > 0.6)

        Returns:
            bool — True if the opportunity should be shown
        """
        tier = self.get_tier(opportunity_code)

        # Dynamic suppression based on value/risk
        if expected_net_value is not None and expected_net_value < 0:
            return False
        if denial_risk is not None and denial_risk > 0.6:
            return False

        if tier == "SUPPRESS":
            return False
        if tier == "STACK_ONLY":
            return in_stack
        if tier == "CONDITIONAL":
            return condition_met
        # STRONG_STANDALONE and STRONG_STACK always display
        return True

    def classify_batch(self, opportunity_codes):
        """
        Classify multiple codes at once.
        Returns list of (code, tier, condition) tuples sorted by priority.
        """
        results = []
        for code in opportunity_codes:
            tier, condition = self.classify(code)
            results.append((code, tier, condition))

        results.sort(key=lambda x: TIER_PRIORITY.get(x[1], 99))
        return results

    def suppress(self, opportunity_code, reason=None):
        """Dynamically suppress a code (e.g., from provider settings)."""
        self.classifications[opportunity_code] = ("SUPPRESS", reason)

    def get_all_by_tier(self, tier):
        """Return all opportunity codes in a given tier."""
        return [code for code, (t, _) in self.classifications.items() if t == tier]

    @staticmethod
    def get_tier_descriptions():
        """Return human-readable tier descriptions for settings UI."""
        return {
            "STRONG_STANDALONE": "Always shown — high-value standalone opportunities",
            "STRONG_STACK": "Always shown — high value when stacked with other codes",
            "STACK_ONLY": "Shown only within a qualifying visit stack",
            "CONDITIONAL": "Shown only when clinical condition is met",
            "SUPPRESS": "Hidden — negative value or excessive denial risk",
        }
