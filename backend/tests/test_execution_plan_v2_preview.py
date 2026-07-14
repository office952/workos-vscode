"""Tests for ExecutionPlan V2 preview (Step 9.3.2)."""

from __future__ import annotations

import ast
import hashlib
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from schemas.execution_plan_v2 import EXECUTION_PLAN_V2_SOURCE, IGNORED_PRICING_SOURCES
from schemas.order_snapshot_v2 import OrderSnapshotV2
from schemas.product_aggregate import (
    ProductAggregate,
    ProductAggregateOperation,
    ProductAggregateTaskContract,
    ProductAggregateTaskRule,
)
from schemas.product_definition import (
    ProductDefinitionOperationRole,
    ProductDefinitionPreview,
    ProductDefinitionSourceContext,
)
from services.execution_plan_v2_preview_service import (
    FORBIDDEN_IMPORT_SUBSTRINGS,
    ExecutionPlanV2PreviewOrderNotFound,
    build_execution_plan_v2_preview,
)
from tests.test_execution_plan_v2_source_metadata import (
    _seed_legacy_order,
    _seed_v2_order_by_json,
)
from tests.test_quote_snapshot_v2_accept_gate import (
    _commercial_preview,
    _insert_snapshot,
    _internal_preview,
    _seed_v6_quote,
    _test_user,
    _valid_accept_body,
)
from tests.test_order_snapshot_v2_convert import _valid_convert_body as _convert_body
from services.intake_v6_quote_to_order_service import accept_v6_quote, convert_v6_quote_to_order
from tests.execution_sold_scope_fixtures import offer_scope, snapshot_with_scope

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]


@pytest.fixture(autouse=True)
def no_workspace_critical_blockers(monkeypatch):
    async def _empty(*args, **kwargs):
        return []

    monkeypatch.setattr(
        "services.intake_v6_quote_to_order_service._collect_accept_critical_blockers",
        _empty,
    )

BACKEND_ROOT = Path(__file__).resolve().parents[1]
STEP_9_3_2_PATHS = (
    BACKEND_ROOT / "schemas" / "execution_plan_v2.py",
    BACKEND_ROOT / "services" / "execution_plan_v2_preview_service.py",
    BACKEND_ROOT / "routers" / "execution_plan_v2.py",
    Path(__file__).resolve(),
)

STEP_9_3_2_CODE_PATHS = STEP_9_3_2_PATHS[:-1]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


def _forbidden_imports_in_paths() -> set[str]:
    found: set[str] = set()
    for path in STEP_9_3_2_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for part in FORBIDDEN_IMPORT_SUBSTRINGS:
                    if part in node.module:
                        found.add(node.module)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for part in FORBIDDEN_IMPORT_SUBSTRINGS:
                        if part in alias.name:
                            found.add(alias.name)
    return found


def _sample_aggregate(*, include_task_rules: bool = True) -> ProductAggregate:
    rules = []
    if include_task_rules:
        rules = [
            ProductAggregateTaskRule(
                task_name="cnc_face_cut",
                task_type="cnc_routing",
                priced_operation="face_cnc_cut",
                sequence=2,
            ),
            ProductAggregateTaskRule(
                task_name="electrical_wiring",
                task_type="led_wiring",
                priced_operation="electrical_letters",
                sequence=9,
            ),
        ]
    return ProductAggregate(
        template_code=TEMPLATE,
        template_id=1,
        operations=[
            ProductAggregateOperation(
                operation_code="face_cnc_cut",
                label="Face CNC Cut",
                workcenter="WC_CNC",
            ),
            ProductAggregateOperation(
                operation_code="electrical_letters",
                label="Electrical Wiring",
                workcenter="WC_ELECTRICAL",
            ),
        ],
        task_contract=ProductAggregateTaskContract(task_rules=rules),
    )


