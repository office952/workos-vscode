"""VL pre-publication E2E proof — close six NOT_TESTED with fresh runtime evidence.

Fixture lineage: VL_PREPUB_E2E_FIXTURE_v1 (12.5 m confirmed perimeter, depth 60,
white_aluminum). No parent publish. No live customer Quote/Order.
"""

from __future__ import annotations

import json
import uuid
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy import select

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from models.product_templates import Product_templates
from schemas.commercial_price_proposal import CommercialPriceProposalPreview
from schemas.estimated_internal_cost import EstimatedInternalCostPreview
from schemas.product_aggregate import ProductAggregate
from schemas.product_definition import (
    ProductDefinitionPreview,
    ProductDefinitionSourceContext,
)
from schemas.quote_snapshot_v2 import QuoteSnapshotOfferScope, QuoteSnapshotV2
from schemas.volum_aluminiu_separate_calc_preview import VolumAluminiuSeparateCalcPreviewRequest
from services.execution_preview_from_frozen_graph_service import (
    build_execution_preview_from_frozen_snapshot,
)
from services.letter_group_instance_authority import build_volumetric_letters_commercial_quantities
from services.letters_commercial_measurement_service import build_letters_commercial_measurements
from services.order_snapshot_v2_convert_service import (
    _enrich_order_provenance_with_product_truth,
)
from services.product_aggregate_service import ProductAggregateService
from services.product_definition_builder_service import ProductDefinitionBuilderService
from services.product_e2e_readiness_service import ProductE2EReadinessService
from services.product_truth_job_confirm_service import (
    commercial_freeze_allowed,
    confirm_job_product_truth,
    get_job_revision_metadata,
    read_product_truth_provenance,
)
from services.volum_aluminiu_component_contract import (
    COMMERCIAL_BASIS_SYNONYM,
    COMMERCIAL_LINE_CODE,
    INTERNAL_RULE_CODE,
    PARENT_TEMPLATE_CODE,
    TEMPLATE_CODE as CHILD_ALUMINIU,
)
from services.volum_aluminiu_quantity_ownership import (
    resolve_component_quantity_from_payload,
    resolve_product_total_perimeter_authority,
)
from services.volum_aluminiu_separate_calc_preview_service import (
    VolumAluminiuSeparateCalcPreviewService,
)
from tests.test_product_aggregate_volumetric_v2 import (
    CHILD_ALUMINUM,
    TEMPLATE_CODE,
    _seed_volumetric_v2_fixture,
)

CONFIRMED_PERIMETER_M = 12.5
RETURN_DEPTH_MM = 60
FINISH_TYPE = "white_aluminum"
FIXTURE_LABEL = "VL_PREPUB_E2E_FIXTURE_v1"


def _prepub_payload(*, perimeter: float = CONFIRMED_PERIMETER_M) -> dict:
    """Isolated fixture: confirmed return perimeter + letter groups (no SVG parse)."""
    return {
        "template_code": TEMPLATE_CODE,
        "analysis_ready": True,
        "fixture_label": FIXTURE_LABEL,
        "quote_geometry": {
            "letter_count": 1,
            "letter_perimeter_m": perimeter,
            "letter_face_area_m2": 0.25,
        },
        "layer_role_setup": {
            "layers": [
                {
                    "layer_key": "pseudo:maria",
                    "layer_id": "pseudo:maria",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                }
            ]
        },
        "finish_setup": {
            "return_finish_type": FINISH_TYPE,
            "return_depth_mm": RETURN_DEPTH_MM,
            "letter_group_finishes": [
                {
                    "group_key": "pseudo:maria",
                    "return_finish_type": FINISH_TYPE,
                    "return_depth_mm": RETURN_DEPTH_MM,
                }
            ],
            "return_cant_component_confirmation": {
                "instances": {
                    "letter_group:pseudo:maria": {
                        "confirmed_perimeter_m": perimeter,
                        "confirmed_perimeter_source": "operator_confirmed",
                        "confirmation_source": "operator_component_confirmation",
                    }
                }
            },
            "letter_group_instances": [
                {
                    "schema": "volumetric_letter_group_instance_v1",
                    "instance_id": "11111111-1111-1111-1111-111111111111",
                    "group_key": "pseudo:maria",
                    "confirmed": True,
                    "geometry": {"face_area_m2": 0.25, "perimeter_m": perimeter},
                    "lighting": {"illuminated": True, "led_module_count": 4},
                }
            ],
            "acm_panel_instance": {
                "schema": "acm_panel_component_instance_v1",
                "component_instance_id": "acm-prepub-1",
                "component_template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                "association_status": "confirmed",
            },
        },
    }


