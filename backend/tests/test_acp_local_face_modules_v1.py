"""ACP local face-module contracts — persistence, PD projection, inactive isolation."""

from __future__ import annotations

from data.product_system.acp_face_treatment_registry_v1 import (
    FACE_TREATMENT_ACRYLIC_INSERT,
    FACE_TREATMENT_APPLIED_VOLUMETRIC,
    FACE_TREATMENT_ROUTED_BACKLIT,
)
from data.product_system.acp_local_face_modules_v1 import (
    ELECTRICAL_OWNERSHIP_MODE,
    INSERT_THICKNESS_OWNER_VARIANT_MM,
    INSERT_THICKNESS_PROVENANCE,
    MODULE_ACRYLIC_INSERT,
    MODULE_ROUTED_BACKLIT,
    list_local_face_modules,
    module_code_for_treatment,
)
from services.acp_local_face_module_service import (
    build_local_module_aggregate_projection,
    normalize_local_module,
)
from services.product_definition_builder_service import _build_canonical_values
from services.svg_component_binding_persistence import (
    build_acp_local_modules_aggregate_from_finish,
    persist_normalized_bindings_on_finish,
    read_svg_component_bindings,
)


def _binding(
    *,
    binding_id: str,
    role: str,
    code: str,
    treatment: str,
    status: str = "CONFIRMED",
    layers: list[str] | None = None,
    module: dict | None = None,
) -> dict:
    row = {
        "binding_id": binding_id,
        "geometry_role": role,
        "component_template_code": code,
        "selection_mode": "LAYER_OR_GROUP",
        "selected_geometry": {
            "layer_ids": layers or [binding_id],
            "group_ids": [],
            "element_ids": [],
            "geometry_hashes": [],
            "source_svg_hash": "svg_h",
        },
        "configuration": {},
        "status": status,
        "face_treatment_code": treatment,
    }
    if module is not None:
        row["local_module_configuration"] = module
    return row


def test_registry_modules_and_treatment_map():
    codes = {m["module_code"] for m in list_local_face_modules()}
    assert MODULE_ROUTED_BACKLIT in codes
    assert MODULE_ACRYLIC_INSERT in codes
    assert module_code_for_treatment(FACE_TREATMENT_ROUTED_BACKLIT) == MODULE_ROUTED_BACKLIT
    assert module_code_for_treatment(FACE_TREATMENT_ACRYLIC_INSERT) == MODULE_ACRYLIC_INSERT


def test_insert_thickness_is_owner_confirmed_variant_not_sole():
    mod = normalize_local_module(
        None,
        binding_id="bind_ins",
        treatment_code=FACE_TREATMENT_ACRYLIC_INSERT,
        geometry_role="ACRYLIC_INSERT",
        component_template_code="TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
        status="CONFIRMED",
    )
    assert mod is not None
    assert mod["insert"]["thickness_mm"] == INSERT_THICKNESS_OWNER_VARIANT_MM
    assert mod["insert"]["thickness_provenance"] == INSERT_THICKNESS_PROVENANCE
    assert mod["insert"]["sole_thickness_admitted"] is False
    assert mod["readiness"]["overall"] == "LOCAL_CONFIGURATION_REQUIRED"
    assert any(g["status"] == "OWNER_GATE_REQUIRED" for g in mod["readiness"]["gates"])


