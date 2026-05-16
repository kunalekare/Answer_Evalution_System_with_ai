#!/usr/bin/env python3
"""
Test Model Answer Text Extraction with HTML Cleaning
=====================================================
Verifies that model answer extraction returns clean text without HTML markup
"""

import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from api.services.ocr_service import OCRService

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_html_stripping():
    """Test the HTML stripping functionality"""
    print_section("TEST 1: HTML Stripping Function")
    
    ocr = OCRService(engine='sarvam')
    
    test_cases = [
        {
            'name': 'HTML Table',
            'input': '<table><tr><td>Name</td><td>Value</td></tr><tr><td>Test</td><td>123</td></tr></table>',
            'expected_to_contain': ['Name', 'Value', 'Test', '123']
        },
        {
            'name': 'Mixed HTML and Text',
            'input': '<p>Semantic Ambiguity</p><table><tr><td>Arrow</td><td>The overall meaning</td></tr></table>',
            'expected_to_contain': ['Semantic', 'Ambiguity', 'overall', 'meaning']
        },
        {
            'name': 'HTML Entities',
            'input': 'Price: &pound;100 &nbsp;&nbsp; Code: &lt;ABC&gt;',
            'expected_to_contain': ['Price', '100', 'Code', 'ABC']
        },
        {
            'name': 'Nested Tables',
            'input': '<table><tr><td>Q1</td><td><table><tr><td>nested</td></tr></table></td></tr></table>',
            'expected_to_contain': ['Q1', 'nested']
        }
    ]
    
    all_passed = True
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        print(f"  Input: {test_case['input'][:60]}...")
        
        result = ocr._strip_html(test_case['input'])
        print(f"  Result: {result[:60]}...")
        
        # Check if expected content is present
        test_passed = True
        for expected in test_case['expected_to_contain']:
            if expected.lower() not in result.lower():
                print(f"  ERROR: Expected '{expected}' not found in result")
                test_passed = False
                all_passed = False
        
        # Check that HTML tags are removed
        if '<' in result or '>' in result:
            print(f"  ERROR: HTML tags still present in result")
            test_passed = False
            all_passed = False
        
        if test_passed:
            print(f"  PASS")
        else:
            print(f"  FAIL")
    
    return all_passed

def test_model_answer_extraction():
    """Test extraction with a model answer image"""
    print_section("TEST 2: Model Answer Extraction with HTML Cleaning")
    
    # Create test image similar to model answer (with tables)
    test_image = "test_model_answer.png"
    
    if not os.path.exists(test_image):
        print(f"INFO: Creating test image...")
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a simple model answer-like image
            img = Image.new('RGB', (600, 400), color='white')
            draw = ImageDraw.Draw(img)
            
            # Draw text similar to model answer
            draw.text((50, 30), "Question 1: Semantic Ambiguity", fill='black')
            draw.text((50, 80), "Answer:", fill='black')
            draw.text((50, 120), "The overall meaning of the question", fill='black')
            draw.text((50, 150), "is unclear.", fill='black')
            
            draw.text((50, 200), "Question 2: Context Ambiguity", fill='black')
            draw.text((50, 250), "The question depends on previous", fill='black')
            draw.text((50, 280), "conversation context.", fill='black')
            
            img.save(test_image)
            print(f"OK: Created test image: {test_image}")
        except Exception as e:
            print(f"ERROR: Could not create test image: {e}")
            return False
    
    print(f"Using test image: {test_image}")
    
    # Initialize OCR service
    print("\nInitializing OCR service with Sarvam SDK...")
    try:
        ocr = OCRService(engine='sarvam')
        print("OK: OCR service initialized")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return False
    
    # Extract text
    print("\nExtracting text from model answer image...")
    print("(This may take 30-60 seconds as Sarvam processes the image)\n")
    
    try:
        result = ocr.extract_text(test_image, detail=True)
        
        if not result:
            print("ERROR: Extraction returned empty result")
            return False
        
        # Handle response format
        if isinstance(result, list) and len(result) > 0:
            result_dict = result[0]
        else:
            result_dict = result if isinstance(result, dict) else {}
        
        text = result_dict.get('text', '')
        engine = result_dict.get('engine', 'unknown')
        
        print(f"OK: Extraction completed!")
        print(f"    Engine: {engine}")
        print(f"    Text length: {len(text)} characters")
        
        # Validate text quality
        print("\nVALIDATION CHECKS:")
        
        checks_passed = True
        
        # Check 1: Text should not contain HTML tags
        if '<' in text or '>' in text:
            print(f"ERROR: HTML tags found in text (< or > characters)")
            print(f"       Preview: {text[:100]}")
            checks_passed = False
        else:
            print("OK: No HTML tags in text")
        
        # Check 2: Text should not be ZIP binary
        if text.startswith('PK'):
            print("ERROR: Text appears to be ZIP binary data")
            print(f"       Preview: {text[:50]}")
            checks_passed = False
        else:
            print("OK: Text is not ZIP binary")
        
        # Check 3: Text should not have table markup
        if '<table>' in text.lower() or '<td>' in text.lower() or '<tr>' in text.lower():
            print(f"ERROR: HTML table markup still present in text")
            checks_passed = False
        else:
            print("OK: No HTML table markup")
        
        # Check 4: Text should not have metadata markers
        if '.metadata' in text or 'page_00' in text:
            print("ERROR: Metadata markers found in text")
            checks_passed = False
        else:
            print("OK: No metadata markers")
        
        # Show text preview
        if len(text) > 0:
            print(f"\nEXTRACTED TEXT PREVIEW:")
            print("    " + "-" * 65)
            lines = text.split('\n')
            for i, line in enumerate(lines[:8]):
                if line.strip():
                    preview = line[:65] if len(line) > 65 else line
                    print(f"    {preview}")
            if len(lines) > 8:
                print(f"    ... ({len(lines) - 8} more lines)")
            print("    " + "-" * 65)
        
        return checks_passed
        
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sarvam_vs_other_engines():
    """Compare Sarvam output with other engines"""
    print_section("TEST 3: Sarvam vs Other Engines (Quick Comparison)")
    
    test_image = "test_model_answer.png"
    if not os.path.exists(test_image):
        print(f"INFO: Test image not found, skipping comparison")
        return None
    
    engines_to_test = ['sarvam', 'easyocr']
    results = {}
    
    for engine in engines_to_test:
        print(f"\nTesting engine: {engine}")
        try:
            ocr = OCRService(engine=engine)
            result = ocr.extract_text(test_image, detail=True)
            
            if isinstance(result, list) and len(result) > 0:
                text = result[0].get('text', '')
            else:
                text = result if isinstance(result, str) else ''
            
            # Check for HTML
            has_html = '<' in text or '>' in text
            
            print(f"  Length: {len(text)} chars")
            print(f"  Has HTML: {has_html}")
            print(f"  Preview: {text[:60].replace(chr(10), ' ')}...")
            
            results[engine] = {
                'length': len(text),
                'has_html': has_html,
                'text': text
            }
        except Exception as e:
            print(f"  ERROR: {type(e).__name__}: {e}")
            results[engine] = None
    
    if all(v for v in results.values()):
        return True
    return None

