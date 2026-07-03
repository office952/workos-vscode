"""Sprint #27 — ProductSystem Strict Contract Hardening — validator tests.

Proves the canonical `validate_hierarchical_payload` contract:

  1. Accepts a well-formed hierarchical payload (round-trip preserves data,
     flat mirrors are re-emitted, dual-name + formula fields survive).
  2. Rejects components_json with an unknown component type (422).
  3. Rejects operations with non-positive estimatedMinutes (static) and
     empty workcenter — collects BOTH errors in one report.
  4. Rejects materials with empty materialCode / non-positive quantity.
  5. Rejects flat rows whose `component_ref` does not resolve to any
     hierarchical component_id (orphan).
  6. Rejects formula_based lines that omit `formula_id`.
  7. Rejects components with duplicate component_ids.
  8. Parity: a strict-validated payload round-trips through
     `product_system_service` → ProductDefinition has the expected layers
     and is_valid becomes True when the user_config is complete.

The test suite bypasses FastAPI/DB entirely — it drives the
`validate_hierarchical_payload` function directly. This is the same
function the router calls on POST/PUT, so equivalent 422 coverage is
guaranteed.
"""

from __future__ import annotations

import json
import os
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from services.product_template_contract import (  # noqa: E402
    TemplateContractError,
    validate_hierarchical_payload,
)
from services.product_system_service import ProductSystemService  # noqa: E402


def _good_components():
    return [
        {
            "component_id": "comp_1",
            "type": "STRUCTURA",
            "name": "Cadru",
            "operations": [
                {
                    "code": "CUT",
                    "name": "Debitare",
                    "workcenter": "CNC",
                    "estimatedMinutes": 30,
                    "sequence": 1,
                    "component_ref": "comp_1",
                },
            ],
            "materials": [
                {
                    "materialCode": "MAT-STEEL",
                    "name": "Oțel",
                    "quantity": 2,
                    "unit": "kg",
                    "component_ref": "comp_1",
                },
            ],
        },
        {
            "component_id": "comp_2",
            "type": "FATA_ACP_ROUTATA",
            "name": "Față ACP Routată",
            "operations": [
                {
                    "code": "PRINT",
                    "name": "Printare",
                    "workcenter": "printing",
                    "estimated_minutes": 45,  # snake_case variant — must be accepted
                    "sequence": 1,
                    "component_ref": "comp_2",
                },
            ],
            "materials": [
                {
                    "material_code": "MAT-ACP",  # snake_case variant
                    "name": "ACP 3mm",
                    "quantity": 4,
                    "unit": "sqm",
                    "component_ref": "comp_2",
                },
            ],
        },
    ]


def _flat_mirrors(components):
    flat_ops, flat_mats = [], []
    for c in components:
        for op in c["operations"]:
            flat_ops.append({**op, "component_ref": c["component_id"]})
        for m in c["materials"]:
            flat_mats.append({**m, "component_ref": c["component_id"]})
    return flat_ops, flat_mats


