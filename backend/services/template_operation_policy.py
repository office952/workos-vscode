"""Template operation flags — quote-priced vs internal-only (calibration)."""

from __future__ import annotations

from typing import Any


def is_internal_only_operation(op: Any) -> bool:
    """True when operation is internal checklist/calibration, not quote-priced."""
    return isinstance(op, dict) and bool(op.get("internal_only"))


def is_quote_priced_operation(op: Any) -> bool:
    """True when operation contributes to quote-priced operation costing."""
    if not isinstance(op, dict):
        return True
    if is_internal_only_operation(op):
        return False
    if op.get("quote_priced") is False:
        return False
    return True


def should_skip_operation_costing(op: Any) -> bool:
    """True when CostEngine must not require a workcenter rate for this op."""
    return not is_quote_priced_operation(op)
