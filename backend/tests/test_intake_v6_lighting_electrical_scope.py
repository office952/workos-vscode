"""LIGHTING / ELECTRICAL sold-scope split within comp_led_litere."""

from __future__ import annotations

import copy
import json
import uuid

import pytest
import pytest_asyncio

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from schemas.intake_v4 import (
    IntakeV4MaterialBreakdownResponse,
    IntakeV4MaterialBreakdownTotals,
    IntakeV4MaterialQuantityRow,
)
from schemas.offer_scope import OfferScopeInput
from services.aggregate_cost_bom_adapter import AggregateCostBomAdapter
from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.estimated_internal_cost_service import EstimatedInternalCostService
from services.execution_sold_scope_reader_service import (
    include_task_rule_for_sold_scope,
    read_execution_sold_scope,
)
from services.intake_v6_offer_scope_live_calc_service import (
    filter_commercial_line_items_by_offer_scope,
    filter_logical_list_rows_by_offer_scope,
    filter_material_breakdown_by_offer_scope,
)
from services.intake_v6_workspace_service import (
    get_intake_v6_workspace,
    save_offer_scope_for_intake_v6_workspace,
)
from services.offer_scope_led_subscope_service import (
    aggregate_material_led_subscope,
    material_led_subscope,
    operation_led_subscope,
    resolve_sold_led_subscopes,
)
from services.offer_scope_resolver_service import resolve_offer_scope
from services.product_aggregate_service import ProductAggregateService
from services.product_definition_builder_service import ProductDefinitionBuilderService
from services.quote_snapshot_component_scope_service import build_frozen_component_scope
from schemas.auth import UserResponse
from tests.execution_sold_scope_fixtures import (
    offer_scope,
    snapshot_with_scope,
    sold_scope_dossier_aggregate,
)
from tests.test_execution_sold_scope_reader import _rule
from tests.test_aggregate_cost_bom_adapter import (
    INVENTORY_CATALOG,
    SAMPLE_RATES,
    SAMPLE_WC_RATES,
    _full_payload,
)

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


def _user() -> UserResponse:
    return UserResponse(id="test-user", email="test@example.com", name="Test User", role="admin", last_login=None)


def _offer_scope(*, mode: str, sold: list[str]) -> dict:
    return {
        "contract_version": "offer_scope_contract/v1",
        "mode": mode,
        "sold_modules": sold,
    }


def _with_offer_scope(base: dict, *, mode: str, sold: list[str]) -> dict:
    out = copy.deepcopy(base)
    out["offer_scope"] = _offer_scope(mode=mode, sold=sold)
    out["product_binding"] = {"template_code": TEMPLATE}
    return out


def _led_quote_input(**overrides) -> dict:
    payload = _full_payload(with_psu=True)
    payload["finish_setup"]["lighting_system_type"] = "led_modules"
    payload.update(overrides)
    return payload


def _material_codes(bom) -> set[str]:
    return {m.material_code for m in bom.costable_materials}


def _operation_codes(bom) -> set[str]:
    return {o.operation_code for o in bom.costable_operations if o.operation_code}


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


def test_lighting_resolver_support() -> None:
    result = resolve_offer_scope(OfferScopeInput(mode="component_subset", sold_modules=["LIGHTING"]))
    assert not result.validation_errors
    assert result.runtime_sold_modules == {"sistem_led"}
    assert "LED_COUNT" not in result.calc_modules


def test_electrical_resolver_support() -> None:
    result = resolve_offer_scope(OfferScopeInput(mode="component_subset", sold_modules=["ELECTRICAL"]))
    assert not result.validation_errors
    assert result.runtime_sold_modules == {"sistem_led"}
    assert "LED_COUNT" in result.calc_modules


def test_subscope_maps() -> None:
    assert material_led_subscope("led_modules") == "LIGHTING"
    assert material_led_subscope("wire_letters_myyup_2x075") == "ELECTRICAL"
    assert aggregate_material_led_subscope("MAT-LED-MODULE") == "LIGHTING"
    assert aggregate_material_led_subscope("MAT-LED-PSU-12V-100W") == "ELECTRICAL"
    assert aggregate_material_led_subscope("MAT-CABLU-MYYUP-2X075") == "ELECTRICAL"
    assert operation_led_subscope("led_install_letters") == "LIGHTING"
    assert operation_led_subscope("electrical_letters") == "ELECTRICAL"


