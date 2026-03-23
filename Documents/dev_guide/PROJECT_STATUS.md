# CareCompanion Ã¢â‚¬â€ Project Status
# File: PROJECT_STATUS.md
# Updated: 2026-03-22
# Version: 1.1.3

---

## Current Build State

| Property | Value |
|---|---|
| App Version | 1.1.3 |
| Python | 3.11 |
| Framework | Flask 3.1.3 + SQLAlchemy 2.0.48 + SQLite |
| Packager | PyInstaller (single-folder .exe via `build.py`) |
| Platform | Windows 11 Pro (1920Ãƒâ€”1080, dual monitor) |
| Deployment | USB zip Ã¢â€ â€™ work PC, auto-start via `.bat` |
| Dev Machine | Local dev with venv, VS Code + GitHub Copilot |
| Work PC Name | FPA-D-NP-DENTON |

---

## Architecture Summary

```
Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
Ã¢â€â€š  Flask Web Server (port 5000)                           Ã¢â€â€š
Ã¢â€â€š  Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ 19 route blueprints (auth, dashboard, patient, Ã¢â‚¬Â¦)  Ã¢â€â€š
Ã¢â€â€š  Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ 59+ SQLAlchemy models (SQLite)                     Ã¢â€â€š
Ã¢â€â€š  Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ Jinja2 templates + vanilla JS frontend             Ã¢â€â€š
Ã¢â€â€š  Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ Role-based access: admin / provider / ma           Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ billing_engine/ (27 detectors, 72 rules, 122 CPT) Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â¤
Ã¢â€â€š  Background Agent (agent_service.py, port 5001)         Ã¢â€â€š
Ã¢â€â€š  Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ System tray (pystray)                              Ã¢â€â€š
Ã¢â€â€š  Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ APScheduler (interval + cron jobs)                 Ã¢â€â€š
Ã¢â€â€š  Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ Amazing Charts automation (PyAutoGUI + OCR)        Ã¢â€â€š
Ã¢â€â€š  Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ NetPractice scraping (Playwright + CDP)            Ã¢â€â€š
Ã¢â€â€š  Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ Inbox monitoring + clinical summary parsing        Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ Watchdog file watcher                              Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â¤
Ã¢â€â€š  External Integrations                                  Ã¢â€â€š
Ã¢â€â€š  Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ NIH RxNorm API (drug data, cached in RxNormCache)  Ã¢â€â€š
Ã¢â€â€š  Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ NIH ICD-10 API (diagnosis codes, Icd10Cache)       Ã¢â€â€š  Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ NIH UMLS API (Ã¢Å“â€¦ licensed 2026-03-19, UmlsCache)   |
  Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ SNOMED CT (via UMLS sabs=SNOMEDCT_US)              |
  Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ VSAC (value sets, VsacValueSetCache)               |Ã¢â€â€š  Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ Pushover API (mobile push notifications)           Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ Tailscale (remote phone access)                    Ã¢â€â€š
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ
```

---

## Registered Blueprints (20)

| Blueprint | Module | Purpose |
|---|---|---|
| auth_bp | routes/auth.py | Login, logout, session, user CRUD |
| admin_bp | routes/admin.py | Admin panel, user management |
| agent_api_bp | routes/agent_api.py | Agent Ã¢â€ â€ server communication |
| dashboard_bp | routes/dashboard.py | Home dashboard, My Patients, schedule |
| timer_bp | routes/timer.py | Time tracking per encounter |
| inbox_bp | routes/inbox.py | Inbox snapshots, message viewer |
| oncall_bp | routes/oncall.py | On-call notes, handoff links |
| orders_bp | routes/orders.py | Order sets, master orders |
| medref_bp | routes/medref.py | Medical reference links |
| labtrack_bp | routes/labtrack.py | Lab result tracking |
| caregap_bp | routes/caregap.py | Care gap rules, USPSTF screening |
| metrics_bp | routes/metrics.py | Analytics, usage metrics |
| tools_bp | routes/tools.py | Utility tools (reformatter, etc.) |
| np_admin_bp | routes/netpractice_admin.py | NetPractice administration |
| patient_bp | routes/patient.py | Patient chart, demographics, meds |
| ai_api_bp | routes/ai_api.py | AI assistant integration |
| intel_bp | routes/intelligence.py | Clinical intelligence endpoints |
| patient_gen_bp | routes/patient_gen.py | Patient generation utilities |
| message_bp | routes/message.py | Secure messaging, recurring messages |
| calculator_bp | routes/calculator.py | Clinical calculator library + risk tools |

---

## Database Models (59+)

### Core
- `User` Ã¢â‚¬â€ login credentials, role (`admin`/`provider`/`ma`), preferences

### Patient Data
- `PatientRecord` Ã¢â‚¬â€ demographics (MRN, name, DOB, sex)
- `PatientMedication` Ã¢â‚¬â€ medications with `rxnorm_cui` column
- `PatientDiagnosis` Ã¢â‚¬â€ diagnoses with ICD-10 codes
- `PatientAllergy`, `PatientImmunization`, `PatientVitals`
- `PatientSpecialist`, `PatientNoteDraft`

