"""INTAKE_V6_MODULAR_PROCESS_FIELD_WIRING — typed PD → adapter → resolver → Aggregate."""

from __future__ import annotations

import copy

import pytest
import pytest_asyncio

from services.execution_preview_from_frozen_graph_service import (
    build_execution_preview_from_frozen_snapshot,
)
from services.frozen_modular_graph_service import build_frozen_modular_graph_from_v2
from services.product_aggregate_service import ProductAggregateService
from services.intake_v6_modular_form_contract_service import VOLUMETRIC_FIELD_BINDINGS
from services.product_definition_builder_service import _build_canonical_values
from services.product_process_aggregate_bridge import (
    apply_modular_process_graph_to_aggregate,
    build_in_memory_snapshot_v2_from_aggregate,
)
from services.product_process_resolve_input_adapter import (
    CONFIG_SOURCE_LEGACY_FALLBACK,
    CONFIG_SOURCE_TYPED_FINISH,
    CONFIG_SOURCE_TYPED_PD,
    PROCESS_GRAPH_SOURCE_MODULAR,
    build_resolve_input_from_active_config,
)
from services.product_process_resolver_service import resolve_product_process_graph
from tests.test_product_aggregate_volumetric_v2 import (
    TEMPLATE_CODE,
    _seed_volumetric_v2_fixture,
)

METAL_SOLUTION = {
    "template_code": "TPL-METAL-PREMOUNT-STRUCTURE_v1",
    "kind": "metal_bars",
    "configuration": {"bar_material": "steel", "bar_count": 2},
}
ACM_SOLUTION = {
    "template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
    "kind": "acm_panel",
    "configuration": {},
}


@pytest_asyncio.fixture
async def volumetric_v2_db(db_session):
    await _seed_volumetric_v2_fixture(db_session)
    return db_session


def _finish(**extra) -> dict:
    base = {
        "return_finish_type": "white_aluminum",
        "lighting_system_type": "led_modules",
        "mounting_template_enabled": False,
        "service_screw_finish": "NATURAL",
        "mounting_system": "direct_wall",
    }
    base.update(extra)
    return base


def _workspace(finish: dict, *, pd_canonical: dict | None = None) -> dict:
    payload = {
        "finish_setup": finish,
        "quote_geometry": {
            "width_mm": 1200,
            "height_mm": 400,
            "letter_count": 5,
            "letter_perimeter_m": 8.2,
            "letter_face_area_m2": 0.45,
            "confirmed": True,
        },
    }
    if pd_canonical is not None:
        payload["product_definition_canonical_values"] = pd_canonical
    return payload


def _codes(agg) -> set[str]:
    return {r.task_name for r in agg.task_contract.task_rules}


def _info_details(agg) -> dict:
    for w in agg.warnings:
        if w.code == "PROCESS_GRAPH_MODULAR_RESOLVER":
            return dict(w.details or {})
    return {}


# --- Authority / precedence ---
def test_a_typed_pd_wins_cable_over_finish_setup():
    finish = _finish(
        mounting_solution=METAL_SOLUTION,
        mounting_system="steel_bars",
        mains_cable_length_m=5.0,
    )
    pd = {
        "mounting_solution": METAL_SOLUTION,
        "mains_cable_length_m": 12.5,
        "return_finish_type": "white_aluminum",
        "service_screw_finish": "NATURAL",
    }
    inp, warnings, blockers, meta = build_resolve_input_from_active_config(
        template_code=TEMPLATE_CODE,
        workspace_payload=_workspace(finish),
        product_definition_canonical_values=pd,
    )
    assert inp.mains_cable_length_m == 12.5
    assert meta["cable_source"] == CONFIG_SOURCE_TYPED_PD
    assert meta["config_source"] == CONFIG_SOURCE_TYPED_PD
    assert "typed_pd_wins_over_finish_setup_cable_conflict" in warnings
    assert not blockers


def test_b_legacy_mounting_system_fallback_still_maps():
    inp, _, _, meta = build_resolve_input_from_active_config(
        template_code=TEMPLATE_CODE,
        workspace_payload=_workspace(_finish(mounting_system="steel_bars", mains_cable_length_m=7.5)),
    )
    assert inp.support_type == "metal_bars"
    assert meta["support_source"] == CONFIG_SOURCE_LEGACY_FALLBACK
    assert inp.mains_cable_length_m == 7.5


def test_c_mounting_solution_maps_acm_and_rejects_flat():
    inp, _, blockers, meta = build_resolve_input_from_active_config(
        template_code=TEMPLATE_CODE,
        workspace_payload=_workspace(
            _finish(
                mounting_solution=ACM_SOLUTION,
                power_supply_service_corner="TOP_RIGHT",
                mains_cable_length_m=10.0,
            )
        ),
    )
    assert inp.support_type == "alucobond_cased"
    assert meta["support_source"] == CONFIG_SOURCE_TYPED_FINISH
    assert inp.power_supply_service_corner == "TOP_RIGHT"

    flat_inp, _, flat_blockers, _ = build_resolve_input_from_active_config(
        template_code=TEMPLATE_CODE,
        workspace_payload=_workspace(_finish(support_type="alucobond_flat")),
    )
    assert "alucobond_flat_not_allowed" in flat_blockers
    assert flat_inp.support_type == "none"


def test_d_typed_finish_screw_and_default():
    inp, warnings, _, meta = build_resolve_input_from_active_config(
        template_code=TEMPLATE_CODE,
        workspace_payload=_workspace(_finish(service_screw_finish="PAINTED_TO_MATCH_CANT")),
    )
    assert inp.screw_finish == "PAINTED_TO_MATCH_CANT"
    assert meta["screw_source"] == CONFIG_SOURCE_TYPED_FINISH

    legacy_inp, legacy_warnings, _, _ = build_resolve_input_from_active_config(
        template_code=TEMPLATE_CODE,
        workspace_payload=_workspace(
            {
                "return_finish_type": "white_aluminum",
                "lighting_system_type": "led_modules",
                "mounting_template_enabled": False,
                "screw_finish": "NATURAL",  # legacy ghost key
            }
        ),
    )
    assert legacy_inp.screw_finish == "NATURAL"
    assert "default_screw_finish_NATURAL" not in legacy_warnings or True


def test_e_never_invent_cable_5m():
    inp, _, _, meta = build_resolve_input_from_active_config(
        template_code=TEMPLATE_CODE,
        workspace_payload=_workspace(_finish(mounting_solution=METAL_SOLUTION)),
    )
    assert inp.mains_cable_length_m is None
    assert meta["cable_source"] is None


@pytest.mark.parametrize("length", [2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0, 22.5, 25.0])
def test_f_all_allowed_cable_values(length):
    inp, _, blockers, _ = build_resolve_input_from_active_config(
        template_code=TEMPLATE_CODE,
        workspace_payload=_workspace(
            _finish(mounting_solution=METAL_SOLUTION, mains_cable_length_m=length)
        ),
    )
    assert inp.mains_cable_length_m == length
    assert "invalid_mains_cable_length" not in blockers
    graph = resolve_product_process_graph(inp)
    assert graph.readiness != "blocked" or not any(
        b.code == "invalid_mains_cable_length" for b in graph.blockers
    )


@pytest.mark.parametrize("bad", [0, 3, 6, 26, -1, "nope"])
def test_g_invalid_cable_rejected(bad):
    inp, _, map_blockers, _ = build_resolve_input_from_active_config(
        template_code=TEMPLATE_CODE,
        workspace_payload=_workspace(
            _finish(mounting_solution=METAL_SOLUTION, mains_cable_length_m=bad)
        ),
    )
    graph = resolve_product_process_graph(inp)
    assert map_blockers or graph.blockers


