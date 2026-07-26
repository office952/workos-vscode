"""W4-T01B — Intake V6 snapshot-authoritative pricing review alignment tests."""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from models.quotes import Quotes
from services.intake_v3_quote_linkage_utils import PRICING_REVIEW_JSON_KEY
from services.intake_v6_commercial_quote_service import INTAKE_V6_LINKAGE_JSON_KEY
from services.intake_v6_quote_to_order_service import (
	complete_v6_pricing_review,
	get_v6_commercial_spine_state,
)
from services.intake_v6_snapshot_authoritative_offer_service import (
	INTAKE_V6_SNAPSHOT_AUTHORITATIVE_OFFER_JSON_KEY,
)
from services.intake_v6_snapshot_authoritative_pricing_review_service import (
	SNAPSHOT_HASH_MISMATCH,
	SNAPSHOT_LINKAGE_MISMATCH,
	SNAPSHOT_QUOTE_TOTAL_DRIFT,
	extract_v6_pricing_review_totals_authoritative,
	resolve_v6_pricing_review_authority,
)
from services.quote_snapshot_v2_accept_gate_service import validate_snapshot_for_accept
from tests.test_intake_v6_snapshot_authoritative_offer import (
	_expected_gross_from_net,
	_insert_snapshot_with_lines,
)
from tests.test_quote_snapshot_v2_accept_gate import (
	ANALYSIS_HASH,
	_full_workspace_payload,
	_test_user,
)
from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from tests.test_quote_snapshot_v2 import TEMPLATE

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]


async def _seed_v6_quote_for_review(
	db,
	*,
	grand_total: float = 0.0,
) -> tuple[Quotes, str]:
	workspace_id = str(uuid.uuid4())
	intake_code = f"IV6-{workspace_id}"
	workspace = IntakeV6WorkspaceRecord(
		id=workspace_id,
		workspace_code=f"WS-{workspace_id[:8]}",
		title="W4-T01B pricing review workspace",
		template_code=TEMPLATE,
		payload_json=json.dumps(_full_workspace_payload()),
		status="draft",
	)
	db.add(workspace)
	linkage = {
		"source_module": "intake_v6",
		"source_intake_version": "V6",
		"source_workspace_id": workspace_id,
		"requires_pricing_review": True,
		"snapshot": {"workspace_payload_snapshot": {"svg_source": {"file_hash": ANALYSIS_HASH}}},
	}
	quote = Quotes(
		code=f"Q-V6-{uuid.uuid4().hex[:8]}",
		client_name="W4-T01B Review Client",
		status="priced",
		version=1,
		intake_code=intake_code,
		grand_total=grand_total,
		notes=json.dumps({INTAKE_V6_LINKAGE_JSON_KEY: linkage}),
	)
	db.add(quote)
	await db.commit()
	await db.refresh(quote)
	return quote, workspace_id


@pytest.fixture(autouse=True)
def no_workspace_critical_blockers(monkeypatch):
	async def _empty(*args, **kwargs):
		return []

	monkeypatch.setattr(
		"services.intake_v6_quote_to_order_service._collect_accept_critical_blockers",
		_empty,
	)


def _pricing_review_body() -> dict:
	return {
		"reviewer_confirmation": True,
		"confirm_quote_stays_draft": True,
		"confirm_no_order": True,
		"confirm_no_execution": True,
		"confirm_no_inventory": True,
		"pricing_review_reason": "W4-T01B pricing review from frozen snapshot.",
	}


def _offer_stamp(record, *, workspace_id: str, quote_id: int, gross: float, net: float) -> dict:
	return {
		"snapshot_id": record.id,
		"snapshot_code": record.snapshot_code,
		"content_hash": record.content_hash,
		"workspace_id": workspace_id,
		"quote_id": quote_id,
		"pricing_source": "quote_snapshot_v2",
		"written_total_gross": gross,
		"written_subtotal_net": net,
		"live_dry_run_used": False,
	}