### Caching
- `Icd10Cache` Ã¢â‚¬â€ cached ICD-10 lookups (keyed by code, permanent)
- `RxNormCache` Ã¢â‚¬â€ cached RxNorm drug data (keyed by rxcui, permanent)

### Clinical Workflow
- `Schedule` Ã¢â‚¬â€ daily appointment schedule
- `CareGap`, `CareGapRule` Ã¢â‚¬â€ USPSTF screening rules + patient gaps
- `LabTrack`, `LabResult`, `LabPanel` Ã¢â‚¬â€ lab result tracking
- `OrderSet`, `OrderItem`, `MasterOrder` Ã¢â‚¬â€ clinical order sets
- `OrderSetVersion`, `OrderExecution`, `OrderExecutionItem`
- `MedicationEntry` Ã¢â‚¬â€ medication reference
- `Tickler` Ã¢â‚¬â€ follow-up reminders

### Billing
- `BillingOpportunity` Ã¢â‚¬â€ per-patient per-visit opportunity (category, code, priority, checklist, actioned status)
- `BillingRule` Ã¢â‚¬â€ 72 seed rules (opportunity_code, cpt_codes, payer_types, estimated_revenue, documentation_checklist, is_active toggle)

### Clinical Calculators (Phase 31)
- `CalculatorResult` Ã¢â‚¬â€ computed risk scores per patient (calculator_key, score_value, score_label, score_detail JSON, input_snapshot JSON, is_current, data_source)

### Communication
- `InboxSnapshot`, `InboxItem` Ã¢â‚¬â€ inbox message snapshots
- `OnCallNote`, `HandoffLink` Ã¢â‚¬â€ on-call handoff data
- `Notification` Ã¢â‚¬â€ push notifications (Pushover)
- `DelayedMessage` Ã¢â‚¬â€ scheduled messages

### Operations
- `AuditLog` Ã¢â‚¬â€ request audit trail (auto-logged)
- `TimeLog` Ã¢â‚¬â€ encounter time tracking
- `AgentLog`, `AgentError` Ã¢â‚¬â€ background agent logs
- `ReformatLog` Ã¢â‚¬â€ text reformatting history

---

## Migration Files (40)

All migrations are idempotent (`ALTER TABLE Ã¢â‚¬Â¦ ADD COLUMN` with `try/except` or column-existence checks). Safe to re-run.

**Root directory (4):**

| Migration | Purpose |
|---|---|
| migrate_add_dismissal_reason.py | Billing opportunity dismissal reasons |
| migrate_add_dotphrase_sharing.py | Shared dot-phrase library |
| migrate_add_notification_priority.py | Notification priority levels |
| migrate_add_template_sharing.py | Shared result templates |

**migrations/ directory (35):**

| Migration | Purpose |
|---|---|
| migrate_phase2_columns.py | Phase 2 widget schema |
| migrate_phase4_columns.py | Phase 4 feature columns |
| migrate_cl21.py | CareLink 2.1 schema |
| migrate_add_ac_columns.py | Amazing Charts integration |
| migrate_add_ai_columns.py | AI feature columns |
| migrate_add_api_cache_tables.py | API response cache tables |
| migrate_add_awv_checklist.py | AWV interactive checklist |
| migrate_add_billing_models.py | Billing opportunity + rule models |
| migrate_add_billing_rules.py | Billing rule seed data |
| migrate_add_billing_type_width.py | Billing type column width |
| migrate_add_bookmarks.py | Patient chart bookmarks |
| migrate_add_caregap_columns.py | Care gap tracking |
| migrate_add_chart_columns.py | Chart feature columns |
| migrate_add_claim_columns.py | Patient claim data |
| migrate_add_escalation_columns.py | Alert escalation tracking |
| migrate_add_forward_columns.py | Message forwarding |
| migrate_add_icd10_cache.py | ICD-10 cache table |
| migrate_add_insurer_type.py | Patient insurer type field |
| migrate_add_labtrack_columns.py | Lab tracking columns |
| migrate_add_macros.py | AutoHotkey macro library |
| migrate_add_master_order_cpt.py | CPT codes on orders |
| migrate_add_medentry_review_cols.py | Medication entry review columns |
| migrate_add_ndc_to_rxnorm_cache.py | NDCÃ¢â€ â€™RxNorm mapping cache |
| migrate_add_nlm_conditions_cache.py | NLM conditions cache |
| migrate_add_np_columns.py | NetPractice columns |
| migrate_add_orderset_columns.py | Order set columns |
| migrate_add_patient_sex.py | Patient sex demographic |
| migrate_add_recurring_messages.py | Recurring message scheduling |
| migrate_add_referral_specialty_fields.py | Specialty referral fields |
| migrate_add_result_templates.py | Result response templates |
| migrate_add_rxnorm_cache.py | RxNorm cache table |
| migrate_add_shared_pa.py | Shared prior authorization library |
| migrate_add_timer_columns.py | Timer feature columns |
| migrate_add_vsac_cache.py | VSAC value set cache |
| migrate_billing_opp_expansion.py | Billing opportunity expanded columns |
| migrate_seed_billing_rules.py | Seed billing rules (72 rules) |
| migrate_add_calculator_results.py | CalculatorResult table (Phase 31) |

---

