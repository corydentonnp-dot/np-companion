# CareCompanion -- Feature Registry

> **Generated:** 03-24-26
> **Purpose:** Complete inventory of every feature in CareCompanion with status, dependencies, and test metadata.
> **Usage:** Reference during QA sessions to understand feature scope and identify what to test.
> **Numbering:** F-001+ (used consistently across all QA artifacts)

---

## F-001: Authentication and Session Management
**Status:** BUILT
**Route(s):** `/login`, `/logout`, `/register`, `/settings`, `/settings/account`, `/settings/notifications`
**Model(s):** User
**Service(s):** None (Flask-Login built-in)
**API Dependencies:** NONE
**Depends On:** None
**Required For:** F-002 through F-039 (everything requires auth)
**Demo Mode Coverage:** YES
**Test Complexity:** LOW
**Notes:** PIN-based quick auth available. Fernet-encrypted credential storage for NP, AC, PDMP, VIIS, AI keys. Dev admin: CORY / ASDqwe123.

---

## F-002: Dashboard and Schedule View
**Status:** BUILT
**Route(s):** `/dashboard`, `/api/schedule/add`, `/api/schedule/parse-text`, `/api/active-chart`
**Model(s):** Schedule, PatientRecord, TimeLog, BillingOpportunity
**Service(s):** insurer_classifier, previsit_templates
**API Dependencies:** NONE (schedule data from NetPractice scraper)
**Depends On:** F-001, F-003 (schedule data)
**Required For:** F-006, F-008, F-011
**Demo Mode Coverage:** YES (seed_test_data creates Schedule rows)
**Test Complexity:** MEDIUM
**Notes:** Double-booking detection, anomaly flags, VIIS status column, chart flag widget with 5s polling.

---

## F-003: NetPractice Scraper
**Status:** BUILT (PARTIAL -- MFA selectors need customization)
**Route(s):** `/admin/netpractice`, `/api/netpractice/scrape`, `/api/netpractice/session-status`
**Model(s):** Schedule
**Service(s):** scrapers/netpractice.py
**API Dependencies:** NetPractice web app (Playwright CDP)
**Depends On:** F-001, Chrome debug mode
**Required For:** F-002 (schedule data), F-011 (pre-visit prep)
**Demo Mode Coverage:** NO (requires live NetPractice)
**Test Complexity:** HIGH
**Notes:** Three CUSTOMIZE markers in scrapers/netpractice.py (lines 268, 342, 1070) for MFA and insurer field selectors. Two-pass extraction: Pass 1 calendar, Pass 2 details. Google redirect detection with reauth alert.

---

## F-004: Patient Chart and Demographics
**Status:** BUILT
**Route(s):** `/patient/<mrn>`, `/patient/roster`, `/patient/print-stub/<mrn>`, `/api/patient/<mrn>/pricing`, `/api/patient/<mrn>/viis-status`
**Model(s):** PatientRecord, PatientMedication, PatientDiagnosis, PatientAllergy, PatientImmunization, PatientVitals, PatientSpecialist, PatientNoteDraft, PatientSocialHistory, PatientEncounterNote, PatientLabResult
**Service(s):** clinical_summary_parser
**API Dependencies:** NONE (data from XML import)
**Depends On:** F-001, F-005 (XML import)
**Required For:** F-006, F-008, F-009, F-013, F-015, F-020
**Demo Mode Coverage:** YES (35 demo patients)
**Test Complexity:** MEDIUM
**Notes:** Tab-based chart layout with widget grid. Price badges on medication tab. Specialist referral panel.

---

