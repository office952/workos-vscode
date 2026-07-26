"""W5-INT-01 accepted snapshot → Order → Execution contract gate smoke (read-only)."""
from __future__ import annotations

import asyncio
import json
import sqlite3
import sys
from pathlib import Path

import httpx

from core.database import db_manager
from services.intake_v6_quote_to_order_service import get_v6_commercial_spine_state

BASE = "http://127.0.0.1:8001"
WS = "80570a4a-a806-4305-a39c-b34a72092694"
QUOTE_ID = 1
SNAPSHOT_CODE = "QSN2-2026-0001"
EXPECTED_GROSS = 2649.99
DB = Path(__file__).resolve().parents[1] / "dev.db"
OUT = (
	Path(__file__).resolve().parents[2]
	/ "docs"
	/ "qa"
	/ "product-system-active-path-isolation-v1"
	/ "w5_int_01_gate_evidence.json"
)


def _quote_row() -> dict:
	con = sqlite3.connect(DB)
	try:
		row = con.execute(
			"select id, code, status, grand_total, accepted_snapshot_v2_id, notes from quotes where id=?",
			(QUOTE_ID,),
		).fetchone()
		if not row:
			return {}
		notes = json.loads(row[5] or "{}")
		linkage = notes.get("intake_v6_linkage_v1") or {}
		return {
			"id": row[0],
			"code": row[1],
			"status": row[2],
			"grand_total": row[3],
			"accepted_snapshot_v2_id": row[4],
			"offer_stamp": linkage.get("intake_v6_snapshot_authoritative_offer_v1"),
			"accept_decision": linkage.get("accept_decision"),
			"convert_decision": linkage.get("convert_decision"),
		}
	finally:
		con.close()


def _snapshot_row() -> dict | None:
	con = sqlite3.connect(DB)
	try:
		row = con.execute(
			"select id, snapshot_code, content_hash, readiness, status from quote_snapshots_v2 where snapshot_code=?",
			(SNAPSHOT_CODE,),
		).fetchone()
		if not row:
			return None
		return {
			"id": row[0],
			"snapshot_code": row[1],
			"content_hash": row[2],
			"readiness": row[3],
			"status": row[4],
		}
	finally:
		con.close()


def _orders_count() -> int:
	con = sqlite3.connect(DB)
	try:
		return int(con.execute("select count(*) from orders where quote_id=?", (QUOTE_ID,)).fetchone()[0])
	finally:
		con.close()


def _execution_plans_count() -> int:
	con = sqlite3.connect(DB)
	try:
		return int(
			con.execute(
				"select count(*) from execution_plan ep join orders o on ep.order_id=o.id where o.quote_id=?",
				(QUOTE_ID,),
			).fetchone()[0]
		)
	finally:
		con.close()


async def main() -> int:
	before = {
		"quote": _quote_row(),
		"snapshot": _snapshot_row(),
		"orders": _orders_count(),
		"execution_plans": _execution_plans_count(),
	}
	http_spine_status = None
	http_spine_body: dict | None = None
	try:
		async with httpx.AsyncClient(base_url=BASE, timeout=30.0) as client:
			resp = await client.get(
				f"/api/v1/intake-v6/workspaces/{WS}/commercial-spine-state",
			)
			http_spine_status = resp.status_code
			http_spine_body = resp.json() if resp.status_code == 200 else {"error": resp.text}
	except Exception as exc:
		http_spine_body = {"error": str(exc)}

	service_spine: dict | None = None
	try:
		await db_manager.ensure_initialized()
		async with db_manager.async_session_maker() as db:
			service_spine = await get_v6_commercial_spine_state(db, workspace_id=WS)
	except Exception as exc:
		service_spine = {"error": str(exc)}

	after = {
		"quote": _quote_row(),
		"snapshot": _snapshot_row(),
		"orders": _orders_count(),
		"execution_plans": _execution_plans_count(),
	}

	read_model = (http_spine_body or {}).get("pricing_review_read_model") or {}
	offer_stamp = (http_spine_body or {}).get("snapshot_authoritative_offer") or {}
	pass_checks = {
		"http_spine_ok": http_spine_status == 200,
		"pricing_review_authority": read_model.get("authority_source") == "quote_snapshot_v2",
		"frozen_gross": read_model.get("commercial_totals", {}).get("total_gross") == EXPECTED_GROSS,
		"offer_stamp_present": bool(offer_stamp),
		"live_dry_run_false": read_model.get("live_dry_run_used") is False,
		"quote_not_accepted": before["quote"].get("accepted_snapshot_v2_id") is None,
		"no_orders": before["orders"] == 0,
		"no_execution_plans": before["execution_plans"] == 0,
		"fixture_unchanged": before == after,
	}
	passed = all(pass_checks.values())

	evidence = {
		"base": BASE,
		"workspace_id": WS,
		"quote_id": QUOTE_ID,
		"snapshot_code": SNAPSHOT_CODE,
		"before": before,
		"http_spine": {"status": http_spine_status, "body": http_spine_body},
		"service_spine": service_spine,
		"after": after,
		"pass_checks": pass_checks,
		"pass": passed,
	}
	OUT.parent.mkdir(parents=True, exist_ok=True)
	OUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
	print(json.dumps({"pass": passed, "out": str(OUT)}, indent=2))
	return 0 if passed else 1


if __name__ == "__main__":
	raise SystemExit(asyncio.run(main()))