def _sample_product_definition() -> ProductDefinitionPreview:
    return ProductDefinitionPreview(
        template_code=TEMPLATE,
        source_context=ProductDefinitionSourceContext(template_code=TEMPLATE),
        operation_roles=[
            ProductDefinitionOperationRole(
                operation_code="face_cnc_cut",
                label="Face CNC Cut",
                workcenter="WC_CNC",
            ),
            ProductDefinitionOperationRole(
                operation_code="electrical_letters",
                label="Electrical Wiring",
                workcenter="WC_ELECTRICAL",
            ),
        ],
    )


def _build_order_snapshot_v2_json(
    *,
    quote_id: int = 1,
    quote_snapshot_v2_id: int = 1,
    include_product_definition: bool = True,
    include_product_aggregate: bool = True,
    include_task_rules: bool = True,
) -> str:
    snapshot = OrderSnapshotV2(
        quote_id=quote_id,
        quote_snapshot_v2_id=quote_snapshot_v2_id,
        snapshot_code="OSN2-TEST-001",
        content_hash="abc123def456abc123def456abc123de",
        product_definition_snapshot=_sample_product_definition()
        if include_product_definition
        else None,
        product_aggregate_snapshot=_sample_aggregate(include_task_rules=include_task_rules)
        if include_product_aggregate
        else None,
        commercial_price_proposal_snapshot=_commercial_preview(total=1500.0),
        estimated_internal_cost_snapshot=_internal_preview(total=620.0),
        accepted_commercial_total=1500.0,
        accepted_currency="RON",
        estimated_internal_total=620.0,
    )
    return snapshot.model_dump_json()


async def _seed_v2_order_with_snapshot(
    db_session,
    *,
    order_id: int | None = None,
    quote_snapshot_v2_id: int | None = None,
    snapshot_v2_json: str | None = None,
    include_product_definition: bool = True,
    include_product_aggregate: bool = True,
    include_task_rules: bool = True,
) -> Orders:
    oid = order_id or (9600 + int(uuid.uuid4().hex[:4], 16) % 1000)
    qsn_id = quote_snapshot_v2_id
    if qsn_id is None:
        record = QuoteSnapshotV2Record(
            snapshot_code=f"QSN2-PREV-{oid}",
            snapshot_version="1.0.0",
            version=1,
            template_code=TEMPLATE,
            status="frozen",
            readiness="ready_for_owner_review",
            snapshot_json="{}",
            content_hash="abc123",
        )
        db_session.add(record)
        await db_session.flush()
        qsn_id = record.id

    payload_json = snapshot_v2_json
    if payload_json is None:
        payload_json = _build_order_snapshot_v2_json(
            quote_id=oid,
            quote_snapshot_v2_id=int(qsn_id),
            include_product_definition=include_product_definition,
            include_product_aggregate=include_product_aggregate,
            include_task_rules=include_task_rules,
        )

    order = Orders(
        id=oid,
        code=f"ORD-V2-PREV-{oid}",
        client_name="V2 Preview Client",
        status="locked",
        total_amount=1500.0,
        quote_id=oid,
        snapshot_line_items=None,
        quote_snapshot_v2_id=qsn_id,
        snapshot_v2_json=payload_json,
        readiness_snapshot={"execution_plan_created": False, "no_execution_plan_created": True},
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)
    return order


# ---------------------------------------------------------------------------
# 1-6. Blocked / missing inputs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cannot_preview_without_order(db_session):
    with pytest.raises(ExecutionPlanV2PreviewOrderNotFound):
        await build_execution_plan_v2_preview(db_session, 999999)


def test_cannot_preview_without_order_via_endpoint(db_fixture, auth_client):
    resp = auth_client.post("/api/v1/execution/plan-v2/preview/999999")
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"] == "order_not_found"


@pytest.mark.asyncio
async def test_cannot_preview_legacy_order_without_snapshot_v2_json(db_session):
    order = _seed_legacy_order(db_session, order_id=9701)
    await db_session.commit()
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    assert preview.status == "blocked_legacy_order"
    assert "blocked_legacy_order" in preview.blockers


