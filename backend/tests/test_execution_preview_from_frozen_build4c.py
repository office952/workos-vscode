"""Build 4C — Execution preview from frozen modular graph (no writes)."""

from __future__ import annotations

import ast
import copy
import inspect
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import func, select

from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from schemas.active_scope import ActiveScopeResult
from schemas.active_scope_snapshot import QuoteSnapshotActiveScope
from schemas.commercial_price_proposal import CommercialPriceLine, CommercialPriceProposalPreview
from schemas.estimated_internal_cost import EstimatedInternalCostPreview
from schemas.product_aggregate import (
    ProductAggregate,
    ProductAggregateMaterial,
    ProductAggregateOperation,
    ProductAggregateTaskContract,
    ProductAggregateTaskRule,
)
from schemas.product_definition import ProductDefinitionPreview, ProductDefinitionSourceContext
from schemas.quote_snapshot_v2 import QuoteSnapshotOfferScope, QuoteSnapshotV2
from services.execution_preview_from_frozen_graph_service import (
    build_execution_preview_from_frozen_snapshot,
)
from services.frozen_modular_graph_service import classify_order14_compatibility
from services.quote_snapshot_v2_service import QuoteSnapshotV2Service
from tests.test_quote_snapshot_v2 import TEMPLATE, _full_quote_input, _seed_workspace

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]


def _offer(*, mode: str, sold: list[str], use_legacy: bool | None = None) -> QuoteSnapshotOfferScope:
    legacy = use_legacy if use_legacy is not None else mode == "full_product"
    return QuoteSnapshotOfferScope(
        mode=mode,  # type: ignore[arg-type]
        sold_modules=sold,
        use_legacy=legacy,
        resolved_runtime_sold_modules=[] if legacy else sold,
    )


def _active(
    *,
    mode: str,
    sold: list[str],
    active: list[str],
    inactive: list[str],
    excl_ops: list[str] | None = None,
    excl_mats: list[str] | None = None,
    interface: bool | None = None,
    use_legacy: bool = False,
    errors: list[str] | None = None,
) -> QuoteSnapshotActiveScope:
    return QuoteSnapshotActiveScope(
        source_template_code=TEMPLATE,
        compiled=ActiveScopeResult(
            template_code=TEMPLATE,
            mode=mode,  # type: ignore[arg-type]
            use_legacy_full_product=use_legacy,
            sold_module_codes=sold,
            active_runtime_modules=[] if use_legacy else active,
            inactive_runtime_modules=[] if use_legacy else inactive,
            composition_excluded_operations=excl_ops or [],
            composition_excluded_materials=excl_mats or [],
            errors=list(errors or []),
            provenance={
                "interface_face_cant_active": bool(interface) if interface is not None else False,
            },
        ),
    )


def _aggregate(
    *,
    materials: list[str],
    operations: list[str],
    task_rules: list[tuple[str, str | None, str | None]],
) -> ProductAggregate:
    return ProductAggregate(
        template_code=TEMPLATE,
        template_id=1,
        materials=[
            ProductAggregateMaterial(
                material_code=code,
                component_ref="comp",
                mini_module_code="modelare_cant" if "ADEZIV" in code or "PROFIL" in code else "debitare_fata",
                provenance="dossier",
            )
            for code in materials
        ],
        operations=[
            ProductAggregateOperation(
                operation_code=code,
                component_ref="comp",
                mini_module_code="modelare_cant" if "bonding" in code.lower() or "FORMING" in code else "debitare_fata",
                provenance="dossier",
            )
            for code in operations
        ],
        task_contract=ProductAggregateTaskContract(
            task_rules=[
                ProductAggregateTaskRule(
                    task_name=name,
                    priced_operation=priced,
                    mini_module_code=owner,
                    sequence=i,
                    provenance="dossier",
                )
                for i, (name, priced, owner) in enumerate(task_rules)
            ]
        ),
    )


