"""Operational skill and workcenter catalog — stable codes for registry UI.

Read-only reference data. Does NOT touch CostEngine or pricing workcenters.
"""
from __future__ import annotations

from typing import Any, Dict, List

OPERATIONAL_SKILLS: List[Dict[str, str]] = [
    {"skill_code": "SK_GRAPHIC_DESIGN", "label_ro": "Grafician", "category": "design"},
    {"skill_code": "SK_QUOTING", "label_ro": "Ofertare", "category": "commercial"},
    {"skill_code": "SK_PRINT_OPERATOR", "label_ro": "Operator Imprimantă", "category": "production"},
    {"skill_code": "SK_LAMINATOR_OPERATOR", "label_ro": "Operator Laminator", "category": "production"},
    {"skill_code": "SK_CUTTER_OPERATOR", "label_ro": "Operator Cutter Plotter", "category": "production"},
    {"skill_code": "SK_CNC_OPERATOR", "label_ro": "CNC", "category": "production"},
    {"skill_code": "SK_CNC_PREP", "label_ro": "Pregătire materiale CNC", "category": "production"},
    {"skill_code": "SK_LETTER_CANT_OPERATOR", "label_ro": "Operator CNC cant litere", "category": "production"},
    {"skill_code": "SK_LETTER_MODELING", "label_ro": "Modelare cant litere", "category": "production"},
    {"skill_code": "SK_LOCKSMITH", "label_ro": "Lăcătuș", "category": "production"},
    {"skill_code": "SK_ASSEMBLY", "label_ro": "Ansamblare", "category": "production"},
    {"skill_code": "SK_VINYL_APPLICATOR", "label_ro": "Colantator", "category": "production"},
    {"skill_code": "SK_ELECTRICIAN", "label_ro": "Electrician", "category": "production"},
    {"skill_code": "SK_FIELD_INSTALLER", "label_ro": "Montator", "category": "field"},
    {"skill_code": "SK_COMMERCIAL_TECH", "label_ro": "Director comercial / tehnic", "category": "management"},
]

OPERATIONAL_WORKCENTERS: List[Dict[str, str]] = [
    {"workcenter_code": "WC_PREPRESS", "label_ro": "Grafică / Prepress", "category": "design"},
    {"workcenter_code": "WC_PRINT", "label_ro": "Print", "category": "production"},
    {"workcenter_code": "WC_LAMINATE", "label_ro": "Laminare", "category": "production"},
    {"workcenter_code": "WC_CUT", "label_ro": "Cutter plotter", "category": "production"},
    {"workcenter_code": "WC_CNC_ROUTING", "label_ro": "CNC router", "category": "production"},
    {"workcenter_code": "WC_LASER_CUTTING", "label_ro": "Laser", "category": "production"},
    {"workcenter_code": "WC_LETTER_FORMING", "label_ro": "Modelare cant litere", "category": "production"},
    {"workcenter_code": "WC_METAL_FAB", "label_ro": "Sudură", "category": "production"},
    {"workcenter_code": "WC_METAL_CUTTING", "label_ro": "Debitare metal", "category": "production"},
    {"workcenter_code": "WC_ASSEMBLY", "label_ro": "Ansamblare", "category": "production"},
    {"workcenter_code": "WC_VINYL_APPLICATION", "label_ro": "Colantare", "category": "production"},
    {"workcenter_code": "WC_LED_ASSEMBLY", "label_ro": "Electric", "category": "production"},
    {"workcenter_code": "WC_FIELD_INSTALLATION", "label_ro": "Montaj teren", "category": "field"},
    {"workcenter_code": "WC_STYRO_CUTTING", "label_ro": "Debitare polistiren", "category": "production"},
]

# Suggested ProductSystem alias → registry operation_code (admin reference only).
SUGGESTED_OPERATION_ALIASES: Dict[str, str] = {
  # TPL-VOLUMETRIC-LETTERS ProductSystem operation codes
    "vector_prep": "prepress",
    "face_cnc_cut": "cnc_cutting",
    "back_cut": "cnc_cutting",
    "mounting_template_cnc_cut": "cnc_cutting",
    "side_forming": "cant_modelare",
    "return_face_bonding": "welding",
    "vinyl_application": "colantare",
    "led_install_letters": "montaj_led",
    "electrical_letters": "montaj_led",
    "assembly_letters": "assembly",
    "painting": "assembly",
    "qc_letters": "quality_control",
    "packaging_letters": "packaging",
    "print_roll": "print_roll",
    "cutter_plotter": "cutter_plotter",
    "laminare": "laminare",
    "prepress": "prepress",
    # Execution / canonical task types (OperatorView)
    "file_preparation": "prepress",
    "cnc_routing": "cnc_cutting",
    "edge_bending": "cant_modelare",
    "vinyl_cutting": "colantare",
    "led_assembly": "montaj_led",
    "led_wiring": "montaj_led",
    "volumetric_letter_assembly": "assembly",
    "quality_control": "quality_control",
    "packaging": "packaging",
    "installation_onsite": "field_installation",
    "print_large_format": "print",
    "laminating": "laminare",
}


def get_operational_catalog() -> Dict[str, Any]:
    return {
        "skills": OPERATIONAL_SKILLS,
        "workcenters": OPERATIONAL_WORKCENTERS,
        "suggested_operation_aliases": SUGGESTED_OPERATION_ALIASES,
        "authorization_modes": ["skill", "explicit", "hybrid"],
    }
