"""Data validation and quality scoring using Grok-3"""

from typing import List, Dict, Any, Optional
from utils.logging import get_logger
from analyzer.xai_client import XAIClient

logger = get_logger(__name__)


class DataValidator:
    """Validate and score review/complaint data quality using AI"""
    
    def __init__(self, xai_client: Optional[XAIClient] = None):
        """
        Initialize data validator
        
        Args:
            xai_client: xAI client instance (optional, will create if needed)
        """
        self.xai_client = xai_client
        logger.info("Data validator initialized")
    
    def validate_review_relevance(
        self,
        review_text: str,
        tool_name: str,
        min_score: int = 5
    ) -> Dict[str, Any]:
        """
        Validate review relevance for product ideation using Grok-3
        
        Args:
            review_text: Review/complaint text
            tool_name: Name of the tool being reviewed
            min_score: Minimum relevance score (1-10) to consider valid
            
        Returns:
            Dictionary with 'valid', 'score', and 'reason' keys
        """
        if not self.xai_client:
            logger.warning("No xAI client provided, skipping validation")
            return {'valid': True, 'score': 5, 'reason': 'No validation client'}
        
        prompt = f"""You are evaluating a complaint/review about {tool_name} for its relevance to product ideation.

Review text:
"{review_text}"

Task: Rate this complaint's relevance to generating actionable B2B product ideas on a scale of 1-10.

Consider:
- Does it identify a specific pain point or unmet need?
- Is it actionable (can we build something to solve this)?
- Is it relevant to B2B product development?
- Does it provide enough context?

Respond in JSON format:
{{
    "score": <1-10>,
    "reason": "<brief explanation>",
    "valid": <true if score >= {min_score}, false otherwise>
}}
"""
        
        try:
            response = self.xai_client.client.chat.completions.create(
                model=self.xai_client.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content
            
            # Parse JSON response
            import json
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                score = result.get('score', 5)
                valid = score >= min_score
                
                logger.debug(
                    "Review validated",
                    tool_name=tool_name,
                    score=score,
                    valid=valid
                )
                
                return {
                    'valid': valid,
                    'score': score,
                    'reason': result.get('reason', 'No reason provided')
                }
            else:
                # Fallback: assume valid if can't parse
                return {'valid': True, 'score': 5, 'reason': 'Could not parse validation response'}
                
        except Exception as e:
            logger.error("Error validating review", error=str(e))
            # On error, assume valid to not block processing
            return {'valid': True, 'score': 5, 'reason': f'Validation error: {str(e)}'}
    
    def filter_reviews_by_relevance(
        self,
        reviews: List[Dict[str, Any]],
        tool_name: str,
        min_score: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Filter reviews by relevance score
        
        Args:
            reviews: List of review dictionaries
            tool_name: Name of the tool
            min_score: Minimum relevance score
            
        Returns:
            Filtered list of reviews with validation metadata
        """
        if not reviews:
            return []
        
        filtered_reviews = []
        validation_stats = {'total': len(reviews), 'valid': 0, 'invalid': 0}
        
        for review in reviews:
            review_text = review.get('text', '')
            if not review_text or len(review_text) < 20:
                validation_stats['invalid'] += 1
                continue
            
            validation_result = self.validate_review_relevance(
                review_text,
                tool_name,
                min_score
            )
            
            if validation_result['valid']:
                # Add validation metadata
                review['validation'] = validation_result
                filtered_reviews.append(review)
                validation_stats['valid'] += 1
            else:
                validation_stats['invalid'] += 1
        
        logger.info(
            "Reviews filtered by relevance",
            tool_name=tool_name,
            total=validation_stats['total'],
            valid=validation_stats['valid'],
            invalid=validation_stats['invalid']
        )
        
        return filtered_reviews
    
    def detect_bias_patterns(
        self,
        reviews: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect bias patterns in reviews using sentiment analysis
        
        Args:
            reviews: List of review dictionaries
            
        Returns:
            Dictionary with bias detection results
        """
        from analyzer.sentiment_analyzer import SentimentAnalyzer
        
        analyzer = SentimentAnalyzer()
        reviews_with_sentiment = analyzer.analyze_sentiment(reviews)
        
        # Analyze sentiment distribution by source
        source_sentiment = {}
        for review in reviews_with_sentiment:
            source = review.get('source', 'unknown')
            sentiment = review.get('sentiment_label', 'neutral')
            
            if source not in source_sentiment:
                source_sentiment[source] = {'very_negative': 0, 'negative': 0, 'neutral': 0}
            
            if sentiment in source_sentiment[source]:
                source_sentiment[source][sentiment] += 1
        
        # Detect potential bias (e.g., one source has overwhelmingly negative sentiment)
        bias_flags = []
        for source, sentiments in source_sentiment.items():
            total = sum(sentiments.values())
            if total > 0:
                negative_ratio = (sentiments['very_negative'] + sentiments['negative']) / total
                if negative_ratio > 0.9:  # More than 90% negative
                    bias_flags.append({
                        'source': source,
                        'issue': 'Overwhelmingly negative sentiment',
                        'negative_ratio': negative_ratio
                    })
        
        return {
            'source_sentiment': source_sentiment,
            'bias_flags': bias_flags,
            'recommendation': 'Balance sources' if bias_flags else 'Sources appear balanced'
        }
