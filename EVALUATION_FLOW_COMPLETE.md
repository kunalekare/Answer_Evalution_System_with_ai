## 📋 Answer Sheet Evaluation Flow - Complete Execution Guide

### Overview
This document explains the **complete execution flow** of the Evaluation Section - from when a user uploads answer sheets to when they receive the final score.

---

## 🔄 Complete Evaluation Flow

### Phase 1: Upload & Validation
```
User Action: Upload Files
    ↓
Upload Route (/api/v1/upload/)
    ├─ Receives: model_answer.pdf + student_answer.pdf
    ├─ Validates: File extension, file size, format
    ├─ Creates: Unique evaluation directory (UUID)
    ├─ Saves: Files to evaluation folder
    └─ Returns: evaluation_id (e.g., "abc123-def456")

Directory Structure Created:
uploads/evaluations/
└── abc123-def456/
    ├── model_abc123.pdf
    └── student_xyz789.pdf
```

---

### Phase 2: Evaluation Initiated
```
User Action: Click Evaluate
    ↓
Evaluation Route POST /api/v1/evaluate/
    ↓
EvaluationRequest Received:
{
    "evaluation_id": "abc123-def456",
    "question_type": "descriptive",
    "max_marks": 10,
    "ocr_engine": "easyocr",
    "custom_keywords": ["concept1", "concept2"]
}
```

---

## 🎯 Phase 3: File Detection & OCR Engine Selection

### Step 1: Detect File Types
```
Check uploaded files:
├─ model file type: .pdf? .png? .jpg?
└─ student file type: .pdf? .png? .jpg?

Check if PDF detected:
├─ IF PDF → Auto-switch to "sarvam" engine
│  └─ Reason: Better for handwritten content
└─ ELSE → Use user's selected engine
```

### Step 2: Initialize OCR Service
```
OCRService Initialization:
    ├─ Engine: easyocr (or sarvam if PDF)
    ├─ Languages: ["en", "hi", "ta", "te"]
    ├─ Load Models: Download if not cached
    └─ Status: Ready for extraction
```

### Step 3: Log Setup
```
Logging Output:
[INFO] Evaluation abc123-def456 using OCR engine: easyocr
[INFO] 🖼️ Extracting student image - wait for language detection...
[INFO] ✓ Image extraction complete - Student: 1234 chars
[INFO] 🖼️ Extracting model image - wait for language detection...
[INFO] ✓ Image extraction complete - Model: 2456 chars
```

---

## 📄 Phase 4: Text Extraction (OCR)

### For Image Files:
```
OCR Extraction Process:
    ├─ Detect language from filename (auto)
    │  └─ "student_hindi.png" → language=hi
    │
    ├─ Run OCR Engine:
    │  ├─ Preprocess image (enhance, denoise)
    │  ├─ Extract text using engine
    │  ├─ Calculate confidence score
    │  └─ Post-process (fix errors)
    │
    ├─ Validate extraction:
    │  ├─ Check if text > 50 chars
    │  ├─ Check quality score
    │  └─ Log warnings if poor quality
    │
    └─ Return extracted text
```

### For PDF Files:
```
PDF Extraction Process:
    ├─ Force Sarvam AI engine
    │
    ├─ For EACH page in PDF:
    │  ├─ Try embedded text extraction
    │  ├─ If no text → Render page to image
    │  ├─ Run Sarvam OCR on rendered image
    │  ├─ Detect language from filename
    │  ├─ Add page number to text
    │  └─ Log: "[PDF Page 1/5] ✓ Extracted 456 chars"
    │
    ├─ Join all pages with "\n\n"
    │
    └─ Return complete text from all pages
```

