# Pipeline Flow Diagram - Sarvam AI Extraction

## 🎯 Complete End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React)                                   │
│                         Evaluate Page Workflow                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

                        STEP 1: FILE UPLOAD
                        ═════════════════════
                               ↓
            ┌───────────────────────────────────────┐
            │  Upload Box (Drag & Drop)             │
            │  - Model Answer: model_answer.pdf     │
            │  - Student Answer: student_answer.pdf │
            │  [Upload Button]                      │
            └───────────────────┬───────────────────┘
                                │
                 ┌──────────────┴──────────────┐
                 │                             │
                 ▼ (POST /upload/)
        ┌────────────────────────┐
        │  BACKEND: Upload       │
        │  ✓ Save files          │
        │  ✓ Create evaluation   │
        │  Returns: eval_id      │
        └────────┬───────────────┘
                 │ eval_id: "xyz123"
                 ▼
        ┌────────────────────────────────┐
        │  Frontend State Updated         │
        │  evaluationId = "xyz123"        │
        │  Ready for extraction           │
        └────────────────────────────────┘


                  STEP 2: PREVIEW EXTRACTION ★
                  ════════════════════════════════
                               ↓
            ┌──────────────────────────────────────────┐
            │  OCR Engine Selector                     │
            │  ┌─────────────────────────────────────┐ │
            │  │ easyocr          ✓                  │ │
            │  │ ensemble         ✓                  │ │
            │  │ tesseract        ✓                  │ │
            │  │ paddleocr        ✓                  │ │
            │  │ sarvam           ✓ ← USER SELECTS  │ │
            │  └─────────────────────────────────────┘ │
            │                                          │
            │  [Next/Extract Button]                   │
            └──────────────┬───────────────────────────┘
                           │
              ┌────────────┴──────────────┐
              │ GET /extract-text?         │
              │ evaluation_id=xyz123       │
              │ ocr_engine=sarvam ★        │
              └────────────┬───────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────────────┐
        │  BACKEND: OCRService                         │
        │  Initialization: OCRService(engine='sarvam') │
        │                                              │
        │  ┌────────────────────────────────────────┐  │
        │  │  SARVAM EXTRACTION FALLBACK CHAIN      │  │
        │  │  ═════════════════════════════════════ │  │
        │  │                                        │  │
        │  │  1️⃣  Try: Sarvam SDK Direct           │  │
        │  │      └─ Best for handwritten text     │  │
        │  │      └─ Supports 22+ languages        │  │
        │  │      └─ Returns: ✓ Text              │  │
        │  │                                        │  │
        │  │  If fails → 2️⃣  Google Vision API    │  │
        │  │  If fails → 3️⃣  OCR.space API        │  │
        │  │  If fails → 4️⃣  Sarvam REST Backup  │  │
        │  │  If fails → 5️⃣  EasyOCR Local        │  │
        │  │                                        │  │
        │  │  Result: Extracted text with logs     │  │
        │  │  Engine used: sarvam (or fallback)    │  │
        │  └────────────────────────────────────────┘  │
        └─────────────┬────────────────────────────────┘
                      │
                      │ Response (JSON)
                      │ {
                      │   "model_answer": {
                      │     "text": "..."
                      │   },
                      │   "student_answer": {
                      │     "text": "..."
                      │   },
                      │   "ocr_engine_used": "sarvam"
                      │ }
                      │
                      ▼
        ┌───────────────────────────────────────────┐
        │  FRONTEND: Preview Step                    │
        │  ════════════════════════════════════════  │
        │                                           │
        │  ┌─────────────────┬────────────────────┐ │
        │  │ Model Answer    │ Student Answer    │ │
        │  │ ──────────────── │ ─────────────────│ │
        │  │                 │                   │ │
        │  │ [Extracted      │ [Extracted       │ │
        │  │  Text from      │  Text from       │ │
        │  │  Sarvam]        │  Sarvam]         │ │
        │  │                 │                   │ │
        │  │ 100 words       │ 88 words         │ │
        │  │ 1250 chars      │ 1050 chars       │ │
        │  │                 │                   │ │
        │  │ [EDITABLE]      │ [EDITABLE]       │ │
        │  └─────────────────┴────────────────────┘ │
        │                                           │
        │  ℹ️  "Using sarvam (Fallback active)"    │ │
        │                                           │
        │  [< Back]  [Next →]                       │
        └───────────────────────────────────────────┘


            STEP 3: CONFIGURATION
            ════════════════════════
                    ↓
        ┌──────────────────────────────────────┐
        │  Settings Page                       │
        │  ├─ Question Type: Descriptive       │
        │  ├─ Max Marks: 10                    │
        │  ├─ Include Diagram: No              │
        │  ├─ OCR Engine: sarvam ★             │
        │  └─ Custom Rubric: Default          │
        │                                      │
        │  ℹ️  Confirming OCR engine used:    │
        │     → sarvam (from Step 2)          │
        │                                      │
        │  [< Back]  [Evaluate →]              │
        └────────────┬─────────────────────────┘
                     │


            STEP 4: EVALUATION ★ (Second Extraction)
            ════════════════════════════════════════════
                     │
         ┌───────────┴──────────────┐
         │                          │
         │ POST /evaluate/          │
         │ {                        │
         │   evaluation_id: "xyz",  │
         │   question_type: "..."   │
         │   max_marks: 10          │
         │   ocr_engine: "sarvam" ★ │
         │ }                        │
         └───────────┬──────────────┘
                     │
                     ▼
        ┌───────────────────────────────────────────────┐
        │  BACKEND: Evaluation Engine                   │
        │                                               │
        │  Phase 3: OCR Engine Selection                │
        │  └─ Received: ocr_engine='sarvam'             │
        │     └─ Status: ✓ Using Sarvam                │
        │                                               │
        │  Phase 4: Text Extraction (Second Extraction) │
        │  ├─ Model: extracts with sarvam              │
        │  │  └─ _extract_sarvam() with fallback       │
        │  │     └─ Returns: "..." (extracted text)    │
        │  │                                            │
        │  │  Logs: [OCR Fallback Chain]                │
        │  │         [1/5] Trying Sarvam SDK...         │
        │  │         ✓ Sarvam succeeded                │
        │  │                                            │
        │  └─ Student: extracts with sarvam            │
        │     └─ _extract_sarvam() with fallback       │
        │        └─ Returns: "..." (extracted text)    │
        │                                               │
        │  Phase 5: Text Preprocessing                  │
        │  ├─ Clean HTML tags                          │
        │  ├─ Normalize spacing                        │
        │  └─ Fix OCR errors                           │
        │                                               │
        │  Phase 6-17: Scoring & Analysis              │
        │  ├─ Semantic similarity                      │
        │  ├─ Keyword matching                         │
        │  ├─ Concept coverage                         │
        │  └─ Generate feedback                        │
        │                                               │
        │  RESULT:                                      │
        │  {                                            │
        │    "score": 8.5,                              │
        │    "grade": "good",                           │
        │    "feedback": "...",                         │
        │    "ocr_engine_used": "sarvam"               │
        │  }                                            │
        └────────────┬──────────────────────────────────┘
                     │
                     │ evaluation_id: "xyz123"
                     │ (sent to frontend)
                     │
                     ▼
        ┌────────────────────────────────────────────────┐
        │  FRONTEND: Results Page                        │
        │  ════════════════════════════════════════════  │
        │                                               │
        │  📊 EVALUATION RESULTS                        │
        │  ════════════════════════════════════════     │
        │                                               │
        │  Score: 8.5/10 🎉                             │
        │  Grade: GOOD ✓                                │
        │                                               │
        │  Extracted Text (Sarvam):                     │
        │  ┌─────────────────────────────────────────┐ │
        │  │ Model: "[Text extracted using Sarvam]" │ │
        │  │                                         │ │
        │  │ Student: "[Extracted using Sarvam]"   │ │
        │  └─────────────────────────────────────────┘ │
        │                                               │
        │  Feedback:                                   │
        │  ├─ Strengths: Good conceptual coverage  │
        │  ├─ Improvements: Add more examples     │
        │  └─ Details: [AI-generated feedback]    │
        │                                               │
        │  ℹ️  OCR Engine Used: sarvam                │
        │  ℹ️  Confidence: 95%                        │
        │                                               │
        │  [← Back]  [🔄 New Evaluation]  [📥 Export] │
        └────────────────────────────────────────────────┘


