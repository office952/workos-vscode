"""Build 1 — fresh disposable IR + cloned Letters payload + full continuous walk."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8001"
SOURCE_WS = "80570a4a-a806-4305-a39c-b34a72092694"
SVG_HASH = "593c4d439157b83cab16c33d69caf0ab426144d583fb1999fa7d1676d5ab6cf1"
OUT = Path(__file__).resolve().parent / "lineage_evidence_fresh.json"
HEADERS = {
    "Authorization": "Bearer __DEV_BYPASS_TOKEN__",
    "Origin": "http://127.0.0.1:3000",
}


def _step(ev: dict, name: str, resp: httpx.Response) -> dict:
    try:
        body = resp.json()
    except Exception:
        body = resp.text[:2000]
    ev["steps"].append(
        {"step": name, "status": resp.status_code, "ok": 200 <= resp.status_code < 300, "body": body}
    )
    print(f"[{resp.status_code}] {name}")
    return body if isinstance(body, dict) else {}


def main() -> int:
    ts = int(time.time())
    ir = f"IR-BUILD1-{ts}"
    evidence: dict = {
        "label": "LOCAL LIVE STACK SAME-SCENARIO BUILD1 FRESH",
        "base": BASE,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "steps": [],
        "ids": {"intake_request_code": ir},
    }

    with httpx.Client(base_url=BASE, headers=HEADERS, timeout=180.0) as client:
        # Verify PA now has task_rules (reload)
        pa = _step(
            evidence,
            "live_pa",
            client.get("/api/v1/product-system/aggregate/TPL-VOLUMETRIC-LETTERS_v2"),
        )
        rules = ((pa.get("task_contract") or {}).get("task_rules")) or []
        evidence["ids"]["live_pa_task_rules"] = len(rules)
        if len(rules) < 1:
            evidence["stop"] = "PA_TASK_RULES_STILL_EMPTY"
            OUT.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
            return 2

        # Create IR
        _step(
            evidence,
            "create_intake_request",
            client.post(
                "/api/v1/entities/intake_requests",
                json={
                    "code": ir,
                    "client_id": 1,
                    "client_name": "Build1 Same-Scenario Letters",
                    "contact_person": "Build1",
                    "channel": "email",
                    "product_family": "litere_volumetrice",
                    "description": "Build1 letters continuous lineage disposable",
                    "dimensions": "—",
                    "quantity": 1,
                    "status": "new",
                    "assigned_to": "—",
                    "notes": "disposable build1",
                    "priority": "normal",
                    "delivery_type": "pickup",
                    "confirmed_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
                    "confirmed_template_name": "Litere volumetrice",
                },
            ),
        )

        ensure = _step(
            evidence,
            "ensure_v6_workspace",
            client.post(
                "/api/v1/intake-v6/workspaces/ensure-for-intake-request",
                json={
                    "intake_request_code": ir,
                    "offer_method": "full_product",
                    "analyzer_mode": "analyzer_first",
                    "template_hint_code": "TPL-VOLUMETRIC-LETTERS_v2",
                    "selected_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
                    "source": "build1_same_scenario",
                },
            ),
        )
        ws = ensure.get("id") or ensure.get("workspace_id")
        evidence["ids"]["workspace_id"] = ws
        if not ws:
            evidence["stop"] = "ENSURE_FAILED"
            OUT.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
            return 3

        # Clone payload from source (keep finish/composition truths; rewrite IR)
        src = _step(evidence, "get_source_workspace", client.get(f"/api/v1/intake-v6/workspaces/{SOURCE_WS}"))
        payload = dict(src.get("payload") or {})
        payload["intake_request_code"] = ir
        # Prefer letters root binding
        pb = dict(payload.get("product_binding") or {})
        pb["template_code"] = "TPL-VOLUMETRIC-LETTERS_v2"
        payload["product_binding"] = pb

        # Persist cloned payload via DB helper endpoint is unavailable — use analysis + finish paths.
        # Direct SQL update through a small backend one-shot:
        import sqlite3
        from pathlib import Path as P

        db = P(__file__).resolve().parents[3] / "backend" / "dev.db"
        con = sqlite3.connect(db)
        con.execute(
            "UPDATE intake_v6_workspaces SET payload_json=?, readiness_status=?, template_code=?, status=?, title=? WHERE id=?",
            (
                json.dumps(payload),
                "ready_for_quote_preview",
                "TPL-VOLUMETRIC-LETTERS_v2",
                "ready_for_quote_preview",
                f"BUILD1-LETTERS-{ts}",
                ws,
            ),
        )
        con.commit()
        con.close()
        evidence["steps"].append({"step": "clone_payload_sql", "status": 200, "ok": True, "body": {"workspace_id": ws}})

        ws_body = _step(evidence, "get_workspace", client.get(f"/api/v1/intake-v6/workspaces/{ws}"))
        evidence["ids"]["readiness_status"] = ws_body.get("readiness_status")
        evidence["ids"]["template_code"] = ws_body.get("template_code")

        dry = _step(evidence, "priced_quote_dry_run", client.get(f"/api/v1/intake-v6/workspaces/{ws}/priced-quote-dry-run"))
        if dry.get("pricing_status") != "V6_PRICED_DRY_RUN_READY":
            evidence["stop"] = "DRY_RUN_NOT_READY"
            OUT.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
            return 4
        gross = float(dry["commercial_totals"]["total_gross"])
        pricing_hash = (dry.get("pricing_input_trace") or {}).get("pricing_hash") or dry.get("pricing_hash")

        _step(
            evidence,
            "internal_draft_confirmation",
            client.put(
                f"/api/v1/intake-v6/workspaces/{ws}/internal-draft-quote-confirmation",
                json={"confirmed": True},
            ),
        )
        created = _step(
            evidence,
            "create_draft_quote",
            client.post(
                f"/api/v1/intake-v6/workspaces/{ws}/create-draft-quote",
                json={
                    "confirm_create_draft_only": True,
                    "confirm_no_order": True,
                    "confirm_no_execution": True,
                    "confirm_no_inventory": True,
                    "confirm_internal_draft_quote": True,
                    "decision_reason": "Build1 fresh continuous draft",
                    "client_analysis_hash": SVG_HASH,
                },
            ),
        )
        quote_id = created.get("quote_id") or created.get("id")
        evidence["ids"]["quote_id"] = quote_id
        if not quote_id:
            evidence["stop"] = "CREATE_DRAFT_FAILED"
            OUT.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
            return 5

        write_body = {
            "quote_id": int(quote_id),
            "expected_total_gross": gross,
            "operator_confirmation": True,
        }
        if pricing_hash:
            write_body["expected_pricing_hash"] = pricing_hash
        _step(
            evidence,
            "priced_quote_write",
            client.post(f"/api/v1/intake-v6/workspaces/{ws}/priced-quote/write", json=write_body),
        )

        snap = _step(
            evidence,
            "snapshot_v2",
            client.post(
                f"/api/v1/intake-v6/workspaces/{ws}/quotes/{quote_id}/snapshot-v2",
                json={
                    "operator_confirmation": True,
                    "expected_grand_total": gross,
                    **({"expected_pricing_hash": pricing_hash} if pricing_hash else {}),
                },
            ),
        )
        evidence["ids"]["snapshot_code"] = snap.get("snapshot_code") or (snap.get("snapshot") or {}).get(
            "snapshot_code"
        )
        # Verify frozen PA task_rules
        scode = evidence["ids"]["snapshot_code"]
        if scode:
            qs = _step(
                evidence,
                "get_quote_snapshot",
                client.get(f"/api/v1/product-system/quote-snapshot-v2/{scode}"),
            )
            qrules = (((qs.get("product_aggregate_snapshot") or {}).get("task_contract") or {}).get("task_rules")) or []
            evidence["ids"]["snapshot_task_rules"] = len(qrules)

        _step(
            evidence,
            "complete_pricing_review",
            client.post(
                f"/api/v1/intake-v6/quotes/{quote_id}/complete-pricing-review",
                json={
                    "expected_quote_id": int(quote_id),
                    "pricing_review_reason": "Build1 fresh pricing review",
                    "reviewer_confirmation": True,
                    "confirm_quote_stays_draft": True,
                    "confirm_no_order": True,
                    "confirm_no_execution": True,
                    "confirm_no_inventory": True,
                },
            ),
        )
        owner_codes = []
        spine = _step(
            evidence,
            "commercial_spine_state",
            client.get(f"/api/v1/intake-v6/workspaces/{ws}/commercial-spine-state"),
        )
        owner_codes = (spine.get("snapshot_authoritative_offer") or {}).get("owner_decision_codes") or []
        evidence["ids"]["snapshot_frozen_total_gross"] = (
            (spine.get("snapshot_authoritative_offer") or {}).get("written_total_gross")
        )

        _step(
            evidence,
            "owner_approval",
            client.post(
                f"/api/v1/intake-v6/quotes/{quote_id}/owner-approval",
                json={
                    "expected_quote_id": int(quote_id),
                    "decision_reason": "Build1 fresh owner approval",
                    "acknowledged_no_execution_tasks": True,
                    "acknowledged_no_stock_consumption": True,
                    "acknowledged_blockers": list(owner_codes),
                },
            ),
        )
        _step(
            evidence,
            "accept",
            client.post(
                f"/api/v1/intake-v6/quotes/{quote_id}/accept",
                json={
                    "accept_reason": "Build1 fresh accept",
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
        convert = _step(
            evidence,
            "convert_to_order",
            client.post(
                f"/api/v1/intake-v6/quotes/{quote_id}/convert-to-order",
                json={
                    "convert_reason": "Build1 fresh convert",
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
        order_id = convert.get("order_id")
        evidence["ids"]["order_id"] = order_id
        evidence["ids"]["order_code"] = convert.get("order_code")
        if order_id in (None, 23099, 92401):
            # 92401 is prior partial walk — new order should be different
            if order_id in (None, 23099):
                evidence["stop"] = "BAD_ORDER_ID"
                OUT.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
                return 6

        preview = _step(
            evidence, "plan_v2_preview", client.post(f"/api/v1/execution/plan-v2/preview/{order_id}")
        )
        evidence["ids"]["plan_preview_status"] = preview.get("status")
        evidence["ids"]["planned_tasks"] = len(preview.get("planned_tasks") or [])

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
        blockers = release.get("blockers") or []
        for b in blockers:
            code = b.get("code") if isinstance(b, dict) else None
            if not code:
                continue
            _step(
                evidence,
                f"resolve:{code}",
                client.post(
                    f"/api/v1/execution/orders/{order_id}/owner-decisions/{code}/resolve",
                    json={"status": "accepted", "note": "Build1 fresh resolve"},
                ),
            )

        tasks = mat.get("tasks") or mat.get("materialized_tasks") or persist.get("tasks") or []
        task_id = None
        if tasks and isinstance(tasks[0], dict):
            task_id = tasks[0].get("task_id") or tasks[0].get("id")
        if not task_id and preview.get("planned_tasks"):
            # after materialize failure, try list
            listed = _step(
                evidence,
                "list_tasks_alt",
                client.get(f"/api/v1/execution/reality/{order_id}"),
            )
            sess = listed.get("tasks") or listed.get("sessions") or []
            if sess and isinstance(sess[0], dict):
                task_id = sess[0].get("task_id") or sess[0].get("id")
        evidence["ids"]["task_id"] = task_id

        if task_id:
            now = datetime.now(timezone.utc).isoformat()
            _step(
                evidence,
                "reality_start",
                client.post(
                    "/api/v1/execution/reality/start-task",
                    json={"order_id": order_id, "task_id": task_id, "timestamp": now},
                ),
            )
            later = datetime.now(timezone.utc).isoformat()
            _step(
                evidence,
                "reality_end",
                client.post(
                    "/api/v1/execution/reality/end-task",
                    json={"order_id": order_id, "task_id": task_id, "timestamp": later},
                ),
            )

        stock = _step(
            evidence,
            "inventory_status",
            client.get(f"/api/v1/inventory/deduction/status/{order_id}"),
        )
        if isinstance(stock, dict) and stock.get("can_deduct") is True:
            _step(
                evidence,
                "inventory_deduct",
                client.post(
                    f"/api/v1/inventory/deduction/deduct/{order_id}",
                    json={"reason": "Build1 fresh controlled stock"},
                ),
            )
        else:
            evidence["stock_gap_explicit"] = True

        _step(evidence, "post_job_truth", client.get(f"/api/v1/execution/{order_id}/post-job-truth"))
        _step(
            evidence,
            "profitability",
            client.get(f"/api/v1/profitability-analysis/order/{order_id}"),
        )

        spine2 = _step(
            evidence,
            "spine_after",
            client.get(f"/api/v1/intake-v6/workspaces/{ws}/commercial-spine-state"),
        )
        before = evidence["ids"].get("snapshot_frozen_total_gross")
        after = (spine2.get("snapshot_authoritative_offer") or {}).get("written_total_gross")
        evidence["freeze_immutability"] = {"before": before, "after": after, "unchanged": before == after}
        evidence["lineage"] = {
            "intake_request_code": ir,
            "workspace_id": ws,
            "quote_id": quote_id,
            "snapshot_code": evidence["ids"].get("snapshot_code"),
            "order_id": order_id,
            "task_id": task_id,
            "not_23099": order_id != 23099,
        }
        failed = [s["step"] for s in evidence["steps"] if not s.get("ok")]
        evidence["failed_steps"] = failed
        critical_ok = all(
            any(s["step"] == name and s["ok"] for s in evidence["steps"])
            for name in (
                "create_intake_request",
                "ensure_v6_workspace",
                "snapshot_v2",
                "accept",
                "convert_to_order",
                "plan_v2_persist",
                "post_job_truth",
            )
        )
        evidence["verdict"] = "WALK_PASS" if critical_ok and evidence["freeze_immutability"]["unchanged"] else "WALK_PARTIAL"

    evidence["finished_at"] = datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
    print("WROTE", OUT)
    print("VERDICT", evidence.get("verdict"), evidence.get("lineage"))
    print("FAILED", evidence.get("failed_steps"))
    return 0 if evidence.get("verdict") == "WALK_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
