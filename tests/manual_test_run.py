import sys
from pathlib import Path

# Add root to sys.path
root = Path(__file__).parent.parent
sys.path.append(str(root))

from tests.test_robotic_harness import discover_test_files, test_robotic_pipeline

files = discover_test_files()
print(f"Found {len(files)} files.")

if files:
    print(f"Testing with first file: {files[0]}")
    try:
        test_robotic_pipeline(files[0])
        print("✅ Pipeline test succeeded manually.")
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
else:
    print("❌ No files found for testing.")
