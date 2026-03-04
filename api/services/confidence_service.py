"""
Confidence & Reliability Index Service
========================================
Computes a multi-factor confidence score for every evaluation to indicate
how *trustworthy* the automated result is.  When confidence drops below a
configurable threshold the evaluation is flagged for **manual review**.

Confidence Formula:
  evaluation_confidence =
      embedding_stability  × 0.30
    + keyword_consistency  × 0.25
    + score_agreement      × 0.20
    + structure_clarity    × 0.15
    + answer_adequacy      × 0.10

Each factor is a 0-1 score.  The combined result ranges from 0 to 1.

Flags:
  • confidence < 0.70  →  FLAG_MANUAL_REVIEW
  • confidence < 0.50  →  FLAG_LOW_RELIABILITY (results may be unreliable)
  • individual factor < 0.40  →  FLAG on that factor

Author: AssessIQ Team  |  March 2026
"""

from __future__ import annotations

import math
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

logger = logging.getLogger("AssessIQ.Confidence")

# ═════════════════════════════════════════════════════════════════════
#  Configuration
# ═════════════════════════════════════════════════════════════════════

DEFAULT_WEIGHTS = {
    "embedding_stability": 0.30,
    "keyword_consistency": 0.25,
    "score_agreement": 0.20,
    "structure_clarity": 0.15,
    "answer_adequacy": 0.10,
}

MANUAL_REVIEW_THRESHOLD = 0.70
LOW_RELIABILITY_THRESHOLD = 0.50
FACTOR_WARNING_THRESHOLD = 0.40


# ═════════════════════════════════════════════════════════════════════
#  Data classes
# ═════════════════════════════════════════════════════════════════════

@dataclass
class ConfidenceFactor:
    """Single factor contributing to overall confidence."""
    name: str
    display_name: str
    score: float           # 0-1
    weight: float          # portion of total weight
    weighted_score: float  # score × weight
    description: str
    is_warning: bool       # True if score < FACTOR_WARNING_THRESHOLD


@dataclass
class ConfidenceResult:
    """Full confidence & reliability assessment."""
    overall_confidence: float        # 0-1
    confidence_percentage: float     # 0-100
    confidence_label: str            # "High", "Medium", "Low", "Very Low"
    factors: List[ConfidenceFactor]
    flags: List[str]                 # human-readable flag messages
    needs_manual_review: bool
    is_low_reliability: bool
    review_reasons: List[str]        # why manual review is needed

    # OCR-specific (populated when OCR data is available)
    ocr_confidence: Optional[float] = None        # 0-1 from OCR engine
    ocr_confidence_included: bool = False


# ═════════════════════════════════════════════════════════════════════
#  Factor Calculators
# ═════════════════════════════════════════════════════════════════════

def _calc_embedding_stability(
    semantic_score: float,
    concept_graph_score: Optional[float] = None,
    sentence_alignment_score: Optional[float] = None,
) -> float:
    """
    Measure how stable/consistent the embedding-based scores are.
    If semantic, concept-graph, and sentence-alignment scores agree,
    the evaluation is more trustworthy.

    Returns 0-1 where 1 = perfect agreement.
    """
    scores = [semantic_score]
    if concept_graph_score is not None:
        scores.append(concept_graph_score)
    if sentence_alignment_score is not None:
        scores.append(sentence_alignment_score)

    if len(scores) < 2:
        # Only one score available — moderate confidence
        return 0.65

    mean_s = sum(scores) / len(scores)
    # Standard deviation
    variance = sum((s - mean_s) ** 2 for s in scores) / len(scores)
    std_dev = math.sqrt(variance)

    # Map std_dev to confidence: 0 std → 1.0, 0.3 std → ~0.0
    stability = max(0.0, 1.0 - (std_dev / 0.25))
    return round(min(1.0, stability), 4)


def _calc_keyword_consistency(
    keyword_score: float,
    semantic_score: float,
    concept_graph_score: Optional[float] = None,
) -> float:
    """
    Check whether keyword-based scoring agrees with semantic scoring.
    Large disagreement (e.g. high keywords but low semantic) suggests
    keyword stuffing or superficial match — lowering confidence.

    Returns 0-1.
    """
    ref_score = semantic_score
    if concept_graph_score is not None:
        ref_score = (semantic_score + concept_graph_score) / 2

    diff = abs(keyword_score - ref_score)

    # Perfect agreement → 1.0; 0.5 gap → ~0.0
    consistency = max(0.0, 1.0 - (diff / 0.40))
    return round(min(1.0, consistency), 4)


