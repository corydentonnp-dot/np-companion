# CareCompanion -- File-to-Test Block Map

> **Generated:** 03-24-26
> **Purpose:** Machine-readable mapping of source files to their test blocks. Used by `scripts/detect_changes.py` to determine which tests to run when a file changes.
> **Format:** Each source file maps to one or more test files or specific test functions.

---

## Route Files

| Source File | Test Target(s) |
|------------|----------------|
| `routes/auth.py` | `tests/test_auth.py` |
| `routes/admin.py` | `tests/test_admin.py`, `tests/test_admin_panel.py` |
| `routes/admin_benchmarks.py` | `tests/test_benchmarks.py` |
| `routes/admin_med_catalog.py` | `tests/test_med_catalog.py` |
| `routes/admin_rules_registry.py` | `tests/test_monitoring_rules.py` |
| `routes/agent_api.py` | `tests/test_agent_api.py` |
| `routes/ai_api.py` | `tests/test_ai_assistant.py` |
| `routes/bonus.py` | `tests/test_bonus_dashboard.py` |
| `routes/calculator.py` | `tests/test_calculators.py` |
| `routes/campaigns.py` | `tests/test_billing_campaigns.py` |
| `routes/caregap.py` | `tests/test_caregap_engine.py`, `tests/test_caregap_comprehensive.py` |
| `routes/ccm.py` | `tests/test_ccm.py` |
| `routes/daily_summary.py` | `tests/test_daily_summary.py` |
| `routes/dashboard.py` | `tests/test_dashboard_schedule.py` |
| `routes/help.py` | `tests/test_help_guide.py` |
| `routes/inbox.py` | `tests/test_inbox_monitor.py` |
| `routes/intelligence.py` | `tests/test_morning_briefing.py` |
| `routes/labtrack.py` | `tests/test_labtrack.py` |
| `routes/medref.py` | `tests/test_medref.py` |
| `routes/message.py` | `tests/test_messages.py` |
| `routes/metrics.py` | `tests/test_metrics.py` |
| `routes/monitoring.py` | `tests/test_monitoring_calendar.py` |
| `routes/netpractice_admin.py` | (none -- untested) |
| `routes/oncall.py` | `tests/test_oncall.py` |
| `routes/orders.py` | `tests/test_orders.py` |
| `routes/patient.py` | `tests/test_patient_chart.py` |
| `routes/patient_gen.py` | `tests/test_patient_gen.py` |
| `routes/revenue.py` | `tests/test_revenue.py` |
| `routes/telehealth.py` | `tests/test_telehealth.py` |
| `routes/timer.py` | `tests/test_timer.py` |
| `routes/tools.py` | `tests/test_tools.py` |

---

## Models

| Source File | Test Target(s) |
|------------|----------------|
| `models/user.py` | `tests/test_auth.py` |
| `models/patient.py` | `tests/test_patient_chart.py`, `tests/test_clinical_summary.py` |
| `models/schedule.py` | `tests/test_dashboard_schedule.py` |
| `models/billing.py` | `tests/test_billing_engine.py`, `tests/test_billing_unit.py` |
| `models/bonus.py` | `tests/test_bonus_dashboard.py` |
| `models/caregap.py` | `tests/test_caregap_engine.py` |
| `models/monitoring.py` | `tests/test_monitoring_rules.py`, `tests/test_monitoring_calendar.py` |
| `models/lab.py` | `tests/test_labtrack.py` |
| `models/orders.py` | `tests/test_orders.py` |
| `models/inbox.py` | `tests/test_inbox_monitor.py` |
| `models/oncall.py` | `tests/test_oncall.py` |
| `models/ccm.py` | `tests/test_ccm.py` |
| `models/tcm.py` | `tests/test_tcm.py` |
| `models/telehealth.py` | `tests/test_telehealth.py` |
| `models/timer.py` | `tests/test_timer.py` |
| `models/notification.py` | (none -- untested) |
| `models/message.py` | `tests/test_messages.py` |
| `models/calculator.py` | `tests/test_calculators.py` |
| `models/agent.py` | `tests/test_agent_api.py` |

---

## Billing Engine

