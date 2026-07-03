"""Shared pilot contract seed for Intake V6 modular form and ProductDefinition preview."""

from __future__ import annotations

from dataclasses import dataclass

from schemas.intake_v6_modular_form import (
    ActivationKind,
    IntakeFormFieldBinding,
    IntakeModuleDownstreamLinkage,
    IntakeModuleFormSection,
    TriggerFieldAlignment,
)
from schemas.mini_module_registry import REGISTRY_VERSION
from services.mini_module_registry_service import MiniModuleRegistryService
from services.template_architecture_scope import (
    VOLUMETRIC_LOGO_TEMPLATE_CODE,
    VOLUMETRIC_V2_TEMPLATE_CODE,
    resolve_runtime_template_code,
)

PILOT_TEMPLATE = VOLUMETRIC_V2_TEMPLATE_CODE
PILOT_LOGO_TEMPLATE = VOLUMETRIC_LOGO_TEMPLATE_CODE

_FINISH = "finish_setup"
_GEOM = "quote_geometry"
_CLIENT = "client"
_SVG = "svg_source"


@dataclass(frozen=True)
class IntakeV6PilotContractSeed:
    template_code: str
    registry_version: str
    warnings: list[str]
    field_bindings: list[IntakeFormFieldBinding]
    modules: list[IntakeModuleFormSection]
    downstream_linkages: list[IntakeModuleDownstreamLinkage]
    trigger_alignments: list[TriggerFieldAlignment]
    valid_combinations: list[str]
    invalid_combinations: list[str]
    orphan_fields_audit: list[str]


