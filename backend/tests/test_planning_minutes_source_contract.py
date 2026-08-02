"""DEC-011 — planning minutes source contract (not Pricing / rates / salary)."""

from __future__ import annotations

from schemas.product_aggregate import ProductAggregateOperation
from services.execution_plan_v2_preview_service import (
    resolve_planning_minutes_from_aggregate_op,
)
from services.planning_duration_contract import get_planning_duration_contract
from services.product_aggregate_planning_duration_service import (
    apply_planning_duration_resolution,
)
from schemas.product_aggregate import (
    ProductAggregate,
    ProductAggregateTaskContract,
)


def test_vector_prep_formula_resolves_not_from_rate():
    contract = get_planning_duration_contract(
        "TPL-VOLUMETRIC-LETTERS", "vector_prep"
    )
    assert contract is not None
    assert contract.formula_params is not None
    assert "minutes_per_letter" in contract.formula_params
    # Must not look like commercial lei/hour.
    assert "rate" not in str(contract.formula_params).lower()


def test_collect_facts_flattens_quote_geometry():
    from services.product_aggregate_planning_duration_service import (
        collect_planning_duration_facts,
    )

    facts = collect_planning_duration_facts(
        {"quote_geometry": {"letter_count": 5, "letter_perimeter_m": 10.0}}
    )
    assert facts.get("letter_count") == 5
    assert facts.get("letter_perimeter_m") == 10.0


def test_missing_contract_stays_null_not_zero():
    op = ProductAggregateOperation(
        operation_code="painting",
        label="Paint",
        estimated_minutes=None,
        planning_duration_status="placeholder",
    )
    minutes, source = resolve_planning_minutes_from_aggregate_op(op)
    assert minutes is None
    assert source is None or "rate" not in str(source).lower()


def test_false_zero_not_invented_from_empty_op():
    op = ProductAggregateOperation(operation_code="side_forming", label="Side")
    minutes, _ = resolve_planning_minutes_from_aggregate_op(op)
    assert minutes is None


def test_formula_resolution_uses_letter_count_not_price():
    agg = ProductAggregate(
        template_id=1,
        template_code="TPL-VOLUMETRIC-LETTERS",
        operations=[
            ProductAggregateOperation(
                operation_code="vector_prep",
                label="Vector",
                priced=True,
            )
        ],
        task_contract=ProductAggregateTaskContract(task_rules=[]),
    )
    resolved = apply_planning_duration_resolution(agg, {"letter_count": 5})
    vp = resolved.operations[0]
    assert vp.estimated_minutes == 10.0  # 5 * 2
    assert vp.planning_duration_status in {"resolved", "RESOLVED"} or str(
        vp.planning_duration_status
    ).lower() == "resolved"
    assert vp.planning_minutes_source is not None
    assert "formula" in vp.planning_minutes_source.lower() or "count" in (
        vp.planning_duration_formula_id or ""
    ).lower()