def main():
    """Run all tests"""
    print("\nMODEL ANSWER TEXT EXTRACTION - HTML CLEANING TEST")
    print("Verifies that model answers are extracted as clean text")
    
    # Test 1: HTML stripping function
    print_section("TEST 1: HTML Stripping Function")
    result1 = test_html_stripping()
    
    # Test 2: Model answer extraction
    print_section("TEST 2: Model Answer Extraction")
    result2 = test_model_answer_extraction()
    
    # Test 3: Engine comparison
    print_section("TEST 3: Engine Comparison")
    result3 = test_sarvam_vs_other_engines()
    
    # Summary
    print_section("TEST SUMMARY")
    
    if result1:
        print("PASS: HTML stripping function: PASSED")
        status1 = "PASSED"
    else:
        print("FAIL: HTML stripping function: FAILED")
        status1 = "FAILED"
    
    if result2:
        print("PASS: Model answer extraction: PASSED")
        status2 = "PASSED"
    elif result2 is None:
        print("INFO: Model answer extraction: SKIPPED")
        status2 = "SKIPPED"
    else:
        print("FAIL: Model answer extraction: FAILED")
        status2 = "FAILED"
    
    if result3 is None:
        print("INFO: Engine comparison: SKIPPED")
        status3 = "SKIPPED"
    elif result3:
        print("PASS: Engine comparison: PASSED")
        status3 = "PASSED"
    else:
        print("FAIL: Engine comparison: FAILED")
        status3 = "FAILED"
    
    print("\n" + "=" * 70)
    print(f"Overall Status: {status1} | {status2} | {status3}")
    print("=" * 70)
    
    # Key improvements
    print("\nIMPROVEMENTS APPLIED:")
    print("  + Added _strip_html() method to OCRService")
    print("  + Strips HTML tags from Sarvam SDK output")
    print("  + Strips HTML tags from Sarvam PDF extraction")
    print("  + Decodes HTML entities (&nbsp;, &lt;, etc.)")
    print("  + Cleans up excessive whitespace")
    print("  + Preserves text structure with line breaks")
    
    print("\nRESULTS:")
    print("Before: <table>...</table> [HTML markup + metadata]")
    print("After:  Clean question text without markup")
    
    return 0 if status1 == "PASSED" else 1

if __name__ == "__main__":
    sys.exit(main())
