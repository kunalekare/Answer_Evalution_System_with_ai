# Sarvam AI Hindi Text Extraction Fix

## Problem
Sarvam AI's OCR was returning garbled text (appearing like Vietnamese characters) when extracting Hindi text from images. This occurred because the **language parameter** was missing from the API request.

Example of the issue:
- **Input**: Hindi text image (Devanagari script)
- **Expected**: Correctly extracted Hindi text
- **Actual**: `"Bộo Byo vệ sự và potec luy ota tito pce..."`

## Root Cause
Sarvam AI is a **multilingual OCR API that supports 22+ languages** including Hindi (and other Indian languages like Tamil, Telugu, Kannada, Malayalam, Marathi, Gujarati, Punjabi, Bengali, Odia, Urdu).

However, without explicitly specifying the language in the API request, Sarvam AI was:
1. Missing the language parameter altogether
2. Either defaulting to English or misdetecting the language
3. Interpreting Devanagari (Hindi) characters as Vietnamese or other scripts

## Solution Implemented

### 1. Added Language Support to Sarvam API Integration

**File**: `api/services/ocr_service.py`

#### Changes Made:

**A. Language Code Mapping (22+ Languages)**
```python
self._sarvam_languages = {
    'en': 'en', 'english': 'en',
    'hi': 'hi', 'hindi': 'hi',         # ← Added Hindi
    'ta': 'ta', 'tamil': 'ta',         # ← Added Tamil
    'te': 'te', 'telugu': 'te',        # ← Added Telugu
    'kn': 'kn', 'kannada': 'kn',       # ← Added Kannada
    'ml': 'ml', 'malayalam': 'ml',     # ← Added Malayalam
    'mr': 'mr', 'marathi': 'mr',       # ← Added Marathi
    'gu': 'gu', 'gujarati': 'gu',      # ← Added Gujarati
    'pa': 'pa', 'punjabi': 'pa',       # ← Added Punjabi
    'bn': 'bn', 'bengali': 'bn',       # ← Added Bengali
    'or': 'or', 'odia': 'or',          # ← Added Odia
    'ur': 'ur', 'urdu': 'ur',          # ← Added Urdu
    'es': 'es', 'spanish': 'es',
    'fr': 'fr', 'french': 'fr',
    'de': 'de', 'german': 'de',
    'pt': 'pt', 'portuguese': 'pt',
    'it': 'it', 'italian': 'it',
    'ja': 'ja', 'japanese': 'ja',
    'zh': 'zh', 'chinese': 'zh',
    'ar': 'ar', 'arabic': 'ar',
    'ru': 'ru', 'russian': 'ru',
}
```

**B. Automatic Language Detection from Filename**
```python
def _detect_language_from_path(self, image_path: str) -> str:
    """
    Detect language from filename or use primary language from config.
    
    Examples:
    - "answer_hindi.png" → 'hi'
    - "model_tamil.jpg" → 'ta'
    - "student_telugu_response.png" → 'te'
    - "generic_file.png" → 'en' (defaults to English)
    """
```

**C. Updated API Request with Language Parameter**
```python
data = {
    'threshold': '0.5',
    'page_number': '1',
    'language': language,  # ← KEY FIX: Now includes language!
}
```

#### Impact:
- **Before**: `POST /v1/document-intelligence` with no language → Misinterprets script
- **After**: `POST /v1/document-intelligence` with `language=hi` → Correctly extracts Hindi text

**D. Language Support Throughout the Pipeline**

Modified methods to support language parameter:
- `extract_text()` - Accept optional `language` parameter
- `_extract_sarvam()` - Pass language through fallback chain
- `_extract_sarvam_api_direct()` - Include language in API request
- `_extract_sarvam_via_pdf()` - Map language to Sarvam regional codes (e.g., `hi-IN`)

### 2. Updated Configuration

**File**: `config/settings.py`

```python
OCR_LANGUAGES: list = ["en", "hi"]  # Now includes Hindi by default
```

Previously: Only `["en"]` (English)
Now: `["en", "hi"]` (English + Hindi)

## How to Use

### Automatic Language Detection (Recommended)

Simply upload files with language hints in the filename:

```
uploads/
├── evaluations/
│   ├── eval_123/
│   │   ├── model_hindi.png          # ← Hindi detected automatically
│   │   └── student_hindi_answer.png # ← Hindi detected automatically
│   ├── eval_456/
│   │   ├── model_tamil.jpg          # ← Tamil detected automatically
│   │   └── student_answer_tamil.png # ← Tamil detected automatically
```

### Explicit Language Specification

When calling OCR extraction directly:

```python
from api.services.ocr_service import OCRService

# Initialize with Hindi support
ocr = OCRService(engine="sarvam", languages=["en", "hi"])

# Extract Hindi text explicitly
result = ocr.extract_text(
    "path/to/hindi_image.png",
    language="hi"  # ← Explicitly specify Hindi
)
```

### Supported Language Codes

| Language | Code | Alternative |
|----------|------|-------------|
| English | `en` | english |
| **Hindi** | `hi` | hindi |
| **Tamil** | `ta` | tamil |
| **Telugu** | `te` | telugu |
| **Kannada** | `kn` | kannada |
| **Malayalam** | `ml` | malayalam |
| **Marathi** | `mr` | marathi |
| **Gujarati** | `gu` | gujarati |
| **Punjabi** | `pa` | punjabi |
| **Bengali** | `bn` | bengali |
| **Odia** | `or` | odia |
| **Urdu** | `ur` | urdu |
| Spanish | `es` | spanish |
| French | `fr` | french |
| German | `de` | german |
| Portuguese | `pt` | portuguese |
| Italian | `it` | italian |
| Japanese | `ja` | japanese |
| Chinese | `zh` | chinese |
| Arabic | `ar` | arabic |
| Russian | `ru` | russian |

