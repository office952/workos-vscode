"""Intake V4 nesting material precision — sheet role split and roll estimates."""

from __future__ import annotations

from services.intake_v4_nesting_material_precision import (
    BASIS_SHEET_NESTING_PART_KIND,
    BASIS_SHEET_NESTING_PRORATED_FALLBACK,
    BASIS_SHEET_NESTING_ROLE_SPLIT,
    CONFIDENCE_NESTING_HIGH,
    SheetNestingMaterialSplit,
    apply_sheet_material_quantity_floor,
    compute_eligible_sheet_face_area_sum_sqm,
    compute_roll_nesting_vinyl_estimate,
    compute_sheet_nesting_material_split,
)


def _sheet_nesting_with_placements(*, include_backing_part_kind: bool = True) -> dict:
    placements = [
        {
            "partId": "letter-face-a",
            "sourceLayerName": "litere-volumetrice-1",
            "placedWidthMm": 800,
            "placedHeightMm": 500,
        },
    ]
    parts_items = [
        {
            "id": "letter-face-a",
            "derivedPartKind": None,
            "source": {"layerId": "litere-volumetrice-1", "layerName": "litere-volumetrice-1"},
        },
    ]
    if include_backing_part_kind:
        placements.append(
            {
                "partId": "letter-back-a",
                "sourceLayerName": "litere-backing",
                "placedWidthMm": 400,
                "placedHeightMm": 400,
            }
        )
        parts_items.append(
            {
                "id": "letter-back-a",
                "derivedPartKind": "back-cover-plate",
                "materialLabel": "Forex 3mm capac spate",
                "source": {"layerId": "litere-backing", "layerName": "litere-backing"},
            }
        )

    return {
        "sheets": [
            {
                "configId": "sheet_1300x900",
                "sheetsUsed": 2,
                "usedSheetAreaSqm": 2.34,
                "placedItemsCount": len(placements),
                "unplacedItemsCount": 0,
                "placements": placements,
            }
        ],
        "parts_items": parts_items,
    }


def _layer_roles(*, include_backing: bool = True) -> dict:
    layers = [
        {
            "layer_key": "litere-volumetrice-1",
            "layer_name": "litere-volumetrice-1",
            "confirmed_role": "face",
            "confirmation_state": "confirmed",
        },
    ]
    if include_backing:
        layers.append(
            {
                "layer_key": "litere-backing",
                "layer_name": "litere-backing",
                "confirmed_role": "backing",
                "confirmation_state": "confirmed",
            }
        )
    return {"confirmation_status": "complete", "layers": layers}


class TestSheetNestingRoleSplit:
    def test_role_split_when_placements_have_face_and_backing_metadata(self):
        nesting_bundle = _sheet_nesting_with_placements()
        analysis = {"parts": {"items": nesting_bundle["parts_items"]}}
        split = compute_sheet_nesting_material_split(
            {"sheets": nesting_bundle["sheets"]},
            analysis,
            _layer_roles(),
            face_area=1.5,
            backing_area=1.2,
        )
        assert split.mode in {"role_split", "part_kind"}
        assert split.quantity_basis in {BASIS_SHEET_NESTING_ROLE_SPLIT, BASIS_SHEET_NESTING_PART_KIND}
        assert split.face_area_sqm is not None and split.backing_area_sqm is not None
        # Placement footprint (800×500mm + 400×400mm), not full sheet stock area.
        assert round(split.face_area_sqm + split.backing_area_sqm, 4) == 0.56
        assert split.used_sheet_area_sqm == 2.34
        prorata_face = round(2.34 * 1.5 / 2.7, 4)
        assert split.face_area_sqm != prorata_face

    def test_prorated_fallback_without_placements(self):
        nesting = {
            "sheets": [
                {
                    "configId": "sheet_1300x900",
                    "sheetsUsed": 2,
                    "usedSheetAreaSqm": 2.34,
                    "placedItemsCount": 4,
                    "unplacedItemsCount": 0,
                }
            ]
        }
        split = compute_sheet_nesting_material_split(
            nesting,
            {},
            _layer_roles(),
            face_area=1.5,
            backing_area=1.2,
        )
        assert split.mode == "prorated_fallback"
        assert split.quantity_basis == BASIS_SHEET_NESTING_PRORATED_FALLBACK
        assert split.face_area_sqm == round(2.34 * 1.5 / 2.7, 4)

    def test_partial_split_when_one_placement_unclassified(self):
        nesting_bundle = _sheet_nesting_with_placements(include_backing_part_kind=False)
        nesting_bundle["sheets"][0]["placements"].append(
            {
                "partId": "unknown-part",
                "sourceLayerName": "misc",
                "placedWidthMm": 300,
                "placedHeightMm": 300,
            }
        )
        nesting_bundle["sheets"][0]["placedItemsCount"] = 2
        analysis = {"parts": {"items": nesting_bundle["parts_items"]}}
        split = compute_sheet_nesting_material_split(
            {"sheets": nesting_bundle["sheets"]},
            analysis,
            _layer_roles(include_backing=False),
            face_area=1.0,
            backing_area=0.8,
        )
        assert split.mode == "partial_role_split"
        assert split.unclassified_placements == 1


