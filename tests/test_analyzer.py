"""Tests for analyzer modules"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict

from analyzer.pattern_extractor import PatternExtractor
from analyzer.xai_client import XAIClient


class TestPatternExtractor:
    """Test pattern extractor"""
    
    def test_init(self):
        """Test pattern extractor initialization"""
        extractor = PatternExtractor()
        assert extractor.keywords is not None
        assert extractor.min_mentions > 0
    
    def test_extract_patterns_empty(self):
        """Test pattern extraction with empty reviews"""
        extractor = PatternExtractor()
        result = extractor.extract_patterns([])
        
        assert result["patterns"] == []
        assert result["total_reviews"] == 0
        assert result["categorized_complaints"] is not None
    
    def test_extract_patterns_with_reviews(self):
        """Test pattern extraction with sample reviews"""
        reviews = [
            {"text": "This tool doesn't have the features I need", "rating": 1, "source": "G2"},
            {"text": "Missing critical functionality", "rating": 2, "source": "G2"},
            {"text": "I wish it could do more", "rating": 1, "source": "Capterra"},
            {"text": "Can't perform basic tasks", "rating": 2, "source": "G2"},
        ]
        
        extractor = PatternExtractor()
        result = extractor.extract_patterns(reviews)
        
        assert result["total_reviews"] == 4
        assert "patterns" in result
        assert "categorized_complaints" in result
    
    def test_categorize_complaints(self):
        """Test complaint categorization"""
        reviews = [
            {"text": "doesn't have the features", "rating": 1, "source": "G2"},
            {"text": "wish it could do more", "rating": 2, "source": "G2"},
            {"text": "can't perform tasks", "rating": 1, "source": "Capterra"},
        ]
        
        extractor = PatternExtractor()
        categorized = extractor._categorize_complaints(reviews)
        
        assert "missing_feature" in categorized
        assert "wish_desire" in categorized
        assert "cant_blocks" in categorized
    
    def test_cluster_patterns_small_dataset(self):
        """Test clustering with small dataset"""
        reviews = [
            {"text": "Test review one", "rating": 1, "source": "G2"},
            {"text": "Test review two", "rating": 2, "source": "G2"},
        ]
        
        extractor = PatternExtractor()
        patterns = extractor._cluster_patterns(reviews)
        
        # Should return empty or fallback for small datasets
        assert isinstance(patterns, list)
    
    def test_filter_by_frequency(self):
        """Test frequency filtering"""
        patterns = [
            {"frequency": 10, "description": "High frequency"},
            {"frequency": 2, "description": "Low frequency"},
            {"frequency": 5, "description": "Threshold"},
        ]
        
        extractor = PatternExtractor()
        filtered = extractor._filter_by_frequency(patterns, 20)
        
        # Should filter based on min_mentions or frequency threshold
        assert isinstance(filtered, list)


class TestXAIClient:
    """Test xAI client"""
    
    def test_init_valid_key(self):
        """Test initialization with valid API key"""
        with patch('analyzer.xai_client.OpenAI'):
            client = XAIClient("xai-test-key-12345678901234567890")
            assert client.model is not None
    
    def test_init_invalid_key(self):
        """Test initialization with invalid API key"""
        with pytest.raises(ValueError):
            XAIClient("short")
    
    @patch('analyzer.xai_client.OpenAI')
    def test_analyze_patterns_success(self, mock_openai):
        """Test successful pattern analysis"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"top_patterns": [{"name": "Test", "frequency": 5}]}'
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        client = XAIClient("xai-test-key-12345678901234567890")
        client.client = mock_client
        
        patterns = [{"description": "Test pattern", "frequency": 5}]
        reviews = [{"text": "Test review", "rating": 1}]
        
        result = client.analyze_patterns("Test Tool", patterns, reviews)
        
        assert "top_patterns" in result
    
    @patch('analyzer.xai_client.OpenAI')
    def test_analyze_patterns_empty(self, mock_openai):
        """Test pattern analysis with empty patterns"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        client = XAIClient("xai-test-key-12345678901234567890")
        client.client = mock_client
        
        result = client.analyze_patterns("Test Tool", [], [])
        
        assert result["top_patterns"] == []
    
    @patch('analyzer.xai_client.OpenAI')
    def test_generate_product_ideas(self, mock_openai):
        """Test product idea generation"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"ideas": [{"pattern": "Test", "ideas": []}]}'
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        client = XAIClient("xai-test-key-12345678901234567890")
        client.client = mock_client
        
        top_patterns = [{"name": "Test pattern", "frequency": 5}]
        ideas = client.generate_product_ideas("Test Tool", top_patterns)
        
        assert isinstance(ideas, list)
    
    @patch('analyzer.xai_client.OpenAI')
    def test_generate_roadmap(self, mock_openai):
        """Test roadmap generation"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"week1": {"goal": "Test", "tasks": []}}'
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        client = XAIClient("xai-test-key-12345678901234567890")
        client.client = mock_client
        
        idea = {"name": "Test Idea", "value_prop": "Test value"}
        roadmap = client.generate_roadmap(idea)
        
        assert "week1" in roadmap or "week2" in roadmap
