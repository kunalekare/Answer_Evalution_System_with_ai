"""
Concept Graph Matching Service  (Upgrade 4)
=============================================
Advanced semantic evaluation using concept-level graph analysis.

Problem with plain cosine similarity
--------------------------------------
Global SBERT cosine similarity gives ONE number for the whole answer.
A student who writes a verbose answer covering only 40 % of the key
concepts can still score 0.80+ similarity, because the 40 % of matched
content pulls the global embedding close to the model embedding.

Solution: Concept Graph Matching
----------------------------------
Instead of comparing two blobs of text, we:

1.  **Extract atomic propositions** from the model answer.
    Each proposition is one claim:  (subject, predicate, object).
    e.g. "Operating system → manages → hardware"
         "Operating system → provides → services"

2.  **Build a weighted concept graph**.
    • Nodes = key concepts (noun phrases / entities)
    • Edges = relations (verbs / prepositions connecting concepts)
    • Weights = importance (TF-IDF rank in model answer)

3.  **Check per-concept coverage**.
    For *each* model concept we compute its SBERT similarity against
    *every* student concept and pick the best match.  Concepts below
    threshold are "missing".  This is fundamentally different from a
    single global similarity score.

4.  **Anti-cheat analysis**.
    • Verbosity penalty  — lots of words, few concepts → padding
    • Copy detection     — exact long n-gram overlap → plagiarism flag
    • Concept density    — useful information per word
    • Irrelevance ratio  — student concepts absent from model graph

5.  **Combined concept-graph score**:
    score = α·coverage + β·depth + γ·relevance − penalties

Dependencies (all already installed):
    • spaCy (en_core_web_sm) — dependency parsing, noun chunks
    • sentence-transformers  — per-concept SBERT embeddings
    • numpy, scikit-learn    — cosine similarity, TF-IDF
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger("AssessIQ.ConceptGraph")


# ═══════════════════════════════════════════════════════════════════════
# Data Structures
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class Proposition:
    """One atomic claim extracted from text.

    A proposition is the smallest unit of meaning we track:
        (subject, predicate, object)
    e.g. "OS manages hardware" → subject="OS", predicate="manages",
         object="hardware"
    """
    subject: str
    predicate: str
    object: str
    full_text: str = ""
    importance: float = 1.0
    source_sentence: str = ""
    embedding: Optional[np.ndarray] = None

    @property
    def canonical(self) -> str:
        """Canonical form for deduplication."""
        return f"{self.subject.lower()} {self.predicate.lower()} {self.object.lower()}"


@dataclass
class ConceptNode:
    """Node in the concept graph — a key phrase / entity."""
    id: int
    label: str                          # display text
    concept_type: str = "entity"        # entity | action | property
    importance: float = 1.0             # TF-IDF weight
    embedding: Optional[np.ndarray] = None
    propositions: List[Proposition] = field(default_factory=list)
    # matching state (filled during scoring)
    matched: bool = False
    match_score: float = 0.0
    matched_by: str = ""


@dataclass
class ConceptEdge:
    """Directed edge between two concept nodes."""
    source_id: int
    target_id: int
    relation: str       # verb / preposition
    weight: float = 1.0


class ConceptGraph:
    """Weighted directed graph of concepts and their relations."""

    def __init__(self):
        self.nodes: Dict[int, ConceptNode] = {}
        self.edges: List[ConceptEdge] = []
        self._next_id = 0

    # ── mutation ──────────────────────────────────────────────────

    def add_node(self, label: str, concept_type: str = "entity",
                 importance: float = 1.0) -> int:
        """Add (or get existing) node.  Returns node id."""
        # Deduplicate by normalised label
        norm = label.lower().strip()
        for nid, node in self.nodes.items():
            if node.label.lower().strip() == norm:
                # Update importance to max
                node.importance = max(node.importance, importance)
                return nid
        nid = self._next_id
        self._next_id += 1
        self.nodes[nid] = ConceptNode(
            id=nid, label=label,
            concept_type=concept_type,
            importance=importance,
        )
        return nid

    def add_edge(self, src: int, tgt: int, relation: str,
                 weight: float = 1.0):
        """Add a directed edge."""
        self.edges.append(ConceptEdge(src, tgt, relation, weight))

    # ── queries ───────────────────────────────────────────────────

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    def total_importance(self) -> float:
        return sum(n.importance for n in self.nodes.values())

    def covered_importance(self) -> float:
        return sum(
            n.importance * n.match_score
            for n in self.nodes.values()
        )

    def get_labels(self) -> List[str]:
        return [n.label for n in self.nodes.values()]

    def get_missing_concepts(self, threshold: float = 0.5) -> List[str]:
        return [
            n.label for n in self.nodes.values()
            if n.match_score < threshold
        ]

    def summary(self) -> Dict:
        covered = sum(1 for n in self.nodes.values() if n.matched)
        partial = sum(
            1 for n in self.nodes.values()
            if not n.matched and n.match_score >= 0.3
        )
        return {
            "total_concepts": self.node_count,
            "edges": self.edge_count,
            "covered": covered,
            "partial": partial,
            "missing": self.node_count - covered - partial,
        }


@dataclass
class ConceptMatchDetail:
    """Detailed match info for one model concept."""
    model_concept: str
    importance: float
    best_student_match: str
    similarity: float
    status: str            # "covered" | "partial" | "missing"


@dataclass
class ConceptGraphScore:
    """Complete scoring result from concept graph analysis."""
    # core scores (0-1)
    coverage_score: float = 0.0       # what fraction of model concepts are covered
    depth_score: float = 0.0          # average match quality of covered concepts
    relevance_score: float = 0.0      # what fraction of student content is relevant
    density_score: float = 0.0        # concept-to-word ratio comparison
    combined_score: float = 0.0       # final composite score

    # penalties
    verbosity_penalty: float = 0.0
    copy_penalty: float = 0.0

    # details
    concept_matches: List[ConceptMatchDetail] = field(default_factory=list)
    missing_concepts: List[str] = field(default_factory=list)
    irrelevant_phrases: List[str] = field(default_factory=list)

    # counts
    model_concept_count: int = 0
    student_concept_count: int = 0
    covered_count: int = 0
    partial_count: int = 0
    missing_count: int = 0

    # timing
    processing_time: float = 0.0


# ═══════════════════════════════════════════════════════════════════════
# Layer 1: Concept / Proposition Extraction
# ═══════════════════════════════════════════════════════════════════════

class ConceptExtractor:
    """
    Extracts atomic propositions and key phrases from text.

    Uses a multi-strategy approach:
      1. spaCy dependency parsing   → (subj, verb, obj) triples
      2. Noun-chunk extraction      → key entity phrases
      3. Sentence decomposition     → breaks compound sentences
      4. Regex fallback             → when spaCy is unavailable

    All extracted concepts are deduplicated and ranked by importance.
    """

    # Minimum length (chars) for a concept to be kept
    MIN_CONCEPT_LEN = 3
    # Maximum concepts to extract per text
    MAX_CONCEPTS = 80

    def __init__(self):
        self._nlp = None
        self._tfidf = None
        self._init_nlp()

    def _init_nlp(self):
        """Load spaCy model (used for dependency parsing)."""
        try:
            import spacy
            try:
                self._nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.info("Downloading spaCy en_core_web_sm...")
                from spacy.cli import download
                download("en_core_web_sm")
                self._nlp = spacy.load("en_core_web_sm")
            logger.debug("ConceptExtractor: spaCy loaded")
        except ImportError:
            logger.warning(
                "spaCy not available — falling back to regex concept extraction"
            )

    # ── public API ────────────────────────────────────────────────

    def extract_propositions(self, text: str) -> List[Proposition]:
        """Extract (subject, predicate, object) triples from text."""
        if self._nlp:
            return self._extract_propositions_spacy(text)
        return self._extract_propositions_regex(text)

    def extract_key_phrases(self, text: str) -> List[str]:
        """Extract noun chunks / key phrases."""
        if self._nlp:
            return self._extract_phrases_spacy(text)
        return self._extract_phrases_regex(text)

    def rank_by_importance(
        self, phrases: List[str], full_text: str
    ) -> List[Tuple[str, float]]:
        """Rank phrases by TF-IDF importance in the source text."""
        if not phrases:
            return []
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            vectorizer = TfidfVectorizer(
                lowercase=True, stop_words="english",
                ngram_range=(1, 3), max_features=500,
            )
            tfidf_matrix = vectorizer.fit_transform([full_text])
            feature_names = vectorizer.get_feature_names_out()
            scores_arr = tfidf_matrix.toarray()[0]
            score_map = dict(zip(feature_names, scores_arr))

            ranked = []
            for phrase in phrases:
                # Sum TF-IDF of constituent tokens
                tokens = phrase.lower().split()
                score = sum(score_map.get(t, 0) for t in tokens)
                # Also check bigrams / trigrams
                for n in range(2, min(4, len(tokens) + 1)):
                    for i in range(len(tokens) - n + 1):
                        ngram = " ".join(tokens[i:i + n])
                        score += score_map.get(ngram, 0) * 1.5
                ranked.append((phrase, max(score, 0.1)))

            ranked.sort(key=lambda x: x[1], reverse=True)
            # Normalise to [0.1, 1.0]
            if ranked:
                max_s = ranked[0][1]
                if max_s > 0:
                    ranked = [
                        (p, max(0.1, s / max_s)) for p, s in ranked
                    ]
            return ranked[:self.MAX_CONCEPTS]

        except Exception as e:
            logger.debug(f"TF-IDF ranking failed: {e}")
            return [(p, 1.0) for p in phrases[:self.MAX_CONCEPTS]]

    # ── spaCy-based extraction ────────────────────────────────────

    def _extract_propositions_spacy(self, text: str) -> List[Proposition]:
        """Use dependency parsing to extract SVOs."""
        doc = self._nlp(text[:10000])  # cap input length
        propositions: List[Proposition] = []
        seen: Set[str] = set()

        for sent in doc.sents:
            sent_text = sent.text.strip()
            # Find subjects
            subjects = [
                tok for tok in sent
                if tok.dep_ in ("nsubj", "nsubjpass") and not tok.is_stop
            ]
            for subj in subjects:
                # Walk up to root verb
                verb = subj.head
                if verb.pos_ not in ("VERB", "AUX"):
                    continue

                # Find objects
                objects = [
                    child for child in verb.children
                    if child.dep_ in (
                        "dobj", "attr", "pobj", "oprd",
                        "acomp", "xcomp",
                    )
                ]
                # Also look for prepositional objects
                for child in verb.children:
                    if child.dep_ == "prep":
                        for grandchild in child.children:
                            if grandchild.dep_ == "pobj":
                                objects.append(grandchild)

                # Expand tokens to their full noun chunks
                subj_text = self._expand_to_chunk(subj, doc)
                for obj_tok in objects:
                    obj_text = self._expand_to_chunk(obj_tok, doc)
                    pred_text = verb.lemma_

                    prop = Proposition(
                        subject=subj_text,
                        predicate=pred_text,
                        object=obj_text,
                        full_text=f"{subj_text} {pred_text} {obj_text}",
                        source_sentence=sent_text,
                    )
                    if prop.canonical not in seen:
                        seen.add(prop.canonical)
                        propositions.append(prop)

            # Handle conjunctions (compound objects)
            # "OS manages hardware and software" →
            #   (OS, manages, hardware), (OS, manages, software)
            for tok in sent:
                if tok.dep_ == "conj" and tok.head.dep_ in ("dobj", "attr", "pobj"):
                    # Find the subject of the head's verb
                    verb = tok.head.head
                    if verb.pos_ not in ("VERB", "AUX"):
                        continue
                    subj_tok = None
                    for child in verb.children:
                        if child.dep_ in ("nsubj", "nsubjpass"):
                            subj_tok = child
                            break
                    if subj_tok:
                        subj_text = self._expand_to_chunk(subj_tok, doc)
                        obj_text = self._expand_to_chunk(tok, doc)
                        pred_text = verb.lemma_
                        prop = Proposition(
                            subject=subj_text, predicate=pred_text,
                            object=obj_text,
                            full_text=f"{subj_text} {pred_text} {obj_text}",
                            source_sentence=sent_text,
                        )
                        if prop.canonical not in seen:
                            seen.add(prop.canonical)
                            propositions.append(prop)

        return propositions

    def _expand_to_chunk(self, token, doc) -> str:
        """Expand a single token to its enclosing noun chunk."""
        for chunk in doc.noun_chunks:
            if token.i >= chunk.start and token.i < chunk.end:
                return chunk.text.strip()
        # No chunk found — return the token with its immediate modifiers
        parts = []
        for child in token.children:
            if child.dep_ in ("amod", "compound", "det") and not child.is_stop:
                parts.append(child.text)
        parts.append(token.text)
        return " ".join(parts).strip()

    def _extract_phrases_spacy(self, text: str) -> List[str]:
        """Extract noun chunks + named entities via spaCy."""
        doc = self._nlp(text[:10000])
        phrases: List[str] = []
        seen: Set[str] = set()

        # Noun chunks
        for chunk in doc.noun_chunks:
            # Remove leading determiners/pronouns
            clean = self._clean_chunk(chunk.text)
            if len(clean) >= self.MIN_CONCEPT_LEN and clean.lower() not in seen:
                seen.add(clean.lower())
                phrases.append(clean)

        # Named entities
        for ent in doc.ents:
            if len(ent.text) >= self.MIN_CONCEPT_LEN and ent.text.lower() not in seen:
                seen.add(ent.text.lower())
                phrases.append(ent.text)

        # Verb phrases (important actions)
        for tok in doc:
            if tok.pos_ == "VERB" and not tok.is_stop:
                # Get verb + its direct object as a phrase
                obj_tokens = [
                    c for c in tok.children
                    if c.dep_ in ("dobj", "attr")
                ]
                for obj in obj_tokens:
                    vp = f"{tok.lemma_} {self._expand_to_chunk(obj, doc)}"
                    if vp.lower() not in seen:
                        seen.add(vp.lower())
                        phrases.append(vp)

        return phrases[:self.MAX_CONCEPTS]

    # ── Regex fallback extraction ─────────────────────────────────

    def _extract_propositions_regex(self, text: str) -> List[Proposition]:
        """Fallback: extract pseudo-propositions using regex."""
        sentences = re.split(r'[.!?]+', text)
        propositions: List[Proposition] = []
        seen: Set[str] = set()

        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 10:
                continue
            # Try pattern: <NP> <VP> <NP>
            # Simplified: split on common verbs
            verbs = [
                "is", "are", "was", "were", "has", "have", "had",
                "manages", "provides", "handles", "performs", "includes",
                "contains", "defines", "describes", "explains", "controls",
                "allocates", "schedules", "processes", "converts", "uses",
                "creates", "enables", "supports", "implements", "stores",
                "refers", "involves", "requires", "allows", "helps",
            ]
            for verb in verbs:
                pattern = re.compile(
                    rf'\b(\w[\w\s]{{2,30}}?)\s+{verb}\s+(\w[\w\s]{{2,30}}?)(?:[.,;!?]|$)',
                    re.IGNORECASE,
                )
                for m in pattern.finditer(sent):
                    subj = m.group(1).strip()
                    obj = m.group(2).strip()
                    prop = Proposition(
                        subject=subj, predicate=verb, object=obj,
                        full_text=f"{subj} {verb} {obj}",
                        source_sentence=sent,
                    )
                    if prop.canonical not in seen:
                        seen.add(prop.canonical)
                        propositions.append(prop)

        return propositions

    def _extract_phrases_regex(self, text: str) -> List[str]:
        """Fallback: extract capitalised / multi-word phrases via regex."""
        # Common noun phrase patterns
        phrases: List[str] = []
        seen: Set[str] = set()

        # Multi-word capitalised phrases
        for m in re.finditer(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', text):
            p = m.group(0).strip()
            if p.lower() not in seen:
                seen.add(p.lower())
                phrases.append(p)

        # Words that appear multiple times (likely important)
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        from collections import Counter
        counts = Counter(words)
        stopwords = {
            "this", "that", "with", "from", "have", "which", "their",
            "these", "those", "been", "being", "they", "them", "also",
            "such", "than", "each", "very", "will", "would", "could",
            "should", "about", "into", "when", "where", "what", "some",
            "more", "other", "over", "only", "just", "most",
        }
        for word, count in counts.most_common(40):
            if count >= 2 and word not in stopwords and word not in seen:
                seen.add(word)
                phrases.append(word)

        return phrases[:self.MAX_CONCEPTS]

    # ── helpers ───────────────────────────────────────────────────

    @staticmethod
    def _clean_chunk(text: str) -> str:
        """Remove leading determiners / pronouns from noun chunk."""
        determiners = {
            "a", "an", "the", "this", "that", "these", "those",
            "my", "your", "his", "her", "its", "our", "their",
            "some", "any", "no", "every", "each", "all",
        }
        words = text.strip().split()
        while words and words[0].lower() in determiners:
            words.pop(0)
        return " ".join(words)


# ═══════════════════════════════════════════════════════════════════════
# Layer 2: Semantic Graph Builder
# ═══════════════════════════════════════════════════════════════════════

class SemanticGraphBuilder:
    """
    Builds a weighted concept graph from extracted propositions
    and key phrases.

    Graph structure:
      • Nodes: key concepts (noun phrases, entities, actions)
      • Edges: relations (verbs / prepositions from propositions)
      • Node weights: TF-IDF importance in the source text

    The graph also pre-computes SBERT embeddings for every node,
    enabling fast per-concept matching later.
    """

    def __init__(self, embedder=None):
        """
        Args:
            embedder: object with .get_embedding(list[str]) → np.ndarray
                      (SemanticAnalyzer from semantic_service will be used)
        """
        self._embedder = embedder

    def _ensure_embedder(self):
        if self._embedder is None:
            from api.services.semantic_service import SemanticAnalyzer
            self._embedder = SemanticAnalyzer()

    def build(
        self,
        text: str,
        propositions: List[Proposition],
        key_phrases: List[str],
        importance_map: Dict[str, float],
    ) -> ConceptGraph:
        """
        Build a complete concept graph from extraction results.

        Args:
            text: source text (for context)
            propositions: extracted (S, P, O) triples
            key_phrases: extracted noun chunks / entities
            importance_map: {phrase: importance_score}

        Returns:
            ConceptGraph with embedded nodes and relation edges
        """
        self._ensure_embedder()
        graph = ConceptGraph()

        # 1. Add nodes from key phrases
        for phrase in key_phrases:
            imp = importance_map.get(phrase, importance_map.get(phrase.lower(), 0.5))
            graph.add_node(phrase, "entity", imp)

        # 2. Add nodes + edges from propositions
        for prop in propositions:
            subj_imp = importance_map.get(
                prop.subject, importance_map.get(prop.subject.lower(), 0.5)
            )
            obj_imp = importance_map.get(
                prop.object, importance_map.get(prop.object.lower(), 0.5)
            )
            sid = graph.add_node(prop.subject, "entity", subj_imp)
            oid = graph.add_node(prop.object, "entity", obj_imp)
            graph.add_edge(sid, oid, prop.predicate)
            # Attach proposition to source node
            graph.nodes[sid].propositions.append(prop)

        # 3. Compute SBERT embeddings for all nodes (batch)
        if graph.nodes:
            labels = [n.label for n in graph.nodes.values()]
            try:
                embeddings = self._embedder.get_embedding(labels)
                for node, emb in zip(graph.nodes.values(), embeddings):
                    node.embedding = emb
            except Exception as e:
                logger.warning(f"Embedding failed for concept nodes: {e}")

        logger.info(
            f"Built concept graph: {graph.node_count} nodes, "
            f"{graph.edge_count} edges"
        )
        return graph


# ═══════════════════════════════════════════════════════════════════════
# Layer 3: Per-Concept Matcher
# ═══════════════════════════════════════════════════════════════════════

class ConceptMatcher:
    """
    Matches student concepts against model concept graph.

    For each model node:
      1. Compute cosine similarity against every student concept
      2. Best match above threshold → "covered"
      3. Best match above 50 % of threshold → "partial"
      4. Below that → "missing"

    This is the KEY DIFFERENCE from global cosine similarity:
    each concept is checked individually, so skipping a concept
    is detected even if the rest of the answer is perfect.
    """

    # Similarity thresholds
    COVERED_THRESHOLD = 0.55       # above this → fully covered
    PARTIAL_THRESHOLD = 0.35       # above this → partially covered

    def __init__(self, embedder=None):
        self._embedder = embedder

    def _ensure_embedder(self):
        if self._embedder is None:
            from api.services.semantic_service import SemanticAnalyzer
            self._embedder = SemanticAnalyzer()

    def match(
        self,
        model_graph: ConceptGraph,
        student_phrases: List[str],
    ) -> List[ConceptMatchDetail]:
        """
        Match every model concept against student phrases.

        Args:
            model_graph: concept graph of the model answer
            student_phrases: extracted phrases from student answer

        Returns:
            List of ConceptMatchDetail for every model node
        """
        self._ensure_embedder()

        if not model_graph.nodes:
            return []

        # Batch-encode student phrases
        if not student_phrases:
            student_embeddings = np.array([])
        else:
            try:
                student_embeddings = self._embedder.get_embedding(student_phrases)
                if student_embeddings.ndim == 1:
                    student_embeddings = student_embeddings.reshape(1, -1)
            except Exception as e:
                logger.warning(f"Student phrase embedding failed: {e}")
                student_embeddings = np.array([])

        results: List[ConceptMatchDetail] = []

        for node in model_graph.nodes.values():
            if node.embedding is None or student_embeddings.size == 0:
                detail = ConceptMatchDetail(
                    model_concept=node.label,
                    importance=node.importance,
                    best_student_match="",
                    similarity=0.0,
                    status="missing",
                )
                results.append(detail)
                continue

            # Cosine similarity against all student embeddings
            sims = self._cosine_batch(node.embedding, student_embeddings)
            best_idx = int(np.argmax(sims))
            best_sim = float(sims[best_idx])

            # Raw cosine can be in [-1, 1]; normalise to [0, 1]
            # SBERT typically gives 0-1 for same-language texts
            best_sim_norm = max(0.0, best_sim)

            if best_sim_norm >= self.COVERED_THRESHOLD:
                status = "covered"
                node.matched = True
            elif best_sim_norm >= self.PARTIAL_THRESHOLD:
                status = "partial"
            else:
                status = "missing"

            node.match_score = best_sim_norm
            node.matched_by = student_phrases[best_idx] if student_phrases else ""

            detail = ConceptMatchDetail(
                model_concept=node.label,
                importance=node.importance,
                best_student_match=student_phrases[best_idx] if student_phrases else "",
                similarity=round(best_sim_norm, 4),
                status=status,
            )
            results.append(detail)

        return results

    def find_irrelevant(
        self,
        model_graph: ConceptGraph,
        student_phrases: List[str],
        threshold: float = 0.30,
    ) -> List[str]:
        """
        Find student phrases that are NOT relevant to any model concept.

        These are off-topic padding phrases.
        """
        self._ensure_embedder()

        if not student_phrases or not model_graph.nodes:
            return []

        try:
            student_embs = self._embedder.get_embedding(student_phrases)
            if student_embs.ndim == 1:
                student_embs = student_embs.reshape(1, -1)
        except Exception:
            return []

        model_embs = np.array([
            n.embedding for n in model_graph.nodes.values()
            if n.embedding is not None
        ])
        if model_embs.size == 0:
            return []

        irrelevant = []
        for i, s_emb in enumerate(student_embs):
            sims = self._cosine_batch(s_emb, model_embs)
            max_sim = float(np.max(sims))
            if max_sim < threshold:
                irrelevant.append(student_phrases[i])

        return irrelevant

    @staticmethod
    def _cosine_batch(vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        """Cosine similarity of one vector against a matrix of vectors."""
        if matrix.size == 0:
            return np.array([])
        # Normalise
        vec_norm = vec / (np.linalg.norm(vec) + 1e-10)
        mat_norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10
        mat_normalised = matrix / mat_norms
        return mat_normalised @ vec_norm


# ═══════════════════════════════════════════════════════════════════════
# Layer 4: Anti-Cheat Analysis
# ═══════════════════════════════════════════════════════════════════════

class AntiCheatAnalyzer:
    """
    Detects gaming / cheating strategies:

    1. **Verbosity padding**: student writes 3× more words but covers
       the same or fewer concepts → penalty.

    2. **Exact copy detection**: student copies large chunks of the
       model answer verbatim → flag + penalty.

    3. **Concept density analysis**: ratio of unique concepts to
       word count.  Low density = lots of filler.

    4. **Contradiction detection**: student says something that
       directly contradicts the model (future extension).
    """

    # N-gram size for copy detection
    COPY_NGRAM_SIZE = 5
    # Fraction of model n-grams found verbatim in student → copy flag
    COPY_THRESHOLD = 0.40
    # Student / model word ratio above which verbosity penalty kicks in
    VERBOSITY_RATIO = 2.0
    # Maximum verbosity penalty
    MAX_VERBOSITY_PENALTY = 0.15
    # Maximum copy penalty
    MAX_COPY_PENALTY = 0.20

    def analyze_verbosity(
        self, model_text: str, student_text: str,
        model_concept_count: int, student_concept_count: int,
    ) -> float:
        """
        Detect verbose padding.

        Penalty is applied when student writes significantly more words
        but has similar or fewer unique concepts.

        Returns:
            penalty value (0 to MAX_VERBOSITY_PENALTY)
        """
        model_words = len(model_text.split())
        student_words = len(student_text.split())

        if model_words == 0:
            return 0.0

        word_ratio = student_words / max(model_words, 1)
        concept_ratio = student_concept_count / max(model_concept_count, 1)

        # Penalty when word count is disproportionately high vs concepts
        if word_ratio > self.VERBOSITY_RATIO and concept_ratio < 1.2:
            excess = (word_ratio - self.VERBOSITY_RATIO) / self.VERBOSITY_RATIO
            penalty = min(excess * 0.1, self.MAX_VERBOSITY_PENALTY)
            logger.debug(
                f"Verbosity penalty: {penalty:.3f} "
                f"(words {student_words}/{model_words}={word_ratio:.1f}x, "
                f"concepts {student_concept_count}/{model_concept_count})"
            )
            return penalty

        return 0.0

    def analyze_copy(
        self, model_text: str, student_text: str,
    ) -> Tuple[float, float]:
        """
        Detect verbatim copying using n-gram overlap.

        Returns:
            (penalty, copy_ratio)
        """
        model_words = model_text.lower().split()
        student_words = student_text.lower().split()

        if len(model_words) < self.COPY_NGRAM_SIZE:
            return 0.0, 0.0

        # Build n-gram sets
        model_ngrams = set()
        for i in range(len(model_words) - self.COPY_NGRAM_SIZE + 1):
            ngram = tuple(model_words[i:i + self.COPY_NGRAM_SIZE])
            model_ngrams.add(ngram)

        if not model_ngrams:
            return 0.0, 0.0

        student_ngrams = set()
        for i in range(len(student_words) - self.COPY_NGRAM_SIZE + 1):
            ngram = tuple(student_words[i:i + self.COPY_NGRAM_SIZE])
            student_ngrams.add(ngram)

        # Overlap
        overlap = model_ngrams & student_ngrams
        copy_ratio = len(overlap) / len(model_ngrams)

        if copy_ratio >= self.COPY_THRESHOLD:
            penalty = min(
                (copy_ratio - self.COPY_THRESHOLD) * 0.5,
                self.MAX_COPY_PENALTY,
            )
            logger.debug(
                f"Copy detection: {copy_ratio:.1%} n-gram overlap, "
                f"penalty={penalty:.3f}"
            )
            return penalty, copy_ratio

        return 0.0, copy_ratio

    def analyze_density(
        self,
        student_text: str,
        student_concept_count: int,
        model_density: float,
    ) -> float:
        """
        Compare concept density (concepts / 100 words) between
        model and student.

        Returns:
            density score (0-1).  1.0 = student density matches or
            exceeds model density.
        """
        student_words = len(student_text.split())
        if student_words == 0:
            return 0.0

        student_density = (student_concept_count / student_words) * 100
        if model_density <= 0:
            return 1.0

        ratio = student_density / model_density
        return min(ratio, 1.0)


# ═══════════════════════════════════════════════════════════════════════
# Layer 5: Master Orchestrator
# ═══════════════════════════════════════════════════════════════════════

class ConceptGraphScorer:
    """
    Complete concept-graph scoring pipeline.

    Orchestrates:
      1. ConceptExtractor   — extract propositions + phrases
      2. SemanticGraphBuilder — build weighted graph
      3. ConceptMatcher      — per-concept matching
      4. AntiCheatAnalyzer   — penalties
      5. Score computation   — combine into final score

    Usage:
        scorer = ConceptGraphScorer()
        result = scorer.score(model_text, student_text)
        print(f"Coverage: {result.coverage_score:.2%}")
        print(f"Missing: {result.missing_concepts}")
        print(f"Combined: {result.combined_score:.2%}")

    Score formula:
        combined = (α * coverage + β * depth + γ * relevance)
                   - verbosity_penalty - copy_penalty

        α = 0.50  (concept coverage matters most)
        β = 0.30  (quality of coverage)
        γ = 0.20  (relevance of student content)
    """

    # Weights for combining sub-scores
    ALPHA_COVERAGE = 0.50
    BETA_DEPTH = 0.30
    GAMMA_RELEVANCE = 0.20

    def __init__(self):
        self._extractor = ConceptExtractor()
        self._builder: Optional[SemanticGraphBuilder] = None
        self._matcher: Optional[ConceptMatcher] = None
        self._anti_cheat = AntiCheatAnalyzer()
        self._embedder = None

    def _ensure_services(self):
        """Lazy-initialise SBERT-dependent services."""
        if self._embedder is None:
            from api.services.semantic_service import SemanticAnalyzer
            self._embedder = SemanticAnalyzer()
            self._builder = SemanticGraphBuilder(self._embedder)
            self._matcher = ConceptMatcher(self._embedder)

    def score(
        self,
        model_text: str,
        student_text: str,
    ) -> ConceptGraphScore:
        """
        Full concept-graph scoring pipeline.

        Args:
            model_text: The reference / model answer
            student_text: The student's answer

        Returns:
            ConceptGraphScore with all sub-scores and details
        """
        start = time.time()
        self._ensure_services()

        result = ConceptGraphScore()

        if not model_text or not model_text.strip():
            result.processing_time = time.time() - start
            return result

        if not student_text or not student_text.strip():
            result.processing_time = time.time() - start
            return result

        # ── Step 1: Extract concepts from model answer ────────────
        model_propositions = self._extractor.extract_propositions(model_text)
        model_phrases = self._extractor.extract_key_phrases(model_text)
        model_ranked = self._extractor.rank_by_importance(model_phrases, model_text)
        model_importance = {p: s for p, s in model_ranked}

        logger.debug(
            f"Model: {len(model_propositions)} propositions, "
            f"{len(model_phrases)} phrases"
        )

        # ── Step 2: Build model concept graph ─────────────────────
        model_graph = self._builder.build(
            model_text, model_propositions, model_phrases, model_importance,
        )
        result.model_concept_count = model_graph.node_count

        if model_graph.node_count == 0:
            # Cannot do concept matching — return neutral score
            result.coverage_score = 0.5
            result.combined_score = 0.5
            result.processing_time = time.time() - start
            return result

        # ── Step 3: Extract concepts from student answer ──────────
        student_phrases = self._extractor.extract_key_phrases(student_text)
        result.student_concept_count = len(student_phrases)

        # ── Step 4: Per-concept matching ──────────────────────────
        matches = self._matcher.match(model_graph, student_phrases)
        result.concept_matches = matches

        covered = [m for m in matches if m.status == "covered"]
        partial = [m for m in matches if m.status == "partial"]
        missing = [m for m in matches if m.status == "missing"]

        result.covered_count = len(covered)
        result.partial_count = len(partial)
        result.missing_count = len(missing)
        result.missing_concepts = [m.model_concept for m in missing]

        # ── Step 5: Compute coverage score (importance-weighted) ──
        total_importance = model_graph.total_importance()
        if total_importance > 0:
            weighted_coverage = sum(
                m.importance * m.similarity
                for m in matches
                if m.status in ("covered", "partial")
            )
            result.coverage_score = min(
                weighted_coverage / total_importance, 1.0
            )
        else:
            result.coverage_score = 0.0

        # ── Step 6: Depth score (average quality of matched) ──────
        covered_sims = [m.similarity for m in matches if m.status == "covered"]
        if covered_sims:
            result.depth_score = float(np.mean(covered_sims))
        else:
            # Give some credit for partial matches
            partial_sims = [m.similarity for m in matches if m.status == "partial"]
            result.depth_score = float(np.mean(partial_sims)) * 0.5 if partial_sims else 0.0

        # ── Step 7: Relevance score ───────────────────────────────
        irrelevant = self._matcher.find_irrelevant(
            model_graph, student_phrases,
        )
        result.irrelevant_phrases = irrelevant[:10]  # cap for report

        if student_phrases:
            relevant_count = len(student_phrases) - len(irrelevant)
            result.relevance_score = max(0.0, relevant_count / len(student_phrases))
        else:
            result.relevance_score = 0.0

        # ── Step 8: Anti-cheat analysis ───────────────────────────
        result.verbosity_penalty = self._anti_cheat.analyze_verbosity(
            model_text, student_text,
            model_graph.node_count, len(student_phrases),
        )

        copy_penalty, copy_ratio = self._anti_cheat.analyze_copy(
            model_text, student_text,
        )
        result.copy_penalty = copy_penalty

        # Density score (informational)
        model_words = len(model_text.split())
        model_density = (model_graph.node_count / max(model_words, 1)) * 100
        result.density_score = self._anti_cheat.analyze_density(
            student_text, len(student_phrases), model_density,
        )

        # ── Step 9: Combined score ────────────────────────────────
        raw = (
            self.ALPHA_COVERAGE * result.coverage_score
            + self.BETA_DEPTH * result.depth_score
            + self.GAMMA_RELEVANCE * result.relevance_score
        )
        penalised = raw - result.verbosity_penalty - result.copy_penalty
        result.combined_score = max(0.0, min(1.0, penalised))

        result.processing_time = time.time() - start

        logger.info(
            f"Concept graph score: {result.combined_score:.3f} "
            f"(coverage={result.coverage_score:.2f}, "
            f"depth={result.depth_score:.2f}, "
            f"relevance={result.relevance_score:.2f}, "
            f"penalties=-{result.verbosity_penalty + result.copy_penalty:.3f}) "
            f"[{result.covered_count}/{result.model_concept_count} concepts covered, "
            f"{result.processing_time:.2f}s]"
        )

        return result

    def get_detailed_report(
        self, result: ConceptGraphScore,
    ) -> Dict:
        """
        Generate a human-readable report from scoring results.

        Useful for feedback generation and debugging.
        """
        report = {
            "summary": {
                "combined_score": round(result.combined_score, 4),
                "coverage": f"{result.coverage_score:.1%}",
                "depth": f"{result.depth_score:.1%}",
                "relevance": f"{result.relevance_score:.1%}",
                "model_concepts": result.model_concept_count,
                "student_concepts": result.student_concept_count,
                "covered": result.covered_count,
                "partial": result.partial_count,
                "missing": result.missing_count,
            },
            "missing_concepts": result.missing_concepts[:15],
            "irrelevant_content": result.irrelevant_phrases[:10],
            "penalties": {
                "verbosity": round(result.verbosity_penalty, 4),
                "copy_detection": round(result.copy_penalty, 4),
            },
            "concept_details": [
                {
                    "concept": m.model_concept,
                    "importance": round(m.importance, 2),
                    "matched_with": m.best_student_match,
                    "similarity": round(m.similarity, 3),
                    "status": m.status,
                }
                for m in result.concept_matches
            ],
        }
        return report


# ═══════════════════════════════════════════════════════════════════════
# Module-level quick test
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.DEBUG)

    model = """
    An operating system is system software that manages computer hardware
    and software resources. It provides common services for computer programs.
    Key functions include process scheduling, memory management,
    file system management, and device driver coordination.
    """

    student = """
    An operating system manages hardware and provides services to programs.
    It handles process scheduling and memory management.
    """

    print("=" * 60)
    print("  Concept Graph Matching — Demo")
    print("=" * 60)
    print(f"\nModel answer ({len(model.split())} words):")
    print(model.strip())
    print(f"\nStudent answer ({len(student.split())} words):")
    print(student.strip())

    scorer = ConceptGraphScorer()
    result = scorer.score(model, student)
    report = scorer.get_detailed_report(result)

    print(f"\n--- Score ---")
    print(f"  Coverage:  {result.coverage_score:.1%}")
    print(f"  Depth:     {result.depth_score:.1%}")
    print(f"  Relevance: {result.relevance_score:.1%}")
    print(f"  Combined:  {result.combined_score:.1%}")

    print(f"\n--- Concepts ({result.model_concept_count} total) ---")
    for m in result.concept_matches:
        icon = "✓" if m.status == "covered" else ("~" if m.status == "partial" else "✗")
        print(f"  {icon} {m.model_concept} → {m.best_student_match} ({m.similarity:.2f})")

    if result.missing_concepts:
        print(f"\n--- Missing ---")
        for c in result.missing_concepts:
            print(f"  • {c}")

    print(f"\nProcessing time: {result.processing_time:.2f}s")
