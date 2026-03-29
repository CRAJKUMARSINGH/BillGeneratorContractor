# Simple Work Order Processor Launcher
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🎯 SIMPLE WORK ORDER PROCESSOR" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This solution reads scanned work orders and creates Excel files." -ForegroundColor Gray
Write-Host ""

Write-Host "Choose an option:" -ForegroundColor White
Write-Host ""
Write-Host "1. Run Simple Script (Command Line)" -ForegroundColor Green
Write-Host "2. Run Web App (Beautiful Interface)" -ForegroundColor Green
Write-Host "3. Test with Sample Files" -ForegroundColor Green
Write-Host "4. Check Dependencies" -ForegroundColor Green
Write-Host "5. Exit" -ForegroundColor Red
Write-Host ""

$choice = Read-Host "Enter your choice (1-5)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Running Simple Script..." -ForegroundColor Yellow
        Write-Host ""
        python simple_work_order_processor.py
        break
    }
    "2" {
        Write-Host ""
        Write-Host "Running Web App..." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Open your browser and go to: http://localhost:8501" -ForegroundColor Cyan
        Write-Host ""
        streamlit run simple_app.py
        break
    }
    "3" {
        Write-Host ""
        Write-Host "Testing with Sample Files..." -ForegroundColor Yellow
        Write-Host ""
        python simple_work_order_processor.py "INPUT/work_order_samples/work_01_27022026"
        Write-Host ""
        Write-Host "✅ Test complete! Check OUTPUT folder for results." -ForegroundColor Green
        break
    }
    "4" {
        Write-Host ""
        Write-Host "Checking Dependencies..." -ForegroundColor Yellow
        Write-Host ""
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
        Write-Host ""
        Write-Host "If any dependencies are missing, run:" -ForegroundColor Yellow
        Write-Host "pip install pytesseract pandas pillow streamlit" -ForegroundColor Cyan
        break
    }
    "5" {
        Write-Host ""
        Write-Host "Goodbye! 👋" -ForegroundColor Cyan
        break
    }
    default {
        Write-Host "Invalid choice. Please run the script again." -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Process complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to continue..."