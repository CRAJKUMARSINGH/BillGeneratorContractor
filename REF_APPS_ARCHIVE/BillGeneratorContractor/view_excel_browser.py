import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Work Order Excel Viewer", layout="wide")

st.title("📊 Work Order with Quantities")

# Read Excel file
excel_file = Path("OUTPUT/work_order_with_quantities.xlsx")

if excel_file.exists():
    df = pd.read_excel(excel_file)
    
    st.success(f"✅ Loaded {len(df)} items | Total Quantity: {df['Quantity'].sum():.0f} units")
    
    # Display as table
    st.dataframe(df, width="stretch", height=300)
    
    # Download button
    with open(excel_file, 'rb') as f:
        st.download_button(
            label="📥 Download Excel File",
            data=f,
            file_name="work_order_with_quantities.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    st.divider()
    
    # Show OCR text
    st.subheader("📄 OCR Extracted Text")
    
    text_file = Path("OUTPUT/ocr_extracted_text.txt")
    if text_file.exists():
        with open(text_file, 'r', encoding='utf-8') as f:
            ocr_text = f.read()
        
        with st.expander("Click to view full OCR text", expanded=False):
            st.text_area("OCR Text", ocr_text, height=400, label_visibility="collapsed")
    
else:
    st.error("❌ Excel file not found. Please run create_excel_from_scans.py first.")
