from __future__ import annotations

from types import SimpleNamespace

from data_models.product_contracts import CostResult, QuoteCalculationSnapshot, QuotePricing
from routers.quotes import _apply_linked_module_results_to_snapshot


def test_linked_module_results_are_composed_into_quote_snapshot() -> None:
    snapshot = QuoteCalculationSnapshot(
        cost_result=CostResult(
            materials_cost=100,
            labour_cost=40,
            total_cost=140,
            estimated_time_minutes=30,
        ),
        pricing=QuotePricing(margin_pct=25, discount_pct=0, vat_pct=19),
        status="priced",
    )
    snapshot.price = SimpleNamespace(net=175, gross=208.25, final=208.25)

    totals = _apply_linked_module_results_to_snapshot(
        snapshot,
        [
            {
                "status": "priced",
                "cost_result": {
                    "materials_cost": 20.35,
                    "labour_cost": 15.26,
                    "total_cost": 35.61,
                    "estimated_time_minutes": 0,
                },
            }
        ],
        QuotePricing(margin_pct=25, discount_pct=0, vat_pct=19),
    )

    assert totals == {
        "parent_total_cost": 140,
        "linked_modules_total_cost": 35.61,
        "composite_total_cost": 175.61,
    }
    assert snapshot.status == "priced"
    assert snapshot.cost_result.materials_cost == 120.35
    assert snapshot.cost_result.labour_cost == 55.26
    assert snapshot.cost_result.total_cost == 175.61
    assert snapshot.price.net == 219.51
    assert snapshot.price.gross == 261.22


def test_blocked_linked_module_blocks_parent_snapshot() -> None:
    snapshot = QuoteCalculationSnapshot(
        cost_result=CostResult(total_cost=140),
        pricing=QuotePricing(margin_pct=25, discount_pct=0, vat_pct=19),
        status="priced",
    )

    totals = _apply_linked_module_results_to_snapshot(
        snapshot,
        [{"status": "blocked", "blocked_reasons": ["missing_rate"]}],
        QuotePricing(margin_pct=25, discount_pct=0, vat_pct=19),
    )

    assert totals == {}
    assert snapshot.status == "blocked"
    assert snapshot.blocked_reasons == ["linked_module[0]:missing_rate"]
