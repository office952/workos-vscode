"""Unit tests for execution sold scope reader — frozen OrderSnapshotV2 scope only."""

from __future__ import annotations

import pytest

from services.execution_sold_scope_reader_service import (
    BLOCKED_MISSING_SOLD_SCOPE,
    effective_runtime_module_for_task_rule,
    include_operation_for_sold_scope,
    include_task_rule_for_sold_scope,
    is_linked_segment_task_rule,
    is_vector_prep_task_rule,
    read_execution_sold_scope,
)
from tests.execution_sold_scope_fixtures import (
    offer_scope,
    snapshot_with_scope,
    sold_scope_dossier_aggregate,
)
from tests.test_execution_plan_v2_preview import _seed_v2_order_with_snapshot


def _rule(name: str):
    return next(
        rule
        for rule in sold_scope_dossier_aggregate().task_contract.task_rules
        if rule.task_name == name
    )


def _op(code: str):
    return next(op for op in sold_scope_dossier_aggregate().operations if op.operation_code == code)


# ---------------------------------------------------------------------------
# Reader context
# ---------------------------------------------------------------------------


def test_read_legacy_absent_scope_disables_filter():
    ctx = read_execution_sold_scope(snapshot_with_scope(offer_scope=None))
    assert ctx.filter_enabled is False
    assert ctx.linked_logo_tasks_allowed is True
    assert ctx.block_preview is False


def test_read_explicit_full_product_disables_filter():
    ctx = read_execution_sold_scope(
        snapshot_with_scope(
            offer_scope=offer_scope(mode="full_product", use_legacy=True, runtime=[]),
        )
    )
    assert ctx.filter_enabled is False
    assert ctx.linked_logo_tasks_allowed is True


def test_read_component_subset_enables_filter_with_runtime_modules():
    ctx = read_execution_sold_scope(
        snapshot_with_scope(
            offer_scope=offer_scope(runtime=["debitare_fata"]),
        )
    )
    assert ctx.filter_enabled is True
    assert ctx.sold_runtime_modules == frozenset({"debitare_fata"})
    assert ctx.linked_logo_tasks_allowed is False
    assert ctx.block_preview is False


def test_read_invalid_subset_blocks_preview():
    ctx = read_execution_sold_scope(
        snapshot_with_scope(
            offer_scope=offer_scope(runtime=[]),
        )
    )
    assert ctx.filter_enabled is True
    assert ctx.block_preview is True
    assert ctx.block_reason == BLOCKED_MISSING_SOLD_SCOPE


# ---------------------------------------------------------------------------
# Task rule inclusion
# ---------------------------------------------------------------------------


def test_vector_prep_always_included_in_subset():
    ctx = read_execution_sold_scope(
        snapshot_with_scope(offer_scope=offer_scope(runtime=["debitare_spate"]))
    )
    assert include_task_rule_for_sold_scope(_rule("vector_prep"), ctx=ctx) is True
    assert is_vector_prep_task_rule(_rule("vector_prep")) is True


def test_return_face_bonding_alias_maps_to_return_cant():
    bonding = _rule("return_face_bonding")
    assert effective_runtime_module_for_task_rule(bonding) == "modelare_cant"
    ctx = read_execution_sold_scope(
        snapshot_with_scope(offer_scope=offer_scope(runtime=["modelare_cant"]))
    )
    assert include_task_rule_for_sold_scope(bonding, ctx=ctx) is True
    ctx_face = read_execution_sold_scope(
        snapshot_with_scope(offer_scope=offer_scope(runtime=["debitare_fata"]))
    )
    assert include_task_rule_for_sold_scope(bonding, ctx=ctx_face) is False


def test_face_only_includes_face_tasks_and_vector_prep():
    ctx = read_execution_sold_scope(
        snapshot_with_scope(offer_scope=offer_scope(runtime=["debitare_fata"]))
    )
    assert include_task_rule_for_sold_scope(_rule("cnc_face_cut"), ctx=ctx)
    assert include_task_rule_for_sold_scope(_rule("vector_prep"), ctx=ctx)
    assert not include_task_rule_for_sold_scope(_rule("vinyl_application"), ctx=ctx)
    assert not include_task_rule_for_sold_scope(_rule("return_profile_forming"), ctx=ctx)
    assert not include_task_rule_for_sold_scope(_rule("cnc_back_cut"), ctx=ctx)
    assert not include_task_rule_for_sold_scope(_rule("led_installation"), ctx=ctx)
    assert not include_task_rule_for_sold_scope(_rule("painting"), ctx=ctx)
    assert not include_task_rule_for_sold_scope(_rule("mounting_template"), ctx=ctx)


def test_return_cant_only_includes_cant_tasks_and_alias():
    ctx = read_execution_sold_scope(
        snapshot_with_scope(offer_scope=offer_scope(runtime=["modelare_cant"]))
    )
    assert include_task_rule_for_sold_scope(_rule("return_profile_forming"), ctx=ctx)
    assert include_task_rule_for_sold_scope(_rule("return_face_bonding"), ctx=ctx)
    assert include_task_rule_for_sold_scope(_rule("vector_prep"), ctx=ctx)
    assert not include_task_rule_for_sold_scope(_rule("cnc_face_cut"), ctx=ctx)
    assert not include_task_rule_for_sold_scope(_rule("cnc_back_cut"), ctx=ctx)


def test_back_only_includes_back_tasks():
    ctx = read_execution_sold_scope(
        snapshot_with_scope(offer_scope=offer_scope(runtime=["debitare_spate"]))
    )
    assert include_task_rule_for_sold_scope(_rule("cnc_back_cut"), ctx=ctx)
    assert include_task_rule_for_sold_scope(_rule("vector_prep"), ctx=ctx)
    assert not include_task_rule_for_sold_scope(_rule("cnc_face_cut"), ctx=ctx)


