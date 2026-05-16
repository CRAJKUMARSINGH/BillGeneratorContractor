# Unified Construction Billing Pipeline: Master Instruction Set
## Senior Principal Engineer + Strict Refactoring Guardian Mode

Project: [BillGeneratorContractor](https://github.com/CRAJKUMARSINGH/BillGeneratorContractor)

### 1. Goal
Deliver one clean, production-ready application supporting all four input modes feeding into a shared robust pipeline (Editable Table → Auto-Calculation → Preview → Final Export).

### 2. Mandatory Input Modes (Haphazard-Robust)
The system MUST correctly handle messy, non-sequentially arranged items. Item codes (e.g., 1.2.3c) are treated as unique primary keys.

*   **Mode 1 (Strict Excel)**: Full workbook upload (Work Order + Quantities). **Zero Regression Rule**: Existing workflows must remain 100% functional.
*   **Mode 2 (Hybrid)**: Work Order Excel upload only → Quantity/Rate entry in a rich web-based editable table.
*   **Mode 3 (AI-OCR)**: Image/PDF upload → OCR Extraction → Intelligent parsing of item codes → Confidence scoring.
*   **Mode 4 (Previous Bill)**: RA Bill upload (Excel/PDF/Image/Doc/Txt) → Extract previous quantities → Draft new bill by adding "This Bill" quantities.

### 3. Core Intelligence Requirements
*   **Item Code Normalization**: Standardize inconsistent codes (e.g., `1.2.3c`, `1-2-3c`, `1.2.3 C`) into a canonical key.
*   **Smart Merging**: Automatically sum quantities if the same item code appears multiple times across haphazard inputs.
*   **Hierarchical Sorting**: Sort items in proper PWD order (1.1, 1.2, 1.2.3c, 2.1) regardless of input sequence.
*   **Conflict Detection**: Flag quantity/rate conflicts or duplicate items with high visibility for user review.

### 4. Architecture & Technology Stack
*   **Backend**: FastAPI (Python)
*   **Frontend**: React + TypeScript + Tailwind CSS (Premium, responsive, glassmorphism UI).
*   **Logic**: 
    *   Unified internal data model (`UnifiedBillDocument`) with support for `previous_qty`, `this_bill_qty`, and `cumulative_qty`.
    *   Shared downstream calculation and rendering pipeline (PDF, HTML, DOCX).
    *   Background workers for heavy OCR/processing.
*   **Assets**: Reuse best components from `Bill-Contractor-Git4/` and templates from `BillGeneratorHistorical/`.

### 5. Organized Input Structure (Master Repository)
To manage the 125+ project samples and training data:
*   **INPUT/seed_tutorials/**: Clean, curated samples for training and onboarding.
    *   `excel/`, `images/`, `pdf/`, `previous_bills/`
*   **INPUT/recent_projects/**: Real-world, haphazard data from active projects.
    *   `work_orders/`, `previous_bills/`, `haphazard/` (Contains messy/non-sequential files).

### 6. Execution Roadmap
*   **Phase 0**: Audit full repo + Reorganize INPUT folders. Baseline test Mode 1.
*   **Phase 1**: Unified Data Model + Robust Ingestion Layer (Excel + OCR) handling haphazard inputs.
*   **Phase 2**: Mode 2, 3, and 4 (Previous Bill) with strong normalization & merging logic.
*   **Phase 3**: Premium Frontend: Editable table (Previous vs Current columns) + Auto-sorting + Conflict highlighting.
*   **Phase 4**: Shared Calculation & Output Pipeline (Correct final bill regardless of input messiness).
*   **Phase 5**: Comprehensive Regression Suite using haphazard test files.

### 6. Critical Non-Negotiable Rules
*   **PRESERVE MODE 1 100%**: Do not break the legacy Excel path.
*   **AESTHETICS MATTER**: Use rich, premium web design (Tailwind, modern typography, animations).
*   **DOCUMENTATION**: Reply with `=== PHASE X COMPLETE ===` after each phase and wait for `PROCEED`.

---
*Status: Phase 1-5 functionally implemented. Regression verified.*