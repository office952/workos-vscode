"""Tests for shared Quote Snapshot component-scope freeze helper."""

from __future__ import annotations

import copy
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy import func, select

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from schemas.quote_snapshot_v2 import COMPONENT_SCOPE_VERSION, QUOTE_SNAPSHOT_V2_VERSION, QuoteSnapshotV2
from services.intake_v6_quote_snapshot_v2_service import (
    V6_SNAPSHOT_OFFER_SCOPE_INVALID,
    create_v6_quote_snapshot_v2,
)
from services.product_aggregate_service import ProductAggregateService
from services.product_aggregate_workspace_composition_service import SEGMENT_NAMESPACE_SEP
from services.quote_snapshot_component_scope_service import build_frozen_component_scope
from services.quote_snapshot_v2_service import QuoteSnapshotV2Service
from services.estimated_internal_cost_service import EstimatedInternalCostService
from services.intake_v6_product_composition_recommendation_service import LOGO_TEMPLATE_CODE as LOGO
from tests.eic_workspace_logo_fixtures import (
    LOGO_INSTANCE_A,
    LOGO_INSTANCE_B,
    add_workspace,
    confirmed_bindings_payload,
    quote_input_overlay,
    seed_logo_inventory_materials,
    seed_logo_template,
)
from tests.test_aggregate_cost_bom_adapter import INVENTORY_CATALOG
from tests.test_quote_snapshot_v2 import (
    SAMPLE_RATES as QS_SAMPLE_RATES,
    TEMPLATE,
    _full_quote_input,
    _seed_workspace,
)

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

ROOT = TEMPLATE


def _with_offer_scope(base: dict, *, mode: str, sold: list[str]) -> dict:
    out = copy.deepcopy(base)
    out["offer_scope"] = {
        "contract_version": "offer_scope_contract/v1",
        "mode": mode,
        "sold_modules": sold,
    }
    return out


@pytest_asyncio.fixture
async def logo_workspace_db(volumetric_v2_db):
    await seed_logo_template(volumetric_v2_db)
    await seed_logo_inventory_materials(volumetric_v2_db)
    workspace_id = await add_workspace(volumetric_v2_db, confirmed_bindings_payload())
    return volumetric_v2_db, workspace_id


@pytest_asyncio.fixture
async def snapshot_service(volumetric_v2_db):
    service = EstimatedInternalCostService(volumetric_v2_db)

    async def _patched_load():
        return QS_SAMPLE_RATES, {"RON": "RON"}, {"WC_CNC_ROUTING": 120.0}, INVENTORY_CATALOG

    service._load_pricing_context = _patched_load  # type: ignore[method-assign]
    yield QuoteSnapshotV2Service(volumetric_v2_db, eic_service=service)


@pytest.fixture
def allow_freeze_readiness(monkeypatch):
    def _allowed(commercial, internal):
        if commercial.forbidden_hourly_usage_detected or internal.hourly_contamination_detected:
            return "blocked_forbidden_path"
        return "partial_with_owner_decisions"

    monkeypatch.setattr(
        "services.quote_snapshot_v2_service.compute_readiness",
        _allowed,
    )


@pytest.mark.asyncio
async def test_workspace_payload_offer_scope_without_quote_input(volumetric_v2_db) -> None:
    workspace_id = await _seed_workspace(volumetric_v2_db)
    record = await volumetric_v2_db.get(IntakeV6WorkspaceRecord, workspace_id)
    assert record is not None
    payload = json.loads(record.payload_json)
    payload["offer_scope"] = {
        "contract_version": "offer_scope_contract/v1",
        "mode": "component_subset",
        "sold_modules": ["FACE"],
    }
    record.payload_json = json.dumps(payload)
    await volumetric_v2_db.commit()

    scope = await build_frozen_component_scope(
        volumetric_v2_db,
        template_code=ROOT,
        workspace_id=workspace_id,
    )
    assert scope is not None
    assert scope.offer_scope_snapshot.sold_modules == ["FACE"]
    assert scope.offer_scope_snapshot.resolved_runtime_sold_modules == ["debitare_fata"]


@pytest.mark.asyncio
async def test_no_offer_scope_legacy_full_product_scope(volumetric_v2_db) -> None:
    workspace_id = await _seed_workspace(volumetric_v2_db)
    scope = await build_frozen_component_scope(
        volumetric_v2_db,
        template_code=ROOT,
        workspace_id=workspace_id,
        quote_input=_full_quote_input(),
    )
    assert scope is not None
    assert scope.offer_scope_snapshot.use_legacy is True
    assert scope.offer_scope_snapshot.mode == "full_product"
    assert scope.offer_scope_snapshot.validation_errors == []


