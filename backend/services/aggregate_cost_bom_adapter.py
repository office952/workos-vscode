"""Read-only aggregate-expanded cost BOM adapter (Step 7B).

Transforms ProductDefinition preview + ProductAggregate into a cost-ready BOM
preview without pricing quotes or persisting snapshots.
"""

from __future__ import annotations

from typing import Any

from data.mini_module_registry_volumetric_v2 import DOSSIER_COMPONENT_TO_MODULE
from schemas.aggregate_cost_bom import (
    AggregateExpandedCostBom,
    BomStatus,
    CostBomCostableComponent,
    CostBomCostableMaterial,
    CostBomCostableOperation,
    CostBomMissingPricing,
    CostBomModuleRef,
    CostBomPricingBlocker,
    CostBomPricingRequirement,
    CostBomProvenanceEntry,
    CostBomSkippedItem,
    CostBomSourceContext,
    CostLineClassificationEntry,
    ExternalizationRequirement,
    InventoryUsageEntry,
    ProductionMode,
    ResellerRequirement,
    SubcontractableOperation,
)
from schemas.mini_module_registry import MiniModuleContract
from schemas.product_aggregate import (
    ProductAggregate,
    ProductAggregateComponent,
    ProductAggregateMaterial,
    ProductAggregateOperation,
)
from schemas.product_definition import ProductDefinitionPreview
from services.template_architecture_scope import VOLUMETRIC_LOGO_TEMPLATE_CODE
from services.logo_artwork_cost_ownership import (
    include_material_in_composed_aggregate,
    include_operation_in_composed_aggregate,
)
from services.aggregate_cost_externalization_hooks import (
    MODULE_FUTURE_EXTERNALIZATION,
    OPERATION_EXTERNALIZATION_HOOKS,
    RESELLER_PRODUCT_FUTURE,
    get_operation_hook,
    is_external_service_possible,
)
from services.pricing_registry_service import (
    PREMOUNT_STRUCTURE_MATERIAL_CODES,
    TEMPLATE_MATERIAL_VARIANT_EXPANSION,
    V6_REQUIRED_MATERIAL_CODES,
    _expand_material_codes_for_template,
)
from services.volumetric_material_rate_resolver import (
    PROFILE_DEPTH_MM_TO_VARIANT_CODE,
    PSU_WATTS_TO_VARIANT_CODE,
    TEMPLATE_PROFILE_CODE,
    TEMPLATE_PSU_CODE,
)
from services.acm_bond_material_rate_resolver import (
    ACM_THICKNESS_MM_TO_VARIANT_CODE,
    TEMPLATE_ACM_BOND_CODE,
)

BAR_MOUNTING = frozenset({"steel_bars", "aluminum_bars"})
SYNTHETIC_COMPONENT_IDS = frozenset({"comp_auto_1", "comp_flat_legacy"})
GEOMETRY_GATE_OPERATIONS = frozenset({"svg_geometry_analysis"})
GATE_ONLY_MODULES = frozenset({"geometry_svg"})
FUTURE_MODULES = frozenset({"electrica_logo"})
ALWAYS_COSTABLE_MODULES = frozenset(
    {
        "debitare_fata",
        "modelare_cant",
        "debitare_spate",
        "sistem_led",
        "finisaje",
        "sablon_montaj",
        "ambalare_livrare_montaj",
        "structura_suport",
    }
)

MODULE_GEOMETRY_KEYS: dict[str, list[str]] = {
    "geometry_svg": ["vector_file", "width_mm", "height_mm", "letter_count"],
    "debitare_fata": ["letter_face_area_m2", "face_finish_type"],
    "modelare_cant": ["return_depth_mm", "letter_perimeter_m"],
    "debitare_spate": ["backing_mode", "letter_face_area_m2"],
    "sistem_led": ["lighting_system_type", "selected_psu_watts", "led_module_count"],
    "finisaje": ["face_finish_type"],
    "sablon_montaj": ["mounting_template_enabled"],
    "ambalare_livrare_montaj": ["packaging_required"],
    "structura_suport": ["mounting_system"],
}

CRITICAL_GEOMETRY_FOR_READY = frozenset(
    {
        "letter_face_area_m2",
        "letter_perimeter_m",
        "return_depth_mm",
        "width_mm",
        "height_mm",
        "letter_count",
    }
)

WARNING_LINKED_SEGMENT_FINISH_PARTIAL = "LINKED_SEGMENT_FINISH_PARTIAL"
SEGMENT_NAMESPACE_SEP = "::"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _is_namespaced_segment_ref(value: str | None) -> bool:
    return SEGMENT_NAMESPACE_SEP in _text(value)


def _is_aggregate_linked_logo_component(comp: ProductAggregateComponent) -> bool:
    if not _is_namespaced_segment_ref(comp.component_id):
        return False
    return _text(comp.source_template_code) == VOLUMETRIC_LOGO_TEMPLATE_CODE


def _is_aggregate_linked_logo_material(mat: ProductAggregateMaterial) -> bool:
    if _text(mat.source_template_code) != VOLUMETRIC_LOGO_TEMPLATE_CODE:
        return False
    return _is_namespaced_segment_ref(mat.component_ref)


def _is_aggregate_linked_logo_operation(op: ProductAggregateOperation) -> bool:
    if _text(op.source_template_code) != VOLUMETRIC_LOGO_TEMPLATE_CODE:
        return False
    return _is_namespaced_segment_ref(op.component_ref)


def _aggregate_has_partial_linked_logo(aggregate: ProductAggregate) -> bool:
    if any(w.code == WARNING_LINKED_SEGMENT_FINISH_PARTIAL for w in aggregate.warnings):
        return True
    return any(
        _is_aggregate_linked_logo_component(comp) and comp.status == "partial"
        for comp in aggregate.components
    )


def _module_is_cost_active(state: str) -> bool:
    return state in ("always_on", "active", "conditional_active")


