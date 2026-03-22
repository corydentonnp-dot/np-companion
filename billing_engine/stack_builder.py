"""
CareCompanion — Visit Stack Builder
File: billing_engine/stack_builder.py
Phase 20.1

Builds visit-specific billing stacks — compatible collections of
opportunities ordered by expected net value.

Stack templates:
  AWV Stack, DM Follow-Up, Chronic Longitudinal, Post-Hospital, Acute

Compatibility rules enforced — no conflicting codes on same claim/month.
"""

import logging

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Compatibility conflict rules
# ------------------------------------------------------------------
CONFLICTS = [
    # (code_A, code_B, scope, reason)
    ('G2211', 'MODIFIER_25_PROMPT', 'claim', 'G2211 cannot stack with modifier-25 on same claim'),
    ('G2211', 'AWV', 'claim', 'G2211 not billable with preventive-only visit'),
    ('G2211', 'AWV_INITIAL', 'claim', 'G2211 not billable with preventive-only visit'),
    ('CCM', 'PCM', 'month', 'CCM and PCM cannot bill same month'),
    ('BHI', 'COCM_INITIAL', 'month', 'BHI and CoCM cannot bill same month'),
    ('BHI', 'COCM_SUBSEQUENT', 'month', 'BHI and CoCM cannot bill same month'),
    ('BHI', 'COCM_ADDITIONAL_30', 'month', 'BHI and CoCM cannot bill same month'),
]

# ------------------------------------------------------------------
# Stack Templates — ordered lists of opportunity_codes
# ------------------------------------------------------------------
STACK_TEMPLATES = {
    'awv': {
        'label': 'Annual Wellness Visit Stack',
        'visit_types': ['awv', 'wellness', 'annual', 'preventive'],
        'codes': [
            'AWV',              # G0438/G0439 — core AWV
            'COGNITIVE_ASSESSMENT',  # G0444
            'ACP_STANDALONE',   # 99497 — advance care planning
            'ALCOHOL_SCREENING',  # G0442
            'OBESITY_NUTRITION',  # G0446/G0447
            'CARE_GAP_SCREENING',  # 96127 × 2 (PHQ-9 + GAD-7)
            'TOBACCO_CESSATION',  # 99406/99407
            'G2211',            # if chronic conditions present
        ],
    },
    'dm_followup': {
        'label': 'Diabetes Follow-Up Stack',
        'visit_types': ['dm', 'diabetes', 'followup', 'chronic'],
        'codes': [
            'PREVENTIVE_EM',    # E/M code
            'MON_A1C',          # A1C monitoring
            'MON_UACR',         # urine albumin-creatinine ratio
            'MON_LIPID',        # lipid panel
            'G2211',            # complexity add-on
            'TOBACCO_CESSATION',  # if smoker
            'CARE_GAP_SCREENING',  # PHQ-9/GAD-7
        ],
    },
    'chronic_longitudinal': {
        'label': 'Chronic Longitudinal Stack',
        'visit_types': ['chronic', 'followup', 'established'],
        'codes': [
            'PREVENTIVE_EM',
            'G2211',
            'TOBACCO_CESSATION',
            'CARE_GAP_SCREENING',
            'MON_A1C',
            'MON_LIPID',
            'MON_TSH',
            'MON_RENAL',
        ],
    },
    'post_hospital': {
        'label': 'Post-Hospital / TCM Stack',
        'visit_types': ['tcm', 'post_hospital', 'discharge', 'transition'],
        'codes': [
            'TCM',              # 99495/99496
            'MON_CBC',
            'MON_RENAL',
            'MON_LFT',
            'CARE_GAP_SCREENING',
        ],
    },
    'acute': {
        'label': 'Acute Visit Stack',
        'visit_types': ['acute', 'sick', 'urgent'],
        'codes': [
            'PREVENTIVE_EM',
            'MODIFIER_25_PROMPT',
            'PROC_PULSE_OX',
            'PROC_VENIPUNCTURE',
            'PROLONGED_SERVICE',  # 99417 if time > threshold
        ],
    },
}


