"""Local/dev-only User seed for Owner Employee Mobile readiness.

Creates a dev owner User row when the local DB has no OIDC login yet.
Does NOT create Employee, attendance, requests, or payroll rows.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from dependencies.permissions import VALID_ROLES
from models.auth import User
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

DEFAULT_DEV_OWNER_EMAIL = "office@p-media.ro"
DEFAULT_DEV_OWNER_NAME = "Axinte Remus"
DEFAULT_DEV_OWNER_ROLE = "admin"
DEFAULT_DEV_OWNER_USER_ID = "dev-owner-office-p-media-ro"


@dataclass(frozen=True)
class DevOwnerUserSeedConfig:
    email: str
    name: str
    role: str
    user_id: str
    dry_run: bool = True


@dataclass
class DevOwnerUserSeedResult:
    success: bool
    action: str
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    dry_run: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _truthy_env(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes")


def load_dev_owner_user_seed_config_from_env() -> DevOwnerUserSeedConfig:
    return DevOwnerUserSeedConfig(
        email=(os.getenv("WORKOS_DEV_OWNER_EMAIL") or DEFAULT_DEV_OWNER_EMAIL).strip(),
        name=(os.getenv("WORKOS_DEV_OWNER_NAME") or DEFAULT_DEV_OWNER_NAME).strip(),
        role=(os.getenv("WORKOS_DEV_OWNER_ROLE") or DEFAULT_DEV_OWNER_ROLE).strip(),
        user_id=(os.getenv("WORKOS_DEV_OWNER_USER_ID") or DEFAULT_DEV_OWNER_USER_ID).strip(),
        dry_run=_truthy_env("WORKOS_DEV_OWNER_DRY_RUN", default="1"),
    )


def validate_dev_owner_user_seed_config(config: DevOwnerUserSeedConfig) -> Optional[str]:
    if not config.email:
        return "WORKOS_DEV_OWNER_EMAIL is required"
    if not config.name:
        return "WORKOS_DEV_OWNER_NAME is required"
    if not config.user_id:
        return "WORKOS_DEV_OWNER_USER_ID is required"
    if config.role not in VALID_ROLES:
        return f"invalid_role:{config.role}"
    return None


async def _find_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(
        select(User).where(func.lower(User.email) == email.lower())
    )
    return result.scalar_one_or_none()


async def seed_dev_owner_user(
    db: AsyncSession,
    config: DevOwnerUserSeedConfig,
) -> DevOwnerUserSeedResult:
    validation_error = validate_dev_owner_user_seed_config(config)
    if validation_error:
        if validation_error.startswith("invalid_role:"):
            role = validation_error.split(":", 1)[1]
            return DevOwnerUserSeedResult(
                success=False,
                action="error",
                dry_run=config.dry_run,
                error=f"invalid_role:{role}",
            )
        return DevOwnerUserSeedResult(
            success=False,
            action="error",
            dry_run=config.dry_run,
            error=validation_error,
        )

    user_by_id = await db.get(User, config.user_id)
    user_by_email = await _find_user_by_email(db, config.email)

    if user_by_email and user_by_id and user_by_email.id != user_by_id.id:
        return DevOwnerUserSeedResult(
            success=False,
            action="conflict",
            user_id=config.user_id,
            email=config.email,
            role=config.role,
            dry_run=config.dry_run,
            error="email_and_user_id_point_to_different_users",
        )

    if user_by_email:
        if user_by_email.id != config.user_id:
            return DevOwnerUserSeedResult(
                success=False,
                action="conflict",
                user_id=user_by_email.id,
                email=user_by_email.email,
                role=user_by_email.role,
                dry_run=config.dry_run,
                error="email_exists_with_different_user_id",
            )
        updated = False
        if not user_by_email.name and config.name:
            if config.dry_run:
                return DevOwnerUserSeedResult(
                    success=True,
                    action="dry_run_would_update_name",
                    user_id=user_by_email.id,
                    email=user_by_email.email,
                    role=user_by_email.role,
                    dry_run=True,
                )
            user_by_email.name = config.name
            updated = True
        if updated:
            await db.commit()
            await db.refresh(user_by_email)
        return DevOwnerUserSeedResult(
            success=True,
            action="already_exists",
            user_id=user_by_email.id,
            email=user_by_email.email,
            role=user_by_email.role,
            dry_run=config.dry_run,
        )

    if user_by_id:
        return DevOwnerUserSeedResult(
            success=False,
            action="conflict",
            user_id=user_by_id.id,
            email=user_by_id.email,
            role=user_by_id.role,
            dry_run=config.dry_run,
            error="user_id_exists_with_different_email",
        )

    if config.dry_run:
        return DevOwnerUserSeedResult(
            success=True,
            action="dry_run_would_create",
            user_id=config.user_id,
            email=config.email,
            role=config.role,
            dry_run=True,
        )

    user = User(
        id=config.user_id,
        email=config.email,
        name=config.name,
        role=config.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return DevOwnerUserSeedResult(
        success=True,
        action="created",
        user_id=user.id,
        email=user.email,
        role=user.role,
        dry_run=False,
    )
