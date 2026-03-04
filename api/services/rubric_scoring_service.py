"""
Rubric-Based Scoring Service  (Upgrade 10)
============================================
Professional rubric-based evaluation that mirrors real board examination scoring.

Instead of a single fixed-weight formula, the system evaluates answers across
independent rubric dimensions, each scored 0-1, then combined using
teacher-configurable weights.

Default Rubric (Board-Exam style):
─────────────────────────────────
  Understanding        40 %   — Does the student demonstrate comprehension?
  Concept Coverage     30 %   — Are all required concepts/points addressed?
  Terminology          15 %   — Correct use of domain-specific terms?
  Structure            10 %   — Logical organisation, intro/body/conclusion?
  Examples              5 %   — Illustrative examples or applications?

Teachers can override these via the API ``rubric_config`` field.

Dimension → Signal Mapping:
──────────────────────────
  Understanding   ← semantic similarity + sentence-alignment combined_score
  Concept Coverage← concept-graph coverage + keyword coverage
  Terminology     ← exact-keyword hit rate + technical-term density (NLP POS)
  Structure       ← structural_analysis_service score
  Examples        ← example/illustration pattern detection

Advanced Features:
──────────────────
  • Per-dimension feedback text (why the score is what it is)
  • Configurable rubric via API (teacher defines dimensions + weights)
  • Automatic weight normalisation (weights always sum to 1.0)
  • Dimension correlation penalty (prevents double-counting)
  • Band descriptors per dimension (Excellent / Good / Average / Poor)
  • Graceful degradation — missing signals get estimated from available ones
"""

from __future__ import annotations

import re
import math
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger("AssessIQ.RubricScoring")


# ═══════════════════════════════════════════════════════════════════════
#  Data Structures
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class DimensionResult:
    """Result for a single rubric dimension."""
    name: str                      # e.g. "understanding"
    display_name: str              # e.g. "Understanding"
    score: float = 0.0             # 0-1 normalised score
    weight: float = 0.0            # configured weight (0-1, sums to 1)
    weighted_score: float = 0.0    # score × weight
    band: str = "N/A"              # Excellent / Good / Average / Poor
    feedback: str = ""             # human-readable feedback
    signals_used: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RubricReport:
    """Complete rubric evaluation report."""
    dimensions: List[DimensionResult] = field(default_factory=list)
    rubric_score: float = 0.0          # weighted sum of dimension scores (0-1)
    rubric_grade: str = "N/A"          # overall grade band
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    total_weight: float = 1.0          # should be 1.0 after normalisation
    feedback_summary: str = ""
    is_custom_rubric: bool = False     # True if teacher supplied custom config


# ═══════════════════════════════════════════════════════════════════════
#  Band Descriptors
# ═══════════════════════════════════════════════════════════════════════

def _band(score: float) -> str:
    """Map a 0-1 score to a band descriptor."""
    if score >= 0.85:
        return "Excellent"
    if score >= 0.70:
        return "Good"
    if score >= 0.50:
        return "Average"
    return "Poor"


# ═══════════════════════════════════════════════════════════════════════
#  Default Rubric Configuration
# ═══════════════════════════════════════════════════════════════════════

DEFAULT_RUBRIC: Dict[str, Dict[str, Any]] = {
    "understanding": {
        "display_name": "Understanding",
        "weight": 0.40,
        "description": "Demonstrates comprehension of core concepts and their meaning",
    },
    "concept_coverage": {
        "display_name": "Concept Coverage",
        "weight": 0.30,
        "description": "Covers all required key points and concepts from the model answer",
    },
    "terminology": {
        "display_name": "Terminology",
        "weight": 0.15,
        "description": "Correct use of domain-specific and technical terms",
    },
    "structure": {
        "display_name": "Structure & Organisation",
        "weight": 0.10,
        "description": "Logical flow, introduction, body, conclusion, use of headings/lists",
    },
    "examples": {
        "display_name": "Examples & Application",
        "weight": 0.05,
        "description": "Use of illustrative examples, diagrams references, or real-world applications",
    },
}