@pytest.mark.asyncio
async def test_cannot_preview_v2_order_without_quote_snapshot_v2_id(db_session):
    oid = 9702
    order = Orders(
        id=oid,
        code=f"ORD-V2-NOFK-{oid}",
        client_name="No FK",
        status="locked",
        total_amount=1500.0,
        snapshot_v2_json=_build_order_snapshot_v2_json(quote_id=oid, quote_snapshot_v2_id=1),
    )
    db_session.add(order)
    await db_session.commit()
    preview = await build_execution_plan_v2_preview(db_session, oid)
    assert preview.status == "blocked_missing_quote_snapshot_v2_id"


@pytest.mark.asyncio
async def test_cannot_preview_if_snapshot_v2_json_invalid(db_session):
    oid = 9703
    record = QuoteSnapshotV2Record(
        snapshot_code=f"QSN2-INV-{oid}",
        snapshot_version="1.0.0",
        version=1,
        template_code=TEMPLATE,
        status="frozen",
        readiness="ready_for_owner_review",
        snapshot_json="{}",
        content_hash="abc123",
    )
    db_session.add(record)
    await db_session.flush()
    order = Orders(
        id=oid,
        code=f"ORD-V2-INV-{oid}",
        client_name="Invalid JSON",
        status="locked",
        total_amount=1500.0,
        quote_snapshot_v2_id=record.id,
        snapshot_v2_json="{not-json",
    )
    db_session.add(order)
    await db_session.commit()
    preview = await build_execution_plan_v2_preview(db_session, oid)
    assert preview.status == "blocked_missing_order_snapshot_v2"
    assert "SNAPSHOT_JSON_INVALID" in preview.blockers


@pytest.mark.asyncio
async def test_cannot_preview_if_product_definition_snapshot_missing(db_session):
    order = await _seed_v2_order_with_snapshot(
        db_session,
        include_product_definition=False,
        include_product_aggregate=True,
    )
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    assert preview.status == "blocked_missing_product_definition"


@pytest.mark.asyncio
async def test_cannot_preview_if_product_aggregate_snapshot_missing(db_session):
    order = await _seed_v2_order_with_snapshot(
        db_session,
        include_product_definition=True,
        include_product_aggregate=False,
    )
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    assert preview.status == "blocked_missing_product_aggregate"


# ---------------------------------------------------------------------------
# 7. Does not read snapshot_line_items
# ---------------------------------------------------------------------------


def test_preview_service_does_not_reference_snapshot_line_items():
    service_source = (BACKEND_ROOT / "services" / "execution_plan_v2_preview_service.py").read_text(
        encoding="utf-8"
    )
    assert "snapshot_line_items" not in service_source


# ---------------------------------------------------------------------------
# 8-12. No side effects / forbidden calls
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_does_not_call_execution_plan_service_from_order(db_session):
    order = await _seed_v2_order_with_snapshot(db_session)
    with patch("services.execution_plan_service.ExecutionPlanService.from_order") as mocked:
        preview = await build_execution_plan_v2_preview(db_session, order.id)
        mocked.assert_not_called()
    assert preview.planned_tasks


@pytest.mark.asyncio
async def test_does_not_call_execution_plan_gate_evaluate_gate(db_session):
    order = await _seed_v2_order_with_snapshot(db_session)
    with patch("services.execution_plan_gate_service.evaluate_gate") as mocked:
        preview = await build_execution_plan_v2_preview(db_session, order.id)
        mocked.assert_not_called()
    assert preview.status == "partial_missing_planning_minutes"


@pytest.mark.asyncio
async def test_does_not_create_execution_plan_row(db_fixture, db_session, auth_client):
    order = await _seed_v2_order_with_snapshot(db_session)
    plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    resp = auth_client.post(f"/api/v1/execution/plan-v2/preview/{order.id}")
    assert resp.status_code == 200, resp.text
    plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    assert plans_after == plans_before


