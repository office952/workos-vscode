"""Integration readiness for external artwork analysis — non-geometric checks only.

Checks: supported contract version, structural validity, provenance/source hash,
observations unconfirmed until operator, no direct Product Truth write from adapter.
Does NOT judge geometric correctness of the desktop parse.
"""

from __future__ import annotations

from typing import Any, Literal, Mapping, Optional

from pydantic import BaseModel, Field

from schemas.artwork_analysis_contract_v1 import (
    ARTWORK_ANALYSIS_CONTRACT_VERSION,
    SUPPORTED_ARTWORK_ANALYSIS_CONTRACT_VERSIONS,
)
from services.artwork_analysis_intake_adapter import (
    consume_external_artwork_analysis,
    extract_external_artwork_analysis_from_workspace,
)

IntegrationCheckStatus = Literal[
    "PASS",
    "PASS_WITH_WARNINGS",
    "FAIL",
    "NOT_CONFIGURED",
    "NOT_TESTED",
]


class ArtworkAnalysisIntegrationFinding(BaseModel):
    check_id: str
    status: IntegrationCheckStatus
    blocking: bool = False
    message: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class ArtworkAnalysisIntegrationReadinessResult(BaseModel):
    status: IntegrationCheckStatus
    findings: list[ArtworkAnalysisIntegrationFinding] = Field(default_factory=list)
    supported_contract_versions: list[str] = Field(
        default_factory=lambda: sorted(SUPPORTED_ARTWORK_ANALYSIS_CONTRACT_VERSIONS)
    )
    transport: Literal["tbd"] = "tbd"
    product_truth_written: bool = False


