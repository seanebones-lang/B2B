"""Bias detection and explainability utilities for AI analysis"""

from typing import Dict, List, Any, Optional
import re
from collections import Counter

from utils.logging import get_logger

logger = get_logger(__name__)


class BiasDetector:
    """Detect bias in AI-generated content"""
    
    # Bias indicators
    GENDER_BIAS_WORDS = {
        "masculine": ["aggressive", "assertive", "dominant", "competitive", "leader"],
        "feminine": ["nurturing", "supportive", "collaborative", "empathetic", "caring"]
    }
    
    RACIAL_BIAS_INDICATORS = [
        "stereotypical", "typical", "common", "usual"
    ]
    
    AGE_BIAS_INDICATORS = [
        "young", "old", "experienced", "fresh", "veteran", "newbie"
    ]
    
    def __init__(self):
        logger.info("Bias detector initialized")
    
    def detect_gender_bias(self, text: str) -> Dict[str, Any]:
        """
        Detect potential gender bias in text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with bias detection results
        """
        text_lower = text.lower()
        masculine_count = sum(
            text_lower.count(word) for word in self.GENDER_BIAS_WORDS["masculine"]
        )
        feminine_count = sum(
            text_lower.count(word) for word in self.GENDER_BIAS_WORDS["feminine"]
        )
        
        total_bias_words = masculine_count + feminine_count
        
        if total_bias_words == 0:
            return {
                "has_bias": False,
                "bias_type": None,
                "confidence": 0.0,
                "masculine_count": 0,
                "feminine_count": 0
            }
        
        # Calculate bias ratio
        masculine_ratio = masculine_count / total_bias_words
        feminine_ratio = feminine_count / total_bias_words
        
        # Bias detected if ratio is > 0.7 (70% of bias words are one gender)
        has_bias = max(masculine_ratio, feminine_ratio) > 0.7
        
        return {
            "has_bias": has_bias,
            "bias_type": "masculine" if masculine_ratio > feminine_ratio else "feminine" if has_bias else None,
            "confidence": max(masculine_ratio, feminine_ratio),
            "masculine_count": masculine_count,
            "feminine_count": feminine_count
        }
    
    def detect_racial_bias(self, text: str) -> Dict[str, Any]:
        """
        Detect potential racial bias in text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with bias detection results
        """
        text_lower = text.lower()
        indicator_count = sum(
            text_lower.count(indicator) for indicator in self.RACIAL_BIAS_INDICATORS
        )
        
        return {
            "has_bias": indicator_count > 2,
            "bias_type": "racial" if indicator_count > 2 else None,
            "confidence": min(indicator_count / 5.0, 1.0),
            "indicator_count": indicator_count
        }
    
    def detect_age_bias(self, text: str) -> Dict[str, Any]:
        """
        Detect potential age bias in text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with bias detection results
        """
        text_lower = text.lower()
        age_words = [word for word in self.AGE_BIAS_INDICATORS if word in text_lower]
        
        return {
            "has_bias": len(age_words) > 1,
            "bias_type": "age" if len(age_words) > 1 else None,
            "confidence": min(len(age_words) / 3.0, 1.0),
            "age_words_found": age_words
        }
    
    def analyze_bias(self, text: str) -> Dict[str, Any]:
        """
        Comprehensive bias analysis
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with comprehensive bias analysis
        """
        gender_bias = self.detect_gender_bias(text)
        racial_bias = self.detect_racial_bias(text)
        age_bias = self.detect_age_bias(text)
        
        has_any_bias = (
            gender_bias["has_bias"] or
            racial_bias["has_bias"] or
            age_bias["has_bias"]
        )
        
        return {
            "has_bias": has_any_bias,
            "gender_bias": gender_bias,
            "racial_bias": racial_bias,
            "age_bias": age_bias,
            "overall_confidence": max(
                gender_bias.get("confidence", 0),
                racial_bias.get("confidence", 0),
                age_bias.get("confidence", 0)
            )
        }
    
    def analyze_ai_output(self, ai_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze AI-generated output for bias
        
        Args:
            ai_output: AI analysis output dictionary
            
        Returns:
            Dictionary with bias analysis results
        """
        results = {}
        
        # Analyze product ideas
        if "product_ideas" in ai_output:
            for idea_group in ai_output["product_ideas"]:
                for idea in idea_group.get("ideas", []):
                    idea_text = f"{idea.get('name', '')} {idea.get('value_prop', '')} {idea.get('target', '')}"
                    bias_result = self.analyze_bias(idea_text)
                    if bias_result["has_bias"]:
                        results[idea.get("name", "Unknown")] = bias_result
        
        # Analyze patterns
        if "top_patterns" in ai_output:
            for pattern in ai_output["top_patterns"]:
                pattern_text = f"{pattern.get('name', '')} {pattern.get('impact_reason', '')}"
                bias_result = self.analyze_bias(pattern_text)
                if bias_result["has_bias"]:
                    results[pattern.get("name", "Unknown")] = bias_result
        
        return {
            "has_bias": len(results) > 0,
            "bias_detections": results,
            "total_checked": len(ai_output.get("product_ideas", [])) + len(ai_output.get("top_patterns", []))
        }


class ExplainabilityProvider:
    """Provide explainability for AI decisions"""
    
    def __init__(self):
        logger.info("Explainability provider initialized")
    
    def explain_pattern_selection(self, patterns: List[Dict[str, Any]], selected: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Explain why certain patterns were selected
        
        Args:
            patterns: All patterns found
            selected: Selected top patterns
            
        Returns:
            Explanation dictionary
        """
        explanations = []
        
        for pattern in selected:
            explanation = {
                "pattern": pattern.get("name", "Unknown"),
                "frequency": pattern.get("frequency", 0),
                "impact": pattern.get("impact_reason", "N/A"),
                "selection_reason": f"Selected due to high frequency ({pattern.get('frequency', 0)}) and impact on workflows"
            }
            explanations.append(explanation)
        
        return {
            "total_patterns": len(patterns),
            "selected_count": len(selected),
            "explanations": explanations,
            "selection_criteria": "Patterns selected based on frequency and impact on core workflows"
        }
    
    def explain_product_idea(self, idea: Dict[str, Any], source_pattern: Dict[str, Any]) -> Dict[str, Any]:
        """
        Explain how a product idea was generated
        
        Args:
            idea: Product idea dictionary
            source_pattern: Source pattern that generated the idea
            
        Returns:
            Explanation dictionary
        """
        return {
            "idea_name": idea.get("name", "Unknown"),
            "source_pattern": source_pattern.get("name", "Unknown"),
            "generation_reason": f"Idea generated to address pattern: {source_pattern.get('name', 'Unknown')}",
            "target_audience": idea.get("target", "N/A"),
            "value_proposition": idea.get("value_prop", "N/A"),
            "explanation": f"This product idea addresses the '{source_pattern.get('name', 'Unknown')}' complaint pattern by {idea.get('value_prop', 'providing a solution')}"
        }
    
    def generate_explainability_report(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive explainability report
        
        Args:
            analysis_results: Complete analysis results
            
        Returns:
            Explainability report
        """
        report = {
            "methodology": "Pattern extraction using keyword matching and ML clustering, followed by AI analysis",
            "pattern_selection": {},
            "idea_generation": {},
            "transparency_score": 0.0
        }
        
        # Explain pattern selection
        if "pattern_results" in analysis_results:
            patterns = analysis_results["pattern_results"].get("patterns", [])
            if "ai_analysis" in analysis_results:
                selected = analysis_results["ai_analysis"].get("top_patterns", [])
                report["pattern_selection"] = self.explain_pattern_selection(patterns, selected)
        
        # Explain idea generation
        if "ai_analysis" in analysis_results:
            ideas = analysis_results["ai_analysis"].get("product_ideas", [])
            idea_explanations = []
            
            for idea_group in ideas:
                pattern_name = idea_group.get("pattern", "Unknown")
                for idea in idea_group.get("ideas", []):
                    explanation = self.explain_product_idea(idea, {"name": pattern_name})
                    idea_explanations.append(explanation)
            
            report["idea_generation"] = {
                "total_ideas": sum(len(ig.get("ideas", [])) for ig in ideas),
                "explanations": idea_explanations
            }
        
        # Calculate transparency score (0-1)
        score = 0.0
        if report["pattern_selection"]:
            score += 0.4
        if report["idea_generation"]:
            score += 0.4
        if report["methodology"]:
            score += 0.2
        
        report["transparency_score"] = score
        
        return report


# Global instances
_bias_detector: Optional[BiasDetector] = None
_explainability_provider: Optional[ExplainabilityProvider] = None


def get_bias_detector() -> BiasDetector:
    """Get global bias detector instance"""
    global _bias_detector
    if _bias_detector is None:
        _bias_detector = BiasDetector()
    return _bias_detector


def get_explainability_provider() -> ExplainabilityProvider:
    """Get global explainability provider instance"""
    global _explainability_provider
    if _explainability_provider is None:
        _explainability_provider = ExplainabilityProvider()
    return _explainability_provider
