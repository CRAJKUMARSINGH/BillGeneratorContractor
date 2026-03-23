"""
Clean All Caches - Python, PDF, and Temporary Files
"""

import os
import shutil
from pathlib import Path

def clean_python_cache(root_dir):
    """Remove Python cache files"""
    print("\n🧹 Cleaning Python cache...")
    
    removed = 0
    
    # Remove __pycache__ directories
    for root, dirs, files in os.walk(root_dir):
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(cache_dir)
                print(f"   ✅ Removed: {cache_dir}")
                removed += 1
            except Exception as e:
                print(f"   ⚠️  Could not remove {cache_dir}: {e}")
    
    # Remove .pyc files
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.pyc'):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"   ✅ Removed: {file_path}")
                    removed += 1
                except Exception as e:
                    print(f"   ⚠️  Could not remove {file_path}: {e}")
    
    print(f"\n   📊 Removed {removed} Python cache items")
    return removed


def clean_pdf_cache():
    """Clear PDF generation cache"""
    print("\n🧹 Cleaning PDF cache...")
    
    try:
        from data.cache_utils import get_cache
        cache = get_cache()
        
        # Get cache stats before clearing
        try:
            stats = cache.info()
            print(f"   📊 Cache items before: {stats.get('currsize', 'unknown')}")
        except:
            print(f"   📊 Clearing cache...")
        
        # Clear cache
        cache.clear()
        print(f"   ✅ PDF cache cleared")
        
        return True
    except Exception as e:
        print(f"   ⚠️  Could not clear PDF cache: {e}")
        return False


def clean_temp_files(root_dir):
    """Remove temporary files"""
    print("\n🧹 Cleaning temporary files...")
    
    removed = 0
    
    # Patterns to remove
    patterns = [
        '*.tmp',
        '*.temp',
        '*.log',
        '*.bak',
        '*.backup',
        '*~'
    ]
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            for pattern in patterns:
                if file.endswith(pattern.replace('*', '')):
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        print(f"   ✅ Removed: {file_path}")
                        removed += 1
                    except Exception as e:
                        print(f"   ⚠️  Could not remove {file_path}: {e}")
    
    print(f"\n   📊 Removed {removed} temporary files")
    return removed


def clean_test_outputs(root_dir):
    """Clean old test output directories"""
    print("\n🧹 Cleaning old test outputs...")
    
    test_outputs_dir = os.path.join(root_dir, 'test_outputs')
    
    if not os.path.exists(test_outputs_dir):
        print("   ℹ️  No test_outputs directory found")
        return 0
    
    # List all subdirectories
    subdirs = [d for d in os.listdir(test_outputs_dir) 
               if os.path.isdir(os.path.join(test_outputs_dir, d))]
    
    if not subdirs:
        print("   ℹ️  No test output directories to clean")
        return 0
    
    print(f"   📊 Found {len(subdirs)} test output directories")
    print(f"\n   ⚠️  Keep the most recent ones? (recommended)")
    
    # Keep the 3 most recent
    subdirs_with_time = []
    for subdir in subdirs:
        subdir_path = os.path.join(test_outputs_dir, subdir)
        mtime = os.path.getmtime(subdir_path)
        subdirs_with_time.append((subdir, subdir_path, mtime))
    
    # Sort by modification time (newest first)
    subdirs_with_time.sort(key=lambda x: x[2], reverse=True)
    
    # Keep 3 most recent, remove others
    to_keep = subdirs_with_time[:3]
    to_remove = subdirs_with_time[3:]
    
    print(f"\n   ✅ Keeping {len(to_keep)} most recent:")
    for subdir, path, mtime in to_keep:
        print(f"      - {subdir}")
    
    if to_remove:
        print(f"\n   🗑️  Removing {len(to_remove)} old directories:")
        removed = 0
        for subdir, path, mtime in to_remove:
            try:
                shutil.rmtree(path)
                print(f"      ✅ Removed: {subdir}")
                removed += 1
            except Exception as e:
                print(f"      ⚠️  Could not remove {subdir}: {e}")
        
        print(f"\n   📊 Removed {removed} old test directories")
        return removed
    else:
        print(f"\n   ℹ️  No old directories to remove")
        return 0


def get_directory_size(path):
    """Calculate directory size in MB"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
    except Exception:
        pass
    return total_size / (1024 * 1024)


def main():
    """Main cache cleaning process"""
    print(f"\n{'='*80}")
    print(f"{'CACHE CLEANING UTILITY':^80}")
    print(f"{'='*80}\n")
    
    root_dir = os.getcwd()
    print(f"📁 Working directory: {root_dir}")
    
    # Get initial size
    initial_size = get_directory_size(root_dir)
    print(f"📊 Initial directory size: {initial_size:.2f} MB")
    
    print(f"\n{'─'*80}")
    
    # Clean Python cache
    python_removed = clean_python_cache(root_dir)
    
    # Clean PDF cache
    pdf_cache_cleared = clean_pdf_cache()
    
    # Clean temporary files
    temp_removed = clean_temp_files(root_dir)
    
    # Clean old test outputs
    test_removed = clean_test_outputs(root_dir)
    
    # Get final size
    print(f"\n{'─'*80}")
    final_size = get_directory_size(root_dir)
    space_freed = initial_size - final_size
    
    print(f"\n{'='*80}")
    print(f"{'CLEANING SUMMARY':^80}")
    print(f"{'='*80}\n")
    
    print(f"✅ Python cache items removed: {python_removed}")
    print(f"✅ PDF cache cleared: {'Yes' if pdf_cache_cleared else 'No'}")
    print(f"✅ Temporary files removed: {temp_removed}")
    print(f"✅ Old test directories removed: {test_removed}")
    
    print(f"\n📊 Space freed: {space_freed:.2f} MB")
    print(f"📊 Final directory size: {final_size:.2f} MB")
    
    print(f"\n{'='*80}")
    print(f"{'✨ CACHE CLEANING COMPLETE! ✨':^80}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
