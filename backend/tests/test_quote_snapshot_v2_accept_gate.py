"""Tests for Quote Snapshot V2 accept gate (Step 8.3)."""

from __future__ import annotations

import ast
import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from models.orders import Orders
from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from models.quotes import Quotes
from schemas.auth import UserResponse
from schemas.commercial_price_proposal import CommercialPriceProposalPreview
from schemas.estimated_internal_cost import EstimatedInternalCostPreview
from schemas.quote_snapshot_v2 import QuoteSnapshotV2
from services.intake_v3_quote_linkage_utils import ACCEPT_DECISION_JSON_KEY, PRICING_REVIEW_JSON_KEY
from services.intake_v4_quote_linkage_utils import OWNER_APPROVAL_JSON_KEY, V4_ACCEPTED_STATUS
from services.intake_v6_commercial_quote_service import INTAKE_V6_LINKAGE_JSON_KEY
from services.intake_v6_quote_to_order_service import accept_v6_quote, convert_v6_quote_to_order
from services.quote_snapshot_v2_accept_gate_service import (
    build_accept_snapshot_metadata,
    resolve_snapshot_for_accept,
    validate_snapshot_for_accept,
)

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
ANALYSIS_HASH = "a" * 64


@pytest.fixture(autouse=True)
def no_workspace_critical_blockers(monkeypatch):
    async def _empty(*args, **kwargs):
        return []

    monkeypatch.setattr(
        "services.intake_v6_quote_to_order_service._collect_accept_critical_blockers",
        _empty,
    )


def _full_workspace_payload() -> dict:
    return {
        "schema_version": "1.0.0",
        "analysis_ready": True,
        "product_binding": {
            "template_code": TEMPLATE,
            "template_id": 1,
            "template_label": "Litere volumetrice",
            "product_family": "litere_volumetrice",
        },
        "svg_source": {
            "file_name": "test.svg",
            "file_size_bytes": 100,
            "file_hash": ANALYSIS_HASH,
            "upload_status": "analyzed",
        },
        "client": {"width_mm": 1200, "height_mm": 400},
        "quote_geometry": {
            "letter_count": 5,
            "letter_perimeter_m": 12.5,
            "letter_face_area_m2": 1.2,
        },
        "finish_setup": {
            "face_finish_type": "plexiglas_clear",
            "return_depth_mm": 60,
            "return_finish_type": "ral",
            "backing_mode": "none",
            "mounting_system": "direct_wall",
            "letter_group_finishes": [{"group_key": "default", "confirmed": True}],
        },
    }


def _commercial_preview(*, total: float = 1500.0, status: str = "ready") -> CommercialPriceProposalPreview:
    return CommercialPriceProposalPreview(
        template_code=TEMPLATE,
        status=status,
        commercial_total=total,
        subtotal_commercial=total,
        quote_ready_for_commercial_review=True,
    )


def _internal_preview(*, total: float = 620.0, status: str = "ready") -> EstimatedInternalCostPreview:
    return EstimatedInternalCostPreview(
        template_code=TEMPLATE,
        status=status,
        estimated_total_internal_cost=total,
        ready_for_quote_snapshot=True,
    )


def _build_snapshot_json(
    *,
    quote_id: int | None,
    workspace_id: str | None,
    readiness: str = "ready_for_owner_review",
    commercial_total: float = 1500.0,
    internal_total: float = 620.0,
    owner_decisions: list | None = None,
) -> str:
    from schemas.quote_snapshot_v2 import QuoteSnapshotOwnerDecision

    snapshot = QuoteSnapshotV2(
        quote_id=str(quote_id) if quote_id is not None else None,
        workspace_id=workspace_id,
        template_code=TEMPLATE,
        commercial_price_proposal_snapshot=_commercial_preview(total=commercial_total),
        estimated_internal_cost_snapshot=_internal_preview(total=internal_total),
        owner_decisions_snapshot=owner_decisions or [],
        readiness=readiness,
        persist_status="persisted",
    )
    return snapshot.model_dump_json()


