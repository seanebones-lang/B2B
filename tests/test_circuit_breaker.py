"""Tests for circuit breaker implementation"""

import pytest
import time
from unittest.mock import Mock, patch

from utils.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    get_circuit_breaker,
    circuit_breaker
)


class TestCircuitBreaker:
    """Test circuit breaker functionality"""
    
    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state"""
        breaker = CircuitBreaker(failure_threshold=3, timeout=60)
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    def test_circuit_breaker_success(self):
        """Test successful call"""
        breaker = CircuitBreaker(failure_threshold=3, timeout=60)
        
        def success_func():
            return "success"
        
        result = breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    def test_circuit_breaker_failure(self):
        """Test failure handling"""
        breaker = CircuitBreaker(failure_threshold=3, timeout=60)
        
        def fail_func():
            raise ValueError("Test error")
        
        # Fail multiple times
        for i in range(3):
            try:
                breaker.call(fail_func)
            except ValueError:
                pass
        
        assert breaker.failure_count == 3
        assert breaker.state == CircuitState.OPEN
    
    def test_circuit_breaker_open_state(self):
        """Test circuit breaker in open state"""
        breaker = CircuitBreaker(failure_threshold=2, timeout=60)
        
        def fail_func():
            raise ValueError("Test error")
        
        # Trigger open state
        for i in range(2):
            try:
                breaker.call(fail_func)
            except ValueError:
                pass
        
        assert breaker.state == CircuitState.OPEN
        
        # Should raise exception when open
        with pytest.raises(Exception, match="Circuit breaker.*is OPEN"):
            breaker.call(fail_func)
    
    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery"""
        breaker = CircuitBreaker(
            failure_threshold=2,
            timeout=1,  # Short timeout for testing
            expected_exception=ValueError
        )
        
        def fail_func():
            raise ValueError("Test error")
        
        def success_func():
            return "success"
        
        # Trigger open state
        for i in range(2):
            try:
                breaker.call(fail_func)
            except ValueError:
                pass
        
        assert breaker.state == CircuitState.OPEN
        
        # Wait for timeout
        time.sleep(1.1)
        
        # First call should enter half-open
        result = breaker.call(success_func)
        assert breaker.state == CircuitState.HALF_OPEN
        assert result == "success"
        
        # Second success should close circuit
        result = breaker.call(success_func)
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    def test_circuit_breaker_reset(self):
        """Test manual reset"""
        breaker = CircuitBreaker(failure_threshold=2, timeout=60)
        
        def fail_func():
            raise ValueError("Test error")
        
        # Trigger open state
        for i in range(2):
            try:
                breaker.call(fail_func)
            except ValueError:
                pass
        
        assert breaker.state == CircuitState.OPEN
        
        # Reset
        breaker.reset()
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    def test_circuit_breaker_decorator(self):
        """Test circuit breaker decorator"""
        breaker_instance = get_circuit_breaker("test_decorator", failure_threshold=2)
        
        @circuit_breaker("test_decorator", failure_threshold=2, expected_exception=ValueError)
        def test_func():
            raise ValueError("Test error")
        
        # Should fail but not raise circuit breaker exception yet
        with pytest.raises(ValueError):
            test_func()
        
        # Second failure should open circuit
        with pytest.raises(ValueError):
            test_func()
        
        # Third call should raise circuit breaker exception
        with pytest.raises(Exception, match="Circuit breaker.*is OPEN"):
            test_func()
    
    def test_get_circuit_breaker_singleton(self):
        """Test circuit breaker singleton pattern"""
        breaker1 = get_circuit_breaker("singleton_test")
        breaker2 = get_circuit_breaker("singleton_test")
        
        assert breaker1 is breaker2
    
    def test_circuit_breaker_get_state(self):
        """Test getting circuit breaker state"""
        breaker = CircuitBreaker(name="state_test")
        
        state = breaker.get_state()
        
        assert "name" in state
        assert "state" in state
        assert "failure_count" in state
        assert state["name"] == "state_test"
        assert state["state"] == CircuitState.CLOSED.value
