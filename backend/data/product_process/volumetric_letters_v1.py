"""Declarative component + interface contracts for litere volumetrice luminoase.

Authority: local truth on components; cross-component truth on interfaces;
Product Template composes (see PRODUCT_COMPOSITION). No Process Template parallel.
"""

from __future__ import annotations

from typing import Any

CONTRACT_VERSION = "product_process/volumetric_letters/v1"
PRODUCT_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS_v2"

# Component codes (stable identity for this pilot)
COMP_FACE = "FACE"
COMP_CANT = "CANT"
COMP_BACK = "BACK"
COMP_LIGHTING = "LIGHTING"
COMP_METAL_SUPPORT = "METAL_SUPPORT"
COMP_ALUCOBOND = "ALUCOBOND_CASED_PANEL"
COMP_TEMPLATE = "INSTALLATION_TEMPLATE"

IFACE_FACE_CANT = "FACE_CANT"
IFACE_BACK_LIGHTING = "BACK_LIGHTING"
IFACE_BACK_SUPPORT = "BACK_SUPPORT"
IFACE_LIGHTING_SUPPORT = "LIGHTING_SUPPORT"
IFACE_BODY_BACK = "BODY_BACK"


def _proc(
    process_code: str,
    *,
    requires_states: list[str] | None = None,
    produces_states: list[str] | None = None,
    depends_on: list[str] | None = None,
    material_roles: list[str] | None = None,
    required_capabilities: list[str] | None = None,
    active_when: dict[str, Any] | None = None,
    parallel_group: str | None = None,
) -> dict[str, Any]:
    return {
        "process_code": process_code,
        "requires_states": list(requires_states or []),
        "produces_states": list(produces_states or []),
        "depends_on": list(depends_on or []),
        "material_roles": list(material_roles or []),
        "required_capabilities": list(required_capabilities or []),
        "active_when": dict(active_when or {}),
        "parallel_group": parallel_group,
    }


