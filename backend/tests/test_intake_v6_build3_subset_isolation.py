"""Build 3 — subset activation + FACE+CANT interface isolation."""

from __future__ import annotations

import pytest

from schemas.intake_v4 import (
    IntakeV4MaterialBreakdownResponse,
    IntakeV4MaterialBreakdownTotals,
    IntakeV4MaterialQuantityRow,
)
from services.active_scope_resolver_service import compile_active_scope
from services.intake_v6_modular_form_contract_service import IntakeV6ModularFormContractService
from services.intake_v6_offer_scope_live_calc_service import filter_material_breakdown_by_offer_scope
from services.product_aggregate_active_scope_filter import filter_aggregate_by_active_scope
from schemas.product_aggregate import (
    ProductAggregate,
    ProductAggregateMaterial,
    ProductAggregateOperation,
)
from schemas.product_definition import ProductDefinitionPreview, ProductDefinitionSourceContext

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


def _offer(*, mode: str, sold: list[str]) -> dict:
    return {
        "offer_scope": {
            "contract_version": "offer_scope_contract/v1",
            "mode": mode,
            "sold_modules": sold,
        }
    }


def _pd() -> ProductDefinitionPreview:
    return ProductDefinitionPreview(
        template_code=TEMPLATE,
        source_context=ProductDefinitionSourceContext(template_code=TEMPLATE),
    )


def test_build3_contract_subset_activation_enabled():
    contract = IntakeV6ModularFormContractService().get_for_template(TEMPLATE)
    assert contract is not None
    assert contract.summary.composition_authority is True
    assert contract.full_product_composition is not None
    assert contract.full_product_composition.subset_activation_enabled is True
    assert contract.full_product_composition.mode == "subset_activation"
    iface = contract.full_product_composition.interface_candidates[0]
    assert iface["owner"] == "interface_face_cant"
    assert iface["requires"] == ["FACE", "RETURN-CANT"]


def test_cant_only_excludes_interface_materials_and_bonding():
    result = compile_active_scope(
        template_code=TEMPLATE,
        payload=_offer(mode="component_subset", sold=["RETURN-CANT"]),
    )
    assert result.use_legacy_full_product is False
    assert "MAT-ADEZIV-CANT-LITERE" in result.composition_excluded_materials
    assert "adhesive_return_to_face" in result.composition_excluded_materials
    assert "return_face_bonding" in result.composition_excluded_operations
    assert result.provenance.get("interface_face_cant_active") is False


def test_face_only_excludes_interface_materials():
    result = compile_active_scope(
        template_code=TEMPLATE,
        payload=_offer(mode="component_subset", sold=["FACE"]),
    )
    assert "MAT-ADEZIV-CANT-LITERE" in result.composition_excluded_materials
    assert "modelare_cant" not in result.active_runtime_modules


def test_face_cant_keeps_interface_materials():
    result = compile_active_scope(
        template_code=TEMPLATE,
        payload=_offer(mode="component_subset", sold=["FACE", "RETURN-CANT"]),
    )
    assert result.composition_excluded_materials == []
    assert result.provenance.get("interface_face_cant_active") is True
    assert {"debitare_fata", "modelare_cant"} <= set(result.active_runtime_modules)


def test_full_product_legacy_has_no_composition_exclusions():
    result = compile_active_scope(
        template_code=TEMPLATE,
        payload=_offer(mode="full_product", sold=[]),
    )
    assert result.use_legacy_full_product is True
    assert result.composition_excluded_materials == []
    assert result.composition_excluded_operations == []


def test_aggregate_filter_silences_adhesive_for_cant_only():
    aggregate = ProductAggregate(
        template_code=TEMPLATE,
        template_id=1,
        materials=[
            ProductAggregateMaterial(
                material_code="MAT-PROFIL-LATERAL-LITERE",
                component_ref="comp_lateral_litere",
                mini_module_code="modelare_cant",
                provenance="dossier",
            ),
            ProductAggregateMaterial(
                material_code="MAT-ADEZIV-CANT-LITERE",
                component_ref="comp_lateral_litere",
                mini_module_code="modelare_cant",
                provenance="dossier",
            ),
        ],
        operations=[
            ProductAggregateOperation(
                operation_code="side_forming",
                component_ref="comp_lateral_litere",
                mini_module_code="modelare_cant",
                provenance="dossier",
            ),
            ProductAggregateOperation(
                operation_code="return_face_bonding",
                component_ref="comp_lateral_litere",
                mini_module_code="modelare_cant",
                provenance="dossier",
            ),
        ],
    )
    scope = compile_active_scope(
        template_code=TEMPLATE,
        payload=_offer(mode="component_subset", sold=["RETURN-CANT"]),
    )
    filtered = filter_aggregate_by_active_scope(aggregate, pd=_pd(), scope=scope)
    codes = {m.material_code for m in filtered.materials}
    assert "MAT-PROFIL-LATERAL-LITERE" in codes
    assert "MAT-ADEZIV-CANT-LITERE" not in codes
    ops = {o.operation_code for o in filtered.operations}
    assert "side_forming" in ops
    assert "return_face_bonding" not in ops


