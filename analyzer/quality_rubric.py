"""Quality rubric for scoring product ideas"""

from typing import Dict, Any, List, Optional
from utils.logging import get_logger

logger = get_logger(__name__)


class QualityRubric:
    """Rubric for scoring product ideas on multiple dimensions"""
    
    def __init__(self):
        """Initialize quality rubric"""
        self.dimensions = {
            'originality': {
                'weight': 0.25,
                'description': 'How original/novel is the idea?',
                'criteria': {
                    'high': 'Unique approach, no direct competitors',
                    'medium': 'Some differentiation, few competitors',
                    'low': 'Many similar solutions exist'
                }
            },
            'ethics': {
                'weight': 0.15,
                'description': 'Is the idea ethical and bias-free?',
                'criteria': {
                    'high': 'No ethical concerns, inclusive design',
                    'medium': 'Minor concerns, addressable',
                    'low': 'Potential ethical issues'
                }
            },
            'productivity_impact': {
                'weight': 0.30,
                'description': 'How much does it improve productivity?',
                'criteria': {
                    'high': 'Significant time/cost savings, high impact',
                    'medium': 'Moderate improvements',
                    'low': 'Minimal impact'
                }
            },
            'feasibility': {
                'weight': 0.20,
                'description': 'How feasible is it to build?',
                'criteria': {
                    'high': 'Solo founder can build MVP in 4 weeks',
                    'medium': 'Small team needed, 2-3 months',
                    'low': 'Requires significant resources'
                }
            },
            'market_potential': {
                'weight': 0.10,
                'description': 'What is the market potential?',
                'criteria': {
                    'high': 'Large addressable market, clear demand',
                    'medium': 'Moderate market size',
                    'low': 'Niche market, limited demand'
                }
            }
        }
        logger.info("Quality rubric initialized")
    
    def score_idea(
        self,
        idea: Dict[str, Any],
        novelty_score: Optional[int] = None,
        feasibility_score: Optional[int] = None,
        market_size_score: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Score an idea using the quality rubric
        
        Args:
            idea: Idea dictionary
            novelty_score: Novelty score from validation (1-10)
            feasibility_score: Feasibility score from AI (1-10)
            market_size_score: Market size score from AI (1-10)
            
        Returns:
            Dictionary with scores and overall rating
        """
        scores = {}
        
        # Originality (from novelty validation)
        if novelty_score is not None:
            scores['originality'] = novelty_score / 10.0
        else:
            scores['originality'] = 0.5  # Default if not validated
        
        # Ethics (check for bias indicators)
        ethics_score = self._score_ethics(idea)
        scores['ethics'] = ethics_score
        
        # Productivity impact (from value prop analysis)
        productivity_score = self._score_productivity_impact(idea)
        scores['productivity_impact'] = productivity_score
        
        # Feasibility (from AI score)
        if feasibility_score is not None:
            scores['feasibility'] = feasibility_score / 10.0
        else:
            scores['feasibility'] = 0.5
        
        # Market potential (from AI score)
        if market_size_score is not None:
            scores['market_potential'] = market_size_score / 10.0
        else:
            scores['market_potential'] = 0.5
        
        # Calculate weighted overall score
        overall_score = sum(
            scores[dim] * self.dimensions[dim]['weight']
            for dim in scores.keys()
        )
        
        # Determine rating
        if overall_score >= 0.8:
            rating = 'Excellent'
        elif overall_score >= 0.6:
            rating = 'Good'
        elif overall_score >= 0.4:
            rating = 'Fair'
        else:
            rating = 'Needs Improvement'
        
        return {
            'scores': scores,
            'overall_score': overall_score,
            'overall_rating': rating,
            'breakdown': {
                dim: {
                    'score': scores[dim],
                    'weight': self.dimensions[dim]['weight'],
                    'weighted_score': scores[dim] * self.dimensions[dim]['weight']
                }
                for dim in scores.keys()
            }
        }
    
    def _score_ethics(self, idea: Dict[str, Any]) -> float:
        """Score ethics dimension"""
        # Check for bias indicators in value prop and target
        value_prop = idea.get('value_prop', '').lower()
        target = idea.get('target', '').lower()
        
        # Positive indicators
        positive_keywords = ['inclusive', 'accessible', 'diverse', 'equitable']
        # Negative indicators
        negative_keywords = ['exclusive', 'limited to', 'only for']
        
        positive_count = sum(1 for kw in positive_keywords if kw in value_prop or kw in target)
        negative_count = sum(1 for kw in negative_keywords if kw in value_prop or kw in target)
        
        if negative_count > 0:
            return 0.3  # Low ethics score
        elif positive_count > 0:
            return 0.9  # High ethics score
        else:
            return 0.7  # Neutral
    
    def _score_productivity_impact(self, idea: Dict[str, Any]) -> float:
        """Score productivity impact dimension"""
        value_prop = idea.get('value_prop', '').lower()
        mvp_scope = idea.get('mvp_scope', '').lower()
        
        # High impact indicators
        high_impact_keywords = [
            'save time', 'automate', 'reduce', 'eliminate', 'streamline',
            'increase efficiency', 'cut costs', 'faster', 'instant'
        ]
        
        # Count high impact keywords
        impact_count = sum(1 for kw in high_impact_keywords if kw in value_prop or kw in mvp_scope)
        
        if impact_count >= 3:
            return 0.9  # High impact
        elif impact_count >= 1:
            return 0.7  # Medium impact
        else:
            return 0.5  # Low impact
    
    def get_recommendations(self, score_result: Dict[str, Any]) -> List[str]:
        """
        Get recommendations based on score breakdown
        
        Args:
            score_result: Result from score_idea()
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        scores = score_result['scores']
        breakdown = score_result['breakdown']
        
        # Check each dimension
        for dim, data in breakdown.items():
            if data['score'] < 0.5:
                dim_name = dim.replace('_', ' ').title()
                recommendations.append(
                    f"Improve {dim_name}: {self.dimensions[dim]['description']}"
                )
        
        # Overall recommendations
        if score_result['overall_score'] < 0.6:
            recommendations.append(
                "Consider refining the idea or exploring alternative approaches"
            )
        
        if not recommendations:
            recommendations.append("Idea scores well across all dimensions!")
        
        return recommendations
