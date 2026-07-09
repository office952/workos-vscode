from __future__ import annotations

from services.form_system_runtime_capture_read_model_service import (
    build_form_system_runtime_capture_read_model,
)


ROOT = "TPL-VOLUMETRIC-LETTERS_v2"


def _by_key(model: dict) -> dict[str, dict]:
    return {field["field_key"]: field for field in model["fields"]}


def _complete_payload() -> dict:
    return {
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "face-1",
                    "layer_id": "face-1",
                    "layer_name": "face 1",
                    "auto_role": "face",
                    "auto_confidence": "high",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                }
            ],
            "warnings": [],
        },
        "svg": {
            "selected_layer_refs": [
                {
                    "layer_id": "face-1",
                    "role": "vector_litere",
                    "source": "operator_confirmed_layer_role",
                    "confirmed": True,
                }
            ]
        },
        "finish_setup": {
            "finish_target": "face",
            "confirmed": True,
            "artwork_finishes": [
                {
                    "layer_key": "logo-left",
                    "print_required": True,
                    "lamination_required": False,
                },
                {
                    "layer_key": "logo-right",
                    "print_required": False,
                    "lamination_required": True,
                },
            ],
            "mounting_scope": "mounting_included",
            "mounting_system": "steel_bars",
            "support_type": "steel_frame",
            "support_required": "yes",
        },
    }


def test_read_model_returns_all_six_runtime_capture_fields() -> None:
    model = build_form_system_runtime_capture_read_model(_complete_payload(), template_code=ROOT)
    by_key = _by_key(model)

    assert model["read_only"] is True
    assert set(by_key) == {
        "svg.selected_layer_refs[]",
        "finish.finish_target",
        "finish.print_required",
        "finish.lamination_required",
        "mounting.mounting_scope",
        "support.support_type",
    }


def test_read_model_marks_all_fields_confirmed_when_payload_is_complete() -> None:
    model = build_form_system_runtime_capture_read_model(_complete_payload(), template_code=ROOT)

    assert all(field["state"] == "confirmed" for field in model["fields"])
    assert all(field["ready_for_product_truth"] is True for field in model["fields"])
    assert model["blockers"] == []


def test_read_model_missing_selected_layer_refs_and_finish_target_stay_blocked() -> None:
    payload = _complete_payload()
    payload.pop("svg")
    payload["finish_setup"].pop("finish_target")

    model = build_form_system_runtime_capture_read_model(payload, template_code=ROOT)
    fields = _by_key(model)

    assert fields["svg.selected_layer_refs[]"]["state"] == "missing"
    assert fields["svg.selected_layer_refs[]"]["blockers"] == ["SELECTED_LAYER_REFS_MISSING"]
    assert fields["finish.finish_target"]["state"] == "blocked"
    assert fields["finish.finish_target"]["blockers"] == ["FINISH_TARGET_MISSING"]


def test_read_model_missing_row_level_print_and_lamination_stay_blocked() -> None:
    payload = _complete_payload()
    payload["finish_setup"]["artwork_finishes"] = [{"layer_key": "logo-left"}]

    model = build_form_system_runtime_capture_read_model(payload, template_code=ROOT)
    fields = _by_key(model)

    assert fields["finish.print_required"]["state"] == "blocked"
    assert fields["finish.print_required"]["blockers"] == ["PRINT_REQUIRED_UNKNOWN"]
    assert fields["finish.lamination_required"]["state"] == "blocked"
    assert fields["finish.lamination_required"]["blockers"] == ["LAMINATION_REQUIRED_UNKNOWN"]


def test_read_model_mounting_scope_and_support_type_do_not_fall_back() -> None:
    payload = _complete_payload()
    payload["finish_setup"].pop("mounting_scope")
    payload["finish_setup"].pop("support_type")
    payload["finish_setup"]["support_source"] = "detected_svg"

    model = build_form_system_runtime_capture_read_model(payload, template_code=ROOT)
    fields = _by_key(model)

    assert fields["mounting.mounting_scope"]["blockers"] == ["MOUNTING_SCOPE_MISSING"]
    assert fields["mounting.mounting_scope"]["ready_for_product_truth"] is False
    assert fields["support.support_type"]["blockers"] == ["SUPPORT_TYPE_MISSING"]
    assert fields["support.support_type"]["ready_for_product_truth"] is False


def test_read_model_has_no_pricing_quote_or_execution_coupling() -> None:
    model = build_form_system_runtime_capture_read_model(_complete_payload(), template_code=ROOT)

    assert all(value is False for value in model["downstream_write_intent"].values())
    serialized = str(model).lower()
    assert "commercial_total" not in serialized
    assert "quote_write': true" not in serialized
    assert "order_write': true" not in serialized
    assert "execution_runtime_write': true" not in serialized
