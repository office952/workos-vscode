"""Dual Quote Snapshot V2 builder (Step 8 MVP).

Composes CommercialPriceProposal (7G) + EstimatedInternalCost (7H) without duplicating
pricing logic. Does NOT call /price, QuoteOrchestrator, or CostEngine.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.quote_snapshot_v2 import QuoteSnapshotV2Record

from schemas.commercial_price_proposal import CommercialPriceProposalPreview
from schemas.estimated_internal_cost import EstimatedInternalCostPreview
from schemas.quote_snapshot_v2 import (
    QUOTE_SNAPSHOT_V2_SOURCE,
    QUOTE_SNAPSHOT_V2_VERSION,
    QuoteSnapshotBlocker,
    QuoteSnapshotOwnerDecision,
    QuoteSnapshotProvenanceEntry,
    QuoteSnapshotReadiness,
    QuoteSnapshotV2,
)
from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.estimated_internal_cost_service import EstimatedInternalCostService
from services.product_aggregate_service import ProductAggregateService
from services.product_definition_builder_service import ProductDefinitionBuilderService

SUPPORTED_TEMPLATES = frozenset({"TPL-VOLUMETRIC-LETTERS_v2"})

PERSISTENCE_AVAILABLE = True

FREEZE_ALLOWED_READINESS = frozenset(
    {"ready_for_owner_review", "partial_with_owner_decisions"}
)
HARD_BLOCKED_READINESS = frozenset(
    {
        "blocked_missing_commercial",
        "blocked_missing_internal",
        "blocked_snapshot_conflict",
        "blocked_forbidden_path",
    }
)

FORBIDDEN_IMPORT_SUBSTRINGS = (
    "quote_orchestrator",
    "cost_engine_service",
    "aggregate_cost_bom_price_bridge",
)


def _merge_owner_decisions(
    commercial: CommercialPriceProposalPreview,
    internal: EstimatedInternalCostPreview,
) -> list[QuoteSnapshotOwnerDecision]:
    merged: list[QuoteSnapshotOwnerDecision] = []
    seen: set[str] = set()
    for decision in commercial.unknown_owner_decisions:
        key = f"cpp:{decision.code}"
        if key in seen:
            continue
        seen.add(key)
        merged.append(
            QuoteSnapshotOwnerDecision(
                code=decision.code,
                label=decision.label,
                source="commercial_price_proposal",
                module_code=decision.module_code,
                detail=decision.detail,
            )
        )
    for decision in internal.unknown_owner_decisions:
        key = f"eic:{decision.code}"
        if key in seen:
            continue
        seen.add(key)
        merged.append(
            QuoteSnapshotOwnerDecision(
                code=decision.code,
                label=decision.label,
                source="estimated_internal_cost",
                module_code=decision.module_code,
                detail=decision.detail,
            )
        )
    return merged


def _merge_blockers(
    commercial: CommercialPriceProposalPreview,
    internal: EstimatedInternalCostPreview,
) -> list[QuoteSnapshotBlocker]:
    blockers: list[QuoteSnapshotBlocker] = []
    for blocker in commercial.commercial_blockers:
        blockers.append(
            QuoteSnapshotBlocker(
                code=blocker.code,
                message=blocker.message,
                source="commercial_price_proposal",
                module_code=blocker.module_code,
            )
        )
    for blocker in internal.internal_blockers:
        blockers.append(
            QuoteSnapshotBlocker(
                code=blocker.code,
                message=blocker.message,
                source="estimated_internal_cost",
                module_code=blocker.module_code,
                material_code=blocker.material_code,
            )
        )
    return blockers


def _merge_warnings(
    commercial: CommercialPriceProposalPreview,
    internal: EstimatedInternalCostPreview,
) -> list[str]:
    warnings: list[str] = []
    seen: set[str] = set()
    for warning in commercial.warnings + internal.warnings:
        if warning not in seen:
            seen.add(warning)
            warnings.append(warning)
    return warnings


def compute_readiness(
    commercial: CommercialPriceProposalPreview,
    internal: EstimatedInternalCostPreview,
) -> QuoteSnapshotReadiness:
    """Derive snapshot readiness from 7G/7H statuses — never hides blockers."""
    if commercial.forbidden_hourly_usage_detected or internal.hourly_contamination_detected:
        return "blocked_forbidden_path"

    commercial_blocked = commercial.status == "blocked"
    internal_blocked = internal.status == "blocked"
    has_owner = bool(commercial.unknown_owner_decisions or internal.unknown_owner_decisions)

    if commercial_blocked and internal_blocked:
        return "blocked_snapshot_conflict"
    if commercial_blocked:
        return "partial_with_owner_decisions" if has_owner else "blocked_missing_commercial"
    if internal_blocked:
        return "partial_with_owner_decisions" if has_owner else "blocked_missing_internal"

    if (
        commercial.status == "partial"
        or internal.status == "partial"
        or has_owner
    ):
        return "partial_with_owner_decisions"

    if commercial.quote_ready_for_commercial_review and internal.ready_for_quote_snapshot:
        return "ready_for_owner_review"

    return "partial_with_owner_decisions"


def _build_provenance(
    *,
    workspace_id: str | None,
    quote_input: dict[str, Any] | None,
    commercial: CommercialPriceProposalPreview,
    internal: EstimatedInternalCostPreview,
    include_aggregate: bool,
) -> list[QuoteSnapshotProvenanceEntry]:
    entries: list[QuoteSnapshotProvenanceEntry] = [
        QuoteSnapshotProvenanceEntry(
            key="quote_snapshot_v2",
            source=QUOTE_SNAPSHOT_V2_SOURCE,
            detail=f"version={QUOTE_SNAPSHOT_V2_VERSION} read_only_compose=true",
        ),
        QuoteSnapshotProvenanceEntry(
            key="commercial_price_proposal",
            source="commercial_price_proposal_service",
            detail=f"status={commercial.status} source={commercial.source}",
        ),
        QuoteSnapshotProvenanceEntry(
            key="estimated_internal_cost",
            source="estimated_internal_cost_service",
            detail=f"status={internal.status} source={internal.source}",
        ),
        QuoteSnapshotProvenanceEntry(
            key="product_definition",
            source="product_definition_builder_service",
            detail=f"workspace_id={workspace_id or 'none'}",
        ),
    ]
    if include_aggregate:
        entries.append(
            QuoteSnapshotProvenanceEntry(
                key="product_aggregate",
                source="product_aggregate_service",
                detail="read_only=true",
            )
        )
    if workspace_id:
        entries.append(
            QuoteSnapshotProvenanceEntry(
                key="intake_v6_workspace",
                source="workspace_id",
                detail=workspace_id,
            )
        )
    if quote_input:
        entries.append(
            QuoteSnapshotProvenanceEntry(
                key="quote_input",
                source="request_body",
                detail="read_only_no_pricing_engine",
            )
        )
    for entry in commercial.provenance:
        entries.append(
            QuoteSnapshotProvenanceEntry(
                key=f"commercial:{entry.key}",
                source=entry.source,
                detail=entry.detail,
            )
        )
    for entry in internal.provenance:
        entries.append(
            QuoteSnapshotProvenanceEntry(
                key=f"internal:{entry.key}",
                source=entry.source,
                detail=entry.detail,
            )
        )
    entries.append(
        QuoteSnapshotProvenanceEntry(
            key="assembled_at",
            source=QUOTE_SNAPSHOT_V2_SOURCE,
            detail=datetime.now(timezone.utc).isoformat(),
        )
    )
    return entries


def _parse_quote_id(quote_id: str | int | None) -> int | None:
    if quote_id is None:
        return None
    if isinstance(quote_id, int):
        return quote_id
    stripped = str(quote_id).strip()
    if not stripped:
        return None
    return int(stripped)


def _status_for_readiness(readiness: QuoteSnapshotReadiness) -> str:
    """Persisted snapshot rows are frozen; readiness carries review/partial semantics."""
    if readiness in FREEZE_ALLOWED_READINESS:
        return "frozen"
    return "draft"


class QuoteSnapshotV2Service:
    """Build dual quote snapshot preview by composing 7G + 7H — no DB writes in dry-run."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        cpp_service: CommercialPriceProposalService | None = None,
        eic_service: EstimatedInternalCostService | None = None,
        pd_builder: ProductDefinitionBuilderService | None = None,
        aggregate_svc: ProductAggregateService | None = None,
    ) -> None:
        self._db = db
        self._cpp = cpp_service or CommercialPriceProposalService(db)
        self._eic = eic_service or EstimatedInternalCostService(db)
        self._pd_builder = pd_builder or ProductDefinitionBuilderService(db)
        self._aggregate_svc = aggregate_svc or ProductAggregateService(db)

    async def build_preview(
        self,
        template_code: str,
        *,
        workspace_id: str | None = None,
        quote_id: str | None = None,
        quote_input: dict[str, Any] | None = None,
        currency: str = "RON",
        requested_by: str | None = None,
    ) -> QuoteSnapshotV2 | None:
        if template_code not in SUPPORTED_TEMPLATES:
            return None

        commercial = await self._cpp.build_preview(
            template_code,
            workspace_id=workspace_id,
            quote_input=quote_input,
            currency=currency,
        )
        internal = await self._eic.build_preview(
            template_code,
            workspace_id=workspace_id,
            quote_input=quote_input,
            currency=currency,
        )
        if commercial is None or internal is None:
            return None

        pd = await self._pd_builder.build_preview(template_code, workspace_id=workspace_id)
        aggregate = await self._aggregate_svc.build(template_code)

        owner_decisions = _merge_owner_decisions(commercial, internal)
        blockers = _merge_blockers(commercial, internal)
        warnings = _merge_warnings(commercial, internal)
        readiness = compute_readiness(commercial, internal)
        provenance = _build_provenance(
            workspace_id=workspace_id,
            quote_input=quote_input,
            commercial=commercial,
            internal=internal,
            include_aggregate=aggregate is not None,
        )

        notes = [
            "Dual Quote Snapshot V2 preview — Step 8 MVP.",
            "Commercial and internal totals are never merged.",
            "Does not call /price, CostEngine, or QuoteOrchestrator.",
        ]
        if requested_by:
            notes.append(f"requested_by={requested_by}")

        return QuoteSnapshotV2(
            quote_id=quote_id,
            workspace_id=workspace_id,
            template_code=template_code,
            product_definition_snapshot=pd,
            product_aggregate_snapshot=aggregate,
            commercial_price_proposal_snapshot=commercial,
            estimated_internal_cost_snapshot=internal,
            owner_decisions_snapshot=owner_decisions,
            warnings_snapshot=warnings,
            blockers_snapshot=blockers,
            readiness=readiness,
            version=1,
            provenance=provenance,
            persist_status="not_persisted",
            notes=notes,
            input_summary={
                "workspace_id": workspace_id,
                "quote_id": quote_id,
                "has_quote_input": quote_input is not None,
                "commercial_status": commercial.status,
                "internal_status": internal.status,
                "commercial_total": commercial.commercial_total,
                "internal_total": internal.estimated_total_internal_cost,
            },
        )

    async def get_by_snapshot_code(self, snapshot_code: str) -> QuoteSnapshotV2 | None:
        query = select(QuoteSnapshotV2Record).where(
            QuoteSnapshotV2Record.snapshot_code == snapshot_code
        )
        result = await self._db.execute(query)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return QuoteSnapshotV2.model_validate_json(record.snapshot_json)

    async def _generate_snapshot_code(self) -> str:
        year = datetime.now().year
        query = select(func.count(QuoteSnapshotV2Record.id))
        result = await self._db.execute(query)
        count = result.scalar() or 0
        return f"QSN2-{year}-{count + 1:04d}"

    async def _get_next_version(
        self,
        *,
        quote_id: int | None,
        workspace_id: str | None,
    ) -> int:
        if quote_id is not None:
            query = select(func.max(QuoteSnapshotV2Record.version)).where(
                QuoteSnapshotV2Record.quote_id == quote_id
            )
        else:
            query = select(func.max(QuoteSnapshotV2Record.version)).where(
                QuoteSnapshotV2Record.workspace_id == workspace_id
            )
        result = await self._db.execute(query)
        max_version = result.scalar() or 0
        return max_version + 1

    async def _persist_snapshot(
        self,
        snapshot: QuoteSnapshotV2,
        *,
        frozen_by: str | None,
    ) -> QuoteSnapshotV2Record:
        now = datetime.now(timezone.utc)
        parsed_quote_id = _parse_quote_id(snapshot.quote_id)
        version = await self._get_next_version(
            quote_id=parsed_quote_id,
            workspace_id=snapshot.workspace_id,
        )
        snapshot.version = version
        snapshot.frozen_at = now.isoformat()
        snapshot.frozen_by = frozen_by

        snapshot_json = snapshot.model_dump_json()
        content_hash = hashlib.sha256(snapshot_json.encode()).hexdigest()[:32]
        snapshot_code = await self._generate_snapshot_code()
        status = _status_for_readiness(snapshot.readiness)

        record = QuoteSnapshotV2Record(
            snapshot_code=snapshot_code,
            snapshot_version=QUOTE_SNAPSHOT_V2_VERSION,
            version=version,
            quote_id=parsed_quote_id,
            workspace_id=snapshot.workspace_id,
            template_code=snapshot.template_code,
            status=status,
            readiness=snapshot.readiness,
            frozen_at=now,
            frozen_by=frozen_by,
            snapshot_json=snapshot_json,
            content_hash=content_hash,
            notes="\n".join(snapshot.notes) if snapshot.notes else None,
        )
        self._db.add(record)
        await self._db.commit()
        await self._db.refresh(record)

        snapshot.snapshot_id = str(record.id)
        snapshot.snapshot_code = record.snapshot_code
        snapshot.persist_status = "persisted"
        return record

    async def freeze(
        self,
        template_code: str,
        *,
        workspace_id: str | None = None,
        quote_id: str | None = None,
        quote_input: dict[str, Any] | None = None,
        currency: str = "RON",
        frozen_by: str | None = None,
    ) -> QuoteSnapshotV2 | None:
        """Freeze dual snapshot — persists when readiness and identity allow."""
        snapshot = await self.build_preview(
            template_code,
            workspace_id=workspace_id,
            quote_id=quote_id,
            quote_input=quote_input,
            currency=currency,
            requested_by=frozen_by,
        )
        if snapshot is None:
            return None

        if not PERSISTENCE_AVAILABLE:
            snapshot.persist_status = "blocked"
            snapshot.readiness = "blocked_schema_missing"
            snapshot.notes.append(
                "NEEDS_OWNER_DECISION_DB_SCHEMA — persistence table unavailable."
            )
            return snapshot

        if not quote_id and not workspace_id:
            snapshot.persist_status = "blocked"
            snapshot.notes.append(
                "FREEZE_BLOCKED: at least one of quote_id or workspace_id is required."
            )
            return snapshot

        if snapshot.readiness in HARD_BLOCKED_READINESS:
            snapshot.persist_status = "blocked"
            snapshot.notes.append(
                f"FREEZE_BLOCKED: readiness={snapshot.readiness} — hard blocked, not persisted."
            )
            return snapshot

        if snapshot.readiness not in FREEZE_ALLOWED_READINESS:
            snapshot.persist_status = "blocked"
            snapshot.notes.append(
                f"FREEZE_BLOCKED: readiness={snapshot.readiness} not allowed for persist."
            )
            return snapshot

        await self._persist_snapshot(snapshot, frozen_by=frozen_by)
        return snapshot
