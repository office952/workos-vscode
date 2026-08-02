"""Shared process / state / capability / material-role vocabulary (no DB registry)."""

from __future__ import annotations

CATALOG_VERSION = "product_process_catalog/v1"

# --- States (minimal; no adhesive curing, no back drilling) ---
STATE_CODES: frozenset[str] = frozenset(
    {
        "GEOMETRY_CONFIRMED",
        "FACE_READY",
        "CANT_STRIP_READY",
        "CANT_VINYLED",
        "CANT_FORMED",
        "LETTER_BODY_READY",
        "VOLUME_FINISH_READY",
        "BACK_FOREX_READY",
        "LED_LAYOUT_CONFIRMED",
        "LED_MODULES_FIXED",
        "LOCAL_ELECTRICAL_READY",
        "METAL_SUPPORT_READY",
        "ALUCOBOND_SUPPORT_READY",
        "BACKS_ATTACHED_TO_SUPPORT",
        "ASSEMBLY_WIRING_COMPLETE",
        "POWER_SUPPLY_INSTALLED",
        "MAINS_CABLE_INSTALLED",
        "ALL_LED_MODULES_ON",
        "LETTER_CLOSED",
        "LETTER_SERVICEABLE",
        "LIGHT_UNIFORMITY_ACCEPTED",
        "TEMPLATE_READY",
        "POWER_SUPPLY_LABELED",
        "POWER_SUPPLY_PACKED_SEPARATELY",
        "PRODUCT_QC_PASSED",
        "READY_FOR_DELIVERY",
        "TRANSPORT_RIGIDIZED",
    }
)

# --- Material roles (map to existing material registry at Aggregate/BOM — not SKUs here) ---
MATERIAL_ROLE_CODES: frozenset[str] = frozenset(
    {
        "FACE_SHEET",
        "CANT_STRIP",
        "BACK_FOREX",
        "FACE_VINYL",
        "CANT_VINYL",
        "RAL_PAINT",
        "CYANOACRYLATE_ADHESIVE",
        "CYANOACRYLATE_ACTIVATOR",
        "LED_MODULE",
        "ELECTRICAL_WIRE",
        "CABLE_CHANNEL",
        "POWER_SUPPLY",
        "MAINS_CABLE",
        "METAL_PROFILE",
        "ALUCOBOND_PANEL",
        "SMALL_SERVICE_SCREWS",
        "FASTENER_PAINT",
        "INSTALLATION_TEMPLATE_MEDIA",
        "PACKAGING_MATERIAL",
    }
)

# --- Capabilities (machines registry resolves concrete equipment) ---
CAPABILITY_CODES: frozenset[str] = frozenset(
    {
        "CNC_ROUTER_CUTTING",
        "CNC_CANT_FORMING",
        "VINYL_APPLICATION",
        "PAINT_APPLICATION",
        "METAL_PROFILE_CUTTING",
        "METAL_WELDING",
        "ALUCOBOND_PANEL_FABRICATION",
        "ELECTRICAL_ASSEMBLY",
        "LARGE_FORMAT_PRINT_OR_PLOT",
        "QUALITY_INSPECTION",
        "PACKAGING",
    }
)

# --- Process codes (letters pilot minimum) ---
PROCESS_CODES: frozenset[str] = frozenset(
    {
        "ANALYZE_SVG",
        "CONFIRM_GEOMETRY",
        "CUT_FACE",
        "PREPARE_CANT_STRIP",
        "APPLY_CANT_VINYL",
        "FORM_CANT_CNC",
        "BOND_FACE_TO_CANT",
        "PREPARE_VOLUME_FOR_PAINT",
        "MASK_FACE",
        "PAINT_VOLUME_RAL",
        "DRY_VOLUME_PAINT",
        "UNMASK_FACE",
        "INSPECT_VOLUME_FINISH",
        "CUT_FOREX_BACK",
        "INSTALL_LED_MODULES",
        "WIRE_LED_MODULES",
        "ROUTE_CABLES_THROUGH_BACK",
        "FABRICATE_METAL_SUPPORT",
        "FABRICATE_ALUCOBOND_CASED_PANEL",
        "ATTACH_BACKS_TO_SUPPORT",
        "INSTALL_CABLE_CHANNEL",
        "CONNECT_LETTERS",
        "ROUTE_WIRING_BEHIND_PANEL",
        "INSTALL_POWER_SUPPLY",
        "INSTALL_POWER_SUPPLY_NEAR_SERVICE_CORNER",
        "INSTALL_MAINS_CABLE",
        "TEST_LED_ON",
        "ATTACH_BODY_TO_BACK",
        "PAINT_FASTENERS",
        "TEST_LIGHT_UNIFORMITY",
        "GENERATE_INSTALLATION_TEMPLATE",
        "LABEL_POWER_SUPPLY",
        "PACK_POWER_SUPPLY_SEPARATELY",
        "RIGIDIZE_FOR_TRANSPORT",
        "QUALITY_CONTROL",
        "CLEAN_PRODUCT",
        "PACK_PRODUCT",
    }
)

