"""Integration tests — offer_scope sold filter on BOM / EIC / CPP."""

from __future__ import annotations

import copy
import json
import uuid

import pytest
import pytest_asyncio

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from seeds.seed_tpl_volumetric_logo_v1 import seed_tpl_volumetric_logo_v1
from services.aggregate_cost_bom_adapter import AggregateCostBomAdapter, AggregateCostBomBuilderService
from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.estimated_internal_cost_service import EstimatedInternalCostService
from services.product_aggregate_service import ProductAggregateService
from services.product_definition_builder_service import ProductDefinitionBuilderService
from tests.eic_workspace_logo_fixtures import (
    LOGO_INSTANCE_A,
    confirmed_bindings_payload,
)
from tests.test_aggregate_cost_bom_adapter import (
    INVENTORY_CATALOG,
    SAMPLE_RATES,
    SAMPLE_WC_RATES,
    _full_payload,
)

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


def _with_offer_scope(base: dict, *, mode: str, sold: list[str]) -> dict:
    out = copy.deepcopy(base)
    out["offer_scope"] = {
        "contract_version": "offer_scope_contract/v1",
        "mode": mode,
        "sold_modules": sold,
    }
    return out


def _modules_in_bom(bom) -> set[str]:
    mods: set[str] = set()
    for item in bom.costable_components + bom.costable_materials + bom.costable_operations:
        if item.mini_module_code:
            mods.add(item.mini_module_code)
    return mods


@pytest_asyncio.fixture
async def bom_context(volumetric_v2_db):
    pd_builder = ProductDefinitionBuilderService(volumetric_v2_db)
    aggregate_svc = ProductAggregateService(volumetric_v2_db)
    adapter = AggregateCostBomAdapter()

    async def _build(*, quote_input=None):
        pd = await pd_builder.build_preview(TEMPLATE)
        aggregate = await aggregate_svc.build(TEMPLATE)
        assert pd is not None and aggregate is not None
        return adapter.build(
            product_definition=pd,
            aggregate=aggregate,
            quote_input=quote_input,
            material_rates=SAMPLE_RATES,
            workcenter_rates=SAMPLE_WC_RATES,
            inventory_catalog=INVENTORY_CATALOG,
        )

    return _build


@pytest.mark.asyncio
async def test_no_offer_scope_matches_legacy_full_product_modules(bom_context) -> None:
    baseline = await bom_context(quote_input=_full_payload())
    explicit = await bom_context(
        quote_input=_with_offer_scope(_full_payload(), mode="full_product", sold=[]),
    )
    assert _modules_in_bom(baseline) == _modules_in_bom(explicit)
    for expected in ("debitare_fata", "modelare_cant", "debitare_spate", "finisaje"):
        assert expected in _modules_in_bom(baseline)


@pytest.mark.asyncio
async def test_face_only_bom_excludes_other_modules(bom_context) -> None:
    bom = await bom_context(
        quote_input=_with_offer_scope(_full_payload(), mode="component_subset", sold=["FACE"]),
    )
    mods = _modules_in_bom(bom)
    assert "debitare_fata" in mods
    assert "debitare_spate" not in mods
    assert "modelare_cant" not in mods
    assert "finisaje" not in mods


@pytest.mark.asyncio
async def test_return_cant_only_bom_excludes_face(bom_context) -> None:
    bom = await bom_context(
        quote_input=_with_offer_scope(_full_payload(), mode="component_subset", sold=["RETURN-CANT"]),
    )
    mods = _modules_in_bom(bom)
    assert mods == {"modelare_cant"} or ("modelare_cant" in mods and "debitare_fata" not in mods)
    assert "debitare_fata" not in mods
    assert "debitare_spate" not in mods
    assert "finisaje" not in mods


@pytest.mark.asyncio
async def test_back_only_bom(bom_context) -> None:
    bom = await bom_context(
        quote_input=_with_offer_scope(_full_payload(), mode="component_subset", sold=["BACK"]),
    )
    mods = _modules_in_bom(bom)
    assert "debitare_spate" in mods
    assert "debitare_fata" not in mods
    assert "modelare_cant" not in mods


@pytest.mark.asyncio
async def test_face_and_return_cant_bom(bom_context) -> None:
    bom = await bom_context(
        quote_input=_with_offer_scope(
            _full_payload(),
            mode="component_subset",
            sold=["FACE", "RETURN-CANT"],
        ),
    )
    mods = _modules_in_bom(bom)
    assert "debitare_fata" in mods
    assert "modelare_cant" in mods
    assert "debitare_spate" not in mods
    assert "finisaje" not in mods


@pytest.mark.asyncio
async def test_empty_subset_produces_no_costable_modules(bom_context) -> None:
    bom = await bom_context(
        quote_input=_with_offer_scope(_full_payload(), mode="component_subset", sold=[]),
    )
    assert _modules_in_bom(bom) == set()


