"""W4-T01 — Intake V6 snapshot-authoritative Offer consumer tests."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from models.quotes import Quotes
from schemas.commercial_price_proposal import CommercialPriceLine, CommercialPriceProposalPreview
from schemas.estimated_internal_cost import EstimatedInternalCostPreview
from schemas.quote_snapshot_v2 import QuoteSnapshotOwnerDecision, QuoteSnapshotV2
from services.intake_v6_commercial_quote_service import INTAKE_V6_LINKAGE_JSON_KEY, intake_v6_linkage_code
from services.intake_v6_offer_handoff_service import handoff_intake_v6_workspace_to_offer
from services.intake_v6_priced_quote_write_service import (
	V6_PRICED_QUOTE_WRITE_SNAPSHOT_ALREADY_FROZEN,
	write_intake_v6_priced_quote_totals,
)
from services.intake_v6_snapshot_authoritative_offer_service import (
	V6_OFFER_FROM_SNAPSHOT_BLOCKED,
	V6_OFFER_FROM_SNAPSHOT_IDEMPOTENT,
	V6_OFFER_FROM_SNAPSHOT_WRITTEN,
	INTAKE_V6_SNAPSHOT_AUTHORITATIVE_OFFER_JSON_KEY,
	write_intake_v6_offer_from_frozen_snapshot_v2,
)
from tests.test_quote_snapshot_v2_accept_gate import (
	ANALYSIS_HASH,
	TEMPLATE,
	_insert_snapshot,
	_seed_v6_quote,
	_test_user,
)

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]


@pytest.fixture(autouse=True)
def no_workspace_critical_blockers(monkeypatch):
	async def _empty(*args, **kwargs):
		return []

	monkeypatch.setattr(
		"services.intake_v6_quote_to_order_service._collect_accept_critical_blockers",
		_empty,
	)


def _commercial_preview_with_lines(*, total: float = 1000.0) -> CommercialPriceProposalPreview:
	return CommercialPriceProposalPreview(
		template_code=TEMPLATE,
		status="ready",
		commercial_total=total,
		subtotal_commercial=total,
		quote_ready_for_commercial_review=True,
		commercial_price_lines=[
			CommercialPriceLine(
				code="debitare_fata",
				label="Debitare fata",
				module_code="debitare_fata",
				component_code="face",
				basis_type="m2",
				quantity=1.25,
				unit="m2",
				commercial_unit_price=800.0,
				subtotal=1000.0,
				pricing_rule_code="CPP-FACE",
				source="commercial_rules_volumetric_v2",
			)
		],
	)


async def _insert_snapshot_with_lines(
	db,
	*,
	quote_id: int,
	workspace_id: str,
	readiness: str = "partial_with_owner_decisions",
	commercial_total: float = 1000.0,
	internal_total: float = 620.0,
	internal_status: str = "blocked",
	owner_decisions: list | None = None,
) -> QuoteSnapshotV2Record:
	owner_list = owner_decisions or [
		QuoteSnapshotOwnerDecision(
			code="INTERNAL_SABLON_FOREX_COST",
			label="Sablon forex",
			source="estimated_internal_cost",
		),
		QuoteSnapshotOwnerDecision(
			code="INTERNAL_MONTAJ_RULE",
			label="Montaj rule",
			source="estimated_internal_cost",
		),
	]
	snapshot = QuoteSnapshotV2(
		quote_id=str(quote_id),
		workspace_id=workspace_id,
		template_code=TEMPLATE,
		commercial_price_proposal_snapshot=_commercial_preview_with_lines(total=commercial_total),
		estimated_internal_cost_snapshot=EstimatedInternalCostPreview(
			template_code=TEMPLATE,
			status=internal_status,
			estimated_total_internal_cost=internal_total,
			ready_for_quote_snapshot=True,
		),
		owner_decisions_snapshot=owner_list,
		readiness=readiness,
		persist_status="persisted",
	)
	snapshot_json = snapshot.model_dump_json()
	content_hash = hashlib.sha256(snapshot_json.encode()).hexdigest()[:32]
	record = QuoteSnapshotV2Record(
		snapshot_code=f"QSN2-TEST-{uuid.uuid4().hex[:8]}",
		snapshot_version="1.0.0",
		version=1,
		quote_id=quote_id,
		workspace_id=workspace_id,
		template_code=TEMPLATE,
		status="frozen",
		readiness=readiness,
		frozen_at=datetime.now(timezone.utc),
		frozen_by="test",
		snapshot_json=snapshot_json,
		content_hash=content_hash,
	)
	db.add(record)
	await db.commit()
	await db.refresh(record)
	return record


def _expected_gross_from_net(net: float, vat_pct: float = 21.0) -> float:
	vat_amount = round(net * vat_pct / 100, 2)
	return round(net + vat_amount, 2)


@pytest.mark.asyncio
async def test_snapshot_offer_consumes_frozen_7g_without_dry_run(volumetric_v2_db, monkeypatch) -> None:
	quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db, grand_total=0.0)
	record = await _insert_snapshot_with_lines(
		volumetric_v2_db,
		quote_id=quote.id,
		workspace_id=workspace_id,
		commercial_total=1000.0,
	)

	dry_run_mock = AsyncMock()
	monkeypatch.setattr(
		"services.intake_v6_priced_quote_write_service.build_intake_v6_priced_quote_dry_run",
		dry_run_mock,
	)

	expected_gross = _expected_gross_from_net(1000.0)
	result = await write_intake_v6_offer_from_frozen_snapshot_v2(
		volumetric_v2_db,
		workspace_id,
		quote_id=quote.id,
		expected_total_gross=expected_gross,
		operator_confirmation=True,
		operator_identifier="ops@example.com",
	)

	assert result["status"] == V6_OFFER_FROM_SNAPSHOT_WRITTEN
	assert result["pricing_trace"]["live_dry_run_used"] is False
	assert result["pricing_trace"]["pricing_source"] == "quote_snapshot_v2"
	assert result["snapshot_v2"]["snapshot_id"] == record.id
	assert result["internal_cost_reference"]["status"] == "blocked"
	dry_run_mock.assert_not_called()

	refreshed = await volumetric_v2_db.get(Quotes, quote.id)
	assert refreshed is not None
	assert float(refreshed.grand_total) == expected_gross
	notes = json.loads(refreshed.notes or "{}")
	stamp = notes[INTAKE_V6_LINKAGE_JSON_KEY][INTAKE_V6_SNAPSHOT_AUTHORITATIVE_OFFER_JSON_KEY]
	assert stamp["content_hash"] == record.content_hash
	assert stamp["snapshot_id"] == record.id


@pytest.mark.asyncio
async def test_priced_write_blocked_when_snapshot_frozen(volumetric_v2_db, monkeypatch) -> None:
	quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db, grand_total=0.0)
	await _insert_snapshot_with_lines(
		volumetric_v2_db,
		quote_id=quote.id,
		workspace_id=workspace_id,
	)

	dry_run_mock = AsyncMock(return_value={"pricing_status": "V6_PRICED_DRY_RUN_READY"})
	monkeypatch.setattr(
		"services.intake_v6_priced_quote_write_service.build_intake_v6_priced_quote_dry_run",
		dry_run_mock,
	)

	result = await write_intake_v6_priced_quote_totals(
		volumetric_v2_db,
		workspace_id,
		quote_id=quote.id,
		expected_total_gross=1210.0,
		operator_confirmation=True,
	)

	assert result["status"] == "V6_PRICED_QUOTE_WRITE_BLOCKED"
	assert result["blockers"][0]["code"] == V6_PRICED_QUOTE_WRITE_SNAPSHOT_ALREADY_FROZEN
	dry_run_mock.assert_not_called()


@pytest.mark.asyncio
async def test_snapshot_offer_rejects_frontend_total_mismatch(volumetric_v2_db) -> None:
	quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db, grand_total=0.0)
	await _insert_snapshot_with_lines(
		volumetric_v2_db,
		quote_id=quote.id,
		workspace_id=workspace_id,
		commercial_total=1000.0,
	)

	result = await write_intake_v6_offer_from_frozen_snapshot_v2(
		volumetric_v2_db,
		workspace_id,
		quote_id=quote.id,
		expected_total_gross=9999.0,
		operator_confirmation=True,
	)

	assert result["status"] == V6_OFFER_FROM_SNAPSHOT_BLOCKED
	assert result["blockers"][0]["code"] == "V6_OFFER_SNAPSHOT_EXPECTED_TOTAL_MISMATCH"


@pytest.mark.asyncio
async def test_snapshot_offer_preserves_owner_decisions_and_partial_7h(volumetric_v2_db) -> None:
	quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db, grand_total=0.0)
	await _insert_snapshot_with_lines(
		volumetric_v2_db,
		quote_id=quote.id,
		workspace_id=workspace_id,
		internal_status="blocked",
	)

	expected_gross = _expected_gross_from_net(1000.0)
	result = await write_intake_v6_offer_from_frozen_snapshot_v2(
		volumetric_v2_db,
		workspace_id,
		quote_id=quote.id,
		expected_total_gross=expected_gross,
		operator_confirmation=True,
	)

	codes = {item["code"] for item in result["owner_decisions_snapshot"]}
	assert "INTERNAL_SABLON_FOREX_COST" in codes
	assert "INTERNAL_MONTAJ_RULE" in codes
	assert result["internal_cost_reference"]["status"] == "blocked"


@pytest.mark.asyncio
async def test_snapshot_offer_handoff_idempotent(volumetric_v2_db) -> None:
	quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db, grand_total=0.0)
	await _insert_snapshot_with_lines(
		volumetric_v2_db,
		quote_id=quote.id,
		workspace_id=workspace_id,
	)

	expected_gross = _expected_gross_from_net(1000.0)
	first = await write_intake_v6_offer_from_frozen_snapshot_v2(
		volumetric_v2_db,
		workspace_id,
		quote_id=quote.id,
		expected_total_gross=expected_gross,
		operator_confirmation=True,
	)
	second = await write_intake_v6_offer_from_frozen_snapshot_v2(
		volumetric_v2_db,
		workspace_id,
		quote_id=quote.id,
		expected_total_gross=expected_gross,
		operator_confirmation=True,
	)

	assert first["status"] == V6_OFFER_FROM_SNAPSHOT_WRITTEN
	assert second["status"] == V6_OFFER_FROM_SNAPSHOT_IDEMPOTENT
	assert second["pricing_trace"]["content_hash"] == first["pricing_trace"]["content_hash"]


@pytest.mark.asyncio
async def test_handoff_routes_to_snapshot_consumer_when_snapshot_exists(volumetric_v2_db, monkeypatch) -> None:
	quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db, grand_total=1210.0)
	await _insert_snapshot_with_lines(
		volumetric_v2_db,
		quote_id=quote.id,
		workspace_id=workspace_id,
	)

	from types import SimpleNamespace

	async def fake_reuse(_db, ws_id, request, current_user):
		return SimpleNamespace(
			quote_created=False,
			quote_id=quote.id,
			quote_code=quote.code,
			quote_status="priced",
		)

	snapshot_write = AsyncMock(
		return_value={
			"status": V6_OFFER_FROM_SNAPSHOT_WRITTEN,
			"commercial_totals": {"total_gross": 1210.0},
			"line_items": [],
			"pricing_trace": {"pricing_source": "quote_snapshot_v2", "live_dry_run_used": False},
			"blockers": [],
			"warnings": [],
			"can_create_quote_snapshot": False,
			"commercial_authority_source": "quote_snapshot_v2",
			"snapshot_v2": {"snapshot_id": 1},
		}
	)
	dry_run_write = AsyncMock()

	monkeypatch.setattr(
		"services.intake_v6_offer_handoff_service.create_or_reuse_guarded_draft_quote_from_intake_v6_workspace",
		fake_reuse,
	)
	monkeypatch.setattr(
		"services.intake_v6_offer_handoff_service.write_intake_v6_offer_from_frozen_snapshot_v2",
		snapshot_write,
	)
	monkeypatch.setattr(
		"services.intake_v6_offer_handoff_service.write_intake_v6_priced_quote_totals",
		dry_run_write,
	)

	result = await handoff_intake_v6_workspace_to_offer(
		volumetric_v2_db,
		workspace_id,
		client_analysis_hash=ANALYSIS_HASH,
		expected_total_gross=1210.0,
		expected_pricing_hash=None,
		operator_confirmation=True,
		current_user=_test_user(),
	)

	assert result["snapshot_authoritative_offer"] is True
	assert result["status"] == V6_OFFER_FROM_SNAPSHOT_WRITTEN
	snapshot_write.assert_awaited_once()
	dry_run_write.assert_not_awaited()


@pytest.mark.asyncio
async def test_no_snapshot_still_uses_pre_freeze_dry_run_path(volumetric_v2_db, monkeypatch) -> None:
	quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db, grand_total=0.0)

	from types import SimpleNamespace

	async def fake_reuse(_db, ws_id, request, current_user):
		return SimpleNamespace(
			quote_created=False,
			quote_id=quote.id,
			quote_code=quote.code,
			quote_status="draft",
		)

	snapshot_write = AsyncMock()
	dry_run_write = AsyncMock(
		return_value={
			"status": "V6_PRICED_QUOTE_WRITTEN",
			"commercial_totals": {"total_gross": 1210.0},
			"line_items": [],
			"pricing_trace": {"pricing_source": "intake_v6_backend_priced_dry_run"},
			"blockers": [],
			"warnings": [],
			"can_create_quote_snapshot": True,
		}
	)

	monkeypatch.setattr(
		"services.intake_v6_offer_handoff_service.create_or_reuse_guarded_draft_quote_from_intake_v6_workspace",
		fake_reuse,
	)
	monkeypatch.setattr(
		"services.intake_v6_offer_handoff_service.write_intake_v6_offer_from_frozen_snapshot_v2",
		snapshot_write,
	)
	monkeypatch.setattr(
		"services.intake_v6_offer_handoff_service.write_intake_v6_priced_quote_totals",
		dry_run_write,
	)

	result = await handoff_intake_v6_workspace_to_offer(
		volumetric_v2_db,
		workspace_id,
		client_analysis_hash=ANALYSIS_HASH,
		expected_total_gross=1210.0,
		expected_pricing_hash="hash",
		operator_confirmation=True,
		current_user=_test_user(),
	)

	assert result["snapshot_authoritative_offer"] is False
	dry_run_write.assert_awaited_once()
	snapshot_write.assert_not_awaited()


@pytest.mark.asyncio
async def test_order_v2_convert_still_green_after_snapshot_offer(volumetric_v2_db) -> None:
	from services.intake_v6_quote_to_order_service import accept_v6_quote, convert_v6_quote_to_order
	from tests.test_quote_snapshot_v2_accept_gate import _valid_accept_body

	quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db, grand_total=0.0)
	record = await _insert_snapshot_with_lines(
		volumetric_v2_db,
		quote_id=quote.id,
		workspace_id=workspace_id,
	)

	expected_gross = _expected_gross_from_net(1000.0)
	await write_intake_v6_offer_from_frozen_snapshot_v2(
		volumetric_v2_db,
		workspace_id,
		quote_id=quote.id,
		expected_total_gross=expected_gross,
		operator_confirmation=True,
	)

	await accept_v6_quote(
		volumetric_v2_db,
		quote.id,
		_valid_accept_body(confirm_owner_decisions_acknowledged=True),
		_test_user(),
	)
	convert_result = await convert_v6_quote_to_order(
		volumetric_v2_db,
		quote.id,
		{
			"convert_reason": "test",
			"reviewer_confirmation": True,
			"confirm_quote_accepted": True,
			"confirm_pricing_review_completed": True,
			"confirm_create_order_only": True,
			"confirm_no_execution_plan": True,
			"confirm_no_execution_tasks": True,
			"confirm_no_inventory": True,
			"confirm_production_separate": True,
		},
		_test_user(),
	)

	assert convert_result["converted"] is True
	assert convert_result["order_snapshot_v2_convert"]["quote_snapshot_v2_id"] == record.id
