from __future__ import annotations

from services.letter_group_finish_readiness_service import (
    build_letter_group_finish_readiness_from_workspace_payload,
)


ROOT = "TPL-VOLUMETRIC-LETTERS_v2"


def _layer(group_key: str, name: str, color: str) -> dict:
    return {
        "layer_key": group_key,
        "layer_id": group_key,
        "layer_name": name,
        "auto_role": "face",
        "confirmed_role": "face",
        "confirmation_state": "confirmed",
        "colors": [color],
    }


def _group(group_key: str, name: str, color: str, code: str, oracal_name: str, *, confirmed: bool = False) -> dict:
    return {
        "group_key": group_key,
        "layer_name": name,
        "source_fill_color": color,
        "face_finish_type": "oracal_651",
        "face_oracal_code": code,
        "face_oracal_name": oracal_name,
        "return_finish_type": "white_aluminum",
        "return_depth_mm": 60,
        "confirmed": confirmed,
    }


def _payload(*, confirmed: bool = False) -> dict:
    layers = [
        _layer("pseudo:maria", "pseudo maria (blue)", "#00a0e3"),
        _layer("pseudo:soare", "pseudo soare (red)", "#e31e24"),
        _layer("pseudo:ana", "pseudo ana (green)", "#009846"),
        _layer("pseudo:gradinita", "pseudo gradinita (orange)", "#ef7f1a"),
    ]
    return {
        "product_binding": {"template_code": ROOT},
        "layer_role_setup": {"confirmation_status": "complete", "layers": layers},
        "svg_analysis_json": {"layers": [{"id": item["layer_key"], "name": item["layer_name"], "colors": item["colors"], "autoRole": "face", "layerKind": "pseudo"} for item in layers]},
        "finish_setup": {
            "confirmed": True,
            "letter_group_finishes": [
                {
                    **_group("pseudo:maria", "pseudo maria (blue)", "#00a0e3", "053", "Light blue", confirmed=confirmed),
                    "return_finish_type": "ral_paint",
                    "return_oracal_code": "1002",
                    "return_oracal_name": "Sand yellow",
                },
                _group("pseudo:soare", "pseudo soare (red)", "#e31e24", "047", "Orange red", confirmed=confirmed),
                _group("pseudo:ana", "pseudo ana (green)", "#009846", "062", "Light green", confirmed=confirmed),
                _group("pseudo:gradinita", "pseudo gradinita (orange)", "#ef7f1a", "035", "Pastel orange", confirmed=confirmed),
            ],
        },
    }


def _build(payload: dict | None = None) -> dict:
    return build_letter_group_finish_readiness_from_workspace_payload(payload or _payload(), ROOT)


def test_extracts_four_letter_group_rows_from_payload():
    result = _build()

    assert result["letter_group_finish_readiness_summary"]["groups_count"] == 4
    assert {row["group_key"] for row in result["letter_group_finish_rows"]} == {
        "pseudo:maria",
        "pseudo:soare",
        "pseudo:ana",
        "pseudo:gradinita",
    }


def test_each_row_has_root_role_and_ownership():
    result = _build()

    for row in result["letter_group_finish_rows"]:
        assert row["parent_root_template_code"] == ROOT
        assert row["owning_template_code"] == ROOT
        assert row["role"] == "letter_group_finish"
        assert row["owning_components"]["face_finish"] == "finish_artwork"
        assert row["owning_components"]["return_cant"] == "return_cant"
        assert row["no_component_quote"] is True


def test_svg_evidence_keeps_analyzer_boundaries_explicit():
    result = _build()

    for row in result["letter_group_finish_rows"]:
        evidence = row["svg_evidence"]
        assert evidence["derived_from_svg"] is True
        assert evidence["analyzer_detected_color"] is True
        assert evidence["analyzer_detected_oracal"] is False
        assert evidence["analyzer_detected_cant"] is False
        assert evidence["analyzer_detected_return_depth"] is False
        assert evidence["analyzer_detected_ral_or_white"] is False


def test_face_oracal_is_svg_nearest_mapping_suggested_until_row_confirmed():
    result = _build()
    row = result["letter_group_finish_rows"][0]

    assert row["face_finish"]["source_type"] == "svg_nearest_color_mapping"
    assert row["face_finish"]["state"] == "suggested"
    assert row["face_finish"]["confirmed"] is False
    assert row["face_finish"]["warnings"][0]["code"] == "FACE_ORACAL_NEAREST_MAPPING_NOT_CONFIRMED"


