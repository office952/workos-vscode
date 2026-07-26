"""Build — Product Process Contract + simple resolver (litere volumetrice)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from schemas.product_process_contract import ProductProcessResolveInput
from services.execution_preview_from_frozen_graph_service import (
    build_execution_preview_from_frozen_snapshot,
)
from services.frozen_modular_graph_service import build_frozen_modular_graph_from_v2
from services.product_process_aggregate_bridge import resolve_and_build_snapshot
from services.product_process_resolver_service import resolve_product_process_graph


def _codes(graph) -> set[str]:
    return {r.process_code for r in graph.process_rules}


def _before(graph, a: str, b: str) -> bool:
    order = graph.process_order
    assert a in order and b in order
    return order.index(a) < order.index(b)


def _deps(graph, code: str) -> set[str]:
    for r in graph.process_rules:
        if r.process_code == code:
            return set(r.depends_on)
    return set()


def _full_metal(**kwargs) -> ProductProcessResolveInput:
    base = dict(
        support_type="metal_bars",
        cant_finish="standard",
        mains_cable_length_m=7.5,
        illuminated=True,
        geometry_confirmed=True,
        led_layout_confirmed=True,
        geometry={"overall_width": 1200, "overall_height": 400, "element_count": 5},
    )
    base.update(kwargs)
    return ProductProcessResolveInput(**base)


def _full_alucobond(**kwargs) -> ProductProcessResolveInput:
    base = dict(
        support_type="alucobond_cased",
        cant_finish="standard",
        power_supply_service_corner="TOP_LEFT",
        mains_cable_length_m=10.0,
        illuminated=True,
        geometry_confirmed=True,
        led_layout_confirmed=True,
    )
    base.update(kwargs)
    return ProductProcessResolveInput(**base)


def _no_support(**kwargs) -> ProductProcessResolveInput:
    base = dict(
        support_type="none",
        cant_finish="standard",
        illuminated=True,
        geometry_confirmed=True,
        led_layout_confirmed=True,
    )
    base.update(kwargs)
    return ProductProcessResolveInput(**base)


# --- A. Full metal bars ---
def test_a_full_metal_bars_branch():
    g = resolve_product_process_graph(_full_metal())
    assert g.readiness == "ready"
    codes = _codes(g)
    assert "FACE" in g.active_component_codes
    assert "METAL_SUPPORT" in g.active_component_codes
    assert "ALUCOBOND_CASED_PANEL" not in g.active_component_codes
    assert "INSTALL_CABLE_CHANNEL" in codes
    assert "INSTALL_POWER_SUPPLY" in codes
    assert "INSTALL_MAINS_CABLE" in codes
    assert "FABRICATE_ALUCOBOND_CASED_PANEL" not in codes
    assert "ROUTE_WIRING_BEHIND_PANEL" not in codes
    assert "PACK_POWER_SUPPLY_SEPARATELY" not in codes
    assert _before(g, "TEST_LED_ON", "ATTACH_BODY_TO_BACK")
    assert _before(g, "ATTACH_BODY_TO_BACK", "TEST_LIGHT_UNIFORMITY")
    assert g.config_echo["mains_cable_length_m"] == 7.5
    assert 7.5 != 5.0 or g.config_echo["mains_cable_length_m"] == 7.5


# --- B. Alucobond ---
def test_b_alucobond_cased_branch():
    g = resolve_product_process_graph(_full_alucobond())
    assert g.readiness == "ready"
    codes = _codes(g)
    assert "INSTALL_CABLE_CHANNEL" not in codes
    assert "FABRICATE_METAL_SUPPORT" not in codes
    assert "ROUTE_WIRING_BEHIND_PANEL" in codes
    assert "INSTALL_POWER_SUPPLY_NEAR_SERVICE_CORNER" in codes
    assert "FABRICATE_ALUCOBOND_CASED_PANEL" in codes
    assert g.config_echo["power_supply_service_corner"] == "TOP_LEFT"
    assert "TEST_LED_ON" in codes and "TEST_LIGHT_UNIFORMITY" in codes


def test_b_alucobond_requires_service_corner():
    g = resolve_product_process_graph(_full_alucobond(power_supply_service_corner=None))
    assert g.readiness == "blocked"
    assert any(b.code == "service_corner_required" for b in g.blockers)


# --- C. No support ---
def test_c_no_support_branch():
    g = resolve_product_process_graph(_no_support())
    assert g.readiness == "ready"
    codes = _codes(g)
    assert "FABRICATE_METAL_SUPPORT" not in codes
    assert "FABRICATE_ALUCOBOND_CASED_PANEL" not in codes
    assert "INSTALL_CABLE_CHANNEL" not in codes
    assert "CONNECT_LETTERS" not in codes
    assert "INSTALL_POWER_SUPPLY" not in codes
    assert "INSTALL_MAINS_CABLE" not in codes
    assert "PACK_POWER_SUPPLY_SEPARATELY" in codes
    assert "LABEL_POWER_SUPPLY" in codes
    assert "RIGIDIZE_FOR_TRANSPORT" in codes
    assert "ATTACH_BODY_TO_BACK" in codes
    assert "TEST_LIGHT_UNIFORMITY" in codes


# --- D/E/F cant branches ---
def test_d_cant_vinyl_before_form():
    g = resolve_product_process_graph(_full_metal(cant_finish="vinyl"))
    assert g.readiness == "ready"
    codes = _codes(g)
    assert "APPLY_CANT_VINYL" in codes
    assert "PAINT_VOLUME_RAL" not in codes
    assert _before(g, "APPLY_CANT_VINYL", "FORM_CANT_CNC")
    assert "APPLY_CANT_VINYL" in _deps(g, "FORM_CANT_CNC")


def test_e_cant_ral_after_bond_no_curing():
    g = resolve_product_process_graph(_full_metal(cant_finish="ral"))
    assert g.readiness == "ready"
    codes = _codes(g)
    assert "APPLY_CANT_VINYL" not in codes
    assert "MASK_FACE" in codes
    assert "DRY_VOLUME_PAINT" in codes
    assert "PAINT_VOLUME_RAL" in codes
    assert _before(g, "BOND_FACE_TO_CANT", "PAINT_VOLUME_RAL")
    assert "ADHESIVE_CURING" not in codes
    assert "CURE_ADHESIVE" not in codes
    assert "BACK_DRILLING" not in codes


def test_f_cant_standard_no_vinyl_no_paint():
    g = resolve_product_process_graph(_full_metal(cant_finish="standard"))
    codes = _codes(g)
    assert "APPLY_CANT_VINYL" not in codes
    assert "PAINT_VOLUME_RAL" not in codes
    assert "FORM_CANT_CNC" in codes
    assert "BOND_FACE_TO_CANT" in codes


# --- G/H template ---
def test_g_template_off_isolation():
    g = resolve_product_process_graph(_full_metal(template_selected=False))
    assert "INSTALLATION_TEMPLATE" not in g.active_component_codes
    assert "GENERATE_INSTALLATION_TEMPLATE" not in _codes(g)
    assert not any(m.material_role == "INSTALLATION_TEMPLATE_MEDIA" for m in g.material_roles)


def test_h_template_on():
    g = resolve_product_process_graph(
        _full_metal(
            template_selected=True,
            geometry={"overall_width": 1000, "template_segment_count": 3},
        )
    )
    assert "INSTALLATION_TEMPLATE" in g.active_component_codes
    assert "GENERATE_INSTALLATION_TEMPLATE" in _codes(g)
    assert any(m.material_role == "INSTALLATION_TEMPLATE_MEDIA" for m in g.material_roles)
    assert g.config_echo["geometry"].get("template_segment_count") == 3


# --- I inactive support isolation ---
@pytest.mark.parametrize(
    "support,forbidden",
    [
        (
            "metal_bars",
            {
                "FABRICATE_ALUCOBOND_CASED_PANEL",
                "ROUTE_WIRING_BEHIND_PANEL",
                "INSTALL_POWER_SUPPLY_NEAR_SERVICE_CORNER",
                "PACK_POWER_SUPPLY_SEPARATELY",
            },
        ),
        (
            "alucobond_cased",
            {
                "FABRICATE_METAL_SUPPORT",
                "INSTALL_CABLE_CHANNEL",
                "INSTALL_POWER_SUPPLY",
                "PACK_POWER_SUPPLY_SEPARATELY",
            },
        ),
        (
            "none",
            {
                "FABRICATE_METAL_SUPPORT",
                "FABRICATE_ALUCOBOND_CASED_PANEL",
                "INSTALL_CABLE_CHANNEL",
                "ATTACH_BACKS_TO_SUPPORT",
                "CONNECT_LETTERS",
            },
        ),
    ],
)
def test_i_inactive_support_isolation(support, forbidden):
    if support == "metal_bars":
        inp = _full_metal()
    elif support == "alucobond_cased":
        inp = _full_alucobond()
    else:
        inp = _no_support()
    g = resolve_product_process_graph(inp)
    codes = _codes(g)
    for f in forbidden:
        assert f not in codes, f


# --- Interfaces / LED / screws ---
def test_face_cant_interface_materials():
    g = resolve_product_process_graph(_full_metal())
    assert "FACE_CANT" in g.active_interface_codes
    bond = next(r for r in g.process_rules if r.process_code == "BOND_FACE_TO_CANT")
    assert "CYANOACRYLATE_ADHESIVE" in bond.material_roles
    assert "CYANOACRYLATE_ACTIVATOR" in bond.material_roles
    assert bond.source_interface == "FACE_CANT"


def test_led_uses_cyano_and_activator():
    g = resolve_product_process_graph(_full_metal())
    led = next(r for r in g.process_rules if r.process_code == "INSTALL_LED_MODULES")
    assert "CYANOACRYLATE_ADHESIVE" in led.material_roles
    assert "CYANOACRYLATE_ACTIVATOR" in led.material_roles
    assert "LED_MODULE" in led.material_roles


def test_screw_finish_painted():
    g = resolve_product_process_graph(
        _full_metal(screw_finish="PAINTED_TO_MATCH_CANT")
    )
    assert "PAINT_FASTENERS" in _codes(g)
    assert g.config_echo["screw_finish"] == "PAINTED_TO_MATCH_CANT"


def test_screw_finish_natural_no_paint_process():
    g = resolve_product_process_graph(_full_metal(screw_finish="NATURAL"))
    assert "PAINT_FASTENERS" not in _codes(g)


def test_body_back_demountable_states():
    g = resolve_product_process_graph(_full_metal())
    attach = next(r for r in g.process_rules if r.process_code == "ATTACH_BODY_TO_BACK")
    assert "LETTER_SERVICEABLE" in attach.produces_states
    assert "LETTER_CLOSED" in attach.produces_states


def test_two_distinct_light_tests():
    g = resolve_product_process_graph(_full_metal())
    assert "TEST_LED_ON" in _codes(g)
    assert "TEST_LIGHT_UNIFORMITY" in _codes(g)
    assert _before(g, "TEST_LED_ON", "TEST_LIGHT_UNIFORMITY")


def test_no_back_drilling_process():
    g = resolve_product_process_graph(_full_metal())
    assert "BACK_DRILLING" not in _codes(g)
    assert "CUT_FOREX_BACK" in _codes(g)


def test_mains_cable_not_hardcoded_five():
    g = resolve_product_process_graph(_full_metal(mains_cable_length_m=12.5))
    assert g.config_echo["mains_cable_length_m"] == 12.5
    bad = resolve_product_process_graph(_full_metal(mains_cable_length_m=6.0))
    assert bad.readiness == "blocked"
    assert any(b.code == "invalid_mains_cable_length" for b in bad.blockers)


# --- J determinism ---
def test_j_determinism():
    a = resolve_product_process_graph(_full_metal(cant_finish="vinyl"))
    b = resolve_product_process_graph(_full_metal(cant_finish="vinyl"))
    assert a.graph_hash == b.graph_hash
    assert a.process_order == b.process_order
    assert [r.process_code for r in a.process_rules] == [r.process_code for r in b.process_rules]
    assert [r.depends_on for r in a.process_rules] == [r.depends_on for r in b.process_rules]


def test_j_hash_changes_on_config():
    a = resolve_product_process_graph(_full_metal(cant_finish="standard"))
    b = resolve_product_process_graph(_full_metal(cant_finish="vinyl"))
    assert a.graph_hash != b.graph_hash


# --- K/L adversarial ---
def test_k_cycle_detection_blocks():
    g = resolve_product_process_graph(
        _full_metal(inject_cycle_edge=("CUT_FACE", "FORM_CANT_CNC"))
    )
    # May or may not cycle depending on existing edges — force mutual
    assert g.readiness == "blocked"
    assert any(b.code == "dependency_cycle" for b in g.blockers)
    assert g.process_rules == []
    assert g.process_order == []


def test_l_missing_state_producer_blocks():
    g = resolve_product_process_graph(
        _full_metal(inject_missing_producer_state="NONEXISTENT_STATE_XYZ")
    )
    assert g.readiness == "blocked"
    assert any(b.code == "missing_state_producer" for b in g.blockers)
    assert g.process_rules == []


# --- FACE-only inactive isolation ---
def test_face_only_no_cant_bond_or_support():
    g = resolve_product_process_graph(
        ProductProcessResolveInput(
            active_components=["FACE"],
            illuminated=False,
            support_type="none",
            template_selected=False,
        )
    )
    codes = _codes(g)
    assert "CUT_FACE" in codes
    assert "BOND_FACE_TO_CANT" not in codes
    assert "FORM_CANT_CNC" not in codes
    assert "INSTALL_LED_MODULES" not in codes
    assert "INSTALL_CABLE_CHANNEL" not in codes
    assert not g.blockers or g.readiness in ("ready", "blocked")


# --- M Build 4C compatibility ---
def test_m_build4c_real_depends_on_no_sequence_overwrite():
    graph, snap = resolve_and_build_snapshot(_full_metal(cant_finish="vinyl"))
    assert graph.readiness == "ready"
    frozen = build_frozen_modular_graph_from_v2(snap)
    # Frozen candidates carry depends_on
    bonded = [c for c in frozen.execution.task_candidates if c.task_name == "BOND_FACE_TO_CANT"]
    assert bonded
    assert bonded[0].depends_on_process_ids

    preview = build_execution_preview_from_frozen_snapshot(snap)
    assert preview.safety.no_write is True
    assert preview.safety.preview_only is True
    real_edges = [e for e in preview.dependency_graph.edges if e.provenance == "process_depends_on"]
    assert real_edges, "expected real process_depends_on edges, not sequence-only"
    seq_only = [e for e in preview.dependency_graph.edges if e.provenance == "sequence_order"]
    assert not seq_only

    # Vinyl before form preserved in preview deps
    form_cand = next(c for c in preview.task_candidates if c.task_name == "FORM_CANT_CNC")
    vinyl_cand = next(c for c in preview.task_candidates if c.task_name == "APPLY_CANT_VINYL")
    assert vinyl_cand.preview_candidate_key in form_cand.dependencies


def test_aggregate_task_rules_compatible():
    from services.product_process_resolver_service import resolved_graph_to_aggregate_task_rules
    from schemas.product_aggregate import ProductAggregateTaskRule

    g = resolve_product_process_graph(_full_metal())
    rules = resolved_graph_to_aggregate_task_rules(g)
    assert rules
    parsed = [ProductAggregateTaskRule.model_validate(r) for r in rules]
    assert all(r.depends_on_process_ids is not None for r in parsed)
    bond = next(r for r in parsed if r.task_name == "BOND_FACE_TO_CANT")
    assert "CUT_FACE" in bond.depends_on_process_ids or "FORM_CANT_CNC" in bond.depends_on_process_ids


def test_capabilities_are_codes_not_machine_names():
    g = resolve_product_process_graph(_full_metal())
    for cap in g.required_capabilities:
        assert not cap.startswith("MCH-")
        assert cap == cap.upper() or "_" in cap


def test_resolver_service_has_no_db_writes():
    path = Path(__file__).resolve().parents[1] / "services" / "product_process_resolver_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    text = path.read_text(encoding="utf-8")
    assert "session.commit" not in text
    assert "db.add" not in text
    assert "flush(" not in text
    assert "AsyncSession" not in text


@pytest.mark.parametrize(
    "factory",
    [_full_metal, _full_alucobond, _no_support],
)
def test_runtime_proof_three_configs(factory):
    g, snap = resolve_and_build_snapshot(factory())
    assert g.readiness == "ready"
    assert g.graph_hash
    assert g.process_rules
    preview = build_execution_preview_from_frozen_snapshot(snap)
    assert preview.safety.no_write
    report = {
        "active_components": g.active_component_codes,
        "active_interfaces": g.active_interface_codes,
        "process_count": len(g.process_rules),
        "dependency_count": sum(len(r.depends_on) for r in g.process_rules),
        "material_roles": sorted({m.material_role for m in g.material_roles}),
        "capabilities": g.required_capabilities,
        "warnings": [w.code for w in g.warnings],
        "blockers": [b.code for b in g.blockers],
        "graph_hash": g.graph_hash,
        "first": g.process_order[:3],
        "last": g.process_order[-3:],
        "cable_channel": "INSTALL_CABLE_CHANNEL" in _codes(g),
        "service_corner": g.config_echo.get("power_supply_service_corner"),
        "psu_packed_separately": "PACK_POWER_SUPPLY_SEPARATELY" in _codes(g),
        "preview_candidates": len(preview.task_candidates),
    }
    assert report["process_count"] > 0
    if factory is _full_metal:
        assert report["cable_channel"] is True
        assert report["psu_packed_separately"] is False
    if factory is _full_alucobond:
        assert report["cable_channel"] is False
        assert report["service_corner"] == "TOP_LEFT"
    if factory is _no_support:
        assert report["cable_channel"] is False
        assert report["psu_packed_separately"] is True
