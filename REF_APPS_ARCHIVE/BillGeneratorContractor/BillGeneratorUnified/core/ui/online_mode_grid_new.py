"""
Online Entry Mode with Excel-Like Grid
Phase 1 Implementation: Fixed version based on GenSpark code
Fixes all 5 critical bugs and implements proper state management
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import io
import zipfile


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def _default_df(n: int, offset: int = 0) -> pd.DataFrame:
    """
    Create default items DataFrame with n blank rows.
    
    Args:
        n: Number of rows to create
        offset: Starting index for item numbers
        
    Returns:
        DataFrame with columns: Item No, Description, Unit, Quantity, Rate, Amount
    """
    if n == 0:
        # Return empty DataFrame with correct columns
        return pd.DataFrame(columns=["Item No", "Description", "Unit", "Quantity", "Rate", "Amount"])
    
    return pd.DataFrame([{
        "Item No":    f"{offset + i + 1:03d}",
        "Description": "",
        "Unit":       "NOS",
        "Quantity":   0.0,
        "Rate":       0.0,
        "Amount":     0.0,
    } for i in range(n)])


def _safe_float(val, default: float = 0.0) -> float:
    """
    Safely convert value to float with fallback.
    
    Args:
        val: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float value or default
    """
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _recalc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recalculate Amount column for all rows.
    
    Args:
        df: DataFrame with Quantity and Rate columns
        
    Returns:
        DataFrame with updated Amount column
    """
    df = df.copy()
    df["Amount"] = df["Quantity"] * df["Rate"]
    return df


def update_validation_status(df: pd.DataFrame) -> pd.DataFrame:
    """
    Update validation status for all rows.
    
    Validation Rules:
    - ⚪ Empty: All fields empty or zero (ignored)
    - 🟢 Valid: Description + Quantity > 0 + Rate > 0
    - 🟠 Partial: Description but missing Quantity or Rate
    - 🔴 Invalid: Quantity or Rate without Description
    
    Args:
        df: DataFrame with Description, Quantity, Rate columns
        
    Returns:
        DataFrame with updated Status column
    """
    if df is None or df.empty:
        return df
    
    df = df.copy()
    
    # Add Status column if it doesn't exist
    if 'Status' not in df.columns:
        df.insert(0, 'Status', '⚪')
    
    for idx, row in df.iterrows():
        qty = float(row.get('Quantity', 0))
        rate = float(row.get('Rate', 0))
        desc = str(row.get('Description', '')).strip()
        
        # Check if row is active (has any data)
        is_active = qty > 0 or rate > 0 or desc != ''
        
        if not is_active:
            status = '⚪'  # Empty / Ignored
        elif desc and qty > 0 and rate > 0:
            status = '🟢'  # Fully valid
        elif desc == '' and (qty > 0 or rate > 0):
            status = '🔴 No Desc'  # Error: has qty/rate but no description
        elif desc != '' and (qty == 0 or rate == 0):
            status = '🟠 Miss Q/R'  # Partial: has description but missing qty or rate
        else:
            status = '🔴 Inv'  # Catch-all invalid
        
        df.loc[idx, 'Status'] = status
    
    return df


def can_submit(df: pd.DataFrame) -> tuple[bool, str]:
    """
    Check if grid data is valid for document generation.
    
    Submit button should be enabled only when:
    - At least one valid item exists (🟢)
    - No active items have invalid status (🔴 or 🟠)
    
    Args:
        df: DataFrame with Status column
        
    Returns:
        Tuple of (can_submit: bool, error_message: str)
    """
    if df is None or df.empty:
        return False, "No items in grid"
    
    # Get active items (not empty ⚪)
    active_mask = ~df['Status'].str.contains('⚪')
    active_df = df[active_mask]
    
    if len(active_df) == 0:
        return False, "No active items. Please add at least one item with Description, Quantity > 0, and Rate > 0."
    
    # Check for invalid items (🔴 or 🟠)
    invalid_mask = active_df['Status'].str.contains('🔴|🟠')
    invalid_count = invalid_mask.sum()
    
    if invalid_count > 0:
        return False, f"Found {invalid_count} invalid active items. Please fix items marked with 🔴 or 🟠."
    
    # Check for at least one valid item (🟢)
    valid_mask = active_df['Status'].str.contains('🟢')
    valid_count = valid_mask.sum()
    
    if valid_count == 0:
        return False, "No valid items. A valid item must have Description, Quantity > 0, AND Rate > 0."
    
    return True, ""


