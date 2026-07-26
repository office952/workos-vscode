"""Tests for Order Snapshot V2 component-scope passthrough from Quote Snapshot V2."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from models.orders import Orders
from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from schemas.order_snapshot_v2 import OrderSnapshotV2
from schemas.product_aggregate import ProductAggregate, ProductAggregateComponent, ProductAggregateTaskContract
from schemas.quote_snapshot_v2 import (
    COMPONENT_SCOPE_VERSION,
    QuoteSnapshotComponentInstance,
    QuoteSnapshotGeometryInput,
    QuoteSnapshotOfferScope,
    QuoteSnapshotV2,
)
from services.intake_v6_product_composition_recommendation_service import LOGO_TEMPLATE_CODE
from services.intake_v6_quote_to_order_service import accept_v6_quote, convert_v6_quote_to_order
from services.order_snapshot_v2_convert_service import (
    _build_order_snapshot_v2,
    _component_scope_fields_from_quote,
)
from tests.test_order_snapshot_v2_convert import _valid_convert_body
from tests.test_quote_snapshot_v2_accept_gate import (
    _commercial_preview,
    _insert_snapshot,
    _internal_preview,
    _seed_v6_quote,
    _test_user,
    _valid_accept_body,
)

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
LOGO = LOGO_TEMPLATE_CODE


@pytest.fixture(autouse=True)
def no_workspace_critical_blockers(monkeypatch):
    async def _empty(*args, **kwargs):
        return []

    monkeypatch.setattr(
        "services.intake_v6_quote_to_order_service._collect_accept_critical_blockers",
        _empty,
    )


def _offer_scope(*, mode: str, sold: list[str], runtime: list[str], use_legacy: bool) -> QuoteSnapshotOfferScope:
    return QuoteSnapshotOfferScope(
        mode=mode,  # type: ignore[arg-type]
        sold_modules=sold,
        resolved_runtime_sold_modules=runtime,
        use_legacy=use_legacy,
    )


def _minimal_aggregate(*, component_ids: list[str]) -> ProductAggregate:
    return ProductAggregate(
        template_code=TEMPLATE,
        template_id=1,
        components=[
            ProductAggregateComponent(component_id=cid, mini_module_code="debitare_fata")
            for cid in component_ids
        ],
        task_contract=ProductAggregateTaskContract(task_rules=[]),
    )


def _component_instances_for_subset(sold: list[str], runtime: list[str]) -> list[QuoteSnapshotComponentInstance]:
    instances = [
        QuoteSnapshotComponentInstance(
            instance_id="comp_face_litere",
            canonical_component_code="FACE",
            runtime_module_code="debitare_fata",
            source_template_code=TEMPLATE,
            classification="sold" if "FACE" in sold else "calc_only",
        ),
        QuoteSnapshotComponentInstance(
            instance_id="comp_lateral_litere",
            canonical_component_code="RETURN-CANT",
            runtime_module_code="modelare_cant",
            source_template_code=TEMPLATE,
            classification="sold" if "RETURN-CANT" in sold else "calc_only",
        ),
        QuoteSnapshotComponentInstance(
            instance_id="comp_spate_litere",
            canonical_component_code="BACK",
            runtime_module_code="debitare_spate",
            source_template_code=TEMPLATE,
            classification="sold" if "BACK" in sold else "calc_only",
        ),
    ]
    if sold == []:
        for item in instances:
            item.classification = "sold"
    return instances


def _linked_logo_instances() -> list[QuoteSnapshotComponentInstance]:
    return [
        QuoteSnapshotComponentInstance(
            instance_id="comp_face_litere::logo_instance_001",
            canonical_component_code="FACE",
            runtime_module_code="debitare_fata",
            source_template_code=LOGO,
            segment_key="logo_instance_001",
            classification="linked_neutral",
        ),
        QuoteSnapshotComponentInstance(
            instance_id="comp_face_litere::logo_instance_002",
            canonical_component_code="FACE",
            runtime_module_code="debitare_fata",
            source_template_code=LOGO,
            segment_key="logo_instance_002",
            classification="linked_neutral",
        ),
    ]


def _geometry_snapshot() -> QuoteSnapshotGeometryInput:
    return QuoteSnapshotGeometryInput(
        quote_geometry={"letter_count": 5, "letter_face_area_m2": 1.2},
        svg_source={"file_name": "test.svg"},
        analysis_ready=True,
        workspace_payload_hash="abc123",
    )


async def _insert_scoped_snapshot(
    db,
    *,
    quote_id: int,
    workspace_id: str,
    offer_scope: QuoteSnapshotOfferScope,
    component_instances: list[QuoteSnapshotComponentInstance],
    aggregate: ProductAggregate | None = None,
) -> QuoteSnapshotV2Record:
    snapshot = QuoteSnapshotV2(
        quote_id=str(quote_id),
        workspace_id=workspace_id,
        template_code=TEMPLATE,
        component_scope_version=COMPONENT_SCOPE_VERSION,
        offer_scope_snapshot=offer_scope,
        component_instances=component_instances,
        geometry_input_snapshot=_geometry_snapshot(),
        product_aggregate_snapshot=aggregate,
        commercial_price_proposal_snapshot=_commercial_preview(),
        estimated_internal_cost_snapshot=_internal_preview(),
        readiness="ready_for_owner_review",
        persist_status="persisted",
    )
    snapshot_json = snapshot.model_dump_json()
    record = QuoteSnapshotV2Record(
        snapshot_code=f"QSN2-SCOPE-{uuid.uuid4().hex[:8]}",
        snapshot_version="1.0.0",
        version=1,
        quote_id=quote_id,
        workspace_id=workspace_id,
        template_code=TEMPLATE,
        status="frozen",
        readiness="ready_for_owner_review",
        frozen_at=datetime.now(timezone.utc),
        frozen_by="test",
        snapshot_json=snapshot_json,
        content_hash=hashlib.sha256(snapshot_json.encode()).hexdigest()[:32],
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def _accept_and_convert(db, quote_id: int) -> OrderSnapshotV2:
    await accept_v6_quote(db, quote_id, _valid_accept_body(), _test_user())
    result = await convert_v6_quote_to_order(
        db,
        quote_id,
        _valid_convert_body(),
        _test_user(),
    )
    order = await db.get(Orders, result["order_id"])
    assert order is not None
    return OrderSnapshotV2.model_validate_json(order.snapshot_v2_json)


def _quote_record(record: QuoteSnapshotV2Record) -> QuoteSnapshotV2:
    return QuoteSnapshotV2.model_validate_json(record.snapshot_json)


@pytest.mark.parametrize(
    ("sold", "runtime", "use_legacy"),
    [
        ([], [], True),
        (["FACE"], ["debitare_fata"], False),
        (["RETURN-CANT"], ["modelare_cant"], False),
        (["BACK"], ["debitare_spate"], False),
        (["FACE", "RETURN-CANT"], ["debitare_fata", "modelare_cant"], False),
    ],
)
@pytest.mark.asyncio
async def test_quote_to_order_preserves_component_scope(
    volumetric_v2_db,
    sold: list[str],
    runtime: list[str],
    use_legacy: bool,
) -> None:
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    mode = "full_product" if use_legacy else "component_subset"
    offer_scope = _offer_scope(mode=mode, sold=sold, runtime=runtime, use_legacy=use_legacy)
    instances = _component_instances_for_subset(sold, runtime)
    aggregate = _minimal_aggregate(component_ids=[i.instance_id for i in instances if "::" not in i.instance_id])
    record = await _insert_scoped_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
        offer_scope=offer_scope,
        component_instances=instances,
        aggregate=aggregate,
    )
    quote_snapshot = _quote_record(record)
    order_snapshot = await _accept_and_convert(volumetric_v2_db, quote.id)

    assert order_snapshot.component_scope_version == COMPONENT_SCOPE_VERSION
    assert order_snapshot.offer_scope_snapshot == quote_snapshot.offer_scope_snapshot
    assert order_snapshot.component_instances == quote_snapshot.component_instances
    assert order_snapshot.geometry_input_snapshot == quote_snapshot.geometry_input_snapshot
    assert order_snapshot.product_aggregate_snapshot == quote_snapshot.product_aggregate_snapshot
    assert order_snapshot.offer_scope_snapshot.sold_modules == sold
    assert order_snapshot.offer_scope_snapshot.resolved_runtime_sold_modules == runtime


@pytest.mark.asyncio
async def test_linked_logo_neutral_instances_preserved(volumetric_v2_db) -> None:
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    instances = _component_instances_for_subset([], []) + _linked_logo_instances()
    aggregate = _minimal_aggregate(
        component_ids=[
            "comp_face_litere",
            "comp_face_litere::logo_instance_001",
            "comp_face_litere::logo_instance_002",
        ]
    )
    offer_scope = _offer_scope(mode="full_product", sold=[], runtime=[], use_legacy=True)
    record = await _insert_scoped_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
        offer_scope=offer_scope,
        component_instances=instances,
        aggregate=aggregate,
    )
    quote_snapshot = _quote_record(record)
    order_snapshot = await _accept_and_convert(volumetric_v2_db, quote.id)

    linked = [i for i in order_snapshot.component_instances if i.classification == "linked_neutral"]
    assert len(linked) == 2
    assert {i.segment_key for i in linked} == {"logo_instance_001", "logo_instance_002"}
    assert order_snapshot.component_instances == quote_snapshot.component_instances


@pytest.mark.asyncio
async def test_legacy_quote_snapshot_converts_without_scope(volumetric_v2_db) -> None:
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    await _insert_snapshot(volumetric_v2_db, quote_id=quote.id, workspace_id=workspace_id)
    order_snapshot = await _accept_and_convert(volumetric_v2_db, quote.id)

    assert order_snapshot.offer_scope_snapshot is None
    assert order_snapshot.component_instances == []
    assert order_snapshot.geometry_input_snapshot is None
    assert order_snapshot.component_scope_version is None


def test_component_scope_fields_copy_verbatim() -> None:
    offer_scope = _offer_scope(
        mode="component_subset",
        sold=["FACE"],
        runtime=["debitare_fata"],
        use_legacy=False,
    )
    parsed = QuoteSnapshotV2(
        template_code=TEMPLATE,
        component_scope_version=COMPONENT_SCOPE_VERSION,
        offer_scope_snapshot=offer_scope,
        component_instances=_component_instances_for_subset(["FACE"], ["debitare_fata"]),
        geometry_input_snapshot=_geometry_snapshot(),
        product_aggregate_snapshot=_minimal_aggregate(component_ids=["comp_face_litere"]),
        commercial_price_proposal_snapshot=_commercial_preview(),
        estimated_internal_cost_snapshot=_internal_preview(),
    )
    copied = _component_scope_fields_from_quote(parsed)
    assert copied["offer_scope_snapshot"] == offer_scope
    assert copied["component_instances"] == parsed.component_instances
    assert copied["geometry_input_snapshot"] == parsed.geometry_input_snapshot
    assert copied["product_aggregate_snapshot"] == parsed.product_aggregate_snapshot


@pytest.mark.asyncio
async def test_convert_does_not_rerun_resolver_or_rebuild_aggregate(volumetric_v2_db, monkeypatch) -> None:
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    await _insert_scoped_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
        offer_scope=_offer_scope(mode="full_product", sold=[], runtime=[], use_legacy=True),
        component_instances=_component_instances_for_subset([], []),
        aggregate=_minimal_aggregate(component_ids=["comp_face_litere"]),
    )

    resolver_mock = MagicMock(side_effect=AssertionError("resolver must not run at order convert"))
    scope_mock = AsyncMock(side_effect=AssertionError("aggregate rebuild must not run at order convert"))
    monkeypatch.setattr(
        "services.offer_scope_resolver_service.resolve_offer_scope",
        resolver_mock,
    )
    monkeypatch.setattr(
        "services.quote_snapshot_component_scope_service.build_frozen_component_scope",
        scope_mock,
    )

    order_snapshot = await _accept_and_convert(volumetric_v2_db, quote.id)
    assert order_snapshot.product_aggregate_snapshot is not None
    resolver_mock.assert_not_called()
    scope_mock.assert_not_called()


@pytest.mark.asyncio
async def test_pricing_unchanged_on_convert(volumetric_v2_db) -> None:
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db, grand_total=999.0)
    await _insert_scoped_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
        offer_scope=_offer_scope(mode="full_product", sold=[], runtime=[], use_legacy=True),
        component_instances=[],
        aggregate=_minimal_aggregate(component_ids=["comp_face_litere"]),
    )
    record = await volumetric_v2_db.scalar(
        select(QuoteSnapshotV2Record).where(QuoteSnapshotV2Record.quote_id == quote.id)
    )
    parsed = QuoteSnapshotV2.model_validate_json(record.snapshot_json)
    expected_total = parsed.commercial_price_proposal_snapshot.commercial_total

    order_snapshot = await _accept_and_convert(volumetric_v2_db, quote.id)
    order = await volumetric_v2_db.get(Orders, order_snapshot.order_id)

    assert order_snapshot.accepted_commercial_total == expected_total
    assert float(order.total_amount) == expected_total


def test_build_order_snapshot_v2_unit_passthrough() -> None:
    offer_scope = _offer_scope(
        mode="component_subset",
        sold=["BACK"],
        runtime=["debitare_spate"],
        use_legacy=False,
    )
    parsed = QuoteSnapshotV2(
        template_code=TEMPLATE,
        component_scope_version=COMPONENT_SCOPE_VERSION,
        offer_scope_snapshot=offer_scope,
        component_instances=_component_instances_for_subset(["BACK"], ["debitare_spate"]),
        geometry_input_snapshot=_geometry_snapshot(),
        product_aggregate_snapshot=_minimal_aggregate(component_ids=["comp_spate_litere"]),
        commercial_price_proposal_snapshot=_commercial_preview(total=2000.0),
        estimated_internal_cost_snapshot=_internal_preview(),
    )
    record = SimpleNamespace(snapshot_code="OSN-1", content_hash="hash", id=42)
    quote = SimpleNamespace(id=7)
    user = SimpleNamespace(name="Tester", email="test@example.com")
    order = _build_order_snapshot_v2(
        quote=quote,
        record=record,
        parsed=parsed,
        commercial_total=2000.0,
        currency="RON",
        linkage={},
        current_user=user,
        order_id=99,
    )
    assert order.offer_scope_snapshot == offer_scope
    assert order.component_scope_version == COMPONENT_SCOPE_VERSION
    assert order.accepted_commercial_total == 2000.0
