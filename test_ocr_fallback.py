"""
Test OCR Fallback Chain - Verify that text extraction works
"""
import os
from PIL import Image, ImageDraw, ImageFont
import tempfile

def create_test_image(text="Hello World Test"):
    """Create a simple test image with text"""
    img = Image.new('RGB', (400, 200), color='white')
    d = ImageDraw.Draw(img)
    d.text((20, 20), text, fill='black')
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        img.save(tmp.name)
        return tmp.name

def test_ocr_service():
    """Test OCR service with fallback chain"""
    print("=" * 70)
    print("TEST: OCR Service Fallback Chain")
    print("=" * 70)
    
    # Create test image
    print("\n[1] Creating test image...")
    test_image = create_test_image("Test Student Answer Paper")
    print(f"    Created: {test_image}")
    
    # Initialize OCR service with Sarvam
    print("\n[2] Initializing OCRService with engine='sarvam'...")
    try:
        from api.services.ocr_service import OCRService
        ocr = OCRService(engine='sarvam')
        print(f"    Engine: {ocr.engine_name}")
        print(f"    Sarvam API Key: {ocr._sarvam_api_key[:15]}...***")
    except Exception as e:
        print(f"    ERROR: {e}")
        return
    
    # Try text extraction
    print("\n[3] Extracting text (with automatic fallback)...")
    print("    Trying: Sarvam -> Google Vision -> OCR.space -> Sarvam PDF -> EasyOCR")
    print()
    
    try:
        result = ocr.extract_text(test_image)
        print(f"\n[OK] SUCCESS!")
        print(f"  Extracted Text: {result[:100]}...")
        print(f"  Total Length: {len(result)} characters")
        print(f"  Success: Text was extracted using fallback chain")
    except Exception as e:
        print(f"\n[ERR] FAILED!")
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if os.path.exists(test_image):
            os.remove(test_image)
            print(f"\n[4] Cleaned up test image")

if __name__ == '__main__':
    test_ocr_service()
