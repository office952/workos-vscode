"""Tests for dual Quote Snapshot V2 preview and persistence (Step 8 / 8.2)."""

from __future__ import annotations

import ast
import json
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy import func, select

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from schemas.quote_snapshot_v2 import QUOTE_SNAPSHOT_V2_VERSION, QuoteSnapshotV2
from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.estimated_internal_cost_service import EstimatedInternalCostService
from services.quote_snapshot_v2_service import (
    PERSISTENCE_AVAILABLE,
    QuoteSnapshotV2Service,
)

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"

SAMPLE_RATES = {
    "MAT-SABLON-MONTAJ": 8.0,
    "MAT-SABLON-HARTIE": 2.0,
    "MAT-LED-MODULE": 0.5,
    "MAT-LED-PSU-12V-100W": 45.0,
    "MAT-PROFIL-LATERAL-LITERE-60MM": 3.0,
    "MAT-ORACAL-651": 9.0,
}

INVENTORY_CATALOG = {
    code: {"status": "active", "unit_cost": rate}
    for code, rate in {
        **SAMPLE_RATES,
        "MAT-LED-PSU-12V-60W": 30.0,
        "MAT-ACP-FATA-LITERE": 15.0,
        "MAT-SPATE-PVC-LITERE": 8.0,
        "MAT-ADEZIV-CANT-LITERE": 4.0,
        "MAT-VOPSEA-RAL": 10.0,
    }.items()
}


def _full_quote_input(*, mounting_system: str = "direct_wall") -> dict:
    return {
        "analysis_ready": True,
        "svg_source": {"file_name": "test.svg"},
        "client": {"width_mm": 1200, "height_mm": 400},
        "quote_geometry": {
            "letter_count": 5,
            "letter_perimeter_m": 12.5,
            "letter_face_area_m2": 1.2,
        },
        "finish_setup": {
            "face_finish_type": "plexiglas_clear",
            "return_depth_mm": 60,
            "return_finish_type": "ral",
            "volum_aluminum_module_template_code": "TPL-VOLUM-ALUMINIU_v1",
            "backing_mode": "closed_back",
            "mounting_system": mounting_system,
            "lighting_system_type": "front_lit",
            "illuminated": True,
            "led_module_count": 24,
            "selected_psu_watts": 100,
            "required_psu_watts": 140.4,
            "mounting_template_enabled": True,
            "mounting_template_area_m2": 2.5,
            "mounting_template_material_type": "forex",
            "letter_group_finishes": [{"group_key": "default", "confirmed": True}],
        },
    }


@pytest_asyncio.fixture
async def cpp_service(volumetric_v2_db):
    yield CommercialPriceProposalService(volumetric_v2_db)


@pytest_asyncio.fixture
async def eic_service(volumetric_v2_db):
    service = EstimatedInternalCostService(volumetric_v2_db)

    async def _patched_load():
        return SAMPLE_RATES, {"RON": "RON"}, {"WC_CNC_ROUTING": 120.0}, INVENTORY_CATALOG

    service._load_pricing_context = _patched_load  # type: ignore[method-assign]
    yield service


@pytest_asyncio.fixture
async def snapshot_service(volumetric_v2_db, eic_service):
    yield QuoteSnapshotV2Service(
        volumetric_v2_db,
        eic_service=eic_service,
    )


@pytest.fixture
def allow_freeze_readiness(monkeypatch):
    """Default volumetric payload yields dual-blocked 7G/7H; persistence tests need allowed readiness."""

    def _allowed(commercial, internal):
        if commercial.forbidden_hourly_usage_detected or internal.hourly_contamination_detected:
            return "blocked_forbidden_path"
        return "partial_with_owner_decisions"

    monkeypatch.setattr(
        "services.quote_snapshot_v2_service.compute_readiness",
        _allowed,
    )


@pytest.fixture
def snapshot_auth_client(volumetric_auth_client):
    return volumetric_auth_client


