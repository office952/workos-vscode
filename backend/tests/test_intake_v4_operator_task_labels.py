"""Tests for Intake V4 operator-facing task label overrides."""

from __future__ import annotations

from services.intake_v4_operator_task_labels import operator_task_label_for_seed


class TestIntakeV4OperatorTaskLabels:
    def test_return_vinyl_workbench_label(self):
        label = operator_task_label_for_seed(
            "return_vinyl_application_workbench",
            "Colantare cant la banc de lucru",
        )
        assert label == "Aplicare Oracal 651 pe cant / volum la banc de lucru"
        assert "Colantare cant" not in label

    def test_face_vinyl_final_label(self):
        label = operator_task_label_for_seed(
            "face_vinyl_application_final",
            "Colantare finală fețe litere",
        )
        assert label == "Aplicare autocolant pe fețele literelor"

    def test_unknown_seed_preserves_catalog_label(self):
        assert operator_task_label_for_seed("cnc_file_preparation", "Pregătire fișiere CNC") == (
            "Pregătire fișiere CNC"
        )
