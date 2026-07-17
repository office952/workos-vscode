"""CPP / live materials — typed mains_cable_length_m → wire supply quantity."""

from __future__ import annotations

import pytest
import pytest_asyncio

from services.intake_v4_consumables_adhesive_wiring_service import (
    ALLOWED_MAINS_CABLE_LENGTHS_M,
    BASIS_WIRE_SUPPLY_TYPED_LENGTH,
    QTY_SOURCE_LEGACY_FIXED,
    QTY_SOURCE_TYPED,
    WIRE_SUPPLY_ML_PER_JOB,
    WIRE_SUPPLY_PRICE_RON_PER_ML,
    append_volumetric_adhesive_and_wiring_consumables,
    build_wire_supply_myyup_row,
    owner_ron_to_eur,
    resolve_mains_cable_commercial_quantity,
    resolve_support_type_for_commercial,
)
from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown
from services.product_aggregate_service import ProductAggregateService
from services.product_process_resolve_input_adapter import PROCESS_GRAPH_SOURCE_MODULAR
from tests.test_product_aggregate_volumetric_v2 import TEMPLATE_CODE, _seed_volumetric_v2_fixture

METAL_SOLUTION = {
    "kind": "product_system_template",
    "template_code": "TPL-METAL-PREMOUNT-STRUCTURE_v1",
    "configuration": {},
}
ACM_SOLUTION = {
    "kind": "product_system_template",
    "template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
    "configuration": {},
}


def _payload(**finish_extra) -> dict:
    finish = {
        "face_finish_type": "oracal_8500",
        "return_finish_type": "oracal_wrapped",
        "return_depth_mm": 60,
        "illuminated": True,
        "lighting_system_type": "led_modules",
        "confirmed": True,
        "mounting_template_enabled": False,
    }
    finish.update(finish_extra)
    return {
        "schema_version": "1.0.0",
        "product_binding": {"template_code": "TPL-VOLUMETRIC-LETTERS_v2"},
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
        "finish_setup": finish,
    }


def _wire_row(result):
    for row in result.consumable_rows:
        if row.material_key == "wire_supply_myyup_2x15":
            return row
    return None


def _warn_codes(result) -> set[str]:
    return {w.code for w in result.warnings}


def test_a_legacy_constant_still_five():
    assert WIRE_SUPPLY_ML_PER_JOB == 5.0


def test_b_allowed_lengths_match_process_contract():
    assert ALLOWED_MAINS_CABLE_LENGTHS_M == frozenset(
        {2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0, 22.5, 25.0}
    )


@pytest.mark.parametrize("length", sorted(ALLOWED_MAINS_CABLE_LENGTHS_M))
def test_d_m_all_allowed_typed_lengths(length):
    result = build_intake_v4_material_breakdown(
        "ws-cable",
        _payload(
            mounting_solution=METAL_SOLUTION,
            mounting_system="steel_bars",
            mains_cable_length_m=length,
        ),
    )
    row = _wire_row(result)
    assert row is not None
    assert row.quantity == length
    assert row.priced_quantity == length
    assert row.quantity_basis == BASIS_WIRE_SUPPLY_TYPED_LENGTH
    assert row.quantity_source == QTY_SOURCE_TYPED
    assert row.material_code == "MAT-CABLU-MYYUP-2X15"
    unit = owner_ron_to_eur(WIRE_SUPPLY_PRICE_RON_PER_ML)
    assert row.estimated_cost == round(length * unit, 2)


@pytest.mark.parametrize("bad", [0, -1, 3, 6, 26])
def test_n_q_invalid_numeric_typed_skips_line(bad):
    result = build_intake_v4_material_breakdown(
        "ws-bad-cable",
        _payload(
            mounting_solution=METAL_SOLUTION,
            mounting_system="steel_bars",
            mains_cable_length_m=bad,
        ),
    )
    assert _wire_row(result) is None
    assert "INVALID_MAINS_CABLE_LENGTH_COMMERCIAL_SKIPPED" in _warn_codes(result)


def test_r_invalid_string_resolver_skips():
    qty, _, source, warns = resolve_mains_cable_commercial_quantity(
        finish={"mains_cable_length_m": "abc", "mounting_system": "steel_bars"},
    )
    assert qty is None
    assert source == "typed_mains_cable_length_invalid"
    assert "invalid_mains_cable_length_commercial_skipped" in warns


def test_legacy_missing_typed_keeps_5ml():
    result = build_intake_v4_material_breakdown("ws-legacy", _payload())
    row = _wire_row(result)
    assert row is not None
    assert row.quantity == 5.0
    assert row.quantity_source == QTY_SOURCE_LEGACY_FIXED
    assert "LEGACY_WIRE_SUPPLY_DEFAULT_5ML" in _warn_codes(result)


def test_typed_wins_over_legacy_default():
    qty, basis, source, _ = resolve_mains_cable_commercial_quantity(
        finish={"mains_cable_length_m": 12.5, "mounting_system": "steel_bars"},
    )
    assert qty == 12.5
    assert source == QTY_SOURCE_TYPED
    assert basis == BASIS_WIRE_SUPPLY_TYPED_LENGTH


def test_proportional_cost_2_5_vs_25():
    low = build_wire_supply_myyup_row(
        quantity_ml=2.5, quantity_basis=BASIS_WIRE_SUPPLY_TYPED_LENGTH, quantity_source=QTY_SOURCE_TYPED
    )
    high = build_wire_supply_myyup_row(
        quantity_ml=25.0, quantity_basis=BASIS_WIRE_SUPPLY_TYPED_LENGTH, quantity_source=QTY_SOURCE_TYPED
    )
    assert high.quantity == pytest.approx(low.quantity * 10.0)
    assert low.unit_price == high.unit_price
    assert high.estimated_cost == round(25.0 * owner_ron_to_eur(WIRE_SUPPLY_PRICE_RON_PER_ML), 2)


