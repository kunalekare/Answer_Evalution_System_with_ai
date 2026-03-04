"""
Structural Analysis Service  (Upgrade 8)
==========================================
Logical structure evaluation for student answers.

Why Structure Matters
----------------------
Professional examiners assess not just *what* is written but *how* it
is organized.  A well-structured answer with introduction, body,
conclusion, definitions, examples, and bullet points demonstrates
deeper understanding and communication skill.

Architecture: 7-Detector Structural Analysis Pipeline
------------------------------------------------------

1. **IntroDetector**       - Opening sentence quality: defines, introduces, contextualizes
2. **BodyAnalyzer**        - Paragraph depth, sentence count, elaboration density
3. **ConclusionDetector**  - Closing summary, "therefore"/"in conclusion" signals
4. **ListPointDetector**   - Numbered/bulleted items, comma-separated enumerations
5. **DefinitionDetector**  - "is defined as", "refers to", formal definition patterns
6. **ExampleDetector**     - "for example", "such as", concrete illustrations
7. **CoherenceAnalyzer**   - Transition words, topic sentence detection, logical flow

Scoring Model
--------------
The structural score is a **quality bonus** applied on top of the
content-based score, not a replacement.  This mirrors real exam marking
where structure earns extra credit.

    structural_score  = weighted sum of 7 detector scores
    structure_bonus   = structural_score * BONUS_CAP  (max +0.08)

The bonus is added *after* the weighted content score, capped so it
can improve a borderline answer but cannot override poor content.

Dependencies (all already installed):
    - spaCy (en_core_web_sm) — sentence splitting, POS tagging
    - re (stdlib) — pattern matching
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set

logger = logging.getLogger("AssessIQ.StructuralAnalysis")


# ═══════════════════════════════════════════════════════════════════════
#  Data Structures
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class DetectorResult:
    """Output from a single structural detector."""
    name: str
    detected: bool
    score: float            # 0.0 – 1.0  (detector-local)
    evidence: List[str] = field(default_factory=list)
    details: Dict = field(default_factory=dict)


@dataclass
class StructuralReport:
    """Complete output from the structural analysis pipeline."""
    # Per-detector results
    intro: DetectorResult = field(default_factory=lambda: DetectorResult("intro", False, 0.0))
    body: DetectorResult = field(default_factory=lambda: DetectorResult("body", False, 0.0))
    conclusion: DetectorResult = field(default_factory=lambda: DetectorResult("conclusion", False, 0.0))
    list_points: DetectorResult = field(default_factory=lambda: DetectorResult("list_points", False, 0.0))
    definitions: DetectorResult = field(default_factory=lambda: DetectorResult("definitions", False, 0.0))
    examples: DetectorResult = field(default_factory=lambda: DetectorResult("examples", False, 0.0))
    coherence: DetectorResult = field(default_factory=lambda: DetectorResult("coherence", False, 0.0))

    # Aggregated scores
    structural_score: float = 0.0       # weighted sum [0, 1]
    structure_bonus: float = 0.0        # actual bonus added to final score
    detected_patterns: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    # Stats
    sentence_count: int = 0
    paragraph_count: int = 0
    word_count: int = 0


# ═══════════════════════════════════════════════════════════════════════
#  Individual Detectors
# ═══════════════════════════════════════════════════════════════════════

class IntroDetector:
    """Detect whether the answer starts with a proper introduction.

    Signals of a good introduction:
    - Restates / paraphrases the question topic
    - Uses definition-style opening ("X is …", "X refers to …")
    - Provides context or scope ("In this context …", "Generally …")
    - First sentence is substantive (>= 8 words)
    """

    _INTRO_PATTERNS = re.compile(
        r"^("
        r"(?:.*?\b(?:is defined as|refers to|is the process|is a |are the |means that|"
        r"can be described|is known as|denotes|consists of|comprises)\b)"
        r"|(?:(?:in this context|generally|broadly|fundamentally|essentially|"
        r"to understand|to begin with|the concept of|the term)\b.*)"
        r")",
        re.IGNORECASE,
    )

    _CONTEXT_STARTERS = re.compile(
        r"^(in computing|in biology|in physics|in chemistry|in mathematics|"
        r"in software engineering|in economics|in the field of|according to|"
        r"the term|the concept|a |an )\b",
        re.IGNORECASE,
    )

    @staticmethod
    def detect(sentences: List[str], full_text: str) -> DetectorResult:
        if not sentences:
            return DetectorResult("intro", False, 0.0)

        first = sentences[0].strip()
        score = 0.0
        evidence = []

        # Check word count of opening sentence
        word_count = len(first.split())
        if word_count >= 12:
            score += 0.3
            evidence.append(f"Substantial opening ({word_count} words)")
        elif word_count >= 8:
            score += 0.15
            evidence.append(f"Moderate opening ({word_count} words)")

        # Check for definition / context-setting pattern
        if IntroDetector._INTRO_PATTERNS.match(first):
            score += 0.5
            evidence.append("Definition/context-setting pattern detected")
        elif IntroDetector._CONTEXT_STARTERS.match(first):
            score += 0.3
            evidence.append("Contextual opening detected")

        # Check if first sentence mentions a proper noun or key topic
        # (heuristic: contains a capitalised word beyond sentence start)
        words = first.split()
        if len(words) > 2:
            mid_caps = [w for w in words[1:] if w[0].isupper() and w.isalpha()]
            if mid_caps:
                score += 0.2
                evidence.append(f"Topic reference: {', '.join(mid_caps[:3])}")

        score = min(1.0, score)
        return DetectorResult("intro", score >= 0.3, round(score, 4), evidence)


class BodyAnalyzer:
    """Analyze the body/middle of the answer for depth and organization.

    Signals:
    - Multiple sentences / paragraphs
    - Elaboration (sentences >= 10 words)
    - Diverse vocabulary (type-token ratio)
    - Technical depth (noun density)
    """

    @staticmethod
    def detect(sentences: List[str], paragraphs: List[str], word_count: int) -> DetectorResult:
        if not sentences:
            return DetectorResult("body", False, 0.0)

        score = 0.0
        evidence = []
        details = {}

        # Sentence depth
        n_sents = len(sentences)
        details["sentence_count"] = n_sents
        if n_sents >= 6:
            score += 0.25
            evidence.append(f"Good depth: {n_sents} sentences")
        elif n_sents >= 3:
            score += 0.15
            evidence.append(f"Moderate depth: {n_sents} sentences")

        # Paragraph structure
        n_paras = len(paragraphs)
        details["paragraph_count"] = n_paras
        if n_paras >= 3:
            score += 0.20
            evidence.append(f"Well-organized: {n_paras} paragraphs")
        elif n_paras >= 2:
            score += 0.10
            evidence.append(f"{n_paras} paragraphs")

        # Elaboration — fraction of sentences with >= 10 words
        elaborate = sum(1 for s in sentences if len(s.split()) >= 10)
        elab_ratio = elaborate / max(n_sents, 1)
        details["elaboration_ratio"] = round(elab_ratio, 3)
        if elab_ratio >= 0.6:
            score += 0.25
            evidence.append(f"Strong elaboration ({elab_ratio:.0%} detailed sentences)")
        elif elab_ratio >= 0.3:
            score += 0.15
            evidence.append(f"Moderate elaboration ({elab_ratio:.0%})")

        # Vocabulary diversity (type-token ratio for first 200 words)
        all_words = " ".join(sentences).lower().split()[:200]
        if all_words:
            ttr = len(set(all_words)) / len(all_words)
            details["type_token_ratio"] = round(ttr, 3)
            if ttr >= 0.65:
                score += 0.15
                evidence.append(f"Rich vocabulary (TTR={ttr:.2f})")
            elif ttr >= 0.50:
                score += 0.08
                evidence.append(f"Adequate vocabulary (TTR={ttr:.2f})")

        # Average sentence length
        avg_len = word_count / max(n_sents, 1)
        details["avg_sentence_length"] = round(avg_len, 1)
        if 12 <= avg_len <= 25:
            score += 0.15
            evidence.append(f"Good sentence length (avg {avg_len:.0f} words)")

        score = min(1.0, score)
        return DetectorResult("body", score >= 0.3, round(score, 4), evidence, details)


class ConclusionDetector:
    """Detect whether the answer ends with a proper conclusion.

    Signals:
    - Transition words: "therefore", "in conclusion", "thus", "hence"
    - Summarizing language: "overall", "in summary", "to summarize"
    - Restating the main point
    - Last sentence is substantive
    """

    _CONCLUSION_MARKERS = re.compile(
        r"\b(therefore|in conclusion|thus|hence|to conclude|"
        r"in summary|to summarize|overall|consequently|"
        r"as a result|to sum up|in short|finally|"
        r"it can be concluded|we can conclude|this shows that|"
        r"this demonstrates|this proves|this indicates)\b",
        re.IGNORECASE,
    )

    _SUMMARY_RESTATE = re.compile(
        r"\b(important|essential|crucial|key point|main idea|"
        r"primary|significant|necessary|fundamental)\b",
        re.IGNORECASE,
    )

    @staticmethod
    def detect(sentences: List[str]) -> DetectorResult:
        if len(sentences) < 2:
            return DetectorResult("conclusion", False, 0.0)

        # Check last 2 sentences
        last_sents = sentences[-2:]
        last_text = " ".join(last_sents)
        score = 0.0
        evidence = []

        # Conclusion markers
        markers = ConclusionDetector._CONCLUSION_MARKERS.findall(last_text)
        if markers:
            score += 0.5
            evidence.append(f"Conclusion marker: '{markers[0]}'")

        # Summarizing / restating
        restates = ConclusionDetector._SUMMARY_RESTATE.findall(last_text)
        if restates:
            score += 0.2
            evidence.append(f"Summary language: '{restates[0]}'")

        # Last sentence substantive
        last = sentences[-1].strip()
        if len(last.split()) >= 10:
            score += 0.2
            evidence.append(f"Substantive closing ({len(last.split())} words)")

        # Check if last sentence is not just a throwaway
        if len(last.split()) >= 6 and not last.endswith("?"):
            score += 0.1
            evidence.append("Declarative closing")

        score = min(1.0, score)
        return DetectorResult("conclusion", score >= 0.3, round(score, 4), evidence)


class ListPointDetector:
    """Detect structured lists in the answer.

    Signals:
    - Numbered items: "1.", "2.", "1)", "2)"
    - Bullet/dash items: "- ", "* ", "• "
    - Roman numerals: "i.", "ii.", "iii."
    - Letter items: "a.", "b.", "a)"
    - Comma-separated enumerations: "such as X, Y, and Z"
    - Semicolon-separated points
    """

    _NUMBERED = re.compile(r"^[\s]*(\d{1,2})[.)]\s+", re.MULTILINE)
    _BULLET = re.compile(r"^[\s]*[-*\u2022\u25CF\u25CB\u25AA]\s+", re.MULTILINE)
    _ROMAN = re.compile(r"^[\s]*(i{1,3}|iv|vi{0,3}|ix|x)[.)]\s+", re.MULTILINE | re.IGNORECASE)
    _LETTER = re.compile(r"^[\s]*[a-hA-H][.)]\s+", re.MULTILINE)
    _ENUM_COMMA = re.compile(
        r"\b(?:such as|including|like|namely|e\.g\.)\s+[^.]+,\s+[^.]+(?:,?\s+and\s+[^.]+)?",
        re.IGNORECASE,
    )
    _COLON_LIST = re.compile(r":\s*\n\s*[-*\d]", re.MULTILINE)

    @staticmethod
    def detect(full_text: str) -> DetectorResult:
        score = 0.0
        evidence = []
        details = {}

        # Numbered list
        numbered = ListPointDetector._NUMBERED.findall(full_text)
        details["numbered_items"] = len(numbered)
        if len(numbered) >= 3:
            score += 0.4
            evidence.append(f"{len(numbered)} numbered points")
        elif len(numbered) >= 2:
            score += 0.2
            evidence.append(f"{len(numbered)} numbered points")

        # Bullet list
        bullets = ListPointDetector._BULLET.findall(full_text)
        details["bullet_items"] = len(bullets)
        if len(bullets) >= 2:
            score += 0.3
            evidence.append(f"{len(bullets)} bullet points")

        # Roman / letter lists
        roman = ListPointDetector._ROMAN.findall(full_text)
        letter = ListPointDetector._LETTER.findall(full_text)
        if roman:
            score += 0.2
            evidence.append(f"Roman numeral list ({len(roman)} items)")
        if letter:
            score += 0.2
            evidence.append(f"Lettered list ({len(letter)} items)")

        # Comma-separated enumerations
        enums = ListPointDetector._ENUM_COMMA.findall(full_text)
        details["enumerations"] = len(enums)
        if enums:
            score += 0.2
            evidence.append(f"{len(enums)} comma-separated enumeration(s)")

        # Colon-followed list
        if ListPointDetector._COLON_LIST.search(full_text):
            score += 0.15
            evidence.append("Colon-introduced list detected")

        score = min(1.0, score)
        return DetectorResult("list_points", score >= 0.2, round(score, 4), evidence, details)


class DefinitionDetector:
    """Detect formal definitions in the answer.

    Patterns:
    - "X is defined as Y"
    - "X refers to Y"
    - "X is the process of Y"
    - "X means Y"
    - "X can be described as Y"
    - "X is a type of Y"
    - "X, also known as Y, is Z"
    """

    _DEF_PATTERNS = [
        re.compile(r"\b\w+(?:\s+\w+){0,3}\s+(?:is|are)\s+defined\s+as\b", re.IGNORECASE),
        re.compile(r"\b\w+(?:\s+\w+){0,3}\s+refers?\s+to\b", re.IGNORECASE),
        re.compile(r"\b\w+(?:\s+\w+){0,3}\s+(?:is|are)\s+(?:the\s+)?process\s+(?:of|by which)\b", re.IGNORECASE),
        re.compile(r"\b\w+(?:\s+\w+){0,3}\s+(?:is|are)\s+(?:a|an)\s+(?:type|kind|form|method|technique)\s+of\b", re.IGNORECASE),
        re.compile(r"\b\w+(?:\s+\w+){0,3}\s+means\s+(?:that|the)\b", re.IGNORECASE),
        re.compile(r"\b\w+(?:\s+\w+){0,3}\s+can\s+be\s+(?:defined|described|understood)\s+as\b", re.IGNORECASE),
        re.compile(r"\b\w+(?:\s+\w+){0,3},\s*also\s+known\s+as\b", re.IGNORECASE),
        re.compile(r"\b\w+(?:\s+\w+){0,3}\s+(?:is|are)\s+known\s+as\b", re.IGNORECASE),
        re.compile(r"\b\w+(?:\s+\w+){0,3}\s+(?:is|are)\s+(?:a|an)\s+\w+\s+that\b", re.IGNORECASE),
        re.compile(r"\bthe\s+term\s+['\"]?\w+['\"]?\s+(?:means|refers|denotes)\b", re.IGNORECASE),
    ]

    @staticmethod
    def detect(full_text: str) -> DetectorResult:
        score = 0.0
        evidence = []
        matched_patterns = 0

        for pat in DefinitionDetector._DEF_PATTERNS:
            matches = pat.findall(full_text)
            if matches:
                matched_patterns += 1
                snippet = matches[0][:60] if isinstance(matches[0], str) else str(matches[0])[:60]
                evidence.append(f"Definition pattern: '{snippet}...'")

        if matched_patterns >= 3:
            score = 1.0
        elif matched_patterns >= 2:
            score = 0.7
        elif matched_patterns >= 1:
            score = 0.4

        return DetectorResult("definitions", matched_patterns > 0, round(score, 4), evidence,
                              {"pattern_count": matched_patterns})


class ExampleDetector:
    """Detect concrete examples in the answer.

    Signals:
    - "for example", "for instance", "e.g.", "such as"
    - Specific named entities (proper nouns as examples)
    - Numeric data / statistics
    - Case studies or scenarios ("consider the case of…")
    - Analogies ("like…", "similar to…")
    """

    _EXAMPLE_MARKERS = re.compile(
        r"\b(for example|for instance|e\.g\.|such as|"
        r"consider the case|consider the|take for example|"
        r"to illustrate|as an example|an example of|"
        r"a good example|a typical example|"
        r"in practice|in real life|a case in point)\b",
        re.IGNORECASE,
    )

    _ANALOGY = re.compile(
        r"\b(similar\s+to|analogous\s+to|just\s+like|much\s+like|"
        r"comparable\s+to|resembles|akin\s+to)\b",
        re.IGNORECASE | re.DOTALL,
    )

    _NUMERIC = re.compile(r"\b\d+(?:\.\d+)?(?:\s*%|\s*percent|\s*times|\s*years)\b", re.IGNORECASE)

    _PROPER_NOUN_EXAMPLE = re.compile(
        r"\b(?:(?:like|such as|e\.g\.)\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    )

    @staticmethod
    def detect(full_text: str, sentences: List[str]) -> DetectorResult:
        score = 0.0
        evidence = []
        details = {}

        # Explicit example markers
        markers = ExampleDetector._EXAMPLE_MARKERS.findall(full_text)
        details["example_markers"] = len(markers)
        if markers:
            score += min(0.5, len(markers) * 0.2)
            evidence.append(f"{len(markers)} example marker(s): {', '.join(list(set(markers))[:3])}")

        # Analogies
        analogies = ExampleDetector._ANALOGY.findall(full_text)
        details["analogies"] = len(analogies)
        if analogies:
            score += 0.2
            evidence.append(f"Analogy detected: '{analogies[0]}'")

        # Numeric / statistical data
        numerics = ExampleDetector._NUMERIC.findall(full_text)
        details["numeric_references"] = len(numerics)
        if numerics:
            score += 0.15
            evidence.append(f"Numeric data: {', '.join(numerics[:3])}")

        # Named examples (proper nouns after "like"/"such as")
        named = ExampleDetector._PROPER_NOUN_EXAMPLE.findall(full_text)
        details["named_examples"] = len(named)
        if named:
            score += 0.15
            evidence.append(f"Named examples: {', '.join(named[:3])}")

        score = min(1.0, score)
        return DetectorResult("examples", score >= 0.2, round(score, 4), evidence, details)


class CoherenceAnalyzer:
    """Analyze logical flow and coherence of the answer.

    Signals:
    - Transition words (additive, adversative, causal, sequential)
    - Topic consistency (first and last sentences share words)
    - Logical connectors density
    - Sentence-to-sentence flow (shared vocabulary between adjacent sentences)
    """

    _ADDITIVE = re.compile(
        r"\b(moreover|furthermore|in addition|additionally|also|"
        r"besides|what is more|equally important)\b", re.IGNORECASE,
    )
    _ADVERSATIVE = re.compile(
        r"\b(however|on the other hand|nevertheless|although|"
        r"despite|in contrast|whereas|but|yet|nonetheless)\b", re.IGNORECASE,
    )
    _CAUSAL = re.compile(
        r"\b(therefore|because|since|consequently|as a result|"
        r"due to|owing to|hence|thus|so that|leads to|causes)\b", re.IGNORECASE,
    )
    _SEQUENTIAL = re.compile(
        r"\b(first|firstly|second|secondly|third|thirdly|"
        r"next|then|finally|lastly|subsequently|meanwhile|"
        r"at the same time|after that|following this)\b", re.IGNORECASE,
    )

    @staticmethod
    def detect(sentences: List[str], full_text: str) -> DetectorResult:
        if len(sentences) < 2:
            return DetectorResult("coherence", False, 0.0)

        score = 0.0
        evidence = []
        details = {}

        # Count transition types
        add_count = len(CoherenceAnalyzer._ADDITIVE.findall(full_text))
        adv_count = len(CoherenceAnalyzer._ADVERSATIVE.findall(full_text))
        cau_count = len(CoherenceAnalyzer._CAUSAL.findall(full_text))
        seq_count = len(CoherenceAnalyzer._SEQUENTIAL.findall(full_text))

        total_trans = add_count + adv_count + cau_count + seq_count
        details["transitions"] = {
            "additive": add_count,
            "adversative": adv_count,
            "causal": cau_count,
            "sequential": seq_count,
            "total": total_trans,
        }

        # Transition density
        n_sents = len(sentences)
        trans_density = total_trans / max(n_sents, 1)
        details["transition_density"] = round(trans_density, 3)

        if total_trans >= 4:
            score += 0.3
            evidence.append(f"Rich transitions ({total_trans} connectors)")
        elif total_trans >= 2:
            score += 0.15
            evidence.append(f"Some transitions ({total_trans} connectors)")

        # Variety of transition types (at least 2 different types)
        types_used = sum(1 for c in [add_count, adv_count, cau_count, seq_count] if c > 0)
        details["transition_types_used"] = types_used
        if types_used >= 3:
            score += 0.25
            evidence.append(f"Diverse connectors ({types_used} types)")
        elif types_used >= 2:
            score += 0.15
            evidence.append(f"{types_used} connector types")

        # Sentence-to-sentence vocabulary overlap (lexical cohesion)
        overlaps = []
        for i in range(len(sentences) - 1):
            words_a = set(sentences[i].lower().split()) - _STOPWORDS
            words_b = set(sentences[i + 1].lower().split()) - _STOPWORDS
            if words_a and words_b:
                overlap = len(words_a & words_b) / min(len(words_a), len(words_b))
                overlaps.append(overlap)

        if overlaps:
            avg_overlap = sum(overlaps) / len(overlaps)
            details["avg_lexical_cohesion"] = round(avg_overlap, 3)
            if avg_overlap >= 0.15:
                score += 0.25
                evidence.append(f"Good lexical cohesion ({avg_overlap:.2f})")
            elif avg_overlap >= 0.08:
                score += 0.12
                evidence.append(f"Moderate lexical cohesion ({avg_overlap:.2f})")

        # Topic consistency: first and last sentence share content words
        if len(sentences) >= 3:
            first_words = set(sentences[0].lower().split()) - _STOPWORDS
            last_words = set(sentences[-1].lower().split()) - _STOPWORDS
            if first_words and last_words:
                topic_overlap = len(first_words & last_words) / max(len(first_words), 1)
                details["topic_consistency"] = round(topic_overlap, 3)
                if topic_overlap >= 0.15:
                    score += 0.2
                    evidence.append("Good topic consistency (intro-conclusion link)")

        score = min(1.0, score)
        return DetectorResult("coherence", score >= 0.2, round(score, 4), evidence, details)


# ── Stopwords set (lightweight, no NLTK dependency) ─────────────────
_STOPWORDS: Set[str] = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "must", "can", "could", "am", "it", "its",
    "i", "me", "my", "we", "our", "you", "your", "he", "him", "his",
    "she", "her", "they", "them", "their", "this", "that", "these",
    "those", "of", "in", "to", "for", "with", "on", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above",
    "below", "between", "out", "off", "over", "under", "again", "further",
    "then", "once", "and", "but", "or", "nor", "not", "no", "so",
    "if", "when", "which", "who", "whom", "what", "where", "how",
    "all", "each", "every", "both", "few", "more", "most", "other",
    "some", "such", "only", "own", "same", "than", "too", "very",
    "just", "about", "up", "down", "here", "there", "any",
}


# ═══════════════════════════════════════════════════════════════════════
#  Master Orchestrator
# ═══════════════════════════════════════════════════════════════════════

class StructuralAnalyzer:
    """
    Master orchestrator for Upgrade 8 — Logical Structure Evaluation.

    Call ``analyze(student_text)`` to get a ``StructuralReport``.

    The structural score is used as a **bonus** on top of content-based
    scoring, not as a full weighted component.  This avoids penalising
    correct but informally-written answers while rewarding professional
    structure.
    """

    # Detector weights in the structural_score formula
    W_INTRO       = 0.15
    W_BODY        = 0.25
    W_CONCLUSION  = 0.10
    W_LIST_POINTS = 0.15
    W_DEFINITIONS = 0.10
    W_EXAMPLES    = 0.10
    W_COHERENCE   = 0.15

    # Bonus cap: maximum structural bonus added to final score
    BONUS_CAP = 0.08

    def __init__(self):
        self._nlp = None
        try:
            import spacy
            self._nlp = spacy.load("en_core_web_sm")
        except Exception:
            logger.warning("spaCy not available; using regex sentence splitting")

    # ─── Public API ──────────────────────────────────────────────────

    def analyze(self, student_text: str) -> StructuralReport:
        """Run all 7 detectors and produce an aggregated ``StructuralReport``."""
        if not student_text or len(student_text.strip()) < 10:
            return StructuralReport()

        # Preprocessing
        sentences = self._split_sentences(student_text)
        paragraphs = self._split_paragraphs(student_text)
        word_count = len(student_text.split())

        # Run detectors
        intro_r    = IntroDetector.detect(sentences, student_text)
        body_r     = BodyAnalyzer.detect(sentences, paragraphs, word_count)
        concl_r    = ConclusionDetector.detect(sentences)
        list_r     = ListPointDetector.detect(student_text)
        defn_r     = DefinitionDetector.detect(student_text)
        example_r  = ExampleDetector.detect(student_text, sentences)
        coher_r    = CoherenceAnalyzer.detect(sentences, student_text)

        # Weighted structural score
        structural_score = (
            self.W_INTRO       * intro_r.score +
            self.W_BODY        * body_r.score +
            self.W_CONCLUSION  * concl_r.score +
            self.W_LIST_POINTS * list_r.score +
            self.W_DEFINITIONS * defn_r.score +
            self.W_EXAMPLES    * example_r.score +
            self.W_COHERENCE   * coher_r.score
        )
        structural_score = min(1.0, structural_score)

        # Bonus (capped)
        structure_bonus = structural_score * self.BONUS_CAP

        # Detected patterns list
        detected = []
        for r in [intro_r, body_r, concl_r, list_r, defn_r, example_r, coher_r]:
            if r.detected:
                detected.append(r.name)

        # Generate improvement suggestions
        suggestions = self._generate_suggestions(
            intro_r, body_r, concl_r, list_r, defn_r, example_r, coher_r,
        )

        return StructuralReport(
            intro=intro_r,
            body=body_r,
            conclusion=concl_r,
            list_points=list_r,
            definitions=defn_r,
            examples=example_r,
            coherence=coher_r,
            structural_score=round(structural_score, 4),
            structure_bonus=round(structure_bonus, 4),
            detected_patterns=detected,
            suggestions=suggestions,
            sentence_count=len(sentences),
            paragraph_count=len(paragraphs),
            word_count=word_count,
        )

    def get_detailed_report(self, report: StructuralReport) -> Dict:
        """Human-readable summary dict for API responses."""
        return {
            "structural_score": report.structural_score,
            "structure_bonus": report.structure_bonus,
            "detected_patterns": report.detected_patterns,
            "suggestions": report.suggestions,
            "stats": {
                "sentence_count": report.sentence_count,
                "paragraph_count": report.paragraph_count,
                "word_count": report.word_count,
            },
            "detectors": {
                "intro": {
                    "detected": report.intro.detected,
                    "score": report.intro.score,
                    "evidence": report.intro.evidence,
                },
                "body": {
                    "detected": report.body.detected,
                    "score": report.body.score,
                    "evidence": report.body.evidence,
                    "details": report.body.details,
                },
                "conclusion": {
                    "detected": report.conclusion.detected,
                    "score": report.conclusion.score,
                    "evidence": report.conclusion.evidence,
                },
                "list_points": {
                    "detected": report.list_points.detected,
                    "score": report.list_points.score,
                    "evidence": report.list_points.evidence,
                    "details": report.list_points.details,
                },
                "definitions": {
                    "detected": report.definitions.detected,
                    "score": report.definitions.score,
                    "evidence": report.definitions.evidence,
                },
                "examples": {
                    "detected": report.examples.detected,
                    "score": report.examples.score,
                    "evidence": report.examples.evidence,
                    "details": report.examples.details,
                },
                "coherence": {
                    "detected": report.coherence.detected,
                    "score": report.coherence.score,
                    "evidence": report.coherence.evidence,
                    "details": report.coherence.details,
                },
            },
        }

    # ─── Private Helpers ─────────────────────────────────────────────

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences using spaCy or regex fallback."""
        if self._nlp is not None:
            doc = self._nlp(text[:100000])
            return [s.text.strip() for s in doc.sents if s.text.strip()]
        # Regex fallback
        parts = re.split(r'(?<=[.!?])\s+', text)
        return [p.strip() for p in parts if p.strip()]

    @staticmethod
    def _split_paragraphs(text: str) -> List[str]:
        """Split text into paragraphs (double newline or single newline with indent)."""
        # Try double newline first
        paras = re.split(r'\n\s*\n', text)
        paras = [p.strip() for p in paras if p.strip()]
        if len(paras) >= 2:
            return paras
        # Fall back to single newlines
        paras = re.split(r'\n', text)
        paras = [p.strip() for p in paras if p.strip() and len(p.strip()) > 15]
        if len(paras) >= 2:
            return paras
        # Single paragraph
        return [text.strip()] if text.strip() else []

    @staticmethod
    def _generate_suggestions(
        intro: DetectorResult,
        body: DetectorResult,
        conclusion: DetectorResult,
        list_points: DetectorResult,
        definitions: DetectorResult,
        examples: DetectorResult,
        coherence: DetectorResult,
    ) -> List[str]:
        """Generate actionable improvement suggestions."""
        suggestions = []

        if not intro.detected:
            suggestions.append(
                "Start with a clear introduction that defines the topic or sets context."
            )

        if body.score < 0.4:
            suggestions.append(
                "Develop your answer with more detailed sentences and multiple paragraphs."
            )

        if not conclusion.detected:
            suggestions.append(
                "End with a brief conclusion or summary statement (e.g., 'Therefore...', 'In conclusion...')."
            )

        if not list_points.detected:
            suggestions.append(
                "Use numbered points or bullet lists to organize key facts clearly."
            )

        if not definitions.detected:
            suggestions.append(
                "Include formal definitions — e.g., 'X is defined as...' or 'X refers to...'."
            )

        if not examples.detected:
            suggestions.append(
                "Add concrete examples to strengthen your answer (e.g., 'For example, ...')."
            )

        if coherence.score < 0.3:
            suggestions.append(
                "Use transition words (however, therefore, moreover) to improve logical flow."
            )

        if not suggestions:
            suggestions.append("Excellent structure! Your answer is well-organized.")

        return suggestions
