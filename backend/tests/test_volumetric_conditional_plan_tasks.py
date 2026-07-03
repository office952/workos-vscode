"""Conditional volumetric execution plan task filtering — TPL-VOLUMETRIC-LETTERS."""

from __future__ import annotations

import os
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from services.volumetric_conditional_plan_tasks_service import (  # noqa: E402
    FACE_VINYL_PROCESS_ID,
    ILLUMINATION_PROCESS_IDS,
    MOUNTING_TEMPLATE_CNC_PROCESS_ID,
    PAINTING_PROCESS_ID,
    PACKAGING_PROCESS_ID,
    QC_DISPLAY_NAME,
    QC_PROCESS_ID,
    apply_dynamic_volumetric_assembly_dependencies,
    apply_volumetric_conditional_plan_from_snapshot,
    apply_volumetric_qc_taxonomy_to_plan_tasks,
    finalize_volumetric_plan_dependencies,
    filter_volumetric_conditional_plan_tasks,
    is_direct_mounting_in_plan,
    prune_orphan_plan_dependencies,
    resequence_plan_task_ids,
    should_include_illumination_in_plan,
    should_include_mounting_template_cnc_in_plan,
    should_include_packaging_in_plan,
)
from services.volumetric_face_vinyl_service import FACE_VINYL_DISPLAY_NAME  # noqa: E402

BASE_QUOTE_INPUT = {
    "width_mm": 4800,
    "height_mm": 600,
    "depth_mm": 60,
    "letter_face_area_m2": 2.88,
    "letter_perimeter_m": 18.0,
    "letter_count": 9,
    "return_depth_mm": 60,
    "face_finish_type": "none",
    "mounting_system": "direct_wall",
}

ILLUMINATED_QUOTE_INPUT = {
    **BASE_QUOTE_INPUT,
    "illumination_type": "frontlit",
    "lighting_system_type": "led_modules",
    "led_module_count": 180,
    "selected_psu_watts": 100,
}

FACE_VINYL_QUOTE_INPUT = {
    **BASE_QUOTE_INPUT,
    "face_finish_type": "oracal_651",
    "face_vinyl_color_code": "651-020",
    "face_vinyl_roll_width_mm": 1260,
}

FOREX_TEMPLATE_QUOTE_INPUT = {
    **BASE_QUOTE_INPUT,
    "mounting_template_enabled": True,
    "mounting_template_material_type": "forex",
    "mounting_template_area_m2": 2.88,
}

PAPER_TEMPLATE_QUOTE_INPUT = {
    **BASE_QUOTE_INPUT,
    "mounting_template_enabled": True,
    "mounting_template_material_type": "paper",
    "mounting_template_area_m2": 2.88,
}

PAINT_QUOTE_INPUT = {
    **BASE_QUOTE_INPUT,
    "volume_finish": "paint_after_face_miter_bond",
    "paint_tube_count": 3,
}


def _full_volumetric_plan_tasks():
    return [
        {"task_id": "T-001", "process_id": "vector_prep", "display_name": "Verificare grafică", "estimated_time_minutes": 10},
        {"task_id": "T-002", "process_id": "face_cnc_cut", "display_name": "Debitare față", "estimated_time_minutes": 20},
        {"task_id": "T-003", "process_id": FACE_VINYL_PROCESS_ID, "display_name": "Colantare", "estimated_time_minutes": 15},
        {"task_id": "T-004", "process_id": "side_forming", "display_name": "Modelare canturi", "estimated_time_minutes": 25},
        {"task_id": "T-005", "process_id": "return_face_bonding", "display_name": "Lipire canturi", "estimated_time_minutes": 20},
        {"task_id": "T-006", "process_id": "back_cut", "display_name": "Debitare spate", "estimated_time_minutes": 18},
        {"task_id": "T-007", "process_id": "led_install_letters", "display_name": "Montaj LED", "estimated_time_minutes": 30},
        {"task_id": "T-008", "process_id": "electrical_letters", "display_name": "Cablare", "estimated_time_minutes": 12},
        {"task_id": "T-009", "process_id": MOUNTING_TEMPLATE_CNC_PROCESS_ID, "display_name": "CNC șablon", "estimated_time_minutes": 8},
        {"task_id": "T-010", "process_id": PAINTING_PROCESS_ID, "display_name": "Vopsire", "estimated_time_minutes": 22},
        {"task_id": "T-011", "process_id": "assembly_letters", "display_name": "Asamblare", "estimated_time_minutes": 60},
        {"task_id": "T-012", "process_id": "qc_letters", "display_name": "QC", "estimated_time_minutes": 15},
        {"task_id": "T-013", "process_id": "packaging_letters", "display_name": "Ambalare", "estimated_time_minutes": 10},
    ]


