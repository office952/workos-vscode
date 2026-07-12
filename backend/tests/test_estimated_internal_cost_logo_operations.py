"""EstimatedInternalCost linked-logo operation mapping from Cost BOM (blocker-only rates)."""

from __future__ import annotations

import inspect

import pytest
import pytest_asyncio

from schemas.aggregate_cost_bom import CostBomCostableOperation
from seeds.seed_tpl_volumetric_logo_v1 import seed_tpl_volumetric_logo_v1
from services.estimated_internal_cost_service import (
    ARTWORK_OWNED_LOGO_OPERATION_CODES,
    EstimatedInternalCostService,
    _estimate_logo_operation_quantity,
    _is_linked_logo_bom_operation,
    _resolve_logo_operation_internal_rate,
)
from services.template_architecture_scope import VOLUMETRIC_LOGO_TEMPLATE_CODE
from tests.eic_patched_bom_builder import FilteredLogoBomBuilder, PatchedAggregateCostBomBuilder
from tests.eic_workspace_logo_fixtures import (
    LOGO_INVENTORY,
    LOGO_MATERIAL_RATES,
    LOGO_INSTANCE_A,
    LOGO_INSTANCE_B,
    ROOT,
    add_workspace as _add_workspace,
    confirmed_bindings_payload as _confirmed_bindings_payload,
    gradi_payload as _gradi_payload,
    letters_only_payload as _letters_only_payload,
    quote_input_overlay as _quote_input_overlay,
    seed_logo_inventory_materials as _seed_logo_inventory_materials,
    seed_logo_template,
    single_logo_bindings_payload as _single_logo_bindings_payload,
)
from tests.test_product_aggregate_volumetric_v2 import _seed_volumetric_v2_fixture

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]


@pytest_asyncio.fixture
async def eic_logo_ops_db(volumetric_v2_db):
    await seed_logo_template(volumetric_v2_db)
    await _seed_logo_inventory_materials(volumetric_v2_db)
    return volumetric_v2_db


@pytest_asyncio.fixture
async def eic_logo_ops_service(eic_logo_ops_db):
    service = EstimatedInternalCostService(
        eic_logo_ops_db,
        bom_builder=PatchedAggregateCostBomBuilder(
            eic_logo_ops_db,
            material_rates=LOGO_MATERIAL_RATES,
            inventory_catalog=LOGO_INVENTORY,
        ),
    )

    async def _patched_load():
        return LOGO_MATERIAL_RATES, {"RON": "RON"}, {"WC_CNC_ROUTING": 120.0}, LOGO_INVENTORY

    service._load_pricing_context = _patched_load  # type: ignore[method-assign]
    return service


def _logo_operation_lines(preview):
    return [
        line
        for line in preview.estimated_operation_lines
        if line.component_code and "::" in line.component_code
    ]


def _letter_operation_lines(preview):
    return [
        line
        for line in preview.estimated_operation_lines
        if not line.component_code or "::" not in line.component_code
    ]


def test_linked_logo_operation_filter_accepts_namespaced_logo_row() -> None:
    op = CostBomCostableOperation(
        operation_code="logo_face_print",
        component_ref="comp_logo_finish::logo_instance_001",
        source_template_code=VOLUMETRIC_LOGO_TEMPLATE_CODE,
        provenance="linked_module",
    )
    assert _is_linked_logo_bom_operation(op) is True


def test_linked_logo_operation_filter_rejects_letters_row() -> None:
    op = CostBomCostableOperation(
        operation_code="debitare_fata",
        component_ref="comp_face_litere",
        source_template_code=ROOT,
        provenance="parent",
    )
    assert _is_linked_logo_bom_operation(op) is False


def test_linked_logo_operation_filter_rejects_logo_template_without_namespace() -> None:
    op = CostBomCostableOperation(
        operation_code="logo_face_print",
        component_ref="comp_logo_face",
        source_template_code=VOLUMETRIC_LOGO_TEMPLATE_CODE,
        provenance="linked_module",
    )
    assert _is_linked_logo_bom_operation(op) is False