@pytest.mark.asyncio
async def test_explicit_full_product_equivalent_scope(volumetric_v2_db) -> None:
    workspace_id = await _seed_workspace(volumetric_v2_db)
    qi = _with_offer_scope(_full_quote_input(), mode="full_product", sold=[])
    scope = await build_frozen_component_scope(
        volumetric_v2_db,
        template_code=ROOT,
        workspace_id=workspace_id,
        quote_input=qi,
    )
    assert scope is not None
    assert scope.offer_scope_snapshot.use_legacy is True
    assert scope.offer_scope_snapshot.mode == "full_product"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("sold", "expected_runtime"),
    [
        (["FACE"], ["debitare_fata"]),
        (["RETURN-CANT"], ["modelare_cant"]),
        (["BACK"], ["debitare_spate"]),
        (["FACE", "RETURN-CANT"], ["debitare_fata", "modelare_cant"]),
    ],
)
async def test_component_subset_freezes_runtime_modules(
    volumetric_v2_db,
    sold: list[str],
    expected_runtime: list[str],
) -> None:
    workspace_id = await _seed_workspace(volumetric_v2_db)
    qi = _with_offer_scope(_full_quote_input(), mode="component_subset", sold=sold)
    scope = await build_frozen_component_scope(
        volumetric_v2_db,
        template_code=ROOT,
        workspace_id=workspace_id,
        quote_input=qi,
    )
    assert scope is not None
    assert scope.offer_scope_snapshot.use_legacy is False
    assert scope.offer_scope_snapshot.sold_modules == sold
    assert scope.offer_scope_snapshot.resolved_runtime_sold_modules == expected_runtime
    assert scope.product_aggregate is not None


@pytest.mark.asyncio
async def test_linked_logo_full_product_preserves_neutral_instances(logo_workspace_db) -> None:
    db, workspace_id = logo_workspace_db
    scope = await build_frozen_component_scope(
        db,
        template_code=ROOT,
        workspace_id=workspace_id,
        quote_input=quote_input_overlay(confirmed_bindings_payload()),
    )
    assert scope is not None
    component_ids = {c.component_id for c in scope.product_aggregate.components}
    assert any(LOGO_INSTANCE_A in cid for cid in component_ids)
    assert any(LOGO_INSTANCE_B in cid for cid in component_ids)
    assert any(SEGMENT_NAMESPACE_SEP in cid for cid in component_ids)

    linked = [i for i in scope.component_instances if i.classification == "linked_neutral"]
    assert len(linked) >= 2
    segment_keys = {i.segment_key for i in linked}
    assert LOGO_INSTANCE_A in segment_keys
    assert LOGO_INSTANCE_B in segment_keys
    logo_sources = {i.source_template_code for i in linked}
    assert LOGO in logo_sources


@pytest.mark.asyncio
async def test_face_only_marks_calc_only_letter_components(volumetric_v2_db) -> None:
    workspace_id = await _seed_workspace(volumetric_v2_db)
    qi = _with_offer_scope(_full_quote_input(), mode="component_subset", sold=["FACE"])
    scope = await build_frozen_component_scope(
        volumetric_v2_db,
        template_code=ROOT,
        workspace_id=workspace_id,
        quote_input=qi,
    )
    assert scope is not None
    by_class = {i.instance_id: i.classification for i in scope.component_instances}
    assert any(cls == "sold" for cls in by_class.values())
    assert any(cls == "calc_only" for cls in by_class.values())


@pytest.mark.asyncio
async def test_invalid_subset_has_validation_errors(volumetric_v2_db) -> None:
    workspace_id = await _seed_workspace(volumetric_v2_db)
    qi = _with_offer_scope(_full_quote_input(), mode="component_subset", sold=[])
    scope = await build_frozen_component_scope(
        volumetric_v2_db,
        template_code=ROOT,
        workspace_id=workspace_id,
        quote_input=qi,
    )
    assert scope is not None
    assert scope.offer_scope_snapshot.validation_errors


@pytest.mark.asyncio
async def test_invalid_subset_blocks_path_a_freeze(
    snapshot_service,
    volumetric_v2_db,
    allow_freeze_readiness,
) -> None:
    workspace_id = await _seed_workspace(volumetric_v2_db)
    qi = _with_offer_scope(_full_quote_input(), mode="component_subset", sold=["LIGHTING"])
    before = await volumetric_v2_db.scalar(select(func.count()).select_from(QuoteSnapshotV2Record))
    snapshot = await snapshot_service.freeze(
        ROOT,
        workspace_id=workspace_id,
        quote_input=qi,
        frozen_by="test",
    )
    assert snapshot is not None
    assert snapshot.readiness == "blocked_snapshot_conflict"
    assert snapshot.persist_status == "blocked"
    after = await volumetric_v2_db.scalar(select(func.count()).select_from(QuoteSnapshotV2Record))
    assert after == before


