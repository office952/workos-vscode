"""Sold-scope snapshot closure — freeze compiled ActiveScopeResult (Letters Slice 1)."""

from __future__ import annotations

import copy
import json

import pytest
import pytest_asyncio

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from schemas.active_scope import ActiveScopeResult
from schemas.active_scope_snapshot import ACTIVE_SCOPE_SNAPSHOT_VERSION, QuoteSnapshotActiveScope
from schemas.quote_snapshot_v2 import QuoteSnapshotV2
from services.active_scope_resolver_service import compile_active_scope
from services.active_scope_semantic_compare import (
    ActiveScopePreviewFreezeMismatch,
    assert_preview_freeze_semantic_match,
    compare_active_scope_semantics,
)
from services.execution_sold_scope_reader_service import (
    ENRICHED_SCOPE,
    LEGACY_SCOPE_FALLBACK,
    include_operation_for_sold_scope,
    include_task_rule_for_sold_scope,
    read_execution_sold_scope,
)
from services.order_snapshot_v2_convert_service import _component_scope_fields_from_quote
from services.quote_snapshot_component_scope_service import build_frozen_component_scope
from tests.execution_sold_scope_fixtures import offer_scope, snapshot_with_scope, sold_scope_dossier_aggregate
from tests.test_quote_snapshot_v2 import TEMPLATE, _full_quote_input, _seed_workspace
from tests.test_quote_snapshot_v2_accept_gate import _commercial_preview, _internal_preview

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

ROOT = TEMPLATE


def _with_offer_scope(base: dict, *, mode: str, sold: list[str]) -> dict:
    out = copy.deepcopy(base)
    out["offer_scope"] = {
        "contract_version": "offer_scope_contract/v1",
        "mode": mode,
        "sold_modules": sold,
    }
    return out


def _rule(name: str):
    return next(
        rule
        for rule in sold_scope_dossier_aggregate().task_contract.task_rules
        if rule.task_name == name
    )


def _op(code: str):
    return next(op for op in sold_scope_dossier_aggregate().operations if op.operation_code == code)


@pytest.mark.asyncio
async def test_return_cant_freezes_enriched_active_scope(volumetric_v2_db) -> None:
    workspace_id = await _seed_workspace(volumetric_v2_db)
    qi = _with_offer_scope(_full_quote_input(), mode="component_subset", sold=["RETURN-CANT"])
    scope = await build_frozen_component_scope(
        volumetric_v2_db,
        template_code=ROOT,
        workspace_id=workspace_id,
        quote_input=qi,
    )
    assert scope is not None
    assert scope.active_scope_snapshot is not None
    snap = scope.active_scope_snapshot
    assert snap.active_scope_snapshot_version == ACTIVE_SCOPE_SNAPSHOT_VERSION
    assert snap.compatibility_mode == "enriched"
    assert snap.source_workspace_id == workspace_id
    assert snap.source_template_code == ROOT
    compiled = snap.compiled
    assert compiled.sold_module_codes == ["RETURN-CANT"]
    assert "modelare_cant" in compiled.active_runtime_modules
    assert "geometry_svg" in compiled.active_runtime_modules
    assert "debitare_fata" in compiled.inactive_runtime_modules
    assert "debitare_spate" in compiled.inactive_runtime_modules
    assert "sistem_led" in compiled.inactive_runtime_modules
    assert compiled.commercial_scope_modules == ["modelare_cant"]
    assert "modelare_cant" in compiled.execution_scope_modules
    assert "geometry_svg" in compiled.execution_scope_modules
    assert "return_face_bonding" in compiled.composition_excluded_operations
    assert scope.offer_scope_snapshot.resolved_runtime_sold_modules == ["modelare_cant"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "sold",
    [["FACE"], ["BACK"], ["LIGHTING"], ["ELECTRICAL"]],
)
async def test_subset_freezes_exact_sold_module(volumetric_v2_db, sold: list[str]) -> None:
    workspace_id = await _seed_workspace(volumetric_v2_db)
    qi = _with_offer_scope(_full_quote_input(), mode="component_subset", sold=sold)
    scope = await build_frozen_component_scope(
        volumetric_v2_db,
        template_code=ROOT,
        workspace_id=workspace_id,
        quote_input=qi,
    )
    assert scope is not None
    assert scope.active_scope_snapshot is not None
    assert scope.active_scope_snapshot.compiled.sold_module_codes == sold
    assert scope.offer_scope_snapshot.sold_modules == sold
    assert scope.active_scope_snapshot.compiled.errors == []


