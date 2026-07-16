"""Readiness severity channel split — Aggregate info vs Order/Execution review."""

from __future__ import annotations

from types import SimpleNamespace

from services.intake_v4_internal_draft_quote_policy_service import (
    client_order_production_flags_for_quote,
)
from services.intake_v6_canonical_readiness_service import (
    IntakeV6CanonicalReadinessFindings,
    classify_canonical_unresolved_warning,
    merge_policy_findings,
    partition_canonical_unresolved_warnings,
)


def test_partition_routes_info_codes_to_diagnostics() -> None:
    review, diagnostic = partition_canonical_unresolved_warnings(
        [
            "DOSSIER_METADATA_ONLY: Blueprint dossier available for inspection only.",
            "CANONICAL_CONTRACT_AUTHORITY: ProductAggregate compiled from canonical contracts.",
            "TEMPLATE_IDENTITY: Template identity resolution trace.",
            "TRIGGER_FIELD_MISMATCH: structura_suport link=metal_support_required intake=finish_setup.mounting_system",
            "TRIGGER_FIELD_MISMATCH: Module link trigger_field 'metal_support_required' may not match.",
            "artwork_execution_undecided:logo-left",
        ]
    )
    assert review == [
        "TRIGGER_FIELD_MISMATCH: structura_suport link=metal_support_required intake=finish_setup.mounting_system",
        "TRIGGER_FIELD_MISMATCH: Module link trigger_field 'metal_support_required' may not match.",
        "artwork_execution_undecided:logo-left",
    ]
    assert len(diagnostic) == 3
    assert "DOSSIER_METADATA_ONLY" in diagnostic[0]
    assert "CANONICAL_CONTRACT_AUTHORITY" in diagnostic[1]
    assert "TEMPLATE_IDENTITY" in diagnostic[2]
    assert all("TRIGGER_FIELD_MISMATCH" not in d for d in diagnostic)


def test_classify_strips_canonical_prefix() -> None:
    assert (
        classify_canonical_unresolved_warning(
            "canonical_unresolved_warning:DOSSIER_METADATA_ONLY: Blueprint..."
        )
        == "diagnostic"
    )
    assert (
        classify_canonical_unresolved_warning(
            "canonical_unresolved_warning:TRIGGER_FIELD_MISMATCH: structura_suport..."
        )
        == "review"
    )


def test_merge_only_diagnostics_allows_accept_when_no_fatal() -> None:
    policy = SimpleNamespace(fatal_blockers=[], review_warnings=[])
    findings = IntakeV6CanonicalReadinessFindings(
        fatal_blockers=[],
        review_warnings=[],
        diagnostic_warnings=[
            "canonical_unresolved_warning:DOSSIER_METADATA_ONLY: Blueprint...",
            "canonical_unresolved_warning:CANONICAL_CONTRACT_AUTHORITY: compiled...",
            "canonical_unresolved_warning:TEMPLATE_IDENTITY: trace...",
        ],
    )
    merged = merge_policy_findings(policy=policy, findings=findings)
    assert merged["can_create_internal_draft_quote"] is True
    assert merged["accept_allowed"] is True
    assert merged["convert_to_order_allowed"] is True
    assert merged["production_allowed"] is True
    assert merged["review_warnings"] == []
    assert len(merged["diagnostic_warnings"]) == 3
    flags = client_order_production_flags_for_quote(review_warnings=merged["review_warnings"])
    assert flags["accept_allowed"] is True
    assert flags["production_allowed"] is True


def test_merge_trigger_blocks_order_execution_not_quote_create() -> None:
    policy = SimpleNamespace(fatal_blockers=[], review_warnings=[])
    findings = IntakeV6CanonicalReadinessFindings(
        fatal_blockers=[],
        review_warnings=[
            "canonical_unresolved_warning:TRIGGER_FIELD_MISMATCH: metal_support_required vs mounting_system",
        ],
        diagnostic_warnings=[
            "canonical_unresolved_warning:DOSSIER_METADATA_ONLY: Blueprint...",
        ],
    )
    merged = merge_policy_findings(policy=policy, findings=findings)
    assert merged["can_create_internal_draft_quote"] is True
    assert merged["accept_allowed"] is False
    assert merged["convert_to_order_allowed"] is False
    assert merged["production_allowed"] is False
    assert any("TRIGGER_FIELD_MISMATCH" in w for w in merged["review_warnings"])
    assert any("DOSSIER_METADATA_ONLY" in w for w in merged["diagnostic_warnings"])
    assert all("DOSSIER_METADATA_ONLY" not in w for w in merged["review_warnings"])


