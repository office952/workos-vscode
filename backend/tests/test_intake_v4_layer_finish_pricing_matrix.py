"""E2E matrix — Intake V4 per-layer Oracal finish → material breakdown pricing."""

from __future__ import annotations

from copy import deepcopy
from unittest.mock import AsyncMock, patch

import pytest

from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown
from services.intake_v4_oracal_face_pricing_service import (
    INTAKE_V4_ORACAL_641_EUR_PER_M2,
    INTAKE_V4_ORACAL_651_EUR_PER_M2,
    INTAKE_V4_ORACAL_8500_EUR_PER_M2,
    face_oracal_vinyl_areas_by_series,
)


def _roll_job(layer_name: str, area_sqm: float, color: str = "c1") -> dict:
    return {
        "sourceLayerName": layer_name,
        "colorKey": color,
        "consumedLengthMm": area_sqm * 1000,
        "usedRollAreaSqm": area_sqm,
        "placedItemsCount": 1,
        "unplacedItemsCount": 0,
        "efficiencyPercent": 80.0,
    }


def _layer_finish_payload(
    *,
    groups: list[dict],
    roll_jobs: list[dict] | None = None,
    global_face: str = "oracal_651",
) -> dict:
    nesting: dict = {}
    if roll_jobs:
        nesting["rolls"] = [
            {
                "configId": "vinyl_roll_1000",
                "rollWidthMm": 1000,
                "jobs": roll_jobs,
            }
        ]
    layers = [
        {
            "id": g["group_key"],
            "name": g["layer_name"],
            "perimeterMl": g.get("perimeter_m", 5.0),
            "filledAreaSqm": g.get("face_area_m2", 1.0),
        }
        for g in groups
    ]
    face_total = sum(float(g.get("face_area_m2") or 0) for g in groups)
    return {
        "schema_version": "1.0.0",
        "product_binding": {"template_code": "TPL-VOLUMETRIC-LETTERS"},
        "svg_analysis_json": {
            "schemaVersion": "1.10.0",
            "nesting": nesting,
            "layers": layers,
        },
        "quote_geometry": {
            "letter_perimeter_m": 10.0,
            "face_area_m2": face_total,
            "backing_area_m2": face_total,
            "return_material_perimeter_ml": 10.0,
        },
        "path_geometry_summary": {
            "parse_status": "parsed",
            "face_area_m2": face_total,
            "backing_area_m2": face_total,
            "return_material_perimeter_ml": 10.0,
        },
        "finish_setup": {
            "face_finish_type": global_face,
            "return_finish_type": "white_aluminum",
            "return_depth_mm": 60,
            "illuminated": False,
            "letter_group_finishes": groups,
            "confirmed": True,
        },
    }


def _vinyl_row(result, series: str):
    return next(row for row in result.material_rows if row.material_key == f"face_vinyl_{series}")