@pytest.mark.asyncio
async def test_does_not_mutate_order_readiness_snapshot(db_fixture, db_session, auth_client):
    order = await _seed_v2_order_with_snapshot(db_session)
    before = dict(order.readiness_snapshot or {})
    resp = auth_client.post(f"/api/v1/execution/plan-v2/preview/{order.id}")
    assert resp.status_code == 200
    refreshed = await db_session.get(Orders, order.id)
    assert refreshed.readiness_snapshot == before


@pytest.mark.asyncio
async def test_does_not_create_tasks_or_sessions(db_fixture, db_session, auth_client):
    order = await _seed_v2_order_with_snapshot(db_session)
    plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    resp = auth_client.post(f"/api/v1/execution/plan-v2/preview/{order.id}")
    assert resp.status_code == 200
    plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    assert plans_after == plans_before
    body = resp.json()
    assert body["execution_tasks_created"] is False


# ---------------------------------------------------------------------------
# 13-17. Forbidden scope static checks
# ---------------------------------------------------------------------------


def test_does_not_call_price_endpoint():
    for path in STEP_9_3_2_CODE_PATHS:
        text = path.read_text(encoding="utf-8")
        assert '"/price"' not in text
        assert "/api/v1/price" not in text


def test_does_not_import_quote_orchestrator():
    found = _forbidden_imports_in_paths()
    assert not any("quote_orchestrator" in mod for mod in found)


def test_does_not_import_cost_engine():
    found = _forbidden_imports_in_paths()
    assert not any("cost_engine_service" in mod for mod in found)


def test_does_not_use_commercial_totals_for_task_generation():
    service_source = (BACKEND_ROOT / "services" / "execution_plan_v2_preview_service.py").read_text(
        encoding="utf-8"
    )
    assert "commercial_price_proposal_snapshot" not in service_source
    assert "commercial_total" not in service_source
    assert "accepted_commercial_total" not in service_source


def test_does_not_use_internal_totals_for_task_generation():
    service_source = (BACKEND_ROOT / "services" / "execution_plan_v2_preview_service.py").read_text(
        encoding="utf-8"
    )
    assert "estimated_internal_cost_snapshot" not in service_source
    assert "estimated_internal_total" not in service_source


# ---------------------------------------------------------------------------
# 18-25. Preview contract / determinism
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_produces_preview_source_order_snapshot_v2(db_session):
    order = await _seed_v2_order_with_snapshot(db_session)
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    assert preview.source == EXECUTION_PLAN_V2_SOURCE


@pytest.mark.asyncio
async def test_includes_order_snapshot_hash(db_session):
    order = await _seed_v2_order_with_snapshot(db_session)
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    expected = hashlib.sha256(order.snapshot_v2_json.encode()).hexdigest()[:32]
    assert preview.order_snapshot_hash == expected


@pytest.mark.asyncio
async def test_includes_quote_snapshot_v2_id(db_session):
    order = await _seed_v2_order_with_snapshot(db_session)
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    assert preview.quote_snapshot_v2_id == order.quote_snapshot_v2_id


@pytest.mark.asyncio
async def test_includes_ignored_pricing_sources(db_session):
    order = await _seed_v2_order_with_snapshot(db_session)
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    assert preview.ignored_pricing_sources == list(IGNORED_PRICING_SOURCES)


@pytest.mark.asyncio
async def test_includes_provenance(db_session):
    order = await _seed_v2_order_with_snapshot(db_session)
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    keys = {entry.key for entry in preview.provenance}
    assert "order_snapshot_v2" in keys
    assert "product_aggregate_snapshot" in keys


