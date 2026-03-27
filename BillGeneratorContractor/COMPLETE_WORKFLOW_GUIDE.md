# Complete Workflow Guide - Bill Generation System

## 📋 What We Have

### ✅ Successfully Completed
1. **First Bill Processed** - `FirstFINALnoExtra.xlsx`
   - Generated 4 HTML documents
   - Location: `OUTPUT/` folder

2. **Work Order Template Created** - `work_order_template.xlsx`
   - Ready for manual data entry
   - Location: `OUTPUT/` folder

3. **Processing Scripts Ready**
   - `process_first_bill.py` - Main processor
   - `simple_ocr_to_excel.py` - OCR converter
   - `create_work_order_template.py` - Template creator
   - `generate_pdf_from_html.py` - PDF converter

### 📁 Available Data
- **Test Excel Files:** 8 files in `TEST_INPUT_FILES/`
- **Work Order Images:** 5 JPEG files in `INPUT/work_order_samples/work_01_27022026/`

---

## 🎯 Two Main Workflows

### Workflow A: Process Existing Excel Files ✅ WORKING

**Use when:** You already have Excel file with bill data

**Steps:**
```bash
# Process any Excel file
python process_first_bill.py "TEST_INPUT_FILES/FirstFINALnoExtra.xlsx"

# Or other test files
python process_first_bill.py "TEST_INPUT_FILES/FirstFINALvidExtra.xlsx"
python process_first_bill.py "TEST_INPUT_FILES/3rdFinalNoExtra.xlsx"
```

**Output:** HTML documents in `OUTPUT/` folder
- Certificate II
- Certificate III
- Bill Scrutiny Sheet
- First Page Summary

**To get PDF:** Open HTML in browser → Print → Save as PDF

---

### Workflow B: Create Excel from Work Order Images

**Use when:** You have work order images/PDFs and need to create Excel

#### Option B1: Manual Entry (RECOMMENDED - No dependencies)

**Step 1: Create Template**
```bash
python create_work_order_template.py
```
Output: `OUTPUT/work_order_template.xlsx`

**Step 2: View Images**
```bash
# Open folder with images
start INPUT\work_order_samples\work_01_27022026\
```

**Step 3: Open Template**
```bash
# Open Excel template
start OUTPUT\work_order_template.xlsx
```

**Step 4: Enter Data**
- Look at images on one side of screen
- Type data into Excel on other side
- Follow instructions in `OUTPUT/TEMPLATE_INSTRUCTIONS.txt`
- Refer to `VIEW_WORK_ORDER_IMAGES.md` for guidance

**Step 5: Process**
```bash
python process_first_bill.py OUTPUT\work_order_template.xlsx
```

**Time Required:** 30-60 minutes depending on number of items

---

#### Option B2: Automatic OCR (Requires Tesseract Installation)

**Step 1: Install Tesseract OCR**
- Download: https://github.com/UB-Mannheim/tesseract/wiki
- Install with English + Hindi support
- Add to PATH
- See `INSTALL_TESSERACT.md` for details

**Step 2: Run OCR**
```bash
python simple_ocr_to_excel.py "INPUT\work_order_samples\work_01_27022026"
```

**Step 3: Review & Correct**
- Open `OUTPUT/work_order_extracted.xlsx`
- Check `OUTPUT/work_order_raw_text.txt` for accuracy
- Correct any OCR errors

**Step 4: Process**
```bash
python process_first_bill.py OUTPUT\work_order_extracted.xlsx
```

**Time Required:** 10-15 minutes (mostly for verification)

---

## 📊 Excel File Structure

All Excel files must have these 4 sheets:

### Sheet 1: Title
| Field | Value |
|-------|-------|
| Work Name | Project name |
| Agreement Number | Agreement no. |
| Contractor Name | Contractor name |
| Bill Type | First/Running/Final |
| Bill Number | Bill number |
| Date | DD/MM/YYYY |

### Sheet 2: Work Order
| Item Number | Description | Unit | Quantity | Rate | Amount | Remarks |
|-------------|-------------|------|----------|------|--------|---------|
| 1 | Item description | sqm | 100 | 50 | 5000 | |
| 2 | Item description | cum | 50 | 500 | 25000 | |

### Sheet 3: Bill Quantity
(Same structure as Work Order - actual quantities)

### Sheet 4: Extra Items
| Item Number | Description | Unit | Quantity | Rate | Amount | Deviation % | Remarks |
|-------------|-------------|------|----------|------|--------|-------------|---------|
| E1 | Extra item | sqm | 10 | 50 | 500 | 5% | |

---

## 🚀 Quick Start Commands

### Process First Bill (Already Done ✅)
```bash
python process_first_bill.py "TEST_INPUT_FILES/FirstFINALnoExtra.xlsx"
```