## What's Done (Phase Completion Summary)

### Clinical Calculator System (Phases 31Ã¢â‚¬â€œ38) Ã¢Å“â€¦ Ã¢â‚¬â€ *Added 2026-03-22*
- [x] Phase 31 Ã¢â‚¬â€ Calculator Engine & Data Model (`CalculatorResult`, `CalculatorEngine`, 25 tests)
- [x] Phase 32 Ã¢â‚¬â€ Auto-Score Widget on Patient Chart (Risk Scores widget, nightly pre-compute, 10 tests)
- [x] Phase 33 Ã¢â‚¬â€ Risk Tool Picker (19-calculator registry, 5-route `calculator_bp`, 15 tests)
- [x] Phase 34 Ã¢â‚¬â€ Top Menu Integration (References menu entry, Ctrl+Shift+K shortcut, chart tab, 5 tests)
- [x] Phase 35 Ã¢â‚¬â€ Trend Monitoring & Score History (sparklines, threshold alerts, care-gap linkage, 10 tests)
- [x] Phase 36 Ã¢â‚¬â€ Questionnaire Calculator Forms (GAD-7, C-SSRS, AUDIT-C, Wells DVT, 12 tests)
- [x] Phase 37 Ã¢â‚¬â€ Semi-Auto Pre-Population UX (prefill indicators, context hints, 8 tests)
- [x] Phase 38 Ã¢â‚¬â€ Billing Integration (CalculatorBillingDetector, 9 triggers, 4 phrase seeds, 10 tests)
- **95 new tests** | **1 new model** | **1 new blueprint** | **1 new billing detector** | **27 billing detectors total**

---

## What's Done (CL23 Beta Readiness Ã¢â‚¬â€ Part 1)

### Phase 0 Ã¢â‚¬â€ Critical Bugs Ã¢Å“â€¦
- [x] 0.1 Admin send-notification endpoint fixed (JSON body, field alignment)
- [x] 0.2 Patient "unknown" name on claim fixed
- [x] 0.3 RxNorm API integration Ã¢â‚¬â€ `RxNormCache` model, `rxnorm_cui` on `PatientMedication`, `utils/api_client.py`, enrichment pipeline

### Phase 1 Ã¢â‚¬â€ Data Correctness Ã¢Å“â€¦
- [x] 1.1 Full MRN displayed everywhere
- [x] 1.2 DOB format MM/DD/YYYY
- [x] 1.3 Sex/gender in chart header
- [x] 1.4 Demographics edit UI
- [x] 1.5 ICD-10 auto-lookup on chart load
- [x] 1.6 Care gap sex filter

### Phase 2 Ã¢â‚¬â€ Widget System Ã¢Å“â€¦
- [x] 2.1 True freeform default (no snap)
- [x] 2.2 Per-widget settings button
- [x] 2.3 Scrollable widget content
- [x] 2.4 Layout persists per-user

### Phase 3 Ã¢â‚¬â€ Context Menu & Clipboard Ã¢Å“â€¦
- [x] 3.1 Enhanced right-click on links
- [x] 3.2 Right-click on selected text
- [x] 3.3 Text selection on admin pages

### Phase 4 Ã¢â‚¬â€ Feature Completions Ã¢Å“â€¦
- [x] 4.1 USPSTF enhancements (billing codes, due/overdue filter)
- [x] 4.2 Order set redesign (popup flow, master order browser)
- [x] 4.3 Notification admin rebuild
- [x] 4.4 Care gaps spreadsheet for claimed patients
- [x] 4.5 Diagnoses copy with column picker
- [x] 4.6 Admin deactivation scheduling
- [x] 4.7 Collect user email

### Phase 5 Ã¢â‚¬â€ UI Polish Ã¢Å“â€¦
- [x] 5.1 Version Ã¢â€ â€™ user popover only
- [x] 5.2 Center dashboard appointment banner
- [x] 5.3 Remove redundant "Open" button
- [x] 5.4 Refresh button next to notification bell
- [x] 5.5 AI panel minimize/snap-back
- [x] 5.6 My Patients live search filter
- [x] 5.7 Provider name format verified

### Code Cleanup Ã¢Å“â€¦
- [x] models/__init__.py Ã¢â‚¬â€ all models exported (Notification, Icd10Cache, RxNormCache added)
- [x] carecompanion.spec Ã¢â‚¬â€ routes.ai_api added to hiddenimports
- [x] requirements.txt Ã¢â‚¬â€ psutil added
- [x] .gitignore Ã¢â‚¬â€ dist/, build/, *.ico, *.code-workspace added
- [x] 9 unused imports cleaned across 6 route files
- [x] 0 compile errors across all Python files

---

## What's Next Ã¢â‚¬â€ Current Status

