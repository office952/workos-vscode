"""Seed TPL-VOLUMETRIC-FACE-BACK-PREP into ProductSystem (product_templates).

Idempotent on template_code. Template is inserted inactive (draft_internal);
active_template_scope keeps only TPL-VOLUMETRIC-LETTERS commercial-active.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List

from sqlalchemy import select

from core.database import db_manager
import models  # noqa: F401
from models.product_templates import Product_templates
from seeds.seed_build4_templates import (
    _comp,
    _flatten_materials,
    _flatten_operations,
    _mat_formula,
    _op_static,
)
from services.tpl_volumetric_face_back_prep_productsystem_contract import (
    CNC_RATE_EUR_PER_ML,
    MATERIAL_REGISTRY_BY_LOGICAL_KEY,
    PRODUCTSYSTEM_COMPONENTS,
    PRODUCTSYSTEM_OPERATIONS,
    SHARED_CNC_OPERATION_KEY_BY_TASK,
    TEMPLATE_METADATA,
    productsystem_template_notes,
)

logger = logging.getLogger(__name__)


def _op_draft_fixed_ml(
    *,
    task_key: str,
    label: str,
    seq: int,
    required: bool = True,
    appears_when: str | None = None,
) -> Dict[str, Any]:
    shared_key = SHARED_CNC_OPERATION_KEY_BY_TASK.get(task_key)
    row: Dict[str, Any] = {
        "code": task_key,
        "workcenter": "CNC_ROUTER",
        "sequence": seq,
        "estimatedMinutes": 0,
        "estimated_minutes": 0,
        "calculation_type": "draft_fixed_ml",
        "unit": "ml",
        "unit_price_eur": CNC_RATE_EUR_PER_ML,
        "price_source": "fixed_rule",
        "quote_priced": False,
        "internal_draft_only": True,
        "creates_real_task": False,
        "required": required,
        "label": label,
        "productsystem_operation_key": task_key,
    }
    if shared_key:
        row["shared_cnc_operation_key"] = shared_key
    if appears_when:
        row["appears_when"] = appears_when
    return row


def _op_draft_station(
    *,
    task_key: str,
    label: str,
    seq: int,
    workcenter: str,
    station: str,
) -> Dict[str, Any]:
    return {
        "code": task_key,
        "workcenter": workcenter,
        "sequence": seq,
        "estimatedMinutes": 0,
        "estimated_minutes": 0,
        "calculation_type": "draft_internal",
        "quote_priced": False,
        "internal_draft_only": True,
        "creates_real_task": False,
        "required": True,
        "label": label,
        "station": station,
        "productsystem_operation_key": task_key,
    }


def volumetric_face_back_prep_components() -> List[Dict[str, Any]]:
    """ProductSystem components_json payload for partial face/back prep."""
    face = PRODUCTSYSTEM_COMPONENTS["FACE_PLEXI"]
    back = PRODUCTSYSTEM_COMPONENTS["BACK_FOREX"]
    return [
        _comp(
            "FACE_PLEXI",
            face["component_type"],
            face["label"],
            operations=[
                _op_draft_station(
                    task_key="PREPARE_CNC_FILES",
                    label="Pregătire fișiere CNC",
                    seq=1,
                    workcenter="PREPRESS",
                    station="prepress",
                ),
                _op_draft_fixed_ml(
                    task_key="CUT_FACE_PLEXI",
                    label="Debitare CNC față plexiglas 3 mm",
                    seq=2,
                    required=True,
                ),
                _op_draft_fixed_ml(
                    task_key="SHANFREN_FACE_PLEXI",
                    label="Șanfren/canal CNC față plexiglas",
                    seq=3,
                    required=True,
                ),
            ],
            materials=[
                _mat_formula(
                    MATERIAL_REGISTRY_BY_LOGICAL_KEY["plexiglas_3mm"],
                    "mp",
                    "letter_face_area",
                    {"waste_pct": 0.15},
                    "plexiglas 3mm PMMA - opal (MAT-ACP-FATA-LITERE)",
                    requires_quote_input=["letter_face_area_m2"],
                ),
            ],
        ),
        _comp(
            "BACK_FOREX",
            back["component_type"],
            back["label"],
            operations=[
                _op_draft_fixed_ml(
                    task_key="CUT_BACK_FOREX",
                    label="Debitare CNC spate Forex 10 mm",
                    seq=4,
                    required=True,
                ),
                _op_draft_fixed_ml(
                    task_key="SHANFREN_BACK_FOREX",
                    label="Șanfren/canal CNC spate Forex",
                    seq=5,
                    required=False,
                    appears_when="shanfren_forex=true",
                ),
                _op_draft_station(
                    task_key="CLEAN_AND_CHECK_PARTS",
                    label="Curățare și verificare piese",
                    seq=6,
                    workcenter="FINISHING",
                    station="finishing",
                ),
                _op_static(
                    "PACKAGE_FACE_BACK_PARTS",
                    "PACKAGING",
                    7,
                    0,
                    "Ambalare piese față + spate",
                    internal_only=True,
                    quote_priced=False,
                ),
            ],
            materials=[
                _mat_formula(
                    MATERIAL_REGISTRY_BY_LOGICAL_KEY["forex_10mm"],
                    "mp",
                    "letter_face_area",
                    {"waste_pct": 0.10, "notes": "Forex 10 mm spate; fallback arie față în draft"},
                    "Forex 10 mm — spate litere (MAT-SPATE-PVC-LITERE alias)",
                    requires_quote_input=["letter_face_area_m2"],
                ),
            ],
        ),
    ]


async def seed_tpl_volumetric_face_back_prep_template() -> Dict[str, Any]:
    """Insert or skip TPL-VOLUMETRIC-FACE-BACK-PREP in product_templates."""
    code = TEMPLATE_METADATA["key"]
    inserted = False
    skipped = False

    async with db_manager.async_session_maker() as session:
        existing = await session.execute(
            select(Product_templates).where(Product_templates.template_code == code)
        )
        if existing.scalar_one_or_none():
            skipped = True
            logger.info("Template %s already exists, skipping.", code)
            return {"template_code": code, "inserted": inserted, "skipped": skipped}

        components = volumetric_face_back_prep_components()
        ops = _flatten_operations(components)
        mats = _flatten_materials(components)

        session.add(
            Product_templates(
                template_code=code,
                family_id=TEMPLATE_METADATA["family_id"],
                family_name=TEMPLATE_METADATA["family_name"],
                description=TEMPLATE_METADATA["description"],
                components_json=json.dumps(components, ensure_ascii=False),
                operations_json=json.dumps(ops, ensure_ascii=False),
                required_materials_json=json.dumps(mats, ensure_ascii=False),
                estimated_hours=4.0,
                base_labor_rate=80.0,
                base_margin_pct=0.0,
                active=False,
                notes=productsystem_template_notes(),
            )
        )
        await session.commit()
        inserted = True
        logger.info("Inserted ProductSystem template: %s (active=false)", code)

    return {
        "template_code": code,
        "inserted": inserted,
        "skipped": skipped,
        "operation_catalog_count": len(PRODUCTSYSTEM_OPERATIONS),
        "component_count": len(PRODUCTSYSTEM_COMPONENTS),
    }


async def _main() -> None:
    await db_manager.init_db()
    stats = await seed_tpl_volumetric_face_back_prep_template()
    print(f"[seed_tpl_volumetric_face_back_prep_template] {stats}")


if __name__ == "__main__":
    asyncio.run(_main())
