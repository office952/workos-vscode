"""
Sprint #27 — Phase 4 Registry Linkage Validation — contract tests.

Proves the canonical ProductSystemLinkageValidator contract:

  TC_PS_P4_LINK_001: All skills resolving → no PS-BLK-09 in blockers
  TC_PS_P4_LINK_002: Unresolvable skill_code → PS-BLK-09 in blockers
  TC_PS_P4_LINK_003: All workcenters resolving → no PS-BLK-10 in blockers
  TC_PS_P4_LINK_004: Unresolvable workcenter_code → PS-BLK-10 in blockers
  TC_PS_P4_LINK_005: Invalid machine_type → PS-BLK-12 in blockers
  TC_PS_P4_LINK_006: Unresolvable material_code + REGISTRY_MATERIALS_LIVE=false → PS-WRN-02
  TC_PS_P4_LINK_007: Unresolvable material_code + REGISTRY_MATERIALS_LIVE=true → PS-BLK-11
  TC_PS_P4_LINK_008: Unresolvable machine_id + REGISTRY_MACHINES_LIVE=false → PS-WRN-03
  TC_PS_P4_LINK_009: Unresolvable machine_id + REGISTRY_MACHINES_LIVE=true → PS-BLK-12
  TC_PS_P4_CFG_001: REGISTRY_MATERIALS_LIVE defaults to false
  TC_PS_P4_CFG_002: REGISTRY_MACHINES_LIVE defaults to false
  TC_PS_P4_BLK_005: Empty skills for non-exempt task_type → PS-BLK-05
  TC_PS_P4_BLK_006: NULL workcenter + no machine for non-exempt → PS-BLK-06
  TC_PS_P4_MAT_013: Quantity XOR violation → PS-BLK-13
  TC_PS_P4_MAT_014: Quantity ≤ 0 → PS-BLK-14

The test suite drives the validator directly (no HTTP, no DB).
"""

from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from data_models.linkage_contracts import LinkageIssue, LinkageValidationResult
from services.product_system_linkage_validator import (
    CANONICAL_MACHINE_TYPES,
    CANONICAL_MATERIAL_CODES,
    ProductSystemLinkageValidator,
    SKILL_EXEMPT_TASK_TYPES,
    WORKCENTER_EXEMPT_TASK_TYPES,
)
from core.config import settings


# ---------------------------------------------------------------------------
# Helpers — mock skills/workcenters caches
# ---------------------------------------------------------------------------

def _skills_cache_with(*codes: str):
    """Build a skills_cache dict with given codes (all active)."""
    return {
        code: {"skill_code": code, "skill_name": f"Skill {code}", "active": True}
        for code in codes
    }


def _workcenters_cache_with(*codes: str):
    """Build a workcenters_cache dict with given codes (all active)."""
    return {
        code: {
            "workcenter_code": code,
            "workcenter_name": f"WC {code}",
            "operational_status": "active",
            "active": True,
        }
        for code in codes
    }


def _make_task_row(
    task_template_id="tt_test",
    task_type="assembly",
    required_skill_ids=None,
    required_workcenter_id=None,
    required_machine_type=None,
    required_machine_id=None,
    material_requirements=None,
):
    return {
        "task_template_id": task_template_id,
        "task_type": task_type,
        "required_skill_ids": required_skill_ids if required_skill_ids is not None else [],
        "required_workcenter_id": required_workcenter_id,
        "required_machine_type": required_machine_type,
        "required_machine_id": required_machine_id,
        "material_requirements": material_requirements if material_requirements is not None else [],
    }