def _snapshot(quote_input=None, **extra):
    snap = {
        "product_definition": {"product_id": "TPL-VOLUMETRIC-LETTERS"},
        "quote_input": dict(quote_input or {}),
    }
    snap.update(extra)
    return snap


DIRECT_MOUNT_SNAPSHOT = _snapshot(BASE_QUOTE_INPUT, delivery_type="delivery_install")
PICKUP_SNAPSHOT = _snapshot({**BASE_QUOTE_INPUT, "delivery_type": "pickup"})


def _process_ids(tasks):
    return [t.get("process_id") for t in tasks if isinstance(t, dict)]


def _task_ids(tasks):
    return [t.get("task_id") for t in tasks if isinstance(t, dict)]


def _all_deps_valid(tasks):
    valid = {t["task_id"] for t in tasks if isinstance(t, dict)}
    for t in tasks:
        if not isinstance(t, dict):
            continue
        for dep in t.get("depends_on_task_ids") or []:
            if dep not in valid:
                return False
    return True


class TestIlluminationPlanPolicy(unittest.TestCase):
    def test_no_explicit_signal_omits_led(self):
        self.assertFalse(should_include_illumination_in_plan({}))
        self.assertFalse(should_include_illumination_in_plan(None))

    def test_explicit_none_omits_led(self):
        self.assertFalse(
            should_include_illumination_in_plan(
                {"illumination_type": "none", "lighting_system_type": "none"}
            )
        )

    def test_explicit_frontlit_includes_led(self):
        self.assertTrue(
            should_include_illumination_in_plan(
                {"illumination_type": "frontlit", "lighting_system_type": "led_modules"}
            )
        )


class TestMountingTemplatePlanPolicy(unittest.TestCase):
    def test_no_signal_omits_forex_cnc(self):
        self.assertFalse(should_include_mounting_template_cnc_in_plan({}))

    def test_paper_template_omits_forex_cnc(self):
        self.assertFalse(should_include_mounting_template_cnc_in_plan(PAPER_TEMPLATE_QUOTE_INPUT))

    def test_forex_template_includes_cnc(self):
        self.assertTrue(should_include_mounting_template_cnc_in_plan(FOREX_TEMPLATE_QUOTE_INPUT))


class TestConditionalPlanFiltering(unittest.TestCase):
    def test_minimal_quote_input_strips_conditional_tasks(self):
        tasks, removed = filter_volumetric_conditional_plan_tasks(
            _full_volumetric_plan_tasks(),
            quote_input={},
        )
        self.assertIn(FACE_VINYL_PROCESS_ID, removed)
        self.assertTrue(ILLUMINATION_PROCESS_IDS.issubset(set(removed)))
        self.assertIn(MOUNTING_TEMPLATE_CNC_PROCESS_ID, removed)
        self.assertIn(PAINTING_PROCESS_ID, removed)
        pids = _process_ids(tasks)
        self.assertNotIn(FACE_VINYL_PROCESS_ID, pids)
        self.assertFalse(ILLUMINATION_PROCESS_IDS.intersection(pids))
        self.assertNotIn(MOUNTING_TEMPLATE_CNC_PROCESS_ID, pids)
        self.assertNotIn(PAINTING_PROCESS_ID, pids)
        self.assertIn("vector_prep", pids)
        self.assertIn("assembly_letters", pids)
        self.assertIn("back_cut", pids)
        self.assertIn(PACKAGING_PROCESS_ID, pids)

    def test_back_cut_always_included(self):
        tasks, removed = filter_volumetric_conditional_plan_tasks(
            _full_volumetric_plan_tasks(),
            quote_input={},
        )
        self.assertNotIn("back_cut", removed)
        self.assertIn("back_cut", _process_ids(tasks))

    def test_face_vinyl_present_when_explicit(self):
        tasks, removed = filter_volumetric_conditional_plan_tasks(
            _full_volumetric_plan_tasks(),
            quote_input=FACE_VINYL_QUOTE_INPUT,
        )
        self.assertNotIn(FACE_VINYL_PROCESS_ID, removed)
        self.assertIn(FACE_VINYL_PROCESS_ID, _process_ids(tasks))

    def test_illumination_present_when_enabled(self):
        tasks, removed = filter_volumetric_conditional_plan_tasks(
            _full_volumetric_plan_tasks(),
            quote_input=ILLUMINATED_QUOTE_INPUT,
        )
        self.assertFalse(ILLUMINATION_PROCESS_IDS.intersection(removed))
        pids = _process_ids(tasks)
        self.assertIn("led_install_letters", pids)
        self.assertIn("electrical_letters", pids)

    def test_no_illumination_removes_led_and_electrical(self):
        qi = {**BASE_QUOTE_INPUT, "illumination_type": "none", "lighting_system_type": "none"}
        tasks, removed = filter_volumetric_conditional_plan_tasks(
            _full_volumetric_plan_tasks(),
            quote_input=qi,
        )
        self.assertTrue(ILLUMINATION_PROCESS_IDS.issubset(set(removed)))


