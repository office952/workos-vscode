from __future__ import annotations

from services.form_system_contract_mapping_adapter_service import (
    build_form_system_contract_readonly_mapping,
)


ROOT = "TPL-VOLUMETRIC-LETTERS_v2"


def _by_key(model: dict) -> dict[str, dict]:
    return {field["field_key"]: field for field in model["fields"]}


def test_field_with_clear_owner_is_mapped_read_only() -> None:
    model = build_form_system_contract_readonly_mapping(ROOT)
    by_key = _by_key(model)

    assert by_key["finish.finish_target"] == {
        "field_key": "finish.finish_target",
        "owner": "finish_artwork",
        "source": "ui_zone_implied_target",
        "state": "blocked",
        "product_truth_path": "components.finish.target",
        "confirmation_required": True,
        "blockers": ["FINISH_TARGET_MISSING"],
        "notes": "Existing UI zones imply target by area, but the canonical finish target is not a first-class confirmed field yet.",
    }


def test_missing_owner_becomes_blocked() -> None:
    model = build_form_system_contract_readonly_mapping(
        ROOT,
        field_specs=[
            {
                "field_key": "support.support_type",
                "owner": None,
                "source": "mounting_bridge_or_operator_input",
                "state": "draft",
                "product_truth_path": "components.support.supportType",
                "confirmation_required": True,
                "blockers": ["SUPPORT_TYPE_MISSING"],
            }
        ],
    )

    field = model["fields"][0]
    assert field["state"] == "blocked"
    assert field["blockers"] == ["SUPPORT_TYPE_MISSING", "FIELD_OWNER_MISSING"]


def test_suggested_field_does_not_become_confirmed() -> None:
    model = build_form_system_contract_readonly_mapping(ROOT)
    field = _by_key(model)["svg.selected_layer_group"]

    assert field["state"] == "suggested"
    assert field["state"] != "confirmed"
    assert field["confirmation_required"] is True


def test_product_truth_path_is_generated_explicitly() -> None:
    model = build_form_system_contract_readonly_mapping(ROOT)
    by_key = _by_key(model)

    assert by_key["finish.print_required"]["product_truth_path"] == "components.finish.printRequired"
    assert by_key["finish.lamination_required"]["product_truth_path"] == "components.finish.laminationRequired"
    assert by_key["mounting.mounting_scope"]["product_truth_path"] == "components.mounting.mountingScope"


def test_selected_layer_remains_evidence_without_confirmation() -> None:
    model = build_form_system_contract_readonly_mapping(ROOT)
    field = _by_key(model)["svg.selected_layer_group"]

    assert field["source"] == "operator_layer_selection_evidence"
    assert field["product_truth_path"] == "svg.selected_layer_refs[]"
    assert field["state"] == "suggested"
    assert field["blockers"] == ["SELECTED_FACE_LAYER_MISSING"]


def test_no_pricing_quote_or_execution_coupling() -> None:
    model = build_form_system_contract_readonly_mapping(ROOT)

    assert model["read_only"] is True
    assert all(value is False for value in model["downstream_write_intent"].values())
    serialized = str(model).lower()
    assert "commercial_total" not in serialized
    assert "quote_write': true" not in serialized
    assert "order_write': true" not in serialized
    assert "execution_runtime_write': true" not in serialized


def test_blocked_root_fails_closed_without_field_output() -> None:
    model = build_form_system_contract_readonly_mapping("TPL-VOLUMETRIC-LOGO_v1")

    assert model["root"]["allowed"] is False
    assert model["fields"] == []