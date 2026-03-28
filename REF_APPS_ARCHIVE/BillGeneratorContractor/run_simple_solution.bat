@echo off
echo ========================================
echo 🎯 SIMPLE WORK ORDER PROCESSOR
echo ========================================
echo.
echo This solution reads scanned work orders and creates Excel files.
echo.
echo Choose an option:
echo.
echo 1. Run Simple Script (Command Line)
echo 2. Run Web App (Beautiful Interface)
echo 3. Test with Sample Files
echo 4. Check Dependencies
echo 5. Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto option1
if "%choice%"=="2" goto option2
if "%choice%"=="3" goto option3
if "%choice%"=="4" goto option4
if "%choice%"=="5" goto option5

:option1
echo.
echo Running Simple Script...
echo.
python simple_work_order_processor.py
pause
goto end

:option2
echo.
echo Running Web App...
echo.
echo Open your browser and go to: http://localhost:8501
echo.
streamlit run simple_app.py
pause
goto end

:option3
echo.
echo Testing with Sample Files...
echo.
python simple_work_order_processor.py "INPUT/work_order_samples/work_01_27022026"
echo.
echo ✅ Test complete! Check OUTPUT folder for results.
pause
goto end

:option4
echo.
echo Checking Dependencies...
echo.
python -c "
try:
    import pytesseract
    print('✅ pytesseract - OK')
except:
    print('❌ pytesseract - MISSING')
try:
    import pandas
    print('✅ pandas - OK')
except:
    print('❌ pandas - MISSING')
try:
    from PIL import Image
    print('✅ PIL (Pillow) - OK')
except:
    print('❌ PIL (Pillow) - MISSING')
try:
    import streamlit
    print('✅ streamlit - OK')
except:
    print('❌ streamlit - MISSING')
"
echo.
echo If any dependencies are missing, run:
echo pip install pytesseract pandas pillow streamlit
pause
goto end

:option5
echo.
echo Goodbye! 👋
pause
exit

:end
echo.
echo ========================================
echo Process complete!
echo ========================================
pause