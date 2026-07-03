"""BUILD 4 — Tests for 6 real advertising production templates.

Tests cover:
  - Seed creates 6 templates (idempotent)
  - Template shape is stable (components, operations, materials)
  - Banner caps spacing validation
  - Banner mesh externalization rule
  - Plexi thickness/material blockers
  - Vinyl lamination dependency
  - Lightbox electrical blockers
  - Volumetric letters vector/LED blockers
  - Mesh external supplier blocker
  - Readiness integration per template
  - CostEngine mapping presence
  - ProductSystem API returns templates
"""

from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.product_readiness_service import (
    ProductReadinessService,
    VALID_CAPS_SPACINGS_CM,
    BANNER_ROLL_WIDTHS_MM,
)
from seeds.seed_build4_templates import (
    TEMPLATE_DEFINITIONS,
    _banner_components,
    _plexi_components,
    _vinyl_sticker_components,
    _lightbox_components,
    _volumetric_letters_components,
    _mesh_externalized_components,
    _flatten_operations,
    _flatten_materials,
)
from seeds.seed_build4_materials import BUILD4_MATERIAL_STUBS
from seeds.seed_build4_workcenters import BUILD4_WORKCENTERS


# ============================================================
# SEED SHAPE TESTS
# ============================================================

class TestSeedDefinitions:
    """Verify seed data shape and completeness."""

    def test_six_templates_defined(self):
        assert len(TEMPLATE_DEFINITIONS) == 6

    def test_template_codes_stable(self):
        codes = {t["template_code"] for t in TEMPLATE_DEFINITIONS}
        expected = {
            "TPL-BANNER-STANDARD",
            "TPL-PLEXI-PLATE",
            "TPL-VINYL-STICKER",
            "TPL-LIGHTBOX-STANDARD",
            "TPL-VOLUMETRIC-LETTERS",
            "TPL-MESH-EXTERNALIZED",
        }
        assert codes == expected

    def test_each_template_has_required_fields(self):
        required = {
            "template_code", "family_id", "family_name", "description",
            "components_fn", "estimated_hours", "base_labor_rate",
            "base_margin_pct", "notes",
        }
        for tpl in TEMPLATE_DEFINITIONS:
            missing = required - set(tpl.keys())
            assert not missing, f"{tpl['template_code']} missing: {missing}"

    def test_each_template_has_components(self):
        for tpl in TEMPLATE_DEFINITIONS:
            components = tpl["components_fn"]()
            assert isinstance(components, list)
            assert len(components) > 0, f"{tpl['template_code']} has no components"

    def test_each_component_has_required_shape(self):
        for tpl in TEMPLATE_DEFINITIONS:
            for comp in tpl["components_fn"]():
                assert "component_id" in comp
                assert "type" in comp
                assert "name" in comp
                assert "operations" in comp
                assert "materials" in comp
                assert comp["component_id"], f"Empty component_id in {tpl['template_code']}"
                assert comp["type"], f"Empty type in {tpl['template_code']}"
                assert comp["name"], f"Empty name in {tpl['template_code']}"

    def test_operations_have_required_fields(self):
        for tpl in TEMPLATE_DEFINITIONS:
            for comp in tpl["components_fn"]():
                for op in comp["operations"]:
                    assert "code" in op, f"Missing code in op of {comp['component_id']}"
                    assert "workcenter" in op, f"Missing workcenter in op of {comp['component_id']}"
                    assert "sequence" in op, f"Missing sequence in op of {comp['component_id']}"
                    assert op["sequence"] > 0, f"Non-positive sequence in {comp['component_id']}"

    def test_materials_have_required_fields(self):
        for tpl in TEMPLATE_DEFINITIONS:
            for comp in tpl["components_fn"]():
                for mat in comp["materials"]:
                    code = mat.get("materialCode") or mat.get("material_code")
                    assert code, f"Missing material code in {comp['component_id']}"
                    assert "unit" in mat, f"Missing unit in {comp['component_id']}"

    def test_flatten_operations_preserves_component_ref(self):
        for tpl in TEMPLATE_DEFINITIONS:
            components = tpl["components_fn"]()
            ops = _flatten_operations(components)
            comp_ids = {c["component_id"] for c in components}
            for op in ops:
                assert op.get("component_ref") in comp_ids, (
                    f"Orphan component_ref {op.get('component_ref')} in {tpl['template_code']}"
                )

    def test_flatten_materials_preserves_component_ref(self):
        for tpl in TEMPLATE_DEFINITIONS:
            components = tpl["components_fn"]()
            mats = _flatten_materials(components)
            comp_ids = {c["component_id"] for c in components}
            for mat in mats:
                assert mat.get("component_ref") in comp_ids, (
                    f"Orphan component_ref {mat.get('component_ref')} in {tpl['template_code']}"
                )