def test_aggregate_filter_keeps_adhesive_once_for_face_cant():
    aggregate = ProductAggregate(
        template_code=TEMPLATE,
        template_id=1,
        materials=[
            ProductAggregateMaterial(
                material_code="FACE_SHEET",
                component_ref="comp_face_litere",
                mini_module_code="debitare_fata",
                provenance="dossier",
            ),
            ProductAggregateMaterial(
                material_code="MAT-PROFIL-LATERAL-LITERE",
                component_ref="comp_lateral_litere",
                mini_module_code="modelare_cant",
                provenance="dossier",
            ),
            ProductAggregateMaterial(
                material_code="MAT-ADEZIV-CANT-LITERE",
                component_ref="comp_lateral_litere",
                mini_module_code="modelare_cant",
                provenance="dossier",
            ),
        ],
    )
    scope = compile_active_scope(
        template_code=TEMPLATE,
        payload=_offer(mode="component_subset", sold=["FACE", "RETURN-CANT"]),
    )
    filtered = filter_aggregate_by_active_scope(aggregate, pd=_pd(), scope=scope)
    adhesive = [m for m in filtered.materials if m.material_code == "MAT-ADEZIV-CANT-LITERE"]
    assert len(adhesive) == 1
    assert {m.material_code for m in filtered.materials} >= {
        "FACE_SHEET",
        "MAT-PROFIL-LATERAL-LITERE",
        "MAT-ADEZIV-CANT-LITERE",
    }


def _consumable_row(*, key: str, material_code: str, quantity: float) -> IntakeV4MaterialQuantityRow:
    return IntakeV4MaterialQuantityRow(
        material_key=key,
        display_name=key,
        category="consumable",
        quantity=quantity,
        unit="ml",
        quantity_source="test",
        quantity_quality="exact",
        quantity_with_waste=quantity,
        material_code=material_code,
    )


def test_live_calc_filters_adhesive_for_cant_only():
    breakdown = IntakeV4MaterialBreakdownResponse(
        workspace_id="ws-build3-cant",
        template_code=TEMPLATE,
        consumable_rows=[
            _consumable_row(
                key="adhesive_return_to_face",
                material_code="MAT-ADEZIV-CANT-LITERE",
                quantity=10.0,
            ),
            _consumable_row(
                key="return_material",
                material_code="MAT-PROFIL-LATERAL-LITERE",
                quantity=1.0,
            ),
        ],
        totals=IntakeV4MaterialBreakdownTotals(estimated_cost_total=0.0),
    )
    filtered = filter_material_breakdown_by_offer_scope(
        breakdown,
        payload_raw=_offer(mode="component_subset", sold=["RETURN-CANT"]),
    )
    keys = {row.material_key for row in filtered.consumable_rows}
    assert "return_material" in keys
    assert "adhesive_return_to_face" not in keys


def test_live_calc_keeps_adhesive_for_face_cant():
    breakdown = IntakeV4MaterialBreakdownResponse(
        workspace_id="ws-build3-face-cant",
        template_code=TEMPLATE,
        consumable_rows=[
            _consumable_row(
                key="adhesive_return_to_face",
                material_code="MAT-ADEZIV-CANT-LITERE",
                quantity=10.0,
            ),
        ],
        totals=IntakeV4MaterialBreakdownTotals(estimated_cost_total=0.0),
    )
    filtered = filter_material_breakdown_by_offer_scope(
        breakdown,
        payload_raw=_offer(mode="component_subset", sold=["FACE", "RETURN-CANT"]),
    )
    keys = [row.material_key for row in filtered.consumable_rows]
    assert keys.count("adhesive_return_to_face") == 1
