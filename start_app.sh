#!/usr/bin/env bash
# WorkOS local dev — bash/WSL/Linux/macOS
#
# Starts backend (uvicorn :8000) and frontend (vite :3000) from repo root.
# Native Windows: use scripts/start-dev.ps1 instead (idempotent port checks).
#
# Requires: Python 3.11+, Node 20+, pnpm (or npx pnpm@8.10.0)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT/backend"
FRONTEND_DIR="$ROOT/frontend"
DEV_DB="$BACKEND_DIR/dev.db"

export APP_ENV=development
export ENVIRONMENT=development
export DATABASE_URL="sqlite+aiosqlite:///${DEV_DB//\\//}"
export JWT_SECRET_KEY="local-dev-secret-not-for-production"
export DEBUG=true
export ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
export VITE_ENABLE_DEV_AUTH=true

PY="${WORKOS_PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
  PY=python
fi

echo "=== WorkOS dev (bash) ==="
echo "Root:     $ROOT"
echo "Backend:  http://127.0.0.1:8000"
echo "Frontend: http://127.0.0.1:3000"
echo ""

cd "$BACKEND_DIR"
if [ ! -d .venv ]; then
  "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

cleanup() {
  if [ -n "${BACKEND_PID:-}" ]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

cd "$FRONTEND_DIR"
if [ ! -d node_modules ]; then
  if command -v pnpm >/dev/null 2>&1; then
    pnpm install
  else
    npx --yes pnpm@8.10.0 install
  fi
fi

if command -v pnpm >/dev/null 2>&1; then
  exec pnpm run dev --host 127.0.0.1 --port 3000
else
  exec npx --yes pnpm@8.10.0 run dev --host 127.0.0.1 --port 3000
fi
