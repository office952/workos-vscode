"""Read-only shared volumetric component contract metadata.

This registry documents shared component direction for Letters + Logo. It does
not activate pricing, ProductDefinition, ProductAggregate, Work Intake exposure,
or task/execution materialization.
"""

from __future__ import annotations

from schemas.shared_volumetric_component_contracts import (
    SharedVolumetricComponentContract,
    SharedVolumetricComponentProfile,
    SharedVolumetricComponentSummary,
    SharedVolumetricTemplateBinding,
)
from services.template_architecture_scope import (
    STRUCTURE_PREMOUNT_TEMPLATE_CODE,
    VOLUM_ALUMINUM_TEMPLATE_CODE,
    VOLUMETRIC_BACK_TEMPLATE_CODE,
    VOLUMETRIC_FACE_TEMPLATE_CODE,
    VOLUMETRIC_FINISH_TEMPLATE_CODE,
    VOLUMETRIC_LED_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_BACK_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_FACE_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_FINISH_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_LIGHTING_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_MOUNTING_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_RETURN_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_TEMPLATE_CODE,
    VOLUMETRIC_V2_TEMPLATE_CODE,
    normalize_template_code,
)

LETTERS_PROFILE = "letters"
LOGO_PROFILE = "logo"

_FORBIDDEN_RUNTIME_BEHAVIOR = [
    "does_not_change_quote_offerability",
    "does_not_expose_candidate_products_in_work_intake",
    "does_not_replace_template_module_links",
    "does_not_create_pricing_or_cost_engine_inputs",
    "does_not_create_product_definition_runtime_outputs",
    "does_not_create_product_aggregate_or_execution_outputs",
]


def _profile(
    *,
    profile_key: str,
    template_code: str,
    module_template_code: str,
    role_label: str,
    behavior_notes: list[str],
    template_config: dict[str, object],
    not_confirmed: list[str] | None = None,
) -> SharedVolumetricComponentProfile:
    return SharedVolumetricComponentProfile(
        profile_key=profile_key,
        profile_label="Letters" if profile_key == LETTERS_PROFILE else "Logo",
        template_code=template_code,
        module_template_code=module_template_code,
        role_label=role_label,
        behavior_notes=behavior_notes,
        template_config=template_config,
        not_confirmed=not_confirmed or [],
    )


def _binding(
    *,
    template_code: str,
    profile_key: str,
    module_template_code: str,
    role_label: str,
    module_code: str | None = None,
    template_config: dict[str, object] | None = None,
) -> SharedVolumetricTemplateBinding:
    return SharedVolumetricTemplateBinding(
        template_code=template_code,
        profile_key=profile_key,
        module_template_code=module_template_code,
        module_code=module_code,
        role_label=role_label,
        template_config=template_config or {},
    )


def _contract(
    *,
    component_key: str,
    display_name: str,
    purpose: str,
    shared_truth_fields: list[str],
    letters_module_template_code: str,
    letters_role_label: str,
    logo_module_template_code: str,
    logo_role_label: str,
    letters_behavior_notes: list[str],
    logo_behavior_notes: list[str],
    letters_template_config: dict[str, object],
    logo_template_config: dict[str, object],
    confidence: str,
    owner_decision: str,
    letters_module_code: str | None = None,
    logo_module_code: str | None = None,
    letters_not_confirmed: list[str] | None = None,
    logo_not_confirmed: list[str] | None = None,
) -> SharedVolumetricComponentContract:
    return SharedVolumetricComponentContract(
        component_key=component_key,
        display_name=display_name,
        purpose=purpose,
        shared_truth_fields=shared_truth_fields,
        profiles=[
            _profile(
                profile_key=LETTERS_PROFILE,
                template_code=VOLUMETRIC_V2_TEMPLATE_CODE,
                module_template_code=letters_module_template_code,
                role_label=letters_role_label,
                behavior_notes=letters_behavior_notes,
                template_config=letters_template_config,
                not_confirmed=letters_not_confirmed,
            ),
            _profile(
                profile_key=LOGO_PROFILE,
                template_code=VOLUMETRIC_LOGO_TEMPLATE_CODE,
                module_template_code=logo_module_template_code,
                role_label=logo_role_label,
                behavior_notes=logo_behavior_notes,
                template_config=logo_template_config,
                not_confirmed=logo_not_confirmed,
            ),
        ],
        template_bindings=[
            _binding(
                template_code=VOLUMETRIC_V2_TEMPLATE_CODE,
                profile_key=LETTERS_PROFILE,
                module_template_code=letters_module_template_code,
                role_label=letters_role_label,
                module_code=letters_module_code,
                template_config=letters_template_config,
            ),
            _binding(
                template_code=VOLUMETRIC_LOGO_TEMPLATE_CODE,
                profile_key=LOGO_PROFILE,
                module_template_code=logo_module_template_code,
                role_label=logo_role_label,
                module_code=logo_module_code,
                template_config=logo_template_config,
            ),
        ],
        confidence=confidence,
        owner_decision=owner_decision,
        forbidden_runtime_behavior=_FORBIDDEN_RUNTIME_BEHAVIOR,
    )


