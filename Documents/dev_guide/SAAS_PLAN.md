# CareCompanion â†’ Cloud SaaS Transformation Plan
## Version 3.0 â€” Exhaustive Technical Implementation Guide
### Generated: 2026-03-22 | Machine-Readable Checkbox Format

---

> **Purpose:** This document is a ~5,000-line, machine-readable instruction guide that transforms CareCompanion
> from a single-practice desktop Flask application into a multi-tenant, FHIR-native, cloud-deployed B2B SaaS product.
> Every technical section uses `- [ ]` checkboxes so progress can be tracked programmatically.
> Business sections are preserved as-is for strategic context.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Technical Audit â€” Current Codebase](#2-technical-audit--current-codebase)
3. [Architecture â€” Cloud-Native Redesign](#3-architecture--cloud-native-redesign)
4. [Market Analysis & Positioning](#4-market-analysis--positioning)
5. [Product Packaging & Tiering](#5-product-packaging--tiering)
6. [Data Layer â€” SQLite â†’ PostgreSQL + Alembic](#6-data-layer--sqlite--postgresql--alembic)
7. [FHIR R4 Integration Layer](#7-fhir-r4-integration-layer)
8. [Multi-Tenancy Architecture](#8-multi-tenancy-architecture)
9. [Cloud Deployment â€” Docker / AWS / CI-CD](#9-cloud-deployment--docker--aws--ci-cd)
10. [MVP Scope â€” Phase 0 + Phase 1](#10-mvp-scope--phase-0--phase-1)
11. [FHIR Development & Testing Tools](#11-fhir-development--testing-tools)
12. [HIPAA & Security Compliance](#12-hipaa--security-compliance)
13. [Pricing Strategy](#13-pricing-strategy)
14. [Go-to-Market Plan](#14-go-to-market-plan)
15. [Multi-EMR Abstraction Layer](#15-multi-emr-abstraction-layer)
16. [Customer Success Framework](#16-customer-success-framework)
17. [Competitive Intelligence](#17-competitive-intelligence)
18. [Financial Projections](#18-financial-projections)
19. [Risk Register](#19-risk-register)
20. [Intellectual Property & Licensing](#20-intellectual-property--licensing)
21. [Regulatory & Compliance Roadmap](#21-regulatory--compliance-roadmap)
22. [Team & Hiring Plan](#22-team--hiring-plan)
23. [Partnership Strategy](#23-partnership-strategy)
24. [Success Metrics & KPIs](#24-success-metrics--kpis)
25. [90-Day Launch Checklist](#25-90-day-launch-checklist)
- [Appendix A â€” Technology Stack Reference](#appendix-a--technology-stack-reference)
- [Appendix B â€” FHIR Resource Quick Reference](#appendix-b--fhir-resource-quick-reference)
- [Appendix C â€” Glossary](#appendix-c--glossary)

---

# 1. Executive Summary

CareCompanion is a clinical workflow automation platform built for primary care. It currently runs as a
desktop application (Python/Flask/SQLite) tightly integrated with Amazing Charts EHR via screen automation
(PyAutoGUI + Tesseract OCR) and CDA XML parsing. The system detects billing opportunities across 25+
CPT categories, tracks USPSTF care gaps, monitors EHR inbox messages, and provides real-time clinical
decision support at the point of care.

**Current scale:** 1 practice, 2 providers, ~4,000 patients, 60+ database tables, 250+ API endpoints.

**Target state:** A cloud-hosted, FHIR-native, multi-tenant B2B SaaS platform serving independent and
small-group primary care practices nationwide. The transformation replaces screen-scraping with
standards-based FHIR R4 APIs, SQLite with PostgreSQL, and single-user deployment with per-practice tenancy.

**Key value proposition:** Automated billing capture + care gap closure + clinical workflow optimization,
purpose-built for primary care â€” not a generic EHR add-on but a revenue intelligence and quality platform.

**Revenue model:** Per-provider monthly subscription ($299-$799/mo) with optional performance-based pricing
tied to incremental revenue captured.

---

# 2. Technical Audit â€” Current Codebase

> This section is an exhaustive, line-by-line inventory of every module, model, route, scheduled job,
> and configuration value in the current CareCompanion codebase. Each item is a checkbox task for
> cloud-readiness assessment.

## 2.1 Codebase Statistics

| Metric | Count |
|--------|-------|
| Python source files | 120+ |
| SQLAlchemy models | 24 distinct classes |
| Database tables | 60+ |
| Flask blueprints | 28 |
| API endpoints | 250+ |
| HTML templates | 111 |
| Billing detectors | 25+ |
| Care gap rules | 20 USPSTF defaults |
| Scheduled jobs | 19 APScheduler tasks |
| Migration scripts | 64 |
| Lines of Python | ~35,000 |

## 2.2 Application Entry Points

- [ ] `app.py` â€” Main Flask entry point; calls `create_app()`, registers blueprints, starts scheduler
- [ ] `launcher.py` â€” PyInstaller/desktop launcher; opens browser, manages tray icon
- [ ] `agent_service.py` â€” Background agent Windows service wrapper
- [ ] `build.py` â€” PyInstaller build script for `.exe` distribution
- [ ] `carecompanion.spec` â€” PyInstaller spec file

### 2.2.1 Cloud Migration Assessment for Entry Points
- [ ] `app.py` â†’ Keep as WSGI entry point; replace `app.run()` with Gunicorn in Docker
- [ ] `launcher.py` â†’ **REMOVE** â€” desktop-only; not needed in cloud
- [ ] `agent_service.py` â†’ **REMOVE** â€” Windows service; replace with Celery workers
- [ ] `build.py` â†’ **REMOVE** â€” PyInstaller not needed in cloud
- [ ] `carecompanion.spec` â†’ **REMOVE** â€” PyInstaller spec not needed

## 2.3 Configuration Audit (`config.py`)

### 2.3.1 Current Configuration Values â€” Must Migrate

**Application Settings:**
- [ ] `APP_VERSION = "1.1.2"` â†’ Move to environment variable `APP_VERSION`
- [ ] `HOST = "0.0.0.0"` â†’ Gunicorn bind address; keep as-is
- [ ] `PORT = 5000` â†’ Gunicorn port; keep as-is or use `$PORT`
- [ ] `DEBUG = False` â†’ Environment-based: `os.getenv("FLASK_DEBUG", "false")`

**Amazing Charts Settings (Desktop-Only â€” Remove in Cloud):**
- [ ] `AC_VERSION = "12.3.1"` â†’ **REMOVE** â€” replaced by FHIR
- [ ] `AC_BUILD = "297"` â†’ **REMOVE**
- [ ] `AC_PRACTICE_ID = 2799` â†’ **REMOVE** â€” replaced by `Practice.id`
- [ ] `AC_PRACTICE_NAME = "Family Practice Associates..."` â†’ **REMOVE** â€” stored in Practice model
- [ ] `AC_LOGIN_USERNAME` â†’ **REMOVE** â€” FHIR uses OAuth2, not screen credentials
- [ ] `AC_LOGIN_PASSWORD` â†’ **REMOVE** â€” FHIR uses OAuth2

**Database Settings â€” Must Migrate:**
- [ ] `DATABASE_PATH = "data/carecompanion.db"` â†’ Replace with `DATABASE_URL` env var (PostgreSQL)
- [ ] `BACKUP_PATH = "data/backups/"` â†’ Replace with S3 bucket + automated pg_dump

**Inbox Settings â€” Transform:**
- [ ] `INBOX_CHECK_INTERVAL_MINUTES = 120` â†’ Keep as configurable per-practice setting
- [ ] `CRITICAL_VALUE_KEYWORDS = [...]` â†’ Move to Practice-level config in DB

**Clinical Summary Settings â€” Transform:**
- [ ] `CLINICAL_SUMMARY_EXPORT_FOLDER` â†’ **REMOVE** â€” FHIR replaces XML export
- [ ] `CLINICAL_SUMMARY_RETENTION_DAYS = 183` â†’ Keep as data retention policy setting

**OCR Coordinate Settings â€” Remove Entirely:**
- [ ] `PATIENT_LIST_ID_SEARCH_XY = (0, 0)` â†’ **REMOVE** â€” no screen automation in cloud
- [ ] `PATIENT_CHART_MRN_XY = (0, 0)` â†’ **REMOVE**
- [ ] `SELECT_TEMPLATE_DROPDOWN_XY = (0, 0)` â†’ **REMOVE**
- [ ] `EXPORT_CLIN_SUM_MENU_XY = (0, 0)` â†’ **REMOVE**
- [ ] `EXPORT_BUTTON_XY = (0, 0)` â†’ **REMOVE**

**OCR/Tesseract Settings â€” Remove:**
- [ ] `TESSERACT_PATH` â†’ **REMOVE** â€” no OCR in cloud

**NetPractice Settings â€” Transform:**
- [ ] `NETPRACTICE_URL` â†’ Move to Practice-level integrations config
- [ ] `NETPRACTICE_CLIENT_NUMBER` â†’ Move to Practice-level integrations config

**API Keys â€” Move to Secrets Manager:**
- [ ] `OPENFDA_API_KEY` â†’ AWS Secrets Manager / Vault
- [ ] `PUBMED_API_KEY` â†’ AWS Secrets Manager / Vault
- [ ] `LOINC_USERNAME` â†’ AWS Secrets Manager / Vault
- [ ] `UMLS_API_KEY` â†’ AWS Secrets Manager / Vault

### 2.3.2 New Cloud Configuration Required
- [ ] `DATABASE_URL` â€” PostgreSQL connection string (env var)
- [ ] `REDIS_URL` â€” Redis connection string for Celery broker + cache
- [ ] `SECRET_KEY` â€” Flask session secret (env var, rotate quarterly)
- [ ] `FHIR_BASE_URL` â€” Per-practice FHIR server endpoint (stored in Practice model)
- [ ] `FHIR_CLIENT_ID` â€” OAuth2 client ID for FHIR SMART on FHIR (per-practice)
- [ ] `FHIR_CLIENT_SECRET` â€” OAuth2 client secret (Secrets Manager, per-practice)
- [ ] `STRIPE_SECRET_KEY` â€” Stripe billing API key
- [ ] `STRIPE_WEBHOOK_SECRET` â€” Stripe webhook signing secret
- [ ] `SENDGRID_API_KEY` â€” Email delivery
- [ ] `SENTRY_DSN` â€” Error tracking
- [ ] `AWS_S3_BUCKET` â€” Document/backup storage
- [ ] `AWS_REGION` â€” AWS deployment region
- [ ] `CELERY_BROKER_URL` â€” Same as REDIS_URL or separate
- [ ] `CELERY_RESULT_BACKEND` â€” Redis or database
- [ ] `LOG_LEVEL` â€” Configurable logging level (default: INFO)
- [ ] `ALLOWED_ORIGINS` â€” CORS whitelist for API access

## 2.4 Agent Modules Audit (`agent/`)

### 2.4.1 `agent/clinical_summary_parser.py` â€” CDA XML Parser
**Current:** Parses HL7 CDA XML exports from Amazing Charts; uses PyAutoGUI to trigger export.
**Cloud Fate:** FHIR replaces XML. The parsing logic for medications, allergies, diagnoses maps to FHIR resources.

**Functions requiring migration:**
- [ ] `_hash_mrn(mrn)` â†’ **KEEP** â€” MRN hashing still needed for PHI de-identification
- [ ] `open_patient_chart(mrn, patient_name)` â†’ **REMOVE** â€” PyAutoGUI screen automation
- [ ] `export_clinical_summary(mrn)` â†’ **REMOVE** â€” replaced by FHIR DocumentReference fetch
- [ ] `parse_clinical_summary(xml_path)` â†’ **REPLACE** â€” with FHIR resource parsers
- [ ] `_extract_section(root, loinc_code)` â†’ **REPLACE** â€” FHIR Observation/Condition lookups by LOINC
- [ ] `_parse_code_from_text(text)` â†’ **KEEP** â€” regex ICD-10 parsing still useful for FHIR CodeableConcepts
- [ ] `_parse_date(date_str)` â†’ **KEEP** â€” date parsing utility
- [ ] `detect_new_medications(user_id, mrn, parsed)` â†’ **TRANSFORM** â€” compare FHIR MedicationStatement vs local DB
- [ ] `store_parsed_summary(...)` â†’ **TRANSFORM** â€” store from FHIR resources instead of XML
- [ ] `schedule_deletion(...)` â†’ **KEEP** â€” data retention policy enforcement
- [ ] `ClinicalSummaryHandler` (watchdog) â†’ **REMOVE** â€” file watching not needed; FHIR subscription replaces

**CDA sections parsed (map to FHIR):**
- [ ] medications â†’ `MedicationStatement` / `MedicationRequest`
- [ ] allergies â†’ `AllergyIntolerance`
- [ ] diagnoses â†’ `Condition`
- [ ] vitals â†’ `Observation` (category: vital-signs)
- [ ] lab_results â†’ `Observation` (category: laboratory)
- [ ] immunizations â†’ `Immunization`
- [ ] social_history â†’ `Observation` (category: social-history)
- [ ] encounter_reason â†’ `Encounter.reasonCode`
- [ ] instructions â†’ `CarePlan`
- [ ] goals â†’ `Goal`
- [ ] health_concerns â†’ `Condition` (category: health-concern)
- [ ] patient_demographics â†’ `Patient`
- [ ] insurance â†’ `Coverage`

### 2.4.2 `agent/mrn_reader.py` â€” Screen OCR MRN Detection
**Cloud Fate:** **REMOVE ENTIRELY** â€” no screen scraping in cloud.
- [ ] `read_mrn_from_screen()` â†’ **REMOVE** â€” replaced by FHIR Patient context from session
- [ ] `get_active_patient()` â†’ **REPLACE** â€” with `session['active_patient_fhir_id']`
- [ ] OCR region detection â†’ **REMOVE**

### 2.4.3 `agent/ocr_helpers.py` â€” Tesseract OCR Utilities
**Cloud Fate:** **REMOVE ENTIRELY**
- [ ] `capture_region(x, y, w, h)` â†’ **REMOVE**
- [ ] `ocr_text(image)` â†’ **REMOVE**
- [ ] `find_text_on_screen(target)` â†’ **REMOVE**
- [ ] All coordinate-based detection â†’ **REMOVE**

### 2.4.4 `agent/pyautogui_runner.py` â€” Screen Automation
**Cloud Fate:** **REMOVE ENTIRELY**
- [ ] All click/type/screenshot functions â†’ **REMOVE**
- [ ] Window focus management â†’ **REMOVE**
- [ ] Keyboard shortcut simulation â†’ **REMOVE**

### 2.4.5 `agent/inbox_reader.py` â€” EHR Inbox Scraping
**Cloud Fate:** **TRANSFORM** â€” Replace screen scraping with FHIR Communication/Task resources.
- [ ] `read_inbox_messages()` â†’ **REPLACE** with FHIR `Communication?category=notification`
- [ ] `parse_message_details(msg)` â†’ **REPLACE** with FHIR Communication resource parsing
- [ ] `mark_as_read(msg_id)` â†’ **REPLACE** with FHIR Task status update
- [ ] Screen navigation logic â†’ **REMOVE**

### 2.4.6 `agent/inbox_monitor.py` â€” Inbox Polling
**Cloud Fate:** **TRANSFORM** â€” Replace polling with FHIR Subscription (webhook-based).
- [ ] Polling loop â†’ Replace with FHIR Subscription to `Communication` resource
- [ ] Critical value detection â†’ Keep logic, change data source to FHIR Observation (flags)
- [ ] Notification dispatch â†’ Keep; use WebSocket/push notification instead of desktop toast

### 2.4.7 `agent/inbox_digest.py` â€” Daily Inbox Summary
**Cloud Fate:** **KEEP** (transform data source)
- [ ] `generate_digest()` â†’ Keep logic; source from FHIR Communications instead of scraped messages
- [ ] Email delivery â†’ Replace local SMTP with SendGrid API
- [ ] Template rendering â†’ Keep Jinja templates

### 2.4.8 `agent/note_parser.py` â€” Clinical Note Parser
**Cloud Fate:** **TRANSFORM**
- [ ] Note text extraction â†’ FHIR DocumentReference
- [ ] Diagnosis extraction from notes â†’ Keep NLP logic
- [ ] Medication extraction â†’ Keep NLP logic

### 2.4.9 `agent/note_reformatter.py` â€” Note Reformatter
**Cloud Fate:** **KEEP** â€” valuable clinical tool
- [ ] `reformat_note(raw_text, template)` â†’ Keep; useful for FHIR DocumentReference content
- [ ] Template matching â†’ Keep

### 2.4.10 `agent/note_classifier.py` â€” Note Type Classification
**Cloud Fate:** **KEEP**
- [ ] `classify_note(text)` â†’ Keep; map to FHIR DocumentReference.type
- [ ] Classification categories â†’ Map to LOINC document type codes

### 2.4.11 `agent/notifier.py` â€” Desktop Notification System
**Cloud Fate:** **TRANSFORM** â€” desktop notifications â†’ WebSocket push + email
- [ ] `send_notification(title, body, priority)` â†’ WebSocket event + optional email
- [ ] Desktop toast â†’ **REMOVE** â€” replace with browser notification API
- [ ] Sound alerts â†’ **REMOVE** â€” replace with browser notification

### 2.4.12 `agent/eod_checker.py` â€” End-of-Day Checker
**Cloud Fate:** **KEEP** (transform delivery)
- [ ] `check_eod_tasks()` â†’ Keep logic; source data from FHIR/DB
- [ ] Desktop alert â†’ Email + in-app notification

### 2.4.13 `agent/scheduler.py` â€” APScheduler Background Jobs
**Cloud Fate:** **REPLACE** with Celery Beat for distributed scheduling.

**Job-by-job migration plan:**

| Job ID | Current | Cloud Replacement | Priority |
|--------|---------|-------------------|----------|
| `heartbeat` | 30s health check | Celery health check / ECS health endpoint | P0 |
| `mrn_reader` | 3s OCR poll | **REMOVE** â€” no screen reading | â€” |
| `inbox_check` | 120min poll | FHIR Subscription webhook OR Celery periodic | P1 |
| `inbox_digest` | Daily 17:00 | Celery Beat â†’ SendGrid | P1 |
| `callback_check` | 10min | Celery periodic task | P2 |
| `overdue_lab_check` | Daily 06:00 | Celery Beat + FHIR DiagnosticReport query | P1 |
| `xml_archive_cleanup` | Daily 02:00 | **REMOVE** â€” no XML in cloud | â€” |
| `xml_poll` | 30s | **REMOVE** â€” no XML in cloud | â€” |
| `weekly_summary` | Fri 17:00 | Celery Beat â†’ SendGrid | P2 |
| `monthly_billing` | 1st 07:00 | Celery Beat â†’ billing report generator | P1 |
| `deactivation_check` | 5min | Celery periodic + Stripe webhook (subscription cancel) | P1 |
| `delayed_message_sender` | 60s | Celery task queue (immediate dispatch) | P2 |
| `eod_check` | Daily 17:00 | Celery Beat â†’ WebSocket + email | P2 |
| `drug_recall_scan` | Daily 03:00 | Celery Beat â†’ openFDA API | P3 |
| `previsit_billing` | Daily 20:00 | Celery Beat â†’ billing pre-compute | P1 |
| `daily_backup` | Daily 01:00 | AWS RDS automated backup + Celery pg_dump to S3 | P0 |
| `escalation_check` | 2min | Celery periodic â†’ critical value alerts | P1 |
| `tcm_deadline_check` | Daily 06:00 | Celery Beat â†’ TCM reminders | P2 |
| `ccm_month_end` | 1st 02:00 | Celery Beat â†’ CCM billing rollup | P1 |
| `xml_cleanup` | Daily 02:00 | **REMOVE** â€” no XML | â€” |

**Summary: 5 jobs REMOVE, 15 jobs TRANSFORM to Celery Beat/tasks**

### 2.4.14 `agent/caregap_engine.py` â€” Care Gap Rules Engine
**Cloud Fate:** **KEEP** â€” core product value. Transform data source only.

**20 USPSTF Default Rules â€” Cloud Migration Checklist:**
- [ ] `colorectal_colonoscopy` â€” Age 45-75, all, 10yr interval, G0105/G0121 â†’ FHIR Procedure search
- [ ] `colorectal_fobt` â€” Age 45-75, all, 1yr, 82270 â†’ FHIR DiagnosticReport search
- [ ] `mammogram` â€” Age 40+, female, 2yr, 77067 â†’ FHIR DiagnosticReport search
- [ ] `cervical_pap` â€” Age 21-65, female, 3yr, 88141/Q0091 â†’ FHIR DiagnosticReport search
- [ ] `cervical_pap_hpv` â€” Age 30-65, female, 5yr, 88141/87624 â†’ FHIR DiagnosticReport search
- [ ] `lung_ldct` â€” Age 50-80, all, 1yr, G0297/71271 â†’ Risk: heavy_smoker â†’ FHIR Observation (smoking)
- [ ] `dexa_scan` â€” Age 65+, female, 2yr, 77080 â†’ FHIR Procedure search
- [ ] `hypertension_screen` â€” Age 18+, all, 1yr, 99473 â†’ FHIR Observation (blood-pressure)
- [ ] `diabetes_screen` â€” Age 35-70, all, 3yr, 82947/83036 â†’ Risk: overweight â†’ FHIR Observation (BMI)
- [ ] `lipid_screen` â€” Age 35+, all, 5yr, 80061 â†’ FHIR DiagnosticReport search
- [ ] `depression_screen` â€” Age 18+, all, 1yr, G0444/96127 â†’ FHIR QuestionnaireResponse (PHQ-9)
- [ ] `aaa_screen` â€” Age 65-75, male, one-time, G0389 â†’ Risk: ever_smoked â†’ FHIR Observation
- [ ] `fall_risk` â€” Age 65+, all, 1yr, 99420 â†’ FHIR RiskAssessment
- [ ] `hiv_screen` â€” Age 15-65, all, one-time, 86701/87389 â†’ FHIR DiagnosticReport
- [ ] `flu_vaccine` â€” Age 18+, all, 1yr, 90688/90471 â†’ FHIR Immunization search
- [ ] `covid_vaccine` â€” Age 18+, all, 1yr, 91309/0074A â†’ FHIR Immunization search
- [ ] `shingrix` â€” Age 50+, all, series, 90750/90471 â†’ FHIR Immunization search
- [ ] `tdap` â€” Age 18+, all, 10yr, 90715/90471 â†’ FHIR Immunization search
- [ ] `pneumococcal` â€” Age 65+, all, series, 90677/90471 â†’ FHIR Immunization search
- [ ] Rule evaluation engine: `evaluate_care_gaps()` â†’ Keep algorithm; change `existing_gaps` source to FHIR

### 2.4.15 `agent/ac_window.py` â€” Amazing Charts Window Management
**Cloud Fate:** **REMOVE ENTIRELY**
- [ ] Window detection â†’ **REMOVE**
- [ ] Focus management â†’ **REMOVE**
- [ ] Screen coordinates â†’ **REMOVE**

## 2.5 App Factory Audit (`app/__init__.py`)

### 2.5.1 Flask Extensions â€” Cloud Migration
- [ ] `SQLAlchemy(db)` â†’ **KEEP** â€” change engine from SQLite to PostgreSQL
- [ ] `Flask-Login(login_manager)` â†’ **KEEP** â€” add JWT option for API clients
- [ ] `Flask-Bcrypt(bcrypt)` â†’ **KEEP** â€” password hashing
- [ ] `Flask-WTF(CSRFProtect)` â†’ **KEEP** â€” CSRF protection

### 2.5.2 Role-Based Access Control
Current RBAC structure:
```
ma:       [dashboard, orders, caregap, medref, patient_gen]
provider: [dashboard, orders, caregap, medref, timer, billing, inbox,
           oncall, labtrack, metrics, tools, reformatter, briefing, patient_gen]
admin:    [*]
```
- [ ] Add `practice_admin` role â€” can manage practice settings but not platform admin
- [ ] Add `billing_specialist` role â€” billing + revenue modules only
- [ ] Add `platform_admin` role â€” super-admin across all practices
- [ ] Move RBAC to database table (`Role`, `Permission`, `RolePermission`) for dynamic management
- [ ] Add per-practice role assignments (user can be admin at one practice, provider at another)

### 2.5.3 Context Processors â€” Cloud Updates
- [ ] `user_can_access(module)` â†’ **KEEP**, add practice context
- [ ] `feature_enabled(feat)` â†’ **KEEP**, add practice-level + subscription-tier feature flags
- [ ] `oncall_pending_count()` â†’ **KEEP**, add practice filter
- [ ] `user_can_use_ai()` â†’ **KEEP**, gate by subscription tier
- [ ] `app_version` â†’ Source from env var, not hardcoded
- [ ] Add `current_practice` context processor for multi-practice users

### 2.5.4 Request Logging / Audit
- [ ] AuditLog `after_request` handler â†’ **KEEP**, add `practice_id` column
- [ ] JSON log handler (TimedRotatingFileHandler) â†’ Replace with CloudWatch/structured logging
- [ ] Midnight rotation â†’ **REMOVE** â€” CloudWatch handles retention
- [ ] Error handlers (404, 500) â†’ **KEEP**, add Sentry integration

## 2.6 Billing Engine Audit (`billing_engine/`)

### 2.6.1 Engine Architecture Overview
**Current:** Modular detector-based pipeline.
1. Discover all `BaseDetector` subclasses via `discover_detector_classes()`
2. Run each detector's `detect(patient_data, payer_context)` method
3. Deduplicate by `opportunity_code`
4. Score with 8-factor `ExpectedNetValueCalculator`
5. Sort by `expected_net_dollars` DESC

**Cloud Fate:** **KEEP ENTIRE ENGINE** â€” This is the core product value. Only change data sources.

### 2.6.2 Base Detector Interface (`base.py`)
- [ ] `BaseDetector.detect(patient_data, payer_context) â†’ list[BillingOpportunity]` â€” Keep interface
- [ ] `BaseDetector._get_rate(code) â†’ float` â€” Keep; CMS PFS rates still apply
- [ ] `BaseDetector._make_opportunity(**kwargs)` â€” Keep; add `practice_id` to kwargs
- [ ] Add `BaseDetector.fhir_resources_needed() â†’ list[str]` â€” declare which FHIR resources detector needs
- [ ] Add `BaseDetector.supports_payer(payer_type) â†’ bool` â€” filter detectors by payer

### 2.6.3 Engine Orchestrator (`engine.py`)
`BillingCaptureEngine` methods:
- [ ] `evaluate(patient_data)` â†’ **KEEP** â€” add `practice_id` to context
- [ ] `get_suppressions()` â†’ **KEEP**
- [ ] `log_suppressions(mrn_hash, user_id, visit_date)` â†’ Add `practice_id`
- [ ] `record_funnel_stage(opportunity_id, stage, actor, notes)` â†’ **KEEP** closed-loop tracking
- [ ] `_load_category_toggles(patient_data)` â†’ Add per-practice toggle overrides
- [ ] `_enrich_cost_share(opportunities, payer_context)` â†’ **KEEP**
- [ ] `_deduplicate_and_sort(opportunities, patient_data)` â†’ **KEEP**
- [ ] `_build_scorer(patient_data)` â†’ **KEEP**

### 2.6.4 Scoring Model (`scoring.py`)
**8-Factor Expected Net Value Calculator:**
- [ ] Factor 1: Collection rate by payer (25%) â€” Medicare 0.67, Commercial 0.57, Medicaid 0.60 â†’ Make configurable per-practice
- [ ] Factor 2: Denial risk proxy (15%) â€” adjustment rate from DiagnosisRevenueProfile â†’ Keep
- [ ] Factor 3: Documentation burden (10%) â€” LOW/MEDIUM/HIGH/VERY_HIGH â†’ Keep
- [ ] Factor 4: Completion probability (15%) â€” STRONG_STANDALONE 0.85, STACK_ENHANCER 0.75, CONDITIONAL 0.60, STACK_ONLY 0.50 â†’ Keep
- [ ] Factor 5: Time-to-cash (10%) â€” IMMEDIATE 0d, STANDARD 45d, COMPLEX 75d â†’ Make configurable
- [ ] Factor 6: Bonus timing urgency (10%) â€” quarter-end proximity + gap < $25k â†’ Keep
- [ ] Factor 7: Staff effort (5%) â€” provider-only/MA-handleable/multi-staff â†’ Keep
- [ ] Factor 8: Revenue magnitude (10%) â€” normalized to $300 â†’ Keep
- [ ] Add Factor 9 (optional): Historical capture rate per practice â€” learned from closed-loop data
- [ ] Make all factor weights configurable per practice via `PracticeSettings` model

### 2.6.5 Payer Routing (`payer_routing.py`)
- [ ] `get_payer_context(patient_data)` â†’ **KEEP**; normalize payer to 4 types
- [ ] Payer types: `medicare_b`, `medicare_advantage`, `medicaid`, `commercial`
- [ ] G-code routing: `use_g_codes = True` for traditional Medicare only
- [ ] Modifier 33 routing: `use_modifier_33 = True` for Medicaid, Commercial, MA
- [ ] Program eligibility: `awv_eligible`, `ccm_eligible`, `g2211_eligible`, `epsdt_eligible`, `cocm_eligible`
- [ ] Suppressed codes per payer type (Commercial: CCM/PCM flagged "uncertain")
- [ ] Cost share notes per payer type
- [ ] Add payer-specific fee schedule overrides (contracted rates vs CMS default)

### 2.6.6 Stack Builder (`stack_builder.py`)
**5 Visit Stack Templates:**
- [ ] `awv` â€” G0438/G0439 + cognitive + ACP + alcohol + obesity + care gaps + tobacco + G2211
- [ ] `dm_followup` â€” preventive E/M + A1C + UACR + lipid + G2211 + tobacco + care gaps
- [ ] `chronic_longitudinal` â€” preventive E/M + G2211 + tobacco + care gaps + labs
- [ ] `post_hospital` â€” TCM 99495/96 + labs (CBC, renal, LFT) + care gaps
- [ ] `acute` â€” preventive E/M + modifier 25 + pulse ox + venipuncture + prolonged

**Conflict Rules (hard blocks):**
- [ ] G2211 + MODIFIER_25 â€” cannot coexist on same claim
- [ ] CCM + PCM â€” cannot bill in same month
- [ ] BHI + COCM â€” cannot bill in same month

- [ ] `build_stack(patient_data, payer_context, visit_type, opportunities, encounter_duration)` â†’ **KEEP**
- [ ] `_match_template(visit_type)` â†’ **KEEP**
- [ ] `_check_conflict(code, included_codes)` â†’ **KEEP**
- [ ] `get_available_templates()` â†’ **KEEP**; add practice-custom templates
- [ ] Add ability for practices to define custom stack templates via admin UI

### 2.6.7 Code Specificity Recommender (`specificity.py`)
**Upgrade Paths:**
- [ ] `E78.5` (HLD unspecified) â†’ `E78.49`/`E78.2` based on lipid panel
- [ ] `E11.65`/`E11.69` (DM2) â†’ confirm/upgrade based on A1C > 7
- [ ] `F32.9` (MDD unspecified) â†’ `F32.0`/`F32.1`/`F32.2` based on PHQ-9 score
- [ ] `E03.9` (hypothyroidism) â†’ `E03.8` based on TSH + treatment
- [ ] `I10` (HTN) â†’ `I11.9` (hypertensive heart disease) or `I12.9` (hypertensive CKD) based on echo/eGFR
- [ ] `N18.9` (CKD unspecified) â†’ `N18.3`/`N18.4` based on eGFR stage
- [ ] Compliance guard: never recommends unsupported codes; missing evidence â†’ "Missing: [element]"

### 2.6.8 All 25+ Billing Detectors â€” Cloud Readiness

| # | Detector | CATEGORY | Key CPT Codes | Cloud Change | Status |
|---|----------|----------|---------------|--------------|--------|
| 1 | `ccm.py` | ccm | 99490, 99439, 99487, 99489, 99424, 99425 | FHIR Condition count | - [ ] |
| 2 | `awv.py` | awv | G0402, G0438, G0439, G2211, G0444, 99497, G0136, G0468 | FHIR Procedure history | - [ ] |
| 3 | `procedures.py` | procedures | 93000, 94060, 36415, 99203, 90834 | FHIR Condition triggers | - [ ] |
| 4 | `screening.py` | screening | 96110, 99408, 99409, 96127 | FHIR Patient age/sex | - [ ] |
| 5 | `vaccine_admin.py` | vaccines | 90471, 90472, G0008-G0010 | FHIR Immunization | - [ ] |
| 6 | `tcm.py` | tcm | 99495, 99496, 99497, 99498 | FHIR Encounter (discharge) | - [ ] |
| 7 | `tobacco.py` | tobacco | 99406, 99407, G0436, G0437 | FHIR Observation (smoking) | - [ ] |
| 8 | `alcohol.py` | alcohol | G0442, 99408 | FHIR Observation (AUDIT) | - [ ] |
| 9 | `cognitive.py` | cognitive | G0444, 96127, 96131 | FHIR QuestionnaireResponse | - [ ] |
| 10 | `obesity.py` | obesity | G0446, G0447, 97802, 97803 | FHIR Observation (BMI) | - [ ] |
| 11 | `pediatric.py` | pediatric | 96110, 99385-87 | FHIR Patient (age) | - [ ] |
| 12 | `preventive.py` | preventive | 99383-87, 99391-97 | FHIR Patient age/sex | - [ ] |
| 13 | `rpm.py` | rpm | 99457, 99458, 99091 | FHIR Device + Observation | - [ ] |
| 14 | `chronic_monitoring.py` | chronic_monitoring | MON_* | FHIR Observation (labs) | - [ ] |
| 15 | `em_addons.py` | em_addons | 99417, 99415, 99416 | FHIR Encounter (duration) | - [ ] |
| 16 | `g2211.py` | g2211 | G2211 | FHIR Condition (chronic) | - [ ] |
| 17 | `bhi.py` | bhi | 99492, 99493, 99494 | FHIR Condition (mental) | - [ ] |
| 18 | `acp.py` | acp | 99497, 99498 | FHIR CarePlan | - [ ] |
| 19 | `cocm.py` | cocm | 99492-94 (alt) | FHIR Condition (psych) | - [ ] |
| 20 | `counseling.py` | counseling | 99406-09, 97802 | FHIR Observation | - [ ] |
| 21 | `preventive_em.py` | preventive_em | 99213-15, 99285-87 | FHIR Patient + Encounter | - [ ] |
| 22 | `sti.py` | sti | (doc tracking) | FHIR DiagnosticReport | - [ ] |
| 23 | `sdoh.py` | sdoh | G0136, 96160-61 | FHIR Observation (SDOH) | - [ ] |
| 24 | `misc.py` | misc | Various | Keep as-is | - [ ] |
| 25 | `shared.py` | (helpers) | â€” | FHIR CodeSystem lookups | - [ ] |

## 2.7 Model Layer Audit (`models/`)

### 2.7.1 Complete Model Inventory â€” 24 Models

**Patient Data Models (FHIR-mapped):**
- [ ] `PatientRecord` â€” Per-patient metadata â†’ FHIR `Patient` resource
- [ ] `PatientVitals` â€” Vital signs â†’ FHIR `Observation` (vital-signs)
- [ ] `PatientMedication` â€” Drug records â†’ FHIR `MedicationStatement`
- [ ] `PatientDiagnosis` â€” ICD-10 codes â†’ FHIR `Condition`
- [ ] `PatientAllergy` â€” Allergies â†’ FHIR `AllergyIntolerance`
- [ ] `ImmunizationSeries` â€” Vaccine series â†’ FHIR `Immunization`

**Billing Models (Keep â€” add practice_id):**
- [ ] `BillingOpportunity` â€” Detected opportunities; add `practice_id` column
- [ ] `BillingRuleCache` â€” CMS fee schedule; shared across practices (no practice_id)
- [ ] `BonusTracker` â€” Bonus tracking; add `practice_id`

**Care Management Models (Keep â€” add practice_id):**
- [ ] `CareGap` â€” Per-patient gaps; add `practice_id`
- [ ] `CareGapRule` â€” USPSTF rules; default set + practice overrides
- [ ] `CCMEnrollment` â€” CCM enrollment; add `practice_id`
- [ ] `CCMTimeEntry` â€” CCM time logs; add `practice_id`

**Clinical Workflow Models (Keep â€” add practice_id):**
- [ ] `Schedule` â€” Appointments; add `practice_id`
- [ ] `TimeLog` â€” Visit durations; add `practice_id`
- [ ] `OnCallNote` â€” On-call records; add `practice_id`
- [ ] `LabTrack` â€” Lab tracking; add `practice_id`
- [ ] `InboxMessage` â€” EHR messages; add `practice_id`
- [ ] `CalculatorResult` â€” Calculator results; add `practice_id`

**Reference/Cache Models (Shared â€” no practice_id):**
- [ ] `RxClassCache` â€” Drug classification cache
- [ ] `FdaLabelCache` â€” FDA label data cache
- [ ] `FaersCache` â€” FAERS adverse event cache

**System Models (Platform-level):**
- [ ] `User` â€” Add `practice_id` FK + multi-practice junction table
- [ ] `AuditLog` â€” Add `practice_id` column
- [ ] `PracticeBookmark` â€” Add `practice_id`

## 2.8 Routes/Blueprints Audit

### 2.8.1 All 28 Blueprints â€” Cloud Readiness Assessment

| Blueprint | Endpoints | Cloud Status | Notes |
|-----------|-----------|--------------|-------|
| `auth_bp` | login, logout, register, pin, prefs | **KEEP** â€” add JWT | - [ ] |
| `dashboard_bp` | today view, schedule, estimator | **KEEP** â€” FHIR schedule | - [ ] |
| `caregap_bp` | gap overview, panel, outreach | **KEEP** â€” FHIR data source | - [ ] |
| `revenue_bp` | monthly reports, breakdown | **KEEP** | - [ ] |
| `billing_bp` | capture, review, dismiss | **KEEP** â€” core product | - [ ] |
| `admin_hub` | admin dash, analytics, sitemap | **KEEP** â€” add practice scope | - [ ] |
| `inbox_bp` | digest, message list, alerts | **KEEP** â€” FHIR Communication | - [ ] |
| `timer_bp` | visit timer, post-visit, close-loop | **KEEP** | - [ ] |
| `oncall_bp` | on-call dashboard, escalation | **KEEP** | - [ ] |
| `labtrack_bp` | ordering, results, overdue | **KEEP** â€” FHIR DiagnosticReport | - [ ] |
| `medref_bp` | drug lookup, warnings | **KEEP** | - [ ] |
| `tools_bp` | calculators, macros, templates | **KEEP** | - [ ] |
| `metrics_bp` | KPI dashboard, productivity | **KEEP** | - [ ] |
| `patient_gen_bp` | patient summary, AI assist | **KEEP** | - [ ] |
| `bonus_bp` | bonus tracking, projection | **KEEP** | - [ ] |
| `ccm_bp` | CCM enrollment, time logging | **KEEP** | - [ ] |
| `tcm_bp` | TCM billing | **KEEP** | - [ ] |
| `orders_bp` | order tablet | **TRANSFORM** â€” FHIR ServiceRequest | - [ ] |
| `daily_summary_bp` | EOD email report | **KEEP** â€” SendGrid | - [ ] |
| `intelligence_bp` | AI note gen, coding suggestions | **KEEP** â€” gate by tier | - [ ] |
| `netpractice_admin_bp` | NP session management | **TRANSFORM** â€” per-practice | - [ ] |
| `ai_api_bp` | AI API endpoints | **KEEP** â€” gate by subscription | - [ ] |
| `agent_api_bp` | Background agent status | **TRANSFORM** â€” Celery status | - [ ] |
| `message_bp` | In-app messaging | **KEEP** | - [ ] |
| `monitoring_bp` | Patient monitoring, alerts | **KEEP** | - [ ] |
| `telehealth_bp` | Telehealth sessions | **KEEP** | - [ ] |
| `campaigns_bp` | Outreach campaigns | **KEEP** | - [ ] |
| `help_bp` | Help pages, docs | **KEEP** | - [ ] |
| `calculator_bp` | Clinical calculators | **KEEP** | - [ ] |

**Summary: 0 removed, 4 transformed, 24 kept as-is with practice_id addition**

---

# 3. Architecture â€” Cloud-Native Redesign

> Complete architectural specification for transforming CareCompanion from a single-user desktop
> application to a multi-tenant cloud SaaS platform.

## 3.1 Current Architecture (Desktop)

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                  Desktop App                      â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚
â”‚  â”‚ Flask     â”‚  â”‚ Agent    â”‚  â”‚ PyAutoGUI    â”‚   â”‚
â”‚  â”‚ Web UI    â”‚  â”‚ Service  â”‚  â”‚ + Tesseract  â”‚   â”‚
â”‚  â”‚ (Jinja2)  â”‚  â”‚ (APSched)â”‚  â”‚ (OCR)        â”‚   â”‚
â”‚  â””â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚
â”‚        â”‚              â”‚               â”‚            â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”   â”‚
â”‚  â”‚           SQLite Database                   â”‚   â”‚
â”‚  â”‚           (data/carecompanion.db)           â”‚   â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚
â”‚        â”‚                              â”‚            â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”                â”Œâ”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚
â”‚  â”‚ CDA XML   â”‚                â”‚ Amazing Charts â”‚   â”‚
â”‚  â”‚ Parser    â”‚                â”‚ Screen Control â”‚   â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## 3.2 Target Architecture (Cloud SaaS)

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                        Load Balancer (ALB)                        â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                    â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    ECS Fargate Cluster                            â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚ Web Service    â”‚  â”‚ Celery Worker  â”‚  â”‚ Celery Beat        â”‚  â”‚
â”‚  â”‚ (Gunicorn +   â”‚  â”‚ (Background    â”‚  â”‚ (Periodic task     â”‚  â”‚
â”‚  â”‚  Flask)        â”‚  â”‚  tasks)        â”‚  â”‚  scheduler)        â”‚  â”‚
â”‚  â”‚ [2-4 replicas] â”‚  â”‚ [2-4 replicas] â”‚  â”‚ [1 replica]        â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚                   â”‚                     â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                     Shared Infrastructure                         â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚ PostgreSQL     â”‚  â”‚ Redis          â”‚  â”‚ S3                 â”‚  â”‚
â”‚  â”‚ (RDS)          â”‚  â”‚ (ElastiCache)  â”‚  â”‚ (Documents/Backups)â”‚  â”‚
â”‚  â”‚ Multi-tenant   â”‚  â”‚ Celery broker  â”‚  â”‚                    â”‚  â”‚
â”‚  â”‚ shared schema  â”‚  â”‚ + cache        â”‚  â”‚                    â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                     External Integrations                        â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚
â”‚  â”‚ FHIR R4  â”‚  â”‚ Stripe   â”‚  â”‚ SendGrid â”‚  â”‚ Sentry        â”‚   â”‚
â”‚  â”‚ Servers  â”‚  â”‚ Billing  â”‚  â”‚ Email    â”‚  â”‚ Monitoring    â”‚   â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## 3.3 Component Specifications

### 3.3.1 Web Service (Gunicorn + Flask)
- [ ] Base image: `python:3.11-slim`
- [ ] WSGI server: Gunicorn with 4 workers per container
- [ ] Worker class: `gevent` for async I/O (FHIR API calls)
- [ ] Port: 8000 (internal), 443 (ALB terminates TLS)
- [ ] Health check endpoint: `GET /health` â†’ 200 OK with `{"status": "healthy", "version": "x.y.z"}`
- [ ] Readiness check: `GET /ready` â†’ 200 only when DB + Redis connected
- [ ] Container resources: 0.5 vCPU, 1 GB RAM per replica
- [ ] Min replicas: 2, Max replicas: 4, scale on CPU > 70%
- [ ] Graceful shutdown: 30s drain period

### 3.3.2 Celery Worker
- [ ] Base image: Same as web service
- [ ] Concurrency: 4 prefork workers per container
- [ ] Queues: `default`, `billing`, `fhir_sync`, `email`, `reports`
- [ ] Container resources: 0.5 vCPU, 1 GB RAM per replica
- [ ] Min replicas: 2, Max replicas: 4, scale on queue depth > 100
- [ ] Task time limit: 300s (soft), 600s (hard)
- [ ] Task retry policy: exponential backoff, max 3 retries

### 3.3.3 Celery Beat (Scheduler)
- [ ] Single replica (leader election via redis lock)
- [ ] Beat schedule stored in Redis
- [ ] All 15 migrated APScheduler jobs â†’ Celery Beat periodic tasks
- [ ] Container resources: 0.25 vCPU, 512 MB RAM

### 3.3.4 PostgreSQL (RDS)
- [ ] Engine: PostgreSQL 15+
- [ ] Instance: `db.t3.medium` (2 vCPU, 4 GB RAM) â€” start
- [ ] Storage: 100 GB gp3, autoscale to 500 GB
- [ ] Multi-AZ: Yes (production), No (staging)
- [ ] Automated backups: Daily, 7-day retention
- [ ] Point-in-time recovery: Enabled
- [ ] Encryption at rest: AES-256 (AWS KMS)
- [ ] Encryption in transit: TLS 1.2+ (require SSL)
- [ ] Connection pooling: PgBouncer sidecar or RDS Proxy
- [ ] Max connections: 100 (with pooling, effective ~400)

### 3.3.5 Redis (ElastiCache)
- [ ] Engine: Redis 7+
- [ ] Instance: `cache.t3.micro` â€” start
- [ ] Cluster mode: Disabled (single shard)
- [ ] Encryption at rest: Yes
- [ ] Encryption in transit: Yes (TLS)
- [ ] Purpose: Celery broker + result backend + session cache + rate limiting

### 3.3.6 S3 (Object Storage)
- [ ] Bucket: `carecompanion-{env}-documents`
- [ ] Encryption: SSE-S3 (AES-256)
- [ ] Versioning: Enabled
- [ ] Lifecycle: Move to IA after 90 days, Glacier after 365 days
- [ ] Purpose: Database backups, exported reports, uploaded documents
- [ ] Access: IAM role (ECS task role), no public access

## 3.4 Network Architecture
- [ ] VPC: 10.0.0.0/16 with 3 AZs
- [ ] Public subnets: ALB only (10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24)
- [ ] Private subnets: ECS tasks (10.0.11.0/24, 10.0.12.0/24, 10.0.13.0/24)
- [ ] Database subnets: RDS only (10.0.21.0/24, 10.0.22.0/24, 10.0.23.0/24)
- [ ] NAT Gateway: 1 per AZ for outbound internet (FHIR API calls)
- [ ] Security groups: ALBâ†’ECS (8000), ECSâ†’RDS (5432), ECSâ†’Redis (6379)
- [ ] No direct internet access to ECS tasks or RDS
- [ ] VPC endpoints for S3 and ECR (avoid NAT costs)

## 3.5 Request Flow

### 3.5.1 Web Request Flow
```
Browser â†’ ALB (443/TLS) â†’ ECS Web (8000) â†’ Flask â†’ SQLAlchemy â†’ PostgreSQL
                                           â†’ Redis (session/cache)
                                           â†’ Celery (async tasks)
```

### 3.5.2 FHIR Sync Flow
```
Celery Beat (schedule) â†’ Celery Worker â†’ FHIR Server (OAuth2)
                                       â†’ Parse FHIR Resources
                                       â†’ Store in PostgreSQL
                                       â†’ Trigger billing evaluation
```

### 3.5.3 Billing Evaluation Flow
```
Patient visit detected â†’ Celery task (billing queue)
  â†’ BillingCaptureEngine.evaluate(patient_data)
    â†’ All 25 detectors run in parallel
    â†’ Deduplicate + Score (8-factor model)
    â†’ Store BillingOpportunity records
    â†’ WebSocket push to provider UI
    â†’ Email notification if critical
```


## 3.6 API Design Standards

### 3.6.1 REST API Conventions
- [ ] Base path: `/api/v1/` for all programmatic endpoints
- [ ] Content-Type: `application/json` for all request/response bodies
- [ ] Authentication: `Authorization: Bearer <JWT>` header on every request
- [ ] Pagination: cursor-based via `?cursor=<opaque>&limit=25` (default 25, max 100)
- [ ] Sorting: `?sort=created_at&order=desc` (default: descending by created)
- [ ] Filtering: `?status=active&provider_id=123` (query params per resource)
- [ ] Partial response: `?fields=id,name,status` to reduce payload size
- [ ] Rate limits returned in headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- [ ] Request ID: `X-Request-Id` header (UUID generated per request, returned in response, logged)

### 3.6.2 Standard Response Envelope
```json
{
  "data": { ... },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-01-15T10:30:00Z",
    "pagination": {
      "cursor": "eyJpZCI6IDEyM30=",
      "has_more": true,
      "limit": 25
    }
  }
}
```

### 3.6.3 Standard Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": [
      {"field": "email", "issue": "Invalid email format"},
      {"field": "npi", "issue": "NPI must be 10 digits"}
    ],
    "request_id": "uuid"
  }
}
```

### 3.6.4 HTTP Status Code Usage
| Code | Usage |
|------|-------|
| 200 | Successful GET, PUT, PATCH |
| 201 | Successful POST (resource created) |
| 204 | Successful DELETE (no body) |
| 400 | Validation error, malformed request |
| 401 | Missing or invalid authentication token |
| 403 | Authenticated but insufficient permissions / wrong practice |
| 404 | Resource not found |
| 409 | Conflict (duplicate resource, stale update) |
| 422 | Semantically invalid (valid JSON but business rule violation) |
| 429 | Rate limit exceeded |
| 500 | Internal server error (unexpected) |
| 502 | Upstream FHIR server error |
| 503 | Service temporarily unavailable (maintenance) |

### 3.6.5 API Versioning Strategy
- [ ] URL path versioning: `/api/v1/`, `/api/v2/`
- [ ] v1 supported for 12 months after v2 release
- [ ] Deprecation header: `Sunset: <date>` on deprecated endpoints
- [ ] Changelog published at `/api/changelog`
- [ ] Breaking changes only in major version bumps

## 3.7 WebSocket Architecture (Real-Time Notifications)

### 3.7.1 WebSocket Server
- [ ] Library: Flask-SocketIO with Redis message queue adapter
- [ ] Transport: WebSocket with long-polling fallback
- [ ] Namespace: `/notifications` (all real-time events)
- [ ] Authentication: JWT token sent on connection handshake
- [ ] Practice isolation: each client joins room `practice:{practice_id}`
- [ ] User-level targeting: also joins room `user:{user_id}`

### 3.7.2 WebSocket Events (Server to Client)
| Event | Payload | Trigger |
|-------|---------|---------|
| `billing:new` | `{opportunity_id, patient_name, cpt_code, estimated_value}` | New billing opportunity detected |
| `billing:updated` | `{opportunity_id, status, updated_by}` | Opportunity captured/dismissed |
| `caregap:new` | `{gap_id, patient_name, gap_type}` | New care gap identified |
| `caregap:resolved` | `{gap_id, resolved_by}` | Gap marked resolved |
| `fhir:sync_complete` | `{practice_id, patients_synced, errors}` | FHIR sync finished |
| `fhir:sync_error` | `{practice_id, error_message}` | FHIR sync failed |
| `system:maintenance` | `{message, scheduled_at, duration_minutes}` | Upcoming maintenance window |
| `notification:generic` | `{title, body, priority, action_url}` | General notification |

### 3.7.3 WebSocket Scaling
- [ ] Flask-SocketIO with Redis pub/sub adapter for multi-instance support
- [ ] Sticky sessions on ALB (required for Socket.IO handshake)
- [ ] Connection limit: 1,000 concurrent connections per ECS task
- [ ] Heartbeat interval: 25 seconds, timeout: 60 seconds
- [ ] Reconnection: exponential backoff (1s, 2s, 4s, 8s, max 30s)

## 3.8 Caching Strategy

### 3.8.1 Redis Cache Layers
| Cache Layer | Key Pattern | TTL | Purpose |
|-------------|-------------|-----|---------|
| Session | `session:{session_id}` | 30 min | Flask session data |
| User profile | `user:{user_id}:profile` | 5 min | Avoid DB hit per request |
| Practice config | `practice:{id}:config` | 10 min | Detector toggles, settings |
| Billing rules | `billing_rules:v{version}` | 24 hr | CMS fee schedule data |
| FHIR token | `fhir_token:{practice_id}` | token expiry - 60s | OAuth access token |
| Rate limit | `ratelimit:{user_id}:{endpoint}` | 60s | Per-user per-endpoint counter |
| Patient data | `patient:{fhir_id}:data` | 15 min | Most recent FHIR patient fetch |
| Care gap rules | `caregap_rules:default` | 24 hr | USPSTF default rule set |

### 3.8.2 Cache Invalidation Rules
- [ ] User profile cache: invalidate on any user settings change
- [ ] Practice config cache: invalidate on admin settings save
- [ ] Billing rules cache: invalidate on CMS fee schedule update (annual + hotfix)
- [ ] FHIR token cache: invalidate on 401 from FHIR server (trigger re-auth)
- [ ] Patient data cache: invalidate on FHIR sync completion for that patient
- [ ] Cache-aside pattern: check cache, miss, fetch from DB/API, store in cache

### 3.8.3 Cache Implementation
```python
import redis
from functools import wraps

cache = redis.Redis.from_url(app.config['REDIS_URL'])

def cached(key_template, ttl=300):
    """Decorator for caching function results in Redis."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = key_template.format(*args, **kwargs)
            result = cache.get(key)
            if result:
                return json.loads(result)
            result = f(*args, **kwargs)
            cache.setex(key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

## 3.9 Observability Stack

### 3.9.1 Structured Logging
- [ ] Library: Python `structlog` with JSON output
- [ ] Log format: JSON lines (one JSON object per log entry)
- [ ] Required fields: `timestamp`, `level`, `logger`, `request_id`, `practice_id`, `user_id`, `message`
- [ ] Sensitive data filter: strip PII (patient names, MRN, SSN) from all log output
- [ ] Log destination: CloudWatch Logs (via awslogs driver on ECS)
- [ ] Log retention: 90 days in CloudWatch, archived to S3 for 6 years (HIPAA)
- [ ] Log levels: DEBUG (dev only), INFO (request flow), WARNING (recoverable), ERROR (failure), CRITICAL (system down)

### 3.9.2 Structured Log Example
```json
{
  "timestamp": "2026-01-15T10:30:00.123Z",
  "level": "info",
  "logger": "billing_engine",
  "request_id": "abc-123",
  "practice_id": 42,
  "user_id": 7,
  "message": "Billing evaluation completed",
  "detectors_run": 25,
  "opportunities_found": 3,
  "duration_ms": 145
}
```

### 3.9.3 Application Metrics (CloudWatch + Sentry)
| Metric | Type | Alert Threshold |
|--------|------|-----------------|
| `http_request_duration_seconds` | Histogram | p99 > 2s |
| `http_requests_total` | Counter | tracking |
| `http_errors_total` | Counter | 5xx rate > 1% |
| `billing_evaluation_duration_ms` | Histogram | p99 > 1000ms |
| `billing_opportunities_detected` | Counter | tracking |
| `fhir_api_calls_total` | Counter | tracking |
| `fhir_api_errors_total` | Counter | error rate > 5% |
| `fhir_api_latency_ms` | Histogram | p99 > 3s |
| `celery_task_duration_seconds` | Histogram | tracking |
| `celery_task_failures_total` | Counter | failures > 10/hr |
| `celery_queue_depth` | Gauge | depth > 500 |
| `active_websocket_connections` | Gauge | tracking |
| `db_connection_pool_active` | Gauge | active > 80% of pool |
| `cache_hit_ratio` | Gauge | ratio < 0.5 |

### 3.9.4 Alerting Rules
- [ ] P0 (page immediately): 5xx error rate > 5%, database unreachable, Redis unreachable
- [ ] P1 (page within 15 min): 5xx error rate > 1%, FHIR sync failure for > 1 hour, Celery queue depth > 1000
- [ ] P2 (Slack alert): p99 latency > 3s, cache hit ratio < 50%, disk usage > 80%
- [ ] P3 (daily digest): elevated 4xx rates, slow queries > 1s, certificate expiry < 30 days
- [ ] Alert destinations: PagerDuty (P0/P1), Slack #alerts (P2), email digest (P3)

### 3.9.5 Distributed Tracing
- [ ] Library: OpenTelemetry Python SDK
- [ ] Trace propagation: W3C TraceContext headers
- [ ] Trace key spans: HTTP request, DB query, FHIR API call, Celery task dispatch
- [ ] Sampling: 100% for errors, 10% for successful requests (adjustable)
- [ ] Backend: AWS X-Ray (native ECS integration) or Jaeger (self-hosted)
- [ ] Correlation: `request_id` in logs links to trace ID for full request lifecycle

### 3.9.6 Health Check Details
```python
@app.route('/health')
def health():
    """Shallow health check -- app is running."""
    return jsonify({"status": "healthy", "version": __version__}), 200

@app.route('/ready')
def readiness():
    """Deep readiness check -- all dependencies available."""
    checks = {
        "database": check_db_connection(),
        "redis": check_redis_connection(),
        "fhir_token_valid": check_fhir_token_valid(),
    }
    all_ok = all(checks.values())
    return jsonify({"ready": all_ok, "checks": checks}), 200 if all_ok else 503
```

- [ ] `/health` returns 200 if process is alive (for ALB health check, every 30s)
- [ ] `/ready` returns 200 only when DB + Redis + FHIR token valid (for deploy readiness gate)
- [ ] `/metrics` Prometheus-format metrics endpoint (internal only, not exposed via ALB)

## 3.10 Database Connection Management

### 3.10.1 Connection Pooling Strategy
- [ ] SQLAlchemy pool: `QueuePool` with `pool_size=10`, `max_overflow=20`, `pool_timeout=30`
- [ ] Connection recycling: `pool_recycle=1800` (recycle connections after 30 min to avoid RDS idle timeout)
- [ ] Pre-ping: `pool_pre_ping=True` (test connection health before use)
- [ ] RDS Proxy: optional, use if connection count exceeds RDS max_connections
- [ ] Read replicas: not needed initially; add when read:write ratio exceeds 10:1
- [ ] Slow query log: enable PostgreSQL `log_min_duration_statement = 500` (log queries > 500ms)

### 3.10.2 SQLAlchemy Engine Configuration
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_timeout': 30,
    'pool_recycle': 1800,
    'pool_pre_ping': True,
    'connect_args': {
        'sslmode': 'require',
        'options': '-c statement_timeout=30000',  # 30s query timeout
    },
}
```

- [ ] Configure engine options in Flask app factory
- [ ] Set `statement_timeout` to 30s (prevent runaway queries)
- [ ] Verify SSL connection to RDS (require `sslmode=require`)
- [ ] Monitor pool exhaustion via `db_connection_pool_active` metric

## 3.11 Static Asset Architecture

### 3.11.1 Static File Serving
- [ ] Development: Flask serves static files from `/static/`
- [ ] Production: S3 bucket + CloudFront CDN for static assets
- [ ] Asset fingerprinting: `style.abc123.css` for cache busting
- [ ] CloudFront cache TTL: 1 year for fingerprinted assets, 5 min for `index.html`
- [ ] S3 bucket: `carecompanion-{env}-static`, private, CloudFront OAI access only
- [ ] Deployment: `collectstatic` step in CI/CD pipeline uploads to S3
---

# 4. Market Analysis & Positioning

**Target Market:** Independent and small-group primary care practices (1-10 providers) in the US.

**Market Size:**
- ~230,000 primary care physicians in the US
- ~60% in practices of 10 or fewer providers
- TAM: ~140,000 potential provider seats
- SAM (reachable in years 1-3): ~15,000 providers
- SOM (year 1 target): 100-200 providers

**Pain Points Addressed:**
1. **Revenue leakage** â€” missed billing codes cost practices $50,000-$150,000/provider/year
2. **Care gap tracking** â€” manual processes lead to missed preventive screenings
3. **Administrative burden** â€” 2+ hours/day on non-clinical tasks per provider
4. **Quality measure reporting** â€” MIPS/HEDIS compliance is complex and time-consuming

**Competitive Landscape:**
- **Athenahealth** â€” Full EHR; billing capture is secondary; enterprise pricing
- **Elation Health** â€” Primary-care focused EHR; limited billing intelligence
- **Aledade** â€” ACO model; requires network participation; not a standalone tool
- **Phreesia** â€” Patient intake focus; limited post-visit billing capture
- **CareCompanion differentiator:** Purpose-built billing intelligence + care gap engine + visit optimization
  for primary care, deployable alongside any EHR via FHIR

---

# 5. Product Packaging & Tiering

## 5.1 Tier Structure

### Essentials ($299/provider/month)
- Billing opportunity detection (core 15 detectors)
- Care gap dashboard (20 USPSTF rules)
- Visit timer + duration tracking
- Basic revenue reporting
- Email notifications (daily digest)
- Standard support (email, 48hr response)

### Professional ($499/provider/month)
- Everything in Essentials, plus:
- Full 25+ billing detector suite
- Code specificity recommendations
- Visit stack builder (5 templates)
- Advanced analytics + KPI dashboard
- CCM/TCM/RPM billing workflows
- Inbox monitoring + critical alerts
- Priority support (email + chat, 24hr response)

### Enterprise ($799/provider/month)
- Everything in Professional, plus:
- Custom billing detector configuration
- Custom care gap rules
- Multi-practice management
- API access for integrations
- Dedicated customer success manager
- Custom reporting + data exports
- SLA: 99.9% uptime guarantee
- Phone support (4hr response)

## 5.2 Add-Ons
- **AI Clinical Assistant:** +$99/provider/month â€” AI-powered note generation, coding suggestions
- **Performance Pricing:** Revenue share model â€” 5% of incremental captured revenue (instead of flat fee)
- **Additional Practice:** $199/month per additional practice location
- **Data Migration:** $2,000 one-time setup fee (waived for annual contracts)


---

# 6. Data Layer â€” SQLite â†’ PostgreSQL + Alembic

> Complete migration specification for every table, column, index, and constraint.
> Every model gets a checkbox for migration status.

## 6.1 Database Migration Strategy

### 6.1.1 Migration Approach
- [ ] Phase 1: Schema design in PostgreSQL (all models + multi-tenancy columns)
- [ ] Phase 2: Alembic migration framework setup
- [ ] Phase 3: Data migration scripts (SQLite â†’ PostgreSQL ETL)
- [ ] Phase 4: Verify data integrity post-migration
- [ ] Phase 5: Performance tuning (indexes, connection pooling)

### 6.1.2 Connection Configuration
```python
# Current (config.py)
DATABASE_PATH = "data/carecompanion.db"
DATABASE_URI = 'sqlite:///' + DATABASE_PATH.replace('\\', '/')

# Target (environment variable)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/carecompanion")
```

- [ ] Replace `sqlite:///` URI with `postgresql://` URI from env var
- [ ] Add connection pool settings: `pool_size=20`, `max_overflow=10`, `pool_timeout=30`, `pool_recycle=1800`
- [ ] Add `connect_args={"sslmode": "require"}` for production
- [ ] Configure SQLAlchemy engine options for PostgreSQL-specific features

### 6.1.3 Alembic Setup
- [ ] Install: `pip install alembic`
- [ ] Initialize: `alembic init migrations/alembic`
- [ ] Configure `alembic.ini` with `sqlalchemy.url` from env var
- [ ] Configure `env.py` to import all models for autogenerate
- [ ] Create initial migration: `alembic revision --autogenerate -m "initial_schema"`
- [ ] Set up multi-tenant migration helper for adding `practice_id` columns

### 6.1.4 SQLite â†’ PostgreSQL Type Mapping
| SQLite Type | PostgreSQL Type | Notes |
|-------------|-----------------|-------|
| `INTEGER PRIMARY KEY` | `SERIAL` / `BIGSERIAL` | Auto-increment |
| `TEXT` | `VARCHAR(n)` / `TEXT` | Add length constraints where appropriate |
| `REAL` | `NUMERIC(10,2)` / `FLOAT` | Use NUMERIC for money |
| `BLOB` | `BYTEA` | Binary data |
| `TEXT` (JSON stored) | `JSONB` | PostgreSQL native JSON |
| `TEXT` (datetime stored) | `TIMESTAMP WITH TIME ZONE` | Proper datetime type |
| `INTEGER` (boolean) | `BOOLEAN` | Native boolean |

## 6.2 Model-by-Model Migration Specification

### 6.2.1 `User` Model â€” Authentication & Multi-Tenancy

**Current columns:**
- [ ] `id` INTEGER PK â†’ `id SERIAL PRIMARY KEY`
- [ ] `username` TEXT UNIQUE â†’ `username VARCHAR(100) UNIQUE NOT NULL`
- [ ] `password_hash` TEXT â†’ `password_hash VARCHAR(255) NOT NULL`
- [ ] `role` TEXT â†’ `role VARCHAR(20) NOT NULL DEFAULT 'provider'` â€” CHECK constraint: ('provider','ma','admin','practice_admin','billing_specialist','platform_admin')
- [ ] `preferences` TEXT (JSON) â†’ `preferences JSONB DEFAULT '{}'::jsonb`
- [ ] `encrypted_credentials` TEXT â†’ `encrypted_credentials TEXT` â€” for EHR OAuth tokens
- [ ] `is_active` BOOLEAN â†’ `is_active BOOLEAN NOT NULL DEFAULT TRUE`
- [ ] `created_at` TEXT â†’ `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- [ ] `last_login` TEXT â†’ `last_login TIMESTAMPTZ`
- [ ] `pin_hash` TEXT â†’ `pin_hash VARCHAR(255)` â€” quick-access PIN

**New columns for multi-tenancy:**
- [ ] `practice_id` INTEGER FK â†’ `practices.id` â€” primary practice affiliation
- [ ] `email` VARCHAR(255) â€” for notifications + password reset
- [ ] `phone` VARCHAR(20) â€” for MFA
- [ ] `mfa_secret` VARCHAR(64) â€” TOTP secret (encrypted)
- [ ] `mfa_enabled` BOOLEAN DEFAULT FALSE
- [ ] `subscription_tier` VARCHAR(20) â€” user-visible tier (essentials/professional/enterprise)
- [ ] `stripe_customer_id` VARCHAR(100) â€” Stripe customer reference
- [ ] `password_changed_at` TIMESTAMPTZ â€” for forced rotation policy
- [ ] `failed_login_attempts` INTEGER DEFAULT 0 â€” lockout after 5
- [ ] `locked_until` TIMESTAMPTZ â€” account lockout expiry

**New indexes:**
- [ ] `idx_user_practice` ON `users(practice_id)`
- [ ] `idx_user_email` ON `users(email)` UNIQUE
- [ ] `idx_user_stripe` ON `users(stripe_customer_id)`

### 6.2.2 `Practice` Model â€” NEW (Multi-Tenancy Root)

**New table: `practices`**
- [ ] `id` SERIAL PRIMARY KEY
- [ ] `name` VARCHAR(255) NOT NULL â€” practice display name
- [ ] `slug` VARCHAR(100) UNIQUE NOT NULL â€” URL-safe identifier
- [ ] `npi` VARCHAR(10) â€” practice NPI number
- [ ] `tax_id` VARCHAR(20) â€” practice TIN/EIN
- [ ] `address_line1` VARCHAR(255)
- [ ] `address_line2` VARCHAR(255)
- [ ] `city` VARCHAR(100)
- [ ] `state` VARCHAR(2)
- [ ] `zip_code` VARCHAR(10)
- [ ] `phone` VARCHAR(20)
- [ ] `fax` VARCHAR(20)
- [ ] `email` VARCHAR(255) â€” practice contact email
- [ ] `website` VARCHAR(255)
- [ ] `timezone` VARCHAR(50) DEFAULT 'America/New_York'
- [ ] `subscription_tier` VARCHAR(20) NOT NULL DEFAULT 'essentials'
- [ ] `subscription_status` VARCHAR(20) NOT NULL DEFAULT 'trial' â€” trial/active/past_due/canceled
- [ ] `stripe_subscription_id` VARCHAR(100)
- [ ] `trial_ends_at` TIMESTAMPTZ
- [ ] `max_providers` INTEGER DEFAULT 5
- [ ] `is_active` BOOLEAN NOT NULL DEFAULT TRUE
- [ ] `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
- [ ] `updated_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
- [ ] `settings` JSONB DEFAULT '{}'::jsonb â€” practice-level config overrides
- [ ] `fhir_base_url` VARCHAR(500) â€” EHR FHIR endpoint
- [ ] `fhir_client_id` VARCHAR(255) â€” OAuth2 client ID (encrypted reference)
- [ ] `fhir_client_secret_ref` VARCHAR(255) â€” Secrets Manager ARN
- [ ] `fhir_auth_type` VARCHAR(20) DEFAULT 'smart_on_fhir' â€” smart_on_fhir/basic/bearer
- [ ] `ehr_type` VARCHAR(50) â€” amazing_charts/epic/cerner/athena/allscripts/generic_fhir
- [ ] `feature_flags` JSONB DEFAULT '{}'::jsonb â€” per-practice feature toggles
- [ ] `billing_categories_enabled` JSONB DEFAULT '[]'::jsonb â€” which billing detectors active
- [ ] `collection_rates` JSONB DEFAULT '{}'::jsonb â€” payer-specific collection rates override
- [ ] `inbox_check_interval_minutes` INTEGER DEFAULT 120
- [ ] `critical_value_keywords` JSONB DEFAULT '["critical","panic","STAT"]'::jsonb

**Indexes:**
- [ ] `idx_practice_slug` ON `practices(slug)` UNIQUE
- [ ] `idx_practice_npi` ON `practices(npi)` UNIQUE WHERE npi IS NOT NULL
- [ ] `idx_practice_stripe` ON `practices(stripe_subscription_id)`

### 6.2.3 `UserPractice` Model â€” NEW (Multi-Practice Junction)

**New table: `user_practices`**
- [ ] `id` SERIAL PRIMARY KEY
- [ ] `user_id` INTEGER FK â†’ `users.id` ON DELETE CASCADE
- [ ] `practice_id` INTEGER FK â†’ `practices.id` ON DELETE CASCADE
- [ ] `role` VARCHAR(20) NOT NULL â€” role at this specific practice
- [ ] `is_primary` BOOLEAN DEFAULT FALSE â€” primary practice for this user
- [ ] `joined_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
- [ ] UNIQUE constraint: `(user_id, practice_id)`

### 6.2.4 `PatientRecord` â€” Patient Metadata

**Current columns + migration:**
- [ ] `id` â†’ `SERIAL PRIMARY KEY`
- [ ] `mrn_hash` TEXT â†’ `VARCHAR(64) NOT NULL` â€” SHA-256 of MRN
- [ ] `user_id` INTEGER FK â†’ Keep
- [ ] `patient_name` TEXT â†’ `VARCHAR(255)` â€” encrypted at rest
- [ ] `date_of_birth` TEXT â†’ `DATE`
- [ ] `sex` TEXT â†’ `VARCHAR(10)`
- [ ] `last_parsed_at` TEXT â†’ `TIMESTAMPTZ`
- [ ] `claimed_by` INTEGER â†’ Keep
- [ ] `claimed_at` TEXT â†’ `TIMESTAMPTZ`

**New columns:**
- [ ] `practice_id` INTEGER FK â†’ `practices.id` NOT NULL
- [ ] `fhir_patient_id` VARCHAR(255) â€” FHIR server Patient resource ID
- [ ] `fhir_last_synced` TIMESTAMPTZ â€” last FHIR sync timestamp
- [ ] `age` INTEGER â€” computed from DOB, cached for query performance
- [ ] `insurer_type` VARCHAR(50) â€” cached payer type for quick routing

**Indexes:**
- [ ] `idx_patient_practice_mrn` ON `patient_records(practice_id, mrn_hash)` UNIQUE
- [ ] `idx_patient_fhir` ON `patient_records(fhir_patient_id)` WHERE fhir_patient_id IS NOT NULL
- [ ] `idx_patient_practice` ON `patient_records(practice_id)`

### 6.2.5 `PatientVitals` â€” Vital Signs

**Current columns + migration:**
- [ ] `id` â†’ `SERIAL PRIMARY KEY`
- [ ] `mrn_hash` TEXT â†’ `VARCHAR(64) NOT NULL`
- [ ] `user_id` INTEGER FK
- [ ] `recorded_at` TEXT â†’ `TIMESTAMPTZ NOT NULL`
- [ ] `systolic` REAL â†’ `NUMERIC(5,1)`
- [ ] `diastolic` REAL â†’ `NUMERIC(5,1)`
- [ ] `heart_rate` REAL â†’ `NUMERIC(5,1)`
- [ ] `respiratory_rate` REAL â†’ `NUMERIC(5,1)`
- [ ] `temperature` REAL â†’ `NUMERIC(5,2)`
- [ ] `oxygen_saturation` REAL â†’ `NUMERIC(5,2)`
- [ ] `weight` REAL â†’ `NUMERIC(6,2)` â€” in kg
- [ ] `height` REAL â†’ `NUMERIC(5,2)` â€” in cm
- [ ] `bmi` REAL â†’ `NUMERIC(5,2)` â€” computed

**New columns:**
- [ ] `practice_id` INTEGER FK â†’ `practices.id` NOT NULL
- [ ] `fhir_observation_ids` JSONB â€” array of FHIR Observation resource IDs

**Indexes:**
- [ ] `idx_vitals_practice_mrn` ON `patient_vitals(practice_id, mrn_hash)`
- [ ] `idx_vitals_recorded` ON `patient_vitals(recorded_at DESC)`

### 6.2.6 `PatientMedication` â€” Medication Records

**Current columns + migration:**
- [ ] `id` â†’ `SERIAL PRIMARY KEY`
- [ ] `mrn_hash` TEXT â†’ `VARCHAR(64) NOT NULL`
- [ ] `user_id` INTEGER FK
- [ ] `drug_name` TEXT â†’ `VARCHAR(500) NOT NULL`
- [ ] `rxnorm_cui` TEXT â†’ `VARCHAR(20)` â€” RxNorm Concept Unique Identifier
- [ ] `dosage` TEXT â†’ `VARCHAR(255)`
- [ ] `frequency` TEXT â†’ `VARCHAR(255)`
- [ ] `route` TEXT â†’ `VARCHAR(100)`
- [ ] `status` TEXT â†’ `VARCHAR(20) DEFAULT 'active'`
- [ ] `start_date` TEXT â†’ `DATE`
- [ ] `end_date` TEXT â†’ `DATE`
- [ ] `prescriber` TEXT â†’ `VARCHAR(255)`

**New columns:**
- [ ] `practice_id` INTEGER FK â†’ `practices.id` NOT NULL
- [ ] `fhir_medication_id` VARCHAR(255) â€” FHIR MedicationStatement resource ID

**Indexes:**
- [ ] `idx_med_practice_mrn` ON `patient_medications(practice_id, mrn_hash)`
- [ ] `idx_med_status` ON `patient_medications(status)` WHERE status = 'active'
- [ ] `idx_med_rxnorm` ON `patient_medications(rxnorm_cui)` WHERE rxnorm_cui IS NOT NULL

### 6.2.7 `PatientDiagnosis` â€” ICD-10 Diagnoses

**Current columns + migration:**
- [ ] `id` â†’ `SERIAL PRIMARY KEY`
- [ ] `mrn_hash` TEXT â†’ `VARCHAR(64) NOT NULL`
- [ ] `user_id` INTEGER FK
- [ ] `icd10_code` TEXT â†’ `VARCHAR(10) NOT NULL`
- [ ] `description` TEXT â†’ `VARCHAR(500)`
- [ ] `status` TEXT â†’ `VARCHAR(20) DEFAULT 'active'` â€” active/inactive/resolved
- [ ] `category` TEXT â†’ `VARCHAR(100)` â€” clinical category
- [ ] `onset_date` TEXT â†’ `DATE`
- [ ] `resolved_date` TEXT â†’ `DATE`

**New columns:**
- [ ] `practice_id` INTEGER FK â†’ `practices.id` NOT NULL
- [ ] `fhir_condition_id` VARCHAR(255)
- [ ] `is_chronic` BOOLEAN DEFAULT FALSE â€” cached for billing engine (2+ chronic = CCM)

**Indexes:**
- [ ] `idx_dx_practice_mrn` ON `patient_diagnoses(practice_id, mrn_hash)`
- [ ] `idx_dx_icd10` ON `patient_diagnoses(icd10_code)`
- [ ] `idx_dx_chronic` ON `patient_diagnoses(is_chronic)` WHERE is_chronic = TRUE AND status = 'active'

### 6.2.8 `PatientAllergy` â€” Allergy Records

**Current columns + migration:**
- [ ] `id` â†’ `SERIAL PRIMARY KEY`
- [ ] `mrn_hash` TEXT â†’ `VARCHAR(64) NOT NULL`
- [ ] `user_id` INTEGER FK
- [ ] `allergen` TEXT â†’ `VARCHAR(500) NOT NULL`
- [ ] `reaction` TEXT â†’ `VARCHAR(500)`
- [ ] `severity` TEXT â†’ `VARCHAR(20)` â€” mild/moderate/severe

**New columns:**
- [ ] `practice_id` INTEGER FK â†’ `practices.id` NOT NULL
- [ ] `fhir_allergy_id` VARCHAR(255)

### 6.2.9 `BillingOpportunity` â€” Core Billing Model

**Current columns + migration:**
- [ ] `id` â†’ `SERIAL PRIMARY KEY`
- [ ] `mrn_hash` TEXT â†’ `VARCHAR(64) NOT NULL`
- [ ] `user_id` INTEGER FK
- [ ] `visit_date` TEXT â†’ `DATE NOT NULL`
- [ ] `opportunity_type` TEXT â†’ `VARCHAR(50) NOT NULL` â€” category (ccm, awv, etc.)
- [ ] `opportunity_code` TEXT â†’ `VARCHAR(20) NOT NULL` â€” unique dedup key
- [ ] `applicable_codes` TEXT â†’ `VARCHAR(100)` â€” comma-separated CPT codes
- [ ] `modifier` TEXT â†’ `VARCHAR(10)` â€” modifier 25, modifier 33, etc.
- [ ] `estimated_revenue` REAL â†’ `NUMERIC(10,2)` â€” gross revenue
- [ ] `expected_net_dollars` REAL â†’ `NUMERIC(10,2)` â€” after 8-factor scoring
- [ ] `opportunity_score` REAL â†’ `NUMERIC(5,3)` â€” composite score 0.0-1.0
- [ ] `urgency_score` REAL â†’ `NUMERIC(5,3)` â€” time-sensitivity score
- [ ] `implementation_priority` TEXT â†’ `VARCHAR(20)` â€” high/medium/low
- [ ] `priority` TEXT â†’ `VARCHAR(10)` â€” sorting priority
- [ ] `documentation_checklist` TEXT (JSON) â†’ `JSONB` â€” required docs for billing
- [ ] `status` TEXT â†’ `VARCHAR(20) DEFAULT 'pending'` â€” pending/reviewed/captured/dismissed
- [ ] `reviewed_at` TEXT â†’ `TIMESTAMPTZ`
- [ ] `reviewed_by` INTEGER â†’ FK users.id
- [ ] `dismissed_reason` TEXT â†’ `VARCHAR(500)`
- [ ] `bonus_impact_dollars` REAL â†’ `NUMERIC(10,2)` â€” impact on quarterly bonus
- [ ] `created_at` TEXT â†’ `TIMESTAMPTZ NOT NULL DEFAULT NOW()`

**New columns:**
- [ ] `practice_id` INTEGER FK â†’ `practices.id` NOT NULL
- [ ] `closed_loop_status` VARCHAR(20) DEFAULT 'detected' â€” detected/submitted/adjudicated/paid/denied
- [ ] `claim_id` VARCHAR(50) â€” external claim reference
- [ ] `paid_amount` NUMERIC(10,2) â€” actual paid amount (closed-loop)
- [ ] `denial_reason` VARCHAR(500) â€” if denied

**Indexes:**
- [ ] `idx_billing_practice_date` ON `billing_opportunities(practice_id, visit_date DESC)`
- [ ] `idx_billing_practice_mrn` ON `billing_opportunities(practice_id, mrn_hash)`
- [ ] `idx_billing_status` ON `billing_opportunities(status)` WHERE status = 'pending'
- [ ] `idx_billing_opportunity_code` ON `billing_opportunities(opportunity_code)`
- [ ] `idx_billing_created` ON `billing_opportunities(created_at DESC)`

### 6.2.10 `BillingRuleCache` â€” CMS Fee Schedule

**Current columns + migration:**
- [ ] `id` â†’ `SERIAL PRIMARY KEY`
- [ ] `cpt_code` TEXT â†’ `VARCHAR(10) NOT NULL`
- [ ] `description` TEXT â†’ `VARCHAR(500)`
- [ ] `rvu_work` REAL â†’ `NUMERIC(8,4)`
- [ ] `rvu_pe` REAL â†’ `NUMERIC(8,4)`
- [ ] `rvu_mp` REAL â†’ `NUMERIC(8,4)`
- [ ] `conversion_factor` REAL â†’ `NUMERIC(8,4)`
- [ ] `national_rate` REAL â†’ `NUMERIC(10,2)` â€” CMS non-facility rate
- [ ] `effective_year` INTEGER â†’ `INTEGER NOT NULL`
- [ ] `fetched_at` TEXT â†’ `TIMESTAMPTZ NOT NULL DEFAULT NOW()`

**No practice_id needed â€” shared reference data.**
- [ ] UNIQUE constraint: `(cpt_code, effective_year)`

### 6.2.11 `CareGap` â€” Patient Care Gaps

**Current columns + migration:**
- [ ] `id` â†’ `SERIAL PRIMARY KEY`
- [ ] `mrn_hash` TEXT â†’ `VARCHAR(64) NOT NULL`
- [ ] `user_id` INTEGER FK
- [ ] `gap_type` TEXT â†’ `VARCHAR(50) NOT NULL` â€” colorectal_colonoscopy, mammogram, etc.
- [ ] `gap_name` TEXT â†’ `VARCHAR(255) NOT NULL`
- [ ] `due_date` TEXT â†’ `DATE`
- [ ] `completed_date` TEXT â†’ `DATE`
- [ ] `status` TEXT â†’ `VARCHAR(20) DEFAULT 'open'` â€” open/addressed/completed/declined
- [ ] `is_addressed` BOOLEAN â†’ Keep
- [ ] `documentation_snippet` TEXT â†’ Keep
- [ ] `billing_code_suggested` TEXT â†’ `VARCHAR(20)`

**New columns:**
- [ ] `practice_id` INTEGER FK â†’ `practices.id` NOT NULL
- [ ] `fhir_service_request_id` VARCHAR(255) â€” FHIR ServiceRequest for ordered screening
- [ ] `outreach_status` VARCHAR(20) â€” none/contacted/scheduled/completed

**Indexes:**
- [ ] `idx_caregap_practice_mrn` ON `care_gaps(practice_id, mrn_hash)`
- [ ] `idx_caregap_status` ON `care_gaps(status)` WHERE status = 'open'
- [ ] `idx_caregap_due` ON `care_gaps(due_date)` WHERE status = 'open'

### 6.2.12 `CareGapRule` â€” USPSTF Rule Configuration

**Current columns + migration:**
- [ ] `id` â†’ `SERIAL PRIMARY KEY`
- [ ] `gap_type` TEXT â†’ `VARCHAR(50) NOT NULL`
- [ ] `gap_name` TEXT â†’ `VARCHAR(255) NOT NULL`
- [ ] `description` TEXT â†’ `TEXT`
- [ ] `criteria_json` TEXT â†’ `JSONB NOT NULL` â€” age range, sex, risk factors
- [ ] `interval_days` INTEGER â†’ Keep
- [ ] `billing_code_pair` TEXT â†’ `VARCHAR(50)`
- [ ] `documentation_template` TEXT â†’ `TEXT`
- [ ] `source` TEXT â†’ `VARCHAR(20) DEFAULT 'hardcoded'` â€” hardcoded/api/custom
- [ ] `is_active` BOOLEAN â†’ `BOOLEAN DEFAULT TRUE`

**New columns:**
- [ ] `practice_id` INTEGER FK â†’ `practices.id` â€” NULL = system default, non-NULL = practice override
- [ ] `created_by` INTEGER FK â†’ `users.id`

**Indexes:**
- [ ] `idx_caregaprule_practice` ON `care_gap_rules(practice_id)` WHERE practice_id IS NOT NULL
- [ ] `idx_caregaprule_type` ON `care_gap_rules(gap_type)`

### 6.2.13 `CCMEnrollment` â€” Chronic Care Management

**Current columns + migration:**
- [ ] `id` â†’ `SERIAL PRIMARY KEY`
- [ ] `mrn_hash` TEXT â†’ `VARCHAR(64) NOT NULL`
- [ ] `user_id` INTEGER FK
- [ ] `consent_date` TEXT â†’ `DATE NOT NULL`
- [ ] `care_plan_date` TEXT â†’ `DATE`
- [ ] `qualifying_conditions` TEXT (JSON) â†’ `JSONB NOT NULL`
- [ ] `status` TEXT â†’ `VARCHAR(20) DEFAULT 'active'` â€” active/paused/disenrolled
- [ ] `monthly_time_goal` INTEGER â†’ `INTEGER DEFAULT 20` â€” minutes

**New columns:**
- [ ] `practice_id` INTEGER FK â†’ `practices.id` NOT NULL
- [ ] `disenrolled_date` DATE
- [ ] `disenroll_reason` VARCHAR(255)

### 6.2.14 `CCMTimeEntry` â€” CCM Time Logging

**Current columns + migration:**
- [ ] `id` â†’ `SERIAL PRIMARY KEY`
- [ ] `enrollment_id` INTEGER FK â†’ `ccm_enrollments.id`
- [ ] `user_id` INTEGER FK
- [ ] `date` TEXT â†’ `DATE NOT NULL`
- [ ] `minutes` INTEGER NOT NULL
- [ ] `activity_type` TEXT â†’ `VARCHAR(50)` â€” phone_call, care_coordination, medication_review, etc.
- [ ] `notes` TEXT
- [ ] `is_billable` BOOLEAN DEFAULT TRUE

**New columns:**
- [ ] `practice_id` INTEGER FK â†’ `practices.id` NOT NULL

### 6.2.15 `Schedule` â€” Appointments

**Current columns + migration:**
- [ ] `id` â†’ `SERIAL PRIMARY KEY`
- [ ] `appointment_date` TEXT â†’ `DATE NOT NULL`
- [ ] `appointment_time` TEXT â†’ `TIME NOT NULL`
- [ ] `patient_mrn` TEXT â†’ `VARCHAR(20)` â€” encrypted
- [ ] `patient_name` TEXT â†’ `VARCHAR(255)` â€” encrypted
- [ ] `visit_type` TEXT â†’ `VARCHAR(100)`
- [ ] `duration_minutes` INTEGER
- [ ] `patient_age` INTEGER
- [ ] `insurer_type` TEXT â†’ `VARCHAR(50)`
- [ ] `user_id` INTEGER FK

**New columns:**
- [ ] `practice_id` INTEGER FK â†’ `practices.id` NOT NULL
- [ ] `fhir_appointment_id` VARCHAR(255)
- [ ] `status` VARCHAR(20) DEFAULT 'scheduled' â€” scheduled/checked_in/completed/no_show/canceled

**Indexes:**
- [ ] `idx_schedule_practice_date` ON `schedules(practice_id, appointment_date)`
- [ ] `idx_schedule_user_date` ON `schedules(user_id, appointment_date)`

### 6.2.16-6.2.24 Remaining Models (pattern: add practice_id + PostgreSQL types)

**TimeLog:**
- [ ] Add `practice_id` FK; `duration_seconds` INTEGER; `visit_type` VARCHAR(100)

**OnCallNote:**
- [ ] Add `practice_id` FK; `mrn_hash` VARCHAR(64); convert TEXT dates to TIMESTAMPTZ

**LabTrack:**
- [ ] Add `practice_id` FK; `test_code` VARCHAR(20); `result_value` VARCHAR(100); FHIR DiagnosticReport ID

**InboxMessage:**
- [ ] Add `practice_id` FK; `message_type` VARCHAR(50); convert dates to TIMESTAMPTZ

**CalculatorResult:**
- [ ] Add `practice_id` FK; `calculator_type` VARCHAR(50); `data_source` VARCHAR(50)

**BonusTracker:**
- [ ] Add `practice_id` FK; `quarterly_threshold` NUMERIC(10,2); `monthly_receipts` JSONB

**ImmunizationSeries:**
- [ ] Add `practice_id` FK; `vaccine_cpt` VARCHAR(10); `dose_number`/`total_doses` INTEGER

**PracticeBookmark:**
- [ ] Add `practice_id` FK; `url` VARCHAR(1000); `sort_order` INTEGER

**AuditLog:**
- [ ] Add `practice_id` FK; `ip_address` INET (PostgreSQL native type); `timestamp` TIMESTAMPTZ

**RxClassCache / FdaLabelCache / FaersCache:**
- [ ] No `practice_id` needed â€” shared reference data
- [ ] Convert TEXT dates to TIMESTAMPTZ
- [ ] Add TTL index for cache expiry

## 6.3 Data Migration ETL Script

### 6.3.1 Migration Script Structure
```python
# scripts/migrate_sqlite_to_postgres.py
"""
ETL: SQLite â†’ PostgreSQL migration
Usage: python scripts/migrate_sqlite_to_postgres.py --source data/carecompanion.db --target $DATABASE_URL
"""
```

- [ ] Read all SQLite tables with `sqlite3` module
- [ ] Transform dates: TEXT â†’ datetime objects
- [ ] Transform JSON: TEXT â†’ dict (for JSONB columns)
- [ ] Transform booleans: 0/1 â†’ True/False
- [ ] Insert into PostgreSQL with `psycopg2` / SQLAlchemy bulk_insert_mappings
- [ ] Assign default `practice_id = 1` for existing data (single practice migration)
- [ ] Verify row counts match: `SELECT COUNT(*) FROM table` on both sides
- [ ] Verify checksums on critical columns (mrn_hash, icd10_code, cpt_code)

### 6.3.2 Migration Order (respecting foreign keys)
1. [ ] `practices` â€” create initial practice record
2. [ ] `users` â€” with `practice_id` = 1
3. [ ] `patient_records` â€” with `practice_id` = 1
4. [ ] `patient_vitals` â€” FK to patient_records
5. [ ] `patient_medications` â€” FK to patient_records
6. [ ] `patient_diagnoses` â€” FK to patient_records
7. [ ] `patient_allergies` â€” FK to patient_records
8. [ ] `billing_opportunities` â€” FK to users
9. [ ] `billing_rule_cache` â€” no FK
10. [ ] `care_gaps` â€” FK to patient_records
11. [ ] `care_gap_rules` â€” optional FK to practices
12. [ ] `ccm_enrollments` â€” FK to users
13. [ ] `ccm_time_entries` â€” FK to ccm_enrollments
14. [ ] `schedules` â€” FK to users
15. [ ] `time_logs` â€” FK to users
16. [ ] `on_call_notes` â€” FK to users
17. [ ] `lab_tracks` â€” FK to users
18. [ ] `inbox_messages` â€” FK to users
19. [ ] `calculator_results` â€” FK to users
20. [ ] `bonus_trackers` â€” FK to users
21. [ ] `immunization_series` â€” FK to patient_records
22. [ ] `practice_bookmarks` â€” FK to practices
23. [ ] `audit_logs` â€” FK to users
24. [ ] `rx_class_cache` â€” no FK
25. [ ] `fda_label_cache` â€” no FK
26. [ ] `faers_cache` â€” no FK

## 6.4 PostgreSQL-Specific Optimizations

### 6.4.1 Indexes for Common Queries
- [ ] Composite index for billing dashboard: `(practice_id, visit_date DESC, status)` on billing_opportunities
- [ ] Composite index for care gap panel: `(practice_id, status, due_date)` on care_gaps
- [ ] Partial index for active patients: `(practice_id)` on patient_records WHERE last_parsed_at > NOW() - INTERVAL '1 year'
- [ ] GIN index for JSONB searches: `documentation_checklist` on billing_opportunities
- [ ] GIN index for JSONB searches: `preferences` on users

### 6.4.2 Row-Level Security (Optional â€” Defense in Depth)
```sql
-- Enable RLS on billing_opportunities
ALTER TABLE billing_opportunities ENABLE ROW LEVEL SECURITY;

-- Policy: users can only see their practice's data
CREATE POLICY practice_isolation ON billing_opportunities
  USING (practice_id = current_setting('app.current_practice_id')::int);
```
- [ ] Evaluate RLS for critical tables: billing_opportunities, care_gaps, patient_records
- [ ] Set `app.current_practice_id` in SQLAlchemy session events
- [ ] RLS as defense-in-depth only â€” primary isolation via application-level WHERE clauses

### 6.4.3 Connection Pooling
- [ ] PgBouncer sidecar container in ECS task definition
- [ ] Transaction mode pooling (recommended for web apps)
- [ ] Pool size: 50 connections per PgBouncer instance
- [ ] SQLAlchemy pool_size = 20 per web container â†’ PgBouncer â†’ RDS

---

# 7. FHIR R4 Integration Layer

> Complete specification for replacing screen-scraping and CDA XML parsing with
> FHIR R4 API integration. Every resource mapping, endpoint, and adapter method
> has a checkbox.

## 7.1 FHIR Integration Strategy

### 7.1.1 Approach: Adapter Pattern
```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Billing Engine      â”‚
â”‚  Care Gap Engine     â”‚  â† Uses internal patient_data dict (unchanged)
â”‚  Clinical Workflows  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚ patient_data dict
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  FHIR Adapter Layer  â”‚  â† NEW: translates FHIR â†” internal format
â”‚  (fhir/adapter.py)   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚ FHIR R4 REST API
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  EHR FHIR Server     â”‚  â† Epic, Cerner, Athena, AC, etc.
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

- [ ] Create `fhir/` package in project root
- [ ] `fhir/__init__.py` â€” package initialization
- [ ] `fhir/client.py` â€” FHIR REST client with OAuth2 token management
- [ ] `fhir/adapter.py` â€” Resource â†’ internal dict translation
- [ ] `fhir/resources.py` â€” FHIR resource dataclass definitions
- [ ] `fhir/auth.py` â€” SMART on FHIR OAuth2 flow
- [ ] `fhir/sync.py` â€” Periodic sync engine (Celery tasks)
- [ ] `fhir/webhooks.py` â€” FHIR Subscription webhook handlers
- [ ] `fhir/mapper.py` â€” Code system mapping (ICD-10, CPT, LOINC, SNOMED)

### 7.1.2 FHIR Client Specification (`fhir/client.py`)

```python
class FHIRClient:
    """Thread-safe FHIR R4 REST client with automatic token refresh."""

    def __init__(self, base_url: str, client_id: str, client_secret: str,
                 auth_type: str = 'smart_on_fhir'):
        self.base_url = base_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_type = auth_type
        self._token = None
        self._token_expires_at = None
        self._session = requests.Session()

    def get(self, resource_type: str, resource_id: str = None,
            params: dict = None) -> dict: ...
    def search(self, resource_type: str, params: dict = None) -> list[dict]: ...
    def create(self, resource_type: str, resource: dict) -> dict: ...
    def update(self, resource_type: str, resource_id: str, resource: dict) -> dict: ...
```

- [ ] Implement `FHIRClient.__init__()` with base_url, credentials, session
- [ ] Implement `FHIRClient._authenticate()` â€” OAuth2 client_credentials flow
- [ ] Implement `FHIRClient._refresh_token()` â€” auto-refresh before expiry (5min buffer)
- [ ] Implement `FHIRClient.get(resource_type, id)` â€” GET /Patient/123
- [ ] Implement `FHIRClient.search(resource_type, params)` â€” GET /Patient?name=Smith
- [ ] Implement `FHIRClient._handle_pagination(bundle)` â€” follow Bundle.link[rel=next]
- [ ] Implement `FHIRClient.create(resource_type, resource)` â€” POST /Observation
- [ ] Implement `FHIRClient.update(resource_type, id, resource)` â€” PUT /Observation/456
- [ ] Implement rate limiting: max 100 requests/minute per practice (configurable)
- [ ] Implement retry with exponential backoff: 429 Too Many Requests, 503 Service Unavailable
- [ ] Implement request timeout: 30s connect, 60s read
- [ ] Implement response validation: check `resourceType` matches expected
- [ ] Implement error handling: OperationOutcome parsing for FHIR error responses
- [ ] Add request/response logging for audit trail (sanitize PHI from logs)

### 7.1.3 SMART on FHIR OAuth2 (`fhir/auth.py`)

- [ ] Implement `get_authorization_url(practice)` â€” redirect to EHR authorize endpoint
- [ ] Implement `exchange_code_for_token(code, practice)` â€” POST to token endpoint
- [ ] Implement `refresh_access_token(practice)` â€” refresh expired tokens
- [ ] Store tokens encrypted in `PracticeFHIRToken` model (not in plaintext)
- [ ] Token rotation: refresh 5 minutes before expiry
- [ ] Scopes requested: `patient/*.read`, `user/*.read`, `launch/patient` (minimum)
- [ ] Support both backend (system) and EHR launch (user-facing) flows

### 7.1.4 FHIR Adapter â€” Resource Mapping (`fhir/adapter.py`)

**Master class: `FHIRAdapter`**
```python
class FHIRAdapter:
    """Translates FHIR resources to CareCompanion internal patient_data dict."""

    def __init__(self, client: FHIRClient):
        self.client = client

    def get_patient_data(self, patient_fhir_id: str) -> dict:
        """Fetch all needed FHIR resources and return patient_data dict
        compatible with BillingCaptureEngine.evaluate()."""
        ...
```

- [ ] `get_patient_data(patient_fhir_id)` â€” orchestrator that calls all sub-fetchers
- [ ] Returns dict with keys: `mrn`, `age`, `sex`, `dob`, `diagnoses`, `medications`, `allergies`, `vitals`, `lab_results`, `immunizations`, `encounters`, `social_history`, `insurer_type`, `user_id`, `visit_date`, `billing_categories_enabled`

## 7.2 FHIR Resource â†’ Internal Field Mapping

### 7.2.1 Patient Resource â†’ Demographics

**FHIR `Patient` fields used:**
- [ ] `Patient.identifier[system=MRN].value` â†’ `patient_data['mrn']`
- [ ] `Patient.birthDate` â†’ `patient_data['dob']` â†’ compute `patient_data['age']`
- [ ] `Patient.gender` â†’ `patient_data['sex']` (FHIR: male/female/other/unknown)
- [ ] `Patient.name[0].given[0]` + `Patient.name[0].family` â†’ `patient_data['patient_name']`
- [ ] `Patient.address[0]` â†’ practice address for geo-based rules

**Adapter method:**
```python
def _fetch_patient(self, patient_id: str) -> dict:
    resource = self.client.get('Patient', patient_id)
    return {
        'mrn': self._extract_mrn(resource),
        'dob': resource.get('birthDate'),
        'age': self._calculate_age(resource.get('birthDate')),
        'sex': resource.get('gender', 'unknown'),
        'patient_name': self._format_name(resource.get('name', [{}])[0]),
    }
```

### 7.2.2 Condition Resource â†’ Diagnoses

**FHIR `Condition` fields used:**
- [ ] `Condition.code.coding[system=ICD10].code` â†’ `diagnosis['icd10_code']`
- [ ] `Condition.code.text` â†’ `diagnosis['description']`
- [ ] `Condition.clinicalStatus.coding[0].code` â†’ `diagnosis['status']` (active/inactive/resolved)
- [ ] `Condition.category[0].coding[0].code` â†’ `diagnosis['category']` (encounter-diagnosis/problem-list-item)
- [ ] `Condition.onsetDateTime` â†’ `diagnosis['onset_date']`
- [ ] `Condition.abatementDateTime` â†’ `diagnosis['resolved_date']`

**FHIR search query:**
```
GET /Condition?patient={id}&clinical-status=active&_count=100
```

- [ ] Implement `_fetch_diagnoses(patient_id)` â†’ list of diagnosis dicts
- [ ] Map ICD-10 system URI: `http://hl7.org/fhir/sid/icd-10-cm`
- [ ] Handle multiple codings per Condition (ICD-10 + SNOMED)
- [ ] Filter by `clinicalStatus`: active, recurrence, relapse (not resolved/inactive)
- [ ] Handle `Condition.category`: separate problem-list from encounter-diagnosis
- [ ] Deduplicate by ICD-10 code (keep most recent)

### 7.2.3 MedicationStatement / MedicationRequest â†’ Medications

**FHIR fields used:**
- [ ] `MedicationStatement.medicationCodeableConcept.coding[system=RxNorm].code` â†’ `medication['rxnorm_cui']`
- [ ] `MedicationStatement.medicationCodeableConcept.text` â†’ `medication['drug_name']`
- [ ] `MedicationStatement.dosage[0].text` â†’ `medication['dosage']`
- [ ] `MedicationStatement.status` â†’ `medication['status']` (active/completed/stopped)
- [ ] `MedicationStatement.effectivePeriod.start` â†’ `medication['start_date']`

**FHIR search:**
```
GET /MedicationStatement?patient={id}&status=active&_count=200
```
OR (if MedicationStatement not supported):
```
GET /MedicationRequest?patient={id}&status=active&_count=200
```

- [ ] Implement `_fetch_medications(patient_id)` â†’ list of medication dicts
- [ ] Map RxNorm system URI: `http://www.nlm.nih.gov/research/umls/rxnorm`
- [ ] Try MedicationStatement first, fall back to MedicationRequest
- [ ] Handle `medicationReference` (Reference to Medication resource) vs `medicationCodeableConcept`
- [ ] Extract dosage from `dosage[0].doseAndRate[0].doseQuantity`

### 7.2.4 AllergyIntolerance â†’ Allergies

**FHIR fields used:**
- [ ] `AllergyIntolerance.code.text` â†’ `allergy['allergen']`
- [ ] `AllergyIntolerance.reaction[0].manifestation[0].text` â†’ `allergy['reaction']`
- [ ] `AllergyIntolerance.criticality` â†’ `allergy['severity']` (low/high/unable-to-assess)

**FHIR search:**
```
GET /AllergyIntolerance?patient={id}&clinical-status=active
```

- [ ] Implement `_fetch_allergies(patient_id)` â†’ list of allergy dicts

### 7.2.5 Observation (vital-signs) â†’ Vitals

**FHIR Observation mapping by LOINC code:**
- [ ] `85354-9` (Blood pressure panel) â†’ `systolic`, `diastolic` from `component`
- [ ] `8867-4` (Heart rate) â†’ `heart_rate`
- [ ] `9279-1` (Respiratory rate) â†’ `respiratory_rate`
- [ ] `8310-5` (Body temperature) â†’ `temperature`
- [ ] `2708-6` (SpO2) â†’ `oxygen_saturation`
- [ ] `29463-7` (Body weight) â†’ `weight`
- [ ] `8302-2` (Body height) â†’ `height`
- [ ] `39156-5` (BMI) â†’ `bmi`

**FHIR search:**
```
GET /Observation?patient={id}&category=vital-signs&_sort=-date&_count=20
```

- [ ] Implement `_fetch_vitals(patient_id)` â†’ most recent vital signs dict
- [ ] Handle blood pressure `component` array (systolic/diastolic as sub-observations)
- [ ] Convert units if needed (lbsâ†’kg, inchesâ†’cm) using `valueQuantity.unit`

### 7.2.6 Observation (laboratory) â†’ Lab Results

**FHIR search:**
```
GET /Observation?patient={id}&category=laboratory&_sort=-date&_count=50
```

**Key lab LOINC codes for billing engine:**
- [ ] `4548-4` (Hemoglobin A1C) â†’ diabetes monitoring / screening
- [ ] `2085-9` (HDL), `2089-1` (LDL), `2093-3` (Total cholesterol) â†’ lipid screening
- [ ] `33914-3` (eGFR) â†’ CKD staging
- [ ] `2160-0` (Creatinine) â†’ renal function
- [ ] `1742-6` (ALT), `1920-8` (AST) â†’ liver function
- [ ] `6690-2` (WBC), `718-7` (Hemoglobin) â†’ CBC
- [ ] `3016-3` (TSH) â†’ thyroid monitoring

- [ ] Implement `_fetch_lab_results(patient_id)` â†’ list of lab result dicts
- [ ] Map result values: `Observation.valueQuantity.value` + `unit`
- [ ] Map reference ranges: `Observation.referenceRange[0].low/high`
- [ ] Map status: `Observation.status` (final/preliminary/amended)

### 7.2.7 Observation (social-history) â†’ Social History

**Key LOINC codes:**
- [ ] `72166-2` (Tobacco smoking status) â†’ smoking_status for billing (tobacco cessation)
- [ ] `11331-6` (History of alcohol use) â†’ alcohol screening
- [ ] `82589-3` (Highest education level) â†’ SDOH

- [ ] Implement `_fetch_social_history(patient_id)` â†’ social history dict
- [ ] Extract smoking status for tobacco cessation detector
- [ ] Extract alcohol use for alcohol screening detector

### 7.2.8 Immunization â†’ Vaccination History

**FHIR search:**
```
GET /Immunization?patient={id}&status=completed&_count=100
```

**Fields used:**
- [ ] `Immunization.vaccineCode.coding[system=CVX].code` â†’ vaccine CVX code
- [ ] `Immunization.occurrenceDateTime` â†’ date administered
- [ ] `Immunization.status` â†’ completed/not-done/entered-in-error
- [ ] `Immunization.doseNumberPositiveInt` â†’ dose number in series

- [ ] Implement `_fetch_immunizations(patient_id)` â†’ list of immunization dicts
- [ ] Map CVX codes to care gap rule matching (flu, pneumo, shingrix, tdap, covid)

### 7.2.9 Encounter â†’ Visit History

**FHIR search:**
```
GET /Encounter?patient={id}&_sort=-date&_count=50
```

**Fields used:**
- [ ] `Encounter.type[0].coding[0].code` â†’ visit type (office-visit, wellness, etc.)
- [ ] `Encounter.period.start` / `Encounter.period.end` â†’ visit date + duration
- [ ] `Encounter.class.code` â†’ AMB (ambulatory), EMER (emergency), IMP (inpatient)
- [ ] `Encounter.hospitalization.dischargeDisposition` â†’ for TCM detection
- [ ] `Encounter.reasonCode` â†’ visit reason

- [ ] Implement `_fetch_encounters(patient_id)` â†’ list of encounter dicts
- [ ] Detect recent hospital discharge for TCM billing (within 30 days)
- [ ] Calculate encounter duration for prolonged services billing
- [ ] Detect AWV history (when was last G0402/G0438/G0439)

### 7.2.10 Coverage â†’ Insurance/Payer

**FHIR search:**
```
GET /Coverage?patient={id}&status=active
```

**Fields used:**
- [ ] `Coverage.type.coding[0].code` â†’ insurance type
- [ ] `Coverage.payor[0].display` â†’ payer name
- [ ] `Coverage.class[0].value` â†’ plan ID
- [ ] `Coverage.period.start` / `Coverage.period.end` â†’ coverage dates

- [ ] Implement `_fetch_coverage(patient_id)` â†’ payer context dict
- [ ] Map to internal payer types: `medicare_b`, `medicare_advantage`, `medicaid`, `commercial`
- [ ] Feed into `get_payer_context()` for billing engine routing

### 7.2.11 Additional FHIR Resources

**QuestionnaireResponse (for screening scores):**
- [ ] PHQ-9 (depression) â†’ `QuestionnaireResponse?questionnaire=phq-9&patient={id}`
- [ ] GAD-7 (anxiety) â†’ `QuestionnaireResponse?questionnaire=gad-7&patient={id}`
- [ ] AUDIT-C (alcohol) â†’ `QuestionnaireResponse?questionnaire=audit-c&patient={id}`
- [ ] MoCA (cognitive) â†’ cognitive screening detector

**Procedure (for care gap completion):**
- [ ] `Procedure?patient={id}&code=77067` â†’ mammogram completion
- [ ] `Procedure?patient={id}&code=G0105` â†’ colonoscopy completion
- [ ] General: `Procedure?patient={id}&_sort=-date&_count=50`

**DiagnosticReport (for lab/imaging orders):**
- [ ] `DiagnosticReport?patient={id}&category=LAB&_sort=-date`
- [ ] Contains references to Observation results

**CarePlan (for CCM):**
- [ ] `CarePlan?patient={id}&status=active&category=assess-plan`

**Communication (for inbox):**
- [ ] `Communication?recipient={practitioner_id}&status=in-progress`

## 7.3 FHIR Sync Engine (`fhir/sync.py`)

### 7.3.1 Sync Strategy
- [ ] **Initial sync:** Full patient roster + all historical data (one-time per practice onboarding)
- [ ] **Incremental sync:** Poll for changes since `_lastUpdated` (configurable interval)
- [ ] **Event-driven sync:** FHIR Subscription webhooks for real-time updates (when supported)
- [ ] **On-demand sync:** Triggered when provider opens patient chart in CareCompanion

### 7.3.2 Celery Tasks for FHIR Sync
```python
@celery.task(queue='fhir_sync', rate_limit='10/m')
def sync_patient(practice_id: int, patient_fhir_id: str):
    """Sync a single patient's FHIR data to local database."""
    ...

@celery.task(queue='fhir_sync')
def sync_practice_roster(practice_id: int):
    """Sync entire patient roster for a practice (run nightly)."""
    ...

@celery.task(queue='fhir_sync')
def sync_incremental(practice_id: int, since: datetime):
    """Sync all resources updated since timestamp."""
    ...
```

- [ ] Implement `sync_patient()` â€” fetch all resources for one patient, update local DB
- [ ] Implement `sync_practice_roster()` â€” `GET /Patient?_count=100` with pagination
- [ ] Implement `sync_incremental()` â€” `GET /Patient?_lastUpdated=gt{since}` for each resource type
- [ ] Implement conflict resolution: FHIR data wins for clinical fields, local data wins for billing status
- [ ] Implement sync status tracking: `FHIRSyncLog` model with timestamps and error counts
- [ ] Rate limit per practice: max 100 FHIR API calls/minute to avoid EHR throttling

### 7.3.3 Webhook Handler (`fhir/webhooks.py`)
- [ ] `POST /api/fhir/webhook/{practice_id}` â€” receive FHIR Subscription notifications
- [ ] Verify webhook signature (HMAC-SHA256)
- [ ] Parse notification bundle: extract changed resource type + ID
- [ ] Dispatch Celery task to sync changed resource
- [ ] Support both REST-hook and websocket channel types

---

# 8. Multi-Tenancy Architecture

> Complete specification for isolating practice data while sharing infrastructure.

## 8.1 Multi-Tenancy Strategy

### 8.1.1 Chosen Approach: Shared Schema with Row-Level Isolation
- [ ] Single PostgreSQL database instance
- [ ] All practices share the same schema (tables)
- [ ] Every tenant-scoped table has `practice_id` column (NOT NULL, FK)
- [ ] Application-level WHERE clause filtering on every query
- [ ] Optional PostgreSQL Row-Level Security as defense-in-depth

**Why shared schema (not schema-per-tenant or database-per-tenant):**
- Simpler migrations (one schema to update)
- Lower infrastructure cost at scale
- Easier cross-practice analytics (for platform admin)
- Sufficient for target market (100-200 practices initially)

### 8.1.2 Tenant Context Management

**Flask middleware: `PracticeContextMiddleware`**
```python
class PracticeContextMiddleware:
    """Sets practice context for every request based on authenticated user."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        with self.app.request_context(environ):
            if current_user.is_authenticated:
                g.practice_id = current_user.practice_id
                g.practice = Practice.query.get(current_user.practice_id)
            return self.app(environ, start_response)
```

- [ ] Implement `PracticeContextMiddleware` â€” sets `g.practice_id` on every request
- [ ] Implement `get_current_practice_id()` helper â†’ returns `g.practice_id` or raises 403
- [ ] Add `practice_id` to all SQLAlchemy queries via query filter mixin
- [ ] Add `@require_practice` decorator for practice-scoped routes

### 8.1.3 SQLAlchemy Query Mixin for Auto-Filtering

```python
class PracticeScopedQuery(BaseQuery):
    """Automatically filters by practice_id on all queries."""

    def filter_by_practice(self):
        from flask import g
        practice_id = getattr(g, 'practice_id', None)
        if practice_id:
            return self.filter_by(practice_id=practice_id)
        return self
```

- [ ] Create `PracticeScopedMixin` base class with `practice_id` column
- [ ] Override `query_class` for all tenant-scoped models
- [ ] Ensure admin/platform queries can bypass practice filter (explicit `unscoped()` method)
- [ ] Add unit tests: verify cross-practice data leakage is impossible via ORM
- [ ] Add integration test: verify raw SQL queries also respect practice isolation

### 8.1.4 Tables Requiring `practice_id` (Tenant-Scoped)
- [ ] `users` â€” with `practice_id` FK + `user_practices` junction
- [ ] `patient_records` â€” `practice_id` NOT NULL
- [ ] `patient_vitals` â€” `practice_id` NOT NULL
- [ ] `patient_medications` â€” `practice_id` NOT NULL
- [ ] `patient_diagnoses` â€” `practice_id` NOT NULL
- [ ] `patient_allergies` â€” `practice_id` NOT NULL
- [ ] `billing_opportunities` â€” `practice_id` NOT NULL
- [ ] `care_gaps` â€” `practice_id` NOT NULL
- [ ] `care_gap_rules` â€” `practice_id` NULL (NULL = system default)
- [ ] `ccm_enrollments` â€” `practice_id` NOT NULL
- [ ] `ccm_time_entries` â€” `practice_id` NOT NULL
- [ ] `schedules` â€” `practice_id` NOT NULL
- [ ] `time_logs` â€” `practice_id` NOT NULL
- [ ] `on_call_notes` â€” `practice_id` NOT NULL
- [ ] `lab_tracks` â€” `practice_id` NOT NULL
- [ ] `inbox_messages` â€” `practice_id` NOT NULL
- [ ] `calculator_results` â€” `practice_id` NOT NULL
- [ ] `bonus_trackers` â€” `practice_id` NOT NULL
- [ ] `immunization_series` â€” `practice_id` NOT NULL
- [ ] `practice_bookmarks` â€” `practice_id` NOT NULL
- [ ] `audit_logs` â€” `practice_id` NOT NULL

### 8.1.5 Tables NOT Requiring `practice_id` (Shared/Platform)
- [ ] `practices` â€” IS the tenant table itself
- [ ] `billing_rule_cache` â€” CMS rates, shared across all practices
- [ ] `rx_class_cache` â€” Drug classification, shared
- [ ] `fda_label_cache` â€” FDA labels, shared
- [ ] `faers_cache` â€” Adverse events, shared

## 8.2 Practice Onboarding Workflow

### 8.2.1 Self-Service Signup Flow
1. [ ] User visits `/signup` â†’ enters name, email, practice name, NPI
2. [ ] System creates `Practice` record with `subscription_status = 'trial'`
3. [ ] System creates `User` record with `role = 'practice_admin'`
4. [ ] System creates `UserPractice` record linking user to practice
5. [ ] System seeds default `CareGapRule` records (20 USPSTF rules, `practice_id = NULL` shared)
6. [ ] System sends welcome email via SendGrid
7. [ ] Redirect to `/setup` wizard for FHIR configuration

### 8.2.2 FHIR Setup Wizard (`/setup/fhir`)
1. [ ] Select EHR type dropdown: Epic, Cerner, Athena, Amazing Charts, AllScripts, Generic FHIR
2. [ ] Enter FHIR base URL (auto-detect from EHR type if possible)
3. [ ] Enter OAuth2 client credentials (or generate via EHR app registration)
4. [ ] Test connection: `GET /metadata` (FHIR CapabilityStatement)
5. [ ] Verify required resources supported: Patient, Condition, Observation, MedicationStatement
6. [ ] Initial patient roster sync (background Celery task)
7. [ ] Show sync progress bar
8. [ ] Complete: redirect to dashboard

### 8.2.3 Practice Settings Configuration (`/admin/practice`)
- [ ] Practice name, NPI, address, phone, fax
- [ ] Timezone selection (for scheduled job timing)
- [ ] Billing detector toggles (enable/disable each of 25+ detectors)
- [ ] Collection rate overrides by payer type
- [ ] Inbox check interval
- [ ] Critical value keywords
- [ ] Custom care gap rules (add/edit/disable)
- [ ] Provider management (invite/remove/change role)
- [ ] FHIR connection settings (re-authorize, test connection)

## 8.3 Subscription Management (Stripe Integration)

### 8.3.1 Stripe Setup
- [ ] Create Stripe products: Essentials, Professional, Enterprise
- [ ] Create Stripe prices: monthly + annual for each tier
- [ ] Implement `POST /api/billing/create-checkout-session` â†’ Stripe Checkout
- [ ] Implement `POST /api/billing/create-portal-session` â†’ Stripe Customer Portal
- [ ] Implement Stripe webhook handler: `POST /api/stripe/webhook`

### 8.3.2 Stripe Webhook Events
- [ ] `checkout.session.completed` â†’ Activate practice subscription; set `subscription_status = 'active'`
- [ ] `invoice.paid` â†’ Update `subscription_status = 'active'`; reset `past_due` flag
- [ ] `invoice.payment_failed` â†’ Set `subscription_status = 'past_due'`; email admin
- [ ] `customer.subscription.updated` â†’ Handle plan changes (upgrade/downgrade); update `subscription_tier`
- [ ] `customer.subscription.deleted` â†’ Set `subscription_status = 'canceled'`; start grace period (30 days)

### 8.3.3 Feature Gating by Subscription Tier

```python
TIER_FEATURES = {
    'essentials': {
        'max_detectors': 15,
        'care_gap_rules': 20,
        'stack_builder': False,
        'specificity': False,
        'ccm_billing': False,
        'api_access': False,
        'ai_assistant': False,
        'custom_rules': False,
    },
    'professional': {
        'max_detectors': 999,  # all
        'care_gap_rules': 999,
        'stack_builder': True,
        'specificity': True,
        'ccm_billing': True,
        'api_access': False,
        'ai_assistant': False,
        'custom_rules': False,
    },
    'enterprise': {
        'max_detectors': 999,
        'care_gap_rules': 999,
        'stack_builder': True,
        'specificity': True,
        'ccm_billing': True,
        'api_access': True,
        'ai_assistant': True,
        'custom_rules': True,
    },
}
```

- [ ] Implement `@require_tier(minimum_tier)` decorator for routes
- [ ] Implement `practice_has_feature(feature_name)` helper
- [ ] Gate billing detector count by tier in `BillingCaptureEngine.evaluate()`
- [ ] Gate stack builder access by tier
- [ ] Gate API access by tier (Enterprise only)
- [ ] Gate AI assistant by tier + add-on purchase

## 8.4 Data Isolation Testing

### 8.4.1 Test Scenarios
- [ ] Practice A user cannot see Practice B patient records
- [ ] Practice A user cannot see Practice B billing opportunities
- [ ] Practice A user cannot modify Practice B care gap rules
- [ ] Platform admin CAN see all practice data (with explicit scope override)
- [ ] User with access to two practices can switch context correctly
- [ ] Bulk operations (billing evaluation) respect practice scope
- [ ] API endpoints return 403 for cross-practice access attempts
- [ ] Celery tasks process only the target practice's data
- [ ] Stripe webhook updates only the correct practice
- [ ] Deleted practice data is properly soft-deleted (not visible but recoverable)



## 8.5 PostgreSQL Row-Level Security (Defense-in-Depth)

### 8.5.1 RLS Policy Definitions
```sql
-- Enable RLS on all tenant-scoped tables
ALTER TABLE patient_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE care_gaps ENABLE ROW LEVEL SECURITY;
ALTER TABLE ccm_enrollments ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_vitals ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_medications ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_diagnoses ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_allergies ENABLE ROW LEVEL SECURITY;
ALTER TABLE schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE time_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE on_call_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE lab_tracks ENABLE ROW LEVEL SECURITY;
ALTER TABLE inbox_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE calculator_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE bonus_trackers ENABLE ROW LEVEL SECURITY;
ALTER TABLE immunization_series ENABLE ROW LEVEL SECURITY;
ALTER TABLE practice_bookmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ccm_time_entries ENABLE ROW LEVEL SECURITY;

-- Create policy: users can only see rows matching their practice
CREATE POLICY practice_isolation ON patient_records
    USING (practice_id = current_setting('app.current_practice_id')::INTEGER);

CREATE POLICY practice_isolation ON billing_opportunities
    USING (practice_id = current_setting('app.current_practice_id')::INTEGER);

CREATE POLICY practice_isolation ON care_gaps
    USING (practice_id = current_setting('app.current_practice_id')::INTEGER);

-- Repeat for all 21 tenant-scoped tables (automated via migration script)
```

- [ ] Write Alembic migration to enable RLS on all 21 tenant-scoped tables
- [ ] Create `practice_isolation` policy on each table using `current_setting('app.current_practice_id')`
- [ ] Set `app.current_practice_id` in SQLAlchemy `before_cursor_execute` event hook
- [ ] Create superuser bypass: `ALTER ROLE carecompanion_admin BYPASSRLS`
- [ ] Test: verify application user cannot bypass RLS even with raw SQL

### 8.5.2 Setting Practice Context at Database Level
```python
from sqlalchemy import event

@event.listens_for(db.engine, "before_cursor_execute")
def set_practice_context(conn, cursor, statement, parameters, context, executemany):
    """Set PostgreSQL session variable for RLS before every query."""
    from flask import g
    practice_id = getattr(g, 'practice_id', None)
    if practice_id:
        cursor.execute("SET LOCAL app.current_practice_id = %s", (str(practice_id),))
```

- [ ] Implement `before_cursor_execute` listener in Flask app factory
- [ ] Use `SET LOCAL` (transaction-scoped) rather than `SET` (session-scoped) for safety
- [ ] Verify RLS variable is cleared between requests (Flask's request-scoped connection pooling)
- [ ] Performance test: measure overhead of `SET LOCAL` on every query (target: < 1ms)

### 8.5.3 RLS Test Suite
- [ ] Test: Practice A user with RLS sees only Practice A rows
- [ ] Test: Practice A user via raw SQL (bypassing ORM) still blocked by RLS
- [ ] Test: Platform admin with BYPASSRLS can see all rows
- [ ] Test: Missing `app.current_practice_id` setting returns zero rows (fail-closed)
- [ ] Test: Concurrent requests from different practices get correct isolation
- [ ] Test: Celery workers set practice context before processing tasks

## 8.6 Tenant-Aware Celery Tasks

### 8.6.1 Task Pattern
```python
from celery import Task

class PracticeScopedTask(Task):
    """Base task class that sets practice context before execution."""

    def __call__(self, *args, **kwargs):
        practice_id = kwargs.pop('practice_id', None) or args[0]
        with app.app_context():
            g.practice_id = practice_id
            # Also set PostgreSQL RLS context
            db.session.execute(
                text("SET LOCAL app.current_practice_id = :pid"),
                {"pid": str(practice_id)}
            )
            return super().__call__(*args, **kwargs)
```

- [ ] Create `PracticeScopedTask` base class
- [ ] All tenant-scoped tasks must use `base=PracticeScopedTask`
- [ ] Every task that touches patient data must receive `practice_id` as first argument
- [ ] Task signatures: `evaluate_billing.delay(practice_id=42, patient_fhir_id='abc')`
- [ ] Validate `practice_id` exists before processing (reject stale tasks)
- [ ] Log `practice_id` in all task log entries for audit trail

### 8.6.2 Task Queue Isolation (Optional for High-Priority Tenants)
```python
# Enterprise tenants get dedicated queues
CELERY_TASK_ROUTES = {
    'billing.evaluate': {
        'queue': lambda task, args, kwargs: (
            f'billing_enterprise_{kwargs["practice_id"]}'
            if is_enterprise_practice(kwargs['practice_id'])
            else 'billing'
        )
    },
}
```

- [ ] Default: all practices share queues (`billing`, `fhir_sync`, `email`, `reports`)
- [ ] Enterprise option: dedicated queues per practice (prevents noisy neighbor)
- [ ] Monitoring: per-practice queue depth metrics for capacity planning
- [ ] Priority: Enterprise tasks get higher Celery priority (lower number = higher priority)

## 8.7 Data Migration for Adding practice_id

### 8.7.1 Migration Strategy (Zero-Downtime)
```python
"""Alembic migration: add practice_id to all tenant-scoped tables."""

def upgrade():
    # Step 1: Add column as nullable (non-breaking)
    op.add_column('patient_records', sa.Column('practice_id', sa.Integer(), nullable=True))
    op.add_column('billing_opportunities', sa.Column('practice_id', sa.Integer(), nullable=True))
    # ... (all 21 tables)

    # Step 2: Backfill existing data with practice_id = 1 (founder practice)
    op.execute("UPDATE patient_records SET practice_id = 1 WHERE practice_id IS NULL")
    op.execute("UPDATE billing_opportunities SET practice_id = 1 WHERE practice_id IS NULL")
    # ... (all 21 tables)

    # Step 3: Make column NOT NULL (after backfill)
    op.alter_column('patient_records', 'practice_id', nullable=False)
    op.alter_column('billing_opportunities', 'practice_id', nullable=False)
    # ... (all 21 tables)

    # Step 4: Add foreign key constraints
    op.create_foreign_key('fk_patient_records_practice', 'patient_records',
                          'practices', ['practice_id'], ['id'])
    # ... (all 21 tables)

    # Step 5: Add composite indexes for query performance
    op.create_index('ix_patient_records_practice_id', 'patient_records', ['practice_id'])
    op.create_index('ix_billing_opp_practice_id', 'billing_opportunities', ['practice_id'])
    # ... (all 21 tables)
```

- [ ] Write Alembic migration script with 5-step approach (add nullable, backfill, set NOT NULL, FK, index)
- [ ] Test migration on copy of production database before running on real data
- [ ] Verify migration is idempotent (safe to re-run)
- [ ] Estimate migration time for 100K rows per table (target: < 5 minutes total)
- [ ] Create rollback migration (drop columns) in case of failure

### 8.7.2 Composite Indexes for Multi-Tenant Queries
```sql
-- Every query filters by practice_id first, so it should be the leading index column
CREATE INDEX ix_patient_records_practice_created ON patient_records (practice_id, created_at DESC);
CREATE INDEX ix_billing_opp_practice_status ON billing_opportunities (practice_id, status, created_at DESC);
CREATE INDEX ix_care_gaps_practice_status ON care_gaps (practice_id, status);
CREATE INDEX ix_schedules_practice_date ON schedules (practice_id, appointment_date);
CREATE INDEX ix_audit_logs_practice_ts ON audit_logs (practice_id, timestamp DESC);
CREATE INDEX ix_ccm_practice_patient ON ccm_enrollments (practice_id, patient_fhir_id);
```

- [ ] Create composite indexes with `practice_id` as leading column on all tenant-scoped tables
- [ ] Add `EXPLAIN ANALYZE` tests for top 20 queries to verify index usage
- [ ] Monitor index size and bloat after initial data load

## 8.8 Tenant Deletion and Data Export

### 8.8.1 Practice Data Export (GDPR/HIPAA Right of Access)
- [ ] Implement `GET /api/v1/admin/export` endpoint (practice_admin role required)
- [ ] Export format: ZIP file containing JSON files per resource type
- [ ] Include: patients, billing_opportunities, care_gaps, ccm_enrollments, audit_logs, settings
- [ ] Exclude: shared platform data (billing rules, drug caches)
- [ ] Generate export as background Celery task (may take minutes for large practices)
- [ ] Notify admin via email when export is ready for download
- [ ] Export download link expires after 24 hours (signed S3 URL)
- [ ] Log all data exports in audit trail

### 8.8.2 Practice Deletion (Account Closure)
- [ ] Soft-delete first: set `Practice.status = 'deleted'`, `deleted_at = now()`
- [ ] Soft-deleted practices: hide from UI, block logins, stop FHIR syncs, stop Celery tasks
- [ ] 30-day recovery window: practice admin can request reactivation via support
- [ ] After 30 days: hard-delete all practice data (cascade delete on all 21 tenant-scoped tables)
- [ ] Hard-delete process: Celery task that deletes in batches (1000 rows at a time) to avoid DB locks
- [ ] Retain audit logs for 6 years per HIPAA even after practice deletion
- [ ] Send confirmation email to practice admin after hard-delete completes
- [ ] Cancel Stripe subscription on soft-delete
---

# 9. Cloud Deployment â€” Docker / AWS / CI-CD

> Complete deployment specification including Dockerfiles, Terraform, CI/CD pipelines,
> monitoring, and operational runbooks.

## 9.1 Docker Configuration

### 9.1.1 Web Service Dockerfile
```dockerfile
FROM python:3.11-slim AS base

# Security: non-root user
RUN groupadd -r carecompanion && useradd -r -g carecompanion carecompanion

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn[gevent]

# Copy application code
COPY . .

# Security: drop to non-root
USER carecompanion

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "gevent", \
     "--timeout", "120", "--graceful-timeout", "30", "--access-logfile", "-", "app:create_app()"]
```

- [ ] Create `Dockerfile` for web service
- [ ] Create `Dockerfile.worker` for Celery worker (same base, different CMD)
- [ ] Create `Dockerfile.beat` for Celery Beat (same base, different CMD)
- [ ] Create `.dockerignore` â€” exclude `venv/`, `data/`, `__pycache__/`, `.git/`, `*.pyc`, `tesseract/`
- [ ] Pin Python version: `python:3.11.9-slim` (specific patch for reproducibility)
- [ ] Multi-stage build: builder stage for compilation, runtime stage without gcc
- [ ] Verify non-root user works with Gunicorn

### 9.1.2 Docker Compose (Local Development)
```yaml
version: '3.8'
services:
  web:
    build: .
    ports: ["5000:8000"]
    environment:
      - DATABASE_URL=postgresql://cc:cc@db:5432/carecompanion
      - REDIS_URL=redis://redis:6379/0
      - FLASK_DEBUG=true
    depends_on: [db, redis]

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - DATABASE_URL=postgresql://cc:cc@db:5432/carecompanion
      - REDIS_URL=redis://redis:6379/0
    depends_on: [db, redis]

  beat:
    build:
      context: .
      dockerfile: Dockerfile.beat
    environment:
      - DATABASE_URL=postgresql://cc:cc@db:5432/carecompanion
      - REDIS_URL=redis://redis:6379/0
    depends_on: [db, redis]

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: cc
      POSTGRES_PASSWORD: cc
      POSTGRES_DB: carecompanion
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports: ["5432:5432"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

volumes:
  pgdata:
```

- [ ] Create `docker-compose.yml` for local dev
- [ ] Create `docker-compose.test.yml` for CI testing
- [ ] Verify all services start and communicate
- [ ] Add volume mount for live code reload in dev

### 9.1.3 Celery Worker Dockerfile CMD
```dockerfile
CMD ["celery", "-A", "app.celery_app", "worker", \
     "--loglevel=info", "--concurrency=4", \
     "-Q", "default,billing,fhir_sync,email,reports"]
```

### 9.1.4 Celery Beat Dockerfile CMD
```dockerfile
CMD ["celery", "-A", "app.celery_app", "beat", \
     "--loglevel=info", "--schedule=/tmp/celerybeat-schedule"]
```

## 9.2 AWS Infrastructure (Terraform)

### 9.2.1 Terraform Structure
```
infra/
â”œâ”€â”€ main.tf
â”œâ”€â”€ variables.tf
â”œâ”€â”€ outputs.tf
â”œâ”€â”€ terraform.tfvars
â”œâ”€â”€ modules/
â”‚   â”œâ”€â”€ vpc/
â”‚   â”œâ”€â”€ ecs/
â”‚   â”œâ”€â”€ rds/
â”‚   â”œâ”€â”€ elasticache/
â”‚   â”œâ”€â”€ alb/
â”‚   â”œâ”€â”€ s3/
â”‚   â”œâ”€â”€ ecr/
â”‚   â””â”€â”€ monitoring/
â””â”€â”€ environments/
    â”œâ”€â”€ staging.tfvars
    â””â”€â”€ production.tfvars
```

- [ ] Create VPC module: 3-AZ, public/private/db subnets, NAT gateways
- [ ] Create ECR module: repositories for web, worker, beat images
- [ ] Create ECS module: cluster, service definitions, task definitions, auto-scaling
- [ ] Create RDS module: PostgreSQL 15, multi-AZ, automated backups, encryption
- [ ] Create ElastiCache module: Redis 7, encryption at rest + in transit
- [ ] Create ALB module: HTTPS listener, health checks, WAF integration
- [ ] Create S3 module: document bucket, backup bucket, lifecycle rules
- [ ] Create monitoring module: CloudWatch dashboards, alarms, SNS topics
- [ ] Create IAM roles: ECS task role, ECS execution role, backup role
- [ ] Create security groups: ALBâ†’ECS, ECSâ†’RDS, ECSâ†’Redis, ECSâ†’Internet

### 9.2.2 ECS Task Definition (Web)
```json
{
  "family": "carecompanion-web",
  "cpu": "512",
  "memory": "1024",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "executionRoleArn": "arn:aws:iam::role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::role/carecompanionTaskRole",
  "containerDefinitions": [{
    "name": "web",
    "image": "{ecr_url}/carecompanion-web:latest",
    "portMappings": [{"containerPort": 8000}],
    "environment": [],
    "secrets": [
      {"name": "DATABASE_URL", "valueFrom": "arn:aws:secretsmanager:..."},
      {"name": "REDIS_URL", "valueFrom": "arn:aws:secretsmanager:..."},
      {"name": "SECRET_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/carecompanion-web",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "web"
      }
    },
    "healthCheck": {
      "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
      "interval": 30,
      "timeout": 5,
      "retries": 3
    }
  }]
}
```

- [ ] Create web task definition with secrets from Secrets Manager
- [ ] Create worker task definition (same image, different command)
- [ ] Create beat task definition (single instance, leader election)
- [ ] Configure CloudWatch log groups with 30-day retention
- [ ] Configure ECS service auto-scaling: CPU > 70% â†’ scale out

### 9.2.3 Domain & TLS
- [ ] Register domain: `carecompanion.health` or `app.carecompanion.io`
- [ ] Request ACM certificate for `*.carecompanion.health`
- [ ] Configure ALB HTTPS listener with ACM certificate
- [ ] Redirect HTTP â†’ HTTPS (ALB listener rule)
- [ ] HSTS header: `Strict-Transport-Security: max-age=31536000; includeSubDomains`

## 9.3 CI/CD Pipeline (GitHub Actions)

### 9.3.1 Workflow: Build + Test + Deploy
```yaml
# .github/workflows/deploy.yml
name: Build and Deploy
on:
  push:
    branches: [main, staging]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_carecompanion
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports: [5432:5432]
      redis:
        image: redis:7
        ports: [6379:6379]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt -r requirements-test.txt
      - run: pytest tests/ --cov=. --cov-report=xml
      - uses: codecov/codecov-action@v4

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
      - uses: aws-actions/amazon-ecr-login@v2
      - run: |
          docker build -t $ECR_URL/web:$GITHUB_SHA .
          docker push $ECR_URL/web:$GITHUB_SHA

  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/staging'
    runs-on: ubuntu-latest
    steps:
      - run: |
          aws ecs update-service --cluster carecompanion-staging \
            --service web --force-new-deployment

  deploy-production:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production  # Requires approval
    steps:
      - run: |
          aws ecs update-service --cluster carecompanion-prod \
            --service web --force-new-deployment
```

- [ ] Create `.github/workflows/test.yml` â€” runs on all PRs
- [ ] Create `.github/workflows/deploy.yml` â€” builds + deploys on merge
- [ ] Configure GitHub Environments: `staging` (auto), `production` (manual approval)
- [ ] Configure AWS OIDC provider for GitHub Actions (no long-lived keys)
- [ ] Add branch protection: require PR reviews + passing tests before merge
- [ ] Add Dependabot for dependency updates
- [ ] Add CodeQL security scanning

### 9.3.2 Database Migration in CI/CD
- [ ] Run `alembic upgrade head` as part of deploy step (before new code goes live)
- [ ] Use ECS one-off task for migration: `aws ecs run-task --overrides '{"command": ["alembic", "upgrade", "head"]}'`
- [ ] Migration must be backward-compatible (old code works with new schema during rolling deploy)
- [ ] Add `alembic downgrade -1` rollback command to emergency playbook

## 9.4 Monitoring & Observability

### 9.4.1 Application Metrics
- [ ] Sentry integration: `sentry-sdk[flask]` for error tracking
- [ ] Sentry performance monitoring: transaction sampling (10% in production)
- [ ] Custom Sentry tags: `practice_id`, `user_id`, `module`

### 9.4.2 CloudWatch Alarms
- [ ] ECS CPU > 80% for 5 minutes â†’ SNS alert
- [ ] ECS memory > 80% for 5 minutes â†’ SNS alert
- [ ] RDS CPU > 70% for 10 minutes â†’ SNS alert
- [ ] RDS free storage < 10 GB â†’ SNS alert
- [ ] RDS connections > 80 â†’ SNS alert
- [ ] ALB 5xx error rate > 1% for 5 minutes â†’ PagerDuty
- [ ] ALB target response time p99 > 5s â†’ SNS alert
- [ ] Celery queue depth > 500 for 10 minutes â†’ SNS alert
- [ ] Health check failures > 3 â†’ PagerDuty

### 9.4.3 Structured Logging
```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)
```

- [ ] Replace Python `logging` with `structlog` for JSON output
- [ ] Add `practice_id`, `user_id`, `request_id` to all log entries
- [ ] CloudWatch Logs Insights queries for troubleshooting
- [ ] Log retention: 30 days in CloudWatch, 1 year in S3 (HIPAA)

### 9.4.4 Uptime Monitoring
- [ ] External health check: Pingdom or UptimeRobot on `https://app.carecompanion.health/health`
- [ ] Status page: `status.carecompanion.health` (e.g. Statuspage.io or Instatus)
- [ ] Incident response: PagerDuty for P0/P1, email for P2/P3

## 9.5 Environment Configuration

### 9.5.1 Environment Variables by Environment

| Variable | Staging | Production |
|----------|---------|------------|
| `FLASK_ENV` | `staging` | `production` |
| `FLASK_DEBUG` | `false` | `false` |
| `DATABASE_URL` | Secrets Manager | Secrets Manager |
| `REDIS_URL` | Secrets Manager | Secrets Manager |
| `SECRET_KEY` | Secrets Manager | Secrets Manager |
| `SENTRY_DSN` | Sentry staging DSN | Sentry production DSN |
| `SENTRY_TRACES_SAMPLE_RATE` | `1.0` | `0.1` |
| `STRIPE_SECRET_KEY` | Stripe test key | Stripe live key |
| `SENDGRID_API_KEY` | Secrets Manager | Secrets Manager |
| `LOG_LEVEL` | `DEBUG` | `INFO` |
| `ALLOWED_ORIGINS` | `https://staging.carecompanion.health` | `https://app.carecompanion.health` |

- [ ] Create AWS Secrets Manager entries for all sensitive values
- [ ] Create parameter store entries for non-sensitive config
- [ ] Verify ECS task role can access Secrets Manager
- [ ] Rotate secrets quarterly (automated via Lambda)

---

# 10. MVP Scope â€” Phase 0 + Phase 1

> Defines the minimum viable product for market launch. Phase 0 is infrastructure.
> Phase 1 is the first customer-facing release.

## 10.1 Phase 0 â€” Infrastructure Foundation

### 10.1.1 PostgreSQL Migration
- [ ] Set up PostgreSQL 15 locally (Docker)
- [ ] Create all model schemas with `practice_id` columns
- [ ] Configure Alembic and create initial migration
- [ ] Write SQLite â†’ PostgreSQL ETL script
- [ ] Run ETL for existing practice data (practice_id = 1)
- [ ] Verify all queries work against PostgreSQL
- [ ] Performance test: billing evaluation on PostgreSQL (target: < 500ms)

### 10.1.2 Multi-Tenancy Foundation
- [ ] Create `Practice` model and migration
- [ ] Create `UserPractice` junction table
- [ ] Add `practice_id` to all 21 tenant-scoped models
- [ ] Implement `PracticeContextMiddleware`
- [ ] Implement `PracticeScopedMixin` for auto-filtering
- [ ] Write isolation tests (Practice A can't see Practice B data)

### 10.1.3 Desktop Coupling Removal
- [ ] Remove all PyAutoGUI imports and usage
- [ ] Remove all Tesseract OCR imports and usage
- [ ] Remove `agent/mrn_reader.py`, `agent/ocr_helpers.py`, `agent/pyautogui_runner.py`, `agent/ac_window.py`
- [ ] Remove PyInstaller build system (`build.py`, `carecompanion.spec`, `launcher.py`)
- [ ] Remove Windows service wrapper (`agent_service.py`)
- [ ] Remove all coordinate-based config values
- [ ] Create stub FHIR adapter (returns mock data) for testing

### 10.1.4 Celery Integration
- [ ] Replace APScheduler with Celery + Celery Beat
- [ ] Migrate 15 scheduled jobs to Celery periodic tasks
- [ ] Configure Redis as broker
- [ ] Verify all background tasks work with PostgreSQL
- [ ] Add Flower for Celery monitoring (internal tool)

### 10.1.5 Docker + Local Dev
- [ ] Create Dockerfiles (web, worker, beat)
- [ ] Create docker-compose.yml
- [ ] Verify full stack runs in Docker locally
- [ ] Document local development setup in README

### 10.1.6 Auth + Security Hardening
- [ ] Add JWT tokens for API endpoints (in addition to session auth)
- [ ] Add MFA support (TOTP via `pyotp`)
- [ ] Add password complexity requirements (12+ chars, mixed case, number)
- [ ] Add account lockout (5 failed attempts â†’ 15 min lockout)
- [ ] Add forced password rotation (90 days)
- [ ] CORS configuration (whitelist origins only)
- [ ] Rate limiting on auth endpoints (5 attempts/minute)

**Phase 0 Completion Gate:** All of the above checked before starting Phase 1.

## 10.2 Phase 1 â€” MVP Feature Set

### 10.2.1 Core Billing Module
- [ ] Billing opportunity dashboard â€” list all pending opportunities for today's patients
- [ ] Billing detail view â€” show documentation checklist, estimated revenue, scoring breakdown
- [ ] Capture/Dismiss workflow â€” provider marks opportunity as captured or dismissed (with reason)
- [ ] Revenue summary â€” daily/weekly/monthly revenue from captured billing
- [ ] All 25 billing detectors operational via FHIR data source
- [ ] Visit stack builder (Professional + Enterprise tiers only)
- [ ] Code specificity recommender (Professional + Enterprise tiers only)

### 10.2.2 Care Gap Module
- [ ] Care gap dashboard â€” all open gaps for practice panel
- [ ] Patient-level gap view â€” all gaps for a specific patient
- [ ] Gap resolution â€” mark gap as addressed/completed/declined
- [ ] 20 USPSTF default rules active
- [ ] Custom rule creation (Enterprise tier only)
- [ ] Outreach tracking â€” log patient contacts for gap closure

### 10.2.3 Dashboard / Today View
- [ ] Today's schedule display (from FHIR Appointment or direct schedule import)
- [ ] Per-patient billing opportunity count badge
- [ ] Per-patient care gap count badge
- [ ] Visit duration estimator
- [ ] Quick-launch to billing/caregap detail for any patient

### 10.2.4 Authentication & User Management
- [ ] Login / logout with session management
- [ ] User registration (practice admin creates users)
- [ ] Role assignment (provider, MA, practice_admin)
- [ ] Practice settings page
- [ ] User preferences (notification settings, timezone, display preferences)

### 10.2.5 FHIR Integration (MVP Scope)
- [ ] FHIR setup wizard in practice admin
- [ ] EHR connection test (`GET /metadata`)
- [ ] Patient roster sync (initial + nightly incremental)
- [ ] On-demand patient data refresh (provider clicks "Sync" in UI)
- [ ] Support at minimum: Epic, Cerner, Athena (3 largest EHR platforms)
- [ ] Graceful degradation: if FHIR unavailable, show cached data with "stale" indicator

### 10.2.6 Notifications
- [ ] Email notifications via SendGrid (daily digest, critical alerts)
- [ ] In-app notification bell with unread count
- [ ] WebSocket for real-time billing opportunity alerts
- [ ] Configurable notification preferences per user

### 10.2.7 Admin Module
- [ ] Practice management (name, NPI, settings)
- [ ] User management (list, add, deactivate)
- [ ] Billing detector toggles
- [ ] Subscription management (link to Stripe Portal)
- [ ] Usage statistics (API calls, FHIR syncs, active users)

### 10.2.8 Subscription & Payment
- [ ] Stripe Checkout integration for new subscriptions
- [ ] Stripe Customer Portal for plan changes, invoices, payment methods
- [ ] Trial period (30 days free)
- [ ] Feature gating by tier (Essentials/Professional/Enterprise)
- [ ] Grace period on failed payments (7 days before feature degradation)

### 10.2.9 MVP Routes Required

| Route | Blueprint | Template | API? |
|-------|-----------|----------|------|
| `GET /` | dashboard | `dashboard/today.html` | No |
| `GET /login` | auth | `auth/login.html` | No |
| `POST /login` | auth | â€” | No |
| `GET /logout` | auth | â€” | No |
| `GET /billing` | billing | `billing/dashboard.html` | No |
| `GET /billing/<id>` | billing | `billing/detail.html` | No |
| `POST /billing/<id>/capture` | billing | â€” | Yes |
| `POST /billing/<id>/dismiss` | billing | â€” | Yes |
| `GET /caregap` | caregap | `caregap/dashboard.html` | No |
| `GET /caregap/patient/<mrn>` | caregap | `caregap/patient.html` | No |
| `POST /caregap/<id>/resolve` | caregap | â€” | Yes |
| `GET /revenue` | revenue | `revenue/summary.html` | No |
| `GET /admin` | admin | `admin/dashboard.html` | No |
| `GET /admin/users` | admin | `admin/users.html` | No |
| `GET /admin/settings` | admin | `admin/settings.html` | No |
| `GET /admin/fhir` | admin | `admin/fhir_setup.html` | No |
| `GET /health` | â€” | â€” | Yes |
| `GET /ready` | â€” | â€” | Yes |
| `GET /api/v1/billing` | api | â€” | Yes (JSON) |
| `GET /api/v1/caregaps` | api | â€” | Yes (JSON) |
| `GET /api/v1/patients` | api | â€” | Yes (JSON) |
| `POST /api/stripe/webhook` | stripe | â€” | Yes |
| `POST /api/fhir/webhook/<id>` | fhir | â€” | Yes |

**MVP Route Count: 23 routes (subset of 250+ current endpoints)**

**Phase 1 Completion Gate:** All above checked and verified in staging environment before production launch.

## 10.3 Post-MVP Phases

### Phase 2 â€” CCM/TCM/RPM Workflows
- [ ] CCM enrollment management
- [ ] CCM time logging
- [ ] CCM monthly billing automation
- [ ] TCM tracking (2-day contact, 7/14-day follow-up)
- [ ] RPM device integration (FHIR Device + Observation)

### Phase 3 â€” Advanced Analytics
- [ ] KPI dashboard (capture rate, revenue trend, care gap closure rate)
- [ ] Provider productivity metrics
- [ ] Practice benchmarking (anonymized percentile ranking)
- [ ] Bonus tracker integration

### Phase 4 â€” AI & Intelligence
- [ ] AI-powered codifying suggestions
- [ ] AI clinical note generation assist
- [ ] Predictive billing opportunity scoring (ML on closed-loop data)
- [ ] Natural language search across patient data

### Phase 5 â€” Multi-Practice & Enterprise
- [ ] Multi-location dashboard
- [ ] Cross-practice analytics
- [ ] Custom billing detector builder
- [ ] API marketplace for third-party integrations
- [ ] White-label option


## 10.4 Detailed Acceptance Criteria

### 10.4.1 Billing Dashboard Acceptance Criteria
**Story: As a provider, I want to see today's billing opportunities so I capture all available revenue.**
- [ ] Given: Provider logs in and navigates to `/billing`
- [ ] When: Page loads
- [ ] Then: Display list of all pending billing opportunities for today's scheduled patients
- [ ] And: Each row shows: patient name, opportunity type, CPT code, estimated value, confidence score
- [ ] And: Rows are sorted by estimated value descending (highest first)
- [ ] And: Color coding: green (> $100), yellow ($50-100), gray (< $50)
- [ ] And: Total estimated revenue banner at top of page
- [ ] And: Filter controls: by provider, by status (pending/captured/dismissed), by date range
- [ ] And: Page loads in < 2 seconds for practices with up to 50 patients/day
- [ ] And: Empty state message if no opportunities: "No billing opportunities detected for today"

### 10.4.2 Billing Detail View Acceptance Criteria
**Story: As a provider, I want to see documentation requirements for a billing opportunity.**
- [ ] Given: Provider clicks on a billing opportunity row
- [ ] When: Detail view loads
- [ ] Then: Display full opportunity details: CPT code, description, documentation checklist
- [ ] And: Show 8-factor scoring breakdown (collection rate, denial risk, documentation burden, etc.)
- [ ] And: Show supporting evidence from patient data (diagnoses, vitals, labs that triggered detection)
- [ ] And: "Capture" button to mark as billed
- [ ] And: "Dismiss" button with required reason dropdown (not applicable, already billed, documentation insufficient, other)
- [ ] And: History section showing previous capture/dismiss actions for this patient+code combination
- [ ] And: Link to full patient record

### 10.4.3 Care Gap Dashboard Acceptance Criteria
**Story: As a provider, I want to see all open care gaps across my patient panel.**
- [ ] Given: Provider navigates to `/caregap`
- [ ] When: Page loads
- [ ] Then: Display grouped list of all open care gaps for the practice
- [ ] And: Group by gap type (screening, immunization, chronic disease management, preventive)
- [ ] And: Each gap shows: patient name, gap type, due date, overdue indicator, last outreach date
- [ ] And: Filter controls: by gap type, by provider panel, by overdue status, by outreach status
- [ ] And: Sort options: by due date, by patient name, by gap type
- [ ] And: Badge counts per category in sidebar navigation
- [ ] And: Export to CSV button for practice managers
- [ ] And: Bulk action: "Mark as outreach sent" for selected patients

### 10.4.4 FHIR Setup Wizard Acceptance Criteria
**Story: As a practice admin, I want to connect my EHR so patient data flows automatically.**
- [ ] Given: Practice admin navigates to `/admin/fhir`
- [ ] When: No FHIR connection exists
- [ ] Then: Show setup wizard with 5 steps
- [ ] Step 1: Select EHR type (dropdown: Epic, Cerner, Athena, AllScripts, Generic FHIR)
- [ ] Step 2: Enter FHIR base URL (pre-filled based on EHR selection if known)
- [ ] Step 3: Enter OAuth2 credentials (client ID, client secret, or upload JWT key)
- [ ] Step 4: Test connection button (calls `GET /metadata`, shows success/failure)
- [ ] Step 5: Initial sync trigger (launches background task, shows progress bar)
- [ ] On completion: redirect to dashboard with "FHIR Connected" badge
- [ ] On failure: show specific error message and troubleshooting steps
- [ ] Save progress between steps (can return and complete later)

### 10.4.5 Dashboard / Today View Acceptance Criteria
**Story: As a provider, I want a summary of today's workload when I log in.**
- [ ] Given: Provider navigates to `/` (home/dashboard)
- [ ] When: Page loads
- [ ] Then: Display today's schedule with appointment list
- [ ] And: Each appointment shows: patient name, appointment time, visit type
- [ ] And: Billing opportunity count badge per patient (e.g., "3 opportunities")
- [ ] And: Care gap count badge per patient (e.g., "2 gaps")
- [ ] And: Click on patient row expands inline preview of top opportunities and gaps
- [ ] And: Revenue summary widget: "Today's potential: $X,XXX | Captured: $X,XXX"
- [ ] And: Quick stats: patients seen today, avg revenue per patient, capture rate %
- [ ] And: Notification bell in header with unread count

### 10.4.6 Notification Acceptance Criteria
**Story: As a provider, I want real-time alerts for high-value billing opportunities.**
- [ ] Given: Provider is logged in (any page)
- [ ] When: New billing opportunity detected with estimated value > $100
- [ ] Then: Browser notification (push notification if permissions granted)
- [ ] And: In-app notification bell increments unread count
- [ ] And: Notification dropdown shows: opportunity type, patient name, estimated value, timestamp
- [ ] And: Click on notification navigates to billing detail view
- [ ] And: "Mark all as read" button in notification dropdown
- [ ] And: Notification history page at `/notifications` with pagination
- [ ] And: Email digest setting: immediate, hourly, daily, or off (per user preference)

## 10.5 Data Flow Specifications

### 10.5.1 Patient Data Sync Flow
```
Celery Beat (nightly at 2 AM practice time)
  |
  v
sync_patient_roster task (practice_id)
  |
  +--> FHIR Server: GET /Patient?_count=100&_summary=true
  |    (paginate through all patients)
  |
  +--> For each new/updated patient:
  |      +--> FHIR: GET /Condition?patient={id}
  |      +--> FHIR: GET /Observation?patient={id}&category=vital-signs
  |      +--> FHIR: GET /Observation?patient={id}&category=laboratory
  |      +--> FHIR: GET /MedicationStatement?patient={id}
  |      +--> FHIR: GET /Immunization?patient={id}
  |      +--> FHIR: GET /Encounter?patient={id}&date=ge{last_sync}
  |      +--> FHIR: GET /Coverage?patient={id}
  |
  +--> Normalize FHIR resources into internal patient_data dict
  |
  +--> Store/update in PostgreSQL
  |
  +--> Trigger billing evaluation task for updated patients
  |
  +--> Update FHIR sync status: {patients_synced, errors, duration}
```

### 10.5.2 Billing Evaluation Data Flow
```
evaluate_billing task (practice_id, patient_fhir_id)
  |
  +--> Load patient_data from PostgreSQL cache
  |
  +--> Load practice billing config (enabled detectors, payer overrides)
  |
  +--> BillingCaptureEngine.evaluate(patient_data, config)
  |      |
  |      +--> Run all enabled detectors in parallel (ThreadPoolExecutor)
  |      |      +--> AWVDetector.detect(patient_data)
  |      |      +--> DepressionScreenDetector.detect(patient_data)
  |      |      +--> FallRiskDetector.detect(patient_data)
  |      |      +--> ... (25+ detectors)
  |      |
  |      +--> Collect raw opportunities
  |      +--> Deduplicate (same CPT code, same-day)
  |      +--> Score each opportunity (8-factor model)
  |      +--> Apply payer-specific adjustments
  |      +--> Return ranked opportunity list
  |
  +--> Upsert BillingOpportunity records in PostgreSQL
  |
  +--> Push WebSocket event: billing:new (for each new opportunity)
  |
  +--> Queue email notification if any opportunity > $100
```

### 10.5.3 Care Gap Evaluation Data Flow
```
evaluate_care_gaps task (practice_id, patient_fhir_id)
  |
  +--> Load patient_data from PostgreSQL cache
  |
  +--> Load care gap rules (20 default + practice custom rules)
  |
  +--> For each rule:
  |      +--> Check if patient is in target population (age, sex, conditions)
  |      +--> Check if service was performed within guideline interval
  |      +--> If gap found: create CareGap record
  |
  +--> Upsert CareGap records (avoid duplicates by patient+rule+period)
  |
  +--> Push WebSocket event: caregap:new (for each new gap)
```
---

# 11. FHIR Development & Testing Tools

> Tools, sandboxes, and testing strategies for FHIR R4 integration development.

## 11.1 FHIR Sandbox Environments

### 11.1.1 Public FHIR Sandboxes
- [ ] **HAPI FHIR Server** â€” `https://hapi.fhir.org/baseR4` (open, no auth, good for prototyping)
- [ ] **SMART on FHIR Sandbox** â€” `https://launch.smarthealthit.org` (full SMART auth flow)
- [ ] **Logica Health Sandbox** â€” `https://sandbox.logicahealth.org` (multi-EHR simulation)
- [ ] **Epic Open Sandbox** â€” `https://fhir.epic.com/interconnect-fhir-oauth/` (Epic-specific)
- [ ] **Cerner Code Sandbox** â€” `https://fhir-open.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d/` (Cerner-specific)
- [ ] **Athena Health API** â€” `https://api.platform.athenahealth.com/fhir/r4` (requires developer account)

### 11.1.2 Local FHIR Server for Development
```bash
# Run HAPI FHIR server locally
docker run -p 8080:8080 hapiproject/hapi:latest
```

- [ ] Add HAPI FHIR to `docker-compose.yml` as `fhir` service
- [ ] Pre-load test patient data (10 synthetic patients with realistic clinical data)
- [ ] Create test data loader script: `scripts/seed_fhir_test_data.py`

### 11.1.3 Synthetic Test Data
- [ ] **Synthea** â€” `https://github.com/synthetichealth/synthea` â€” generate realistic patient FHIR bundles
- [ ] Generate 100 synthetic patients with varied demographics, conditions, medications
- [ ] Include patients triggering every billing detector (at least 1 patient per detector)
- [ ] Include patients with every care gap scenario
- [ ] Include edge cases: infants (pediatric), elderly (AWV/fall risk), pregnant, multi-chronic

## 11.2 FHIR Testing Strategy

### 11.2.1 Unit Tests â€” FHIR Adapter
- [ ] Test `_fetch_patient()` with mock Patient resource â†’ correct demographics dict
- [ ] Test `_fetch_diagnoses()` with mock Condition bundle â†’ correct ICD-10 list
- [ ] Test `_fetch_medications()` with mock MedicationStatement â†’ correct drug list
- [ ] Test `_fetch_vitals()` with mock Observation (vital-signs) â†’ correct vitals dict
- [ ] Test `_fetch_lab_results()` with mock Observation (laboratory) â†’ correct lab list
- [ ] Test `_fetch_immunizations()` with mock Immunization bundle â†’ correct vaccine list
- [ ] Test `_fetch_coverage()` with mock Coverage â†’ correct payer context
- [ ] Test `_fetch_encounters()` with mock Encounter â†’ correct visit history
- [ ] Test `get_patient_data()` orchestrator â†’ complete patient_data dict
- [ ] Test pagination handling (multi-page Bundle responses)
- [ ] Test error handling (OperationOutcome, 404, 403, timeout)
- [ ] Test token refresh flow

### 11.2.2 Integration Tests â€” End-to-End with HAPI
- [ ] Load Synthea patient into local HAPI FHIR server
- [ ] Fetch full patient data via `FHIRAdapter.get_patient_data()`
- [ ] Run `BillingCaptureEngine.evaluate()` on fetched data â†’ verify billing opportunities detected
- [ ] Run `evaluate_care_gaps()` on fetched data â†’ verify care gaps identified
- [ ] Verify round-trip: FHIR â†’ internal dict â†’ billing engine â†’ correct CPT codes

### 11.2.3 EHR-Specific Integration Tests
- [ ] Epic sandbox: test full SMART on FHIR flow (authorization â†’ token â†’ data fetch)
- [ ] Cerner sandbox: test full flow
- [ ] Athena sandbox: test full flow
- [ ] Verify each EHR returns compatible FHIR resources for all required resource types
- [ ] Document EHR-specific quirks (e.g., Epic uses contained medication resources)

### 11.2.4 Mock FHIR Server for CI
```python
# tests/fhir/mock_server.py
"""Flask-based FHIR mock server for unit tests."""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/Patient/<patient_id>')
def get_patient(patient_id):
    return jsonify(MOCK_PATIENTS[patient_id])

@app.route('/Condition')
def search_conditions():
    patient_id = request.args.get('patient')
    return jsonify(create_bundle(MOCK_CONDITIONS[patient_id]))
```

- [ ] Create mock FHIR server with all required endpoints
- [ ] Pre-populate with test data for every billing detector scenario
- [ ] Run in CI without external network dependencies

## 11.3 FHIR Conformance Validation

### 11.3.1 Resource Validation
- [ ] Validate all created FHIR resources against R4 profiles using `fhir.resources` library
- [ ] Validate outgoing resources (if any) match US Core profiles
- [ ] Log validation errors for EHR-provided resources (don't reject; log and adapt)

### 11.3.2 Capability Discovery
- [ ] On practice onboarding, fetch `GET /metadata` (CapabilityStatement)
- [ ] Parse supported resources and interactions
- [ ] Warn if required resources missing (Patient, Condition, Observation, Immunization, Encounter)
- [ ] Adapt behavior based on what's available (e.g., no MedicationStatement â†’ try MedicationRequest)


## 11.4 FHIR Bulk Data Export ($export)

### 11.4.1 Bulk Data Overview
- [ ] FHIR Bulk Data Access (Flat FHIR) spec: IG `hl7.fhir.uv.bulkdata`
- [ ] Used for initial patient roster load and large-scale data migration
- [ ] Asynchronous: `GET /Patient/$export` returns `202 Accepted` with `Content-Location` polling URL
- [ ] Output format: NDJSON (newline-delimited JSON) files

### 11.4.2 Bulk Export Implementation
```python
class BulkExportClient:
    """Client for FHIR Bulk Data Export operations."""

    def __init__(self, fhir_client):
        self.client = fhir_client

    def start_export(self, resource_types=None):
        """Kick off a bulk export request."""
        params = {'_outputFormat': 'application/fhir+ndjson'}
        if resource_types:
            params['_type'] = ','.join(resource_types)
        response = self.client.get('/Patient/$export', headers={
            'Accept': 'application/fhir+json',
            'Prefer': 'respond-async',
        }, params=params)
        assert response.status_code == 202
        return response.headers['Content-Location']

    def poll_status(self, status_url):
        """Poll until export is complete."""
        response = self.client.get(status_url)
        if response.status_code == 202:
            retry_after = int(response.headers.get('Retry-After', 60))
            return {'status': 'in-progress', 'retry_after': retry_after}
        elif response.status_code == 200:
            return {'status': 'complete', 'output': response.json()['output']}

    def download_ndjson(self, file_url):
        """Download and parse an NDJSON output file."""
        response = self.client.get(file_url)
        resources = [json.loads(line) for line in response.text.strip().split('\n')]
        return resources
```

- [ ] Implement `BulkExportClient` class
- [ ] Handle `Retry-After` header (poll at suggested interval, max 5 min between polls)
- [ ] Timeout: abort if export not complete after 1 hour
- [ ] Parse NDJSON output into FHIR resource dicts
- [ ] Error handling: `OperationOutcome` in error output files
- [ ] Support resource type filtering: `_type=Patient,Condition,Observation`
- [ ] EHR support matrix:
  - [ ] Epic: supports bulk export via Backend Services
  - [ ] Cerner: supports bulk export (limited resource types)
  - [ ] Athena: limited/no bulk export support (fall back to individual queries)

### 11.4.3 Bulk Export for Initial Onboarding
- [ ] On practice signup: offer "Initial Bulk Import" option
- [ ] Trigger `$export` for Patient, Condition, Observation, MedicationStatement, Immunization, Encounter
- [ ] Process NDJSON files in Celery worker (batch of 100 resources at a time)
- [ ] Progress tracking: store export job status in `PracticeSyncJob` table
- [ ] Show progress bar in FHIR setup wizard (percentage based on processed files)
- [ ] After bulk import: switch to incremental sync (daily differential)

## 11.5 FHIR Subscription Notifications

### 11.5.1 FHIR Subscription (R4 Backport / R5)
- [ ] Subscribe to patient data changes via FHIR Subscriptions
- [ ] Subscription topic: new Encounter (patient checked in)
- [ ] Subscription topic: updated Condition (new diagnosis added)
- [ ] Subscription topic: new Observation (new lab result)
- [ ] Channel: REST-hook (FHIR server sends POST to our webhook)
- [ ] Webhook endpoint: `POST /api/fhir/webhook/{practice_id}`

### 11.5.2 Webhook Handler
```python
@fhir_bp.route('/api/fhir/webhook/<int:practice_id>', methods=['POST'])
def fhir_webhook(practice_id):
    """Handle FHIR Subscription notifications."""
    # Verify webhook signature/token
    practice = Practice.query.get_or_404(practice_id)
    if not verify_fhir_webhook_token(request, practice):
        abort(401)

    bundle = request.get_json()
    if bundle.get('resourceType') != 'Bundle':
        abort(400)

    for entry in bundle.get('entry', []):
        resource = entry.get('resource', {})
        resource_type = resource.get('resourceType')
        patient_ref = extract_patient_reference(resource)

        if patient_ref:
            # Queue async processing
            process_fhir_notification.delay(
                practice_id=practice_id,
                resource_type=resource_type,
                patient_fhir_id=patient_ref,
                resource_data=resource,
            )

    return jsonify({'status': 'accepted'}), 202
```

- [ ] Implement webhook endpoint with signature verification
- [ ] Parse incoming Bundle/notification resource
- [ ] Extract patient reference from any resource type
- [ ] Queue Celery task for async processing (don't block webhook response)
- [ ] Return 202 immediately (FHIR servers expect fast response)
- [ ] Idempotent processing: handle duplicate notifications gracefully
- [ ] EHR support: Epic supports Subscriptions; Cerner/Athena vary

## 11.6 FHIR Performance Testing

### 11.6.1 Performance Benchmarks
| Operation | Target Latency | Max Acceptable |
|-----------|---------------|----------------|
| Single patient fetch (all resources) | < 2s | 5s |
| Billing evaluation (1 patient) | < 500ms | 1s |
| Care gap evaluation (1 patient) | < 300ms | 800ms |
| Patient roster sync (100 patients) | < 5 min | 15 min |
| Bulk export (1000 patients) | < 30 min | 60 min |
| Dashboard load (today's patients) | < 1s | 3s |

### 11.6.2 Load Testing Plan
- [ ] Tool: `locust` (Python-based load testing)
- [ ] Scenario 1: 50 concurrent users viewing billing dashboard
- [ ] Scenario 2: 10 concurrent FHIR syncs for different practices
- [ ] Scenario 3: Billing evaluation for 200 patients simultaneously
- [ ] Scenario 4: WebSocket notification delivery under load
- [ ] Scenario 5: API endpoint stress test (100 req/s sustained)
- [ ] Environment: Local Docker Compose + HAPI FHIR with 1000 synthetic patients
- [ ] Success criteria: p99 latency within "Max Acceptable" column
- [ ] Run before every major release

### 11.6.3 Locust Test Example
```python
from locust import HttpUser, task, between

class BillingUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.client.post('/login', json={
            'email': 'test@example.com',
            'password': 'test_password_123'
        })

    @task(3)
    def view_billing_dashboard(self):
        self.client.get('/billing')

    @task(1)
    def view_billing_detail(self):
        self.client.get('/billing/1')

    @task(1)
    def capture_opportunity(self):
        self.client.post('/billing/1/capture', json={'notes': 'Billed'})
```

## 11.7 FHIR CI/CD Pipeline Integration

### 11.7.1 FHIR Tests in CI
- [ ] Step 1: Start HAPI FHIR container in CI (GitHub Actions service container)
- [ ] Step 2: Load synthetic test data (10 patients with known conditions)
- [ ] Step 3: Run FHIR adapter unit tests (mocked)
- [ ] Step 4: Run FHIR adapter integration tests (against HAPI)
- [ ] Step 5: Run billing engine integration tests (FHIR data flow)
- [ ] Step 6: Run care gap integration tests (FHIR data flow)
- [ ] Step 7: Fail build if any FHIR test fails

### 11.7.2 GitHub Actions FHIR Service
```yaml
services:
  fhir:
    image: hapiproject/hapi:latest
    ports:
      - 8080:8080
    env:
      hapi.fhir.server_address: http://localhost:8080/fhir
    options: >-
      --health-cmd "curl -f http://localhost:8080/fhir/metadata"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

- [ ] Add HAPI FHIR service container to `.github/workflows/test.yml`
- [ ] Create `scripts/seed_fhir_ci_data.py` to load test data from Synthea JSON files
- [ ] Store Synthea test bundles in `tests/fixtures/fhir/` directory
- [ ] Total CI FHIR test time target: < 3 minutes
---

# 12. HIPAA & Security Compliance

> Complete security specification for HIPAA Technical + Administrative safeguards,
> encryption, access control, audit logging, and incident response.

## 12.1 HIPAA Technical Safeguards

### 12.1.1 Access Control (Â§164.312(a))
- [ ] Unique user identification: every user has unique `user_id`, no shared accounts
- [ ] Emergency access procedure: documented break-glass process for platform admin
- [ ] Automatic logoff: session timeout at 30 minutes of inactivity
- [ ] Encryption and decryption: AES-256 for data at rest, TLS 1.2+ in transit

**Implementation checklist:**
- [ ] Flask session timeout: `PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)`
- [ ] Session cookie: `Secure=True`, `HttpOnly=True`, `SameSite=Lax`
- [ ] JWT expiry: 15 minutes (access token), 7 days (refresh token)
- [ ] Password complexity: min 12 chars, must include uppercase, lowercase, number
- [ ] Account lockout: 5 failed attempts â†’ 15 minute lockout (configurable per practice)
- [ ] MFA: optional for Professional tier, required for Enterprise tier
- [ ] IP allowlisting: optional per-practice setting (Enterprise tier)
- [ ] Role-based access: provider/MA/practice_admin/billing_specialist/platform_admin

### 12.1.2 Audit Controls (Â§164.312(b))
- [ ] Record all login/logout events in `AuditLog`
- [ ] Record all PHI access (patient record views) in `AuditLog`
- [ ] Record all data modifications (billing status changes, gap resolutions) in `AuditLog`
- [ ] Record all admin actions (user creation, settings changes) in `AuditLog`
- [ ] Record all FHIR API calls (resource type, patient ID, timestamp) in `FHIRAuditLog`
- [ ] Record all data exports and report downloads

**AuditLog schema enhancements:**
- [ ] `id` SERIAL PK
- [ ] `timestamp` TIMESTAMPTZ NOT NULL
- [ ] `user_id` INTEGER FK
- [ ] `practice_id` INTEGER FK
- [ ] `action` VARCHAR(50) â€” login/logout/view/create/update/delete/export/fhir_access
- [ ] `resource_type` VARCHAR(50) â€” patient/billing/caregap/user/setting
- [ ] `resource_id` VARCHAR(100) â€” ID of accessed resource
- [ ] `ip_address` INET
- [ ] `user_agent` VARCHAR(500)
- [ ] `request_path` VARCHAR(500)
- [ ] `details` JSONB â€” additional context (changes made, search parameters)
- [ ] `risk_level` VARCHAR(10) â€” low/medium/high (auto-classified)

**Audit log retention:**
- [ ] 6 years in hot storage (PostgreSQL) per HIPAA Â§164.530(j)
- [ ] Archive to S3 (Glacier) after 1 year for cost optimization
- [ ] Never delete audit logs (hard retention policy)

### 12.1.3 Integrity Controls (Â§164.312(c))
- [ ] Database checksums: PostgreSQL data checksums enabled at initdb
- [ ] S3 object integrity: enable S3 object lock for backups
- [ ] Application integrity: checksum validation for deployment artifacts
- [ ] Migration integrity: Alembic migration checksums verified before execution

### 12.1.4 Transmission Security (Â§164.312(e))
- [ ] TLS 1.2+ enforced on all connections (ALB, RDS, Redis, S3, FHIR)
- [ ] HSTS header on all responses (1 year max-age)
- [ ] Certificate pinning for FHIR API calls (optional, EHR-dependent)
- [ ] No PHI transmitted over unencrypted channels (ever)
- [ ] Email notifications: no PHI in email body; links to app for details

## 12.2 Encryption Specification

### 12.2.1 Data at Rest
- [ ] PostgreSQL (RDS): AES-256 encryption via AWS KMS
- [ ] Redis (ElastiCache): at-rest encryption enabled
- [ ] S3: Server-Side Encryption with S3-managed keys (SSE-S3)
- [ ] ECS task storage: encrypted EBS volumes
- [ ] Secrets Manager: automatic AES-256 encryption

### 12.2.2 Data in Transit
- [ ] ALB â†’ Browser: TLS 1.2+ (ACM certificate)
- [ ] ECS â†’ RDS: TLS 1.2+ (require SSL in connection string)
- [ ] ECS â†’ Redis: TLS 1.2+ (in-transit encryption enabled)
- [ ] ECS â†’ S3: HTTPS only (bucket policy denies HTTP)
- [ ] ECS â†’ FHIR Servers: HTTPS only (verify SSL certificates)
- [ ] ECS â†’ Stripe/SendGrid/Sentry: HTTPS only

### 12.2.3 Application-Level Encryption
- [ ] Patient names: encrypted at application level (AES-256-GCM) before storage
- [ ] MRN: SHA-256 hashed (one-way; stored as `mrn_hash`, never plain MRN)
- [ ] FHIR OAuth tokens: AES-256-GCM encrypted in database
- [ ] User passwords: bcrypt with cost factor 12
- [ ] API keys: stored in AWS Secrets Manager, never in config files or environment variables directly
- [ ] Encryption key management: AWS KMS with automatic annual rotation

## 12.3 HIPAA Administrative Safeguards

### 12.3.1 Business Associate Agreement (BAA)
- [ ] Execute BAA with AWS (covered under AWS BAA program)
- [ ] Execute BAA with Stripe (Stripe supports BAA for healthcare)
- [ ] Execute BAA with SendGrid (Twilio BAA program)
- [ ] Execute BAA with Sentry (verify HIPAA compliance)
- [ ] Execute BAA with each customer practice (standard template)
- [ ] Review BAAs annually

### 12.3.2 Security Policies (documented)
- [ ] Information Security Policy
- [ ] Acceptable Use Policy
- [ ] Incident Response Plan
- [ ] Disaster Recovery Plan
- [ ] Data Backup and Recovery Policy
- [ ] Access Control Policy
- [ ] Employee Termination Checklist
- [ ] Workforce Training Records

### 12.3.3 Risk Assessment
- [ ] Conduct initial HIPAA Security Risk Assessment before launch
- [ ] Document all ePHI data flows (FHIR â†’ App â†’ Database â†’ Backups)
- [ ] Identify and mitigate all reasonably anticipated threats
- [ ] Review risk assessment annually
- [ ] Use NIST SP 800-66 as framework

## 12.4 Security Controls â€” Application Level

### 12.4.1 Input Validation
- [ ] All user inputs validated (type, length, format) before processing
- [ ] SQL injection prevention: parameterized queries only (SQLAlchemy ORM handles this)
- [ ] XSS prevention: Jinja2 auto-escaping enabled; `| safe` filter used sparingly and reviewed
- [ ] CSRF protection: Flask-WTF CSRFProtect on all forms
- [ ] File upload validation: MIME type check, size limits, virus scan
- [ ] API input validation: JSON schema validation for all POST/PUT endpoints

### 12.4.2 Output Security
- [ ] Content-Security-Policy header (restrict script/style sources)
- [ ] X-Content-Type-Options: nosniff
- [ ] X-Frame-Options: DENY (prevent clickjacking)
- [ ] Referrer-Policy: strict-origin-when-cross-origin
- [ ] Permissions-Policy: camera=(), microphone=(), geolocation=()
- [ ] No PHI in URL parameters (POST bodies only)
- [ ] No PHI in log messages (sanitize before logging)
- [ ] No PHI in error messages returned to client

### 12.4.3 Rate Limiting
- [ ] Login endpoint: 5 attempts per IP per minute
- [ ] API endpoints: 100 requests per minute per user
- [ ] FHIR sync: 100 requests per minute per practice (to avoid EHR throttling)
- [ ] Stripe webhook: no rate limit (but verify signature)
- [ ] Health check: no rate limit

### 12.4.4 Dependency Security
- [ ] `pip-audit` in CI pipeline â€” fail build on known vulnerabilities
- [ ] Dependabot enabled for automatic security updates
- [ ] No `eval()`, `exec()`, or `pickle.loads()` with untrusted data
- [ ] Docker base image scanning with Trivy or Snyk
- [ ] Review and audit all third-party packages before adding to requirements.txt

## 12.5 Incident Response

### 12.5.1 Incident Response Plan
- [ ] Define incident severity levels: P0 (data breach), P1 (service down), P2 (degraded), P3 (minor)
- [ ] P0 response: contain â†’ investigate â†’ notify (within 60 days per HIPAA Breach Notification Rule)
- [ ] P1 response: diagnose â†’ fix â†’ post-mortem (target: 1 hour to resolution)
- [ ] P2 response: diagnose â†’ fix (target: 4 hours to resolution)
- [ ] P3 response: track â†’ fix in next sprint

### 12.5.2 Breach Notification
- [ ] HIPAA Breach Notification Rule: notify affected individuals within 60 days
- [ ] HHS notification: within 60 days for breaches affecting 500+ individuals
- [ ] State notification: varies by state (some require faster notification)
- [ ] Document breach investigation, scope, mitigation in incident log

### 12.5.3 Backup & Recovery
- [ ] RDS automated daily backups (7-day retention)
- [ ] RDS point-in-time recovery (5-minute granularity)
- [ ] Weekly pg_dump to S3 (encrypted, versioned)
- [ ] Monthly backup restore test (verify data integrity)
- [ ] Recovery Time Objective (RTO): 4 hours
- [ ] Recovery Point Objective (RPO): 1 hour
- [ ] Documented runbook for database restore from backup



## 12.6 Web Application Firewall (WAF)

### 12.6.1 AWS WAF Rules
- [ ] Deploy AWS WAF on ALB
- [ ] Rule 1: AWS Managed Rules - Common Rule Set (CRS) - blocks known attack patterns
- [ ] Rule 2: AWS Managed Rules - Known Bad Inputs - blocks request patterns associated with exploitation
- [ ] Rule 3: AWS Managed Rules - SQL Injection Rule Set - deep SQL injection inspection
- [ ] Rule 4: AWS Managed Rules - Linux OS Rule Set - blocks Linux-specific LFI/RFI patterns
- [ ] Rule 5: Rate-based rule: 2000 requests per 5 minutes per IP (general DDoS protection)
- [ ] Rule 6: Geo-blocking: optionally restrict to US-only (configurable per deployment)
- [ ] Rule 7: IP reputation list: block known malicious IPs (AWS IP Reputation list)
- [ ] Rule 8: Custom rule: block requests with `User-Agent` matching known scanners
- [ ] Rule 9: Custom rule: block requests to `/admin` from non-allowlisted IPs (platform admin only)
- [ ] WAF logging: full request logging to S3 for incident investigation
- [ ] WAF metrics: blocked request count by rule, false positive monitoring

### 12.6.2 WAF Testing
- [ ] Verify CRS blocks common XSS payloads in request parameters
- [ ] Verify SQL injection rule blocks `' OR 1=1 --` and variants
- [ ] Verify rate limiting blocks brute-force login attempts
- [ ] Verify legitimate FHIR webhook traffic is not blocked
- [ ] Verify Stripe webhook traffic is not blocked (allowlist Stripe IPs)
- [ ] False positive review: run full regression test suite through WAF
- [ ] Tuning: adjust rules based on false positive analysis (count mode first, then block)

## 12.7 Security Monitoring and Alerting

### 12.7.1 CloudWatch Security Alarms
| Alarm | Condition | Action |
|-------|-----------|--------|
| Brute force login | > 10 failed logins from single IP in 5 min | Block IP via WAF, notify security |
| PHI bulk access | Single user views > 50 patient records in 1 hour | Alert CSM + security team |
| Admin privilege escalation | Non-admin user attempts admin endpoints | Block + log + alert |
| FHIR token abuse | More than 1000 FHIR API calls per practice per hour | Throttle + alert |
| Unusual data export | Data export triggered for > 1000 records | Require MFA re-verification |
| Off-hours access | Login from IP not seen before, outside business hours | Flag for review |
| Failed MFA | > 5 failed MFA attempts in 10 min | Lock account + alert |
| New device login | Login from unrecognized device/browser | Email notification to user |

### 12.7.2 Security Dashboard (Platform Admin)
- [ ] Real-time failed login attempt map (by IP, by user)
- [ ] Active session list (by practice, by user, with IP and device info)
- [ ] PHI access heatmap (which patients accessed most frequently, by whom)
- [ ] FHIR API usage graphs (calls per practice, errors, latency)
- [ ] WAF block rate graph (by rule, over time)
- [ ] Audit log search interface (filter by action, user, practice, date range)

### 12.7.3 Automated Security Responses
- [ ] Auto-block IP after 20 failed login attempts from same IP in 1 hour
- [ ] Auto-disable user account after 10 failed login attempts
- [ ] Auto-revoke FHIR token on suspicious access pattern detection
- [ ] Auto-terminate sessions on password change
- [ ] Auto-notify practice admin on any user permission changes

## 12.8 Penetration Testing

### 12.8.1 Annual Penetration Test Scope
- [ ] External network penetration test (public-facing endpoints)
- [ ] Web application penetration test (OWASP Top 10 coverage)
- [ ] API security test (authentication, authorization, injection)
- [ ] FHIR endpoint security test (subscription webhooks, data access)
- [ ] Social engineering test (phishing simulation for team members)
- [ ] Cloud configuration review (AWS account, IAM policies, S3 buckets)
- [ ] Container security review (Docker images, ECS task definitions)

### 12.8.2 Penetration Test Checklist
- [ ] Authentication testing: brute force, credential stuffing, session fixation, JWT vulnerabilities
- [ ] Authorization testing: IDOR, privilege escalation, cross-practice access, role bypass
- [ ] Input validation: SQL injection, XSS (reflected/stored/DOM), command injection, SSRF
- [ ] API testing: parameter tampering, mass assignment, rate limit bypass, GraphQL introspection (if applicable)
- [ ] FHIR-specific: unauthorized patient access, FHIR search parameter injection, webhook spoofing
- [ ] Business logic: billing manipulation (inflate scores), care gap falsification, subscription bypass
- [ ] Infrastructure: S3 bucket enumeration, RDS public access check, security group review

### 12.8.3 Remediation SLAs
| Severity | Definition | Fix SLA |
|----------|-----------|---------|
| Critical | Data breach possible, RCE, auth bypass | 24 hours |
| High | Privilege escalation, significant data exposure | 7 days |
| Medium | XSS, CSRF, minor data exposure | 30 days |
| Low | Information disclosure, best practice violations | 90 days |
| Info | Recommendations, hardening suggestions | Next release |

## 12.9 Key Management

### 12.9.1 AWS KMS Key Hierarchy
```
Root Key (AWS managed)
  |
  +-- carecompanion-rds-key (RDS encryption)
  |
  +-- carecompanion-s3-key (S3 backup encryption)
  |
  +-- carecompanion-secrets-key (Secrets Manager encryption)
  |
  +-- carecompanion-app-key (Application-level encryption: patient names, FHIR tokens)
```

- [ ] Create 4 KMS keys with appropriate key policies
- [ ] Key rotation: automatic annual rotation enabled on all keys
- [ ] Key usage logging: CloudTrail logs all KMS API calls
- [ ] IAM policies: only ECS task roles can use keys (principle of least privilege)
- [ ] Cross-account access: denied (keys locked to production AWS account)
- [ ] Key deletion protection: minimum 30-day waiting period

### 12.9.2 Secret Management
| Secret | Storage | Rotation |
|--------|---------|----------|
| Database password | AWS Secrets Manager | 90 days (auto) |
| Redis password | AWS Secrets Manager | 90 days (auto) |
| FHIR OAuth client secrets | AWS Secrets Manager (per practice) | On EHR re-authorization |
| Stripe API keys | AWS Secrets Manager | On Stripe key rotation |
| SendGrid API key | AWS Secrets Manager | Annual |
| JWT signing key | AWS Secrets Manager | 90 days (rotate with overlap) |
| Flask SECRET_KEY | AWS Secrets Manager | Annual |
| Sentry DSN | AWS Secrets Manager | Never (not a secret per se) |

- [ ] All secrets loaded from AWS Secrets Manager at app startup (never in env vars or config files)
- [ ] Secret caching: 5-minute local cache to reduce Secrets Manager API calls
- [ ] Secret rotation handler: Lambda function triggered by Secrets Manager rotation schedule
- [ ] Zero-downtime rotation: overlap period where both old and new secrets are valid
---

# 13. Pricing Strategy

## 13.1 Pricing Tiers

| Tier | Monthly (per provider) | Annual (per provider) | Savings |
|------|------------------------|-----------------------|---------|
| Essentials | $299/mo | $2,990/yr ($249/mo) | 17% |
| Professional | $499/mo | $4,990/yr ($416/mo) | 17% |
| Enterprise | $799/mo | $7,990/yr ($666/mo) | 17% |

## 13.2 Pricing Rationale
- **Essentials $299:** Conservative entry point. Practices capturing even 2 additional billing
  opportunities per provider per day at $50 average = $2,200/month additional revenue.
  ROI: 7:1. Low barrier to entry.
- **Professional $499:** Full billing suite. Target practice capturing 4+ additional opportunities
  per provider per day = $4,400/month. ROI: 9:1.
- **Enterprise $799:** Premium features + API + custom rules. Target practice capturing 6+ additional
  opportunities = $6,600/month. ROI: 8:1.

## 13.3 Performance-Based Alternative
- Instead of flat fee: 5% of incremental captured revenue (auditable via closed-loop tracking)
- Minimum monthly fee: $149/provider (floor)
- Maximum monthly fee: $999/provider (cap)
- Only available for Professional tier and above
- Requires closed-loop billing data integration

## 13.4 Add-On Pricing
| Add-On | Price |
|--------|-------|
| AI Clinical Assistant | +$99/provider/month |
| Additional Practice Location | $199/month flat |
| Data Migration & Setup | $2,000 one-time (waived for annual contracts) |
| Custom Detector Development | $5,000 per detector (one-time) |
| Dedicated CSM | Included in Enterprise; $500/mo for Professional |
| API Access | Included in Enterprise; $199/mo for Professional |

---

# 14. Go-to-Market Plan

## 14.1 Launch Phases

### Phase 1: Founder Sales (Months 1-3)
- Target: 5-10 practices in local/regional market
- Channel: Direct outreach, provider network, medical society contacts
- Offer: 60-day free trial + discounted annual pricing (20% off first year)
- Goal: Prove product-market fit, gather testimonials, refine onboarding

### Phase 2: Regional Expansion (Months 4-8)
- Target: 20-50 practices via channel partners
- Channel: Medical billing companies, practice management consultants, EHR resellers
- Marketing: Case studies from Phase 1 customers, ROI calculator on website
- Content: Blog posts on billing optimization, care gap closure, MIPS reporting
- Goal: Establish repeatable sales motion, optimize onboarding to < 2 hours

### Phase 3: National Scale (Months 9-18)
- Target: 100-200 practices
- Channel: Digital marketing (Google Ads, LinkedIn), conference presence (AAFP, ACP)
- Partnerships: EHR marketplace listings (Epic App Orchard, Cerner Open, Athena Marketplace)
- Product: API ecosystem for third-party integrations
- Goal: $500K ARR, positive unit economics

## 14.2 Sales Process
1. **Lead:** Inbound (website, content) or outbound (email, LinkedIn)
2. **Demo:** 30-min product walkthrough focused on their EHR + billing pain
3. **Trial:** 30-day free trial with guided setup
4. **Convert:** Follow-up at day 7, 14, 21 with ROI metrics from trial period
5. **Onboard:** 60-min setup call (FHIR config, user creation, training)
6. **Success:** Monthly check-in for first 3 months; quarterly thereafter

## 14.3 Marketing Channels
- **Website:** `carecompanion.health` â€” product pages, pricing, ROI calculator, blog
- **Content Marketing:** Weekly blog on billing optimization, regulatory updates
- **Email Marketing:** Drip campaigns for trial users, monthly newsletter for leads
- **Social Media:** LinkedIn (primary), Twitter/X (secondary)
- **Conferences:** AAFP FMX, ACP Internal Medicine Meeting, HIMSS
- **Webinars:** Monthly "Billing Intelligence for Primary Care" series
- **Referral Program:** Existing customers get 1 month free per successful referral

---

# 15. Multi-EMR Abstraction Layer

> Architecture for supporting multiple EHR systems through a unified interface.

## 15.1 EMR Adapter Pattern

### 15.1.1 Architecture
```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚         CareCompanion Application           â”‚
â”‚  (Billing Engine, Care Gaps, Workflows)     â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                   â”‚ unified patient_data dict
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚          EMR Abstraction Layer              â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚   BaseEMRAdapter (abstract class)     â”‚  â”‚
â”‚  â”‚   - get_patient_data(patient_id)      â”‚  â”‚
â”‚  â”‚   - search_patients(query)            â”‚  â”‚
â”‚  â”‚   - sync_patient(patient_id)          â”‚  â”‚
â”‚  â”‚   - get_capabilities()                â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
â”‚    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”              â”‚
â”‚  â”Œâ”€â–¼â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â–¼â”€â”€â”€â”€â”         â”‚
â”‚  â”‚Epicâ”‚  â”‚Cerner/Oracleâ”‚ â”‚Athena â”‚         â”‚
â”‚  â””â”€â”¬â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”¬â”€â”€â”€â”€â”˜         â”‚
â”‚    â”‚           â”‚            â”‚               â”‚
â”‚  â”Œâ”€â–¼â”€â”€â”  â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â–¼â”€â”€â”€â”           â”‚
â”‚  â”‚FHIRâ”‚  â”‚FHIR     â”‚  â”‚FHIR   â”‚           â”‚
â”‚  â”‚R4  â”‚  â”‚R4       â”‚  â”‚R4     â”‚           â”‚
â”‚  â””â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”˜           â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### 15.1.2 Base Adapter Interface
```python
class BaseEMRAdapter(ABC):
    """Abstract base class for EHR-specific FHIR adapters."""

    def __init__(self, practice: Practice):
        self.practice = practice
        self.client = FHIRClient(
            base_url=practice.fhir_base_url,
            client_id=practice.fhir_client_id,
            client_secret=self._get_secret(practice.fhir_client_secret_ref),
            auth_type=practice.fhir_auth_type,
        )

    @abstractmethod
    def get_patient_data(self, patient_fhir_id: str) -> dict: ...

    @abstractmethod
    def search_patients(self, query: str) -> list[dict]: ...

    @abstractmethod
    def get_capabilities(self) -> dict: ...

    def get_adapter_name(self) -> str: ...
```

- [ ] Create `fhir/adapters/__init__.py`
- [ ] Create `fhir/adapters/base.py` â€” `BaseEMRAdapter` abstract class
- [ ] Create `fhir/adapters/epic.py` â€” `EpicAdapter(BaseEMRAdapter)`
- [ ] Create `fhir/adapters/cerner.py` â€” `CernerAdapter(BaseEMRAdapter)`
- [ ] Create `fhir/adapters/athena.py` â€” `AthenaAdapter(BaseEMRAdapter)`
- [ ] Create `fhir/adapters/generic.py` â€” `GenericFHIRAdapter(BaseEMRAdapter)` (default fallback)
- [ ] Create `fhir/adapters/factory.py` â€” `get_adapter(practice) â†’ BaseEMRAdapter`

### 15.1.3 EHR-Specific Quirks

**Epic:**
- [ ] Uses `contained` medication resources (not reference-based)
- [ ] Requires `Prefer: return=representation` header for creates
- [ ] OAuth2 uses backend services flow with JWT assertion
- [ ] Appointment resource uses custom extensions for visit type
- [ ] Epic App Orchard approval required for production access

**Cerner (Oracle Health):**
- [ ] Uses `MedicationRequest` instead of `MedicationStatement` for some data
- [ ] `Observation.category` may use custom system URIs
- [ ] OAuth2 uses standard authorization_code flow
- [ ] Code Console registration required for production

**Athena:**
- [ ] Some resources behind `athenaPractice` API (non-FHIR) â€” need dual integration
- [ ] FHIR coverage may be limited for older Athena versions
- [ ] OAuth2 uses standard client_credentials flow
- [ ] Marketplace listing required for production

**Generic FHIR:**
- [ ] Assumes standard R4 compliance
- [ ] Graceful degradation: check CapabilityStatement, skip unsupported resources
- [ ] Used for smaller EHRs, Amazing Charts (when FHIR available), and eClinicalWorks

### 15.1.4 Adapter Factory
```python
ADAPTER_REGISTRY = {
    'epic': EpicAdapter,
    'cerner': CernerAdapter,
    'athena': AthenaAdapter,
    'amazing_charts': GenericFHIRAdapter,
    'allscripts': GenericFHIRAdapter,
    'eclinicalworks': GenericFHIRAdapter,
    'generic_fhir': GenericFHIRAdapter,
}

def get_adapter(practice: Practice) -> BaseEMRAdapter:
    adapter_class = ADAPTER_REGISTRY.get(practice.ehr_type, GenericFHIRAdapter)
    return adapter_class(practice)
```

- [ ] Implement factory function
- [ ] Cache adapter instances per practice (avoid re-creating on every request)
- [ ] Log adapter selection for debugging

## 15.2 Capability Detection

### 15.2.1 Auto-Detection Flow
- [ ] On FHIR setup: `GET /metadata` â†’ parse CapabilityStatement
- [ ] Extract supported `rest[0].resource[].type` list
- [ ] Extract supported search parameters per resource
- [ ] Store capabilities in `Practice.fhir_capabilities` JSONB column
- [ ] Warn user if critical resources missing (Patient, Condition, Observation)
- [ ] Automatically disable features that require unsupported resources


## 15.3 Detailed Adapter Method Specifications

### 15.3.1 Epic Adapter Implementation Details
```python
class EpicAdapter(BaseEMRAdapter):
    """Epic-specific FHIR R4 adapter with Epic quirk handling."""

    AUTH_TYPE = 'smart_backend_services'  # JWT assertion flow

    def get_patient_data(self, patient_fhir_id: str) -> dict:
        patient = self._fetch_patient(patient_fhir_id)
        conditions = self._fetch_conditions(patient_fhir_id)
        medications = self._fetch_medications_epic(patient_fhir_id)  # Epic-specific
        vitals = self._fetch_vitals(patient_fhir_id)
        labs = self._fetch_labs(patient_fhir_id)
        immunizations = self._fetch_immunizations(patient_fhir_id)
        encounters = self._fetch_encounters(patient_fhir_id)
        coverage = self._fetch_coverage(patient_fhir_id)

        return self._normalize(patient, conditions, medications, vitals,
                               labs, immunizations, encounters, coverage)

    def _fetch_medications_epic(self, patient_fhir_id):
        """Epic uses contained medication resources within MedicationRequest."""
        bundle = self.client.search('MedicationRequest', {
            'patient': patient_fhir_id,
            'status': 'active',
            '_include': 'MedicationRequest:medication',
        })
        medications = []
        for entry in bundle.get('entry', []):
            resource = entry.get('resource', {})
            if resource.get('resourceType') == 'MedicationRequest':
                med_ref = resource.get('medicationReference', {})
                # Epic embeds medication in contained resources
                contained = {r['id']: r for r in resource.get('contained', [])}
                med_id = med_ref.get('reference', '').replace('#', '')
                med_resource = contained.get(med_id, {})
                medications.append({
                    'name': self._extract_medication_name(med_resource),
                    'code': self._extract_rxnorm(med_resource),
                    'status': resource.get('status'),
                    'authored_on': resource.get('authoredOn'),
                })
        return medications

    def _get_auth_token(self):
        """Epic Backend Services: JWT assertion for access token."""
        now = int(time.time())
        claims = {
            'iss': self.practice.fhir_client_id,
            'sub': self.practice.fhir_client_id,
            'aud': f'{self.practice.fhir_base_url}/oauth2/token',
            'jti': str(uuid.uuid4()),
            'exp': now + 300,  # 5 minutes
        }
        private_key = self._get_secret(self.practice.fhir_private_key_ref)
        assertion = jwt.encode(claims, private_key, algorithm='RS384')
        response = requests.post(
            f'{self.practice.fhir_base_url}/oauth2/token',
            data={
                'grant_type': 'client_credentials',
                'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
                'client_assertion': assertion,
            }
        )
        return response.json()['access_token']
```

- [ ] Implement Epic JWT assertion auth flow (RS384 signing)
- [ ] Handle Epic's contained medication resources
- [ ] Handle Epic's custom extensions for visit type (`urn:oid:1.2.840.114350.1.13.0.1.7.4.698084.30`)
- [ ] Handle Epic's preferred `Prefer: return=representation` header
- [ ] Handle Epic's pagination: `link[rel=next]` in Bundle
- [ ] Rate limiting awareness: Epic allows ~100 requests/min per app
- [ ] Test against Epic Open Sandbox before production

### 15.3.2 Cerner Adapter Implementation Details
```python
class CernerAdapter(BaseEMRAdapter):
    """Cerner/Oracle Health-specific FHIR R4 adapter."""

    AUTH_TYPE = 'authorization_code'  # Standard OAuth2

    def _fetch_medications_cerner(self, patient_fhir_id):
        """Cerner may return MedicationRequest instead of MedicationStatement."""
        # Try MedicationStatement first
        bundle = self.client.search('MedicationStatement', {
            'patient': patient_fhir_id,
            'status': 'active',
        })
        if not bundle.get('entry'):
            # Fallback to MedicationRequest
            bundle = self.client.search('MedicationRequest', {
                'patient': patient_fhir_id,
                'status': 'active',
            })
        return self._parse_medications(bundle)

    def _fetch_vitals_cerner(self, patient_fhir_id):
        """Cerner may use custom category codes for vital signs."""
        bundle = self.client.search('Observation', {
            'patient': patient_fhir_id,
            'category': 'vital-signs',
            '_sort': '-date',
            '_count': 50,
        })
        if not bundle.get('entry'):
            # Fallback: search by Cerner-specific category URI
            bundle = self.client.search('Observation', {
                'patient': patient_fhir_id,
                'category': 'http://terminology.cerner.com/category|vital-signs',
                '_sort': '-date',
                '_count': 50,
            })
        return self._parse_vitals(bundle)
```

- [ ] Implement Cerner standard OAuth2 flow (authorization_code + PKCE)
- [ ] Handle MedicationRequest fallback when MedicationStatement unavailable
- [ ] Handle Cerner custom category URIs for Observations
- [ ] Handle Cerner-specific Encounter types and extensions
- [ ] Rate limiting: Cerner allows ~200 requests/min
- [ ] Test against Cerner Code Sandbox

### 15.3.3 Athena Adapter Implementation Details
```python
class AthenaAdapter(BaseEMRAdapter):
    """Athena-specific adapter with dual FHIR + athenaPractice API support."""

    AUTH_TYPE = 'client_credentials'

    def get_patient_data(self, patient_fhir_id: str) -> dict:
        # FHIR for standard resources
        patient = self._fetch_patient(patient_fhir_id)
        conditions = self._fetch_conditions(patient_fhir_id)
        vitals = self._fetch_vitals(patient_fhir_id)

        # athenaPractice API for resources not well-supported via FHIR
        medications = self._fetch_medications_athena_api(patient_fhir_id)
        immunizations = self._fetch_immunizations_athena_api(patient_fhir_id)

        return self._normalize(patient, conditions, medications, vitals,
                               None, immunizations, None, None)

    def _fetch_medications_athena_api(self, patient_fhir_id):
        """Use athenaPractice REST API for medications (better coverage than FHIR)."""
        athena_patient_id = self._fhir_to_athena_id(patient_fhir_id)
        response = self.athena_client.get(
            f'/patients/{athena_patient_id}/medications',
            params={'showprescriptions': 'true'}
        )
        return self._normalize_athena_medications(response.json().get('medications', []))
```

- [ ] Implement dual API strategy (FHIR + athenaPractice REST)
- [ ] Map FHIR patient IDs to Athena internal patient IDs
- [ ] Handle Athena's limited FHIR resource coverage
- [ ] Handle Athena's authentication (client_credentials with API key)
- [ ] Graceful degradation: if athenaPractice API unavailable, use FHIR-only
- [ ] Rate limiting: Athena allows ~120 requests/min
- [ ] Test against Athena developer sandbox

## 15.4 Data Normalization Rules

### 15.4.1 Code System Mapping
| Internal Field | FHIR Code System | Description |
|----------------|-------------------|-------------|
| `diagnosis.code` | `http://hl7.org/fhir/sid/icd-10-cm` | ICD-10-CM code |
| `medication.rxnorm` | `http://www.nlm.nih.gov/research/umls/rxnorm` | RxNorm code |
| `medication.ndc` | `http://hl7.org/fhir/sid/ndc` | NDC code (fallback) |
| `lab.loinc` | `http://loinc.org` | LOINC code for lab tests |
| `vital.loinc` | `http://loinc.org` | LOINC code for vitals |
| `immunization.cvx` | `http://hl7.org/fhir/sid/cvx` | CVX vaccine code |
| `payer.type` | `http://terminology.hl7.org/CodeSystem/v3-ActCode` | Coverage type |

### 15.4.2 Code Extraction Priority
```python
def extract_code(codeable_concept, preferred_systems):
    """Extract best available code from a FHIR CodeableConcept."""
    for system in preferred_systems:
        for coding in codeable_concept.get('coding', []):
            if coding.get('system') == system:
                return {'code': coding['code'], 'display': coding.get('display', ''),
                        'system': system}
    # Fallback: return first available coding
    codings = codeable_concept.get('coding', [])
    if codings:
        return {'code': codings[0]['code'], 'display': codings[0].get('display', ''),
                'system': codings[0].get('system', 'unknown')}
    return None
```

- [ ] Prefer ICD-10-CM for diagnoses (fallback: ICD-10, SNOMED CT)
- [ ] Prefer RxNorm for medications (fallback: NDC, display text)
- [ ] Prefer LOINC for labs and vitals (fallback: local codes with display text)
- [ ] Prefer CVX for immunizations (fallback: NDC, CPT)
- [ ] Log unknown code systems for analysis (may indicate EHR-specific quirks)
- [ ] Map SNOMED CT to ICD-10-CM where possible (using SNOMED-ICD-10 map table)

## 15.5 Token Management Lifecycle

### 15.5.1 OAuth2 Token Flow
```
Practice Setup (one-time)
  |
  +--> Register app with EHR (get client_id + client_secret or private key)
  |
  +--> Store credentials in AWS Secrets Manager
  |
  v
First FHIR Request
  |
  +--> Check Redis cache: fhir_token:{practice_id}
  |
  +--> Cache miss: request new token from EHR OAuth2 endpoint
  |      +--> Epic: JWT assertion (client_credentials with JWT)
  |      +--> Cerner: authorization_code + PKCE (user consent)
  |      +--> Athena: client_credentials (API key)
  |
  +--> Store token in Redis with TTL = (expiry - 60 seconds)
  |
  +--> Return token for FHIR API call
  |
  v
Subsequent Requests
  |
  +--> Cache hit: use cached token
  |
  +--> On 401 response: invalidate cache, request new token, retry once
  |
  +--> On repeated 401: mark FHIR connection as unhealthy, alert practice admin
```

- [ ] Implement token cache with Redis (TTL = token expiry minus 60s buffer)
- [ ] Implement automatic token refresh on 401 response
- [ ] Implement retry logic: refresh token and retry request once on 401
- [ ] Implement circuit breaker: after 3 consecutive auth failures, pause FHIR sync for 1 hour
- [ ] Alert practice admin via email when FHIR connection is unhealthy
- [ ] Log all token refresh events in audit trail

## 15.6 Error Handling and Retry Strategy

### 15.6.1 FHIR Error Handling Matrix
| HTTP Status | Error Type | Action |
|-------------|-----------|--------|
| 200 | Success | Process response |
| 401 | Token expired | Refresh token, retry once |
| 403 | Scope insufficient | Log error, alert admin, skip resource |
| 404 | Resource not found | Log warning, return empty result |
| 429 | Rate limited | Respect Retry-After header, back off |
| 500 | Server error | Retry with exponential backoff (3 attempts) |
| 502/503 | Server unavailable | Retry with exponential backoff (3 attempts) |
| Timeout | Network timeout | Retry once, then fail gracefully |
| OperationOutcome | FHIR error | Parse issue details, log, skip or retry based on severity |

### 15.6.2 Retry Configuration
```python
FHIR_RETRY_CONFIG = {
    'max_retries': 3,
    'base_delay': 1.0,     # 1 second
    'max_delay': 60.0,     # 60 seconds
    'backoff_factor': 2.0, # exponential: 1s, 2s, 4s
    'retry_statuses': [429, 500, 502, 503],
    'timeout': 30,         # 30 second request timeout
}
```

- [ ] Implement exponential backoff with jitter for FHIR API retries
- [ ] Respect `Retry-After` header from 429 responses
- [ ] Circuit breaker: open after 5 consecutive failures per practice per resource type
- [ ] Circuit breaker reset: half-open after 5 minutes, close on success
- [ ] Per-practice rate limit tracking in Redis to avoid hitting EHR limits
- [ ] Graceful degradation: if a resource type consistently fails, disable it and alert admin
---

# 16. Customer Success Framework

## 16.1 Onboarding Journey
1. **Day 0 â€” Signup:** Account creation, practice profile
2. **Day 1 â€” Setup Call:** 60-minute guided FHIR setup + team training
3. **Day 3 â€” Data Sync:** Verify patient roster sync complete, check data quality
4. **Day 7 â€” First Check-in:** Review billing opportunities detected, answer questions
5. **Day 14 â€” Optimization:** Adjust detector settings, review dismissed opportunities
6. **Day 21 â€” ROI Review:** Calculate captured revenue vs subscription cost
7. **Day 30 â€” Trial End:** Convert or extend trial (case-by-case)

## 16.2 Health Score
| Metric | Weight | Healthy | At Risk | Churning |
|--------|--------|---------|---------|----------|
| Daily active users | 25% | >50% of seats | 25-50% | <25% |
| Opportunities captured/week | 25% | >20 | 5-20 | <5 |
| Care gaps resolved/month | 20% | >10 | 3-10 | <3 |
| Support tickets (negative) | 15% | 0-1/month | 2-4/month | 5+/month |
| Login frequency | 15% | Daily | Weekly | Monthly or less |

## 16.3 Churn Prevention
- Health score < 50 â†’ automated CSM alert + outreach within 48 hours
- No login for 7 days â†’ automated email: "Did you know you missed X billing opportunities?"
- Payment failure â†’ 3-day grace, email reminder, CSM call
- Cancellation request â†’ offer: 1 month free, training session, plan downgrade

---

# 17. Competitive Intelligence

## 17.1 Competitor Matrix

| Feature | CareCompanion | Athenahealth | Elation | Aledade | Phreesia |
|---------|---------------|--------------|---------|---------|----------|
| Billing capture engine | **25+ detectors** | Basic | Minimal | None | None |
| Care gap tracking | **USPSTF + custom** | Basic | Good | ACO-focused | Intake only |
| Visit stack builder | **Yes** | No | No | No | No |
| Code specificity | **Yes** | No | No | No | No |
| EHR-agnostic | **FHIR (any EHR)** | Athena only | Elation only | Any (ACO) | Any (intake) |
| Expected net value scoring | **8-factor model** | None | None | None | None |
| Target market | **1-10 providers** | All sizes | Primary care | Practices in ACOs | All sizes |
| Pricing | **$299-799/provider** | ~$140/provider + % | ~$300/provider | Revenue share | Per-patient |

## 17.2 Defensible Advantages
1. **Depth of billing intelligence:** 25+ detectors with 8-factor scoring is significantly deeper than any competitor
2. **Primary care specialization:** Purpose-built for primary care workflows, not a generic tool
3. **Closed-loop tracking:** End-to-end from detection â†’ submission â†’ adjudication â†’ payment
4. **EHR agnosticism:** FHIR-based, works with any EHR (not locked to one platform)
5. **Care gap + billing integration:** Unified view of quality and revenue opportunities

---

# 18. Financial Projections

## 18.1 Revenue Model

### Year 1 Projections
| Quarter | Practices | Providers | Avg Revenue/Provider | MRR | ARR |
|---------|-----------|-----------|----------------------|-----|-----|
| Q1 | 5 | 10 | $399 | $3,990 | $47,880 |
| Q2 | 15 | 35 | $399 | $13,965 | $167,580 |
| Q3 | 35 | 80 | $449 | $35,920 | $431,040 |
| Q4 | 60 | 150 | $449 | $67,350 | $808,200 |

### Year 2 Projections
| Quarter | Practices | Providers | Avg Revenue/Provider | MRR | ARR |
|---------|-----------|-----------|----------------------|-----|-----|
| Q1 | 80 | 200 | $449 | $89,800 | $1,077,600 |
| Q2 | 110 | 300 | $499 | $149,700 | $1,796,400 |
| Q3 | 140 | 400 | $499 | $199,600 | $2,395,200 |
| Q4 | 170 | 500 | $499 | $249,500 | $2,994,000 |

## 18.2 Cost Structure

### Monthly Operating Costs (at 100 providers)
| Category | Monthly Cost |
|----------|-------------|
| AWS Infrastructure | $2,500 |
| Stripe fees (2.9% + 30Â¢) | ~$1,300 |
| SendGrid | $90 |
| Sentry | $80 |
| Domain + SSL | $20 |
| Monitoring (Pingdom, etc.) | $50 |
| **Total Infrastructure** | **~$4,040** |

### Monthly Operating Costs (at 500 providers)
| Category | Monthly Cost |
|----------|-------------|
| AWS Infrastructure | $8,000 |
| Stripe fees | ~$7,200 |
| SendGrid | $300 |
| Sentry | $160 |
| Monitoring | $100 |
| **Total Infrastructure** | **~$15,760** |

## 18.3 Unit Economics
- **Customer Acquisition Cost (CAC):** Target $1,500-$3,000 per practice
- **Lifetime Value (LTV):** ~$15,000 (avg 30 months Ã— $499/provider Ã— 1 provider avg)
- **LTV:CAC ratio:** 5:1 to 10:1 (healthy SaaS benchmark: >3:1)
- **Gross margin:** ~85% (infrastructure costs are low relative to subscription revenue)
- **Payback period:** 3-6 months

---

# 19. Risk Register

## 19.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| FHIR API inconsistencies across EHRs | High | Medium | Adapter pattern, capability detection, graceful degradation |
| EHR rate limiting blocks data sync | Medium | High | Aggressive caching, incremental sync, off-peak scheduling |
| Database performance at scale | Low | High | PostgreSQL optimization, connection pooling, read replicas |
| Security breach / data leak | Low | Critical | HIPAA controls, encryption, audit logging, penetration testing |
| Dependence on third-party APIs | Medium | Medium | Caching, graceful degradation, multiple data source fallbacks |

## 19.2 Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Slow practice adoption | Medium | High | Free trial, ROI guarantee, founder-led sales |
| Competitor copying features | Medium | Medium | Speed of execution, depth of billing intelligence, relationships |
| Regulatory changes (CMS billing) | Medium | Medium | Modular rule engine, rapid update pipeline, medical advisory board |
| EHR vendors blocking FHIR access | Low | High | 21st Century Cures Act mandates FHIR access; regulatory leverage |
| Key person dependency | High | High | Document everything, hire 2nd engineer early, open-source components |

## 19.3 Compliance Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| HIPAA violation | Low | Critical | Technical safeguards, BAAs, annual risk assessment, training |
| OCR audit | Low | High | Complete HIPAA policy documentation, audit logs, encryption |
| State privacy law variations | Medium | Medium | Track state laws (CCPA, etc.), configurable data retention |

---

# 20. Intellectual Property & Licensing

## 20.1 Core IP
- **Billing detection algorithms:** 25+ detectors with proprietary logic for opportunity identification
- **8-factor expected net value scoring model:** Unique scoring combining collection rates, denial risk, documentation burden, time-to-cash, and bonus timing
- **Visit stack builder:** Template-based visit optimization with conflict resolution
- **Code specificity recommender:** Evidence-based ICD-10 upgrade recommendations
- **Care gap engine:** USPSTF rule evaluation with risk factor matching

## 20.2 Patent Considerations
- No patents filed currently; consider provisional patents for:
  - 8-factor billing opportunity scoring method
  - Real-time visit stack optimization algorithm
  - Automated care gap detection from FHIR data sources

## 20.3 Licensing
- **Application code:** Proprietary (all rights reserved)
- **Dependencies:** All open-source libraries are permissively licensed (MIT, BSD, Apache 2.0)
  - Flask (BSD), SQLAlchemy (MIT), Celery (BSD), fhirclient (Apache 2.0), Gunicorn (MIT)
- **CMS fee schedule data:** Public domain (US government work)
- **USPSTF guidelines:** Public domain (US government recommendations)
- **ICD-10 codes:** Licensed via CMS (free for internal use)
- **CPT codes:** Requires AMA license for commercial redistribution
  - [ ] Execute AMA CPT license agreement before launch
  - [ ] Budget: ~$500-$2,000/year for distribution license

## 20.4 Open Source Strategy
- **Do not open-source:** Billing detectors, scoring model, care gap engine, FHIR adapters
- **Consider open-sourcing:** Generic FHIR client library, utility functions, sample Celery tasks
- **Benefits:** Community goodwill, hiring signal, security audits
- **Risks:** Competitors forking; mitigated by keeping core algorithms proprietary


---

# 21. Regulatory & Compliance Roadmap

> Regulatory requirements beyond HIPAA for operating a healthcare SaaS platform.

## 21.1 Federal Regulations

### 21.1.1 21st Century Cures Act / Information Blocking
- [ ] Ensure CareCompanion does not engage in information blocking practices
- [ ] Support patient access to their data via FHIR (patient-facing API if requested)
- [ ] Document compliance with ONC's information blocking exceptions
- [ ] Monitor ONC rule updates for new FHIR requirements

### 21.1.2 CMS Interoperability Rules
- [ ] Support CMS-required FHIR endpoints (Patient Access API for payers)
- [ ] Monitor CMS Interoperability and Prior Authorization Final Rule (CMS-0057-F)
- [ ] Track changes in CMS Quality Payment Program (MIPS/APM) that affect billing
- [ ] Annual CMS fee schedule update (November) â€” update BillingRuleCache within 30 days

### 21.1.3 FDA Considerations
- [ ] CareCompanion is a **clinical decision support (CDS)** tool, not a medical device
- [ ] Verify exemption under 21st Century Cures Act Section 3060(a) â€” software meeting ALL 4 criteria:
  1. [ ] Not intended to acquire, process, or analyze a medical image/signal
  2. [ ] Intended for a healthcare professional (not patient-facing)
  3. [ ] Intended to enable the HCP to independently review the basis for recommendations
  4. [ ] Intended for use as a support tool, not as the sole basis for clinical decisions
- [ ] Document FDA exemption analysis
- [ ] If adding AI features: re-evaluate â€” ML-based clinical recommendations may cross into SaMD territory

### 21.1.4 OIG Anti-Kickback / Stark Law
- [ ] Performance-based pricing must not create improper referral incentives
- [ ] Revenue share model must be based on value delivered, not referral volume
- [ ] Consult healthcare attorney before finalizing performance-based pricing terms
- [ ] Document fair market value analysis for all pricing tiers

## 21.2 State Regulations

### 21.2.1 State Privacy Laws
- [ ] **California (CCPA/CPRA):** Health data carve-out for HIPAA-covered entities; verify compliance
- [ ] **Washington (My Health My Data Act):** Broad health data definition; may apply to non-HIPAA data
- [ ] **Colorado, Connecticut, Virginia, Utah:** Privacy acts with health data provisions
- [ ] Track new state laws via IAPP State Law Tracker
- [ ] Implement configurable data retention periods per state requirements

### 21.2.2 State Health IT Regulations
- [ ] Some states require registration for health IT platforms (e.g., Vermont)
- [ ] Track state-specific health IT vendor requirements
- [ ] Maintain state-by-state compliance matrix

## 21.3 Certifications & Audits

### 21.3.1 SOC 2 Type II
- [ ] Scope: Security, Availability, Confidentiality (Trust Service Criteria)
- [ ] Timeline: Begin SOC 2 readiness assessment at 50+ customers
- [ ] Audit firm: select at Month 6
- [ ] Type I completion: Month 9-12
- [ ] Type II completion: Month 15-18 (requires 6-month observation period)
- [ ] Annual renewal thereafter

### 21.3.2 HITRUST CSF (Optional â€” Enterprise Requirement)
- [ ] HITRUST certification may be required by large health systems
- [ ] Expensive (~$50K-$100K) and time-consuming (6-12 months)
- [ ] Defer to Phase 3+ unless enterprise customer demands it
- [ ] SOC 2 + HIPAA compliance is sufficient for initial target market

### 21.3.3 ONC Health IT Certification (Optional)
- [ ] Not required for CDS tools, but may be advantageous for credibility
- [ ] Required for EHR vendors â€” CareCompanion is not an EHR
- [ ] Monitor ONC certification criteria updates for applicability

## 21.4 Compliance Calendar

| Month | Task |
|-------|------|
| January | Annual HIPAA risk assessment |
| February | Review/update BAAs with all vendors |
| March | CMS QPP rule review (MIPS changes) |
| April | Penetration test (annual) |
| May | SOC 2 readiness review |
| June | Employee HIPAA training (annual) |
| July | Disaster recovery test |
| August | Backup restore validation test |
| September | State privacy law review |
| October | Security policy review/update |
| November | CMS fee schedule update (billing rules) |
| December | Annual compliance report to board |


## 21.5 Vendor Compliance Assessment

### 21.5.1 Vendor Assessment Checklist (Before Onboarding Any Third-Party Service)
- [ ] Does the vendor handle PHI? If yes, BAA is required
- [ ] Does the vendor have SOC 2 Type II certification?
- [ ] Does the vendor support HIPAA compliance? (documented on their website)
- [ ] Does the vendor encrypt data at rest and in transit?
- [ ] What is the vendor's data retention and deletion policy?
- [ ] Does the vendor have an incident response plan?
- [ ] Does the vendor conduct regular penetration tests?
- [ ] Where is the vendor's data stored? (US-only for HIPAA compliance preference)
- [ ] Does the vendor have a breach notification process?
- [ ] What is the vendor's uptime SLA? (target: >= 99.9%)
- [ ] Can the vendor provide a security questionnaire response (SIG Lite or equivalent)?
- [ ] Does the vendor support SSO/SAML for admin access?

### 21.5.2 Current Vendor Compliance Status
| Vendor | PHI? | BAA Available | SOC 2 | HIPAA Compliant | Status |
|--------|------|---------------|-------|-----------------|--------|
| AWS | Yes | Yes (standard) | Yes | Yes | Approved |
| Stripe | Yes (minimal) | Yes (healthcare) | Yes | Yes | Approved |
| SendGrid/Twilio | No (no PHI in emails) | Yes | Yes | Yes | Approved |
| Sentry | Minimal (error traces may contain PHI) | In progress | Yes | Partial | Review needed |
| HAPI FHIR (self-hosted) | Yes (internal) | N/A (self-hosted) | N/A | N/A | N/A |
| PagerDuty | No | N/A | Yes | N/A | Approved |
| GitHub | No (code only) | N/A | Yes | N/A | Approved |

### 21.5.3 Vendor Review Cadence
- [ ] Annual vendor compliance review (every January)
- [ ] Review triggered on vendor security incident notification
- [ ] Review triggered on vendor terms of service change
- [ ] Document all vendor assessments in compliance folder

## 21.6 HIPAA Training Program

### 21.6.1 Employee Training Requirements
- [ ] All employees: annual HIPAA Privacy and Security training (mandatory)
- [ ] Developers: additional training on secure coding practices (OWASP Top 10)
- [ ] Customer-facing staff: additional training on handling PHI inquiries
- [ ] New hire: HIPAA training within 30 days of start date
- [ ] Training records: stored for 6 years per HIPAA retention requirements

### 21.6.2 Training Curriculum Outline
| Module | Duration | Topics | Audience |
|--------|----------|--------|----------|
| HIPAA Basics | 1 hour | Privacy vs Security Rules, PHI definition, minimum necessary standard | All |
| Security Safeguards | 1 hour | Technical safeguards, access control, encryption, audit controls | Developers |
| Breach Notification | 30 min | Breach definition, notification timeline, incident reporting | All |
| Secure Development | 2 hours | OWASP Top 10, injection prevention, auth/authz patterns, secret management | Developers |
| PHI in Code | 1 hour | Logging PHI (don't), test data (synthetic only), dev environments | Developers |
| Customer Communication | 30 min | What to say/not say about PHI, redirecting clinical questions | Support staff |

### 21.6.3 Training Completion Tracking
- [ ] Use LMS (Learning Management System) or simple spreadsheet for < 20 employees
- [ ] Require quiz completion (80% passing score) for each module
- [ ] Re-training required on quiz failure (within 14 days)
- [ ] Annual refresher training (shorter version for returning employees)

## 21.7 Documentation and Policy Templates

### 21.7.1 Required Policy Documents
- [ ] Information Security Policy (overarching framework)
- [ ] Access Control Policy (user provisioning, de-provisioning, password requirements)
- [ ] Acceptable Use Policy (employee device usage, data handling)
- [ ] Incident Response Plan (detection, containment, notification, recovery, lessons learned)
- [ ] Disaster Recovery Plan (RTO, RPO, backup procedures, failover procedures)
- [ ] Data Classification Policy (public, internal, confidential/PHI)
- [ ] Data Retention and Disposal Policy (retention periods, secure deletion)
- [ ] Encryption Policy (at-rest, in-transit, key management)
- [ ] Change Management Policy (code review, deployment procedures, rollback)
- [ ] Third-Party Risk Management Policy (vendor assessment, BAA requirements)
- [ ] Physical Security Policy (office access, device encryption, remote work)
- [ ] Workforce Sanctions Policy (consequences for HIPAA violations)

### 21.7.2 Policy Review Schedule
- [ ] All policies reviewed annually by Security Officer (designated role)
- [ ] Policies updated when significant infrastructure changes occur
- [ ] Policies updated when regulatory requirements change
- [ ] Version-controlled in Git (separate `compliance` repository)
- [ ] Policy acknowledgment: all employees sign annually
---

# 22. Team & Hiring Plan

## 22.1 Current Team
- **Founder/CTO:** Full-stack development, billing engine, clinical domain expertise

## 22.2 Hiring Roadmap

### Month 1-3 (Pre-Revenue)
| Role | Priority | Responsibility |
|------|----------|----------------|
| Backend Engineer (Senior) | P0 | FHIR integration, PostgreSQL migration, Celery |
| Frontend Engineer | P1 | React/Vue dashboard rebuild, responsive design |

### Month 4-6 (Early Revenue)
| Role | Priority | Responsibility |
|------|----------|----------------|
| Customer Success Manager | P0 | Onboarding, training, retention |
| DevOps / SRE | P1 | AWS infrastructure, CI/CD, monitoring |

### Month 7-12 (Growth)
| Role | Priority | Responsibility |
|------|----------|----------------|
| Sales Representative | P0 | Outbound sales, demo, conversion |
| Marketing (Content) | P1 | Blog, SEO, case studies, social media |
| QA Engineer | P2 | Test automation, regression, compliance testing |

### Year 2
| Role | Priority |
|------|----------|
| Additional Backend Engineer | P0 |
| Product Manager | P0 |
| Data Engineer / Analyst | P1 |
| Security Engineer | P1 |
| Additional CSM | P2 |

## 22.3 Key Hire Profile: Senior Backend Engineer
- **Required:** Python 3.10+, Flask or Django, SQLAlchemy, PostgreSQL, Docker
- **Preferred:** Healthcare experience, FHIR HL7, HIPAA, Celery/Redis
- **Nice-to-have:** AWS ECS/Fargate, Terraform, SMART on FHIR
- **Compensation range:** $140K-$180K + equity (0.5-2.0%)

---

# 23. Partnership Strategy

## 23.1 EHR Vendor Partnerships

### 23.1.1 Epic App Orchard
- [ ] Register as Epic developer partner
- [ ] Build SMART on FHIR app with launch context
- [ ] Submit for Epic App Orchard review/listing
- [ ] Estimated timeline: 3-6 months from submission to listing

### 23.1.2 Oracle Health (Cerner) App Gallery
- [ ] Register on Cerner Code Console
- [ ] Build integration, submit for review
- [ ] Estimated timeline: 2-4 months

### 23.1.3 Athena Marketplace
- [ ] Register as Athena API partner
- [ ] Build integration using Athena FHIR + athenaPractice APIs
- [ ] Submit for marketplace listing
- [ ] Estimated timeline: 2-4 months

## 23.2 Channel Partnerships
- **Medical Billing Companies:** Refer clients who need billing optimization
- **Practice Management Consultants:** Recommend CareCompanion as part of practice improvement engagements
- **ACO/CIN Networks:** Care gap closure tool for network practices
- **Health IT Consultants:** Implementation partners for larger deployments

## 23.3 Partnership Terms
- **Referral fee:** 10% of first-year subscription value
- **Channel partner discount:** 15% off list price for partner-referred practices
- **Co-marketing:** Joint case studies, webinars, conference booth sharing

---

# 24. Success Metrics & KPIs

## 24.1 Product Metrics

| Metric | Target (Month 3) | Target (Month 12) |
|--------|-------------------|--------------------|
| Monthly Active Users (MAU) | 20 | 200 |
| Daily Active Users (DAU) | 10 | 100 |
| Billing opportunities detected/day | 50 | 500 |
| Billing opportunities captured/day | 30 | 300 |
| Care gaps resolved/month | 20 | 200 |
| Average session duration | 5 min | 8 min |
| Feature adoption rate | 40% | 70% |

## 24.2 Business Metrics

| Metric | Target (Month 3) | Target (Month 12) |
|--------|-------------------|--------------------|
| Practices (customers) | 5 | 60 |
| Provider seats | 10 | 150 |
| MRR | $3,990 | $67,350 |
| ARR | $47,880 | $808,200 |
| Churn rate (monthly) | <5% | <3% |
| NPS | >40 | >50 |
| CAC | <$3,000 | <$2,000 |
| LTV:CAC ratio | >4:1 | >6:1 |

## 24.3 Technical Metrics

| Metric | Target |
|--------|--------|
| Uptime | 99.9% |
| API response time (p95) | <500ms |
| Billing evaluation time | <500ms per patient |
| FHIR sync time (per patient) | <5s |
| Deployment frequency | 2x/week |
| Error rate | <0.1% |
| Security incidents | 0 |
| HIPAA audit findings | 0 |

---

# 25. 90-Day Launch Checklist

> Week-by-week checklist for the first 90 days of development, ending with beta launch.

## Weeks 1-2: Foundation
- [ ] Set up GitHub repository with branch protection
- [ ] Set up AWS account with HIPAA BAA
- [ ] Create Terraform modules for VPC, RDS, ElastiCache, ECS, S3
- [ ] Deploy staging environment
- [ ] Set up CI/CD pipeline (GitHub Actions â†’ ECR â†’ ECS)
- [ ] Create PostgreSQL schema with all models + `practice_id` columns
- [ ] Initialize Alembic with first migration
- [ ] Set up Sentry for error tracking
- [ ] Run first Docker build and deploy to staging

## Weeks 3-4: Database + Multi-Tenancy
- [ ] Write SQLite â†’ PostgreSQL ETL migration script
- [ ] Run migration for existing practice data
- [ ] Implement `Practice` model and `PracticeContextMiddleware`
- [ ] Add `practice_id` auto-filtering to all queries
- [ ] Write multi-tenancy isolation tests
- [ ] Remove all PyAutoGUI/Tesseract/desktop dependencies
- [ ] Replace APScheduler with Celery Beat (migrate 15 jobs)
- [ ] Verify all existing functionality works on PostgreSQL

## Weeks 5-6: FHIR Integration
- [ ] Create FHIR client library (`fhir/client.py`)
- [ ] Implement SMART on FHIR OAuth2 flow
- [ ] Create FHIR adapter for at least one EHR (start with Epic sandbox)
- [ ] Map all 13 FHIR resource types to internal patient_data dict
- [ ] Run billing engine with FHIR-sourced data â†’ verify same opportunities detected
- [ ] Run care gap engine with FHIR-sourced data â†’ verify same gaps identified
- [ ] Set up local HAPI FHIR server for dev/test
- [ ] Generate Synthea test patients

## Weeks 7-8: Subscription + Auth
- [ ] Integrate Stripe for subscription billing
- [ ] Implement signup flow with free trial
- [ ] Implement feature gating by subscription tier
- [ ] Add MFA support (TOTP)
- [ ] Implement password policies (complexity, rotation, lockout)
- [ ] Create FHIR setup wizard in admin
- [ ] Write HIPAA security policies (documented)

## Weeks 9-10: UI Polish + Testing
- [ ] Review and update all 23 MVP routes
- [ ] Ensure responsive design (work on tablet and desktop)
- [ ] Add WebSocket for real-time billing alerts
- [ ] Write comprehensive test suite: unit + integration + E2E
- [ ] Run OWASP ZAP scan for security vulnerabilities
- [ ] Run load test: simulate 100 concurrent users, 500 patients per practice
- [ ] Fix all critical and high-severity bugs

## Weeks 11-12: Beta Launch
- [ ] Deploy to production environment
- [ ] Run production smoke tests
- [ ] Final security review (encryption, access controls, audit logging)
- [ ] Onboard first 3-5 beta practices (hand-held setup)
- [ ] Monitor error rates and performance (Sentry + CloudWatch)
- [ ] Gather feedback daily from beta users
- [ ] Create status page at `status.carecompanion.health`
- [ ] Draft press release / public launch announcement

## Post-90-Day: Iterate
- [ ] Analyze beta feedback â†’ prioritize fixes and feature requests
- [ ] Calculate ROI for beta practices â†’ create case study
- [ ] Expand FHIR support to Cerner and Athena
- [ ] Begin SOC 2 readiness assessment
- [ ] Hire first Customer Success Manager
- [ ] Launch marketing website with pricing and ROI calculator
- [ ] Open self-service signup for general availability

---

# Appendix A â€” Technology Stack Reference

## A.1 Current Stack (Desktop)

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Language | Python | 3.11 | Primary language |
| Web Framework | Flask | 3.1.3 | HTTP server, routing, templates |
| ORM | SQLAlchemy | 2.0 | Database access |
| Database | SQLite | 3.x | Local data storage |
| Template Engine | Jinja2 | 3.x | HTML rendering |
| Auth | Flask-Login | 0.6.x | Session management |
| CSRF | Flask-WTF | 1.2.x | Form protection |
| Password Hashing | Flask-Bcrypt | 1.0.x | bcrypt hashing |
| Scheduler | APScheduler | 3.10.x | Background jobs |
| Screen Automation | PyAutoGUI | 0.9.x | Click/type/screenshot |
| OCR | Tesseract | 5.x | Screen text reading |
| Browser Automation | Playwright | 1.x | NetPractice scraping |
| XML Parsing | lxml | 4.x | CDA XML parsing |
| HTTP Client | requests | 2.x | API calls |
| Build | PyInstaller | 6.x | .exe packaging |

## A.2 Target Stack (Cloud SaaS)

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Language | Python | 3.11 | Primary language |
| Web Framework | Flask | 3.1.3 | HTTP server, routing, templates |
| WSGI Server | Gunicorn | 22.x | Production HTTP server |
| ORM | SQLAlchemy | 2.0 | Database access |
| Database | PostgreSQL | 15+ | Cloud data storage |
| Migration | Alembic | 1.13.x | Schema migrations |
| Task Queue | Celery | 5.4.x | Background job processing |
| Broker/Cache | Redis | 7.x | Celery broker + cache |
| Template Engine | Jinja2 | 3.x | HTML rendering |
| Auth | Flask-Login | 0.6.x | Session management |
| JWT | PyJWT | 2.x | API token auth |
| MFA | pyotp | 2.x | TOTP two-factor auth |
| CSRF | Flask-WTF | 1.2.x | Form protection |
| Password Hashing | Flask-Bcrypt | 1.0.x | bcrypt hashing |
| FHIR Client | fhirclient | 4.x | FHIR R4 API access |
| HTTP Client | requests | 2.x | API calls |
| Payments | stripe | 8.x | Subscription billing |
| Email | sendgrid | 6.x | Transactional email |
| Error Tracking | sentry-sdk[flask] | 2.x | Error monitoring |
| Logging | structlog | 24.x | Structured JSON logging |
| Containerization | Docker | 24+ | Application packaging |
| Orchestration | AWS ECS Fargate | â€” | Container orchestration |
| Load Balancer | AWS ALB | â€” | HTTPS termination, routing |
| Storage | AWS S3 | â€” | Document/backup storage |
| Secrets | AWS Secrets Manager | â€” | Sensitive config |
| Infrastructure | Terraform | 1.7+ | IaC provisioning |
| CI/CD | GitHub Actions | â€” | Build, test, deploy pipeline |
| Monitoring | CloudWatch + Sentry | â€” | Metrics + errors |
| Uptime | Pingdom / UptimeRobot | â€” | External health checks |

## A.3 Removed from Stack (Desktop-Only)

| Technology | Reason Removed |
|-----------|----------------|
| PyAutoGUI | Screen automation not needed; FHIR replaces |
| Tesseract OCR | Screen reading not needed; FHIR replaces |
| Playwright | NetPractice scraping â†’ direct API/FHIR |
| PyInstaller | No .exe packaging in cloud |
| APScheduler | Replaced by Celery Beat |
| lxml (CDA parsing) | CDA XML replaced by FHIR resources |

## A.4 Python Requirements (Cloud)
```
# requirements.txt (cloud version)
Flask==3.1.3
SQLAlchemy==2.0.36
Flask-Login==0.6.3
Flask-WTF==1.2.2
Flask-Bcrypt==1.0.1
gunicorn[gevent]==22.0.0
psycopg2-binary==2.9.9
alembic==1.13.3
celery[redis]==5.4.0
redis==5.1.1
fhirclient==4.2.0
requests==2.32.3
PyJWT==2.9.0
pyotp==2.9.0
stripe==8.11.0
sendgrid==6.11.0
sentry-sdk[flask]==2.14.0
structlog==24.4.0
python-dotenv==1.0.1
```

---

# Appendix B â€” FHIR Resource Quick Reference

## B.1 FHIR R4 Resources Used by CareCompanion

### Patient
```json
{
  "resourceType": "Patient",
  "id": "example-123",
  "identifier": [{"system": "urn:oid:2.16.840.1.113883.4.1", "value": "123456"}],
  "name": [{"family": "Smith", "given": ["John"]}],
  "gender": "male",
  "birthDate": "1965-04-23",
  "address": [{"city": "Richmond", "state": "VA", "postalCode": "23220"}]
}
```
**Used by:** Demographics, age calculations, care gap eligibility

### Condition
```json
{
  "resourceType": "Condition",
  "id": "condition-456",
  "clinicalStatus": {"coding": [{"code": "active"}]},
  "category": [{"coding": [{"code": "problem-list-item"}]}],
  "code": {
    "coding": [
      {"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": "E11.65", "display": "Type 2 diabetes with hyperglycemia"},
      {"system": "http://snomed.info/sct", "code": "44054006", "display": "Diabetes mellitus type 2"}
    ]
  },
  "subject": {"reference": "Patient/example-123"},
  "onsetDateTime": "2018-03-15"
}
```
**Used by:** Billing detectors (CCM chronic count, diagnosis-based triggers), care gap risk factors, code specificity

### Observation (Vital Signs)
```json
{
  "resourceType": "Observation",
  "id": "bp-789",
  "status": "final",
  "category": [{"coding": [{"code": "vital-signs"}]}],
  "code": {"coding": [{"system": "http://loinc.org", "code": "85354-9", "display": "Blood pressure panel"}]},
  "subject": {"reference": "Patient/example-123"},
  "effectiveDateTime": "2026-03-22T10:00:00Z",
  "component": [
    {
      "code": {"coding": [{"system": "http://loinc.org", "code": "8480-6", "display": "Systolic"}]},
      "valueQuantity": {"value": 138, "unit": "mmHg"}
    },
    {
      "code": {"coding": [{"system": "http://loinc.org", "code": "8462-4", "display": "Diastolic"}]},
      "valueQuantity": {"value": 88, "unit": "mmHg"}
    }
  ]
}
```
**Used by:** Hypertension screening, BMI calculation, obesity detector

### Observation (Laboratory)
```json
{
  "resourceType": "Observation",
  "id": "lab-101",
  "status": "final",
  "category": [{"coding": [{"code": "laboratory"}]}],
  "code": {"coding": [{"system": "http://loinc.org", "code": "4548-4", "display": "Hemoglobin A1c"}]},
  "subject": {"reference": "Patient/example-123"},
  "effectiveDateTime": "2026-02-15",
  "valueQuantity": {"value": 7.8, "unit": "%"},
  "referenceRange": [{"low": {"value": 4.0}, "high": {"value": 5.6}}]
}
```
**Used by:** Diabetes monitoring, code specificity (A1C > 7 â†’ upgrade), chronic monitoring detectors

### MedicationStatement
```json
{
  "resourceType": "MedicationStatement",
  "id": "med-201",
  "status": "active",
  "medicationCodeableConcept": {
    "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "860975", "display": "Metformin 500mg"}],
    "text": "Metformin 500mg tablet"
  },
  "subject": {"reference": "Patient/example-123"},
  "effectivePeriod": {"start": "2020-01-15"},
  "dosage": [{"text": "500mg twice daily"}]
}
```
**Used by:** Drug interaction checks, medication-based billing triggers, care gap medication matching

### AllergyIntolerance
```json
{
  "resourceType": "AllergyIntolerance",
  "id": "allergy-301",
  "clinicalStatus": {"coding": [{"code": "active"}]},
  "code": {"text": "Penicillin"},
  "patient": {"reference": "Patient/example-123"},
  "reaction": [{"manifestation": [{"text": "Hives"}], "severity": "moderate"}]
}
```
**Used by:** Drug safety checks, medication reference

### Immunization
```json
{
  "resourceType": "Immunization",
  "id": "imm-401",
  "status": "completed",
  "vaccineCode": {"coding": [{"system": "http://hl7.org/fhir/sid/cvx", "code": "141", "display": "Influenza, seasonal"}]},
  "patient": {"reference": "Patient/example-123"},
  "occurrenceDateTime": "2025-10-01"
}
```
**Used by:** Care gap engine (flu, pneumo, shingrix, tdap, covid vaccine gap detection)

### Encounter
```json
{
  "resourceType": "Encounter",
  "id": "enc-501",
  "status": "finished",
  "class": {"code": "AMB", "display": "ambulatory"},
  "type": [{"coding": [{"code": "99214", "display": "Office visit, established, moderate"}]}],
  "subject": {"reference": "Patient/example-123"},
  "period": {"start": "2026-03-22T09:00:00Z", "end": "2026-03-22T09:25:00Z"},
  "reasonCode": [{"text": "Diabetes follow-up"}]
}
```
**Used by:** Visit history, AWV detection (last AWV date), TCM (recent discharge), duration for prolonged services

### Coverage
```json
{
  "resourceType": "Coverage",
  "id": "cov-601",
  "status": "active",
  "type": {"coding": [{"code": "MEDICARE", "display": "Medicare"}]},
  "beneficiary": {"reference": "Patient/example-123"},
  "payor": [{"display": "Medicare Part B"}],
  "period": {"start": "2030-04-23"}
}
```
**Used by:** Payer routing (Medicare B vs MA vs Medicaid vs Commercial), G-code selection, modifier routing

## B.2 FHIR Code Systems

| System URI | Name | Used For |
|-----------|------|----------|
| `http://hl7.org/fhir/sid/icd-10-cm` | ICD-10-CM | Diagnosis codes |
| `http://www.ama-assn.org/go/cpt` | CPT | Procedure/billing codes |
| `http://loinc.org` | LOINC | Lab tests, vital signs, documents |
| `http://snomed.info/sct` | SNOMED CT | Clinical terms |
| `http://www.nlm.nih.gov/research/umls/rxnorm` | RxNorm | Medications |
| `http://hl7.org/fhir/sid/cvx` | CVX | Vaccine codes |
| `http://hl7.org/fhir/sid/ndc` | NDC | Drug package codes |
| `http://nucc.org/provider-taxonomy` | NUCC | Provider taxonomy |

## B.3 FHIR Search Parameters â€” Most Used

| Resource | Parameter | Example | Purpose |
|----------|-----------|---------|---------|
| Patient | `_id` | `Patient/123` | Direct lookup |
| Patient | `name` | `?name=Smith` | Patient search |
| Patient | `identifier` | `?identifier=MRN\|12345` | MRN lookup |
| Condition | `patient` | `?patient=123` | Patient's conditions |
| Condition | `clinical-status` | `?clinical-status=active` | Active only |
| Observation | `patient` + `category` | `?patient=123&category=vital-signs` | Vitals |
| Observation | `code` | `?code=http://loinc.org\|4548-4` | Specific lab (A1C) |
| Observation | `_sort` | `?_sort=-date` | Most recent first |
| Immunization | `patient` + `status` | `?patient=123&status=completed` | Completed vaccines |
| Encounter | `patient` + `date` | `?patient=123&date=ge2025-01-01` | Recent encounters |
| Coverage | `patient` + `status` | `?patient=123&status=active` | Active insurance |
| * | `_count` | `?_count=100` | Page size |
| * | `_lastUpdated` | `?_lastUpdated=gt2026-03-01` | Incremental sync |

---

# Appendix C â€” Glossary

| Term | Definition |
|------|-----------|
| **ACO** | Accountable Care Organization â€” provider group sharing financial risk |
| **ACP** | Advance Care Planning â€” CPT 99497/99498 |
| **ALB** | Application Load Balancer (AWS) |
| **APM** | Alternative Payment Model (CMS) |
| **AWV** | Annual Wellness Visit â€” G0402/G0438/G0439 |
| **BAA** | Business Associate Agreement (HIPAA) |
| **BHI** | Behavioral Health Integration â€” CPT 99492-99494 |
| **CCM** | Chronic Care Management â€” CPT 99490/99439/99487 |
| **CDA** | Clinical Document Architecture (HL7) |
| **CDS** | Clinical Decision Support |
| **CMS** | Centers for Medicare & Medicaid Services |
| **COCM** | Collaborative Care Management â€” psychiatric CPT codes |
| **CPT** | Current Procedural Terminology (AMA) |
| **CSRF** | Cross-Site Request Forgery |
| **CVX** | Vaccine Administered code set |
| **E/M** | Evaluation and Management (office visit codes) |
| **ECS** | Elastic Container Service (AWS) |
| **EHR** | Electronic Health Record |
| **ePHI** | Electronic Protected Health Information |
| **FHIR** | Fast Healthcare Interoperability Resources (HL7) |
| **G-code** | CMS-specific billing codes (e.g., G0438, G2211) |
| **HEDIS** | Healthcare Effectiveness Data and Information Set |
| **HIPAA** | Health Insurance Portability and Accountability Act |
| **HSTS** | HTTP Strict Transport Security |
| **ICD-10** | International Classification of Diseases, 10th Revision |
| **JWT** | JSON Web Token |
| **KMS** | Key Management Service (AWS) |
| **LOINC** | Logical Observation Identifiers Names and Codes |
| **MA** | Medical Assistant (role) or Medicare Advantage (payer) |
| **MIPS** | Merit-based Incentive Payment System |
| **MRN** | Medical Record Number |
| **MVP** | Minimum Viable Product |
| **NPI** | National Provider Identifier |
| **OIG** | Office of Inspector General (HHS) |
| **ONC** | Office of the National Coordinator for Health IT |
| **PCM** | Principal Care Management â€” CPT 99424/99425 |
| **PFS** | Physician Fee Schedule (CMS) |
| **PHI** | Protected Health Information |
| **PHQ-9** | Patient Health Questionnaire (depression screening) |
| **RDS** | Relational Database Service (AWS) |
| **RLS** | Row-Level Security (PostgreSQL) |
| **RPM** | Remote Patient Monitoring â€” CPT 99457/99458 |
| **RVU** | Relative Value Unit |
| **SaMD** | Software as a Medical Device |
| **SDOH** | Social Determinants of Health |
| **SMART** | Substitutable Medical Apps, Reusable Technologies (on FHIR) |
| **SNOMED** | Systematized Nomenclature of Medicine |
| **SOC 2** | Service Organization Control Type 2 (audit standard) |
| **TCM** | Transitional Care Management â€” CPT 99495/99496 |
| **TLS** | Transport Layer Security |
| **TOTP** | Time-based One-Time Password (MFA) |
| **USPSTF** | US Preventive Services Task Force |
| **VSAC** | Value Set Authority Center (NLM) |
| **WSGI** | Web Server Gateway Interface |
| **XSS** | Cross-Site Scripting |

---

*End of document. Total sections: 25 + 3 appendices.*
*Version 3.0 â€” Machine-Readable Checkbox Implementation Guide*
*Generated for CareCompanion SaaS Transformation*

