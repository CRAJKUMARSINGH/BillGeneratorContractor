# BROWSER TEST GUIDE
## Testing Excel-Like Grid in Browser

**Date:** March 1, 2026  
**Mode:** Online Entry with Excel-Like Grid (Phase 2)

---

## STEP-BY-STEP TESTING INSTRUCTIONS

### Step 1: Open the App
The Streamlit app should automatically open in your browser at:
```
http://localhost:8501
```

If it doesn't open automatically, manually open your browser and go to that URL.

---

### Step 2: Select Online Entry Mode

1. Look at the **left sidebar**
2. Find the mode selector dropdown
3. Select: **"💻 Online Entry"**

---

### Step 3: Enable Excel-Like Grid (Phase 2)

In the sidebar, you should see:
```
🆕 Use Excel-Like Grid (Phase 2) [✓]
```

**Make sure this checkbox is CHECKED** (it should be by default)

---

### Step 4: Upload Test Excel File

**Recommended Test Files (from TEST_INPUT_FILES folder):**

**Option 1 (Recommended):**
```
TEST_INPUT_FILES/FirstFINALvidExtra.xlsx
```

**Option 2:**
```
TEST_INPUT_FILES/3rdFinalVidExtra.xlsx
```

**Option 3:**
```
TEST_INPUT_FILES/0511Wextra.xlsx
```

**Steps:**
1. Click the **"Upload Excel file (optional)"** button
2. Navigate to: `TEST_INPUT_FILES` folder
3. Select one of the files above (recommend: `FirstFINALvidExtra.xlsx`)
4. Click **Open**
5. Wait for "✅ Data extracted successfully!" message

---

### Step 5: Verify Excel-Like Grid

After upload, you should see:

**Project Details (Auto-Filled):**
- Name of Work: [Extracted from Excel]
- Contractor Name: [Extracted from Excel]
- Bill Date: [Can be set]
- Tender Premium: 4.0%

**Excel-Like Grid:**
```
┌─────────┬──────────────────┬──────┬──────────┬─────────┬──────────┐
│ Item No │ Description      │ Unit │ Quantity │ Rate    │ Amount   │
├─────────┼──────────────────┼──────┼──────────┼─────────┼──────────┤
│ 001     │ [From Excel]     │ CUM  │ 100.00   │ 500.00  │ ₹50,000  │
│ 002     │ [From Excel]     │ SQM  │ 50.00    │ 5000.00 │ ₹250,000 │
│ 003     │ [From Excel]     │ MT   │ 10.00    │ 50000.00│ ₹500,000 │
│ ...     │ ...              │ ...  │ ...      │ ...     │ ...      │
└─────────┴──────────────────┴──────┴──────────┴─────────┴──────────┘
```

---

### Step 6: Test Excel-Like Editing

**Test 1: Click to Edit**
1. Click on any cell in the grid
2. Type new value
3. Press **Tab** to move to next cell
4. Press **Enter** to move down

**Test 2: Activate Zero-Qty Items**
1. Find items with Quantity = 0.00
2. Click on the Quantity cell
3. Enter a value (e.g., 50.00)
4. Press Tab or Enter
5. Watch Amount auto-calculate

**Test 3: Part-Rate Payment**
1. Find an item with quantity > 0
2. Click on the Rate cell
3. Reduce the rate by ₹5 (e.g., 500 → 495)
4. Press Tab or Enter
5. Watch Amount recalculate

**Test 4: Add More Rows**
1. Scroll down below the grid
2. Click **"➕ Add 5 Rows"** button
3. Watch 5 new rows appear
4. Try **"➕ Add 10 Rows"** button

---

### Step 7: Verify Change Tracking

After making edits:
1. Scroll down to **"Change Log"** section
2. Click to expand
3. Verify your changes are tracked:
   - Timestamp
   - Item number
   - Field changed
   - Old value → New value
   - Reason

---

### Step 8: Check Summary

Look at the summary metrics:
```
Total Amount:    ₹XXX,XXX.XX
Premium (4%):    ₹XX,XXX.XX
NET PAYABLE:     ₹XXX,XXX.XX
Active Items:    XX/XX
```

Verify calculations are correct.

---

### Step 9: Generate Documents

1. Scroll down to **"Document Generation Options"**
2. Check desired formats:
   - ✓ HTML
   - ✓ PDF
   - ✓ DOCX (optional)
3. Click **"🚀 Generate Documents"** button
4. Wait for generation to complete

---

### Step 10: Download and Verify

After generation:

**Download All:**
1. Click **"📦 Download All (ZIP)"**
2. Extract ZIP file
3. Verify contents:
   - `html/` folder with HTML documents
   - `pdf/` folder with PDF documents
   - `excel/bill_data.xlsx` with edited data + change log

**Verify Excel Export:**
1. Open `excel/bill_data.xlsx`
2. Check **Title** sheet
3. Check **Bill Quantity** sheet (your edited data)
4. Check **Change Log** sheet (your changes)

