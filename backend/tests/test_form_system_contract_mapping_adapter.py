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

    assert by_key["finish.print_required"]["product_truth_path"] == "components.artwork.items[].printRequired"
    assert by_key["finish.lamination_required"]["product_truth_path"] == "components.artwork.items[].laminationRequired"
    assert by_key["mounting.mounting_scope"]["product_truth_path"] == "components.mounting.mountingScope"
    assert by_key["support.support_type"]["product_truth_path"] == "components.support.supportType"


def test_selected_layer_remains_evidence_without_confirmation() -> None:
    model = build_form_system_contract_readonly_mapping(ROOT)
    field = _by_key(model)["svg.selected_layer_group"]

    assert field["source"] == "operator_layer_selection_evidence"
    assert field["product_truth_path"] == "svg.selected_layer_refs[]"
    assert field["state"] == "suggested"
    assert field["blockers"] == ["SELECTED_FACE_LAYER_MISSING"]


def test_selected_layer_runtime_overlay_reads_persisted_selected_layer_refs() -> None:
    payload = {
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
    }

    model = build_form_system_contract_readonly_mapping(ROOT, payload_raw=payload)
    field = _by_key(model)["svg.selected_layer_group"]

    assert field["source"] == "payload_persisted"
    assert field["state"] == "confirmed"
    assert field["blockers"] == []


def test_selected_layer_runtime_overlay_missing_refs_remains_blocked() -> None:
    payload = {
        "layer_role_setup": {
            "confirmation_status": "partial",
            "layers": [
                {
                    "layer_key": "face-1",
                    "layer_id": "face-1",
                    "layer_name": "face 1",
                    "auto_role": "face",
                    "auto_confidence": "high",
                    "confirmed_role": None,
                    "confirmation_state": "pending",
                }
            ],
            "warnings": [],
        }
    }

    model = build_form_system_contract_readonly_mapping(ROOT, payload_raw=payload)
    field = _by_key(model)["svg.selected_layer_group"]

    assert field["state"] == "blocked"
    assert field["blockers"] == ["SELECTED_LAYER_REFS_UNCONFIRMED"]


def test_finish_target_runtime_overlay_reads_persisted_finish_target() -> None:
    payload = {
        "finish_setup": {
            "finish_target": "face",
            "confirmed": True,
        }
    }

    model = build_form_system_contract_readonly_mapping(ROOT, payload_raw=payload)
    field = _by_key(model)["finish.finish_target"]

    assert field["source"] == "payload_persisted"
    assert field["state"] == "confirmed"
    assert field["blockers"] == []
    assert field["product_truth_path"] == "components.finish.target"


def test_finish_target_runtime_overlay_unconfirmed_does_not_become_confirmed() -> None:
    payload = {
        "finish_setup": {
            "finish_target": "face",
            "confirmed": False,
        }
    }

    model = build_form_system_contract_readonly_mapping(ROOT, payload_raw=payload)
    field = _by_key(model)["finish.finish_target"]

    assert field["state"] == "blocked"
    assert field["source"] == "ui_zone_implied_target"
    assert field["blockers"] == ["FINISH_TARGET_MISSING"]


def test_print_and_lamination_runtime_overlay_reads_persisted_row_level_source() -> None:
    payload = {
        "finish_setup": {
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
        }
    }

    model = build_form_system_contract_readonly_mapping(ROOT, payload_raw=payload)
    fields = _by_key(model)

    assert fields["finish.print_required"]["source"] == "payload_persisted"
    assert fields["finish.print_required"]["state"] == "confirmed"
    assert fields["finish.print_required"]["blockers"] == []
    assert fields["finish.lamination_required"]["source"] == "payload_persisted"
    assert fields["finish.lamination_required"]["state"] == "confirmed"
    assert fields["finish.lamination_required"]["blockers"] == []


def test_print_and_lamination_runtime_overlay_missing_values_remain_blocked() -> None:
    payload = {
        "finish_setup": {
            "confirmed": True,
            "artwork_finishes": [
                {
                    "layer_key": "logo-left",
                    "lamination_required": True,
                }
            ],
        }
    }

    model = build_form_system_contract_readonly_mapping(ROOT, payload_raw=payload)
    fields = _by_key(model)

    assert fields["finish.print_required"]["source"] == "payload_artwork_rows"
    assert fields["finish.print_required"]["state"] == "blocked"
    assert fields["finish.print_required"]["blockers"] == ["PRINT_REQUIRED_UNKNOWN"]
    assert fields["finish.lamination_required"]["source"] == "payload_persisted"
    assert fields["finish.lamination_required"]["state"] == "confirmed"
    assert fields["finish.lamination_required"]["blockers"] == []