def test_resolve_logo_print_rate_is_35_ron_m2() -> None:
    op = CostBomCostableOperation(
        operation_code="logo_face_print",
        component_ref="comp_logo_finish::logo_instance_001",
        source_template_code=VOLUMETRIC_LOGO_TEMPLATE_CODE,
        provenance="linked_module",
    )
    rate, rule_code, source = _resolve_logo_operation_internal_rate("logo_face_print", op=op)
    assert rate == pytest.approx(35.0)
    assert rule_code == "INT_LOGO_FACE_PRINT_M2"
    assert "logo_face_print" in source


def test_resolve_logo_laminate_rate_is_35_ron_m2() -> None:
    op = CostBomCostableOperation(
        operation_code="logo_face_laminate",
        component_ref="comp_logo_finish::logo_instance_001",
        source_template_code=VOLUMETRIC_LOGO_TEMPLATE_CODE,
        provenance="linked_module",
    )
    rate, rule_code, source = _resolve_logo_operation_internal_rate("logo_face_laminate", op=op)
    assert rate == pytest.approx(35.0)
    assert rule_code == "INT_LOGO_FACE_LAMINATE_M2"
    assert "logo_face_laminate" in source


def test_resolve_logo_application_rate_remains_missing() -> None:
    op = CostBomCostableOperation(
        operation_code="logo_finish_application",
        component_ref="comp_logo_finish::logo_instance_001",
        source_template_code=VOLUMETRIC_LOGO_TEMPLATE_CODE,
        provenance="linked_module",
    )
    rate, rule_code, source = _resolve_logo_operation_internal_rate("logo_finish_application", op=op)
    assert rate is None
    assert rule_code == "INT_LOGO_OP_RATE_MISSING"
    assert "missing" in source


def test_artwork_print_uses_same_segment_area_not_letters() -> None:
    payload = {
        "finish_setup": {
            "artwork_finishes": [
                {"layer_key": "logo_instance_001", "estimated_area_m2": 0.42},
                {"layer_key": "logo_instance_002", "estimated_area_m2": 0.38},
            ]
        },
        "quote_geometry": {"letter_face_area_m2": 3.05},
    }
    op = CostBomCostableOperation(
        operation_code="logo_face_print",
        formula_id="logo_area",
        component_ref="comp_logo_finish::logo_instance_001",
        source_template_code=VOLUMETRIC_LOGO_TEMPLATE_CODE,
        provenance="linked_module",
    )
    qty, _ = _estimate_logo_operation_quantity(op, payload, payload)
    assert qty == pytest.approx(0.42)

    op_dreapta = op.model_copy(update={"component_ref": "comp_logo_finish::logo_instance_002"})
    qty_dreapta, _ = _estimate_logo_operation_quantity(op_dreapta, payload, payload)
    assert qty_dreapta == pytest.approx(0.38)


def test_cnc_operation_does_not_use_artwork_area() -> None:
    payload = {
        "finish_setup": {
            "artwork_finishes": [
                {"layer_key": "logo_instance_001", "estimated_area_m2": 0.42},
            ]
        },
        "quote_geometry": {"letter_face_area_m2": 3.05},
    }
    op = CostBomCostableOperation(
        operation_code="logo_face_cnc_cut",
        formula_id="logo_area",
        component_ref="comp_logo_face::logo_instance_001",
        source_template_code=VOLUMETRIC_LOGO_TEMPLATE_CODE,
        provenance="linked_module",
    )
    qty, _ = _estimate_logo_operation_quantity(op, payload, payload)
    assert qty is None


