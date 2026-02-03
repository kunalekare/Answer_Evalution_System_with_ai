"""
Scoring Service
================
Hybrid scoring system combining multiple evaluation metrics.

This module implements the final scoring logic:
- Keyword Coverage Score
- Semantic Similarity Score
- Diagram Score (if applicable)
- Length Normalization
- Dynamic Weight Adjustment

Scoring Formula:
================
Final_Score = (Semantic_Score × W_s) + (Keyword_Score × W_k) + (Diagram_Score × W_d) - Length_Penalty

Where:
- W_s = Semantic weight (default: 0.6)
- W_k = Keyword weight (default: 0.2)
- W_d = Diagram weight (default: 0.2)
- Length_Penalty = Applied if answer is too short

Why Hybrid Scoring?
===================
1. Semantic alone may miss specific terms
2. Keywords alone miss paraphrasing
3. Combined approach catches both
4. Dynamic weights adapt to question type
"""

import logging
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("AssessIQ.Scoring")


class QuestionType(Enum):
    """Types of questions for weight adjustment."""
    FACTUAL = "factual"
    DESCRIPTIVE = "descriptive"
    DIAGRAM = "diagram"
    MIXED = "mixed"


@dataclass
class ScoreResult:
    """Data class for holding scoring results."""
    semantic_score: float
    keyword_score: float
    diagram_score: float
    length_penalty: float
    final_score: float
    obtained_marks: float
    max_marks: int
    grade: str
    matched_keywords: List[str]
    missing_keywords: List[str]


