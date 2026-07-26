"""Live calculation paths must honor persisted workspace offer_scope."""

from __future__ import annotations

import copy
import json
import uuid

import pytest

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from schemas.intake_v4 import (
    IntakeV4MaterialBreakdownResponse,
    IntakeV4MaterialBreakdownTotals,
    IntakeV4MaterialQuantityRow,
)
from schemas.auth import UserResponse
from services.intake_v6_offer_scope_live_calc_service import (
    filter_logical_list_rows_by_offer_scope,
    filter_material_breakdown_by_offer_scope,
    merge_workspace_offer_scope_into_quote_input,
)
from services.intake_v6_priced_quote_dry_run_service import build_intake_v6_priced_quote_dry_run
from services.intake_v6_pricing_input_service import build_v6_pricing_input_preview
from services.intake_v6_workspace_service import (
    _parse_payload,
    get_intake_v6_workspace,
    save_offer_scope_for_intake_v6_workspace,
)
from tests.eic_workspace_logo_fixtures import confirmed_bindings_payload

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


def _modules_in_cpp_lines(lines: list[dict]) -> set[str]:
    return {str(line.get("module_code")) for line in lines if line.get("module_code")}

async def _seed_workspace(db, *, offer_scope: dict | None = None) -> str:
    payload = copy.deepcopy(confirmed_bindings_payload())
    payload["product_composition_confirmed"] = {"confirmed": True}
    payload["svg_source"]["file_hash"] = "test-hash-gradi-live-scope"
    if offer_scope is not None:
        payload["offer_scope"] = offer_scope
        payload["offer_scope_confirmed"] = {"confirmed": True}
    workspace_id = str(uuid.uuid4())
    db.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"IV6-LIVE-SCOPE-{workspace_id[:8]}",
            title="Live calc offer scope",
            template_code=TEMPLATE,
            status="ready_for_quote_preview",
            payload_json=json.dumps(payload),
        )
    )
    await db.commit()
    return workspace_id


@pytest.mark.asyncio
async def test_merge_workspace_offer_scope_into_quote_input(volumetric_v2_db) -> None:
    payload_raw = {"offer_scope": _offer_scope(mode="component_subset", sold=["BACK"])}
    merged = merge_workspace_offer_scope_into_quote_input(payload_raw, {"analysis_ready": True})
    assert merged["offer_scope"]["sold_modules"] == ["BACK"]


@pytest.mark.asyncio
async def test_pricing_preview_includes_workspace_offer_scope(volumetric_v2_db) -> None:
    workspace_id = await _seed_workspace(
        volumetric_v2_db,
        offer_scope=_offer_scope(mode="component_subset", sold=["FACE"]),
    )
    record = await get_intake_v6_workspace(volumetric_v2_db, workspace_id)
    payload_raw = record.payload if isinstance(record.payload, dict) else {}
    preview = build_v6_pricing_input_preview(
        workspace_id=workspace_id,
        payload=_parse_payload(payload_raw),
        template_code=TEMPLATE,
        payload_raw=payload_raw,
    )
    assert preview.quote_input_payload.get("offer_scope", {}).get("sold_modules") == ["FACE"]


@pytest.mark.asyncio
async def test_legacy_workspace_without_offer_scope_unchanged_module_breadth(volumetric_v2_db) -> None:
    baseline_id = await _seed_workspace(volumetric_v2_db, offer_scope=None)
    explicit_id = await _seed_workspace(
        volumetric_v2_db,
        offer_scope=_offer_scope(mode="full_product", sold=[]),
    )
    baseline = await build_intake_v6_priced_quote_dry_run(volumetric_v2_db, baseline_id)
    explicit = await build_intake_v6_priced_quote_dry_run(volumetric_v2_db, explicit_id)
    assert _modules_in_cpp_lines(baseline["commercial_line_items"]) == _modules_in_cpp_lines(
        explicit["commercial_line_items"]
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("sold", "allowed", "forbidden"),
    [
        (["FACE"], {"debitare_fata"}, {"modelare_cant", "debitare_spate", "sistem_led", "finisaje"}),
        (["RETURN-CANT"], {"modelare_cant"}, {"debitare_fata", "debitare_spate", "sistem_led", "finisaje"}),
        (["BACK"], {"debitare_spate"}, {"debitare_fata", "modelare_cant", "sistem_led", "finisaje"}),
        (
            ["FACE", "RETURN-CANT"],
            {"debitare_fata", "modelare_cant"},
            {"debitare_spate", "sistem_led", "finisaje"},
        ),
    ],
)
async def test_live_calc_paths_filter_by_offer_scope(
    volumetric_v2_db,
    sold: list[str],
    allowed: set[str],
    forbidden: set[str],
) -> None:
    workspace_id = await _seed_workspace(
        volumetric_v2_db,
        offer_scope=_offer_scope(mode="component_subset", sold=sold),
    )
    dry_run = await build_intake_v6_priced_quote_dry_run(volumetric_v2_db, workspace_id)
    cpp_modules = _modules_in_cpp_lines(dry_run["commercial_line_items"])
    assert allowed <= cpp_modules
    assert not cpp_modules & forbidden


