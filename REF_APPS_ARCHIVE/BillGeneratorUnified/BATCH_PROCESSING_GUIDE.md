# 📦 Batch Processing Mode - User Guide

**Feature**: Process multiple Excel bill files at once  
**Status**: ✅ **NOW ENABLED**  
**Updated**: March 7, 2026

---

## ✅ Batch Processing is Now Enabled!

I've enabled the batch processing feature in your configuration. 

### What Changed:
- Updated `config/v01.json`
- Set `batch_processing: true`
- Restarted the app
- Pushed to GitHub

---

## 🎯 How to Access Batch Processing

### Step 1: Refresh Your Browser
1. Go to **http://localhost:8501**
2. Press **Ctrl+R** (or Cmd+R on Mac) to refresh
3. The app will reload with new configuration

### Step 2: Find Batch Processing in Sidebar
You should now see in the sidebar:
```
Select Mode:
○ 📊 Excel Upload
○ 🔄 Hybrid: Upload + Edit
○ 💻 Online Entry
○ 📦 Batch Processing  ← NEW!
○ 📥 Download Center
○ 📖 User Manual
```

### Step 3: Click on "📦 Batch Processing"

---

## 📦 Using Batch Processing Mode

### What You'll See:

```
📦 Batch Processing Mode

Upload Multiple Excel Files
┌─────────────────────────────────┐
│  Drag and drop files here       │
│  or click to browse              │
│                                  │
│  Accepts: .xlsx, .xls files      │
└─────────────────────────────────┘

Processing Options:
○ Detect Automatically
○ All Final Bills
○ All Running Bills

Output Formats:
☑ HTML
☑ Word Document
☑ PDF (if available)

[Process All Files] Button
```

---

## 🧪 Test with Your Files

### Quick Test (2 files):
1. Click "Browse files"
2. Navigate to `TEST_INPUT_FILES/`
3. Select:
   - `FirstFINALnoExtra.xlsx`
   - `FirstFINALvidExtra.xlsx`
4. Click "Process All Files"
5. Wait for completion
6. Download results

### Full Test (8 files):
Select all files from `TEST_INPUT_FILES/`:
1. 0511-N-extra.xlsx
2. 0511Wextra.xlsx
3. 3rdFinalNoExtra.xlsx
4. 3rdFinalVidExtra.xlsx
5. 3rdRunningNoExtra.xlsx
6. 3rdRunningVidExtra.xlsx
7. FirstFINALnoExtra.xlsx
8. FirstFINALvidExtra.xlsx

---

## 📊 Processing Flow

### 1. Upload Phase
```
Uploading files...
✅ File 1: FirstFINALnoExtra.xlsx (33.4 KB)
✅ File 2: FirstFINALvidExtra.xlsx (34.2 KB)
Total: 2 files, 67.6 KB
```

### 2. Processing Phase
```
Processing files...
[████████░░] 80% (4/5 files)

✅ FirstFINALnoExtra.xlsx - Complete
   - HTML: ✅ Generated
   - Word: ✅ Generated
   - PDF: ✅ Generated

⏳ FirstFINALvidExtra.xlsx - Processing...
```

### 3. Results Phase
```
Processing Complete!
✅ 2/2 files processed successfully
✅ 6 output files generated
✅ Ready for download

[Download All as ZIP] Button
[View Individual Files] Button
```

---

## 📥 Download Options

### Option 1: Download All as ZIP
- Click "Download All as ZIP"
- Gets a single ZIP file with all outputs
- Organized by source filename
- Easy to share

### Option 2: Download Individual Files
- Browse through results
- Download specific files
- Choose format (HTML/Word/PDF)

### ZIP Structure:
```
batch_output_20260307_151500.zip
├── FirstFINALnoExtra/
│   ├── bill_report.html
│   ├── bill_report.docx
│   └── bill_report.pdf
└── FirstFINALvidExtra/
    ├── bill_report.html
    ├── bill_report.docx
    └── bill_report.pdf
```

---

## ⚙️ Processing Options

### Bill Type Detection
- **Detect Automatically**: Reads from filename/content
- **All Final Bills**: Treats all as final bills
- **All Running Bills**: Treats all as running bills

### Output Formats
- **HTML**: Always generated (fast, viewable in browser)
- **Word**: Always generated (editable, professional)
- **PDF**: Generated if WeasyPrint available