class StrictContractSuite(unittest.TestCase):
    # ------------------------------------------------------------------
    # 1. Happy path — round-trip preserves data
    # ------------------------------------------------------------------
    def test_accept_well_formed_payload(self):
        comps = _good_components()
        flat_ops, flat_mats = _flat_mirrors(comps)
        normalized = validate_hierarchical_payload(
            components_json=json.dumps(comps),
            operations_json=json.dumps(flat_ops),
            required_materials_json=json.dumps(flat_mats),
        )

        # Returns three JSON-encoded strings.
        self.assertIn("components_json", normalized)
        self.assertIn("operations_json", normalized)
        self.assertIn("required_materials_json", normalized)

        comps_out = json.loads(normalized["components_json"])
        self.assertEqual(len(comps_out), 2)
        # Dual-name normalization: both estimatedMinutes & estimated_minutes
        # present, both materialCode & material_code present.
        op0 = comps_out[0]["operations"][0]
        self.assertEqual(op0["estimatedMinutes"], 30.0)
        self.assertEqual(op0["estimated_minutes"], 30.0)
        mat0 = comps_out[0]["materials"][0]
        self.assertEqual(mat0["materialCode"], "MAT-STEEL")
        self.assertEqual(mat0["material_code"], "MAT-STEEL")

        # Snake-case-only input on comp_2 was accepted and normalized.
        op1 = comps_out[1]["operations"][0]
        self.assertEqual(op1["estimatedMinutes"], 45.0)
        self.assertEqual(op1["estimated_minutes"], 45.0)
        mat1 = comps_out[1]["materials"][0]
        self.assertEqual(mat1["materialCode"], "MAT-ACP")
        self.assertEqual(mat1["material_code"], "MAT-ACP")

        # Flat mirrors re-emitted from the hierarchical shape.
        flat_ops_out = json.loads(normalized["operations_json"])
        flat_mats_out = json.loads(normalized["required_materials_json"])
        self.assertEqual(len(flat_ops_out), 2)
        self.assertEqual(len(flat_mats_out), 2)
        self.assertEqual({o["component_ref"] for o in flat_ops_out}, {"comp_1", "comp_2"})
        self.assertEqual({m["component_ref"] for m in flat_mats_out}, {"comp_1", "comp_2"})

    # ------------------------------------------------------------------
    # 2. Unknown component type → COMPONENT_TYPE_INVALID
    # ------------------------------------------------------------------
    def test_reject_unknown_component_type(self):
        comps = _good_components()
        comps[0]["type"] = "WTF_UNKNOWN"
        flat_ops, flat_mats = _flat_mirrors(comps)
        with self.assertRaises(TemplateContractError) as cm:
            validate_hierarchical_payload(
                json.dumps(comps), json.dumps(flat_ops), json.dumps(flat_mats)
            )
        codes = {e["code"] for e in cm.exception.errors}
        self.assertIn("COMPONENT_TYPE_INVALID", codes)
        paths = {e["path"] for e in cm.exception.errors if e["code"] == "COMPONENT_TYPE_INVALID"}
        self.assertIn("components[0].type", paths)

    # ------------------------------------------------------------------
    # 3. Operation: non-positive minutes + empty workcenter (both reported)
    # ------------------------------------------------------------------
    def test_reject_operation_minutes_and_workcenter(self):
        comps = _good_components()
        comps[0]["operations"][0]["estimatedMinutes"] = 0
        comps[0]["operations"][0]["workcenter"] = ""
        flat_ops, flat_mats = _flat_mirrors(comps)
        with self.assertRaises(TemplateContractError) as cm:
            validate_hierarchical_payload(
                json.dumps(comps), json.dumps(flat_ops), json.dumps(flat_mats)
            )
        codes = [e["code"] for e in cm.exception.errors]
        self.assertIn("OPERATION_MINUTES_NON_POSITIVE", codes)
        self.assertIn("OPERATION_WORKCENTER_EMPTY", codes)
        # Both errors carry the same op path.
        for e in cm.exception.errors:
            if e["code"] == "OPERATION_MINUTES_NON_POSITIVE":
                self.assertEqual(e["path"], "components[0].operations[0].estimatedMinutes")
            if e["code"] == "OPERATION_WORKCENTER_EMPTY":
                self.assertEqual(e["path"], "components[0].operations[0].workcenter")

    # ------------------------------------------------------------------
    # 4. Material: empty code + non-positive quantity
    # ------------------------------------------------------------------
    def test_reject_material_empty_code_and_qty(self):
        comps = _good_components()
        comps[0]["materials"][0]["materialCode"] = ""
        comps[0]["materials"][0]["quantity"] = 0
        flat_ops, flat_mats = _flat_mirrors(comps)
        with self.assertRaises(TemplateContractError) as cm:
            validate_hierarchical_payload(
                json.dumps(comps), json.dumps(flat_ops), json.dumps(flat_mats)
            )
        codes = [e["code"] for e in cm.exception.errors]
        self.assertIn("MATERIAL_CODE_EMPTY", codes)
        self.assertIn("MATERIAL_QUANTITY_NON_POSITIVE", codes)

    # ------------------------------------------------------------------
    # 5. Flat orphan — operation references an unknown component_id
    # ------------------------------------------------------------------
    def test_reject_flat_operation_orphan_ref(self):
        comps = _good_components()
        flat_ops, flat_mats = _flat_mirrors(comps)
        flat_ops.append(
            {
                "code": "GHOST",
                "name": "Orphan",
                "workcenter": "ghost",
                "estimatedMinutes": 15,
                "sequence": 99,
                "component_ref": "comp_does_not_exist",
            }
        )
        with self.assertRaises(TemplateContractError) as cm:
            validate_hierarchical_payload(
                json.dumps(comps), json.dumps(flat_ops), json.dumps(flat_mats)
            )
        codes = [e["code"] for e in cm.exception.errors]
        self.assertIn("COMPONENT_REF_ORPHAN", codes)
        # Path is the flat row, not a nested one.
        paths = [
            e["path"] for e in cm.exception.errors if e["code"] == "COMPONENT_REF_ORPHAN"
        ]
        self.assertTrue(any(p.startswith("operations_json[") for p in paths))

    # ------------------------------------------------------------------
    # 6. Formula-based op without formula_id
    # ------------------------------------------------------------------
    def test_reject_formula_based_op_without_formula_id(self):
        comps = _good_components()
        comps[0]["operations"][0]["calculation_type"] = "formula_based"
        # formula_based MUST declare formula_id; removing minutes alone is
        # intentionally not required for formula lines.
        comps[0]["operations"][0].pop("formula_id", None)
        flat_ops, flat_mats = _flat_mirrors(comps)
        with self.assertRaises(TemplateContractError) as cm:
            validate_hierarchical_payload(
                json.dumps(comps), json.dumps(flat_ops), json.dumps(flat_mats)
            )
        codes = [e["code"] for e in cm.exception.errors]
        self.assertIn("OPERATION_FORMULA_ID_EMPTY", codes)

    def test_accept_formula_based_material_with_formula_id(self):
        """Formula-based materials without a static quantity are OK as long
        as they declare a non-empty formula_id."""
        comps = _good_components()
        comps[0]["materials"][0]["calculation_type"] = "formula_based"
        comps[0]["materials"][0]["quantity"] = 0  # allowed for formula_based
        comps[0]["materials"][0]["formula_id"] = "perimeter_m"
        comps[0]["materials"][0]["formula_params"] = {"factor": 1.0}
        comps[0]["materials"][0]["requires_quote_input"] = ["personalization_path_length_mm"]
        flat_ops, flat_mats = _flat_mirrors(comps)
        normalized = validate_hierarchical_payload(
            json.dumps(comps), json.dumps(flat_ops), json.dumps(flat_mats)
        )
        comps_out = json.loads(normalized["components_json"])
        mat0 = comps_out[0]["materials"][0]
        self.assertEqual(mat0["calculation_type"], "formula_based")
        self.assertEqual(mat0["formula_id"], "perimeter_m")
        self.assertEqual(mat0["formula_params"], {"factor": 1.0})
        self.assertEqual(
            mat0["requires_quote_input"], ["personalization_path_length_mm"]
        )

    # ------------------------------------------------------------------
    # 7. Duplicate component_ids
    # ------------------------------------------------------------------
    def test_reject_duplicate_component_ids(self):
        comps = _good_components()
        comps[1]["component_id"] = "comp_1"  # collision
        # operations/materials of the second component now reference comp_1
        for op in comps[1]["operations"]:
            op["component_ref"] = "comp_1"
        for m in comps[1]["materials"]:
            m["component_ref"] = "comp_1"
        flat_ops, flat_mats = _flat_mirrors(comps)
        with self.assertRaises(TemplateContractError) as cm:
            validate_hierarchical_payload(
                json.dumps(comps), json.dumps(flat_ops), json.dumps(flat_mats)
            )
        codes = [e["code"] for e in cm.exception.errors]
        self.assertIn("COMPONENT_ID_DUPLICATE", codes)

    # ------------------------------------------------------------------
    # 8. Empty components_json → rejected
    # ------------------------------------------------------------------
    def test_reject_empty_components_json(self):
        with self.assertRaises(TemplateContractError) as cm:
            validate_hierarchical_payload("[]", "[]", "[]")
        codes = [e["code"] for e in cm.exception.errors]
        self.assertIn("COMPONENTS_EMPTY", codes)

    def test_reject_malformed_json(self):
        with self.assertRaises(TemplateContractError) as cm:
            validate_hierarchical_payload("{not json", "[]", "[]")
        codes = [e["code"] for e in cm.exception.errors]
        self.assertIn("JSON_MALFORMED", codes)

    def test_reject_missing_operations_in_component(self):
        comps = _good_components()
        comps[0]["operations"] = []  # comp_1 has no ops
        flat_ops, flat_mats = _flat_mirrors(comps)
        with self.assertRaises(TemplateContractError) as cm:
            validate_hierarchical_payload(
                json.dumps(comps), json.dumps(flat_ops), json.dumps(flat_mats)
            )
        codes = [e["code"] for e in cm.exception.errors]
        self.assertIn("COMPONENT_HAS_NO_OPERATIONS", codes)

    # ------------------------------------------------------------------
    # 9. Parity — strict-validated payload drives ProductSystem service
    # ------------------------------------------------------------------
    def test_parity_validated_payload_builds_product_definition(self):
        comps = _good_components()
        flat_ops, flat_mats = _flat_mirrors(comps)
        normalized = validate_hierarchical_payload(
            json.dumps(comps), json.dumps(flat_ops), json.dumps(flat_mats)
        )
        template = {
            "id": 99,
            "template_code": "SPRINT27-TPL",
            "family_id": "totemuri_pyloni",
            "family_name": "Totemuri / Pyloni",
            "components_json": normalized["components_json"],
            "operations_json": normalized["operations_json"],
            "required_materials_json": normalized["required_materials_json"],
        }
        user_config = {"quantity": 2, "dimensions": {"width_mm": 500, "height_mm": 1200}}
        pd = ProductSystemService().build_product_definition(
            product_template=template, user_config=user_config
        )
        self.assertTrue(
            pd.validation.is_valid,
            f"PD should be valid, got missing={pd.validation.missing_fields}",
        )
        self.assertEqual(pd.quantity, 2)
        self.assertGreater(len(pd.layers), 0)


