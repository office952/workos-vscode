"""Intake V4 Oracal 641/651 owner face vinyl pricing — series-specific, no registry bleed."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services.intake_v4_material_breakdown_service import (
    WASTE_PERCENT,
    BASIS_ROLL_NESTING,
    build_intake_v4_material_breakdown,
    build_intake_v4_material_breakdown_with_registry,
    _apply_registry_prices,
)
from schemas.intake_v4 import IntakeV4MaterialQuantityRow
from services.intake_v4_oracal_face_pricing_service import (
    INTAKE_V4_ORACAL_641_EUR_PER_M2,
    INTAKE_V4_ORACAL_651_EUR_PER_M2,
    INTAKE_V4_ORACAL_8500_EUR_PER_M2,
    is_intake_v4_owner_oracal_price_source,
    resolve_intake_v4_oracal_face_series,
)


def _payload(*, face_finish: str, area_m2: float = 0.5834, roll_nesting: bool = False) -> dict:
    nesting: dict = {}
    if roll_nesting:
        nesting["rolls"] = [
            {
                "configId": "vinyl_roll_1000",
                "rollWidthMm": 1000,
                "jobs": [
                    {
                        "sourceLayerName": "litere-volumetrice-1",
                        "colorKey": "651-green",
                        "consumedLengthMm": 5834,
                        "usedRollAreaSqm": area_m2,
                        "placedItemsCount": 3,
                        "unplacedItemsCount": 0,
                        "efficiencyPercent": 80.0,
                    }
                ],
            }
        ]

    return {
        "schema_version": "1.0.0",
        "product_binding": {"template_code": "TPL-VOLUMETRIC-LETTERS"},
        "svg_analysis_json": {
            "schemaVersion": "1.10.0",
            "nesting": nesting,
            "layers": [
                {
                    "id": "litere-volumetrice-1",
                    "name": "litere-volumetrice-1",
                    "perimeterMl": 10.0,
                    "filledAreaSqm": area_m2,
                }
            ],
            "geometry": {"perimeterMl": 10.0},
        },
        "quote_geometry": {
            "letter_perimeter_m": 10.0,
            "face_area_m2": area_m2,
            "backing_area_m2": area_m2,
            "return_material_perimeter_ml": 10.0,
        },
        "path_geometry_summary": {
            "parse_status": "parsed",
            "face_area_m2": area_m2,
            "backing_area_m2": area_m2,
            "return_material_perimeter_ml": 10.0,
        },
        "finish_setup": {
            "face_finish_type": face_finish,
            "return_finish_type": "oracal_wrapped",
            "return_depth_mm": 60,
            "illuminated": False,
            "letter_group_finishes": [
                {
                    "group_key": "litere-volumetrice-1",
                    "layer_name": "litere-volumetrice-1",
                    "face_finish_type": face_finish,
                    "face_area_m2": area_m2,
                    "return_finish_type": "oracal_wrapped",
                    "return_oracal_code": "651-010",
                }
            ],
            "confirmed": True,
        },
    }


class TestIntakeV4OracalFaceSeries:
    def test_series_resolver_keeps_641_651_and_8500_distinct(self):
        assert resolve_intake_v4_oracal_face_series("oracal_641") == "641"
        assert resolve_intake_v4_oracal_face_series("oracal_651") == "651"
        assert resolve_intake_v4_oracal_face_series("oracal_8500") == "8500"
        assert resolve_intake_v4_oracal_face_series("oracal_8500") != "651"


class TestIntakeV4OracalOwnerFacePricing:
    def test_face_oracal_641_area_times_owner_price(self):
        area = 0.5834
        result = build_intake_v4_material_breakdown("ws-641", _payload(face_finish="oracal_641", area_m2=area))
        vinyl = next(row for row in result.material_rows if row.material_key == "face_vinyl_641")
        assert vinyl.unit_price == INTAKE_V4_ORACAL_641_EUR_PER_M2
        assert vinyl.price_source == "intake_v4_owner_oracal_641"
        priced_qty = vinyl.priced_quantity
        assert priced_qty == round(area * (1 + WASTE_PERCENT / 100), 4)
        assert vinyl.estimated_cost == round(priced_qty * INTAKE_V4_ORACAL_641_EUR_PER_M2, 4)
        assert "face_vinyl_651" not in {row.material_key for row in result.material_rows}

    def test_face_oracal_651_area_times_owner_price(self):
        area = 0.5834
        result = build_intake_v4_material_breakdown("ws-651", _payload(face_finish="oracal_651", area_m2=area))
        vinyl = next(row for row in result.material_rows if row.material_key == "face_vinyl_651")
        assert vinyl.unit_price == INTAKE_V4_ORACAL_651_EUR_PER_M2
        assert vinyl.price_source == "intake_v4_owner_oracal_651"
        priced_qty = vinyl.priced_quantity
        assert vinyl.estimated_cost == round(priced_qty * INTAKE_V4_ORACAL_651_EUR_PER_M2, 4)
        assert "face_vinyl_641" not in {row.material_key for row in result.material_rows}

    def test_face_oracal_8500_area_times_owner_price_before_vat(self):
        area = 0.5834
        result = build_intake_v4_material_breakdown("ws-8500", _payload(face_finish="oracal_8500", area_m2=area))
        vinyl = next(row for row in result.material_rows if row.material_key == "face_vinyl_8500")
        assert vinyl.unit_price == INTAKE_V4_ORACAL_8500_EUR_PER_M2
        assert vinyl.price_source == "intake_v4_owner_oracal_8500"
        priced_qty = vinyl.priced_quantity
        assert vinyl.estimated_cost == round(priced_qty * INTAKE_V4_ORACAL_8500_EUR_PER_M2, 4)
        assert "face_vinyl_651" not in {row.material_key for row in result.material_rows}
        assert "face_vinyl_641" not in {row.material_key for row in result.material_rows}

    def test_return_colantat_keeps_oracal_651_series(self):
        payload = _payload(face_finish="oracal_651")
        group = payload["finish_setup"]["letter_group_finishes"][0]
        group["return_finish_type"] = "oracal_wrapped"
        group["return_oracal_code"] = "651-020"
        result = build_intake_v4_material_breakdown("ws-return", payload)
        assert result.stock_consumption is False
        assert result.consumption_mode == "quote_estimate_not_stock"
        keys = {row.material_key for row in result.material_rows}
        assert "face_vinyl_651" in keys
        assert "edge_cant_oracal_651" in keys
        edge_vinyl = next(row for row in result.material_rows if row.material_key == "edge_cant_oracal_651")
        assert edge_vinyl.unit_price == INTAKE_V4_ORACAL_651_EUR_PER_M2
        assert "shared_edge_cant_rules" in edge_vinyl.quantity_source
        assert not any(key.startswith("return_vinyl") for key in keys)

    @pytest.mark.asyncio
    async def test_owner_oracal_rows_not_overridden_by_registry(self):
        with patch(
            "services.inventory_materials_admin_service.load_material_pricing_dict",
            new_callable=AsyncMock,
        ) as lookup:
            lookup.return_value = {
                "MAT-ORACAL-641": {"unit_cost": 99.0, "currency": "EUR", "source": "inventory_materials"},
                "MAT-ORACAL-651": {"unit_cost": 99.0, "currency": "EUR", "source": "inventory_materials"},
                "MAT-ORACAL-8500": {"unit_cost": 99.0, "currency": "EUR", "source": "inventory_materials"},
            }
            result = await build_intake_v4_material_breakdown_with_registry(
                None,  # type: ignore[arg-type]
                "ws-registry",
                _payload(face_finish="oracal_641"),
            )
            result_8500 = await build_intake_v4_material_breakdown_with_registry(
                None,  # type: ignore[arg-type]
                "ws-registry-8500",
                _payload(face_finish="oracal_8500"),
            )
        vinyl = next(row for row in result.material_rows if row.material_key == "face_vinyl_641")
        assert vinyl.unit_price == INTAKE_V4_ORACAL_641_EUR_PER_M2
        assert vinyl.price_source == "intake_v4_owner_oracal_641"
        vinyl_8500 = next(row for row in result_8500.material_rows if row.material_key == "face_vinyl_8500")
        assert vinyl_8500.unit_price == INTAKE_V4_ORACAL_8500_EUR_PER_M2
        assert vinyl_8500.price_source == "intake_v4_owner_oracal_8500"
        assert vinyl_8500.unit_price != INTAKE_V4_ORACAL_651_EUR_PER_M2

    @pytest.mark.asyncio
    async def test_edge_cant_oracal_651_composite_owner_source_not_overridden_by_registry(self):
        with patch(
            "services.inventory_materials_admin_service.load_material_pricing_dict",
            new_callable=AsyncMock,
        ) as lookup:
            lookup.return_value = {
                "MAT-ORACAL-651": {"unit_cost": 5.0, "currency": "EUR", "source": "inventory_materials"},
            }
            payload = _payload(face_finish="oracal_651")
            group = payload["finish_setup"]["letter_group_finishes"][0]
            group["return_finish_type"] = "oracal_wrapped"
            group["return_oracal_code"] = "651-020"
            result = await build_intake_v4_material_breakdown_with_registry(
                None,  # type: ignore[arg-type]
                "ws-edge-cant-oracal",
                payload,
            )
        edge_vinyl = next(row for row in result.material_rows if row.material_key == "edge_cant_oracal_651")
        assert edge_vinyl.unit_price == INTAKE_V4_ORACAL_651_EUR_PER_M2
        assert edge_vinyl.price_source == "shared_edge_cant_rules|intake_v4_owner_oracal_651"
        assert edge_vinyl.unit_price != 5.0


def test_is_intake_v4_owner_oracal_price_source_direct_and_composite():
    assert is_intake_v4_owner_oracal_price_source("intake_v4_owner_oracal_651")
    assert is_intake_v4_owner_oracal_price_source("shared_edge_cant_rules|intake_v4_owner_oracal_651")
    assert is_intake_v4_owner_oracal_price_source("some_future_module|intake_v4_owner_oracal_8500")
    assert not is_intake_v4_owner_oracal_price_source("pricing_registry")
    assert not is_intake_v4_owner_oracal_price_source("shared_edge_cant_rules")
    assert not is_intake_v4_owner_oracal_price_source(None)


@pytest.mark.asyncio
async def test_apply_registry_prices_composite_owner_oracal_skipped():
    row = IntakeV4MaterialQuantityRow(
        material_key="edge_cant_oracal_651",
        display_name="Oracal 651 / cant volum",
        category="material",
        quantity=1.1442,
        base_quantity=1.1442,
        unit="m2",
        quantity_basis="edge_cant_oracal_wrap",
        quantity_source="shared_edge_cant_rules",
        quantity_quality="estimated",
        waste_percent=None,
        quantity_with_waste=1.1442,
        priced_quantity=1.1442,
        registry_code="MAT-ORACAL-651",
        material_code="MAT-ORACAL-651",
        unit_price=9.0,
        currency="EUR",
        price_source="shared_edge_cant_rules|intake_v4_owner_oracal_651",
    )
    with patch(
        "services.inventory_materials_admin_service.load_material_pricing_dict",
        new_callable=AsyncMock,
    ) as lookup:
        lookup.return_value = {
            "MAT-ORACAL-651": {"unit_cost": 5.0, "currency": "EUR", "source": "inventory_materials"},
        }
        enriched = await _apply_registry_prices(None, [row])  # type: ignore[arg-type]
    assert enriched[0].unit_price == 9.0
    assert enriched[0].price_source == "shared_edge_cant_rules|intake_v4_owner_oracal_651"
    assert enriched[0].unit_price != 5.0


@pytest.mark.asyncio
async def test_apply_registry_prices_non_owner_still_uses_registry():
    row = IntakeV4MaterialQuantityRow(
        material_key="plexiglas_face",
        display_name="Plexiglas",
        category="material",
        quantity=1.0,
        base_quantity=1.0,
        unit="m2",
        quantity_basis=BASIS_ROLL_NESTING,
        quantity_source="svg_analysis_json.nesting",
        quantity_quality="estimated",
        waste_percent=None,
        quantity_with_waste=1.0,
        priced_quantity=1.0,
        registry_code="MAT-ACP-FATA-LITERE",
        material_code="MAT-ACP-FATA-LITERE",
        price_source="missing",
    )
    with patch(
        "services.inventory_materials_admin_service.load_material_pricing_dict",
        new_callable=AsyncMock,
    ) as lookup:
        lookup.return_value = {
            "MAT-ACP-FATA-LITERE": {"unit_cost": 10.0, "currency": "EUR", "source": "inventory_materials"},
        }
        enriched = await _apply_registry_prices(None, [row])  # type: ignore[arg-type]
    assert enriched[0].unit_price == 10.0
    assert enriched[0].price_source == "pricing_registry"