# Question-type presets — teachers can pick these or supply custom
RUBRIC_PRESETS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "factual": {
        "understanding": {"display_name": "Understanding", "weight": 0.20},
        "concept_coverage": {"display_name": "Concept Coverage", "weight": 0.40},
        "terminology": {"display_name": "Terminology", "weight": 0.25},
        "structure": {"display_name": "Structure & Organisation", "weight": 0.10},
        "examples": {"display_name": "Examples & Application", "weight": 0.05},
    },
    "descriptive": {
        "understanding": {"display_name": "Understanding", "weight": 0.40},
        "concept_coverage": {"display_name": "Concept Coverage", "weight": 0.30},
        "terminology": {"display_name": "Terminology", "weight": 0.15},
        "structure": {"display_name": "Structure & Organisation", "weight": 0.10},
        "examples": {"display_name": "Examples & Application", "weight": 0.05},
    },
    "diagram": {
        "understanding": {"display_name": "Understanding", "weight": 0.25},
        "concept_coverage": {"display_name": "Concept Coverage", "weight": 0.30},
        "terminology": {"display_name": "Terminology", "weight": 0.15},
        "structure": {"display_name": "Structure & Organisation", "weight": 0.10},
        "examples": {"display_name": "Diagram & Visual Accuracy", "weight": 0.20},
    },
    "mixed": {
        "understanding": {"display_name": "Understanding", "weight": 0.35},
        "concept_coverage": {"display_name": "Concept Coverage", "weight": 0.30},
        "terminology": {"display_name": "Terminology", "weight": 0.15},
        "structure": {"display_name": "Structure & Organisation", "weight": 0.10},
        "examples": {"display_name": "Examples & Application", "weight": 0.10},
    },
}


# ═══════════════════════════════════════════════════════════════════════
#  Sub-Scorers for each dimension
# ═══════════════════════════════════════════════════════════════════════

class _UnderstandingScorer:
    """
    Evaluate depth of understanding.

    Primary signals:
      • semantic similarity (embedding cosine sim)
      • sentence-alignment combined_score (how well student sentences map to model)
    Secondary (fallback):
      • concept-graph combined_score as proxy
    """

    @staticmethod
    def score(
        semantic_score: float,
        sentence_alignment_score: Optional[float],
        concept_graph_score: Optional[float],
    ) -> Tuple[float, str, List[str], Dict]:
        signals = ["semantic_similarity"]
        details: Dict[str, Any] = {"semantic_score": round(semantic_score, 4)}

        # Primary: blend semantic + sentence-alignment
        if sentence_alignment_score is not None:
            # Sentence-alignment captures how well each model point is paraphrased
            s = 0.55 * semantic_score + 0.45 * sentence_alignment_score
            signals.append("sentence_alignment")
            details["sentence_alignment_score"] = round(sentence_alignment_score, 4)
        elif concept_graph_score is not None:
            s = 0.60 * semantic_score + 0.40 * concept_graph_score
            signals.append("concept_graph_fallback")
            details["concept_graph_fallback"] = round(concept_graph_score, 4)
        else:
            s = semantic_score

        s = max(0.0, min(1.0, s))
        band = _band(s)

        # Generate feedback
        if s >= 0.85:
            fb = "Excellent comprehension — your answer closely captures the intended meaning."
        elif s >= 0.70:
            fb = "Good understanding — most core ideas are accurately conveyed."
        elif s >= 0.50:
            fb = "Partial understanding — some key ideas are present but others are vaguely expressed."
        else:
            fb = "Limited understanding — the answer does not adequately convey the expected meaning."

        return s, fb, signals, details


