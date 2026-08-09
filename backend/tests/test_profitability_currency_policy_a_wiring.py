"""Policy A wiring helpers — FX stamp parse + schema (convert covered in order_snapshot tests)."""

from __future__ import annotations

import pytest

from schemas.order_snapshot_v2 import ProfitabilityFxV1Stamp
from services.profitability_actual_read_model_service import _parse_profitability_fx_v1


def test_profitability_fx_stamp_parse_accepts_policy_a():
    stamp = ProfitabilityFxV1Stamp(
        policy="A",
        eur_to_ron_rate=5.1234,
        frozen_at="2026-08-09T18:00:00+00:00",
    )
    parsed = _parse_profitability_fx_v1(stamp.model_dump())
    assert parsed is not None
    assert parsed["policy"] == "A"
    assert parsed["eur_to_ron_rate"] == pytest.approx(5.1234)
    assert parsed["freeze_point"] == "order_convert"


def test_profitability_fx_stamp_parse_rejects_invalid():
    assert _parse_profitability_fx_v1(None) is None
    assert _parse_profitability_fx_v1({"eur_to_ron_rate": 0}) is None
    assert _parse_profitability_fx_v1({"eur_to_ron_rate": -1}) is None
    assert _parse_profitability_fx_v1({"policy": "B", "eur_to_ron_rate": 5}) is None
    assert _parse_profitability_fx_v1({"eur_to_ron_rate": "x"}) is None
