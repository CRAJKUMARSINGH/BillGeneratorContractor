# Implementation Plan: Contractor-Friendly Bill Generator

## Overview

This implementation plan breaks down the Contractor-Friendly Bill Generator into discrete, testable coding tasks. The system extends BillGenerator Unified v2.0.3 to serve contractors with a mobile-first Streamlit application that processes scanned PDF work orders and generates bills through simplified interfaces.

The implementation follows a bottom-up approach: core data models and utilities first, then PDF extraction and input handlers, followed by validation and session management, and finally the Streamlit UI integration.

## Tasks

- [ ] 1. Set up project structure and core data models
  - Create `core/contractor/` directory structure with subdirectories: `pdf/`, `input/`, `validation/`, `session/`
  - Implement data models in `core/contractor/models.py`: WorkOrderItem, WorkOrderData, QuantityInput, BillData, BillLineItem, SessionData, ContractorInfo, OCRResult, BoundingBox, ValidationError, ValidationResult
  - Add type hints and dataclass decorators for all models
  - Implement helper methods: `WorkOrderItem.line_total()`, `WorkOrderData.get_item()`, `WorkOrderData.total_work_order_value()`, `BillData.calculate_totals()`, `SessionData.is_complete()`, `ValidationResult.has_errors()`, `ValidationResult.get_error_summary()`
  - Create `requirements_contractor.txt` with dependencies: pdfplumber, pdf2image, Pillow, pytesseract, opencv-python, streamlit
  - _Requirements: 17.1, 17.5_

- [ ]* 1.1 Write property tests for data models
  - **Property 1: Round-trip bill calculation consistency**
  - **Validates: Requirements 21.1, 21.2, 21.3**
  - Test that `BillLineItem.amount` equals `executed_quantity * rate` for all valid inputs
  - Test that `BillData.total_amount` equals sum of line items plus GST
  - Test precision preservation to 2 decimal places

- [ ] 2. Implement PDF extraction and OCR processing
  - [ ] 2.1 Create OCRProcessor class in `core/contractor/pdf/ocr_processor.py`
    - Implement `__init__()` with language pack initialization (English and Hindi)
    - Implement `preprocess_image()`: grayscale conversion, Gaussian blur, adaptive thresholding, skew detection using Hough transform, rotation correction, bilateral filtering, DPI normalization
    - Implement `extract_text()` using pytesseract with confidence scores
    - Implement `parse_work_order()` with regex patterns for item number, description, quantity, unit, and rate
    - _Requirements: 2.1, 2.2, 2.5_

  - [ ]* 2.2 Write unit tests for OCRProcessor
    - Test image preprocessing pipeline with sample images
    - Test text extraction with known test images
    - Test work order parsing with various formats
    - _Requirements: 2.1, 2.5_

  - [ ] 2.3 Create PDFExtractor class in `core/contractor/pdf/pdf_extractor.py`
    - Implement `extract_work_order()` main entry point
    - Implement `_detect_pdf_type()` to distinguish structured vs scanned PDFs
    - Implement `_extract_table()` using pdfplumber for structured PDFs
    - Implement `_extract_ocr()` using OCRProcessor for scanned images
    - Add confidence scoring logic: 0.95 for table extraction, OCR confidence for scanned
    - Add flagging for items with confidence < 0.8
    - Handle file size validation (max 10MB)
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4_

  - [ ]* 2.4 Write property tests for PDFExtractor
    - **Property 2: Extraction completeness**
    - **Validates: Requirements 2.1, 2.6**
    - Test that all items from structured PDFs are extracted
    - Test that item order is preserved from original work order
    - Test that extraction returns valid WorkOrderData for all supported formats

