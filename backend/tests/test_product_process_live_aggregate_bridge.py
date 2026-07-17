"""Live Aggregate bridge — ProductAggregateService → modular process resolver."""

from __future__ import annotations

import copy

import pytest
import pytest_asyncio

from services.execution_preview_from_frozen_graph_service import (
    build_execution_preview_from_frozen_snapshot,
)
from services.frozen_modular_graph_service import build_frozen_modular_graph_from_v2
from services.product_aggregate_service import ProductAggregateService
from services.product_process_aggregate_bridge import (
    apply_modular_process_graph_to_aggregate,
    build_in_memory_snapshot_v2_from_aggregate,
)
from services.product_process_resolve_input_adapter import (
    PROCESS_GRAPH_SOURCE_LEGACY,
    PROCESS_GRAPH_SOURCE_MODULAR,
    template_has_modular_process_contract,
)
from tests.test_product_aggregate_volumetric_v2 import (
    TEMPLATE_CODE,
    _seed_volumetric_v2_fixture,
)


@pytest_asyncio.fixture
async def volumetric_v2_db(db_session):
    await _seed_volumetric_v2_fixture(db_session)
    return db_session


def _payload(**finish_extra) -> dict:
    finish = {
        "return_finish_type": "standard_supplier",
        "lighting_system_type": "led_modules",
        "mounting_system": "none",
        "mounting_template_enabled": False,
        "screw_finish": "NATURAL",
    }
    finish.update(finish_extra)
    return {
        "finish_setup": finish,
        "quote_geometry": {
            "width_mm": 1200,
            "height_mm": 400,
            "letter_count": 5,
            "letter_perimeter_m": 8.2,
            "letter_face_area_m2": 0.45,
        },
    }


def _codes(agg) -> set[str]:
    return {r.task_name for r in agg.task_contract.task_rules}


def _before(agg, a: str, b: str) -> bool:
    order = [r.task_name for r in sorted(
        agg.task_contract.task_rules,
        key=lambda r: (r.sequence if r.sequence is not None else 10_000, r.task_name),
    )]
    return order.index(a) < order.index(b)


def _deps(agg, code: str) -> set[str]:
    for r in agg.task_contract.task_rules:
        if r.task_name == code:
            return set(r.depends_on_process_ids)
    return set()


# --- A/B identity ---
def test_a_stable_identity_gate():
    assert template_has_modular_process_contract("TPL-VOLUMETRIC-LETTERS_v2")
    assert template_has_modular_process_contract("TPL-VOLUMETRIC-LETTERS")
    assert not template_has_modular_process_contract("TPL-OTHER-PRODUCT")
    assert not template_has_modular_process_contract("Litere volumetrice luminoase")


@pytest.mark.asyncio
async def test_b_no_display_name_matching(volumetric_v2_db):
    svc = ProductAggregateService(volumetric_v2_db)
    agg = await svc.build(TEMPLATE_CODE)
    assert agg.task_contract.process_graph_source == PROCESS_GRAPH_SOURCE_MODULAR
    # Display-name-like codes must not activate
    assert not template_has_modular_process_contract("Litere Volumetrice")


# --- C/D/E branches via active build entry ---
@pytest.mark.asyncio
async def test_c_bare_metal_active_aggregate(volumetric_v2_db):
    svc = ProductAggregateService(volumetric_v2_db)
    agg = await svc.build(
        TEMPLATE_CODE,
        process_bridge_payload=_payload(
            mounting_system="steel_bars",
            mains_cable_length_m=7.5,
        ),
    )
    assert agg.task_contract.process_graph_source == PROCESS_GRAPH_SOURCE_MODULAR
    codes = _codes(agg)
    assert "INSTALL_CABLE_CHANNEL" in codes
    assert "INSTALL_POWER_SUPPLY" in codes
    assert "INSTALL_MAINS_CABLE" in codes
    assert "FABRICATE_ALUCOBOND_CASED_PANEL" not in codes
    assert "PACK_POWER_SUPPLY_SEPARATELY" not in codes
    assert _before(agg, "TEST_LED_ON", "ATTACH_BODY_TO_BACK")
    assert _before(agg, "ATTACH_BODY_TO_BACK", "TEST_LIGHT_UNIFORMITY")
    assert any(w.code == "PROCESS_GRAPH_MODULAR_RESOLVER" for w in agg.warnings)


