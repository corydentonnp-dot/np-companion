"""Utilities for scrubbing PHI from logs and free-text messages."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

# Demo MRNs are intentionally not scrubbed.
DEMO_MRNS = {str(i) for i in range(90001, 90036)}

# Core PHI patterns used for inline sanitization and file auditing.
MRN_RE = re.compile(r"\b\d{5,10}\b")
DOB_RE = re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b")
PHONE_RE = re.compile(r"(?:\(\d{3}\)\s*\d{3}-\d{4}|\b\d{3}-\d{3}-\d{4}\b)")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def hash_mrn(mrn: str) -> str:
    """Return first 12 chars of SHA-256 digest for an MRN-like string."""
    value = (mrn or "").strip()
    return hashlib.sha256(value.encode()).hexdigest()[:12]


def redact_patient_name(name: str) -> str:
    """Replace any patient name with a stable redaction token."""
    return "[REDACTED]"


def _replace_mrn(match: re.Match[str]) -> str:
    value = match.group(0)
    if value in DEMO_MRNS:
        return value
    return hash_mrn(value)


def sanitize_log_message(msg: str) -> str:
    """Scrub MRNs, DOB, phone, and SSN patterns from text messages."""
    text = msg or ""
    text = MRN_RE.sub(_replace_mrn, text)
    text = DOB_RE.sub("[DOB]", text)
    text = PHONE_RE.sub("[PHONE]", text)
    text = SSN_RE.sub("[SSN]", text)
    return text


def audit_log_for_phi(log_path: str) -> list[dict]:
    """Scan a log file and return structured findings for PHI-like patterns."""
    findings: list[dict] = []
    path = Path(log_path)
    if not path.exists():
        return findings

    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        for match in MRN_RE.finditer(line):
            value = match.group(0)
            if value in DEMO_MRNS:
                continue
            findings.append({"type": "mrn", "line_number": line_number, "match": value})

        for match in DOB_RE.finditer(line):
            findings.append({"type": "dob", "line_number": line_number, "match": match.group(0)})

        for match in PHONE_RE.finditer(line):
            findings.append({"type": "phone", "line_number": line_number, "match": match.group(0)})

        for match in SSN_RE.finditer(line):
            findings.append({"type": "ssn", "line_number": line_number, "match": match.group(0)})

    return findings