@pytest_asyncio.fixture
async def volumetric_v2_db(db_session):
    await _seed_volumetric_v2_fixture(db_session)
    # Activation GO already landed — keep aluminiu active for publication-axis honesty.
    child = (
        await db_session.execute(
            select(Product_templates).where(
                Product_templates.template_code == CHILD_ALUMINUM
            ).limit(1)
        )
    ).scalar_one()
    child.active = True
    await db_session.commit()
    return db_session


@pytest_asyncio.fixture
async def prepub_confirmed_workspace(volumetric_v2_db):
    _, confirmed = confirm_job_product_truth(
        workspace_id="pending",
        workspace_code="IV6-VL-PREPUB",
        payload_raw=_prepub_payload(),
        expected_revision=0,
        expected_draft_hash=None,
        expected_content_hash=None,
        root_template_code=TEMPLATE_CODE,
        root_template_version=None,
        actor_id="vl_prepub_e2e",
    )
    meta = get_job_revision_metadata(confirmed)
    assert meta is not None
    assert commercial_freeze_allowed(confirmed) is True
    workspace_id = str(uuid.uuid4())
    record = IntakeV6WorkspaceRecord(
        id=workspace_id,
        workspace_code=f"IV6-VL-PREPUB-{workspace_id[:8]}",
        title=FIXTURE_LABEL,
        template_code=TEMPLATE_CODE,
        status="draft",
        payload_json=json.dumps(confirmed),
    )
    volumetric_v2_db.add(record)
    await volumetric_v2_db.commit()
    return workspace_id, confirmed, meta


# --- CP1 Intake + Product Truth ---


def test_cp1_intake_fixture_has_confirmed_perimeter_and_alum_spec():
    payload = _prepub_payload()
    bag = payload["finish_setup"]["return_cant_component_confirmation"]["instances"]
    inst = bag["letter_group:pseudo:maria"]
    assert inst["confirmed_perimeter_m"] == CONFIRMED_PERIMETER_M
    assert payload["finish_setup"]["return_depth_mm"] == RETURN_DEPTH_MM
    assert payload["finish_setup"]["return_finish_type"] == FINISH_TYPE
    assert payload["template_code"] == PARENT_TEMPLATE_CODE


def test_cp1_product_truth_confirm_freeze_allowed():
    _, confirmed = confirm_job_product_truth(
        workspace_id="ws-prepub-pt",
        workspace_code="IV6-VL-PREPUB-PT",
        payload_raw=_prepub_payload(),
        expected_revision=0,
        expected_draft_hash=None,
        expected_content_hash=None,
        root_template_code=TEMPLATE_CODE,
        root_template_version=None,
        actor_id="vl_prepub_e2e",
    )
    meta = get_job_revision_metadata(confirmed)
    assert meta is not None
    assert meta["confirmation_state"] == "confirmed"
    assert meta["revision"] == 1
    assert str(meta["content_hash"]).startswith("sha256:")
    assert commercial_freeze_allowed(confirmed) is True


# --- CP2 / CP3 PD + Aggregate + Quantity ---


