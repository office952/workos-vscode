"""EstimatedInternalCost wiring for workspace-aware Cost BOM linked logo segments."""

from __future__ import annotations

import inspect
import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from seeds.seed_tpl_volumetric_logo_v1 import seed_tpl_volumetric_logo_v1
from services.aggregate_cost_bom_adapter import AggregateCostBomBuilderService
from services.estimated_internal_cost_service import (
    ARTWORK_OWNED_LOGO_MATERIAL_CODES,
    EstimatedInternalCostService,
    WARNING_LINKED_SEGMENT_FINISH_PARTIAL,
    _estimate_material_quantity,
)
from services.intake_v6_layer_binding_persistence_service import (
    persist_logo_layer_bindings_from_composition_confirmation,
)
from services.intake_v6_product_composition_recommendation_service import (
    LOGO_TEMPLATE_CODE,
    apply_product_composition_recommendation,
)
from services.product_aggregate_service import ProductAggregateService
from services.product_aggregate_workspace_composition_service import WARNING_FINISH_PARTIAL
from services.template_architecture_scope import VOLUMETRIC_LOGO_TEMPLATE_CODE
from schemas.aggregate_cost_bom import CostBomCostableMaterial
from tests.eic_patched_bom_builder import PatchedAggregateCostBomBuilder
from tests.test_aggregate_cost_bom_adapter import INVENTORY_CATALOG, SAMPLE_RATES
from tests.test_product_aggregate_volumetric_v2 import _seed_volumetric_v2_fixture

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

ROOT = "TPL-VOLUMETRIC-LETTERS_v2"
LOGO = LOGO_TEMPLATE_CODE

LOGO_MATERIAL_RATES = {
    **SAMPLE_RATES,
    "print_media": 5.0,
    "laminate_media": 4.0,
    "logo_face_material": 12.0,
    "logo_return_profile": 3.0,
    "logo_back_material": 8.0,
}

LOGO_INVENTORY = {
    **INVENTORY_CATALOG,
    **{code: {"status": "active", "unit_cost": rate} for code, rate in LOGO_MATERIAL_RATES.items()},
}


def _layer(key: str, name: str, role: str) -> dict:
    return {
        "layer_key": key,
        "layer_id": key,
        "layer_name": name,
        "auto_role": role,
        "confirmed_role": role,
        "confirmation_state": "confirmed",
        "auto_confidence": "high",
    }


def _gradi_payload(*, finish_confirmed: bool = True) -> dict:
    payload = {
        "analysis_ready": True,
        "product_binding": {"template_code": ROOT},
        "svg_source": {"file_name": "gradi-curat.svg", "file_size_bytes": 27173, "upload_status": "analyzed"},
        "quote_geometry": {"letter_count": 19, "letter_perimeter_m": 31.638, "letter_face_area_m2": 3.05},
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                _layer("letters", "Litere GRADI", "face"),
                _layer("logo-stanga", "logo stanga", "printed_artwork"),
                _layer("logo-dreapta", "logo dreapta", "printed_artwork"),
            ],
            "layer_bindings": [],
            "warnings": [],
        },
        "finish_setup": {
            "confirmed": True,
            "face_finish_type": "oracal_651",
            "return_depth_mm": 60,
            "return_finish_type": "white_aluminum",
            "artwork_finishes": [
                {
                    "layer_key": "logo-stanga",
                    "layer_name": "logo stanga",
                    "execution_type": "print_laminate",
                    "color_mode": "polychrome",
                    "return_depth_mm": 60,
                    "estimated_area_m2": 0.42,
                    "confirmed": finish_confirmed,
                },
                {
                    "layer_key": "logo-dreapta",
                    "layer_name": "logo dreapta",
                    "execution_type": "print_laminate",
                    "color_mode": "polychrome",
                    "return_depth_mm": 60,
                    "estimated_area_m2": 0.38,
                    "confirmed": finish_confirmed,
                },
            ],
        },
    }
    apply_product_composition_recommendation(payload)
    return payload


def _confirmed_bindings_payload() -> dict:
    payload = _gradi_payload()
    items = payload["product_composition_recommendation"]["composition_items"]
    persist_logo_layer_bindings_from_composition_confirmation(payload, confirmed=True, confirmed_items=items)
    payload["product_composition_confirmed"] = {"confirmed": True, "items": items}
    return payload


