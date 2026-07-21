"""Seed TPL-ACM-BOXED-MOUNTING-SUPPORT_v1 — offerable boxed ACM mounting Product System template."""

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
from scripts.seed_acm_template_pack import (
    ACM_CASSETTED_QUOTE_INPUT_KEYS,
    CASSETTED_COMPONENTS,
)
from services.acm_boxed_support_composition_v1 import (
    APPLIED_CONTENT_LETTERS,
    APPLIED_CONTENT_LOGO,
    APPLIED_CONTENT_TRIGGER_FIELD,
    FRAME_DOMAIN_KIND,
    LETTERS_PACK_TEMPLATE_CODES,
    LOGO_PACK_TEMPLATE_CODES,
)
from services.product_template_module_links_service import ProductTemplateModuleLinksService

logger = logging.getLogger(__name__)

TEMPLATE_CODE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"
LETTERS_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS_v2"
FAMILY_ID = "panouri_acp_iluminate"
FAMILY_NAME = "Panouri ACP / ACM"

ACM_OPERATION_CODES = (
    "CUT_ACM_PANEL",
    "V_GROOVE_ROUTER",
    "FOLD_CASSETTE",
    "ACM_BOXED_ASSEMBLY",
    "MOUNT_ACM_PANEL",
)
ACM_COMPONENT_IDS = (
    "comp_acm_panel_face",
    "comp_casetted_returns",
    "comp_mounting_fasteners",
)


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _flatten_operations(components: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ops: list[dict[str, Any]] = []
    for component in components:
        cid = component.get("component_id")
        for op in component.get("operations") or []:
            if isinstance(op, dict):
                flat = dict(op)
                if cid and not flat.get("component_ref"):
                    flat["component_ref"] = cid
                ops.append(flat)
    return ops


def _boxed_mounting_components() -> list[dict[str, Any]]:
    """Boxed-mounting slice — owner commercial rates on dedicated workcenters."""
    import copy

    components = copy.deepcopy(CASSETTED_COMPONENTS)
    by_id = {comp["component_id"]: comp for comp in components}

    face = by_id["comp_acm_panel_face"]
    for op in face.get("operations") or []:
        if op.get("code") == "CUT_ACM_PANEL":
            op["workcenter"] = "ACM_PANEL_CUTTING"
            op["calculation_type"] = "formula_based"
            op["formula_id"] = "perimeter_based_time"
            op["formula_params"] = {
                "perimeter_quote_input_key": "panel_perimeter_m",
                "minutes_per_meter": 1.0,
                "passes": 1,
            }
            op["requires_quote_input"] = [
                "panel_width_mm",
                "panel_height_mm",
                "panel_perimeter_m",
                "acm_thickness_mm",
            ]
            op.pop("estimated_minutes", None)

    returns = by_id["comp_casetted_returns"]
    for op in returns.get("operations") or []:
        if op.get("code") == "V_GROOVE_ROUTER":
            op["workcenter"] = "ACM_V_GROOVE"
        elif op.get("code") == "FOLD_CASSETTE":
            op["quote_priced"] = False

    fasteners = by_id["comp_mounting_fasteners"]
    mount_ops = fasteners.get("operations") or []
    priced_assembly = {
        "code": "ACM_BOXED_ASSEMBLY",
        "name": "Asamblare suport ACM casetat (comercial)",
        "workcenter": "ACM_BOXED_ASSEMBLY",
        "sequence": 4,
        "component_ref": "comp_mounting_fasteners",
        "calculation_type": "formula_based",
        "formula_id": "area_from_quote_input",
        "formula_params": {"area_quote_input_key": "panel_area_m2"},
        "requires_quote_input": ["panel_area_m2"],
    }
    updated_mount_ops: list[dict[str, Any]] = []
    for op in mount_ops:
        if op.get("code") == "MOUNT_ACM_PANEL":
            op = dict(op)
            op["quote_priced"] = False
            op["sequence"] = 5
            updated_mount_ops.append(priced_assembly)
            updated_mount_ops.append(op)
        else:
            updated_mount_ops.append(op)
    if not any(op.get("code") == "ACM_BOXED_ASSEMBLY" for op in updated_mount_ops):
        updated_mount_ops.insert(0, priced_assembly)
    fasteners["operations"] = updated_mount_ops
    return components


def _flatten_materials(components: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mats: list[dict[str, Any]] = []
    for component in components:
        cid = component.get("component_id")
        for mat in component.get("materials") or []:
            if isinstance(mat, dict):
                flat = dict(mat)
                if cid:
                    flat["component_ref"] = cid
                mats.append(flat)
    return mats


def _template_payload() -> dict[str, Any]:
    components = _boxed_mounting_components()
    operations = _flatten_operations(components)
    materials = _flatten_materials(components)
    return {
        "template_code": TEMPLATE_CODE,
        "family_id": FAMILY_ID,
        "family_name": FAMILY_NAME,
        "description": (
            "Suport casetat ACM/Dibond pentru premontaj — template Product System separat, "
            "selectabil din Intake V6 Pregătire montaj sau ofertabil standalone."
        ),
        "components_json": _json_dumps(components),
        "operations_json": _json_dumps(operations),
        "required_materials_json": _json_dumps(materials),
        "estimated_hours": 2.5,
        "base_labor_rate": 80.0,
        "base_margin_pct": 40.0,
        "active": True,
        "notes": (
            "Owner GO 2026-07-13 PRODUCT_SYSTEM_ACM_BOXED_MOUNTING_TEMPLATE_V1. "
            "quote_input: "
            + ", ".join(ACM_CASSETTED_QUOTE_INPUT_KEYS)
            + ". Slice casetted components 1–3; not full illuminated panel product."
        ),
    }


def _dossier_payload(template_id: int) -> dict[str, Any]:
    sections = {
        "template_identity": {
            "template_code": TEMPLATE_CODE,
            "purpose": "Suport casetat ACM pentru premontaj / montaj litere volumetrice.",
            "owner_valid_active": True,
            "root_offerable": True,
        },
        "composition_extension_v1": {
            "decision": "A",
            "applied_content_xor": [APPLIED_CONTENT_LETTERS, APPLIED_CONTENT_LOGO],
            "letters_pack": list(LETTERS_PACK_TEMPLATE_CODES),
            "letters_root_reference": LETTERS_TEMPLATE_CODE,
            "logo_pack": list(LOGO_PACK_TEMPLATE_CODES),
            "logo_branch": "honestly_blocked_candidate_until_owner_go",
            "metal_frame": {
                "kind": FRAME_DOMAIN_KIND,
                "cardinality": "optional",
                "selection": "operator_explicit",
                "automatic_thresholds": False,
                "product_template": None,
            },
            "cycle_guard": "do_not_link_VL_root_under_ACM_while_VL_links_ACM",
        },
        "components": [
            {"id": cid, "label": cid.replace("comp_", "").replace("_", " ").upper()}
            for cid in ACM_COMPONENT_IDS
        ],
        "material_keys": ["MAT-ACM-BOND-PANEL", "MAT-SURUBURI-GEN"],
        "operation_keys": list(ACM_OPERATION_CODES),
    }
    return {
        "template_id": template_id,
        "template_code": TEMPLATE_CODE,
        "dossier_version": 1,
        "status": "approved",
        "sections_json": _json_dumps(sections),
        "variants_json": _json_dumps({"acm_thickness_mm": [3], "fold_sides": ["all", "top_bottom", "left_right"]}),
        "layers_json": _json_dumps({"layers": ["acm_boxed_mounting_support"]}),
        "task_rules_json": _json_dumps(
            {
                "tasks": [
                    {
                        "task_name": "cut_acm_panel",
                        "task_type": "cnc_routing",
                        "trigger_condition": "always",
                        "required_or_optional": "required",
                        "priced_operation": "CUT_ACM_PANEL",
                    },
                    {
                        "task_name": "v_groove_router",
                        "task_type": "cnc_routing",
                        "trigger_condition": "fold_length_m > 0",
                        "required_or_optional": "required",
                        "priced_operation": "V_GROOVE_ROUTER",
                    },
                    {
                        "task_name": "fold_cassette",
                        "task_type": "casette_assembly",
                        "trigger_condition": "return_depth_mm > 0",
                        "required_or_optional": "required",
                        "priced_operation": "FOLD_CASSETTE",
                    },
                    {
                        "task_name": "acm_boxed_assembly",
                        "task_type": "casette_assembly",
                        "trigger_condition": "always",
                        "required_or_optional": "required",
                        "priced_operation": "ACM_BOXED_ASSEMBLY",
                    },
                    {
                        "task_name": "mount_acm_panel",
                        "task_type": "installation_prep",
                        "trigger_condition": "always",
                        "required_or_optional": "required",
                        "priced_operation": "MOUNT_ACM_PANEL",
                    },
                ]
            }
        ),
        "costengine_mapping_json": _json_dumps(
            {
                "template_code": TEMPLATE_CODE,
                "inputs": {"required": ACM_CASSETTED_QUOTE_INPUT_KEYS},
                "pricing_source": "inventory_materials + workcenter_rates registries",
            }
        ),
        "quote_readiness_json": _json_dumps(
            {
                "ready_for_quote_selector": True,
                "reason": "Owner-approved offerable boxed ACM mounting support template.",
            }
        ),
        "owner_role": "product_owner",
        "reviewer_role": "technical_reviewer",
        "reviewed_at": datetime.now(timezone.utc),
    }


def _letters_module_link_payload(
    *,
    parent_template: Product_templates,
    child_template: Product_templates,
) -> dict[str, Any]:
    return {
        "parent_template_id": parent_template.id,
        "parent_template_code": LETTERS_TEMPLATE_CODE,
        "module_template_id": child_template.id,
        "module_template_code": TEMPLATE_CODE,
        "relation_type": "optional_addon",
        "trigger_field": "mounting_solution_active",
        "trigger_value_json": _json_dumps(True),
        "input_mapping_json": _json_dumps(
            {
                "width_mm": "panel_width_mm",
                "height_mm": "panel_height_mm",
            }
        ),
        "default_values_json": _json_dumps(
            {
                "panel_width_mm": 1000,
                "panel_height_mm": 600,
                "acm_thickness_mm": 3,
                "return_depth_mm": 60,
                "rear_lip_mm": 25,
                "fold_sides": "all",
                "v_groove_angle_deg": 135,
                "frame_clearance_mm": 0,
            }
        ),
        "pricing_mode": "separate_quote_line",
        "execution_mode": "linked_child_work",
        "active": True,
        "notes": (
            "Litere volumetrice — suport casetat ACM când operatorul selectează "
            "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1 în Pregătire montaj."
        ),
    }


def _applied_content_child_link_payload(
    *,
    parent_template: Product_templates,
    child_template: Product_templates,
    pack: str,
) -> dict[str, Any]:
    """ACM root → letters/logo pack child (Decision A composition extension)."""
    is_logo = pack == APPLIED_CONTENT_LOGO
    return {
        "parent_template_id": parent_template.id,
        "parent_template_code": TEMPLATE_CODE,
        "module_template_id": child_template.id,
        "module_template_code": child_template.template_code,
        "relation_type": "optional_addon",
        "trigger_field": APPLIED_CONTENT_TRIGGER_FIELD,
        "trigger_value_json": _json_dumps(pack),
        "input_mapping_json": _json_dumps(
            {
                "panel_width_mm": "width_mm",
                "panel_height_mm": "height_mm",
            }
        ),
        "default_values_json": _json_dumps(
            {
                APPLIED_CONTENT_TRIGGER_FIELD: pack,
                "metal_frame_optional": True,
                "metal_frame_domain": FRAME_DOMAIN_KIND,
            }
        ),
        "pricing_mode": "separate_quote_line",
        "execution_mode": "linked_child_work",
        "usage_mode": "linked_child",
        "instance_schema_id": (
            "acm_applied_logo_pack_v1" if is_logo else "acm_applied_letters_pack_v1"
        ),
        "active": True,
        "notes": (
            f"ACM boxed composition Decision A — applied_content={pack} XOR. "
            + (
                "Logo root candidate-blocked for offerability; edge is draft intent only."
                if is_logo
                else "Letters component reuse; VL root not linked (cycle guard)."
            )
        ),
    }


async def seed_tpl_acm_boxed_mounting_support_v1() -> dict[str, Any]:
    template_action = "unchanged"
    dossier_action = "unchanged"
    module_link_action = "unchanged"
    composition_link_actions: dict[str, str] = {}

    async with db_manager.async_session_maker() as session:
        existing = (
            await session.execute(
                select(Product_templates).where(Product_templates.template_code == TEMPLATE_CODE)
            )
        ).scalar_one_or_none()
        payload = _template_payload()
        if existing is None:
            template = Product_templates(**payload)
            session.add(template)
            await session.flush()
            template_action = "created"
        else:
            template = existing
            for key, value in payload.items():
                if key != "template_code":
                    setattr(template, key, value)
            template_action = "updated"

        dossier_payload = _dossier_payload(template.id)
        dossier = (
            await session.execute(
                select(ProductBlueprintDossier).where(ProductBlueprintDossier.template_id == template.id)
            )
        ).scalar_one_or_none()
        if dossier is None:
            session.add(ProductBlueprintDossier(**dossier_payload))
            dossier_action = "created"
        else:
            for key, value in dossier_payload.items():
                setattr(dossier, key, value)
            dossier_action = "updated"

        letters_template = (
            await session.execute(
                select(Product_templates).where(Product_templates.template_code == LETTERS_TEMPLATE_CODE)
            )
        ).scalar_one_or_none()
        if letters_template is not None:
            link_payload = _letters_module_link_payload(
                parent_template=letters_template,
                child_template=template,
            )
            _, module_link_action = await ProductTemplateModuleLinksService(session).upsert_by_contract(
                link_payload
            )
        else:
            module_link_action = "skipped_letters_template_missing"

        links_svc = ProductTemplateModuleLinksService(session)
        for child_code in LETTERS_PACK_TEMPLATE_CODES:
            child = (
                await session.execute(
                    select(Product_templates).where(Product_templates.template_code == child_code)
                )
            ).scalar_one_or_none()
            if child is None:
                composition_link_actions[child_code] = "skipped_missing"
                continue
            _, action = await links_svc.upsert_by_contract(
                _applied_content_child_link_payload(
                    parent_template=template,
                    child_template=child,
                    pack=APPLIED_CONTENT_LETTERS,
                )
            )
            composition_link_actions[child_code] = action

        for child_code in LOGO_PACK_TEMPLATE_CODES:
            child = (
                await session.execute(
                    select(Product_templates).where(Product_templates.template_code == child_code)
                )
            ).scalar_one_or_none()
            if child is None:
                composition_link_actions[child_code] = "skipped_missing"
                continue
            _, action = await links_svc.upsert_by_contract(
                _applied_content_child_link_payload(
                    parent_template=template,
                    child_template=child,
                    pack=APPLIED_CONTENT_LOGO,
                )
            )
            composition_link_actions[child_code] = action

        await session.commit()
        await session.refresh(template)

    stats = {
        "template_code": TEMPLATE_CODE,
        "template_action": template_action,
        "dossier_action": dossier_action,
        "module_link_action": module_link_action,
        "composition_link_actions": composition_link_actions,
        "letters_parent": LETTERS_TEMPLATE_CODE,
        "applied_content_xor": [APPLIED_CONTENT_LETTERS, APPLIED_CONTENT_LOGO],
        "active": True,
        "component_count": len(ACM_COMPONENT_IDS),
        "operation_count": len(ACM_OPERATION_CODES),
    }
    logger.info("seed_tpl_acm_boxed_mounting_support_v1: %s", stats)
    return stats


async def _main() -> None:
    await db_manager.init_db()
    try:
        await db_manager.create_tables()
        print(await seed_tpl_acm_boxed_mounting_support_v1())
    finally:
        await db_manager.close_db()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_main())