| Source File | Test Target(s) |
|------------|----------------|
| `billing_engine/engine.py` | `tests/test_billing_engine.py` |
| `billing_engine/base.py` | `tests/test_billing_engine.py`, `tests/test_billing_unit.py` |
| `billing_engine/scoring.py` | `tests/test_billing_unit.py` |
| `billing_engine/payer_routing.py` | `tests/test_billing_unit.py`, `tests/test_billing_engine.py` |
| `billing_engine/stack_builder.py` | `tests/test_billing_unit.py` |
| `billing_engine/rules.py` | `tests/test_billing_rules.py` |
| `billing_engine/detectors/g2211.py` | `tests/test_billing_engine.py::test_g2211_*` |
| `billing_engine/detectors/awv.py` | `tests/test_billing_engine.py::test_awv_*` |
| `billing_engine/detectors/tcm.py` | `tests/test_billing_engine.py::test_tcm_*` |
| `billing_engine/detectors/ccm.py` | `tests/test_billing_engine.py::test_ccm_*` |
| `billing_engine/detectors/bhi.py` | `tests/test_billing_engine.py::test_bhi_*` |
| `billing_engine/detectors/tobacco.py` | `tests/test_billing_engine.py::test_tobacco_*` |
| `billing_engine/detectors/alcohol.py` | `tests/test_billing_engine.py::test_alcohol_*` |
| `billing_engine/detectors/obesity.py` | `tests/test_billing_engine.py::test_obesity_*` |
| `billing_engine/detectors/screening.py` | `tests/test_billing_engine.py::test_screening_*` |
| `billing_engine/detectors/pediatric.py` | `tests/test_billing_engine.py::test_pediatric_*` |
| `billing_engine/detectors/sdoh.py` | `tests/test_billing_engine.py::test_sdoh_*` |
| `billing_engine/detectors/sti.py` | `tests/test_billing_engine.py::test_sti_*` |
| `billing_engine/detectors/rpm.py` | `tests/test_billing_engine.py::test_rpm_*` |
| `billing_engine/detectors/cognitive.py` | `tests/test_billing_engine.py::test_cognitive_*` |
| `billing_engine/detectors/acp.py` | `tests/test_billing_engine.py::test_acp_*` |
| `billing_engine/detectors/cocm.py` | `tests/test_billing_engine.py::test_cocm_*` |
| `billing_engine/detectors/telehealth.py` | `tests/test_billing_engine.py::test_telehealth_*` |
| `billing_engine/detectors/prolonged_service.py` | `tests/test_billing_engine.py::test_prolonged_*` |
| `billing_engine/detectors/em_addons.py` | `tests/test_billing_engine.py::test_em_addons_*` |
| `billing_engine/detectors/vaccine_admin.py` | `tests/test_billing_engine.py::test_vaccine_*` |
| `billing_engine/detectors/chronic_monitoring.py` | `tests/test_billing_engine.py::test_chronic_mon_*` |
| `billing_engine/detectors/care_gaps.py` | `tests/test_billing_engine.py::test_caregap_detector_*` |
| `billing_engine/detectors/preventive.py` | `tests/test_billing_engine.py::test_preventive_*` |
| `billing_engine/detectors/counseling.py` | `tests/test_billing_engine.py::test_counseling_*` |
| `billing_engine/detectors/procedures.py` | `tests/test_billing_engine.py::test_procedures_*` |
| `billing_engine/detectors/misc.py` | `tests/test_billing_engine.py::test_misc_*` |
| `billing_engine/detectors/calculator_billing.py` | `tests/test_billing_engine.py::test_calculator_billing_*` |

---

## Agent

| Source File | Test Target(s) |
|------------|----------------|
| `agent/clinical_summary_parser.py` | `tests/test_clinical_summary.py` |
| `agent/caregap_engine.py` | `tests/test_caregap_engine.py` |
| `agent/inbox_monitor.py` | `tests/test_inbox_monitor.py` |
| `agent/inbox_reader.py` | `tests/test_inbox_monitor.py` |
| `agent/mrn_reader.py` | `tests/test_mrn_reader.py` |
| `agent/note_reformatter.py` | `tests/test_note_reformatter.py` |
| `agent/note_parser.py` | `tests/test_note_reformatter.py` |
| `agent/ocr_helpers.py` | `tests/test_ocr.py` |
| `agent/ac_window.py` | `tests/test_chart_flag.py` |
| `agent/notifier.py` | (none -- untested) |
| `agent/scheduler.py` | (none -- untested) |

---

## Services