def _diff_log(old: pd.DataFrame, new: pd.DataFrame, work_order_rates: dict = None) -> list[dict]:
    """
    Generate change log entries by comparing two DataFrames.
    
    Compares old and new DataFrames to detect changes in Quantity and Rate fields.
    Auto-generates reason based on change type:
    - Zero-Qty Activation: Quantity changed from 0 to non-zero
    - Rate Reduction: Rate decreased
    - Rate Increase: Rate increased
    - Qty Change: Quantity changed (non-zero to non-zero)
    - Part-Rate Applied: Rate reduced below work-order rate
    
    Args:
        old: Previous DataFrame state
        new: Current DataFrame state
        work_order_rates: Dictionary mapping Item No to original work-order rate (optional)
        
    Returns:
        List of change dictionaries with keys:
        - Item No: Item number
        - Field: Changed field name (Quantity or Rate)
        - Old: Previous value
        - New: Current value
        - Reason: Auto-generated reason for change
        - Timestamp: Time of change (HH:MM:SS)
        - Work_Order_Rate: Original work-order rate (for part-rate changes)
    """
    if old is None or new is None:
        return []
    
    if old.empty or new.empty:
        return []
    
    changes = []
    work_order_rates = work_order_rates or {}
    
    # Compare only rows that exist in both DataFrames
    for idx in new.index:
        if idx >= len(old):
            continue
        
        item_no = new.loc[idx, "Item No"]
        
        # Check Quantity changes
        old_qty = _safe_float(old.loc[idx, "Quantity"], 0.0)
        new_qty = _safe_float(new.loc[idx, "Quantity"], 0.0)
        
        if abs(old_qty - new_qty) > 1e-9:
            # Determine reason
            if old_qty == 0 and new_qty > 0:
                reason = "Zero-Qty Activation"
            elif old_qty > 0 and new_qty == 0:
                reason = "Qty Set to Zero"
            else:
                reason = "Qty Change"
            
            changes.append({
                "Item No": item_no,
                "Field": "Quantity",
                "Old": round(old_qty, 3),
                "New": round(new_qty, 3),
                "Reason": reason,
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
            })
        
        # Check Rate changes
        old_rate = _safe_float(old.loc[idx, "Rate"], 0.0)
        new_rate = _safe_float(new.loc[idx, "Rate"], 0.0)
        
        if abs(old_rate - new_rate) > 1e-9:
            # Determine reason
            work_order_rate = work_order_rates.get(item_no)
            
            if work_order_rate and new_rate < (work_order_rate - 0.01):
                reason = "Part-Rate Applied"
            elif new_rate < old_rate:
                reason = "Rate Reduction"
            elif new_rate > old_rate:
                reason = "Rate Increase"
            else:
                reason = "Rate Change"
            
            change_entry = {
                "Item No": item_no,
                "Field": "Rate",
                "Old": round(old_rate, 3),
                "New": round(new_rate, 3),
                "Reason": reason,
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
            }
            
            # Add work-order rate for part-rate changes
            if work_order_rate and reason == "Part-Rate Applied":
                change_entry["Work_Order_Rate"] = round(work_order_rate, 3)
            
            changes.append(change_entry)
    
    return changes


