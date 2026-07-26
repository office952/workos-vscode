"""Effective parity feature flags with production/staging guard."""

from __future__ import annotations

from functools import lru_cache

from core.environment import get_runtime_environment, is_production_environment
from parity.flags import ParityFeatureFlags, get_parity_feature_flags, reset_parity_feature_flags_cache

_RUNTIME_PARITY_ALLOWED = frozenset({"local", "development", "test"})


def _runtime_allows_parity_activation() -> bool:
    return get_runtime_environment() in _RUNTIME_PARITY_ALLOWED


@lru_cache(maxsize=1)
def get_effective_parity_flags() -> ParityFeatureFlags:
    """Return flags forced off outside local/development/test."""
    if not _runtime_allows_parity_activation():
        return ParityFeatureFlags.model_construct()
    return get_parity_feature_flags()


def reset_effective_parity_flags_cache() -> None:
    get_effective_parity_flags.cache_clear()
    reset_parity_feature_flags_cache()


def parity_observe_is_enabled() -> bool:
    return get_effective_parity_flags().parity_observe_enabled


def parity_domain_enabled(flag_attr: str) -> bool:
    flags = get_effective_parity_flags()
    if not flags.parity_observe_enabled:
        return False
    return bool(getattr(flags, flag_attr, False))


def parity_runtime_flags_requested_in_deployed_env() -> bool:
    """True when raw env requests parity flags but runtime is not dev/test."""
    if _runtime_allows_parity_activation():
        return False
    raw = get_parity_feature_flags()
    return raw.parity_observe_enabled or raw.any_subflag_enabled()


def check_parity_production_guard() -> tuple[str, str]:
    """Startup guard helper. Returns (status, message)."""
    if parity_runtime_flags_requested_in_deployed_env():
        env = get_runtime_environment()
        if is_production_environment():
            return (
                "BLOCKED",
                f"Parity runtime flags are set in production environment '{env}' — forced off at runtime",
            )
        return (
            "WARNING",
            f"Parity runtime flags are set in deployed environment '{env}' — forced off at runtime",
        )
    return ("PASS", "Parity runtime flags inactive or allowed for current environment")
