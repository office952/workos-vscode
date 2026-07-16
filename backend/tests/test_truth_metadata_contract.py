"""Tests for WorkOS Truth Metadata Contract (W0-B1).

Fixtures are TEST_FIXTURE / NOT_CANONICAL_TRUTH — not production claims.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from schemas.truth_metadata import (
    TRUTH_METADATA_VERSION,
    AuthorityReference,
    AuthorityType,
    ClaimStatus,
    ClaimType,
    DocumentReference,
    DriftRecord,
    DriftStatus,
    EdgeRelationshipType,
    EvidenceReference,
    EvidenceType,
    FigmaApprovalStatus,
    FigmaReference,
    OwnerType,
    PageNode,
    PageRole,
    SubjectType,
    SystemNode,
    TruthClaim,
    TypedEdge,
    VisibilityClass,
    normalize_repo_path,
)
from schemas.truth_metadata.enums import FigmaDriftType, FigmaFlowStatus
from schemas.truth_metadata.references import DisplayMetadata

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "truth_metadata"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _now() -> datetime:
    return datetime(2026, 7, 16, 12, 0, 0, tzinfo=timezone.utc)


def test_fixtures_load_as_claims_and_document():
    c1 = TruthClaim.model_validate(_load("claim_product_system_owns_templates.json"))
    c2 = TruthClaim.model_validate(_load("claim_modules_runtime_health.json"))
    c3 = TruthClaim.model_validate(_load("claim_figma_harta_approved_with_notes.json"))
    d1 = DocumentReference.model_validate(_load("document_superseded_example.json"))
    assert c1.is_test_fixture and c1.canonicality == "NOT_CANONICAL_TRUTH"
    assert c2.authority.authority_type == AuthorityType.RUNTIME_EVIDENCE
    assert c3.figma_refs[0].figma_approval_status == FigmaApprovalStatus.APPROVED_WITH_NOTES
    assert d1.superseded_by == "fixture.doc.wave0_plan_consolidated"
    assert d1.authority.value == "SUPERSEDED"


def test_metadata_version_rejected():
    payload = _load("claim_modules_runtime_health.json")
    payload["metadata_version"] = "workos_truth_metadata/v0"
    with pytest.raises(ValidationError, match="unsupported metadata_version"):
        TruthClaim.model_validate(payload)


def test_serialization_roundtrip_stable_version():
    claim = TruthClaim.model_validate(_load("claim_product_system_owns_templates.json"))
    data = claim.model_dump(mode="json")
    assert data["metadata_version"] == TRUTH_METADATA_VERSION
    again = TruthClaim.model_validate(data)
    assert again.claim_id == claim.claim_id
    assert again.display_label_ro == claim.display_label_ro


def test_path_safety():
    assert normalize_repo_path("docs/a/b.md") == "docs/a/b.md"
    with pytest.raises(ValueError, match="traversal"):
        normalize_repo_path("docs/../secret")
    with pytest.raises(ValueError, match="absolute"):
        normalize_repo_path("/etc/passwd")


def test_runtime_cannot_use_canonical_rank():
    with pytest.raises(ValidationError, match="RUNTIME_EVIDENCE"):
        TruthClaim(
            claim_id="bad.runtime.rank",
            subject_type=SubjectType.RUNTIME_CHECK,
            subject_id="x",
            claim_type=ClaimType.RUNTIME_BEHAVIOR,
            claim_text="bad",
            display_label_ro="Rău",
            authority=AuthorityReference(
                authority_type=AuthorityType.RUNTIME_EVIDENCE,
                authority_reference="GET /health",
                authority_rank=100,
            ),
            owner_type=OwnerType.UNASSIGNED,
            status=ClaimStatus.CURRENT_WITH_GUARDS,
            last_validated_at=_now(),
            evidence_refs=[
                EvidenceReference(
                    evidence_id="e1",
                    evidence_type=EvidenceType.RUNTIME,
                    reference="GET /health",
                )
            ],
            visibility_class=VisibilityClass.INTERNAL_TECHNICAL,
        )


def test_current_requires_evidence_and_validation_date():
    base = dict(
        claim_id="bad.current",
        subject_type=SubjectType.SYSTEM,
        subject_id="s",
        claim_type=ClaimType.OWNS,
        claim_text="x",
        display_label_ro="X",
        authority=AuthorityReference(
            authority_type=AuthorityType.SUPPORTING_DOCUMENT,
            authority_reference="docs/plans/2026-07-16-workos-wave-0-foundation-truth-pages-plan.md",
            authority_rank=10,
        ),
        owner_type=OwnerType.UNASSIGNED,
        status=ClaimStatus.CURRENT,
        visibility_class=VisibilityClass.INTERNAL_TECHNICAL,
    )
    with pytest.raises(ValidationError, match="last_validated_at"):
        TruthClaim(**base, evidence_refs=[
            EvidenceReference(evidence_id="e", evidence_type=EvidenceType.DOCUMENT, reference="docs/a.md")
        ])
    with pytest.raises(ValidationError, match="evidence_refs"):
        TruthClaim(**base, last_validated_at=_now(), evidence_refs=[])


def test_canonical_current_requires_owner():
    with pytest.raises(ValidationError, match="owner"):
        TruthClaim(
            claim_id="bad.canonical.owner",
            subject_type=SubjectType.SYSTEM,
            subject_id="s",
            claim_type=ClaimType.OWNS,
            claim_text="x",
            display_label_ro="X",
            authority=AuthorityReference(
                authority_type=AuthorityType.CANONICAL_ARCHITECTURE,
                authority_reference="docs/architecture/WORKOS_TRUTH_METADATA_CONTRACT.md",
                authority_rank=200,
            ),
            owner_type=OwnerType.UNASSIGNED,
            status=ClaimStatus.CURRENT,
            last_validated_at=_now(),
            evidence_refs=[
                EvidenceReference(
                    evidence_id="e",
                    evidence_type=EvidenceType.DOCUMENT,
                    reference="docs/architecture/WORKOS_TRUTH_METADATA_CONTRACT.md",
                )
            ],
            visibility_class=VisibilityClass.ADMIN_ONLY,
        )


def test_figma_unapproved_cannot_back_figma_approved_authority():
    with pytest.raises(ValidationError, match="APPROVED"):
        TruthClaim(
            claim_id="bad.figma",
            subject_type=SubjectType.FIGMA_NODE,
            subject_id="n",
            claim_type=ClaimType.FIGMA_MAPPING,
            claim_text="x",
            display_label_ro="X",
            authority=AuthorityReference(
                authority_type=AuthorityType.FIGMA_APPROVED,
                authority_reference="docs/qa/workos-e2e-figma-master-maps-v1/FIGMA_MASTER_FINAL_REVIEW.md",
                authority_rank=80,
            ),
            owner_type=OwnerType.DOC_OWNER,
            owner_reference="o",
            status=ClaimStatus.PARTIAL,
            evidence_refs=[
                EvidenceReference(evidence_id="e", evidence_type=EvidenceType.FIGMA, reference="docs/a.md")
            ],
            figma_refs=[
                FigmaReference(
                    figma_file_key="abc",
                    figma_node_id="1:1",
                    figma_approval_status=FigmaApprovalStatus.PROPOSED,
                    figma_flow_status=FigmaFlowStatus.PROPOSED,
                )
            ],
            visibility_class=VisibilityClass.ADMIN_ONLY,
        )


def test_self_supersession_rejected():
    with pytest.raises(ValidationError, match="supersede"):
        TruthClaim(
            claim_id="c1",
            subject_type=SubjectType.RULE,
            subject_id="r",
            claim_type=ClaimType.FORBIDDEN,
            claim_text="x",
            display_label_ro="X",
            authority=AuthorityReference(
                authority_type=AuthorityType.REFERENCE_ONLY,
                authority_reference="docs/a.md",
                authority_rank=1,
            ),
            owner_type=OwnerType.UNASSIGNED,
            status=ClaimStatus.PROPOSED,
            supersedes=["c1"],
            visibility_class=VisibilityClass.HIDDEN_FROM_UI,
        )


def test_drift_requires_reason():
    with pytest.raises(ValidationError, match="drift_reason"):
        TruthClaim(
            claim_id="c-drift",
            subject_type=SubjectType.PAGE,
            subject_id="p",
            claim_type=ClaimType.STATUS,
            claim_text="x",
            display_label_ro="X",
            authority=AuthorityReference(
                authority_type=AuthorityType.REFERENCE_ONLY,
                authority_reference="docs/a.md",
                authority_rank=1,
            ),
            owner_type=OwnerType.UNASSIGNED,
            status=ClaimStatus.STALE,
            drift_status=DriftStatus.CODE_DRIFT,
            visibility_class=VisibilityClass.INTERNAL_TECHNICAL,
        )


def test_valid_until_before_from_rejected():
    with pytest.raises(ValidationError, match="valid_until"):
        TruthClaim(
            claim_id="c-dates",
            subject_type=SubjectType.RULE,
            subject_id="r",
            claim_type=ClaimType.FORBIDDEN,
            claim_text="x",
            display_label_ro="X",
            authority=AuthorityReference(
                authority_type=AuthorityType.REFERENCE_ONLY,
                authority_reference="docs/a.md",
                authority_rank=1,
            ),
            owner_type=OwnerType.UNASSIGNED,
            status=ClaimStatus.PROPOSED,
            valid_from=_now(),
            valid_until=datetime(2020, 1, 1, tzinfo=timezone.utc),
            visibility_class=VisibilityClass.INTERNAL_TECHNICAL,
        )


def test_translation_key_and_display():
    claim = TruthClaim.model_validate(_load("claim_product_system_owns_templates.json"))
    dm = claim.to_display_metadata()
    assert dm.display_label_ro
    assert dm.translation_key.startswith("truth.")
    with pytest.raises(ValidationError):
        DisplayMetadata(display_label_ro="X", translation_key="Invalid-Key")


def test_system_page_edge_models():
    system = SystemNode(
        system_id="product_system",
        display=DisplayMetadata(
            display_label_ro="Sistem produs",
            technical_alias="Product System",
            translation_key="system.product_system.title",
        ),
        status="OPERATIONAL_PARTIAL",
        runtime_status=None,
        runtime_status_source=None,
        visibility_class=VisibilityClass.ADMIN_ONLY,
        is_test_fixture=True,
    )
    page = PageNode(
        page_id="modules",
        route="/modules",
        system_id="module_chain",
        role=PageRole.REFERENCE,
        display=DisplayMetadata(
            display_label_ro="Harta sistemelor",
            technical_alias="Module Chain",
            translation_key="system_map.title",
        ),
        status="REFERENCE_ONLY",
        visibility_class=VisibilityClass.ADMIN_ONLY,
        is_test_fixture=True,
    )
    edge = TypedEdge(
        edge_id="e.ps.intake",
        source_id="product_system",
        target_id="intake_v6",
        relationship_type=EdgeRelationshipType.DIRECT,
        is_test_fixture=True,
    )
    assert system.system_id == "product_system"
    assert page.route == "/modules"
    assert edge.relationship_type == EdgeRelationshipType.DIRECT


def test_drift_record_rejects_aligned():
    with pytest.raises(ValidationError, match="ALIGNED"):
        DriftRecord(
            drift_id="d1",
            subject_type="PAGE",
            subject_id="modules",
            drift_status=DriftStatus.ALIGNED,
            drift_reason="n/a",
        )


def test_figma_drift_description_required():
    with pytest.raises(ValidationError, match="drift_description"):
        FigmaReference(
            figma_file_key="k",
            figma_node_id="1:1",
            drift_type=FigmaDriftType.RUNTIME,
        )


def test_evidence_path_traversal_rejected():
    with pytest.raises(ValidationError, match="traversal"):
        EvidenceReference(
            evidence_id="e",
            evidence_type=EvidenceType.DOCUMENT,
            reference="docs/../../etc/passwd",
        )
