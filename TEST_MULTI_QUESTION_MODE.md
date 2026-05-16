# Multi-Question Mode Integration Test

## Overview
This document verifies that the Question-Wise Evaluation feature works end-to-end.

## Changes Made

### 1. Frontend (Evaluate.jsx)
- ✅ `multiQuestionMode` state variable exists
- ✅ Sends `multi_question_mode: multiQuestionMode` in evalBody when evaluating file-based answers
- ✅ Checks for `result.per_question` to detect multi-question result
- ✅ Navigates to Results with `isMultiQuestion: true` flag

### 2. Backend - Model (evaluation.py)
- ✅ Added `multi_question_mode: bool = Field(default=False)` to `EvaluationRequest`

### 3. Backend - Logic (evaluation.py)
- ✅ Added early check after Phase 1 validation
- ✅ Loads cached extracted text (student_extracted.txt, model_extracted.txt)
- ✅ Creates `MultiQuestionRequest` with loaded text
- ✅ Calls `evaluate_multi_question()` function
- ✅ Returns result with `per_question` array

### 4. Response Format
- ✅ `evaluate_multi_question()` returns `MultiQuestionResult`
- ✅ Includes `per_question: List[PerQuestionResult]`
- ✅ Each per-question result includes:
  - question_number
  - max_marks
  - obtained_marks
  - final_score (0-100)
  - grade
  - score_breakdown (semantic, keyword, structure, etc.)
  - concepts (covered, partially_covered, not_covered)
  - explanation
  - suggestions

## Test Flow

### Manual Testing

1. **Upload PDFs**
   - Upload model answer PDF
   - Upload student answer PDF
   - System extracts and caches text

2. **Configure Settings**
   - Set Question Type: Descriptive
   - Set Max Marks: 40
   - Toggle "Question Wise Evaluate" button to ON
   - Verify the button shows as "active" or highlighted

3. **Evaluate**
   - Click Evaluate button
   - Wait for evaluation to complete (2-3 minutes)
   - Verify backend receives `multi_question_mode: true`

4. **Expected Result**
   - Results page displays per-question breakdown
   - Each question shows:
     - Question number (Q1, Q2, Q3, Q4, etc.)
     - Max marks for that question
     - Obtained marks for that question
     - Percentage score
     - Letter grade (A+, A, B+, etc.)
     - Detailed score breakdown
     - Concept coverage analysis
     - Improvement suggestions

### API Testing (curl/Postman)

```bash
# 1. Upload files first
curl -X POST "http://localhost:8000/api/v1/upload/" \
  -F "model_answer=@model_answer.pdf" \
  -F "student_answer=@student_answer.pdf" \
  -F "question_type=descriptive" \
  -F "max_marks=40"

# 2. Run multi-question evaluation
curl -X POST "http://localhost:8000/api/v1/evaluate/" \
  -H "Content-Type: application/json" \
  -d '{
    "evaluation_id": "<FROM_UPLOAD_RESPONSE>",
    "question_type": "descriptive",
    "max_marks": 40,
    "ocr_engine": "easyocr",
    "multi_question_mode": true
  }'

# 3. Expected response structure:
{
  "success": true,
  "evaluation_id": "...",
  "total_questions": 4,
  "answered_questions": 4,
  "unanswered_questions": 0,
  "total_max_marks": 40,
  "total_obtained_marks": 35.5,
  "overall_percentage": 88.75,
  "overall_grade": "A+",
  "per_question": [
    {
      "question_number": 1,
      "max_marks": 10,
      "obtained_marks": 9,
      "final_score": 90,
      "grade": "A+",
      "score_breakdown": {
        "semantic_relevance": 45,
        "keyword_match": 25,
        "structure_organization": 15,
        "concepts_coverage": 5
      },
      "concepts": {
        "covered": ["concept1", "concept2"],
        "partially_covered": ["concept3"],
        "not_covered": []
      },
      "explanation": "...",
      "suggestions": ["Consider adding more details about..."]
    },
    ...
  ]
}
```

## Verification Checklist

- [ ] Frontend UI shows "Question Wise Evaluate" button in Configure Settings
- [ ] Button toggles `multiQuestionMode` state
- [ ] When enabled, API request includes `"multi_question_mode": true`
- [ ] Backend receives the flag in `EvaluationRequest.multi_question_mode`
- [ ] Backend early check intercepts and loads cached text
- [ ] Backend calls `evaluate_multi_question()` with cached text
- [ ] Response includes `per_question` array with 4+ question results
- [ ] Results page displays per-question breakdown with:
  - [ ] Question numbers
  - [ ] Individual marks (e.g., Q1: 9/10, Q2: 7/10, etc.)
  - [ ] Per-question grades
  - [ ] Per-question feedback and suggestions
  - [ ] Overall summary at bottom
- [ ] Overall evaluation also displayed (total marks, overall percentage, overall grade)

## Troubleshooting

### Issue: Backend doesn't recognize multi_question_mode
**Solution**: Verify `EvaluationRequest` model has the field and default=False is set

### Issue: Evaluation still shows overall scores, not per-question
**Solution**: 
1. Check that frontend sends `multi_question_mode: true` (inspect Network tab in DevTools)
2. Check that backend early check is being executed (look for log: "🔄 [MULTI-QUESTION MODE]")
3. Verify cached text files exist at `.cache/model_extracted.txt` and `.cache/student_extracted.txt`

### Issue: Multi-question evaluation crashes
**Solution**:
1. Check logs for error in `evaluate_multi_question()` function
2. Verify text segmentation is working (check `segmentation_info` in response)
3. Ensure at least 2 questions were detected in the text

## Files Modified

1. `frontend/src/pages/Evaluate.jsx`
   - Added `multi_question_mode` to evalBody when calling `/api/v1/evaluate/`

2. `api/routes/evaluation.py`
   - Added `multi_question_mode: bool` field to `EvaluationRequest` model
   - Added early check and redirect logic in `evaluate_answer()` endpoint
   - Calls `evaluate_multi_question()` when mode is enabled

## Next Steps

1. Test the complete flow end-to-end
2. Monitor logs for any issues
3. Verify per-question results format matches UI expectations
4. Document any edge cases or improvements needed
