# ANTIGRAVITY IMAGE & TEXT SAMPLES

Sample input files for testing the OCR/text-to-Excel pipeline.
These are derived from the 3 canonical test Excel files.

## Files

| File | Source | Has Extra Items |
|------|--------|-----------------|
| 0511Wextra_ocr_scan.txt | 0511Wextra.xlsx | YES (5 extra items) |
| FirstFINALnoExtra_ocr_scan.txt | FirstFINALnoExtra.xlsx | NO |
| FirstFINALvidExtra_ocr_scan.txt | FirstFINALvidExtra.xlsx | YES (5 extra items) |
| sample_handwritten_bill.txt | Synthetic | YES |
| sample_measurement_book_page.txt | Synthetic | NO |

## How to Use

Feed any of these .txt files to the OCR pipeline:
  python -c "from ingestion.ocr_extractor import extract_table_from_image; print(extract_table_from_image('ANTIGRAVITY_IMAGE_TEXT_SAMPLES/0511Wextra_ocr_scan.txt'))"

Or use the backend API:
  POST /bills/upload-image  (multipart form, field: file)

## Expected Output
Each file should produce a 4-sheet Excel:
  Title | Work Order | Bill Quantity | Extra Items