@pytest.mark.asyncio
async def test_lighting_only_bom_excludes_psu(bom_context) -> None:
    bom = await bom_context(
        quote_input=_with_offer_scope(_led_quote_input(), mode="component_subset", sold=["LIGHTING"]),
    )
    codes = _material_codes(bom)
    assert "MAT-LED-MODULE" in codes
    assert not any(code.startswith("MAT-LED-PSU") for code in codes)
    ops = _operation_codes(bom)
    assert "led_install_letters" not in ops
    assert "electrical_letters" not in ops


@pytest.mark.asyncio
async def test_electrical_only_bom_excludes_led_module(bom_context) -> None:
    bom = await bom_context(
        quote_input=_with_offer_scope(_led_quote_input(), mode="component_subset", sold=["ELECTRICAL"]),
    )
    codes = _material_codes(bom)
    assert "MAT-LED-MODULE" not in codes
    assert any(code.startswith("MAT-LED-PSU") for code in codes)
    ops = _operation_codes(bom)
    assert "electrical_letters" in ops
    assert "led_install_letters" not in ops


@pytest.mark.asyncio
async def test_combined_bom_without_duplication(bom_context) -> None:
    bom = await bom_context(
        quote_input=_with_offer_scope(
            _led_quote_input(),
            mode="component_subset",
            sold=["LIGHTING", "ELECTRICAL"],
        ),
    )
    codes = list(_material_codes(bom))
    assert codes.count("MAT-LED-MODULE") <= 1
    assert sum(1 for code in codes if code.startswith("MAT-LED-PSU")) <= 1
    ops = _operation_codes(bom)
    assert "led_install_letters" not in ops
    assert "electrical_letters" in ops


@pytest.mark.asyncio
async def test_lighting_only_eic_cpp(volumetric_v2_db) -> None:
    qi = _with_offer_scope(_led_quote_input(), mode="component_subset", sold=["LIGHTING"])
    eic = await EstimatedInternalCostService(volumetric_v2_db).build_preview(TEMPLATE, quote_input=qi)
    cpp = await CommercialPriceProposalService(volumetric_v2_db).build_preview(TEMPLATE, quote_input=qi)
    assert eic is not None and cpp is not None
    eic_codes = {line.code for line in eic.estimated_operation_lines}
    cpp_codes = {line.code for line in cpp.commercial_price_lines}
    assert "sistem_led_install" not in eic_codes
    assert "sistem_led_module" in cpp_codes
    assert "sursa_led" not in eic_codes
    assert "sursa_led" not in cpp_codes


@pytest.mark.asyncio
async def test_electrical_only_eic_cpp(volumetric_v2_db) -> None:
    qi = _with_offer_scope(_led_quote_input(), mode="component_subset", sold=["ELECTRICAL"])
    eic = await EstimatedInternalCostService(volumetric_v2_db).build_preview(TEMPLATE, quote_input=qi)
    cpp = await CommercialPriceProposalService(volumetric_v2_db).build_preview(TEMPLATE, quote_input=qi)
    assert eic is not None and cpp is not None
    eic_codes = {line.code for line in eic.estimated_operation_lines}
    cpp_codes = {line.code for line in cpp.commercial_price_lines}
    assert "sursa_led" in eic_codes
    assert "sursa_led" in cpp_codes
    assert "sistem_led_install" not in eic_codes
    assert "sistem_led_module" not in cpp_codes


def test_electrical_calc_dependency_does_not_price_led() -> None:
    payload = _with_offer_scope(_led_quote_input(), mode="component_subset", sold=["ELECTRICAL"])
    subscopes = resolve_sold_led_subscopes(payload, payload)
    assert subscopes == frozenset({"ELECTRICAL"})
    breakdown = IntakeV4MaterialBreakdownResponse(
        workspace_id="ws",
        template_code=TEMPLATE,
        material_rows=[],
        consumable_rows=[
            IntakeV4MaterialQuantityRow(
                material_key="led_modules",
                display_name="LED modules",
                category="consumable",
                quantity=100.0,
                unit="buc",
                quantity_source="test",
                quantity_quality="estimate",
                estimated_cost=50.0,
            ),
            IntakeV4MaterialQuantityRow(
                material_key="wire_letters_myyup_2x075",
                display_name="Wire",
                category="consumable",
                quantity=10.0,
                unit="ml",
                quantity_source="test",
                quantity_quality="estimate",
                estimated_cost=7.0,
            ),
        ],
        operation_rows=[],
        edge_cant_operation_rows=[],
        totals=IntakeV4MaterialBreakdownTotals(
            material_cost_total=57.0,
            estimated_cost_total=57.0,
            currency="EUR",
        ),
        warnings=[],
    )
    filtered = filter_material_breakdown_by_offer_scope(breakdown, payload_raw=payload)
    keys = {row.material_key for row in filtered.consumable_rows}
    assert "led_modules" not in keys
    assert "wire_letters_myyup_2x075" in keys
    assert filtered.totals.estimated_cost_total == 7.0


