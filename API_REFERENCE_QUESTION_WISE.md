# Question-Wise Evaluation API Reference

## Overview

This document describes the API endpoints and data structures for Question-Wise Evaluation feature.

---

## Upload & Extraction Endpoints

### POST `/api/v1/upload/`

Upload model and student answers, automatically extract and clean text.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/upload/ \
  -F "model_answer=@model.pdf" \
  -F "student_answer=@student.pdf" \
  -F "question_type=descriptive" \
  -F "max_marks=10" \
  -F "subject=Physics" \
  -F "ocr_engine=easyocr"
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_answer` | File | Yes | Model answer key (PDF, PNG, JPG, etc.) |
| `student_answer` | File | No* | Student answer sheet (*or provide `student_text`) |
| `student_text` | String | No* | Student answer as text (*or provide `student_answer`) |
| `question_type` | String | No | `factual`, `descriptive`, `diagram`, `mixed` (default: `descriptive`) |
| `subject` | String | No | Subject/topic name for context |
| `max_marks` | Integer | No | Maximum marks (default: 10) |
| `ocr_engine` | String | No | `easyocr`, `ensemble`, `tesseract`, `paddleocr`, `sarvam` (default: `easyocr`) |

**Response (Success):**
```json
{
  "success": true,
  "message": "Files uploaded successfully. Ready for evaluation.",
  "data": {
    "evaluation_id": "550e8400-e29b-41d4-a716-446655440000",
    "model_answer": {
      "filename": "model_physics_20240407_a1b2c3d4.pdf",
      "saved_path": "/uploads/evaluations/550e8400-e29b-41d4-a716-446655440000/model_physics_20240407_a1b2c3d4.pdf",
      "size_bytes": 245632
    },
    "student_answer": {
      "type": "file",
      "filename": "student_physics_20240407_x9y8z7w6.pdf",
      "saved_path": "/uploads/evaluations/550e8400-e29b-41d4-a716-446655440000/student_physics_20240407_x9y8z7w6.pdf",
      "size_bytes": 189456
    },
    "metadata": {
      "question_type": "descriptive",
      "subject": "Physics",
      "max_marks": 10,
      "upload_time": "2024-04-07T10:30:45.123Z"
    }
  }
}
```

**Process (Internal):**
1. Files saved to evaluation directory
2. Text extracted using specified OCR engine
3. Text cleaned using `TextCleaningService`
4. Cleaned text cached for later use
5. Quality score calculated (0-1)

**Response (Error):**
```json
{
  "success": false,
  "message": "Failed to upload files: File too large",
  "detail": "File too large. Maximum size is 10.0MB"
}
```

---

### GET `/api/v1/upload/{evaluation_id}/extract-text`

Retrieve cached, cleaned extracted text.

**Request:**
```bash
curl "http://localhost:8000/api/v1/upload/550e8400-e29b-41d4-a716-446655440000/extract-text?ocr_engine=easyocr"
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evaluation_id` | String (Path) | Yes | Evaluation ID from upload |
| `ocr_engine` | String (Query) | No | OCR engine (for reference only) |

**Response (Success):**
```json
{
  "success": true,
  "data": {
    "evaluation_id": "550e8400-e29b-41d4-a716-446655440000",
    "ocr_engine_requested": "easyocr",
    "ocr_engine_used": "easyocr",
    "note": "✅ LOADED FROM CACHE (no re-extraction)",
    "model_answer": {
      "text": "Q1. Explain the concept of pressure in physics...\nQ2. Define force and its SI unit...",
      "char_count": 4891,
      "word_count": 742,
      "source": "cache",
      "quality_score": 0.92
    },
    "student_answer": {
      "text": "Q1. Pressure is force per unit area...\nQ2. Force is a push or pull...",
      "char_count": 3245,
      "word_count": 521,
      "source": "cache",
      "quality_score": 0.88
    }
  }
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `text` | String | Cleaned extracted text (OCR artifacts removed, errors fixed) |
| `char_count` | Integer | Length of cleaned text |
| `word_count` | Integer | Word count |
| `quality_score` | Float | 0.0-1.0 score (0.7+ is good) |
| `source` | String | `cache` (text loaded from cache), `text_input` (user typed text) |

---

## Evaluation Endpoints

### POST `/api/v1/evaluate/`

Evaluate answers (single question or per-question).

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/evaluate/ \
  -H "Content-Type: application/json" \
  -d '{
    "evaluation_id": "550e8400-e29b-41d4-a716-446655440000",
    "question_type": "descriptive",
    "max_marks": 10,
    "ocr_engine": "easyocr",
    "include_diagram": false
  }'
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evaluation_id` | String | Yes | From upload response |
| `question_type` | String | No | `factual`, `descriptive`, `diagram`, `mixed` |
| `max_marks` | Integer | No | Maximum marks (default: 10) |
| `ocr_engine` | String | No | Which engine was used (for logging) |
| `include_diagram` | Boolean | No | Include diagram analysis (default: false) |
| `rubric_config` | Object | No | Custom rubric weights |

**Response (Single Question Mode):**
```json
{
  "success": true,
  "evaluation_id": "550e8400-e29b-41d4-a716-446655440000",
  "final_score": 85.5,
  "obtained_marks": 8.55,
  "max_marks": 10,
  "grade": "good",
  "explanation": "Your answer demonstrates good understanding...",
  "suggestions": ["Mention the unit", "Provide an example"],
  "processing_time": 45.23
}
```

**Response (Question-Wise Mode - Per-Question):**
```json
{
  "success": true,
  "evaluation_id": "550e8400-e29b-41d4-a716-446655440000",
  "overall_percentage": 88.0,
  "overall_grade": "good",
  "total_questions": 4,
  "total_obtained_marks": 35,
  "total_max_marks": 40,
  "answered_questions": 4,
  "unanswered_questions": 0,
  "segmentation_info": {
    "method": "regex",
    "confidence": 0.95,
    "questions_detected": 4
  },
  "per_question": [
    {
      "question_number": 1,
      "question_label": "Q1",
      "question_text": "Explain pressure",
      "is_unanswered": false,
      "obtained_marks": 9.0,
      "max_marks": 10,
      "final_score": 90.0,
      "grade": "excellent",
      "explanation": "Excellent explanation with correct definition...",
      "suggestions": ["Add SI unit"],
      "score_breakdown": {
        "semantic_score": 0.92,
        "keyword_score": 0.88,
        "concept_graph_score": 0.95,
        "sentence_alignment_score": 0.87,
        "structural_score": 0.85,
        "rubric_score": 0.90,
        "length_penalty": 0.0,
        "anti_gaming_penalty": 0.0,
        "bloom_modifier": 0.02,
        "weighted_score": 0.90
      },
      "concepts": {
        "coverage_percentage": 85,
        "matched": ["pressure", "force", "area", "SI unit"],
        "missing": ["fluid dynamics"],
        "rubric_details": {
          "dimensions": [
            {
              "name": "clarity",
              "display_name": "Clarity",
              "weight": 0.3,
              "score": 0.95,
              "band": "Excellent"
            },
            {
              "name": "accuracy",
              "display_name": "Accuracy",
              "weight": 0.4,
              "score": 0.90,
              "band": "Excellent"
            },
            {
              "name": "completeness",
              "display_name": "Completeness",
              "weight": 0.3,
              "score": 0.85,
              "band": "Good"
            }
          ]
        }
      }
    },
    {
      "question_number": 2,
      "question_label": "Q2",
      "question_text": "Define force",
      "is_unanswered": false,
      "obtained_marks": 7.0,
      "max_marks": 10,
      "final_score": 70.0,
      "grade": "good",
      "explanation": "Good definition but missing SI unit...",
      "suggestions": ["Include SI unit (Newton)", "Add example"]
      // ... similar structure as Q1
    },
    // Q3, Q4 similarly
  ]
}
```

---

## Text Cleaning API (Backend Only)

### TextCleaningService Class

Located in: `api/services/text_cleaning_service.py`

**Main Methods:**

#### `clean_text(text: str, aggressive: bool = False) -> str`
```python
from api.services.text_cleaning_service import TextCleaningService