| Source File | Test Target(s) |
|------------|----------------|
| `app/services/bonus_calculator.py` | `tests/test_bonus_dashboard.py` |
| `app/services/billing_rules.py` | `tests/test_billing_rules.py` |
| `app/services/calculator_engine.py` | `tests/test_calculators.py` |
| `app/services/immunization_engine.py` | `tests/test_immunization.py` |
| `app/services/monitoring_rule_engine.py` | `tests/test_monitoring_rules.py` |
| `app/services/pricing_service.py` | `tests/test_pricing.py` |
| `app/services/insurer_classifier.py` | `tests/test_insurer_classifier.py` |

---

## Shared / Global (changes here affect everything)

| Source File | When Changed, Run |
|------------|-------------------|
| `app/__init__.py` | `scripts/smoke_test.py` + ALL tests |
| `config.py` | `scripts/smoke_test.py` + ALL tests |
| `models/__init__.py` | `scripts/db_integrity_check.py` + ALL tests |
| `templates/base.html` | `tests/e2e/test_ui_flows.py` (visual check) |
| `static/css/main.css` | Visual inspection only |
| `static/js/main.js` | `tests/e2e/test_ui_flows.py` (E2E) |
| `utils/api_client.py` | `tests/test_api_cache.py` + all API-dependent tests |
| `utils/feature_gates.py` | `tests/test_feature_gates.py` + feature-gated route tests |

---

## JSON Data for detect_changes.py

This section provides the mapping in a format consumable by the detect_changes script:

```python
FILE_TO_BLOCKS = {
    # Routes
    "routes/auth.py": ["tests/test_auth.py"],
    "routes/admin.py": ["tests/test_admin.py", "tests/test_admin_panel.py"],
    "routes/agent_api.py": ["tests/test_agent_api.py"],
    "routes/bonus.py": ["tests/test_bonus_dashboard.py"],
    "routes/calculator.py": ["tests/test_calculators.py"],
    "routes/caregap.py": ["tests/test_caregap_engine.py", "tests/test_caregap_comprehensive.py"],
    "routes/ccm.py": ["tests/test_ccm.py"],
    "routes/dashboard.py": ["tests/test_dashboard_schedule.py"],
    "routes/inbox.py": ["tests/test_inbox_monitor.py"],
    "routes/intelligence.py": ["tests/test_morning_briefing.py"],
    "routes/labtrack.py": ["tests/test_labtrack.py"],
    "routes/medref.py": ["tests/test_medref.py"],
    "routes/message.py": ["tests/test_messages.py"],
    "routes/monitoring.py": ["tests/test_monitoring_calendar.py"],
    "routes/oncall.py": ["tests/test_oncall.py"],
    "routes/orders.py": ["tests/test_orders.py"],
    "routes/patient.py": ["tests/test_patient_chart.py"],
    "routes/revenue.py": ["tests/test_revenue.py"],
    "routes/telehealth.py": ["tests/test_telehealth.py"],
    "routes/timer.py": ["tests/test_timer.py"],
    "routes/tools.py": ["tests/test_tools.py"],
    # Models
    "models/billing.py": ["tests/test_billing_engine.py", "tests/test_billing_unit.py"],
    "models/bonus.py": ["tests/test_bonus_dashboard.py"],
    "models/patient.py": ["tests/test_patient_chart.py", "tests/test_clinical_summary.py"],
    "models/caregap.py": ["tests/test_caregap_engine.py"],
    "models/monitoring.py": ["tests/test_monitoring_rules.py", "tests/test_monitoring_calendar.py"],
    # Billing engine
    "billing_engine/engine.py": ["tests/test_billing_engine.py"],
    "billing_engine/base.py": ["tests/test_billing_engine.py", "tests/test_billing_unit.py"],
    "billing_engine/scoring.py": ["tests/test_billing_unit.py"],
    "billing_engine/payer_routing.py": ["tests/test_billing_engine.py", "tests/test_billing_unit.py"],
    "billing_engine/rules.py": ["tests/test_billing_rules.py"],
    # Agent
    "agent/clinical_summary_parser.py": ["tests/test_clinical_summary.py"],
    "agent/caregap_engine.py": ["tests/test_caregap_engine.py"],
    "agent/mrn_reader.py": ["tests/test_mrn_reader.py"],
    "agent/note_reformatter.py": ["tests/test_note_reformatter.py"],
    # Services
    "app/services/bonus_calculator.py": ["tests/test_bonus_dashboard.py"],
    "app/services/calculator_engine.py": ["tests/test_calculators.py"],
    "app/services/billing_rules.py": ["tests/test_billing_rules.py"],
    # Global (changes trigger full suite)
    "app/__init__.py": ["tests/"],
    "config.py": ["tests/"],
    "models/__init__.py": ["tests/"],
}
```
