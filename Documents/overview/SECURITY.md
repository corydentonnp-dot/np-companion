# Security and Compliance Overview

**Application**: CareCompanion
**Version**: 1.1.2 (active development)
**Environment**: On-premises, single workstation
**Data Classification**: Contains workflows touching Protected Health Information (PHI)
**Last Updated**: March 19, 2026

---

## 1. Application Architecture and Data Boundaries

CareCompanion is a locally-hosted web application that runs entirely within
the practice's network perimeter. The application does not have an internet-
facing component. All data processing occurs on the provider's workstation
(FPA-D-NP-DENTON).

**Data flow summary:**

```
Amazing Charts EHR → FHIR XML Export (manual trigger) → Local processing
on workstation → Local SQLite database → Provider browser interface
```

Patient data never traverses outside the practice network at any point in
this flow. The only outbound network requests from the application are to
external reference APIs (NIH, FDA, CMS), and those requests contain
exclusively non-PHI parameters.

---

## 2. Protected Health Information (PHI) Handling

### What PHI the application touches

The application reads Clinical Summary XML exports from Amazing Charts.
These exports contain: patient demographics, problem lists, medication lists,
allergy lists, lab results, immunization records, and vital signs. This
constitutes PHI under HIPAA's definition.

### How PHI is stored locally

PHI-adjacent data is stored in a local SQLite database on the provider's
workstation. Patient identifiers are stored as SHA-256 hashes rather than
plain MRN values where used outside the active session context. The database
file is located at a path defined in the application configuration and is
not synced to any cloud service.

### PHI retention and deletion

Clinical Summary XML files are processed and then scheduled for automatic
deletion after 183 days. This is consistent with HIPAA minimum necessary
standards and the practice's record retention policies. The deletion schedule
is enforced by the application's background job scheduler (APScheduler cron
job, confirmed active as of 2026-03-19) and logged to the audit trail.

### What is transmitted externally

The following information may leave the workstation via API calls to
reference services:

- Drug names and RxNorm identifiers (to NIH NLM for drug information)
- ICD-10 diagnosis codes (to NIH clinical tables for code lookup)
- CPT/HCPCS billing codes (to CMS Physician Fee Schedule API)
- LOINC lab codes (to Regenstrief Institute LOINC API)
- ZIP code (to Open-Meteo for weather — no PHI involved)

**No patient names, dates of birth, MRN numbers, social security numbers,
or any other direct patient identifiers are ever transmitted to any external
service.**

---

## 3. Authentication and Access Control

### User roles

The application implements three role levels:

| Role | Access |
|---|---|
| Provider | Full access including confidential chart sections, billing, inbox, metrics |
| Admin | Practice management access, user CRUD, all modules |
| Medical Assistant (MA) | Dashboard, orders, care gaps, medical reference only |

### Session security

Sessions time out after configurable inactivity periods and require
re-authentication. All session tokens are stored server-side (Flask-Login
with server-side session management) and invalidated on logout.

### CSRF Protection

Flask-WTF is integrated and `CSRFProtect(app)` is initialized in the
application factory. The CSRF token is available to all templates via
`csrf_token()`. Template-wide rollout of `{{ csrf_token() }}` to all
POST forms is in progress (Phase 11.1).

### PIN Rate Limiting

The PIN verification endpoint (`/api/verify-pin`) implements brute-force
protection: after 5 consecutive failed PIN attempts per user, the account
is locked out for 5 minutes. The counter resets on correct PIN entry or
after the lockout period expires. Tracking uses an in-memory dictionary
with per-user timestamps.

### Password storage

Passwords are stored as bcrypt hashes via Flask-Bcrypt. Plain-text passwords
are never stored or logged at any point. All authentication events are
recorded to the audit log.

---

## 4. Encryption

### Data at rest

The local SQLite database is stored on the Windows 11 Pro workstation.
Windows 11 Pro supports BitLocker full-disk encryption — it is recommended
that the workstation have BitLocker enabled. The application relies on
operating system-level disk encryption for at-rest protection.

### Data in transit

