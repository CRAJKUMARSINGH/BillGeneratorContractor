# Install Tesseract OCR for Windows

## Quick Installation Steps

### Option 1: Download Installer (Recommended)

1. **Download Tesseract OCR Installer:**
   - Go to: https://github.com/UB-Mannheim/tesseract/wiki
   - Download: `tesseract-ocr-w64-setup-5.3.3.20231005.exe` (or latest version)
   - Or direct link: https://digi.bib.uni-mannheim.de/tesseract/

2. **Run the Installer:**
   - Double-click the downloaded .exe file
   - **IMPORTANT:** During installation, select "Additional language data"
   - Check: ✅ English
   - Check: ✅ Hindi (हिन्दी)
   - Default install location: `C:\Program Files\Tesseract-OCR`

3. **Add to PATH (if not done automatically):**
   - Right-click "This PC" → Properties → Advanced system settings
   - Click "Environment Variables"
   - Under "System variables", find "Path"
   - Click "Edit" → "New"
   - Add: `C:\Program Files\Tesseract-OCR`
   - Click OK on all dialogs

4. **Verify Installation:**
   ```bash
   tesseract --version
   ```

### Option 2: Using Chocolatey (if you have it)

```bash
choco install tesseract
```

### Option 3: Using Scoop (if you have it)

```bash
scoop install tesseract
```

## After Installation

Once Tesseract is installed, run:

```bash
# Process work order images
python simple_ocr_to_excel.py "INPUT/work_order_samples/work_01_27022026"
```

## Troubleshooting

### If Python can't find Tesseract

Add this to your script or set environment variable:

```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

Or set environment variable:
```bash
setx TESSERACT_PATH "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

## Alternative: Use Online OCR Service

If you can't install Tesseract, you can:

1. Upload images to: https://www.onlineocr.net/
2. Download the extracted text
3. Manually create Excel file using the template in WORK_ORDER_OCR_GUIDE.md

## Quick Test

After installation, test with:

```bash
tesseract INPUT/work_order_samples/work_01_27022026/WhatsApp*.jpeg output.txt
```

This should create `output.txt` with extracted text.