- [ ] 3. Checkpoint - Verify PDF extraction works with sample files
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Implement input handlers for quantity entry
  - [ ] 4.1 Create VoiceInputHandler class in `core/contractor/input/voice_handler.py`
    - Implement `__init__()` with language code initialization
    - Implement `start_listening()` to interface with Web Speech API (JavaScript bridge)
    - Implement `parse_command()` with pattern matching for English and Hindi voice commands
    - Support patterns: "item <number>, <quantity> <unit>", "item number <number>, quantity <quantity>", Hindi equivalents
    - Implement `get_confidence()` to return recognition confidence
    - Add normalization: lowercase, punctuation removal, whitespace trimming
    - _Requirements: 5.1, 5.2, 5.3, 5.6_

  - [ ]* 4.2 Write unit tests for VoiceInputHandler
    - Test command parsing with various patterns
    - Test Hindi and English language support
    - Test ambiguous input handling
    - _Requirements: 5.3, 5.6_

  - [ ] 4.3 Create ImageHandler class in `core/contractor/input/image_handler.py`
    - Implement `__init__()` with Tesseract handwriting configuration
    - Implement `capture_image()` to interface with device camera (Streamlit file_uploader)
    - Implement `extract_quantities()`: preprocess image, apply OCR with handwriting model, parse item-quantity pairs using regex patterns
    - Support patterns: "<item_no>: <quantity>", "<item_no> - <quantity>", "<quantity> for <item_no>"
    - Implement confidence calculation based on OCR confidence, item match, and format validity
    - Implement `resolve_conflicts()` for duplicate entries from multiple photos
    - Flag items with confidence < 0.7
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

  - [ ]* 4.4 Write unit tests for ImageHandler
    - Test handwriting recognition with sample images
    - Test quantity extraction patterns
    - Test conflict resolution logic
    - _Requirements: 6.3, 6.4, 6.7_

  - [ ] 4.5 Create FormHandler class in `core/contractor/input/form_handler.py`
    - Implement `__init__()` with work order data
    - Implement `render_form()` using Streamlit components: display items in table, create number_input for each item, show running totals
    - Implement `validate_quantity()`: check non-negative, validate precision for unit type, warn if > 110% of work order quantity
    - Implement `calculate_totals()`: compute line totals and grand total
    - Implement `auto_save()` to save form state every 30 seconds using Streamlit session state
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

  - [ ]* 4.6 Write property tests for FormHandler
    - **Property 3: Total calculation correctness**
    - **Validates: Requirements 4.8, 7.5, 7.6**
    - Test that calculated totals match manual calculation for all quantity combinations
    - Test that line totals equal quantity * rate

- [ ] 5. Implement validation and session management
  - [ ] 5.1 Create ContractorValidator class in `core/contractor/validation/contractor_validator.py`
    - Implement `validate_work_order()`: check required fields, verify unique item numbers, validate positive rates, check valid units
    - Implement `validate_quantities()`: ensure all items have quantities, check unit precision, verify total > 0, prevent negative values
    - Implement `validate_bill_data()`: final validation before generation
    - Return ValidationResult with detailed errors and warnings
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7_

  - [ ]* 5.2 Write unit tests for ContractorValidator
    - Test work order validation with invalid data
    - Test quantity validation with edge cases
    - Test error message generation
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

  - [ ] 5.3 Create SessionManager class in `core/contractor/session/session_manager.py`
    - Implement `__init__()` with Streamlit session state initialization
    - Implement `save_work_order()`: save to session_state and serialize to localStorage (JavaScript bridge)
    - Implement `save_quantities()`: save to session_state and localStorage
    - Implement `restore_session()`: load from localStorage on app start
    - Implement `archive_session()`: move completed session to history with 90-day retention
    - Implement `clear_session()`: reset current session
    - Implement `get_history()`: retrieve historical sessions with filtering
    - Add auto-save trigger every 30 seconds
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 19.1, 19.2_

  - [ ]* 5.4 Write property tests for SessionManager
    - **Property 4: Session persistence consistency**
    - **Validates: Requirements 13.1, 13.2, 13.3, 21.1**
    - Test that saved and restored sessions are equivalent
    - Test that auto-save preserves all data

- [ ] 6. Checkpoint - Verify core components work independently
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement bill generation integration
  - [ ] 7.1 Create ContractorBillGenerator class in `core/contractor/bill_generator.py`
    - Implement `__init__()` with references to shared generators: HTMLGenerator, FixedPDFGenerator, TemplateManager
    - Implement `_transform_to_unified_format()`: convert WorkOrderData and quantities to BillGenerator Unified format
    - Implement `generate_bill()`: transform data, invoke HTMLGenerator, invoke FixedPDFGenerator, return PDF bytes
    - Ensure compatibility with existing templates from `templates/` directory
    - Apply contractor-specific template if available, otherwise use default
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 17.1, 17.2, 17.3, 17.4_

  - [ ]* 7.2 Write integration tests for ContractorBillGenerator
    - Test data transformation to unified format
    - Test PDF generation with sample work orders
    - Test compatibility with BillGenerator Unified templates
    - _Requirements: 17.1, 17.2, 17.3, 17.4_

  - [ ]* 7.3 Write property tests for bill generation
    - **Property 5: Bill format compatibility**
    - **Validates: Requirements 17.3, 20.1, 20.2, 20.3, 20.4, 20.5**
    - Test that generated PDFs match BillGenerator Unified format
    - Test that PDF quality meets standards (300 DPI, proper margins, embedded fonts)
    - Test that calculations match BillGenerator Unified within 0.01 currency units

