"""
Evaluation Routes
==================
Handles the core evaluation logic - OCR, NLP, Semantic Analysis, and Scoring.
This is the main processing pipeline for answer evaluation.
"""

import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from config.settings import settings

router = APIRouter()
logger = logging.getLogger("AssessIQ.Evaluation")


# ========== Enums ==========
class QuestionType(str, Enum):
    """Types of questions for dynamic weight adjustment."""
    FACTUAL = "factual"
    DESCRIPTIVE = "descriptive"
    DIAGRAM = "diagram"
    MIXED = "mixed"


class GradeLevel(str, Enum):
    """Grade classification based on similarity scores."""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"


# ========== Pydantic Models ==========
class EvaluationRequest(BaseModel):
    """Request model for evaluation."""
    evaluation_id: str = Field(..., description="ID from upload response")
    question_type: QuestionType = Field(default=QuestionType.DESCRIPTIVE)
    max_marks: int = Field(default=10, ge=1, le=100)
    include_diagram: bool = Field(default=False)
    custom_keywords: Optional[List[str]] = Field(default=None)


class TextEvaluationRequest(BaseModel):
    """Request model for direct text evaluation (without file upload)."""
    model_answer: str = Field(..., min_length=10, description="The correct/model answer text")
    student_answer: str = Field(..., min_length=1, description="The student's answer text")
    question_type: QuestionType = Field(default=QuestionType.DESCRIPTIVE)
    max_marks: int = Field(default=10, ge=1, le=100)
    custom_keywords: Optional[List[str]] = Field(default=None)


class ScoreBreakdown(BaseModel):
    """Detailed breakdown of scores."""
    semantic_score: float = Field(..., ge=0, le=1)
    keyword_score: float = Field(..., ge=0, le=1)
    diagram_score: Optional[float] = Field(default=None, ge=0, le=1)
    length_penalty: float = Field(default=0, ge=0, le=1)
    weighted_score: float = Field(..., ge=0, le=1)


class ConceptMatch(BaseModel):
    """Matched and missing concepts."""
    matched: List[str]
    missing: List[str]
    coverage_percentage: float


class EvaluationResult(BaseModel):
    """Complete evaluation result."""
    success: bool
    evaluation_id: str
    final_score: float
    max_marks: int
    obtained_marks: float
    grade: GradeLevel
    score_breakdown: ScoreBreakdown
    concepts: ConceptMatch
    explanation: str
    suggestions: List[str]
    processing_time: float
    timestamp: str


# ========== Helper Functions ==========
def classify_grade(similarity: float) -> GradeLevel:
    """Classify similarity score into grade levels."""
    if similarity >= settings.SEMANTIC_EXCELLENT_THRESHOLD:
        return GradeLevel.EXCELLENT
    elif similarity >= settings.SEMANTIC_GOOD_THRESHOLD:
        return GradeLevel.GOOD
    elif similarity >= settings.SEMANTIC_AVERAGE_THRESHOLD:
        return GradeLevel.AVERAGE
    else:
        return GradeLevel.POOR


def get_dynamic_weights(question_type: QuestionType) -> Dict[str, float]:
    """
    Adjust scoring weights based on question type.
    
    - Factual questions: Higher weight on keyword matching
    - Descriptive questions: Higher weight on semantic understanding
    - Diagram questions: Include diagram evaluation weight
    """
    weights = {
        QuestionType.FACTUAL: {
            "semantic": 0.4,
            "keyword": 0.5,
            "diagram": 0.1
        },
        QuestionType.DESCRIPTIVE: {
            "semantic": 0.7,
            "keyword": 0.2,
            "diagram": 0.1
        },
        QuestionType.DIAGRAM: {
            "semantic": 0.3,
            "keyword": 0.2,
            "diagram": 0.5
        },
        QuestionType.MIXED: {
            "semantic": settings.WEIGHT_SEMANTIC,
            "keyword": settings.WEIGHT_KEYWORD,
            "diagram": settings.WEIGHT_DIAGRAM
        }
    }
    return weights.get(question_type, weights[QuestionType.MIXED])


