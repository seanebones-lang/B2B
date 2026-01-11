"""Sentiment analysis using sentence-transformers for clustering complaints"""

from typing import List, Dict, Any
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from utils.logging import get_logger

logger = get_logger(__name__)

# Try to import sentence-transformers, fallback to simple sentiment
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available, using simple sentiment analysis")


class SentimentAnalyzer:
    """Analyze sentiment and cluster similar complaints"""
    
    def __init__(self):
        """Initialize sentiment analyzer"""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Use a lightweight model for sentiment
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                self.use_embeddings = True
                logger.info("Sentiment analyzer initialized with sentence-transformers")
            except Exception as e:
                logger.warning("Failed to load sentence-transformers model", error=str(e))
                self.use_embeddings = False
        else:
            self.use_embeddings = False
    
    def analyze_sentiment(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for reviews and add sentiment scores
        
        Args:
            reviews: List of review dictionaries
            
        Returns:
            Reviews with added sentiment scores
        """
        if not reviews:
            return []
        
        if self.use_embeddings:
            return self._analyze_with_embeddings(reviews)
        else:
            return self._analyze_simple(reviews)
    
    def _analyze_with_embeddings(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze using sentence embeddings"""
        texts = [review.get('text', '') for review in reviews]
        
        try:
            # Generate embeddings
            embeddings = self.model.encode(texts, show_progress_bar=False)
            
            # Cluster similar complaints
            if len(reviews) > 3:
                n_clusters = min(5, max(2, len(reviews) // 10))
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                clusters = kmeans.fit_predict(embeddings)
                
                # Add cluster info to reviews
                for i, review in enumerate(reviews):
                    review['sentiment_cluster'] = int(clusters[i])
                    # Calculate average similarity to cluster center
                    cluster_center = kmeans.cluster_centers_[clusters[i]]
                    similarity = cosine_similarity([embeddings[i]], [cluster_center])[0][0]
                    review['cluster_similarity'] = float(similarity)
            
            # Add basic sentiment score (negative = lower score)
            negative_words = ['terrible', 'awful', 'worst', 'hate', 'disappointed', 
                            'frustrated', 'broken', 'problem', 'issue', 'bug']
            positive_words = ['good', 'great', 'excellent', 'love', 'amazing', 'perfect']
            
            for i, review in enumerate(reviews):
                text_lower = review.get('text', '').lower()
                negative_count = sum(1 for word in negative_words if word in text_lower)
                positive_count = sum(1 for word in positive_words if word in text_lower)
                
                # Sentiment score: -1 (very negative) to 1 (very positive)
                # For complaints, we expect negative scores
                sentiment_score = (positive_count - negative_count) / max(len(text_lower.split()), 1)
                review['sentiment_score'] = float(sentiment_score)
                review['sentiment_label'] = 'very_negative' if sentiment_score < -0.1 else 'negative' if sentiment_score < 0 else 'neutral'
            
            logger.info("Sentiment analysis complete", reviews_analyzed=len(reviews))
            
        except Exception as e:
            logger.error("Error in sentiment analysis", error=str(e))
            return self._analyze_simple(reviews)
        
        return reviews
    
    def _analyze_simple(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simple sentiment analysis without embeddings"""
        negative_words = ['terrible', 'awful', 'worst', 'hate', 'disappointed', 
                        'frustrated', 'broken', 'problem', 'issue', 'bug', 'missing',
                        'doesn\'t', 'cannot', 'unable', 'failed', 'error']
        positive_words = ['good', 'great', 'excellent', 'love', 'amazing', 'perfect', 'works']
        
        for review in reviews:
            text_lower = review.get('text', '').lower()
            negative_count = sum(1 for word in negative_words if word in text_lower)
            positive_count = sum(1 for word in positive_words if word in text_lower)
            
            sentiment_score = (positive_count - negative_count) / max(len(text_lower.split()), 1)
            review['sentiment_score'] = float(sentiment_score)
            review['sentiment_label'] = 'very_negative' if sentiment_score < -0.1 else 'negative' if sentiment_score < 0 else 'neutral'
            review['sentiment_cluster'] = None
            review['cluster_similarity'] = None
        
        return reviews
    
    def cluster_by_sentiment(self, reviews: List[Dict[str, Any]], n_clusters: int = 5) -> List[List[Dict[str, Any]]]:
        """
        Cluster reviews by sentiment similarity
        
        Args:
            reviews: List of reviews with sentiment scores
            n_clusters: Number of clusters
            
        Returns:
            List of clusters (each cluster is a list of reviews)
        """
        if not self.use_embeddings or len(reviews) < n_clusters:
            # Simple clustering by sentiment score
            sorted_reviews = sorted(reviews, key=lambda x: x.get('sentiment_score', 0))
            cluster_size = len(sorted_reviews) // n_clusters
            clusters = []
            for i in range(n_clusters):
                start = i * cluster_size
                end = start + cluster_size if i < n_clusters - 1 else len(sorted_reviews)
                clusters.append(sorted_reviews[start:end])
            return clusters
        
        # Use embeddings for clustering
        texts = [review.get('text', '') for review in reviews]
        embeddings = self.model.encode(texts, show_progress_bar=False)
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(embeddings)
        
        # Group reviews by cluster
        cluster_groups = [[] for _ in range(n_clusters)]
        for i, cluster_id in enumerate(clusters):
            cluster_groups[int(cluster_id)].append(reviews[i])
        
        return cluster_groups
