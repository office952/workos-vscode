"""INTAKE_V6_MOUNTING_SCOPE_FOUNDATION_V1 — backend mounting scope tests."""

from __future__ import annotations

from schemas.intake_v4 import IntakeV4FinishSetup
from services.intake_v4_finish_truth_service import normalize_intake_v4_finish_setup
from services.intake_v6_offer_scope_live_calc_service import (
    _is_mounting_prep_material_key,
    filter_material_breakdown_by_offer_scope,
)
from services.mounting_scope_service import (
    hydrate_mounting_scope_fields,
    is_mounting_preparation_active,
    is_site_installation_active,
    normalize_mounting_scope,
)
from services.volumetric_conditional_plan_tasks_service import should_include_mounting_template_cnc_in_plan
from services.volumetric_quote_input_policy import normalize_mounting_template_enabled
from services.volumetric_quote_ready_policy import _collect_geometry_blockers
from schemas.intake_v4 import (
    IntakeV4MaterialBreakdownResponse,
    IntakeV4MaterialBreakdownTotals,
    IntakeV4MaterialQuantityRow,
)


def test_legacy_no_mounting_hydrates_to_none() -> None:
    assert normalize_mounting_scope("no_mounting") == "none"


def test_legacy_mounting_included_hydrates_to_site_install() -> None:
    assert normalize_mounting_scope("mounting_included") == "preparation_and_site_installation"


def test_legacy_mounting_external_hydrates_to_prep_only() -> None:
    assert normalize_mounting_scope("mounting_external") == "preparation_only"


def test_missing_scope_with_prep_signals_hydrates_to_prep_only() -> None:
    setup = {"mounting_template_enabled": True, "mounting_template_area_m2": 2.5}
    assert normalize_mounting_scope(None, setup=setup) == "preparation_only"


def test_missing_scope_without_prep_hydrates_to_none() -> None:
    assert normalize_mounting_scope(None, setup={}) == "none"


def test_normalize_persists_v1_scope_on_finish_setup() -> None:
    setup = IntakeV4FinishSetup.model_validate({"mounting_scope": "preparation_only"})
    normalized = normalize_intake_v4_finish_setup(setup)
    assert normalized.mounting_scope == "preparation_only"


def test_hydrate_legacy_mounting_included_sets_site_flag() -> None:
    hydrated = hydrate_mounting_scope_fields({"mounting_scope": "mounting_included"})
    assert hydrated["mounting_scope"] == "preparation_and_site_installation"
    assert hydrated["site_installation_included"] is True


def test_prep_inactive_when_scope_none() -> None:
    assert is_mounting_preparation_active({"mounting_scope": "none"}) is False


def test_site_install_active_only_for_full_scope_and_flag() -> None:
    assert is_site_installation_active({"mounting_scope": "preparation_only"}) is False
    assert is_site_installation_active(
        {"mounting_scope": "preparation_and_site_installation", "site_installation_included": True}
    ) is True
    assert is_site_installation_active(
        {"mounting_scope": "preparation_and_site_installation", "site_installation_included": False}
    ) is False


def test_normalize_mounting_template_disabled_when_scope_none() -> None:
    assert (
        normalize_mounting_template_enabled(
            True,
            mounting_scope="none",
            quote_input={"mounting_scope": "none"},
        )
        is False
    )


def test_readiness_skips_prep_blockers_when_scope_none() -> None:
    blockers = _collect_geometry_blockers(
        {
            "width_mm": 1000,
            "height_mm": 800,
            "letter_face_area_m2": 1.0,
            "letter_perimeter_m": 10,
            "letter_count": 5,
            "depth_mm": 60,
            "mounting_scope": "none",
            "mounting_template_enabled": True,
            "mounting_system": "steel_bars",
        }
    )
    assert "quote_input_missing:mounting_template_area_m2" not in blockers
    assert "quote_input_missing:mounting_bar_profile" not in blockers


def test_plan_excludes_mounting_template_cnc_when_scope_none() -> None:
    qi = {
        "mounting_scope": "none",
        "mounting_template_enabled": True,
        "mounting_template_material_type": "forex",
        "mounting_template_area_m2": 2.5,
    }
    assert should_include_mounting_template_cnc_in_plan(qi) is False


def test_live_calc_filters_mounting_accessories_when_scope_none() -> None:
    payload = {"finish_setup": {"mounting_scope": "none"}}
    breakdown = IntakeV4MaterialBreakdownResponse(
        workspace_id="ws",
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        material_rows=[],
        consumable_rows=[
            IntakeV4MaterialQuantityRow(
                material_key="mounting_accessories_percent",
                display_name="Accesorii",
                category="consumable",
                quantity=1.0,
                unit="pct",
                quantity_source="test",
                quantity_quality="estimate",
                estimated_cost=5.0,
            )
        ],
        operation_rows=[],
        edge_cant_operation_rows=[],
        totals=IntakeV4MaterialBreakdownTotals(
            material_cost_total=5.0,
            estimated_cost_total=5.0,
            currency="EUR",
        ),
    )
    filtered = filter_material_breakdown_by_offer_scope(breakdown, payload_raw=payload, quote_input=payload)
    assert filtered.consumable_rows == []


def test_mounting_prep_material_key_detection() -> None:
    assert _is_mounting_prep_material_key("mounting_accessories_percent") is True
    assert _is_mounting_prep_material_key("plexiglas_face") is False
