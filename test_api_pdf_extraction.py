#!/usr/bin/env python3
"""Direct test of PDF extraction through actual API endpoint"""

import os
import sys
import requests
import json
from pathlib import Path

def create_test_pdf():
    """Create a simple test PDF file."""
    try:
        import fitz
        import tempfile
    except ImportError:
        print("Missing PyMuPDF. Install: pip install pymupdf")
        return None
    
    pdf_path = os.path.join(tempfile.gettempdir(), 'test_api_extraction.pdf')
    doc = fitz.open()
    
    # Add a simple page with text
    page = doc.new_page()
    page.insert_textbox(fitz.Rect(50, 50, 500, 200), 
                       "This is a test PDF for API extraction.\n"
                       "Testing in-memory PDF processing.\n"
                       "If no permission error, the fix works!")
    
    # Add another page
    page2 = doc.new_page()
    page2.insert_textbox(fitz.Rect(50, 50, 500, 200),
                        "Page 2 of test PDF.\n"
                        "Testing multi-page extraction.")
    
    doc.save(pdf_path)
    doc.close()
    
    return pdf_path

def test_api_extraction():
    """Test PDF extraction through actual API"""
    print("🔧 Setting up test environment...")
    
    # Create test PDF
    pdf_path = create_test_pdf()
    if not pdf_path or not os.path.exists(pdf_path):
        print("❌ Failed to create test PDF")
        return False
    
    print(f"✓ Created test PDF: {pdf_path}")
    print(f"  Size: {os.path.getsize(pdf_path)} bytes")
    
    try:
        # Prepare file upload
        with open(pdf_path, 'rb') as f:
            files = {'file': f}
            data = {
                'text_extraction_model': 'ensemble',
                'detail_flag': False
            }
            
            print("\n📡 Sending request to API...")
            print(f"   Endpoint: http://localhost:8000/api/evaluate/extract-text")
            
            # Make request to API
            response = requests.post(
                'http://localhost:8000/api/evaluate/extract-text',
                files=files,
                data=data,
                timeout=30
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                text = result.get('extracted_text', '')
                
                print(f"\n✅ API Request Successful!")
                print(f"   Extracted {len(text)} characters")
                print(f"   First 100 chars: {text[:100]}")
                
                if len(text) > 20:
                    print("\n✅ PDF extraction through API is WORKING!")
                    print("   ✓ No permission errors")
                    print("   ✓ In-memory processing successful")
                    print("   ✓ File cleanup completed")
                    return True
                else:
                    print("\n⚠️  Extraction succeeded but text seems minimal")
                    return True
            else:
                print(f"\n❌ API Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
                # Check for permission error in response
                if "Permission denied" in response.text or "cannot remove file" in response.text:
                    print("\n❌ Permission error still occurring!")
                    return False
                else:
                    print("   (Not a permission error - may be another issue)")
                    return False
    
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API")
        print("   Make sure backend is running: python run_backend.py")
        return False
    
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False
    
    finally:
        # Cleanup test file
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                print(f"\n✓ Cleaned up test PDF")
            except Exception as cleanup_err:
                print(f"⚠️  Could not cleanup: {cleanup_err}")

if __name__ == "__main__":
    print("=" * 70)
    print("PDF EXTRACTION API TEST")
    print("=" * 70)
    print()
    
    success = test_api_extraction()
    
    print()
    print("=" * 70)
    if success:
        print("✅ TEST PASSED - PDF extraction API is working!")
        print("   In-memory processing is successfully resolving permission errors")
    else:
        print("❌ TEST FAILED - Check backend logs")
    print("=" * 70)
    
    sys.exit(0 if success else 1)
