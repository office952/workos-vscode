"""Operational Readiness — dataGaps notices stay domain-separated."""

from __future__ import annotations

from services.operational_data_gaps import data_gap_notices


def test_data_gap_notices_order_and_domains():
    gaps = {
        "pricing": {
            "notice": "Pricing Registry: 1 rate/price lipsă — Owner data needed.",
            "ownerDataNeeded": True,
        },
        "costIntern": {
            "notice": "Cost Intern (HR analytics — NU tarif client): incomplete.",
            "ownerDataNeeded": True,
        },
        "capacity": {
            "notice": "Capacitate: util calendar/shift necunoscut.",
            "ownerDataNeeded": True,
        },
    }
    notices = data_gap_notices(gaps)
    assert len(notices) == 3
    assert "Pricing Registry" in notices[0]
    assert "NU tarif client" in notices[1] or "Cost Intern" in notices[1]
    assert "Capacitate" in notices[2]
    # No commercial←→salary mix-up language in capacity/pricing cross-claim
    joined = " | ".join(notices)
    assert "salariu → tarif" not in joined.lower()


def test_data_gap_notices_skips_empty_blocks():
    assert data_gap_notices({"pricing": {}, "costIntern": {"notice": "x"}}) == ["x"]