class VisitStackBuilder:
    """
    Builds compatible billing stacks for a specific visit type.

    Usage:
        builder = VisitStackBuilder()
        stack = builder.build_stack(patient_data, payer_context, visit_type, opportunities)
    """

    def __init__(self):
        self._conflict_pairs = {}
        for a, b, scope, reason in CONFLICTS:
            self._conflict_pairs.setdefault(a, []).append((b, scope, reason))
            self._conflict_pairs.setdefault(b, []).append((a, scope, reason))

    def build_stack(self, patient_data, payer_context, visit_type,
                    opportunities=None, encounter_duration=None):
        """
        Build an ordered, compatible stack of billing opportunities.

        Parameters
        ----------
        patient_data : dict
            Standard patient_data dict from engine.
        payer_context : dict
            From get_payer_context().
        visit_type : str
            e.g. 'awv', 'dm_followup', 'chronic_longitudinal', 'post_hospital', 'acute'
        opportunities : list[BillingOpportunity], optional
            Pre-evaluated opportunities. If None, builds from template codes only.
        encounter_duration : int, optional
            Minutes; used for prolonged service eligibility.

        Returns
        -------
        dict
            {
                'stack_type': str,
                'label': str,
                'items': [{'opportunity_code': str, 'revenue': float, 'net_value': float,
                           'codes': str, 'type': str, 'conflict_removed': bool}],
                'total_revenue': float,
                'total_net_value': float,
                'item_count': int,
                'conflicts_removed': [{'code': str, 'reason': str}],
            }
        """
        template = self._match_template(visit_type)
        if not template:
            # No template match — return all compatible opportunities
            template = {
                'label': f'{visit_type.replace("_", " ").title()} Stack',
                'codes': [],
            }

        # Build opportunity lookup by opportunity_code
        opp_map = {}
        if opportunities:
            for opp in opportunities:
                code = getattr(opp, 'opportunity_code', None) or getattr(opp, 'opportunity_type', '')
                opp_map[code] = opp

        # Order: template codes first, then remaining opportunities
        template_codes = template.get('codes', [])
        ordered_codes = list(template_codes)
        if opportunities:
            for opp in opportunities:
                code = getattr(opp, 'opportunity_code', None) or getattr(opp, 'opportunity_type', '')
                if code and code not in ordered_codes:
                    ordered_codes.append(code)

        # Build stack with conflict checking
        stack_items = []
        included_codes = set()
        conflicts_removed = []

        for code in ordered_codes:
            opp = opp_map.get(code)
            if not opp:
                continue

            # Check conflicts with already-included codes
            conflict = self._check_conflict(code, included_codes)
            if conflict:
                conflicts_removed.append({
                    'code': code,
                    'reason': conflict,
                })
                continue

            # Prolonged service check
            if code == 'PROLONGED_SERVICE' and encounter_duration:
                if encounter_duration < 54:
                    continue

            revenue = getattr(opp, 'estimated_revenue', 0) or 0
            net_value = getattr(opp, 'expected_net_dollars', 0) or 0

            stack_items.append({
                'opportunity_code': code,
                'revenue': round(revenue, 2),
                'net_value': round(net_value, 2),
                'codes': getattr(opp, 'applicable_codes', '') or '',
                'type': getattr(opp, 'opportunity_type', '') or '',
                'confidence': getattr(opp, 'confidence_level', '') or '',
                'priority': getattr(opp, 'priority', '') or '',
            })
            included_codes.add(code)

        # Sort by net value descending within the stack
        stack_items.sort(key=lambda x: x['net_value'], reverse=True)

        total_revenue = sum(i['revenue'] for i in stack_items)
        total_net = sum(i['net_value'] for i in stack_items)

        return {
            'stack_type': visit_type,
            'label': template['label'],
            'items': stack_items,
            'total_revenue': round(total_revenue, 2),
            'total_net_value': round(total_net, 2),
            'item_count': len(stack_items),
            'conflicts_removed': conflicts_removed,
        }

    def _match_template(self, visit_type):
        """Find the best matching stack template for a visit type."""
        vt = visit_type.lower().strip()
        # Direct key match
        if vt in STACK_TEMPLATES:
            return STACK_TEMPLATES[vt]
        # Search visit_types lists
        for key, tmpl in STACK_TEMPLATES.items():
            if vt in tmpl.get('visit_types', []):
                return tmpl
        return None

    def _check_conflict(self, code, included_codes):
        """Check if code conflicts with any already-included code."""
        pairs = self._conflict_pairs.get(code, [])
        for other, scope, reason in pairs:
            if other in included_codes:
                return reason
        return None

    @staticmethod
    def get_available_templates():
        """Return list of available stack templates for UI selection."""
        return [
            {
                'key': key,
                'label': tmpl['label'],
                'visit_types': tmpl.get('visit_types', []),
                'code_count': len(tmpl['codes']),
            }
            for key, tmpl in STACK_TEMPLATES.items()
        ]
