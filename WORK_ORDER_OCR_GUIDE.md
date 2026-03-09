# Work Order Image to Excel - Processing Guide

## Current Status

✅ **First Bill Processing**: Successfully processed `FirstFINALnoExtra.xlsx` and generated HTML documents
- Certificate II
- Certificate III  
- BILL SCRUTINY SHEET
- First Page Summary

📁 **Output Location**: `E:\Rajkumar\BillGeneratorContractor\OUTPUT`

## Work Order Image Processing

### Available Images
Located in: `INPUT/work_order_samples/work_01_27022026/`
- WhatsApp Image 2026-02-25 at 1.13.49 PM.jpeg
- WhatsApp Image 2026-02-25 at 1.14.08 PM.jpeg
- WhatsApp Image 2026-02-25 at 1.14.51 PM.jpeg
- WhatsApp Image 2026-02-25 at 1.15.04 PM.jpeg
- WhatsApp Image 2026-02-25 at 1.15.19 PM.jpeg

### OCR Capabilities

The system has built-in OCR capabilities to extract text from work order images and create Excel files:

**Features:**
- ✅ OCR Engine with Tesseract support
- ✅ English + Hindi language support
- ✅ Image preprocessing for better accuracy
- ✅ Automatic item extraction (item numbers, descriptions, units)
- ✅ Excel generation with multiple sheets (Title, Work Order, Bill Quantity, Extra Items)
- ✅ Confidence scoring for extracted data

### Required Dependencies

To use OCR functionality, you need to install:

1. **Python packages** (add to requirements.txt if missing):
   ```bash
   pip install pytesseract pillow opencv-python-headless
   ```

2. **Tesseract OCR Engine**:
   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
   - Install and add to PATH
   - Default location: `C:\Program Files\Tesseract-OCR\tesseract.exe`

### How to Process Work Order Images

#### Option 1: Using Simple OCR Script (Recommended)

```bash
python simple_ocr_to_excel.py "INPUT/work_order_samples/work_01_27022026"
```

**Output:**
- `OUTPUT/work_order_extracted.xlsx` - Excel file with extracted data
- `OUTPUT/work_order_raw_text.txt` - Raw OCR text for verification

#### Option 2: Using Advanced Document Processor

```bash
python process_work_order_images.py "INPUT/work_order_samples/work_01_27022026"
```

**Features:**
- Advanced image preprocessing
- Better item detection
- Confidence scoring
- Detailed reports

#### Option 3: Using Streamlit App

```bash
streamlit run app.py
```

Then select "📄 Document Upload" mode from the sidebar.

### Manual Alternative (If OCR Not Available)

If OCR dependencies cannot be installed:

1. **Open images in browser or image viewer**
2. **Manually create Excel file** with this structure:

**Sheet 1: Title**
| Field | Value |
|-------|-------|
| Work Name | [Enter work name] |
| Agreement Number | [Enter number] |
| Contractor Name | [Enter name] |
| Bill Type | First/Running/Final |
| Bill Number | [Enter number] |
| Date | [Enter date] |

**Sheet 2: Work Order**
| Item Number | Description | Unit | Quantity | Rate | Amount | Remarks |
|-------------|-------------|------|----------|------|--------|---------|
| 1 | [Description] | sqm | | | | |
| 2 | [Description] | cum | | | | |

**Sheet 3: Bill Quantity**
(Same structure as Work Order - copy and edit quantities)

**Sheet 4: Extra Items**
| Item Number | Description | Unit | Quantity | Rate | Amount | Deviation % | Remarks |
|-------------|-------------|------|----------|------|--------|-------------|---------|

3. **Save as**: `work_order_manual.xlsx`
4. **Process using**: `python process_first_bill.py work_order_manual.xlsx`

### Verification Steps

After OCR extraction:

1. ✅ **Review raw text file** - Check OCR accuracy
2. ✅ **Verify Excel data** - Ensure items are correctly parsed
3. ✅ **Check item numbers** - Confirm sequential numbering
4. ✅ **Validate descriptions** - Fix any OCR errors
5. ✅ **Add missing data** - Fill in quantities, rates, amounts
6. ✅ **Process bill** - Use the corrected Excel file

### Common OCR Issues

| Issue | Solution |
|-------|----------|
| Poor image quality | Use higher resolution images |
| Handwritten text | OCR works best with printed text |
| Mixed languages | Ensure lang='eng+hin' is set |
| Table detection | May need manual formatting |
| Special characters | Review and correct manually |

### Next Steps

1. **Install Tesseract OCR** (if not already installed)
2. **Install Python packages**: `pip install pytesseract pillow`
3. **Run OCR script**: `python simple_ocr_to_excel.py`
4. **Review and correct** the generated Excel file
5. **Process bill**: `python process_first_bill.py OUTPUT/work_order_extracted.xlsx`

### Support Files Created

- ✅ `process_first_bill.py` - Process Excel and generate bill documents
- ✅ `simple_ocr_to_excel.py` - Simple OCR to Excel converter
- ✅ `process_work_order_images.py` - Advanced OCR processor
- ✅ `generate_pdf_from_html.py` - HTML to PDF converter

### Contact & Credits

**Prepared on Initiative of:**
Mrs. Premlata Jain, AAO
PWD Udaipur

**AI Development Partner:** Kiro AI Assistant

---

## Quick Reference Commands

```bash
# Process existing Excel file
python process_first_bill.py "TEST_INPUT_FILES/FirstFINALnoExtra.xlsx"

# Extract work order from images (requires Tesseract)
python simple_ocr_to_excel.py "INPUT/work_order_samples/work_01_27022026"

# Generate PDF from HTML
python generate_pdf_from_html.py "OUTPUT/FirstFINALnoExtra_First_Page_Summary.html"

# Run Streamlit app
streamlit run app.py
```
