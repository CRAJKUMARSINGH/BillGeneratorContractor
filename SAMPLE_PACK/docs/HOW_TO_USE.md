# How To Use SAMPLE_PACK

## 1) Daily regression check

From repo root:

`python tests/pdf_certification_harness.py --unif-root "C:\Users\Rajkumar\BillGeneratorUnified" --limit 9 --visual --dpi 150`

Then inspect:

- `REGRESSION_RESULTS_CERT/summary.csv`
- `REGRESSION_RESULTS_CERT/<case>/DIFF/*`

## 2) Update the pack after a validated release

1. Pick stable runs from `REGRESSION_RESULTS_CERT/`.
2. Copy outputs into:
   - `02_reference_unif_outputs/` (UNIF artifacts)
   - `03_consolidated_outputs/` (current app artifacts)
   - `05_reports/` (summary + per-case evidence)
3. Update `docs/PROVENANCE.md` and `docs/CHANGELOG.md`.

## 3) What to compare first

- `first_page`
- `deviation_statement`
- `note_sheet`
- `certificate_ii`
- `certificate_iii`
- `extra_items` (only when source has extra items)

## 4) Extra-items correctness checks

For files containing extra items:

- `extra_items` PDF must exist and be non-empty.
- `first_page` should include extra-item effect in totals where applicable.
- `deviation_statement` and `note_sheet` should reflect adjusted amounts.

## 5) Onboarding checklist for a new team lead

- Read `SAMPLE_PACK/README.md`.
- Read `docs/PROVENANCE.md` and confirm data sources still exist.
- Run certification harness once.
- Review one case with extra items and one without extra items.
- Confirm local pre-PDF editor flow in browser before approving release.

