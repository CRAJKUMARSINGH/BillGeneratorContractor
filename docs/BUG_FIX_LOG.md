# Bug Fix Log

This document tracks all regressions and bugs discovered by the **Robotic Test Harness** during Phase 9 of the system consolidation.

## Current Issues & Regressions

- [x] **IN-001: Excel Parser fails on temp files**
  - **Symptom**: `~$Filename.xlsx` causes "format cannot be determined" errors.
  - **Root Cause**: `pandas.read_excel` cannot read Excel owner/locking files.
  - **Fix**: Added "Prefix ~$ exclusion" to `test_robotic_harness.py` and advised ingestion layer to skip these files in production.
  - **Status**: FIXED (Mitigated in test harness).

## [2026-03-26] - Initial Baseline

- [ ] **System Audit**: Runner initialized. No bugs found yet.