def test_filter_material_breakdown_and_logical_rows_for_back_only() -> None:
    payload_raw = {
        "offer_scope": _offer_scope(mode="component_subset", sold=["BACK"]),
        "finish_setup": {"illuminated": True, "lighting_system_type": "front_lit"},
    }
    breakdown = IntakeV4MaterialBreakdownResponse(
        workspace_id="ws",
        template_code=TEMPLATE,
        material_rows=[
            IntakeV4MaterialQuantityRow(
                material_key="plexiglas_face",
                display_name="Face",
                category="material",
                quantity=1.0,
                unit="m2",
                quantity_source="test",
                quantity_quality="estimate",
                estimated_cost=10.0,
            ),
            IntakeV4MaterialQuantityRow(
                material_key="forex_backing",
                display_name="Back",
                category="material",
                quantity=1.0,
                unit="m2",
                quantity_source="test",
                quantity_quality="estimate",
                estimated_cost=5.0,
            ),
        ],
        consumable_rows=[],
        operation_rows=[],
        edge_cant_operation_rows=[],
        totals=IntakeV4MaterialBreakdownTotals(
            material_cost_total=15.0,
            estimated_cost_total=15.0,
            currency="EUR",
        ),
        warnings=[],
    )
    filtered = filter_material_breakdown_by_offer_scope(breakdown, payload_raw=payload_raw)
    keys = {row.material_key for row in filtered.material_rows}
    assert keys == {"forex_backing"}
    assert filtered.totals.estimated_cost_total == 5.0

    rows = [
        {"line_id": "material.plexiglas_face", "module_code": "debitare_fata"},
        {"line_id": "material.forex_backing", "module_code": "debitare_spate"},
        {"line_id": "material.led_modules", "module_code": "sistem_led"},
    ]
    logical = filter_logical_list_rows_by_offer_scope(rows, payload_raw=payload_raw)
    assert {row["line_id"] for row in logical} == {"material.forex_backing"}


@pytest.mark.asyncio
async def test_workspace_reload_preserves_calculation_scope(volumetric_v2_db) -> None:
    workspace_id = await _seed_workspace(
        volumetric_v2_db,
        offer_scope=_offer_scope(mode="component_subset", sold=["BACK"]),
    )
    first = await build_intake_v6_priced_quote_dry_run(volumetric_v2_db, workspace_id)
    reloaded = await get_intake_v6_workspace(volumetric_v2_db, workspace_id)
    scope = reloaded.payload.get("offer_scope") if isinstance(reloaded.payload, dict) else None
    assert scope is not None
    assert scope.get("sold_modules") == ["BACK"]
    second = await build_intake_v6_priced_quote_dry_run(volumetric_v2_db, workspace_id)
    assert _modules_in_cpp_lines(first["commercial_line_items"]) == _modules_in_cpp_lines(
        second["commercial_line_items"]
    )


@pytest.mark.asyncio
async def test_save_offer_scope_then_live_calc_filters(volumetric_v2_db) -> None:
    workspace_id = await _seed_workspace(volumetric_v2_db, offer_scope=None)
    full = await build_intake_v6_priced_quote_dry_run(volumetric_v2_db, workspace_id)
    assert "modelare_cant" in _modules_in_cpp_lines(full["commercial_line_items"])

    await save_offer_scope_for_intake_v6_workspace(
        volumetric_v2_db,
        workspace_id,
        mode="component_subset",
        sold_modules=["RETURN-CANT"],
        confirmed=True,
        current_user=_user(),
    )
    scoped = await build_intake_v6_priced_quote_dry_run(volumetric_v2_db, workspace_id)
    modules = _modules_in_cpp_lines(scoped["commercial_line_items"])
    assert modules == {"modelare_cant"} or ("modelare_cant" in modules and "debitare_fata" not in modules)
