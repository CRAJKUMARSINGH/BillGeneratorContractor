# Requirements Document

## Introduction

This document specifies requirements for enhancing the existing Streamlit-based Bill Generator application with Excel-like browser grid functionality. The enhancement must preserve all existing PWD-specific business logic (LD calculations, GST rounding, hierarchical items, deductions) while improving the online data-entry user experience to match Excel-like interactions.

The current application is a working Python/Streamlit system with Excel processing, document generation, and batch processing capabilities. This enhancement focuses on gradual UI improvements without rewriting the backend or changing the framework.

## Glossary

- **Grid_Component**: The browser-based editable data grid that displays work items
- **Bill_Generator**: The existing Streamlit application that processes PWD bills
- **Part_Rate**: A reduced payment rate lower than the work-order rate, requiring special display and audit tracking
- **Change_Logger**: Component that tracks all modifications to bill items with original values and reasons
- **Excel_Processor**: Backend component that handles Excel file uploads and data extraction
- **PWD_Calculator**: Business logic component that performs LD calculations, GST rounding, and hierarchical item processing
- **Session_State**: Streamlit's mechanism for maintaining data across user interactions
- **Virtual_Scrolling**: Performance optimization technique that renders only visible rows
- **Hybrid_Mode**: Workflow that combines Excel upload with online editing
- **Feature_Flag**: Configuration mechanism to enable/disable new features without code changes
- **ARIA_Role**: Accessibility attribute that defines element purpose for screen readers

## Requirements

### Requirement 1: Excel-Like Grid Rendering

**User Story:** As a bill processor, I want to see work items in an Excel-like grid in my browser, so that I can quickly understand and edit the data using familiar visual patterns.

#### Acceptance Criteria

1. THE Grid_Component SHALL render work items in a tabular layout with fixed column headers
2. THE Grid_Component SHALL apply sticky positioning to the first column containing item numbers and descriptions
3. THE Grid_Component SHALL align numeric values (quantities, rates, amounts) to the right
4. THE Grid_Component SHALL align text values (descriptions, units) to the left
5. WHEN a user hovers over a column boundary, THE Grid_Component SHALL display a resize cursor
6. WHEN a user drags a column boundary, THE Grid_Component SHALL resize the column width and persist the preference in Session_State
7. THE Grid_Component SHALL highlight the currently active cell with a distinct border color
8. THE Grid_Component SHALL maintain visual consistency with Excel's grid appearance (borders, spacing, fonts)

### Requirement 2: Inline Cell Editing

**User Story:** As a bill processor, I want to edit cells directly in the grid, so that I can modify quantities and rates without switching to separate forms.

#### Acceptance Criteria

1. WHEN a user clicks on an editable cell, THE Grid_Component SHALL enter edit mode for that cell
2. WHEN a user double-clicks on an editable cell, THE Grid_Component SHALL select all text in the cell
3. WHILE a cell is in edit mode, THE Grid_Component SHALL display a text input with the current value
4. WHEN a user presses Enter in edit mode, THE Grid_Component SHALL save the value and move focus to the cell below
5. WHEN a user presses Tab in edit mode, THE Grid_Component SHALL save the value and move focus to the next cell to the right
6. WHEN a user presses Escape in edit mode, THE Grid_Component SHALL cancel editing and restore the original value
7. THE Grid_Component SHALL prevent editing of calculated fields (amounts, totals)
8. THE Grid_Component SHALL prevent editing of rate fields for non-part-rate items

### Requirement 3: Real-Time Validation and Feedback

**User Story:** As a bill processor, I want immediate feedback when I enter invalid data, so that I can correct errors before submission.

#### Acceptance Criteria

1. WHEN a user enters a non-numeric value in a quantity field, THE Grid_Component SHALL highlight the cell with a red border
2. WHEN a user enters a negative value in a quantity field, THE Grid_Component SHALL highlight the cell with a red border
3. WHEN a user hovers over an invalid cell, THE Grid_Component SHALL display a tooltip with the validation error message
4. WHEN a user enters a rate lower than the work-order rate, THE Grid_Component SHALL mark the item as part-rate
5. THE Grid_Component SHALL accept zero as a valid quantity value
6. THE Grid_Component SHALL accept decimal values in quantity fields where applicable
7. IF any cell contains invalid data, THEN THE Grid_Component SHALL disable the submit button
8. WHEN all validation errors are resolved, THE Grid_Component SHALL enable the submit button

### Requirement 4: Auto-Calculation and Real-Time Updates

**User Story:** As a bill processor, I want calculations to update automatically when I change quantities or rates, so that I can see the impact of my edits immediately.