class TestRollNestingVinylEstimate:
    def test_sums_jobs_and_tracks_colors(self):
        nesting = {
            "rolls": [
                {
                    "rollWidthMm": 1000,
                    "jobs": [
                        {
                            "colorKey": "651-green",
                            "usedRollAreaSqm": 4.0,
                            "placedItemsCount": 2,
                            "unplacedItemsCount": 0,
                        },
                        {
                            "colorKey": "651-red",
                            "usedRollAreaSqm": 3.0,
                            "placedItemsCount": 1,
                            "unplacedItemsCount": 0,
                        },
                    ],
                }
            ]
        }
        estimate = compute_roll_nesting_vinyl_estimate(nesting)
        assert estimate.area_sqm == 7.0
        assert estimate.fully_valid is True
        assert len(estimate.color_keys) == 2

    def test_invalid_when_unplaced(self):
        nesting = {
            "rolls": [
                {
                    "rollWidthMm": 1000,
                    "jobs": [
                        {
                            "usedRollAreaSqm": 2.0,
                            "placedItemsCount": 1,
                            "unplacedItemsCount": 1,
                        }
                    ],
                }
            ]
        }
        estimate = compute_roll_nesting_vinyl_estimate(nesting)
        assert estimate.area_sqm == 2.0
        assert estimate.fully_valid is False

    def test_picks_best_roll_width_per_layer_not_sum_alternatives(self):
        nesting = {
            "rolls": [
                {
                    "rollWidthMm": 1000,
                    "jobs": [
                        {
                            "sourceLayerName": "face-a",
                            "colorKey": "#009846",
                            "usedRollAreaSqm": 0.54,
                            "placedItemsCount": 5,
                        }
                    ],
                },
                {
                    "rollWidthMm": 1260,
                    "jobs": [
                        {
                            "sourceLayerName": "face-a",
                            "colorKey": "#009846",
                            "usedRollAreaSqm": 0.50,
                            "placedItemsCount": 5,
                        }
                    ],
                },
            ]
        }
        layer_roles = {
            "layers": [
                {"layer_key": "face-a", "layer_name": "face-a", "confirmed_role": "face", "confirmation_state": "confirmed"},
            ]
        }
        estimate = compute_roll_nesting_vinyl_estimate(nesting, layer_role_setup=layer_roles)
        assert estimate.area_sqm == 0.5
        assert estimate.job_count == 1

    def test_excludes_printed_artwork_from_face_vinyl_roll_sum(self):
        nesting = {
            "rolls": [
                {
                    "rollWidthMm": 1000,
                    "jobs": [
                        {
                            "sourceLayerName": "artwork",
                            "usedRollAreaSqm": 0.33,
                            "placedItemsCount": 1,
                        },
                        {
                            "sourceLayerName": "face-a",
                            "colorKey": "#009846",
                            "usedRollAreaSqm": 0.51,
                            "placedItemsCount": 5,
                        },
                    ],
                }
            ]
        }
        layer_roles = {
            "layers": [
                {"layer_key": "artwork", "layer_name": "artwork", "confirmed_role": "printed_artwork", "confirmation_state": "confirmed"},
                {"layer_key": "face-a", "layer_name": "face-a", "confirmed_role": "face", "confirmation_state": "confirmed"},
            ]
        }
        estimate = compute_roll_nesting_vinyl_estimate(nesting, layer_role_setup=layer_roles)
        assert estimate.area_sqm == 0.51


