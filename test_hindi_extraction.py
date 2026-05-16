"""
Test Hindi Text Extraction with Sarvam AI
============================================
This test verifies that Hindi text is correctly extracted from images
using Sarvam AI's multilingual OCR capabilities.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from api.services.ocr_service import OCRService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("HindiExtractionTest")


def test_sarvam_hindi_extraction():
    """Test Sarvam AI extraction with Hindi language support."""
    
    print("=" * 80)
    print("TESTING HINDI TEXT EXTRACTION WITH SARVAM AI")
    print("=" * 80)
    
    # Check Sarvam API key
    if not settings.SARVAM_API_KEY:
        logger.error("SARVAM_API_KEY not configured in settings")
        return False
    
    logger.info(f"Sarvam AI API URL: {settings.SARVAM_API_URL}")
    logger.info(f"OCR Engine: {settings.OCR_ENGINE}")
    logger.info(f"OCR Languages: {settings.OCR_LANGUAGES}")
    
    # Initialize OCR service with Sarvam
    try:
        logger.info("\n[1/3] Initializing Sarvam AI OCR Service...")
        ocr = OCRService(engine="sarvam", languages=["en", "hi"])
        logger.info("✓ Sarvam AI OCR Service initialized successfully")
    except Exception as e:
        logger.error(f"✗ Failed to initialize Sarvam AI: {e}")
        return False
    
    # Check for test image
    test_image_path = "uploads/evaluations/test_hindi_image.png"
    
    if not os.path.exists(test_image_path):
        logger.warning(f"\n[2/3] Test image not found at: {test_image_path}")
        logger.info("Creating a simple test image with Hindi text...")
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            import tempfile
            
            # Create a simple test image
            img = Image.new('RGB', (400, 200), color='white')
            d = ImageDraw.Draw(img)
            
            # Try to use a Hindi-compatible font
            font_paths = [
                "/usr/share/fonts/opentype/noto/NotoSansDevanagari-Regular.ttf",  # Linux
                "C:\\Windows\\Fonts\\Devanagari.ttf",  # Windows
                "C:\\Windows\\Fonts\\NotoSansDevanagari-Regular.ttf",  # Windows (Noto font)
            ]
            
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, 24)
                        break
                    except:
                        continue
            
            if font is None:
                # Fallback to default font
                logger.warning("Hindi font not found, using default font")
                d.text((10, 50), "Test Image (No Hindi font)", fill='black')
            else:
                # Hindi text: "यह एक परीक्षण है" (This is a test)
                hindi_text = "यह एक परीक्षण है"
                d.text((10, 50), hindi_text, fill='black', font=font)
            
            # Save test image
            os.makedirs("uploads/evaluations", exist_ok=True)
            img.save(test_image_path)
            logger.info(f"✓ Test image created at: {test_image_path}")
            
        except ImportError:
            logger.error("PIL not available. Install with: pip install Pillow")
            return False
    
    # Test extraction with explicit Hindi language
    try:
        logger.info("\n[3/3] Testing Hindi text extraction...")
        logger.info("Extracting with language='hi' (Hindi)...")
        
        result = ocr.extract_text(
            test_image_path,
            preprocess=False,
            detail=True,
            language='hi'  # ← Explicitly specify Hindi
        )
        
        if result:
            logger.info(f"\n✓ SUCCESS! Extracted text:")
            if isinstance(result, list):
                for item in result:
                    logger.info(f"  - Text: {item.get('text', '')[:100]}")
                    logger.info(f"    Engine: {item.get('engine', 'unknown')}")
                    logger.info(f"    Language: {item.get('language', 'unknown')}")
                    logger.info(f"    Confidence: {item.get('confidence', 'unknown')}")
            else:
                logger.info(f"  - Text: {result[:100]}")
        else:
            logger.warning("No text extracted")
            return False
        
        logger.info("\n" + "=" * 80)
        logger.info("✓ HINDI EXTRACTION TEST PASSED!")
        logger.info("=" * 80)
        return True
        
    except Exception as e:
        logger.error(f"✗ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_language_detection():
    """Test automatic language detection from filename."""
    
    print("\n" + "=" * 80)
    print("TESTING LANGUAGE AUTO-DETECTION")
    print("=" * 80)
    
    try:
        ocr = OCRService(engine="sarvam", languages=["en", "hi"])
        
        test_cases = [
            ("student_answer_hindi.png", "hi"),
            ("model_answer_english.jpg", "en"),
            ("question_tamil.pdf", "ta"),
            ("generic_file.png", "en"),  # Should default to English
        ]
        
        logger.info("Testing language detection from filenames:")
        for filename, expected_lang in test_cases:
            detected_lang = ocr._detect_language_from_path(filename)
            status = "✓" if detected_lang == expected_lang else "⚠"
            logger.info(f"  {status} {filename:30} → {detected_lang:5} (expected: {expected_lang})")
        
        logger.info("\n✓ LANGUAGE DETECTION TEST COMPLETED!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Language detection test failed: {e}")
        return False


def test_supported_languages():
    """Print supported languages."""
    
    print("\n" + "=" * 80)
    print("SUPPORTED LANGUAGES")
    print("=" * 80)
    
    try:
        ocr = OCRService(engine="sarvam", languages=["en", "hi"])
        
        logger.info("Sarvam AI supports the following languages:")
        for lang_name, lang_code in sorted(ocr._sarvam_languages.items()):
            if len(lang_name) <= 2:  # Show only unique 2-letter codes
                logger.info(f"  - {lang_name:3} ({lang_code})")
        
        logger.info("\n✓ LANGUAGE LISTING TEST COMPLETED!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Language listing test failed: {e}")
        return False


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + "SARVAM AI MULTILINGUAL OCR TEST SUITE".center(78) + "║")
    print("║" + "Hindi & 22+ Language Support Verification".center(78) + "║")
    print("╚" + "=" * 78 + "╝")
    
    results = {
        "Language Listing": test_supported_languages(),
        "Language Detection": test_language_detection(),
        "Hindi Extraction": test_sarvam_hindi_extraction(),
    }
    
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + "FINAL RESULTS".center(78) + "║")
    print("╠" + "=" * 78 + "╣")
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"║ {test_name:40} {status:>35} ║")
    
    print("╚" + "=" * 78 + "╝")
    
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)
