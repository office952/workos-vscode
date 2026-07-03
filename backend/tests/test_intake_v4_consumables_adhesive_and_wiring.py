"""Intake V4 consumables — adhesive bonding + wiring for illuminated volumetric letters."""

from __future__ import annotations

import math

import pytest

from services.intake_v4_consumables_adhesive_wiring_service import (
    ADHESIVE_BOTTLE_ML,
    ADHESIVE_ML_PER_LED_MODULE,
    ADHESIVE_ML_PER_ML_CANT,
    OWNER_EUR_RATE_RON,
    WIRE_LETTERS_PRICE_RON_PER_ML,
    WIRE_SUPPLY_ML_PER_JOB,
    WIRE_SUPPLY_PRICE_RON_PER_ML,
    build_adhesive_led_modules_row,
    build_adhesive_return_to_face_row,
    build_wire_letters_myyup_row,
    build_wire_supply_myyup_row,
    owner_ron_to_eur,
    owner_ron_to_eur_display,
    resolve_letter_return_perimeter_ml_for_adhesive,
)
from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown


def _pbl_payload(*, illuminated: bool = True) -> dict:
    return {
        "schema_version": "1.0.0",
        "product_binding": {"template_code": "TPL-VOLUMETRIC-LETTERS"},
        "svg_analysis_json": {
            "schemaVersion": "1.10.0",
            "geometry": {
                "letter_perimeter_m": 11.6299,
                "real_letters_count": 10,
                "artwork_piece_count": 1,
            },
        },
        "quote_geometry": {
            "letter_perimeter_m": 11.6299,
            "total_letter_perimeter_ml": 11.6299,
            "return_material_perimeter_ml": 15.4672,
            "letter_return_perimeter_ml": 13.6211,
            "artwork_return_perimeter_ml": 1.8461,
            "face_area_m2": 0.6907,
            "real_letters_count": 10,
            "artwork_piece_count": 1,
            "letter_count": 10,
        },
        "finish_setup": {
            "face_finish_type": "oracal_8500",
            "return_finish_type": "oracal_wrapped",
            "return_depth_mm": 60,
            "illuminated": illuminated,
            "lighting_system_type": "led_modules" if illuminated else None,
            "letter_group_finishes": [
                {
                    "group_key": "Layer_x0020_2",
                    "face_finish_type": "oracal_8500",
                    "return_finish_type": "oracal_wrapped",
                    "perimeter_m": 6.1683,
                },
                {
                    "group_key": "Layer_x0020_3",
                    "face_finish_type": "oracal_8500",
                    "return_finish_type": "standard_aluminum",
                    "perimeter_m": 7.4528,
                },
            ],
            "confirmed": True,
        },
    }


def _consumable_keys(result) -> list[str]:
    return [row.material_key for row in result.consumable_rows]


def _row(result, key: str):
    for row in result.consumable_rows:
        if row.material_key == key:
            return row
    raise AssertionError(f"missing consumable row {key}")


class TestConsumablePricingHelpers:
    def test_adhesive_eur_conversion(self):
        unit_ron = 30.0 / 50.0
        assert owner_ron_to_eur_display(30.0) == 5.9
        assert owner_ron_to_eur_display(unit_ron) == 0.1

    def test_wire_075_eur_display(self):
        assert owner_ron_to_eur_display(WIRE_LETTERS_PRICE_RON_PER_ML) == 0.4

    def test_wire_supply_eur_display_and_job_cost(self):
        assert owner_ron_to_eur_display(WIRE_SUPPLY_PRICE_RON_PER_ML) == 0.8
        cost = round(WIRE_SUPPLY_ML_PER_JOB * owner_ron_to_eur(WIRE_SUPPLY_PRICE_RON_PER_ML), 2)
        assert cost == 3.82


class TestAdhesiveBasis:
    def test_prefers_letter_return_perimeter(self):
        ml = resolve_letter_return_perimeter_ml_for_adhesive(
            13.6211,
            total_return_ml=15.4672,
            artwork_return_ml=1.8461,
        )
        assert ml == 13.6211

    def test_derives_from_total_minus_artwork(self):
        ml = resolve_letter_return_perimeter_ml_for_adhesive(
            None,
            total_return_ml=15.4672,
            artwork_return_ml=1.8461,
        )
        assert round(ml, 4) == round(15.4672 - 1.8461, 4)


