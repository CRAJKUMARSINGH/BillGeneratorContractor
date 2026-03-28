"""
App Package Initialization
Ensures proper module resolution for Streamlit Cloud deployment
"""
import os
import sys

# Get paths
APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(APP_DIR)

# Add root directory to Python path
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Add app directory to Python path
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

__all__ = ['main']