@pytest.mark.asyncio
async def test_snapshot_reread_does_not_rerun_resolver(
    snapshot_service,
    volumetric_v2_db,
    allow_freeze_readiness,
) -> None:
    workspace_id = await _seed_workspace(volumetric_v2_db)
    qi = _with_offer_scope(_full_quote_input(), mode="component_subset", sold=["FACE"])
    snapshot = await snapshot_service.freeze(
        ROOT,
        workspace_id=workspace_id,
        quote_input=qi,
        frozen_by="test",
    )
    assert snapshot is not None and snapshot.persist_status == "persisted"
    frozen_runtime = list(snapshot.offer_scope_snapshot.resolved_runtime_sold_modules)

    record = await volumetric_v2_db.scalar(
        select(QuoteSnapshotV2Record).where(
            QuoteSnapshotV2Record.snapshot_code == snapshot.snapshot_code
        )
    )
    loaded = QuoteSnapshotV2.model_validate_json(record.snapshot_json)
    assert loaded.offer_scope_snapshot.resolved_runtime_sold_modules == frozen_runtime


@pytest.mark.asyncio
async def test_old_snapshot_json_deserializes() -> None:
    legacy = {
        "snapshot_version": QUOTE_SNAPSHOT_V2_VERSION,
        "template_code": ROOT,
        "commercial_price_proposal_snapshot": {
            "template_code": ROOT,
            "status": "ready",
            "commercial_price_lines": [],
            "currency": "RON",
            "provenance": [],
            "confidence": "high",
            "quote_ready_for_commercial_review": True,
            "notes": [],
        },
        "estimated_internal_cost_snapshot": {
            "template_code": ROOT,
            "status": "ready",
            "currency": "RON",
            "provenance": [],
            "completeness": 1.0,
            "confidence": "medium",
            "ready_for_quote_snapshot": True,
            "notes": [],
        },
    }
    parsed = QuoteSnapshotV2.model_validate(legacy)
    assert parsed.offer_scope_snapshot is None
    assert parsed.component_instances == []
    assert parsed.component_scope_version is None


@pytest.mark.asyncio
async def test_workspace_aggregate_parity_with_bom_builder(logo_workspace_db) -> None:
    from services.aggregate_cost_bom_adapter import AggregateCostBomBuilderService

    db, workspace_id = logo_workspace_db
    scope = await build_frozen_component_scope(
        db,
        template_code=ROOT,
        workspace_id=workspace_id,
        quote_input=quote_input_overlay(confirmed_bindings_payload()),
    )
    bom_agg = await ProductAggregateService(db).build_for_workspace(ROOT, workspace_id)
    assert scope is not None and bom_agg is not None
    scope_ids = {c.component_id for c in scope.product_aggregate.components}
    assert scope_ids == {c.component_id for c in bom_agg.components}
    bom = await AggregateCostBomBuilderService(db).build_preview(ROOT, workspace_id=workspace_id)
    assert bom is not None


@pytest.mark.asyncio
async def test_no_commercial_total_regression(snapshot_service, volumetric_v2_db) -> None:
    baseline = await snapshot_service.build_preview(ROOT, quote_input=_full_quote_input())
    workspace_id = await _seed_workspace(volumetric_v2_db)
    with_workspace = await snapshot_service.build_preview(
        ROOT,
        workspace_id=workspace_id,
        quote_input=_full_quote_input(),
    )
    assert baseline is not None and with_workspace is not None
    assert baseline.commercial_price_proposal_snapshot.commercial_total == (
        with_workspace.commercial_price_proposal_snapshot.commercial_total
    )
    assert with_workspace.component_scope_version == COMPONENT_SCOPE_VERSION
    assert with_workspace.offer_scope_snapshot is not None
    assert with_workspace.product_aggregate_snapshot is not None


