"""Romanian Unicode / mojibake integrity regression suite."""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.utf8_text_integrity import (  # noqa: E402
    TextClass,
    assert_no_mojibake,
    classify_text,
    has_suspicious_mojibake,
    repair_source_text,
    safe_repair_text,
    walk_repair_json,
)

CLEAN_SAMPLES = [
    "ă â î ș ț",
    "Ă Â Î Ș Ț",
    "față",
    "șablon",
    "manoperă",
    "aplicare folie pe fețe",
    "tăiere",
    "îndoire",
    "vopsire",
    "execuție",
    "operație",
    "cantitate",
    "preț",
    "măsură",
    "en dash –",
    "em dash —",
    "apostrophe ’",
    "euro €",
    "multiplication ×",
    "area m²",
    "TPL-VOLUMETRIC-LETTERS / față",
]

SINGLE_PASS = [
    ("PregÄƒtire vector / font", "Pregătire vector / font"),
    ("TÄƒiere CNC faÈ›Äƒ litere", "Tăiere CNC față litere"),
    ("ManoperÄƒ aplicare folie feÈ›e litere", "Manoperă aplicare folie fețe litere"),
    ("Lipire cant pe faÈ›Äƒ (EUR/ml serviciu)", "Lipire cant pe față (EUR/ml serviciu)"),
    ("È˜ablon hÃ¢rtie", "Șablon hârtie"),
    ("Modelare cant profil â€” utilaj", "Modelare cant profil — utilaj"),
    ("faÈ›Äƒ", "față"),
    ("È™ablon", "șablon"),
]


class Utf8TextIntegrityTests(unittest.TestCase):
    def test_clean_utf8_unchanged(self):
        for sample in CLEAN_SAMPLES:
            with self.subTest(sample=sample):
                repaired, classification = safe_repair_text(sample)
                self.assertEqual(repaired, sample)
                self.assertEqual(classification.text_class, TextClass.CLEAN_UTF8)
                self.assertFalse(has_suspicious_mojibake(sample))

    def test_single_pass_confirmed(self):
        for old, expected in SINGLE_PASS:
            with self.subTest(old=old):
                repaired, classification = safe_repair_text(old)
                self.assertEqual(classification.text_class, TextClass.MOJIBAKE_SINGLE_PASS_CONFIRMED)
                self.assertEqual(repaired, expected)
                self.assertFalse(has_suspicious_mojibake(repaired))

    def test_repair_idempotent(self):
        for old, expected in SINGLE_PASS:
            once, _ = safe_repair_text(old)
            twice, classification = safe_repair_text(once)
            self.assertEqual(once, expected)
            self.assertEqual(twice, expected)
            self.assertEqual(classification.text_class, TextClass.CLEAN_UTF8)

    def test_ambiguous_not_changed(self):
        # Lone letters that look similar but are not confirmed mojibake of Romanian words.
        sample = "Brand Ä only"
        # Contains Ä + space pattern — may be suspicious; must not invent a wrong repair.
        repaired, classification = safe_repair_text(sample)
        if classification.text_class not in (
            TextClass.MOJIBAKE_SINGLE_PASS_CONFIRMED,
            TextClass.MOJIBAKE_DOUBLE_PASS_CONFIRMED,
        ):
            self.assertEqual(repaired, sample)

    def test_assert_no_mojibake(self):
        assert_no_mojibake("față")
        with self.assertRaises(AssertionError):
            assert_no_mojibake("faÈ›Äƒ", context="label")

    def test_walk_repair_json(self):
        payload = {
            "label": "TÄƒiere CNC faÈ›Äƒ litere",
            "nested": [{"name": "È˜ablon montaj"}],
            "clean": "preț",
        }
        fixed, audit = walk_repair_json(payload)
        self.assertEqual(fixed["label"], "Tăiere CNC față litere")
        self.assertEqual(fixed["nested"][0]["name"], "Șablon montaj")
        self.assertEqual(fixed["clean"], "preț")
        self.assertGreaterEqual(len(audit), 2)

    def test_repair_source_mixed_file(self):
        body = 'label = "faÈ›Äƒ"\nclean = "față"\n'
        fixed, audit = repair_source_text(body)
        self.assertIn('"față"', fixed)
        self.assertEqual(fixed.count("față"), 2)
        self.assertEqual(len(audit), 1)

    def test_json_roundtrip_preserves_romanian(self):
        payload = {"task": "aplicare folie pe fețe", "price": "12 €", "dash": "a — b"}
        raw = json.dumps(payload, ensure_ascii=False)
        loaded = json.loads(raw)
        self.assertEqual(loaded, payload)
        for value in loaded.values():
            assert_no_mojibake(value)

    def test_build4_volumetric_seed_labels_are_clean_utf8(self):
        from seeds.seed_build4_templates import _volumetric_letters_components

        components = _volumetric_letters_components()
        raw = json.dumps(components, ensure_ascii=False)
        assert_no_mojibake(raw, context="TPL-VOLUMETRIC-LETTERS")
        self.assertIn("față", raw)
        self.assertIn("Manoperă", raw)
        self.assertIn("—", raw)
        self.assertNotIn("faÈ", raw)
        self.assertNotIn("Äƒ", raw)


class Utf8HttpJsonTests(unittest.TestCase):
    def test_fastapi_json_response_preserves_romanian(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()

        @app.get("/probe")
        def probe():
            return {
                "label": "Lipire cant pe față",
                "dash": "a — b",
                "euro": "12 €",
            }

        client = TestClient(app)
        response = client.get("/probe")
        self.assertEqual(response.status_code, 200)
        # Starlette JSONResponse encodes UTF-8; charset may be omitted but body is Unicode.
        body = response.content.decode("utf-8")
        self.assertIn("față", body)
        self.assertIn("—", body)
        self.assertIn("€", body)
        assert_no_mojibake(body)
        self.assertEqual(response.json()["label"], "Lipire cant pe față")


if __name__ == "__main__":
    unittest.main()
