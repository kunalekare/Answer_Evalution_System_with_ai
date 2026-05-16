"""
Check Sarvam AI API Models and Available Endpoints
"""
import requests
from config.settings import settings

def test_sarvam_api_models():
    """Test getting available Sarvam models"""
    api_key = settings.SARVAM_API_KEY
    
    # Sarvam API typically structures endpoints as:
    # /api/v2/{model_name} or /v1/{model_name}
    
    # Let's test the models endpoint
    endpoints = [
        "https://api.sarvam.ai/api/v2/models",
        "https://api.sarvam.ai/v2/models",
        "https://api.sarvam.ai/api/v1/models",
        "https://api.sarvam.ai/v1/models",
        "https://api.sarvam.ai/models",
        "https://api.sarvam.ai/api/v2/text/summarization",  # Test actual model
        "https://api.sarvam.ai/api/describe-image",  # For image processing
        "https://api.sarvam.ai/api/document-parsing",  # For document
    ]
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
    }
    
    print("Testing Sarvam AI Models/Endpoints...")
    print("=" * 70)
    
    for url in endpoints:
        try:
            response = requests.get(url, headers=headers, timeout=5)
            status = response.status_code
            print(f"\n{url}")
            print(f"  Status: {status}")
            if status < 400:
                print(f"  Response: {response.text[:200]}")
            else:
                print(f"  Error: {response.text[:200]}")
        except Exception as e:
            print(f"\n{url}")
            print(f"  Error: {type(e).__name__}: {str(e)[:80]}")

if __name__ == '__main__':
    test_sarvam_api_models()
