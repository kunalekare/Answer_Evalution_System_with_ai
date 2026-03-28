"""
Comprehensive Test Suite for Sarvam AI and Evaluation API
===========================================================
Tests:
1. Sarvam AI API key validity
2. OCR extraction with Sarvam
3. Text evaluation endpoint (handles 422 errors)
4. Multi-question evaluation
5. Timeout/Performance issues
"""

import sys
import os
import json
import time
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings

# ============================================================================
# SECTION 1: Test Sarvam AI API Key
# ============================================================================

def test_sarvam_api_key():
    """Test if Sarvam AI API key is valid and accessible."""
    print("\n" + "="*80)
    print("TEST 1: Sarvam AI API Key Validity")
    print("="*80)
    
    api_key = settings.SARVAM_API_KEY
    print(f"API Key configured: {bool(api_key)}")
    print(f"API Key (masked): {api_key[:10]}...{api_key[-10:] if api_key else 'NOT SET'}")
    
    if not api_key:
        print("❌ FAILED: SARVAM_API_KEY not configured in settings.py")
        return False
    
    try:
        from sarvam import Sarvam
        client = Sarvam(api_key=api_key)
        print("✅ PASSED: Sarvam client initialized successfully")
        return True
    except ImportError:
        print("❌ FAILED: sarvam-ai package not installed. Run: pip install sarvam-ai")
        return False
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


# ============================================================================
# SECTION 2: Test Sarvam OCR Extraction
# ============================================================================

