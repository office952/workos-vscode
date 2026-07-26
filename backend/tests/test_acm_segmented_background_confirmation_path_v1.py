"""Operator confirmation path for segmented ACM/ACP backgrounds."""

from __future__ import annotations

import pytest

from data.product_system.acm_segmented_background_v1 import (
    CONSTRUCTION_ACRYLIC_INSERT,
    CONSTRUCTION_APPLIED_VOLUMETRIC,
    CONSTRUCTION_CUTOUT,
    MSG_ASSEMBLY_CONFIRMED,
    MSG_INSERT_CROSSING_BLOCKER,
    MSG_PROPOSAL_REJECTED,
    STATUS_CONFIRMED,
    STATUS_PROPOSED,
    STATUS_REJECTED,
    operator_message,
)
from services.acm_segmented_background_service import (
    coalesce_segmented_background_for_finish,
    confirm_segmented_background,
    persist_segmented_background_on_finish,
    project_segmented_background_for_aggregate,
    project_segmented_background_for_product_definition,
    propose_segmented_assembly,
    reject_segmented_background,
)
from services.product_definition_builder_service import _build_canonical_values


def _proposal(**extra):
    base = propose_segmented_assembly(
        nearby_supports=[
            {
                "panel_id": "panel_1",
                "contour_element_id": "a",
                "width_mm": 1000,
                "height_mm": 1000,
            },
            {
                "panel_id": "panel_2",
                "contour_element_id": "b",
                "width_mm": 1000,
                "height_mm": 1000,
            },
        ]
    )
    base.update(extra)
    return base


def test_propose_unresolved_zero_pd_aggregate():
    proposal = _proposal()
    assert proposal["status"] == STATUS_PROPOSED
    assert project_segmented_background_for_product_definition(proposal) is None
    assert project_segmented_background_for_aggregate(proposal) is None
    values = _build_canonical_values([], {"finish_setup": {"segmented_background": proposal}})
    assert "segmented_background" not in values
    assert values["segmented_background_proposal"]["downstream_effects"] is False


def test_reject_zero_confirmed_truth():
    rejected = reject_segmented_background(_proposal())
    assert rejected["status"] == STATUS_REJECTED
    assert rejected["operator_confirmed"] is False
    assert rejected["confirmation"]["message"] == operator_message(MSG_PROPOSAL_REJECTED)
    assert project_segmented_background_for_product_definition(rejected) is None
    finish = persist_segmented_background_on_finish({"segmented_background": rejected})
    assert finish["segmented_background"]["status"] == STATUS_REJECTED
    values = _build_canonical_values([], {"finish_setup": finish})
    assert "segmented_background" not in values


def test_sparse_finish_patch_does_not_wipe_proposed_segmented():
    """Binding-sync finish PUTs omit segmented_background — keep live PROPOSED."""
    proposal = _proposal()
    sparse = {"svg_component_bindings": [], "mounting_solution": {"kind": "x"}, "segmented_background": None}
    merged = coalesce_segmented_background_for_finish(
        sparse,
        {"segmented_background": proposal},
    )
    assert merged["segmented_background"]["status"] == STATUS_PROPOSED
    assert merged["segmented_background"]["assembly_id"] == proposal["assembly_id"]


def test_confirm_persists_and_projects_pd_aggregate():
    confirmed = confirm_segmented_background(_proposal())
    assert confirmed["status"] == STATUS_CONFIRMED
    assert confirmed["operator_confirmed"] is True
    assert confirmed["confirmation"]["message"] == operator_message(MSG_ASSEMBLY_CONFIRMED)
    finish = persist_segmented_background_on_finish({"segmented_background": confirmed})
    values = _build_canonical_values([], {"finish_setup": finish})
    pd = values["segmented_background"]
    assert pd["assembly_id"]
    assert [p["panel_id"] for p in pd["panels"]] == ["panel_1", "panel_2"]
    agg = values["segmented_background_aggregate_projection"]
    assert agg["future_task_intent_authority"] == "INFORMATIONAL_ONLY"
    assert agg["task_rules"] == []
    assert "task_contract.task_rules" in agg["task_contract_authority"]


