# Requirements Document

## Introduction

Before generating the final PDF output, users should be able to preview the rendered HTML content for each input file (Excel uploads or OCR-scanned images) directly in the browser. The preview is interactive: users can edit cell values, text fields, and table data inline within the rendered HTML view. Once satisfied, they confirm and the system proceeds to generate the final PDF using the edited content.

This feature inserts a "Preview & Edit" step between the existing data-editing step and the final PDF generation step in the bill workflow.

## Glossary

- **Preview_Panel**: The browser-based UI component that renders the HTML preview for a given document type.
- **Preview_Session**: A server-side or client-side record holding the rendered HTML and any user edits for a specific input file before PDF generation.
- **Document_Type**: One of the supported bill document types (first_page, deviation_statement, extra_items, note_sheet, certificate_ii, certificate_iii, last_page).
- **HTML_Renderer**: The `EnterpriseHTMLRenderer` engine component that renders Jinja2 templates into HTML.
- **Input_File**: An uploaded Excel file or OCR-scanned image that has been parsed into bill data.
- **Editable_Field**: A cell, text node, or table row within the preview that the user can modify inline.
- **Preview_API**: The backend endpoint that accepts bill data and returns rendered HTML for a given Document_Type.
- **Confirmed_Payload**: The final bill data (original + user edits) submitted to the PDF generation pipeline.
- **Bill_Store**: The Zustand client-side state store managing bill header, items, and view mode.

---

## Requirements

### Requirement 1: Preview Rendering Endpoint

**User Story:** As a developer, I want a backend endpoint that renders HTML previews for each document type, so that the frontend can display them before PDF generation.

#### Acceptance Criteria

1. WHEN a POST request is sent to `/bills/preview` with a valid bill data payload and a `document_type` field, THE Preview_API SHALL return the rendered HTML string for that Document_Type.
2. WHEN the `document_type` field in the request is not one of the supported Document_Type values, THE Preview_API SHALL return an HTTP 422 response with a descriptive error message.
3. WHEN the bill data payload fails validation, THE Preview_API SHALL return an HTTP 422 response with a descriptive error message.
4. THE Preview_API SHALL render HTML using the same HTML_Renderer and Jinja2 templates used by the PDF generation pipeline, ensuring visual consistency.
5. THE Preview_API SHALL complete rendering and return a response within 3000ms for any single Document_Type.

---

### Requirement 2: Preview Step in the Workflow

**User Story:** As a user, I want a preview step inserted between the bill editor and PDF generation, so that I can review the rendered output before committing to PDF.

#### Acceptance Criteria

1. WHEN the user clicks "Generate Documents" in the bill editor, THE Bill_Store SHALL transition the view mode to `preview` instead of directly initiating PDF generation.
2. WHILE the view mode is `preview`, THE Preview_Panel SHALL display a rendered HTML preview for each Document_Type in a tabbed or paginated interface.
3. WHEN the user confirms the preview by clicking a "Confirm & Generate PDF" button, THE system SHALL submit the Confirmed_Payload to the existing PDF generation pipeline.
4. WHEN the user clicks "Back to Editor" from the preview step, THE Bill_Store SHALL transition the view mode back to `edit` without discarding any edits.
5. THE Preview_Panel SHALL display a loading indicator while HTML previews are being fetched from the Preview_API.

---

### Requirement 3: Inline Editing in Preview

**User Story:** As a user, I want to edit text and table values directly within the HTML preview, so that I can make last-minute corrections without returning to the editor.

#### Acceptance Criteria

1. WHEN the Preview_Panel renders a document, THE Preview_Panel SHALL mark all user-editable fields (text cells, header fields, table rows) with the `contenteditable` attribute.
2. WHEN a user modifies an Editable_Field in the preview, THE Preview_Panel SHALL capture the change and store it in the local preview edit state.
3. WHEN the user confirms the preview, THE system SHALL merge the inline edits from the preview edit state into the Confirmed_Payload before submitting to PDF generation.
4. IF the user modifies a numeric Editable_Field with a non-numeric value, THEN THE Preview_Panel SHALL highlight the field with a visual error indicator and prevent confirmation until the value is corrected.
5. THE Preview_Panel SHALL display an "Unsaved preview edits" indicator when the preview edit state contains changes not yet confirmed.

---

### Requirement 4: Per-File Preview for Multiple Input Files

**User Story:** As a user, I want to preview the rendered output for each uploaded input file separately, so that I can review and edit each file's documents independently.

#### Acceptance Criteria

1. WHEN multiple Input_Files have been uploaded in a session, THE Preview_Panel SHALL display a file selector allowing the user to switch between per-file previews.
2. WHEN the user switches between Input_Files in the file selector, THE Preview_Panel SHALL load and display the preview for the selected Input_File without discarding edits made to other Input_Files.
3. THE Preview_Panel SHALL indicate which Input_Files have pending inline edits using a visual badge or marker on the file selector.
4. WHEN the user confirms the preview, THE system SHALL include the Confirmed_Payload for all Input_Files with their respective edits.

---

### Requirement 5: Preview Consistency with Final PDF

**User Story:** As a user, I want the browser preview to visually match the final PDF output, so that what I see is what I get.

#### Acceptance Criteria

1. THE Preview_API SHALL apply the same `pdf_ready` CSS optimizations to the preview HTML as are applied during PDF generation.
2. THE Preview_Panel SHALL render the HTML preview inside an `<iframe>` or sandboxed container to isolate template styles from the application shell.
3. WHEN the user edits an Editable_Field and the preview re-renders, THE Preview_Panel SHALL preserve the A4 page dimensions and layout defined in the Jinja2 templates.
4. THE Preview_Panel SHALL use the same template version (v1 or v2) selected by the user in the Generate Documents panel.

---

### Requirement 6: Error Handling in Preview

**User Story:** As a user, I want clear feedback when a preview fails to load, so that I can take corrective action.

#### Acceptance Criteria

1. IF the Preview_API returns an error for a Document_Type, THEN THE Preview_Panel SHALL display an inline error message for that document tab identifying the failure.
2. IF the Preview_API is unreachable or times out after 3000ms, THEN THE Preview_Panel SHALL display a retry button for the affected Document_Type.
3. WHEN the user clicks the retry button, THE Preview_Panel SHALL re-request the preview from the Preview_API for the failed Document_Type.
4. IF all Document_Type previews fail to load, THEN THE Preview_Panel SHALL offer the user the option to skip the preview step and proceed directly to PDF generation.