@pytest.mark.asyncio
async def test_full_product_enriched_legacy_flag(volumetric_v2_db) -> None:
    workspace_id = await _seed_workspace(volumetric_v2_db)
    qi = _with_offer_scope(_full_quote_input(), mode="full_product", sold=[])
    scope = await build_frozen_component_scope(
        volumetric_v2_db,
        template_code=ROOT,
        workspace_id=workspace_id,
        quote_input=qi,
    )
    assert scope is not None
    assert scope.active_scope_snapshot is not None
    assert scope.active_scope_snapshot.compiled.use_legacy_full_product is True


def test_semantic_compare_ignores_order_and_null_lists() -> None:
    a = ActiveScopeResult(
        template_code=ROOT,
        mode="component_subset",
        use_legacy_full_product=False,
        sold_module_codes=["RETURN-CANT"],
        active_runtime_modules=["geometry_svg", "modelare_cant"],
        inactive_runtime_modules=["debitare_fata"],
        commercial_scope_modules=["modelare_cant"],
        execution_scope_modules=["geometry_svg", "modelare_cant"],
        composition_excluded_operations=["return_face_bonding"],
    )
    b = ActiveScopeResult(
        template_code=ROOT,
        mode="component_subset",
        use_legacy_full_product=False,
        sold_module_codes=["RETURN-CANT"],
        active_runtime_modules=["modelare_cant", "geometry_svg"],
        inactive_runtime_modules=["debitare_fata"],
        commercial_scope_modules=["modelare_cant"],
        execution_scope_modules=["modelare_cant", "geometry_svg"],
        composition_excluded_operations=["return_face_bonding"],
        warnings=[],
    )
    assert compare_active_scope_semantics(a, b) == []
    assert_preview_freeze_semantic_match(a, b)


def test_semantic_compare_reports_exact_field() -> None:
    a = compile_active_scope(
        template_code=ROOT,
        quote_input={"offer_scope": {"mode": "component_subset", "sold_modules": ["FACE"]}},
    )
    b = compile_active_scope(
        template_code=ROOT,
        quote_input={"offer_scope": {"mode": "component_subset", "sold_modules": ["BACK"]}},
    )
    diffs = compare_active_scope_semantics(a, b)
    assert diffs
    assert any(d.startswith("sold_module_codes:") for d in diffs)
    with pytest.raises(ActiveScopePreviewFreezeMismatch) as exc:
        assert_preview_freeze_semantic_match(a, b)
    assert "sold_module_codes" in str(exc.value)


def test_order_passthrough_copies_active_scope_snapshot() -> None:
    compiled = compile_active_scope(
        template_code=ROOT,
        quote_input={
            "offer_scope": {"mode": "component_subset", "sold_modules": ["RETURN-CANT"]},
        },
    )
    active = QuoteSnapshotActiveScope(
        source_template_code=ROOT,
        source_workspace_id="ws-frozen-1",
        compiled=compiled,
    )
    quote = QuoteSnapshotV2(
        template_code=ROOT,
        workspace_id="ws-frozen-1",
        offer_scope_snapshot=offer_scope(
            sold=["RETURN-CANT"],
            runtime=["modelare_cant"],
        ),
        active_scope_snapshot=active,
        commercial_price_proposal_snapshot=_commercial_preview(total=100.0),
        estimated_internal_cost_snapshot=_internal_preview(total=40.0),
    )
    fields = _component_scope_fields_from_quote(quote)
    assert fields["active_scope_snapshot"] is active
    assert fields["active_scope_snapshot"].source_workspace_id == "ws-frozen-1"


def test_exec_enriched_excludes_bonding_without_legacy_hardcode() -> None:
    compiled = compile_active_scope(
        template_code=ROOT,
        quote_input={
            "offer_scope": {"mode": "component_subset", "sold_modules": ["RETURN-CANT"]},
        },
    )
    active = QuoteSnapshotActiveScope(
        source_template_code=ROOT,
        compiled=compiled,
    )
    snap = snapshot_with_scope(
        offer_scope=offer_scope(sold=["RETURN-CANT"], runtime=["modelare_cant"]),
    )
    snap = snap.model_copy(update={"active_scope_snapshot": active})
    ctx = read_execution_sold_scope(snap)
    assert ctx.scope_compatibility_mode == ENRICHED_SCOPE
    assert "return_face_bonding" in ctx.composition_excluded_operations
    assert "geometry_svg" in ctx.sold_runtime_modules
    assert not include_task_rule_for_sold_scope(_rule("return_face_bonding"), ctx=ctx)
    assert not include_operation_for_sold_scope(_op("return_face_bonding"), ctx=ctx)
    assert include_task_rule_for_sold_scope(_rule("return_profile_forming"), ctx=ctx)


def test_exec_legacy_thin_snapshot_still_excludes_bonding() -> None:
    ctx = read_execution_sold_scope(
        snapshot_with_scope(
            offer_scope=offer_scope(sold=["RETURN-CANT"], runtime=["modelare_cant"]),
        )
    )
    assert ctx.scope_compatibility_mode == LEGACY_SCOPE_FALLBACK
    assert not include_task_rule_for_sold_scope(_rule("return_face_bonding"), ctx=ctx)