- [ ] 8. Implement Streamlit UI application
  - [ ] 8.1 Create main application file `app_contractor.py`
    - Set up Streamlit page configuration: mobile-responsive layout, page title, favicon
    - Initialize SessionManager and restore previous session if available
    - Create navigation: "Upload Work Order", "Enter Quantities", "Generate Bill", "History"
    - Implement mobile-first CSS styling with minimum 14px font size, 44x44px tap targets
    - Add language selector (Hindi/English) with persistence
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 11.1, 11.2, 11.3_

  - [ ] 8.2 Implement "Upload Work Order" page
    - Create file uploader with support for PDF, JPEG, PNG, HEIC up to 10MB
    - Add drag-and-drop support for desktop
    - Add camera capture button for mobile
    - Display upload progress bar
    - Implement retry logic (up to 3 attempts)
    - Show confirmation message on successful upload
    - Invoke PDFExtractor to process uploaded file
    - Display extraction progress indicator
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2.2, 15.1, 15.2, 15.3_

  - [ ] 8.3 Implement "Verification Interface" page
    - Display extracted work order data in editable table using st.data_editor
    - Show confidence scores for each field
    - Highlight low-confidence items (< 0.8) and sort to top
    - Enable inline editing for all fields
    - Add "Add Item" and "Delete Item" buttons
    - Show extraction method (table/OCR) and timestamp
    - Add "Proceed to Quantities" button (enabled after verification)
    - Invoke SessionManager to auto-save verified work order
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 2.3, 2.4_

  - [ ] 8.4 Implement "Enter Quantities" page with multiple input methods
    - Create tab interface: "Form Input", "Voice Input", "Image Input"
    - Tab 1 - Form Input: use FormHandler to render quantity form, display running totals, show validation errors inline
    - Tab 2 - Voice Input: add microphone button, display transcript, use VoiceInputHandler to parse commands, show confirmation dialog for ambiguous input, highlight populated fields
    - Tab 3 - Image Input: add camera capture button, use ImageHandler to extract quantities, display extracted data with confidence scores, flag low-confidence items (< 0.7), support multiple photos
    - Add "Generate Bill" button (enabled when quantities are valid)
    - Invoke SessionManager to auto-save quantities every 30 seconds
    - _Requirements: 4.1-4.8, 5.1-5.7, 6.1-6.7, 13.1, 13.2_

  - [ ] 8.5 Implement "Generate Bill" page
    - Invoke ContractorValidator for final validation
    - Display validation errors if any, with focus on first error
    - Show bill preview with all line items and totals
    - Add contractor information form: name, mobile, email, address, GST number
    - Add "Generate PDF" button
    - Display progress indicator during generation
    - Show generated PDF preview using st.download_button
    - Add "Download" button to save PDF to device
    - Add "Share" button for mobile devices (opens native share dialog)
    - Generate unique filename with work order number and timestamp
    - Invoke SessionManager to archive completed session
    - _Requirements: 7.1-7.8, 8.1-8.7, 12.5, 12.6, 15.4_

  - [ ] 8.6 Implement "History" page
    - Use SessionManager to retrieve historical sessions (90 days)
    - Display bills in table sorted by date (newest first)
    - Add filters: work order number, date range, status
    - Show bill status (draft, submitted, paid)
    - Add "View" button to display bill details
    - Add "Download" button to re-download PDF
    - Add "Notes" field for contractors to add comments
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7_

  - [ ]* 8.7 Write integration tests for Streamlit UI
    - Test navigation flow from upload to bill generation
    - Test session restoration on app reload
    - Test mobile responsiveness at various screen sizes
    - _Requirements: 9.1, 9.5, 13.3_

- [ ] 9. Implement offline capability and progressive enhancement
  - [ ] 9.1 Add connection status indicator to UI
    - Create JavaScript component to detect online/offline status
    - Display status badge in header
    - Update status in real-time
    - _Requirements: 10.4_

  - [ ] 9.2 Implement local caching for offline work
    - Extend SessionManager to cache up to 10 work orders in localStorage
    - Allow quantity input and save locally when offline
    - Queue bill generation requests when offline
    - Implement sync logic when connection is restored
    - Display sync status and progress
    - Prompt user when cache is full (sync or clear old data)
    - _Requirements: 10.1, 10.2, 10.3, 10.5, 10.6, 10.7_

  - [ ]* 9.3 Write tests for offline functionality
    - Test local caching and sync logic
    - Test queue management for bill generation
    - Test cache size limits
    - _Requirements: 10.1, 10.2, 10.3, 10.6_

