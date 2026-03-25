#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"
source .venv/bin/activate

if [ -f "s.env" ]; then
  set -a
  source "s.env"
  set +a
elif [ -f ".env" ]; then
  set -a
  source ".env"
  set +a
fi

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
RELOAD="${RELOAD:-false}"

if [ "$RELOAD" = "true" ]; then
  uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
else
  uvicorn app.main:app --host "$HOST" --port "$PORT"
fi