---

## WHAT TO TEST

### ✅ Excel-Like Grid Features

1. **Inline Editing**
   - Click any cell to edit
   - Type directly in cell
   - Changes save automatically

2. **Keyboard Navigation**
   - Tab: Move to next cell
   - Enter: Move down
   - Click: Jump to any cell

3. **Auto-Calculation**
   - Amount = Quantity × Rate
   - Updates automatically
   - Accurate calculations

4. **Dynamic Rows**
   - Add 5 rows button works
   - Add 10 rows button works
   - Item numbering continues correctly

5. **Unit Dropdown**
   - Click Unit cell
   - Select from dropdown
   - Options: NOS, CUM, SQM, RMT, MT, KG, LTR, SET, LS

### ✅ Integration Features

1. **Excel Upload**
   - File uploads successfully
   - Data extracts correctly
   - Grid populates automatically

2. **Change Tracking**
   - Changes are logged
   - Timestamp recorded
   - Old/new values shown
   - Reason captured

3. **Excel Export**
   - Excel file created
   - Change log included
   - Formatting preserved

4. **Document Generation**
   - HTML generated
   - PDF generated
   - DOCX generated (if selected)
   - ZIP download works

---

## EXPECTED BEHAVIOR

### ✅ Should Work

- Click any cell to edit ✅
- Tab to next cell ✅
- Enter to move down ✅
- Auto-calculate amounts ✅
- Add rows dynamically ✅
- Track changes automatically ✅
- Export to Excel with change log ✅
- Generate documents ✅

### 🟡 May Need Enhancement

- Arrow keys (up/down/left/right) 🟡
- Ctrl+C / Ctrl+V (advanced copy/paste) 🟡
- Ctrl+Z / Ctrl+Y (undo/redo) 🟡
- Multi-cell selection 🟡
- Column resizing 🟡

---

## TROUBLESHOOTING

### Issue: Grid Not Showing
**Solution:** Make sure "🆕 Use Excel-Like Grid (Phase 2)" is checked in sidebar

### Issue: Excel Upload Fails
**Solution:** 
- Check file format (.xlsx, .xls, .xlsm)
- Try a different Excel file
- Check console for errors

### Issue: Changes Not Tracked
**Solution:**
- Make sure you're editing cells (not just clicking)
- Press Tab or Enter after editing
- Check Change Log section

### Issue: Documents Not Generating
**Solution:**
- Make sure Project Name is filled
- Make sure at least 1 item has Quantity > 0 and Rate > 0
- Check browser console for errors

---

## COMPARISON: OLD vs NEW

### OLD (Form-Based) 🔴
```
Item 1:
  Item No:      [text input]
  Description:  [text input]
  Quantity:     [number input]
  Rate:         [number input]

Item 2:
  Item No:      [text input]
  Description:  [text input]
  ...
```
**Problems:** Slow, no keyboard nav, no Excel feel

### NEW (Excel-Like Grid) ✅
```
┌─────────┬──────────────┬──────┬──────────┬─────────┬──────────┐
│ Item No │ Description  │ Unit │ Quantity │ Rate    │ Amount   │
├─────────┼──────────────┼──────┼──────────┼─────────┼──────────┤
│ 001     │ [click edit] │ NOS  │ [edit]   │ [edit]  │ ₹0.00    │
│ 002     │ [click edit] │ CUM  │ [edit]   │ [edit]  │ ₹0.00    │
└─────────┴──────────────┴──────┴──────────┴─────────┴──────────┘
```
**Benefits:** Fast, keyboard nav, Excel-like feel

---

## TEST CHECKLIST

Use this checklist while testing:

- [ ] App opens in browser
- [ ] Online Entry mode selected
- [ ] Excel-like grid checkbox enabled
- [ ] Excel file uploaded successfully
- [ ] Project details auto-filled
- [ ] Grid shows extracted data
- [ ] Can click cells to edit
- [ ] Tab moves to next cell
- [ ] Enter moves down
- [ ] Amounts auto-calculate
- [ ] Can add 5 rows
- [ ] Can add 10 rows
- [ ] Unit dropdown works
- [ ] Zero-qty items can be activated
- [ ] Rate can be reduced (part-rate)
- [ ] Changes appear in change log
- [ ] Summary shows correct totals
- [ ] Documents generate successfully
- [ ] ZIP download works
- [ ] Excel export includes change log

---

## FEEDBACK

After testing, note:

**What Works Well:**
- [Your observations]

**What Needs Improvement:**
- [Your observations]

**Bugs Found:**
- [Any issues]

**Suggestions:**
- [Your ideas]

---

## NEXT STEPS AFTER TESTING

1. **If everything works:** Ready for production deployment
2. **If issues found:** Document and fix before deployment
3. **Performance test:** Try with 1000+ rows
4. **User acceptance:** Get feedback from actual users

---

**Happy Testing!** 🚀

The Excel-like grid is a major improvement over the form-based UI. Enjoy the Excel-like experience in your browser!