### final_plan.md Ã¢â‚¬â€ Pre-Beta Deployment Plan Ã¢Å“â€¦ Complete
7-phase pre-beta deployment plan executed in full:
- **Phase 0:** UpToDate service + config wiring
- **Phase 1:** Care Gap print handout + toggle + trigger-type UI
- **Phase 2:** Provider name placeholder + F10 keyboard audit
- **Phase 3:** E2E integration test suite (75 tests across 5 files)
- **Phase 4:** `deploy_check.py` automated pre-flight checker (11 sections)
- **Phase 5:** Infrastructure smoke test tools (USB, backup/restore, connectivity)
- **Phase 6:** `verify_all.py` interactive verification orchestrator (5 stages, 38 URL smoke tests, 32 manual checks)
- **Phase 7:** Full regression (127 main + 42 pytest + 140 custom = 309 checks, all passing), docs updated
- **Bug fixes:** Dashboard `timedelta` scope collision, scheduler `**kwargs` missing
- **New files:** 5 tools (`deploy_check.py`, `usb_smoke_test.py`, `backup_restore_test.py`, `connectivity_test.py`, `verify_all.py`), 8 test files (98 tests), `Deployment_Guide.md` updated

### Next Step
Run `python tools/verify_all.py` on FPA-D-NP-DENTON for the interactive verification session, then Tier-1 beta with real patient data.

### Blocked Ã¢â‚¬â€ Requires External Action
| Item | Blocker | Status |
|------|---------|--------|
| F9 Ã¢â‚¬â€ Pre-visit Chart Prefill | Work PC + Amazing Charts OCR calibration | Agent modules ready, needs hands-on calibration |
| F28a Ã¢â‚¬â€ Click-to-Set MRN Calibration | Work PC required for visual region tool | Diagnostic calibration exists, visual tool not buildable remotely |
| GoodRx API Key | Developer application approval | Code 100% complete, activates automatically on key addition |
| 21.4 Claim Denial Prediction | Historical denial data + ML pipeline | Requires dataset that doesn't exist yet |
| 21.5 Real-Time Eligibility | Clearinghouse API credentials (270/271) | Requires payer/clearinghouse contract |

### Known Configuration Requirements
- `AC_MOCK_MODE = True` in dev config Ã¢â‚¬â€ must flip to `False` for production
- `DEBUG = True` in dev config Ã¢â‚¬â€ must flip to `False` for production
- `SECRET_KEY` is hardcoded in config.py Ã¢â‚¬â€ acceptable for single-user local deploy
- Clinical summary parser depends on AC XML export format Ã¢â‚¬â€ if AC updates, parser may need adjustment
- Tesseract path is machine-specific Ã¢â‚¬â€ must be updated per machine
- Chrome CDP port 9222 required for NetPractice Playwright scraping

### Deployment Steps
- Build with `python build.py --bump patch --notes "CL23 beta" --usb E:`
- Transfer zip to work PC via USB or Google Drive
- Unzip, run `Start_CareCompanion.bat`
- Set `AC_MOCK_MODE = False` and `DEBUG = False` in config.py on work PC
- Update `TESSERACT_PATH` to match work PC Tesseract install location
- Run through `Documents/VERIFICATION_CHECKLIST.md`

### Planned Future Work
- **F30 Ã¢â‚¬â€ Offline Mode** (HIGH complexity): Service Worker + IndexedDB + sync logic
- **Mobile PWA** (MEDIUM): Push subscription, background sync
- **Multi-Provider Scheduling** (MEDIUM): Shared schedule views
- **CI/CD Pipeline** (LOW): GitHub Actions for automated test runs
- **FHIR/HL7 Integration** (HIGH): Only if AC or replacement EHR supports it
- **Billing Engine payer-specific rules**: Stubs exist in payer_routing.py 
---

## Running Plan 3 Ã¢â‚¬â€ Part 1 Ã¢Å“â€¦ (Completed 2026-03-21)

Chrome 136 compatibility, manual schedule entry, paste-from-OCR, and AC data collection.

### Phase 1 Ã¢â‚¬â€ Chrome 136 Debug Profile Infrastructure Ã¢Å“â€¦
- `config.py` + `utils/chrome_launcher.py` Ã¢â‚¬â€ dedicated `--user-data-dir` for CDP
- `launcher.py` Ã¢â‚¬â€ auto-launch on startup
- All 3 scrapers updated: CDP Ã¢â€ â€™ auto-launch Ã¢â€ â€™ retry Ã¢â€ â€™ headless fallback
- Admin NP page: Chrome status card with launch button

### Phase 2 Ã¢â‚¬â€ Manual Patient Schedule Entry Ã¢Å“â€¦
- `POST /api/schedule/add`, `DELETE /api/schedule/<id>` endpoints
- Add Patient modal on dashboard, manual row styling

### Phase 3 Ã¢â‚¬â€ Paste-from-OCR Bulk Schedule Import Ã¢Å“â€¦
- `POST /api/schedule/parse-text` Ã¢â‚¬â€ regex parser (time, name, MRN, visit type)
- Paste Schedule modal with confidence indicators and preview table

### Phase 4 Ã¢â‚¬â€ Data Collection with Takeover Warning Ã¢Å“â€¦
- `POST /api/schedule/<id>/collect`, `GET /api/schedule/<id>/collect-status`
- Background thread Ã¢â€ â€™ AC pipeline (open chart Ã¢â€ â€™ export XML Ã¢â€ â€™ parse Ã¢â€ â€™ store)
- Takeover warning modal, Actions column with Collect/Delete buttons

