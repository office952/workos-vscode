"""Read-only Intake V6 modular form contract — derived from mini-module registry."""

from __future__ import annotations

from schemas.intake_v6_modular_form import (
    ActivationKind,
    FullProductCompositionSpec,
    IntakeFormFieldBinding,
    IntakeFormOption,
    IntakeModuleFormSection,
    IntakeRenderSection,
    IntakeVisibilityRule,
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

# Scoped runtime authority — Letters pilot generic field writes (unchanged in Build 2).
_LETTERS_RUNTIME_AUTHORITY_SCOPE = "selected_sections:finisaje_fields,iluminare,montaj_template"
_LETTERS_RUNTIME_AUTHORITY_NOTE = (
    "runtime_authority=false; composition_authority=true; "
    "runtime_authority_scope=selected_sections:finisaje_fields,iluminare,montaj_template — "
    "Product System owns full-product Review tab order + section registry; "
    "generic field writes remain allowlisted; letter-group/montaj specialized adapters preserve golden UI; "
    "subset activation enabled for FACE / CANT / FACE+CANT; "
    "inactive modules are silent; FACE+CANT interface owns adhesive/bonding once."
)

_FACE_CANT_INTERFACE_CANDIDATE = {
    "interface_id": "RETURN_FACE_BONDING",
    "components": ["FACE", "CANT"],
    "material_code": "MAT-ADEZIV-CANT-LITERE",
    "operation_codes": ["RETURN_PROFILE_FACE_BONDING", "return_face_bonding"],
    "current_owner": "modelare_cant",
    "target_owner": "interface:FACE+CANT",
    "owner": "interface_face_cant",
    "requires": ["FACE", "RETURN-CANT"],
    "build2_behavior": "full_product_output_unchanged",
    "build3_isolation": "cant_only_and_face_only_silence_adhesive_and_bonding",
    "build3_activation": "face_plus_cant_emits_adhesive_exactly_once",
}

_OPTION_LABELS_RO: dict[str, dict[str, str]] = {
    "face_finish_type": {
        "none": "Fără finisaj",
        "oracal_651": "Oracal 651",
        "oracal_641": "Oracal 641",
        "oracal_8500": "Oracal 8500",
        "printed_vinyl": "Vinil printat",
        "printed_laminated_vinyl": "Vinil printat laminat",
        "print_laminate": "Print + laminat",
        "colored_plexiglas": "Plexiglas colorat",
        "plexiglas_clear": "Plexiglas transparent",
    },
    "return_finish_type": {
        "white_aluminum": "Aluminiu alb",
        "black_aluminum": "Aluminiu negru",
        "gold_aluminum": "Aluminiu auriu",
        "mirror_silver": "Oglindă argintie",
        "ral_paint": "Vopsire RAL",
        "oracal_wrapped": "Îmbrăcat Oracal",
        "ral": "Vopsire RAL",
    },
    "backing_mode": {
        "forex_10_no_bevel": "Forex 10 mm fără bevel",
        "forex_10_with_bevel": "Forex 10 mm cu bevel",
        "closed_back": "Spate închis",
    },
    "lighting_system_type": {
        "none": "Fără iluminare",
        "led_modules": "Module LED",
        "led_strip": "Bandă LED",
        "front_lit": "Iluminare față",
        "back_lit": "Iluminare spate",
    },
}


def _options_for(canonical_key: str, option_values: list[str] | None) -> list[IntakeFormOption] | None:
    if not option_values:
        return None
    labels = _OPTION_LABELS_RO.get(canonical_key, {})
    return [
        IntakeFormOption(value=value, label_ro=labels.get(value, value.replace("_", " ")))
        for value in option_values
    ]


def _enrich_binding(binding: IntakeFormFieldBinding) -> IntakeFormFieldBinding:
    """Normalize field_type and attach structured options/visibility for generic renderer."""
    data = binding.model_dump()
    field_type = data.get("field_type")
    if field_type == "enum":
        data["field_type"] = "select"
    # Number fields with discrete option_values render as select (e.g. return depth).
    if field_type == "number" and data.get("option_values"):
        data["field_type"] = "select"
    if data.get("options") is None and data.get("option_values"):
        opts = _options_for(binding.canonical_key, binding.option_values) or [
            IntakeFormOption(value=str(v), label_ro=str(v)) for v in (binding.option_values or [])
        ]
        data["options"] = [opt.model_dump() for opt in opts]
    if data.get("visibility") is None and binding.visibility_rule:
        raw = binding.visibility_rule.strip()
        if "=" in raw and not raw.startswith("in:"):
            path_key, expected = raw.split("=", 1)
            data["visibility"] = IntakeVisibilityRule(
                kind="equals",
                workspace_path=f"{_FINISH}.{path_key.strip()}",
                value=expected.strip(),
            ).model_dump()
    return IntakeFormFieldBinding.model_validate(data)


LETTERS_RENDER_SECTIONS: list[IntakeRenderSection] = [
    IntakeRenderSection(
        section_key="finisaje_fields",
        title_ro="Finisaje",
        order=10,
        description_ro="Față · cant · spate / Vector Logo — adapter specializat pe grupuri litere (golden UI).",
        module_codes=["debitare_fata", "modelare_cant", "debitare_spate"],
        field_keys=[
            "face_finish_type",
            "return_finish_type",
            "return_depth_mm",
            "backing_mode",
        ],
        pilot_role="adapted_specialized",
        ui_tab_id="finisaje",
        renderer="specialized_letter_groups",
        component_owners=["FACE", "CANT", "BACK", "SURFACE_FINISH"],
        tab_label_ro="Finisaje",
        tab_hint_ro="Față · cant · Vector Logo",
        drives_review_tab=True,
    ),
    IntakeRenderSection(
        section_key="iluminare",
        title_ro="Iluminare",
        order=20,
        description_ro="Tip iluminare și PSU — câmpuri generice + adapter iluminare specializat.",
        module_codes=["sistem_led"],
        field_keys=["lighting_system_type", "selected_psu_watts"],
        pilot_role="generic_renderer",
        ui_tab_id="iluminare",
        renderer="specialized_lighting",
        component_owners=["LIGHTING", "ELECTRICAL"],
        tab_label_ro="Iluminare",
        tab_hint_ro="LED · backing",
        drives_review_tab=True,
    ),
    IntakeRenderSection(
        section_key="montaj_template",
        title_ro="Șablon montaj",
        order=30,
        description_ro="Activare și arie șablon — responsibility sablon_montaj (nu finisaj suprafață).",
        module_codes=["sablon_montaj"],
        field_keys=["mounting_template_enabled", "mounting_template_area_m2"],
        pilot_role="generic_renderer",
        ui_tab_id="montaj",
        renderer="generic_fields",
        component_owners=["INSTALLATION_TEMPLATE"],
        tab_label_ro="Montaj",
        tab_hint_ro="Șablon · sistem",
        drives_review_tab=True,
    ),
    IntakeRenderSection(
        section_key="montaj_system",
        title_ro="Sistem montaj",
        order=31,
        description_ro="Sistem / scope montaj — adapter specializat golden (nu câmpuri generice noi).",
        module_codes=["finisaje", "structura_suport"],
        field_keys=["mounting_system"],
        pilot_role="adapted_specialized",
        ui_tab_id="montaj",
        renderer="specialized_montaj",
        component_owners=["MOUNTING", "STRUCTURE_SUPPORT"],
        drives_review_tab=False,
    ),
    IntakeRenderSection(
        section_key="geometry_svg",
        title_ro="Geometrie SVG",
        order=5,
        description_ro="Facts SVG (layere, culori, contururi, dimensiuni) — consumate din analyzer; fără redesign classifier.",
        module_codes=["geometry_svg"],
        field_keys=["vector_file", "width_mm", "height_mm", "letter_count", "letter_perimeter_m", "letter_face_area_m2"],
        pilot_role="readonly_geometry",
        renderer="metadata_only",
        component_owners=["GEOMETRY_SVG"],
        drives_review_tab=False,
    ),
    IntakeRenderSection(
        section_key="packaging_logistics",
        title_ro="Ambalare / logistică",
        order=40,
        description_ro="Comportament full-product golden (always-on / pending) — fără sold packaging în Build 2.",
        module_codes=["ambalare_livrare_montaj"],
        field_keys=[],
        pilot_role="composition_metadata",
        renderer="metadata_only",
        component_owners=["PACKAGING_LOGISTICS"],
        drives_review_tab=False,
    ),
    IntakeRenderSection(
        section_key="interface_face_cant",
        title_ro="Interfață FACE+CANT (candidat)",
        order=50,
        description_ro="Target ownership pentru adeziv/bonding — metadata Build 2; output full-product neschimbat.",
        module_codes=["modelare_cant", "debitare_fata"],
        field_keys=[],
        pilot_role="composition_metadata",
        renderer="metadata_only",
        component_owners=["FACE", "CANT", "INTERFACE_FACE_CANT"],
        drives_review_tab=False,
    ),
]

PILOT_WRITABLE_PATHS = [
    f"{_FINISH}.face_finish_type",
    f"{_FINISH}.return_finish_type",
    f"{_FINISH}.return_depth_mm",
    f"{_FINISH}.backing_mode",
    f"{_FINISH}.lighting_system_type",
    f"{_FINISH}.selected_psu_watts",
    f"{_FINISH}.mounting_template_enabled",
    f"{_FINISH}.mounting_template_area_m2",
]

VOLUMETRIC_FIELD_BINDINGS: list[IntakeFormFieldBinding] = [
    IntakeFormFieldBinding(
        canonical_key="vector_file",
        workspace_path=f"{_SVG}.file_name",
        label_ro="Fișier SVG",
        required=True,
        field_type="file",
        decision="operator_upload",
        consumers=["geometry_svg", "svg_geometry_analysis"],
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
        field_type="number",
        unit="mm",
        decision="operator_input",
        consumers=["geometry_svg", "debitare_fata", "structura_suport"],
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
        field_type="number",
        unit="mm",
        decision="operator_input",
        consumers=["geometry_svg"],
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
        field_type="number",
        unit="count",
        decision="svg_analyzer_derived",
        consumers=["geometry_svg"],
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
        field_type="number",
        unit="m",
        decision="svg_analyzer_derived",
        consumers=["geometry_svg", "modelare_cant", "debitare_fata"],
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
        field_type="number",
        unit="m2",
        decision="svg_analyzer_derived",
        consumers=["geometry_svg", "debitare_fata", "debitare_spate"],
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
        field_type="enum",
        option_values=[
            "none",
            "oracal_651",
            "oracal_641",
            "oracal_8500",
            "printed_vinyl",
            "printed_laminated_vinyl",
            "print_laminate",
            "colored_plexiglas",
        ],
        decision="operator_select",
        consumers=["debitare_fata", "CostEngine Step 7 face_cnc_cut / vinyl"],
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
        field_type="number",
        unit="mm",
        option_values=["40", "60", "80", "100", "120"],
        decision="operator_select",
        consumers=["modelare_cant", "CostEngine Step 7 return_profile_linear_meter"],
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
        field_type="enum",
        option_values=[
            "white_aluminum",
            "black_aluminum",
            "gold_aluminum",
            "mirror_silver",
            "ral_paint",
            "oracal_wrapped",
        ],
        decision="operator_select",
        consumers=["modelare_cant", "CostEngine Step 7 RAL vs Oracal gate"],
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
        field_type="enum",
        option_values=["forex_10_no_bevel", "forex_10_with_bevel"],
        decision="operator_select",
        consumers=["debitare_spate", "components.comp_spate_litere"],
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
        field_type="boolean",
        visibility_rule="backing_mode=forex_10_with_bevel",
        decision="operator_toggle",
        consumers=["debitare_spate"],
        field_role="module_configuration",
        module_codes=["debitare_spate"],
        product_definition_keys=["back_bevel_enabled"],
    ),
    IntakeFormFieldBinding(
        canonical_key="lighting_system_type",
        workspace_path=f"{_FINISH}.lighting_system_type",
        label_ro="Tip iluminare",
        required=False,
        field_type="enum",
        option_values=["led_modules", "led_strip", "none"],
        visibility_rule="illuminated=true",
        decision="operator_select",
        consumers=["sistem_led", "components.comp_led_litere"],
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
        field_type="readonly",
        unit="buc",
        read_only=True,
        field_role="module_configuration",
        module_codes=["sistem_led"],
        product_definition_keys=["led_module_count"],
        cost_engine_step="Step 7",
        notes=["Derived / analyzer-owned — display only in generic renderer."],
    ),
    IntakeFormFieldBinding(
        canonical_key="selected_psu_watts",
        workspace_path=f"{_FINISH}.selected_psu_watts",
        label_ro="PSU selectat",
        required=False,
        field_type="select",
        unit="W",
        option_values=["60", "100", "150", "200", "250", "300"],
        decision="operator_select",
        field_role="module_configuration",
        module_codes=["sistem_led"],
        product_definition_keys=["selected_psu_watts"],
    ),
    IntakeFormFieldBinding(
        canonical_key="mounting_system",
        workspace_path=f"{_FINISH}.mounting_system",
        label_ro="Sistem montaj",
        required=True,
        field_type="enum",
        option_values=["direct_wall", "steel_bars", "aluminum_bars", "acm_panel"],
        decision="operator_select",
        consumers=["structura_suport"],
        field_role="module_activation",
        module_codes=["structura_suport"],
        product_definition_keys=["mounting_system"],
        aggregate_trace=["modules.optional trigger candidate"],
        notes=["Canonical Intake field for premount structure activation — not surface FINISH."],
    ),
    IntakeFormFieldBinding(
        canonical_key="mounting_template_enabled",
        workspace_path=f"{_FINISH}.mounting_template_enabled",
        label_ro="Șablon montaj activ",
        required=False,
        field_type="boolean",
        decision="operator_toggle",
        field_role="module_activation",
        module_codes=["sablon_montaj"],
        product_definition_keys=["mounting_template_enabled"],
        aggregate_trace=["materials.parent MAT-SABLON-*"],
    ),
    IntakeFormFieldBinding(
        canonical_key="mounting_template_area_m2",
        workspace_path=f"{_FINISH}.mounting_template_area_m2",
        label_ro="Suprafață șablon montaj",
        required=False,
        field_type="number",
        unit="m2",
        min_value=0,
        visibility=IntakeVisibilityRule(
            kind="truthy",
            workspace_path=f"{_FINISH}.mounting_template_enabled",
        ),
        decision="operator_input",
        field_role="module_configuration",
        module_codes=["sablon_montaj"],
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

        enriched_bindings = [_enrich_binding(b) for b in VOLUMETRIC_FIELD_BINDINGS]
        tab_driving = [s for s in LETTERS_RENDER_SECTIONS if s.drives_review_tab and s.ui_tab_id]
        ui_tab_ids: list[str] = []
        for section in sorted(tab_driving, key=lambda s: s.order):
            if section.ui_tab_id and section.ui_tab_id not in ui_tab_ids:
                ui_tab_ids.append(section.ui_tab_id)
        component_owners: list[str] = []
        for section in LETTERS_RENDER_SECTIONS:
            for owner in section.component_owners:
                if owner not in component_owners:
                    component_owners.append(owner)
        composition = FullProductCompositionSpec(
            mode="subset_activation",
            composition_authority=True,
            subset_activation_enabled=True,
            ui_tab_ids=ui_tab_ids,
            component_owners=component_owners,
            interface_candidates=[_FACE_CANT_INTERFACE_CANDIDATE],
            notes=[
                "Build 2: Review tabs composed from render_sections (drives_review_tab).",
                "Specialized adapters preserve golden Finisaje/Iluminare/Montaj UI.",
                "Build 3: subset activation real — FACE / CANT / FACE+CANT / full product.",
                "Inactive value policy: Option A — ignore downstream (no silent purge).",
            ],
        )
        return IntakeV6ModularFormContract(
            summary=IntakeV6ModularFormContractSummary(
                template_code=canonical_template_code,
                registry_version=REGISTRY_VERSION,
                active_module_count=len(active_modules),
                field_binding_count=len(enriched_bindings),
                runtime_authority=False,
                runtime_authority_scope=_LETTERS_RUNTIME_AUTHORITY_SCOPE,
                composition_authority=True,
                warnings=warnings,
            ),
            modules=modules,
            field_bindings=enriched_bindings,
            render_sections=LETTERS_RENDER_SECTIONS,
            writable_workspace_paths=list(PILOT_WRITABLE_PATHS),
            form_system_backbone=backbone,
            trigger_alignments=TRIGGER_ALIGNMENTS,
            valid_combinations=VALID_COMBINATIONS,
            invalid_combinations=INVALID_COMBINATIONS,
            orphan_fields_audit=ORPHAN_FIELDS_AUDIT,
            full_product_composition=composition,
            notes=[
                _LETTERS_RUNTIME_AUTHORITY_NOTE,
                "render_sections drive Review tab composition + generic field sections for Letters full-product.",
                "writable_workspace_paths is the allowlist for generic nested writes (unchanged vs Build 1).",
                "Does not mutate workspace payload server-side; Intake hydrates/saves answers.",
                "ProductDefinition consumes field_bindings / product_definition_keys as compiler inputs.",
                "ProductAggregate emits non-monetary commercial measurements; CPP 7G alone prices.",
                "Other templates remain unsupported by this scoped contract.",
                "No second Intake; no parallel catalog; no subset activation in Build 2.",
            ],
        )


_service: IntakeV6ModularFormContractService | None = None


def get_intake_v6_modular_form_contract_service() -> IntakeV6ModularFormContractService:
    global _service
    if _service is None:
        _service = IntakeV6ModularFormContractService()
    return _service
