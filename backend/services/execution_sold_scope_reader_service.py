"""Read frozen sold scope from OrderSnapshotV2 for Execution Plan V2 filtering.

Uses offer_scope_snapshot fields only — no resolver rerun, no aggregate rebuild.
"""

from __future__ import annotations

from dataclasses import dataclass

from schemas.order_snapshot_v2 import OrderSnapshotV2
from schemas.product_aggregate import ProductAggregateOperation, ProductAggregateTaskRule
from services.offer_scope_led_subscope_service import (
    led_runtime_module_bucket,
    led_subscope_row_allowed,
    partial_led_subscope_filter,
    task_rule_led_subscope,
)

LINKED_SEGMENT_TRIGGER_PREFIX = "linked_segment:"
SEGMENT_NAMESPACE_SEP = "::"
VECTOR_PREP_OPERATION_CODE = "vector_prep"
FILE_PREPARATION_TASK_TYPE = "file_preparation"

# Execution-only alias — not a component registry extension.
EXECUTION_PRICED_OP_RUNTIME_ALIASES: dict[str, str] = {
    "return_face_bonding": "modelare_cant",
}

BLOCKED_MISSING_SOLD_SCOPE = "blocked_missing_sold_scope"


@dataclass(frozen=True)
class ExecutionSoldScopeContext:
    """Frozen sold-scope view for execution task/operation filtering."""

    filter_enabled: bool
    mode: str = "full_product"
    sold_runtime_modules: frozenset[str] = frozenset()
    canonical_sold_modules: frozenset[str] = frozenset()
    linked_logo_tasks_allowed: bool = True
    block_preview: bool = False
    block_reason: str | None = None


def _text(value: str | None) -> str:
    return str(value or "").strip()


def read_execution_sold_scope(snapshot: OrderSnapshotV2) -> ExecutionSoldScopeContext:
    """Read frozen order scope — never calls offer_scope resolver."""
    offer_scope = snapshot.offer_scope_snapshot
    if offer_scope is None or offer_scope.use_legacy or offer_scope.mode == "full_product":
        return ExecutionSoldScopeContext(
            filter_enabled=False,
            mode="full_product" if offer_scope is None else offer_scope.mode,
            linked_logo_tasks_allowed=True,
        )

    sold_runtime = frozenset(
        module for module in (offer_scope.resolved_runtime_sold_modules or []) if _text(module)
    )
    canonical_sold = frozenset(
        code for code in (offer_scope.sold_modules or []) if _text(code)
    )
    if not sold_runtime:
        return ExecutionSoldScopeContext(
            filter_enabled=True,
            mode="component_subset",
            sold_runtime_modules=frozenset(),
            canonical_sold_modules=canonical_sold,
            linked_logo_tasks_allowed=False,
            block_preview=True,
            block_reason=BLOCKED_MISSING_SOLD_SCOPE,
        )

    return ExecutionSoldScopeContext(
        filter_enabled=True,
        mode="component_subset",
        sold_runtime_modules=sold_runtime,
        canonical_sold_modules=canonical_sold,
        linked_logo_tasks_allowed=False,
    )


def is_linked_segment_task_rule(rule: ProductAggregateTaskRule) -> bool:
    trigger = _text(rule.trigger_condition)
    return trigger.lower().startswith(LINKED_SEGMENT_TRIGGER_PREFIX)


def is_linked_segment_operation(operation: ProductAggregateOperation) -> bool:
    component_ref = _text(operation.component_ref)
    if SEGMENT_NAMESPACE_SEP in component_ref:
        return True
    if component_ref.lower().startswith(LINKED_SEGMENT_TRIGGER_PREFIX):
        return True
    return _text(operation.provenance) == "linked_module" and SEGMENT_NAMESPACE_SEP in component_ref


def is_vector_prep_task_rule(rule: ProductAggregateTaskRule) -> bool:
    task_type = _text(rule.task_type).lower()
    priced_op = _text(rule.priced_operation)
    task_name = _text(rule.task_name)
    if task_type == FILE_PREPARATION_TASK_TYPE and priced_op == VECTOR_PREP_OPERATION_CODE:
        return True
    return task_name == "vector_prep" and priced_op == VECTOR_PREP_OPERATION_CODE


def is_vector_prep_operation(operation: ProductAggregateOperation) -> bool:
    return _text(operation.operation_code) == VECTOR_PREP_OPERATION_CODE


def effective_runtime_module_for_task_rule(rule: ProductAggregateTaskRule) -> str | None:
    priced_op = _text(rule.priced_operation)
    if priced_op in EXECUTION_PRICED_OP_RUNTIME_ALIASES:
        return EXECUTION_PRICED_OP_RUNTIME_ALIASES[priced_op]
    mini = led_runtime_module_bucket(_text(rule.mini_module_code) or None)
    if mini:
        return mini
    return None


def effective_runtime_module_for_operation(operation: ProductAggregateOperation) -> str | None:
    op_code = _text(operation.operation_code)
    if op_code in EXECUTION_PRICED_OP_RUNTIME_ALIASES:
        return EXECUTION_PRICED_OP_RUNTIME_ALIASES[op_code]
    mini = led_runtime_module_bucket(_text(operation.mini_module_code) or None)
    if mini:
        return mini
    return None


def _led_subscope_allows_task_rule(
    rule: ProductAggregateTaskRule,
    *,
    ctx: ExecutionSoldScopeContext,
) -> bool:
    sold_led = partial_led_subscope_filter(ctx.canonical_sold_modules)
    if sold_led is None or "sistem_led" not in ctx.sold_runtime_modules:
        return True
    sub = task_rule_led_subscope(
        priced_operation=rule.priced_operation,
        task_name=rule.task_name,
    )
    return led_subscope_row_allowed(sub, sold_led_subscopes=sold_led)


def _led_subscope_allows_operation(
    operation: ProductAggregateOperation,
    *,
    ctx: ExecutionSoldScopeContext,
) -> bool:
    from services.offer_scope_led_subscope_service import operation_led_subscope

    sold_led = partial_led_subscope_filter(ctx.canonical_sold_modules)
    if sold_led is None or "sistem_led" not in ctx.sold_runtime_modules:
        return True
    sub = operation_led_subscope(operation.operation_code)
    return led_subscope_row_allowed(sub, sold_led_subscopes=sold_led)


def include_task_rule_for_sold_scope(
    rule: ProductAggregateTaskRule,
    *,
    ctx: ExecutionSoldScopeContext,
) -> bool:
    if not ctx.filter_enabled:
        return True

    if is_linked_segment_task_rule(rule):
        return ctx.linked_logo_tasks_allowed

    if is_vector_prep_task_rule(rule):
        return True

    runtime_module = effective_runtime_module_for_task_rule(rule)
    if runtime_module is None:
        return False

    if runtime_module not in ctx.sold_runtime_modules:
        return False

    return _led_subscope_allows_task_rule(rule, ctx=ctx)


def include_operation_for_sold_scope(
    operation: ProductAggregateOperation,
    *,
    ctx: ExecutionSoldScopeContext,
) -> bool:
    if not ctx.filter_enabled:
        return True

    if is_linked_segment_operation(operation):
        return ctx.linked_logo_tasks_allowed

    if is_vector_prep_operation(operation):
        return True

    runtime_module = effective_runtime_module_for_operation(operation)
    if runtime_module is None:
        return False

    if runtime_module not in ctx.sold_runtime_modules:
        return False

    return _led_subscope_allows_operation(operation, ctx=ctx)
