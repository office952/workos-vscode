"""ACP local face-module contracts (component-owned, code authority).

Identity + guarded technical configuration. No invented plexi/LED quantities.
Electrical ownership: SHELL_COMMON_WITH_ZONE_INTENTS (per-zone intent, shell PSU/wiring).
Legacy TPL-ACP-LIGHT-ROUTED is PARALLEL_LEGACY_COST_PATH — not imported.
"""

from __future__ import annotations

from typing import Any

from data.product_system.acp_face_treatment_registry_v1 import (
    FACE_TREATMENT_ACRYLIC_INSERT,
    FACE_TREATMENT_APPLIED_VOLUMETRIC,
    FACE_TREATMENT_PLAIN_DECORATIVE,
    FACE_TREATMENT_ROUTED_BACKLIT,
    LIVE_ACP_SHELL_TEMPLATE,
)

MODULES_CONTRACT_VERSION = "acp_local_face_modules/v1"
ELECTRICAL_OWNERSHIP_MODE = "SHELL_COMMON_WITH_ZONE_INTENTS"

MODULE_ROUTED_BACKLIT = "ACP-LOCAL-MODULE-ROUTED-BACKLIT"
MODULE_ACRYLIC_INSERT = "ACP-LOCAL-MODULE-ACRYLIC-INSERT"
MODULE_PLAIN_DECORATIVE = "ACP-LOCAL-MODULE-PLAIN-DECORATIVE"
INTERFACE_APPLIED_VOLUMETRIC = "ACP-APPLIED-COMPONENT-INTERFACE"

STATUS_ACTIVE = "ACTIVE"
STATUS_INACTIVE = "INACTIVE"

GATE_OWNER_REQUIRED = "OWNER_GATE_REQUIRED"
GATE_MANUAL = "MANUAL_CONFIRMATION_REQUIRED"
GATE_OWNER_REVIEW = "OWNER_REVIEW_REQUIRED"
STATUS_NOT_CONFIGURED = "NOT_CONFIGURED"
STATUS_NOT_REQUIRED = "NOT_REQUIRED"
STATUS_CONFIGURED = "CONFIGURED"

# Owner-confirmed frequent insert thickness — not sole admitted value.
INSERT_THICKNESS_OWNER_VARIANT_MM = 10.0
INSERT_THICKNESS_PROVENANCE = "OWNER_CONFIRMED_VARIANT"