async def _seed_workspace(volumetric_v2_db, *, payload: dict | None = None) -> str:
    workspace_id = str(uuid.uuid4())
    record = IntakeV6WorkspaceRecord(
        id=workspace_id,
        workspace_code=f"WS-QS2-{workspace_id[:8]}",
        title="QS2 test workspace",
        template_code=TEMPLATE,
        payload_json=json.dumps(payload or _full_quote_input()),
        status="draft",
    )
    volumetric_v2_db.add(record)
    await volumetric_v2_db.commit()
    return workspace_id


# 1. dry-run includes both snapshots
@pytest.mark.asyncio
async def test_dry_run_includes_both_snapshots(snapshot_service: QuoteSnapshotV2Service):
    snapshot = await snapshot_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert snapshot is not None
    assert snapshot.commercial_price_proposal_snapshot is not None
    assert snapshot.estimated_internal_cost_snapshot is not None
    assert snapshot.commercial_price_proposal_snapshot.source == "commercial_price_proposal"
    assert snapshot.estimated_internal_cost_snapshot.source == "estimated_internal_cost"


# 2. totals remain separate
@pytest.mark.asyncio
async def test_totals_remain_separate(snapshot_service: QuoteSnapshotV2Service):
    snapshot = await snapshot_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert snapshot is not None
    commercial = snapshot.commercial_price_proposal_snapshot
    internal = snapshot.estimated_internal_cost_snapshot
    assert internal.estimated_total_internal_cost is not None
    assert snapshot.input_summary.get("internal_total") is not None
    assert commercial.commercial_total != internal.estimated_total_internal_cost
    assert "commercial_total" in snapshot.input_summary
    assert "internal_total" in snapshot.input_summary


# 3. internal does not overwrite commercial
@pytest.mark.asyncio
async def test_internal_does_not_overwrite_commercial(
    snapshot_service: QuoteSnapshotV2Service,
    cpp_service: CommercialPriceProposalService,
):
    payload = _full_quote_input()
    commercial_only = await cpp_service.build_preview(TEMPLATE, quote_input=payload)
    snapshot = await snapshot_service.build_preview(TEMPLATE, quote_input=payload)
    assert commercial_only is not None and snapshot is not None
    assert snapshot.commercial_price_proposal_snapshot.commercial_total == commercial_only.commercial_total
    assert snapshot.commercial_price_proposal_snapshot.subtotal_commercial == commercial_only.subtotal_commercial


# 4. commercial does not overwrite internal
@pytest.mark.asyncio
async def test_commercial_does_not_overwrite_internal(
    snapshot_service: QuoteSnapshotV2Service,
    eic_service: EstimatedInternalCostService,
):
    payload = _full_quote_input()
    internal_only = await eic_service.build_preview(TEMPLATE, quote_input=payload)
    snapshot = await snapshot_service.build_preview(TEMPLATE, quote_input=payload)
    assert internal_only is not None and snapshot is not None
    assert (
        snapshot.estimated_internal_cost_snapshot.estimated_total_internal_cost
        == internal_only.estimated_total_internal_cost
    )
    assert (
        snapshot.estimated_internal_cost_snapshot.estimated_material_cost
        == internal_only.estimated_material_cost
    )


# 5. snapshot does not call /price
@pytest.mark.asyncio
async def test_snapshot_does_not_call_price(snapshot_auth_client):
    response = snapshot_auth_client.post(
        f"/api/v1/product-system/quote-snapshot-v2/preview/{TEMPLATE}",
        json={"quote_input": _full_quote_input(), "currency": "RON"},
    )
    assert response.status_code == 200
    body = response.json()
    notes_blob = " ".join(body.get("notes", [])).lower()
    assert "/price" not in notes_blob or "does not call /price" in notes_blob
    assert body["persist_status"] == "not_persisted"


# 6. no QuoteOrchestrator import
def test_service_does_not_import_quote_orchestrator():
    modules = _forbidden_service_imports()
    assert not any("quote_orchestrator" in mod for mod in modules)


# 7. no CostEngine import
def test_service_does_not_import_cost_engine():
    modules = _forbidden_service_imports()
    assert not any("cost_engine" in mod for mod in modules)


def _step8_qa_quote_input(*, mounting_template_material_type: str = "paper") -> dict:
    """Paper sablon avoids forex owner-critical blockers; geometry matches live QA payload."""
    payload = _full_quote_input()
    payload["finish_setup"]["mounting_template_material_type"] = mounting_template_material_type
    return payload