### Phase 5 Ã¢â‚¬â€ Integration Testing & Polish Ã¢Å“â€¦
- `tests/test_schedule_manual.py` (9 tests), `tests/test_chrome_launcher.py` (6 tests)
- Edge cases: tab normalization, duplicate detection, Chrome PATH fallback
- `config.example.py` updated, admin NP setup docs added

> **Parts 2 & 3 (Phases 6Ã¢â‚¬â€œ29)** outlined in `Documents/dev_guide/RUNNING_PLAN.md`.

---

## Ongoing Development Ã¢â‚¬â€ Phase Roadmap

### Next: Phase 6+ Features (from Development Guide)
- **API Intelligence (Phase 10A/10B)** Ã¢â‚¬â€ Ã¢Å“â€¦ 16+ API clients built in `app/services/api/`. UMLS licensed 2026-03-19. Intelligence endpoints implemented: lab_interpretation, drug_safety, guidelines, formulary_gaps, patient_education. RxCUIÃ¢â€ â€™RxClassCache enrichment added (14.5).
- **Billing Capture Engine** Ã¢â‚¬â€ Ã¢Å“â€¦ Phase 13 Ã¢â€ â€™ Phase 19 refactor complete: modular `billing_engine/` package with 26 auto-discovered detector modules, 72 seed rules, 122 CPT/HCPCS codes. `BillingCaptureEngine` orchestrator, `SharedPatientContext`, payer routing, priority sort, dedup. Provider-toggleable via `/settings/billing`. Pre-visit billing job runs nightly.
- **Running Plan 4 (Phases 1Ã¢â‚¬â€œ14)** Ã¢â‚¬â€ Ã¢Å“â€¦ Complete: Double-booking detection, guideline review admin, PDMP briefing, specialty referrals (21 specialties), macro auto-sync, AWV checklist, template sharing, notification priorities, starter pack import, new-med education triggers, document refresh, PROJECT_STATUS overhaul. 150 new tests added.
- **AI Assistant Expansion** Ã¢â‚¬â€ clinical decision support, documentation assistance
- **Enhanced Scheduling** Ã¢â‚¬â€ WebPractice bidirectional sync, patient reminders
- **Reporting** Ã¢â‚¬â€ provider productivity, care gap compliance, panel management

### Multi-Year Horizon
- Migration from Amazing Charts if EHR changes
- Multi-provider support (currently single-provider optimized)
- FHIR/HL7 integration if AC or replacement EHR supports it
- Potential cloud component for cross-device sync (currently local-only by design for HIPAA)

---

## Dependencies (41 packages)

### Core Framework
| Package | Version |
|---|---|
| Flask | 3.1.3 |
| Flask-SQLAlchemy | 3.1.1 |
| Flask-Login | 0.6.3 |
| Flask-Bcrypt | 1.0.1 |
| SQLAlchemy | 2.0.48 |
| Werkzeug | 3.1.6 |
| Jinja2 | 3.1.6 |

### Desktop Automation
| Package | Version |
|---|---|
| PyAutoGUI | 0.9.54 |
| pytesseract | 0.3.13 |
| Pillow | 12.1.1 |
| pywin32 | 311 |
| psutil | 7.0.0 |
| pyperclip | 1.11.0 |

### Browser Automation
| Package | Version |
|---|---|
| Playwright | 1.58.0 |

### Background Services
| Package | Version |
|---|---|
| APScheduler | 3.11.0 |
| pystray | 0.19.5 |
| watchdog | 6.0.0 |

### Notifications & UI
| Package | Version |
|---|---|
| plyer | 2.1.0 |
| pywebview | 5.3.2 |

### Security
| Package | Version |
|---|---|
| bcrypt | 5.0.0 |
| cryptography | 46.0.5 |

---

## Feature Registry

> **Single source of truth for feature status.** Update this table — not the Dev Guide checklist — when features change status. Columns: ID, Feature name, Build status, Tested (AI/unit), User-verified (manual QA), Plan reference, Notes.