def test_cnc_operation_uses_segment_geometry_area_when_present() -> None:
    payload = {
        "finish_setup": {
            "artwork_finishes": [
                {"layer_key": "logo_instance_001", "estimated_area_m2": 0.42, "svg_area_m2": 0.51},
            ]
        }
    }
    op = CostBomCostableOperation(
        operation_code="logo_face_cnc_cut",
        formula_id="logo_area",
        component_ref="comp_logo_face::logo_instance_001",
        source_template_code=VOLUMETRIC_LOGO_TEMPLATE_CODE,
        provenance="linked_module",
    )
    qty, warnings = _estimate_logo_operation_quantity(op, payload, payload)
    assert qty == pytest.approx(0.51)
    assert any("segment_geometry_area" in w for w in warnings)


def test_led_operation_uses_segment_module_count() -> None:
    payload = {
        "finish_setup": {
            "artwork_finishes": [
                {"layer_key": "logo_instance_001", "emblem_led_module_count": 4},
            ]
        }
    }
    op = CostBomCostableOperation(
        operation_code="logo_led_install",
        formula_id="logo_led_modules",
        component_ref="comp_logo_lighting::logo_instance_001",
        source_template_code=VOLUMETRIC_LOGO_TEMPLATE_CODE,
        provenance="linked_module",
    )
    qty, _ = _estimate_logo_operation_quantity(op, payload, payload)
    assert qty == 4


def test_artwork_owned_operation_codes_include_application() -> None:
    assert "logo_finish_application" in ARTWORK_OWNED_LOGO_OPERATION_CODES
    assert "logo_face_cnc_cut" not in ARTWORK_OWNED_LOGO_OPERATION_CODES


@pytest.mark.asyncio
async def test_letters_operation_lines_unchanged_with_workspace_logos(eic_logo_ops_service, eic_logo_ops_db) -> None:
    payload = _confirmed_bindings_payload()
    quote = _quote_input_overlay(payload)
    template_preview = await eic_logo_ops_service.build_preview(ROOT, quote_input=quote)
    workspace_id = await _add_workspace(eic_logo_ops_db, payload)
    workspace_preview = await eic_logo_ops_service.build_preview(
        ROOT,
        workspace_id=workspace_id,
        quote_input=quote,
    )
    assert template_preview is not None
    assert workspace_preview is not None

    template_letters = _letter_operation_lines(template_preview)
    workspace_letters = _letter_operation_lines(workspace_preview)
    assert {line.code for line in template_letters} == {line.code for line in workspace_letters}
    for t_line in template_letters:
        w_line = next(line for line in workspace_letters if line.code == t_line.code)
        assert w_line.subtotal == t_line.subtotal
        assert w_line.quantity == t_line.quantity
        assert w_line.internal_unit_cost == t_line.internal_unit_cost


@pytest.mark.asyncio
async def test_letters_only_workspace_matches_template_letter_operations(
    eic_logo_ops_service, eic_logo_ops_db
) -> None:
    payload = _letters_only_payload()
    quote = _quote_input_overlay(payload)
    template_preview = await eic_logo_ops_service.build_preview(ROOT, quote_input=quote)
    workspace_id = await _add_workspace(eic_logo_ops_db, payload)
    workspace_preview = await eic_logo_ops_service.build_preview(
        ROOT,
        workspace_id=workspace_id,
        quote_input=quote,
    )
    assert template_preview is not None
    assert workspace_preview is not None
    assert _letter_operation_lines(template_preview) == _letter_operation_lines(workspace_preview)
    assert _logo_operation_lines(workspace_preview) == []


@pytest.mark.asyncio
async def test_two_logo_segments_produce_separate_operation_lines(eic_logo_ops_service, eic_logo_ops_db) -> None:
    workspace_id = await _add_workspace(eic_logo_ops_db, _confirmed_bindings_payload())
    preview = await eic_logo_ops_service.build_preview(
        ROOT,
        workspace_id=workspace_id,
        quote_input=_quote_input_overlay(_confirmed_bindings_payload()),
    )
    assert preview is not None
    logo_ops = _logo_operation_lines(preview)
    assert logo_ops

    print_ops = [line for line in logo_ops if line.code == "operation_logo_face_print"]
    assert len(print_ops) == 2
    refs = {line.component_code for line in print_ops}
    assert "comp_logo_finish::logo_instance_001" in refs
    assert "comp_logo_finish::logo_instance_002" in refs


