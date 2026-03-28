"""
Evaluation Routes
==================
Handles the core evaluation logic - OCR, NLP, Semantic Analysis, and Scoring.
This is the main processing pipeline for answer evaluation.
"""

import os
import logging
import uuid
import tempfile
import shutil
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

import numpy as np
from fastapi import APIRouter, HTTPException, BackgroundTasks, File, UploadFile
from pydantic import BaseModel, Field, model_validator

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


class OCREngine(str, Enum):
    """Available OCR engines for text extraction."""
    ENSEMBLE = "ensemble"           # All 3 local engines in parallel (best accuracy, ~10-15s)
    EASYOCR = "easyocr"             # EasyOCR only (balanced, ~5s)
    TESSERACT = "tesseract"         # Tesseract only (fast, ~3s)
    PADDLEOCR = "paddleocr"         # PaddleOCR only (slower but good for layouts)
    SARVAM = "sarvam"               # Sarvam AI Cloud API (requires API key)


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
    ocr_engine: OCREngine = Field(
        default=OCREngine.EASYOCR,
        description=(
            "OCR engine to use for text extraction. "
            "Options: 'ensemble' (best accuracy, ~10-15s), 'easyocr' (balanced, ~5s), "
            "'tesseract' (fast, ~3s), 'paddleocr' (good for layouts), 'sarvam' (cloud API). "
            "Default: 'easyocr' for production, 'ensemble' for best accuracy."
        )
    )
    rubric_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Custom rubric configuration. Keys are dimension names "
            "(understanding, concept_coverage, terminology, structure, examples). "
            "Each value is a dict with 'weight' (0-1). Weights are auto-normalised. "
            "Example: {\"understanding\": {\"weight\": 0.50}, \"concept_coverage\": {\"weight\": 0.30}, \"terminology\": {\"weight\": 0.20}}"
        )
    )


class TextEvaluationRequest(BaseModel):
    """Request model for direct text evaluation (without file upload)."""
    model_answer: str = Field(..., min_length=10, description="The correct/model answer text")
    student_answer: str = Field(..., min_length=1, description="The student's answer text")
    question_type: QuestionType = Field(default=QuestionType.DESCRIPTIVE)
    max_marks: int = Field(default=10, ge=1, le=100)
    custom_keywords: Optional[List[str]] = Field(default=None)
    ocr_engine: OCREngine = Field(
        default=OCREngine.EASYOCR,
        description="OCR engine for reference (not used in direct text evaluation, but kept for consistency)"
    )
    rubric_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Custom rubric configuration. Keys are dimension names "
            "(understanding, concept_coverage, terminology, structure, examples). "
            "Each value is a dict with 'weight' (0-1). Weights are auto-normalised."
        )
    )


class ScoreBreakdown(BaseModel):
    """Detailed breakdown of scores."""
    semantic_score: float = Field(..., ge=0, le=1)
    concept_graph_score: Optional[float] = Field(default=None, ge=0, le=1)
    sentence_alignment_score: Optional[float] = Field(default=None, ge=0, le=1)
    keyword_score: float = Field(..., ge=0, le=1)
    diagram_score: Optional[float] = Field(default=None, ge=0, le=1)
    structural_score: Optional[float] = Field(default=None, ge=0, le=1)
    structure_bonus: Optional[float] = Field(default=None, ge=0, le=1)
    anti_gaming_penalty: Optional[float] = Field(default=None, ge=0, le=1)
    rubric_score: Optional[float] = Field(default=None, ge=0, le=1, description="Rubric-based weighted score (replaces legacy weighted_score when enabled)")
    bloom_modifier: Optional[float] = Field(default=None, ge=-1, le=1, description="Bloom's Taxonomy cognitive-level score modifier")
    length_penalty: float = Field(default=0, ge=0, le=1)
    weighted_score: float = Field(..., ge=0, le=1)


def _sanitize_numpy(obj):
    """Recursively convert numpy scalars/arrays to JSON-safe Python native types."""
    if isinstance(obj, dict):
        return {k: _sanitize_numpy(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_numpy(v) for v in obj]
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.str_):
        return str(obj)
    return obj


class ConceptMatch(BaseModel):
    """Matched and missing concepts."""
    matched: List[str]
    missing: List[str]
    coverage_percentage: float
    concept_graph_coverage: Optional[float] = Field(default=None, description="Per-concept coverage from graph analysis")
    concept_graph_details: Optional[List[Dict[str, Any]]] = Field(default=None, description="Per-concept match details")
    sentence_alignment_details: Optional[Dict[str, Any]] = Field(default=None, description="Sentence alignment matrix report")
    structural_analysis_details: Optional[Dict[str, Any]] = Field(default=None, description="Logical structure evaluation report")
    anti_gaming_details: Optional[Dict[str, Any]] = Field(default=None, description="Anti-gaming protection report")
    rubric_details: Optional[Dict[str, Any]] = Field(default=None, description="Rubric-based evaluation report with per-dimension scores")
    bloom_taxonomy_details: Optional[Dict[str, Any]] = Field(default=None, description="Bloom's Taxonomy cognitive-level analysis")
    confidence_details: Optional[Dict[str, Any]] = Field(default=None, description="Confidence & Reliability Index report")

    @model_validator(mode='before')
    @classmethod
    def _sanitize_numpy_fields(cls, data):
        """Convert numpy scalars/arrays to Python-native types in all dict/list fields."""
        if not isinstance(data, dict):
            return data
        _DICT_LIST_FIELDS = (
            'concept_graph_details', 'sentence_alignment_details',
            'structural_analysis_details', 'anti_gaming_details',
            'rubric_details', 'bloom_taxonomy_details', 'confidence_details',
        )
        for key in _DICT_LIST_FIELDS:
            if key in data and data[key] is not None:
                data[key] = _sanitize_numpy(data[key])
        return data


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


# ========== Multi-Question Models ==========

class QuestionPair(BaseModel):
    """A single question's model + student answer pair (for pre-segmented input)."""
    question_number: int = Field(..., ge=1, description="1-based question number")
    question_text: Optional[str] = Field(default=None, description="The question text (optional)")
    model_answer: str = Field(..., min_length=1, description="Model/expected answer for this question")
    student_answer: str = Field(default="", description="Student's answer (empty = unanswered)")
    max_marks: int = Field(default=10, ge=1, le=100, description="Marks for this question")


class MultiQuestionRequest(BaseModel):
    """Request model for per-question independent evaluation."""
    # Option A: pre-segmented question pairs
    questions: Optional[List[QuestionPair]] = Field(
        default=None,
        description="Pre-segmented question pairs. If provided, auto-segmentation is skipped."
    )
    # Option B: raw text → auto-segment
    model_answer: Optional[str] = Field(default=None, min_length=10, description="Full model answer text (auto-segmented)")
    student_answer: Optional[str] = Field(default=None, min_length=1, description="Full student answer text (auto-segmented)")
    # Shared settings
    question_type: QuestionType = Field(default=QuestionType.DESCRIPTIVE)
    total_max_marks: int = Field(default=10, ge=1, le=500, description="Total marks for the answer sheet")
    rubric_config: Optional[Dict[str, Any]] = Field(default=None)


class PerQuestionResult(BaseModel):
    """Evaluation result for a single question."""
    question_number: int
    question_text: Optional[str] = None
    model_answer_preview: str = Field(default="", description="First 200 chars of model answer")
    student_answer_preview: str = Field(default="", description="First 200 chars of student answer")
    max_marks: float
    obtained_marks: float
    final_score: float  # 0-100
    grade: GradeLevel
    score_breakdown: ScoreBreakdown
    concepts: ConceptMatch
    explanation: str
    suggestions: List[str]
    is_unanswered: bool = False


