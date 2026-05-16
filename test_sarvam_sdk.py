#!/usr/bin/env python3
"""
Test Sarvam AI SDK Direct Extraction
=====================================
Tests the SarvamAI Python SDK for text extraction
"""

import sys
import os
import tempfile
from pathlib import Path

def test_sarvam_sdk_installation():
    """Check if Sarvam SDK is installed"""
    print("\n" + "="*70)
    print("TEST 1: Checking Sarvam AI SDK Installation")
    print("="*70)
    
    try:
        from sarvamai import SarvamAI
        print("✅ SarvamAI SDK is installed")
        return True
    except ImportError as e:
        print(f"❌ SarvamAI SDK not installed: {e}")
        print("\nInstall it with:")
        print("  pip install sarvamai")
        return False

def test_sarvam_sdk_connection():
    """Test connection to Sarvam API using SDK"""
    print("\n" + "="*70)
    print("TEST 2: Testing Sarvam SDK Connection")
    print("="*70)
    
    from config.settings import settings
    
    api_key = getattr(settings, 'SARVAM_API_KEY', None)
    
    if not api_key:
        print("❌ SARVAM_API_KEY not configured in settings")
        return False
    
    masked_key = api_key[:15] + "..." + api_key[-5:] if len(api_key) > 20 else "***"
    print(f"API Key: {masked_key}")
    
    try:
        from sarvamai import SarvamAI
        
        print("Initializing SarvamAI client...")
        client = SarvamAI(api_subscription_key=api_key)
        print("✅ SarvamAI client initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize SarvamAI: {type(e).__name__}: {e}")
        return False

def test_sarvam_sdk_extraction():
    """Test actual text extraction with sample image"""
    print("\n" + "="*70)
    print("TEST 3: Testing Text Extraction with SDK")
    print("="*70)
    
    from config.settings import settings
    from sarvamai import SarvamAI
    from PIL import Image, ImageDraw
    import tempfile
    
    api_key = getattr(settings, 'SARVAM_API_KEY', None)
    
    if not api_key:
        print("❌ SARVAM_API_KEY not configured")
        return False
    
    # Create a sample image with handwritten text
    print("Creating sample handwritten text image...")
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw some text
    draw.text((50, 50), "This is a handwritten", fill='black')
    draw.text((50, 100), "test document", fill='black')
    draw.text((50, 150), "for Sarvam AI", fill='black')
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        temp_image_path = f.name
        img.save(temp_image_path)
    
    try:
        print(f"Sample image created: {temp_image_path}")
        
        # Initialize client
        client = SarvamAI(api_subscription_key=api_key)
        
        # Create document intelligence job
        print("\nCreating document intelligence job...")
        job = client.document_intelligence.create_job(
            language="en-IN",
            output_format="md"
        )
        print(f"✅ Job created: {job.job_id}")
        
        # Upload file
        print("Uploading image to Sarvam AI...")
        job.upload_file(temp_image_path)
        print("✅ File uploaded")
        
        # Start processing
        print("Starting processing...")
        job.start()
        print("✅ Job started")
        
        # Wait for completion
        print("Waiting for completion (this may take a minute)...")
        status = job.wait_until_complete()
        print(f"✅ Job completed: {status.job_state}")
        
        # Get page metrics
        try:
            metrics = job.get_page_metrics()
            print(f"Page metrics: {metrics}")
        except:
            print("(Metrics not available)")
        
        # Download output
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "output")
            print(f"\nDownloading output to {temp_dir}...")
            job.download_output(output_path)
            print("✅ Output downloaded")
            
            # Try to read extracted text
            output_files = list(Path(temp_dir).glob("**/*"))
            if output_files:
                print(f"Output files: {len(output_files)} file(s) extracted")
                
                # Try to read text files
                for file in output_files:
                    if file.is_file() and file.suffix in ['.txt', '.md', '.html']:
                        print(f"\n📄 Content from {file.name}:")
                        try:
                            with open(file, 'r', encoding='utf-8') as f:
                                content = f.read()
                                print(content[:500] + ("..." if len(content) > 500 else ""))
                        except:
                            pass
            else:
                print("⚠️ No output files generated")
        
        print("\n✅ Sarvam SDK EXTRACTION SUCCESSFUL!")
        return True
        
    except Exception as e:
        print(f"\n❌ Extraction failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        try:
            os.remove(temp_image_path)
        except:
            pass

def summary():
    """Print test summary"""
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    print("\n✅ NEXT STEPS:")
    print("1. Install Sarvam SDK: pip install sarvamai")
    print("2. Verify API key at: https://console.sarvam.ai/")
    print("3. Update OCR service to use SDK instead of REST API")
    print("4. Test extraction with your actual documents")

def main():
    print("\n" + "="*70)
    print("SARVAM AI SDK TEXT EXTRACTION TEST")
    print("Testing the SarvamAI Python SDK for document processing")
    print("="*70)
    
    results = {}
    
    # Test 1: SDK Installation
    results['sdk_installed'] = test_sarvam_sdk_installation()
    
    if not results['sdk_installed']:
        print("\n⚠️  SarvamAI SDK not installed. Install it first:")
        print("  pip install sarvamai")
        return 1
    
    # Test 2: Connection
    results['sdk_connection'] = test_sarvam_sdk_connection()
    
    if not results['sdk_connection']:
        print("\n⚠️  Could not connect to Sarvam API")
        print("  Check your API key and internet connection")
        return 1
    
    # Test 3: Extraction
    results['sdk_extraction'] = test_sarvam_sdk_extraction()
    
    summary()
    
    if all(results.values()):
        print("\n✅ ALL TESTS PASSED - Sarvam SDK is working!")
        return 0
    else:
        print("\n❌ Some tests failed - See details above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
