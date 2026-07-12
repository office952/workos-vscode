"""Shared fixtures/helpers for EIC workspace-linked logo tests (no pytest plugins)."""

from __future__ import annotations

import json
import uuid

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from seeds.seed_tpl_volumetric_logo_v1 import seed_tpl_volumetric_logo_v1
from services.intake_v6_layer_binding_persistence_service import (
    persist_logo_layer_bindings_from_composition_confirmation,
)
from services.intake_v6_product_composition_recommendation_service import apply_product_composition_recommendation
from tests.test_aggregate_cost_bom_adapter import INVENTORY_CATALOG, SAMPLE_RATES

ROOT = "TPL-VOLUMETRIC-LETTERS_v2"

LOGO_MATERIAL_RATES = {
    **SAMPLE_RATES,
    "print_media": 5.0,
    "laminate_media": 4.0,
    "logo_face_material": 12.0,
    "logo_return_profile": 3.0,
    "logo_back_material": 8.0,
}

LOGO_INVENTORY = {
    **INVENTORY_CATALOG,
    **{code: {"status": "active", "unit_cost": rate} for code, rate in LOGO_MATERIAL_RATES.items()},
}


def _layer(key: str, name: str, role: str) -> dict:
    return {
        "layer_key": key,
        "layer_id": key,
        "layer_name": name,
        "auto_role": role,
        "confirmed_role": role,
        "confirmation_state": "confirmed",
        "auto_confidence": "high",
    }


def gradi_payload(*, finish_confirmed: bool = True) -> dict:
    payload = {
        "analysis_ready": True,
        "product_binding": {"template_code": ROOT},
        "svg_source": {"file_name": "gradi-curat.svg", "file_size_bytes": 27173, "upload_status": "analyzed"},
        "quote_geometry": {"letter_count": 19, "letter_perimeter_m": 31.638, "letter_face_area_m2": 3.05},
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                _layer("letters", "Litere GRADI", "face"),
                _layer("logo-stanga", "logo stanga", "printed_artwork"),
                _layer("logo-dreapta", "logo dreapta", "printed_artwork"),
            ],
            "layer_bindings": [],
            "warnings": [],
        },
        "finish_setup": {
            "confirmed": True,
            "face_finish_type": "oracal_651",
            "return_depth_mm": 60,
            "return_finish_type": "white_aluminum",
            "artwork_finishes": [
                {
                    "layer_key": "logo-stanga",
                    "layer_name": "logo stanga",
                    "execution_type": "print_laminate",
                    "color_mode": "polychrome",
                    "return_depth_mm": 60,
                    "estimated_area_m2": 0.42,
                    "confirmed": finish_confirmed,
                },
                {
                    "layer_key": "logo-dreapta",
                    "layer_name": "logo dreapta",
                    "execution_type": "print_laminate",
                    "color_mode": "polychrome",
                    "return_depth_mm": 60,
                    "estimated_area_m2": 0.38,
                    "confirmed": finish_confirmed,
                },
            ],
        },
    }
    apply_product_composition_recommendation(payload)
    return payload


def confirmed_bindings_payload() -> dict:
    payload = gradi_payload()
    items = payload["product_composition_recommendation"]["composition_items"]
    persist_logo_layer_bindings_from_composition_confirmation(payload, confirmed=True, confirmed_items=items)
    payload["product_composition_confirmed"] = {"confirmed": True, "items": items}
    return payload


def letters_only_payload() -> dict:
    payload = {
        "analysis_ready": True,
        "product_binding": {"template_code": ROOT},
        "svg_source": {"file_name": "letters.svg", "file_size_bytes": 1000, "upload_status": "analyzed"},
        "quote_geometry": {"letter_count": 5, "letter_perimeter_m": 2.0, "letter_face_area_m2": 0.5},
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [_layer("letters", "Litere", "face")],
            "layer_bindings": [],
            "warnings": [],
        },
        "finish_setup": {
            "confirmed": True,
            "face_finish_type": "oracal_651",
            "return_depth_mm": 60,
            "return_finish_type": "white_aluminum",
            "artwork_finishes": [],
        },
    }
    apply_product_composition_recommendation(payload)
    return payload


def quote_input_overlay(payload: dict) -> dict:
    return {
        "analysis_ready": payload.get("analysis_ready"),
        "quote_geometry": dict(payload.get("quote_geometry") or {}),
        "finish_setup": dict(payload.get("finish_setup") or {}),
    }


async def seed_logo_template(session) -> None:
    await seed_tpl_volumetric_logo_v1()


async def seed_logo_inventory_materials(session) -> None:
    from sqlalchemy import select

    from models.inventory_materials import Inventory_materials

    for code, rate in LOGO_MATERIAL_RATES.items():
        existing = (
            await session.execute(select(Inventory_materials).where(Inventory_materials.code == code))
        ).scalar_one_or_none()
        if existing is not None:
            continue
        session.add(
            Inventory_materials(
                code=code,
                name=code,
                unit="buc",
                unit_cost=rate,
                status="active",
                currency="RON",
            )
        )
    await session.commit()


async def add_workspace(session, payload: dict) -> str:
    workspace_id = str(uuid.uuid4())
    session.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"WS-EIC-{workspace_id[:8]}",
            title="EIC workspace linked logo",
            template_code=ROOT,
            status="draft",
            payload_json=json.dumps(payload),
        )
    )
    await session.commit()
    return workspace_id
