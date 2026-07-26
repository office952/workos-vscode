"""CPP Letters↔ACM composition connection commercial lines."""

from __future__ import annotations

import pytest

from data.commercial_rules_volumetric_v2 import (
    LETTERS_ACM_COMPOSITION_CONNECTION_RULES,
    LETTERS_ACM_PACK_MIN_EUR,
    LETTERS_ACM_SABLON_PROCESS_EUR_M2,
)
from services.commercial_price_proposal_service import _build_line, _rule_applies
from services.letters_acm_composition_commercial_v1 import (
    COMPOSITION_LINE_PREFIX,
    is_letters_acm_composition_active,
    resolve_letters_layer_outbox_m2,
)
from services.mounting_solution_service import ACM_BOXED_MOUNTING_TEMPLATE_CODE


def _acm_letters_payload(*, outbox_m2: float = 0.5) -> dict:
    return {
        "template_code": ACM_BOXED_MOUNTING_TEMPLATE_CODE,
        "applied_content": "letters",
        "letters_layer_outbox_m2": outbox_m2,
        "panel_width_mm": 2000,
        "panel_height_mm": 1000,
        "acm_thickness_mm": 3,
        "return_depth_mm": 60,
        "fold_sides": "all",
        "finish_setup": {
            "applied_content": "letters",
            "mounting_template_enabled": True,
            "mounting_template_material_type": "forex",
            "mounting_template_area_m2": 0.9,
            "mounting_solution": {
                "template_code": ACM_BOXED_MOUNTING_TEMPLATE_CODE,
                "configuration": {
                    "panel_width_mm": 2000,
                    "panel_height_mm": 1000,
                    "acm_thickness_mm": 3,
                    "return_depth_mm": 60,
                    "fold_sides": "all",
                },
            },
        },
    }


def test_composition_active_gate():
    assert is_letters_acm_composition_active(_acm_letters_payload()) is True
    bare = _acm_letters_payload()
    bare["applied_content"] = "none"
    bare["finish_setup"]["applied_content"] = "none"
    assert is_letters_acm_composition_active(bare) is False


def test_composition_active_when_finish_applied_content_empty_but_confirmed_letters():
    """Live Remus bug: finish_setup.applied_content cleared; confirmed still letters."""
    payload = _acm_letters_payload()
    payload.pop("applied_content", None)
    payload["finish_setup"]["applied_content"] = None
    payload["product_composition_confirmed"] = {
        "confirmed": True,
        "applied_content": "letters",
        "items": [
            {"composition_item_id": "letters"},
            {"composition_item_id": "support"},
        ],
    }
    assert is_letters_acm_composition_active(payload) is True


def test_outbox_prefers_canonical_key():
    qty, src = resolve_letters_layer_outbox_m2(_acm_letters_payload(outbox_m2=0.42))
    assert qty == pytest.approx(0.42)
    assert src == "letters_layer_outbox_m2"


def test_outbox_falls_back_to_quote_geometry_letter_face():
    payload = _acm_letters_payload()
    del payload["letters_layer_outbox_m2"]
    payload["finish_setup"].pop("mounting_template_area_m2", None)
    payload["quote_geometry"] = {"letter_face_area_m2": 0.31}
    qty, src = resolve_letters_layer_outbox_m2(payload)
    assert qty == pytest.approx(0.31)
    assert src == "quote_geometry.letter_face_area_m2"


def test_composition_rules_apply_and_suppress_legacy_sablon():
    payload = _acm_letters_payload()
    modules = {"sablon_montaj", "structura_suport", "ambalare_livrare_montaj"}
    conn_rules = [r for r in LETTERS_ACM_COMPOSITION_CONNECTION_RULES]
    assert len(conn_rules) == 7
    for rule in conn_rules:
        assert rule.line_code.startswith(COMPOSITION_LINE_PREFIX)
        assert _rule_applies(rule, modules, payload) is True

    from data.commercial_rules_volumetric_v2 import VOLUMETRIC_V2_COMMERCIAL_RULES

    legacy = next(r for r in VOLUMETRIC_V2_COMMERCIAL_RULES if r.line_code == "sablon_montaj_forex")
    assert _rule_applies(legacy, modules, payload) is False


@pytest.mark.asyncio
async def test_sablon_line_uses_20_eur_and_outbox_qty(db_session=None):
    """Build line without DB — documented EUR path."""
    from unittest.mock import AsyncMock, MagicMock

    rule = next(
        r
        for r in LETTERS_ACM_COMPOSITION_CONNECTION_RULES
        if r.line_code == "letters_acm_conn_sablon_process"
    )
    db = MagicMock()
    db.execute = AsyncMock()
    line = await _build_line(db, rule, _acm_letters_payload(outbox_m2=0.5))
    assert line.commercial_unit_price == pytest.approx(LETTERS_ACM_SABLON_PROCESS_EUR_M2)
    assert line.quantity == pytest.approx(0.5)
    assert line.subtotal == pytest.approx(10.0)
    assert any("letters_acm_outbox" in w for w in line.warnings)


@pytest.mark.asyncio
async def test_pack_applies_minimum(db_session=None):
    from unittest.mock import AsyncMock, MagicMock

    rule = next(
        r for r in LETTERS_ACM_COMPOSITION_CONNECTION_RULES if r.line_code == "letters_acm_conn_pack"
    )
    db = MagicMock()
    db.execute = AsyncMock()
    # 0.5 mp × 10 = 5 < min 15
    line = await _build_line(db, rule, _acm_letters_payload(outbox_m2=0.5))
    assert line.subtotal == pytest.approx(LETTERS_ACM_PACK_MIN_EUR)
    assert any("minimum_charge_applied" in w for w in line.warnings)
