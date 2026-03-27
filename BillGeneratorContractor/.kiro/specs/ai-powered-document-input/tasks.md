# Implementation Plan: AI-Powered Document Input

## Overview

This implementation plan breaks down the AI-powered document input feature into discrete coding tasks. The system will integrate with the existing Streamlit BillGenerator app as a new input mode, processing scanned work orders, handwritten bill quantities, and extra items pages using OCR and handwriting recognition.

The implementation follows a sequential approach: core infrastructure → document processing → data extraction → validation → UI integration → testing.

## Tasks

- [x] 1. Set up project infrastructure and dependencies
  - Install required packages: pytesseract, opencv-python, Pillow, google-cloud-vision (or azure-cognitiveservices-vision-computervision)
  - Update requirements.txt with new dependencies
  - Create core/processors/document/ directory structure
  - Create core/ui/document_mode.py for UI components
  - Set up .env variables for Cloud Vision API credentials
  - _Requirements: 4.1, 5.1_

- [ ] 2. Implement folder organization system
  - [x] 2.1 Create WorkOrderOrganizer class in core/utils/work_order_organizer.py
    - Implement create_work_order_folder() to create work_XX_DDMMYYYY folders
    - Implement get_next_work_order_id() to auto-increment work order numbers
    - Implement save_uploaded_file() with category prefixes
    - Implement list_work_orders() to retrieve existing work orders
    - _Requirements: 12.1, 12.2, 12.4_
  
  - [ ]* 2.2 Write property test for folder organization
    - **Property 22: Original File Persistence**
    - **Validates: Requirements 12.1, 12.2, 12.4**
    - Test that uploaded files are stored with metadata and associations

- [ ] 3. Implement image preprocessing pipeline
  - [x] 3.1 Create ImagePreprocessor class in core/processors/document/image_preprocessor.py
    - Implement preprocess() for full pipeline
    - Implement correct_rotation() using Hough line transform
    - Implement enhance_contrast() with adaptive thresholding
    - Implement remove_noise() with morphological operations
    - Implement binarize() for optimal OCR
    - _Requirements: 11.1, 11.2_
  
  - [ ]* 3.2 Write property tests for image preprocessing
    - **Property 17: Rotation Correction**
    - **Validates: Requirements 11.1**
    - **Property 18: Image Enhancement Application**
    - **Validates: Requirements 11.2**

- [ ] 4. Implement OCR engine for printed text
  - [x] 4.1 Create OCREngine class in core/processors/document/ocr_engine.py
    - Initialize Tesseract with English and Hindi language support
    - Implement extract_text() to get all text with bounding boxes
    - Implement extract_structured_data() for template-based extraction
    - Implement get_confidence_scores() for field-level confidence
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ]* 4.2 Write property tests for OCR engine
    - **Property 1: File Format Acceptance**
    - **Validates: Requirements 1.1, 1.2, 2.1, 3.1**
    - **Property 6: Work Order Field Completeness**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
    - **Property 7: Confidence Score Provision**
    - **Validates: Requirements 4.5, 5.5**

- [x] 5. Checkpoint - Verify OCR functionality
  - Test OCR engine with sample work order from INPUT/work_order_samples/work_01_27022026/
  - Ensure all tests pass, ask the user if questions arise

- [ ] 6. Implement handwriting recognition engine
  - [x] 6.1 Create HandwritingRecognizer class in core/processors/document/hwr_engine.py
    - Initialize Google Cloud Vision API client (or Azure as fallback)
    - Implement recognize_text() for general handwritten text
    - Implement recognize_numbers() optimized for numerical values
    - Implement recognize_item_quantity_pairs() with spatial analysis
    - Handle API errors with retry logic and exponential backoff
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [ ]* 6.2 Write property tests for handwriting recognition
    - **Property 8: Handwriting Recognition Extraction**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**
    - **Property 19: Mixed Content Processing**
    - **Validates: Requirements 11.3**

- [ ] 7. Implement data extraction and parsing
  - [x] 7.1 Create DataExtractor class in core/processors/document/data_extractor.py
    - Implement extract_work_order_items() to parse OCR output into structured items
    - Implement extract_bill_quantities() to parse handwritten quantities
    - Implement extract_extra_items() to parse handwritten extra items
    - Implement apply_extraction_rules() with regex patterns for item numbers
    - Use spatial analysis to associate descriptions with item numbers
    - _Requirements: 2.2, 2.4, 3.2, 3.4, 3.5_
  
  - [ ]* 7.2 Write property tests for data extraction
    - **Property 3: Item-Quantity Mapping**
    - **Validates: Requirements 2.2, 2.4**
    - **Property 5: Extra Items Field Extraction**
    - **Validates: Requirements 3.2, 3.4, 3.5**
    - **Property 20: Relevant Field Extraction**
    - **Validates: Requirements 11.4**