### Extraction Log Example:
```
📄 Extracting student PDF (Sarvam AI) - processing ALL pages...
[PDF Extraction] Processing 5 pages with language=hi
[PDF Page 1/5] Found embedded text (234 chars)
[PDF Page 2/5] No embedded text, rendering for OCR...
[PDF Page 2/5] Calling sarvam for OCR...
[PDF Page 2/5] ✓ OCR extracted 456 chars
[PDF Page 3/5] ✓ OCR extracted 389 chars
[PDF Page 4/5] ✓ OCR extracted 412 chars
[PDF Page 5/5] ✓ OCR extracted 267 chars
[PDF Extraction] ✓ Complete! Processed 5 pages, extracted 1758 chars
✓ PDF extraction complete - Student: 1758 chars
```

---

## 🧹 Phase 5: Text Preprocessing (NLP)

### Step 1: Normalize Text
```
NLPPreprocessor.normalize_text():
    ├─ Remove extra whitespace
    ├─ Fix encoding issues
    ├─ Standardize punctuation
    ├─ Convert to consistent case
    └─ Remove artifacts from OCR

Input:  "the  QUICK   brown  fox..."
Output: "the quick brown fox..."
```

### Step 2: Extract Keywords
```
NLPPreprocessor.extract_keywords():
    ├─ Remove stop words (the, is, and, etc.)
    ├─ Extract named entities (concepts, terms)
    ├─ Weight by frequency
    ├─ Filter by relevance
    
Example Model Keywords: ["photosynthesis", "chlorophyll", "glucose", "oxygen"]
Example Student Keywords: ["photosynthesis", "glucose", "energy"]
```

### Step 3: Extract Sentences
```
NLPPreprocessor.extract_sentences():
    ├─ Split text into sentences
    ├─ Clean each sentence
    ├─ Filter out very short sentences
    ├─ Maintain sentence order
    
Output:
Sentence 1: "Photosynthesis is the process..."
Sentence 2: "Plants use chlorophyll to capture..."
Sentence 3: "The glucose produced is used for energy..."
...
```

---

## 🔍 Phase 6: Semantic Analysis

### Step 1: Calculate Similarity Score
```
SemanticAnalyzer.calculate_similarity():
    ├─ Embed model text → Vector A
    ├─ Embed student text → Vector B
    ├─ Calculate cosine similarity
    │  └─ Range: 0.0 (completely different) to 1.0 (identical)
    │
    └─ Return: Similarity Score (0-1)

Example:
Model:   "Photosynthesis converts light energy to chemical energy"
Student: "Plants capture sunlight to produce energy compounds"
Score:   0.82 (HIGH similarity - same concept, different words)
```

### Step 2: Interpretation
```
Score Ranges in settings.py:
0.85+ → EXCELLENT similarity
0.70-0.84 → GOOD similarity
0.50-0.69 → AVERAGE similarity
<0.50 → POOR similarity
```

---

## 🔑 Phase 7: Keyword Coverage Analysis

### Step 1: Extract Keywords
```
ScoringService.calculate_keyword_coverage():
    ├─ Model Keywords: [kw1, kw2, kw3, kw4, kw5]
    ├─ Student Keywords: [kw2, kw3, kw5, kw6]
    │
    ├─ Calculate matches:
    │  ├─ Matched: [kw2, kw3, kw5] = 3 keywords
    │  ├─ Missing: [kw1, kw4] = 2 keywords
    │  └─ Extra: [kw6] = 1 keyword
    │
    └─ Calculate coverage:
       Coverage = Matched / Total Model Keywords
       Coverage = 3 / 5 = 0.60 (60%) = SCORE: 0.60
```

### Step 2: Keyword Score
```
Example Calculation:
Model Keywords: 6 important keywords
Matched: 4 keywords
Missing: 2 keywords
Score: 4/6 = 0.67 (67% coverage)
Weight in final score: 15%
Contribution: 0.67 × 0.15 = 0.10 (10 points)
```

---

## 🌐 Phase 8: Concept Graph Analysis (Optional)