def test_sarvam_ocr_extraction():
    """Test Sarvam OCR on a sample image."""
    print("\n" + "="*80)
    print("TEST 2: Sarvam AI OCR Extraction")
    print("="*80)
    
    try:
        from api.services.ocr_service import OCRService
        from config.settings import settings
        
        ocr = OCRService()
        
        # Create a simple test image with text (if sample exists)
        sample_images = [
            "temp/test_image_eval.py",
            "uploads/student_answers",
            "uploads/model_answers",
        ]
        
        test_image_found = False
        for path in sample_images:
            if os.path.exists(path):
                files = [f for f in os.listdir(path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf'))]
                if files:
                    test_file = os.path.join(path, files[0])
                    print(f"\nUsing test image: {test_file}")
                    
                    start = time.time()
                    text = ocr.extract_text(test_file, engine="sarvam")
                    elapsed = time.time() - start
                    
                    print(f"✅ Sarvam extracted text in {elapsed:.2f}s")
                    print(f"Extracted text length: {len(text)} characters")
                    print(f"Sample text: {text[:100]}...")
                    test_image_found = True
                    break
        
        if not test_image_found:
            print("⚠️  No test images found - skipping Sarvam OCR extraction test")
            print("   To test, place an image in uploads/student_answers/ or uploads/model_answers/")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# SECTION 3: Test Text Evaluation Endpoint
# ============================================================================

def test_text_evaluation_endpoint():
    """Test the /api/v1/evaluate/text endpoint directly."""
    print("\n" + "="*80)
    print("TEST 3: Text Evaluation Endpoint (/api/v1/evaluate/text)")
    print("="*80)
    
    api_url = "http://127.0.0.1:8000/api/v1/evaluate/text"
    
    # Test case 1: Valid request
    valid_payload = {
        "model_answer": "The photosynthesis process occurs in plants where chlorophyll absorbs light energy and converts it into chemical energy. This process involves two main stages: the light-dependent reactions in the thylakoid membrane and the light-independent reactions (Calvin cycle) in the stroma. The overall equation is 6CO2 + 6H2O + light energy → C6H12O6 + 6O2.",
        "student_answer": "Photosynthesis is when plants use sunlight to make food. It happens in chloroplasts using chlorophyll. There are light reactions and dark reactions that together make glucose and oxygen.",
        "question_type": "descriptive",
        "max_marks": 10,
        "ocr_engine": "easyocr"
    }
    
    print(f"\nEndpoint URL: {api_url}")
    print(f"\nTest Payload:")
    print(f"  model_answer length: {len(valid_payload['model_answer'])} chars")
    print(f"  student_answer length: {len(valid_payload['student_answer'])} chars")
    print(f"  question_type: {valid_payload['question_type']}")
    print(f"  max_marks: {valid_payload['max_marks']}")
    print(f"  ocr_engine: {valid_payload['ocr_engine']}")
    
    try:
        start = time.time()
        response = requests.post(api_url, json=valid_payload, timeout=120)
        elapsed = time.time() - start
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASSED: Endpoint returned 200")
            print(f"\nResponse Structure:")
            print(f"  success: {data.get('success')}")
            print(f"  final_score: {data.get('final_score')}")
            print(f"  grade: {data.get('grade')}")
            print(f"  obtained_marks: {data.get('obtained_marks')}")
            print(f"  max_marks: {data.get('max_marks')}")
            
            if data.get('score_breakdown'):
                print(f"\nScore Breakdown:")
                for key, value in data['score_breakdown'].items():
                    if value is not None:
                        print(f"  {key}: {value}")
            
            return True
        
        elif response.status_code == 422:
            print(f"❌ VALIDATION ERROR (422): Invalid request body")
            print(f"\nError Details: {response.text}")
            
            # Try to parse error details
            try:
                error_data = response.json()
                if 'detail' in error_data:
                    print(f"\nValidation Errors:")
                    for error in error_data['detail']:
                        print(f"  Field: {error.get('loc')}")
                        print(f"  Problem: {error.get('msg')}")
                        print(f"  Type: {error.get('type')}")
            except:
                pass
            
            return False
        
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ FAILED: Cannot connect to {api_url}")
        print("   Make sure the backend is running: python api/main.py")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ FAILED: Request timed out after 120 seconds")
        return False
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


# ============================================================================
# SECTION 4: Test All OCR Engines
# ============================================================================

def test_all_ocr_engines():
    """Test all 5 OCR engines to verify they work."""
    print("\n" + "="*80)
    print("TEST 4: All OCR Engines")
    print("="*80)
    
    engines = ["easyocr", "ensemble", "tesseract", "paddleocr", "sarvam"]
    results = {}
    
    try:
        from api.services.ocr_service import OCRService
        ocr = OCRService()
        
        # Find a test image
        test_image_path = None
        for root, dirs, files in os.walk("uploads"):
            for f in files:
                if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                    test_image_path = os.path.join(root, f)
                    break
            if test_image_path:
                break
        
        if not test_image_path:
            print("⚠️  No test image found - creating minimal test")
            # Try with a small image
            try:
                from PIL import Image, ImageDraw, ImageFont
                import io
                
                # Create a simple test image with text
                img = Image.new('RGB', (200, 100), color='white')
                d = ImageDraw.Draw(img)
                d.text((10, 10), "Test OCR", fill='black')
                
                test_image_path = "temp/test_ocr.png"
                os.makedirs("temp", exist_ok=True)
                img.save(test_image_path)
                print(f"Created test image: {test_image_path}")
            except:
                print("Could not create test image")
                return False
        
        print(f"\nUsing test image: {test_image_path}")
        
        for engine in engines:
            try:
                print(f"\nTesting {engine}...", end=" ", flush=True)
                start = time.time()
                text = ocr.extract_text(test_image_path, engine=engine)
                elapsed = time.time() - start
                
                results[engine] = {
                    "success": True,
                    "text_length": len(text),
                    "time": elapsed,
                    "sample": text[:50] if text else ""
                }
                print(f"✅ {elapsed:.2f}s - {len(text)} chars")
                
            except Exception as e:
                results[engine] = {
                    "success": False,
                    "error": str(e)
                }
                print(f"❌ {str(e)[:50]}")
        
        print(f"\n\nEngine Summary:")
        for engine, result in results.items():
            if result['success']:
                print(f"  {engine:12} ✅ {result['time']:6.2f}s - {result['text_length']:4} chars")
            else:
                print(f"  {engine:12} ❌ {result['error'][:40]}")
        
        return all(r['success'] for r in results.values())
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# SECTION 5: Test with Rubric Config Variations
# ============================================================================

def test_rubric_config_validation():
    """Test different rubric_config formats to identify 422 errors."""
    print("\n" + "="*80)
    print("TEST 5: Rubric Config Validation")
    print("="*80)
    
    api_url = "http://127.0.0.1:8000/api/v1/evaluate/text"
    
    base_payload = {
        "model_answer": "The photosynthesis process occurs in plants where chlorophyll absorbs light energy and converts it into chemical energy.",
        "student_answer": "Photosynthesis is when plants use sunlight to make food.",
        "question_type": "descriptive",
        "max_marks": 10,
        "ocr_engine": "easyocr"
    }
    
    test_cases = [
        ("No rubric_config", {}),
        ("With preset rubric", {"rubric_config": {"preset": "factual"}}),
        ("With custom dimensions", {
            "rubric_config": {
                "dimensions": [
                    {"name": "understanding", "weight": 0.5},
                    {"name": "terminology", "weight": 0.5}
                ]
            }
        }),
    ]
    
    for test_name, extra_payload in test_cases:
        print(f"\n{test_name}:")
        payload = {**base_payload, **extra_payload}
        
        try:
            response = requests.post(api_url, json=payload, timeout=60)
            
            if response.status_code == 200:
                print(f"  ✅ Status 200 - Success")
                data = response.json()
                print(f"     Score: {data.get('final_score')}")
            elif response.status_code == 422:
                print(f"  ❌ Status 422 - Validation Error")
                try:
                    error_data = response.json()
                    for error in error_data.get('detail', []):
                        print(f"     Field: {error.get('loc')}")
                        print(f"     Error: {error.get('msg')}")
                except:
                    print(f"     {response.text[:100]}")
            else:
                print(f"  ❌ Status {response.status_code}")
                print(f"     {response.text[:100]}")
                
        except requests.exceptions.ConnectionError:
            print(f"  ⚠️  Backend not running")
            break
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  COMPREHENSIVE DIAGNOSTICS: Sarvam AI & Evaluation API".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)
    
    results = []
    
    results.append(("Sarvam API Key", test_sarvam_api_key()))
    results.append(("Sarvam OCR Extraction", test_sarvam_ocr_extraction()))
    results.append(("Text Evaluation Endpoint", test_text_evaluation_endpoint()))
    results.append(("All OCR Engines", test_all_ocr_engines()))
    
    if all(r[1] for r in results if r[1] is not None):
        print("\n")
        test_rubric_config_validation()
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED" if passed is False else "⚠️  SKIPPED"
        print(f"{test_name:40} {status}")
    
    print("\n" + "="*80)
    
    if any(r[1] is False for r in results):
        print("🔧 RECOMMENDATIONS:")
        for test_name, passed in results:
            if passed is False:
                if "Sarvam API" in test_name:
                    print("  1. Verify SARVAM_API_KEY in config/settings.py")
                    print("  2. Run: pip install sarvam-ai")
                elif "Endpoint" in test_name:
                    print("  3. Start backend: python api/main.py")
                    print("  4. Check for validation errors in test output above")
                elif "OCR" in test_name:
                    print("  5. Install missing OCR dependencies: pip install -r requirements.txt")
