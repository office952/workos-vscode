"""Resource domain configuration write boundary (R7).

Application-level append-only for transitions: insert/read only.
Current-state row may be inserted/updated under CAS in the command service.
"""

from __future__ import annotations

from models.resource_domain_configuration import (
    ResourceDomainConfiguration,
    ResourceDomainConfigurationTransition,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class ResourceDomainConfigurationRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_domain_scope(
        self, *, domain: str, application_scope_key: str = "application"
    ) -> ResourceDomainConfiguration | None:
        result = await self._db.execute(
            select(ResourceDomainConfiguration).where(
                ResourceDomainConfiguration.domain == domain,
                ResourceDomainConfiguration.application_scope_key
                == application_scope_key,
            )
        )
        return result.scalar_one_or_none()

    async def get_transition_by_idempotency_key(
        self, idempotency_key: str
    ) -> ResourceDomainConfigurationTransition | None:
        result = await self._db.execute(
            select(ResourceDomainConfigurationTransition).where(
                ResourceDomainConfigurationTransition.idempotency_key
                == idempotency_key
            )
        )
        return result.scalar_one_or_none()

    async def add_configuration(
        self, row: ResourceDomainConfiguration
    ) -> ResourceDomainConfiguration:
        self._db.add(row)
        await self._db.flush()
        return row

    async def add_transition(
        self, row: ResourceDomainConfigurationTransition
    ) -> ResourceDomainConfigurationTransition:
        self._db.add(row)
        await self._db.flush()
        return row

    # Intentionally absent: delete_configuration, update_transition, delete_transition


FORBIDDEN_TRANSITION_MUTATORS = frozenset(
    {
        "update_transition",
        "delete_transition",
        "delete_configuration",
        "clear_history",
    }
)
