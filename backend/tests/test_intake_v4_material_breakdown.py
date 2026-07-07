"""Intake V4 material breakdown — quote material costing for volumetric letters."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from schemas.intake_v4 import IntakeV4CncOperationRow, IntakeV4MaterialQuantityRow
from services.intake_v4_material_breakdown_service import (
    BASIS_AREA_FALLBACK,
    BASIS_ROLL_NESTING,
    BASIS_PERIMETER,
    PILOT_V4_TEMPLATE_CODE,
    WASTE_PERCENT,
    _apply_registry_operation_prices,
    _apply_registry_prices,
    _build_mounting_accessories_percent_row,
    build_intake_v4_material_breakdown,
    build_intake_v4_material_breakdown_with_registry,
)
from services.intake_v4_nesting_material_precision import (
    BASIS_LAMINATE_AREA,
    BASIS_PRINT_AREA,
    BASIS_SHEET_NESTING_PRORATED_FALLBACK,
    BASIS_SHEET_NESTING_ROLE_SPLIT,
    CONFIDENCE_FORMULA,
    CONFIDENCE_NESTING_HIGH,
    CONFIDENCE_PERIMETER,
)


def _payload_with_letter_groups(*, roll_nesting: bool = True, sheet_nesting: bool = True) -> dict:
    nesting: dict = {}
    if sheet_nesting:
        nesting["sheets"] = [
            {
                "configId": "sheet_1300x900",
                "sheetsUsed": 2,
                "usedSheetAreaSqm": 2.34,
                "placedItemsCount": 4,
                "unplacedItemsCount": 0,
                "efficiencyPercent": 70.0,
            }
        ]
    if roll_nesting:
        nesting["rolls"] = [
            {
                "configId": "vinyl_roll_1000",
                "rollWidthMm": 1000,
                "jobs": [
                    {
                        "sourceLayerName": "litere-volumetrice-1",
                        "colorKey": "651-green",
                        "consumedLengthMm": 8000,
                        "usedRollAreaSqm": 8.0,
                        "placedItemsCount": 3,
                        "unplacedItemsCount": 0,
                        "efficiencyPercent": 80.0,
                    }
                ],
            }
        ]

    return {
        "schema_version": "1.0.0",
        "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
        "svg_analysis_json": {
            "schemaVersion": "1.10.0",
            "nesting": nesting,
            "layers": [
                {
                    "id": "litere-volumetrice-1",
                    "name": "litere-volumetrice-1",
                    "perimeterMl": 10.0,
                    "filledAreaSqm": 1.5,
                }
            ],
            "geometry": {"perimeterMl": 10.0},
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
                    "return_finish_type": "oracal_wrapped",
                },
                {
                    "group_key": "logo",
                    "layer_name": "logo",
                    "face_finish_type": "none",
                    "face_area_m2": 0.4,
                },
            ],
            "artwork_finishes": [
                {
                    "layer_key": "logo",
                    "layer_name": "logo",
                    "execution_type": "needs_decision",
                    "estimated_area_m2": 0.4,
                },
            ],
            "confirmed": True,
        },
    }


def _payload_with_sheet_role_split(*, roll_nesting: bool = False) -> dict:
    payload = _payload_with_letter_groups(roll_nesting=roll_nesting, sheet_nesting=True)
    payload["svg_analysis_json"]["nesting"]["sheets"][0]["placements"] = [
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
    ]
    payload["svg_analysis_json"]["parts"] = {
        "items": [
            {
                "id": "letter-face-a",
                "source": {"layerId": "litere-volumetrice-1", "layerName": "litere-volumetrice-1"},
            },
            {
                "id": "letter-back-a",
                "derivedPartKind": "back-cover-plate",
                "materialLabel": "Forex 3mm capac spate",
                "source": {"layerId": "litere-backing", "layerName": "litere-backing"},
            },
        ]
    }
    payload["layer_role_setup"] = {
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
    }
    return payload


class TestIntakeV4MaterialBreakdownLetterGroups:
    def test_oracal_prefers_roll_nesting_when_jobs_present(self):
        result = build_intake_v4_material_breakdown("ws-1", _payload_with_letter_groups(roll_nesting=True))
        vinyl = next(row for row in result.material_rows if row.material_key == "face_vinyl_651")
        assert vinyl.quantity_basis == BASIS_ROLL_NESTING
        assert vinyl.quantity == 8.0
        assert vinyl.waste_percent is None
        assert vinyl.priced_quantity == 8.0
        assert any(row.nesting_kind == "roll" for row in result.nesting_rows)

    def test_vinyl_area_fallback_when_no_roll_nesting(self):
        result = build_intake_v4_material_breakdown("ws-2", _payload_with_letter_groups(roll_nesting=False))
        vinyl = next(row for row in result.material_rows if row.material_key == "face_vinyl_651")
        assert vinyl.quantity_basis == BASIS_AREA_FALLBACK
        assert vinyl.quantity == 1.5
        assert vinyl.waste_percent == WASTE_PERCENT

    def test_ral_paint_spray_uses_owner_tube_rule_for_painted_cant(self):
        payload = _payload_with_letter_groups(roll_nesting=False, sheet_nesting=False)
        payload["finish_setup"]["return_finish_type"] = "white_aluminum"
        payload["finish_setup"]["letter_group_finishes"] = [
            {
                "group_key": "litere-volumetrice-1",
                "layer_name": "litere-volumetrice-1",
                "face_finish_type": "oracal_651",
                "face_area_m2": 1.5,
                "return_finish_type": "ral_paint",
                "return_oracal_code": "9005",
                "return_oracal_name": "Jet black",
                "perimeter_m": 16.2,
            }
        ]
        payload["finish_setup"]["artwork_finishes"] = []

        result = build_intake_v4_material_breakdown("ws-ral", payload)
        row = next(item for item in result.material_rows if item.material_key == "ral_paint_spray")

        assert row.registry_code == "MAT-VOPSEA-RAL"
        assert row.quantity == 2
        assert row.base_quantity == 1.08
        assert row.priced_quantity == 2
        assert row.unit_price == 10.0
        assert row.estimated_cost == 20.0
        assert "50 RON/tub" in row.quantity_source
        assert "15 m pe tub" in row.warnings[0]

    def test_sheet_nesting_prorated_fallback_without_placement_metadata(self):
        payload = _payload_with_letter_groups(roll_nesting=False)
        payload["layer_role_setup"] = {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "litere-volumetrice-1",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                },
                {
                    "layer_key": "backing-layer",
                    "confirmed_role": "backing",
                    "confirmation_state": "confirmed",
                },
            ],
        }
        result = build_intake_v4_material_breakdown("ws-sheet", payload)
        plexi = next(row for row in result.material_rows if row.material_key == "plexiglas_face")
        forex = next(row for row in result.material_rows if row.material_key == "forex_backing")
        assert plexi.quantity_basis == BASIS_SHEET_NESTING_PRORATED_FALLBACK
        assert forex.quantity_basis == BASIS_SHEET_NESTING_PRORATED_FALLBACK
        assert plexi.waste_percent is None
        assert round(plexi.quantity + forex.quantity, 4) == 2.34
        assert any(w.code == "sheet_nesting_prorated_fallback" for w in result.warnings)

    def test_sheet_nesting_role_split_when_metadata_present(self):
        result = build_intake_v4_material_breakdown("ws-role-split", _payload_with_sheet_role_split())
        plexi = next(row for row in result.material_rows if row.material_key == "plexiglas_face")
        forex = next(row for row in result.material_rows if row.material_key == "forex_backing")
        assert plexi.quantity_basis in {BASIS_SHEET_NESTING_ROLE_SPLIT, "sheet_nesting_part_kind_quote_estimate"}
        assert forex.quantity_basis == plexi.quantity_basis
        # Placement footprint below letter-group eligible area — floor raises to 1.5 m².
        assert plexi.quantity == 1.5
        assert forex.quantity == 0.16
        assert round(plexi.quantity + forex.quantity, 4) == 1.66
        assert not any(w.code == "sheet_nesting_prorated_fallback" for w in result.warnings)
        assert result.nesting_preview is not None
        trace = next(t for t in result.nesting_preview.material_traces if t.material_key == "plexiglas_face")
        assert trace.uses_placement_footprint is True
        assert trace.uses_full_sheet_stock_proration is False

    def test_derives_geometry_from_nest2_when_quote_geometry_missing(self):
        payload = _payload_with_letter_groups(roll_nesting=False, sheet_nesting=False)
        payload["quote_geometry"] = {}
        payload["layer_role_setup"] = {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "litere-volumetrice-1",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                }
            ],
        }
        result = build_intake_v4_material_breakdown("ws-derived", payload)
        plexi = next(row for row in result.material_rows if row.material_key == "plexiglas_face")
        assert plexi.quantity == 1.5
        assert plexi.quantity_basis == BASIS_AREA_FALLBACK

    def test_logo_only_artwork_blocks_letters_sheet_prorated_fallback_for_plexiglas(self):
        payload = {
            "schema_version": "1.0.0",
            "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
            "svg_analysis_json": {
                "nesting": {
                    "sheets": [
                        {
                            "configId": "sheet_3000x2000",
                            "sheetsUsed": 1,
                            "usedSheetAreaSqm": 6.0,
                            "placedItemsCount": 1,
                            "unplacedItemsCount": 0,
                            "placements": [
                                {
                                    "partId": "art-a",
                                    "sourceLayerName": "Logo 1",
                                    "placedWidthMm": 1000,
                                    "placedHeightMm": 1000,
                                }
                            ],
                        }
                    ]
                },
                "parts": {
                    "items": [
                        {
                            "id": "art-a",
                            "source": {"layerId": "logo-dreapta", "layerName": "Logo 1"},
                        }
                    ]
                },
                "layers": [
                    {
                        "id": "logo-dreapta",
                        "name": "Logo 1",
                        "perimeterMl": 3.142,
                        "filledAreaSqm": 1.0,
                    }
                ],
            },
            "quote_geometry": {
                "face_area_m2": 1.0004,
                "letter_face_area_m2": 1.0004,
                "artwork_area_m2": 1.0,
                "artwork_boxes": [
                    {"layer_key": "logo-dreapta", "width_mm": 1000, "height_mm": 1000, "area_m2": 1.0}
                ],
                "return_material_perimeter_ml": 6.284,
                "letter_return_perimeter_ml": 3.142,
                "artwork_return_perimeter_ml": 3.142,
            },
            "path_geometry_summary": {
                "face_area_m2": 1.0004,
                "letter_face_area_m2": 1.0004,
                "artwork_area_m2": 1.0,
                "return_material_perimeter_ml": 6.284,
            },
            "layer_role_setup": {
                "confirmation_status": "complete",
                "layers": [
                    {
                        "layer_key": "logo-dreapta",
                        "layer_name": "Logo 1",
                        "confirmed_role": "printed_artwork",
                        "confirmation_state": "confirmed",
                    }
                ],
            },
            "finish_setup": {
                "face_finish_type": "oracal_651",
                "return_finish_type": "white_aluminum",
                "return_depth_mm": 60,
                "illuminated": True,
                "letter_group_finishes": [],
                "artwork_finishes": [
                    {
                        "layer_key": "logo-dreapta",
                        "layer_name": "Logo 1",
                        "execution_type": "none_raw_plexi",
                        "face_personalization_method": "none_raw_plexi",
                        "estimated_area_m2": 1.0,
                        "return_finish_type": "white_aluminum",
                        "return_depth_mm": 60,
                    }
                ],
            },
        }

        result = build_intake_v4_material_breakdown("ws-logo-only-prorated-blocked", payload)
        plexi = next(row for row in result.material_rows if row.material_key == "plexiglas_face")
        assert plexi.quantity_basis == "artwork_box_bounding_footprint_quote_estimate"
        assert plexi.quantity == pytest.approx(1.0, rel=0, abs=1e-4)
        assert plexi.estimated_cost is None
        assert not any(w.code == "sheet_nesting_prorated_fallback" for w in result.warnings)
        assert any(w.code == "sheet_nesting_prorated_fallback_blocked_for_logo_only" for w in result.warnings)

    def test_logo_only_unconfirmed_backing_does_not_emit_forex_from_area_fallback(self):
        payload = {
            "schema_version": "1.0.0",
            "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
            "svg_analysis_json": {
                "nesting": {
                    "sheets": [
                        {
                            "configId": "sheet_3000x2000",
                            "sheetsUsed": 1,
                            "usedSheetAreaSqm": 6.0,
                            "placedItemsCount": 1,
                            "unplacedItemsCount": 0,
                            "placements": [
                                {"partId": "art-a", "sourceLayerName": "Logo 1", "placedWidthMm": 1500, "placedHeightMm": 1500}
                            ],
                        }
                    ]
                },
                "parts": {"items": [{"id": "art-a", "source": {"layerId": "logo-dreapta", "layerName": "Logo 1"}}]},
                "layers": [
                    {"id": "logo-dreapta", "name": "Logo 1", "perimeterMl": 4.7553, "filledAreaSqm": 1.5547, "widthMm": 1500, "heightMm": 1500}
                ],
            },
            "quote_geometry": {
                "face_area_m2": 2.2506,
                "letter_face_area_m2": 2.2506,
                "artwork_area_m2": 1.5547,
                "artwork_boxes": [{"layer_key": "logo-dreapta", "width_mm": 1500, "height_mm": 1500, "area_m2": 2.25}],
            },
            "path_geometry_summary": {
                "face_area_m2": 2.2506,
                "letter_face_area_m2": 2.2506,
                "artwork_area_m2": 1.5547,
                "artwork_boxes": [{"layer_key": "logo-dreapta", "width_mm": 1500, "height_mm": 1500, "area_m2": 2.25}],
            },
            "layer_role_setup": {
                "confirmation_status": "complete",
                "layers": [
                    {
                        "layer_key": "logo-dreapta",
                        "layer_name": "Logo 1",
                        "confirmed_role": "printed_artwork",
                        "confirmation_state": "confirmed",
                    }
                ],
            },
        }

        result = build_intake_v4_material_breakdown("ws-logo-unconfirmed-backing", payload)
        keys = {row.material_key for row in result.material_rows}
        assert "plexiglas_face" in keys
        assert "forex_backing" not in keys
        assert any(w.code == "backing_not_confirmed" for w in result.warnings)

    def test_logo_only_physical_material_rows_use_artwork_box_footprint_source(self):
        payload = {
            "schema_version": "1.0.0",
            "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
            "svg_analysis_json": {
                "nesting": {
                    "sheets": [
                        {
                            "configId": "sheet_3000x2000",
                            "sheetsUsed": 1,
                            "usedSheetAreaSqm": 6.0,
                            "placedItemsCount": 1,
                            "unplacedItemsCount": 0,
                            "placements": [
                                {"partId": "art-a", "sourceLayerName": "Logo 1", "placedWidthMm": 1500, "placedHeightMm": 1500}
                            ],
                        }
                    ]
                },
                "parts": {"items": [{"id": "art-a", "source": {"layerId": "logo-dreapta", "layerName": "Logo 1"}}]},
                "layers": [
                    {"id": "logo-dreapta", "name": "Logo 1", "perimeterMl": 4.7553, "filledAreaSqm": 1.5547, "widthMm": 1500, "heightMm": 1500}
                ],
            },
            "quote_geometry": {
                "face_area_m2": 2.2506,
                "letter_face_area_m2": 2.2506,
                "artwork_area_m2": 1.5547,
                "artwork_boxes": [{"layer_key": "logo-dreapta", "width_mm": 1500, "height_mm": 1500, "area_m2": 2.25}],
            },
            "path_geometry_summary": {
                "face_area_m2": 2.2506,
                "letter_face_area_m2": 2.2506,
                "artwork_area_m2": 1.5547,
                "artwork_boxes": [{"layer_key": "logo-dreapta", "width_mm": 1500, "height_mm": 1500, "area_m2": 2.25}],
            },
            "layer_role_setup": {
                "confirmation_status": "complete",
                "layers": [
                    {
                        "layer_key": "logo-dreapta",
                        "layer_name": "Logo 1",
                        "confirmed_role": "printed_artwork",
                        "confirmation_state": "confirmed",
                    }
                ],
            },
            "finish_setup": {
                "backing_mode": "forex_10_no_bevel",
                "letter_group_finishes": [],
                "artwork_finishes": [
                    {
                        "layer_key": "logo-dreapta",
                        "layer_name": "Logo 1",
                        "execution_type": "none_raw_plexi",
                        "face_personalization_method": "none_raw_plexi",
                        "estimated_area_m2": 1.5547,
                        "return_finish_type": "white_aluminum",
                        "return_depth_mm": 60,
                    }
                ],
            },
        }

        result = build_intake_v4_material_breakdown("ws-logo-footprint-contract", payload)
        plexi = next(row for row in result.material_rows if row.material_key == "plexiglas_face")
        forex = next(row for row in result.material_rows if row.material_key == "forex_backing")

        assert plexi.quantity == pytest.approx(2.25, rel=0, abs=1e-4)
        assert forex.quantity == pytest.approx(2.25, rel=0, abs=1e-4)
        assert plexi.quantity_basis == "artwork_box_bounding_footprint_quote_estimate"
        assert forex.quantity_basis == "backing_area_fallback_from_artwork_box_footprint"
        assert plexi.quantity_source == "quote_geometry.artwork_boxes|bounding_box_footprint"
        assert forex.quantity_source == "quote_geometry.artwork_boxes|bounding_box_footprint"
        assert plexi.source_part_ids == ["art-a"]
        assert forex.source_part_ids == ["art-a"]
        assert plexi.trace_markers == []
        assert forex.trace_markers == []
        assert "artwork_area_m2" not in plexi.quantity_source
        assert "face_area_m2" not in plexi.quantity_source
        assert "artwork_area_m2" not in forex.quantity_source
        assert "face_area_m2" not in forex.quantity_source
        assert any(w.code == "backing_artwork_box_footprint_used" for w in result.warnings)

    def test_print_material_should_not_use_raw_area_alias_as_final_physical_source(self):
        payload = _payload_with_letter_groups(roll_nesting=False, sheet_nesting=False)
        payload["finish_setup"]["face_finish_type"] = "print_laminate"
        payload["finish_setup"]["letter_group_finishes"] = [
            {
                "group_key": "litere-volumetrice-1",
                "layer_name": "litere-volumetrice-1",
                "face_finish_type": "print_laminate",
                "face_area_m2": 1.5,
                "return_finish_type": "standard_aluminum",
            }
        ]
        result = build_intake_v4_material_breakdown("ws-print-contract", payload)
        print_row = next(row for row in result.material_rows if row.material_key.endswith("print_vinyl"))

        assert "face_area_m2" not in (print_row.quantity_source or "")
        assert "artwork_finishes|svg_analysis_json.layers" not in (print_row.quantity_source or "")


class TestIntakeV4ArtworkVolumetricBreakdown:
    def test_separate_emblem_adds_plexiglas_and_return(self):
        payload = _payload_with_letter_groups(roll_nesting=False, sheet_nesting=False)
        payload["svg_analysis_json"]["layers"].append(
            {
                "id": "logo",
                "name": "logo",
                "perimeterMl": 4.2,
                "filledAreaSqm": 0.85,
            }
        )
        payload["finish_setup"]["artwork_finishes"] = [
            {
                "layer_key": "logo",
                "layer_name": "logo",
                "execution_type": "separate_emblem",
                "estimated_area_m2": 0.85,
                "return_finish_type": "oracal_wrapped",
                "return_depth_mm": 60,
            }
        ]
        result = build_intake_v4_material_breakdown("ws-art", payload)
        keys = {row.material_key for row in result.material_rows}
        assert "artwork_plexiglas_logo" in keys
        assert "artwork_return_logo" in keys
        plexi = next(row for row in result.material_rows if row.material_key == "artwork_plexiglas_logo")
        assert plexi.quantity == 0.85
        ret = next(row for row in result.material_rows if row.material_key == "artwork_return_logo")
        assert ret.quantity == 4.2


class TestIntakeV4QuoteMaterialCosting:
    def test_response_contract_quote_estimate_not_stock(self):
        result = build_intake_v4_material_breakdown("ws-contract", _payload_with_letter_groups(roll_nesting=False))
        assert result.costing_purpose == "quote_material_cost_estimate"
        assert result.consumption_mode == "quote_estimate_not_stock"
        assert result.stock_consumption is False
        assert result.breakdown_scope == "quote_material_cost_estimate"
        plexi = next(row for row in result.material_rows if row.material_key == "plexiglas_face")
        assert plexi.consumption_mode == "quote_estimate"
        assert plexi.quantity_basis == BASIS_SHEET_NESTING_PRORATED_FALLBACK
        assert plexi.base_quantity == plexi.quantity
        assert plexi.material_code == plexi.registry_code

    def test_no_double_waste_on_nesting_based_rows(self):
        result = build_intake_v4_material_breakdown("ws-waste", _payload_with_letter_groups(roll_nesting=True))
        vinyl = next(row for row in result.material_rows if row.material_key == "face_vinyl_651")
        assert vinyl.waste_percent is None
        assert vinyl.priced_quantity == vinyl.base_quantity
        ret = next(row for row in result.material_rows if row.material_key == "return_material")
        assert ret.quantity_basis == BASIS_PERIMETER
        assert ret.waste_percent == WASTE_PERCENT

    def test_return_profile_variant_by_depth(self):
        result = build_intake_v4_material_breakdown("ws-depth", _payload_with_letter_groups(roll_nesting=False))
        ret = next(row for row in result.material_rows if row.material_key == "return_material")
        assert ret.material_code == "MAT-PROFIL-LATERAL-LITERE-60MM"

    def test_no_owner_fallback_price_source(self):
        result = build_intake_v4_material_breakdown("ws-nofallback", _payload_with_letter_groups(roll_nesting=False))
        for row in result.material_rows + result.consumable_rows:
            assert row.price_source != "owner_fallback"

    def test_print_laminate_rows_when_face_finish_print(self):
        payload = _payload_with_letter_groups(roll_nesting=False, sheet_nesting=False)
        payload["finish_setup"]["face_finish_type"] = "print_laminate"
        for group in payload["finish_setup"]["letter_group_finishes"]:
            if group.get("face_finish_type") != "none":
                group["face_finish_type"] = "print_laminate"
        result = build_intake_v4_material_breakdown("ws-print", payload)
        keys = {row.material_key for row in result.material_rows}
        assert any(k.endswith("_print_vinyl") for k in keys)
        assert any(k.endswith("_laminated_vinyl") for k in keys)
        assert "face_vinyl" not in keys
        print_row = next(row for row in result.material_rows if row.material_key.endswith("_print_vinyl"))
        assert print_row.quantity_basis == BASIS_PRINT_AREA
        assert print_row.display_name.startswith("Material print Orafol")
        laminate_row = next(row for row in result.material_rows if row.material_key.endswith("_laminated_vinyl"))
        assert laminate_row.quantity_basis == BASIS_LAMINATE_AREA
        assert laminate_row.registry_code == "MAT-VINYL-PRINT-LAMINATED"
        print_service = next(row for row in result.operation_rows if row.key.endswith("_print_service"))
        assert print_service.display_name.startswith("Serviciu print")
        assert any(row.key.endswith("_lamination_service") for row in result.operation_rows)
        assert any(row.key.endswith("_application_service") for row in result.operation_rows)

    def test_printed_vinyl_skips_laminate_material_but_keeps_application_service(self):
        payload = _payload_with_letter_groups(roll_nesting=False, sheet_nesting=False)
        payload["finish_setup"]["face_finish_type"] = "printed_vinyl"
        for group in payload["finish_setup"]["letter_group_finishes"]:
            if group.get("face_finish_type") != "none":
                group["face_finish_type"] = "printed_vinyl"

        result = build_intake_v4_material_breakdown("ws-printed-vinyl", payload)

        assert any(row.material_key.endswith("_print_vinyl") for row in result.material_rows)
        assert not any(row.material_key.endswith("_laminated_vinyl") for row in result.material_rows)
        assert any(row.key.endswith("_print_service") for row in result.operation_rows)
        assert not any(row.key.endswith("_lamination_service") for row in result.operation_rows)
        assert any(row.key.endswith("_application_service") for row in result.operation_rows)

    @pytest.mark.asyncio
    async def test_operation_price_falls_back_to_owner_service_rate_for_m2_rows(self):
        row = IntakeV4CncOperationRow(
            key="artwork_logo_application_service",
            display_name="Serviciu aplicare — logo",
            operation_type="vinyl_application",
            quantity=1.2,
            unit="m2",
            operation_equivalent_quantity=1.2,
            operation_equivalent_unit="m2",
            pricing_rate_key="workcenter_rates:WC_VINYL_APPLICATION:per_square_meter",
        )
        with patch(
            "services.workcenter_rates_service.load_workcenter_rate_pricing_dict",
            new_callable=AsyncMock,
        ) as lookup:
            lookup.return_value = {}
            enriched = await _apply_registry_operation_prices(None, [row])  # type: ignore[arg-type]
        assert enriched[0].unit_price == 3.0
        assert enriched[0].estimated_cost == 3.6
        assert enriched[0].pricing_status == "intake_v4_owner_application_service"

    def test_raw_vector_total_includes_unclassified_logo_perimeter(self):
        payload = _payload_with_letter_groups(roll_nesting=False, sheet_nesting=False)
        payload["quote_geometry"].update(
            {
                "return_material_perimeter_ml": 24.6488,
                "letter_return_perimeter_ml": 24.6488,
                "face_cutting_perimeter_ml": 24.6488,
                "cutting_perimeter_ml": 24.6488,
                "cnc_cutting_perimeter_ml": 24.6488,
                "inner_hole_letter_perimeter_ml": 3.4812,
            }
        )
        payload["path_geometry_summary"].update(
            {
                "perimeter_mm_approx": 31637.330856,
                "return_material_perimeter_ml": 24.6488,
                "face_cutting_perimeter_ml": 24.6488,
                "cutting_perimeter_ml": 24.6488,
                "cnc_cutting_perimeter_ml": 24.6488,
            }
        )
        payload["finish_setup"]["return_finish_type"] = "white_aluminum"
        payload["finish_setup"]["letter_group_finishes"] = [
            {
                "group_key": "letters",
                "layer_name": "letters",
                "face_finish_type": "oracal_651",
                "face_area_m2": 1.2638,
                "perimeter_m": 26.7472,
                "return_finish_type": "white_aluminum",
                "return_depth_mm": 60,
                "confirmed": True,
            }
        ]

        result = build_intake_v4_material_breakdown("ws-raw-vector", payload)

        ret = next(row for row in result.material_rows if row.material_key == "return_material")
        assert ret.quantity == 31.6373
        adhesive = next(row for row in result.consumable_rows if row.material_key == "adhesive_return_to_face")
        assert adhesive.quantity == 63.2746
        assert any(round(row.quantity, 4) == 31.6373 for row in result.operation_rows)
        assert any(w.code == "raw_vector_total_perimeter_applied" for w in result.warnings)
        assert any(w.code == "unclassified_vector_artwork_requires_decision" for w in result.warnings)

    def test_mounting_accessories_use_internal_manufacturing_subtotal_before_markup(self):
        row = _build_mounting_accessories_percent_row(596.24)

        assert row is not None
        assert row.material_key == "mounting_accessories_percent"
        assert row.category == "consumable"
        assert row.quantity == 1.0
        assert row.unit == "job"
        assert row.unit_price == 29.812
        assert row.estimated_cost == 29.812
        assert row.material_code == "MAT-CONSUMABILE-MONTAJ"
        assert row.registry_code is None
        assert "manufacturing_cost_subtotal_before_markup=596.24" in row.quantity_source
        assert "excludes_client_markup" in row.quantity_source

    @pytest.mark.asyncio
    async def test_registry_price_enriches_estimated_cost(self):
        row = IntakeV4MaterialQuantityRow(
            material_key="face_vinyl",
            display_name="Vinil",
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
            registry_code="MAT-ORACAL-651",
            material_code="MAT-ORACAL-651",
            price_source="missing",
        )
        with patch(
            "services.inventory_materials_admin_service.load_material_pricing_dict",
            new_callable=AsyncMock,
        ) as lookup:
            lookup.return_value = {
                "MAT-ORACAL-651": {"unit_cost": 5.0, "currency": "EUR", "source": "inventory_materials"}
            }
            enriched = await _apply_registry_prices(None, [row])  # type: ignore[arg-type]
        assert enriched[0].unit_price == 5.0
        assert enriched[0].price_source == "pricing_registry"
        assert enriched[0].estimated_cost == 5.0

    @pytest.mark.asyncio
    async def test_registry_workcenter_rate_enriches_cnc_operation_cost(self):
        row = IntakeV4CncOperationRow(
            key="cnc_face_cutting",
            display_name="Debitare CNC",
            operation_type="cnc_cutting",
            quantity=24.6488,
            operation_equivalent_quantity=49.2976,
            operation_equivalent_unit="ml-pass",
            pricing_rate_key="workcenter_rates:CNC_ROUTER:per_linear_meter",
        )
        with patch(
            "services.workcenter_rates_service.load_workcenter_rate_pricing_dict",
            new_callable=AsyncMock,
        ) as lookup:
            lookup.return_value = {
                "CNC_ROUTER": {
                    "rate_basis": "per_linear_meter",
                    "rate_per_linear_meter": 1.5,
                    "currency": "EUR",
                    "source": "workcenter_rates",
                }
            }
            enriched = await _apply_registry_operation_prices(None, [row])  # type: ignore[arg-type]
        assert enriched[0].unit_price == 1.5
        assert enriched[0].estimated_cost == 73.9464
        assert enriched[0].pricing_status == "pricing_registry"

    @pytest.mark.asyncio
    async def test_missing_registry_sets_contains_missing_prices(self):
        payload = _payload_with_letter_groups(roll_nesting=False, sheet_nesting=False)
        with patch(
            "services.inventory_materials_admin_service.load_material_pricing_dict",
            new_callable=AsyncMock,
        ) as lookup:
            lookup.return_value = {}
            result = await build_intake_v4_material_breakdown_with_registry(None, "ws-miss", payload)  # type: ignore[arg-type]
        assert result.totals.contains_missing_prices is True
        registry_rows = [
            row
            for row in result.material_rows
            if row.quantity > 0 and "intake_v4_owner_oracal" not in (row.price_source or "")
        ]
        assert all(row.price_source == "missing" for row in registry_rows)
        owner_rows = [row for row in result.material_rows if row.price_source.startswith("intake_v4_owner_oracal")]
        assert owner_rows
        assert result.totals.estimated_cost_total > 0.0


class TestIntakeV4NestingMaterialPrecisionIntegration:
    def test_oracal_roll_confidence_and_no_double_waste(self):
        result = build_intake_v4_material_breakdown("ws-oracal", _payload_with_letter_groups(roll_nesting=True))
        vinyl = next(row for row in result.material_rows if row.material_key == "face_vinyl_651")
        assert vinyl.quantity_basis == BASIS_ROLL_NESTING
        assert vinyl.confidence == CONFIDENCE_NESTING_HIGH
        assert vinyl.waste_percent is None

    def test_return_perimeter_confidence(self):
        result = build_intake_v4_material_breakdown("ws-ret", _payload_with_sheet_role_split())
        ret = next(row for row in result.material_rows if row.material_key == "return_material")
        assert ret.quantity_basis == BASIS_PERIMETER
        assert ret.confidence == CONFIDENCE_PERIMETER
        assert ret.waste_percent == WASTE_PERCENT

    def test_led_psu_formula_basis(self):
        payload = _payload_with_letter_groups(roll_nesting=False, sheet_nesting=False)
        payload["finish_setup"]["illuminated"] = True
        payload["finish_setup"]["led_module_count"] = 42
        payload["finish_setup"]["psu_configuration"] = [100, 100]
        payload["finish_setup"]["required_psu_watts"] = 200
        result = build_intake_v4_material_breakdown("ws-led", payload)
        led = next(row for row in result.consumable_rows if row.material_key == "led_modules")
        psu = next(row for row in result.consumable_rows if row.material_key == "led_psu")
        assert led.confidence == CONFIDENCE_FORMULA
        assert psu.quantity_basis == "psu_configuration_quote_estimate"
        assert psu.confidence == CONFIDENCE_FORMULA

    def test_roll_color_split_warning(self):
        payload = _payload_with_letter_groups(roll_nesting=True)
        payload["svg_analysis_json"]["nesting"]["rolls"][0]["jobs"].append(
            {
                "sourceLayerName": "litere-volumetrice-1",
                "colorKey": "651-red",
                "usedRollAreaSqm": 2.0,
                "placedItemsCount": 1,
                "unplacedItemsCount": 0,
            }
        )
        result = build_intake_v4_material_breakdown("ws-colors", payload)
        assert any(w.code == "roll_nesting_color_split_missing" for w in result.warnings)

    def test_nesting_not_stock_warning(self):
        result = build_intake_v4_material_breakdown("ws-stock", _payload_with_sheet_role_split())
        assert any(w.code == "nesting_used_for_quote_not_stock" for w in result.warnings)
        assert result.stock_consumption is False

    def test_backing_not_confirmed_excludes_forex_from_estimate(self):
        payload = _payload_with_sheet_role_split()
        payload["layer_role_setup"] = {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "litere-volumetrice-1",
                    "layer_name": "litere-volumetrice-1",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                },
            ],
        }
        result = build_intake_v4_material_breakdown("ws-no-backing", payload)
        keys = {row.material_key for row in result.material_rows}
        assert "forex_backing" not in keys
        assert any(w.code == "backing_not_confirmed" for w in result.warnings)
        assert result.nesting_preview is not None
        assert any(w.code == "backing_not_confirmed" for w in result.nesting_preview.warnings)


def _payload_finish_truth_base() -> dict:
    payload = _payload_with_letter_groups(roll_nesting=True, sheet_nesting=False)
    payload["finish_setup"]["letter_group_finishes"] = [
        {
            "group_key": "layer-2",
            "layer_name": "Layer_x0020_2",
            "face_finish_type": "none",
            "face_area_m2": 0.35,
            "perimeter_m": 4.0,
            "return_finish_type": "standard_aluminum",
            "return_depth_mm": 60,
        },
        {
            "group_key": "layer-3",
            "layer_name": "Layer_x0020_3",
            "face_finish_type": "none",
            "face_area_m2": 0.23,
            "perimeter_m": 3.2,
            "return_finish_type": "standard_aluminum",
            "return_depth_mm": 60,
        },
    ]
    payload["finish_setup"]["face_finish_type"] = "oracal_651"
    payload["finish_setup"]["return_finish_type"] = "oracal_wrapped"
    payload["finish_setup"]["artwork_finishes"] = [
        {
            "layer_key": "layer-1",
            "layer_name": "Layer_x0020_1",
            "execution_type": "needs_decision",
            "color_mode": "polychrome",
            "estimated_area_m2": 0.198,
            "return_finish_type": "standard_aluminum",
            "return_depth_mm": 60,
        }
    ]
    return payload


class TestIntakeV4FinishStateTruthMaterialBreakdown:
    def test_face_none_skips_vinyl_despite_stale_global_and_roll_nesting(self):
        result = build_intake_v4_material_breakdown("ws-truth-a", _payload_finish_truth_base())
        keys = {row.material_key for row in result.material_rows}
        assert "face_vinyl" not in keys
        assert "letter_face_print_vinyl" not in keys
        assert "artwork_layer-1_print_vinyl" not in keys

    def test_artwork_raw_skips_global_oracal_face_fallback(self):
        payload = _payload_finish_truth_base()
        payload["finish_setup"]["letter_group_finishes"] = []
        payload["finish_setup"]["artwork_finishes"] = [
            {
                "layer_key": "layer-1",
                "layer_name": "Logo 1",
                "execution_type": "none_raw_plexi",
                "face_personalization_method": "none_raw_plexi",
                "color_mode": "none",
                "estimated_area_m2": 0.198,
                "return_finish_type": "standard_aluminum",
                "return_depth_mm": 60,
            }
        ]
        result = build_intake_v4_material_breakdown("ws-art-raw", payload)
        names = {row.display_name for row in result.material_rows}
        op_names = {row.display_name for row in result.operation_rows}
        assert "Vinil față Oracal 651" not in names
        assert all("Serviciu aplicare — litere" != name for name in op_names)
        assert any("Plexiglas 3 mm" == name for name in names)

    def test_artwork_oracal_641_adds_logo_specific_vinyl_and_application(self):
        payload = _payload_finish_truth_base()
        payload["finish_setup"]["letter_group_finishes"] = []
        payload["finish_setup"]["artwork_finishes"] = [
            {
                "layer_key": "layer-1",
                "layer_name": "Logo 1",
                "execution_type": "cut_vinyl",
                "face_personalization_method": "oracal",
                "material_code": "ORACAL_641",
                "color_mode": "monochrome",
                "estimated_area_m2": 0.198,
                "return_finish_type": "standard_aluminum",
                "return_depth_mm": 60,
            }
        ]
        result = build_intake_v4_material_breakdown("ws-art-641", payload)
        names = {row.display_name for row in result.material_rows}
        op_names = {row.display_name for row in result.operation_rows}
        assert any(name == "Plexiglas 3 mm" for name in names)
        assert any("Vinil față Oracal 641 — Logo 1" == name for name in names)
        assert "Vinil față Oracal 651" not in names
        assert any("Serviciu aplicare — Logo 1" == name for name in op_names)

    def test_artwork_oracal_8500_adds_logo_specific_vinyl_and_application(self):
        payload = _payload_finish_truth_base()
        payload["finish_setup"]["letter_group_finishes"] = []
        payload["finish_setup"]["artwork_finishes"] = [
            {
                "layer_key": "layer-1",
                "layer_name": "Logo 1",
                "execution_type": "translucent_vinyl",
                "face_personalization_method": "oracal",
                "material_code": "ORACAL_8500",
                "color_mode": "monochrome",
                "estimated_area_m2": 0.198,
                "return_finish_type": "standard_aluminum",
                "return_depth_mm": 60,
            }
        ]
        result = build_intake_v4_material_breakdown("ws-art-8500", payload)
        names = {row.display_name for row in result.material_rows}
        op_names = {row.display_name for row in result.operation_rows}
        assert any(name == "Plexiglas 3 mm" for name in names)
        assert any("Vinil față Oracal 8500 — Logo 1" == name for name in names)
        assert "Vinil față Oracal 651" not in names
        assert any("Serviciu aplicare — Logo 1" == name for name in op_names)

    def test_artwork_print_laminate_adds_logo_specific_rows(self):
        payload = _payload_finish_truth_base()
        payload["finish_setup"]["letter_group_finishes"] = []
        payload["finish_setup"]["artwork_finishes"] = [
            {
                "layer_key": "layer-1",
                "layer_name": "Logo 1",
                "execution_type": "print_laminate",
                "face_personalization_method": "print_laminate",
                "material_code": "ORAFOL_PRINT_LAMINATION",
                "print_material_code": "ORAFOL_PRINT",
                "lamination_material_code": "ORAFOL_LAMINATION",
                "color_mode": "polychrome",
                "estimated_area_m2": 0.198,
                "return_finish_type": "standard_aluminum",
                "return_depth_mm": 60,
            }
        ]
        result = build_intake_v4_material_breakdown("ws-art-print", payload)
        names = {row.display_name for row in result.material_rows}
        op_names = {row.display_name for row in result.operation_rows}
        assert any(name == "Plexiglas 3 mm" for name in names)
        assert any("Material print Orafol — Logo 1" == name for name in names)
        assert any("Material laminare Orafol — Logo 1" == name for name in names)
        assert any("Serviciu print — Logo 1" == name for name in op_names)
        assert any("Serviciu laminare X-PRO — Logo 1" == name for name in op_names)
        assert any("Serviciu aplicare — Logo 1" == name for name in op_names)

    @pytest.mark.asyncio
    async def test_artwork_finish_totals_are_additive_relative_to_raw(self):
        def _artwork_payload(execution_type: str, face_personalization_method: str, material_code: str | None):
            payload = _payload_finish_truth_base()
            payload["finish_setup"]["letter_group_finishes"] = []
            payload["finish_setup"]["artwork_finishes"] = [
                {
                    "layer_key": "layer-1",
                    "layer_name": "Logo 1",
                    "execution_type": execution_type,
                    "face_personalization_method": face_personalization_method,
                    "material_code": material_code,
                    "print_material_code": "ORAFOL_PRINT" if execution_type == "print_laminate" else None,
                    "lamination_material_code": "ORAFOL_LAMINATION" if execution_type == "print_laminate" else None,
                    "color_mode": "polychrome" if execution_type == "print_laminate" else ("none" if execution_type == "none_raw_plexi" else "monochrome"),
                    "estimated_area_m2": 0.198,
                    "return_finish_type": "standard_aluminum",
                    "return_depth_mm": 60,
                }
            ]
            return payload

        material_prices = {
            "MAT-ACP-FATA-LITERE": {"unit_cost": 16.0, "currency": "EUR"},
            "MAT-VINYL-PRINT": {"unit_cost": 1.8, "currency": "EUR"},
            "MAT-VINYL-PRINT-LAMINATED": {"unit_cost": 12.0, "currency": "EUR"},
        }

        with patch(
            "services.inventory_materials_admin_service.load_material_pricing_dict",
            new_callable=AsyncMock,
        ) as material_lookup, patch(
            "services.workcenter_rates_service.load_workcenter_rate_pricing_dict",
            new_callable=AsyncMock,
        ) as rate_lookup:
            material_lookup.return_value = material_prices
            rate_lookup.return_value = {}

            raw = await build_intake_v4_material_breakdown_with_registry(None, "ws-art-total-raw", _artwork_payload("none_raw_plexi", "none_raw_plexi", None))  # type: ignore[arg-type]
            o641 = await build_intake_v4_material_breakdown_with_registry(None, "ws-art-total-641", _artwork_payload("cut_vinyl", "oracal", "ORACAL_641"))  # type: ignore[arg-type]
            o8500 = await build_intake_v4_material_breakdown_with_registry(None, "ws-art-total-8500", _artwork_payload("translucent_vinyl", "oracal", "ORACAL_8500"))  # type: ignore[arg-type]
            pr = await build_intake_v4_material_breakdown_with_registry(None, "ws-art-total-print", _artwork_payload("print_laminate", "print_laminate", "ORAFOL_PRINT_LAMINATION"))  # type: ignore[arg-type]

        assert raw.totals.estimated_cost_total is not None
        assert o641.totals.estimated_cost_total is not None
        assert o8500.totals.estimated_cost_total is not None
        assert pr.totals.estimated_cost_total is not None
        assert o641.totals.estimated_cost_total >= raw.totals.estimated_cost_total
        assert o8500.totals.estimated_cost_total >= raw.totals.estimated_cost_total
        assert pr.totals.estimated_cost_total >= raw.totals.estimated_cost_total

    def test_standard_aluminum_return_label_not_oracal_wrapped(self):
        result = build_intake_v4_material_breakdown("ws-truth-e", _payload_finish_truth_base())
        ret = next(row for row in result.material_rows if row.material_key == "return_material")
        assert "Argintiu" in ret.display_name
        assert "oracal_wrapped" not in ret.display_name
        assert "Cant / volum" in ret.display_name

    def test_artwork_needs_decision_emits_pending_warning(self):
        result = build_intake_v4_material_breakdown("ws-truth-art", _payload_finish_truth_base())
        assert any(w.code == "artwork_execution_pending" for w in result.warnings)

    def test_face_oracal_group_produces_vinyl(self):
        payload = _payload_finish_truth_base()
        payload["finish_setup"]["letter_group_finishes"][0]["face_finish_type"] = "oracal_651"
        result = build_intake_v4_material_breakdown("ws-truth-b", payload)
        assert any(row.material_key == "face_vinyl_651" for row in result.material_rows)

    def test_oracal_wrapped_return_label(self):
        payload = _payload_finish_truth_base()
        for group in payload["finish_setup"]["letter_group_finishes"]:
            group["return_finish_type"] = "oracal_wrapped"
        payload["finish_setup"]["artwork_finishes"][0]["return_finish_type"] = "oracal_wrapped"
        result = build_intake_v4_material_breakdown("ws-truth-d", payload)
        ret = next(row for row in result.material_rows if row.material_key == "return_material")
        assert "Oracal 651" in ret.display_name
        assert "oracal_wrapped" not in ret.display_name
        assert "Cant / volum" in ret.display_name
        assert "+ artwork" in ret.display_name


def _payload_ana_maria_sheet_floor() -> dict:
    """Synthetic Ana Maria–like: nesting footprint below letter-group face area sum."""
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
                        "usedSheetAreaSqm": 6.0,
                        "efficiencyPercent": 19.0,
                        "placedItemsCount": 19,
                        "unplacedItemsCount": 0,
                        "placements": [
                            {
                                "partId": f"part-{index}",
                                "sourceLayerName": "pseudo maria (blue)",
                                "placedWidthMm": 200 + index,
                                "placedHeightMm": 150 + index,
                            }
                            for index in range(19)
                        ],
                    }
                ]
            },
            "layers": [
                {"id": "pseudo:maria", "name": "pseudo maria (blue)", "filledAreaSqm": 0.281},
                {"id": "pseudo:soare", "name": "pseudo soare (red)", "filledAreaSqm": 0.3071},
                {"id": "pseudo:ana", "name": "pseudo ana (green)", "filledAreaSqm": 0.1964},
                {"id": "pseudo:gradinita", "name": "pseudo gradinita (orange)", "filledAreaSqm": 0.4792},
            ],
            "parts": {
                "items": [
                    {
                        "id": f"part-{index}",
                        "source": {"layerId": "pseudo:maria", "layerName": "pseudo maria (blue)"},
                    }
                    for index in range(19)
                ]
            },
        },
        "quote_geometry": {
            "face_area_m2": 1.2638,
            "letter_return_perimeter_ml": 25.0188,
            "artwork_return_perimeter_ml": 4.891,
            "return_material_perimeter_ml": 29.9098,
        },
        "path_geometry_summary": {
            "parse_status": "parsed",
            "face_area_m2": 1.2638,
            "return_material_perimeter_ml": 29.9098,
        },
        "finish_setup": {
            "face_finish_type": "none",
            "return_finish_type": "white_aluminum",
            "return_depth_mm": 60,
            "illuminated": True,
            "backing_mode": "forex_10_with_bevel",
            "letter_group_finishes": [
                {"group_key": "pseudo:maria", "layer_name": "pseudo maria (blue)", "face_area_m2": 0.281, "return_finish_type": "white_aluminum", "perimeter_m": 6.2547},
                {"group_key": "pseudo:soare", "layer_name": "pseudo soare (red)", "face_area_m2": 0.3071, "return_finish_type": "white_aluminum", "perimeter_m": 6.7547},
                {"group_key": "pseudo:ana", "layer_name": "pseudo ana (green)", "face_area_m2": 0.1964, "return_finish_type": "white_aluminum", "perimeter_m": 6.0047},
                {"group_key": "pseudo:gradinita", "layer_name": "pseudo gradinita (orange)", "face_area_m2": 0.4792, "return_finish_type": "white_aluminum", "perimeter_m": 6.0047},
            ],
            "artwork_finishes": [
                {
                    "layer_key": "logo-stanga",
                    "layer_name": "logo stanga",
                    "execution_type": "needs_decision",
                    "estimated_area_m2": 1.5608,
                    "return_finish_type": "white_aluminum",
                    "return_depth_mm": 60,
                },
                {
                    "layer_key": "logo-dreapta",
                    "layer_name": "logo dreapta",
                    "execution_type": "needs_decision",
                    "estimated_area_m2": 1.5608,
                    "return_finish_type": "white_aluminum",
                    "return_depth_mm": 60,
                },
            ],
            "confirmed": True,
        },
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {"layer_key": "pseudo:maria", "layer_name": "pseudo maria (blue)", "confirmed_role": "face", "confirmation_state": "confirmed"},
                {"layer_key": "pseudo:soare", "layer_name": "pseudo soare (red)", "confirmed_role": "face", "confirmation_state": "confirmed"},
                {"layer_key": "pseudo:ana", "layer_name": "pseudo ana (green)", "confirmed_role": "face", "confirmation_state": "confirmed"},
                {"layer_key": "pseudo:gradinita", "layer_name": "pseudo gradinita (orange)", "confirmed_role": "face", "confirmation_state": "confirmed"},
                {"layer_key": "logo-stanga", "layer_name": "logo stanga", "confirmed_role": "printed_artwork", "confirmation_state": "confirmed"},
                {"layer_key": "logo-dreapta", "layer_name": "logo dreapta", "confirmed_role": "printed_artwork", "confirmation_state": "confirmed"},
            ],
        },
    }


class TestIntakeV4SheetNestingQuantityFloor:
    def test_plexiglas_not_below_eligible_face_area_sum(self):
        result = build_intake_v4_material_breakdown("ws-ana-floor", _payload_ana_maria_sheet_floor())
        plexi = next(row for row in result.material_rows if row.material_key == "plexiglas_face")
        assert plexi.quantity >= 1.2637
        assert any(w.code == "sheet_nesting_quantity_floor_applied" for w in result.warnings)

    def test_forex_backing_fallback_not_below_corrected_face_area(self):
        result = build_intake_v4_material_breakdown("ws-ana-backing", _payload_ana_maria_sheet_floor())
        forex = next(row for row in result.material_rows if row.material_key == "forex_backing")
        plexi = next(row for row in result.material_rows if row.material_key == "plexiglas_face")
        assert forex.quantity >= plexi.quantity
        assert forex.quantity >= 1.2637
        assert any(w.code == "backing_area_fallback_used" for w in result.warnings)

    def test_cant_label_includes_cant_active_artwork(self):
        result = build_intake_v4_material_breakdown("ws-ana-cant", _payload_ana_maria_sheet_floor())
        ret = next(row for row in result.material_rows if row.material_key == "return_material")
        assert "+ artwork" in ret.display_name

    def test_pbl_like_floor_raises_below_geometry_face_area(self):
        payload = _payload_with_letter_groups(roll_nesting=False, sheet_nesting=True)
        payload["svg_analysis_json"]["nesting"]["sheets"] = [
            {
                "configId": "sheet_3000x2000",
                "sheetsUsed": 1,
                "usedSheetAreaSqm": 6.0,
                "placedItemsCount": 10,
                "unplacedItemsCount": 0,
                "placements": [
                    {"partId": f"p{i}", "sourceLayerName": "litere-volumetrice-1", "placedWidthMm": 200, "placedHeightMm": 150}
                    for i in range(10)
                ],
            }
        ]
        payload["svg_analysis_json"]["parts"] = {
            "items": [
                {"id": f"p{i}", "source": {"layerId": "litere-volumetrice-1", "layerName": "litere-volumetrice-1"}}
                for i in range(10)
            ]
        }
        payload["layer_role_setup"] = {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "litere-volumetrice-1",
                    "layer_name": "litere-volumetrice-1",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                },
            ],
        }
        result = build_intake_v4_material_breakdown("ws-pbl-floor", payload)
        plexi = next(row for row in result.material_rows if row.material_key == "plexiglas_face")
        assert plexi.quantity == 1.5
