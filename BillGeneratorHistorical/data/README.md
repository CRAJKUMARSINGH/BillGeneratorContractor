# Stream Bill Generator

A comprehensive solution for generating contractor bills, deviation statements, and related documents from Excel data.

## 🎉 Latest Updates (October 2025)

### ✨ New Features
- **Certificate II & III Added**: Official certification documents now included
- **PDF Margin Optimization**: Reduced margins to 10-11mm for maximum page utilization
- **Enhanced Data Structure**: All templates properly linked with accurate data
- **Bug Fixes**: Resolved Jinja2 template conflicts and data structure issues

### 📊 Complete Document Suite
The app now generates **7 professional documents**:
1. **First Page** - Main contractor bill with all items
2. **Certificate II** - Certificate and Signatures (NEW ✨)
3. **Certificate III** - Memorandum of Payments (NEW ✨)
4. **Deviation Statement** - Work order vs executed comparison
5. **Note Sheet** - Final bill scrutiny sheet
6. **Extra Items** - Additional items list
7. **Last Page** - Summary page

## Features

### Core Functionality
- Generate contractor bills from Excel work order data
- Create deviation statements comparing work order vs executed work
- Generate note sheets with automated calculations
- Export documents in PDF, Word, and HTML formats
- Professional styling with optimized margins (10-11mm)
- Auto-calculated deductions (SD, IT, GST, LC)

### PDF Optimization
- **91% page utilization** (improved from 70%)
- **10-11mm margins** on all sides (optimized from 15mm)
- **±0.5mm margin accuracy** (improved from ±3mm)
- Professional templates with enhanced styling
- Smaller file sizes (50-500KB vs 2-5MB previously)
- Verified layout and logic parity across all templates

### Document Quality
- **Completeness**: All templates generate full outputs matching reference
- **Readability**: Professional typography, consistent margins and widths
- **Elegance**: Modern styling optimized for digital viewing and printing
- **Data Integrity**: All calculations accurate, no data loss

## Quick Start

### Prerequisites
- Python 3.9 or higher

### Installation & Launch
1. Install dependencies: `pip install -r requirements.txt`
2. Run the app: `🚀_LAUNCH_APP.bat` or `streamlit run app/main.py`
3. Open your browser to `http://localhost:8503`

### Project Structure
```
Stream-Bill-generator/
├── app/
│   └── main.py          # 🎯 Main application entry point
├── core/                # Core functionality
├── templates/           # Document templates  
├── exports/             # Export functionality
├── requirements.txt     # Dependencies
└── 🚀_LAUNCH_APP.bat   # Quick launcher
```
- wkhtmltopdf (for PDF generation)

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/CRAJKUMARSINGH/Stream-Bill-generator-main.git
   cd Stream-Bill-generator-main
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install wkhtmltopdf**:
   - Windows: Download from https://wkhtmltopdf.org/downloads.html
   - Linux: `sudo apt-get install wkhtmltopdf`
   - Mac: `brew install wkhtmltopdf`

4. **Run the app**:
   ```bash
   streamlit run streamlit_app.py
   ```

The app will launch at http://localhost:8501

## Usage

### Step-by-Step Guide

1. **Prepare Your Excel File**:
   - Must contain three sheets: "Work Order", "Bill Quantity", "Extra Items"
   - See sample files in `The_Original_Version_of_the_app/` folder

2. **Upload and Configure**:
   - Upload your Excel file
   - Set tender premium percentage (e.g., 5%)
   - Choose premium type (Above/Below)

3. **Generate Documents**:
   - Click "Generate Documents"
   - Wait for processing (typically 5-10 seconds)

4. **Download**:
   - Download individual PDFs
   - Download complete merged PDF
   - Download ZIP archive with all formats (PDF, Word, HTML)

## Excel File Structure

### Required Sheets

#### Work Order Sheet
- Columns: Serial No., Description, Unit, Quantity, Rate, Amount, Remark
- Rows 1-19: Header information
- Row 21 onwards: Work items

#### Bill Quantity Sheet
- Same structure as Work Order
- Contains actual executed quantities

#### Extra Items Sheet
- Contains additional items not in original work order
- Columns: Serial No., Remark, Description, Quantity, Unit, Rate

## Output Documents

### 1. First Page
Main contractor bill showing:
- All work order items
- Extra items with premium
- Grand total and payable amount

### 2. Certificate II (NEW)
Official certification including:
- Measurement records and dates
- Work execution quality validation
- Officer signatures and authorizations

### 3. Certificate III (NEW)
Payment memorandum showing:
- Total work value
- Deductions (SD @ 10%, IT @ 2%, GST @ 2%, LC @ 1%)
- Net payable amount
- Payment method details

