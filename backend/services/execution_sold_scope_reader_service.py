"""Read frozen sold scope from OrderSnapshotV2 for Execution Plan V2 filtering.

Primary: enriched active_scope_snapshot (compiled ActiveScopeResult).
Fallback: thin offer_scope_snapshot + legacy RETURN-CANT hardcode.
Never re-resolves offer_scope, never rebuilds aggregate, never rereads Intake workspace.
"""

from __future__ import annotations

from dataclasses import dataclass

from schemas.active_scope_snapshot import (
    ACTIVE_SCOPE_SNAPSHOT_VERSION,
    KNOWN_ACTIVE_SCOPE_SNAPSHOT_VERSIONS,
    QuoteSnapshotActiveScope,
)
from schemas.order_snapshot_v2 import OrderSnapshotV2
from schemas.product_aggregate import ProductAggregateOperation, ProductAggregateTaskRule
from services.offer_scope_led_subscope_service import (
    led_consumer_row_allowed,
    led_runtime_module_bucket,
    partial_led_subscope_filter,
    task_rule_led_subscope,
)
from services.lighting_mount_consumer_service import (
    LightingMountConsumerDecision,
    resolve_lighting_mount_consumers_from_snapshot,
)

LINKED_SEGMENT_TRIGGER_PREFIX = "linked_segment:"
SEGMENT_NAMESPACE_SEP = "::"
VECTOR_PREP_OPERATION_CODE = "vector_prep"
FILE_PREPARATION_TASK_TYPE = "file_preparation"

# Execution-only alias — not a component registry extension.
EXECUTION_PRICED_OP_RUNTIME_ALIASES: dict[str, str] = {
    "return_face_bonding": "modelare_cant",
    "mounting_template_cnc_cut": "finisaje",
}

BLOCKED_MISSING_SOLD_SCOPE = "blocked_missing_sold_scope"
LEGACY_SCOPE_FALLBACK = "legacy_scope_fallback"
ENRICHED_SCOPE = "enriched"
UNKNOWN_ACTIVE_SCOPE_SNAPSHOT_VERSION = "unknown_active_scope_snapshot_version"


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
    lighting_mount_consumer: LightingMountConsumerDecision | None = None
    composition_excluded_operations: frozenset[str] = frozenset()
    scope_compatibility_mode: str = LEGACY_SCOPE_FALLBACK
    active_scope_snapshot_version: str | None = None


def _text(value: str | None) -> str:
    return str(value or "").strip()


def _enriched_usable(active: QuoteSnapshotActiveScope | None) -> bool:
    if active is None:
        return False
    version = _text(active.active_scope_snapshot_version)
    if version not in KNOWN_ACTIVE_SCOPE_SNAPSHOT_VERSIONS:
        return False
    if active.compatibility_mode != ENRICHED_SCOPE:
        return False
    compiled = active.compiled
    if compiled is None or compiled.use_legacy_full_product:
        return False
    if compiled.errors:
        return False
    return True


