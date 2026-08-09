"""Network proof for CREATE/ADD/by-task against isolated :8010 — never QA."""
from __future__ import annotations

import json
import uuid
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = "http://127.0.0.1:8010/api/v1/execution/resource-state/machine-runs"
OUT = Path(__file__).resolve().parent / "network_proof.json"
FACE_C = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_c"
FACE_D = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_d"
FACE_E = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_e"


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


def main() -> None:
    proof: dict = {"base": BASE, "steps": [], "lookup": {}}
    # CREATE candidates
    st, cand = req("GET", f"{BASE}/candidates?machine_id=1")
    proof["steps"].append({"op": "GET_candidates", "status": st, "count": cand.get("count") if isinstance(cand, dict) else None})

    start = datetime(2026, 8, 11, 8, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=2)
    st, created = req(
        "POST",
        BASE,
        {
            "machine_id": 1,
            "reservation_start": start.isoformat().replace("+00:00", "Z"),
            "reservation_end": end.isoformat().replace("+00:00", "Z"),
            "timezone": "Europe/Bucharest",
            "participants": [
                {"execution_plan_id": 27, "task_key": FACE_C},
                {"execution_plan_id": 28, "task_key": FACE_D},
            ],
            "expected_version": 0,
            "idempotency_key": str(uuid.uuid4()),
            "reason_code": "closure_network_create",
        },
    )
    proof["steps"].append({"op": "POST_create", "status": st, "body": created})
    rid = created["machine_run_id"] if isinstance(created, dict) else None
    if rid:
        st, detail = req("GET", f"{BASE}/{rid}")
        proof["steps"].append({"op": "GET_created_detail", "status": st, "version": detail.get("version") if isinstance(detail, dict) else None})

    # ADD on pre-seeded HELD (id=1)
    st, add_cand = req("GET", f"{BASE}/1/candidate-participants")
    proof["steps"].append(
        {
            "op": "GET_candidate_participants",
            "status": st,
            "mutation_allowed": add_cand.get("mutation_allowed") if isinstance(add_cand, dict) else None,
            "count": add_cand.get("count") if isinstance(add_cand, dict) else None,
        }
    )
    st, held = req("GET", f"{BASE}/1")
    ver = held.get("version") if isinstance(held, dict) else 1
    st, added = req(
        "POST",
        f"{BASE}/1/add-participant",
        {
            "expected_version": ver,
            "execution_plan_id": 23,
            "task_key": FACE_C,
            "idempotency_key": str(uuid.uuid4()),
            "reason_code": "closure_network_add",
        },
    )
    proof["steps"].append({"op": "POST_add_participant", "status": st, "body": added})
    st, refreshed = req("GET", f"{BASE}/1")
    proof["steps"].append(
        {
            "op": "GET_refreshed_detail",
            "status": st,
            "active": refreshed.get("active_participant_count") if isinstance(refreshed, dict) else None,
        }
    )

    # by-task for RUNNING chip plan 25
    st, by_task = req(
        "GET",
        f"{BASE}/by-task?execution_plan_id=25&task_key={FACE_A}",
    )
    proof["lookup"]["running_chip"] = {"status": st, "membership": by_task}

    # terminal absence — no RELEASED in this seed; probe non-member
    st, none = req(
        "GET",
        f"{BASE}/by-task?execution_plan_id=29&task_key={FACE_E}",
    )
    proof["lookup"]["no_active"] = {"status": st, "membership": none}

    OUT.write_text(json.dumps(proof, indent=2, default=str), encoding="utf-8")
    print(json.dumps(proof, indent=2, default=str))


if __name__ == "__main__":
    main()
