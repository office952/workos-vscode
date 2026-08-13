"""Owner GO 2026-08-13 — back bevel commercial line + same CNC task."""

from __future__ import annotations

import pytest

from data.commercial_rules_volumetric_v2 import (
    OWNER_CONFIRMED_PROVISIONAL_COMMERCIAL_LINE_CODES,
    WORKCENTER_REUSE_PROVISIONAL_COMMERCIAL_LINE_CODES,
    inventory_commercial_rules_for_template,
)
from services.shared_cnc_operation_model import FOREX_10MM_BEVEL_PASSES_OWNER
from tests.test_commercial_price_proposal_preview import TEMPLATE, _full_quote_input

pytest_plugins = ["tests.test_commercial_price_proposal_preview"]

BEVEL_ML = 7.4175
EXPECTED_NET = BEVEL_ML * FOREX_10MM_BEVEL_PASSES_OWNER * 1.5


def _quote(*, bevel: bool, perimeter_ml: float | None = BEVEL_ML) -> dict:
    payload = _full_quote_input()
    payload["back_bevel_enabled"] = bevel
    payload["backing_mode"] = "forex_10_with_bevel" if bevel else "forex_10_no_bevel"
    payload["backing_bevel_perimeter_ml"] = perimeter_ml if bevel else None
    finish = payload.setdefault("finish_setup", {})
    finish["backing_mode"] = payload["backing_mode"]
    finish["back_bevel_enabled"] = bevel
    finish["backing_bevel_perimeter_ml"] = payload["backing_bevel_perimeter_ml"]
    return payload


@pytest.mark.asyncio
async def test_sanfren_absent_when_bevel_off(cpp_service):
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=_quote(bevel=False))
    assert preview is not None
    codes = {line.code for line in preview.commercial_price_lines}
    assert "sanfren_spate" not in codes
    assert "debitare_spate" in codes


@pytest.mark.asyncio
async def test_sanfren_present_with_owner_formula_when_bevel_on(cpp_service):
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=_quote(bevel=True))
    assert preview is not None
    line = next(row for row in preview.commercial_price_lines if row.code == "sanfren_spate")
    assert line.label == "Șanfren CNC spate Forex 10 mm"
    assert line.module_code == "debitare_spate"
    assert line.unit == "ml"
    assert line.quantity == pytest.approx(BEVEL_ML)
    assert line.commercial_unit_price == pytest.approx(3.0)
    assert line.subtotal == pytest.approx(EXPECTED_NET)
    assert line.registry_pricing_code == "CNC_ROUTER"
    assert line.source_currency == "EUR"
    assert any("pass_factor=VOLUMETRIC_BACKING_BEVEL_RULE.passes:2" in w for w in line.warnings)


@pytest.mark.asyncio
async def test_debitare_spate_unchanged_when_bevel_on(cpp_service):
    off = await cpp_service.build_preview(TEMPLATE, quote_input=_quote(bevel=False))
    on = await cpp_service.build_preview(TEMPLATE, quote_input=_quote(bevel=True))
    off_back = next(row for row in off.commercial_price_lines if row.code == "debitare_spate")
    on_back = next(row for row in on.commercial_price_lines if row.code == "debitare_spate")
    assert on_back.quantity == off_back.quantity
    assert on_back.commercial_unit_price == off_back.commercial_unit_price
    assert on_back.subtotal == off_back.subtotal
    assert on_back.unit == "m2"


@pytest.mark.asyncio
async def test_no_double_sanfren_line(cpp_service):
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=_quote(bevel=True))
    sanfren = [row for row in preview.commercial_price_lines if row.code == "sanfren_spate"]
    assert len(sanfren) == 1


def test_sanfren_not_in_f7i1_owner_provisional_set():
    assert "sanfren_spate" not in OWNER_CONFIRMED_PROVISIONAL_COMMERCIAL_LINE_CODES
    assert "sanfren_spate" in WORKCENTER_REUSE_PROVISIONAL_COMMERCIAL_LINE_CODES
    inv = {row["canonical_rule_code"]: row for row in inventory_commercial_rules_for_template(TEMPLATE)}
    row = inv["sanfren_spate"]
    assert row["publication_state"] == "ACTIVE_PROVISIONAL"
    assert row["provisional_nature"] == "workcenter_reuse_provisional"
    assert row["current_rate"] == 1.5
