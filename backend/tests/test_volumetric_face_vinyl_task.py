"""Tests for conditional face vinyl task generation and nesting."""

from __future__ import annotations

import json
import os
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from services.volumetric_face_vinyl_service import (  # noqa: E402
    FACE_VINYL_DISPLAY_NAME,
    FACE_VINYL_PROCESS_ID,
    apply_face_vinyl_taxonomy_to_plan_tasks,
    build_face_vinyl_task_instructions,
    build_return_vinyl_task_instructions,
    estimate_face_vinyl_nesting,
    estimate_return_vinyl_linear_consumption,
    has_face_vinyl_application,
    collect_nesting_pieces,
    NestingPiece,
)


def _face_vinyl_quote_input(**overrides):
    base = {
        "face_finish_type": "oracal_651",
        "face_vinyl_color_code": "651-020",
        "face_vinyl_color_name": "Golden yellow",
        "face_vinyl_roll_width_mm": 1260,
        "letter_face_area_m2": 1.466571,
        "width_mm": 4800,
        "height_mm": 600,
        "letter_count": 11,
        "mounting_system": "direct_wall",
    }
    base.update(overrides)
    return base


def _sample_plan_tasks():
    return [
        {"task_id": "T-002", "process_id": "face_cnc_cut", "display_name": "Debitare față"},
        {"task_id": "T-003", "process_id": FACE_VINYL_PROCESS_ID, "display_name": "Colantare"},
        {"task_id": "T-004", "process_id": "side_forming", "display_name": "Modelare canturi"},
    ]


class TestHasFaceVinylApplication(unittest.TestCase):
    def test_false_when_no_explicit_signals(self):
        self.assertFalse(has_face_vinyl_application({}))
        self.assertFalse(has_face_vinyl_application(None))

    def test_true_when_face_finish_vinyl(self):
        self.assertTrue(has_face_vinyl_application({"face_finish_type": "oracal_651"}))
        self.assertTrue(has_face_vinyl_application({"face_finish_type": "printed_vinyl"}))

    def test_true_when_face_vinyl_enabled(self):
        self.assertTrue(has_face_vinyl_application({"face_vinyl_enabled": True}))

    def test_false_when_face_finish_none(self):
        self.assertFalse(has_face_vinyl_application({"face_finish_type": "none"}))


class TestFaceVinylPlanTasks(unittest.TestCase):
    def test_no_face_vinyl_filters_vinyl_task(self):
        tasks, action = apply_face_vinyl_taxonomy_to_plan_tasks(
            _sample_plan_tasks(),
            quote_input={"face_finish_type": "none"},
            set_owner_instructions=True,
        )
        self.assertEqual(action, "filtered_no_face_vinyl")
        process_ids = [t.get("process_id") for t in tasks]
        self.assertNotIn(FACE_VINYL_PROCESS_ID, process_ids)
        self.assertEqual(len(tasks), 2)

    def test_face_vinyl_renames_and_instructs(self):
        qi = _face_vinyl_quote_input()
        tasks, action = apply_face_vinyl_taxonomy_to_plan_tasks(
            _sample_plan_tasks(),
            quote_input=qi,
            set_owner_instructions=True,
        )
        self.assertEqual(action, "updated")
        vinyl = next(t for t in tasks if t.get("process_id") == FACE_VINYL_PROCESS_ID)
        self.assertEqual(vinyl["display_name"], FACE_VINYL_DISPLAY_NAME)
        self.assertIn("Colantezi fețele din plexiglas", vinyl["instructions"])
        self.assertIn("651-020", vinyl["instructions"])
        self.assertIn("1260 mm", vinyl["instructions"])
        meta = vinyl["face_vinyl_metadata"]
        self.assertEqual(meta["roll_width_mm"], 1260)
        self.assertIn("face_area_sqm", meta)

    def test_non_volumetric_tasks_untouched(self):
        tasks = [{"task_id": "T-1", "process_id": "cnc_routing", "display_name": "CNC"}]
        updated, action = apply_face_vinyl_taxonomy_to_plan_tasks(
            tasks,
            quote_input=_face_vinyl_quote_input(),
            set_owner_instructions=True,
        )
        self.assertEqual(action, "unchanged")
        self.assertEqual(updated[0]["display_name"], "CNC")


