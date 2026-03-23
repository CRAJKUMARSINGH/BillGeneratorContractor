#!/usr/bin/env python3
"""
BillGenerator Unified - Enhanced Version
Includes best features from all 5 apps
With automatic cache cleaning and centralized output management
"""
import os
import sys
from pathlib import Path
import streamlit as st
import shutil

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

# Import utilities
from core.utils.cache_cleaner import CacheCleaner
from core.utils.output_manager import get_output_manager

# Clean cache on startup
CacheCleaner.clean_cache(verbose=False)

# Load configuration
from core.config.config_loader import ConfigLoader

# Get config from environment or use default
config = ConfigLoader.load_from_env('BILL_CONFIG', 'config/v01.json')

# Page config
st.set_page_config(
    page_title=config.app_name,
    page_icon=config.ui.branding.icon,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Automatic cache cleaning on startup (optional)
# This can be controlled by configuration or environment variable
auto_clean_env = os.getenv('CLEAN_CACHE_ON_STARTUP', 'false').lower() == 'true'

# Only clean cache once per session to avoid repeated cleaning
if 'cache_cleaned' not in st.session_state:
    st.session_state.cache_cleaned = False

if (auto_clean_env or (config and config.processing.auto_clean_cache)) and not st.session_state.cache_cleaned:
    # Define cache directories to clean
    cache_dirs = [
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache"
    ]
    
    # Define additional patterns to clean
    additional_patterns = [
        "**/__pycache__",  # Recursive py cache directories
        "**/*.pyc",        # Python compiled files
        "**/*.pyo",        # Optimized Python files
        "**/*.pyd",        # Python DLL files
        "**/*.pyz",        # Python zip files
        "**/*.pyx",        # Cython files
        "**/*.so",         # Shared libraries
        "**/*.dll",        # Windows DLL files
        "**/*.dylib"       # macOS dynamic libraries
    ]
    
    cleaned_any = False
    
    # Clean cache directories
    for cache_dir in cache_dirs:
        cache_path = Path(cache_dir)
        if cache_path.exists():
            try:
                if cache_path.is_dir():
                    shutil.rmtree(cache_path)
                else:
                    cache_path.unlink()
                cleaned_any = True
                print(f"Cleaned cache directory: {cache_dir}")
            except Exception as e:
                print(f"Failed to clean {cache_dir}: {e}")
                pass  # Silent fail on startup
    
    # Clean additional patterns
    for pattern in additional_patterns:
        try:
            for file_path in Path(".").glob(pattern):
                if file_path.is_file():
                    file_path.unlink()
                    cleaned_any = True
                    print(f"Cleaned file: {file_path}")
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
                    cleaned_any = True
                    print(f"Cleaned directory: {file_path}")
        except Exception as e:
            print(f"Failed to clean pattern {pattern}: {e}")
            pass  # Silent fail on startup
    
    # Mark cache as cleaned for this session
    if cleaned_any:
        st.session_state.cache_cleaned = True
        print("Cache cleaning completed for this session")
    else:
        print("No cache files found to clean")

# Custom CSS with Beautiful Gradient Styling
st.markdown("""
<style>
    /* Main app background gradient */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .stApp {
        background: linear-gradient(to bottom, #f0f4f8, #e8ecf1);
    }
    
    /* Hide Streamlit branding and default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Hide the default Streamlit header toolbar */
    .stApp > header {display: none;}
    
    /* Hide file uploader details */
    [data-testid="stFileUploaderDeleteBtn"] {display: none;}
    
    /* Hide timestamp in header */
    time {display: none;}
    
    /* Hide footer file path */
    .reportview-container .main footer {visibility: hidden;}
    .reportview-container .main footer:after {
        content:''; 
        visibility: visible;
        display: block;
    }
    
    /* Hide Streamlit deploy button */
    .stDeployButton {display: none;}
    
    /* Hide "Made with Streamlit" */
    footer:after {
        content:''; 
        visibility: visible;
        display: block;
    }
    
    /* Beautiful Gradient Header */
    .main-header {
        background: linear-gradient(to right, #667eea, #764ba2, #f093fb);
        padding: 2.5rem 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
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
    
    /* Metric Cards with Gradient */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Success Banner */
    .success-banner {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
    
    /* Feature Cards */
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Buttons with Gradient */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3rem;
        font-weight: 600;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        background: linear-gradient(135deg, #764ba2 0%, #f093fb 100%);
    }
    
    /* File Upload with Gradient */
    [data-testid="stFileUploader"] {
        border: 2px dashed #667eea !important;
        background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%) !important;
        border-radius: 10px !important;
        padding: 20px !important;
        text-align: center !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid="stFileUploader"]:hover {
        border: 2px dashed #764ba2 !important;
        background: linear-gradient(135deg, #e8ecf1 0%, #d1d8e0 100%) !important;
        box-shadow: 0 0 15px rgba(102, 126, 234, 0.3) !important;
    }
    
    [data-testid="stFileUploader"] div:first-child {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: bold !important;
        font-size: 16px !important;
        box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid="stFileUploader"] div:first-child:hover {
        background: linear-gradient(135deg, #764ba2 0%, #f093fb 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4) !important;
    }
    
    [data-testid="stFileUploader"] div:first-child:active {
        transform: translateY(0) !important;
        box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3) !important;
    }
    
    /* Sidebar Styling with Gradient */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Success/Info boxes with Gradient */
    .stSuccess {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left: 4px solid #667eea;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
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
    modes = ["📊 Excel Upload", "🔄 Hybrid: Upload + Edit", "💻 Online Entry"]
    
    if config.features.is_enabled('batch_processing'):
        modes.append("📦 Batch Processing")
    modes.append("📥 Download Center")
    modes.append("📖 User Manual")
    
    if config.features.is_enabled('analytics'):
        modes.append("📈 Analytics")
    
    selected_mode = st.radio("Select Mode", modes)
    
    st.markdown("---")
    
    # Cache cleaning feature
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
                success_message = f"✅ Cleaned {cleaned_dirs} directories, {cleaned_files} files"
                st.success(success_message)
            else:
                st.info("ℹ️ No cache files found to clean")
        st.info("💡 Cache has been cleaned. Next run will start with a fresh state.")
    
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
        "Analytics": config.features.analytics
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

# Main content
if "📊 Excel Upload" in selected_mode:
    # Use fixed Excel mode with correct template flow
    try:
        from core.ui.excel_mode_fixed import show_excel_mode
        show_excel_mode(config)
    except ImportError:
        st.error("❌ Excel mode not available. Please check installation.")

elif "🔄 Hybrid: Upload + Edit" in selected_mode:
    try:
        from core.ui.hybrid_mode import show_hybrid_mode
        show_hybrid_mode(config)
    except ImportError as e:
        st.error(f"❌ Hybrid mode not available: {str(e)}")

elif "💻 Online Entry" in selected_mode:
    # Feature flag for Excel-like grid (Phase 2)
    use_excel_grid = st.sidebar.checkbox(
        "🆕 Use Excel-Like Grid (Phase 2)",
        value=True,
        help="Enable new Excel-like grid interface with keyboard navigation"
    )
    
    if use_excel_grid:
        try:
            from core.ui.online_mode_grid import show_online_mode_grid
            show_online_mode_grid(config)
        except ImportError as e:
            st.error(f"❌ Excel-like grid mode not available: {str(e)}")
            st.info("Falling back to form-based mode...")
            try:
                from core.ui.online_mode import show_online_mode
                show_online_mode(config)
            except ImportError:
                st.info("💻 Online entry mode coming soon!")
    else:
        try:
            from core.ui.online_mode import show_online_mode
            show_online_mode(config)
        except ImportError:
            st.info("💻 Online entry mode coming soon!")

elif "📦 Batch Processing" in selected_mode:
    # Use fixed batch processor with correct template flow
    try:
        from core.processors.batch_processor_fixed import show_batch_mode
        show_batch_mode(config)
    except ImportError:
        st.error("❌ Batch processing not available. Please check installation.")

elif "📥 Download Center" in selected_mode:
    from core.utils.download_manager import EnhancedDownloadManager
    from core.ui.enhanced_download_center import EnhancedDownloadCenter, create_enhanced_download_center
    
    # Initialize download manager in session state if not exists
    if 'download_manager' not in st.session_state:
        st.session_state.download_manager = EnhancedDownloadManager()
    
    # Create and show download center
    download_center = create_enhanced_download_center(st.session_state.download_manager)
    download_center.render_download_center()

elif "📈 Analytics" in selected_mode:
    st.markdown("## 📈 Analytics Dashboard")
    st.info("Analytics dashboard coming soon!")

elif "📖 User Manual" in selected_mode:
    st.markdown("## 📖 User Manual / उपयोगकर्ता मैनुअल")
    
    # Language selector
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        language = st.radio(
            "Select Language / भाषा चुनें",
            ["🇬🇧 English", "🇮🇳 हिंदी"],
            horizontal=True
        )
    
    st.markdown("---")
    
    # Read and display user manual based on language
    try:
        if "English" in language:
            manual_file = "USER_MANUAL.md"
            download_name = "BillGenerator_User_Manual_English.md"
        else:
            manual_file = "USER_MANUAL_HINDI.md"
            download_name = "BillGenerator_User_Manual_Hindi.md"
        
        with open(manual_file, "r", encoding="utf-8") as f:
            manual_content = f.read()
        
        # Display manual with nice formatting
        st.markdown(manual_content, unsafe_allow_html=True)
        
        # Download button for manual
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.download_button(
                label="📥 Download Manual / मैनुअल डाउनलोड करें",
                data=manual_content,
                file_name=download_name,
                mime="text/markdown",
                help="Download user manual / उपयोगकर्ता मैनुअल डाउनलोड करें"
            )
    except FileNotFoundError:
        st.error("User manual file not found. Please contact support. / उपयोगकर्ता मैनुअल फ़ाइल नहीं मिली। कृपया सहायता से संपर्क करें।")

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
        🎯 BillGenerator Unified v2.0.0
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
            Enhanced PDF Generation • Batch Processing • No-Shrink Fix
        </p>
    </div>
    <div style='margin-top: 1rem;'>
        <p style='color: #b2bec3; font-size: 0.9rem; margin: 0.3rem 0;'>
            ⚡ Powered by Streamlit | 🚀 Production Ready | 📦 Open Source
        </p>
        <p style='color: #b2bec3; font-size: 0.85rem; margin: 0.3rem 0;'>
            <a href='https://github.com/CRAJKUMARSINGH/BillGeneratorUnified' 
               style='color: #00b894; text-decoration: none; font-weight: 600;'
               target='_blank'>
                ⭐ Star on GitHub
            </a>
        </p>
    </div>
</div>
""", unsafe_allow_html=True)