"""Complete TPL-VOLUMETRIC-LETTERS_v2 composition with component-owned child PTs.

Creates / updates FACE / BACK / LED / FINISH as component-only Product Templates,
links them as required modules, stamps usage_mode + instance_schema_id on all VL
edges (including Aluminiu / Premount / ACM), and moves BOM ownership off the root
for those components so Aggregate provenance is not duplicated.

Preserves owner-activated TPL-VOLUM-ALUMINIU_v1 (active=true after ACTIVATION GO).
Does NOT publish parent or child. No ComponentTemplate table.
Geometry contracts are inputs-only (no SVG/DWG/DXF parse).
"""

from __future__ import annotations

import asyncio
import json
import logging
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from core.database import db_manager
import models  # noqa: F401
from models.product_blueprint_dossier import ProductBlueprintDossier
from models.product_templates import Product_templates
from services.product_template_module_links_service import ProductTemplateModuleLinksService
from services.template_architecture_scope import (
    ACM_BOXED_MOUNTING_TEMPLATE_CODE,
    STRUCTURE_PREMOUNT_TEMPLATE_CODE,
    VOLUM_ALUMINUM_TEMPLATE_CODE,
    VOLUMETRIC_BACK_TEMPLATE_CODE,
    VOLUMETRIC_FACE_TEMPLATE_CODE,
    VOLUMETRIC_FINISH_TEMPLATE_CODE,
    VOLUMETRIC_LED_TEMPLATE_CODE,
    VOLUMETRIC_V2_TEMPLATE_CODE,
)

logger = logging.getLogger(__name__)

PARENT_CODE = VOLUMETRIC_V2_TEMPLATE_CODE
FAMILY_ID = "litere_volumetrice"
FAMILY_NAME = "Litere volumetrice"

# Geometry inputs only — never parsed/analyzed by WorkOS.
GEOMETRY_INPUT_CONTRACT = {
    "contract_version": "vl_geometry_inputs_v1",
    "owner": "external_desktop_or_manual",
    "workos_role": "consume_only",
    "forbidden": [
        "svg_parse",
        "dwg_parse",
        "dxf_parse",
        "auto_group",
        "geometry_inference",
    ],
    "expected_inputs": [
        {"key": "width_mm", "unit": "mm", "required": True},
        {"key": "height_mm", "unit": "mm", "required": True},
        {"key": "depth_mm", "unit": "mm", "required": True},
        {"key": "letter_face_area_m2", "unit": "m2", "required": True},
        {"key": "letter_perimeter_m", "unit": "m", "required": True},
        {"key": "letter_count", "unit": "count", "required": True},
        {"key": "component_placements", "unit": "placement", "required": False},
        {"key": "external_artwork_analysis_ref", "unit": "ref", "required": False},
        {"key": "geometry_provenance", "unit": "provenance", "required": False},
    ],
}