def _calc_score_agreement(
    semantic_score: float,
    keyword_score: float,
    concept_graph_score: Optional[float] = None,
    sentence_alignment_score: Optional[float] = None,
    structural_score: Optional[float] = None,
    rubric_score: Optional[float] = None,
) -> float:
    """
    Overall agreement across ALL scoring dimensions.
    When multiple independent scorers agree, the result is more reliable.

    Returns 0-1.
    """
    scores = [semantic_score, keyword_score]
    if concept_graph_score is not None:
        scores.append(concept_graph_score)
    if sentence_alignment_score is not None:
        scores.append(sentence_alignment_score)
    if structural_score is not None:
        scores.append(structural_score)
    if rubric_score is not None:
        scores.append(rubric_score)

    if len(scores) < 2:
        return 0.60

    mean_s = sum(scores) / len(scores)
    max_diff = max(abs(s - mean_s) for s in scores)

    # More scores agreeing → higher n_factor bonus
    n_factor = min(1.0, len(scores) / 6)  # 6 possible dimensions

    # Map max deviation to agreement: 0 → 1.0, 0.35 → ~0.0
    base_agreement = max(0.0, 1.0 - (max_diff / 0.30))
    agreement = base_agreement * 0.8 + n_factor * 0.2
    return round(min(1.0, agreement), 4)


def _calc_structure_clarity(
    structural_score: Optional[float] = None,
    length_ratio: float = 1.0,
    has_intro: bool = False,
    has_conclusion: bool = False,
    student_text_length: int = 0,
) -> float:
    """
    How clear and well-structured the answer is.
    Well-structured answers are easier to evaluate reliably.

    Returns 0-1.
    """
    base = 0.5  # Start neutral

    if structural_score is not None:
        base = structural_score

    # Length adequacy factor
    if length_ratio < 0.2:
        base *= 0.3  # Very short — unreliable
    elif length_ratio < 0.5:
        base *= 0.7
    elif length_ratio > 3.0:
        base *= 0.8  # Verbose — slightly less reliable

    # Minimum length check
    if student_text_length < 20:
        base *= 0.2  # Almost no text to evaluate — very unreliable

    return round(min(1.0, max(0.0, base)), 4)


def _calc_answer_adequacy(
    student_text_length: int,
    model_text_length: int,
    keyword_score: float,
    coverage_percentage: float = 0.0,
) -> float:
    """
    Does the student answer contain enough substance to evaluate?
    Extremely short or empty answers produce unreliable scores.

    Returns 0-1.
    """
    if student_text_length < 5:
        return 0.0

    # Length ratio (capped)
    ratio = min(2.0, student_text_length / max(model_text_length, 1))
    length_factor = min(1.0, ratio / 0.4)  # Reaches 1.0 at 40% of model length

    # Keyword coverage factor
    kw_factor = min(1.0, keyword_score / 0.3)  # Reaches 1.0 at 30% coverage

    # Coverage factor
    cov_factor = min(1.0, coverage_percentage / 30.0)  # Reaches 1.0 at 30% concept coverage

    adequacy = length_factor * 0.4 + kw_factor * 0.3 + cov_factor * 0.3
    return round(min(1.0, adequacy), 4)


def _get_confidence_label(confidence: float) -> str:
    """Map 0-1 confidence to a human label."""
    if confidence >= 0.85:
        return "High"
    elif confidence >= 0.70:
        return "Medium"
    elif confidence >= 0.50:
        return "Low"
    else:
        return "Very Low"


# ═════════════════════════════════════════════════════════════════════
#  Main Service
# ═════════════════════════════════════════════════════════════════════