- [ ] 10. Implement accessibility and help features
  - [ ] 10.1 Add accessibility enhancements to UI
    - Add alt text for all images and icons
    - Implement keyboard navigation for all interactive elements
    - Ensure color contrast ratio ≥ 4.5:1 for all text
    - Add focus indicators for all interactive elements
    - Use semantic HTML and ARIA labels for dynamic content
    - Test browser zoom up to 200%
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7_

  - [ ] 10.2 Create help system
    - Add tooltips for all input fields using st.help()
    - Create first-time user tutorial with step-by-step guide
    - Add example images showing proper PDF upload
    - Create video demonstrations for voice and image input (embed links)
    - Implement contextual help messages for common errors
    - Create FAQ section with common issues and solutions
    - Support Hindi and English help content
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7_

- [ ] 11. Implement authentication and security
  - [ ] 11.1 Create authentication system
    - Implement mobile number-based OTP authentication using Streamlit session state
    - Add login page with mobile number input
    - Integrate with SMS OTP service (placeholder for actual service)
    - Implement session timeout after 30 minutes of inactivity
    - Require re-authentication for bill generation
    - _Requirements: 14.1, 14.2, 14.3, 14.6, 14.7_

  - [ ] 11.2 Add security measures
    - Implement HTTPS for all communications (deployment configuration)
    - Add file upload encryption during transmission
    - Encrypt stored work order data in localStorage
    - Add input sanitization for all user inputs
    - Implement rate limiting for API calls
    - _Requirements: 14.4, 14.5_

  - [ ]* 11.3 Write security tests
    - Test authentication flow
    - Test session timeout
    - Test input sanitization
    - _Requirements: 14.1, 14.2, 14.6_

- [ ] 12. Checkpoint - End-to-end testing and optimization
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Performance optimization and final integration
  - [ ] 13.1 Optimize PDF extraction performance
    - Add image compression before OCR processing
    - Implement parallel processing for multi-page PDFs
    - Add caching for repeated extractions
    - Ensure 5MB PDF processes within 30 seconds
    - _Requirements: 15.3, 15.6_

  - [ ] 13.2 Optimize bill generation performance
    - Ensure bills with 50 items generate within 10 seconds
    - Add progress indicators for long operations (> 5 seconds)
    - Optimize template rendering
    - _Requirements: 15.4, 15.7_

  - [ ] 13.3 Add performance monitoring
    - Implement timing logs for key operations
    - Add performance metrics to session data
    - Create performance dashboard for monitoring
    - _Requirements: 15.1, 15.2, 15.5_

  - [ ]* 13.4 Write performance tests
    - Test PDF extraction with various file sizes
    - Test bill generation with various item counts
    - Test concurrent usage simulation
    - _Requirements: 15.3, 15.4, 15.5_

- [ ] 14. Create deployment configuration and documentation
  - [ ] 14.1 Create deployment files
    - Create `Dockerfile` for containerized deployment
    - Create `docker-compose.yml` for local development
    - Create deployment script for cloud platforms (AWS/GCP/Azure)
    - Configure environment variables for production
    - _Requirements: 9.6, 9.7_

  - [ ] 14.2 Create user documentation
    - Write README.md with setup instructions
    - Create user guide with screenshots
    - Document all input methods with examples
    - Create troubleshooting guide
    - Document API endpoints if applicable
    - _Requirements: 18.1, 18.2, 18.3, 18.4_

  - [ ] 14.3 Create developer documentation
    - Document code architecture and component interactions
    - Create API documentation for all classes and methods
    - Document integration points with BillGenerator Unified
    - Create contribution guidelines
    - _Requirements: 17.1, 17.2, 17.6, 17.7_

- [ ] 15. Final checkpoint - Complete system validation
  - Ensure all tests pass, ask the user if questions arise.
  - Verify all requirements are met
  - Validate integration with BillGenerator Unified
  - Test on multiple mobile devices and browsers

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties from the design
- Unit tests validate specific examples and edge cases
- The implementation reuses core components from BillGenerator Unified v2.0.3 (HTMLGenerator, FixedPDFGenerator, TemplateManager)
- All code should follow Python best practices with type hints and comprehensive docstrings
- Mobile-first design is critical - test on actual mobile devices throughout development