def _cpp(lines: list[tuple[str, float, float]]) -> CommercialPriceProposalPreview:
    return CommercialPriceProposalPreview(
        template_code=TEMPLATE,
        currency="RON",
        commercial_price_lines=[
            CommercialPriceLine(
                code=code,
                label=code,
                basis_type="ml",
                quantity=qty,
                unit="m",
                commercial_unit_price=price,
                subtotal=round(qty * price, 2),
                pricing_rule_code=code,
                source="test_fixture",
            )
            for code, qty, price in lines
        ],
        subtotal_commercial=sum(round(q * p, 2) for _, q, p in lines),
        commercial_total=sum(round(q * p, 2) for _, q, p in lines),
    )


def _snapshot(
    *,
    offer: QuoteSnapshotOfferScope,
    active: QuoteSnapshotActiveScope | None,
    aggregate: ProductAggregate,
    cpp: CommercialPriceProposalPreview | None = None,
) -> QuoteSnapshotV2:
    return QuoteSnapshotV2(
        template_code=TEMPLATE,
        offer_scope_snapshot=offer,
        active_scope_snapshot=active,
        product_definition_snapshot=ProductDefinitionPreview(
            template_code=TEMPLATE,
            source_context=ProductDefinitionSourceContext(template_code=TEMPLATE),
        ),
        product_aggregate_snapshot=aggregate,
        commercial_price_proposal_snapshot=cpp
        or _cpp([("RULE-FACE", 1.2, 10.0), ("RULE-CANT", 12.5, 3.0)]),
        estimated_internal_cost_snapshot=EstimatedInternalCostPreview(template_code=TEMPLATE),
        persist_status="not_persisted",
        frozen_at="2099-01-01T00:00:00Z",
        provenance=[],
    )


def _face_cant_snap() -> QuoteSnapshotV2:
    return _snapshot(
        offer=_offer(mode="component_subset", sold=["FACE", "RETURN-CANT"]),
        active=_active(
            mode="component_subset",
            sold=["FACE", "RETURN-CANT"],
            active=["debitare_fata", "modelare_cant"],
            inactive=["sistem_led"],
            interface=True,
        ),
        aggregate=_aggregate(
            materials=["MAT-ACP-FATA-LITERE", "MAT-PROFIL-LATERAL-LITERE", "MAT-ADEZIV-CANT-LITERE"],
            operations=["face_cutting", "RETURN_PROFILE_MACHINE_FORMING", "RETURN_PROFILE_FACE_BONDING"],
            task_rules=[
                ("Cut face", "face_cutting", "debitare_fata"),
                ("Form cant", "RETURN_PROFILE_MACHINE_FORMING", "modelare_cant"),
                ("Bond interface", "RETURN_PROFILE_FACE_BONDING", "modelare_cant"),
            ],
        ),
    )


def test_candidates_from_task_rules_not_all_operations():
    snap = _snapshot(
        offer=_offer(mode="component_subset", sold=["FACE"]),
        active=_active(
            mode="component_subset",
            sold=["FACE"],
            active=["debitare_fata"],
            inactive=["modelare_cant"],
            excl_ops=["RETURN_PROFILE_FACE_BONDING"],
            excl_mats=["MAT-ADEZIV-CANT-LITERE"],
            interface=False,
        ),
        aggregate=_aggregate(
            materials=["MAT-ACP-FATA-LITERE"],
            operations=["face_cutting", "info_only_op", "another_op"],
            task_rules=[("Cut face", "face_cutting", "debitare_fata")],
        ),
        cpp=_cpp([("RULE-FACE", 1.2, 10.0)]),
    )
    preview = build_execution_preview_from_frozen_snapshot(snap)
    assert preview.safety.no_write is True
    assert preview.safety.no_live_recompile is True
    assert preview.safety.no_materialization is True
    assert len(preview.task_candidates) == 1
    assert preview.task_candidates[0].source_operation_code == "face_cutting"
    assert preview.source.source_authority == "frozen_snapshot_v2"


def test_face_cant_bonding_candidate_and_adhesive_exactly_once():
    preview = build_execution_preview_from_frozen_snapshot(_face_cant_snap())
    assert preview.frozen_graph.compatibility.scenario == "face_cant"
    bonding = [
        c
        for c in preview.task_candidates
        if (c.source_operation_code and "bonding" in c.source_operation_code.lower())
        or "bond" in c.task_name.lower()
    ]
    assert len(bonding) == 1
    assert preview.frozen_graph.execution.adhesive_material_count == 1
    adhesive_reqs = [
        m for m in preview.material_requirements if "ADEZIV" in m.material_code.upper()
    ]
    assert len(adhesive_reqs) == 1
    assert adhesive_reqs[0].interface_provenance is True
    assert preview.dependency_graph.cycle_detected is False
    assert len(preview.dependency_graph.topological_order) == len(preview.task_candidates)


