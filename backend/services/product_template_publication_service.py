"""Product Template publication lifecycle — hard-gated by E2E readiness.

Rules:
- active=true is never treated as published.
- NULL publication_status = legacy unspecified; prior offerability policy continues.
- Explicit non-PUBLISHED status hard-blocks quote offerability.
- publish / mark_e2e_checked require readiness verdict in publishable set.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.product_templates import Product_templates
from schemas.product_template_publication import (
    PublicationAction,
    PublicationStatus,
    ProductTemplatePublicationState,
    ProductTemplatePublicationTransitionRequest,
    ProductTemplatePublicationTransitionResponse,
)
from services.product_e2e_readiness_service import ProductE2EReadinessService

PUBLICATION_STATUSES: tuple[PublicationStatus, ...] = (
    "DRAFT",
    "VALIDATED",
    "E2E_CHECKED",
    "PUBLISHED",
    "DEPRECATED",
    "ARCHIVED",
)

PUBLISHABLE_VERDICTS = frozenset(
    {
        "STATIC_READY",
        "STATIC_READY_WITH_WARNINGS",
        "RUNTIME_READY",
    }
)

_ACTION_TARGET: dict[PublicationAction, PublicationStatus] = {
    "enter_draft": "DRAFT",
    "mark_validated": "VALIDATED",
    "mark_e2e_checked": "E2E_CHECKED",
    "publish": "PUBLISHED",
    "deprecate": "DEPRECATED",
    "archive": "ARCHIVED",
    "reopen_draft": "DRAFT",
}

_ALLOWED: dict[Optional[PublicationStatus], frozenset[PublicationAction]] = {
    None: frozenset({"enter_draft", "mark_e2e_checked", "publish"}),
    "DRAFT": frozenset({"mark_validated", "deprecate"}),
    "VALIDATED": frozenset({"enter_draft", "mark_e2e_checked", "deprecate"}),
    "E2E_CHECKED": frozenset({"mark_validated", "publish", "deprecate"}),
    "PUBLISHED": frozenset({"deprecate"}),
    "DEPRECATED": frozenset({"archive", "reopen_draft"}),
    "ARCHIVED": frozenset(),
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc).isoformat()
    return value.isoformat()


def normalize_publication_status(raw: object) -> PublicationStatus | None:
    text = str(raw or "").strip().upper()
    if not text:
        return None
    if text in PUBLICATION_STATUSES:
        return text  # type: ignore[return-value]
    return None


def publication_blocks_offerability(raw_status: object) -> bool:
    """Explicit lifecycle status other than PUBLISHED blocks offerability."""
    status = normalize_publication_status(raw_status)
    if status is None:
        return False
    return status != "PUBLISHED"


def apply_publication_offerability_gate(
    *,
    legacy_quote_offerable: bool,
    publication_status: object,
) -> tuple[bool, str]:
    """Return (offerable, gate_reason). Preserves legacy when status is NULL."""
    status = normalize_publication_status(publication_status)
    if status is None:
        return legacy_quote_offerable, "legacy_unspecified_keeps_prior_policy"
    if status == "PUBLISHED":
        return legacy_quote_offerable, "published_defers_to_policy_and_active"
    return False, f"publication_status_{status.lower()}_blocks_offerability"


class ProductTemplatePublicationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _load_template(self, template_code: str) -> Product_templates:
        code = (template_code or "").strip()
        if not code:
            raise HTTPException(status_code=400, detail={"error": "template_code_required"})
        row = (
            await self.db.execute(
                select(Product_templates).where(Product_templates.template_code == code).limit(1)
            )
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(
                status_code=404,
                detail={"error": "template_not_found", "template_code": code},
            )
        return row

    def _build_state(
        self,
        row: Product_templates,
        *,
        publish_blockers: list[str] | None = None,
        publish_allowed: bool | None = None,
    ) -> ProductTemplatePublicationState:
        status = normalize_publication_status(getattr(row, "publication_status", None))
        legacy = status is None
        effective = "LEGACY_UNSPECIFIED" if legacy else status
        blockers = list(publish_blockers or [])
        allowed = sorted(_ALLOWED.get(status, frozenset()))
        if publish_allowed is None:
            publish_allowed = "publish" in allowed and not blockers

        offer_gate = (
            "legacy_unspecified_keeps_prior_policy"
            if legacy
            else (
                "published_requires_active_and_policy"
                if status == "PUBLISHED"
                else f"blocked_by_{str(status).lower()}"
            )
        )

        return ProductTemplatePublicationState(
            template_code=str(row.template_code),
            template_id=int(row.id),
            db_active=row.active is not False,
            publication_status=status,
            effective_status=str(effective),
            legacy_unspecified=legacy,
            publication_version=getattr(row, "publication_version", None),
            last_e2e_verdict=getattr(row, "last_e2e_verdict", None),
            last_e2e_checked_at=_iso(getattr(row, "last_e2e_checked_at", None)),
            published_at=_iso(getattr(row, "published_at", None)),
            published_by=getattr(row, "published_by", None),
            offerability_gate=offer_gate,
            publish_allowed=bool(publish_allowed),
            publish_blockers=blockers,
            allowed_actions=allowed,  # type: ignore[arg-type]
            active_is_not_published=True,
        )

    async def get_state(self, template_code: str) -> ProductTemplatePublicationState:
        row = await self._load_template(template_code)
        blockers = await self._publish_blockers(row, run_readiness=False)
        status = normalize_publication_status(getattr(row, "publication_status", None))
        allowed = _ALLOWED.get(status, frozenset())
        return self._build_state(
            row,
            publish_blockers=blockers,
            publish_allowed=("publish" in allowed and not blockers),
        )

    async def _publish_blockers(
        self,
        row: Product_templates,
        *,
        run_readiness: bool,
    ) -> list[str]:
        blockers: list[str] = []
        if row.active is False:
            blockers.append("template_inactive")

        if not run_readiness:
            # Cheap preview: use last stored verdict when present.
            last = str(getattr(row, "last_e2e_verdict", None) or "").strip()
            if last and last not in PUBLISHABLE_VERDICTS:
                blockers.append(f"last_e2e_verdict_not_publishable:{last}")
            return blockers

        readiness = await ProductE2EReadinessService(self.db).run_static(str(row.template_code))
        row.last_e2e_verdict = readiness.verdict
        row.last_e2e_checked_at = _utcnow()
        if readiness.verdict not in PUBLISHABLE_VERDICTS and not readiness.e2e_ready:
            blockers.append(f"readiness_verdict_{readiness.verdict}")
        if readiness.known_conflicts:
            for conflict in readiness.known_conflicts:
                blockers.append(f"known_conflict:{conflict}")
        blocking_findings = [f for f in readiness.findings if f.blocking]
        if blocking_findings:
            blockers.append(f"blocking_findings:{len(blocking_findings)}")
        return blockers

    async def transition(
        self,
        template_code: str,
        request: ProductTemplatePublicationTransitionRequest,
    ) -> ProductTemplatePublicationTransitionResponse:
        row = await self._load_template(template_code)
        status = normalize_publication_status(getattr(row, "publication_status", None))
        action = request.action
        allowed = _ALLOWED.get(status, frozenset())
        if action not in allowed:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "publication_transition_not_allowed",
                    "from": status,
                    "action": action,
                    "allowed_actions": sorted(allowed),
                },
            )

        target = _ACTION_TARGET[action]
        readiness_verdict: str | None = None
        readiness_ready: bool | None = None
        evidence: dict = {"action": action, "from": status, "to": target}

        needs_readiness = action in {"mark_e2e_checked", "publish"} and request.run_readiness
        blockers: list[str] = []
        if needs_readiness:
            blockers = await self._publish_blockers(row, run_readiness=True)
            readiness_verdict = getattr(row, "last_e2e_verdict", None)
            readiness_ready = readiness_verdict in PUBLISHABLE_VERDICTS
            evidence["readiness_verdict"] = readiness_verdict
            evidence["publish_blockers"] = blockers
            # Persist last readiness evidence even when publish is blocked (no status change).
            await self.db.commit()
            await self.db.refresh(row)
            if blockers:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "publication_blocked_by_e2e_readiness",
                        "template_code": str(row.template_code),
                        "action": action,
                        "readiness_verdict": readiness_verdict,
                        "blockers": blockers,
                        "active_is_not_published": True,
                        "last_e2e_verdict": readiness_verdict,
                    },
                )

        row.publication_status = target
        if target == "PUBLISHED":
            version = int(getattr(row, "publication_version", None) or 0)
            row.publication_version = version + 1 if version >= 0 else 1
            row.published_at = _utcnow()
            row.published_by = (request.actor or "product_system_admin").strip() or "product_system_admin"
        if target in {"DRAFT", "VALIDATED"} and status == "DEPRECATED":
            row.published_at = None
            row.published_by = None

        await self.db.commit()
        await self.db.refresh(row)

        state = self._build_state(row, publish_blockers=[], publish_allowed=False)
        return ProductTemplatePublicationTransitionResponse(
            ok=True,
            state=state,
            readiness_verdict=readiness_verdict,
            readiness_e2e_ready=readiness_ready,
            message=f"publication_status → {target}",
            evidence=evidence,
        )
