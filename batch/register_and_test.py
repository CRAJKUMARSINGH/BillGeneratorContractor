#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Register and Test all synthetic inputs with the Brilliant Batch Input Management System.

This script:
1. Copies all 24 synthetic test files to INPUTS_MANAGEMENT/pending/
2. Registers them in the metadata system
3. Validates all inputs
4. Generates an initial report
"""
import sys
import os
import io
from pathlib import Path

# Fix Windows console encoding for ASCII-safe output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Setup paths - add parent directory to path for imports
root_dir = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(root_dir))
os.environ.setdefault('ALLOW_INSECURE_SECRET', '1')

from batch.input_manager import BrilliantBatchInputManager


def main():
    print("=" * 70)
    print("BRILLIANT BATCH INPUT MANAGEMENT SYSTEM - REGISTRATION")
    print("=" * 70)

    # Initialize the input manager
    mgr = BrilliantBatchInputManager()

    # Source directory with synthetic test files
    source_dir = root_dir / "tests" / "SYNTHETIC_INPUTS"

    if not source_dir.exists():
        print(f"ERROR: Source directory not found: {source_dir}")
        print("Please run: python tests/generate_synthetic_inputs.py first")
        return

    # Get all Excel files
    excel_files = list(source_dir.glob("*.xlsx"))
    print(f"\nFound {len(excel_files)} synthetic test files in {source_dir}\n")

    # Register each file
    registered_count = 0
    for filepath in sorted(excel_files):
        try:
            meta = mgr.register_input_file(filepath, category="pending")
            extra_marker = " [HAS EXTRA ITEMS]" if meta.has_extra_items else ""
            print(f"[OK] Registered: {filepath.name}{extra_marker}")
            registered_count += 1
        except Exception as e:
            print(f"[FAIL] Failed to register {filepath.name}: {e}")

    print(f"\n{registered_count}/{len(excel_files)} files registered successfully")

    # Validate all inputs
    print("\n" + "=" * 70)
    print("VALIDATING ALL INPUTS")
    print("=" * 70)

    valid, invalid = mgr.validate_all_inputs()
    print(f"Validation Results: {valid} valid, {invalid} invalid")

    # Generate report
    print("\n" + "=" * 70)
    print("GENERATING INITIAL REPORT")
    print("=" * 70)

    report_path = root_dir / "batch" / "input_registration_report.md"
    report = mgr.generate_report(report_path)
    print(report)

    print(f"\n[OK] Report saved to: {report_path}")
    print(f"[OK] Input files registered in: {mgr.base_dir}")
    print(f"   - Pending: {mgr.pending_dir}")
    print(f"   - Metadata: {mgr.metadata_file}")

    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("1. Review the generated report")
    print("2. Run batch processing: python batch\\run_batch_test.py")
    print("3. Check outputs in: backend\\outputs\\")
    print("=" * 70)


if __name__ == "__main__":
    main()
