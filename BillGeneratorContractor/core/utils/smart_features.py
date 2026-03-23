"""
Smart Features Module
Best features from SmartBillFlow
"""
import streamlit as st
from datetime import datetime
import pandas as pd

class SmartFeatures:
    """Smart features and enhancements"""
    
    @staticmethod
    def smart_file_naming(project_name: str, document_type: str) -> str:
        """Generate smart file names"""
        # Clean project name
        clean_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_'))
        clean_name = clean_name.replace(' ', '_')
        
        # Add timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Generate name
        filename = f"{clean_name}_{document_type}_{timestamp}.html"
        return filename
    
    @staticmethod
    def validate_excel_structure(df: pd.DataFrame, required_columns: list) -> tuple:
        """Validate Excel file structure"""
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return False, f"Missing columns: {', '.join(missing_columns)}"
        
        return True, "Structure valid"
    
    @staticmethod
    def smart_progress_indicator(current: int, total: int, message: str = "Processing"):
        """Show smart progress indicator"""
        progress = current / total if total > 0 else 0
        st.progress(progress)
        st.text(f"{message}... {current}/{total} ({progress*100:.1f}%)")
    
    @staticmethod
    def smart_error_message(error: Exception, context: str = ""):
        """Display smart error messages with solutions"""
        error_solutions = {
            'FileNotFoundError': 'Check if the file path is correct and file exists',
            'PermissionError': 'Check if you have permission to access the file',
            'KeyError': 'Check if all required columns are present in Excel',
            'ValueError': 'Check if data types are correct',
        }
        
        error_type = type(error).__name__
        solution = error_solutions.get(error_type, 'Please check your input and try again')
        
        st.error(f"❌ Error: {str(error)}")
        if context:
            st.info(f"📍 Context: {context}")
        st.info(f"💡 Solution: {solution}")
    
    @staticmethod
    def smart_defaults(field_name: str):
        """Provide smart default values"""
        defaults = {
            'tender_premium': 4.0,
            'gst_rate': 18.0,
            'retention_percentage': 5.0,
            'mobilization_advance': 10.0
        }
        return defaults.get(field_name, None)
    
    @staticmethod
    def analytics_placeholder():
        """Analytics dashboard placeholder"""
        st.markdown("## 📈 Analytics Dashboard")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Bills", "156", "+12")
        with col2:
            st.metric("Total Amount", "₹45.2L", "+8.3%")
        with col3:
            st.metric("Avg Processing Time", "3.2s", "-0.5s")
        with col4:
            st.metric("Success Rate", "98.5%", "+1.2%")
        
        st.info("📊 Full analytics dashboard coming soon!")

def show_smart_analytics(config):
    """Show analytics with smart features"""
    SmartFeatures.analytics_placeholder()
