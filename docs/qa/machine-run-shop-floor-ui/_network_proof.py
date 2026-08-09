"""Network command proof against isolated :8010 — never QA."""
from __future__ import annotations

import json
import sqlite3
import uuid
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = "http://127.0.0.1:8010/api/v1/execution/resource-state/machine-runs"
OUT = Path(__file__).resolve().parent / "network_proof.json"
DB = Path(__file__).resolve().parent / "_isolated_s67_ui.db"
FACE_A = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_a"
FACE_B = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_b"


def req(method: str, url: str, body: dict | None = None):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"} if body else {}
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw
        return exc.code, parsed


def ensure_plans() -> None:
    conn = sqlite3.connect(DB)
    have = {
        r[0]
        for r in conn.execute("select id from execution_plan where id in (31,32)").fetchall()
    }

    def task(tid: str) -> dict:
        return {
            "task_id": tid,
            "source_operation_code": "face_cnc_cut",
            "resource_mode": "MACHINE_BOUND",
            "machine_capability_code": "CNC_ROUTER_CUTTING",
            "batch_eligible": True,
            "assigned_employee_id": None,
        }

    for pid, oid, tk in ((31, 880761, FACE_A), (32, 880762, FACE_B)):
        if pid in have:
            continue
        conn.execute(
            "INSERT INTO execution_plan "
            "(id, order_id, order_code, snapshot_version, tasks_json, "
            "total_estimated_time_minutes, created_at, updated_at) "
            "VALUES (?,?,?,1,?,0.0,'2026-08-09 10:00:00','2026-08-09 10:00:00')",
            (
                pid,
                oid,
                str(oid),
                json.dumps(
                    {"source": "order_snapshot_v2", "operational_tasks": [task(tk)]}
                ),
            ),
        )
    conn.commit()
    conn.close()


def main() -> None:
    ensure_plans()
    proof: dict = {"base": BASE, "steps": []}
    start = datetime(2026, 8, 10, 8, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=2)
    status, created = req(
        "POST",
        BASE,
        {
            "machine_id": 1,
            "reservation_start": start.isoformat().replace("+00:00", "Z"),
            "reservation_end": end.isoformat().replace("+00:00", "Z"),
            "timezone": "Europe/Bucharest",
            "participants": [
                {"execution_plan_id": 31, "task_key": FACE_A},
                {"execution_plan_id": 32, "task_key": FACE_B},
            ],
            "idempotency_key": str(uuid.uuid4()),
            "reason_code": "network_proof_create",
        },
    )
    proof["steps"].append(
        {
            "op": "CREATE",
            "http": status,
            "id": created.get("machine_run_id") if isinstance(created, dict) else None,
            "body": created,
        }
    )
    if status >= 400:
        OUT.write_text(json.dumps(proof, indent=2), encoding="utf-8")
        print(json.dumps(proof, indent=2))
        raise SystemExit(1)

    rid = created["machine_run_id"]
    ver = created["version"]
    status, detail = req("GET", f"{BASE}/{rid}")
    proof["steps"].append(
        {
            "op": "GET_DETAIL",
            "http": status,
            "version": detail.get("version"),
            "status": detail.get("status"),
        }
    )

    for op, path in [
        ("CONFIRM", "confirm"),
        ("START", "start"),
        ("COMPLETE", "complete"),
        ("RELEASE", "release"),
    ]:
        sent_version = ver
        status, body = req(
            "POST",
            f"{BASE}/{rid}/{path}",
            {
                "expected_version": ver,
                "idempotency_key": str(uuid.uuid4()),
                "reason_code": f"network_proof_{path}",
            },
        )
        proof["steps"].append(
            {
                "op": op,
                "http": status,
                "expected_version_sent": sent_version,
                "version": body.get("version") if isinstance(body, dict) else None,
                "status": body.get("status") if isinstance(body, dict) else None,
                "reservation_status": body.get("reservation_status")
                if isinstance(body, dict)
                else None,
                "body": body,
            }
        )
        if status >= 400:
            break
        ver = body["version"]
        status, detail = req("GET", f"{BASE}/{rid}")
        proof["steps"].append(
            {
                "op": "GET_DETAIL_REFETCH",
                "after": op,
                "http": status,
                "version": detail.get("version"),
                "status": detail.get("status"),
            }
        )

    status, listing = req("GET", f"{BASE}?open_only=true")
    proof["steps"].append(
        {"op": "GET_LIST_OPEN", "http": status, "count": listing.get("count")}
    )
    OUT.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()