class TestSkillsValidation(unittest.TestCase):
    """TC_PS_P4_LINK_001, TC_PS_P4_LINK_002, TC_PS_P4_BLK_005."""

    def _validate(self, task_row, skills_cache, workcenters_cache=None):
        """Run _validate_single_task directly (no DB needed)."""
        validator = ProductSystemLinkageValidator.__new__(ProductSystemLinkageValidator)
        return validator._validate_single_task(
            task_row=task_row,
            idx=0,
            skills_cache=skills_cache,
            workcenters_cache=workcenters_cache or {},
        )

    def test_TC_PS_P4_LINK_001_all_skills_resolving(self):
        """All skills resolving → no PS-BLK-09 in blockers."""
        cache = _skills_cache_with("CNC_ROUTING", "ARTCAM")
        task = _make_task_row(
            required_skill_ids=["CNC_ROUTING", "ARTCAM"],
            required_workcenter_id="WC_CNC_ROUTING",
        )
        issues = self._validate(task, cache, _workcenters_cache_with("WC_CNC_ROUTING"))
        blk09 = [i for i in issues if i.code == "PS-BLK-09"]
        self.assertEqual(len(blk09), 0, "Expected no PS-BLK-09 when all skills resolve")

    def test_TC_PS_P4_LINK_002_unresolvable_skill(self):
        """Unresolvable skill_code → PS-BLK-09 in blockers."""
        cache = _skills_cache_with("CNC_ROUTING")
        task = _make_task_row(
            required_skill_ids=["CNC_ROUTING", "NONEXISTENT_SKILL"],
            required_workcenter_id="WC_CNC_ROUTING",
        )
        issues = self._validate(task, cache, _workcenters_cache_with("WC_CNC_ROUTING"))
        blk09 = [i for i in issues if i.code == "PS-BLK-09"]
        self.assertEqual(len(blk09), 1)
        self.assertEqual(blk09[0].severity, "blocker")
        self.assertIn("NONEXISTENT_SKILL", blk09[0].details.get("skill_code", ""))

    def test_TC_PS_P4_BLK_005_empty_skills_non_exempt(self):
        """Empty skills for non-exempt task_type → PS-BLK-05."""
        cache = _skills_cache_with("CNC_ROUTING")
        task = _make_task_row(
            task_type="assembly",
            required_skill_ids=[],
            required_workcenter_id="WC_CNC_ROUTING",
        )
        issues = self._validate(task, cache, _workcenters_cache_with("WC_CNC_ROUTING"))
        blk05 = [i for i in issues if i.code == "PS-BLK-05"]
        self.assertEqual(len(blk05), 1)
        self.assertEqual(blk05[0].severity, "blocker")

    def test_empty_skills_exempt_task_type_no_blocker(self):
        """Empty skills for exempt task_type → no PS-BLK-05."""
        cache = _skills_cache_with("CNC_ROUTING")
        task = _make_task_row(
            task_type="quality_control",
            required_skill_ids=[],
            required_workcenter_id="WC_CNC_ROUTING",
        )
        issues = self._validate(task, cache, _workcenters_cache_with("WC_CNC_ROUTING"))
        blk05 = [i for i in issues if i.code == "PS-BLK-05"]
        self.assertEqual(len(blk05), 0)

    def test_inactive_skill_produces_blocker(self):
        """Inactive skill → PS-BLK-09 with reason=skill_inactive."""
        cache = {"CNC_ROUTING": {"skill_code": "CNC_ROUTING", "skill_name": "CNC", "active": False}}
        task = _make_task_row(
            required_skill_ids=["CNC_ROUTING"],
            required_workcenter_id="WC_CNC_ROUTING",
        )
        issues = self._validate(task, cache, _workcenters_cache_with("WC_CNC_ROUTING"))
        blk09 = [i for i in issues if i.code == "PS-BLK-09"]
        self.assertEqual(len(blk09), 1)
        self.assertEqual(blk09[0].details.get("reason"), "skill_inactive")


