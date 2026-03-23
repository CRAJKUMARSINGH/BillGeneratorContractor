# 📖 BillGenerator Unified - User Manual

## Welcome to BillGenerator Unified v2.0.0

A professional bill generation system for PWD (Public Works Department) that automatically generates all required documents from Excel files.

---

## 🚀 Quick Start Guide

### Step 1: Choose Your Mode

The application has 4 main modes:

1. **📊 Excel Upload** - Process single Excel file
2. **📦 Batch Processing** - Process multiple files at once
3. **💻 Online Entry** - Manual data entry (coming soon)
4. **📥 Download Center** - Access previously generated files

---

## 📊 Excel Upload Mode

### How to Use:

1. **Upload File**
   - Click the green upload area
   - Select your Excel file (.xlsx, .xls, .xlsm)
   - Supported formats: PWD bill Excel files

2. **Select Output Options**
   - ✅ **HTML** - Web-viewable documents
   - ✅ **PDF** - Print-ready documents (recommended)
   - ✅ **DOCX** - Editable Word documents

3. **Choose Save Location**
   - ✅ **Save to OUTPUT folder** - Files saved on server
   - ❌ **Uncheck** - Download directly to browser

4. **Generate Documents**
   - Click "🚀 Generate All Documents"
   - Wait for processing (usually 10-30 seconds)
   - Download individual files or ZIP package

### Generated Documents:

1. **First Page** - Bill summary and work details
2. **Deviation Statement** - Excess/shortage items (FINAL bills only)
3. **Bill Scrutiny Sheet** - Complete bill analysis (fits on ONE page)
4. **Certificate II** - Contractor certification
5. **Certificate III** - Payment certification with amounts
6. **Extra Items Slip** - Additional items (if any)

---

## 📦 Batch Processing Mode

### How to Use:

1. **Upload Multiple Files**
   - Click upload area
   - Select multiple Excel files (Ctrl+Click or Shift+Click)
   - All files will be processed together

2. **Select Options**
   - ✅ **HTML** - Generate HTML files
   - ✅ **PDF** - Generate PDF files
   - ✅ **DOCX** - Generate Word documents
   - ✅ **Folders** - Create separate folder per file

3. **Run Batch Processing**
   - Click "⚡ RUN BATCH PROCESSING"
   - Progress shown for each file
   - All files processed automatically

4. **Download Results**
   - Individual file downloads available
   - Or download complete ZIP package

### Benefits:
- Process 10+ files in minutes
- Consistent formatting across all bills
- Automatic organization by file name

---

## 📥 Download Center

Access all previously generated files:

- View by date
- Filter by file type (HTML, PDF, DOCX)
- Download individual files
- Bulk download options
- File size and timestamp information

---

## 📋 Document Specifications

### First Page
- **Format**: Portrait A4
- **Margins**: 10mm all sides
- **Content**: Work details, contractor info, bill summary
- **Features**: Complete item breakdown with quantities

### Deviation Statement
- **Format**: Landscape A4
- **Margins**: 10mm all sides
- **Content**: Excess/shortage items comparison
- **Note**: Generated only for FINAL bills

### Bill Scrutiny Sheet (Note Sheet)
- **Format**: Portrait A4
- **Margins**: 8mm all sides
- **Content**: 22 fields with complete bill analysis
- **Features**: 
  - Automatic delay calculation
  - Dynamic Hindi notes
  - Fits on ONE page
  - AAO signature: प्रेमलता जैन, AAO

### Certificate II
- **Format**: Portrait A4
- **Margins**: 10mm all sides
- **Content**: Contractor certification
- **Note**: Blank fields for manual entry (date, page, MB number)

### Certificate III
- **Format**: Portrait A4
- **Margins**: 10mm all sides
- **Content**: Payment certification
- **Features**:
  - Correct total including extra items
  - Amount in words (Indian numbering: Lakh, Crore)
  - All deductions listed

