"""Security audit logging module"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import hashlib
import hmac

from utils.logging import get_logger

logger = get_logger(__name__)


class AuditLogger:
    """Security audit logging with tamper-proof storage"""
    
    def __init__(self, audit_log_dir: Optional[str] = None):
        """
        Initialize audit logger
        
        Args:
            audit_log_dir: Directory for audit logs (defaults to ./logs/audit)
        """
        self.audit_log_dir = Path(audit_log_dir or "./logs/audit")
        self.audit_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Get secret key for HMAC (tamper-proofing)
        self.secret_key = os.getenv("AUDIT_SECRET_KEY", "default-secret-change-in-production")
        
        logger.info("Audit logger initialized", log_dir=str(self.audit_log_dir))
    
    def _generate_hmac(self, data: str) -> str:
        """Generate HMAC for tamper-proofing"""
        return hmac.new(
            self.secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _write_audit_log(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        Write audit log entry with tamper-proofing
        
        Args:
            event_type: Type of audit event
            details: Event details
        """
        timestamp = datetime.utcnow().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "details": details
        }
        
        # Create tamper-proof log entry
        log_json = json.dumps(log_entry, sort_keys=True)
        hmac_signature = self._generate_hmac(log_json)
        
        tamper_proof_entry = {
            **log_entry,
            "hmac": hmac_signature
        }
        
        # Write to daily log file
        log_file = self.audit_log_dir / f"audit_{datetime.utcnow().date().isoformat()}.jsonl"
        
        with open(log_file, "a") as f:
            f.write(json.dumps(tamper_proof_entry) + "\n")
        
        # Also log to structured logger
        logger.info(
            "Audit event",
            event_type=event_type,
            details=details,
            timestamp=timestamp
        )
    
    def log_api_key_usage(self, api_key_hash: str, operation: str, success: bool) -> None:
        """Log API key usage"""
        self._write_audit_log(
            "api_key_usage",
            {
                "api_key_hash": api_key_hash,
                "operation": operation,
                "success": success
            }
        )
    
    def log_authentication_attempt(self, identifier: str, success: bool, reason: Optional[str] = None) -> None:
        """Log authentication attempt"""
        self._write_audit_log(
            "authentication_attempt",
            {
                "identifier": identifier,
                "success": success,
                "reason": reason
            }
        )
    
    def log_authorization_failure(self, identifier: str, resource: str, action: str) -> None:
        """Log authorization failure"""
        self._write_audit_log(
            "authorization_failure",
            {
                "identifier": identifier,
                "resource": resource,
                "action": action
            }
        )
    
    def log_input_validation_failure(self, input_type: str, value: str, reason: str) -> None:
        """Log input validation failure"""
        self._write_audit_log(
            "input_validation_failure",
            {
                "input_type": input_type,
                "value": value[:100],  # Truncate for security
                "reason": reason
            }
        )
    
    def log_security_threat(self, threat_type: str, details: Dict[str, Any]) -> None:
        """Log security threat detection"""
        self._write_audit_log(
            "security_threat",
            {
                "threat_type": threat_type,
                "details": details
            }
        )
    
    def log_rate_limit_violation(self, identifier: str, endpoint: str, limit: int) -> None:
        """Log rate limit violation"""
        self._write_audit_log(
            "rate_limit_violation",
            {
                "identifier": identifier,
                "endpoint": endpoint,
                "limit": limit
            }
        )
    
    def log_data_access(self, session_id: str, data_type: str, action: str, success: bool) -> None:
        """Log data access (GDPR compliance)"""
        self._write_audit_log(
            "data_access",
            {
                "session_id": session_id,
                "data_type": data_type,
                "action": action,
                "success": success
            }
        )
    
    def log_data_deletion(self, session_id: str, data_type: str, count: int) -> None:
        """Log data deletion (GDPR compliance)"""
        self._write_audit_log(
            "data_deletion",
            {
                "session_id": session_id,
                "data_type": data_type,
                "count": count
            }
        )
    
    def verify_log_integrity(self, log_file: Path) -> bool:
        """
        Verify audit log integrity (tamper detection)
        
        Args:
            log_file: Path to audit log file
            
        Returns:
            True if log is intact, False if tampered
        """
        if not log_file.exists():
            return False
        
        try:
            with open(log_file, "r") as f:
                for line in f:
                    entry = json.loads(line.strip())
                    
                    # Extract HMAC
                    stored_hmac = entry.pop("hmac", None)
                    if not stored_hmac:
                        return False
                    
                    # Recalculate HMAC
                    log_json = json.dumps(entry, sort_keys=True)
                    calculated_hmac = self._generate_hmac(log_json)
                    
                    # Compare HMACs
                    if not hmac.compare_digest(stored_hmac, calculated_hmac):
                        return False
            
            return True
        except Exception as e:
            logger.error("Error verifying log integrity", error=str(e))
            return False
    
    def query_audit_logs(
        self,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list:
        """
        Query audit logs
        
        Args:
            event_type: Filter by event type
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum number of results
            
        Returns:
            List of audit log entries
        """
        results = []
        
        # Get all audit log files in date range
        if start_date:
            start_file = self.audit_log_dir / f"audit_{start_date.date().isoformat()}.jsonl"
        else:
            start_file = None
        
        if end_date:
            end_file = self.audit_log_dir / f"audit_{end_date.date().isoformat()}.jsonl"
        else:
            end_file = None
        
        # Iterate through log files
        for log_file in sorted(self.audit_log_dir.glob("audit_*.jsonl")):
            if start_file and log_file < start_file:
                continue
            if end_file and log_file > end_file:
                continue
            
            try:
                with open(log_file, "r") as f:
                    for line in f:
                        entry = json.loads(line.strip())
                        
                        # Filter by event type
                        if event_type and entry.get("event_type") != event_type:
                            continue
                        
                        # Filter by date
                        entry_date = datetime.fromisoformat(entry.get("timestamp", ""))
                        if start_date and entry_date < start_date:
                            continue
                        if end_date and entry_date > end_date:
                            continue
                        
                        results.append(entry)
                        
                        if len(results) >= limit:
                            return results
            except Exception as e:
                logger.error("Error reading audit log", file=str(log_file), error=str(e))
        
        return results


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