class ScoringService:
    """
    Hybrid Scoring Service for Answer Evaluation.
    
    This class combines multiple scoring methods to provide
    a comprehensive evaluation of student answers.
    
    Features:
    - Keyword coverage analysis
    - Length normalization
    - Dynamic weight adjustment
    - Grade classification
    
    Usage:
        scorer = ScoringService()
        keyword_score, matched, missing = scorer.calculate_keyword_coverage(
            model_keywords=['photosynthesis', 'chlorophyll', 'glucose'],
            student_keywords=['photosynthesis', 'glucose', 'light']
        )
    """
    
    # Default scoring weights
    DEFAULT_WEIGHTS = {
        QuestionType.FACTUAL: {
            'semantic': 0.4,
            'keyword': 0.5,
            'diagram': 0.1
        },
        QuestionType.DESCRIPTIVE: {
            'semantic': 0.7,
            'keyword': 0.2,
            'diagram': 0.1
        },
        QuestionType.DIAGRAM: {
            'semantic': 0.3,
            'keyword': 0.2,
            'diagram': 0.5
        },
        QuestionType.MIXED: {
            'semantic': 0.5,
            'keyword': 0.25,
            'diagram': 0.25
        }
    }
    
    # Grade thresholds
    GRADE_THRESHOLDS = {
        'excellent': 0.85,
        'good': 0.70,
        'average': 0.50,
        'poor': 0.0
    }
    
    def __init__(self):
        """Initialize the scoring service."""
        from config.settings import settings
        
        self.settings = settings
        logger.info("ScoringService initialized")
    
    def calculate_keyword_coverage(
        self,
        model_keywords: List[str],
        student_keywords: List[str],
        partial_match: bool = True,
        partial_threshold: float = 0.8
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calculate keyword coverage score.
        
        Measures how many key concepts from the model answer
        are present in the student's answer.
        
        Args:
            model_keywords: Keywords from model answer
            student_keywords: Keywords from student answer
            partial_match: Allow partial word matching
            partial_threshold: Threshold for partial matching
            
        Returns:
            Tuple of (coverage_score, matched_keywords, missing_keywords)
        """
        if not model_keywords:
            return 1.0, [], []
        
        # Normalize keywords to lowercase
        model_set = set(kw.lower().strip() for kw in model_keywords if kw)
        student_set = set(kw.lower().strip() for kw in student_keywords if kw)
        
        matched = []
        missing = []
        
        for model_kw in model_set:
            # Check for exact match
            if model_kw in student_set:
                matched.append(model_kw)
                continue
            
            # Check for partial match
            if partial_match:
                found = False
                for student_kw in student_set:
                    similarity = self._word_similarity(model_kw, student_kw)
                    if similarity >= partial_threshold:
                        matched.append(model_kw)
                        found = True
                        break
                
                if not found:
                    missing.append(model_kw)
            else:
                missing.append(model_kw)
        
        # Calculate coverage score
        coverage = len(matched) / len(model_set) if model_set else 0
        
        logger.debug(f"Keyword coverage: {coverage:.4f} ({len(matched)}/{len(model_set)})")
        
        return coverage, matched, missing
    
    def _word_similarity(self, word1: str, word2: str) -> float:
        """
        Calculate similarity between two words using character-level comparison.
        
        Uses Jaro-Winkler similarity for fuzzy matching.
        
        Args:
            word1: First word
            word2: Second word
            
        Returns:
            Similarity score between 0 and 1
        """
        # Simple check first
        if word1 == word2:
            return 1.0
        
        # Check if one is substring of other
        if word1 in word2 or word2 in word1:
            return 0.9
        
        # Use Levenshtein-based similarity
        len1, len2 = len(word1), len(word2)
        
        if len1 == 0 or len2 == 0:
            return 0.0
        
        # Calculate edit distance
        matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j
        
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                cost = 0 if word1[i-1] == word2[j-1] else 1
                matrix[i][j] = min(
                    matrix[i-1][j] + 1,      # deletion
                    matrix[i][j-1] + 1,      # insertion
                    matrix[i-1][j-1] + cost  # substitution
                )
        
        distance = matrix[len1][len2]
        max_len = max(len1, len2)
        
        return 1 - (distance / max_len)
    
    def calculate_length_penalty(
        self,
        model_length: int,
        student_length: int,
        min_ratio: float = 0.5,
        penalty_factor: float = 0.1
    ) -> float:
        """
        Calculate length penalty for answers that are too short.
        
        If student answer is less than min_ratio of model answer length,
        a penalty is applied proportional to the deficit.
        
        Args:
            model_length: Length of model answer (chars or words)
            student_length: Length of student answer
            min_ratio: Minimum acceptable length ratio
            penalty_factor: Penalty multiplier
            
        Returns:
            Penalty value (0 to penalty_factor)
        """
        if model_length == 0:
            return 0.0
        
        ratio = student_length / model_length
        
        if ratio >= min_ratio:
            return 0.0
        
        # Calculate penalty proportional to deficit
        deficit = min_ratio - ratio
        penalty = deficit * penalty_factor
        
        logger.debug(f"Length penalty: {penalty:.4f} (ratio: {ratio:.2f})")
        
        return min(penalty, penalty_factor)  # Cap at max penalty
    
    def get_weights(self, question_type: QuestionType) -> Dict[str, float]:
        """
        Get scoring weights for a specific question type.
        
        Different question types emphasize different aspects:
        - Factual: Higher keyword weight (specific terms matter)
        - Descriptive: Higher semantic weight (understanding matters)
        - Diagram: Higher diagram weight (visual accuracy matters)
        
        Args:
            question_type: Type of question
            
        Returns:
            Dictionary of weights
        """
        return self.DEFAULT_WEIGHTS.get(question_type, self.DEFAULT_WEIGHTS[QuestionType.MIXED])
    
    def classify_grade(self, score: float) -> str:
        """
        Classify score into grade category.
        
        Categories:
        - Excellent: >= 85%
        - Good: >= 70%
        - Average: >= 50%
        - Poor: < 50%
        
        Args:
            score: Normalized score (0 to 1)
            
        Returns:
            Grade string
        """
        if score >= self.GRADE_THRESHOLDS['excellent']:
            return 'excellent'
        elif score >= self.GRADE_THRESHOLDS['good']:
            return 'good'
        elif score >= self.GRADE_THRESHOLDS['average']:
            return 'average'
        else:
            return 'poor'
    
    def calculate_final_score(
        self,
        semantic_score: float,
        keyword_score: float,
        diagram_score: float = 0.0,
        length_penalty: float = 0.0,
        question_type: QuestionType = QuestionType.DESCRIPTIVE,
        max_marks: int = 10
    ) -> Tuple[float, float, str]:
        """
        Calculate final weighted score.
        
        Formula:
        Final = (Semantic × W_s) + (Keyword × W_k) + (Diagram × W_d) - Penalty
        
        Args:
            semantic_score: Semantic similarity score (0-1)
            keyword_score: Keyword coverage score (0-1)
            diagram_score: Diagram similarity score (0-1)
            length_penalty: Length penalty (0-1)
            question_type: Type of question for weight selection
            max_marks: Maximum marks for this question
            
        Returns:
            Tuple of (normalized_score, obtained_marks, grade)
        """
        # Get weights for question type
        weights = self.get_weights(question_type)
        
        # If no diagram, redistribute weight
        if diagram_score == 0.0:
            total_weight = weights['semantic'] + weights['keyword']
            weights = {
                'semantic': weights['semantic'] / total_weight,
                'keyword': weights['keyword'] / total_weight,
                'diagram': 0.0
            }
        
        # Calculate weighted score
        weighted_score = (
            semantic_score * weights['semantic'] +
            keyword_score * weights['keyword'] +
            diagram_score * weights['diagram']
        )
        
        # Apply length penalty
        final_score = max(0.0, weighted_score - length_penalty)
        
        # Ensure score is in valid range
        final_score = min(1.0, max(0.0, final_score))
        
        # Calculate marks
        obtained_marks = round(final_score * max_marks, 2)
        
        # Classify grade
        grade = self.classify_grade(final_score)
        
        logger.info(f"Final score: {final_score:.4f} ({obtained_marks}/{max_marks}) - Grade: {grade}")
        
        return final_score, obtained_marks, grade
    
    def evaluate_answer(
        self,
        model_text: str,
        student_text: str,
        model_keywords: List[str],
        student_keywords: List[str],
        semantic_score: float,
        diagram_score: float = 0.0,
        question_type: str = "descriptive",
        max_marks: int = 10
    ) -> ScoreResult:
        """
        Complete answer evaluation combining all scoring methods.
        
        This is the main entry point for scoring an answer.
        
        Args:
            model_text: Model answer text
            student_text: Student answer text
            model_keywords: Keywords from model answer
            student_keywords: Keywords from student answer
            semantic_score: Pre-calculated semantic similarity
            diagram_score: Pre-calculated diagram similarity
            question_type: Type of question
            max_marks: Maximum marks
            
        Returns:
            ScoreResult with all scoring details
        """
        # Convert question type
        try:
            q_type = QuestionType(question_type.lower())
        except ValueError:
            q_type = QuestionType.DESCRIPTIVE
        
        # Calculate keyword coverage
        keyword_score, matched, missing = self.calculate_keyword_coverage(
            model_keywords, student_keywords
        )
        
        # Calculate length penalty
        length_penalty = self.calculate_length_penalty(
            len(model_text.split()),
            len(student_text.split())
        )
        
        # Calculate final score
        final_score, obtained_marks, grade = self.calculate_final_score(
            semantic_score=semantic_score,
            keyword_score=keyword_score,
            diagram_score=diagram_score,
            length_penalty=length_penalty,
            question_type=q_type,
            max_marks=max_marks
        )
        
        return ScoreResult(
            semantic_score=round(semantic_score, 4),
            keyword_score=round(keyword_score, 4),
            diagram_score=round(diagram_score, 4),
            length_penalty=round(length_penalty, 4),
            final_score=round(final_score, 4),
            obtained_marks=obtained_marks,
            max_marks=max_marks,
            grade=grade,
            matched_keywords=matched,
            missing_keywords=missing
        )
    
    def generate_feedback(
        self,
        result: ScoreResult,
        model_text: str = "",
        student_text: str = ""
    ) -> Dict:
        """
        Generate detailed feedback based on scoring result.
        
        Args:
            result: ScoreResult from evaluate_answer
            model_text: Original model answer
            student_text: Original student answer
            
        Returns:
            Dictionary with feedback components
        """
        feedback = {
            'summary': '',
            'strengths': [],
            'improvements': [],
            'suggestions': []
        }
        
        # Generate summary based on grade
        grade_messages = {
            'excellent': "Excellent work! Your answer demonstrates strong understanding.",
            'good': "Good attempt! Your answer covers most key concepts.",
            'average': "Satisfactory answer. Some important concepts are missing.",
            'poor': "Your answer needs significant improvement."
        }
        feedback['summary'] = grade_messages.get(result.grade, "Evaluation complete.")
        
        # Identify strengths
        if result.semantic_score >= 0.8:
            feedback['strengths'].append("Strong conceptual understanding")
        if result.keyword_score >= 0.8:
            feedback['strengths'].append("Excellent coverage of key terms")
        if len(result.matched_keywords) > 0:
            feedback['strengths'].append(f"Correctly included: {', '.join(result.matched_keywords[:5])}")
        
        # Identify areas for improvement
        if result.semantic_score < 0.6:
            feedback['improvements'].append("Focus on understanding the core concepts")
        if result.keyword_score < 0.6:
            feedback['improvements'].append("Include more relevant technical terms")
        if result.length_penalty > 0:
            feedback['improvements'].append("Your answer is too brief - add more detail")
        if result.missing_keywords:
            feedback['improvements'].append(
                f"Missing concepts: {', '.join(result.missing_keywords[:5])}"
            )
        
        # Suggestions
        if result.grade in ['average', 'poor']:
            feedback['suggestions'].extend([
                "Review the topic thoroughly",
                "Focus on key definitions and concepts",
                "Use proper technical terminology"
            ])
        elif result.grade == 'good':
            feedback['suggestions'].extend([
                "Add more specific examples",
                "Elaborate on key points"
            ])
        else:
            feedback['suggestions'].append("Keep up the excellent work!")
        
        return feedback


class JaccardScorer:
    """
    Jaccard Similarity based scorer.
    
    Simple set-based similarity for quick word overlap calculation.
    J(A, B) = |A ∩ B| / |A ∪ B|
    """
    
    @staticmethod
    def calculate(
        text1: str, 
        text2: str, 
        use_ngrams: bool = False,
        n: int = 2
    ) -> float:
        """
        Calculate Jaccard similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            use_ngrams: Use n-grams instead of words
            n: Size of n-grams if use_ngrams is True
            
        Returns:
            Jaccard similarity score (0 to 1)
        """
        if not text1 or not text2:
            return 0.0
        
        if use_ngrams:
            # Create n-grams
            words1 = text1.lower().split()
            words2 = text2.lower().split()
            
            set1 = set(
                ' '.join(words1[i:i+n]) 
                for i in range(len(words1) - n + 1)
            )
            set2 = set(
                ' '.join(words2[i:i+n]) 
                for i in range(len(words2) - n + 1)
            )
        else:
            set1 = set(text1.lower().split())
            set2 = set(text2.lower().split())
        
        intersection = set1 & set2
        union = set1 | set2
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)


# ========== Example Usage ==========
if __name__ == "__main__":
    """
    Example usage of the Scoring Service.
    """
    
    print("=" * 60)
    print("Scoring Service Module Demo")
    print("=" * 60)
    
    scorer = ScoringService()
    
    # Example keywords
    model_keywords = ['photosynthesis', 'chlorophyll', 'glucose', 'oxygen', 'sunlight', 'carbon dioxide']
    student_keywords = ['photosynthesis', 'glucose', 'light', 'plants', 'energy']
    
    print("\nModel Keywords:", model_keywords)
    print("Student Keywords:", student_keywords)
    
    # Calculate keyword coverage
    coverage, matched, missing = scorer.calculate_keyword_coverage(
        model_keywords, student_keywords
    )
    
    print(f"\nKeyword Coverage: {coverage:.2%}")
    print(f"Matched: {matched}")
    print(f"Missing: {missing}")
    
    # Calculate final score
    final_score, marks, grade = scorer.calculate_final_score(
        semantic_score=0.78,
        keyword_score=coverage,
        diagram_score=0.0,
        length_penalty=0.0,
        question_type=QuestionType.DESCRIPTIVE,
        max_marks=10
    )
    
    print(f"\nFinal Score: {final_score:.2%}")
    print(f"Obtained Marks: {marks}/10")
    print(f"Grade: {grade.upper()}")
    
    # Full evaluation
    result = scorer.evaluate_answer(
        model_text="Photosynthesis is the process by which plants convert sunlight into glucose.",
        student_text="Plants use photosynthesis to make food from light and produce glucose.",
        model_keywords=model_keywords,
        student_keywords=student_keywords,
        semantic_score=0.78,
        question_type="descriptive",
        max_marks=10
    )
    
    print(f"\n--- Full Evaluation ---")
    print(f"Semantic Score: {result.semantic_score}")
    print(f"Keyword Score: {result.keyword_score}")
    print(f"Final Score: {result.final_score}")
    print(f"Grade: {result.grade.upper()}")
    
    # Generate feedback
    feedback = scorer.generate_feedback(result)
    print(f"\nFeedback Summary: {feedback['summary']}")
    print(f"Strengths: {feedback['strengths']}")
    print(f"Improvements: {feedback['improvements']}")
    
    print("\nScoring Service module loaded successfully!")
