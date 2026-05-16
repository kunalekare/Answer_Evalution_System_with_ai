#!/usr/bin/env python3
"""
Sarvam AI API Key Diagnostic Tool
==================================
Verifies Sarvam API key configuration and tests connectivity.
"""

import sys
import requests
import json
from pathlib import Path
from config.settings import settings

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def check_api_key():
    """Check if Sarvam API key is configured"""
    print_header("1. SARVAM API KEY CONFIGURATION")
    
    api_key = getattr(settings, 'SARVAM_API_KEY', None)
    
    if not api_key:
        print("❌ ERROR: SARVAM_API_KEY is NOT configured!")
        print("\n📋 Solution:")
        print("   1. Open .env file (or create one from .env.example)")
        print("   2. Add or update: SARVAM_API_KEY=sk_xxxxxxxxxxxxx")
        print("   3. Get API key from: https://console.sarvam.ai/")
        return False
    
    # Mask the key for security
    masked_key = api_key[:15] + "..." + api_key[-5:] if len(api_key) > 20 else "***"
    print(f"✅ API Key Found: {masked_key}")
    print(f"   Full length: {len(api_key)} characters")
    
    if not api_key.startswith("sk_"):
        print("⚠️  WARNING: API key doesn't start with 'sk_' (might be invalid)")
    
    return True

def check_endpoint():
    """Check if Sarvam API endpoint is configured"""
    print_header("2. SARVAM API ENDPOINT CONFIGURATION")
    
    endpoint = getattr(settings, 'SARVAM_API_URL', None)
    
    if not endpoint:
        print("❌ ERROR: SARVAM_API_URL is NOT configured!")
        return False
    
    print(f"✅ Endpoint Configured: {endpoint}")
    return True

def test_api_connection():
    """Test actual connection to Sarvam API"""
    print_header("3. TESTING SARVAM API CONNECTION")
    
    api_key = getattr(settings, 'SARVAM_API_KEY', None)
    endpoint = getattr(settings, 'SARVAM_API_URL', None)
    
    if not api_key or not endpoint:
        print("⚠️  Skipping - API key or endpoint not configured")
        return False
    
    print(f"Contacting: {endpoint}")
    print(f"Auth: Bearer {api_key[:15]}...\n")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
    }
    
    try:
        # Test with a simple HEAD request first
        print("Attempting connection...")
        response = requests.head(endpoint, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Connection successful!")
            return True
        elif response.status_code == 401:
            print("❌ AUTHENTICATION FAILED (401)")
            print("   Possible causes:")
            print("   - Invalid API key")
            print("   - Expired API key")
            print("   - Wrong API key format")
            print("\n📋 Solution:")
            print("   1. Go to: https://console.sarvam.ai/")
            print("   2. Generate a new API key")
            print("   3. Update .env file with new key")
            return False
        elif response.status_code == 404:
            print("❌ ENDPOINT NOT FOUND (404)")
            print("   The API endpoint URL may have changed")
            print(f"   Current: {endpoint}")
            print("\n📋 Testing alternative endpoints...")
            return test_alternative_endpoints(api_key)
        elif response.status_code == 429:
            print("⚠️  RATE LIMIT (429)")
            print("   Too many requests - try again later")
            return False
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT - Connection took too long")
        print("   The API server might be down or unreachable")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR - Cannot reach API")
        print("   Possible causes:")
        print("   - No internet connection")
        print("   - API domain is unreachable")
        print("   - Firewall/VPN blocking the connection")
        return False
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        return False

def test_alternative_endpoints(api_key):
    """Test alternative Sarvam API endpoints"""
    print("\n🔍 Testing alternative Sarvam endpoints:\n")
    
    alternatives = [
        ("Parse Image API", "https://api.sarvam.ai/parse-image"),
        ("v2 Document Intelligence", "https://api.sarvam.ai/v2/document-intelligence"),
        ("OCR Endpoint", "https://api.sarvam.ai/v1/ocr"),
        ("Vision OCR", "https://api.sarvam.ai/v1/vision/ocr"),
        ("Text Extract", "https://api.sarvam.ai/v1/text/extract"),
    ]
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
    }
    
    found_working = False
    
    for name, url in alternatives:
        try:
            response = requests.head(url, headers=headers, timeout=5)
            status = response.status_code
            
            if status == 200:
                print(f"   ✅ {name}")
                print(f"      URL: {url}")
                print(f"      Status: {status}\n")
                found_working = True
            elif status == 404:
                print(f"   ❌ {name} - Not found (404)")
            elif status == 401:
                print(f"   ⚠️  {name} - Auth failed (401)")
            else:
                print(f"   ⚠️  {name} - Status {status}")
        except Exception as e:
            print(f"   ❌ {name} - Error: {str(e)[:40]}")
    
    if found_working:
        print("\n📋 Found working endpoint! Update your .env file:")
        print("   SARVAM_API_URL=<working_url_from_above>")
    else:
        print("\n❌ No working alternative endpoints found")
        print("\n📋 Next steps:")
        print("   1. Visit: https://console.sarvam.ai/")
        print("   2. Check API documentation and available endpoints")
        print("   3. Verify your API key is active")
        print("   4. Check your account quota/billing")
    
    return found_working

