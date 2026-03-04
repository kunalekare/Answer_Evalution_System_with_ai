"""
Bloom's Taxonomy Evaluation Service
=====================================
Detects the cognitive level of a question (Remember → Create) using
Bloom's Revised Taxonomy, then analyses whether the student's answer
demonstrates the *expected* cognitive depth.

Bloom Levels (low → high):
  1  Remember      — recall facts, definitions
  2  Understand    — explain, describe, summarise
  3  Apply         — use knowledge in a new situation
  4  Analyse       — compare, contrast, differentiate
  5  Evaluate      — justify, argue, critique
  6  Create        — design, construct, propose

Scoring:
  • If the question demands Analyse but the student only Remembers,
    a cognitive-depth penalty is applied.
  • If the student demonstrates a *higher* level than expected,
    a small bonus is awarded ("exceeds expectations").
  • Detected analytical/comparative/evaluative language is tracked.

Author: AssessIQ Team  |  March 2026
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("AssessIQ.Bloom")

# ═════════════════════════════════════════════════════════════════════
#  Bloom Level Definitions
# ═════════════════════════════════════════════════════════════════════

BLOOM_LEVELS = {
    1: "Remember",
    2: "Understand",
    3: "Apply",
    4: "Analyse",
    5: "Evaluate",
    6: "Create",
}

BLOOM_LEVEL_FROM_NAME = {v.lower(): k for k, v in BLOOM_LEVELS.items()}

# Question-stem keywords mapped to Bloom level
# These are the verbs/phrases typically found in exam questions.
_QUESTION_VERBS: Dict[int, List[str]] = {
    1: [  # Remember
        r"\bdefine\b", r"\blist\b", r"\bstate\b", r"\brecall\b",
        r"\bname\b", r"\bidentify\b", r"\benumerate\b", r"\blabel\b",
        r"\brecite\b", r"\brecognize\b", r"\bmatch\b",
        r"\bwhat\s+is\b", r"\bwhat\s+are\b", r"\bwho\b",
    ],
    2: [  # Understand
        r"\bexplain\b", r"\bdescribe\b", r"\bsummar(?:ize|ise)\b",
        r"\binterpret\b", r"\bparaphrase\b", r"\billustrate\b",
        r"\bdiscuss\b", r"\belaborate\b", r"\bclarify\b",
        r"\bin\s+your\s+own\s+words\b", r"\bgive\s+(?:an?\s+)?example",
        r"\bwhy\b", r"\bhow\s+does\b",
    ],
    3: [  # Apply
        r"\bapply\b", r"\bdemonstrate\b", r"\bcalculate\b",
        r"\bsolve\b", r"\buse\b", r"\bimplement\b",
        r"\bshow\s+how\b", r"\bcompute\b", r"\bexecute\b",
        r"\bconstruct\b", r"\bperform\b", r"\boperate\b",
        r"\bpractice\b", r"\bexercise\b",
    ],
    4: [  # Analyse
        r"\banalyse\b", r"\banalyze\b", r"\bcompare\b",
        r"\bcontrast\b", r"\bdifferentiat\w*\b", r"\bdistinguish\b",
        r"\bexamine\b", r"\binvestigat\w*\b", r"\bcategoriz\w*\b",
        r"\bclassify\b", r"\bdeconstruct\b", r"\bbreak\s+down\b",
        r"\brelate\b", r"\borganiz\w*\b",
        r"\bdifference\s+between\b", r"\bsimilarit(?:y|ies)\b",
    ],
    5: [  # Evaluate
        r"\bevaluat\w*\b", r"\bjustify\b", r"\bjudge\b",
        r"\bcritiqu\w*\b", r"\bcritical(?:ly)?\b",
        r"\bassess\b", r"\bappraise\b", r"\bargue\b",
        r"\bdefend\b", r"\bsupport\b", r"\bvalidate\b",
        r"\bprioritiz\w*\b", r"\brecommend\b", r"\brate\b",
        r"\bto\s+what\s+extent\b", r"\bdo\s+you\s+agree\b",
    ],
    6: [  # Create
        r"\bcreate\b", r"\bdesign\b", r"\bpropose\b",
        r"\bformulat\w*\b", r"\binvent\b", r"\bcompose\b",
        r"\bplan\b", r"\bdevelop\b", r"\bgenerate\b",
        r"\bbuild\b", r"\bsynthesize\b", r"\bsynth[ei]s[ei]\w*\b",
        r"\bconstruct\s+a\b", r"\boriginal\b",
    ],
}

# Compiled patterns (lazy init)
_COMPILED_Q_PATTERNS: Dict[int, List[re.Pattern]] = {}

# ─────────────────────────────────────────────────────────────────────
#  Answer-level language indicators
#  These detect whether the student's text operates at a given level.
# ─────────────────────────────────────────────────────────────────────

_ANSWER_INDICATORS: Dict[int, List[str]] = {
    1: [  # Remember — plain recall
        r"\bis\s+defined\s+as\b", r"\bis\s+called\b",
        r"\brefers?\s+to\b", r"\bstands?\s+for\b",
        r"\bknown\s+as\b", r"\babbreviation\b",
    ],
    2: [  # Understand — explanatory language
        r"\bthis\s+means\b", r"\bin\s+other\s+words\b",
        r"\bfor\s+example\b", r"\bfor\s+instance\b",
        r"\bsuch\s+as\b", r"\bi\.e\.?\b", r"\be\.g\.?\b",
        r"\bin\s+simple\s+terms\b", r"\bto\s+put\s+it\b",
        r"\bbecause\b", r"\bsince\b", r"\btherefore\b",
        r"\bthus\b", r"\bhence\b",
    ],
    3: [  # Apply — procedural / application
        r"\bstep\s*\d?\b", r"\bfirst(?:ly)?\b.*\bthen\b",
        r"\bwe\s+(?:can|could)\s+use\b", r"\bapplying\s+this\b",
        r"\bsubstitut(?:e|ing)\b", r"\baccording\s+to\s+the\s+formula\b",
        r"\busing\s+(?:the\s+)?(?:method|technique|approach)\b",
    ],
    4: [  # Analyse — comparative / analytical
        r"\bwhereas\b", r"\bunlike\b", r"\bin\s+contrast\b",
        r"\bon\s+the\s+other\s+hand\b", r"\bwhile\b",
        r"\bsimilar(?:ly)?\b", r"\bdiffers?\s+(?:from|in)\b",
        r"\bcompared?\s+(?:to|with)\b", r"\bdistinct(?:ion|ly)?\b",
        r"\brelationship\s+between\b", r"\bcorrelation\b",
        r"\bfactor\b", r"\bcomponent\b", r"\baspect\b",
        r"\badvantage\b", r"\bdisadvantage\b",
        r"\bstrength\b", r"\bweakness\b",
        r"\bpro(?:s)?\b.*\bcon(?:s)?\b",
        r"\bmore\s+(?:than|efficient|effective)\b",
        r"\bless\s+(?:than|efficient|effective)\b",
    ],
    5: [  # Evaluate — judgement / argumentation
        r"\bin\s+my\s+opinion\b", r"\bi\s+(?:think|believe|argue)\b",
        r"\bit\s+(?:can\s+be|is)\s+argued\b",
        r"\boverall\b", r"\bin\s+conclusion\b",
        r"\bsuperi(?:or|ority)\b", r"\binferi(?:or|ority)\b",
        r"\bmost\s+(?:important|effective|significant)\b",
        r"\bshould\b", r"\bprefer(?:able|red)?\b",
        r"\bbest\s+(?:approach|method|solution)\b",
        r"\bcritical(?:ly)?\b", r"\bsignificant(?:ly)?\b",
        r"\beffective(?:ness)?\b", r"\bjustif(?:y|ied|ication)\b",
        r"\bvalid(?:ity)?\b", r"\breliab(?:le|ility)\b",
    ],
    6: [  # Create — generative / original
        r"\bi\s+(?:would\s+)?propose\b", r"\bmy\s+(?:design|approach|solution)\b",
        r"\ba\s+(?:new|novel|original)\s+(?:method|approach|solution|system)\b",
        r"\bcombining\b", r"\bintegrat(?:e|ing)\b",
        r"\bhypothes[ie]s\b", r"\bmodel\s+(?:that|which)\b",
        r"\bframework\b", r"\bblueprint\b",
    ],
}

_COMPILED_A_PATTERNS: Dict[int, List[re.Pattern]] = {}


# ═════════════════════════════════════════════════════════════════════
#  Data classes
# ═════════════════════════════════════════════════════════════════════

@dataclass
class BloomLevelDetail:
    """Detail for a single Bloom level detected in text."""
    level: int
    name: str
    indicators_found: List[str]
    indicator_count: int
    confidence: float  # 0-1


@dataclass
class BloomAnalysisResult:
    """Complete Bloom's Taxonomy analysis."""
    # Question analysis
    question_bloom_level: int          # 1-6
    question_bloom_name: str           # "Analyse", "Remember", etc.
    question_detection_confidence: float  # 0-1
    question_indicators: List[str]     # verbs/phrases found in question

    # Student answer analysis
    student_bloom_level: int           # Highest level with sufficient evidence
    student_bloom_name: str
    student_detection_confidence: float
    student_level_breakdown: List[BloomLevelDetail]
    student_indicators: Dict[str, List[str]]  # level_name → indicators

    # Scoring
    cognitive_alignment: float         # 0-1: how well student meets expected level
    bloom_score_modifier: float        # -0.15 to +0.05 adjustment
    exceeds_expectations: bool
    below_expectations: bool

    # Rich feedback
    feedback: str
    suggestions: List[str]


