"""Resolve operational planning minutes into ProductAggregate operations.

TE2E-028B — Aggregate is the resolver/emitter. Uses Product System duration
contracts + ProductDefinition/product facts. Does not call CostEngine or EIC.
"""

from __future__ import annotations

from typing import Any, Mapping

from schemas.product_aggregate import ProductAggregate, ProductAggregateOperation
from services.formula_handlers import UNIT_MINUTES, resolve_formula
from services.planning_duration_contract import (
    PlanningDurationContract,
    get_planning_duration_contract,
)

PLANNING_DURATION_STATUS_RESOLVED = "resolved"
PLANNING_DURATION_STATUS_MISSING_INPUT = "missing_input"
PLANNING_DURATION_STATUS_INVALID_INPUT = "invalid_input"
PLANNING_DURATION_STATUS_FAILED = "failed"
PLANNING_DURATION_STATUS_PLACEHOLDER = "placeholder"
PLANNING_DURATION_STATUS_STATIC = "static"
PLANNING_DURATION_STATUS_NONE = "none"

PLANNING_MINUTES_SOURCE_AGGREGATE_FORMULA_PREFIX = (
    "product_aggregate_snapshot.operations.estimated_minutes.formula"
)


def planning_minutes_source_for_formula(formula_id: str) -> str:
    fid = str(formula_id or "").strip() or "unknown"
    return f"{PLANNING_MINUTES_SOURCE_AGGREGATE_FORMULA_PREFIX}:{fid}"


