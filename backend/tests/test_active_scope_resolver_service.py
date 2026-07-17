"""Letters Slice 1 — canonical active-scope compiler."""

from __future__ import annotations

from services.active_scope_resolver_service import (
    COMPOSITION_ONLY_EXECUTION_OPS,
    compile_active_scope,
)

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


def _scope(*, mode: str, sold: list[str]) -> dict:
    return {
        "contract_version": "offer_scope_contract/v1",
        "mode": mode,
        "sold_modules": sold,
    }


def test_full_product_legacy_passthrough() -> None:
    result = compile_active_scope(
        template_code=TEMPLATE,
        payload={"offer_scope": _scope(mode="full_product", sold=[])},
    )
    assert result.use_legacy_full_product is True
    assert result.mode == "full_product"
    assert result.active_runtime_modules == []


def test_return_cant_only_active_modules() -> None:
    result = compile_active_scope(
        template_code=TEMPLATE,
        payload={"offer_scope": _scope(mode="component_subset", sold=["RETURN-CANT"])},
    )
    assert result.use_legacy_full_product is False
    assert result.sold_module_codes == ["RETURN-CANT"]
    assert set(result.active_runtime_modules) == {"modelare_cant", "geometry_svg"}
    assert "debitare_fata" in result.inactive_runtime_modules
    assert "debitare_spate" in result.inactive_runtime_modules
    assert "sistem_led" in result.inactive_runtime_modules
    assert "finisaje" in result.inactive_runtime_modules
    assert "PERIMETER" in result.calculation_prerequisites
    assert set(result.commercial_scope_modules) == {"modelare_cant"}
    assert "return_face_bonding" in result.composition_excluded_operations
    assert "return_face_bonding" in COMPOSITION_ONLY_EXECUTION_OPS
    assert "MAT-ADEZIV-CANT-LITERE" in result.composition_excluded_materials
    assert "adhesive_return_to_face" in result.composition_excluded_materials


def test_face_only_active_modules() -> None:
    result = compile_active_scope(
        template_code=TEMPLATE,
        payload={"offer_scope": _scope(mode="component_subset", sold=["FACE"])},
    )
    assert set(result.commercial_scope_modules) == {"debitare_fata"}
    assert "geometry_svg" in result.active_runtime_modules
    assert "modelare_cant" not in result.active_runtime_modules


def test_back_only_active_modules() -> None:
    result = compile_active_scope(
        template_code=TEMPLATE,
        payload={"offer_scope": _scope(mode="component_subset", sold=["BACK"])},
    )
    assert set(result.commercial_scope_modules) == {"debitare_spate"}


def test_lighting_only_maps_to_sistem_led() -> None:
    result = compile_active_scope(
        template_code=TEMPLATE,
        payload={
            "offer_scope": _scope(mode="component_subset", sold=["LIGHTING"]),
            "finish_setup": {"illuminated": True, "lighting_system_type": "front_lit"},
        },
    )
    assert "sistem_led" in result.commercial_scope_modules
    assert "debitare_fata" not in result.commercial_scope_modules


def test_unknown_module_errors() -> None:
    result = compile_active_scope(
        template_code=TEMPLATE,
        payload={"offer_scope": _scope(mode="component_subset", sold=["NOT-A-MODULE"])},
    )
    assert result.errors
    assert result.commercial_scope_modules == []


def test_composition_dependency_not_universal_active() -> None:
    result = compile_active_scope(
        template_code=TEMPLATE,
        payload={"offer_scope": _scope(mode="component_subset", sold=["RETURN-CANT"])},
    )
    assert "return_face_bonding" not in result.active_runtime_modules
    classes = {d.dependency_class for d in result.dependencies if d.code == "return_face_bonding"}
    assert "composition_only" in classes