CHILD_SPECS: list[dict[str, Any]] = [
    {
        "template_code": VOLUMETRIC_FACE_TEMPLATE_CODE,
        "component_id": "comp_face_litere",
        "type": "LITERE_3D",
        "name": "Vizual fata — plexi/acrilic",
        "description": "Component-only Product Template for letter face panel.",
        "relation_type": "required_module",
        "trigger_field": "face_module_template_code",
        "usage_mode": "linked_child",
        "instance_schema_id": "letter_group_instances.face",
        "input_mapping": {
            "letter_face_area_m2": "letter_face_area_m2",
            "face_finish_type": "face_finish_type",
            "face_vinyl_color_code": "face_vinyl_color_code",
            "width_mm": "width_mm",
            "height_mm": "height_mm",
        },
        "operations": [
            {
                "code": "geometry_inputs_readiness_gate",
                "workcenter": "PREPRESS",
                "sequence": 0,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "svg_geometry_readiness_gate",
                "formula_params": {
                    "non_priced": True,
                    "consume_only": True,
                    "no_file_parse": True,
                },
                "requires_quote_input": [
                    "letter_face_area_m2",
                    "letter_perimeter_m",
                    "letter_count",
                ],
                "label": "Geometry inputs readiness (consume-only)",
                "component_ref": "comp_face_litere",
            },
            {
                "code": "vector_prep",
                "workcenter": "PREPRESS",
                "sequence": 1,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "vector_prep",
                "formula_params": {"non_priced": True},
                "requires_quote_input": ["letter_face_area_m2"],
                "label": "Pregatire vector (input-gated)",
                "component_ref": "comp_face_litere",
            },
            {
                "code": "face_cnc_cut",
                "workcenter": "CNC_ROUTER",
                "sequence": 2,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "face_cnc_cut",
                "requires_quote_input": ["letter_face_area_m2"],
                "label": "Debitare fata litere",
                "component_ref": "comp_face_litere",
            },
            {
                "code": "vinyl_application",
                "workcenter": "WC_FINISH",
                "sequence": 3,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "vinyl_application",
                "requires_quote_input": ["letter_face_area_m2", "face_finish_type"],
                "label": "Aplicare folie fata",
                "component_ref": "comp_face_litere",
            },
        ],
        "materials": [
            {
                "materialCode": "MAT-ACP-FATA-LITERE",
                "material_code": "MAT-ACP-FATA-LITERE",
                "unit": "mp",
                "quantity": 0,
                "calculation_type": "formula_based",
                "formula_id": "letter_face_area",
                "requires_quote_input": ["letter_face_area_m2"],
                "component_ref": "comp_face_litere",
            },
            {
                "materialCode": "MAT-ORACAL-651",
                "material_code": "MAT-ORACAL-651",
                "unit": "mp",
                "quantity": 0,
                "calculation_type": "formula_based",
                "formula_id": "letter_face_area",
                "requires_quote_input": ["letter_face_area_m2", "face_finish_type"],
                "component_ref": "comp_face_litere",
            },
            {
                "materialCode": "MAT-VINYL-PRINT",
                "material_code": "MAT-VINYL-PRINT",
                "unit": "mp",
                "quantity": 0,
                "calculation_type": "formula_based",
                "formula_id": "letter_face_area",
                "requires_quote_input": ["letter_face_area_m2"],
                "component_ref": "comp_face_litere",
            },
            {
                "materialCode": "MAT-VINYL-PRINT-LAMINATED",
                "material_code": "MAT-VINYL-PRINT-LAMINATED",
                "unit": "mp",
                "quantity": 0,
                "calculation_type": "formula_based",
                "formula_id": "letter_face_area",
                "requires_quote_input": ["letter_face_area_m2"],
                "component_ref": "comp_face_litere",
            },
        ],
    },
    {
        "template_code": VOLUMETRIC_BACK_TEMPLATE_CODE,
        "component_id": "comp_spate_litere",
        "type": "STRUCTURA",
        "name": "Capac spate — Forex 10 mm",
        "description": "Component-only Product Template for letter back panel.",
        "relation_type": "required_module",
        "trigger_field": "back_module_template_code",
        "usage_mode": "linked_child",
        "instance_schema_id": "letter_group_instances.back",
        "input_mapping": {
            "letter_face_area_m2": "letter_face_area_m2",
            "backing_mode": "backing_mode",
            "backing_thickness_mm": "backing_thickness_mm",
        },
        "operations": [
            {
                "code": "back_cut",
                "workcenter": "CNC_ROUTER",
                "sequence": 1,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "back_cut",
                "requires_quote_input": ["letter_face_area_m2"],
                "label": "Debitare spate litere",
                "component_ref": "comp_spate_litere",
            }
        ],
        "materials": [
            {
                "materialCode": "MAT-SPATE-PVC-LITERE",
                "material_code": "MAT-SPATE-PVC-LITERE",
                "unit": "mp",
                "quantity": 0,
                "calculation_type": "formula_based",
                "formula_id": "letter_face_area",
                "requires_quote_input": ["letter_face_area_m2"],
                "component_ref": "comp_spate_litere",
            }
        ],
    },
    {
        "template_code": VOLUMETRIC_LED_TEMPLATE_CODE,
        "component_id": "comp_led_litere",
        "type": "ELECTRIC_LED",
        "name": "Sistem LED — module, surse, cablaj",
        "description": "Component-only Product Template for letter lighting.",
        "relation_type": "required_module",
        "trigger_field": "led_module_template_code",
        "usage_mode": "linked_child",
        "instance_schema_id": "letter_group_instances.lighting",
        "input_mapping": {
            "lighting_system_type": "lighting_system_type",
            "led_module_count": "led_module_count",
            "selected_psu_watts": "selected_psu_watts",
        },
        "operations": [
            {
                "code": "led_install_letters",
                "workcenter": "WC_ELECTRICAL",
                "sequence": 1,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "led_install_letters",
                "requires_quote_input": ["led_module_count"],
                "label": "Montaj module LED",
                "component_ref": "comp_led_litere",
            },
            {
                "code": "electrical_letters",
                "workcenter": "WC_ELECTRICAL",
                "sequence": 2,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "electrical_letters",
                "requires_quote_input": ["selected_psu_watts"],
                "label": "Cablaj / test electric",
                "component_ref": "comp_led_litere",
            },
        ],
        "materials": [
            {
                "materialCode": "MAT-LED-MODULE",
                "material_code": "MAT-LED-MODULE",
                "unit": "buc",
                "quantity": 0,
                "calculation_type": "formula_based",
                "formula_id": "led_module_count",
                "requires_quote_input": ["led_module_count"],
                "component_ref": "comp_led_litere",
            },
            {
                "materialCode": "MAT-LED-PSU-12V",
                "material_code": "MAT-LED-PSU-12V",
                "unit": "buc",
                "quantity": 0,
                "calculation_type": "formula_based",
                "formula_id": "psu_selection",
                "requires_quote_input": ["selected_psu_watts"],
                "component_ref": "comp_led_litere",
            },
        ],
    },
    {
        "template_code": VOLUMETRIC_FINISH_TEMPLATE_CODE,
        "component_id": "comp_finisaj_litere",
        "type": "FINISAJ",
        "name": "Finisaj — vopsire, asamblare, ambalare",
        "description": "Component-only Product Template for finishes, packaging, QC.",
        "relation_type": "required_module",
        "trigger_field": "finish_module_template_code",
        "usage_mode": "linked_child",
        "instance_schema_id": "letter_group_instances.finish",
        "input_mapping": {
            "face_finish_type": "face_finish_type",
            "mounting_template_enabled": "mounting_template_enabled",
            "mounting_template_area_m2": "mounting_template_area_m2",
        },
        "operations": [
            {
                "code": "mounting_template_cnc_cut",
                "workcenter": "CNC_ROUTER",
                "sequence": 1,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "mounting_template_area",
                "requires_quote_input": ["mounting_template_area_m2"],
                "label": "Debitare sablon montaj",
                "component_ref": "comp_finisaj_litere",
            },
            {
                "code": "painting",
                "workcenter": "WC_PAINT",
                "sequence": 2,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "painting",
                "requires_quote_input": ["letter_perimeter_m"],
                "label": "Vopsire / finisaj",
                "component_ref": "comp_finisaj_litere",
            },
            {
                "code": "assembly_letters",
                "workcenter": "WC_ASSEMBLY",
                "sequence": 3,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "assembly_letters",
                "requires_quote_input": ["letter_count"],
                "label": "Asamblare litere",
                "component_ref": "comp_finisaj_litere",
            },
            {
                "code": "qc_letters",
                "workcenter": "WC_QC",
                "sequence": 4,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "qc_letters",
                "formula_params": {"non_priced": True},
                "requires_quote_input": ["letter_count"],
                "label": "Control calitate",
                "component_ref": "comp_finisaj_litere",
            },
            {
                "code": "packaging_letters",
                "workcenter": "WC_PACK",
                "sequence": 5,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "packaging_letters",
                "requires_quote_input": ["letter_count"],
                "label": "Ambalare",
                "component_ref": "comp_finisaj_litere",
            },
        ],
        "materials": [
            {
                "materialCode": "MAT-VOPSEA-RAL",
                "material_code": "MAT-VOPSEA-RAL",
                "unit": "buc",
                "quantity": 0,
                "calculation_type": "formula_based",
                "formula_id": "return_paint_consumption",
                "requires_quote_input": ["letter_perimeter_m"],
                "component_ref": "comp_finisaj_litere",
            },
            {
                "materialCode": "MAT-SABLON-HARTIE",
                "material_code": "MAT-SABLON-HARTIE",
                "unit": "mp",
                "quantity": 0,
                "calculation_type": "formula_based",
                "formula_id": "mounting_template_area",
                "requires_quote_input": ["mounting_template_area_m2"],
                "component_ref": "comp_finisaj_litere",
            },
            {
                "materialCode": "MAT-SABLON-MONTAJ",
                "material_code": "MAT-SABLON-MONTAJ",
                "unit": "mp",
                "quantity": 0,
                "calculation_type": "formula_based",
                "formula_id": "mounting_template_area",
                "requires_quote_input": ["mounting_template_area_m2"],
                "component_ref": "comp_finisaj_litere",
            },
            {
                "materialCode": "MAT-CONSUMABILE-MONTAJ",
                "material_code": "MAT-CONSUMABILE-MONTAJ",
                "unit": "set",
                "quantity": 0,
                "calculation_type": "formula_based",
                "formula_id": "packaging_letters",
                "requires_quote_input": ["letter_count"],
                "component_ref": "comp_finisaj_litere",
            },
        ],
    },
]

