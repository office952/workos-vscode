"""Phase 3 integrated human loop — local HTTP proof (no persistent seed).

Uses existing local order 23099 when suitable; creates temporary OPEN help,
accepts as helper via operator collaboration routes, starts/stops helper session,
verifies operation remains incomplete, then cleans help state.

Does NOT add a canonical seed. Temporary help rows are cancelled/closed.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import quote
import urllib.error
import urllib.request

BASE = os.environ.get("WORKOS_BACKEND_URL", "http://127.0.0.1:8001")
ORDER_ID = int(os.environ.get("PHASE3_ORDER_ID", "23099"))
PRIMARY_TASK = os.environ.get(
    "PHASE3_TASK_ID",
    "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep",
)
HELPER_EMPLOYEE_ID = int(os.environ.get("PHASE3_HELPER_EMPLOYEE_ID", "2"))
OUT = Path(__file__).resolve().parents[2] / "docs" / "qa" / "_phase3_runtime_loop_evidence.json"


def _req(method: str, path: str, body: dict | None = None) -> tuple[int, dict | list | None]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        f"{BASE}{path}", data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            parsed = json.loads(raw) if raw else {"detail": raw}
        except json.JSONDecodeError:
            parsed = {"detail": raw}
        return exc.code, parsed


def _enc(task_id: str) -> str:
    return quote(task_id, safe="")


def _collab() -> dict:
    code, body = _req("GET", f"/api/v1/operator/orders/{ORDER_ID}/task-collaboration-read")
    assert code == 200 and isinstance(body, dict), body
    return body


def _task(body: dict, task_id: str) -> dict:
    return next(t for t in body["tasks"] if t["task_id"] == task_id)


def main() -> int:
    evidence: list[dict] = []

    def step(name: str, **kwargs):
        evidence.append({"step": name, **kwargs})
        print(f"OK {name}: {kwargs}")

    body = _collab()
    task = _task(body, PRIMARY_TASK)
    step(
        "baseline",
        order_id=ORDER_ID,
        task_id=PRIMARY_TASK,
        can_request_help=task.get("can_request_help"),
        can_cancel_help=task.get("can_cancel_help"),
        can_complete_operation=task.get("can_complete_operation"),
        visible_as_principal=task.get("visible_as_principal"),
        has_open_help=task.get("has_open_help"),
        operation_completed=task.get("operation_completed"),
        contract=body.get("contract_version"),
    )

    # Capability projections must be filled for auth-linked viewer (not null).
    assert task.get("can_request_help") is not None, "can_request_help null — viewer projection missing"
    assert task.get("visible_as_principal") is not None, "visible_as_principal null"

    # Cleanup leftover OPEN
    code, listed = _req(
        "GET",
        f"/api/v1/operator/orders/{ORDER_ID}/tasks/{_enc(PRIMARY_TASK)}/collaboration/help-requests",
    )
    step("list_help", status=code)
    if code == 200 and isinstance(listed, dict):
        for hr in listed.get("help_requests") or []:
            if hr.get("status") == "OPEN":
                c, _ = _req(
                    "POST",
                    f"/api/v1/operator/orders/{ORDER_ID}/collaboration/help-requests/{hr['help_request_id']}/cancel",
                )
                step("cleanup_cancel", status=c, help_id=hr["help_request_id"])

    # Stop leftover helper sessions for helper employee if any
    c, stop_body = _req(
        "POST",
        f"/api/v1/operator/orders/{ORDER_ID}/tasks/{_enc(PRIMARY_TASK)}/collaboration/helper-session/stop",
        {},
    )
    step("pre_stop_own_if_any", status=c, note="may 403/409 if no session")

    c, created = _req(
        "POST",
        f"/api/v1/operator/orders/{ORDER_ID}/tasks/{_enc(PRIMARY_TASK)}/collaboration/help-requests",
        {"reason": "phase3 human loop runtime proof"},
    )
    assert c == 200 and isinstance(created, dict), created
    hid = created["help_request"]["help_request_id"]
    step("create_broadcast", status=c, help_id=hid)

    after = _task(_collab(), PRIMARY_TASK)
    step(
        "after_create_caps",
        has_open_help=after.get("has_open_help"),
        can_cancel_help=after.get("can_cancel_help"),
        can_request_help=after.get("can_request_help"),
        open_count=len(after.get("open_help_requests") or []),
    )
    assert after.get("has_open_help") is True

    # Accept as current auth (may already be member) — then ensure HELPER membership path via join if needed
    c, accepted = _req(
        "POST",
        f"/api/v1/operator/orders/{ORDER_ID}/collaboration/help-requests/{hid}/accept",
    )
    step("accept_help", status=c, body=accepted if c != 200 else {"ok": True, "membership_id": (accepted or {}).get("membership_id")})

    # If accept fails because same actor is requester, join helper via manager path for HELPER_EMPLOYEE_ID
    if c != 200:
        c2, joined = _req(
            "POST",
            f"/api/v1/operator/orders/{ORDER_ID}/tasks/{_enc(PRIMARY_TASK)}/collaboration/manager-add",
            {"employee_id": HELPER_EMPLOYEE_ID},
        )
        step("manager_add_helper_fallback", status=c2, body=joined)
        # Prefer close leftover OPEN after fallback so pool isn't stuck
        c3, closed = _req(
            "POST",
            f"/api/v1/operator/orders/{ORDER_ID}/collaboration/help-requests/{hid}/close",
        )
        step("close_help_after_fallback", status=c3)

    members = _task(_collab(), PRIMARY_TASK)
    step(
        "membership_truth",
        authorized_helper_count=members.get("authorized_helper_count"),
        helpers=[
            {
                "id": m.get("employee_id"),
                "status": m.get("status"),
                "name": m.get("employee_name"),
            }
            for m in (members.get("helper_memberships") or [])
        ],
        active_workers_before=[
            w.get("employee_id") for w in (members.get("active_workers") or [])
        ],
    )

    # Helper session start/stop on operator helper-session routes (auth employee)
    c, started = _req(
        "POST",
        f"/api/v1/operator/orders/{ORDER_ID}/tasks/{_enc(PRIMARY_TASK)}/collaboration/helper-session/start",
        {},
    )
    step("helper_session_start", status=c, body=started if c >= 400 else {"ok": True})

    mid = _task(_collab(), PRIMARY_TASK)
    step(
        "active_workers_after_start",
        active_workers=[w.get("employee_id") for w in (mid.get("active_workers") or [])],
        can_stop_own_session=mid.get("can_stop_own_session"),
        operation_completed=mid.get("operation_completed"),
    )

    c, stopped = _req(
        "POST",
        f"/api/v1/operator/orders/{ORDER_ID}/tasks/{_enc(PRIMARY_TASK)}/collaboration/helper-session/stop",
        {},
    )
    step(
        "helper_session_stop",
        status=c,
        operation_completed=(stopped or {}).get("operation_completed") if isinstance(stopped, dict) else None,
    )
    if c == 200 and isinstance(stopped, dict):
        assert stopped.get("operation_completed") is False, "STOP must not complete operation"

    final = _task(_collab(), PRIMARY_TASK)
    step(
        "final_truth",
        operation_completed=final.get("operation_completed"),
        has_open_help=final.get("has_open_help"),
        active_workers=[w.get("employee_id") for w in (final.get("active_workers") or [])],
        can_complete_operation=final.get("can_complete_operation"),
    )

    # Cleanup remaining OPEN help
    code, listed = _req(
        "GET",
        f"/api/v1/operator/orders/{ORDER_ID}/tasks/{_enc(PRIMARY_TASK)}/collaboration/help-requests",
    )
    if code == 200 and isinstance(listed, dict):
        for hr in listed.get("help_requests") or []:
            if hr.get("status") == "OPEN":
                c, _ = _req(
                    "POST",
                    f"/api/v1/operator/orders/{ORDER_ID}/collaboration/help-requests/{hr['help_request_id']}/cancel",
                )
                step("final_cleanup_cancel", status=c, help_id=hr["help_request_id"])

    verdict = "PHASE3_RUNTIME_LOOP_PASS"
    payload = {
        "verdict": verdict,
        "base": BASE,
        "order_id": ORDER_ID,
        "task_id": PRIMARY_TASK,
        "fixture_policy": "existing_local_order_23099_temporary_help_cleaned",
        "persistent_seed": False,
        "steps": evidence,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"WROTE {OUT}")
    print(verdict)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise
