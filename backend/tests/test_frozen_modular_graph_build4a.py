"""Build 4A — Frozen Modular Graph fingerprints + scenario assertions (no writes)."""

from __future__ import annotations

import ast
import copy
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import func, select

from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from schemas.commercial_price_proposal import CommercialPriceLine, CommercialPriceProposalPreview
from schemas.estimated_internal_cost import EstimatedInternalCostPreview
from schemas.frozen_modular_graph import FROZEN_MODULAR_GRAPH_ADAPTER_VERSION
from schemas.product_aggregate import (
    ProductAggregate,
    ProductAggregateMaterial,
    ProductAggregateOperation,
    ProductAggregateTaskContract,
    ProductAggregateTaskRule,
)
from schemas.product_definition import ProductDefinitionPreview, ProductDefinitionSourceContext
from schemas.quote_snapshot_v2 import (
    QuoteSnapshotActiveScope,
    QuoteSnapshotOfferScope,
    QuoteSnapshotV2,
)
from schemas.active_scope import ActiveScopeResult
from services.frozen_modular_graph_service import (
    build_frozen_modular_graph_from_v2,
    classify_order14_compatibility,
    fingerprint_cpp_lines,
    fingerprint_hash,
)
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
                mini_module_code="m",
                provenance="dossier",
            )
            for code in materials
        ],
        operations=[
            ProductAggregateOperation(
                operation_code=code,
                component_ref="comp",
                mini_module_code="m",
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


def test_canonical_hash_strips_volatile_timestamps():
    a = _snapshot(
        offer=_offer(mode="full_product", sold=[]),
        active=_active(
            mode="full_product",
            sold=[],
            active=[],
            inactive=[],
            use_legacy=True,
        ),
        aggregate=_aggregate(
            materials=["MAT-ADEZIV-CANT-LITERE", "MAT-ACP-FATA-LITERE"],
            operations=["return_face_bonding", "face_cutting"],
            task_rules=[("Bond face", "return_face_bonding", "interface"), ("Cut face", "face_cutting", "debitare_fata")],
        ),
    )
    b = copy.deepcopy(a)
    b.frozen_at = "1999-01-01T00:00:00Z"
    b.version = 99
    ga = build_frozen_modular_graph_from_v2(a)
    gb = build_frozen_modular_graph_from_v2(b)
    assert ga.hashes.frozen_graph == gb.hashes.frozen_graph
    assert ga.hashes.product_aggregate == gb.hashes.product_aggregate


def test_semantic_material_change_changes_hash():
    base = _snapshot(
        offer=_offer(mode="component_subset", sold=["FACE"]),
        active=_active(
            mode="component_subset",
            sold=["FACE"],
            active=["debitare_fata"],
            inactive=["modelare_cant"],
            excl_ops=["return_face_bonding"],
            excl_mats=["MAT-ADEZIV-CANT-LITERE"],
            interface=False,
        ),
        aggregate=_aggregate(
            materials=["MAT-ACP-FATA-LITERE"],
            operations=["face_cutting"],
            task_rules=[("Cut face", "face_cutting", "debitare_fata")],
        ),
    )
    changed = copy.deepcopy(base)
    assert changed.product_aggregate_snapshot is not None
    changed.product_aggregate_snapshot.materials.append(
        ProductAggregateMaterial(
            material_code="MAT-EXTRA",
            component_ref="comp",
            mini_module_code="m",
            provenance="dossier",
        )
    )
    assert (
        build_frozen_modular_graph_from_v2(base).hashes.product_aggregate
        != build_frozen_modular_graph_from_v2(changed).hashes.product_aggregate
    )


def test_cpp_line_fingerprint_not_totals_only():
    cpp = _cpp([("RULE-B", 2.0, 5.0), ("RULE-A", 1.0, 10.0)])
    fp = fingerprint_cpp_lines(cpp)
    assert [r["code"] for r in fp] == ["RULE-A", "RULE-B"]
    assert fp[0]["quantity"] == 1.0
    assert fp[0]["unit_price"] == 10.0
    assert fp[0]["subtotal"] == 10.0


def test_legacy_active_empty_is_full_product_not_empty_subset():
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
            materials=["MAT-ADEZIV-CANT-LITERE"],
            operations=["return_face_bonding"],
            task_rules=[("Bond", "return_face_bonding", "interface")],
        ),
    )
    graph = build_frozen_modular_graph_from_v2(snap)
    assert graph.compatibility.scenario == "legacy_full_product"
    assert graph.scope.use_legacy_full_product is True
    assert graph.scope.active_modules == []
    assert any(a.code == "legacy_active_empty_not_empty_subset" and a.passed for a in graph.assertions)


