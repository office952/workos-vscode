from __future__ import annotations

from services.intake_v6_modular_form_contract_service import IntakeV6ModularFormContractService


TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


def _contract():
    contract = IntakeV6ModularFormContractService().get_for_template(TEMPLATE)
    assert contract is not None
    return contract


def test_modular_form_contract_exposes_read_only_backbone_section():
    contract = _contract()
    backbone = contract.form_system_backbone

    assert backbone is not None
    assert backbone["read_only"] is True
    assert backbone["root"]["canonical_code"] == TEMPLATE
    assert backbone["root"]["root_type"] == "product_template"
    assert backbone["root"]["quote_mode"] == "product_total"
    assert backbone["linked_template_composition"]["root_template_code"] == TEMPLATE
    assert backbone["linked_template_composition"]["linked_templates"][0]["template_code"] == "TPL-VOLUMETRIC-LOGO_v1"


def test_existing_modular_form_fields_remain_available_after_backbone_alignment():
    contract = _contract()
    field_keys = {field.canonical_key for field in contract.field_bindings}
    module_codes = {module.module_code for module in contract.modules}

    assert "face_finish_type" in field_keys
    assert "return_depth_mm" in field_keys
    assert "mounting_system" in field_keys
    assert "debitare_fata" in module_codes
    assert "modelare_cant" in module_codes
    assert "structura_suport" in module_codes
    assert contract.summary.active_module_count == 7


def test_backbone_bridge_preserves_source_state_and_truth_targets():
    contract = _contract()
    backbone = contract.form_system_backbone or {}
    fields = {field["field_key"]: field for field in backbone["fields"]}

    for key in ("svg.layer_group_role", "return.depth_mm", "lighting.type", "mounting.support_option"):
        assert fields[key]["owning_component"]
        assert fields[key]["source_type"]
        assert fields[key]["state"]
        assert fields[key].get("product_truth_path") or fields[key].get("missing_target_path")

    assert fields["svg.layer_group_role"]["source_type"] == "svg_suggested"
    assert fields["svg.layer_group_role"]["state"] == "suggested"
    assert fields["return.depth_mm"]["state"] == "hydrated"
    assert fields["lighting.type"]["state"] == "fallback"


def test_backbone_bridge_exposes_product_truth_blockers():
    contract = _contract()
    blockers = {blocker["blocker_code"] for blocker in contract.form_system_backbone["readiness"]["blockers"]}

    assert "LAYER_ROLES_INCOMPLETE" in blockers
    assert "FACE_MATERIAL_MISSING" in blockers
    assert "PRODUCT_TRUTH_INCOMPLETE" in blockers


def test_backbone_bridge_has_no_downstream_write_intent_or_totals():
    contract = _contract()
    backbone = contract.form_system_backbone or {}

    assert all(value is False for value in backbone["downstream_write_intent"].values())
    serialized = str(backbone).lower()
    assert "commercial_total" not in serialized
    assert "grand_total" not in serialized
    assert "quote_write': true" not in serialized
    assert "order_write': true" not in serialized
    assert "execution_plan_write': true" not in serialized
    assert "materialized_task" not in serialized


def test_backbone_bridge_root_guards_are_available_without_returning_modular_contracts():
    service = IntakeV6ModularFormContractService()

    legacy_contract = service.get_for_template("TPL-VOLUMETRIC-LETTERS")
    assert legacy_contract is not None
    assert legacy_contract.summary.template_code == TEMPLATE
    assert legacy_contract.form_system_backbone["root"]["canonical_alias_resolution"] is True

    logo_backbone = service.get_backbone_section_for_template("TPL-VOLUMETRIC-LOGO_v1")
    assert logo_backbone["root"]["blocker_code"] == "LOGO_NOT_OFFERABLE"
    assert service.get_for_template("TPL-VOLUMETRIC-LOGO_v1") is None

    component_backbone = service.get_backbone_section_for_template("TPL-VOLUMETRIC-FACE_v1")
    assert component_backbone["root"]["blocker_code"] == "COMPONENT_ROOT_BLOCKED"
    assert service.get_for_template("TPL-VOLUMETRIC-FACE_v1") is None