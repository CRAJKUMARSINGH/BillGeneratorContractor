# 🚀 Streamlit Cloud Deployment - Step by Step

## Issue: App not loading at https://bill-priyanka-online.streamlit.app/

## Root Cause Analysis

Based on the code review, the most likely issues are:

1. **Missing or incorrect imports** in deployed modules
2. **File path issues** (Windows vs Linux)
3. **WeasyPrint dependencies** not loading correctly
4. **Configuration file** not found or invalid

## ✅ Pre-Deployment Checklist

### 1. Verify All Required Files Exist

```bash
# Check critical files
ls -la app.py
ls -la requirements.txt
ls -la packages.txt
ls -la config/v01.json
ls -la USER_MANUAL.md
ls -la USER_MANUAL_HINDI.md
```

### 2. Verify Core Modules

```bash
# Check all core modules exist
ls -la core/__init__.py
ls -la core/config/
ls -la core/ui/
ls -la core/utils/
ls -la core/processors/
ls -la core/generators/
```

### 3. Check Git Status

```bash
# Ensure all files are tracked
git status

# Add any untracked files
git add .

# Commit
git commit -m "Fix: Ensure all files are committed for deployment"
```

## 🔧 Deployment Fixes

### Fix #1: Ensure All Files Are Committed

Streamlit Cloud only deploys files that are committed to git!

```bash
# Check what's committed
git ls-files

# If core modules are missing, add them
git add core/
git add config/
git add *.md
git commit -m "Add missing files for deployment"
git push
```

### Fix #2: Verify requirements.txt

Ensure all dependencies are listed:

```txt
streamlit==1.49.1
pandas==2.3.3
numpy==1.26.4
openpyxl==3.1.5
weasyprint==66.0
python-docx==1.2.0
Jinja2==3.1.6
Pillow==10.4.0
num2words==0.5.14
cairocffi==1.7.1
CairoSVG==2.8.2
tinycss2==1.4.0
cssselect2==0.8.0
python-dotenv==1.0.0
python-dateutil==2.9.0.post0
pytz==2025.2
beautifulsoup4==4.12.3
lxml==5.3.0
```

### Fix #3: Verify packages.txt

System dependencies for WeasyPrint:

```txt
libcairo2-dev
libpango1.0-dev
libgdk-pixbuf2.0-dev
libffi-dev
shared-mime-info
```

### Fix #4: Check .gitignore

Ensure you're not ignoring critical files:

```bash
# View .gitignore
cat .gitignore

# Make sure these are NOT ignored:
# - core/
# - config/
# - *.md files
# - requirements.txt
# - packages.txt
```

## 🎯 Deployment Steps

### Step 1: Commit All Changes

```bash
git add .
git commit -m "Fix: Deployment ready - all files included"
git push origin main
```

### Step 2: Check Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Log in with your account
3. Find your app: "bill-priyanka-online"
4. Click "Manage app"

### Step 3: View Logs

In the Streamlit Cloud dashboard:
1. Click on your app
2. Click "Manage app"
3. Scroll down to "Logs"
4. Look for error messages

### Step 4: Force Reboot (if needed)

If the app is stuck:
1. In "Manage app" page
2. Click "Reboot app"
3. Wait 2-3 minutes for rebuild

## 🐛 Common Errors & Solutions

### Error: "ModuleNotFoundError: No module named 'core'"

**Cause**: `core/` directory not committed to git

**Solution**:
```bash
git add core/
git commit -m "Add core modules"
git push
```

### Error: "FileNotFoundError: config/v01.json"

**Cause**: Config file not committed

**Solution**:
```bash
git add config/v01.json
git commit -m "Add config file"
git push
```

### Error: "ImportError: cannot import name 'show_excel_mode'"

**Cause**: Function doesn't exist or file is corrupted

**Solution**: Check the file exists and has the function:
```bash
grep -n "def show_excel_mode" core/ui/excel_mode_fixed.py
```

### Error: "OSError: cannot load library 'gobject-2.0-0'"

**Cause**: WeasyPrint system dependencies missing

**Solution**: Verify `packages.txt` has all required libraries (already correct in your case)

## 🔍 Debugging Steps

### 1. Check Streamlit Cloud Logs

The logs will show the exact error. Common patterns:

```
ModuleNotFoundError: No module named 'X'
→ Missing dependency in requirements.txt or file not committed

FileNotFoundError: [Errno 2] No such file or directory: 'X'
→ File not committed to git

ImportError: cannot import name 'X' from 'Y'
→ Function/class doesn't exist or circular import
```

### 2. Test Locally with Clean Environment

```bash
# Create fresh environment
python -m venv test_deploy
source test_deploy/bin/activate  # Windows: test_deploy\Scripts\activate

# Install only from requirements.txt
pip install -r requirements.txt

# Run app
streamlit run app.py

# If it works locally, the issue is with deployment
```

### 3. Check File Permissions

```bash
# Ensure files are readable
chmod 644 app.py
chmod 644 requirements.txt
chmod 644 packages.txt
chmod -R 755 core/
```

## 🎉 Verification

After deployment, verify:

1. **App loads**: Visit https://bill-priyanka-online.streamlit.app/
2. **No errors**: Check for error messages on page
3. **Sidebar works**: Can switch between modes
4. **File upload works**: Try uploading a file
5. **Logs are clean**: No errors in Streamlit Cloud logs

## 📊 Monitoring

### Check App Health

```bash
# Visit these URLs to check status
https://bill-priyanka-online.streamlit.app/
https://bill-priyanka-online.streamlit.app/_stcore/health
```

### Monitor Logs

Set up log monitoring:
1. Go to Streamlit Cloud dashboard
2. Enable email notifications for errors
3. Check logs daily for issues

## 🆘 Emergency Rollback

If deployment breaks:

```bash
# Revert to last working commit
git log --oneline  # Find last working commit
git revert <commit-hash>
git push

# Or reset to specific commit
git reset --hard <commit-hash>
git push --force
```

## 📞 Support Resources

- **Streamlit Docs**: https://docs.streamlit.io/
- **Streamlit Forum**: https://discuss.streamlit.io/
- **Streamlit Cloud Status**: https://status.streamlit.io/
- **WeasyPrint Docs**: https://doc.courtbouillon.org/weasyprint/

## 🎯 Next Steps

1. ✅ Verify all files are committed
2. ✅ Push to GitHub
3. ✅ Check Streamlit Cloud logs
4. ✅ Test the deployed app
5. ✅ Monitor for errors

---

**Deployment Date**: March 7, 2026  
**App URL**: https://bill-priyanka-online.streamlit.app/  
**Repository**: BillGeneratorUnified  
**Prepared for**: PWD Udaipur