| ID | Feature | Status | Tested | Verified | Plan Ref | Notes |
|----|---------|--------|--------|----------|----------|-------|
| F1 | Core Platform (auth, dashboard, base UI) | ✅ Complete | ✅ | ⬜ | Phase 1 | 20+ blueprints, dark mode, auto-lock, agent health |
| F2 | Background Agent & Scheduler | ✅ Complete | ✅ | ⬜ | Phase 1 | System tray, APScheduler, heartbeat, crash recovery |
| F3 | NetPractice Schedule Scraper | ✅ Complete | ✅ | ⬜ | Phase 2 | Playwright-based, Chrome 136 debug profile |
| F4 | Today View & Timer | ✅ Complete | ✅ | ⬜ | Phase 2 | Timer, manual entry, paste-from-OCR, double-booking (RP4) |
| F5 | Inbox Monitor | ✅ Complete | ✅ | ⬜ | Phase 2 | OCR-based, snapshot diffs, priority detection |
| F6 | Clinical Summary Parser (CDA XML) | ✅ Complete | ✅ | ⬜ | Phase 2 | Patient chart, vitals, meds, diagnoses, new-med education (RP4) |
| F7 | On-Call Note Keeper | ✅ Complete | ✅ | ⬜ | Phase 3 | CRUD, export, callback tracking |
| F8 | Order Set Manager | ✅ Complete | ✅ | ⬜ | Phase 3 | Sets, items, versions, execution tracking |
| F9 | Chart Prefill (AC Automation) | ⏸️ AC-Blocked | ⬜ | ⬜ | Phase 3 | AC Calibration Wizard built (UX-17); awaits live AC testing |
| F10 | Medication Reference | ✅ Complete | ✅ | ⬜ | Phase 3 | Drug lookup, interactions, RxNorm, guideline review (RP4) |
| F11 | Lab Tracker | ✅ Complete | ✅ | ⬜ | Phase 4 | Per-patient tracking, trends, panels |
| F12 | Care Gap Tracker | ✅ Complete | ✅ | ⬜ | Phase 5 | Age/sex rules, admin editor, gap alerts |
| F13 | Metrics Dashboard | ✅ Complete | ✅ | ⬜ | Phase 4 | Productivity, on-call, billing metrics |
| F14 | Patient Roster | ✅ Complete | ✅ | ⬜ | Phase 4 | Search, chart links, specialist tracking |
| F15 | Billing Tools | ✅ Complete | ✅ | ⬜ | Phase 5 | CPT/ICD-10 lookup, billing rules, opportunities |
| F16 | Coding Suggester | ✅ Complete | ✅ | ⬜ | Phase 5 | ICD-10 search, favorites, AWV checklist (RP4) |
| F17 | Care Gap Alerts (CDS) | ✅ Complete | ✅ | ⬜ | Phase 5 | HealthFinder API, CDC immunizations |
| F18 | Delayed Message Sender | ✅ Complete | ✅ | ⬜ | Phase 6 | Queue, compose, cancel, scheduler job |
| F19 | Result Response Templates | ✅ Complete | ✅ | ⬜ | Phase 6 | 13 templates, 5 tiers, shared library (RP4) |
| F20 | End-of-Day Checker | ✅ Complete | ✅ | ⬜ | Phase 6 | 5-category checklist, scheduler, Pushover alerts |
| F21 | Push Notification System | ✅ Complete | ✅ | ⬜ | Phase 7 | Pushover, quiet hours, notification history |
| F22 | Morning Briefing | ✅ Complete | ✅ | ⬜ | Phase 7 | Schedule + weather + care gaps + inbox summary |
| F22a | Commute Mode (TTS) | ✅ Complete | ✅ | ⬜ | Phase 7 | Web Speech API, hands-free briefing |
| F23 | AutoHotkey Macro Library | ✅ Complete | ✅ | ⬜ | Phase 7 | CRUD, dot phrases, AHK generator, auto-sync (RP4) |
| F24 | Follow-Up Tickler System | ✅ Complete | ✅ | ⬜ | Phase 7 | Due dates, snooze, assign, recurring |
| F25 | Prior Authorization Tracker | ✅ Complete | ✅ | ⬜ | Phase 7 | PA forms, status tracking, PDMP flag (RP4) |
| F26 | Referral Letter Generator | ✅ Complete | ✅ | ⬜ | Phase 7 | Templates, specialist directory, 21 specialties (RP4) |
| F27 | Note Reformatter | ✅ Complete | ✅ | ⬜ | Phase 9 | Reformat logs, flagged items |
| F28 | Provider Onboarding Wizard | ✅ Complete | ✅ | ⬜ | Phase 8 | 5-step wizard, skip support, starter pack (RP4) |
| F29 | Admin Tools | ✅ Complete | ✅ | ⬜ | Phase 8 | User mgmt, config, sitemap, updates |
| F30 | Offline Mode | 🔲 Not Started | ⬜ | ⬜ | Phase 8 | Requires Service Worker + IndexedDB |
| F31 | AI Assistant Integration | ✅ Complete | ✅ | ⬜ | Phase 9 | OpenAI/Anthropic/xAI, HIPAA ack |
| F32 | Clinical Calculators | ✅ Complete | ✅ | ⬜ | Phases 31–38 | 48 calculators, auto-score, risk tools, billing integration |
| F33 | UX Infrastructure Overhaul | ✅ Complete | ✅ | ⬜ | UX Audit | 14 items: double-submit guard, 401 interceptor, modal focus trap, loading spinner system, .btn-close class, default table CSS, autofocus (9 pages), empty states, role/tabindex (12 elements), input types, status dot a11y, back nav links, cmd-palette focus fix, 8 silent-fetch error handlers |
| F34 | CSS Design System & Template Migration (M1–M3) | ✅ Complete | ✅ | ⬜ | UI Overhaul | M1: core CSS classes (.page-header, .data-table, .cc-modal, .stat-grid, .action-bar, .form-row). M2: 8 primary templates migrated. M3: 31 secondary templates migrated (15 admin, 5 billing, 7 clinical tools, 4 settings). All inline styles replaced with utility classes. |

**Summary:** 32/33 complete · 1 blocked (F9, calibration wizard ready) · 1 not started (F30) · UX Audit items 1-20 + UX Overhaul (CL-UXAUDIT + CL-UXAUDIT2 + CL-UX-OVERHAUL + CL-M3)