def _extract_excel(file) -> dict:
    """
    Extract data from uploaded Excel file.
    
    Uses existing ExcelProcessor to extract project details and work items.
    Also stores original work-order rates for part-rate detection.
    
    Args:
        file: Uploaded file object from st.file_uploader
        
    Returns:
        Dictionary with keys:
        - project_name: Name of work/project
        - contractor: Contractor name
        - df: DataFrame with work items (Item No, Description, Unit, Quantity, Rate, Amount)
        - work_order_rates: Dictionary mapping Item No to original work-order rate
        
        Returns empty dict on error.
    """
    try:
        from core.processors.excel_processor import ExcelProcessor
        
        processor = ExcelProcessor()
        data = processor.process_excel(file)
        result = {}
        
        # Extract title data
        title = data.get("title_data", {})
        result["project_name"] = title.get("Name of Work", "")
        result["contractor"] = title.get(
            "Name of Contractor or supplier",
            title.get("Contractor", "")
        )
        
        # Extract work order data
        wo_df = data.get("work_order_data", pd.DataFrame())
        if not wo_df.empty:
            rows = []
            work_order_rates = {}
            
            for _, row in wo_df.iterrows():
                item_no = str(row.get("Item No.", ""))
                qty = _safe_float(row.get("Quantity", 0))
                rate = _safe_float(row.get("Rate", 0))
                
                # Store original work-order rate for part-rate detection
                if item_no and rate > 0:
                    work_order_rates[item_no] = rate
                
                rows.append({
                    "Item No": item_no,
                    "Description": str(row.get("Description", "")),
                    "Unit": str(row.get("Unit", "NOS")),
                    "Quantity": qty,
                    "Rate": rate,
                    "Amount": qty * rate,
                })
            
            result["df"] = pd.DataFrame(rows)
            result["work_order_rates"] = work_order_rates
        
        return result
    except Exception as e:
        st.error(f"❌ Excel extraction error: {e}")
        return {}


def _init_session_state() -> dict:
    """
    Initialize session state dictionary with default values.
    
    Creates the 'ogd' (online grid data) dictionary with all required keys:
    - project_name: Name of work/project
    - contractor: Contractor name
    - bill_date: Bill date
    - tender_premium: Tender premium percentage
    - df: DataFrame with work items
    - last_upload: Last uploaded filename (for tracking re-uploads)
    - change_log: List of change log entries
    - prev_df: Previous DataFrame snapshot (for change detection)
    - work_order_rates: Dictionary mapping Item No to original work-order rate (for part-rate detection)
    
    Returns:
        Dictionary with initialized session state
    """
    return {
        "project_name": "",
        "contractor": "",
        "bill_date": None,
        "tender_premium": 4.0,
        "df": _default_df(5),
        "last_upload": None,
        "change_log": [],
        "prev_df": None,
        "work_order_rates": {},  # Store original rates for part-rate detection
    }


def _reset_session_state(ss: st.session_state) -> None:
    """
    Reset session state to initial values.
    
    Clears all data from the 'ogd' dictionary and reinitializes
    with default values.
    
    Args:
        ss: Streamlit session state object
    """
    ss.ogd = _init_session_state()


def _is_new_upload(current_filename: str, last_upload: str) -> bool:
    """
    Check if uploaded file is new (different from last upload).
    
    This fixes Bug #2: excel_uploaded flag never resets.
    Instead of using a boolean flag, we compare filenames.
    
    Args:
        current_filename: Name of currently uploaded file
        last_upload: Name of last uploaded file (or None)
        
    Returns:
        True if this is a new upload, False otherwise
    """
    if current_filename is None:
        return False
    
    if last_upload is None:
        return True
    
    return current_filename != last_upload


def _column_config() -> dict:
    """
    Generate column configuration for st.data_editor.
    
    Configures each column with appropriate type, width, and editability:
    - Status: Small, disabled (auto-generated)
    - Item No: Small, required
    - Description: Large, required
    - Unit: Small, selectbox with predefined options
    - Quantity: Small, editable, number with 2 decimals
    - Rate: Small, editable, number with 2 decimals
    - Amount: Medium, disabled (calculated)
    
    Returns:
        Dictionary mapping column names to st.column_config objects
    """
    return {
        "Status": st.column_config.TextColumn(
            "Status",
            width="small",
            disabled=True,
            help="Validation status: ⚪ Empty, 🟢 Valid, 🟠 Partial, 🔴 Invalid"
        ),
        "Item No": st.column_config.TextColumn(
            "Item No",
            width="small",
            required=True
        ),
        "Description": st.column_config.TextColumn(
            "Description",
            width="large",
            required=True
        ),
        "Unit": st.column_config.SelectboxColumn(
            "Unit",
            width="small",
            options=["NOS", "CUM", "SQM", "RMT", "MT", "KG", "LTR", "SET", "LS", "JOB"],
            required=True
        ),
        "Quantity": st.column_config.NumberColumn(
            "✏️ Qty",
            width="small",
            min_value=0.0,
            step=0.01,
            format="%.2f",
            required=True
        ),
        "Rate": st.column_config.NumberColumn(
            "✏️ Rate (₹)",
            width="small",
            min_value=0.0,
            step=0.01,
            format="%.2f",
            required=True
        ),
        "Amount": st.column_config.NumberColumn(
            "Amount (₹)",
            width="medium",
            format="₹%.2f",
            disabled=True
        ),
    }