SHARED_VOLUMETRIC_COMPONENT_CONTRACTS: list[SharedVolumetricComponentContract] = [
    _contract(
        component_key="volumetric_face",
        display_name="Volumetric face",
        purpose="Front visual component contract for face panel / logo face surfaces.",
        shared_truth_fields=["component_role", "material_role", "geometry_basis", "area", "finish_target", "source"],
        letters_module_template_code=VOLUMETRIC_FACE_TEMPLATE_CODE,
        letters_module_code="debitare_fata",
        letters_role_label="Fata litera",
        logo_module_template_code=VOLUMETRIC_LOGO_FACE_TEMPLATE_CODE,
        logo_role_label="Fata logo",
        letters_behavior_notes=["Uses letter face area and face CNC / vinyl operation family."],
        logo_behavior_notes=["Uses logo area plus print / laminate operation family."],
        letters_template_config={"area_key": "letter_face_area_m2", "display_label": "Fata litera"},
        logo_template_config={"area_key": "svg_area_m2", "display_label": "Fata logo", "artwork_mode": "profile_specific"},
        confidence="MEDIUM",
        owner_decision="APPROVE_AS_DIRECTION",
    ),
    _contract(
        component_key="volumetric_back",
        display_name="Volumetric back",
        purpose="Back / closing panel component contract.",
        shared_truth_fields=["component_role", "material_role", "geometry_basis", "area", "source"],
        letters_module_template_code=VOLUMETRIC_BACK_TEMPLATE_CODE,
        letters_module_code="debitare_spate",
        letters_role_label="Spate litera",
        logo_module_template_code=VOLUMETRIC_LOGO_BACK_TEMPLATE_CODE,
        logo_role_label="Spate logo",
        letters_behavior_notes=["Uses backing mode and back cut semantics."],
        logo_behavior_notes=["Uses logo backing material and logo back cut semantics."],
        letters_template_config={"area_key": "letter_face_area_m2", "display_label": "Spate litera"},
        logo_template_config={"area_key": "svg_area_m2", "display_label": "Spate logo"},
        confidence="MEDIUM",
        owner_decision="APPROVE_AS_DIRECTION",
    ),
    _contract(
        component_key="volumetric_return_side",
        display_name="Volumetric return / side",
        purpose="Return, side wall, and lateral profile contract.",
        shared_truth_fields=["component_role", "material_role", "geometry_basis", "perimeter", "return_depth", "source"],
        letters_module_template_code=VOLUM_ALUMINUM_TEMPLATE_CODE,
        letters_module_code="modelare_cant",
        letters_role_label="Cant / laterale",
        logo_module_template_code=VOLUMETRIC_LOGO_RETURN_TEMPLATE_CODE,
        logo_role_label="Return / cant logo",
        letters_behavior_notes=["Uses letter perimeter and depth/finish gates for aluminum return."],
        logo_behavior_notes=["Uses logo perimeter with dedicated logo return operations."],
        letters_template_config={"perimeter_key": "letter_perimeter_m", "display_label": "Cant / laterale"},
        logo_template_config={"perimeter_key": "svg_perimeter_ml", "display_label": "Return / cant logo"},
        confidence="MEDIUM",
        owner_decision="APPROVE_AS_DIRECTION",
    ),
    _contract(
        component_key="volumetric_lighting",
        display_name="Volumetric lighting",
        purpose="Lighting and electrical component direction, kept partial until owner/electrical audit.",
        shared_truth_fields=["component_role", "led_material_role", "psu_material_role", "led_module_count", "psu_selection", "lighting_mode", "source"],
        letters_module_template_code=VOLUMETRIC_LED_TEMPLATE_CODE,
        letters_module_code="sistem_led",
        letters_role_label="LED / iluminare",
        logo_module_template_code=VOLUMETRIC_LOGO_LIGHTING_TEMPLATE_CODE,
        logo_role_label="Iluminare logo",
        letters_behavior_notes=["Uses lighting_system_type, led_module_count and PSU configuration."],
        logo_behavior_notes=["Uses logo_lighting_mode, emblem_led_module_count and logo electrical test."],
        letters_template_config={"led_count_key": "led_module_count", "psu_key": "selected_psu_watts", "display_label": "LED / iluminare"},
        logo_template_config={"led_count_key": "emblem_led_module_count", "psu_key": "selected_psu_watts", "display_label": "Iluminare logo"},
        confidence="PARTIAL",
        owner_decision="NEEDS_MORE_AUDIT",
        letters_not_confirmed=["front_lit_halo_combined", "lighting_zones", "circuits", "service_access"],
        logo_not_confirmed=["front_lit_halo_combined", "lighting_zones", "irregular_shape_impact", "circuits", "service_access"],
    ),
    _contract(
        component_key="volumetric_surface_finish",
        display_name="Volumetric surface finish",
        purpose="Surface finish direction for paint, vinyl, print, laminate and finishing targets.",
        shared_truth_fields=["component_role", "finish_target", "material_role", "geometry_basis", "source"],
        letters_module_template_code=VOLUMETRIC_FINISH_TEMPLATE_CODE,
        letters_module_code="finisaje",
        letters_role_label="Finisaje",
        logo_module_template_code=VOLUMETRIC_LOGO_FINISH_TEMPLATE_CODE,
        logo_role_label="Finisaje logo",
        letters_behavior_notes=["Covers RAL, vinyl, mounting template, packaging and QC responsibilities today."],
        logo_behavior_notes=["Focuses on logo print / laminate / application behavior today."],
        letters_template_config={"display_label": "Finisaje", "finish_family": "paint_vinyl_template"},
        logo_template_config={"display_label": "Finisaje logo", "finish_family": "print_laminate_profile"},
        confidence="LOW",
        owner_decision="KEEP_SEPARATE_NOW",
        letters_not_confirmed=["shared_packaging_qc_boundary"],
        logo_not_confirmed=["print_laminate_vs_letters_finish_boundary"],
    ),
    _contract(
        component_key="volumetric_mounting_interface",
        display_name="Volumetric mounting interface",
        purpose="Mounting, support, premount and template/install interface direction.",
        shared_truth_fields=["component_role", "mounting_support_requirement", "material_role", "activation_source", "source"],
        letters_module_template_code=STRUCTURE_PREMOUNT_TEMPLATE_CODE,
        letters_module_code="structura_suport",
        letters_role_label="Structura montaj",
        logo_module_template_code=VOLUMETRIC_LOGO_MOUNTING_TEMPLATE_CODE,
        logo_role_label="Montaj logo",
        letters_behavior_notes=["Optional premount/support bars controlled by support trigger semantics."],
        logo_behavior_notes=["Logo-specific mounting template / fastener / install behavior."],
        letters_template_config={"display_label": "Structura montaj", "activation": "optional_addon"},
        logo_template_config={"display_label": "Montaj logo", "activation": "required_module"},
        confidence="LOW",
        owner_decision="KEEP_SEPARATE_NOW",
        letters_not_confirmed=["mounting_system_vs_metal_support_required_alignment"],
        logo_not_confirmed=["mounting_kit_vs_premount_structure_boundary"],
    ),
]