@pytest.mark.asyncio
async def test_d_alucobond_active_aggregate(volumetric_v2_db):
    svc = ProductAggregateService(volumetric_v2_db)
    agg = await svc.build(
        TEMPLATE_CODE,
        process_bridge_payload=_payload(
            support_type="alucobond_cased",
            mounting_system="alucobond_cased",
            power_supply_service_corner="TOP_RIGHT",
            mains_cable_length_m=10.0,
        ),
    )
    codes = _codes(agg)
    assert "INSTALL_CABLE_CHANNEL" not in codes
    assert "FABRICATE_METAL_SUPPORT" not in codes
    assert "ROUTE_WIRING_BEHIND_PANEL" in codes
    assert "INSTALL_POWER_SUPPLY_NEAR_SERVICE_CORNER" in codes
    assert agg.task_contract.process_graph_hash


@pytest.mark.asyncio
async def test_e_no_support_active_aggregate(volumetric_v2_db):
    svc = ProductAggregateService(volumetric_v2_db)
    agg = await svc.build(
        TEMPLATE_CODE,
        process_bridge_payload=_payload(mounting_system="none"),
    )
    codes = _codes(agg)
    assert "FABRICATE_METAL_SUPPORT" not in codes
    assert "INSTALL_CABLE_CHANNEL" not in codes
    assert "PACK_POWER_SUPPLY_SEPARATELY" in codes
    assert "RIGIDIZE_FOR_TRANSPORT" in codes


# --- F/G/H cant ---
@pytest.mark.asyncio
async def test_f_cant_standard(volumetric_v2_db):
    agg = await ProductAggregateService(volumetric_v2_db).build(
        TEMPLATE_CODE,
        process_bridge_payload=_payload(return_finish_type="white_aluminum"),
    )
    codes = _codes(agg)
    assert "APPLY_CANT_VINYL" not in codes
    assert "PAINT_VOLUME_RAL" not in codes
    assert "FORM_CANT_CNC" in codes
    assert "BOND_FACE_TO_CANT" in codes


@pytest.mark.asyncio
async def test_g_cant_vinyl_before_cnc(volumetric_v2_db):
    agg = await ProductAggregateService(volumetric_v2_db).build(
        TEMPLATE_CODE,
        process_bridge_payload=_payload(return_finish_type="oracal_wrapped"),
    )
    assert "APPLY_CANT_VINYL" in _codes(agg)
    assert "APPLY_CANT_VINYL" in _deps(agg, "FORM_CANT_CNC")
    assert _before(agg, "APPLY_CANT_VINYL", "FORM_CANT_CNC")
    assert "PAINT_VOLUME_RAL" not in _codes(agg)


@pytest.mark.asyncio
async def test_h_cant_ral_order_no_curing(volumetric_v2_db):
    agg = await ProductAggregateService(volumetric_v2_db).build(
        TEMPLATE_CODE,
        process_bridge_payload=_payload(return_finish_type="ral_paint"),
    )
    codes = _codes(agg)
    assert "APPLY_CANT_VINYL" not in codes
    assert "MASK_FACE" in codes
    assert "DRY_VOLUME_PAINT" in codes
    assert _before(agg, "BOND_FACE_TO_CANT", "MASK_FACE")
    assert _before(agg, "MASK_FACE", "PAINT_VOLUME_RAL")
    assert "ADHESIVE_CURING" not in codes
    assert "BACK_DRILLING" not in codes


