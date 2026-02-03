"""
Semantic Analysis Service
==========================
Deep semantic understanding using sentence embeddings and similarity metrics.

This module provides semantic analysis capabilities:
- Sentence Embeddings using Transformer models (BERT, RoBERTa, etc.)
- Cosine Similarity for meaning-based comparison
- Semantic similarity scoring

Why Semantic Analysis?
======================
Traditional keyword matching fails when:
- Student uses synonyms ("large" vs "big")
- Different sentence structures express same meaning
- Paraphrasing is used

Semantic analysis understands MEANING, not just words.

Comparison of Approaches:
=========================
1. TF-IDF:
   - Pros: Fast, simple, no ML needed
   - Cons: No semantic understanding, bag-of-words model
   - Use case: Large document retrieval

2. Word2Vec:
   - Pros: Captures word relationships
   - Cons: Loses sentence context, averaging problem
   - Use case: Word similarity tasks

3. Sentence-BERT (RECOMMENDED):
   - Pros: Full sentence understanding, state-of-the-art accuracy
   - Cons: Requires more computation
   - Use case: Semantic similarity, answer evaluation

We use Sentence-BERT because it provides the best semantic understanding
for comparing student answers with model answers.
"""

import logging
from typing import List, Tuple, Optional, Union
import numpy as np
from functools import lru_cache

logger = logging.getLogger("AssessIQ.Semantic")