class _ConceptCoverageScorer:
    """
    Evaluate factual completeness.

    Primary signals:
      • concept-graph coverage_score (per-concept matching)
      • keyword coverage (term hit rate)
    """

    @staticmethod
    def score(
        keyword_score: float,
        concept_graph_score: Optional[float],
        concept_graph_coverage: Optional[float],   # 0-100 coverage %
        missing_count: int = 0,
        total_concepts: int = 0,
    ) -> Tuple[float, str, List[str], Dict]:
        signals = ["keyword_coverage"]
        details: Dict[str, Any] = {"keyword_score": round(keyword_score, 4)}

        if concept_graph_score is not None and concept_graph_coverage is not None:
            # concept-graph is the better signal for concept coverage
            cg_norm = concept_graph_coverage / 100.0  # normalise to 0-1
            s = 0.35 * keyword_score + 0.65 * cg_norm
            signals.append("concept_graph_coverage")
            details["concept_graph_coverage_pct"] = round(concept_graph_coverage, 1)
            details["concept_graph_score"] = round(concept_graph_score, 4)
        elif concept_graph_score is not None:
            s = 0.40 * keyword_score + 0.60 * concept_graph_score
            signals.append("concept_graph_score")
            details["concept_graph_score"] = round(concept_graph_score, 4)
        else:
            s = keyword_score

        s = max(0.0, min(1.0, s))
        band = _band(s)

        if missing_count > 0:
            details["missing_concepts"] = missing_count
            details["total_concepts"] = total_concepts

        if s >= 0.85:
            fb = "Excellent coverage — all key concepts are addressed."
        elif s >= 0.70:
            fb = f"Good coverage — most concepts present. {missing_count} concept(s) could be stronger."
        elif s >= 0.50:
            fb = f"Partial coverage — {missing_count} important concept(s) are missing or weak."
        else:
            fb = f"Poor coverage — {missing_count} of {total_concepts} concepts are missing."

        return s, fb, signals, details


class _TerminologyScorer:
    """
    Evaluate correctness and density of domain-specific terminology.

    Signals:
      • Keyword exact-match ratio (from matched vs total model keywords)
      • Technical term density (ratio of NOUN/PROPN tokens to total)
      • Bonus for multi-word technical terms
    """

    # Common filler words that shouldn't count as "terminology"
    _FILLER = frozenset({
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "shall", "should", "may", "might", "can", "could",
        "this", "that", "these", "those", "it", "its", "i", "we",
        "you", "he", "she", "they", "me", "us", "him", "her", "them",
        "my", "our", "your", "his", "their", "not", "no", "nor",
        "and", "but", "or", "so", "if", "then", "else", "also",
        "very", "just", "only", "even", "still", "yet", "too",
        "for", "of", "in", "on", "at", "to", "from", "by", "with",
        "about", "as", "into", "through", "during", "before", "after",
    })

    @staticmethod
    def score(
        matched_keywords: List[str],
        missing_keywords: List[str],
        student_text: str,
        model_text: str,
    ) -> Tuple[float, str, List[str], Dict]:
        signals = ["keyword_exact_match"]
        details: Dict[str, Any] = {}

        total_kw = len(matched_keywords) + len(missing_keywords)
        if total_kw == 0:
            return 0.5, "No terminology benchmarks available.", signals, details

        # ── Signal 1: Keyword hit ratio ──────────────────────────────
        hit_ratio = len(matched_keywords) / total_kw
        details["keyword_hit_ratio"] = round(hit_ratio, 4)
        details["matched_count"] = len(matched_keywords)
        details["total_keywords"] = total_kw

        # ── Signal 2: Technical term density ─────────────────────────
        stu_words = student_text.lower().split()
        n_stu = len(stu_words)
        if n_stu > 0:
            tech_words = [w for w in stu_words if len(w) >= 4
                          and w not in _TerminologyScorer._FILLER]
            tech_density = len(tech_words) / n_stu
        else:
            tech_density = 0.0

        mod_words = model_text.lower().split()
        n_mod = len(mod_words)
        if n_mod > 0:
            mod_tech_words = [w for w in mod_words if len(w) >= 4
                              and w not in _TerminologyScorer._FILLER]
            mod_tech_density = len(mod_tech_words) / n_mod
        else:
            mod_tech_density = 0.3  # reasonable default

        # Compare student vs model density (within reasonable bounds)
        if mod_tech_density > 0:
            density_ratio = min(tech_density / mod_tech_density, 1.5)
        else:
            density_ratio = 1.0
        details["student_tech_density"] = round(tech_density, 4)
        details["model_tech_density"] = round(mod_tech_density, 4)
        details["density_ratio"] = round(density_ratio, 3)
        signals.append("technical_term_density")

        # ── Signal 3: Multi-word term bonus ──────────────────────────
        multi_word_bonus = 0.0
        multi_word_matches = [kw for kw in matched_keywords if " " in kw]
        if multi_word_matches:
            multi_word_bonus = min(len(multi_word_matches) * 0.03, 0.10)
            details["multi_word_matches"] = len(multi_word_matches)
            signals.append("multi_word_terms")

        # Combine signals
        s = (
            0.55 * hit_ratio +
            0.30 * min(density_ratio / 1.5, 1.0) +
            0.15 * min(hit_ratio + multi_word_bonus, 1.0)
        )
        s = max(0.0, min(1.0, s))

        if s >= 0.85:
            fb = "Excellent use of technical terminology."
        elif s >= 0.70:
            fb = "Good terminology — most domain-specific terms are used correctly."
        elif s >= 0.50:
            fb = f"Some technical terms are missing. Include: {', '.join(missing_keywords[:3])}."
        else:
            fb = f"Technical terminology is largely absent. Key terms needed: {', '.join(missing_keywords[:4])}."

        return s, fb, signals, details