def _legacy_structural_active_modules(
    pd: ProductDefinitionPreview,
    quote_input: dict[str, Any] | None = None,
) -> set[str]:
    """Modules whose aggregate lines belong in the cost BOM (structure vs runtime pending)."""
    active: set[str] = set()
    seen: set[str] = set()
    all_mods = list(pd.selected_modules) + list(pd.optional_modules) + list(pd.inactive_modules)
    for mod in all_mods:
        if mod.module_code in seen:
            continue
        seen.add(mod.module_code)
        code = mod.module_code
        if code in FUTURE_MODULES or code in GATE_ONLY_MODULES:
            continue
        if code == "structura_suport":
            if mod.state == "active":
                active.add(code)
            continue
        from services.letters_finish_mounting_runtime_decoupling import (
            apply_decoupled_module_activation,
        )

        if apply_decoupled_module_activation(
            code=code,
            state=mod.state,
            activation_kind=mod.activation_kind or "",
            active=active,
        ):
            continue
        if code == "sistem_led":
            if mod.state in ("active", "conditional_active"):
                active.add(code)
            continue
        if mod.activation_kind in ("always_on", "required_module"):
            active.add(code)
            continue
        if _module_is_cost_active(mod.state):
            active.add(code)

    if quote_input:
        finish = quote_input.get("finish_setup") if isinstance(quote_input.get("finish_setup"), dict) else {}
        merged_finish = dict(finish)
        for key in (
            "mounting_system",
            "lighting_system_type",
            "illuminated",
            "return_depth_mm",
            "return_finish_type",
            "selected_psu_watts",
            "led_module_count",
        ):
            if key in quote_input and key not in merged_finish:
                merged_finish[key] = quote_input[key]

        mounting = merged_finish.get("mounting_system")
        from services.mounting_solution_service import is_structura_suport_active

        if is_structura_suport_active(merged_finish):
            active.add("structura_suport")
        elif mounting:
            if mounting in BAR_MOUNTING:
                active.add("structura_suport")
            else:
                active.discard("structura_suport")

        illuminated = merged_finish.get("illuminated")
        is_lit = illuminated is True or str(illuminated).lower() in ("true", "1", "yes")
        lighting = merged_finish.get("lighting_system_type")
        if is_lit and lighting and str(lighting).strip().lower() not in ("", "none"):
            active.add("sistem_led")
        elif not is_lit:
            active.discard("sistem_led")

    return active


def _structural_active_modules(
    pd: ProductDefinitionPreview,
    quote_input: dict[str, Any] | None = None,
) -> set[str]:
    from services.offer_scope_resolver_service import resolve_pricing_active_modules

    payload = dict(quote_input) if quote_input else {}
    return resolve_pricing_active_modules(
        pd=pd,
        payload=payload,
        quote_input=quote_input,
        legacy_fn=_legacy_structural_active_modules,
    )


def _active_module_codes(
    pd: ProductDefinitionPreview,
    quote_input: dict[str, Any] | None = None,
    aggregate: ProductAggregate | None = None,
) -> tuple[set[str], Any | None]:
    if aggregate is not None and aggregate.composition_graph is not None:
        from services.product_aggregate_graph_cost_projection_service import resolve_cost_active_modules

        active, projection = resolve_cost_active_modules(
            pd=pd,
            aggregate=aggregate,
            quote_input=quote_input,
        )
        if projection is not None:
            return active, projection
    return _structural_active_modules(pd, quote_input), None


def _inactive_module_codes(pd: ProductDefinitionPreview) -> set[str]:
    inactive = {m.module_code for m in pd.inactive_modules}
    for m in pd.optional_modules:
        if not _module_is_cost_active(m.state):
            inactive.add(m.module_code)
    for m in pd.selected_modules + pd.optional_modules + pd.inactive_modules:
        if m.state in ("inactive", "future_reserved"):
            inactive.add(m.module_code)
    return inactive


def _canonical_and_quote_input(
    pd: ProductDefinitionPreview,
    quote_input: dict[str, Any] | None,
) -> dict[str, Any]:
    from services.acm_quote_input_helpers import merge_acm_boxed_mounting_derived_fields

    merged = dict(pd.canonical_values)
    if not quote_input:
        return merged
    coalesced = merge_acm_boxed_mounting_derived_fields(quote_input)
    merged.update(
        {
            k: v
            for k, v in coalesced.items()
            if v is not None and v != "" and not isinstance(v, dict)
        }
    )
    finish = coalesced.get("finish_setup") if isinstance(coalesced.get("finish_setup"), dict) else {}
    for key, value in finish.items():
        if value is not None and value != "":
            merged[key] = value
    geometry = coalesced.get("quote_geometry") if isinstance(coalesced.get("quote_geometry"), dict) else {}
    for key, value in geometry.items():
        if value is not None and value != "":
            merged[key] = value
    client = coalesced.get("client") if isinstance(coalesced.get("client"), dict) else {}
    for key, value in client.items():
        if value is not None and value != "":
            merged[key] = value
    return merged


def _resolve_material_code(
    material_code: str,
    values: dict[str, Any],
) -> tuple[str, list[str], str | None]:
    """Return (resolved_code, required_geometry_keys, variant_error)."""
    if material_code == TEMPLATE_PSU_CODE:
        watts_raw = values.get("selected_psu_watts") or values.get("psu_watts")
        if watts_raw is None or watts_raw == "":
            return material_code, ["selected_psu_watts"], "missing_psu_watts_selection"
        try:
            watts = int(watts_raw)
        except (TypeError, ValueError):
            return material_code, ["selected_psu_watts"], "unsupported_psu_watts"
        variant = PSU_WATTS_TO_VARIANT_CODE.get(watts)
        if not variant:
            return material_code, ["selected_psu_watts"], "unsupported_psu_watts"
        return variant, ["selected_psu_watts"], None

    if material_code == TEMPLATE_PROFILE_CODE or material_code.startswith("MAT-PROFIL-LATERAL-LITERE"):
        depth_raw = values.get("return_depth_mm")
        if depth_raw is None or depth_raw == "":
            return material_code, ["return_depth_mm"], "missing_return_depth_mm"
        try:
            depth = int(depth_raw)
        except (TypeError, ValueError):
            return material_code, ["return_depth_mm"], "unsupported_return_depth_mm"
        variant = PROFILE_DEPTH_MM_TO_VARIANT_CODE.get(depth)
        if not variant:
            return material_code, ["return_depth_mm"], "unsupported_return_depth_mm"
        return variant, ["return_depth_mm"], None

    if material_code == TEMPLATE_ACM_BOND_CODE:
        thickness_raw = values.get("acm_thickness_mm")
        if thickness_raw is None or thickness_raw == "":
            return material_code, ["acm_thickness_mm"], "missing_acm_thickness_mm"
        try:
            thickness = int(round(float(thickness_raw)))
        except (TypeError, ValueError):
            return material_code, ["acm_thickness_mm"], "unsupported_acm_thickness_mm"
        variant = ACM_THICKNESS_MM_TO_VARIANT_CODE.get(thickness)
        if not variant:
            return material_code, ["acm_thickness_mm"], "unsupported_acm_thickness_mm"
        return variant, ["acm_thickness_mm"], None

    return material_code, [], None


def _sold_led_subscopes_from_quote(quote_input: dict[str, Any] | None) -> frozenset | None:
    if not quote_input:
        return None
    from services.offer_scope_led_subscope_service import resolve_sold_led_subscopes

    return resolve_sold_led_subscopes(quote_input, quote_input)


