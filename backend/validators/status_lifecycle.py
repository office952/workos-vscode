"""
Status Lifecycle Validator — Backend enforcement of canonical status transitions.

AUDIT FIX (Task 10): Backend MUST validate status values and transitions,
not just accept any string. This is the single source of truth for allowed
statuses and valid transitions, mirroring the frontend governanceData.ts.

ENFORCEMENT LEVELS:
  - quotes:             FULLY ENFORCED (routers/quotes.py — create + update)
  - orders:             FULLY ENFORCED (routers/orders.py — create + update)
  - intake_requests:    FULLY ENFORCED (routers/intake_requests.py — create + update)
  - execution_plan:     DOCUMENTED/DERIVED — statuses are managed internally via
                        tasks_json state in ExecutionPlanService. The validator is
                        available for use but execution_plan does not expose a
                        top-level mutable "status" column through its REST API.
                        Task-level statuses within tasks_json are validated by
                        ExecutionRealityService.
  - execution_reality:  DOCUMENTED/DERIVED — same as execution_plan. Task statuses
                        are managed by ExecutionRealityService (start_task/end_task).
                        The validator definitions serve as the canonical reference
                        for allowed task states and transitions.

Usage:
    from validators.status_lifecycle import validate_status, validate_transition

    validate_status("quotes", new_status)         # raises ValueError if invalid
    validate_transition("quotes", old_status, new_status)  # raises ValueError if invalid transition
"""

from typing import Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# CANONICAL STATUS DEFINITIONS (mirrors governanceData.ts)
# ---------------------------------------------------------------------------

ENTITY_STATUSES: Dict[str, List[str]] = {
    "quotes": ["draft", "priced", "sent", "viewed", "negotiating", "accepted", "rejected", "expired"],
    "orders": ["created", "confirmed", "locked", "in_execution", "completed", "cancelled"],
    "execution_plan": ["pending", "scheduled", "in_progress", "blocked", "partial_done", "done"],
    "execution_reality": ["created", "assigned", "in_progress", "blocked", "done", "cancelled"],
    "intake_requests": ["new", "in_review", "needs_info", "ready_for_quote", "blocked", "cancelled"],
}

# Valid transitions: (from_status, to_status) pairs
ENTITY_TRANSITIONS: Dict[str, Set[Tuple[str, str]]] = {
    "quotes": {
        ("draft", "priced"),
        ("priced", "sent"),
        ("sent", "viewed"),
        ("viewed", "negotiating"),
        ("negotiating", "accepted"),
        ("negotiating", "rejected"),
        ("sent", "accepted"),
        ("sent", "rejected"),
        ("viewed", "accepted"),
        ("viewed", "rejected"),
        ("sent", "expired"),
        ("viewed", "expired"),
        ("negotiating", "expired"),
        # Quote revision — recalcular commercial → status priced (re-send required)
        ("sent", "priced"),
        ("viewed", "priced"),
        ("negotiating", "priced"),
        # Allow direct transitions for admin/system operations
        ("draft", "sent"),
        ("priced", "accepted"),
    },
    "orders": {
        ("created", "confirmed"),
        ("confirmed", "locked"),
        ("locked", "in_execution"),
        ("in_execution", "completed"),
        ("created", "cancelled"),
        ("confirmed", "cancelled"),
        ("locked", "cancelled"),
        ("in_execution", "cancelled"),
    },
    "execution_plan": {
        ("pending", "scheduled"),
        ("scheduled", "in_progress"),
        ("in_progress", "blocked"),
        ("blocked", "in_progress"),
        ("in_progress", "partial_done"),
        ("partial_done", "done"),
        ("in_progress", "done"),
    },
    "execution_reality": {
        ("created", "assigned"),
        ("assigned", "in_progress"),
        ("in_progress", "blocked"),
        ("blocked", "in_progress"),
        ("in_progress", "done"),
        ("assigned", "cancelled"),
        ("in_progress", "cancelled"),
    },
    "intake_requests": {
        ("new", "in_review"),
        ("in_review", "needs_info"),
        ("needs_info", "in_review"),
        ("in_review", "ready_for_quote"),
        ("new", "cancelled"),
        ("in_review", "cancelled"),
        ("needs_info", "cancelled"),
        ("in_review", "blocked"),
        ("blocked", "in_review"),
    },
}

# ---------------------------------------------------------------------------
# ENFORCEMENT METADATA — documents which entities are actively enforced
# ---------------------------------------------------------------------------

ENFORCEMENT_LEVEL: Dict[str, str] = {
    "quotes": "fully_enforced",
    "orders": "fully_enforced",
    "intake_requests": "fully_enforced",
    "execution_plan": "documented_derived",
    "execution_reality": "documented_derived",
}


def get_valid_statuses(entity: str) -> List[str]:
    """Return the list of valid statuses for an entity type."""
    return ENTITY_STATUSES.get(entity, [])


def get_enforcement_level(entity: str) -> str:
    """Return the enforcement level for an entity type.

    Returns:
        "fully_enforced" — validator is called on every create/update via REST API
        "documented_derived" — statuses are defined here as canonical reference,
            but enforcement happens internally (e.g. via service-layer task state)
        "unknown" — entity not registered
    """
    return ENFORCEMENT_LEVEL.get(entity, "unknown")


def validate_status(entity: str, status: str) -> None:
    """Validate that a status value is allowed for the given entity.

    Args:
        entity: Entity type key (e.g. "quotes", "orders")
        status: The status value to validate

    Raises:
        ValueError: If the status is not in the allowed list for this entity
    """
    valid = ENTITY_STATUSES.get(entity)
    if valid is None:
        # Unknown entity — skip validation (don't block unknown entities)
        return
    if status not in valid:
        raise ValueError(
            f"Invalid status '{status}' for entity '{entity}'. "
            f"Allowed values: {valid}"
        )


def validate_transition(entity: str, from_status: Optional[str], to_status: str) -> None:
    """Validate that a status transition is allowed.

    Args:
        entity: Entity type key
        from_status: Current status (None if creating new entity)
        to_status: Target status

    Raises:
        ValueError: If the transition is not allowed
    """
    # First validate the target status itself
    validate_status(entity, to_status)

    # If creating (no from_status), only validate the target is valid
    if from_status is None:
        return

    # Same status — always allowed (no-op)
    if from_status == to_status:
        return

    transitions = ENTITY_TRANSITIONS.get(entity)
    if transitions is None:
        # Unknown entity — skip transition validation
        return

    if (from_status, to_status) not in transitions:
        raise ValueError(
            f"Invalid status transition '{from_status}' -> '{to_status}' for entity '{entity}'. "
            f"Check governance rules for allowed transitions."
        )