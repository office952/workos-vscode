"""Volumetric execution plan task order — owner rules alignment."""

from __future__ import annotations

import os
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from services.volumetric_conditional_plan_tasks_service import (  # noqa: E402
    FACE_VINYL_PROCESS_ID,
    PACKAGING_DISPLAY_NAME,
    PAINTING_PROCESS_ID,
    RETURN_VINYL_PROCESS_ID,
    apply_volumetric_conditional_plan_from_snapshot,
    finalize_volumetric_plan_dependencies,
)
from services.volumetric_finish_assignment_service import RETURN_VINYL_PROCESS_ID as RV_PID  # noqa: E402

assert RETURN_VINYL_PROCESS_ID == RV_PID

UNIFORM_PRODUCT_SPEC = {
    "letterGroupFinishAssignments": [
        {
            "groupId": "fill-group-1",
            "confirmedByOperator": True,
            "face": {
                "finishType": "translucent_film",
                "materialCode": "8500",
                "colorCode": "527",
                "colorName": "Pastel blue",
            },
            "returnCant": {
                "finishType": "oracal_wrapped",
                "depthMm": 60,
                "materialCode": "651",
                "colorCode": "055m",
                "colorName": "Int",
            },
            "backing": {"materialType": "forex_10mm"},
        }
    ],
    "svgLetterGroups": [
        {"groupId": "fill-group-1", "visualLabel": "Grup principal", "elementCount": 27}
    ],
    "face_finish_type": "none",
    "face_vinyl_enabled": False,
    "return_depth_mm": 80,
}

BASE_QUOTE_INPUT = {
    "width_mm": 4800,
    "height_mm": 600,
    "return_depth_mm": 60,
    "face_finish_type": "none",
}

ILLUMINATED_QUOTE_INPUT = {
    **BASE_QUOTE_INPUT,
    "illumination_type": "frontlit",
    "lighting_system_type": "led_modules",
    "selected_psu_watts": 100,
}

PAINT_QUOTE_INPUT = {
    **BASE_QUOTE_INPUT,
    "volume_finish": "paint_after_face_miter_bond",
    "paint_tube_count": 3,
    "paint_ral_code": "RAL 9005",
}


def _full_volumetric_plan_tasks():
    return [
        {"task_id": "T-001", "process_id": "vector_prep", "estimated_time_minutes": 10},
        {"task_id": "T-002", "process_id": "face_cnc_cut", "estimated_time_minutes": 20},
        {"task_id": "T-003", "process_id": FACE_VINYL_PROCESS_ID, "estimated_time_minutes": 15},
        {"task_id": "T-004", "process_id": "side_forming", "estimated_time_minutes": 25},
        {"task_id": "T-005", "process_id": "return_face_bonding", "estimated_time_minutes": 20},
        {"task_id": "T-006", "process_id": "back_cut", "estimated_time_minutes": 18},
        {"task_id": "T-007", "process_id": "led_install_letters", "estimated_time_minutes": 30},
        {"task_id": "T-008", "process_id": "electrical_letters", "estimated_time_minutes": 12},
        {"task_id": "T-009", "process_id": PAINTING_PROCESS_ID, "estimated_time_minutes": 22},
        {"task_id": "T-010", "process_id": "assembly_letters", "estimated_time_minutes": 60},
        {"task_id": "T-011", "process_id": "qc_letters", "estimated_time_minutes": 15},
        {"task_id": "T-012", "process_id": "packaging_letters", "estimated_time_minutes": 10},
    ]


def _snapshot(*, quote_input=None, product_spec=None):
    return {
        "product_definition": {"product_id": "TPL-VOLUMETRIC-LETTERS"},
        "quote_input": dict(quote_input or {}),
        "product_spec_json": dict(product_spec or {}),
    }


def _process_ids(tasks):
    return [t.get("process_id") for t in tasks if isinstance(t, dict)]


def _task_index(tasks, process_id):
    for index, task in enumerate(tasks):
        if isinstance(task, dict) and task.get("process_id") == process_id:
            return index
    return -1


def _task_by_pid(tasks, process_id):
    return next(t for t in tasks if isinstance(t, dict) and t.get("process_id") == process_id)


def _plan(quote_input=None, product_spec=None):
    tasks, _ = apply_volumetric_conditional_plan_from_snapshot(
        _full_volumetric_plan_tasks(),
        _snapshot(quote_input=quote_input, product_spec=product_spec),
        set_face_vinyl_instructions=True,
    )
    return finalize_volumetric_plan_dependencies(tasks)


