"""
Sentence Alignment Matrix Weighting Service  (Upgrade 5)
=========================================================
Advanced sentence-level evaluation with importance weighting,
optimal alignment, and structured scoring.

Problem with plain sentence similarity
----------------------------------------
The existing ``SemanticAnalyzer.calculate_sentence_similarities()``
computes greedy best-match for each model sentence, but:
*   Every model sentence has *equal* weight — a throwaway example
    counts as much as a core definition.
*   Greedy matching is suboptimal — one student sentence can "steal"
    the best match from multiple model sentences.
*   No penalty for skipping *important* model sentences.
*   No reward for structural order alignment.

Solution: Importance-Weighted Sentence Alignment Matrix
---------------------------------------------------------

1. **Sentence Segmentation & Classification** (Layer 1)
   Split both texts into sentences.  Classify each model sentence
   by its rhetorical role:
     • Definition  → weight 1.5
     • Key fact    → weight 1.5
     • Explanation → weight 1.3
     • Example     → weight 0.5
     • Transition  → weight 0.3

2. **Importance Scoring** (Layer 2)
   Per-sentence importance derived from:
     • TF-IDF salience of its words
     • Position signal (first / last sentences matter more)
     • Entity / technical-term density
     • Custom keyword boost
   Scores are normalised to [0.3, 2.0].

3. **Alignment Matrix** (Layer 3)
   Full N × M cosine-similarity matrix via SBERT batch encoding.
   Optimal 1-to-1 alignment via the **Hungarian algorithm** (scipy).
   Also supports 1-to-many soft matching above a threshold.

4. **Match Quality Analysis** (Layer 4)
   Each model sentence is classified:
     STRONG  (≥ 0.70)  — fully covered
     PARTIAL (≥ 0.45)  — idea present but incomplete
     WEAK    (≥ 0.30)  — tangentially related
     MISSING (< 0.30)  — not addressed at all

5. **Gap & Penalty Analysis** (Layer 5)
   • Missing important sentence penalty  (weighted by importance)
   • Filler / orphan student sentence detection
   • Order-deviation penalty  (Kendall tau on aligned pairs)
   • Redundancy detection  (diminishing returns for repeats)

6. **Structured Score** (Layer 6)
   alignment_score = Σ (importance_i × match_quality_i) / Σ importance_i
   coverage_score  = Σ 1[matched_i] importance_i / Σ importance_i
   order_score     = normalised Kendall tau of alignment
   gap_penalty     = Σ importance_i for each MISSING sentence × penalty_rate
   Final = 0.55 × alignment + 0.25 × coverage + 0.10 × order
           + 0.10 × depth_bonus − gap_penalty

Dependencies (all already installed):
   • sentence-transformers  — SBERT batch encoding
   • numpy                  — matrix ops
   • scipy                  — Hungarian algorithm (linear_sum_assignment)
   • spaCy (en_core_web_sm) — sentence tokenization, NER
   • scikit-learn           — TF-IDF
"""

from __future__ import annotations

import logging
import math
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger("AssessIQ.SentenceAlignment")


# ═══════════════════════════════════════════════════════════════════════
#  Data Structures
# ═══════════════════════════════════════════════════════════════════════

class SentenceRole:
    """Rhetorical role of a sentence with its default importance weight."""
    DEFINITION  = "definition"    # weight 1.5
    KEY_FACT    = "key_fact"      # weight 1.5
    EXPLANATION = "explanation"   # weight 1.3
    EXAMPLE     = "example"       # weight 0.5
    TRANSITION  = "transition"    # weight 0.3
    GENERAL     = "general"       # weight 1.0

    ROLE_WEIGHTS = {
        "definition":  1.5,
        "key_fact":    1.5,
        "explanation": 1.3,
        "example":     0.5,
        "transition":  0.3,
        "general":     1.0,
    }


class MatchQuality:
    """Match quality tiers between a model sentence and its best student match."""
    STRONG  = "strong"    # >= 0.70
    PARTIAL = "partial"   # >= 0.45
    WEAK    = "weak"      # >= 0.30
    MISSING = "missing"   # <  0.30

    THRESHOLDS = {
        "strong":  0.70,
        "partial": 0.45,
        "weak":    0.30,
    }