@pytest.mark.asyncio
async def test_cp2_cp3_pd_aggregate_quantity_share_revision(
    volumetric_v2_db, prepub_confirmed_workspace
):
    workspace_id, confirmed, meta = prepub_confirmed_workspace
    expected_rev = int(meta["revision"])
    expected_hash = str(meta["content_hash"])

    pd = await ProductDefinitionBuilderService(volumetric_v2_db).build_preview(
        TEMPLATE_CODE, workspace_id=workspace_id
    )
    assert pd is not None
    assert pd.product_truth_job_revision == expected_rev
    assert pd.product_truth_content_hash == expected_hash

    aggregate = await ProductAggregateService(volumetric_v2_db).build_for_workspace(
        TEMPLATE_CODE, workspace_id
    )
    assert aggregate is not None
    assert aggregate.provenance_summary.product_truth_job_revision == expected_rev
    assert aggregate.provenance_summary.product_truth_content_hash == expected_hash
    # Identity: modelare_cant once (no double BOM owner)
    module_codes = [m.module_code for m in (aggregate.modules.required or [])]
    assert module_codes.count("modelare_cant") <= 1 or any(
        getattr(c, "mini_module_code", None) == "modelare_cant"
        for c in aggregate.components
    )

    truth = read_product_truth_provenance(confirmed)
    qty = build_volumetric_letters_commercial_quantities(
        quote_geometry=confirmed.get("quote_geometry"),
        finish_setup=confirmed.get("finish_setup"),
        product_truth_job_revision=truth["product_truth_job_revision"],
        product_truth_content_hash=truth["product_truth_content_hash"],
        product_truth_status=truth["product_truth_status"],
    )
    assert qty["product_truth_job_revision"] == expected_rev
    assert qty["letter_face_area_m2"] == 0.25

    bundle = build_letters_commercial_measurements(
        template_code=TEMPLATE_CODE,
        pd=pd,
        quote_input=confirmed,
    )
    assert bundle is not None
    assert bundle.product_truth_job_revision == expected_rev


# --- CP4 CPP + EIC ---


def test_cp4_cpp_eic_preview_matches_product_total_ml_anti_hourly():
    payload = _prepub_payload()
    component = resolve_component_quantity_from_payload(payload)
    total = resolve_product_total_perimeter_authority(payload)
    preview = VolumAluminiuSeparateCalcPreviewService().build_preview(
        CHILD_ALUMINIU,
        VolumAluminiuSeparateCalcPreviewRequest(payload=payload),
    )

    assert component["ok"] is True
    assert component["quantity_m"] == CONFIRMED_PERIMETER_M
    assert total["ok"] is True
    assert total["quantity_m"] == CONFIRMED_PERIMETER_M
    assert preview.separate_calculation == "PASS"
    assert preview.persist is False
    assert preview.quantity["quantity_m"] == CONFIRMED_PERIMETER_M
    assert preview.commercial is not None
    assert preview.commercial["basis_type"] == COMMERCIAL_BASIS_SYNONYM
    assert preview.commercial["line_code"] == COMMERCIAL_LINE_CODE
    assert preview.commercial.get("anti_hourly") is True
    assert preview.internal_cost is not None
    assert preview.internal_cost["rule_code"] == INTERNAL_RULE_CODE
    assert preview.internal_cost.get("anti_hourly") is True
    assert abs(float(preview.quantity["quantity_m"]) - float(total["quantity_m"])) < 1e-6


def test_cp4_negative_divergence_fail_closed():
    payload = _prepub_payload(perimeter=12.5)
    payload["quote_geometry"]["letter_perimeter_m"] = 18.5
    total = resolve_product_total_perimeter_authority(payload)
    assert total.get("fail_closed") is True
    assert total.get("quantity_m") is None


# --- CP5 Quote Snapshot freeze gate ---


def test_cp5_quote_snapshot_freeze_gate_allows_confirmed():
    _, confirmed = confirm_job_product_truth(
        workspace_id="ws-prepub-snap",
        workspace_code="IV6-VL-PREPUB-SNAP",
        payload_raw=_prepub_payload(),
        expected_revision=0,
        expected_draft_hash=None,
        expected_content_hash=None,
        root_template_code=TEMPLATE_CODE,
        root_template_version=None,
        actor_id="vl_prepub_e2e",
    )
    assert commercial_freeze_allowed(confirmed) is True


