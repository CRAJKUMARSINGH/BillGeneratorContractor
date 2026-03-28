@echo off
REM Excel Viewer - Always uses correct virtual environment
cd /d "%~dp0"
echo Starting Excel Viewer...
echo Using: %CD%\.venv\Scripts\python.exe
.venv\Scripts\python.exe -m streamlit run view_excel_browser.py --server.port 8505
pause