### Extra Items Slip
- **Format**: Portrait A4
- **Margins**: 10mm all sides
- **Content**: Extra items only (if any)
- **Features**:
  - Shows only extra items from input sheet
  - Tender premium calculation
  - Grand total with premium
  - Displayed as last document (#6)

---

## 💡 Tips & Best Practices

### Excel File Preparation:

1. **Use Standard Template**
   - Follow PWD Excel format
   - Include all required sheets
   - Fill mandatory fields

2. **Required Sheets**:
   - Title/Header information
   - Work order items
   - Extra items (if applicable)
   - Measurement details

3. **Data Quality**:
   - Ensure dates are in correct format
   - Verify amounts and quantities
   - Check contractor details
   - Confirm agreement numbers

### For Best Results:

1. **File Naming**
   - Use descriptive names
   - Include bill serial/number
   - Example: "FirstFINAL_Project123.xlsx"

2. **Batch Processing**
   - Group similar bills together
   - Process by project or contractor
   - Use separate folders option

3. **Output Management**
   - Regularly clean old files
   - Download important bills
   - Use ZIP for bulk downloads

---

## 🔧 Maintenance Features

### Cache Cleaning
- **Location**: Sidebar → Maintenance section
- **Purpose**: Remove temporary files
- **When**: Before processing new bills or if errors occur

### Output Folder Management
- **View Size**: See total space used
- **Clean Old Files**: Remove files older than specified date
- **Keep Latest**: Option to keep recent N files

---

## ⚙️ Advanced Features

### Document Customization:
- All amounts in whole rupees (note sheet)
- GST always even number
- Indian numbering system (Lakh, Crore)
- Automatic page breaks
- No content truncation

### Security Features:
- XSS prevention
- Formula injection protection
- Secure file handling
- No macro execution

### Performance:
- Fast processing (10-30 seconds per bill)
- Memory-efficient operations
- Parallel PDF generation
- Optimized ZIP creation

---

## 🐛 Troubleshooting

### Common Issues:

**1. File Upload Fails**
- Check file format (.xlsx, .xls, .xlsm)
- Verify file size (max 200MB)
- Ensure file is not corrupted

**2. PDF Generation Errors**
- Clean cache and try again
- Check if all required data is present
- Verify Excel file structure

**3. Missing Documents**
- Deviation Statement only for FINAL bills
- Extra Items Slip only if extra items exist
- Check bill serial number format

**4. Formatting Issues**
- Ensure Excel template is correct
- Verify all mandatory fields filled
- Check date formats

### Solutions:

1. **Clean Cache**
   - Click "🧹 Clean Cache & Temp Files" in sidebar
   - Restart processing

2. **Re-upload File**
   - Close and re-open file in Excel
   - Save as new file
   - Upload again

3. **Check Logs**
   - Error messages shown in app
   - Contact support with error details

---

## 📞 Support Information

### Prepared By:
**Mrs. Premlata Jain, AAO**  
PWD Udaipur

### Development Partner:
**Kiro AI Assistant**

### Repository:
https://github.com/CRAJKUMARSINGH/BillGeneratorUnified

### Version:
2.0.0 (Production Ready)

---

## 📝 Document Checklist

Before submitting generated bills, verify:

- ✅ All 6 documents generated (or 5 if no extra items)
- ✅ Contractor name and details correct
- ✅ Work description accurate
- ✅ Agreement number matches
- ✅ Bill serial number correct
- ✅ Amounts match Excel file
- ✅ Dates are accurate
- ✅ Certificate II fields filled manually
- ✅ All signatures in place
- ✅ Documents printed clearly

---

## 🎯 Key Features Summary

✅ **6 Documents** - Complete bill package  
✅ **Multiple Formats** - HTML, PDF, DOCX  
✅ **Batch Processing** - Process multiple files  
✅ **One Page Note Sheet** - Optimized layout  
✅ **Accurate Calculations** - Including extra items  
✅ **Indian Numbering** - Lakh, Crore format  
✅ **Auto Delay Calculation** - Smart date handling  
✅ **Clean Output** - Professional formatting  
✅ **Fast Processing** - 10-30 seconds per bill  
✅ **Easy Download** - Individual or ZIP  

---

## 🚀 Ready to Start?

1. Select **Excel Upload** or **Batch Processing** mode
2. Upload your Excel file(s)
3. Choose output options
4. Click Generate
5. Download your documents

**That's it! Your professional bill package is ready.**

---

*For technical support or feature requests, please contact the development team or create an issue on GitHub.*

**Version**: 2.0.0  
**Last Updated**: February 24, 2026  
**Status**: Production Ready ✅
