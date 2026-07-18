"""ACP face-treatment authority registry (canonical, code-owned).

Separates:
  geometry_role ≠ component ownership ≠ face_treatment ≠ finish ≠ material

V1 defines identity + compatibility only — no plexiglas/LED/process modules.
Legacy TPL-ACP-LIGHT-ROUTED is NOT an authority for Intake V6 composition.
"""

from __future__ import annotations

from typing import Any

REGISTRY_VERSION = "acp_face_treatment/v1"

# ---------------------------------------------------------------------------
# Treatment codes (construction / use of face zones — not finishes)
# ---------------------------------------------------------------------------

FACE_TREATMENT_APPLIED_VOLUMETRIC = "FACE-TREATMENT-APPLIED-VOLUMETRIC-COMPONENT"
FACE_TREATMENT_ROUTED_BACKLIT = "FACE-TREATMENT-ROUTED-BACKLIT-CUTOUT"
FACE_TREATMENT_ACRYLIC_INSERT = "FACE-TREATMENT-ACRYLIC-INSERT"
FACE_TREATMENT_PLAIN_DECORATIVE = "FACE-TREATMENT-PLAIN-DECORATIVE"

FACE_TREATMENT_NOT_APPLICABLE = "NOT_APPLICABLE"

# Geometry roles that participate in face treatments (shell SUPPORT_CONTOUR is not a treatment)
GEOMETRY_ROLE_CUTOUT_TEXT = "CUTOUT_TEXT"
GEOMETRY_ROLE_CUTOUT_LOGO = "CUTOUT_LOGO"
GEOMETRY_ROLE_ACRYLIC_INSERT = "ACRYLIC_INSERT"

# Readiness (V1 foundation — stops at LOCAL_CONFIGURATION_REQUIRED for routed/insert)
READINESS_DETECTED = "DETECTED"
READINESS_SUGGESTED = "SUGGESTED"
READINESS_CONFIRMED = "CONFIRMED"
READINESS_LOCAL_CONFIGURATION_REQUIRED = "LOCAL_CONFIGURATION_REQUIRED"
READINESS_READY_FOR_AGGREGATION = "READY_FOR_AGGREGATION"
READINESS_INACTIVE = "INACTIVE"
READINESS_NOT_APPLICABLE = "NOT_APPLICABLE"

CAPABILITY_BOXED_ACP_SHELL = "boxed_acp_shell"
CAPABILITY_LOCAL_FACE_TREATMENTS = "local_face_treatments"
CAPABILITY_LETTER_VECTOR = "letter_vector_geometry"
CAPABILITY_LOGO_VECTOR = "logo_vector_geometry"

# Live Intake V6 shell authority (not LIGHT-ROUTED)
LIVE_ACP_SHELL_TEMPLATE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"
LEGACY_ACP_LIGHT_ROUTED = "TPL-ACP-LIGHT-ROUTED"
LEGACY_ACP_LIGHT_ROUTED_STATUS = "PARALLEL_LEGACY_COST_PATH"

