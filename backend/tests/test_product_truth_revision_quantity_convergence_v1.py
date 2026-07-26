"""FINAL COMPLETION GATE — PD / Aggregate / Quantity / EIC revision+quantity convergence."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
import pytest_asyncio

from services.estimated_internal_cost_service import _overlay_canonical_quantity_builder
from services.intake_v6_quote_snapshot_v2_service import (
    V6_SNAPSHOT_PRODUCT_TRUTH_PROVENANCE_MISMATCH,
    _product_truth_provenance_mismatch_blocker,
)
from services.letter_group_instance_authority import build_volumetric_letters_commercial_quantities
from services.letters_commercial_measurement_service import build_letters_commercial_measurements
from services.product_aggregate_service import ProductAggregateService
from services.product_definition_builder_service import ProductDefinitionBuilderService
from services.product_truth_job_confirm_service import (
    confirm_job_product_truth,
    get_job_revision_metadata,
    read_product_truth_provenance,
)

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

ROOT = "TPL-VOLUMETRIC-LETTERS_v2"


def _confirmable_payload() -> dict:
    return {
        "template_code": ROOT,
        "analysis_ready": True,
        "quote_geometry": {
            "letter_count": 2,
            "letter_perimeter_m": 9.5,
            "letter_face_area_m2": 99.0,  # deliberate conflict vs instances
        },
        "finish_setup": {
            "letter_group_instances": [
                {
                    "schema": "volumetric_letter_group_instance_v1",
                    "instance_id": "11111111-1111-1111-1111-111111111111",
                    "group_key": "pseudo:maria",
                    "confirmed": True,
                    "geometry": {"face_area_m2": 0.2, "perimeter_m": 1.0},
                    "lighting": {"illuminated": True, "led_module_count": 3},
                },
                {
                    "schema": "volumetric_letter_group_instance_v1",
                    "instance_id": "22222222-2222-2222-2222-222222222222",
                    "group_key": "pseudo:soare",
                    "confirmed": True,
                    "geometry": {"face_area_m2": 0.3, "perimeter_m": 2.0},
                    "lighting": {"illuminated": True, "led_module_count": 5},
                },
            ],
            "led_module_count": 999,  # deliberate conflict
            "acm_panel_instance": {
                "schema": "acm_panel_component_instance_v1",
                "component_instance_id": "acm-1",
                "component_template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                "association_status": "confirmed",
            },
        },
    }


def test_quantity_builder_surfaces_product_truth_provenance():
    qty = build_volumetric_letters_commercial_quantities(
        quote_geometry={"letter_perimeter_m": 9.5},
        finish_setup=_confirmable_payload()["finish_setup"],
        product_truth_job_revision=3,
        product_truth_content_hash="abc123",
        product_truth_status="confirmed",
    )
    assert qty["product_truth_job_revision"] == 3
    assert qty["product_truth_content_hash"] == "abc123"
    assert qty["product_truth_status"] == "confirmed"
    assert qty["letter_face_area_m2"] == 0.5
    assert qty["led_module_count"] == 8


def test_eic_overlay_prefers_quantity_builder_over_raw_payload():
    payload = _confirmable_payload()
    out = _overlay_canonical_quantity_builder(ROOT, payload)
    assert out["quote_geometry"]["letter_face_area_m2"] == 0.5
    assert out["quote_geometry"]["letter_perimeter_m"] == 9.5
    assert out["finish_setup"]["led_module_count"] == 8
    assert out["volumetric_letters_commercial_quantities"]["source"] == (
        "letter_group_instance_authority"
    )


def test_freeze_provenance_mismatch_blocker_detects_missing_surfaces():
    job_meta = {"revision": 2, "content_hash": "deadbeef"}
    pd = SimpleNamespace(
        product_truth_job_revision=2,
        product_truth_content_hash="deadbeef",
        template_code=ROOT,
    )
    agg = SimpleNamespace(
        template_code=ROOT,
        provenance_summary=SimpleNamespace(
            product_truth_job_revision=2,
            product_truth_content_hash="deadbeef",
        ),
        commercial_measurements=None,
    )
    snap = SimpleNamespace(product_definition_snapshot=pd, product_aggregate_snapshot=agg)
    blocker = _product_truth_provenance_mismatch_blocker(
        job_truth_meta=job_meta,
        quote_snapshot_v2=snap,
    )
    assert blocker is not None
    assert blocker["code"] == V6_SNAPSHOT_PRODUCT_TRUTH_PROVENANCE_MISMATCH
    assert "quantity_builder" in blocker["message"]


def test_freeze_provenance_mismatch_blocker_passes_when_aligned():
    job_meta = {"revision": 2, "content_hash": "deadbeef"}
    pd = SimpleNamespace(
        product_truth_job_revision=2,
        product_truth_content_hash="deadbeef",
        template_code=ROOT,
    )
    cm = SimpleNamespace(
        product_truth_job_revision=2,
        product_truth_content_hash="deadbeef",
    )
    agg = SimpleNamespace(
        template_code=ROOT,
        provenance_summary=SimpleNamespace(
            product_truth_job_revision=2,
            product_truth_content_hash="deadbeef",
        ),
        commercial_measurements=cm,
    )
    snap = SimpleNamespace(product_definition_snapshot=pd, product_aggregate_snapshot=agg)
    assert (
        _product_truth_provenance_mismatch_blocker(
            job_truth_meta=job_meta,
            quote_snapshot_v2=snap,
        )
        is None
    )


@pytest_asyncio.fixture
async def confirmed_workspace(volumetric_v2_db):
    from models.intake_v6_workspace import IntakeV6WorkspaceRecord
    import json
    import uuid

    _, confirmed = confirm_job_product_truth(
        workspace_id="pending",
        workspace_code="IV6-CONV",
        payload_raw=_confirmable_payload(),
        expected_revision=0,
        expected_draft_hash=None,
        expected_content_hash=None,
        root_template_code=ROOT,
        root_template_version=None,
        actor_id="convergence",
    )
    meta = get_job_revision_metadata(confirmed)
    assert meta is not None
    workspace_id = str(uuid.uuid4())
    record = IntakeV6WorkspaceRecord(
        id=workspace_id,
        workspace_code="IV6-CONV",
        title="Convergence fixture",
        template_code=ROOT,
        status="draft",
        payload_json=json.dumps(confirmed),
    )
    volumetric_v2_db.add(record)
    await volumetric_v2_db.commit()
    return workspace_id, confirmed, meta


@pytest.mark.asyncio
async def test_pd_aggregate_quantity_share_confirmed_revision(
    volumetric_v2_db, confirmed_workspace
) -> None:
    workspace_id, confirmed, meta = confirmed_workspace
    expected_rev = int(meta["revision"])
    expected_hash = str(meta["content_hash"])

    pd = await ProductDefinitionBuilderService(volumetric_v2_db).build_preview(
        ROOT, workspace_id=workspace_id
    )
    assert pd is not None
    assert pd.product_truth_job_revision == expected_rev
    assert pd.product_truth_content_hash == expected_hash
    assert pd.product_truth_status == "confirmed"
    assert any(e.key == "product_truth_job_revision" for e in pd.provenance)

    aggregate = await ProductAggregateService(volumetric_v2_db).build_for_workspace(
        ROOT, workspace_id
    )
    assert aggregate is not None
    assert aggregate.provenance_summary.product_truth_job_revision == expected_rev
    assert aggregate.provenance_summary.product_truth_content_hash == expected_hash
    assert aggregate.commercial_measurements is not None
    assert aggregate.commercial_measurements.product_truth_job_revision == expected_rev
    assert aggregate.commercial_measurements.product_truth_content_hash == expected_hash

    truth = read_product_truth_provenance(confirmed)
    qty = build_volumetric_letters_commercial_quantities(
        quote_geometry=confirmed.get("quote_geometry"),
        finish_setup=confirmed.get("finish_setup"),
        product_truth_job_revision=truth["product_truth_job_revision"],
        product_truth_content_hash=truth["product_truth_content_hash"],
        product_truth_status=truth["product_truth_status"],
    )
    assert qty["product_truth_job_revision"] == expected_rev
    assert qty["product_truth_content_hash"] == expected_hash

    bundle = build_letters_commercial_measurements(
        template_code=ROOT,
        pd=pd,
        quote_input=confirmed,
    )
    assert bundle is not None
    assert bundle.product_truth_job_revision == expected_rev
    assert bundle.product_truth_content_hash == expected_hash
