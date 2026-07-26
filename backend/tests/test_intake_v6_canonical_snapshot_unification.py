"""W3-T03 — V6 snapshot unification with canonical 7G/7H compose."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from schemas.commercial_price_proposal import CommercialPriceLine, CommercialPriceProposalPreview
from schemas.estimated_internal_cost import EstimatedInternalCostPreview
from schemas.product_aggregate import ProductAggregate, ProductAggregateCompositionGraph
from schemas.quote_snapshot_v2 import QuoteSnapshotOfferScope, QuoteSnapshotV2
from services import intake_v6_quote_snapshot_v2_service as snapshot_service
from services.intake_v6_priced_quote_dry_run_service import V6_PRICED_DRY_RUN_READY
from services.quote_snapshot_v2_service import QuoteSnapshotV2Service

from tests.test_intake_v6_quote_snapshot_v2 import (
	FakeDb,
	FakeQuotesService,
	_fake_persist,
	_line_items,
	_notes,
	_quote,
)


def _canonical(**overrides) -> QuoteSnapshotV2:
	commercial = CommercialPriceProposalPreview(
		template_code="TPL-VOLUMETRIC-LETTERS_v2",
		status=overrides.pop("commercial_status", "ready"),
		commercial_price_lines=[
			CommercialPriceLine(
				code="MOD-FACE",
				label="7G line",
				basis_type="m2",
				quantity=1.0,
				unit="m2",
				commercial_unit_price=1000.0,
				subtotal=1000.0,
				pricing_rule_code="COMM-7G-RULE",
				source="commercial_price_proposal",
			)
		],
		subtotal_commercial=1000.0,
		commercial_total=overrides.pop("commercial_total", 1190.0),
		currency="RON",
		quote_ready_for_commercial_review=overrides.pop("commercial_ready", True),
	)
	internal = EstimatedInternalCostPreview(
		template_code="TPL-VOLUMETRIC-LETTERS_v2",
		status=overrides.pop("internal_status", "ready"),
		estimated_total_internal_cost=overrides.pop("internal_total", 782.38),
		currency="EUR",
		ready_for_quote_snapshot=overrides.pop("internal_ready", True),
	)
	graph = overrides.pop(
		"composition_graph",
		ProductAggregateCompositionGraph(
			composed_graph_version="1.0.0",
			composition_mode="explicit",
			root_template_code="TPL-VOLUMETRIC-LETTERS_v2",
			solution_status="ready",
			compatibility_status="compatible",
			edges=[],
		),
	)
	aggregate = ProductAggregate(
		template_code="TPL-VOLUMETRIC-LETTERS_v2",
		template_id=1,
		composition_graph=graph,
	)
	data = {
		"quote_id": "6",
		"workspace_id": "workspace-v6",
		"template_code": "TPL-VOLUMETRIC-LETTERS_v2",
		"offer_scope_snapshot": QuoteSnapshotOfferScope(use_legacy=True, mode="full_product"),
		"product_aggregate_snapshot": aggregate,
		"commercial_price_proposal_snapshot": commercial,
		"estimated_internal_cost_snapshot": internal,
		"readiness": overrides.pop("readiness", "ready_for_owner_review"),
		"provenance": [],
		"warnings_snapshot": [],
		"blockers_snapshot": [],
		"notes": [],
	}
	data.update(overrides)
	return QuoteSnapshotV2(**data)


@pytest.fixture
def patch_canonical(monkeypatch):
	preview_holder: dict[str, QuoteSnapshotV2 | None] = {"snapshot": _canonical()}

	async def no_snapshots(_db, _quote_id):
		return 0

	async def no_orders(_db, _quote_id):
		return 0

	async def fake_build_preview(self, template_code, **kwargs):
		return preview_holder["snapshot"]

	async def fake_dry_run(_db, _workspace_id, **kwargs):
		return {
			"pricing_status": V6_PRICED_DRY_RUN_READY,
			"commercial_totals": {"total_gross": 1190.0},
			"warnings": [],
			"blockers": [],
		}

	async def fake_resolve(_db, _workspace_id):
		return ("TPL-VOLUMETRIC-LETTERS_v2", {"is_ready_for_quote": True})

	monkeypatch.setattr(snapshot_service, "QuotesService", FakeQuotesService)
	monkeypatch.setattr(snapshot_service, "_snapshot_count", no_snapshots)
	monkeypatch.setattr(snapshot_service, "_order_count", no_orders)
	monkeypatch.setattr(snapshot_service, "_persist_snapshot", _fake_persist)
	monkeypatch.setattr(QuoteSnapshotV2Service, "build_preview", fake_build_preview)
	monkeypatch.setattr(snapshot_service, "build_intake_v6_priced_quote_dry_run", fake_dry_run)
	monkeypatch.setattr(snapshot_service, "resolve_intake_v6_canonical_quote_input", fake_resolve)
	FakeQuotesService.quote = _quote()
	return preview_holder


async def _create(**kwargs):
	return await snapshot_service.create_v6_quote_snapshot_v2(
		FakeDb(),
		quote_id=6,
		workspace_id="workspace-v6",
		operator_confirmation=True,
		expected_grand_total=kwargs.pop("expected_grand_total", 1190.0),
		created_by="test@example.com",
		**kwargs,
	)


def _codes(result: dict) -> set[str]:
	return {str(blocker.get("code")) for blocker in result.get("blockers", [])}


@pytest.mark.asyncio
async def test_7g_ready_7h_ready_creates_canonical_snapshot(patch_canonical) -> None:
	result = await _create()
	assert result["status"] == snapshot_service.V6_QUOTE_SNAPSHOT_V2_CREATED
	assert result["readiness"] == "ready_for_owner_review"
	assert result["can_accept_quote"] is True


@pytest.mark.asyncio
async def test_7g_ready_7h_blocked_allows_partial_snapshot(patch_canonical) -> None:
	patch_canonical["snapshot"] = _canonical(internal_status="blocked", readiness="blocked_missing_internal")
	result = await _create()
	assert result["status"] == snapshot_service.V6_QUOTE_SNAPSHOT_V2_CREATED
	assert result["readiness"] == "partial_with_owner_decisions"
	assert result["internal_trace"]["estimated_internal_cost_snapshot_status"] == "blocked"


@pytest.mark.asyncio
async def test_7g_blocked_7h_ready_blocks_snapshot(patch_canonical) -> None:
	patch_canonical["snapshot"] = _canonical(
		commercial_status="blocked",
		commercial_ready=False,
		readiness="blocked_missing_commercial",
	)
	result = await _create()
	assert result["status"] == snapshot_service.V6_QUOTE_SNAPSHOT_V2_BLOCKED
	assert snapshot_service.V6_SNAPSHOT_COMMERCIAL_AUTHORITY_BLOCKED in _codes(result)


@pytest.mark.asyncio
async def test_both_blocked_blocks_snapshot(patch_canonical) -> None:
	patch_canonical["snapshot"] = _canonical(
		commercial_status="blocked",
		internal_status="blocked",
		readiness="blocked_snapshot_conflict",
	)
	result = await _create()
	assert result["status"] == snapshot_service.V6_QUOTE_SNAPSHOT_V2_BLOCKED


@pytest.mark.asyncio
async def test_commercial_total_mismatch_blocks_snapshot(patch_canonical) -> None:
	patch_canonical["snapshot"] = _canonical(commercial_total=999.0)
	patch_canonical["snapshot"].commercial_price_proposal_snapshot.subtotal_commercial = 999.0
	result = await _create()
	assert snapshot_service.V6_SNAPSHOT_COMMERCIAL_TOTAL_MISMATCH in _codes(result)


@pytest.mark.asyncio
async def test_synthetic_cpp_pricing_rule_blocks_snapshot(patch_canonical) -> None:
	from schemas.commercial_price_proposal import CommercialPriceLine

	snap = _canonical()
	snap.commercial_price_proposal_snapshot.commercial_price_lines = [
		CommercialPriceLine(
			code="SYN",
			label="Synthetic",
			basis_type="unknown",
			pricing_rule_code="V6_BACKEND_PRICED_QUOTE_LINE",
			source="intake_v6_priced_quote_write_service",
		)
	]
	patch_canonical["snapshot"] = snap
	result = await _create()
	assert snapshot_service.V6_SNAPSHOT_SYNTHETIC_CPP_FORBIDDEN in _codes(result)


@pytest.mark.asyncio
async def test_composition_graph_preserved_in_persisted_snapshot(patch_canonical) -> None:
	db = FakeDb()
	preview = _canonical()
	patch_canonical["snapshot"] = preview

	async def capture_persist(db, **kwargs):
		db.quote_snapshot_v2 = kwargs["quote_snapshot_v2"]
		return SimpleNamespace(id=101, snapshot_code="QS2-2026-0001")

	from services import intake_v6_quote_snapshot_v2_service as svc

	orig = svc._persist_snapshot
	try:
		svc._persist_snapshot = capture_persist  # type: ignore[method-assign]
		await snapshot_service.create_v6_quote_snapshot_v2(
			db,
			quote_id=6,
			workspace_id="workspace-v6",
			expected_grand_total=1190.0,
			created_by="test@example.com",
		)
	finally:
		svc._persist_snapshot = orig  # type: ignore[method-assign]

	assert db.quote_snapshot_v2.product_aggregate_snapshot is not None
	assert db.quote_snapshot_v2.product_aggregate_snapshot.composition_graph is not None
	assert db.quote_snapshot_v2.product_aggregate_snapshot.composition_graph.root_template_code == "TPL-VOLUMETRIC-LETTERS_v2"


def test_apply_v6_commercial_first_readiness_promotes_internal_block() -> None:
	snap = _canonical(internal_status="blocked", readiness="blocked_missing_internal")
	adjusted = snapshot_service._apply_v6_commercial_first_readiness(snap)
	assert adjusted.readiness == "partial_with_owner_decisions"


def test_validate_rejects_hard_blocked_readiness() -> None:
	snap = _canonical(readiness="blocked_missing_commercial", commercial_status="blocked")
	blockers = snapshot_service._validate_canonical_snapshot(
		snap,
		quote_grand_total=1190.0,
		quote_total_before_vat=1000.0,
	)
	codes = {b["code"] for b in blockers}
	assert snapshot_service.V6_SNAPSHOT_COMMERCIAL_AUTHORITY_BLOCKED in codes
	assert snapshot_service.V6_SNAPSHOT_READINESS_BLOCKED in codes
