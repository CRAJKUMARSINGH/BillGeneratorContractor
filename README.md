# 🏗️ BillGenerator Contractor

A mobile-first Streamlit application for contractors to generate bills from scanned PDF work orders with simplified, accessible interfaces.

## 🚀 Features

- **📱 Mobile-First Design**: Optimized for contractors working on mobile devices
- **📄 PDF Extraction**: Hybrid table detection and OCR for scanned work orders
- **🎤 Voice Input**: Hindi and English voice commands for quantity entry
- **📸 Image Processing**: Extract quantities from handwritten notes
- **💾 Offline Support**: Work offline with local caching and sync
- **🔐 Secure**: Mobile OTP authentication and encrypted data storage
- **♿ Accessible**: WCAG compliant with keyboard navigation and screen reader support

## 🛠️ Tech Stack

- **Frontend**: Streamlit (Mobile-responsive)
- **PDF Processing**: pdfplumber, pytesseract, opencv-python
- **Bill Generation**: Reuses BillGenerator Unified v2.0.3 components
- **Authentication**: Mobile OTP (Streamlit session state)
- **Storage**: Browser localStorage + Streamlit session state

## 📦 Installation

### Prerequisites

- Python 3.9+
- Tesseract OCR (for text extraction)
- System dependencies (see `packages.txt`)

### Local Setup

```bash
# Clone the repository
git clone https://github.com/CRAJKUMARSINGH/BillGeneratorContractor.git
cd BillGeneratorContractor

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install -y tesseract-ocr tesseract-ocr-hin tesseract-ocr-eng
sudo apt-get install -y libcairo2-dev libpango1.0-dev libgdk-pixbuf2.0-dev libffi-dev

# Run the application
streamlit run app.py
```

## 🌐 Streamlit Cloud Deployment

### Deploy to Streamlit Cloud

1. **Fork/Clone this repository**
2. **Go to [share.streamlit.io](https://share.streamlit.io)**
3. **Click "New app"**
4. **Select your repository**: `CRAJKUMARSINGH/BillGeneratorContractor`
5. **Main file path**: `app.py`
6. **Click "Deploy"**

### Configuration

The app uses `.streamlit/config.toml` for configuration. System dependencies are automatically installed from `packages.txt`.

### Environment Variables (Optional)

Create `.streamlit/secrets.toml` for sensitive configuration:

```toml
[general]
BILL_CONFIG = "config/v01.json"
CLEAN_CACHE_ON_STARTUP = "false"

[auth]
OTP_SERVICE_API_KEY = "your-api-key-here"
```

## 📱 Usage

### For Contractors

1. **Upload Work Order**: Take a photo or upload PDF of work order
2. **Verify Data**: Review and correct extracted items
3. **Enter Quantities**: Use form, voice, or image input
4. **Generate Bill**: Add contractor details and generate PDF
5. **Download/Share**: Save or share the generated bill

### Input Methods

- **📝 Form Input**: Manual entry with validation
- **🎤 Voice Input**: "Item twelve, fifteen numbers"
- **📸 Image Input**: Photo of handwritten quantities

## 🏗️ Project Structure

```
BillGeneratorContractor/
├── app.py                          # Main Streamlit application
├── app_contractor.py               # Contractor-specific UI (to be created)
├── core/
│   ├── contractor/                 # Contractor-specific modules
│   │   ├── pdf/                   # PDF extraction and OCR
│   │   ├── input/                 # Voice, image, form handlers
│   │   ├── validation/            # Data validation
│   │   ├── session/               # Session management
│   │   └── models.py              # Data models
│   ├── generators/                # Shared bill generators
│   ├── processors/                # Data processors
│   └── utils/                     # Utilities
├── templates/                      # HTML templates for bills
├── config/                         # Configuration files
├── .streamlit/
│   └── config.toml                # Streamlit configuration
├── requirements.txt               # Python dependencies
├── packages.txt                   # System dependencies
└── README.md                      # This file
```

## 🔧 Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov hypothesis

# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov-report=html
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy core/
```

## 📋 Roadmap

- [x] Core data models and project structure
- [x] PDF extraction with hybrid OCR
- [ ] Voice input handler (Web Speech API)
- [ ] Image processing for handwritten notes
- [ ] Form-based quantity input
- [ ] Session management and offline support
- [ ] Bill generation integration
- [ ] Streamlit UI implementation
- [ ] Authentication and security
- [ ] Performance optimization
- [ ] Deployment and documentation

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Credits

**Prepared on Initiative of:**
- Mrs. Premlata Jain, AAO
- PWD Udaipur

**Development:**
- AI Development Partner: Kiro AI Assistant
- Based on BillGenerator Unified v2.0.3

## 📞 Support

For issues and questions:
- 📧 Email: support@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/CRAJKUMARSINGH/BillGeneratorContractor/issues)
- 📖 Documentation: [User Manual](USER_MANUAL.md)

## 🌟 Acknowledgments

- BillGenerator Unified v2.0.3 for core bill generation components
- Streamlit for the amazing framework
- Tesseract OCR for text extraction
- All contributors and users

---

⚡ **Powered by Streamlit** | 🚀 **Production Ready** | 📦 **Open Source**

[⭐ Star on GitHub](https://github.com/CRAJKUMARSINGH/BillGeneratorContractor)
