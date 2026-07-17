"""BUILD 4 — Seed 6 real advertising production templates.

Templates:
  1. TPL-BANNER-STANDARD      — Banner publicitar
  2. TPL-PLEXI-PLATE          — Placa plexiglass
  3. TPL-VINYL-STICKER        — Autocolant / sticker
  4. TPL-LIGHTBOX-STANDARD    — Caseta luminoasa
  5. TPL-VOLUMETRIC-LETTERS   — Litere volumetrice
  6. TPL-MESH-EXTERNALIZED    — Mesh externalizat

Canonical rules:
  - Idempotent on template_code — re-running is safe.
  - Additive-only — no existing template is touched.
  - Components use the BUILD 4 extended component types.
  - Operations and materials are hierarchical (Sprint #15 shape).
  - Formula-based lines where quantity depends on user input.
  - Mesh is ALWAYS externalized (ready_for_internal_production=false).
  - No commercial prices invented — cost comes from CostEngine at runtime.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from core.database import db_manager
from core.utf8_text_integrity import assert_no_mojibake
import models  # noqa: F401
from models.product_templates import Product_templates
from models.product_families import Product_families

logger = logging.getLogger(__name__)


def _assert_utf8_clean_tree(node: Any, *, context: str) -> None:
    """Fail fast if template seed text contains confirmed mojibake markers."""
    if isinstance(node, str):
        assert_no_mojibake(node, context=context)
        return
    if isinstance(node, list):
        for i, item in enumerate(node):
            _assert_utf8_clean_tree(item, context=f"{context}[{i}]")
        return
    if isinstance(node, dict):
        for key, value in node.items():
            if key in {"label", "name", "description", "notes", "source_notes"} or isinstance(value, (dict, list, str)):
                _assert_utf8_clean_tree(value, context=f"{context}.{key}")


# ---------------------------------------------------------------------------
# Helper to build hierarchical JSON
# ---------------------------------------------------------------------------
def _comp(
    component_id: str,
    ctype: str,
    name: str,
    operations: List[Dict[str, Any]],
    materials: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "component_id": component_id,
        "type": ctype,
        "name": name,
        "operations": operations,
        "materials": materials,
    }


def _op_static(
    code: str,
    workcenter: str,
    seq: int,
    minutes: int,
    label: str = "",
    *,
    internal_only: bool = False,
    quote_priced: bool = True,
    source_notes: str = "",
) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "code": code,
        "workcenter": workcenter,
        "sequence": seq,
        "estimatedMinutes": minutes,
        "estimated_minutes": minutes,
        "calculation_type": "static",
        "label": label or code,
    }
    if internal_only:
        row["internal_only"] = True
        row["quote_priced"] = False
        row["duration_calibration_only"] = True
    elif not quote_priced:
        row["quote_priced"] = False
        row["duration_calibration_only"] = True
        if source_notes:
            row["source_notes"] = source_notes
    return row


def _op_formula(
    code: str,
    workcenter: str,
    seq: int,
    formula_id: str,
    formula_params: Optional[Dict[str, Any]] = None,
    label: str = "",
    requires_quote_input: Optional[Any] = None,
) -> Dict[str, Any]:
    return {
        "code": code,
        "workcenter": workcenter,
        "sequence": seq,
        "estimatedMinutes": 0,
        "estimated_minutes": 0,
        "calculation_type": "formula_based",
        "formula_id": formula_id,
        "formula_params": formula_params or {},
        "requires_quote_input": True if requires_quote_input is None else requires_quote_input,
        "label": label or code,
    }


def _mat_static(
    code: str,
    unit: str,
    qty: float,
    label: str = "",
) -> Dict[str, Any]:
    return {
        "materialCode": code,
        "material_code": code,
        "unit": unit,
        "quantity": qty,
        "calculation_type": "static",
        "label": label or code,
    }


def _mat_formula(
    code: str,
    unit: str,
    formula_id: str,
    formula_params: Optional[Dict[str, Any]] = None,
    label: str = "",
    requires_quote_input: Optional[Any] = None,
) -> Dict[str, Any]:
    return {
        "materialCode": code,
        "material_code": code,
        "unit": unit,
        "quantity": 0,
        "calculation_type": "formula_based",
        "formula_id": formula_id,
        "formula_params": formula_params or {},
        "requires_quote_input": True if requires_quote_input is None else requires_quote_input,
        "label": label or code,
    }


# ---------------------------------------------------------------------------
# TEMPLATE 1: Banner publicitar
# ---------------------------------------------------------------------------
def _banner_components() -> List[Dict[str, Any]]:
    return [
        _comp(
            "comp_print_substrate",
            "PRINT_SUBSTRATE",
            "Substrat banner — imprimare",
            operations=[
                _op_static("prepress", "PREPRESS", 1, 30, "Pregătire fișier print"),
                _op_formula(
                    "print_large_format", "LARGE_FORMAT_PRINT", 2,
                    "area_based_time",
                    {"speed_sqm_per_hour": 12, "setup_minutes": 15},
                    "Imprimare format mare",
                ),
            ],
            materials=[
                _mat_formula(
                    "MAT-BANNER-510", "mp", "area_with_waste",
                    {"waste_pct": 0.05, "roll_widths_mm": [1100, 1350, 1600]},
                    "Banner PVC 510g",
                ),
                _mat_formula(
                    "MAT-INK-ECOSOLVENT", "set", "ink_consumption",
                    {"ml_per_sqm": 12},
                    "Cerneală ecosolvent",
                ),
            ],
        ),
        _comp(
            "comp_finisaj_banner",
            "FINISAJ",
            "Finisare banner — tiv, capse, tăiere",
            operations=[
                _op_formula(
                    "cutting_banner", "PANEL_CUTTING", 3,
                    "perimeter_based_time",
                    {"speed_m_per_min": 2},
                    "Tăiere la dimensiune",
                ),
                _op_formula(
                    "tiv_welding", "WELDING_BANNER", 4,
                    "perimeter_based_time",
                    {"speed_m_per_min": 1.5, "conditional": "tiv_enabled"},
                    "Sudură tiv",
                ),
                _op_formula(
                    "capsare", "CAPSARE", 5,
                    "caps_count_time",
                    {"minutes_per_cap": 0.5, "conditional": "caps_enabled"},
                    "Montaj capse metalice",
                ),
                _op_static("qc_banner", "QC_INSPECTION", 6, 10, "Control calitate"),
                _op_static("packaging_banner", "PACKAGING", 7, 15, "Ambalare"),
            ],
            materials=[
                _mat_formula(
                    "MAT-TIV-BANDA", "ml", "perimeter_material",
                    {"conditional": "tiv_enabled"},
                    "Bandă tiv",
                ),
                _mat_formula(
                    "MAT-CAPSE-METAL", "buc", "caps_count",
                    {"conditional": "caps_enabled", "valid_spacings_cm": [15, 30, 50, 75, 100]},
                    "Capse metalice",
                ),
            ],
        ),
    ]


# ---------------------------------------------------------------------------
# TEMPLATE 2: Placa plexiglass
# ---------------------------------------------------------------------------
def _plexi_components() -> List[Dict[str, Any]]:
    return [
        _comp(
            "comp_plexi_panel",
            "PLEXI_PANEL",
            "Placă plexiglas — tăiere și prelucrare",
            operations=[
                _op_static("prepress_plexi", "PREPRESS", 1, 20, "Pregătire fișier vector"),
                _op_formula(
                    "cnc_laser_cut", "LASER_CUTTING", 2,
                    "perimeter_based_time",
                    {"speed_m_per_min": 0.8},
                    "Tăiere laser/CNC",
                ),
                _op_static("edge_finish", "FINISHING", 3, 20, "Finisare muchii"),
                _op_formula(
                    "drilling", "CNC_ROUTER", 4,
                    "count_based_time",
                    {"minutes_per_hole": 2, "conditional": "holes_enabled"},
                    "Găurire montaj",
                ),
            ],
            materials=[
                _mat_formula(
                    "MAT-PLEXI-TRANSP-3MM", "mp", "sheet_area_nesting",
                    {"waste_pct": 0.10, "thickness_options_mm": [3, 5, 10]},
                    "Plexiglas (implicit transp. 3mm)",
                ),
                _mat_static("MAT-FOLIE-PROTECTIE", "mp", 0, "Folie protecție"),
            ],
        ),
        _comp(
            "comp_vinyl_app_plexi",
            "VINYL_APPLICATION",
            "Aplicare print/vinyl pe plexiglas",
            operations=[
                _op_formula(
                    "print_vinyl_plexi", "LARGE_FORMAT_PRINT", 5,
                    "area_based_time",
                    {"speed_sqm_per_hour": 8, "conditional": "print_or_vinyl_application"},
                    "Print/vinyl aplicare",
                ),
            ],
            materials=[
                _mat_formula(
                    "MAT-VINYL-TRANSPARENT", "mp", "area_with_waste",
                    {"waste_pct": 0.08, "conditional": "print_or_vinyl_application"},
                    "Vinyl transparent printabil",
                ),
            ],
        ),
        _comp(
            "comp_montaj_plexi",
            "FINISAJ",
            "Montaj final — distanțiere, ambalare",
            operations=[
                _op_formula(
                    "spacer_assembly", "ASSEMBLY", 6,
                    "count_based_time",
                    {"minutes_per_spacer": 3, "conditional": "spacers_enabled"},
                    "Montaj distanțiere",
                ),
                _op_static("qc_plexi", "QC_INSPECTION", 7, 10, "Control calitate"),
                _op_static("packaging_plexi", "PACKAGING", 8, 15, "Ambalare"),
            ],
            materials=[
                _mat_formula(
                    "MAT-DISTANTIERE-INOX", "set", "spacer_count",
                    {"conditional": "spacers_enabled"},
                    "Distanțiere inox",
                ),
                _mat_static("MAT-SURUBURI-GEN", "set", 1, "Șuruburi montaj"),
            ],
        ),
    ]


# ---------------------------------------------------------------------------
# TEMPLATE 3: Autocolant / sticker
# ---------------------------------------------------------------------------
def _vinyl_sticker_components() -> List[Dict[str, Any]]:
    return [
        _comp(
            "comp_vinyl_print",
            "VINYL_APPLICATION",
            "Print pe vinyl autoadeziv",
            operations=[
                _op_static("prepress_vinyl", "PREPRESS", 1, 20, "Pregătire fișier"),
                _op_formula(
                    "print_vinyl", "LARGE_FORMAT_PRINT", 2,
                    "area_based_time",
                    {"speed_sqm_per_hour": 10},
                    "Imprimare vinyl",
                ),
            ],
            materials=[
                _mat_formula(
                    "MAT-VINYL-CALANDRAT", "mp", "area_with_waste",
                    {"waste_pct": 0.08, "roll_widths_mm": [1060, 1370, 1520]},
                    "Vinyl calandrat (implicit)",
                ),
                _mat_formula(
                    "MAT-INK-ECOSOLVENT", "set", "ink_consumption",
                    {"ml_per_sqm": 14},
                    "Cerneală ecosolvent",
                ),
            ],
        ),
        _comp(
            "comp_laminare",
            "LAMINARE",
            "Laminare protecție UV",
            operations=[
                _op_formula(
                    "lamination", "LAMINATION", 3,
                    "area_based_time",
                    {"speed_sqm_per_hour": 20, "conditional": "lamination_enabled"},
                    "Laminare",
                ),
            ],
            materials=[
                _mat_formula(
                    "MAT-LAMINARE-MAT", "mp", "area_with_waste",
                    {"waste_pct": 0.05, "conditional": "lamination_enabled"},
                    "Folie laminare mat (implicit)",
                ),
            ],
        ),
        _comp(
            "comp_taiere_contur",
            "TAIERE_CNC_LASER",
            "Tăiere contur și pregătire",
            operations=[
                _op_formula(
                    "contour_cut", "CONTOUR_CUTTING", 4,
                    "perimeter_based_time",
                    {"speed_m_per_min": 0.5, "conditional": "contour_cut_enabled"},
                    "Tăiere contur",
                ),
                _op_static("weeding", "FINISHING", 5, 30, "Weeding (îndepărtare surplus)"),
                _op_formula(
                    "transfer_tape", "FINISHING", 6,
                    "area_based_time",
                    {"speed_sqm_per_hour": 15, "conditional": "transfer_tape_enabled"},
                    "Aplicare bandă transfer",
                ),
            ],
            materials=[
                _mat_formula(
                    "MAT-TRANSFER-TAPE", "mp", "area_with_waste",
                    {"waste_pct": 0.05, "conditional": "transfer_tape_enabled"},
                    "Bandă transfer",
                ),
            ],
        ),
        _comp(
            "comp_finisaj_vinyl",
            "FINISAJ",
            "Control calitate și ambalare",
            operations=[
                _op_static("qc_vinyl", "QC_INSPECTION", 7, 10, "Control calitate"),
                _op_static("packaging_vinyl", "PACKAGING", 8, 10, "Ambalare"),
            ],
            materials=[],
        ),
    ]


# ---------------------------------------------------------------------------
# TEMPLATE 4: Caseta luminoasa
# ---------------------------------------------------------------------------
def _lightbox_components() -> List[Dict[str, Any]]:
    return [
        _comp(
            "comp_frame_lightbox",
            "FRAME_PROFILE",
            "Cadru aluminiu casetă",
            operations=[
                _op_formula(
                    "frame_cutting", "PANEL_CUTTING", 1,
                    "perimeter_based_time",
                    {"speed_m_per_min": 1.0},
                    "Debitare profil cadru",
                ),
                _op_static("frame_assembly", "ASSEMBLY", 2, 60, "Asamblare cadru"),
            ],
            materials=[
                _mat_formula(
                    "MAT-PROFIL-ALU-BOX", "ml", "perimeter_material",
                    {"extra_pct": 0.10},
                    "Profil aluminiu casetă",
                ),
                _mat_static("MAT-SURUBURI-GEN", "set", 1, "Șuruburi asamblare"),
            ],
        ),
        _comp(
            "comp_face_lightbox",
            "PLEXI_PANEL",
            "Față casetă — plexiglas/policarbonat",
            operations=[
                _op_static("prepress_lightbox", "PREPRESS", 3, 30, "Pregătire grafică"),
                _op_formula(
                    "face_cutting", "LASER_CUTTING", 4,
                    "area_based_time",
                    {"speed_sqm_per_hour": 3},
                    "Tăiere față",
                ),
                _op_formula(
                    "face_print", "LARGE_FORMAT_PRINT", 5,
                    "area_based_time",
                    {"speed_sqm_per_hour": 6},
                    "Print pe față",
                ),
            ],
            materials=[
                _mat_formula(
                    "MAT-POLICARBONAT-OPAL", "mp", "area_with_waste",
                    {"waste_pct": 0.08},
                    "Policarbonat opal (implicit)",
                ),
                _mat_formula(
                    "MAT-VINYL-TRANSPARENT", "mp", "area_with_waste",
                    {"waste_pct": 0.05},
                    "Vinyl print față",
                ),
            ],
        ),
        _comp(
            "comp_back_lightbox",
            "STRUCTURA",
            "Panou spate casetă",
            operations=[
                _op_formula(
                    "back_cutting", "PANEL_CUTTING", 6,
                    "area_based_time",
                    {"speed_sqm_per_hour": 5},
                    "Tăiere panou spate",
                ),
            ],
            materials=[
                _mat_formula(
                    "MAT-PANOU-SPATE-ALU", "mp", "area_with_waste",
                    {"waste_pct": 0.05},
                    "Panou spate aluminiu",
                ),
            ],
        ),
        _comp(
            "comp_led_lightbox",
            "ELECTRIC_LED",
            "Sistem iluminare LED",
            operations=[
                _op_formula(
                    "led_mounting", "LED_ASSEMBLY", 7,
                    "area_based_time",
                    {"modules_per_sqm": 25, "minutes_per_module": 1.5},
                    "Montaj module LED",
                ),
                _op_static("electrical_wiring", "ELECTRICAL_WIRING", 8, 45, "Cablaj electric"),
                _op_static("led_testing", "QC_INSPECTION", 9, 15, "Test iluminare"),
            ],
            materials=[
                _mat_formula(
                    "MAT-LED-MODULE", "buc", "led_density_area",
                    {"modules_per_sqm": 25},
                    "Module LED",
                ),
                _mat_formula(
                    "MAT-LED-PSU-12V", "buc", "psu_count",
                    {"watts_per_module": 1.5, "psu_watts": 150},
                    "Surse alimentare LED",
                ),
                _mat_static("MAT-CABLU-ELECTRIC", "set", 1, "Cablu + conectori"),
            ],
        ),
        _comp(
            "comp_finisaj_lightbox",
            "FINISAJ",
            "Asamblare finală și QC",
            operations=[
                _op_static("final_assembly", "ASSEMBLY", 10, 45, "Asamblare finală"),
                _op_static("qc_lightbox", "QC_INSPECTION", 11, 15, "Control calitate"),
                _op_static("packaging_lightbox", "PACKAGING", 12, 20, "Ambalare"),
            ],
            materials=[
                _mat_static("MAT-CONSUMABILE-MONTAJ", "set", 1, "Consumabile montaj"),
            ],
        ),
    ]


# ---------------------------------------------------------------------------
# TEMPLATE 5: Litere volumetrice
# ---------------------------------------------------------------------------
def _volumetric_letters_components() -> List[Dict[str, Any]]:
    return [
        _comp(
            "comp_face_litere",
            "LITERE_3D",
            "Față litere — plexi/acrilic (CNC/laser)",
            operations=[
                _op_formula(
                    "vector_prep", "PREPRESS", 1,
                    "letter_count_material",
                    {},
                    "Pregătire vector / font",
                    requires_quote_input=["letter_count"],
                ),
                _op_formula(
                    "face_cnc_cut", "CNC_ROUTER", 2,
                    "perimeter_pass_linear_meter",
                    {
                        "pass_count": 2,
                        "cut_passes": 1,
                        "bevel_passes": 1,
                        "perimeter_quote_input_key": "cnc_cutting_perimeter_ml",
                        "material": "plexiglas face 3mm",
                        "notes": "1 cut pass + 1 bevel/sanfren pass on CNC cutting perimeter (outer + holes)",
                    },
                    "Tăiere CNC față litere",
                    requires_quote_input=["cnc_cutting_perimeter_ml"],
                ),
                _op_formula(
                    "vinyl_application", "FACE_VINYL_APPLICATION_LABOR", 3,
                    "face_vinyl_used_sqm",
                    {
                        "gate": {"face_finish_type_not": "none"},
                    },
                    "Manoperă aplicare folie fețe litere",
                    requires_quote_input=["letter_face_area_m2"],
                ),
            ],
            materials=[
                _mat_formula(
                    "MAT-ACP-FATA-LITERE", "mp", "letter_face_area",
                    {"waste_pct": 0.15},
                    "Față plexi/acrilic sau ACP; opțional vinyl/oracal/print",
                    requires_quote_input=["letter_face_area_m2"],
                ),
                _mat_formula(
                    "MAT-ORACAL-651", "mp", "face_vinyl_used_sqm",
                    {
                        "gate": {"face_finish_type": "oracal_651"},
                    },
                    "Oracal 651 — autocolant față litere",
                    requires_quote_input=["letter_face_area_m2"],
                ),
                _mat_formula(
                    "MAT-VINYL-PRINT", "mp", "face_vinyl_used_sqm",
                    {
                        "gate": {"face_finish_type": "printed_vinyl"},
                    },
                    "Autocolant print față litere",
                    requires_quote_input=["letter_face_area_m2"],
                ),
                _mat_formula(
                    "MAT-VINYL-PRINT-LAMINATED", "mp", "face_vinyl_used_sqm",
                    {
                        "gate": {"face_finish_type": "printed_laminated_vinyl"},
                    },
                    "Autocolant print + laminare față litere",
                    requires_quote_input=["letter_face_area_m2"],
                ),
            ],
        ),
        _comp(
            "comp_lateral_litere",
            "LITERE_3D",
            "Laterale litere — profil aluminiu (bordură)",
            operations=[
                _op_formula(
                    "side_forming", "RETURN_PROFILE_MACHINE_FORMING", 3,
                    "letter_perimeter",
                    {"extra_pct": 0},
                    "Modelare cant profil — utilaj (EUR/ml serviciu)",
                    requires_quote_input=["letter_perimeter_m"],
                ),
                _op_formula(
                    "return_face_bonding", "RETURN_PROFILE_FACE_BONDING", 4,
                    "letter_perimeter",
                    {"extra_pct": 0, "perimeter_quote_input_key": "return_material_perimeter_ml"},
                    "Lipire cant pe față (EUR/ml serviciu)",
                    requires_quote_input=["return_material_perimeter_ml"],
                ),
            ],
            materials=[
                _mat_formula(
                    "MAT-PROFIL-LATERAL-LITERE", "ml", "letter_perimeter",
                    {"extra_pct": 0.10},
                    "Profil lateral litere",
                    requires_quote_input=["letter_perimeter_m"],
                ),
            ],
        ),
        _comp(
            "comp_spate_litere",
            "STRUCTURA",
            "Spate litere — Forex 10 mm",
            operations=[
                _op_formula(
                    "back_cut", "CNC_ROUTER", 5,
                    "perimeter_pass_linear_meter",
                    {
                        "base_pass_count": 3,
                        "bevel_pass_count": 2,
                        "bevel_quote_input_key": "back_bevel_enabled",
                        "cut_passes": 3,
                        "bevel_passes": 2,
                        "perimeter_quote_input_key": "cnc_cutting_perimeter_ml",
                        "material": "Forex 10mm",
                        "gate": {"backing_present": True},
                        "notes": (
                            "Forex 10mm back: 3 cut passes (10mm/3.5mm ceil); optional "
                            "back_bevel_enabled adds 2 bevel passes (7mm/3.5mm) = 5 total; "
                            "skipped when backing_present is false"
                        ),
                    },
                    "Tăiere CNC spate Forex 10 mm",
                    requires_quote_input=["cnc_cutting_perimeter_ml"],
                ),
            ],
            materials=[
                _mat_formula(
                    "MAT-SPATE-PVC-LITERE", "mp", "letter_face_area",
                    {"waste_pct": 0.10, "gate": {"backing_present": True}},
                    "Forex 10 mm spate litere (cod MAT-SPATE-PVC-LITERE)",
                    requires_quote_input=["letter_face_area_m2"],
                ),
            ],
        ),
        _comp(
            "comp_led_litere",
            "ELECTRIC_LED",
            "Iluminare LED — montaj pe spate Forex",
            operations=[
                _op_formula(
                    "led_install_letters", "LED_ASSEMBLY", 6,
                    "led_module_count",
                    {"conditional": "illumination_enabled"},
                    "Montaj LED per modul",
                    requires_quote_input=["led_module_count"],
                ),
                _op_formula(
                    "electrical_letters", "ELECTRICAL_WIRING", 7,
                    "letter_count_material",
                    {"conditional": "illumination_enabled"},
                    "Cablaj electric litere",
                    requires_quote_input=["letter_count"],
                ),
            ],
            materials=[
                _mat_formula(
                    "MAT-LED-MODULE", "buc", "led_per_letter",
                    {
                        "module_length_mm": 75,
                        "module_gap_mm": 25,
                        "conditional": "illumination_enabled",
                    },
                    "Module LED litere (pitch 75+25 mm pe perimetru)",
                    requires_quote_input=["letter_perimeter_m"],
                ),
                _mat_formula(
                    "MAT-LED-PSU-12V", "buc", "psu_count",
                    {"watts_per_module": 1.5, "psu_watts": 150, "conditional": "illumination_enabled"},
                    "Surse LED litere",
                    requires_quote_input=["led_module_count"],
                ),
            ],
        ),
        _comp(
            "comp_finisaj_litere",
            "FINISAJ",
            "Finisare — vopsire, asamblare, QC",
            operations=[
                _op_formula(
                    "mounting_template_cnc_cut", "CNC_ROUTER", 6,
                    "perimeter_pass_linear_meter",
                    {
                        "pass_count": 1,
                        "cut_passes": 1,
                        "material": "Forex 3mm mounting template",
                        "notes": "Single pass CNC cut for mounting template",
                        "gate": {"mounting_template_material_type": "forex"},
                    },
                    "CNC debitare șablon montaj Forex 3 mm (serviciu separat)",
                    requires_quote_input=["letter_perimeter_m"],
                ),
                _op_formula(
                    "painting", "PAINTING", 7,
                    "letter_perimeter",
                    {
                        "extra_pct": 0,
                        "gate": {"volume_finish": "paint_after_face_miter_bond"},
                    },
                    "Vopsire RAL (serviciu perimetru)",
                    requires_quote_input=["letter_perimeter_m"],
                ),
                _op_static(
                    "assembly_letters",
                    "ASSEMBLY",
                    8,
                    60,
                    "Asamblare litere",
                    quote_priced=False,
                    source_notes=(
                        "Generic assembly is not priced separately for "
                        "TPL-VOLUMETRIC-LETTERS because forming, bonding, "
                        "LED assembly, electrical wiring, painting, and "
                        "packaging are priced explicitly."
                    ),
                ),
                _op_static(
                    "qc_letters",
                    "QC_INSPECTION",
                    9,
                    15,
                    "Control calitate",
                    internal_only=True,
                ),
                _op_formula(
                    "packaging_letters", "PACKAGING", 10,
                    "letter_face_area",
                    {"waste_pct": 0},
                    "Ambalare + șablon",
                    requires_quote_input=["letter_face_area_m2"],
                ),
            ],
            materials=[
                _mat_formula(
                    "MAT-VOPSEA-RAL", "buc", "ceil_quote_input_quantity",
                    {
                        "conditional": "paint_finish",
                        "gate": {"volume_finish": "paint_after_face_miter_bond"},
                        "quote_input_key": "paint_tube_count",
                        "fallback_quote_input_key": "estimated_paint_tubes",
                    },
                    "Vopsea RAL spray — tub (consumabil)",
                    requires_quote_input=[],
                ),
                _mat_formula(
                    "MAT-SABLON-HARTIE", "mp", "letter_face_area",
                    {
                        "waste_pct": 0,
                        "area_quote_input_key": "mounting_template_area_m2",
                        "gate": {"mounting_template_material_type": "paper"},
                    },
                    "Șablon hârtie (material mp; fără CNC Forex)",
                    requires_quote_input=["mounting_template_area_m2"],
                ),
                _mat_formula(
                    "MAT-SABLON-MONTAJ", "mp", "letter_face_area",
                    {
                        "waste_pct": 0,
                        "area_quote_input_key": "mounting_template_area_m2",
                        "gate": {"mounting_template_material_type": "forex"},
                    },
                    "Șablon montaj Forex 3 mm (material mp; CNC separat)",
                    requires_quote_input=["mounting_template_area_m2"],
                ),
                _mat_static("MAT-CONSUMABILE-MONTAJ", "set", 1, "Consumabile"),
            ],
        ),
        _comp(
            "comp_premount_bars",
            "STRUCTURA",
            "Bare premontaj oțel / aluminiu",
            operations=[],
            materials=[
                _mat_formula(
                    "MAT-PREMOUNT-BAR-STEEL", "ml", "mounting_bar_total_length",
                    {
                        "default_bar_count": 2,
                        "gate": {
                            "mounting_system": "steel_bars",
                            "mounting_bar_profile_in": ["30x30x1.5"],
                        },
                    },
                    "Bare premontaj oțel — profil selectabil (30Ã—30Ã—1.5 preț confirmat)",
                    requires_quote_input=[],
                ),
                _mat_formula(
                    "MAT-PREMOUNT-BAR-ALUMINUM", "ml", "mounting_bar_total_length",
                    {
                        "default_bar_count": 2,
                        "gate": {
                            "mounting_system": "aluminum_bars",
                            "mounting_bar_profile_in": ["30x30x1.5"],
                        },
                    },
                    "Bare premontaj aluminiu — profil selectabil (30Ã—30Ã—1.5 preț confirmat)",
                    requires_quote_input=[],
                ),
            ],
        ),
    ]


# ---------------------------------------------------------------------------
# TEMPLATE 6: Mesh externalizat
# ---------------------------------------------------------------------------
def _mesh_externalized_components() -> List[Dict[str, Any]]:
    return [
        _comp(
            "comp_prepress_mesh",
            "PRINT_SUBSTRATE",
            "Pregătire fișier mesh",
            operations=[
                _op_static("prepress_mesh", "PREPRESS", 1, 30, "Pregătire fișier print"),
            ],
            materials=[],
        ),
        _comp(
            "comp_externalizare_mesh",
            "EXTERNALIZARE",
            "Producție externalizată mesh",
            operations=[
                _op_formula(
                    "external_production", "EXTERNAL_SUBCONTRACT", 2,
                    "external_quote_based",
                    {"requires_supplier_quote": True},
                    "Subcontractare producție mesh",
                ),
            ],
            materials=[
                _mat_formula(
                    "MAT-MESH-270", "mp", "area_with_waste",
                    {"waste_pct": 0.05, "external": True},
                    "Mesh perforat (furnizor extern)",
                ),
            ],
        ),
        _comp(
            "comp_finisaj_mesh",
            "FINISAJ",
            "Recepție, QC, tiv/capse, ambalare",
            operations=[
                _op_static("incoming_qc", "QC_INSPECTION", 3, 15, "QC recepție"),
                _op_formula(
                    "tiv_mesh", "WELDING_BANNER", 4,
                    "perimeter_based_time",
                    {"speed_m_per_min": 1.5, "conditional": "tiv_enabled"},
                    "Tiv mesh",
                ),
                _op_formula(
                    "capsare_mesh", "CAPSARE", 5,
                    "caps_count_time",
                    {"minutes_per_cap": 0.5, "conditional": "caps_enabled"},
                    "Capse mesh",
                ),
                _op_static("packaging_mesh", "PACKAGING", 6, 15, "Ambalare"),
            ],
            materials=[
                _mat_formula(
                    "MAT-TIV-BANDA", "ml", "perimeter_material",
                    {"conditional": "tiv_enabled"},
                    "Bandă tiv mesh",
                ),
                _mat_formula(
                    "MAT-CAPSE-METAL", "buc", "caps_count",
                    {"conditional": "caps_enabled", "valid_spacings_cm": [15, 30, 50, 75, 100]},
                    "Capse mesh",
                ),
            ],
        ),
    ]


# ---------------------------------------------------------------------------
# Template definitions
# ---------------------------------------------------------------------------
TEMPLATE_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "template_code": "TPL-BANNER-STANDARD",
        "family_id": "print_large_format",
        "family_name": "Print format mare",
        "description": (
            "Banner publicitar PVC — imprimare ecosolvent/UV format mare, "
            "cu opțiuni tiv, capse, sudură. Role: 1100/1350/1600mm. "
            "Mesh nu se produce intern — se externalizează."
        ),
        "components_fn": _banner_components,
        "estimated_hours": 2.5,
        "base_labor_rate": 80.0,
        "base_margin_pct": 25.0,
        "notes": (
            "Input params: width_mm, height_mm, quantity, banner_material, "
            "print_type, tiv_enabled, tiv_width_mm(30), caps_enabled, "
            "caps_spacing_cm(15/30/50/75/100), reinforced_edges, welding, "
            "delivery_finish. Roll widths: 1100/1350/1600mm."
        ),
    },
    {
        "template_code": "TPL-PLEXI-PLATE",
        "family_id": "plexi_cnc",
        "family_name": "Plexiglass / Debitare CNC",
        "description": (
            "Placă plexiglas — tăiere laser/CNC, finisare muchii, "
            "opțional print/vinyl, distanțiere, găurire. "
            "Tipuri: transparent, alb, opal, colorat. Grosimi: 3/5/10mm."
        ),
        "components_fn": _plexi_components,
        "estimated_hours": 3.0,
        "base_labor_rate": 80.0,
        "base_margin_pct": 30.0,
        "notes": (
            "Input params: width_mm, height_mm, quantity, plexi_type, "
            "thickness_mm, print_or_vinyl_application, edge_finish, "
            "holes_enabled, spacers_enabled, spacer_type, mounting_type, shape."
        ),
    },
    {
        "template_code": "TPL-VINYL-STICKER",
        "family_id": "vinyl_stickers",
        "family_name": "Autocolant / Sticker",
        "description": (
            "Autocolant / sticker — print pe vinyl autoadeziv, "
            "laminare UV opțională, tăiere contur, bandă transfer. "
            "Tipuri vinyl: calandrat, turnat, transparent."
        ),
        "components_fn": _vinyl_sticker_components,
        "estimated_hours": 2.0,
        "base_labor_rate": 80.0,
        "base_margin_pct": 30.0,
        "notes": (
            "Input params: width_mm, height_mm, quantity, vinyl_type, "
            "print_type, lamination_enabled, lamination_type, "
            "contour_cut_enabled, transfer_tape_enabled, "
            "application_surface, indoor_outdoor."
        ),
    },
    {
        "template_code": "TPL-LIGHTBOX-STANDARD",
        "family_id": "casete_luminoase",
        "family_name": "Casete luminoase",
        "description": (
            "Casetă luminoasă cu LED — cadru aluminiu, față plexiglas/"
            "policarbonat, panou spate, module LED, surse alimentare. "
            "Opțiuni: single/double sided, interior/exterior."
        ),
        "components_fn": _lightbox_components,
        "estimated_hours": 8.0,
        "base_labor_rate": 80.0,
        "base_margin_pct": 35.0,
        "notes": (
            "Input params: width_mm, height_mm, depth_mm, quantity, "
            "face_material, frame_type, illumination_type, "
            "single_sided/double_sided, indoor_outdoor, mounting_type, "
            "electrical_requirements."
        ),
    },
    {
        "template_code": "TPL-VOLUMETRIC-LETTERS",
        "family_id": "litere_volumetrice",
        "family_name": "Litere volumetrice",
        "description": (
            "Litere volumetrice 3D — față plexi/acrilic (opțional vinyl/oracal), "
            "bordură profil aluminiu, spate Forex 10 mm. LED pe spate. "
            "Premontaj opțional: perete / structură metalică / panou ACM casetat "
            "(suport separat de spatele literei)."
        ),
        "components_fn": _volumetric_letters_components,
        "estimated_hours": 12.0,
        "base_labor_rate": 80.0,
        "base_margin_pct": 40.0,
        "notes": (
            "Input params: text, font/vector_file, height_mm, depth_mm, "
            "quantity, face_material, side_material, back_material, "
            "illumination(none/frontlit/backlit/halo), mounting_type, "
            "paint_finish, indoor_outdoor. "
            "Straturi producție (ref. docs/production/volumetric-letters-production-layers.md): "
            "față plexi/acrilic tăiat; opțional vinyl/print/oracal; șanfren față opțional/configurabil. "
            "Bordură: profil aluminiu, adâncime configurabilă. "
            "Spate litere: Forex 10 mm (nu PVC/aluminiu generic); șanfren spate opțional/configurabil. "
            "LED: module montate pe spate Forex; cablaj + sursă în strat electric. "
            "Premontaj opțional: structură metalică sau panou Alucobond/ACM casetat — "
            "panoul ACM este suport de montaj, nu spatele literei."
        ),
    },
    {
        "template_code": "TPL-MESH-EXTERNALIZED",
        "family_id": "externalized_print",
        "family_name": "Print externalizat",
        "description": (
            "Mesh publicitar externalizat — NU se produce intern. "
            "Producția este subcontractată la furnizor extern. "
            "Intern: pregătire fișier, recepție QC, tiv/capse opțional, ambalare."
        ),
        "components_fn": _mesh_externalized_components,
        "estimated_hours": 1.5,
        "base_labor_rate": 80.0,
        "base_margin_pct": 20.0,
        "notes": (
            "REGULA CANONICĂ: Mesh nu se produce intern. "
            "Input params: width_mm, height_mm, quantity, mesh_type, "
            "print_quality, tiv_enabled, caps_enabled, "
            "caps_spacing_cm(15/30/50/75/100), supplier_required, "
            "delivery_deadline. ready_for_internal_production=false."
        ),
    },
]


# ---------------------------------------------------------------------------
# Flatten components into operations_json / required_materials_json
# ---------------------------------------------------------------------------
def _flatten_operations(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ops = []
    for comp in components:
        cid = comp["component_id"]
        for op in comp.get("operations", []):
            flat = dict(op)
            flat["component_ref"] = cid
            ops.append(flat)
    return ops


def _flatten_materials(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    mats = []
    for comp in components:
        cid = comp["component_id"]
        for mat in comp.get("materials", []):
            flat = dict(mat)
            flat["component_ref"] = cid
            mats.append(flat)
    return mats


# ---------------------------------------------------------------------------
# Seed function
# ---------------------------------------------------------------------------
async def seed_build4_templates() -> Dict[str, int]:
    """Seed 6 real advertising production templates. Idempotent on template_code."""
    inserted = 0
    skipped = 0

    async with db_manager.async_session_maker() as session:
        for tpl_def in TEMPLATE_DEFINITIONS:
            existing = await session.execute(
                select(Product_templates).where(
                    Product_templates.template_code == tpl_def["template_code"]
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                logger.info("Template %s already exists, skipping.", tpl_def["template_code"])
                continue

            components = tpl_def["components_fn"]()
            ops = _flatten_operations(components)
            mats = _flatten_materials(components)
            _assert_utf8_clean_tree(components, context=tpl_def["template_code"])
            _assert_utf8_clean_tree(tpl_def.get("family_name", ""), context=f"{tpl_def['template_code']}.family_name")
            _assert_utf8_clean_tree(tpl_def.get("description", ""), context=f"{tpl_def['template_code']}.description")
            _assert_utf8_clean_tree(tpl_def.get("notes", "") or "", context=f"{tpl_def['template_code']}.notes")

            # Strip operations/materials from components for components_json
            clean_components = []
            for c in components:
                clean_components.append({
                    "component_id": c["component_id"],
                    "type": c["type"],
                    "name": c["name"],
                    "operations": c.get("operations", []),
                    "materials": c.get("materials", []),
                })

            components_json = json.dumps(clean_components, ensure_ascii=False)
            operations_json = json.dumps(ops, ensure_ascii=False)
            materials_json = json.dumps(mats, ensure_ascii=False)
            _assert_utf8_clean_tree(components_json, context=f"{tpl_def['template_code']}.components_json")
            _assert_utf8_clean_tree(operations_json, context=f"{tpl_def['template_code']}.operations_json")
            _assert_utf8_clean_tree(materials_json, context=f"{tpl_def['template_code']}.required_materials_json")

            session.add(
                Product_templates(
                    template_code=tpl_def["template_code"],
                    family_id=tpl_def["family_id"],
                    family_name=tpl_def["family_name"],
                    description=tpl_def["description"],
                    components_json=components_json,
                    operations_json=operations_json,
                    required_materials_json=materials_json,
                    estimated_hours=tpl_def["estimated_hours"],
                    base_labor_rate=tpl_def["base_labor_rate"],
                    base_margin_pct=tpl_def["base_margin_pct"],
                    active=tpl_def["template_code"] == "TPL-VOLUMETRIC-LETTERS",
                    notes=tpl_def["notes"],
                )
            )
            inserted += 1
            logger.info("Inserted template: %s", tpl_def["template_code"])

        await session.commit()

    logger.info(
        "Seeded BUILD 4 templates: inserted=%d skipped=%d",
        inserted,
        skipped,
    )
    return {"inserted": inserted, "skipped": skipped}


async def _main() -> None:
    await db_manager.init_db()
    stats = await seed_build4_templates()
    print(
        f"[seed_build4_templates] inserted={stats['inserted']} "
        f"skipped={stats['skipped']}"
    )


if __name__ == "__main__":
    asyncio.run(_main())