class TestPblIlluminatedConsumables:
    def test_adds_adhesive_row(self):
        result = build_intake_v4_material_breakdown("ws-pbl", _pbl_payload())
        assert "adhesive_return_to_face" in _consumable_keys(result)

    def test_adhesive_quantity_is_return_perimeter_times_two(self):
        result = build_intake_v4_material_breakdown("ws-pbl", _pbl_payload())
        row = _row(result, "adhesive_return_to_face")
        expected_ml = round(13.6211 * ADHESIVE_ML_PER_ML_CANT, 4)
        assert row.quantity == expected_ml

    def test_adhesive_bottle_count(self):
        row = build_adhesive_return_to_face_row(13.6211)
        quantity_ml = 13.6211 * ADHESIVE_ML_PER_ML_CANT
        bottles = math.ceil(quantity_ml / ADHESIVE_BOTTLE_ML)
        assert bottles == 1
        assert f"bottles_required={bottles}" in row.quantity_source

    def test_adhesive_pricing_owner_ron_rate(self):
        row = build_adhesive_return_to_face_row(10.0)
        assert row.unit_price == 0.1
        assert row.price_source == "intake_v4_owner_consumable_adhesive"
        assert row.estimated_cost == round(20.0 * owner_ron_to_eur(30.0 / 50.0), 2)

    def test_adds_wire_075_row(self):
        result = build_intake_v4_material_breakdown("ws-pbl", _pbl_payload())
        assert "wire_letters_myyup_2x075" in _consumable_keys(result)

    def test_wire_075_quantity_per_real_letter(self):
        result = build_intake_v4_material_breakdown("ws-pbl", _pbl_payload())
        row = _row(result, "wire_letters_myyup_2x075")
        assert row.quantity == 10.0

    def test_wire_075_unit_price_display(self):
        row = build_wire_letters_myyup_row(10)
        assert row.unit_price == 0.4
        assert row.estimated_cost == round(10 * owner_ron_to_eur(WIRE_LETTERS_PRICE_RON_PER_ML), 2)

    def test_adds_wire_supply_row_five_ml(self):
        result = build_intake_v4_material_breakdown("ws-pbl", _pbl_payload())
        row = _row(result, "wire_supply_myyup_2x15")
        assert row.quantity == 5.0

    def test_adds_led_module_adhesive_row(self):
        result = build_intake_v4_material_breakdown("ws-pbl", _pbl_payload())
        assert "adhesive_led_modules" in _consumable_keys(result)

    def test_led_adhesive_quantity_per_module(self):
        row = build_adhesive_led_modules_row(47)
        assert row.quantity == round(47 * ADHESIVE_ML_PER_LED_MODULE, 4)
        assert row.quantity == 9.4

    def test_led_adhesive_bottle_count(self):
        row = build_adhesive_led_modules_row(47)
        bottles = math.ceil(9.4 / ADHESIVE_BOTTLE_ML)
        assert bottles == 1
        assert f"bottles_required={bottles}" in row.quantity_source

    def test_led_adhesive_uses_same_pricing_as_return_adhesive(self):
        cant_row = build_adhesive_return_to_face_row(10.0)
        led_row = build_adhesive_led_modules_row(47)
        assert led_row.price_source == cant_row.price_source
        assert led_row.unit_price == cant_row.unit_price

    def test_pbl_led_adhesive_quantity(self):
        result = build_intake_v4_material_breakdown("ws-pbl", _pbl_payload())
        row = _row(result, "adhesive_led_modules")
        assert row.quantity == 9.4

    def test_wire_supply_has_owner_price(self):
        row = build_wire_supply_myyup_row()
        assert row.unit_price == 0.8
        assert row.estimated_cost == 3.82
        assert row.price_source == "intake_v4_owner_consumable_wire_supply"


class TestNonIlluminated:
    def test_no_wiring_rows_when_not_illuminated(self):
        result = build_intake_v4_material_breakdown("ws-dark", _pbl_payload(illuminated=False))
        keys = _consumable_keys(result)
        assert "adhesive_return_to_face" in keys
        assert "adhesive_led_modules" not in keys
        assert "wire_letters_myyup_2x075" not in keys
        assert "wire_supply_myyup_2x15" not in keys
        assert "led_modules" not in keys


class TestBreakdownSafety:
    def test_no_stock_consumption_flag(self):
        result = build_intake_v4_material_breakdown("ws-pbl", _pbl_payload())
        assert result.stock_consumption is False

    def test_consumable_rows_are_quote_estimate_only(self):
        result = build_intake_v4_material_breakdown("ws-pbl", _pbl_payload())
        for row in result.consumable_rows:
            if row.material_key.startswith(("adhesive_", "wire_")):
                assert row.consumption_mode == "quote_estimate"
                assert row.price_source.startswith("intake_v4_owner_consumable")
