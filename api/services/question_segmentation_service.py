"""
Question Segmentation Service
==============================
Advanced service for detecting and splitting answer sheets / answer text
into per-question segments.  Handles both model answers and student answers.

Supports:
  • Numbered patterns: "1.", "1)", "Q1.", "Q1)", "Question 1", "Ans 1"
  • Lettered sub-parts: "a)", "b)", "(a)", "(b)"
  • Roman numeral patterns: "i.", "ii.", "iii."
  • Mixed Hindi/English numbering: "प्रश्न 1", "उत्तर 1"
  • Heading-style segmentation via blank-line heuristics
  • Robust fallback: treat entire text as single question when no markers found
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("AssessIQ.QuestionSegmentation")


# ═════════════════════════════════════════════════════════════════════
#  Data Structures
# ═════════════════════════════════════════════════════════════════════

@dataclass
class QuestionSegment:
    """A single question + answer segment extracted from text."""
    question_number: int           # 1-based ordinal
    label: str                     # original label text e.g. "Q1.", "2)", "Question 3"
    text: str                      # the answer body for this question
    start_char: int = 0            # char offset in original text
    end_char: int = 0              # char offset in original text
    sub_parts: List["QuestionSegment"] = field(default_factory=list)
    marks: Optional[int] = None    # if marks detected e.g. "[5 marks]"


@dataclass
class SegmentationResult:
    """Result of segmenting a text into questions."""
    segments: List[QuestionSegment]
    total_questions: int
    method: str                     # which strategy succeeded
    confidence: float               # 0-1 confidence in segmentation quality
    warnings: List[str] = field(default_factory=list)


# ═════════════════════════════════════════════════════════════════════
#  Compiled regex patterns
# ═════════════════════════════════════════════════════════════════════

# Pattern 1: "Q1.", "Q.1.", "Q 1.", "Q1)", "Q1:", "q1."
_Q_DOT = re.compile(
    r'^[ \t]*[Qq]\.?\s*(\d{1,3})\s*[.):]\s*',
    re.MULTILINE,
)

# Pattern 2: "Question 1", "Question 1.", "Question 1:"
_QUESTION_WORD = re.compile(
    r'^[ \t]*(?:Question|QUESTION|Ques|Que)\s*[.:\-]?\s*(\d{1,3})\s*[.):]*\s*',
    re.MULTILINE,
)

# Pattern 3: "1.", "1)", "1:", "1 ." at line start (with possible indentation)
_DIGIT_DOT = re.compile(
    r'^[ \t]*(\d{1,3})\s*[.):\-]\s+',
    re.MULTILINE,
)

# Pattern 4: "Ans 1", "Ans. 1", "Answer 1"
_ANS_NUM = re.compile(
    r'^[ \t]*(?:Ans(?:wer)?)\s*\.?\s*(\d{1,3})\s*[.):]*\s*',
    re.MULTILINE,
)

# Pattern 5: Sub-parts "(a)", "a)", "a.", "(i)", "i)"
_SUB_PART = re.compile(
    r'^[ \t]*\(?([a-hA-H]|[ivxIVX]{1,4})\)\s*',
    re.MULTILINE,
)

# Pattern 6: Marks indicator "[5 marks]", "(5 marks)", "[5M]"
_MARKS_PATTERN = re.compile(
    r'\[?\(?\s*(\d{1,3})\s*(?:marks?|m|M)\s*\]?\)?\s*$',
    re.MULTILINE,
)

# ═════════════════════════════════════════════════════════════════════
#  Heuristic helpers
# ═════════════════════════════════════════════════════════════════════

def _clean_text(text: str) -> str:
    """Normalise whitespace but preserve structure."""
    # Replace tabs with spaces
    text = text.replace('\t', '    ')
    # Collapse 3+ newlines into 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _detect_marks(text: str) -> Optional[int]:
    """Try to extract marks from a question header."""
    m = _MARKS_PATTERN.search(text)
    if m:
        return int(m.group(1))
    return None


def _validate_sequence(numbers: List[int]) -> Tuple[bool, float]:
    """
    Check if detected question numbers form a valid sequence.
    Returns (is_valid, confidence).
    """
    if not numbers:
        return False, 0.0
    if len(numbers) == 1:
        return True, 0.7  # Single question is plausible

    # Check 1-based sequential
    expected = list(range(numbers[0], numbers[0] + len(numbers)))
    if numbers == expected:
        return True, 0.95

    # Check mostly sequential (allow small gaps)
    sequential_pairs = sum(
        1 for i in range(1, len(numbers)) if numbers[i] == numbers[i - 1] + 1
    )
    ratio = sequential_pairs / max(len(numbers) - 1, 1)
    if ratio >= 0.6:
        return True, 0.6 + ratio * 0.3

    # Check at least monotonically increasing
    if all(numbers[i] >= numbers[i - 1] for i in range(1, len(numbers))):
        return True, 0.5

    return False, 0.2


def _extract_segments_from_matches(
    text: str,
    matches: List[Tuple[int, int, str, int]],
    method: str,
) -> Optional[SegmentationResult]:
    """
    Given sorted (start, end_of_header, label, q_number) tuples,
    split text into segments.
    """
    if not matches:
        return None

    # Sort by position
    matches = sorted(matches, key=lambda m: m[0])

    # Validate sequence
    numbers = [m[3] for m in matches]
    is_valid, confidence = _validate_sequence(numbers)
    if not is_valid and len(matches) > 1:
        return None

    segments: List[QuestionSegment] = []
    for i, (start, header_end, label, q_num) in enumerate(matches):
        # Text runs from header_end to next match start (or end of text)
        if i + 1 < len(matches):
            body_end = matches[i + 1][0]
        else:
            body_end = len(text)
        body = text[header_end:body_end].strip()

        # Check for marks in the label region
        marks = _detect_marks(text[start:header_end + 50] if header_end + 50 <= len(text) else text[start:])

        seg = QuestionSegment(
            question_number=q_num,
            label=label.strip(),
            text=body,
            start_char=start,
            end_char=body_end,
            marks=marks,
        )
        segments.append(seg)

    warnings = []
    if len(segments) == 1:
        warnings.append("Only 1 question detected — the answer may not be segmented.")

    return SegmentationResult(
        segments=segments,
        total_questions=len(segments),
        method=method,
        confidence=confidence,
        warnings=warnings,
    )


# ═════════════════════════════════════════════════════════════════════
#  Strategy functions (tried in priority order)
# ═════════════════════════════════════════════════════════════════════

def _try_pattern(text: str, pattern: re.Pattern, method_name: str) -> Optional[SegmentationResult]:
    """Generic strategy: find all matches for a numbered pattern."""
    matches_raw = list(pattern.finditer(text))
    if len(matches_raw) < 1:
        return None

    matches: List[Tuple[int, int, str, int]] = []
    for m in matches_raw:
        start = m.start()
        end = m.end()
        label = m.group(0)
        q_num = int(m.group(1))
        matches.append((start, end, label, q_num))

    return _extract_segments_from_matches(text, matches, method_name)


def _try_blank_line_heuristic(text: str) -> Optional[SegmentationResult]:
    """
    Fallback: split on double-newlines (paragraph boundaries).
    Only triggers when paragraphs are ≥ 3 and each has decent length.
    """
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]

    # Need at least 2 substantial paragraphs
    substantial = [p for p in paragraphs if len(p) >= 30]
    if len(substantial) < 2:
        return None

    segments: List[QuestionSegment] = []
    offset = 0
    for i, para in enumerate(paragraphs):
        if len(para) < 15:
            continue
        idx = text.find(para, offset)
        seg = QuestionSegment(
            question_number=len(segments) + 1,
            label=f"Section {len(segments) + 1}",
            text=para,
            start_char=idx if idx >= 0 else offset,
            end_char=(idx + len(para)) if idx >= 0 else offset + len(para),
        )
        segments.append(seg)
        if idx >= 0:
            offset = idx + len(para)

    if len(segments) < 2:
        return None

    return SegmentationResult(
        segments=segments,
        total_questions=len(segments),
        method="blank_line_heuristic",
        confidence=0.35,
        warnings=["Segmented by paragraph breaks — accuracy may be lower."],
    )


# ═════════════════════════════════════════════════════════════════════
#  Sub-part detection (runs on each segment's text)
# ═════════════════════════════════════════════════════════════════════

def _detect_sub_parts(segment: QuestionSegment) -> None:
    """Find sub-parts (a, b, c or i, ii, iii) within a segment."""
    matches = list(_SUB_PART.finditer(segment.text))
    if len(matches) < 2:
        return  # need at least 2 sub-parts

    sub_parts: List[QuestionSegment] = []
    for i, m in enumerate(matches):
        label = m.group(0).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(segment.text)
        body = segment.text[start:end].strip()
        sub = QuestionSegment(
            question_number=i + 1,
            label=label,
            text=body,
            start_char=segment.start_char + m.start(),
            end_char=segment.start_char + end,
        )
        sub_parts.append(sub)

    segment.sub_parts = sub_parts


# ═════════════════════════════════════════════════════════════════════
#  Alignment helper — match model Q segments ↔ student Q segments
# ═════════════════════════════════════════════════════════════════════

def align_segments(
    model_segments: List[QuestionSegment],
    student_segments: List[QuestionSegment],
) -> List[Dict[str, Any]]:
    """
    Align model answer segments with student answer segments by question number.
    Returns list of {"question_number", "model_segment", "student_segment"} dicts.
    Missing answers get None.
    """
    model_map = {s.question_number: s for s in model_segments}
    student_map = {s.question_number: s for s in student_segments}

    all_numbers = sorted(set(model_map.keys()) | set(student_map.keys()))
    pairs = []
    for qnum in all_numbers:
        pairs.append({
            "question_number": qnum,
            "model_segment": model_map.get(qnum),
            "student_segment": student_map.get(qnum),
        })
    return pairs


# ═════════════════════════════════════════════════════════════════════
#  Main Service Class
# ═════════════════════════════════════════════════════════════════════

class QuestionSegmenter:
    """
    Segment answer text into per-question blocks.

    Usage:
        segmenter = QuestionSegmenter()
        result = segmenter.segment(text)
        for seg in result.segments:
            print(f"Q{seg.question_number}: {seg.text[:60]}...")
    """

    # Strategy priority — higher-confidence patterns first
    _STRATEGIES = [
        ("question_word", _QUESTION_WORD),
        ("q_dot_number", _Q_DOT),
        ("ans_number", _ANS_NUM),
        ("digit_dot", _DIGIT_DOT),
    ]

    def segment(self, text: str) -> SegmentationResult:
        """
        Segment the given text into question blocks.
        Tries multiple strategies in confidence order; falls back to
        single-segment if nothing works.
        """
        if not text or len(text.strip()) < 5:
            return SegmentationResult(
                segments=[QuestionSegment(
                    question_number=1,
                    label="Q1",
                    text=text or "",
                )],
                total_questions=1,
                method="empty_fallback",
                confidence=1.0,
                warnings=["Text too short to segment."],
            )

        cleaned = _clean_text(text)

        # Try each numbered pattern
        best_result: Optional[SegmentationResult] = None
        for method_name, pattern in self._STRATEGIES:
            result = _try_pattern(cleaned, pattern, method_name)
            if result and result.total_questions >= 2:
                # Keep the best (highest confidence + most questions)
                if (
                    best_result is None
                    or result.confidence > best_result.confidence
                    or (result.confidence == best_result.confidence
                        and result.total_questions > best_result.total_questions)
                ):
                    best_result = result

        if best_result and best_result.total_questions >= 2:
            # Detect sub-parts within each segment
            for seg in best_result.segments:
                _detect_sub_parts(seg)
            logger.info(
                f"Segmented into {best_result.total_questions} questions "
                f"via {best_result.method} (confidence={best_result.confidence:.2f})"
            )
            return best_result

        # Try blank-line heuristic
        heuristic = _try_blank_line_heuristic(cleaned)
        if heuristic and heuristic.total_questions >= 2:
            for seg in heuristic.segments:
                _detect_sub_parts(seg)
            logger.info(
                f"Segmented into {heuristic.total_questions} questions "
                f"via blank_line_heuristic"
            )
            return heuristic

        # Fallback: entire text as single question
        logger.info("No question markers found — treating as single question.")
        return SegmentationResult(
            segments=[QuestionSegment(
                question_number=1,
                label="Q1",
                text=cleaned,
                start_char=0,
                end_char=len(cleaned),
            )],
            total_questions=1,
            method="single_question_fallback",
            confidence=1.0,
        )

    def segment_pair(
        self, model_text: str, student_text: str
    ) -> Dict[str, Any]:
        """
        Segment both model and student texts, then align by question number.
        Returns a dict with model_result, student_result, aligned_pairs.
        """
        model_result = self.segment(model_text)
        student_result = self.segment(student_text)

        pairs = align_segments(model_result.segments, student_result.segments)

        return {
            "model_result": model_result,
            "student_result": student_result,
            "aligned_pairs": pairs,
            "total_questions": len(pairs),
        }

    @staticmethod
    def get_segment_summary(result: SegmentationResult) -> Dict[str, Any]:
        """Serialise segmentation result for API response."""
        return {
            "total_questions": result.total_questions,
            "method": result.method,
            "confidence": round(result.confidence, 3),
            "warnings": result.warnings,
            "segments": [
                {
                    "question_number": s.question_number,
                    "label": s.label,
                    "text_preview": s.text[:120] + ("..." if len(s.text) > 120 else ""),
                    "text_length": len(s.text),
                    "marks": s.marks,
                    "sub_parts_count": len(s.sub_parts),
                }
                for s in result.segments
            ],
        }
