# Question-Wise Evaluation - Visual Guide & Examples

## Architecture Overview

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                    PAPEREVAL SYSTEM                        ┃
┃           Question-Wise Evaluation Architecture            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React/MUI)                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Upload UI   │  │  Preview UI  │  │  Settings UI │      │
│  │              │  │   (Step 2)   │  │  (Step 3)    │      │
│  │ • Drag drop  │  │              │  │ ┌───────────┐│      │
│  │ • File input │  │ • Shows      │  │ │Overall    ││      │
│  │              │  │   cleaned    │  │ │Evaluation ││      │
│  └──────┬───────┘  │   text       │  │ └─────↑─────┘│      │
│         │          │              │  │ ┌─────↓─────┐│      │
│         │          │ Quality      │  │ │Question   ││  ← YOU CLICK HERE
│         │          │ Feedback     │  │ │Wise Eval  ││      │
│         │          │              │  │ └───────────┘│      │
│         │          └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           │                                  │
│      questionSegmentation.js utils                          │
│      • extractQuestions()                                   │
│      • analyzeQuestionStructure()                           │
│                                                              │
│      Results.jsx Component                                  │
│      • Displays per_question array                          │
│      • Shows per-question scores                            │
│                                                              │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ↓
                    API: /api/v1/upload/
                    API: /api/v1/evaluate/
                    API: /api/v1/results/
                               │
┌──────────────────────────────↓───────────────────────────────┐
│                    BACKEND (FastAPI/Python)                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Upload Handler                                            │
│  ├─ Receive files                                          │
│  ├─ Validate                                               │
│  └─ Save to disk                                           │
│        │                                                    │
│        ↓                                                    │
│  OCR Service                                               │
│  ├─ Engine: EasyOCR/Ensemble/Tesseract/Sarvam            │
│  ├─ Extract text                                           │
│  └─ Performance: 5-12 sec per image                       │
│        │                                                    │
│        ↓                                                    │
│  TextCleaningService ← NEW                                │
│  ├─ Remove OCR artifacts (~~~ removed)                    │
│  ├─ Fix 30+ common errors (vvord → word)                 │
│  ├─ Normalize whitespace                                  │
│  ├─ Preserve question structure                           │
│  └─ Quality score (0-1)                                   │
│        │                                                    │
│        ↓                                                    │
│  Cache Manager                                            │
│  ├─ Store cleaned text                                   │
│  └─ Reuse on preview/eval                                │
│        │                                                    │
│        ↓  ┌─────────────────────────────────┐             │
│  Question Segmentation Service             │             │
│  ├─ Detect: Q1. 1. Question 1 Ans 1       │             │
│  ├─ Match model ↔ student questions       │             │
│  ├─ Extract sub-parts (a) (b) (i) (ii)   │             │
│  └─ Confidence score                      │             │
│        │                                  │              │
│        ↓                                  │              │
│  Evaluation Service                       │ IF QUESTION-│
│  ├─ For each question:                  │ WISE MODE   │
│  ├─ Semantic scoring                    │             │
│  ├─ Keyword coverage                    │             │
│  ├─ Concept graph analysis              │             │
│  ├─ Rubric scoring                      │             │
│  └─ Per-question feedback               │             │
│        │                                 └─────────────┘
│        ↓
│  Results Formatter
│  ├─ Overall score
│  ├─ Per-question breakdown
│  ├─ Explanations
│  └─ Suggestions
│
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ↓
                      Database / File Storage
                      ├─ Evaluations
                      ├─ Results
                      └─ Cache (.cache/)
```

---

## Data Flow Example

### Example: Physics Question Paper

**INPUT:**
```
Model Answer PDF (2 pages):
─────────────────────────────
Q1. Explain pressure in fluids
A: Pressure is force per unit area...

Q2. Define velocity
A: Velocity is rate of change of position...

Student Answer PDF (3 pages):
─────────────────────────────
Q1. What is pressure?
A: Pressure is a force...

Q2. What is velocity?
A: Velocity is speed in a direction...
```

**PROCESSING:**

```
Stage 1: OCR Extraction (5-12 sec)
┌────────────────────────────────────────┐
│ Using: EasyOCR Engine                  │
│ Raw output (with artifacts):           │
│ "Q1. Exp|a|n pressure in f|~u|ids      │
│  Pressure is force..." (messy)         │
└────────────────────────────────────────┘
                 ↓
