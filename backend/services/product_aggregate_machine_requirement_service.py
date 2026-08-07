"""Stamp Operation Contract machine demand onto ProductAggregate operations.

Demand only — no machine_id, Reservation, MACHINE_RUN, or Capacity.
"""

from __future__ import annotations

from schemas.product_aggregate import ProductAggregate, ProductAggregateOperation
from services.operation_machine_requirement_contract import (
    get_operation_machine_requirement_contract,
)


def resolve_operation_machine_requirement(
    op: ProductAggregateOperation,
) -> ProductAggregateOperation:
    """Apply contract-driven machine demand fields when declared for the op."""
    contract = get_operation_machine_requirement_contract(op.operation_code)
    if contract is None:
        return op
    return op.model_copy(
        update={
            "machine_capability_code": contract.machine_capability_code,
            "resource_mode": contract.resource_mode,
            "batch_eligible": contract.batch_eligible,
        }
    )


def apply_machine_requirement_resolution(
    aggregate: ProductAggregate,
) -> ProductAggregate:
    """Resolve machine demand for all Aggregate operations (deterministic)."""
    resolved_ops = [resolve_operation_machine_requirement(op) for op in aggregate.operations]
    return aggregate.model_copy(update={"operations": resolved_ops})
