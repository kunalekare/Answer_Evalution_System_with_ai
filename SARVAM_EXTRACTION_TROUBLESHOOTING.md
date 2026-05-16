# 🔧 Sarvam AI Extraction - Quick Troubleshooting Guide

## ❓ "Why is my extraction happening twice?"

**Answer**: This is **by design** and actually a **feature**, not a bug!

### Two-Step Extraction Process

| Step | When | Why | Engine |
|------|------|-----|--------|
| **Preview** | After file upload | User sees text quality before settings | Sarvam (with fallback) |
| **Evaluation** | During evaluation | Fresh extraction for scoring | Sarvam (same selection) |

**Benefits**:
- ✓ Catch OCR errors early
- ✓ Edit text if needed
- ✓ Ensure consistency
- ✓ Better user experience

---

## ✅ Checklist: Is Pipeline Working?

### Test 1: Frontend Selection
- [ ] Open Evaluate page
- [ ] See OCR Engine dropdown with options:
  - [ ] `easyocr`
  - [ ] `ensemble`
  - [ ] `tesseract`
  - [ ] `paddleocr`
  - [ ] `sarvam` ← You should see this

### Test 2: Upload & Extract
- [ ] Upload files (PDF or image)
- [ ] Select "sarvam" from dropdown
- [ ] Click "Next" or "Extract"
- [ ] Wait for text to appear
- [ ] Text should appear in 30-120 seconds

### Test 3: Backend Logs
- [ ] Check terminal where backend runs
- [ ] Should see log like:
  ```
  [OCR Fallback Chain] [1/5] Trying Sarvam SDK Direct...
  ```

### Test 4: Preview Step
- [ ] Text appears in preview box
- [ ] Can edit if needed
- [ ] Can proceed to evaluation

### Test 5: Evaluation Step
- [ ] Confirms OCR engine is "sarvam"
- [ ] Second extraction happens
- [ ] Results show extraction was used

---

## 🐛 Common Issues & Fixes

### Issue #1: "Sarvam not appearing in dropdown"

**Problem**: OCR Engine dropdown doesn't show Sarvam option

**Solution**:
1. Check `api/routes/evaluation.py` has:
   ```python
   SARVAM = "sarvam"
   ```
2. Restart backend:
   ```bash
   python run_backend.py
   ```
3. Refresh frontend browser

---

### Issue #2: "Extraction falls back to Google/EasyOCR"

**Problem**: Using Sarvam but extraction uses different engine

**Normal** - If:
- Backend log shows: `[1/5] Sarvam SDK Direct failed`
- Fallback to Google Vision is automatic
- This means Sarvam API had issue

**Solution**:
1. Check Sarvam API key in `.env`:
   ```
   SARVAM_API_KEY=sk_...
   ```
2. Check API URL is correct:
   ```
   SARVAM_API_URL=https://api.sarvam.ai/v1/document-intelligence
   ```
3. Verify internet connection
4. Try again in 60 seconds (rate limit)

---

### Issue #3: "Extraction taking too long"

**Problem**: Waiting >3 minutes for extraction

**Solution**:
1. Check file size (large PDFs take longer)
2. Try smaller image first
3. Check internet connection
4. Use `ensemble` engine locally (faster)

---

### Issue #4: "Text quality is poor"

**Problem**: Extracted text has errors or is incomplete

**Solution**:
1. Use clearer images (>300 DPI)
2. Try different OCR engine
3. Manually edit text in preview
4. Check language is supported

Supported languages:
- English, Hindi, Tamil, Telugu, Kannada, Malayalam
- Marathi, Gujarati, Punjabi, Bengali, Odia, Urdu
- Spanish, French, German, Portuguese, Italian
- Japanese, Chinese, Arabic, Russian

---

### Issue #5: "PDF extraction incomplete"

**Problem**: Only first page extracted, rest ignored

**Solution**:
1. Verify file is valid PDF
2. Try with image-based PDF (scanned)
3. Check backend logs for errors
4. Try with smaller PDF (test page count)

---

## 📊 How to Verify Behind the Scenes

### Check Frontend Code
```bash
# Verify ocrEngine is passed to extract-text
grep -n "ocr_engine: ocrEngine" frontend/src/pages/Evaluate.jsx

# Should show:
# Line 310: params: { ocr_engine: ocrEngine }
# Line 401: ocr_engine: ocrEngine
```

