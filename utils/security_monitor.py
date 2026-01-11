"""Security monitoring and threat detection"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import time

from utils.logging import get_logger
from utils.audit import get_audit_logger

logger = get_logger(__name__)
audit_logger = get_audit_logger()


class SecurityMonitor:
    """Monitor security events and detect threats"""
    
    def __init__(self):
        """Initialize security monitor"""
        self.event_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.threat_patterns: Dict[str, List[datetime]] = defaultdict(list)
        
        # Thresholds
        self.failed_auth_threshold = 5  # Failed auths per minute
        self.rate_limit_threshold = 10  # Rate limit violations per minute
        self.security_threat_threshold = 3  # Security threats per minute
        
        # Time windows
        self.window_minutes = 1
        
        logger.info("Security monitor initialized")
    
    def record_event(self, event_type: str, identifier: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Record a security event
        
        Args:
            event_type: Type of event (auth_failure, rate_limit, security_threat)
            identifier: Identifier (IP, API key, etc.)
            details: Additional event details
        """
        now = datetime.utcnow()
        key = f"{event_type}:{identifier}"
        
        # Clean old events
        self._clean_old_events(now)
        
        # Record event
        self.event_counts[event_type][identifier] += 1
        self.threat_patterns[key].append(now)
        
        logger.debug(
            "Security event recorded",
            event_type=event_type,
            identifier=identifier,
            count=self.event_counts[event_type][identifier]
        )
        
        # Check thresholds
        self._check_thresholds(event_type, identifier, now)
    
    def _clean_old_events(self, now: datetime) -> None:
        """Clean events older than time window"""
        cutoff = now - timedelta(minutes=self.window_minutes)
        
        for key in list(self.threat_patterns.keys()):
            self.threat_patterns[key] = [
                ts for ts in self.threat_patterns[key] if ts > cutoff
            ]
            
            if not self.threat_patterns[key]:
                del self.threat_patterns[key]
    
    def _check_thresholds(self, event_type: str, identifier: str, now: datetime) -> None:
        """Check if thresholds are exceeded"""
        count = len(self.threat_patterns.get(f"{event_type}:{identifier}", []))
        
        if event_type == "auth_failure" and count >= self.failed_auth_threshold:
            self._alert("failed_auth_threshold", identifier, count)
        
        elif event_type == "rate_limit" and count >= self.rate_limit_threshold:
            self._alert("rate_limit_threshold", identifier, count)
        
        elif event_type == "security_threat" and count >= self.security_threat_threshold:
            self._alert("security_threat_threshold", identifier, count)
    
    def _alert(self, alert_type: str, identifier: str, count: int) -> None:
        """Send security alert"""
        alert_message = f"Security alert: {alert_type} exceeded for {identifier} ({count} events)"
        
        logger.warning(
            "Security alert",
            alert_type=alert_type,
            identifier=identifier,
            count=count
        )
        
        audit_logger.log_security_threat(
            alert_type,
            {
                "identifier": identifier,
                "count": count,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def detect_anomaly(self, event_type: str, identifier: str) -> bool:
        """
        Detect anomalies in event patterns
        
        Args:
            event_type: Type of event
            identifier: Identifier
            
        Returns:
            True if anomaly detected
        """
        key = f"{event_type}:{identifier}"
        events = self.threat_patterns.get(key, [])
        
        if len(events) < 3:
            return False
        
        # Check for rapid-fire events (potential attack)
        if len(events) >= 3:
            time_diffs = [
                (events[i+1] - events[i]).total_seconds()
                for i in range(len(events) - 1)
            ]
            
            # If events are happening very quickly (< 1 second apart)
            if any(diff < 1.0 for diff in time_diffs):
                self._alert("anomaly_detected", identifier, len(events))
                return True
        
        return False
    
    def get_threat_summary(self) -> Dict[str, Any]:
        """Get summary of current threats"""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=self.window_minutes)
        
        summary = {
            "timestamp": now.isoformat(),
            "failed_auths": {},
            "rate_limit_violations": {},
            "security_threats": {},
            "anomalies": []
        }
        
        # Count events in time window
        for key, timestamps in self.threat_patterns.items():
            recent = [ts for ts in timestamps if ts > cutoff]
            if not recent:
                continue
            
            event_type, identifier = key.split(":", 1)
            count = len(recent)
            
            if event_type == "auth_failure":
                summary["failed_auths"][identifier] = count
            elif event_type == "rate_limit":
                summary["rate_limit_violations"][identifier] = count
            elif event_type == "security_threat":
                summary["security_threats"][identifier] = count
        
        return summary


# Global security monitor instance
_security_monitor: Optional[SecurityMonitor] = None


def get_security_monitor() -> SecurityMonitor:
    """Get global security monitor instance"""
    global _security_monitor
    if _security_monitor is None:
        _security_monitor = SecurityMonitor()
    return _security_monitor
