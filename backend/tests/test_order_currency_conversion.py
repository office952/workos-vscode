"""Tests for quote EUR → order RON conversion at order creation."""

from __future__ import annotations

import pytest

from services.order_currency_conversion_service import (
    convert_quote_totals_to_order_base,
    round_commercial_total_eur,
    validate_eur_to_ron_rate,
)


def test_round_commercial_total_eur_standard():
    assert round_commercial_total_eur(1412.15) == 1412
    assert round_commercial_total_eur(1412.49) == 1412
    assert round_commercial_total_eur(1412.51) == 1413


def test_convert_eur_quote_to_ron_order_total():
    handoff = convert_quote_totals_to_order_base(
        gross_amount=1412.15,
        net_amount=1186.68,
        source_currency="EUR",
        eur_to_ron_rate=5.0,
    )
    assert handoff.commercial_total_eur == 1412.0
    assert handoff.exchange_rate_eur_ron == 5.0
    assert handoff.base_total_ron == 7060.0
    assert handoff.base_currency == "RON"
    assert handoff.commercial_currency == "EUR"


def test_convert_does_not_copy_eur_numeric_as_ron():
    handoff = convert_quote_totals_to_order_base(
        gross_amount=1412.15,
        net_amount=None,
        source_currency="EUR",
        eur_to_ron_rate=5.0,
    )
    assert handoff.base_total_ron != 1412.15
    assert handoff.base_total_ron == 7060.0


def test_missing_rate_raises():
    with pytest.raises(ValueError, match="eur_to_ron_rate_missing"):
        convert_quote_totals_to_order_base(
            gross_amount=1000,
            net_amount=None,
            source_currency="EUR",
            eur_to_ron_rate=None,
        )


def test_invalid_rate_raises():
    with pytest.raises(ValueError, match="eur_to_ron_rate_invalid"):
        validate_eur_to_ron_rate(0)


def test_ron_quote_passthrough_without_fx():
    handoff = convert_quote_totals_to_order_base(
        gross_amount=1104.33,
        net_amount=928.0,
        source_currency="RON",
        eur_to_ron_rate=5.0,
    )
    assert handoff.commercial_total_eur is None
    assert handoff.exchange_rate_eur_ron is None
    assert handoff.base_total_ron == 1104.33