def _letters_only_payload() -> dict:
    payload = {
        "analysis_ready": True,
        "product_binding": {"template_code": ROOT},
        "svg_source": {"file_name": "letters.svg", "file_size_bytes": 1000, "upload_status": "analyzed"},
        "quote_geometry": {"letter_count": 5, "letter_perimeter_m": 2.0, "letter_face_area_m2": 0.5},
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [_layer("letters", "Litere", "face")],
            "layer_bindings": [],
            "warnings": [],
        },
        "finish_setup": {
            "confirmed": True,
            "face_finish_type": "oracal_651",
            "return_depth_mm": 60,
            "return_finish_type": "white_aluminum",
            "artwork_finishes": [],
        },
    }
    apply_product_composition_recommendation(payload)
    return payload


def _quote_input_overlay(payload: dict) -> dict:
    return {
        "analysis_ready": payload.get("analysis_ready"),
        "quote_geometry": dict(payload.get("quote_geometry") or {}),
        "finish_setup": dict(payload.get("finish_setup") or {}),
    }


async def _seed_logo_template(session) -> None:
    await seed_tpl_volumetric_logo_v1()


async def _seed_logo_inventory_materials(session) -> None:
    from models.inventory_materials import Inventory_materials

    for code, rate in LOGO_MATERIAL_RATES.items():
        session.add(
            Inventory_materials(
                code=code,
                name=code,
                unit="buc",
                unit_cost=rate,
                status="active",
                currency="RON",
            )
        )
    await session.commit()


async def _add_workspace(session, payload: dict) -> str:
    workspace_id = str(uuid.uuid4())
    session.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"WS-EIC-{workspace_id[:8]}",
            title="EIC workspace linked logo",
            template_code=ROOT,
            status="draft",
            payload_json=json.dumps(payload),
        )
    )
    await session.commit()
    return workspace_id


@pytest_asyncio.fixture
async def eic_workspace_db(volumetric_v2_db):
    await _seed_logo_template(volumetric_v2_db)
    await _seed_logo_inventory_materials(volumetric_v2_db)
    return volumetric_v2_db


@pytest_asyncio.fixture
async def eic_service(eic_workspace_db):
    service = EstimatedInternalCostService(
        eic_workspace_db,
        bom_builder=PatchedAggregateCostBomBuilder(
            eic_workspace_db,
            material_rates=LOGO_MATERIAL_RATES,
            inventory_catalog=LOGO_INVENTORY,
        ),
    )

    async def _patched_load():
        return LOGO_MATERIAL_RATES, {"RON": "RON"}, {"WC_CNC_ROUTING": 120.0}, LOGO_INVENTORY

    service._load_pricing_context = _patched_load  # type: ignore[method-assign]
    return service


def _logo_material_lines(preview):
    return [
        line
        for line in preview.estimated_material_lines
        if line.component_code and "::" in line.component_code
    ]


@pytest.mark.asyncio
async def test_eic_uses_cost_bom_builder_when_workspace_id_present(eic_workspace_db) -> None:
    workspace_id = await _add_workspace(eic_workspace_db, _confirmed_bindings_payload())
    service = EstimatedInternalCostService(eic_workspace_db)
    with patch.object(
        AggregateCostBomBuilderService,
        "build_preview",
        new_callable=AsyncMock,
        wraps=AggregateCostBomBuilderService(eic_workspace_db).build_preview,
    ) as build_preview:
        preview = await service.build_preview(ROOT, workspace_id=workspace_id)
        assert preview is not None
        build_preview.assert_awaited_once()
        assert build_preview.await_args.kwargs.get("workspace_id") == workspace_id


@pytest.mark.asyncio
async def test_eic_does_not_build_template_only_bom_on_workspace_path(eic_workspace_db) -> None:
    workspace_id = await _add_workspace(eic_workspace_db, _confirmed_bindings_payload())
    service = EstimatedInternalCostService(
        eic_workspace_db,
        bom_builder=PatchedAggregateCostBomBuilder(
            eic_workspace_db,
            material_rates=LOGO_MATERIAL_RATES,
            inventory_catalog=LOGO_INVENTORY,
        ),
    )
    real_svc = ProductAggregateService(eic_workspace_db)
    with patch.object(
        ProductAggregateService,
        "build_for_workspace",
        new_callable=AsyncMock,
        side_effect=real_svc.build_for_workspace,
    ) as build_for_workspace:
        preview = await service.build_preview(
            ROOT,
            workspace_id=workspace_id,
            quote_input=_quote_input_overlay(_confirmed_bindings_payload()),
        )
        assert preview is not None
        build_for_workspace.assert_awaited_once_with(ROOT, workspace_id)


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


