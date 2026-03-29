#!/usr/bin/env python3
"""
Simple Test App - Minimal version to test deployment
"""
import streamlit as st
import sys
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

# Page config
st.set_page_config(
    page_title="BillGenerator Test",
    page_icon="📄",
    layout="wide"
)

st.title("🎉 BillGenerator Unified - Test Mode")

st.success("✅ App is running successfully!")

st.write("### System Check")

# Test imports
try:
    import pandas as pd
    st.success("✅ Pandas imported")
except Exception as e:
    st.error(f"❌ Pandas error: {e}")

try:
    import openpyxl
    st.success("✅ OpenPyXL imported")
except Exception as e:
    st.error(f"❌ OpenPyXL error: {e}")

try:
    from core.config.config_loader import ConfigLoader
    config = ConfigLoader.load_from_file('config/v01.json')
    st.success(f"✅ Config loaded: {config.app_name}")
except Exception as e:
    st.error(f"❌ Config error: {e}")

try:
    from core.utils.output_manager import OutputManager
    st.success("✅ Output Manager imported")
except Exception as e:
    st.error(f"❌ Output Manager error: {e}")

st.write("### Test File Upload")
uploaded_file = st.file_uploader("Upload a test Excel file", type=['xlsx'])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.success(f"✅ File read: {len(df)} rows, {len(df.columns)} columns")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")

st.write("---")
st.info("If you see this message, the app is working correctly!")
