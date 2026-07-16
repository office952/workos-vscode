"""FLEX collaboration feature flags — Phase 1 membership + Phase 2 help/work."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class FlexMembershipFlags(BaseSettings):
    """Operational flags for collaboration membership and Phase 2 work authority."""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_file=None,
    )

    # Phase 1: join/leave membership writes.
    flex_membership_api_enabled: bool = True
    # Phase 2: help lifecycle, pool inclusion, helper session verbs, capability projection.
    flex_collab_phase2_enabled: bool = True


@lru_cache(maxsize=1)
def get_flex_membership_flags() -> FlexMembershipFlags:
    return FlexMembershipFlags()


def reset_flex_membership_flags_cache() -> None:
    get_flex_membership_flags.cache_clear()


def is_membership_api_enabled() -> bool:
    return bool(get_flex_membership_flags().flex_membership_api_enabled)


def is_collab_phase2_enabled() -> bool:
    return bool(get_flex_membership_flags().flex_collab_phase2_enabled)