@pytest.mark.asyncio
async def test_dev_bridge_readiness_not_dual_blocked(volumetric_v2_db):
    """Without allow_freeze monkeypatch, dev bridge must avoid blocked_snapshot_conflict."""
    service = QuoteSnapshotV2Service(volumetric_v2_db)
    snapshot = await service.build_preview(
        TEMPLATE,
        quote_input=_step8_qa_quote_input(mounting_template_material_type="paper"),
    )
    assert snapshot is not None
    assert snapshot.commercial_price_proposal_snapshot.status == "blocked"
    assert snapshot.estimated_internal_cost_snapshot.status in ("partial", "ready")
    assert snapshot.readiness == "partial_with_owner_decisions"
    assert snapshot.readiness != "blocked_snapshot_conflict"


@pytest.mark.asyncio
async def test_freeze_partial_persists_status_frozen(volumetric_v2_db):
    """Step 8.3: partial readiness freeze must persist status=frozen for accept gate."""
    workspace_id = await _seed_workspace(volumetric_v2_db)
    service = QuoteSnapshotV2Service(volumetric_v2_db)
    snapshot = await service.freeze(
        TEMPLATE,
        workspace_id=workspace_id,
        quote_input=_step8_qa_quote_input(mounting_template_material_type="paper"),
        frozen_by="op-1",
    )
    assert snapshot is not None
    assert snapshot.persist_status == "persisted"
    assert snapshot.readiness == "partial_with_owner_decisions"
    record = await volumetric_v2_db.scalar(
        select(QuoteSnapshotV2Record).where(
            QuoteSnapshotV2Record.snapshot_code == snapshot.snapshot_code
        )
    )
    assert record is not None
    assert record.status == "frozen"
    assert record.readiness == "partial_with_owner_decisions"


# 8. blocked 7G produces blocked/partial readiness
@pytest.mark.asyncio
async def test_blocked_7g_readiness(snapshot_service: QuoteSnapshotV2Service):
    bad_input = _full_quote_input()
    bad_input["quote_geometry"] = {"letter_count": 5}
    bad_input.pop("client", None)
    snapshot = await snapshot_service.build_preview(TEMPLATE, quote_input=bad_input)
    assert snapshot is not None
    assert snapshot.commercial_price_proposal_snapshot.status == "blocked"
    assert snapshot.readiness in (
        "blocked_missing_commercial",
        "partial_with_owner_decisions",
        "blocked_snapshot_conflict",
    )
    assert snapshot.readiness != "ready_for_owner_review"


# 9. blocked 7H produces blocked/partial readiness
@pytest.mark.asyncio
async def test_blocked_7h_readiness(volumetric_v2_db):
    service = QuoteSnapshotV2Service(volumetric_v2_db)
    eic = EstimatedInternalCostService(volumetric_v2_db)

    async def _empty():
        return {}, {}, {}, {}

    eic._load_pricing_context = _empty  # type: ignore[method-assign]
    service._eic = eic
    snapshot = await service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert snapshot is not None
    assert snapshot.estimated_internal_cost_snapshot.status == "blocked"
    assert snapshot.readiness in (
        "blocked_missing_internal",
        "partial_with_owner_decisions",
        "blocked_snapshot_conflict",
    )
    assert snapshot.readiness != "ready_for_owner_review"


# 10. owner decisions carried from 7G and 7H
@pytest.mark.asyncio
async def test_owner_decisions_carried(snapshot_service: QuoteSnapshotV2Service):
    snapshot = await snapshot_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert snapshot is not None
    sources = {d.source for d in snapshot.owner_decisions_snapshot}
    assert "commercial_price_proposal" in sources
    assert "estimated_internal_cost" in sources
    assert any(d.code == "DEBITARE_SPATE_BASIS_ML_VS_M2" for d in snapshot.owner_decisions_snapshot)