### Create Work Order Template
```bash
python create_work_order_template.py
```

### View Work Order Images
```bash
start INPUT\work_order_samples\work_01_27022026\
```

### Process Template After Filling
```bash
python process_first_bill.py OUTPUT\work_order_template.xlsx
```

### Run Streamlit Web Interface
```bash
streamlit run app.py
```

---

## 📂 File Locations

### Input Files
```
TEST_INPUT_FILES/
├── FirstFINALnoExtra.xlsx ✅ (Processed)
├── FirstFINALvidExtra.xlsx
├── 3rdFinalNoExtra.xlsx
├── 3rdFinalVidExtra.xlsx
├── 3rdRunningNoExtra.xlsx
├── 3rdRunningVidExtra.xlsx
├── 0511-N-extra.xlsx
└── 0511Wextra.xlsx

INPUT/work_order_samples/work_01_27022026/
├── WhatsApp Image 2026-02-25 at 1.13.49 PM.jpeg
├── WhatsApp Image 2026-02-25 at 1.14.08 PM.jpeg
├── WhatsApp Image 2026-02-25 at 1.14.51 PM.jpeg
├── WhatsApp Image 2026-02-25 at 1.15.04 PM.jpeg
└── WhatsApp Image 2026-02-25 at 1.15.19 PM.jpeg
```

### Output Files
```
OUTPUT/
├── FirstFINALnoExtra_Certificate_II.html ✅
├── FirstFINALnoExtra_Certificate_III.html ✅
├── FirstFINALnoExtra_BILL_SCRUTINY_SHEET.html ✅
├── FirstFINALnoExtra_First_Page_Summary.html ✅
├── work_order_template.xlsx ✅
└── TEMPLATE_INSTRUCTIONS.txt ✅
```

### Documentation
```
├── COMPLETE_WORKFLOW_GUIDE.md (this file)
├── SESSION_SUMMARY.md
├── WORK_ORDER_OCR_GUIDE.md
├── VIEW_WORK_ORDER_IMAGES.md
├── INSTALL_TESSERACT.md
├── USER_MANUAL.md
└── USER_MANUAL_HINDI.md
```

---

## 🔧 Troubleshooting

### Issue: PDF not generating
**Solution:** 
- HTML files are generated successfully
- Open HTML in Chrome/Edge
- Press Ctrl+P (Print)
- Select "Save as PDF"
- Or install: `pip install xhtml2pdf`

### Issue: OCR not working
**Solution:**
- Install Tesseract OCR (see INSTALL_TESSERACT.md)
- Or use manual data entry (Option B1)

### Issue: Excel file not processing
**Check:**
- File has all 4 sheets (Title, Work Order, Bill Quantity, Extra Items)
- Column names match exactly
- No empty required fields
- Numbers are formatted correctly (no commas or currency symbols)

### Issue: Import errors
**Solution:**
```bash
pip install -r requirements.txt
```

---

## 📞 Support & Credits

**Prepared on Initiative of:**
Mrs. Premlata Jain, AAO
PWD Udaipur

**AI Development Partner:** Kiro AI Assistant

**System Version:** BillGenerator Unified v2.0.0

---

## ✅ Current Status Summary

| Task | Status | Location |
|------|--------|----------|
| First Bill Processing | ✅ Complete | OUTPUT/ |
| Work Order Template | ✅ Created | OUTPUT/work_order_template.xlsx |
| Processing Scripts | ✅ Ready | Root directory |
| Documentation | ✅ Complete | Multiple .md files |
| OCR Setup | ⏳ Pending | Requires Tesseract |
| PDF Generation | ⚠️ Workaround | Use browser Print to PDF |

---

## 🎯 Recommended Next Steps

### For Immediate Use (No additional setup needed):

1. **Open work order template:**
   ```bash
   start OUTPUT\work_order_template.xlsx
   ```

2. **View work order images:**
   ```bash
   start INPUT\work_order_samples\work_01_27022026\
   ```

3. **Fill in data manually** (30-60 minutes)

4. **Process the filled template:**
   ```bash
   python process_first_bill.py OUTPUT\work_order_template.xlsx
   ```

5. **View generated HTML files** in OUTPUT folder

6. **Convert to PDF** using browser Print function

### For Future Automation:

1. **Install Tesseract OCR** (see INSTALL_TESSERACT.md)
2. **Run OCR script** for automatic extraction
3. **Verify and correct** OCR output
4. **Process** as usual

---

## 📖 Additional Resources

- **Full User Manual:** `USER_MANUAL.md`
- **Hindi Manual:** `USER_MANUAL_HINDI.md`
- **Video Guide Script:** `VIDEO_GUIDE_SCRIPT.md`
- **Deployment Guide:** `DEPLOYMENT.md`

---

**Last Updated:** March 9, 2026
**Status:** Ready for Production Use
