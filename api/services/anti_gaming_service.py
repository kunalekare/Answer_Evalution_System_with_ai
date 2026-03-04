"""
Anti-Gaming Protection Service  (Upgrade 9)
=============================================
Detects and penalises student answer manipulation strategies.

Why This Matters
-----------------
Students may attempt to game automated evaluation by:
    - Copying keywords randomly without coherent sentences
    - Writing unrelated long text to inflate length
    - Adding repeated sentences to pad answers
    - Shuffling model-answer sentences with minor edits
    - Inserting filler / hedging phrases
    - Typing gibberish or random characters

Architecture: 6-Layer Detection Pipeline
------------------------------------------

1. **RepetitionDetector**      — Near-duplicate sentence pairs (embedding cosine > 0.9)
2. **IrrelevanceDetector**     — Sentences with < 0.2 max similarity to any model sentence
3. **KeywordStuffingDetector** — High keyword hit-rate but low semantic coherence
4. **GibberishDetector**       — Character entropy, real-word ratio, vocabulary diversity
5. **PaddingDetector**         — Filler phrases, hedging, circular restatement
6. **CopyShuffleDetector**     — Rearranged model sentences with minor word swaps

Scoring Model
--------------
Each detector produces a penalty ∈ [0, detector_cap].
The combined penalty is capped at ``MAX_TOTAL_PENALTY`` (default 0.40)
and **subtracted** from the weighted content score:

    final = weighted_score + structure_bonus − gaming_penalty

Dependencies (all already installed):
    - sentence-transformers (all-MiniLM-L6-v2) — sentence embeddings
    - numpy — cosine similarity, statistics
    - re (stdlib) — pattern matching
    - math / collections (stdlib) — entropy, counters
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger("AssessIQ.AntiGaming")


# ═══════════════════════════════════════════════════════════════════════
#  Data Structures
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class DetectionResult:
    """Output from a single anti-gaming detector."""
    name: str
    detected: bool
    penalty: float        # 0.0 – detector cap
    severity: str         # "none" | "low" | "medium" | "high"
    evidence: List[str] = field(default_factory=list)
    details: Dict = field(default_factory=dict)


@dataclass
class AntiGamingReport:
    """Complete output from the anti-gaming pipeline."""
    # Per-detector results
    repetition: DetectionResult = field(
        default_factory=lambda: DetectionResult("repetition", False, 0.0, "none"))
    irrelevance: DetectionResult = field(
        default_factory=lambda: DetectionResult("irrelevance", False, 0.0, "none"))
    keyword_stuffing: DetectionResult = field(
        default_factory=lambda: DetectionResult("keyword_stuffing", False, 0.0, "none"))
    gibberish: DetectionResult = field(
        default_factory=lambda: DetectionResult("gibberish", False, 0.0, "none"))
    padding: DetectionResult = field(
        default_factory=lambda: DetectionResult("padding", False, 0.0, "none"))
    copy_shuffle: DetectionResult = field(
        default_factory=lambda: DetectionResult("copy_shuffle", False, 0.0, "none"))

    # Aggregated
    total_penalty: float = 0.0          # capped combined penalty
    flags: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    is_flagged: bool = False            # True if any detector fires at "high"
    confidence: float = 0.0             # 0-1 how confident we are gaming occurred


# ═══════════════════════════════════════════════════════════════════════
#  Shared Utilities
# ═══════════════════════════════════════════════════════════════════════

def _classify_severity(penalty: float, low: float, med: float) -> str:
    """Map a penalty value to a severity label."""
    if penalty <= 0:
        return "none"
    if penalty < low:
        return "low"
    if penalty < med:
        return "medium"
    return "high"


def _split_sentences_simple(text: str) -> List[str]:
    """Regex sentence splitter (no spaCy dependency)."""
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p.strip() for p in parts if p.strip() and len(p.strip()) > 3]


# Lightweight stopwords set
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
#  Layer 1: Repetition Detector
# ═══════════════════════════════════════════════════════════════════════

class RepetitionDetector:
    """
    Detect near-duplicate sentences within the student answer.

    Strategy:
    - Compute pairwise cosine similarity between all sentence embeddings
    - Pairs with similarity > THRESHOLD are flagged as repetitions
    - Also detects exact substring repetitions (no embeddings needed)

    Penalty scales with the fraction of repeated sentences.
    """

    SIMILARITY_THRESHOLD = 0.90    # cosine sim above this = near-duplicate
    EXACT_OVERLAP_THRESHOLD = 0.85 # word overlap ratio for exact match
    MAX_PENALTY = 0.20

    @staticmethod
    def detect(
        sentences: List[str],
        sentence_embeddings: Optional[np.ndarray] = None,
    ) -> DetectionResult:
        if len(sentences) < 2:
            return DetectionResult("repetition", False, 0.0, "none")

        evidence = []
        details: Dict = {}
        duplicate_pairs = []
        duplicate_indices: Set[int] = set()

        n = len(sentences)

        # Method A: Embedding-based similarity
        if sentence_embeddings is not None and len(sentence_embeddings) >= 2:
            # Cosine similarity matrix
            norms = np.linalg.norm(sentence_embeddings, axis=1, keepdims=True)
            norms = np.maximum(norms, 1e-10)
            normed = sentence_embeddings / norms
            sim_matrix = normed @ normed.T

            for i in range(n):
                for j in range(i + 1, n):
                    if sim_matrix[i, j] >= RepetitionDetector.SIMILARITY_THRESHOLD:
                        duplicate_pairs.append((i, j, float(sim_matrix[i, j])))
                        duplicate_indices.update([i, j])

        # Method B: Word-overlap fallback (catches exact copy-paste)
        word_sets = [set(s.lower().split()) - _STOPWORDS for s in sentences]
        for i in range(n):
            for j in range(i + 1, n):
                if (i, j) not in {(p[0], p[1]) for p in duplicate_pairs}:
                    if word_sets[i] and word_sets[j]:
                        overlap = len(word_sets[i] & word_sets[j])
                        ratio = overlap / min(len(word_sets[i]), len(word_sets[j]))
                        if ratio >= RepetitionDetector.EXACT_OVERLAP_THRESHOLD:
                            duplicate_pairs.append((i, j, ratio))
                            duplicate_indices.update([i, j])

        details["duplicate_pair_count"] = len(duplicate_pairs)
        details["duplicate_sentence_indices"] = sorted(duplicate_indices)
        details["total_sentences"] = n

        if not duplicate_pairs:
            return DetectionResult("repetition", False, 0.0, "none", [], details)

        # Penalty proportional to fraction of duplicated sentences
        dup_fraction = len(duplicate_indices) / max(n, 1)
        penalty = min(dup_fraction * 0.35, RepetitionDetector.MAX_PENALTY)

        for i, j, sim in duplicate_pairs[:5]:
            snip_i = sentences[i][:50]
            snip_j = sentences[j][:50]
            evidence.append(f"Sentences {i+1}&{j+1} similar ({sim:.2f}): '{snip_i}…' ↔ '{snip_j}…'")

        severity = _classify_severity(penalty, 0.05, 0.12)
        return DetectionResult("repetition", True, round(penalty, 4), severity, evidence, details)


# ═══════════════════════════════════════════════════════════════════════
#  Layer 2: Irrelevance Detector
# ═══════════════════════════════════════════════════════════════════════

class IrrelevanceDetector:
    """
    Detect sentences that are completely unrelated to the model answer.

    For each student sentence, compute max similarity to any model sentence.
    If max_sim < THRESHOLD repeatedly, it indicates off-topic padding.

    Also checks:
    - Sequential irrelevant sentences (consecutive off-topic blocks)
    - Overall irrelevance ratio
    """

    SIMILARITY_THRESHOLD = 0.20   # below this = irrelevant to model
    CONSECUTIVE_BONUS = 0.03      # extra penalty per consecutive irrelevant pair
    MAX_PENALTY = 0.25

    @staticmethod
    def detect(
        student_sentences: List[str],
        model_sentences: List[str],
        student_embeddings: Optional[np.ndarray] = None,
        model_embeddings: Optional[np.ndarray] = None,
    ) -> DetectionResult:
        if not student_sentences or not model_sentences:
            return DetectionResult("irrelevance", False, 0.0, "none")

        evidence = []
        details: Dict = {}
        irrelevant_indices: List[int] = []

        n_stu = len(student_sentences)
        n_mod = len(model_sentences)

        # Compute cross-similarity: student × model
        if (student_embeddings is not None and model_embeddings is not None
                and len(student_embeddings) > 0 and len(model_embeddings) > 0):
            # Normalize
            s_norm = student_embeddings / np.maximum(
                np.linalg.norm(student_embeddings, axis=1, keepdims=True), 1e-10)
            m_norm = model_embeddings / np.maximum(
                np.linalg.norm(model_embeddings, axis=1, keepdims=True), 1e-10)
            cross_sim = s_norm @ m_norm.T  # (n_stu, n_mod)

            max_sims = cross_sim.max(axis=1)  # max similarity to any model sentence

            for i in range(n_stu):
                if max_sims[i] < IrrelevanceDetector.SIMILARITY_THRESHOLD:
                    irrelevant_indices.append(i)
        else:
            # Word-overlap fallback
            model_words = [set(s.lower().split()) - _STOPWORDS for s in model_sentences]
            for i, sent in enumerate(student_sentences):
                stu_words = set(sent.lower().split()) - _STOPWORDS
                if not stu_words:
                    irrelevant_indices.append(i)
                    continue
                max_overlap = 0.0
                for mw in model_words:
                    if mw:
                        overlap = len(stu_words & mw) / max(len(stu_words), 1)
                        max_overlap = max(max_overlap, overlap)
                if max_overlap < 0.10:
                    irrelevant_indices.append(i)

        details["irrelevant_count"] = len(irrelevant_indices)
        details["total_student_sentences"] = n_stu
        details["irrelevance_ratio"] = round(len(irrelevant_indices) / max(n_stu, 1), 3)
        details["irrelevant_indices"] = irrelevant_indices[:20]

        if not irrelevant_indices:
            return DetectionResult("irrelevance", False, 0.0, "none", [], details)

        # Base penalty: proportional to irrelevance ratio
        irr_ratio = len(irrelevant_indices) / max(n_stu, 1)
        penalty = irr_ratio * 0.30

        # Consecutive irrelevant sentences bonus
        consecutive_count = 0
        for k in range(len(irrelevant_indices) - 1):
            if irrelevant_indices[k + 1] == irrelevant_indices[k] + 1:
                consecutive_count += 1
        penalty += consecutive_count * IrrelevanceDetector.CONSECUTIVE_BONUS
        details["consecutive_irrelevant_pairs"] = consecutive_count

        penalty = min(penalty, IrrelevanceDetector.MAX_PENALTY)

        for idx in irrelevant_indices[:4]:
            snippet = student_sentences[idx][:60]
            evidence.append(f"Sentence {idx+1} irrelevant: '{snippet}…'")

        severity = _classify_severity(penalty, 0.06, 0.15)
        return DetectionResult("irrelevance", True, round(penalty, 4), severity, evidence, details)


# ═══════════════════════════════════════════════════════════════════════
#  Layer 3: Keyword Stuffing Detector
# ═══════════════════════════════════════════════════════════════════════

class KeywordStuffingDetector:
    """
    Detect keyword stuffing: high keyword count but low semantic coherence.

    Signals:
    - Keyword density is unusually high (> 2× model's density)
    - Semantic score is significantly lower than keyword score
    - Keywords appear without connecting sentences
    - High keyword count in very short text (listing keywords)

    Advanced: also detects "keyword salad" — keywords appear but
    surrounding context is incoherent (low average sentence embedding similarity).
    """

    MAX_PENALTY = 0.20
    # If keyword_score - semantic_score > this, suspect stuffing
    SCORE_GAP_THRESHOLD = 0.30
    # If keyword density > model density × this, suspect stuffing
    DENSITY_MULTIPLIER = 2.5

    @staticmethod
    def detect(
        student_text: str,
        model_text: str,
        keyword_score: float,
        semantic_score: float,
        matched_keywords: List[str],
        student_sentences: List[str],
        student_embeddings: Optional[np.ndarray] = None,
    ) -> DetectionResult:
        evidence = []
        details: Dict = {}
        penalty = 0.0

        stu_words = student_text.lower().split()
        mod_words = model_text.lower().split()
        n_stu_words = len(stu_words)
        n_mod_words = len(mod_words)

        if n_stu_words < 5:
            return DetectionResult("keyword_stuffing", False, 0.0, "none")

        # ── Signal 1: Score gap (keyword >> semantic) ───────────────
        score_gap = keyword_score - semantic_score
        details["score_gap"] = round(score_gap, 3)
        if score_gap > KeywordStuffingDetector.SCORE_GAP_THRESHOLD:
            gap_penalty = min((score_gap - KeywordStuffingDetector.SCORE_GAP_THRESHOLD) * 0.5, 0.10)
            penalty += gap_penalty
            evidence.append(
                f"Keyword-semantic gap: keywords={keyword_score:.2f}, "
                f"semantic={semantic_score:.2f} (gap={score_gap:.2f})"
            )

        if not matched_keywords:
            # Even without explicit matched_keywords, score gap alone can signal stuffing
            if penalty > 0:
                penalty = min(penalty, KeywordStuffingDetector.MAX_PENALTY)
                severity = _classify_severity(penalty, 0.04, 0.10)
                return DetectionResult("keyword_stuffing", True, round(penalty, 4), severity, evidence, details)
            return DetectionResult("keyword_stuffing", False, 0.0, "none")

        # ── Signal 2: Abnormal keyword density ─────────────────────
        kw_set = {k.lower() for k in matched_keywords}
        stu_kw_count = sum(1 for w in stu_words if w in kw_set)
        mod_kw_count = sum(1 for w in mod_words if w in kw_set)

        stu_density = stu_kw_count / max(n_stu_words, 1)
        mod_density = mod_kw_count / max(n_mod_words, 1)
        details["student_keyword_density"] = round(stu_density, 4)
        details["model_keyword_density"] = round(mod_density, 4)

        if mod_density > 0 and stu_density > mod_density * KeywordStuffingDetector.DENSITY_MULTIPLIER:
            density_ratio = stu_density / max(mod_density, 0.001)
            density_penalty = min((density_ratio - KeywordStuffingDetector.DENSITY_MULTIPLIER) * 0.04, 0.08)
            penalty += density_penalty
            evidence.append(
                f"Keyword density {stu_density:.3f} is {density_ratio:.1f}× model's {mod_density:.3f}"
            )

        # ── Signal 3: Keyword salad — low inter-sentence coherence ──
        if student_embeddings is not None and len(student_embeddings) >= 3:
            norms = np.linalg.norm(student_embeddings, axis=1, keepdims=True)
            norms = np.maximum(norms, 1e-10)
            normed = student_embeddings / norms
            sim_matrix = normed @ normed.T

            # Average off-diagonal similarity
            n = len(student_embeddings)
            mask = ~np.eye(n, dtype=bool)
            avg_coherence = float(sim_matrix[mask].mean()) if n > 1 else 1.0
            details["avg_inter_sentence_coherence"] = round(avg_coherence, 4)

            if avg_coherence < 0.25 and keyword_score > 0.5:
                coherence_penalty = min((0.25 - avg_coherence) * 0.4, 0.08)
                penalty += coherence_penalty
                evidence.append(
                    f"Low inter-sentence coherence ({avg_coherence:.3f}) despite high keywords"
                )

        # ── Signal 4: Keywords in very short / fragmented text ──────
        avg_sent_len = n_stu_words / max(len(student_sentences), 1)
        details["avg_sentence_length"] = round(avg_sent_len, 1)
        if avg_sent_len < 4 and len(matched_keywords) >= 3:
            penalty += 0.06
            evidence.append(
                f"Very short sentences (avg {avg_sent_len:.1f} words) with {len(matched_keywords)} keywords — likely keyword list"
            )

        penalty = min(penalty, KeywordStuffingDetector.MAX_PENALTY)

        if penalty <= 0:
            return DetectionResult("keyword_stuffing", False, 0.0, "none", [], details)

        severity = _classify_severity(penalty, 0.04, 0.10)
        return DetectionResult("keyword_stuffing", True, round(penalty, 4), severity, evidence, details)


# ═══════════════════════════════════════════════════════════════════════
#  Layer 4: Gibberish Detector
# ═══════════════════════════════════════════════════════════════════════

class GibberishDetector:
    """
    Detect nonsensical / random text.

    Signals:
    - Character entropy (random chars → high entropy, normal text ~4.0-4.5)
    - Real-word ratio (fraction of words found in a basic dictionary)
    - Vowel-consonant ratio anomaly
    - Character type diversity anomaly (excessive punctuation, digits, symbols)
    - Very low type-token ratio on short text
    """

    MAX_PENALTY = 0.30
    # Above this character entropy = suspicious
    HIGH_ENTROPY_THRESHOLD = 4.8
    # Below this real-word ratio = gibberish
    LOW_REAL_WORD_RATIO = 0.40

    # Basic English word set (top ~500 common words)
    _COMMON_WORDS: Optional[Set[str]] = None

    @classmethod
    def _get_common_words(cls) -> Set[str]:
        if cls._COMMON_WORDS is not None:
            return cls._COMMON_WORDS
        # Build a lightweight set of common English words from stopwords + common vocab
        common = set(_STOPWORDS)
        common.update({
            "also", "back", "because", "been", "call", "come", "day", "did",
            "even", "find", "first", "get", "give", "go", "good", "great",
            "hand", "help", "high", "keep", "know", "large", "last", "let",
            "life", "like", "line", "long", "look", "made", "make", "many",
            "much", "name", "need", "new", "next", "number", "old", "one",
            "open", "order", "part", "people", "place", "point", "right",
            "said", "same", "say", "set", "show", "small", "start", "state",
            "still", "take", "tell", "think", "three", "time", "turn", "two",
            "use", "used", "want", "way", "well", "work", "world", "year",
            "data", "system", "process", "computer", "program", "software",
            "method", "function", "class", "object", "type", "value", "code",
            "example", "different", "important", "information", "result",
            "problem", "question", "answer", "student", "learning", "define",
            "defined", "definition", "means", "refers", "concept", "theory",
            "based", "include", "includes", "including", "following", "given",
            "called", "known", "describes", "description", "explain", "provides",
            "used", "using", "also", "however", "therefore", "thus", "hence",
            "since", "because", "although", "while", "where", "when", "which",
            "between", "through", "during", "other", "another", "such",
            "each", "every", "these", "those", "there", "here", "most",
            "after", "before", "above", "below", "under", "over",
            "specific", "general", "particular", "certain", "various",
            "main", "primary", "major", "key", "basic", "simple", "complex",
            "structure", "form", "level", "step", "stage", "phase",
            "memory", "network", "database", "server", "client", "user",
            "input", "output", "file", "table", "list", "array", "queue",
            "stack", "tree", "graph", "node", "edge", "path", "algorithm",
            "sort", "search", "binary", "linear", "recursive", "loop",
            "variable", "constant", "parameter", "argument", "return",
            "language", "model", "test", "case", "error", "exception",
            "handle", "manage", "control", "operate", "perform", "execute",
            "create", "delete", "update", "read", "write", "access",
            "public", "private", "protected", "static", "final", "abstract",
            "interface", "implement", "extend", "inherit", "override",
            "application", "service", "component", "module", "package",
            "library", "framework", "platform", "environment", "tool",
        })
        cls._COMMON_WORDS = common
        return common

    @staticmethod
    def detect(student_text: str, student_sentences: List[str]) -> DetectionResult:
        if len(student_text.strip()) < 15:
            return DetectionResult("gibberish", False, 0.0, "none")

        evidence = []
        details: Dict = {}
        penalty = 0.0

        text = student_text.strip()
        words = text.lower().split()
        n_words = len(words)

        # ── Signal 1: Character entropy ─────────────────────────────
        char_freq = Counter(text.lower())
        total_chars = sum(char_freq.values())
        entropy = 0.0
        if total_chars > 0:
            for count in char_freq.values():
                p = count / total_chars
                if p > 0:
                    entropy -= p * math.log2(p)
        details["char_entropy"] = round(entropy, 3)

        if entropy > GibberishDetector.HIGH_ENTROPY_THRESHOLD:
            ent_penalty = min((entropy - GibberishDetector.HIGH_ENTROPY_THRESHOLD) * 0.15, 0.10)
            penalty += ent_penalty
            evidence.append(f"High character entropy ({entropy:.2f}) — possible random text")

        # ── Signal 2: Real-word ratio ───────────────────────────────
        common_words = GibberishDetector._get_common_words()
        alpha_words = [w for w in words if w.isalpha()]
        if alpha_words:
            real_count = sum(1 for w in alpha_words if w in common_words)
            real_ratio = real_count / len(alpha_words)
            details["real_word_ratio"] = round(real_ratio, 3)

            if real_ratio < GibberishDetector.LOW_REAL_WORD_RATIO and len(alpha_words) >= 8:
                ratio_penalty = min((GibberishDetector.LOW_REAL_WORD_RATIO - real_ratio) * 0.5, 0.12)
                penalty += ratio_penalty
                evidence.append(
                    f"Low real-word ratio ({real_ratio:.2f}) — "
                    f"only {real_count}/{len(alpha_words)} recognizable words"
                )

        # ── Signal 3: Vowel-consonant anomaly ───────────────────────
        alpha_text = re.sub(r'[^a-zA-Z]', '', text.lower())
        if len(alpha_text) >= 20:
            vowels = sum(1 for c in alpha_text if c in 'aeiou')
            consonants = len(alpha_text) - vowels
            vc_ratio = vowels / max(consonants, 1)
            details["vowel_consonant_ratio"] = round(vc_ratio, 3)

            # Normal English: ~0.55-0.65. Very low or very high = suspicious
            if vc_ratio < 0.20 or vc_ratio > 1.5:
                penalty += 0.08
                evidence.append(
                    f"Abnormal vowel-consonant ratio ({vc_ratio:.2f}) — "
                    f"normal English is ~0.55-0.65"
                )

        # ── Signal 4: Special character ratio ───────────────────────
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        special_ratio = special_chars / max(len(text), 1)
        details["special_char_ratio"] = round(special_ratio, 3)

        if special_ratio > 0.15:
            penalty += min(special_ratio * 0.3, 0.08)
            evidence.append(f"High special character ratio ({special_ratio:.2%})")

        # ── Signal 5: Vocabulary diversity on short text ────────────
        if 5 <= n_words <= 50:
            ttr = len(set(words)) / max(n_words, 1)
            details["type_token_ratio"] = round(ttr, 3)
            if ttr < 0.30:
                penalty += 0.06
                evidence.append(f"Very low vocabulary diversity (TTR={ttr:.2f})")

        penalty = min(penalty, GibberishDetector.MAX_PENALTY)

        if penalty <= 0:
            return DetectionResult("gibberish", False, 0.0, "none", [], details)

        severity = _classify_severity(penalty, 0.05, 0.15)
        return DetectionResult("gibberish", True, round(penalty, 4), severity, evidence, details)


# ═══════════════════════════════════════════════════════════════════════
#  Layer 5: Padding Detector
# ═══════════════════════════════════════════════════════════════════════

class PaddingDetector:
    """
    Detect filler phrases, hedging, and circular restatement.

    Signals:
    - High density of filler phrases ("it is important to note that", etc.)
    - Excessive hedging ("may", "might", "perhaps", "possibly")
    - Circular restatement (first and last sentences nearly identical)
    - Excessive qualifiers without substantive content
    """

    MAX_PENALTY = 0.15

    _FILLER_PHRASES = re.compile(
        r"\b("
        r"it is important to note that|"
        r"it should be noted that|"
        r"it is worth mentioning that|"
        r"as we all know|"
        r"as everyone knows|"
        r"needless to say|"
        r"it goes without saying|"
        r"in today's world|"
        r"in the modern world|"
        r"in today's society|"
        r"since the beginning of time|"
        r"from time immemorial|"
        r"in this day and age|"
        r"at the end of the day|"
        r"when all is said and done|"
        r"last but not least|"
        r"each and every|"
        r"first and foremost|"
        r"the fact that|"
        r"due to the fact that|"
        r"in spite of the fact that|"
        r"as a matter of fact|"
        r"for all intents and purposes|"
        r"it can be said that|"
        r"it is well known that|"
        r"basically|essentially|actually|literally|"
        r"very very|really really"
        r")\b",
        re.IGNORECASE,
    )

    _HEDGE_WORDS = re.compile(
        r"\b(perhaps|maybe|possibly|arguably|somewhat|"
        r"sort of|kind of|more or less|to some extent|"
        r"in a way|in some sense|it seems|it appears)\b",
        re.IGNORECASE,
    )

    @staticmethod
    def detect(
        student_text: str,
        student_sentences: List[str],
    ) -> DetectionResult:
        if len(student_sentences) < 2:
            return DetectionResult("padding", False, 0.0, "none")

        evidence = []
        details: Dict = {}
        penalty = 0.0

        n_sents = len(student_sentences)
        n_words = len(student_text.split())

        # ── Signal 1: Filler phrase density ─────────────────────────
        fillers = PaddingDetector._FILLER_PHRASES.findall(student_text)
        filler_density = len(fillers) / max(n_sents, 1)
        details["filler_count"] = len(fillers)
        details["filler_density"] = round(filler_density, 3)

        if len(fillers) >= 3:
            penalty += min(len(fillers) * 0.02, 0.08)
            evidence.append(
                f"{len(fillers)} filler phrases detected: "
                f"{', '.join(list(set(fillers))[:3])}"
            )
        elif len(fillers) >= 2:
            penalty += 0.03
            evidence.append(f"{len(fillers)} filler phrases")

        # ── Signal 2: Excessive hedging ─────────────────────────────
        hedges = PaddingDetector._HEDGE_WORDS.findall(student_text)
        hedge_density = len(hedges) / max(n_sents, 1)
        details["hedge_count"] = len(hedges)
        details["hedge_density"] = round(hedge_density, 3)

        if hedge_density > 0.8:
            penalty += 0.05
            evidence.append(f"Excessive hedging ({len(hedges)} hedge words in {n_sents} sentences)")

        # ── Signal 3: Circular restatement ──────────────────────────
        first_words = set(student_sentences[0].lower().split()) - _STOPWORDS
        last_words = set(student_sentences[-1].lower().split()) - _STOPWORDS

        if first_words and last_words and len(student_sentences) >= 4:
            overlap = len(first_words & last_words) / max(min(len(first_words), len(last_words)), 1)
            details["first_last_overlap"] = round(overlap, 3)

            if overlap > 0.7:
                penalty += 0.05
                evidence.append(
                    f"Circular restatement: first and last sentences {overlap:.0%} similar"
                )

        # ── Signal 4: Low information density ───────────────────────
        # Content words per sentence
        content_words_per_sent = []
        for sent in student_sentences:
            cw = [w for w in sent.lower().split() if w not in _STOPWORDS and w.isalpha()]
            content_words_per_sent.append(len(cw))

        avg_content = sum(content_words_per_sent) / max(n_sents, 1)
        details["avg_content_words_per_sentence"] = round(avg_content, 1)

        if avg_content < 2.0 and n_sents >= 3:
            penalty += 0.04
            evidence.append(
                f"Low information density (avg {avg_content:.1f} content words/sentence)"
            )

        penalty = min(penalty, PaddingDetector.MAX_PENALTY)

        if penalty <= 0:
            return DetectionResult("padding", False, 0.0, "none", [], details)

        severity = _classify_severity(penalty, 0.04, 0.08)
        return DetectionResult("padding", True, round(penalty, 4), severity, evidence, details)


# ═══════════════════════════════════════════════════════════════════════
#  Layer 6: Copy-Shuffle Detector
# ═══════════════════════════════════════════════════════════════════════

class CopyShuffleDetector:
    """
    Detect rearranged model sentences with minor word swaps.

    Distinct from the concept_graph's copy detection (n-gram based):
    this uses sentence-level embedding similarity to catch paraphrase-level
    copying where students rearrange the model answer's sentences and
    make minor edits.

    Signals:
    - Many student sentences match model sentences at sim > 0.85
    - Matched sentences cover most of the student answer
    - Student unique content is very low
    """

    HIGH_MATCH_THRESHOLD = 0.92  # sentence-level copy sim (high to avoid false positives on good paraphrases)
    MAX_PENALTY = 0.15

    @staticmethod
    def detect(
        student_sentences: List[str],
        model_sentences: List[str],
        student_embeddings: Optional[np.ndarray] = None,
        model_embeddings: Optional[np.ndarray] = None,
    ) -> DetectionResult:
        if not student_sentences or not model_sentences:
            return DetectionResult("copy_shuffle", False, 0.0, "none")

        evidence = []
        details: Dict = {}
        high_match_indices: List[int] = []

        n_stu = len(student_sentences)

        if (student_embeddings is not None and model_embeddings is not None
                and len(student_embeddings) > 0 and len(model_embeddings) > 0):
            # Cross-similarity
            s_norm = student_embeddings / np.maximum(
                np.linalg.norm(student_embeddings, axis=1, keepdims=True), 1e-10)
            m_norm = model_embeddings / np.maximum(
                np.linalg.norm(model_embeddings, axis=1, keepdims=True), 1e-10)
            cross_sim = s_norm @ m_norm.T

            max_sims = cross_sim.max(axis=1)
            best_matches = cross_sim.argmax(axis=1)

            for i in range(n_stu):
                if max_sims[i] >= CopyShuffleDetector.HIGH_MATCH_THRESHOLD:
                    high_match_indices.append(i)
        else:
            # Word overlap fallback
            model_word_sets = [set(s.lower().split()) - _STOPWORDS for s in model_sentences]
            for i, sent in enumerate(student_sentences):
                stu_words = set(sent.lower().split()) - _STOPWORDS
                if stu_words:
                    best = max(
                        (len(stu_words & mw) / max(len(stu_words), 1) for mw in model_word_sets if mw),
                        default=0.0,
                    )
                    if best >= 0.75:
                        high_match_indices.append(i)

        copy_ratio = len(high_match_indices) / max(n_stu, 1)
        details["high_match_count"] = len(high_match_indices)
        details["copy_ratio"] = round(copy_ratio, 3)
        details["total_student_sentences"] = n_stu

        if copy_ratio < 0.5:
            return DetectionResult("copy_shuffle", False, 0.0, "none", [], details)

        # Penalty scales with copy ratio
        penalty = min((copy_ratio - 0.5) * 0.4, CopyShuffleDetector.MAX_PENALTY)

        evidence.append(
            f"{len(high_match_indices)}/{n_stu} student sentences closely match model "
            f"(copy ratio {copy_ratio:.0%})"
        )

        # Check if student added any original content
        original_count = n_stu - len(high_match_indices)
        details["original_sentence_count"] = original_count
        if original_count <= 1:
            penalty += 0.05
            evidence.append("Almost no original content beyond copied sentences")

        penalty = min(penalty, CopyShuffleDetector.MAX_PENALTY)

        severity = _classify_severity(penalty, 0.04, 0.08)
        return DetectionResult("copy_shuffle", True, round(penalty, 4), severity, evidence, details)


# ═══════════════════════════════════════════════════════════════════════
#  Master Orchestrator
# ═══════════════════════════════════════════════════════════════════════

class AntiGamingAnalyzer:
    """
    Master orchestrator for Upgrade 9 — Anti-Gaming Protection.

    Call ``analyze(...)`` to get an ``AntiGamingReport``.

    The total penalty is **subtracted** from the final score:
        final = weighted_score + structure_bonus − gaming_penalty

    Max total penalty is capped at ``MAX_TOTAL_PENALTY``.
    """

    MAX_TOTAL_PENALTY = 0.40  # absolute maximum deduction

    def __init__(self):
        self._nlp = None
        self._embedder = None
        try:
            import spacy
            self._nlp = spacy.load("en_core_web_sm")
        except Exception:
            logger.debug("spaCy not available; using regex sentence splitting")
        try:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            logger.warning("SentenceTransformer not available; using word-overlap fallback")

    # ─── Public API ──────────────────────────────────────────────────

    def analyze(
        self,
        student_text: str,
        model_text: str,
        keyword_score: float = 0.0,
        semantic_score: float = 0.0,
        matched_keywords: Optional[List[str]] = None,
    ) -> AntiGamingReport:
        """Run all 6 detectors and produce an aggregated report."""
        if not student_text or len(student_text.strip()) < 10:
            return AntiGamingReport()
        if not model_text or len(model_text.strip()) < 10:
            return AntiGamingReport()

        matched_keywords = matched_keywords or []

        # ── Preprocessing ────────────────────────────────────────────
        student_sents = self._split_sentences(student_text)
        model_sents = self._split_sentences(model_text)

        # Compute embeddings (batched for efficiency)
        stu_emb = None
        mod_emb = None
        if self._embedder is not None:
            all_sents = student_sents + model_sents
            if all_sents:
                all_emb = self._embedder.encode(all_sents, show_progress_bar=False)
                stu_emb = all_emb[:len(student_sents)]
                mod_emb = all_emb[len(student_sents):]

        # ── Run detectors ────────────────────────────────────────────
        rep_r = RepetitionDetector.detect(student_sents, stu_emb)
        irr_r = IrrelevanceDetector.detect(student_sents, model_sents, stu_emb, mod_emb)
        kws_r = KeywordStuffingDetector.detect(
            student_text, model_text, keyword_score, semantic_score,
            matched_keywords, student_sents, stu_emb,
        )
        gib_r = GibberishDetector.detect(student_text, student_sents)
        pad_r = PaddingDetector.detect(student_text, student_sents)
        cps_r = CopyShuffleDetector.detect(student_sents, model_sents, stu_emb, mod_emb)

        # ── Aggregate ────────────────────────────────────────────────
        raw_penalty = (
            rep_r.penalty + irr_r.penalty + kws_r.penalty +
            gib_r.penalty + pad_r.penalty + cps_r.penalty
        )
        total_penalty = min(raw_penalty, self.MAX_TOTAL_PENALTY)

        # Build flags and warnings
        flags = []
        warnings = []
        for det in [rep_r, irr_r, kws_r, gib_r, pad_r, cps_r]:
            if det.severity == "high":
                flags.append(f"[HIGH] {det.name}: {det.evidence[0] if det.evidence else 'detected'}")
            elif det.severity == "medium":
                warnings.append(f"[MEDIUM] {det.name}: {det.evidence[0] if det.evidence else 'detected'}")

        is_flagged = any(
            d.severity == "high" for d in [rep_r, irr_r, kws_r, gib_r, pad_r, cps_r]
        )

        # Confidence: weighted average of normalized penalties
        max_possible = (
            RepetitionDetector.MAX_PENALTY + IrrelevanceDetector.MAX_PENALTY +
            KeywordStuffingDetector.MAX_PENALTY + GibberishDetector.MAX_PENALTY +
            PaddingDetector.MAX_PENALTY + CopyShuffleDetector.MAX_PENALTY
        )
        confidence = raw_penalty / max(max_possible, 0.01)

        return AntiGamingReport(
            repetition=rep_r,
            irrelevance=irr_r,
            keyword_stuffing=kws_r,
            gibberish=gib_r,
            padding=pad_r,
            copy_shuffle=cps_r,
            total_penalty=round(total_penalty, 4),
            flags=flags,
            warnings=warnings,
            is_flagged=is_flagged,
            confidence=round(confidence, 4),
        )

    def get_detailed_report(self, report: AntiGamingReport) -> Dict:
        """Human-readable summary dict for API responses."""
        return {
            "total_penalty": report.total_penalty,
            "is_flagged": report.is_flagged,
            "confidence": report.confidence,
            "flags": report.flags,
            "warnings": report.warnings,
            "detectors": {
                "repetition": {
                    "detected": report.repetition.detected,
                    "penalty": report.repetition.penalty,
                    "severity": report.repetition.severity,
                    "evidence": report.repetition.evidence,
                    "details": report.repetition.details,
                },
                "irrelevance": {
                    "detected": report.irrelevance.detected,
                    "penalty": report.irrelevance.penalty,
                    "severity": report.irrelevance.severity,
                    "evidence": report.irrelevance.evidence,
                    "details": report.irrelevance.details,
                },
                "keyword_stuffing": {
                    "detected": report.keyword_stuffing.detected,
                    "penalty": report.keyword_stuffing.penalty,
                    "severity": report.keyword_stuffing.severity,
                    "evidence": report.keyword_stuffing.evidence,
                    "details": report.keyword_stuffing.details,
                },
                "gibberish": {
                    "detected": report.gibberish.detected,
                    "penalty": report.gibberish.penalty,
                    "severity": report.gibberish.severity,
                    "evidence": report.gibberish.evidence,
                    "details": report.gibberish.details,
                },
                "padding": {
                    "detected": report.padding.detected,
                    "penalty": report.padding.penalty,
                    "severity": report.padding.severity,
                    "evidence": report.padding.evidence,
                    "details": report.padding.details,
                },
                "copy_shuffle": {
                    "detected": report.copy_shuffle.detected,
                    "penalty": report.copy_shuffle.penalty,
                    "severity": report.copy_shuffle.severity,
                    "evidence": report.copy_shuffle.evidence,
                    "details": report.copy_shuffle.details,
                },
            },
        }

    # ─── Private Helpers ─────────────────────────────────────────────

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences using spaCy or regex fallback."""
        if self._nlp is not None:
            doc = self._nlp(text[:100000])
            return [s.text.strip() for s in doc.sents if s.text.strip()]
        return _split_sentences_simple(text)
