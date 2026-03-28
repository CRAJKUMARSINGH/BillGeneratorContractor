# Quick Start Guide - Updated BillGenerator Historical

## What's New? 🎉

Your root `app.py` has been updated to match the modern architecture of `BillGeneratorUnified`! Here's what you get:

### ✨ New Features
- **Configuration-Driven**: Easy customization via JSON files
- **Modern UI**: Beautiful green theme with fluorescent upload buttons
- **Cache Management**: Automatic cleanup of temporary files
- **Download Center**: Centralized file management
- **Feature Flags**: Enable/disable features without code changes
- **Fallback Support**: Works standalone or with BillGeneratorUnified modules

## Running the Application

### Option 1: Standard Mode (Recommended)
```bash
streamlit run app.py
```

### Option 2: With Custom Configuration
```bash
BILL_CONFIG=config/app_config.json streamlit run app.py
```

### Option 3: With Environment Variables
```bash
APP_NAME="My Bill Generator" APP_MODE="Production" streamlit run app.py
```

## Available Modes

### 📊 Excel Upload
Upload individual Excel files for processing
- Supports .xlsx and .xls formats
- Real-time processing
- Download PDFs and Word documents

### 🧪 Test Run (Sample Files)
Test with pre-loaded sample files
- Uses files from `test_input_files/` folder
- Perfect for testing and demonstrations
- No upload required

### 📦 Batch Process All Files
Process multiple files at once
- Batch processing of all files in `test_input_files/`
- Creates master ZIP with all outputs
- Progress tracking and detailed results

### 📥 Download Center
Manage generated files
- View all generated documents
- Download individual files or ZIP archives
- Clean old files to free space

## Configuration

### Basic Configuration
Edit `config/app_config.json`:

```json
{
  "app_name": "BillGenerator Historical",
  "version": "2.0.0",
  "features": {
    "excel_upload": true,
    "batch_processing": true,
    "advanced_pdf": true
  }
}
```

### Enable/Disable Features
```json
{
  "features": {
    "excel_upload": true,        // ✅ Enable Excel upload
    "online_entry": false,       // ❌ Disable online entry
    "batch_processing": true,    // ✅ Enable batch mode
    "analytics": false           // ❌ Disable analytics
  }
}
```

### Customize Branding
```json
{
  "ui": {
    "branding": {
      "title": "My Custom Bill Generator",
      "icon": "🏗️",
      "color": "#00b894"
    }
  }
}
```

## Maintenance Tools

### Clean Cache
Click "🧹 Clean Cache & Temp Files" in the sidebar to:
- Remove `__pycache__` directories
- Delete `.pyc` compiled files
- Clean temporary cache files

### Clean Old Outputs
Click "🗑️ Clean Old Output Files" in the sidebar to:
- Delete old generated files
- Keep only the latest 10 files
- Free up disk space

### Automatic Cleaning
Enable in configuration:
```json
{
  "processing": {
    "auto_clean_cache": true
  }
}
```

## File Structure

```
Root/
├── app.py                      # ✅ Updated main application
├── config/
│   └── app_config.json        # ✅ Configuration file
├── BillGeneratorUnified/      # Reference implementation
│   ├── app.py
│   └── core/                  # Shared modules
├── test_input_files/          # Sample Excel files
├── batch_outputs/             # Batch processing outputs
├── test_outputs/              # Test run outputs
└── uploaded_outputs/          # Upload mode outputs
```

## Troubleshooting

### Issue: "BillGeneratorUnified modules not found"
**Cause**: BillGeneratorUnified folder is missing or incomplete
**Solution**: 
- Ensure `BillGeneratorUnified/` folder exists in root
- Check that `BillGeneratorUnified/core/` contains required modules
- App will use fallback mode if modules are unavailable

### Issue: "Configuration file not loading"
**Cause**: Invalid JSON or missing file
**Solution**:
- Verify `config/app_config.json` exists
- Check JSON syntax (use a JSON validator)
- App will use default configuration if file is invalid