#### Acceptance Criteria

1. WHEN a user modifies a quantity value, THE PWD_Calculator SHALL recalculate the item amount within 100ms
2. WHEN a user modifies a rate value, THE PWD_Calculator SHALL recalculate the item amount within 100ms
3. WHEN any item amount changes, THE PWD_Calculator SHALL recalculate subtotals within 200ms
4. WHEN any item amount changes, THE PWD_Calculator SHALL recalculate GST within 200ms
5. WHEN any item amount changes, THE PWD_Calculator SHALL recalculate the final total within 200ms
6. THE Grid_Component SHALL visually highlight modified cells with a light yellow background
7. THE Grid_Component SHALL display updated totals in a summary panel below the grid
8. THE PWD_Calculator SHALL preserve all existing business logic for LD calculations, GST rounding, and hierarchical items

### Requirement 5: Keyboard Navigation

**User Story:** As a bill processor, I want to navigate the grid using keyboard shortcuts, so that I can work efficiently without constantly switching between keyboard and mouse.

#### Acceptance Criteria

1. WHEN a user presses the Down Arrow key, THE Grid_Component SHALL move focus to the cell directly below
2. WHEN a user presses the Up Arrow key, THE Grid_Component SHALL move focus to the cell directly above
3. WHEN a user presses the Right Arrow key, THE Grid_Component SHALL move focus to the next cell to the right
4. WHEN a user presses the Left Arrow key, THE Grid_Component SHALL move focus to the previous cell to the left
5. WHEN a user presses Tab, THE Grid_Component SHALL move focus to the next editable cell
6. WHEN a user presses Shift+Tab, THE Grid_Component SHALL move focus to the previous editable cell
7. WHEN a user presses Home, THE Grid_Component SHALL move focus to the first cell in the current row
8. WHEN a user presses End, THE Grid_Component SHALL move focus to the last cell in the current row
9. WHEN a user presses Ctrl+Home, THE Grid_Component SHALL move focus to the first cell in the grid
10. WHEN a user presses Ctrl+End, THE Grid_Component SHALL move focus to the last cell in the grid

### Requirement 6: Copy and Paste Operations

**User Story:** As a bill processor, I want to copy and paste data between cells, rows, and columns, so that I can quickly duplicate or move data.

#### Acceptance Criteria

1. WHEN a user selects a cell and presses Ctrl+C, THE Grid_Component SHALL copy the cell value to the clipboard
2. WHEN a user selects a cell and presses Ctrl+V, THE Grid_Component SHALL paste the clipboard value into the cell
3. WHEN a user selects multiple cells and presses Ctrl+C, THE Grid_Component SHALL copy all selected values in tab-separated format
4. WHEN a user selects multiple cells and presses Ctrl+V, THE Grid_Component SHALL paste tab-separated values into the selected cells
5. THE Grid_Component SHALL validate pasted values using the same rules as manual entry
6. IF pasted data contains invalid values, THEN THE Grid_Component SHALL highlight invalid cells and display error tooltips
7. THE Grid_Component SHALL support copying from external applications (Excel, Google Sheets)
8. THE Grid_Component SHALL support pasting to external applications (Excel, Google Sheets)

### Requirement 7: Undo and Redo Functionality

**User Story:** As a bill processor, I want to undo and redo my edits, so that I can recover from mistakes without manually reverting changes.

#### Acceptance Criteria

1. WHEN a user modifies a cell value, THE Grid_Component SHALL add the change to the undo history
2. WHEN a user presses Ctrl+Z, THE Grid_Component SHALL undo the last change and restore the previous value
3. WHEN a user presses Ctrl+Y, THE Grid_Component SHALL redo the last undone change
4. THE Grid_Component SHALL maintain an undo history of at least 50 operations
5. WHEN a user makes a new edit after undoing, THE Grid_Component SHALL clear the redo history
6. THE Grid_Component SHALL display the current undo/redo state in the UI
7. THE Grid_Component SHALL disable the undo button when no operations are available to undo
8. THE Grid_Component SHALL disable the redo button when no operations are available to redo

### Requirement 8: Part-Rate Display and Handling

**User Story:** As a bill processor, I want to clearly see which items have part-rate payments, so that I can distinguish them from standard-rate items and maintain audit trails.

#### Acceptance Criteria