@pytest.mark.asyncio
async def test_full_product_totals_unchanged(volumetric_v2_db) -> None:
    qi = _led_quote_input()
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


def test_logical_list_subscope_filter() -> None:
    payload = _with_offer_scope(_led_quote_input(), mode="component_subset", sold=["ELECTRICAL"])
    rows = [
        {"line_id": "material.led_modules", "module_code": "sistem_led"},
        {"line_id": "material.led_psu", "module_code": "sistem_led"},
        {"line_id": "material.wire_letters", "module_code": "sistem_led"},
    ]
    filtered = filter_logical_list_rows_by_offer_scope(rows, payload_raw=payload)
    assert {row["line_id"] for row in filtered} == {"material.led_psu", "material.wire_letters"}


def test_commercial_line_subscope_filter() -> None:
    payload = _with_offer_scope(_led_quote_input(), mode="component_subset", sold=["LIGHTING"])
    lines = [
        {"code": "sistem_led_module", "module_code": "sistem_led"},
        {"code": "sursa_led", "module_code": "sistem_led"},
    ]
    filtered = filter_commercial_line_items_by_offer_scope(lines, payload_raw=payload)
    assert {line["code"] for line in filtered} == {"sistem_led_module"}


@pytest.mark.asyncio
async def test_workspace_persistence_lighting_scope(volumetric_v2_db) -> None:
    workspace_id = str(uuid.uuid4())
    volumetric_v2_db.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"IV6-LED-SCOPE-{workspace_id[:8]}",
            title="LED scope",
            template_code=TEMPLATE,
            status="ready_for_quote_preview",
            payload_json=json.dumps(
                {
                    "product_binding": {"template_code": TEMPLATE},
                    "svg_source": {
                        "file_name": "test.svg",
                        "file_size_bytes": 100,
                        "upload_status": "analyzed",
                    },
                    "product_composition_confirmed": {"confirmed": True},
                }
            ),
        )
    )
    await volumetric_v2_db.commit()

    await save_offer_scope_for_intake_v6_workspace(
        volumetric_v2_db,
        workspace_id,
        mode="component_subset",
        sold_modules=["LIGHTING"],
        confirmed=True,
        current_user=_user(),
    )
    reloaded = await get_intake_v6_workspace(volumetric_v2_db, workspace_id)
    assert reloaded.payload["offer_scope"]["sold_modules"] == ["LIGHTING"]

    scope = await build_frozen_component_scope(
        volumetric_v2_db,
        template_code=TEMPLATE,
        workspace_id=workspace_id,
    )
    assert scope is not None
    assert scope.offer_scope_snapshot.sold_modules == ["LIGHTING"]
    assert "sistem_led" in scope.offer_scope_snapshot.resolved_runtime_sold_modules


def test_execution_lighting_tasks_only() -> None:
    ctx = read_execution_sold_scope(
        snapshot_with_scope(
            offer_scope=offer_scope(sold=["LIGHTING"], runtime=["sistem_led"]),
        )
    )
    assert not include_task_rule_for_sold_scope(_rule("led_installation"), ctx=ctx)
    assert not include_task_rule_for_sold_scope(_rule("electrical_wiring"), ctx=ctx)


def test_execution_electrical_tasks_only() -> None:
    ctx = read_execution_sold_scope(
        snapshot_with_scope(
            offer_scope=offer_scope(sold=["ELECTRICAL"], runtime=["sistem_led"]),
        )
    )
    assert not include_task_rule_for_sold_scope(_rule("led_installation"), ctx=ctx)
    assert include_task_rule_for_sold_scope(_rule("electrical_wiring"), ctx=ctx)


def test_execution_combined_union() -> None:
    ctx = read_execution_sold_scope(
        snapshot_with_scope(
            offer_scope=offer_scope(sold=["LIGHTING", "ELECTRICAL"], runtime=["sistem_led"]),
        )
    )
    included = {
        rule.task_name
        for rule in sold_scope_dossier_aggregate().task_contract.task_rules
        if include_task_rule_for_sold_scope(rule, ctx=ctx)
    }
    assert "led_installation" not in included
    assert "electrical_wiring" in included
