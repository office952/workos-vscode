from __future__ import annotations

import os
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from seeds.seed_tpl_volumetric_letters_dossier import _task_rules  # noqa: E402
from services.execution_plan_gate_service import CANONICAL_TASK_TYPES  # noqa: E402


class TestTplVolumetricLettersDossierTaskTypes(unittest.TestCase):
    def test_dossier_uses_canonical_task_types_for_production_rules(self):
        allowed = set(CANONICAL_TASK_TYPES) | {"READINESS_GATE"}
        rules = _task_rules()["rules"]

        task_types = {rule["task_type"] for rule in rules}

        self.assertTrue(task_types.issubset(allowed), task_types)
        self.assertIn("file_preparation", task_types)
        self.assertIn("cnc_routing", task_types)
        self.assertIn("edge_bending", task_types)
        self.assertIn("volumetric_letter_assembly", task_types)
        self.assertIn("led_assembly", task_types)
        self.assertIn("led_wiring", task_types)
        self.assertIn("quality_control", task_types)
        self.assertIn("packaging", task_types)


if __name__ == "__main__":
    unittest.main()