# --- K LED / screws / cable ---
@pytest.mark.asyncio
async def test_k_led_cyano_roles(volumetric_v2_db):
    from services.product_process_resolver_service import resolve_product_process_graph
    from services.product_process_resolve_input_adapter import build_resolve_input_from_active_config

    inp, _, _, _ = build_resolve_input_from_active_config(
        template_code=TEMPLATE_CODE,
        workspace_payload=_payload(),
    )
    g = resolve_product_process_graph(inp)
    led = next(r for r in g.process_rules if r.process_code == "INSTALL_LED_MODULES")
    assert "CYANOACRYLATE_ADHESIVE" in led.material_roles
    assert "CYANOACRYLATE_ACTIVATOR" in led.material_roles


@pytest.mark.asyncio
async def test_l_m_screw_finish(volumetric_v2_db):
    natural = await ProductAggregateService(volumetric_v2_db).build(
        TEMPLATE_CODE,
        process_bridge_payload=_payload(screw_finish="NATURAL"),
    )
    assert "PAINT_FASTENERS" not in _codes(natural)
    painted = await ProductAggregateService(volumetric_v2_db).build(
        TEMPLATE_CODE,
        process_bridge_payload=_payload(screw_finish="PAINTED_TO_MATCH_CANT"),
    )
    assert "PAINT_FASTENERS" in _codes(painted)


@pytest.mark.parametrize(
    "length",
    [2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0, 22.5, 25.0],
)
@pytest.mark.asyncio
async def test_n_cable_valid_lengths(volumetric_v2_db, length):
    agg = await ProductAggregateService(volumetric_v2_db).build(
        TEMPLATE_CODE,
        process_bridge_payload=_payload(
            mounting_system="steel_bars",
            mains_cable_length_m=length,
        ),
    )
    assert agg.task_contract.process_graph_source == PROCESS_GRAPH_SOURCE_MODULAR
    assert "INSTALL_MAINS_CABLE" in _codes(agg)
    assert not any(c.code.endswith("INVALID_MAINS_CABLE_LENGTH") for c in agg.conflicts)


@pytest.mark.parametrize("bad", [0, 3, 26, -5, "abc"])
@pytest.mark.asyncio
async def test_o_cable_invalid_rejected(volumetric_v2_db, bad):
    agg = await ProductAggregateService(volumetric_v2_db).build(
        TEMPLATE_CODE,
        process_bridge_payload=_payload(
            mounting_system="steel_bars",
            mains_cable_length_m=bad,
        ),
    )
    # blocked → letters rules cleared
    assert "INSTALL_MAINS_CABLE" not in _codes(agg) or agg.conflicts
    assert agg.task_contract.process_graph_source == PROCESS_GRAPH_SOURCE_MODULAR
    assert agg.conflicts or "INSTALL_CABLE_CHANNEL" not in _codes(agg)


@pytest.mark.asyncio
async def test_p_service_corner_required_alucobond(volumetric_v2_db):
    agg = await ProductAggregateService(volumetric_v2_db).build(
        TEMPLATE_CODE,
        process_bridge_payload=_payload(
            support_type="alucobond_cased",
            mounting_system="alucobond_cased",
            # no corner
        ),
    )
    assert any("SERVICE_CORNER" in c.code for c in agg.conflicts)
    assert "INSTALL_POWER_SUPPLY_NEAR_SERVICE_CORNER" not in _codes(agg)


@pytest.mark.asyncio
async def test_q_r_s_branch_isolation(volumetric_v2_db):
    metal = await ProductAggregateService(volumetric_v2_db).build(
        TEMPLATE_CODE,
        process_bridge_payload=_payload(
            mounting_system="steel_bars",
            mains_cable_length_m=5.0,
            power_supply_service_corner="TOP_LEFT",  # irrelevant for metal
        ),
    )
    assert "INSTALL_CABLE_CHANNEL" in _codes(metal)
    assert "INSTALL_POWER_SUPPLY_NEAR_SERVICE_CORNER" not in _codes(metal)

    none = await ProductAggregateService(volumetric_v2_db).build(
        TEMPLATE_CODE,
        process_bridge_payload=_payload(mounting_system="none"),
    )
    assert "PACK_POWER_SUPPLY_SEPARATELY" in _codes(none)
    assert "INSTALL_CABLE_CHANNEL" not in _codes(none)