class TestWorkcentersValidation(unittest.TestCase):
    """TC_PS_P4_LINK_003, TC_PS_P4_LINK_004, TC_PS_P4_BLK_006."""

    def _validate(self, task_row, workcenters_cache, skills_cache=None):
        validator = ProductSystemLinkageValidator.__new__(ProductSystemLinkageValidator)
        return validator._validate_single_task(
            task_row=task_row,
            idx=0,
            skills_cache=skills_cache or _skills_cache_with("CNC_ROUTING"),
            workcenters_cache=workcenters_cache,
        )

    def test_TC_PS_P4_LINK_003_all_workcenters_resolving(self):
        """All workcenters resolving → no PS-BLK-10."""
        cache = _workcenters_cache_with("WC_CNC_ROUTING")
        task = _make_task_row(
            required_skill_ids=["CNC_ROUTING"],
            required_workcenter_id="WC_CNC_ROUTING",
        )
        issues = self._validate(task, cache)
        blk10 = [i for i in issues if i.code == "PS-BLK-10"]
        self.assertEqual(len(blk10), 0)

    def test_TC_PS_P4_LINK_004_unresolvable_workcenter(self):
        """Unresolvable workcenter_code → PS-BLK-10."""
        cache = _workcenters_cache_with("WC_CNC_ROUTING")
        task = _make_task_row(
            required_skill_ids=["CNC_ROUTING"],
            required_workcenter_id="WC_NONEXISTENT",
        )
        issues = self._validate(task, cache)
        blk10 = [i for i in issues if i.code == "PS-BLK-10"]
        self.assertEqual(len(blk10), 1)
        self.assertEqual(blk10[0].severity, "blocker")

    def test_TC_PS_P4_BLK_006_null_workcenter_no_machine(self):
        """NULL workcenter + no machine for non-exempt → PS-BLK-06."""
        cache = _workcenters_cache_with("WC_CNC_ROUTING")
        task = _make_task_row(
            required_skill_ids=["CNC_ROUTING"],
            required_workcenter_id=None,
            required_machine_type=None,
            required_machine_id=None,
            task_type="assembly",
        )
        issues = self._validate(task, cache)
        blk06 = [i for i in issues if i.code == "PS-BLK-06"]
        self.assertEqual(len(blk06), 1)
        self.assertEqual(blk06[0].severity, "blocker")

    def test_null_workcenter_exempt_task_type_no_blocker(self):
        """NULL workcenter for exempt task_type → no PS-BLK-06."""
        cache = _workcenters_cache_with("WC_CNC_ROUTING")
        task = _make_task_row(
            required_skill_ids=[],
            required_workcenter_id=None,
            task_type="file_preparation",
        )
        issues = self._validate(task, cache)
        blk06 = [i for i in issues if i.code == "PS-BLK-06"]
        self.assertEqual(len(blk06), 0)

    def test_workcenter_not_active_produces_blocker(self):
        """Workcenter with non-active status → PS-BLK-10."""
        cache = {
            "WC_CNC_ROUTING": {
                "workcenter_code": "WC_CNC_ROUTING",
                "workcenter_name": "CNC",
                "operational_status": "maintenance",
                "active": True,
            }
        }
        task = _make_task_row(
            required_skill_ids=["CNC_ROUTING"],
            required_workcenter_id="WC_CNC_ROUTING",
        )
        issues = self._validate(task, cache)
        blk10 = [i for i in issues if i.code == "PS-BLK-10"]
        self.assertEqual(len(blk10), 1)
        self.assertIn("workcenter_not_active", blk10[0].details.get("reason", ""))


class TestMachineTypeValidation(unittest.TestCase):
    """TC_PS_P4_LINK_005."""

    def _validate(self, task_row):
        validator = ProductSystemLinkageValidator.__new__(ProductSystemLinkageValidator)
        return validator._validate_single_task(
            task_row=task_row,
            idx=0,
            skills_cache=_skills_cache_with("CNC_ROUTING"),
            workcenters_cache=_workcenters_cache_with("WC_CNC_ROUTING"),
        )

    def test_TC_PS_P4_LINK_005_invalid_machine_type(self):
        """Invalid machine_type → PS-BLK-12."""
        task = _make_task_row(
            required_skill_ids=["CNC_ROUTING"],
            required_workcenter_id="WC_CNC_ROUTING",
            required_machine_type="INVALID_MACHINE",
        )
        issues = self._validate(task)
        blk12 = [i for i in issues if i.code == "PS-BLK-12"]
        self.assertEqual(len(blk12), 1)
        self.assertEqual(blk12[0].severity, "blocker")

    def test_valid_machine_type_no_blocker(self):
        """Valid machine_type → no PS-BLK-12."""
        task = _make_task_row(
            required_skill_ids=["CNC_ROUTING"],
            required_workcenter_id="WC_CNC_ROUTING",
            required_machine_type="cnc_router",
        )
        issues = self._validate(task)
        blk12 = [i for i in issues if i.code == "PS-BLK-12"]
        self.assertEqual(len(blk12), 0)

    def test_null_machine_type_no_blocker(self):
        """NULL machine_type → no PS-BLK-12 (handled by workcenter check)."""
        task = _make_task_row(
            required_skill_ids=["CNC_ROUTING"],
            required_workcenter_id="WC_CNC_ROUTING",
            required_machine_type=None,
        )
        issues = self._validate(task)
        blk12 = [i for i in issues if i.code == "PS-BLK-12"]
        self.assertEqual(len(blk12), 0)