def test_face_only_no_cant_bonding_adhesive():
    snap = _snapshot(
        offer=_offer(mode="component_subset", sold=["FACE"]),
        active=_active(
            mode="component_subset",
            sold=["FACE"],
            active=["debitare_fata"],
            inactive=["modelare_cant", "sistem_led"],
            excl_ops=["RETURN_PROFILE_FACE_BONDING", "RETURN_PROFILE_MACHINE_FORMING"],
            excl_mats=["MAT-ADEZIV-CANT-LITERE"],
            interface=False,
        ),
        aggregate=_aggregate(
            materials=["MAT-ACP-FATA-LITERE"],
            operations=["face_cutting"],
            task_rules=[("Cut face", "face_cutting", "debitare_fata")],
        ),
        cpp=_cpp([("RULE-FACE", 1.2, 10.0)]),
    )
    preview = build_execution_preview_from_frozen_snapshot(snap)
    assert preview.frozen_graph.compatibility.scenario == "face_only"
    assert preview.frozen_graph.execution.adhesive_material_count == 0
    assert preview.frozen_graph.execution.bonding_operation_count == 0
    assert all("bonding" not in (c.source_operation_code or "").lower() for c in preview.task_candidates)
    assert all("cant" not in (c.owner_module or "").lower() for c in preview.task_candidates)


def test_cant_only_no_face_bonding_adhesive():
    snap = _snapshot(
        offer=_offer(mode="component_subset", sold=["RETURN-CANT"]),
        active=_active(
            mode="component_subset",
            sold=["RETURN-CANT"],
            active=["modelare_cant"],
            inactive=["debitare_fata", "sistem_led"],
            excl_ops=["RETURN_PROFILE_FACE_BONDING", "face_cutting"],
            excl_mats=["MAT-ADEZIV-CANT-LITERE", "MAT-ACP-FATA-LITERE"],
            interface=False,
        ),
        aggregate=_aggregate(
            materials=["MAT-PROFIL-LATERAL-LITERE"],
            operations=["RETURN_PROFILE_MACHINE_FORMING"],
            task_rules=[("Form cant", "RETURN_PROFILE_MACHINE_FORMING", "modelare_cant")],
        ),
        cpp=_cpp([("RULE-CANT", 12.5, 3.0)]),
    )
    preview = build_execution_preview_from_frozen_snapshot(snap)
    assert preview.frozen_graph.compatibility.scenario == "cant_only"
    assert preview.frozen_graph.execution.adhesive_material_count == 0
    assert preview.frozen_graph.execution.bonding_operation_count == 0
    assert all("face" not in (c.owner_module or "").lower() for c in preview.task_candidates)


def test_legacy_active_empty_not_empty_subset():
    snap = _snapshot(
        offer=_offer(mode="full_product", sold=[], use_legacy=True),
        active=_active(
            mode="full_product",
            sold=[],
            active=[],
            inactive=[],
            use_legacy=True,
        ),
        aggregate=_aggregate(
            materials=["MAT-ADEZIV-CANT-LITERE", "MAT-ACP-FATA-LITERE"],
            operations=["RETURN_PROFILE_FACE_BONDING", "face_cutting"],
            task_rules=[
                ("Bond", "RETURN_PROFILE_FACE_BONDING", "modelare_cant"),
                ("Cut", "face_cutting", "debitare_fata"),
            ],
        ),
    )
    preview = build_execution_preview_from_frozen_snapshot(snap)
    assert preview.source.legacy_mode is True
    assert preview.readiness == "legacy_compatible"
    assert preview.frozen_graph.compatibility.scenario == "legacy_full_product"


def test_scope_errors_fail_closed_no_silent_full_product():
    snap = _face_cant_snap()
    assert snap.active_scope_snapshot is not None
    snap.active_scope_snapshot.compiled.errors = ["SOLD_SCOPE_INVALID"]
    preview = build_execution_preview_from_frozen_snapshot(snap)
    assert preview.readiness == "scope_invalid"
    assert preview.task_candidates == []
    assert any("scope_error:" in b for b in preview.blockers)


