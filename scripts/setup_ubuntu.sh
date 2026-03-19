#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-$PWD}"

sudo apt update
sudo apt install -y python3 python3-venv python3-pip

cd "$PROJECT_DIR"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
fi

echo "Setup completado. Edita .env si necesitas credenciales reales."
