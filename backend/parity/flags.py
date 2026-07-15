"""Parity feature flags — all default false, isolated from global Settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class ParityFeatureFlags(BaseSettings):
    """Feature flags pentru instrumentarea de paritate — necitite de servicii operaționale în APP-AUTH-04."""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_file=None,
    )

    parity_observe_enabled: bool = False
    competence_parity_enabled: bool = False
    authorization_parity_enabled: bool = False
    workcenter_parity_enabled: bool = False
    resource_parity_enabled: bool = False
    explicit_mapping_tracking_enabled: bool = False
    eligibility_shadow_enabled: bool = False
    execution_surface_parity_enabled: bool = False
    assignment_writer_parity_enabled: bool = False
    session_parity_enabled: bool = False
    attendance_comparison_enabled: bool = False
    legacy_fallback_tracking_enabled: bool = False
    parity_event_emission_enabled: bool = False
    parity_metrics_enabled: bool = False
    parity_persistence_enabled: bool = False
    parity_manager_projection_enabled: bool = False

    def any_subflag_enabled(self) -> bool:
        return any(
            (
                self.competence_parity_enabled,
                self.authorization_parity_enabled,
                self.workcenter_parity_enabled,
                self.resource_parity_enabled,
                self.explicit_mapping_tracking_enabled,
                self.eligibility_shadow_enabled,
                self.execution_surface_parity_enabled,
                self.assignment_writer_parity_enabled,
                self.session_parity_enabled,
                self.attendance_comparison_enabled,
                self.legacy_fallback_tracking_enabled,
                self.parity_event_emission_enabled,
                self.parity_metrics_enabled,
                self.parity_persistence_enabled,
                self.parity_manager_projection_enabled,
            )
        )

    def is_active(self) -> bool:
        return self.parity_observe_enabled and self.any_subflag_enabled()


@lru_cache(maxsize=1)
def get_parity_feature_flags() -> ParityFeatureFlags:
    return ParityFeatureFlags()


def reset_parity_feature_flags_cache() -> None:
    get_parity_feature_flags.cache_clear()
