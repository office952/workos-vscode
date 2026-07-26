"""W4-T01B live snapshot-authoritative pricing review smoke (read-only)."""
from __future__ import annotations

import asyncio
import json
import sqlite3
import sys
from pathlib import Path

import httpx

from core.database import db_manager
from services.intake_v6_quote_to_order_service import get_v6_commercial_spine_state
from services.intake_v6_snapshot_authoritative_pricing_review_service import (
	build_v6_pricing_review_spine_projection,
)
from services.quotes import QuotesService

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
	/ "w4_t01b_gate_evidence.json"
)


def _quote_row() -> dict:
	con = sqlite3.connect(DB)
	try:
		row = con.execute(
			"select id, code, status, grand_total, notes from quotes where id=?",
			(QUOTE_ID,),
		).fetchone()
		if not row:
			return {}
		notes = json.loads(row[4] or "{}")
		linkage = notes.get("intake_v6_linkage_v1") or {}
		return {
			"id": row[0],
			"code": row[1],
			"status": row[2],
			"grand_total": row[3],
			"offer_stamp": linkage.get("intake_v6_snapshot_authoritative_offer_v1"),
			"pricing_review_completed": (linkage.get("pricing_review") or {}).get("status") == "completed",
		}
	finally:
		con.close()


def _snapshot_row() -> dict | None:
	con = sqlite3.connect(DB)
	try:
		row = con.execute(
			"select id, snapshot_code, content_hash, readiness from quote_snapshots_v2 where snapshot_code=?",
			(SNAPSHOT_CODE,),
		).fetchone()
		if not row:
			return None
		return {
			"id": row[0],
			"snapshot_code": row[1],
			"content_hash": row[2],
			"readiness": row[3],
		}
	finally:
		con.close()


def _orders_count() -> int:
	con = sqlite3.connect(DB)
	try:
		return int(con.execute("select count(*) from orders").fetchone()[0])
	finally:
		con.close()


async def _service_projection() -> dict:
	await db_manager.ensure_initialized()
	async with db_manager.async_session_maker() as db:
		quotes = QuotesService(db)
		quote = await quotes.get_by_id(QUOTE_ID)
		if quote is None:
			raise RuntimeError(f"quote {QUOTE_ID} missing")
		from services.intake_v6_commercial_quote_service import parse_intake_v6_linkage_from_notes

		linkage = parse_intake_v6_linkage_from_notes(quote.notes)
		if linkage is None:
			raise RuntimeError("missing v6 linkage")
		read_model = await build_v6_pricing_review_spine_projection(db, quote, linkage)
		spine = await get_v6_commercial_spine_state(db, workspace_id=WS)
		return {"read_model": read_model, "spine": spine}


async def main() -> int:
	before = {
		"quote": _quote_row(),
		"snapshot": _snapshot_row(),
		"orders": _orders_count(),
	}
	http_status = None
	http_body: dict | None = None
	try:
		async with httpx.AsyncClient(timeout=20.0) as client:
			resp = await client.get(f"{BASE}/intake-v6/workspaces/{WS}/commercial-spine-state")
			http_status = resp.status_code
			http_body = resp.json()
	except Exception as exc:
		http_body = {"error": str(exc)}

	service = await _service_projection()
	read_model = service["read_model"]
	spine = service["spine"]
	commercial = read_model.get("commercial_totals") or {}
	after = {
		"quote": _quote_row(),
		"snapshot": _snapshot_row(),
		"orders": _orders_count(),
	}
	pass_gate = (
		before.get("snapshot") is not None
		and before["quote"].get("offer_stamp") is not None
		and float(commercial.get("total_gross") or 0) == EXPECTED_GROSS
		and read_model.get("authority_source") == "quote_snapshot_v2"
		and read_model.get("live_dry_run_used") is False
		and after["orders"] == before["orders"]
		and spine.get("quote_commercial_totals", {}).get("pricing_totals_source") == "quote_snapshot_v2"
	)
	evidence = {
		"base": BASE,
		"workspace_id": WS,
		"quote_id": QUOTE_ID,
		"snapshot_code": SNAPSHOT_CODE,
		"before": before,
		"http": {"status": http_status, "body": http_body},
		"service": service,
		"after": after,
		"pass": pass_gate,
	}
	OUT.parent.mkdir(parents=True, exist_ok=True)
	OUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
	print(json.dumps({"pass": pass_gate, "out": str(OUT)}, indent=2))
	return 0 if pass_gate else 1


if __name__ == "__main__":
	sys.exit(asyncio.run(main()))
