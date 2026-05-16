# GENIUS PROMPT: Senior Principal Engineer + Strict Refactoring Guardian

## Goal
Deliver one clean, production-ready application that fully supports all three input modes with shared downstream pipeline (editable workflow → auto-calculation → preview → final print edit → PDF/HTML output).

### 1. Mandatory Core Rule: PRESERVE MODE 1 100%
*   The existing Excel workbook upload (work order + quantity together) must continue to work exactly as today with zero regression.
*   Add new code in parallel; use feature flags or clear route/module separation.

### 2. Supported Input Modes
1.  **Mode 1 (Strict)**: Full Excel workbook upload (WO + BQ sheets).
2.  **Mode 2 (Hybrid)**: Excel Work Order upload + Manual web entry for quantities.
3.  **Mode 3 (AI/OCR)**: Image/PDF scan ingestion or irregular Excel parsing via LLM/Heuristics.
4.  **Mode 4 (Previous Bill)**: Drafting a new bill by using a previous bill's cumulative data.

### 3. Key Robustness Features (Haphazard-Tolerant)
*   **Hierarchical Sorting**: Smart numeric-aware sorting (e.g., 1.2 < 1.10).
*   **Smart Merging**: Intelligent aggregation of duplicate item codes.
*   **Parent Synthesis**: Auto-generation of missing headers for orphaned sub-items.
*   **Hierarchical Pruning**: Removal of unused headers where all descendants are zero.
*   **PWD Compliance**: GST even-number rounding and professional report structures.

### 4. Technical Stack & Assets
*   **Backend**: FastAPI, Pandas, Openpyxl, Jinja2 (PDF/HTML templates).
*   **Frontend**: React, TypeScript, Tailwind CSS, Zustand (State).
*   **Design**: 2025 Premium Trends: Glassmorphism, Bento Grids, Neon Accents.

### 5. Organized Input Structure (Master Repository)
*   **INPUT/seed_tutorials/**: Clean, curated samples for training and onboarding.
*   **INPUT/recent_projects/**: Real-world, haphazard data from 125+ active projects.

### 6. Execution Roadmap
*   **Phase 0**: Audit full repo + Reorganize INPUT folders.
*   **Phase 1**: Unified Data Model + Robust Ingestion Layer (Excel + OCR).
*   **Phase 2**: Normalization & Merging logic for haphazard inputs.
*   **Phase 3**: Premium Frontend: Editable table + Auto-sorting + Conflict highlighting.
*   **Phase 4**: Shared Calculation & Output Pipeline (6 Statutory PDFs).
*   **Phase 5**: World-Standard Polish: Robotic Simulation + PWD Compliance.

### 7. Core Technical Differentiators
1.  **Robotic Filler**: Automated simulation of billing scenarios (`tests/robotic_filler.py`).
2.  **Parent Synthesis**: Structural auto-correction for haphazard inputs.
3.  **Advanced Ingestion**: Multi-modal section detection (WO vs BQ vs Extra).

---
*Status: Production Ready. World-Standard Features Implemented.*