from __future__ import annotations

from services.form_system_contract_backbone_service import build_form_system_contract_map


ROOT = "TPL-VOLUMETRIC-LETTERS_v2"
LEGACY_ROOT = "TPL-VOLUMETRIC-LETTERS"


def _fields_by_key(contract: dict):
    return {field["field_key"]: field for field in contract["fields"]}


def test_legacy_letters_alias_canonicalizes_to_v2_root():
    contract = build_form_system_contract_map(LEGACY_ROOT)

    assert contract["root"]["requested_code"] == LEGACY_ROOT
    assert contract["root"]["canonical_code"] == ROOT
    assert contract["root"]["code"] == ROOT
    assert contract["root"]["canonical_alias_resolution"] is True
    assert contract["root"]["allowed"] is True


def test_letters_v2_is_allowed_product_template_product_total_root():
    contract = build_form_system_contract_map(ROOT)

    assert contract["root"]["canonical_code"] == ROOT
    assert contract["root"]["root_type"] == "product_template"
    assert contract["root"]["quote_mode"] == "product_total"
    assert contract["root"]["offerability_status"] == "allowed_owner_valid_root"
    assert contract["root"]["blocked"] is False


def test_letters_v2_exposes_linked_logo_segment_composition_without_root_activation():
    contract = build_form_system_contract_map(ROOT)
    composition = contract["linked_template_composition"]
    linked_logo = composition["linked_templates"][0]

    assert composition["root_template_code"] == ROOT
    assert composition["root_role"] == "root_product"
    assert composition["composition_mode"] == "root_with_linked_segments"
    assert linked_logo["template_code"] == "TPL-VOLUMETRIC-LOGO_v1"
    assert linked_logo["composition_role"] == "linked_logo_segment"
    assert linked_logo["binding_status"] == "suggested"
    assert linked_logo["activation_state"] == "child_only_not_root_offerable"
    assert linked_logo["quote_policy"] == "no_separate_quote"
    assert linked_logo["root_offerability_policy"] == "blocked_as_root_in_this_flow"
    assert linked_logo["component_quote_policy"] == "blocked"
    assert linked_logo["segment_discovery"]["status"] == "runtime_payload_required"
    assert linked_logo["segments"] == []
    assert composition["no_duplicate_task_policy"]["task_graph_implemented"] is False
    assert all(value is False for value in contract["downstream_write_intent"].values())


def test_logo_root_is_blocked_and_legacy_logo_components_do_not_generate_fields():
    contract = build_form_system_contract_map("TPL-VOLUMETRIC-LOGO_v1")

    assert contract["root"]["allowed"] is False
    assert contract["root"]["blocker_code"] == "LOGO_NOT_OFFERABLE"
    assert contract["fields"] == []
    assert "linked_template_composition" not in contract

    legacy_component = build_form_system_contract_map("TPL-VOLUMETRIC-LOGO-FACE_v1")
    assert legacy_component["root"]["allowed"] is False
    assert legacy_component["root"]["blocker_code"] == "LEGACY_LOGO_COMPONENT_BLOCKED"
    assert legacy_component["fields"] == []


def test_component_template_root_and_component_only_quote_are_blocked():
    component_root = build_form_system_contract_map(
        "TPL-VOLUMETRIC-FACE_v1",
        root_type="component_template",
        quote_mode="component_only",
    )
    assert component_root["root"]["allowed"] is False
    assert component_root["root"]["blocker_code"] == "ROOT_TYPE_BLOCKED"

    component_quote = build_form_system_contract_map(ROOT, quote_mode="component_only")
    assert component_quote["root"]["allowed"] is False
    assert component_quote["root"]["blocker_code"] == "QUOTE_MODE_BLOCKED"


def test_unknown_template_fails_closed():
    contract = build_form_system_contract_map("TPL-UNKNOWN")

    assert contract["root"]["allowed"] is False
    assert contract["root"]["blocker_code"] == "UNKNOWN_TEMPLATE_BLOCKED"
    assert contract["components"] == []
    assert contract["fields"] == []