class TestFaceVinylNesting(unittest.TestCase):
    def test_assembly_bbox_1260_recommended_about_528(self):
        pieces, source = collect_nesting_pieces(_face_vinyl_quote_input())
        self.assertEqual(source, "assembly_bbox")
        nesting = estimate_face_vinyl_nesting(pieces, roll_width_mm=1260, nesting_source=source)
        self.assertEqual(nesting.nesting_width_mm, 1260)
        self.assertAlmostEqual(nesting.nested_roll_length_m or 0, 4.8, places=2)
        self.assertAlmostEqual(nesting.recommended_roll_length_m or 0, 5.28, places=2)

    def test_nesting_uses_selected_width_1000_not_default(self):
        pieces = [NestingPiece(width_mm=1100, height_mm=400)]
        n1260 = estimate_face_vinyl_nesting(pieces, roll_width_mm=1260, nesting_source="letter_bounding_boxes")
        n1000 = estimate_face_vinyl_nesting(pieces, roll_width_mm=1000, nesting_source="letter_bounding_boxes")
        self.assertEqual(n1260.nesting_width_mm, 1260)
        self.assertEqual(n1000.nesting_width_mm, 1000)
        self.assertAlmostEqual(n1260.recommended_roll_length_m or 0, 0.44, places=2)
        self.assertAlmostEqual(n1000.recommended_roll_length_m or 0, 1.21, places=2)
        self.assertNotEqual(n1260.recommended_roll_length_m, n1000.recommended_roll_length_m)

    def test_missing_roll_width_does_not_invent_length(self):
        pieces = [NestingPiece(width_mm=4800, height_mm=600)]
        nesting = estimate_face_vinyl_nesting(pieces, roll_width_mm=None, nesting_source="assembly_bbox")
        self.assertTrue(nesting.roll_width_missing)
        self.assertIsNone(nesting.recommended_roll_length_m)
        instructions = build_face_vinyl_task_instructions(
            _face_vinyl_quote_input(face_vinyl_roll_width_mm=None),
        )
        self.assertIn("nu este setată", instructions)
        self.assertNotIn("1260 mm", instructions)

    def test_missing_geometry_fallback(self):
        qi = _face_vinyl_quote_input()
        qi.pop("width_mm")
        qi.pop("height_mm")
        instructions = build_face_vinyl_task_instructions(qi)
        self.assertIn("Colantezi fețele din plexiglas", instructions)
        self.assertNotIn("Lungime pregătire:", instructions)
        self.assertNotIn("assembly_bbox", instructions.lower())


class TestReturnVinylLinearHelper(unittest.TestCase):
    def test_cant_60_band_70_and_perimeter_waste(self):
        out = estimate_return_vinyl_linear_consumption(
            cant_width_mm=60,
            perimeter_m=10.0,
            roll_width_mm=1260,
        )
        self.assertEqual(out["band_width_mm"], 70)
        self.assertAlmostEqual(out["recommended_length_m"], 11.0, places=2)
        self.assertEqual(out["bands_per_roll"], 18)
        self.assertAlmostEqual(out["roll_length_m_needed"], 11.0 / 18, places=3)


class TestFaceVinylInstructionsContent(unittest.TestCase):
    def test_instructions_reference_faces_operational(self):
        text = build_face_vinyl_task_instructions(_face_vinyl_quote_input())
        self.assertIn("Colantezi fețele din plexiglas", text)
        self.assertIn("Material autocolant:", text)
        self.assertIn("Lățime rolă", text)
        self.assertTrue(
            "Lungime pregătire" in text or "Material estimat pentru pregătire" in text
        )
        self.assertIn("PAȘI DE LUCRU", text)
        self.assertIn("Curăță fețele din plexiglas", text)
        lowered = text.lower()
        self.assertNotIn("nu pe cant", lowered)
        self.assertNotIn("assembly_bbox", lowered)
        self.assertNotIn("quantity_m2", lowered)
        self.assertNotIn("eur/mp", lowered)
        self.assertNotIn("pierdere", lowered)

    def test_return_vinyl_instructions_when_data_present(self):
        text = build_return_vinyl_task_instructions(
            {
                "return_vinyl_enabled": True,
                "return_finish_type": "oracal_wrapped",
                "return_depth_mm": 60,
                "return_vinyl_material": "Oracal 651",
                "return_vinyl_color_code": "055m",
                "return_vinyl_color_name": "Int",
            }
        )
        self.assertIsNotNone(text)
        assert text is not None
        self.assertIn("Colantezi cantul/lateralul literelor", text)
        self.assertIn("înainte de modelarea cantului", text)
        self.assertIn("Material cant", text)
        self.assertIn("Adâncime cant", text)
        self.assertIn("Oracal 651", text)
        self.assertIn("055m Int", text)
        lowered = text.lower()
        self.assertNotIn("letter_bounding_boxes", lowered)
        self.assertNotIn("rest placă", lowered)
        self.assertNotIn("quantity_m2", lowered)

    def test_return_vinyl_instructions_deferred_without_depth(self):
        qi = {
            "return_vinyl_enabled": True,
            "return_finish_type": "oracal_wrapped",
        }
        self.assertIsNone(build_return_vinyl_task_instructions(qi))

    def test_metadata_serializable(self):
        tasks, _ = apply_face_vinyl_taxonomy_to_plan_tasks(
            _sample_plan_tasks(),
            quote_input=_face_vinyl_quote_input(),
            set_owner_instructions=True,
        )
        vinyl = next(t for t in tasks if t.get("process_id") == FACE_VINYL_PROCESS_ID)
        json.dumps(vinyl["face_vinyl_metadata"])


if __name__ == "__main__":
    unittest.main()
