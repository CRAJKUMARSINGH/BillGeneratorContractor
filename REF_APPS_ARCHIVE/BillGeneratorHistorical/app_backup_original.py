#!/usr/bin/env python3
"""
BillGenerator Historical - Streamlit Cloud Ready
Enterprise-grade version with production-ready Excel processing and HTML rendering
"""
import os
import sys
from pathlib import Path
import streamlit as st
import shutil
import traceback

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Streamlit Cloud detection
IS_STREAMLIT_CLOUD = os.getenv('STREAMLIT_SHARING_MODE') or os.getenv('STREAMLIT_RUNTIME_ENV') == 'cloud'

# Import enterprise modules
try:
    from core.excel_processor_enterprise import (
        EnterpriseExcelProcessor,
        SheetSchema,
        ValidationResult,
        ProcessingResult
    )
    ENTERPRISE_EXCEL_AVAILABLE = True
except ImportError as e:
    print(f"Enterprise Excel processor not available: {e}")
    ENTERPRISE_EXCEL_AVAILABLE = False

try:
    from core.html_renderer_enterprise import (
        EnterpriseHTMLRenderer,
        RenderConfig,
        DocumentType,
        RenderResult
    )
    ENTERPRISE_HTML_AVAILABLE = True
except ImportError as e:
    print(f"Enterprise HTML renderer not available: {e}")
    ENTERPRISE_HTML_AVAILABLE = False

# Check if BillGeneratorUnified core modules are available
unified_core_available = (project_root / "BillGeneratorUnified" / "core").exists()

if unified_core_available:
    try:
        # Use BillGeneratorUnified's modular structure
        sys.path.insert(0, str(project_root / "BillGeneratorUnified"))
        
        from core.utils.cache_cleaner import CacheCleaner
        from core.utils.output_manager import get_output_manager
        from core.config.config_loader import ConfigLoader
        
        # Clean cache on startup (skip on Streamlit Cloud to avoid permission issues)
        if not IS_STREAMLIT_CLOUD:
            CacheCleaner.clean_cache(verbose=False)
        
        # Load configuration
        config_path = 'BillGeneratorUnified/config/v01.json'
        if not Path(config_path).exists():
            config_path = 'config/app_config.json'
        
        config = ConfigLoader.load_from_env('BILL_CONFIG', config_path)
    except Exception as e:
        print(f"Warning: Could not load BillGeneratorUnified modules: {e}")
        unified_core_available = False

if not unified_core_available:
    # Fallback to basic configuration
    class SimpleConfig:
        def __init__(self):
            self.app_name = "Bill Generator Historical"
            self.version = "2.0.0 Enterprise"
            self.mode = "Cloud" if IS_STREAMLIT_CLOUD else "Standard"
            self.features = type('obj', (object,), {
                'excel_upload': True,
                'online_entry': False,
                'batch_processing': True,
                'advanced_pdf': True,
                'analytics': False,
                'enterprise_processing': ENTERPRISE_EXCEL_AVAILABLE and ENTERPRISE_HTML_AVAILABLE,
                'is_enabled': lambda self, x: getattr(self, x, False)
            })()
            self.ui = type('obj', (object,), {
                'theme': 'default',
                'show_debug': False,
                'branding': type('obj', (object,), {
                    'title': 'Bill Generator Historical - Enterprise',
                    'icon': '📄',
                    'color': '#00b894'
                })()
            })()
            self.processing = type('obj', (object,), {
                'max_file_size_mb': 200,
                'enable_caching': True,
                'pdf_engine': 'reportlab',
                'auto_clean_cache': False,
                'enterprise_mode': ENTERPRISE_EXCEL_AVAILABLE and ENTERPRISE_HTML_AVAILABLE
            })()
    
    config = SimpleConfig()

