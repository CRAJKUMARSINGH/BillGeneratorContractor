#!/usr/bin/env python3
"""
Deployment Verification Script
Checks if all required files and configurations are ready for Streamlit Cloud deployment
"""

import sys
from pathlib import Path
import json

class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def check_file_exists(file_path, required=True):
    """Check if a file exists"""
    path = Path(file_path)
    if path.exists():
        print_success(f"Found: {file_path}")
        return True
    else:
        if required:
            print_error(f"Missing: {file_path} (REQUIRED)")
        else:
            print_warning(f"Missing: {file_path} (Optional)")
        return False

def check_requirements_txt():
    """Check requirements.txt"""
    print_header("Checking requirements.txt")
    
    if not check_file_exists("requirements.txt"):
        return False
    
    with open("requirements.txt", 'r') as f:
        content = f.read()
    
    required_packages = [
        'streamlit',
        'pandas',
        'openpyxl',
        'jinja2',
        'python-docx'
    ]
    
    all_found = True
    for package in required_packages:
        if package in content:
            print_success(f"Package found: {package}")
        else:
            print_error(f"Package missing: {package}")
            all_found = False
    
    return all_found

def check_packages_txt():
    """Check packages.txt"""
    print_header("Checking packages.txt")
    
    if not check_file_exists("packages.txt", required=False):
        print_info("packages.txt is optional but recommended for PDF generation")
        return True
    
    return True

def check_streamlit_config():
    """Check Streamlit configuration"""
    print_header("Checking Streamlit Configuration")
    
    config_exists = check_file_exists(".streamlit/config.toml")
    secrets_example_exists = check_file_exists(".streamlit/secrets.toml.example", required=False)
    
    # Check if secrets.toml exists (should NOT be in git)
    if Path(".streamlit/secrets.toml").exists():
        print_warning("secrets.toml found - ensure it's in .gitignore!")
    else:
        print_success("secrets.toml not found (good - should not be in git)")
    
    return config_exists

def check_app_config():
    """Check application configuration"""
    print_header("Checking Application Configuration")
    
    config_paths = [
        "config/app_config.json",
        "BillGeneratorUnified/config/v01.json"
    ]
    
    found = False
    for config_path in config_paths:
        if check_file_exists(config_path, required=False):
            found = True
            # Validate JSON
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                print_success(f"Valid JSON in {config_path}")
                
                # Check required fields
                required_fields = ['app_name', 'version', 'features']
                for field in required_fields:
                    if field in config:
                        print_success(f"Field found: {field}")
                    else:
                        print_warning(f"Field missing: {field}")
            except json.JSONDecodeError as e:
                print_error(f"Invalid JSON in {config_path}: {e}")
                return False
    
    if not found:
        print_warning("No configuration file found - will use defaults")
    
    return True

def check_main_app():
    """Check main application file"""
    print_header("Checking Main Application")
    
    if not check_file_exists("app.py"):
        return False
    
    try:
        with open("app.py", 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open("app.py", 'r', encoding='latin-1') as f:
                content = f.read()
        except Exception as e:
            print_error(f"Could not read app.py: {e}")
            return False
    
    # Check for Streamlit Cloud detection
    if "IS_STREAMLIT_CLOUD" in content or "STREAMLIT_SHARING_MODE" in content:
        print_success("Streamlit Cloud detection found")
    else:
        print_warning("No Streamlit Cloud detection - may have issues on cloud")
    
    # Check for error handling
    if "try:" in content and "except" in content:
        print_success("Error handling found")
    else:
        print_warning("Limited error handling - consider adding more")
    
    return True

def check_gitignore():
    """Check .gitignore"""
    print_header("Checking .gitignore")
    
    if not check_file_exists(".gitignore"):
        print_warning("No .gitignore found - secrets may be exposed!")
        return False
    
    with open(".gitignore", 'r') as f:
        content = f.read()
    
    critical_entries = [
        '.streamlit/secrets.toml',
        '.env',
        '__pycache__'
    ]
    
    all_found = True
    for entry in critical_entries:
        if entry in content:
            print_success(f"Ignored: {entry}")
        else:
            print_error(f"Not ignored: {entry} (CRITICAL)")
            all_found = False
    
    return all_found

def check_directory_structure():
    """Check directory structure"""
    print_header("Checking Directory Structure")
    
    required_dirs = [
        "config",
        "templates"
    ]
    
    optional_dirs = [
        "core",
        "BillGeneratorUnified",
        "test_input_files"
    ]
    
    all_found = True
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print_success(f"Directory found: {dir_name}")
        else:
            print_error(f"Directory missing: {dir_name}")
            all_found = False
    
    for dir_name in optional_dirs:
        if Path(dir_name).exists():
            print_success(f"Optional directory found: {dir_name}")
        else:
            print_info(f"Optional directory missing: {dir_name}")
    
    return all_found

def check_documentation():
    """Check documentation"""
    print_header("Checking Documentation")
    
    docs = [
        ("README.md", True),
        ("STREAMLIT_CLOUD_DEPLOYMENT.md", True),
        ("QUICK_START.md", False),
        ("UPDATE_NOTES.md", False)
    ]
    
    for doc, required in docs:
        check_file_exists(doc, required=required)
    
    return True

def run_all_checks():
    """Run all verification checks"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     Streamlit Cloud Deployment Verification Script        ║")
    print("║                BillGenerator Historical                    ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")
    
    checks = [
        ("Main Application", check_main_app),
        ("Requirements", check_requirements_txt),
        ("System Packages", check_packages_txt),
        ("Streamlit Config", check_streamlit_config),
        ("App Configuration", check_app_config),
        ("Git Ignore", check_gitignore),
        ("Directory Structure", check_directory_structure),
        ("Documentation", check_documentation)
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print_error(f"Error in {check_name}: {e}")
            results.append((check_name, False))
    
    # Summary
    print_header("Verification Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        if result:
            print_success(f"{check_name}: PASSED")
        else:
            print_error(f"{check_name}: FAILED")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} checks passed{Colors.END}\n")
    
    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}")
        print("╔════════════════════════════════════════════════════════════╗")
        print("║                  ✅ DEPLOYMENT READY! ✅                   ║")
        print("║                                                            ║")
        print("║  Your app is ready to deploy to Streamlit Cloud!          ║")
        print("║  Follow STREAMLIT_CLOUD_DEPLOYMENT.md for next steps.     ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print(f"{Colors.END}\n")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}")
        print("╔════════════════════════════════════════════════════════════╗")
        print("║              ⚠️  DEPLOYMENT NOT READY ⚠️                  ║")
        print("║                                                            ║")
        print("║  Please fix the issues above before deploying.            ║")
        print("║  Check STREAMLIT_CLOUD_DEPLOYMENT.md for guidance.        ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print(f"{Colors.END}\n")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_checks())
