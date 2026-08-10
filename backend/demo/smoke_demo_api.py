"""In-process smoke of demo DB via FastAPI TestClient (no port conflict)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
DEMO_DB = Path(__file__).resolve().parent / "workos_demo.db"
sys.path.insert(0, str(BACKEND))

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("JWT_SECRET_KEY", "local-dev-secret-not-for-production")
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///" + DEMO_DB.resolve().as_posix()

from demo.db_guard import assert_safe_demo_database_url  # noqa: E402

assert_safe_demo_database_url(os.environ["DATABASE_URL"])

from fastapi.testclient import TestClient  # noqa: E402
import main  # noqa: E402

client = TestClient(main.app)
headers = {"Authorization": "Bearer __DEV_BYPASS_TOKEN__"}
paths = [
    "/health",
    "/api/v1/intake-v6/workspaces",
    "/api/v1/intake-v6/workspaces/d0e10001-0000-4000-8000-000000000001",
    "/api/v1/intake-v6/workspaces/d0e10002-0000-4000-8000-000000000002",
    "/api/v1/entities/quotes",
    "/api/v1/entities/quotes/1",
    "/api/v1/entities/orders",
    "/api/v1/entities/orders/1",
    "/api/v1/execution/plan/1",
    "/api/v1/execution/resource-state/machine-runs",
    "/api/v1/profitability-actual/order/1",
]
results = []
for path in paths:
    res = client.get(path, headers=headers)
    results.append({"path": path, "status": res.status_code, "ok": res.status_code < 400})
    print(res.status_code, path)

out = Path(__file__).resolve().parent / "smoke_results.json"
out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
print("wrote", out)
if not all(r["ok"] for r in results):
    raise SystemExit(1)