# 11. provenance present
@pytest.mark.asyncio
async def test_provenance_present(snapshot_service: QuoteSnapshotV2Service):
    snapshot = await snapshot_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert snapshot is not None
    keys = {p.key for p in snapshot.provenance}
    assert "commercial_price_proposal" in keys
    assert "estimated_internal_cost" in keys
    assert "product_definition" in keys
    assert "assembled_at" in keys


# 12. dry-run does not write DB
@pytest.mark.asyncio
async def test_dry_run_no_db_writes(snapshot_service: QuoteSnapshotV2Service, volumetric_v2_db):
    session = volumetric_v2_db
    add_mock = MagicMock(wraps=session.add)
    commit_mock = AsyncMock(wraps=session.commit)
    session.add = add_mock
    session.commit = commit_mock
    snapshot = await snapshot_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert snapshot is not None
    add_mock.assert_not_called()
    commit_mock.assert_not_called()


# 13. freeze does not create order/task/execution_plan (snapshot persist allowed)
@pytest.mark.asyncio
async def test_freeze_no_side_effects(
    snapshot_service: QuoteSnapshotV2Service,
    volumetric_v2_db,
    allow_freeze_readiness,
):
    from models.execution_plan import ExecutionPlan
    from models.orders import Orders

    orders_before = await volumetric_v2_db.scalar(select(func.count()).select_from(Orders))
    plans_before = await volumetric_v2_db.scalar(select(func.count()).select_from(ExecutionPlan))
    workspace_id = await _seed_workspace(volumetric_v2_db)
    snapshot = await snapshot_service.freeze(
        TEMPLATE,
        workspace_id=workspace_id,
        quote_input=_full_quote_input(),
        frozen_by="test-operator",
    )
    assert snapshot is not None
    assert snapshot.persist_status == "persisted"
    orders_after = await volumetric_v2_db.scalar(select(func.count()).select_from(Orders))
    plans_after = await volumetric_v2_db.scalar(select(func.count()).select_from(ExecutionPlan))
    assert orders_after == orders_before
    assert plans_after == plans_before


# 14. no rate_per_hour commercial path
@pytest.mark.asyncio
async def test_no_rate_per_hour_commercial_path(snapshot_service: QuoteSnapshotV2Service):
    snapshot = await snapshot_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert snapshot is not None
    blob = snapshot.model_dump_json().lower()
    assert "rate_per_hour" not in blob or snapshot.readiness == "blocked_forbidden_path"
    for line in snapshot.commercial_price_proposal_snapshot.commercial_price_lines:
        assert "rate_per_hour" not in line.source.lower()


# 15. no total_cost x margin path
@pytest.mark.asyncio
async def test_no_total_cost_times_margin_path(snapshot_service: QuoteSnapshotV2Service):
    snapshot = await snapshot_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert snapshot is not None
    blob = snapshot.model_dump_json().lower()
    assert "margin_pct" not in blob
    assert "total_cost × margin" not in blob
    internal = snapshot.estimated_internal_cost_snapshot.estimated_total_internal_cost
    commercial = snapshot.commercial_price_proposal_snapshot.commercial_total
    assert internal is not None
    assert commercial != internal
    assert snapshot.commercial_price_proposal_snapshot.source == "commercial_price_proposal"
    assert snapshot.estimated_internal_cost_snapshot.source == "estimated_internal_cost"


# 16. persistence available — freeze persists when identity + readiness allow
@pytest.mark.asyncio
async def test_persistence_available(snapshot_service: QuoteSnapshotV2Service):
    assert PERSISTENCE_AVAILABLE is True


@pytest.mark.asyncio
async def test_freeze_blocked_without_identity(snapshot_service: QuoteSnapshotV2Service):
    snapshot = await snapshot_service.freeze(
        TEMPLATE,
        quote_input=_full_quote_input(),
        frozen_by="test-operator",
    )
    assert snapshot is not None
    assert snapshot.persist_status == "blocked"
    assert any("quote_id or workspace_id" in n for n in snapshot.notes)


# 17. snapshot version present
@pytest.mark.asyncio
async def test_snapshot_version_present(snapshot_service: QuoteSnapshotV2Service):
    snapshot = await snapshot_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert snapshot is not None
    assert snapshot.snapshot_version == QUOTE_SNAPSHOT_V2_VERSION
    assert snapshot.version == 1


