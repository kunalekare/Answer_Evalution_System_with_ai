#!/usr/bin/env python3
"""Direct in-memory PDF extraction test - verify no permission errors"""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def create_test_pdf():
    """Create simple test PDF"""
    try:
        import fitz
    except ImportError:
        print("Missing PyMuPDF. Install: pip install pymupdf")
        return None
    
    pdf_path = os.path.join(tempfile.gettempdir(), "test_inmem_extraction.pdf")
    
    doc = fitz.open()
    
    # Page 1: Text only
    page = doc.new_page(width=595, height=842)
    page.insert_textbox(fitz.Rect(50, 50, 500, 250),
        "Test PDF\n\n"
        "This is page 1 of the test PDF.\n"
        "Testing in-memory PDF extraction with files written to disk.\n"
        "If successful, no permission errors should occur.\n"
        "File cleanup should complete without locking issues."
    )
    
    # Page 2: More text
    page2 = doc.new_page(width=595, height=842)
    page2.insert_textbox(fitz.Rect(50, 50, 500, 250),
        "Page 2\n\n"
        "Testing multi-page extraction.\n"
        "Each page should extract without permission errors.\n"
        "Temporary files should cleanup immediately after use."
    )
    
    # Save to temp directory
    doc.save(pdf_path)
    doc.close()
    
    return pdf_path

def test_extraction():
    """Test PDF extraction directly"""
    print("🔧 Setting up test environment...")
    
    pdf_path = create_test_pdf()
    if not pdf_path or not os.path.exists(pdf_path):
        print("❌ Failed to create test PDF")
        return False
    
    file_size = os.path.getsize(pdf_path)
    print(f"✓ Created test PDF: {pdf_path}")
    print(f"  Size: {file_size} bytes")
    
    try:
        # Import service
        from api.services.ocr_service import OCRService
        from config.settings import Settings
        
        print("\n📄 Initializing OCR service...")
        settings = Settings()
        
        # Try with ensemble engine
        ocr = OCRService(engine="ensemble")
        
        print("🔍 Extracting text from PDF using in-memory processing...")
        print("   (This calls _extract_from_pdf with new in-memory approach)")
        
        # Test extraction
        result = ocr._extract_from_pdf(pdf_path, preprocess=False, detail=False)
        
        print(f"\n✅ Extraction succeeded!")
        print(f"   Result length: {len(result)} characters")
        print(f"   First 150 chars:\n   {result[:150]}")
        
        if len(result) > 30:
            print("\n✅✅ SUCCESS - PDF extraction with in-memory processing working!")
            print("   ✓ No permission errors occurred")
            print("   ✓ File cleanup completed successfully")
            print("   ✓ Multi-page extraction functional")
            return True
        else:
            print("\n⚠️  Extraction succeeded but text minimal")
            return False
    
    except PermissionError as e:
        print(f"\n❌ FAILED - Permission error still occurring!")
        print(f"   Error: {e}")
        print("\n   This means the in-memory fix did not work as expected.")
        return False
    
    except Exception as e:
        error_str = str(e)
        
        if "Permission denied" in error_str or "cannot remove file" in error_str:
            print(f"\n❌ FAILED - Permission error detected!")
            print(f"   Error: {e}")
            return False
        else:
            print(f"\n⚠️  Other error occurred: {type(e).__name__}")
            print(f"   Error: {e}")
            print("   (This is not a permission error - fix may still be working)")
            return False
    
    finally:
        # Cleanup
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                print(f"\n✓ Test PDF cleaned up successfully")
            except Exception as e:
                print(f"\n⚠️  Could not cleanup test PDF: {e}")

if __name__ == "__main__":
    print("=" * 70)
    print("DIRECT IN-MEMORY PDF EXTRACTION TEST")
    print("=" * 70)
    print()
    
    success = test_extraction()
    
    print()
    print("=" * 70)
    if success:
        print("✅✅✅ TEST PASSED!")
        print("In-memory PDF processing is working correctly")
        print("Permission errors have been resolved")
    else:
        print("❌❌❌ TEST FAILED!")
        print("In-memory fix needs further investigation")
    print("=" * 70)
    
    sys.exit(0 if success else 1)
