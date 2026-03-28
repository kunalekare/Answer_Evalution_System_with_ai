# Quick Start: OCR Engine Selection

## 30-Second Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Choose Your OCR Engine

#### Option A: EasyOCR (Recommended - Default)
✅ No additional setup needed!
- Balanced accuracy & speed (~5s)
- CPU-only
```python
from api.services.ocr_service import OCRService
ocr = OCRService(engine="easyocr")  # or just OCRService()
text = ocr.extract_text("answer.jpg")
```

#### Option B: Ensemble (Best Accuracy)
✅ No additional setup needed!
- Highest accuracy (~12s, 90-95%)
- Runs 3 engines in parallel
```python
from api.services.ocr_service import OCRService
ocr = OCRService(engine="ensemble")
text = ocr.extract_text("answer.jpg")
```

#### Option C: Sarvam AI (Cloud-Based)
1. Create account: https://console.sarvam.ai/
2. Get API key and add to `.env`:
   ```env
   SARVAM_API_KEY=your_key_here
   ```
3. Use in code:
   ```python
   from api.services.ocr_service import OCRService
   ocr = OCRService(engine="sarvam")
   text = ocr.extract_text("answer.jpg")
   ```

#### Option D: Tesseract (Fast)
1. Install Tesseract binary
   - Windows: https://github.com/UB-Mannheim/tesseract/wiki
   - Linux: `sudo apt-get install tesseract-ocr`
   - macOS: `brew install tesseract`
2. Use in code:
   ```python
   from api.services.ocr_service import OCRService
   ocr = OCRService(engine="tesseract")
   text = ocr.extract_text("answer.jpg")
   ```

#### Option E: PaddleOCR (Layouts)
1. Install: `pip install paddlepaddle paddleocr`
2. Use in code:
   ```python
   from api.services.ocr_service import OCRService
   ocr = OCRService(engine="paddleocr")
   text = ocr.extract_text("answer.jpg")
   ```

---

## Via REST API

### Request Format
```bash
curl -X POST http://localhost:8000/api/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "evaluation_id": "test-123",
    "ocr_engine": "sarvam",  # Change this
    "question_type": "descriptive",
    "max_marks": 10
  }'
```

### Available OCR Engines
- `"easyocr"` - Balanced (default)
- `"ensemble"` - Best accuracy
- `"tesseract"` - Fast
- `"paddleocr"` - For layouts
- `"sarvam"` - Cloud API

---

## Configuration

### .env File (Recommended)
```env
# OCR Settings
OCR_ENGINE=easyocr  # or ensemble, tesseract, paddleocr, sarvam
FAST_OCR_MODE=true
LOW_MEMORY_MODE=false

# Sarvam AI API Key (required for "sarvam" engine)
SARVAM_API_KEY=your_sarvam_api_key_here

# Optional: Google Cloud Vision (for better Sarvam fallback)
GOOGLE_CLOUD_API_KEY=your_google_key_here

# Optional: OCR.space key (free fallback)
OCRSPACE_API_KEY=K88888888888957
```

### settings.py (Alternative)
```python
# config/settings.py
OCR_ENGINE = "ensemble"  # or "easyocr", "sarvam", etc.
SARVAM_API_KEY = "your_key_here"
FAST_OCR_MODE = True
```

---

## Performance Comparison

```
Task: Extract text from handwritten exam paper

Engine      | Time   | Accuracy | Notes
------------|--------|----------|---------------------------
EasyOCR     | ~5s    | 85-90%   | ✅ Recommended for production
Ensemble    | ~12s   | 90-95%   | ✅ Best accuracy, slower
Tesseract   | ~3s    | 80-85%   | ✅ Fastest, ok accuracy
PaddleOCR   | ~8s    | 85-90%   | ✅ Good for structured text
Sarvam AI   | ~2s*   | 90-95%   | ✅ Cloud, high accuracy
            |        |          | (* + network latency)
```

---

## Examples

### Example 1: Simple Text Extraction
```python
from api.services.ocr_service import OCRService

# Use default (EasyOCR)
ocr = OCRService()
text = ocr.extract_text("student_answer.jpg")
print(f"Extracted: {text[:100]}...")
```

### Example 2: Compare Engines
```python
from api.services.ocr_service import OCRService

engines = ["easyocr", "ensemble", "sarvam"]
image = "exam_paper.jpg"

for engine in engines:
    try:
        ocr = OCRService(engine=engine)
        text = ocr.extract_text(image)
        print(f"{engine}: {len(text)} chars extracted")
    except Exception as e:
        print(f"{engine}: Error - {e}")
```

