#!/usr/bin/env python3
"""
System Health Check and Diagnostics
Verifies all components are working correctly
"""
import sys
import os
from pathlib import Path
import importlib.util

def check_python_version():
    """Check Python version is 3.8+"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"  Python Version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  Python Version: {version.major}.{version.minor}.{version.micro} (REQUIRES 3.8+)")
        return False

def check_dependencies():
    """Check required packages are installed"""
    required = {
        'google.genai': 'google-genai',
        'openpyxl': 'openpyxl',
        'PIL': 'Pillow',
        'reportlab': 'reportlab'
    }
    
    all_installed = True
    for module, package in required.items():
        try:
            __import__(module)
            print(f"  {package}: Installed")
        except ImportError:
            print(f"  {package}: MISSING")
            all_installed = False
    
    return all_installed

def check_api_keys():
    """Check API keys are configured"""
    api_key = os.environ.get('GEMINI_API_KEY')
    
    if api_key:
        # Mask key for security
        masked = api_key[:10] + "..." + api_key[-4:]
        print(f"  Gemini API Key: Configured ({masked})")
        return True
    else:
        print(f"  Gemini API Key: NOT SET")
        return False

def check_ocr_systems():
    """Check OCR systems availability"""
    try:
        from modules.gemini_vision_parser_v2 import GeminiVisionParserV2
        parser = GeminiVisionParserV2()
        
        if parser.available:
            print(f"  Gemini Vision API: Available")
            return True
        else:
            print(f"  Gemini Vision API: NOT AVAILABLE")
            return False
    except Exception as e:
        print(f"  Gemini Vision API: ERROR - {str(e)}")
        return False

def check_file_permissions():
    """Check file system permissions"""
    test_dirs = ['INPUT_WORK_ORDER_IMAGES_TEXT', 'OUTPUT', 'logs']
    
    all_ok = True
    for dir_name in test_dirs:
        dir_path = Path(dir_name)
        
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"  {dir_name}/: Created")
            except Exception as e:
                print(f"  {dir_name}/: CANNOT CREATE - {str(e)}")
                all_ok = False
        else:
            # Test write permission
            test_file = dir_path / '.test_write'
            try:
                test_file.write_text('test')
                test_file.unlink()
                print(f"  {dir_name}/: Writable")
            except Exception as e:
                print(f"  {dir_name}/: NOT WRITABLE - {str(e)}")
                all_ok = False
    
    return all_ok

def check_internet():
    """Check internet connectivity"""
    import socket
    
    try:
        # Try to connect to Google DNS
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        print(f"  Internet: Connected")
        return True
    except OSError:
        print(f"  Internet: NOT CONNECTED (offline mode available)")
        return False

def check_sample_images():
    """Check if sample images exist"""
    work_dir = Path("INPUT_WORK_ORDER_IMAGES_TEXT")
    
    if not work_dir.exists():
        print(f"  Sample Images: Directory not found")
        return False
    
    image_files = list(work_dir.glob('*.jpg')) + list(work_dir.glob('*.png'))
    
    if image_files:
        print(f"  Sample Images: {len(image_files)} found")
        return True
    else:
        print(f"  Sample Images: None found")
        return False

def main():
    """Run all health checks"""
    
    print("\n" + "=" * 60)
    print("BILLGENERATOR SYSTEM HEALTH CHECK")
    print("=" * 60 + "\n")
    
    checks = {
        "Python Version": check_python_version(),
        "Dependencies": check_dependencies(),
        "API Keys": check_api_keys(),
        "OCR Systems": check_ocr_systems(),
        "File Permissions": check_file_permissions(),
        "Internet Connection": check_internet(),
        "Sample Images": check_sample_images(),
    }
    
    print("\n" + "=" * 60)
    
    passed = sum(checks.values())
    total = len(checks)
    
    if passed == total:
        print(f"ALL SYSTEMS OPERATIONAL ({passed}/{total})")
        print("=" * 60)
        print("\nYou're ready to generate bills!")
        print("\nRun: python extract_all_items_RELIABLE.py")
        return 0
    else:
        print(f"SOME ISSUES DETECTED ({passed}/{total} passed)")
        print("=" * 60)
        
        print("\nFailed Checks:")
        for name, status in checks.items():
            if not status:
                print(f"  - {name}")
        
        print("\nRecommended Actions:")
        
        if not checks["Dependencies"]:
            print("  1. Install dependencies: pip install -r requirements.txt")
        
        if not checks["API Keys"]:
            print("  2. Set API key: export GEMINI_API_KEY='your-key-here'")
        
        if not checks["Internet Connection"]:
            print("  3. Check internet connection (or use offline mode)")
        
        if not checks["Sample Images"]:
            print("  4. Add work order images to INPUT_WORK_ORDER_IMAGES_TEXT/")
        
        return 1

if __name__ == '__main__':
    sys.exit(main())
