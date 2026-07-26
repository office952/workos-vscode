"""Step 8.3 snapshot acceptability — freeze status + IV6 pricing review from snapshot V2."""

from __future__ import annotations

import json
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from models.orders import Orders
from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from models.quotes import Quotes
from schemas.order_snapshot_v2 import OrderSnapshotV2
from services.intake_v3_quote_linkage_utils import PRICING_REVIEW_JSON_KEY
from services.intake_v4_quote_linkage_utils import V4_ACCEPTED_STATUS
from services.intake_v6_commercial_quote_service import INTAKE_V6_LINKAGE_JSON_KEY
from services.intake_v6_quote_to_order_service import (
    accept_v6_quote,
    complete_v6_pricing_review,
    convert_v6_quote_to_order,
    persist_v6_owner_approval,
)
from services.quote_snapshot_v2_accept_gate_service import validate_snapshot_for_accept
from services.quote_snapshot_v2_service import QuoteSnapshotV2Service
from tests.test_order_snapshot_v2_convert import _valid_convert_body
from tests.test_quote_snapshot_v2 import TEMPLATE, _step8_qa_quote_input
from tests.test_quote_snapshot_v2_accept_gate import (
    ANALYSIS_HASH,
    _full_workspace_payload,
    _insert_snapshot,
    _test_user,
    _valid_accept_body,
)

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]


async def _seed_v6_handoff_quote(
    db,
    *,
    grand_total: float = 0.0,
) -> tuple[Quotes, str]:
    workspace_id = str(uuid.uuid4())
    intake_code = f"IV6-{workspace_id}"
    workspace = IntakeV6WorkspaceRecord(
        id=workspace_id,
        workspace_code=f"WS-{workspace_id[:8]}",
        title="Step 8 handoff workspace",
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
        client_name="Step 8 Handoff Client",
        status="draft",
        version=1,
        intake_code=intake_code,
        grand_total=grand_total,
        notes=json.dumps({INTAKE_V6_LINKAGE_JSON_KEY: linkage}),
    )
    db.add(quote)
    await db.commit()
    await db.refresh(quote)
    return quote, workspace_id


def _pricing_review_body() -> dict:
    return {
        "reviewer_confirmation": True,
        "confirm_quote_stays_draft": True,
        "confirm_no_order": True,
        "confirm_no_execution": True,
        "confirm_no_inventory": True,
        "pricing_review_reason": "Step 8.3 pricing review from frozen Quote Snapshot V2 total.",
    }


def _owner_approval_body() -> dict:
    return {
        "decision_reason": "Owner approves Step 8 snapshot V2 handoff.",
        "acknowledged_no_execution_tasks": True,
        "acknowledged_no_stock_consumption": True,
        "client_analysis_hash": ANALYSIS_HASH,
    }


@pytest.fixture(autouse=True)
def no_workspace_critical_blockers(monkeypatch):
    async def _empty(*args, **kwargs):
        return []

    monkeypatch.setattr(
        "services.intake_v6_quote_to_order_service._collect_accept_critical_blockers",
        _empty,
    )


@pytest.mark.asyncio
async def test_v6_pricing_review_uses_snapshot_v2_when_quote_unpriced(volumetric_v2_db):
    quote, workspace_id = await _seed_v6_handoff_quote(volumetric_v2_db, grand_total=0.0)
    await _insert_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
        readiness="partial_with_owner_decisions",
        status="frozen",
        commercial_total=12.5,
        internal_total=866.67,
        owner_decisions=[
            {
                "code": "DEBITARE_SPATE_BASIS_ML_VS_M2",
                "label": "Debitare spate basis",
                "source": "commercial_price_proposal",
            }
        ],
    )

    result = await complete_v6_pricing_review(
        volumetric_v2_db,
        quote.id,
        _pricing_review_body(),
        _test_user(),
    )

    assert result["pricing_review_completed"] is True
    assert result["pricing_totals_source"] == "quote_snapshot_v2"
    refreshed = await volumetric_v2_db.get(Quotes, quote.id)
    notes = json.loads(refreshed.notes)
    pricing_record = notes[INTAKE_V6_LINKAGE_JSON_KEY][PRICING_REVIEW_JSON_KEY]
    expected_gross = round(12.5 * 1.21, 2)
    assert float(pricing_record["total"]) == expected_gross


