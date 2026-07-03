"""Tests for CNC material process profiles and material/operation separation."""

from __future__ import annotations

import pytest

from services.intake_v4_material_breakdown_service import MATERIAL_REGISTRY_CODES
from services.shared_cnc_material_process_profiles import (
    CLIENT_SUPPLIED_MATERIAL_WARNING,
    FOREX_10MM_PROFILE,
    PLEXIGLAS_3MM_PROFILE,
    build_cutting_service_preview_bundle,
    build_material_cost_preview_row,
    get_material_process_profile,
)
from services.shared_cnc_operation_model import (
    CncMaterialSource,
    build_volumetric_letters_cnc_operation_rows,
)


PBL_FACE_ML = 13.6211
PBL_FACE_M2 = 0.5834


class TestMaterialProcessProfiles:
    def test_plexiglas_profile_links_registry_stock_code(self):
        assert PLEXIGLAS_3MM_PROFILE.stock_material_key == MATERIAL_REGISTRY_CODES["plexiglas_face"]
        assert PLEXIGLAS_3MM_PROFILE.stock_mapping_status == "mapped"
        assert PLEXIGLAS_3MM_PROFILE.cutting_passes == 1
        assert PLEXIGLAS_3MM_PROFILE.bevel_default is True

    def test_forex_profile_five_passes_and_stock_field(self):
        assert FOREX_10MM_PROFILE.stock_material_key == MATERIAL_REGISTRY_CODES["forex_backing"]
        assert FOREX_10MM_PROFILE.cutting_passes == 5
        assert FOREX_10MM_PROFILE.owner_pass_override is True
        assert FOREX_10MM_PROFILE.bevel_default is False

    def test_plexiglas_profile_links_cnc_operations(self):
        geometry = {"face_cutting_perimeter_ml": PBL_FACE_ML}
        rows = build_volumetric_letters_cnc_operation_rows(geometry, backing_mode="none")
        for row in rows:
            assert row.material_key == "plexiglas_3mm"
            assert row.consumes_stock_now is False
            assert row.creates_task_now is False

    def test_internal_material_source_creates_material_and_operation_rows(self):
        material_rows, op_rows, warnings = build_cutting_service_preview_bundle(
            material_source=CncMaterialSource.INTERNAL_STOCK,
            material_key="plexiglas_3mm",
            area_m2=PBL_FACE_M2,
            perimeter_ml=PBL_FACE_ML,
            bevel_enabled=True,
        )
        assert len(material_rows) == 1
        assert material_rows[0].stock_material_key == "MAT-ACP-FATA-LITERE"
        assert material_rows[0].consumes_stock_now is False
        assert len(op_rows) >= 2
        assert all(r.consumes_stock_now is False for r in op_rows)

    def test_client_supplied_no_internal_material_row(self):
        material_rows, op_rows, warnings = build_cutting_service_preview_bundle(
            material_source=CncMaterialSource.CLIENT_SUPPLIED,
            material_key="plexiglas_3mm",
            area_m2=PBL_FACE_M2,
            perimeter_ml=PBL_FACE_ML,
        )
        assert material_rows == []
        assert len(op_rows) >= 1
        assert any(CLIENT_SUPPLIED_MATERIAL_WARNING in w for w in warnings)

    def test_missing_inventory_profile_warning_not_fake_stock(self):
        material_rows, op_rows, warnings = build_cutting_service_preview_bundle(
            material_source=CncMaterialSource.INTERNAL_STOCK,
            material_key="unknown_material_xyz",
            area_m2=1.0,
            perimeter_ml=10.0,
        )
        assert material_rows == []
        assert op_rows == []
        assert any("unknown_material_profile" in w for w in warnings)

    def test_missing_operation_rate_no_fake_cost(self):
        _, op_rows, _ = build_cutting_service_preview_bundle(
            material_source=CncMaterialSource.INTERNAL_STOCK,
            material_key="forex_10mm",
            area_m2=0.5,
            perimeter_ml=PBL_FACE_ML,
            configured_rate_eur_per_ml_pass=None,
        )
        for row in op_rows:
            assert row.estimated_cost is None
            assert row.pricing_status == "missing_rate"

    def test_material_and_operation_rows_separate_types(self):
        material_rows, op_rows, _ = build_cutting_service_preview_bundle(
            material_source=CncMaterialSource.INTERNAL_STOCK,
            material_key="plexiglas_3mm",
            area_m2=PBL_FACE_M2,
            perimeter_ml=PBL_FACE_ML,
        )
        assert material_rows[0].row_type == "material"
        assert all(r.operation_type in {"cutting", "bevel"} for r in op_rows)

    def test_material_row_missing_price_warning(self):
        row = build_material_cost_preview_row(
            PLEXIGLAS_3MM_PROFILE,
            PBL_FACE_M2,
            "m2",
            material_source=CncMaterialSource.INTERNAL_STOCK,
        )
        assert row is not None
        assert row.pricing_status == "pending_mapping"
        assert "material_price_missing" in row.warnings
        assert row.consumes_stock_now is False

    def test_operation_rows_carry_machine_skill_or_pending(self):
        geometry = {"face_cutting_perimeter_ml": PBL_FACE_ML}
        rows = build_volumetric_letters_cnc_operation_rows(geometry, backing_mode="none")
        cut = next(r for r in rows if r.key == "cnc_face_cutting_plexiglas_3mm")
        bevel = next(r for r in rows if r.key == "cnc_face_bevel_plexiglas_3mm")
        assert cut.workstation_key == "cnc_router"
        assert cut.required_skill_key == "cnc_operator"
        assert bevel.resource_mapping_status == "pending_mapping"

    def test_get_profile_by_key(self):
        assert get_material_process_profile("plexiglas_3mm") is PLEXIGLAS_3MM_PROFILE
        assert get_material_process_profile("missing") is None
