"""
NLP Preprocessing Service
==========================
Natural Language Processing module for text normalization and preprocessing.

This module handles all text preprocessing required before semantic analysis:
- Tokenization: Breaking text into words/sentences
- Stopword Removal: Removing common words (the, is, at, etc.)
- Lemmatization: Converting words to base form (running → run)
- Sentence Normalization: Standardizing text format

Architecture Flow:
==================
Raw Text → Tokenization → Lowercasing → Stopword Removal → Lemmatization → Clean Text

Why NLP Preprocessing?
======================
1. Reduces noise in the text
2. Focuses on meaningful content words
3. Improves semantic similarity calculations
4. Handles variations in student answers (typos, different word forms)
"""

import re
import logging
from typing import List, Set, Tuple, Optional
from functools import lru_cache

logger = logging.getLogger("AssessIQ.NLP")


class NLPPreprocessor:
    """
    NLP Text Preprocessing Pipeline.
    
    This class provides comprehensive text preprocessing for answer evaluation:
    - Tokenization (word and sentence level)
    - Stopword removal (customizable)
    - Lemmatization (using spaCy or NLTK)
    - Keyword extraction
    - Text normalization
    
    Usage:
        nlp = NLPPreprocessor()
        clean_text = nlp.normalize_text("The student is running fast!")
        # Output: "student run fast"
    """
    
    # Default English stopwords
    DEFAULT_STOPWORDS = {
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 
        "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 
        'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 
        'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 
        'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 
        'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 
        'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 
        'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 
        'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 
        'by', 'for', 'with', 'about', 'against', 'between', 'into', 
        'through', 'during', 'before', 'after', 'above', 'below', 'to', 
        'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 
        'again', 'further', 'then', 'once', 'here', 'there', 'when', 
        'where', 'why', 'how', 'all', 'each', 'few', 'more', 'most', 
        'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 
        'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 
        'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll', 
        'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', 
        "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', 
        "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 
        'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', 
        "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn', 
        "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"
    }
    
    def __init__(self, use_spacy: bool = True, spacy_model: str = None):
        """
        Initialize NLP preprocessor.
        
        Args:
            use_spacy: Whether to use spaCy (True) or NLTK (False)
            spacy_model: spaCy model name (default: en_core_web_sm)
        """
        from config.settings import settings
        
        self.use_spacy = use_spacy
        self.spacy_model_name = spacy_model or settings.SPACY_MODEL
        self._nlp = None
        self._lemmatizer = None
        self.stopwords = self.DEFAULT_STOPWORDS.copy()
        
        # Initialize the selected NLP library
        self._init_nlp()
    
    def _init_nlp(self):
        """Initialize NLP library (spaCy or NLTK)."""
        if self.use_spacy:
            self._init_spacy()
        else:
            self._init_nltk()
    
    def _init_spacy(self):
        """Initialize spaCy NLP pipeline."""
        try:
            import spacy
            
            try:
                self._nlp = spacy.load(self.spacy_model_name)
                logger.info(f"spaCy model '{self.spacy_model_name}' loaded successfully")
            except OSError:
                # Model not found, try to download
                logger.info(f"Downloading spaCy model: {self.spacy_model_name}")
                from spacy.cli import download
                download(self.spacy_model_name)
                self._nlp = spacy.load(self.spacy_model_name)
                logger.info(f"spaCy model '{self.spacy_model_name}' downloaded and loaded")
            
            # Update stopwords from spaCy
            self.stopwords.update(self._nlp.Defaults.stop_words)
            
        except ImportError:
            logger.warning("spaCy not installed, falling back to NLTK")
            self.use_spacy = False
            self._init_nltk()
    
    def _init_nltk(self):
        """Initialize NLTK for text processing."""
        try:
            import nltk
            from nltk.stem import WordNetLemmatizer
            from nltk.corpus import stopwords
            
            # Download required NLTK data
            for resource in ['punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger']:
                try:
                    nltk.data.find(f'tokenizers/{resource}' if resource == 'punkt' else resource)
                except LookupError:
                    nltk.download(resource, quiet=True)
            
            self._lemmatizer = WordNetLemmatizer()
            
            # Update stopwords from NLTK
            try:
                self.stopwords.update(set(stopwords.words('english')))
            except:
                pass
            
            logger.info("NLTK initialized successfully")
            
        except ImportError:
            logger.error("Neither spaCy nor NLTK is installed. Install at least one.")
            raise
    
    def tokenize_words(self, text: str) -> List[str]:
        """
        Tokenize text into individual words.
        
        Tokenization splits text into meaningful units (tokens).
        Example: "Hello, world!" → ["Hello", ",", "world", "!"]
        
        Args:
            text: Input text string
            
        Returns:
            List of word tokens
        """
        if self.use_spacy and self._nlp:
            doc = self._nlp(text)
            return [token.text for token in doc]
        else:
            import nltk
            return nltk.word_tokenize(text)
    
    def tokenize_sentences(self, text: str) -> List[str]:
        """
        Tokenize text into sentences.
        
        Example: "Hello. How are you?" → ["Hello.", "How are you?"]
        
        Args:
            text: Input text string
            
        Returns:
            List of sentences
        """
        if self.use_spacy and self._nlp:
            doc = self._nlp(text)
            return [sent.text.strip() for sent in doc.sents]
        else:
            import nltk
            return nltk.sent_tokenize(text)
    
    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """
        Remove stopwords from token list.
        
        Stopwords are common words that don't carry much meaning
        (the, is, at, which, on, etc.)
        
        Args:
            tokens: List of word tokens
            
        Returns:
            Filtered list without stopwords
        """
        return [
            token for token in tokens 
            if token.lower() not in self.stopwords
        ]
    
    def lemmatize(self, tokens: List[str]) -> List[str]:
        """
        Lemmatize tokens to their base form.
        
        Lemmatization converts words to their dictionary form:
        - "running" → "run"
        - "better" → "good"
        - "studies" → "study"
        
        Args:
            tokens: List of word tokens
            
        Returns:
            List of lemmatized tokens
        """
        if self.use_spacy and self._nlp:
            # Process tokens through spaCy
            text = " ".join(tokens)
            doc = self._nlp(text)
            return [token.lemma_ for token in doc if token.text in tokens]
        else:
            # Use NLTK WordNetLemmatizer
            return [self._lemmatizer.lemmatize(token) for token in tokens]
    
    def clean_text(self, text: str) -> str:
        """
        Basic text cleaning.
        
        - Remove special characters
        - Remove extra whitespace
        - Convert to lowercase
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        # Remove special characters except basic punctuation
        text = re.sub(r'[^a-zA-Z0-9\s\.\,\!\?\-]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def normalize_text(self, text: str, keep_punctuation: bool = False) -> str:
        """
        Complete text normalization pipeline.
        
        Pipeline:
        1. Clean text (remove special characters)
        2. Lowercase
        3. Tokenize
        4. Remove stopwords
        5. Lemmatize
        6. Rejoin into string
        
        Args:
            text: Input text to normalize
            keep_punctuation: Whether to keep punctuation marks
            
        Returns:
            Normalized text string
        """
        if not text or not text.strip():
            return ""
        
        logger.debug(f"Normalizing text: {text[:50]}...")
        
        # Step 1: Basic cleaning
        text = self.clean_text(text)
        
        # Step 2: Lowercase
        text = text.lower()
        
        # Step 3: Tokenize
        tokens = self.tokenize_words(text)
        
        # Step 4: Remove punctuation (optional)
        if not keep_punctuation:
            tokens = [t for t in tokens if t.isalnum()]
        
        # Step 5: Remove stopwords
        tokens = self.remove_stopwords(tokens)
        
        # Step 6: Lemmatize
        tokens = self.lemmatize(tokens)
        
        # Step 7: Rejoin
        normalized = " ".join(tokens)
        
        logger.debug(f"Normalized result: {normalized[:50]}...")
        
        return normalized
    
    def extract_keywords(
        self, 
        text: str, 
        top_n: int = 10,
        min_length: int = 3
    ) -> List[str]:
        """
        Extract key terms/concepts from text.
        
        Uses POS tagging to identify nouns, verbs, and adjectives
        as they typically carry the most meaning.
        
        Args:
            text: Input text
            top_n: Maximum number of keywords to extract
            min_length: Minimum word length to consider
            
        Returns:
            List of extracted keywords
        """
        if not text:
            return []
        
        keywords = []
        
        if self.use_spacy and self._nlp:
            doc = self._nlp(text)
            
            # Extract nouns, proper nouns, and adjectives
            for token in doc:
                if (token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and 
                    len(token.text) >= min_length and
                    token.text.lower() not in self.stopwords):
                    keywords.append(token.lemma_.lower())
            
            # Also extract noun phrases
            for chunk in doc.noun_chunks:
                if len(chunk.text) >= min_length:
                    keywords.append(chunk.text.lower())
        else:
            # Fallback: extract words that are not stopwords
            import nltk
            tokens = nltk.word_tokenize(text.lower())
            pos_tags = nltk.pos_tag(tokens)
            
            for word, pos in pos_tags:
                # NN = noun, JJ = adjective, VB = verb
                if (pos.startswith(('NN', 'JJ', 'VB')) and 
                    len(word) >= min_length and
                    word not in self.stopwords):
                    keywords.append(word)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        
        return unique_keywords[:top_n]
    
    def extract_named_entities(self, text: str) -> List[Tuple[str, str]]:
        """
        Extract named entities from text.
        
        Named entities are proper nouns like:
        - Person names
        - Organizations
        - Locations
        - Dates
        
        Args:
            text: Input text
            
        Returns:
            List of (entity_text, entity_type) tuples
        """
        entities = []
        
        if self.use_spacy and self._nlp:
            doc = self._nlp(text)
            for ent in doc.ents:
                entities.append((ent.text, ent.label_))
        else:
            import nltk
            try:
                tokens = nltk.word_tokenize(text)
                pos_tags = nltk.pos_tag(tokens)
                chunks = nltk.ne_chunk(pos_tags)
                
                for chunk in chunks:
                    if hasattr(chunk, 'label'):
                        entity_text = ' '.join(c[0] for c in chunk)
                        entities.append((entity_text, chunk.label()))
            except:
                pass
        
        return entities
    
    def calculate_word_overlap(
        self, 
        text1: str, 
        text2: str
    ) -> Tuple[float, Set[str], Set[str]]:
        """
        Calculate word overlap between two texts.
        
        Useful for quick keyword matching before semantic analysis.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Tuple of (overlap_ratio, common_words, unique_to_text1)
        """
        # Normalize both texts
        tokens1 = set(self.normalize_text(text1).split())
        tokens2 = set(self.normalize_text(text2).split())
        
        # Calculate overlap
        common = tokens1 & tokens2
        unique_to_1 = tokens1 - tokens2
        
        # Overlap ratio
        total_unique = len(tokens1 | tokens2)
        overlap_ratio = len(common) / total_unique if total_unique > 0 else 0
        
        return overlap_ratio, common, unique_to_1
    
    def get_text_statistics(self, text: str) -> dict:
        """
        Get statistical information about the text.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with text statistics
        """
        words = self.tokenize_words(text)
        sentences = self.tokenize_sentences(text)
        
        word_count = len([w for w in words if w.isalnum()])
        sentence_count = len(sentences)
        
        return {
            "character_count": len(text),
            "word_count": word_count,
            "sentence_count": sentence_count,
            "average_word_length": sum(len(w) for w in words if w.isalnum()) / max(word_count, 1),
            "average_sentence_length": word_count / max(sentence_count, 1),
            "unique_words": len(set(w.lower() for w in words if w.isalnum()))
        }


# ========== Example Usage ==========
if __name__ == "__main__":
    """
    Example usage of the NLP Preprocessor.
    """
    
    nlp = NLPPreprocessor()
    
    # Sample student answer
    sample_text = """
    Photosynthesis is the process by which plants convert sunlight into energy. 
    The process takes place in the chloroplasts, where chlorophyll captures light energy.
    Carbon dioxide and water are converted into glucose and oxygen.
    """
    
    print("Original Text:")
    print(sample_text)
    print("\n" + "="*50 + "\n")
    
    # Normalize text
    normalized = nlp.normalize_text(sample_text)
    print("Normalized Text:")
    print(normalized)
    print("\n" + "="*50 + "\n")
    
    # Extract keywords
    keywords = nlp.extract_keywords(sample_text)
    print("Keywords:")
    print(keywords)
    print("\n" + "="*50 + "\n")
    
    # Text statistics
    stats = nlp.get_text_statistics(sample_text)
    print("Text Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\nNLP Preprocessor module loaded successfully!")
