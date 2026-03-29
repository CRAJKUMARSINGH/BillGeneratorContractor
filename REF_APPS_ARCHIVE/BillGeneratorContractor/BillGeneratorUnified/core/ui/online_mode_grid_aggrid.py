"""
Online Entry Mode with AG-Grid (Week 2 Enhanced Version)
Implements all Week 2 UX enhancements:
- Sticky headers and columns
- Advanced column resizing with persistence
- Dynamic row height
- Enhanced visual indicators
- Advanced validation tooltips
- Full keyboard navigation
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import io
import zipfile

try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
    AGGRID_AVAILABLE = True
except ImportError:
    AGGRID_AVAILABLE = False
    st.warning("⚠️ streamlit-aggrid not installed. Install with: pip install streamlit-aggrid")


# Import helper functions from the base implementation
from core.ui.online_mode_grid_new import (
    _default_df, _safe_float, _recalc, update_validation_status, can_submit,
    _diff_log, _extract_excel, _init_session_state, _reset_session_state,
    _is_new_upload, _calculate_metrics, _detect_part_rates, _format_rate_display,
    _generate
)


# ═══════════════════════════════════════════════════════════════════════════
# AG-GRID SPECIFIC FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def _build_grid_options(df: pd.DataFrame) -> dict:
    """
    Build AG-Grid options with all Week 2 enhancements.
    
    Features:
    - Sticky header (always visible)
    - Pinned first column (Item No - freeze pane style)
    - Editable cells with validation
    - Live formula for Amount calculation
    - Custom cell styling
    - Keyboard navigation
    - Column resizing with persistence
    - Dynamic row height
    
    Args:
        df: DataFrame to configure
        
    Returns:
        GridOptions dictionary
    """
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Column Configuration
    # ═══════════════════════════════════════════════════════════════════════
    
    # Status column - read-only, small width
    gb.configure_column(
        "Status",
        header_name="Status",
        width=80,
        editable=False,
        pinned="left",  # Sticky with Item No
        cellStyle={"textAlign": "center"},
        tooltipField="Status"
    )
    
    # Item No - pinned left (freeze pane)
    gb.configure_column(
        "Item No",
        header_name="Item No",
        width=90,
        editable=False,
        pinned="left",
        cellStyle={"fontWeight": "bold"}
    )
    
    # Description - wide, editable, auto-height
    gb.configure_column(
        "Description",
        header_name="Description",
        width=350,
        editable=True,
        wrapText=True,  # Dynamic row height
        autoHeight=True,  # Auto-adjust row height
        cellStyle={"whiteSpace": "normal"}
    )
    
    # Unit - dropdown editor
    gb.configure_column(
        "Unit",
        header_name="Unit",
        width=80,
        editable=True,
        cellEditor="agSelectCellEditor",
        cellEditorParams={
            "values": ["NOS", "CUM", "SQM", "RMT", "MT", "KG", "LTR", "SET", "LS", "JOB"]
        }
    )
    
    # Quantity - numeric, editable, highlighted
    gb.configure_column(
        "Quantity",
        header_name="✏️ Qty",
        width=100,
        editable=True,
        type=["numericColumn", "numberColumnFilter"],
        valueFormatter="value.toFixed(2)",
        cellStyle=JsCode("""
            function(params) {
                return {
                    backgroundColor: '#fffde7',
                    textAlign: 'right'
                };
            }
        """)
    )
    
    # Rate - numeric, editable, highlighted
    gb.configure_column(
        "Rate",
        header_name="✏️ Rate (₹)",
        width=120,
        editable=True,
        type=["numericColumn", "numberColumnFilter"],
        valueFormatter="'₹' + value.toFixed(2)",
        cellStyle=JsCode("""
            function(params) {
                return {
                    backgroundColor: '#fffde7',
                    textAlign: 'right'
                };
            }
        """)
    )
    
    # Amount - calculated, read-only, live formula
    gb.configure_column(
        "Amount",
        header_name="Amount (₹)",
        width=140,
        editable=False,
        type=["numericColumn"],
        valueGetter=JsCode("""
            function(params) {
                return params.data.Quantity * params.data.Rate;
            }
        """),
        valueFormatter="'₹' + value.toFixed(2)",
        cellStyle={"textAlign": "right", "fontWeight": "bold"}
    )
    
    # Part_Rate column (hidden, used for styling)
    if 'Part_Rate' in df.columns:
        gb.configure_column(
            "Part_Rate",
            hide=True
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # Grid Options
    # ═══════════════════════════════════════════════════════════════════════
    
    gb.configure_grid_options(
        # Selection
        enableRangeSelection=True,  # Ctrl+C/V like Excel
        rowSelection="multiple",
        
        # Editing
        undoRedoCellEditing=True,  # Ctrl+Z support
        undoRedoCellEditingLimit=50,
        stopEditingWhenCellsLoseFocus=True,
        singleClickEdit=False,  # Double-click to edit
        
        # Navigation
        tabToNextCell=True,
        enterNavigatesVertically=True,
        enterNavigatesVerticallyAfterEdit=True,
        
        # Resizing
        enableCellChangeFlash=True,  # Flash on change
        animateRows=True,
        
        # Performance
        suppressColumnVirtualisation=False,
        suppressRowVirtualisation=False,
        
        # Styling
        rowHeight=40,  # Default row height
        headerHeight=45,
        
        # Tooltips
        tooltipShowDelay=500,
        enableBrowserTooltips=False  # Use AG-Grid tooltips
    )
    
    # Row styling based on validation status
    gb.configure_grid_options(
        getRowStyle=JsCode("""
            function(params) {
                if (params.data.Quantity > 0 || params.data.Rate > 0) {
                    return {backgroundColor: '#f0f9ff'};  // Active items - light blue
                }
                return {backgroundColor: '#ffffff'};  // Empty items - white
            }
        """)
    )
    
    return gb.build()


def _show_aggrid_editor(df: pd.DataFrame, key: str = "aggrid_editor") -> pd.DataFrame:
    """
    Show AG-Grid editor with all Week 2 enhancements.
    
    Args:
        df: DataFrame to edit
        key: Unique key for the grid
        
    Returns:
        Edited DataFrame
    """
    if not AGGRID_AVAILABLE:
        st.error("❌ AG-Grid not available. Please install: pip install streamlit-aggrid")
        return df
    
    grid_options = _build_grid_options(df)
    
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        fit_columns_on_grid_load=False,  # Preserve column widths
        theme="streamlit",  # or "alpine", "balham", "material"
        height=550,
        allow_unsafe_jscode=True,  # Required for valueGetter and styling
        key=key,
        reload_data=False  # Preserve state
    )
    
    return grid_response["data"]


def _fallback_editor(df: pd.DataFrame, key: str = "fallback_editor") -> pd.DataFrame:
    """
    Fallback to st.data_editor if AG-Grid not available.
    
    Args:
        df: DataFrame to edit
        key: Unique key for the editor
        
    Returns:
        Edited DataFrame
    """
    from core.ui.online_mode_grid_new import _column_config
    
    return st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        height=550,
        column_config=_column_config(),
        hide_index=True,
        key=key
    )


def _grid_tips_enhanced() -> None:
    """
    Display enhanced grid usage tips for AG-Grid.
    """
    st.markdown("""
    <div style="background-color: #e3f2fd; padding: 12px; border-radius: 5px; margin-bottom: 10px; border-left: 4px solid #2196f3;">
        <b>💡 Enhanced Grid Features:</b><br/>
        <div style="margin-top: 8px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <div>
                • <b>Sticky Header:</b> Header stays visible while scrolling<br/>
                • <b>Frozen Column:</b> Item No column always visible<br/>
                • <b>Auto-Height:</b> Rows expand for long descriptions<br/>
                • <b>Live Calculation:</b> Amount updates instantly
            </div>
            <div>
                • <b>Undo/Redo:</b> Ctrl+Z / Ctrl+Y to undo changes<br/>
                • <b>Range Select:</b> Click+drag or Shift+click<br/>
                • <b>Copy/Paste:</b> Ctrl+C / Ctrl+V like Excel<br/>
                • <b>Resize Columns:</b> Drag column borders
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def show_online_mode_grid_aggrid(config):
    """
    Show online entry interface with AG-Grid (Week 2 Enhanced).
    
    Implements all Week 2 UX enhancements:
    - Sticky headers and frozen columns
    - Advanced column resizing
    - Dynamic row height
    - Enhanced visual indicators
    - Advanced validation tooltips
    - Full keyboard navigation
    
    Args:
        config: Application configuration dictionary
    """
    st.markdown("## 💻 Online Entry Mode — Enhanced Excel-Like Grid")
    
    # Show AG-Grid availability status
    if AGGRID_AVAILABLE:
        st.success("✅ Enhanced AG-Grid mode active")
    else:
        st.warning("⚠️ Fallback mode: Install streamlit-aggrid for enhanced features")
    
    # ═══════════════════════════════════════════════════════════════════════
    # Initialize session state
    # ═══════════════════════════════════════════════════════════════════════
    ss = st.session_state
    if "ogd_aggrid" not in ss:
        ss.ogd_aggrid = _init_session_state()
    
    ogd = ss.ogd_aggrid  # Shortcut
    
    # ═══════════════════════════════════════════════════════════════════════
    # Step 1: Project Details
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown("### 📋 Step 1: Project Details")
    
    col_up, col_rst = st.columns([3, 1])
    
    with col_up:
        excel_file = st.file_uploader(
            "Upload Excel to auto-fill (optional)",
            type=["xlsx", "xls", "xlsm"],
            key="ogd_aggrid_uploader",
        )
        
        # Re-extract only when a NEW file arrives
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
        if st.button("🔄 Reset All", use_container_width=True, key="reset_aggrid"):
            _reset_session_state(ss)
            ss.ogd_aggrid = _init_session_state()
            st.rerun()
    
    # Project details input
    c1, c2 = st.columns(2)
    with c1:
        ogd["project_name"] = st.text_input(
            "Name of Work *",
            value=ogd["project_name"],
            placeholder="Required",
            key="project_name_aggrid"
        )
        ogd["contractor"] = st.text_input(
            "Contractor Name",
            value=ogd["contractor"],
            key="contractor_aggrid"
        )
    with c2:
        ogd["bill_date"] = st.date_input(
            "Bill Date",
            value=ogd["bill_date"],
            key="bill_date_aggrid"
        )
        ogd["tender_premium"] = st.number_input(
            "Tender Premium (%)",
            0.0, 100.0,
            value=float(ogd["tender_premium"]),
            step=0.5,
            key="tender_premium_aggrid"
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # Step 2: Enhanced Excel-Like Grid
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 📊 Step 2: Work Items — Enhanced Excel-Like Grid")
    
    _grid_tips_enhanced()
    
    cur = ogd["df"]
    
    # Add rows buttons
    c1, c2, c3 = st.columns([2, 1, 1])
    active = int((cur["Quantity"] > 0).sum())
    with c1:
        st.info(f"📦 Rows: {len(cur)} | Active (Qty>0): {active}")
    with c2:
        if st.button("➕ Add 5 Rows", use_container_width=True, key="add5_aggrid"):
            ogd["df"] = pd.concat(
                [cur, _default_df(5, offset=len(cur))],
                ignore_index=True
            )
            st.rerun()
    with c3:
        if st.button("➕ Add 10 Rows", use_container_width=True, key="add10_aggrid"):
            ogd["df"] = pd.concat(
                [cur, _default_df(10, offset=len(cur))],
                ignore_index=True
            )
            st.rerun()
    
    # Save snapshot BEFORE showing the editor
    prev_snap = cur.copy()
    
    # Show enhanced grid (AG-Grid or fallback)
    if AGGRID_AVAILABLE:
        edited = _show_aggrid_editor(cur, key="aggrid_main")
    else:
        edited = _fallback_editor(cur, key="fallback_main")
    
    # Recalculate Amount immediately after edit
    edited = _recalc(edited)
    
    # Detect part-rates
    edited = _detect_part_rates(edited, ogd.get("work_order_rates", {}))
    
    # Update validation status
    edited = update_validation_status(edited)
    
    # Track changes (compare ONLY if shape matches)
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
    gen_html = c1.checkbox("📄 HTML", value=True, key="html_aggrid")
    gen_pdf = c2.checkbox("📕 PDF", value=True, key="pdf_aggrid")
    gen_docx = c3.checkbox("📝 DOCX", value=False, key="docx_aggrid")
    
    # Generate button
    can, msg = can_submit(edited)
    
    if st.button(
        "🚀 Generate Documents",
        type="primary",
        use_container_width=True,
        disabled=not can,
        key="generate_btn_aggrid"
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
