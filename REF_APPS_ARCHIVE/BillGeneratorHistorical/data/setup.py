"""
Setup script for Stream Bill Generator
"""
from setuptools import setup, find_packages

setup(
    name="stream-bill-generator",
    version="1.0.0",
    description="Infrastructure Bill Generator for Government Statutory Formats",
    author="CRAJKUMARSINGH",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.28.0",
        "pandas>=2.0.0",
        "openpyxl>=3.1.0",
        "numpy>=1.24.0",
        "python-docx>=0.8.11",
        "jinja2>=3.1.2",
        "xhtml2pdf>=0.2.11",
        "reportlab>=4.0.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "num2words>=0.5.12",
        "Pillow>=10.0.0"
    ],
    python_requires=">=3.8",
)