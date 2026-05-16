"""
Test Sarvam AI Parse-Image Endpoint
====================================
Testing the correct endpoint that might actually work
"""

import os
import sys
import requests
import tempfile
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))
from config.settings import settings

def test_parse_image_endpoint():
    """Test the /parse-image endpoint"""
    print("\n" + "="*80)
    print("Testing Sarvam AI /parse-image Endpoint")
    print("="*80)
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create simple test image
        img = Image.new('RGB', (400, 200), color='white')
        d = ImageDraw.Draw(img)
        d.text((20, 50), "Hello World Test", fill='black')
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            test_image = f.name
        
        api_key = settings.SARVAM_API_KEY
        
        # Test /parse-image endpoint
        endpoints = [
            "https://api.sarvam.ai/parse-image",
            "https://api.sarvam.ai/v1/parse-image",
            "https://api.sarvam.ai/parse",
            "https://api.sarvam.ai/v1/ocr",
            "https://api.sarvam.ai/ocr",
        ]
        
        with open(test_image, 'rb') as f:
            image_data = f.read()
        
        headers = {
            'Authorization': f'Bearer {api_key}',
        }
        
        files = {
            'file': ('test.png', image_data)
        }
        
        data = {
            'threshold': '0.5',
            'page_number': '1',
            'language': 'en',
        }
        
        for endpoint in endpoints:
            print(f"\nTesting: {endpoint}")
            try:
                response = requests.post(
                    endpoint,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=30
                )
                
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"  ✓ SUCCESS!")
                    result = response.json()
                    text = result.get('text', '') or result.get('output', {}).get('text', '')
                    if text:
                        print(f"  Extracted: {text[:80]}")
                    return endpoint
                elif response.status_code == 404:
                    print(f"  Status: 404 Not Found")
                elif response.status_code == 401:
                    print(f"  Status: 401 Unauthorized")
                else:
                    print(f"  Response: {response.text[:100]}")
                    
            except requests.exceptions.Timeout:
                print(f"  Timeout")
            except Exception as e:
                print(f"  Error: {e}")
        
        os.remove(test_image)
        return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    working_endpoint = test_parse_image_endpoint()
    
    if  working_endpoint:
        print(f"\n" + "="*80)
        print(f"✓ WORKING ENDPOINT FOUND: {working_endpoint}")
        print(f"="*80)
    else:
        print(f"\n" + "="*80)
        print(f"✗ NO WORKING ENDPOINT FOUND")
        print("="*80)
        print("The Sarvam API endpoint might have changed.")
        print("Visit https://console.sarvam.ai/ to check your API documentation")
