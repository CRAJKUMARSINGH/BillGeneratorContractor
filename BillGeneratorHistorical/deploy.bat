@echo off
REM Streamlit Cloud Deployment Helper Script for Windows

echo ================================================================
echo      Streamlit Cloud Deployment Helper
echo      BillGenerator Historical
echo ================================================================
echo.

REM Step 1: Run verification
echo Step 1: Running deployment verification...
python verify_deployment.py

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Verification failed. Please fix issues before deploying.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Verification passed!
echo.

REM Step 2: Check git status
echo Step 2: Checking git status...
if exist .git (
    echo [SUCCESS] Git repository found
    
    REM Check for uncommitted changes
    git status --porcelain > nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        git status --short
        echo.
        set /p commit_choice="Do you want to commit these changes? (y/n): "
        if /i "%commit_choice%"=="y" (
            set /p commit_msg="Enter commit message: "
            git add .
            git commit -m "%commit_msg%"
            echo [SUCCESS] Changes committed
        ) else (
            echo [WARNING] Proceeding without committing changes
        )
    ) else (
        echo [SUCCESS] No uncommitted changes
    )
    
    REM Check remote
    git remote -v | findstr origin > nul
    if %ERRORLEVEL% EQU 0 (
        echo [SUCCESS] Remote repository configured
        
        REM Offer to push
        echo.
        set /p push_choice="Do you want to push to remote? (y/n): "
        if /i "%push_choice%"=="y" (
            git push origin main
            if %ERRORLEVEL% NEQ 0 (
                git push origin master
            )
            echo [SUCCESS] Pushed to remote
        )
    ) else (
        echo [WARNING] No remote repository configured
        echo    Add remote: git remote add origin ^<your-repo-url^>
    )
) else (
    echo [ERROR] Not a git repository
    echo    Initialize: git init
    pause
    exit /b 1
)

REM Step 3: Deployment instructions
echo.
echo Step 3: Deploy to Streamlit Cloud
echo.
echo Next steps:
echo 1. Go to: https://share.streamlit.io/
echo 2. Sign in with GitHub
echo 3. Click 'New app'
echo 4. Select your repository
echo 5. Set main file: app.py
echo 6. Click 'Deploy!'
echo.
echo [INFO] For detailed instructions, see: STREAMLIT_CLOUD_DEPLOYMENT.md
echo.

REM Step 4: Open browser (optional)
set /p browser_choice="Open Streamlit Cloud in browser? (y/n): "
if /i "%browser_choice%"=="y" (
    start https://share.streamlit.io/
)

echo.
echo ================================================================
echo               Ready for Deployment!
echo ================================================================
echo.
pause