class TestMaterialsValidation(unittest.TestCase):
    """TC_PS_P4_LINK_006, TC_PS_P4_LINK_007, TC_PS_P4_MAT_013, TC_PS_P4_MAT_014."""

    def _validate(self, task_row):
        validator = ProductSystemLinkageValidator.__new__(ProductSystemLinkageValidator)
        return validator._validate_single_task(
            task_row=task_row,
            idx=0,
            skills_cache=_skills_cache_with("CNC_ROUTING"),
            workcenters_cache=_workcenters_cache_with("WC_CNC_ROUTING"),
        )

    def test_TC_PS_P4_LINK_006_unresolvable_material_registry_not_live(self):
        """Unresolvable material_code + REGISTRY_MATERIALS_LIVE=false → PS-WRN-02."""
        with patch.object(settings, "registry_materials_live", False):
            task = _make_task_row(
                required_skill_ids=["CNC_ROUTING"],
                required_workcenter_id="WC_CNC_ROUTING",
                material_requirements=[
                    {"material_code": "MAT-NONEXISTENT", "quantity": 2, "unit": "pcs"}
                ],
            )
            issues = self._validate(task)
            wrn02 = [i for i in issues if i.code == "PS-WRN-02"]
            self.assertEqual(len(wrn02), 1)
            self.assertEqual(wrn02[0].severity, "warning")

    def test_TC_PS_P4_LINK_007_unresolvable_material_registry_live(self):
        """Unresolvable material_code + REGISTRY_MATERIALS_LIVE=true → PS-BLK-11."""
        with patch.object(settings, "registry_materials_live", True):
            task = _make_task_row(
                required_skill_ids=["CNC_ROUTING"],
                required_workcenter_id="WC_CNC_ROUTING",
                material_requirements=[
                    {"material_code": "MAT-NONEXISTENT", "quantity": 2, "unit": "pcs"}
                ],
            )
            issues = self._validate(task)
            blk11 = [i for i in issues if i.code == "PS-BLK-11"]
            self.assertEqual(len(blk11), 1)
            self.assertEqual(blk11[0].severity, "blocker")

    def test_valid_material_code_no_warning(self):
        """Valid material_code → no PS-WRN-02 or PS-BLK-11."""
        with patch.object(settings, "registry_materials_live", False):
            task = _make_task_row(
                required_skill_ids=["CNC_ROUTING"],
                required_workcenter_id="WC_CNC_ROUTING",
                material_requirements=[
                    {"material_code": "MAT-ACP-3MM", "quantity": 2, "unit": "pcs"}
                ],
            )
            issues = self._validate(task)
            mat_issues = [i for i in issues if i.code in ("PS-WRN-02", "PS-BLK-11")]
            self.assertEqual(len(mat_issues), 0)

    def test_TC_PS_P4_MAT_013_quantity_xor_violation(self):
        """Both quantity_formula and quantity_static → PS-BLK-13."""
        with patch.object(settings, "registry_materials_live", False):
            task = _make_task_row(
                required_skill_ids=["CNC_ROUTING"],
                required_workcenter_id="WC_CNC_ROUTING",
                material_requirements=[
                    {
                        "material_code": "MAT-ACP-3MM",
                        "quantity_formula": "width*height/1000000",
                        "quantity_static": 5,
                        "unit": "pcs",
                    }
                ],
            )
            issues = self._validate(task)
            blk13 = [i for i in issues if i.code == "PS-BLK-13"]
            self.assertEqual(len(blk13), 1)
            self.assertEqual(blk13[0].severity, "blocker")

    def test_TC_PS_P4_MAT_014_quantity_non_positive(self):
        """Quantity ≤ 0 → PS-BLK-14."""
        with patch.object(settings, "registry_materials_live", False):
            task = _make_task_row(
                required_skill_ids=["CNC_ROUTING"],
                required_workcenter_id="WC_CNC_ROUTING",
                material_requirements=[
                    {"material_code": "MAT-ACP-3MM", "quantity_static": -1, "unit": "pcs"}
                ],
            )
            issues = self._validate(task)
            blk14 = [i for i in issues if i.code == "PS-BLK-14"]
            self.assertEqual(len(blk14), 1)
            self.assertEqual(blk14[0].severity, "blocker")

    def test_quantity_zero_produces_blocker(self):
        """Quantity == 0 → PS-BLK-14."""
        with patch.object(settings, "registry_materials_live", False):
            task = _make_task_row(
                required_skill_ids=["CNC_ROUTING"],
                required_workcenter_id="WC_CNC_ROUTING",
                material_requirements=[
                    {"material_code": "MAT-ACP-3MM", "quantity_static": 0, "unit": "pcs"}
                ],
            )
            issues = self._validate(task)
            blk14 = [i for i in issues if i.code == "PS-BLK-14"]
            self.assertEqual(len(blk14), 1)


