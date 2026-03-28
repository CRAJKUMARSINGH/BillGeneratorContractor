import streamlit as st
import streamlit.components.v1 as components
from utils.branding import apply_custom_css, show_header
from utils.navigation import create_breadcrumb, create_back_button

# Page configuration
st.set_page_config(
    page_title="Delay Calculator | PWD Tools Hub",
    page_icon="⏱️",
    layout="wide"
)

# Apply branding
apply_custom_css()
create_breadcrumb("Delay Calculator")

def main():
    # Read and display the HTML content at full width
    try:
        with open("static/html/DelayCalculator.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # Display the HTML content centered with wide width
        col_left, col_center, col_right = st.columns([1, 10, 1])
        with col_center:
            components.html(html_content, height=600, scrolling=True, width=1200)
        
    except FileNotFoundError:
        st.error("Tool not available")

# Navigation
create_back_button()

# Run main function
if __name__ == "__main__":
    main()