async def _quote_with_stamp(
	db,
	*,
	workspace_id: str,
	grand_total: float,
	net: float,
	stamp: dict,
) -> Quotes:
	quote, ws_id = await _seed_v6_quote_for_review(db, grand_total=grand_total)
	linkage = json.loads(quote.notes)[INTAKE_V6_LINKAGE_JSON_KEY]
	linkage[INTAKE_V6_SNAPSHOT_AUTHORITATIVE_OFFER_JSON_KEY] = stamp
	quote.notes = json.dumps({INTAKE_V6_LINKAGE_JSON_KEY: linkage})
	quote.total_before_vat = net
	quote.subtotal = net
	quote.vat = round(grand_total - net, 2)
	await db.commit()
	await db.refresh(quote)
	return quote


@pytest.mark.asyncio
async def test_pricing_review_totals_from_frozen_7g_when_snapshot_exists(volumetric_v2_db) -> None:
	quote, workspace_id = await _seed_v6_quote_for_review(volumetric_v2_db, grand_total=0.0)
	record = await _insert_snapshot_with_lines(
		volumetric_v2_db,
		quote_id=quote.id,
		workspace_id=workspace_id,
		commercial_total=1000.0,
	)
	linkage = json.loads(quote.notes)[INTAKE_V6_LINKAGE_JSON_KEY]

	totals = await extract_v6_pricing_review_totals_authoritative(volumetric_v2_db, quote, linkage)

	assert totals["pricing_totals_source"] == "quote_snapshot_v2"
	assert totals["net_before_vat"] == 1000.0
	assert totals["total"] == _expected_gross_from_net(1000.0)
	assert totals["snapshot_v2_id"] == record.id


@pytest.mark.asyncio
async def test_matching_quote_columns_valid_projection(volumetric_v2_db) -> None:
	quote, workspace_id = await _seed_v6_quote_for_review(volumetric_v2_db, grand_total=0.0)
	record = await _insert_snapshot_with_lines(
		volumetric_v2_db,
		quote_id=quote.id,
		workspace_id=workspace_id,
		commercial_total=1000.0,
	)
	gross = _expected_gross_from_net(1000.0)
	quote.grand_total = gross
	quote.total_before_vat = 1000.0
	quote.subtotal = 1000.0
	quote.vat = round(gross - 1000.0, 2)
	await volumetric_v2_db.commit()
	await volumetric_v2_db.refresh(quote)
	linkage = json.loads(quote.notes)[INTAKE_V6_LINKAGE_JSON_KEY]
	linkage[INTAKE_V6_SNAPSHOT_AUTHORITATIVE_OFFER_JSON_KEY] = _offer_stamp(
		record,
		workspace_id=workspace_id,
		quote_id=quote.id,
		gross=gross,
		net=1000.0,
	)

	totals, read_model = await resolve_v6_pricing_review_authority(
		volumetric_v2_db,
		quote,
		linkage,
		fail_on_drift=False,
	)
	assert totals["total"] == gross
	assert read_model["column_drift"] == []
	assert read_model["column_drift_blocked"] is False


@pytest.mark.asyncio
async def test_quote_gross_drift_blocks_pricing_review(volumetric_v2_db) -> None:
	quote, workspace_id = await _seed_v6_quote_for_review(volumetric_v2_db, grand_total=9999.0)
	record = await _insert_snapshot_with_lines(
		volumetric_v2_db,
		quote_id=quote.id,
		workspace_id=workspace_id,
		commercial_total=1000.0,
	)
	quote.total_before_vat = 1000.0
	await volumetric_v2_db.commit()
	linkage = json.loads(quote.notes)[INTAKE_V6_LINKAGE_JSON_KEY]

	with pytest.raises(HTTPException) as exc:
		await extract_v6_pricing_review_totals_authoritative(volumetric_v2_db, quote, linkage)

	assert exc.value.detail["error"] == SNAPSHOT_QUOTE_TOTAL_DRIFT