def test_persist_mixed_modules_and_electrical_shell_ownership():
    finish = persist_normalized_bindings_on_finish(
        {
            "svg_component_bindings": [
                _binding(
                    binding_id="bind_letters",
                    role="LETTER_VECTOR_SET",
                    code="TPL-VOLUMETRIC-FACE_v1",
                    treatment=FACE_TREATMENT_APPLIED_VOLUMETRIC,
                    layers=["L1"],
                ),
                _binding(
                    binding_id="bind_cut",
                    role="CUTOUT_TEXT",
                    code="TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                    treatment=FACE_TREATMENT_ROUTED_BACKLIT,
                    layers=["C1"],
                ),
                _binding(
                    binding_id="bind_ins",
                    role="ACRYLIC_INSERT",
                    code="TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                    treatment=FACE_TREATMENT_ACRYLIC_INSERT,
                    layers=["I1"],
                ),
                _binding(
                    binding_id="bind_support",
                    role="SUPPORT_CONTOUR",
                    code="TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                    treatment="NOT_APPLICABLE",
                    layers=[],
                ),
            ],
            "power_supply_service_corner": "BOTTOM_RIGHT",
        }
    )
    bindings = {b["geometry_role"]: b for b in read_svg_component_bindings(finish)}
    assert bindings["CUTOUT_TEXT"]["local_module_configuration"]["module_code"] == MODULE_ROUTED_BACKLIT
    assert bindings["ACRYLIC_INSERT"]["local_module_configuration"]["module_code"] == MODULE_ACRYLIC_INSERT
    assert (
        bindings["LETTER_VECTOR_SET"]["local_module_configuration"]["module_code"]
        == "ACP-APPLIED-COMPONENT-INTERFACE"
    )
    electrical = finish["acp_electrical_configuration"]
    assert electrical["ownership_mode"] == ELECTRICAL_OWNERSHIP_MODE
    assert electrical["service_corner"] == "BOTTOM_RIGHT"
    assert len(electrical["zone_intents"]) >= 2
    assert "quantity" not in str(electrical).lower() or "GUARDED" in str(
        build_acp_local_modules_aggregate_from_finish(finish)
    )


def test_inactive_module_zero_leakage_in_aggregate():
    finish = persist_normalized_bindings_on_finish(
        {
            "svg_component_bindings": [
                _binding(
                    binding_id="bind_cut",
                    role="CUTOUT_TEXT",
                    code="TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                    treatment=FACE_TREATMENT_ROUTED_BACKLIT,
                    layers=["C1"],
                ),
                _binding(
                    binding_id="bind_ins",
                    role="ACRYLIC_INSERT",
                    code="TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                    treatment=FACE_TREATMENT_ACRYLIC_INSERT,
                    status="INACTIVE",
                    layers=["I1"],
                ),
            ]
        }
    )
    proj = build_acp_local_modules_aggregate_from_finish(finish)
    assert proj is not None
    codes = {m["module_code"] for m in proj["modules"]}
    assert MODULE_ROUTED_BACKLIT in codes
    assert MODULE_ACRYLIC_INSERT not in codes
    assert proj["quantity_status"] == "GUARDED"
    for m in proj["modules"]:
        assert m.get("quantity_status") == "GUARDED"
        assert "material_qty" not in m


def test_product_definition_compiles_local_modules_guarded():
    finish = persist_normalized_bindings_on_finish(
        {
            "svg_component_bindings": [
                _binding(
                    binding_id="bind_cut",
                    role="CUTOUT_TEXT",
                    code="TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                    treatment=FACE_TREATMENT_ROUTED_BACKLIT,
                    layers=["C1"],
                ),
                _binding(
                    binding_id="bind_ins",
                    role="ACRYLIC_INSERT",
                    code="TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                    treatment=FACE_TREATMENT_ACRYLIC_INSERT,
                    layers=["I1"],
                ),
            ],
            "svg_support_selection": {
                "schema": "svg_support_selection_v1",
                "status": "confirmed",
                "role": "ALUCOBOND_CASED_PANEL",
                "contour_id": "cc1",
            },
        }
    )
    values = _build_canonical_values([], {"finish_setup": finish})
    modules = values.get("acp_local_face_module_instances")
    assert modules, f"expected local modules in PD, got keys={sorted(values.keys())[:40]}"
    assert len(modules) == 2
    proj = values.get("acp_local_face_modules_aggregate_projection")
    assert proj and proj["quantity_status"] == "GUARDED"
    assert build_local_module_aggregate_projection(modules)["quantity_status"] == "GUARDED"


def test_stable_module_instance_ids_across_normalize():
    raw = _binding(
        binding_id="bind_cut_stable",
        role="CUTOUT_TEXT",
        code="TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
        treatment=FACE_TREATMENT_ROUTED_BACKLIT,
        layers=["C1"],
    )
    a = persist_normalized_bindings_on_finish({"svg_component_bindings": [raw]})
    mid = a["svg_component_bindings"][0]["local_module_configuration"]["module_instance_id"]
    b = persist_normalized_bindings_on_finish(
        {"svg_component_bindings": a["svg_component_bindings"]}
    )
    assert b["svg_component_bindings"][0]["local_module_configuration"]["module_instance_id"] == mid
