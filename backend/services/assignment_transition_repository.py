"""Append-only repository for execution_task_assignment_transitions.

Phase A: insert + read only. No update/delete methods by design.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

from models.execution_task_assignment_transition import (
    REASON_NOTE_MAX_LEN,
    ExecutionTaskAssignmentTransition,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class AssignmentTransitionAppendOnlyRepository:
    """Explicit append-only contract — callers must not mutate rows."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def insert_transition(
        self, row: ExecutionTaskAssignmentTransition
    ) -> ExecutionTaskAssignmentTransition:
        if row.reason_note is not None and len(row.reason_note) > REASON_NOTE_MAX_LEN:
            raise ValueError("reason_note_exceeds_max_length")
        self._db.add(row)
        await self._db.flush()
        return row

    async def get_by_transition_id(
        self, transition_id: str
    ) -> Optional[ExecutionTaskAssignmentTransition]:
        result = await self._db.execute(
            select(ExecutionTaskAssignmentTransition).where(
                ExecutionTaskAssignmentTransition.transition_id == transition_id
            )
        )
        return result.scalar_one_or_none()

    async def list_for_task(
        self, *, execution_plan_id: int, task_key: str
    ) -> Sequence[ExecutionTaskAssignmentTransition]:
        result = await self._db.execute(
            select(ExecutionTaskAssignmentTransition)
            .where(
                ExecutionTaskAssignmentTransition.execution_plan_id
                == execution_plan_id,
                ExecutionTaskAssignmentTransition.task_key == task_key,
            )
            .order_by(ExecutionTaskAssignmentTransition.id.asc())
        )
        return list(result.scalars().all())

    # Intentionally absent (append-only proof):
    # - update_transition
    # - delete_transition
    # - clear_history


def repository_public_mutation_methods() -> set[str]:
    """Test helper: public methods that mutate state."""
    names = {
        name
        for name in dir(AssignmentTransitionAppendOnlyRepository)
        if not name.startswith("_")
    }
    return names


APPEND_ONLY_ALLOWED_MUTATORS = {"insert_transition"}
FORBIDDEN_MUTATOR_NAMES = {
    "update_transition",
    "delete_transition",
    "clear_history",
    "remove_transition",
}