Stage 2: Text Cleaning (50-100ms)
┌────────────────────────────────────────┐
│ TextCleaningService.clean_text():      │
│ • Fix: "|" → "", "~" → removed         │
│ • Output (clean):                      │
│ "Q1. Explain pressure in fluids        │
│  Pressure is force per unit area..."   │
│ Quality Score: 0.92 (Good!)            │
└────────────────────────────────────────┘
                 ↓
Stage 3: Question Segmentation (10-20ms)
┌────────────────────────────────────────┐
│ segment_text():                        │
│ Segments: [                            │
│   {number: 1, label: "Q1.", ...},     │
│   {number: 2, label: "Q2.", ...}      │
│ ]                                      │
│ Confidence: 0.95 (Very High!)         │
└────────────────────────────────────────┘
                 ↓
Stage 4: Cache Storage (instant)
┌────────────────────────────────────────┐
│ .cache/model_extracted.txt (clean)    │
│ .cache/student_extracted.txt (clean)  │
│ Ready for evaluation & preview         │
└────────────────────────────────────────┘
                 ↓
Stage 5: Evaluation (30-60 sec/question)
┌────────────────────────────────────────┐
│ For Q1 (Pressure):                    │
│ ├─ Semantic: 0.92 (student ans        │
│ │           matches model)            │
│ ├─ Keywords: 0.88 (covered most)      │
│ ├─ Concepts: 0.85 (force, area)       │
│ └─ Final: 9.2/10 (92%)                │
│                                        │
│ For Q2 (Velocity):                    │
│ ├─ Semantic: 0.88                     │
│ ├─ Keywords: 0.85                     │
│ ├─ Concepts: 0.80                     │
│ └─ Final: 8.4/10 (84%)                │
└────────────────────────────────────────┘
                 ↓
Stage 6: Results Display
┌────────────────────────────────────────┐
│ QUESTION-WISE EVALUATION REPORT        │
│ ════════════════════════════════════   │
│ Overall Score: 88%                    │
│                                        │
│ Q1. Pressure: 92% (Excellent) ⭐⭐⭐⭐⭐  │
│    Marks: 9.2/10                      │
│    Feedback: Excellent explanation    │
│                                        │
│ Q2. Velocity: 84% (Good) ⭐⭐⭐⭐       │
│    Marks: 8.4/10                      │
│    Feedback: Good, but could add...   │
└────────────────────────────────────────┘
```

---

## UI Examples

### Step 3: Configure Settings - Mode Selection

```
═══════════════════════════════════════════════════════════════
          📋 Evaluation Mode
───────────────────────────────────────────────────────────────
Choose how you want your answer to be evaluated:

┌───────────────────┐     ┌───────────────────┐
│  📝 Overall       │     │  ❓ Question Wise │
│  Evaluation       │     │  Evaluate         │
├───────────────────┤     ├───────────────────┤
│ Evaluate the      │     │ Evaluate each     │
│ complete answer   │     │ question          │
│ as a single unit  │     │ separately        │
│                   │     │                   │
│ Best for:         │     │ Best for:         │
│ • Single Qs       │     │ • Multiple Qs     │
│ • Essays          │     │ • Worksheets      │
│ • Overall score   │     │ • Per-Q scores    │
│                   │     │                   │
│  [Unselected]     │     │  [✓ Selected]     │  ← YOU CLICK HERE
└───────────────────┘     └───────────────────┘

💡 Tip: Number each question (Q1., Q2., etc.)
───────────────────────────────────────────────────────────────
```

### Results Page - Question-Wise Display

```
QUESTION-WISE ANSWER EVALUATION REPORT
═══════════════════════════════════════════════════════════════

Student: Alex Johnson | Date: October 26, 2023 | Physics
Overall Score: 88%  ┌─────────┐
                    │ Excellent
                    │   Good   │
                    │ Average  │
                    └─────────┘

═══════════════════════════════════════════════════════════════

[Q1]  [Q2]  [Q3]  [Q4]   ← Question Map
90%   75%   100%  81%

