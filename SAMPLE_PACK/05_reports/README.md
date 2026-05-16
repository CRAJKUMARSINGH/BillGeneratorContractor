# Reports

This folder stores certification evidence for refactor safety.

## Current

- `cert_run_latest/summary.csv` - tabular per-template comparison output.
- `cert_run_latest/summary.json` - machine-readable version.

## How to read quickly

- `status`:
  - `PASS` = both outputs present and compared
  - `PASS (both missing)` = usually acceptable for extra-items on no-extra-input cases
  - `FAIL (missing one side)` = template presence mismatch
- `text_similarity`:
  - closer to `1.0` means stronger textual overlap
- `visual_*_percent_diff`:
  - lower is better visual closeness

## Caveat

UNIF and CONS may differ in pagination and layout engine behavior, so exact byte match is not expected.

