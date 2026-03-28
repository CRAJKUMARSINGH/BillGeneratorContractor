@echo off
REM Quick deployment fix script for Windows

echo ==========================================
echo Streamlit App Deployment Fix
echo ==========================================
echo.

REM Check if git is available
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo X Git not found. Please install git first.
    exit /b 1
)

echo √ Git found
echo.

REM Show current status
echo Current git status:
git status --short
echo.

REM Add modified files
echo Adding modified files...
git add requirements.txt
git add .streamlit/config.toml
git add core/utils/mobile_optimization.py
git add app_mobile_optimized.py
git add DEPLOYMENT_FIX_GUIDE.md
git add STREAMLIT_DEPLOYMENT_COMPLETE.md

echo √ Files staged
echo.

REM Show what will be committed
echo Files to be committed:
git diff --cached --name-only
echo.

REM Commit
echo Committing changes...
git commit -m "Fix: Add beautifulsoup4 dependency and mobile optimization - Add beautifulsoup4==4.12.3 to requirements.txt - Add lxml==5.3.0 for better HTML parsing - Optimize .streamlit/config.toml for performance - Create mobile optimization utilities - Add mobile-optimized app version - Improve configuration for cloud deployment Fixes #1: No module named 'bs4' error Fixes #2: Sluggish performance on mobile devices"

if %ERRORLEVEL% EQU 0 (
    echo √ Changes committed
    echo.
    
    REM Push to GitHub
    echo Pushing to GitHub...
    git push origin main
    
    if %ERRORLEVEL% EQU 0 (
        echo √ Successfully pushed to GitHub!
        echo.
        echo ==========================================
        echo Deployment initiated!
        echo ==========================================
        echo.
        echo Next steps:
        echo 1. Wait 2-3 minutes for Streamlit Cloud to rebuild
        echo 2. Check https://bill-priyanka-online.streamlit.app
        echo 3. Test on mobile and desktop
        echo 4. Monitor logs for any errors
        echo.
        echo Monitor deployment:
        echo https://share.streamlit.io
        echo.
    ) else (
        echo X Failed to push to GitHub
        echo Please check your git configuration and try again
        exit /b 1
    )
) else (
    echo X Failed to commit changes
    exit /b 1
)

pause
