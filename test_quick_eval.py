"""
Quick Test: Direct Text Evaluation Without Files
=================================================
Test if the /evaluate/text endpoint works by calling it directly
and validating the 422 error issue.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test the Pydantic model directly
print("\n" + "="*80)
print("TEST 1: Pydantic Model Validation")
print("="*80)

from api.routes.evaluation import TextEvaluationRequest, QuestionType, OCREngine

# Create test request
try:
    request = TextEvaluationRequest(
        model_answer="The photosynthesis process occurs in plants where chlorophyll absorbs light energy and converts it into chemical energy.",
        student_answer="Photosynthesis is when plants use sunlight to make food.",
        question_type="descriptive",
        max_marks=10,
        ocr_engine="easyocr"
    )
    print("✅ TextEvaluationRequest model validation PASSED")
    print(f"   Model answer length: {len(request.model_answer)}")
    print(f"   Student answer length: {len(request.student_answer)}")
    print(f"   Question type: {request.question_type}")
    print(f"   Max marks: {request.max_marks}")
    print(f"   OCR engine: {request.ocr_engine}")
except Exception as e:
    print(f"❌ Model validation FAILED: {e}")
    import traceback
    traceback.print_exc()


# Test direct evaluation
print("\n" + "="*80)
print("TEST 2: Direct Evaluation (sync)")
print("="*80)

try:
    from api.routes.evaluation import _evaluate_single_question_sync
    import time
    
    model_answer = "The photosynthesis process occurs in plants where chlorophyll absorbs light energy and converts it into chemical energy. This process involves two main stages: the light-dependent reactions in the thylakoid membrane and the light-independent reactions (Calvin cycle) in the stroma."
    
    student_answer = "Photosynthesis is when plants use sunlight to make food. It happens in chloroplasts using chlorophyll. There are light reactions and dark reactions."
    
    print("Evaluating...")
    start = time.time()
    result = _evaluate_single_question_sync(
        model_answer=model_answer,
        student_answer=student_answer,
        question_type="descriptive",
        max_marks=10,
        rubric_config=None,
        custom_keywords=None
    )
    elapsed = time.time() - start
    
    print(f"✅ Evaluation completed in {elapsed:.2f}s")
    print(f"   Final score: {result.get('final_score', 'N/A')}")
    print(f"   Grade: {result.get('grade', 'N/A')}")
    print(f"   Obtained marks: {result.get('obtained_marks', 'N/A')}")
    
    if result.get('score_breakdown'):
        print(f"\n   Score breakdown:")
        for key, value in result['score_breakdown'].items():
            if value is not None:
                print(f"     {key}: {value}")
    
except Exception as e:
    print(f"❌ Direct evaluation FAILED: {e}")
    import traceback
    traceback.print_exc()


print("\n" + "="*80)
print("RECOMMENDATIONS")
print("="*80)

print("""
1. If TEST 1 passed but TEST 2 failed:
   - There's an issue with the evaluation pipeline
   - Check NLPPreprocessor, SemanticAnalyzer, or ScoringService
   
2. If TEST 1 failed with validation error:
   - There's a Pydantic model mismatch
   - Update the frontend to send correct field types
   
3. For Sarvam AI:
   - The correct package name might be different
   - Try: pip search sarvam or check PyPI directly
   - Or use: pip install sarvambot (if available)
   
4. For timeout issues (>120s):
   - The evaluation pipeline is too slow
   - Consider:
     a) Disabling some analysis layers (concept_graph, sentence_alignment)
     b) Using faster OCR engine (tesseract instead of ensemble)
     c) Running services in parallel instead of sequential
""")
