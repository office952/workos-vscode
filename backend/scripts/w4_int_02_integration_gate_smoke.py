"""W4-INT-02 frozen snapshot Offer/Order E2E integration gate smoke (read-only)."""
from __future__ import annotations

import asyncio
import json
import sqlite3
import sys
from pathlib import Path

import httpx

from core.database import db_manager
from schemas.auth import UserResponse
from services.intake_v6_offer_handoff_service import handoff_intake_v6_workspace_to_offer
from services.intake_v6_priced_quote_write_service import write_intake_v6_priced_quote_totals
from services.intake_v6_quote_to_order_service import get_v6_commercial_spine_state
from services.intake_v6_snapshot_authoritative_pricing_review_service import (
	build_v6_pricing_review_spine_projection,
)
from services.quotes import QuotesService
from services.intake_v6_commercial_quote_service import parse_intake_v6_linkage_from_notes

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
	/ "w4_int_02_gate_evidence.json"
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
			"pricing_review": linkage.get("pricing_review"),
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


async def _service_checks() -> dict:
	await db_manager.ensure_initialized()
	async with db_manager.async_session_maker() as db:
		quotes = QuotesService(db)
		quote = await quotes.get_by_id(QUOTE_ID)
		linkage = parse_intake_v6_linkage_from_notes(quote.notes)
		read_model = await build_v6_pricing_review_spine_projection(db, quote, linkage)
		spine = await get_v6_commercial_spine_state(db, workspace_id=WS)
		user = UserResponse(
			id="w4-int-02-gate-user",
			email="w4-int-02-gate@local",
			name="W4 INT-02 Gate",
			role="admin",
			is_active=True,
			last_login=None,
		)
		handoff_second = await handoff_intake_v6_workspace_to_offer(
			db,
			WS,
			client_analysis_hash="593c4d439157b83cab16c33d69caf0ab426144d583fb1999fa7d1676d5ab6cf1",
			expected_total_gross=EXPECTED_GROSS,
			expected_pricing_hash=None,
			operator_confirmation=True,
			current_user=user,
		)
		priced_write = await write_intake_v6_priced_quote_totals(
			db,
			WS,
			quote_id=QUOTE_ID,
			expected_total_gross=EXPECTED_GROSS,
			operator_confirmation=True,
			operator_identifier="w4-int-02-gate@local",
		)
		return {
			"pricing_review_read_model": read_model,
			"spine": spine,
			"handoff_idempotent_retry": handoff_second,
			"priced_write_blocked": priced_write,
		}


async def main() -> int:
	before = {
		"quote": _quote_row(),
		"snapshot": _snapshot_row(),
		"orders": _orders_count(),
	}
	http_spine_status = None
	http_spine_body: dict | None = None
	try:
		async with httpx.AsyncClient(timeout=20.0) as client:
			resp = await client.get(f"{BASE}/api/v1/intake-v6/workspaces/{WS}/commercial-spine-state")
			http_spine_status = resp.status_code
			http_spine_body = resp.json()
	except Exception as exc:
		http_spine_body = {"error": str(exc)}

	service = await _service_checks()
	read_model = service["pricing_review_read_model"]
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
		and service["handoff_idempotent_retry"].get("status") in {
			"V6_OFFER_FROM_SNAPSHOT_IDEMPOTENT",
			"V6_OFFER_FROM_SNAPSHOT_WRITTEN",
		}
		and service["priced_write_blocked"].get("status") == "V6_PRICED_QUOTE_WRITE_BLOCKED"
		and after["orders"] == before["orders"]
		and after["snapshot"]["content_hash"] == before["snapshot"]["content_hash"]
	)

	evidence = {
		"base": BASE,
		"workspace_id": WS,
		"quote_id": QUOTE_ID,
		"snapshot_code": SNAPSHOT_CODE,
		"before": before,
		"http_spine": {"status": http_spine_status, "body": http_spine_body},
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
