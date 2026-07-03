"""Canonical material naming catalog — seed documentation guard."""

from __future__ import annotations

import unittest

from seeds.material_canonical_naming import (
    CANONICAL_MATERIAL_NAMING,
    canonical_name_for_code,
)


class TestMaterialCanonicalNaming(unittest.TestCase):
    def test_catalog_has_premount_steel_canonical_name(self) -> None:
        entry = CANONICAL_MATERIAL_NAMING["MAT-PREMOUNT-BAR-STEEL"]
        self.assertIn("Țeavă pătrată oțel", entry["canonical_name"])
        self.assertNotIn("premontaj", entry["canonical_name"].lower())
        self.assertIn("premontaj", entry["source_notes"].lower())

    def test_catalog_pvc_backing_not_forex_in_canonical_name(self) -> None:
        entry = CANONICAL_MATERIAL_NAMING["MAT-SPATE-PVC-LITERE"]
        self.assertIn("PVC expandat", entry["canonical_name"])
        self.assertIn("Forex", entry["source_notes"])

    def test_canonical_name_for_unknown_code_falls_back(self) -> None:
        self.assertEqual(canonical_name_for_code("MAT-UNKNOWN", "Fallback"), "Fallback")

    def test_acm_bond_codes_share_canonical_family_label(self) -> None:
        name_3 = CANONICAL_MATERIAL_NAMING["MAT-ACM-BOND-3MM"]["canonical_name"]
        name_4 = CANONICAL_MATERIAL_NAMING["MAT-ACM-BOND-4MM"]["canonical_name"]
        self.assertTrue(name_3.startswith("Panou compozit aluminiu"))
        self.assertTrue(name_4.startswith("Panou compozit aluminiu"))


if __name__ == "__main__":
    unittest.main()
