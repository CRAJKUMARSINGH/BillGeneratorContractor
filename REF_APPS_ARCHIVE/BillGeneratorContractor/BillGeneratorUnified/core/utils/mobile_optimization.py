"""
Mobile Optimization Utilities
Detect mobile devices and apply optimizations
"""
import streamlit as st

def is_mobile() -> bool:
    """
    Detect if user is on mobile device
    
    Returns:
        bool: True if mobile device detected
    """
    try:
        # Try to get user agent from headers
        if hasattr(st, 'context') and hasattr(st.context, 'headers'):
            user_agent = st.context.headers.get("User-Agent", "").lower()
        else:
            # Fallback: check session state or assume desktop
            return st.session_state.get('is_mobile', False)
        
        # Mobile device keywords
        mobile_keywords = [
            'mobile', 'android', 'iphone', 'ipad', 
            'tablet', 'webos', 'blackberry', 'windows phone'
        ]
        
        return any(keyword in user_agent for keyword in mobile_keywords)
    except:
        # Default to desktop if detection fails
        return False

def apply_mobile_css():
    """Apply mobile-optimized CSS styling"""
    if is_mobile():
        st.markdown("""
        <style>
            /* Mobile-specific optimizations */
            .main .block-container {
                padding: 1rem 0.5rem !important;
                max-width: 100% !important;
            }
            
            /* Buttons */
            .stButton>button {
                width: 100%;
                font-size: 14px;
                padding: 0.75rem 0.5rem;
                margin: 0.25rem 0;
            }
            
            /* File uploader */
            [data-testid="stFileUploader"] {
                font-size: 13px;
                padding: 0.5rem;
            }
            
            [data-testid="stFileUploader"] div:first-child {
                font-size: 14px !important;
                padding: 10px 20px !important;
            }
            
            /* Headers */
            h1 {
                font-size: 1.5rem !important;
            }
            
            h2 {
                font-size: 1.25rem !important;
            }
            
            h3 {
                font-size: 1.1rem !important;
            }
            
            /* Reduce animations for better performance */
            * {
                animation-duration: 0.1s !important;
                transition-duration: 0.1s !important;
            }
            
            /* Sidebar */
            [data-testid="stSidebar"] {
                width: 100% !important;
            }
            
            /* Metrics */
            [data-testid="stMetricValue"] {
                font-size: 1.5rem !important;
            }
            
            /* Tables */
            table {
                font-size: 12px !important;
            }
            
            /* Download buttons */
            .stDownloadButton>button {
                width: 100%;
                font-size: 13px;
            }
            
            /* Info/Warning/Error boxes */
            .stAlert {
                font-size: 13px;
                padding: 0.5rem;
            }
            
            /* Reduce spacing */
            .element-container {
                margin-bottom: 0.5rem !important;
            }
        </style>
        """, unsafe_allow_html=True)

def get_max_upload_size() -> int:
    """
    Get maximum upload size based on device
    
    Returns:
        int: Maximum file size in MB
    """
    return 10 if is_mobile() else 50

def should_generate_pdf() -> bool:
    """
    Determine if PDF generation should be enabled
    
    Returns:
        bool: True if PDF generation recommended
    """
    # Disable PDF generation on mobile by default for performance
    if is_mobile():
        return st.checkbox(
            "Generate PDF (slower on mobile)",
            value=False,
            help="PDF generation may be slow on mobile devices"
        )
    else:
        return st.checkbox(
            "Generate PDF",
            value=True,
            help="Generate PDF documents"
        )

def show_mobile_warning():
    """Show warning message for mobile users"""
    if is_mobile():
        st.info("""
        📱 **Mobile Device Detected**
        
        For best performance:
        - Upload smaller files (< 10MB)
        - PDF generation is optional
        - Use HTML downloads for faster processing
        """)

def optimize_dataframe_display(df, max_rows: int = None):
    """
    Optimize dataframe display for mobile
    
    Args:
        df: DataFrame to display
        max_rows: Maximum rows to show (None for auto)
    """
    if is_mobile():
        # Show fewer rows on mobile
        max_rows = max_rows or 10
        if len(df) > max_rows:
            st.dataframe(df.head(max_rows), use_container_width=True)
            st.caption(f"Showing {max_rows} of {len(df)} rows")
        else:
            st.dataframe(df, use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)