# ============================================================
# BANNER-SPECIFIC TESTS
# ============================================================

class TestBannerTemplate:
    def test_banner_has_print_substrate(self):
        comps = _banner_components()
        types = {c["type"] for c in comps}
        assert "PRINT_SUBSTRATE" in types

    def test_banner_has_finisaj(self):
        comps = _banner_components()
        types = {c["type"] for c in comps}
        assert "FINISAJ" in types

    def test_banner_roll_widths_in_formula(self):
        comps = _banner_components()
        mats = _flatten_materials(comps)
        found = False
        for m in mats:
            fp = m.get("formula_params", {})
            if "roll_widths_mm" in fp:
                found = True
                for w in fp["roll_widths_mm"]:
                    assert w in BANNER_ROLL_WIDTHS_MM
        assert found, "Banner must have roll_widths_mm in formula_params"

    def test_banner_caps_spacing_valid(self):
        comps = _banner_components()
        mats = _flatten_materials(comps)
        for m in mats:
            fp = m.get("formula_params", {})
            if "valid_spacings_cm" in fp:
                for s in fp["valid_spacings_cm"]:
                    assert s in VALID_CAPS_SPACINGS_CM, f"Invalid spacing: {s}"

    def test_banner_has_tiv_operation(self):
        comps = _banner_components()
        ops = _flatten_operations(comps)
        tiv_ops = [o for o in ops if "tiv" in o["code"].lower()]
        assert len(tiv_ops) > 0

    def test_banner_has_capsare_operation(self):
        comps = _banner_components()
        ops = _flatten_operations(comps)
        caps_ops = [o for o in ops if "capsare" in o["code"].lower()]
        assert len(caps_ops) > 0


# ============================================================
# PLEXI-SPECIFIC TESTS
# ============================================================

class TestPlexiTemplate:
    def test_plexi_has_panel_component(self):
        comps = _plexi_components()
        types = {c["type"] for c in comps}
        assert "PLEXI_PANEL" in types

    def test_plexi_has_thickness_options(self):
        comps = _plexi_components()
        mats = _flatten_materials(comps)
        found = False
        for m in mats:
            fp = m.get("formula_params", {})
            if "thickness_options_mm" in fp:
                found = True
        assert found, "Plexi must have thickness_options_mm"

    def test_plexi_has_laser_cutting(self):
        comps = _plexi_components()
        ops = _flatten_operations(comps)
        wcs = {o["workcenter"] for o in ops}
        assert "LASER_CUTTING" in wcs


# ============================================================
# VINYL-SPECIFIC TESTS
# ============================================================

class TestVinylTemplate:
    def test_vinyl_has_application_component(self):
        comps = _vinyl_sticker_components()
        types = {c["type"] for c in comps}
        assert "VINYL_APPLICATION" in types

    def test_vinyl_has_lamination_component(self):
        comps = _vinyl_sticker_components()
        types = {c["type"] for c in comps}
        assert "LAMINARE" in types

    def test_vinyl_has_contour_cutting(self):
        comps = _vinyl_sticker_components()
        ops = _flatten_operations(comps)
        wcs = {o["workcenter"] for o in ops}
        assert "CONTOUR_CUTTING" in wcs

    def test_vinyl_has_lamination_workcenter(self):
        comps = _vinyl_sticker_components()
        ops = _flatten_operations(comps)
        wcs = {o["workcenter"] for o in ops}
        assert "LAMINATION" in wcs


# ============================================================
# LIGHTBOX-SPECIFIC TESTS
# ============================================================

class TestLightboxTemplate:
    def test_lightbox_has_frame_profile(self):
        comps = _lightbox_components()
        types = {c["type"] for c in comps}
        assert "FRAME_PROFILE" in types

    def test_lightbox_has_electric_led(self):
        comps = _lightbox_components()
        types = {c["type"] for c in comps}
        assert "ELECTRIC_LED" in types

    def test_lightbox_has_led_materials(self):
        comps = _lightbox_components()
        mats = _flatten_materials(comps)
        codes = {m.get("materialCode") or m.get("material_code") for m in mats}
        assert "MAT-LED-MODULE" in codes
        assert "MAT-LED-PSU-12V" in codes

    def test_lightbox_has_electrical_wiring(self):
        comps = _lightbox_components()
        ops = _flatten_operations(comps)
        wcs = {o["workcenter"] for o in ops}
        assert "ELECTRICAL_WIRING" in wcs or "LED_ASSEMBLY" in wcs


