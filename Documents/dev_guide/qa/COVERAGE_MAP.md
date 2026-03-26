# CareCompanion -- Coverage Map

> **Generated:** 03-24-26
> **Purpose:** Maps every source file to its test file(s) and identifies untested files.
> **Legend:** TESTED = has dedicated test file | PARTIAL = tested indirectly | NONE = no test coverage

---

## Route Files

| Source File | Test File(s) | Coverage |
|------------|-------------|----------|
| routes/auth.py | tests/test_auth.py | TESTED |
| routes/admin.py | tests/test_admin.py, tests/test_admin_panel.py | TESTED |
| routes/admin_benchmarks.py | tests/test_benchmarks.py | TESTED |
| routes/admin_med_catalog.py | tests/test_med_catalog.py | PARTIAL |
| routes/admin_rules_registry.py | tests/test_monitoring_rules.py | PARTIAL |
| routes/agent_api.py | tests/test_agent_api.py | TESTED |
| routes/ai_api.py | tests/test_ai_assistant.py | TESTED |
| routes/bonus.py | tests/test_bonus_dashboard.py | TESTED |
| routes/calculator.py | tests/test_calculators.py | TESTED |
| routes/campaigns.py | tests/test_billing_campaigns.py | PARTIAL |
| routes/caregap.py | tests/test_caregap_engine.py, tests/test_caregap_comprehensive.py | TESTED |
| routes/ccm.py | tests/test_ccm.py | TESTED |
| routes/daily_summary.py | tests/test_daily_summary.py | TESTED |
| routes/dashboard.py | tests/test_dashboard_schedule.py | TESTED |
| routes/help.py | tests/test_help_guide.py | PARTIAL |
| routes/inbox.py | tests/test_inbox_monitor.py | PARTIAL |
| routes/intelligence.py | tests/test_morning_briefing.py | TESTED |
| routes/labtrack.py | tests/test_labtrack.py | TESTED |
| routes/medref.py | tests/test_medref.py | TESTED |
| routes/message.py | tests/test_messages.py | TESTED |
| routes/metrics.py | tests/test_metrics.py | PARTIAL |
| routes/monitoring.py | tests/test_monitoring_calendar.py | TESTED |
| routes/netpractice_admin.py | (none) | NONE |
| routes/oncall.py | tests/test_oncall.py | TESTED |
| routes/orders.py | tests/test_orders.py | TESTED |
| routes/patient.py | tests/test_patient_chart.py | TESTED |
| routes/patient_gen.py | tests/test_patient_gen.py | PARTIAL |
| routes/revenue.py | tests/test_revenue.py | TESTED |
| routes/telehealth.py | tests/test_telehealth.py | TESTED |
| routes/timer.py | tests/test_timer.py | TESTED |
| routes/tools.py | tests/test_tools.py | TESTED |

---

## Models

| Source File | Test File(s) | Coverage |
|------------|-------------|----------|
| models/user.py | tests/test_auth.py | PARTIAL |
| models/patient.py | tests/test_patient_chart.py, tests/test_clinical_summary.py | TESTED |
| models/schedule.py | tests/test_dashboard_schedule.py | PARTIAL |
| models/billing.py | tests/test_billing_engine.py (NEW), tests/test_billing_unit.py | TESTED |
| models/bonus.py | tests/test_bonus_dashboard.py | TESTED |
| models/caregap.py | tests/test_caregap_engine.py | TESTED |
| models/monitoring.py | tests/test_monitoring_rules.py | TESTED |
| models/lab.py | tests/test_labtrack.py | PARTIAL |
| models/orders.py | tests/test_orders.py | TESTED |
| models/inbox.py | tests/test_inbox_monitor.py | PARTIAL |
| models/oncall.py | tests/test_oncall.py | TESTED |
| models/ccm.py | tests/test_ccm.py | TESTED |
| models/tcm.py | tests/test_tcm.py | TESTED |
| models/telehealth.py | tests/test_telehealth.py | PARTIAL |
| models/timer.py | tests/test_timer.py | PARTIAL |
| models/notification.py | (none) | NONE |
| models/message.py | tests/test_messages.py | PARTIAL |
| models/calculator.py | tests/test_calculators.py | PARTIAL |
| models/agent.py | tests/test_agent_api.py | PARTIAL |
| models/tools.py | tests/test_tools.py | PARTIAL |