def test_confirm_blocked_on_cutout_crossing():
    proposal = _proposal(
        element_bindings=[
            {
                "binding_id": "eb_cut",
                "construction_type": CONSTRUCTION_CUTOUT,
                "primary_panel_id": "panel_1",
                "secondary_panel_id": "panel_2",
                "crosses_joint": True,
            }
        ]
    )
    with pytest.raises(ValueError) as exc:
        confirm_segmented_background(proposal)
    detail = exc.value.args[0]
    assert detail["error"] == "segmented_background_confirmation_blocked"
    assert any(b["code"] for b in detail["blockers"])


def test_confirm_blocked_on_insert_crossing():
    proposal = _proposal(
        element_bindings=[
            {
                "binding_id": "eb_ins",
                "construction_type": CONSTRUCTION_ACRYLIC_INSERT,
                "primary_panel_id": "panel_1",
                "secondary_panel_id": "panel_2",
                "crosses_joint": True,
            }
        ]
    )
    with pytest.raises(ValueError):
        confirm_segmented_background(proposal)
    # finish persist also blocks CONFIRMED with insert crossing
    proposal["status"] = STATUS_CONFIRMED
    proposal["operator_confirmed"] = True
    with pytest.raises(ValueError) as exc:
        persist_segmented_background_on_finish({"segmented_background": proposal})
    assert any(
        b["code"] == MSG_INSERT_CROSSING_BLOCKER for b in exc.value.args[0]["blockers"]
    )


def test_confirm_allows_applied_crossing_two_stage():
    proposal = _proposal(
        element_bindings=[
            {
                "binding_id": "eb_app",
                "element_ref": "letter_X",
                "construction_type": CONSTRUCTION_APPLIED_VOLUMETRIC,
                "primary_panel_id": "panel_1",
                "secondary_panel_id": "panel_2",
                "crosses_joint": True,
                "joint_id": "joint_panel_1_panel_2",
            }
        ]
    )
    confirmed = confirm_segmented_background(proposal)
    finish = persist_segmented_background_on_finish({"segmented_background": confirmed})
    values = _build_canonical_values([], {"finish_setup": finish})
    binding = values["segmented_background"]["element_bindings"][0]
    assert binding["mount_strategy"] == "TWO_STAGE_JOINT_CROSSING"
    assert binding["does_not_absorb_letter_ownership"] is True
    agg = values["segmented_background_aggregate_projection"]
    assert len(agg["allowed_applied_crossings"]) == 1


def test_reject_then_confirm_corrected_proposal():
    rejected = reject_segmented_background(_proposal())
    corrected = _proposal(assembly_id="asm_corrected")
    confirmed = confirm_segmented_background(corrected)
    finish = persist_segmented_background_on_finish(
        {"segmented_background": rejected}
    )
    assert finish["segmented_background"]["status"] == STATUS_REJECTED
    finish2 = persist_segmented_background_on_finish(
        {"segmented_background": confirmed}
    )
    values = _build_canonical_values([], {"finish_setup": finish2})
    assert values["segmented_background"]["assembly_id"] == "asm_corrected"


def test_reload_preserves_ids_order_joints():
    confirmed = confirm_segmented_background(_proposal(assembly_id="asm_reload"))
    finish = persist_segmented_background_on_finish({"segmented_background": confirmed})
    # Simulate reload: re-normalize persisted doc
    finish2 = persist_segmented_background_on_finish(finish)
    a = finish["segmented_background"]
    b = finish2["segmented_background"]
    assert a["assembly_id"] == b["assembly_id"] == "asm_reload"
    assert [p["panel_id"] for p in a["panels"]] == [p["panel_id"] for p in b["panels"]]
    assert [j["joint_id"] for j in a["joints"]] == [j["joint_id"] for j in b["joints"]]
