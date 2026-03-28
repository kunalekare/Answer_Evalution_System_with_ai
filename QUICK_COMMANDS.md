#!/usr/bin/env bash
# QUICK REFERENCE: Start System, Run Tests, Debug

# ==============================================================================
# OPTION 1: START SYSTEM (Normal Operation)
# ==============================================================================

# Terminal 1: Start Backend (port 8000)
echo "Starting Backend..."
python api/main.py
# Wait for: "Uvicorn running on http://127.0.0.1:8000"
# Press CTRL+C to stop

---

# Terminal 2: Start Frontend (port 3000)
echo "Starting Frontend..."
cd frontend
npm install  # First time only
npm start
# Wait for: "Compiled successfully!"
# Press CTRL+C to stop

# Then open browser: http://localhost:3000

---


# ==============================================================================
# OPTION 2: QUICK TEST (Verify Everything Works)
# ==============================================================================

# Test 1: Pydantic Model Validation (no API needed)
python test_quick_eval.py

# Test 2: Check API is running
curl http://127.0.0.1:8000/docs

# Test 3: Test Text Evaluation via API
curl -X POST http://127.0.0.1:8000/api/v1/evaluate/text \
  -H "Content-Type: application/json" \
  -d '{
    "model_answer": "The photosynthesis process occurs in plants where chlorophyll absorbs light energy and converts it into chemical energy through two main stages: light-dependent reactions and light-independent reactions (Calvin cycle).",
    "student_answer": "Photosynthesis is when plants use sunlight to make food using chlorophyll.",
    "question_type": "descriptive",
    "max_marks": 10,
    "ocr_engine": "easyocr"
  }' \
  --max-time 120

# Expected: JSON response with score, grade, breakdown (wait 60-120s)

---


# ==============================================================================
# OPTION 3: INSTALL DEPENDENCIES (First Time)
# ==============================================================================

# Backend dependencies
pip install -r requirements.txt --upgrade

# Frontend dependencies
cd frontend
npm install
cd ..

# Optional: Sarvam AI (if package becomes available)
pip install sarvam-ai  # Currently NOT available on PyPI

---


# ==============================================================================
# OPTION 4: TROUBLESHOOT
# ==============================================================================

# Check if ports are in use
netstat -an | grep 8000  # Port 8000 (backend)
netstat -an | grep 3000  # Port 3000 (frontend)

# Kill process on port
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -i :8000
kill -9 <PID>

# Check backend logs
tail -f logs/*.log

# Fresh start (clear cache)
rm -rf node_modules package-lock.json
npm install
npm start

---


# ==============================================================================
# OPTION 5: ENABLE DEBUG MODE
# ==============================================================================

# Backend Debug Logging
export LOG_LEVEL=DEBUG
python api/main.py

# Frontend Debug Logging
export REACT_APP_DEBUG=true
npm start

---


# ==============================================================================
# OPTION 6: RUN DATABASE MIGRATIONS (if needed)
# ==============================================================================

# Check database status
python -c "from database.models import *; print('Database OK')"

# Reset database (WARNING: Deletes all data!)
rm assessiq.db
python api/main.py

---


# ==============================================================================
# OPTION 7: TEST DIFFERENT SCENARIOS
# ==============================================================================

# Scenario A: Text Input Only (Fastest Test)
# 1. Backend: python api/main.py
# 2. Frontend: npm start (from frontend/)
# 3. Click: Evaluate Answer → Toggle ON "Use text input"
# 4. Enter: Sample answers (min 10 chars each)
# 5. Click: Evaluate → Wait 60-120 seconds
# 6. See: Results page with scores

# Scenario B: File Upload (With OCR)
# 1. Backend: python api/main.py
# 2. Frontend: npm start (from frontend/)
# 3. Click: Evaluate Answer → Toggle OFF "Use text input"
# 4. Select: OCR Engine = "tesseract" (fastest)
# 5. Upload: Image or PDF files
# 6. Click: Next → Review extracted text
# 7. Click: Evaluate → Wait 60-120 seconds
# 8. See: Results page with scores

# Scenario C: Multi-Question Evaluation
# 1. Enable: "Multi-Question Mode" toggle in Step 3
# 2. Enter: Question 1 answer\nQuestion 2 answer...
# 3. Set: Total marks (auto-divides per question)
# 4. Click: Evaluate → Wait 60-120 seconds
# 5. See: Per-question scores breakdown

---


# ==============================================================================
# OPTION 8: PERFORMANCE PROFILING
# ==============================================================================

# Time the evaluation
time python test_quick_eval.py

# Expected times (first run):
# TEST 1 (Model validation): < 1 second
# TEST 2 (Evaluation): 60-90 seconds (includes model loading)

# Second run (cached models):
# TEST 2 (Evaluation): 10-30 seconds (much faster!)

---


# ==============================================================================
# OPTION 9: CLEAN UP & RESET
# ==============================================================================

# Remove compiled Python files
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

# Remove cache
rm -rf .pytest_cache
rm -rf node_modules

# Clear logs
rm -f logs/*.log

# Reset database
rm -f assessiq.db
rm -f db/*.db

# Fresh start
python api/main.py

---


# ==============================================================================
# OPTION 10: PRODUCTION DEPLOYMENT (Future)
# ==============================================================================

# Run with Gunicorn (production WSGI server)
pip install gunicorn
gunicorn api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Build frontend for production
cd frontend
npm run build

# Serve static files from backend
# (Configure in api/main.py or use nginx reverse proxy)

---


# ==============================================================================
# QUICK KEYBOARD SHORTCUTS
# ==============================================================================

# Terminal multiplexing (tmux) - RunBoth In One Terminal Window
tmux new-session -d -s backend "python api/main.py"
tmux new-window -t backend "cd frontend && npm start"
tmux attach-session -t backend

# Kill session
tmux kill-session -t backend

---


# ==============================================================================
# IMPORTANT TIMEOUTS & SETTINGS
# ==============================================================================

# Text Evaluation Timeout: 120 seconds (in api.js)
# API Server Timeout: 120 seconds (in api/main.py)
# Request Timeout: 120 seconds (in api.js)

# These are set because:
# - Model loading: 30-50 seconds (first time only)
# - Semantic analysis: 20-40 seconds
# - Scoring: 10-20 seconds
# Total: 60-120 seconds (first run with model initialization)
# Future: 10-30 seconds (cached models)

---


# ==============================================================================
# NOTES
# ==============================================================================

## Expected Behavior:
✅ Text evaluation shows "Running AI evaluation (60-120 seconds)" toast
✅ File upload can take 5-15s for text extraction
✅ Results page shows detailed score breakdown
✅ No 422 errors or timeout messages
✅ Browser console shows successful API calls

## Common Issues:
❌ 422 Error → Restart backend & frontend
❌ Connection refused → Backend not running (python api/main.py)
❌ Port already in use → Kill process using port
❌ PyMuPDF error → pip install PyMuPDF
❌ Model timeout → First run takes 60-120s, that's normal!

## Performance Tips:
⚡ Use "tesseract" OCR engine for fastest extraction (3s)
⚡ Text-only mode is fastest (no OCR extraction needed)
⚡ Second evaluation onwards is much faster (cached models)
⚡ Don't use "ensemble" for quick tests (slowest but most accurate)

---

For detailed documentation, see:
- TESTING_GUIDE.md (comprehensive testing)
- QUICK_FIXES_SUMMARY.md (what was fixed)
- README.md (general overview)