def evaluate_artwork_analysis_integration_readiness(
    workspace_payload: Mapping[str, Any] | None = None,
    *,
    external_payload: Optional[Mapping[str, Any]] = None,
    mode: Literal["static", "runtime"] = "static",
) -> ArtworkAnalysisIntegrationReadinessResult:
    findings: list[ArtworkAnalysisIntegrationFinding] = []

    findings.append(
        ArtworkAnalysisIntegrationFinding(
            check_id="external_artwork_analysis.contract_supported",
            status="PASS",
            blocking=False,
            message=(
                f"WorkOS supports {ARTWORK_ANALYSIS_CONTRACT_VERSION}; "
                "unknown versions are rejected at consume time."
            ),
            evidence={
                "supported": sorted(SUPPORTED_ARTWORK_ANALYSIS_CONTRACT_VERSIONS),
            },
        )
    )
    findings.append(
        ArtworkAnalysisIntegrationFinding(
            check_id="external_artwork_analysis.transport",
            status="NOT_CONFIGURED",
            blocking=False,
            message="Desktop → WorkOS transport remains TBD (separate decision).",
            evidence={"transport": "tbd"},
        )
    )

    payload = external_payload
    if payload is None and workspace_payload is not None:
        payload = extract_external_artwork_analysis_from_workspace(workspace_payload)

    if payload is None:
        findings.append(
            ArtworkAnalysisIntegrationFinding(
                check_id="external_artwork_analysis.payload_present",
                status="NOT_CONFIGURED" if mode == "static" else "NOT_TESTED",
                blocking=False,
                message=(
                    "No external artwork_analysis_external_v1 bag present; "
                    "legacy in-repo analysis paths may still exist (do not extend)."
                ),
                evidence={"bag_key": "artwork_analysis_external_v1"},
            )
        )
        return ArtworkAnalysisIntegrationReadinessResult(
            status="NOT_CONFIGURED",
            findings=findings,
            product_truth_written=False,
        )

    product_truth_probe: dict[str, Any] = {"sentinel": True}
    adapter_result = consume_external_artwork_analysis(
        payload, product_truth_store=product_truth_probe
    )

    if adapter_result.product_truth_written or adapter_result.write_performed:
        findings.append(
            ArtworkAnalysisIntegrationFinding(
                check_id="external_artwork_analysis.no_direct_product_truth_write",
                status="FAIL",
                blocking=True,
                message="Adapter must not write Product Truth.",
                evidence={},
            )
        )
    else:
        findings.append(
            ArtworkAnalysisIntegrationFinding(
                check_id="external_artwork_analysis.no_direct_product_truth_write",
                status="PASS",
                blocking=False,
                message="Adapter consume path did not write Product Truth.",
                evidence={"product_truth_probe_intact": product_truth_probe == {"sentinel": True}},
            )
        )

    if not adapter_result.ok:
        findings.append(
            ArtworkAnalysisIntegrationFinding(
                check_id="external_artwork_analysis.structural_validation",
                status="FAIL",
                blocking=True,
                message="External artwork analysis payload failed structural validation.",
                evidence={"errors": list(adapter_result.errors)},
            )
        )
        return ArtworkAnalysisIntegrationReadinessResult(
            status="FAIL",
            findings=findings,
            product_truth_written=False,
        )

    findings.append(
        ArtworkAnalysisIntegrationFinding(
            check_id="external_artwork_analysis.structural_validation",
            status="PASS",
            blocking=False,
            message="External artwork analysis payload is structurally valid.",
            evidence={
                "analysis_id": adapter_result.contract.provenance.analysis_id
                if adapter_result.contract
                else None,
            },
        )
    )

    contract = adapter_result.contract
    assert contract is not None
    hash_present = bool(str(contract.provenance.source_file_hash or "").strip())
    findings.append(
        ArtworkAnalysisIntegrationFinding(
            check_id="external_artwork_analysis.source_hash_or_name",
            status="PASS" if hash_present else "PASS_WITH_WARNINGS",
            blocking=False,
            message=(
                "Source file hash present."
                if hash_present
                else "Source file name present but hash missing (prefer hash for Snapshot freeze)."
            ),
            evidence={
                "source_file_hash": contract.provenance.source_file_hash,
                "source_file_name": contract.provenance.source_file_name,
            },
        )
    )

    unconfirmed = sum(1 for o in contract.observations if o.status != "confirmed")
    bindings_ok = all(b.status == "proposed" for b in contract.suggested_bindings)
    if not bindings_ok:
        findings.append(
            ArtworkAnalysisIntegrationFinding(
                check_id="external_artwork_analysis.bindings_proposed_only",
                status="FAIL",
                blocking=True,
                message="Inbound suggested bindings must not be confirmed.",
                evidence={},
            )
        )
    else:
        findings.append(
            ArtworkAnalysisIntegrationFinding(
                check_id="external_artwork_analysis.bindings_proposed_only",
                status="PASS",
                blocking=False,
                message="Suggested bindings remain proposed (operator confirms Product Truth).",
                evidence={"suggested_binding_count": len(contract.suggested_bindings)},
            )
        )

    findings.append(
        ArtworkAnalysisIntegrationFinding(
            check_id="external_artwork_analysis.observations_await_operator",
            status="PASS_WITH_WARNINGS" if unconfirmed else "PASS",
            blocking=False,
            message=(
                f"{unconfirmed} observation(s) await operator confirmation before Product Truth."
                if unconfirmed
                else "No unconfirmed observations listed."
            ),
            evidence={"unconfirmed_observation_count": unconfirmed},
        )
    )

    findings.append(
        ArtworkAnalysisIntegrationFinding(
            check_id="external_artwork_analysis.geometry_correctness_not_claimed",
            status="PASS",
            blocking=False,
            message=(
                "Readiness does not claim geometric correctness of the desktop parse."
            ),
            evidence={"geometric_validation": "out_of_scope"},
        )
    )

    statuses = {f.status for f in findings}
    if "FAIL" in statuses:
        overall: IntegrationCheckStatus = "FAIL"
    elif "PASS_WITH_WARNINGS" in statuses or "NOT_CONFIGURED" in statuses:
        overall = "PASS_WITH_WARNINGS"
    else:
        overall = "PASS"

    return ArtworkAnalysisIntegrationReadinessResult(
        status=overall,
        findings=findings,
        product_truth_written=False,
    )