class TestMachineIdValidation(unittest.TestCase):
    """TC_PS_P4_LINK_008, TC_PS_P4_LINK_009."""

    def _validate(self, task_row):
        validator = ProductSystemLinkageValidator.__new__(ProductSystemLinkageValidator)
        return validator._validate_single_task(
            task_row=task_row,
            idx=0,
            skills_cache=_skills_cache_with("CNC_ROUTING"),
            workcenters_cache=_workcenters_cache_with("WC_CNC_ROUTING"),
        )

    def test_TC_PS_P4_LINK_008_machine_id_registry_not_live(self):
        """Unresolvable machine_id + REGISTRY_MACHINES_LIVE=false → PS-WRN-03."""
        with patch.object(settings, "registry_machines_live", False):
            task = _make_task_row(
                required_skill_ids=["CNC_ROUTING"],
                required_workcenter_id="WC_CNC_ROUTING",
                required_machine_type="cnc_router",
                required_machine_id="MACHINE-001",
            )
            issues = self._validate(task)
            wrn03 = [i for i in issues if i.code == "PS-WRN-03"]
            self.assertEqual(len(wrn03), 1)
            self.assertEqual(wrn03[0].severity, "warning")

    def test_TC_PS_P4_LINK_009_machine_id_registry_live(self):
        """Unresolvable machine_id + REGISTRY_MACHINES_LIVE=true → PS-BLK-12."""
        with patch.object(settings, "registry_machines_live", True):
            task = _make_task_row(
                required_skill_ids=["CNC_ROUTING"],
                required_workcenter_id="WC_CNC_ROUTING",
                required_machine_type="cnc_router",
                required_machine_id="MACHINE-001",
            )
            issues = self._validate(task)
            blk12 = [i for i in issues if i.code == "PS-BLK-12"]
            self.assertEqual(len(blk12), 1)
            self.assertEqual(blk12[0].severity, "blocker")

    def test_null_machine_id_no_warning(self):
        """NULL machine_id → no PS-WRN-03."""
        with patch.object(settings, "registry_machines_live", False):
            task = _make_task_row(
                required_skill_ids=["CNC_ROUTING"],
                required_workcenter_id="WC_CNC_ROUTING",
                required_machine_type="cnc_router",
                required_machine_id=None,
            )
            issues = self._validate(task)
            wrn03 = [i for i in issues if i.code == "PS-WRN-03"]
            self.assertEqual(len(wrn03), 0)