def test_deterministic_candidate_keys_and_preview_fingerprint():
    snap = _face_cant_snap()
    a = build_execution_preview_from_frozen_snapshot(snap)
    b = build_execution_preview_from_frozen_snapshot(copy.deepcopy(snap))
    assert a.preview_fingerprint == b.preview_fingerprint
    assert [c.preview_candidate_key for c in a.task_candidates] == [
        c.preview_candidate_key for c in b.task_candidates
    ]
    assert all(c.preview_candidate_key.startswith("pv|") for c in a.task_candidates)


def test_no_uuid_in_candidate_keys():
    preview = build_execution_preview_from_frozen_snapshot(_face_cant_snap())
    for c in preview.task_candidates:
        assert "-" * 4 not in c.preview_candidate_key or "pv|" in c.preview_candidate_key
        # UUID v4 pattern roughly: 8-4-4-4-12 hex — ensure not pure UUID
        assert not (
            len(c.preview_candidate_key) == 36 and c.preview_candidate_key.count("-") == 4
        )


def test_order14_classifier_unchanged():
    result = classify_order14_compatibility(
        has_order=True, has_execution_plan=True, has_v2_json=False
    )
    assert "reinterpret_as_empty_subset" in result["must_not"]


def test_from_snapshot_endpoint_has_no_db_param():
    from routers.execution_preview_from_frozen import post_preview_from_frozen_snapshot

    params = inspect.signature(post_preview_from_frozen_snapshot).parameters
    assert "db" not in params


def test_router_ast_no_write_attributes():
    path = Path(__file__).resolve().parents[1] / "routers" / "execution_preview_from_frozen.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    writes = {"commit", "add", "flush", "delete", "merge"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in writes:
            pytest.fail(f"write attribute in Build 4C router: {node.attr}")


def test_commercial_no_reprice():
    preview = build_execution_preview_from_frozen_snapshot(_face_cant_snap())
    assert preview.commercial_reference.no_reprice is True
    assert preview.commercial_reference.cpp_line_count >= 1


def test_face_cant_missing_adhesive_blocks():
    snap = _snapshot(
        offer=_offer(mode="component_subset", sold=["FACE", "RETURN-CANT"]),
        active=_active(
            mode="component_subset",
            sold=["FACE", "RETURN-CANT"],
            active=["debitare_fata", "modelare_cant"],
            inactive=[],
            interface=True,
        ),
        aggregate=_aggregate(
            materials=["MAT-ACP-FATA-LITERE", "MAT-PROFIL-LATERAL-LITERE"],
            operations=["face_cutting", "RETURN_PROFILE_FACE_BONDING"],
            task_rules=[
                ("Cut face", "face_cutting", "debitare_fata"),
                ("Bond interface", "RETURN_PROFILE_FACE_BONDING", "modelare_cant"),
            ],
        ),
    )
    preview = build_execution_preview_from_frozen_snapshot(snap)
    assert preview.readiness == "blocked"
    assert any("adhesive_exactly_once" in b for b in preview.blockers)


def test_excluded_materials_do_not_leak_into_requirements():
    """Aggregate still carries excluded adhesive; scope excludes it — preview must not surface it."""
    snap = _snapshot(
        offer=_offer(mode="component_subset", sold=["FACE"]),
        active=_active(
            mode="component_subset",
            sold=["FACE"],
            active=["debitare_fata"],
            inactive=["modelare_cant"],
            excl_ops=["RETURN_PROFILE_FACE_BONDING"],
            excl_mats=["MAT-ADEZIV-CANT-LITERE"],
            interface=False,
        ),
        aggregate=_aggregate(
            materials=["MAT-ACP-FATA-LITERE", "MAT-ADEZIV-CANT-LITERE"],
            operations=["face_cutting", "RETURN_PROFILE_FACE_BONDING"],
            task_rules=[("Cut face", "face_cutting", "debitare_fata")],
        ),
        cpp=_cpp([("RULE-FACE", 1.2, 10.0)]),
    )
    preview = build_execution_preview_from_frozen_snapshot(snap)
    # Frozen graph Aggregate list may still list adhesive if snapshot Aggregate was not re-filtered;
    # Build 4C must honor scope.excluded_materials for requirements projection.
    codes = {m.material_code for m in preview.material_requirements}
    assert "MAT-ADEZIV-CANT-LITERE" not in codes