### Step 1: Extract Propositions
```
ConceptGraphScorer.score():
    ├─ Extract from model answer:
    │  ├─ Proposition 1: (Photosynthesis, uses, Light)
    │  ├─ Proposition 2: (Light, converted to, Chemical Energy)
    │  └─ Proposition 3: (Chlorophyll, absorbs, Light Wavelengths)
    │
    ├─ Extract from student answer:
    │  ├─ Proposition 1: (Photosynthesis, process, Light)
    │  ├─ Proposition 2: (Light, produces, Energy)
    │  └─ Proposition 3: (Plants, have, Chlorophyll)
    │
    └─ Graph Scoring (based on similarity)
```

### Step 2: Calculate Concept Graph Score
```
Concept Matching:
├─ Model Concepts: 8 unique concepts
├─ Student Concepts: 7 unique concepts
├─ Matched Concepts: 5 concepts
├─ Coverage: 5/8 = 0.625
│
└─ Score: 0.625 (62.5%)
   Weight: 25%
   Contribution: 0.625 × 0.25 = 0.156 (15.6 points)
```

---

## 📊 Phase 9: Sentence Alignment Matrix

### Step 1: Build Alignment Matrix
```
SentenceAlignmentScorer.score():
    ├─ Model Sentences: [S1, S2, S3, S4, S5]
    ├─ Student Sentences: [T1, T2, T3]
    │
    ├─ Build Alignment Matrix:
    │  
    │        T1    T2    T3
    │    S1 [0.85] 0.12  0.05
    │    S2 [0.70] 0.88  0.15
    │    S3 [0.05] 0.92  0.08
    │    S4 [0.10] 0.15  0.85
    │    S5 [0.02] 0.08  0.65
    │
    └─ Find best alignment (greedy or optimal)
       S1→T1 (0.85), S2→T2 (0.88), S3→T2 (0.92), S4→T3 (0.85), S5→T3 (0.65)
```

### Step 2: Calculate Alignment Score
```
Alignment Scoring:
├─ Best Match Score: avg([0.85, 0.88, 0.92, 0.85, 0.65]) = 0.83
├─ Coverage: 5 model sentences matched / 5 total = 1.0
│
└─ Final Score: (0.83 + 1.0) / 2 = 0.915 (91.5%)
   Weight: 25%
   Contribution: 0.915 × 0.25 = 0.229 (22.9 points)
```

---

## 🏗️ Phase 10: Structural Analysis (Optional)

### Step 1: Analyze Structure
```
StructuralAnalyzer.score():
    ├─ Check for Introduction
    │  └─ "Photosynthesis is..." or "This process is..." → 1.0
    │
    ├─ Check for Body/Details
    │  └─ Multiple detailed sentences → Score by coverage
    │
    ├─ Check for Definition
    │  └─ "X is the process of..." → 1.0
    │
    ├─ Check for Examples
    │  └─ "For example...", "Like..." → 1.0
    │
    └─ Check for Conclusion
       └─ "In conclusion...", "Therefore..." → 1.0
```

### Step 2: Calculate Structural Bonus
```
Structure Score: 0.75 (3 of 4 components present)
Bonus Cap: 0.08 (8% max bonus)
Bonus: 0.75 × 0.08 = 0.06 (6% bonus)

This bonus is added to final score (if structural quality is good)
```

---

## 🎖️ Phase 11: Bloom's Taxonomy Evaluation (Optional)

### Step 1: Detect Cognitive Level
```
BloomTaxonomyScorer.score():
    ├─ Expected Level: 5 (Analysis)
    ├─ Question asks: "Analyze how photosynthesis..."
    │
    ├─ Analyze student answer for cognitive indicators:
    │  ├─ Remember Level (1): "defines", "lists" → INDICATOR: 1
    │  ├─ Understand Level (2): "explains", "describes" → INDICATOR: 2
    │  ├─ Apply Level (3): "applies", "uses" → INDICATOR: 3
    │  ├─ Analyze Level (4): "compares", "contrasts" → INDICATOR: 4
    │  ├─ Evaluate Level (5): "judges", "critiques" → INDICATOR: 5
    │  └─ Create Level (6): "hypothesizes" → INDICATOR: 6
    │
    └─ Detected Level: 4 (Analysis found)
```

