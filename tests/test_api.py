"""Tests for REST API endpoints"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock

from api.rest import app, _analysis_tasks
from utils.security import SecurityManager
from utils.rate_limiter import RateLimiter

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check_no_auth(self):
        """Test health check without authentication"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data


class TestAuthentication:
    """Test API authentication"""
    
    def test_analyze_without_api_key(self):
        """Test analyze endpoint without API key"""
        response = client.post(
            "/api/v1/analyze",
            json={"tools": ["Salesforce"]}
        )
        assert response.status_code == 401
        assert "API key required" in response.json()["detail"]
    
    def test_analyze_with_invalid_api_key(self):
        """Test analyze endpoint with invalid API key"""
        response = client.post(
            "/api/v1/analyze",
            json={"tools": ["Salesforce"]},
            headers={"X-API-Key": "invalid"}
        )
        assert response.status_code == 401
        assert "Invalid API key format" in response.json()["detail"]
    
    def test_analyze_with_valid_api_key(self):
        """Test analyze endpoint with valid API key"""
        with patch('api.rest.InputValidator.validate_api_key', return_value=True):
            with patch('api.rest.XAIClient'):
                response = client.post(
                    "/api/v1/analyze",
                    json={"tools": ["Salesforce"]},
                    headers={"X-API-Key": "xai-valid-api-key-12345678901234567890"}
                )
                assert response.status_code == 200
                data = response.json()
                assert "analysis_id" in data
                assert data["status"] == "accepted"


class TestAnalyzeEndpoint:
    """Test analyze endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        _analysis_tasks.clear()
        yield
        _analysis_tasks.clear()
    
    def test_analyze_invalid_tools(self):
        """Test analyze with invalid tools"""
        with patch('api.rest.InputValidator.validate_api_key', return_value=True):
            response = client.post(
                "/api/v1/analyze",
                json={"tools": ["InvalidTool123!@#"]},
                headers={"X-API-Key": "xai-valid-api-key-12345678901234567890"}
            )
            assert response.status_code == 400
            assert "No valid tools provided" in response.json()["detail"]
    
    def test_analyze_empty_tools(self):
        """Test analyze with empty tools list"""
        with patch('api.rest.InputValidator.validate_api_key', return_value=True):
            response = client.post(
                "/api/v1/analyze",
                json={"tools": []},
                headers={"X-API-Key": "xai-valid-api-key-12345678901234567890"}
            )
            assert response.status_code == 422  # Validation error
    
    def test_analyze_too_many_tools(self):
        """Test analyze with too many tools"""
        with patch('api.rest.InputValidator.validate_api_key', return_value=True):
            response = client.post(
                "/api/v1/analyze",
                json={"tools": ["Tool1", "Tool2", "Tool3", "Tool4"]},
                headers={"X-API-Key": "xai-valid-api-key-12345678901234567890"}
            )
            assert response.status_code == 422  # Validation error


class TestResultsEndpoint:
    """Test results endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        _analysis_tasks.clear()
        yield
        _analysis_tasks.clear()
    
    def test_get_results_not_found(self):
        """Test getting results for non-existent analysis"""
        with patch('api.rest.InputValidator.validate_api_key', return_value=True):
            response = client.get(
                "/api/v1/results/non-existent-id",
                headers={"X-API-Key": "xai-valid-api-key-12345678901234567890"}
            )
            assert response.status_code == 404
            assert "Analysis not found" in response.json()["detail"]
    
    def test_get_results_pending(self):
        """Test getting results for pending analysis"""
        _analysis_tasks["test-id"] = {"status": "pending"}
        
        with patch('api.rest.InputValidator.validate_api_key', return_value=True):
            response = client.get(
                "/api/v1/results/test-id",
                headers={"X-API-Key": "xai-valid-api-key-12345678901234567890"}
            )
            assert response.status_code == 202
            assert "still in progress" in response.json()["detail"]
    
    def test_get_results_completed(self):
        """Test getting results for completed analysis"""
        _analysis_tasks["test-id"] = {
            "status": "completed",
            "results": {"Tool1": {"reviews": [], "pattern_results": {}, "ai_analysis": {}}},
        }
        
        with patch('api.rest.InputValidator.validate_api_key', return_value=True):
            response = client.get(
                "/api/v1/results/test-id",
                headers={"X-API-Key": "xai-valid-api-key-12345678901234567890"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "analysis_id" in data
            assert "tool_results" in data
            assert "top_opportunities" in data
    
    def test_get_results_failed(self):
        """Test getting results for failed analysis"""
        _analysis_tasks["test-id"] = {
            "status": "failed",
            "error": "Test error"
        }
        
        with patch('api.rest.InputValidator.validate_api_key', return_value=True):
            response = client.get(
                "/api/v1/results/test-id",
                headers={"X-API-Key": "xai-valid-api-key-12345678901234567890"}
            )
            assert response.status_code == 500
            assert "failed" in response.json()["detail"]


class TestToolsEndpoint:
    """Test tools endpoint"""
    
    def test_list_tools(self):
        """Test listing available tools"""
        with patch('api.rest.InputValidator.validate_api_key', return_value=True):
            response = client.get(
                "/api/v1/tools",
                headers={"X-API-Key": "xai-valid-api-key-12345678901234567890"}
            )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0
            assert "name" in data[0]
            assert "category" in data[0]


class TestRateLimiting:
    """Test rate limiting"""
    
    def test_rate_limit_exceeded(self):
        """Test rate limiting"""
        with patch('api.rest.InputValidator.validate_api_key', return_value=True):
            with patch('api.rest.rate_limiter.is_allowed', return_value=False):
                response = client.post(
                    "/api/v1/analyze",
                    json={"tools": ["Salesforce"]},
                    headers={"X-API-Key": "xai-valid-api-key-12345678901234567890"}
                )
                assert response.status_code == 429
                assert "Rate limit exceeded" in response.json()["detail"]


class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_json(self):
        """Test invalid JSON"""
        with patch('api.rest.InputValidator.validate_api_key', return_value=True):
            response = client.post(
                "/api/v1/analyze",
                data="invalid json",
                headers={
                    "X-API-Key": "xai-valid-api-key-12345678901234567890",
                    "Content-Type": "application/json"
                }
            )
            assert response.status_code == 422
    
    def test_missing_required_fields(self):
        """Test missing required fields"""
        with patch('api.rest.InputValidator.validate_api_key', return_value=True):
            response = client.post(
                "/api/v1/analyze",
                json={},
                headers={"X-API-Key": "xai-valid-api-key-12345678901234567890"}
            )
            assert response.status_code == 422