def _mount_consumer_from_quote(quote_input: dict[str, Any] | None):
    if not quote_input:
        return None
    from services.lighting_mount_consumer_service import resolve_lighting_mount_consumers

    return resolve_lighting_mount_consumers(quote_input, quote_input)


def _material_module_active(
    mat: ProductAggregateMaterial,
    active_modules: set[str],
    sold_led_subscopes: frozenset | None = None,
    mount_decision=None,
) -> bool:
    from services.offer_scope_led_subscope_service import (
        aggregate_material_led_subscope,
        led_consumer_row_allowed,
        led_runtime_module_bucket,
    )

    if _is_aggregate_linked_logo_material(mat):
        return True
    effective_mini = led_runtime_module_bucket(mat.mini_module_code)
    if effective_mini:
        if effective_mini not in active_modules:
            return False
    elif mat.component_ref:
        mod = DOSSIER_COMPONENT_TO_MODULE.get(mat.component_ref)
        if mod and mod not in active_modules:
            return False
    elif mat.provenance == "linked_module" and mat.source_template_code:
        if "PREMOUNT" in mat.source_template_code and "structura_suport" not in active_modules:
            return False
        if "VOLUM-ALUMINIU" in mat.source_template_code:
            return "modelare_cant" in active_modules
    elif mat.provenance == "parent":
        mod = DOSSIER_COMPONENT_TO_MODULE.get(mat.component_ref or "")
        if mod and mod not in active_modules:
            return False
    elif mat.mini_module_code and mat.mini_module_code not in active_modules:
        return False

    if sold_led_subscopes is not None:
        sub = aggregate_material_led_subscope(mat.material_code)
        if sub is not None and not led_consumer_row_allowed(
            row_subscope=sub,
            sold_led_subscopes=sold_led_subscopes,
            material_key=str(mat.material_code or ""),
            mount_decision=mount_decision,
        ):
            return False
    return True


def _operation_module_active(
    op: ProductAggregateOperation,
    active_modules: set[str],
    sold_led_subscopes: frozenset | None = None,
    mount_decision=None,
) -> bool:
    from services.offer_scope_led_subscope_service import (
        led_consumer_row_allowed,
        led_runtime_module_bucket,
        operation_led_subscope,
    )

    if _is_aggregate_linked_logo_operation(op):
        return True
    effective_mini = led_runtime_module_bucket(op.mini_module_code)
    if effective_mini:
        if effective_mini not in active_modules:
            return False
    elif op.operation_code in GEOMETRY_GATE_OPERATIONS:
        if "geometry_svg" not in active_modules:
            return False
    elif op.provenance == "linked_module" and op.source_template_code:
        if "PREMOUNT" in (op.source_template_code or ""):
            if "structura_suport" not in active_modules:
                return False
        elif "VOLUM-ALUMINIU" in (op.source_template_code or ""):
            if "modelare_cant" not in active_modules:
                return False
    elif op.component_ref:
        mod = DOSSIER_COMPONENT_TO_MODULE.get(op.component_ref)
        if mod and mod not in active_modules:
            return False
    elif op.mini_module_code and op.mini_module_code not in active_modules:
        return False

    if sold_led_subscopes is not None:
        sub = operation_led_subscope(op.operation_code)
        if sub is not None and not led_consumer_row_allowed(
            row_subscope=sub,
            sold_led_subscopes=sold_led_subscopes,
            operation_code=op.operation_code,
            mount_decision=mount_decision,
        ):
            return False
    return True


def _check_material_pricing(
    resolved_code: str,
    material_rates: dict[str, float],
    variant_error: str | None,
) -> tuple[str, float | None]:
    if variant_error:
        return "variant_required", None
    rate = material_rates.get(resolved_code)
    if rate is None or rate <= 0:
        return "missing", None
    return "available", float(rate)


def _check_workcenter_pricing(workcenter: str | None, workcenter_rates: dict[str, Any]) -> str:
    if not workcenter:
        return "missing"
    rate = workcenter_rates.get(workcenter)
    if rate is None:
        return "missing"
    if isinstance(rate, dict):
        basis = str(rate.get("rate_basis") or "per_hour")
        if basis == "per_hour":
            value = rate.get("rate_per_hour")
        else:
            value = rate.get("rate_per_linear_meter")
        if value is None or float(value) <= 0:
            return "missing"
        return "available"
    if float(rate) <= 0:
        return "missing"
    return "available"


def _material_module_code(mat: ProductAggregateMaterial) -> str | None:
    if mat.mini_module_code:
        return mat.mini_module_code
    return DOSSIER_COMPONENT_TO_MODULE.get(mat.component_ref or "")


def _inventory_has_code(code: str, inventory_catalog: dict[str, dict]) -> bool:
    return code in inventory_catalog


def _inventory_has_valid_price(
    code: str,
    inventory_catalog: dict[str, dict],
    material_rates: dict[str, float],
) -> bool:
    if code in material_rates and material_rates[code] > 0:
        return True
    row = inventory_catalog.get(code)
    if not row:
        return False
    status = str(row.get("status") or "").lower()
    unit_cost = row.get("unit_cost")
    return status == "active" and unit_cost is not None and float(unit_cost) > 0


def _template_material_scope(template_code: str) -> tuple[set[str], set[str]]:
    required = set(V6_REQUIRED_MATERIAL_CODES)
    optional = set(PREMOUNT_STRUCTURE_MATERIAL_CODES)
    registry_codes = set(_expand_material_codes_for_template(template_code, required | optional))
    return required, registry_codes


def _classify_material_inventory(
    mat: ProductAggregateMaterial,
    *,
    mod: str | None,
    module_active: bool,
    inventory_catalog: dict[str, dict],
    material_rates: dict[str, float],
    resolved: str,
    availability: str,
    variant_err: str | None,
) -> tuple[str, str | None, int | None]:
    """Return (classification, notes, owner_step)."""
    if mat.provenance == "parent":
        return (
            "LEGACY_REFERENCED_ONLY",
            "Parent template BOM reference — aggregate-expanded path is structural truth.",
            None,
        )
    if mod in FUTURE_MODULES:
        return (
            "FUTURE_RESERVED_BY_TEMPLATE",
            f"Module {mod} is future_reserved — not costed in Step 7B.1.",
            8,
        )
    if not module_active:
        return (
            "USED_BY_OPTIONAL_MODULE",
            f"Material belongs to optional/inactive module {mod or 'unknown'}.",
            None,
        )
    if variant_err:
        if mat.material_code == TEMPLATE_PSU_CODE:
            return (
                "USED_BY_ACTIVE_TEMPLATE",
                "Base MAT-LED-PSU-12V requires watt variant selection — not a zero fallback.",
                None,
            )
        if mat.material_code == TEMPLATE_PROFILE_CODE or mat.material_code.startswith("MAT-PROFIL-LATERAL-LITERE"):
            return (
                "USED_BY_ACTIVE_TEMPLATE",
                "Profile material requires return_depth_mm variant selection.",
                None,
            )
        if mat.material_code == TEMPLATE_ACM_BOND_CODE:
            return (
                "USED_BY_ACTIVE_TEMPLATE",
                "ACM bond panel requires acm_thickness_mm variant selection.",
                None,
            )
    in_inventory = _inventory_has_code(resolved, inventory_catalog) or _inventory_has_code(
        mat.material_code, inventory_catalog
    )
    if not in_inventory and not variant_err:
        return (
            "MISSING_FROM_INVENTORY",
            f"Material {resolved} required by active template path but absent from Inventory/Pricing Registry.",
            None,
        )
    if availability == "missing" and not variant_err:
        return (
            "MISSING_PRICE",
            "Material exists in registry scope but lacks owner_confirmed active rate.",
            None,
        )
    return ("USED_BY_ACTIVE_TEMPLATE", None, None)


