import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
print(f"ROOT_DIR: {ROOT_DIR}")

def discover_test_files():
    bench_root = ROOT_DIR / "MASTER_INPUT_BENCHMARKS"
    if not bench_root.exists():
        return []
        
    folders = [f for f in bench_root.iterdir() if f.is_dir()]
    print(f"Folders found: {[f.name for f in folders]}")
    files = []
    
    extensions = ["*.xlsx", "*.xls", "*.xlsm", "*.pdf", "*.jpeg", "*.jpg", "*.png"]
    for folder in folders:
        for ext in extensions:
            found = list(folder.rglob(ext))
            print(f"  {folder.name} -> {ext}: {len(found)}")
            files.extend(found)
            
    return files

files = discover_test_files()
print(f"Total files: {len(files)}")