def test_face_only_assertions():
    snap = _snapshot(
        offer=_offer(mode="component_subset", sold=["FACE"]),
        active=_active(
            mode="component_subset",
            sold=["FACE"],
            active=["debitare_fata"],
            inactive=["modelare_cant", "sistem_led"],
            excl_ops=["return_face_bonding", "side_forming"],
            excl_mats=["MAT-ADEZIV-CANT-LITERE", "adhesive_return_to_face"],
            interface=False,
        ),
        aggregate=_aggregate(
            materials=["MAT-ACP-FATA-LITERE"],
            operations=["face_cutting"],
            task_rules=[("Cut face", "face_cutting", "debitare_fata")],
        ),
        cpp=_cpp([("RULE-FACE", 1.2, 10.0)]),
    )
    graph = build_frozen_modular_graph_from_v2(snap)
    assert graph.compatibility.scenario == "face_only"
    assert graph.execution.adhesive_material_count == 0
    assert graph.execution.bonding_operation_count == 0
    assert all(a.passed for a in graph.assertions if a.code.startswith("no_"))


def test_cant_only_assertions():
    snap = _snapshot(
        offer=_offer(mode="component_subset", sold=["RETURN-CANT"]),
        active=_active(
            mode="component_subset",
            sold=["RETURN-CANT"],
            active=["modelare_cant"],
            inactive=["debitare_fata", "sistem_led"],
            excl_ops=["return_face_bonding", "face_cutting"],
            excl_mats=["MAT-ADEZIV-CANT-LITERE", "MAT-ACP-FATA-LITERE"],
            interface=False,
        ),
        aggregate=_aggregate(
            materials=["MAT-PROFIL-LATERAL-LITERE"],
            operations=["side_forming"],
            task_rules=[("Form cant", "side_forming", "modelare_cant")],
        ),
        cpp=_cpp([("RULE-CANT", 12.5, 3.0)]),
    )
    graph = build_frozen_modular_graph_from_v2(snap)
    assert graph.compatibility.scenario == "cant_only"
    assert graph.execution.adhesive_material_count == 0
    assert graph.execution.bonding_operation_count == 0
    failed = [a for a in graph.assertions if not a.passed]
    assert failed == []


def test_face_cant_adhesive_bonding_exactly_once():
    snap = _snapshot(
        offer=_offer(mode="component_subset", sold=["FACE", "RETURN-CANT"]),
        active=_active(
            mode="component_subset",
            sold=["FACE", "RETURN-CANT"],
            active=["debitare_fata", "modelare_cant"],
            inactive=["sistem_led"],
            excl_ops=[],
            excl_mats=[],
            interface=True,
        ),
        aggregate=_aggregate(
            materials=["MAT-ACP-FATA-LITERE", "MAT-PROFIL-LATERAL-LITERE", "MAT-ADEZIV-CANT-LITERE"],
            operations=["face_cutting", "side_forming", "return_face_bonding"],
            task_rules=[
                ("Cut face", "face_cutting", "debitare_fata"),
                ("Form cant", "side_forming", "modelare_cant"),
                ("Bond interface", "return_face_bonding", "interface"),
            ],
        ),
    )
    graph = build_frozen_modular_graph_from_v2(snap)
    assert graph.compatibility.scenario == "face_cant"
    assert graph.execution.adhesive_material_count == 1
    assert graph.execution.bonding_operation_count == 1
    assert graph.scope.interface_face_cant_active is True
    assert all(
        a.passed
        for a in graph.assertions
        if a.code in ("adhesive_exactly_once", "bonding_exactly_once", "interface_active")
    )