class TestPackagingPlanPolicy(unittest.TestCase):
    def test_default_includes_packaging_without_direct_mount_signal(self):
        self.assertTrue(should_include_packaging_in_plan({}))
        self.assertTrue(should_include_packaging_in_plan(BASE_QUOTE_INPUT))

    def test_delivery_install_omits_packaging(self):
        self.assertTrue(is_direct_mounting_in_plan({}, snapshot={"delivery_type": "delivery_install"}))
        self.assertFalse(
            should_include_packaging_in_plan({}, snapshot={"delivery_type": "delivery_install"})
        )

    def test_field_installation_flag_omits_packaging(self):
        self.assertFalse(
            should_include_packaging_in_plan({"requires_installation": True})
        )

    def test_pickup_keeps_packaging(self):
        self.assertTrue(
            should_include_packaging_in_plan({}, snapshot={"delivery_type": "pickup"})
        )


class TestQcPlanPolicy(unittest.TestCase):
    def test_qc_renamed_without_qc_term(self):
        tasks = apply_volumetric_qc_taxonomy_to_plan_tasks(
            [{"task_id": "T-010", "process_id": QC_PROCESS_ID, "display_name": "QC"}]
        )
        qc = tasks[0]
        self.assertEqual(qc["display_name"], QC_DISPLAY_NAME)
        self.assertNotIn("(QC)", qc["display_name"])
        self.assertTrue(qc["internal_only"])
        self.assertIn("Verifică lucrarea", qc["instructions"])