@dataclass
class SentenceInfo:
    """Rich metadata for a single sentence."""
    index: int
    text: str
    role: str = SentenceRole.GENERAL
    importance: float = 1.0           # final normalised importance
    role_weight: float = 1.0          # from rhetorical classification
    tfidf_score: float = 0.0          # salience of its terms
    position_weight: float = 1.0      # first/last boost
    entity_density: float = 0.0       # NER / technical term density
    keyword_boost: float = 0.0        # overlap with explicit keywords
    word_count: int = 0
    embedding: Optional[np.ndarray] = None


@dataclass
class AlignmentPair:
    """One matched pair from the alignment matrix."""
    model_index: int
    student_index: int
    model_text: str
    student_text: str
    similarity: float
    match_quality: str          # strong / partial / weak / missing
    model_importance: float
    weighted_contribution: float  # importance * similarity


@dataclass
class AlignmentResult:
    """Complete output from the sentence alignment pipeline."""
    # Scores  (all in [0, 1])
    alignment_score: float      # importance-weighted match quality
    coverage_score: float       # fraction of important content covered
    order_score: float          # structural order coherence
    depth_bonus: float          # bonus for high-quality strong matches
    gap_penalty: float          # penalty for missing important sentences
    combined_score: float       # final aggregated score

    # Statistics
    model_sentence_count: int
    student_sentence_count: int
    strong_matches: int
    partial_matches: int
    weak_matches: int
    missing_matches: int
    orphan_student_count: int   # student sentences that match nothing

    # Details
    alignment_pairs: List[AlignmentPair] = field(default_factory=list)
    missing_sentences: List[str] = field(default_factory=list)
    orphan_sentences: List[str] = field(default_factory=list)
    similarity_matrix: Optional[np.ndarray] = None

    # Timing
    processing_time: float = 0.0


# ═══════════════════════════════════════════════════════════════════════
#  Layer 1 — Sentence Segmentation & Classification
# ═══════════════════════════════════════════════════════════════════════

