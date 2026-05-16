#!/usr/bin/env python3
"""
SARVAM AI SETUP & TROUBLESHOOTING GUIDE
=========================================

This guide explains how to properly configure and test Sarvam AI integration.
"""

# ============================================================================
# 1. GETTING SARVAM API KEY
# ============================================================================
"""
Step 1: Create a Sarvam AI Account
  - Visit: https://console.sarvam.ai/
  - Sign up with your email
  - Create a new API key

Step 2: Copy Your API Key
  - Go to: https://console.sarvam.ai/api-keys
  - Copy your API key (starts with "sk_")
  - Keep it safe! Don't share it publicly
"""

# ============================================================================
# 2. CONFIGURING SARVAM IN YOUR PROJECT
# ============================================================================
"""
Option A: Using .env File (Recommended)
  
  1. Open or create .env in project root
  2. Add these lines:
  
     SARVAM_API_KEY=sk_your_actual_api_key_here
     SARVAM_API_URL=https://api.sarvam.ai/parse-image
  
  3. Save the file
  4. Restart your application

Option B: Using Environment Variable (Alternative)
  
  export SARVAM_API_KEY=sk_your_actual_api_key_here
  python run_backend.py

Option C: Direct Configuration (Not recommended - security risk)
  
  Edit config/settings.py:
    SARVAM_API_KEY: Optional[str] = "sk_your_actual_api_key_here"
"""

# ============================================================================
# 3. TESTING SARVAM API CONFIGURATION
# ============================================================================
"""
Run the diagnostic tool to verify your setup:

  python test_sarvam_api_key.py

This will check:
  ✓ API Key is configured
  ✓ Endpoint URL is configured  
  ✓ Can connect to Sarvam API
  ✓ Can authenticate with API key
  ✓ Can extract text from sample image (if available)
"""

# ============================================================================
# 4. USING SARVAM FOR HANDWRITTEN TEXT EXTRACTION
# ============================================================================
"""
Option 1: API Endpoint (Set OCR_ENGINE='sarvam')
  
  1. In .env, set: OCR_ENGINE=sarvam
  2. Configure API key as above
  3. Upload handwritten document
  4. System will use Sarvam AI for extraction

Option 2: Dashboard Selection
  
  1. Go to Evaluate page in dashboard
  2. In "OCR Engine" dropdown, select "Sarvam AI Cloud"
  3. Upload your document
  4. Sarvam AI will be used for extraction

Option 3: API Request
  
  POST /api/v1/evaluate
  {
    "evaluation_id": "...",
    "ocr_engine": "sarvam",
    "max_marks": 10
  }
"""

# ============================================================================
# 5. COMMON ISSUES & SOLUTIONS
# ============================================================================
"""
Issue 1: "Endpoint Not Found (404)"
  
  Cause: API endpoint URL is incorrect or API has changed
  
  Solution:
    1. Run: python test_sarvam_api_key.py
    2. Check current endpoint in settings
    3. Visit: https://sarvam.ai/api-documentation
    4. Update SARVAM_API_URL with correct endpoint

Issue 2: "Authentication Failed (401)"
  
  Cause: Invalid or expired API key
  
  Solution:
    1. Go to: https://console.sarvam.ai/api-keys
    2. Check if API key is active
    3. Generate new API key if needed
    4. Update .env file with new key

Issue 3: "Connection Error - Cannot Reach API"
  
  Cause: Network issue or Sarvam API is down
  
  Solution:
    1. Check internet connection
    2. Try ping sarvam.ai
    3. Check firewall/VPN settings
    4. Wait and retry later
    5. Contact Sarvam support

Issue 4: "Extraction returns empty or no text"
  
  Cause: API doesn't recognize image format or language
  
  Solution:
    1. Ensure image is in supported format (PNG, JPG, PDF)
    2. Try uploading clearer image
    3. Explicitly set language in filename
    4. Check Sarvam API documentation for limitations

Issue 5: "Falling back to other engines"
  
  Cause: Sarvam API is not available or returns error
  
  System behavior:
    1. Tries Sarvam API first (if configured)
    2. Falls back to Google Vision (if configured)
    3. Falls back to OCR.space (free)
    4. Falls back to Sarvam PDF SDK
    5. Falls back to local EasyOCR (always works)
  
  This is EXPECTED - system automatically uses best available option
"""

