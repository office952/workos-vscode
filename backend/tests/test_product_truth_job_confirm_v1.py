"""ConfirmJobProductTruth — revision, pin, idempotency, stale, 409."""

from __future__ import annotations

import copy

import pytest

from types import SimpleNamespace

from services.product_truth_job_confirm_service import (
    apply_pinned_bags_onto_payload,
    commercial_freeze_allowed,
    confirm_job_product_truth,
    draft_hash_for_payload,
    get_job_revision_metadata,
    mark_job_revision_stale_if_confirmed,
)
from services.acm_panel_domain_service import project_acm_mirrors_from_canonical
from services.order_snapshot_v2_convert_service import _enrich_order_provenance_with_product_truth


def _payload_with_bags() -> dict:
    return {
        "template_code": "TPL-VOLUMETRIC-LETTERS_v2",
        "finish_setup": {
            "letter_group_instances": [
                {
                    "schema": "volumetric_letter_group_instance_v1",
                    "instance_id": "11111111-1111-1111-1111-111111111111",
                    "group_key": "pseudo:maria",
                    "confirmed": True,
                }
            ],
            "component_placements": [
                {
                    "schema": "component_placement_v1",
                    "placement_id": "pl1",
                    "source_instance_id": "11111111-1111-1111-1111-111111111111",
                    "target_kind": "acm_panel",
                    "target_instance_id": "acm-1",
                }
            ],
            "acm_panel_instance": {
                "schema": "acm_panel_component_instance_v1",
                "component_instance_id": "acm-1",
                "component_template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                "association_status": "confirmed",
            },
        },
    }


def test_first_confirm_pins_bags_and_sets_revision_1():
    payload = _payload_with_bags()
    response, out = confirm_job_product_truth(
        workspace_id="ws-1",
        workspace_code="IV6-TEST",
        payload_raw=payload,
        expected_revision=0,
        expected_draft_hash=None,
        expected_content_hash=None,
        root_template_code="TPL-VOLUMETRIC-LETTERS_v2",
        root_template_version=None,
        actor_id="user-1",
    )
    assert response["write_performed"] is True
    assert response["idempotent_noop"] is False
    assert response["metadata"]["revision"] == 1
    assert response["metadata"]["confirmation_state"] == "confirmed"
    assert response["metadata"]["content_hash"].startswith("sha256:")
    snap = out["product_truth"]["confirmed_snapshot_v1"]
    assert snap["pinned_typed_bags"]["acm_panel_instance"]["component_instance_id"] == "acm-1"
    assert len(snap["pinned_typed_bags"]["letter_group_instances"]) == 1
    assert commercial_freeze_allowed(out) is True


def test_idempotent_reconfirm_same_hash():
    payload = _payload_with_bags()
    confirm_job_product_truth(
        workspace_id="ws-1",
        workspace_code="IV6-TEST",
        payload_raw=payload,
        expected_revision=0,
        expected_draft_hash=None,
        expected_content_hash=None,
        root_template_code="TPL-VOLUMETRIC-LETTERS_v2",
        root_template_version=None,
        actor_id="user-1",
    )
    response, out = confirm_job_product_truth(
        workspace_id="ws-1",
        workspace_code="IV6-TEST",
        payload_raw=payload,
        expected_revision=1,
        expected_draft_hash=None,
        expected_content_hash=None,
        root_template_code="TPL-VOLUMETRIC-LETTERS_v2",
        root_template_version=None,
        actor_id="user-1",
    )
    assert response["idempotent_noop"] is True
    assert response["write_performed"] is False
    assert get_job_revision_metadata(out)["revision"] == 1
    assert len(out["product_truth"]["confirmed_snapshot_v1"]["audit_trail"]) == 1


def test_revision_mismatch_409():
    payload = _payload_with_bags()
    confirm_job_product_truth(
        workspace_id="ws-1",
        workspace_code="IV6-TEST",
        payload_raw=payload,
        expected_revision=0,
        expected_draft_hash=None,
        expected_content_hash=None,
        root_template_code="TPL-VOLUMETRIC-LETTERS_v2",
        root_template_version=None,
        actor_id="user-1",
    )
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        confirm_job_product_truth(
            workspace_id="ws-1",
            workspace_code="IV6-TEST",
            payload_raw=payload,
            expected_revision=0,
            expected_draft_hash=None,
            expected_content_hash=None,
            root_template_code="TPL-VOLUMETRIC-LETTERS_v2",
            root_template_version=None,
            actor_id="user-1",
        )
    assert exc.value.status_code == 409
    assert exc.value.detail["error"] == "revision_mismatch"


def test_draft_hash_mismatch_409():
    payload = _payload_with_bags()
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        confirm_job_product_truth(
            workspace_id="ws-1",
            workspace_code="IV6-TEST",
            payload_raw=payload,
            expected_revision=0,
            expected_draft_hash="sha256:deadbeef",
            expected_content_hash=None,
            root_template_code="TPL-VOLUMETRIC-LETTERS_v2",
            root_template_version=None,
            actor_id="user-1",
        )
    assert exc.value.status_code == 409
    assert exc.value.detail["error"] == "draft_hash_mismatch"