def _build_inventory_alignment(
    *,
    template_code: str,
    aggregate: ProductAggregate,
    active_modules: set[str],
    inventory_catalog: dict[str, dict],
    material_rates: dict[str, float],
    costable_materials: list[CostBomCostableMaterial],
    missing_pricing: list[CostBomMissingPricing],
    values: dict[str, Any],
    sold_led_subscopes: frozenset | None = None,
    mount_decision=None,
) -> tuple[
    list[InventoryUsageEntry],
    list[str],
    list[str],
    list[str],
    list[str],
    list[str],
    list[CostBomPricingBlocker],
]:
    template_required, template_registry = _template_material_scope(template_code)
    template_optional = set(PREMOUNT_STRUCTURE_MATERIAL_CODES)

    inventory_usage: list[InventoryUsageEntry] = []
    missing_inventory_materials: list[str] = []
    legacy_inventory_references: list[str] = []
    pricing_blockers: list[CostBomPricingBlocker] = []

    seen_usage: set[str] = set()
    used_by_template: set[str] = set()

    for mat in aggregate.materials:
        mod = _material_module_code(mat)
        module_active = _material_module_active(mat, active_modules, sold_led_subscopes, mount_decision)
        resolved, _, variant_err = _resolve_material_code(mat.material_code, values)
        availability, _ = _check_material_pricing(resolved, material_rates, variant_err)
        classification, notes, owner_step = _classify_material_inventory(
            mat,
            mod=mod,
            module_active=module_active,
            inventory_catalog=inventory_catalog,
            material_rates=material_rates,
            resolved=resolved,
            availability=availability,
            variant_err=variant_err,
        )

        if mat.provenance == "parent":
            legacy_inventory_references.append(mat.material_code)

        if module_active:
            used_by_template.add(mat.material_code)
            if resolved != mat.material_code:
                used_by_template.add(resolved)

        usage_key = f"{mat.material_code}:{classification}"
        if usage_key in seen_usage:
            continue
        seen_usage.add(usage_key)

        in_inv = _inventory_has_code(resolved, inventory_catalog) or _inventory_has_code(
            mat.material_code, inventory_catalog
        )
        has_price = _inventory_has_valid_price(resolved, inventory_catalog, material_rates)

        inventory_usage.append(
            InventoryUsageEntry(
                material_code=mat.material_code,
                resolved_material_code=resolved if resolved != mat.material_code else None,
                classification=classification,  # type: ignore[arg-type]
                module_code=mod,
                module_active=module_active,
                in_inventory=in_inv,
                has_valid_price=has_price and not variant_err,
                provenance=mat.provenance,
                owner_step=owner_step,
                notes=notes,
            )
        )

        if classification == "MISSING_FROM_INVENTORY" and module_active:
            missing_inventory_materials.append(resolved)
            pricing_blockers.append(
                CostBomPricingBlocker(
                    blocker_code="MISSING_FROM_INVENTORY",
                    item_type="inventory",
                    code=resolved,
                    reason=notes or "missing_from_inventory",
                    module_code=mod,
                )
            )
        if classification == "MISSING_PRICE" and module_active:
            pricing_blockers.append(
                CostBomPricingBlocker(
                    blocker_code="MISSING_PRICE",
                    item_type="material",
                    code=resolved,
                    reason=notes or "missing_price",
                    module_code=mod,
                )
            )

    for mp in missing_pricing:
        if mp.reason in ("missing_psu_watts_selection", "missing_return_depth_mm"):
            pricing_blockers.append(
                CostBomPricingBlocker(
                    blocker_code="VARIANT_REQUIRED",
                    item_type="variant",
                    code=mp.code,
                    reason=mp.reason,
                    module_code=mp.module_code,
                )
            )

    costable_codes = {m.material_code for m in costable_materials}
    costable_resolved = {
        m.resolved_material_code or m.material_code for m in costable_materials
    }
    active_used = costable_codes | costable_resolved | used_by_template

    unused_inventory_candidates: list[str] = []
    for code in sorted(template_registry):
        if code not in active_used and _inventory_has_code(code, inventory_catalog):
            unused_inventory_candidates.append(code)
            inventory_usage.append(
                InventoryUsageEntry(
                    material_code=code,
                    classification="UNUSED_IN_TEMPLATE",
                    module_code=None,
                    module_active=False,
                    in_inventory=True,
                    has_valid_price=_inventory_has_valid_price(code, inventory_catalog, material_rates),
                    notes="Present in Inventory/Pricing Registry but not used by current active template path.",
                )
            )

    for code in sorted(legacy_inventory_references):
        if code not in {u.material_code for u in inventory_usage if u.classification == "LEGACY_REFERENCED_ONLY"}:
            pass  # already captured per material

    return (
        inventory_usage,
        sorted(set(missing_inventory_materials)),
        unused_inventory_candidates,
        sorted(set(legacy_inventory_references)),
        sorted(template_required),
        sorted(template_optional),
        pricing_blockers,
    )


