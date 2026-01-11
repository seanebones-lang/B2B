"""Enhanced pattern extraction using sentence transformers for better semantic understanding"""

import re
from collections import defaultdict
from typing import List, Dict, Any, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.cluster import DBSCAN
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans

from utils.logging import get_logger
import config

logger = get_logger(__name__)


class PatternExtractorV2:
    """
    Enhanced pattern extractor using sentence transformers for semantic similarity
    
    Falls back to TF-IDF + K-Means if sentence-transformers is not available
    """
    
    def __init__(
        self,
        use_semantic: bool = True,
        model_name: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize pattern extractor
        
        Args:
            use_semantic: Use sentence transformers if available
            model_name: Name of sentence transformer model
        """
        self.keywords = config.PAIN_KEYWORDS
        self.min_mentions = config.settings.min_pattern_mentions
        self.frequency_threshold = config.settings.pattern_frequency_threshold
        
        self.use_semantic = use_semantic and HAS_TRANSFORMERS
        self.model = None
        
        if self.use_semantic:
            try:
                logger.info("Loading sentence transformer model", model=model_name)
                self.model = SentenceTransformer(model_name)
                logger.info("Sentence transformer model loaded successfully")
            except Exception as e:
                logger.warning("Failed to load sentence transformer, falling back to TF-IDF", error=str(e))
                self.use_semantic = False
        
        if not self.use_semantic:
            logger.info("Using TF-IDF + K-Means for pattern extraction")
    
    def extract_patterns(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract pain patterns from reviews using semantic similarity or clustering
        
        Args:
            reviews: List of review dictionaries
            
        Returns:
            Dictionary with patterns, frequencies, and categorized complaints
        """
        if not reviews:
            return {
                "patterns": [],
                "total_reviews": 0,
                "categorized_complaints": []
            }
        
        logger.info("Extracting patterns", review_count=len(reviews), use_semantic=self.use_semantic)
        
        # Categorize complaints by keyword type
        categorized = self._categorize_complaints(reviews)
        
        # Extract patterns using semantic similarity or clustering
        if self.use_semantic:
            patterns = self._extract_semantic_patterns(reviews)
        else:
            patterns = self._cluster_patterns(reviews)
        
        # Filter patterns by frequency threshold
        filtered_patterns = self._filter_by_frequency(patterns, len(reviews))
        
        logger.info("Pattern extraction complete", pattern_count=len(filtered_patterns))
        
        return {
            "patterns": filtered_patterns,
            "total_reviews": len(reviews),
            "categorized_complaints": categorized
        }
    
    def _extract_semantic_patterns(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract patterns using sentence transformers and semantic similarity
        
        Args:
            reviews: List of review dictionaries
            
        Returns:
            List of pattern dictionaries
        """
        if len(reviews) < 3:
            return []
        
        try:
            # Get review texts
            texts = [review["text"] for review in reviews]
            
            # Generate embeddings
            logger.debug("Generating embeddings", text_count=len(texts))
            embeddings = self.model.encode(texts, show_progress_bar=False)
            
            # Use DBSCAN for density-based clustering (better for semantic similarity)
            # eps controls the distance threshold for clustering
            # min_samples controls minimum points in a cluster
            eps = 0.5  # Adjust based on similarity threshold
            min_samples = max(2, self.min_mentions)
            
            clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
            cluster_labels = clustering.fit_predict(embeddings)
            
            # Group reviews by cluster
            cluster_groups = defaultdict(list)
            for idx, cluster_id in enumerate(cluster_labels):
                if cluster_id != -1:  # -1 is noise in DBSCAN
                    cluster_groups[cluster_id].append(reviews[idx])
            
            # Extract patterns from clusters
            patterns = []
            for cluster_id, cluster_reviews in cluster_groups.items():
                if len(cluster_reviews) >= self.min_mentions:
                    # Find most representative review (closest to cluster centroid)
                    cluster_embeddings = embeddings[[i for i, label in enumerate(cluster_labels) if label == cluster_id]]
                    centroid = np.mean(cluster_embeddings, axis=0)
                    
                    # Find review closest to centroid
                    distances = np.linalg.norm(cluster_embeddings - centroid, axis=1)
                    representative_idx = np.argmin(distances)
                    representative_review = cluster_reviews[representative_idx]
                    
                    # Extract key phrases from representative review
                    pattern_description = self._extract_key_phrases(representative_review["text"])
                    
                    patterns.append({
                        "id": int(cluster_id),
                        "description": pattern_description,
                        "frequency": len(cluster_reviews),
                        "reviews": cluster_reviews[:10],  # Limit examples
                        "representative_review": representative_review["text"][:200]
                    })
            
            return sorted(patterns, key=lambda x: x["frequency"], reverse=True)
            
        except Exception as e:
            logger.error("Error in semantic pattern extraction", error=str(e), exc_info=True)
            # Fallback to clustering
            return self._cluster_patterns(reviews)
    
    def _cluster_patterns(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Cluster similar complaints using TF-IDF + K-Means (fallback)
        
        Args:
            reviews: List of review dictionaries
            
        Returns:
            List of pattern dictionaries
        """
        if len(reviews) < 3:
            return []
        
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.cluster import KMeans
            
            texts = [review["text"] for review in reviews]
            
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2
            )
            vectors = vectorizer.fit_transform(texts)
            
            # Determine number of clusters
            n_clusters = min(5, max(3, len(reviews) // 10))
            if vectors.shape[0] < n_clusters:
                n_clusters = max(2, vectors.shape[0] // 2)
            
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(vectors)
            
            cluster_groups = defaultdict(list)
            for idx, cluster_id in enumerate(clusters):
                cluster_groups[cluster_id].append(reviews[idx])
            
            patterns = []
            for cluster_id, cluster_reviews in cluster_groups.items():
                if len(cluster_reviews) >= self.min_mentions:
                    pattern_text = self._extract_common_phrases(cluster_reviews)
                    patterns.append({
                        "id": int(cluster_id),
                        "description": pattern_text,
                        "frequency": len(cluster_reviews),
                        "reviews": cluster_reviews[:10]
                    })
            
            return sorted(patterns, key=lambda x: x["frequency"], reverse=True)
            
        except Exception as e:
            logger.error("Error in clustering", error=str(e), exc_info=True)
            return self._simple_pattern_extraction(reviews)
    
    def _extract_key_phrases(self, text: str, max_phrases: int = 5) -> str:
        """
        Extract key phrases from text using simple heuristics
        
        Args:
            text: Text to extract phrases from
            max_phrases: Maximum number of phrases to return
            
        Returns:
            Comma-separated key phrases
        """
        # Extract meaningful phrases (3-5 words)
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Create n-grams (2-4 words)
        phrases = []
        for n in [2, 3, 4]:
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i:i+n])
                if len(phrase) > 5:  # Filter very short phrases
                    phrases.append(phrase)
        
        # Count phrase frequencies
        phrase_freq = defaultdict(int)
        for phrase in phrases:
            phrase_freq[phrase] += 1
        
        # Get top phrases
        top_phrases = sorted(phrase_freq.items(), key=lambda x: x[1], reverse=True)[:max_phrases]
        return ", ".join([phrase for phrase, _ in top_phrases])
    
    def _extract_common_phrases(self, reviews: List[Dict[str, Any]]) -> str:
        """Extract common phrases from a cluster of reviews"""
        all_words = []
        for review in reviews:
            words = re.findall(r'\b\w+\b', review["text"].lower())
            all_words.extend(words)
        
        word_freq = defaultdict(int)
        for word in all_words:
            if len(word) > 4:
                word_freq[word] += 1
        
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        return ", ".join([word for word, _ in top_words])
    
    def _categorize_complaints(self, reviews: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
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
                        break
        
        return categorized
    
    def _simple_pattern_extraction(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback: simple pattern extraction based on keyword matching"""
        patterns = defaultdict(list)
        
        for review in reviews:
            text_lower = review["text"].lower()
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
    
    def _filter_by_frequency(self, patterns: List[Dict[str, Any]], total_reviews: int) -> List[Dict[str, Any]]:
        """Filter patterns by frequency threshold"""
        filtered = []
        for pattern in patterns:
            frequency_ratio = pattern["frequency"] / total_reviews if total_reviews > 0 else 0
            if pattern["frequency"] >= self.min_mentions or frequency_ratio >= self.frequency_threshold:
                filtered.append(pattern)
        return filtered
