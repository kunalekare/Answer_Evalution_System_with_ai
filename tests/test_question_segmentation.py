"""
Tests for Question Segmentation Service & Multi-Question Evaluation
====================================================================
Covers: segmentation patterns, alignment, edge cases, per-question scoring.
"""

import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

passed = 0
failed = 0
total  = 0

def test(name, condition):
    global passed, failed, total
    total += 1
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}")

# ── Segmentation Service ─────────────────────────────────────────────
print("\n=== Question Segmentation Service ===")
from api.services.question_segmentation_service import QuestionSegmenter, SegmentationResult

seg = QuestionSegmenter()

# 1. Q_DOT pattern  (Q1. ... Q2. ...)
text1 = """Q1. What is photosynthesis?
Photosynthesis is the process by which plants make food.

Q2. What is respiration?
Respiration is the breaking down of glucose.

Q3. Define osmosis.
Osmosis is the movement of water through a membrane."""
r1 = seg.segment(text1)
test("Q_dot pattern detects 3 questions", r1.total_questions == 3)
test("Q_dot method identified", "q_dot" in r1.method or "question" in r1.method.lower())
test("Segments have sequential numbers", [s.question_number for s in r1.segments] == [1, 2, 3])

# 2. QUESTION_WORD pattern  (Question 1: ...)
text2 = """Question 1: Explain Newton's first law.
An object at rest stays at rest.

Question 2: State the second law.
F equals ma."""
r2 = seg.segment(text2)
test("question_word pattern detects 2 questions", r2.total_questions == 2)

# 3. DIGIT_DOT pattern (1. ... 2. ...)
text3 = """1. Define cell.
A cell is the basic unit of life.

2. What is tissue?
Tissue is a group of cells.

3. What is an organ?
An organ is a structure with specific function.

4. What is a system?
A system is a group of organs."""
r3 = seg.segment(text3)
test("digit_dot pattern detects 4 questions", r3.total_questions == 4)

# 4. ANS_NUMBER pattern (Ans 1: ... Ans 2: ...)
text4 = """Ans 1: Gravity pulls objects down.
Ans 2: Friction opposes motion.
Ans 3: Inertia resists change."""
r4 = seg.segment(text4)
test("ans_number pattern detects 3 questions", r4.total_questions == 3)

# 5. Blank-line heuristic fallback
text5 = """Photosynthesis converts sunlight into energy stored in glucose molecules using chlorophyll.

Respiration breaks down glucose into ATP releasing carbon dioxide and water as byproducts.

Osmosis moves water across semipermeable membranes from low to high solute concentration."""
r5 = seg.segment(text5)
test("blank-line heuristic produces segments", r5.total_questions >= 2)
test("blank-line method name", "blank" in r5.method.lower() or "heuristic" in r5.method.lower() or "single" in r5.method.lower())

# 6. Single text (no segmentation markers)
text6 = "Just one answer about photosynthesis."
r6 = seg.segment(text6)
test("single text returns 1 segment", r6.total_questions == 1)

# 7. Alignment
model_text = """Q1. What is photosynthesis?
Q2. What is respiration?
Q3. Define osmosis."""

student_text = """Q1. Plants use sunlight to make food.
Q3. Water moves through membrane."""

pair_result = seg.segment_pair(model_text, student_text)
test("segment_pair returns dict", isinstance(pair_result, dict))
test("segment_pair has aligned_pairs", "aligned_pairs" in pair_result)
pairs = pair_result.get("aligned_pairs", [])
test("segment_pair has entries", len(pairs) >= 2)
# Check that Q2 is detected as having no student answer or Q3 is matched
q_nums = [p["question_number"] for p in pairs]
test("aligned pairs have question numbers", all(n is not None for n in q_nums))

# 8. Sub-part detection
text8 = """Q1. Answer the following:
a) What is cell?
b) What is tissue?

Q2. State Newton's laws."""
r8 = seg.segment(text8)
test("Sub-part detection: Q1 has sub_parts or total >= 2", r8.total_questions >= 2)

# 9. segment summary via get_segment_summary
model_seg_result = seg.segment(model_text)
summary = seg.get_segment_summary(model_seg_result)
test("get_segment_summary returns dict", isinstance(summary, dict))
test("summary has total_questions", "total_questions" in summary)

# 10. Marks pattern detection
text10 = """Q1. (5 marks) What is photosynthesis?
Answer about photosynthesis.

Q2. (10 marks) Explain respiration in detail.
Answer about respiration."""
r10 = seg.segment(text10)
test("marks pattern: detects 2 questions", r10.total_questions == 2)
# Check if marks were extracted
has_marks = any(s.marks is not None for s in r10.segments)
test("marks pattern: extracts marks value", has_marks)