def _build_externalization_readiness(
    *,
    template_code: str,
    aggregate: ProductAggregate,
    active_modules: set[str],
    costable_operations: list[CostBomCostableOperation],
    costable_materials: list[CostBomCostableMaterial],
    workcenter_rates: dict[str, float],
    external_selections: dict[str, bool] | None = None,
) -> tuple[
    ProductionMode,
    list[ExternalizationRequirement],
    list[ResellerRequirement],
    list[SubcontractableOperation],
    list[CostLineClassificationEntry],
    list[CostBomPricingBlocker],
]:
    external_selections = external_selections or {}
    externalization_requirements: list[ExternalizationRequirement] = []
    subcontractable_operations: list[SubcontractableOperation] = []
    cost_line_classification: list[CostLineClassificationEntry] = []
    pricing_blockers: list[CostBomPricingBlocker] = []

    seen_subcontract: set[str] = set()
    scanned_ops: list[tuple[str, str | None, str | None]] = []
    for op in aggregate.operations:
        scanned_ops.append((op.operation_code, op.workcenter, op.label))
    for cop in costable_operations:
        if cop.operation_code not in {o[0] for o in scanned_ops}:
            scanned_ops.append((cop.operation_code, cop.workcenter, None))

    for op_code, wc, label in scanned_ops:
        hook = get_operation_hook(op_code) or (get_operation_hook(wc) if wc else None)
        if not hook:
            continue
        op_key = hook["code"]
        if op_key in seen_subcontract:
            continue
        seen_subcontract.add(op_key)

        mod = None
        for op in aggregate.operations:
            if op.operation_code == op_code:
                mod = op.mini_module_code
                break
        if not mod:
            for cop in costable_operations:
                if cop.operation_code == op_code:
                    mod = cop.mini_module_code
                    break
        mod = mod or hook.get("module_code")
        mod_active = mod in active_modules if mod else True
        if mod in FUTURE_MODULES:
            continue

        default_mode: ProductionMode = hook.get("default_mode", "external_service_possible")  # type: ignore[assignment]
        subcontractable_operations.append(
            SubcontractableOperation(
                operation_code=op_code,
                label=label,
                module_code=mod,
                default_mode=default_mode,
                fallback_mode=hook.get("fallback_mode"),
                required_machine_type=hook.get("required_machine_type"),
                external_partner_fallback=hook.get("external_partner_fallback"),
                owner_step=hook.get("owner_step", 9),
            )
        )

        selected_now = external_selections.get(hook["code"], False)
        requires_external_price = selected_now
        blocks = selected_now

        externalization_requirements.append(
            ExternalizationRequirement(
                code=hook["code"],
                label=hook["label"],
                module_code=mod,
                reason=hook["reason"],
                supplier_type=hook.get("supplier_type"),
                selected_now=selected_now,
                requires_external_price=requires_external_price,
                blocks_pricing_if_selected_without_price=blocks,
                creates_external_task_now=False,
                owner_step=hook.get("owner_step", 9),
                production_mode=default_mode,
            )
        )

    for mod_code, hook in MODULE_FUTURE_EXTERNALIZATION.items():
        externalization_requirements.append(
            ExternalizationRequirement(
                code=hook["code"],
                label=hook["label"],
                module_code=hook.get("module_code", mod_code),
                reason=hook["reason"],
                selected_now=False,
                requires_external_price=False,
                blocks_pricing_if_selected_without_price=False,
                creates_external_task_now=False,
                owner_step=hook.get("owner_step", 8),
                production_mode="future_reserved",
            )
        )

    for sel_code, selected in external_selections.items():
        if not selected:
            continue
        existing = next((r for r in externalization_requirements if r.code == sel_code), None)
        if existing:
            externalization_requirements = [
                r.model_copy(
                    update={
                        "selected_now": True,
                        "requires_external_price": True,
                        "blocks_pricing_if_selected_without_price": True,
                    }
                )
                if r.code == sel_code
                else r
                for r in externalization_requirements
            ]
            pricing_blockers.append(
                CostBomPricingBlocker(
                    blocker_code="EXTERNAL_PRICE_REQUIRED",
                    item_type="external",
                    code=sel_code,
                    reason="External service selected but external price/source not configured.",
                    module_code=existing.module_code,
                )
            )
            continue
        hook = next((h for h in OPERATION_EXTERNALIZATION_HOOKS.values() if h["code"] == sel_code), None)
        if hook:
            externalization_requirements.append(
                ExternalizationRequirement(
                    code=hook["code"],
                    label=hook["label"],
                    module_code=hook.get("module_code"),
                    reason=hook["reason"],
                    supplier_type=hook.get("supplier_type"),
                    selected_now=True,
                    requires_external_price=True,
                    blocks_pricing_if_selected_without_price=True,
                    creates_external_task_now=False,
                    owner_step=hook.get("owner_step", 9),
                    production_mode=hook.get("default_mode", "external_service_possible"),
                )
            )
            pricing_blockers.append(
                CostBomPricingBlocker(
                    blocker_code="EXTERNAL_PRICE_REQUIRED",
                    item_type="external",
                    code=sel_code,
                    reason="External service selected but external price/source not configured.",
                    module_code=hook.get("module_code"),
                )
            )

    reseller_requirements = [
        ResellerRequirement(
            product_code=item["product_code"],
            label=item["label"],
            purchase_price_required=item.get("purchase_price_required", True),
            supplier_required=item.get("supplier_required", True),
            margin_policy_required=item.get("margin_policy_required", True),
            internal_operations_required=item.get("internal_operations_required", False),
            status=item.get("status", "future_reserved"),
            owner_step=item.get("owner_step", 8),
        )
        for item in RESELLER_PRODUCT_FUTURE
    ]

    for mat in costable_materials:
        cost_line_classification.append(
            CostLineClassificationEntry(
                item_type="material",
                item_key=mat.resolved_material_code or mat.material_code,
                classification="INTERNAL_PRODUCTION",
                production_mode="internal_production",
                module_code=mat.mini_module_code,
            )
        )

    for op in costable_operations:
        hook = get_operation_hook(op.operation_code) or (
            get_operation_hook(op.workcenter) if op.workcenter else None
        )
        if hook and hook.get("default_mode") == "external_service_possible":
            classification = "FUTURE_EXTERNALIZATION_RULE"
            prod_mode: ProductionMode = "external_service_possible"
        elif hook and external_selections.get(hook["code"], False):
            classification = "EXTERNAL_SERVICE"
            prod_mode = "external_service_required"
        else:
            classification = "INTERNAL_PRODUCTION"
            prod_mode = "internal_production"

        cost_line_classification.append(
            CostLineClassificationEntry(
                item_type="operation",
                item_key=op.operation_code,
                classification=classification,  # type: ignore[arg-type]
                production_mode=prod_mode,
                module_code=op.mini_module_code,
            )
        )

    for item in reseller_requirements:
        cost_line_classification.append(
            CostLineClassificationEntry(
                item_type="component",
                item_key=item.product_code,
                classification="RESELLER_PRODUCT",
                production_mode="reseller_product_future",
                module_code=None,
            )
        )

    production_mode: ProductionMode = "internal_production"
    if any(
        r.selected_now
        for r in externalization_requirements
        if r.production_mode != "future_reserved"
    ):
        production_mode = "hybrid_internal_external"

    return (
        production_mode,
        externalization_requirements,
        reseller_requirements,
        subcontractable_operations,
        cost_line_classification,
        pricing_blockers,
    )


