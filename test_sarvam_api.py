"""
Test Sarvam AI API connection
"""
import requests
import json
from config.settings import settings

def test_sarvam_connection():
    """Test Sarvam API connection and authentication"""
    print("=" * 60)
    print("TESTING SARVAM AI API CONNECTION")
    print("=" * 60)
    
    api_url = settings.SARVAM_API_URL
    api_key = settings.SARVAM_API_KEY
    
    print(f"\nAPI URL: {api_url}")
    print(f"API Key: {api_key[:10]}...{api_key[-10:]}")
    
    # Test 1: Simple health check
    print("\n[TEST 1] Testing API endpoint with simple GET request...")
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
        }
        
        # Try GET first
        response = requests.get(
            api_url,
            headers=headers,
            timeout=10
        )
        print(f"GET Response Status: {response.status_code}")
        print(f"GET Response: {response.text[:200]}")
    except Exception as e:
        print(f"GET Error: {e}")
    
    # Test 2: Create a simple test image and try extraction
    print("\n[TEST 2] Creating test image and attempting extraction...")
    try:
        # Create a simple test image
        from PIL import Image, ImageDraw, ImageFont
        import tempfile
        import os
        
        # Create a simple image with text
        img = Image.new('RGB', (200, 100), color='white')
        d = ImageDraw.Draw(img)
        d.text((10, 10), "Test", fill='black')
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img.save(tmp.name)
            temp_image = tmp.name
        
        print(f"Created test image: {temp_image}")
        
        # Read the image for API call
        with open(temp_image, 'rb') as f:
            image_data = f.read()
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
        }
        
        files = {
            'file': ('test.png', image_data)
        }
        
        data = {
            'threshold': '0.5',
            'page_number': '1'
        }
        
        print(f"Sending POST request to {api_url}...")
        response = requests.post(
            api_url,
            headers=headers,
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text[:500]}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCCESS! Sarvam API is working")
            print(f"Result: {json.dumps(result, indent=2)}")
        elif response.status_code == 401:
            print(f"\n❌ AUTHENTICATION ERROR: Invalid API key")
            print(f"Make sure your API key is valid and has the necessary permissions")
        elif response.status_code == 403:
            print(f"\n❌ PERMISSION ERROR: API key doesn't have access to this endpoint")
        elif response.status_code == 429:
            print(f"\n❌ RATE LIMIT: Too many requests")
        else:
            print(f"\n❌ ERROR: {response.status_code}")
            
        # Clean up
        os.remove(temp_image)
        
    except Exception as e:
        print(f"POST Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_sarvam_connection()