def generate_explanation(
    grade: GradeLevel,
    semantic_score: float,
    keyword_score: float,
    concepts: ConceptMatch
) -> str:
    """Generate human-readable explanation of the score."""
    
    explanations = {
        GradeLevel.EXCELLENT: (
            f"Excellent work! Your answer demonstrates a strong understanding of the concept. "
            f"The semantic similarity is {semantic_score:.1%}, indicating your explanation "
            f"closely matches the expected answer. You covered {concepts.coverage_percentage:.0%} "
            f"of the key concepts."
        ),
        GradeLevel.GOOD: (
            f"Good attempt! Your answer shows a reasonable understanding of the topic. "
            f"The semantic similarity is {semantic_score:.1%}. You covered {concepts.coverage_percentage:.0%} "
            f"of the key concepts. Consider elaborating on: {', '.join(concepts.missing[:3]) if concepts.missing else 'N/A'}."
        ),
        GradeLevel.AVERAGE: (
            f"Your answer partially addresses the question. "
            f"The semantic similarity is {semantic_score:.1%}. You missed some important concepts: "
            f"{', '.join(concepts.missing[:3]) if concepts.missing else 'N/A'}. "
            f"Try to include more relevant details."
        ),
        GradeLevel.POOR: (
            f"Your answer needs significant improvement. "
            f"The semantic similarity is only {semantic_score:.1%}. "
            f"Key missing concepts include: {', '.join(concepts.missing[:5]) if concepts.missing else 'N/A'}. "
            f"Please review the topic and focus on the main concepts."
        )
    }
    
    return explanations.get(grade, "Evaluation complete.")


def generate_suggestions(
    grade: GradeLevel,
    concepts: ConceptMatch,
    length_ratio: float
) -> List[str]:
    """Generate improvement suggestions based on evaluation."""
    
    suggestions = []
    
    # Length-based suggestions
    if length_ratio < 0.5:
        suggestions.append("Your answer is too short. Try to provide more detailed explanations.")
    elif length_ratio > 2.0:
        suggestions.append("Your answer is quite lengthy. Focus on the key points for conciseness.")
    
    # Concept-based suggestions
    if concepts.missing:
        if len(concepts.missing) <= 2:
            suggestions.append(f"Include these concepts: {', '.join(concepts.missing)}")
        else:
            suggestions.append(f"Missing key concepts: {', '.join(concepts.missing[:3])}... and {len(concepts.missing)-3} more")
    
    # Grade-based suggestions
    if grade == GradeLevel.POOR:
        suggestions.append("Review the topic thoroughly before attempting again.")
        suggestions.append("Focus on understanding the fundamental concepts first.")
    elif grade == GradeLevel.AVERAGE:
        suggestions.append("Try to explain concepts in your own words while covering all key points.")
    elif grade == GradeLevel.GOOD:
        suggestions.append("Good foundation! Add more specific examples to strengthen your answer.")
    
    if not suggestions:
        suggestions.append("Great job! Keep up the excellent work.")
    
    return suggestions