class AggregateCostBomAdapter:
    """Build aggregate-expanded cost BOM from PD + Aggregate (read-only)."""

    def build(
        self,
        *,
        product_definition: ProductDefinitionPreview,
        aggregate: ProductAggregate,
        quote_input: dict[str, Any] | None = None,
        material_rates: dict[str, float] | None = None,
        workcenter_rates: dict[str, float] | None = None,
        material_currencies: dict[str, str] | None = None,
        inventory_catalog: dict[str, dict] | None = None,
        registry_modules: list[MiniModuleContract] | None = None,
        external_selections: dict[str, bool] | None = None,
    ) -> AggregateExpandedCostBom:
        pd = product_definition
        material_rates = material_rates or {}
        workcenter_rates = workcenter_rates or {}
        material_currencies = material_currencies or {}
        inventory_catalog = inventory_catalog or {}
        values = _canonical_and_quote_input(pd, quote_input)

        active_modules, graph_cost_projection = _active_module_codes(pd, quote_input, aggregate)
        sold_led_subscopes = _sold_led_subscopes_from_quote(quote_input)
        mount_decision = _mount_consumer_from_quote(quote_input)
        inactive_modules_set = _inactive_module_codes(pd)

        active_module_refs: list[CostBomModuleRef] = []
        inactive_module_refs: list[CostBomModuleRef] = []

        all_module_refs = (
            list(pd.selected_modules) + list(pd.optional_modules) + list(pd.inactive_modules)
        )
        seen_modules: set[str] = set()
        for mod in all_module_refs:
            if mod.module_code in seen_modules:
                continue
            seen_modules.add(mod.module_code)
            included = mod.module_code in active_modules and mod.module_code not in GATE_ONLY_MODULES
            if mod.module_code in FUTURE_MODULES:
                included = False
            ref = CostBomModuleRef(
                module_code=mod.module_code,
                module_name=mod.module_name,
                state=mod.state,
                included_in_cost_bom=included,
                exclusion_reason=(
                    None
                    if included
                    else (
                        "geometry_gate_only"
                        if mod.module_code in GATE_ONLY_MODULES
                        else (
                            "future_reserved"
                            if mod.module_code in FUTURE_MODULES
                            else "module_inactive_or_pending"
                        )
                    )
                ),
            )
            if included or mod.module_code in GATE_ONLY_MODULES:
                active_module_refs.append(ref)
            else:
                inactive_module_refs.append(ref)

        skipped: list[CostBomSkippedItem] = []
        warnings: list[str] = list(pd.warnings)
        for w in aggregate.warnings:
            warnings.append(f"{w.code}: {w.message}")

        skipped.append(
            CostBomSkippedItem(
                item_type="module",
                item_key="geometry_svg",
                reason="geometry_gate",
                detail="SVG geometry analysis is readiness gate only — not a priced cost line.",
            )
        )
        for mod_code in FUTURE_MODULES:
            if any(m.module_code == mod_code for m in all_module_refs):
                skipped.append(
                    CostBomSkippedItem(
                        item_type="module",
                        item_key=mod_code,
                        reason="future_reserved",
                        detail="FUTURE_RESERVED — not costed in Step 7B.",
                    )
                )

        skipped.append(
            CostBomSkippedItem(
                item_type="component",
                item_key="comp_flat_legacy",
                reason="legacy_parent_only",
                detail="Parent flat legacy BOM (comp_flat_legacy) is diagnostic only — not structural truth.",
            )
        )

        costable_components: list[CostBomCostableComponent] = []
        for comp in aggregate.components:
            if comp.component_id in SYNTHETIC_COMPONENT_IDS:
                skipped.append(
                    CostBomSkippedItem(
                        item_type="component",
                        item_key=comp.component_id,
                        reason="synthetic_component",
                        detail="Synthetic legacy component — excluded from aggregate cost BOM.",
                    )
                )
                continue
            if _is_aggregate_linked_logo_component(comp):
                mod = comp.mini_module_code or DOSSIER_COMPONENT_TO_MODULE.get(
                    comp.component_id.split(SEGMENT_NAMESPACE_SEP, 1)[0]
                )
            else:
                mod = comp.mini_module_code or DOSSIER_COMPONENT_TO_MODULE.get(comp.component_id)
            if mod in GATE_ONLY_MODULES or mod in FUTURE_MODULES:
                continue
            if not _is_aggregate_linked_logo_component(comp) and mod and mod not in active_modules:
                continue
            costable_components.append(
                CostBomCostableComponent(
                    component_id=comp.component_id,
                    label_ro=comp.label_ro,
                    role=comp.role,
                    mini_module_code=mod,
                    provenance=comp.provenance,
                    source_template_code=comp.source_template_code,
                )
            )

        missing_geometry: list[str] = []
        missing_pricing: list[CostBomMissingPricing] = []
        pricing_requirements: list[CostBomPricingRequirement] = []

        has_workspace = pd.source_context.source_payload_type == "workspace_payload"
        for mod_code in active_modules:
            if mod_code in GATE_ONLY_MODULES:
                continue
            for key in MODULE_GEOMETRY_KEYS.get(mod_code, []):
                if key not in values:
                    missing_geometry.append(f"{mod_code}:{key}")

        costable_materials: list[CostBomCostableMaterial] = []
        for mat in aggregate.materials:
            if not include_material_in_composed_aggregate(
                material_code=mat.material_code,
                component_ref=mat.component_ref,
                provenance=mat.provenance,
                status=mat.status,
                source_template_code=mat.source_template_code,
            ):
                skipped.append(
                    CostBomSkippedItem(
                        item_type="material",
                        item_key=mat.material_code,
                        reason="non_canonical_logo_owner",
                        detail=(
                            "Excluded — mapping_only or non-canonical linked-logo ownership "
                            f"({mat.component_ref or 'unknown'})."
                        ),
                    )
                )
                continue
            if not _material_module_active(mat, active_modules, sold_led_subscopes, mount_decision):
                mod = mat.mini_module_code or DOSSIER_COMPONENT_TO_MODULE.get(mat.component_ref or "")
                skipped.append(
                    CostBomSkippedItem(
                        item_type="material",
                        item_key=mat.material_code,
                        reason="module_inactive",
                        detail=f"Excluded — module {mod or 'unknown'} inactive.",
                    )
                )
                continue

            resolved, geom_keys, variant_err = _resolve_material_code(mat.material_code, values)
            availability, unit_cost = _check_material_pricing(resolved, material_rates, variant_err)

            if variant_err == "missing_psu_watts_selection" and "sistem_led" in active_modules:
                missing_geometry.append("selected_psu_watts")
                pricing_requirements.append(
                    CostBomPricingRequirement(
                        requirement_code="psu_watt_variant",
                        description="LED PSU variant requires selected_psu_watts when sistem_led is active.",
                        module_codes=["sistem_led"],
                        geometry_keys=["selected_psu_watts"],
                        registry_codes=[TEMPLATE_PSU_CODE, *PSU_WATTS_TO_VARIANT_CODE.values()],
                    )
                )
            if variant_err:
                missing_pricing.append(
                    CostBomMissingPricing(
                        item_type="variant",
                        code=mat.material_code,
                        reason=variant_err,
                        module_code=mat.mini_module_code,
                    )
                )
            elif availability == "missing":
                missing_pricing.append(
                    CostBomMissingPricing(
                        item_type="material",
                        code=resolved,
                        reason="material_rate_missing_or_zero",
                        module_code=mat.mini_module_code,
                    )
                )

            costable_materials.append(
                CostBomCostableMaterial(
                    material_code=mat.material_code,
                    resolved_material_code=resolved if resolved != mat.material_code else None,
                    label=mat.label,
                    unit=mat.unit,
                    component_ref=mat.component_ref,
                    mini_module_code=mat.mini_module_code,
                    provenance=mat.provenance,
                    source_template_code=mat.source_template_code,
                    pricing_availability=availability if not variant_err else "variant_required",
                    unit_cost=unit_cost,
                    currency=material_currencies.get(resolved),
                    required_geometry_keys=geom_keys,
                )
            )

        costable_operations: list[CostBomCostableOperation] = []
        for op in aggregate.operations:
            if not include_operation_in_composed_aggregate(
                operation_code=op.operation_code,
                component_ref=op.component_ref,
                provenance=op.provenance,
                status=op.status,
                source_template_code=op.source_template_code,
            ):
                skipped.append(
                    CostBomSkippedItem(
                        item_type="operation",
                        item_key=op.operation_code,
                        reason="non_canonical_logo_owner",
                        detail=(
                            "Excluded — mapping_only or non-canonical linked-logo ownership "
                            f"({op.component_ref or 'unknown'})."
                        ),
                    )
                )
                continue
            if op.operation_code in GEOMETRY_GATE_OPERATIONS or op.mini_module_code in GATE_ONLY_MODULES:
                skipped.append(
                    CostBomSkippedItem(
                        item_type="operation",
                        item_key=op.operation_code,
                        reason="geometry_gate",
                        detail="Non-priced geometry readiness gate.",
                    )
                )
                continue
            if not op.priced:
                skipped.append(
                    CostBomSkippedItem(
                        item_type="operation",
                        item_key=op.operation_code,
                        reason="non_priced_internal",
                        detail="Operation marked non_priced — internal/future, not quoted.",
                    )
                )
                continue
            if not _operation_module_active(op, active_modules, sold_led_subscopes, mount_decision):
                skipped.append(
                    CostBomSkippedItem(
                        item_type="operation",
                        item_key=op.operation_code,
                        reason="module_inactive",
                        detail=f"Excluded — module {op.mini_module_code or 'unknown'} inactive.",
                    )
                )
                continue

            wc_availability = _check_workcenter_pricing(op.workcenter, workcenter_rates)
            ext_possible = is_external_service_possible(op.operation_code, op.workcenter)
            if wc_availability == "missing" and op.workcenter and not ext_possible:
                missing_pricing.append(
                    CostBomMissingPricing(
                        item_type="operation",
                        code=op.workcenter,
                        reason="workcenter_rate_missing_or_zero",
                        module_code=op.mini_module_code,
                    )
                )

            mod = op.mini_module_code or DOSSIER_COMPONENT_TO_MODULE.get(op.component_ref or "")
            geom_keys = MODULE_GEOMETRY_KEYS.get(mod or "", [])

            costable_operations.append(
                CostBomCostableOperation(
                    operation_code=op.operation_code,
                    label=op.label,
                    workcenter=op.workcenter,
                    formula_id=op.formula_id,
                    component_ref=op.component_ref,
                    mini_module_code=op.mini_module_code,
                    provenance=op.provenance,
                    source_template_code=op.source_template_code,
                    pricing_availability=wc_availability,
                    required_geometry_keys=geom_keys,
                )
            )

        module_coverage: dict[str, int] = {m: 0 for m in active_modules if m not in GATE_ONLY_MODULES}
        for item in costable_components:
            if item.mini_module_code in module_coverage:
                module_coverage[item.mini_module_code] += 1
        for item in costable_materials:
            if item.mini_module_code in module_coverage:
                module_coverage[item.mini_module_code] += 1
        for item in costable_operations:
            if item.mini_module_code in module_coverage:
                module_coverage[item.mini_module_code] += 1

        for mod_code, count in module_coverage.items():
            if count == 0 and mod_code in ALWAYS_COSTABLE_MODULES:
                warnings.append(f"ACTIVE_MODULE_NO_COST_LINES:{mod_code}")

        bom_status = self._resolve_bom_status(
            has_workspace=has_workspace,
            missing_geometry=missing_geometry,
            missing_pricing=missing_pricing,
            module_coverage=module_coverage,
            active_modules=active_modules,
        )

        (
            inventory_usage,
            missing_inventory_materials,
            unused_inventory_candidates,
            legacy_inventory_references,
            template_required_material_codes,
            template_optional_material_codes,
            inventory_pricing_blockers,
        ) = _build_inventory_alignment(
            template_code=pd.template_code,
            aggregate=aggregate,
            active_modules=active_modules,
            inventory_catalog=inventory_catalog,
            material_rates=material_rates,
            costable_materials=costable_materials,
            missing_pricing=missing_pricing,
            values=values,
            sold_led_subscopes=sold_led_subscopes,
            mount_decision=mount_decision,
        )

        (
            production_mode,
            externalization_requirements,
            reseller_requirements,
            subcontractable_operations,
            cost_line_classification,
            external_pricing_blockers,
        ) = _build_externalization_readiness(
            template_code=pd.template_code,
            aggregate=aggregate,
            active_modules=active_modules,
            costable_operations=costable_operations,
            costable_materials=costable_materials,
            workcenter_rates=workcenter_rates,
            external_selections=external_selections,
        )

        pricing_blockers = inventory_pricing_blockers + external_pricing_blockers
        if _aggregate_has_partial_linked_logo(aggregate):
            bom_status = "partial"
        elif pricing_blockers and bom_status == "ready":
            bom_status = "blocked"
        elif missing_inventory_materials and bom_status == "ready":
            bom_status = "blocked"

        if graph_cost_projection is not None:
            provenance_graph = CostBomProvenanceEntry(
                key="graph_cost_projection",
                source="product_aggregate_graph_cost_projection_service",
                detail=(
                    f"authority={graph_cost_projection.structural_authority} "
                    f"modules={','.join(graph_cost_projection.active_mini_module_codes)}"
                ),
            )
        else:
            provenance_graph = None

        provenance = [
            CostBomProvenanceEntry(
                key="product_definition_preview",
                source="product_definition_builder_service",
                detail=f"readiness={pd.validation.readiness_status} modules={len(active_modules)}",
            ),
            CostBomProvenanceEntry(
                key="product_aggregate",
                source="product_aggregate_service",
                detail=(
                    f"components={len(aggregate.components)} "
                    f"materials={len(aggregate.materials)} operations={len(aggregate.operations)}"
                ),
            ),
            CostBomProvenanceEntry(
                key="bom_expansion",
                source="aggregate_cost_bom_adapter",
                detail="Parent BOM not used as structural truth; aggregate-expanded only.",
            ),
            CostBomProvenanceEntry(
                key="inventory_externalization_guards",
                source="aggregate_cost_bom_adapter",
                detail="Step 7B.1 inventory alignment + externalization readiness hooks (read-only).",
            ),
        ]
        if provenance_graph is not None:
            provenance.insert(1, provenance_graph)
        if graph_cost_projection is not None and graph_cost_projection.compatibility_note:
            warnings.append(graph_cost_projection.compatibility_note)
        for blocker in graph_cost_projection.blockers if graph_cost_projection else []:
            if blocker.startswith("UPSTREAM_TRUTH_MISSING:"):
                warnings.append(blocker)

        legacy_note = (
            "Parent template row has minimal BOM (components_json=[]). "
            "Cost Engine v2 flat_legacy path is NOT used by this adapter."
        )

        return AggregateExpandedCostBom(
            template_code=pd.template_code,
            source_context=CostBomSourceContext(
                template_code=pd.template_code,
                workspace_id=pd.source_context.workspace_id,
                quote_id=pd.source_context.quote_id,
                source_payload_type=pd.source_context.source_payload_type,
                uses_parent_bom_as_structural_truth=False,
                legacy_parent_bom_note=legacy_note,
            ),
            bom_status=bom_status,
            active_modules=active_module_refs,
            inactive_modules=inactive_module_refs,
            costable_components=costable_components,
            costable_materials=costable_materials,
            costable_operations=costable_operations,
            skipped_items=skipped,
            pricing_requirements=pricing_requirements,
            missing_pricing=missing_pricing,
            missing_geometry=sorted(set(missing_geometry)),
            warnings=warnings,
            provenance=provenance,
            notes=[
                "Read-only aggregate-expanded cost BOM preview — Step 7B.1.",
                "No final price, no quote persistence, no silent zero fallback.",
                "Inventory alignment and externalization hooks are advisory — Step 9 routing not active.",
            ],
            production_mode=production_mode,
            inventory_usage=inventory_usage,
            missing_inventory_materials=missing_inventory_materials,
            unused_inventory_candidates=unused_inventory_candidates,
            legacy_inventory_references=legacy_inventory_references,
            template_required_material_codes=template_required_material_codes,
            template_optional_material_codes=template_optional_material_codes,
            pricing_blockers=pricing_blockers,
            externalization_requirements=externalization_requirements,
            reseller_requirements=reseller_requirements,
            subcontractable_operations=subcontractable_operations,
            cost_line_classification=cost_line_classification,
            graph_cost_projection=graph_cost_projection,
        )

    def _resolve_bom_status(
        self,
        *,
        has_workspace: bool,
        missing_geometry: list[str],
        missing_pricing: list[CostBomMissingPricing],
        module_coverage: dict[str, int],
        active_modules: set[str],
    ) -> BomStatus:
        uncovered = [
            m
            for m, count in module_coverage.items()
            if count == 0 and m in ALWAYS_COSTABLE_MODULES and m in active_modules
        ]
        if missing_pricing or uncovered:
            return "blocked"
        critical_missing = [g for g in missing_geometry if any(k in g for k in CRITICAL_GEOMETRY_FOR_READY)]
        if critical_missing and has_workspace:
            return "blocked"
        if not has_workspace or missing_geometry:
            return "partial"
        return "ready"


