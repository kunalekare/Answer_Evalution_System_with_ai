# TESTING & TROUBLESHOOTING GUIDE
## Sarvam AI Integration & Evaluation System

### ⚡ QUICK START: How to Test Everything

#### 1. **Install Dependencies**
```bash
pip install -r requirements.txt --upgrade
pip install sarvambot  # Possible Sarvam package name (if available)
```

#### 2. **Start the Backend**
```bash
python api/main.py
# Server will run at http://127.0.0.1:8000
# API documentation: http://127.0.0.1:8000/docs
```

#### 3. **Start the Frontend**
```bash
cd frontend
npm install  # First time only
npm start
# Frontend will open at http://127.0.0.1:3000
```

#### 4. **Test Modes**

##### Mode A: Text Input (Fastest - 60-120s)
1. Go to **Evaluate Answer** page
2. Toggle ON: "Use text input instead of file upload"
3. **Select OCR Engine**: Choose any engine (EasyOCR recommended for testing)
4. Enter Model Answer & Student Answer (min 10 chars each)
5. Click **Configure Settings** → Configure rubric if needed
6. Click **Evaluate** and WAIT (60-120 seconds for full pipeline)

##### Mode B: File Upload (Slower - 120-180s)
1. Go to **Evaluate Answer** page
2. Toggle OFF: "Use text input instead of file upload"
3. **Select OCR Engine**: Try different engines:
   - `easyocr` (balanced, 5s extraction)
   - `tesseract` (fast, 3s extraction)
   - `ensemble` (best accuracy, 12s extraction)
   - `sarvam` (cloud, 2-5s extraction + network)
   - `paddleocr` (layouts, 8s extraction)
4. Upload student & model answers (images or PDF)
5. **Next** → Wait for text extraction (5-15s)
6. Review extracted text and correct if needed
7. Click **Evaluate** and WAIT (60-120s)

---

### 🔴 Known Issues & Fixes

#### Issue 1: Evaluation Takes 60-120 Seconds ⏱️
**Cause**: Sentence Transformers models load on first request (~30s)

**Why This Happens**:
- Semantic similarity uses `all-MiniLM-L6-v2` model
- Concept graph uses BERT models
- Models initialize on-demand (lazy loading)
- Sequential processing (not parallel)

**Current Workaround**: 
- First request: 60-120s (first load)
- Subsequent requests: 10-30s (cached models)
- Use this time to review extracted text

**Future Optimization**:
```python
# Planned: Initialize models at startup
from api.services.semantic_service import SemanticAnalyzer
semantic = SemanticAnalyzer()  # During app startup, not per-request
```

#### Issue 2: 422 Unprocessable Content Error
**Root Cause**: HTTP timeout too short for long-running evaluations

**Fix Applied**: 
- Backend timeout increased to 120s in `api/main.py`
- Frontend timeout increased to 120s in `api.js`
- Backend now documents expected processing time

**Test the Fix**:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/evaluate/text \
  -H "Content-Type: application/json" \
  -d '{
    "model_answer": "The photosynthesis process...",
    "student_answer": "Photosynthesis is when plants...",
    "question_type": "descriptive",
    "max_marks": 10,
    "ocr_engine": "easyocr"
  }' \
  --max-time 120
```

#### Issue 3: PyMuPDF Import Error
**Status**: ✅ FIXED

**Solution**: PyMuPDF added to requirements.txt
```bash
pip install PyMuPDF>=1.23.0
```

#### Issue 4: Sarvam AI Package Not Found
**Status**: ⚠️ BLOCKED - Package name mismatch

**What We Know**:
- Sarvam has a Python SDK, but PyPI package name is unclear
- sarvam-ai is NOT available on PyPI
- Alternatives:
  - `pip install sarvambot` (if available)
  - Use HTTP API directly (no SDK needed)
  - Contact Sarvam for official Python SDK

**Workaround**: Use HTTP API call instead
```python
import requests
response = requests.post(
    'https://api.sarvam.ai/v1/document-intelligence',
    headers={'Authorization': f'Bearer {SARVAM_API_KEY}'},
    files={'file': open('document.pdf', 'rb')}
)
```

---

### 🧪 Unit Tests

#### Test 1: Pydantic Model Validation
```bash
python test_quick_eval.py
# Output: ✅ TextEvaluationRequest model validation PASSED
```

#### Test 2: Direct Evaluation (No API)
```bash
python test_quick_eval.py
# Output: ✅ Evaluation completed in 77.95s (first load)
# Subsequent calls: ~10-30s (cached models)
```

#### Test 3: Full API Integration
```bash
# Start backend first: python api/main.py

