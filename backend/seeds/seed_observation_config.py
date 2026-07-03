"""Sprint #37 — ExecutionObservationConfig canonical seed.

Idempotent seed for the singleton `execution_observation_config` row
that the `ExecutionObservabilityService` reads to classify divergence
between `ExecutionPlan` and `ExecutionReality`.

Canonical defaults (Sprint #37, locked):

    scope                   = global (implicit — singleton table)
    warning_time_delta_minutes  = 15
    critical_time_delta_minutes = 30
    warning_time_delta_pct      = 10
    critical_time_delta_pct     = 20
    is_active                   = True

Idempotency strategy:

  - If no row exists: INSERT one row with the canonical defaults.
  - If a row already exists with values that match the canonical
    defaults AND `is_active = True`: do nothing (skip).
  - If a row exists but is INACTIVE or has non-canonical values: UPDATE
    the lowest-id row to the canonical defaults and set
    `is_active = True`. Extra duplicate rows (if any) are left alone —
    this seed never deletes; the service already prefers the first
    active row, which after this seed is the canonical one.

Invariants (verified by tests + service contract):

  - This seed writes ONLY to `execution_observation_config`. It never
    touches Orders, ExecutionPlan, ExecutionReality, ProductTemplate,
    MaterialRate, or any cost/quote structure.
  - It is safe to run repeatedly (orchestrator Sprint #23 pattern).
  - It never creates a second singleton row when a valid one exists.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from sqlalchemy import select

from core.database import db_manager
from models.execution_observation_config import ExecutionObservationConfig
import models  # noqa: F401 — ensure all models registered with Base.metadata

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Canonical Sprint #37 defaults — single source of truth.
# ---------------------------------------------------------------------------
CANONICAL_WARNING_MINUTES: float = 15.0
CANONICAL_CRITICAL_MINUTES: float = 30.0
CANONICAL_WARNING_PCT: float = 10.0
CANONICAL_CRITICAL_PCT: float = 20.0
CANONICAL_IS_ACTIVE: bool = True


def _row_matches_canonical(row: ExecutionObservationConfig) -> bool:
    """Return True iff the row already equals the canonical config."""
    return (
        row.warning_time_delta_minutes == CANONICAL_WARNING_MINUTES
        and row.critical_time_delta_minutes == CANONICAL_CRITICAL_MINUTES
        and row.warning_time_delta_pct == CANONICAL_WARNING_PCT
        and row.critical_time_delta_pct == CANONICAL_CRITICAL_PCT
        and bool(row.is_active) is CANONICAL_IS_ACTIVE
    )


async def seed_observation_config() -> Dict[str, Any]:
    """Seed the canonical observation config row. Returns stats dict.

    Stats keys:
      - inserted: 1 if a new row was created, else 0
      - updated:  1 if an existing row was corrected to canonical, else 0
      - skipped:  1 if an existing canonical row was left untouched, else 0
      - active_row_id: id of the row that is now canonical & active
    """
    inserted = 0
    updated = 0
    skipped = 0
    active_row_id = None

    async with db_manager.async_session_maker() as session:
        res = await session.execute(
            select(ExecutionObservationConfig).order_by(
                ExecutionObservationConfig.id.asc()
            )
        )
        rows = list(res.scalars().all())

        if not rows:
            row = ExecutionObservationConfig(
                warning_time_delta_minutes=CANONICAL_WARNING_MINUTES,
                critical_time_delta_minutes=CANONICAL_CRITICAL_MINUTES,
                warning_time_delta_pct=CANONICAL_WARNING_PCT,
                critical_time_delta_pct=CANONICAL_CRITICAL_PCT,
                is_active=CANONICAL_IS_ACTIVE,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            inserted = 1
            active_row_id = row.id
        else:
            head = rows[0]
            if _row_matches_canonical(head):
                skipped = 1
                active_row_id = head.id
            else:
                head.warning_time_delta_minutes = CANONICAL_WARNING_MINUTES
                head.critical_time_delta_minutes = CANONICAL_CRITICAL_MINUTES
                head.warning_time_delta_pct = CANONICAL_WARNING_PCT
                head.critical_time_delta_pct = CANONICAL_CRITICAL_PCT
                head.is_active = CANONICAL_IS_ACTIVE
                await session.commit()
                await session.refresh(head)
                updated = 1
                active_row_id = head.id

    logger.info(
        "Seeded observation_config: inserted=%d updated=%d skipped=%d active_row_id=%s",
        inserted,
        updated,
        skipped,
        active_row_id,
    )
    return {
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "active_row_id": active_row_id,
        "canonical": {
            "warning_time_delta_minutes": CANONICAL_WARNING_MINUTES,
            "critical_time_delta_minutes": CANONICAL_CRITICAL_MINUTES,
            "warning_time_delta_pct": CANONICAL_WARNING_PCT,
            "critical_time_delta_pct": CANONICAL_CRITICAL_PCT,
            "is_active": CANONICAL_IS_ACTIVE,
        },
    }


async def _main() -> None:
    logging.basicConfig(level=logging.INFO)
    await db_manager.init_db()
    stats = await seed_observation_config()
    print(f"[seed_observation_config] {stats}")


if __name__ == "__main__":
    asyncio.run(_main())