# ========== API Endpoints ==========
@router.post("/", response_model=EvaluationResult)
async def evaluate_answer(request: EvaluationRequest):
    """
    Evaluate student answer against model answer using uploaded files.
    
    **Processing Pipeline:**
    1. Load uploaded files using evaluation_id
    2. OCR: Extract text from images/PDFs
    3. NLP: Preprocess and normalize text
    4. Semantic: Generate embeddings and calculate similarity
    5. Keywords: Extract and match key concepts
    6. Diagram: Compare diagrams if present
    7. Score: Apply hybrid scoring formula
    8. Return detailed results
    """
    
    import time
    start_time = time.time()
    
    # Verify evaluation exists
    eval_dir = os.path.join(settings.UPLOAD_DIR, "evaluations", request.evaluation_id)
    if not os.path.exists(eval_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Evaluation {request.evaluation_id} not found. Please upload files first."
        )
    
    try:
        # Import services
        from api.services.ocr_service import OCRService
        from api.services.nlp_service import NLPPreprocessor
        from api.services.semantic_service import SemanticAnalyzer
        from api.services.scoring_service import ScoringService
        
        # Initialize services
        ocr = OCRService()
        nlp = NLPPreprocessor()
        semantic = SemanticAnalyzer()
        scorer = ScoringService()
        
        # Find files in evaluation directory
        files = os.listdir(eval_dir)
        model_file = next((f for f in files if f.startswith("model_")), None)
        student_file = next((f for f in files if f.startswith("student_") or f == "student_answer.txt"), None)
        
        if not model_file or not student_file:
            raise HTTPException(
                status_code=400,
                detail="Missing model or student answer file"
            )
        
        model_path = os.path.join(eval_dir, model_file)
        student_path = os.path.join(eval_dir, student_file)
        
        # Step 1: Extract text using OCR (or read directly if text file)
        logger.info(f"Processing evaluation {request.evaluation_id}")
        
        if student_file.endswith('.txt'):
            with open(student_path, 'r', encoding='utf-8') as f:
                student_text = f.read()
        else:
            student_text = ocr.extract_text(student_path)
        
        model_text = ocr.extract_text(model_path)
        
        logger.info(f"Extracted text - Model: {len(model_text)} chars, Student: {len(student_text)} chars")
        
        # Step 2: NLP Preprocessing
        model_normalized = nlp.normalize_text(model_text)
        student_normalized = nlp.normalize_text(student_text)
        
        # Step 3: Semantic Analysis
        semantic_score = semantic.calculate_similarity(model_normalized, student_normalized)
        
        # Step 4: Keyword Analysis
        model_keywords = nlp.extract_keywords(model_text)
        student_keywords = nlp.extract_keywords(student_text)
        
        # Add custom keywords if provided
        if request.custom_keywords:
            model_keywords.extend(request.custom_keywords)
        
        keyword_score, matched, missing = scorer.calculate_keyword_coverage(
            model_keywords, student_keywords
        )
        
        # Step 5: Diagram Analysis (if applicable)
        diagram_score = 0.0
        if request.include_diagram:
            from api.services.diagram_service import DiagramEvaluator
            diagram_eval = DiagramEvaluator()
            # Look for diagram regions
            diagram_score = diagram_eval.evaluate(model_path, student_path)
        
        # Step 6: Calculate length ratio and penalty
        length_ratio = len(student_text) / max(len(model_text), 1)
        length_penalty = 0.0
        if length_ratio < settings.LENGTH_PENALTY_THRESHOLD:
            length_penalty = (settings.LENGTH_PENALTY_THRESHOLD - length_ratio) * settings.LENGTH_PENALTY_FACTOR
        
        # Step 7: Get dynamic weights and calculate final score
        weights = get_dynamic_weights(request.question_type)
        
        weighted_score = (
            semantic_score * weights["semantic"] +
            keyword_score * weights["keyword"] +
            diagram_score * weights["diagram"] -
            length_penalty
        )
        weighted_score = max(0.0, min(1.0, weighted_score))
        
        # Calculate marks
        obtained_marks = round(weighted_score * request.max_marks, 2)
        
        # Classify grade
        grade = classify_grade(weighted_score)
        
        # Prepare concepts
        concepts = ConceptMatch(
            matched=matched,
            missing=missing,
            coverage_percentage=keyword_score * 100
        )
        
        # Generate explanation and suggestions
        explanation = generate_explanation(grade, semantic_score, keyword_score, concepts)
        suggestions = generate_suggestions(grade, concepts, length_ratio)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Prepare score breakdown
        score_breakdown = ScoreBreakdown(
            semantic_score=round(semantic_score, 4),
            keyword_score=round(keyword_score, 4),
            diagram_score=round(diagram_score, 4) if request.include_diagram else None,
            length_penalty=round(length_penalty, 4),
            weighted_score=round(weighted_score, 4)
        )
        
        result = EvaluationResult(
            success=True,
            evaluation_id=request.evaluation_id,
            final_score=round(weighted_score * 100, 2),
            max_marks=request.max_marks,
            obtained_marks=obtained_marks,
            grade=grade,
            score_breakdown=score_breakdown,
            concepts=concepts,
            explanation=explanation,
            suggestions=suggestions,
            processing_time=round(processing_time, 3),
            timestamp=datetime.now().isoformat()
        )
        
        # Save result to storage
        from api.routes.results import save_result
        save_result(request.evaluation_id, result.model_dump())
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Evaluation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}"
        )