class _StructureScorer:
    """
    Evaluate logical organisation.

    Primary signal:
      • structural_analysis_service score (intro, body, conclusion, headings, lists)
    Fallback:
      • Simple heuristic checks
    """

    @staticmethod
    def score(
        structural_score: Optional[float],
        structure_bonus: Optional[float],
        student_text: str,
    ) -> Tuple[float, str, List[str], Dict]:
        signals = []
        details: Dict[str, Any] = {}

        if structural_score is not None:
            s = structural_score
            signals.append("structural_analysis_service")
            details["structural_score"] = round(structural_score, 4)
            if structure_bonus is not None:
                details["structure_bonus"] = round(structure_bonus, 4)
        else:
            # Fallback: simple heuristic
            s = _StructureScorer._heuristic_structure(student_text)
            signals.append("heuristic_fallback")
            details["method"] = "heuristic"

        s = max(0.0, min(1.0, s))

        if s >= 0.85:
            fb = "Excellent structure — clear logical organisation with well-defined sections."
        elif s >= 0.70:
            fb = "Good structure — the answer flows logically with adequate organisation."
        elif s >= 0.50:
            fb = "Average structure — some organisation present but could be improved."
        else:
            fb = "Poor structure — answer lacks logical flow. Consider using headings, lists, or clear paragraphs."

        return s, fb, signals, details

    @staticmethod
    def _heuristic_structure(text: str) -> float:
        """Quick heuristic when structural_analysis_service isn't available."""
        s = 0.30  # baseline

        sentences = [p.strip() for p in re.split(r'[.!?]+', text) if p.strip()]
        n_sents = len(sentences)

        # Paragraph detection
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if len(paragraphs) >= 2:
            s += 0.15

        # List markers
        if re.search(r'(?m)^\s*[\-\•\*\d]+[\.\)]\s', text):
            s += 0.10

        # Length reward (enough content to have structure)
        if n_sents >= 3:
            s += 0.10
        if n_sents >= 6:
            s += 0.10

        # Transition words
        transitions = re.findall(
            r'\b(?:firstly|secondly|thirdly|moreover|furthermore|however|'
            r'therefore|thus|hence|in\s+conclusion|finally|additionally|'
            r'on\s+the\s+other\s+hand|for\s+example|in\s+summary)\b',
            text, re.IGNORECASE
        )
        if transitions:
            s += min(len(transitions) * 0.05, 0.15)

        # Heading-like elements
        if re.search(r'(?m)^[A-Z][^.!?]{3,40}$', text):
            s += 0.05

        return min(s, 1.0)


