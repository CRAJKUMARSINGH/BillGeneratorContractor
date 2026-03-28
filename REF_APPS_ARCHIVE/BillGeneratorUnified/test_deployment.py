#!/usr/bin/env python3
"""
Robotic Deployment Testing Suite
Tests every component before and after deployment
"""
import sys
from pathlib import Path
import traceback

class DeploymentTester:
    """Comprehensive deployment testing"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def test(self, name, func):
        """Run a test and track results"""
        try:
            print(f"Testing: {name}...", end=" ")
            func()
            print("✓ PASS")
            self.passed += 1
            return True
        except Exception as e:
            print(f"✗ FAIL: {e}")
            self.failed += 1
            self.errors.append((name, str(e), traceback.format_exc()))
            return False
    
    def test_imports(self):
        """Test all critical imports"""
        print("\n=== TESTING IMPORTS ===")
        
        self.test("Import pandas", lambda: __import__('pandas'))
        self.test("Import numpy", lambda: __import__('numpy'))
        self.test("Import openpyxl", lambda: __import__('openpyxl'))
        self.test("Import jinja2", lambda: __import__('jinja2'))
        self.test("Import weasyprint", lambda: __import__('weasyprint'))
        self.test("Import streamlit", lambda: __import__('streamlit'))
    
    def test_core_modules(self):
        """Test core application modules"""
        print("\n=== TESTING CORE MODULES ===")
        
        self.test("Import excel_processor", 
                 lambda: __import__('core.processors.excel_processor'))
        self.test("Import html_generator", 
                 lambda: __import__('core.generators.html_generator'))
        self.test("Import document_generator", 
                 lambda: __import__('core.generators.document_generator'))
        self.test("Import base_generator", 
                 lambda: __import__('core.generators.base_generator'))
    
    def test_templates(self):
        """Test template files exist"""
        print("\n=== TESTING TEMPLATES ===")
        
        templates = [
            'first_page.html',
            'deviation_statement.html',
            'note_sheet_new.html',
            'certificate_ii.html',
            'certificate_iii.html',
            'extra_items.html'
        ]
        
        for template in templates:
            self.test(f"Template: {template}", 
                     lambda t=template: Path(f'templates/{t}').exists() or (_ for _ in ()).throw(FileNotFoundError(f'{t} not found')))
    
    def test_file_structure(self):
        """Test required files and directories"""
        print("\n=== TESTING FILE STRUCTURE ===")
        
        required = [
            'app.py',
            'requirements.txt',
            'runtime.txt',
            '.streamlit/config.toml',
            'core/',
            'templates/',
            'TEST_INPUT_FILES/'
        ]
        
        for item in required:
            self.test(f"Exists: {item}", 
                     lambda i=item: Path(i).exists() or (_ for _ in ()).throw(FileNotFoundError(f'{i} not found')))
    
    def test_excel_processing(self):
        """Test Excel processing functionality"""
        print("\n=== TESTING EXCEL PROCESSING ===")
        
        def test_processor():
            from core.processors.excel_processor import ExcelProcessor
            processor = ExcelProcessor()
            test_file = Path("TEST_INPUT_FILES/FirstFINALvidExtra.xlsx")
            if not test_file.exists():
                raise FileNotFoundError("Test file not found")
            data = processor.process_excel(test_file)
            if not data:
                raise ValueError("No data returned")
            if 'title_data' not in data:
                raise ValueError("Missing title_data")
        
        self.test("Excel processing", test_processor)
    
    def test_document_generation(self):
        """Test document generation"""
        print("\n=== TESTING DOCUMENT GENERATION ===")
        
        def test_generation():
            from core.processors.excel_processor import ExcelProcessor
            from core.generators.document_generator import DocumentGenerator
            
            processor = ExcelProcessor()
            test_file = Path("TEST_INPUT_FILES/FirstFINALvidExtra.xlsx")
            data = processor.process_excel(test_file)
            
            doc_gen = DocumentGenerator(data)
            documents = doc_gen.generate_all_documents()
            
            if not documents:
                raise ValueError("No documents generated")
            
            required_docs = ['First Page Summary', 'Certificate II', 'Certificate III']
            for doc in required_docs:
                if doc not in documents:
                    raise ValueError(f"Missing document: {doc}")
                if not documents[doc]:
                    raise ValueError(f"Empty document: {doc}")
        
        self.test("Document generation", test_generation)
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("ROBOTIC DEPLOYMENT TESTING")
        print("="*60)
        
        self.test_imports()
        self.test_core_modules()
        self.test_templates()
        self.test_file_structure()
        self.test_excel_processing()
        self.test_document_generation()
        
        print("\n" + "="*60)
        print("TEST RESULTS")
        print("="*60)
        print(f"✓ Passed: {self.passed}")
        print(f"✗ Failed: {self.failed}")
        print(f"Total: {self.passed + self.failed}")
        
        if self.failed > 0:
            print("\n" + "="*60)
            print("ERRORS")
            print("="*60)
            for name, error, trace in self.errors:
                print(f"\n{name}:")
                print(f"  Error: {error}")
                print(f"  Trace: {trace[:200]}...")
        
        print("\n" + "="*60)
        if self.failed == 0:
            print("✅ ALL TESTS PASSED - READY FOR DEPLOYMENT")
        else:
            print("❌ SOME TESTS FAILED - FIX BEFORE DEPLOYMENT")
        print("="*60)
        
        return self.failed == 0

if __name__ == "__main__":
    tester = DeploymentTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