@pytest.mark.asyncio
async def test_planning_minutes_missing_partial_with_warning_not_fake_minutes(db_session):
    order = await _seed_v2_order_with_snapshot(db_session)
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    assert preview.status == "partial_missing_planning_minutes"
    assert "PLANNING_MINUTES_SOURCE_REQUIRED" in preview.warnings
    assert preview.planned_tasks
    assert all(task.estimated_minutes is None for task in preview.planned_tasks)


@pytest.mark.asyncio
async def test_planned_tasks_deterministic_when_task_rules_exist(db_session):
    order = await _seed_v2_order_with_snapshot(db_session)
    first = await build_execution_plan_v2_preview(db_session, order.id)
    second = await build_execution_plan_v2_preview(db_session, order.id)
    assert first.model_dump() == second.model_dump()
    assert [t.source_task_rule_code for t in first.planned_tasks] == ["cnc_face_cut", "electrical_wiring"]


@pytest.mark.asyncio
async def test_duplicate_preview_calls_no_db_write_and_deterministic(db_fixture, db_session, auth_client):
    order = await _seed_v2_order_with_snapshot(db_session)
    plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    resp1 = auth_client.post(f"/api/v1/execution/plan-v2/preview/{order.id}")
    resp2 = auth_client.post(f"/api/v1/execution/plan-v2/preview/{order.id}")
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json() == resp2.json()
    plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
    assert plans_after == plans_before


# ---------------------------------------------------------------------------
# 26-27. Regression guards for 9.3.1 and 9.2
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_existing_9_3_1_legacy_guard_still_passes(db_fixture, db_session, auth_client):
    order = await _seed_v2_order_by_json(db_session)
    resp = auth_client.post(f"/api/v1/execution/plan/from-order/{order.id}")
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"] == "EXECUTION_PLAN_V2_REQUIRED"


@pytest.mark.asyncio
async def test_existing_9_2_convert_still_works(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    await _insert_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
    )
    await accept_v6_quote(
        volumetric_v2_db,
        quote.id,
        _valid_accept_body(),
        _test_user(),
    )
    result = await convert_v6_quote_to_order(
        volumetric_v2_db,
        quote.id,
        _convert_body(),
        _test_user(),
    )
    assert result["converted"] is True