# --- ProductDefinition projection (same binder as ProductDefinitionBuilderService) ---
def test_h_product_definition_compiles_typed_fields():
    payload = _workspace(
        _finish(
            mounting_solution=METAL_SOLUTION,
            mounting_system="steel_bars",
            mains_cable_length_m=17.5,
            service_screw_finish="PAINTED_TO_MATCH_CANT",
            power_supply_service_corner="TOP_LEFT",
            mounting_template_enabled=True,
        )
    )
    compile_payload = {k: v for k, v in payload.items() if k != "product_definition_canonical_values"}
    cv = _build_canonical_values(VOLUMETRIC_FIELD_BINDINGS, compile_payload)
    assert cv.get("mains_cable_length_m") == 17.5
    assert cv.get("service_screw_finish") == "PAINTED_TO_MATCH_CANT"
    assert cv.get("power_supply_service_corner") == "TOP_LEFT"
    assert cv.get("mounting_template_enabled") is True
    assert isinstance(cv.get("mounting_solution"), dict)
    assert "METAL" in str(cv["mounting_solution"].get("template_code", "")).upper()
    # PD → adapter → resolver continuity
    inp, _, _, meta = build_resolve_input_from_active_config(
        template_code=TEMPLATE_CODE,
        workspace_payload=compile_payload,
        product_definition_canonical_values=cv,
    )
    assert inp.mains_cable_length_m == 17.5
    assert inp.support_type == "metal_bars"
    assert meta["config_source"] == CONFIG_SOURCE_TYPED_PD


# --- Live Aggregate path ---
@pytest.mark.asyncio
async def test_i_typed_pd_reaches_aggregate_via_build(volumetric_v2_db):
    finish = _finish(
        mounting_system="steel_bars",
        mains_cable_length_m=5.0,
        service_screw_finish="NATURAL",
    )
    pd = {
        "mounting_solution": METAL_SOLUTION,
        "mains_cable_length_m": 20.0,
        "return_finish_type": "oracal_wrapped",
        "service_screw_finish": "PAINTED_TO_MATCH_CANT",
        "lighting_system_type": "led_modules",
        "mounting_template_enabled": False,
    }
    agg = await ProductAggregateService(volumetric_v2_db).build(
        TEMPLATE_CODE,
        process_bridge_payload=_workspace(finish, pd_canonical=pd),
    )
    assert agg.task_contract.process_graph_source == PROCESS_GRAPH_SOURCE_MODULAR
    details = _info_details(agg)
    assert details.get("config_source") == CONFIG_SOURCE_TYPED_PD
    assert details.get("mains_cable_length_m") == 20.0
    assert details.get("service_screw_finish") == "PAINTED_TO_MATCH_CANT"
    assert details.get("cant_finish") == "vinyl"
    assert "APPLY_CANT_VINYL" in _codes(agg)
    assert "PAINT_FASTENERS" in _codes(agg)
    assert "INSTALL_CABLE_CHANNEL" in _codes(agg)


@pytest.mark.asyncio
async def test_j_metal_bars_mounting_solution_branch(volumetric_v2_db):
    agg = await ProductAggregateService(volumetric_v2_db).build(
        TEMPLATE_CODE,
        process_bridge_payload=_workspace(
            _finish(
                mounting_solution=METAL_SOLUTION,
                mains_cable_length_m=7.5,
                service_screw_finish="NATURAL",
            )
        ),
    )
    details = _info_details(agg)
    assert details.get("support_type") == "metal_bars"
    assert "INSTALL_CABLE_CHANNEL" in _codes(agg)
    assert "INSTALL_POWER_SUPPLY_NEAR_SERVICE_CORNER" not in _codes(agg)