COMPONENT_CONTRACTS: dict[str, dict[str, Any]] = {
    COMP_FACE: {
        "component_code": COMP_FACE,
        "processes": [
            _proc(
                "CUT_FACE",
                requires_states=["GEOMETRY_CONFIRMED"],
                produces_states=["FACE_READY"],
                material_roles=["FACE_SHEET"],
                required_capabilities=["CNC_ROUTER_CUTTING"],
                parallel_group="cut_parallel",
            ),
        ],
    },
    COMP_CANT: {
        "component_code": COMP_CANT,
        "processes": [
            _proc(
                "PREPARE_CANT_STRIP",
                requires_states=["GEOMETRY_CONFIRMED"],
                produces_states=["CANT_STRIP_READY"],
                material_roles=["CANT_STRIP"],
                parallel_group="cut_parallel",
            ),
            _proc(
                "APPLY_CANT_VINYL",
                requires_states=["CANT_STRIP_READY"],
                produces_states=["CANT_VINYLED"],
                depends_on=["PREPARE_CANT_STRIP"],
                material_roles=["CANT_VINYL"],
                required_capabilities=["VINYL_APPLICATION"],
                active_when={"cant_finish": "vinyl"},
            ),
            _proc(
                "FORM_CANT_CNC",
                requires_states=["CANT_STRIP_READY"],
                produces_states=["CANT_FORMED"],
                # vinyl branch: also requires CANT_VINYLED (enforced via depends_on injection)
                depends_on=["PREPARE_CANT_STRIP"],
                required_capabilities=["CNC_CANT_FORMING"],
            ),
        ],
    },
    COMP_BACK: {
        "component_code": COMP_BACK,
        "processes": [
            _proc(
                "CUT_FOREX_BACK",
                requires_states=["GEOMETRY_CONFIRMED"],
                produces_states=["BACK_FOREX_READY"],
                material_roles=["BACK_FOREX"],
                required_capabilities=["CNC_ROUTER_CUTTING"],
                parallel_group="cut_parallel",
            ),
        ],
    },
    COMP_LIGHTING: {
        "component_code": COMP_LIGHTING,
        "processes": [
            _proc(
                "INSTALL_LED_MODULES",
                requires_states=["BACK_FOREX_READY", "LED_LAYOUT_CONFIRMED"],
                produces_states=["LED_MODULES_FIXED"],
                material_roles=[
                    "LED_MODULE",
                    "CYANOACRYLATE_ADHESIVE",
                    "CYANOACRYLATE_ACTIVATOR",
                ],
                required_capabilities=["ELECTRICAL_ASSEMBLY"],
            ),
            _proc(
                "WIRE_LED_MODULES",
                requires_states=["LED_MODULES_FIXED"],
                produces_states=[],
                depends_on=["INSTALL_LED_MODULES"],
                material_roles=["ELECTRICAL_WIRE"],
                required_capabilities=["ELECTRICAL_ASSEMBLY"],
            ),
            _proc(
                "ROUTE_CABLES_THROUGH_BACK",
                requires_states=["LED_MODULES_FIXED"],
                produces_states=["LOCAL_ELECTRICAL_READY"],
                depends_on=["WIRE_LED_MODULES"],
                required_capabilities=["ELECTRICAL_ASSEMBLY"],
            ),
            _proc(
                "TEST_LED_ON",
                requires_states=["LOCAL_ELECTRICAL_READY"],
                produces_states=["ALL_LED_MODULES_ON"],
                depends_on=["ROUTE_CABLES_THROUGH_BACK"],
                required_capabilities=["QUALITY_INSPECTION"],
            ),
            _proc(
                "TEST_LIGHT_UNIFORMITY",
                requires_states=["LETTER_CLOSED", "ALL_LED_MODULES_ON"],
                produces_states=["LIGHT_UNIFORMITY_ACCEPTED"],
                depends_on=["ATTACH_BODY_TO_BACK", "TEST_LED_ON"],
                required_capabilities=["QUALITY_INSPECTION"],
            ),
        ],
    },
    COMP_METAL_SUPPORT: {
        "component_code": COMP_METAL_SUPPORT,
        "processes": [
            _proc(
                "FABRICATE_METAL_SUPPORT",
                produces_states=["METAL_SUPPORT_READY"],
                material_roles=["METAL_PROFILE"],
                required_capabilities=["METAL_PROFILE_CUTTING", "METAL_WELDING"],
                parallel_group="support_fab",
            ),
            _proc(
                "ATTACH_BACKS_TO_SUPPORT",
                requires_states=["BACK_FOREX_READY", "METAL_SUPPORT_READY"],
                produces_states=["BACKS_ATTACHED_TO_SUPPORT"],
                depends_on=["FABRICATE_METAL_SUPPORT", "CUT_FOREX_BACK"],
                material_roles=["SMALL_SERVICE_SCREWS"],
            ),
            _proc(
                "INSTALL_CABLE_CHANNEL",
                requires_states=["BACKS_ATTACHED_TO_SUPPORT", "LOCAL_ELECTRICAL_READY"],
                produces_states=[],
                depends_on=["ATTACH_BACKS_TO_SUPPORT", "ROUTE_CABLES_THROUGH_BACK"],
                material_roles=["CABLE_CHANNEL"],
            ),
            _proc(
                "CONNECT_LETTERS",
                requires_states=["BACKS_ATTACHED_TO_SUPPORT"],
                produces_states=["ASSEMBLY_WIRING_COMPLETE"],
                depends_on=["INSTALL_CABLE_CHANNEL"],
                material_roles=["ELECTRICAL_WIRE"],
                required_capabilities=["ELECTRICAL_ASSEMBLY"],
            ),
            _proc(
                "INSTALL_POWER_SUPPLY",
                requires_states=["ASSEMBLY_WIRING_COMPLETE"],
                produces_states=["POWER_SUPPLY_INSTALLED"],
                depends_on=["CONNECT_LETTERS"],
                material_roles=["POWER_SUPPLY"],
            ),
            _proc(
                "INSTALL_MAINS_CABLE",
                requires_states=["POWER_SUPPLY_INSTALLED"],
                produces_states=["MAINS_CABLE_INSTALLED"],
                depends_on=["INSTALL_POWER_SUPPLY"],
                material_roles=["MAINS_CABLE"],
                active_when={"mains_cable_selected": True},
            ),
        ],
    },
    COMP_ALUCOBOND: {
        "component_code": COMP_ALUCOBOND,
        "processes": [
            _proc(
                "FABRICATE_ALUCOBOND_CASED_PANEL",
                produces_states=["ALUCOBOND_SUPPORT_READY"],
                material_roles=["ALUCOBOND_PANEL"],
                required_capabilities=["ALUCOBOND_PANEL_FABRICATION"],
                parallel_group="support_fab",
            ),
            _proc(
                "ATTACH_BACKS_TO_SUPPORT",
                requires_states=["BACK_FOREX_READY", "ALUCOBOND_SUPPORT_READY"],
                produces_states=["BACKS_ATTACHED_TO_SUPPORT"],
                depends_on=["FABRICATE_ALUCOBOND_CASED_PANEL", "CUT_FOREX_BACK"],
                material_roles=["SMALL_SERVICE_SCREWS"],
            ),
            _proc(
                "ROUTE_WIRING_BEHIND_PANEL",
                requires_states=["BACKS_ATTACHED_TO_SUPPORT", "LOCAL_ELECTRICAL_READY"],
                produces_states=[],
                depends_on=["ATTACH_BACKS_TO_SUPPORT", "ROUTE_CABLES_THROUGH_BACK"],
                required_capabilities=["ELECTRICAL_ASSEMBLY"],
            ),
            _proc(
                "CONNECT_LETTERS",
                requires_states=["BACKS_ATTACHED_TO_SUPPORT"],
                produces_states=["ASSEMBLY_WIRING_COMPLETE"],
                depends_on=["ROUTE_WIRING_BEHIND_PANEL"],
                material_roles=["ELECTRICAL_WIRE"],
                required_capabilities=["ELECTRICAL_ASSEMBLY"],
            ),
            _proc(
                "INSTALL_POWER_SUPPLY_NEAR_SERVICE_CORNER",
                requires_states=["ASSEMBLY_WIRING_COMPLETE"],
                produces_states=["POWER_SUPPLY_INSTALLED"],
                depends_on=["CONNECT_LETTERS"],
                material_roles=["POWER_SUPPLY"],
                active_when={"service_corner_required": True},
            ),
            _proc(
                "INSTALL_MAINS_CABLE",
                requires_states=["POWER_SUPPLY_INSTALLED"],
                produces_states=["MAINS_CABLE_INSTALLED"],
                depends_on=["INSTALL_POWER_SUPPLY_NEAR_SERVICE_CORNER"],
                material_roles=["MAINS_CABLE"],
                active_when={"mains_cable_selected": True},
            ),
        ],
    },
    COMP_TEMPLATE: {
        "component_code": COMP_TEMPLATE,
        "processes": [
            _proc(
                "GENERATE_INSTALLATION_TEMPLATE",
                requires_states=["GEOMETRY_CONFIRMED"],
                produces_states=["TEMPLATE_READY"],
                material_roles=["INSTALLATION_TEMPLATE_MEDIA"],
                required_capabilities=["LARGE_FORMAT_PRINT_OR_PLOT"],
                parallel_group="template",
                active_when={"template_selected": True},
            ),
        ],
    },
}