def test_initial_component_coverage_is_reported_without_inventing_logo_or_component_roots():
    contract = build_form_system_contract_map(ROOT)
    components = {component["component_key"]: component for component in contract["components"]}

    for key in (
        "face",
        "back",
        "return_cant",
        "finish_artwork",
        "lighting_led",
        "mounting_support",
        "electrical",
        "production_operations_reference",
    ):
        assert key in components
        assert components[key]["coverage"] in {"covered", "partial", "missing", "not_found", "future"}

    assert all("LOGO" not in str(component.get("component_template_code", "")).upper() for component in components.values())


def test_each_initial_field_has_owner_source_state_and_truth_target_or_explicit_missing_target():
    contract = build_form_system_contract_map(ROOT)

    assert contract["fields"]
    for field in contract["fields"]:
        assert field["field_key"]
        assert field["owning_component"]
        assert field["source_type"]
        assert field["state"]
        assert field.get("product_truth_path") or field.get("missing_target_path")


def test_required_field_set_includes_requested_backbone_fields():
    fields = _fields_by_key(build_form_system_contract_map(ROOT))

    for key in (
        "svg.layer_group_role",
        "svg.selected_layer_group",
        "face.material",
        "face.finish_artwork_target",
        "finish.print_required",
        "finish.lamination_required",
        "return.material",
        "return.depth_mm",
        "lighting.type",
        "lighting.led_profile",
        "mounting.support_option",
        "mounting.mounting_scope",
        "support.support_type",
        "readiness.product_truth_blockers",
    ):
        assert key in fields


def test_svg_suggested_is_not_treated_as_confirmed():
    fields = _fields_by_key(build_form_system_contract_map(ROOT))
    field = fields["svg.layer_group_role"]

    assert field["source_type"] == "svg_suggested"
    assert field["state"] == "suggested"
    assert field["state"] != "confirmed"
    assert field["field_key"] in build_form_system_contract_map(ROOT)["readiness"]["suggestions_allowed"]


def test_fallback_and_hydrated_values_do_not_unlock_quote_automatically():
    contract = build_form_system_contract_map(ROOT)
    fields = _fields_by_key(contract)

    assert fields["return.depth_mm"]["state"] == "hydrated"
    assert fields["lighting.type"]["state"] == "fallback"
    assert fields["mounting.support_option"]["state"] == "hydrated"

    not_confirmed = set(contract["readiness"]["fallback_or_hydrated_not_confirmed"])
    assert {"return.depth_mm", "lighting.type", "mounting.support_option"} <= not_confirmed
    assert contract["readiness"]["status"] == "blocked"


def test_missing_required_truth_produces_readiness_blockers():
    contract = build_form_system_contract_map(ROOT)
    blockers = {blocker["blocker_code"] for blocker in contract["readiness"]["blockers"]}

    assert "FACE_MATERIAL_MISSING" in blockers
    assert "SELECTED_FACE_LAYER_MISSING" in blockers
    assert "PRODUCT_TRUTH_INCOMPLETE" in blockers
    assert all("Pricing" not in blocker["message"] for blocker in contract["readiness"]["blockers"])


def test_runtime_selected_layer_refs_confirm_selected_layer_field_when_persisted():
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

    contract = build_form_system_contract_map(ROOT, payload_raw=payload)
    field = _fields_by_key(contract)["svg.selected_layer_group"]

    assert field["source_type"] == "payload_persisted"
    assert field["state"] == "confirmed"
    assert field["blocker_code"] is None
    blocker_codes = {blocker["blocker_code"] for blocker in contract["readiness"]["blockers"]}
    assert "SELECTED_LAYER_REFS_MISSING" not in blocker_codes
    assert "SELECTED_LAYER_REFS_UNCONFIRMED" not in blocker_codes


