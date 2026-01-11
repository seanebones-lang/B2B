"""Tests for bias detection and explainability"""

import pytest

from utils.bias_detection import BiasDetector, ExplainabilityProvider, get_bias_detector, get_explainability_provider


class TestBiasDetector:
    """Test bias detection functionality"""
    
    def test_detect_gender_bias_masculine(self):
        """Test detection of masculine gender bias"""
        detector = BiasDetector()
        text = "This tool is aggressive and competitive, perfect for leaders"
        
        result = detector.detect_gender_bias(text)
        
        assert result["has_bias"] is True
        assert result["bias_type"] == "masculine"
        assert result["masculine_count"] > 0
    
    def test_detect_gender_bias_feminine(self):
        """Test detection of feminine gender bias"""
        detector = BiasDetector()
        text = "This tool is nurturing and supportive, great for collaborative teams"
        
        result = detector.detect_gender_bias(text)
        
        assert result["has_bias"] is True
        assert result["bias_type"] == "feminine"
        assert result["feminine_count"] > 0
    
    def test_detect_gender_bias_none(self):
        """Test no gender bias detected"""
        detector = BiasDetector()
        text = "This tool helps with data management"
        
        result = detector.detect_gender_bias(text)
        
        assert result["has_bias"] is False
        assert result["bias_type"] is None
    
    def test_detect_racial_bias(self):
        """Test detection of racial bias"""
        detector = BiasDetector()
        text = "This is a typical stereotypical solution for common users"
        
        result = detector.detect_racial_bias(text)
        
        assert result["has_bias"] is True
        assert result["bias_type"] == "racial"
    
    def test_detect_age_bias(self):
        """Test detection of age bias"""
        detector = BiasDetector()
        text = "Perfect for young fresh users, not for old veterans"
        
        result = detector.detect_age_bias(text)
        
        assert result["has_bias"] is True
        assert result["bias_type"] == "age"
    
    def test_analyze_bias_comprehensive(self):
        """Test comprehensive bias analysis"""
        detector = BiasDetector()
        text = "Aggressive competitive tool for young leaders"
        
        result = detector.analyze_bias(text)
        
        assert "has_bias" in result
        assert "gender_bias" in result
        assert "racial_bias" in result
        assert "age_bias" in result
    
    def test_analyze_ai_output(self):
        """Test bias analysis of AI output"""
        detector = BiasDetector()
        ai_output = {
            "product_ideas": [
                {
                    "pattern": "Test",
                    "ideas": [
                        {
                            "name": "Aggressive Tool",
                            "value_prop": "Competitive solution for leaders",
                            "target": "Aggressive users"
                        }
                    ]
                }
            ],
            "top_patterns": [
                {
                    "name": "Missing features",
                    "impact_reason": "Affects typical users"
                }
            ]
        }
        
        result = detector.analyze_ai_output(ai_output)
        
        assert "has_bias" in result
        assert "bias_detections" in result


class TestExplainabilityProvider:
    """Test explainability functionality"""
    
    def test_explain_pattern_selection(self):
        """Test pattern selection explanation"""
        provider = ExplainabilityProvider()
        
        patterns = [
            {"name": "Pattern 1", "frequency": 10},
            {"name": "Pattern 2", "frequency": 5},
        ]
        
        selected = [
            {"name": "Pattern 1", "frequency": 10, "impact_reason": "High impact"}
        ]
        
        explanation = provider.explain_pattern_selection(patterns, selected)
        
        assert explanation["total_patterns"] == 2
        assert explanation["selected_count"] == 1
        assert len(explanation["explanations"]) == 1
    
    def test_explain_product_idea(self):
        """Test product idea explanation"""
        provider = ExplainabilityProvider()
        
        idea = {
            "name": "Test Tool",
            "value_prop": "Solves problem X",
            "target": "Users needing X"
        }
        
        pattern = {"name": "Missing Feature X"}
        
        explanation = provider.explain_product_idea(idea, pattern)
        
        assert explanation["idea_name"] == "Test Tool"
        assert explanation["source_pattern"] == "Missing Feature X"
        assert "explanation" in explanation
    
    def test_generate_explainability_report(self):
        """Test explainability report generation"""
        provider = ExplainabilityProvider()
        
        analysis_results = {
            "pattern_results": {
                "patterns": [
                    {"name": "Pattern 1", "frequency": 10}
                ]
            },
            "ai_analysis": {
                "top_patterns": [
                    {"name": "Pattern 1", "frequency": 10, "impact_reason": "High impact"}
                ],
                "product_ideas": [
                    {
                        "pattern": "Pattern 1",
                        "ideas": [
                            {"name": "Idea 1", "value_prop": "Solution"}
                        ]
                    }
                ]
            }
        }
        
        report = provider.generate_explainability_report(analysis_results)
        
        assert "methodology" in report
        assert "pattern_selection" in report
        assert "idea_generation" in report
        assert "transparency_score" in report
        assert 0 <= report["transparency_score"] <= 1
    
    def test_get_bias_detector_singleton(self):
        """Test singleton pattern"""
        detector1 = get_bias_detector()
        detector2 = get_bias_detector()
        assert detector1 is detector2
    
    def test_get_explainability_provider_singleton(self):
        """Test singleton pattern"""
        provider1 = get_explainability_provider()
        provider2 = get_explainability_provider()
        assert provider1 is provider2