class TestIntakeV4LayerFinishPricingMatrix:
    def test_a0_no_oracal_face_rows_when_all_none(self):
        payload = _layer_finish_payload(
            groups=[
                {
                    "group_key": "layer-a",
                    "layer_name": "layer-a",
                    "face_finish_type": "none",
                    "face_area_m2": 1.0,
                    "return_finish_type": "white_aluminum",
                }
            ],
            roll_jobs=[_roll_job("layer-a", 1.0)],
        )
        result = build_intake_v4_material_breakdown("ws-a0", payload)
        assert not any(row.material_key.startswith("face_vinyl_") for row in result.material_rows)

    def test_a1_single_layer_oracal_641_geometry_path(self):
        payload = _layer_finish_payload(
            groups=[
                {
                    "group_key": "layer-a",
                    "layer_name": "layer-a",
                    "face_finish_type": "oracal_641",
                    "face_area_m2": 0.5,
                    "return_finish_type": "white_aluminum",
                }
            ],
            roll_jobs=None,
        )
        row = _vinyl_row(build_intake_v4_material_breakdown("ws-a1", payload), "641")
        assert row.quantity == 0.5
        assert row.unit_price == INTAKE_V4_ORACAL_641_EUR_PER_M2
        assert row.priced_quantity == 0.6
        assert row.estimated_cost == round(0.6 * INTAKE_V4_ORACAL_641_EUR_PER_M2, 4)

    def test_a2_single_layer_oracal_651_roll_nesting(self):
        payload = _layer_finish_payload(
            groups=[
                {
                    "group_key": "layer-a",
                    "layer_name": "layer-a",
                    "face_finish_type": "oracal_651",
                    "face_area_m2": 0.4,
                    "return_finish_type": "white_aluminum",
                }
            ],
            roll_jobs=[_roll_job("layer-a", 0.6)],
        )
        row = _vinyl_row(build_intake_v4_material_breakdown("ws-a2", payload), "651")
        assert row.quantity == 0.6
        assert row.unit_price == INTAKE_V4_ORACAL_651_EUR_PER_M2
        assert row.estimated_cost == round(0.6 * INTAKE_V4_ORACAL_651_EUR_PER_M2, 4)

    def test_a3_single_layer_oracal_8500_roll_nesting(self):
        payload = _layer_finish_payload(
            groups=[
                {
                    "group_key": "layer-a",
                    "layer_name": "layer-a",
                    "face_finish_type": "oracal_8500",
                    "face_area_m2": 0.33,
                    "return_finish_type": "white_aluminum",
                }
            ],
            roll_jobs=[_roll_job("layer-a", 0.5), _roll_job("layer-b", 0.3)],
        )
        row = _vinyl_row(build_intake_v4_material_breakdown("ws-a3", payload), "8500")
        assert row.quantity == 0.5
        assert row.unit_price == INTAKE_V4_ORACAL_8500_EUR_PER_M2

    def test_b3_two_layers_oracal_8500_sums_roll_area_not_total_roll(self):
        payload = _layer_finish_payload(
            groups=[
                {
                    "group_key": "layer-a",
                    "layer_name": "layer-a",
                    "face_finish_type": "oracal_8500",
                    "face_area_m2": 0.33,
                    "return_finish_type": "white_aluminum",
                },
                {
                    "group_key": "layer-b",
                    "layer_name": "layer-b",
                    "face_finish_type": "oracal_8500",
                    "face_area_m2": 0.36,
                    "return_finish_type": "white_aluminum",
                },
            ],
            roll_jobs=[_roll_job("layer-a", 0.5), _roll_job("layer-b", 0.4), _roll_job("layer-c", 0.3)],
        )
        one_layer = deepcopy(payload)
        one_layer["finish_setup"]["letter_group_finishes"] = [payload["finish_setup"]["letter_group_finishes"][0]]
        row_one = _vinyl_row(build_intake_v4_material_breakdown("ws-b3-one", one_layer), "8500")
        row_two = _vinyl_row(build_intake_v4_material_breakdown("ws-b3-two", payload), "8500")
        assert row_one.quantity == 0.5
        assert row_two.quantity == round(0.5 + 0.4, 4)
        assert row_two.quantity > row_one.quantity
        assert row_two.estimated_cost > row_one.estimated_cost

    def test_c1_mixed_641_and_8500_separate_rows(self):
        payload = _layer_finish_payload(
            groups=[
                {
                    "group_key": "layer-a",
                    "layer_name": "layer-a",
                    "face_finish_type": "oracal_641",
                    "face_area_m2": 0.4,
                    "return_finish_type": "white_aluminum",
                },
                {
                    "group_key": "layer-b",
                    "layer_name": "layer-b",
                    "face_finish_type": "oracal_8500",
                    "face_area_m2": 0.6,
                    "return_finish_type": "white_aluminum",
                },
            ],
            roll_jobs=[_roll_job("layer-a", 0.45), _roll_job("layer-b", 0.7)],
        )
        result = build_intake_v4_material_breakdown("ws-c1", payload)
        row_641 = _vinyl_row(result, "641")
        row_8500 = _vinyl_row(result, "8500")
        assert row_641.quantity == 0.45
        assert row_8500.quantity == 0.7
        assert row_641.estimated_cost == round(0.45 * INTAKE_V4_ORACAL_641_EUR_PER_M2, 4)
        assert row_8500.estimated_cost == round(0.7 * INTAKE_V4_ORACAL_8500_EUR_PER_M2, 4)

    def test_d1_removing_second_8500_layer_decreases_cost(self):
        payload = _layer_finish_payload(
            groups=[
                {
                    "group_key": "layer-a",
                    "layer_name": "layer-a",
                    "face_finish_type": "oracal_8500",
                    "face_area_m2": 0.33,
                    "return_finish_type": "white_aluminum",
                },
                {
                    "group_key": "layer-b",
                    "layer_name": "layer-b",
                    "face_finish_type": "oracal_8500",
                    "face_area_m2": 0.36,
                    "return_finish_type": "white_aluminum",
                },
            ],
            roll_jobs=[_roll_job("layer-a", 0.5), _roll_job("layer-b", 0.4)],
        )
        two = build_intake_v4_material_breakdown("ws-d1-two", payload)
        one_payload = deepcopy(payload)
        one_payload["finish_setup"]["letter_group_finishes"] = [payload["finish_setup"]["letter_group_finishes"][0]]
        one = build_intake_v4_material_breakdown("ws-d1-one", one_payload)
        cost_two = _vinyl_row(two, "8500").estimated_cost
        cost_one = _vinyl_row(one, "8500").estimated_cost
        assert cost_two is not None and cost_one is not None
        assert cost_two > cost_one

    def test_d2_change_second_layer_8500_to_651_moves_quantity(self):
        payload = _layer_finish_payload(
            groups=[
                {
                    "group_key": "layer-a",
                    "layer_name": "layer-a",
                    "face_finish_type": "oracal_8500",
                    "face_area_m2": 0.33,
                    "return_finish_type": "white_aluminum",
                },
                {
                    "group_key": "layer-b",
                    "layer_name": "layer-b",
                    "face_finish_type": "oracal_8500",
                    "face_area_m2": 0.36,
                    "return_finish_type": "white_aluminum",
                },
            ],
            roll_jobs=[_roll_job("layer-a", 0.5), _roll_job("layer-b", 0.4)],
        )
        mixed = deepcopy(payload)
        mixed["finish_setup"]["letter_group_finishes"][1]["face_finish_type"] = "oracal_651"
        both_8500 = build_intake_v4_material_breakdown("ws-d2-both", payload)
        mixed_result = build_intake_v4_material_breakdown("ws-d2-mixed", mixed)
        row_8500_both = _vinyl_row(both_8500, "8500")
        row_8500_mixed = _vinyl_row(mixed_result, "8500")
        row_651_mixed = _vinyl_row(mixed_result, "651")
        assert row_8500_mixed.quantity < row_8500_both.quantity
        assert row_651_mixed.quantity == 0.4

    @pytest.mark.asyncio
    async def test_owner_oracal_prices_preserved_with_registry(self):
        payload = _layer_finish_payload(
            groups=[
                {
                    "group_key": "layer-a",
                    "layer_name": "layer-a",
                    "face_finish_type": "oracal_8500",
                    "face_area_m2": 0.5,
                    "return_finish_type": "white_aluminum",
                }
            ],
            roll_jobs=[_roll_job("layer-a", 0.5)],
        )
        from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown_with_registry

        with patch(
            "services.inventory_materials_admin_service.load_material_pricing_dict",
            new_callable=AsyncMock,
        ) as lookup:
            lookup.return_value = {
                "MAT-ORACAL-8500": {"unit_cost": 99.0, "currency": "EUR", "source": "inventory_materials"},
            }
            result = await build_intake_v4_material_breakdown_with_registry(
                None,  # type: ignore[arg-type]
                "ws-owner",
                payload,
            )
        row = _vinyl_row(result, "8500")
        assert row.unit_price == INTAKE_V4_ORACAL_8500_EUR_PER_M2


def test_face_oracal_areas_by_series_roll_layer_attribution_no_global_scale():
    groups = [
        {"layer_name": "layer-a", "group_key": "layer-a", "face_finish_type": "oracal_8500", "face_area_m2": 0.33},
        {"layer_name": "layer-b", "group_key": "layer-b", "face_finish_type": "oracal_8500", "face_area_m2": 0.36},
    ]
    roll_by_layer = {"layer-a": 0.5, "layer-b": 0.4, "layer-c": 0.3}
    scaled_wrong = face_oracal_vinyl_areas_by_series(groups, "oracal_651", 0.9, roll_area_by_layer=None)
    attributed = face_oracal_vinyl_areas_by_series(groups, "oracal_651", 0.9, roll_area_by_layer=roll_by_layer)
    assert scaled_wrong["8500"] == 0.9
    assert attributed["8500"] == 0.9