---

## Risk Register

> **Active risks ranked by severity.** Surface top 3 at every session start. Update immediately when risks are discovered or resolved.

| ID | Category | Description | Severity | Mitigation | Owner | Status |
|----|----------|-------------|----------|------------|-------|--------|
| R1 | External | Amazing Charts UI change breaks OCR automation | Critical | OCR-first with coordinate fallback; screenshot before every action; AC_MOCK_MODE for testing | Copilot | Open |
| R2 | Compliance | PHI leak through new logging or notification code | Critical | Session-start HIPAA scan; MRN hashing enforced; no PHI in Pushover (callback msg stripped); soft-delete on all clinical records; MRN masked to last-4 in all templates (15 violations fixed across CL-HIPAA-SOFTDEL + CL-HIPAA-AUDIT2); netpractice.py logs anonymized; model repr masked; JSON errors masked | Copilot | Mitigating |
| R3 | Technical | SQLite scaling limits hit as data grows | High | SQLAlchemy ORM only (no raw SQL); PostgreSQL migration path in SAAS_PLAN.md | Copilot | Open |
| R4 | Technical | No practice_id scoping — blocks multi-tenant SaaS | High | Planned: Practice model + user.practice_id + @require_practice decorator | Copilot | Open |
| R5 | External | API key expiration (UMLS, Pushover) disrupts features | Medium | Graceful degradation: stale cache → hardcoded fallback → "not available" | User | Open |
| R6 | Operational | Config drift between dev machine and work PC (FPA-D-NP-DENTON) | Medium | deploy_check.py pre-flight; DEPLOYMENT_GUIDE.md procedures | Copilot | Mitigating |
| R7 | Technical | 64 migration files — complexity risk on fresh installs; recursion risk if migrations call create_app() | Low | All migrations idempotent; recursion guard in `_run_pending_migrations`; all migrations now use `def run_migration(app, db)` pattern; consolidation planned for SaaS | Copilot | Mitigating |

### Closed Risks
*None yet.*

---

## File Reference

| Document | Path | Purpose |
|---|---|---|
| Master Instructions | `init.prompt.md` | Coding rules, conventions, HIPAA, architecture |
| Copilot Instructions | `.github/copilot-instructions.md` | VS Code Copilot rules, doc management, session workflow |
| Active Plan | `Documents/dev_guide/ACTIVE_PLAN.md` | Current sprint / work-in-progress plan |
| Development Guide | `Documents/dev_guide/CARECOMPANION_DEVELOPMENT_GUIDE.md` | Phase-by-phase feature specs (the "bible") |
| This File | `PROJECT_STATUS.md` | Build state, Feature Registry, dependency list |
| API Plan | `Documents/dev_guide/API_INTEGRATION_PLAN.md` | All 17+ APIs, caching, billing rules |
| AC Reference | `Documents/dev_guide/AC_INTERFACE_REFERENCE_V4.md` | AC UI ground truth (2788 lines) |
| Deployment Guide | `Documents/dev_guide/DEPLOYMENT_GUIDE.md` | Build, transfer, install workflow |
| Setup Guide | `Documents/dev_guide/SETUP_GUIDE.md` | Dev environment setup + troubleshooting |
| Changelog | `Documents/CHANGE_LOG.md` | All changes, single authoritative log |

---

## VS Code Pre-Flight Findings (2026-03-18)

- **Problems panel**: 0 errors in actual project files (108 stale Copilot chat code-block artifacts Ã¢â‚¬â€ not real code)
- **Dependency conflicts (pip check)**: None known
- **Python compile errors**: 0 across all .py files
- **.git repository**: Not yet initialized Ã¢â‚¬â€ `git init` required before first push
- **config.py**: Contains hardcoded credentials Ã¢â‚¬â€ correctly excluded from Git via `.gitignore`

---

## Part 2 Ã¢â‚¬â€ Hardening, Intelligence & Platform Completion Ã¢Å“â€¦

**Started:** 2026-03-19  |  **Completed:** 2026-03-20
**Test count:** 127 checks passing (main suite) + 525 phase suites = 652 total
**Table count:** 59+ tables  |  **Model files:** 23
**Blueprint count:** 19  |  **Billing detectors:** 26

### Completed Phases

| Phase | Status | Summary |
|-------|--------|--------- |
| Phase 11 Ã¢â‚¬â€ Security Hardening | Ã¢Å“â€¦ Mostly Complete | PIN rate limiting, secrets to env vars, admin password confirm. CSRF (11.1) pending template-wide rollout. |
| Phase 12 Ã¢â‚¬â€ Bug Fixes | Ã¢Å“â€¦ Complete | All 7 bugs fixed (TCM logic, drug matching, timezone, spell check, Tesseract, message delivery) |
| Phase 13 Ã¢â‚¬â€ Billing Engine (v1) | Ã¢Å“â€¦ Complete | Original monolithic billing rules Ã¢â‚¬â€ superseded by Phase 19 modular engine |
| Phase 14 Ã¢â‚¬â€ QoL Improvements | Ã¢Å“â€¦ Mostly Complete | Cache staleness badges, spell check confidence, SMTP config, What's New modal, RxCUIÃ¢â€ â€™RxClassCache enrichment (14.5), centralized MRN hashing (14.6) |
| Phase 15 Ã¢â‚¬â€ Document Refresh | Ã¢Å“â€¦ Complete | PROJECT_STATUS, CODEBASE_AUDIT, VERIFICATION_CHECKLIST, SECURITY, API plan all updated |

