# Phase 0 — Baseline Report
Generated: 2026-03-23 | Branch: consolidation/saas-2026

## Smoke Test Results
| File | Items | Extra | HTML | Grand Total | Status |
|------|-------|-------|------|-------------|--------|
| 0511-N-extra.xlsx | 8 | 6 | 6 | ₹1,07,789.79 | ✅ PASS |
| 0511Wextra.xlsx | 8 | 6 | 6 | ₹1,07,789.79 | ✅ PASS |
| 3rdFinalNoExtra.xlsx | 36 | 0 | 4 | ₹4,84,962.93 | ✅ PASS |
| 3rdFinalVidExtra.xlsx | 36 | 6 | 6 | ₹4,99,453.93 | ✅ PASS |
| 3rdRunningNoExtra.xlsx | 36 | 6 | 6 | ₹5,20,230.52 | ✅ PASS |
| 3rdRunningVidExtra.xlsx | 36 | 6 | 6 | ₹5,20,230.52 | ✅ PASS |
| 9th and final Amli Fala | 97 | 6 | 6 | ₹4,31,26,767.35 | ✅ PASS |
| FirstFINALnoExtra.xlsx | 36 | 0 | 4 | ₹5,09,028.36 | ✅ PASS |
| FirstFINALvidExtra.xlsx | 36 | 6 | 6 | ₹5,32,432.09 | ✅ PASS |

**BASELINE: 9/9 PASS**

## Bugs Fixed Before Baseline
1. `_safe_float()` — did not handle `inf`/`-inf` → fixed
2. Upload endpoint — no file size limit → fixed (20MB cap)
3. Upload endpoint — orphan files on parse failure → fixed (cleanup on error)

## Known Remaining Issues (Pre-Consolidation)
- No auth layer
- In-memory JOBS dict (no persistence, no expiry)
- No test framework (pytest / vitest) — tests are ad-hoc scripts
- `lib/db/src/schema/index.ts` is empty — DB layer not wired
- `artifacts/api-server` routes only have `/healthz` — bills proxied to Python
- `artifacts/bill-api/uploads/` has 8 stale uploaded files (not cleaned up)
- `artifacts/bill-api/outputs/` has 4 stale job output dirs
- `config.json` max_file_size_mb=10 but code enforces 20MB (inconsistency)
- No `.env` / secret management
- CORS is `allow_origins=["*"]` — fine for single-tenant, needs review for prod
- No rate limiting
- No structured request tracing
- Frontend routing uses `useState` (no URL-based routing — deep links broken)
- Amount recalculation on qty/rate edit is NOT reactive (amount stays stale)
- `lib/db` Drizzle schema is empty — no persistence layer
- `Invoice-Design-Pro/` subfolder is a duplicate of root (nested repo artifact)
