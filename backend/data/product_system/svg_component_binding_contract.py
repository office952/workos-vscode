"""Product System SVG component-binding contract (canonical, code-owned).

Authority for which Component Templates may receive SVG geometry under a
Product Template. Intake must consume this projection later — not invent options.

No DB migration. No Intake UI changes. No FinishSetup / CPP / tasking.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Canonical geometry roles (not materials, not Product Template codes)
# ---------------------------------------------------------------------------

GEOMETRY_ROLE_LETTER_VECTOR_SET = "LETTER_VECTOR_SET"
GEOMETRY_ROLE_LOGO_VECTOR_SET = "LOGO_VECTOR_SET"
GEOMETRY_ROLE_SUPPORT_CONTOUR = "SUPPORT_CONTOUR"
GEOMETRY_ROLE_DECORATIVE_VECTOR = "DECORATIVE_VECTOR"
GEOMETRY_ROLE_IGNORE = "IGNORE"

GEOMETRY_ROLE_OWNER_LABELS: dict[str, str] = {
    GEOMETRY_ROLE_LETTER_VECTOR_SET: "Vector litere",
    GEOMETRY_ROLE_LOGO_VECTOR_SET: "Vector logo",
    GEOMETRY_ROLE_SUPPORT_CONTOUR: "Contur suport",
    GEOMETRY_ROLE_DECORATIVE_VECTOR: "Element decorativ",
    GEOMETRY_ROLE_IGNORE: "Ignoră",
}

SELECTION_MODE_LAYER_OR_GROUP = "LAYER_OR_GROUP"
SELECTION_MODE_CLOSED_CONTOUR = "CLOSED_CONTOUR"
SELECTION_MODE_NONE = "NONE"

CARDINALITY_MULTI = "MULTI"
CARDINALITY_MAX_ONE = "MAX_ONE"
CARDINALITY_NONE = "NONE"

# Product / component identities
LETTERS_PRODUCT = "TPL-VOLUMETRIC-LETTERS_v2"
LOGO_PRODUCT = "TPL-VOLUMETRIC-LOGO_v1"
FACE_COMPONENT = "TPL-VOLUMETRIC-FACE_v1"
ACM_BOXED_SUPPORT = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"
METAL_PREMOUNT = "TPL-METAL-PREMOUNT-STRUCTURE_v1"

# Stale string-only placeholder (never a seeded Product Template)
STALE_BOND_CASETAT = "TPL-BOND-CASETAT"
STALE_BOND_CASETAT_STATUS = "legacy_deprecated_string_only"

PROCESS_FACE = "FACE"
PROCESS_ALUCOBOND = "ALUCOBOND_CASED_PANEL"
PROCESS_METAL = "METAL_SUPPORT"


def _binding(
    *,
    component_template_code: str,
    owner_label: str,
    accepted_geometry_roles: list[str],
    selection_mode: str,
    cardinality: str,
    required: bool,
    available: bool,
    active_by_default: bool,
    process_component_code: str | None = None,
    technical_role: str,
    geometry_requirements: dict[str, Any] | None = None,
    guards: list[str] | None = None,
    product_definition_targets: list[str] | None = None,
    svg_binding_enabled: bool = True,
    capabilities: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "component_template_code": component_template_code,
        "process_component_code": process_component_code,
        "owner_label": owner_label,
        "accepted_geometry_roles": list(accepted_geometry_roles),
        "selection_mode": selection_mode,
        "cardinality": cardinality,
        "required": required,
        "available": available,
        "active": False if not active_by_default else True,
        "active_by_default": active_by_default,
        "svg_binding": {
            "enabled": svg_binding_enabled,
            "accepted_geometry_roles": list(accepted_geometry_roles),
            "selection_mode": selection_mode,
            "cardinality": cardinality,
            "geometry_requirements": geometry_requirements or {},
            "owner_label": owner_label,
            "technical_role": technical_role,
        },
        "technical_role": technical_role,
        "guards": list(guards or []),
        "product_definition_targets": list(product_definition_targets or []),
        "capabilities": list(capabilities or []),
    }


# Bindable components declared by Product Template composition (static contract).
SVG_BINDABLE_BY_PRODUCT_TEMPLATE: dict[str, list[dict[str, Any]]] = {
    LETTERS_PRODUCT: [
        _binding(
            component_template_code=FACE_COMPONENT,
            process_component_code=PROCESS_FACE,
            owner_label="Vector litere",
            accepted_geometry_roles=[GEOMETRY_ROLE_LETTER_VECTOR_SET],
            selection_mode=SELECTION_MODE_LAYER_OR_GROUP,
            cardinality=CARDINALITY_MULTI,
            required=True,
            available=True,
            active_by_default=True,
            technical_role="letter_face",
            geometry_requirements={"closed_required": False},
            product_definition_targets=[
                "layer_role_setup",
                "selected_layer_refs.vector_litere",
                "composition.letters",
            ],
            capabilities=["letter_vector_geometry"],
        ),
        _binding(
            component_template_code=LOGO_PRODUCT,
            process_component_code=None,
            owner_label="Vector logo",
            accepted_geometry_roles=[GEOMETRY_ROLE_LOGO_VECTOR_SET],
            selection_mode=SELECTION_MODE_LAYER_OR_GROUP,
            cardinality=CARDINALITY_MULTI,
            required=False,
            available=True,
            active_by_default=False,
            technical_role="logo_vector",
            geometry_requirements={"closed_required": False},
            guards=[
                "candidate_only",
                "not_root_offerable",
                "linked_segment_only",
            ],
            product_definition_targets=[
                "layer_role_setup",
                "selected_layer_refs.vector_logo",
                "composition.logo",
            ],
            capabilities=["logo_vector_geometry"],
        ),
        _binding(
            component_template_code=ACM_BOXED_SUPPORT,
            process_component_code=PROCESS_ALUCOBOND,
            owner_label="Panou Alucobond casetat",
            accepted_geometry_roles=[GEOMETRY_ROLE_SUPPORT_CONTOUR],
            selection_mode=SELECTION_MODE_CLOSED_CONTOUR,
            cardinality=CARDINALITY_MAX_ONE,
            required=False,
            available=True,
            active_by_default=False,
            technical_role="alucobond_cased_support",
            geometry_requirements={
                "closed_required": True,
                "panel_geometry": True,
                "casing_configuration": True,
                "service_corner": True,
                "internal_frame": True,
            },
            guards=[
                "optional_addon",
                "xor_with_metal_support",
                "inactive_until_operator_activates",
                "no_cpp_from_binding",
                "no_tasking_from_binding",
            ],
            product_definition_targets=[
                "finish_setup.mounting_solution",
                "finish_setup.svg_support_selection",
                "canonical_values.support_type=alucobond_cased",
                "canonical_values.svg_support_element_id",
                "canonical_values.panel_geometry",
                "canonical_values.casing_profile",
                "power_supply_service_corner",
            ],
            capabilities=[
                "panel_geometry",
                "casing_configuration",
                "service_corner",
                "internal_frame",
            ],
        ),
        _binding(
            component_template_code=METAL_PREMOUNT,
            process_component_code=PROCESS_METAL,
            owner_label="Structură metalică premontaj",
            accepted_geometry_roles=[],
            selection_mode=SELECTION_MODE_NONE,
            cardinality=CARDINALITY_NONE,
            required=False,
            available=True,
            active_by_default=False,
            svg_binding_enabled=False,
            technical_role="metal_premount_support",
            geometry_requirements={},
            guards=[
                "optional_addon",
                "xor_with_alucobond_cased",
                "svg_geometry_not_required",
            ],
            product_definition_targets=[
                "finish_setup.mounting_solution",
                "canonical_values.support_type=metal_bars",
            ],
            capabilities=["metal_support"],
        ),
    ],
    ACM_BOXED_SUPPORT: [
        _binding(
            component_template_code=ACM_BOXED_SUPPORT,
            process_component_code=PROCESS_ALUCOBOND,
            owner_label="Panou Alucobond casetat",
            accepted_geometry_roles=[GEOMETRY_ROLE_SUPPORT_CONTOUR],
            selection_mode=SELECTION_MODE_CLOSED_CONTOUR,
            cardinality=CARDINALITY_MAX_ONE,
            required=False,
            available=True,
            active_by_default=False,
            technical_role="alucobond_cased_support",
            geometry_requirements={
                "closed_required": True,
                "panel_geometry": True,
                "casing_configuration": True,
                "service_corner": True,
                "internal_frame": True,
            },
            guards=[
                "standalone_or_linked_child",
                "inactive_until_operator_activates",
            ],
            product_definition_targets=[
                "finish_setup.mounting_solution",
                "finish_setup.svg_support_selection",
            ],
            capabilities=[
                "panel_geometry",
                "casing_configuration",
                "service_corner",
                "internal_frame",
            ],
        ),
    ],
    LOGO_PRODUCT: [
        _binding(
            component_template_code=LOGO_PRODUCT,
            process_component_code=None,
            owner_label="Vector logo",
            accepted_geometry_roles=[GEOMETRY_ROLE_LOGO_VECTOR_SET],
            selection_mode=SELECTION_MODE_LAYER_OR_GROUP,
            cardinality=CARDINALITY_MULTI,
            required=True,
            available=True,
            active_by_default=False,
            technical_role="logo_vector",
            guards=["candidate_only", "not_root_offerable"],
            product_definition_targets=[
                "layer_role_setup",
                "selected_layer_refs.vector_logo",
            ],
            capabilities=["logo_vector_geometry"],
        ),
    ],
}


def stale_bond_casetat_status() -> dict[str, Any]:
    """Documented containment for the string-only pending support code."""
    return {
        "code": STALE_BOND_CASETAT,
        "status": STALE_BOND_CASETAT_STATUS,
        "seeded_product_template": False,
        "new_selection_authority": False,
        "live_authority": ACM_BOXED_SUPPORT,
        "strategy": "deprecated_mapping",
        "owner_facing": False,
        "notes": (
            "String-only pending placeholder from Intake composition recommendation. "
            "Not a seeded Product Template. Live support authority is "
            f"{ACM_BOXED_SUPPORT}."
        ),
    }


def list_geometry_roles() -> list[dict[str, str]]:
    return [
        {"code": code, "owner_label": label}
        for code, label in GEOMETRY_ROLE_OWNER_LABELS.items()
    ]