### Issue: "Cache cleaning not working"
**Cause**: Permission issues
**Solution**:
- Check write permissions in application directory
- Run with appropriate user permissions
- Manually delete cache folders if needed

### Issue: "Download Center not available"
**Cause**: BillGeneratorUnified modules not found
**Solution**:
- Ensure BillGeneratorUnified folder is present
- Check that core modules are installed
- Use other modes (Excel Upload, Batch Processing) as alternatives

## Tips & Best Practices

### 1. Regular Maintenance
- Clean cache weekly to prevent buildup
- Clean old outputs monthly to save space
- Monitor output folder size in sidebar

### 2. Configuration Management
- Keep backup of `config/app_config.json`
- Use environment variables for deployment-specific settings
- Document custom configurations

### 3. File Organization
- Use descriptive names for Excel files
- Organize sample files in `test_input_files/`
- Archive old outputs regularly

### 4. Performance Optimization
- Enable caching for faster processing
- Use batch mode for multiple files
- Clean cache before large batch operations

## Environment Variables

### Available Variables
```bash
# Application Settings
APP_NAME="Custom Name"
APP_VERSION="2.0.0"
APP_MODE="Production"

# Feature Flags
FEATURE_EXCEL_UPLOAD=true
FEATURE_BATCH_PROCESSING=true
FEATURE_ANALYTICS=false

# Processing Settings
PROCESSING_MAX_FILE_SIZE_MB=50
PROCESSING_AUTO_CLEAN_CACHE=true
PROCESSING_PDF_ENGINE=chrome_headless

# UI Settings
UI_THEME=default
BRANDING_TITLE="My Bill Generator"
BRANDING_ICON="📄"
BRANDING_COLOR="#00b894"
```

### Using Environment Variables
```bash
# Linux/Mac
export APP_NAME="My Bill Generator"
streamlit run app.py

# Windows (PowerShell)
$env:APP_NAME="My Bill Generator"
streamlit run app.py

# Windows (CMD)
set APP_NAME=My Bill Generator
streamlit run app.py
```

## Comparison with BillGeneratorUnified

### Similarities ✅
- Configuration-driven architecture
- Modern UI with green theme
- Cache management tools
- Feature flags support
- Download center integration

### Differences ⚠️
- Root app has fallback support for standalone operation
- BillGeneratorUnified has online entry mode (planned for root)
- Root app references BillGeneratorUnified modules
- Different default configuration files

### When to Use Each

**Use Root App (`app.py`) when:**
- You want a single entry point
- You need fallback support
- You're working with historical data
- You want automatic BillGeneratorUnified integration

**Use BillGeneratorUnified (`BillGeneratorUnified/app.py`) when:**
- You need online entry mode
- You want the latest features
- You're deploying to production
- You need full modular architecture

## Next Steps

### 1. Test the Application
```bash
streamlit run app.py
```

### 2. Try Different Modes
- Upload a test file in Excel Upload mode
- Run sample files in Test Run mode
- Process all files in Batch mode

### 3. Customize Configuration
- Edit `config/app_config.json`
- Enable/disable features
- Customize branding

### 4. Explore Advanced Features
- Use Download Center for file management
- Set up automatic cache cleaning
- Configure environment variables

## Support & Resources

### Documentation
- `UPDATE_NOTES.md` - Detailed update information
- `COMPARISON.md` - Comparison with BillGeneratorUnified
- `BillGeneratorUnified/README.md` - Reference documentation

### Getting Help
1. Check troubleshooting section above
2. Review error messages in the app
3. Check console output for detailed logs
4. Verify configuration file syntax

## Credits

**Prepared on Initiative of:**
Mrs. Premlata Jain, AAO
PWD Udaipur

**AI Development Partner:**
Kiro AI Assistant

**Architecture Reference:**
BillGeneratorUnified v2.0.0

---

**Status:** ✅ Ready to Use
**Last Updated:** February 23, 2026

🚀 **Happy Bill Generating!**