@pytest.mark.asyncio
async def test_acm_template_does_not_stamp_letters_active_scope(volumetric_v2_db) -> None:
    """ACM freeze must not receive Letters Slice 1 active_scope_snapshot."""
    from services.quote_snapshot_component_scope_service import LETTERS_ACTIVE_SCOPE_TEMPLATE

    assert LETTERS_ACTIVE_SCOPE_TEMPLATE == ROOT
    # Direct unit: non-Letters template skips enrich
    from services.quote_snapshot_component_scope_service import _build_active_scope_snapshot

    snap = _build_active_scope_snapshot(
        template_code="TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
        workspace_id="ws-acm",
        workspace_payload={},
        quote_input=_full_quote_input(),
    )
    assert snap is None


def test_exec_unknown_active_scope_version_blocks() -> None:
    from services.execution_sold_scope_reader_service import UNKNOWN_ACTIVE_SCOPE_SNAPSHOT_VERSION

    compiled = compile_active_scope(
        template_code=ROOT,
        quote_input={
            "offer_scope": {"mode": "component_subset", "sold_modules": ["RETURN-CANT"]},
        },
    )
    active = QuoteSnapshotActiveScope(
        active_scope_snapshot_version="active_scope_snapshot/v999",
        source_template_code=ROOT,
        compiled=compiled,
    )
    snap = snapshot_with_scope(
        offer_scope=offer_scope(sold=["RETURN-CANT"], runtime=["modelare_cant"]),
    ).model_copy(update={"active_scope_snapshot": active})
    ctx = read_execution_sold_scope(snap)
    assert ctx.block_preview is True
    assert ctx.block_reason == UNKNOWN_ACTIVE_SCOPE_SNAPSHOT_VERSION


@pytest.mark.asyncio
async def test_intent_mismatch_workspace_vs_quote_input_fails_closed(volumetric_v2_db) -> None:
    workspace_id = await _seed_workspace(volumetric_v2_db)
    record = await volumetric_v2_db.get(IntakeV6WorkspaceRecord, workspace_id)
    assert record is not None
    payload = json.loads(record.payload_json)
    payload["offer_scope"] = {
        "contract_version": "offer_scope_contract/v1",
        "mode": "component_subset",
        "sold_modules": ["FACE"],
    }
    record.payload_json = json.dumps(payload)
    await volumetric_v2_db.commit()

    qi = _with_offer_scope(_full_quote_input(), mode="component_subset", sold=["RETURN-CANT"])
    scope = await build_frozen_component_scope(
        volumetric_v2_db,
        template_code=ROOT,
        workspace_id=workspace_id,
        quote_input=qi,
    )
    assert scope is not None
    assert scope.active_scope_snapshot is not None
    assert any(
        "ACTIVE_SCOPE_INTENT_SOURCE_MISMATCH" in e
        for e in scope.active_scope_snapshot.compiled.errors
    )
    assert "ACTIVE_SCOPE_INTENT_SOURCE_MISMATCH" in (
        scope.offer_scope_snapshot.validation_errors or []
    )


@pytest.mark.asyncio
async def test_freeze_survives_workspace_payload_mutation(volumetric_v2_db) -> None:
    """After freeze, workspace edits must not change frozen compiled scope."""
    workspace_id = await _seed_workspace(volumetric_v2_db)
    qi = _with_offer_scope(_full_quote_input(), mode="component_subset", sold=["RETURN-CANT"])
    scope = await build_frozen_component_scope(
        volumetric_v2_db,
        template_code=ROOT,
        workspace_id=workspace_id,
        quote_input=qi,
    )
    assert scope is not None
    frozen = scope.active_scope_snapshot
    assert frozen is not None

    record = await volumetric_v2_db.get(IntakeV6WorkspaceRecord, workspace_id)
    assert record is not None
    payload = json.loads(record.payload_json)
    payload["offer_scope"] = {
        "contract_version": "offer_scope_contract/v1",
        "mode": "component_subset",
        "sold_modules": ["FACE"],
    }
    record.payload_json = json.dumps(payload)
    await volumetric_v2_db.commit()

    # Frozen blob unchanged — Exec reads freeze, not workspace
    order_snap = snapshot_with_scope(
        offer_scope=scope.offer_scope_snapshot,
    ).model_copy(update={"active_scope_snapshot": frozen})
    ctx = read_execution_sold_scope(order_snap)
    assert ctx.canonical_sold_modules == frozenset({"RETURN-CANT"})
    assert frozen.compiled.sold_module_codes == ["RETURN-CANT"]