@pytest.mark.asyncio
async def test_t_u_two_light_tests_order(volumetric_v2_db):
    agg = await ProductAggregateService(volumetric_v2_db).build(
        TEMPLATE_CODE,
        process_bridge_payload=_payload(mounting_system="steel_bars", mains_cable_length_m=5.0),
    )
    assert "TEST_LED_ON" in _codes(agg)
    assert "TEST_LIGHT_UNIFORMITY" in _codes(agg)
    assert _before(agg, "TEST_LED_ON", "ATTACH_BODY_TO_BACK")
    assert _before(agg, "ATTACH_BODY_TO_BACK", "TEST_LIGHT_UNIFORMITY")


@pytest.mark.asyncio
async def test_v_inactive_template_isolation(volumetric_v2_db):
    off = await ProductAggregateService(volumetric_v2_db).build(
        TEMPLATE_CODE,
        process_bridge_payload=_payload(mounting_template_enabled=False),
    )
    assert "GENERATE_INSTALLATION_TEMPLATE" not in _codes(off)
    on = await ProductAggregateService(volumetric_v2_db).build(
        TEMPLATE_CODE,
        process_bridge_payload=_payload(mounting_template_enabled=True),
    )
    assert "GENERATE_INSTALLATION_TEMPLATE" in _codes(on)


@pytest.mark.asyncio
async def test_w_no_duplicate_process_codes(volumetric_v2_db):
    agg = await ProductAggregateService(volumetric_v2_db).build(
        TEMPLATE_CODE,
        process_bridge_payload=_payload(mounting_system="steel_bars", mains_cable_length_m=5.0),
    )
    names = [r.task_name for r in agg.task_contract.task_rules]
    assert len(names) == len(set(names))


@pytest.mark.asyncio
async def test_z_aa_determinism(volumetric_v2_db):
    svc = ProductAggregateService(volumetric_v2_db)
    payload = _payload(mounting_system="steel_bars", mains_cable_length_m=12.5, return_finish_type="oracal_wrapped")
    a = await svc.build(TEMPLATE_CODE, process_bridge_payload=payload)
    b = await svc.build(TEMPLATE_CODE, process_bridge_payload=copy.deepcopy(payload))
    assert a.task_contract.process_graph_hash == b.task_contract.process_graph_hash
    assert [r.task_name for r in a.task_contract.task_rules] == [
        r.task_name for r in b.task_contract.task_rules
    ]
    assert [r.depends_on_process_ids for r in a.task_contract.task_rules] == [
        r.depends_on_process_ids for r in b.task_contract.task_rules
    ]


@pytest.mark.asyncio
async def test_ab_ac_ad_snapshot_4a_4c_preserve_dag(volumetric_v2_db):
    agg = await ProductAggregateService(volumetric_v2_db).build(
        TEMPLATE_CODE,
        process_bridge_payload=_payload(
            mounting_system="steel_bars",
            mains_cable_length_m=7.5,
            return_finish_type="oracal_wrapped",
        ),
    )
    snap = build_in_memory_snapshot_v2_from_aggregate(agg)
    frozen = build_frozen_modular_graph_from_v2(snap)
    form = next(c for c in frozen.execution.task_candidates if c.task_name == "FORM_CANT_CNC")
    assert "APPLY_CANT_VINYL" in form.depends_on_process_ids

    preview = build_execution_preview_from_frozen_snapshot(snap)
    assert preview.safety.no_write is True
    real = [e for e in preview.dependency_graph.edges if e.provenance == "process_depends_on"]
    assert real
    assert not [e for e in preview.dependency_graph.edges if e.provenance == "sequence_order"]


