# LLM_ABOUT.md — CareCompanion Machine-Readable Project Overview

> **Generated:** 2026-03-22 | **Version:** 1.1.2 | **Status:** Pre-Beta
> **Purpose:** Complete machine-readable reference for any LLM/AI agent to understand the entire CareCompanion project — architecture, features, files, data flows, and integration points.

---

## 1. PROJECT IDENTITY

| Key | Value |
|-----|-------|
| **Name** | CareCompanion (formerly NP_Companion) |
| **Type** | Desktop clinical workflow automation + billing optimization platform |
| **Stack** | Python 3.11, Flask 3.1.3, SQLAlchemy 2.0, SQLite, Jinja2, PyAutoGUI, Tesseract OCR, Playwright |
| **Target EHR** | Amazing Charts (AC) 12.3.x + CGM webPRACTICE (NetPractice) scheduling |
| **Deployment** | PyInstaller → single `.exe` + data folder, runs on Windows 10/11 clinic workstation |
| **Auth** | Flask-Login session-based, bcrypt hashed passwords, Fernet-encrypted credential fields, CSRF via Flask-WTF |
| **Database** | SQLite (single file `data/carecompanion.db`), 82 model classes, 60+ tables, 59 migration scripts |
| **Background Agent** | Windows service with APScheduler (20 scheduled jobs), OCR automation, system tray icon |
| **Test Suite** | 127+ main tests (test.py), 70+ Phase 7 tests (test_phase7.py), ~800 total across all suites |

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                     CareCompanion Desktop App                    │
│                                                                  │
│  ┌──────────┐  ┌───────────────┐  ┌────────────────────────┐   │
│  │ launcher  │→│ Flask Web App  │  │ Background Agent       │   │
│  │  .py      │  │ (port 5000)   │  │ (agent_service.py)     │   │
│  └──────────┘  │                │  │                        │   │
│                │ 29 blueprints  │  │ 20 scheduled jobs      │   │
│                │ 250+ endpoints │  │ OCR/pyautogui automation│   │
│                │ 111 templates  │  │ HTTP status (port 5001)│   │
│                └───────┬───────┘  │ System tray icon       │   │
│                        │          └────────────┬───────────┘   │
│                        ▼                       ▼               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   SQLite Database                        │   │
│  │   82 models · 60+ tables · Fernet-encrypted fields      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                        │                                        │
│         ┌──────────────┼──────────────┐                        │
│         ▼              ▼              ▼                         │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐                 │
│  │ 19 External│ │ Billing    │ │ 3 Scrapers │                 │
│  │ APIs       │ │ Engine     │ │ (Playwright)│                │
│  │ (cached)   │ │ 27 detect. │ │ NP/PDMP/   │                │
│  │            │ │ scoring    │ │ VIIS        │                │
│  └────────────┘ └────────────┘ └────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
```

### Request Flow
1. User opens `http://localhost:5000` (or pywebview native window)
2. Flask routes requests through 29 blueprints → Jinja2 templates
3. Templates reference SQLAlchemy models for data
4. Background agent runs OCR automation, inbox monitoring, scheduled jobs
5. Billing engine evaluates patient data through 27 detectors → scoring → stack builder
6. 19 external APIs provide clinical intelligence (drug safety, lab interpretation, guidelines)

---

## 3. FEATURE REGISTRY (F1–F32)

### Status Key
- ✅ = Complete and tested
- ⏸️ = Blocked by external dependency
- 🔲 = Not started