def _grid_tips() -> None:
    """
    Display Excel-like grid usage tips.
    
    Shows keyboard shortcuts and navigation hints for the grid interface.
    """
    st.markdown("""
    <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
        💡 <b>Grid Tips:</b>
        &nbsp;&nbsp;•&nbsp; Click a cell to edit
        &nbsp;&nbsp;•&nbsp; Tab / Enter to move
        &nbsp;&nbsp;•&nbsp; Delete to clear
        &nbsp;&nbsp;•&nbsp; Ctrl+C / V to copy-paste rows
        &nbsp;&nbsp;•&nbsp; Use ➕ buttons to add rows
    </div>
    """, unsafe_allow_html=True)


def _calculate_metrics(df: pd.DataFrame, tender_premium: float) -> dict:
    """
    Calculate summary metrics from DataFrame.
    
    Args:
        df: DataFrame with work items (must have Status, Quantity, Rate, Amount columns)
        tender_premium: Tender premium percentage
        
    Returns:
        Dictionary with keys:
        - total_items: Total number of rows
        - active_items: Number of non-empty items
        - valid_items: Number of valid items (🟢)
        - invalid_items: Number of invalid items (🔴 or 🟠)
        - grand_total: Sum of all amounts
        - premium_amount: Premium amount
        - net_payable: Grand total + premium
    """
    if df is None or df.empty:
        return {
            "total_items": 0,
            "active_items": 0,
            "valid_items": 0,
            "invalid_items": 0,
            "grand_total": 0.0,
            "premium_amount": 0.0,
            "net_payable": 0.0,
        }
    
    # Count items by status
    total_items = len(df)
    active_items = int((~df['Status'].str.contains('⚪')).sum()) if 'Status' in df.columns else 0
    valid_items = int((df['Status'] == '🟢').sum()) if 'Status' in df.columns else 0
    invalid_items = int((df['Status'].str.contains('🔴|🟠')).sum()) if 'Status' in df.columns else 0
    
    # Calculate totals
    grand_total = float(df['Amount'].sum()) if 'Amount' in df.columns else 0.0
    premium_amount = grand_total * tender_premium / 100
    net_payable = grand_total + premium_amount
    
    return {
        "total_items": total_items,
        "active_items": active_items,
        "valid_items": valid_items,
        "invalid_items": invalid_items,
        "grand_total": grand_total,
        "premium_amount": premium_amount,
        "net_payable": net_payable,
    }


def _detect_part_rates(df: pd.DataFrame, work_order_rates: dict) -> pd.DataFrame:
    """
    Detect and mark part-rate items.
    
    Part-rate items are those where the current rate is lower than the
    original work-order rate from the Excel upload.
    
    Args:
        df: DataFrame with work items
        work_order_rates: Dictionary mapping Item No to original work-order rate
        
    Returns:
        DataFrame with Part_Rate column added (True/False)
    """
    if df is None or df.empty or not work_order_rates:
        if df is not None and not df.empty:
            df = df.copy()
            df['Part_Rate'] = False
        return df
    
    df = df.copy()
    df['Part_Rate'] = False
    
    for idx, row in df.iterrows():
        item_no = row.get('Item No', '')
        current_rate = _safe_float(row.get('Rate', 0))
        
        if item_no in work_order_rates:
            original_rate = work_order_rates[item_no]
            # Part-rate if current rate is lower than original (with small tolerance)
            if current_rate < (original_rate - 0.01):
                df.loc[idx, 'Part_Rate'] = True
    
    return df


def _format_rate_display(rate: float, is_part_rate: bool) -> str:
    """
    Format rate for display with part-rate indicator.
    
    Args:
        rate: Rate value
        is_part_rate: Whether this is a part-rate item
        
    Returns:
        Formatted string like "₹95.00" or "₹95.00 (Part Rate)"
    """
    formatted = f"₹{rate:.2f}"
    if is_part_rate:
        formatted += " (Part Rate)"
    return formatted


