"""Focused tests for artwork_analysis_contract_v1 + consume-only adapter."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from schemas.artwork_analysis_contract_v1 import (
    ARTWORK_ANALYSIS_CONTRACT_VERSION,
    ArtworkAnalysisContractV1,
    ArtworkAnalysisSuggestedBindingV1,
)
from services.artwork_analysis_intake_adapter import (
    consume_external_artwork_analysis,
    validate_artwork_analysis_payload,
)
from services.artwork_analysis_integration_readiness import (
    evaluate_artwork_analysis_integration_readiness,
)


def _valid_payload(**overrides):
    base = {
        "artwork_analysis_contract_version": ARTWORK_ANALYSIS_CONTRACT_VERSION,
        "provenance": {
            "analysis_id": "an-001",
            "analysis_version": "desktop-1.0.0",
            "source_file_name": "letters.svg",
            "source_file_hash": "sha256:abc",
            "source_file_kind": "svg",
            "source_entity_ids": ["e1"],
        },
        "entities": [{"entity_id": "e1", "kind": "letter", "status": "observed"}],
        "groups": [],
        "measurements": [],
        "observations": [
            {
                "observation_id": "o1",
                "message": "Two layers detected",
                "status": "observed",
            }
        ],
        "suggested_bindings": [
            {
                "binding_id": "b1",
                "target_role": "face",
                "entity_ids": ["e1"],
                "status": "proposed",
            }
        ],
    }
    base.update(overrides)
    return base


def test_reject_unknown_contract_version():
    with pytest.raises(ValidationError) as exc:
        ArtworkAnalysisContractV1.model_validate(
            _valid_payload(artwork_analysis_contract_version="artwork_analysis_contract_v99")
        )
    assert "unsupported artwork_analysis_contract_version" in str(exc.value)


def test_structural_validation_requires_provenance_source():
    payload = _valid_payload()
    payload["provenance"] = {
        "analysis_id": "an-001",
        "analysis_version": "desktop-1.0.0",
    }
    result = validate_artwork_analysis_payload(payload)
    assert result.ok is False
    assert result.write_performed is False
    assert any("source_file" in e for e in result.errors)


def test_suggested_binding_cannot_be_confirmed_inbound():
    with pytest.raises(ValidationError) as exc:
        ArtworkAnalysisSuggestedBindingV1.model_validate(
            {
                "binding_id": "b1",
                "status": "confirmed",
                "entity_ids": ["e1"],
            }
        )
    assert "proposed" in str(exc.value).lower() or "confirmed" in str(exc.value).lower()


def test_adapter_does_not_write_product_truth():
    store = {"product_truth": {"confirmed_snapshot_v1": {"x": 1}}}
    before = dict(store)
    result = consume_external_artwork_analysis(_valid_payload(), product_truth_store=store)
    assert result.ok is True
    assert result.write_performed is False
    assert result.product_truth_written is False
    assert store == before
    assert result.review_surface is not None
    assert result.review_surface.product_truth_writable_from_adapter is False


def test_integration_readiness_not_configured_without_payload():
    result = evaluate_artwork_analysis_integration_readiness(None, mode="static")
    assert result.status == "NOT_CONFIGURED"
    assert result.product_truth_written is False
    assert result.transport == "tbd"


def test_integration_readiness_valid_payload():
    workspace = {"artwork_analysis_external_v1": _valid_payload()}
    result = evaluate_artwork_analysis_integration_readiness(workspace, mode="runtime")
    assert result.status in ("PASS", "PASS_WITH_WARNINGS")
    assert result.product_truth_written is False
    ids = {f.check_id for f in result.findings}
    assert "external_artwork_analysis.structural_validation" in ids
    assert "external_artwork_analysis.no_direct_product_truth_write" in ids
    assert "external_artwork_analysis.geometry_correctness_not_claimed" in ids


def test_integration_readiness_rejects_bad_version_in_bag():
    workspace = {
        "artwork_analysis_external_v1": _valid_payload(
            artwork_analysis_contract_version="nope"
        )
    }
    result = evaluate_artwork_analysis_integration_readiness(workspace, mode="runtime")
    assert result.status == "FAIL"
    assert any(
        f.check_id == "external_artwork_analysis.structural_validation" and f.status == "FAIL"
        for f in result.findings
    )
