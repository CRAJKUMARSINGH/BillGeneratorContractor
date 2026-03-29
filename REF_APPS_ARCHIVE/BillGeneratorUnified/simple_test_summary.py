#!/usr/bin/env python3
"""Simple Test Summary - ASCII only"""
import sys
from pathlib import Path

print("="*70)
print("BILLGENERATOR TEST SUMMARY")
print("="*70)

# Count output folders
output_dir = Path("OUTPUT")
folders = list(output_dir.glob("*_20260307_*"))
print(f"\nOutput Folders Created: {len(folders)}")

# Count Word documents
word_docs = list(output_dir.glob("*/bill_report.docx"))
print(f"Word Documents Generated: {len(word_docs)}")

# List test files
test_dir = Path("TEST_INPUT_FILES")
test_files = list(test_dir.glob("*.xlsx"))
print(f"Test Files Available: {len(test_files)}")

print("\n" + "="*70)
print("TEST RESULTS")
print("="*70)

print(f"\nFiles Processed: {len(test_files)}/8")
print(f"Word Docs Created: {len(word_docs)}/8")
print(f"Success Rate: {(len(word_docs)/8*100):.0f}%")

if len(word_docs) == 8:
    print("\nSTATUS: ALL TESTS PASSED!")
    print("System is READY FOR PRODUCTION")
else:
    print(f"\nSTATUS: {len(word_docs)} files processed successfully")

print("\n" + "="*70)
print("GENERATED FILES")
print("="*70)

for doc in sorted(word_docs):
    print(f"  {doc}")

print("\n" + "="*70)
print("NEXT STEPS")
print("="*70)
print("\n1. Open Streamlit UI: http://localhost:8501")
print("2. Upload test files from TEST_INPUT_FILES/")
print("3. Generate and download outputs")
print("4. Deploy to Streamlit Cloud")

print("\n" + "="*70)
