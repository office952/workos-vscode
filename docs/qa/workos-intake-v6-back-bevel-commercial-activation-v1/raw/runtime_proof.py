"""QA-clone runtime proof for back-bevel commercial activation. Owner workspace is read-only."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import requests

OWNER_ID = "e994927e-aa90-46b0-bde0-dd34e025e44e"
BASE = "http://127.0.0.1:8000/api/v1/intake-v6"
HEADERS = {
    "Authorization": "Bearer __DEV_BYPASS_TOKEN__",
    "Content-Type": "application/json",
}
OUT = Path(__file__).resolve().parent


def _get(path: str) -> dict:
    resp = requests.get(f"{BASE}{path}", headers=HEADERS, timeout=120)
    resp.raise_for_status()
    return resp.json()


def _post(path: str, body: dict | None = None) -> dict:
    resp = requests.post(f"{BASE}{path}", headers=HEADERS, json=body or {}, timeout=120)
    resp.raise_for_status()
    return resp.json()


def _put(path: str, body: dict) -> dict:
    resp = requests.put(f"{BASE}{path}", headers=HEADERS, json=body, timeout=120)
    resp.raise_for_status()
    return resp.json()


def _clone() -> dict:
    return _post(f"/workspaces/from-v4/{OWNER_ID}")


def _set_layer_backing(workspace_id: str, mode: str) -> dict:
    ws = _get(f"/workspaces/{workspace_id}")
    finish = dict((ws.get("payload") or {}).get("finish_setup") or {})
    groups = list(finish.get("letter_group_finishes") or [])
    updated = []
    for group in groups:
        row = dict(group)
        row["backing_mode"] = mode
        updated.append(row)
    finish["letter_group_finishes"] = updated
    instances = list(finish.get("letter_group_instances") or [])
    new_instances = []
    for inst in instances:
        row = dict(inst)
        construction = dict(row.get("construction") or {})
        construction["backing_mode"] = mode
        row["construction"] = construction
        materials = dict(row.get("materials") or {})
        materials["backing_mode"] = mode
        row["materials"] = materials
        new_instances.append(row)
    finish["letter_group_instances"] = new_instances
    finish.pop("backing_mode", None)
    finish.pop("back_bevel_enabled", None)
    return _put(f"/workspaces/{workspace_id}/finish-setup", finish)


def _lines(preview: dict) -> list[dict]:
    return list(
        preview.get("commercial_line_items")
        or preview.get("commercial_price_lines")
        or preview.get("lines")
        or []
    )


def _summarize(workspace_id: str) -> dict:
    ws = _get(f"/workspaces/{workspace_id}")
    payload = ws.get("payload") or {}
    finish = payload.get("finish_setup") or {}
    groups = finish.get("letter_group_finishes") or []
    pricing = _get(f"/workspaces/{workspace_id}/pricing-input-preview")
    qi = pricing.get("quote_input_payload") or pricing.get("quote_input") or {}
    quote = _get(f"/workspaces/{workspace_id}/priced-quote-dry-run")
    commercial = quote.get("commercial_price_proposal") or quote.get("preview") or quote
    totals = commercial.get("commercial_totals") or {}
    lines = _lines(commercial)
    by_code = {str(line.get("code")): line for line in lines}
    tasks = _get(f"/workspaces/{workspace_id}/production-task-dry-run")
    gen = _get(f"/workspaces/{workspace_id}/task-generation-dry-run")
    cnc_ops = [
        {
            "key": row.get("operation_key") or row.get("candidate_key") or row.get("key"),
            "title": row.get("title") or row.get("display_name"),
            "quantity": row.get("quantity"),
            "passes": row.get("passes"),
        }
        for row in (gen.get("cnc_operation_candidates") or [])
    ]
    candidate_tasks = tasks.get("candidate_tasks") or []
    gen_tasks = gen.get("task_candidates") or []
    return {
        "workspace_id": workspace_id,
        "workspace_code": ws.get("workspace_code"),
        "updated_at": ws.get("updated_at"),
        "payload_global_backing_mode": finish.get("backing_mode"),
        "payload_global_back_bevel_enabled": finish.get("back_bevel_enabled"),
        "layer_backing_modes": [g.get("backing_mode") for g in groups],
        "quote_input": {
            "backing_mode": qi.get("backing_mode"),
            "back_bevel_enabled": qi.get("back_bevel_enabled"),
            "backing_bevel_perimeter_ml": qi.get("backing_bevel_perimeter_ml"),
            "backing_present": qi.get("backing_present"),
        },
        "totals": {
            "net": totals.get("subtotal_net") or commercial.get("net_total"),
            "gross": totals.get("total_gross") or commercial.get("gross_total"),
            "vat": totals.get("vat_rate") or commercial.get("vat_rate"),
            "line_count": len(lines),
            "line_codes": sorted(by_code),
        },
        "sanfren_spate": by_code.get("sanfren_spate"),
        "debitare_spate": by_code.get("debitare_spate"),
        "production_task_count": len(candidate_tasks),
        "generation_task_count": len(gen_tasks),
        "generation_task_keys": [t.get("task_key") for t in gen_tasks],
        "cnc_operation_keys": [row["key"] for row in cnc_ops],
        "cnc_operations": cnc_ops,
        "backing_cnc_tasks": [
            {
                "id": t.get("candidate_task_id") or t.get("task_key"),
                "title": t.get("title"),
                "seed_code": t.get("seed_code") or t.get("task_key"),
                "warnings": t.get("warnings"),
            }
            for t in candidate_tasks
            if "cnc_backing" in str(t.get("candidate_task_id") or t.get("seed_code") or t.get("task_key") or "")
        ],
        "separate_bevel_task": any(
            "cnc_backing_bevel" in str(t.get("candidate_task_id") or t.get("seed_code") or t.get("task_key") or "")
            for t in candidate_tasks + gen_tasks
        ),
    }


def main() -> None:
    owner_before = _get(f"/workspaces/{OWNER_ID}")
    off_ws = _clone()
    on_ws = _clone()
    off_id = off_ws["id"]
    on_id = on_ws["id"]
    _set_layer_backing(off_id, "forex_10_no_bevel")
    _set_layer_backing(on_id, "forex_10_with_bevel")
    owner_after = _get(f"/workspaces/{OWNER_ID}")
    off = _summarize(off_id)
    on = _summarize(on_id)
    summary = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "owner_source": OWNER_ID,
        "owner_updated_at_before": owner_before.get("updated_at"),
        "owner_updated_at_after": owner_after.get("updated_at"),
        "owner_dev_db_mutations": 0
        if owner_before.get("updated_at") == owner_after.get("updated_at")
        else "CHANGED",
        "off": off,
        "on": on,
        "deltas": {
            "net": (on["totals"]["net"] or 0) - (off["totals"]["net"] or 0),
            "gross": (on["totals"]["gross"] or 0) - (off["totals"]["gross"] or 0),
            "production_task_count": on["production_task_count"] - off["production_task_count"],
            "generation_task_count": on["generation_task_count"] - off["generation_task_count"],
            "debitare_spate_subtotal": (
                (on.get("debitare_spate") or {}).get("subtotal"),
                (off.get("debitare_spate") or {}).get("subtotal"),
            ),
        },
    }
    (OUT / "runtime_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary["deltas"], indent=2))
    print("owner_dev_db_mutations", summary["owner_dev_db_mutations"])
    print("off_tasks", off["production_task_count"], off["generation_task_count"])
    print("on_tasks", on["production_task_count"], on["generation_task_count"])
    print("sanfren", bool(on.get("sanfren_spate")), (on.get("sanfren_spate") or {}).get("subtotal"))
    print("separate_bevel_task", on["separate_bevel_task"])


if __name__ == "__main__":
    main()
