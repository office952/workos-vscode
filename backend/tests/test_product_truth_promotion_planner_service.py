from __future__ import annotations

from services.product_truth_promotion_planner_service import build_product_truth_promotion_plan


ROOT = "TPL-VOLUMETRIC-LETTERS_v2"


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


def _entries_by_key(entries: list[dict]) -> dict[str, list[dict]]:
    by_key: dict[str, list[dict]] = {}
    for entry in entries:
        by_key.setdefault(entry["field_key"], []).append(entry)
    return by_key


def test_planner_marks_all_confirmed_runtime_capture_entries_eligible() -> None:
    plan = build_product_truth_promotion_plan(_complete_payload(), template_code=ROOT)
    eligible = _entries_by_key(plan["eligible_entries"])

    assert plan["planner_version"] == "v1"
    assert plan["blocked_entries"] == []
    assert set(eligible) == {
        "svg.selected_layer_refs[]",
        "finish.finish_target",
        "finish.print_required",
        "finish.lamination_required",
        "mounting.mounting_scope",
        "support.support_type",
    }
    assert len(eligible["svg.selected_layer_refs[]"]) == 1
    assert len(eligible["finish.print_required"]) == 2
    assert len(eligible["finish.lamination_required"]) == 2
    assert all(entry["promotion_allowed"] is True for entry in plan["eligible_entries"])


def test_planner_blocks_missing_finish_target() -> None:
    payload = _complete_payload()
    payload["finish_setup"].pop("finish_target")

    plan = build_product_truth_promotion_plan(payload, template_code=ROOT)
    blocked = _entries_by_key(plan["blocked_entries"])

    assert blocked["finish.finish_target"][0]["promotion_allowed"] is False
    assert blocked["finish.finish_target"][0]["blockers"] == ["FINISH_TARGET_MISSING"]


def test_planner_blocks_missing_selected_layer_refs() -> None:
    payload = _complete_payload()
    payload.pop("svg")

    plan = build_product_truth_promotion_plan(payload, template_code=ROOT)
    blocked = _entries_by_key(plan["blocked_entries"])

    assert blocked["svg.selected_layer_refs[]"][0]["promotion_allowed"] is False
    assert blocked["svg.selected_layer_refs[]"][0]["blockers"] == ["SELECTED_LAYER_REFS_MISSING"]


def test_planner_blocks_print_and_lamination_without_row_identity_or_explicit_boolean() -> None:
    payload = _complete_payload()
    payload["finish_setup"]["artwork_finishes"] = [
        {
            "layer_key": "   ",
            "print_required": True,
            "lamination_required": False,
        },
        {
            "layer_key": "logo-left",
            "execution_type": "print_laminate",
        },
    ]

    plan = build_product_truth_promotion_plan(payload, template_code=ROOT)
    blocked = _entries_by_key(plan["blocked_entries"])

    assert any("ARTWORK_ROW_IDENTITY_MISSING" in entry["blockers"] for entry in blocked["finish.print_required"])
    assert any(entry["state"] == "suggested" for entry in blocked["finish.print_required"])
    assert any("ARTWORK_BOOLEAN_EXPLICIT_VALUE_MISSING" in entry["blockers"] for entry in blocked["finish.lamination_required"])


def test_planner_does_not_fall_back_mounting_scope_from_mounting_system() -> None:
    payload = _complete_payload()
    payload["finish_setup"].pop("mounting_scope")

    plan = build_product_truth_promotion_plan(payload, template_code=ROOT)
    blocked = _entries_by_key(plan["blocked_entries"])

    assert blocked["mounting.mounting_scope"][0]["promotion_allowed"] is False
    assert blocked["mounting.mounting_scope"][0]["blockers"] == ["MOUNTING_SCOPE_MISSING"]


def test_planner_does_not_fall_back_support_type_from_support_or_mounting_evidence() -> None:
    payload = _complete_payload()
    payload["finish_setup"].pop("support_type")
    payload["finish_setup"]["support_source"] = "detected_svg"

    plan = build_product_truth_promotion_plan(payload, template_code=ROOT)
    blocked = _entries_by_key(plan["blocked_entries"])

    assert blocked["support.support_type"][0]["promotion_allowed"] is False
    assert blocked["support.support_type"][0]["state"] == "suggested"
    assert blocked["support.support_type"][0]["blockers"] == ["SUPPORT_TYPE_MISSING"]


def test_planner_keeps_hydrated_and_suggested_states_blocked() -> None:
    payload = _complete_payload()
    payload["layer_role_setup"]["confirmation_status"] = "partial"
    payload["finish_setup"]["confirmed"] = False
    payload["finish_setup"]["artwork_finishes"][0]["confirmed"] = False
    payload["finish_setup"]["artwork_finishes"][1]["confirmed"] = False
    payload["finish_setup"]["support_type"] = "steel_frame"

    plan = build_product_truth_promotion_plan(payload, template_code=ROOT)
    blocked = _entries_by_key(plan["blocked_entries"])

    assert plan["eligible_entries"] == []
    assert blocked["svg.selected_layer_refs[]"][0]["state"] in {"partial", "suggested"}
    assert blocked["finish.finish_target"][0]["state"] == "hydrated"
    assert any(entry["state"] == "hydrated" for entry in blocked["finish.print_required"])
    assert blocked["mounting.mounting_scope"][0]["state"] == "hydrated"
    assert blocked["support.support_type"][0]["state"] == "hydrated"


def test_planner_has_no_downstream_write_intent() -> None:
    plan = build_product_truth_promotion_plan(_complete_payload(), template_code=ROOT)

    assert all(value is False for value in plan["downstream_write_intent"].values())