@pytest.mark.asyncio
async def test_snapshot_hash_mismatch_blocks_pricing_review(volumetric_v2_db) -> None:
	quote, workspace_id = await _seed_v6_quote_for_review(volumetric_v2_db, grand_total=1210.0)
	record = await _insert_snapshot_with_lines(
		volumetric_v2_db,
		quote_id=quote.id,
		workspace_id=workspace_id,
		commercial_total=1000.0,
	)
	gross = _expected_gross_from_net(1000.0)
	quote.grand_total = gross
	quote.total_before_vat = 1000.0
	await volumetric_v2_db.commit()
	linkage = json.loads(quote.notes)[INTAKE_V6_LINKAGE_JSON_KEY]
	linkage[INTAKE_V6_SNAPSHOT_AUTHORITATIVE_OFFER_JSON_KEY] = _offer_stamp(
		record,
		workspace_id=workspace_id,
		quote_id=quote.id,
		gross=gross,
		net=1000.0,
	)
	linkage[INTAKE_V6_SNAPSHOT_AUTHORITATIVE_OFFER_JSON_KEY]["content_hash"] = "deadbeef"

	with pytest.raises(HTTPException) as exc:
		await extract_v6_pricing_review_totals_authoritative(volumetric_v2_db, quote, linkage)

	assert exc.value.detail["error"] == SNAPSHOT_HASH_MISMATCH


@pytest.mark.asyncio
async def test_snapshot_linkage_mismatch_blocks_pricing_review(volumetric_v2_db) -> None:
	quote, workspace_id = await _seed_v6_quote_for_review(volumetric_v2_db, grand_total=1210.0)
	record = await _insert_snapshot_with_lines(
		volumetric_v2_db,
		quote_id=quote.id,
		workspace_id=workspace_id,
		commercial_total=1000.0,
	)
	gross = _expected_gross_from_net(1000.0)
	quote.grand_total = gross
	quote.total_before_vat = 1000.0
	await volumetric_v2_db.commit()
	linkage = json.loads(quote.notes)[INTAKE_V6_LINKAGE_JSON_KEY]
	linkage[INTAKE_V6_SNAPSHOT_AUTHORITATIVE_OFFER_JSON_KEY] = _offer_stamp(
		record,
		workspace_id=workspace_id,
		quote_id=quote.id + 99,
		gross=gross,
		net=1000.0,
	)

	with pytest.raises(HTTPException) as exc:
		await extract_v6_pricing_review_totals_authoritative(volumetric_v2_db, quote, linkage)

	assert exc.value.detail["error"] == SNAPSHOT_LINKAGE_MISMATCH


@pytest.mark.asyncio
async def test_live_dry_run_not_invoked_for_pricing_review(volumetric_v2_db, monkeypatch) -> None:
	quote, workspace_id = await _seed_v6_quote_for_review(volumetric_v2_db, grand_total=1210.0)
	record = await _insert_snapshot_with_lines(
		volumetric_v2_db,
		quote_id=quote.id,
		workspace_id=workspace_id,
		commercial_total=1000.0,
	)
	gross = _expected_gross_from_net(1000.0)
	quote.grand_total = gross
	quote.total_before_vat = 1000.0
	await volumetric_v2_db.commit()
	linkage = json.loads(quote.notes)[INTAKE_V6_LINKAGE_JSON_KEY]

	dry_run = AsyncMock(side_effect=AssertionError("dry-run must not be called"))
	monkeypatch.setattr(
		"services.intake_v6_priced_quote_dry_run_service.build_intake_v6_priced_quote_dry_run",
		dry_run,
	)

	totals = await extract_v6_pricing_review_totals_authoritative(volumetric_v2_db, quote, linkage)
	assert totals["pricing_totals_source"] == "quote_snapshot_v2"
	dry_run.assert_not_called()


@pytest.mark.asyncio
async def test_partial_7h_and_owner_decisions_preserved_in_read_model(volumetric_v2_db) -> None:
	quote, workspace_id = await _seed_v6_quote_for_review(volumetric_v2_db, grand_total=0.0)
	await _insert_snapshot_with_lines(
		volumetric_v2_db,
		quote_id=quote.id,
		workspace_id=workspace_id,
		commercial_total=1000.0,
		internal_status="blocked",
	)
	linkage = json.loads(quote.notes)[INTAKE_V6_LINKAGE_JSON_KEY]

	_totals, read_model = await resolve_v6_pricing_review_authority(
		volumetric_v2_db,
		quote,
		linkage,
		fail_on_drift=False,
	)
	assert read_model["internal_cost"]["status"] == "blocked"
	assert read_model["internal_cost"]["execution_blocked"] is True
	assert "INTERNAL_SABLON_FOREX_COST" in read_model["owner_decision_codes"]