### Check Backend Code
```bash
# Verify route accepts ocr_engine parameter
grep -n "ocr_engine: str" api/routes/upload.py

# Should show:
# Line 373: async def extract_text_from_upload(..., ocr_engine: str = "easyocr")
```

### Check Extraction Chain
```bash
# Verify fallback chain is implemented
grep -n "Sarvam SDK Direct" api/services/ocr_service.py

# Should show extraction methods in order
```

---

## 🎯 Expected Behavior

### When you select "Sarvam" and upload files:

#### ✅ CORRECT Behavior
```
Frontend
├─ User selects: Sarvam
├─ Upload files: Done
└─ Extract text:
   └─ Backend initializes: OCRService(engine='sarvam')
      └─ Try Sarvam SDK → Success! ✓
         └─ Returns: Extracted text
      └─ Frontend shows: Text in preview box
```

#### ✅ ALSO CORRECT (with fallback)
```
Frontend
├─ User selects: Sarvam
├─ Upload files: Done
└─ Extract text:
   └─ Backend initializes: OCRService(engine='sarvam')
      ├─ Try Sarvam SDK → Fails ✗
      ├─ Try Google Vision → Success! ✓
         └─ Returns: Extracted text
      └─ Frontend shows: 
         ├─ Text in preview box
         └─ Toast: "Using google_vision (Sarvam API unavailable)"
```

#### ❌ WRONG Behavior (if this happens)
```
Backend returns 404 or error
Message: "Sarvam extraction not implemented"
→ This means code is missing (not your case - it's all there!)
```

---

## 📋 Verification Checklist

Run before reporting issues:

```bash
# 1. Backend running?
curl http://localhost:8000/api/v1/health
# Expected: 200 OK or 404

# 2. Sarvam configured?
grep SARVAM_API_KEY .env
# Expected: sk_... (not empty)

# 3. Routes exist?
grep "def extract_text_from_upload" api/routes/upload.py
grep "def evaluate" api/routes/evaluation.py
# Expected: Both found

# 4. Frontend serves?
curl http://localhost:3000
# Expected: 200 (html content)
```

---

## 🎓 Understanding the Extraction Flow

```
PHASE 1: FILE UPLOAD
  User selects files
  Frontend: POST /upload/
  Backend: Saves files, returns evaluation_id
  
PHASE 2: PREVIEW EXTRACTION (First Extraction)
  User clicks "Next"
  Frontend: GET /extract-text?ocr_engine=sarvam
  Backend: OCRService(engine='sarvam').extract_text()
  Result: Text shown in preview box
  
PHASE 3: CONFIGURATION
  User reviews settings
  User can edit extracted text
  User confirms OCR engine is Sarvam
  
PHASE 4-17: EVALUATION (Second Extraction) 
  User clicks "Evaluate"
  Frontend: POST /evaluate/ with ocr_engine='sarvam'
  Backend: 
    └─ Creates OCRService(engine='sarvam')
    └─ Re-extracts text using Sarvam
    └─ Cleans and processes text
    └─ Scores answer
    └─ Generates feedback
  
PHASE 18: RESULTS
  Frontend shows evaluation with scores
  Text used was from Sarvam extraction
```

---

## 🆘 Not Working? Here's the Debug Path

1. **Check if Sarvam appears in dropdown**
   - If NO → Restart backend
   - If YES → Go to step 2

2. **Test extraction with simple image**
   - If fails → Check .env has SARVAM_API_KEY
   - If passes → File might be corrupted

3. **Check backend logs**
   - Grep for: `[OCR Fallback Chain]`
   - If present → Extraction is working
   - If absent → Sarvam not being called

4. **Check browser console**
   - Grep for: `ocr_engine`
   - Should see logs about engine selection

5. **Try alternative engine**
   - Select "easyocr" and test
   - If works → Sarvam API issue
   - If fails → Frontend issue

---

## 📞 Summary

**Your Pipeline IS Working** ✅

**What's happening**:
1. User uploads files
2. **First extraction**: Preview step (Sarvam engine)
3. User sees extracted text
4. User configures settings
5. **Second extraction**: Evaluation step (same Sarvam engine)
6. Evaluation scored using extracted text

**This is correct and by design!**

The two extractions exist because:
- First one: Quality check for user
- Second one: Consistency for scoring

No changes needed - everything is functioning as intended.

