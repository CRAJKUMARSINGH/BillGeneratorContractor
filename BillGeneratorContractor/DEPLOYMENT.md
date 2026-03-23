# 🚀 Deployment Guide - BillGenerator Contractor

## ✅ Repository Successfully Pushed to GitHub

Your code is now live at: **https://github.com/CRAJKUMARSINGH/BillGeneratorContractor**

## 📋 Pre-Deployment Checklist

- [x] Git repository initialized
- [x] Code pushed to GitHub
- [x] `.streamlit/config.toml` configured
- [x] `requirements.txt` updated with all dependencies
- [x] `packages.txt` includes system dependencies (Tesseract OCR)
- [x] `.gitignore` configured
- [x] README.md created
- [x] LICENSE added (MIT)

## 🌐 Deploy to Streamlit Cloud

### Step 1: Access Streamlit Cloud

1. Go to **[share.streamlit.io](https://share.streamlit.io)**
2. Sign in with your GitHub account

### Step 2: Create New App

1. Click **"New app"** button
2. Fill in the deployment form:
   - **Repository**: `CRAJKUMARSINGH/BillGeneratorContractor`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL** (optional): Choose a custom subdomain

### Step 3: Advanced Settings (Optional)

Click "Advanced settings" to configure:

```toml
# Python version
[python]
version = "3.11"

# Secrets (if needed)
[secrets]
BILL_CONFIG = "config/v01.json"
```

### Step 4: Deploy

1. Click **"Deploy!"**
2. Wait 5-10 minutes for initial deployment
3. Your app will be live at: `https://your-app-name.streamlit.app`

## 🔧 Configuration Files

### `.streamlit/config.toml`
```toml
[theme]
primaryColor = "#00b894"
backgroundColor = "#f5f7fa"
secondaryBackgroundColor = "#e8ecf1"
textColor = "#2d3436"

[server]
headless = true
maxUploadSize = 200
```

### `packages.txt` (System Dependencies)
```
libcairo2-dev
libpango1.0-dev
tesseract-ocr
tesseract-ocr-eng
tesseract-ocr-hin
poppler-utils
```

### `requirements.txt` (Python Dependencies)
All dependencies are listed including:
- Streamlit
- PDF processing (pdfplumber, pytesseract)
- Image processing (opencv-python-headless)
- Bill generation (weasyprint, python-docx)

## 🎯 Post-Deployment

### Verify Deployment

1. **Check App Status**: Ensure app is running without errors
2. **Test File Upload**: Upload a sample PDF work order
3. **Test PDF Generation**: Generate a test bill
4. **Check Mobile Responsiveness**: Test on mobile device

### Monitor Logs

- View logs in Streamlit Cloud dashboard
- Check for any missing dependencies
- Monitor resource usage

### Update App

To update your deployed app:

```bash
# Make changes locally
git add .
git commit -m "Your update message"
git push origin main
```

Streamlit Cloud will automatically redeploy within 2-3 minutes.

## 🔐 Environment Variables (Optional)

If you need to add secrets:

1. Go to Streamlit Cloud dashboard
2. Click on your app
3. Go to **Settings** → **Secrets**
4. Add secrets in TOML format:

```toml
[auth]
OTP_API_KEY = "your-api-key"

[database]
CONNECTION_STRING = "your-connection-string"
```

Access in code:
```python
import streamlit as st
api_key = st.secrets["auth"]["OTP_API_KEY"]
```

## 📱 Custom Domain (Optional)

To use a custom domain:

1. Go to app settings in Streamlit Cloud
2. Click **"Custom domain"**
3. Follow instructions to configure DNS

## 🐛 Troubleshooting

### Common Issues

**Issue**: App fails to start
- **Solution**: Check logs for missing dependencies
- Add missing packages to `requirements.txt` or `packages.txt`

**Issue**: Tesseract not found
- **Solution**: Ensure `tesseract-ocr` is in `packages.txt`
- Verify language packs are installed

**Issue**: File upload fails
- **Solution**: Check `maxUploadSize` in config.toml
- Default is 200MB, adjust if needed

**Issue**: PDF generation fails
- **Solution**: Verify weasyprint dependencies in `packages.txt`
- Check cairo, pango, and gdk-pixbuf libraries

### Get Help

- 📖 [Streamlit Docs](https://docs.streamlit.io)
- 💬 [Streamlit Community](https://discuss.streamlit.io)
- 🐛 [GitHub Issues](https://github.com/CRAJKUMARSINGH/BillGeneratorContractor/issues)

## 🎉 Success!

Your BillGenerator Contractor app is now deployed and accessible worldwide!

**Live URL**: `https://your-app-name.streamlit.app`

### Share Your App

Share the URL with contractors to start using the mobile-first bill generation system.

### Next Steps

1. ✅ Test all features thoroughly
2. ✅ Gather user feedback
3. ✅ Implement contractor-specific features from spec
4. ✅ Monitor usage and performance
5. ✅ Iterate based on feedback

---

**Deployed by**: RAJKUMAR SINGH CHAUHAN  
**Repository**: https://github.com/CRAJKUMARSINGH/BillGeneratorContractor  
**Date**: 2025

🚀 **Happy Deploying!**