def test_operator_confirmation_fatal_still_blocks_quote_create() -> None:
    policy = SimpleNamespace(
        fatal_blockers=["operator_confirmation_missing"],
        review_warnings=[],
    )
    findings = IntakeV6CanonicalReadinessFindings(
        fatal_blockers=[],
        review_warnings=[],
        diagnostic_warnings=[
            "canonical_unresolved_warning:TEMPLATE_IDENTITY: trace...",
        ],
    )
    merged = merge_policy_findings(policy=policy, findings=findings)
    assert merged["can_create_internal_draft_quote"] is False
    assert "operator_confirmation_missing" in merged["fatal_blockers"]
    assert merged["accept_allowed"] is False
    assert merged["diagnostic_warnings"]


def test_enrich_pricing_preview_keeps_diagnostics_out_of_adapter_warnings() -> None:
    from schemas.intake_v4 import IntakeV4PricingInputPreviewResponse
    from services.intake_v6_canonical_readiness_service import (
        enrich_pricing_preview_with_canonical_findings,
    )

    preview = IntakeV4PricingInputPreviewResponse(
        workspace_id="ws-diag",
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        is_ready_for_quote=True,
        adapter_status="ready",
        adapter_blockers=[],
        adapter_warnings=[],
        quote_input_payload={"letter_count": 3},
    )
    findings = IntakeV6CanonicalReadinessFindings(
        fatal_blockers=[],
        review_warnings=[],
        diagnostic_warnings=[
            "canonical_unresolved_warning:DOSSIER_METADATA_ONLY: Blueprint...",
        ],
    )
    enriched = enrich_pricing_preview_with_canonical_findings(preview, findings)
    assert enriched.adapter_status == "ready"
    assert enriched.adapter_warnings == []
    assert enriched.is_ready_for_quote is True
    readiness = (enriched.quote_input_payload or {}).get("canonical_readiness") or {}
    assert readiness["diagnostic_warnings"]
    assert readiness["review_warnings"] == []


def test_merge_defensive_repartitions_misplaced_info_on_findings_review() -> None:
    policy = SimpleNamespace(fatal_blockers=[], review_warnings=[])
    findings = IntakeV6CanonicalReadinessFindings(
        fatal_blockers=[],
        review_warnings=[
            "canonical_unresolved_warning:DOSSIER_METADATA_ONLY: misplaced on review",
        ],
        diagnostic_warnings=[],
    )
    merged = merge_policy_findings(policy=policy, findings=findings)
    assert merged["review_warnings"] == []
    assert any("DOSSIER_METADATA_ONLY" in w for w in merged["diagnostic_warnings"])
    assert merged["accept_allowed"] is True


def test_enrich_pricing_preview_keeps_diagnostics_out_of_adapter_warnings() -> None:
    from schemas.intake_v4 import IntakeV4PricingInputPreviewResponse
    from services.intake_v6_canonical_readiness_service import (
        enrich_pricing_preview_with_canonical_findings,
    )

    preview = IntakeV4PricingInputPreviewResponse(
        workspace_id="ws-diag",
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        is_ready_for_quote=True,
        adapter_status="ready",
        adapter_blockers=[],
        adapter_warnings=[],
        quote_input_payload={"letter_count": 3},
    )
    findings = IntakeV6CanonicalReadinessFindings(
        fatal_blockers=[],
        review_warnings=[],
        diagnostic_warnings=[
            "canonical_unresolved_warning:DOSSIER_METADATA_ONLY: Blueprint...",
        ],
    )
    enriched = enrich_pricing_preview_with_canonical_findings(preview, findings)
    assert enriched.adapter_status == "ready"
    assert enriched.adapter_warnings == []
    assert enriched.is_ready_for_quote is True
    readiness = (enriched.quote_input_payload or {}).get("canonical_readiness") or {}
    assert readiness["diagnostic_warnings"]
    assert readiness["review_warnings"] == []


def test_merge_defensive_repartitions_misplaced_info_on_findings_review() -> None:
    policy = SimpleNamespace(fatal_blockers=[], review_warnings=[])
    findings = IntakeV6CanonicalReadinessFindings(
        fatal_blockers=[],
        review_warnings=[
            "canonical_unresolved_warning:DOSSIER_METADATA_ONLY: misplaced on review",
        ],
        diagnostic_warnings=[],
    )
    merged = merge_policy_findings(policy=policy, findings=findings)
    assert merged["review_warnings"] == []
    assert any("DOSSIER_METADATA_ONLY" in w for w in merged["diagnostic_warnings"])
    assert merged["accept_allowed"] is True
