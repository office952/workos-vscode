"""LIGHTING mount consumer gating — adhesive / install vs sold scope + confirmations."""

from __future__ import annotations

import copy

import pytest

from services.lighting_mount_consumer_service import resolve_lighting_mount_consumers
from services.sold_scope_dependency_validator_service import (
    CODE_LED_INSTALLATION_BY_US,
    CODE_LED_MOUNT_SURFACE_NOT_SOLD,
)
from tests.test_intake_v6_lighting_electrical_scope import (
    TEMPLATE,
    _led_quote_input,
    _material_codes,
    _offer_scope,
    _operation_codes,
    _with_offer_scope,
)
from services.estimated_internal_cost_service import EstimatedInternalCostService
from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.execution_sold_scope_reader_service import (
    include_task_rule_for_sold_scope,
    read_execution_sold_scope,
)
from services.intake_v6_offer_scope_live_calc_service import filter_material_breakdown_by_offer_scope
from schemas.intake_v4 import (
    IntakeV4MaterialBreakdownResponse,
    IntakeV4MaterialBreakdownTotals,
    IntakeV4MaterialQuantityRow,
)
from tests.execution_sold_scope_fixtures import offer_scope, snapshot_with_scope
from tests.test_execution_sold_scope_reader import _rule

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2", "tests.test_intake_v6_lighting_electrical_scope"]


def _payload(*, sold: list[str], confirmations: list[str] | None = None) -> dict:
    payload = _with_offer_scope(_led_quote_input(), mode="component_subset", sold=sold)
    payload["product_binding"] = {"template_code": TEMPLATE}
    payload["offer_scope_confirmed"] = {
        "confirmed": True,
        "dependency_confirmations": confirmations or [],
    }
    return payload


def _decision(*, sold: list[str], confirmations: list[str] | None = None):
    return resolve_lighting_mount_consumers(_payload(sold=sold, confirmations=confirmations), None)


def test_back_lighting_includes_all_consumers() -> None:
    d = _decision(sold=["BACK", "LIGHTING"])
    assert d is not None
    assert d.include_led_modules is True
    assert d.include_led_adhesive is True
    assert d.include_led_install_operation is True
    assert d.installation_by_us is True
    assert d.sold_mount_provider is True


def test_face_cant_lighting_includes_all_consumers() -> None:
    d = _decision(sold=["FACE", "RETURN-CANT", "LIGHTING"])
    assert d is not None
    assert d.include_led_adhesive is True
    assert d.include_led_install_operation is True
    assert d.sold_mount_provider is True


def test_lighting_only_unconfirmed_excludes_adhesive_install() -> None:
    d = _decision(sold=["LIGHTING"])
    assert d is not None
    assert d.include_led_modules is True
    assert d.include_led_adhesive is False
    assert d.include_led_install_operation is False
    assert d.installation_by_us is False


def test_lighting_external_confirmed_modules_only() -> None:
    d = _decision(
        sold=["LIGHTING"],
        confirmations=[CODE_LED_MOUNT_SURFACE_NOT_SOLD],
    )
    assert d is not None
    assert d.external_mount_confirmed is True
    assert d.mount_surface_satisfied is True
    assert d.include_led_modules is True
    assert d.include_led_adhesive is False
    assert d.include_led_install_operation is False


def test_lighting_external_confirmed_install_by_us() -> None:
    d = _decision(
        sold=["LIGHTING"],
        confirmations=[CODE_LED_MOUNT_SURFACE_NOT_SOLD, CODE_LED_INSTALLATION_BY_US],
    )
    assert d is not None
    assert d.installation_by_us is True
    assert d.include_led_adhesive is True
    assert d.include_led_install_operation is True


def test_lighting_electrical_no_mount_gates_adhesive_only() -> None:
    d = _decision(sold=["LIGHTING", "ELECTRICAL"])
    assert d is not None
    assert d.include_led_modules is True
    assert d.include_led_adhesive is False
    assert d.include_led_install_operation is False


def test_electrical_only_unchanged() -> None:
    d = _decision(sold=["ELECTRICAL"])
    assert d is not None
    assert d.lighting_sold is False
    assert d.include_led_modules is False


def test_back_only_unchanged() -> None:
    d = _decision(sold=["BACK"])
    assert d is not None
    assert d.lighting_sold is False


def test_full_product_legacy_bypass() -> None:
    payload = _led_quote_input()
    payload["offer_scope"] = _offer_scope(mode="full_product", sold=[])
    d = resolve_lighting_mount_consumers(payload, payload)
    assert d is not None
    assert d.use_legacy is True
    assert d.include_led_adhesive is True