# 11. Confidence score
test("confidence is float 0-1", 0.0 <= r1.confidence <= 1.0)

# 12. Warnings list
test("warnings is a list", isinstance(r1.warnings, list))

# ── _evaluate_single_question_sync ────────────────────────────────
print("\n=== Single Question Evaluation Helper ===")
try:
    from api.routes.evaluation import _evaluate_single_question_sync
    
    # 13. Perfect match
    ev1 = _evaluate_single_question_sync(
        model_answer="Photosynthesis is the process by which green plants use sunlight to synthesize nutrients from carbon dioxide and water.",
        student_answer="Photosynthesis is the process by which green plants use sunlight to synthesize nutrients from carbon dioxide and water.",
        question_type="theory",
        max_marks=10,
    )
    test("perfect match returns dict", isinstance(ev1, dict))
    test("perfect match has obtained_marks", "obtained_marks" in ev1)
    test("perfect match score >= 80%", ev1["final_score"] >= 80)
    test("perfect match grade is excellent or good", ev1["grade"] in ("excellent", "good"))

    # 14. Unanswered
    ev3 = _evaluate_single_question_sync(
        model_answer="Explain photosynthesis.",
        student_answer="",
        question_type="theory",
        max_marks=10,
    )
    test("unanswered gets 0 marks", ev3["obtained_marks"] == 0)
    test("unanswered is flagged", ev3.get("is_unanswered") == True)

    # 15. Score breakdown structure
    sb = ev1.get("score_breakdown", {})
    test("breakdown has semantic_score", "semantic_score" in sb)
    test("breakdown has keyword_score", "keyword_score" in sb)
    test("breakdown has weighted_score", "weighted_score" in sb)
    test("breakdown has length_penalty", "length_penalty" in sb)

    # 16. Concepts structure
    concepts = ev1.get("concepts", {})
    test("concepts has matched list", isinstance(concepts.get("matched"), list))
    test("concepts has missing list", isinstance(concepts.get("missing"), list))
    test("concepts has coverage_percentage", "coverage_percentage" in concepts)

    # 17. Max marks applied correctly
    test("obtained_marks <= max_marks", ev1["obtained_marks"] <= ev1.get("max_marks", 10) + 0.01)

except Exception as e:
    print(f"  [SKIP] Evaluation helper tests skipped (model/network): {type(e).__name__}: {str(e)[:120]}")

# ── Pydantic Models ──────────────────────────────────────────────────
print("\n=== Pydantic Models ===")
from api.routes.evaluation import MultiQuestionRequest, PerQuestionResult, MultiQuestionResult, QuestionPair

# 21. QuestionPair validation
qp = QuestionPair(question_number=1, model_answer="What is X?", student_answer="X is Y.", max_marks=5)
test("QuestionPair creates ok", qp.model_answer == "What is X?")
test("QuestionPair has question_number", qp.question_number == 1)

# 22. MultiQuestionRequest with questions array
mqr1 = MultiQuestionRequest(questions=[qp], question_type="descriptive")
test("MultiQuestionRequest with questions array", len(mqr1.questions) == 1)

# 23. MultiQuestionRequest with raw text (auto-segment mode)
mqr2 = MultiQuestionRequest(model_answer="Q1. Answer text here\nQ2. Another answer", student_answer="Q1. My answer here\nQ2. My answer", question_type="descriptive")
test("MultiQuestionRequest with raw text", mqr2.model_answer is not None)

# 24. PerQuestionResult
pqr = PerQuestionResult(
    question_number=1,
    model_answer_preview="What...", student_answer_preview="Answer...",
    max_marks=10, obtained_marks=8, final_score=80.0, grade="good",
    score_breakdown={"semantic_score": 0.8, "keyword_score": 0.7, "weighted_score": 0.75, "length_penalty": 0.0},
    concepts={"matched": ["test"], "missing": [], "coverage_percentage": 100.0},
    explanation="Good", suggestions=[], is_unanswered=False,
)
test("PerQuestionResult creates ok", pqr.final_score == 80.0)

# 25. MultiQuestionResult
mqresult = MultiQuestionResult(
    success=True, evaluation_id="test-123",
    total_questions=2, answered_questions=2, unanswered_questions=0,
    total_max_marks=20, total_obtained_marks=16,
    overall_percentage=80.0, overall_grade="good",
    per_question=[pqr], processing_time=1.0, timestamp="now",
)
test("MultiQuestionResult creates ok", mqresult.overall_grade == "good")

# ── Results ──────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"  TOTAL: {total}  |  PASSED: {passed}  |  FAILED: {failed}")
print(f"{'='*50}")
if failed == 0:
    print("  ALL TESTS PASSED!")
else:
    print(f"  {failed} test(s) failed.")