# Existing linked children — stamp contract edge fields only.
EDGE_STAMPS: list[dict[str, Any]] = [
    {
        "module_template_code": VOLUM_ALUMINUM_TEMPLATE_CODE,
        "usage_mode": "linked_child",
        "instance_schema_id": "letter_group_instances.sidewall",
    },
    {
        "module_template_code": STRUCTURE_PREMOUNT_TEMPLATE_CODE,
        "usage_mode": "linked_child",
        "instance_schema_id": "component_placements.mounting",
    },
    {
        "module_template_code": ACM_BOXED_MOUNTING_TEMPLATE_CODE,
        "usage_mode": "linked_child",
        "instance_schema_id": "acm_panel_component_instance_v1",
    },
]

OWNED_COMPONENT_IDS = {
    "comp_face_litere",
    "comp_spate_litere",
    "comp_led_litere",
    "comp_finisaj_litere",
    "comp_lateral_litere",  # owned by Aluminiu child
}

# Legacy root op codes superseded by child ownership / renamed geometry gate.
LEGACY_ROOT_OP_CODES_TO_DROP = {
    "svg_geometry_analysis",
    "vector_prep",
    "face_cnc_cut",
    "vinyl_application",
    "back_cut",
    "led_install_letters",
    "electrical_letters",
    "mounting_template_cnc_cut",
    "painting",
    "assembly_letters",
    "qc_letters",
    "packaging_letters",
    "side_forming",
    "return_face_bonding",
}


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _json_loads(raw: str | None, fallback: Any) -> Any:
    if not raw:
        return deepcopy(fallback)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return deepcopy(fallback)