def collect_planning_duration_facts(
    *sources: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Merge product-fact sources (PD geometry / quote_input / canonical)."""
    out: dict[str, Any] = {}
    for source in sources:
        if not isinstance(source, dict):
            continue
        for key, value in source.items():
            if value is None:
                continue
            if isinstance(value, dict):
                # Flatten common nested geometry bags without inventing values.
                # quote_geometry is the freeze-time Product System bag for letter_count etc.
                if key in {
                    "geometry",
                    "geometry_inputs",
                    "finish_setup",
                    "quote_geometry",
                }:
                    for nested_key, nested_val in value.items():
                        if nested_val is not None and nested_key not in out:
                            out[str(nested_key)] = nested_val
                continue
            out[str(key)] = value
    return out


def _is_static_op(op: ProductAggregateOperation) -> bool:
    calc = (op.calculation_type or "").strip().lower()
    return calc == "static"


def _is_placeholder_zero(op: ProductAggregateOperation) -> bool:
    calc = (op.calculation_type or "").strip().lower()
    if calc != "formula_based":
        return False
    if op.estimated_minutes is None:
        return False
    try:
        return float(op.estimated_minutes) == 0.0
    except (TypeError, ValueError):
        return False


def _resolve_formula_minutes(
    contract: PlanningDurationContract,
    facts: Mapping[str, Any],
) -> tuple[float | None, str, str | None]:
    """Return (minutes|None, status, detail)."""
    if not contract.formula_id:
        return None, PLANNING_DURATION_STATUS_FAILED, "missing_formula_id"

    for key in contract.required_inputs:
        if key not in facts or facts.get(key) is None:
            return None, PLANNING_DURATION_STATUS_MISSING_INPUT, f"missing:{key}"

    result = resolve_formula(
        contract.formula_id,
        dict(contract.formula_params or {}),
        dict(facts),
    )
    if not result.resolved or result.value is None:
        err = result.error or {}
        kind = str(err.get("kind") or "FAILED")
        missing = err.get("missing") or []
        if kind in {"MISSING_INPUT", "MISSING"} or missing:
            return None, PLANNING_DURATION_STATUS_MISSING_INPUT, kind
        if kind in {"INVALID_INPUT", "INVALID_PARAM", "ERR_INVALID_PARAM"}:
            return None, PLANNING_DURATION_STATUS_INVALID_INPUT, kind
        return None, PLANNING_DURATION_STATUS_FAILED, kind

    unit = str(result.unit or "").strip().lower()
    if unit and unit not in {UNIT_MINUTES, "min", "minutes"}:
        return None, PLANNING_DURATION_STATUS_FAILED, f"unexpected_unit:{unit}"

    try:
        minutes = float(result.value)
    except (TypeError, ValueError):
        return None, PLANNING_DURATION_STATUS_FAILED, "non_numeric_result"

    if minutes < 0:
        return None, PLANNING_DURATION_STATUS_INVALID_INPUT, "negative_minutes"

    return minutes, PLANNING_DURATION_STATUS_RESOLVED, None


def resolve_operation_planning_duration(
    op: ProductAggregateOperation,
    *,
    template_code: str | None,
    facts: Mapping[str, Any],
) -> ProductAggregateOperation:
    """Apply contract-driven duration mode to one Aggregate operation."""
    contract = get_planning_duration_contract(template_code, op.operation_code)

    # CONTRACT RULE: static configured minutes are never overwritten by formula.
    if _is_static_op(op):
        return op.model_copy(
            update={
                "planning_duration_mode": "static",
                "planning_duration_status": PLANNING_DURATION_STATUS_STATIC,
                "planning_duration_formula_id": None,
                "planning_minutes_source": (
                    "product_aggregate_snapshot.operations.estimated_minutes"
                ),
            }
        )

    if contract is None:
        # No Product System duration contract → planning mode none for qty placeholders.
        if _is_placeholder_zero(op):
            return op.model_copy(
                update={
                    "estimated_minutes": None,
                    "planning_duration_mode": "none",
                    "planning_duration_status": PLANNING_DURATION_STATUS_PLACEHOLDER,
                    "planning_duration_formula_id": None,
                    "planning_minutes_source": None,
                }
            )
        return op.model_copy(
            update={
                "planning_duration_mode": "none",
                "planning_duration_status": PLANNING_DURATION_STATUS_NONE,
            }
        )

    if contract.duration_mode == "none":
        return op.model_copy(
            update={
                "estimated_minutes": None,
                "planning_duration_mode": "none",
                "planning_duration_status": PLANNING_DURATION_STATUS_NONE,
                "planning_duration_formula_id": None,
                "planning_minutes_source": None,
            }
        )

    if contract.duration_mode == "static":
        return op.model_copy(
            update={
                "planning_duration_mode": "static",
                "planning_duration_status": PLANNING_DURATION_STATUS_STATIC,
                "planning_duration_formula_id": None,
                "planning_minutes_source": (
                    "product_aggregate_snapshot.operations.estimated_minutes"
                ),
            }
        )

    # formula mode
    minutes, status, _detail = _resolve_formula_minutes(contract, facts)
    if status != PLANNING_DURATION_STATUS_RESOLVED or minutes is None:
        return op.model_copy(
            update={
                "estimated_minutes": None,
                "planning_duration_mode": "formula",
                "planning_duration_status": status,
                "planning_duration_formula_id": contract.formula_id,
                "planning_minutes_source": None,
            }
        )

    return op.model_copy(
        update={
            "estimated_minutes": minutes,
            "planning_duration_mode": "formula",
            "planning_duration_status": PLANNING_DURATION_STATUS_RESOLVED,
            "planning_duration_formula_id": contract.formula_id,
            "planning_minutes_source": planning_minutes_source_for_formula(
                contract.formula_id or ""
            ),
        }
    )


def apply_planning_duration_resolution(
    aggregate: ProductAggregate,
    facts: Mapping[str, Any] | None = None,
) -> ProductAggregate:
    """Resolve planning minutes for all Aggregate operations (deterministic)."""
    fact_map = dict(facts or {})
    template_code = aggregate.template_code
    resolved_ops = [
        resolve_operation_planning_duration(
            op, template_code=template_code, facts=fact_map
        )
        for op in aggregate.operations
    ]
    return aggregate.model_copy(update={"operations": resolved_ops})