def test_task_candidates_from_task_rules_not_all_operations():
    snap = _snapshot(
        offer=_offer(mode="component_subset", sold=["FACE"]),
        active=_active(
            mode="component_subset",
            sold=["FACE"],
            active=["debitare_fata"],
            inactive=[],
            interface=False,
        ),
        aggregate=_aggregate(
            materials=["MAT-ACP-FATA-LITERE"],
            operations=["face_cutting", "info_only_op", "another_op"],
            task_rules=[("Cut face", "face_cutting", "debitare_fata")],
        ),
    )
    graph = build_frozen_modular_graph_from_v2(snap)
    assert graph.execution.candidate_count == 1
    assert graph.execution.task_candidates[0].priced_operation == "face_cutting"
    assert len(graph.execution.operation_codes) == 3


def test_excluded_priced_operation_filtered_from_candidates():
    snap = _snapshot(
        offer=_offer(mode="component_subset", sold=["FACE"]),
        active=_active(
            mode="component_subset",
            sold=["FACE"],
            active=["debitare_fata"],
            inactive=["modelare_cant"],
            excl_ops=["return_face_bonding"],
            excl_mats=["MAT-ADEZIV-CANT-LITERE"],
            interface=False,
        ),
        aggregate=_aggregate(
            materials=["MAT-ACP-FATA-LITERE"],
            operations=["face_cutting"],
            task_rules=[
                ("Cut face", "face_cutting", "debitare_fata"),
                ("Bond leak", "return_face_bonding", "interface"),
            ],
        ),
    )
    graph = build_frozen_modular_graph_from_v2(snap)
    assert graph.execution.candidate_count == 1
    assert graph.execution.task_candidates[0].task_name == "Cut face"


def test_determinism_repeat():
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
            materials=["MAT-ADEZIV-CANT-LITERE", "MAT-ACP-FATA-LITERE"],
            operations=["return_face_bonding", "face_cutting"],
            task_rules=[
                ("Bond", "return_face_bonding", "interface"),
                ("Cut", "face_cutting", "debitare_fata"),
            ],
        ),
    )
    hashes = [build_frozen_modular_graph_from_v2(snap).hashes.frozen_graph for _ in range(5)]
    assert len(set(hashes)) == 1


def test_order14_compatibility_classifier():
    result = classify_order14_compatibility(
        has_order=True, has_execution_plan=True, has_v2_json=False
    )
    assert result["anchor_order_id"] == 14
    assert "reinterpret_as_empty_subset" in result["must_not"]
    assert result["no_write"] is True


def test_duplicate_adhesive_rows_fail_exactly_once():
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
            materials=[
                "MAT-ACP-FATA-LITERE",
                "MAT-ADEZIV-CANT-LITERE",
                "MAT-ADEZIV-CANT-LITERE",
            ],
            operations=["return_face_bonding", "face_cutting"],
            task_rules=[
                ("Bond", "return_face_bonding", "interface"),
                ("Cut", "face_cutting", "debitare_fata"),
            ],
        ),
    )
    graph = build_frozen_modular_graph_from_v2(snap)
    assert graph.execution.adhesive_material_count == 2
    assert any(a.code == "adhesive_exactly_once" and not a.passed for a in graph.assertions)


def test_scope_list_order_does_not_change_hash():
    snap = _snapshot(
        offer=_offer(mode="component_subset", sold=["FACE", "RETURN-CANT"]),
        active=_active(
            mode="component_subset",
            sold=["FACE", "RETURN-CANT"],
            active=["debitare_fata", "modelare_cant"],
            inactive=["sistem_led", "debitare_spate"],
            interface=True,
        ),
        aggregate=_aggregate(
            materials=["MAT-ADEZIV-CANT-LITERE", "MAT-ACP-FATA-LITERE"],
            operations=["return_face_bonding"],
            task_rules=[("Bond", "return_face_bonding", "interface")],
        ),
    )
    reordered = copy.deepcopy(snap)
    assert reordered.active_scope_snapshot is not None
    reordered.active_scope_snapshot.compiled.active_runtime_modules = [
        "modelare_cant",
        "debitare_fata",
    ]
    assert (
        build_frozen_modular_graph_from_v2(snap).hashes.frozen_graph
        == build_frozen_modular_graph_from_v2(reordered).hashes.frozen_graph
    )


def test_from_snapshot_endpoint_has_no_db_dependency():
    import inspect

    from routers.frozen_modular_graph import post_frozen_modular_graph_from_snapshot

    params = inspect.signature(post_frozen_modular_graph_from_snapshot).parameters
    assert "db" not in params


