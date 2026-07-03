"""Shared canonical readiness helpers for Intake V6 flows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from schemas.intake_v4 import IntakeV4PricingInputPreviewResponse
from services.intake_v4_internal_draft_quote_policy_service import resolve_internal_draft_quote_status_label
from services.product_definition_builder_service import ProductDefinitionBuilderService


@dataclass(frozen=True)
class IntakeV6CanonicalReadinessFindings:
    fatal_blockers: list[str]
    review_warnings: list[str]


def findings_summary(findings: IntakeV6CanonicalReadinessFindings) -> dict[str, Any]:
    return {
        "fatal_blockers": list(findings.fatal_blockers),
        "review_warnings": list(findings.review_warnings),
        "fatal_count": len(findings.fatal_blockers),
        "warning_count": len(findings.review_warnings),
    }


def dedupe_codes(codes: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for code in codes:
        token = str(code).strip()
        if not token or token in seen:
            continue
        seen.add(token)
        ordered.append(token)
    return ordered


async def collect_canonical_readiness_findings(
    db: AsyncSession,
    *,
    workspace_id: str,
    template_code: str,
) -> IntakeV6CanonicalReadinessFindings:
    preview = await ProductDefinitionBuilderService(db).build_preview(
        template_code,
        workspace_id=workspace_id,
    )
    if preview is None:
        return IntakeV6CanonicalReadinessFindings(
            fatal_blockers=["product_definition_preview_unavailable"],
            review_warnings=[],
        )

    fatal: list[str] = []
    review: list[str] = []
    for field in list(preview.validation.missing_required_fields or []):
        fatal.append(f"canonical_missing_required_field:{field}")
    for issue in list(preview.validation.invalid_combinations or []):
        fatal.append(f"canonical_invalid_combination:{issue}")
    for warning in list(preview.validation.unresolved_warnings or []):
        review.append(f"canonical_unresolved_warning:{warning}")
    return IntakeV6CanonicalReadinessFindings(
        fatal_blockers=fatal,
        review_warnings=review,
    )


def merge_policy_findings(*, policy: Any, findings: IntakeV6CanonicalReadinessFindings) -> dict[str, Any]:
    fatal_blockers = dedupe_codes([*policy.fatal_blockers, *findings.fatal_blockers])
    review_warnings = dedupe_codes([*policy.review_warnings, *findings.review_warnings])
    can_create = not fatal_blockers
    has_review_only_warnings = bool(review_warnings)
    return {
        "fatal_blockers": fatal_blockers,
        "review_warnings": review_warnings,
        "blockers": [*fatal_blockers, *review_warnings],
        "can_create_internal_draft_quote": can_create,
        "client_send_allowed": not has_review_only_warnings and can_create,
        "accept_allowed": not has_review_only_warnings and can_create,
        "convert_to_order_allowed": not has_review_only_warnings and can_create,
        "production_allowed": not has_review_only_warnings and can_create,
        "status_label": resolve_internal_draft_quote_status_label(fatal_blockers, review_warnings),
    }


def enrich_pricing_preview_with_canonical_findings(
    preview: IntakeV4PricingInputPreviewResponse,
    findings: IntakeV6CanonicalReadinessFindings,
) -> IntakeV4PricingInputPreviewResponse:
    adapter_blockers = dedupe_codes([*list(preview.adapter_blockers or []), *findings.fatal_blockers])
    adapter_warnings = dedupe_codes([*list(preview.adapter_warnings or []), *findings.review_warnings])
    is_ready_for_quote = bool(preview.is_ready_for_quote) and not adapter_blockers
    adapter_status = preview.adapter_status
    if adapter_blockers:
        adapter_status = "blocked"
    elif adapter_warnings and adapter_status == "ready":
        adapter_status = "review_required"

    quote_input_payload = dict(preview.quote_input_payload or {})
    quote_input_payload.setdefault("canonical_readiness", {})
    quote_input_payload["canonical_readiness"] = {
        "fatal_blockers": list(findings.fatal_blockers),
        "review_warnings": list(findings.review_warnings),
    }

    return preview.model_copy(
        update={
            "is_ready_for_quote": is_ready_for_quote,
            "adapter_status": adapter_status,
            "adapter_blockers": adapter_blockers,
            "adapter_warnings": adapter_warnings,
            "quote_input_payload": quote_input_payload,
        }
    )