def test_runtime_missing_selected_layer_refs_stays_blocked():
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
        }
    }

    contract = build_form_system_contract_map(ROOT, payload_raw=payload)
    field = _fields_by_key(contract)["svg.selected_layer_group"]

    assert field["state"] == "missing"
    assert field["blocker_code"] == "SELECTED_LAYER_REFS_MISSING"


def test_runtime_selected_layer_refs_without_stable_ids_are_ambiguous():
    payload = {
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "face-1",
                    "layer_name": "face 1",
                    "auto_role": "face",
                    "auto_confidence": "high",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                }
            ],
            "warnings": [],
        }
    }

    contract = build_form_system_contract_map(ROOT, payload_raw=payload)
    field = _fields_by_key(contract)["svg.selected_layer_group"]

    assert field["state"] == "blocked"
    assert field["blocker_code"] == "SELECTED_LAYER_REFS_AMBIGUOUS"


def test_runtime_finish_target_confirms_backbone_field_when_persisted_and_confirmed():
    payload = {
        "finish_setup": {
            "finish_target": "face",
            "confirmed": True,
        }
    }

    contract = build_form_system_contract_map(ROOT, payload_raw=payload)
    field = _fields_by_key(contract)["face.finish_artwork_target"]

    assert field["source_type"] == "payload_persisted"
    assert field["state"] == "confirmed"
    assert field["blocker_code"] is None


def test_runtime_finish_target_unconfirmed_does_not_unlock_backbone_field():
    payload = {
        "finish_setup": {
            "finish_target": "face",
            "confirmed": False,
        }
    }

    contract = build_form_system_contract_map(ROOT, payload_raw=payload)
    field = _fields_by_key(contract)["face.finish_artwork_target"]

    assert field["source_type"] == "operator_confirmed"
    assert field["state"] == "missing"
    assert field["blocker_code"] == "FACE_FINISH_TARGET_MISSING"


def test_runtime_artwork_print_and_lamination_confirm_backbone_fields_row_level_only():
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

    contract = build_form_system_contract_map(ROOT, payload_raw=payload)
    fields = _fields_by_key(contract)

    assert fields["finish.print_required"]["source_type"] == "payload_persisted"
    assert fields["finish.print_required"]["state"] == "confirmed"
    assert fields["finish.print_required"]["product_truth_path"] == "components.artwork.items[].printRequired"
    assert fields["finish.lamination_required"]["source_type"] == "payload_persisted"
    assert fields["finish.lamination_required"]["state"] == "confirmed"
    assert fields["finish.lamination_required"]["product_truth_path"] == "components.artwork.items[].laminationRequired"


def test_runtime_artwork_print_missing_value_keeps_backbone_blocked():
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

    contract = build_form_system_contract_map(ROOT, payload_raw=payload)
    field = _fields_by_key(contract)["finish.print_required"]

    assert field["source_type"] == "payload_artwork_rows"
    assert field["state"] == "blocked"
    assert field["blocker_code"] == "PRINT_REQUIRED_UNKNOWN"


def test_runtime_artwork_lamination_unconfirmed_does_not_unlock_backbone_field():
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

    contract = build_form_system_contract_map(ROOT, payload_raw=payload)
    field = _fields_by_key(contract)["finish.lamination_required"]

    assert field["source_type"] == "payload_artwork_rows"
    assert field["state"] == "blocked"
    assert field["blocker_code"] == "LAMINATION_REQUIRED_UNKNOWN"


def test_runtime_mounting_scope_confirms_backbone_field_when_persisted_and_confirmed():
    payload = {
        "finish_setup": {
            "mounting_scope": "mounting_included",
            "mounting_system": "steel_bars",
            "support_type": "steel_frame",
            "confirmed": True,
        }
    }

    contract = build_form_system_contract_map(ROOT, payload_raw=payload)
    field = _fields_by_key(contract)["mounting.mounting_scope"]

    assert field["source_type"] == "payload_persisted"
    assert field["state"] == "confirmed"
    assert field["blocker_code"] is None


