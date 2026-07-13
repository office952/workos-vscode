"""Intake V4 finish truth — per-layer resolution vs stale globals."""

from __future__ import annotations

from schemas.intake_v4 import IntakeV4ArtworkFinish, IntakeV4FinishSetup, IntakeV4LetterGroupFinish
from services.intake_v4_finish_truth_service import (
    any_letter_group_face_vinyl_required,
    dump_intake_v4_finish_setup_for_persist,
    format_intake_v4_return_finish_operator_label,
    mounting_scope_runtime_state,
    normalize_intake_v4_finish_setup,
    resolve_effective_return_finish_label,
    support_type_runtime_state,
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


def test_mounting_scope_persists_through_finish_setup_schema():
    setup = IntakeV4FinishSetup.model_validate(
        {
            "mounting_scope": "mounting_included",
            "mounting_system": "steel_bars",
        }
    )

    assert setup.mounting_scope == "mounting_included"
    assert setup.model_dump(mode="json")["mounting_scope"] == "mounting_included"


def test_mounting_scope_runtime_state_requires_explicit_value_and_confirmation():
    assert mounting_scope_runtime_state(None)["status"] == "missing"

    missing = mounting_scope_runtime_state(
        {
            "confirmed": True,
            "mounting_system": "steel_bars",
            "support_type": "steel_frame",
        }
    )
    assert missing["status"] == "missing"
    assert missing["blocker_code"] == "MOUNTING_SCOPE_MISSING"

    unconfirmed = mounting_scope_runtime_state(
        {
            "confirmed": False,
            "mounting_scope": "mounting_included",
        }
    )
    assert unconfirmed["status"] == "unconfirmed"
    assert unconfirmed["blocker_code"] == "MOUNTING_SCOPE_MISSING"

    confirmed = mounting_scope_runtime_state(
        {
            "confirmed": True,
            "mounting_scope": "mounting_included",
            "mounting_system": "steel_bars",
            "support_type": "steel_frame",
        }
    )
    assert confirmed["status"] == "confirmed"
    assert confirmed["value"] == "mounting_included"


def test_support_type_persists_through_finish_setup_schema():
    setup = IntakeV4FinishSetup.model_validate(
        {
            "support_type": "steel_frame",
            "mounting_system": "steel_bars",
            "mounting_scope": "mounting_included",
        }
    )

    assert setup.support_type == "steel_frame"
    assert setup.model_dump(mode="json")["support_type"] == "steel_frame"


def test_support_type_runtime_state_requires_explicit_value_and_confirmation():
    assert support_type_runtime_state(None)["status"] == "missing"

    missing = support_type_runtime_state(
        {
            "confirmed": True,
            "support_required": "yes",
            "mounting_system": "steel_bars",
            "mounting_scope": "mounting_included",
        }
    )
    assert missing["status"] == "missing"
    assert missing["blocker_code"] == "SUPPORT_TYPE_MISSING"

    unconfirmed = support_type_runtime_state(
        {
            "confirmed": False,
            "support_type": "steel_frame",
            "support_required": "yes",
        }
    )
    assert unconfirmed["status"] == "unconfirmed"
    assert unconfirmed["blocker_code"] == "SUPPORT_TYPE_MISSING"

    confirmed = support_type_runtime_state(
        {
            "confirmed": True,
            "support_type": "steel_frame",
            "support_required": "yes",
            "mounting_system": "steel_bars",
            "mounting_scope": "mounting_included",
            "support_source": "detected_svg",
        }
    )
    assert confirmed["status"] == "confirmed"
    assert confirmed["value"] == "steel_frame"


def test_format_return_finish_operator_labels():
    assert format_intake_v4_return_finish_operator_label("oracal_wrapped") == "Oracal 651"
    assert format_intake_v4_return_finish_operator_label("white_aluminum") == "Alb"
    assert format_intake_v4_return_finish_operator_label("standard_aluminum") == "Argintiu"
    assert format_intake_v4_return_finish_operator_label(None) == "Alb"


def test_normalize_preserves_legacy_global_backing_when_layers_have_none():
    setup = IntakeV4FinishSetup(
        backing_mode="forex_10_with_bevel",
        back_bevel_enabled=True,
        letter_group_finishes=[
            IntakeV4LetterGroupFinish(
                group_key="a",
                layer_name="A",
                face_finish_type="oracal_651",
                return_finish_type="standard_aluminum",
            ),
        ],
    )
    normalized = normalize_intake_v4_finish_setup(setup)
    assert normalized.backing_mode == "forex_10_with_bevel"
    assert normalized.back_bevel_enabled is True
    assert normalized.letter_group_finishes[0].backing_mode is None


def test_normalize_strips_global_backing_mirror_when_layer_explicit():
    setup = IntakeV4FinishSetup(
        backing_mode="forex_10_no_bevel",
        back_bevel_enabled=False,
        letter_group_finishes=[
            IntakeV4LetterGroupFinish(
                group_key="a",
                layer_name="A",
                face_finish_type="oracal_651",
                return_finish_type="standard_aluminum",
                backing_mode="forex_10_with_bevel",
            ),
            IntakeV4LetterGroupFinish(
                group_key="b",
                layer_name="B",
                face_finish_type="oracal_651",
                return_finish_type="standard_aluminum",
            ),
        ],
    )
    normalized = normalize_intake_v4_finish_setup(setup)
    dumped = normalized.model_dump(mode="json")
    assert dumped.get("backing_mode") is None
    assert dumped.get("back_bevel_enabled") is None
    assert normalized.letter_group_finishes[0].backing_mode == "forex_10_with_bevel"
    assert normalized.letter_group_finishes[1].backing_mode == "forex_10_no_bevel"


def test_normalize_mixed_layers_keep_independent_backing_values():
    setup = IntakeV4FinishSetup(
        backing_mode="forex_10_no_bevel",
        letter_group_finishes=[
            IntakeV4LetterGroupFinish(
                group_key="a",
                layer_name="A",
                backing_mode="forex_10_no_bevel",
            ),
            IntakeV4LetterGroupFinish(
                group_key="b",
                layer_name="B",
                backing_mode="forex_10_with_bevel",
            ),
        ],
    )
    normalized = normalize_intake_v4_finish_setup(setup)
    assert normalized.letter_group_finishes[0].backing_mode == "forex_10_no_bevel"
    assert normalized.letter_group_finishes[1].backing_mode == "forex_10_with_bevel"
    assert normalized.model_dump(mode="json").get("backing_mode") is None


def test_normalize_artwork_explicit_backing_strips_global_mirror():
    setup = IntakeV4FinishSetup(
        backing_mode="forex_10_with_bevel",
        artwork_finishes=[
            IntakeV4ArtworkFinish(
                layer_key="logo",
                layer_name="Logo",
                execution_type="needs_decision",
                backing_mode="forex_10_no_bevel",
            ),
        ],
    )
    normalized = normalize_intake_v4_finish_setup(setup)
    assert normalized.model_dump(mode="json").get("backing_mode") is None
    assert normalized.artwork_finishes[0].backing_mode == "forex_10_no_bevel"


def test_dump_for_persist_omits_global_mirror_keys():
    setup = IntakeV4FinishSetup(
        backing_mode="forex_10_no_bevel",
        back_bevel_enabled=False,
        letter_group_finishes=[
            IntakeV4LetterGroupFinish(
                group_key="a",
                layer_name="A",
                backing_mode="forex_10_with_bevel",
            ),
        ],
    )
    normalized = normalize_intake_v4_finish_setup(setup)
    dumped = dump_intake_v4_finish_setup_for_persist(normalized)
    assert "backing_mode" not in dumped
    assert "back_bevel_enabled" not in dumped
    assert dumped["letter_group_finishes"][0]["backing_mode"] == "forex_10_with_bevel"