def test_with_sample_image():
    """Test Sarvam API with a sample image (if available)"""
    print_header("4. TESTING WITH SAMPLE IMAGE")
    
    api_key = getattr(settings, 'SARVAM_API_KEY', None)
    endpoint = getattr(settings, 'SARVAM_API_URL', None)
    
    if not api_key or not endpoint:
        print("⚠️  Skipping - API key or endpoint not configured")
        return False
    
    # Check if sample image exists
    sample_path = Path("test_image.png")
    if not sample_path.exists():
        print("⚠️  No test image found (test_image.png)")
        print("   Create a sample handwritten image to test full extraction")
        return False
    
    print(f"Found test image: {sample_path}")
    print("Attempting to extract text...\n")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
    }
    
    try:
        with open(sample_path, 'rb') as f:
            files = {'file': (sample_path.name, f)}
            data = {
                'threshold': '0.5',
                'language': 'en',
            }
            
            response = requests.post(
                endpoint,
                headers=headers,
                files=files,
                data=data,
                timeout=120
            )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            text = result.get('text', '') or result.get('output', {}).get('text', '')
            if text:
                print(f"✅ Extraction successful!")
                print(f"Extracted {len(text)} characters")
                print(f"Preview: {text[:200]}...")
                return True
            else:
                print(f"⚠️  Got response but no text extracted")
                print(f"Response: {json.dumps(result, indent=2)[:300]}")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False

def print_summary():
    """Print summary and recommendations"""
    print_header("SUMMARY & RECOMMENDATIONS")
    
    api_key_ok = bool(getattr(settings, 'SARVAM_API_KEY', None))
    endpoint_ok = bool(getattr(settings, 'SARVAM_API_URL', None))
    
    print("\n✅ Configuration Status:")
    print(f"   {'✓' if api_key_ok else '✗'} API Key configured")
    print(f"   {'✓' if endpoint_ok else '✗'} Endpoint configured")
    
    if not (api_key_ok and endpoint_ok):
        print("\n⚠️  SETUP INCOMPLETE - Fix configuration above")
        return False
    
    print("\n📋 To enable Sarvam-only extraction:")
    print("   1. Set OCR_ENGINE='sarvam' in .env file")
    print("   2. Verify API key is valid and activated")
    print("   3. Ensure Sarvam API endpoint is correct")
    print("   4. Run this test again to verify connectivity")
    
    print("\n🔗 Useful Links:")
    print("   - API Console: https://console.sarvam.ai/")
    print("   - Docs: https://sarvam.ai/api-documentation")
    print("   - Support: https://support.sarvam.ai/")
    
    return True

def main():
    """Run all diagnostic checks"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║           SARVAM AI API KEY DIAGNOSTIC TOOL                        ║")
    print("║      Verifies configuration and tests API connectivity             ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    
    # Run checks
    checks = [
        ("API Key Check", check_api_key),
        ("Endpoint Check", check_endpoint),
        ("Connection Test", test_api_connection),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n❌ Error during {name}: {e}")
            results[name] = False
    
    # Print summary
    print_summary()
    
    # Final status
    print("\n" + "=" * 70)
    if all(results.values()):
        print("✅ All checks passed! Sarvam AI is ready to use")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
