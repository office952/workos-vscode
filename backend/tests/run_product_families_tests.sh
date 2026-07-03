#!/usr/bin/env bash
# Canonical test runner for Product Families Registry tests.
# Uses the project's configured Python interpreter (with sqlalchemy + fastapi + aiosqlite installed).
# Fixes "ModuleNotFoundError: No module named 'sqlalchemy'" when invoked with a wrong interpreter.

set -euo pipefail

# Prefer explicit env var, else fall back to project interpreter, else to PATH 'python'.
PYBIN="${PYBIN:-/opt/python/envs/mgx-chat/bin/python}"
if [ ! -x "$PYBIN" ]; then
  PYBIN="$(command -v python3 || command -v python)"
fi

BACKEND_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "[runner] interpreter : $PYBIN"
echo "[runner] backend dir : $BACKEND_DIR"
echo "[runner] version     : $("$PYBIN" --version 2>&1)"
echo ""

# Verify critical deps BEFORE running tests so failures are unambiguous.
"$PYBIN" - << 'PYCHECK'
import sys
missing = []
for m in ("sqlalchemy", "fastapi", "aiosqlite", "pydantic", "httpx"):
    try:
        __import__(m)
    except ModuleNotFoundError:
        missing.append(m)
if missing:
    sys.stderr.write(
        "[runner] MISSING DEPENDENCIES: "
        + ", ".join(missing)
        + "\n[runner] install with: pip install -r "
        + "requirements.txt\n"
    )
    sys.exit(2)
print("[runner] dependency check OK")
PYCHECK

echo ""
cd "$BACKEND_DIR"
exec "$PYBIN" -m unittest tests.test_product_families_registry -v
