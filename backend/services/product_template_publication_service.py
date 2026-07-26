"""Product Template publication lifecycle — hard-gated by E2E readiness.

Rules:
- active=true is never treated as published.
- NULL publication_status = legacy unspecified; prior offerability policy continues.
- Explicit non-PUBLISHED status hard-blocks quote offerability.
- publish / mark_e2e_checked require readiness verdict in publishable set.
- TEMPLATE_ACTIVATION_V1: known_conflicts are warnings unless structural;
  AI defaults are valid commercial truth and must appear in publish evidence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

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
from services.template_activation_eligibility import (
    STRUCTURAL_KNOWN_CONFLICTS,
    build_activation_eligibility,
    classify_finding_scope,
)
from services.template_pricing_recipe_service import TemplatePricingRecipeService

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

    async def _pricing_context(self, template_code: str) -> dict[str, Any]:
        try:
            recipe = await TemplatePricingRecipeService(self.db).build_recipe(template_code)
        except Exception:
            return {
                "operational_readiness": None,
                "ai_decisions": [],
                "acm_treatment_allowed": None,
            }
        if recipe is None:
            return {
                "operational_readiness": None,
                "ai_decisions": [],
                "acm_treatment_allowed": None,
            }
        ai = [d.model_dump() for d in (recipe.ai_decisions or [])]
        acm = recipe.acm_acceptance
        return {
            "operational_readiness": getattr(recipe.readiness, "activation_status", None),
            "ai_decisions": ai,
            "acm_treatment_allowed": (
                acm.treatment_commercial_lines_allowed if acm and acm.applies else None
            ),
        }

    def _build_state(
        self,
        row: Product_templates,
        *,
        publish_blockers: list[str] | None = None,
        publish_warnings: list[str] | None = None,
        publish_allowed: bool | None = None,
        eligibility: dict[str, Any] | None = None,
    ) -> ProductTemplatePublicationState:
        status = normalize_publication_status(getattr(row, "publication_status", None))
        legacy = status is None
        effective = "LEGACY_UNSPECIFIED" if legacy else status
        blockers = list(publish_blockers or [])
        warnings = list(publish_warnings or [])
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

        elig = eligibility or {}
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
            publish_warnings=warnings,
            allowed_actions=allowed,  # type: ignore[arg-type]
            active_is_not_published=True,
            operational_readiness=elig.get("operational_readiness"),
            uses_ai_defaults=bool((elig.get("ai_defaults") or {}).get("uses_ai_defaults")),
            ai_decision_ids=list((elig.get("ai_defaults") or {}).get("ai_decision_ids") or []),
            publication_eligible=elig.get("publication_eligible"),
            activation_eligible=elig.get("activation_eligible"),
            optional_capability_blockers=list(elig.get("optional_capability_blockers") or []),
            recommended_target=elig.get("target_state"),
            eligibility=elig or None,
        )

    async def _eligibility_for_row(
        self,
        row: Product_templates,
        *,
        readiness: Any | None = None,
    ) -> dict[str, Any]:
        pricing = await self._pricing_context(str(row.template_code))
        if readiness is None:
            # Lightweight: no full re-run; use stored verdict
            return build_activation_eligibility(
                template_code=str(row.template_code),
                publication_status=normalize_publication_status(
                    getattr(row, "publication_status", None)
                ),
                effective_status=(
                    "LEGACY_UNSPECIFIED"
                    if normalize_publication_status(getattr(row, "publication_status", None))
                    is None
                    else str(getattr(row, "publication_status"))
                ),
                db_active=row.active is not False,
                e2e_verdict=getattr(row, "last_e2e_verdict", None),
                e2e_ready=False,
                known_conflicts=[],
                findings=[],
                pricing_activation=pricing.get("operational_readiness"),
                ai_decisions=pricing.get("ai_decisions") or [],
                acm_treatment_allowed=pricing.get("acm_treatment_allowed"),
            )

        findings = list(getattr(readiness, "findings", None) or [])
        return build_activation_eligibility(
            template_code=str(row.template_code),
            publication_status=normalize_publication_status(
                getattr(row, "publication_status", None)
            ),
            effective_status=(
                "LEGACY_UNSPECIFIED"
                if normalize_publication_status(getattr(row, "publication_status", None))
                is None
                else str(getattr(row, "publication_status"))
            ),
            db_active=row.active is not False,
            e2e_verdict=getattr(readiness, "verdict", None),
            e2e_ready=bool(getattr(readiness, "e2e_ready", False)),
            known_conflicts=list(getattr(readiness, "known_conflicts", None) or []),
            findings=findings,
            pricing_activation=pricing.get("operational_readiness"),
            ai_decisions=pricing.get("ai_decisions") or [],
            acm_treatment_allowed=pricing.get("acm_treatment_allowed"),
        )

    async def get_state(self, template_code: str) -> ProductTemplatePublicationState:
        row = await self._load_template(template_code)
        blockers, warnings, _ = await self._publish_blockers(row, run_readiness=False)
        status = normalize_publication_status(getattr(row, "publication_status", None))
        allowed = _ALLOWED.get(status, frozenset())
        eligibility = await self._eligibility_for_row(row, readiness=None)
        # Align eligibility.publish with cheap gate when last verdict is known.
        if eligibility.get("publication_eligible") is None:
            pass
        last = str(getattr(row, "last_e2e_verdict", None) or "")
        if last in PUBLISHABLE_VERDICTS and not blockers:
            eligibility["publication_eligible"] = True
            eligibility["target_state"] = "PUBLISHED"
        return self._build_state(
            row,
            publish_blockers=blockers,
            publish_warnings=warnings,
            publish_allowed=("publish" in allowed and not blockers),
            eligibility=eligibility,
        )

    def _split_publish_blockers(
        self,
        row: Product_templates,
        readiness: Any,
    ) -> tuple[list[str], list[str]]:
        blockers: list[str] = []
        warnings: list[str] = []
        if row.active is False:
            blockers.append("template_inactive")

        verdict = str(getattr(readiness, "verdict", None) or "").strip()
        if verdict and verdict not in PUBLISHABLE_VERDICTS:
            blockers.append(f"readiness_verdict_{verdict}")

        for conflict in getattr(readiness, "known_conflicts", None) or []:
            code = str(conflict)
            if code in STRUCTURAL_KNOWN_CONFLICTS:
                blockers.append(f"known_conflict:{code}")
            else:
                warnings.append(f"known_conflict:{code}")

        for f in getattr(readiness, "findings", None) or []:
            scope = classify_finding_scope(f)
            check_id = str(getattr(f, "check_id", None) or "finding")
            if scope == "structural" and (
                bool(getattr(f, "blocking", False))
                or str(getattr(f, "status", None)) in {"FAIL", "BLOCKED"}
            ):
                blockers.append(check_id)
            elif scope == "optional_capability":
                warnings.append(f"optional_capability:{check_id}")
            elif bool(getattr(f, "blocking", False)):
                blockers.append(check_id)

        return sorted(set(blockers)), sorted(set(warnings))[:40]

    async def _publish_blockers(
        self,
        row: Product_templates,
        *,
        run_readiness: bool,
    ) -> tuple[list[str], list[str], Any | None]:
        if not run_readiness:
            blockers: list[str] = []
            warnings: list[str] = []
            if row.active is False:
                blockers.append("template_inactive")
            last = str(getattr(row, "last_e2e_verdict", None) or "").strip()
            if last and last not in PUBLISHABLE_VERDICTS:
                blockers.append(f"last_e2e_verdict_not_publishable:{last}")
            return blockers, warnings, None

        readiness = await ProductE2EReadinessService(self.db).run_static(str(row.template_code))
        row.last_e2e_verdict = readiness.verdict
        row.last_e2e_checked_at = _utcnow()
        blockers, warnings = self._split_publish_blockers(row, readiness)
        return blockers, warnings, readiness

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
        evidence: dict[str, Any] = {"action": action, "from": status, "to": target}

        needs_readiness = action in {"mark_e2e_checked", "publish"} and request.run_readiness
        blockers: list[str] = []
        warnings: list[str] = []
        readiness = None
        if needs_readiness:
            blockers, warnings, readiness = await self._publish_blockers(
                row, run_readiness=True
            )
            readiness_verdict = getattr(row, "last_e2e_verdict", None)
            readiness_ready = readiness_verdict in PUBLISHABLE_VERDICTS
            pricing = await self._pricing_context(str(row.template_code))
            evidence["readiness_verdict"] = readiness_verdict
            evidence["publish_blockers"] = blockers
            evidence["publish_warnings"] = warnings
            evidence["uses_ai_defaults"] = bool(pricing.get("ai_decisions"))
            evidence["ai_decision_ids"] = [
                str(d.get("decision_id"))
                for d in (pricing.get("ai_decisions") or [])
                if d.get("decision_id")
            ]
            evidence["operational_readiness"] = pricing.get("operational_readiness")
            evidence["active_is_not_published"] = True
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
                        "warnings": warnings,
                        "active_is_not_published": True,
                        "last_e2e_verdict": readiness_verdict,
                        "uses_ai_defaults": evidence["uses_ai_defaults"],
                        "ai_decision_ids": evidence["ai_decision_ids"],
                    },
                )

        # Idempotent publish: already PUBLISHED → no double version bump
        if action == "publish" and status == "PUBLISHED":
            eligibility = await self._eligibility_for_row(row, readiness=readiness)
            state = self._build_state(
                row,
                publish_blockers=[],
                publish_warnings=warnings,
                publish_allowed=False,
                eligibility=eligibility,
            )
            return ProductTemplatePublicationTransitionResponse(
                ok=True,
                state=state,
                readiness_verdict=readiness_verdict,
                readiness_e2e_ready=readiness_ready,
                message="publication_status already PUBLISHED (idempotent)",
                evidence={**evidence, "idempotent": True},
            )

        row.publication_status = target
        if target == "PUBLISHED":
            version = int(getattr(row, "publication_version", None) or 0)
            row.publication_version = version + 1 if version >= 0 else 1
            row.published_at = _utcnow()
            row.published_by = (
                (request.actor or "product_system_admin").strip() or "product_system_admin"
            )
        if target in {"DRAFT", "VALIDATED"} and status == "DEPRECATED":
            row.published_at = None
            row.published_by = None

        await self.db.commit()
        await self.db.refresh(row)

        eligibility = await self._eligibility_for_row(row, readiness=readiness)
        state = self._build_state(
            row,
            publish_blockers=[],
            publish_warnings=warnings,
            publish_allowed=False,
            eligibility=eligibility,
        )
        return ProductTemplatePublicationTransitionResponse(
            ok=True,
            state=state,
            readiness_verdict=readiness_verdict,
            readiness_e2e_ready=readiness_ready,
            message=f"publication_status → {target}",
            evidence=evidence,
        )
