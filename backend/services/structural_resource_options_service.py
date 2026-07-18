"""Read-only Shared Technical Resource Options service."""

from __future__ import annotations

from typing import Any

from data.product_system import structural_resource_options_v1 as catalog
from schemas.structural_resource_options import (
    ComponentAcceptedOptions,
    StructuralMaterialOption,
    StructuralProfileOption,
    StructuralResourceOptionsResponse,
)


class StructuralResourceOptionsService:
    def snapshot(self) -> StructuralResourceOptionsResponse:
        raw = catalog.registry_snapshot()
        return StructuralResourceOptionsResponse(
            registry_version=raw["registry_version"],
            materials=[StructuralMaterialOption.model_validate(m) for m in raw["materials"]],
            profiles=[StructuralProfileOption.model_validate(p) for p in raw["profiles"]],
            notes=list(raw.get("notes") or []),
        )

    def list_materials(self) -> list[StructuralMaterialOption]:
        return [StructuralMaterialOption.model_validate(m) for m in catalog.list_materials()]

    def list_profiles(self) -> list[StructuralProfileOption]:
        return [StructuralProfileOption.model_validate(p) for p in catalog.list_profiles()]

    def accepted_for_component(self, template_code: str) -> ComponentAcceptedOptions | None:
        raw = catalog.get_accepted_options(template_code)
        if not raw:
            return None
        return ComponentAcceptedOptions.model_validate(raw)

    def profiles_for_component(
        self, template_code: str, *, material_code: str | None = None
    ) -> list[StructuralProfileOption]:
        accepted = catalog.get_accepted_options(template_code) or {}
        allowed = set(accepted.get("accepted_profile_codes") or [])
        rows = []
        for profile in catalog.list_profiles():
            if profile["code"] not in allowed:
                continue
            if material_code and material_code not in (profile.get("compatible_material_codes") or []):
                continue
            rows.append(StructuralProfileOption.model_validate(profile))
        return rows

    def raw_snapshot(self) -> dict[str, Any]:
        return catalog.registry_snapshot()


_service: StructuralResourceOptionsService | None = None


def get_structural_resource_options_service() -> StructuralResourceOptionsService:
    global _service
    if _service is None:
        _service = StructuralResourceOptionsService()
    return _service