═══════════════════════════════════════════════════════════════

▼ Q1. ESSAY: Explain the Concept of Pressure         [9/10]

    ╔════════════════════════════════════════════════════╗
    ║ Clarity:      ⭐⭐⭐⭐⭐  | Accuracy:    ⭐⭐⭐⭐⭐  ║
    ║ Evidence:     ⭐⭐⭐⭐   | Structure:   ⭐⭐⭐⭐⭐  ║
    ╚════════════════════════════════════════════════════╝

    Score Breakdown:
    ├─ Semantic Similarity   ████████████████████ 92%
    ├─ Keyword Coverage      ████████████████░░░░ 88%
    ├─ Concept Analysis      █████████████████░░░ 85%
    └─ Final Score: 9.0/10 (90%)

    💬 Comment:
    "Excellent! Your answer shows clear understanding of
     pressure. You correctly defined it as force per unit
     area and provided good examples."

    ✓ Concepts Covered (85%):
      • Pressure definition  • Force concept  • Area concept
      • SI units

    ✗ Concepts Missing (15%):
      • Pressure in liquids  • Pascal's principle

    💡 Suggestions:
      • Mention pressure in different states of matter
      • Add more real-world applications

───────────────────────────────────────────────────────────

▼ Q2. SHORT ANSWER: Define Velocity              [7/10]

    [Similar accordion format with 75% score]

───────────────────────────────────────────────────────────

▼ Q3. DIAGRAM: Draw & Label Pressure Vessel      [10/10]

    [Similar accordion format with 100% score]

───────────────────────────────────────────────────────────

▼ Q4. INTERPRETATION: Analyze Reynolds Number   [8.1/10]

    [Similar accordion format with 81% score]

═══════════════════════════════════════════════════════════════
```

---

## Text Cleaning Examples

### Before & After

```
BEFORE (Raw OCR Output - Messy):
────────────────────────────────────────────────────────
Q1. Exp|a|n pressure in f|~u|ids
Pressure is force per un|t area.
1t can be...
tlie student learns...
vvord "Pascal's" describes......

AFTER (Cleaned):
────────────────────────────────────────────────────────
Q1. Explain pressure in fluids
Pressure is force per unit area.
It can be...
the student learns...
word "Pascal's" describes...

Issues Fixed:
✓ Removed OCR noise: | ~ removed
✓ Fixed errors: "1" → "I", "tlie" → "the", "vvord" → "word"
✓ Normalized spacing
✓ Preserved structure

Quality Score: 0.92 (Good!)
────────────────────────────────────────────────────────
```

---

## Question Extraction Example

### Input Text:
```
Q1. What is pressure?
Pressure is the force applied perpendicular to the surface per unit area.
It is measured in Pascals.

Q2. Define velocity
Velocity is the rate of change of position with respect to time.
It is a vector quantity.

(a) What is the SI unit of velocity?
The SI unit of velocity is meter per second (m/s).
```

### Extracted Questions:
```
[
  {
    number: 1,
    header: "Q1. What is pressure?",
    content: "Pressure is the force applied... measured in Pascals.",
    type: "main_question"
  },
  {
    number: 2,
    header: "Q2. Define velocity",
    content: "Velocity is the rate of change... vector quantity.",
    type: "main_question"
  },
  {
    number: 2.1,
    header: "(a) What is the SI unit of velocity?",
    content: "The SI unit... m/s.",
    type: "sub_part"
  }
]
```

---

## Quality Score Interpretation

```
Quality Score Scale:
═══════════════════════════════════════════

1.0 ███████████████████████████  Perfect
    └─ No errors, perfect segmentation

0.9 ██████████████████████░░░░░░░ Excellent
    └─ Minimal noise, clear questions

0.8 ███████████████████░░░░░░░░░░ Good
    └─ Some noise, manageable

0.7 ██████████████░░░░░░░░░░░░░░░ Fair
    └─ Moderate noise, needs review
    👆 THRESHOLD - Acceptable quality

0.5 ███████░░░░░░░░░░░░░░░░░░░░░░ Poor
    └─ Significant errors, manual review needed

0.3 ████░░░░░░░░░░░░░░░░░░░░░░░░░ Very Poor
    └─ Many artifacts, consider retake