class TestAcmSupportExcludedFromVlSheets:
    def test_support_panel_does_not_enter_face_or_backing_split(self):
        nesting = {
            "sheets": [
                {
                    "configId": "sheet_3000x1500",
                    "sheetsUsed": 1,
                    "usedSheetAreaSqm": 4.5,
                    "placedItemsCount": 2,
                    "unplacedItemsCount": 0,
                    "placements": [
                        {
                            "partId": "letter-face",
                            "sourceLayerName": "Litere",
                            "placedWidthMm": 700,
                            "placedHeightMm": 470,
                        },
                        {
                            "partId": "acm-bond",
                            "sourceLayerName": "Alucobond",
                            "placedWidthMm": 2000,
                            "placedHeightMm": 500,
                        },
                    ],
                }
            ]
        }
        analysis = {
            "parts": {
                "items": [
                    {
                        "id": "letter-face",
                        "source": {"layerId": "Litere", "layerName": "Litere"},
                    },
                    {
                        "id": "acm-bond",
                        "source": {"layerId": "Alucobond", "layerName": "Alucobond"},
                    },
                ]
            }
        }
        roles = {
            "layers": [
                {
                    "layer_key": "Litere",
                    "layer_name": "Litere",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                },
                {
                    "layer_key": "Alucobond",
                    "layer_name": "Alucobond",
                    "confirmed_role": "support_panel",
                    "confirmation_state": "confirmed",
                },
            ]
        }
        split = compute_sheet_nesting_material_split(
            nesting,
            analysis,
            roles,
            face_area=0.33,
            backing_area=None,
        )
        assert split.mode == "single_face"
        assert split.face_area_sqm == round((700 * 470) / 1_000_000, 4)
        assert split.face_area_sqm < 1.0
        assert split.backing_area_sqm is None

    def test_prorated_fallback_caps_full_sheet_to_letter_geometry(self):
        # Only ACM support placements → excluded → total_pl=0 → prorated fallback path.
        nesting = {
            "sheets": [
                {
                    "configId": "sheet_3000x1500",
                    "sheetsUsed": 1,
                    "usedSheetAreaSqm": 4.5,
                    "placedItemsCount": 1,
                    "unplacedItemsCount": 0,
                    "placements": [
                        {
                            "partId": "acm-only",
                            "sourceLayerName": "Alucobond",
                            "placedWidthMm": 2000,
                            "placedHeightMm": 500,
                        }
                    ],
                }
            ]
        }
        analysis = {
            "parts": {
                "items": [
                    {
                        "id": "acm-only",
                        "source": {"layerId": "Alucobond", "layerName": "Alucobond"},
                    }
                ]
            }
        }
        roles = {
            "layers": [
                {
                    "layer_key": "Alucobond",
                    "layer_name": "Alucobond",
                    "confirmed_role": "support_panel",
                    "confirmation_state": "confirmed",
                }
            ]
        }
        split = compute_sheet_nesting_material_split(
            nesting,
            analysis,
            roles,
            face_area=0.3298,
            backing_area=None,
        )
        assert split.mode == "prorated_fallback"
        assert split.face_area_sqm == 0.3298
        assert split.face_area_sqm != 4.5


class TestSheetNestingQuantityFloor:
    def test_raises_face_quantity_when_placement_footprint_below_eligible_area(self):
        nesting = {
            "sheets": [
                {
                    "configId": "sheet_3000x2000",
                    "sheetsUsed": 1,
                    "usedSheetAreaSqm": 6.0,
                    "efficiencyPercent": 19.0,
                    "placedItemsCount": 2,
                    "placements": [
                        {"partId": "f1", "sourceLayerName": "L1", "placedWidthMm": 700, "placedHeightMm": 820},
                    ],
                }
            ]
        }
        analysis = {
            "parts": {"items": [{"id": "f1", "source": {"layerId": "L1", "layerName": "L1"}}]},
            "layers": [{"id": "L1", "name": "L1", "filledAreaSqm": 1.2638}],
        }
        roles = {
            "layers": [
                {"layer_key": "L1", "layer_name": "L1", "confirmed_role": "face", "confirmation_state": "confirmed"},
            ]
        }
        split = compute_sheet_nesting_material_split(nesting, analysis, roles, face_area=1.2638, backing_area=None)
        assert split.face_area_sqm == 0.574
        eligible = compute_eligible_sheet_face_area_sum_sqm(
            analysis,
            roles,
            letter_groups=[{"group_key": "L1", "layer_name": "L1", "face_area_m2": 1.2638}],
        )
        assert eligible == 1.2638
        floored, applied = apply_sheet_material_quantity_floor(split, eligible_face_area_sqm=eligible)
        assert applied is True
        assert floored.face_area_sqm == 1.2638

    def test_no_floor_when_nesting_meets_eligible_area(self):
        split = SheetNestingMaterialSplit(
            face_area_sqm=0.69,
            backing_area_sqm=None,
            config_id="sheet_3000x2000",
            fully_valid=True,
            mode="single_face",
            quantity_basis=BASIS_SHEET_NESTING_ROLE_SPLIT,
            confidence=CONFIDENCE_NESTING_HIGH,
        )
        floored, applied = apply_sheet_material_quantity_floor(split, eligible_face_area_sqm=0.69)
        assert applied is False
        assert floored.face_area_sqm == 0.69