@pytest.mark.asyncio
async def test_logo_print_and_laminate_subtotals_configured_application_remains_blocker(
    eic_logo_ops_service, eic_logo_ops_db
) -> None:
    workspace_id = await _add_workspace(eic_logo_ops_db, _confirmed_bindings_payload())
    preview = await eic_logo_ops_service.build_preview(
        ROOT,
        workspace_id=workspace_id,
        quote_input=_quote_input_overlay(_confirmed_bindings_payload()),
    )
    assert preview is not None
    logo_ops = _logo_operation_lines(preview)
    assert logo_ops

    print_ops = [line for line in logo_ops if line.code == "operation_logo_face_print"]
    lam_ops = [line for line in logo_ops if line.code == "operation_logo_face_laminate"]
    app_ops = [line for line in logo_ops if line.code == "operation_logo_finish_application"]
    assert len(print_ops) == 2
    assert len(lam_ops) == 2
    assert len(app_ops) == 2

    for line in print_ops + lam_ops:
        assert line.internal_unit_cost == pytest.approx(35.0)
        assert line.subtotal is not None
        assert line.subtotal > 0

    subtotals_by_ref = {
        (line.component_code, line.code): line.subtotal
        for line in print_ops + lam_ops
    }
    assert subtotals_by_ref[("comp_logo_finish::logo_instance_001", "operation_logo_face_print")] == pytest.approx(14.70)
    assert subtotals_by_ref[("comp_logo_finish::logo_instance_001", "operation_logo_face_laminate")] == pytest.approx(14.70)
    assert subtotals_by_ref[("comp_logo_finish::logo_instance_002", "operation_logo_face_print")] == pytest.approx(13.30)
    assert subtotals_by_ref[("comp_logo_finish::logo_instance_002", "operation_logo_face_laminate")] == pytest.approx(13.30)

    for line in app_ops:
        assert line.internal_unit_cost is None
        assert line.subtotal is None

    blocker_codes = {b.code for b in preview.internal_blockers}
    assert "INTERNAL_OPERATION_RULE_MISSING" in blocker_codes
    assert preview.status == "blocked"
    assert preview.ready_for_quote_snapshot is False


@pytest.mark.asyncio
async def test_material_and_operation_lines_remain_separate(eic_logo_ops_service, eic_logo_ops_db) -> None:
    workspace_id = await _add_workspace(eic_logo_ops_db, _confirmed_bindings_payload())
    preview = await eic_logo_ops_service.build_preview(
        ROOT,
        workspace_id=workspace_id,
        quote_input=_quote_input_overlay(_confirmed_bindings_payload()),
    )
    assert preview is not None
    logo_materials = [
        line
        for line in preview.estimated_material_lines
        if line.component_code and "::" in line.component_code
    ]
    print_materials = [line for line in logo_materials if line.code == "material_print_media"]
    lam_materials = [line for line in logo_materials if line.code == "material_laminate_media"]
    assert len(print_materials) == 2
    assert len(lam_materials) == 2
    for line in print_materials:
        assert line.internal_unit_cost == pytest.approx(5.0)
        assert line.subtotal is not None
    logo_ops = _logo_operation_lines(preview)
    assert len([line for line in logo_ops if line.code == "operation_logo_face_print"]) == 2
    assert len([line for line in logo_ops if line.code == "operation_logo_face_laminate"]) == 2


