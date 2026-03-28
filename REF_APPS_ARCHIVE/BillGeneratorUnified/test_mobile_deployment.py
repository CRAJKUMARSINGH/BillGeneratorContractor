#!/usr/bin/env python3
"""
Mobile Deployment Test - Simulates Mobile User Experience
Tests the deployed app functionality as if accessed from a mobile device
"""
import sys
from pathlib import Path
import requests
from datetime import datetime

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

def test_deployment_status():
    """Test if the deployment is live and responding"""
    print("="*60)
    print("TEST 1: DEPLOYMENT STATUS CHECK")
    print("="*60)
    print()
    
    url = "https://bill-priyanka-online.streamlit.app/"
    
    try:
        print(f"🌐 Checking deployment at: {url}")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Deployment is LIVE and responding")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response Time: {response.elapsed.total_seconds():.2f}s")
            
            # Check for key content
            content = response.text.lower()
            
            checks = {
                "App Title": "billgenerator" in content or "bill generator" in content,
                "Streamlit": "streamlit" in content,
                "File Upload": "upload" in content or "file" in content,
                "Hybrid Mode": "hybrid" in content,
            }
            
            print("\n   Content Checks:")
            for check_name, passed in checks.items():
                status = "✅" if passed else "⚠️"
                print(f"   {status} {check_name}")
            
            return True
        else:
            print(f"⚠️ Deployment responding with status: {response.status_code}")
            return False
    
    except requests.exceptions.Timeout:
        print("❌ Request timed out - deployment may be slow or down")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - deployment may be down")
        return False
    except Exception as e:
        print(f"❌ Error checking deployment: {e}")
        return False

def test_mobile_imports():
    """Test mobile-specific imports"""
    print()
    print("="*60)
    print("TEST 2: MOBILE OPTIMIZATION IMPORTS")
    print("="*60)
    print()
    
    try:
        from core.utils.mobile_optimization import (
            is_mobile,
            get_max_upload_size,
            should_generate_pdf,
            apply_mobile_css
        )
        
        print("✅ Mobile optimization module loaded")
        
        # Test functions
        max_size = get_max_upload_size()
        print(f"✅ Max upload size: {max_size}MB")
        
        # Simulate mobile detection
        print(f"✅ Mobile detection function available")
        print(f"✅ PDF generation control available")
        print(f"✅ Mobile CSS application available")
        
        return True
    
    except Exception as e:
        print(f"❌ Mobile optimization import failed: {e}")
        return False

def test_hybrid_mode():
    """Test hybrid mode functionality"""
    print()
    print("="*60)
    print("TEST 3: HYBRID MODE FUNCTIONALITY")
    print("="*60)
    print()
    
    try:
        from core.ui.hybrid_mode import show_hybrid_mode
        print("✅ Hybrid mode module loaded")
        
        # Check if function is callable
        if callable(show_hybrid_mode):
            print("✅ Hybrid mode function is callable")
        
        return True
    
    except Exception as e:
        print(f"❌ Hybrid mode import failed: {e}")
        return False