### Step 2: Calculate Bloom Score
```
Expected Level: 5
Detected Level: 4
Difference: -1 (1 level below expected)

Penalty: Yes (below expected level)
Penalty Amount: 0.15 × 0.10 = 0.015 (1.5% penalty)

If above expected: Apply bonus instead
Bonus: 0.05 × 0.10 = 0.005 (0.5% bonus per level above)
```

---

## ⚔️ Phase 12: Anti-Gaming Protection (Optional)

### Step 1: Detect Gaming Patterns
```
AntiGamingService.detect_gaming():
    ├─ Repetition Detection
    │  └─ Same phrase repeated 3+ times → GAMING SCORE: 20%
    │
    ├─ Keyword Stuffing
    │  └─ Keywords = 70% of answer → GAMING SCORE: 30%
    │
    ├─ Irrelevance Detection
    │  └─ Answer similarity to expected: 0.15 → GAMING SCORE: 40%
    │
    ├─ Gibberish Detection
    │  └─ Dictionary words: 20% only → GAMING SCORE: 50%
    │
    └─ Plagiarism Patterns
       └─ Exact sentences from random sources → GAMING SCORE: 60%
```

### Step 2: Calculate Gaming Penalty
```
Total Gaming Score: 25% (some repetition detected)
Max Penalty Cap: 0.40 (40% max penalty)
Penalty Applied: 25% × 0.40 = 0.10 (max 10% penalty)

This penalty is subtracted from final score
```

---

## 💯 Phase 13: Confidence Index Calculation

### Step 1: Calculate Confidence
```
ConfidenceService.calculate():
    ├─ Factor 1: OCR Quality Score → 0.92
    ├─ Factor 2: Semantic Consistency → 0.88
    ├─ Factor 3: Text Length Adequacy → 0.85
    ├─ Factor 4: Grammar/Structure Quality → 0.80
    ├─ Factor 5: Keyword Match Precision → 0.87
    │
    └─ Weighted Average:
       (0.92×0.25 + 0.88×0.25 + 0.85×0.20 + 0.80×0.15 + 0.87×0.15)
       = 0.873 (87.3% CONFIDENCE)
```

### Step 2: Define Confidence Range
```
Confidence Levels:
0.90-1.00 → ✅ VERY HIGH (Highly Reliable)
0.70-0.89 → ✅ HIGH (Reliable)
0.50-0.69 → ⚠️  MEDIUM (Review Recommended)
0.30-0.49 → ⚠️  LOW (Manual Review Needed)
<0.30     → ❌ VERY LOW (Unreliable - Flag for Human Review)

In Example: 0.873 → HIGH CONFIDENCE
```

---

## 📈 Phase 14: Final Scoring & Weighting

### Step 1: Collect All Scores
```
Individual Component Scores:
├─ Semantic Similarity: 0.82 (Weight: 20%)
├─ Keyword Coverage: 0.67 (Weight: 15%)
├─ Concept Graph: 0.62 (Weight: 25%)
├─ Sentence Alignment: 0.91 (Weight: 25%)
├─ Structural Bonus: +0.06
├─ Bloom's Penalty: -0.015
└─ Anti-Gaming Penalty: 0.0
```

### Step 2: Calculate Weighted Score
```
Final Score = (Weighted Sum of Components) + Bonuses - Penalties

Calculation:
├─ Semantic: 0.82 × 0.20 = 0.164
├─ Keywords: 0.67 × 0.15 = 0.101
├─ Concepts: 0.62 × 0.25 = 0.155
├─ Alignment: 0.91 × 0.25 = 0.228
├─ Structural Bonus: +0.060
├─ Bloom's Penalty: -0.015
└─ Gaming Penalty: 0.000

Total: 0.164 + 0.101 + 0.155 + 0.228 + 0.060 - 0.015 = 0.693 (69.3%)
```

### Step 3: Convert to Marks
```
Raw Score: 0.693 (69.3%)
Max Marks: 10
Final Marks: 0.693 × 10 = 6.93

Rounded: 6.93 / 10 (or 7/10)
```

