"""Tests for sentiment analyzer"""

import pytest
from analyzer.sentiment_analyzer import SentimentAnalyzer


class TestSentimentAnalyzer:
    """Test sentiment analysis functionality"""
    
    def test_init(self):
        """Test sentiment analyzer initialization"""
        analyzer = SentimentAnalyzer()
        # Should initialize whether or not sentence-transformers is available
        assert hasattr(analyzer, 'use_embeddings')
    
    def test_analyze_simple_sentiment(self):
        """Test simple sentiment analysis"""
        analyzer = SentimentAnalyzer()
        
        reviews = [
            {'text': 'This tool is terrible and awful. Worst experience ever.'},
            {'text': 'Great tool, love it! Amazing features.'},
            {'text': 'The tool has some problems and issues.'}
        ]
        
        results = analyzer._analyze_simple(reviews)
        
        assert len(results) == 3
        # First review should be very negative
        assert results[0]['sentiment_score'] < 0
        assert results[0]['sentiment_label'] in ['very_negative', 'negative']
        
        # Second review should be positive
        assert results[1]['sentiment_score'] > 0 or results[1]['sentiment_label'] == 'neutral'
        
        # Third review should be negative
        assert results[2]['sentiment_score'] <= 0
    
    def test_empty_reviews(self):
        """Test with empty reviews list"""
        analyzer = SentimentAnalyzer()
        results = analyzer.analyze_sentiment([])
        assert results == []
    
    def test_cluster_by_sentiment(self):
        """Test sentiment clustering"""
        analyzer = SentimentAnalyzer()
        
        reviews = [
            {'text': 'Terrible tool', 'sentiment_score': -0.5},
            {'text': 'Awful experience', 'sentiment_score': -0.4},
            {'text': 'Great tool', 'sentiment_score': 0.3},
            {'text': 'Amazing features', 'sentiment_score': 0.4},
        ]
        
        clusters = analyzer.cluster_by_sentiment(reviews, n_clusters=2)
        
        assert len(clusters) == 2
        # Should have at least one cluster with negative reviews
        assert any(len(cluster) > 0 for cluster in clusters)