# Aggregate / CostEngine bridge aliases (do not invent new commercial SKUs).
PROCESS_TO_PRICED_OPERATION: dict[str, str] = {
    "CONFIRM_GEOMETRY": "vector_prep",
    "CUT_FACE": "face_cnc_cut",
    "PREPARE_CANT_STRIP": "side_forming",
    "FORM_CANT_CNC": "side_forming",
    "BOND_FACE_TO_CANT": "return_face_bonding",
    "PAINT_VOLUME_RAL": "painting",
    "APPLY_CANT_VINYL": "vinyl_application",
    "CUT_FOREX_BACK": "back_cut",
    "INSTALL_LED_MODULES": "led_install_letters",
    "WIRE_LED_MODULES": "electrical_letters",
    "ROUTE_CABLES_THROUGH_BACK": "electrical_letters",
    "FABRICATE_METAL_SUPPORT": "assembly_letters",
    "FABRICATE_ALUCOBOND_CASED_PANEL": "assembly_letters",
    "ATTACH_BACKS_TO_SUPPORT": "assembly_letters",
    "INSTALL_CABLE_CHANNEL": "electrical_letters",
    "CONNECT_LETTERS": "electrical_letters",
    "ROUTE_WIRING_BEHIND_PANEL": "electrical_letters",
    "INSTALL_POWER_SUPPLY": "electrical_letters",
    "INSTALL_POWER_SUPPLY_NEAR_SERVICE_CORNER": "electrical_letters",
    "INSTALL_MAINS_CABLE": "electrical_letters",
    "TEST_LED_ON": "qc_letters",
    "ATTACH_BODY_TO_BACK": "assembly_letters",
    "TEST_LIGHT_UNIFORMITY": "qc_letters",
    "GENERATE_INSTALLATION_TEMPLATE": "mounting_template_cnc_cut",
    "QUALITY_CONTROL": "qc_letters",
    "CLEAN_PRODUCT": "packaging_letters",
    "RIGIDIZE_FOR_TRANSPORT": "packaging_letters",
    "LABEL_POWER_SUPPLY": "packaging_letters",
    "PACK_PRODUCT": "packaging_letters",
    "PACK_POWER_SUPPLY_SEPARATELY": "packaging_letters",
}

# Analytical / desktop-boundary processes — never become EP operational tasks.
# DEC-001: WorkOS must not operationalize SVG/DWG geometry analysis.
NON_OPERATIONAL_PROCESS_CODES: frozenset[str] = frozenset(
    {
        "ANALYZE_SVG",
        "SVG_GEOMETRY_ANALYSIS",
        "SVG_GEOMETRY_READINESS_GATE",
        "GEOMETRY_INPUTS_READINESS_GATE",
    }
)

# DEC-002 = A — BOM-only by default. May appear on Aggregate operations[] for BOM
# truth, but must not become task_rules / planned_tasks / materialization candidates
# without an explicit frozen activation signal (none exists in repo today).
BOM_ONLY_OPERATION_CODES: frozenset[str] = frozenset(
    {
        "PREMOUNT_BAR_PREPARATION",
    }
)


def is_bom_only_operation_code(code: str | None) -> bool:
    raw = str(code or "").strip().upper()
    return bool(raw) and raw in BOM_ONLY_OPERATION_CODES


def premount_activation_signal_present(
    *,
    trigger_condition: str | None = None,
    process_code: str | None = None,
    notes: list[str] | None = None,
) -> bool:
    """Return True only when an explicit canonical activation signal is present.

    F7A.1 research: no Owner-approved activation boolean / frozen field exists for
    ``premount_bar_preparation`` on volumetric letters. Composition of a separate
    metal-premount *child product* is a different path and must not be inferred here.
    """
    del trigger_condition, process_code, notes
    return False


def is_bom_only_without_activation(
    *,
    operation_code: str | None = None,
    priced_operation: str | None = None,
    task_name: str | None = None,
    process_code: str | None = None,
    trigger_condition: str | None = None,
) -> bool:
    """True when code is BOM-only and no activation signal authorizes a task."""
    for raw in (operation_code, priced_operation, task_name, process_code):
        if is_bom_only_operation_code(raw):
            return not premount_activation_signal_present(
                trigger_condition=trigger_condition,
                process_code=process_code,
            )
    return False