---

## 📊 Phase 15: Grading & Interpretation

### Step 1: Determine Grade Level
```
if score >= 0.85:
    grade = "EXCELLENT" ⭐⭐⭐⭐⭐
elif score >= 0.70:
    grade = "GOOD" ⭐⭐⭐⭐
elif score >= 0.50:
    grade = "AVERAGE" ⭐⭐⭐
else:
    grade = "POOR" ⭐⭐

Example: 0.693 → GOOD (comes under 0.70)
```

### Step 2: Flag for Manual Review (if needed)
```
Review Triggers:
├─ Confidence < 0.50 → FLAG: Low confidence, needs review
├─ Semantic Score < 0.30 → FLAG: Very low similarity
├─ Gaming Score > 50% → FLAG: Suspicious patterns
├─ Blank/Empty pages → FLAG: Invalid submission
└─ Length < Required → FLAG: Incomplete answer

In Example: No flags → Automatic evaluation sufficient
```

---

## 📦 Phase 16: Generate Results

### Step 1: Create Result Object
```python
{
    "evaluation_id": "abc123-def456",
    "score": 6.93,
    "max_marks": 10,
    "percentage": 69.3,
    "grade": "GOOD",
    
    "breakdown": {
        "semantic_score": 0.82,
        "keyword_coverage": 0.67,
        "concept_graph": 0.62,
        "sentence_alignment": 0.91,
        "structural_analysis": 0.75,
        "bloom_level": 4
    },
    
    "confidence": 0.873,
    "confidence_level": "HIGH",
    
    "recommendations": [
        "Student demonstrated good understanding of concepts",
        "Could improve on providing examples",
        "Structure and organization needs work"
    ],
    
    "extraction_details": {
        "model_text_length": 2456,
        "student_text_length": 1758,
        "ocr_engine": "easyocr",
        "extraction_time": 3.5
    },
    
    "timestamp": "2026-04-01T10:30:45Z"
}
```

### Step 2: Save Results
```
Database Storage:
├─ Evaluation record created
├─ Score stored
├─ Breakdown saved
├─ Confidence index saved
├─ Recommendations stored
└─ Timestamp recorded

File Storage:
├─ Result JSON saved to: uploads/evaluations/abc123/result.json
├─ Extraction logs saved to: logs/assessiq.log
└─ Analysis details stored in database
```

---

## 📤 Phase 17: Return Response to User

### Step 1: API Response
```json
{
    "success": true,
    "message": "Evaluation completed successfully",
    "data": {
        "evaluation_result": {
            "score": 6.93,
            "max_marks": 10,
            "percentage": 69.3,
            "grade": "GOOD",
            "confidence": 0.873,
            "extraction_info": {
                "student_chars": 1758,
                "model_chars": 2456,
                "engine_used": "easyocr"
            }
        }
    }
}
```

### Step 2: User Interface Update
```
Frontend receives response:
├─ Display Score: 6.93/10
├─ Display Grade: GOOD ⭐⭐⭐⭐
├─ Display Confidence: 87.3% ✓ High
├─ Show Breakdown Chart
├─ Display Recommendations
└─ Show Detailed Analysis
```

---

## 📋 Complete Execution Timeline

| Phase | Action | Time | Component |
|-------|--------|------|-----------|
| 1 | Upload files | 2-5s | Upload Route |
| 2 | Validation | <1s | Middleware |
| 3 | OCR Engine Setup | 2-10s | OCRService Init |
| 4 | Text Extraction | 3-60s | OCR Engine |
| 5 | Preprocessing | <2s | NLPPreprocessor |
| 6 | Semantic Analysis | 2-5s | SemanticAnalyzer |
| 7 | Keyword Analysis | <1s | ScoringService |
| 8 | Concept Graph | 3-8s | ConceptGraphScorer |
| 9 | Sentence Alignment | 2-5s | SentenceAlignmentScorer |
| 10 | Structural Analysis | <1s | StructuralAnalyzer |
| 11 | Bloom's Taxonomy | <1s | BloomTaxonomyScorer |
| 12 | Anti-Gaming | <1s | AntiGamingService |
| 13 | Confidence Index | <1s | ConfidenceService |
| 14 | Final Scoring | <1s | ScoringService |
| 15 | Grading | <1s | ScoringService |
| 16 | Result Generation | <1s | ResultGenerator |
| 17 | Response | <1s | API Response |

