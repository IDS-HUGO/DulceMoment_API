#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"
source .venv/bin/activate

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
RELOAD="${RELOAD:-false}"

if [ "$RELOAD" = "true" ]; then
  uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
else
  uvicorn app.main:app --host "$HOST" --port "$PORT"
fi
