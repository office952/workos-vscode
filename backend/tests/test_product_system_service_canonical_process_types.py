from __future__ import annotations

import os
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from services.execution_plan_gate_service import CANONICAL_TASK_TYPES  # noqa: E402
from services.product_system_service import ProductSystemService  # noqa: E402


class TestProductSystemServiceCanonicalProcessTypes(unittest.TestCase):
    def test_volumetric_operation_codes_emit_canonical_process_types(self):
        service = ProductSystemService()
        product = service.build_product_definition(
            {
                "template_code": "TPL-VOLUMETRIC-LETTERS_v2",
                "family_name": "Litere volumetrice",
                "components_json": [],
                "operations_json": [
                    {"code": "vector_prep", "workcenter": "PREPRESS", "estimatedMinutes": 18},
                    {"code": "face_cnc_cut", "workcenter": "WC_CNC_ROUTING", "estimatedMinutes": 40},
                    {"code": "assembly_letters", "workcenter": "ASSEMBLY", "estimatedMinutes": 600},
                    {"code": "qc_letters", "workcenter": "QC", "estimatedMinutes": 15},
                ],
                "required_materials_json": [
                    {"materialCode": "MAT-ACP-FATA-LITERE", "name": "Face", "unit": "sqm", "quantity": 1}
                ],
            },
            {"quantity": 1, "dimensions": {"width_mm": 4800, "height_mm": 600, "depth_mm": 60}},
        )

        process_types = [process.type for layer in product.layers for process in layer.processes]

        self.assertIn("file_preparation", process_types)
        self.assertIn("cnc_routing", process_types)
        self.assertIn("volumetric_letter_assembly", process_types)
        self.assertIn("quality_control", process_types)
        self.assertTrue(set(process_types).issubset(CANONICAL_TASK_TYPES), process_types)


if __name__ == "__main__":
    unittest.main()