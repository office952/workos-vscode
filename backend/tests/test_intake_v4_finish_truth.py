"""Intake V4 finish truth — per-layer resolution vs stale globals."""

from __future__ import annotations

from schemas.intake_v4 import IntakeV4ArtworkFinish, IntakeV4FinishSetup, IntakeV4LetterGroupFinish
from services.intake_v4_finish_truth_service import (
    any_letter_group_face_vinyl_required,
    format_intake_v4_return_finish_operator_label,
    normalize_intake_v4_finish_setup,
    resolve_effective_return_finish_label,
)


def test_any_group_face_none_skips_vinyl_with_stale_global():
    groups = [
        {"face_finish_type": "none", "return_finish_type": "standard_aluminum"},
        {"face_finish_type": "none", "return_finish_type": "standard_aluminum"},
    ]
    assert any_letter_group_face_vinyl_required(groups, "oracal_651") is False


def test_resolve_return_finish_from_groups_not_global():
    groups = [{"return_finish_type": "standard_aluminum"}]
    label = resolve_effective_return_finish_label(groups, [], "oracal_wrapped")
    assert label == "standard_aluminum"


def test_normalize_syncs_globals_from_layer_groups():
    setup = IntakeV4FinishSetup(
        face_finish_type="oracal_651",
        return_finish_type="oracal_wrapped",
        letter_group_finishes=[
            IntakeV4LetterGroupFinish(
                group_key="a",
                layer_name="A",
                face_finish_type="none",
                return_finish_type="standard_aluminum",
                return_depth_mm=60,
            ),
            IntakeV4LetterGroupFinish(
                group_key="b",
                layer_name="B",
                face_finish_type="none",
                return_finish_type="standard_aluminum",
                return_depth_mm=60,
            ),
        ],
        artwork_finishes=[
            IntakeV4ArtworkFinish(
                layer_key="art",
                layer_name="Art",
                execution_type="needs_decision",
                return_finish_type="standard_aluminum",
                return_depth_mm=60,
            )
        ],
    )
    normalized = normalize_intake_v4_finish_setup(setup)
    assert normalized.face_finish_type == "none"
    assert normalized.return_finish_type == "standard_aluminum"
    assert normalized.return_depth_mm == 60


def test_artwork_print_transparency_persists_through_finish_setup_schema():
    setup = IntakeV4FinishSetup.model_validate(
        {
            "artwork_finishes": [
                {
                    "layer_key": "logo",
                    "layer_name": "Logo",
                    "execution_type": "print_laminate",
                    "color_mode": "polychrome",
                    "print_transparency": "transparent",
                    "return_finish_type": "standard_aluminum",
                    "return_depth_mm": 60,
                }
            ],
        }
    )

    assert setup.artwork_finishes[0].print_transparency == "transparent"
    assert setup.model_dump(mode="json")["artwork_finishes"][0]["print_transparency"] == "transparent"


def test_artwork_print_and_lamination_booleans_persist_through_finish_setup_schema():
    setup = IntakeV4FinishSetup.model_validate(
        {
            "artwork_finishes": [
                {
                    "layer_key": "logo",
                    "layer_name": "Logo",
                    "print_required": True,
                    "lamination_required": False,
                }
            ],
        }
    )

    assert setup.artwork_finishes[0].print_required is True
    assert setup.artwork_finishes[0].lamination_required is False
    dumped = setup.model_dump(mode="json")["artwork_finishes"][0]
    assert dumped["print_required"] is True
    assert dumped["lamination_required"] is False


def test_format_return_finish_operator_labels():
    assert format_intake_v4_return_finish_operator_label("oracal_wrapped") == "Oracal 651"
    assert format_intake_v4_return_finish_operator_label("white_aluminum") == "Alb"
    assert format_intake_v4_return_finish_operator_label("standard_aluminum") == "Argintiu"
    assert format_intake_v4_return_finish_operator_label(None) == "Alb"