@pytest.mark.asyncio
async def test_print_only_partial_state_via_filtered_bom(eic_logo_ops_db) -> None:
    service = EstimatedInternalCostService(
        eic_logo_ops_db,
        bom_builder=FilteredLogoBomBuilder(
            eic_logo_ops_db,
            material_rates=LOGO_MATERIAL_RATES,
            inventory_catalog=LOGO_INVENTORY,
            allowed_logo_operation_codes=frozenset({"logo_face_print"}),
            allowed_logo_material_codes=frozenset({"print_media"}),
        ),
    )

    async def _patched_load():
        return LOGO_MATERIAL_RATES, {"RON": "RON"}, {"WC_CNC_ROUTING": 120.0}, LOGO_INVENTORY

    service._load_pricing_context = _patched_load  # type: ignore[method-assign]
    payload = _single_logo_bindings_payload(execution_type="print")
    workspace_id = await _add_workspace(eic_logo_ops_db, payload)
    preview = await service.build_preview(ROOT, workspace_id=workspace_id, quote_input=_quote_input_overlay(payload))
    assert preview is not None
    logo_materials = [
        line for line in preview.estimated_material_lines if line.component_code and "::" in line.component_code
    ]
    logo_ops = _logo_operation_lines(preview)
    assert len([line for line in logo_materials if line.code == "material_print_media"]) == 1
    assert len([line for line in logo_materials if line.code == "material_laminate_media"]) == 0
    assert len([line for line in logo_ops if line.code == "operation_logo_face_print"]) == 1
    assert len([line for line in logo_ops if line.code == "operation_logo_face_laminate"]) == 0
    assert len([line for line in logo_ops if line.code == "operation_logo_finish_application"]) == 0
    print_line = next(line for line in logo_ops if line.code == "operation_logo_face_print")
    assert print_line.subtotal == pytest.approx(14.70)


@pytest.mark.asyncio
async def test_application_inactive_partial_state_via_filtered_bom(eic_logo_ops_db) -> None:
    service = EstimatedInternalCostService(
        eic_logo_ops_db,
        bom_builder=FilteredLogoBomBuilder(
            eic_logo_ops_db,
            material_rates=LOGO_MATERIAL_RATES,
            inventory_catalog=LOGO_INVENTORY,
            allowed_logo_operation_codes=frozenset({"logo_face_print", "logo_face_laminate"}),
            allowed_logo_material_codes=frozenset({"print_media", "laminate_media"}),
        ),
    )

    async def _patched_load():
        return LOGO_MATERIAL_RATES, {"RON": "RON"}, {"WC_CNC_ROUTING": 120.0}, LOGO_INVENTORY

    service._load_pricing_context = _patched_load  # type: ignore[method-assign]
    payload = _single_logo_bindings_payload()
    workspace_id = await _add_workspace(eic_logo_ops_db, payload)
    preview = await service.build_preview(ROOT, workspace_id=workspace_id, quote_input=_quote_input_overlay(payload))
    assert preview is not None
    logo_ops = _logo_operation_lines(preview)
    assert len([line for line in logo_ops if line.code == "operation_logo_finish_application"]) == 0
    assert all(
        line.subtotal == pytest.approx(14.70)
        for line in logo_ops
        if line.code in {"operation_logo_face_print", "operation_logo_face_laminate"}
    )
    assert not any(b.code == "INTERNAL_OPERATION_RULE_MISSING" for b in preview.internal_blockers)


@pytest.mark.asyncio
async def test_logo_operation_preserves_provenance_fields(eic_logo_ops_service, eic_logo_ops_db) -> None:
    workspace_id = await _add_workspace(eic_logo_ops_db, _confirmed_bindings_payload())
    preview = await eic_logo_ops_service.build_preview(
        ROOT,
        workspace_id=workspace_id,
        quote_input=_quote_input_overlay(_confirmed_bindings_payload()),
    )
    assert preview is not None
    logo_ops = _logo_operation_lines(preview)
    assert logo_ops
    for line in logo_ops:
        assert line.component_code and "::" in line.component_code
        assert any("source_template_code=" in w for w in line.warnings)