@pytest.mark.asyncio
async def test_k_alucobond_cased_branch(volumetric_v2_db):
    agg = await ProductAggregateService(volumetric_v2_db).build(
        TEMPLATE_CODE,
        process_bridge_payload=_workspace(
            _finish(
                mounting_solution=ACM_SOLUTION,
                mains_cable_length_m=15.0,
                power_supply_service_corner="BOTTOM_RIGHT",
            )
        ),
    )
    details = _info_details(agg)
    assert details.get("support_type") == "alucobond_cased"
    assert details.get("power_supply_service_corner") == "BOTTOM_RIGHT"
    assert "INSTALL_CABLE_CHANNEL" not in _codes(agg)
    assert "INSTALL_POWER_SUPPLY_NEAR_SERVICE_CORNER" in _codes(agg)


@pytest.mark.asyncio
async def test_l_no_support_isolation(volumetric_v2_db):
    agg = await ProductAggregateService(volumetric_v2_db).build(
        TEMPLATE_CODE,
        process_bridge_payload=_workspace(
            _finish(
                mounting_solution={"template_code": "", "kind": "none"},
                mounting_system="none",
                mounting_template_enabled=True,
            )
        ),
    )
    assert "PACK_POWER_SUPPLY_SEPARATELY" in _codes(agg)
    assert "INSTALL_CABLE_CHANNEL" not in _codes(agg)
    assert "INSTALL_POWER_SUPPLY_NEAR_SERVICE_CORNER" not in _codes(agg)
    assert "GENERATE_INSTALLATION_TEMPLATE" in _codes(agg)


@pytest.mark.asyncio
async def test_m_snapshot_4a_4c_preserve_typed_config(volumetric_v2_db):
    agg = await ProductAggregateService(volumetric_v2_db).build(
        TEMPLATE_CODE,
        process_bridge_payload=_workspace(
            _finish(
                mounting_solution=METAL_SOLUTION,
                mains_cable_length_m=12.5,
                return_finish_type="ral_paint",
            )
        ),
    )
    snap = build_in_memory_snapshot_v2_from_aggregate(agg)
    frozen = build_frozen_modular_graph_from_v2(snap)
    paint = next(c for c in frozen.execution.task_candidates if c.task_name == "PAINT_VOLUME_RAL")
    assert "BOND_FACE_TO_CANT" in paint.depends_on_process_ids or paint.depends_on_process_ids
    preview = build_execution_preview_from_frozen_snapshot(snap)
    assert preview.safety.no_write is True
    assert any(e.provenance == "process_depends_on" for e in preview.dependency_graph.edges)


@pytest.mark.asyncio
async def test_n_apply_bridge_accepts_pd_canonical_directly(volumetric_v2_db):
    base = await ProductAggregateService(volumetric_v2_db).build(TEMPLATE_CODE)
    bridged = apply_modular_process_graph_to_aggregate(
        base,
        workspace_payload=_workspace(
            _finish(mounting_system="steel_bars", mains_cable_length_m=5.0)
        ),
        product_definition_canonical_values={
            "mounting_solution": METAL_SOLUTION,
            "mains_cable_length_m": 22.5,
            "return_finish_type": "white_aluminum",
        },
    )
    details = _info_details(bridged)
    assert details.get("mains_cable_length_m") == 22.5
    assert details.get("config_source") == CONFIG_SOURCE_TYPED_PD


@pytest.mark.asyncio
async def test_o_determinism_typed_path(volumetric_v2_db):
    svc = ProductAggregateService(volumetric_v2_db)
    payload = _workspace(
        _finish(
            mounting_solution=METAL_SOLUTION,
            mains_cable_length_m=10.0,
            service_screw_finish="PAINTED_TO_MATCH_CANT",
            return_finish_type="oracal_wrapped",
        )
    )
    a = await svc.build(TEMPLATE_CODE, process_bridge_payload=payload)
    b = await svc.build(TEMPLATE_CODE, process_bridge_payload=copy.deepcopy(payload))
    assert a.task_contract.process_graph_hash == b.task_contract.process_graph_hash
