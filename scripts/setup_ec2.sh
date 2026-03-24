#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== DulceMoment API - EC2 Setup ===${NC}"

PROJECT_DIR="${1:-$PWD}"
cd "$PROJECT_DIR"

# 1. Update system
echo -e "${YELLOW}[1/5] Updating system...${NC}"
sudo apt update
sudo apt install -y python3 python3-venv python3-pip mysql-server > /dev/null 2>&1

# 2. Setup Python environment
echo -e "${YELLOW}[2/5] Setting up Python environment...${NC}"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

# 3. Create .env if doesn't exist
echo -e "${YELLOW}[3/5] Configuring environment...${NC}"
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo -e "${GREEN}✓ Created .env from .env.example${NC}"
  echo -e "${GREEN}✓ Cloudinary credentials already configured from .env.example${NC}"
else
  echo -e "${GREEN}✓ .env already exists${NC}"
  # Verify Cloudinary is configured
  if ! grep -q "CLOUDINARY_CLOUD_NAME" .env || grep -q "CLOUDINARY_CLOUD_NAME=$" .env; then
    echo -e "${YELLOW}Warning: Cloudinary not configured in .env${NC}"
    echo -e "${YELLOW}Please add Cloudinary credentials manually to .env${NC}"
  else
    echo -e "${GREEN}✓ Cloudinary is configured${NC}"
  fi
fi

# 4. Setup MySQL (if not already done)
echo -e "${YELLOW}[4/5] Configuring MySQL database (if needed)...${NC}"
sudo systemctl start mysql > /dev/null 2>&1 || true

DB_CREATED=$(sudo mysql -u root -e "SHOW DATABASES;" | grep -c "dulcemoment_db" || echo "0")
if [ "$DB_CREATED" -eq "0" ]; then
  echo "Creating MySQL database..."
  sudo mysql -u root << MYSQL_EOF > /dev/null 2>&1
CREATE DATABASE dulcemoment_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'dulcemoment'@'localhost' IDENTIFIED BY 'dulcemoment_password';
GRANT ALL PRIVILEGES ON dulcemoment_db.* TO 'dulcemoment'@'localhost';
FLUSH PRIVILEGES;
MYSQL_EOF
  echo -e "${GREEN}✓ MySQL database created${NC}"
  echo -e "${YELLOW}  User: dulcemoment${NC}"
  echo -e "${YELLOW}  Password: dulcemoment_password${NC}"
  echo -e "${YELLOW}  Database: dulcemoment_db${NC}"
else
  echo -e "${GREEN}✓ MySQL database already exists${NC}"
fi

# 5. Update .env with MySQL connection (if using MySQL)
echo -e "${YELLOW}[5/5] Final setup...${NC}"
if grep -q "sqlite" .env; then
  read -p "Do you want to use MySQL instead of SQLite? (y/n) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    sed -i 's|DATABASE_URL=sqlite:///.*|DATABASE_URL=mysql+pymysql://dulcemoment:dulcemoment_password@localhost:3306/dulcemoment_db|' .env
    echo -e "${GREEN}✓ Updated .env to use MySQL${NC}"
  fi
fi

echo -e "${GREEN}=== Setup completed! ===${NC}"
echo -e "${YELLOW}To start the API, run:${NC}"
echo -e "${GREEN}bash scripts/run_api.sh${NC}"
echo ""
echo -e "${YELLOW}=== Image Service (Cloudinary) ===${NC}"
if grep -q "CLOUDINARY_CLOUD_NAME=root" .env; then
  echo -e "${GREEN}✓ Cloudinary is configured in .env${NC}"
  echo -e "${YELLOW}  Cloud: $(grep CLOUDINARY_CLOUD_NAME .env | cut -d'=' -f2)${NC}"
  echo -e "${YELLOW}  API Key: $(grep CLOUDINARY_API_KEY .env | cut -d'=' -f2)${NC}"
  echo -e "${GREEN}Images can be uploaded via POST /api/v1/media/cloudinary/upload-url${NC}"
else
  echo -e "${RED}✗ Cloudinary NOT configured${NC}"
  echo -e "${YELLOW}Update .env with your Cloudinary credentials:${NC}"
  echo -e "${YELLOW}  CLOUDINARY_CLOUD_NAME=your_cloud_name${NC}"
  echo -e "${YELLOW}  CLOUDINARY_API_KEY=your_api_key${NC}"
  echo -e "${YELLOW}  CLOUDINARY_API_SECRET=your_api_secret${NC}"
fi
