"""
Test PDF Extraction with New Permission Fix

This script tests the improved PDF extraction to ensure
permission errors are resolved.
"""

import os
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def create_test_pdf():
    """Create a simple test PDF from images"""
    try:
        import fitz
    except ImportError:
        print("ERROR: PyMuPDF not installed. Install with: pip install pymupdf")
        return None
    
    # Create 3 test pages as images first
    images = []
    for page_num in range(3):
        img = Image.new('RGB', (400, 300), color='white')
        d = ImageDraw.Draw(img)
        
        text = f"""Page {page_num + 1}

Test Student Answer
For PDF Extraction Testing

Lorem ipsum dolor sit amet,
consectetur adipiscing elit."""
        
        d.text((20, 20), text, fill='black')
        
        img_path = f"temp_page_{page_num}.png"
        img.save(img_path)
        images.append(img_path)
    
    # Convert images to PDF
    pdf_path = "test_document.pdf"
    doc = fitz.open()
    
    for img_path in images:
        img = Image.open(img_path)
        img_data = img.convert('RGB')
        
        # Create page from image
        pix_from_img = fitz.Pixmap(img_data)
        rect = fitz.Rect(pix_from_img.bbox)
        page = doc.new_page(width=rect.width, height=rect.height)
        page.insert_image(rect, pixmap=pix_from_img)
        os.remove(img_path)  # Clean up temp image
    
    doc.save(pdf_path)
    doc.close()
    
    return pdf_path

def test_pdf_extraction():
    """Test PDF extraction with permission handling"""
    
    print("=" * 70)
    print("TEST: PDF Extraction with Permission Fix")
    print("=" * 70)
    
    # Create test PDF
    print("\n[1] Creating test PDF...")
    pdf_path = create_test_pdf()
    
    if not pdf_path:
        print("     ERROR: Could not create test PDF")
        return False
    
    print(f"     Created: {pdf_path}")
    print(f"     Size: {os.path.getsize(pdf_path) / 1024:.1f}KB")
    
    # Test extraction
    print("\n[2] Initializing OCR service...")
    try:
        from api.services.ocr_service import OCRService
        ocr = OCRService(engine='easyocr')
        print("     Engine: easyocr")
        print("     Status: OK")
    except Exception as e:
        print(f"     ERROR: {e}")
        return False
    
    # Extract from PDF
    print("\n[3] Extracting text from PDF...")
    print("     (This tests the new permission fix)")
    
    try:
        result = ocr.extract_text(pdf_path)
        
        print("\n[RESULT] SUCCESS!")
        print(f"     Extracted: {len(result)} characters")
        print(f"     Preview: {result[:100]}...")
        
        success = True
    except Exception as e:
        print(f"\n[ERROR] Extraction failed: {e}")
        
        if "Permission denied" in str(e):
            print("     Issue: Permission error still occurring")
            print("     Solution: Check antivirus and indexing settings")
        
        success = False
    
    # Cleanup
    print("\n[4] Cleaning up...")
    try:
        os.remove(pdf_path)
        print(f"     Removed test PDF: {pdf_path}")
    except Exception as e:
        print(f"     Could not remove PDF (that's OK): {e}")
    
    print("\n" + "=" * 70)
    return success

if __name__ == '__main__':
    import sys
    success = test_pdf_extraction()
    
    if success:
        print("\n✓ PDF extraction is working with the new permission fix!")
        sys.exit(0)
    else:
        print("\n✗ PDF extraction still has issues")
        print("\nTroubleshooting steps:")
        print("1. Check antivirus exclusions (add temp folder)")
        print("2. Check indexing settings (exclude temp folder)")
        print("3. Restart computer to clear file locks")
        print("4. Check disk space availability")
        sys.exit(1)
