"""Build 1 — Same-scenario Letters continuous walk (live :8001).

Starts from known disposable IR/workspace/quote/snapshot (not order 23099),
then accept → convert → plan-v2 → reality → post-job.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8001"
WS = "80570a4a-a806-4305-a39c-b34a72092694"
QUOTE_ID = 1
OUT = Path(__file__).resolve().parent / "lineage_evidence.json"
HEADERS = {
    "Authorization": "Bearer __DEV_BYPASS_TOKEN__",
    "Origin": "http://127.0.0.1:3000",
}


def _step(ev: dict, name: str, resp: httpx.Response) -> dict:
    body: dict | list | str | None
    try:
        body = resp.json()
    except Exception:
        body = resp.text[:2000]
    entry = {"step": name, "status": resp.status_code, "ok": 200 <= resp.status_code < 300, "body": body}
    ev["steps"].append(entry)
    print(f"[{resp.status_code}] {name}")
    return body if isinstance(body, dict) else {}


def main() -> int:
    evidence: dict = {
        "label": "LOCAL LIVE STACK SAME-SCENARIO BUILD1",
        "base": BASE,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "fixture_policy": "controlled_clone_continue — IR/workspace/quote/snapshot from wave disposable; new order via convert; not order 23099",
        "gates": {"G1": "letters_root", "G2": "full_commercial", "G3": "controlled_stock", "G4": "strict_lineage"},
        "steps": [],
        "ids": {},
    }

    with httpx.Client(base_url=BASE, headers=HEADERS, timeout=120.0) as client:
        ws = _step(evidence, "get_workspace", client.get(f"/api/v1/intake-v6/workspaces/{WS}"))
        evidence["ids"]["workspace_id"] = WS
        evidence["ids"]["intake_request_code"] = (ws.get("payload") or {}).get("intake_request_code")
        evidence["ids"]["workspace_code"] = ws.get("workspace_code")
        evidence["ids"]["template_code"] = ws.get("template_code")
        evidence["ids"]["readiness_status"] = ws.get("readiness_status")

        spine = _step(
            evidence,
            "commercial_spine_state",
            client.get(f"/api/v1/intake-v6/workspaces/{WS}/commercial-spine-state"),
        )
        evidence["ids"]["quote_id"] = spine.get("quote_id") or QUOTE_ID
        snap = (spine.get("snapshot_v2") or {})
        evidence["ids"]["snapshot_code"] = snap.get("snapshot_code")
        evidence["ids"]["snapshot_frozen_total_gross"] = (
            (spine.get("snapshot_authoritative_offer") or {}).get("written_total_gross")
        )
        quote_id = evidence["ids"]["quote_id"]

        if not snap.get("exists"):
            evidence["stop"] = "MISSING_SNAPSHOT_V2"
            OUT.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
            return 2

        # Pricing review
        _step(
            evidence,
            "complete_pricing_review",
            client.post(
                f"/api/v1/intake-v6/quotes/{quote_id}/complete-pricing-review",
                json={
                    "expected_quote_id": int(quote_id),
                    "pricing_review_reason": "Build1 same-scenario pricing review",
                    "reviewer_confirmation": True,
                    "confirm_quote_stays_draft": True,
                    "confirm_no_order": True,
                    "confirm_no_execution": True,
                    "confirm_no_inventory": True,
                    "pricing_method": "quote_priced_review",
                },
            ),
        )

        owner_codes = (spine.get("snapshot_authoritative_offer") or {}).get("owner_decision_codes") or []
        _step(
            evidence,
            "owner_approval",
            client.post(
                f"/api/v1/intake-v6/quotes/{quote_id}/owner-approval",
                json={
                    "expected_quote_id": int(quote_id),
                    "decision_reason": "Build1 same-scenario owner approval",
                    "acknowledged_no_execution_tasks": True,
                    "acknowledged_no_stock_consumption": True,
                    "acknowledged_warnings": [],
                    "acknowledged_blockers": list(owner_codes),
                },
            ),
        )

        accept = _step(
            evidence,
            "accept",
            client.post(
                f"/api/v1/intake-v6/quotes/{quote_id}/accept",
                json={
                    "accept_reason": "Build1 same-scenario accept snapshot v2 quote",
                    "reviewer_confirmation": True,
                    "confirm_pricing_review_completed": True,
                    "confirm_no_order": True,
                    "confirm_no_execution": True,
                    "confirm_no_inventory": True,
                    "confirm_convert_separate": True,
                    "confirm_owner_decisions_acknowledged": True,
                },
            ),
        )
        if not evidence["steps"][-1]["ok"]:
            evidence["stop"] = "ACCEPT_FAILED"
            OUT.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
            return 3

        convert = _step(
            evidence,
            "convert_to_order",
            client.post(
                f"/api/v1/intake-v6/quotes/{quote_id}/convert-to-order",
                json={
                    "convert_reason": "Build1 same-scenario convert accepted snapshot",
                    "reviewer_confirmation": True,
                    "confirm_quote_accepted": True,
                    "confirm_pricing_review_completed": True,
                    "confirm_create_order_only": True,
                    "confirm_no_execution_plan": True,
                    "confirm_no_execution_tasks": True,
                    "confirm_no_inventory": True,
                    "confirm_production_separate": True,
                },
            ),
        )
        if not evidence["steps"][-1]["ok"]:
            evidence["stop"] = "CONVERT_FAILED"
            OUT.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
            return 4

        order_id = (
            convert.get("order_id")
            or convert.get("id")
            or (convert.get("order") or {}).get("id")
            or (convert.get("order") or {}).get("order_id")
        )
        evidence["ids"]["order_id"] = order_id
        evidence["ids"]["order_code"] = convert.get("order_code") or (convert.get("order") or {}).get("code")
        if evidence["ids"]["order_id"] == 23099:
            evidence["stop"] = "STITCH_REJECTED_ORDER_23099"
            OUT.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
            return 5

        # Plan V2
        _step(evidence, "plan_v2_preview", client.post(f"/api/v1/execution/plan-v2/preview/{order_id}"))
        persist = _step(
            evidence, "plan_v2_persist", client.post(f"/api/v1/execution/plan-v2/from-order/{order_id}")
        )
        mat = _step(
            evidence,
            "plan_v2_materialize",
            client.post(f"/api/v1/execution/plan-v2/materialize-tasks/{order_id}"),
        )

        release = _step(
            evidence,
            "production_release_status",
            client.get(f"/api/v1/execution/orders/{order_id}/production-release-status"),
        )
        # Resolve owner decisions if listed
        codes = []
        if isinstance(release, dict):
            codes = release.get("blocking_owner_decision_codes") or release.get("owner_decision_codes") or []
            if not codes and isinstance(release.get("blockers"), list):
                codes = [b.get("code") for b in release["blockers"] if isinstance(b, dict) and b.get("code")]
        for code in codes:
            _step(
                evidence,
                f"resolve_owner_decision:{code}",
                client.post(
                    f"/api/v1/execution/orders/{order_id}/owner-decisions/{code}/resolve",
                    json={"status": "accepted", "note": "Build1 same-scenario resolve"},
                ),
            )

        # Pick a task
        tasks = []
        if isinstance(mat, dict):
            tasks = mat.get("tasks") or mat.get("materialized_tasks") or []
        if not tasks and isinstance(persist, dict):
            tasks = persist.get("tasks") or []
        task_id = None
        if tasks and isinstance(tasks[0], dict):
            task_id = tasks[0].get("task_id") or tasks[0].get("id") or tasks[0].get("key")
        if not task_id:
            # list tasks endpoint fallback
            listed = _step(
                evidence,
                "list_execution_tasks",
                client.get(f"/api/v1/execution/orders/{order_id}/tasks"),
            )
            arr = listed.get("tasks") or listed.get("items") or []
            if arr and isinstance(arr[0], dict):
                task_id = arr[0].get("task_id") or arr[0].get("id")
        evidence["ids"]["task_id"] = task_id

        if task_id:
            ts = datetime.now(timezone.utc).isoformat()
            _step(
                evidence,
                "reality_start_task",
                client.post(
                    "/api/v1/execution/reality/start-task",
                    json={"order_id": order_id, "task_id": task_id, "timestamp": ts},
                ),
            )
            ts2 = datetime.now(timezone.utc).isoformat()
            _step(
                evidence,
                "reality_end_task",
                client.post(
                    "/api/v1/execution/reality/end-task",
                    json={"order_id": order_id, "task_id": task_id, "timestamp": ts2},
                ),
            )
        else:
            evidence["notes"] = evidence.get("notes", []) + ["no_task_id_for_reality"]

        # Controlled stock — attempt status; deduct only if ready
        stock = _step(
            evidence,
            "inventory_deduction_status",
            client.get(f"/api/v1/inventory/deduction/status/{order_id}"),
        )
        if isinstance(stock, dict) and stock.get("can_deduct") is True:
            _step(
                evidence,
                "inventory_deduct",
                client.post(
                    f"/api/v1/inventory/deduction/deduct/{order_id}",
                    json={"reason": "Build1 same-scenario controlled stock"},
                ),
            )
        else:
            evidence["stock_gap_explicit"] = {
                "attempted": True,
                "can_deduct": isinstance(stock, dict) and stock.get("can_deduct"),
                "note": "G3 — advanced inventory gap left explicit",
            }

        pj = _step(
            evidence,
            "post_job_truth",
            client.get(f"/api/v1/execution/{order_id}/post-job-truth"),
        )
        try:
            _step(
                evidence,
                "profitability",
                client.get(f"/api/v1/profitability-analysis/order/{order_id}"),
            )
        except Exception as exc:  # noqa: BLE001
            evidence["profitability_error"] = str(exc)

        # Freeze immutability check
        spine2 = _step(
            evidence,
            "commercial_spine_after",
            client.get(f"/api/v1/intake-v6/workspaces/{WS}/commercial-spine-state"),
        )
        before_gross = evidence["ids"].get("snapshot_frozen_total_gross")
        after_gross = (spine2.get("snapshot_authoritative_offer") or {}).get("written_total_gross")
        evidence["freeze_immutability"] = {
            "before": before_gross,
            "after": after_gross,
            "unchanged": before_gross == after_gross,
        }

        # Lineage summary
        evidence["lineage"] = {
            "intake_request_code": evidence["ids"].get("intake_request_code"),
            "workspace_id": WS,
            "quote_id": quote_id,
            "snapshot_code": evidence["ids"].get("snapshot_code"),
            "order_id": order_id,
            "task_id": task_id,
            "not_order_23099": order_id != 23099,
        }
        failed = [s for s in evidence["steps"] if not s.get("ok")]
        evidence["failed_steps"] = [s["step"] for s in failed]
        evidence["verdict"] = (
            "WALK_PARTIAL"
            if failed or not order_id or not evidence.get("steps")[-1:]
            else "WALK_REACHED_POST_JOB"
        )
        if order_id and any(s["step"] == "post_job_truth" and s["ok"] for s in evidence["steps"]):
            if not failed or all(
                s["step"].startswith("inventory") or s["step"] == "profitability" for s in failed
            ):
                evidence["verdict"] = "WALK_REACHED_POST_JOB"

    evidence["finished_at"] = datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
    print("WROTE", OUT)
    print("VERDICT", evidence.get("verdict"), "ORDER", evidence["ids"].get("order_id"))
    print("FAILED", evidence.get("failed_steps"))
    return 0 if evidence.get("verdict") == "WALK_REACHED_POST_JOB" else 1


if __name__ == "__main__":
    sys.exit(main())
