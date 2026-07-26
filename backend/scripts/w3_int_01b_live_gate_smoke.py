"""W3-INT-01B live snapshot + runtime gate smoke (HTTP via trusted port)."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8001"
WS = "80570a4a-a806-4305-a39c-b34a72092694"
SVG_HASH = "593c4d439157b83cab16c33d69caf0ab426144d583fb1999fa7d1676d5ab6cf1"
DB = Path(__file__).resolve().parents[1] / "dev.db"
OUT = Path(__file__).resolve().parents[2] / "docs" / "qa" / "product-system-active-path-isolation-v1" / "w3_int_01b_gate_evidence.json"


def _canonical_hash(obj: object) -> str:
    encoded = json.dumps(obj, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _db_counts() -> dict[str, int]:
    con = sqlite3.connect(DB)
    try:
        return {
            "quotes": con.execute("select count(*) from quotes").fetchone()[0],
            "snapshots": con.execute("select count(*) from quote_snapshots_v2").fetchone()[0],
        }
    finally:
        con.close()


def _snapshot_row(snapshot_code: str | None) -> dict | None:
    if not snapshot_code:
        return None
    con = sqlite3.connect(DB)
    try:
        row = con.execute(
            "select id, snapshot_code, readiness, content_hash, snapshot_json from quote_snapshots_v2 where snapshot_code=?",
            (snapshot_code,),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "snapshot_code": row[1],
            "readiness": row[2],
            "content_hash": row[3],
            "snapshot_json_hash": hashlib.sha256((row[4] or "").encode()).hexdigest(),
        }
    finally:
        con.close()


def main() -> int:
    evidence: dict = {"base": BASE, "workspace_id": WS, "steps": []}
    before = _db_counts()
    evidence["db_before"] = before

    with httpx.Client(base_url=BASE, timeout=120.0) as client:
        # Accepted behavior fingerprints
        dry = client.get(f"/api/v1/intake-v6/workspaces/{WS}/priced-quote-dry-run")
        evidence["steps"].append({"step": "dry_run", "status": dry.status_code, "body": dry.json()})
        dry_body = dry.json()
        assert dry.status_code == 200, dry.text
        assert dry_body.get("pricing_authority") == "commercial_price_proposal_7g", dry_body.get("pricing_authority")
        diag = dry_body.get("diagnostic_cost_plus") or {}
        assert diag.get("diagnostic_only") is True or diag.get("authority") != "commercial_price_proposal_7g"
        assert dry_body.get("pricing_status") == "V6_PRICED_DRY_RUN_READY", dry_body.get("pricing_status")
        gross = float(dry_body["commercial_totals"]["total_gross"])
        pricing_hash = dry_body.get("pricing_input_trace", {}).get("pricing_hash") or dry_body.get("pricing_hash")
        if not pricing_hash:
            payload = {
                "pricing_source": dry_body.get("pricing_source"),
                "commercial_totals": dry_body.get("commercial_totals"),
                "commercial_line_items": dry_body.get("commercial_line_items"),
                "pricing_input_trace": dry_body.get("pricing_input_trace"),
                "commercial_proposal_trace": dry_body.get("commercial_proposal_trace"),
            }
            pricing_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()

        confirm = client.put(
            f"/api/v1/intake-v6/workspaces/{WS}/internal-draft-quote-confirmation",
            json={"confirmed": True},
        )
        evidence["steps"].append({"step": "internal_draft_confirmation", "status": confirm.status_code, "body": confirm.json() if confirm.content else {}})
        assert confirm.status_code == 200, confirm.text

        create = client.post(
            f"/api/v1/intake-v6/workspaces/{WS}/create-draft-quote",
            json={
                "confirm_create_draft_only": True,
                "confirm_no_order": True,
                "confirm_no_execution": True,
                "confirm_no_inventory": True,
                "confirm_internal_draft_quote": True,
                "decision_reason": "W3-INT-01B gate draft quote — no offer/order",
                "client_analysis_hash": SVG_HASH,
            },
        )
        evidence["steps"].append({"step": "create_draft_quote", "status": create.status_code, "body": create.json() if create.content else {}})
        assert create.status_code in (200, 201), create.text
        quote_id = create.json()["quote_id"]

        write = client.post(
            f"/api/v1/intake-v6/workspaces/{WS}/priced-quote/write",
            json={
                "quote_id": quote_id,
                "expected_total_gross": gross,
                "expected_pricing_hash": pricing_hash,
                "operator_confirmation": True,
            },
        )
        evidence["steps"].append({"step": "priced_quote_write", "status": write.status_code, "body": write.json()})
        assert write.status_code == 200, write.text
        assert write.json().get("status") == "V6_PRICED_QUOTE_WRITTEN", write.json()

        snap1 = client.post(
            f"/api/v1/intake-v6/workspaces/{WS}/quotes/{quote_id}/snapshot-v2",
            json={
                "operator_confirmation": True,
                "expected_grand_total": gross,
                "expected_pricing_hash": pricing_hash,
            },
        )
        snap1_body = snap1.json()
        evidence["steps"].append({"step": "snapshot_post_1", "status": snap1.status_code, "body": snap1_body})
        assert snap1.status_code == 200, snap1.text
        assert snap1_body.get("status") == "V6_QUOTE_SNAPSHOT_V2_CREATED", snap1_body
        snapshot_code = snap1_body.get("snapshot_code")
        readiness = snap1_body.get("readiness")
        hash_post = _snapshot_row(snapshot_code)
        evidence["snapshot_after_post"] = hash_post

        read = client.get(f"/api/v1/product-system/quote-snapshot-v2/{snapshot_code}")
        read_body = read.json()
        evidence["steps"].append({"step": "snapshot_read_api", "status": read.status_code, "keys": list(read_body.keys())[:20]})
        assert read.status_code == 200, read.text
        hash_read1 = _canonical_hash(read_body)
        evidence["hash_read_1"] = hash_read1

        time.sleep(0.5)
        read2 = client.get(f"/api/v1/product-system/quote-snapshot-v2/{snapshot_code}")
        read_body2 = read2.json()
        hash_read2 = _canonical_hash(read_body2)
        evidence["hash_read_2"] = hash_read2
        evidence["hash_read_stable"] = hash_read1 == hash_read2

        snap2 = client.post(
            f"/api/v1/intake-v6/workspaces/{WS}/quotes/{quote_id}/snapshot-v2",
            json={
                "operator_confirmation": True,
                "expected_grand_total": gross,
                "expected_pricing_hash": pricing_hash,
            },
        )
        snap2_body = snap2.json()
        evidence["steps"].append({"step": "snapshot_post_2", "status": snap2.status_code, "body": snap2_body})
        codes = {b.get("code") for b in snap2_body.get("blockers", []) if isinstance(b, dict)}
        assert "V6_SNAPSHOT_ALREADY_EXISTS" in codes, snap2_body

        after = _db_counts()
        evidence["db_after"] = after
        evidence["snapshot_count_delta"] = after["snapshots"] - before["snapshots"]
        evidence["quote_id"] = quote_id
        evidence["snapshot_code"] = snapshot_code
        evidence["readiness"] = readiness
        evidence["gross"] = gross

        # Owner decisions + graph fields from read body
        internal = read_body.get("estimated_internal_cost_snapshot") or {}
        evidence["7h_status"] = internal.get("status")
        evidence["unknown_owner_decisions"] = internal.get("unknown_owner_decisions") or []
        evidence["internal_blockers"] = internal.get("internal_blockers") or []
        agg = read_body.get("product_aggregate_snapshot") or {}
        evidence["composition_graph_present"] = bool(agg.get("composition_graph"))
        prov = internal.get("provenance") or []
        evidence["graph_cost_provenance"] = [p for p in prov if isinstance(p, dict) and "graph_cost" in str(p.get("key", ""))]

        cpp = read_body.get("commercial_price_proposal_snapshot") or {}
        lines = cpp.get("commercial_price_lines") or []
        evidence["synthetic_cpp_present"] = any(
            (line.get("pricing_rule_code") == "V6_BACKEND_PRICED_QUOTE_LINE") for line in lines if isinstance(line, dict)
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"ok": True, "snapshot_code": evidence.get("snapshot_code"), "out": str(OUT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
