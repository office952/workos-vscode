from __future__ import annotations

from services.form_system_contract_backbone_service import build_form_system_contract_map
from services.linked_template_runtime_segment_extraction_service import (
    extract_linked_template_segments_from_workspace_payload,
)


ROOT = "TPL-VOLUMETRIC-LETTERS_v2"
LOGO = "TPL-VOLUMETRIC-LOGO_v1"


def _composition() -> dict:
    return build_form_system_contract_map(ROOT)["linked_template_composition"]


def _payload() -> dict:
    return {
        "layer_role_setup": {
            "layers": [
                {
                    "layer_key": "logo-stanga",
                    "layer_id": "logo-stanga",
                    "layer_name": "logo stanga",
                    "auto_role": "printed_artwork",
                    "confirmed_role": "printed_artwork",
                    "confirmation_state": "confirmed",
                },
                {
                    "layer_key": "logo-dreapta",
                    "layer_id": "logo-dreapta",
                    "layer_name": "logo dreapta",
                    "auto_role": "printed_artwork",
                    "confirmed_role": "printed_artwork",
                    "confirmation_state": "confirmed",
                },
            ],
            "layer_bindings": [
                {
                    "layer_key": "logo-stanga",
                    "source_layer_name": "logo stanga",
                    "suggested_semantic_role": "printed_artwork",
                    "confirmed_semantic_role": "printed_artwork",
                    "target_template_code": LOGO,
                    "target_module_code": "logo_finish",
                    "binding_status": "suggested",
                    "binding_reason": "additional_template_suggestion_requires_binding_confirmation",
                },
                {
                    "layer_key": "logo-dreapta",
                    "source_layer_name": "logo dreapta",
                    "suggested_semantic_role": "printed_artwork",
                    "confirmed_semantic_role": "printed_artwork",
                    "target_template_code": LOGO,
                    "target_module_code": "logo_finish",
                    "binding_status": "suggested",
                    "binding_reason": "additional_template_suggestion_requires_binding_confirmation",
                },
            ],
        },
        "finish_setup": {
            "confirmed": True,
            "artwork_finishes": [
                {
                    "layer_key": "logo-stanga",
                    "layer_name": "logo stanga",
                    "execution_type": "print_laminate",
                    "color_mode": "polychrome",
                    "print_transparency": "translucent",
                    "return_finish_type": "white_aluminum",
                    "return_depth_mm": 60,
                    "confirmed": True,
                },
                {
                    "layer_key": "logo-dreapta",
                    "layer_name": "logo dreapta",
                    "execution_type": "print_laminate",
                    "color_mode": "polychrome",
                    "print_transparency": "translucent",
                    "return_finish_type": "white_aluminum",
                    "return_depth_mm": 60,
                    "confirmed": True,
                },
            ],
        },
    }


def _extract(payload: dict | None = None, root: str = ROOT, composition: dict | None = None) -> dict:
    return extract_linked_template_segments_from_workspace_payload(
        root_template_code=root,
        workspace_payload=payload if payload is not None else _payload(),
        linked_template_composition=composition if composition is not None else _composition(),
    )


def test_extracts_logo_left_right_segments():
    result = _extract()

    assert result["summary"]["segments_count"] == 2
    assert {segment["segment_key"] for segment in result["segments"]} == {"logo-stanga", "logo-dreapta"}


def test_preserves_root_child_ownership_and_role():
    result = _extract()

    assert result["root_template_code"] == ROOT
    for segment in result["segments"]:
        assert segment["parent_root_template_code"] == ROOT
        assert segment["owning_template_code"] == LOGO
        assert segment["composition_role"] == "linked_logo_segment"
        assert segment["product_truth_path"].startswith(f"linked_templates.{LOGO}.segments.")


def test_preserves_suggested_binding_without_root_activation():
    result = _extract()

    assert result["summary"]["suggested_binding_count"] == 2
    assert result["summary"]["root_offerable_activation"] is False
    assert result["summary"]["separate_quote_activation"] is False
    for segment in result["segments"]:
        assert segment["binding_status"] == "suggested"
        assert "binding_status_suggested_requires_product_truth_confirmation_boundary" in segment["warnings"]


def test_suggested_binding_produces_partial_readiness():
    result = _extract()

    for segment in result["segments"]:
        readiness = segment["product_truth_readiness"]
        assert readiness["status"] == "partial"
        assert readiness["is_ready"] is False
        assert readiness["reason"] == "template_binding_suggested"
        assert readiness["binding_status"] == "suggested"
        assert readiness["template_binding_confirmed"] is False
        assert readiness["blockers"][0]["code"] == "LINKED_TEMPLATE_BINDING_SUGGESTED"


def test_confirmed_finish_does_not_imply_quote_readiness():
    result = _extract()

    for segment in result["segments"]:
        readiness = segment["product_truth_readiness"]
        assert readiness["finish_confirmed"] is True
        assert readiness["layer_role_confirmed"] is True
        assert readiness["ready_for_pricing"] is False
        assert readiness["ready_for_quote"] is False
        assert readiness["ready_for_order"] is False
        assert readiness["ready_for_execution"] is False


def test_preserves_finish_confirmation_separately_from_binding_suggestion():
    result = _extract()

    assert result["summary"]["confirmed_segments_count"] == 2
    assert result["summary"]["product_truth_readiness_status"] == "partial_binding_suggested"
    for segment in result["segments"]:
        assert segment["state"] == "confirmed"
        assert segment["finish"] == {
            "execution_type": "print_laminate",
            "color_mode": "polychrome",
            "print_transparency": "translucent",
            "return_finish_type": "white_aluminum",
            "return_depth_mm": 60,
            "confirmed": True,
        }
        assert segment["binding_status"] == "suggested"


