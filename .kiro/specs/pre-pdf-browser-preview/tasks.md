# Implementation Plan: Pre-PDF Browser Preview

## Overview

Insert a "Preview & Edit" step between the bill editor and PDF generation. A new `/bills/preview` backend endpoint renders HTML synchronously using the existing `EnterpriseHTMLRenderer`. The frontend gains a `PreviewPanel` component that fetches all 7 document types in parallel, displays them in sandboxed iframe tabs, supports inline `contenteditable` editing, and submits the merged payload to the existing `/bills/generate` pipeline on confirm.

## Tasks

- [x] 1. Add `PreviewRequest` and `PreviewResponse` models to `backend/models.py`
  - Add `PreviewRequest(BaseModel)` with fields: `document_type: str`, `fileId: str`, `titleData: dict`, `billItems: list[BillItem]`, `extraItems: list[ExtraItem]`, `options: GenerateOptions`
  - Add `PreviewResponse(BaseModel)` with fields: `document_type: str`, `html: str`
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Implement `POST /bills/preview` route in `backend/routes/bills.py`
  - [x] 2.1 Implement the preview endpoint
    - Validate `document_type` against `DocumentType` enum; return 422 on failure
    - Build `template_data` the same way `BillService.process_generation` does (merge `titleData`, `billItems`, `options`)
    - Instantiate `EnterpriseHTMLRenderer` with `RenderConfig(pdf_ready=True, template_dir=..., output_dir=...)`
    - Call `renderer.render(doc_type, template_data)` without `output_filename` (no file write)
    - Return `PreviewResponse(document_type=..., html=result.html_content)` on success; raise HTTP 500 if `result.success` is False
    - No Redis, no job queue — synchronous and stateless
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ]* 2.2 Write property test for valid preview requests return non-empty HTML (P1)
    - **Property 1: Valid preview requests return non-empty HTML**
    - Use Hypothesis to generate random valid `document_type` values and bill data; assert 200 + non-empty HTML string
    - **Validates: Requirements 1.1**

  - [ ]* 2.3 Write property test for invalid inputs return 422 (P2)
    - **Property 2: Invalid inputs return 422**
    - Use Hypothesis to generate strings not in `DocumentType` enum and malformed payloads; assert HTTP 422
    - **Validates: Requirements 1.2, 1.3**

  - [ ]* 2.4 Write property test for preview HTML matches direct renderer output (P3)
    - **Property 3: Preview HTML matches direct renderer output**
    - Use Hypothesis to generate random bill data; compare endpoint HTML to direct `EnterpriseHTMLRenderer.render()` call with same data and `pdf_ready=True`
    - **Validates: Requirements 1.4, 5.1**

  - [ ]* 2.5 Write property test for response time under 3000ms (P4)
    - **Property 4: Preview response time is under 3000ms**
    - Use Hypothesis to generate random valid requests; assert elapsed time < 3000ms
    - **Validates: Requirements 1.5**

- [x] 3. Add HTML post-processor for `contenteditable` field annotation
  - Write a function (in `backend/routes/bills.py` or a new `backend/utils/preview_annotator.py`) that post-processes rendered HTML using BeautifulSoup
  - Add `contenteditable="true" data-field-id="..."` to header key-value `<td>` cells and bill item `<td>` cells
  - Header fields: `data-field-id` = the key string (e.g. `"Agreement No."`)
  - Bill item cells: `data-field-id` = `"item-{itemNo}-{field}"` format
  - Call this annotator inside the preview endpoint before returning HTML
  - _Requirements: 3.1, 5.3_

  - [ ]* 3.1 Write property test for contenteditable present in preview HTML (P9)
    - **Property 9: Editable fields carry `contenteditable` attribute**
    - Use Hypothesis to generate random valid `document_type`; assert returned HTML contains at least one element with `contenteditable="true"` and `data-field-id`
    - **Validates: Requirements 3.1**

- [x] 4. Checkpoint — Ensure all backend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Add `preview` API method to `frontend/src/lib/api.ts`
  - Add `PreviewRequest` and `PreviewResponse` TypeScript interfaces matching the backend models
  - Add `api.preview(req: PreviewRequest): Promise<PreviewResponse>` using the existing `request<T>` helper with `timeoutMs: 3000`
  - _Requirements: 1.1, 1.5_