@router.post("/text", response_model=EvaluationResult)
async def evaluate_text_directly(request: TextEvaluationRequest):
    """
    Evaluate student answer against model answer using direct text input.
    No file upload required - useful for quick testing or text-based answers.
    
    **Use Case:**
    - When student answer is already in text format
    - For quick API testing
    - For integration with other systems
    """
    
    import time
    import uuid
    start_time = time.time()
    
    try:
        # Import services
        from api.services.nlp_service import NLPPreprocessor
        from api.services.semantic_service import SemanticAnalyzer
        from api.services.scoring_service import ScoringService
        
        # Initialize services
        nlp = NLPPreprocessor()
        semantic = SemanticAnalyzer()
        scorer = ScoringService()
        
        # Generate evaluation ID
        evaluation_id = str(uuid.uuid4())
        
        # NLP Preprocessing
        model_normalized = nlp.normalize_text(request.model_answer)
        student_normalized = nlp.normalize_text(request.student_answer)
        
        # Semantic Analysis
        semantic_score = semantic.calculate_similarity(model_normalized, student_normalized)
        
        # Keyword Analysis
        model_keywords = nlp.extract_keywords(request.model_answer)
        student_keywords = nlp.extract_keywords(request.student_answer)
        
        if request.custom_keywords:
            model_keywords.extend(request.custom_keywords)
        
        keyword_score, matched, missing = scorer.calculate_keyword_coverage(
            model_keywords, student_keywords
        )
        
        # Length analysis
        length_ratio = len(request.student_answer) / max(len(request.model_answer), 1)
        length_penalty = 0.0
        if length_ratio < settings.LENGTH_PENALTY_THRESHOLD:
            length_penalty = (settings.LENGTH_PENALTY_THRESHOLD - length_ratio) * settings.LENGTH_PENALTY_FACTOR
        
        # Get dynamic weights
        weights = get_dynamic_weights(request.question_type)
        
        # Calculate weighted score (no diagram for text-only)
        weighted_score = (
            semantic_score * (weights["semantic"] + weights["diagram"]) +
            keyword_score * weights["keyword"] -
            length_penalty
        )
        weighted_score = max(0.0, min(1.0, weighted_score))
        
        # Calculate marks
        obtained_marks = round(weighted_score * request.max_marks, 2)
        
        # Classify grade
        grade = classify_grade(weighted_score)
        
        # Prepare concepts
        concepts = ConceptMatch(
            matched=matched,
            missing=missing,
            coverage_percentage=keyword_score * 100
        )
        
        # Generate explanation and suggestions
        explanation = generate_explanation(grade, semantic_score, keyword_score, concepts)
        suggestions = generate_suggestions(grade, concepts, length_ratio)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Prepare score breakdown
        score_breakdown = ScoreBreakdown(
            semantic_score=round(semantic_score, 4),
            keyword_score=round(keyword_score, 4),
            diagram_score=None,
            length_penalty=round(length_penalty, 4),
            weighted_score=round(weighted_score, 4)
        )
        
        result = EvaluationResult(
            success=True,
            evaluation_id=evaluation_id,
            final_score=round(weighted_score * 100, 2),
            max_marks=request.max_marks,
            obtained_marks=obtained_marks,
            grade=grade,
            score_breakdown=score_breakdown,
            concepts=concepts,
            explanation=explanation,
            suggestions=suggestions,
            processing_time=round(processing_time, 3),
            timestamp=datetime.now().isoformat()
        )
        
        # Save result to storage
        from api.routes.results import save_result
        save_result(evaluation_id, result.model_dump())
        
        return result
        
    except Exception as e:
        logger.error(f"Text evaluation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}"
        )


@router.get("/weights")
async def get_scoring_weights():
    """
    Get current scoring weights for different question types.
    Useful for understanding how scores are calculated.
    """
    return {
        "success": True,
        "data": {
            "factual": get_dynamic_weights(QuestionType.FACTUAL),
            "descriptive": get_dynamic_weights(QuestionType.DESCRIPTIVE),
            "diagram": get_dynamic_weights(QuestionType.DIAGRAM),
            "mixed": get_dynamic_weights(QuestionType.MIXED)
        },
        "thresholds": {
            "excellent": settings.SEMANTIC_EXCELLENT_THRESHOLD,
            "good": settings.SEMANTIC_GOOD_THRESHOLD,
            "average": settings.SEMANTIC_AVERAGE_THRESHOLD
        }
    }