class SemanticAnalyzer:
    """
    Semantic Analysis using Sentence Transformers.
    
    This class provides semantic similarity calculation using
    state-of-the-art transformer models (BERT, RoBERTa, etc.)
    
    The workflow:
    1. Convert text to high-dimensional embeddings (vectors)
    2. Calculate cosine similarity between vectors
    3. Higher similarity = more similar meaning
    
    Usage:
        analyzer = SemanticAnalyzer()
        similarity = analyzer.calculate_similarity(
            "The cat sat on the mat",
            "A feline was sitting on the rug"
        )
        # Output: ~0.75 (high similarity despite different words)
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize Semantic Analyzer with specified model.
        
        Args:
            model_name: Name of the sentence-transformers model to use
                       Default: 'all-MiniLM-L6-v2' (fast and accurate)
                       
        Available Models (from sentence-transformers):
        - 'all-MiniLM-L6-v2': Fast, good accuracy (recommended)
        - 'all-mpnet-base-v2': Best accuracy, slower
        - 'paraphrase-MiniLM-L6-v2': Good for paraphrase detection
        - 'multi-qa-MiniLM-L6-cos-v1': Optimized for Q&A
        """
        from config.settings import settings
        
        self.model_name = model_name or settings.SENTENCE_TRANSFORMER_MODEL
        self.low_memory_mode = getattr(settings, 'LOW_MEMORY_MODE', False)
        self._model = None
        self._model_initialized = False
        
        # Only load model immediately if not in low memory mode
        if not self.low_memory_mode:
            self._init_model()
        else:
            logger.info("Low memory mode: Semantic model will be loaded on first use")
    
    def _ensure_model_initialized(self):
        """Ensure the model is initialized (for lazy loading)."""
        if not self._model_initialized:
            self._init_model()
            self._model_initialized = True
    
    def _init_model(self):
        """Initialize the Sentence Transformer model."""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading Sentence Transformer model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Model '{self.model_name}' loaded successfully")
            
        except ImportError:
            logger.error(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def get_embedding(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embedding vector(s) for text.
        
        Embeddings are high-dimensional vectors that capture
        the semantic meaning of the text.
        
        Args:
            text: Single text string or list of strings
            
        Returns:
            numpy array of embeddings
            - Single text: shape (embedding_dim,)
            - Multiple texts: shape (n_texts, embedding_dim)
        """
        # Ensure model is loaded (for lazy loading in low memory mode)
        self._ensure_model_initialized()
        
        if not text:
            raise ValueError("Text cannot be empty")
        
        # Ensure text is not too long (models have max length)
        if isinstance(text, str):
            text = text[:10000]  # Truncate if too long
        else:
            text = [t[:10000] for t in text]
        
        embedding = self._model.encode(text, convert_to_numpy=True)
        
        return embedding
    
    def cosine_similarity(
        self, 
        embedding1: np.ndarray, 
        embedding2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Cosine similarity measures the angle between two vectors:
        - 1.0 = identical direction (same meaning)
        - 0.0 = orthogonal (unrelated)
        - -1.0 = opposite direction (opposite meaning)
        
        Formula:
        similarity = (A · B) / (||A|| × ||B||)
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between -1 and 1
        """
        # Normalize vectors
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        similarity = dot_product / (norm1 * norm2)
        
        return float(similarity)
    
    def calculate_similarity(
        self, 
        text1: str, 
        text2: str,
        normalize: bool = True
    ) -> float:
        """
        Calculate semantic similarity between two texts.
        
        This is the main method for comparing student answers
        with model answers.
        
        Args:
            text1: First text (e.g., model answer)
            text2: Second text (e.g., student answer)
            normalize: Whether to normalize score to 0-1 range
            
        Returns:
            Similarity score (0 to 1 if normalized)
        """
        if not text1 or not text2:
            logger.warning("Empty text provided for similarity calculation")
            return 0.0
        
        logger.debug(f"Calculating similarity between texts...")
        
        # Generate embeddings
        embedding1 = self.get_embedding(text1)
        embedding2 = self.get_embedding(text2)
        
        # Calculate cosine similarity
        similarity = self.cosine_similarity(embedding1, embedding2)
        
        # Normalize to 0-1 range (cosine can be negative)
        if normalize:
            similarity = (similarity + 1) / 2  # Map [-1, 1] to [0, 1]
        
        logger.debug(f"Semantic similarity: {similarity:.4f}")
        
        return similarity
    
    def calculate_sentence_similarities(
        self, 
        reference: str, 
        candidate: str
    ) -> List[Tuple[str, str, float]]:
        """
        Calculate similarity between individual sentences.
        
        Useful for detailed analysis of which parts of the answer
        match well and which don't.
        
        Args:
            reference: Reference text (model answer)
            candidate: Candidate text (student answer)
            
        Returns:
            List of (reference_sent, candidate_sent, similarity) tuples
        """
        from api.services.nlp_service import NLPPreprocessor
        
        nlp = NLPPreprocessor()
        
        # Split into sentences
        ref_sentences = nlp.tokenize_sentences(reference)
        cand_sentences = nlp.tokenize_sentences(candidate)
        
        if not ref_sentences or not cand_sentences:
            return []
        
        # Get embeddings for all sentences
        ref_embeddings = self.get_embedding(ref_sentences)
        cand_embeddings = self.get_embedding(cand_sentences)
        
        # Calculate pairwise similarities
        results = []
        for i, (ref_sent, ref_emb) in enumerate(zip(ref_sentences, ref_embeddings)):
            best_match = None
            best_sim = -1
            
            for j, (cand_sent, cand_emb) in enumerate(zip(cand_sentences, cand_embeddings)):
                sim = self.cosine_similarity(ref_emb, cand_emb)
                if sim > best_sim:
                    best_sim = sim
                    best_match = cand_sent
            
            # Normalize similarity
            best_sim = (best_sim + 1) / 2
            results.append((ref_sent, best_match, best_sim))
        
        return results
    
    def find_missing_concepts(
        self, 
        model_text: str, 
        student_text: str,
        threshold: float = 0.6
    ) -> List[str]:
        """
        Identify concepts from model answer missing in student answer.
        
        Args:
            model_text: Model/reference answer
            student_text: Student's answer
            threshold: Similarity threshold below which a concept is "missing"
            
        Returns:
            List of sentences/concepts from model answer not found in student answer
        """
        sentence_sims = self.calculate_sentence_similarities(model_text, student_text)
        
        missing = []
        for ref_sent, _, sim in sentence_sims:
            if sim < threshold:
                missing.append(ref_sent)
        
        return missing


class TFIDFAnalyzer:
    """
    TF-IDF based text similarity analyzer.
    
    TF-IDF (Term Frequency-Inverse Document Frequency) is a simpler
    approach that works well for keyword-based matching.
    
    Used as a complementary method alongside semantic analysis.
    """
    
    def __init__(self):
        """Initialize TF-IDF vectorizer."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            self.vectorizer = TfidfVectorizer(
                lowercase=True,
                stop_words='english',
                ngram_range=(1, 2),  # Include bigrams
                max_features=5000
            )
            self._cosine_similarity = cosine_similarity
            self._fitted = False
            
        except ImportError:
            logger.error(
                "scikit-learn not installed. "
                "Install with: pip install scikit-learn"
            )
            raise
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate TF-IDF based similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        if not text1 or not text2:
            return 0.0
        
        # Fit and transform both texts
        tfidf_matrix = self.vectorizer.fit_transform([text1, text2])
        
        # Calculate cosine similarity
        similarity = self._cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        
        return float(similarity[0][0])
    
    def get_important_terms(
        self, 
        text: str, 
        top_n: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Get the most important terms in a text based on TF-IDF scores.
        
        Args:
            text: Input text
            top_n: Number of top terms to return
            
        Returns:
            List of (term, score) tuples
        """
        # Fit vectorizer on the text
        tfidf_matrix = self.vectorizer.fit_transform([text])
        feature_names = self.vectorizer.get_feature_names_out()
        
        # Get scores
        scores = tfidf_matrix.toarray()[0]
        
        # Sort by score
        term_scores = list(zip(feature_names, scores))
        term_scores.sort(key=lambda x: x[1], reverse=True)
        
        return term_scores[:top_n]


class JaccardSimilarity:
    """
    Jaccard Similarity Calculator.
    
    Jaccard similarity is a simple set-based similarity metric:
    J(A, B) = |A ∩ B| / |A ∪ B|
    
    Useful for quick word overlap calculations.
    """
    
    @staticmethod
    def calculate(text1: str, text2: str) -> float:
        """
        Calculate Jaccard similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Jaccard similarity score (0 to 1)
        """
        if not text1 or not text2:
            return 0.0
        
        # Tokenize and create sets
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Calculate intersection and union
        intersection = words1 & words2
        union = words1 | words2
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)


class HybridSimilarity:
    """
    Hybrid Similarity combining multiple approaches.
    
    Combines:
    1. Semantic similarity (BERT) - captures meaning
    2. TF-IDF similarity - captures keyword importance
    3. Jaccard similarity - captures word overlap
    
    This provides a more robust similarity measure than any single approach.
    """
    
    def __init__(
        self,
        semantic_weight: float = 0.6,
        tfidf_weight: float = 0.25,
        jaccard_weight: float = 0.15
    ):
        """
        Initialize hybrid similarity calculator.
        
        Args:
            semantic_weight: Weight for semantic similarity
            tfidf_weight: Weight for TF-IDF similarity
            jaccard_weight: Weight for Jaccard similarity
        """
        # Validate weights sum to 1
        total = semantic_weight + tfidf_weight + jaccard_weight
        self.semantic_weight = semantic_weight / total
        self.tfidf_weight = tfidf_weight / total
        self.jaccard_weight = jaccard_weight / total
        
        self.semantic = SemanticAnalyzer()
        self.tfidf = TFIDFAnalyzer()
    
    def calculate_similarity(
        self, 
        text1: str, 
        text2: str,
        return_breakdown: bool = False
    ) -> Union[float, Tuple[float, dict]]:
        """
        Calculate hybrid similarity score.
        
        Args:
            text1: First text
            text2: Second text
            return_breakdown: Whether to return individual scores
            
        Returns:
            Combined similarity score, or (score, breakdown_dict) if return_breakdown
        """
        # Calculate individual similarities
        semantic_sim = self.semantic.calculate_similarity(text1, text2)
        tfidf_sim = self.tfidf.calculate_similarity(text1, text2)
        jaccard_sim = JaccardSimilarity.calculate(text1, text2)
        
        # Weighted combination
        combined = (
            semantic_sim * self.semantic_weight +
            tfidf_sim * self.tfidf_weight +
            jaccard_sim * self.jaccard_weight
        )
        
        if return_breakdown:
            breakdown = {
                'semantic': semantic_sim,
                'tfidf': tfidf_sim,
                'jaccard': jaccard_sim,
                'combined': combined,
                'weights': {
                    'semantic': self.semantic_weight,
                    'tfidf': self.tfidf_weight,
                    'jaccard': self.jaccard_weight
                }
            }
            return combined, breakdown
        
        return combined


# ========== Example Usage ==========
if __name__ == "__main__":
    """
    Example usage of the Semantic Analysis module.
    """
    
    print("=" * 60)
    print("Semantic Analysis Module Demo")
    print("=" * 60)
    
    # Sample texts
    model_answer = """
    Photosynthesis is the process by which green plants and some other organisms 
    use sunlight to synthesize nutrients from carbon dioxide and water. 
    The process takes place primarily in the leaves, within structures called chloroplasts.
    The main products are glucose and oxygen.
    """
    
    student_answer = """
    Photosynthesis is how plants make their food using light from the sun.
    It happens in the leaves where chlorophyll is present.
    Plants take in carbon dioxide and water to produce sugar and release oxygen.
    """
    
    print("\nModel Answer:")
    print(model_answer.strip())
    print("\nStudent Answer:")
    print(student_answer.strip())
    print("\n" + "=" * 60)
    
    # Semantic similarity
    analyzer = SemanticAnalyzer()
    similarity = analyzer.calculate_similarity(model_answer, student_answer)
    print(f"\nSemantic Similarity: {similarity:.4f} ({similarity*100:.1f}%)")
    
    # TF-IDF similarity
    tfidf = TFIDFAnalyzer()
    tfidf_sim = tfidf.calculate_similarity(model_answer, student_answer)
    print(f"TF-IDF Similarity: {tfidf_sim:.4f} ({tfidf_sim*100:.1f}%)")
    
    # Jaccard similarity
    jaccard_sim = JaccardSimilarity.calculate(model_answer, student_answer)
    print(f"Jaccard Similarity: {jaccard_sim:.4f} ({jaccard_sim*100:.1f}%)")
    
    # Hybrid similarity
    hybrid = HybridSimilarity()
    combined, breakdown = hybrid.calculate_similarity(
        model_answer, student_answer, return_breakdown=True
    )
    print(f"\nHybrid Similarity: {combined:.4f} ({combined*100:.1f}%)")
    
    print("\nSemantic Analysis module loaded successfully!")
