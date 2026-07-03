"""Intake V4 production handoff preview — read-only, no ExecutionTask."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from schemas.intake_v4 import PILOT_V4_TEMPLATE_CODE
from services.intake_v4_production_handoff_preview_service import (
    build_intake_v4_production_handoff_preview,
)


def _complete_payload(*, confirmed: bool = True, template_code: str = PILOT_V4_TEMPLATE_CODE) -> dict:
    nesting = {
        "sheets": [
            {
                "configId": "sheet_1300x900",
                "sheetsUsed": 2,
                "usedSheetAreaSqm": 2.34,
                "placedItemsCount": 2,
                "unplacedItemsCount": 0,
                "placements": [
                    {
                        "partId": "letter-face-a",
                        "sourceLayerName": "litere-volumetrice-1",
                        "placedWidthMm": 800,
                        "placedHeightMm": 500,
                    },
                    {
                        "partId": "letter-back-a",
                        "sourceLayerName": "litere-backing",
                        "placedWidthMm": 400,
                        "placedHeightMm": 400,
                    },
                ],
            }
        ],
        "rolls": [
            {
                "rollWidthMm": 1000,
                "jobs": [
                    {
                        "usedRollAreaSqm": 8.0,
                        "placedItemsCount": 3,
                        "unplacedItemsCount": 0,
                    }
                ],
            }
        ],
    }
    return {
        "schema_version": "1.0.0",
        "product_binding": {"template_code": template_code},
        "svg_source": {"file_name": "test.svg", "file_size_bytes": 100, "file_hash": "a" * 64, "upload_status": "analyzed"},
        "svg_analysis_json": {
            "schemaVersion": "1.10.0",
            "nesting": nesting,
            "parts": {
                "items": [
                    {
                        "id": "letter-face-a",
                        "source": {"layerName": "litere-volumetrice-1"},
                    },
                    {
                        "id": "letter-back-a",
                        "derivedPartKind": "back-cover-plate",
                        "source": {"layerName": "litere-backing"},
                    },
                ]
            },
            "layers": [
                {
                    "id": "litere-volumetrice-1",
                    "name": "litere-volumetrice-1",
                    "perimeterMl": 10.0,
                    "filledAreaSqm": 1.5,
                }
            ],
        },
        "quote_geometry": {
            "letter_perimeter_m": 10.0,
            "face_area_m2": 1.5,
            "backing_area_m2": 1.2,
            "return_material_perimeter_ml": 10.0,
        },
        "path_geometry_summary": {
            "parse_status": "parsed",
            "face_area_m2": 1.5,
            "backing_area_m2": 1.2,
            "return_material_perimeter_ml": 10.0,
        },
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "litere-volumetrice-1",
                    "layer_name": "litere-volumetrice-1",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                },
                {
                    "layer_key": "litere-backing",
                    "layer_name": "litere-backing",
                    "confirmed_role": "backing",
                    "confirmation_state": "confirmed",
                },
            ],
        },
        "finish_setup": {
            "face_finish_type": "oracal_651",
            "return_finish_type": "oracal_wrapped",
            "return_depth_mm": 60,
            "illuminated": False,
            "letter_group_finishes": [
                {
                    "group_key": "litere-volumetrice-1",
                    "layer_name": "litere-volumetrice-1",
                    "face_finish_type": "oracal_651",
                    "face_area_m2": 1.5,
                }
            ],
            "confirmed": confirmed,
        },
    }


@pytest.mark.asyncio
async def test_preview_only_contract():
    from services.intake_v4_workspace_service import _parse_payload

    payload_raw = _complete_payload()
    payload = _parse_payload(payload_raw)
    with patch(
        "services.inventory_materials_admin_service.load_material_pricing_dict",
        new_callable=AsyncMock,
    ) as pricing:
        pricing.return_value = {
            "MAT-ORACAL-651": {"unit_cost": 5.0, "currency": "EUR", "source": "inventory_materials"},
            "MAT-ACP-FATA-LITERE": {"unit_cost": 10.0, "currency": "EUR", "source": "inventory_materials"},
            "MAT-SPATE-PVC-LITERE": {"unit_cost": 16.0, "currency": "EUR", "source": "inventory_materials"},
            "MAT-PROFIL-LATERAL-LITERE-60MM": {"unit_cost": 3.0, "currency": "EUR", "source": "inventory_materials"},
        }
        preview = await build_intake_v4_production_handoff_preview(
            None,  # type: ignore[arg-type]
            "ws-preview",
            payload_raw,
            payload,
        )
    assert preview.handoff_mode == "preview_only"
    assert preview.stock_consumption is False
    assert preview.creates_execution_tasks is False
    assert preview.creates_stock_reservations is False
    assert all(not job.creates_stock_reservation for job in preview.material_jobs)
    assert all(not seed.creates_execution_task for seed in preview.task_seed_preview)


@pytest.mark.asyncio
async def test_material_jobs_from_breakdown():
    from services.intake_v4_workspace_service import _parse_payload

    payload_raw = _complete_payload()
    payload = _parse_payload(payload_raw)
    with patch(
        "services.inventory_materials_admin_service.load_material_pricing_dict",
        new_callable=AsyncMock,
    ) as pricing:
        pricing.return_value = {}
        preview = await build_intake_v4_production_handoff_preview(
            None,  # type: ignore[arg-type]
            "ws-jobs",
            payload_raw,
            payload,
        )
    job_keys = {job.job_key for job in preview.material_jobs}
    assert "face_plexiglas_cutting" in job_keys
    assert "forex_backing_cutting" in job_keys
    assert "oracal_vinyl_cutting" in job_keys
    assert "return_profile_material" in job_keys


@pytest.mark.asyncio
async def test_operation_groups_include_cnc_cant_led_when_data_exists():
    from services.intake_v4_workspace_service import _parse_payload

    payload_raw = _complete_payload()
    payload = _parse_payload(payload_raw)
    payload_raw["finish_setup"]["illuminated"] = True
    payload_raw["finish_setup"]["psu_configuration"] = [100]
    payload_raw["finish_setup"]["estimated_led_watts"] = 50
    payload = _parse_payload(payload_raw)
    with patch(
        "services.inventory_materials_admin_service.load_material_pricing_dict",
        new_callable=AsyncMock,
    ) as pricing:
        pricing.return_value = {
            "MAT-LED-MODULE": {"unit_cost": 0.5, "currency": "EUR", "source": "inventory_materials"},
            "MAT-LED-PSU-12V-100W": {"unit_cost": 16.0, "currency": "EUR", "source": "inventory_materials"},
        }
        preview = await build_intake_v4_production_handoff_preview(
            None,  # type: ignore[arg-type]
            "ws-groups",
            payload_raw,
            payload,
        )
    group_keys = {group.group_key for group in preview.operation_groups if group.active}
    assert "cnc_cutting" in group_keys
    assert "return_forming" in group_keys
    assert "led_electrical" in group_keys


@pytest.mark.asyncio
async def test_blockers_for_missing_layer_roles():
    from services.intake_v4_workspace_service import _parse_payload

    payload_raw = _complete_payload()
    payload_raw["layer_role_setup"]["confirmation_status"] = "partial"
    payload = _parse_payload(payload_raw)
    preview = await build_intake_v4_production_handoff_preview(
        None,  # type: ignore[arg-type]
        "ws-block",
        payload_raw,
        payload,
    )
    assert any(item.code == "layer_roles_incomplete" for item in preview.blockers)


@pytest.mark.asyncio
async def test_unsupported_template_blocker():
    from services.intake_v4_workspace_service import _parse_payload

    payload_raw = _complete_payload(template_code="TPL-ACM-CASSETTED-PANEL")
    payload = _parse_payload(payload_raw)
    preview = await build_intake_v4_production_handoff_preview(
        None,  # type: ignore[arg-type]
        "ws-tpl",
        payload_raw,
        payload,
    )
    assert any(item.code == "unsupported_template" for item in preview.blockers)


@pytest.mark.asyncio
async def test_finish_not_confirmed_blocker():
    from services.intake_v4_workspace_service import _parse_payload

    payload_raw = _complete_payload(confirmed=False)
    payload = _parse_payload(payload_raw)
    preview = await build_intake_v4_production_handoff_preview(
        None,  # type: ignore[arg-type]
        "ws-finish",
        payload_raw,
        payload,
    )
    assert any(item.code == "finish_setup_not_confirmed" for item in preview.blockers)