def test_print_and_lamination_runtime_overlay_unconfirmed_rows_do_not_become_confirmed() -> None:
    payload = {
        "finish_setup": {
            "confirmed": False,
            "artwork_finishes": [
                {
                    "layer_key": "logo-left",
                    "print_required": True,
                    "lamination_required": True,
                    "confirmed": False,
                }
            ],
        }
    }

    model = build_form_system_contract_readonly_mapping(ROOT, payload_raw=payload)
    fields = _by_key(model)

    assert fields["finish.print_required"]["state"] == "blocked"
    assert fields["finish.print_required"]["blockers"] == ["PRINT_REQUIRED_UNKNOWN"]
    assert fields["finish.lamination_required"]["state"] == "blocked"
    assert fields["finish.lamination_required"]["blockers"] == ["LAMINATION_REQUIRED_UNKNOWN"]


def test_mounting_scope_runtime_overlay_reads_persisted_mounting_scope() -> None:
    payload = {
        "finish_setup": {
            "mounting_scope": "mounting_included",
            "mounting_system": "steel_bars",
            "support_type": "steel_frame",
            "confirmed": True,
        }
    }

    model = build_form_system_contract_readonly_mapping(ROOT, payload_raw=payload)
    field = _by_key(model)["mounting.mounting_scope"]

    assert field["source"] == "payload_persisted"
    assert field["state"] == "confirmed"
    assert field["blockers"] == []


def test_mounting_scope_runtime_overlay_missing_value_remains_blocked_without_mounting_system_or_support_fallback() -> None:
    payload = {
        "finish_setup": {
            "mounting_system": "steel_bars",
            "support_type": "steel_frame",
            "confirmed": True,
        }
    }

    model = build_form_system_contract_readonly_mapping(ROOT, payload_raw=payload)
    field = _by_key(model)["mounting.mounting_scope"]

    assert field["source"] == "operator_confirmed"
    assert field["state"] == "missing"
    assert field["blockers"] == ["MOUNTING_SCOPE_MISSING"]


def test_mounting_scope_runtime_overlay_unconfirmed_value_does_not_become_confirmed() -> None:
    payload = {
        "finish_setup": {
            "mounting_scope": "mounting_included",
            "confirmed": False,
        }
    }

    model = build_form_system_contract_readonly_mapping(ROOT, payload_raw=payload)
    field = _by_key(model)["mounting.mounting_scope"]

    assert field["source"] == "operator_confirmed"
    assert field["state"] == "blocked"
    assert field["blockers"] == ["MOUNTING_SCOPE_MISSING"]


def test_support_type_runtime_overlay_reads_persisted_support_type() -> None:
    payload = {
        "finish_setup": {
            "support_type": "steel_frame",
            "support_required": "yes",
            "mounting_system": "steel_bars",
            "mounting_scope": "mounting_included",
            "confirmed": True,
        }
    }

    model = build_form_system_contract_readonly_mapping(ROOT, payload_raw=payload)
    field = _by_key(model)["support.support_type"]

    assert field["source"] == "payload_persisted"
    assert field["state"] == "confirmed"
    assert field["blockers"] == []


def test_support_type_runtime_overlay_missing_value_remains_blocked_without_fallbacks() -> None:
    payload = {
        "finish_setup": {
            "support_required": "yes",
            "mounting_system": "steel_bars",
            "mounting_scope": "mounting_included",
            "support_source": "detected_svg",
            "confirmed": True,
        }
    }

    model = build_form_system_contract_readonly_mapping(ROOT, payload_raw=payload)
    field = _by_key(model)["support.support_type"]

    assert field["source"] == "operator_confirmed"
    assert field["state"] == "missing"
    assert field["blockers"] == ["SUPPORT_TYPE_MISSING"]


def test_support_type_runtime_overlay_unconfirmed_value_does_not_become_confirmed() -> None:
    payload = {
        "finish_setup": {
            "support_type": "steel_frame",
            "support_required": "yes",
            "confirmed": False,
        }
    }

    model = build_form_system_contract_readonly_mapping(ROOT, payload_raw=payload)
    field = _by_key(model)["support.support_type"]

    assert field["source"] == "operator_confirmed"
    assert field["state"] == "blocked"
    assert field["blockers"] == ["SUPPORT_TYPE_MISSING"]


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