VOLUMETRIC_FIELD_BINDINGS: list[IntakeFormFieldBinding] = [
    IntakeFormFieldBinding(
        canonical_key="vector_file",
        workspace_path=f"{_SVG}.file_name",
        label_ro="Fișier SVG",
        required=True,
        field_role="geometry_input",
        module_codes=["geometry_svg"],
        product_definition_keys=["vector_file"],
        aggregate_trace=["operations.parent svg_geometry_analysis"],
        cost_engine_step="Step 7 readiness gate",
    ),
    IntakeFormFieldBinding(
        canonical_key="width_mm",
        workspace_path=f"{_GEOM}.width_mm",
        label_ro="Lățime totală",
        required=True,
        field_role="geometry_input",
        module_codes=["geometry_svg", "debitare_fata", "structura_suport"],
        product_definition_keys=["dimensions.width_mm"],
        aggregate_trace=["form_contract.required_quote_input_keys"],
        cost_engine_step="Step 7",
    ),
    IntakeFormFieldBinding(
        canonical_key="height_mm",
        workspace_path=f"{_GEOM}.height_mm",
        label_ro="Înălțime totală",
        required=True,
        field_role="geometry_input",
        module_codes=["geometry_svg"],
        product_definition_keys=["dimensions.height_mm"],
        aggregate_trace=["form_contract.required_quote_input_keys"],
    ),
    IntakeFormFieldBinding(
        canonical_key="letter_count",
        workspace_path=f"{_GEOM}.letter_count",
        label_ro="Număr litere",
        required=True,
        field_role="geometry_input",
        module_codes=["geometry_svg"],
        product_definition_keys=["quantity"],
        aggregate_trace=["form_contract.required_quote_input_keys"],
    ),
    IntakeFormFieldBinding(
        canonical_key="letter_perimeter_m",
        workspace_path=f"{_GEOM}.letter_perimeter_m",
        label_ro="Perimetru litere",
        required=True,
        field_role="geometry_input",
        module_codes=["geometry_svg", "modelare_cant", "debitare_fata"],
        product_definition_keys=["letter_perimeter_m"],
        aggregate_trace=["form_contract.required_quote_input_keys"],
        cost_engine_step="Step 7",
    ),
    IntakeFormFieldBinding(
        canonical_key="letter_face_area_m2",
        workspace_path=f"{_GEOM}.face_area_m2",
        label_ro="Suprafață față",
        required=True,
        field_role="geometry_input",
        module_codes=["geometry_svg", "debitare_fata", "debitare_spate"],
        product_definition_keys=["letter_face_area_m2"],
        aggregate_trace=["form_contract.required_quote_input_keys"],
        cost_engine_step="Step 7",
    ),
    IntakeFormFieldBinding(
        canonical_key="face_finish_type",
        workspace_path=f"{_FINISH}.face_finish_type",
        label_ro="Finisaj față",
        required=True,
        field_role="module_configuration",
        module_codes=["debitare_fata"],
        product_definition_keys=["layers[].components.comp_face_litere"],
        aggregate_trace=["components.comp_face_litere"],
        cost_engine_step="Step 7 face_cnc_cut / vinyl",
    ),
    IntakeFormFieldBinding(
        canonical_key="return_depth_mm",
        workspace_path=f"{_FINISH}.return_depth_mm",
        label_ro="Adâncime cant",
        required=True,
        field_role="module_configuration",
        module_codes=["modelare_cant"],
        product_definition_keys=["return_depth_mm"],
        aggregate_trace=["modules.required TPL-VOLUM-ALUMINIU_v1"],
        cost_engine_step="Step 7 return_profile_linear_meter",
    ),
    IntakeFormFieldBinding(
        canonical_key="return_finish_type",
        workspace_path=f"{_FINISH}.return_finish_type",
        label_ro="Finisaj cant",
        required=True,
        field_role="module_configuration",
        module_codes=["modelare_cant"],
        product_definition_keys=["return_finish_type"],
        cost_engine_step="Step 7 RAL vs Oracal gate",
    ),
    IntakeFormFieldBinding(
        canonical_key="volum_aluminum_module_template_code",
        workspace_path=f"{_FINISH}.volum_aluminum_module_template_code",
        label_ro="Modul volum aluminiu",
        required=True,
        field_role="module_activation",
        module_codes=["modelare_cant"],
        product_definition_keys=["linked_modules.TPL-VOLUM-ALUMINIU_v1"],
        aggregate_trace=["modules.required"],
        notes=["Module link trigger field — matches Intake UI."],
    ),
    IntakeFormFieldBinding(
        canonical_key="backing_mode",
        workspace_path=f"{_FINISH}.backing_mode",
        label_ro="Mod spate",
        required=True,
        field_role="module_configuration",
        module_codes=["debitare_spate"],
        product_definition_keys=["backing_mode"],
        aggregate_trace=["components.comp_spate_litere"],
    ),
    IntakeFormFieldBinding(
        canonical_key="back_bevel_enabled",
        workspace_path=f"{_FINISH}.back_bevel_enabled",
        label_ro="Bevel spate",
        required=False,
        field_role="module_configuration",
        module_codes=["debitare_spate"],
        product_definition_keys=["back_bevel_enabled"],
    ),
    IntakeFormFieldBinding(
        canonical_key="lighting_system_type",
        workspace_path=f"{_FINISH}.lighting_system_type",
        label_ro="Tip iluminare",
        required=False,
        field_role="module_activation",
        module_codes=["sistem_led"],
        product_definition_keys=["lighting_system_type"],
        aggregate_trace=["components.comp_led_litere"],
        cost_engine_step="Step 7 led_install_letters",
    ),
    IntakeFormFieldBinding(
        canonical_key="led_module_count",
        workspace_path=f"{_FINISH}.led_module_count",
        label_ro="Număr module LED",
        required=False,
        field_role="module_configuration",
        module_codes=["sistem_led"],
        product_definition_keys=["led_module_count"],
        cost_engine_step="Step 7",
    ),
    IntakeFormFieldBinding(
        canonical_key="selected_psu_watts",
        workspace_path=f"{_FINISH}.selected_psu_watts",
        label_ro="PSU selectat",
        required=False,
        field_role="module_configuration",
        module_codes=["sistem_led"],
        product_definition_keys=["selected_psu_watts"],
    ),
    IntakeFormFieldBinding(
        canonical_key="mounting_system",
        workspace_path=f"{_FINISH}.mounting_system",
        label_ro="Sistem montaj",
        required=True,
        field_role="module_activation",
        module_codes=["structura_suport", "finisaje"],
        product_definition_keys=["mounting_system"],
        aggregate_trace=["modules.optional trigger candidate"],
        notes=["Canonical Intake field for premount structure activation."],
    ),
    IntakeFormFieldBinding(
        canonical_key="mounting_template_enabled",
        workspace_path=f"{_FINISH}.mounting_template_enabled",
        label_ro="Șablon montaj activ",
        required=False,
        field_role="module_activation",
        module_codes=["finisaje"],
        product_definition_keys=["mounting_template_enabled"],
        aggregate_trace=["materials.parent MAT-SABLON-*"],
    ),
    IntakeFormFieldBinding(
        canonical_key="mounting_template_area_m2",
        workspace_path=f"{_FINISH}.mounting_template_area_m2",
        label_ro="Suprafață șablon montaj",
        required=False,
        field_role="module_configuration",
        module_codes=["finisaje"],
        product_definition_keys=["mounting_template_area_m2"],
        cost_engine_step="Step 7 mounting_template_area",
    ),
    IntakeFormFieldBinding(
        canonical_key="letter_group_finishes",
        workspace_path=f"{_FINISH}.letter_group_finishes",
        label_ro="Finisaje pe grup litere",
        required=False,
        field_role="module_configuration",
        module_codes=["debitare_fata", "modelare_cant", "finisaje"],
        product_definition_keys=["letter_group_finishes"],
    ),
    IntakeFormFieldBinding(
        canonical_key="metal_support_required",
        workspace_path="quote_input.metal_support_required",
        label_ro="Suport metal derivat",
        required=False,
        field_role="derived_quote_input",
        module_codes=["structura_suport"],
        product_definition_keys=["metal_support_required"],
        derived_from=f"{_FINISH}.mounting_system",
        derivation_rule="mounting_system in ('steel_bars','aluminum_bars')",
        notes=[
            "Not a finish_setup control — derived at quote adapter.",
            "Module link still uses trigger_field metal_support_required (DB).",
        ],
    ),
    IntakeFormFieldBinding(
        canonical_key="premount_bar_length_ml",
        workspace_path="quote_input.premount_bar_length_ml",
        label_ro="Lungime bare premontaj",
        required=False,
        field_role="derived_quote_input",
        module_codes=["structura_suport"],
        derived_from="quote_input.width_mm",
        derivation_rule="Set when structura_suport active",
        cost_engine_step="Step 7 premount_bar_linear_meter",
    ),
    IntakeFormFieldBinding(
        canonical_key="bar_material",
        workspace_path="quote_input.bar_material",
        label_ro="Material bare",
        required=False,
        field_role="derived_quote_input",
        module_codes=["structura_suport"],
        derived_from=f"{_FINISH}.mounting_system",
        derivation_rule="steel_bars -> steel; aluminum_bars -> aluminum",
    ),
]