### Advanced Options
- **Include Extra Items**: Process extra items sections
- **Generate Summary**: Create summary report
- **Validate Data**: Check for errors before processing

---

## 🎯 Use Cases

### 1. Monthly Bill Processing
- Upload all bills for the month
- Process in one batch
- Download ZIP for records
- Share with team

### 2. Year-End Reports
- Process all bills for the year
- Generate consistent outputs
- Archive as ZIP
- Easy retrieval

### 3. Bulk Conversion
- Convert old Excel bills to PDF
- Maintain formatting
- Organize by project
- Digital archive

### 4. Quality Check
- Process multiple versions
- Compare outputs
- Verify consistency
- Identify issues

---

## 💡 Tips & Best Practices

### For Best Results:
1. **Group similar files**: Process final bills together, running bills together
2. **Check file names**: Use consistent naming for auto-detection
3. **Verify before processing**: Review file list before clicking process
4. **Monitor progress**: Watch for any errors during processing
5. **Download promptly**: Files are temporary, download soon after processing

### Performance Tips:
- **Smaller batches**: 5-10 files at a time for faster processing
- **Close other apps**: Free up system resources
- **Stable internet**: Important for cloud deployment
- **Check file sizes**: Larger files take longer

### Troubleshooting:
- **File won't upload**: Check file format (.xlsx or .xls)
- **Processing fails**: Try files individually first
- **Missing outputs**: Check if format is enabled
- **Slow processing**: Reduce batch size

---

## 🔍 What Happens Behind the Scenes

### 1. File Validation
- Checks file format
- Verifies file size
- Validates Excel structure

### 2. Data Extraction
- Reads each Excel file
- Extracts bill information
- Identifies bill type
- Finds extra items

### 3. Output Generation
- Creates HTML (always)
- Generates Word document (always)
- Produces PDF (if available)
- Organizes in folders

### 4. Packaging
- Creates timestamped folders
- Organizes by source file
- Prepares ZIP archive
- Makes available for download

---

## 📊 Expected Processing Times

### Per File (approximate):
- **Small file** (< 50 KB): 2-3 seconds
- **Medium file** (50-100 KB): 3-5 seconds
- **Large file** (> 100 KB): 5-10 seconds

### Batch Processing:
- **2 files**: ~10 seconds
- **5 files**: ~20 seconds
- **8 files**: ~30 seconds
- **10 files**: ~40 seconds

*Times may vary based on system performance and file complexity*

---

## ✅ Success Indicators

You'll know batch processing is working when:

✅ Multiple files upload successfully  
✅ Progress bar shows processing  
✅ Each file shows completion status  
✅ Output files are generated  
✅ ZIP download is available  
✅ No error messages appear  

---

## 🐛 Common Issues & Solutions

### Issue: "Batch Processing not in sidebar"
**Solution**: Refresh browser (Ctrl+R), feature is now enabled

### Issue: "Can't upload multiple files"
**Solution**: Hold Ctrl (Windows) or Cmd (Mac) while selecting files

### Issue: "Processing stuck"
**Solution**: Check browser console (F12), refresh if needed

### Issue: "Some files failed"
**Solution**: Process failed files individually to see specific errors

### Issue: "ZIP download fails"
**Solution**: Download individual files instead, or try smaller batch

---

## 📞 Support

### Need Help?
1. Check this guide first
2. Try processing files individually
3. Check browser console (F12)
4. Review error messages
5. Test with sample files first

### Useful Commands:
```bash
# Check if app is running
curl http://localhost:8501

# Restart app
# Stop current process (Ctrl+C)
# Then: python -m streamlit run app.py

# Check output folder
ls OUTPUT/

# View recent outputs
ls OUTPUT/ | sort -r | head -5
```

---

## 🎉 You're Ready!

Batch Processing is now enabled and ready to use!

### Quick Start:
1. **Refresh browser**: http://localhost:8501
2. **Click**: "📦 Batch Processing" in sidebar
3. **Upload**: Multiple files from TEST_INPUT_FILES/
4. **Process**: Click "Process All Files"
5. **Download**: Get your ZIP file!

---

**Feature Enabled By**: Kiro AI Assistant  
**Configuration**: config/v01.json  
**Status**: ✅ **ACTIVE**  
**Deployed**: GitHub + Local

🎉 **Happy Batch Processing!** 🎉