raw_text = "vvord rn issue tlie problem..."
cleaned = TextCleaningService.clean_text(raw_text)
# Returns: "word 'm issue the problem..."
```

#### `clean_for_question_segmentation(text: str) -> str`
```python
# Cleans specifically for question detection
cleaned = TextCleaningService.clean_for_question_segmentation(text)
```

#### `get_quality_score(text: str) -> float`
```python
# Score 0.0-1.0, where 0.7+ is considered good
quality = TextCleaningService.get_quality_score(cleaned_text)
if quality < 0.5:
    logger.warning("Text extraction quality is low")
```

#### `extract_clean_questions(text: str) -> List[str]`
```python
# Extract individual cleaned questions
questions = TextCleaningService.extract_clean_questions(text)
# Returns: ["Q1. First question...", "Q2. Second question..."]
```

---

## Question Segmentation API (Backend)

Located in: `api/services/question_segmentation_service.py`

### SegmentationResult Data Structure

```python
@dataclass
class QuestionSegment:
    question_number: int           # 1-based ordinal
    label: str                     # "Q1.", "2)", "Question 3"
    text: str                      # Answer body
    start_char: int                # Position in original text
    end_char: int                  # Position in original text
    sub_parts: List["QuestionSegment"]  # For (a), (b), etc.
    marks: Optional[int]           # Detected marks if present

