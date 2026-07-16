"""Create Product System template TPL-VOLUMETRIC-LOGO_v1 with minimal live children.

Controlled, idempotent DB seed.
Does not touch Cost Engine, Quote/Order, execution task materialization, or UI.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from core.database import db_manager
import models  # noqa: F401
from models.product_blueprint_dossier import ProductBlueprintDossier
from models.product_templates import Product_templates
from services.product_template_module_links_service import ProductTemplateModuleLinksService
from services.template_architecture_scope import (
    VOLUMETRIC_LOGO_BACK_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_FACE_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_FINISH_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_LIGHTING_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_MOUNTING_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_RETURN_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_TEMPLATE_CODE,
    VOLUMETRIC_V2_TEMPLATE_CODE,
)

logger = logging.getLogger(__name__)

PARENT_TEMPLATE_CODE = VOLUMETRIC_LOGO_TEMPLATE_CODE
FALLBACK_FAMILY_ID = "litere_volumetrice"
FALLBACK_FAMILY_NAME = "Litere volumetrice"

PARENT_COMPONENT_SPECS = [
    ("comp_logo_face", "LOGO FACE", "față logo volumetric / print surface"),
    ("comp_logo_finish", "LOGO FINISH", "print / laminare / finisaj logo"),
    ("comp_logo_return", "LOGO RETURN", "cant / volum logo"),
    ("comp_logo_back", "LOGO BACK", "spate logo / închidere"),
    ("comp_logo_lighting", "LOGO LIGHTING", "iluminare, PSU și cablaj logo"),
    ("comp_logo_mounting", "LOGO MOUNTING", "șablon și montaj logo"),
]

CHILD_SPECS = [
    {
        "template_code": VOLUMETRIC_LOGO_FACE_TEMPLATE_CODE,
        "component_id": "comp_logo_face",
        "type": "LITERE_3D",
        "name": "Față logo volumetric",
        "description": "Template modular separat pentru fața logo-ului volumetric.",
        "notes": "Seed minim controlat pentru fața logo-ului volumetric.",
        "trigger_field": "logo_face_module_template_code",
        "input_mapping": {
            "svg_area_m2": "svg_area_m2",
            "svg_bbox": "svg_bbox",
            "logo_artwork_mode": "print_mode",
            "logo_face_material": "face_material",
        },
        "operations": [
            {
                "code": "logo_face_cnc_cut",
                "workcenter": "CNC_ROUTER",
                "sequence": 1,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "logo_area",
                "requires_quote_input": ["svg_area_m2"],
                "label": "Debitare față logo volumetric",
            },
        ],
        "materials": [
            {
                "materialCode": "logo_face_material",
                "material_code": "logo_face_material",
                "unit": "mp",
                "quantity": 0,
                "calculation_type": "formula_based",
                "formula_id": "logo_area",
                "requires_quote_input": ["svg_area_m2"],
                "label": "Material față logo",
            },
        ],
    },
    {
        "template_code": VOLUMETRIC_LOGO_RETURN_TEMPLATE_CODE,
        "component_id": "comp_logo_return",
        "type": "LITERE_3D",
        "name": "Cant / volum logo",
        "description": "Template modular separat pentru cantul / volumul logo-ului.",
        "notes": "Seed minim controlat pentru cantul logo-ului volumetric.",
        "trigger_field": "logo_return_module_template_code",
        "input_mapping": {
            "svg_perimeter_ml": "svg_perimeter_ml",
            "return_depth_mm": "return_depth_mm",
            "return_finish_type": "return_finish_type",
        },
        "operations": [
            {
                "code": "logo_return_forming",
                "workcenter": "RETURN_PROFILE_MACHINE_FORMING",
                "sequence": 1,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "logo_perimeter",
                "requires_quote_input": ["svg_perimeter_ml"],
                "label": "Formare cant logo",
            },
            {
                "code": "logo_return_bonding",
                "workcenter": "RETURN_PROFILE_FACE_BONDING",
                "sequence": 2,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "logo_perimeter",
                "requires_quote_input": ["svg_perimeter_ml"],
                "label": "Lipire cant logo",
            },
        ],
        "materials": [
            {
                "materialCode": "logo_return_profile",
                "material_code": "logo_return_profile",
                "unit": "ml",
                "quantity": 0,
                "calculation_type": "formula_based",
                "formula_id": "logo_perimeter",
                "requires_quote_input": ["svg_perimeter_ml"],
                "label": "Profil cant logo",
            },
        ],
    },
    {
        "template_code": VOLUMETRIC_LOGO_BACK_TEMPLATE_CODE,
        "component_id": "comp_logo_back",
        "type": "STRUCTURA",
        "name": "Spate logo volumetric",
        "description": "Template modular separat pentru spatele logo-ului volumetric.",
        "notes": "Seed minim controlat pentru spatele logo-ului volumetric.",
        "trigger_field": "logo_back_module_template_code",
        "input_mapping": {
            "svg_area_m2": "svg_area_m2",
            "logo_backing_material": "back_material",
        },
        "operations": [
            {
                "code": "logo_back_cut",
                "workcenter": "CNC_ROUTER",
                "sequence": 1,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "logo_area",
                "requires_quote_input": ["svg_area_m2"],
                "label": "Debitare spate logo",
            },
        ],
        "materials": [
            {
                "materialCode": "logo_back_material",
                "material_code": "logo_back_material",
                "unit": "mp",
                "quantity": 0,
                "calculation_type": "formula_based",
                "formula_id": "logo_area",
                "requires_quote_input": ["svg_area_m2"],
                "label": "Material spate logo",
            },
        ],
    },
    {
        "template_code": VOLUMETRIC_LOGO_LIGHTING_TEMPLATE_CODE,
        "component_id": "comp_logo_lighting",
        "type": "ELECTRIC_LED",
        "name": "Iluminare logo volumetric",
        "description": "Template modular separat pentru iluminarea logo-ului volumetric.",
        "notes": "Seed minim controlat pentru iluminarea logo-ului volumetric.",
        "trigger_field": "logo_lighting_module_template_code",
        "input_mapping": {
            "logo_lighting_mode": "emblem_lighting_mode",
            "emblem_led_module_count": "emblem_led_module_count",
            "selected_psu_watts": "selected_psu_watts",
        },
        "operations": [
            {
                "code": "logo_led_install",
                "workcenter": "LED_ASSEMBLY",
                "sequence": 1,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "logo_led_modules",
                "requires_quote_input": ["emblem_led_module_count"],
                "label": "Montaj LED logo",
            },
            {
                "code": "logo_electrical_test",
                "workcenter": "ELECTRICAL_WIRING",
                "sequence": 2,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "logo_led_modules",
                "requires_quote_input": ["emblem_led_module_count"],
                "label": "Test electric logo",
            },
        ],
        "materials": [
            {
                "materialCode": "MAT-LED-MODULE",
                "material_code": "MAT-LED-MODULE",
                "unit": "buc",
                "quantity": 0,
                "calculation_type": "formula_based",
                "formula_id": "logo_led_modules",
                "requires_quote_input": ["emblem_led_module_count"],
                "label": "Module LED logo",
            },
            {
                "materialCode": "MAT-LED-PSU-12V",
                "material_code": "MAT-LED-PSU-12V",
                "unit": "buc",
                "quantity": 0,
                "calculation_type": "formula_based",
                "formula_id": "logo_psu_count",
                "requires_quote_input": ["selected_psu_watts"],
                "label": "PSU LED logo",
            },
        ],
    },
    {
        "template_code": VOLUMETRIC_LOGO_FINISH_TEMPLATE_CODE,
        "component_id": "comp_logo_finish",
        "type": "FINISAJ",
        "name": "Print / laminare / finisaj logo",
        "description": "Template modular separat pentru printul și finisajul logo-ului volumetric.",
        "notes": "Seed minim controlat pentru finisajul logo-ului volumetric.",
        "trigger_field": "logo_finish_module_template_code",
        "input_mapping": {
            "logo_artwork_mode": "print_mode",
            "svg_area_m2": "area_m2",
        },
        "operations": [
            {
                "code": "logo_face_print",
                "workcenter": "LARGE_FORMAT_PRINT",
                "sequence": 1,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "logo_area",
                "requires_quote_input": ["svg_area_m2"],
                "label": "Print față logo",
            },
            {
                "code": "logo_face_laminate",
                "workcenter": "LAMINATION",
                "sequence": 2,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "logo_area",
                "requires_quote_input": ["svg_area_m2"],
                "label": "Laminare față logo",
            },
            {
                "code": "logo_finish_application",
                "workcenter": "FACE_VINYL_APPLICATION_LABOR",
                "sequence": 3,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "logo_area",
                "requires_quote_input": ["svg_area_m2"],
                "label": "Aplicare finisaj logo",
            },
        ],
        "materials": [
            {
                "materialCode": "print_media",
                "material_code": "print_media",
                "unit": "mp",
                "quantity": 0,
                "calculation_type": "formula_based",
                "formula_id": "logo_area",
                "requires_quote_input": ["svg_area_m2"],
                "label": "Media print logo finisaj",
            },
            {
                "materialCode": "laminate_media",
                "material_code": "laminate_media",
                "unit": "mp",
                "quantity": 0,
                "calculation_type": "formula_based",
                "formula_id": "logo_area",
                "requires_quote_input": ["svg_area_m2"],
                "label": "Media laminare logo finisaj",
            },
        ],
    },
    {
        "template_code": VOLUMETRIC_LOGO_MOUNTING_TEMPLATE_CODE,
        "component_id": "comp_logo_mounting",
        "type": "STRUCTURA",
        "name": "Montaj logo volumetric",
        "description": "Template modular separat pentru montajul logo-ului volumetric.",
        "notes": "Seed minim controlat pentru montajul logo-ului volumetric.",
        "trigger_field": "logo_mounting_module_template_code",
        "input_mapping": {
            "mounting_system": "mounting_system",
            "mounting_template_enabled": "mounting_template_enabled",
        },
        "operations": [
            {
                "code": "logo_mounting_template_cut",
                "workcenter": "CNC_ROUTER",
                "sequence": 1,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "logo_area",
                "requires_quote_input": ["svg_area_m2"],
                "label": "Debitare șablon montaj logo",
            },
            {
                "code": "logo_mounting_install",
                "workcenter": "ASSEMBLY",
                "sequence": 2,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "logo_area",
                "requires_quote_input": ["svg_area_m2"],
                "label": "Montaj logo",
            },
        ],
        "materials": [
            {
                "materialCode": "logo_mounting_template",
                "material_code": "logo_mounting_template",
                "unit": "mp",
                "quantity": 0,
                "calculation_type": "formula_based",
                "formula_id": "logo_area",
                "requires_quote_input": ["svg_area_m2"],
                "label": "Șablon montaj logo",
            },
            {
                "materialCode": "logo_fasteners",
                "material_code": "logo_fasteners",
                "unit": "set",
                "quantity": 1,
                "calculation_type": "static",
                "label": "Elemente montaj logo",
            },
        ],
    },
]


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _component_from_spec(spec: dict[str, Any]) -> dict[str, Any]:
    operations = []
    for row in spec["operations"]:
        operation = dict(row)
        operation["component_ref"] = spec["component_id"]
        operations.append(operation)

    materials = []
    for row in spec["materials"]:
        material = dict(row)
        material["component_ref"] = spec["component_id"]
        materials.append(material)

    return {
        "component_id": spec["component_id"],
        "type": spec["type"],
        "name": spec["name"],
        "operations": operations,
        "materials": materials,
    }


def _child_template_payload(spec: dict[str, Any], family_id: str, family_name: str) -> dict[str, Any]:
    component = _component_from_spec(spec)
    return {
        "template_code": spec["template_code"],
        "family_id": family_id,
        "family_name": family_name,
        "description": spec["description"],
        "components_json": _json_dumps([component]),
        "operations_json": _json_dumps(component["operations"]),
        "required_materials_json": _json_dumps(component["materials"]),
        "estimated_hours": 2.0,
        "base_labor_rate": 80.0,
        "base_margin_pct": 40.0,
        "active": True,
        "notes": spec["notes"],
    }


def _parent_template_payload(family_id: str, family_name: str) -> dict[str, Any]:
    # Linked-child ProductAggregate expansion namespaces these parent component rows
    # per logo segment (comp_logo_face::logo_instance_001, …). Keep empty arrays for
    # parent materials/ops — child module rows remain the BOM/ops source.
    parent_components = [
        {
            "id": component_id,
            "component_id": component_id,
            "code": component_id,
            "label": label,
            "label_ro": label,
            "name": label,
            "role": role,
            "type": "LITERE_3D" if "FACE" in label or "RETURN" in label or "FINISH" in label else "STRUCTURA",
            "materials": [],
            "operations": [],
        }
        for component_id, label, role in PARENT_COMPONENT_SPECS
    ]
    return {
        "template_code": PARENT_TEMPLATE_CODE,
        "family_id": family_id,
        "family_name": family_name,
        "description": "Logo volumetric luminos / componentă volumetrică logo.",
        "components_json": _json_dumps(parent_components),
        "operations_json": _json_dumps([]),
        "required_materials_json": _json_dumps([]),
        "estimated_hours": 2.0,
        "base_labor_rate": 80.0,
        "base_margin_pct": 40.0,
        "active": True,
        "notes": (
            "Linked-child-only parent for volumetric logo. Not root-offerable. "
            "Used by ProductAggregate/ProductDefinition composition under letters."
        ),
    }


def _parent_dossier_payload(template_id: int) -> dict[str, Any]:
    material_keys = [
        "logo_face_material",
        "print_media",
        "laminate_media",
        "logo_return_profile",
        "logo_back_material",
        "MAT-LED-MODULE",
        "MAT-LED-PSU-12V",
        "logo_mounting_template",
        "logo_fasteners",
    ]
    operation_keys = [
        "logo_face_cnc_cut",
        "logo_face_print",
        "logo_face_laminate",
        "logo_return_forming",
        "logo_return_bonding",
        "logo_back_cut",
        "logo_led_install",
        "logo_electrical_test",
        "logo_finish_application",
        "logo_mounting_template_cut",
        "logo_mounting_install",
    ]
    sections = {
        "template_identity": {
            "template_code": PARENT_TEMPLATE_CODE,
            "source_template_code": PARENT_TEMPLATE_CODE,
            "purpose": "Template Product System minim pentru logo volumetric independent sau compus cu litere.",
            "owner_valid_active": True,
        },
        "components": [
            {"id": component_id, "label": label, "role": role}
            for component_id, label, role in PARENT_COMPONENT_SPECS
        ],
        "material_keys": material_keys,
        "operation_keys": operation_keys,
    }
    task_rules = {
        "rules": [
            {
                "task_name": "logo_face_cut",
                "task_type": "cnc_routing",
                "priced_operation": "logo_face_cnc_cut",
                "sequence": 1,
                "trigger_condition": "svg_area_m2 present",
            },
            {
                "task_name": "logo_print_finish",
                "task_type": "print_finish",
                "priced_operation": "logo_finish_application",
                "sequence": 2,
                "trigger_condition": "logo_artwork_mode print/vinyl path",
            },
            {
                "task_name": "logo_mounting",
                "task_type": "assembly",
                "priced_operation": "logo_mounting_install",
                "sequence": 3,
                "trigger_condition": "mounting_system present",
            },
        ]
    }
    mapping = {
        "template_code": PARENT_TEMPLATE_CODE,
        "family_id": FALLBACK_FAMILY_ID,
        "status": "approved_structural_mapping",
        "quote_ready": False,
        "pricing_ready": False,
        "inputs": {
            "required": ["vector_file", "svg_area_m2", "svg_bbox", "mounting_system"],
            "optional": [
                "svg_perimeter_ml",
                "return_depth_mm",
                "return_finish_type",
                "logo_artwork_mode",
                "logo_face_material",
                "logo_backing_material",
                "logo_lighting_mode",
                "selected_psu_watts",
                "mounting_template_enabled",
            ],
        },
        "material_keys": material_keys,
        "operation_keys": operation_keys,
        "readiness_notes": [
            "Minimal structural seed only.",
            "No commercial pricing formulas introduced.",
            "No task materialization introduced.",
        ],
    }
    return {
        "template_id": template_id,
        "template_code": PARENT_TEMPLATE_CODE,
        "dossier_version": 1,
        "status": "approved",
        "sections_json": _json_dumps(sections),
        "variants_json": _json_dumps(
            {
                "variants": [
                    {"variant_key": "logo_artwork_mode", "allowed_values": ["plexi_face", "print_vinyl", "printed_artwork"]},
                    {"variant_key": "logo_lighting_mode", "allowed_values": ["area_lit", "excluded"]},
                    {"variant_key": "return_depth_mm", "allowed_values": [30, 60, 80, 100]},
                ]
            }
        ),
        "layers_json": _json_dumps({"layers": [item[0] for item in PARENT_COMPONENT_SPECS]}),
        "task_rules_json": _json_dumps(task_rules),
        "time_assumptions_json": _json_dumps({}),
        "costengine_mapping_json": _json_dumps(mapping),
        "quote_readiness_json": _json_dumps(
            {
                "preliminary_simulation_without_vector": True,
                "final_quote_requires_vector_file": True,
                "vector_analysis_policy": {"svg": "automatic_layer_analysis_when_provided"},
            }
        ),
        "output_blocks_json": _json_dumps({"short_description": "Logo volumetric luminos — parent template minim live."}),
        "visual_prompt_blocks_json": _json_dumps({"prompt": "Logo volumetric luminos"}),
        "production_notes_json": _json_dumps({"notes": ["Seed minim Product System live pentru logo volumetric."]}),
        "qc_checkpoints_json": _json_dumps({"checkpoints": []}),
        "risks_json": _json_dumps({}),
        "completion_state_json": _json_dumps({"seed_scope": "minimal_live_parent"}),
        "owner_role": "product_owner",
        "reviewer_role": "technical_reviewer",
        "reviewed_at": datetime.now(timezone.utc),
    }


def _child_dossier_payload(template_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    component = _component_from_spec(spec)
    sections = {
        "template_identity": {
            "template_code": spec["template_code"],
            "source_template_code": PARENT_TEMPLATE_CODE,
            "purpose": spec["description"],
            "owner_valid_active": True,
        },
        "components": [
            {"id": spec["component_id"], "label": spec["name"], "role": spec["description"]}
        ],
        "material_keys": [row["material_code"] for row in component["materials"]],
        "operation_keys": [row["code"] for row in component["operations"]],
    }
    return {
        "template_id": template_id,
        "template_code": spec["template_code"],
        "dossier_version": 1,
        "status": "approved",
        "sections_json": _json_dumps(sections),
        "variants_json": _json_dumps({"variants": []}),
        "layers_json": _json_dumps({"layers": [spec["component_id"]]}),
        "task_rules_json": _json_dumps({"tasks": []}),
        "time_assumptions_json": _json_dumps({}),
        "costengine_mapping_json": _json_dumps(
            {
                "template_code": spec["template_code"],
                "inputs": {"required": sorted(set(spec["input_mapping"].keys()))},
                "material_keys": [row["material_code"] for row in component["materials"]],
                "operation_keys": [row["code"] for row in component["operations"]],
            }
        ),
        "quote_readiness_json": _json_dumps({"ready_for_quote_selector": True, "reason": spec["description"]}),
        "output_blocks_json": _json_dumps({}),
        "visual_prompt_blocks_json": _json_dumps({}),
        "production_notes_json": _json_dumps({}),
        "qc_checkpoints_json": _json_dumps({}),
        "risks_json": _json_dumps({}),
        "completion_state_json": _json_dumps({}),
        "owner_role": "product_owner",
        "reviewer_role": "technical_reviewer",
        "reviewed_at": datetime.now(timezone.utc),
    }


def _link_payload(parent_template_id: int, child_template_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "parent_template_id": parent_template_id,
        "parent_template_code": PARENT_TEMPLATE_CODE,
        "module_template_id": child_template_id,
        "module_template_code": spec["template_code"],
        "relation_type": "required_module",
        "trigger_field": spec["trigger_field"],
        "trigger_value_json": _json_dumps([spec["template_code"]]),
        "input_mapping_json": _json_dumps(spec["input_mapping"]),
        "default_values_json": _json_dumps({spec["trigger_field"]: spec["template_code"]}),
        "pricing_mode": "separate_quote_line",
        "execution_mode": "linked_child_work",
        "active": True,
        "notes": f"Modul separat {spec['template_code']} este linkuit obligatoriu din {PARENT_TEMPLATE_CODE}.",
    }


async def _get_template(template_code: str) -> Product_templates | None:
    async with db_manager.async_session_maker() as db:
        result = await db.execute(
            select(Product_templates).where(Product_templates.template_code == template_code).order_by(Product_templates.id.asc()).limit(1)
        )
        return result.scalar_one_or_none()


async def _upsert_template(payload: dict[str, Any]) -> tuple[Product_templates, str]:
    async with db_manager.async_session_maker() as db:
        result = await db.execute(
            select(Product_templates).where(Product_templates.template_code == payload["template_code"]).order_by(Product_templates.id.asc()).limit(1)
        )
        row = result.scalar_one_or_none()
        action = "created"
        if row is None:
            row = Product_templates(**payload)
            db.add(row)
        else:
            action = "updated"
            for key, value in payload.items():
                setattr(row, key, value)
        await db.commit()
        await db.refresh(row)
        return row, action


async def _upsert_dossier(payload: dict[str, Any]) -> tuple[ProductBlueprintDossier, str]:
    async with db_manager.async_session_maker() as db:
        result = await db.execute(
            select(ProductBlueprintDossier).where(ProductBlueprintDossier.template_id == payload["template_id"]).limit(1)
        )
        row = result.scalar_one_or_none()
        action = "created"
        if row is None:
            row = ProductBlueprintDossier(**payload)
            db.add(row)
        else:
            action = "updated"
            for key, value in payload.items():
                setattr(row, key, value)
        await db.commit()
        await db.refresh(row)
        return row, action


async def seed_tpl_volumetric_logo_v1() -> dict[str, Any]:
    await db_manager.init_db()

    letters_template = await _get_template(VOLUMETRIC_V2_TEMPLATE_CODE)
    family_id = letters_template.family_id if letters_template and letters_template.family_id else FALLBACK_FAMILY_ID
    family_name = letters_template.family_name if letters_template and letters_template.family_name else FALLBACK_FAMILY_NAME

    created_templates = 0
    updated_templates = 0
    created_dossiers = 0
    updated_dossiers = 0
    created_links = 0
    updated_links = 0

    parent_row, action = await _upsert_template(_parent_template_payload(str(family_id), str(family_name)))
    if action == "created":
        created_templates += 1
    else:
        updated_templates += 1

    _row, action = await _upsert_dossier(_parent_dossier_payload(parent_row.id))
    if action == "created":
        created_dossiers += 1
    else:
        updated_dossiers += 1

    link_service = None
    async with db_manager.async_session_maker() as db:
        link_service = ProductTemplateModuleLinksService(db)
        for spec in CHILD_SPECS:
            child_row, action = await _upsert_template(_child_template_payload(spec, str(family_id), str(family_name)))
            if action == "created":
                created_templates += 1
            else:
                updated_templates += 1

            _dossier_row, dossier_action = await _upsert_dossier(_child_dossier_payload(child_row.id, spec))
            if dossier_action == "created":
                created_dossiers += 1
            else:
                updated_dossiers += 1

            _link, link_action = await link_service.upsert_by_contract(_link_payload(parent_row.id, child_row.id, spec))
            if link_action == "created":
                created_links += 1
            else:
                updated_links += 1

    logger.info("Seeded %s and child templates", PARENT_TEMPLATE_CODE)
    return {
        "template_code": PARENT_TEMPLATE_CODE,
        "created_templates": created_templates,
        "updated_templates": updated_templates,
        "created_dossiers": created_dossiers,
        "updated_dossiers": updated_dossiers,
        "created_links": created_links,
        "updated_links": updated_links,
        "family_id": family_id,
        "family_name": family_name,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(json.dumps(asyncio.run(seed_tpl_volumetric_logo_v1()), indent=2, default=str))