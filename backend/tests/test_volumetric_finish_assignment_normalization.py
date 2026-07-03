"""Tests for letterGroupFinishAssignments → quote_input normalization and vinyl plan tasks."""

from __future__ import annotations

import os
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from services.volumetric_conditional_plan_tasks_service import (  # noqa: E402
    FACE_VINYL_PROCESS_ID,
    apply_volumetric_conditional_plan_from_snapshot,
    finalize_volumetric_plan_dependencies,
)
from services.volumetric_face_vinyl_service import (  # noqa: E402
    build_face_vinyl_task_instructions,
    build_return_vinyl_task_instructions,
    has_face_vinyl_application,
)
from services.volumetric_finish_assignment_service import (  # noqa: E402
    RETURN_VINYL_DISPLAY_NAME,
    RETURN_VINYL_PROCESS_ID,
    build_face_vinyl_operator_instructions,
    has_return_vinyl_application,
    instructions_contain_forbidden_tokens,
    normalize_volumetric_quote_input_from_finish_assignments,
    resolve_volumetric_operational_quote_input,
)

IR_MQHZ41CM_FACE_ASSIGNMENT = {
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

UNIFORM_PRODUCT_SPEC = {
    "letterGroupFinishAssignments": [IR_MQHZ41CM_FACE_ASSIGNMENT],
    "svgLetterGroups": [
        {
            "groupId": "fill-group-1",
            "visualLabel": "Grup principal",
            "elementCount": 27,
        }
    ],
    "face_finish_type": "none",
    "face_vinyl_enabled": False,
    "return_depth_mm": 80,
    "letter_perimeter_m": 47.234961,
    "letter_face_area_m2": 3.181035,
}

MULTI_GROUP_PRODUCT_SPEC = {
    "letterGroupFinishAssignments": [
        {
            "groupId": "fill-red",
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
        },
        {
            "groupId": "fill-blue",
            "confirmedByOperator": True,
            "face": {
                "finishType": "oracal",
                "materialCode": "651",
                "colorCode": "020",
                "colorName": "Golden yellow",
            },
            "returnCant": {
                "finishType": "oracal_wrapped",
                "depthMm": 80,
                "materialCode": "651",
                "colorCode": "010",
                "colorName": "White",
            },
        },
    ],
    "svgLetterGroups": [
        {"groupId": "fill-red", "visualLabel": "Grup roșu"},
        {"groupId": "fill-blue", "visualLabel": "Grup albastru"},
    ],
}


def _full_volumetric_plan_tasks():
    return [
        {"task_id": "T-001", "process_id": "vector_prep", "display_name": "Verificare grafică", "estimated_time_minutes": 10},
        {"task_id": "T-002", "process_id": "face_cnc_cut", "display_name": "Debitare față", "estimated_time_minutes": 20},
        {"task_id": "T-003", "process_id": "side_forming", "display_name": "Modelare canturi", "estimated_time_minutes": 25},
        {"task_id": "T-004", "process_id": "return_face_bonding", "display_name": "Lipire canturi", "estimated_time_minutes": 20},
        {"task_id": "T-005", "process_id": "back_cut", "display_name": "Debitare spate", "estimated_time_minutes": 18},
        {"task_id": "T-006", "process_id": "assembly_letters", "display_name": "Asamblare", "estimated_time_minutes": 60},
        {"task_id": "T-007", "process_id": "qc_letters", "display_name": "QC", "estimated_time_minutes": 15},
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


class TestFinishAssignmentNormalization(unittest.TestCase):
    def test_face_group_assignment_enables_face_vinyl(self):
        qi = normalize_volumetric_quote_input_from_finish_assignments(
            {"face_finish_type": "none", "face_vinyl_enabled": False},
            product_spec=UNIFORM_PRODUCT_SPEC,
        )
        self.assertTrue(qi.get("face_vinyl_enabled"))
        self.assertEqual(qi.get("face_finish_type"), "oracal_651")
        self.assertEqual(qi.get("face_finish_subtype"), "oracal_8500")
        self.assertEqual(qi.get("face_vinyl_material"), "Oracal 8500")
        self.assertEqual(qi.get("face_vinyl_color_code"), "527")
        self.assertEqual(qi.get("face_vinyl_color_name"), "Pastel blue")
        self.assertTrue(has_face_vinyl_application(qi, product_spec=UNIFORM_PRODUCT_SPEC))

    def test_oracal_8500_uses_costing_umbrella_but_stays_visible_operationally(self):
        """oracal_651 = CostEngine gate; Oracal 8500 series must remain on subtype/material/instructions."""
        qi = normalize_volumetric_quote_input_from_finish_assignments({}, product_spec=UNIFORM_PRODUCT_SPEC)
        self.assertEqual(qi.get("face_finish_type"), "oracal_651")
        self.assertEqual(qi.get("face_finish_subtype"), "oracal_8500")
        self.assertEqual(qi.get("face_vinyl_material"), "Oracal 8500")
        self.assertEqual(qi.get("face_vinyl_color_code"), "527")
        self.assertEqual(qi.get("face_vinyl_color_name"), "Pastel blue")

        text = build_face_vinyl_operator_instructions(qi, product_spec=UNIFORM_PRODUCT_SPEC)
        self.assertIn("Oracal 8500", text)
        self.assertIn("527 Pastel blue", text)
        self.assertNotIn("Oracal 651", text)

    def test_return_group_assignment_sets_depth_60(self):
        qi = normalize_volumetric_quote_input_from_finish_assignments(
            {"return_depth_mm": 80},
            product_spec=UNIFORM_PRODUCT_SPEC,
        )
        self.assertTrue(qi.get("return_vinyl_enabled"))
        self.assertEqual(qi.get("return_finish_type"), "oracal_wrapped")
        self.assertEqual(qi.get("return_depth_mm"), 60)
        self.assertEqual(qi.get("return_vinyl_material"), "Oracal 651")
        self.assertEqual(qi.get("return_vinyl_color_code"), "055m")
        self.assertEqual(qi.get("return_vinyl_color_name"), "Int")
        self.assertTrue(has_return_vinyl_application(qi, product_spec=UNIFORM_PRODUCT_SPEC))

    def test_uniform_all_letters_handoff_flag(self):
        qi = normalize_volumetric_quote_input_from_finish_assignments({}, product_spec=UNIFORM_PRODUCT_SPEC)
        face_handoff = qi.get("letter_group_face_vinyl_handoff")
        return_handoff = qi.get("letter_group_return_vinyl_handoff")
        self.assertIsInstance(face_handoff, dict)
        self.assertTrue(face_handoff.get("uniform_all_letters"))
        self.assertTrue(return_handoff.get("uniform_all_letters"))

    def test_multi_group_preserves_group_details(self):
        qi = normalize_volumetric_quote_input_from_finish_assignments({}, product_spec=MULTI_GROUP_PRODUCT_SPEC)
        face_handoff = qi.get("letter_group_face_vinyl_handoff") or {}
        return_handoff = qi.get("letter_group_return_vinyl_handoff") or {}
        self.assertFalse(face_handoff.get("uniform_all_letters"))
        self.assertFalse(return_handoff.get("uniform_all_letters"))
        self.assertEqual(len(face_handoff.get("groups") or []), 2)
        self.assertEqual(len(return_handoff.get("groups") or []), 2)

    def test_negative_face_none_does_not_enable_vinyl(self):
        spec = {
            "letterGroupFinishAssignments": [
                {
                    "groupId": "g1",
                    "confirmedByOperator": True,
                    "face": {"finishType": "none"},
                }
            ]
        }
        qi = normalize_volumetric_quote_input_from_finish_assignments({}, product_spec=spec)
        self.assertNotIn("face_vinyl_enabled", qi)
        self.assertFalse(has_face_vinyl_application(qi, product_spec=spec))


class TestVinylOperatorInstructions(unittest.TestCase):
    def test_face_instructions_uniform(self):
        qi = normalize_volumetric_quote_input_from_finish_assignments({}, product_spec=UNIFORM_PRODUCT_SPEC)
        text = build_face_vinyl_operator_instructions(qi, product_spec=UNIFORM_PRODUCT_SPEC)
        self.assertIn("Oracal 8500", text)
        self.assertIn("527 Pastel blue", text)
        self.assertIn("toate literele", text.lower())
        self.assertEqual(instructions_contain_forbidden_tokens(text), [])

    def test_return_instructions_uniform(self):
        qi = normalize_volumetric_quote_input_from_finish_assignments({}, product_spec=UNIFORM_PRODUCT_SPEC)
        text = build_return_vinyl_task_instructions(qi, product_spec=UNIFORM_PRODUCT_SPEC)
        self.assertIsNotNone(text)
        assert text is not None
        self.assertIn("Oracal 651", text)
        self.assertIn("055m Int", text)
        self.assertIn("60 mm", text)
        self.assertEqual(instructions_contain_forbidden_tokens(text), [])

    def test_multi_group_face_instructions_list_groups(self):
        qi = normalize_volumetric_quote_input_from_finish_assignments({}, product_spec=MULTI_GROUP_PRODUCT_SPEC)
        text = build_face_vinyl_task_instructions(qi, product_spec=MULTI_GROUP_PRODUCT_SPEC)
        self.assertIn("Grup roșu", text)
        self.assertIn("Grup albastru", text)
        self.assertEqual(instructions_contain_forbidden_tokens(text), [])


class TestVinylPlanGeneration(unittest.TestCase):
    def test_generates_face_and_return_vinyl_tasks_with_order(self):
        snap = _snapshot(
            quote_input={"face_finish_type": "none", "return_depth_mm": 80},
            product_spec=UNIFORM_PRODUCT_SPEC,
        )
        tasks, summary = apply_volumetric_conditional_plan_from_snapshot(
            _full_volumetric_plan_tasks(),
            snap,
            set_face_vinyl_instructions=True,
        )
        tasks = finalize_volumetric_plan_dependencies(tasks)
        pids = _process_ids(tasks)
        self.assertIn(FACE_VINYL_PROCESS_ID, pids)
        self.assertIn(RETURN_VINYL_PROCESS_ID, pids)
        self.assertLess(
            _task_index(tasks, RETURN_VINYL_PROCESS_ID),
            _task_index(tasks, "side_forming"),
        )
        self.assertLess(
            _task_index(tasks, "assembly_letters"),
            _task_index(tasks, FACE_VINYL_PROCESS_ID),
        )
        self.assertLess(
            _task_index(tasks, FACE_VINYL_PROCESS_ID),
            _task_index(tasks, "qc_letters"),
        )
        return_task = next(t for t in tasks if t.get("process_id") == RETURN_VINYL_PROCESS_ID)
        self.assertEqual(return_task.get("display_name"), RETURN_VINYL_DISPLAY_NAME)
        self.assertIn("Oracal 651", return_task.get("instructions") or "")
        self.assertNotIn(summary.get("face_vinyl_action"), {"filtered_no_face_vinyl", "unchanged"})
        self.assertNotIn(summary.get("return_vinyl_action"), {"filtered_no_return_vinyl", "unchanged"})

    def test_dependencies_include_vinyl_predecessors(self):
        snap = _snapshot(product_spec=UNIFORM_PRODUCT_SPEC)
        tasks = finalize_volumetric_plan_dependencies(
            apply_volumetric_conditional_plan_from_snapshot(
                _full_volumetric_plan_tasks(),
                snap,
                set_face_vinyl_instructions=True,
            )[0]
        )
        vinyl = next(t for t in tasks if t.get("process_id") == FACE_VINYL_PROCESS_ID)
        return_vinyl = next(t for t in tasks if t.get("process_id") == RETURN_VINYL_PROCESS_ID)
        side = next(t for t in tasks if t.get("process_id") == "side_forming")
        bonding = next(t for t in tasks if t.get("process_id") == "return_face_bonding")
        assembly = next(t for t in tasks if t.get("process_id") == "assembly_letters")

        self.assertIn(assembly["task_id"], vinyl.get("depends_on_task_ids") or [])
        self.assertNotIn(
            next(t["task_id"] for t in tasks if t.get("process_id") == "face_cnc_cut"),
            vinyl.get("depends_on_task_ids") or [],
        )
        self.assertIn(return_vinyl["task_id"], side.get("depends_on_task_ids") or [])
        self.assertNotIn(vinyl["task_id"], bonding.get("depends_on_task_ids") or [])
        self.assertIn(side["task_id"], bonding.get("depends_on_task_ids") or [])

    def test_no_vinyl_when_assignments_absent(self):
        tasks, summary = apply_volumetric_conditional_plan_from_snapshot(
            _full_volumetric_plan_tasks(),
            _snapshot(quote_input={"face_finish_type": "none"}),
            set_face_vinyl_instructions=True,
        )
        pids = _process_ids(tasks)
        self.assertNotIn(FACE_VINYL_PROCESS_ID, pids)
        self.assertNotIn(RETURN_VINYL_PROCESS_ID, pids)


class TestResolveOperationalQuoteInput(unittest.TestCase):
    def test_resolve_merges_product_spec_only(self):
        qi = resolve_volumetric_operational_quote_input(
            {"face_finish_type": "none"},
            product_spec=UNIFORM_PRODUCT_SPEC,
        )
        self.assertTrue(qi.get("face_vinyl_enabled"))
        self.assertEqual(qi.get("return_depth_mm"), 60)


if __name__ == "__main__":
    unittest.main()