def test_face_plus_return_cant_union():
    ctx = read_execution_sold_scope(
        snapshot_with_scope(
            offer_scope=offer_scope(runtime=["debitare_fata", "modelare_cant"])
        )
    )
    included = {
        rule.task_name
        for rule in sold_scope_dossier_aggregate().task_contract.task_rules
        if include_task_rule_for_sold_scope(rule, ctx=ctx)
    }
    assert "cnc_face_cut" in included
    assert "return_profile_forming" in included
    assert "return_face_bonding" in included
    assert "vector_prep" in included
    assert "vinyl_application" not in included
    assert "cnc_back_cut" not in included
    assert "led_installation" not in included


def test_unsold_modules_excluded():
    ctx = read_execution_sold_scope(
        snapshot_with_scope(offer_scope=offer_scope(runtime=["debitare_fata"]))
    )
    assert not include_task_rule_for_sold_scope(_rule("led_installation"), ctx=ctx)
    assert not include_task_rule_for_sold_scope(_rule("electrical_wiring"), ctx=ctx)
    assert not include_task_rule_for_sold_scope(_rule("painting"), ctx=ctx)
    assert not include_task_rule_for_sold_scope(_rule("mounting_template"), ctx=ctx)


def test_linked_logo_included_in_legacy():
    ctx = read_execution_sold_scope(snapshot_with_scope(offer_scope=None))
    assert is_linked_segment_task_rule(_rule("linked_logo_apply"))
    assert include_task_rule_for_sold_scope(_rule("linked_logo_apply"), ctx=ctx)


def test_linked_logo_excluded_in_subset():
    ctx = read_execution_sold_scope(
        snapshot_with_scope(offer_scope=offer_scope(runtime=["debitare_fata"]))
    )
    assert not include_task_rule_for_sold_scope(_rule("linked_logo_apply"), ctx=ctx)


# ---------------------------------------------------------------------------
# Operation inclusion
# ---------------------------------------------------------------------------


def test_operation_filter_matches_task_scope():
    ctx = read_execution_sold_scope(
        snapshot_with_scope(offer_scope=offer_scope(runtime=["debitare_fata"]))
    )
    assert include_operation_for_sold_scope(_op("vector_prep"), ctx=ctx)
    assert include_operation_for_sold_scope(_op("face_cnc_cut"), ctx=ctx)
    assert not include_operation_for_sold_scope(_op("back_cut"), ctx=ctx)
    assert not include_operation_for_sold_scope(_op("logo_vinyl"), ctx=ctx)


def test_linked_logo_operation_included_in_legacy():
    ctx = read_execution_sold_scope(snapshot_with_scope(offer_scope=None))
    assert include_operation_for_sold_scope(_op("logo_vinyl"), ctx=ctx)


def test_return_face_bonding_operation_alias_in_return_cant():
    # Runtime-only freeze (no canonical sold list) keeps historical alias inclusion.
    ctx = read_execution_sold_scope(
        snapshot_with_scope(offer_scope=offer_scope(runtime=["modelare_cant"]))
    )
    assert include_operation_for_sold_scope(_op("return_face_bonding"), ctx=ctx)


def test_return_cant_canonical_sold_excludes_composition_bonding():
    """RETURN-CANT ONLY — face↔return bonding is composition-only, not sold alone."""
    ctx = read_execution_sold_scope(
        snapshot_with_scope(
            offer_scope=offer_scope(
                sold=["RETURN-CANT"],
                runtime=["modelare_cant"],
            )
        )
    )
    assert include_task_rule_for_sold_scope(_rule("return_profile_forming"), ctx=ctx)
    assert not include_task_rule_for_sold_scope(_rule("return_face_bonding"), ctx=ctx)
    assert not include_operation_for_sold_scope(_op("return_face_bonding"), ctx=ctx)


@pytest.mark.asyncio
async def test_no_resolver_rerun_during_preview(db_session, monkeypatch):
    """Preview must not call offer scope resolver."""
    called = {"resolver": False}

    def _resolver(*args, **kwargs):
        called["resolver"] = True
        raise AssertionError("resolve_offer_scope must not run during execution preview")

    monkeypatch.setattr("services.offer_scope_resolver_service.resolve_offer_scope", _resolver)

    from services.execution_plan_v2_preview_service import build_execution_plan_v2_preview

    snapshot = snapshot_with_scope(
        offer_scope=offer_scope(runtime=["debitare_fata"]),
    )
    order = await _seed_v2_order_with_snapshot(
        db_session,
        snapshot_v2_json=snapshot.model_dump_json(),
    )
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    assert called["resolver"] is False
    assert preview.status == "partial_missing_planning_minutes"


@pytest.mark.asyncio
async def test_no_aggregate_rebuild_during_preview(db_session, monkeypatch):
    called = {"aggregate": False}

    async def _build(*args, **kwargs):
        called["aggregate"] = True
        raise AssertionError("build_for_workspace must not run during execution preview")

    monkeypatch.setattr("services.product_aggregate_service.ProductAggregateService.build_for_workspace", _build)

    from services.execution_plan_v2_preview_service import build_execution_plan_v2_preview

    snapshot = snapshot_with_scope(
        offer_scope=offer_scope(runtime=["debitare_fata"]),
    )
    order = await _seed_v2_order_with_snapshot(
        db_session,
        snapshot_v2_json=snapshot.model_dump_json(),
    )
    preview = await build_execution_plan_v2_preview(db_session, order.id)
    assert called["aggregate"] is False
    assert preview.planned_tasks
