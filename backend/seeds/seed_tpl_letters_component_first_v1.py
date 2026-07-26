"""Create inert component-first letters templates in product_templates.

This seed is intentionally NOT wired into any live seed runner.
It creates a grouped, fully inactive candidate family for future
component-first letters work. No module links, dossiers, pricing wiring,
ProductDefinition wiring, or executable BOM rows are created here.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from sqlalchemy import select

from core.database import db_manager
import models  # noqa: F401
from models.product_templates import Product_templates

logger = logging.getLogger(__name__)

COMPOSER_TEMPLATE_CODE = "TPL-LETTERS-COMPOSER_v1"
FACE_TEMPLATE_CODE = "TPL-COMP-LETTER-FACE_v1"
BACK_TEMPLATE_CODE = "TPL-COMP-LETTER-BACK_v1"
RETURN_CANT_TEMPLATE_CODE = "TPL-COMP-LETTER-RETURN-CANT_v1"
LED_TEMPLATE_CODE = "TPL-COMP-LETTER-LED_v1"
FINISH_TEMPLATE_CODE = "TPL-COMP-LETTER-FINISH_v1"
MOUNTING_TEMPLATE_CODE = "TPL-COMP-LETTER-MOUNTING_v1"

ALL_TEMPLATE_CODES = [
    COMPOSER_TEMPLATE_CODE,
    FACE_TEMPLATE_CODE,
    BACK_TEMPLATE_CODE,
    RETURN_CANT_TEMPLATE_CODE,
    LED_TEMPLATE_CODE,
    FINISH_TEMPLATE_CODE,
    MOUNTING_TEMPLATE_CODE,
]

FAMILY_ID = "litere_component_first_candidate"
FAMILY_NAME = "Litere component-first candidate"
STATUS_PLANNED = "planned"


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _base_note_metadata(*, template_kind: str, activation_guard: str) -> dict[str, Any]:
    return {
        "template_kind": template_kind,
        "status": "inactive_candidate",
        "readiness": STATUS_PLANNED,
        "offerable": False,
        "work_intake_exposed": False,
        "pricing_active": False,
        "product_definition_active": False,
        "product_aggregate_runtime_consumed": False,
        "component_root_active": False,
        "quote_mode": "inactive_only",
        "no_executable_operations": True,
        "no_executable_bom": True,
        "activation_guard": activation_guard,
        "owner_go_required": True,
    }


def _dependency(
    key: str,
    *,
    source_component_id: str | None = None,
    source_path: str | None = None,
) -> dict[str, Any]:
    row = {"dependency_key": key}
    if source_component_id:
        row["source_component_id"] = source_component_id
    if source_path:
        row["source_path"] = source_path
    return row


def _component_contract_entry(
    *,
    component_id: str,
    template_code: str,
    role_key: str,
    role_label: str,
    component_kind: str,
    target_product_truth_path: str,
    required_inputs: list[str],
    outputs: list[str],
    dependencies: list[dict[str, Any]],
    blockers: list[str],
    activation_guard: str,
) -> dict[str, Any]:
    return {
        "component_id": component_id,
        "component_template_code": template_code,
        "role_key": role_key,
        "role_label": role_label,
        "component_kind": component_kind,
        "target_product_truth_path": target_product_truth_path,
        "required_inputs": required_inputs,
        "outputs": outputs,
        "dependencies": dependencies,
        "blockers": blockers,
        "readiness_state": STATUS_PLANNED,
        "activation_guard": activation_guard,
    }


def _composer_components() -> list[dict[str, Any]]:
    return [
        {
            "component_id": "comp_letter_face_v1",
            "component_template_code": FACE_TEMPLATE_CODE,
            "role": "face",
            "kind": "structural",
            "required": True,
            "readiness_state": STATUS_PLANNED,
            "target_product_truth_path": "components.face.instances[]",
            "allowed_component_variants": [FACE_TEMPLATE_CODE],
            "dependencies": [],
        },
        {
            "component_id": "comp_letter_back_v1",
            "component_template_code": BACK_TEMPLATE_CODE,
            "role": "back",
            "kind": "structural",
            "required": True,
            "readiness_state": STATUS_PLANNED,
            "target_product_truth_path": "components.back.instances[]",
            "allowed_component_variants": [BACK_TEMPLATE_CODE],
            "dependencies": ["comp_letter_face_v1"],
        },
        {
            "component_id": "comp_letter_return_cant_v1",
            "component_template_code": RETURN_CANT_TEMPLATE_CODE,
            "role": "return_cant",
            "kind": "structural",
            "required": True,
            "readiness_state": STATUS_PLANNED,
            "target_product_truth_path": "components.return_cant.instances[]",
            "allowed_component_variants": [RETURN_CANT_TEMPLATE_CODE],
            "dependencies": ["comp_letter_face_v1"],
        },
        {
            "component_id": "comp_letter_led_v1",
            "component_template_code": LED_TEMPLATE_CODE,
            "role": "lighting",
            "kind": "functional",
            "required": False,
            "readiness_state": STATUS_PLANNED,
            "target_product_truth_path": "components.led.instances[]",
            "allowed_component_variants": [LED_TEMPLATE_CODE],
            "dependencies": ["comp_letter_face_v1"],
        },
        {
            "component_id": "comp_letter_finish_v1",
            "component_template_code": FINISH_TEMPLATE_CODE,
            "role": "finish",
            "kind": "functional",
            "required": True,
            "readiness_state": STATUS_PLANNED,
            "target_product_truth_path": "components.finish.instances[]",
            "allowed_component_variants": [FINISH_TEMPLATE_CODE],
            "dependencies": [
                "comp_letter_face_v1",
                "comp_letter_back_v1",
                "comp_letter_return_cant_v1",
            ],
        },
        {
            "component_id": "comp_letter_mounting_v1",
            "component_template_code": MOUNTING_TEMPLATE_CODE,
            "role": "mounting",
            "kind": "functional",
            "required": False,
            "readiness_state": STATUS_PLANNED,
            "target_product_truth_path": "components.mounting.instances[]",
            "allowed_component_variants": [MOUNTING_TEMPLATE_CODE],
            "dependencies": ["comp_letter_back_v1", "product_root"],
        },
    ]


def _composer_notes() -> str:
    data = _base_note_metadata(
        template_kind="product_template",
        activation_guard="COMPONENT_FIRST_SET_INERT_UNTIL_OWNER_GO",
    )
    data.update(
        {
            "allowed_component_variants": {
                "face": [FACE_TEMPLATE_CODE],
                "back": [BACK_TEMPLATE_CODE],
                "return_cant": [RETURN_CANT_TEMPLATE_CODE],
                "lighting": [LED_TEMPLATE_CODE],
                "finish": [FINISH_TEMPLATE_CODE],
                "mounting": [MOUNTING_TEMPLATE_CODE],
            },
            "component_dependency_graph": [
                {"from": "comp_letter_face_v1", "to": "comp_letter_return_cant_v1"},
                {"from": "comp_letter_face_v1", "to": "comp_letter_back_v1"},
                {"from": "comp_letter_face_v1", "to": "comp_letter_led_v1"},
                {"from": "comp_letter_face_v1", "to": "comp_letter_finish_v1"},
                {"from": "comp_letter_back_v1", "to": "comp_letter_finish_v1"},
                {"from": "comp_letter_return_cant_v1", "to": "comp_letter_finish_v1"},
                {"from": "comp_letter_back_v1", "to": "comp_letter_mounting_v1"},
                {"from": "product_root", "to": "comp_letter_mounting_v1"},
            ],
            "blockers": [
                "OWNER_GO_REQUIRED",
                "COMPONENT_TRUTH_NOT_IMPLEMENTED",
                "WORK_INTAKE_NOT_ENABLED",
                "PRICING_NOT_ENABLED",
                "PRODUCT_DEFINITION_NOT_ENABLED",
            ],
            "read_model_hints": [
                "composer_only",
                "dependency_graph_metadata_only",
                "no_runtime_module_links",
            ],
        }
    )
    return _json_dumps(data)


def _component_notes(*, activation_guard: str) -> str:
    data = _base_note_metadata(
        template_kind="component_template",
        activation_guard=activation_guard,
    )
    data.update(
        {
            "component_truth_owner": True,
            "component_calculation_state": STATUS_PLANNED,
            "read_only_only": True,
        }
    )
    return _json_dumps(data)


def build_letters_component_first_payloads() -> list[dict[str, Any]]:
    composer_payload = {
        "template_code": COMPOSER_TEMPLATE_CODE,
        "family_id": FAMILY_ID,
        "family_name": FAMILY_NAME,
        "description": "Inactive component-first letters composer. Composition metadata only; no executable BOM.",
        "components_json": _json_dumps(_composer_components()),
        "operations_json": _json_dumps([]),
        "required_materials_json": _json_dumps([]),
        "estimated_hours": 0.0,
        "base_labor_rate": 0.0,
        "base_margin_pct": 0.0,
        "active": False,
        "notes": _composer_notes(),
    }

    component_payloads = [
        {
            "template_code": FACE_TEMPLATE_CODE,
            "family_id": FAMILY_ID,
            "family_name": FAMILY_NAME,
            "description": "Inactive component-first letters FACE contract. Metadata only; no executable BOM.",
            "components_json": _json_dumps([
                _component_contract_entry(
                    component_id="comp_letter_face_v1",
                    template_code=FACE_TEMPLATE_CODE,
                    role_key="face",
                    role_label="structural face",
                    component_kind="structural",
                    target_product_truth_path="components.face.instances[]",
                    required_inputs=[
                        "layer_group_ids",
                        "selected_layer_refs",
                        "face_material_code",
                        "face_thickness_mm",
                        "face_finish_target",
                    ],
                    outputs=[
                        "confirmed_area_m2",
                        "confirmed_perimeter_m",
                        "face_geometry_ref",
                        "face_cutting_operation_ref",
                    ],
                    dependencies=[],
                    blockers=[
                        "SOURCE_LAYERS_UNCONFIRMED",
                        "FACE_MATERIAL_MISSING",
                        "FACE_THICKNESS_MISSING",
                    ],
                    activation_guard="FACE_CONTRACT_ONLY_NOT_EXECUTABLE",
                )
            ]),
            "operations_json": _json_dumps([]),
            "required_materials_json": _json_dumps([]),
            "estimated_hours": 0.0,
            "base_labor_rate": 0.0,
            "base_margin_pct": 0.0,
            "active": False,
            "notes": _component_notes(activation_guard="FACE_CONTRACT_ONLY_NOT_EXECUTABLE"),
        },
        {
            "template_code": BACK_TEMPLATE_CODE,
            "family_id": FAMILY_ID,
            "family_name": FAMILY_NAME,
            "description": "Inactive component-first letters BACK contract. Metadata only; no executable BOM.",
            "components_json": _json_dumps([
                _component_contract_entry(
                    component_id="comp_letter_back_v1",
                    template_code=BACK_TEMPLATE_CODE,
                    role_key="back",
                    role_label="structural back",
                    component_kind="structural",
                    target_product_truth_path="components.back.instances[]",
                    required_inputs=[
                        "source_face_geometry_ref",
                        "back_material_code",
                        "back_thickness_mm",
                        "backing_mode",
                    ],
                    outputs=[
                        "back_geometry_ref",
                        "back_cut_operation_ref",
                        "back_material_consumption_ref",
                    ],
                    dependencies=[
                        _dependency("source_face_geometry", source_component_id="comp_letter_face_v1"),
                    ],
                    blockers=[
                        "FACE_GEOMETRY_REF_MISSING",
                        "BACK_MATERIAL_MISSING",
                        "BACKING_MODE_MISSING",
                    ],
                    activation_guard="BACK_CONTRACT_ONLY_NOT_EXECUTABLE",
                )
            ]),
            "operations_json": _json_dumps([]),
            "required_materials_json": _json_dumps([]),
            "estimated_hours": 0.0,
            "base_labor_rate": 0.0,
            "base_margin_pct": 0.0,
            "active": False,
            "notes": _component_notes(activation_guard="BACK_CONTRACT_ONLY_NOT_EXECUTABLE"),
        },
        {
            "template_code": RETURN_CANT_TEMPLATE_CODE,
            "family_id": FAMILY_ID,
            "family_name": FAMILY_NAME,
            "description": "Inactive component-first letters RETURN/CANT contract. Metadata only; no executable BOM.",
            "components_json": _json_dumps([
                _component_contract_entry(
                    component_id="comp_letter_return_cant_v1",
                    template_code=RETURN_CANT_TEMPLATE_CODE,
                    role_key="return_cant",
                    role_label="structural return/cant",
                    component_kind="structural",
                    target_product_truth_path="components.return_cant.instances[]",
                    required_inputs=[
                        "source_face_perimeter_ref",
                        "material_profile_code",
                        "depth_mm",
                        "finish_type",
                        "color_source",
                        "layer_group_ids",
                    ],
                    outputs=[
                        "confirmed_perimeter_m",
                        "return_profile_material_ref",
                        "modelare_cant_operation_ref",
                        "bonding_operation_ref",
                    ],
                    dependencies=[
                        _dependency(
                            "components.face.confirmed_perimeter",
                            source_component_id="comp_letter_face_v1",
                            source_path="components.face.confirmed_perimeter",
                        ),
                    ],
                    blockers=[
                        "SOURCE_FACE_PERIMETER_REF_MISSING",
                        "MATERIAL_PROFILE_MISSING",
                        "DEPTH_MM_MISSING",
                        "CONFIRMATION_STATE_MISSING",
                    ],
                    activation_guard="RETURN_CANT_CONTRACT_ONLY_NOT_EXECUTABLE",
                )
            ]),
            "operations_json": _json_dumps([]),
            "required_materials_json": _json_dumps([]),
            "estimated_hours": 0.0,
            "base_labor_rate": 0.0,
            "base_margin_pct": 0.0,
            "active": False,
            "notes": _component_notes(activation_guard="RETURN_CANT_CONTRACT_ONLY_NOT_EXECUTABLE"),
        },
        {
            "template_code": LED_TEMPLATE_CODE,
            "family_id": FAMILY_ID,
            "family_name": FAMILY_NAME,
            "description": "Inactive component-first letters LED contract. Metadata only; no executable BOM.",
            "components_json": _json_dumps([
                _component_contract_entry(
                    component_id="comp_letter_led_v1",
                    template_code=LED_TEMPLATE_CODE,
                    role_key="lighting",
                    role_label="functional lighting",
                    component_kind="functional",
                    target_product_truth_path="components.led.instances[]",
                    required_inputs=[
                        "lighting_mode",
                        "source_face_area_ref",
                        "led_density_config",
                        "led_module_type",
                        "psu_policy",
                    ],
                    outputs=[
                        "led_count",
                        "power_w",
                        "selected_psu_config",
                        "led_install_operation_ref",
                    ],
                    dependencies=[
                        _dependency(
                            "components.face.confirmed_area",
                            source_component_id="comp_letter_face_v1",
                            source_path="components.face.confirmed_area",
                        ),
                    ],
                    blockers=[
                        "LIGHTING_MODE_MISSING",
                        "SOURCE_FACE_AREA_REF_MISSING",
                        "LED_DENSITY_CONFIG_MISSING",
                    ],
                    activation_guard="LED_CONTRACT_ONLY_NOT_EXECUTABLE",
                )
            ]),
            "operations_json": _json_dumps([]),
            "required_materials_json": _json_dumps([]),
            "estimated_hours": 0.0,
            "base_labor_rate": 0.0,
            "base_margin_pct": 0.0,
            "active": False,
            "notes": _component_notes(activation_guard="LED_CONTRACT_ONLY_NOT_EXECUTABLE"),
        },
        {
            "template_code": FINISH_TEMPLATE_CODE,
            "family_id": FAMILY_ID,
            "family_name": FAMILY_NAME,
            "description": "Inactive component-first letters FINISH contract. Metadata only; no executable BOM.",
            "components_json": _json_dumps([
                _component_contract_entry(
                    component_id="comp_letter_finish_v1",
                    template_code=FINISH_TEMPLATE_CODE,
                    role_key="finish",
                    role_label="functional finish",
                    component_kind="functional",
                    target_product_truth_path="components.finish.instances[]",
                    required_inputs=[
                        "finish_target_component_ids",
                        "finish_type",
                        "color_code",
                        "print_required",
                        "lamination_required",
                    ],
                    outputs=[
                        "finish_operation_refs",
                        "finish_material_refs",
                        "finish_scope_summary",
                    ],
                    dependencies=[
                        _dependency("finish_target_components", source_component_id="comp_letter_face_v1"),
                        _dependency("finish_target_components", source_component_id="comp_letter_back_v1"),
                        _dependency("finish_target_components", source_component_id="comp_letter_return_cant_v1"),
                    ],
                    blockers=[
                        "FINISH_TARGET_MISSING",
                        "FINISH_TYPE_MISSING",
                        "COLOR_DECISION_MISSING",
                    ],
                    activation_guard="FINISH_CONTRACT_ONLY_NOT_EXECUTABLE",
                )
            ]),
            "operations_json": _json_dumps([]),
            "required_materials_json": _json_dumps([]),
            "estimated_hours": 0.0,
            "base_labor_rate": 0.0,
            "base_margin_pct": 0.0,
            "active": False,
            "notes": _component_notes(activation_guard="FINISH_CONTRACT_ONLY_NOT_EXECUTABLE"),
        },
        {
            "template_code": MOUNTING_TEMPLATE_CODE,
            "family_id": FAMILY_ID,
            "family_name": FAMILY_NAME,
            "description": "Inactive component-first letters MOUNTING contract. Metadata only; no executable BOM.",
            "components_json": _json_dumps([
                _component_contract_entry(
                    component_id="comp_letter_mounting_v1",
                    template_code=MOUNTING_TEMPLATE_CODE,
                    role_key="mounting",
                    role_label="functional mounting",
                    component_kind="functional",
                    target_product_truth_path="components.mounting.instances[]",
                    required_inputs=[
                        "mounting_mode",
                        "wall_type",
                        "mounting_height_mm",
                        "support_required",
                    ],
                    outputs=[
                        "mounting_operation_refs",
                        "support_material_refs",
                        "mounting_strategy_summary",
                    ],
                    dependencies=[
                        _dependency("back_install_anchor", source_component_id="comp_letter_back_v1"),
                        _dependency("product_install_context", source_path="product.install_context"),
                    ],
                    blockers=[
                        "MOUNTING_MODE_MISSING",
                        "SUPPORT_REQUIRED_UNKNOWN",
                        "INSTALL_CONTEXT_MISSING",
                    ],
                    activation_guard="MOUNTING_CONTRACT_ONLY_NOT_EXECUTABLE",
                )
            ]),
            "operations_json": _json_dumps([]),
            "required_materials_json": _json_dumps([]),
            "estimated_hours": 0.0,
            "base_labor_rate": 0.0,
            "base_margin_pct": 0.0,
            "active": False,
            "notes": _component_notes(activation_guard="MOUNTING_CONTRACT_ONLY_NOT_EXECUTABLE"),
        },
    ]

    return [composer_payload, *component_payloads]


async def seed_tpl_letters_component_first_v1() -> dict[str, Any]:
    await db_manager.init_db()

    payloads = build_letters_component_first_payloads()
    created_templates = 0
    updated_templates = 0

    async with db_manager.async_session_maker() as session:
        rows = (
            await session.execute(
                select(Product_templates).where(Product_templates.template_code.in_(ALL_TEMPLATE_CODES))
            )
        ).scalars().all()
        existing_by_code = {str(row.template_code): row for row in rows if row.template_code}

        for payload in payloads:
            template_code = str(payload["template_code"])
            row = existing_by_code.get(template_code)
            if row is None:
                session.add(Product_templates(**payload))
                created_templates += 1
                continue

            for key, value in payload.items():
                setattr(row, key, value)
            updated_templates += 1

        await session.commit()

    logger.info("Seeded inert component-first letters set: %s", COMPOSER_TEMPLATE_CODE)
    return {
        "template_code": COMPOSER_TEMPLATE_CODE,
        "created_templates": created_templates,
        "updated_templates": updated_templates,
        "created_links": 0,
        "updated_links": 0,
        "created_dossiers": 0,
        "updated_dossiers": 0,
        "template_codes": list(ALL_TEMPLATE_CODES),
        "inactive_only": True,
        "module_links_created": False,
        "registered_in_seed_sync_all": False,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(json.dumps(asyncio.run(seed_tpl_letters_component_first_v1()), indent=2, default=str))