def test_no_write_marker_and_adapter_version():
    snap = _snapshot(
        offer=_offer(mode="full_product", sold=[]),
        active=_active(mode="full_product", sold=[], active=[], inactive=[], use_legacy=True),
        aggregate=_aggregate(
            materials=["MAT-ADEZIV-CANT-LITERE"],
            operations=["return_face_bonding"],
            task_rules=[("Bond", "return_face_bonding", "interface")],
        ),
    )
    graph = build_frozen_modular_graph_from_v2(snap)
    assert graph.no_write is True
    assert graph.compatibility.adapter_version == FROZEN_MODULAR_GRAPH_ADAPTER_VERSION
    assert graph.hashes.frozen_graph
    assert graph.hashes.cpp
    assert graph.hashes.active_scope


def test_router_has_no_db_writes_in_from_snapshot():
    """Static guard: from-snapshot handler must not call commit/add/flush."""
    path = Path(__file__).resolve().parents[1] / "routers" / "frozen_modular_graph.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    writes = {"commit", "add", "flush", "delete", "merge"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in writes:
            # db.commit etc. must not appear
            pytest.fail(f"write attribute found in router: {node.attr}")


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
async def test_build_preview_then_normalize_no_persist(volumetric_v2_db, snapshot_service):
    workspace_id = await _seed_workspace(volumetric_v2_db)
    before = await volumetric_v2_db.scalar(select(func.count()).select_from(QuoteSnapshotV2Record))
    qi = copy.deepcopy(_full_quote_input())
    qi["offer_scope"] = {
        "contract_version": "offer_scope_contract/v1",
        "mode": "component_subset",
        "sold_modules": ["RETURN-CANT"],
    }
    snap = await snapshot_service.build_preview(
        TEMPLATE, workspace_id=workspace_id, quote_input=qi
    )
    assert snap is not None
    graph = build_frozen_modular_graph_from_v2(snap)
    after = await volumetric_v2_db.scalar(select(func.count()).select_from(QuoteSnapshotV2Record))
    assert before == after
    assert graph.no_write is True
    assert graph.compatibility.scenario == "cant_only"
    assert graph.execution.adhesive_material_count == 0
    assert graph.execution.bonding_operation_count == 0
    # Excluded bonding must not leak into candidates
    assert all(
        c.priced_operation != "return_face_bonding" for c in graph.execution.task_candidates
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "sold,expected_scenario",
    [
        (["FACE"], "face_only"),
        (["RETURN-CANT"], "cant_only"),
        (["FACE", "RETURN-CANT"], "face_cant"),
    ],
)
async def test_live_preview_scenarios(volumetric_v2_db, snapshot_service, sold, expected_scenario):
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
    graph = build_frozen_modular_graph_from_v2(snap)
    after = await volumetric_v2_db.scalar(select(func.count()).select_from(QuoteSnapshotV2Record))
    assert before == after
    assert graph.compatibility.scenario == expected_scenario
    if expected_scenario == "face_cant":
        assert graph.scope.interface_face_cant_active is True
        assert graph.scope.excluded_materials == []
        assert graph.scope.excluded_operations == []
        assert graph.execution.semantic_interface_face_cant_active is True
        assert all(
            a.passed
            for a in graph.assertions
            if a.code in ("interface_active", "interface_exclusions_empty")
        )
        # No greenwash: missing technical adhesive/bonding must FAIL assertions.
        if (
            graph.execution.adhesive_material_count == 1
            and graph.execution.bonding_operation_count == 1
        ):
            assert all(
                a.passed
                for a in graph.assertions
                if a.code in ("adhesive_exactly_once", "bonding_exactly_once")
            )
        else:
            assert any(
                a.code == "adhesive_exactly_once" and not a.passed for a in graph.assertions
            ) or any(a.code == "bonding_exactly_once" and not a.passed for a in graph.assertions)
    else:
        assert graph.execution.adhesive_material_count == 0
        assert graph.execution.bonding_operation_count == 0
        assert graph.scope.interface_face_cant_active is not True
    assert fingerprint_hash({"x": 1}) == fingerprint_hash({"x": 1})
