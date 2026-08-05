"""Schema ownership boundaries for Alembic-governed tables.

Production-like and development runtime must not silently create these tables
via ``Base.metadata.create_all``. Schema changes go through Alembic migrations.

Isolated tests may still call ``create_all`` directly (e.g. IsolatedDBFixture)
when explicitly scoped — that path does not use DatabaseManager.create_tables.
"""

from __future__ import annotations

# Tables whose DDL is owned exclusively by Alembic revisions.
# Runtime DatabaseManager.create_tables / repair must skip these.
ALEMBIC_OWNED_TABLES: frozenset[str] = frozenset(
    {
        "execution_task_assignment_transitions",
        "resource_domain_configurations",
        "resource_domain_configuration_transitions",
        "execution_task_schedules",
        "execution_task_schedule_transitions",
        "execution_task_machine_reservations",
        "execution_task_machine_reservation_transitions",
        "execution_task_capacity_allocations",
        "execution_task_capacity_allocation_transitions",
    }
)

RESOURCE_STATE_TABLES: frozenset[str] = frozenset(
    {
        "resource_domain_configurations",
        "resource_domain_configuration_transitions",
        "execution_task_schedules",
        "execution_task_schedule_transitions",
        "execution_task_machine_reservations",
        "execution_task_machine_reservation_transitions",
        "execution_task_capacity_allocations",
        "execution_task_capacity_allocation_transitions",
    }
)

# Canonical non-unique indexes for execution_task_assignment_transitions.
# Single source of truth: Alembic s63 + matching ORM Index names (no Column index=True).
CANONICAL_ASSIGNMENT_TRANSITION_INDEXES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("ix_exec_task_assign_tr_transition_id", ("transition_id",)),
    ("ix_exec_task_assign_tr_plan_id", ("execution_plan_id",)),
    ("ix_exec_task_assign_tr_order_id", ("order_id",)),
    ("ix_exec_task_assign_tr_task_key", ("task_key",)),
    ("ix_exec_task_assign_tr_source", ("source",)),
    (
        "ix_exec_task_assign_tr_plan_task_id",
        ("execution_plan_id", "task_key", "id"),
    ),
)

# Legacy ORM auto-names that may exist on DBs where create_all raced Alembic.
# Equivalent columns; safe normalization = drop these only after Owner GO + backup.
LEGACY_ORM_ASSIGNMENT_TRANSITION_INDEX_NAMES: frozenset[str] = frozenset(
    {
        "ix_execution_task_assignment_transitions_transition_id",
        "ix_execution_task_assignment_transitions_execution_plan_id",
        "ix_execution_task_assignment_transitions_order_id",
        "ix_execution_task_assignment_transitions_task_key",
        "ix_execution_task_assignment_transitions_source",
    }
)
