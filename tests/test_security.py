"""
Security-focused tests for Context Rollover Checkpoint Agent.
Tests path traversal protection, HMAC key generation, and input validation.
"""
import os
import sys
import tempfile
import pytest

sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.base import AuditTrail, PHIGuard, SecurityException
from context_rollover.compression import CheckpointCompressor


class TestAuditTrailSecurity:
    """Test HMAC audit trail security features."""

    def test_audit_trail_generates_random_key_when_no_secret_provided(self):
        """AuditTrail should generate a random key when no secret is provided."""
        import os
        # Ensure env var is not set
        original_key = os.environ.pop("AUDIT_SECRET_KEY", None)
        try:
            trail = AuditTrail()
            assert len(trail.secret_key) > 0
            # Key should be different each time
            trail2 = AuditTrail()
            assert trail.secret_key != trail2.secret_key
        finally:
            if original_key:
                os.environ["AUDIT_SECRET_KEY"] = original_key

    def test_audit_trail_uses_env_var_when_set(self):
        """AuditTrail should use AUDIT_SECRET_KEY env var when set."""
        os.environ["AUDIT_SECRET_KEY"] = "test-secret-key-12345"
        try:
            trail = AuditTrail()
            assert trail.secret_key == b"test-secret-key-12345"
        finally:
            del os.environ["AUDIT_SECRET_KEY"]

    def test_audit_trail_accepts_explicit_key(self):
        """AuditTrail should accept an explicit key parameter."""
        trail = AuditTrail(secret_key="my-explicit-key")
        assert trail.secret_key == b"my-explicit-key"

    def test_audit_trail_integrity_verification(self):
        """Audit trail should maintain cryptographic integrity."""
        trail = AuditTrail(secret_key="test-key")
        trail.log("actor1", "tier1", "EVENT_TYPE", {"data": "value1"})
        trail.log("actor2", "tier2", "EVENT_TYPE", {"data": "value2"})
        assert trail.verify_integrity() is True

    def test_audit_trail_detects_tampering(self):
        """Audit trail should detect tampered entries."""
        trail = AuditTrail(secret_key="test-key")
        trail.log("actor1", "tier1", "EVENT_TYPE", {"data": "value1"})
        trail.log("actor2", "tier2", "EVENT_TYPE", {"data": "value2"})
        # Tamper with the first entry
        if trail.logs:
            trail.logs[0]["current_hash"] = "TAMPERED_HASH"
        assert trail.verify_integrity() is False

    def test_audit_trail_detects_last_signature_tampering(self):
        trail = AuditTrail(secret_key="test-key")
        trail.log("actor1", "tier1", "EVENT_TYPE", {"data": "value1"})
        trail.logs[-1]["current_hash"] = "TAMPERED_HASH"
        assert trail.verify_integrity() is False

    def test_audit_trail_detects_metadata_tampering(self):
        trail = AuditTrail(secret_key="test-key")
        trail.log("actor1", "tier1", "EVENT_TYPE", {"data": "value1"})
        trail.logs[-1]["actor"] = "attacker"
        assert trail.verify_integrity() is False


class TestPathTraversalProtection:
    """Test path traversal prevention in file operations."""

    def test_save_checkpoint_rejects_path_traversal(self):
        """save_checkpoint should reject paths with '..' components."""
        compressor = CheckpointCompressor()
        with pytest.raises(ValueError, match="path traversal"):
            compressor.save_checkpoint({"data": "test"}, "../etc/passwd")

    def test_save_checkpoint_rejects_absolute_paths(self):
        """save_checkpoint should reject absolute paths."""
        compressor = CheckpointCompressor()
        with pytest.raises(ValueError, match="path traversal"):
            compressor.save_checkpoint({"data": "test"}, "/etc/passwd")

    def test_load_checkpoint_rejects_path_traversal(self):
        """load_checkpoint should reject paths with '..' components."""
        compressor = CheckpointCompressor()
        with pytest.raises(ValueError, match="path traversal"):
            compressor.load_checkpoint("../etc/passwd")

    def test_load_checkpoint_rejects_absolute_paths(self):
        """load_checkpoint should reject absolute paths."""
        compressor = CheckpointCompressor()
        with pytest.raises(ValueError, match="path traversal"):
            compressor.load_checkpoint("/etc/passwd")

    def test_load_checkpoint_file_not_found(self):
        """load_checkpoint should raise FileNotFoundError for missing files."""
        compressor = CheckpointCompressor()
        with pytest.raises(FileNotFoundError):
            compressor.load_checkpoint("nonexistent_file.json")

    def test_save_and_load_checkpoint_roundtrip(self):
        """save_checkpoint and load_checkpoint should roundtrip correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            compressor = CheckpointCompressor(compress_threshold=1, base_dir=tmpdir)
            filepath = os.path.join(tmpdir, "test_checkpoint")
            data = {"agent_id": "A1", "state": "active", "tokens": 1500}
            compressor.save_checkpoint(data, filepath)
            loaded = compressor.load_checkpoint(filepath + ".gz")
            assert loaded == data


class TestPHIGuard:
    """Test PHI outbound guard functionality."""

    def test_phi_guard_blocks_ssn(self):
        """PHI guard should block SSN patterns."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient SSN: 123-45-6789")

    def test_phi_guard_blocks_mrn(self):
        """PHI guard should block MRN patterns."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("MRN-12345678")

    def test_phi_guard_blocks_phone(self):
        """PHI guard should block phone number patterns."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Call patient at 555-123-4567")

    def test_phi_guard_blocks_email(self):
        """PHI guard should block email patterns."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Email: patient@example.com")

    def test_phi_guard_allows_safe_text(self):
        """PHI guard should allow safe text."""
        PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")
        PHIGuard.assert_no_phi("Task TASK-2026-001 completed successfully")

    def test_phi_guard_handles_empty_string(self):
        """PHI guard should handle empty strings."""
        PHIGuard.assert_no_phi("")

    def test_phi_guard_handles_none(self):
        """PHI guard should handle None."""
        PHIGuard.assert_no_phi(None)

    def test_phi_redaction(self):
        """PHI guard should redact sensitive data."""
        text = "Patient John Doe has MRN-12345678 and SSN 123-45-6789"
        redacted = PHIGuard.redact_phi(text)
        assert "John Doe" not in redacted
        assert "123-45-6789" not in redacted
        assert "MRN-12345678" not in redacted
        assert "[REDACTED_IDENTIFIER]" in redacted
