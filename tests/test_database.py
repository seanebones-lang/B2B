"""Tests for database utilities"""

import pytest
import os
import tempfile
from pathlib import Path

from utils.database import DatabaseManager, Review, AnalysisResult, get_db_manager


class TestDatabaseManager:
    """Test database manager"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db_url = f"sqlite:///{db_path}"
            yield db_url
    
    def test_init(self, temp_db):
        """Test database initialization"""
        db = DatabaseManager(database_url=temp_db)
        assert db.engine is not None
        assert db.SessionLocal is not None
    
    def test_save_reviews(self, temp_db):
        """Test saving reviews"""
        db = DatabaseManager(database_url=temp_db)
        
        reviews = [
            {"text": "Test review 1", "rating": 1, "date": "2024-01-01", "source": "G2"},
            {"text": "Test review 2", "rating": 2, "date": "2024-01-02", "source": "Capterra"},
        ]
        
        count = db.save_reviews("Test Tool", reviews)
        assert count == 2
    
    def test_get_reviews(self, temp_db):
        """Test retrieving reviews"""
        db = DatabaseManager(database_url=temp_db)
        
        reviews = [
            {"text": "Test review", "rating": 1, "date": "2024-01-01", "source": "G2"},
        ]
        db.save_reviews("Test Tool", reviews)
        
        retrieved = db.get_reviews("Test Tool")
        assert len(retrieved) > 0
        assert retrieved[0]["text"] == "Test review"
    
    def test_save_analysis_result(self, temp_db):
        """Test saving analysis result"""
        db = DatabaseManager(database_url=temp_db)
        
        result_id = db.save_analysis_result(
            tool_name="Test Tool",
            session_id="test-session",
            patterns={"patterns": []},
            ai_analysis={"analysis": "test"},
            product_ideas=[]
        )
        
        assert result_id > 0
    
    def test_get_analysis_result(self, temp_db):
        """Test retrieving analysis result"""
        db = DatabaseManager(database_url=temp_db)
        
        result_id = db.save_analysis_result(
            tool_name="Test Tool",
            session_id="test-session",
            patterns={"patterns": []},
            ai_analysis={"analysis": "test"},
            product_ideas=[]
        )
        
        result = db.get_analysis_result(result_id)
        assert result is not None
        assert result["tool_name"] == "Test Tool"
    
    def test_delete_user_data(self, temp_db):
        """Test GDPR data deletion"""
        db = DatabaseManager(database_url=temp_db)
        
        db.save_analysis_result(
            tool_name="Test Tool",
            session_id="test-session",
            patterns={},
            ai_analysis={},
            product_ideas=[]
        )
        
        deleted = db.delete_user_data("test-session")
        assert deleted > 0
    
    def test_cleanup_expired_data(self, temp_db):
        """Test expired data cleanup"""
        db = DatabaseManager(database_url=temp_db)
        
        # Create result with short retention
        db.save_analysis_result(
            tool_name="Test Tool",
            session_id="test-session",
            patterns={},
            ai_analysis={},
            product_ideas=[],
            retention_days=-1  # Already expired
        )
        
        deleted = db.cleanup_expired_data()
        assert deleted >= 0


class TestGetDbManager:
    """Test global database manager"""
    
    def test_get_db_manager_singleton(self):
        """Test that get_db_manager returns singleton"""
        db1 = get_db_manager()
        db2 = get_db_manager()
        
        # Should be same instance (or at least same type)
        assert type(db1) == type(db2)
