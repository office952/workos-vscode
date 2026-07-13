"""Shared dossier consumption policy for behavior-bearing dossier JSON fields."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from models.product_blueprint_dossier import ProductBlueprintDossier
from services.template_architecture_scope import normalize_template_code

DOSSIER_APPROVED_STATUS = "approved"

DossierConsumerSurface = Literal["aggregate", "intake_contract", "output_blocks"]

DOSSIER_BEHAVIOR_FIELDS_AGGREGATE = (
    "sections_json",
    "costengine_mapping_json",
    "task_rules_json",
)

DOSSIER_BEHAVIOR_FIELDS_INTAKE_CONTRACT = ("variants_json",)

DOSSIER_BEHAVIOR_FIELDS_OUTPUT_BLOCKS = ("output_blocks_json",)


@dataclass(frozen=True)
class DossierConsumptionDecision:
    """Deterministic allow/deny decision for behavior-bearing dossier consumption."""

    consume: bool
    reason: str
    consumer_surface: DossierConsumerSurface
    dossier_id: int | None
    dossier_status: str | None
    dossier_template_code: str | None
    canonical_template_code: str
    behavior_bearing_fields: tuple[str, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_trace_dict(self) -> dict[str, Any]:
        return {
            "consume": self.consume,
            "reason": self.reason,
            "consumer_surface": self.consumer_surface,
            "dossier_id": self.dossier_id,
            "dossier_status": self.dossier_status,
            "dossier_template_code": self.dossier_template_code,
            "canonical_template_code": self.canonical_template_code,
            "behavior_bearing_fields": list(self.behavior_bearing_fields),
            **self.provenance,
        }


def evaluate_dossier_consumption(
    dossier: ProductBlueprintDossier | None,
    *,
    canonical_template_code: str,
    consumer_surface: DossierConsumerSurface,
    behavior_bearing_fields: tuple[str, ...],
) -> DossierConsumptionDecision:
    """Return whether behavior-bearing dossier JSON may be consumed on this surface."""
    canonical = normalize_template_code(canonical_template_code)
    base_provenance = {
        "policy": "dossier_consumption_policy.v1",
        "required_status": DOSSIER_APPROVED_STATUS,
    }

    if dossier is None:
        return DossierConsumptionDecision(
            consume=False,
            reason="dossier_missing",
            consumer_surface=consumer_surface,
            dossier_id=None,
            dossier_status=None,
            dossier_template_code=None,
            canonical_template_code=canonical,
            behavior_bearing_fields=behavior_bearing_fields,
            provenance=base_provenance,
        )

    if dossier.status != DOSSIER_APPROVED_STATUS:
        return DossierConsumptionDecision(
            consume=False,
            reason="dossier_not_approved",
            consumer_surface=consumer_surface,
            dossier_id=dossier.id,
            dossier_status=dossier.status,
            dossier_template_code=dossier.template_code,
            canonical_template_code=canonical,
            behavior_bearing_fields=behavior_bearing_fields,
            provenance={**base_provenance, "actual_status": dossier.status},
        )

    if normalize_template_code(dossier.template_code) != canonical:
        return DossierConsumptionDecision(
            consume=False,
            reason="template_identity_mismatch",
            consumer_surface=consumer_surface,
            dossier_id=dossier.id,
            dossier_status=dossier.status,
            dossier_template_code=dossier.template_code,
            canonical_template_code=canonical,
            behavior_bearing_fields=behavior_bearing_fields,
            provenance={
                **base_provenance,
                "normalized_dossier_template_code": normalize_template_code(dossier.template_code),
            },
        )

    return DossierConsumptionDecision(
        consume=True,
        reason="approved_dossier_consumed",
        consumer_surface=consumer_surface,
        dossier_id=dossier.id,
        dossier_status=dossier.status,
        dossier_template_code=dossier.template_code,
        canonical_template_code=canonical,
        behavior_bearing_fields=behavior_bearing_fields,
        provenance=base_provenance,
    )
