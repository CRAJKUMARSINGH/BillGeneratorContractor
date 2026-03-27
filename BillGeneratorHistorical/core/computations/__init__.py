"""
Computations Package Initialization
Contains bill processing and calculation logic
"""
import os
import sys

# Ensure the root directory is in the Python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

__all__ = ['bill_processor']