class AggregateCostBomBuilderService:
    """Orchestrates PD + Aggregate + registry checks for cost BOM preview."""

    def __init__(self, db) -> None:
        self._db = db
        self._pd_builder = None
        self._aggregate_svc = None
        self._adapter = AggregateCostBomAdapter()

    async def build_preview(
        self,
        template_code: str,
        *,
        workspace_id: str | None = None,
        quote_input: dict[str, Any] | None = None,
    ) -> AggregateExpandedCostBom | None:
        from services.product_aggregate_service import ProductAggregateService
        from services.product_definition_builder_service import ProductDefinitionBuilderService

        pd_builder = ProductDefinitionBuilderService(self._db)
        aggregate_svc = ProductAggregateService(self._db)

        pd = await pd_builder.build_preview(template_code, workspace_id=workspace_id)
        if pd is None:
            return None
        if workspace_id:
            aggregate = await aggregate_svc.build_for_workspace(template_code, workspace_id)
        else:
            aggregate = await aggregate_svc.build(template_code)
        if aggregate is None:
            return None

        material_rates: dict[str, float] = {}
        workcenter_rates: dict[str, float] = {}
        material_currencies: dict[str, str] = {}
        inventory_catalog: dict[str, dict] = {}
        try:
            from sqlalchemy import select

            from models.inventory_materials import Inventory_materials
            from services.inventory_materials_admin_service import load_material_cost_dict, load_material_pricing_dict
            from services.workcenter_rates_service import load_workcenter_rate_dict

            material_rates = await load_material_cost_dict(self._db)
            pricing_dict = await load_material_pricing_dict(self._db)
            material_currencies = {
                code: str(row.get("currency") or "RON").strip().upper()
                for code, row in pricing_dict.items()
            }
            workcenter_rates = await load_workcenter_rate_dict(self._db)

            inv_rows = (
                await self._db.execute(select(Inventory_materials))
            ).scalars().all()
            for row in inv_rows:
                inventory_catalog[row.code] = {
                    "status": row.status,
                    "unit_cost": float(row.unit_cost) if row.unit_cost is not None else None,
                }
        except Exception:
            pass

        return self._adapter.build(
            product_definition=pd,
            aggregate=aggregate,
            quote_input=quote_input,
            material_rates=material_rates,
            workcenter_rates=workcenter_rates,
            material_currencies=material_currencies,
            inventory_catalog=inventory_catalog,
        )