# --- CP6 / CP7 Order provenance + EP preview ---


def test_cp6_order_provenance_no_live_reread():
    parsed = SimpleNamespace(provenance={"source": "quote_snapshot_v2"})
    linkage = {
        "product_truth_revision": 1,
        "product_truth_content_hash": "sha256:prepub",
        "freeze_from_pinned_product_truth": True,
    }
    prov = _enrich_order_provenance_with_product_truth(parsed, linkage)
    assert prov["product_truth_revision"] == 1
    assert prov["no_live_workspace_reread"] is True


def test_cp7_execution_preview_frozen_no_materialization():
    snap = QuoteSnapshotV2(
        template_code=TEMPLATE_CODE,
        offer_scope_snapshot=QuoteSnapshotOfferScope(
            mode="full_product", sold_modules=[], use_legacy=True
        ),
        product_definition_snapshot=ProductDefinitionPreview(
            template_code=TEMPLATE_CODE,
            source_context=ProductDefinitionSourceContext(template_code=TEMPLATE_CODE),
        ),
        product_aggregate_snapshot=ProductAggregate(
            template_code=TEMPLATE_CODE, template_id=0
        ),
        commercial_price_proposal_snapshot=CommercialPriceProposalPreview(
            template_code=TEMPLATE_CODE, currency="RON"
        ),
        estimated_internal_cost_snapshot=EstimatedInternalCostPreview(
            template_code=TEMPLATE_CODE
        ),
        persist_status="not_persisted",
    )
    preview = build_execution_preview_from_frozen_snapshot(snap)
    assert preview.safety.no_write is True
    assert preview.safety.no_materialization is True
    assert preview.safety.no_live_recompile is True


# --- Readiness: static preserves NOT_TESTED; runtime closes six ---


@pytest.mark.asyncio
async def test_static_readiness_preserves_not_tested_for_unproven_stages(volumetric_v2_db):
    result = await ProductE2EReadinessService(volumetric_v2_db).run_static(TEMPLATE_CODE)
    assert result.write_performed is False
    systems = {n.system: n.status for n in result.systems}
    for key in (
        "product_truth",
        "cpp",
        "eic",
        "quote_snapshot",
        "order_snapshot",
        "execution_preview",
    ):
        assert systems[key] == "NOT_TESTED", f"{key} should stay NOT_TESTED in static"
    assert result.template_publication_status in ("PASS", "PASS_WITH_WARNINGS", "BLOCKED")


@pytest.mark.asyncio
async def test_runtime_dry_run_closes_six_not_tested(
    volumetric_v2_db, prepub_confirmed_workspace
):
    workspace_id, _confirmed, _meta = prepub_confirmed_workspace
    result = await ProductE2EReadinessService(volumetric_v2_db).run_runtime_dry_run(
        TEMPLATE_CODE,
        workspace_id=workspace_id,
        dry_run=True,
    )
    assert result.write_performed is False
    assert result.no_write is True
    assert result.mode == "runtime_dry_run"
    systems = {n.system: n.status for n in result.systems}
    for key in (
        "product_truth",
        "cpp",
        "eic",
        "quote_snapshot",
        "order_snapshot",
        "execution_preview",
    ):
        assert systems[key] == "PASS", (
            f"{key} expected PASS after runtime evidence, got {systems[key]}; "
            f"findings={[ (f.check_id, f.status, f.message) for f in result.findings if f.system == key ]}"
        )
    assert result.verdict in ("RUNTIME_READY", "PARTIAL")
    # Parent must remain unpublished axis-wise if publication still blocked by other findings;
    # activation closed inactivity — publication GO is separate.
    assert result.e2e_ready is True or result.verdict == "PARTIAL"
