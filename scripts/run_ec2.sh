#!/usr/bin/env bash
set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}  DulceMoment API - EC2 Setup & Run${NC}"
echo -e "${BLUE}===============================================${NC}"

PROJECT_DIR="${1:-.}"
cd "$PROJECT_DIR"

echo -e "${YELLOW}[1/4] Pulling latest changes...${NC}"
git pull origin main 2>/dev/null || echo -e "${YELLOW}Warning: No git repo or already up to date${NC}"

echo -e "${YELLOW}[2/4] Installing dependencies...${NC}"
if [ ! -d ".venv" ]; then
  echo -e "${YELLOW}Creating virtual environment...${NC}"
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q

echo -e "${YELLOW}[3/4] Setting up environment file...${NC}"
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo -e "${GREEN}✓ Created .env from .env.example${NC}"
  echo -e "${YELLOW}  - Cloudinary credentials: INCLUDED${NC}"
  echo -e "${YELLOW}  - Update DATABASE_URL if using MySQL${NC}"
else
  echo -e "${GREEN}✓ .env exists - using current configuration${NC}"
fi

echo -e "${YELLOW}[4/4] Verifying Cloudinary configuration...${NC}"
if grep -q "CLOUDINARY_CLOUD_NAME=root" .env; then
  echo -e "${GREEN}✓ Cloudinary is configured and ready${NC}"
else
  echo -e "${RED}⚠ Cloudinary may not be configured${NC}"
  echo -e "${YELLOW}  Make sure these vars are in .env:${NC}"
  echo -e "${YELLOW}    - CLOUDINARY_CLOUD_NAME${NC}"
  echo -e "${YELLOW}    - CLOUDINARY_API_KEY${NC}"
  echo -e "${YELLOW}    - CLOUDINARY_API_SECRET${NC}"
fi

echo ""
echo -e "${GREEN}=== SETUP COMPLETE ===${NC}"
echo ""
echo -e "${BLUE}Ready to run! Starting API...${NC}"
echo ""

# Activate venv and run API
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
