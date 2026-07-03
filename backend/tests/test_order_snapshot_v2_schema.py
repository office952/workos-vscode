"""Tests for Order Snapshot V2 schema fields (Step 9.1).

Schema + guard only — no V2 order conversion, no ExecutionPlan.
Future Step 9.2 will populate quote_snapshot_v2_id and snapshot_v2_json.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import func, inspect as sa_inspect, select

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from models.quotes import Quotes
from schemas.commercial_price_proposal import CommercialPriceProposalPreview
from schemas.estimated_internal_cost import EstimatedInternalCostPreview
from schemas.quote_snapshot_v2 import QuoteSnapshotV2
from services.intake_v6_quote_to_order_service import accept_v6_quote, convert_v6_quote_to_order
from tests.test_quote_snapshot_v2_accept_gate import (
    _insert_snapshot,
    _seed_v6_quote,
    _test_user,
    _valid_accept_body,
)

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

MIGRATION_FILE = "s55_add_orders_quote_snapshot_v2_fields.py"
STEP_9_1_PATHS = (
    Path(__file__).resolve().parents[1] / "models" / "orders.py",
    Path(__file__).resolve().parents[1] / "alembic" / "versions" / MIGRATION_FILE,
    Path(__file__).resolve(),
)


@pytest.fixture(autouse=True)
def no_workspace_critical_blockers(monkeypatch):
    async def _empty(*args, **kwargs):
        return []

    monkeypatch.setattr(
        "services.intake_v6_quote_to_order_service._collect_accept_critical_blockers",
        _empty,
    )


def _forbidden_imports_in_paths() -> set[str]:
    forbidden = {
        "quote_orchestrator",
        "cost_engine_service",
        "aggregate_cost_bom_price_bridge",
    }
    found: set[str] = set()
    for path in STEP_9_1_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for part in forbidden:
                    if part in node.module:
                        found.add(node.module)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for part in forbidden:
                        if part in alias.name:
                            found.add(alias.name)
    return found


def test_orders_model_exposes_quote_snapshot_v2_id():
    assert "quote_snapshot_v2_id" in Orders.__table__.columns
    col = Orders.__table__.columns["quote_snapshot_v2_id"]
    assert col.nullable is True


def test_orders_model_exposes_snapshot_v2_json():
    assert "snapshot_v2_json" in Orders.__table__.columns
    col = Orders.__table__.columns["snapshot_v2_json"]
    assert col.nullable is True


@pytest.mark.asyncio
async def test_new_fields_are_nullable_on_legacy_order_row(volumetric_v2_db):
    order = Orders(
        code="ORD-LEGACY-9-1",
        quote_id=None,
        client_name="Legacy Client",
        status="locked",
        total_amount=1000.0,
        snapshot_line_items='{"legacy": true}',
    )
    volumetric_v2_db.add(order)
    await volumetric_v2_db.commit()

    refreshed = await volumetric_v2_db.get(Orders, order.id)
    assert refreshed.quote_snapshot_v2_id is None
    assert refreshed.snapshot_v2_json is None
    assert refreshed.snapshot_line_items == '{"legacy": true}'
    assert refreshed.total_amount == 1000.0


@pytest.mark.asyncio
async def test_v2_fields_do_not_replace_snapshot_line_items(volumetric_v2_db):
    snapshot = QuoteSnapshotV2(
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        commercial_price_proposal_snapshot=CommercialPriceProposalPreview(
            template_code="TPL-VOLUMETRIC-LETTERS_v2",
            commercial_total=1500.0,
        ),
        estimated_internal_cost_snapshot=EstimatedInternalCostPreview(
            template_code="TPL-VOLUMETRIC-LETTERS_v2",
            estimated_total_internal_cost=620.0,
        ),
    )
    snapshot_json = snapshot.model_dump_json()
    record = QuoteSnapshotV2Record(
        snapshot_code="QSN2-ORD-9-1",
        snapshot_version="1.0.0",
        version=1,
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        status="frozen",
        readiness="ready_for_owner_review",
        snapshot_json=snapshot_json,
        content_hash=hashlib.sha256(snapshot_json.encode()).hexdigest()[:32],
    )
    volumetric_v2_db.add(record)
    await volumetric_v2_db.commit()
    await volumetric_v2_db.refresh(record)

    payload = {"order_snapshot_v2": "future_step_9_2"}
    order = Orders(
        code="ORD-V2-FIELDS-9-1",
        client_name="V2 Schema Client",
        status="locked",
        total_amount=1500.0,
        snapshot_line_items=None,
        quote_snapshot_v2_id=record.id,
        snapshot_v2_json=json.dumps(payload),
    )
    volumetric_v2_db.add(order)
    await volumetric_v2_db.commit()
    await volumetric_v2_db.refresh(order)

    assert order.quote_snapshot_v2_id == record.id
    assert json.loads(order.snapshot_v2_json) == payload
    assert order.snapshot_line_items is None
    assert order.total_amount == 1500.0


@pytest.mark.asyncio
async def test_v2_accepted_quote_converts_to_order_with_snapshot_v2(volumetric_v2_db):
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

    orders_before = await volumetric_v2_db.scalar(select(func.count()).select_from(Orders))
    plans_before = await volumetric_v2_db.scalar(select(func.count()).select_from(ExecutionPlan))

    result = await convert_v6_quote_to_order(
        volumetric_v2_db,
        quote.id,
        {
            "convert_reason": "Convert accepted snapshot v2",
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

    orders_after = await volumetric_v2_db.scalar(select(func.count()).select_from(Orders))
    plans_after = await volumetric_v2_db.scalar(select(func.count()).select_from(ExecutionPlan))

    assert result["converted"] is True
    assert orders_after == orders_before + 1
    assert plans_after == plans_before
    order = await volumetric_v2_db.get(Orders, result["order_id"])
    assert order.snapshot_v2_json is not None
    assert order.snapshot_line_items is None


def test_v2_branch_delegates_before_legacy_order_create_in_source():
    source = inspect.getsource(convert_v6_quote_to_order)
    delegate_pos = source.index("convert_accepted_quote_snapshot_v2_to_order")
    create_pos = source.index("orders_service.create")
    assert delegate_pos < create_pos


def test_migration_additive_only():
    migration_path = (
        Path(__file__).resolve().parents[1] / "alembic" / "versions" / MIGRATION_FILE
    )
    text = migration_path.read_text(encoding="utf-8").lower()
    assert "quote_snapshot_v2_id" in text
    assert "snapshot_v2_json" in text
    assert "quote_snapshots_v2" in text
    assert "create_table" not in text
    assert "order_snapshots_v2" not in text
    assert "snapshot_line_items" not in text
    assert "total_amount" not in text
    assert "line_items" not in text
    assert "update(" not in text
    assert "backfill" not in text


def test_migration_rollback_drops_step_9_1_fields_only():
    migration_path = (
        Path(__file__).resolve().parents[1] / "alembic" / "versions" / MIGRATION_FILE
    )
    text = migration_path.read_text(encoding="utf-8")
    assert "drop_column" in text
    assert "snapshot_v2_json" in text
    assert "quote_snapshot_v2_id" in text
    assert "drop_index" in text
    assert "ix_orders_quote_snapshot_v2_id" in text
    assert "drop_constraint" in text
    assert "fk_orders_quote_snapshot_v2_id" in text


def test_migration_fk_targets_quote_snapshots_v2():
    migration_path = (
        Path(__file__).resolve().parents[1] / "alembic" / "versions" / MIGRATION_FILE
    )
    text = migration_path.read_text(encoding="utf-8")
    assert "quote_snapshots_v2" in text


def test_no_order_snapshots_v2_table_in_repo_migrations():
    versions_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    for path in versions_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "order_snapshots_v2" not in text


def test_step_9_1_code_has_no_forbidden_imports():
    assert _forbidden_imports_in_paths() == set()


@pytest.mark.asyncio
async def test_quote_without_accepted_snapshot_v2_id_has_null_fk(volumetric_v2_db):
    quote = Quotes(
        code="Q-LEGACY-9-1",
        client_name="Legacy Quote",
        status="draft",
        version=1,
    )
    volumetric_v2_db.add(quote)
    await volumetric_v2_db.commit()
    await volumetric_v2_db.refresh(quote)
    assert quote.accepted_snapshot_v2_id is None


def test_orders_table_mapper_includes_v2_columns():
    mapper = sa_inspect(Orders)
    col_names = {c.key for c in mapper.columns}
    assert "quote_snapshot_v2_id" in col_names
    assert "snapshot_v2_json" in col_names