0.0 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ Failed
    └─ Complete failure, re-upload required

Recommendation:
─────────────────────────────
< 0.5 → Try another OCR engine or use text input mode
0.5-0.7 → Acceptable but may need review
> 0.7 → Good! Proceed with evaluation
```

---

## OCR Engine Selection Guide

```
Your Image Type         Recommended Engine      Time    Accuracy
─────────────────────────────────────────────────────────────────
Handwritten (messy)  →  Ensemble               12s     95%
                        (or Sarvam AI)

Handwritten (neat)   →  EasyOCR                5s      85%

Printed text         →  PaddleOCR              8s      90%

Mixed (text+diagram) →  Ensemble               12s     95%

Faded/low contrast   →  Ensemble + Sarvam      12s     95%
                        (try both)

Speed critical       →  Tesseract               3s      75%

Online (no GPU)      →  Sarvam AI Cloud        vary    90%+

Budget constraint    →  EasyOCR (default)      5s      85%

Best quality         →  Ensemble               12s     95%
────────────────────────────────────────────────────────────────
```

---

## Common Scenarios

### Scenario 1: Perfect Case
```
Input: Clear PDF, 4 questions, neat handwriting
OCR Engine: EasyOCR
Quality Score: 0.95
Questions Detected: 4 (100% match)
Time: 5 seconds
Result: ✅ Excellent - Ready for evaluation
```

### Scenario 2: Challenging Case
```
Input: Faded photocopy, handwritten, 6 questions
OCR Engine: Ensemble (auto-switched from EasyOCR)
Quality Score: 0.82
Questions Detected: 6 (100% match)
Time: 12 seconds
Result: ✅ Good - Minor cleaning but acceptable
```

### Scenario 3: Poor Case
```
Input: Very faded, poor scan, 3 questions mixed
OCR Engine: Multiple tried, all poor
Quality Score: 0.45
Questions Detected: Unclear
Time: Various
Result: ⚠️ Recommend text input mode instead
```

---

## Integration Points

```
Frontend Components              Backend Services
──────────────────              ────────────────

Evaluate.jsx          ←→         upload.py
├─ File upload UI                ├─ File validation
├─ Question mode btn             ├─ OCR extraction
└─ Submit evaluation             └─ Text cleaning

Preview Step          ←→         extract-text API
├─ Show text                     ├─ Load from cache
└─ Quality feedback              └─ Quality score

Results.jsx           ←→         evaluation.py
├─ Per-question cards            ├─ Semantic scoring
├─ Rubric display                ├─ Keyword analysis
└─ Suggestions                   └─ Per-question results

questionSegmentation  ←→         question_segmentation
utility.js                       service.py
├─ Client-side parse             ├─ Backend segment
├─ Structure analysis            └─ Detection methods
└─ Quality hints

TextCleaning          ←→         text_cleaning_service
(logs only)                      ├─ Error fixes
                                 ├─ Noise removal
                                 └─ Quality scoring
```

---

## Performance Metrics Dashboard

```
Typical Evaluation Performance (4-Question Paper):
═══════════════════════════════════════════════════════

Timings:
 Upload               [▓▓░░░░░░░░░░░░░░░░]  2-3 sec
 OCR Extraction       [▓▓▓▓▓░░░░░░░░░░░░░]  5-12 sec
 Text Cleaning        [▓░░░░░░░░░░░░░░░░░]  0.1 sec
 Segmentation         [▓░░░░░░░░░░░░░░░░░]  0.01 sec
 Question Eval (×4)   [▓▓▓▓▓▓▓░░░░░░░░░░░]  120-240 sec
                      ────────────────────
 Total:               [▓▓▓▓▓▓▓▓░░░░░░░░░░░]  2-4 min

Quality Metrics:
 Extraction Quality   [████████░░░] 92%
 Segmentation Match   [████████░░░] 95%
 Field Coverage       [███████░░░░]  85%
 Final Accuracy       [████████░░░] 88%
═══════════════════════════════════════════════════════
```

---

This visual guide helps understand:
✅ System architecture
✅ Data flow through the system
✅ UI/UX layouts
✅ Text cleaning before/after
✅ Question extraction process
✅ OCR engine selection
✅ Performance metrics