@dataclass
class SegmentationResult:
    segments: List[QuestionSegment]
    total_questions: int
    method: str                    # "regex", "blank_line", "fallback"
    confidence: float              # 0-1
    warnings: List[str]
```

### Usage Example

```python
from api.services.question_segmentation_service import segment_text

result = segment_text(
    text="Q1. First question\nAnswer here\n\nQ2. Second",
    language="en"
)

print(f"Detected {result.total_questions} questions")
print(f"Method: {result.method}, Confidence: {result.confidence:.2%}")

for seg in result.segments:
    print(f"Q{seg.question_number}: {seg.label}")
    print(f"  Text: {seg.text[:50]}...")
```

---

## Frontend Utilities API

Located in: `frontend/src/utils/questionSegmentation.js`

### Functions

#### `extractQuestions(text: String) -> Array`
```javascript
import { extractQuestions } from '@/utils/questionSegmentation.js';

const questions = extractQuestions(`Q1. First question\nAnswer...\n\nQ2. Second`);
// Returns:
// [
//   { number: 1, header: "Q1. First question", content: "...", lines: [...] },
//   { number: 2, header: "Q2. Second", content: "...", lines: [...] }
// ]
```

#### `analyzeQuestionStructure(text: String) -> Object`
```javascript
const analysis = analyzeQuestionStructure(studentText);
// Returns:
// {
//   score: 0.85,        // 0-1 quality score
//   questions: 2,       // Count detected
//   issues: [],         // Array of problems found
//   details: {
//     sequential: true,
//     avgContentLength: 342,
//     minContentLength: 45,
//     maxContentLength: 623
//   }
// }
```

#### `segmentQuestionsForPreview(modelText: String, studentText: String) -> Array`
```javascript
const segments = segmentQuestionsForPreview(modelText, studentText);
// Returns paired questions:
// [
//   {
//     number: 1,
//     model: "..."
//     student: "..."
//     modelContent: "..."
//     studentContent: "..."
//   },
//   // ...
// ]
```

#### `getQuestionsQualityFeedback(modelText: String, studentText: String) -> Object`
```javascript
const feedback = getQuestionsQualityFeedback(modelText, studentText);
// Returns:
// {
//   modelQuality: 0.85,
//   studentQuality: 0.82,
//   overallQuality: 0.835,
//   suggestions: [
//     "Model answer text needs better question formatting",
//     "✓ Text is well-formatted for question-wise evaluation"
//   ]
// }
```

---

## Error Handling

### Common Errors

**400 Bad Request:**
```json
{
  "detail": "Please provide either a student answer file or text"
}
```

**404 Not Found:**
```json
{
  "detail": "Evaluation 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**413 Payload Too Large:**
```json
{
  "detail": "File too large. Maximum size is 10.0MB"
}
```

**422 Unprocessable Entity:**
```json
{
  "detail": [
    {
      "loc": ["body", "max_marks"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Failed to evaluate: OCR extraction timeout after 60 seconds"
}
```

---

## Rate Limiting & Timeouts

| Operation | Timeout | Limit |
|-----------|---------|-------|
| File upload | 300s (5 min) | 100MB max file size |
| Text extraction | 60s | 50 concurrent |
| Evaluation | 600s (10 min) | 10 concurrent |
| Results retrieval | 30s | 1000 req/min |

---

## Logging

Backend logs key information:

```
[easyocr] ✓ Engine initialized for pre-caching
[easyocr] Extracting model answer...
[easyocr] Cleaning model text...
[easyocr] ✓ Model cached: 5234 → 4891 chars (quality: 0.92)
[EXTRACT-TEXT] Model text loaded from CACHE: 4891 chars (NO RE-EXTRACTION)
```

Look for these patterns in logs to debug issues:
- `✓` = Success
- `✗` = Failure
- `⚠️` = Warning (fallback used)
- `🔍` = Debug info (parameter values)

---

## Version Information

- **First Released**: April 7, 2026
- **Feature**: Question-Wise Evaluation with OCR + Text Cleaning
- **Backend**: FastAPI/Python
- **Frontend**: React/Material-UI
- **Languages**: English (primary), Hindi (via Sarvam API)

---

## Support & Contact

For issues or enhancements:
1. Check logs for error details
2. Refer to `QUESTION_WISE_EVALUATION_COMPLETE.md`
3. Run `test_question_wise_integration.sh` to verify setup
4. Check individual service docstrings for method details
