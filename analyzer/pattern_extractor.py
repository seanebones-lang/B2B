"""Pattern extraction from reviews using keyword matching and clustering"""

import re
from collections import defaultdict
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np
import config


class PatternExtractor:
    """Extract pain patterns from reviews using keyword matching and clustering"""
    
    def __init__(self):
        self.keywords = config.PAIN_KEYWORDS
        self.min_mentions = config.MIN_PATTERN_MENTIONS
        self.frequency_threshold = config.PATTERN_FREQUENCY_THRESHOLD
    
    def extract_patterns(self, reviews: List[Dict]) -> Dict:
        """
        Extract pain patterns from reviews
        Returns dict with patterns, frequencies, and categorized complaints
        """
        if not reviews:
            return {
                "patterns": [],
                "total_reviews": 0,
                "categorized_complaints": []
            }
        
        # Categorize complaints by keyword type
        categorized = self._categorize_complaints(reviews)
        
        # Extract patterns using clustering
        patterns = self._cluster_patterns(reviews)
        
        # Filter patterns by frequency threshold
        filtered_patterns = self._filter_by_frequency(patterns, len(reviews))
        
        return {
            "patterns": filtered_patterns,
            "total_reviews": len(reviews),
            "categorized_complaints": categorized
        }
    
    def _categorize_complaints(self, reviews: List[Dict]) -> Dict:
        """Categorize complaints by keyword type"""
        categorized = {
            "missing_feature": [],
            "wish_desire": [],
            "cant_blocks": []
        }
        
        for review in reviews:
            text_lower = review["text"].lower()
            
            for category, keywords in self.keywords.items():
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        categorized[category].append({
                            "text": review["text"],
                            "rating": review.get("rating"),
                            "source": review.get("source"),
                            "matched_keyword": keyword
                        })
                        break  # Only count once per review
        
        return categorized
    
    def _cluster_patterns(self, reviews: List[Dict]) -> List[Dict]:
        """Cluster similar complaints to identify patterns"""
        if len(reviews) < 3:
            return []
        
        # Prepare texts for clustering
        texts = [review["text"] for review in reviews]
        
        # Vectorize texts
        try:
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2
            )
            vectors = vectorizer.fit_transform(texts)
            
            # Determine number of clusters (between 3 and 5, or fewer if not enough data)
            n_clusters = min(5, max(3, len(reviews) // 10))
            
            if vectors.shape[0] < n_clusters:
                n_clusters = max(2, vectors.shape[0] // 2)
            
            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(vectors)
            
            # Group reviews by cluster
            cluster_groups = defaultdict(list)
            for idx, cluster_id in enumerate(clusters):
                cluster_groups[cluster_id].append(reviews[idx])
            
            # Extract patterns from clusters
            patterns = []
            for cluster_id, cluster_reviews in cluster_groups.items():
                if len(cluster_reviews) >= self.min_mentions:
                    # Find common keywords/phrases
                    pattern_text = self._extract_common_phrases(cluster_reviews)
                    patterns.append({
                        "id": cluster_id,
                        "description": pattern_text,
                        "frequency": len(cluster_reviews),
                        "reviews": cluster_reviews[:10]  # Limit to 10 examples
                    })
            
            return sorted(patterns, key=lambda x: x["frequency"], reverse=True)
            
        except Exception as e:
            print(f"Error in clustering: {str(e)}")
            # Fallback: return simple frequency-based patterns
            return self._simple_pattern_extraction(reviews)
    
    def _extract_common_phrases(self, reviews: List[Dict]) -> str:
        """Extract common phrases from a cluster of reviews"""
        # Simple approach: find most common words/phrases
        all_words = []
        for review in reviews:
            words = re.findall(r'\b\w+\b', review["text"].lower())
            all_words.extend(words)
        
        # Count word frequencies
        word_freq = defaultdict(int)
        for word in all_words:
            if len(word) > 4:  # Only meaningful words
                word_freq[word] += 1
        
        # Get top words
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        return ", ".join([word for word, _ in top_words])
    
    def _simple_pattern_extraction(self, reviews: List[Dict]) -> List[Dict]:
        """Fallback: simple pattern extraction based on keyword matching"""
        patterns = defaultdict(list)
        
        for review in reviews:
            text_lower = review["text"].lower()
            # Find matching keywords
            for category, keywords in self.keywords.items():
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        patterns[f"{category}: {keyword}"].append(review)
                        break
        
        result = []
        for pattern_name, pattern_reviews in patterns.items():
            if len(pattern_reviews) >= self.min_mentions:
                result.append({
                    "id": pattern_name,
                    "description": pattern_name,
                    "frequency": len(pattern_reviews),
                    "reviews": pattern_reviews[:10]
                })
        
        return sorted(result, key=lambda x: x["frequency"], reverse=True)
    
    def _filter_by_frequency(self, patterns: List[Dict], total_reviews: int) -> List[Dict]:
        """Filter patterns by frequency threshold"""
        filtered = []
        for pattern in patterns:
            frequency_ratio = pattern["frequency"] / total_reviews if total_reviews > 0 else 0
            if pattern["frequency"] >= self.min_mentions or frequency_ratio >= self.frequency_threshold:
                filtered.append(pattern)
        return filtered
