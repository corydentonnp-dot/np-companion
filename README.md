# NP Companion

A locally-hosted clinical workflow intelligence tool for Family Practice
Associates of Chesterfield, Virginia, developed by Cory Denton, FNP.

## What This Application Does

NP Companion runs on the provider's workstation and connects to the practice's
existing Amazing Charts EHR (v12.3.1) to surface clinical intelligence that
Amazing Charts does not provide natively. It does not replace Amazing Charts —
it enhances it by providing:

- **Pre-visit preparation**: Patient data analyzed and organized before the
  provider opens the chart, including care gaps, medication safety alerts,
  and relevant lab trends.
- **Billing opportunity detection**: Real-time identification of Medicare and
  Medicaid billing opportunities (CCM, AWV, TCM, G2211 add-on) based on
  patient diagnoses and visit type, using the CMS Physician Fee Schedule API.
- **Drug safety monitoring**: Daily checks against FDA recall data for
  medications in the patient panel; drug interaction analysis using NIH
  RxNorm data.
- **Clinical decision support**: USPSTF care gap recommendations via the
  AHRQ HealthFinder API, immunization gap detection via CDC schedules,
  and evidence-based guideline lookup via PubMed.
- **Note assistance**: Pre-populated note sections based on clinical data,
  with templates aligned to Amazing Charts' 16-section note format.

## How Patient Data Is Handled

This application is designed with HIPAA compliance as a foundational
requirement:

- **Patient data never leaves the practice network.** All processing happens
  locally on the provider's workstation.
- The application reads from Amazing Charts' Clinical Summary XML export
  (a FHIR-compatible CDA format). These export files are processed locally
  and auto-deleted after 183 days.
- **External APIs receive only non-PHI parameters** — drug names, ICD-10
  codes, CPT codes, LOINC codes. Patient identifiers are never transmitted
  to any external service.
- Patient data is stored in a local SQLite database on the provider's
  workstation only. MRN identifiers are hashed (SHA-256) where stored
  outside the active session context.

## Why It Runs Locally

Amazing Charts stores all patient data on the practice's local server at
192.168.2.51. Any tool that interacts with Amazing Charts must be on the
same local network. Running NP Companion on the provider's workstation
keeps all patient data within the practice network and eliminates any
external transmission pathway for PHI.

## Remote Access

The provider accesses the application from personal devices via Tailscale,
a zero-configuration VPN built on the WireGuard protocol. Tailscale creates
an encrypted peer-to-peer connection between the provider's authorized
devices and the workstation — traffic is not routed through external servers.
Only devices explicitly authorized by the provider are in the Tailscale
network. This is functionally equivalent to a site-to-site VPN but requires
no changes to the practice's network infrastructure.

## Technical Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask 3.1.3, SQLAlchemy 2.0.48, SQLite |
| Frontend | HTML + CSS custom properties + vanilla JavaScript (no frameworks) |
| EHR Integration | Amazing Charts v12.3.1 via FHIR Clinical Summary XML + PyAutoGUI/OCR |
| Scheduling System | NetPractice/WebPractice via Playwright browser automation |
| Background Agent | System tray service (pystray + APScheduler + watchdog) |
| External APIs | NIH NLM (RxNorm, LOINC, ICD-10, UMLS, MedlinePlus, PubMed), FDA OpenFDA, CMS PFS, AHRQ, CDC, Open-Meteo |
| Notifications | Pushover (encrypted push to provider's phone) |
| Remote Access | Tailscale VPN (WireGuard protocol) |
| Packaging | PyInstaller (single-folder .exe, deployed via USB zip) |

## Project Status

Version 1.1.2. CL23 Beta Readiness phases 0–5 complete (critical bugs,
data correctness, widget system, context menus, feature completions, UI
polish). Currently integrating the API intelligence layer (17+ external
clinical APIs). See `PROJECT_STATUS.md` for full build state.

## Approval and Oversight

This application was developed with the knowledge and approval of
Dr. Chawla, MD, supervising physician at Family Practice Associates
of Chesterfield. Development is overseen with awareness from practice
administration.

## Repository Structure

```
NP_Companion/
├── app.py                  ← Flask application entry point
├── config.py               ← Machine-specific settings (gitignored)
├── agent_service.py        ← Background agent (system tray)
├── build.py                ← PyInstaller build script
├── launcher.py             ← Production launcher
├── init.prompt.md          ← Master coding instructions
├── PROJECT_STATUS.md       ← Current build state
├── .env.example            ← Environment variable template
├── requirements.txt        ← Python dependencies (41 packages)
├── agent/                  ← Background automation modules
├── models/                 ← SQLAlchemy models (39+)
├── routes/                 ← Flask blueprints (16)
├── scrapers/               ← NetPractice Playwright scraper
├── templates/              ← Jinja2 HTML templates
├── static/                 ← CSS + JS + assets
├── utils/                  ← Shared utilities (API client, etc.)
├── tools/                  ← CLI tools
├── tests/                  ← Test files
└── Documents/              ← Planning docs, AC reference, guides
```

## Security

See `SECURITY.md` for a full security and compliance overview, including
data handling, access controls, encryption, and IT review information.
