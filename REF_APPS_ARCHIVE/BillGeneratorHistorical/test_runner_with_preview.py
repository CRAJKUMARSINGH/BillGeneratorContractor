#!/usr/bin/env python3
"""
Test Runner with HTML and PDF Preview
Processes sample files and displays outputs in tabs
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import base64
from datetime import datetime
import tempfile
import os

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import enterprise modules
try:
    from core.excel_processor_enterprise import EnterpriseExcelProcessor, SheetSchema
    ENTERPRISE_EXCEL = True
except ImportError:
    ENTERPRISE_EXCEL = False
    print("⚠️ Enterprise Excel processor not available")

try:
    from core.html_renderer_enterprise import EnterpriseHTMLRenderer, RenderConfig, DocumentType
    ENTERPRISE_HTML = True
except ImportError:
    ENTERPRISE_HTML = False
    print("⚠️ Enterprise HTML renderer not available")

# Fallback imports
try:
    from core.computations.bill_processor import process_bill
    from exports.renderers import generate_html
    LEGACY_PROCESSOR = True
except ImportError:
    LEGACY_PROCESSOR = False
    print("⚠️ Legacy processor not available")

# Page config
st.set_page_config(
    page_title="Test Runner - Bill Generator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 24px;
        background-color: #f0f2f6;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }
    
    iframe {
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🧪 Test Runner with Preview</h1>
    <p>Process sample files and view HTML/PDF outputs in tabs</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🎯 Test Configuration")
    
    # Check available processors
    st.markdown("#### Available Processors")
    if ENTERPRISE_EXCEL:
        st.success("✅ Enterprise Excel Processor")
    else:
        st.warning("⚠️ Enterprise Excel (fallback)")
    
    if ENTERPRISE_HTML:
        st.success("✅ Enterprise HTML Renderer")
    else:
        st.warning("⚠️ Enterprise HTML (fallback)")
    
    if LEGACY_PROCESSOR:
        st.success("✅ Legacy Processor")
    else:
        st.warning("⚠️ Legacy Processor")
    
    st.markdown("---")
    
    # File selection
    test_input_dir = Path("test_input_files")
    if test_input_dir.exists():
        excel_files = list(test_input_dir.glob("*.xlsx"))
        if excel_files:
            st.markdown("#### 📁 Select Test File")
            selected_file = st.selectbox(
                "Choose file:",
                excel_files,
                format_func=lambda x: x.name,
                label_visibility="collapsed"
            )
        else:
            st.error("No Excel files found in test_input_files/")
            st.stop()
    else:
        st.error("test_input_files/ folder not found!")
        st.stop()
    
    st.markdown("---")
    
    # Processing options
    st.markdown("#### ⚙️ Processing Options")
    premium_percent = st.number_input("Premium %", value=5.0, min_value=0.0, max_value=100.0, step=0.1)
    premium_type = st.radio("Premium Type", ["above", "below"], horizontal=True)
    last_bill_amount = st.number_input("Last Bill Amount", value=0.0, min_value=0.0, step=1000.0)
    
    st.markdown("---")
    
    # Process button
    process_button = st.button("🚀 Process File", type="primary", use_container_width=True)

# Main content
if process_button:
    with st.spinner(f"Processing {selected_file.name}..."):
        try:
            # Create output directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("test_outputs") / f"test_run_{timestamp}"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Process with enterprise or legacy processor
            if ENTERPRISE_EXCEL and LEGACY_PROCESSOR:
                # Use enterprise Excel processor for validation
                processor = EnterpriseExcelProcessor(
                    sanitize_strings=True,
                    validate_schemas=True
                )
                
                # Define schemas
                schemas = {
                    "Work Order": SheetSchema(name="Work Order", required=True, min_rows=1),
                    "Bill Quantity": SheetSchema(name="Bill Quantity", required=True, min_rows=1),
                    "Extra Items": SheetSchema(name="Extra Items", required=False, allow_empty=True)
                }
                
                # Validate and process
                result = processor.process_file(selected_file, schemas=schemas)
                
                if not result.success:
                    st.error(f"❌ Validation failed: {', '.join(result.errors)}")
                    st.stop()
                
                st.success(f"✅ Validation passed: {len(result.data)} sheets processed")
                
                # Use legacy processor for bill calculations
                xl_file = pd.ExcelFile(selected_file)
                ws_wo = pd.read_excel(xl_file, "Work Order", header=None)
                ws_bq = pd.read_excel(xl_file, "Bill Quantity", header=None)
                ws_extra = pd.read_excel(xl_file, "Extra Items", header=None)
                
                first_page_data, last_page_data, deviation_data, extra_items_data, note_sheet_data = process_bill(
                    ws_wo, ws_bq, ws_extra, premium_percent, premium_type, last_bill_amount
                )
                
            elif LEGACY_PROCESSOR:
                # Use legacy processor only
                xl_file = pd.ExcelFile(selected_file)
                ws_wo = pd.read_excel(xl_file, "Work Order", header=None)
                ws_bq = pd.read_excel(xl_file, "Bill Quantity", header=None)
                ws_extra = pd.read_excel(xl_file, "Extra Items", header=None)
                
                first_page_data, last_page_data, deviation_data, extra_items_data, note_sheet_data = process_bill(
                    ws_wo, ws_bq, ws_extra, premium_percent, premium_type, last_bill_amount
                )
                
                st.success("✅ Processing complete (legacy mode)")
            else:
                st.error("❌ No processor available!")
                st.stop()
            
            # Generate HTML files
            template_dir = "templates"
            html_files = {}
            
            documents = [
                ("first_page", first_page_data, "First Page"),
                ("deviation_statement", deviation_data, "Deviation Statement"),
                ("extra_items", extra_items_data, "Extra Items"),
                ("note_sheet", note_sheet_data, "Note Sheet"),
            ]
            
            for template_name, data, display_name in documents:
                try:
                    if ENTERPRISE_HTML:
                        # Use enterprise HTML renderer
                        config = RenderConfig(
                            template_dir=template_dir,
                            output_dir=str(output_dir),
                            enable_security_checks=True,
                            pdf_ready=True
                        )
                        renderer = EnterpriseHTMLRenderer(config)
                        
                        result = renderer.render(
                            template_name,
                            data,
                            f"{template_name}.html"
                        )
                        
                        if result.success:
                            html_files[display_name] = result.output_path
                    else:
                        # Use legacy renderer
                        html_path = generate_html(template_name, data, template_dir, str(output_dir))
                        if os.path.exists(html_path):
                            html_files[display_name] = Path(html_path)
                except Exception as e:
                    st.warning(f"⚠️ Could not generate {display_name}: {e}")
            
            st.success(f"✅ Generated {len(html_files)} HTML files")
            
            # Display results
            st.markdown("## 📊 Financial Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Grand Total", f"₹{first_page_data['totals']['grand_total']:,.2f}")
            with col2:
                st.metric("Premium", f"₹{first_page_data['totals']['premium']['amount']:,.2f}")
            with col3:
                st.metric("Payable", f"₹{first_page_data['totals']['payable']:,.2f}")
            
            # Display outputs in tabs
            st.markdown("## 📄 Document Preview")
            
            if html_files:
                # Create tabs for each document
                tab_names = list(html_files.keys())
                tabs = st.tabs(tab_names)
                
                for tab, (doc_name, html_path) in zip(tabs, html_files.items()):
                    with tab:
                        # Read HTML content
                        with open(html_path, 'r', encoding='utf-8') as f:
                            html_content = f.read()
                        
                        # Create sub-tabs for HTML and PDF preview
                        html_tab, pdf_tab, download_tab = st.tabs(["📄 HTML Preview", "📑 PDF Preview", "⬇️ Download"])
                        
                        with html_tab:
                            st.markdown("### HTML Preview")
                            # Display HTML in iframe
                            st.components.v1.html(html_content, height=800, scrolling=True)
                        
                        with pdf_tab:
                            st.markdown("### PDF Preview")
                            
                            # Try to generate PDF
                            try:
                                # Try using wkhtmltopdf or chrome
                                pdf_path = html_path.with_suffix('.pdf')
                                
                                # Try chrome headless first
                                import subprocess
                                chrome_paths = [
                                    'google-chrome',
                                    'chrome',
                                    'chromium',
                                    'chromium-browser',
                                    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                                    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                                ]
                                
                                chrome_cmd = None
                                for cmd in chrome_paths:
                                    try:
                                        result = subprocess.run([cmd, '--version'], capture_output=True, timeout=5)
                                        if result.returncode == 0:
                                            chrome_cmd = cmd
                                            break
                                    except:
                                        continue
                                
                                if chrome_cmd:
                                    # Generate PDF with Chrome
                                    cmd = [
                                        chrome_cmd,
                                        '--headless',
                                        '--disable-gpu',
                                        '--no-margins',
                                        '--disable-smart-shrinking',
                                        '--run-all-compositor-stages-before-draw',
                                        f'--print-to-pdf={pdf_path}',
                                        str(html_path)
                                    ]
                                    
                                    result = subprocess.run(cmd, capture_output=True, timeout=30)
                                    
                                    if result.returncode == 0 and pdf_path.exists():
                                        # Display PDF
                                        with open(pdf_path, 'rb') as f:
                                            pdf_bytes = f.read()
                                        
                                        # Encode PDF for display
                                        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                                        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px" type="application/pdf"></iframe>'
                                        st.markdown(pdf_display, unsafe_allow_html=True)
                                        
                                        st.success(f"✅ PDF generated with Chrome ({len(pdf_bytes)} bytes)")
                                    else:
                                        st.warning("⚠️ Chrome PDF generation failed")
                                        st.info("💡 HTML preview is available in the HTML Preview tab")
                                else:
                                    st.info("ℹ️ Chrome not available for PDF generation")
                                    st.info("💡 HTML preview is available in the HTML Preview tab")
                                    st.info("💡 Download HTML and convert to PDF using your browser's print function")
                                
                            except Exception as e:
                                st.warning(f"⚠️ PDF generation error: {e}")
                                st.info("💡 HTML preview is available in the HTML Preview tab")
                        
                        with download_tab:
                            st.markdown("### Download Options")
                            
                            # Download HTML
                            with open(html_path, 'rb') as f:
                                st.download_button(
                                    label=f"⬇️ Download {doc_name} (HTML)",
                                    data=f.read(),
                                    file_name=html_path.name,
                                    mime="text/html",
                                    use_container_width=True
                                )
                            
                            # Download PDF if available
                            pdf_path = html_path.with_suffix('.pdf')
                            if pdf_path.exists():
                                with open(pdf_path, 'rb') as f:
                                    st.download_button(
                                        label=f"⬇️ Download {doc_name} (PDF)",
                                        data=f.read(),
                                        file_name=pdf_path.name,
                                        mime="application/pdf",
                                        use_container_width=True
                                    )
                            
                            st.info(f"📁 Files saved to: {output_dir}")
            
            st.balloons()
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            with st.expander("Error Details"):
                st.code(traceback.format_exc())

else:
    # Show instructions
    st.info("👈 Select a test file from the sidebar and click 'Process File' to begin")
    
    st.markdown("## 📋 Instructions")
    st.markdown("""
    1. **Select a test file** from the sidebar
    2. **Configure processing options** (premium %, type, last bill amount)
    3. **Click 'Process File'** to generate documents
    4. **View outputs** in tabs:
       - **HTML Preview**: Interactive HTML view
       - **PDF Preview**: PDF rendering (if available)
       - **Download**: Download HTML and PDF files
    
    ### Features
    - ✅ Enterprise-grade Excel validation
    - ✅ Secure HTML rendering
    - ✅ Multiple document types
    - ✅ Interactive preview
    - ✅ PDF generation (Chrome/Chromium)
    - ✅ Download options
    """)
    
    # Show available test files
    test_input_dir = Path("test_input_files")
    if test_input_dir.exists():
        excel_files = list(test_input_dir.glob("*.xlsx"))
        if excel_files:
            st.markdown("### 📁 Available Test Files")
            for i, file in enumerate(excel_files, 1):
                st.write(f"{i}. {file.name}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p><strong>🧪 Test Runner with Preview</strong></p>
    <p>Enterprise-grade bill processing with interactive preview</p>
</div>
""", unsafe_allow_html=True)