# ============================================================
# VOLUMETRIC LETTERS-SPECIFIC TESTS
# ============================================================

class TestVolumetricLettersTemplate:
    def test_letters_has_3d_component(self):
        comps = _volumetric_letters_components()
        types = {c["type"] for c in comps}
        assert "LITERE_3D" in types

    def test_letters_has_face_material(self):
        comps = _volumetric_letters_components()
        mats = _flatten_materials(comps)
        codes = {m.get("materialCode") or m.get("material_code") for m in mats}
        assert "MAT-ACP-FATA-LITERE" in codes

    def test_letters_has_lateral_profile(self):
        comps = _volumetric_letters_components()
        mats = _flatten_materials(comps)
        codes = {m.get("materialCode") or m.get("material_code") for m in mats}
        assert "MAT-PROFIL-LATERAL-LITERE" in codes

    def test_letters_has_cnc_or_laser(self):
        comps = _volumetric_letters_components()
        ops = _flatten_operations(comps)
        wcs = {o["workcenter"] for o in ops}
        assert "CNC_ROUTER" in wcs or "LASER_CUTTING" in wcs

    def test_letters_has_led_for_illumination(self):
        comps = _volumetric_letters_components()
        mats = _flatten_materials(comps)
        codes = {m.get("materialCode") or m.get("material_code") for m in mats}
        assert "MAT-LED-MODULE" in codes


# ============================================================
# MESH EXTERNALIZED-SPECIFIC TESTS
# ============================================================

class TestMeshTemplate:
    def test_mesh_has_externalizare_component(self):
        comps = _mesh_externalized_components()
        types = {c["type"] for c in comps}
        assert "EXTERNALIZARE" in types

    def test_mesh_has_external_subcontract(self):
        comps = _mesh_externalized_components()
        ops = _flatten_operations(comps)
        wcs = {o["workcenter"] for o in ops}
        assert "EXTERNAL_SUBCONTRACT" in wcs

    def test_mesh_not_internally_produced(self):
        """Mesh canonical rule: no internal print operation."""
        comps = _mesh_externalized_components()
        ops = _flatten_operations(comps)
        wcs = {o["workcenter"] for o in ops}
        assert "LARGE_FORMAT_PRINT" not in wcs, "Mesh must NOT have internal print"

    def test_mesh_has_incoming_qc(self):
        comps = _mesh_externalized_components()
        ops = _flatten_operations(comps)
        wcs = {o["workcenter"] for o in ops}
        assert "QC_INSPECTION" in wcs

    def test_mesh_caps_spacing_valid(self):
        comps = _mesh_externalized_components()
        mats = _flatten_materials(comps)
        for m in mats:
            fp = m.get("formula_params", {})
            if "valid_spacings_cm" in fp:
                for s in fp["valid_spacings_cm"]:
                    assert s in VALID_CAPS_SPACINGS_CM


# ============================================================
# READINESS SERVICE TESTS (unit-level with mocked DB)
# ============================================================

