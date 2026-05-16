#!/usr/bin/env python3
"""
Test HTML Stripping Function
=============================
Simple test to verify HTML tags are properly stripped
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.services.ocr_service import OCRService

def test_html_stripping():
    """Test the HTML stripping functionality"""
    print("\nTesting HTML Stripping Function")
    print("=" * 70)
    
    ocr = OCRService(engine='easyocr')  # Initialize without Sarvam for fast startup
    
    test_cases = [
        {
            'name': 'HTML Table',
            'input': '<table><tr><td>Name</td><td>Value</td></tr><tr><td>Test</td><td>123</td></tr></table>',
            'should_contain': ['Name', 'Value', 'Test', '123'],
            'should_not_contain': ['<table>', '<td>', '<tr>']
        },
        {
            'name': 'Mixed HTML and Text',
            'input': '<p>Semantic Ambiguity</p><table><tr><td>Arrow</td><td>The overall meaning</td></tr></table>',
            'should_contain': ['Semantic', 'Ambiguity', 'overall', 'meaning', 'Arrow'],
            'should_not_contain': ['<p>', '<table>']
        },
        {
            'name': 'HTML Entities',
            'input': 'Price: &pound;100 &nbsp;&nbsp; Code: &lt;ABC&gt;',
            'should_contain': ['Price', '100', 'Code', 'ABC'],
            'should_not_contain': ['&nbsp;', '&lt;', '&gt;']
        },
        {
            'name': 'Nested Tables',
            'input': '<table><tr><td>Q1</td><td><table><tr><td>nested</td></tr></table></td></tr></table>',
            'should_contain': ['Q1', 'nested'],
            'should_not_contain': ['<table>', '<td>']
        },
        {
            'name': 'Real Model Answer Format',
            'input': '<table><thead><tr><th>Name: NIRAJ</th><th colspan="2">VIth Sem - DS</th></tr></thead><tbody><tr><td>Roll no: 48</td></tr></tbody></table><p>Semantic Ambiguity</p><p>The overall meaning is unclear.</p>',
            'should_contain': ['Name', 'NIRAJ', 'VIth', 'Semantic', 'Ambiguity', 'unclear'],
            'should_not_contain': ['<table>', '<thead>', '<tbody>', '<th>']
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print(f"Input:  {test_case['input'][:50]}...")
        
        result = ocr._strip_html(test_case['input'])
        print(f"Output: {result[:60]}...")
        
        test_passed = True
        
        # Check if items that should be in result are present
        for item in test_case['should_contain']:
            if item.lower() not in result.lower():
                print(f"  ERROR: Expected '{item}' not found in result")
                test_passed = False
                all_passed = False
            else:
                print(f"  OK: Found '{item}'")
        
        # Check that items that should NOT be in result are absent
        for item in test_case['should_not_contain']:
            if item.lower() in result.lower():
                print(f"  ERROR: Unexpected '{item}' found in result")
                test_passed = False
                all_passed = False
            else:
                print(f"  OK: '{item}' properly removed")
        
        if test_passed:
            print(f"  PASS")
        else:
            print(f"  FAIL")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("Result: ALL TESTS PASSED")
    else:
        print("Result: SOME TESTS FAILED")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(test_html_stripping())