@pytest.mark.asyncio
async def test_letters_only_workspace_matches_template_eic(eic_service, eic_workspace_db) -> None:
    workspace_id = await _add_workspace(eic_workspace_db, _letters_only_payload())
    template_preview = await eic_service.build_preview(ROOT)
    workspace_preview = await eic_service.build_preview(ROOT, workspace_id=workspace_id)
    assert template_preview is not None and workspace_preview is not None
    assert not _logo_material_lines(workspace_preview)
    template_non_logo = {
        (line.code, line.component_code)
        for line in template_preview.estimated_material_lines
        if not (line.component_code and "::" in line.component_code)
    }
    workspace_non_logo = {
        (line.code, line.component_code)
        for line in workspace_preview.estimated_material_lines
        if not (line.component_code and "::" in line.component_code)
    }
    assert template_non_logo <= workspace_non_logo


@pytest.mark.asyncio
async def test_two_logo_segments_produce_distinct_material_lines(eic_service, eic_workspace_db) -> None:
    workspace_id = await _add_workspace(eic_workspace_db, _confirmed_bindings_payload())
    payload = _confirmed_bindings_payload()
    preview = await eic_service.build_preview(
        ROOT,
        workspace_id=workspace_id,
        quote_input=_quote_input_overlay(payload),
    )
    assert preview is not None
    logo_lines = _logo_material_lines(preview)
    assert logo_lines
    stanga = [line for line in logo_lines if "logo-stanga" in (line.component_code or "")]
    dreapta = [line for line in logo_lines if "logo-dreapta" in (line.component_code or "")]
    assert stanga and dreapta
    assert {line.component_code for line in stanga}.isdisjoint({line.component_code for line in dreapta})


@pytest.mark.asyncio
async def test_missing_binding_creates_no_logo_cost_lines(eic_service, eic_workspace_db) -> None:
    workspace_id = await _add_workspace(eic_workspace_db, _gradi_payload())
    preview = await eic_service.build_preview(ROOT, workspace_id=workspace_id)
    assert preview is not None
    assert not _logo_material_lines(preview)


@pytest.mark.asyncio
async def test_missing_finish_partial_status_without_fabricated_logo_cost(eic_service, eic_workspace_db) -> None:
    payload = _confirmed_bindings_payload()
    payload["finish_setup"]["artwork_finishes"][0]["confirmed"] = False
    payload["finish_setup"]["artwork_finishes"][1]["confirmed"] = False
    workspace_id = await _add_workspace(eic_workspace_db, payload)
    preview = await eic_service.build_preview(ROOT, workspace_id=workspace_id)
    assert preview is not None
    assert preview.status == "partial"
    assert not _logo_material_lines(preview)
    assert any(WARNING_FINISH_PARTIAL in w or WARNING_LINKED_SEGMENT_FINISH_PARTIAL in w for w in preview.warnings)
    assert preview.estimated_material_lines


@pytest.mark.asyncio
async def test_artwork_area_used_for_print_not_logo_face_material() -> None:
    payload = _quote_input_overlay(_confirmed_bindings_payload())
    print_mat = CostBomCostableMaterial(
        material_code="print_media",
        component_ref="comp_logo_finish::logo-stanga",
        source_template_code=VOLUMETRIC_LOGO_TEMPLATE_CODE,
        provenance="linked_module",
        unit="mp",
        pricing_availability="available",
        unit_cost=5.0,
    )
    face_mat = CostBomCostableMaterial(
        material_code="logo_face_material",
        component_ref="comp_logo_face::logo-stanga",
        source_template_code=VOLUMETRIC_LOGO_TEMPLATE_CODE,
        provenance="linked_module",
        unit="mp",
        pricing_availability="available",
        unit_cost=12.0,
    )
    print_qty, _ = _estimate_material_quantity(print_mat, payload, {})
    face_qty, _ = _estimate_material_quantity(face_mat, payload, {})
    assert print_qty == 0.42
    assert face_qty is None


@pytest.mark.asyncio
async def test_letter_area_not_used_for_logo_print() -> None:
    payload = {
        "quote_geometry": {"letter_face_area_m2": 3.05},
        "finish_setup": {"artwork_finishes": []},
    }
    print_mat = CostBomCostableMaterial(
        material_code="print_media",
        component_ref="comp_logo_finish::logo-stanga",
        source_template_code=VOLUMETRIC_LOGO_TEMPLATE_CODE,
        provenance="linked_module",
        unit="mp",
        pricing_availability="available",
        unit_cost=5.0,
    )
    qty, _ = _estimate_material_quantity(print_mat, payload, {"letter_face_area_m2": 3.05})
    assert qty is None


