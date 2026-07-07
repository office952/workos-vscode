"""Tests for shared CNC operation preview model."""

from __future__ import annotations

import pytest

from services.shared_cnc_operation_model import (
    CLIENT_MATERIAL_CNC_WARNINGS,
    FOREX_10MM_CUTTING_PASSES_OWNER,
    CncMaterialSource,
    build_cutting_service_cnc_operation_rows,
    build_volumetric_letters_cnc_operation_rows,
    resolve_volumetric_backing_mode,
)


PBL_FACE_ML = 13.6211


@pytest.fixture
def pbl_geometry() -> dict:
    return {
        "face_cutting_perimeter_ml": PBL_FACE_ML,
        "cnc_cutting_perimeter_ml": PBL_FACE_ML,
        "led_perimeter_ml": 11.6299,
        "return_material_perimeter_ml": 15.4672,
    }


class TestVolumetricLettersCncRows:
    def test_face_cutting_and_mandatory_bevel_rows(self, pbl_geometry):
        rows = build_volumetric_letters_cnc_operation_rows(pbl_geometry, backing_mode="none")
        keys = [r.key for r in rows]
        assert "cnc_face_cutting_plexiglas_3mm" in keys
        assert "cnc_face_bevel_plexiglas_3mm" in keys
        cut = next(r for r in rows if r.key == "cnc_face_cutting_plexiglas_3mm")
        bevel = next(r for r in rows if r.key == "cnc_face_bevel_plexiglas_3mm")
        assert cut.display_name == "Debitare CNC față Plexiglas 3 mm"
        assert bevel.display_name == "Șanfren CNC față Plexiglas 3 mm"
        assert cut.quantity == pytest.approx(PBL_FACE_ML, rel=1e-4)
        assert bevel.quantity == pytest.approx(PBL_FACE_ML, rel=1e-4)
        assert cut.passes == 1
        assert bevel.passes == 1
        assert cut.operation_type == "cutting"
        assert bevel.operation_type == "bevel"

    def test_plexiglas_label_explicit(self, pbl_geometry):
        rows = build_volumetric_letters_cnc_operation_rows(pbl_geometry, backing_mode="none")
        cut = next(r for r in rows if r.key == "cnc_face_cutting_plexiglas_3mm")
        assert cut.material_name == "Plexiglas 3 mm"
        assert cut.thickness_mm == 3.0

    def test_forex_backing_three_passes_without_bevel(self, pbl_geometry):
        rows = build_volumetric_letters_cnc_operation_rows(
            pbl_geometry,
            backing_mode="forex_10_no_bevel",
        )
        back = next(r for r in rows if r.key == "cnc_backing_cutting_forex_10mm")
        assert back.passes == FOREX_10MM_CUTTING_PASSES_OWNER == 3
        assert back.owner_pass_override is True
        assert back.operation_equivalent_quantity == pytest.approx(PBL_FACE_ML * 3, rel=1e-4)
        assert "cnc_backing_bevel_forex_10mm" not in [r.key for r in rows]

    def test_backing_bevel_only_when_selected(self, pbl_geometry):
        with_bevel = build_volumetric_letters_cnc_operation_rows(
            pbl_geometry,
            backing_mode="forex_10_with_bevel",
        )
        assert "cnc_backing_bevel_forex_10mm" in [r.key for r in with_bevel]
        bevel = next(r for r in with_bevel if r.key == "cnc_backing_bevel_forex_10mm")
        assert bevel.passes == 2
        assert bevel.operation_equivalent_quantity == pytest.approx(PBL_FACE_ML * 2, rel=1e-4)

    def test_face_cutting_production_resource_binding(self, pbl_geometry):
        rows = build_volumetric_letters_cnc_operation_rows(pbl_geometry, backing_mode="none")
        cut = next(r for r in rows if r.key == "cnc_face_cutting_plexiglas_3mm")
        assert cut.required_machine_key == "MCH-CNC-4020"
        assert cut.machine_type == "cnc_router"
        assert cut.workstation_key == "cnc_router"
        assert cut.required_skill_key == "cnc_operator"
        assert cut.registry_skill_code == "SK_CNC_OPERATOR"
        assert cut.operation_catalog_key == "face_and_backing_cnc_cut"
        assert cut.dossier_operation_key == "face_cnc_cut"
        assert cut.production_task_type == "cnc_routing"
        assert cut.resource_mapping_status == "mapped"

    def test_face_bevel_pending_catalog_mapping(self, pbl_geometry):
        rows = build_volumetric_letters_cnc_operation_rows(pbl_geometry, backing_mode="none")
        bevel = next(r for r in rows if r.key == "cnc_face_bevel_plexiglas_3mm")
        assert bevel.resource_mapping_status == "pending_mapping"
        assert "operation_catalog_key" in bevel.mapping_gaps
        assert bevel.workstation_key == "cnc_router"
        assert bevel.required_skill_key == "cnc_operator"

    def test_cnc_rows_not_material_rows(self, pbl_geometry):
        rows = build_volumetric_letters_cnc_operation_rows(pbl_geometry, backing_mode="none")
        for row in rows:
            assert row.operation_type in {"cutting", "bevel"}
            assert row.unit == "ml"

    def test_missing_rate_does_not_invent_cost(self, pbl_geometry):
        rows = build_volumetric_letters_cnc_operation_rows(
            pbl_geometry,
            backing_mode="forex_10_no_bevel",
            configured_rate_eur_per_ml_pass=None,
        )
        for row in rows:
            assert row.estimated_cost is None
            assert row.unit_price is None
            assert row.pricing_status == "missing_rate"

    def test_configured_rate_preview_only_when_provided(self, pbl_geometry):
        rows = build_volumetric_letters_cnc_operation_rows(
            pbl_geometry,
            backing_mode="none",
            configured_rate_eur_per_ml_pass=1.5,
        )
        cut = next(r for r in rows if r.key == "cnc_face_cutting_plexiglas_3mm")
        assert cut.pricing_status == "configured_rate_preview"
        assert cut.estimated_cost == pytest.approx(PBL_FACE_ML * 1.5, rel=1e-4)


class TestCuttingServiceContract:
    def test_client_material_warnings(self):
        rows, warnings = build_cutting_service_cnc_operation_rows(
            material_source=CncMaterialSource.CLIENT_SUPPLIED,
            perimeter_ml=10.0,
            thickness_mm=3.0,
            material_family="plexiglas",
            material_name="Plexiglas 3 mm",
        )
        assert len(rows) >= 1
        assert any("nu se consumă stoc intern" in w for w in warnings)
        assert len(warnings) == len(CLIENT_MATERIAL_CNC_WARNINGS)

    def test_client_material_no_stock_cost_in_rows(self):
        rows, _ = build_cutting_service_cnc_operation_rows(
            material_source=CncMaterialSource.CLIENT_SUPPLIED,
            perimeter_ml=5.0,
            thickness_mm=10.0,
            material_family="forex",
            material_name="Forex 10 mm",
            passes_override=5,
            owner_pass_override=True,
        )
        assert all(r.estimated_cost is None for r in rows)


class TestBackingModeResolver:
    def test_modes(self):
        assert resolve_volumetric_backing_mode(backing_confirmed=False, back_bevel_enabled=False) == "none"
        assert resolve_volumetric_backing_mode(backing_confirmed=True, back_bevel_enabled=False) == "forex_10_no_bevel"
        assert resolve_volumetric_backing_mode(backing_confirmed=True, back_bevel_enabled=True) == "forex_10_with_bevel"