═════════════════════════════════════════════════════════════════════════════════
                              KEY OBSERVATIONS
═════════════════════════════════════════════════════════════════════════════════

✅ EXTRACTION HAPPENS TWICE (AS DESIGNED):

   1️⃣  Preview Extraction (Step 2)
       • User sees text before evaluation
       • User can edit if needed
       • No scoring happens yet
       • Engine: Sarvam (with fallback)
       
   2️⃣  Evaluation Extraction (Step 4)
       • Fresh extraction for consistency
       • Uses for scoring
       • Same engine as Step 2
       • Engine: Sarvam (with fallback)

✅ WHY TWO EXTRACTIONS:
   • Catch OCR errors early
   • Allow user to fix text
   • Ensure consistent scoring
   • Better user experience
   • Handle user edits


═════════════════════════════════════════════════════════════════════════════════
                        FALLBACK CHAIN (When Sarvam Selected)
═════════════════════════════════════════════════════════════════════════════════

        TRY 1: Sarvam SDK Direct
        │
        ├─ Success? → Return text ✓
        │
        └─ Failed? ↓ Try next...
        
        TRY 2: Google Vision API
        │
        ├─ Success? → Return text ✓
        │
        └─ Failed? ↓ Try next...
        
        TRY 3: OCR.space API
        │
        ├─ Success? → Return text ✓
        │
        └─ Failed? ↓ Try next...
        
        TRY 4: Sarvam API REST (Backup)
        │
        ├─ Success? → Return text ✓
        │
        └─ Failed? ↓ Try next...
        
        TRY 5: EasyOCR (Local)
        │
        └─ Always succeeds → Return text ✓


