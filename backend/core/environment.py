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


def _raw_runtime_environment() -> str:
    """Return the raw APP_ENV / ENVIRONMENT string (may be empty or invalid)."""
    raw = os.environ.get("APP_ENV", "").strip().lower()
    if not raw:
        raw = os.environ.get("ENVIRONMENT", "").strip().lower()
    return raw


def get_runtime_environment() -> EnvironmentName:
    """
    Determine the current runtime environment.

    Resolution order:
    1. APP_ENV env var
    2. ENVIRONMENT env var (fallback)
    3. Default: "development"

    Unknown / typo values log a warning and fall back to "development" for
    non-auth classification helpers. Auth bypass must use ``dev_auth_allowed()``,
    which denies bypass for unknown values (Wave 8 fail-closed).
    """
    raw = _raw_runtime_environment()
    if not raw:
        return "development"

    if raw not in _VALID_ENVIRONMENTS:
        logger.warning(
            "Unknown APP_ENV value '%s', defaulting to 'development' for "
            "non-auth classification. Dev auth bypass is denied for unknown "
            "values. Valid values: %s",
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
    Whether dev auth fallback (missing credentials → synthetic admin / impersonation)
    is permitted.

    Returns True only when the explicit runtime environment is one of
    local / development / test.

    Fail-closed cases (bypass denied):
    - staging / production
    - missing APP_ENV/ENVIRONMENT is treated as development (local default)
    - unknown / typo APP_ENV values (do not grant development trust)
    - DEBUG has no effect on this gate
    """
    raw = _raw_runtime_environment()
    if raw and raw not in _VALID_ENVIRONMENTS:
        logger.warning(
            "Dev auth bypass denied: unknown APP_ENV value %r (fail-closed)",
            raw,
        )
        return False
    return get_runtime_environment() in _DEV_AUTH_ALLOWED_ENVIRONMENTS