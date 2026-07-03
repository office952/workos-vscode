"""
BUILD 20 — Environment Classification Helper.

Provides a single source of truth for runtime environment classification.
Used by auth hardening, startup safety checks, and config guards.

Env var: APP_ENV (or ENVIRONMENT as fallback)
Allowed values: local, development, staging, production, test
Default: development (safe for local dev, does not grant production trust)
"""

import logging
import os
from typing import Literal

logger = logging.getLogger(__name__)

EnvironmentName = Literal["local", "development", "staging", "production", "test"]

_VALID_ENVIRONMENTS: set[str] = {"local", "development", "staging", "production", "test"}

# Environments where dev auth fallback is permitted
_DEV_AUTH_ALLOWED_ENVIRONMENTS: set[str] = {"local", "development", "test"}


def get_runtime_environment() -> EnvironmentName:
    """
    Determine the current runtime environment.

    Resolution order:
    1. APP_ENV env var
    2. ENVIRONMENT env var (fallback)
    3. Default: "development"
    """
    raw = os.environ.get("APP_ENV", "").strip().lower()
    if not raw:
        raw = os.environ.get("ENVIRONMENT", "").strip().lower()
    if not raw:
        raw = "development"

    if raw not in _VALID_ENVIRONMENTS:
        logger.warning(
            "Unknown APP_ENV value '%s', defaulting to 'development'. "
            "Valid values: %s",
            raw,
            ", ".join(sorted(_VALID_ENVIRONMENTS)),
        )
        return "development"

    return raw  # type: ignore[return-value]


def is_development_environment() -> bool:
    """True for local, development, or test environments."""
    return get_runtime_environment() in {"local", "development", "test"}


def is_staging_environment() -> bool:
    """True only for staging."""
    return get_runtime_environment() == "staging"


def is_production_environment() -> bool:
    """True only for production."""
    return get_runtime_environment() == "production"


def dev_auth_allowed() -> bool:
    """
    Whether dev auth fallback (role=user→admin, dev user creation) is permitted.

    Returns True only in local/development/test environments.
    In staging/production, returns False regardless of any other flag.
    """
    return get_runtime_environment() in _DEV_AUTH_ALLOWED_ENVIRONMENTS