@pytest.mark.asyncio
async def test_intake_v6_official_snapshot_includes_aggregate_and_scope(
    logo_workspace_db,
    monkeypatch,
) -> None:
    from services import intake_v6_quote_snapshot_v2_service as v6_snap

    db, workspace_id = logo_workspace_db
    captured: dict = {}

    async def _capture_persist(
        _db,
        *,
        quote_obj,
        snapshot_payload,
        commercial,
        client_output,
        created_by,
        content_hash,
        quote_snapshot_v2,
    ):
        captured["snapshot"] = quote_snapshot_v2
        return SimpleNamespace(id=501, snapshot_code="QS2-2026-0501")

    monkeypatch.setattr(v6_snap, "_persist_snapshot", _capture_persist)
    monkeypatch.setattr(v6_snap, "_snapshot_count", AsyncMock(return_value=0))
    monkeypatch.setattr(v6_snap, "_order_count", AsyncMock(return_value=0))

    notes = json.dumps(
        {
            "intake_v6_linkage_v1": {
                "source_workspace_id": workspace_id,
                "template_code": ROOT,
                "pricing_source": "intake_v6_backend_priced_dry_run",
                "intake_v6_priced_quote_write_v1": {
                    "pricing_input_trace": quote_input_overlay(confirmed_bindings_payload()),
                    "internal_cost_trace_summary": {"estimated_cost_total": 100.0, "currency": "EUR"},
                    "no_v4_v2_commercial_truth": True,
                    "frontend_preview_not_used": True,
                },
            }
        }
    )
    quote = SimpleNamespace(
        id=99,
        code="Q-V6-TEST",
        intake_code=f"IV6-{workspace_id}",
        client_id=1,
        client_name="Test",
        status="priced",
        line_items=json.dumps(
            [{"name": "Line", "total": 100.0, "unit_price": 100.0, "quantity": 1, "unit": "buc"}]
        ),
        subtotal=100.0,
        discount=0.0,
        total_before_vat=100.0,
        vat=19.0,
        grand_total=119.0,
        margin_pct=0.0,
        valid_until=None,
        created_at=None,
        notes=notes,
    )

    class _Quotes:
        async def get_by_id(self, _quote_id):
            return quote

    monkeypatch.setattr(v6_snap, "QuotesService", lambda _db: _Quotes())

    result = await create_v6_quote_snapshot_v2(
        db,
        quote_id=99,
        workspace_id=workspace_id,
        expected_grand_total=119.0,
    )
    assert result["status"] == v6_snap.V6_QUOTE_SNAPSHOT_V2_CREATED
    snap = captured["snapshot"]
    assert snap.product_aggregate_snapshot is not None
    assert snap.offer_scope_snapshot is not None
    assert snap.component_scope_version == COMPONENT_SCOPE_VERSION
    assert snap.commercial_price_proposal_snapshot.commercial_total == 119.0


@pytest.mark.asyncio
async def test_intake_v6_invalid_offer_scope_blocks(monkeypatch, volumetric_v2_db) -> None:
    from services import intake_v6_quote_snapshot_v2_service as v6_snap

    workspace_id = await _seed_workspace(volumetric_v2_db)
    notes = json.dumps(
        {
            "intake_v6_linkage_v1": {
                "source_workspace_id": workspace_id,
                "template_code": ROOT,
                "pricing_source": "intake_v6_backend_priced_dry_run",
                "intake_v6_priced_quote_write_v1": {
                    "pricing_input_trace": _with_offer_scope(
                        _full_quote_input(),
                        mode="component_subset",
                        sold=[],
                    ),
                    "internal_cost_trace_summary": {"estimated_cost_total": 100.0},
                    "no_v4_v2_commercial_truth": True,
                    "frontend_preview_not_used": True,
                },
            }
        }
    )
    quote = SimpleNamespace(
        id=100,
        code="Q-V6-BLOCK",
        intake_code=f"IV6-{workspace_id}",
        client_id=1,
        client_name="Test",
        status="priced",
        line_items=json.dumps([{"name": "Line", "total": 100.0, "unit_price": 100.0, "quantity": 1}]),
        subtotal=100.0,
        discount=0.0,
        total_before_vat=100.0,
        vat=19.0,
        grand_total=119.0,
        margin_pct=0.0,
        valid_until=None,
        created_at=None,
        notes=notes,
    )

    class _Quotes:
        async def get_by_id(self, _quote_id):
            return quote

    monkeypatch.setattr(v6_snap, "QuotesService", lambda _db: _Quotes())
    monkeypatch.setattr(v6_snap, "_snapshot_count", AsyncMock(return_value=0))
    monkeypatch.setattr(v6_snap, "_order_count", AsyncMock(return_value=0))

    result = await create_v6_quote_snapshot_v2(
        volumetric_v2_db,
        quote_id=100,
        workspace_id=workspace_id,
        expected_grand_total=119.0,
    )
    assert result["status"] == v6_snap.V6_QUOTE_SNAPSHOT_V2_BLOCKED
    assert V6_SNAPSHOT_OFFER_SCOPE_INVALID in {b["code"] for b in result["blockers"]}
