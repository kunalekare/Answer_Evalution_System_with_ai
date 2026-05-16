"""
Debug Sarvam AI Hindi Extraction Issue
======================================
This script tests different approaches to send language parameter to Sarvam API
and logs exactly what's being sent and received.
"""

import os
import sys

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import logging
import requests
import base64
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SarvamDebug")


def create_simple_hindi_image():
    """Create a simple test image with Hindi text"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import tempfile
        
        img = Image.new('RGB', (400, 200), color='white')
        d = ImageDraw.Draw(img)
        
        # Try to find a Hindi font
        font_paths = [
            "/usr/share/fonts/opentype/noto/NotoSansDevanagari-Regular.ttf",
            "C:\\Windows\\Fonts\\NotoSansDevanagari-Regular.ttf",
            "C:\\Windows\\Fonts\\Devanagari.ttf",
        ]
        
        font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, 32)
                    break
                except:
                    pass
        
        # Hindi text: "यह एक परीक्षण है" (This is a test)
        if font:
            d.text((20, 50), "यह एक परीक्षण है", fill='black', font=font)
        else:
            # English fallback
            d.text((20, 50), "This is a test", fill='black')
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            return f.name
    except Exception as e:
        logger.error(f"Failed to create test image: {e}")
        return None


def test_method_1_form_data_with_language():
    """Method 1: Form data with language parameter (current approach)"""
    print("\n" + "="*80)
    print("METHOD 1: Form Data with Language Parameter (Current)")
    print("="*80)
    
    try:
        api_key = settings.SARVAM_API_KEY
        api_url = settings.SARVAM_API_URL
        
        image_path = create_simple_hindi_image()
        if not image_path:
            logger.error("Failed to create test image")
            return
        
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
        }
        
        files = {
            'file': (os.path.basename(image_path), image_data)
        }
        
        # Method 1: language in form data
        data = {
            'threshold': '0.5',
            'page_number': '1',
            'language': 'hi',  # Hindi
        }
        
        print(f"\nRequest Details:")
        print(f"  URL: {api_url}")
        print(f"  Method: POST")
        print(f"  Headers: {dict(headers)}")
        print(f"  Form Data: {data}")
        print(f"  File: {os.path.basename(image_path)} ({len(image_data)} bytes)")
        
        logger.info(f"Sending request to {api_url}")
        response = requests.post(
            api_url,
            headers=headers,
            files=files,
            data=data,
            timeout=120
        )
        
        print(f"\nResponse:")
        print(f"  Status Code: {response.status_code}")
        print(f"  Headers: {dict(response.headers)}")
        print(f"  Body (first 200 chars): {response.text[:200]}")
        
        if response.status_code == 200:
            result = response.json()
            text = result.get('text', '') or result.get('output', {}).get('text', '')
            print(f"\n✓ SUCCESS!")
            print(f"  Extracted Text: {text[:100]}")
            print(f"  Text Length: {len(text)}")
            return True
        else:
            print(f"\n✗ FAILED!")
            print(f"  Full Response: {response.text}")
            return False
        
    except Exception as e:
        logger.error(f"Method 1 error: {e}", exc_info=True)
        return False
    finally:
        if 'image_path' in locals() and os.path.exists(image_path):
            os.remove(image_path)


def test_method_2_json_body():
    """Method 2: JSON body instead of form data"""
    print("\n" + "="*80)
    print("METHOD 2: JSON Body with Base64 Image")
    print("="*80)
    
    try:
        api_key = settings.SARVAM_API_KEY
        api_url = settings.SARVAM_API_URL
        
        image_path = create_simple_hindi_image()
        if not image_path:
            logger.error("Failed to create test image")
            return
        
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Convert to base64
        b64_image = base64.b64encode(image_data).decode('utf-8')
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
        
        # Method 2: JSON body with base64
        data = {
            'image': b64_image,
            'threshold': 0.5,
            'page_number': 1,
            'language': 'hi',
        }
        
        print(f"\nRequest Details:")
        print(f"  URL: {api_url}")
        print(f"  Method: POST (JSON)")
        print(f"  Headers: {dict(headers)}")
        print(f"  Body Keys: {list(data.keys())}")
        print(f"  Base64 Image Length: {len(b64_image)}")
        
        logger.info(f"Sending JSON request to {api_url}")
        response = requests.post(
            api_url,
            headers=headers,
            json=data,
            timeout=120
        )
        
        print(f"\nResponse:")
        print(f"  Status Code: {response.status_code}")
        print(f"  Body (first 200 chars): {response.text[:200]}")
        
        if response.status_code == 200:
            result = response.json()
            text = result.get('text', '') or result.get('output', {}).get('text', '')
            print(f"\n✓ SUCCESS!")
            print(f"  Extracted Text: {text[:100]}")
            return True
        else:
            print(f"\n✗ FAILED!")
            print(f"  Full Response: {response.text}")
            return False
        
    except Exception as e:
        logger.error(f"Method 2 error: {e}", exc_info=True)
        return False
    finally:
        if 'image_path' in locals() and os.path.exists(image_path):
            os.remove(image_path)


def test_method_3_url_parameter():
    """Method 3: Language as URL parameter"""
    print("\n" + "="*80)
    print("METHOD 3: Language as URL Parameter")
    print("="*80)
    
    try:
        api_key = settings.SARVAM_API_KEY
        api_url = settings.SARVAM_API_URL
        
        image_path = create_simple_hindi_image()
        if not image_path:
            logger.error("Failed to create test image")
            return
        
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
        }
        
        files = {
            'file': (os.path.basename(image_path), image_data)
        }
        
        # Method 3: language as URL parameter
        params = {
            'language': 'hi',
            'threshold': '0.5',
        }
        
        url_with_params = f"{api_url}?language=hi&threshold=0.5"
        
        print(f"\nRequest Details:")
        print(f"  URL: {url_with_params}")
        print(f"  Method: POST (with URL params)")
        print(f"  Headers: {dict(headers)}")
        print(f"  File: {os.path.basename(image_path)}")
        
        logger.info(f"Sending request with URL parameters")
        response = requests.post(
            api_url,
            headers=headers,
            files=files,
            params=params,
            timeout=120
        )
        
        print(f"\nResponse:")
        print(f"  Status Code: {response.status_code}")
        print(f"  Body (first 200 chars): {response.text[:200]}")
        
        if response.status_code == 200:
            result = response.json()
            text = result.get('text', '') or result.get('output', {}).get('text', '')
            print(f"\n✓ SUCCESS!")
            print(f"  Extracted Text: {text[:100]}")
            return True
        else:
            print(f"\n✗ FAILED!")
            print(f"  Full Response: {response.text}")
            return False
        
    except Exception as e:
        logger.error(f"Method 3 error: {e}", exc_info=True)
        return False
    finally:
        if 'image_path' in locals() and os.path.exists(image_path):
            os.remove(image_path)


def test_method_4_header_parameter():
    """Method 4: Language as custom header"""
    print("\n" + "="*80)
    print("METHOD 4: Language as Custom Header")
    print("="*80)
    
    try:
        api_key = settings.SARVAM_API_KEY
        api_url = settings.SARVAM_API_URL
        
        image_path = create_simple_hindi_image()
        if not image_path:
            logger.error("Failed to create test image")
            return
        
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
            'X-Language': 'hi',  # Custom header
        }
        
        files = {
            'file': (os.path.basename(image_path), image_data)
        }
        
        data = {
            'threshold': '0.5',
            'page_number': '1',
        }
        
        print(f"\nRequest Details:")
        print(f"  URL: {api_url}")
        print(f"  Method: POST")
        print(f"  Headers: {dict(headers)}")
        print(f"  Form Data: {data}")
        print(f"  File: {os.path.basename(image_path)}")
        
        logger.info(f"Sending request with X-Language header")
        response = requests.post(
            api_url,
            headers=headers,
            files=files,
            data=data,
            timeout=120
        )
        
        print(f"\nResponse:")
        print(f"  Status Code: {response.status_code}")
        print(f"  Body (first 200 chars): {response.text[:200]}")
        
        if response.status_code == 200:
            result = response.json()
            text = result.get('text', '') or result.get('output', {}).get('text', '')
            print(f"\n✓ SUCCESS!")
            print(f"  Extracted Text: {text[:100]}")
            return True
        else:
            print(f"\n✗ FAILED!")
            print(f"  Full Response: {response.text}")
            return False
        
    except Exception as e:
        logger.error(f"Method 4 error: {e}", exc_info=True)
        return False
    finally:
        if 'image_path' in locals() and os.path.exists(image_path):
            os.remove(image_path)


def test_api_without_language():
    """Test what happens when we DON'T send language (current problem)"""
    print("\n" + "="*80)
    print("BASELINE: Without Language Parameter (Current Problem)")
    print("="*80)
    
    try:
        api_key = settings.SARVAM_API_KEY
        api_url = settings.SARVAM_API_URL
        
        image_path = create_simple_hindi_image()
        if not image_path:
            logger.error("Failed to create test image")
            return
        
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
        }
        
        files = {
            'file': (os.path.basename(image_path), image_data)
        }
        
        # NO language parameter
        data = {
            'threshold': '0.5',
            'page_number': '1',
        }
        
        print(f"\nRequest Details:")
        print(f"  URL: {api_url}")
        print(f"  Form Data: {data}")
        print(f"  NOTE: NO language parameter")
        
        response = requests.post(
            api_url,
            headers=headers,
            files=files,
            data=data,
            timeout=120
        )
        
        print(f"\nResponse:")
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            text = result.get('text', '') or result.get('output', {}).get('text', '')
            print(f"  Extracted Text: {text[:100]}")
            print(f"  Text Length: {len(text)}")
            print(f"\n✗ THIS IS THE GARBLED OUTPUT PROBLEM!")
        
    except Exception as e:
        logger.error(f"Baseline test error: {e}", exc_info=True)
    finally:
        if 'image_path' in locals() and os.path.exists(image_path):
            os.remove(image_path)


