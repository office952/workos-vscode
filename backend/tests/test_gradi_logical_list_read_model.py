from __future__ import annotations

from types import SimpleNamespace

import pytest

from services.gradi_logical_list_read_model_service import build_gradi_logical_list_read_model_from_runtime


def _row(key: str, label: str, quantity: float, unit: str, cost: float, **extra):
    return SimpleNamespace(
        material_key=key,
        key=key,
        display_name=label,
        quantity=quantity,
        unit=unit,
        estimated_cost=cost,
        material_cost=cost,
        currency="EUR",
        price_source=extra.get("price_source", "pricing_registry"),
        pricing_status=extra.get("pricing_status"),
        quantity_basis=extra.get("quantity_basis"),
        quantity_source=extra.get("quantity_source"),
        source_part_ids=extra.get("source_part_ids"),
        trace_markers=extra.get("trace_markers"),
        basis_label=extra.get("basis_label"),
        operation_type=extra.get("operation_type"),
    )


def _payload(*, selected_psu_watts: int = 100) -> dict:
    return {
        "svg_source": {"file_name": "gradi-curat.svg"},
        "svg_analysis_json": {
            "nesting": {
                "rolls": [
                    {
                        "configId": "vinyl_roll_1000",
                        "rollWidthMm": 1000,
                        "jobs": [
                            {"sourceLayerName": "pseudo:maria", "colorKey": "651-053", "usedRollAreaSqm": 0.45, "placedItemsCount": 1, "unplacedItemsCount": 0},
                            {"sourceLayerName": "pseudo:soare", "colorKey": "651-047", "usedRollAreaSqm": 0.35, "placedItemsCount": 1, "unplacedItemsCount": 0},
                            {"sourceLayerName": "pseudo:gradinita", "colorKey": "641-010", "usedRollAreaSqm": 0.6009, "placedItemsCount": 1, "unplacedItemsCount": 0},
                        ],
                    }
                ]
            },
            "layers": [
                {"id": "pseudo:maria", "name": "pseudo:maria", "filledAreaSqm": 0.4},
                {"id": "pseudo:soare", "name": "pseudo:soare", "filledAreaSqm": 0.3},
                {"id": "pseudo:gradinita", "name": "pseudo:gradinita", "filledAreaSqm": 0.6009},
                {"id": "pseudo:ana", "name": "pseudo:ana", "filledAreaSqm": 0.1964},
                {"id": "logo-stanga", "name": "Logo 1", "filledAreaSqm": 0.4002},
                {"id": "logo-dreapta", "name": "Logo 2", "filledAreaSqm": 0.4002},
            ],
            "parts": {
                "items": [
                    {"id": "part_logo_1_001", "source": {"layerId": "logo-stanga", "layerName": "Logo 1"}},
                    {"id": "part_logo_2_002", "source": {"layerId": "logo-dreapta", "layerName": "Logo 2"}},
                ]
            },
        },
        "layer_role_setup": {
            "layers": [
                {"layerKey": "pseudo:maria", "layerName": "pseudo:maria", "confirmedRole": "face"},
                {"layerKey": "pseudo:soare", "layerName": "pseudo:soare", "confirmedRole": "face"},
                {"layerKey": "pseudo:gradinita", "layerName": "pseudo:gradinita", "confirmedRole": "face"},
                {"layerKey": "pseudo:ana", "layerName": "pseudo:ana", "confirmedRole": "face"},
                {"layerKey": "logo-stanga", "layerName": "Logo 1", "confirmedRole": "printed_artwork"},
                {"layerKey": "logo-dreapta", "layerName": "Logo 2", "confirmedRole": "printed_artwork"},
            ]
        },
        "quote_geometry": {
            "artwork_area_m2": 0.8005,
            "artwork_boxes": [
                {"layer_key": "logo-stanga", "layer_name": "Logo 1", "width_mm": 667.2126344054284, "height_mm": 599.8535337617757, "area_m2": 0.4002},
                {"layer_key": "logo-dreapta", "layer_name": "Logo 2", "width_mm": 667.2126344054288, "height_mm": 599.8535337617757, "area_m2": 0.4002},
            ],
        },
        "finish_setup": {
            "required_psu_watts": 140.4,
            "selected_psu_watts": selected_psu_watts,
            "psu_configuration": [160],
            "backing_mode": "forex_10_no_bevel",
            "letter_group_finishes": [
                {"group_key": "pseudo:maria", "layer_name": "pseudo:maria", "face_finish_type": "oracal_651", "face_oracal_code": "053", "face_oracal_name": "Light blue", "face_vinyl_roll_width_mm": 1000},
                {"group_key": "pseudo:soare", "layer_name": "pseudo:soare", "face_finish_type": "oracal_651", "face_oracal_code": "047", "face_oracal_name": "Orange red", "face_vinyl_roll_width_mm": 1000},
                {"group_key": "pseudo:gradinita", "layer_name": "pseudo:gradinita", "face_finish_type": "oracal_641", "face_oracal_code": "010", "face_oracal_name": "White", "face_vinyl_roll_width_mm": 1000},
                {"group_key": "pseudo:ana", "face_finish_type": "print_laminate"},
            ],
            "artwork_finishes": [
                {"layer_key": "logo-stanga", "face_personalization_method": "print_laminate"},
                {"layer_key": "logo-dreapta", "face_personalization_method": "print_laminate"},
            ],
        },
        "product_composition_recommendation": {
            "composition_type": "letters_plus_logo",
            "recommended_templates": [
                {"template_code": "TPL-VOLUMETRIC-LETTERS_v2", "role_in_composition": "letters"},
                {"template_code": "TPL-VOLUMETRIC-LOGO_v1", "role_in_composition": "logo_vector_atipic"},
            ],
            "composition_items": [
                {"composition_item_id": "letters", "template_code": "TPL-VOLUMETRIC-LETTERS_v2", "component_role": "volumetric_letters", "source_layer_ids": ["pseudo:maria", "pseudo:soare", "pseudo:ana", "pseudo:gradinita"], "source_group_ids": ["pseudo:maria", "pseudo:soare", "pseudo:ana", "pseudo:gradinita"]},
                {"composition_item_id": "logo", "template_code": "TPL-VOLUMETRIC-LOGO_v1", "component_role": "volumetric_logo", "source_layer_ids": ["logo-stanga", "logo-dreapta"], "source_group_ids": ["logo-stanga", "logo-dreapta"]},
            ],
        },
    }