class TestPlanOrchestration(unittest.TestCase):
    def test_no_face_vinyl_no_illumination_plan(self):
        tasks, summary = apply_volumetric_conditional_plan_from_snapshot(
            _full_volumetric_plan_tasks(),
            _snapshot({}),
            set_face_vinyl_instructions=True,
        )
        pids = _process_ids(tasks)
        self.assertNotIn(FACE_VINYL_PROCESS_ID, pids)
        self.assertFalse(ILLUMINATION_PROCESS_IDS.intersection(pids))
        self.assertEqual(summary["face_vinyl_action"], "filtered_no_face_vinyl")
        self.assertTrue(summary["applied"])

    def test_face_vinyl_renames_and_nesting(self):
        tasks, summary = apply_volumetric_conditional_plan_from_snapshot(
            _full_volumetric_plan_tasks(),
            _snapshot(FACE_VINYL_QUOTE_INPUT),
            set_face_vinyl_instructions=True,
        )
        vinyl = next(t for t in tasks if t.get("process_id") == FACE_VINYL_PROCESS_ID)
        self.assertEqual(vinyl["display_name"], FACE_VINYL_DISPLAY_NAME)
        self.assertIn("1260 mm", vinyl.get("instructions") or "")
        self.assertEqual(summary["face_vinyl_action"], "updated")

    def test_forex_mounting_template_kept(self):
        tasks, _ = apply_volumetric_conditional_plan_from_snapshot(
            _full_volumetric_plan_tasks(),
            _snapshot(FOREX_TEMPLATE_QUOTE_INPUT),
        )
        self.assertIn(MOUNTING_TEMPLATE_CNC_PROCESS_ID, _process_ids(tasks))

    def test_paper_mounting_template_excludes_cnc(self):
        tasks, summary = apply_volumetric_conditional_plan_from_snapshot(
            _full_volumetric_plan_tasks(),
            _snapshot(PAPER_TEMPLATE_QUOTE_INPUT),
        )
        self.assertNotIn(MOUNTING_TEMPLATE_CNC_PROCESS_ID, _process_ids(tasks))
        self.assertIn(MOUNTING_TEMPLATE_CNC_PROCESS_ID, summary["removed_process_ids"])

    def test_painting_only_when_ral_selected(self):
        tasks, _ = apply_volumetric_conditional_plan_from_snapshot(
            _full_volumetric_plan_tasks(),
            _snapshot(PAINT_QUOTE_INPUT),
        )
        self.assertIn(PAINTING_PROCESS_ID, _process_ids(tasks))

        tasks_no_paint, summary = apply_volumetric_conditional_plan_from_snapshot(
            _full_volumetric_plan_tasks(),
            _snapshot(BASE_QUOTE_INPUT),
        )
        self.assertNotIn(PAINTING_PROCESS_ID, _process_ids(tasks_no_paint))
        self.assertIn(PAINTING_PROCESS_ID, summary["removed_process_ids"])

    def test_total_minutes_recalculated_after_filter(self):
        tasks, summary = apply_volumetric_conditional_plan_from_snapshot(
            _full_volumetric_plan_tasks(),
            _snapshot({}),
        )
        expected = sum(t.get("estimated_time_minutes") or 0 for t in tasks if isinstance(t, dict))
        self.assertAlmostEqual(summary["total_estimated_time_minutes"], expected)

    def test_scenario_a_pickup_keeps_packaging_and_qc_title(self):
        tasks, _ = apply_volumetric_conditional_plan_from_snapshot(
            _full_volumetric_plan_tasks(),
            PICKUP_SNAPSHOT,
        )
        pids = _process_ids(tasks)
        self.assertIn("back_cut", pids)
        self.assertIn(PACKAGING_PROCESS_ID, pids)
        qc = next(t for t in tasks if t.get("process_id") == QC_PROCESS_ID)
        self.assertEqual(qc["display_name"], QC_DISPLAY_NAME)

    def test_scenario_b_direct_mount_omits_packaging(self):
        tasks, summary = apply_volumetric_conditional_plan_from_snapshot(
            _full_volumetric_plan_tasks(),
            DIRECT_MOUNT_SNAPSHOT,
        )
        pids = _process_ids(tasks)
        self.assertIn("back_cut", pids)
        self.assertIn(QC_PROCESS_ID, pids)
        self.assertNotIn(PACKAGING_PROCESS_ID, pids)
        self.assertIn(PACKAGING_PROCESS_ID, summary["removed_process_ids"])
        qc = next(t for t in tasks if t.get("process_id") == QC_PROCESS_ID)
        self.assertEqual(qc["display_name"], QC_DISPLAY_NAME)

    def test_packaging_after_qc_when_present(self):
        tasks, _ = apply_volumetric_conditional_plan_from_snapshot(
            _full_volumetric_plan_tasks(),
            PICKUP_SNAPSHOT,
        )
        tasks = finalize_volumetric_plan_dependencies(tasks)
        packaging = next(t for t in tasks if t.get("process_id") == PACKAGING_PROCESS_ID)
        qc_id = next(t["task_id"] for t in tasks if t.get("process_id") == QC_PROCESS_ID)
        self.assertIn(qc_id, packaging.get("depends_on_task_ids") or [])


