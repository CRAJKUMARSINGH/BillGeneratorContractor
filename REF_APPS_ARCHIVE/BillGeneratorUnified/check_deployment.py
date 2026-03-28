#!/usr/bin/env python3
"""
Deployment Health Check Script
Run this to diagnose deployment issues
"""
import sys
import os
from pathlib import Path

def check_deployment():
    """Check deployment health"""
    issues = []
    warnings = []
    
    print("=" * 60)
    print("DEPLOYMENT HEALTH CHECK")
    print("=" * 60)
    
    # Check Python version
    print(f"\n✓ Python Version: {sys.version}")
    
    # Check required files
    required_files = [
        'app.py',
        'requirements.txt',
        'packages.txt',
        'config/v01.json',
        'USER_MANUAL.md',
        'USER_MANUAL_HINDI.md'
    ]
    
    print("\n📁 Checking Required Files:")
    for file in required_files:
        if Path(file).exists():
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} - MISSING")
            issues.append(f"Missing file: {file}")
    
    # Check core modules
    print("\n📦 Checking Core Modules:")
    core_modules = [
        'core.config.config_loader',
        'core.utils.cache_cleaner',
        'core.utils.output_manager',
        'core.ui.excel_mode_fixed',
        'core.ui.hybrid_mode',
        'core.ui.online_mode',
        'core.processors.batch_processor_fixed'
    ]
    
    for module in core_modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError as e:
            print(f"  ✗ {module} - {str(e)}")
            issues.append(f"Import error: {module}")
    
    # Check critical dependencies
    print("\n📚 Checking Dependencies:")
    critical_deps = [
        'streamlit',
        'pandas',
        'openpyxl',
        'weasyprint',
        'docx',
        'jinja2',
        'PIL'
    ]
    
    for dep in critical_deps:
        try:
            __import__(dep)
            print(f"  ✓ {dep}")
        except ImportError as e:
            print(f"  ✗ {dep} - NOT INSTALLED")
            issues.append(f"Missing dependency: {dep}")
        except OSError as e:
            # WeasyPrint on Windows needs GTK libraries
            if dep == 'weasyprint' and 'libgobject' in str(e):
                print(f"  ⚠ {dep} - Installed but needs GTK (OK for Linux deployment)")
                warnings.append(f"{dep} needs GTK libraries (will work on Streamlit Cloud)")
            else:
                print(f"  ✗ {dep} - {str(e)}")
                issues.append(f"Dependency error: {dep}")
    
    # Check directories
    print("\n📂 Checking Directories:")
    required_dirs = ['core', 'config', 'templates']
    
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"  ✓ {dir_name}/")
        else:
            print(f"  ⚠ {dir_name}/ - MISSING")
            warnings.append(f"Missing directory: {dir_name}")
    
    # Check OUTPUT directory
    output_dir = Path('OUTPUT')
    if not output_dir.exists():
        print(f"  ⚠ OUTPUT/ - Will be created automatically")
        warnings.append("OUTPUT directory will be created on first use")
    else:
        print(f"  ✓ OUTPUT/")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if not issues and not warnings:
        print("✅ All checks passed! Deployment should work.")
    else:
        if issues:
            print(f"\n❌ CRITICAL ISSUES ({len(issues)}):")
            for issue in issues:
                print(f"  • {issue}")
        
        if warnings:
            print(f"\n⚠️  WARNINGS ({len(warnings)}):")
            for warning in warnings:
                print(f"  • {warning}")
    
    print("\n" + "=" * 60)
    
    return len(issues) == 0

if __name__ == "__main__":
    success = check_deployment()
    sys.exit(0 if success else 1)