LOGO_FIELD_BINDINGS: list[IntakeFormFieldBinding] = [
    IntakeFormFieldBinding(
        canonical_key="vector_file",
        workspace_path=f"{_SVG}.file_name",
        label_ro="Fișier SVG logo",
        required=True,
        field_role="geometry_input",
        module_codes=["logo_geometry_svg"],
        product_definition_keys=["vector_file"],
        aggregate_trace=["operations.parent svg_geometry_analysis"],
    ),
    IntakeFormFieldBinding(
        canonical_key="svg_area_m2",
        workspace_path=f"{_GEOM}.artwork_area_m2",
        label_ro="Suprafață logo/artwork",
        required=True,
        field_role="geometry_input",
        module_codes=["logo_geometry_svg", "logo_face", "logo_back"],
        product_definition_keys=["logo_artwork_area_m2"],
        aggregate_trace=["form_contract.required_quote_input_keys"],
    ),
    IntakeFormFieldBinding(
        canonical_key="svg_bbox",
        workspace_path=f"{_GEOM}.artwork_boxes",
        label_ro="Bounding boxes logo",
        required=True,
        field_role="geometry_input",
        module_codes=["logo_geometry_svg", "logo_face"],
        product_definition_keys=["logo_artwork_boxes"],
    ),
    IntakeFormFieldBinding(
        canonical_key="svg_perimeter_ml",
        workspace_path=f"{_GEOM}.artwork_return_perimeter_ml",
        label_ro="Perimetru logo pentru cant",
        required=True,
        field_role="geometry_input",
        module_codes=["logo_return"],
        product_definition_keys=["logo_return_perimeter_ml"],
    ),
    IntakeFormFieldBinding(
        canonical_key="return_depth_mm",
        workspace_path=f"{_FINISH}.return_depth_mm",
        label_ro="Adâncime logo volumetric",
        required=True,
        field_role="module_configuration",
        module_codes=["logo_return"],
        product_definition_keys=["logo_return_depth_mm"],
    ),
    IntakeFormFieldBinding(
        canonical_key="return_finish_type",
        workspace_path=f"{_FINISH}.return_finish_type",
        label_ro="Finisaj cant logo",
        required=True,
        field_role="module_configuration",
        module_codes=["logo_return"],
        product_definition_keys=["logo_return_finish_type"],
    ),
    IntakeFormFieldBinding(
        canonical_key="logo_artwork_mode",
        workspace_path=f"{_FINISH}.artwork_finishes",
        label_ro="Mod artwork/logo",
        required=True,
        field_role="module_configuration",
        module_codes=["logo_face", "logo_finish"],
        product_definition_keys=["logo_artwork_mode"],
        notes=["Current source is artwork_finishes until dedicated logo form fields exist."],
    ),
    IntakeFormFieldBinding(
        canonical_key="logo_face_material",
        workspace_path=f"{_FINISH}.artwork_finishes",
        label_ro="Material față logo",
        required=False,
        field_role="module_configuration",
        module_codes=["logo_face"],
        product_definition_keys=["logo_face_material"],
    ),
    IntakeFormFieldBinding(
        canonical_key="logo_backing_material",
        workspace_path=f"{_FINISH}.artwork_finishes",
        label_ro="Material spate logo",
        required=False,
        field_role="module_configuration",
        module_codes=["logo_back"],
        product_definition_keys=["logo_backing_material"],
    ),
    IntakeFormFieldBinding(
        canonical_key="logo_lighting_mode",
        workspace_path=f"{_FINISH}.emblem_lighting_mode",
        label_ro="Mod iluminare logo",
        required=False,
        field_role="module_activation",
        module_codes=["logo_lighting"],
        product_definition_keys=["logo_lighting_mode"],
    ),
    IntakeFormFieldBinding(
        canonical_key="emblem_led_module_count",
        workspace_path=f"{_FINISH}.emblem_led_module_count",
        label_ro="Număr module LED logo",
        required=False,
        field_role="module_configuration",
        module_codes=["logo_lighting"],
        product_definition_keys=["emblem_led_module_count"],
    ),
    IntakeFormFieldBinding(
        canonical_key="selected_psu_watts",
        workspace_path=f"{_FINISH}.selected_psu_watts",
        label_ro="PSU logo selectat",
        required=False,
        field_role="module_configuration",
        module_codes=["logo_lighting"],
        product_definition_keys=["selected_psu_watts"],
    ),
    IntakeFormFieldBinding(
        canonical_key="mounting_system",
        workspace_path=f"{_FINISH}.mounting_system",
        label_ro="Sistem montaj logo",
        required=True,
        field_role="module_activation",
        module_codes=["logo_mounting"],
        product_definition_keys=["mounting_system"],
    ),
    IntakeFormFieldBinding(
        canonical_key="mounting_template_enabled",
        workspace_path=f"{_FINISH}.mounting_template_enabled",
        label_ro="Șablon montaj logo",
        required=False,
        field_role="module_activation",
        module_codes=["logo_mounting"],
        product_definition_keys=["mounting_template_enabled"],
    ),
]

