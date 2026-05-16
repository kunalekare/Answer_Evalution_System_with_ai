# 🧪 Testing Guide - Sarvam Engine Selection Fix

**Updated**: April 4, 2026  
**Status**: ✅ Ready to test after backend restart

---

## Quick Start

### Step 1: Stop the Backend
```
Press Ctrl+C in the terminal where backend is running
```

### Step 2: Restart Backend
```bash
cd c:\Users\Lenovo\Desktop\Answer_Evaluation
python run_backend.py
```

Wait for:
```
Uvicorn running on http://127.0.0.1:8000
```

### Step 3: Refresh Frontend
- Open http://localhost:3000
- Hard refresh: `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac)

✅ Now test!

---

## Test Case 1: Verify Sarvam Is Used (Happy Path)

**Prerequisites**: 
- `SARVAM_API_KEY` is set in `.env` file ✓
- `SARVAM_API_URL` is set in `.env` file ✓

**Steps**:
1. Go to Evaluate page
2. Upload a file (PDF or image)
3. **Select "sarvam"** from OCR Engine dropdown
4. Click "Next" or "Extract Text"
5. Wait 30-120 seconds

**Expected Result**:
- ✅ Text appears in preview box
- ✅ Backend logs show: `[sarvam] ✓ Engine initialized successfully`
- ✅ Backend logs show: `[sarvam] Extracting model answer...`
- ✅ Backend logs show: `[sarvam] ✓ Model extraction complete: XXXX chars`

**Backend Logs to Look For**:
```
[2026-04-04 12:00:00] INFO: Initializing OCRService with engine: sarvam
[2026-04-04 12:00:01] INFO: [sarvam] ✓ Engine initialized successfully
[2026-04-04 12:00:02] INFO: [sarvam] Extracting model answer...
[2026-04-04 12:00:30] INFO: [sarvam] ✓ Model extraction complete: 1250 chars
```

---

## Test Case 2: Verify Error When Sarvam Not Configured (Error Path)

**Prerequisites**:
- Temporarily comment out or delete `SARVAM_API_KEY` from `.env`
- Delete `SARVAM_API_URL` from `.env` (or leave blank)

**Steps**:
1. Restart backend with modified `.env`
2. Go to Evaluate page
3. Upload a file
4. **Select "sarvam"** from OCR Engine dropdown
5. Click "Next" or "Extract Text"

**Expected Result**:
- ❌ Red error message appears
- ❌ Message: `"Sarvam AI API key not configured. Set SARVAM_API_KEY in .env file."`
- ✅ Backend logs show: `[x] OCR engine initialization failed`

**Backend Logs to Look For**:
```
[2026-04-04 12:00:00] INFO: Initializing OCRService with engine: sarvam
[2026-04-04 12:00:01] ERROR: OCR Engine initialization failed: 
    Sarvam AI API key not configured. Set SARVAM_API_KEY in .env file.
```

---

## Test Case 3: Other Engines Still Work (Control Test)

**Prerequisites**: None (EasyOCR built-in)

**Steps**:
1. Go to Evaluate page
2. Upload a file
3. **Select "easyocr"** from OCR Engine dropdown
4. Click "Next" or "Extract Text"

**Expected Result**:
- ✅ Text appears in preview box
- ✅ Backend logs show: `[easyocr] ✓ Engine initialized successfully`
- ✅ Backend logs show: `[easyocr] Extracting model answer...`

---

## Test Case 4: Verify Frontend Is Passing Parameter

**How to Check**:

1. **Browser Developer Tools**:
   - Press `F12`
   - Go to "Network" tab
   - Click "Extract Text" button
   - Look for request to `/upload/XXX/extract-text`
   - Click on it
   - Under "Query String Parameters", you should see:
     ```
     ocr_engine: sarvam
     ```

2. **Backend Logs**:
   - Look for:
     ```
     Initializing OCRService with engine: sarvam
     ```

---

## Troubleshooting

### Issue: "ModuleNotFoundError" or other import errors

**Solution**: 
```bash
# Restart Python environment
pip install -r requirements.txt
python run_backend.py
```

### Issue: Backend shows "Sarvam AI not properly configured"

**Solution**:
```bash
# Check your .env file
cat .env | grep SARVAM

# Should show:
# SARVAM_API_KEY=sk_...
# SARVAM_API_URL=https://api.sarvam.ai/v1/document-intelligence

# If missing, add them and restart
```

### Issue: "Connection refused" or "Cannot connect to backend"

**Solution**:
```bash
# Check if backend is running
# If not, restart:
python run_backend.py
```

### Issue: Frontend shows old code

**Solution**:
```
Hard refresh browser:
- Windows/Linux: Ctrl+Shift+R
- Mac: Cmd+Shift+R
```

---

## Sign of Success ✅

When all tests pass, you should see:

- **Before**: Sarvam selected, but EasyOCR used secretly
- **After**: Sarvam selected, Sarvam is actually used

You'll know it worked when:
1. ✅ Backend logs explicitly show `[sarvam]` prefix
2. ✅ Error handling works: Sarvam misconfiguration gives clear error
3. ✅ Other engines still work fine
4. ✅ Frontend parameter passing works (visible in Network tab)

---

## Quick Verification Command

To verify code changes were applied:

```bash
# Check frontend fix
grep -A3 "extractTextFromUpload = async" frontend/src/services/api.js
# Should show: params: { ocr_engine: ocrEngine }

# Check backend fix
grep -A5 "def _init_sarvam" api/services/ocr_service.py
# Should show: raise ValueError(...) not silent fallback
```

---

## After Verification

Once tests pass:

1. ✅ Restore `.env` file with Sarvam credentials
2. ✅ Restart backend: `python run_backend.py`
3. ✅ Test with real Sarvam extraction
4. ✅ Verify no EasyOCR logs when Sarvam selected

---

## What Was Fixed

**Files Changed**:
- ✅ `frontend/src/services/api.js` - Now passes `ocr_engine` parameter
- ✅ `api/services/ocr_service.py` - Now raises errors instead of silent fallback
- ✅ `api/routes/upload.py` - Better error handling
- ✅ `api/routes/evaluation.py` - Better error handling

**User Experience**:
- ✅ Select Sarvam → Use Sarvam (not EasyOCR)
- ✅ Sarvam not configured → Get clear error
- ✅ Other engines work independently
- ✅ No more silent switches

---

## Questions?

Check the detailed documentation: [FIX_SARVAM_ENGINE_SELECTION.md](FIX_SARVAM_ENGINE_SELECTION.md)

