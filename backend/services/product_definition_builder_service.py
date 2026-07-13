"""Read-only ProductDefinition preview builder (Step 6) — no pricing, no DB writes."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.mini_module_registry_volumetric_v2 import DOSSIER_COMPONENT_TO_MODULE
from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from schemas.intake_v6_modular_form import IntakeFormFieldBinding, IntakeModuleFormSection
from schemas.product_aggregate import ProductAggregate, ProductAggregateComponent
from schemas.product_definition import (
    ProductDefinitionComponentRole,
    ProductDefinitionMaterialRole,
    ProductDefinitionModuleRef,
    ProductDefinitionOperationRole,
    ProductDefinitionPreview,
    ProductDefinitionProvenanceEntry,
    ProductDefinitionResourceHints,
    ProductDefinitionSourceContext,
    ProductDefinitionValidation,
    ReadinessStatus,
)
from services.intake_v6_modular_form_contract_service import IntakeV6ModularFormContractService
from services.linked_template_runtime_segment_extraction_service import (
    extract_linked_template_segments_from_workspace_payload,
)
from services.mini_module_registry_service import MiniModuleRegistryService, get_mini_module_registry_service
from services.mounting_solution_service import (
    is_structura_suport_active,
    legacy_mounting_system_from_solution,
    resolve_effective_mounting_solution,
)
from services.product_aggregate_service import ProductAggregateService

BAR_MOUNTING = frozenset({"steel_bars", "aluminum_bars"})
SYNTHETIC_COMPONENT_IDS = frozenset({"comp_auto_1"})
GEOMETRY_GATE_OPERATIONS = frozenset({"svg_geometry_analysis"})


def _get_by_path(root: Any, path: str) -> Any:
    if not path:
        return None
    cur = root
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _read_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _read_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _parse_workspace_payload(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _is_illuminated(finish: dict[str, Any]) -> bool:
    illuminated = _read_bool(finish.get("illuminated"))
    if illuminated is False:
        return False
    lighting = _read_string(finish.get("lighting_system_type"))
    if lighting and lighting != "none":
        return True
    return illuminated is not False


def _has_geometry_basics(payload: dict[str, Any]) -> bool:
    svg = payload.get("svg_source") if isinstance(payload.get("svg_source"), dict) else {}
    geom = payload.get("quote_geometry") if isinstance(payload.get("quote_geometry"), dict) else {}
    if not _read_string(svg.get("file_name")):
        return False
    letter_count = geom.get("letter_count")
    if letter_count is None:
        return False
    try:
        return float(letter_count) >= 0
    except (TypeError, ValueError):
        return False


def _resolve_module_state(
    module: IntakeModuleFormSection,
    *,
    finish: dict[str, Any],
    quote_geometry: dict[str, Any],
    svg_source: dict[str, Any],
    analysis_ready: bool,
) -> str:
    mounting_system = _read_string(finish.get("mounting_system"))

    if module.operational_status.startswith("FUTURE"):
        return "future_reserved"

    code = module.module_code
    if code == "geometry_svg":
        return "always_on" if _has_geometry_basics({"svg_source": svg_source, "quote_geometry": quote_geometry}) else "pending"
    if code in ("debitare_fata", "debitare_spate", "modelare_cant"):
        return "always_on" if analysis_ready else "pending"
    if code == "structura_suport":
        if is_structura_suport_active(finish):
            return "active"
        mounting_system = _read_string(finish.get("mounting_system"))
        if not mounting_system:
            return "pending"
        return "active" if mounting_system in BAR_MOUNTING else "inactive"
    if code == "sistem_led":
        if not _is_illuminated(finish):
            return "inactive"
        lighting = _read_string(finish.get("lighting_system_type"))
        if not lighting or lighting == "none":
            return "pending"
        return "conditional_active"
    if code == "finisaje":
        if _read_bool(finish.get("mounting_template_enabled")) is True:
            return "conditional_active"
        return "always_on"

    kind = module.activation_kind
    if kind in ("always_on", "required_module"):
        return "always_on" if analysis_ready else "pending"
    if kind == "optional_addon":
        return "inactive"
    return "pending"


def _collect_missing_fields(
    module: IntakeModuleFormSection,
    state: str,
    *,
    finish: dict[str, Any],
    quote_geometry: dict[str, Any],
    client: dict[str, Any],
    svg_source: dict[str, Any],
) -> list[str]:
    if state in ("inactive", "future_reserved"):
        return []

    missing: list[str] = []
    for field_key in module.required_form_fields:
        if field_key == "vector_file":
            if not _read_string(svg_source.get("file_name")):
                missing.append(field_key)
            continue
        finish_val = finish.get(field_key)
        geom_val = quote_geometry.get(field_key)
        client_val = client.get(field_key)
        has_value = any(
            v is not None and v != ""
            for v in (finish_val, geom_val, client_val)
        )
        if not has_value:
            missing.append(field_key)
    return missing


def _derive_metal_support_required(mounting_system: str | None, finish: dict[str, Any] | None = None) -> bool | None:
    if isinstance(finish, dict) and is_structura_suport_active(finish):
        return True
    if not mounting_system:
        return None
    return mounting_system in BAR_MOUNTING


def _build_canonical_values(
    bindings: list[IntakeFormFieldBinding],
    payload: dict[str, Any],
) -> dict[str, Any]:
    values: dict[str, Any] = {}
    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}

    for binding in bindings:
        if binding.field_role == "derived_quote_input":
            if binding.canonical_key == "metal_support_required":
                derived = _derive_metal_support_required(_read_string(finish.get("mounting_system")), finish)
                if derived is None and isinstance(finish, dict):
                    solution = resolve_effective_mounting_solution(finish)
                    derived = legacy_mounting_system_from_solution(solution) is not None and is_structura_suport_active(finish)
                if derived is not None:
                    values[binding.canonical_key] = derived
            continue

        val = _get_by_path(payload, binding.workspace_path)
        if val is not None and val != "":
            values[binding.canonical_key] = val

    return values


def _build_geometry_inputs(canonical_values: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "vector_file",
        "width_mm",
        "height_mm",
        "letter_count",
        "letter_perimeter_m",
        "letter_face_area_m2",
        "depth_mm",
    )
    return {k: canonical_values[k] for k in keys if k in canonical_values}


def _module_is_active(state: str) -> bool:
    return state in ("always_on", "active", "conditional_active")


def _classify_modules(
    modules: list[IntakeModuleFormSection],
    *,
    finish: dict[str, Any],
    quote_geometry: dict[str, Any],
    svg_source: dict[str, Any],
    client: dict[str, Any],
    analysis_ready: bool,
) -> tuple[list[ProductDefinitionModuleRef], list[ProductDefinitionModuleRef], list[ProductDefinitionModuleRef]]:
    selected: list[ProductDefinitionModuleRef] = []
    optional: list[ProductDefinitionModuleRef] = []
    inactive: list[ProductDefinitionModuleRef] = []

    for module in modules:
        state = _resolve_module_state(
            module,
            finish=finish,
            quote_geometry=quote_geometry,
            svg_source=svg_source,
            analysis_ready=analysis_ready,
        )
        missing = _collect_missing_fields(
            module,
            state,
            finish=finish,
            quote_geometry=quote_geometry,
            client=client,
            svg_source=svg_source,
        )
        if missing and state in ("always_on", "active", "conditional_active"):
            state = "pending"

        ref = ProductDefinitionModuleRef(
            module_code=module.module_code,
            module_name=module.module_name,
            activation_kind=module.activation_kind,
            state=state,  # type: ignore[arg-type]
            activation_reason=module.warnings[0] if module.warnings else None,
            missing_fields=missing,
        )

        if state == "future_reserved":
            inactive.append(ref)
        elif module.activation_kind == "optional_addon":
            optional.append(ref)
            if _module_is_active(state):
                selected.append(ref)
            else:
                inactive.append(ref)
        elif _module_is_active(state):
            selected.append(ref)
        elif state == "pending":
            optional.append(ref)
        else:
            inactive.append(ref)

    return selected, optional, inactive


def _active_module_codes(
    selected: list[ProductDefinitionModuleRef],
) -> set[str]:
    return {m.module_code for m in selected}


def _component_module_active(component: ProductAggregateComponent, active_modules: set[str]) -> bool:
    if component.component_id in SYNTHETIC_COMPONENT_IDS:
        return False
    mod = component.mini_module_code or DOSSIER_COMPONENT_TO_MODULE.get(component.component_id)
    if mod:
        return mod in active_modules
    return True


def _build_components(
    aggregate: ProductAggregate,
    active_modules: set[str],
) -> list[ProductDefinitionComponentRole]:
    out: list[ProductDefinitionComponentRole] = []
    for comp in aggregate.components:
        if comp.component_id in SYNTHETIC_COMPONENT_IDS:
            continue
        module_active = _component_module_active(comp, active_modules)
        out.append(
            ProductDefinitionComponentRole(
                component_id=comp.component_id,
                label_ro=comp.label_ro,
                role=comp.role,
                mini_module_code=comp.mini_module_code or DOSSIER_COMPONENT_TO_MODULE.get(comp.component_id),
                module_active=module_active,
                provenance=comp.provenance,
                source_template_code=comp.source_template_code,
            )
        )
    return out


def _build_material_roles(aggregate: ProductAggregate, active_modules: set[str]) -> list[ProductDefinitionMaterialRole]:
    roles: list[ProductDefinitionMaterialRole] = []
    for mat in aggregate.materials:
        mod = mat.mini_module_code
        module_active = mod in active_modules if mod else True
        roles.append(
            ProductDefinitionMaterialRole(
                material_code=mat.material_code,
                label=mat.label,
                unit=mat.unit,
                component_ref=mat.component_ref,
                mini_module_code=mat.mini_module_code,
                module_active=module_active,
                provenance=mat.provenance,
            )
        )
    return roles


def _build_operation_roles(aggregate: ProductAggregate, active_modules: set[str]) -> list[ProductDefinitionOperationRole]:
    roles: list[ProductDefinitionOperationRole] = []
    for op in aggregate.operations:
        mod = op.mini_module_code
        module_active = mod in active_modules if mod else True
        is_gate = op.operation_code in GEOMETRY_GATE_OPERATIONS or mod == "geometry_svg"
        roles.append(
            ProductDefinitionOperationRole(
                operation_code=op.operation_code,
                label=op.label,
                workcenter=op.workcenter,
                component_ref=op.component_ref,
                mini_module_code=op.mini_module_code,
                module_active=module_active,
                is_geometry_gate=is_gate,
                is_priced=op.priced,
                provenance=op.provenance,
            )
        )
    return roles


def _build_resource_hints(registry: MiniModuleRegistryService, template_code: str) -> ProductDefinitionResourceHints:
    hints = ProductDefinitionResourceHints()
    response = registry.get_by_template(template_code)
    for module in response.modules:
        if module.operational_status != "ACTIVE_OPERATIONAL":
            continue
        for op in module.required_operation_roles:
            hints.required_machine_type.append(f"{module.module_code}:{op}")
        for mat in module.required_material_roles:
            hints.inventory_source.append(f"{module.module_code}:{mat}")
        hints.pricing_source.append(f"{module.module_code}:cost_engine_inputs")
        hints.execution_routing_notes.append(
            f"{module.module_code}:task_preview_outputs={','.join(module.task_preview_outputs) or 'none'}"
        )
    return hints


def _compute_readiness(
    *,
    missing_required: list[str],
    invalid_combinations: list[str],
    unresolved_warnings: list[str],
    has_payload: bool,
) -> ReadinessStatus:
    if not has_payload:
        return "partial"
    if invalid_combinations:
        return "blocked"
    if missing_required:
        return "partial"
    if unresolved_warnings:
        return "partial"
    return "ready"


class ProductDefinitionBuilderService:
    """Build read-only ProductDefinition preview from contracts + optional workspace payload."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        form_service: IntakeV6ModularFormContractService | None = None,
        registry: MiniModuleRegistryService | None = None,
    ) -> None:
        self._db = db
        self._form = form_service or IntakeV6ModularFormContractService()
        self._registry = registry or get_mini_module_registry_service()
        self._aggregate_svc = ProductAggregateService(db)

    async def build_preview(
        self,
        template_code: str,
        *,
        workspace_id: str | None = None,
    ) -> ProductDefinitionPreview | None:
        form_contract = self._form.get_for_template(template_code)
        if form_contract is None:
            return None

        aggregate = await self._aggregate_svc.build(template_code)
        if aggregate is None:
            return None

        payload: dict[str, Any] = {}
        source_type: str = "template_only"
        if workspace_id:
            ws_payload, ws_error = await self._load_workspace_payload(workspace_id, template_code)
            if ws_error == "workspace_not_found":
                return None
            if ws_error == "workspace_template_mismatch":
                payload = {}
            else:
                payload = ws_payload or {}
                source_type = "workspace_payload"

        finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
        quote_geometry = payload.get("quote_geometry") if isinstance(payload.get("quote_geometry"), dict) else {}
        svg_source = payload.get("svg_source") if isinstance(payload.get("svg_source"), dict) else {}
        client = payload.get("client") if isinstance(payload.get("client"), dict) else {}
        analysis_ready = bool(payload.get("analysis_ready")) or _has_geometry_basics(payload)

        selected, optional, inactive = _classify_modules(
            form_contract.modules,
            finish=finish,
            quote_geometry=quote_geometry,
            svg_source=svg_source,
            client=client,
            analysis_ready=analysis_ready,
        )

        registry_response = self._registry.get_by_template(template_code)
        classified_codes = {
            m.module_code
            for m in selected + optional + inactive
        }
        for reg_module in registry_response.modules:
            if reg_module.module_code in classified_codes:
                continue
            if reg_module.operational_status.startswith("FUTURE"):
                inactive.append(
                    ProductDefinitionModuleRef(
                        module_code=reg_module.module_code,
                        module_name=reg_module.module_name,
                        activation_kind="future_reserved",
                        state="future_reserved",
                        activation_reason=reg_module.warnings[0] if reg_module.warnings else reg_module.operational_status,
                        missing_fields=[],
                    )
                )
        active_modules = _active_module_codes(selected)

        canonical_values = _build_canonical_values(form_contract.field_bindings, payload)
        geometry_inputs = _build_geometry_inputs(canonical_values)

        linked_template_runtime_segments = None
        backbone = form_contract.form_system_backbone if isinstance(form_contract.form_system_backbone, dict) else {}
        linked_template_composition = backbone.get("linked_template_composition")
        if isinstance(linked_template_composition, dict):
            linked_template_runtime_segments = extract_linked_template_segments_from_workspace_payload(
                root_template_code=template_code,
                workspace_payload=payload,
                linked_template_composition=linked_template_composition,
            )

        inactive_module_codes = {
            m.module_code for m in inactive if m.state in ("inactive", "future_reserved")
        }

        missing_required: list[str] = []
        for binding in form_contract.field_bindings:
            if binding.field_role == "derived_quote_input":
                continue
            if binding.operational_status.startswith("FUTURE"):
                continue
            if not binding.required:
                continue
            mod_codes = binding.module_codes
            if mod_codes and all(code in inactive_module_codes for code in mod_codes):
                continue
            if binding.canonical_key not in canonical_values:
                missing_required.append(binding.canonical_key)

        invalid_combinations: list[str] = []
        mounting = _read_string(finish.get("mounting_system"))
        if mounting and mounting not in BAR_MOUNTING and mounting not in ("direct_wall", "none", "template_only"):
            invalid_combinations.append(f"unknown mounting_system value: {mounting}")

        unresolved_warnings: list[str] = []
        warnings: list[str] = list(form_contract.summary.warnings)
        for align in form_contract.trigger_alignments:
            unresolved_warnings.append(
                f"{align.warning_code}: {align.module_code} link={align.module_link_trigger_field} "
                f"intake={align.canonical_intake_field}"
            )
            warnings.append(
                f"{align.warning_code} for {align.module_code} — canonical intake is {align.canonical_intake_field}"
            )

        for w in aggregate.warnings:
            msg = f"{w.code}: {w.message}"
            warnings.append(msg)
            unresolved_warnings.append(msg)

        for w in form_contract.orphan_fields_audit:
            warnings.append(f"ORPHAN_FIELD: {w}")

        for module in form_contract.modules:
            if module.operational_status == "FUTURE_RESERVED_STEP_6":
                warnings.append(f"FUTURE_RESERVED: {module.module_code} — not active in Step 6 preview")

        validation = ProductDefinitionValidation(
            readiness_status=_compute_readiness(
                missing_required=sorted(set(missing_required)),
                invalid_combinations=invalid_combinations,
                unresolved_warnings=unresolved_warnings,
                has_payload=source_type == "workspace_payload",
            ),
            missing_required_fields=sorted(set(missing_required)),
            invalid_combinations=invalid_combinations,
            unresolved_warnings=unresolved_warnings,
        )

        provenance = [
            ProductDefinitionProvenanceEntry(
                key="form_contract",
                source="intake_v6_modular_form_contract",
                detail=f"version={form_contract.summary.contract_version} bindings={form_contract.summary.field_binding_count}",
            ),
            ProductDefinitionProvenanceEntry(
                key="mini_module_registry",
                source="mini_module_registry_service",
                detail=f"active_modules={form_contract.summary.active_module_count}",
            ),
            ProductDefinitionProvenanceEntry(
                key="product_aggregate",
                source="product_aggregate_service",
                detail=f"components={len(aggregate.components)} operations={len(aggregate.operations)}",
            ),
        ]
        if workspace_id:
            provenance.append(
                ProductDefinitionProvenanceEntry(
                    key="workspace_payload",
                    source="intake_v6_workspaces.payload_json",
                    detail=f"workspace_id={workspace_id} read_only=true",
                )
            )

        notes = [
            "Read-only ProductDefinition preview — Step 6. No pricing, quote, order, or task generation.",
            "Template-level preview marks missing required fields when workspace payload is absent.",
        ]

        return ProductDefinitionPreview(
            template_code=template_code,
            business_name_ro=aggregate.business_name_ro or aggregate.family_name,
            source_context=ProductDefinitionSourceContext(
                template_code=template_code,
                workspace_id=workspace_id,
                source_payload_type=source_type,  # type: ignore[arg-type]
            ),
            selected_modules=selected,
            optional_modules=optional,
            inactive_modules=inactive,
            components=_build_components(aggregate, active_modules),
            material_roles=_build_material_roles(aggregate, active_modules),
            operation_roles=_build_operation_roles(aggregate, active_modules),
            linked_template_runtime_segments=linked_template_runtime_segments,
            canonical_values=canonical_values,
            geometry_inputs=geometry_inputs,
            validation=validation,
            provenance=provenance,
            resource_hints=_build_resource_hints(self._registry, template_code),
            warnings=warnings,
            notes=notes,
        )

    async def _load_workspace_payload(
        self,
        workspace_id: str,
        template_code: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        result = await self._db.execute(
            select(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == workspace_id).limit(1)
        )
        record = result.scalar_one_or_none()
        if record is None:
            return None, "workspace_not_found"
        if record.template_code != template_code:
            return None, "workspace_template_mismatch"
        return _parse_workspace_payload(record.payload_json), None
