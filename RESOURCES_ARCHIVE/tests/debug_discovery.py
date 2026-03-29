import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
print(f"ROOT_DIR: {ROOT_DIR}")

def discover_test_files():
    folders = [f for f in ROOT_DIR.iterdir() if f.is_dir() and (f.name.startswith("INPUT") or f.name.startswith("TEST"))]
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