def test_stale_after_edit_blocks_freeze():
    payload = _payload_with_bags()
    confirm_job_product_truth(
        workspace_id="ws-1",
        workspace_code="IV6-TEST",
        payload_raw=payload,
        expected_revision=0,
        expected_draft_hash=None,
        expected_content_hash=None,
        root_template_code="TPL-VOLUMETRIC-LETTERS_v2",
        root_template_version=None,
        actor_id="user-1",
    )
    assert commercial_freeze_allowed(payload) is True
    payload["finish_setup"]["letter_group_instances"][0]["confirmed"] = False
    assert mark_job_revision_stale_if_confirmed(payload) is True
    assert get_job_revision_metadata(payload)["confirmation_state"] == "stale_after_edit"
    assert commercial_freeze_allowed(payload) is False
    # pin retained
    assert payload["product_truth"]["confirmed_snapshot_v1"]["pinned_typed_bags"]["acm_panel_instance"]


def test_correction_increments_revision():
    payload = _payload_with_bags()
    confirm_job_product_truth(
        workspace_id="ws-1",
        workspace_code="IV6-TEST",
        payload_raw=payload,
        expected_revision=0,
        expected_draft_hash=None,
        expected_content_hash=None,
        root_template_code="TPL-VOLUMETRIC-LETTERS_v2",
        root_template_version=None,
        actor_id="user-1",
    )
    payload["finish_setup"]["acm_panel_instance"]["association_status"] = "proposed"
    mark_job_revision_stale_if_confirmed(payload)
    response, out = confirm_job_product_truth(
        workspace_id="ws-1",
        workspace_code="IV6-TEST",
        payload_raw=payload,
        expected_revision=1,
        expected_draft_hash=draft_hash_for_payload(payload),
        expected_content_hash=None,
        root_template_code="TPL-VOLUMETRIC-LETTERS_v2",
        root_template_version=None,
        actor_id="user-1",
        correction_reason="operator correction",
    )
    assert response["write_performed"] is True
    assert response["metadata"]["revision"] == 2
    assert response["metadata"]["confirmation_state"] == "confirmed"
    assert commercial_freeze_allowed(out) is True


def test_acm_mirrors_projected_from_canonical():
    finish = {
        "acm_panel_instance": {
            "schema": "acm_panel_component_instance_v1",
            "component_instance_id": "acm-1",
            "component_template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
        },
        "svg_support_selection": {"schema": "svg_support_selection_v1", "status": "proposed"},
        "mounting_solution": {"template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1", "configuration": {}},
    }
    out = project_acm_mirrors_from_canonical(copy.deepcopy(finish))
    assert out["svg_support_selection"]["acm_panel_instance"]["component_instance_id"] == "acm-1"
    assert out["mounting_solution"]["configuration"]["acm_panel_instance"]["component_instance_id"] == "acm-1"


def test_content_hash_mismatch_409():
    payload = _payload_with_bags()
    confirm_job_product_truth(
        workspace_id="ws-1",
        workspace_code="IV6-TEST",
        payload_raw=payload,
        expected_revision=0,
        expected_draft_hash=None,
        expected_content_hash=None,
        root_template_code="TPL-VOLUMETRIC-LETTERS_v2",
        root_template_version=None,
        actor_id="user-1",
    )
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        confirm_job_product_truth(
            workspace_id="ws-1",
            workspace_code="IV6-TEST",
            payload_raw=payload,
            expected_revision=1,
            expected_draft_hash=None,
            expected_content_hash="sha256:deadbeef",
            root_template_code="TPL-VOLUMETRIC-LETTERS_v2",
            root_template_version=None,
            actor_id="user-1",
        )
    assert exc.value.status_code == 409
    assert exc.value.detail["error"] == "content_hash_mismatch"


def test_apply_pinned_bags_ignores_live_draft_drift():
    payload = _payload_with_bags()
    confirm_job_product_truth(
        workspace_id="ws-1",
        workspace_code="IV6-TEST",
        payload_raw=payload,
        expected_revision=0,
        expected_draft_hash=None,
        expected_content_hash=None,
        root_template_code="TPL-VOLUMETRIC-LETTERS_v2",
        root_template_version=None,
        actor_id="user-1",
    )
    pinned_id = payload["product_truth"]["confirmed_snapshot_v1"]["pinned_typed_bags"][
        "letter_group_instances"
    ][0]["instance_id"]
    payload["finish_setup"]["letter_group_instances"][0]["instance_id"] = "drifted-live-id"
    restored = apply_pinned_bags_onto_payload(payload)
    assert restored["finish_setup"]["letter_group_instances"][0]["instance_id"] == pinned_id
    assert commercial_freeze_allowed(payload) is True


def test_order_provenance_copies_product_truth_revision_no_live_reread():
    parsed = SimpleNamespace(provenance={"source": "quote_snapshot_v2"})
    linkage = {
        "product_truth_revision": 3,
        "product_truth_content_hash": "sha256:pin",
        "freeze_from_pinned_product_truth": True,
    }
    prov = _enrich_order_provenance_with_product_truth(parsed, linkage)
    assert prov["product_truth_revision"] == 3
    assert prov["product_truth_content_hash"] == "sha256:pin"
    assert prov["freeze_from_pinned_product_truth"] is True
    assert prov["no_live_workspace_reread"] is True