class _ExamplesScorer:
    """
    Evaluate use of examples, illustrations, and applications.

    Detection patterns:
      • Explicit markers: "for example", "such as", "e.g.", "for instance"
      • Application phrases: "in real life", "in practice", "real world"
      • Specific instances: proper nouns, numerical data, named entities
      • Diagram references: "as shown in", "figure", "diagram"
    """

    # Compiled patterns for example detection
    _EXAMPLE_PATTERNS = [
        re.compile(r'\bfor\s+example\b', re.I),
        re.compile(r'\bfor\s+instance\b', re.I),
        re.compile(r'\bsuch\s+as\b', re.I),
        re.compile(r'\be\.?g\.?\b', re.I),
        re.compile(r'\bi\.?e\.?\b', re.I),
        re.compile(r'\blike\s+(?:the|a|an)\b', re.I),
        re.compile(r'\bincluding\b', re.I),
        re.compile(r'\billustrat(?:e[sd]?|ion|ing)\b', re.I),
        re.compile(r'\bnamely\b', re.I),
        re.compile(r'\bspecifically\b', re.I),
    ]

    _APPLICATION_PATTERNS = [
        re.compile(r'\bin\s+(?:real\s+(?:life|world)|practice|daily\s+life|everyday)\b', re.I),
        re.compile(r'\bapplicat(?:ion|ions|ed)\b', re.I),
        re.compile(r'\bused?\s+(?:in|for|to)\b', re.I),
        re.compile(r'\bpractical(?:ly)?\b', re.I),
    ]

    _DIAGRAM_PATTERNS = [
        re.compile(r'\b(?:as\s+shown|diagram|figure|fig\.?|illustration|chart|table|graph)\b', re.I),
    ]

    @staticmethod
    def score(
        student_text: str,
        model_text: str,
        diagram_score: Optional[float] = None,
    ) -> Tuple[float, str, List[str], Dict]:
        signals = []
        details: Dict[str, Any] = {}

        if not student_text or len(student_text.strip()) < 10:
            return 0.0, "No text to evaluate for examples.", signals, details

        # Count example markers in student text vs model
        stu_examples = sum(
            len(p.findall(student_text)) for p in _ExamplesScorer._EXAMPLE_PATTERNS
        )
        mod_examples = sum(
            len(p.findall(model_text)) for p in _ExamplesScorer._EXAMPLE_PATTERNS
        )

        stu_applications = sum(
            len(p.findall(student_text)) for p in _ExamplesScorer._APPLICATION_PATTERNS
        )
        mod_applications = max(sum(
            len(p.findall(model_text)) for p in _ExamplesScorer._APPLICATION_PATTERNS
        ), 1)

        stu_diagrams = sum(
            len(p.findall(student_text)) for p in _ExamplesScorer._DIAGRAM_PATTERNS
        )

        details["student_example_markers"] = stu_examples
        details["model_example_markers"] = mod_examples
        details["student_application_refs"] = stu_applications
        details["student_diagram_refs"] = stu_diagrams

        # ── Numeric / proper noun detection (specific instances) ─────
        numbers = re.findall(r'\b\d+(?:\.\d+)?(?:\s*%|\s*°[CF]?)?\b', student_text)
        # Rough proper noun detection: capitalized words not at sentence start
        proper_nouns = re.findall(
            r'(?<=[.!?]\s)[a-z][^.]*?\b([A-Z][a-z]{2,})\b',
            student_text
        )
        specific_instances = len(numbers) + len(proper_nouns)
        details["specific_instances"] = specific_instances
        signals.append("example_markers")

        # ── Score computation ────────────────────────────────────────
        # Base: does the student give any examples at all?
        s = 0.0

        # Example markers
        if stu_examples > 0:
            # Compare to model expectation
            if mod_examples > 0:
                example_ratio = min(stu_examples / mod_examples, 1.5)
            else:
                # Model doesn't use examples but student does — bonus
                example_ratio = 1.0
            s += 0.40 * min(example_ratio, 1.0)
            signals.append("example_ratio")
        elif mod_examples == 0:
            # Neither model nor student has examples — neutral score
            s += 0.30

        # Application references
        app_ratio = min(stu_applications / mod_applications, 1.5)
        s += 0.25 * min(app_ratio, 1.0)

        # Specific instances (numbers, proper nouns)
        if specific_instances >= 3:
            s += 0.15
        elif specific_instances >= 1:
            s += 0.08
        signals.append("specific_instances")

        # Diagram references or actual diagram score
        if diagram_score is not None and diagram_score > 0:
            s += 0.20 * diagram_score
            signals.append("diagram_score")
        elif stu_diagrams > 0:
            s += 0.08
            signals.append("diagram_references")

        s = max(0.0, min(1.0, s))

        if s >= 0.85:
            fb = "Excellent use of examples and practical applications."
        elif s >= 0.70:
            fb = "Good examples provided to support the answer."
        elif s >= 0.50:
            fb = "Some examples present — consider adding more specific illustrations."
        elif s >= 0.20:
            fb = "Few examples given. Try using 'for example...', 'such as...', or cite specific cases."
        else:
            fb = "No examples or applications detected. Illustrate your points with concrete examples."

        return s, fb, signals, details


