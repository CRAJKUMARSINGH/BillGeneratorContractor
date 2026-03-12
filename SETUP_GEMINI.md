# 🚀 SETUP GEMINI API - 3 MINUTES

## Step 1: Get FREE API Key

**Go to:** https://makersuite.google.com/app/apikey

**Or use this direct link:** https://aistudio.google.com/app/apikey

1. Sign in with your Google account
2. Click "Create API Key" button
3. Copy the key (starts with "AIza...")

---

## Step 2: Add Key to .env File

Open `.env` file and add this line:

```
GEMINI_API_KEY=AIzaSy...your_key_here
```

---

## Step 3: Install Library

```bash
pip install google-generativeai
```

---

## Step 4: Test Extraction

```bash
python extract_with_gemini.py
```

---

## ✅ DONE!

The script will:
- Process all 5 images
- Extract ALL items
- Save to `OUTPUT/GEMINI_EXTRACTED_DATA.json`

Then we'll create the INPUT Excel automatically!

---

## 🆘 If Link Doesn't Work

Alternative ways to get API key:

1. **Google AI Studio:** https://aistudio.google.com
2. **Google Cloud Console:** https://console.cloud.google.com/apis/credentials
3. **MakerSuite:** https://makersuite.google.com

All lead to the same place - just click "Create API Key"

---

## 💡 Quick Test

After adding key, test with:

```bash
python -c "import os; print('Key found!' if os.getenv('GEMINI_API_KEY') else 'Key not found')"
```
