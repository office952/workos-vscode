"""Intake V4 return finish adapter normalization."""

from __future__ import annotations

from schemas.intake_v4 import IntakeV4FinishSetup, IntakeV4LetterGroupFinish
from services.intake_v4_finish_adapter import finish_assignment_from_v4_setup


def test_painted_return_preserves_ral_code_from_return_oracal_code():
    setup = IntakeV4FinishSetup(
        face_finish_type="none",
        return_finish_type="ral_paint",
        return_oracal_code="9005",
        return_depth_mm=60,
        confirmed=True,
        letter_group_finishes=[
            IntakeV4LetterGroupFinish(
                group_key="a",
                layer_name="A",
                face_finish_type="none",
                return_finish_type="ral_paint",
                return_oracal_code="9005",
                return_depth_mm=60,
            )
        ],
    )
    assignment = finish_assignment_from_v4_setup(setup)
    assert assignment is not None
    group = assignment.active_groups()[0]
    assert group.return_finish.finish_type == "painted"
    assert group.return_finish.color_code == "9005"


def test_gold_aluminum_return_maps_to_raw_material():
    setup = IntakeV4FinishSetup(
        face_finish_type="none",
        return_finish_type="gold_aluminum",
        return_depth_mm=60,
        confirmed=True,
        letter_group_finishes=[
            IntakeV4LetterGroupFinish(
                group_key="a",
                layer_name="A",
                face_finish_type="none",
                return_finish_type="gold_aluminum",
                return_depth_mm=60,
            )
        ],
    )
    assignment = finish_assignment_from_v4_setup(setup)
    group = assignment.active_groups()[0]
    assert group.return_finish.finish_type == "raw_material"
    assert group.return_finish.material_code == "gold_aluminum"