# ═══════════════════════════════════════════════════════════════════════
#  Master Orchestrator
# ═══════════════════════════════════════════════════════════════════════

class RubricScorer:
    """
    Professional rubric-based evaluation engine.

    Usage:
        scorer = RubricScorer()

        # With default rubric (based on question type):
        report = scorer.evaluate(
            question_type="descriptive",
            semantic_score=0.82,
            keyword_score=0.75,
            ...
        )

        # With custom teacher rubric:
        custom = {
            "understanding": {"weight": 0.50},
            "concept_coverage": {"weight": 0.30},
            "terminology": {"weight": 0.20},
        }
        report = scorer.evaluate(rubric_config=custom, ...)

    The returned ``RubricReport`` contains per-dimension scores, bands,
    feedback, and the final rubric_score (weighted sum).
    """

    # Valid dimension names
    VALID_DIMENSIONS = {
        "understanding", "concept_coverage", "terminology",
        "structure", "examples",
    }

    def evaluate(
        self,
        # ── Pipeline scores ──────────────────────────────────────
        semantic_score: float = 0.0,
        keyword_score: float = 0.0,
        concept_graph_score: Optional[float] = None,
        concept_graph_coverage: Optional[float] = None,
        sentence_alignment_score: Optional[float] = None,
        structural_score: Optional[float] = None,
        structure_bonus: Optional[float] = None,
        diagram_score: Optional[float] = None,
        # ── Text data (for terminology / examples scorers) ───────
        student_text: str = "",
        model_text: str = "",
        matched_keywords: Optional[List[str]] = None,
        missing_keywords: Optional[List[str]] = None,
        missing_concept_count: int = 0,
        total_concept_count: int = 0,
        # ── Rubric configuration ─────────────────────────────────
        question_type: str = "descriptive",
        rubric_config: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> RubricReport:
        """Run rubric evaluation and return a RubricReport."""

        matched_keywords = matched_keywords or []
        missing_keywords = missing_keywords or []

        # ── Resolve rubric configuration ─────────────────────────
        is_custom = rubric_config is not None and len(rubric_config) > 0
        if is_custom:
            # Handle frontend format: {"preset": "factual"} or
            # {"dimensions": [{"name": "...", "weight": ...}, ...]}
            normalised_config = rubric_config
            if "preset" in rubric_config:
                preset_name = rubric_config["preset"]
                effective_rubric = dict(RUBRIC_PRESETS.get(preset_name, DEFAULT_RUBRIC))
                # Deep copy inner dicts
                effective_rubric = {k: dict(v) for k, v in effective_rubric.items()}
            elif "dimensions" in rubric_config and isinstance(rubric_config["dimensions"], list):
                # Convert [{name, weight}, ...] to {name: {weight: ...}}
                normalised_config = {}
                for dim in rubric_config["dimensions"]:
                    dname = dim.get("name", "")
                    normalised_config[dname] = {
                        k: v for k, v in dim.items() if k != "name"
                    }
                effective_rubric = self._merge_custom_rubric(normalised_config)
            else:
                # Assume direct {dim_name: {cfg}} format
                effective_rubric = self._merge_custom_rubric(rubric_config)
        else:
            effective_rubric = dict(RUBRIC_PRESETS.get(question_type, DEFAULT_RUBRIC))
            # Deep copy inner dicts
            effective_rubric = {k: dict(v) for k, v in effective_rubric.items()}

        # Normalise weights so they sum to 1.0
        effective_rubric = self._normalise_weights(effective_rubric)

        # ── Score each dimension ─────────────────────────────────
        dim_results: List[DimensionResult] = []

        for dim_name, cfg in effective_rubric.items():
            weight = cfg.get("weight", 0.0)
            display = cfg.get("display_name", dim_name.replace("_", " ").title())

            if dim_name == "understanding":
                s, fb, sig, det = _UnderstandingScorer.score(
                    semantic_score, sentence_alignment_score, concept_graph_score
                )
            elif dim_name == "concept_coverage":
                s, fb, sig, det = _ConceptCoverageScorer.score(
                    keyword_score, concept_graph_score, concept_graph_coverage,
                    missing_concept_count, total_concept_count,
                )
            elif dim_name == "terminology":
                s, fb, sig, det = _TerminologyScorer.score(
                    matched_keywords, missing_keywords, student_text, model_text,
                )
            elif dim_name == "structure":
                s, fb, sig, det = _StructureScorer.score(
                    structural_score, structure_bonus, student_text,
                )
            elif dim_name == "examples":
                s, fb, sig, det = _ExamplesScorer.score(
                    student_text, model_text, diagram_score,
                )
            else:
                # Unknown dimension — skip gracefully
                logger.warning(f"Unknown rubric dimension: {dim_name}")
                continue

            dr = DimensionResult(
                name=dim_name,
                display_name=display,
                score=round(s, 4),
                weight=round(weight, 4),
                weighted_score=round(s * weight, 4),
                band=_band(s),
                feedback=fb,
                signals_used=sig,
                details=det,
            )
            dim_results.append(dr)

        # ── Aggregate ────────────────────────────────────────────
        rubric_score = sum(d.weighted_score for d in dim_results)
        rubric_score = max(0.0, min(1.0, rubric_score))

        dimension_scores = {d.name: d.score for d in dim_results}
        rubric_grade = _band(rubric_score)

        # ── Summary feedback ─────────────────────────────────────
        feedback_parts = []
        # Best dimension
        if dim_results:
            best = max(dim_results, key=lambda d: d.score)
            worst = min(dim_results, key=lambda d: d.score)
            if best.score > 0.50:
                feedback_parts.append(f"Strongest area: {best.display_name} ({best.band})")
            if worst.score < 0.70 and worst.name != best.name:
                feedback_parts.append(f"Area to improve: {worst.display_name} ({worst.band})")
        feedback_summary = ". ".join(feedback_parts)

        return RubricReport(
            dimensions=dim_results,
            rubric_score=round(rubric_score, 4),
            rubric_grade=rubric_grade,
            dimension_scores=dimension_scores,
            total_weight=round(sum(d.weight for d in dim_results), 4),
            feedback_summary=feedback_summary,
            is_custom_rubric=is_custom,
        )

    # ── Helpers ───────────────────────────────────────────────────

    def _merge_custom_rubric(
        self, custom: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Merge a teacher's custom rubric with defaults for missing fields."""
        merged: Dict[str, Dict[str, Any]] = {}
        for dim_name, dim_cfg in custom.items():
            # Allow custom display name but keep the scorer key
            key = dim_name.lower().replace(" ", "_")
            if key not in self.VALID_DIMENSIONS:
                logger.warning(f"Ignoring unknown rubric dimension: {dim_name}")
                continue
            base = dict(DEFAULT_RUBRIC.get(key, {}))
            base.update(dim_cfg)
            merged[key] = base
        return merged

    @staticmethod
    def _normalise_weights(
        rubric: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Ensure dimension weights sum to 1.0 (proportional scaling)."""
        total = sum(cfg.get("weight", 0) for cfg in rubric.values())
        if total <= 0:
            # Fallback: equal weights
            n = len(rubric)
            for cfg in rubric.values():
                cfg["weight"] = 1.0 / max(n, 1)
        elif abs(total - 1.0) > 0.001:
            for cfg in rubric.values():
                cfg["weight"] = cfg.get("weight", 0) / total
        return rubric

    def get_detailed_report(self, report: RubricReport) -> Dict[str, Any]:
        """Serialise a RubricReport to a JSON-friendly dict for the API."""
        return {
            "rubric_score": report.rubric_score,
            "rubric_grade": report.rubric_grade,
            "is_custom_rubric": report.is_custom_rubric,
            "feedback_summary": report.feedback_summary,
            "dimensions": [
                {
                    "name": d.name,
                    "display_name": d.display_name,
                    "score": d.score,
                    "weight": d.weight,
                    "weighted_score": d.weighted_score,
                    "band": d.band,
                    "feedback": d.feedback,
                    "signals_used": d.signals_used,
                    "details": d.details,
                }
                for d in report.dimensions
            ],
            "dimension_scores": report.dimension_scores,
        }
