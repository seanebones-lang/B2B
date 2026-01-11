"""Tests for compliance module"""

import pytest
from unittest.mock import Mock, patch
from utils.compliance import ComplianceChecker


class TestComplianceChecker:
    """Test compliance checking functionality"""
    
    def test_init(self):
        """Test compliance checker initialization"""
        checker = ComplianceChecker()
        assert checker.robots_cache == {}
    
    def test_check_robots_txt_allowed(self):
        """Test robots.txt check when allowed"""
        checker = ComplianceChecker()
        
        # Mock RobotFileParser
        mock_rp = Mock()
        mock_rp.can_fetch.return_value = True
        
        with patch('urllib.robotparser.RobotFileParser', return_value=mock_rp):
            with patch.object(mock_rp, 'read'):
                result = checker.check_robots_txt('https://example.com/page', 'test-bot')
                assert result is True
    
    def test_check_robots_txt_disallowed(self):
        """Test robots.txt check when disallowed"""
        checker = ComplianceChecker()
        
        mock_rp = Mock()
        mock_rp.can_fetch.return_value = False
        
        with patch('urllib.robotparser.RobotFileParser', return_value=mock_rp):
            with patch.object(mock_rp, 'read'):
                result = checker.check_robots_txt('https://example.com/page', 'test-bot')
                assert result is False
    
    def test_check_robots_txt_error(self):
        """Test robots.txt check when error occurs"""
        checker = ComplianceChecker()
        
        with patch('urllib.robotparser.RobotFileParser') as mock_rp_class:
            mock_rp = Mock()
            mock_rp.read.side_effect = Exception("Network error")
            mock_rp_class.return_value = mock_rp
            
            # Should return True (allow by default) on error
            result = checker.check_robots_txt('https://example.com/page', 'test-bot')
            assert result is True
    
    def test_should_throttle(self):
        """Test throttling logic"""
        checker = ComplianceChecker()
        
        # Should throttle if request_count >= 1
        assert checker.should_throttle('example.com', 1) is True
        assert checker.should_throttle('example.com', 0) is False
        assert checker.should_throttle('example.com', 2) is True
    
    def test_log_compliance_violation(self):
        """Test compliance violation logging"""
        checker = ComplianceChecker()
        
        with patch('utils.logging.get_logger') as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log
            
            checker.log_compliance_violation('https://example.com', 'robots_txt', 'Test violation')
            
            mock_log.warning.assert_called_once()