All external API calls use HTTPS (TLS 1.2 minimum). Communication between
the provider's remote device and the workstation via Tailscale uses the
WireGuard protocol, which provides ChaCha20-Poly1305 encryption for all
traffic. The local web interface is served over HTTP on localhost — this is
appropriate for a locally-hosted single-workstation application where the
only remote access is via an already-encrypted Tailscale tunnel.

---

## 5. Remote Access via Tailscale

### What Tailscale is

Tailscale is a zero-configuration mesh VPN built on the WireGuard protocol.
It creates encrypted point-to-point connections between authorized devices
without requiring changes to firewall rules or network infrastructure.
WireGuard is the same protocol used in many enterprise VPN products and is
considered cryptographically modern (ChaCha20 encryption, Curve25519 key
exchange, BLAKE2 authentication).

### How it is configured

The Tailscale network for CareCompanion contains exactly two devices: the
provider's personal phone/laptop and the workstation running the application.
No other devices are authorized. Access is managed through the provider's
Tailscale account and can be revoked at any time. Tailscale does not route
all internet traffic through external servers — it creates a direct encrypted
tunnel between the two authorized devices only.

### Why Tailscale instead of traditional VPN

A traditional site-to-site VPN would require changes to the practice's
network infrastructure and IT configuration. Tailscale requires no network
infrastructure changes, creates no open inbound ports on the practice
network, and is simpler to audit and manage for a single-provider use case.

### IT review resources

- Tailscale security model: https://tailscale.com/security
- Tailscale architecture: https://tailscale.com/blog/how-tailscale-works

---

## 6. Dependency and Software Supply Chain

### Python dependencies

All Python dependencies are specified in `requirements.txt` with pinned
version numbers (41 packages). Dependencies are reviewed for known CVEs
before updates are applied to the production workstation.

### External API surface

The application's external API surface is limited to the services listed
in Section 2. No user-generated content is transmitted externally. All
API responses are validated before processing. Rate limits are respected
per each API's terms of service.

### No third-party data processors

The application does not use any third-party analytics, error tracking,
or telemetry services. No patient data or usage data is transmitted to
any service other than the reference APIs listed above.

---

## 7. Audit Trail

All access to patient-related data within the application is logged to a
local audit table (`AuditLog` model) with timestamp, user ID, action type,
and endpoint. The audit log is append-only and is available to administrators
through the application's admin interface. Authenticated requests are
automatically logged (excluding high-frequency API polling endpoints to
prevent log bloat).

---

## 8. Known Limitations and Accepted Risks

**No independent ONC certification**: CareCompanion is a workflow support
tool, not a certified EHR. It does not replace Amazing Charts for regulated
clinical documentation. All regulated clinical workflows (prescribing,
official clinical documentation, billing submission) continue to occur
within Amazing Charts, which maintains its own ONC certification.

**Single-workstation architecture**: The current implementation is designed
for single-workstation use. Multi-provider expansion is documented in
planning materials as a future consideration.

**Disk encryption dependency**: The security of locally stored data depends
on BitLocker being enabled on the workstation. If BitLocker is not currently
enabled, this should be addressed as part of the IT approval process.

**config.py contains credentials**: Application configuration including
database paths and service credentials are stored in `config.py`, which is
excluded from version control via `.gitignore`. As of Phase 11.3, all 10
sensitive values are wrapped with `os.getenv()` calls (development defaults
preserved as fallbacks). `config.example.py` documents all required
environment variable names without real values.

---

## 9. Reporting Security Concerns

If you identify a security concern with this application, please contact:

- **Primary**: Cory Denton, FNP (application developer)
- **Escalation**: Dr. Chawla, MD (supervising physician)

For urgent concerns that may represent an active data breach, follow the
practice's existing breach notification protocol and contact the Privacy
Officer immediately.

---

## 10. IT Review Access

The full source code is available for review. IT staff can be granted
read-only Collaborator access to the private GitHub repository upon request.
No write access is required for security review.

Key files for review:
- `README.md` — Project overview and data handling summary
- `SECURITY.md` — This document
- `.env.example` — Environment variable template (no real credentials)
- `config.py` — Not in repository (gitignored), contains machine-specific settings
- `requirements.txt` — All Python dependencies with pinned versions
- `init.prompt.md` — Full architecture and coding conventions
