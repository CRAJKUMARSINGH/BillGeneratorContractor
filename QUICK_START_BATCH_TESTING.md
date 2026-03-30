# 🚀 Quick Start - Batch Testing Guide

## TL;DR - Run These Commands

```bash
cd e:\Rajkumar\BillGeneratorContractor

# 1. Register all test files
python batch\register_and_test.py

# 2. Run comprehensive tests
python batch\run_batch_test.py

# 3. Check results
ls backend/outputs/*/
```

---

## What Was Done

### ✅ Fixed (Critical Issues from genspark.md)
1. **Security**: JWT secret validation, download auth, path traversal prevention
2. **Architecture**: Service layer created, worker non-blocking async
3. **Batch System**: Brilliant Input Management System created
4. **Test Files**: 24 synthetic inputs generated (12 without + 12 with extra items)

### 📁 New Files Created
- `backend/services/bill_generation_service.py` - Service layer
- `batch/input_manager.py` - Input management
- `batch/processor.py` - Batch processor  
- `batch/run_batch_test.py` - Test runner
- `batch/register_and_test.py` - Registration script
- `REFACTORING_SUMMARY_AND_TEST_PLAN.md` - Full documentation

### 📊 Test Files Status
- Location: `tests/SYNTHETIC_INPUTS/`
- Count: 24 files (12 NoExtra + 12 WithExtra)
- Format: PWD 4-sheet Excel (.xlsx)

---

## Running the Tests

### Step 1: Ensure Server is Running
```bash
# Option A: Use start script
python start_server.py

# Option B: Direct uvicorn
uvicorn backend.app:app --reload --port 8000
```

Verify:
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok","engine":"ok",...}
```

### Step 2: Register Test Files
```bash
python batch\register_and_test.py
```

This will:
- Copy 24 files to `INPUTS_MANAGEMENT/pending/`
- Create metadata registry
- Validate all files
- Generate report

Expected output:
```
✓ Registered: SYNTH_01_NoExtra.xlsx
✓ Registered: SYNTH_02_NoExtra.xlsx
...
✓ Registered: SYNTH_13_WithExtra.xlsx ⚠️  HAS EXTRA ITEMS
...
24/24 files registered successfully
```

### Step 3: Run Tests
```bash
python batch\run_batch_test.py
```

This performs:
1. **Individual Testing** - Each file processed separately
2. **Batch Processing** - All files concurrently (max 4 parallel)
3. **Report Generation** - Detailed markdown reports

Duration: ~5-15 minutes depending on system

### Step 4: Review Results

Check generated PDFs:
```bash
# Windows PowerShell
Get-ChildItem -Recurse backend/outputs/*.pdf | Select-Object FullName

# Or simply explore in File Explorer
explorer backend\outputs
```

Check reports:
- `batch/input_registration_report.md` - Initial status
- `backend/outputs/batch_test_report_*.md` - Final results

---

## What to Verify

### For Files WITHOUT Extra Items:
Open any PDF from a `SYNTH_01_*` to `SYNTH_12_*` file:
- ✅ First page has header info
- ✅ Note sheet shows calculations
- ✅ Extra items sheet says "No extra items"
- ✅ Deviation statement empty/zero

### For Files WITH Extra Items:
Open any PDF from a `SYNTH_13_*` to `SYNTH_24_*` file:
- ✅ Extra items sheet populated
- ✅ Deviation statement shows amounts
- ✅ Note sheet includes extra scrutiny
- ✅ Total includes extra item value

### Batch Processing:
Check `INPUTS_MANAGEMENT/metadata.json`:
```json
{
  "stats": {
    "total": 24,
    "completed": 24,
    "failed": 0
  }
}
```

---

## Troubleshooting

### Redis Connection Failed
**Symptom**: Warning about Redis not available
**Impact**: Processing falls back to synchronous mode
**Fix**: 
```bash
# Start Redis (if installed)
redis-server

# Or continue without it (slower but works)
```

### PDF Generation Failed
**Symptom**: HTML generated but PDF fails
**Cause**: WeasyPrint or dependency missing
**Fix**:
```bash
pip install weasyprint
# or check backend/requirements.txt
```

### File Not Found Errors
**Symptom**: "File not found on disk"
**Cause**: Files moved manually
**Fix**: Re-run registration script

---

## Reference Files Testing

To test with the 9 reference files:

1. **Copy to Pending**
```bash
copy "RESOURCES_ARCHIVE\TEST_INPUT_FILES\*.xlsx" INPUTS_MANAGEMENT\pending\
```

2. **Register Them**
```bash
python -c "from batch.input_manager import BrilliantBatchInputManager; mgr = BrilliantBatchInputManager(); import pathlib; [mgr.register_input_file(f) for f in pathlib.Path('INPUTS_MANAGEMENT/pending').glob('*.xlsx')]"
```

3. **Run Tests**
```bash
python batch\run_batch_test.py
```

4. **Compare Outputs**
Manually compare generated PDFs with reference outputs from:
- `REF_APPS_ARCHIVE/BillGeneratorUnified/`
- Historical test outputs in `TEST_OUTPUTS/`

---

## Success Indicators

✅ All 24 files registered without errors
✅ Validation passes (24 valid, 0 invalid)
✅ Individual tests complete with minimal failures
✅ Batch processing completes successfully
✅ PDFs generated for all document types
✅ Extra items appear in correct sheets
✅ Metadata shows high completion rate (>90%)
✅ Reports generated successfully

---

## Important Notes

### ⚠️ DO NOT DELETE
These folders are preserved for future reference:
- `REF_APPS_ARCHIVE/` - All 5 reference apps
- `tests/SYNTHETIC_INPUTS/` - 24 synthetic files
- `RESOURCES_ARCHIVE/TEST_INPUT_FILES/` - 9 reference files
- `BATCH_SYSTEM/` - Historical batch data
- `TEST_OUTPUTS/` - All previous test runs

### 📝 Output Locations
- **PDFs**: `backend/outputs/{job_id}/*.pdf`
- **HTMLs**: `backend/outputs/{job_id}/*.html`
- **Reports**: `backend/outputs/batch_test_report_*.md`
- **Metadata**: `INPUTS_MANAGEMENT/metadata.json`

### 🔧 Configuration
- Template version: v2 (hardcoded)
- Concurrency: 4 concurrent jobs
- PDF generation: Enabled by default
- Upload limit: 20MB per file

---

## Next Steps After Testing

1. **Review Generated Reports**
   - Check for patterns in failures
   - Note any calculation discrepancies

2. **Compare with Reference Outputs**
   - Manually compare PDFs
   - Focus on extra item handling

3. **Document Findings**
   - List bugs discovered
   - Note template issues
   - Identify regressions

4. **Iterate**
   - Fix identified issues
   - Re-run tests
   - Verify fixes

---

## Questions?

See full documentation:
- `REFACTORING_SUMMARY_AND_TEST_PLAN.md` - Complete details
- `attached assets/genspark.md` - Code review observations
- `BATCH_SYSTEM/batch_report.md` - Historical context

---

**Ready to Start?** Run: `python batch\register_and_test.py`