def main():
    print("\n")
    print("=" * 80)
    print("SARVAM AI HINDI EXTRACTION - DEBUGGING SCRIPT")
    print("Testing different methods to send language parameter")
    print("=" * 80)
    
    print(f"\nConfiguration:")
    print(f"  API Key: {settings.SARVAM_API_KEY[:20]}...")
    print(f"  API URL: {settings.SARVAM_API_URL}")
    
    # Test baseline (current problem)
    test_api_without_language()
    
    # Test different methods
    results = {
        "Method 1 (Form Data)": test_method_1_form_data_with_language(),
        "Method 2 (JSON Body)": test_method_2_json_body(),
        "Method 3 (URL Param)": test_method_3_url_parameter(),
        "Method 4 (Header)": test_method_4_header_parameter(),
    }
    
    print("\n" + "="*80)
    print("SUMMARY OF RESULTS")
    print("="*80)
    
    for method, success in results.items():
        if success is None:
            status = "⚠  SKIPPED"
        elif success:
            status = "✓ WORKS"
        else:
            status = "✗ FAILED"
        print(f"{method:<40} {status}")
    
    working_methods = [m for m, s in results.items() if s is True]
    if working_methods:
        print(f"\n✓ FOUND {len(working_methods)} working method(s)!")
        print(f"  Will use: {working_methods[0]}")
    else:
        print(f"\n✗ NO WORKING METHODS FOUND")
        print(f"  The Sarvam API endpoint might have changed or require different format")


if __name__ == "__main__":
    main()