# ═════════════════════════════════════════════════════════════════════
#  Internal helpers
# ═════════════════════════════════════════════════════════════════════

def _ensure_compiled():
    """Lazy-compile all regex patterns."""
    if not _COMPILED_Q_PATTERNS:
        for lvl, pats in _QUESTION_VERBS.items():
            _COMPILED_Q_PATTERNS[lvl] = [re.compile(p, re.IGNORECASE) for p in pats]
    if not _COMPILED_A_PATTERNS:
        for lvl, pats in _ANSWER_INDICATORS.items():
            _COMPILED_A_PATTERNS[lvl] = [re.compile(p, re.IGNORECASE) for p in pats]


def _detect_level_from_patterns(
    text: str,
    pattern_dict: Dict[int, List[re.Pattern]],
    top_n_chars: int = 0,
) -> Tuple[int, float, Dict[int, List[str]]]:
    """
    Scan text for Bloom-level indicator patterns.
    Returns (best_level, confidence, {level: [matched_phrases]}).
    If top_n_chars > 0, only the first top_n_chars of text are scanned
    (useful for question stems where the verb is at the start).
    """
    scan_text = text[:top_n_chars] if top_n_chars > 0 else text

    hits: Dict[int, List[str]] = {lvl: [] for lvl in range(1, 7)}
    for lvl, patterns in pattern_dict.items():
        for pat in patterns:
            for m in pat.finditer(scan_text):
                hits[lvl].append(m.group().strip().lower())

    # Score each level: higher levels get a weight multiplier so that
    # if both "define" and "compare" are found, we favour "compare".
    level_weights = {1: 1.0, 2: 1.2, 3: 1.4, 4: 1.8, 5: 2.0, 6: 2.2}
    scores: Dict[int, float] = {}
    for lvl in range(1, 7):
        scores[lvl] = len(hits[lvl]) * level_weights[lvl]

    total_hits = sum(len(h) for h in hits.values())
    if total_hits == 0:
        return 2, 0.3, hits  # default to Understand with low confidence

    best_level = max(scores, key=lambda k: scores[k])
    best_score = scores[best_level]
    total_score = sum(scores.values())
    confidence = min(1.0, best_score / max(total_score, 1) + 0.2 * min(total_hits, 5) / 5)
    confidence = round(min(1.0, confidence), 3)

    return best_level, confidence, hits