def test_aa_metal_bars_cable_and_channel_guard():
    result = build_intake_v4_material_breakdown(
        "ws-metal",
        _payload(
            mounting_solution=METAL_SOLUTION,
            mounting_system="steel_bars",
            mains_cable_length_m=2.5,
        ),
    )
    assert _wire_row(result).quantity == 2.5
    assert "CABLE_CHANNEL_COMMERCIAL_FORMULA_GUARDED" in _warn_codes(result)
    assert not any(r.material_key and "channel" in r.material_key for r in result.consumable_rows)


def test_ab_ae_alucobond_cable_no_channel():
    result = build_intake_v4_material_breakdown(
        "ws-acm",
        _payload(
            mounting_solution=ACM_SOLUTION,
            mounting_system="acm_panel",
            mains_cable_length_m=10.0,
            power_supply_service_corner="TOP_LEFT",
        ),
    )
    assert _wire_row(result).quantity == 10.0
    assert "CABLE_CHANNEL_COMMERCIAL_FORMULA_GUARDED" not in _warn_codes(result)


def test_ac_af_no_support_typed_cable_explicit():
    result = build_intake_v4_material_breakdown(
        "ws-none",
        _payload(
            mounting_system="direct_wall",
            mounting_solution={"kind": "installation_template", "template_code": None},
            mains_cable_length_m=7.5,
        ),
    )
    assert _wire_row(result).quantity == 7.5
    assert "CABLE_CHANNEL_COMMERCIAL_FORMULA_GUARDED" not in _warn_codes(result)


def test_support_mapping_metal_acm_none():
    assert resolve_support_type_for_commercial({"mounting_solution": METAL_SOLUTION}) == "metal_bars"
    assert resolve_support_type_for_commercial({"mounting_solution": ACM_SOLUTION}) == "alucobond_cased"
    assert resolve_support_type_for_commercial({"mounting_system": "direct_wall"}) == "none"


def test_ak_template_off_no_sablon_consumable_from_wiring():
    result = build_intake_v4_material_breakdown(
        "ws-tpl-off",
        _payload(mounting_template_enabled=False, mains_cable_length_m=5.0),
    )
    assert not any("sablon" in (r.material_key or "") for r in result.consumable_rows)


def test_append_direct_skips_invalid_without_inventing_five():
    rows = []
    warnings = []
    append_volumetric_adhesive_and_wiring_consumables(
        geom_sources=[{"real_letters_count": 3}],
        letter_return_ml=2.0,
        total_return_ml=2.0,
        artwork_return_ml=None,
        illuminated=True,
        led_module_count=None,
        consumable_rows=rows,
        warnings=warnings,
        finish_setup={"mains_cable_length_m": 3.0, "mounting_system": "steel_bars"},
    )
    assert not any(r.material_key == "wire_supply_myyup_2x15" for r in rows)
    assert any(w.code == "INVALID_MAINS_CABLE_LENGTH_COMMERCIAL_SKIPPED" for w in warnings)


@pytest_asyncio.fixture
async def volumetric_v2_db(db_session):
    await _seed_volumetric_v2_fixture(db_session)
    return db_session


@pytest.mark.asyncio
async def test_process_task_set_stable_across_cable_lengths(volumetric_v2_db):
    """Commercial length must not change process task codes/order (hash may include length echo)."""
    svc = ProductAggregateService(volumetric_v2_db)
    payload = {
        "finish_setup": {
            "return_finish_type": "white_aluminum",
            "lighting_system_type": "led_modules",
            "mounting_system": "steel_bars",
            "mounting_solution": METAL_SOLUTION,
            "mains_cable_length_m": 2.5,
            "mounting_template_enabled": False,
            "service_screw_finish": "NATURAL",
        },
        "quote_geometry": {
            "width_mm": 1200,
            "height_mm": 400,
            "letter_count": 5,
            "letter_perimeter_m": 8.2,
            "letter_face_area_m2": 0.45,
        },
    }
    a = await svc.build(TEMPLATE_CODE, process_bridge_payload=payload)
    payload["finish_setup"]["mains_cable_length_m"] = 25.0
    b = await svc.build(TEMPLATE_CODE, process_bridge_payload=payload)
    assert a.task_contract.process_graph_source == PROCESS_GRAPH_SOURCE_MODULAR
    assert [r.task_name for r in a.task_contract.task_rules] == [
        r.task_name for r in b.task_contract.task_rules
    ]
    assert [r.depends_on_process_ids for r in a.task_contract.task_rules] == [
        r.depends_on_process_ids for r in b.task_contract.task_rules
    ]

    bd_low = build_intake_v4_material_breakdown(
        "ws-a",
        _payload(
            mounting_solution=METAL_SOLUTION,
            mounting_system="steel_bars",
            mains_cable_length_m=2.5,
        ),
    )
    bd_high = build_intake_v4_material_breakdown(
        "ws-b",
        _payload(
            mounting_solution=METAL_SOLUTION,
            mounting_system="steel_bars",
            mains_cable_length_m=25.0,
        ),
    )
    assert _wire_row(bd_low).quantity == 2.5
    assert _wire_row(bd_high).quantity == 25.0