| ID | Feature | Status | Blueprints | Models | Templates | Services/Agent |
|----|---------|--------|------------|--------|-----------|----------------|
| **F1** | Core Platform | ✅ | All | All | base.html, errors/ | app/__init__.py |
| **F2** | Background Agent | ✅ | agent_api | AgentLog, AgentError | admin_agent.html | agent_service.py, agent/*.py |
| **F3** | NetPractice Scraper | ✅ | netpractice_admin | Schedule | np_setup_wizard.html | scrapers/netpractice.py |
| **F4** | Today View & Timer | ✅ | timer, dashboard | TimeLog | timer.html, dashboard.html | — |
| **F5** | Inbox Monitor | ✅ | inbox | InboxSnapshot, InboxItem | inbox.html | agent/inbox_reader.py, inbox_monitor.py, inbox_digest.py |
| **F6** | Clinical Summary Parser | ✅ | patient | Patient*, vitals, meds, dx, allergies, labs | patient_chart.html | agent/clinical_summary_parser.py |
| **F7** | On-Call Note Keeper | ✅ | oncall | OnCallNote, HandoffLink | oncall.html, oncall_new.html | — |
| **F8** | Order Set Manager | ✅ | orders | OrderSet, OrderItem, OrderExecution | orders.html | agent/pyautogui_runner.py |
| **F9** | Chart Prefill (AC Automation) | ⏸️ | — | — | — | agent/ac_window.py (partial) |
| **F10** | Medication Reference | ✅ | medref | MedicationEntry, RxNormCache | medref.html | services/api/rxnorm, openfda |
| **F11** | Lab Tracker | ✅ | labtrack | LabTrack, LabResult, LabPanel | labtrack.html | — |
| **F12** | Care Gap Tracker | ✅ | caregap | CareGap, CareGapRule | caregap.html | agent/caregap_engine.py |
| **F13** | Metrics Dashboard | ✅ | metrics | TimeLog (aggregated) | metrics.html | — |
| **F14** | Patient Roster | ✅ | patient | PatientRecord | patient_roster.html | — |
| **F15** | Billing Tools | ✅ | intelligence, timer | BillingOpportunity, BillingRule | billing_review.html, billing_log.html | billing_engine/*.py |
| **F16** | Coding Suggester + AWV Checklist | ✅ | intelligence, timer | BillingRule, TimeLog (awv_checklist) | coding.html, timer.html | billing_engine/detectors/awv.py |
| **F17** | Care Gap Alerts | ✅ | caregap, intelligence | CareGap | caregap.html | agent/caregap_engine.py, notifier.py |
| **F18** | Delayed Message Sender | ✅ | messages | DelayedMessage | messages.html, message_new.html | agent_service.py (sender job) |
| **F19** | Result Response Templates | ✅ | intelligence | ResultTemplate | result_template_library.html | — |
| **F20** | End-of-Day Checker | ✅ | tools | — | eod.html | agent/eod_checker.py |
| **F21** | Push Notifications | ✅ | auth | Notification | notifications.html | agent/notifier.py |
| **F22** | Morning Briefing | ✅ | intelligence | — | morning_briefing.html | services/api_scheduler.py |
| **F22a** | Commute Mode TTS | ✅ | intelligence | — | commute_briefing.html | — |
| **F23** | AutoHotkey Macros | ✅ | tools | AhkMacro, DotPhrase, MacroStep, MacroVariable | macros.html, dot_phrases.html | utils/ahk_generator.py |
| **F24** | Follow-Up Tickler | ✅ | tools | Tickler | tickler.html | — |
| **F25** | Prior Auth Tracker + PDMP Flag | ✅ | tools, intelligence | PriorAuthorization | pa.html | scrapers/pdmp.py |
| **F26** | Referral Letter Generator | ✅ | tools | ReferralLetter | referral.html | — |
| **F27** | Note Reformatter | ✅ | intelligence | ReformatLog | reformatter.html | agent/note_reformatter.py, note_parser.py, note_classifier.py |
| **F28** | Provider Onboarding Wizard + Starter Pack | ✅ | auth | User prefs | onboarding.html, starter_pack.html | — |
| **F29** | Admin Tools | ✅ | admin | — | admin_dashboard.html, admin_*.html | — |
| **F30** | Offline Mode | 🔲 | — | — | — | — |
| **F31** | AI Assistant | ✅ | ai_api | — | base.html (ai-panel) | routes/ai_api.py |
| **F32** | Clinical Calculators (48 calculators) | ✅ | calculator | CalculatorResult | calculators.html, calculator_detail.html | services/calculator_engine.py, calculator_registry.py |

### Additional Feature Sets (from Running Plan)
| Feature Set | Status | Description |
|-------------|--------|-------------|
| Billing Capture Engine (26 detectors) | ✅ | billing_engine/detectors/*.py |
| Expected Net Value Scoring | ✅ | billing_engine/scoring.py |
| Visit Stack Builder + Staff Routing | ✅ | billing_engine/stack_builder.py, stack_classifier.py |
| Documentation Phrase Library | ✅ | models/billing.py (DocumentationPhrase) |
| Why-Not Explainability + Closed-Loop | ✅ | routes/intelligence.py, models/billing.py (ClosedLoopStatus) |
| Dynamic Monitoring Rules | ✅ | services/monitoring_rule_engine.py |
| Immunization Series Tracking | ✅ | services/immunization_engine.py |
| Revenue Reporting + Reconciliation | ✅ | routes/revenue.py |
| Campaign Mode + Admin ROI | ✅ | routes/campaigns.py |
| Payer Coverage Integration | ✅ | models/billing.py (PayerCoverageMatrix) |
| Demo Mode + Test Patients | ✅ | scripts/seed_test_data.py, routes/patient_gen.py |
| Daily Provider Summary | ✅ | routes/daily_summary.py |
| MA/Rooming Staff Sheet | ✅ | routes/daily_summary.py |
| REMS Medication Database | ✅ | routes/daily_summary.py, data/rems_database.json |
| Infectious Disease Reporting | ✅ | routes/daily_summary.py, data/reportable_diseases.json |
| Help/Feature Guide System | ✅ | routes/help.py, data/help_guide.json |
| Bonus Tracker | ✅ | routes/bonus.py, services/bonus_calculator.py |
| CCM Enrollment + Tracking | ✅ | routes/ccm.py |
| TCM Discharge Watch | ✅ | routes/intelligence.py |

---

## 4. EXTERNAL API INTEGRATIONS (19 APIs)

All 19 APIs are implemented with caching, rate limiting, and offline graceful degradation.

| Tier | API | Purpose | Auth | Cache Model |
|------|-----|---------|------|-------------|
| 1-Core | RxNorm (NIH) | Drug normalization, interactions | None (20 req/s) | RxNormCache |
| 1-Core | RxClass (NIH) | Drug-class relationships | None | RxClassCache |
| 1-Core | OpenFDA Drug Label | SPL labels, boxed warnings, dosing | Optional key | FdaLabelCache |
| 1-Core | OpenFDA FAERS | Adverse event reports | Same key | FaersCache |
| 1-Core | OpenFDA Recalls | Drug recall enforcement | Same key | RecallCache |
| 1-Core | ICD-10 (NLM) | ICD-10-CM code search | None | Icd10Cache |
| 1-Core | LOINC (Regenstrief) | Lab code standardization | Free account | LoincCache |
| 1-Core | UMLS (NLM) | Unified medical vocabulary | Licensed (exp 2026-03-19) | UmlsCache |
| 1-Core | SNOMED CT (via UMLS) | Clinical terminology | Via UMLS | Via UmlsCache |
| 1-Core | VSAC (NLM) | Clinical value sets for quality measures | Via UMLS | VsacValueSetCache |
| 2-CDS | AHRQ HealthFinder | Preventive care recommendations | None | HealthFinderCache |
| 2-CDS | CDC CVX (via RxNorm) | Vaccine codes | Via RxNorm | CdcImmunizationCache |
| 2-CDS | CMS HCPCS/CPT | Procedure code lookups | Flat files | BillingRuleCache |
| 2-CDS | NLM Conditions | Disease reference | None | NlmConditionsCache |
| 3-Lit | PubMed E-utilities | Literature search | Free key | PubmedCache |
| 3-Lit | MedlinePlus Connect | Patient education | None | MedlinePlusCache |
| 4-Supp | Open-Meteo Weather | Heat advisories | None | In-memory |
| Billing | CMS PFS | Medicare Fee Schedule | None | BillingRuleCache |
| Billing | CMS data.cms.gov | GPCI, RVU files | None | BillingRuleCache |

---

## 5. BILLING ENGINE ARCHITECTURE

```
Patient Data (from clinical_summary_parser or manual entry)
        │
        ▼
┌──────────────────────────────────┐
│   BillingCaptureEngine.evaluate()│ ← engine.py
│                                  │
│   For each of 27 detectors:     │
│   ┌────────────────────────────┐ │
│   │ BaseDetector.detect()      │ │ ← base.py
│   │ → Returns opportunities[]  │ │
│   └────────────────────────────┘ │
│                                  │
│   Deduplicate by opportunity_code│
│   Apply payer routing/suppression│ ← payer_routing.py
│   Enrich with cost share data   │
│   Score by expected net value    │ ← scoring.py
│   Build visit stack              │ ← stack_builder.py
│   Classify for staff routing     │ ← stack_classifier.py
│   Check code specificity         │ ← specificity.py
│   Attach doc phrase suggestions  │
└──────────────────────────────────┘
        │
        ▼
BillingOpportunity records (stored in DB)
        │
        ▼
Staff-facing UI: billing_review, staff_billing_tasks, opportunity_report
```

### 27 Detectors
| Detector | Category | CPT Codes | Description |
|----------|----------|-----------|-------------|
| acp | acp_standalone | 99497/99498 | Advance Care Planning |
| alcohol | alcohol_screening | 99408/G0442 | SBIRT alcohol screening |
| awv | awv | G0438/G0439 | Annual Wellness Visit |
| bhi | bhi | 99484/99492-99494 | Behavioral Health Integration |
| calculator_detector | calculator_billing | 96127 + others | Calculator-triggered billing (GAD-7, PHQ-9, AUDIT-C, EPDS) |
| care_gaps | care_gap_screenings | various | Overdue preventive screenings |
| ccm | ccm | 99490/99491/99487 | Chronic Care Management |
| chronic_monitoring | chronic_monitoring | various | Overdue monitoring labs |
| cocm | cocm | 99492-99494 | Collaborative Care Model |
| cognitive | cognitive_assessment | 99483 | Cognitive assessment (dementia) |
| counseling | counseling | 99401-99404 | Preventive counseling |
| em_addons | em_addons | 99417 | Prolonged E&M add-ons |
| g2211 | g2211 | G2211 | Complex visit add-on (Medicare only) |
| misc | misc | various | After-hours, care coordination, PRN smoking, education |
| obesity | obesity_nutrition | G0447/97802-97804 | Obesity/nutrition counseling |
| pediatric | pediatric | 96110/96127 + others | Developmental, vision, hearing, dental, maternal depression |
| preventive | preventive_visit | 99381-99397 | Preventive visit detection |
| procedures | procedures | 93000/94010 + others | In-office procedures (EKG, spirometry, etc.) |
| prolonged | prolonged_service | 99354/99355 | Prolonged service time |
| rpm | rpm | 99453-99458 | Remote Patient Monitoring |
| screening | screening | various | SDOH, maternal depression, fall risk, hearing |
| sdoh | sdoh | 96160/G0444 | Social Determinants screening |
| sti | sti_screening | 86580/87491 + others | STI/hepatitis screening |
| tcm | tcm | 99495/99496 | Transitional Care Management |
| telehealth | telehealth | modifier -95 | Telehealth place of service |
| tobacco | tobacco_cessation | 99406/99407/G0436 | Tobacco cessation counseling |
| vaccine_admin | vaccine_admin | 90460-90474 | Vaccine administration fees |

### Scoring Engine (8 Factors)
| Factor | Weight | Source |
|--------|--------|--------|
| Revenue magnitude | 0.25 | CMS fee schedule lookup |
| Documentation burden | 0.15 | Complexity classification |
| Completion probability | 0.15 | Historical capture rate |
| Time to cash | 0.10 | Payer-specific payment speed |
| Bonus urgency | 0.10 | Quarterly threshold proximity |
| Staff effort | 0.10 | Role-based routing complexity |
| Denial risk | 0.10 | Payer-specific denial rate |
| Patient complexity | 0.05 | Chronic condition count |

---

## 6. UI OVERHAUL SYSTEMS (Phase 44)

| # | System | Status | Implementation Location |
|---|--------|--------|------------------------|
| 1 | Context Sub-Panel | ✅ COMPLETE | CSS: main.css L1515-1680; JS: base.html L1087+; 15 templates with `{% block subpanel %}` |
| 2 | Popup Taskbar | ✅ COMPLETE | CSS: main.css L1685-1765; JS: `window.ModalTaskbar` in base.html L1136 |
| 3 | Split View | ⚠️ PARTIAL | JS: `window.SplitViewManager` in base.html L1509; CSS grid layout incomplete |
| 4 | PiP Widgets | ✅ COMPLETE | JS: `window.PipManager` in base.html L1628; 21 patient_chart widgets pip-eligible |
| 5 | Smart Bookmarks | ❌ PLANNED | HTML container in base.html L125; No folder/drag JS |
| 6 | Breadcrumb Trail | ✅ COMPLETE | CSS: main.css L1770-1830; JS: base.html L1339-1385; sessionStorage |
| 7 | Type-Ahead Filtering | ✅ COMPLETE | CSS: main.css L1835-1900; JS: base.html L1388-1447; 16+ templates with `data-filterable` |
| 8 | Page Transitions | ✅ COMPLETE | CSS: main.css L1903-1945; 8 keyframes, localStorage pref |
| 9 | AI Enhancements | ⚠️ PARTIAL | Routes: ai_api.py (3 endpoints); UI: ai-panel in base.html; help popovers container only |

---

## 7. FILE & FOLDER MANIFEST

### Root Directory: `C:\Users\coryd\Documents\NP_Companion\`

#### Entry Points & Config
| File | Purpose | Key Exports |
|------|---------|-------------|
| `app.py` | Flask entry point — thin wrapper calling `create_app()` | — |
| `launcher.py` | Unified launcher with 4 modes (dev/server/agent/all), pywebview, Chrome debug, tray icon | `main()` |
| `agent_service.py` | Background agent: 20 scheduled jobs, HTTP control API (port 5001), tray icon, crash recovery, SMTP reports | `AgentService` |
| `config.py` | Live configuration (gitignored) — all settings, API keys, AC paths, credentials | All `UPPERCASE` vars |
| `config.example.py` | Config template for deployment (safe to commit) | Template vars |
| `build.py` | PyInstaller build script — version bumping, exe building, ZIP packaging | `build()` |
| `carecompanion.spec` | PyInstaller spec file — defines included files, hidden imports, binary paths | — |
| `requirements.txt` | 39 Python dependencies with pinned versions | — |
| `init.prompt.md` | AI/Copilot initial context prompt — 4000+ lines of feature specs | — |

#### Startup & Operations Scripts
| File | Purpose |
|------|---------|
| `Start_CareCompanion.bat` | User-facing startup script |
| `beta_launch.bat` | Beta deployment batch script |
| `restart.bat` | Service restart batch script |
| `agent_startup.xml` | Windows Task Scheduler XML for agent auto-start |
| `CareCompanion.ico` | App icon file |
| `CareCompanion.code-workspace` | VS Code workspace settings |

#### Test Files
| File | Purpose | Tests |
|------|---------|-------|
| `test.py` | Main integration test suite — 15 sections covering models, routes, billing, APIs, forms, scheduler | ~127 checks |
| `test_phase7.py` | Phase 7 UI tests — menu bar, bookmarks, command palette, patient generator, CSS responsiveness | ~70 checks |

#### Stray Files (should be moved to `migrations/`)
| File | Purpose |
|------|---------|
| `migrate_add_dismissal_reason.py` | Migration: add dismissal reason column |
| `migrate_add_dotphrase_sharing.py` | Migration: add dot phrase sharing columns |
| `migrate_add_notification_priority.py` | Migration: add notification priority columns |
| `migrate_add_template_sharing.py` | Migration: add template sharing columns |
| `deploy_check_output.txt` | Output from deploy_check.py run |

---

### `app/` — Flask Application Package

| File | Purpose | Key Exports |
|------|---------|-------------|
| `__init__.py` | App factory: `create_app()`, 29 blueprint registrations, middleware, error handlers, auto-migrations, RBAC context processors | `create_app`, `db`, `login_manager`, `bcrypt` |
| `api_config.py` | Single source of truth for all external API config: base URLs, cache TTLs, rate limits, CMS billing constants, GPCI locality, ICD-10 prefix lists | `API_CONFIG`, `CMS_*` constants |

### `app/services/` — Business Logic Services

| File | Purpose | Key Exports |
|------|---------|-------------|
| `api_scheduler.py` | 19 background API job definitions: morning briefing, visit prep, recall checks, cache refresh, pricing updates, monitoring | `register_api_jobs()` |
| `billing_rules.py` | Thin wrapper around BillingCaptureEngine for service layer | `BillingRulesService` |
| `billing_valueset_map.py` | Maps billing categories to VSAC ICD-10 code sets | `get_vsac_icd10_codes()` |
| `bonus_calculator.py` | Quarterly bonus calculation: threshold tracking, projection, opportunity impact | `calculate_quarterly_bonus()` |
| `calculator_engine.py` | Clinical calculator computation: BMI, LDL, PHQ-9, GAD-7, AUDIT-C, AHA PREVENT, pack-years; auto-scoring, persistence | `CalculatorEngine` |
| `calculator_registry.py` | Static registry: 48 calculator definitions with metadata, categories, automation tags | `CALCULATOR_REGISTRY` |
| `clinical_spell_check.py` | Medical text spell-checker with abbreviation expansion and clinical dictionary | `analyze_text()`, `expand_abbreviation()` |
| `immunization_engine.py` | CDC immunization series tracking and gap detection | `populate_patient_series()`, `get_series_gaps()` |
| `insurer_classifier.py` | Classifies free-text insurer names into categories (Medicare, Medicaid, Commercial, etc.) | `classify_insurer()` |
| `monitoring_rule_engine.py` | Lab/drug monitoring rules: waterfall lookup (cache→DailyMed→FDA→RxClass), FHIR PlanDefinition export, CDS Hooks cards | `MonitoringRuleEngine` |
| `pricing_service.py` | Waterfall drug pricing: Cost Plus → GoodRx → NADAC | `PricingService` |
| `telehealth_engine.py` | Telehealth-specific visit fields (modifier codes, place of service) | `get_telehealth_fields()` |

### `app/services/api/` — Individual API Client Modules
Contains individual client modules for each of the 19 external APIs. Each follows the pattern: `fetch()`, `search()`, caching, rate limiting.

---

### `agent/` — Background Automation Agent (16 files)

| File | Purpose | Key Exports |
|------|---------|-------------|
| `ac_window.py` | Amazing Charts window detection, state tracking, auto-login, resurrect dialog handling | `find_ac_window()`, `get_ac_state()`, `auto_login_ac()` |
| `caregap_engine.py` | Rule-based care gap evaluation against patient data; seeds default rules | `evaluate_care_gaps()`, `seed_default_rules()` |
| `clinical_summary_parser.py` | OCR automation: open chart, export clinical summary, parse XML, detect new meds, store to DB | `open_patient_chart()`, `export_clinical_summary()`, `parse_clinical_summary()`, `store_parsed_summary()` |
| `eod_checker.py` | End-of-day verification: open notes, unsigned orders, pending callbacks | `run_eod_check()` |
| `inbox_digest.py` | Inbox activity digest generation and notification | `generate_digest()`, `run_digest_job()` |
| `inbox_monitor.py` | Thin wrapper triggering inbox read cycle | `run_inbox_monitor()` |
| `inbox_reader.py` | OCR-based inbox table parsing, item categorization, critical value detection, auto-TCM creation | `read_inbox()` |
| `mrn_reader.py` | OCR-based MRN detection from AC title bar; thread-locked with idle timeout | `read_mrn()`, `calibrate_mrn_reader()` |
| `note_classifier.py` | Clinical note content classification (medications, diagnoses, allergies, ROS, exam) | `classify_content()`, `get_classification_summary()` |
| `note_parser.py` | Section-based clinical note parsing (SOAP format) | `parse_note_sections()`, `parse_medication_list()` |
| `note_reformatter.py` | Note reformatting with template application and SNOMED enrichment | `reformat_note()`, `build_reformatted_note()` |
| `notifier.py` | Push notification delivery (Pushover), callback reminders, escalation checking | `send_inbox_notification()`, `check_escalations()` |
| `ocr_helpers.py` | OCR utility functions: screenshot, preprocess, find text, find element near text, click text | `ocr_find_all_text()`, `find_text_on_screen()`, `find_and_click()` |
| `pyautogui_runner.py` | Order set execution via PyAutoGUI (clicks, types, tab navigation in AC) | `execute_order_set()` |
| `scheduler.py` | APScheduler builder: defines all cron/interval triggers for agent jobs | `build_scheduler()` |

---

### `billing_engine/` — Billing Detection & Scoring (38 files)

#### Core Files
| File | Purpose | Key Exports |
|------|---------|-------------|
| `base.py` | Abstract base detector: interface contract, `_make_opportunity()`, `_get_rate()` | `BaseDetector` |
| `engine.py` | Orchestrator: loads detectors, evaluates, deduplicates, scores, routes | `BillingCaptureEngine` |
| `payer_routing.py` | Payer-type context (Medicare/MA/Medicaid/Commercial), code suppression, flags | `get_payer_context()` |
| `rules.py` | 60+ billing rule definitions with CPT codes, categories, RVU data | `BILLING_RULES` |
| `scoring.py` | 8-factor expected net value calculator; priority tiers, urgency scoring | `ExpectedNetValueCalculator` |
| `shared.py` | Shared utilities: VSAC codes, dx prefix matching, MRN hashing, `months_since()`, `add_business_days()` | Various |
| `specificity.py` | ICD-10 code specificity recommender — suggests more specific child codes | `CodeSpecificityRecommender` |
| `stack_builder.py` | Visit stack builder: composes compatible billing codes, resolves conflicts | `VisitStackBuilder` |
| `stack_classifier.py` | Staff routing: classifies opportunities by responsible role (provider vs MA vs biller) | `StackClassifier` |
| `utils.py` | Patient data utilities: `age_from_dob()`, `has_dx()`, `has_medication()`, `months_since()` | Various |

#### `billing_engine/detectors/` — 27 Detector Files
Each implements `BaseDetector.detect(patient_data, payer_context) → list[dict]`. See Section 5 for full list.

---

### `models/` — SQLAlchemy Models (31 files, 82 classes)

| File | Models | Tables |
|------|--------|--------|
| `user.py` | User | users |
| `patient.py` | PatientRecord, PatientVitals, PatientMedication, PatientDiagnosis, PatientAllergy, PatientImmunization, PatientSpecialist, PatientNoteDraft, Icd10Cache, RxNormCache, PatientLabResult, PatientSocialHistory | 12 tables |
| `billing.py` | BillingOpportunity, BillingRuleCache, BillingRule, DiagnosisRevenueProfile, StaffRoutingRule, DocumentationPhrase, OpportunitySuppression, ClosedLoopStatus, BillingCampaign, PayerCoverageMatrix | 10 tables |
| `agent.py` | AgentLog, AgentError | 2 tables |
| `audit.py` | AuditLog | 1 table |
| `timelog.py` | TimeLog | 1 table |
| `inbox.py` | InboxSnapshot, InboxItem | 2 tables |
| `oncall.py` | OnCallNote, HandoffLink | 2 tables |
| `orderset.py` | OrderSet, OrderItem, MasterOrder, OrderSetVersion, OrderExecution, OrderExecutionItem | 6 tables |
| `medication.py` | MedicationEntry | 1 table |
| `labtrack.py` | LabTrack, LabResult, LabPanel | 3 tables |
| `caregap.py` | CareGap, CareGapRule | 2 tables |
| `tickler.py` | Tickler | 1 table |
| `message.py` | DelayedMessage | 1 table |
| `reformatter.py` | ReformatLog | 1 table |
| `schedule.py` | Schedule | 1 table |
| `notification.py` | Notification | 1 table |
| `bonus.py` | BonusTracker | 1 table |
| `tcm.py` | TCMWatchEntry | 1 table |
| `ccm.py` | CCMEnrollment, CCMTimeEntry | 2 tables |
| `tools.py` | ControlledSubstanceEntry, CodeFavorite, CodePairing, PriorAuthorization, ReferralLetter | 5 tables |
| `result_template.py` | ResultTemplate | 1 table |
| `api_cache.py` | RxClassCache, FdaLabelCache, FaersCache, RecallCache, LoincCache, UmlsCache, HealthFinderCache, PubmedCache, MedlinePlusCache, CdcImmunizationCache, VsacValueSetCache, NlmConditionsCache | 12 tables |
| `macro.py` | AhkMacro, DotPhrase, MacroStep, MacroVariable | 4 tables |
| `monitoring.py` | MonitoringRule, MonitoringSchedule, REMSTrackerEntry | 3 tables |
| `preventive.py` | PreventiveServiceRecord | 1 table |
| `immunization.py` | ImmunizationSeries | 1 table |
| `telehealth.py` | CommunicationLog | 1 table |
| `calculator.py` | CalculatorResult | 1 table |
| `bookmark.py` | PracticeBookmark | 1 table |

---

### `routes/` — Flask Blueprints (29 files, ~250 endpoints)

| File | Blueprint | ~Lines | Endpoint Count | Domain |
|------|-----------|--------|----------------|--------|
| `admin.py` | admin_hub | 700 | 13 | Practice settings, config, care gap rules, updates |
| `agent_api.py` | agent_api | 400 | 7 | Agent status, health check, restart controls |
| `ai_api.py` | ai_api | 200 | 3 | AI chat proxy (OpenAI/Anthropic/xAI), HIPAA gate |
| `auth.py` | auth | 2200 | 40+ | Login, registration, settings, notifications, bookmarks, onboarding, admin users |
| `bonus.py` | bonus | 240 | 5 | Bonus tracker, calibration, projection |
| `calculator.py` | calculator | 140 | 5 | Calculator index, compute, patient risk tools, score history |
| `campaigns.py` | campaigns | 290 | 5 | Billing campaigns, ROI reporting |
| `caregap.py` | caregap | 500 | 8 | Care gap dashboard, panel report, outreach |
| `ccm.py` | ccm | 310 | 7 | CCM enrollment, time logging, billing roster |
| `daily_summary.py` | daily_summary | 400 | 6 | Provider summary, rooming sheet, REMS, reportable diseases |
| `dashboard.py` | dashboard | 500 | 2 | Main dashboard, schedule JSON |
| `help.py` | help | 170 | 4 | Help center, search, feature items |
| `inbox.py` | inbox | 260 | 7 | Inbox digest, held items, audit log |
| `intelligence.py` | intelligence | 2600 | 45+ | Billing review, note reformatter, clinical intelligence APIs, morning briefing, TCM watch, staff tasks |
| `labtrack.py` | labtrack | 460 | 10 | Lab tracking, trends, panels |
| `medref.py` | medref | 450 | 6 | Drug lookup (RxNorm+OpenFDA), pricing, review queue |
| `message.py` | messages | 340 | 9 | Delayed messages, result templates |
| `metrics.py` | metrics | 500 | 5 | Metrics dashboard, charts, weekly report |
| `monitoring.py` | monitoring | 500 | 5 | Monitoring calendar, FHIR export, preventive gaps |
| `netpractice_admin.py` | np_admin | 350 | 8 | NetPractice setup, nav steps, Chrome management |
| `oncall.py` | oncall | 480 | 12 | On-call log, handoff, forwarding |
| `orders.py` | orders | 500 | 18 | Order sets CRUD, execution, sharing, master list |
| `patient.py` | patient | 1500 | 19 | Patient chart, XML upload, roster, note drafts |
| `patient_gen.py` | patient_gen | 130 | 3 | Test patient generator |
| `revenue.py` | revenue | 400 | 3 | Revenue reports, diagnosis families |
| `telehealth.py` | telehealth | 100 | 2 | Communication logging |
| `timer.py` | timer | 1400 | 24 | Timer, AWV checklist, F2F tracking, E&M calculator, billing log, benchmarks |
| `tools.py` | tools | 1800 | 50+ | CS tracker, coding, prior auth, tickler, referral, dot phrases, macros |

---

### `utils/` — Utility Modules (7 files)

| File | Purpose | Key Exports |
|------|---------|-------------|
| `__init__.py` | Package init; `safe_patient_id()` (SHA-256 MRN hashing), `log_access()` | `safe_patient_id()`, `log_access()` |
| `ahk_generator.py` | AutoHotkey script generation from macro/dot-phrase models | `generate_macro_script()`, `generate_dot_phrase_script()` |
| `chrome_launcher.py` | Chrome CDP mode launcher for Playwright scraping | `ensure_chrome_debug()` |
| `error_logger.py` | JSON structured error logging with daily rotation (30-day retention) | `log_error()`, `log_exception()` |
| `feature_gates.py` | 3-tier feature gating (Essential/Standard/Advanced) with admin bypass | `is_feature_enabled()`, `require_feature()` |
| `paths.py` | Path resolution for PyInstaller frozen mode + dev mode | `get_base_dir()`, `get_data_dir()`, `get_db_path()`, `get_tesseract_path()` |
| `updater.py` | Self-update: scan for ZIP, compare versions, extract while preserving data/config | `check_for_update()`, `apply_update()` |

---

### `scrapers/` — Browser Automation (4 files)

| File | Purpose | Key Exports |
|------|---------|-------------|
| `netpractice.py` | Playwright CDP scraper for CGM webPRACTICE scheduling — appointment parsing | `NetPracticeScraper` |
| `pdmp.py` | Playwright scraper for Virginia PDMP (PMP AWARxE) — controlled substance history | `PDMPScraper` |
| `viis.py` | Playwright scraper for Virginia Immunization Information System | `VIISScraper` |

---

### `templates/` — Jinja2 Templates (111 files)

Key templates by category:
- **Layout:** `base.html` (2,027 lines — master template with all UI systems)
- **Dashboard:** `dashboard.html` (1,272 lines)
- **Patient:** `patient_chart.html` (2,818 lines — largest template, 21 pip-eligible widgets)
- **Settings:** `settings.html`, `settings_account.html`, `settings_notifications.html`
- **Billing:** `billing_review.html`, `billing_log.html`, `billing_em_calculator.html`, `billing_monthly.html`, `billing_benchmarks.html`, `billing_opportunity_report.html`, `billing_why_not.html`
- **Clinical:** `timer.html`, `inbox.html`, `medref.html`, `labtrack.html`, `caregap.html`, `orders.html`
- **Admin:** `admin_dashboard.html`, `admin_users.html`, `admin_agent.html`, `admin_api.html`, `admin_config.html`, `admin_practice.html`
- **Reference:** `daily_summary.html`, `morning_briefing.html`, `commute_briefing.html`
- **Partials:** `_billing_alert_bar.html`, `_billing_post_visit.html`, `_cache_badge.html`, `_calculator_questionnaire.html`, `_empty_state.html`, `_free_widgets.html`, `_tickler_card.html`, `_why_link.html`
- **Print:** `daily_summary_print.html`, `rooming_sheet_print.html`, `caregap_print_handout.html`, `oncall_export.html`
- **Error:** `errors/404.html`, `errors/500.html`

---

### `static/` — CSS, JS, Images (8 files)

| File | Purpose | Lines |
|------|---------|-------|
| `css/main.css` | Main stylesheet — all layout, components, themes, transitions | 3,535 |
| `css/themes.css` | Theme variable definitions (light/dark modes) | — |
| `css/calculators.css` | Calculator-specific styles | — |
| `js/main.js` | Main application JavaScript — 40+ functions covering dark mode, notifications, auto-lock, menu bar, bookmarks, command palette, AI panel | 1,755 |
| `js/error-handler.js` | Client-side error handling/logging | — |
| `js/calculator_charts.js` | Chart rendering for calculator score history | — |
| `js/free_widgets.js` | Dashboard embedded widget framework | — |
| `changelog.json` | Version changelog data (read by What's New modal) | — |

---

### `scripts/` — Standalone Scripts (2 files)

| File | Purpose |
|------|---------|
| `seed_master_orders.py` | Seeds master_orders table from Excel spreadsheet |
| `seed_test_data.py` | Generates 35 fake patients covering all billing detectors, care gap rules, payer types, edge cases |

---

### `tools/` — Deployment & Testing Tools (6 files + 2 subdirs)

| File | Purpose |
|------|---------|
| `backup_restore_test.py` | Validates database backups are healthy and restorable |
| `clinical_summary_test.py` | Integration test for clinical summary XML → DB pipeline |
| `connectivity_test.py` | LAN, Tailscale, AC file share connectivity verification |
| `deploy_check.py` | Comprehensive pre-flight deployment checker (10 sections) |
| `usb_smoke_test.py` | Post-deployment smoke test for USB/exe installations |
| `verify_all.py` | 5-stage interactive pre-beta verification orchestrator |
| `emulated_patient_generator/` | Standalone Tkinter GUI for generating fake CDA XML patients |
| `patient_gen/` | Web-integrated version of patient generator (used by patient_gen blueprint) |

---

### `migrations/` — Database Migration Scripts (59 files)

Auto-executed by `app/__init__.py` `_run_pending_migrations()` on startup. Tracked via `_applied_migrations` metadata table. All are idempotent (check before alter).

---

### `data/` — Runtime Data Files

| File/Dir | Purpose |
|----------|---------|
| `carecompanion.db` | Main SQLite database (5 MB) |
| `carecompanion_empty.db` | Fresh-install template database |
| `active_user.json` | Currently logged-in user state (for room widget) |
| `changelog.json` | App version history |
| `help_guide.json` | In-app help system (49 KB, 40+ features) |
| `rems_database.json` | FDA REMS program data (31 KB, 22 programs) |
| `reportable_diseases.json` | Reportable disease reference (37 KB, 31 conditions) |
| `backups/` | Automated database backups |
| `clinical_summaries/` | Exported CDA XML storage |
| `logs/` | Application logs (JSON structured, daily rotation) |

---

### `Documents/` — Project Documentation

| Dir/File | Purpose |
|----------|---------|
| `dev_guide/CARECOMPANION_DEVELOPMENT_GUIDE.md` | Master development guide (205 KB — all feature specs) |
| `dev_guide/RUNNING_PLAN.md` | Execution plan: 43 phases, all complete (219 KB) |
| `dev_guide/API_INTEGRATION_PLAN.md` | API integration specs for all 19 APIs |
| `dev_guide/REVIEW_2025_03_21.md` | Code audit: Phase A (7 done), B (10 done), C (12 todo), D (8 todo) |
| `dev_guide/PRE_BETA_DEPLOYMENT_CHECKLIST.md` | Deployment walkthrough checklist |
| `dev_guide/UI_OVERHAUL.md` | UI overhaul spec: 9 systems |
| `dev_guide/PROJECT_STATUS.md` | Current architecture and status summary |
| `dev_guide/DEPLOYMENT_GUIDE.md` | PyInstaller build and transfer guide |
| `dev_guide/AC_INTERFACE_REFERENCE_V4.md` | Amazing Charts UI automation reference |
| `billing_resources/` | Billing reference PDFs, Excel files, prompt templates |
| `ac_interface_reference/` | AC screenshots (56) and test documents |
| `xml_test_patients/` | 7 test CDA XML patient files |
| `_archive/` | Archived documents (38 files) |

---

### `tesseract/` — Bundled OCR Engine

Complete Tesseract 5.x installation with `tesseract.exe`, 92 support files, and 124 language packs in `tessdata/`. Only `eng.traineddata` is required for operation.

---

### `build/` and `dist/` — Build Artifacts

- `build/npcompanion/` — PyInstaller intermediate build files
- `dist/NP_Companion/` — Distributable folder
- `dist/NP_Companion_v1.1.2.zip` — Release archive

---

## 8. CONFIGURATION REFERENCE

All keys from `config.py`, grouped by section:

### Application
| Key | Type | Description |
|-----|------|-------------|
| `APP_VERSION` | str | Current version ("1.1.2") |
| `UPDATE_FOLDER` | str | Path to scan for update ZIPs |
| `HOST` | str | Flask bind address |
| `PORT` | int | Flask bind port (default 5000) |
| `SECRET_KEY` | str | Flask session signing key (auto-generated) |
| `DEBUG` | bool | Flask debug mode (False for production) |
| `TEST_PATIENT_APPOINTMENT_ENABLED` | bool | Show test patient in schedule |

### Amazing Charts Integration
| Key | Type | Description |
|-----|------|-------------|
| `AC_MOCK_MODE` | bool | Use mock data instead of real AC |
| `AC_LOGIN_USERNAME` / `AC_LOGIN_PASSWORD` | str | AC auto-login credentials (env-overridable) |
| `AC_VERSION` / `AC_BUILD` / `AC_PRACTICE_ID` / `AC_PRACTICE_NAME` | str | AC instance identification |
| `AC_EXE_PATH` / `AC_LOG_PATH` / `AC_DB_PATH` | str | AC file paths |
| `AC_IMPORTED_ITEMS_PATH` | str | Path for AC clinical summary import |
| `AC_WINDOW_TITLE_PREFIX` / `AMAZING_CHARTS_PROCESS_NAME` | str | Window detection |
| `AC_STATES` | dict | AC UI state definitions for OCR |
| `ORDER_TABS` | list | AC Order Entry tab names |
| `SCREEN_RESOLUTION` / `MRN_CAPTURE_REGION` | tuple | Display configuration for OCR |
| Various `*_XY` fallback coordinates | tuple | Pixel fallbacks for AC automation |

### Clinical Summary & Agent
| Key | Type | Description |
|-----|------|-------------|
| `CLINICAL_SUMMARY_EXPORT_FOLDER` | str | Where AC exports CDA XML |
| `CLINICAL_SUMMARY_RETENTION_DAYS` | int | Days to keep summaries |
| `IDLE_THRESHOLD_SECONDS` | int | Agent idle detection |
| `MAX_CHART_OPEN_MINUTES` | int | Chart duration warning threshold |
| `INBOX_CHECK_INTERVAL_MINUTES` | int | Inbox monitor frequency |
| `INBOX_WARNING_HOURS` / `INBOX_CRITICAL_HOURS` | int | Inbox age thresholds |
| `INBOX_DIGEST_ENABLED` / `INBOX_DIGEST_HOURS` / `INBOX_DIGEST_SEND_HOUR` / `INBOX_DIGEST_SEND_MINUTE` | mixed | Digest configuration |
| `CRITICAL_VALUE_KEYWORDS` | list | Keywords triggering critical inbox alerts |

### Notifications
| Key | Type | Description |
|-----|------|-------------|
| `PUSHOVER_USER_KEY` / `PUSHOVER_API_TOKEN` / `PUSHOVER_EMAIL` | str | Pushover push notification credentials |
| `NOTIFY_QUIET_HOURS_START` / `NOTIFY_QUIET_HOURS_END` | int | Quiet hours (default 22-7) |

### Chrome & NetPractice
| Key | Type | Description |
|-----|------|-------------|
| `NETPRACTICE_URL` / `NETPRACTICE_BOOKMARKED_URL` / `NETPRACTICE_CLIENT_NUMBER` | str | NP connection details |
| `SESSION_COOKIE_FILE` | str | NP session persistence path |
| `CHROME_CDP_PORT` / `CHROME_EXE_PATH` / `CHROME_DEBUG_PROFILE_DIR` | mixed | Chrome automation config |

### External API Keys
| Key | Type | Description |
|-----|------|-------------|
| `OPENFDA_API_KEY` | str | OpenFDA enhanced rate limit |
| `PUBMED_API_KEY` | str | PubMed E-utilities key |
| `LOINC_USERNAME` / `LOINC_PASSWORD` | str | LOINC FHIR API auth |
| `UMLS_API_KEY` | str | UMLS/SNOMED/VSAC access |

### Environment Variables (from config.example.py, not yet in config.py)
| Key | Type | Description |
|-----|------|-------------|
| `VIIS_USERNAME` / `VIIS_PASSWORD` | str | Virginia Immunization scraper |
| `PDMP_EMAIL` / `PDMP_PASSWORD` | str | Virginia PDMP scraper |
| `SMTP_SERVER` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` / `SMTP_FROM` / `SMTP_TO` | str | Email reports |

### Database
| Key | Type | Description |
|-----|------|-------------|
| `DATABASE_PATH` | str | SQLite database file path |
| `BACKUP_PATH` | str | Backup directory path |

---

## 9. KNOWN ISSUES & BUGS

### Critical (will cause runtime failures)
| # | Location | Issue |
|---|----------|-------|
| 1 | `models/__init__.py` | `PracticeBookmark` not imported — table invisible to `db.create_all()` |
| 2 | `tools/verify_all.py` | `run_stage1()` calls `checker.run()` which doesn't exist; iterates dict as tuples — **crashes** |
| 3 | `billing_engine/shared.py` + `utils.py` | Duplicate `months_since()` with conflicting None semantics (0 vs 9999) — wrong import flips eligibility |

### High (incorrect behavior)
| # | Location | Issue |
|---|----------|-------|
| 4 | `routes/admin.py` + `agent_api.py` | Duplicate `/admin/server/restart` route registration |
| 5 | 3 billing detectors | Triple 96127 opportunity — violates CMS 1-per-encounter rule |
| 6 | `billing_engine/shared.py` | `_vsac_code_cache` dict mutated without lock — thread safety |
| 7 | `billing_engine/shared.py` | TCM `add_business_days()` off-by-one — deadline 1 day late |
| 8 | `scrapers/pdmp.py` + `viis.py` | `pickle.load()` for cookies — deserialization risk |
| 9 | `static/js/main.js` L1517 | `MENU_ACTIONS.openWhatsNew` references undefined var — What's New banner Details link broken |

### Medium (should fix before deploy)
| # | Location | Issue |
|---|----------|-------|
| 10 | `utils/updater.py` | `zipfile.extractall()` without path traversal validation |
| 11 | `app/api_config.py` | NADAC dataset ID `"a]4y-5ky]b"` has bracket chars — garbled |
| 12 | `billing_engine/detectors/sti.py` | No frequency guard — fires Hep C for every visit without checking history |
| 13 | `routes/timer.py` | `RVU_TABLE` referenced before definition |
| 14 | `routes/tools.py` | `pa_generate()` uses `'cui_result' in dir()` anti-pattern |
| 15 | `agent/mrn_reader.py` | Variables accessed outside lock scope — race condition |
| 16 | `app/__init__.py` | File opened without `with` statement |
| 17 | 4 stray migration files at root | Should be in `migrations/` directory |
| 18 | `tools/emulated_patient_generator/generators.py` | Invalid syntax on line 13 — ternary inside import |

### Low (code quality)
| # | Location | Issue |
|---|----------|-------|
| 19 | `static/css/main.css` L787 | Empty `.nav-item {}` ruleset |
| 20 | `routes/` (3 files) | `_require_admin` decorator duplicated 3 times |
| 21 | `routes/patient.py` + `medref.py` | `_fetch_rxnorm()` duplicated |
| 22 | `routes/dashboard.py` | `_collect_jobs` dead code |
| 23 | 4 models | Missing `__repr__` (PracticeBookmark, CodeFavorite, CodePairing, CalculatorResult) |
| 24 | 17+ FK columns | Missing `index=True` on foreign keys |
| 25 | `__pycache__/config.cpython-311.pyc` | Compiled bytecode may contain secrets |

---

## 10. BLOCKED & DEFERRED ITEMS

### Blocked (External Dependencies)
| Item | Blocker |
|------|---------|
| F9 — Chart Prefill | Requires AC calibration on physical work PC |
| F28a — Click-to-set MRN | Requires work PC visual region tool |
| GoodRx API | Awaiting developer application approval |
| ASCVD PCE Calculator | Missing published risk coefficients |
| Gail Model Calculator | Missing published coefficients |
| F21.4 — Claim Denial Prediction | Requires historical denial dataset |
| F21.5 — Real-time Eligibility | Requires 270/271 clearinghouse contract |

### Deferred (Post-Beta)
| Item | Priority |
|------|----------|
| F30 — Offline Mode | Medium |
| CI/CD Pipeline | Medium |
| Split View UI Completion | Low |
| Smart Bookmarks (folders, drag) | Low |
| AI Context Injection | Low |
| Phase C Code Improvements (rate limiting, pagination, JSON standardization) | Low |
| Phase D Code Hygiene (refactoring, exception handling, dead code) | Low |

---

*End of LLM_ABOUT.md — This document provides complete context for any AI agent to understand, navigate, and modify the CareCompanion codebase.*
