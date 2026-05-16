"""
Test the fixed API upload/extract-text endpoint
"""
import requests
import json
from PIL import Image, ImageDraw
import tempfile
import os

def create_test_image(filename="test.png"):
    """Create a simple test image"""
    img = Image.new('RGB', (400, 200), color='white')
    d = ImageDraw.Draw(img)
    d.text((20, 20), "Test Student Answer\nFor Evaluation", fill='black')
    img.save(filename)
    return filename

def test_upload_endpoint():
    """Test the upload endpoint"""
    print("=" * 70)
    print("TEST: Upload & Extract API Endpoint")
    print("=" * 70)
    
    API_URL = "http://localhost:8000/api/v1"
    
    # Create test images
    print("\n[1] Creating test images...")
    model_image = create_test_image("temp_model.png")
    student_image = create_test_image("temp_student.png")
    print(f"    Model: {model_image}")
    print(f"    Student: {student_image}")
    
    try:
        # Step 1: Upload files
        print("\n[2] Uploading files to backend...")
        with open(model_image, 'rb') as m, open(student_image, 'rb') as s:
            files = {
                'model_answer': ('model.png', m, 'image/png'),
                'student_answer': ('student.png', s, 'image/png'),
            }
            data = {
                'question_type': 'descriptive',
                'subject': 'Science',
                'max_marks': '10'
            }
            
            response = requests.post(
                f"{API_URL}/upload/",
                files=files,
                data=data,
                timeout=60
            )
        
        print(f"    Status: {response.status_code}")
        if response.status_code != 200:
            print(f"    Error: {response.text}")
            return False
        
        upload_data = response.json()
        print(f"    Response: {json.dumps(upload_data, indent=2)}")
        
        if not upload_data.get('success'):
            print(f"    Upload failed: {upload_data.get('message')}")
            return False
        
        evaluation_id = upload_data['data']['evaluation_id']
        print(f"    Evaluation ID: {evaluation_id}")
        
        # Step 2: Extract text with Sarvam engine
        print(f"\n[3] Extracting text with Sarvam engine...")
        response = requests.get(
            f"{API_URL}/upload/{evaluation_id}/extract-text",
            params={'ocr_engine': 'sarvam'},
            timeout=180
        )
        
        print(f"    Status: {response.status_code}")
        if response.status_code != 200:
            print(f"    Error: {response.text}")
            return False
        
        extract_data = response.json()
        print(f"    Response received")
        print(f"    OCR Engine Requested: {extract_data.get('data', {}).get('ocr_engine_requested')}")
        print(f"    OCR Engine Used: {extract_data.get('data', {}).get('ocr_engine_used')}")
        
        if extract_data.get('success'):
            print(f"\n[RESULT] SUCCESS!")
            print(f"    Model text extracted: {len(extract_data['data']['model_answer']['text'])} characters")
            print(f"    Student text extracted: {len(extract_data['data']['student_answer']['text'])} characters")
            print(f"    Note: {extract_data['data'].get('note', 'None')}")
            return True
        else:
            print(f"\n[ERROR] Extraction failed")
            print(f"    Message: {extract_data.get('message')}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Cannot connect to API")
        print("        Is the backend running on http://localhost:8000?")
        print("        Start it with: python -m uvicorn api.main:app --reload")
        return False
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if os.path.exists(model_image):
            os.remove(model_image)
        if os.path.exists(student_image):
            os.remove(student_image)
        print("\n[4] Cleaned up test images")

if __name__ == '__main__':
    success = test_upload_endpoint()
    exit(0 if success else 1)
