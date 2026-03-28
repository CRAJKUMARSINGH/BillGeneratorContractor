# 🚀 Deployment Fix Guide for Streamlit Cloud

## Current Issue
The app at https://bill-priyanka-online.streamlit.app/ is not working.

## Common Causes & Solutions

### 1. **WeasyPrint System Dependencies** ✅ FIXED
Your `packages.txt` file is correct and includes all required system libraries:
```
libcairo2-dev
libpango1.0-dev
libgdk-pixbuf2.0-dev
libffi-dev
shared-mime-info
```

### 2. **Missing Python Dependencies**
Check if all packages in `requirements.txt` are compatible with Streamlit Cloud.

**Action**: Update `requirements.txt` with pinned versions:
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

### 3. **Import Errors**
The app tries to import modules that might fail on deployment.

**Solution**: Use the deployment-ready version:
```bash
# Rename current app.py to app_original.py
mv app.py app_original.py

# Use the deployment-ready version
cp app_deployment_fix.py app.py
```

### 4. **Missing Configuration File**
Ensure `config/v01.json` exists and is valid.

**Action**: Check if the file exists:
```bash
ls -la config/v01.json
```

### 5. **File Path Issues**
Streamlit Cloud uses Linux paths, not Windows paths.

**Fixed**: The code uses `pathlib.Path` which handles cross-platform paths correctly.

### 6. **OUTPUT Directory**
The app creates an OUTPUT directory which might not persist on Streamlit Cloud.

**Fixed**: The code creates the directory automatically with `OUTPUT_DIR.mkdir(exist_ok=True)`.

## 🔧 Quick Fix Steps

### Option A: Use Deployment-Ready App (Recommended)
```bash
# 1. Backup current app
cp app.py app_backup.py

# 2. Use deployment-ready version
cp app_deployment_fix.py app.py

# 3. Commit and push
git add app.py
git commit -m "Fix: Use deployment-ready app version"
git push
```

### Option B: Debug Current App
```bash
# 1. Run health check
python check_deployment.py

# 2. Fix any reported issues

# 3. Test locally first
streamlit run app.py

# 4. If working locally, commit and push
git add .
git commit -m "Fix: Deployment issues"
git push
```

## 📋 Deployment Checklist

- [x] `requirements.txt` exists with all dependencies
- [x] `packages.txt` exists with system dependencies
- [x] `.streamlit/config.toml` exists
- [ ] `config/v01.json` exists and is valid
- [ ] All `core/` modules are present
- [ ] `USER_MANUAL.md` and `USER_MANUAL_HINDI.md` exist
- [ ] No hardcoded Windows paths (use `pathlib.Path`)
- [ ] All imports have error handling
- [ ] OUTPUT directory is created automatically

## 🐛 Debugging on Streamlit Cloud

### View Logs
1. Go to https://share.streamlit.io/
2. Click on your app
3. Click "Manage app"
4. View logs to see error messages

### Common Error Messages

**Error**: `ModuleNotFoundError: No module named 'core.ui.excel_mode_fixed'`
**Fix**: Ensure all files in `core/ui/` are committed to git

**Error**: `FileNotFoundError: config/v01.json`
**Fix**: Ensure config file exists and is committed

**Error**: `ImportError: cannot import name 'show_excel_mode'`
**Fix**: Check that the function exists in the module

**Error**: `OSError: cannot load library 'gobject-2.0-0'`
**Fix**: Ensure `packages.txt` includes all WeasyPrint dependencies

## 🎯 Testing Locally Before Deployment

```bash
# 1. Create a clean virtual environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py

# 4. Test all modes:
#    - Excel Upload
#    - Online Entry
#    - Download Center
#    - User Manual

# 5. If everything works, deploy
git add .
git commit -m "Ready for deployment"
git push
```

## 🔍 Verify Deployment

After pushing changes:

1. Wait 2-3 minutes for Streamlit Cloud to rebuild
2. Visit https://bill-priyanka-online.streamlit.app/
3. Check if the app loads
4. Test each mode
5. Check browser console for JavaScript errors (F12)

## 📞 Still Not Working?

If the app still doesn't work after these fixes:

1. **Check Streamlit Cloud logs** for specific error messages
2. **Run `python check_deployment.py`** locally to identify issues
3. **Test with `app_deployment_fix.py`** which has better error handling
4. **Verify all files are committed** to git (Streamlit Cloud only sees committed files)
5. **Check Streamlit Cloud status** at https://status.streamlit.io/

## 💡 Pro Tips

1. **Always test locally first** before deploying
2. **Use `st.error()` and `st.info()`** to show helpful error messages
3. **Wrap imports in try-except** blocks for graceful degradation
4. **Check file paths** - use `Path(__file__).parent` for relative paths
5. **Monitor app logs** on Streamlit Cloud dashboard
6. **Keep dependencies minimal** - only include what you actually use

## 🎉 Success Indicators

Your app is working correctly when:
- ✅ App loads without errors
- ✅ All modes are accessible from sidebar
- ✅ File upload works
- ✅ PDF generation works
- ✅ Download center shows files
- ✅ No error messages in logs

---

**Last Updated**: March 7, 2026
**Prepared for**: PWD Udaipur Bill Generator Deployment