# Then run diagnostics
python test_sarvam_and_api.py
```

#### Test 4: Multi-Question Evaluation
```python
# frontend/src/services/api.js
const result = await evaluateMultiQuestion({
  model_answer: "Question 1: Answer A\nQuestion 2: Answer B",
  student_answer: "Question 1: Student A\nQuestion 2: Student B",
  question_type: 'mixed',
  total_max_marks: 20,
  ocr_engine: 'easyocr'
});
```

---

### 📊 Expected Performance

#### Response Times by Mode

| Mode | First Request | Cached | OCR Time | Evaluation Time | Total |
|------|---|---|---|---|---|
| Text Direct | 80-120s | 10-30s | N/A | 60-90s | 80-120s |
| File (EasyOCR) | 100-150s | 15-40s | 5s | 60-90s | 100-150s |
| File (Tesseract) | 60-100s | 10-30s | 3s | 60-90s | 70-100s |
| File (Ensemble) | 100-150s | 20-40s | 12s | 60-90s | 100-150s |
| File (Sarvam) | TBD (API key needed) | TBD | 2-5s + network | 60-90s | TBD |

**Key**: 
- First Request includes model initialization
- Cached times after models loaded in memory
- OCR Time = text extraction from images
- Evaluation Time = semantic analysis, scoring, etc.
- Requests 2+ use cached models (much faster)

---

### ✅ Verification Checklist

- [ ] Backend starts without errors: `python api/main.py`
- [ ] API docs accessible: http://127.0.0.1:8000/docs
- [ ] Frontend starts: `cd frontend && npm start`
- [ ] Frontend connects to backend: No "Failed to connect" errors
- [ ] Text evaluation works: Takes 60-120s, no timeout
- [ ] File upload works: Can select different OCR engines
- [ ] Results save: Can view results page
- [ ] Multi-question mode works: Evaluates multiple questions
- [ ] Custom rubric works: Can customize dimensions & weights
- [ ] Confidence scores display: No NaN or -1 values

---

### 🚀 Production Deployment Notes

1. **Model Preloading**: Initialize all models at startup
```python
# In api/main.py startup
@app.on_event("startup")
async def startup_event():
    logger.info("Preloading NLP models...")
    from api.services.semantic_service import SemanticAnalyzer
    SemanticAnalyzer()  # Load on startup, not per-request
    logger.info("Models loaded")
```

2. **Caching Strategy**: Use Redis for model caching
```bash
pip install redis
# Use Redis to cache model outputs across requests
```

3. **Async Processing**: Move evaluations to background tasks
```python
# Use Celery or RQ for async job queue
# Frontend polls /api/v1/results/{evaluation_id}
```

4. **Rate Limiting**: Add rate limits to prevent abuse
```bash
pip install slowapi
```

5. **Monitoring**: Add Prometheus metrics
```bash
pip install prometheus-client
```

---

### 📞 Support & Debug

#### Enable Debug Logging
```bash
export LOG_LEVEL=DEBUG
python api/main.py
```

#### Check Backend Logs
```bash
# Look for errors in console output
# Check {timestamp}.log file in logs/ directory
```

#### Test Specific Endpoints
```bash
# Get rubric presets
curl http://127.0.0.1:8000/api/v1/evaluate/rubric-presets

# Upload file
curl -F "file=@answer.pdf" http://127.0.0.1:8000/api/v1/evaluate/upload

# Evaluate text
curl -X POST http://127.0.0.1:8000/api/v1/evaluate/text \
  -H "Content-Type: application/json" \
  -d '{"model_answer": "...", "student_answer": "...", "question_type": "descriptive", "max_marks": 10, "ocr_engine": "easyocr"}'
```

#### Check Frontend Console (Browser DevTools)
```javascript
// F12 → Console tab
// Look for API response errors
// Check network tab for request/response details
```

---

### 🎯 Next Steps

1. ✅ **Immediate**: Run tests to verify core functionality works
2. ⏳ **Short-term**: Optimize model loading (preload at startup)
3. 🔄 **Medium-term**: Implement Sarvam AI integration with HTTP API fallback
4. 🚀 **Long-term**: Deploy to production with async task queue

