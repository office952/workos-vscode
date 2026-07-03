"""Quote Snapshot V2 accept gate (Step 8.3).

Validates persisted dual snapshots for V6 quote accept.
Does NOT call /price, QuoteOrchestrator, or CostEngine.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from models.quotes import Quotes
from schemas.quote_snapshot_v2 import QuoteSnapshotV2
from services.intake_v4_quote_linkage_utils import linkage_workspace_id

GateStatus = Literal[
    "snapshot_ready_for_acceptance",
    "snapshot_partial_needs_owner_decision",
    "snapshot_blocked",
    "legacy_quote_requires_reprice_blocked",
    "missing_active_snapshot",
    "snapshot_mismatch",
]

HARD_BLOCKED_READINESS = frozenset(
    {
        "blocked_missing_commercial",
        "blocked_missing_internal",
        "blocked_snapshot_conflict",
        "blocked_forbidden_path",
        "blocked_schema_missing",
    }
)

FORBIDDEN_IMPORT_SUBSTRINGS = (
    "quote_orchestrator",
    "cost_engine_service",
    "aggregate_cost_bom_price_bridge",
)


@dataclass
class AcceptGateResult:
    gate_status: GateStatus
    accept_allowed: bool
    error_code: str | None = None
    message: str | None = None
    blockers: list[str] = field(default_factory=list)
    commercial_total: float | None = None
    internal_total: float | None = None
    acknowledged_owner_decision_codes: list[str] = field(default_factory=list)
    snapshot_id: int | None = None
    snapshot_code: str | None = None
    content_hash: str | None = None
    snapshot_readiness: str | None = None


def _compute_content_hash(snapshot_json: str) -> str:
    return hashlib.sha256(snapshot_json.encode()).hexdigest()[:32]


def _parse_snapshot(record: QuoteSnapshotV2Record) -> QuoteSnapshotV2:
    return QuoteSnapshotV2.model_validate_json(record.snapshot_json)


def validate_snapshot_for_accept(
    record: QuoteSnapshotV2Record,
    *,
    quote_id: int,
    workspace_id: str | None,
    confirm_owner_decisions_acknowledged: bool = False,
) -> AcceptGateResult:
    """Validate a persisted snapshot row for quote accept."""
    base = AcceptGateResult(
        gate_status="snapshot_blocked",
        accept_allowed=False,
        snapshot_id=record.id,
        snapshot_code=record.snapshot_code,
        content_hash=record.content_hash,
        snapshot_readiness=record.readiness,
    )

    if record.content_hash:
        expected = _compute_content_hash(record.snapshot_json)
        if record.content_hash != expected:
            return AcceptGateResult(
                gate_status="snapshot_mismatch",
                accept_allowed=False,
                error_code="SNAPSHOT_HASH_MISMATCH",
                message="Snapshot content_hash does not match snapshot_json.",
                blockers=["snapshot_hash_mismatch"],
                snapshot_id=record.id,
                snapshot_code=record.snapshot_code,
                content_hash=record.content_hash,
                snapshot_readiness=record.readiness,
            )
    else:
        return AcceptGateResult(
            gate_status="snapshot_blocked",
            accept_allowed=False,
            error_code="SNAPSHOT_HASH_MISSING",
            message="Snapshot content_hash is required for accept.",
            blockers=["content_hash_missing"],
            snapshot_id=record.id,
            snapshot_code=record.snapshot_code,
            snapshot_readiness=record.readiness,
        )

    if record.quote_id is not None and record.quote_id != quote_id:
        return AcceptGateResult(
            gate_status="snapshot_mismatch",
            accept_allowed=False,
            error_code="SNAPSHOT_QUOTE_MISMATCH",
            message="Snapshot quote_id does not match accepting quote.",
            blockers=["snapshot_quote_mismatch"],
            snapshot_id=record.id,
            snapshot_code=record.snapshot_code,
            content_hash=record.content_hash,
            snapshot_readiness=record.readiness,
        )

    if workspace_id and record.workspace_id and record.workspace_id != workspace_id:
        return AcceptGateResult(
            gate_status="snapshot_mismatch",
            accept_allowed=False,
            error_code="SNAPSHOT_WORKSPACE_MISMATCH",
            message="Snapshot workspace_id does not match quote workspace linkage.",
            blockers=["snapshot_workspace_mismatch"],
            snapshot_id=record.id,
            snapshot_code=record.snapshot_code,
            content_hash=record.content_hash,
            snapshot_readiness=record.readiness,
        )

    if record.status != "frozen":
        return AcceptGateResult(
            gate_status="snapshot_blocked",
            accept_allowed=False,
            error_code="SNAPSHOT_NOT_FROZEN",
            message=f"Snapshot status {record.status!r} is not acceptable for accept.",
            blockers=["snapshot_not_frozen"],
            snapshot_id=record.id,
            snapshot_code=record.snapshot_code,
            content_hash=record.content_hash,
            snapshot_readiness=record.readiness,
        )

    if record.readiness in HARD_BLOCKED_READINESS:
        return AcceptGateResult(
            gate_status="snapshot_blocked",
            accept_allowed=False,
            error_code="SNAPSHOT_READINESS_BLOCKED",
            message=f"Snapshot readiness {record.readiness!r} blocks accept.",
            blockers=[record.readiness],
            snapshot_id=record.id,
            snapshot_code=record.snapshot_code,
            content_hash=record.content_hash,
            snapshot_readiness=record.readiness,
        )

    try:
        parsed = _parse_snapshot(record)
    except Exception as exc:
        return AcceptGateResult(
            gate_status="snapshot_blocked",
            accept_allowed=False,
            error_code="SNAPSHOT_JSON_INVALID",
            message=f"Snapshot JSON invalid: {exc}",
            blockers=["snapshot_json_invalid"],
            snapshot_id=record.id,
            snapshot_code=record.snapshot_code,
            content_hash=record.content_hash,
            snapshot_readiness=record.readiness,
        )

    if parsed.commercial_price_proposal_snapshot is None:
        return AcceptGateResult(
            gate_status="snapshot_blocked",
            accept_allowed=False,
            error_code="SNAPSHOT_COMMERCIAL_MISSING",
            message="CommercialPriceProposal snapshot missing.",
            blockers=["commercial_snapshot_missing"],
            snapshot_id=record.id,
            snapshot_code=record.snapshot_code,
            content_hash=record.content_hash,
            snapshot_readiness=record.readiness,
        )

    if parsed.estimated_internal_cost_snapshot is None:
        return AcceptGateResult(
            gate_status="snapshot_blocked",
            accept_allowed=False,
            error_code="SNAPSHOT_INTERNAL_MISSING",
            message="EstimatedInternalCost snapshot missing.",
            blockers=["internal_snapshot_missing"],
            snapshot_id=record.id,
            snapshot_code=record.snapshot_code,
            content_hash=record.content_hash,
            snapshot_readiness=record.readiness,
        )

    commercial_total = parsed.commercial_price_proposal_snapshot.commercial_total
    internal_total = parsed.estimated_internal_cost_snapshot.estimated_total_internal_cost

    if commercial_total is None or float(commercial_total) <= 0:
        return AcceptGateResult(
            gate_status="snapshot_blocked",
            accept_allowed=False,
            error_code="SNAPSHOT_COMMERCIAL_TOTAL_MISSING",
            message="Commercial snapshot total is required for V2 accept.",
            blockers=["commercial_total_missing"],
            snapshot_id=record.id,
            snapshot_code=record.snapshot_code,
            content_hash=record.content_hash,
            snapshot_readiness=record.readiness,
            commercial_total=commercial_total,
            internal_total=internal_total,
        )

    if record.readiness == "ready_for_owner_review":
        return AcceptGateResult(
            gate_status="snapshot_ready_for_acceptance",
            accept_allowed=True,
            snapshot_id=record.id,
            snapshot_code=record.snapshot_code,
            content_hash=record.content_hash,
            snapshot_readiness=record.readiness,
            commercial_total=float(commercial_total),
            internal_total=float(internal_total) if internal_total is not None else None,
        )

    if record.readiness == "partial_with_owner_decisions":
        decision_codes = [d.code for d in parsed.owner_decisions_snapshot]
        if not confirm_owner_decisions_acknowledged:
            return AcceptGateResult(
                gate_status="snapshot_partial_needs_owner_decision",
                accept_allowed=False,
                error_code="OWNER_DECISIONS_ACK_REQUIRED",
                message="Partial snapshot requires confirm_owner_decisions_acknowledged.",
                blockers=["owner_decisions_ack_required"],
                snapshot_id=record.id,
                snapshot_code=record.snapshot_code,
                content_hash=record.content_hash,
                snapshot_readiness=record.readiness,
                commercial_total=float(commercial_total),
                internal_total=float(internal_total) if internal_total is not None else None,
            )
        return AcceptGateResult(
            gate_status="snapshot_ready_for_acceptance",
            accept_allowed=True,
            snapshot_id=record.id,
            snapshot_code=record.snapshot_code,
            content_hash=record.content_hash,
            snapshot_readiness=record.readiness,
            commercial_total=float(commercial_total),
            internal_total=float(internal_total) if internal_total is not None else None,
            acknowledged_owner_decision_codes=decision_codes,
        )

    return AcceptGateResult(
        gate_status="snapshot_blocked",
        accept_allowed=False,
        error_code="SNAPSHOT_READINESS_NOT_ALLOWED",
        message=f"Snapshot readiness {record.readiness!r} is not allowed for accept.",
        blockers=[record.readiness],
        snapshot_id=record.id,
        snapshot_code=record.snapshot_code,
        content_hash=record.content_hash,
        snapshot_readiness=record.readiness,
        commercial_total=float(commercial_total) if commercial_total is not None else None,
        internal_total=float(internal_total) if internal_total is not None else None,
    )


async def resolve_snapshot_for_accept(
    db: AsyncSession,
    quote: Quotes,
    linkage: dict[str, Any],
) -> QuoteSnapshotV2Record | None:
    """Return latest frozen snapshot for quote, or workspace fallback."""
    workspace_id = linkage_workspace_id(linkage)

    query = (
        select(QuoteSnapshotV2Record)
        .where(
            QuoteSnapshotV2Record.quote_id == quote.id,
            QuoteSnapshotV2Record.status == "frozen",
        )
        .order_by(QuoteSnapshotV2Record.version.desc())
        .limit(1)
    )
    result = await db.execute(query)
    record = result.scalar_one_or_none()
    if record is not None:
        return record

    if not workspace_id:
        return None

    ws_query = (
        select(QuoteSnapshotV2Record)
        .where(
            QuoteSnapshotV2Record.workspace_id == workspace_id,
            QuoteSnapshotV2Record.status == "frozen",
        )
        .order_by(QuoteSnapshotV2Record.version.desc())
        .limit(1)
    )
    ws_result = await db.execute(ws_query)
    return ws_result.scalar_one_or_none()


def build_accept_snapshot_metadata(
    record: QuoteSnapshotV2Record,
    gate: AcceptGateResult,
) -> dict[str, Any]:
    """Metadata stored in accept_decision linkage JSON."""
    return {
        "accepted_snapshot_v2_id": record.id,
        "snapshot_code": record.snapshot_code,
        "content_hash": record.content_hash,
        "snapshot_readiness": record.readiness,
        "snapshot_version": record.version,
        "gate_status": gate.gate_status,
        "accepted_commercial_total": gate.commercial_total,
        "internal_estimate_total": gate.internal_total,
        "acknowledged_owner_decision_codes": gate.acknowledged_owner_decision_codes,
        "pricing_source": "quote_snapshot_v2",
    }