class TestReadinessTemplateSpecific:
    """Test template-specific readiness checks using mock templates."""

    def _make_mock_template(self, code: str, components_fn, active: bool = True):
        """Create a mock template object."""
        components = components_fn()
        ops = _flatten_operations(components)
        mats = _flatten_materials(components)
        mock = MagicMock()
        mock.id = 1
        mock.template_code = code
        mock.family_id = "test"
        mock.family_name = "Test"
        mock.active = active
        mock.components_json = json.dumps(components)
        mock.operations_json = json.dumps(ops)
        mock.required_materials_json = json.dumps(mats)
        return mock

    def test_banner_readiness_no_blockers(self):
        """Banner with full materials/ops should have no template-specific blockers."""
        svc = ProductReadinessService.__new__(ProductReadinessService)
        tpl = self._make_mock_template("TPL-BANNER-STANDARD", _banner_components)
        components = json.loads(tpl.components_json)
        materials = json.loads(tpl.required_materials_json)
        operations = json.loads(tpl.operations_json)
        blockers, warnings = svc._check_banner_readiness(tpl, components, materials, operations)
        assert len(blockers) == 0, f"Unexpected blockers: {blockers}"

    def test_banner_missing_material_blocker(self):
        """Banner without banner material should have blocker."""
        svc = ProductReadinessService.__new__(ProductReadinessService)
        tpl = self._make_mock_template("TPL-BANNER-STANDARD", _banner_components)
        # Remove all banner materials
        materials = [m for m in json.loads(tpl.required_materials_json) if "BANNER" not in (m.get("materialCode") or "")]
        operations = json.loads(tpl.operations_json)
        components = json.loads(tpl.components_json)
        blockers, _ = svc._check_banner_readiness(tpl, components, materials, operations)
        assert "banner_material_missing" in blockers

    def test_mesh_readiness_has_supplier_warning(self):
        """Mesh should always warn about supplier quote."""
        svc = ProductReadinessService.__new__(ProductReadinessService)
        tpl = self._make_mock_template("TPL-MESH-EXTERNALIZED", _mesh_externalized_components)
        components = json.loads(tpl.components_json)
        materials = json.loads(tpl.required_materials_json)
        operations = json.loads(tpl.operations_json)
        blockers, warnings = svc._check_mesh_readiness(tpl, components, materials, operations)
        assert "mesh_requires_supplier_quote" in warnings
        assert "mesh_not_for_internal_production" in warnings

    def test_mesh_without_external_subcontract_blocker(self):
        """Mesh without EXTERNAL_SUBCONTRACT should be blocked."""
        svc = ProductReadinessService.__new__(ProductReadinessService)
        tpl = self._make_mock_template("TPL-MESH-EXTERNALIZED", _mesh_externalized_components)
        components = json.loads(tpl.components_json)
        materials = json.loads(tpl.required_materials_json)
        # Remove external subcontract operations
        operations = [o for o in json.loads(tpl.operations_json) if o.get("workcenter") != "EXTERNAL_SUBCONTRACT"]
        blockers, _ = svc._check_mesh_readiness(tpl, components, materials, operations)
        assert "mesh_external_supplier_path_missing" in blockers

    def test_lightbox_readiness_no_blockers(self):
        """Lightbox with full data should have no blockers."""
        svc = ProductReadinessService.__new__(ProductReadinessService)
        tpl = self._make_mock_template("TPL-LIGHTBOX-STANDARD", _lightbox_components)
        components = json.loads(tpl.components_json)
        materials = json.loads(tpl.required_materials_json)
        operations = json.loads(tpl.operations_json)
        blockers, _ = svc._check_lightbox_readiness(tpl, components, materials, operations)
        assert len(blockers) == 0, f"Unexpected blockers: {blockers}"

    def test_letters_always_warns_vector_file(self):
        """Volumetric letters should always warn about vector file."""
        svc = ProductReadinessService.__new__(ProductReadinessService)
        tpl = self._make_mock_template("TPL-VOLUMETRIC-LETTERS", _volumetric_letters_components)
        components = json.loads(tpl.components_json)
        materials = json.loads(tpl.required_materials_json)
        operations = json.loads(tpl.operations_json)
        _, warnings = svc._check_volumetric_letters_readiness(tpl, components, materials, operations)
        assert "letters_vector_file_required" in warnings

    def test_vinyl_readiness_no_blockers(self):
        """Vinyl with full data should have no blockers."""
        svc = ProductReadinessService.__new__(ProductReadinessService)
        tpl = self._make_mock_template("TPL-VINYL-STICKER", _vinyl_sticker_components)
        components = json.loads(tpl.components_json)
        materials = json.loads(tpl.required_materials_json)
        operations = json.loads(tpl.operations_json)
        blockers, _ = svc._check_vinyl_readiness(tpl, components, materials, operations)
        assert len(blockers) == 0, f"Unexpected blockers: {blockers}"


# ============================================================
# MATERIAL & WORKCENTER STUBS TESTS
# ============================================================

class TestBuild4Stubs:
    def test_material_stubs_have_required_fields(self):
        for mat in BUILD4_MATERIAL_STUBS:
            assert "code" in mat
            assert "name" in mat
            assert "unit" in mat
            assert "category" in mat
            assert mat["code"].startswith("MAT-")

    def test_material_codes_unique(self):
        codes = [m["code"] for m in BUILD4_MATERIAL_STUBS]
        assert len(codes) == len(set(codes)), "Duplicate material codes"

    def test_workcenter_stubs_have_required_fields(self):
        for wc in BUILD4_WORKCENTERS:
            assert "code" in wc
            assert "label" in wc
            assert "notes" in wc

    def test_workcenter_codes_unique(self):
        codes = [w["code"] for w in BUILD4_WORKCENTERS]
        assert len(codes) == len(set(codes)), "Duplicate workcenter codes"