TRIGGER_ALIGNMENTS: list[TriggerFieldAlignment] = [
    TriggerFieldAlignment(
        module_code="structura_suport",
        module_link_trigger_field="metal_support_required",
        canonical_intake_field=f"{_FINISH}.mounting_system",
        derived_quote_input_key="metal_support_required",
        derivation_rule="mounting_system in ('steel_bars','aluminum_bars')",
        warning_code="TRIGGER_FIELD_MISMATCH",
        backwards_compatible=True,
        resolution_owner_step=5,
        notes=[
            "Intake operator selects mounting_system; commercial quote adapter derives metal_support_required.",
            "ProductAggregate warning remains until module link trigger_field is migrated (future DB step).",
        ],
    ),
]

VALID_COMBINATIONS = [
    "geometry_svg + debitare_fata + modelare_cant + debitare_spate + sistem_led (illuminated) + finisaje",
    "structura_suport activates when mounting_system is steel_bars or aluminum_bars",
    "finisaje sablon materials when mounting_template_enabled=true",
    "modelare_cant always required for volumetric letters v2 (required_module link)",
]

INVALID_COMBINATIONS = [
    "structura_suport without steel_bars/aluminum_bars mounting_system",
    "sistem_led with lighting_system_type=none while illuminated product expected",
    "Any finish_setup field without module_codes binding (orphan) — must be FUTURE or removed",
]

