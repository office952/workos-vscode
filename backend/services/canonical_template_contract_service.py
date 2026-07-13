"""Canonical template contract authority — behavior-bearing truth without dossier."""

from __future__ import annotations

from typing import Any

from data.canonical_output_blocks_volumetric_v2 import CANONICAL_OUTPUT_BLOCKS_V2
from data.canonical_template_variants_volumetric_v2 import CANONICAL_TEMPLATE_VARIANTS_V2
from data.mini_module_registry_volumetric_v2 import DOSSIER_COMPONENT_TO_MODULE, PILOT_TEMPLATE
from services.intake_v6_modular_form_contract_service import (
    IntakeV6ModularFormContractService,
    VOLUMETRIC_FIELD_BINDINGS,
)
from services.template_architecture_scope import normalize_template_code

_COMPONENT_MODULE_MAP = DOSSIER_COMPONENT_TO_MODULE


class CanonicalTemplateContractService:
    """Read-only canonical contracts for active template compilation."""

    def __init__(self) -> None:
        self._form = IntakeV6ModularFormContractService()

    def has_canonical_contract(self, template_code: str) -> bool:
        return normalize_template_code(template_code) == normalize_template_code(PILOT_TEMPLATE)

    def get_variants(self, template_code: str) -> list[dict[str, Any]]:
        if not self.has_canonical_contract(template_code):
            return []
        return [dict(v) for v in CANONICAL_TEMPLATE_VARIANTS_V2]

    def get_output_blocks_payload(self, template_code: str) -> dict[str, Any] | None:
        if not self.has_canonical_contract(template_code):
            return None
        return dict(CANONICAL_OUTPUT_BLOCKS_V2)

    def build_components_from_template_rows(
        self,
        parent_components: Any,
        *,
        source_template_code: str,
    ) -> list[dict[str, Any]]:
        if not isinstance(parent_components, list):
            return []
        out: list[dict[str, Any]] = []
        for entry in parent_components:
            if not isinstance(entry, dict):
                continue
            comp_id = str(entry.get("component_id") or entry.get("id") or "")
            if not comp_id:
                continue
            out.append(
                {
                    "component_id": comp_id,
                    "label_ro": entry.get("name") or entry.get("label"),
                    "role": entry.get("type") or entry.get("role"),
                    "mini_module_code": _COMPONENT_MODULE_MAP.get(comp_id),
                    "provenance": "parent",
                    "source_template_code": source_template_code,
                    "status": "present",
                }
            )
        return out

    def get_form_contract_keys(self, template_code: str) -> tuple[list[str], list[str]]:
        if not self.has_canonical_contract(template_code):
            return [], []
        required = sorted(
            {
                b.canonical_key
                for b in VOLUMETRIC_FIELD_BINDINGS
                if b.required and b.field_role != "derived_quote_input"
            }
        )
        optional = sorted(
            {
                b.canonical_key
                for b in VOLUMETRIC_FIELD_BINDINGS
                if not b.required and b.field_role != "derived_quote_input"
            }
        )
        return required, optional

    def dossier_metadata_fields(self) -> tuple[str, ...]:
        """Fields dossier may supply for inspection only — never runtime behavior."""
        return (
            "status",
            "dossier_version",
            "template_code",
            "completion_state_json",
            "production_notes_json",
            "qc_checkpoints_json",
            "risks_json",
            "layers_json",
            "time_assumptions_json",
            "quote_readiness_json",
            "visual_prompt_blocks_json",
        )


_canonical_service: CanonicalTemplateContractService | None = None


def get_canonical_template_contract_service() -> CanonicalTemplateContractService:
    global _canonical_service
    if _canonical_service is None:
        _canonical_service = CanonicalTemplateContractService()
    return _canonical_service