---

## Billing Engine

| Source File | Test File(s) | Coverage |
|------------|-------------|----------|
| billing_engine/engine.py | tests/test_billing_engine.py (NEW) | TESTED |
| billing_engine/base.py | tests/test_billing_unit.py | PARTIAL |
| billing_engine/scoring.py | tests/test_billing_unit.py | PARTIAL |
| billing_engine/payer_routing.py | tests/test_billing_unit.py | PARTIAL |
| billing_engine/stack_builder.py | tests/test_billing_unit.py | PARTIAL |
| billing_engine/rules.py | tests/test_billing_rules.py | TESTED |
| billing_engine/detectors/*.py (27) | tests/test_billing_engine.py (NEW) | TESTED |

---

## Agent

| Source File | Test File(s) | Coverage |
|------------|-------------|----------|
| agent/ac_window.py | tests/test_chart_flag.py | PARTIAL |
| agent/ac_interact.py | tests/test_ac_automation.py | PARTIAL |
| agent/clinical_summary_parser.py | tests/test_clinical_summary.py | TESTED |
| agent/caregap_engine.py | tests/test_caregap_engine.py | TESTED |
| agent/inbox_monitor.py | tests/test_inbox_monitor.py | TESTED |
| agent/inbox_reader.py | tests/test_inbox_monitor.py | PARTIAL |
| agent/mrn_reader.py | tests/test_mrn_reader.py | TESTED |
| agent/notifier.py | (none) | NONE |
| agent/note_reformatter.py | tests/test_note_reformatter.py | TESTED |
| agent/note_parser.py | tests/test_note_reformatter.py | PARTIAL |
| agent/ocr_helpers.py | tests/test_ocr.py | TESTED |
| agent/scheduler.py | (none) | NONE |
| agent/eod_checker.py | tests/test_eod.py | PARTIAL |

---

## Services

| Source File | Test File(s) | Coverage |
|------------|-------------|----------|
| app/services/bonus_calculator.py | tests/test_bonus_dashboard.py | TESTED |
| app/services/billing_rules.py | tests/test_billing_rules.py | TESTED |
| app/services/calculator_engine.py | tests/test_calculators.py | TESTED |
| app/services/immunization_engine.py | tests/test_immunization.py | TESTED |
| app/services/monitoring_rule_engine.py | tests/test_monitoring_rules.py | TESTED |
| app/services/pricing_service.py | tests/test_pricing.py | TESTED |
| app/services/insurer_classifier.py | tests/test_insurer_classifier.py | TESTED |
| app/services/api/*.py (28 modules) | tests/test_api_services.py | PARTIAL |

---

## Utilities

| Source File | Test File(s) | Coverage |
|------------|-------------|----------|
| utils/api_client.py | tests/test_api_cache.py | TESTED |
| utils/feature_gates.py | tests/test_feature_gates.py | TESTED |
| utils/ahk_generator.py | (none) | NONE |
| utils/phi_scrub.py | tests/test_phi_scrubbing.py (NEW) | **DOES NOT EXIST YET** |

---

## Scripts

| Source File | Test File(s) | Coverage |
|------------|-------------|----------|
| scripts/seed_test_data.py | (manual execution) | NONE |
| scripts/generate_test_xmls.py | (manual execution) | NONE |
| scripts/seed_master_orders.py | (manual execution) | NONE |

---

## Summary

| Category | Files | Tested | Partial | None |
|----------|-------|--------|---------|------|
| Routes | 31 | 22 | 7 | 2 |
| Models | 20 | 10 | 8 | 2 |
| Billing Engine | 33 | 3 | 4 | 0 |
| Agent | 12 | 6 | 4 | 2 |
| Services | 30+ | 8 | 1 | 0 |
| Utilities | 4 | 2 | 0 | 2 |
| Scripts | 3 | 0 | 0 | 3 |
| **Total** | **133+** | **51** | **24** | **11** |

---

## Priority Gaps (Untested Files That Matter)

1. **utils/phi_scrub.py** -- DOES NOT EXIST (BUG-001)
2. **agent/notifier.py** -- Handles Pushover; no PHI leak test
3. **agent/scheduler.py** -- APScheduler job coordinator; no test
4. **routes/netpractice_admin.py** -- NetPractice admin panel; no test
5. **models/notification.py** -- No dedicated test