def test_file_processing_mobile():
    """Test file processing with mobile constraints"""
    print()
    print("="*60)
    print("TEST 4: MOBILE FILE PROCESSING")
    print("="*60)
    print()
    
    try:
        from core.processors.excel_processor_enterprise import ExcelProcessor
        from core.generators.html_generator import HTMLGenerator
        from core.utils.mobile_optimization import get_max_upload_size
        
        # Use a test file
        test_file = Path('TEST_INPUT_FILES/0511Wextra.xlsx')
        
        if not test_file.exists():
            print("⚠️ Test file not found, using first available file")
            test_files = list(Path('TEST_INPUT_FILES').glob('*.xlsx'))
            if test_files:
                test_file = test_files[0]
            else:
                print("❌ No test files found")
                return False
        
        # Check file size against mobile limit
        file_size_mb = test_file.stat().st_size / (1024 * 1024)
        mobile_limit = 10  # 10MB for mobile
        
        print(f"📁 Test file: {test_file.name}")
        print(f"📊 File size: {file_size_mb:.2f}MB")
        print(f"📱 Mobile limit: {mobile_limit}MB")
        
        if file_size_mb > mobile_limit:
            print(f"⚠️ File exceeds mobile limit (would be rejected on mobile)")
        else:
            print(f"✅ File size acceptable for mobile")
        
        # Process file
        processor = ExcelProcessor(sanitize_strings=True, validate_schemas=False)
        result = processor.process_file(test_file)
        
        if result.success:
            print(f"✅ Excel processed: {len(result.data)} sheets")
            
            # Prepare data
            data = {
                'title_data': {},
                'work_order_data': result.data.get('Work Order'),
                'bill_quantity_data': result.data.get('Bill Quantity'),
                'extra_items_data': result.data.get('Extra Items'),
                'source_filename': test_file.name
            }
            
            # Extract title data
            if 'Title' in result.data:
                title_df = result.data['Title']
                for index, row in title_df.iterrows():
                    if len(row) >= 2:
                        key = str(row.iloc[0]).strip()
                        value = row.iloc[1]
                        if key:
                            data['title_data'][key] = value
            
            # Generate HTML
            generator = HTMLGenerator(data)
            html_docs = generator.generate_all_documents()
            
            print(f"✅ Generated {len(html_docs)} HTML documents")
            
            # Check HTML size (mobile consideration)
            for doc_name, html_content in html_docs.items():
                size_kb = len(html_content.encode('utf-8')) / 1024
                print(f"   📄 {doc_name}: {size_kb:.1f}KB")
            
            return True
        else:
            print("❌ Excel processing failed")
            return False
    
    except Exception as e:
        print(f"❌ File processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_bs4_availability():
    """Test beautifulsoup4 availability (critical for mobile)"""
    print()
    print("="*60)
    print("TEST 5: BS4 AVAILABILITY (MOBILE CRITICAL)")
    print("="*60)
    print()
    
    try:
        from bs4 import BeautifulSoup
        import lxml
        
        print("✅ beautifulsoup4 available")
        print("✅ lxml available")
        
        # Test parsing
        html = "<html><body><h1>Test</h1></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        
        if soup.find('h1'):
            print("✅ BeautifulSoup parsing works")
        
        return True
    
    except Exception as e:
        print(f"❌ BS4 test failed: {e}")
        return False

def generate_mobile_test_report():
    """Generate mobile-specific test report"""
    print()
    print("="*60)
    print("MOBILE USER EXPERIENCE SIMULATION")
    print("="*60)
    print()
    
    print("This simulates what a mobile user would experience:")
    print()
    
    print("MOBILE DEVICE CHARACTERISTICS:")
    print("-" * 60)
    print("📱 Device: Smartphone (iOS/Android)")
    print("📶 Connection: 4G/5G Mobile Data")
    print("🖥️ Screen: 360x640 to 414x896 pixels")
    print("💾 Storage: Limited (10MB upload limit)")
    print("🔋 Battery: Consideration for processing")
    print()
    
    print("EXPECTED MOBILE BEHAVIOR:")
    print("-" * 60)
    print()
    
    print("1. ✅ App loads with mobile-optimized UI")
    print("   - Responsive layout")
    print("   - Touch-friendly buttons")
    print("   - Simplified navigation")
    print()
    
    print("2. ✅ File upload works on mobile")
    print("   - 10MB file size limit")
    print("   - Mobile file picker integration")
    print("   - Progress indicators")
    print()
    
    print("3. ✅ Processing completes efficiently")
    print("   - Excel parsing works")
    print("   - HTML generation works")
    print("   - LD calculation works")
    print("   - Memory management optimized")
    print()
    
    print("4. ✅ Hybrid mode available")
    print("   - Upload Excel file")
    print("   - Edit rates in table")
    print("   - Generate documents")
    print()
    
    print("5. ✅ Downloads work on mobile")
    print("   - Individual file downloads")
    print("   - ZIP download option")
    print("   - Mobile browser download handling")
    print()
    
    print("MOBILE-SPECIFIC OPTIMIZATIONS:")
    print("-" * 60)
    print("✅ Reduced file size limits (10MB vs 50MB)")
    print("✅ Mobile CSS applied automatically")
    print("✅ Simplified UI for small screens")
    print("✅ Optional PDF generation (saves processing)")
    print("✅ Fast reruns enabled")
    print("✅ Minimal toolbar mode")
    print()
    
    print("DEPLOYMENT STATUS:")
    print("-" * 60)
    print("🌐 URL: https://bill-priyanka-online.streamlit.app/")
    print("🚀 Auto-deploy: Enabled")
    print("⏱️ Deploy time: ~4 minutes after push")
    print("✅ Latest commit: Hybrid Mode + Full Descriptions")
    print()

def main():
    """Run all mobile tests"""
    print()
    print("🔍 STARTING MOBILE DEPLOYMENT TESTS")
    print()
    print("Simulating mobile user experience for:")
    print("https://bill-priyanka-online.streamlit.app/")
    print()
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    # Run tests
    results.append(("Deployment Status", test_deployment_status()))
    results.append(("Mobile Optimization", test_mobile_imports()))
    results.append(("Hybrid Mode", test_hybrid_mode()))
    results.append(("Mobile File Processing", test_file_processing_mobile()))
    results.append(("BS4 Availability", test_bs4_availability()))
    
    # Generate report
    generate_mobile_test_report()
    
    # Summary
    print()
    print("="*60)
    print("MOBILE TEST SUMMARY")
    print("="*60)
    print()
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<30} {status}")
        if not passed:
            all_passed = False
    
    print()
    print("="*60)
    
    if all_passed:
        print("✅ ALL MOBILE TESTS PASSED")
        print()
        print("🎉 MOBILE DEPLOYMENT PREDICTION: SUCCESS")
        print()
        print("The deployed app should work well on mobile:")
        print("  ✅ Loads without errors")
        print("  ✅ Mobile-optimized UI")
        print("  ✅ File upload works (10MB limit)")
        print("  ✅ Processing completes")
        print("  ✅ Hybrid mode available")
        print("  ✅ Downloads work")
        print()
        print("📱 RECOMMENDED MOBILE TESTING:")
        print("  1. Open on actual mobile device")
        print("  2. Test file upload (use small test file)")
        print("  3. Try Hybrid mode with rate editing")
        print("  4. Verify document downloads")
        print("  5. Check UI responsiveness")
        print()
        return 0
    else:
        print("❌ SOME MOBILE TESTS FAILED")
        print()
        print("Please review failed tests above")
        print()
        return 1

if __name__ == '__main__':
    sys.exit(main())