class TestDependencyIntegrity(unittest.TestCase):
    def test_resequence_renumbers_and_remaps_deps(self):
        tasks = [
            {"task_id": "T-003", "process_id": "side_forming", "depends_on_task_ids": ["T-001"]},
            {"task_id": "T-001", "process_id": "vector_prep", "depends_on_task_ids": []},
        ]
        updated, id_map = resequence_plan_task_ids(tasks)
        self.assertEqual(_task_ids(updated), ["T-001", "T-002"])
        self.assertEqual(id_map["T-003"], "T-001")
        side = next(t for t in updated if t["process_id"] == "side_forming")
        self.assertEqual(side["depends_on_task_ids"], ["T-002"])

    def test_prune_orphan_dependencies(self):
        tasks = [
            {"task_id": "T-001", "process_id": "vector_prep", "depends_on_task_ids": []},
            {"task_id": "T-002", "process_id": "assembly_letters", "depends_on_task_ids": ["T-099", "T-001"]},
        ]
        prune_orphan_plan_dependencies(tasks)
        assembly = tasks[1]
        self.assertEqual(assembly["depends_on_task_ids"], ["T-001"])

    def test_assembly_deps_dynamic_without_led(self):
        tasks = filter_volumetric_conditional_plan_tasks(
            _full_volumetric_plan_tasks(),
            quote_input={**BASE_QUOTE_INPUT, "illumination_type": "none", "lighting_system_type": "none"},
        )[0]
        tasks, _ = resequence_plan_task_ids(tasks)
        tasks = apply_dynamic_volumetric_assembly_dependencies(tasks)
        assembly = next(t for t in tasks if t["process_id"] == "assembly_letters")
        dep_pids = []
        index = {t["task_id"]: t["process_id"] for t in tasks}
        for dep in assembly["depends_on_task_ids"]:
            dep_pids.append(index[dep])
        self.assertIn("return_face_bonding", dep_pids)
        self.assertIn("back_cut", dep_pids)
        self.assertNotIn("led_install_letters", dep_pids)
        self.assertNotIn("electrical_letters", dep_pids)

    def test_full_pipeline_dependency_integrity_no_illumination(self):
        tasks, _ = apply_volumetric_conditional_plan_from_snapshot(
            _full_volumetric_plan_tasks(),
            _snapshot({**BASE_QUOTE_INPUT, "illumination_type": "none", "lighting_system_type": "none"}),
        )
        tasks = finalize_volumetric_plan_dependencies(tasks)
        self.assertTrue(_all_deps_valid(tasks))
        ids = _task_ids(tasks)
        self.assertEqual(ids[0], "T-001")
        self.assertEqual(len(ids), len(set(ids)))

    def test_full_pipeline_dependency_integrity_illuminated(self):
        tasks, _ = apply_volumetric_conditional_plan_from_snapshot(
            _full_volumetric_plan_tasks(),
            _snapshot(ILLUMINATED_QUOTE_INPUT),
        )
        tasks = finalize_volumetric_plan_dependencies(tasks)
        self.assertTrue(_all_deps_valid(tasks))
        assembly = next(t for t in tasks if t["process_id"] == "assembly_letters")
        index = {t["task_id"]: t["process_id"] for t in tasks}
        dep_pids = [index[d] for d in assembly["depends_on_task_ids"]]
        self.assertIn("led_install_letters", dep_pids)
        self.assertIn("electrical_letters", dep_pids)

    def test_direct_mount_pipeline_no_orphan_deps(self):
        tasks, summary = apply_volumetric_conditional_plan_from_snapshot(
            _full_volumetric_plan_tasks(),
            DIRECT_MOUNT_SNAPSHOT,
        )
        tasks = finalize_volumetric_plan_dependencies(tasks)
        self.assertTrue(_all_deps_valid(tasks))
        self.assertNotIn(PACKAGING_PROCESS_ID, _process_ids(tasks))
        expected = sum(t.get("estimated_time_minutes") or 0 for t in tasks if isinstance(t, dict))
        self.assertAlmostEqual(summary["total_estimated_time_minutes"], expected)


class TestNonVolumetricUnchanged(unittest.TestCase):
    def test_other_product_skips_filter(self):
        tasks = [{"task_id": "T-001", "process_id": "cnc_routing", "estimated_time_minutes": 5}]
        updated, summary = apply_volumetric_conditional_plan_from_snapshot(
            tasks,
            {"product_definition": {"product_id": "TPL-OTHER"}},
        )
        self.assertFalse(summary["applied"])
        self.assertEqual(updated, tasks)


if __name__ == "__main__":
    unittest.main()