1. WHEN a user reduces a rate below the work-order rate, THE Grid_Component SHALL append "(Part Rate)" to the rate display
2. THE Grid_Component SHALL display part-rate values in the format "₹95 (Part Rate)"
3. THE Change_Logger SHALL record the original work-order rate internally for audit purposes
4. THE Change_Logger SHALL record the part-rate value separately
5. THE Change_Logger SHALL record the reason for the rate reduction
6. THE PWD_Calculator SHALL use the part-rate value for all calculations
7. WHEN a user exports the bill, THE Excel_Processor SHALL include both original and part-rate values in the change log sheet
8. THE Grid_Component SHALL visually distinguish part-rate cells with a light blue background

### Requirement 9: Change Tracking and Audit Log

**User Story:** As a bill processor, I want all my edits to be tracked with original values and reasons, so that I can maintain a complete audit trail for compliance.

#### Acceptance Criteria

1. WHEN a user modifies a quantity from zero to non-zero, THE Change_Logger SHALL record the change with timestamp
2. WHEN a user modifies a rate, THE Change_Logger SHALL record the original rate, new rate, and reason
3. THE Change_Logger SHALL capture the user's reason for each modification
4. THE Change_Logger SHALL store changes in Session_State for the current session
5. WHEN a user generates a bill, THE Excel_Processor SHALL create a "Change Log" sheet in the output Excel file
6. THE Change_Logger SHALL display a summary of all changes in the UI before bill generation
7. THE Change_Logger SHALL allow users to review and edit change reasons before final submission
8. THE Change_Logger SHALL persist change history when switching between online and hybrid modes

### Requirement 10: Performance Optimization for Large Datasets

**User Story:** As a bill processor, I want the grid to remain responsive when working with bills containing 1000+ items, so that I can process large projects efficiently.

#### Acceptance Criteria

1. WHEN the grid contains 1000 rows, THE Grid_Component SHALL render the initial view within 2 seconds
2. WHEN the grid contains 5000 rows, THE Grid_Component SHALL implement Virtual_Scrolling to render only visible rows
3. THE Grid_Component SHALL render scrolling updates within 16ms to maintain 60fps
4. THE Grid_Component SHALL debounce calculation updates to avoid excessive re-renders
5. THE Grid_Component SHALL use memoization for expensive calculations
6. THE Grid_Component SHALL lazy-load row data as the user scrolls
7. WHEN memory usage exceeds 500MB, THE Grid_Component SHALL trigger garbage collection
8. THE Grid_Component SHALL maintain smooth scrolling performance for datasets up to 10,000 rows

### Requirement 11: Excel Upload and Hybrid Mode Integration

**User Story:** As a bill processor, I want to upload an Excel file and then edit it online, so that I can leverage existing data while making necessary adjustments in the browser.

#### Acceptance Criteria

1. WHEN a user uploads an Excel file, THE Excel_Processor SHALL extract project details and work items
2. THE Excel_Processor SHALL populate the Grid_Component with extracted data
3. THE Grid_Component SHALL preserve all Excel formatting metadata for re-export
4. WHEN a user edits grid data after Excel upload, THE Change_Logger SHALL track all modifications
5. WHEN a user downloads the edited bill, THE Excel_Processor SHALL generate an Excel file with all edits applied
6. THE Excel_Processor SHALL maintain the original Excel structure (sheets, formulas, formatting)
7. THE Excel_Processor SHALL never corrupt data during upload-edit-download cycles
8. THE Grid_Component SHALL support switching between Excel mode, online mode, and hybrid mode without data loss

### Requirement 12: Accessibility Compliance

**User Story:** As a bill processor with visual impairments, I want the grid to work with screen readers and keyboard-only navigation, so that I can process bills independently.

#### Acceptance Criteria

1. THE Grid_Component SHALL assign appropriate ARIA_Role attributes to all grid elements
2. THE Grid_Component SHALL provide ARIA labels for column headers
3. THE Grid_Component SHALL announce cell values and positions to screen readers
4. THE Grid_Component SHALL support full keyboard operation without requiring mouse input
5. THE Grid_Component SHALL maintain visible focus indicators with sufficient contrast (4.5:1 minimum)
6. THE Grid_Component SHALL provide skip navigation links for large grids
7. THE Grid_Component SHALL announce validation errors to screen readers
8. THE Grid_Component SHALL support browser zoom up to 200% without breaking layout

### Requirement 13: Application Safety and Backward Compatibility

**User Story:** As a system administrator, I want all enhancements to preserve existing functionality, so that current users can continue their workflows without disruption.

#### Acceptance Criteria

