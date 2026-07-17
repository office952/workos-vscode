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
    ProductDefinitionComposition,
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
from services.product_definition_composition_contract import (
    build_product_definition_composition,
    metal_support_required_from_composition,
    structura_suport_active_from_composition,
)
from services.intake_v6_modular_form_contract_service import IntakeV6ModularFormContractService
from services.linked_template_runtime_segment_extraction_service import (
    extract_linked_template_segments_from_workspace_payload,
)
from services.mini_module_registry_service import MiniModuleRegistryService, get_mini_module_registry_service
from services.mounting_solution_service import (
    is_structura_suport_active,
    legacy_mounting_system_from_solution,
    read_mounting_solution,
)
from services.product_aggregate_service import ProductAggregateService
from services.acm_quote_input_helpers import (
    ACM_BOXED_MOUNTING_STANDALONE_REQUIRED_KEYS,
    is_acm_boxed_mounting_standalone_root_template,
    merge_acm_boxed_mounting_derived_fields,
)
from services.template_architecture_scope import resolve_template_identity
from schemas.active_scope import ActiveScopeResult
from services.active_scope_resolver_service import compile_active_scope

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
    composition: ProductDefinitionComposition | None = None,
    active_scope: ActiveScopeResult | None = None,
) -> str:
    mounting_system = _read_string(finish.get("mounting_system"))

    if module.operational_status.startswith("FUTURE"):
        return "future_reserved"

    code = module.module_code

    # Letters Slice 1 — sold/active scope is authority. Unselected modules are inactive
    # (not pending) so they cannot block readiness.
    if active_scope is not None and not active_scope.use_legacy_full_product:
        if active_scope.errors:
            return "inactive"
        allowed = active_scope.active_set()
        if code not in allowed:
            return "inactive"
        # Selected / prerequisite modules use scoped activation rules below.

    if code == "geometry_svg":
        return "always_on" if _has_geometry_basics({"svg_source": svg_source, "quote_geometry": quote_geometry}) else "pending"
    if code in ("debitare_fata", "debitare_spate", "modelare_cant"):
        # Full product: co-active when analysis ready.
        # Subset: only modules already allowlisted by active_scope reach here.
        return "always_on" if analysis_ready else "pending"
    if code == "structura_suport":
        if composition is not None:
            return "active" if structura_suport_active_from_composition(composition) else "inactive"
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
        # Surface finish only — template/packaging are separate runtime codes.
        if active_scope is not None and not active_scope.use_legacy_full_product:
            # Slice1 does not sell FINISH; activate only when allowlisted.
            return "active"
        return "always_on"
    if code == "sablon_montaj":
        template_on = _read_bool(finish.get("mounting_template_enabled")) is True
        if active_scope is not None and not active_scope.use_legacy_full_product:
            return "conditional_active" if template_on else "inactive"
        return "conditional_active" if template_on else "inactive"
    if code == "ambalare_livrare_montaj":
        # Composition/logistics — full Letters composition, never MOUNTING-only.
        if active_scope is not None and not active_scope.use_legacy_full_product:
            return "active" if code in active_scope.active_set() else "inactive"
        return "always_on"

    kind = module.activation_kind
    if kind in ("always_on", "required_module"):
        return "always_on" if analysis_ready else "pending"
    if kind == "optional_addon":
        return "inactive"
    return "pending"


def _resolve_letter_face_area_m2(quote_geometry: dict[str, Any]) -> Any:
    if quote_geometry.get("letter_face_area_m2") is not None:
        return quote_geometry["letter_face_area_m2"]
    if quote_geometry.get("face_area_m2") is not None:
        return quote_geometry["face_area_m2"]
    return None


def _resolve_dimension_mm(
    key: str,
    *,
    quote_geometry: dict[str, Any],
    client: dict[str, Any],
) -> Any:
    geom_val = quote_geometry.get(key)
    if geom_val is not None and geom_val != "":
        return geom_val
    client_val = client.get(key)
    if client_val is not None and client_val != "":
        return client_val
    return None