async def _insert_snapshot(
    db,
    *,
    quote_id: int | None,
    workspace_id: str | None,
    readiness: str = "ready_for_owner_review",
    status: str = "frozen",
    commercial_total: float = 1500.0,
    internal_total: float = 620.0,
    owner_decisions: list | None = None,
    version: int = 1,
) -> QuoteSnapshotV2Record:
    from schemas.quote_snapshot_v2 import QuoteSnapshotOwnerDecision

    od_list = []
    if owner_decisions:
        for item in owner_decisions:
            if isinstance(item, QuoteSnapshotOwnerDecision):
                od_list.append(item)
            else:
                od_list.append(QuoteSnapshotOwnerDecision(**item))
    snapshot_json = _build_snapshot_json(
        quote_id=quote_id,
        workspace_id=workspace_id,
        readiness=readiness,
        commercial_total=commercial_total,
        internal_total=internal_total,
        owner_decisions=od_list or None,
    )
    content_hash = hashlib.sha256(snapshot_json.encode()).hexdigest()[:32]
    record = QuoteSnapshotV2Record(
        snapshot_code=f"QSN2-TEST-{uuid.uuid4().hex[:8]}",
        snapshot_version="1.0.0",
        version=version,
        quote_id=quote_id,
        workspace_id=workspace_id,
        template_code=TEMPLATE,
        status=status,
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


async def _seed_v6_quote(
    db,
    *,
    workspace_id: str | None = None,
    grand_total: float = 0.0,
) -> tuple[Quotes, str, dict]:
    workspace_id = workspace_id or str(uuid.uuid4())
    intake_code = f"IV6-{workspace_id}"

    workspace = IntakeV6WorkspaceRecord(
        id=workspace_id,
        workspace_code=f"WS-{workspace_id[:8]}",
        title="Accept gate test workspace",
        template_code=TEMPLATE,
        payload_json=json.dumps(_full_workspace_payload()),
        status="draft",
    )
    db.add(workspace)

    linkage = {
        "source_module": "intake_v6",
        "source_intake_version": "V6",
        "source_workspace_id": workspace_id,
        "requires_pricing_review": False,
        PRICING_REVIEW_JSON_KEY: {
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "method": "quote_snapshot_v2",
        },
        OWNER_APPROVAL_JSON_KEY: {
            "approved": True,
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "analysis_hash": ANALYSIS_HASH,
        },
        "snapshot": {"workspace_payload_snapshot": {"svg_source": {"file_hash": ANALYSIS_HASH}}},
    }
    notes = json.dumps({INTAKE_V6_LINKAGE_JSON_KEY: linkage})

    quote = Quotes(
        code=f"Q-V6-{uuid.uuid4().hex[:8]}",
        client_name="Accept Gate Client",
        status="draft",
        version=1,
        intake_code=intake_code,
        grand_total=grand_total,
        notes=notes,
    )
    db.add(quote)
    await db.commit()
    await db.refresh(quote)
    return quote, workspace_id, linkage


def _valid_accept_body(**overrides) -> dict:
    body = {
        "accept_reason": "Owner approved snapshot v2 quote.",
        "reviewer_confirmation": True,
        "confirm_pricing_review_completed": True,
        "confirm_no_order": True,
        "confirm_no_execution": True,
        "confirm_no_inventory": True,
        "confirm_convert_separate": True,
    }
    body.update(overrides)
    return body


def _test_user() -> UserResponse:
    return UserResponse(
        id="test-user-1",
        email="operator@test.local",
        name="Test Operator",
        role="admin",
    )


@pytest.mark.asyncio
async def test_cannot_accept_without_persisted_snapshot(volumetric_v2_db):
    quote, workspace_id, linkage = await _seed_v6_quote(volumetric_v2_db)
    with pytest.raises(HTTPException) as exc:
        await accept_v6_quote(
            volumetric_v2_db,
            quote.id,
            _valid_accept_body(),
            _test_user(),
        )
    assert exc.value.detail["error"] == "MISSING_SNAPSHOT_V2"


@pytest.mark.asyncio
async def test_cannot_accept_hard_blocked_readiness(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    await _insert_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
        readiness="blocked_forbidden_path",
    )
    with pytest.raises(HTTPException) as exc:
        await accept_v6_quote(
            volumetric_v2_db,
            quote.id,
            _valid_accept_body(),
            _test_user(),
        )
    assert exc.value.detail["error"] == "SNAPSHOT_READINESS_BLOCKED"


@pytest.mark.asyncio
async def test_can_accept_ready_for_owner_review_snapshot(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    snapshot = await _insert_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
        readiness="ready_for_owner_review",
    )
    result = await accept_v6_quote(
        volumetric_v2_db,
        quote.id,
        _valid_accept_body(),
        _test_user(),
    )
    assert result["accepted"] is True
    refreshed = await volumetric_v2_db.get(Quotes, quote.id)
    assert refreshed is not None
    assert refreshed.status == V4_ACCEPTED_STATUS
    assert refreshed.accepted_snapshot_v2_id == snapshot.id


@pytest.mark.asyncio
async def test_partial_snapshot_requires_owner_decision_acknowledgement(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    await _insert_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
        readiness="partial_with_owner_decisions",
        owner_decisions=[
            {
                "code": "DEBITARE_SPATE_BASIS_ML_VS_M2",
                "label": "Debitare spate basis",
                "source": "commercial_price_proposal",
            }
        ],
    )
    with pytest.raises(HTTPException) as exc:
        await accept_v6_quote(
            volumetric_v2_db,
            quote.id,
            _valid_accept_body(),
            _test_user(),
        )
    assert exc.value.detail["error"] == "OWNER_DECISIONS_ACK_REQUIRED"

    result = await accept_v6_quote(
        volumetric_v2_db,
        quote.id,
        _valid_accept_body(confirm_owner_decisions_acknowledged=True),
        _test_user(),
    )
    assert result["accepted"] is True


@pytest.mark.asyncio
async def test_accept_stores_accepted_snapshot_v2_id(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    snapshot = await _insert_snapshot(
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
    refreshed = await volumetric_v2_db.get(Quotes, quote.id)
    assert refreshed.accepted_snapshot_v2_id == snapshot.id


@pytest.mark.asyncio
async def test_accept_linkage_records_snapshot_metadata(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    snapshot = await _insert_snapshot(
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
    refreshed = await volumetric_v2_db.get(Quotes, quote.id)
    notes = json.loads(refreshed.notes)
    accept_decision = notes[INTAKE_V6_LINKAGE_JSON_KEY][ACCEPT_DECISION_JSON_KEY]
    meta = accept_decision["snapshot_v2"]
    assert meta["accepted_snapshot_v2_id"] == snapshot.id
    assert meta["snapshot_code"] == snapshot.snapshot_code
    assert meta["content_hash"] == snapshot.content_hash
    assert meta["accepted_commercial_total"] == 1500.0
    assert meta["internal_estimate_total"] == 620.0


@pytest.mark.asyncio
async def test_grand_total_zero_can_accept_with_snapshot_commercial_total(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db, grand_total=0.0)
    await _insert_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
        commercial_total=2400.0,
    )
    result = await accept_v6_quote(
        volumetric_v2_db,
        quote.id,
        _valid_accept_body(),
        _test_user(),
    )
    assert result["accepted"] is True
    refreshed = await volumetric_v2_db.get(Quotes, quote.id)
    assert float(refreshed.grand_total or 0) == 0.0
    notes = json.loads(refreshed.notes)
    meta = notes[INTAKE_V6_LINKAGE_JSON_KEY][ACCEPT_DECISION_JSON_KEY]["snapshot_v2"]
    assert meta["accepted_commercial_total"] == 2400.0
    assert meta["internal_estimate_total"] == 620.0
    assert meta["accepted_commercial_total"] != meta["internal_estimate_total"]


@pytest.mark.asyncio
async def test_accept_does_not_create_order_or_execution_plan(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    await _insert_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
    )
    orders_before = await volumetric_v2_db.scalar(select(func.count()).select_from(Orders))
    plans_before = await volumetric_v2_db.scalar(select(func.count()).select_from(ExecutionPlan))
    await accept_v6_quote(
        volumetric_v2_db,
        quote.id,
        _valid_accept_body(),
        _test_user(),
    )
    orders_after = await volumetric_v2_db.scalar(select(func.count()).select_from(Orders))
    plans_after = await volumetric_v2_db.scalar(select(func.count()).select_from(ExecutionPlan))
    assert orders_after == orders_before
    assert plans_after == plans_before


@pytest.mark.asyncio
async def test_v2_accepted_quote_converts_via_snapshot_v2(volumetric_v2_db):
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
    assert result["converted"] is True
    assert result["order_created"] is True


def _forbidden_accept_gate_imports() -> set[str]:
    path = Path(__file__).resolve().parents[1] / "services" / "quote_snapshot_v2_accept_gate_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
    return modules


def test_accept_gate_service_does_not_import_quote_orchestrator():
    modules = _forbidden_accept_gate_imports()
    assert not any("quote_orchestrator" in mod for mod in modules)


def test_accept_gate_service_does_not_import_cost_engine():
    modules = _forbidden_accept_gate_imports()
    assert not any("cost_engine" in mod for mod in modules)


@pytest.mark.asyncio
async def test_resolve_snapshot_prefers_quote_id(volumetric_v2_db):
    quote, workspace_id, linkage = await _seed_v6_quote(volumetric_v2_db)
    older = await _insert_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
        version=1,
    )
    newer = await _insert_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
        version=2,
    )
    resolved = await resolve_snapshot_for_accept(volumetric_v2_db, quote, linkage)
    assert resolved is not None
    assert resolved.id == newer.id


@pytest.mark.asyncio
async def test_validate_snapshot_rejects_missing_commercial_total(volumetric_v2_db):
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    record = await _insert_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
        commercial_total=0.0,
    )
    parsed = QuoteSnapshotV2.model_validate_json(record.snapshot_json)
    parsed.commercial_price_proposal_snapshot.commercial_total = None
    record.snapshot_json = parsed.model_dump_json()
    record.content_hash = hashlib.sha256(record.snapshot_json.encode()).hexdigest()[:32]
    await volumetric_v2_db.commit()

    gate = validate_snapshot_for_accept(
        record,
        quote_id=quote.id,
        workspace_id=workspace_id,
    )
    assert gate.accept_allowed is False
    assert gate.error_code == "SNAPSHOT_COMMERCIAL_TOTAL_MISSING"


def test_migration_additive_only():
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "s54_add_quotes_accepted_snapshot_v2_id.py"
    )
    text = migration_path.read_text(encoding="utf-8").lower()
    assert "accepted_snapshot_v2_id" in text
    assert "quote_snapshots_v2" in text
    assert "orders" not in text.replace("quote_snapshots_v2", "")
    assert "line_items" not in text


def test_build_accept_snapshot_metadata_separates_totals():
    record = MagicMock()
    record.id = 42
    record.snapshot_code = "QSN2-TEST"
    record.content_hash = "abc"
    record.readiness = "ready_for_owner_review"
    record.version = 1
    from services.quote_snapshot_v2_accept_gate_service import AcceptGateResult

    gate = AcceptGateResult(
        gate_status="snapshot_ready_for_acceptance",
        accept_allowed=True,
        commercial_total=100.0,
        internal_total=55.0,
    )
    meta = build_accept_snapshot_metadata(record, gate)
    assert meta["accepted_commercial_total"] == 100.0
    assert meta["internal_estimate_total"] == 55.0
    assert meta["accepted_commercial_total"] != meta["internal_estimate_total"]