@pytest.mark.asyncio
async def test_back_lighting_bom_coherent(bom_context) -> None:
    bom = await bom_context(
        quote_input=_payload(sold=["BACK", "LIGHTING"]),
    )
    codes = _material_codes(bom)
    assert "MAT-LED-MODULE" in codes
    ops = _operation_codes(bom)
    assert "led_install_letters" in ops


@pytest.mark.asyncio
async def test_lighting_only_unconfirmed_bom_excludes_adhesive_install(bom_context) -> None:
    bom = await bom_context(quote_input=_payload(sold=["LIGHTING"]))
    codes = _material_codes(bom)
    assert "MAT-LED-MODULE" in codes
    ops = _operation_codes(bom)
    assert "led_install_letters" not in ops


@pytest.mark.asyncio
async def test_lighting_external_install_by_us_bom(bom_context) -> None:
    bom = await bom_context(
        quote_input=_payload(
            sold=["LIGHTING"],
            confirmations=[CODE_LED_MOUNT_SURFACE_NOT_SOLD, CODE_LED_INSTALLATION_BY_US],
        ),
    )
    ops = _operation_codes(bom)
    assert "led_install_letters" in ops


@pytest.mark.asyncio
async def test_lighting_only_eic_cpp_install_gated(volumetric_v2_db) -> None:
    qi = _payload(sold=["LIGHTING"])
    eic = await EstimatedInternalCostService(volumetric_v2_db).build_preview(TEMPLATE, quote_input=qi)
    cpp = await CommercialPriceProposalService(volumetric_v2_db).build_preview(TEMPLATE, quote_input=qi)
    eic_codes = {line.code for line in eic.estimated_operation_lines}
    cpp_codes = {line.code for line in cpp.commercial_price_lines}
    assert "sistem_led_module" in cpp_codes
    assert "sistem_led_install" not in eic_codes


@pytest.mark.asyncio
async def test_back_lighting_eic_install_present(volumetric_v2_db) -> None:
    qi = _payload(sold=["BACK", "LIGHTING"])
    eic = await EstimatedInternalCostService(volumetric_v2_db).build_preview(TEMPLATE, quote_input=qi)
    eic_codes = {line.code for line in eic.estimated_operation_lines}
    assert "sistem_led_install" in eic_codes


def test_material_breakdown_filters_adhesive() -> None:
    payload = _payload(sold=["LIGHTING"])
    breakdown = IntakeV4MaterialBreakdownResponse(
        workspace_id="ws",
        template_code=TEMPLATE,
        material_rows=[],
        consumable_rows=[
            IntakeV4MaterialQuantityRow(
                material_key="led_modules",
                display_name="LED",
                category="consumable",
                quantity=10.0,
                unit="buc",
                quantity_source="test",
                quantity_quality="estimate",
                estimated_cost=50.0,
            ),
            IntakeV4MaterialQuantityRow(
                material_key="adhesive_led_modules",
                display_name="Adhesive",
                category="consumable",
                quantity=2.0,
                unit="ml",
                quantity_source="test",
                quantity_quality="estimate",
                estimated_cost=1.0,
            ),
        ],
        operation_rows=[],
        edge_cant_operation_rows=[],
        totals=IntakeV4MaterialBreakdownTotals(
            material_cost_total=51.0,
            estimated_cost_total=51.0,
            currency="EUR",
        ),
    )
    filtered = filter_material_breakdown_by_offer_scope(
        breakdown,
        payload_raw=payload,
        quote_input=payload,
    )
    keys = {row.material_key for row in filtered.consumable_rows}
    assert "led_modules" in keys
    assert "adhesive_led_modules" not in keys


def test_execution_lighting_only_excludes_led_install_task() -> None:
    ctx = read_execution_sold_scope(
        snapshot_with_scope(
            offer_scope=offer_scope(
                sold=["LIGHTING"],
                runtime=["sistem_led"],
            ),
        ),
    )
    assert include_task_rule_for_sold_scope(_rule("led_installation"), ctx=ctx) is False


def test_execution_back_lighting_includes_led_install_task() -> None:
    ctx = read_execution_sold_scope(
        snapshot_with_scope(
            offer_scope=offer_scope(
                sold=["BACK", "LIGHTING"],
                runtime=["debitare_spate", "sistem_led"],
            ),
        ),
    )
    assert include_task_rule_for_sold_scope(_rule("led_installation"), ctx=ctx) is True


def test_execution_external_install_confirmed_includes_task() -> None:
    scope = offer_scope(sold=["LIGHTING"], runtime=["sistem_led"])
    scope = scope.model_copy(
        update={"dependency_confirmations": [CODE_LED_MOUNT_SURFACE_NOT_SOLD, CODE_LED_INSTALLATION_BY_US]}
    )
    ctx = read_execution_sold_scope(snapshot_with_scope(offer_scope=scope))
    assert include_task_rule_for_sold_scope(_rule("led_installation"), ctx=ctx) is True
