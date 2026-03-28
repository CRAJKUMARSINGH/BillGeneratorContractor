#!/usr/bin/env python3
"""
BillGenerator Unified - Deployment-Ready Version
Handles missing dependencies and files gracefully
"""
import os
import sys
from pathlib import Path
import streamlit as st

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

# Page config MUST be first Streamlit command
st.set_page_config(
    page_title="BillGenerator Unified",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Error handling wrapper
def safe_import(module_name, fallback=None):
    """Safely import module with fallback"""
    try:
        parts = module_name.split('.')
        module = __import__(module_name)
        for part in parts[1:]:
            module = getattr(module, part)
        return module
    except Exception as e:
        st.error(f"⚠️ Failed to import {module_name}: {str(e)}")
        return fallback

# Try to load configuration
try:
    from core.config.config_loader import ConfigLoader
    config = ConfigLoader.load_from_env('BILL_CONFIG', 'config/v01.json')
except Exception as e:
    st.error(f"⚠️ Configuration error: {str(e)}")
    st.info("Using default configuration...")
    # Create minimal config
    class MinimalConfig:
        app_name = "BillGenerator Unified"
        version = "2.0.0"
        mode = "Standard"
        class features:
            excel_upload = True
            online_entry = True
            batch_processing = True
            advanced_pdf = True
            analytics = False
            @staticmethod
            def is_enabled(name):
                return getattr(MinimalConfig.features, name, False)
        class ui:
            theme = "default"
            show_debug = False
            class branding:
                title = "BillGenerator Unified"
                icon = "📄"
                color = "#00b894"
        class processing:
            max_file_size_mb = 50
            enable_caching = True
            pdf_engine = "reportlab"
            auto_clean_cache = False
    config = MinimalConfig()

# Ensure OUTPUT directory exists
OUTPUT_DIR = Path("OUTPUT")
OUTPUT_DIR.mkdir(exist_ok=True)

# Custom CSS
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .main-header {
        background: linear-gradient(to right, #667eea, #764ba2, #f093fb);
        padding: 2.5rem 2rem;
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
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3rem;
        font-weight: 600;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown(f"""
<div class="main-header">
    <h1>{config.ui.branding.icon} {config.ui.branding.title}</h1>
    <p>✨ Professional Bill Generation System | Version {config.version}</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #00b894 0%, #00cec9 100%); 
                padding: 1.5rem; 
                border-radius: 10px; 
                text-align: center; 
                margin-bottom: 1rem;
                box-shadow: 0 2px 8px rgba(0, 184, 148, 0.3);'>
        <h2 style='color: white; margin: 0; font-size: 1.5rem;'>
            {config.ui.branding.icon} {config.app_name}
        </h2>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    # Mode selection
    modes = ["📊 Excel Upload", "💻 Online Entry", "📥 Download Center", "📖 User Manual"]
    selected_mode = st.radio("Select Mode", modes)
    
    st.markdown("---")
    st.markdown("### ✨ System Status")
    st.success("✅ System Ready")
    st.info(f"📦 Mode: {config.mode}")

# Main content
if "📊 Excel Upload" in selected_mode:
    try:
        from core.ui.excel_mode_fixed import show_excel_mode
        show_excel_mode(config)
    except Exception as e:
        st.error(f"❌ Excel mode error: {str(e)}")
        st.info("Please check that all dependencies are installed correctly.")
        
        # Show basic upload interface as fallback
        st.markdown("### 📊 Excel Upload (Basic Mode)")
        uploaded_file = st.file_uploader("Upload Excel File", type=['xlsx', 'xls'])
        if uploaded_file:
            st.info("File uploaded successfully. Processing functionality requires full installation.")

elif "💻 Online Entry" in selected_mode:
    try:
        from core.ui.online_mode import show_online_mode
        show_online_mode(config)
    except Exception as e:
        st.error(f"❌ Online mode error: {str(e)}")
        st.info("Online entry mode is being loaded...")

elif "📥 Download Center" in selected_mode:
    st.markdown("## 📥 Download Center")
    
    # List files in OUTPUT directory
    output_files = list(OUTPUT_DIR.glob('*'))
    
    if output_files:
        st.success(f"Found {len(output_files)} files")
        for file in sorted(output_files, key=lambda x: x.stat().st_mtime, reverse=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.text(file.name)
            with col2:
                size = file.stat().st_size
                st.text(f"{size/1024:.1f} KB")
            with col3:
                with open(file, 'rb') as f:
                    st.download_button(
                        "📥 Download",
                        f.read(),
                        file.name,
                        key=f"download_{file.name}"
                    )
    else:
        st.info("No files available for download yet.")

elif "📖 User Manual" in selected_mode:
    st.markdown("## 📖 User Manual")
    
    language = st.radio("Select Language", ["🇬🇧 English", "🇮🇳 हिंदी"], horizontal=True)
    
    try:
        manual_file = "USER_MANUAL.md" if "English" in language else "USER_MANUAL_HINDI.md"
        with open(manual_file, "r", encoding="utf-8") as f:
            manual_content = f.read()
        st.markdown(manual_content)
    except FileNotFoundError:
        st.warning("User manual not found. Please contact support.")

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; padding: 2rem; color: #636e72;'>
    <p style='font-size: 1.2rem; font-weight: 700;'>🎯 BillGenerator Unified v{config.version}</p>
    <p>Prepared on Initiative of: <strong>Mrs. Premlata Jain, AAO</strong> | PWD Udaipur</p>
    <p style='font-size: 0.9rem;'>⚡ Powered by Streamlit | 🚀 Production Ready</p>
</div>
""", unsafe_allow_html=True)
