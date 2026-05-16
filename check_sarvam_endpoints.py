"""
Sarvam AI API Endpoints Reference
Based on official Sarvam AI documentation
"""

# The issue is that the endpoint has changed or is incorrect
# Let me test different possible endpoints

import requests
from config.settings import settings

def test_sarvam_endpoints():
    """Test multiple Sarvam AI endpoints to find the correct one"""
    api_key = settings.SARVAM_API_KEY
    
    # Possible endpoints (based on common Sarvam AI API patterns)
    endpoints = [
        "https://api.sarvam.ai/v1/document-intelligence",  # Current (404)
        "https://api.sarvam.ai/v2/document-intelligence",
        "https://api.sarvam.ai/v1/parse",
        "https://api.sarvam.ai/v1/ocr",
        "https://api.sarvam.ai/v1/text/extract",
        "https://api.sarvam.ai/document-intelligence",
        "https://api.sarvam.ai/parse",
        "https://api.sarvam.ai/ocr",
    ]
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
    }
    
    print("Testing Sarvam AI endpoints...")
    print("=" * 70)
    
    for url in endpoints:
        try:
            response = requests.get(url, headers=headers, timeout=5)
            status = response.status_code
            print(f"[OK] {url:<60} -> {status}")
            if status != 404 and status != 405:  # If not error
                print(f"  Response: {response.text[:100]}")
        except Exception as e:
            print(f"[ERR] {url:<60} -> ERROR: {str(e)[:40]}")
    
    print("\nRECOMMENDATION:")
    print("Check Sarvam AI console or API documentation at:")
    print("https://console.sarvam.ai/api-keys")
    print("\nOr check their API docs:")
    print("https://sarvam.ai/api-documentation")

if __name__ == '__main__':
    test_sarvam_endpoints()
