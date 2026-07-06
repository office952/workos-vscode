"""Read-only Intake V6 modular form contract — derived from mini-module registry."""

from __future__ import annotations

from schemas.intake_v6_modular_form import (
    ActivationKind,
    IntakeFormFieldBinding,
    IntakeModuleFormSection,
    IntakeV6ModularFormContract,
    IntakeV6ModularFormContractSummary,
    TriggerFieldAlignment,
)
from schemas.mini_module_registry import REGISTRY_VERSION
from services.form_system_contract_backbone_service import build_form_system_contract_map
from services.mini_module_registry_service import MiniModuleRegistryService, get_mini_module_registry_service

PILOT_TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"

_FINISH = "finish_setup"
_GEOM = "quote_geometry"
_CLIENT = "client"
_SVG = "svg_source"

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
        workspace_path=f"{_CLIENT}.width_mm",
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
        workspace_path=f"{_CLIENT}.height_mm",
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
        workspace_path=f"{_GEOM}.letter_face_area_m2",
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
}


class IntakeV6ModularFormContractService:
    """Build read-only form contract from mini-module registry + volumetric bindings."""

    def __init__(self, registry: MiniModuleRegistryService | None = None) -> None:
        self._registry = registry or get_mini_module_registry_service()

    def get_backbone_section_for_template(self, template_code: str) -> dict | None:
        backbone = build_form_system_contract_map(template_code)
        root = backbone.get("root") if isinstance(backbone.get("root"), dict) else {}
        if root.get("allowed") is not True:
            return backbone
        if root.get("canonical_code") != PILOT_TEMPLATE:
            return None
        return backbone

    def get_for_template(self, template_code: str) -> IntakeV6ModularFormContract | None:
        backbone = self.get_backbone_section_for_template(template_code)
        if backbone is None:
            return None
        root = backbone.get("root") if isinstance(backbone.get("root"), dict) else {}
        if root.get("allowed") is not True:
            return None
        canonical_template_code = str(root.get("canonical_code") or "")
        if canonical_template_code != PILOT_TEMPLATE:
            return None
        registry_response = self._registry.get_by_template(canonical_template_code)
        active_modules = [
            m for m in registry_response.modules if m.operational_status == "ACTIVE_OPERATIONAL"
        ]

        modules: list[IntakeModuleFormSection] = []
        for mod in active_modules:
            required_fields = [
                f.canonical_key
                for f in VOLUMETRIC_FIELD_BINDINGS
                if mod.module_code in f.module_codes and f.required and f.field_role != "derived_quote_input"
            ]
            optional_fields = [
                f.canonical_key
                for f in VOLUMETRIC_FIELD_BINDINGS
                if mod.module_code in f.module_codes and not f.required and f.field_role != "derived_quote_input"
            ]
            activation_kind = _MODULE_ACTIVATION_KIND.get(mod.module_code, "conditional_gate")
            trigger_fields = [r.trigger_field for r in mod.activation_rules if r.trigger_field]
            if mod.module_code == "structura_suport":
                trigger_fields = ["mounting_system"]

            valid_when: list[str] = []
            invalid_when: list[str] = []
            if mod.module_code == "structura_suport":
                valid_when = ["mounting_system in (steel_bars, aluminum_bars)"]
                invalid_when = ["mounting_system=direct_wall without premount intent"]
            elif mod.module_code == "sistem_led":
                valid_when = ["lighting_system_type != none OR illuminated=true"]
            elif mod.module_code == "finisaje":
                valid_when = ["mounting_template_enabled optional"]

            modules.append(
                IntakeModuleFormSection(
                    module_code=mod.module_code,
                    module_name=mod.module_name,
                    operational_status=mod.operational_status,
                    activation_kind=activation_kind,
                    intake_trigger_fields=trigger_fields,
                    consumed_form_fields=mod.consumed_form_fields,
                    required_form_fields=sorted(set(required_fields)),
                    optional_form_fields=sorted(set(optional_fields)),
                    product_definition_outputs=mod.product_definition_outputs,
                    valid_when=valid_when,
                    invalid_when=invalid_when,
                    warnings=mod.warnings,
                )
            )

        warnings = list(registry_response.summary.warnings)
        warnings.append(
            "TRIGGER_FIELD_MISMATCH for structura_suport is documented — canonical intake trigger is mounting_system."
        )

        return IntakeV6ModularFormContract(
            summary=IntakeV6ModularFormContractSummary(
                template_code=canonical_template_code,
                registry_version=REGISTRY_VERSION,
                active_module_count=len(active_modules),
                field_binding_count=len(VOLUMETRIC_FIELD_BINDINGS),
                warnings=warnings,
            ),
            modules=modules,
            field_bindings=VOLUMETRIC_FIELD_BINDINGS,
            form_system_backbone=backbone,
            trigger_alignments=TRIGGER_ALIGNMENTS,
            valid_combinations=VALID_COMBINATIONS,
            invalid_combinations=INVALID_COMBINATIONS,
            orphan_fields_audit=ORPHAN_FIELDS_AUDIT,
            notes=[
                "This contract is read-only. Does not mutate workspace payload.",
                "Pricing, ProductDefinition builder, and Cost Engine are out of scope for Step 5.",
                "Step 6 consumes field_bindings.product_definition_keys.",
            ],
        )


_service: IntakeV6ModularFormContractService | None = None


def get_intake_v6_modular_form_contract_service() -> IntakeV6ModularFormContractService:
    global _service
    if _service is None:
        _service = IntakeV6ModularFormContractService()
    return _service
