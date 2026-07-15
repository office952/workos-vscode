"""FLEX collaboration membership API feature flags.

Separate from parity observe flags. Writes gated; reads remain available.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class FlexMembershipFlags(BaseSettings):
    """Operational flag for Phase 1 membership join/leave writes."""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_file=None,
    )

    # Default True for local/dev; set FLEX_MEMBERSHIP_API_ENABLED=false to disable writes.
    flex_membership_api_enabled: bool = True


@lru_cache(maxsize=1)
def get_flex_membership_flags() -> FlexMembershipFlags:
    return FlexMembershipFlags()


def reset_flex_membership_flags_cache() -> None:
    get_flex_membership_flags.cache_clear()


def is_membership_api_enabled() -> bool:
    return bool(get_flex_membership_flags().flex_membership_api_enabled)
