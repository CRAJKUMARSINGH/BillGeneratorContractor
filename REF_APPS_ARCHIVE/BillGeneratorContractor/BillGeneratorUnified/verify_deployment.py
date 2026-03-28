#!/usr/bin/env python3
"""
Deployment Verification Script
Checks if all required dependencies are available
"""
import sys

def check_dependencies():
    """Check if all required packages are importable"""
    
    print("="*60)
    print("DEPLOYMENT VERIFICATION")
    print("="*60)
    print()
    
    dependencies = [
        ('streamlit', 'Streamlit'),
        ('pandas', 'Pandas'),
        ('numpy', 'NumPy'),
        ('openpyxl', 'OpenPyXL'),
        ('weasyprint', 'WeasyPrint'),
        ('docx', 'python-docx'),
        ('jinja2', 'Jinja2'),
        ('PIL', 'Pillow'),
        ('num2words', 'num2words'),
        ('cairocffi', 'CairoCFFI'),
        ('cairosvg', 'CairoSVG'),
        ('tinycss2', 'TinyCSS2'),
        ('cssselect2', 'CSSSelect2'),
        ('dotenv', 'python-dotenv'),
        ('dateutil', 'python-dateutil'),
        ('pytz', 'pytz'),
        ('bs4', 'beautifulsoup4'),  # THE FIX!
        ('lxml', 'lxml'),  # THE FIX!
    ]
    
    all_ok = True
    
    print("Checking dependencies...")
    print()
    
    for module_name, package_name in dependencies:
        try:
            __import__(module_name)
            print(f"✅ {package_name:<20} - OK")
        except ImportError as e:
            print(f"❌ {package_name:<20} - MISSING")
            print(f"   Error: {e}")
            all_ok = False
    
    print()
    print("="*60)
    
    if all_ok:
        print("✅ ALL DEPENDENCIES AVAILABLE")
        print()
        print("The app should work correctly!")
        print("No 'bs4' import errors expected.")
        return 0
    else:
        print("❌ SOME DEPENDENCIES MISSING")
        print()
        print("Please install missing packages:")
        print("pip install -r requirements.txt")
        return 1

def check_files():
    """Check if all required files exist"""
    
    print()
    print("="*60)
    print("CHECKING REQUIRED FILES")
    print("="*60)
    print()
    
    from pathlib import Path
    
    required_files = [
        'requirements.txt',
        '.streamlit/config.toml',
        'app.py',
        'core/generators/base_generator.py',
        'core/generators/html_generator.py',
        'core/processors/excel_processor_enterprise.py',
        'core/utils/mobile_optimization.py',
        'templates/note_sheet_new.html',
    ]
    
    all_ok = True
    
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            all_ok = False
    
    print()
    print("="*60)
    
    if all_ok:
        print("✅ ALL REQUIRED FILES PRESENT")
        return 0
    else:
        print("❌ SOME FILES MISSING")
        return 1

def check_requirements_file():
    """Check if requirements.txt has beautifulsoup4"""
    
    print()
    print("="*60)
    print("CHECKING REQUIREMENTS.TXT")
    print("="*60)
    print()
    
    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()
        
        has_bs4 = 'beautifulsoup4' in content
        has_lxml = 'lxml' in content
        
        if has_bs4:
            print("✅ beautifulsoup4 found in requirements.txt")
        else:
            print("❌ beautifulsoup4 NOT found in requirements.txt")
        
        if has_lxml:
            print("✅ lxml found in requirements.txt")
        else:
            print("❌ lxml NOT found in requirements.txt")
        
        print()
        print("="*60)
        
        if has_bs4 and has_lxml:
            print("✅ REQUIREMENTS.TXT IS CORRECT")
            return 0
        else:
            print("❌ REQUIREMENTS.TXT NEEDS UPDATE")
            print()
            print("Add these lines to requirements.txt:")
            if not has_bs4:
                print("beautifulsoup4==4.12.3")
            if not has_lxml:
                print("lxml==5.3.0")
            return 1
    
    except FileNotFoundError:
        print("❌ requirements.txt not found!")
        return 1

def main():
    """Run all verification checks"""
    
    print()
    print("🔍 Starting deployment verification...")
    print()
    
    # Check requirements file first
    req_status = check_requirements_file()
    
    # Check if files exist
    files_status = check_files()
    
    # Check if dependencies can be imported
    deps_status = check_dependencies()
    
    # Final summary
    print()
    print("="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    print()
    
    if req_status == 0 and files_status == 0 and deps_status == 0:
        print("✅ ALL CHECKS PASSED")
        print()
        print("🚀 Ready to deploy!")
        print()
        print("Next steps:")
        print("1. Run: deploy_fix.bat (Windows) or ./deploy_fix.sh (Linux/Mac)")
        print("2. Wait for Streamlit Cloud to rebuild (~4 minutes)")
        print("3. Test at: https://bill-priyanka-online.streamlit.app")
        print()
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print()
        print("Please fix the issues above before deploying.")
        print()
        return 1

if __name__ == '__main__':
    sys.exit(main())