@pytest.mark.asyncio
async def test_ae_legacy_non_volumetric_path(volumetric_v2_db):
    # Child aluminum template from fixture — no modular contract
    from tests.test_product_aggregate_volumetric_v2 import CHILD_ALUMINUM

    agg = await ProductAggregateService(volumetric_v2_db).build(CHILD_ALUMINUM)
    if agg is None:
        pytest.skip("child template not seeded as full aggregate")
    assert agg.task_contract.process_graph_source in {
        PROCESS_GRAPH_SOURCE_LEGACY,
        None,
    } or agg.task_contract.process_graph_source != PROCESS_GRAPH_SOURCE_MODULAR
    # Must not have CUT_FACE from letters resolver
    assert "CUT_FACE" not in _codes(agg)


@pytest.mark.asyncio
async def test_ag_no_sequence_overwrite_on_resolver_graph(volumetric_v2_db):
    agg = await ProductAggregateService(volumetric_v2_db).build(
        TEMPLATE_CODE,
        process_bridge_payload=_payload(return_finish_type="oracal_wrapped"),
    )
    form = next(r for r in agg.task_contract.task_rules if r.task_name == "FORM_CANT_CNC")
    # Real dep, not merely previous sequence neighbor
    assert "APPLY_CANT_VINYL" in form.depends_on_process_ids


@pytest.mark.asyncio
async def test_ah_zero_writes_ast():
    from pathlib import Path

    for rel in (
        "services/product_process_aggregate_bridge.py",
        "services/product_process_resolve_input_adapter.py",
    ):
        text = (Path(__file__).resolve().parents[1] / rel).read_text(encoding="utf-8")
        assert "session.commit" not in text
        assert ".commit(" not in text
        assert "db.add" not in text


@pytest.mark.asyncio
async def test_runtime_proof_three_configs_via_build(volumetric_v2_db):
    svc = ProductAggregateService(volumetric_v2_db)
    reports = []
    configs = [
        ("metal", _payload(mounting_system="steel_bars", mains_cable_length_m=7.5)),
        (
            "alucobond",
            _payload(
                support_type="alucobond_cased",
                mounting_system="alucobond_cased",
                power_supply_service_corner="BOTTOM_LEFT",
                mains_cable_length_m=15.0,
            ),
        ),
        ("none", _payload(mounting_system="none")),
    ]
    for name, payload in configs:
        agg = await svc.build(TEMPLATE_CODE, process_bridge_payload=payload)
        assert agg.task_contract.process_graph_source == PROCESS_GRAPH_SOURCE_MODULAR
        snap = build_in_memory_snapshot_v2_from_aggregate(agg)
        preview = build_execution_preview_from_frozen_snapshot(snap)
        edge_count = sum(len(r.depends_on_process_ids) for r in agg.task_contract.task_rules)
        reports.append(
            {
                "name": name,
                "process_count": len(agg.task_contract.task_rules),
                "edge_count": edge_count,
                "hash": agg.task_contract.process_graph_hash,
                "channel": "INSTALL_CABLE_CHANNEL" in _codes(agg),
                "psu_pack": "PACK_POWER_SUPPLY_SEPARATELY" in _codes(agg),
                "preview_candidates": len(preview.task_candidates),
                "no_write": preview.safety.no_write,
            }
        )
    assert reports[0]["channel"] is True and reports[0]["psu_pack"] is False
    assert reports[1]["channel"] is False
    assert reports[2]["psu_pack"] is True
    assert all(r["no_write"] for r in reports)


@pytest.mark.asyncio
async def test_no_dossier_concat(volumetric_v2_db):
    """Resolver path must not keep dossier task names alongside modular codes."""
    agg = await ProductAggregateService(volumetric_v2_db).build(TEMPLATE_CODE)
    names = _codes(agg)
    assert "cnc_face_cut" not in names
    assert "electrical_wiring" not in names
    assert "return_face_bonding" not in names
    assert "CUT_FACE" in names