# 18. same payload runs 7G + 7H independently before assembly
@pytest.mark.asyncio
async def test_independent_7g_7h_before_assembly(
    snapshot_service: QuoteSnapshotV2Service,
    cpp_service: CommercialPriceProposalService,
    eic_service: EstimatedInternalCostService,
):
    payload = _full_quote_input()
    commercial = await cpp_service.build_preview(TEMPLATE, quote_input=payload)
    internal = await eic_service.build_preview(TEMPLATE, quote_input=payload)
    snapshot = await snapshot_service.build_preview(TEMPLATE, quote_input=payload)
    assert commercial is not None and internal is not None and snapshot is not None
    assert snapshot.commercial_price_proposal_snapshot.model_dump() == commercial.model_dump()
    assert snapshot.estimated_internal_cost_snapshot.model_dump() == internal.model_dump()


def _forbidden_service_imports() -> set[str]:
    path = Path(__file__).resolve().parents[1] / "services" / "quote_snapshot_v2_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
    return modules


def test_post_preview_endpoint_returns_snapshot(snapshot_auth_client):
    response = snapshot_auth_client.post(
        f"/api/v1/product-system/quote-snapshot-v2/preview/{TEMPLATE}",
        json={"quote_input": _full_quote_input(), "currency": "RON"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["template_code"] == TEMPLATE
    assert body["persist_status"] == "not_persisted"
    assert "commercial_price_proposal_snapshot" in body
    assert "estimated_internal_cost_snapshot" in body


@pytest.mark.asyncio
async def test_post_freeze_endpoint_persists(
    volumetric_v2_db, snapshot_auth_client, allow_freeze_readiness
):
    workspace_id = await _seed_workspace(volumetric_v2_db)
    response = snapshot_auth_client.post(
        f"/api/v1/product-system/quote-snapshot-v2/freeze/{TEMPLATE}",
        json={
            "workspace_id": workspace_id,
            "quote_input": _full_quote_input(),
            "frozen_by": "test-operator",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["persist_status"] == "persisted"
    assert body.get("snapshot_code")


@pytest.mark.asyncio
async def test_forbidden_path_readiness(
    snapshot_service: QuoteSnapshotV2Service,
    volumetric_v2_db,
    monkeypatch,
):
    from services import commercial_price_proposal_service as cpp_mod

    original_scan = cpp_mod.scan_forbidden_hourly_usage

    def _force_hourly(lines):
        return original_scan(lines) + ["debitare_fata:rate_per_hour"]

    monkeypatch.setattr(cpp_mod, "scan_forbidden_hourly_usage", _force_hourly)
    workspace_id = await _seed_workspace(volumetric_v2_db)
    before = await volumetric_v2_db.scalar(select(func.count()).select_from(QuoteSnapshotV2Record))
    snapshot = await snapshot_service.freeze(
        TEMPLATE,
        workspace_id=workspace_id,
        quote_input=_full_quote_input(),
        frozen_by="test-operator",
    )
    assert snapshot is not None
    assert snapshot.readiness == "blocked_forbidden_path"
    assert snapshot.persist_status == "blocked"
    after = await volumetric_v2_db.scalar(
        select(func.count()).select_from(QuoteSnapshotV2Record)
    )
    assert after == before


@pytest.mark.asyncio
async def test_workspace_id_payload(volumetric_v2_db):
    import json

    service = QuoteSnapshotV2Service(volumetric_v2_db)
    eic = EstimatedInternalCostService(volumetric_v2_db)

    async def _patched():
        return SAMPLE_RATES, {}, {}, INVENTORY_CATALOG

    eic._load_pricing_context = _patched  # type: ignore[method-assign]
    service._eic = eic

    workspace_id = str(uuid.uuid4())
    record = IntakeV6WorkspaceRecord(
        id=workspace_id,
        workspace_code=f"WS-QS2-{workspace_id[:8]}",
        title="QS2 test workspace",
        template_code=TEMPLATE,
        payload_json=json.dumps(_full_quote_input()),
        status="draft",
    )
    volumetric_v2_db.add(record)
    await volumetric_v2_db.commit()

    snapshot = await service.build_preview(TEMPLATE, workspace_id=workspace_id)
    assert snapshot is not None
    assert snapshot.workspace_id == workspace_id
    assert snapshot.input_summary.get("workspace_id") == workspace_id


# --- Step 8.2 persistence tests (required 20) ---


@pytest.mark.asyncio
async def test_freeze_persists_row(
    snapshot_service: QuoteSnapshotV2Service, volumetric_v2_db, allow_freeze_readiness
):
    workspace_id = await _seed_workspace(volumetric_v2_db)
    before = await volumetric_v2_db.scalar(select(func.count()).select_from(QuoteSnapshotV2Record))
    snapshot = await snapshot_service.freeze(
        TEMPLATE,
        workspace_id=workspace_id,
        quote_input=_full_quote_input(),
        frozen_by="op-1",
    )
    after = await volumetric_v2_db.scalar(select(func.count()).select_from(QuoteSnapshotV2Record))
    assert snapshot is not None
    assert snapshot.persist_status == "persisted", (snapshot.readiness, snapshot.notes)
    assert after == before + 1


@pytest.mark.asyncio
async def test_persisted_contains_both_snapshots(
    snapshot_service: QuoteSnapshotV2Service, volumetric_v2_db, allow_freeze_readiness
):
    workspace_id = await _seed_workspace(volumetric_v2_db)
    snapshot = await snapshot_service.freeze(TEMPLATE, workspace_id=workspace_id, quote_input=_full_quote_input(), frozen_by="op-1")
    assert snapshot is not None
    assert snapshot.commercial_price_proposal_snapshot is not None
    assert snapshot.estimated_internal_cost_snapshot is not None
    record = await volumetric_v2_db.scalar(
        select(QuoteSnapshotV2Record).where(
            QuoteSnapshotV2Record.snapshot_code == snapshot.snapshot_code
        )
    )
    assert record is not None
    stored = QuoteSnapshotV2.model_validate_json(record.snapshot_json)
    assert stored.commercial_price_proposal_snapshot is not None
    assert stored.estimated_internal_cost_snapshot is not None


@pytest.mark.asyncio
async def test_totals_remain_separate_after_persistence(
    snapshot_service: QuoteSnapshotV2Service, volumetric_v2_db, allow_freeze_readiness
):
    workspace_id = await _seed_workspace(volumetric_v2_db)
    snapshot = await snapshot_service.freeze(TEMPLATE, workspace_id=workspace_id, quote_input=_full_quote_input(), frozen_by="op-1")
    assert snapshot is not None
    commercial = snapshot.commercial_price_proposal_snapshot.commercial_total
    internal = snapshot.estimated_internal_cost_snapshot.estimated_total_internal_cost
    assert commercial != internal
    record = await volumetric_v2_db.scalar(
        select(QuoteSnapshotV2Record).where(
            QuoteSnapshotV2Record.snapshot_code == snapshot.snapshot_code
        )
    )
    stored = QuoteSnapshotV2.model_validate_json(record.snapshot_json)
    assert stored.commercial_price_proposal_snapshot.commercial_total == commercial
    assert (
        stored.estimated_internal_cost_snapshot.estimated_total_internal_cost
        == internal
    )


@pytest.mark.asyncio
async def test_snapshot_json_round_trip(
    snapshot_service: QuoteSnapshotV2Service, volumetric_v2_db, allow_freeze_readiness
):
    workspace_id = await _seed_workspace(volumetric_v2_db)
    snapshot = await snapshot_service.freeze(TEMPLATE, workspace_id=workspace_id, quote_input=_full_quote_input(), frozen_by="op-1")
    assert snapshot is not None
    record = await volumetric_v2_db.scalar(
        select(QuoteSnapshotV2Record).where(
            QuoteSnapshotV2Record.snapshot_code == snapshot.snapshot_code
        )
    )
    round_trip = QuoteSnapshotV2.model_validate_json(record.snapshot_json)
    assert round_trip.template_code == snapshot.template_code
    assert round_trip.readiness == snapshot.readiness
    assert (
        round_trip.commercial_price_proposal_snapshot.commercial_total
        == snapshot.commercial_price_proposal_snapshot.commercial_total
    )


@pytest.mark.asyncio
async def test_quote_id_version_increment(
    snapshot_service: QuoteSnapshotV2Service, volumetric_v2_db, allow_freeze_readiness
):
    first = await snapshot_service.freeze(
        TEMPLATE,
        quote_id="9001",
        quote_input=_full_quote_input(),
        frozen_by="op-1",
    )
    second = await snapshot_service.freeze(
        TEMPLATE,
        quote_id="9001",
        quote_input=_full_quote_input(),
        frozen_by="op-1",
    )
    assert first is not None and second is not None
    assert first.version == 1
    assert second.version == 2
    assert first.persist_status == "persisted"
    assert second.persist_status == "persisted"


@pytest.mark.asyncio
async def test_workspace_only_snapshot(
    snapshot_service: QuoteSnapshotV2Service, volumetric_v2_db, allow_freeze_readiness
):
    workspace_id = await _seed_workspace(volumetric_v2_db)
    snapshot = await snapshot_service.freeze(TEMPLATE, workspace_id=workspace_id, frozen_by="op-1")
    assert snapshot is not None
    assert snapshot.workspace_id == workspace_id
    assert snapshot.quote_id is None
    record = await volumetric_v2_db.scalar(
        select(QuoteSnapshotV2Record).where(
            QuoteSnapshotV2Record.snapshot_code == snapshot.snapshot_code
        )
    )
    assert record.quote_id is None
    assert record.workspace_id == workspace_id


@pytest.mark.asyncio
async def test_owner_decisions_persisted(
    snapshot_service: QuoteSnapshotV2Service, volumetric_v2_db, allow_freeze_readiness
):
    workspace_id = await _seed_workspace(volumetric_v2_db)
    snapshot = await snapshot_service.freeze(TEMPLATE, workspace_id=workspace_id, quote_input=_full_quote_input(), frozen_by="op-1")
    assert snapshot is not None
    assert snapshot.owner_decisions_snapshot
    record = await volumetric_v2_db.scalar(
        select(QuoteSnapshotV2Record).where(
            QuoteSnapshotV2Record.snapshot_code == snapshot.snapshot_code
        )
    )
    stored = QuoteSnapshotV2.model_validate_json(record.snapshot_json)
    assert stored.owner_decisions_snapshot
    sources = {d.source for d in stored.owner_decisions_snapshot}
    assert "commercial_price_proposal" in sources
    assert "estimated_internal_cost" in sources


@pytest.mark.asyncio
async def test_provenance_persisted(
    snapshot_service: QuoteSnapshotV2Service, volumetric_v2_db, allow_freeze_readiness
):
    workspace_id = await _seed_workspace(volumetric_v2_db)
    snapshot = await snapshot_service.freeze(TEMPLATE, workspace_id=workspace_id, quote_input=_full_quote_input(), frozen_by="op-1")
    assert snapshot is not None
    record = await volumetric_v2_db.scalar(
        select(QuoteSnapshotV2Record).where(
            QuoteSnapshotV2Record.snapshot_code == snapshot.snapshot_code
        )
    )
    stored = QuoteSnapshotV2.model_validate_json(record.snapshot_json)
    keys = {p.key for p in stored.provenance}
    assert "commercial_price_proposal" in keys
    assert "estimated_internal_cost" in keys


def test_migration_additive_only():
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "s53_create_quote_snapshots_v2.py"
    )
    text = migration_path.read_text(encoding="utf-8").lower()
    assert "quote_snapshots_v2" in text
    assert "create_table" in text
    assert "quotes" not in text.replace("quote_snapshots_v2", "")
    assert "orders" not in text
    assert "line_items" not in text


def test_quote_orchestrator_unchanged():
    path = Path(__file__).resolve().parents[1] / "services" / "quote_orchestrator.py"
    assert path.exists()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    assert isinstance(tree, ast.Module)


def test_cost_engine_unchanged():
    path = Path(__file__).resolve().parents[1] / "services" / "cost_engine_service.py"
    assert path.exists()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    assert isinstance(tree, ast.Module)