@pytest.mark.asyncio
async def test_partial_frozen_snapshot_accept_gate_still_requires_owner_ack(volumetric_v2_db):
    quote, workspace_id = await _seed_v6_handoff_quote(volumetric_v2_db)
    record = await _insert_snapshot(
        volumetric_v2_db,
        quote_id=quote.id,
        workspace_id=workspace_id,
        readiness="partial_with_owner_decisions",
        status="frozen",
        commercial_total=12.5,
        owner_decisions=[
            {
                "code": "DEBITARE_SPATE_BASIS_ML_VS_M2",
                "label": "Debitare spate basis",
                "source": "commercial_price_proposal",
            }
        ],
    )

    blocked = validate_snapshot_for_accept(
        record,
        quote_id=quote.id,
        workspace_id=workspace_id,
        confirm_owner_decisions_acknowledged=False,
    )
    assert blocked.accept_allowed is False
    assert blocked.error_code == "OWNER_DECISIONS_ACK_REQUIRED"

    allowed = validate_snapshot_for_accept(
        record,
        quote_id=quote.id,
        workspace_id=workspace_id,
        confirm_owner_decisions_acknowledged=True,
    )
    assert allowed.accept_allowed is True
    assert record.status == "frozen"


@pytest.mark.asyncio
async def test_v6_step8_chain_freeze_prereq_accept_convert(volumetric_v2_db):
    quote, workspace_id = await _seed_v6_handoff_quote(volumetric_v2_db, grand_total=0.0)
    service = QuoteSnapshotV2Service(volumetric_v2_db)

    orders_before = await volumetric_v2_db.scalar(select(func.count()).select_from(Orders))
    plans_before = await volumetric_v2_db.scalar(select(func.count()).select_from(ExecutionPlan))

    frozen = await service.freeze(
        TEMPLATE,
        quote_id=str(quote.id),
        workspace_id=workspace_id,
        quote_input=_step8_qa_quote_input(),
        frozen_by="step8-qa",
    )
    assert frozen is not None
    assert frozen.persist_status == "persisted"
    assert frozen.readiness == "partial_with_owner_decisions"

    record = await volumetric_v2_db.get(QuoteSnapshotV2Record, int(frozen.snapshot_id))
    assert record is not None
    assert record.status == "frozen"
    assert float(frozen.commercial_price_proposal_snapshot.commercial_total or 0) > 0

    pricing = await complete_v6_pricing_review(
        volumetric_v2_db,
        quote.id,
        _pricing_review_body(),
        _test_user(),
    )
    assert pricing["pricing_totals_source"] == "quote_snapshot_v2"

    await persist_v6_owner_approval(
        volumetric_v2_db,
        quote.id,
        _owner_approval_body(),
        _test_user(),
    )

    accept = await accept_v6_quote(
        volumetric_v2_db,
        quote.id,
        _valid_accept_body(confirm_owner_decisions_acknowledged=True),
        _test_user(),
    )
    assert accept["accepted"] is True

    accepted_quote = await volumetric_v2_db.get(Quotes, quote.id)
    assert accepted_quote is not None
    assert accepted_quote.status == V4_ACCEPTED_STATUS
    assert accepted_quote.accepted_snapshot_v2_id == record.id

    convert = await convert_v6_quote_to_order(
        volumetric_v2_db,
        quote.id,
        _valid_convert_body(),
        _test_user(),
    )
    assert convert["converted"] is True

    order = await volumetric_v2_db.get(Orders, convert["order_id"])
    assert order is not None
    assert order.quote_snapshot_v2_id == record.id
    assert order.snapshot_v2_json is not None

    payload = OrderSnapshotV2.model_validate_json(order.snapshot_v2_json)
    assert payload.commercial_price_proposal_snapshot is not None
    assert payload.estimated_internal_cost_snapshot is not None

    orders_after = await volumetric_v2_db.scalar(select(func.count()).select_from(Orders))
    plans_after = await volumetric_v2_db.scalar(select(func.count()).select_from(ExecutionPlan))
    assert orders_after == orders_before + 1
    assert plans_after == plans_before