PROCESS_TO_MINI_MODULE: dict[str, str] = {
    "CONFIRM_GEOMETRY": "geometry_svg",
    "ANALYZE_SVG": "geometry_svg",
    "CUT_FACE": "debitare_fata",
    "PREPARE_CANT_STRIP": "modelare_cant",
    "APPLY_CANT_VINYL": "modelare_cant",
    "FORM_CANT_CNC": "modelare_cant",
    "BOND_FACE_TO_CANT": "modelare_cant",
    "MASK_FACE": "finisaje",
    "PAINT_VOLUME_RAL": "finisaje",
    "DRY_VOLUME_PAINT": "finisaje",
    "UNMASK_FACE": "finisaje",
    "INSPECT_VOLUME_FINISH": "finisaje",
    "PREPARE_VOLUME_FOR_PAINT": "finisaje",
    "CUT_FOREX_BACK": "debitare_spate",
    "INSTALL_LED_MODULES": "sistem_led",
    "WIRE_LED_MODULES": "sistem_led",
    "ROUTE_CABLES_THROUGH_BACK": "sistem_led",
    "FABRICATE_METAL_SUPPORT": "structura_suport",
    "FABRICATE_ALUCOBOND_CASED_PANEL": "structura_suport",
    "ATTACH_BACKS_TO_SUPPORT": "structura_suport",
    "INSTALL_CABLE_CHANNEL": "structura_suport",
    "CONNECT_LETTERS": "sistem_led",
    "ROUTE_WIRING_BEHIND_PANEL": "sistem_led",
    "INSTALL_POWER_SUPPLY": "sistem_led",
    "INSTALL_POWER_SUPPLY_NEAR_SERVICE_CORNER": "sistem_led",
    "INSTALL_MAINS_CABLE": "sistem_led",
    "TEST_LED_ON": "sistem_led",
    "ATTACH_BODY_TO_BACK": "ambalare_livrare_montaj",
    "PAINT_FASTENERS": "finisaje",
    "TEST_LIGHT_UNIFORMITY": "sistem_led",
    "GENERATE_INSTALLATION_TEMPLATE": "sablon_montaj",
    "LABEL_POWER_SUPPLY": "sistem_led",
    "PACK_POWER_SUPPLY_SEPARATELY": "ambalare_livrare_montaj",
    "RIGIDIZE_FOR_TRANSPORT": "ambalare_livrare_montaj",
    "QUALITY_CONTROL": "ambalare_livrare_montaj",
    "CLEAN_PRODUCT": "ambalare_livrare_montaj",
    "PACK_PRODUCT": "ambalare_livrare_montaj",
}

ALLOWED_MAINS_CABLE_LENGTHS_M: frozenset[float] = frozenset(
    {2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0, 22.5, 25.0}
)

PROCESS_NAMES_RO: dict[str, str] = {
    "ANALYZE_SVG": "Analiză SVG",
    "CONFIRM_GEOMETRY": "Confirmare geometrie",
    "CUT_FACE": "Debitare față",
    "PREPARE_CANT_STRIP": "Pregătire bandă cant",
    "APPLY_CANT_VINYL": "Aplicare folie pe bandă plană",
    "FORM_CANT_CNC": "Formare cant CNC",
    "BOND_FACE_TO_CANT": "Lipire cant–față",
    "PREPARE_VOLUME_FOR_PAINT": "Pregătire volum pentru vopsire",
    "MASK_FACE": "Mascare față",
    "PAINT_VOLUME_RAL": "Vopsire cant/volum RAL",
    "DRY_VOLUME_PAINT": "Uscare vopsea",
    "UNMASK_FACE": "Îndepărtare mască",
    "INSPECT_VOLUME_FINISH": "Control finisaj volum",
    "CUT_FOREX_BACK": "Debitare spate Forex",
    "INSTALL_LED_MODULES": "Montare module LED",
    "WIRE_LED_MODULES": "Cablare module LED",
    "ROUTE_CABLES_THROUGH_BACK": "Scoate cabluri prin Forex",
    "FABRICATE_METAL_SUPPORT": "Confectionare bare metalice",
    "FABRICATE_ALUCOBOND_CASED_PANEL": "Fabricare panou Alucobond casetat",
    "ATTACH_BACKS_TO_SUPPORT": "Prindere spate pe suport",
    "INSTALL_CABLE_CHANNEL": "Montare canal cablu",
    "CONNECT_LETTERS": "Legături între litere",
    "ROUTE_WIRING_BEHIND_PANEL": "Traseu cabluri spatele panoului",
    "INSTALL_POWER_SUPPLY": "Montare transformator pe ansamblu",
    "INSTALL_POWER_SUPPLY_NEAR_SERVICE_CORNER": "Montare transformator la colț service",
    "INSTALL_MAINS_CABLE": "Montare cablu alimentare",
    "TEST_LED_ON": "Test aprindere LED",
    "ATTACH_BODY_TO_BACK": "Prindere corp pe spate",
    "PAINT_FASTENERS": "Vopsire suruburi",
    "TEST_LIGHT_UNIFORMITY": "Test uniformitate lumină",
    "GENERATE_INSTALLATION_TEMPLATE": "Generare șablon montaj",
    "LABEL_POWER_SUPPLY": "Etichetare transformator",
    "PACK_POWER_SUPPLY_SEPARATELY": "Ambalare transformator separat",
    "RIGIDIZE_FOR_TRANSPORT": "Rigidizare pentru transport",
    "QUALITY_CONTROL": "Control calitate final",
    "CLEAN_PRODUCT": "Curățare produs",
    "PACK_PRODUCT": "Ambalare produs",
}
