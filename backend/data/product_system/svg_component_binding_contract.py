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
# Face-zone geometry (role = geometry intent; construction = face_treatment — not ROUTED_FACE)
GEOMETRY_ROLE_CUTOUT_TEXT = "CUTOUT_TEXT"
GEOMETRY_ROLE_CUTOUT_LOGO = "CUTOUT_LOGO"
GEOMETRY_ROLE_ACRYLIC_INSERT = "ACRYLIC_INSERT"

GEOMETRY_ROLE_OWNER_LABELS: dict[str, str] = {
    GEOMETRY_ROLE_LETTER_VECTOR_SET: "Vector litere",
    GEOMETRY_ROLE_LOGO_VECTOR_SET: "Vector logo",
    GEOMETRY_ROLE_SUPPORT_CONTOUR: "Contur suport",
    GEOMETRY_ROLE_DECORATIVE_VECTOR: "Element decorativ",
    GEOMETRY_ROLE_IGNORE: "Ignoră",
    GEOMETRY_ROLE_CUTOUT_TEXT: "Text decupat",
    GEOMETRY_ROLE_CUTOUT_LOGO: "Logo decupat",
    GEOMETRY_ROLE_ACRYLIC_INSERT: "Insert plexiglas",
}

# Face treatments hosted on the ACM boxed shell (codes from acp_face_treatment_registry_v1)
ACM_SHELL_FACE_TREATMENT_CODES: list[str] = [
    "FACE-TREATMENT-ROUTED-BACKLIT-CUTOUT",
    "FACE-TREATMENT-ACRYLIC-INSERT",
    "FACE-TREATMENT-PLAIN-DECORATIVE",
]

ACM_SHELL_GEOMETRY_ROLES: list[str] = [
    GEOMETRY_ROLE_SUPPORT_CONTOUR,
    GEOMETRY_ROLE_CUTOUT_TEXT,
    GEOMETRY_ROLE_CUTOUT_LOGO,
    GEOMETRY_ROLE_ACRYLIC_INSERT,
    GEOMETRY_ROLE_DECORATIVE_VECTOR,
]

ACM_SHELL_CAPABILITIES: list[str] = [
    "boxed_acp_shell",
    "local_face_treatments",
    "panel_geometry",
    "casing_configuration",
    "service_corner",
    "internal_frame",
]

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
    accepted_face_treatment_codes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "component_template_code": component_template_code,
        "process_component_code": process_component_code,
        "owner_label": owner_label,
        "accepted_geometry_roles": list(accepted_geometry_roles),
        "accepted_face_treatment_codes": list(accepted_face_treatment_codes or []),
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
            "accepted_face_treatment_codes": list(accepted_face_treatment_codes or []),
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
            accepted_geometry_roles=list(ACM_SHELL_GEOMETRY_ROLES),
            accepted_face_treatment_codes=list(ACM_SHELL_FACE_TREATMENT_CODES),
            selection_mode=SELECTION_MODE_CLOSED_CONTOUR,
            # SUPPORT_CONTOUR remains MAX_ONE; cutout/insert/decorative are MULTI via same component.
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
                "local_face_treatments": True,
                "support_contour_cardinality": CARDINALITY_MAX_ONE,
                "face_treatment_cardinality": CARDINALITY_MULTI,
            },
            guards=[
                "optional_addon",
                "xor_with_metal_support",
                "inactive_until_operator_activates",
                "no_cpp_from_binding",
                "no_tasking_from_binding",
                "no_global_face_mode_xor",
            ],
            product_definition_targets=[
                "finish_setup.mounting_solution",
                "finish_setup.svg_support_selection",
                "finish_setup.svg_component_bindings.face_treatment",
                "canonical_values.support_type=alucobond_cased",
                "canonical_values.svg_support_element_id",
                "canonical_values.panel_geometry",
                "canonical_values.casing_profile",
                "canonical_values.face_treatment_instances",
                "power_supply_service_corner",
            ],
            capabilities=list(ACM_SHELL_CAPABILITIES),
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
            accepted_geometry_roles=list(ACM_SHELL_GEOMETRY_ROLES),
            accepted_face_treatment_codes=list(ACM_SHELL_FACE_TREATMENT_CODES),
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
                "local_face_treatments": True,
                "support_contour_cardinality": CARDINALITY_MAX_ONE,
                "face_treatment_cardinality": CARDINALITY_MULTI,
            },
            guards=[
                "standalone_or_linked_child",
                "inactive_until_operator_activates",
                "no_global_face_mode_xor",
            ],
            product_definition_targets=[
                "finish_setup.mounting_solution",
                "finish_setup.svg_support_selection",
                "finish_setup.svg_component_bindings.face_treatment",
                "canonical_values.face_treatment_instances",
            ],
            capabilities=list(ACM_SHELL_CAPABILITIES),
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


def acp_shell_face_treatment_authority() -> dict[str, Any]:
    """Projection for Product System / Intake consumers — shell hosts local treatments."""
    return {
        "live_shell_template": ACM_BOXED_SUPPORT,
        "capabilities": list(ACM_SHELL_CAPABILITIES),
        "accepted_geometry_roles": list(ACM_SHELL_GEOMETRY_ROLES),
        "accepted_face_treatment_codes": list(ACM_SHELL_FACE_TREATMENT_CODES),
        "support_contour_cardinality": CARDINALITY_MAX_ONE,
        "face_treatment_cardinality": CARDINALITY_MULTI,
        "global_face_mode": None,
        "authority": "product_system_svg_component_binding_contract_v1",
    }