def _logo_only_payload() -> dict:
    return {
        "svg_source": {"file_name": "cerc100cm.svg"},
        "quote_geometry": {
            "face_area_m2": 1.0004,
            "letter_face_area_m2": 1.0004,
            "artwork_area_m2": 1.0,
            "return_material_perimeter_ml": 6.284,
            "letter_return_perimeter_ml": 3.142,
            "artwork_return_perimeter_ml": 3.142,
        },
        "layer_role_setup": {
            "layers": [
                {"layerKey": "logo-dreapta", "layerName": "Logo 1", "confirmedRole": "printed_artwork", "confirmationState": "confirmed"},
            ]
        },
        "finish_setup": {
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
        "product_composition_recommendation": {
            "composition_type": "logo_only",
            "recommended_templates": [
                {"template_code": "TPL-VOLUMETRIC-LOGO_v1", "role_in_composition": "logo_vector_atipic"}
            ],
        },
    }


def _logo_only_breakdown() -> SimpleNamespace:
    return SimpleNamespace(
        workspace_id="workspace-logo-only",
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        totals={"estimated_cost_total": 27.3112, "currency": "EUR"},
        material_rows=[
            _row(
                "plexiglas_face",
                "Plexiglas 3 mm",
                1.0004,
                "m2",
                16.0064,
                quantity_basis="artwork_box_bounding_footprint_quote_estimate",
                quantity_source="quote_geometry.artwork_boxes|bounding_box_footprint",
                source_part_ids=["art-a"],
            ),
            _row("return_material", "Cant / volum litere + artwork", 3.142, "m", 11.3112),
        ],
        consumable_rows=[],
        operation_rows=[],
        edge_cant_operation_rows=[],
        warnings=[{"code": "sheet_nesting_prorated_fallback_blocked_for_logo_only"}],
    )


def _breakdown() -> SimpleNamespace:
    return SimpleNamespace(
        workspace_id="workspace-v6",
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        totals={"estimated_cost_total": 772.92, "currency": "EUR"},
        material_rows=[
            _row("plexiglas_face", "Plexiglas 3 mm / fata litere", 1.2638, "m2", 20.2208),
            _row("forex_backing", "Forex 10 mm / spate litere", 1.2638, "m2", 20.2208),
            _row("artwork_plexiglas_logo-stanga", "Plexiglas față emblemă — Logo 1", 0.4002, "m2", 6.4032, quantity_basis="linked_logo_face_bounding_footprint_quote_estimate", quantity_source="quote_geometry.artwork_boxes|bounding_box_footprint|linked_logo_segment", source_part_ids=["part_logo_1_001"]),
            _row("artwork_plexiglas_logo-dreapta", "Plexiglas față emblemă — Logo 2", 0.4002, "m2", 6.4032, quantity_basis="linked_logo_face_bounding_footprint_quote_estimate", quantity_source="quote_geometry.artwork_boxes|bounding_box_footprint|linked_logo_segment", source_part_ids=["part_logo_2_002"]),
            _row("artwork_forex_backing_logo-stanga", "Forex backing emblemă — Logo 1", 0.4002, "m2", 6.4032, quantity_basis="linked_logo_backing_bounding_footprint_quote_estimate", quantity_source="quote_geometry.artwork_boxes|bounding_box_footprint|linked_logo_segment", source_part_ids=["part_logo_1_001"]),
            _row("artwork_forex_backing_logo-dreapta", "Forex backing emblemă — Logo 2", 0.4002, "m2", 6.4032, quantity_basis="linked_logo_backing_bounding_footprint_quote_estimate", quantity_source="quote_geometry.artwork_boxes|bounding_box_footprint|linked_logo_segment", source_part_ids=["part_logo_2_002"]),
            _row("letter_face_pseudo:ana_print_vinyl", "Material print Orafol - pseudo ana", 0.1964, "m2", 0.3534),
            _row("letter_face_pseudo:ana_laminated_vinyl", "Material laminare Orafol - pseudo ana", 0.1964, "m2", 2.356),
            _row("artwork_logo-stanga_print_vinyl", "Material print Orafol - logo stanga", 0.4002, "m2", 0.7205),
            _row("artwork_logo-stanga_laminated_vinyl", "Material laminare Orafol - logo stanga", 0.4002, "m2", 4.803),
            _row("artwork_logo-dreapta_print_vinyl", "Material print Orafol - logo dreapta", 0.4002, "m2", 0.7205),
            _row("artwork_logo-dreapta_laminated_vinyl", "Material laminare Orafol - logo dreapta", 0.4002, "m2", 4.803),
            _row("return_material", "Cant / volum litere + interioare + artwork", 31.6382, "m", 113.8974),
        ],
        consumable_rows=[
            _row("adhesive_return_to_face", "Adeziv lipire cant pe fete litere", 53.4944, "ml", 6.2935),
            _row("adhesive_led_modules", "Adeziv suplimentar module LED", 28.8, "ml", 3.3882),
            _row("wire_letters_myyup_2x075", "Cablu electric MYYUP 2 x 0.75", 19.0, "ml", 7.0784),
            _row("wire_supply_myyup_2x15", "Cablu electric MYYUP 2 x 1.5 alimentare 220V", 5.0, "ml", 3.8235),
            _row("led_modules", "Module LED", 144.0, "buc", 86.4),
            _row("led_psu", "Sursa LED 12V", 1.0, "buc", 24.0),
            _row("mounting_accessories_percent", "Accesorii montaj / conectori", 1.0, "job", 36.8058),
        ],
        operation_rows=[
            _row("cnc_face_cutting_plexiglas_3mm", "Debitare CNC fata Plexiglas", 25.0188, "ml", 37.5282),
            _row("cnc_face_bevel_plexiglas_3mm", "Sanfren CNC fata Plexiglas", 25.0188, "ml", 37.5282),
            _row("cnc_backing_cutting_forex_10mm", "Debitare CNC spate Forex", 25.0188, "ml", 187.641),
            _row("letter_face_pseudo:ana_print_service", "Serviciu print - pseudo ana", 0.2356, "m2", 2.0026),
            _row("letter_face_pseudo:ana_lamination_service", "Serviciu laminare X-PRO - pseudo ana", 0.2356, "m2", 0.4712),
            _row("letter_face_pseudo:ana_application_service", "Serviciu aplicare - pseudo ana", 0.2356, "m2", 0.7068),
            _row("artwork_logo-stanga_print_service", "Serviciu print - logo stanga", 0.4803, "m2", 4.0826),
            _row("artwork_logo-stanga_lamination_service", "Serviciu laminare X-PRO - logo stanga", 0.4803, "m2", 0.9606),
            _row("artwork_logo-stanga_application_service", "Serviciu aplicare - logo stanga", 0.4803, "m2", 1.4409),
            _row("artwork_logo-dreapta_print_service", "Serviciu print - logo dreapta", 0.4803, "m2", 4.0826),
            _row("artwork_logo-dreapta_lamination_service", "Serviciu laminare X-PRO - logo dreapta", 0.4803, "m2", 0.9606),
            _row("artwork_logo-dreapta_application_service", "Serviciu aplicare - logo dreapta", 0.4803, "m2", 1.4409),
        ],
        edge_cant_operation_rows=[
            _row("edge_cant_bond_to_face", "Lipire cant / volum pe fata litere", 31.6382, "m", 158.191),
        ],
        warnings=[{"code": "roll_nesting_color_split_missing"}, {"code": "backing_area_fallback_used"}, {"code": "linked_logo_backing_fallback_used"}],
    )


def _dry_run() -> dict:
    return {
        "workspace_id": "workspace-v6",
        "workspace_code": "IV6-TEST",
        "template_code": "TPL-VOLUMETRIC-LETTERS_v2",
        "commercial_totals": {"total_gross": 6439.08, "currency": "RON"},
        "commercial_line_items": [
            {"code": "ambalare", "owner_decision_required": True},
            {"code": "montaj", "owner_decision_required": True},
        ],
    }


def test_gradi_logical_read_model_returns_21_core_rows_and_excludes_extras() -> None:
    result = build_gradi_logical_list_read_model_from_runtime(
        workspace_payload=_payload(), material_breakdown=_breakdown(), priced_dry_run=_dry_run()
    )

    assert result["core_row_count"] == 21
    assert result["core_rows_complete"] is True
    assert {row["category"] for row in result["rows"]} == {"MATERIALE", "SERVICII_OPERATII", "MANOPERA"}
    assert {line["code"] for line in result["excluded_extra_commercial_lines"]} == {"ambalare", "montaj"}


def test_gradi_logical_read_model_builds_oracal_row_and_logo_plexi_rows_without_runtime_material_row() -> None:
    result = build_gradi_logical_list_read_model_from_runtime(
        workspace_payload=_payload(), material_breakdown=_breakdown(), priced_dry_run=_dry_run()
    )
    by_id = {row["line_id"]: row for row in result["rows"]}

    assert by_id["material.face_oracal"]["display_label"] == "Vinil fata Oracal - consum pe serii 641 + 651"
    assert by_id["material.face_oracal"]["status"] == "PARTIAL_TARIFF_CONFIRMATION_REQUIRED"
    assert by_id["material.face_oracal"]["material_code"] == "ORACAL_MULTIPLE"
    assert by_id["material.face_oracal"]["category"] == "MATERIALE"
    assert by_id["material.face_oracal"]["selected_series"] == "multiple"
    assert by_id["material.face_oracal"]["quantity"] == 1.4009
    assert by_id["material.face_oracal"]["unit"] == "m2"
    assert by_id["material.face_oracal"]["subtotal"] == 11.1059
    assert by_id["material.face_oracal"]["tariff_status"] == "MIXED_OWNER_CONFIRMED_INTERIM"
    assert by_id["material.face_oracal"]["inventory_consumption_mode"] == "split_by_series_color"
    assert by_id["material.face_oracal"]["inventory_consumption_key"] == "ORACAL_MULTIPLE"
    assert by_id["material.face_oracal"]["source_roles"] == ["LETTER_FACE"]
    assert by_id["material.face_oracal"]["affected_group_keys"] == ["pseudo:maria", "pseudo:soare", "pseudo:gradinita"]
    assert len(by_id["material.face_oracal"]["source_groups"]) == 3
    assert {row["key"] for row in by_id["material.face_oracal"]["child_rows"]} == {"face_vinyl_641", "face_vinyl_651"}
    assert {row["inventory_consumption_key"] for row in by_id["material.face_oracal"]["child_rows"]} == {"ORACAL_641", "ORACAL_651"}
    assert "ORACAL_MATERIAL_RUNTIME_ROW_MISSING" not in by_id["material.face_oracal"]["gaps"]
    assert by_id["material.logo_plexiglas_face"]["display_label"] == "Plexiglas 3 mm / embleme/logo"
    assert by_id["material.logo_plexiglas_face"]["quantity"] == pytest.approx(0.8004, rel=0, abs=1e-4)
    assert by_id["material.logo_plexiglas_face"]["material_code"] == "PLEXIGLAS_3MM"
    assert by_id["material.logo_plexiglas_face"]["nesting_group"] == "PLEXIGLAS_3MM_FACE_BATCH"
    assert by_id["material.logo_plexiglas_face"]["material_tariff_source"] == "pricing_registry"
    assert by_id["material.logo_plexiglas_face"]["status"] == "MATCHED"
    assert by_id["material.logo_plexiglas_face"]["subtotal"] == pytest.approx(12.8064, rel=0, abs=1e-4)
    assert "ORACAL_MATERIAL_RUNTIME_ROW_MISSING" not in result["warnings"]


def test_gradi_logical_read_model_shares_plexiglas_material_batch_between_letters_and_logo() -> None:
    result = build_gradi_logical_list_read_model_from_runtime(
        workspace_payload=_payload(), material_breakdown=_breakdown(), priced_dry_run=_dry_run()
    )
    by_id = {row["line_id"]: row for row in result["rows"]}

    letters = by_id["material.plexiglas_face"]
    logo = by_id["material.logo_plexiglas_face"]

    assert letters["material_code"] == "PLEXIGLAS_3MM"
    assert logo["material_code"] == "PLEXIGLAS_3MM"
    assert letters["nesting_group"] == "PLEXIGLAS_3MM_FACE_BATCH"
    assert logo["nesting_group"] == "PLEXIGLAS_3MM_FACE_BATCH"
    assert letters["material_tariff_eur_per_m2"] == logo["material_tariff_eur_per_m2"] == 16.0
    assert letters["batch_trace"]["letter_face_area_m2"] == 1.2638
    assert letters["batch_trace"]["logo_face_area_m2"] == pytest.approx(0.8004, rel=0, abs=1e-4)
    assert letters["batch_trace"]["total_face_area_m2"] == pytest.approx(2.0642, rel=0, abs=1e-4)
    assert logo["batch_roles"] == ["LOGO_FACE"]
    assert letters["batch_roles"] == ["LETTER_FACE"]


def test_gradi_logical_read_model_aggregates_split_print_lamination_application_rows() -> None:
    result = build_gradi_logical_list_read_model_from_runtime(
        workspace_payload=_payload(), material_breakdown=_breakdown(), priced_dry_run=_dry_run()
    )
    by_id = {row["line_id"]: row for row in result["rows"]}

    assert by_id["material.print"]["status"] == "SPLIT_IN_RUNTIME"
    assert len(by_id["material.print"]["child_rows"]) == 3
    assert by_id["material.lamination"]["status"] == "SPLIT_IN_RUNTIME"
    assert len(by_id["material.lamination"]["child_rows"]) == 3
    assert len(by_id["service.print"]["child_rows"]) == 3
    assert len(by_id["service.lamination"]["child_rows"]) == 3
    assert len(by_id["service.application"]["child_rows"]) == 3
    assert by_id["material.face_oracal"]["line_id"] != by_id["material.print"]["line_id"]
    assert by_id["material.face_oracal"]["line_id"] != by_id["material.lamination"]["line_id"]


def test_logo_only_runtime_does_not_emit_letters_plexiglas_logical_row() -> None:
    result = build_gradi_logical_list_read_model_from_runtime(
        workspace_payload=_logo_only_payload(), material_breakdown=_logo_only_breakdown(), priced_dry_run={"workspace_id": "workspace-logo-only", "template_code": "TPL-VOLUMETRIC-LETTERS_v2", "commercial_totals": {"total_gross": 0, "currency": "RON"}, "commercial_line_items": []}
    )
    by_id = {row["line_id"]: row for row in result["rows"]}

    assert "material.plexiglas_face" not in by_id
    assert by_id["material.logo_plexiglas_face"]["quantity"] == 1.0004
    assert by_id["material.logo_plexiglas_face"]["subtotal"] == pytest.approx(16.0064, rel=0, abs=1e-4)
    assert by_id["material.logo_plexiglas_face"]["batch_roles"] == ["LOGO_FACE"]
    assert by_id["material.logo_plexiglas_face"]["shared_batch_roles"] == ["LOGO_FACE"]


def test_logo_only_logical_rows_keep_compatible_physical_footprint_source_for_plexi_and_forex() -> None:
    breakdown = SimpleNamespace(
        workspace_id="workspace-logo-only-footprint",
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        totals={"estimated_cost_total": 79.2, "currency": "EUR"},
        material_rows=[
            _row(
                "plexiglas_face",
                "Plexiglas 3 mm",
                2.25,
                "m2",
                36.0,
                quantity_basis="artwork_box_bounding_footprint_quote_estimate",
                quantity_source="quote_geometry.artwork_boxes|bounding_box_footprint",
                source_part_ids=["art-a"],
            ),
            _row(
                "forex_backing",
                "Forex 10 mm",
                2.25,
                "m2",
                43.2,
                quantity_basis="backing_area_fallback_from_artwork_box_footprint",
                quantity_source="quote_geometry.artwork_boxes|bounding_box_footprint",
                source_part_ids=["art-a"],
            ),
        ],
        consumable_rows=[],
        operation_rows=[],
        edge_cant_operation_rows=[],
        warnings=[{"code": "backing_artwork_box_footprint_used"}],
    )

    result = build_gradi_logical_list_read_model_from_runtime(
        workspace_payload=_logo_only_payload(),
        material_breakdown=breakdown,
        priced_dry_run={"workspace_id": "workspace-logo-only", "template_code": "TPL-VOLUMETRIC-LETTERS_v2", "commercial_totals": {"total_gross": 0, "currency": "RON"}, "commercial_line_items": []},
    )
    by_id = {row["line_id"]: row for row in result["rows"]}

    logo = by_id["material.logo_plexiglas_face"]
    forex = by_id["material.forex_backing"]

    assert logo["quantity"] == pytest.approx(2.25, rel=0, abs=1e-4)
    assert logo["subtotal"] == pytest.approx(36.0, rel=0, abs=1e-4)
    assert logo["batch_trace"]["logo_face_area_m2"] == pytest.approx(2.25, rel=0, abs=1e-4)
    assert forex["quantity"] == pytest.approx(2.25, rel=0, abs=1e-4)
    assert forex["subtotal"] == pytest.approx(43.2, rel=0, abs=1e-4)
    assert logo["source_part_ids"] == ["art-a"]
    assert forex["source_part_ids"] == ["art-a"]
    child = forex["child_rows"][0]
    assert child["basis"] == "backing_area_fallback_from_artwork_box_footprint"
    assert child["source_part_ids"] == ["art-a"]


def test_gradi_linked_logo_backing_scope_adds_logo_forex_to_logical_total() -> None:
    result = build_gradi_logical_list_read_model_from_runtime(
        workspace_payload=_payload(), material_breakdown=_breakdown(), priced_dry_run=_dry_run()
    )
    by_id = {row["line_id"]: row for row in result["rows"]}

    forex = by_id["material.forex_backing"]
    assert forex["quantity"] == pytest.approx(2.0642, rel=0, abs=1e-4)
    assert forex["subtotal"] == pytest.approx(33.0272, rel=0, abs=1e-4)
    assert any(child["key"].startswith("artwork_forex_backing_") for child in forex["child_rows"])
    assert forex["warnings"] == ["LINKED_LOGO_BACKING_FALLBACK_USED"]


def test_gradi_logo_plexiglas_uses_runtime_rows_not_artwork_area_fallback() -> None:
    result = build_gradi_logical_list_read_model_from_runtime(
        workspace_payload=_payload(), material_breakdown=_breakdown(), priced_dry_run=_dry_run()
    )
    by_id = {row["line_id"]: row for row in result["rows"]}

    logo = by_id["material.logo_plexiglas_face"]
    assert logo["source_part_ids"] == ["part_logo_1_001", "part_logo_2_002"]
    assert logo["quantity"] == pytest.approx(0.8004, rel=0, abs=1e-4)
    assert logo["subtotal"] == pytest.approx(12.8064, rel=0, abs=1e-4)


def test_logo_only_logical_rows_still_expose_trace_debt_when_source_part_ids_are_missing() -> None:
    row = _logo_only_breakdown().material_rows[0]
    assert row.quantity_source == "quote_geometry.artwork_boxes|bounding_box_footprint"
    assert row.source_part_ids == ["art-a"]


def test_gradi_logical_read_model_keeps_series_breakdown_when_oracal_row_aggregates_641_and_651() -> None:
    result = build_gradi_logical_list_read_model_from_runtime(
        workspace_payload=_payload(), material_breakdown=_breakdown(), priced_dry_run=_dry_run()
    )
    oracal = {row["line_id"]: row for row in result["rows"]}["material.face_oracal"]

    assert oracal["selected_series"] == "multiple"
    breakdown = {row["series"]: row for row in oracal["series_breakdown"]}
    assert set(breakdown) == {"641", "651"}
    assert breakdown["641"]["material_code"] == "ORACAL_641"
    assert breakdown["641"]["inventory_consumption_key"] == "ORACAL_641"
    assert breakdown["641"]["tariff_eur_per_m2"] == 6.5
    assert breakdown["641"]["subtotal"] == 3.9059
    assert breakdown["641"]["color_breakdown"][0]["color_code"] == "010"
    assert breakdown["641"]["color_breakdown"][0]["inventory_consumption_key"] == "ORACAL_641_010"
    assert breakdown["651"]["material_code"] == "ORACAL_651"
    assert breakdown["651"]["inventory_consumption_key"] == "ORACAL_651"
    assert breakdown["651"]["tariff_eur_per_m2"] == 9.0
    assert breakdown["651"]["subtotal"] == 7.2
    assert {row["color_code"] for row in breakdown["651"]["color_breakdown"]} == {"047", "053"}


def test_gradi_logical_read_model_enriches_oracal_child_rows_with_registry_metadata() -> None:
    result = build_gradi_logical_list_read_model_from_runtime(
        workspace_payload=_payload(), material_breakdown=_breakdown(), priced_dry_run=_dry_run()
    )
    oracal = {row["line_id"]: row for row in result["rows"]}["material.face_oracal"]
    child_by_series = {row["series"]: row for row in oracal["child_rows"]}

    assert oracal["material_variant_code"] is None
    assert oracal["inventory_status"] == "split_by_child_rows"
    assert oracal["stock_identity_status"] == "not_required"

    assert child_by_series["641"]["material_variant_code"] == "ORACAL_641_WHITE"
    assert child_by_series["641"]["inventory_key_preview"] == "ORACAL_641_WHITE::ROLL_PENDING"
    assert child_by_series["641"]["inventory_status"] == "inventory_key_preview_ready"
    assert child_by_series["641"]["stock_identity_status"] == "roll_pending"
    assert child_by_series["641"]["material_series"] == "ORACAL_641"
    assert child_by_series["641"]["material_family"] == "VINYL"
    assert child_by_series["641"]["catalog_color_code"] == "010"
    assert child_by_series["641"]["catalog_color_name"] == "White"
    assert child_by_series["641"]["quantity"] == 0.6009
    assert child_by_series["641"]["subtotal"] == 3.9059

    assert child_by_series["651"]["material_variant_code"] == "ORACAL_651_UNKNOWN"
    assert child_by_series["651"]["inventory_key_preview"] == "ORACAL_651_UNKNOWN::ROLL_PENDING"
    assert child_by_series["651"]["inventory_status"] == "pending_catalog_model"
    assert child_by_series["651"]["stock_identity_status"] == "roll_pending"
    assert child_by_series["651"]["material_series"] == "ORACAL_651"
    assert child_by_series["651"]["material_family"] == "VINYL"
    assert child_by_series["651"]["catalog_color_code"] == "UNKNOWN"
    assert child_by_series["651"]["catalog_color_name"] == "Unknown"
    assert child_by_series["651"]["quantity"] == 0.8
    assert child_by_series["651"]["subtotal"] == 7.2

    assert child_by_series["641"]["material_variant_code"] != child_by_series["651"]["material_variant_code"]
    assert child_by_series["641"]["inventory_key_preview"].endswith("ROLL_PENDING")
    assert child_by_series["651"]["inventory_key_preview"].endswith("ROLL_PENDING")
    assert child_by_series["641"]["color_breakdown"][0]["material_variant_code"] == "ORACAL_641_WHITE"
    assert {row["material_variant_code"] for row in child_by_series["651"]["color_breakdown"]} == {"ORACAL_651_UNKNOWN"}


def test_gradi_logical_read_model_enriches_plexiglas_and_forex_rows_with_registry_metadata() -> None:
    result = build_gradi_logical_list_read_model_from_runtime(
        workspace_payload=_payload(), material_breakdown=_breakdown(), priced_dry_run=_dry_run()
    )
    by_id = {row["line_id"]: row for row in result["rows"]}

    plexi = by_id["material.plexiglas_face"]
    logo_plexi = by_id["material.logo_plexiglas_face"]
    forex = by_id["material.forex_backing"]

    assert plexi["material_variant_code"] == "PLEXIGLAS_3MM_OPAL"
    assert plexi["inventory_key_preview"] == "PLEXIGLAS_3MM_OPAL::BATCH_PENDING"
    assert plexi["inventory_status"] == "batch_missing"
    assert plexi["stock_identity_status"] == "batch_pending"
    assert plexi["material_family"] == "PLEXIGLAS"
    assert plexi["material_series"] == "PLEXIGLAS_3MM"
    assert plexi["cnc_processable"] is True
    assert "CNC_CUT_PLEXIGLAS_3MM" in plexi["compatible_cnc_operations"]
    assert "CNC_FLAT_RECESS_PLEXIGLAS_GLUE_SEAT" in plexi["compatible_cnc_operations"]
    assert "CANAL_PLAT_GHIDAJ" in plexi["compatible_cnc_operations"]

    assert logo_plexi["material_variant_code"] == "PLEXIGLAS_3MM_OPAL"
    assert logo_plexi["inventory_key_preview"] == "PLEXIGLAS_3MM_OPAL::BATCH_PENDING"
    assert logo_plexi["nesting_group"] == "PLEXIGLAS_3MM_FACE_BATCH"

    assert forex["material_variant_code"] == "FOREX_10MM_WHITE"
    assert forex["inventory_key_preview"] == "FOREX_10MM_WHITE::BATCH_PENDING"
    assert forex["inventory_status"] == "batch_missing"
    assert forex["stock_identity_status"] == "batch_pending"
    assert forex["material_family"] == "FOREX"
    assert forex["material_series"] == "FOREX_10MM"
    assert forex["cnc_processable"] is True
    assert "CNC_CUT_FOREX_10MM" in forex["compatible_cnc_operations"]
    assert "CNC_FLAT_RECESS_FOREX_BACK_SEAT" in forex["compatible_cnc_operations"]


def test_gradi_logical_read_model_handles_ral_missing_without_guessing_variant() -> None:
    payload = _payload()
    payload["finish_setup"] = {
        **payload["finish_setup"],
        "return_finish_type": "ral_paint",
        "paint_finish": "matte",
    }

    result = build_gradi_logical_list_read_model_from_runtime(
        workspace_payload=payload,
        material_breakdown=_breakdown(),
        priced_dry_run=_dry_run(),
    )
    return_row = {row["line_id"]: row for row in result["rows"]}["material.return_profile"]

    assert return_row["material_variant_code"] is None
    assert return_row["inventory_status"] == "ral_code_missing"
    assert return_row["inventory_key_preview"] is None
    assert return_row["material_family"] == "PAINT"
    assert return_row["material_series"] == "RAL_PAINT"


def test_gradi_logical_read_model_resolves_ral_variant_when_code_exists() -> None:
    payload = _payload()
    payload["finish_setup"] = {
        **payload["finish_setup"],
        "return_finish_type": "ral_paint",
        "paint_finish": "matte",
        "paint_ral_code": "7016",
        "paint_ral_name": "Anthracite grey",
    }

    result = build_gradi_logical_list_read_model_from_runtime(
        workspace_payload=payload,
        material_breakdown=_breakdown(),
        priced_dry_run=_dry_run(),
    )
    return_row = {row["line_id"]: row for row in result["rows"]}["material.return_profile"]

    assert return_row["material_variant_code"] == "RAL_7016_MATTE_PAINT"
    assert return_row["inventory_key_preview"] == "RAL_7016_MATTE_PAINT::PROCESS_PENDING"
    assert return_row["inventory_status"] == "process_pending"
    assert return_row["stock_identity_status"] == "process_pending"
    assert return_row["material_family"] == "PAINT"
    assert return_row["material_series"] == "RAL_PAINT"


def test_gradi_logical_read_model_surfaces_oracal_roll_color_split_warning_on_parent_row() -> None:
    result = build_gradi_logical_list_read_model_from_runtime(
        workspace_payload=_payload(), material_breakdown=_breakdown(), priced_dry_run=_dry_run()
    )
    oracal = {row["line_id"]: row for row in result["rows"]}["material.face_oracal"]

    assert "ORACAL_ROLL_COLOR_SPLIT_MISSING" in result["warnings"]
    assert "ORACAL_ROLL_COLOR_SPLIT_MISSING" in oracal["warnings"]


def test_gradi_logical_read_model_preserves_plexiglas_batch_and_commercial_totals_when_oracal_row_is_built() -> None:
    dry_run = _dry_run()
    result = build_gradi_logical_list_read_model_from_runtime(
        workspace_payload=_payload(), material_breakdown=_breakdown(), priced_dry_run=dry_run
    )
    by_id = {row["line_id"]: row for row in result["rows"]}

    assert result["core_row_count"] == 21
    assert by_id["material.plexiglas_face"]["material_code"] == "PLEXIGLAS_3MM"
    assert by_id["material.plexiglas_face"]["nesting_group"] == "PLEXIGLAS_3MM_FACE_BATCH"
    assert by_id["material.logo_plexiglas_face"]["nesting_group"] == "PLEXIGLAS_3MM_FACE_BATCH"
    assert result["runtime_totals"]["priced_quote_dry_run"]["total_gross"] == dry_run["commercial_totals"]["total_gross"]


def test_gradi_logical_read_model_adds_cnc_face_trace_metadata() -> None:
    result = build_gradi_logical_list_read_model_from_runtime(
        workspace_payload=_payload(), material_breakdown=_breakdown(), priced_dry_run=_dry_run()
    )
    by_id = {row["line_id"]: row for row in result["rows"]}

    face_cut = by_id["service.cnc_face"]
    face_flat = by_id["service.cnc_face_bevel"]

    assert face_cut["operation_code"] == "CNC_CUT_PLEXIGLAS_3MM"
    assert face_cut["operation_kind"] == "cut"
    assert face_cut["pass_count"] == 1
    assert face_cut["tariff_basis"] == "ml_pass"
    assert face_cut["tariff_eur_per_ml_pass"] == 1.5
    assert face_cut["status"] == "MATCHED"
    assert face_cut["runtime_source"] == "owner_confirmed_plexiglas_cut_baseline"
    assert "OWNER_TARIFF_CONFIRMATION_REQUIRED" not in face_cut["warnings"]

    assert face_flat["operation_code"] == "CNC_FLAT_RECESS_PLEXIGLAS_GLUE_SEAT"
    assert face_flat["operation_kind"] == "flat_recess"
    assert face_flat["display_label"] == "Canal plat ghidaj fata Plexiglas"
    assert face_flat["canonical_label"] == "Canal plat ghidaj fata Plexiglas"
    assert face_flat["legacy_label"] == "Sanfren CNC fata Plexiglas"
    assert "glue_seat" in face_flat["operation_semantics"]
    assert "guide_channel" in face_flat["operation_semantics"]
    assert face_flat["not_v_cut"] is True
    assert face_flat["operation_depth_mm"] == 1.0
    assert face_flat["pass_count"] == 1
    assert face_flat["tariff_eur_per_ml_pass"] == 1.5
    assert face_flat["status"] == "MATCHED"
    assert face_flat["runtime_source"] == "owner_confirmed_plexiglas_guide_channel_baseline"
    assert face_flat["future_form_field_key"] == "guide_channel_depth_mm"
    assert face_flat["future_form_field_default_mm"] == 1.0
    assert "GUIDE_CHANNEL_DEPTH_FORM_FIELD_PENDING" in face_flat["warnings"]


def test_gradi_logical_read_model_keeps_cnc_and_totals_stable_after_cnc_closeout() -> None:
    dry_run = _dry_run()
    result = build_gradi_logical_list_read_model_from_runtime(
        workspace_payload=_payload(), material_breakdown=_breakdown(), priced_dry_run=dry_run
    )
    by_id = {row["line_id"]: row for row in result["rows"]}

    assert result["core_row_count"] == 21
    assert by_id["service.cnc_back"]["cut_passes"] == 3
    assert by_id["service.cnc_back"]["flat_recess_passes"] == 0
    assert by_id["service.cnc_back"]["total_effective_passes"] == 3
    assert result["runtime_totals"]["priced_quote_dry_run"]["total_gross"] == dry_run["commercial_totals"]["total_gross"]


def test_gradi_logical_read_model_adds_forex_back_trace_metadata() -> None:
    result = build_gradi_logical_list_read_model_from_runtime(
        workspace_payload=_payload(), material_breakdown=_breakdown(), priced_dry_run=_dry_run()
    )
    cnc_back = {row["line_id"]: row for row in result["rows"]}["service.cnc_back"]

    assert cnc_back["operation_code"] == "CNC_CUT_FOREX_10MM"
    assert cnc_back["cut_passes"] == 3
    assert cnc_back["flat_recess_passes"] == 0
    assert cnc_back["total_effective_passes"] == 3
    assert cnc_back["pass_count"] == 3
    assert cnc_back["tariff_eur_per_ml_pass"] == 1.5
    assert len(cnc_back["trace_breakdown"]) == 1
    assert cnc_back["trace_breakdown"][0]["operation_code"] == "CNC_CUT_FOREX_10MM"


def test_gradi_logical_read_model_uses_geometry_fallback_for_cnc_trace_when_operation_rows_missing() -> None:
    breakdown = _breakdown()
    breakdown.operation_rows = []
    payload = _payload()
    payload["quote_geometry"] = {
        **payload["quote_geometry"],
        "face_cutting_perimeter_ml": 25.0188,
        "cnc_cutting_perimeter_ml": 25.0188,
    }

    result = build_gradi_logical_list_read_model_from_runtime(
        workspace_payload=payload,
        material_breakdown=breakdown,
        priced_dry_run=_dry_run(),
    )
    by_id = {row["line_id"]: row for row in result["rows"]}

    assert by_id["service.cnc_face"]["quantity"] == 25.0188
    assert by_id["service.cnc_face"]["subtotal"] == 37.5282
    assert by_id["service.cnc_face_bevel"]["quantity"] == 25.0188
    assert by_id["service.cnc_face_bevel"]["subtotal"] == 37.5282
    assert by_id["service.cnc_back"]["quantity"] == 25.0188
    assert by_id["service.cnc_back"]["subtotal"] == 112.5846


def test_gradi_logical_read_model_flags_undersized_psu() -> None:
    result = build_gradi_logical_list_read_model_from_runtime(
        workspace_payload=_payload(selected_psu_watts=60),
        material_breakdown=_breakdown(),
        priced_dry_run=_dry_run(),
    )
    psu = {row["line_id"]: row for row in result["rows"]}["material.led_psu"]

    assert "PSU_UNDERSIZED" in result["warnings"]
    assert "PSU_UNDERSIZED" in result["blockers"]
    assert "PSU_UNDERSIZED" in psu["warnings"]
    assert "PSU_UNDERSIZED" in psu["blockers"]