def test_marks_missing_finish_without_inventing_confirmation():
    payload = _payload()
    payload["finish_setup"]["artwork_finishes"] = payload["finish_setup"]["artwork_finishes"][:1]

    result = _extract(payload)
    missing_finish = next(segment for segment in result["segments"] if segment["segment_key"] == "logo-dreapta")

    assert result["summary"]["segments_count"] == 2
    assert result["summary"]["missing_finish_count"] == 1
    assert missing_finish["state"] == "missing_finish"
    assert missing_finish["finish"]["confirmed"] is False
    assert "artwork_finish_missing" in missing_finish["warnings"]
    assert missing_finish["product_truth_readiness"]["status"] == "blocked"
    assert missing_finish["product_truth_readiness"]["reason"] == "missing_finish"
    assert missing_finish["product_truth_readiness"]["blockers"][0]["code"] == "LINKED_SEGMENT_FINISH_MISSING"


def test_missing_binding_produces_blocked_readiness():
    payload = _payload()
    payload["layer_role_setup"]["layer_bindings"] = payload["layer_role_setup"]["layer_bindings"][:1]

    result = _extract(payload)
    missing_binding = next(segment for segment in result["segments"] if segment["segment_key"] == "logo-dreapta")

    assert result["summary"]["missing_binding_count"] == 1
    assert missing_binding["binding_status"] == "missing"
    assert missing_binding["product_truth_readiness"]["status"] == "blocked"
    assert missing_binding["product_truth_readiness"]["reason"] == "missing_linked_template_binding"
    assert missing_binding["product_truth_readiness"]["blockers"][0]["code"] == "LINKED_TEMPLATE_BINDING_MISSING"


def test_confirmed_binding_can_produce_ready_segment_but_no_downstream_activation():
    payload = _payload()
    for binding in payload["layer_role_setup"]["layer_bindings"]:
        binding["binding_status"] = "confirmed"

    result = _extract(payload)

    assert result["product_truth_readiness_summary"]["status"] == "ready"
    for segment in result["segments"]:
        readiness = segment["product_truth_readiness"]
        assert readiness["status"] == "ready"
        assert readiness["is_ready"] is True
        assert readiness["template_binding_confirmed"] is True
        assert readiness["ready_for_quote"] is False
    assert result["summary"]["root_offerable_activation"] is False
    assert result["summary"]["separate_quote_activation"] is False
    assert result["summary"]["task_graph_activation"] is False


def test_no_downstream_activation():
    result = _extract()
    summary = result["summary"]

    assert summary["root_offerable_activation"] is False
    assert summary["separate_quote_activation"] is False
    assert summary["task_graph_activation"] is False
    assert all(segment["quote_policy"] == "no_separate_quote" for segment in result["segments"])
    assert all(segment["task_policy"] == "emit_intents_merge_later_no_task_runtime_now" for segment in result["segments"])

def test_summary_partial_for_two_suggested_logo_bindings():
    result = _extract()
    summary = result["product_truth_readiness_summary"]

    assert summary["status"] == "partial"
    assert summary["ready_segments_count"] == 0
    assert summary["partial_segments_count"] == 2
    assert summary["blocked_segments_count"] == 0
    assert summary["pricing_ready"] is False
    assert summary["quote_ready"] is False
    assert summary["execution_ready"] is False
    assert summary["reason"] == "linked_template_binding_suggested"
    assert summary["warnings_count"] == 2

def test_summary_blocked_when_missing_required_data():
    payload = _payload()
    payload["finish_setup"]["artwork_finishes"] = []

    result = _extract(payload)
    summary = result["product_truth_readiness_summary"]

    assert summary["status"] == "blocked"
    assert summary["ready_segments_count"] == 0
    assert summary["partial_segments_count"] == 0
    assert summary["blocked_segments_count"] == 2
    assert summary["reason"] == "linked_segment_required_data_missing"

def test_readiness_includes_product_truth_path():
    result = _extract()

    for segment in result["segments"]:
        assert segment["product_truth_readiness"]["product_truth_path"] == segment["product_truth_path"]
        assert segment["product_truth_readiness"]["product_truth_path"].startswith(
            f"linked_templates.{LOGO}.segments."
        )

def test_handles_empty_payload_safely():
    result = _extract({})

    assert result["segments"] == []
    assert result["product_truth_readiness_summary"]["status"] == "not_applicable"
    assert result["summary"]["segments_count"] == 0
    assert result["summary"]["confirmed_segments_count"] == 0
    assert result["summary"]["suggested_binding_count"] == 0
    assert result["summary"]["missing_finish_count"] == 0
    assert result["summary"]["missing_binding_count"] == 0
    assert result["summary"]["product_truth_readiness_status"] == "no_runtime_segments"


def test_rejects_non_linked_root_and_missing_composition_safely():
    non_linked = _extract(root="TPL-VOLUMETRIC-LOGO_v1")
    missing_composition = _extract(composition={})

    assert non_linked["segments"] == []
    assert non_linked["summary"]["status"] == "non_linked_root"
    assert missing_composition["segments"] == []
    assert missing_composition["summary"]["status"] == "composition_root_mismatch"