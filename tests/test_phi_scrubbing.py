"""
CareCompanion -- PHI Scrubbing Tests (TDD)
tests/test_phi_scrubbing.py

These tests define the SPEC for a PHI scrubbing module that DOES NOT YET EXIST.
They will fail until utils/phi_scrubber.py is implemented (BUG-001).

The module should provide:
  - hash_mrn(mrn: str) -> str          — SHA-256 first 12 chars
  - redact_patient_name(name: str) -> str  — replace with [REDACTED]
  - sanitize_log_message(msg: str) -> str  — strip PHI patterns
  - audit_log_for_phi(log_path: str) -> list[dict]  — scan log for PHI leaks

Usage:
    venv\\Scripts\\python.exe -m pytest tests/test_phi_scrubbing.py -v
"""

import pytest
import hashlib


# ======================================================================
# Helper — expected hash for test MRN
# ======================================================================

def _expected_hash(mrn: str) -> str:
    """What hash_mrn should produce: SHA-256 hex digest, first 12 chars."""
    return hashlib.sha256(mrn.encode()).hexdigest()[:12]


# ======================================================================
# hash_mrn
# ======================================================================

class TestHashMRN:
    """hash_mrn() should produce a consistent, non-reversible identifier."""

    def test_import_exists(self):
        """utils.phi_scrubber module exists and hash_mrn is importable."""
        from utils.phi_scrubber import hash_mrn
        assert callable(hash_mrn)

    def test_returns_12_char_hex(self):
        """hash_mrn returns exactly 12 hex characters."""
        from utils.phi_scrubber import hash_mrn
        result = hash_mrn("62815")
        assert len(result) == 12
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic(self):
        """Same MRN always produces the same hash."""
        from utils.phi_scrubber import hash_mrn
        a = hash_mrn("62815")
        b = hash_mrn("62815")
        assert a == b

    def test_matches_sha256_spec(self):
        """Output matches SHA-256 first 12 chars per HIPAA rules."""
        from utils.phi_scrubber import hash_mrn
        assert hash_mrn("62815") == _expected_hash("62815")

    def test_different_mrns_different_hashes(self):
        """Different MRNs produce different hashes."""
        from utils.phi_scrubber import hash_mrn
        assert hash_mrn("62815") != hash_mrn("90001")


# ======================================================================
# redact_patient_name
# ======================================================================

class TestRedactPatientName:
    """redact_patient_name() should replace any name with [REDACTED]."""

    def test_redacts_name(self):
        from utils.phi_scrubber import redact_patient_name
        assert redact_patient_name("John Smith") == "[REDACTED]"

    def test_redacts_last_first(self):
        from utils.phi_scrubber import redact_patient_name
        assert redact_patient_name("SMITH, JOHN") == "[REDACTED]"

    def test_empty_string(self):
        from utils.phi_scrubber import redact_patient_name
        assert redact_patient_name("") == "[REDACTED]"


# ======================================================================
# sanitize_log_message
# ======================================================================

class TestSanitizeLogMessage:
    """sanitize_log_message() should strip PHI patterns from log text."""

    def test_strips_mrn_pattern(self):
        """6-10 digit MRN patterns are replaced with hash."""
        from utils.phi_scrubber import sanitize_log_message
        msg = "Processing patient MRN 62815 for billing"
        result = sanitize_log_message(msg)
        assert "62815" not in result
        assert _expected_hash("62815") in result

    def test_strips_dob_pattern(self):
        """Date patterns like MM/DD/YYYY are redacted."""
        from utils.phi_scrubber import sanitize_log_message
        msg = "Patient DOB: 10/01/1980"
        result = sanitize_log_message(msg)
        assert "10/01/1980" not in result
        assert "[DOB]" in result

    def test_strips_phone_pattern(self):
        """Phone number patterns are redacted."""
        from utils.phi_scrubber import sanitize_log_message
        msg = "Contact: (555) 123-4567"
        result = sanitize_log_message(msg)
        assert "555" not in result
        assert "[PHONE]" in result

    def test_strips_ssn_pattern(self):
        """SSN patterns (###-##-####) are redacted."""
        from utils.phi_scrubber import sanitize_log_message
        msg = "SSN: 123-45-6789"
        result = sanitize_log_message(msg)
        assert "123-45-6789" not in result
        assert "[SSN]" in result

    def test_preserves_non_phi(self):
        """Non-PHI content passes through unchanged."""
        from utils.phi_scrubber import sanitize_log_message
        msg = "Billing engine evaluated 5 detectors"
        result = sanitize_log_message(msg)
        assert result == msg

    def test_demo_mrns_exempt(self):
        """Demo MRNs (90001-90035) and test MRN 62815 pass through."""
        from utils.phi_scrubber import sanitize_log_message
        msg = "Demo patient MRN 90001"
        result = sanitize_log_message(msg)
        # Demo MRNs should NOT be scrubbed (they are test data)
        assert "90001" in result


# ======================================================================
# audit_log_for_phi
# ======================================================================

class TestAuditLogForPHI:
    """audit_log_for_phi() should scan a log file and report PHI leaks."""

    def test_finds_mrn_in_log(self, tmp_path):
        from utils.phi_scrubber import audit_log_for_phi
        log_file = tmp_path / "test.log"
        log_file.write_text(
            "2026-01-15 INFO Processing patient 12345678\n"
            "2026-01-15 INFO Billing complete\n"
        )
        findings = audit_log_for_phi(str(log_file))
        assert len(findings) >= 1
        assert findings[0]["type"] == "mrn"
        assert findings[0]["line_number"] == 1

    def test_finds_dob_in_log(self, tmp_path):
        from utils.phi_scrubber import audit_log_for_phi
        log_file = tmp_path / "test.log"
        log_file.write_text("Patient born 03/15/1955\n")
        findings = audit_log_for_phi(str(log_file))
        assert any(f["type"] == "dob" for f in findings)

    def test_clean_log_returns_empty(self, tmp_path):
        from utils.phi_scrubber import audit_log_for_phi
        log_file = tmp_path / "test.log"
        log_file.write_text("INFO Billing engine started\nINFO 5 detectors loaded\n")
        findings = audit_log_for_phi(str(log_file))
        assert findings == []

    def test_ignores_demo_mrns(self, tmp_path):
        from utils.phi_scrubber import audit_log_for_phi
        log_file = tmp_path / "test.log"
        log_file.write_text("INFO Processing demo patient 90001\n")
        findings = audit_log_for_phi(str(log_file))
        assert findings == []