class CanonicalComponentTypeVocabularySuite(unittest.TestCase):
    """Sprint #27 vocabulary alignment — proves the canonical 6 ProductSystem
    component types are all accepted, and anything outside that set is still
    rejected with COMPONENT_TYPE_INVALID (no free-text, no coercion).

    Canonical types come from the approved spec (Panouri ACP Iluminate) and
    MUST stay in sync with PRODUCT_COMPONENT_TYPES in
    app/frontend/src/lib/api.ts.
    """

    CANONICAL_TYPES = (
        # --- Original ACP types ---
        "STRUCTURA",
        "FATA_ACP_ROUTATA",
        "DIFUZIE_PLEXI",
        "ILUMINARE",
        "RELIEF_PLEXI_10MM",
        "FINISAJ",
        # --- BUILD 4: Advertising production types ---
        "PRINT_SUBSTRATE",
        "VINYL_APPLICATION",
        "PLEXI_PANEL",
        "FRAME_PROFILE",
        "LITERE_3D",
        "ELECTRIC_LED",
        "EXTERNALIZARE",
        "TAIERE_CNC_LASER",
        "LAMINARE",
    )

    def _single_component_payload(self, ctype: str):
        comps = [
            {
                "component_id": "comp_x",
                "type": ctype,
                "name": f"Componentă {ctype}",
                "operations": [
                    {
                        "code": "OP1",
                        "name": "Op 1",
                        "workcenter": "wc1",
                        "estimatedMinutes": 10,
                        "sequence": 1,
                        "component_ref": "comp_x",
                    }
                ],
                "materials": [
                    {
                        "materialCode": "MAT-X",
                        "name": "Material X",
                        "quantity": 1,
                        "unit": "pcs",
                        "component_ref": "comp_x",
                    }
                ],
            }
        ]
        flat_ops, flat_mats = _flat_mirrors(comps)
        return comps, flat_ops, flat_mats

    def test_allowed_types_matches_canonical_spec(self):
        """Defensive: the validator's allowed set IS exactly the canonical 6.
        If this assertion ever changes, both frontend PRODUCT_COMPONENT_TYPES
        and this test must be updated together."""
        from services.product_template_contract import ALLOWED_COMPONENT_TYPES

        self.assertEqual(
            tuple(ALLOWED_COMPONENT_TYPES),
            self.CANONICAL_TYPES,
            "backend ALLOWED_COMPONENT_TYPES drifted from canonical spec",
        )

    def test_accept_all_six_canonical_types(self):
        """Each of the 6 canonical types must pass validation in isolation."""
        for ctype in self.CANONICAL_TYPES:
            with self.subTest(component_type=ctype):
                comps, flat_ops, flat_mats = self._single_component_payload(ctype)
                normalized = validate_hierarchical_payload(
                    json.dumps(comps),
                    json.dumps(flat_ops),
                    json.dumps(flat_mats),
                )
                comps_out = json.loads(normalized["components_json"])
                self.assertEqual(len(comps_out), 1)
                self.assertEqual(comps_out[0]["type"], ctype)

    def test_reject_previous_vocabulary_leftovers(self):
        """Types from the old narrow vocabulary (FATA, SPATE, SUPORT) that
        are NOT in the canonical 6 must be rejected, not silently accepted
        or coerced. This locks in the vocabulary migration."""
        for ctype in ("FATA", "SPATE", "SUPORT"):
            with self.subTest(component_type=ctype):
                comps, flat_ops, flat_mats = self._single_component_payload(ctype)
                with self.assertRaises(TemplateContractError) as cm:
                    validate_hierarchical_payload(
                        json.dumps(comps),
                        json.dumps(flat_ops),
                        json.dumps(flat_mats),
                    )
                codes = {e["code"] for e in cm.exception.errors}
                self.assertIn("COMPONENT_TYPE_INVALID", codes)

    def test_reject_free_text_and_random_strings(self):
        """No wildcard / free-text support: arbitrary strings must 422.

        Note: the validator case-normalizes via `.upper()` before comparing to
        the allowed set (legitimate pre-existing behavior — `"structura"` still
        lands on canonical `"STRUCTURA"`). This test only covers strings whose
        uppercase form is NOT in the canonical 6, so they must be rejected.
        """
        for ctype in ("CUSTOM_TYPE", "whatever", "FATA", "SUPORT", "RANDOM_X", ""):
            with self.subTest(component_type=repr(ctype)):
                comps, flat_ops, flat_mats = self._single_component_payload(ctype)
                with self.assertRaises(TemplateContractError) as cm:
                    validate_hierarchical_payload(
                        json.dumps(comps),
                        json.dumps(flat_ops),
                        json.dumps(flat_mats),
                    )
                codes = {e["code"] for e in cm.exception.errors}
                self.assertIn("COMPONENT_TYPE_INVALID", codes)


if __name__ == "__main__":
    unittest.main()