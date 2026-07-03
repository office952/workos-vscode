"""Unit tests for intake product_spec_json shape validation."""

from __future__ import annotations

import unittest

from validators.intake_product_spec import validate_intake_product_spec


class IntakeProductSpecValidatorTests(unittest.TestCase):
    def test_none_and_empty(self) -> None:
        self.assertIsNone(validate_intake_product_spec(None))
        self.assertIsNone(validate_intake_product_spec({}))

    def test_accepts_canonical_fields(self) -> None:
        spec = validate_intake_product_spec(
            {
                "text": "BT",
                "letter_height_mm": 600,
                "illumination_type": "backlit",
                "backing_chamfer": True,
                "unknown": "drop",
            }
        )
        self.assertEqual(spec["text"], "BT")
        self.assertNotIn("unknown", spec)

    def test_rejects_invalid_enum(self) -> None:
        with self.assertRaises(ValueError):
            validate_intake_product_spec({"illumination_type": "neon"})

    def test_accepts_canonical_volumetric_fields(self) -> None:
        spec = validate_intake_product_spec(
            {
                "face_finish_type": "oracal_651",
                "mounting_system": "steel_bars",
                "mounting_bar_profile": "30x30x1.5",
                "paint_ral_code": "RAL 9005",
                "face_vinyl_roll_width_mm": 1260,
                "selected_psu_watts": 100,
                "width_mm": 4800,
            }
        )
        self.assertEqual(spec["mounting_system"], "steel_bars")
        self.assertEqual(spec["face_vinyl_roll_width_mm"], 1260)

    def test_accepts_volume_finish_and_face_miter(self) -> None:
        spec = validate_intake_product_spec(
            {
                "face_finish": "oracal_651",
                "volume_finish": "paint_after_face_miter_bond",
                "face_miter_chamfer": True,
            }
        )
        self.assertEqual(spec["volume_finish"], "paint_after_face_miter_bond")
        self.assertTrue(spec["face_miter_chamfer"])

    def test_accepts_vector_analysis_summary_fields(self) -> None:
        spec = validate_intake_product_spec(
            {
                "vector_file_name": "litere.svg",
                "vector_file_type": "svg",
                "vector_analysis_status": "analyzed",
                "vector_parse_status": "parsed_sanitized",
                "vector_preview_available": True,
                "vector_analysis_warnings": ["svg_sanitized_doctype_removed"],
                "svg_layer_mappings": {"Layer_x0020_1": "TPL-VOLUMETRIC-LETTERS"},
                "vector_detected_layers_summary": [
                    {
                        "layer_name": "Layer_x0020_1",
                        "mapping_status": "mapped_manual",
                        "mapped_by": "manual",
                        "mapped_target": "TPL-VOLUMETRIC-LETTERS",
                    }
                ],
            }
        )
        self.assertEqual(spec["vector_parse_status"], "parsed_sanitized")
        self.assertTrue(spec["vector_preview_available"])
        self.assertEqual(len(spec["vector_detected_layers_summary"]), 1)

    def test_accepts_client_svg_layer_detection_fields(self) -> None:
        spec = validate_intake_product_spec(
            {
                "vector_file_name": "layers.svg",
                "vector_svg_analyzed": True,
                "vector_svg_viewbox": "0 0 100 50",
                "vector_detected_layer_count": 2,
                "vector_detected_layers": [
                    {
                        "id": "l1",
                        "label": "LITERE",
                        "element_count": 3,
                        "suggested_role": "volumetric_letters",
                        "confirmed_role": "volumetric_letters",
                    }
                ],
                "vector_layer_mapping_confirmed": True,
                "vector_layer_analysis_warnings": ["viewBox lipsește"],
            }
        )
        self.assertTrue(spec["vector_svg_analyzed"])
        self.assertEqual(spec["vector_detected_layer_count"], 2)
        self.assertEqual(len(spec["vector_detected_layers"]), 1)

    def test_accepts_svg_geometry_suggestion_fields(self) -> None:
        spec = validate_intake_product_spec(
            {
                "vector_geometry_analyzed": True,
                "vector_geometry_confidence": "high",
                "vector_geometry_parser_version": "mvp-1",
                "vector_geometry_warnings": ["Aria suportului este estimare bounding-box"],
                "vector_suggested_assembly_width_mm": 4800,
                "vector_suggested_assembly_height_mm": 600,
                "vector_suggested_letter_element_count": 9,
                "geometry_source": "svg_suggestion_confirmed",
            }
        )
        self.assertTrue(spec["vector_geometry_analyzed"])
        self.assertEqual(spec["vector_geometry_confidence"], "high")
        self.assertEqual(spec["vector_suggested_assembly_width_mm"], 4800)
        self.assertEqual(spec["geometry_source"], "svg_suggestion_confirmed")

    def test_preserves_svg_letter_group_finish_assignment_fields(self) -> None:
        spec = validate_intake_product_spec(
            {
                "vector_file_name": "publi-cadru-fx.svg",
                "svgLetterGroups": [
                    {
                        "groupId": "fill-e31e24",
                        "sourceLayerName": "Litere_x0020_volumetrice",
                        "sourceFillColor": "#E31E24",
                        "sourceStrokeColor": "#2B2A29",
                        "visualLabel": "Grup #E31E24",
                        "elementCount": 1,
                        "faceAreaM2": 0.1617,
                        "perimeterM": 3.676,
                        "status": "suggested",
                        "elementIds": ["path-0"],
                        "unsafeExtra": "drop-me",
                    },
                    {
                        "groupId": "fill-393185",
                        "sourceLayerName": "Litere_x0020_volumetrice",
                        "sourceFillColor": "#393185",
                        "status": "suggested",
                    },
                ],
                "letterGroupFinishAssignments": [
                    {
                        "groupId": "fill-e31e24",
                        "face": {
                            "finishType": "oracal",
                            "colorCode": "test red",
                            "notes": "operator",
                            "unexpected": "ignored",
                        },
                        "returnCant": {
                            "finishType": "same_as_face",
                            "depthMm": 60,
                            "colorCode": "test red",
                        },
                        "backing": {
                            "materialType": "forex_10mm",
                            "notes": "optional",
                        },
                        "confirmedByOperator": True,
                    },
                    {
                        "groupId": "fill-393185",
                        "face": {"finishType": "oracal", "colorCode": "test blue"},
                        "returnCant": {"finishType": "oracal_wrapped", "depthMm": 60},
                        "confirmedByOperator": False,
                    },
                ],
                "svgArtworkLayersPending": [
                    {
                        "layerId": "Emblema",
                        "layerName": "Emblema",
                        "elementCount": 510,
                        "distinctFillCount": 242,
                        "distinctFills": ["#E31E24", "#CF1C5F"],
                        "note": "Artwork multicolor",
                        "reason": "needs_operator_decision",
                        "status": "pending",
                        "autoOracal": "drop-me",
                    }
                ],
                "svgArtworkFinishAssignments": [
                    {
                        "layerId": "Emblema",
                        "layerName": "Emblema",
                        "executionType": "print_laminate",
                        "materialCode": "LAM-001",
                        "colorMode": "polychrome",
                        "elementCount": 510,
                        "distinctFillCount": 242,
                        "returnCant": {
                            "finishType": "standard_aluminum",
                            "depthMm": 60,
                            "notes": "cant pe volum",
                            "unexpected": "drop-me",
                        },
                        "printFile": {
                            "fileName": "emblema-print.pdf",
                            "storedFileName": "emblema-print.pdf",
                            "sizeBytes": 12345,
                            "contentType": "application/pdf",
                            "uploadedAt": "2026-06-10T12:00:00+00:00",
                            "unexpected": "drop-me",
                        },
                        "notes": "test policromie",
                        "confirmedByOperator": True,
                        "unexpected": "drop-me",
                    }
                ],
                "workFileAttachments": [
                    {
                        "id": "wf-1",
                        "fileName": "master.cdr",
                        "fileUrl": "/api/v1/entities/intake_requests/by-code/IR-TEST/work-files/wf-1/download",
                        "storedFileName": "wf-1_master.cdr",
                        "mimeType": "application/octet-stream",
                        "extension": ".cdr",
                        "sizeBytes": 4096,
                        "role": "master_work_file",
                        "usableFor": ["cnc", "print", "cutter_plotter", "modeling"],
                        "uploadedAt": "2026-06-10T12:00:00+00:00",
                        "notes": "Corel master",
                        "isPrimary": True,
                        "unexpected": "drop-me",
                    }
                ],
            }
        )
        self.assertEqual(len(spec["svgLetterGroups"]), 2)
        self.assertNotIn("elementIds", spec["svgLetterGroups"][0])
        self.assertNotIn("unsafeExtra", spec["svgLetterGroups"][0])
        self.assertEqual(spec["svgLetterGroups"][0]["groupId"], "fill-e31e24")
        self.assertEqual(spec["svgLetterGroups"][0]["sourceFillColor"], "#E31E24")
        self.assertEqual(spec["svgLetterGroups"][0]["faceAreaM2"], 0.1617)

        red_assignment = spec["letterGroupFinishAssignments"][0]
        self.assertEqual(red_assignment["groupId"], "fill-e31e24")
        self.assertEqual(red_assignment["face"]["finishType"], "oracal")
        self.assertEqual(red_assignment["face"]["colorCode"], "test red")
        self.assertNotIn("unexpected", red_assignment["face"])
        self.assertEqual(red_assignment["returnCant"]["finishType"], "same_as_face")
        self.assertEqual(red_assignment["returnCant"]["depthMm"], 60.0)
        self.assertEqual(red_assignment["backing"]["materialType"], "forex_10mm")
        self.assertTrue(red_assignment["confirmedByOperator"])

        self.assertEqual(spec["svgArtworkLayersPending"][0]["layerName"], "Emblema")
        self.assertEqual(spec["svgArtworkLayersPending"][0]["distinctFillCount"], 242)
        self.assertEqual(len(spec["svgArtworkLayersPending"][0]["distinctFills"]), 2)
        self.assertNotIn("autoOracal", spec["svgArtworkLayersPending"][0])

        artwork_assignment = spec["svgArtworkFinishAssignments"][0]
        self.assertEqual(artwork_assignment["layerName"], "Emblema")
        self.assertEqual(artwork_assignment["executionType"], "print_laminate")
        self.assertEqual(artwork_assignment["materialCode"], "LAM-001")
        self.assertEqual(artwork_assignment["notes"], "test policromie")
        self.assertTrue(artwork_assignment["confirmedByOperator"])
        self.assertEqual(artwork_assignment["returnCant"]["depthMm"], 60.0)
        self.assertEqual(artwork_assignment["returnCant"]["notes"], "cant pe volum")
        self.assertNotIn("unexpected", artwork_assignment["returnCant"])
        self.assertEqual(artwork_assignment["printFile"]["fileName"], "emblema-print.pdf")
        self.assertEqual(artwork_assignment["printFile"]["sizeBytes"], 12345.0)
        self.assertNotIn("unexpected", artwork_assignment["printFile"])
        self.assertNotIn("unexpected", artwork_assignment)

        work_file = spec["workFileAttachments"][0]
        self.assertEqual(work_file["fileName"], "master.cdr")
        self.assertEqual(work_file["role"], "master_work_file")
        self.assertIn("cnc", work_file["usableFor"])
        self.assertTrue(work_file["isPrimary"])
        self.assertNotIn("unexpected", work_file)

    def test_rejects_non_list_svg_letter_group_fields(self) -> None:
        with self.assertRaises(ValueError):
            validate_intake_product_spec({"svgLetterGroups": {"groupId": "x"}})
        with self.assertRaises(ValueError):
            validate_intake_product_spec({"letterGroupFinishAssignments": "bad"})
        with self.assertRaises(ValueError):
            validate_intake_product_spec({"svgArtworkLayersPending": 1})
        with self.assertRaises(ValueError):
            validate_intake_product_spec({"svgArtworkFinishAssignments": 1})


if __name__ == "__main__":
    unittest.main(verbosity=2)