def _child_template_payload(spec: dict[str, Any], family_id: str, family_name: str) -> dict[str, Any]:
    component = {
        "component_id": spec["component_id"],
        "type": spec["type"],
        "name": spec["name"],
        "operations": spec["operations"],
        "materials": spec["materials"],
    }
    return {
        "template_code": spec["template_code"],
        "family_id": family_id,
        "family_name": family_name,
        "description": spec["description"],
        "components_json": _json_dumps([component]),
        "operations_json": _json_dumps(spec["operations"]),
        "required_materials_json": _json_dumps(spec["materials"]),
        "estimated_hours": 2.0,
        "base_labor_rate": 80.0,
        "base_margin_pct": 40.0,
        "active": True,
        "notes": (
            f"Component-only PT for {PARENT_CODE}. Not root-offerable. "
            "BOM/ops owned here; root keeps identity stubs only."
        ),
    }


def _child_dossier_payload(template_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    sections = {
        "template_identity": {
            "template_code": spec["template_code"],
            "source_template_code": PARENT_CODE,
            "purpose": spec["description"],
            "owner_valid_active": True,
            "usage_mode": "component_only",
        },
        "components": [
            {
                "id": spec["component_id"],
                "label": spec["name"],
                "role": spec["description"],
            }
        ],
        "ownership": {
            "materials": "child_product_template",
            "operations": "child_product_template",
            "quantities": "quantity_builder_via_component_inputs",
            "dossier": "documentary_only",
        },
        "geometry_input_contract": GEOMETRY_INPUT_CONTRACT
        if spec["template_code"] == VOLUMETRIC_FACE_TEMPLATE_CODE
        else {
            "contract_version": "vl_geometry_inputs_v1",
            "inherits_from": VOLUMETRIC_FACE_TEMPLATE_CODE,
            "workos_role": "consume_only",
        },
        "material_keys": [m["material_code"] for m in spec["materials"]],
        "operation_keys": [o["code"] for o in spec["operations"]],
        "cpp_eic_exposure": "via_parent_aggregate_measurements",
        "aggregate_exposure": "linked_module",
        "execution_exposure": "preview_only_no_materialization",
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
        "costengine_mapping_json": _json_dumps(
            {
                "template_code": spec["template_code"],
                "inputs": {"required": sorted(set(spec["input_mapping"].keys()))},
                "material_keys": [m["material_code"] for m in spec["materials"]],
                "operation_keys": [o["code"] for o in spec["operations"]],
            }
        ),
        "quote_readiness_json": _json_dumps(
            {
                "ready_for_quote_selector": False,
                "reason": "Component-only; offerability owned by parent root.",
            }
        ),
        "owner_role": "product_owner",
        "reviewer_role": "technical_reviewer",
        "reviewed_at": datetime.now(timezone.utc),
    }


def _link_payload(parent_id: int, child_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "parent_template_id": parent_id,
        "parent_template_code": PARENT_CODE,
        "module_template_id": child_id,
        "module_template_code": spec["template_code"],
        "relation_type": spec["relation_type"],
        "trigger_field": spec["trigger_field"],
        "trigger_value_json": _json_dumps([spec["template_code"]]),
        "input_mapping_json": _json_dumps(spec["input_mapping"]),
        "default_values_json": _json_dumps({spec["trigger_field"]: spec["template_code"]}),
        "pricing_mode": "separate_quote_line",
        "execution_mode": "linked_child_work",
        "usage_mode": spec["usage_mode"],
        "instance_schema_id": spec["instance_schema_id"],
        "active": True,
        "notes": (
            f"Required component contract {spec['template_code']} for {PARENT_CODE}. "
            "Child PT owns materials/ops; no ComponentTemplate table."
        ),
    }


def _handoff_parent_bom(parent: Product_templates) -> dict[str, Any]:
    """Keep root identity stubs; drop BOM rows owned by child contracts."""
    components = _json_loads(parent.components_json, [])
    operations = _json_loads(parent.operations_json, [])
    materials = _json_loads(parent.required_materials_json, [])

    stub_components: list[dict[str, Any]] = []
    for component in components if isinstance(components, list) else []:
        if not isinstance(component, dict):
            continue
        component_id = str(component.get("component_id") or "")
        stub = {
            "component_id": component_id,
            "type": component.get("type"),
            "name": component.get("name"),
            "operations": [],
            "materials": [],
        }
        if component_id in OWNED_COMPONENT_IDS:
            stub["ownership"] = "linked_child_product_template"
        stub_components.append(stub)

    kept_ops = [
        op
        for op in (operations if isinstance(operations, list) else [])
        if isinstance(op, dict)
        and str(op.get("component_ref") or "") not in OWNED_COMPONENT_IDS
        and str(op.get("code") or "") not in LEGACY_ROOT_OP_CODES_TO_DROP
    ]
    kept_mats = [
        mat
        for mat in (materials if isinstance(materials, list) else [])
        if isinstance(mat, dict)
        and str(mat.get("component_ref") or "") not in OWNED_COMPONENT_IDS
    ]

    parent.components_json = _json_dumps(stub_components)
    parent.operations_json = _json_dumps(kept_ops)
    parent.required_materials_json = _json_dumps(kept_mats)
    return {
        "stub_components": len(stub_components),
        "kept_root_operations": len(kept_ops),
        "kept_root_materials": len(kept_mats),
    }


def _patch_parent_dossier(dossier: ProductBlueprintDossier | None) -> bool:
    if dossier is None:
        return False
    sections = _json_loads(dossier.sections_json, {})
    if not isinstance(sections, dict):
        sections = {}
    sections["geometry_input_contract"] = GEOMETRY_INPUT_CONTRACT
    sections["component_ownership"] = {
        "model": "child_dual_role_product_template",
        "no_component_templates_table": True,
        "required_children": [
            VOLUMETRIC_FACE_TEMPLATE_CODE,
            VOLUMETRIC_BACK_TEMPLATE_CODE,
            VOLUM_ALUMINUM_TEMPLATE_CODE,
            VOLUMETRIC_LED_TEMPLATE_CODE,
            VOLUMETRIC_FINISH_TEMPLATE_CODE,
        ],
        "optional_children": [
            STRUCTURE_PREMOUNT_TEMPLATE_CODE,
            ACM_BOXED_MOUNTING_TEMPLATE_CODE,
        ],
        "dossier_is_not_bom_sot": True,
    }
    sections["publication_policy"] = {
        "aluminiu_required_inactive_blocks_publication": False,
        "aluminiu_active_after_owner_go": True,
        "do_not_auto_publish": True,
        "publication_status_left_unspecified_until_ready": True,
    }
    dossier.sections_json = _json_dumps(sections)
    return True


async def seed_tpl_volumetric_letters_component_modules_v1() -> dict[str, Any]:
    await db_manager.init_db()
    stats: dict[str, Any] = {
        "parent_template_code": PARENT_CODE,
        "created_templates": 0,
        "updated_templates": 0,
        "created_dossiers": 0,
        "updated_dossiers": 0,
        "created_links": 0,
        "updated_links": 0,
        "edge_stamps": 0,
        "aluminiu_active_preserved": None,
        "parent_bom_handoff": None,
    }

    async with db_manager.async_session_maker() as session:
        parent = (
            await session.execute(
                select(Product_templates).where(Product_templates.template_code == PARENT_CODE).limit(1)
            )
        ).scalar_one_or_none()
        if parent is None:
            raise RuntimeError(
                f"{PARENT_CODE} missing — run seed_tpl_volumetric_letters_v2 first."
            )

        family_id = str(parent.family_id or FAMILY_ID)
        family_name = str(parent.family_name or FAMILY_NAME)
        link_service = ProductTemplateModuleLinksService(session)

        for spec in CHILD_SPECS:
            payload = _child_template_payload(spec, family_id, family_name)
            existing = (
                await session.execute(
                    select(Product_templates)
                    .where(Product_templates.template_code == spec["template_code"])
                    .limit(1)
                )
            ).scalar_one_or_none()
            if existing is None:
                child = Product_templates(**payload)
                session.add(child)
                await session.flush()
                stats["created_templates"] += 1
            else:
                child = existing
                for key, value in payload.items():
                    setattr(child, key, value)
                stats["updated_templates"] += 1

            dossier_payload = _child_dossier_payload(child.id, spec)
            dossier = (
                await session.execute(
                    select(ProductBlueprintDossier)
                    .where(ProductBlueprintDossier.template_id == child.id)
                    .limit(1)
                )
            ).scalar_one_or_none()
            if dossier is None:
                session.add(ProductBlueprintDossier(**dossier_payload))
                stats["created_dossiers"] += 1
            else:
                for key, value in dossier_payload.items():
                    setattr(dossier, key, value)
                stats["updated_dossiers"] += 1

            _link, action = await link_service.upsert_by_contract(
                _link_payload(parent.id, child.id, spec)
            )
            if action == "created":
                stats["created_links"] += 1
            else:
                stats["updated_links"] += 1

        # Stamp contract fields on already-existing VL edges.
        from models.product_template_module_links import ProductTemplateModuleLink

        for stamp in EDGE_STAMPS:
            link = (
                await session.execute(
                    select(ProductTemplateModuleLink).where(
                        ProductTemplateModuleLink.parent_template_code == PARENT_CODE,
                        ProductTemplateModuleLink.module_template_code
                        == stamp["module_template_code"],
                    ).limit(1)
                )
            ).scalar_one_or_none()
            if link is None:
                continue
            link.usage_mode = stamp["usage_mode"]
            link.instance_schema_id = stamp["instance_schema_id"]
            stats["edge_stamps"] += 1

        # Owner ACTIVATION GO — preserve active Aluminiu; never force-deactivate or publish.
        aluminiu = (
            await session.execute(
                select(Product_templates)
                .where(Product_templates.template_code == VOLUM_ALUMINUM_TEMPLATE_CODE)
                .limit(1)
            )
        ).scalar_one_or_none()
        if aluminiu is not None:
            stats["aluminiu_active_preserved"] = bool(aluminiu.active)

        stats["parent_bom_handoff"] = _handoff_parent_bom(parent)

        parent_dossier = (
            await session.execute(
                select(ProductBlueprintDossier)
                .where(ProductBlueprintDossier.template_code == PARENT_CODE)
                .limit(1)
            )
        ).scalar_one_or_none()
        stats["parent_dossier_patched"] = _patch_parent_dossier(parent_dossier)

        await session.commit()

    logger.info("seed_tpl_volumetric_letters_component_modules_v1: %s", stats)
    return stats


async def _main() -> None:
    result = await seed_tpl_volumetric_letters_component_modules_v1()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_main())
