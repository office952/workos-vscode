"""W1-L-FINISH — canonical finish truth persistence through save/normalize."""

from __future__ import annotations

from schemas.intake_v4 import IntakeV4ArtworkFinish, IntakeV4FinishSetup, IntakeV4LetterGroupFinish
from services.form_system_runtime_capture_read_model_service import build_form_system_runtime_capture_read_model
from services.intake_v4_finish_truth_service import (
    artwork_finish_runtime_boolean_state,
    normalize_intake_v4_finish_setup,
)


def _confirmed_artwork_setup() -> IntakeV4FinishSetup:
    return IntakeV4FinishSetup(
        face_finish_type="oracal_651",
        return_finish_type="standard_aluminum",
        return_depth_mm=60,
        confirmed=True,
        letter_group_finishes=[
            IntakeV4LetterGroupFinish(
                group_key="group-a",
                layer_name="A",
                face_finish_type="oracal_651",
                return_finish_type="standard_aluminum",
                return_depth_mm=60,
                confirmed=True,
            ),
        ],
        artwork_finishes=[
            IntakeV4ArtworkFinish(
                layer_key="logo-left",
                execution_type="print_laminate",
                confirmed=True,
            ),
            IntakeV4ArtworkFinish(
                layer_key="logo-right",
                execution_type="cut_vinyl",
                confirmed=True,
            ),
        ],
    )


def test_normalize_persists_finish_target_and_artwork_booleans_for_runtime_capture():
    normalized = normalize_intake_v4_finish_setup(_confirmed_artwork_setup())
    assert normalized.finish_target == "all"
    assert normalized.artwork_finishes[0].print_required is True
    assert normalized.artwork_finishes[0].lamination_required is True
    assert normalized.artwork_finishes[1].print_required is False
    assert normalized.artwork_finishes[1].lamination_required is False


def test_runtime_capture_agrees_with_persisted_finish_truth():
    normalized = normalize_intake_v4_finish_setup(_confirmed_artwork_setup())
    payload = {"finish_setup": normalized.model_dump(mode="json")}
    read_model = build_form_system_runtime_capture_read_model(payload)
    fields = {item["field_key"]: item for item in read_model["fields"]}

    assert fields["finish.finish_target"]["state"] == "confirmed"
    assert fields["finish.finish_target"]["blockers"] == []
    assert fields["finish.print_required"]["state"] == "confirmed"
    assert fields["finish.lamination_required"]["state"] == "confirmed"


def test_changing_execution_type_clears_stale_booleans_on_renormalize():
    setup = IntakeV4FinishSetup(
        confirmed=True,
        artwork_finishes=[
            IntakeV4ArtworkFinish(
                layer_key="logo-left",
                execution_type="print_laminate",
                print_required=True,
                lamination_required=True,
                confirmed=True,
            ),
        ],
    )
    first = normalize_intake_v4_finish_setup(setup)
    assert first.artwork_finishes[0].print_required is True

    mutated = first.model_copy(
        update={
            "artwork_finishes": [
                first.artwork_finishes[0].model_copy(update={"execution_type": "cut_vinyl"}),
            ],
        }
    )
    second = normalize_intake_v4_finish_setup(mutated)
    assert second.artwork_finishes[0].print_required is False
    assert second.artwork_finishes[0].lamination_required is False
    assert artwork_finish_runtime_boolean_state(second, "print_required")["status"] == "confirmed"