INTERFACE_CONTRACTS: dict[str, dict[str, Any]] = {
    IFACE_FACE_CANT: {
        "interface_code": IFACE_FACE_CANT,
        "requires_components": [COMP_FACE, COMP_CANT],
        "processes": [
            _proc(
                "BOND_FACE_TO_CANT",
                requires_states=["FACE_READY", "CANT_FORMED"],
                produces_states=["LETTER_BODY_READY"],
                depends_on=["CUT_FACE", "FORM_CANT_CNC"],
                material_roles=["CYANOACRYLATE_ADHESIVE", "CYANOACRYLATE_ACTIVATOR"],
            ),
            # RAL branch owned at interface after bond (cross-finish, not cant-local alone)
            _proc(
                "PREPARE_VOLUME_FOR_PAINT",
                requires_states=["LETTER_BODY_READY"],
                produces_states=[],
                depends_on=["BOND_FACE_TO_CANT"],
                active_when={"cant_finish": "ral"},
            ),
            _proc(
                "MASK_FACE",
                requires_states=["LETTER_BODY_READY"],
                produces_states=[],
                depends_on=["PREPARE_VOLUME_FOR_PAINT"],
                active_when={"cant_finish": "ral"},
            ),
            _proc(
                "PAINT_VOLUME_RAL",
                requires_states=["LETTER_BODY_READY"],
                produces_states=[],
                depends_on=["MASK_FACE"],
                material_roles=["RAL_PAINT"],
                required_capabilities=["PAINT_APPLICATION"],
                active_when={"cant_finish": "ral"},
            ),
            _proc(
                "DRY_VOLUME_PAINT",
                depends_on=["PAINT_VOLUME_RAL"],
                active_when={"cant_finish": "ral"},
            ),
            _proc(
                "UNMASK_FACE",
                depends_on=["DRY_VOLUME_PAINT"],
                active_when={"cant_finish": "ral"},
            ),
            _proc(
                "INSPECT_VOLUME_FINISH",
                produces_states=["VOLUME_FINISH_READY"],
                depends_on=["UNMASK_FACE"],
                required_capabilities=["QUALITY_INSPECTION"],
                active_when={"cant_finish": "ral"},
            ),
        ],
    },
    IFACE_BACK_LIGHTING: {
        "interface_code": IFACE_BACK_LIGHTING,
        "requires_components": [COMP_BACK, COMP_LIGHTING],
        "processes": [],  # wiring owned on LIGHTING; interface marks coupling
        "coupling_notes": [
            "INSTALL_LED_MODULES requires BACK_FOREX_READY + LED_LAYOUT_CONFIRMED",
            "LED fixative = own tape + CYANOACRYLATE_ADHESIVE + CYANOACRYLATE_ACTIVATOR",
        ],
    },
    IFACE_BACK_SUPPORT: {
        "interface_code": IFACE_BACK_SUPPORT,
        "requires_components_any": [COMP_METAL_SUPPORT, COMP_ALUCOBOND],
        "also_requires": [COMP_BACK],
        "processes": [],
    },
    IFACE_LIGHTING_SUPPORT: {
        "interface_code": IFACE_LIGHTING_SUPPORT,
        "requires_components_any": [COMP_METAL_SUPPORT, COMP_ALUCOBOND],
        "also_requires": [COMP_LIGHTING],
        "processes": [],
        "coupling_notes": [
            "Metal: channel + PSU on assembly; Alucobond: hidden wiring + service corner PSU",
        ],
    },
    IFACE_BODY_BACK: {
        "interface_code": IFACE_BODY_BACK,
        "requires_components": [COMP_FACE, COMP_CANT, COMP_BACK],
        "processes": [
            _proc(
                "ATTACH_BODY_TO_BACK",
                requires_states=["LETTER_BODY_READY", "BACK_FOREX_READY", "ALL_LED_MODULES_ON"],
                produces_states=["LETTER_CLOSED", "LETTER_SERVICEABLE"],
                depends_on=["TEST_LED_ON", "BOND_FACE_TO_CANT"],
                material_roles=["SMALL_SERVICE_SCREWS"],
            ),
            _proc(
                "PAINT_FASTENERS",
                requires_states=["LETTER_CLOSED"],
                depends_on=["ATTACH_BODY_TO_BACK"],
                material_roles=["FASTENER_PAINT"],
                active_when={"screw_finish": "PAINTED_TO_MATCH_CANT"},
            ),
        ],
    },
}