def _resolve_binding_value(
    canonical_key: str,
    *,
    finish: dict[str, Any],
    quote_geometry: dict[str, Any],
    client: dict[str, Any],
    svg_source: dict[str, Any],
) -> Any:
    if canonical_key == "vector_file":
        return _read_string(svg_source.get("file_name"))
    if canonical_key in ("width_mm", "height_mm"):
        return _resolve_dimension_mm(canonical_key, quote_geometry=quote_geometry, client=client)
    if canonical_key == "letter_face_area_m2":
        return _resolve_letter_face_area_m2(quote_geometry)
    finish_val = finish.get(canonical_key)
    if finish_val is not None and finish_val != "":
        return finish_val
    geom_val = quote_geometry.get(canonical_key)
    if geom_val is not None and geom_val != "":
        return geom_val
    client_val = client.get(canonical_key)
    if client_val is not None and client_val != "":
        return client_val
    return None


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
        if _resolve_binding_value(
            field_key,
            finish=finish,
            quote_geometry=quote_geometry,
            client=client,
            svg_source=svg_source,
        ) is None:
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
    *,
    composition: ProductDefinitionComposition | None = None,
) -> dict[str, Any]:
    values: dict[str, Any] = {}
    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
    quote_geometry = payload.get("quote_geometry") if isinstance(payload.get("quote_geometry"), dict) else {}
    client = payload.get("client") if isinstance(payload.get("client"), dict) else {}
    svg_source = payload.get("svg_source") if isinstance(payload.get("svg_source"), dict) else {}

    for binding in bindings:
        if binding.field_role == "derived_quote_input":
            if binding.canonical_key == "metal_support_required":
                derived = metal_support_required_from_composition(composition, finish=finish)
                if derived is None:
                    derived = _derive_metal_support_required(_read_string(finish.get("mounting_system")), finish)
                if derived is not None:
                    values[binding.canonical_key] = derived
            continue

        val = _get_by_path(payload, binding.workspace_path)
        if val is not None and val != "":
            values[binding.canonical_key] = val

    for binding in bindings:
        if binding.field_role == "derived_quote_input":
            continue
        if binding.canonical_key in values:
            continue
        resolved = _resolve_binding_value(
            binding.canonical_key,
            finish=finish,
            quote_geometry=quote_geometry,
            client=client,
            svg_source=svg_source,
        )
        if resolved is not None and resolved != "":
            values[binding.canonical_key] = resolved

    if "mounting_system" not in values:
        explicit_mounting = _read_string(finish.get("mounting_system"))
        if explicit_mounting:
            values["mounting_system"] = explicit_mounting
        else:
            projected = legacy_mounting_system_from_solution(read_mounting_solution(finish))
            if projected:
                values["mounting_system"] = projected

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
    composition: ProductDefinitionComposition | None = None,
    active_scope: ActiveScopeResult | None = None,
) -> tuple[list[ProductDefinitionModuleRef], list[ProductDefinitionModuleRef], list[ProductDefinitionModuleRef]]:
    selected: list[ProductDefinitionModuleRef] = []
    optional: list[ProductDefinitionModuleRef] = []
    inactive: list[ProductDefinitionModuleRef] = []
    scoped_subset = (
        active_scope is not None
        and not active_scope.use_legacy_full_product
        and not active_scope.errors
    )

    for module in modules:
        state = _resolve_module_state(
            module,
            finish=finish,
            quote_geometry=quote_geometry,
            svg_source=svg_source,
            analysis_ready=analysis_ready,
            composition=composition,
            active_scope=active_scope,
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

        reason = module.warnings[0] if module.warnings else None
        if scoped_subset and state == "inactive":
            reason = reason or "inactive_outside_offer_scope"

        ref = ProductDefinitionModuleRef(
            module_code=module.module_code,
            module_name=module.module_name,
            activation_kind=module.activation_kind,
            state=state,  # type: ignore[arg-type]
            activation_reason=reason,
            missing_fields=missing if state not in ("inactive", "future_reserved") else [],
        )

        if state == "future_reserved":
            inactive.append(ref)
        elif state == "inactive":
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
            # In-scope pending still belongs to the selected graph (missing fields
            # block readiness, not scope membership). Outside subset, keep optional.
            if scoped_subset:
                selected.append(ref)
            else:
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


def _build_acm_standalone_canonical_values(payload: dict[str, Any]) -> dict[str, Any]:
    merged = merge_acm_boxed_mounting_derived_fields(payload)
    values: dict[str, Any] = {}
    for key in ACM_BOXED_MOUNTING_STANDALONE_REQUIRED_KEYS:
        if key in merged and merged[key] is not None:
            values[key] = merged[key]
    for key, value in merged.items():
        if key not in values and value is not None:
            values[key] = value
    return values


def _build_acm_standalone_geometry_inputs(canonical_values: dict[str, Any]) -> dict[str, Any]:
    geometry: dict[str, Any] = {}
    for key in (
        "panel_width_mm",
        "panel_height_mm",
        "panel_area_m2",
        "panel_perimeter_m",
        "fold_length_m",
        "return_strip_area_m2",
        "acm_thickness_mm",
        "return_depth_mm",
    ):
        if key in canonical_values:
            geometry[key] = canonical_values[key]
    return geometry


async def _build_acm_standalone_product_definition_preview(
    *,
    aggregate: ProductAggregate,
    template_code: str,
    workspace_id: str | None,
    payload: dict[str, Any],
    source_type: str,
) -> ProductDefinitionPreview:
    active_modules = {"structura_suport"}
    structura_ref = ProductDefinitionModuleRef(
        module_code="structura_suport",
        module_name="Structura suport ACM casetat",
        activation_kind="always_on",
        state="active",
        activation_reason="Standalone boxed ACM mounting root template.",
        missing_fields=[],
    )

    canonical_values = _build_acm_standalone_canonical_values(payload) if payload else {}
    geometry_inputs = _build_acm_standalone_geometry_inputs(canonical_values)
    has_payload = source_type == "workspace_payload" or bool(canonical_values)

    missing_required = [
        key
        for key in ACM_BOXED_MOUNTING_STANDALONE_REQUIRED_KEYS
        if key not in canonical_values or canonical_values[key] in (None, "")
    ]
    if has_payload and canonical_values.get("acm_thickness_mm") == 4:
        missing_required.append("acm_thickness_mm_unsupported_4mm")

    validation = ProductDefinitionValidation(
        readiness_status=_compute_readiness(
            missing_required=sorted(set(missing_required)),
            invalid_combinations=[],
            unresolved_warnings=[],
            has_payload=has_payload,
        ),
        missing_required_fields=sorted(set(missing_required)),
        invalid_combinations=[],
        unresolved_warnings=[],
    )

    warnings = [f"{w.code}: {w.message}" for w in aggregate.warnings if hasattr(w, "code")]

    provenance = [
        ProductDefinitionProvenanceEntry(
            key="product_aggregate",
            source="product_aggregate_service",
            detail=f"standalone_root=true components={len(aggregate.components)} operations={len(aggregate.operations)}",
        ),
        ProductDefinitionProvenanceEntry(
            key="standalone_root_contract",
            source="acm_quote_input_helpers",
            detail="boxed_mounting_standalone_root_v1",
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

    return ProductDefinitionPreview(
        template_code=template_code,
        business_name_ro=aggregate.business_name_ro or aggregate.family_name,
        source_context=ProductDefinitionSourceContext(
            template_code=template_code,
            workspace_id=workspace_id,
            source_payload_type=source_type,  # type: ignore[arg-type]
        ),
        selected_modules=[structura_ref],
        optional_modules=[],
        inactive_modules=[],
        components=_build_components(aggregate, active_modules),
        material_roles=_build_material_roles(aggregate, active_modules),
        operation_roles=_build_operation_roles(aggregate, active_modules),
        linked_template_runtime_segments=None,
        canonical_values=canonical_values,
        geometry_inputs=geometry_inputs,
        validation=validation,
        provenance=provenance,
        resource_hints=ProductDefinitionResourceHints(),
        warnings=warnings,
        notes=[
            "Read-only ProductDefinition preview — standalone boxed ACM mounting root.",
            "Reuses linked-child aggregate/BOM truth; no Intake V6 modular form contract.",
        ],
        composition=build_product_definition_composition(
            root_template_code=template_code,
            payload=payload,
            source_payload_type=source_type,  # type: ignore[arg-type]
            standalone_root=True,
        ),
    )


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
        identity = resolve_template_identity(template_code)
        aggregate = await self._aggregate_svc.build(template_code)
        if aggregate is None:
            return None

        stored_template_code = aggregate.template_code

        payload: dict[str, Any] = {}
        source_type: str = "template_only"
        if workspace_id:
            ws_payload, ws_error = await self._load_workspace_payload(workspace_id, stored_template_code)
            if ws_error == "workspace_not_found":
                return None
            if ws_error == "workspace_template_mismatch":
                payload = {}
            else:
                payload = ws_payload or {}
                source_type = "workspace_payload"

        if is_acm_boxed_mounting_standalone_root_template(stored_template_code):
            preview = await _build_acm_standalone_product_definition_preview(
                aggregate=aggregate,
                template_code=stored_template_code,
                workspace_id=workspace_id,
                payload=payload,
                source_type=source_type,
            )
            preview.provenance.insert(
                0,
                ProductDefinitionProvenanceEntry(
                    key="template_identity",
                    source="template_architecture_scope",
                    detail=(
                        f"requested={identity.requested_template_code!r} "
                        f"canonical={identity.canonical_template_code!r} "
                        f"type={identity.resolution_type} "
                        f"alias={identity.legacy_alias_used} "
                        f"src={identity.resolution_source}"
                    ),
                ),
            )
            return preview

        form_contract = self._form.get_for_template(stored_template_code)
        if form_contract is None:
            return None

        finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
        quote_geometry = payload.get("quote_geometry") if isinstance(payload.get("quote_geometry"), dict) else {}
        svg_source = payload.get("svg_source") if isinstance(payload.get("svg_source"), dict) else {}
        client = payload.get("client") if isinstance(payload.get("client"), dict) else {}
        analysis_ready = bool(payload.get("analysis_ready")) or _has_geometry_basics(payload)

        active_scope = compile_active_scope(
            template_code=stored_template_code,
            payload=payload,
            quote_input=payload,
        )

        composition = build_product_definition_composition(
            root_template_code=stored_template_code,
            payload=payload,
            source_payload_type=source_type,  # type: ignore[arg-type]
        )

        selected, optional, inactive = _classify_modules(
            form_contract.modules,
            finish=finish,
            quote_geometry=quote_geometry,
            svg_source=svg_source,
            client=client,
            analysis_ready=analysis_ready,
            composition=composition,
            active_scope=active_scope,
        )

        registry_response = self._registry.get_by_template(stored_template_code)
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
        selected_codes = _active_module_codes(selected)
        if not active_scope.use_legacy_full_product and not active_scope.errors:
            # Composition graph nodes (mounting/ACM) only when allowlisted by sold scope.
            composition_active = set(composition.active_module_codes) & active_scope.active_set()
            active_modules = selected_codes | composition_active
        else:
            active_modules = selected_codes | set(composition.active_module_codes)

        canonical_values = _build_canonical_values(form_contract.field_bindings, payload, composition=composition)
        geometry_inputs = _build_geometry_inputs(canonical_values)

        linked_template_runtime_segments = None
        backbone = form_contract.form_system_backbone if isinstance(form_contract.form_system_backbone, dict) else {}
        linked_template_composition = backbone.get("linked_template_composition")
        if isinstance(linked_template_composition, dict):
            linked_template_runtime_segments = extract_linked_template_segments_from_workspace_payload(
                root_template_code=stored_template_code,
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
            # Active-scope: skip required bindings whose owning modules are all outside sold set.
            if (
                not active_scope.use_legacy_full_product
                and not active_scope.errors
                and mod_codes
                and not any(code in active_scope.active_set() for code in mod_codes)
            ):
                continue
            if binding.canonical_key not in canonical_values:
                missing_required.append(binding.canonical_key)

        invalid_combinations: list[str] = []
        mounting = _read_string(finish.get("mounting_system"))
        mounting_scope_active = (
            "structura_suport" in active_modules or "sablon_montaj" in active_modules
        )
        if (
            mounting_scope_active
            and mounting
            and mounting not in BAR_MOUNTING
            and mounting not in ("direct_wall", "none", "template_only")
        ):
            invalid_combinations.append(f"unknown mounting_system value: {mounting}")

        unresolved_warnings: list[str] = []
        warnings: list[str] = list(form_contract.summary.warnings)
        if active_scope.use_legacy_full_product:
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

            for code in composition.blockers:
                invalid_combinations.append(code)
            for code in composition.warnings:
                warnings.append(code)
                unresolved_warnings.append(code)
        else:
            # Subset: only surface warnings/blockers tied to active modules.
            for code in composition.blockers:
                if any(mod in active_modules for mod in ("structura_suport", "modelare_cant")):
                    invalid_combinations.append(code)
            warnings.append(
                f"ACTIVE_SCOPE_SUBSET mode={active_scope.mode} sold={','.join(active_scope.sold_module_codes)}"
            )

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
                key="template_identity",
                source="template_architecture_scope",
                detail=(
                    f"requested={identity.requested_template_code!r} "
                    f"canonical={identity.canonical_template_code!r} "
                    f"type={identity.resolution_type} "
                    f"alias={identity.legacy_alias_used} "
                    f"src={identity.resolution_source}"
                ),
            ),
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
            ProductDefinitionProvenanceEntry(
                key="composition_contract",
                source="product_definition_composition_contract",
                detail=f"mode={composition.composition_mode} nodes={len(composition.nodes)} edges={len(composition.edges)}",
            ),
            ProductDefinitionProvenanceEntry(
                key="active_scope",
                source="active_scope_resolver_service",
                detail=(
                    f"resolver={active_scope.resolver_version} mode={active_scope.mode} "
                    f"legacy={active_scope.use_legacy_full_product} "
                    f"sold={active_scope.sold_module_codes} "
                    f"active={active_scope.active_runtime_modules}"
                ),
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
            "Active-scope readiness validates selected modules only (offer_scope component_subset).",
        ]

        return ProductDefinitionPreview(
            template_code=stored_template_code,
            business_name_ro=aggregate.business_name_ro or aggregate.family_name,
            source_context=ProductDefinitionSourceContext(
                template_code=stored_template_code,
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
            resource_hints=_build_resource_hints(self._registry, stored_template_code),
            warnings=warnings,
            notes=notes,
            composition=composition,
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