**Total Time: 15-100+ seconds** (depending on PDF pages and OCR complexity)

---

## 🔧 Key Components Involved

### Services Used:
- ✅ **OCRService** - Text extraction from images/PDFs
- ✅ **NLPService** - Text preprocessing and normalization
- ✅ **SemanticAnalyzer** - Similarity calculation
- ✅ **ScoringService** - Keyword and overall scoring
- ✅ **ConceptGraphScorer** - Proposition extraction and matching
- ✅ **SentenceAlignmentScorer** - Sentence-level matching
- ✅ **StructuralAnalyzer** - Document structure evaluation
- ✅ **BloomTaxonomyScorer** - Cognitive level assessment
- ✅ **AntiGamingService** - Gaming pattern detection
- ✅ **ConfidenceService** - Reliability scoring
- ✅ **LayoutAnalysisService** - Document layout detection

### External APIs (if configured):
- ✅ **Sarvam AI** - Multilingual OCR (for PDFs & Hindi)
- ✅ **Google Cloud Vision** - High-accuracy OCR (optional)
- ✅ **OCR.space** - Free OCR fallback (optional)
- ✅ **Google Gemini/OpenAI** - Text correction (optional)

---

## 🎯 Decision Points in Flow

### 1. OCR Engine Selection
```
IF uploaded file is PDF:
    USE "sarvam" (forced for handwritten support)
ELSE IF user selected "ensemble":
    USE "ensemble" (all 3 engines in parallel)
ELSE:
    USE user's selected engine
```

### 2. Language Detection
```
IF filename contains language hint (e.g., "hindi", "tamil"):
    DETECT language from filename
ELSE:
    DEFAULT to "en" (English)
```

### 3. Optional Analysis
```
IF ENABLE_CONCEPT_GRAPH = True:
    PERFORM concept graph analysis
IF ENABLE_SENTENCE_ALIGNMENT = True:
    PERFORM sentence alignment analysis
IF ENABLE_STRUCTURAL_ANALYSIS = True:
    PERFORM structural analysis
```

### 4. Scoring Adjustment
```
IF anti_gaming_score > 30%:
    APPLY gaming penalty
IF bloom_level < expected_level:
    APPLY cognitive level penalty
IF bloom_level > expected_level:
    APPLY cognitive level bonus
IF structural_quality > threshold:
    APPLY structural bonus
```

---

## 📊 Scoring Weights (Configurable)

```python
# From config/settings.py
WEIGHT_SEMANTIC: float = 0.20           # 20% - Semantic similarity
WEIGHT_CONCEPT_GRAPH: float = 0.25      # 25% - Concept matching
WEIGHT_SENTENCE_ALIGNMENT: float = 0.25 # 25% - Sentence alignment
WEIGHT_KEYWORD: float = 0.15            # 15% - Keyword coverage
WEIGHT_DIAGRAM: float = 0.15            # 15% - Diagram analysis (if applicable)

STRUCTURAL_BONUS_CAP: float = 0.08      # Max 8% bonus for structure
BLOOM_MAX_PENALTY: float = 0.15         # Max 15% penalty for low cognitive level
BLOOM_MAX_BONUS: float = 0.05           # Max 5% bonus for high cognitive level
ANTI_GAMING_MAX_PENALTY: float = 0.40   # Max 40% penalty for gaming detection
```

---

## ✅ Quality Checks Throughout Flow