@pytest.mark.asyncio
async def test_pre_freeze_review_uses_quote_columns_without_snapshot(volumetric_v2_db) -> None:
	quote, _workspace_id = await _seed_v6_quote_for_review(volumetric_v2_db, grand_total=1500.0)
	quote.total_before_vat = 1200.0
	quote.subtotal = 1200.0
	quote.vat = 300.0
	await volumetric_v2_db.commit()
	linkage = json.loads(quote.notes)[INTAKE_V6_LINKAGE_JSON_KEY]

	totals, read_model = await resolve_v6_pricing_review_authority(
		volumetric_v2_db,
		quote,
		linkage,
		fail_on_drift=False,
	)
	assert totals["pricing_totals_source"] == "pre_freeze_quote_projection"
	assert read_model["pre_freeze"] is True
	assert read_model["snapshot_v2"]["exists"] is False


@pytest.mark.asyncio
async def test_complete_pricing_review_persists_snapshot_source(volumetric_v2_db) -> None:
	quote, workspace_id = await _seed_v6_quote_for_review(volumetric_v2_db, grand_total=0.0)
	await _insert_snapshot_with_lines(
		volumetric_v2_db,
		quote_id=quote.id,
		workspace_id=workspace_id,
		commercial_total=1000.0,
	)

	result = await complete_v6_pricing_review(
		volumetric_v2_db,
		quote.id,
		_pricing_review_body(),
		_test_user(),
	)
	assert result["pricing_totals_source"] == "quote_snapshot_v2"
	refreshed = await volumetric_v2_db.get(Quotes, quote.id)
	pricing_record = json.loads(refreshed.notes)[INTAKE_V6_LINKAGE_JSON_KEY][PRICING_REVIEW_JSON_KEY]
	assert pricing_record["pricing_totals_source"] == "quote_snapshot_v2"
	assert float(pricing_record["total"]) == _expected_gross_from_net(1000.0)


@pytest.mark.asyncio
async def test_spine_state_exposes_snapshot_authoritative_review_read_model(volumetric_v2_db) -> None:
	quote, workspace_id = await _seed_v6_quote_for_review(volumetric_v2_db, grand_total=1210.0)
	record = await _insert_snapshot_with_lines(
		volumetric_v2_db,
		quote_id=quote.id,
		workspace_id=workspace_id,
		commercial_total=1000.0,
	)
	gross = _expected_gross_from_net(1000.0)
	quote.grand_total = gross
	quote.total_before_vat = 1000.0
	await volumetric_v2_db.commit()
	linkage = json.loads(quote.notes)[INTAKE_V6_LINKAGE_JSON_KEY]
	linkage[INTAKE_V6_SNAPSHOT_AUTHORITATIVE_OFFER_JSON_KEY] = _offer_stamp(
		record,
		workspace_id=workspace_id,
		quote_id=quote.id,
		gross=gross,
		net=1000.0,
	)
	quote.notes = json.dumps({INTAKE_V6_LINKAGE_JSON_KEY: linkage})
	await volumetric_v2_db.commit()

	state = await get_v6_commercial_spine_state(volumetric_v2_db, workspace_id=workspace_id)
	assert state["quote_commercial_totals"]["pricing_totals_source"] == "quote_snapshot_v2"
	assert state["quote_commercial_totals"]["grand_total"] == gross
	read_model = state["pricing_review_read_model"]
	assert read_model["authority_source"] == "quote_snapshot_v2"
	assert read_model["commercial_totals"]["total_gross"] == gross


@pytest.mark.asyncio
async def test_acceptance_still_uses_snapshot_gate(volumetric_v2_db) -> None:
	quote, workspace_id = await _seed_v6_quote_for_review(volumetric_v2_db, grand_total=0.0)
	record = await _insert_snapshot_with_lines(
		volumetric_v2_db,
		quote_id=quote.id,
		workspace_id=workspace_id,
		commercial_total=1000.0,
	)
	gate = validate_snapshot_for_accept(
		record,
		quote_id=quote.id,
		workspace_id=workspace_id,
		confirm_owner_decisions_acknowledged=True,
	)
	assert gate.accept_allowed is True
