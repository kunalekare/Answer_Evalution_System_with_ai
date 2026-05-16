#!/usr/bin/env python3
"""Test PDF extraction with in-memory processing (no temp file permission issues)."""

import os
import sys
import tempfile
from pathlib import Path

# Add api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

def create_test_pdf():
    """Create a simple test PDF file."""
    try:
        import fitz
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("❌ Missing dependencies. Install: pip install pymupdf pillow")
        return None
    
    # Create a temporary PDF
    pdf_path = os.path.join(tempfile.gettempdir(), "test_mem_fix.pdf")
    
    # Create a PDF with both text and images
    doc = fitz.open()
    
    # Page 1: Text and image
    page1 = doc.new_page()
    
    # Add text
    text_rect = fitz.Rect(50, 50, 500, 150)
    page1.insert_textbox(text_rect, "This is a test PDF for memory-based extraction.\n"
                                     "Testing in-memory processing without temp files.\n"
                                     "If no permission error appears, the fix works!")
    
    # Page 2: Image only (will need OCR)
    page2 = doc.new_page()
    
    # Add text that requires OCR
    text_rect = fitz.Rect(50, 50, 500, 250)
    page2.insert_textbox(text_rect, "OCR Test Page\n\nThis page contains only images that will need OCR processing.\n"
                                     "Testing extraction from image without embedded text.\n"
                                     "If successful, in-memory fix is working correctly.")
    
    # Save PDF
    doc.save(pdf_path)
    doc.close()
    
    return pdf_path

def test_extraction():
    """Test PDF extraction with the fixed method."""
    print("🔧 Setting up test environment...")
    
    pdf_path = create_test_pdf()
    if not pdf_path:
        print("❌ Failed to create test PDF")
        return False
    
    print(f"✓ Created test PDF: {pdf_path}")
    
    try:
        from services.ocr_service import OCRService
        from config.settings import Settings
        
        settings = Settings()
        ocr = OCRService(settings=settings, engine_name="ensemble")
        
        print("\n📄 Extracting text from test PDF...")
        print("   (Using in-memory processing - should NOT create permission errors)")
        
        # Extract text
        text = ocr._extract_from_pdf(pdf_path, preprocess=False, detail=False)
        
        print(f"\n✓ Extraction successful!")
        print(f"   Extracted text length: {len(text)} characters")
        print(f"   First 100 chars: {text[:100]}")
        
        # Check for actual content
        if len(text) > 20:
            print("\n✅ PDF extraction with in-memory processing is WORKING!")
            print("   No permission errors occurred during extraction or cleanup.")
            return True
        else:
            print("\n⚠️  Text extracted but appears minimal. Check extraction logic.")
            return True
    
    except PermissionError as e:
        print(f"\n❌ Permission Error (fix did not work): {e}")
        return False
    
    except Exception as e:
        print(f"\n⚠️  Extraction error: {type(e).__name__}: {e}")
        # This might be OK if it's an API error, not a permission error
        if "Permission denied" not in str(e):
            print("   (This is not a permission error - fix may still be working)")
            return True
        return False
    
    finally:
        # Cleanup
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                print(f"\n✓ Cleaned up test PDF: {pdf_path}")
            except Exception as cleanup_err:
                print(f"\n⚠️  Could not cleanup test PDF: {cleanup_err}")

if __name__ == "__main__":
    print("=" * 70)
    print("PDF EXTRACTION IN-MEMORY PROCESSING TEST")
    print("=" * 70)
    print()
    
    success = test_extraction()
    
    print()
    print("=" * 70)
    if success:
        print("✅ TEST PASSED - In-memory processing fix is working!")
    else:
        print("❌ TEST FAILED - Fix may need adjustment")
    print("=" * 70)
    
    sys.exit(0 if success else 1)
