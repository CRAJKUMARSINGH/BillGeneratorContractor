#!/bin/bash
# Streamlit Cloud Deployment Helper Script

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Streamlit Cloud Deployment Helper                     ║"
echo "║     BillGenerator Historical                               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Run verification
echo -e "${BLUE}Step 1: Running deployment verification...${NC}"
python verify_deployment.py

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Verification failed. Please fix issues before deploying.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Verification passed!${NC}"
echo ""

# Step 2: Check git status
echo -e "${BLUE}Step 2: Checking git status...${NC}"
if [ -d .git ]; then
    echo -e "${GREEN}✅ Git repository found${NC}"
    
    # Check for uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}⚠️  You have uncommitted changes:${NC}"
        git status --short
        echo ""
        read -p "Do you want to commit these changes? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            read -p "Enter commit message: " commit_msg
            git add .
            git commit -m "$commit_msg"
            echo -e "${GREEN}✅ Changes committed${NC}"
        else
            echo -e "${YELLOW}⚠️  Proceeding without committing changes${NC}"
        fi
    else
        echo -e "${GREEN}✅ No uncommitted changes${NC}"
    fi
    
    # Check remote
    if git remote -v | grep -q origin; then
        echo -e "${GREEN}✅ Remote repository configured${NC}"
        
        # Offer to push
        echo ""
        read -p "Do you want to push to remote? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git push origin main || git push origin master
            echo -e "${GREEN}✅ Pushed to remote${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  No remote repository configured${NC}"
        echo "   Add remote: git remote add origin <your-repo-url>"
    fi
else
    echo -e "${RED}❌ Not a git repository${NC}"
    echo "   Initialize: git init"
    exit 1
fi

# Step 3: Deployment instructions
echo ""
echo -e "${BLUE}Step 3: Deploy to Streamlit Cloud${NC}"
echo ""
echo "Next steps:"
echo "1. Go to: https://share.streamlit.io/"
echo "2. Sign in with GitHub"
echo "3. Click 'New app'"
echo "4. Select your repository"
echo "5. Set main file: app.py"
echo "6. Click 'Deploy!'"
echo ""
echo -e "${GREEN}📖 For detailed instructions, see: STREAMLIT_CLOUD_DEPLOYMENT.md${NC}"
echo ""

# Step 4: Open browser (optional)
read -p "Open Streamlit Cloud in browser? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v xdg-open > /dev/null; then
        xdg-open "https://share.streamlit.io/"
    elif command -v open > /dev/null; then
        open "https://share.streamlit.io/"
    elif command -v start > /dev/null; then
        start "https://share.streamlit.io/"
    else
        echo "Please open: https://share.streamlit.io/"
    fi
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              🚀 Ready for Deployment! 🚀                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