def test_runtime_mounting_scope_missing_stays_blocked_without_mounting_system_or_support_type_fallback():
    payload = {
        "finish_setup": {
            "mounting_system": "steel_bars",
            "support_type": "steel_frame",
            "confirmed": True,
        }
    }

    contract = build_form_system_contract_map(ROOT, payload_raw=payload)
    field = _fields_by_key(contract)["mounting.mounting_scope"]

    assert field["source_type"] == "operator_confirmed"
    assert field["state"] == "missing"
    assert field["blocker_code"] == "MOUNTING_SCOPE_MISSING"


def test_runtime_mounting_scope_unconfirmed_does_not_unlock_backbone_field():
    payload = {
        "finish_setup": {
            "mounting_scope": "mounting_included",
            "confirmed": False,
        }
    }

    contract = build_form_system_contract_map(ROOT, payload_raw=payload)
    field = _fields_by_key(contract)["mounting.mounting_scope"]

    assert field["source_type"] == "operator_confirmed"
    assert field["state"] == "blocked"
    assert field["blocker_code"] == "MOUNTING_SCOPE_MISSING"


def test_runtime_support_type_confirms_backbone_field_when_persisted_and_confirmed():
    payload = {
        "finish_setup": {
            "support_type": "steel_frame",
            "support_required": "yes",
            "mounting_system": "steel_bars",
            "mounting_scope": "mounting_included",
            "confirmed": True,
        }
    }

    contract = build_form_system_contract_map(ROOT, payload_raw=payload)
    field = _fields_by_key(contract)["support.support_type"]

    assert field["source_type"] == "payload_persisted"
    assert field["state"] == "confirmed"
    assert field["blocker_code"] is None


def test_runtime_support_type_missing_stays_blocked_without_support_required_mounting_or_scope_fallbacks():
    payload = {
        "finish_setup": {
            "support_required": "yes",
            "mounting_system": "steel_bars",
            "mounting_scope": "mounting_included",
            "support_source": "detected_svg",
            "confirmed": True,
        }
    }

    contract = build_form_system_contract_map(ROOT, payload_raw=payload)
    field = _fields_by_key(contract)["support.support_type"]

    assert field["source_type"] == "operator_confirmed"
    assert field["state"] == "missing"
    assert field["blocker_code"] == "SUPPORT_TYPE_MISSING"


def test_runtime_support_type_unconfirmed_does_not_unlock_backbone_field():
    payload = {
        "finish_setup": {
            "support_type": "steel_frame",
            "support_required": "yes",
            "confirmed": False,
        }
    }

    contract = build_form_system_contract_map(ROOT, payload_raw=payload)
    field = _fields_by_key(contract)["support.support_type"]

    assert field["source_type"] == "operator_confirmed"
    assert field["state"] == "blocked"
    assert field["blocker_code"] == "SUPPORT_TYPE_MISSING"


def test_no_downstream_write_or_pricing_quote_order_execution_leakage():
    contract = build_form_system_contract_map(ROOT)

    assert contract["read_only"] is True
    assert all(value is False for value in contract["downstream_write_intent"].values())
    serialized = str(contract).lower()
    assert "commercial_total" not in serialized
    assert "grand_total" not in serialized
    assert "quote_write': true" not in serialized
    assert "order_write': true" not in serialized
    assert "execution_plan_write': true" not in serialized
    assert "materialized_task" not in serialized


def test_product_definition_boundary_is_consumer_only():
    contract = build_form_system_contract_map(ROOT)

    assert any("product_definition" in field["required_for"] for field in contract["fields"])
    assert contract["downstream_write_intent"]["product_definition_write"] is False
    assert contract["downstream_write_intent"]["product_aggregate_write"] is False
    assert contract["downstream_write_intent"]["task_graph_write"] is False