FACE_TREATMENT_REGISTRY: dict[str, dict[str, Any]] = {
    FACE_TREATMENT_APPLIED_VOLUMETRIC: {
        "code": FACE_TREATMENT_APPLIED_VOLUMETRIC,
        "label": "Componentă volumetrică aplicată",
        "version": 1,
        "status": "active",
        "applicable_component_capabilities": [CAPABILITY_LETTER_VECTOR, CAPABILITY_LOGO_VECTOR],
        "allowed_geometry_roles": ["LETTER_VECTOR_SET", "LOGO_VECTOR_SET"],
        "allowed_component_template_codes": [
            "TPL-VOLUMETRIC-FACE_v1",
            "TPL-VOLUMETRIC-LOGO_v1",
        ],
        "requires_local_module": False,
        "allows_multiple_instances": True,
        "ownership_mode": "external_component",
        "local_configuration_status_default": "NOT_REQUIRED",
        "provenance": {
            "source": "OWNER_CONFIRMED_AUDIT_2026-07-18",
            "registry_version": REGISTRY_VERSION,
            "notes": "Applied letters/logo remain separate component instances.",
        },
    },
    FACE_TREATMENT_ROUTED_BACKLIT: {
        "code": FACE_TREATMENT_ROUTED_BACKLIT,
        "label": "Decupaj iluminat (plexiglas pe spate)",
        "version": 1,
        "status": "active",
        "applicable_component_capabilities": [
            CAPABILITY_BOXED_ACP_SHELL,
            CAPABILITY_LOCAL_FACE_TREATMENTS,
        ],
        "allowed_geometry_roles": [GEOMETRY_ROLE_CUTOUT_TEXT, GEOMETRY_ROLE_CUTOUT_LOGO],
        "allowed_component_template_codes": [LIVE_ACP_SHELL_TEMPLATE],
        "requires_local_module": True,
        "allows_multiple_instances": True,
        "ownership_mode": "acp_shell_local",
        "local_configuration_status_default": "NOT_CONFIGURED",
        "provenance": {
            "source": "OWNER_CONFIRMED_AUDIT_2026-07-18",
            "registry_version": REGISTRY_VERSION,
            "notes": "Identity only in V1 — plexiglas/LED modules deferred.",
        },
    },
    FACE_TREATMENT_ACRYLIC_INSERT: {
        "code": FACE_TREATMENT_ACRYLIC_INSERT,
        "label": "Insert plexiglas",
        "version": 1,
        "status": "active",
        "applicable_component_capabilities": [
            CAPABILITY_BOXED_ACP_SHELL,
            CAPABILITY_LOCAL_FACE_TREATMENTS,
        ],
        "allowed_geometry_roles": [GEOMETRY_ROLE_ACRYLIC_INSERT],
        "allowed_component_template_codes": [LIVE_ACP_SHELL_TEMPLATE],
        "requires_local_module": True,
        "allows_multiple_instances": True,
        "ownership_mode": "acp_shell_local",
        "local_configuration_status_default": "NOT_CONFIGURED",
        "provenance": {
            "source": "OWNER_CONFIRMED_AUDIT_2026-07-18",
            "registry_version": REGISTRY_VERSION,
            "notes": "Identity only in V1 — fit/retention/illumination deferred.",
        },
    },
    FACE_TREATMENT_PLAIN_DECORATIVE: {
        "code": FACE_TREATMENT_PLAIN_DECORATIVE,
        "label": "Zonă plină / decorativă",
        "version": 1,
        "status": "active",
        "applicable_component_capabilities": [
            CAPABILITY_BOXED_ACP_SHELL,
            CAPABILITY_LOCAL_FACE_TREATMENTS,
        ],
        "allowed_geometry_roles": ["DECORATIVE_VECTOR"],
        "allowed_component_template_codes": [LIVE_ACP_SHELL_TEMPLATE],
        "requires_local_module": False,
        "allows_multiple_instances": True,
        "ownership_mode": "acp_shell_local",
        "local_configuration_status_default": "NOT_REQUIRED",
        "provenance": {
            "source": "OWNER_CONFIRMED_AUDIT_2026-07-18",
            "registry_version": REGISTRY_VERSION,
        },
    },
}


def list_face_treatments(*, status: str | None = "active") -> list[dict[str, Any]]:
    rows = [dict(v) for v in FACE_TREATMENT_REGISTRY.values()]
    if status is None:
        return rows
    return [r for r in rows if r.get("status") == status]


def get_face_treatment(code: str | None) -> dict[str, Any] | None:
    key = str(code or "").strip()
    if not key or key == FACE_TREATMENT_NOT_APPLICABLE:
        return None
    row = FACE_TREATMENT_REGISTRY.get(key)
    return dict(row) if row else None


def legacy_light_routed_policy() -> dict[str, Any]:
    return {
        "template_code": LEGACY_ACP_LIGHT_ROUTED,
        "status": LEGACY_ACP_LIGHT_ROUTED_STATUS,
        "intake_v6_composition_authority": False,
        "svg_bindable_authority": False,
        "face_treatment_authority": False,
        "live_shell_authority": LIVE_ACP_SHELL_TEMPLATE,
        "consumers": [
            "CostEngine / QuoteWizard hierarchical quote_input",
            "seed_tpl_acp_light_routed / seed_sync_all",
            "svg_layer_template_mapping label map",
            "productsystem gate / registry linkage tests",
        ],
        "policy": (
            "Keep seeded for parallel CostEngine path. Do not use as Intake V6 "
            "SVG binding or face-treatment authority. Do not auto-migrate into "
            "face modules without owner GO."
        ),
        "registry_version": REGISTRY_VERSION,
    }


def treatments_for_geometry_role(geometry_role: str | None) -> list[dict[str, Any]]:
    role = str(geometry_role or "").strip()
    if not role:
        return []
    return [
        dict(row)
        for row in FACE_TREATMENT_REGISTRY.values()
        if role in (row.get("allowed_geometry_roles") or []) and row.get("status") == "active"
    ]


def is_shell_local_treatment(code: str | None) -> bool:
    row = get_face_treatment(code)
    return bool(row and row.get("ownership_mode") == "acp_shell_local")
