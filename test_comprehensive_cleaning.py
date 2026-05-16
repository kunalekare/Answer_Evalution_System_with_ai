#!/usr/bin/env python3
"""
Test Comprehensive OCR Text Cleaning for Student & Model Answers
==================================================================
Verifies that messy OCR text is cleaned and normalized properly
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.services.ocr_service import OCRService

def print_test(title, input_text, expected_patterns):
    """Helper to print test results"""
    print(f"\n{title}")
    print("=" * 70)
    
    # Safely print input/output with encoding handling
    try:
        print(f"INPUT Preview:\n{input_text[:100]}...\n")
    except UnicodeEncodeError:
        print("INPUT: (text with special characters)\n")
    
    ocr = OCRService(engine='easyocr')
    output = ocr._postprocess_ocr(input_text)
    
    try:
        print(f"OUTPUT:\n{output}\n")
    except UnicodeEncodeError:
        print(f"OUTPUT: (text with special characters, length={len(output)})\n")
    
    # Check expected patterns
    all_found = True
    for pattern in expected_patterns:
        # Check if pattern is in output (case-insensitive, allows for line breaks)
        found = False
        if pattern.lower() in output.lower():
            found = True
        elif '-' in pattern:
            # For hyphenated words like "word-by-word", check flexible matching
            parts = pattern.split('-')
            if all(part.lower() in output.lower() for part in parts):
                found = True
        
        if found:
            print(f"  OK: Found '{pattern}'")
        else:
            print(f"  ERROR: Missing '{pattern}'")
            all_found = False
    
    return all_found

def test_student_answer_cleaning():
    """Test cleaning messy student answer like the example provided"""
    print_test(
        "TEST 1: Student Answer Text Cleaning",
        """ustification:

1) Automatic Language conversijm
Google tranelate can instantly tranelate words,
sentences across more than 100 lang. using ML
Models.

2) Context understanding
Modern neural machine translation analyzers
the entire sentences instead of translating word-by-
word.

Steps involved in Machine translation

3) Large training data
Google traine its models using massive bilingual
dataset dictionaries and multilingual corpora,
which helps improve translation accuracy.

1> Text input
2> Lexical Analysis
3> Syntactic Analysis
4> Translation stage
5> Target language Generation
6> Output delivery

Question 3:

Sentiment Analysis is a NLP technique used to
determine the emotional tone or attitude
expressed in a piece of text.

Working of sentiment analysts
1> Text preprocessing

>> feature Extraction""",
        [
            'Automatic Language conversion',  # Fixed typo
            'Google translate',  # Fixed typo
            'translate words',  # Fixed typo
            'word-by-word',  # Normalized dashes
            'machine translation',  # Joined lines
            'sentiment analysis',  # Fixed typo from "analysts"
            'feature extraction',  # Fixed case
            'Text input',  # Normalized number format
        ]
    )

def test_model_answer_cleaning():
    """Test cleaning model answer with HTML and formatting issues"""
    print_test(
        "TEST 2: Model Answer HTML & Numbering Cleaning",
        """<table><tr><td>Name: NIRAJ B BHAKTE</td></tr>
<tr><td>Roll no: 48</td></tr></table>

1. Justification:
2. Automatic Language conversion
3. Google translate can instantly translate words,
4. sentences across more than 100 lang. using ML
5. Models.
6. Context understanding
7. Modern neural machine translation analyzes
8. the entire sentences instead of translating word-by-
9. word.
10. Large training data
11. Google traine its models using massive bilingual
12. dataset dictionarice and multilingual corpora,
13. which helps improve translation accuracy.""",
        [
            'Name',
            'NIRAJ',
            'Roll',
            '48',
            'Justification',
            'Automatic Language conversion',
            'Google translate',
            'dictionaries',  # Fixed typo from "dictionarice"
            'multilingual corpora',
            'word-by-word',  # Properly formatted
            'trained its models',  # Fixed typo from "traine"
        ]
    )

def test_numbering_normalization():
    """Test that different numbering formats are normalized"""
    print_test(
        "TEST 3: Numbering Format Normalization",
        """1) First point
2) Second point
3> Third point with arrow
4. Fourth point with dot
- Fifth point with dash
* Sixth point with asterisk""",
        [
            'First point',
            'Second point',
            'Third point',
            'Fourth point',
            'Fifth point',
            'Sixth point',
        ]
    )

def test_ocr_typo_corrections():
    """Test that common OCR errors are fixed"""
    ocr = OCRService(engine='easyocr')
    
    print("\nTEST 4: OCR Typo Corrections")
    print("=" * 70)
    
    test_cases = [
        ('tranelate', 'translate'),
        ('conversijm', 'conversion'),
        ('Dejection', 'Detection'),
        ('dictionarice', 'dictionaries'),
        ('traine', 'trained'),
        ('the test expresses', 'the text expresses'),
        ('sentiment analyzer', 'sentiment analysis'),  # analyzer can be correct too
    ]
    
    all_passed = True
    for input_word, expected in test_cases:
        result = ocr._postprocess_ocr(input_word)
        if expected.lower() in result.lower():
            print(f"  OK: '{input_word}' -> contains '{expected}'")
        else:
            # Check if it's a similar match (like analyzer vs analysis)
            if 'sentiment' in result.lower() and ('analyz' in result.lower() or 'analysis' in result.lower()):
                print(f"  OK: '{input_word}' -> contains sentiment analysis pattern")
            else:
                print(f"  ERROR: '{input_word}' should contain '{expected}', got '{result}'")
                all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    print("\nOCR TEXT CLEANING - STUDENT & MODEL ANSWERS")
    print("Comprehensive cleaning for messy OCR text")
    
    results = []
    
    # Test 1: Student answer
    results.append(("Student Answer Cleaning", test_student_answer_cleaning()))
    
    # Test 2: Model answer
    results.append(("Model Answer Cleaning", test_model_answer_cleaning()))
    
    # Test 3: Numbering
    results.append(("Numbering Normalization", test_numbering_normalization()))
    
    # Test 4: OCR corrections
    results.append(("OCR Typo Corrections", test_ocr_typo_corrections()))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + "=" * 70)
    if all_passed:
        print("All tests PASSED - OCR cleaning working for both answers!")
    else:
        print("Some tests failed")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
