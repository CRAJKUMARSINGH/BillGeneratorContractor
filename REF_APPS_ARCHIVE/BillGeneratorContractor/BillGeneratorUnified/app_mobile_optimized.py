#!/usr/bin/env python3
"""
BillGenerator Unified - Mobile Optimized Version
Lightweight version for mobile devices with better performance
"""
import os
import sys
from pathlib import Path
import streamlit as st

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

# Import mobile optimization utilities
from core.utils.mobile_optimization import (
    is_mobile, 
    apply_mobile_css, 
    show_mobile_warning,
    get_max_upload_size,
    should_generate_pdf
)

# Load configuration
from core.config.config_loader import ConfigLoader
config = ConfigLoader.load_from_env('BILL_CONFIG', 'config/v01.json')

# Page config - optimized for mobile
st.set_page_config(
    page_title="Bill Generator",
    page_icon="📱" if is_mobile() else "📊",
    layout="centered" if is_mobile() else "wide",
    initial_sidebar_state="collapsed" if is_mobile() else "expanded"
)

# Apply mobile CSS
apply_mobile_css()

# Show mobile warning
show_mobile_warning()

# Simplified header for mobile
if is_mobile():
    st.title("📱 Bill Generator")
    st.caption("Mobile Optimized Version")
else:
    st.markdown(f"""
    <div class="main-header">
        <h1>{config.ui.branding.icon} {config.ui.branding.title}</h1>
        <p>✨ Professional Bill Generation System | Version {config.version}</p>
    </div>
    """, unsafe_allow_html=True)

# Main content
tab1, tab2 = st.tabs(["📊 Excel Upload", "📖 Help"])

with tab1:
    st.subheader("Upload Excel File")
    
    max_size = get_max_upload_size()
    st.info(f"📁 Maximum file size: {max_size}MB")
    
    uploaded_file = st.file_uploader(
        "Choose Excel file",
        type=['xlsx', 'xlsm'],
        help=f"Upload your bill Excel file (max {max_size}MB)"
    )
    
    if uploaded_file:
        # Check file size
        file_size_mb = uploaded_file.size / (1024 * 1024)
        
        if file_size_mb > max_size:
            st.error(f"❌ File too large: {file_size_mb:.1f}MB. Maximum: {max_size}MB")
            st.stop()
        
        st.success(f"✅ File uploaded: {uploaded_file.name} ({file_size_mb:.1f}MB)")
        
        # Processing options
        col1, col2 = st.columns(2)
        with col1:
            generate_html = st.checkbox("Generate HTML", value=True, disabled=True)
        with col2:
            generate_pdf = should_generate_pdf()
        
        if st.button("🚀 Process File", use_container_width=True):
            with st.spinner("Processing... Please wait"):
                try:
                    # Import processors
                    from core.processors.excel_processor_enterprise import ExcelProcessor
                    from core.generators.html_generator import HTMLGenerator
                    
                    # Process Excel
                    processor = ExcelProcessor(sanitize_strings=True, validate_schemas=False)
                    result = processor.process_file(uploaded_file)
                    
                    if not result.success:
                        st.error("❌ Failed to process Excel file")
                        for error in result.errors:
                            st.error(f"• {error}")
                        st.stop()
                    
                    st.success("✅ Excel processed successfully!")
                    
                    # Generate HTML documents
                    data = {
                        'title_data': {},
                        'work_order_data': result.data.get('Work Order', None),
                        'bill_quantity_data': result.data.get('Bill Quantity', None),
                        'extra_items_data': result.data.get('Extra Items', None),
                        'source_filename': uploaded_file.name
                    }
                    
                    # Extract title data
                    if 'Title' in result.data:
                        title_df = result.data['Title']
                        for index, row in title_df.iterrows():
                            if len(row) >= 2:
                                key = str(row.iloc[0]).strip()
                                value = row.iloc[1]
                                if key:
                                    data['title_data'][key] = value
                    
                    generator = HTMLGenerator(data)
                    html_docs = generator.generate_all_documents()
                    
                    st.success(f"✅ Generated {len(html_docs)} HTML documents")
                    
                    # Download section
                    st.subheader("📥 Download Documents")
                    
                    for doc_name, html_content in html_docs.items():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.text(f"📄 {doc_name}")
                        with col2:
                            st.download_button(
                                "⬇️",
                                html_content,
                                f"{doc_name}.html",
                                "text/html",
                                key=f"download_{doc_name}",
                                use_container_width=True
                            )
                    
                    # PDF generation (optional)
                    if generate_pdf:
                        st.info("📄 PDF generation may take a moment...")
                        try:
                            from core.generators.pdf_generator_fixed import PDFGenerator
                            pdf_gen = PDFGenerator()
                            
                            for doc_name, html_content in html_docs.items():
                                pdf_bytes = pdf_gen.html_to_pdf_bytes(html_content)
                                if pdf_bytes:
                                    col1, col2 = st.columns([3, 1])
                                    with col1:
                                        st.text(f"📑 {doc_name} (PDF)")
                                    with col2:
                                        st.download_button(
                                            "⬇️",
                                            pdf_bytes,
                                            f"{doc_name}.pdf",
                                            "application/pdf",
                                            key=f"download_pdf_{doc_name}",
                                            use_container_width=True
                                        )
                            st.success("✅ PDF documents generated!")
                        except Exception as e:
                            st.warning(f"⚠️ PDF generation failed: {str(e)}")
                            st.info("💡 You can still download HTML documents above")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    with st.expander("Show error details"):
                        st.code(traceback.format_exc())

with tab2:
    st.subheader("📖 How to Use")
    
    st.markdown("""
    ### Steps:
    1. **Upload** your Excel file (.xlsx or .xlsm)
    2. **Choose** generation options
    3. **Click** Process File button
    4. **Download** generated documents
    
    ### File Requirements:
    - Excel format: .xlsx or .xlsm
    - Maximum size: {}MB
    - Must contain: Title, Work Order, Bill Quantity sheets
    
    ### Tips:
    - 📱 On mobile: Disable PDF for faster processing
    - 💾 Keep files under 10MB for best performance
    - 📶 Use stable internet connection
    - 🔄 Refresh page if issues occur
    
    ### Support:
    For questions or issues, refer to USER_MANUAL.md
    """.format(get_max_upload_size()))

# Footer
st.markdown("---")
st.caption(f"""
🎯 Bill Generator v{config.version} | 
Initiative by Mrs. Premlata Jain, AAO, PWD Udaipur
""")