class TestFaceVinylAfterAssembly(unittest.TestCase):
    def test_face_vinyl_after_assembly_no_shared_support(self):
        tasks = _plan(product_spec=UNIFORM_PRODUCT_SPEC)
        assembly = _task_by_pid(tasks, "assembly_letters")
        vinyl = _task_by_pid(tasks, FACE_VINYL_PROCESS_ID)
        self.assertGreater(_task_index(tasks, FACE_VINYL_PROCESS_ID), _task_index(tasks, "assembly_letters"))
        self.assertIn(assembly["task_id"], vinyl.get("depends_on_task_ids") or [])

    def test_no_face_vinyl_when_not_specified(self):
        tasks = _plan(quote_input={"face_finish_type": "none"})
        self.assertNotIn(FACE_VINYL_PROCESS_ID, _process_ids(tasks))


class TestReturnVinylBeforeForming(unittest.TestCase):
    def test_return_vinyl_before_side_forming(self):
        tasks = _plan(product_spec=UNIFORM_PRODUCT_SPEC)
        self.assertLess(
            _task_index(tasks, RETURN_VINYL_PROCESS_ID),
            _task_index(tasks, "side_forming"),
        )
        side = _task_by_pid(tasks, "side_forming")
        return_vinyl = _task_by_pid(tasks, RETURN_VINYL_PROCESS_ID)
        self.assertIn(return_vinyl["task_id"], side.get("depends_on_task_ids") or [])

    def test_no_return_vinyl_when_return_not_wrapped(self):
        tasks = _plan(quote_input={"face_finish_type": "none", "return_depth_mm": 60})
        self.assertNotIn(RETURN_VINYL_PROCESS_ID, _process_ids(tasks))


class TestLedBeforeAssembly(unittest.TestCase):
    def test_led_and_wiring_before_assembly(self):
        tasks = _plan(quote_input=ILLUMINATED_QUOTE_INPUT, product_spec=UNIFORM_PRODUCT_SPEC)
        assembly = _task_by_pid(tasks, "assembly_letters")
        index = {t["task_id"]: t["process_id"] for t in tasks if isinstance(t, dict)}
        dep_pids = [index[d] for d in assembly.get("depends_on_task_ids") or []]
        self.assertIn("led_install_letters", dep_pids)
        self.assertIn("electrical_letters", dep_pids)
        self.assertLess(_task_index(tasks, "electrical_letters"), _task_index(tasks, "assembly_letters"))


class TestNoSharedSupportSourceMounting(unittest.TestCase):
    def test_no_source_mounting_task_generated(self):
        tasks = _plan(quote_input=ILLUMINATED_QUOTE_INPUT, product_spec=UNIFORM_PRODUCT_SPEC)
        pids = _process_ids(tasks)
        self.assertNotIn("electrical_source_mounting", pids)
        self.assertNotIn("mounting_template_cnc_cut", pids)

    def test_packaging_references_psu_for_illuminated_no_shared_support(self):
        tasks = _plan(quote_input=ILLUMINATED_QUOTE_INPUT, product_spec=UNIFORM_PRODUCT_SPEC)
        packaging = _task_by_pid(tasks, "packaging_letters")
        self.assertEqual(packaging.get("display_name"), PACKAGING_DISPLAY_NAME)
        self.assertIn("100 W", packaging.get("instructions") or "")


class TestReturnPaintedRuntimeBranch(unittest.TestCase):
    def test_return_painting_after_assembly_when_volume_finish_selected(self):
        """Runtime uses volume_finish=paint_after_face_miter_bond, not Intake V3 return_finish_type=painted."""
        qi = {**ILLUMINATED_QUOTE_INPUT, **PAINT_QUOTE_INPUT}
        tasks = _plan(quote_input=qi, product_spec=UNIFORM_PRODUCT_SPEC)
        painting = _task_by_pid(tasks, PAINTING_PROCESS_ID)
        assembly = _task_by_pid(tasks, "assembly_letters")
        self.assertIn(assembly["task_id"], painting.get("depends_on_task_ids") or [])
        self.assertLess(_task_index(tasks, "assembly_letters"), _task_index(tasks, PAINTING_PROCESS_ID))

    def test_face_vinyl_after_return_painting_when_both_active(self):
        qi = {
            **ILLUMINATED_QUOTE_INPUT,
            **PAINT_QUOTE_INPUT,
            "face_finish_type": "oracal_651",
            "face_vinyl_color_code": "651-020",
            "face_vinyl_roll_width_mm": 1260,
        }
        tasks = _plan(quote_input=qi)
        vinyl = _task_by_pid(tasks, FACE_VINYL_PROCESS_ID)
        painting = _task_by_pid(tasks, PAINTING_PROCESS_ID)
        self.assertIn(painting["task_id"], vinyl.get("depends_on_task_ids") or [])
        self.assertLess(_task_index(tasks, PAINTING_PROCESS_ID), _task_index(tasks, FACE_VINYL_PROCESS_ID))


if __name__ == "__main__":
    unittest.main()