- [ ] 8. Implement data validation
  - [x] 8.1 Create DataValidator class in core/processors/document/data_validator.py
    - Implement validate_work_order() for completeness checks
    - Implement validate_bill_quantities() to verify item references
    - Implement validate_extra_items() for required fields
    - Implement check_confidence_thresholds() to flag low-confidence fields
    - Generate specific error messages for each validation failure
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  
  - [ ]* 8.2 Write property tests for data validation
    - **Property 11: Item Number Validation**
    - **Validates: Requirements 7.1**
    - **Property 12: Positive Numerical Validation**
    - **Validates: Requirements 7.2, 7.3, 7.4**
    - **Property 9: Low Confidence Flagging**
    - **Validates: Requirements 6.1, 6.3**

- [ ] 9. Implement data transformation and mapping
  - [x] 9.1 Create DataMapper class in core/processors/document/data_mapper.py
    - Implement map_to_bill_format() to transform all extracted data
    - Implement create_excel_compatible_structure() matching Excel processor output
    - Implement merge_work_order_and_quantities() to combine data
    - Set quantity to 0 for work order items not in bill quantities
    - Append extra items to the end of the item list
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 2.5_
  
  - [ ]* 9.2 Write property tests for data mapping
    - **Property 13: Bill Generator Format Compatibility**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4**
    - **Property 4: Missing Item Default Quantity**
    - **Validates: Requirements 2.5**

- [ ] 10. Checkpoint - Verify data processing pipeline
  - Test complete pipeline: preprocessing → OCR/HWR → extraction → validation → mapping
  - Ensure all tests pass, ask the user if questions arise

- [ ] 11. Implement document processor orchestrator
  - [x] 11.1 Create DocumentProcessor class in core/processors/document/document_processor.py
    - Initialize with OCREngine, HandwritingRecognizer, ImagePreprocessor
    - Implement process_work_order() for multi-page work order processing
    - Implement process_bill_quantities() with item validation
    - Implement process_extra_items() for handwritten extra items
    - Implement get_processing_status() for progress tracking
    - Handle multi-page documents by processing pages sequentially
    - Continue processing on partial failures with error logging
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 6.4, 6.5_
  
  - [ ]* 11.2 Write property tests for document processor
    - **Property 15: Multi-Page Sequential Processing**
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.4**
    - **Property 16: Page Failure Isolation**
    - **Validates: Requirements 10.5**
    - **Property 10: Partial Processing Continuation**
    - **Validates: Requirements 6.4, 6.5**

- [ ] 12. Implement error handling and recovery
  - [ ] 12.1 Create error handling utilities in core/processors/document/error_handler.py
    - Define error categories (file upload, image quality, OCR/HWR, validation, pipeline, integration)
    - Implement graceful degradation for OCR/HWR failures
    - Implement retry logic with exponential backoff for API failures
    - Implement error logging with context (document, page, field)
    - Generate user-friendly error messages with actionable guidance
    - _Requirements: 1.3, 1.4, 6.1, 6.2, 6.3, 11.5_
  
  - [ ]* 12.2 Write property tests for error handling
    - **Property 2: Invalid File Rejection**
    - **Validates: Requirements 1.3, 1.4**
    - **Property 21: Error Logging and Recovery**
    - **Validates: Requirements 11.5**

- [ ] 13. Create data models and structures
  - [x] 13.1 Create data models in core/processors/document/models.py
    - Define WorkOrderItem, WorkOrderData dataclasses
    - Define ItemQuantityPair, BillQuantitiesData dataclasses
    - Define ExtraItem, ExtraItemsData dataclasses
    - Define BillItem, BillGeneratorInput dataclasses
    - Define DocumentMetadata, ExtractionMetadata, ProcessingStatus dataclasses
    - Define ValidationResult, OCRResult, HWRResult, BoundingBox dataclasses
    - _Requirements: All requirements (data structures)_

- [ ] 14. Implement metadata storage
  - [ ] 14.1 Create metadata storage in core/processors/document/metadata_store.py
    - Create SQLite database schema for work_order_sessions table
    - Create uploaded_documents table with foreign key relationships
    - Create extraction_results table for field-level tracking
    - Create processing_logs table for audit trail
    - Implement methods to store and retrieve metadata
    - Track manual corrections with timestamps
    - _Requirements: 12.1, 12.2, 12.4, 9.5_
  
  - [ ]* 14.2 Write unit tests for metadata storage
    - Test database creation and schema
    - Test CRUD operations for all tables
    - Test foreign key relationships

