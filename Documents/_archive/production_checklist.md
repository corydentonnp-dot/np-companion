# CareCompanion — Production Deployment Checklist

> Complete every item before the app handles real patient data.
> Tick each box as you go. If a step fails, STOP and resolve before continuing.

---

## 1. Environment & Security

- [ ] **DEBUG = False** in `config.py`
- [ ] **AC_MOCK_MODE = False** in `config.py`
- [ ] **SECRET_KEY** replaced with a cryptographically random key (≥32 chars); never reuse the dev default
- [ ] Sensitive values moved to **environment variables** (SECRET_KEY, SMTP_PASS, API keys, Pushover keys, AC credentials)
- [ ] `config.py` is listed in `.gitignore` and excluded from any shared/backup folder
- [ ] BitLocker (or equivalent full-disk encryption) enabled on the deployment machine
- [ ] Windows Firewall — allow inbound TCP 5000 only from trusted IPs, block all else
- [ ] Automatic Windows Update enabled

---

## 2. Machine & Display

- [ ] **Screen resolution** matches `SCREEN_RESOLUTION` in config (default 1920×1080)
- [ ] Tesseract OCR installed and `TESSERACT_PATH` resolves correctly (`tesseract --version` succeeds)
- [ ] Display scaling set to 100 % (125 %+ breaks OCR coordinates)
- [ ] Amazing Charts EHR installed and opens normally
- [ ] `AC_EXE_PATH`, `AC_DB_PATH`, `AC_IMPORTED_ITEMS_PATH` are reachable from the deployment PC
- [ ] Chrome installed with `--remote-debugging-port=9222` launch shortcut (for NetPractice scraper)

---

## 3. Database & Migrations

- [ ] SQLite database created at `data/carecompanion.db` (first run auto-creates)
- [ ] All `migrate_*.py` scripts have been applied (auto-run on startup via `_applied_migrations` table)
- [ ] Run `python -c "import sqlite3; c=sqlite3.connect('data/carecompanion.db'); print(c.execute('PRAGMA integrity_check').fetchone())"` → should print `('ok',)`
- [ ] `data/backups/` directory exists and nightly backup job is registered

---

## 4. User Accounts

- [ ] Admin account created via `/setup/onboarding` wizard
- [ ] Provider account(s) created and can log in
- [ ] Role assignments verified: admin can see all modules, provider sees permitted modules, MA sees restricted set
- [ ] Password strength acceptable (bcrypt hashed)

---

## 5. Notifications

- [ ] **Pushover** — `PUSHOVER_USER_KEY` and `PUSHOVER_API_TOKEN` set and tested (send a test push from Admin > Agent)
- [ ] **SMTP** — `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM` configured; send a test email
- [ ] Quiet hours configured (`NOTIFY_QUIET_HOURS_START` / `END`)
- [ ] End-of-day notification time suitable for the practice schedule

---

## 6. API Keys

- [ ] **OpenFDA** — `OPENFDA_API_KEY` set (increases rate limit from 40/min → 240/min)
- [ ] **UMLS** — `UMLS_API_KEY` set and approved (provides SNOMED CT, VSAC, RxNorm)
- [ ] **LOINC** — `LOINC_USERNAME` / `LOINC_PASSWORD` set (lab reference ranges)
- [ ] **PubMed** — `PUBMED_API_KEY` set (optional; increases rate limit)
- [ ] Drug Safety, Lab Interpretation, Guidelines, Formulary Gaps, Patient Education endpoints return 200 (run `python test.py` Section 7)

---

## 7. NetPractice / Amazing Charts

- [ ] `NETPRACTICE_URL` and `NETPRACTICE_CLIENT_NUMBER` configured
- [ ] Chrome CDP session alive — `/api/auth-status` shows green
- [ ] Schedule scraper pulls tomorrow's appointments successfully
- [ ] AC login credentials (`AC_LOGIN_USERNAME` / `AC_LOGIN_PASSWORD`) correct
- [ ] AC_MOCK_MODE confirmed **False** — agent reads live screen, not mock images

---

## 8. Agent Service

- [ ] Agent starts via `Start_CareCompanion.bat` or `python agent_service.py`
- [ ] `/api/agent-status` returns `{"status": "green"}` within 60 seconds
- [ ] All 16 scheduled jobs registered (heartbeat, mrn_reader, inbox_check, inbox_digest, callback_check, overdue_lab_check, xml_archive_cleanup, xml_poll, weekly_summary, monthly_billing, deactivation_check, delayed_message_sender, eod_check, drug_recall_scan, previsit_billing, daily_backup)
- [ ] Agent tray icon appears in system tray
- [ ] Admin > Agent dashboard shows uptime and recent heartbeats

---

## 9. Health & Logging

- [ ] `/api/health` returns `{"status": "ok", "db": "connected"}` (200)
- [ ] `data/logs/carecompanion.log` exists and contains JSON entries
- [ ] Log rotation set to daily with 7-day retention
- [ ] Error log captures 500 errors with traceback

---

## 10. Test Gate

- [ ] **`python test.py`** — all checks PASS (0 failures, 0 errors)
- [ ] Manual verification:
  1. Dashboard loads with today's date
  2. Timer starts and stops correctly
  3. Inbox shows current snapshot
  4. On-call note can be created and saved
  5. Orders page loads
  6. Med Ref search works (try "metformin")
  7. Lab Track shows recent labs
  8. Care Gaps page loads
  9. Metrics dashboard shows charts
  10. EOD checker runs and returns results
  11. Settings pages save preferences
  12. Admin pages accessible with admin account
  13. Patient chart page loads for a known MRN
  14. Messages compose and send
  15. Notifications page loads
  16. Commute briefing renders
  17. Macros and dot-phrases load
  18. Billing opportunities appear for scheduled patients
  19. Health check endpoint responds
  20. Agent status shows green
  21. Backup runs successfully overnight (check next day)
  22. Weekly summary email received on Friday

---

## 11. Go-Live

- [ ] Take a manual backup: copy `data/carecompanion.db` to a safe location before first real-data session
- [ ] Confirm `DEBUG = False` one final time
- [ ] Start the Flask server: `python app.py`
- [ ] Start the agent: `python agent_service.py` (or `Start_CareCompanion.bat`)
- [ ] Open browser to `http://localhost:5000` — verify login page loads
- [ ] Log in as admin — verify dashboard is empty/clean
- [ ] Begin first clinical session

---

*Checklist version: 1.0 — generated for CareCompanion v1.1.2*