LOCAL_FACE_MODULE_REGISTRY: dict[str, dict[str, Any]] = {
    MODULE_ROUTED_BACKLIT: {
        "module_code": MODULE_ROUTED_BACKLIT,
        "label": "Decupaj iluminat (plexiglas pe spate)",
        "version": 1,
        "status": "active",
        "host_component_template_codes": [LIVE_ACP_SHELL_TEMPLATE],
        "accepted_face_treatment_codes": [FACE_TREATMENT_ROUTED_BACKLIT],
        "accepted_geometry_roles": ["CUTOUT_TEXT", "CUTOUT_LOGO"],
        "requires_local_module": True,
        "ownership_mode": "acp_shell_local",
        "resource_classes_required": [
            "optical_backing_material",
            "optical_mounting_method",
            "illumination_intent",
        ],
        "resource_authority": "MISSING_OPTICAL_ELECTRICAL_RO — do not invent catalogs",
        "capabilities": ["routed_backlit_cutout_module"],
        "process_intents_guarded": [
            "cnc_route_acp_face",
            "cut_plexiglas_backing",
            "mount_plexiglas_backing",
            "led_cavity_intent",
            "electrical_test_intent",
        ],
        "provenance": {
            "source": "OWNER_GO_ACP_LOCAL_FACE_MODULES_2026-07-18",
            "contract_version": MODULES_CONTRACT_VERSION,
            "legacy_reference": "TPL-ACP-LIGHT-ROUTED diffuser/LED structure — not authority",
        },
    },
    MODULE_ACRYLIC_INSERT: {
        "module_code": MODULE_ACRYLIC_INSERT,
        "label": "Insert plexiglas",
        "version": 1,
        "status": "active",
        "host_component_template_codes": [LIVE_ACP_SHELL_TEMPLATE],
        "accepted_face_treatment_codes": [FACE_TREATMENT_ACRYLIC_INSERT],
        "accepted_geometry_roles": ["ACRYLIC_INSERT"],
        "requires_local_module": True,
        "ownership_mode": "acp_shell_local",
        "resource_classes_required": [
            "optical_insert_material",
            "insert_retention",
            "illumination_intent",
        ],
        "resource_authority": "MISSING_OPTICAL_ELECTRICAL_RO — do not invent catalogs",
        "capabilities": ["acrylic_insert_module"],
        "default_insert_thickness_mm": INSERT_THICKNESS_OWNER_VARIANT_MM,
        "default_insert_thickness_provenance": INSERT_THICKNESS_PROVENANCE,
        "default_insert_thickness_status": GATE_OWNER_REVIEW,
        "sole_thickness_admitted": False,
        "process_intents_guarded": [
            "cnc_route_acp_insert_pocket",
            "cut_plexiglas_insert",
            "fit_insert",
            "retain_insert",
            "illumination_intent",
        ],
        "provenance": {
            "source": "OWNER_GO_ACP_LOCAL_FACE_MODULES_2026-07-18",
            "contract_version": MODULES_CONTRACT_VERSION,
            "legacy_reference": "LIGHT-ROUTED RELIEF_PLEXI_10MM — not V6 authority",
        },
    },
    MODULE_PLAIN_DECORATIVE: {
        "module_code": MODULE_PLAIN_DECORATIVE,
        "label": "Zonă plină / decorativă",
        "version": 1,
        "status": "active",
        "host_component_template_codes": [LIVE_ACP_SHELL_TEMPLATE],
        "accepted_face_treatment_codes": [FACE_TREATMENT_PLAIN_DECORATIVE],
        "accepted_geometry_roles": ["DECORATIVE_VECTOR"],
        "requires_local_module": False,
        "ownership_mode": "acp_shell_local",
        "resource_classes_required": [],
        "capabilities": ["plain_decorative_face_zone"],
        "process_intents_guarded": [],
        "provenance": {
            "source": "OWNER_GO_ACP_LOCAL_FACE_MODULES_2026-07-18",
            "contract_version": MODULES_CONTRACT_VERSION,
        },
    },
    INTERFACE_APPLIED_VOLUMETRIC: {
        "module_code": INTERFACE_APPLIED_VOLUMETRIC,
        "label": "Interfață componentă volumetrică aplicată",
        "version": 1,
        "status": "active",
        "host_component_template_codes": [LIVE_ACP_SHELL_TEMPLATE],
        "accepted_face_treatment_codes": [FACE_TREATMENT_APPLIED_VOLUMETRIC],
        "accepted_geometry_roles": ["LETTER_VECTOR_SET", "LOGO_VECTOR_SET"],
        "requires_local_module": False,
        "ownership_mode": "external_component_interface",
        "applied_component_template_codes": [
            "TPL-VOLUMETRIC-FACE_v1",
            "TPL-VOLUMETRIC-LOGO_v1",
        ],
        "capabilities": ["applied_component_host"],
        "process_intents_guarded": [
            "mount_applied_component_on_acp",
            "cable_passage_intent",
            "electrical_interface_intent",
        ],
        "provenance": {
            "source": "OWNER_GO_ACP_LOCAL_FACE_MODULES_2026-07-18",
            "contract_version": MODULES_CONTRACT_VERSION,
            "notes": "Letters remain separate component instances — interface only.",
        },
    },
}

TREATMENT_TO_MODULE: dict[str, str] = {
    FACE_TREATMENT_ROUTED_BACKLIT: MODULE_ROUTED_BACKLIT,
    FACE_TREATMENT_ACRYLIC_INSERT: MODULE_ACRYLIC_INSERT,
    FACE_TREATMENT_PLAIN_DECORATIVE: MODULE_PLAIN_DECORATIVE,
    FACE_TREATMENT_APPLIED_VOLUMETRIC: INTERFACE_APPLIED_VOLUMETRIC,
}

ACM_LOCAL_MODULE_CAPABILITIES: list[str] = [
    "boxed_acp_shell",
    "local_face_treatments",
    "routed_backlit_cutout_module",
    "acrylic_insert_module",
    "applied_component_host",
    "illumination_host",
    "segmented_background_assembly",
]


def list_local_face_modules(*, status: str | None = "active") -> list[dict[str, Any]]:
    rows = [dict(v) for v in LOCAL_FACE_MODULE_REGISTRY.values()]
    if status is None:
        return rows
    return [r for r in rows if r.get("status") == status]


def get_local_face_module(code: str | None) -> dict[str, Any] | None:
    row = LOCAL_FACE_MODULE_REGISTRY.get(str(code or "").strip())
    return dict(row) if row else None


def module_code_for_treatment(treatment_code: str | None) -> str | None:
    return TREATMENT_TO_MODULE.get(str(treatment_code or "").strip())


def electrical_ownership_policy() -> dict[str, Any]:
    return {
        "mode": ELECTRICAL_OWNERSHIP_MODE,
        "contract_version": MODULES_CONTRACT_VERSION,
        "zone_declares": "illumination_intent",
        "shell_owns": ["led_configuration", "psu_configuration", "wiring", "service_access"],
        "no_duplicate_psu_per_zone": True,
        "letters_electrical_path": "SEPARATE_PRODUCT — not ACP cavity",
        "legacy_light_routed": "PARALLEL_LEGACY_COST_PATH — reference only",
    }