def test_duplicate_bonding_rules_not_silently_ready():
    snap = _snapshot(
        offer=_offer(mode="component_subset", sold=["FACE", "RETURN-CANT"]),
        active=_active(
            mode="component_subset",
            sold=["FACE", "RETURN-CANT"],
            active=["debitare_fata", "modelare_cant"],
            inactive=[],
            interface=True,
        ),
        aggregate=_aggregate(
            materials=["MAT-ACP-FATA-LITERE", "MAT-ADEZIV-CANT-LITERE"],
            operations=["RETURN_PROFILE_FACE_BONDING", "RETURN_PROFILE_FACE_BONDING"],
            task_rules=[
                ("Bond A", "RETURN_PROFILE_FACE_BONDING", "modelare_cant"),
                ("Bond B", "RETURN_PROFILE_FACE_BONDING", "modelare_cant"),
            ],
        ),
    )
    preview = build_execution_preview_from_frozen_snapshot(snap)
    bonding = [
        c
        for c in preview.task_candidates
        if c.source_operation_code and "bonding" in c.source_operation_code.lower()
    ]
    # Two candidates projected; bonding_exactly_once on operations count may still be 1 (set collapse)
    # but bonding_candidate_at_most_once / readiness must not claim clean golden silently.
    assert len(bonding) == 2
    # Operation multiplicity: raw Aggregate has 2 bonding ops → assertion fails → blocked
    assert preview.frozen_graph.execution.bonding_operation_count == 2
    assert preview.readiness == "blocked"


@pytest_asyncio.fixture
async def snapshot_service(volumetric_v2_db):
    from services.estimated_internal_cost_service import EstimatedInternalCostService
    from tests.test_quote_snapshot_v2 import INVENTORY_CATALOG, SAMPLE_RATES

    eic = EstimatedInternalCostService(volumetric_v2_db)

    async def _patched_load():
        return SAMPLE_RATES, {"RON": "RON"}, {"WC_CNC_ROUTING": 120.0}, INVENTORY_CATALOG

    eic._load_pricing_context = _patched_load  # type: ignore[method-assign]
    yield QuoteSnapshotV2Service(volumetric_v2_db, eic_service=eic)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "sold,scenario",
    [
        (["FACE"], "face_only"),
        (["RETURN-CANT"], "cant_only"),
        (["FACE", "RETURN-CANT"], "face_cant"),
    ],
)
async def test_live_build_preview_then_exec_preview_no_persist(
    volumetric_v2_db, snapshot_service, sold, scenario
):
    workspace_id = await _seed_workspace(volumetric_v2_db)
    before = await volumetric_v2_db.scalar(select(func.count()).select_from(QuoteSnapshotV2Record))
    qi = copy.deepcopy(_full_quote_input())
    qi["offer_scope"] = {
        "contract_version": "offer_scope_contract/v1",
        "mode": "component_subset",
        "sold_modules": sold,
    }
    snap = await snapshot_service.build_preview(
        TEMPLATE, workspace_id=workspace_id, quote_input=qi
    )
    assert snap is not None
    preview = build_execution_preview_from_frozen_snapshot(snap)
    after = await volumetric_v2_db.scalar(select(func.count()).select_from(QuoteSnapshotV2Record))
    assert before == after
    assert preview.safety.no_write is True
    assert preview.frozen_graph.compatibility.scenario == scenario
    assert preview.source.source_authority == "frozen_snapshot_v2"
    if scenario == "face_cant":
        bonding = [
            c
            for c in preview.task_candidates
            if (c.source_operation_code and "bonding" in c.source_operation_code.lower())
            or "bond" in c.task_name.lower()
        ]
        assert len(bonding) == 1
        assert preview.frozen_graph.execution.adhesive_material_count == 1
    else:
        assert preview.frozen_graph.execution.adhesive_material_count == 0
        assert preview.frozen_graph.execution.bonding_operation_count == 0
