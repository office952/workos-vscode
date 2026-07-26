"""W4-T01 live snapshot-authoritative Offer handoff smoke."""
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
from services.intake_v6_priced_quote_write_service import (
	V6_PRICED_QUOTE_WRITE_SNAPSHOT_ALREADY_FROZEN,
	write_intake_v6_priced_quote_totals,
)
from services.intake_v6_snapshot_authoritative_offer_service import (
	V6_OFFER_FROM_SNAPSHOT_IDEMPOTENT,
	V6_OFFER_FROM_SNAPSHOT_WRITTEN,
)

BASE = "http://127.0.0.1:8001"
WS = "80570a4a-a806-4305-a39c-b34a72092694"
QUOTE_ID = 1
SNAPSHOT_CODE = "QSN2-2026-0001"
SVG_HASH = "593c4d439157b83cab16c33d69caf0ab426144d583fb1999fa7d1676d5ab6cf1"
GROSS = 2649.99
DB = Path(__file__).resolve().parents[1] / "dev.db"
OUT = (
	Path(__file__).resolve().parents[2]
	/ "docs"
	/ "qa"
	/ "product-system-active-path-isolation-v1"
	/ "w4_t01_gate_evidence.json"
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
		stamp = linkage.get("intake_v6_snapshot_authoritative_offer_v1")
		return {
			"id": row[0],
			"code": row[1],
			"status": row[2],
			"grand_total": row[3],
			"offer_stamp": stamp,
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


def _order_count() -> int:
	con = sqlite3.connect(DB)
	try:
		return int(con.execute("select count(*) from orders where quote_id=?", (QUOTE_ID,)).fetchone()[0])
	finally:
		con.close()


async def _service_handoff() -> dict:
	await db_manager.ensure_initialized()
	user = UserResponse(
		id="w4-t01-gate-user",
		email="w4-t01-gate@local",
		name="W4 Gate",
		role="admin",
		is_active=True,
		last_login=None,
	)
	async with db_manager.async_session_maker() as db:
		first = await handoff_intake_v6_workspace_to_offer(
			db,
			WS,
			client_analysis_hash=SVG_HASH,
			expected_total_gross=GROSS,
			expected_pricing_hash=None,
			operator_confirmation=True,
			current_user=user,
		)
		second = await handoff_intake_v6_workspace_to_offer(
			db,
			WS,
			client_analysis_hash=SVG_HASH,
			expected_total_gross=GROSS,
			expected_pricing_hash=None,
			operator_confirmation=True,
			current_user=user,
		)
		write_blocked = await write_intake_v6_priced_quote_totals(
			db,
			WS,
			quote_id=QUOTE_ID,
			expected_total_gross=GROSS,
			operator_confirmation=True,
			operator_identifier="w4-t01-gate@local",
		)
		await db.commit()
	return {
		"handoff_first": first,
		"handoff_second": second,
		"priced_write_blocked": write_blocked,
	}


def main() -> int:
	evidence: dict = {
		"base": BASE,
		"workspace_id": WS,
		"quote_id": QUOTE_ID,
		"snapshot_code": SNAPSHOT_CODE,
	}
	evidence["before"] = {
		"quote": _quote_row(),
		"snapshot": _snapshot_row(),
		"orders": _order_count(),
	}

	try:
		with httpx.Client(base_url=BASE, timeout=60.0) as client:
			spine = client.get(f"/api/v1/intake-v6/quotes/{QUOTE_ID}/commercial-spine-state")
			evidence["commercial_spine_status"] = spine.status_code
			if spine.status_code == 200:
				evidence["commercial_spine"] = spine.json()
	except Exception as exc:
		evidence["commercial_spine_error"] = str(exc)

	service_result = asyncio.run(_service_handoff())
	evidence["service"] = service_result

	first = service_result["handoff_first"]
	second = service_result["handoff_second"]
	blocked = service_result["priced_write_blocked"]
	evidence["after"] = {
		"quote": _quote_row(),
		"snapshot": _snapshot_row(),
		"orders": _order_count(),
	}

	assert first.get("snapshot_authoritative_offer") is True, first
	assert first.get("status") in {V6_OFFER_FROM_SNAPSHOT_WRITTEN, V6_OFFER_FROM_SNAPSHOT_IDEMPOTENT}, first
	assert first.get("pricing_trace", {}).get("live_dry_run_used") is False, first
	assert second.get("status") == V6_OFFER_FROM_SNAPSHOT_IDEMPOTENT, second
	assert blocked.get("blockers", [{}])[0].get("code") == V6_PRICED_QUOTE_WRITE_SNAPSHOT_ALREADY_FROZEN, blocked
	assert evidence["after"]["orders"] == evidence["before"]["orders"], "order created unexpectedly"
	assert evidence["after"]["snapshot"]["content_hash"] == evidence["before"]["snapshot"]["content_hash"]

	evidence["pass"] = True
	OUT.parent.mkdir(parents=True, exist_ok=True)
	OUT.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
	print(json.dumps({"pass": True, "first_status": first.get("status"), "second_status": second.get("status")}, indent=2))
	return 0


if __name__ == "__main__":
	try:
		raise SystemExit(main())
	except Exception as exc:
		print(f"FAIL: {exc}", file=sys.stderr)
		raise
