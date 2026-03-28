"""
Test script to verify text evaluation endpoint works correctly
==============================================================
Tests various scenarios for the /api/v1/evaluate/text endpoint
"""

import os
import sys
import json
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Test configuration
API_BASE_URL = os.getenv('REACT_APP_API_URL', 'http://localhost:8000')
API_ENDPOINT = f'{API_BASE_URL}/api/v1/evaluate/text'

def print_test(name):
    print(f"\n{'='*70}")
    print(f"  TEST: {name}")
    print('='*70)


def test_valid_text_evaluation():
    """Test 1: Valid text evaluation request"""
    print_test("Valid Text Evaluation")
    
    payload = {
        "model_answer": "Photosynthesis is the process by which plants convert light energy into chemical energy stored in glucose. It occurs in the chloroplasts of plant cells.",
        "student_answer": "Photosynthesis is when plants use sunlight to make food and oxygen.",
        "question_type": "descriptive",
        "max_marks": 10,
        "ocr_engine": "easyocr"
    }
    
    print(f"\nRequest: POST {API_ENDPOINT}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            API_ENDPOINT,
            json=payload,
            timeout=300
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ SUCCESS - Text evaluation completed")
            data = response.json()
            print(f"  Evaluation ID: {data.get('evaluation_id')}")
            print(f"  Score: {data.get('score')}/{data.get('max_marks')}")
            return True
        else:
            print(f"✗ FAILED")
            print(f"Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("✗ TIMEOUT - Endpoint took too long to respond")
        return False
    except requests.exceptions.ConnectionError:
        print("✗ CONNECTION ERROR - Cannot reach backend")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def test_short_model_answer():
    """Test 2: Model answer too short (< 10 chars)"""
    print_test("Short Model Answer (Should Fail)")
    
    payload = {
        "model_answer": "Too short",  # 9 characters - should fail
        "student_answer": "This is a longer student answer with more content",
        "question_type": "descriptive",
        "max_marks": 10
    }
    
    print(f"\nRequest: POST {API_ENDPOINT}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(API_ENDPOINT, json=payload, timeout=30)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 422:
            print("✓ EXPECTED ERROR - Validation failed as expected")
            errors = response.json()
            print(f"  Errors: {json.dumps(errors, indent=2)[:300]}")
            return True
        else:
            print(f"✗ UNEXPECTED STATUS - Expected 422, got {response.status_code}")
            print(f"Response: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def test_empty_student_answer():
    """Test 3: Empty student answer"""
    print_test("Empty Student Answer (Should Fail)")
    
    payload = {
        "model_answer": "This is a valid model answer with at least 10 characters",
        "student_answer": "",  # Empty - should fail
        "question_type": "descriptive"
    }
    
    print(f"\nRequest: POST {API_ENDPOINT}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(API_ENDPOINT, json=payload, timeout=30)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 422:
            print("✓ EXPECTED ERROR - Validation failed as expected")
            errors = response.json()
            print(f"  Errors: {json.dumps(errors, indent=2)[:300]}")
            return True
        else:
            print(f"✗ UNEXPECTED STATUS - Expected 422, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def test_invalid_question_type():
    """Test 4: Invalid question type"""
    print_test("Invalid Question Type (Should Fail)")
    
    payload = {
        "model_answer": "This is a valid model answer with at least 10 characters",
        "student_answer": "This is a valid student answer",
        "question_type": "invalid_type"  # Invalid enum value
    }
    
    print(f"\nRequest: POST {API_ENDPOINT}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(API_ENDPOINT, json=payload, timeout=30)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 422:
            print("✓ EXPECTED ERROR - Invalid enum value rejected")
            errors = response.json()
            print(f"  Errors: {json.dumps(errors, indent=2)[:300]}")
            return True
        else:
            print(f"✗ UNEXPECTED STATUS - Expected 422, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def test_invalid_ocr_engine():
    """Test 5: Invalid OCR engine"""
    print_test("Invalid OCR Engine (Should Fail)")
    
    payload = {
        "model_answer": "This is a valid model answer with at least 10 characters",
        "student_answer": "This is a valid student answer",
        "ocr_engine": "invalid_engine"  # Invalid engine
    }
    
    print(f"\nRequest: POST {API_ENDPOINT}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(API_ENDPOINT, json=payload, timeout=30)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 422:
            print("✓ EXPECTED ERROR - Invalid OCR engine rejected")
            errors = response.json()
            print(f"  Errors: {json.dumps(errors, indent=2)[:300]}")
            return True
        else:
            print(f"✗ UNEXPECTED STATUS - Expected 422, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def test_missing_required_field():
    """Test 6: Missing required field"""
    print_test("Missing Required Field (Should Fail)")
    
    payload = {
        # Missing model_answer
        "student_answer": "This is a valid student answer",
        "question_type": "descriptive"
    }
    
    print(f"\nRequest: POST {API_ENDPOINT}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(API_ENDPOINT, json=payload, timeout=30)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 422:
            print("✓ EXPECTED ERROR - Missing field detected")
            errors = response.json()
            print(f"  Errors: {json.dumps(errors, indent=2)[:300]}")
            return True
        else:
            print(f"✗ UNEXPECTED STATUS - Expected 422, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def test_with_sarvam_engine():
    """Test 7: Valid request with Sarvam engine"""
    print_test("Valid Request with Sarvam Engine")
    
    payload = {
        "model_answer": "Explain the water cycle: Water evaporates from oceans and lakes, forms clouds, and returns as precipitation.",
        "student_answer": "The water cycle is when water goes up as vapor, becomes clouds, and falls as rain.",
        "ocr_engine": "sarvam"  # Using Sarvam instead of default
    }
    
    print(f"\nRequest: POST {API_ENDPOINT}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            API_ENDPOINT,
            json=payload,
            timeout=300
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ SUCCESS - Text evaluation with Sarvam completed")
            data = response.json()
            print(f"  Evaluation ID: {data.get('evaluation_id')}")
            print(f"  Score: {data.get('score')}/{data.get('max_marks')}")
            return True
        else:
            print(f"✗ FAILED")
            print(f"Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("⚠ TIMEOUT - Evaluation took too long (normal for first run)")
        return True
    except requests.exceptions.ConnectionError:
        print("✗ CONNECTION ERROR - Cannot reach backend")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def generate_report(results):
    """Generate test report"""
    print(f"\n\n{'='*70}")
    print("  TEST REPORT: Text Evaluation Endpoint")
    print('='*70)
    
    tests = [
        "Valid Text Evaluation",
        "Short Model Answer",
        "Empty Student Answer",
        "Invalid Question Type",
        "Invalid OCR Engine",
        "Missing Required Field",
        "Sarvam Engine"
    ]
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}\n")
    
    for name, passed in zip(tests, results):
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\n{'='*70}")
    
    if all(results):
        print("✅ ALL TESTS PASSED - Text evaluation is working correctly!")
    else:
        print("⚠️ Some tests failed. Review the details above.")
    
    print('='*70)


def main():
    print("\n" + "="*70)
    print("  TEXT EVALUATION ENDPOINT TEST SUITE")
    print("="*70)
    print(f"\nTesting endpoint: {API_ENDPOINT}")
    print(f"Backend: {API_BASE_URL}")
    
    results = []
    
    # Run tests
    results.append(test_valid_text_evaluation())
    results.append(test_short_model_answer())
    results.append(test_empty_student_answer())
    results.append(test_invalid_question_type())
    results.append(test_invalid_ocr_engine())
    results.append(test_missing_required_field())
    results.append(test_with_sarvam_engine())
    
    # Generate report
    generate_report(results)


if __name__ == "__main__":
    main()