@pytest.mark.asyncio
async def test_partial_finish_does_not_invent_logo_operations(eic_logo_ops_service, eic_logo_ops_db) -> None:
    payload = _confirmed_bindings_payload()
    payload["finish_setup"]["artwork_finishes"][0]["confirmed"] = False
    payload["finish_setup"]["artwork_finishes"][1]["confirmed"] = False
    workspace_id = await _add_workspace(eic_logo_ops_db, payload)
    preview = await eic_logo_ops_service.build_preview(ROOT, workspace_id=workspace_id)
    assert preview is not None
    assert _logo_operation_lines(preview) == []
    assert preview.status == "partial"
    assert _letter_operation_lines(preview)


@pytest.mark.asyncio
async def test_missing_binding_does_not_invent_logo_operations(eic_logo_ops_service, eic_logo_ops_db) -> None:
    workspace_id = await _add_workspace(eic_logo_ops_db, _gradi_payload())
    preview = await eic_logo_ops_service.build_preview(ROOT, workspace_id=workspace_id)
    assert preview is not None
    assert _logo_operation_lines(preview) == []


@pytest.mark.asyncio
async def test_no_commercial_fields_on_logo_operation_preview(eic_logo_ops_service, eic_logo_ops_db) -> None:
    workspace_id = await _add_workspace(eic_logo_ops_db, _confirmed_bindings_payload())
    preview = await eic_logo_ops_service.build_preview(
        ROOT,
        workspace_id=workspace_id,
        quote_input=_quote_input_overlay(_confirmed_bindings_payload()),
    )
    assert preview is not None
    dumped = preview.model_dump()
    for key in ("commercial_price", "client_price", "offer_price", "markup", "margin", "vat"):
        assert key not in dumped


def test_eic_module_has_no_binding_or_recommendation_imports() -> None:
    from services import estimated_internal_cost_service as module

    source = inspect.getsource(module)
    forbidden = (
        "intake_v6_layer_binding_persistence",
        "product_composition_recommendation",
        "persist_logo_layer_bindings",
        "apply_product_composition_recommendation",
    )
    for token in forbidden:
        assert token not in source


def test_post_eic_preview_endpoint_logo_print_lam_rates_and_application_blocker(volumetric_auth_client, db_fixture):
    payload = _confirmed_bindings_payload()

    async def _seed():
        async with db_fixture.session_maker() as session:
            await _seed_volumetric_v2_fixture(session)
            await seed_tpl_volumetric_logo_v1()
            await _seed_logo_inventory_materials(session)
            return await _add_workspace(session, payload)

    workspace_id = db_fixture.run(_seed())
    response = volumetric_auth_client.post(
        f"/api/v1/product-system/estimated-internal-cost-preview/{ROOT}",
        json={"workspace_id": workspace_id, "quote_input": _quote_input_overlay(payload)},
    )
    assert response.status_code == 200
    body = response.json()
    logo_ops = [
        line
        for line in body.get("estimated_operation_lines", [])
        if "::" in (line.get("component_code") or "")
    ]
    assert logo_ops
    print_ops = [line for line in logo_ops if line.get("code") == "operation_logo_face_print"]
    lam_ops = [line for line in logo_ops if line.get("code") == "operation_logo_face_laminate"]
    app_ops = [line for line in logo_ops if line.get("code") == "operation_logo_finish_application"]
    assert print_ops and lam_ops and app_ops
    assert all(line.get("internal_unit_cost") == 35.0 for line in print_ops + lam_ops)
    assert all(line.get("subtotal") is not None for line in print_ops + lam_ops)
    assert all(line.get("internal_unit_cost") is None for line in app_ops)
    assert all(line.get("subtotal") is None for line in app_ops)
    assert any(b.get("code") == "INTERNAL_OPERATION_RULE_MISSING" for b in body.get("internal_blockers", []))
    assert body.get("status") == "blocked"
    assert body.get("ready_for_quote_snapshot") is False
    assert "commercial_price" not in body