def get_shared_volumetric_component_contracts() -> list[SharedVolumetricComponentContract]:
    return SHARED_VOLUMETRIC_COMPONENT_CONTRACTS


def get_shared_volumetric_component_summaries_for_template(
    template_code: str | None,
) -> list[SharedVolumetricComponentSummary]:
    normalized = normalize_template_code(template_code)
    if normalized not in {VOLUMETRIC_V2_TEMPLATE_CODE.upper(), VOLUMETRIC_LOGO_TEMPLATE_CODE.upper()}:
        return []

    summaries: list[SharedVolumetricComponentSummary] = []
    for contract in SHARED_VOLUMETRIC_COMPONENT_CONTRACTS:
        binding = next(
            (
                item
                for item in contract.template_bindings
                if normalize_template_code(item.template_code) == normalized
            ),
            None,
        )
        if binding is None:
            continue
        profile = next(
            (item for item in contract.profiles if item.profile_key == binding.profile_key),
            None,
        )
        summaries.append(
            SharedVolumetricComponentSummary(
                component_key=contract.component_key,
                display_name=contract.display_name,
                profile_key=binding.profile_key,
                module_template_code=binding.module_template_code,
                confidence=contract.confidence,
                owner_decision=contract.owner_decision,
                shared_truth_fields=contract.shared_truth_fields,
                not_confirmed=profile.not_confirmed if profile else [],
            )
        )
    return summaries