def test_return_cant_is_payload_hydrated_and_not_from_svg():
    result = _build()

    for row in result["letter_group_finish_rows"]:
        assert row["return_cant"]["source_type"] == "payload_hydrated_or_prior_state"
        assert row["return_cant"]["state"] == "hydrated"
        assert row["return_cant"]["warnings"][0]["code"] == "RETURN_CANT_NOT_FROM_SVG"


def test_row_confirmed_false_means_partial_readiness_even_when_global_finish_confirmed():
    result = _build()

    for row in result["letter_group_finish_rows"]:
        readiness = row["product_truth_readiness"]
        assert readiness["status"] == "partial"
        assert readiness["reason"] == "letter_group_not_confirmed"
        assert readiness["confirmed"] is False
        assert readiness["ready_for_quote"] is False
        assert readiness["blockers"][0]["code"] == "LETTER_GROUP_FINISH_NOT_CONFIRMED"


def test_confirmed_rows_can_be_ready_but_never_downstream_ready():
    result = _build(_payload(confirmed=True))

    assert result["letter_group_finish_readiness_summary"]["status"] == "ready"
    for row in result["letter_group_finish_rows"]:
        readiness = row["product_truth_readiness"]
        assert readiness["status"] == "ready"
        assert readiness["is_ready"] is True
        assert readiness["ready_for_pricing"] is False
        assert readiness["ready_for_quote"] is False
        assert readiness["ready_for_execution"] is False
    assert all(value is False for value in result["downstream_write_intent"].values())


def test_missing_face_value_blocks_row():
    payload = _payload()
    payload["finish_setup"]["letter_group_finishes"][0]["face_oracal_code"] = None

    result = _build(payload)
    row = next(item for item in result["letter_group_finish_rows"] if item["group_key"] == "pseudo:maria")

    assert row["product_truth_readiness"]["status"] == "blocked"
    assert row["face_finish"]["warnings"][-1]["code"] == "FACE_ORACAL_COLOR_MISSING"


def test_missing_return_depth_blocks_row():
    payload = _payload()
    payload["finish_setup"]["letter_group_finishes"][0]["return_depth_mm"] = None

    result = _build(payload)
    row = next(item for item in result["letter_group_finish_rows"] if item["group_key"] == "pseudo:maria")

    assert row["product_truth_readiness"]["status"] == "blocked"
    assert row["return_cant"]["warnings"][-1]["code"] == "RETURN_CANT_DEPTH_MISSING"


def test_summary_for_current_workspace_like_data_is_partial_and_downstream_safe():
    result = _build()
    summary = result["letter_group_finish_readiness_summary"]

    assert summary["status"] == "partial"
    assert summary["groups_count"] == 4
    assert summary["ready_groups_count"] == 0
    assert summary["partial_groups_count"] == 4
    assert summary["blocked_groups_count"] == 0
    assert summary["face_suggestions_count"] == 4
    assert summary["return_cant_from_svg_count"] == 0
    assert summary["return_cant_hydrated_count"] == 4
    assert summary["pricing_ready"] is False
    assert summary["quote_ready"] is False
    assert summary["execution_ready"] is False


def test_stale_rows_against_current_analyzer_are_blocked():
    payload = _payload()
    payload["svg_analysis_json"]["layers"] = [
        {
            "id": "single-current-layer",
            "name": "single current layer",
            "colors": ["#111111"],
            "autoRole": "face",
            "layerKind": "real",
        }
    ]
    payload["layer_role_setup"]["layers"] = [
        {
            "layer_key": "single-current-layer",
            "layer_name": "single current layer",
            "auto_role": "face",
            "confirmed_role": "face",
            "confirmation_state": "confirmed",
        }
    ]

    result = _build(payload)

    assert result["letter_group_finish_readiness_summary"]["status"] == "blocked"
    first = result["letter_group_finish_rows"][0]
    assert first["svg_evidence"]["source_mismatch"] is True
    assert first["face_finish"]["warnings"][0]["code"] == "STALE_LETTER_GROUP_FINISH_ROWS"
    assert first["product_truth_readiness"]["status"] == "blocked"