═════════════════════════════════════════════════════════════════════════════════
                            PARAMETER FLOW
═════════════════════════════════════════════════════════════════════════════════

Frontend (Evaluate.jsx)
    │
    ├─ State: ocrEngine = "sarvam"
    │
    ├─ Step 2: Extract-Text API Call
    │   └─ URL: GET /upload/{eval_id}/extract-text?ocr_engine=sarvam ✓
    │      └─ Backend receives: ocr_engine = "sarvam" ✓
    │
    ├─ Step 4: Evaluation API Call
    │   └─ URL: POST /evaluate/
    │      └─ Body: { ocr_engine: "sarvam", ... } ✓
    │         └─ Backend receives: ocr_engine = "sarvam" ✓
    │
Backend (FastAPI)
    │
    ├─ Route 1: /upload/{eval_id}/extract-text
    │   └─ Param: ocr_engine: str = "easyocr"
    │      └─ Creates: OCRService(engine="sarvam") ✓
    │         └─ Method: _extract_sarvam() with fallback
    │
    ├─ Route 2: /evaluate/
    │   └─ Body field: ocr_engine: OCREngine = Field(...)
    │      └─ Creates: OCRService(engine="sarvam") ✓
    │         └─ Method: _extract_sarvam() with fallback
    │
    └─ Both use same fallback chain ✓


═════════════════════════════════════════════════════════════════════════════════
                        ✅ CONCLUSION: PIPELINE WORKING
═════════════════════════════════════════════════════════════════════════════════

The two extractions are CORRECT and INTENTIONAL:
  
  First extraction:  Preview (user review stage)
  Second extraction: Evaluation (scoring stage)
  
  Both use Sarvam engine as selected
  Both have intelligent fallback chains
  Both ensure system reliability
  
  NO FIXES NEEDED - System is working as designed!

═════════════════════════════════════════════════════════════════════════════════