1. THE Bill_Generator SHALL maintain support for all existing Excel file formats
2. THE Bill_Generator SHALL continue to generate bills in all existing output formats (HTML, PDF, DOCX)
3. THE Bill_Generator SHALL preserve all existing PWD business logic without modification
4. THE Bill_Generator SHALL support Feature_Flag configuration to enable/disable the new grid interface
5. IF the new grid interface is disabled, THEN THE Bill_Generator SHALL fall back to the original form-based interface
6. THE Bill_Generator SHALL process existing saved bills without requiring migration
7. THE Bill_Generator SHALL maintain API compatibility with existing batch processing scripts
8. THE Bill_Generator SHALL include automated regression tests covering all existing workflows

### Requirement 14: Rollback and Recovery Mechanisms

**User Story:** As a system administrator, I want the ability to quickly rollback to the previous version if issues arise, so that I can minimize disruption to users.

#### Acceptance Criteria

1. THE Bill_Generator SHALL tag each release with a version number in Git
2. THE Bill_Generator SHALL include a rollback script that reverts to the previous version
3. THE Bill_Generator SHALL maintain configuration files that specify the active feature set
4. WHEN a rollback is triggered, THE Bill_Generator SHALL disable new features and restore the previous UI
5. THE Bill_Generator SHALL preserve user data during rollback operations
6. THE Bill_Generator SHALL log all rollback operations with timestamps and reasons
7. THE Bill_Generator SHALL notify administrators of successful rollback completion
8. THE Bill_Generator SHALL include health check endpoints to verify system stability after rollback

### Requirement 15: Cache and Memory Management

**User Story:** As a bill processor, I want the application to remain stable during long sessions with multiple bills, so that I don't lose work due to memory issues.

#### Acceptance Criteria

1. THE Grid_Component SHALL clear Session_State data when a user resets the form
2. THE Grid_Component SHALL implement automatic garbage collection for unused data structures
3. WHEN a user completes a bill, THE Grid_Component SHALL release memory allocated for that bill's data
4. THE Grid_Component SHALL monitor memory usage and display warnings when approaching browser limits
5. THE Grid_Component SHALL implement cache eviction policies for large datasets
6. THE Grid_Component SHALL persist critical data to browser local storage as a backup
7. WHEN memory usage exceeds 80% of available memory, THE Grid_Component SHALL prompt the user to save and refresh
8. THE Grid_Component SHALL maintain stable performance across 100+ consecutive bill processing operations

### Requirement 16: Automated Testing and Quality Assurance

**User Story:** As a developer, I want comprehensive automated tests for the grid functionality, so that I can confidently deploy changes without introducing regressions.

#### Acceptance Criteria

1. THE Bill_Generator SHALL include unit tests for all Grid_Component functions with 90%+ code coverage
2. THE Bill_Generator SHALL include integration tests for Excel upload, online editing, and hybrid workflows
3. THE Bill_Generator SHALL include end-to-end tests that simulate user interactions with the grid
4. THE Bill_Generator SHALL include performance tests that verify rendering times for 1000, 5000, and 10,000 row datasets
5. THE Bill_Generator SHALL include accessibility tests that verify ARIA compliance and keyboard navigation
6. THE Bill_Generator SHALL run all tests automatically on each Git commit
7. IF any test fails, THEN THE Bill_Generator SHALL block the commit and notify the developer
8. THE Bill_Generator SHALL generate test coverage reports and display them in the CI/CD pipeline

### Requirement 17: Excel-Like Grid Parser and Pretty Printer

**User Story:** As a developer, I want robust parsing and serialization of grid data, so that data integrity is maintained throughout the upload-edit-download cycle.

#### Acceptance Criteria

1. WHEN a user uploads an Excel file, THE Excel_Processor SHALL parse all sheets into internal data structures
2. THE Excel_Processor SHALL validate the parsed data against the expected schema
3. IF parsing fails, THEN THE Excel_Processor SHALL return a descriptive error message indicating the problematic cell or sheet
4. THE Excel_Processor SHALL include a pretty printer that formats grid data back into Excel files
5. THE Excel_Processor SHALL preserve cell formatting (colors, borders, fonts) during round-trip operations
6. FOR ALL valid grid data structures, parsing then printing then parsing SHALL produce an equivalent data structure (round-trip property)
7. THE Excel_Processor SHALL handle edge cases including empty cells, merged cells, and formula cells
8. THE Excel_Processor SHALL log parsing and printing operations for debugging purposes

## Notes on Testing

The requirements include several properties that should be tested using property-based testing:

- Requirement 17, Criterion 6: Round-trip property for Excel parsing and printing
- Requirement 4: Calculation invariants (totals should always equal sum of items)
- Requirement 6: Copy-paste operations should preserve data integrity
- Requirement 7: Undo-redo operations should be inverse operations
- Requirement 10: Performance should scale linearly with dataset size

These properties ensure the grid functionality is robust across a wide range of inputs and usage patterns.