def test_preview_endpoint_contract_fields(auth_client, db_fixture, db_session):
    async def _setup():
        return await _seed_v2_order_with_snapshot(db_session)

    order = db_fixture.run(_setup())
    resp = auth_client.post(f"/api/v1/execution/plan-v2/preview/{order.id}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["persist_status"] == "not_persisted"
    assert body["execution_plan_created"] is False
    assert body["execution_tasks_created"] is False
    assert body["source"] == EXECUTION_PLAN_V2_SOURCE


def _module_codes(tasks) -> set[str]:
    return {t.source_module_code for t in tasks if t.source_module_code}


def _task_rule_keys(tasks) -> set[str]:
    """Rule codes — stable across frozen deterministic task_key prefixes."""
    return {
        str(t.source_task_rule_code or t.task_key.split(":")[-1]).strip()
        for t in tasks
    }


def _task_keys(tasks) -> set[str]:
    return {t.task_key for t in tasks}


def _operation_codes(operations) -> set[str]:
    return {op.operation_code for op in operations}


# ---------------------------------------------------------------------------
# Sold scope integration (EXECUTION_SOLD_SCOPE_READ_PATH_V1)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sold_scope_legacy_order_unchanged(db_session):
    order = await _seed_v2_order_with_snapshot(db_session)
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    assert preview.status == "partial_missing_planning_minutes"
    assert _task_rule_keys(preview.planned_tasks) == {"cnc_face_cut", "electrical_wiring"}


@pytest.mark.asyncio
async def test_sold_scope_explicit_full_product_unchanged(db_session):
    snapshot = snapshot_with_scope(
        offer_scope=offer_scope(mode="full_product", use_legacy=True, runtime=[]),
        aggregate=_sample_aggregate(),
    )
    order = await _seed_v2_order_with_snapshot(db_session, snapshot_v2_json=snapshot.model_dump_json())
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    assert _task_rule_keys(preview.planned_tasks) == {"cnc_face_cut", "electrical_wiring"}


@pytest.mark.asyncio
async def test_sold_scope_face_only_filters_tasks_and_operations(db_session):
    snapshot = snapshot_with_scope(
        offer_scope=offer_scope(runtime=["debitare_fata"]),
    )
    order = await _seed_v2_order_with_snapshot(db_session, snapshot_v2_json=snapshot.model_dump_json())
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    keys = _task_rule_keys(preview.planned_tasks)
    assert keys == {"vector_prep", "cnc_face_cut"}
    op_codes = _operation_codes(preview.planned_operations)
    assert "vector_prep" in op_codes
    assert "face_cnc_cut" in op_codes
    assert "back_cut" not in op_codes
    assert "logo_vinyl" not in op_codes


@pytest.mark.asyncio
async def test_sold_scope_return_cant_only(db_session):
    snapshot = snapshot_with_scope(
        offer_scope=offer_scope(runtime=["modelare_cant"]),
    )
    order = await _seed_v2_order_with_snapshot(db_session, snapshot_v2_json=snapshot.model_dump_json())
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    keys = _task_rule_keys(preview.planned_tasks)
    assert keys == {"vector_prep", "return_profile_forming", "return_face_bonding"}


@pytest.mark.asyncio
async def test_sold_scope_back_only(db_session):
    snapshot = snapshot_with_scope(
        offer_scope=offer_scope(runtime=["debitare_spate"]),
    )
    order = await _seed_v2_order_with_snapshot(db_session, snapshot_v2_json=snapshot.model_dump_json())
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    keys = _task_rule_keys(preview.planned_tasks)
    assert keys == {"vector_prep", "cnc_back_cut"}


@pytest.mark.asyncio
async def test_sold_scope_face_plus_return_cant_union(db_session):
    snapshot = snapshot_with_scope(
        offer_scope=offer_scope(runtime=["debitare_fata", "modelare_cant"]),
    )
    order = await _seed_v2_order_with_snapshot(db_session, snapshot_v2_json=snapshot.model_dump_json())
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    keys = _task_rule_keys(preview.planned_tasks)
    assert keys == {
        "vector_prep",
        "cnc_face_cut",
        "return_profile_forming",
        "return_face_bonding",
    }


@pytest.mark.asyncio
async def test_sold_scope_linked_logo_full_product_preserved(db_session):
    snapshot = snapshot_with_scope(offer_scope=None)
    order = await _seed_v2_order_with_snapshot(db_session, snapshot_v2_json=snapshot.model_dump_json())
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    assert "linked_logo_apply" in _task_rule_keys(preview.planned_tasks)
    assert "logo_vinyl" in _operation_codes(preview.planned_operations)


@pytest.mark.asyncio
async def test_sold_scope_invalid_subset_blocks_preview(db_session):
    snapshot = snapshot_with_scope(
        offer_scope=offer_scope(runtime=[]),
    )
    order = await _seed_v2_order_with_snapshot(db_session, snapshot_v2_json=snapshot.model_dump_json())
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    assert preview.status == "blocked_missing_sold_scope"
    assert preview.planned_tasks == []
    assert "blocked_missing_sold_scope" in preview.blockers


@pytest.mark.asyncio
async def test_sold_scope_provenance_includes_frozen_scope(db_session):
    snapshot = snapshot_with_scope(
        offer_scope=offer_scope(runtime=["debitare_fata"]),
    )
    order = await _seed_v2_order_with_snapshot(db_session, snapshot_v2_json=snapshot.model_dump_json())
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    keys = {entry.key for entry in preview.provenance}
    assert "execution_sold_scope_frozen" in keys
