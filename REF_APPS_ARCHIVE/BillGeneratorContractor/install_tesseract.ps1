# Tesseract OCR Installer for Windows
# Automated installation script

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Tesseract OCR Installer" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️  This script should be run as Administrator for best results" -ForegroundColor Yellow
    Write-Host "   Right-click PowerShell and select 'Run as Administrator'`n" -ForegroundColor Yellow
}

# Download URL for Tesseract
$tesseractUrl = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
$installerPath = "$env:TEMP\tesseract-installer.exe"

Write-Host "📥 Downloading Tesseract OCR installer..." -ForegroundColor Green
Write-Host "   URL: $tesseractUrl`n"

try {
    # Download installer
    Invoke-WebRequest -Uri $tesseractUrl -OutFile $installerPath -UseBasicParsing
    Write-Host "✅ Download complete!`n" -ForegroundColor Green
    
    Write-Host "🚀 Starting installation..." -ForegroundColor Green
    Write-Host "   IMPORTANT: During installation:" -ForegroundColor Yellow
    Write-Host "   1. Select 'Additional language data'" -ForegroundColor Yellow
    Write-Host "   2. Check: ✅ English" -ForegroundColor Yellow
    Write-Host "   3. Check: ✅ Hindi (हिन्दी)" -ForegroundColor Yellow
    Write-Host "   4. Install location: C:\Program Files\Tesseract-OCR`n" -ForegroundColor Yellow
    
    # Run installer
    Start-Process -FilePath $installerPath -Wait
    
    Write-Host "`n✅ Installation complete!`n" -ForegroundColor Green
    
    # Add to PATH
    $tesseractPath = "C:\Program Files\Tesseract-OCR"
    
    if (Test-Path $tesseractPath) {
        Write-Host "📝 Adding Tesseract to PATH..." -ForegroundColor Green
        
        # Get current PATH
        $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
        
        if ($currentPath -notlike "*$tesseractPath*") {
            # Add to PATH
            $newPath = "$currentPath;$tesseractPath"
            [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
            
            # Update current session
            $env:Path = "$env:Path;$tesseractPath"
            
            Write-Host "✅ Tesseract added to PATH`n" -ForegroundColor Green
        } else {
            Write-Host "✅ Tesseract already in PATH`n" -ForegroundColor Green
        }
        
        # Verify installation
        Write-Host "🔍 Verifying installation..." -ForegroundColor Green
        $tesseractExe = "$tesseractPath\tesseract.exe"
        
        if (Test-Path $tesseractExe) {
            Write-Host "✅ Tesseract installed successfully!`n" -ForegroundColor Green
            
            # Get version
            $version = & $tesseractExe --version 2>&1 | Select-Object -First 1
            Write-Host "   Version: $version`n" -ForegroundColor Cyan
            
            # Check language packs
            Write-Host "📦 Checking language packs..." -ForegroundColor Green
            $langPath = "$tesseractPath\tessdata"
            
            if (Test-Path "$langPath\eng.traineddata") {
                Write-Host "   ✅ English language pack installed" -ForegroundColor Green
            } else {
                Write-Host "   ⚠️  English language pack missing" -ForegroundColor Yellow
            }
            
            if (Test-Path "$langPath\hin.traineddata") {
                Write-Host "   ✅ Hindi language pack installed" -ForegroundColor Green
            } else {
                Write-Host "   ⚠️  Hindi language pack missing" -ForegroundColor Yellow
                Write-Host "      You may need to reinstall and select Hindi" -ForegroundColor Yellow
            }
            
            Write-Host "`n========================================" -ForegroundColor Cyan
            Write-Host "✅ INSTALLATION SUCCESSFUL!" -ForegroundColor Green
            Write-Host "========================================`n" -ForegroundColor Cyan
            
            Write-Host "Next steps:" -ForegroundColor Yellow
            Write-Host "1. Close and reopen PowerShell/Terminal" -ForegroundColor White
            Write-Host "2. Run: tesseract --version" -ForegroundColor White
            Write-Host "3. Run: python simple_ocr_to_excel.py`n" -ForegroundColor White
            
        } else {
            Write-Host "❌ Installation verification failed" -ForegroundColor Red
            Write-Host "   Tesseract.exe not found at: $tesseractExe`n" -ForegroundColor Red
        }
        
    } else {
        Write-Host "⚠️  Tesseract installation directory not found" -ForegroundColor Yellow
        Write-Host "   Expected location: $tesseractPath" -ForegroundColor Yellow
        Write-Host "   Please check if installation completed successfully`n" -ForegroundColor Yellow
    }
    
    # Cleanup
    if (Test-Path $installerPath) {
        Remove-Item $installerPath -Force
        Write-Host "🧹 Cleaned up installer file`n" -ForegroundColor Green
    }
    
} catch {
    Write-Host "`n❌ Error during installation: $_`n" -ForegroundColor Red
    Write-Host "Manual installation steps:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor White
    Write-Host "2. Run installer and select English + Hindi language packs" -ForegroundColor White
    Write-Host "3. Add C:\Program Files\Tesseract-OCR to PATH`n" -ForegroundColor White
}

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