def _apply_part_rate_styling(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply visual styling to part-rate items.
    
    Note: Streamlit's st.data_editor doesn't support cell-level styling directly.
    This function prepares the data for display. Visual distinction will be
    shown through the Rate column format.
    
    Args:
        df: DataFrame with Part_Rate column
        
    Returns:
        DataFrame with formatted Rate_Display column
    """
    if df is None or df.empty:
        return df
    
    df = df.copy()
    
    if 'Part_Rate' in df.columns and 'Rate' in df.columns:
        df['Rate_Display'] = df.apply(
            lambda row: _format_rate_display(
                _safe_float(row['Rate'], 0),
                row.get('Part_Rate', False)
            ),
            axis=1
        )
    
    return df


def _generate(config: dict) -> None:
    """
    Generate documents and create ZIP download.
    
    Args:
        config: Dictionary with keys:
        - project_name: Name of work
        - contractor: Contractor name
        - bill_date: Bill date
        - tender_premium: Tender premium percentage
        - items_df: DataFrame with work items
        - change_log: List of change log entries
        - gen_html: Generate HTML documents
        - gen_pdf: Generate PDF documents
        - gen_docx: Generate DOCX documents
    """
    with st.spinner("🔄 Generating documents..."):
        try:
            from core.generators.document_generator import DocumentGenerator
            
            # Extract config
            project_name = config.get("project_name", "")
            contractor = config.get("contractor", "")
            bill_date = config.get("bill_date")
            tender_premium = config.get("tender_premium", 4.0)
            items_df = config.get("items_df", pd.DataFrame())
            change_log = config.get("change_log", [])
            gen_html = config.get("gen_html", True)
            gen_pdf = config.get("gen_pdf", True)
            gen_docx = config.get("gen_docx", False)
            
            # Format bill date
            bill_date_str = bill_date.strftime("%d/%m/%Y") if bill_date else ""
            
            # Calculate totals
            total = float(items_df["Amount"].sum())
            premium_amt = total * tender_premium / 100
            
            # Prepare processed data structure
            processed = {
                "title_data": {
                    "Name of Work": project_name,
                    "Contractor": contractor,
                    "Bill Date": bill_date_str,
                    "Tender Premium %": tender_premium,
                },
                "work_order_data": items_df.rename(
                    columns={"Item No": "Item No."}
                ).to_dict("records"),
                "totals": {
                    "grand_total": total,
                    "premium": {
                        "percent": tender_premium / 100,
                        "amount": premium_amt
                    },
                    "net_payable": total + premium_amt,
                },
            }
            
            # Generate documents
            gen = DocumentGenerator(processed)
            html_docs = gen.generate_all_documents() if gen_html else {}
            pdf_docs = gen.create_pdf_documents(html_docs) if gen_pdf and html_docs else {}
            doc_docs = gen.generate_doc_documents() if gen_docx else {}
            
            st.success("✅ Documents generated successfully!")
            
            # Create ZIP file
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                # Add HTML documents
                for name, content in html_docs.items():
                    b = content.encode() if isinstance(content, str) else content
                    zf.writestr(f"html/{name}.html", b)
                
                # Add PDF documents
                for name, content in pdf_docs.items():
                    zf.writestr(f"pdf/{name}.pdf", content)
                
                # Add DOCX documents
                for name, content in doc_docs.items():
                    zf.writestr(f"word/{name}", content)
                
                # Add change log Excel if changes exist
                if change_log:
                    cl_df = pd.DataFrame(change_log)
                    xl_buf = io.BytesIO()
                    with pd.ExcelWriter(xl_buf, engine="openpyxl") as writer:
                        items_df.to_excel(writer, sheet_name="Items", index=False)
                        cl_df.to_excel(writer, sheet_name="Change Log", index=False)
                    zf.writestr("data/bill_with_changelog.xlsx", xl_buf.getvalue())
            
            buf.seek(0)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # ZIP download button
            st.download_button(
                "📦 Download All (ZIP)",
                data=buf.getvalue(),
                file_name=f"bill_{ts}.zip",
                mime="application/zip",
                use_container_width=True,
            )
            
            # Individual download buttons
            st.markdown("#### Individual Downloads")
            c1, c2, c3 = st.columns(3)
            
            if gen_html and html_docs:
                with c1:
                    st.markdown("**📄 HTML**")
                    for name, content in html_docs.items():
                        b = content.encode() if isinstance(content, str) else content
                        st.download_button(
                            f"📄 {name}",
                            b,
                            f"{name}.html",
                            "text/html",
                            key=f"h_{name}",
                            use_container_width=True
                        )
            
            if gen_pdf and pdf_docs:
                with c2:
                    st.markdown("**📕 PDF**")
                    for name, content in pdf_docs.items():
                        st.download_button(
                            f"📕 {name}",
                            content,
                            f"{name}.pdf",
                            "application/pdf",
                            key=f"p_{name}",
                            use_container_width=True
                        )
            
            if gen_docx and doc_docs:
                with c3:
                    st.markdown("**📝 DOCX**")
                    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    for name, content in doc_docs.items():
                        st.download_button(
                            f"📝 {name}",
                            content,
                            name,
                            mime,
                            key=f"d_{name}",
                            use_container_width=True
                        )
        
        except Exception as e:
            st.error(f"❌ Document generation failed: {e}")
            import traceback
            st.code(traceback.format_exc())


# ═══════════════════════════════════════════════════════════════════════════
# MAIN FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def show_online_mode_grid(config):
    """
    Show online entry interface with Excel-like grid.
    
    This is the main entry point for the online mode grid interface.
    Implements all 5 critical bug fixes:
    1. Scope error - All variables properly scoped
    2. Upload flag - Uses filename tracking instead of boolean
    3. Change tracking - Uses snapshot-based diff detection
    4. Validation - Validates all items before submission
    5. Visual distinction - Status column shows validation state
    
    Args:
        config: Application configuration dictionary
    """
    st.markdown("## 💻 Online Entry Mode — Excel-Like Grid")
    
    # ═══════════════════════════════════════════════════════════════════════
    # Initialize session state
    # ═══════════════════════════════════════════════════════════════════════
    ss = st.session_state
    if "ogd" not in ss:
        ss.ogd = _init_session_state()
    
    ogd = ss.ogd  # Shortcut
    
    # ═══════════════════════════════════════════════════════════════════════
    # Step 1: Project Details
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown("### 📋 Step 1: Project Details")
    
    col_up, col_rst = st.columns([3, 1])
    
    with col_up:
        excel_file = st.file_uploader(
            "Upload Excel to auto-fill (optional)",
            type=["xlsx", "xls", "xlsm"],
            key="ogd_uploader",
        )
        
        # Re-extract only when a NEW file arrives (Bug #2 fix)
        if excel_file and _is_new_upload(excel_file.name, ogd["last_upload"]):
            with st.spinner("📂 Extracting from Excel..."):
                extracted = _extract_excel(excel_file)
            
            if extracted:
                ogd["project_name"] = extracted.get("project_name", "")
                ogd["contractor"] = extracted.get("contractor", "")
                if extracted.get("df") is not None:
                    ogd["df"] = _recalc(extracted["df"])
                # Store work-order rates for part-rate detection
                if extracted.get("work_order_rates"):
                    ogd["work_order_rates"] = extracted["work_order_rates"]
                ogd["last_upload"] = excel_file.name
                st.success(f"✅ Loaded {excel_file.name}")
                st.rerun()
    
    with col_rst:
        st.write("")
        st.write("")
        if st.button("🔄 Reset All", use_container_width=True):
            _reset_session_state(ss)
            st.rerun()
    
    # Project details input
    c1, c2 = st.columns(2)
    with c1:
        ogd["project_name"] = st.text_input(
            "Name of Work *",
            value=ogd["project_name"],
            placeholder="Required"
        )
        ogd["contractor"] = st.text_input(
            "Contractor Name",
            value=ogd["contractor"]
        )
    with c2:
        ogd["bill_date"] = st.date_input(
            "Bill Date",
            value=ogd["bill_date"]
        )
        ogd["tender_premium"] = st.number_input(
            "Tender Premium (%)",
            0.0, 100.0,
            value=float(ogd["tender_premium"]),
            step=0.5
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # Step 2: Excel-Like Grid
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 📊 Step 2: Work Items — Excel-Like Grid")
    
    _grid_tips()
    
    cur = ogd["df"]
    
    # Add rows buttons
    c1, c2, c3 = st.columns([2, 1, 1])
    active = int((cur["Quantity"] > 0).sum())
    with c1:
        st.info(f"📦 Rows: {len(cur)} | Active (Qty>0): {active}")
    with c2:
        if st.button("➕ Add 5 Rows", use_container_width=True, key="add5"):
            ogd["df"] = pd.concat(
                [cur, _default_df(5, offset=len(cur))],
                ignore_index=True
            )
            st.rerun()
    with c3:
        if st.button("➕ Add 10 Rows", use_container_width=True, key="add10"):
            ogd["df"] = pd.concat(
                [cur, _default_df(10, offset=len(cur))],
                ignore_index=True
            )
            st.rerun()
    
    # Save snapshot BEFORE showing the editor (Bug #3 fix)
    prev_snap = cur.copy()
    
    # Show data editor
    edited = st.data_editor(
        cur,
        use_container_width=True,
        num_rows="dynamic",
        height=550,
        column_config=_column_config(),
        hide_index=True,
        key="ogd_editor",
    )
    
    # Recalculate Amount immediately after edit
    edited = _recalc(edited)
    
    # Detect part-rates (compare against work-order rates)
    edited = _detect_part_rates(edited, ogd.get("work_order_rates", {}))
    
    # Update validation status
    edited = update_validation_status(edited)
    
    # Track changes (compare ONLY if shape matches) (Bug #3 fix)
    if len(edited) == len(prev_snap):
        new_changes = _diff_log(prev_snap, edited, ogd.get("work_order_rates", {}))
        if new_changes:
            ogd["change_log"].extend(new_changes)
    
    # Persist updated df
    ogd["df"] = edited
    
    # ═══════════════════════════════════════════════════════════════════════
    # Step 3: Summary & Generation
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 📊 Step 3: Summary & Generate")
    
    # Calculate metrics
    metrics = _calculate_metrics(edited, ogd["tender_premium"])
    
    # Count part-rate items
    part_rate_count = int(edited.get('Part_Rate', pd.Series([False] * len(edited))).sum()) if 'Part_Rate' in edited.columns else 0
    
    # Display metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Amount", f"₹{metrics['grand_total']:,.2f}")
    m2.metric(
        "Premium",
        f"₹{metrics['premium_amount']:,.2f}",
        delta=f"{ogd['tender_premium']}%"
    )
    m3.metric("Net Payable", f"₹{metrics['net_payable']:,.2f}")
    m4.metric(
        "Active Items",
        f"{metrics['valid_items']}/{metrics['active_items']}"
    )
    
    # Show part-rate indicator if any exist
    if part_rate_count > 0:
        st.info(f"💰 {part_rate_count} item(s) with Part-Rate detected")
    
    # Change log expander
    if ogd["change_log"]:
        with st.expander(
            f"📝 Change Log ({len(ogd['change_log'])} entries)",
            expanded=False
        ):
            st.dataframe(
                pd.DataFrame(ogd["change_log"]),
                use_container_width=True,
                hide_index=True
            )
    
    # Output options
    st.markdown("#### 📄 Output Options")
    c1, c2, c3 = st.columns(3)
    gen_html = c1.checkbox("📄 HTML", value=True)
    gen_pdf = c2.checkbox("📕 PDF", value=True)
    gen_docx = c3.checkbox("📝 DOCX", value=False)
    
    # Generate button (Bug #4 fix - validation before generation)
    can, msg = can_submit(edited)
    
    if st.button(
        "🚀 Generate Documents",
        type="primary",
        use_container_width=True,
        disabled=not can,
        key="generate_btn"
    ):
        if not ogd["project_name"]:
            st.error("❌ Please enter Name of Work")
        elif not can:
            st.error(f"❌ {msg}")
        else:
            # Get only valid items for generation
            valid_df = edited[edited["Status"] == "🟢"].copy()
            
            _generate({
                "project_name": ogd["project_name"],
                "contractor": ogd["contractor"],
                "bill_date": ogd["bill_date"],
                "tender_premium": ogd["tender_premium"],
                "items_df": valid_df,
                "change_log": ogd["change_log"],
                "gen_html": gen_html,
                "gen_pdf": gen_pdf,
                "gen_docx": gen_docx,
            })
    
    # Show validation error if button is disabled
    if not can:
        st.warning(f"⚠️ {msg}")