ORPHAN_FIELDS_AUDIT = [
    "finish_setup.illuminated — UI gate only; maps to lighting_system_type indirectly",
    "finish_setup.commercial_inputs — quote commercial layer, not product module (READONLY_EXPLANATORY)",
    "finish_setup.artwork_complexity_decisions — artwork path, FUTURE_RESERVED_STEP_6 for emblem modules",
    "finish_setup.emblem_lighting_mode — FUTURE electrica_logo OPEN QUESTION",
]

_MODULE_ACTIVATION_KIND: dict[str, ActivationKind] = {
    "geometry_svg": "always_on",
    "modelare_cant": "required_module",
    "structura_suport": "optional_addon",
    "debitare_fata": "always_on",
    "debitare_spate": "always_on",
    "sistem_led": "conditional_gate",
    "finisaje": "conditional_gate",
    "logo_geometry_svg": "always_on",
    "logo_face": "required_module",
    "logo_return": "required_module",
    "logo_back": "required_module",
    "logo_lighting": "conditional_gate",
    "logo_finish": "conditional_gate",
    "logo_mounting": "conditional_gate",
}

LOGO_VALID_COMBINATIONS = [
    "logo_geometry_svg + logo_face + logo_return + logo_back pentru logo_only volumetric",
    "logo_lighting active doar cand logo_lighting_mode necesita iluminare",
    "logo_finish diferențiază print/vinyl/laminare fără a forța CNC plexi",
    "logo_mounting reutilizează mounting_system și mounting_template_enabled",
]

LOGO_INVALID_COMBINATIONS = [
    "logo_return fără return_depth_mm",
    "logo_mounting fără mounting_system",
    "logo_lighting activ cu logo_lighting_mode=excluded",
]

LOGO_ORPHAN_FIELDS_AUDIT = [
    "finish_setup.artwork_finishes — reused as temporary logo face/print configuration source",
    "finish_setup.emblem_lighting_mode — reused as logo lighting gate until dedicated logo form fields exist",
    "finish_setup.mounting_template_material_type — available in workspace, not yet bound as dedicated logo field",
]


def _build_downstream_linkage(module) -> IntakeModuleDownstreamLinkage:
    has_tasks = bool(module.task_preview_outputs)
    has_operations = bool(module.required_operation_roles)
    has_inventory = bool(module.required_material_roles)

    workcenter_status = "partial" if has_operations else "not_applicable"
    machine_status = "future" if has_operations else "not_applicable"
    employee_status = "post_materialization_only" if has_tasks else "not_applicable"

    notes: list[str] = []
    if has_inventory:
        notes.append("Inventory linkage uses material roles and material registry codes.")
    if module.cost_engine_inputs:
        notes.append("Pricing/internal cost linkage uses cost_engine_inputs and pricing registry rules.")
    if has_operations:
        notes.append("Workcenter and machine routing remain partial until operation roles resolve into operational tasks.")
    if has_tasks:
        notes.append("Employee assignment becomes authoritative only after Step 9 materialization creates operational_tasks.")

    return IntakeModuleDownstreamLinkage(
        module_code=module.module_code,
        inventory_material_roles=list(module.required_material_roles),
        pricing_inputs=list(module.cost_engine_inputs),
        quote_snapshot_outputs=list(module.quote_snapshot_outputs),
        order_snapshot_outputs=list(module.order_snapshot_outputs),
        execution_task_outputs=list(module.task_preview_outputs),
        workcenter_routing_status=workcenter_status,
        machine_linkage_status=machine_status,
        employee_assignment_status=employee_status,
        linkage_notes=notes,
    )