### Upcoming Phases

| Phase | Status | Summary |
|-------|--------|--------- |
| Phase 16 Ã¢â‚¬â€ Test Suite Expansion | Ã¢Å“â€¦ Complete | Expanded to 123 checks Ã¢â‚¬â€ billing detectors, seed data, integration patients, Phase 20-22 features |
| Phase 17 Ã¢â‚¬â€ QoL Features | Ã¢Å“â€¦ Complete | Configurable EOD, pregnancy/renal filter, weekly email, burnout warnings |
| Phase 18 Ã¢â‚¬â€ Deployment Readiness | Ã¢Å“â€¦ Complete | Auto-migrations, structured logging, health check, backup verification, production checklist |
| Phase 19 Ã¢â‚¬â€ Billing Capture Engine | Ã¢Å“â€¦ Complete | Modular `billing_engine/` with 26 detectors, 72 rules, 122 CPT codes, payer routing, UI integration (alert bar, post-visit modal, opportunity report, dashboard widget), 27 new test cases |
| Phase 20 Ã¢â‚¬â€ Feature Completions | Ã¢Å“â€¦ Complete | E&M Calculator, Anomaly Detector, Controlled Substance Tracker, Prior Auth, Referral Letters, Recurring Messages, Room Widget, ICD-10 Specificity, Code Pairing, Panel Gap Report (10/10) |
| Phase 21 Ã¢â‚¬â€ Data Intelligence | Ã¢Å“â€¦ Mostly Complete | Insurer auto-detection, CMS benchmarking, RVU reporting. Claim denial prediction + eligibility verification blocked (external data/APIs needed) |
| Phase 22 Ã¢â‚¬â€ Collaboration | Ã¢Å“â€¦ Complete | Colleague handoffs, note status tracking, shared order sets, version history, MA delegation, escalating alerts, practice admin view, shared PA library (8/8) |

---

## Part 3 Ã¢â‚¬â€ Running Plan 4: Refine & Harden (Phases 1Ã¢â‚¬â€œ14) Ã¢Å“â€¦

**Started:** 2026-03-20  |  **Completed:** 2026-03-20
**New tests added:** 150 (10 phases Ãƒâ€” 15 tests)
**Total test count:** 652 (127 main + 525 phase suites)

### Completed Phases

| Phase | Status | Summary |
|-------|--------|----------|
| Phase 1 Ã¢â‚¬â€ Double-Booking Detection | Ã¢Å“â€¦ Complete | `detect_double_bookings()` in schedule model, dashboard alert widget, 15 tests |
| Phase 2 Ã¢â‚¬â€ Guideline Review Admin | Ã¢Å“â€¦ Complete | GuidelineReview model, CRUD routes in intelligence.py, admin panel, 15 tests |
| Phase 3 Ã¢â‚¬â€ PDMP Morning Briefing | Ã¢Å“â€¦ Complete | `pdmp_briefing_flag` on PatientRecord, flagging in clinical_summary_parser, dashboard widget, 15 tests |
| Phase 4 Ã¢â‚¬â€ Specialty Referral Fields | Ã¢Å“â€¦ Complete | 21 specialty field sets in referral model, dynamic form rendering, 15 tests |
| Phase 5 Ã¢â‚¬â€ Macro Auto-Sync | Ã¢Å“â€¦ Complete | `sync_macros_to_disk()` in tools routes, file watcher integration, 15 tests |
| Phase 6 Ã¢â‚¬â€ AWV Interactive Checklist | Ã¢Å“â€¦ Complete | `AwvChecklistItem` model, toggle/reset endpoints, patient chart integration, 15 tests |
| Phase 7 Ã¢â‚¬â€ Template Library Sharing | Ã¢Å“â€¦ Complete | `shared` flag on ResultTemplate, clone-to-mine, admin shared library view, 15 tests |
| Phase 8 Ã¢â‚¬â€ Notification Priority Tiers | Ã¢Å“â€¦ Complete | Priority field on Notification model, tiered dashboard rendering, 15 tests |
| Phase 9 Ã¢â‚¬â€ Starter Pack Import | Ã¢Å“â€¦ Complete | `import_starter_pack()` in onboarding wizard, JSON bundle format, 15 tests |
| Phase 10 Ã¢â‚¬â€ New Medication Auto-Education | Ã¢Å“â€¦ Complete | `detect_new_medications()` in clinical_summary_parser, auto-draft education messages, 15 tests |
| Phase 11 Ã¢â‚¬â€ Stale Document Fixes | Ã¢Å“â€¦ Complete | DevGuide header/feature table updated, running_plan_done1/done2 annotated |
| Phase 12 Ã¢â‚¬â€ PROJECT_STATUS.md Overhaul | Ã¢Å“â€¦ Complete | Architecture section, migration list, What's Next, RP3/RP4 summaries |