def read_execution_sold_scope(snapshot: OrderSnapshotV2) -> ExecutionSoldScopeContext:
    """Read frozen order scope — never calls offer_scope resolver or live workspace."""
    offer_scope = snapshot.offer_scope_snapshot
    active = getattr(snapshot, "active_scope_snapshot", None)

    if offer_scope is None or offer_scope.use_legacy or offer_scope.mode == "full_product":
        mount_consumer = resolve_lighting_mount_consumers_from_snapshot(
            mode="full_product",
            canonical_sold_modules=frozenset(),
        )
        return ExecutionSoldScopeContext(
            filter_enabled=False,
            mode="full_product" if offer_scope is None else offer_scope.mode,
            linked_logo_tasks_allowed=True,
            lighting_mount_consumer=mount_consumer,
            scope_compatibility_mode=LEGACY_SCOPE_FALLBACK,
            active_scope_snapshot_version=(
                active.active_scope_snapshot_version if active is not None else None
            ),
        )

    confirmations = frozenset(
        str(code).strip()
        for code in (getattr(offer_scope, "dependency_confirmations", None) or [])
        if str(code).strip()
    )

    # --- Primary: enriched compiled freeze ---
    if _enriched_usable(active):
        assert active is not None
        compiled = active.compiled
        sold_runtime = frozenset(
            m for m in (compiled.execution_scope_modules or []) if _text(m)
        )
        canonical_sold = frozenset(
            c for c in (compiled.sold_module_codes or []) if _text(c)
        )
        exclusions = frozenset(
            op for op in (compiled.composition_excluded_operations or []) if _text(op)
        )
        mount_consumer = resolve_lighting_mount_consumers_from_snapshot(
            mode=compiled.mode,
            canonical_sold_modules=canonical_sold,
            dependency_confirmations=confirmations,
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
                lighting_mount_consumer=mount_consumer,
                composition_excluded_operations=exclusions,
                scope_compatibility_mode=ENRICHED_SCOPE,
                active_scope_snapshot_version=active.active_scope_snapshot_version,
            )
        return ExecutionSoldScopeContext(
            filter_enabled=True,
            mode="component_subset",
            sold_runtime_modules=sold_runtime,
            canonical_sold_modules=canonical_sold,
            linked_logo_tasks_allowed=False,
            lighting_mount_consumer=mount_consumer,
            composition_excluded_operations=exclusions,
            scope_compatibility_mode=ENRICHED_SCOPE,
            active_scope_snapshot_version=active.active_scope_snapshot_version
            or ACTIVE_SCOPE_SNAPSHOT_VERSION,
        )

    # Unknown enriched version present → fail closed (do not silently drop exclusions).
    if active is not None:
        version = _text(active.active_scope_snapshot_version)
        if version and version not in KNOWN_ACTIVE_SCOPE_SNAPSHOT_VERSIONS:
            canonical_sold = frozenset(
                code for code in (offer_scope.sold_modules or []) if _text(code)
            )
            mount_consumer = resolve_lighting_mount_consumers_from_snapshot(
                mode=offer_scope.mode,
                canonical_sold_modules=canonical_sold,
                dependency_confirmations=confirmations,
            )
            return ExecutionSoldScopeContext(
                filter_enabled=True,
                mode="component_subset",
                sold_runtime_modules=frozenset(),
                canonical_sold_modules=canonical_sold,
                linked_logo_tasks_allowed=False,
                block_preview=True,
                block_reason=UNKNOWN_ACTIVE_SCOPE_SNAPSHOT_VERSION,
                lighting_mount_consumer=mount_consumer,
                scope_compatibility_mode=UNKNOWN_ACTIVE_SCOPE_SNAPSHOT_VERSION,
                active_scope_snapshot_version=version,
            )

    # --- Legacy thin offer_scope fallback ---
    sold_runtime = frozenset(
        module for module in (offer_scope.resolved_runtime_sold_modules or []) if _text(module)
    )
    canonical_sold = frozenset(
        code for code in (offer_scope.sold_modules or []) if _text(code)
    )
    mount_consumer = resolve_lighting_mount_consumers_from_snapshot(
        mode=offer_scope.mode,
        canonical_sold_modules=canonical_sold,
        dependency_confirmations=confirmations,
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
            lighting_mount_consumer=mount_consumer,
            scope_compatibility_mode=LEGACY_SCOPE_FALLBACK,
            active_scope_snapshot_version=(
                active.active_scope_snapshot_version if active is not None else None
            ),
        )

    return ExecutionSoldScopeContext(
        filter_enabled=True,
        mode="component_subset",
        sold_runtime_modules=sold_runtime,
        canonical_sold_modules=canonical_sold,
        linked_logo_tasks_allowed=False,
        lighting_mount_consumer=mount_consumer,
        scope_compatibility_mode=LEGACY_SCOPE_FALLBACK,
        active_scope_snapshot_version=(
            active.active_scope_snapshot_version if active is not None else None
        ),
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
    if "sistem_led" not in ctx.sold_runtime_modules:
        return True
    sold_led = partial_led_subscope_filter(ctx.canonical_sold_modules)
    sub = task_rule_led_subscope(
        priced_operation=rule.priced_operation,
        task_name=rule.task_name,
    )
    return led_consumer_row_allowed(
        row_subscope=sub,
        sold_led_subscopes=sold_led,
        priced_operation=rule.priced_operation,
        task_name=rule.task_name,
        mount_decision=ctx.lighting_mount_consumer,
    )


def _led_subscope_allows_operation(
    operation: ProductAggregateOperation,
    *,
    ctx: ExecutionSoldScopeContext,
) -> bool:
    from services.offer_scope_led_subscope_service import operation_led_subscope

    if "sistem_led" not in ctx.sold_runtime_modules:
        return True
    sold_led = partial_led_subscope_filter(ctx.canonical_sold_modules)
    sub = operation_led_subscope(operation.operation_code)
    return led_consumer_row_allowed(
        row_subscope=sub,
        sold_led_subscopes=sold_led,
        operation_code=operation.operation_code,
        mount_decision=ctx.lighting_mount_consumer,
    )


def _is_composition_excluded(*, priced_or_op_code: str, ctx: ExecutionSoldScopeContext) -> bool:
    code = _text(priced_or_op_code)
    if not code:
        return False
    # Primary: frozen exclusions from enriched ActiveScopeResult
    if ctx.scope_compatibility_mode == ENRICHED_SCOPE and ctx.composition_excluded_operations:
        return code in ctx.composition_excluded_operations
    # Legacy fallback only — RETURN-CANT hardcode for thin snapshots
    return _is_return_only_composition_exclusion_legacy(
        priced_or_op_code=code,
        ctx=ctx,
    )


def _is_return_only_composition_exclusion_legacy(
    *,
    priced_or_op_code: str,
    ctx: ExecutionSoldScopeContext,
) -> bool:
    """LEGACY_FALLBACK: Face↔return bonding not part of RETURN-CANT sold alone."""
    if ctx.scope_compatibility_mode == ENRICHED_SCOPE:
        return False
    if ctx.canonical_sold_modules != frozenset({"RETURN-CANT"}):
        return False
    return _text(priced_or_op_code) == "return_face_bonding"


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

    if _is_composition_excluded(
        priced_or_op_code=_text(rule.priced_operation),
        ctx=ctx,
    ):
        return False

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

    if _is_composition_excluded(
        priced_or_op_code=_text(operation.operation_code),
        ctx=ctx,
    ):
        return False

    runtime_module = effective_runtime_module_for_operation(operation)
    if runtime_module is None:
        return False

    if runtime_module not in ctx.sold_runtime_modules:
        return False

    return _led_subscope_allows_operation(operation, ctx=ctx)