- [ ] 15. Checkpoint - Verify backend components
  - Test all backend components with sample data
  - Ensure all tests pass, ask the user if questions arise

- [ ] 16. Implement document upload UI
  - [x] 16.1 Create DocumentUploadUI class in core/ui/document_mode.py
    - Implement show_document_mode() as main entry point
    - Implement create_work_order_session() to initialize new session
    - Implement prompt_work_order_upload() for work order file upload
    - Implement prompt_bill_quantities_upload() for bill quantities upload
    - Implement prompt_extra_items_upload() with conditional prompt
    - Add progress indicators during processing
    - _Requirements: 1.1, 1.2, 1.5, 2.1, 3.1_
  
  - [ ]* 16.2 Write integration tests for upload UI
    - Test sequential upload workflow
    - Test file validation and error messages
    - Test progress indicators

- [ ] 17. Implement extraction results display UI
  - [ ] 17.1 Add extraction results display to DocumentUploadUI
    - Implement display_extraction_results() to show extracted data
    - Display confidence scores for each field
    - Highlight low-confidence fields (< 80%) in yellow/orange
    - Show original document thumbnails alongside extracted data
    - Display side-by-side comparison of original image and extracted text
    - _Requirements: 9.1, 9.2, 6.1_
  
  - [ ]* 17.2 Write UI tests for extraction display
    - Test confidence score visualization
    - Test low-confidence field highlighting
    - Test thumbnail display

- [ ] 18. Implement manual correction UI
  - [ ] 18.1 Add manual correction interface to DocumentUploadUI
    - Implement allow_manual_corrections() for inline editing
    - Enable editing for all extracted fields
    - Show original extracted value alongside correction field
    - Track which fields were manually corrected
    - Update structured data with corrected values
    - Retain original values for audit purposes
    - _Requirements: 9.3, 9.4, 9.5_
  
  - [ ]* 18.2 Write property test for manual corrections
    - **Property 14: Manual Correction Application**
    - **Validates: Requirements 9.4, 9.5**

- [ ] 19. Integrate document mode into main app
  - [x] 19.1 Add document mode to app.py
    - Add "📄 Document Upload" to modes list in sidebar
    - Import and call show_document_mode() when selected
    - Ensure consistent styling with existing modes
    - Add feature flag in config for document upload mode
    - _Requirements: All requirements (integration)_
  
  - [ ]* 19.2 Write integration tests for app mode
    - Test mode selection and switching
    - Test integration with existing bill generator
    - Test end-to-end workflow

- [ ] 20. Implement document viewing functionality
  - [ ] 20.1 Add document viewing to UI
    - Implement view_original_documents() to display stored files
    - Show document metadata (upload timestamp, file name, file size)
    - Allow users to download original documents
    - Associate documents with bill records
    - _Requirements: 12.3, 12.4, 12.5_

- [ ] 21. Add configuration and environment setup
  - [ ] 21.1 Update configuration files
    - Add document_upload feature flag to config/v01.json
    - Add OCR/HWR configuration options (language, confidence threshold)
    - Add preprocessing configuration (rotation detection, enhancement)
    - Update .env.example with Cloud Vision API credentials
    - Create setup documentation for API credentials
    - _Requirements: All requirements (configuration)_

- [ ] 22. Final checkpoint and integration testing
  - Test complete end-to-end workflow with real sample data
  - Test with work_01_27022026 sample files
  - Verify integration with existing bill generator
  - Test error handling with various edge cases
  - Ensure all tests pass, ask the user if questions arise

- [ ] 23. Create user documentation
  - [ ] 23.1 Update user manual with document upload instructions
    - Add section on document upload mode to USER_MANUAL.md
    - Add section to USER_MANUAL_HINDI.md
    - Include screenshots of upload workflow
    - Document supported file formats and size limits
    - Explain confidence scores and manual correction process
    - Add troubleshooting section for common issues
    - _Requirements: All requirements (documentation)_

## Notes

- Tasks marked with `*` are optional property-based tests and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The implementation uses Python and integrates with the existing Streamlit app
- Sample data in INPUT/work_order_samples/work_01_27022026/ should be used for testing
- Google Cloud Vision API is the primary choice for handwriting recognition (Azure as fallback)
- All extracted data must be compatible with the existing Bill Generator format