class TestSheetNestingPlacementFootprint:
    def test_single_face_uses_placement_area_not_full_sheet_stock(self):
        nesting = {
            "sheets": [
                {
                    "configId": "sheet_3000x2000",
                    "sheetsUsed": 1,
                    "usedSheetAreaSqm": 6.0,
                    "efficiencyPercent": 13.0,
                    "placedItemsCount": 2,
                    "placements": [
                        {"partId": "f1", "sourceLayerName": "L2", "placedWidthMm": 500, "placedHeightMm": 400},
                        {"partId": "a1", "sourceLayerName": "L1", "placedWidthMm": 300, "placedHeightMm": 200},
                    ],
                }
            ]
        }
        analysis = {
            "parts": {
                "items": [
                    {"id": "f1", "source": {"layerId": "L2", "layerName": "L2"}},
                    {"id": "a1", "source": {"layerId": "L1", "layerName": "L1"}},
                ]
            }
        }
        roles = {
            "layers": [
                {"layer_key": "L1", "layer_name": "L1", "confirmed_role": "printed_artwork", "confirmation_state": "confirmed"},
                {"layer_key": "L2", "layer_name": "L2", "confirmed_role": "face", "confirmation_state": "confirmed"},
            ]
        }
        split = compute_sheet_nesting_material_split(nesting, analysis, roles, face_area=0.69, backing_area=None)
        assert split.mode == "single_face"
        assert split.face_area_sqm == round((500 * 400) / 1_000_000, 4)
        assert split.face_area_sqm == 0.2
        assert split.face_area_sqm != 4.4822
        assert split.used_sheet_area_sqm == 6.0
        floored, applied = apply_sheet_material_quantity_floor(split, eligible_face_area_sqm=0.69)
        assert applied is True
        assert floored.face_area_sqm == 0.69


class TestOrphanDefsSplitExclusion:
    def test_unassigned_split_layer_parts_excluded_from_face_footprint(self):
        nesting = {
            "sheets": [
                {
                    "configId": "sheet_3000x2000",
                    "sheetsUsed": 1,
                    "usedSheetAreaSqm": 6.0,
                    "usedWidthMm": 1974.28,
                    "consumedLengthMm": 2714.92,
                    "placedItemsCount": 3,
                    "placements": [
                        {
                            "partId": "split_layer_1_1",
                            "placedWidthMm": 600,
                            "placedHeightMm": 600,
                        },
                        {
                            "partId": "face-a",
                            "sourceLayerName": "gradinita",
                            "placedWidthMm": 500,
                            "placedHeightMm": 400,
                        },
                    ],
                }
            ]
        }
        analysis = {
            "parts": {
                "items": [
                    {"id": "split_layer_1_1"},
                    {
                        "id": "face-a",
                        "source": {"layerId": "gradinita", "layerName": "gradinita"},
                    },
                ]
            }
        }
        roles = {
            "layers": [
                {
                    "layer_key": "gradinita",
                    "layer_name": "gradinita",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                },
            ]
        }
        split = compute_sheet_nesting_material_split(nesting, analysis, roles, face_area=1.0, backing_area=None)
        assert split.face_area_sqm == 0.2
        assert split.unclassified_placements == 0

    def test_compute_sheet_quote_material_candidates_reports_orphans_and_selected_floor(self):
        from services.intake_v4_nesting_material_precision import compute_sheet_quote_material_candidates

        nesting = {
            "sheets": [
                {
                    "configId": "sheet_3000x2000",
                    "sheetsUsed": 1,
                    "usedSheetAreaSqm": 6.0,
                    "usedWidthMm": 1974.28,
                    "consumedLengthMm": 2714.92,
                    "placements": [
                        {"partId": "split_layer_1_1", "placedWidthMm": 600, "placedHeightMm": 600},
                        {"partId": "face-a", "sourceLayerName": "L1", "placedWidthMm": 500, "placedHeightMm": 400},
                    ],
                }
            ]
        }
        analysis = {
            "parts": {
                "items": [
                    {"id": "split_layer_1_1"},
                    {"id": "face-a", "source": {"layerId": "L1", "layerName": "L1"}},
                ]
            }
        }
        roles = {
            "layers": [
                {"layer_key": "L1", "layer_name": "L1", "confirmed_role": "face", "confirmation_state": "confirmed"},
            ]
        }
        pre_floor = compute_sheet_nesting_material_split(nesting, analysis, roles, face_area=1.2638, backing_area=None)
        floored, applied = apply_sheet_material_quantity_floor(pre_floor, eligible_face_area_sqm=1.2638)
        candidates = compute_sheet_quote_material_candidates(
            nesting,
            analysis,
            roles,
            eligible_face_area_sqm=1.2638,
            sheet_split_pre_floor=pre_floor,
            selected_quote_sheet_area_sqm=floored.face_area_sqm,
            sheet_quantity_floor_applied=applied,
        )
        assert candidates is not None
        assert candidates.placement_footprint_face_sqm == 0.2
        assert candidates.orphan_defs_split_placement_sqm == 0.36
        assert candidates.selected_quote_sheet_area_sqm == 1.2638
        assert candidates.selected_quote_sheet_area_source == "eligible_area_floor"
        assert candidates.layout_occupied_area_sqm == round(1974.28 * 2714.92 / 1_000_000, 4)