@pytest.mark.asyncio
async def test_missing_material_rate_is_explicit_blocker(eic_workspace_db) -> None:
    service = EstimatedInternalCostService(
        eic_workspace_db,
        bom_builder=PatchedAggregateCostBomBuilder(
            eic_workspace_db,
            material_rates={},
            inventory_catalog={},
        ),
    )

    async def _empty():
        return {}, {}, {}, {}

    service._load_pricing_context = _empty  # type: ignore[method-assign]
    workspace_id = await _add_workspace(eic_workspace_db, _confirmed_bindings_payload())
    preview = await service.build_preview(
        ROOT,
        workspace_id=workspace_id,
        quote_input=_quote_input_overlay(_confirmed_bindings_payload()),
    )
    assert preview is not None
    assert any(b.code == "INTERNAL_MATERIAL_COST_MISSING" for b in preview.internal_blockers)


@pytest.mark.asyncio
async def test_no_commercial_fields_on_preview(eic_service, eic_workspace_db) -> None:
    workspace_id = await _add_workspace(eic_workspace_db, _confirmed_bindings_payload())
    preview = await eic_service.build_preview(
        ROOT,
        workspace_id=workspace_id,
        quote_input=_quote_input_overlay(_confirmed_bindings_payload()),
    )
    assert preview is not None
    dumped = preview.model_dump()
    for key in ("commercial_price", "client_price", "offer_price", "markup", "margin", "vat"):
        assert key not in dumped


def test_post_eic_preview_endpoint_with_workspace(volumetric_auth_client, db_fixture):
    payload = _confirmed_bindings_payload()

    async def _seed():
        async with db_fixture.session_maker() as session:
            await _seed_volumetric_v2_fixture(session)
            await _seed_logo_template(session)
            await _seed_logo_inventory_materials(session)
            return await _add_workspace(session, payload)

    workspace_id = db_fixture.run(_seed())
    response = volumetric_auth_client.post(
        f"/api/v1/product-system/estimated-internal-cost-preview/{ROOT}",
        json={"workspace_id": workspace_id, "quote_input": _quote_input_overlay(payload)},
    )
    assert response.status_code == 200
    body = response.json()
    assert body.get("source") == "estimated_internal_cost"
    assert body.get("input_summary", {}).get("workspace_id") == workspace_id
    assert "commercial_price" not in body
    logo_lines = [
        line for line in body.get("estimated_material_lines", []) if "::" in (line.get("component_code") or "")
    ]
    print_logo_lines = [
        line
        for line in logo_lines
        if "print_media" in (line.get("code") or "") or "laminate" in (line.get("code") or "")
    ]
    assert print_logo_lines or any(
        b.get("code") in ("INTERNAL_MATERIAL_COST_MISSING", "INTERNAL_GEOMETRY_MISSING")
        for b in body.get("internal_blockers", [])
    )


def test_post_eic_partial_finish(volumetric_auth_client, db_fixture):
    payload = _confirmed_bindings_payload()
    payload["finish_setup"]["artwork_finishes"][0]["confirmed"] = False
    payload["finish_setup"]["artwork_finishes"][1]["confirmed"] = False

    async def _seed():
        async with db_fixture.session_maker() as session:
            await _seed_volumetric_v2_fixture(session)
            await _seed_logo_template(session)
            await _seed_logo_inventory_materials(session)
            return await _add_workspace(session, payload)

    workspace_id = db_fixture.run(_seed())
    response = volumetric_auth_client.post(
        f"/api/v1/product-system/estimated-internal-cost-preview/{ROOT}",
        json={"workspace_id": workspace_id},
    )
    assert response.status_code == 200
    body = response.json()
    assert body.get("status") == "partial"
    logo_lines = [
        line for line in body.get("estimated_material_lines", []) if "::" in (line.get("component_code") or "")
    ]
    assert logo_lines == []


def test_artwork_owned_material_codes_limited() -> None:
    assert "print_media" in ARTWORK_OWNED_LOGO_MATERIAL_CODES
    assert "laminate_media" in ARTWORK_OWNED_LOGO_MATERIAL_CODES
    assert "logo_face_material" not in ARTWORK_OWNED_LOGO_MATERIAL_CODES
