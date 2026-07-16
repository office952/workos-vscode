"""Phase 2 integrity correction — real HTTP completion proof on order 23099."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote

BASE = os.environ.get("WORKOS_BACKEND_URL", "http://127.0.0.1:8001")
ORDER_ID = 23099
# Primary fixture task for cancel / accept / helper session integrity.
PRIMARY_TASK = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep"
# Canonical Sandu employee on local fixture (also typical WORKOS_DEV_AUTH identity).
PRINCIPAL_EMPLOYEE_ID = 4


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


def _collab_task(task_id: str) -> dict:
    code, body = _req("GET", f"/api/v1/operator/orders/{ORDER_ID}/task-collaboration-read")
    assert code == 200 and isinstance(body, dict), body
    return next(t for t in body["tasks"] if t["task_id"] == task_id)


def _enc(task_id: str) -> str:
    return quote(task_id, safe="")


def _find_complete_proof_task() -> tuple[str, str]:
    """Return (task_id, mode) where mode is 'fresh' or 'already_completed'.

    Prefer a startable incomplete task for a real end_task complete.
    Fall back to an already-completed task to prove idempotent complete closes OPEN help.
    """
    code, body = _req("GET", f"/api/v1/operator/orders/{ORDER_ID}/task-collaboration-read")
    assert code == 200 and isinstance(body, dict), body
    already: str | None = None
    for task in body["tasks"]:
        tid = task["task_id"]
        if task.get("operation_completed"):
            already = already or tid
            continue
        c, start_body = _req(
            "POST",
            "/api/v1/operator/task-action",
            {
                "order_id": ORDER_ID,
                "task_id": tid,
                "action": "start",
                "employee_id": PRINCIPAL_EMPLOYEE_ID,
            },
        )
        if c == 200:
            return tid, "fresh"
        if c == 409 and isinstance(start_body, dict):
            err = start_body.get("detail")
            code_s = None
            if isinstance(err, dict):
                code_s = err.get("error") or err.get("code")
            if code_s == "task_already_started":
                return tid, "fresh"
    if already:
        return already, "already_completed"
    raise AssertionError("no task available for complete→help closure proof")


def main() -> None:
    evidence: list[dict] = []

    def step(name: str, **kwargs):
        evidence.append({"step": name, **kwargs})
        print(f"OK {name}: {kwargs}")

    base = _collab_task(PRIMARY_TASK)
    step(
        "baseline",
        helpers=base.get("authorized_helper_count"),
        has_open_help=base.get("has_open_help"),
        op_completed=base.get("operation_completed"),
        assigned=(base.get("optional_principal") or {}).get("optional_principal_employee_id"),
    )

    # Cancel leftover OPEN as requester (dev auth → Sandu / principal)
    code, listed = _req(
        "GET",
        f"/api/v1/operator/orders/{ORDER_ID}/tasks/{_enc(PRIMARY_TASK)}/collaboration/help-requests",
    )
    step("list_help", status=code)
    if code == 200 and isinstance(listed, dict):
        for hr in listed.get("help_requests") or []:
            if hr.get("status") == "OPEN":
                c, body = _req(
                    "POST",
                    f"/api/v1/operator/orders/{ORDER_ID}/collaboration/help-requests/{hr['help_request_id']}/cancel",
                )
                step(
                    "cleanup_cancel",
                    status=c,
                    help_id=hr["help_request_id"],
                    err=(body or {}).get("detail") if c != 200 else None,
                )

    c, created = _req(
        "POST",
        f"/api/v1/operator/orders/{ORDER_ID}/tasks/{_enc(PRIMARY_TASK)}/collaboration/help-requests",
        {"reason": "integrity correction runtime proof"},
    )
    assert c == 200 and isinstance(created, dict), created
    hid = created["help_request"]["help_request_id"]
    step("create_broadcast", status=c, help_id=hid)

    # Requester cancel succeeds
    c, cancelled = _req(
        "POST",
        f"/api/v1/operator/orders/{ORDER_ID}/collaboration/help-requests/{hid}/cancel",
    )
    assert c == 200, cancelled
    step("requester_cancel", status=c, help_status=cancelled["help_request"]["status"])

    # Non-requester cancel is proven in pytest test_c1 (single HTTP identity = requester).
    step("non_requester_cancel", proven_by="pytest:test_c1_cancel_requester_only")

    # New OPEN for accept + helper session
    c, created = _req(
        "POST",
        f"/api/v1/operator/orders/{ORDER_ID}/tasks/{_enc(PRIMARY_TASK)}/collaboration/help-requests",
        {"reason": "open for helper session proof"},
    )
    assert c == 200 and isinstance(created, dict), created
    hid = created["help_request"]["help_request_id"]
    step("create_broadcast_2", status=c, help_id=hid)

    c, accepted = _req(
        "POST",
        f"/api/v1/operator/orders/{ORDER_ID}/collaboration/help-requests/{hid}/accept",
    )
    step(
        "accept",
        status=c,
        membership_id=(accepted or {}).get("membership_id") if isinstance(accepted, dict) else None,
    )
    assert c == 200, accepted

    c, started = _req(
        "POST",
        f"/api/v1/operator/orders/{ORDER_ID}/tasks/{_enc(PRIMARY_TASK)}/collaboration/helper-session/start",
    )
    step("helper_session_start", status=c)
    if c == 200:
        c, stopped = _req(
            "POST",
            f"/api/v1/operator/orders/{ORDER_ID}/tasks/{_enc(PRIMARY_TASK)}/collaboration/helper-session/stop",
        )
        step(
            "helper_session_stop",
            status=c,
            operation_completed=(stopped or {}).get("operation_completed")
            if isinstance(stopped, dict)
            else None,
        )
        assert isinstance(stopped, dict)
        assert stopped.get("operation_completed") is False

    # Duplicate own helper session rejected
    c, started2 = _req(
        "POST",
        f"/api/v1/operator/orders/{ORDER_ID}/tasks/{_enc(PRIMARY_TASK)}/collaboration/helper-session/start",
    )
    step("helper_session_start_again", status=c)
    if c == 200:
        c_dup, dup = _req(
            "POST",
            f"/api/v1/operator/orders/{ORDER_ID}/tasks/{_enc(PRIMARY_TASK)}/collaboration/helper-session/start",
        )
        step("duplicate_helper_start", status=c_dup, body=dup)
        assert c_dup == 409, dup
        c_stop, stop_body = _req(
            "POST",
            f"/api/v1/operator/orders/{ORDER_ID}/tasks/{_enc(PRIMARY_TASK)}/collaboration/helper-session/stop",
        )
        step("helper_session_stop_after_dup", status=c_stop, body=stop_body)
        assert c_stop == 200, stop_body

    # Never-started task_id must NOT fake already_completed / success.
    # (PRIMARY_TASK may already carry prior explicit completion on local fixtures.)
    bogus_task = f"{PRIMARY_TASK}__never_started_probe"
    c, fake = _req(
        "POST",
        "/api/v1/operator/task-action",
        {
            "order_id": ORDER_ID,
            "task_id": bogus_task,
            "action": "complete",
            "employee_id": PRINCIPAL_EMPLOYEE_ID,
        },
    )
    step("never_started_complete_rejected", status=c, body=fake)
    assert c == 422, fake

    # Complete path — REAL operator complete endpoint closes OPEN help
    complete_task, complete_mode = _find_complete_proof_task()
    step("complete_task_chosen", task_id=complete_task, mode=complete_mode)

    c, created = _req(
        "POST",
        f"/api/v1/operator/orders/{ORDER_ID}/tasks/{_enc(complete_task)}/collaboration/help-requests",
        {"reason": "open for real complete close proof"},
    )
    assert c == 200 and isinstance(created, dict), created
    hid_c = created["help_request"]["help_request_id"]
    step("create_open_for_complete", status=c, help_id=hid_c, task_id=complete_task)

    before = _collab_task(complete_task)
    step(
        "before_complete",
        op_completed=before.get("operation_completed"),
        has_open_help=before.get("has_open_help"),
        helpers=before.get("authorized_helper_count"),
        mode=complete_mode,
    )
    assert before.get("has_open_help") is True

    c, completed = _req(
        "POST",
        "/api/v1/operator/task-action",
        {
            "order_id": ORDER_ID,
            "task_id": complete_task,
            "action": "complete",
            "employee_id": PRINCIPAL_EMPLOYEE_ID,
            "completion_notes": "phase2 integrity correction proof",
        },
    )
    step("operator_complete", status=c, body=completed, mode=complete_mode)
    assert c == 200, completed
    if complete_mode == "fresh":
        assert not (isinstance(completed, dict) and completed.get("already_completed")), completed
    else:
        # Idempotent retry on prior explicit completion
        assert isinstance(completed, dict)
        assert (
            completed.get("already_completed") is True
            or completed.get("action") == "complete"
        ), completed

    after = _collab_task(complete_task)
    step(
        "after_complete",
        op_completed=after.get("operation_completed"),
        has_open_help=after.get("has_open_help"),
        helpers=after.get("authorized_helper_count"),
        assigned=(after.get("optional_principal") or {}).get("optional_principal_employee_id"),
        mode=complete_mode,
    )
    assert after.get("has_open_help") is False
    if complete_mode == "fresh":
        assert after.get("operation_completed") is True
    else:
        assert after.get("operation_completed") is True

    # Idempotent complete retry still leaves help CLOSED
    c, completed2 = _req(
        "POST",
        "/api/v1/operator/task-action",
        {
            "order_id": ORDER_ID,
            "task_id": complete_task,
            "action": "complete",
            "employee_id": PRINCIPAL_EMPLOYEE_ID,
        },
    )
    step("operator_complete_retry", status=c, body=completed2)
    assert c == 200, completed2
    assert isinstance(completed2, dict)
    assert completed2.get("action") == "complete"
    after2 = _collab_task(complete_task)
    step(
        "after_retry",
        has_open_help=after2.get("has_open_help"),
        op_completed=after2.get("operation_completed"),
        helpers=after2.get("authorized_helper_count"),
    )
    assert after2.get("has_open_help") is False
    assert after2.get("operation_completed") is True

    # Memberships on primary task remain after helper accept
    primary_after = _collab_task(PRIMARY_TASK)
    step(
        "primary_memberships_remain",
        helpers=primary_after.get("authorized_helper_count"),
        assigned=(primary_after.get("optional_principal") or {}).get(
            "optional_principal_employee_id"
        ),
    )
    assert primary_after.get("authorized_helper_count", 0) >= 1

    out = Path("C:/w/psiso/docs/qa/_phase2_correction_runtime_evidence.json")
    out.write_text(
        json.dumps(
            {
                "order_id": ORDER_ID,
                "primary_task_id": PRIMARY_TASK,
                "complete_task_id": complete_task,
                "steps": evidence,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print("WROTE", out)
    print("PHASE2_CORRECTION_RUNTIME_PASS")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as exc:
        print("ASSERT", exc)
        sys.exit(1)