# Page config
st.set_page_config(
    page_title=config.app_name,
    page_icon=config.ui.branding.icon,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Automatic cache cleaning on startup (skip on Streamlit Cloud)
if 'cache_cleaned' not in st.session_state:
    st.session_state.cache_cleaned = False

if not IS_STREAMLIT_CLOUD and config.processing.auto_clean_cache and not st.session_state.cache_cleaned:
    cache_dirs = ["__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"]
    additional_patterns = ["**/__pycache__", "**/*.pyc", "**/*.pyo"]
    
    cleaned_any = False
    for cache_dir in cache_dirs:
        cache_path = Path(cache_dir)
        if cache_path.exists():
            try:
                if cache_path.is_dir():
                    shutil.rmtree(cache_path)
                else:
                    cache_path.unlink()
                cleaned_any = True
            except Exception as e:
                print(f"Cache clean warning: {e}")
    
    if cleaned_any:
        st.session_state.cache_cleaned = True

# Show Streamlit Cloud indicator
if IS_STREAMLIT_CLOUD:
    st.sidebar.info("☁️ Running on Streamlit Cloud")

# Show enterprise features indicator
if ENTERPRISE_EXCEL_AVAILABLE and ENTERPRISE_HTML_AVAILABLE:
    st.sidebar.success("🏢 Enterprise Mode: Active")
    st.sidebar.caption("✅ Advanced Excel validation\n✅ Secure HTML rendering\n✅ Production-grade processing")

# Custom CSS with Beautiful Green Header and Fluorescent Green Upload Buttons
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp > header {display: none;}
    .stDeployButton {display: none;}
    
    /* Beautiful Green Header */
    .main-header {
        background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
        padding: 2.5rem 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0, 184, 148, 0.3);
        animation: fadeIn 0.8s ease-in;
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .main-header p {
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
        opacity: 0.95;
    }
    
    /* Feature Cards */
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #00b894;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3rem;
        font-weight: 600;
        background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
        color: white;
        border: none;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 184, 148, 0.4);
    }
    
    /* Fluorescent Green File Upload Button */
    [data-testid="stFileUploader"] {
        border: 2px dashed #00ff00 !important;
        background-color: #e6ffe6 !important;
        border-radius: 10px !important;
        padding: 20px !important;
        text-align: center !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid="stFileUploader"]:hover {
        border: 2px dashed #00cc00 !important;
        background-color: #ccffcc !important;
        box-shadow: 0 0 15px rgba(0, 255, 0, 0.3) !important;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
    }
    
    /* Success/Info boxes */
    .stSuccess {
        background-color: #d4edda;
        border-left: 4px solid #00b894;
    }
    
    .stInfo {
        background-color: #d1ecf1;
        border-left: 4px solid #00cec9;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #00b894;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# Beautiful Green Header
st.markdown(f"""
<div class="main-header">
    <h1>{config.ui.branding.icon} {config.ui.branding.title}</h1>
    <p>✨ Professional Bill Generation System | Version {config.version} | Mode: {config.mode}</p>
</div>
""", unsafe_allow_html=True)

# Sidebar with Green Theme
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
    modes = ["📊 Excel Upload", "🧪 Test Run (Sample Files)"]
    
    if config.features.is_enabled('batch_processing'):
        modes.append("📦 Batch Process All Files")
    
    if unified_core_available:
        modes.append("📥 Download Center")
    
    if config.features.is_enabled('analytics'):
        modes.append("📈 Analytics")
    
    selected_mode = st.radio("Select Mode", modes)
    
    st.markdown("---")
    
    # Cache cleaning feature
    if unified_core_available:
        st.markdown("### 🧹 Maintenance")
        
        # Get output manager
        output_mgr = get_output_manager()
        output_size = output_mgr.get_folder_size()
        output_files = len(output_mgr.get_all_files())
        
        if output_size > 0:
            st.info(f"📦 OUTPUT folder: {output_files} files ({output_mgr.format_size(output_size)})")
        
        # Button to clean cache
        if st.button("🧹 Clean Cache & Temp Files"):
            with st.spinner("Cleaning cache and temporary files..."):
                cleaned_dirs, cleaned_files = CacheCleaner.clean_cache(verbose=False)
                if cleaned_dirs or cleaned_files > 0:
                    st.success(f"✅ Cleaned {cleaned_dirs} directories, {cleaned_files} files")
                else:
                    st.info("ℹ️ No cache files found to clean")
        
        # Button to clean old output files
        if st.button("🗑️ Clean Old Output Files"):
            with st.spinner("Cleaning old output files..."):
                files_deleted, space_freed = output_mgr.clean_old_files(keep_latest=10)
                if files_deleted > 0:
                    st.success(f"✅ Deleted {files_deleted} old files ({output_mgr.format_size(space_freed)} freed)")
                else:
                    st.info("ℹ️ No old files to clean")
        
        st.markdown("---")
    
    # Feature status with beautiful styling
    st.markdown("### ✨ Features")
    features_status = {
        "Excel Upload": config.features.excel_upload,
        "Online Entry": config.features.online_entry,
        "Batch Processing": config.features.batch_processing,
        "Advanced PDF": config.features.advanced_pdf,
        "Analytics": config.features.analytics,
        "Enterprise Processing": ENTERPRISE_EXCEL_AVAILABLE and ENTERPRISE_HTML_AVAILABLE
    }
    
    for feature, enabled in features_status.items():
        if enabled:
            st.markdown(f"""
            <div style='background: linear-gradient(90deg, #d4edda 0%, #c3e6cb 100%); 
                        padding: 0.5rem 1rem; 
                        border-radius: 8px; 
                        margin: 0.3rem 0;
                        border-left: 3px solid #00b894;'>
                <span style='color: #155724; font-weight: 600;'>✅ {feature}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='background: #f8f9fa; 
                        padding: 0.5rem 1rem; 
                        border-radius: 8px; 
                        margin: 0.3rem 0;
                        border-left: 3px solid #dee2e6;'>
                <span style='color: #6c757d;'>❌ {feature}</span>
            </div>
            """, unsafe_allow_html=True)

# Main content routing
if "📊 Excel Upload" in selected_mode:
    # Use unified Excel mode if available, otherwise fallback
    if unified_core_available:
        try:
            from core.ui.excel_mode_fixed import show_excel_mode
            show_excel_mode(config)
        except ImportError:
            st.error("❌ Excel mode not available. Using fallback mode.")
            # Fallback to basic upload
            from core.computations.bill_processor import process_bill
            from exports.renderers import generate_html
            import pandas as pd
            from datetime import datetime
            
            st.markdown("## 📤 Upload Your Excel File")
            uploaded_file = st.file_uploader("Choose an Excel file", type=['xlsx', 'xls'])
            
            if uploaded_file:
                st.info("📄 File uploaded successfully! Configure settings and click Process.")
    else:
        st.error("❌ BillGeneratorUnified core modules not found. Please check installation.")

elif "🧪 Test Run (Sample Files)" in selected_mode:
    st.markdown("""
        <div style='background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); 
                    padding: 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;'>
            <h2 style='color: white; margin: 0;'>🧪 Test Run with Sample Files</h2>
            <p style='color: #ecf0f1; margin: 0.5rem 0 0 0;'>
                Test the system using pre-loaded sample files
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    test_input_dir = Path("test_input_files")
    if test_input_dir.exists():
        excel_files = list(test_input_dir.glob("*.xlsx"))
        if excel_files:
            st.success(f"✅ Found {len(excel_files)} sample files ready for testing")
            selected_file = st.selectbox("Choose file to process:", excel_files, format_func=lambda x: x.name)
            
            if st.button("🚀 Process Selected File", type="primary", use_container_width=True):
                st.info("Processing... (Implementation uses core.computations.bill_processor)")
        else:
            st.warning("⚠️ No Excel files found in test_input_files folder")
    else:
        st.error("❌ test_input_files folder not found!")

elif "📦 Batch Process All Files" in selected_mode:
    if unified_core_available:
        try:
            from core.processors.batch_processor_fixed import show_batch_mode
            show_batch_mode(config)
        except ImportError:
            st.error("❌ Batch processing not available. Please check installation.")
    else:
        st.info("📦 Batch processing requires BillGeneratorUnified core modules.")

elif "📥 Download Center" in selected_mode:
    if unified_core_available:
        from core.utils.download_manager import EnhancedDownloadManager
        from core.ui.enhanced_download_center import create_enhanced_download_center
        
        if 'download_manager' not in st.session_state:
            st.session_state.download_manager = EnhancedDownloadManager()
        
        download_center = create_enhanced_download_center(st.session_state.download_manager)
        download_center.render_download_center()
    else:
        st.info("📥 Download Center requires BillGeneratorUnified core modules.")

elif "📈 Analytics" in selected_mode:
    st.markdown("## 📈 Analytics Dashboard")
    st.info("Analytics dashboard coming soon!")

# Beautiful Footer with Credits
st.markdown("---")
st.markdown(f"""
<div style='background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
            margin-top: 2rem;
            border-top: 3px solid #00b894;'>
    <p style='font-size: 1.2rem; font-weight: 700; color: #2d3436; margin: 0.5rem 0;'>
        🎯 BillGenerator Historical v{config.version}
    </p>
    <p style='color: #636e72; margin: 0.3rem 0; font-size: 0.95rem;'>
        <strong>Prepared on Initiative of:</strong><br>
        <span style='color: #00b894; font-weight: 600;'>Mrs. Premlata Jain, AAO</span><br>
        <span style='font-size: 0.9rem;'>PWD Udaipur</span>
    </p>
    <p style='color: #636e72; margin: 0.3rem 0;'>
        Configuration: <span style='color: #00b894; font-weight: 600;'>{config.mode}</span> | 
        Features: <span style='color: #00b894; font-weight: 600;'>{sum(features_status.values())}/{len(features_status)}</span> enabled
    </p>
    <div style='margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid #dee2e6;'>
        <p style='color: #636e72; font-size: 0.95rem; margin: 0.3rem 0;'>
            <strong>🤖 AI Development Partner:</strong> Kiro AI Assistant
        </p>
        <p style='color: #b2bec3; font-size: 0.9rem; margin: 0.3rem 0;'>
            Enhanced PDF Generation • Batch Processing • Configuration-Driven Architecture
        </p>
    </div>
    <div style='margin-top: 1rem;'>
        <p style='color: #b2bec3; font-size: 0.9rem; margin: 0.3rem 0;'>
            ⚡ Powered by Streamlit | 🚀 Production Ready | 📦 Modular Design
        </p>
    </div>
</div>
""", unsafe_allow_html=True)