class TestConfigFlags(unittest.TestCase):
    """TC_PS_P4_CFG_001, TC_PS_P4_CFG_002."""

    def test_TC_PS_P4_CFG_001_materials_defaults_true(self):
        """REGISTRY_MATERIALS_LIVE defaults to true (activated via M22 config flip)."""
        self.assertTrue(settings.registry_materials_live)

    def test_TC_PS_P4_CFG_002_machines_defaults_false(self):
        """REGISTRY_MACHINES_LIVE defaults to false."""
        self.assertFalse(settings.registry_machines_live)


class TestLinkageValidationResult(unittest.TestCase):
    """Verify LinkageValidationResult.build invariants."""

    def test_valid_true_when_no_blockers(self):
        result = LinkageValidationResult.build(
            template_id=21,
            template_code="TPL-ACP-LIGHT-ROUTED",
            blockers=[],
            warnings=[
                LinkageIssue(
                    severity="warning",
                    task_template_id="tt_test",
                    path="test",
                    code="PS-WRN-02",
                    message="test warning",
                )
            ],
            registries_consulted=["skills"],
            registries_unavailable=["materials"],
            task_template_count=8,
        )
        self.assertTrue(result.valid)
        self.assertEqual(len(result.missing_links), 1)

    def test_valid_false_when_blockers_present(self):
        blocker = LinkageIssue(
            severity="blocker",
            task_template_id="tt_test",
            path="test",
            code="PS-BLK-09",
            message="test blocker",
        )
        result = LinkageValidationResult.build(
            template_id=21,
            template_code="TPL-ACP-LIGHT-ROUTED",
            blockers=[blocker],
            warnings=[],
            registries_consulted=["skills", "workcenters"],
            registries_unavailable=[],
            task_template_count=8,
        )
        self.assertFalse(result.valid)
        self.assertEqual(len(result.missing_links), 1)

    def test_missing_links_is_union(self):
        """missing_links == blockers + warnings."""
        blocker = LinkageIssue(
            severity="blocker",
            task_template_id="tt_1",
            path="p1",
            code="PS-BLK-09",
            message="b",
        )
        warning = LinkageIssue(
            severity="warning",
            task_template_id="tt_2",
            path="p2",
            code="PS-WRN-02",
            message="w",
        )
        result = LinkageValidationResult.build(
            template_id=21,
            template_code="TPL-ACP-LIGHT-ROUTED",
            blockers=[blocker],
            warnings=[warning],
            registries_consulted=["skills"],
            registries_unavailable=["materials"],
            task_template_count=8,
        )
        self.assertEqual(len(result.missing_links), 2)
        self.assertIn(blocker, result.missing_links)
        self.assertIn(warning, result.missing_links)


class TestCanonicalEnums(unittest.TestCase):
    """Verify canonical enum contents match spec."""

    def test_machine_types_has_11_values(self):
        self.assertEqual(len(CANONICAL_MACHINE_TYPES), 11)

    def test_machine_types_contains_expected(self):
        expected = {"cnc_router", "assembly_station", "led_station", "laser_cutter"}
        self.assertTrue(expected.issubset(CANONICAL_MACHINE_TYPES))

    def test_material_codes_contains_seeded(self):
        """All 9 seeded material codes must be in canonical enum."""
        seeded = {
            "MAT-PROFIL-ALU", "MAT-SURUBURI-GEN", "MAT-ADEZIV-SILICON",
            "MAT-ACP-3MM", "MAT-PLEXI-OPAL-3MM", "MAT-LED-MODULE",
            "MAT-LED-PSU-12V", "MAT-CONSUMABILE-MONTAJ", "MAT-PLEXI-OPAL-10MM",
        }
        self.assertTrue(seeded.issubset(CANONICAL_MATERIAL_CODES))


if __name__ == "__main__":
    unittest.main()