## F-005: Clinical Summary XML Parser
**Status:** BUILT
**Route(s):** None (agent-side)
**Model(s):** PatientRecord, PatientMedication, PatientDiagnosis, PatientAllergy, PatientImmunization, PatientVitals, PatientLabResult, PatientSocialHistory, PatientEncounterNote
**Service(s):** agent/clinical_summary_parser.py
**API Dependencies:** NONE
**Depends On:** Amazing Charts export
**Required For:** F-004, F-006, F-008, F-009
**Demo Mode Coverage:** YES (scripts/generate_test_xmls.py creates 7 test XMLs)
**Test Complexity:** HIGH
**Notes:** Parses CDA XML into all patient data models. Triggers auto-catalog via _trigger_auto_catalog hook.

---

## F-006: Billing Engine (27 Detectors)
**Status:** BUILT
**Route(s):** `/billing/review`, `/billing/log`, `/billing/monthly`, `/billing/em-calculator`, `/api/billing/capture`, `/api/billing/dismiss`, `/api/billing/patient/<mrn>`
**Model(s):** BillingOpportunity, BillingRule, BillingRuleCache, PayerCoverageMatrix, OpportunitySuppression, ClosedLoopStatus, StaffRoutingRule, DocumentationPhrase
**Service(s):** billing_engine/engine.py (BillingCaptureEngine), billing_engine/detectors/* (27 detectors), billing_engine/scoring.py, billing_engine/payer_routing.py, billing_engine/stack_builder.py
**API Dependencies:** CMS PFS (for RVU/payment data)
**Depends On:** F-001, F-004, F-005
**Required For:** F-007, F-010, F-012
**Demo Mode Coverage:** YES (35 patients cover all 27 detector categories)
**Test Complexity:** HIGH
**Notes:** Detectors: G2211, AWV, TCM, CCM, BHI, CoCM, RPM, ACP, Alcohol, Tobacco, Obesity, Screening, STI, Cognitive, Counseling, Pediatric, Preventive, Procedures, Prolonged, Telehealth, VaccineAdmin, EMAddons, ChronicMonitoring, CareGaps, SDOH, Calculator, Misc. 72 seed rules, 122 CPT codes.

---

## F-007: Bonus Dashboard and Projections
**Status:** BUILT
**Route(s):** `/bonus`, `/bonus/entry`, `/bonus/calibrate`, `/bonus/confirm-threshold`, `/api/bonus/projection`
**Model(s):** BonusTracker
**Service(s):** bonus_calculator.py
**API Dependencies:** NONE
**Depends On:** F-001, F-006 (billing data for context)
**Required For:** None (standalone reporting)
**Demo Mode Coverage:** PARTIAL (BonusTracker seeded but no receipt history)
**Test Complexity:** MEDIUM
**Notes:** CRITICAL UNKNOWN at models/bonus.py:36 -- deficit_resets_annually flag needs practice admin confirmation. threshold_confirmed defaults False. Quarterly threshold $105,000, multiplier 0.25.

---

## F-008: Care Gap Detection
**Status:** BUILT
**Route(s):** `/caregap`, `/caregap/patient/<mrn>`, `/caregap/panel`, `/caregap/outreach`, `/caregap/print-handout/<mrn>`, `/api/caregap/rules`, `/api/caregap/dismiss`, `/api/caregap/address`
**Model(s):** CareGap, CareGapRule, PreventiveServiceRecord
**Service(s):** agent/caregap_engine.py
**API Dependencies:** NONE (rules are local)
**Depends On:** F-001, F-004, F-005
**Required For:** F-006 (CareGapsDetector), F-011
**Demo Mode Coverage:** YES
**Test Complexity:** MEDIUM
**Notes:** 20+ care gap rules covering USPSTF screenings. Feature-gated via @require_feature().

---

## F-009: Lab Tracking
**Status:** BUILT
**Route(s):** `/labtrack`, `/labtrack/patient/<mrn>`, `/api/labtrack/add`, `/api/labtrack/result`, `/api/labtrack/archive`
**Model(s):** LabTrack, LabResult, LabPanel
**Service(s):** None (direct model queries)
**API Dependencies:** NONE
**Depends On:** F-001, F-004
**Required For:** F-013 (monitoring schedule uses lab data)
**Demo Mode Coverage:** PARTIAL (lab tracks seeded for some demo patients)
**Test Complexity:** LOW
**Notes:** Feature-gated. Status calculation: critical/overdue/due_soon/on_track. Trend tracking: up/down/stable.

---

## F-010: Revenue Reporting
**Status:** BUILT
**Route(s):** `/revenue`, `/revenue/full`, `/api/revenue/summary`, `/api/revenue/dx-family`
**Model(s):** BillingOpportunity, DiagnosisRevenueProfile
**Service(s):** None (aggregation queries)
**API Dependencies:** NONE
**Depends On:** F-001, F-006
**Required For:** None
**Demo Mode Coverage:** PARTIAL
**Test Complexity:** LOW
**Notes:** Full revenue report with dx family breakdown.

---

## F-011: Morning Briefing and Intelligence
**Status:** BUILT
**Route(s):** `/briefing`, `/briefing/commute`, `/api/intelligence/morning-prep`
**Model(s):** Schedule, CareGap, MonitoringSchedule, BillingOpportunity
**Service(s):** api_scheduler.py (morning_briefing_prep), monitoring_rule_engine.py
**API Dependencies:** Open-Meteo (weather), HealthFinder
**Depends On:** F-002, F-008, F-013
**Required For:** None
**Demo Mode Coverage:** PARTIAL (needs schedule data)
**Test Complexity:** MEDIUM
**Notes:** Background job runs at configurable time. Includes weather, care gaps, monitoring alerts, risk scores.

---

## F-012: Billing Campaigns and ROI
**Status:** BUILT
**Route(s):** `/campaigns`, `/admin/billing-roi`, `/api/campaigns/create`, `/api/campaigns/update`
**Model(s):** BillingCampaign
**Service(s):** None
**API Dependencies:** NONE
**Depends On:** F-001, F-006
**Required For:** None
**Demo Mode Coverage:** PARTIAL
**Test Complexity:** LOW
**Notes:** Admin ROI dashboard with campaign tracking.

---

## F-013: Medication Monitoring
**Status:** BUILT
**Route(s):** `/monitoring/calendar`, `/admin/rules-registry`, `/admin/med-catalog`, `/admin/med-coverage`, `/admin/med-testing`, `/admin/med-diffs`
**Model(s):** MonitoringRule, MonitoringSchedule, MonitoringRuleOverride, MonitoringEvaluationLog, MonitoringRuleTestResult, MonitoringRuleDiff, MedicationCatalogEntry, REMSTrackerEntry
**Service(s):** monitoring_rule_engine.py, med_catalog_service.py, med_override_service.py, med_coverage_service.py, med_test_service.py
**API Dependencies:** RxNorm (drug classification), RxClass, DailyMed, VSAC
**Depends On:** F-001, F-004, F-005
**Required For:** F-006 (ChronicMonitoringDetector), F-011
**Demo Mode Coverage:** YES (monitoring rules seeded, schedules generated)
**Test Complexity:** HIGH
**Notes:** 6-step waterfall engine. REMS tracker for high-risk drugs. Medication master catalog with auto-discovery from patient data. 5 admin pages for management.

---

## F-014: Immunization Tracking and VIIS
**Status:** BUILT
**Route(s):** Via F-004 patient chart (immunizations widget), `/api/patient/<mrn>/viis-status`
**Model(s):** PatientImmunization, ImmunizationSeries, VIISCheck, VIISBatchRun
**Service(s):** immunization_engine.py, viis_batch.py
**API Dependencies:** VIIS (Virginia Immunization Information System -- Playwright scraper)
**Depends On:** F-001, F-004
**Required For:** F-008 (vaccine care gaps)
**Demo Mode Coverage:** YES (immunization data seeded for demo patients)
**Test Complexity:** MEDIUM
**Notes:** VIIS batch automation configurable via user settings. 8 vaccine groups tracked. Seasonal alerts for flu/COVID.

---

## F-015: Drug Safety and Pricing
**Status:** BUILT
**Route(s):** `/api/medref/pricing`, `/api/patient/<mrn>/pricing`
**Model(s):** RxNormCache, FdaLabelCache, RecallCache
**Service(s):** pricing_service.py (3-tier waterfall), cost_plus_service.py, goodrx_service.py, drug_assistance_service.py, nadac_service.py
**API Dependencies:** Cost Plus Drugs (T1), GoodRx HMAC (T2), NeedyMeds/RxAssist (T3), NADAC, OpenFDA (labels, recalls, adverse events)
**Depends On:** F-001, F-004
**Required For:** F-016
**Demo Mode Coverage:** PARTIAL (pricing requires live API calls or cached data)
**Test Complexity:** HIGH
**Notes:** Three-tier pricing waterfall with badge colors. FAERS adverse event lookup. Recall alerts.

---

## F-016: Patient Education
**Status:** BUILT
**Route(s):** Via F-004 patient chart
**Model(s):** None (generated content)
**Service(s):** MedlinePlus API, HealthFinder API
**API Dependencies:** MedlinePlus, HealthFinder
**Depends On:** F-004, F-015
**Required For:** None
**Demo Mode Coverage:** PARTIAL
**Test Complexity:** LOW
**Notes:** Auto-draft education messages with pricing info injection.

---

## F-017: Time Tracking
**Status:** BUILT
**Route(s):** `/timer`, `/timer/room-widget` (public), `/timer/face/room-toggle` (public)
**Model(s):** TimeLog
**Service(s):** None
**API Dependencies:** NONE
**Depends On:** F-001
**Required For:** F-006 (billing uses time data for E/M level)
**Demo Mode Coverage:** YES
**Test Complexity:** LOW
**Notes:** Face-to-face timer, idle detection, AWV checklist integration. Room widget is public (no auth).

---

## F-018: Order Sets
**Status:** BUILT
**Route(s):** `/orders`, `/orders/master`, `/api/orders/execute`, `/api/orders/create`, `/api/orders/fork`
**Model(s):** OrderSet, OrderItem, MasterOrder, OrderSetVersion, OrderExecution, OrderExecutionItem
**Service(s):** None (AC automation via agent)
**API Dependencies:** NONE
**Depends On:** F-001, Amazing Charts (for execution)
**Required For:** None
**Demo Mode Coverage:** YES (master orders seeded via seed_master_orders.py)
**Test Complexity:** MEDIUM
**Notes:** Version tracking, fork/share, execution logging. AC automation uses UIA+Win32.

---

## F-019: Inbox Monitoring
**Status:** BUILT
**Route(s):** `/inbox`, `/api/inbox/snapshot`, `/api/inbox/hold`, `/api/inbox/resolve`
**Model(s):** InboxSnapshot, InboxItem
**Service(s):** agent/inbox_monitor.py, agent/inbox_reader.py, agent/inbox_digest.py
**API Dependencies:** NONE (AC OCR-based)
**Depends On:** F-001, Amazing Charts
**Required For:** F-011 (morning briefing uses inbox counts)
**Demo Mode Coverage:** NO (requires live AC)
**Test Complexity:** HIGH
**Notes:** Agent-side OCR reads AC inbox. Priority escalation for critical values.

---

## F-020: On-Call Notes and Handoff
**Status:** BUILT
**Route(s):** `/oncall`, `/oncall/new`, `/oncall/<id>`, `/oncall/export`, `/oncall/handoff/<token>` (public)
**Model(s):** OnCallNote, HandoffLink
**Service(s):** None
**API Dependencies:** NONE
**Depends On:** F-001
**Required For:** None
**Demo Mode Coverage:** YES
**Test Complexity:** LOW
**Notes:** Token-based public handoff links with expiration.

---

## F-021: Secure Messaging
**Status:** BUILT
**Route(s):** `/messages`, `/messages/new`, `/api/messages/send`, `/api/messages/recurring`
**Model(s):** DelayedMessage
**Service(s):** None
**API Dependencies:** NONE
**Depends On:** F-001
**Required For:** None
**Demo Mode Coverage:** YES
**Test Complexity:** LOW
**Notes:** Scheduled and recurring message support.

---

## F-022: Notification System
**Status:** BUILT
**Route(s):** `/notifications`, `/api/notifications/mark-read`
**Model(s):** Notification
**Service(s):** agent/notifier.py (Pushover)
**API Dependencies:** Pushover API
**Depends On:** F-001
**Required For:** None
**Demo Mode Coverage:** YES (notifications seeded)
**Test Complexity:** LOW
**Notes:** Three-tier: P1 interrupt, P2 passive, P3 morning digest. Quiet hours 22:00-07:00.

---

## F-023: Medical Reference
**Status:** BUILT
**Route(s):** `/medref`, `/medref/review-needed`, `/api/medref/pricing`, `/api/medref/dismiss`, `/api/medref/update-rxcui`
**Model(s):** MedicationEntry
**Service(s):** None
**API Dependencies:** NONE (local reference data)
**Depends On:** F-001
**Required For:** None
**Demo Mode Coverage:** YES
**Test Complexity:** LOW
**Notes:** Condition-based medication reference with guideline review flag.

---

## F-024: Clinical Calculators
**Status:** BUILT
**Route(s):** `/calculators`, `/calculators/<key>`, `/api/calculators/compute`, `/api/calculators/refresh`
**Model(s):** CalculatorResult
**Service(s):** calculator_engine.py, calculator_registry.py
**API Dependencies:** NONE
**Depends On:** F-001, F-004 (auto-prefill from patient data)
**Required For:** F-006 (CalculatorBillingDetector)
**Demo Mode Coverage:** YES
**Test Complexity:** MEDIUM
**Notes:** BMI, LDL, PREVENT, GAD-7, Wells DVT, AUDIT-C, C-SSRS, Ottawa Ankle, CRAFFT, pack-years. Semi-auto prefill from EHR data. Score trend tracking with threshold alerts.

---

## F-025: CCM (Chronic Care Management)
**Status:** BUILT
**Route(s):** `/ccm`, `/api/ccm/enroll`, `/api/ccm/time-entry`, `/api/ccm/bill`
**Model(s):** CCMEnrollment, CCMTimeEntry
**Service(s):** None
**API Dependencies:** NONE
**Depends On:** F-001, F-004
**Required For:** F-006 (CCMDetector)
**Demo Mode Coverage:** YES (enrollments seeded for demo patients)
**Test Complexity:** MEDIUM
**Notes:** Monthly minute tracking, consent workflow, billing readiness check. CPT 99490/99439/99487/99489.

---

## F-026: TCM (Transitional Care Management)
**Status:** BUILT
**Route(s):** `/tcm`, `/api/tcm/create`, `/api/tcm/update`
**Model(s):** TCMWatchEntry
**Service(s):** None
**API Dependencies:** NONE
**Depends On:** F-001, F-004
**Required For:** F-006 (TCMDetector)
**Demo Mode Coverage:** YES (TCM entries seeded)
**Test Complexity:** MEDIUM
**Notes:** 30-day post-discharge window. 2-business-day contact deadline. 99495 (moderate) / 99496 (high complexity).

---

## F-027: Controlled Substance Tracker
**Status:** BUILT
**Route(s):** `/tools/cs-tracker`, `/tools/cs-calculator`, `/api/tools/cs/add`, `/api/tools/cs/fill`
**Model(s):** ControlledSubstanceEntry
**Service(s):** None
**API Dependencies:** NONE
**Depends On:** F-001
**Required For:** None
**Demo Mode Coverage:** YES
**Test Complexity:** LOW
**Notes:** DEA schedule tracking, refill date calculation, PDMP/UDS due alerts.

---

## F-028: Prior Authorization
**Status:** BUILT
**Route(s):** `/tools/pa`, `/tools/pa-library`, `/api/tools/pa/generate`, `/api/tools/pa/submit`
**Model(s):** PriorAuthorization
**Service(s):** None
**API Dependencies:** NONE
**Depends On:** F-001
**Required For:** None
**Demo Mode Coverage:** YES
**Test Complexity:** LOW
**Notes:** Auto-generated PA narratives with clinical justification.

---

## F-029: Dot Phrases and Macros
**Status:** BUILT
**Route(s):** `/tools/dot-phrases`, `/tools/macros`, `/tools/macro-recorder`, `/api/tools/dot-phrases/sync`
**Model(s):** (inline in tools routes)
**Service(s):** utils/ahk_generator.py
**API Dependencies:** NONE
**Depends On:** F-001
**Required For:** None
**Demo Mode Coverage:** YES
**Test Complexity:** LOW
**Notes:** AHK v1.1 script generation. Starter pack import/fork sharing.

---

## F-030: Tickler System
**Status:** BUILT
**Route(s):** `/tickler`, `/api/tickler/create`, `/api/tickler/complete`
**Model(s):** Tickler
**Service(s):** None
**API Dependencies:** NONE
**Depends On:** F-001
**Required For:** None
**Demo Mode Coverage:** YES
**Test Complexity:** LOW
**Notes:** Provider-to-MA delegation. Recurring ticklers.

---

## F-031: Telehealth and Communication Log
**Status:** BUILT
**Route(s):** `/telehealth`, `/api/telehealth/log`, `/api/telehealth/billing-check`
**Model(s):** CommunicationLog
**Service(s):** telehealth_engine.py
**API Dependencies:** NONE
**Depends On:** F-001
**Required For:** F-006 (TelehealthDetector, BHIDetector)
**Demo Mode Coverage:** YES
**Test Complexity:** MEDIUM
**Notes:** Phone, portal, video visit logging with billing code generation.

---

## F-032: Result Templates
**Status:** BUILT
**Route(s):** `/tools/result-templates`, `/api/tools/result-templates/create`, `/api/tools/result-templates/fork`
**Model(s):** ResultTemplate
**Service(s):** None
**API Dependencies:** NONE
**Depends On:** F-001
**Required For:** None
**Demo Mode Coverage:** YES
**Test Complexity:** LOW
**Notes:** Normal/abnormal/critical/follow-up/referral categories. Legal review flag.

---

## F-033: Note Reformatter
**Status:** BUILT
**Route(s):** `/tools/reformatter`, `/api/tools/reformatter/reformat`
**Model(s):** ReformatLog
**Service(s):** agent/note_reformatter.py, agent/note_parser.py, agent/note_classifier.py
**API Dependencies:** NONE
**Depends On:** F-001
**Required For:** None
**Demo Mode Coverage:** YES
**Test Complexity:** MEDIUM
**Notes:** One-click note acceptance with template intelligence. Discarded items logged to JSON per HIPAA.

---

## F-034: Admin Panel
**Status:** BUILT
**Route(s):** `/admin/dashboard`, `/admin/users`, `/admin/config`, `/admin/audit-log`, `/admin/practice`, `/admin/tools`, `/admin/sitemap`, `/admin/updates`, `/admin/dismissal-audit`, `/admin/provider-defaults`, `/admin/api`
**Model(s):** User, AuditLog
**Service(s):** None
**API Dependencies:** NONE
**Depends On:** F-001
**Required For:** None
**Demo Mode Coverage:** YES
**Test Complexity:** MEDIUM
**Notes:** All routes require @require_role('admin'). User management, audit trail, config editing.

---

## F-035: Metrics and Analytics
**Status:** BUILT
**Route(s):** `/metrics`, `/metrics/weekly`
**Model(s):** Various (aggregation queries)
**Service(s):** None
**API Dependencies:** NONE
**Depends On:** F-001
**Required For:** None
**Demo Mode Coverage:** PARTIAL
**Test Complexity:** LOW
**Notes:** Feature-gated via @require_feature().

---

## F-036: AI Assistant Integration
**Status:** BUILT
**Route(s):** `/api/ai/query`, `/api/ai/acknowledge-hipaa` (public)
**Model(s):** User (ai_enabled, ai_api_key_enc, ai_hipaa_acknowledged)
**Service(s):** None (proxies to external AI provider)
**API Dependencies:** User-configured AI provider (OpenAI, Anthropic, etc.)
**Depends On:** F-001
**Required For:** None
**Demo Mode Coverage:** NO (requires user API key)
**Test Complexity:** LOW
**Notes:** HIPAA acknowledgment required before use. User brings own API key.

---

## F-037: Help System
**Status:** BUILT
**Route(s):** `/help`, `/api/help/guide`
**Model(s):** None (data/help_guide.json)
**Service(s):** None
**API Dependencies:** NONE
**Depends On:** None
**Required For:** None
**Demo Mode Coverage:** YES
**Test Complexity:** LOW
**Notes:** JSON-driven help with feature-level popovers.

---

## F-038: Benchmarks and QA Dashboard
**Status:** BUILT
**Route(s):** `/admin/benchmarks`, `/api/admin/benchmarks/run`, `/api/admin/benchmarks/results`
**Model(s):** BenchmarkRun, BenchmarkResult
**Service(s):** tests/benchmark_engine.py, tests/benchmark_fixtures.py
**API Dependencies:** NONE
**Depends On:** F-006, F-008, F-013
**Required For:** None
**Demo Mode Coverage:** YES (18 synthetic benchmark patients)
**Test Complexity:** MEDIUM
**Notes:** Performance benchmarks for billing, caregap, monitoring engines. Max timing thresholds in config.py.

---

## F-039: AC Chart-Open Detection Flag
**Status:** BUILT
**Route(s):** `/api/active-chart` (via dashboard blueprint)
**Model(s):** PatientRecord (read-only lookup)
**Service(s):** agent/ac_window.py (parse_chart_title, get_all_chart_windows), agent/mrn_reader.py (_write_active_chart)
**API Dependencies:** NONE
**Depends On:** F-001, Amazing Charts running
**Required For:** None
**Demo Mode Coverage:** YES (mock_get_all_chart_windows in tests/ac_mock.py)
**Test Complexity:** LOW
**Notes:** 5s polling from base.html. Reads data/active_chart.json written by agent. Config: CHART_FLAG_ENABLED, CHART_FLAG_STALE_SECONDS.

---

## F-040: Specialty Referral Letters
**Status:** BUILT
**Route(s):** `/tools/referral`, `/api/tools/referral/generate`
**Model(s):** ReferralLetter, PatientSpecialist
**Service(s):** None
**API Dependencies:** NPPES (NPI lookup)
**Depends On:** F-001, F-004
**Required For:** None
**Demo Mode Coverage:** YES
**Test Complexity:** LOW
**Notes:** 21 specialty templates supported.

---

## F-041: Coding Favorites and Pairings
**Status:** BUILT
**Route(s):** `/tools/coding`, `/api/tools/coding/favorite`, `/api/tools/coding/pair`
**Model(s):** CodeFavorite, CodePairing
**Service(s):** None
**API Dependencies:** NIH ICD-10 API
**Depends On:** F-001
**Required For:** None
**Demo Mode Coverage:** YES
**Test Complexity:** LOW
**Notes:** Use-count tracking, auto-pairing suggestions.

---

## F-042: Daily Summary and Rooming Sheet
**Status:** BUILT
**Route(s):** `/daily-summary`, `/daily-summary/print`, `/api/daily-summary/rooming-sheet`
**Model(s):** Schedule, PatientRecord, CareGap, MonitoringSchedule
**Service(s):** None
**API Dependencies:** NONE
**Depends On:** F-002, F-008, F-013
**Required For:** None
**Demo Mode Coverage:** YES
**Test Complexity:** LOW
**Notes:** Printable rooming sheet with care gaps and monitoring alerts.

---

## F-043: External API Integration Layer
**Status:** BUILT
**Route(s):** `/admin/api` (status dashboard)
**Model(s):** RxNormCache, Icd10Cache, FdaLabelCache, RecallCache, BillingRuleCache
**Service(s):** 28 API service modules in app/services/api/ (BaseAPIClient, CacheManager, rxnorm, openfda_labels, openfda_recalls, openfda_adverse_events, cost_plus_service, goodrx_service, drug_assistance_service, nadac_service, cms_pfs, cms_data, dailymed, clinical_trials, nppes, pubmed, medlineplus, healthfinder, loinc, umls, vsac, rxclass, open_meteo, icd10, nlm_conditions, rxnorm, cdc_immunizations, uptodate)
**API Dependencies:** ALL external APIs
**Depends On:** F-001
**Required For:** F-013, F-015, F-016
**Demo Mode Coverage:** PARTIAL (cache tables must be pre-populated)
**Test Complexity:** HIGH
**Notes:** Unified caching via BaseAPIClient. Offline fallback: stale cache -> hardcoded fallback -> "not available". Rate limiting and retry built in.

---

## F-044: Patient Generator
**Status:** BUILT
**Route(s):** `/patient-gen`, `/api/patient-gen/generate`
**Model(s):** PatientRecord (writes)
**Service(s):** None
**API Dependencies:** NONE
**Depends On:** F-001
**Required For:** None
**Demo Mode Coverage:** YES
**Test Complexity:** LOW
**Notes:** Generates synthetic patient records for testing.

---

## F-045: EOD Checker
**Status:** BUILT
**Route(s):** `/eod`
**Model(s):** Various (aggregation)
**Service(s):** agent/eod_checker.py
**API Dependencies:** NONE
**Depends On:** F-001
**Required For:** None
**Demo Mode Coverage:** YES
**Test Complexity:** LOW
**Notes:** End-of-day compliance checklist.

---

## F-046: UI Framework (CSS/JS Systems)
**Status:** BUILT
**Route(s):** None (global via base.html + main.css + main.js)
**Model(s):** None
**Service(s):** None
**API Dependencies:** NONE
**Depends On:** None
**Required For:** All UI features
**Demo Mode Coverage:** YES
**Test Complexity:** MEDIUM
**Notes:** 9 UI systems completed: sub-panels, popup taskbar, split view, PIP widgets, bookmarks, breadcrumbs, type-ahead, transitions, AI enhancements. Dark mode via [data-theme="dark"]. CSS custom properties in :root.

---

## F-047: Feature Tiers and Onboarding
**Status:** BUILT
**Route(s):** `/onboarding`, `/setup`
**Model(s):** User (preferences)
**Service(s):** utils/feature_gates.py
**API Dependencies:** NONE
**Depends On:** F-001
**Required For:** None
**Demo Mode Coverage:** YES
**Test Complexity:** LOW
**Notes:** Three tiers: Essential, Standard, Advanced. Progressive feature enablement.

---

## F-048: Agent Background Service
**Status:** BUILT
**Route(s):** Agent API on port 5001
**Model(s):** AgentLog, AgentError
**Service(s):** agent_service.py, agent/scheduler.py
**API Dependencies:** NONE
**Depends On:** F-001 (reads active_user.json)
**Required For:** F-003, F-005, F-019, F-039
**Demo Mode Coverage:** PARTIAL (AC_MOCK_MODE for testing)
**Test Complexity:** HIGH
**Notes:** Separate process from Flask. APScheduler with interval + cron jobs. System tray via pystray. Communicates via SQLite + data/active_user.json.

---

## Summary

| Status | Count |
|--------|-------|
| BUILT | 45 |
| PARTIAL | 3 (F-003, F-007, F-043) |
| PLANNED | 0 |
| **Total** | **48** |