# Product-level shared processes (composition, not component-local copy)
PRODUCT_SHARED_PROCESSES: list[dict[str, Any]] = [
    _proc(
        "ANALYZE_SVG",
        parallel_group="prep",
    ),
    _proc(
        "CONFIRM_GEOMETRY",
        produces_states=["GEOMETRY_CONFIRMED"],
        depends_on=["ANALYZE_SVG"],
        parallel_group="prep",
    ),
    _proc(
        "QUALITY_CONTROL",
        requires_states=["LIGHT_UNIFORMITY_ACCEPTED"],
        produces_states=["PRODUCT_QC_PASSED"],
        depends_on=["TEST_LIGHT_UNIFORMITY"],
        required_capabilities=["QUALITY_INSPECTION"],
    ),
    _proc(
        "CLEAN_PRODUCT",
        depends_on=["QUALITY_CONTROL"],
    ),
    _proc(
        "PACK_PRODUCT",
        requires_states=["PRODUCT_QC_PASSED"],
        produces_states=["READY_FOR_DELIVERY"],
        depends_on=["CLEAN_PRODUCT"],
        material_roles=["PACKAGING_MATERIAL"],
        required_capabilities=["PACKAGING"],
    ),
]


NO_SUPPORT_EXTRA_PROCESSES: list[dict[str, Any]] = [
    _proc(
        "RIGIDIZE_FOR_TRANSPORT",
        requires_states=["LETTER_CLOSED"],
        produces_states=["TRANSPORT_RIGIDIZED"],
        depends_on=["TEST_LIGHT_UNIFORMITY"],
    ),
    _proc(
        "LABEL_POWER_SUPPLY",
        produces_states=["POWER_SUPPLY_LABELED"],
        material_roles=["POWER_SUPPLY"],
        depends_on=["TEST_LIGHT_UNIFORMITY"],
    ),
    _proc(
        "PACK_POWER_SUPPLY_SEPARATELY",
        requires_states=["POWER_SUPPLY_LABELED"],
        produces_states=["POWER_SUPPLY_PACKED_SEPARATELY"],
        depends_on=["LABEL_POWER_SUPPLY"],
        material_roles=["PACKAGING_MATERIAL", "POWER_SUPPLY"],
        required_capabilities=["PACKAGING"],
    ),
]


PRODUCT_COMPOSITION: dict[str, Any] = {
    "product_template_code": PRODUCT_TEMPLATE_CODE,
    "contract_version": CONTRACT_VERSION,
    "components": list(COMPONENT_CONTRACTS.keys()),
    "interfaces": list(INTERFACE_CONTRACTS.keys()),
}
