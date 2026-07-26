"""Consume-only adapter for external artwork analysis payloads.

Validates structure and builds a review surface. Never writes Product Truth,
Quantity, PD, Aggregate, Snapshot, or Order.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from pydantic import ValidationError

from schemas.artwork_analysis_contract_v1 import (
    ARTWORK_ANALYSIS_CONTRACT_VERSION,
    ArtworkAnalysisAdapterResultV1,
    ArtworkAnalysisContractV1,
    ArtworkAnalysisReviewSurfaceV1,
)

# Workspace / intake bag key for the external contract (transport TBD).
EXTERNAL_ARTWORK_ANALYSIS_BAG_KEY = "artwork_analysis_external_v1"


def _build_review_surface(
    contract: ArtworkAnalysisContractV1,
) -> ArtworkAnalysisReviewSurfaceV1:
    unconfirmed = sum(
        1 for obs in contract.observations if obs.status != "confirmed"
    )
    all_proposed = all(b.status == "proposed" for b in contract.suggested_bindings)
    notes = [
        "External analysis is observed/proposed only.",
        "Operator confirmation is required before Product Truth write.",
        "Transport for desktop → WorkOS delivery is TBD.",
    ]
    if unconfirmed:
        notes.append(f"{unconfirmed} observation(s) remain unconfirmed.")
    return ArtworkAnalysisReviewSurfaceV1(
        analysis_id=contract.provenance.analysis_id,
        contract_version=contract.artwork_analysis_contract_version,
        source_file_name=contract.provenance.source_file_name,
        source_file_hash=contract.provenance.source_file_hash,
        entity_count=len(contract.entities),
        group_count=len(contract.groups),
        measurement_count=len(contract.measurements),
        observation_count=len(contract.observations),
        suggested_binding_count=len(contract.suggested_bindings),
        unconfirmed_observation_count=unconfirmed,
        all_bindings_proposed=all_proposed,
        product_truth_writable_from_adapter=False,
        transport="tbd",
        notes=notes,
    )


def validate_artwork_analysis_payload(
    payload: Mapping[str, Any] | None,
) -> ArtworkAnalysisAdapterResultV1:
    """Structural validation of an external payload. No side effects."""
    if payload is None:
        return ArtworkAnalysisAdapterResultV1(
            ok=False,
            write_performed=False,
            product_truth_written=False,
            errors=["payload_missing"],
        )
    if not isinstance(payload, Mapping):
        return ArtworkAnalysisAdapterResultV1(
            ok=False,
            write_performed=False,
            product_truth_written=False,
            errors=["payload_not_object"],
        )
    try:
        contract = ArtworkAnalysisContractV1.model_validate(dict(payload))
    except ValidationError as exc:
        return ArtworkAnalysisAdapterResultV1(
            ok=False,
            write_performed=False,
            product_truth_written=False,
            errors=[f"validation_error:{err['loc']}:{err['msg']}" for err in exc.errors()],
        )
    except Exception as exc:  # pragma: no cover — defensive
        return ArtworkAnalysisAdapterResultV1(
            ok=False,
            write_performed=False,
            product_truth_written=False,
            errors=[f"validation_error:{type(exc).__name__}:{exc}"],
        )

    warnings: list[str] = []
    if not contract.suggested_bindings:
        warnings.append("no_suggested_bindings")
    if not contract.entities and not contract.groups:
        warnings.append("no_entities_or_groups")

    return ArtworkAnalysisAdapterResultV1(
        ok=True,
        write_performed=False,
        product_truth_written=False,
        contract=contract,
        review_surface=_build_review_surface(contract),
        warnings=warnings,
    )


def consume_external_artwork_analysis(
    payload: Mapping[str, Any] | None,
    *,
    product_truth_store: Optional[dict[str, Any]] = None,
) -> ArtworkAnalysisAdapterResultV1:
    """Consume external analysis for review.

    Explicitly refuses Product Truth writes even if a store dict is passed.
    """
    result = validate_artwork_analysis_payload(payload)
    if product_truth_store is not None:
        # Guard: adapter must never mutate Product Truth bags.
        before_keys = set(product_truth_store.keys())
        # No writes — only verify the caller's dict was not mutated.
        after_keys = set(product_truth_store.keys())
        if before_keys != after_keys or result.product_truth_written:
            result.ok = False
            result.errors = list(result.errors) + ["adapter_attempted_product_truth_write"]
            result.product_truth_written = False
            result.write_performed = False
    result.write_performed = False
    result.product_truth_written = False
    return result


def extract_external_artwork_analysis_from_workspace(
    workspace_payload: Mapping[str, Any] | None,
) -> Optional[dict[str, Any]]:
    """Locate external analysis bag if present; does not invent or parse files."""
    if not isinstance(workspace_payload, Mapping):
        return None
    bag = workspace_payload.get(EXTERNAL_ARTWORK_ANALYSIS_BAG_KEY)
    if isinstance(bag, Mapping):
        return dict(bag)
    nested = workspace_payload.get("product_truth")
    if isinstance(nested, Mapping):
        ref = nested.get("artwork_analysis_ref")
        if isinstance(ref, Mapping) and isinstance(ref.get("payload"), Mapping):
            return dict(ref["payload"])
    return None


def analysis_reference_for_product_truth(
    contract: ArtworkAnalysisContractV1,
) -> dict[str, Any]:
    """Lean reference suitable for confirmed Product Truth provenance — not authority."""
    return {
        "artwork_analysis_contract_version": ARTWORK_ANALYSIS_CONTRACT_VERSION,
        "analysis_id": contract.provenance.analysis_id,
        "analysis_version": contract.provenance.analysis_version,
        "source_file_hash": contract.provenance.source_file_hash,
        "source_file_name": contract.provenance.source_file_name,
        "source_file_kind": contract.provenance.source_file_kind,
        "source_entity_ids": list(contract.provenance.source_entity_ids),
        "authority": "operator_confirmed_product_truth_only",
        "raw_payload_is_authority": False,
    }
