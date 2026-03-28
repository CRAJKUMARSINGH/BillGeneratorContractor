# 🔧 CI/CD Pipeline Fix Notes

**Issue:** GitHub Actions workflow may be failing because it's not configured for the new test structure.

---

## 🐛 Problems Identified

1. **Test Path Mismatch**
   - CI looks for: `tests/backend`
   - Our tests are in: `tests/test_online_grid_*.py`

2. **Missing Dependencies**
   - `streamlit-aggrid` not in requirements.txt
   - `hypothesis` not in requirements.txt (for property tests)

3. **Test Command**
   - CI runs: `pytest tests/backend -v`
   - Should run: `pytest tests/ -v` (to include all tests)

---

## ✅ Quick Fixes

### Fix 1: Update CI Workflow

Edit `.github/workflows/ci.yml`:

```yaml
# Change this line:
- name: Run backend tests
  run: |
    python -m pytest tests/backend -v --tb=short

# To this:
- name: Run all tests
  run: |
    python -m pytest tests/ -v --tb=short
```

### Fix 2: Update requirements.txt

Add these dependencies:

```txt
streamlit-aggrid>=1.2.0
hypothesis>=6.0.0
pytest>=7.0.0
pytest-cov>=4.0.0
```

### Fix 3: Create Test Directory Structure (if needed)

If CI expects `tests/backend`, either:
- **Option A:** Move tests to `tests/backend/`
- **Option B:** Update CI to use `tests/` (recommended)

---

## 🚀 Recommended CI Workflow Update

Replace the test job in `.github/workflows/ci.yml` with:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov hypothesis

    - name: Run unit tests
      run: |
        python -m pytest tests/test_online_grid_unit.py -v --tb=short

    - name: Run property tests
      run: |
        python -m pytest tests/test_online_grid_properties.py -v --hypothesis-show-statistics

    - name: Run all tests with coverage
      run: |
        python -m pytest tests/ --cov=core/ui --cov-report=xml --cov-report=html

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
```

---

## 📝 Complete requirements.txt Update

Ensure these are in `requirements.txt`:

```txt
# Core dependencies
streamlit>=1.2.0
pandas>=1.4.0
openpyxl>=3.0.0
python-docx>=0.8.11
jinja2>=3.0.0
weasyprint>=52.0

# Enhanced grid
streamlit-aggrid>=1.2.0

# Testing
pytest>=7.0.0
pytest-cov>=4.0.0
hypothesis>=6.0.0

# Code quality
flake8>=4.0.0
bandit>=1.7.0
```

---

## 🔍 Verify Locally Before Push

Before pushing to GitHub, verify locally:

```bash
# 1. Install all dependencies
pip install -r requirements.txt

# 2. Run tests locally
python -m pytest tests/ -v

# 3. Check coverage
python -m pytest tests/ --cov=core/ui --cov-report=html

# 4. Lint code
flake8 core/ui/online_mode_grid_*.py --max-line-length=127

# 5. Security scan
bandit -r core/ -f json
```

---

## 🎯 Expected Results After Fix

- ✅ All 79 tests pass in CI
- ✅ Coverage report generated
- ✅ No lint errors
- ✅ No security issues
- ✅ Build succeeds on Python 3.9, 3.10, 3.11

---

## 🚨 If CI Still Fails

Check these common issues:

1. **Import Errors**
   - Ensure `core/__init__.py` exists
   - Ensure `core/ui/__init__.py` exists
   - Check Python path in tests

2. **Missing Files**
   - Ensure all test files are committed
   - Ensure implementation files are committed
   - Check `.gitignore` isn't excluding needed files

3. **Dependency Conflicts**
   - Pin versions in requirements.txt
   - Use `pip freeze > requirements.txt` to capture exact versions

4. **Platform Differences**
   - CI runs on Ubuntu, you're on Windows
   - Path separators might differ
   - Use `pathlib` for cross-platform paths

---

## 📞 Quick Commands for Debugging

```bash
# Check what's in tests directory
ls -la tests/

# Check if tests can be imported
python -c "import sys; sys.path.insert(0, '.'); from tests.test_online_grid_unit import *"

# Run tests with verbose output
python -m pytest tests/ -vv --tb=long

# Check installed packages
pip list | grep -E "streamlit|pytest|hypothesis"
```

---

## ✅ Action Items for Next Session

When you return:

1. [ ] Update `.github/workflows/ci.yml` with new test paths
2. [ ] Update `requirements.txt` with all dependencies
3. [ ] Push changes and verify CI passes
4. [ ] Check GitHub Actions tab for green checkmarks
5. [ ] Fix any remaining issues

---

**Status:** CI fix documented, ready to apply  
**Priority:** Medium (doesn't block local development)  
**Time Estimate:** 15-30 minutes to fix and verify

**Note:** This won't affect your local development. The tests work fine locally. This is just to make CI happy.
