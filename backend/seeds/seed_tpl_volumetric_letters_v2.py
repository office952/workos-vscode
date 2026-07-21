"""Create Product System template TPL-VOLUMETRIC-LETTERS_v2.

This promotes the V4 SVG/operator principles into a new Product System template
that the simplified Intake V5 can use as its source of truth: template contract,
blueprint dossier, and DB-backed pricing registries stay aligned.
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
from seeds.seed_intake_v5_volumetric_letters_pricing import (
    seed_intake_v5_volumetric_letters_pricing,
)
from seeds.seed_tpl_volumetric_letters_dossier import _dossier_payload

logger = logging.getLogger(__name__)

SOURCE_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS"
TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS_v2"
STRUCTURE_TEMPLATE_CODE = "TPL-METAL-PREMOUNT-STRUCTURE_v1"
VOLUM_ALUMINUM_TEMPLATE_CODE = "TPL-VOLUM-ALUMINIU_v1"
FAMILY_ID = "litere_volumetrice"
FAMILY_NAME = "Litere volumetrice"
STRUCTURE_FAMILY_ID = "structuri_metalice_premontaj"
STRUCTURE_FAMILY_NAME = "Structuri metalice premontaj"
VOLUM_ALUMINUM_FAMILY_ID = "volum_aluminiu_modular"
VOLUM_ALUMINUM_FAMILY_NAME = "Volum aluminiu modular"
PREMOUNT_COMPONENT_ID = "comp_premount_bars"
VOLUM_ALUMINUM_COMPONENT_ID = "comp_volum_aluminiu_module"
PREMOUNT_MATERIAL_CODES = {"MAT-PREMOUNT-BAR-STEEL", "MAT-PREMOUNT-BAR-ALUMINUM"}
VOLUM_ALUMINUM_MATERIAL_CODES = {
    "MAT-PROFIL-LATERAL-LITERE-30MM",
    "MAT-PROFIL-LATERAL-LITERE-60MM",
    "MAT-PROFIL-LATERAL-LITERE-80MM",
    "MAT-PROFIL-LATERAL-LITERE-100MM",
    "MAT-ORACAL-651",
    "MAT-VOPSEA-RAL",
    "MAT-ADEZIV-CANT-LITERE",
}


def _json_loads(raw: str | None, fallback: Any) -> Any:
    if not raw:
        return deepcopy(fallback)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return deepcopy(fallback)


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _replace_template_code(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _replace_template_code(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_template_code(item) for item in value]
    if value == SOURCE_TEMPLATE_CODE:
        return TEMPLATE_CODE
    if isinstance(value, str):
        return value.replace(SOURCE_TEMPLATE_CODE, TEMPLATE_CODE)
    return value


def _premount_bar_operation() -> dict[str, Any]:
    return {
        "code": "premount_bar_preparation",
        "name": "Debitare și pregătire bare premontaj",
        "workcenter": "WC_METAL_FAB",
        "sequence": 1,
        "estimatedMinutes": 0,
        "estimated_minutes": 0,
        "calculation_type": "formula_based",
        "formula_id": "premount_bar_linear_meter",
        "formula_params": {"non_priced": True},
        "requires_quote_input": ["premount_bar_length_ml"],
        "component_ref": PREMOUNT_COMPONENT_ID,
    }


def _premount_bar_materials() -> list[dict[str, Any]]:
    return [
        {
            "materialCode": "MAT-PREMOUNT-BAR-STEEL",
            "material_code": "MAT-PREMOUNT-BAR-STEEL",
            "name": "Bare premontaj oțel",
            "unit": "ml",
            "quantity": 0,
            "calculation_type": "formula_based",
            "formula_id": "premount_bar_linear_meter",
            "formula_params": {"gate": {"bar_material": "steel"}},
            "requires_quote_input": ["premount_bar_length_ml"],
            "component_ref": PREMOUNT_COMPONENT_ID,
        },
        {
            "materialCode": "MAT-PREMOUNT-BAR-ALUMINUM",
            "material_code": "MAT-PREMOUNT-BAR-ALUMINUM",
            "name": "Bare premontaj aluminiu",
            "unit": "ml",
            "quantity": 0,
            "calculation_type": "formula_based",
            "formula_id": "premount_bar_linear_meter",
            "formula_params": {"gate": {"bar_material": "aluminum"}},
            "requires_quote_input": ["premount_bar_length_ml"],
            "component_ref": PREMOUNT_COMPONENT_ID,
        },
    ]


def _ensure_v2_components(source: Product_templates | None) -> tuple[str, str, str]:
    components = _json_loads(source.components_json if source else None, [])
    operations = _json_loads(source.operations_json if source else None, [])
    materials = _json_loads(source.required_materials_json if source else None, [])

    canonical_component_metadata = {
        "comp_face_litere": {
            "type": "LITERE_3D",
            "name": "Vizual față — plexi/acrilic",
        },
        "comp_lateral_litere": {
            "type": "LITERE_3D",
            "name": "Volum aluminiu — profil lateral",
        },
        "comp_spate_litere": {
            "type": "STRUCTURA",
            "name": "Capac spate — Forex 10 mm",
        },
        "comp_led_litere": {
            "type": "ELECTRIC_LED",
            "name": "Sistem LED — module, surse, cablaj",
        },
        "comp_finisaj_litere": {
            "type": "FINISAJ",
            "name": "Finisaj — vopsire, asamblare, ambalare",
        },
    }

    components = [
        c for c in components
        if not (
            isinstance(c, dict)
            and c.get("component_id") in {"comp_svg_analysis_intake", PREMOUNT_COMPONENT_ID}
        )
    ]

    operations = [op for op in operations if isinstance(op, dict)]
    for op in operations:
        if op.get("code") == "svg_geometry_analysis":
            op["component_ref"] = "comp_face_litere"
            op.setdefault("formula_params", {})["non_priced"] = True

    operations = [
        op for op in operations
        if op.get("code") != "premount_bar_preparation"
        and op.get("component_ref") != PREMOUNT_COMPONENT_ID
    ]
    materials = [
        material for material in materials
        if isinstance(material, dict)
        and material.get("component_ref") != PREMOUNT_COMPONENT_ID
        and (material.get("material_code") or material.get("materialCode")) not in PREMOUNT_MATERIAL_CODES
    ]
    operation_codes = {op.get("code") for op in operations if isinstance(op, dict)}
    if "svg_geometry_analysis" not in operation_codes:
        operations.insert(
            0,
            {
                "code": "svg_geometry_analysis",
                "workcenter": "PREPRESS",
                "sequence": 0,
                "estimatedMinutes": 0,
                "estimated_minutes": 0,
                "calculation_type": "formula_based",
                "formula_id": "svg_geometry_readiness_gate",
                "formula_params": {
                    "source": "intake-v4/operator-ui",
                    "non_priced": True,
                },
                "requires_quote_input": ["vector_file"],
                "label": "Analiză SVG și mapare layere/culori",
                "component_ref": "comp_face_litere",
            },
        )

    material_codes = {
        (m.get("material_code") or m.get("materialCode"))
        for m in materials
        if isinstance(m, dict)
    }
    if "MAT-SABLON-MONTAJ" not in material_codes:
        materials.append(
            {
                "materialCode": "MAT-SABLON-MONTAJ",
                "material_code": "MAT-SABLON-MONTAJ",
                "unit": "mp",
                "quantity": 0,
                "calculation_type": "formula_based",
                "formula_id": "mounting_template_area",
                "formula_params": {"waste_pct": 0.05, "gate": {"mounting_template_enabled": True}},
                "requires_quote_input": ["mounting_template_area_m2"],
                "label": "Șablon montaj Forex 3 mm",
                "component_ref": "comp_finisaj_litere",
            }
        )
    if "MAT-SABLON-HARTIE" not in material_codes:
        materials.append(
            {
                "materialCode": "MAT-SABLON-HARTIE",
                "material_code": "MAT-SABLON-HARTIE",
                "unit": "mp",
                "quantity": 0,
                "calculation_type": "formula_based",
                "formula_id": "mounting_template_area",
                "formula_params": {
                    "waste_pct": 0.05,
                    "gate": {
                        "mounting_template_enabled": True,
                        "mounting_template_material_type": "paper",
                    },
                },
                "requires_quote_input": ["mounting_template_area_m2"],
                "label": "Șablon montaj hârtie",
                "component_ref": "comp_finisaj_litere",
            }
        )

    operations_by_component: dict[str, list[dict[str, Any]]] = {}
    for op in operations:
        component_ref = op.get("component_ref")
        if component_ref:
            operations_by_component.setdefault(str(component_ref), []).append(op)

    materials_by_component: dict[str, list[dict[str, Any]]] = {}
    for material in materials:
        if not isinstance(material, dict):
            continue
        component_ref = material.get("component_ref")
        if component_ref:
            materials_by_component.setdefault(str(component_ref), []).append(material)

    for component in components:
        if not isinstance(component, dict):
            continue
        component_id = str(component.get("component_id") or "")
        if component_id in canonical_component_metadata:
            component.update(canonical_component_metadata[component_id])
        if component_id:
            component["operations"] = operations_by_component.get(component_id, component.get("operations") or [])
            component["materials"] = materials_by_component.get(component_id, component.get("materials") or [])

    return _json_dumps(components), _json_dumps(operations), _json_dumps(materials)


def _metal_structure_template_payload() -> dict[str, Any]:
    operation = _premount_bar_operation()
    materials = _premount_bar_materials()
    component = {
        "component_id": PREMOUNT_COMPONENT_ID,
        "type": "STRUCTURA",
        "name": "Structură metalică — bare premontaj",
        "operations": [operation],
        "materials": materials,
    }
    return {
        "template_code": STRUCTURE_TEMPLATE_CODE,
        "family_id": STRUCTURE_FAMILY_ID,
        "family_name": STRUCTURE_FAMILY_NAME,
        "description": (
            "Template activ separat pentru bare premontaj oțel/aluminiu. Nu este parte din "
            "template-ul de litere volumetrice; se instrumentează și validează separat."
        ),
        "components_json": _json_dumps([component]),
        "operations_json": _json_dumps([operation]),
        "required_materials_json": _json_dumps(materials),
        "estimated_hours": 1.0,
        "base_labor_rate": 80.0,
        "base_margin_pct": 40.0,
        "active": True,
        "notes": (
            "Separated from TPL-VOLUMETRIC-LETTERS_v2 on owner request. "
            "Instrumentare separată pentru structură metalică/premontaj."
        ),
    }


def _metal_structure_dossier_payload(template_id: int) -> dict[str, Any]:
    sections = {
        "template_identity": {
            "template_code": STRUCTURE_TEMPLATE_CODE,
            "source_template_code": TEMPLATE_CODE,
            "purpose": "Instrumentare separată pentru bare premontaj oțel/aluminiu.",
            "owner_valid_active": True,
        },
        "components": [
            {
                "id": PREMOUNT_COMPONENT_ID,
                "label": "STRUCTURĂ METALICĂ",
                "role": "bare premontaj oțel/aluminiu, calculate la metru liniar",
            }
        ],
        "material_keys": sorted(PREMOUNT_MATERIAL_CODES),
        "operation_keys": ["premount_bar_preparation"],
    }
    return {
        "template_id": template_id,
        "template_code": STRUCTURE_TEMPLATE_CODE,
        "dossier_version": 1,
        "status": "approved",
        "sections_json": _json_dumps(sections),
        "variants_json": _json_dumps({"variants": ["steel_bars", "aluminum_bars"]}),
        "layers_json": _json_dumps({"layers": ["premount_bar"]}),
        "task_rules_json": _json_dumps(
            {
                "tasks": [
                    {
                        "task_name": "premount_bars",
                        "task_type": "CNC_ROUTER",
                        "trigger_condition": "mounting_system steel_bars|aluminum_bars",
                        "required_or_optional": "optional",
                        "priced_operation": "premount_bar_preparation",
                    }
                ]
            }
        ),
        "costengine_mapping_json": _json_dumps(
            {
                "template_code": STRUCTURE_TEMPLATE_CODE,
                "inputs": {"required": ["premount_bar_length_ml", "mounting_bar_profile"]},
                "pricing_source": "inventory_materials + workcenter_rates registries",
            }
        ),
        "quote_readiness_json": _json_dumps(
            {
                "ready_for_quote_selector": True,
                "reason": "Template activ separat pentru instrumentare premontaj.",
            }
        ),
        "owner_role": "product_owner",
        "reviewer_role": "technical_reviewer",
        "reviewed_at": datetime.now(timezone.utc),
    }


def _volum_aluminum_template_payload() -> dict[str, Any]:
    operations = [
        {
            "code": "RETURN_PROFILE_MACHINE_FORMING",
            "name": "Modelare cant profil litere — utilaj",
            "label": "Modelare cant profil litere — utilaj",
            "workcenter": "WC_FORMING",
            "sequence": 1,
            "estimatedMinutes": 0,
            "estimated_minutes": 0,
            "calculation_type": "formula_based",
            "formula_id": "return_profile_machine_forming",
            "requires_quote_input": ["return_depth_mm"],
            "component_ref": VOLUM_ALUMINUM_COMPONENT_ID,
        },
        {
            "code": "RETURN_PROFILE_FACE_BONDING",
            "name": "Lipire cant profil pe față litere",
            "label": "Lipire cant profil pe față litere",
            "workcenter": "WC_ASSEMBLY",
            "sequence": 2,
            "estimatedMinutes": 0,
            "estimated_minutes": 0,
            "calculation_type": "formula_based",
            "formula_id": "return_profile_face_bonding",
            "requires_quote_input": ["return_depth_mm"],
            "component_ref": VOLUM_ALUMINUM_COMPONENT_ID,
        },
        {
            "code": "PAINTING",
            "name": "Vopsire RAL — serviciu perimetru",
            "label": "Vopsire RAL — serviciu perimetru",
            "workcenter": "WC_PAINT",
            "sequence": 3,
            "estimatedMinutes": 0,
            "estimated_minutes": 0,
            "calculation_type": "formula_based",
            "formula_id": "return_painting_linear_meter",
            "formula_params": {"gate": {"return_finish_type": "ral_paint"}},
            "requires_quote_input": ["return_depth_mm", "return_finish_type"],
            "component_ref": VOLUM_ALUMINUM_COMPONENT_ID,
        },
    ]
    materials = [
        {
            "materialCode": "MAT-PROFIL-LATERAL-LITERE-30MM",
            "material_code": "MAT-PROFIL-LATERAL-LITERE-30MM",
            "name": "Profil aluminiu return/cant 30 mm",
            "unit": "ml",
            "quantity": 0,
            "calculation_type": "formula_based",
            "formula_id": "return_profile_linear_meter",
            "formula_params": {"gate": {"return_depth_mm": 30}},
            "requires_quote_input": ["return_depth_mm"],
            "component_ref": VOLUM_ALUMINUM_COMPONENT_ID,
        },
        {
            "materialCode": "MAT-PROFIL-LATERAL-LITERE-60MM",
            "material_code": "MAT-PROFIL-LATERAL-LITERE-60MM",
            "name": "Profil aluminiu return/cant 60 mm",
            "unit": "ml",
            "quantity": 0,
            "calculation_type": "formula_based",
            "formula_id": "return_profile_linear_meter",
            "formula_params": {"gate": {"return_depth_mm": 60}},
            "requires_quote_input": ["return_depth_mm"],
            "component_ref": VOLUM_ALUMINUM_COMPONENT_ID,
        },
        {
            "materialCode": "MAT-PROFIL-LATERAL-LITERE-80MM",
            "material_code": "MAT-PROFIL-LATERAL-LITERE-80MM",
            "name": "Profil aluminiu return/cant 80 mm",
            "unit": "ml",
            "quantity": 0,
            "calculation_type": "formula_based",
            "formula_id": "return_profile_linear_meter",
            "formula_params": {"gate": {"return_depth_mm": 80}},
            "requires_quote_input": ["return_depth_mm"],
            "component_ref": VOLUM_ALUMINUM_COMPONENT_ID,
        },
        {
            "materialCode": "MAT-PROFIL-LATERAL-LITERE-100MM",
            "material_code": "MAT-PROFIL-LATERAL-LITERE-100MM",
            "name": "Profil aluminiu return/cant 100 mm",
            "unit": "ml",
            "quantity": 0,
            "calculation_type": "formula_based",
            "formula_id": "return_profile_linear_meter",
            "formula_params": {"gate": {"return_depth_mm": 100}},
            "requires_quote_input": ["return_depth_mm"],
            "component_ref": VOLUM_ALUMINUM_COMPONENT_ID,
        },
        {
            "materialCode": "MAT-ORACAL-651",
            "material_code": "MAT-ORACAL-651",
            "name": "Folie autocolantă PVC — Oracal 651",
            "unit": "mp",
            "quantity": 0,
            "calculation_type": "formula_based",
            "formula_id": "return_wrap_area",
            "formula_params": {"gate": {"return_finish_type": "oracal_wrapped"}},
            "requires_quote_input": ["return_finish_type", "return_depth_mm"],
            "component_ref": VOLUM_ALUMINUM_COMPONENT_ID,
        },
        {
            "materialCode": "MAT-VOPSEA-RAL",
            "material_code": "MAT-VOPSEA-RAL",
            "name": "Vopsea RAL spray — tub",
            "unit": "buc",
            "quantity": 0,
            "calculation_type": "formula_based",
            "formula_id": "return_paint_consumption",
            "formula_params": {"gate": {"return_finish_type": "ral_paint"}},
            "requires_quote_input": ["return_finish_type", "return_depth_mm"],
            "component_ref": VOLUM_ALUMINUM_COMPONENT_ID,
        },
        {
            "materialCode": "MAT-ADEZIV-CANT-LITERE",
            "material_code": "MAT-ADEZIV-CANT-LITERE",
            "name": "Adeziv lipire cant / module LED",
            "unit": "ml",
            "quantity": 0,
            "calculation_type": "formula_based",
            "formula_id": "return_profile_adhesive",
            "requires_quote_input": ["return_depth_mm"],
            "component_ref": VOLUM_ALUMINUM_COMPONENT_ID,
        },
    ]
    component = {
        "component_id": VOLUM_ALUMINUM_COMPONENT_ID,
        "type": "LITERE_3D",
        "name": "Volum aluminiu — profil lateral modular",
        "operations": operations,
        "materials": materials,
    }
    return {
        "template_code": VOLUM_ALUMINUM_TEMPLATE_CODE,
        "family_id": VOLUM_ALUMINUM_FAMILY_ID,
        "family_name": VOLUM_ALUMINUM_FAMILY_NAME,
        "description": (
            "Template modular separat pentru volum aluminiu / profil lateral din litere volumetrice. "
            "Leagă formarea, lipirea și finisajul cantului într-un child-template reutilizabil."
        ),
        "components_json": _json_dumps([component]),
        "operations_json": _json_dumps(operations),
        "required_materials_json": _json_dumps(materials),
        "estimated_hours": 3.0,
        "base_labor_rate": 80.0,
        "base_margin_pct": 40.0,
        # Owner ACTIVATION GO — component active; parent publication remains a separate GO.
        "active": True,
        "notes": "Modul separat extras din TPL-VOLUMETRIC-LETTERS_v2 pentru volum aluminiu / cant profil lateral.",
    }


def _volum_aluminum_dossier_payload(template_id: int) -> dict[str, Any]:
    sections = {
        "template_identity": {
            "template_code": VOLUM_ALUMINUM_TEMPLATE_CODE,
            "source_template_code": TEMPLATE_CODE,
            "purpose": "Instrumentare modulară separată pentru volum aluminiu / profil lateral.",
            "owner_valid_active": True,
        },
        "components": [
            {
                "id": VOLUM_ALUMINUM_COMPONENT_ID,
                "label": "VOLUM ALUMINIU",
                "role": "formare, lipire și finisare profil lateral / return cant",
            }
        ],
        "material_keys": sorted(VOLUM_ALUMINUM_MATERIAL_CODES),
        "operation_keys": [
            "RETURN_PROFILE_MACHINE_FORMING",
            "RETURN_PROFILE_FACE_BONDING",
            "PAINTING",
        ],
    }
    return {
        "template_id": template_id,
        "template_code": VOLUM_ALUMINUM_TEMPLATE_CODE,
        "dossier_version": 1,
        "status": "approved",
        "sections_json": _json_dumps(sections),
        "variants_json": _json_dumps(
            {
                "variants": [
                    {
                        "variant_key": "volum_aluminum_module_template_code",
                        "label": "Template modul volum aluminiu",
                        "allowed_values": [VOLUM_ALUMINUM_TEMPLATE_CODE],
                        "default_value": VOLUM_ALUMINUM_TEMPLATE_CODE,
                    }
                ]
            }
        ),
        "layers_json": _json_dumps({"layers": ["return_profile"]}),
        "task_rules_json": _json_dumps(
            {
                "tasks": [
                    {
                        "task_name": "volum_aluminum_module",
                        "task_type": "EDGE_RETURN_MODULE",
                        "trigger_condition": "return_depth_mm > 0",
                        "required_or_optional": "required",
                        "priced_operation": "RETURN_PROFILE_MACHINE_FORMING",
                    }
                ]
            }
        ),
        "costengine_mapping_json": _json_dumps(
            {
                "template_code": VOLUM_ALUMINUM_TEMPLATE_CODE,
                "inputs": {"required": ["return_depth_mm", "return_finish_type"]},
                "pricing_source": "inventory_materials + workcenter_rates registries",
            }
        ),
        "quote_readiness_json": _json_dumps(
            {
                "ready_for_quote_selector": True,
                "reason": "Template modular activ separat pentru volum aluminiu / profil lateral.",
            }
        ),
        "owner_role": "product_owner",
        "reviewer_role": "technical_reviewer",
        "reviewed_at": datetime.now(timezone.utc),
    }


def _strip_premount_references(value: Any) -> Any:
    removed_string_values = {
        PREMOUNT_COMPONENT_ID,
        "premount_bars",
        *PREMOUNT_MATERIAL_CODES,
        "mounting_system",
        "mounting_bar_profile",
        "mounting_bar_count",
        "mounting_bar_length_m",
        "premount_bar_length_ml",
        "steel_bars",
        "aluminum_bars",
        "acm_panel",
    }
    if isinstance(value, dict):
        identity = value.get("id") or value.get("task_name") or value.get("code") or value.get("variant_key") or value.get("block_id")
        if identity in {
            PREMOUNT_COMPONENT_ID,
            "premount_bars",
            "premount_bar_preparation",
            "mounting_system",
            "mounting_bar_profile",
            "acm_panel_separate_template",
            "mounting_options",
        }:
            return None
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if key in {"mounting_system", "mounting_bar_profile", "mounting_bar_count", "mounting_bar_length_m"}:
                continue
            next_value = _strip_premount_references(item)
            if next_value is not None:
                cleaned[key] = next_value
        return cleaned
    if isinstance(value, list):
        cleaned_items = []
        for item in value:
            next_value = _strip_premount_references(item)
            if next_value is not None:
                cleaned_items.append(next_value)
        return cleaned_items
    if isinstance(value, str):
        if value in removed_string_values:
            return None
        lowered = value.lower()
        if "premount" in lowered or "premontaj" in lowered or "mounting_bar" in lowered or "steel_bars" in lowered or "aluminum_bars" in lowered:
            return None
    return value


def _v2_dossier_payload(template_id: int) -> dict[str, Any]:
    payload = _replace_template_code(_dossier_payload())
    payload["template_id"] = template_id
    payload["template_code"] = TEMPLATE_CODE
    payload["dossier_version"] = 3
    payload["status"] = "approved"
    payload["owner_role"] = "product_owner"
    payload["reviewer_role"] = "technical_reviewer"
    payload["reviewed_at"] = datetime.now(timezone.utc)

    sections = _json_loads(payload.get("sections_json"), {})
    sections = _strip_premount_references(sections) or {}
    sections.setdefault("template_identity", {})
    sections["template_identity"].update(
        {
            "template_code": TEMPLATE_CODE,
            "source_template_code": SOURCE_TEMPLATE_CODE,
            "source_intake": "intake-v4/operator-ui",
            "generated_form_target": "intake-v5",
            "purpose": (
                "Template v2 pentru litere volumetrice: preia analiza SVG/layering din Intake V4 "
                "și produce formular simplificat, prețuit din registre DB."
            ),
        }
    )
    sections["svg_analysis_contract"] = {
        "source": "intake-v4/operator-ui",
        "server_analyzer": "services.svg_analyzer.analyze_svg",
        "geometry_outputs": [
            "width_mm",
            "height_mm",
            "letter_groups",
            "artwork_groups",
            "letter_count",
            "letter_face_area_m2",
            "letter_perimeter_m",
            "artwork_perimeter_m",
            "total_perimeter_m",
        ],
        "form_autofill": {
            "width_mm": "document.width_mm",
            "height_mm": "document.height_mm",
            "letter_count": "totals.letter_count",
            "letter_face_area_m2": "totals.letter_face_area_m2",
            "letter_perimeter_m": "totals.letter_perimeter_m",
            "mounting_template_area_m2": "document.width_mm * document.height_mm / 1_000_000",
        },
    }
    payload["sections_json"] = _json_dumps(sections)

    mapping = _json_loads(payload.get("costengine_mapping_json"), {})
    mapping = _strip_premount_references(mapping) or {}
    mapping.update(
        {
            "template_code": TEMPLATE_CODE,
            "source_template_code": SOURCE_TEMPLATE_CODE,
            "source_intake": "intake-v4/operator-ui",
            "generated_form_target": "intake-v5",
            "pricing_ready": True,
        }
    )
    mapping.setdefault("inputs", {}).setdefault("required", [])
    for key in ["width_mm", "height_mm", "mounting_template_enabled", "mounting_template_area_m2"]:
        if key not in mapping["inputs"]["required"]:
            mapping["inputs"]["required"].append(key)
    payload["costengine_mapping_json"] = _json_dumps(mapping)

    quote_readiness = _json_loads(payload.get("quote_readiness_json"), {})
    quote_readiness = _strip_premount_references(quote_readiness) or {}
    quote_readiness["v2_policy"] = {
        "template_created_from": "intake-v4/operator-ui principles",
        "svg_auto_analysis_required_for_final_quote": True,
        "manual_geometry_allowed_for_preliminary_simulation": True,
        "pricing_source": "inventory_materials + workcenter_rates registries",
    }
    payload["quote_readiness_json"] = _json_dumps(quote_readiness)

    for json_field in [
        "variants_json",
        "layers_json",
        "task_rules_json",
        "time_assumptions_json",
        "production_notes_json",
        "qc_checkpoints_json",
        "risks_json",
    ]:
        payload[json_field] = _json_dumps(
            _strip_premount_references(_json_loads(payload.get(json_field), {})) or {}
        )
    return payload


async def seed_tpl_volumetric_letters_v2() -> dict[str, Any]:
    pricing_stats = await seed_intake_v5_volumetric_letters_pricing()
    await db_manager.create_tables()
    async with db_manager.async_session_maker() as session:
        legacy_source = (
            await session.execute(
                select(Product_templates).where(Product_templates.template_code == SOURCE_TEMPLATE_CODE)
            )
        ).scalar_one_or_none()
        existing = (
            await session.execute(
                select(Product_templates).where(Product_templates.template_code == TEMPLATE_CODE)
            )
        ).scalar_one_or_none()

        source = legacy_source or existing
        components_json, operations_json, required_materials_json = _ensure_v2_components(source)
        template_payload = {
            "template_code": TEMPLATE_CODE,
            "family_id": FAMILY_ID,
            "family_name": FAMILY_NAME,
            "description": (
                "Litere volumetrice v2 — template generat din principiile Intake V4: "
                "analiză SVG/layering, formular simplificat, BOM și prețuri din registre DB."
            ),
            "components_json": components_json,
            "operations_json": operations_json,
            "required_materials_json": required_materials_json,
            "estimated_hours": source.estimated_hours if source else 12.0,
            "base_labor_rate": source.base_labor_rate if source else 80.0,
            "base_margin_pct": source.base_margin_pct if source else 40.0,
            "active": True,
            "notes": (
                "V2 source: Intake V4 operator UI SVG analyzer principles. "
                "Used by Intake V5 as generated simplified form with DB-backed pricing."
            ),
        }

        if existing is None:
            template = Product_templates(**template_payload)
            session.add(template)
            await session.flush()
            template_action = "created"
        else:
            template = existing
            for key, value in template_payload.items():
                setattr(template, key, value)
            template_action = "updated"

        dossier_payload = _v2_dossier_payload(template.id)
        dossier = (
            await session.execute(
                select(ProductBlueprintDossier).where(ProductBlueprintDossier.template_id == template.id)
            )
        ).scalar_one_or_none()
        if dossier is None:
            dossier = ProductBlueprintDossier(**dossier_payload)
            session.add(dossier)
            dossier_action = "created"
        else:
            for key, value in dossier_payload.items():
                setattr(dossier, key, value)
            dossier_action = "updated"

        structure_template_payload = _metal_structure_template_payload()
        structure_existing = (
            await session.execute(
                select(Product_templates).where(Product_templates.template_code == STRUCTURE_TEMPLATE_CODE)
            )
        ).scalar_one_or_none()
        if structure_existing is None:
            structure_template = Product_templates(**structure_template_payload)
            session.add(structure_template)
            await session.flush()
            structure_template_action = "created"
        else:
            structure_template = structure_existing
            for key, value in structure_template_payload.items():
                setattr(structure_template, key, value)
            structure_template_action = "updated"

        structure_dossier_payload = _metal_structure_dossier_payload(structure_template.id)
        structure_dossier = (
            await session.execute(
                select(ProductBlueprintDossier).where(
                    ProductBlueprintDossier.template_id == structure_template.id
                )
            )
        ).scalar_one_or_none()
        if structure_dossier is None:
            structure_dossier = ProductBlueprintDossier(**structure_dossier_payload)
            session.add(structure_dossier)
            structure_dossier_action = "created"
        else:
            for key, value in structure_dossier_payload.items():
                setattr(structure_dossier, key, value)
            structure_dossier_action = "updated"

        volum_aluminum_template_payload = _volum_aluminum_template_payload()
        volum_aluminum_existing = (
            await session.execute(
                select(Product_templates).where(
                    Product_templates.template_code == VOLUM_ALUMINUM_TEMPLATE_CODE
                )
            )
        ).scalar_one_or_none()
        if volum_aluminum_existing is None:
            volum_aluminum_template = Product_templates(**volum_aluminum_template_payload)
            session.add(volum_aluminum_template)
            await session.flush()
            volum_aluminum_template_action = "created"
        else:
            volum_aluminum_template = volum_aluminum_existing
            # Owner ACTIVATION GO — seed may set active=True; never force-deactivate on reseed.
            # Do not touch publication_status / published_* (activate-only).
            for key, value in volum_aluminum_template_payload.items():
                if key in {
                    "publication_status",
                    "publication_version",
                    "published_at",
                    "published_by",
                    "last_e2e_verdict",
                    "last_e2e_checked_at",
                }:
                    continue
                setattr(volum_aluminum_template, key, value)
            volum_aluminum_template_action = "updated"

        volum_aluminum_dossier_payload = _volum_aluminum_dossier_payload(volum_aluminum_template.id)
        volum_aluminum_dossier = (
            await session.execute(
                select(ProductBlueprintDossier).where(
                    ProductBlueprintDossier.template_id == volum_aluminum_template.id
                )
            )
        ).scalar_one_or_none()
        if volum_aluminum_dossier is None:
            volum_aluminum_dossier = ProductBlueprintDossier(**volum_aluminum_dossier_payload)
            session.add(volum_aluminum_dossier)
            volum_aluminum_dossier_action = "created"
        else:
            for key, value in volum_aluminum_dossier_payload.items():
                setattr(volum_aluminum_dossier, key, value)
            volum_aluminum_dossier_action = "updated"

        module_link_payload = {
            "parent_template_id": template.id,
            "parent_template_code": TEMPLATE_CODE,
            "module_template_id": structure_template.id,
            "module_template_code": STRUCTURE_TEMPLATE_CODE,
            "relation_type": "optional_addon",
            "trigger_field": "metal_support_required",
            "trigger_value_json": _json_dumps(True),
            "input_mapping_json": _json_dumps(
                {
                    "width_mm": "premount_bar_length_ml",
                    "support_material": "bar_material",
                    "support_profile": "mounting_bar_profile",
                }
            ),
            "default_values_json": _json_dumps(
                {
                    "bar_count": 2,
                    "mounting_bar_profile": "30x30x1.5",
                    "bar_material": "steel",
                }
            ),
            "pricing_mode": "separate_quote_line",
            "execution_mode": "linked_child_work",
            "active": True,
            "notes": "Literele volumetrice atașează structura metalică doar când oferta cere suport din bare.",
        }
        module_link, module_link_action = await ProductTemplateModuleLinksService(session).upsert_by_contract(
            module_link_payload
        )

        volum_aluminum_module_link_payload = {
            "parent_template_id": template.id,
            "parent_template_code": TEMPLATE_CODE,
            "module_template_id": volum_aluminum_template.id,
            "module_template_code": VOLUM_ALUMINUM_TEMPLATE_CODE,
            "relation_type": "required_module",
            "trigger_field": "volum_aluminum_module_template_code",
            "trigger_value_json": _json_dumps([VOLUM_ALUMINUM_TEMPLATE_CODE]),
            "input_mapping_json": _json_dumps(
                {
                    "return_depth_mm": "return_depth_mm",
                    "return_finish_type": "return_finish_type",
                    "return_oracal_code": "return_oracal_code",
                }
            ),
            "default_values_json": _json_dumps(
                {
                    "volum_aluminum_module_template_code": VOLUM_ALUMINUM_TEMPLATE_CODE,
                    "return_finish_type": "white_aluminum",
                }
            ),
            "pricing_mode": "separate_quote_line",
            "execution_mode": "linked_child_work",
            "active": True,
            "notes": "Volum aluminiu este instrumentat modular separat din template-ul mamă pentru Intake V6.",
        }
        volum_aluminum_module_link, volum_aluminum_module_link_action = await ProductTemplateModuleLinksService(session).upsert_by_contract(
            volum_aluminum_module_link_payload
        )

        await session.commit()
        await session.refresh(template)
        await session.refresh(dossier)
        await session.refresh(structure_template)
        await session.refresh(structure_dossier)
        await session.refresh(module_link)
        await session.refresh(volum_aluminum_template)
        await session.refresh(volum_aluminum_dossier)
        await session.refresh(volum_aluminum_module_link)

        result = {
            "template_code": TEMPLATE_CODE,
            "template_id": template.id,
            "template_action": template_action,
            "dossier_id": dossier.id,
            "dossier_action": dossier_action,
            "dossier_status": dossier.status,
            "structure_template_code": STRUCTURE_TEMPLATE_CODE,
            "structure_template_id": structure_template.id,
            "structure_template_action": structure_template_action,
            "structure_dossier_id": structure_dossier.id,
            "structure_dossier_action": structure_dossier_action,
            "structure_active": structure_template.active,
            "module_link_id": module_link.id,
            "module_link_action": module_link_action,
            "volum_aluminum_template_code": VOLUM_ALUMINUM_TEMPLATE_CODE,
            "volum_aluminum_template_id": volum_aluminum_template.id,
            "volum_aluminum_template_action": volum_aluminum_template_action,
            "volum_aluminum_dossier_id": volum_aluminum_dossier.id,
            "volum_aluminum_dossier_action": volum_aluminum_dossier_action,
            "volum_aluminum_active": volum_aluminum_template.active,
            "volum_aluminum_module_link_id": volum_aluminum_module_link.id,
            "volum_aluminum_module_link_action": volum_aluminum_module_link_action,
            "pricing": pricing_stats,
        }
        logger.info("Seeded %s: %s", TEMPLATE_CODE, result)
        return result


async def _main() -> None:
    await db_manager.init_db()
    result = await seed_tpl_volumetric_letters_v2()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_main())
