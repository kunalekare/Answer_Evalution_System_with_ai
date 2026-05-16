#!/usr/bin/env python3
"""
Test HTML Stripping in OCR Postprocessing
==========================================
Verifies that HTML is stripped from all extracted text
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.services.ocr_service import OCRService

def test_postprocess_html_cleaning():
    """Test that _postprocess_ocr cleans HTML"""
    print("\nTesting HTML Cleaning in Postprocessing")
    print("=" * 70)
    
    ocr = OCRService(engine='easyocr')
    
    test_cases = [
        {
            'name': 'Model Answer Table',
            'input': '<table><tr><td>Name: NIRAJ</td></tr><tr><td>Roll: 48</td></tr></table>',
            'should_contain': ['Name', 'NIRAJ', 'Roll', '48']
        },
        {
            'name': 'Mixed Content',
            'input': '<p>Question 1: Semantic Ambiguity</p><p>Answer: The meaning is unclear.</p>',
            'should_contain': ['Question', 'Semantic', 'Ambiguity', 'Answer', 'meaning', 'unclear']
        },
        {
            'name': 'HTML Entities and Tags',
            'input': 'Price: &pound;100 &nbsp; Tag: &lt;test&gt; <b>Bold text</b>',
            'should_contain': ['Price', '100', 'Tag', 'test', 'Bold', 'text']
        },
        {
            'name': 'Complex Nested Structure',
            'input': '<div><table><tr><td>Q1</td><td><ul><li>Point A</li><li>Point B</li></ul></td></tr></table></div>',
            'should_contain': ['Q1', 'Point', 'A', 'Point', 'B']
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        
        # Process through postprocess_ocr (which is what happens to all extracted text)
        result = ocr._postprocess_ocr(test_case['input'])
        
        print(f"Input:  {test_case['input'][:60]}...")
        print(f"Output: {result[:60]}...")
        
        test_passed = True
        
        # Check for expected content
        for item in test_case['should_contain']:
            if item.lower() not in result.lower():
                print(f"  ERROR: Expected '{item}' not found")
                test_passed = False
                all_passed = False
            else:
                print(f"  OK: '{item}'")
        
        # Check that HTML tags are removed
        if '<' in result or '>' in result:
            print(f"  ERROR: HTML tags still present!")
            test_passed = False
            all_passed = False
        else:
            print(f"  OK: No HTML tags")
        
        if test_passed:
            print(f"  PASS")
        else:
            print(f"  FAIL")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("Result: ALL TESTS PASSED - HTML cleaning working!")
    else:
        print("Result: SOME TESTS FAILED")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(test_postprocess_html_cleaning())