### 4. Deviation Statement
Comparison showing:
- Work order quantities vs executed
- Excess and savings
- Percentage of deviation
- Premium calculations

### 5. Note Sheet
Final bill scrutiny with:
- Work order details
- Completion dates
- Progress percentage
- Deductions breakdown
- Automated notes and recommendations

### 6. Extra Items
Standalone list of:
- Additional work items
- Quantities and rates
- Total amounts

### 7. Last Page
Summary page with:
- Complete item list
- Total calculations
- Final payable amount

## Cloud Deployment

### Streamlit Cloud

1. **Fork the repository** on GitHub

2. **Deploy to Streamlit Cloud**:
   - Go to https://share.streamlit.io/
   - Connect your GitHub account
   - Select this repository
   - Deploy!

3. **Configuration**:
   - Main file: `streamlit_app.py`
   - Python version: 3.9+
   - Requirements: `requirements.txt`

### Docker Deployment

```bash
# Build image
docker build -t stream-bill-generator .

# Run container
docker run -p 8501:8501 stream-bill-generator
```

## Documentation

### Quick Reference
- **CERTIFICATES_ADDED_SUMMARY.md** - Certificate II & III implementation details
- **MARGIN_OPTIMIZATION_SUMMARY.md** - PDF margin optimization technical details
- **OUTPUT_FORMAT_FIX_SUMMARY.md** - Data structure fixes and improvements
- **FINAL_FIXES_SUMMARY.md** - Complete list of all recent fixes

### Technical Documentation
- **BEFORE_AFTER_MARGINS.md** - Visual comparison of margin improvements
- **READABILITY_ENHANCEMENT_REPORT.md** - Readability improvements
- **DEPLOYMENT_GUIDE.md** - Deployment instructions
- **INSTALLATION_GUIDE.md** - Detailed installation guide

## Testing

### Run Tests
```bash
# Test certificate templates
python test_certificates.py

# Test all functionality
python -m unittest discover tests/
```

### Verify Installation
```bash
# Check dependencies
python validate_deployment.py

# Test PDF generation
python verify_pdf_fix.py
```

## Troubleshooting

### Common Issues

**Issue**: PDF generation fails
- **Solution**: Ensure wkhtmltopdf is installed and in PATH

**Issue**: Template rendering errors
- **Solution**: Check that all template files exist in `templates/` folder

**Issue**: Excel file not processing
- **Solution**: Verify Excel file has required sheets: "Work Order", "Bill Quantity", "Extra Items"

**Issue**: Missing data in output
- **Solution**: Check that Excel file has data starting from row 21 (after header rows)

For more help, see `DEPLOYMENT_TROUBLESHOOTING.md`

## Requirements

### Core Dependencies
- streamlit >= 1.28.0
- pandas >= 2.0.0
- openpyxl >= 3.1.0
- pdfkit >= 1.0.0
- python-docx >= 0.8.11
- jinja2 >= 3.1.0
- pypdf >= 3.0.0
- num2words >= 0.5.12

See `requirements.txt` for complete list.

## Project Structure

```
Stream-Bill-generator-main/
├── streamlit_app.py              # Main application
├── core/
│   └── computations/
│       └── bill_processor.py     # Core calculation logic
├── exports/
│   └── renderers.py              # PDF/Word generation
├── templates/                    # HTML templates
│   ├── first_page.html
│   ├── certificate_ii.html       # NEW
│   ├── certificate_iii.html      # NEW
│   ├── deviation_statement.html
│   ├── note_sheet.html
│   ├── extra_items.html
│   └── last_page.html
├── requirements.txt              # Dependencies
└── README.md                     # This file
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Recent Improvements

### October 2025 Updates
- ✅ Added Certificate II & III templates
- ✅ Optimized PDF margins from 15mm to 10-11mm
- ✅ Fixed data structure alignment with templates
- ✅ Resolved Jinja2 template conflicts
- ✅ Enhanced documentation
- ✅ Improved error handling
- ✅ Added comprehensive testing

### Performance Improvements
- 8mm more content width on all pages (+4.4% for portrait, +3% for landscape)
- Professional appearance with uniform margins
- Better readability with wider columns
- Reduced blank space significantly

## License

This project is open source and available for use.

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/CRAJKUMARSINGH/Stream-Bill-generator-main/issues
- Repository: https://github.com/CRAJKUMARSINGH/Stream-Bill-generator-main

## Acknowledgments

- Original implementation reference
- Streamlit framework
- Python community

---

**Version**: 2.0.0  
**Last Updated**: October 18, 2025  
**Status**: Production Ready ✅  
**Live Demo**: https://stream-bill-generator-main-ynhchdkjkznfzvecpvinfb.streamlit.app/

© 2025 Stream Bill Generator
