#!/bin/bash
# Quick deployment fix script

echo "=========================================="
echo "Streamlit App Deployment Fix"
echo "=========================================="
echo ""

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "❌ Git not found. Please install git first."
    exit 1
fi

echo "✅ Git found"
echo ""

# Show current status
echo "Current git status:"
git status --short
echo ""

# Add modified files
echo "📦 Adding modified files..."
git add requirements.txt
git add .streamlit/config.toml
git add core/utils/mobile_optimization.py
git add app_mobile_optimized.py
git add DEPLOYMENT_FIX_GUIDE.md
git add STREAMLIT_DEPLOYMENT_COMPLETE.md

echo "✅ Files staged"
echo ""

# Show what will be committed
echo "Files to be committed:"
git diff --cached --name-only
echo ""

# Commit
echo "💾 Committing changes..."
git commit -m "Fix: Add beautifulsoup4 dependency and mobile optimization

- Add beautifulsoup4==4.12.3 to requirements.txt
- Add lxml==5.3.0 for better HTML parsing
- Optimize .streamlit/config.toml for performance
- Create mobile optimization utilities
- Add mobile-optimized app version
- Improve configuration for cloud deployment

Fixes #1: No module named 'bs4' error
Fixes #2: Sluggish performance on mobile devices"

if [ $? -eq 0 ]; then
    echo "✅ Changes committed"
    echo ""
    
    # Push to GitHub
    echo "🚀 Pushing to GitHub..."
    git push origin main
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully pushed to GitHub!"
        echo ""
        echo "=========================================="
        echo "Deployment initiated!"
        echo "=========================================="
        echo ""
        echo "Next steps:"
        echo "1. Wait 2-3 minutes for Streamlit Cloud to rebuild"
        echo "2. Check https://bill-priyanka-online.streamlit.app"
        echo "3. Test on mobile and desktop"
        echo "4. Monitor logs for any errors"
        echo ""
        echo "📊 Monitor deployment:"
        echo "https://share.streamlit.io"
        echo ""
    else
        echo "❌ Failed to push to GitHub"
        echo "Please check your git configuration and try again"
        exit 1
    fi
else
    echo "❌ Failed to commit changes"
    exit 1
fi