class SentenceSegmenter:
    """Split text into sentences and classify rhetorical roles."""

    # Regex cues for rhetorical classification
    _DEFINITION_CUES = re.compile(
        r"\b(is defined as|refers to|is the process|means that|"
        r"can be defined|is known as|is called|denotes|"
        r"is a |are the |consists of|comprises)\b",
        re.IGNORECASE,
    )
    _EXAMPLE_CUES = re.compile(
        r"\b(for example|for instance|such as|e\.g\.|"
        r"consider the|like |an example|illustrat)\b",
        re.IGNORECASE,
    )
    _TRANSITION_CUES = re.compile(
        r"^(however|moreover|furthermore|in addition|"
        r"on the other hand|therefore|thus|hence|"
        r"in conclusion|to summarize|overall|additionally|"
        r"consequently|as a result|in summary)\b",
        re.IGNORECASE,
    )
    _KEY_FACT_CUES = re.compile(
        r"\b(must|always|never|important|critical|essential|"
        r"key |primary|fundamental|significant|crucial|"
        r"main |major |necessary|required)\b",
        re.IGNORECASE,
    )

    def __init__(self):
        """Load spaCy for sentence tokenization and NER."""
        self._nlp = None
        try:
            import spacy
            self._nlp = spacy.load("en_core_web_sm")
            logger.debug("spaCy loaded for sentence segmentation")
        except Exception:
            logger.warning("spaCy not available; falling back to regex splitter")

    def segment(self, text: str) -> List[SentenceInfo]:
        """Split *text* into ``SentenceInfo`` objects with roles."""
        raw_sents = self._split_sentences(text)
        sentences: List[SentenceInfo] = []
        for idx, sent_text in enumerate(raw_sents):
            sent_text = sent_text.strip()
            if len(sent_text) < 3:
                continue
            role = self._classify_role(sent_text)
            sentences.append(SentenceInfo(
                index=idx,
                text=sent_text,
                role=role,
                role_weight=SentenceRole.ROLE_WEIGHTS.get(role, 1.0),
                word_count=len(sent_text.split()),
            ))
        return sentences

    # ── private helpers ──────────────────────────────────────────────

    def _split_sentences(self, text: str) -> List[str]:
        """Use spaCy when available, else simplistic regex."""
        if self._nlp is not None:
            doc = self._nlp(text[:100000])      # Limit for safety
            return [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        # Fallback
        parts = re.split(r'(?<=[.!?])\s+', text)
        return [p.strip() for p in parts if p.strip()]

    def _classify_role(self, sentence: str) -> str:
        """Classify sentence role via keyword cues."""
        if self._DEFINITION_CUES.search(sentence):
            return SentenceRole.DEFINITION
        if self._EXAMPLE_CUES.search(sentence):
            return SentenceRole.EXAMPLE
        if self._TRANSITION_CUES.match(sentence):
            return SentenceRole.TRANSITION
        if self._KEY_FACT_CUES.search(sentence):
            return SentenceRole.KEY_FACT
        # Default: if sentence is short and looks like a clause, it may be
        # an explanation; otherwise general.
        word_count = len(sentence.split())
        if word_count >= 8:
            return SentenceRole.EXPLANATION
        return SentenceRole.GENERAL


# ═══════════════════════════════════════════════════════════════════════
#  Layer 2 — Importance Scoring
# ═══════════════════════════════════════════════════════════════════════

class ImportanceScorer:
    """Compute per-sentence importance from multiple signals."""

    # Signal weights in the importance formula
    W_ROLE     = 0.35
    W_TFIDF    = 0.25
    W_POSITION = 0.15
    W_ENTITY   = 0.15
    W_KEYWORD  = 0.10

    MIN_IMPORTANCE = 0.3
    MAX_IMPORTANCE = 2.0

    def score(
        self,
        sentences: List[SentenceInfo],
        full_text: str,
        custom_keywords: Optional[List[str]] = None,
    ) -> List[SentenceInfo]:
        """Enrich each ``SentenceInfo`` with its importance score."""
        if not sentences:
            return sentences

        # ── TF-IDF salience ─────────────────────────────────────────
        tfidf_scores = self._tfidf_salience(sentences, full_text)
        for sent, sc in zip(sentences, tfidf_scores):
            sent.tfidf_score = sc

        # ── Position weighting ──────────────────────────────────────
        n = len(sentences)
        for sent in sentences:
            if sent.index == 0:
                sent.position_weight = 1.4       # opening sentence
            elif sent.index == n - 1:
                sent.position_weight = 1.2       # closing sentence
            elif sent.index <= 2:
                sent.position_weight = 1.1       # near-opening
            else:
                sent.position_weight = 1.0

        # ── Entity density ──────────────────────────────────────────
        self._entity_density(sentences)

        # ── Keyword boost ───────────────────────────────────────────
        if custom_keywords:
            kw_set = {k.lower() for k in custom_keywords}
            for sent in sentences:
                tokens = set(sent.text.lower().split())
                overlap = len(tokens & kw_set)
                sent.keyword_boost = min(overlap * 0.2, 1.0)

        # ── Final importance aggregation ────────────────────────────
        for sent in sentences:
            raw = (
                self.W_ROLE     * sent.role_weight +
                self.W_TFIDF    * sent.tfidf_score +
                self.W_POSITION * sent.position_weight +
                self.W_ENTITY   * sent.entity_density +
                self.W_KEYWORD  * sent.keyword_boost
            )
            sent.importance = max(
                self.MIN_IMPORTANCE,
                min(self.MAX_IMPORTANCE, raw),
            )

        return sentences

    # ── private helpers ──────────────────────────────────────────────

    def _tfidf_salience(
        self,
        sentences: List[SentenceInfo],
        full_text: str,
    ) -> List[float]:
        """Average TF-IDF value of each sentence's tokens."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            texts = [s.text for s in sentences]
            if len(texts) < 2:
                return [1.0] * len(texts)
            vec = TfidfVectorizer(
                stop_words="english",
                max_features=3000,
                ngram_range=(1, 2),
            )
            mat = vec.fit_transform(texts)
            # Mean TF-IDF per sentence (higher = more distinctive terms)
            scores = np.asarray(mat.mean(axis=1)).flatten()
            # Normalise to [0, 2]
            mx = scores.max() if scores.max() > 0 else 1.0
            scores = (scores / mx) * 2.0
            return scores.tolist()
        except Exception:
            return [1.0] * len(sentences)

    def _entity_density(self, sentences: List[SentenceInfo]) -> None:
        """Count named-entity / technical-term density per sentence."""
        try:
            import spacy
            nlp = spacy.load("en_core_web_sm")
        except Exception:
            for s in sentences:
                s.entity_density = 0.5
            return

        for sent in sentences:
            doc = nlp(sent.text[:5000])
            ent_count = len(doc.ents)
            # Also count capitalised / technical-looking tokens
            tech_count = sum(
                1 for tok in doc
                if tok.pos_ in ("NOUN", "PROPN") and not tok.is_stop
            )
            density = (ent_count + tech_count * 0.5) / max(sent.word_count, 1)
            sent.entity_density = min(density * 2.0, 2.0)


# ═══════════════════════════════════════════════════════════════════════
#  Layer 3 — Alignment Matrix Construction
# ═══════════════════════════════════════════════════════════════════════

class AlignmentMatrixBuilder:
    """Build the N x M SBERT similarity matrix and compute optimal alignment."""

    def __init__(self):
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")

    def build_matrix(
        self,
        model_sents: List[SentenceInfo],
        student_sents: List[SentenceInfo],
    ) -> np.ndarray:
        """Return an N x M cosine-similarity matrix.

        N = len(model_sents), M = len(student_sents).
        Each cell (i, j) = cosine_sim(model_i, student_j).
        Also populates the ``embedding`` field of each SentenceInfo.
        """
        self._ensure_model()

        model_texts = [s.text for s in model_sents]
        student_texts = [s.text for s in student_sents]

        # Batch encode
        model_embs = self._model.encode(model_texts, convert_to_numpy=True,
                                        show_progress_bar=False)
        student_embs = self._model.encode(student_texts, convert_to_numpy=True,
                                          show_progress_bar=False)

        # Store embeddings
        for s, emb in zip(model_sents, model_embs):
            s.embedding = emb
        for s, emb in zip(student_sents, student_embs):
            s.embedding = emb

        # Normalise for cosine similarity via dot product
        model_norms = np.linalg.norm(model_embs, axis=1, keepdims=True)
        student_norms = np.linalg.norm(student_embs, axis=1, keepdims=True)
        model_norms[model_norms == 0] = 1.0
        student_norms[student_norms == 0] = 1.0

        model_normed = model_embs / model_norms
        student_normed = student_embs / student_norms

        # Full similarity matrix
        sim_matrix = model_normed @ student_normed.T     # shape (N, M)
        # Clamp to [0, 1] — negative cosine is irrelevant in this context
        sim_matrix = np.clip(sim_matrix, 0.0, 1.0)

        return sim_matrix

    def optimal_alignment(
        self,
        sim_matrix: np.ndarray,
    ) -> List[Tuple[int, int, float]]:
        """Compute optimal 1-to-1 alignment via the Hungarian algorithm.

        Returns a list of (model_idx, student_idx, similarity) tuples.
        If N > M some model sentences will be unmatched; we still include
        them with student_idx = -1 and similarity = 0.
        """
        try:
            from scipy.optimize import linear_sum_assignment
        except ImportError:
            logger.warning("scipy not available; falling back to greedy alignment")
            return self._greedy_alignment(sim_matrix)

        n_model, n_student = sim_matrix.shape

        # Hungarian expects a cost matrix → use negative similarity
        cost = -sim_matrix.copy()

        # Pad if model sentences > student sentences
        if n_model > n_student:
            pad = np.zeros((n_model, n_model - n_student))
            cost = np.hstack([cost, pad])

        row_idx, col_idx = linear_sum_assignment(cost)

        pairs: List[Tuple[int, int, float]] = []
        matched_model = set()

        for r, c in zip(row_idx, col_idx):
            if r >= n_model:
                continue
            if c >= n_student:
                # This model sentence is unmatched
                pairs.append((r, -1, 0.0))
            else:
                pairs.append((r, c, float(sim_matrix[r, c])))
            matched_model.add(r)

        # Any model sentence not in the assignment (shouldn't happen, but safety)
        for mi in range(n_model):
            if mi not in matched_model:
                pairs.append((mi, -1, 0.0))

        pairs.sort(key=lambda x: x[0])
        return pairs

    def soft_alignment(
        self,
        sim_matrix: np.ndarray,
        threshold: float = 0.40,
    ) -> Dict[int, List[Tuple[int, float]]]:
        """1-to-many soft alignment: for each model sentence, find *all*
        student sentences above *threshold*.

        Returns {model_idx: [(student_idx, similarity), ...]}.
        """
        n_model, n_student = sim_matrix.shape
        result: Dict[int, List[Tuple[int, float]]] = {}
        for i in range(n_model):
            matches = []
            for j in range(n_student):
                if sim_matrix[i, j] >= threshold:
                    matches.append((j, float(sim_matrix[i, j])))
            matches.sort(key=lambda x: x[1], reverse=True)
            result[i] = matches
        return result

    # ── fallback ─────────────────────────────────────────────────────

    def _greedy_alignment(
        self, sim_matrix: np.ndarray,
    ) -> List[Tuple[int, int, float]]:
        """Greedy best-match alignment (fallback if scipy unavailable)."""
        n_model, n_student = sim_matrix.shape
        used_student: Set[int] = set()
        pairs: List[Tuple[int, int, float]] = []

        for i in range(n_model):
            best_j = -1
            best_sim = 0.0
            for j in range(n_student):
                if j not in used_student and sim_matrix[i, j] > best_sim:
                    best_sim = sim_matrix[i, j]
                    best_j = j
            if best_j >= 0 and best_sim >= 0.20:
                pairs.append((i, best_j, best_sim))
                used_student.add(best_j)
            else:
                pairs.append((i, -1, 0.0))

        pairs.sort(key=lambda x: x[0])
        return pairs


# ═══════════════════════════════════════════════════════════════════════
#  Layer 4 — Match Quality Analysis
# ═══════════════════════════════════════════════════════════════════════

class MatchAnalyzer:
    """Categorise each alignment pair and detect merging / splitting."""

    @staticmethod
    def classify(similarity: float) -> str:
        """Return match quality tier for a similarity value."""
        if similarity >= MatchQuality.THRESHOLDS["strong"]:
            return MatchQuality.STRONG
        if similarity >= MatchQuality.THRESHOLDS["partial"]:
            return MatchQuality.PARTIAL
        if similarity >= MatchQuality.THRESHOLDS["weak"]:
            return MatchQuality.WEAK
        return MatchQuality.MISSING

    @staticmethod
    def build_pairs(
        model_sents: List[SentenceInfo],
        student_sents: List[SentenceInfo],
        optimal_pairs: List[Tuple[int, int, float]],
        soft_map: Dict[int, List[Tuple[int, float]]],
    ) -> List[AlignmentPair]:
        """Build rich ``AlignmentPair`` list using both optimal and soft alignment.

        For each model sentence:
        1. Use optimal 1:1 pair as the primary alignment.
        2. If optimal similarity is WEAK/MISSING but the soft map has a
           decent match, upgrade using the best soft candidate (this handles
           1-to-many coverage where the student addresses the same idea
           across multiple sentences).
        """
        pairs: List[AlignmentPair] = []

        for mi, si, sim in optimal_pairs:
            # Try to upgrade via soft map
            effective_sim = sim
            effective_si = si
            effective_text = ""

            if si >= 0 and si < len(student_sents):
                effective_text = student_sents[si].text
            else:
                effective_text = ""

            # Check soft map for a better aggregate
            soft_matches = soft_map.get(mi, [])
            if soft_matches:
                best_soft_sim = soft_matches[0][1] if soft_matches else 0.0
                if best_soft_sim > effective_sim:
                    effective_sim = best_soft_sim
                    effective_si = soft_matches[0][0]
                    effective_text = student_sents[effective_si].text

                # Aggregate: if multiple soft matches, compute a combined
                # "multi-sentence coverage" boost (student split the idea).
                if len(soft_matches) >= 2:
                    # Average the top-2 soft similarities as bonus
                    top2_avg = np.mean([s for _, s in soft_matches[:2]])
                    if top2_avg > effective_sim:
                        effective_sim = min(1.0, top2_avg * 1.05)
                        combined_texts = " | ".join(
                            student_sents[sj].text for sj, _ in soft_matches[:2]
                        )
                        effective_text = combined_texts

            quality = MatchAnalyzer.classify(effective_sim)
            model_imp = model_sents[mi].importance

            pairs.append(AlignmentPair(
                model_index=mi,
                student_index=effective_si,
                model_text=model_sents[mi].text,
                student_text=effective_text,
                similarity=round(effective_sim, 4),
                match_quality=quality,
                model_importance=round(model_imp, 4),
                weighted_contribution=round(model_imp * effective_sim, 4),
            ))

        return pairs


# ═══════════════════════════════════════════════════════════════════════
#  Layer 5 — Gap & Penalty Analysis
# ═══════════════════════════════════════════════════════════════════════

class GapAnalyzer:
    """Detect coverage gaps, orphan filler, and order deviation."""

    GAP_PENALTY_RATE = 0.08   # per-unit-importance penalty for MISSING sentences
    MAX_GAP_PENALTY  = 0.20   # cap total gap penalty
    ORDER_PENALTY_RATE = 0.05 # max order disruption penalty

    @staticmethod
    def find_orphans(
        student_sents: List[SentenceInfo],
        alignment_pairs: List[AlignmentPair],
    ) -> List[str]:
        """Student sentences that are not the best match for *any* model sentence."""
        used_student_indices: Set[int] = set()
        for p in alignment_pairs:
            if p.student_index >= 0:
                used_student_indices.add(p.student_index)
        orphans = [
            s.text for s in student_sents
            if s.index not in used_student_indices
        ]
        return orphans

    @staticmethod
    def gap_penalty(alignment_pairs: List[AlignmentPair]) -> float:
        """Sum importance-weighted penalty for MISSING sentences."""
        penalty = 0.0
        for p in alignment_pairs:
            if p.match_quality == MatchQuality.MISSING:
                penalty += p.model_importance * GapAnalyzer.GAP_PENALTY_RATE
        return min(penalty, GapAnalyzer.MAX_GAP_PENALTY)

    @staticmethod
    def order_score(alignment_pairs: List[AlignmentPair]) -> float:
        """Compute order-coherence score using Kendall's tau.

        If the student answers model-sentence-1, model-sentence-3,
        model-sentence-2, that's a positional swap.  We measure how
        well the student's ordering follows the model's ordering.

        Returns a score in [0, 1] where 1 = perfect order.
        """
        # Collect (model_idx, student_idx) for matched pairs only
        matched = [
            (p.model_index, p.student_index)
            for p in alignment_pairs
            if p.student_index >= 0 and p.match_quality != MatchQuality.MISSING
        ]
        if len(matched) < 2:
            return 1.0  # too few to judge

        # Sort by model index — student indices should be ascending
        matched.sort(key=lambda x: x[0])
        student_order = [si for _, si in matched]

        # Count concordant and discordant pairs (Kendall tau)
        n = len(student_order)
        concordant = 0
        discordant = 0
        for i in range(n):
            for j in range(i + 1, n):
                if student_order[j] > student_order[i]:
                    concordant += 1
                elif student_order[j] < student_order[i]:
                    discordant += 1
                # ties ignored

        total_pairs = n * (n - 1) / 2
        if total_pairs == 0:
            return 1.0
        tau = (concordant - discordant) / total_pairs   # in [-1, 1]
        # Normalise to [0, 1]
        return max(0.0, (tau + 1.0) / 2.0)

    @staticmethod
    def redundancy_penalty(
        sim_matrix: np.ndarray,
        threshold: float = 0.85,
    ) -> float:
        """Detect if the student repeats the same sentence content.

        If multiple student sentences are very similar to each other
        (>= threshold), we apply a small diminishing-returns penalty.
        """
        n_student = sim_matrix.shape[1]
        if n_student < 2:
            return 0.0

        # Compute pairwise similarity among student columns
        # Use the embeddings already in the matrix — approximate via
        # correlation of their column vectors in the alignment matrix.
        # A quicker proxy: each student sentence column is its profile of
        # similarities against model sentences.  Two repeating student
        # sentences will have very similar profiles.
        student_profiles = sim_matrix.T     # (M, N)
        norms = np.linalg.norm(student_profiles, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normed = student_profiles / norms
        pair_sim = normed @ normed.T        # (M, M)

        repeat_count = 0
        for i in range(n_student):
            for j in range(i + 1, n_student):
                if pair_sim[i, j] >= threshold:
                    repeat_count += 1

        # Diminishing returns: each repeat adds less penalty
        penalty = 0.0
        for k in range(1, repeat_count + 1):
            penalty += 0.02 / k     # harmonic-decay penalty
        return min(penalty, 0.10)


# ═══════════════════════════════════════════════════════════════════════
#  Layer 6 — Structured Scorer  (orchestrator)
# ═══════════════════════════════════════════════════════════════════════

class SentenceAlignmentScorer:
    """
    Master orchestrator for Upgrade 5.

    Call ``score(model_text, student_text)`` to get an ``AlignmentResult``.
    """

    # Sub-score weights in the final formula
    W_ALIGNMENT = 0.50
    W_COVERAGE  = 0.20
    W_ORDER     = 0.15
    W_DEPTH     = 0.15

    def __init__(self):
        self._segmenter = SentenceSegmenter()
        self._importance = ImportanceScorer()
        self._matrix_builder = AlignmentMatrixBuilder()

    # ─── public API ──────────────────────────────────────────────────

    def score(
        self,
        model_text: str,
        student_text: str,
        custom_keywords: Optional[List[str]] = None,
    ) -> AlignmentResult:
        """Run the full 6-layer pipeline and return ``AlignmentResult``."""
        t0 = time.time()

        # ── Layer 1: Segment ────────────────────────────────────────
        model_sents = self._segmenter.segment(model_text)
        student_sents = self._segmenter.segment(student_text)

        if not model_sents or not student_sents:
            return self._empty_result(model_sents, student_sents, time.time() - t0)

        # ── Layer 2: Importance ─────────────────────────────────────
        model_sents = self._importance.score(model_sents, model_text, custom_keywords)

        # ── Layer 3: Build alignment matrix ─────────────────────────
        sim_matrix = self._matrix_builder.build_matrix(model_sents, student_sents)
        optimal_pairs = self._matrix_builder.optimal_alignment(sim_matrix)
        soft_map = self._matrix_builder.soft_alignment(sim_matrix, threshold=0.40)

        # ── Layer 4: Match analysis ─────────────────────────────────
        alignment_pairs = MatchAnalyzer.build_pairs(
            model_sents, student_sents, optimal_pairs, soft_map,
        )

        # ── Layer 5: Gap & penalty ──────────────────────────────────
        orphans = GapAnalyzer.find_orphans(student_sents, alignment_pairs)
        gap_pen = GapAnalyzer.gap_penalty(alignment_pairs)
        order_sc = GapAnalyzer.order_score(alignment_pairs)
        redundancy_pen = GapAnalyzer.redundancy_penalty(sim_matrix)

        # Order-disruption penalty: if order_score is low, apply additional penalty
        order_penalty = max(0.0, (0.5 - order_sc)) * GapAnalyzer.ORDER_PENALTY_RATE

        # ── Layer 6: Aggregate ──────────────────────────────────────
        alignment_sc = self._compute_alignment_score(alignment_pairs)
        coverage_sc  = self._compute_coverage_score(alignment_pairs)
        depth_bonus  = self._compute_depth_bonus(alignment_pairs)

        total_penalty = gap_pen + redundancy_pen + order_penalty

        combined = (
            self.W_ALIGNMENT * alignment_sc
            + self.W_COVERAGE * coverage_sc
            + self.W_ORDER * order_sc
            + self.W_DEPTH * depth_bonus
            - total_penalty
        )
        combined = max(0.0, min(1.0, combined))

        # Counts
        strong  = sum(1 for p in alignment_pairs if p.match_quality == MatchQuality.STRONG)
        partial = sum(1 for p in alignment_pairs if p.match_quality == MatchQuality.PARTIAL)
        weak    = sum(1 for p in alignment_pairs if p.match_quality == MatchQuality.WEAK)
        missing = sum(1 for p in alignment_pairs if p.match_quality == MatchQuality.MISSING)

        missing_texts = [
            p.model_text for p in alignment_pairs
            if p.match_quality == MatchQuality.MISSING
        ]

        return AlignmentResult(
            alignment_score=round(alignment_sc, 4),
            coverage_score=round(coverage_sc, 4),
            order_score=round(order_sc, 4),
            depth_bonus=round(depth_bonus, 4),
            gap_penalty=round(total_penalty, 4),
            combined_score=round(combined, 4),
            model_sentence_count=len(model_sents),
            student_sentence_count=len(student_sents),
            strong_matches=strong,
            partial_matches=partial,
            weak_matches=weak,
            missing_matches=missing,
            orphan_student_count=len(orphans),
            alignment_pairs=alignment_pairs,
            missing_sentences=missing_texts,
            orphan_sentences=orphans,
            similarity_matrix=sim_matrix,
            processing_time=round(time.time() - t0, 3),
        )

    def get_detailed_report(self, result: AlignmentResult) -> Dict:
        """Human-readable summary dict for API responses."""
        return {
            "combined_score": result.combined_score,
            "alignment_score": result.alignment_score,
            "coverage_score": result.coverage_score,
            "order_score": result.order_score,
            "depth_bonus": result.depth_bonus,
            "gap_penalty": result.gap_penalty,
            "model_sentences": result.model_sentence_count,
            "student_sentences": result.student_sentence_count,
            "match_summary": {
                "strong": result.strong_matches,
                "partial": result.partial_matches,
                "weak": result.weak_matches,
                "missing": result.missing_matches,
            },
            "missing_sentences": result.missing_sentences[:10],
            "orphan_sentences": result.orphan_sentences[:5],
            "alignment_details": [
                {
                    "model": p.model_text[:120],
                    "student": (p.student_text[:120] if p.student_text else ""),
                    "similarity": p.similarity,
                    "quality": p.match_quality,
                    "importance": p.model_importance,
                    "contribution": p.weighted_contribution,
                }
                for p in result.alignment_pairs
            ],
            "processing_time": result.processing_time,
        }

    # ─── private computations ────────────────────────────────────────

    def _compute_alignment_score(
        self, pairs: List[AlignmentPair],
    ) -> float:
        """Importance-weighted average match quality."""
        total_importance = sum(p.model_importance for p in pairs)
        if total_importance == 0:
            return 0.0
        weighted_sum = sum(p.weighted_contribution for p in pairs)
        return weighted_sum / total_importance

    def _compute_coverage_score(
        self, pairs: List[AlignmentPair],
    ) -> float:
        """Fraction of total importance that is at least partially covered."""
        total_importance = sum(p.model_importance for p in pairs)
        if total_importance == 0:
            return 0.0
        covered_importance = sum(
            p.model_importance for p in pairs
            if p.match_quality in (MatchQuality.STRONG, MatchQuality.PARTIAL)
        )
        return covered_importance / total_importance

    def _compute_depth_bonus(
        self, pairs: List[AlignmentPair],
    ) -> float:
        """Bonus for having many STRONG matches (deep understanding)."""
        strong_pairs = [p for p in pairs if p.match_quality == MatchQuality.STRONG]
        if not pairs:
            return 0.0
        ratio = len(strong_pairs) / len(pairs)
        # Scale: if all pairs are strong, bonus = 1.0
        return ratio

    def _empty_result(
        self,
        model_sents: List[SentenceInfo],
        student_sents: List[SentenceInfo],
        elapsed: float,
    ) -> AlignmentResult:
        """Return a zero-score result when one side has no sentences."""
        return AlignmentResult(
            alignment_score=0.0,
            coverage_score=0.0,
            order_score=0.0,
            depth_bonus=0.0,
            gap_penalty=0.0,
            combined_score=0.0,
            model_sentence_count=len(model_sents) if model_sents else 0,
            student_sentence_count=len(student_sents) if student_sents else 0,
            strong_matches=0,
            partial_matches=0,
            weak_matches=0,
            missing_matches=len(model_sents) if model_sents else 0,
            orphan_student_count=len(student_sents) if student_sents else 0,
            processing_time=round(elapsed, 3),
        )