- [x] 6. Create `frontend/src/components/PreviewPanel.tsx`
  - [x] 6.1 Implement tab bar and parallel fetch logic
    - On mount, fire 7 parallel `api.preview()` calls (one per `DocumentType` value) using `Promise.allSettled`
    - Read `header`, `billItems`, `parsedData`, and `templateVersion` from `useBillStore` to build each `PreviewRequest`
    - Track per-tab state: `'loading' | 'loaded' | 'error'`
    - Render a tab bar with one tab per document type; show loading spinner while fetches are in-flight
    - _Requirements: 2.2, 2.5, 5.4_

  - [x] 6.2 Implement iframe rendering and postMessage edit capture
    - Render each tab's HTML inside `<iframe srcDoc={html} sandbox="allow-scripts allow-same-origin">`
    - Inject a `<script>` into each iframe's HTML that listens for `input` events on `[contenteditable]` elements and posts `{ fieldId, value }` via `window.parent.postMessage`
    - In `PreviewPanel`, listen for `message` events on `window` and update local `previewEdits: Record<string, FieldEdit[]>` state
    - _Requirements: 3.1, 3.2_

  - [x] 6.3 Implement numeric validation and "Unsaved edits" indicator
    - For each edit event, check if the `data-field-id` maps to a numeric field; if the value cannot be parsed as a finite number, mark it as invalid
    - Disable the "Confirm & Generate PDF" button when any invalid edit exists; highlight the field red via a CSS class injected into the iframe
    - Show an "Unsaved preview edits" badge when `previewEdits` is non-empty
    - _Requirements: 3.4, 3.5_

  - [x] 6.4 Implement per-file selector for multiple input files
    - When `parsedData` contains multiple files (future multi-file support), render a file selector above the tab bar
    - Switching files loads that file's preview without discarding edits for other files (store edits keyed by `fileId`)
    - Show a visual badge on file selector entries that have pending edits
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 6.5 Implement "Confirm & Generate PDF" and "Back to Editor" actions
    - "Back to Editor": call `setViewMode('edit')` — no store mutation
    - "Confirm & Generate PDF": merge `previewEdits` into the generate payload (overwrite `titleData` keys and `billItems` fields by `fieldId`), call `api.generate()` with the merged payload for all files, then call `setViewMode('generating')`
    - _Requirements: 2.3, 2.4, 3.3, 4.4_

  - [x] 6.6 Implement error handling UI
    - Per-tab error: show inline error message and a "Retry" button that re-fetches that tab's preview
    - All-tabs failure: show "Skip preview" button that calls `setViewMode('generating')` and submits directly to `api.generate()` without edits
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ]* 6.7 Write property test for "Generate Documents" transitions to preview mode (P5)
    - **Property 5: "Generate Documents" transitions to preview mode**
    - Use fast-check to generate random store states; simulate button click; assert `viewMode === 'preview'` and `api.generate` was not called
    - **Validates: Requirements 2.1**

  - [ ]* 6.8 Write property test for 7 tabs rendered (P6)
    - **Property 6: Preview panel renders a tab for every document type**
    - Use fast-check to generate random store states; render `PreviewPanel` with mocked `api.preview`; assert exactly 7 tabs are present
    - **Validates: Requirements 2.2**

  - [ ]* 6.9 Write property test for confirm merges edits (P7)
    - **Property 7: Confirm merges edits and submits to generate pipeline**
    - Use fast-check to generate random edit states (including empty); confirm; assert `api.generate` called exactly once with payload incorporating all edits
    - **Validates: Requirements 2.3, 3.3**

  - [ ]* 6.10 Write property test for back to editor preserves store state (P8)
    - **Property 8: Back to editor preserves store state**
    - Use fast-check to generate random `header` + `billItems`; navigate back; assert `header` and `billItems` unchanged
    - **Validates: Requirements 2.4**

  - [ ]* 6.11 Write property test for inline edits captured in state (P10)
    - **Property 10: Inline edits are captured in preview edit state**
    - Use fast-check to generate random sequences of `contenteditable` change events; assert edit state contains an entry for each changed field with the latest value
    - **Validates: Requirements 3.2**

  - [ ]* 6.12 Write property test for non-numeric value blocks confirmation (P11)
    - **Property 11: Non-numeric value in numeric field blocks confirmation**
    - Use fast-check to generate non-numeric strings for numeric fields; assert confirm button is disabled
    - **Validates: Requirements 3.4**

  - [ ]* 6.13 Write property test for file switch preserves per-file edits (P12)
    - **Property 12: Switching files preserves per-file edits**
    - Use fast-check to generate random multi-file edit states; switch active file; assert other files' edit states are unchanged
    - **Validates: Requirements 4.2**

  - [ ]* 6.14 Write property test for confirm payload includes all files (P13)
    - **Property 13: Confirm payload includes all files' edits**
    - Use fast-check to generate random multi-file edit states; confirm; assert payload includes merged data for every file
    - **Validates: Requirements 4.4**

  - [ ]* 6.15 Write property test for template version propagated (P14)
    - **Property 14: Preview uses the selected template version**
    - Use fast-check to generate random `templateVersion` values; assert each `PreviewRequest` sent to `api.preview` includes `options.templateVersion` matching the store value
    - **Validates: Requirements 5.4**

- [ ] 7. Wire `PreviewPanel` into `App.tsx` and update `GeneratePanel.tsx`
  - Import `PreviewPanel` in `App.tsx`; add `{viewMode === 'preview' && <PreviewPanel />}` alongside existing view branches
  - Update the `<main>` className logic in `App.tsx` to include `viewMode === 'preview'` in the full-width branch
  - In `GeneratePanel.tsx`, change the "Generate All 6 Documents" button's `onClick` from `startGeneration` to `() => setViewMode('preview')`
  - _Requirements: 2.1, 2.2_

- [~] 8. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Property tests use Hypothesis (Python/backend) and fast-check (TypeScript/frontend)
- The preview endpoint is synchronous and stateless — no Redis or job queue involvement
- `contenteditable` annotation is done via post-processing to keep Jinja2 templates clean