## Testing

### Manual Test

```bash
python test_hindi_extraction.py
```

This test will:
1. ✓ List all supported languages
2. ✓ Test automatic language detection from filenames
3. ✓ Test Hindi text extraction with Sarvam AI

### Integration Test

Upload a Hindi text image through the UI:
1. Navigate to the upload page
2. Upload model answer and student answer
3. Name files with language hints:
   - `model_hindi.png` or `model_answer_hindi.jpg`
   - `student_hindi_answer.png`
4. Proceed with evaluation
5. Verify Hindi text is correctly extracted (not garbled)

## Features

### ✅ What Works Now

- **Hindi Text Extraction**: Correctly extracts Devanagari script
- **Auto-Detection**: Detects language from filename automatically
- **All 22+ Languages**: Full multilingual support in Sarvam AI
- **Fallback Chain**: Multiple OCR methods if Sarvam fails
  1. Sarvam API (direct) - with language parameter ✓
  2. Google Vision API
  3. OCR.space API
  4. Sarvam PDF SDK - with language mapping ✓
  5. Local EasyOCR (always works)
- **Backward Compatible**: Existing code works without changes (language defaults to English)

### 🔄 Fallback Behavior

If Sarvam API fails:
1. Tries Google Vision API (if configured)
2. Tries OCR.space free API
3. Tries Sarvam PDF SDK conversion
4. Falls back to local EasyOCR (always succeeds)

## Advanced Usage

### Custom Language Configuration

To add more languages or change defaults:

**File**: `config/settings.py`

```python
OCR_LANGUAGES: list = ["en", "hi", "ta", "te", "kn"]  # Add more as needed
OCR_ENGINE: str = "sarvam"  # Switch to Sarvam for multilingual support
```

### Enable Language-Specific Preprocessing

```python
ocr = OCRService(
    engine="sarvam",
    languages=["en", "hi", "ta", "te", "kn", "ml"]  # Support all Indian languages
)
```

## Troubleshooting

### Issue: Garbled Text Still Appearing

**Solution**: Ensure filename includes language hint:
- ❌ `answer.png` → defaults to English
- ✓ `answer_hindi.png` → correctly detected as Hindi

### Issue: "No text extracted"

**Possible Causes**:
1. API key invalid or expired
2. Image quality too low
3. Wrong language specified (use filename hint)

**Solution**:
```python
# Check what language is being detected
detected_lang = ocr._detect_language_from_path("path/to/file.png")
print(f"Detected language: {detected_lang}")

# Verify API key
print(f"API Key configured: {bool(settings.SARVAM_API_KEY)}")
```

### Issue: Performance is slow

**Solution**: Fallback chain can be slow if Sarvam API fails
- Option 1: Use local OCR: `OCR_ENGINE = "easyocr"`
- Option 2: Ensure Sarvam API key is valid
- Option 3: Use `FAST_OCR_MODE = True` in config

## Configuration Recommendations

### For Indian Languages (Hindi, Tamil, Telugu, etc.)

```python
# config/settings.py
OCR_ENGINE: str = "sarvam"  # Use Sarvam for multilingual
OCR_LANGUAGES: list = ["en", "hi", "ta", "te", "kn", "ml", "mr", "gu", "pa"]
FAST_OCR_MODE: bool = True  # Skip heavy preprocessing
SARVAM_API_KEY: str = "your_sarvam_api_key_here"  # Required
```

### For English-Only with Best Accuracy

```python
# config/settings.py
OCR_ENGINE: str = "ensemble"  # Use all 3 local engines
OCR_LANGUAGES: list = ["en"]
FAST_OCR_MODE: bool = False  # Use full preprocessing
```

### Production Balanced Setup

```python
# config/settings.py
OCR_ENGINE: str = "easyocr"  # Balanced speed/accuracy
OCR_LANGUAGES: list = ["en"]
FAST_OCR_MODE: bool = True  # Skip heavy preprocessing
```

## Migration Guide

### If You Were Using Sarvam Before

No changes needed! The update is **backward compatible**:
- Existing code continues to work
- Language defaults to English if not specified
- Filename detection is automatic

### If You Want to Add Hindi Support

1. Update `config/settings.py`:
   ```python
   OCR_LANGUAGES: list = ["en", "hi"]
   ```

2. Ensure Sarvam API key is configured

3. (Optional) Add language to upload filenames:
   - `model_hindi.png` → Auto-detected
   - `student_hindi_answer.jpg` → Auto-detected

That's it! Hindi extraction should now work correctly.

## Technical Details

### API Request Format (With Language)

**Before** (Broken):
```http
POST https://api.sarvam.ai/v1/document-intelligence
Authorization: Bearer {api_key}
Content-Type: multipart/form-data

threshold=0.5&page_number=1
```

**After** (Fixed):
```http
POST https://api.sarvam.ai/v1/document-intelligence
Authorization: Bearer {api_key}
Content-Type: multipart/form-data

threshold=0.5&page_number=1&language=hi
```

### Response Format

```json
{
  "text": "यह एक परीक्षण है",  // Hindi text correctly extracted
  "output": {
    "text": "यह एक परीक्षण है"
  }
}
```

## References

- [Sarvam AI Documentation](https://docs.sarvam.ai)
- [Supported Languages Map](https://docs.sarvam.ai/language-codes)
- [Document Intelligence API](https://docs.sarvam.ai/document-intelligence)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review test output: `python test_hindi_extraction.py`
3. Check logs: `logs/assessiq.log`
4. Verify API key: `config/settings.py`

---

**Version**: 1.0 (March 2026)
**Status**: ✓ Fixed and Tested
**Impact**: Sarvam AI now correctly handles Hindi and 21+ other languages