### Example 3: Full Evaluation with Custom Engine
```python
from api.services.ocr_service import OCRService
from api.services.nlp_service import NLPPreprocessor
from api.services.scoring_service import ScoringService

# Setup custom OCR engine
ocr = OCRService(engine="ensemble")  # Use ensemble
nlp = NLPPreprocessor()
scorer = ScoringService()

# Extract answers
model_text = ocr.extract_text("model_answer.jpg")
student_text = ocr.extract_text("student_answer.jpg")

# Process
model_norm = nlp.normalize_text(model_text)
student_norm = nlp.normalize_text(student_text)

# Score
keywords = nlp.extract_keywords(model_norm)
score = scorer.calculate_keyword_coverage(keywords, student_norm)

print(f"Score: {score}")
```

### Example 4: Using Sarvam AI Cloud API
```python
from api.services.ocr_service import OCRService

# Requires SARVAM_API_KEY in .env
ocr = OCRService(engine="sarvam")

# Automatically tries:
# 1. Google Cloud Vision (if key set)
# 2. OCR.space (free)
# 3. Sarvam SDK (requires API key)
# 4. EasyOCR (fallback)

text = ocr.extract_text("handwritten_answer.pdf")
print(text)
```

### Example 5: Quality Assessment
```python
from api.services.ocr_service import OCRService, OCRQualityAnalyzer

ocr = OCRService(engine="ensemble")
text = ocr.extract_text("answer.jpg")

# Get quality metrics
analyzer = OCRQualityAnalyzer()
quality = analyzer.calculate_quality_score(text, confidence=0.85)

print(f"Quality Score: {quality['quality_score']}")
print(f"Dictionary Ratio: {quality['dictionary_ratio']}")
print(f"Language Model: {quality['language_model']}")

# Per-line analysis
line_analysis = analyzer.analyze_per_line(text, confidence=0.85)
for line in line_analysis[:3]:
    print(f"  Line {line['line']}: {line['quality_score']:.3f}")
```

---

## Troubleshooting

### "No module named 'sarvam'"
```bash
pip install sarvam-ai
```

### "Sarvam API key not configured"
1. Add to `.env`: `SARVAM_API_KEY=your_key`
2. Or set environment: `export SARVAM_API_KEY=your_key`
3. Restart application

### "Tesseract not found"
Windows:
```powershell
# Download installer: https://github.com/UB-Mannheim/tesseract/wiki
# Install and add path to settings.py:
# TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

Linux:
```bash
sudo apt-get install tesseract-ocr
```

---

## API Endpoint Reference

### Evaluate with OCR Engine Selection
```
POST /api/v1/evaluate
Content-Type: application/json

{
  "evaluation_id": "exam-123",
  "ocr_engine": "easyocr",      # <-- Your choice!
  "question_type": "descriptive",
  "max_marks": 10,
  "custom_keywords": ["osmosis", "membrane"]
}
```

### Response Includes
```json
{
  "success": true,
  "score": 7.5,
  "feedback": "Good understanding of concepts...",
  "ocr_metadata": {
    "engine_used": "easyocr",
    "extracted_chars": 245,
    "processing_time": 4.2
  }
}
```

---

## Cheat Sheet

| Need | Use | Command |
|------|-----|---------|
| Quick eval | `easyocr` | `OCRService()` |
| Best accuracy | `ensemble` | `OCRService(engine="ensemble")` |
| Very fast | `tesseract` | `OCRService(engine="tesseract")` |
| Forms/docs | `paddleocr` | `OCRService(engine="paddleocr")` |
| Cloud API | `sarvam` | `OCRService(engine="sarvam")` |

---

## Environment Variables

```bash
# Required (choose one)
SARVAM_API_KEY=sk_xxx...

# Optional
OCR_ENGINE=easyocr
FAST_OCR_MODE=true
LOW_MEMORY_MODE=false
TESSERACT_PATH=/path/to/tesseract

# For fallback
GOOGLE_CLOUD_API_KEY=xxx
OCRSPACE_API_KEY=xxx
```

---

## See Also

- [SARVAM_OCR_SETUP.md](SARVAM_OCR_SETUP.md) - Full setup & features
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - What was built
- [README.md](README.md) - Project overview

---

## Support

- 🐍 Python: https://python.org
- 🚀 FastAPI: https://fastapi.tiangolo.com
- 👁️ EasyOCR: https://github.com/JaidedAI/EasyOCR
- ✍️ Sarvam: https://console.sarvam.ai
- 📖 Tesseract: https://github.com/UB-Mannheim/tesseract
- 🎯 PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR

**Happy evaluating! 🎓**
