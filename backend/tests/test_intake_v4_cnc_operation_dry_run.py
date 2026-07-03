"""Intake V4 CNC dry-run aligned with material breakdown operation_rows."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from services.intake_v4_cnc_operation_dry_run_service import CNC_TASK_DRY_RUN_SOURCE
from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown
from services.intake_v4_production_task_dry_run_service import build_v4_production_task_dry_run
from services.intake_v4_task_generation_dry_run_service import build_intake_v4_task_generation_dry_run
from services.intake_v4_workspace_service import _parse_payload

FACE_ML = 13.62
SHEET_FACE_M2 = 0.5834

_DEFAULT_PRICING = {
    "MAT-ORACAL-651": {"unit_cost": 5.0, "currency": "EUR", "source": "inventory_materials"},
    "MAT-ACP-FATA-LITERE": {"unit_cost": 10.0, "currency": "EUR", "source": "inventory_materials"},
    "MAT-SPATE-PVC-LITERE": {"unit_cost": 16.0, "currency": "EUR", "source": "inventory_materials"},
}


def _payload(backing_mode: str, **finish_extra: object) -> dict:
    finish = {
        "face_finish_type": "oracal_651",
        "return_finish_type": "oracal_wrapped",
        "return_depth_mm": 60,
        "illuminated": True,
        "led_module_power_w": 1.44,
        "backing_mode": backing_mode,
        **finish_extra,
    }
    return {
        "schema_version": "1.0.0",
        "product_binding": {"template_code": "TPL-VOLUMETRIC-LETTERS"},
        "svg_analysis_json": {
            "schemaVersion": "1.10.0",
            "nesting": {
                "sheets": [
                    {
                        "configId": "sheet_3000x2000",
                        "sheetsUsed": 1,
                        "usedSheetAreaSqm": SHEET_FACE_M2,
                        "placedItemsCount": 10,
                        "unplacedItemsCount": 0,
                        "efficiencyPercent": 70.0,
                    }
                ],
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
            "letter_perimeter_m": 11.63,
            "face_area_m2": 1.5,
            "face_cutting_perimeter_ml": FACE_ML,
            "artwork_area_m2": 0.45,
        },
        "path_geometry_summary": {
            "parse_status": "parsed",
            "face_area_m2": 1.5,
            "face_cutting_perimeter_ml": FACE_ML,
            "cnc_cutting_perimeter_ml": FACE_ML,
            "led_perimeter_ml": 11.63,
            "artwork_area_m2": 0.45,
        },
        "finish_setup": finish,
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "litere-volumetrice-1",
                    "layer_name": "litere-volumetrice-1",
                    "auto_role": "face",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                }
            ],
        },
    }


@pytest.fixture
def seeded_db(db_fixture):
    from seeds.seed_build4_templates import seed_build4_templates

    asyncio.run(seed_build4_templates())
    return db_fixture


async def _run_task_dry_run(seeded_db, backing_mode: str):
    payload_dict = _payload(backing_mode)
    payload = _parse_payload(payload_dict)

    async def _override_get_db():
        async with seeded_db.session_maker() as session:
            yield session

    with patch(
        "services.inventory_materials_admin_service.load_material_pricing_dict",
        new_callable=AsyncMock,
    ) as mock_pricing:
        mock_pricing.return_value = _DEFAULT_PRICING
        async with seeded_db.session_maker() as session:
            return await build_intake_v4_task_generation_dry_run(
                session,
                "ws-cnc-dry-run",
                payload_dict,
                payload,
            )


def _cnc_candidates_by_key(dry_run):
    return {c.operation_key: c for c in dry_run.cnc_operation_candidates}


@pytest.mark.asyncio
async def test_backing_none_face_cut_and_bevel_from_operation_rows(seeded_db):
    dry_run = await _run_task_dry_run(seeded_db, "none")
    by_key = _cnc_candidates_by_key(dry_run)

    assert dry_run.cnc_task_source == CNC_TASK_DRY_RUN_SOURCE
    assert dry_run.legacy_cnc_mapping_used is False
    assert "cnc_face_cutting_plexiglas_3mm" in by_key
    assert "cnc_face_bevel_plexiglas_3mm" in by_key
    assert "cnc_backing_cutting_forex_10mm" not in by_key

    cut = by_key["cnc_face_cutting_plexiglas_3mm"]
    bevel = by_key["cnc_face_bevel_plexiglas_3mm"]
    assert cut.quantity == pytest.approx(FACE_ML, rel=1e-3)
    assert bevel.quantity == pytest.approx(FACE_ML, rel=1e-3)
    assert cut.source == CNC_TASK_DRY_RUN_SOURCE
    assert cut.required_machine_key == "MCH-CNC-4020"
    assert cut.workstation_key == "cnc_router"
    assert cut.required_skill_key == "cnc_operator"


@pytest.mark.asyncio
async def test_backing_none_quantities_match_material_breakdown(seeded_db):
    payload_dict = _payload("none")
    breakdown = build_intake_v4_material_breakdown("ws", payload_dict)
    dry_run = await _run_task_dry_run(seeded_db, "none")

    breakdown_qty = {
        row.key: row.quantity for row in breakdown.operation_rows
    }
    for candidate in dry_run.cnc_operation_candidates:
        assert candidate.quantity == pytest.approx(breakdown_qty[candidate.operation_key], rel=1e-3)


@pytest.mark.asyncio
async def test_forex_no_bevel_backing_cut_five_passes(seeded_db):
    dry_run = await _run_task_dry_run(seeded_db, "forex_10_no_bevel")
    by_key = _cnc_candidates_by_key(dry_run)

    back = by_key["cnc_backing_cutting_forex_10mm"]
    assert back.passes == 5
    assert back.owner_pass_override is True
    assert back.operation_equivalent_quantity == pytest.approx(FACE_ML * 5, rel=1e-3)
    assert "cnc_backing_bevel_forex_10mm" not in by_key


@pytest.mark.asyncio
async def test_forex_with_bevel_adds_backing_bevel(seeded_db):
    dry_run = await _run_task_dry_run(seeded_db, "forex_10_with_bevel")
    by_key = _cnc_candidates_by_key(dry_run)
    assert "cnc_backing_bevel_forex_10mm" in by_key


@pytest.mark.asyncio
async def test_all_cnc_candidates_source_operation_rows(seeded_db):
    dry_run = await _run_task_dry_run(seeded_db, "forex_10_with_bevel")
    assert all(c.source == CNC_TASK_DRY_RUN_SOURCE for c in dry_run.cnc_operation_candidates)
    assert all(c.consumes_stock_now is False for c in dry_run.cnc_operation_candidates)
    assert all(c.creates_task_now is False for c in dry_run.cnc_operation_candidates)


@pytest.mark.asyncio
async def test_missing_rate_stays_missing_not_zero(seeded_db):
    dry_run = await _run_task_dry_run(seeded_db, "none")
    for candidate in dry_run.cnc_operation_candidates:
        assert candidate.pricing_status == "missing_rate"
        assert candidate.estimated_cost is None


@pytest.mark.asyncio
async def test_dry_run_boundary_flags_no_execution_or_stock(seeded_db):
    dry_run = await _run_task_dry_run(seeded_db, "none")
    assert dry_run.creates_execution_tasks is False
    assert dry_run.writes_to_production is False
    assert dry_run.stock_consumption is False
    assert dry_run.dry_run_only is True
    assert all(not t.creates_execution_task for t in dry_run.task_candidates)


@pytest.mark.asyncio
async def test_legacy_not_used_when_operation_rows_exist(seeded_db):
    dry_run = await _run_task_dry_run(seeded_db, "none")
    assert dry_run.legacy_cnc_mapping_used is False
    legacy_warnings = [
        w for w in dry_run.warnings if w.code == "cnc_dry_run_legacy_parallel_mapping"
    ]
    assert legacy_warnings == []


def test_production_preview_cnc_from_operation_rows():
    payload = _parse_payload(_payload("forex_10_no_bevel"))
    preview = build_v4_production_task_dry_run(workspace_id="ws-preview", payload=payload)

    cnc_tasks = [t for t in preview.candidate_tasks if t.group_key == "cnc_operation_rows"]
    assert len(cnc_tasks) >= 3
    keys = {t.seed_code for t in cnc_tasks}
    assert "cnc_face_cutting" in keys
    assert "cnc_face_bevel" in keys
    assert "cnc_backing_cutting" in keys
    assert "face_and_backing_cnc_cut" not in {t.seed_code for t in preview.candidate_tasks}

    back = next(t for t in cnc_tasks if t.seed_code == "cnc_backing_cutting")
    pass_input = next(i for i in back.inputs_preview if i.label == "Treceri")
    assert pass_input.value == 5
    equiv = next(i for i in back.inputs_preview if i.label == "Echivalent utilaj")
    assert equiv.value == pytest.approx(FACE_ML * 5, rel=1e-2)