def build_pilot_contract_seed(
    registry: MiniModuleRegistryService,
    template_code: str,
) -> IntakeV6PilotContractSeed | None:
    runtime_template_code = resolve_runtime_template_code(template_code)
    if runtime_template_code == PILOT_TEMPLATE.upper():
        resolved_template = PILOT_TEMPLATE
        field_bindings = VOLUMETRIC_FIELD_BINDINGS
        valid_combinations = VALID_COMBINATIONS
        invalid_combinations = INVALID_COMBINATIONS
        orphan_fields_audit = ORPHAN_FIELDS_AUDIT
        seed_warnings: list[str] = []
    elif runtime_template_code == PILOT_LOGO_TEMPLATE.upper():
        resolved_template = PILOT_LOGO_TEMPLATE
        field_bindings = LOGO_FIELD_BINDINGS
        valid_combinations = LOGO_VALID_COMBINATIONS
        invalid_combinations = LOGO_INVALID_COMBINATIONS
        orphan_fields_audit = LOGO_ORPHAN_FIELDS_AUDIT
        seed_warnings = [
            "Preview-supported only: logo modular form contract exists before DB-backed ProductAggregate/ProductDefinition rows.",
            "Current logo bindings reuse existing artwork/logo review and mounting fields; no new UI fields introduced.",
        ]
    else:
        return None

    registry_response = registry.get_by_template(resolved_template)
    active_modules = [
        module for module in registry_response.modules if module.operational_status == "ACTIVE_OPERATIONAL"
    ]

    modules: list[IntakeModuleFormSection] = []
    downstream_linkages: list[IntakeModuleDownstreamLinkage] = []
    for module in active_modules:
        required_fields = [
            binding.canonical_key
            for binding in field_bindings
            if module.module_code in binding.module_codes and binding.required and binding.field_role != "derived_quote_input"
        ]
        optional_fields = [
            binding.canonical_key
            for binding in field_bindings
            if module.module_code in binding.module_codes and not binding.required and binding.field_role != "derived_quote_input"
        ]
        activation_kind = _MODULE_ACTIVATION_KIND.get(module.module_code, "conditional_gate")
        trigger_fields = [rule.trigger_field for rule in module.activation_rules if rule.trigger_field]
        if module.module_code == "structura_suport":
            trigger_fields = ["mounting_system"]

        valid_when: list[str] = []
        invalid_when: list[str] = []
        if module.module_code == "structura_suport":
            valid_when = ["mounting_system in (steel_bars, aluminum_bars)"]
            invalid_when = ["mounting_system=direct_wall without premount intent"]
        elif module.module_code == "sistem_led":
            valid_when = ["lighting_system_type != none OR illuminated=true"]
        elif module.module_code == "finisaje":
            valid_when = ["mounting_template_enabled optional"]
        elif module.module_code == "logo_lighting":
            valid_when = ["logo_lighting_mode != excluded"]
            invalid_when = ["logo_lighting_mode=excluded with logo_lighting selected"]
        elif module.module_code == "logo_mounting":
            valid_when = ["mounting_system provided"]
        elif module.module_code == "logo_finish":
            valid_when = ["logo_artwork_mode differentiates print/vinyl/laminate path"]

        modules.append(
            IntakeModuleFormSection(
                module_code=module.module_code,
                module_name=module.module_name,
                operational_status=module.operational_status,
                activation_kind=activation_kind,
                intake_trigger_fields=trigger_fields,
                consumed_form_fields=module.consumed_form_fields,
                required_form_fields=sorted(set(required_fields)),
                optional_form_fields=sorted(set(optional_fields)),
                product_definition_outputs=module.product_definition_outputs,
                valid_when=valid_when,
                invalid_when=invalid_when,
                warnings=module.warnings,
            )
        )
        downstream_linkages.append(_build_downstream_linkage(module))

    warnings = list(registry_response.summary.warnings)
    warnings.extend(seed_warnings)
    trigger_alignments = list(TRIGGER_ALIGNMENTS)
    if resolved_template == PILOT_TEMPLATE:
        warnings.append(
            "TRIGGER_FIELD_MISMATCH for structura_suport is documented — canonical intake trigger is mounting_system."
        )
    else:
        trigger_alignments = []

    return IntakeV6PilotContractSeed(
        template_code=resolved_template,
        registry_version=REGISTRY_VERSION,
        warnings=warnings,
        field_bindings=field_bindings,
        modules=modules,
        downstream_linkages=downstream_linkages,
        trigger_alignments=trigger_alignments,
        valid_combinations=valid_combinations,
        invalid_combinations=invalid_combinations,
        orphan_fields_audit=orphan_fields_audit,
    )