| Stage | Quality Check | Action if Failed |
|-------|---------------|-----------------|
| Extract | < 50 chars | Warn, continue |
| Normalize | No keywords | Warn, use text length |
| Semantic | Score < 0.3 | Warn, flag for review |
| Alignment | No matches | Warn, use semantic score |
| Confidence | < 0.5 | FLAG for manual review |
| Final | Score < 0.3 | FLAG for manual review |

---

## 🔐 Error Handling

### If OCR Fails:
```
Try Sarvam API Direct
    ↓ (Fails)
Try Google Vision API
    ↓ (Fails)
Try OCR.space API
    ↓ (Fails)
Try Sarvam PDF SDK
    ↓ (Fails)
Try Local EasyOCR (Always succeeds)
    ↓
Return extracted text or error message
```

### If Analysis Fails:
```
Semantic Analysis fails?
    → Use keyword score as fallback
Concept Graph fails?
    → Use semantic score as fallback
Sentence Alignment fails?
    → Use semantic score as fallback
Multiple failures?
    → Flag for manual review with confidence < 0.5
```

---

## 📌 Summary of Evaluation Flow

```
Upload Files
    ↓
Detect File Type (Image/PDF)
    ↓
Select OCR Engine (Auto for PDF)
    ↓
Extract Text (OCR)
    ↓
Preprocess Text (NLP)
    ↓
Analyze Semantics (Similarity)
    ↓
Analyze Keywords (Coverage)
    ↓
[Optional] Concept Graph
    ↓
[Optional] Sentence Alignment
    ↓
[Optional] Structural Analysis
    ↓
[Optional] Bloom's Taxonomy
    ↓
[Optional] Anti-Gaming Check
    ↓
Calculate Confidence Index
    ↓
Calculate Final Score
    ↓
Determine Grade
    ↓
Generate Recommendations
    ↓
Save Results
    ↓
Return to User
```

---

## Example: Complete Evaluation Scenario

### Scenario: Student Submits Hindi Handwritten PDF

**Input:**
- Model Answer: `model_hindi.pdf` (5 pages)
- Student Answer: `student_hindi_answer.pdf` (3 pages)
- Question Type: Descriptive
- Max Marks: 10
- Custom Keywords: ["फोटोसिंथेसिस", "क्लोरोफिल", "ऊर्जा"]

**Execution Timeline:**

1. **Upload** (2s)
   - Files validated and saved

2. **Detection** (1s)
   - PDFs detected → Force Sarvam AI

3. **Extraction** (45s)
   - Model: 5 pages × ~10s = 50s → 2567 chars
   - Student: 3 pages × ~12s = 36s → 1847 chars

4. **Preprocessing** (2s)
   - Normalize both texts
   - Extract keywords: Model [5], Student [4]

5. **Semantic** (3s)
   - Score: 0.78 (Good similarity)

6. **Keywords** (1s)
   - Matched: 3/5 = 0.60 (60%)

7. **Concept Graph** (5s)
   - Score: 0.68 (6/9 concepts matched)

8. **Sentence Alignment** (4s)
   - Score: 0.82 (Good alignment)

9. **Bloom's** (1s)
   - Expected: 5, Detected: 4 → Penalty: -1.5%

10. **Anti-Gaming** (1s)
    - No gaming detected

11. **Confidence** (1s)
    - 81% confidence (HIGH)

12. **Final Score** (1s)
    ```
    = (0.78×0.20) + (0.60×0.15) + (0.68×0.25) + (0.82×0.25) - 0.015
    = 0.156 + 0.09 + 0.17 + 0.205 - 0.015
    = 0.606 → 6.06 / 10 → GOOD ⭐⭐⭐⭐
    ```

13. **Result Saved** (1s)
    - Database updated
    - Files stored
    - Response sent

**Total Time: ~67 seconds**

**Result:**
```
Score: 6.06/10
Grade: GOOD
Confidence: 81% (HIGH)
Breakdown:
  - Semantic: 78%
  - Keywords: 60%
  - Concepts: 68%
  - Alignment: 82%
Recommendation: "Good understanding of concepts. Needs more examples."
```

---

This markdown document provides a complete overview of how the evaluation system works from start to finish!