def _compute_student_level_breakdown(
    hits: Dict[int, List[str]],
) -> List[BloomLevelDetail]:
    """Build per-level detail list from hits dict."""
    details = []
    total = sum(len(v) for v in hits.values()) or 1
    for lvl in range(1, 7):
        count = len(hits[lvl])
        details.append(BloomLevelDetail(
            level=lvl,
            name=BLOOM_LEVELS[lvl],
            indicators_found=list(set(hits[lvl]))[:10],
            indicator_count=count,
            confidence=round(count / total, 3) if count > 0 else 0.0,
        ))
    return details


# ═════════════════════════════════════════════════════════════════════
#  Main Service
# ═════════════════════════════════════════════════════════════════════

class BloomTaxonomyAnalyzer:
    """
    Analyse a question + student answer pair using Bloom's Revised Taxonomy.

    Usage:
        analyzer = BloomTaxonomyAnalyzer()
        result = analyzer.analyze(
            question_text="Compare OS and Compiler",
            student_text="An OS manages hardware whereas a compiler translates code...",
        )
        print(result.bloom_score_modifier)   # e.g. +0.03
        print(result.student_bloom_name)      # e.g. "Analyse"
    """

    # Penalty / bonus caps
    MAX_PENALTY = 0.15      # Max deduction when student is below expected level
    MAX_BONUS = 0.05        # Max bonus when student exceeds expected level
    LEVEL_GAP_PENALTY = 0.05  # Penalty per level gap (student below question)

    def analyze(
        self,
        question_text: str = "",
        student_text: str = "",
        model_text: str = "",
        question_bloom_override: Optional[int] = None,
    ) -> BloomAnalysisResult:
        """
        Analyse cognitive level alignment between question and student answer.

        Args:
            question_text: The question prompt (e.g. "Compare OS and Compiler").
                           If empty, the model_text stem is used heuristically.
            student_text:  Student's answer text.
            model_text:    Model/expected answer (used as fallback for question detection).
            question_bloom_override: Force a specific Bloom level for the question (1-6).
        """
        _ensure_compiled()

        # ── Detect question Bloom level ──────────────────────────
        q_text = question_text.strip()
        if not q_text and model_text:
            # Use first 200 chars of model text as proxy
            q_text = model_text[:200]

        if question_bloom_override and 1 <= question_bloom_override <= 6:
            q_level = question_bloom_override
            q_conf = 1.0
            q_hits: Dict[int, List[str]] = {i: [] for i in range(1, 7)}
        else:
            q_level, q_conf, q_hits = _detect_level_from_patterns(
                q_text, _COMPILED_Q_PATTERNS, top_n_chars=300,
            )

        q_indicators: List[str] = []
        for hits_list in q_hits.values():
            q_indicators.extend(hits_list)

        # ── Detect student answer Bloom level ────────────────────
        s_level, s_conf, s_hits = _detect_level_from_patterns(
            student_text, _COMPILED_A_PATTERNS,
        )

        student_breakdown = _compute_student_level_breakdown(s_hits)

        student_indicators: Dict[str, List[str]] = {}
        for lvl in range(1, 7):
            if s_hits[lvl]:
                student_indicators[BLOOM_LEVELS[lvl]] = list(set(s_hits[lvl]))[:8]

        # ── Calculate alignment score ────────────────────────────
        level_gap = s_level - q_level  # positive = student exceeds, negative = below
        exceeds = level_gap > 0
        below = level_gap < 0

        # Cognitive alignment: 1.0 when matched, decreases with gap
        if level_gap >= 0:
            cognitive_alignment = 1.0
        else:
            # Each level below reduces alignment by ~0.2
            cognitive_alignment = max(0.0, 1.0 + level_gap * 0.2)

        # Score modifier
        if below:
            # Penalty: up to MAX_PENALTY, scaled by gap and confidence
            raw_penalty = abs(level_gap) * self.LEVEL_GAP_PENALTY
            modifier = -min(raw_penalty * min(q_conf, 0.9), self.MAX_PENALTY)
        elif exceeds:
            # Bonus: small reward for exceeding, scaled by confidence
            raw_bonus = min(level_gap, 2) * 0.025
            modifier = min(raw_bonus * s_conf, self.MAX_BONUS)
        else:
            modifier = 0.0

        modifier = round(modifier, 4)
        cognitive_alignment = round(cognitive_alignment, 3)

        # ── Feedback & suggestions ───────────────────────────────
        feedback, suggestions = self._generate_feedback(
            q_level, s_level, q_conf, s_conf,
            exceeds, below, student_indicators,
        )

        return BloomAnalysisResult(
            question_bloom_level=q_level,
            question_bloom_name=BLOOM_LEVELS[q_level],
            question_detection_confidence=q_conf,
            question_indicators=list(set(q_indicators))[:10],
            student_bloom_level=s_level,
            student_bloom_name=BLOOM_LEVELS[s_level],
            student_detection_confidence=s_conf,
            student_level_breakdown=student_breakdown,
            student_indicators=student_indicators,
            cognitive_alignment=cognitive_alignment,
            bloom_score_modifier=modifier,
            exceeds_expectations=exceeds,
            below_expectations=below,
            feedback=feedback,
            suggestions=suggestions,
        )

    # ─────────────────────────────────────────────────────────
    def _generate_feedback(
        self,
        q_level: int, s_level: int,
        q_conf: float, s_conf: float,
        exceeds: bool, below: bool,
        student_indicators: Dict[str, List[str]],
    ) -> Tuple[str, List[str]]:
        """Generate human-readable feedback and improvement suggestions."""
        q_name = BLOOM_LEVELS[q_level]
        s_name = BLOOM_LEVELS[s_level]
        suggestions: List[str] = []

        if below:
            gap = q_level - s_level
            if gap >= 3:
                feedback = (
                    f"The question requires '{q_name}'-level thinking, but your answer "
                    f"mostly stays at the '{s_name}' level — a significant cognitive gap. "
                    f"Try to engage more deeply with the material."
                )
                suggestions.append(
                    f"Upgrade your answer from {s_name} to {q_name}: "
                    + self._level_tip(q_level)
                )
                suggestions.append(
                    "Go beyond definitions — show analysis, comparison, or evaluation."
                )
            elif gap == 2:
                feedback = (
                    f"The question expects '{q_name}'-level response, but your answer "
                    f"mainly demonstrates '{s_name}'. Add more depth."
                )
                suggestions.append(self._level_tip(q_level))
            else:
                feedback = (
                    f"Your answer is close but could aim higher — the question targets "
                    f"'{q_name}' level while your response is at '{s_name}'."
                )
                suggestions.append(self._level_tip(q_level))

        elif exceeds:
            feedback = (
                f"Excellent cognitive depth! The question expects '{q_name}' level, "
                f"and your answer demonstrates '{s_name}' — exceeding expectations."
            )
            suggestions.append("Great analytical depth — keep it up!")

        else:  # matched
            feedback = (
                f"Good cognitive alignment — your answer matches the expected "
                f"'{q_name}' thinking level."
            )
            if q_level >= 4:
                # Check for comparative/analytical richness
                analytic_count = sum(
                    len(v) for k, v in student_indicators.items()
                    if k in ("Analyse", "Evaluate", "Create")
                )
                if analytic_count < 3:
                    suggestions.append(
                        "You're at the right level — strengthening with more "
                        "comparative/evaluative phrases would make it even better."
                    )

        return feedback, suggestions

    @staticmethod
    def _level_tip(level: int) -> str:
        """Short actionable tip for reaching a target Bloom level."""
        tips = {
            1: "State the key facts and definitions clearly.",
            2: "Explain the concept in your own words with examples.",
            3: "Show how you would apply this knowledge in a real scenario.",
            4: "Use comparison language (whereas, unlike, on the other hand) to analyse differences.",
            5: "Include your judgement — argue which approach is better and why.",
            6: "Propose an original design, hypothesis, or solution that combines ideas.",
        }
        return tips.get(level, "Demonstrate deeper thinking.")

    # ─────────────────────────────────────────────────────────
    @staticmethod
    def get_detailed_report(result: BloomAnalysisResult) -> Dict:
        """Serialise analysis for API response / frontend consumption."""
        return {
            "question_bloom_level": result.question_bloom_level,
            "question_bloom_name": result.question_bloom_name,
            "question_confidence": result.question_detection_confidence,
            "question_indicators": result.question_indicators,
            "student_bloom_level": result.student_bloom_level,
            "student_bloom_name": result.student_bloom_name,
            "student_confidence": result.student_detection_confidence,
            "student_level_breakdown": [
                {
                    "level": d.level,
                    "name": d.name,
                    "indicator_count": d.indicator_count,
                    "indicators": d.indicators_found,
                    "confidence": d.confidence,
                }
                for d in result.student_level_breakdown
            ],
            "student_indicators": result.student_indicators,
            "cognitive_alignment": result.cognitive_alignment,
            "bloom_score_modifier": result.bloom_score_modifier,
            "exceeds_expectations": result.exceeds_expectations,
            "below_expectations": result.below_expectations,
            "feedback": result.feedback,
            "suggestions": result.suggestions,
        }