class MultiQuestionResult(BaseModel):
    """Complete multi-question evaluation result."""
    success: bool
    evaluation_id: str
    total_questions: int
    answered_questions: int
    unanswered_questions: int
    total_max_marks: float
    total_obtained_marks: float
    overall_percentage: float
    overall_grade: GradeLevel
    per_question: List[PerQuestionResult]
    segmentation_info: Optional[Dict[str, Any]] = None
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
    
    - Factual questions: Higher keyword + concept graph weight
    - Descriptive questions: Higher semantic + concept graph weight
    - Diagram questions: Include diagram evaluation weight
    - Concept graph weight ensures per-concept coverage is rewarded
    """
    weights = {
        QuestionType.FACTUAL: {
            "semantic": 0.20,
            "concept_graph": 0.25,
            "sentence_alignment": 0.20,
            "keyword": 0.25,
            "diagram": 0.10
        },
        QuestionType.DESCRIPTIVE: {
            "semantic": 0.20,
            "concept_graph": 0.30,
            "sentence_alignment": 0.25,
            "keyword": 0.10,
            "diagram": 0.15
        },
        QuestionType.DIAGRAM: {
            "semantic": 0.15,
            "concept_graph": 0.15,
            "sentence_alignment": 0.15,
            "keyword": 0.10,
            "diagram": 0.45
        },
        QuestionType.MIXED: {
            "semantic": settings.WEIGHT_SEMANTIC,
            "concept_graph": settings.WEIGHT_CONCEPT_GRAPH,
            "sentence_alignment": settings.WEIGHT_SENTENCE_ALIGNMENT,
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
        
        # Initialize services with user-selected OCR engine
        ocr = OCRService(engine=request.ocr_engine.value)
        nlp = NLPPreprocessor()
        semantic = SemanticAnalyzer()
        scorer = ScoringService()
        
        logger.info(f"Evaluation {request.evaluation_id} using OCR engine: {request.ocr_engine.value}")
        
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
        
        # Step 5: Concept Graph Analysis
        concept_graph_score = 0.0
        concept_graph_result = None
        if getattr(settings, 'ENABLE_CONCEPT_GRAPH', True):
            try:
                from api.services.concept_graph_service import ConceptGraphScorer
                cg_scorer = ConceptGraphScorer()
                concept_graph_result = cg_scorer.score(model_text, student_text)
                concept_graph_score = concept_graph_result.combined_score
                logger.info(f"Concept graph score: {concept_graph_score:.4f}")
            except Exception as e:
                logger.warning(f"Concept graph scoring failed: {e}")
                concept_graph_score = semantic_score  # fallback to semantic
        else:
            concept_graph_score = semantic_score  # fallback
        
        # Step 5b: Sentence Alignment Matrix Scoring
        sentence_alignment_score = 0.0
        sentence_alignment_result = None
        if getattr(settings, 'ENABLE_SENTENCE_ALIGNMENT', True):
            try:
                from api.services.sentence_alignment_service import SentenceAlignmentScorer
                sa_scorer = SentenceAlignmentScorer()
                sentence_alignment_result = sa_scorer.score(
                    model_text, student_text,
                    custom_keywords=request.custom_keywords,
                )
                sentence_alignment_score = sentence_alignment_result.combined_score
                logger.info(f"Sentence alignment score: {sentence_alignment_score:.4f}")
            except Exception as e:
                logger.warning(f"Sentence alignment scoring failed: {e}")
                sentence_alignment_score = semantic_score  # fallback
        else:
            sentence_alignment_score = semantic_score  # fallback
        
        # Step 5c: Structural Analysis (logical structure evaluation)
        structural_score_val = 0.0
        structure_bonus = 0.0
        structural_report = None
        if getattr(settings, 'ENABLE_STRUCTURAL_ANALYSIS', True):
            try:
                from api.services.structural_analysis_service import StructuralAnalyzer
                struct_analyzer = StructuralAnalyzer()
                structural_report = struct_analyzer.analyze(student_text)
                structural_score_val = structural_report.structural_score
                structure_bonus = structural_report.structure_bonus
                logger.info(f"Structural score: {structural_score_val:.4f}, bonus: {structure_bonus:.4f}")
            except Exception as e:
                logger.warning(f"Structural analysis failed: {e}")
        
        # Step 5d: Anti-Gaming Protection
        gaming_penalty = 0.0
        gaming_report = None
        if getattr(settings, 'ENABLE_ANTI_GAMING', True):
            try:
                from api.services.anti_gaming_service import AntiGamingAnalyzer
                ag_analyzer = AntiGamingAnalyzer()
                gaming_report = ag_analyzer.analyze(
                    student_text=student_text,
                    model_text=model_text,
                    keyword_score=keyword_score,
                    semantic_score=semantic_score,
                    matched_keywords=matched,
                )
                gaming_penalty = gaming_report.total_penalty
                if gaming_report.is_flagged:
                    logger.warning(f"Anti-gaming FLAGGED: penalty={gaming_penalty:.4f}, flags={gaming_report.flags}")
                else:
                    logger.info(f"Anti-gaming penalty: {gaming_penalty:.4f}")
            except Exception as e:
                logger.warning(f"Anti-gaming analysis failed: {e}")
        
        # Step 6: Diagram Analysis (if applicable)
        diagram_score = 0.0
        if request.include_diagram:
            from api.services.diagram_service import DiagramEvaluator
            diagram_eval = DiagramEvaluator()
            # Look for diagram regions
            diagram_score = diagram_eval.evaluate(model_path, student_path)
        
        # Step 7: Calculate length ratio and penalty
        length_ratio = len(student_text) / max(len(model_text), 1)
        length_penalty = 0.0
        if length_ratio < settings.LENGTH_PENALTY_THRESHOLD:
            length_penalty = (settings.LENGTH_PENALTY_THRESHOLD - length_ratio) * settings.LENGTH_PENALTY_FACTOR
        
        # Step 8: Get dynamic weights and calculate final score
        weights = get_dynamic_weights(request.question_type)
        
        # If concept graph is disabled, redistribute its weight
        if not getattr(settings, 'ENABLE_CONCEPT_GRAPH', True):
            cg_w = weights.get("concept_graph", 0)
            remaining = weights["semantic"] + weights.get("sentence_alignment", 0) + weights["keyword"]
            if remaining > 0:
                weights["semantic"] += cg_w * (weights["semantic"] / remaining)
                if weights.get("sentence_alignment", 0) > 0:
                    weights["sentence_alignment"] += cg_w * (weights["sentence_alignment"] / remaining)
                weights["keyword"] += cg_w * (weights["keyword"] / remaining)
            weights["concept_graph"] = 0
        
        # If sentence alignment is disabled, redistribute its weight
        if not getattr(settings, 'ENABLE_SENTENCE_ALIGNMENT', True):
            sa_w = weights.get("sentence_alignment", 0)
            remaining = weights["semantic"] + weights.get("concept_graph", 0) + weights["keyword"]
            if remaining > 0:
                weights["semantic"] += sa_w * (weights["semantic"] / remaining)
                if weights.get("concept_graph", 0) > 0:
                    weights["concept_graph"] += sa_w * (weights["concept_graph"] / remaining)
                weights["keyword"] += sa_w * (weights["keyword"] / remaining)
            weights["sentence_alignment"] = 0
        
        # If no diagram, redistribute weight
        if not request.include_diagram:
            d_w = weights["diagram"]
            remaining = (weights["semantic"] + weights.get("concept_graph", 0)
                         + weights.get("sentence_alignment", 0) + weights["keyword"])
            if remaining > 0:
                weights["semantic"] += d_w * (weights["semantic"] / remaining)
                if weights.get("concept_graph", 0) > 0:
                    weights["concept_graph"] += d_w * (weights["concept_graph"] / remaining)
                if weights.get("sentence_alignment", 0) > 0:
                    weights["sentence_alignment"] += d_w * (weights["sentence_alignment"] / remaining)
                weights["keyword"] += d_w * (weights["keyword"] / remaining)
            weights["diagram"] = 0
        
        weighted_score = (
            semantic_score * weights["semantic"] +
            concept_graph_score * weights.get("concept_graph", 0) +
            sentence_alignment_score * weights.get("sentence_alignment", 0) +
            keyword_score * weights["keyword"] +
            diagram_score * weights["diagram"] -
            length_penalty
        )
        # Apply structural bonus (additive, capped)
        weighted_score += structure_bonus
        # Apply anti-gaming penalty (subtractive, capped)
        weighted_score -= gaming_penalty
        weighted_score = max(0.0, min(1.0, weighted_score))
        
        # Step 9: Rubric-Based Scoring (Professional Board-Exam style)
        rubric_report = None
        rubric_final_score = None
        if getattr(settings, 'ENABLE_RUBRIC_SCORING', True):
            try:
                from api.services.rubric_scoring_service import RubricScorer
                rubric_scorer = RubricScorer()
                rubric_report = rubric_scorer.evaluate(
                    semantic_score=semantic_score,
                    keyword_score=keyword_score,
                    concept_graph_score=concept_graph_score if getattr(settings, 'ENABLE_CONCEPT_GRAPH', True) else None,
                    concept_graph_coverage=(
                        concept_graph_result.coverage_score * 100
                        if concept_graph_result and hasattr(concept_graph_result, 'coverage_score')
                        else None
                    ),
                    sentence_alignment_score=sentence_alignment_score if getattr(settings, 'ENABLE_SENTENCE_ALIGNMENT', True) else None,
                    structural_score=structural_score_val if getattr(settings, 'ENABLE_STRUCTURAL_ANALYSIS', True) else None,
                    structure_bonus=structure_bonus if getattr(settings, 'ENABLE_STRUCTURAL_ANALYSIS', True) else None,
                    diagram_score=diagram_score if request.include_diagram else None,
                    student_text=student_text,
                    model_text=model_text,
                    matched_keywords=matched,
                    missing_keywords=missing,
                    missing_concept_count=concept_graph_result.missing_count if concept_graph_result else len(missing),
                    total_concept_count=(
                        len(concept_graph_result.concept_matches) if concept_graph_result else len(matched) + len(missing)
                    ),
                    question_type=request.question_type.value,
                    rubric_config=request.rubric_config,
                )
                rubric_final_score = rubric_report.rubric_score
                # Apply gaming penalty and length penalty to rubric score too
                rubric_final_score = rubric_final_score - gaming_penalty - length_penalty
                rubric_final_score = max(0.0, min(1.0, rubric_final_score))
                # Rubric score becomes the authoritative score
                weighted_score = rubric_final_score
                logger.info(f"Rubric score: {rubric_report.rubric_score:.4f}, grade: {rubric_report.rubric_grade}")
            except Exception as e:
                logger.warning(f"Rubric scoring failed, using legacy weights: {e}")
        
        # Step 10: Bloom's Taxonomy Cognitive-Level Evaluation
        bloom_result = None
        bloom_modifier = 0.0
        if getattr(settings, 'ENABLE_BLOOM_TAXONOMY', True):
            try:
                from api.services.bloom_taxonomy_service import BloomTaxonomyAnalyzer
                bloom_analyzer = BloomTaxonomyAnalyzer()
                question_text = getattr(request, 'question_text', '') or ''
                bloom_result = bloom_analyzer.analyze(
                    question_text=question_text,
                    student_text=student_text,
                    model_text=model_text,
                )
                bloom_modifier = bloom_result.bloom_score_modifier
                weighted_score += bloom_modifier
                weighted_score = max(0.0, min(1.0, weighted_score))
                logger.info(
                    f"Bloom's Taxonomy: Q-level={bloom_result.question_bloom_name}, "
                    f"S-level={bloom_result.student_bloom_name}, modifier={bloom_modifier:+.4f}"
                )
            except Exception as e:
                logger.warning(f"Bloom's Taxonomy analysis failed: {e}")
        
        # Step 11: Confidence & Reliability Index
        confidence_result = None
        if getattr(settings, 'ENABLE_CONFIDENCE_INDEX', True):
            try:
                from api.services.confidence_service import ConfidenceAnalyzer
                confidence_analyzer = ConfidenceAnalyzer()
                confidence_result = confidence_analyzer.analyze(
                    semantic_score=semantic_score,
                    keyword_score=keyword_score,
                    concept_graph_score=concept_graph_score if getattr(settings, 'ENABLE_CONCEPT_GRAPH', True) else None,
                    sentence_alignment_score=sentence_alignment_score if getattr(settings, 'ENABLE_SENTENCE_ALIGNMENT', True) else None,
                    structural_score=structural_score_val if getattr(settings, 'ENABLE_STRUCTURAL_ANALYSIS', True) else None,
                    rubric_score=rubric_report.rubric_score if rubric_report else None,
                    length_ratio=length_ratio,
                    student_text=student_text,
                    model_text=model_text,
                    coverage_percentage=(
                        concept_graph_result.coverage_score * 100
                        if concept_graph_result and hasattr(concept_graph_result, 'coverage_score')
                        else keyword_score * 100
                    ),
                    gaming_penalty=gaming_penalty,
                    bloom_score_modifier=bloom_modifier,
                )
                if confidence_result.needs_manual_review:
                    logger.warning(
                        f"Confidence Index: {confidence_result.confidence_percentage:.1f}% — FLAGGED for manual review. "
                        f"Reasons: {confidence_result.review_reasons}"
                    )
                else:
                    logger.info(f"Confidence Index: {confidence_result.confidence_percentage:.1f}% ({confidence_result.confidence_label})")
            except Exception as e:
                logger.warning(f"Confidence Index analysis failed: {e}")
        
        # Calculate marks
        obtained_marks = round(weighted_score * request.max_marks, 2)
        
        # Classify grade
        grade = classify_grade(weighted_score)
        
        # Prepare concepts (merge keyword + concept graph + sentence alignment results)
        cg_coverage = None
        cg_details = None
        sa_details = None
        struct_details = None
        gaming_details = None
        rubric_details = None
        bloom_details = None
        confidence_details = None
        merged_missing = list(missing)
        if concept_graph_result and concept_graph_result.missing_concepts:
            # Add concept-graph-detected missing concepts
            for mc in concept_graph_result.missing_concepts:
                if mc.lower() not in {m.lower() for m in merged_missing}:
                    merged_missing.append(mc)
            cg_coverage = round(concept_graph_result.coverage_score * 100, 1)
            cg_details = [
                {"concept": m.model_concept, "similarity": m.similarity,
                 "status": m.status, "matched_with": m.best_student_match}
                for m in concept_graph_result.concept_matches[:20]
            ]
        
        # Add sentence-alignment-detected missing sentences
        if sentence_alignment_result and sentence_alignment_result.missing_sentences:
            for ms in sentence_alignment_result.missing_sentences[:5]:
                short = ms[:80] + ("..." if len(ms) > 80 else "")
                if short.lower() not in {m.lower() for m in merged_missing}:
                    merged_missing.append(short)
            from api.services.sentence_alignment_service import SentenceAlignmentScorer
            sa_reporter = SentenceAlignmentScorer()
            sa_details = sa_reporter.get_detailed_report(sentence_alignment_result)
        
        # Add structural analysis details
        if structural_report:
            from api.services.structural_analysis_service import StructuralAnalyzer
            struct_reporter = StructuralAnalyzer()
            struct_details = struct_reporter.get_detailed_report(structural_report)
        
        # Add anti-gaming details
        if gaming_report:
            from api.services.anti_gaming_service import AntiGamingAnalyzer
            ag_reporter = AntiGamingAnalyzer()
            gaming_details = ag_reporter.get_detailed_report(gaming_report)
        
        # Add rubric details
        if rubric_report:
            from api.services.rubric_scoring_service import RubricScorer
            rubric_reporter = RubricScorer()
            rubric_details = rubric_reporter.get_detailed_report(rubric_report)
        
        # Add Bloom's Taxonomy details
        if bloom_result:
            from api.services.bloom_taxonomy_service import BloomTaxonomyAnalyzer
            bloom_reporter = BloomTaxonomyAnalyzer()
            bloom_details = bloom_reporter.get_detailed_report(bloom_result)
        
        # Add Confidence & Reliability details
        if confidence_result:
            from api.services.confidence_service import ConfidenceAnalyzer
            conf_reporter = ConfidenceAnalyzer()
            confidence_details = conf_reporter.get_detailed_report(confidence_result)
        
        concepts = ConceptMatch(
            matched=matched,
            missing=merged_missing,
            coverage_percentage=keyword_score * 100,
            concept_graph_coverage=cg_coverage,
            concept_graph_details=cg_details,
            sentence_alignment_details=sa_details,
            structural_analysis_details=struct_details,
            anti_gaming_details=gaming_details,
            rubric_details=rubric_details,
            bloom_taxonomy_details=bloom_details,
            confidence_details=confidence_details,
        )
        
        # Generate explanation and suggestions
        explanation = generate_explanation(grade, semantic_score, keyword_score, concepts)
        suggestions = generate_suggestions(grade, concepts, length_ratio)
        
        # Add concept-graph-specific suggestions
        if concept_graph_result:
            if concept_graph_result.missing_count > 0:
                suggestions.append(
                    f"Missing {concept_graph_result.missing_count} key concept(s): "
                    f"{', '.join(concept_graph_result.missing_concepts[:3])}"
                )
            if concept_graph_result.verbosity_penalty > 0:
                suggestions.append(
                    "Your answer appears verbose — focus on key concepts rather than filler text."
                )
            if concept_graph_result.copy_penalty > 0:
                suggestions.append(
                    "Significant text overlap detected — try rephrasing in your own words."
                )
        
        # Add sentence-alignment-specific suggestions
        if sentence_alignment_result:
            if sentence_alignment_result.missing_matches > 0:
                suggestions.append(
                    f"{sentence_alignment_result.missing_matches} important model sentence(s) not addressed in your answer."
                )
            if sentence_alignment_result.order_score < 0.5:
                suggestions.append(
                    "Your answer's structure differs significantly from the expected order — try organizing your points logically."
                )
            if sentence_alignment_result.orphan_student_count > 2:
                suggestions.append(
                    "Several sentences in your answer don't relate to the expected content — stay focused on the question."
                )
        
        # Add structural-analysis-specific suggestions
        if structural_report and structural_report.suggestions:
            suggestions.extend(structural_report.suggestions)
        
        # Add anti-gaming-specific suggestions
        if gaming_report and gaming_report.is_flagged:
            if gaming_report.flags:
                suggestions.extend([f"\u26a0\ufe0f {flag}" for flag in gaming_report.flags[:5]])
            if gaming_report.warnings:
                suggestions.extend(gaming_report.warnings[:3])
        
        # Add Bloom's Taxonomy suggestions
        if bloom_result and bloom_result.suggestions:
            suggestions.extend(bloom_result.suggestions)
        
        # Add Confidence Index suggestions
        if confidence_result:
            if confidence_result.needs_manual_review:
                suggestions.append(
                    f"\u26a0\ufe0f Evaluation Confidence: {confidence_result.confidence_percentage:.0f}% ({confidence_result.confidence_label}) — flagged for manual review."
                )
            if confidence_result.review_reasons:
                for reason in confidence_result.review_reasons[:2]:
                    suggestions.append(f"\U0001f50d {reason}")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Prepare score breakdown
        score_breakdown = ScoreBreakdown(
            semantic_score=round(semantic_score, 4),
            concept_graph_score=round(concept_graph_score, 4) if getattr(settings, 'ENABLE_CONCEPT_GRAPH', True) else None,
            sentence_alignment_score=round(sentence_alignment_score, 4) if getattr(settings, 'ENABLE_SENTENCE_ALIGNMENT', True) else None,
            keyword_score=round(keyword_score, 4),
            diagram_score=round(diagram_score, 4) if request.include_diagram else None,
            structural_score=round(structural_score_val, 4) if getattr(settings, 'ENABLE_STRUCTURAL_ANALYSIS', True) else None,
            structure_bonus=round(structure_bonus, 4) if getattr(settings, 'ENABLE_STRUCTURAL_ANALYSIS', True) else None,
            anti_gaming_penalty=round(gaming_penalty, 4) if getattr(settings, 'ENABLE_ANTI_GAMING', True) else None,
            rubric_score=round(rubric_report.rubric_score, 4) if rubric_report else None,
            bloom_modifier=round(bloom_modifier, 4) if bloom_result else None,
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
        
        # Concept Graph Analysis
        concept_graph_score = 0.0
        concept_graph_result = None
        if getattr(settings, 'ENABLE_CONCEPT_GRAPH', True):
            try:
                from api.services.concept_graph_service import ConceptGraphScorer
                cg_scorer = ConceptGraphScorer()
                concept_graph_result = cg_scorer.score(request.model_answer, request.student_answer)
                concept_graph_score = concept_graph_result.combined_score
            except Exception as e:
                logger.warning(f"Concept graph scoring failed: {e}")
                concept_graph_score = semantic_score
        else:
            concept_graph_score = semantic_score
        
        # Sentence Alignment Matrix Scoring
        sentence_alignment_score = 0.0
        sentence_alignment_result = None
        if getattr(settings, 'ENABLE_SENTENCE_ALIGNMENT', True):
            try:
                from api.services.sentence_alignment_service import SentenceAlignmentScorer
                sa_scorer = SentenceAlignmentScorer()
                sentence_alignment_result = sa_scorer.score(
                    request.model_answer, request.student_answer,
                    custom_keywords=request.custom_keywords,
                )
                sentence_alignment_score = sentence_alignment_result.combined_score
            except Exception as e:
                logger.warning(f"Sentence alignment scoring failed: {e}")
                sentence_alignment_score = semantic_score
        else:
            sentence_alignment_score = semantic_score
        
        # Structural Analysis (logical structure evaluation)
        structural_score_val = 0.0
        structure_bonus = 0.0
        structural_report = None
        if getattr(settings, 'ENABLE_STRUCTURAL_ANALYSIS', True):
            try:
                from api.services.structural_analysis_service import StructuralAnalyzer
                struct_analyzer = StructuralAnalyzer()
                structural_report = struct_analyzer.analyze(request.student_answer)
                structural_score_val = structural_report.structural_score
                structure_bonus = structural_report.structure_bonus
                logger.info(f"Structural score: {structural_score_val:.4f}, bonus: {structure_bonus:.4f}")
            except Exception as e:
                logger.warning(f"Structural analysis failed: {e}")
        
        # Step 5d: Anti-Gaming Protection
        gaming_penalty = 0.0
        gaming_report = None
        if getattr(settings, 'ENABLE_ANTI_GAMING', True):
            try:
                from api.services.anti_gaming_service import AntiGamingAnalyzer
                ag_analyzer = AntiGamingAnalyzer()
                gaming_report = ag_analyzer.analyze(
                    student_text=request.student_answer,
                    model_text=request.model_answer,
                    keyword_score=keyword_score,
                    semantic_score=semantic_score,
                )
                gaming_penalty = min(
                    gaming_report.total_penalty,
                    getattr(settings, 'ANTI_GAMING_MAX_PENALTY', 0.40)
                )
                if gaming_report.is_flagged:
                    logger.warning(
                        f"Anti-gaming FLAGGED (penalty={gaming_penalty:.4f}): "
                        f"{gaming_report.flags}"
                    )
                else:
                    logger.info(f"Anti-gaming passed (penalty={gaming_penalty:.4f})")
            except Exception as e:
                logger.warning(f"Anti-gaming analysis failed: {e}")
        
        # Length analysis
        length_ratio = len(request.student_answer) / max(len(request.model_answer), 1)
        length_penalty = 0.0
        if length_ratio < settings.LENGTH_PENALTY_THRESHOLD:
            length_penalty = (settings.LENGTH_PENALTY_THRESHOLD - length_ratio) * settings.LENGTH_PENALTY_FACTOR
        
        # Get dynamic weights and redistribute diagram weight (no diagram for text-only)
        weights = get_dynamic_weights(request.question_type)
        d_w = weights["diagram"]
        remaining = (weights["semantic"] + weights.get("concept_graph", 0)
                     + weights.get("sentence_alignment", 0) + weights["keyword"])
        if remaining > 0:
            weights["semantic"] += d_w * (weights["semantic"] / remaining)
            if weights.get("concept_graph", 0) > 0:
                weights["concept_graph"] += d_w * (weights["concept_graph"] / remaining)
            if weights.get("sentence_alignment", 0) > 0:
                weights["sentence_alignment"] += d_w * (weights["sentence_alignment"] / remaining)
            weights["keyword"] += d_w * (weights["keyword"] / remaining)
        weights["diagram"] = 0
        
        # If concept graph is disabled, redistribute its weight too
        if not getattr(settings, 'ENABLE_CONCEPT_GRAPH', True):
            cg_w = weights.get("concept_graph", 0)
            rem2 = weights["semantic"] + weights.get("sentence_alignment", 0) + weights["keyword"]
            if rem2 > 0:
                weights["semantic"] += cg_w * (weights["semantic"] / rem2)
                if weights.get("sentence_alignment", 0) > 0:
                    weights["sentence_alignment"] += cg_w * (weights["sentence_alignment"] / rem2)
                weights["keyword"] += cg_w * (weights["keyword"] / rem2)
            weights["concept_graph"] = 0
        
        # If sentence alignment is disabled, redistribute its weight too
        if not getattr(settings, 'ENABLE_SENTENCE_ALIGNMENT', True):
            sa_w = weights.get("sentence_alignment", 0)
            rem3 = weights["semantic"] + weights.get("concept_graph", 0) + weights["keyword"]
            if rem3 > 0:
                weights["semantic"] += sa_w * (weights["semantic"] / rem3)
                if weights.get("concept_graph", 0) > 0:
                    weights["concept_graph"] += sa_w * (weights["concept_graph"] / rem3)
                weights["keyword"] += sa_w * (weights["keyword"] / rem3)
            weights["sentence_alignment"] = 0
        
        # Calculate weighted score
        weighted_score = (
            semantic_score * weights["semantic"] +
            concept_graph_score * weights.get("concept_graph", 0) +
            sentence_alignment_score * weights.get("sentence_alignment", 0) +
            keyword_score * weights["keyword"] -
            length_penalty
        )
        # Apply structural bonus (additive, capped)
        weighted_score += structure_bonus
        # Apply anti-gaming penalty (subtractive)
        weighted_score -= gaming_penalty
        weighted_score = max(0.0, min(1.0, weighted_score))
        
        # Step 9: Rubric-Based Scoring (Professional Board-Exam style)
        rubric_report = None
        rubric_final_score = None
        if getattr(settings, 'ENABLE_RUBRIC_SCORING', True):
            try:
                from api.services.rubric_scoring_service import RubricScorer
                rubric_scorer = RubricScorer()
                rubric_report = rubric_scorer.evaluate(
                    semantic_score=semantic_score,
                    keyword_score=keyword_score,
                    concept_graph_score=concept_graph_score if getattr(settings, 'ENABLE_CONCEPT_GRAPH', True) else None,
                    concept_graph_coverage=(
                        concept_graph_result.coverage_score * 100
                        if concept_graph_result and hasattr(concept_graph_result, 'coverage_score')
                        else None
                    ),
                    sentence_alignment_score=sentence_alignment_score if getattr(settings, 'ENABLE_SENTENCE_ALIGNMENT', True) else None,
                    structural_score=structural_score_val if getattr(settings, 'ENABLE_STRUCTURAL_ANALYSIS', True) else None,
                    structure_bonus=structure_bonus if getattr(settings, 'ENABLE_STRUCTURAL_ANALYSIS', True) else None,
                    diagram_score=None,
                    student_text=request.student_answer,
                    model_text=request.model_answer,
                    matched_keywords=matched,
                    missing_keywords=missing,
                    missing_concept_count=concept_graph_result.missing_count if concept_graph_result else len(missing),
                    total_concept_count=(
                        len(concept_graph_result.concept_matches) if concept_graph_result else len(matched) + len(missing)
                    ),
                    question_type=request.question_type.value,
                    rubric_config=request.rubric_config,
                )
                rubric_final_score = rubric_report.rubric_score
                # Apply gaming penalty and length penalty to rubric score too
                rubric_final_score = rubric_final_score - gaming_penalty - length_penalty
                rubric_final_score = max(0.0, min(1.0, rubric_final_score))
                # Rubric score becomes the authoritative score
                weighted_score = rubric_final_score
                logger.info(f"Rubric score: {rubric_report.rubric_score:.4f}, grade: {rubric_report.rubric_grade}")
            except Exception as e:
                logger.warning(f"Rubric scoring failed, using legacy weights: {e}")
        
        # Step 10: Bloom's Taxonomy Cognitive-Level Evaluation
        bloom_result = None
        bloom_modifier = 0.0
        if getattr(settings, 'ENABLE_BLOOM_TAXONOMY', True):
            try:
                from api.services.bloom_taxonomy_service import BloomTaxonomyAnalyzer
                bloom_analyzer = BloomTaxonomyAnalyzer()
                question_text = getattr(request, 'question_text', '') or ''
                bloom_result = bloom_analyzer.analyze(
                    question_text=question_text,
                    student_text=request.student_answer,
                    model_text=request.model_answer,
                )
                bloom_modifier = bloom_result.bloom_score_modifier
                weighted_score += bloom_modifier
                weighted_score = max(0.0, min(1.0, weighted_score))
                logger.info(
                    f"Bloom's Taxonomy: Q-level={bloom_result.question_bloom_name}, "
                    f"S-level={bloom_result.student_bloom_name}, modifier={bloom_modifier:+.4f}"
                )
            except Exception as e:
                logger.warning(f"Bloom's Taxonomy analysis failed: {e}")
        
        # Step 11: Confidence & Reliability Index
        confidence_result = None
        if getattr(settings, 'ENABLE_CONFIDENCE_INDEX', True):
            try:
                from api.services.confidence_service import ConfidenceAnalyzer
                confidence_analyzer = ConfidenceAnalyzer()
                confidence_result = confidence_analyzer.analyze(
                    semantic_score=semantic_score,
                    keyword_score=keyword_score,
                    concept_graph_score=concept_graph_score if getattr(settings, 'ENABLE_CONCEPT_GRAPH', True) else None,
                    sentence_alignment_score=sentence_alignment_score if getattr(settings, 'ENABLE_SENTENCE_ALIGNMENT', True) else None,
                    structural_score=structural_score_val if getattr(settings, 'ENABLE_STRUCTURAL_ANALYSIS', True) else None,
                    rubric_score=rubric_report.rubric_score if rubric_report else None,
                    length_ratio=length_ratio,
                    student_text=request.student_answer,
                    model_text=request.model_answer,
                    coverage_percentage=(
                        concept_graph_result.coverage_score * 100
                        if concept_graph_result and hasattr(concept_graph_result, 'coverage_score')
                        else keyword_score * 100
                    ),
                    gaming_penalty=gaming_penalty,
                    bloom_score_modifier=bloom_modifier,
                )
                if confidence_result.needs_manual_review:
                    logger.warning(
                        f"Confidence Index: {confidence_result.confidence_percentage:.1f}% — FLAGGED for manual review. "
                        f"Reasons: {confidence_result.review_reasons}"
                    )
                else:
                    logger.info(f"Confidence Index: {confidence_result.confidence_percentage:.1f}% ({confidence_result.confidence_label})")
            except Exception as e:
                logger.warning(f"Confidence Index analysis failed: {e}")
        
        # Calculate marks
        obtained_marks = round(weighted_score * request.max_marks, 2)
        
        # Classify grade
        grade = classify_grade(weighted_score)
        
        # Prepare concepts (merge keyword + concept graph + sentence alignment results)
        cg_coverage = None
        cg_details = None
        sa_details = None
        struct_details = None
        gaming_details = None
        rubric_details = None
        bloom_details = None
        confidence_details = None
        merged_missing = list(missing)
        if concept_graph_result and concept_graph_result.missing_concepts:
            for mc in concept_graph_result.missing_concepts:
                if mc.lower() not in {m.lower() for m in merged_missing}:
                    merged_missing.append(mc)
            cg_coverage = round(concept_graph_result.coverage_score * 100, 1)
            cg_details = [
                {"concept": m.model_concept, "similarity": m.similarity,
                 "status": m.status, "matched_with": m.best_student_match}
                for m in concept_graph_result.concept_matches[:20]
            ]
        
        # Add sentence-alignment-detected missing sentences
        if sentence_alignment_result and sentence_alignment_result.missing_sentences:
            for ms in sentence_alignment_result.missing_sentences[:5]:
                short = ms[:80] + ("..." if len(ms) > 80 else "")
                if short.lower() not in {m.lower() for m in merged_missing}:
                    merged_missing.append(short)
            from api.services.sentence_alignment_service import SentenceAlignmentScorer
            sa_reporter = SentenceAlignmentScorer()
            sa_details = sa_reporter.get_detailed_report(sentence_alignment_result)
        
        # Add structural analysis details
        if structural_report:
            from api.services.structural_analysis_service import StructuralAnalyzer
            struct_reporter = StructuralAnalyzer()
            struct_details = struct_reporter.get_detailed_report(structural_report)
        
        # Add anti-gaming details
        if gaming_report:
            from api.services.anti_gaming_service import AntiGamingAnalyzer
            ag_reporter = AntiGamingAnalyzer()
            gaming_details = ag_reporter.get_detailed_report(gaming_report)
        
        # Add rubric details
        if rubric_report:
            from api.services.rubric_scoring_service import RubricScorer
            rubric_reporter = RubricScorer()
            rubric_details = rubric_reporter.get_detailed_report(rubric_report)
        
        # Add Bloom's Taxonomy details
        if bloom_result:
            from api.services.bloom_taxonomy_service import BloomTaxonomyAnalyzer
            bloom_reporter = BloomTaxonomyAnalyzer()
            bloom_details = bloom_reporter.get_detailed_report(bloom_result)
        
        # Add Confidence & Reliability details
        if confidence_result:
            from api.services.confidence_service import ConfidenceAnalyzer
            conf_reporter = ConfidenceAnalyzer()
            confidence_details = conf_reporter.get_detailed_report(confidence_result)
        
        concepts = ConceptMatch(
            matched=matched,
            missing=merged_missing,
            coverage_percentage=keyword_score * 100,
            concept_graph_coverage=cg_coverage,
            concept_graph_details=cg_details,
            sentence_alignment_details=sa_details,
            structural_analysis_details=struct_details,
            anti_gaming_details=gaming_details,
            rubric_details=rubric_details,
            bloom_taxonomy_details=bloom_details,
            confidence_details=confidence_details,
        )
        
        # Generate explanation and suggestions
        explanation = generate_explanation(grade, semantic_score, keyword_score, concepts)
        suggestions = generate_suggestions(grade, concepts, length_ratio)
        
        # Add concept-graph-specific suggestions
        if concept_graph_result:
            if concept_graph_result.missing_count > 0:
                suggestions.append(
                    f"Missing {concept_graph_result.missing_count} key concept(s): "
                    f"{', '.join(concept_graph_result.missing_concepts[:3])}"
                )
            if concept_graph_result.verbosity_penalty > 0:
                suggestions.append(
                    "Your answer appears verbose — focus on key concepts rather than filler text."
                )
        
        # Add sentence-alignment-specific suggestions
        if sentence_alignment_result:
            if sentence_alignment_result.missing_matches > 0:
                suggestions.append(
                    f"{sentence_alignment_result.missing_matches} important model sentence(s) not addressed in your answer."
                )
            if sentence_alignment_result.order_score < 0.5:
                suggestions.append(
                    "Your answer's structure differs significantly from the expected order — try organizing your points logically."
                )
            if sentence_alignment_result.orphan_student_count > 2:
                suggestions.append(
                    "Several sentences in your answer don't relate to the expected content — stay focused on the question."
                )
        
        # Add structural-analysis-specific suggestions
        if structural_report and structural_report.suggestions:
            suggestions.extend(structural_report.suggestions)
        
        # Add anti-gaming-specific suggestions
        if gaming_report and gaming_report.is_flagged:
            if gaming_report.flags:
                suggestions.extend([f"\u26a0\ufe0f {flag}" for flag in gaming_report.flags[:5]])
            if gaming_report.warnings:
                suggestions.extend(gaming_report.warnings[:3])
        
        # Add rubric-dimension-specific suggestions
        if rubric_report and rubric_report.dimensions:
            for dim in rubric_report.dimensions:
                if dim.band in ("Poor", "Average"):
                    suggestions.append(f"\U0001f4ca {dim.display_name} ({dim.band}): {dim.feedback}")
        
        # Add Bloom's Taxonomy suggestions
        if bloom_result and bloom_result.suggestions:
            suggestions.extend(bloom_result.suggestions)
        
        # Add Confidence Index suggestions
        if confidence_result:
            if confidence_result.needs_manual_review:
                suggestions.append(
                    f"\u26a0\ufe0f Evaluation Confidence: {confidence_result.confidence_percentage:.0f}% ({confidence_result.confidence_label}) — flagged for manual review."
                )
            if confidence_result.review_reasons:
                for reason in confidence_result.review_reasons[:2]:
                    suggestions.append(f"\U0001f50d {reason}")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Prepare score breakdown
        score_breakdown = ScoreBreakdown(
            semantic_score=round(semantic_score, 4),
            concept_graph_score=round(concept_graph_score, 4) if getattr(settings, 'ENABLE_CONCEPT_GRAPH', True) else None,
            sentence_alignment_score=round(sentence_alignment_score, 4) if getattr(settings, 'ENABLE_SENTENCE_ALIGNMENT', True) else None,
            keyword_score=round(keyword_score, 4),
            diagram_score=None,
            structural_score=round(structural_score_val, 4) if getattr(settings, 'ENABLE_STRUCTURAL_ANALYSIS', True) else None,
            structure_bonus=round(structure_bonus, 4) if getattr(settings, 'ENABLE_STRUCTURAL_ANALYSIS', True) else None,
            anti_gaming_penalty=round(gaming_penalty, 4) if getattr(settings, 'ENABLE_ANTI_GAMING', True) else None,
            rubric_score=round(rubric_report.rubric_score, 4) if rubric_report else None,
            bloom_modifier=round(bloom_modifier, 4) if bloom_result else None,
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


# ========== Internal helper: evaluate a single question pair ==========

def _evaluate_single_question_sync(
    model_answer: str,
    student_answer: str,
    question_type: str = "descriptive",
    max_marks: float = 10,
    rubric_config=None,
    custom_keywords=None,
) -> dict:
    """
    Run the full evaluation pipeline on a single model/student answer pair.
    Returns a dict with all fields needed for PerQuestionResult.
    Designed to be called in a loop by the multi-question endpoint.
    """
    import time as _time
    start = _time.time()

    from api.services.nlp_service import NLPPreprocessor
    from api.services.semantic_service import SemanticAnalyzer
    from api.services.scoring_service import ScoringService

    nlp = NLPPreprocessor()
    semantic = SemanticAnalyzer()
    scorer_svc = ScoringService()

    # Unanswered detection
    if not student_answer or len(student_answer.strip()) < 3:
        return {
            "max_marks": max_marks,
            "obtained_marks": 0.0,
            "final_score": 0.0,
            "grade": "poor",
            "score_breakdown": {
                "semantic_score": 0.0, "keyword_score": 0.0,
                "concept_graph_score": None, "sentence_alignment_score": None,
                "diagram_score": None, "structural_score": None,
                "structure_bonus": None, "anti_gaming_penalty": None,
                "rubric_score": None, "bloom_modifier": None,
                "length_penalty": 0.0, "weighted_score": 0.0,
            },
            "concepts": {
                "matched": [], "missing": [],
                "coverage_percentage": 0.0,
            },
            "explanation": "No answer was provided for this question.",
            "suggestions": ["Attempt this question — even a partial answer earns marks."],
            "is_unanswered": True,
            "processing_time": round(_time.time() - start, 3),
        }

    # ── NLP ──────────────────────────────────────────────────────
    model_norm = nlp.normalize_text(model_answer)
    student_norm = nlp.normalize_text(student_answer)
    semantic_score = semantic.calculate_similarity(model_norm, student_norm)

    model_kws = nlp.extract_keywords(model_answer)
    student_kws = nlp.extract_keywords(student_answer)
    if custom_keywords:
        model_kws.extend(custom_keywords)
    keyword_score, matched, missing = scorer_svc.calculate_keyword_coverage(model_kws, student_kws)

    # ── Concept Graph ────────────────────────────────────────────
    concept_graph_score = 0.0
    concept_graph_result = None
    if getattr(settings, 'ENABLE_CONCEPT_GRAPH', True):
        try:
            from api.services.concept_graph_service import ConceptGraphScorer
            concept_graph_result = ConceptGraphScorer().score(model_answer, student_answer)
            concept_graph_score = concept_graph_result.combined_score
        except Exception:
            concept_graph_score = semantic_score
    else:
        concept_graph_score = semantic_score

    # ── Sentence Alignment ───────────────────────────────────────
    sentence_alignment_score = 0.0
    sentence_alignment_result = None
    if getattr(settings, 'ENABLE_SENTENCE_ALIGNMENT', True):
        try:
            from api.services.sentence_alignment_service import SentenceAlignmentScorer
            sentence_alignment_result = SentenceAlignmentScorer().score(
                model_answer, student_answer, custom_keywords=custom_keywords,
            )
            sentence_alignment_score = sentence_alignment_result.combined_score
        except Exception:
            sentence_alignment_score = semantic_score
    else:
        sentence_alignment_score = semantic_score

    # ── Structural Analysis ──────────────────────────────────────
    structural_score_val = 0.0
    structure_bonus = 0.0
    structural_report = None
    if getattr(settings, 'ENABLE_STRUCTURAL_ANALYSIS', True):
        try:
            from api.services.structural_analysis_service import StructuralAnalyzer
            structural_report = StructuralAnalyzer().analyze(student_answer)
            structural_score_val = structural_report.structural_score
            structure_bonus = structural_report.structure_bonus
        except Exception:
            pass

    # ── Anti-Gaming ──────────────────────────────────────────────
    gaming_penalty = 0.0
    gaming_report = None
    if getattr(settings, 'ENABLE_ANTI_GAMING', True):
        try:
            from api.services.anti_gaming_service import AntiGamingAnalyzer
            gaming_report = AntiGamingAnalyzer().analyze(
                student_text=student_answer, model_text=model_answer,
                keyword_score=keyword_score, semantic_score=semantic_score,
            )
            gaming_penalty = min(
                gaming_report.total_penalty,
                getattr(settings, 'ANTI_GAMING_MAX_PENALTY', 0.40),
            )
        except Exception:
            pass

    # ── Length Penalty ────────────────────────────────────────────
    length_ratio = len(student_answer) / max(len(model_answer), 1)
    length_penalty = 0.0
    if length_ratio < settings.LENGTH_PENALTY_THRESHOLD:
        length_penalty = (settings.LENGTH_PENALTY_THRESHOLD - length_ratio) * settings.LENGTH_PENALTY_FACTOR

    # ── Weighted Score ───────────────────────────────────────────
    qt_enum = QuestionType(question_type) if question_type in [e.value for e in QuestionType] else QuestionType.DESCRIPTIVE
    weights = get_dynamic_weights(qt_enum)
    # Redistribute diagram weight (text-only)
    d_w = weights["diagram"]
    remaining = weights["semantic"] + weights.get("concept_graph", 0) + weights.get("sentence_alignment", 0) + weights["keyword"]
    if remaining > 0:
        weights["semantic"] += d_w * (weights["semantic"] / remaining)
        if weights.get("concept_graph", 0) > 0:
            weights["concept_graph"] += d_w * (weights["concept_graph"] / remaining)
        if weights.get("sentence_alignment", 0) > 0:
            weights["sentence_alignment"] += d_w * (weights["sentence_alignment"] / remaining)
        weights["keyword"] += d_w * (weights["keyword"] / remaining)
    weights["diagram"] = 0
    if not getattr(settings, 'ENABLE_CONCEPT_GRAPH', True):
        cg_w = weights.get("concept_graph", 0)
        rem2 = weights["semantic"] + weights.get("sentence_alignment", 0) + weights["keyword"]
        if rem2 > 0:
            weights["semantic"] += cg_w * (weights["semantic"] / rem2)
            if weights.get("sentence_alignment", 0) > 0:
                weights["sentence_alignment"] += cg_w * (weights["sentence_alignment"] / rem2)
            weights["keyword"] += cg_w * (weights["keyword"] / rem2)
        weights["concept_graph"] = 0
    if not getattr(settings, 'ENABLE_SENTENCE_ALIGNMENT', True):
        sa_w = weights.get("sentence_alignment", 0)
        rem3 = weights["semantic"] + weights.get("concept_graph", 0) + weights["keyword"]
        if rem3 > 0:
            weights["semantic"] += sa_w * (weights["semantic"] / rem3)
            if weights.get("concept_graph", 0) > 0:
                weights["concept_graph"] += sa_w * (weights["concept_graph"] / rem3)
            weights["keyword"] += sa_w * (weights["keyword"] / rem3)
        weights["sentence_alignment"] = 0

    weighted_score = (
        semantic_score * weights["semantic"]
        + concept_graph_score * weights.get("concept_graph", 0)
        + sentence_alignment_score * weights.get("sentence_alignment", 0)
        + keyword_score * weights["keyword"]
        - length_penalty
    )
    weighted_score += structure_bonus
    weighted_score -= gaming_penalty
    weighted_score = max(0.0, min(1.0, weighted_score))

    # ── Rubric Scoring ───────────────────────────────────────────
    rubric_report = None
    if getattr(settings, 'ENABLE_RUBRIC_SCORING', True):
        try:
            from api.services.rubric_scoring_service import RubricScorer
            rubric_report = RubricScorer().evaluate(
                semantic_score=semantic_score,
                keyword_score=keyword_score,
                concept_graph_score=concept_graph_score if getattr(settings, 'ENABLE_CONCEPT_GRAPH', True) else None,
                concept_graph_coverage=(
                    concept_graph_result.coverage_score * 100
                    if concept_graph_result and hasattr(concept_graph_result, 'coverage_score') else None
                ),
                sentence_alignment_score=sentence_alignment_score if getattr(settings, 'ENABLE_SENTENCE_ALIGNMENT', True) else None,
                structural_score=structural_score_val if getattr(settings, 'ENABLE_STRUCTURAL_ANALYSIS', True) else None,
                structure_bonus=structure_bonus if getattr(settings, 'ENABLE_STRUCTURAL_ANALYSIS', True) else None,
                diagram_score=None,
                student_text=student_answer,
                model_text=model_answer,
                matched_keywords=matched,
                missing_keywords=missing,
                missing_concept_count=concept_graph_result.missing_count if concept_graph_result else len(missing),
                total_concept_count=(
                    len(concept_graph_result.concept_matches) if concept_graph_result else len(matched) + len(missing)
                ),
                question_type=question_type,
                rubric_config=rubric_config,
            )
            rubric_final = rubric_report.rubric_score - gaming_penalty - length_penalty
            weighted_score = max(0.0, min(1.0, rubric_final))
        except Exception:
            pass

    # ── Bloom's Taxonomy ─────────────────────────────────────────
    bloom_result = None
    bloom_modifier = 0.0
    if getattr(settings, 'ENABLE_BLOOM_TAXONOMY', True):
        try:
            from api.services.bloom_taxonomy_service import BloomTaxonomyAnalyzer
            bloom_result = BloomTaxonomyAnalyzer().analyze(
                question_text='',
                student_text=student_answer,
                model_text=model_answer,
            )
            bloom_modifier = bloom_result.bloom_score_modifier
            weighted_score += bloom_modifier
            weighted_score = max(0.0, min(1.0, weighted_score))
        except Exception:
            pass

    # ── Confidence & Reliability Index ───────────────────────────
    confidence_result = None
    if getattr(settings, 'ENABLE_CONFIDENCE_INDEX', True):
        try:
            from api.services.confidence_service import ConfidenceAnalyzer
            confidence_result = ConfidenceAnalyzer().analyze(
                semantic_score=semantic_score,
                keyword_score=keyword_score,
                concept_graph_score=concept_graph_score if getattr(settings, 'ENABLE_CONCEPT_GRAPH', True) else None,
                sentence_alignment_score=sentence_alignment_score if getattr(settings, 'ENABLE_SENTENCE_ALIGNMENT', True) else None,
                structural_score=structural_score_val if getattr(settings, 'ENABLE_STRUCTURAL_ANALYSIS', True) else None,
                rubric_score=rubric_report.rubric_score if rubric_report else None,
                length_ratio=length_ratio,
                student_text=student_answer,
                model_text=model_answer,
                coverage_percentage=(
                    concept_graph_result.coverage_score * 100
                    if concept_graph_result and hasattr(concept_graph_result, 'coverage_score')
                    else keyword_score * 100
                ),
                gaming_penalty=gaming_penalty,
                bloom_score_modifier=bloom_modifier,
            )
        except Exception:
            pass

    obtained_marks = round(weighted_score * max_marks, 2)
    grade = classify_grade(weighted_score)

    # ── Concepts & details ───────────────────────────────────────
    cg_coverage = None
    merged_missing = list(missing)
    if concept_graph_result and concept_graph_result.missing_concepts:
        for mc in concept_graph_result.missing_concepts:
            if mc.lower() not in {m.lower() for m in merged_missing}:
                merged_missing.append(mc)
        cg_coverage = round(concept_graph_result.coverage_score * 100, 1)

    # Rubric details
    rubric_details = None
    if rubric_report:
        try:
            from api.services.rubric_scoring_service import RubricScorer
            rubric_details = RubricScorer().get_detailed_report(rubric_report)
        except Exception:
            pass

    # Bloom's Taxonomy details
    bloom_details = None
    if bloom_result:
        try:
            from api.services.bloom_taxonomy_service import BloomTaxonomyAnalyzer
            bloom_details = BloomTaxonomyAnalyzer().get_detailed_report(bloom_result)
        except Exception:
            pass

    # Confidence details
    confidence_details = None
    if confidence_result:
        try:
            from api.services.confidence_service import ConfidenceAnalyzer
            confidence_details = ConfidenceAnalyzer().get_detailed_report(confidence_result)
        except Exception:
            pass

    concepts_dict = {
        "matched": matched,
        "missing": merged_missing,
        "coverage_percentage": round(keyword_score * 100, 1),
        "concept_graph_coverage": cg_coverage,
        "rubric_details": rubric_details,
        "bloom_taxonomy_details": bloom_details,
        "confidence_details": confidence_details,
    }

    # ── Explanation & suggestions ────────────────────────────────
    concepts_obj = ConceptMatch(
        matched=matched, missing=merged_missing,
        coverage_percentage=keyword_score * 100,
    )
    explanation = generate_explanation(grade, semantic_score, keyword_score, concepts_obj)
    suggestions = generate_suggestions(grade, concepts_obj, length_ratio)
    if concept_graph_result and concept_graph_result.missing_count > 0:
        suggestions.append(
            f"Missing {concept_graph_result.missing_count} key concept(s): "
            f"{', '.join(concept_graph_result.missing_concepts[:3])}"
        )
    if rubric_report and rubric_report.dimensions:
        for dim in rubric_report.dimensions:
            if dim.band in ("Poor", "Average"):
                suggestions.append(f"\U0001f4ca {dim.display_name} ({dim.band}): {dim.feedback}")
    if bloom_result and bloom_result.suggestions:
        suggestions.extend(bloom_result.suggestions)
    if confidence_result:
        if confidence_result.needs_manual_review:
            suggestions.append(
                f"\u26a0\ufe0f Evaluation Confidence: {confidence_result.confidence_percentage:.0f}% ({confidence_result.confidence_label}) — flagged for manual review."
            )
        if confidence_result.review_reasons:
            for reason in confidence_result.review_reasons[:2]:
                suggestions.append(f"\U0001f50d {reason}")

    # ── Build score breakdown dict ───────────────────────────────
    sb = {
        "semantic_score": round(semantic_score, 4),
        "keyword_score": round(keyword_score, 4),
        "concept_graph_score": round(concept_graph_score, 4) if getattr(settings, 'ENABLE_CONCEPT_GRAPH', True) else None,
        "sentence_alignment_score": round(sentence_alignment_score, 4) if getattr(settings, 'ENABLE_SENTENCE_ALIGNMENT', True) else None,
        "diagram_score": None,
        "structural_score": round(structural_score_val, 4) if getattr(settings, 'ENABLE_STRUCTURAL_ANALYSIS', True) else None,
        "structure_bonus": round(structure_bonus, 4) if getattr(settings, 'ENABLE_STRUCTURAL_ANALYSIS', True) else None,
        "anti_gaming_penalty": round(gaming_penalty, 4) if getattr(settings, 'ENABLE_ANTI_GAMING', True) else None,
        "rubric_score": round(rubric_report.rubric_score, 4) if rubric_report else None,
        "bloom_modifier": round(bloom_modifier, 4) if bloom_result else None,
        "length_penalty": round(length_penalty, 4),
        "weighted_score": round(weighted_score, 4),
    }

    return {
        "max_marks": max_marks,
        "obtained_marks": obtained_marks,
        "final_score": round(weighted_score * 100, 2),
        "grade": grade.value if hasattr(grade, 'value') else grade,
        "score_breakdown": sb,
        "concepts": concepts_dict,
        "explanation": explanation,
        "suggestions": suggestions,
        "is_unanswered": False,
        "processing_time": round(_time.time() - start, 3),
    }


# ========== Multi-Question Endpoint ==========

@router.post("/text/multi", response_model=MultiQuestionResult)
async def evaluate_multi_question(request: MultiQuestionRequest):
    """
    Per-question independent evaluation.

    **Option A — Pre-segmented:** Supply `questions` array with model+student pairs.
    **Option B — Auto-segment:** Supply `model_answer` + `student_answer` raw text
    and the system auto-detects question boundaries (Q1, Q2, … patterns).

    Returns per-question breakdown + aggregate summary.
    """
    import time
    import uuid
    start_time = time.time()

    try:
        evaluation_id = str(uuid.uuid4())
        question_type_str = request.question_type.value

        # ── Build question pairs ─────────────────────────────────
        pairs: List[Dict[str, Any]] = []

        if request.questions and len(request.questions) > 0:
            # Option A: pre-segmented
            for qp in request.questions:
                pairs.append({
                    "question_number": qp.question_number,
                    "question_text": qp.question_text,
                    "model_answer": qp.model_answer,
                    "student_answer": qp.student_answer,
                    "max_marks": qp.max_marks,
                })
            seg_info = {"method": "pre_segmented", "total_questions": len(pairs), "confidence": 1.0}
        elif request.model_answer and request.student_answer:
            # Option B: auto-segment
            from api.services.question_segmentation_service import QuestionSegmenter, align_segments
            segmenter = QuestionSegmenter()
            pair_data = segmenter.segment_pair(request.model_answer, request.student_answer)

            model_result = pair_data["model_result"]
            student_result = pair_data["student_result"]
            aligned = pair_data["aligned_pairs"]

            # Distribute marks proportionally
            n_q = len(aligned) or 1
            marks_per_q = round(request.total_max_marks / n_q, 2)

            for ap in aligned:
                qnum = ap["question_number"]
                m_seg = ap.get("model_segment")
                s_seg = ap.get("student_segment")
                m_text = m_seg.text if m_seg else ""
                s_text = s_seg.text if s_seg else ""
                # Use marks from model segment if detected
                q_marks = m_seg.marks if (m_seg and m_seg.marks) else marks_per_q
                pairs.append({
                    "question_number": qnum,
                    "question_text": None,
                    "model_answer": m_text,
                    "student_answer": s_text,
                    "max_marks": q_marks,
                })

            seg_info = {
                "method": f"auto:{model_result.method}/{student_result.method}",
                "model_questions": model_result.total_questions,
                "student_questions": student_result.total_questions,
                "total_questions": len(pairs),
                "confidence": round(
                    min(model_result.confidence, student_result.confidence), 3
                ),
                "warnings": model_result.warnings + student_result.warnings,
                "model_segments": QuestionSegmenter.get_segment_summary(model_result),
                "student_segments": QuestionSegmenter.get_segment_summary(student_result),
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Provide either 'questions' array or both 'model_answer' and 'student_answer' text.",
            )

        if len(pairs) == 0:
            raise HTTPException(status_code=400, detail="No questions found to evaluate.")

        # ── Evaluate each question independently ─────────────────
        per_question_results: List[PerQuestionResult] = []
        total_obtained = 0.0
        total_max = 0.0
        answered = 0
        unanswered = 0

        for pair in pairs:
            res = _evaluate_single_question_sync(
                model_answer=pair["model_answer"],
                student_answer=pair["student_answer"],
                question_type=question_type_str,
                max_marks=pair["max_marks"],
                rubric_config=request.rubric_config,
            )

            pqr = PerQuestionResult(
                question_number=pair["question_number"],
                question_text=pair.get("question_text"),
                model_answer_preview=pair["model_answer"][:200],
                student_answer_preview=pair["student_answer"][:200],
                max_marks=pair["max_marks"],
                obtained_marks=res["obtained_marks"],
                final_score=res["final_score"],
                grade=res["grade"],
                score_breakdown=ScoreBreakdown(**res["score_breakdown"]),
                concepts=ConceptMatch(**{
                    k: v for k, v in res["concepts"].items()
                    if k in ConceptMatch.model_fields
                }),
                explanation=res["explanation"],
                suggestions=res["suggestions"],
                is_unanswered=res["is_unanswered"],
            )
            per_question_results.append(pqr)
            total_obtained += res["obtained_marks"]
            total_max += pair["max_marks"]
            if res["is_unanswered"]:
                unanswered += 1
            else:
                answered += 1

        overall_pct = round((total_obtained / max(total_max, 1)) * 100, 2)
        overall_grade = classify_grade(total_obtained / max(total_max, 1))

        processing_time = round(time.time() - start_time, 3)

        result = MultiQuestionResult(
            success=True,
            evaluation_id=evaluation_id,
            total_questions=len(per_question_results),
            answered_questions=answered,
            unanswered_questions=unanswered,
            total_max_marks=total_max,
            total_obtained_marks=round(total_obtained, 2),
            overall_percentage=overall_pct,
            overall_grade=overall_grade,
            per_question=per_question_results,
            segmentation_info=seg_info if request.model_answer else None,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
        )

        # Save result
        from api.routes.results import save_result
        save_result(evaluation_id, result.model_dump())

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multi-question evaluation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Multi-question evaluation failed: {str(e)}")


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


class OCRTestRequest(BaseModel):
    """Request model for OCR comparison test."""
    evaluation_id: str = Field(..., description="Evaluation ID with uploaded images")
    test_model_answer: bool = Field(default=True, description="Test the model answer image")
    test_student_answer: bool = Field(default=True, description="Test the student answer image")
    ocr_engine: OCREngine = Field(
        default=OCREngine.EASYOCR,
        description="OCR engine to test (compare with Sarvam if available)"
    )


@router.post("/test-ocr")
async def test_ocr_comparison(request: OCRTestRequest):
    """
    Test and compare OCR results between Sarvam AI and current OCR engine.
    
    This endpoint allows you to compare the accuracy of Sarvam AI's vision OCR 
    against the current OCR engine (EasyOCR) for the uploaded images.
    
    **Returns:**
    - Results from both OCR engines
    - Character count comparison
    - Recommendation on which engine performed better
    """
    
    # Verify evaluation exists
    eval_dir = os.path.join(settings.UPLOAD_DIR, "evaluations", request.evaluation_id)
    if not os.path.exists(eval_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Evaluation {request.evaluation_id} not found. Please upload files first."
        )
    
    try:
        from api.services.ocr_service import OCRService
        
        # Find uploaded files
        files = os.listdir(eval_dir)
        model_files = [f for f in files if f.startswith("model_")]
        student_files = [f for f in files if f.startswith("student_")]
        
        results = {
            "evaluation_id": request.evaluation_id,
            "model_answer_comparison": None,
            "student_answer_comparison": None,
            "summary": {}
        }
        
        # Initialize OCR service with selected engine
        ocr = OCRService(engine=request.ocr_engine.value)
        
        logger.info(f"OCR Test using engine: {request.ocr_engine.value}")
        
        # Test model answer if requested
        if request.test_model_answer and model_files:
            model_path = os.path.join(eval_dir, model_files[0])
            logger.info(f"Testing OCR on model answer: {model_path}")
            results["model_answer_comparison"] = ocr.extract_with_sarvam_test(model_path)
        
        # Test student answer if requested
        if request.test_student_answer and student_files:
            student_path = os.path.join(eval_dir, student_files[0])
            logger.info(f"Testing OCR on student answer: {student_path}")
            results["student_answer_comparison"] = ocr.extract_with_sarvam_test(student_path)
        
        # Generate summary
        total_current = 0
        total_sarvam = 0
        
        if results["model_answer_comparison"]:
            comp = results["model_answer_comparison"].get("comparison", {})
            total_current += comp.get("current_engine_chars", 0)
            total_sarvam += comp.get("sarvam_chars", 0)
        
        if results["student_answer_comparison"]:
            comp = results["student_answer_comparison"].get("comparison", {})
            total_current += comp.get("current_engine_chars", 0)
            total_sarvam += comp.get("sarvam_chars", 0)
        
        results["summary"] = {
            "total_current_engine_chars": total_current,
            "total_sarvam_chars": total_sarvam,
            "overall_difference": total_sarvam - total_current,
            "overall_recommendation": "sarvam" if total_sarvam > total_current else "current_engine",
            "note": "More characters generally indicates better text extraction, but quality matters too. Review the actual text content for accuracy."
        }
        
        return {
            "success": True,
            "message": "OCR comparison complete",
            "data": results
        }
        
    except Exception as e:
        logger.error(f"OCR test failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"OCR test failed: {str(e)}"
        )


@router.post("/test-sarvam-image")
async def test_sarvam_with_image(
    image: UploadFile = File(..., description="Handwritten image to test OCR (PNG, JPG, JPEG, PDF)")
):
    """
    Upload a handwritten image and test Sarvam AI OCR extraction.
    
    This endpoint allows you to directly upload an image and see:
    - Text extracted by Sarvam AI
    - Text extracted by EasyOCR (current engine)
    - Comparison of both results
    
    **Supported formats:** PNG, JPG, JPEG, PDF
    
    **Returns:**
    - Extracted text from both engines
    - Character count comparison
    - Recommendation on which engine performed better
    """
    
    # Validate file type
    allowed_extensions = {".png", ".jpg", ".jpeg", ".pdf", ".webp", ".bmp", ".tiff"}
    file_ext = os.path.splitext(image.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Create temp directory to store the uploaded file
    temp_dir = tempfile.mkdtemp(prefix="sarvam_test_")
    file_path = os.path.join(temp_dir, f"test_image{file_ext}")
    
    try:
        # Save uploaded file
        logger.info(f"Saving uploaded file: {image.filename}")
        with open(file_path, "wb") as f:
            content = await image.read()
            f.write(content)
        
        logger.info(f"File saved to: {file_path} ({len(content)} bytes)")
        
        from api.services.ocr_service import OCRService
        
        # Initialize OCR service
        ocr = OCRService()
        
        # Get comparison results
        comparison_result = ocr.extract_with_sarvam_test(file_path)
        
        return {
            "success": True,
            "message": "Sarvam AI OCR test complete",
            "filename": image.filename,
            "file_size": len(content),
            "data": {
                "sarvam_result": comparison_result.get("sarvam_result", ""),
                "easyocr_result": comparison_result.get("current_engine_result", ""),
                "sarvam_error": comparison_result.get("sarvam_error"),
                "comparison": comparison_result.get("comparison", {}),
                "recommendation": comparison_result.get("comparison", {}).get("recommended", "unknown")
            }
        }
        
    except Exception as e:
        logger.error(f"Sarvam OCR test failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"OCR test failed: {str(e)}"
        )
    
    finally:
        # Clean up temp directory
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temp directory: {temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to clean up temp dir {temp_dir}: {e}")


@router.get("/rubric-presets")
async def get_rubric_presets():
    """
    Return available rubric presets for the frontend.
    Each preset contains dimension names, display names, default weights,
    and a description of what the preset is best suited for.
    """
    try:
        from api.services.rubric_scoring_service import RUBRIC_PRESETS, DEFAULT_RUBRIC
        
        presets = {}
        for preset_name, dimensions_dict in RUBRIC_PRESETS.items():
            presets[preset_name] = {
                "name": preset_name,
                "description": {
                    "factual": "Best for factual / definition-based questions — emphasises concept coverage and terminology.",
                    "descriptive": "Best for essay-style / descriptive questions — emphasises understanding and structure.",
                    "diagram": "Best for diagram-based questions — gives weight to visual interpretation.",
                    "mixed": "Balanced preset for mixed-type questions.",
                }.get(preset_name, "Custom rubric preset."),
                "dimensions": {
                    dim_name: {
                        "display_name": dim_data.get("display_name", dim_name),
                        "weight": dim_data.get("weight", 0.2),
                        "weight_pct": round(dim_data.get("weight", 0.2) * 100),
                    }
                    for dim_name, dim_data in dimensions_dict.items()
                },
            }
        
        default_dims = {
            dim_name: {
                "display_name": dim_data.get("display_name", dim_name),
                "weight": dim_data.get("weight", 0.2),
                "weight_pct": round(dim_data.get("weight", 0.2) * 100),
            }
            for dim_name, dim_data in DEFAULT_RUBRIC.items()
        }
        
        return {
            "success": True,
            "default": {
                "name": "default",
                "description": "Default balanced rubric used when no preset or custom config is provided.",
                "dimensions": default_dims,
            },
            "presets": presets,
        }
    except Exception as e:
        logger.error(f"Failed to load rubric presets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load rubric presets: {str(e)}")
