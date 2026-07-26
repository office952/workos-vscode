"""Read-only Mini-module Contract Registry service — no DB writes."""

from __future__ import annotations

from data.mini_module_registry_volumetric_v2 import (
    REGISTRY_BY_CODE,
    TEMPLATE_MODULE_INDEX,
    VOLUMETRIC_V2_MODULES,
)
from schemas.mini_module_registry import (
    REGISTRY_VERSION,
    MiniModuleContract,
    MiniModuleRegistryRef,
    MiniModuleRegistryResponse,
    MiniModuleRegistrySummary,
)


from services.template_architecture_scope import normalize_template_code


class MiniModuleRegistryService:
    """Deterministic in-code registry — testable without seed or DB."""

    def list_all(self) -> MiniModuleRegistryResponse:
        return self._build_response(VOLUMETRIC_V2_MODULES)

    def get_by_code(self, module_code: str) -> MiniModuleContract | None:
        return REGISTRY_BY_CODE.get(module_code)

    def get_by_template(self, template_code: str) -> MiniModuleRegistryResponse:
        codes = TEMPLATE_MODULE_INDEX.get(template_code, [])
        resolved_code = template_code
        if not codes:
            normalized = normalize_template_code(template_code)
            for key, module_codes in TEMPLATE_MODULE_INDEX.items():
                if normalize_template_code(key) == normalized:
                    codes = module_codes
                    resolved_code = key
                    break
        modules = [REGISTRY_BY_CODE[c] for c in codes if c in REGISTRY_BY_CODE]
        return self._build_response(modules, template_code=resolved_code)

    def get_refs_for_template(self, template_code: str) -> list[MiniModuleRegistryRef]:
        response = self.get_by_template(template_code)
        return [
            MiniModuleRegistryRef(
                module_code=m.module_code,
                operational_status=m.operational_status,
                child_template_code=m.child_template_code,
                dossier_component_id=m.dossier_component_id,
            )
            for m in response.modules
            if m.operational_status == "ACTIVE_OPERATIONAL"
        ]

    def validate_operational_destinations(self) -> list[str]:
        """Return validation errors for active modules missing destinations."""
        errors: list[str] = []
        for module in VOLUMETRIC_V2_MODULES:
            if module.operational_status == "DEAD_PIECE_REMOVE_OR_APPROVE":
                errors.append(f"{module.module_code}: marked DEAD_PIECE without approval")
                continue
            if not module.operational_status.startswith("FUTURE_RESERVED"):
                dest = module.operational_destination
                has_any = any(
                    [
                        dest.intake_source,
                        dest.product_definition_keys,
                        dest.product_aggregate_display,
                        dest.cost_engine_use,
                        dest.quote_snapshot_use,
                        dest.order_snapshot_use,
                        dest.task_preview_use,
                    ]
                )
                if not has_any:
                    errors.append(f"{module.module_code}: ACTIVE module missing operational_destination")
            if module.operational_status == "ACTIVE_OPERATIONAL":
                if not module.produced_component_roles and module.module_type != "parent_template":
                    if not module.dossier_component_id and not module.child_template_code:
                        errors.append(f"{module.module_code}: ACTIVE without component role or template ref")
        return errors

    def _build_response(
        self,
        modules: list[MiniModuleContract],
        *,
        template_code: str | None = None,
    ) -> MiniModuleRegistryResponse:
        active = sum(1 for m in modules if m.operational_status == "ACTIVE_OPERATIONAL")
        future = sum(1 for m in modules if m.operational_status.startswith("FUTURE_RESERVED"))
        warnings: list[str] = []
        if template_code and template_code not in TEMPLATE_MODULE_INDEX:
            warnings.append(f"No registry entries indexed for template_code={template_code}")
        return MiniModuleRegistryResponse(
            summary=MiniModuleRegistrySummary(
                registry_version=REGISTRY_VERSION,
                template_code=template_code,
                total_modules=len(modules),
                active_operational_count=active,
                future_reserved_count=future,
                warnings=warnings,
            ),
            modules=modules,
        )


_registry_service: MiniModuleRegistryService | None = None


def get_mini_module_registry_service() -> MiniModuleRegistryService:
    global _registry_service
    if _registry_service is None:
        _registry_service = MiniModuleRegistryService()
    return _registry_service
