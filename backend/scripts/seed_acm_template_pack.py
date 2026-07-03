"""Seed TPL-ACM-CASSETTED-PANEL and TPL-CUT-ACM-LETTERS for SVG multi-layer analysis."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List

from sqlalchemy import select

from core.database import db_manager
import models  # noqa: F401
from models.product_templates import Product_templates

logger = logging.getLogger(__name__)

FAMILY_ID = "panouri_acp_iluminate"
FAMILY_NAME = "Panouri ACP / ACM"

# Shared quote_input keys documented in notes
ACM_CASSETTED_QUOTE_INPUT_KEYS = [
    "panel_width_mm",
    "panel_height_mm",
    "acm_thickness_mm",
    "return_depth_mm",
    "rear_lip_mm",
    "fold_sides",
    "v_groove_angle_deg",
    "corner_treatment",
    "frame_clearance_mm",
    "quantity",
    "fold_length_m",
    "panel_area_m2",
    "panel_perimeter_m",
]

CUT_ACM_QUOTE_INPUT_KEYS = [
    "cut_area_m2",
    "cut_perimeter_m",
    "acm_thickness_mm",
    "quantity",
]

CASSETTED_COMPONENTS: List[Dict[str, Any]] = [
    {
        "component_id": "comp_acm_panel_face",
        "type": "STRUCTURA",
        "name": "Panou ACM/Dibond — față corp (fundal / suport premontaj)",
        "materials": [
            {
                "material_code": "MAT-ACM-BOND-PANEL",
                "name": "Panou ACM/Bond față",
                "unit": "mp",
                "calculation_type": "formula_based",
                "formula_id": "rectangular_panel_area",
                "formula_params": {"waste_pct": 5},
                "requires_quote_input": [
                    "panel_width_mm",
                    "panel_height_mm",
                    "acm_thickness_mm",
                ],
            },
        ],
        "operations": [
            {
                "code": "CUT_ACM_PANEL",
                "name": "Debitare panou ACM la dimensiune",
                "workcenter": "PANEL_CUTTING",
                "estimated_minutes": 15,
                "sequence": 1,
                "component_ref": "comp_acm_panel_face",
            },
        ],
    },
    {
        "component_id": "comp_casetted_returns",
        "type": "TAIERE_CNC_LASER",
        "name": "Casetare / pliuri V-groove 135°",
        "materials": [
            {
                "material_code": "MAT-ACM-BOND-PANEL",
                "name": "ACM suplimentar canturi / intoarceri",
                "unit": "mp",
                "calculation_type": "formula_based",
                "formula_id": "letter_face_area",
                "formula_params": {
                    "waste_pct": 3,
                    "area_quote_input_key": "return_strip_area_m2",
                },
                "requires_quote_input": [
                    "return_strip_area_m2",
                    "acm_thickness_mm",
                ],
            },
        ],
        "operations": [
            {
                "code": "V_GROOVE_ROUTER",
                "name": "Frezare V-groove (135°) pe lungimea pliului",
                "workcenter": "CNC_ROUTER",
                "sequence": 2,
                "component_ref": "comp_casetted_returns",
                "calculation_type": "formula_based",
                "formula_id": "perimeter_based_time",
                "formula_params": {
                    "perimeter_quote_input_key": "fold_length_m",
                    "minutes_per_meter": 2.5,
                    "passes": 1,
                },
                "requires_quote_input": [
                    "fold_length_m",
                    "v_groove_angle_deg",
                    "fold_sides",
                ],
            },
            {
                "code": "FOLD_CASSETTE",
                "name": "Casetare / pliere manuală",
                "workcenter": "ASSEMBLY",
                "estimated_minutes": 45,
                "sequence": 3,
                "component_ref": "comp_casetted_returns",
            },
        ],
    },
    {
        "component_id": "comp_mounting_fasteners",
        "type": "FINISAJ",
        "name": "Prinderi înecate / montaj panou",
        "materials": [
            {
                "material_code": "MAT-SURUBURI-GEN",
                "name": "Suruburi autofiletante înecate",
                "quantity": 1.0,
                "unit": "set",
            },
        ],
        "operations": [
            {
                "code": "MOUNT_ACM_PANEL",
                "name": "Montaj panou ACM pe structură / premontaj",
                "workcenter": "ASSEMBLY",
                "estimated_minutes": 30,
                "sequence": 4,
                "component_ref": "comp_mounting_fasteners",
            },
        ],
    },
]

CUT_ACM_COMPONENTS: List[Dict[str, Any]] = [
    {
        "component_id": "comp_cut_acm_sheet",
        "type": "TAIERE_CNC_LASER",
        "name": "Material ACM pentru litere/forme tăiate",
        "materials": [
            {
                "material_code": "MAT-ACM-BOND-PANEL",
                "name": "Panou ACM tăiat",
                "unit": "mp",
                "calculation_type": "formula_based",
                "formula_id": "area_from_quote_input",
                "formula_params": {
                    "area_quote_input_key": "cut_area_m2",
                    "waste_pct": 8,
                },
                "requires_quote_input": ["cut_area_m2", "acm_thickness_mm"],
            },
        ],
        "operations": [
            {
                "code": "CNC_CUT_ACM_LETTERS",
                "name": "Tăiere CNC litere/forme ACM",
                "workcenter": "CNC_ROUTER",
                "sequence": 1,
                "component_ref": "comp_cut_acm_sheet",
                "calculation_type": "formula_based",
                "formula_id": "perimeter_based_time",
                "formula_params": {
                    "perimeter_quote_input_key": "cut_perimeter_m",
                    "minutes_per_meter": 3.0,
                    "passes": 1,
                },
                "requires_quote_input": ["cut_perimeter_m"],
            },
        ],
    },
    {
        "component_id": "comp_cut_acm_finish",
        "type": "FINISAJ",
        "name": "Finisaj margini / curățare",
        "operations": [
            {
                "code": "EDGE_CLEANUP",
                "name": "Curățare margini tăiate",
                "workcenter": "FINISHING",
                "estimated_minutes": 20,
                "sequence": 2,
                "component_ref": "comp_cut_acm_finish",
            },
        ],
        "materials": [],
    },
]

TEMPLATE_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "template_code": "TPL-ACM-CASSETTED-PANEL",
        "description": (
            "Panou ACM/Dibond/Alucobond casetat — fundal, suport premontaj sau bază semn. "
            "Nu este spatele literelor volumetrice (Forex 10 mm). Grosime ACM selectabilă "
            "la ofertare (3/4 mm). Casetare configurabilă: pliuri, cant, buză spate min. 25 mm."
        ),
        "components": CASSETTED_COMPONENTS,
        "notes": (
            "quote_input: "
            + ", ".join(ACM_CASSETTED_QUOTE_INPUT_KEYS)
            + ". return_strip_area_m2 = fold_length_m * return_depth_mm / 1000 (derivat). "
            "rear_lip_mm < 25 → warning la validare. Nu confunda cu MAT-SPATE-PVC-LITERE."
        ),
    },
    {
        "template_code": "TPL-CUT-ACM-LETTERS",
        "description": (
            "Litere/forme plate tăiate din ACM/Alucobond/Dibond — nu litere volumetrice. "
            "Separat de TPL-VOLUMETRIC-LETTERS."
        ),
        "components": CUT_ACM_COMPONENTS,
        "notes": (
            "quote_input: " + ", ".join(CUT_ACM_QUOTE_INPUT_KEYS) + "."
        ),
    },
]


def _template_payload(defn: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "template_code": defn["template_code"],
        "family_id": FAMILY_ID,
        "family_name": FAMILY_NAME,
        "description": defn["description"],
        "components_json": json.dumps(defn["components"], ensure_ascii=False),
        "operations_json": None,
        "required_materials_json": None,
        "estimated_hours": None,
        "base_labor_rate": None,
        "base_margin_pct": None,
        "active": False,
        "notes": defn["notes"],
    }


async def seed_acm_template_pack() -> Dict[str, Any]:
    inserted = 0
    updated = 0

    async with db_manager.async_session_maker() as session:
        for defn in TEMPLATE_DEFINITIONS:
            code = defn["template_code"]
            existing = await session.execute(
                select(Product_templates).where(
                    Product_templates.template_code == code
                )
            )
            row = existing.scalar_one_or_none()
            payload = _template_payload(defn)

            if row is None:
                session.add(Product_templates(**payload))
                inserted += 1
            else:
                for key, value in payload.items():
                    if key == "template_code":
                        continue
                    setattr(row, key, value)
                updated += 1

        await session.commit()

    return {
        "inserted": inserted,
        "updated": updated,
        "template_codes": [d["template_code"] for d in TEMPLATE_DEFINITIONS],
    }


async def _main() -> None:
    await db_manager.init_db()
    stats = await seed_acm_template_pack()
    print(f"[seed_acm_template_pack] {stats}")


if __name__ == "__main__":
    asyncio.run(_main())
