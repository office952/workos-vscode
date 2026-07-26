"""Return/cant finish truth normalization and runtime state."""

from __future__ import annotations

from schemas.intake_v4 import IntakeV4ArtworkFinish, IntakeV4FinishSetup, IntakeV4LetterGroupFinish
from services.intake_v4_finish_truth_service import normalize_intake_v4_finish_setup
from services.return_cant_finish_truth_service import (
    normalize_return_cant_finish_setup,
    return_finish_method_for_type,
    return_finish_requires_color_fields,
)
from services.return_cant_product_truth_bridge import build_return_cant_runtime_product_truth
from services.return_cant_runtime_state import return_cant_runtime_state


def test_return_finish_method_for_stock_oracal_and_ral() -> None:
    assert return_finish_method_for_type("white_aluminum") == "stock_color"
    assert return_finish_method_for_type("oracal_wrapped") == "vinyl_application"
    assert return_finish_method_for_type("ral_paint") == "paint_application"
    assert return_finish_method_for_type("none") is None


def test_normalize_clears_stale_color_when_switching_to_stock() -> None:
    setup = IntakeV4FinishSetup(
        confirmed=True,
        letter_group_finishes=[
            IntakeV4LetterGroupFinish(
                group_key="group-a",
                return_finish_type="white_aluminum",
                return_depth_mm=60,
                return_oracal_code="651-070",
                return_oracal_name="Black",
            ),
        ],
    )
    normalized = normalize_return_cant_finish_setup(setup)
    row = normalized.letter_group_finishes[0]
    assert row.return_oracal_code is None
    assert row.return_oracal_name is None


def test_normalize_hydrates_missing_row_depth_from_global() -> None:
    setup = IntakeV4FinishSetup(
        confirmed=True,
        return_depth_mm=80,
        return_finish_type="white_aluminum",
        artwork_finishes=[
            IntakeV4ArtworkFinish(
                layer_key="logo-left",
                return_finish_type="white_aluminum",
                return_depth_mm=None,
            ),
        ],
    )
    normalized = normalize_return_cant_finish_setup(setup)
    assert normalized.artwork_finishes[0].return_depth_mm == 80


def test_normalize_requires_color_fields_only_for_oracal_and_ral() -> None:
    assert return_finish_requires_color_fields("oracal_wrapped") is True
    assert return_finish_requires_color_fields("ral_paint") is True
    assert return_finish_requires_color_fields("white_aluminum") is False


def test_finish_setup_save_path_applies_return_cant_normalization() -> None:
    setup = IntakeV4FinishSetup(
        confirmed=True,
        return_finish_type="white_aluminum",
        return_depth_mm=60,
        letter_group_finishes=[
            IntakeV4LetterGroupFinish(
                group_key="pseudo:maria",
                return_finish_type="white_aluminum",
            ),
        ],
        artwork_finishes=[
            IntakeV4ArtworkFinish(
                layer_key="logo-left",
                execution_type="print_laminate",
                return_finish_type="white_aluminum",
            ),
        ],
    )
    normalized = normalize_intake_v4_finish_setup(setup)
    assert normalized.letter_group_finishes[0].return_depth_mm == 60
    assert normalized.artwork_finishes[0].return_depth_mm == 60


def test_return_cant_runtime_state_confirmed_from_product_truth_bridge() -> None:
    payload = {
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "pseudo:maria",
                    "layer_id": "pseudo:maria",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                }
            ],
        },
        "quote_geometry": {"letter_perimeter_m": 18.5, "confirmed": True},
        "finish_setup": {
            "confirmed": True,
            "return_finish_type": "white_aluminum",
            "return_depth_mm": 60,
            "letter_group_finishes": [
                {
                    "group_key": "pseudo:maria",
                    "layer_name": "maria",
                    "return_finish_type": "white_aluminum",
                    "return_depth_mm": 60,
                }
            ],
            "artwork_finishes": [],
        },
    }
    payload["product_truth"] = build_return_cant_runtime_product_truth(payload)
    runtime = return_cant_runtime_state(payload)
    assert runtime["status"] == "confirmed"
    assert runtime["depth_mm"] == 60
    assert runtime["material_profile"] == "MAT-PROFIL-LATERAL-LITERE-60MM"
    assert runtime["layer_group_ids"] == ["pseudo:maria"]
    assert runtime["operator_blockers"] == []