class ConfidenceAnalyzer:
    """
    Calculate evaluation confidence & reliability index.

    Usage:
        analyzer = ConfidenceAnalyzer()
        result = analyzer.analyze(
            semantic_score=0.82,
            keyword_score=0.75,
            student_text="...",
            model_text="...",
        )
        if result.needs_manual_review:
            flag_for_review(result.review_reasons)
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or dict(DEFAULT_WEIGHTS)
        # Normalise weights
        total = sum(self.weights.values())
        if total > 0 and abs(total - 1.0) > 0.01:
            self.weights = {k: v / total for k, v in self.weights.items()}

    def analyze(
        self,
        semantic_score: float = 0.0,
        keyword_score: float = 0.0,
        concept_graph_score: Optional[float] = None,
        sentence_alignment_score: Optional[float] = None,
        structural_score: Optional[float] = None,
        rubric_score: Optional[float] = None,
        length_ratio: float = 1.0,
        student_text: str = "",
        model_text: str = "",
        coverage_percentage: float = 0.0,
        ocr_confidence: Optional[float] = None,
        gaming_penalty: float = 0.0,
        bloom_score_modifier: float = 0.0,
    ) -> ConfidenceResult:
        """Compute full confidence assessment."""

        # ── Calculate each factor ────────────────────────────────
        f_embedding = _calc_embedding_stability(
            semantic_score, concept_graph_score, sentence_alignment_score,
        )
        f_keyword = _calc_keyword_consistency(
            keyword_score, semantic_score, concept_graph_score,
        )
        f_agreement = _calc_score_agreement(
            semantic_score, keyword_score,
            concept_graph_score, sentence_alignment_score,
            structural_score, rubric_score,
        )
        f_structure = _calc_structure_clarity(
            structural_score, length_ratio,
            student_text_length=len(student_text),
        )
        f_adequacy = _calc_answer_adequacy(
            len(student_text), len(model_text),
            keyword_score, coverage_percentage,
        )

        # ── Build factor list ────────────────────────────────────
        factor_data = [
            ("embedding_stability", "Embedding Stability",
             f_embedding,
             "Agreement between semantic, concept-graph, and alignment scores"),
            ("keyword_consistency", "Keyword Consistency",
             f_keyword,
             "Agreement between keyword coverage and meaning-based scores"),
            ("score_agreement", "Score Agreement",
             f_agreement,
             "Overall agreement across all scoring dimensions"),
            ("structure_clarity", "Structure Clarity",
             f_structure,
             "How well-structured and clear the student answer is"),
            ("answer_adequacy", "Answer Adequacy",
             f_adequacy,
             "Whether the answer contains sufficient substance to evaluate"),
        ]

        factors: List[ConfidenceFactor] = []
        weighted_total = 0.0

        for key, display, score, desc in factor_data:
            w = self.weights.get(key, 0.0)
            ws = round(score * w, 4)
            weighted_total += ws
            factors.append(ConfidenceFactor(
                name=key,
                display_name=display,
                score=round(score, 4),
                weight=round(w, 4),
                weighted_score=ws,
                description=desc,
                is_warning=score < FACTOR_WARNING_THRESHOLD,
            ))

        # ── Include OCR confidence if available ──────────────────
        ocr_conf_included = False
        if ocr_confidence is not None:
            # Blend OCR confidence into the total (extra 10% weight, rescale)
            ocr_weight = 0.10
            weighted_total = weighted_total * (1 - ocr_weight) + ocr_confidence * ocr_weight
            ocr_conf_included = True
            factors.append(ConfidenceFactor(
                name="ocr_confidence",
                display_name="OCR Quality",
                score=round(ocr_confidence, 4),
                weight=round(ocr_weight, 4),
                weighted_score=round(ocr_confidence * ocr_weight, 4),
                description="Text extraction quality from handwritten/scanned input",
                is_warning=ocr_confidence < FACTOR_WARNING_THRESHOLD,
            ))

        # ── Apply penalties from gaming/bloom ────────────────────
        if gaming_penalty > 0.05:
            # Gaming detection reduces confidence
            weighted_total *= max(0.5, 1.0 - gaming_penalty)

        overall = round(max(0.0, min(1.0, weighted_total)), 4)

        # ── Flags ────────────────────────────────────────────────
        flags: List[str] = []
        review_reasons: List[str] = []
        needs_review = False
        is_low = False

        if overall < MANUAL_REVIEW_THRESHOLD:
            needs_review = True
            flags.append(f"⚠️ Confidence {overall:.0%} < {MANUAL_REVIEW_THRESHOLD:.0%} — manual review recommended")
            review_reasons.append(f"Overall confidence ({overall:.0%}) below threshold ({MANUAL_REVIEW_THRESHOLD:.0%})")

        if overall < LOW_RELIABILITY_THRESHOLD:
            is_low = True
            flags.append(f"🔴 Low reliability ({overall:.0%}) — results may be inaccurate")
            review_reasons.append(f"Very low confidence ({overall:.0%}) — evaluation may not be reliable")

        # Per-factor warnings
        for f in factors:
            if f.is_warning:
                flags.append(f"⚠️ {f.display_name}: {f.score:.0%} (below {FACTOR_WARNING_THRESHOLD:.0%})")
                review_reasons.append(f"Low {f.display_name.lower()} ({f.score:.0%})")
                if not needs_review:
                    needs_review = True  # Any critical factor triggers review

        # Gaming flag
        if gaming_penalty > 0.10:
            flags.append(f"🎮 Anti-gaming penalty ({gaming_penalty:.0%}) reduces evaluation reliability")
            review_reasons.append(f"Gaming behaviour detected (penalty: {gaming_penalty:.0%})")
            needs_review = True

        label = _get_confidence_label(overall)

        return ConfidenceResult(
            overall_confidence=overall,
            confidence_percentage=round(overall * 100, 1),
            confidence_label=label,
            factors=factors,
            flags=flags,
            needs_manual_review=needs_review,
            is_low_reliability=is_low,
            review_reasons=review_reasons,
            ocr_confidence=ocr_confidence,
            ocr_confidence_included=ocr_conf_included,
        )

    # ─────────────────────────────────────────────────────────
    @staticmethod
    def get_detailed_report(result: ConfidenceResult) -> Dict[str, Any]:
        """Serialise for API / frontend."""
        return {
            "overall_confidence": result.overall_confidence,
            "confidence_percentage": result.confidence_percentage,
            "confidence_label": result.confidence_label,
            "needs_manual_review": result.needs_manual_review,
            "is_low_reliability": result.is_low_reliability,
            "flags": result.flags,
            "review_reasons": result.review_reasons,
            "factors": [
                {
                    "name": f.name,
                    "display_name": f.display_name,
                    "score": f.score,
                    "weight": f.weight,
                    "weighted_score": f.weighted_score,
                    "description": f.description,
                    "is_warning": f.is_warning,
                }
                for f in result.factors
            ],
            "ocr_confidence": result.ocr_confidence,
            "ocr_confidence_included": result.ocr_confidence_included,
        }