@pytest.mark.asyncio
async def test_unknown_module_produces_no_costable_modules(bom_context) -> None:
    payload = _full_payload()
    payload["offer_scope"] = {
        "contract_version": "offer_scope_contract/v1",
        "mode": "component_subset",
        "sold_modules": ["NOT_A_MODULE"],
    }
    bom = await bom_context(quote_input=payload)
    assert _modules_in_bom(bom) == set()


@pytest.mark.asyncio
async def test_return_cant_perimeter_rows_without_face_pricing(bom_context) -> None:
    bom = await bom_context(
        quote_input=_with_offer_scope(_full_payload(), mode="component_subset", sold=["RETURN-CANT"]),
    )
    profile_rows = [
        m
        for m in bom.costable_materials
        if (m.material_code or "").startswith("MAT-PROFIL-LATERAL-LITERE")
    ]
    assert profile_rows
    face_ops = [o for o in bom.costable_operations if o.mini_module_code == "debitare_fata"]
    assert not face_ops


@pytest.mark.asyncio
async def test_eic_and_cpp_face_only_match_bom_filter(volumetric_v2_db) -> None:
    qi = _with_offer_scope(_full_payload(), mode="component_subset", sold=["FACE"])
    bom = await AggregateCostBomBuilderService(volumetric_v2_db).build_preview(TEMPLATE, quote_input=qi)
    eic = await EstimatedInternalCostService(volumetric_v2_db).build_preview(TEMPLATE, quote_input=qi)
    cpp = await CommercialPriceProposalService(volumetric_v2_db).build_preview(TEMPLATE, quote_input=qi)
    assert bom is not None and eic is not None and cpp is not None
    bom_mods = _modules_in_bom(bom)
    assert bom_mods == {"debitare_fata"} or "debitare_fata" in bom_mods
    eic_mods = {
        line.module_code
        for line in eic.estimated_material_lines + eic.estimated_operation_lines
        if line.module_code
    }
    assert "debitare_spate" not in eic_mods
    assert "modelare_cant" not in eic_mods
    cpp_mods = {line.module_code for line in cpp.commercial_price_lines if line.module_code}
    assert "debitare_spate" not in cpp_mods
    assert "modelare_cant" not in cpp_mods


@pytest.mark.asyncio
async def test_full_product_cpp_eic_totals_unchanged_without_offer_scope(volumetric_v2_db) -> None:
    qi = _full_payload()
    cpp_a = await CommercialPriceProposalService(volumetric_v2_db).build_preview(TEMPLATE, quote_input=qi)
    eic_a = await EstimatedInternalCostService(volumetric_v2_db).build_preview(TEMPLATE, quote_input=qi)
    cpp_b = await CommercialPriceProposalService(volumetric_v2_db).build_preview(
        TEMPLATE,
        quote_input=_with_offer_scope(qi, mode="full_product", sold=[]),
    )
    eic_b = await EstimatedInternalCostService(volumetric_v2_db).build_preview(
        TEMPLATE,
        quote_input=_with_offer_scope(qi, mode="full_product", sold=[]),
    )
    assert cpp_a is not None and cpp_b is not None
    assert eic_a is not None and eic_b is not None
    assert cpp_a.commercial_total == cpp_b.commercial_total
    assert eic_a.estimated_total_internal_cost == eic_b.estimated_total_internal_cost


@pytest.mark.asyncio
async def test_linked_logo_full_product_unchanged(volumetric_v2_db) -> None:
    from tests.test_product_aggregate_volumetric_v2 import _seed_volumetric_v2_fixture

    await _seed_volumetric_v2_fixture(volumetric_v2_db)
    await seed_tpl_volumetric_logo_v1()
    workspace_id = str(uuid.uuid4())
    volumetric_v2_db.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code="WS-OFFER-SCOPE-LOGO",
            title="logo baseline",
            template_code=TEMPLATE,
            status="draft",
            payload_json=json.dumps(confirmed_bindings_payload()),
        )
    )
    await volumetric_v2_db.commit()

    bom_before = await AggregateCostBomBuilderService(volumetric_v2_db).build_preview(
        TEMPLATE, workspace_id=workspace_id
    )
    assert bom_before is not None
    logo_mats_before = [
        m for m in bom_before.costable_materials if LOGO_INSTANCE_A in (m.component_ref or "")
    ]
    count_before = len(bom_before.costable_materials)

    bom_after = await AggregateCostBomBuilderService(volumetric_v2_db).build_preview(
        TEMPLATE,
        workspace_id=workspace_id,
        quote_input=_with_offer_scope(_full_payload(), mode="full_product", sold=[]),
    )
    assert bom_after is not None
    assert len(bom_after.costable_materials) == count_before
    logo_mats_after = [
        m for m in bom_after.costable_materials if LOGO_INSTANCE_A in (m.component_ref or "")
    ]
    assert len(logo_mats_after) == len(logo_mats_before)
