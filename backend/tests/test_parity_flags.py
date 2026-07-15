"""Parity feature flag tests."""

from __future__ import annotations

import os

import pytest

from parity.flags import ParityFeatureFlags, get_parity_feature_flags, reset_parity_feature_flags_cache


@pytest.fixture(autouse=True)
def _clear_flag_cache(monkeypatch):
    reset_parity_feature_flags_cache()
    monkeypatch.delenv("PARITY_OBSERVE_ENABLED", raising=False)
    monkeypatch.delenv("COMPETENCE_PARITY_ENABLED", raising=False)
    yield
    reset_parity_feature_flags_cache()


def test_all_flags_default_false():
    flags = ParityFeatureFlags()
    assert flags.parity_observe_enabled is False
    assert flags.competence_parity_enabled is False
    assert flags.authorization_parity_enabled is False
    assert flags.workcenter_parity_enabled is False
    assert flags.resource_parity_enabled is False
    assert flags.explicit_mapping_tracking_enabled is False
    assert flags.eligibility_shadow_enabled is False
    assert flags.execution_surface_parity_enabled is False
    assert flags.assignment_writer_parity_enabled is False
    assert flags.session_parity_enabled is False
    assert flags.attendance_comparison_enabled is False
    assert flags.legacy_fallback_tracking_enabled is False
    assert flags.parity_event_emission_enabled is False
    assert flags.parity_metrics_enabled is False
    assert flags.parity_persistence_enabled is False
    assert flags.parity_manager_projection_enabled is False


def test_master_flag_does_not_activate_subflags(monkeypatch):
    monkeypatch.setenv("PARITY_OBSERVE_ENABLED", "true")
    reset_parity_feature_flags_cache()
    flags = get_parity_feature_flags()
    assert flags.parity_observe_enabled is True
    assert flags.any_subflag_enabled() is False
    assert flags.is_active() is False


def test_true_false_parsing(monkeypatch):
    monkeypatch.setenv("COMPETENCE_PARITY_ENABLED", "true")
    monkeypatch.setenv("AUTHORIZATION_PARITY_ENABLED", "false")
    reset_parity_feature_flags_cache()
    flags = get_parity_feature_flags()
    assert flags.competence_parity_enabled is True
    assert flags.authorization_parity_enabled is False


def test_active_requires_master_and_subflag(monkeypatch):
    monkeypatch.setenv("PARITY_OBSERVE_ENABLED", "true")
    monkeypatch.setenv("ELIGIBILITY_SHADOW_ENABLED", "1")
    reset_parity_feature_flags_cache()
    flags = get_parity_feature_flags()
    assert flags.is_active() is True
