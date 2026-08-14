"""Read-only manager JWT probe against attendance endpoints. No writes."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from jose import jwt

BASE = os.environ.get("WORKOS_API_URL", "http://127.0.0.1:8000")
SECRET = os.environ.get("JWT_SECRET_KEY", "local-dev-secret-not-for-production")
ALG = os.environ.get("JWT_ALGORITHM", "HS256")
READS = [
    "/api/v1/employee-attendance/summary?year=2026&month=8",
    "/api/v1/employee-attendance/events",
    "/api/v1/employee-attendance/effects",
]


def mint(role: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": f"gap-closure-{role}",
            "email": f"{role}@localhost",
            "name": f"Gap {role}",
            "role": role,
            "exp": now + timedelta(minutes=10),
            "iat": now,
            "nbf": now,
        },
        SECRET,
        algorithm=ALG,
    )


def probe(label: str, token: str) -> dict:
    out = {"label": label, "endpoints": []}
    for path in READS:
        req = Request(
            f"{BASE}{path}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
        try:
            with urlopen(req, timeout=12) as res:
                body = res.read()[:240]
                out["endpoints"].append(
                    {"path": path, "status": res.status, "body_prefix": body.decode("utf-8", "replace")}
                )
        except HTTPError as exc:
            body = exc.read()[:400]
            out["endpoints"].append(
                {
                    "path": path,
                    "status": exc.code,
                    "body_prefix": body.decode("utf-8", "replace"),
                }
            )
        except Exception as exc:  # noqa: BLE001 — probe must record transport errors
            out["endpoints"].append({"path": path, "status": None, "error": str(exc)})
    return out


def main() -> int:
    report = {
        "task": "WAVE_5_EVIDENCE_GAP_CLOSURE_V1",
        "mutations": 0,
        "probes": [
            probe("dev_bypass_admin", "__DEV_BYPASS_TOKEN__"),
            probe("minted_manager_jwt", mint("manager")),
            probe("minted_operator_jwt", mint("operator")),
            probe("minted_admin_jwt", mint("admin")),
        ],
    }
    dest = Path(__file__).with_name("manager-attendance-probe.json")
    dest.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "wrote": str(dest),
        "summary": [
            {
                "label": p["label"],
                "statuses": [e.get("status") for e in p["endpoints"]],
            }
            for p in report["probes"]
        ],
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