# ============================================================================
# 6. SUPPORTED LANGUAGES (Sarvam AI)
# ============================================================================
"""
Sarvam AI supports text extraction in:

  - English (en)
  - Hindi (hi) 
  - Tamil (ta)
  - Telugu (te)
  - Kannada (kn)
  - Malayalam (ml)
  - Marathi (mr)
  - Gujarati (gu)
  - Punjabi (pa)
  - Bengali (bn)
  - Odia (or)
  - Urdu (ur)
  - Spanish (es)
  - French (fr)
  - German (de)
  - Portuguese (pt)
  - Italian (it)
  - Japanese (ja)
  - Chinese (zh)
  - Arabic (ar)
  - Russian (ru)

How to use:
  1. Name file with language hint: "answer_hindi.pdf"
  2. System auto-detects from filename
  3. Or pass language code explicitly in API
"""

# ============================================================================
# 7. SARVAM PRICING & LIMITS
# ============================================================================
"""
For current pricing and rate limits, visit:
  https://console.sarvam.ai/billing

Key Points:
  ✓ Free tier available for testing
  ✓ Pay-as-you-go pricing for production
  ✓ Rate limits depend on your plan
  ✓ Check billing page for current status
  ✓ Monitor API usage in console
"""

# ============================================================================
# 8. PERFORMANCE TIPS
# ============================================================================
"""
Optimizing Sarvam API usage:

1. Image Quality
   - Use clear, high-contrast handwritten images
   - Avoid blurry or low-resolution scans
   - Minimum 300 DPI for best results

2. File Format
   - Use PNG or JPG for single pages
   - Use PDF for multi-page documents
   - Keep file size < 50MB

3. Language Setting
   - Specify correct language for better accuracy
   - Include language in filename: "student_hindi.pdf"
   - Or set OCR_LANGUAGES in settings

4. Fallback Strategy
   - System uses intelligent fallback chain
   - Never fails completely (always falls back to EasyOCR)
   - Check logs to see which engine was used
"""

# ============================================================================
# 9. MONITORING & LOGGING
# ============================================================================
"""
Check logs to see Sarvam API activity:

  [Sarvam API] POST https://api.sarvam.ai/parse-image with language=en
  [Sarvam API] Response status: 200
  [Sarvam API] ✓ SUCCESS - Extracted 1234 chars

In case of errors:

  [Sarvam API] AUTHENTICATION FAILED (401)
  [Sarvam API] CONNECTION ERROR - Cannot reach API
  [Sarvam API] TIMEOUT - Request took too long
  
  → Check diagnostic tool output for detailed troubleshooting
"""

# ============================================================================
# 10. FREQUENTLY ASKED QUESTIONS
# ============================================================================
"""
Q: Is Sarvam API required?
A: No! System has intelligent fallback to Google Vision, OCR.space, and EasyOCR

Q: What if I don't have valid Sarvam API key?
A: System will automatically skip Sarvam and use other OCR engines

Q: Can I use other OCR engines for handwritten text?
A: Yes! Try 'ensemble', 'paddleocr', 'easyocr', or 'tesseract' for local processing

Q: Do I need internet for OCR?
A: For Sarvam only. Local engines (ensemble, easyocr) work offline

Q: How many pages can I extract?
A: Unlimited! System processes ALL pages from PDFs

Q: Is my document sent to Sarvam servers?
A: Yes, with Sarvam engine. Use local engines (easyocr) to keep data private

Q: Can I use free tier?
A: Yes! Sarvam offers free tier for testing

Q: What if API is down?
A: System automatically falls back to other OCR engines

Q: How to disable Sarvam and use local only?
A: Set OCR_ENGINE='ensemble' in .env file
"""

# ============================================================================
# 11. QUICK START CHECKLIST
# ============================================================================
"""
□ Create Sarvam AI account at console.sarvam.ai
□ Generate API key
□ Set SARVAM_API_KEY in .env file
□ Set SARVAM_API_URL in .env file
□ Run: python test_sarvam_api_key.py
□ Verify all checks pass (green ✓)
□ Set OCR_ENGINE='sarvam' in .env (optional)
□ Upload handwritten document to test
□ Check logs for extraction success
"""

# ============================================================================
# 12. SUPPORT
# ============================================================================
"""
If you need help:

1. Run diagnostic tool:
   python test_sarvam_api_key.py

2. Check documentation:
   - Sarvam API Docs: https://sarvam.ai/api-documentation
   - Sarvam Console: https://console.sarvam.ai/

3. Review logs:
   - Check stderr output for error messages
   - Look for [Sarvam API] debug logs

4. Contact Support:
   - Email: support@sarvam.ai
   - Website: https://sarvam.ai/
   - GitHub Issues: [Your project repo]
"""

if __name__ == "__main__":
    print(__doc__)
    print("\nTo test your Sarvam setup, run:")
    print("  python test_sarvam_api_key.py")
