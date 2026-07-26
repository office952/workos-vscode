"""ProductAggregate selected-graph filter — Letters Slice 1."""

from __future__ import annotations

import copy
import json
import uuid

import pytest

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from schemas.product_aggregate import (
    ProductAggregate,
    ProductAggregateComponent,
    ProductAggregateMaterial,
    ProductAggregateOperation,
    ProductAggregateTaskContract,
    ProductAggregateTaskRule,
)
from schemas.product_definition import ProductDefinitionPreview, ProductDefinitionSourceContext
from data.mini_module_registry_volumetric_v2 import CHILD_TEMPLATE_TO_MODULE
from services.active_scope_resolver_service import compile_active_scope
from services.product_aggregate_active_scope_filter import filter_aggregate_by_active_scope
from services.product_aggregate_service import ProductAggregateService
from tests.eic_workspace_logo_fixtures import confirmed_bindings_payload

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


def _pd() -> ProductDefinitionPreview:
    return ProductDefinitionPreview(
        template_code=TEMPLATE,
        source_context=ProductDefinitionSourceContext(template_code=TEMPLATE),
    )


def _offer(*, sold: list[str]) -> dict:
    return {
        "offer_scope": {
            "contract_version": "offer_scope_contract/v1",
            "mode": "component_subset",
            "sold_modules": sold,
        }
    }


def test_filter_drops_unmapped_parent_and_unsold_modules() -> None:
    aggregate = ProductAggregate(
        template_code=TEMPLATE,
        template_id=1,
        components=[
            ProductAggregateComponent(component_id="comp_face_litere", role="face"),
            ProductAggregateComponent(component_id="comp_lateral_litere", role="return"),
            ProductAggregateComponent(component_id="comp_orphan_parent", role="unknown"),
        ],
        materials=[
            ProductAggregateMaterial(
                material_code="FACE_SHEET",
                component_ref="comp_face_litere",
                provenance="dossier",
            ),
            ProductAggregateMaterial(
                material_code="RETURN_ALU",
                component_ref="comp_lateral_litere",
                provenance="dossier",
            ),
        ],
        operations=[
            ProductAggregateOperation(
                operation_code="face_cnc_cut",
                component_ref="comp_face_litere",
                provenance="dossier",
            ),
            ProductAggregateOperation(
                operation_code="side_forming",
                component_ref="comp_lateral_litere",
                provenance="dossier",
            ),
            ProductAggregateOperation(
                operation_code="return_face_bonding",
                component_ref="comp_lateral_litere",
                provenance="dossier",
                mini_module_code="modelare_cant",
            ),
        ],
        task_contract=ProductAggregateTaskContract(
            task_rules=[
                ProductAggregateTaskRule(
                    task_name="return_profile_forming",
                    priced_operation="side_forming",
                    mini_module_code="modelare_cant",
                ),
                ProductAggregateTaskRule(
                    task_name="bond",
                    priced_operation="return_face_bonding",
                    mini_module_code="modelare_cant",
                ),
            ]
        ),
    )
    scope = compile_active_scope(template_code=TEMPLATE, payload=_offer(sold=["RETURN-CANT"]))
    filtered = filter_aggregate_by_active_scope(aggregate, pd=_pd(), scope=scope)
    comp_ids = {c.component_id for c in filtered.components}
    assert "comp_lateral_litere" in comp_ids
    assert "comp_face_litere" not in comp_ids
    assert "comp_orphan_parent" not in comp_ids
    # Geometry calc prerequisite may emit an identity row.
    assert comp_ids <= {"comp_lateral_litere", "comp_geometry_svg_gate"}
    assert {m.material_code for m in filtered.materials} == {"RETURN_ALU"}
    op_codes = {o.operation_code for o in filtered.operations}
    assert "side_forming" in op_codes
    assert "face_cnc_cut" not in op_codes
    assert "return_face_bonding" not in op_codes
    rule_ops = {r.priced_operation for r in filtered.task_contract.task_rules}
    assert "side_forming" in rule_ops
    assert "return_face_bonding" not in rule_ops


@pytest.mark.asyncio
async def test_workspace_aggregate_return_cant_selected_graph(volumetric_v2_db) -> None:
    payload = copy.deepcopy(confirmed_bindings_payload())
    payload["product_composition_confirmed"] = {"confirmed": True}
    payload["svg_source"]["file_hash"] = "test-hash-agg-scope"
    payload["offer_scope"] = {
        "contract_version": "offer_scope_contract/v1",
        "mode": "component_subset",
        "sold_modules": ["RETURN-CANT"],
    }
    payload["offer_scope_confirmed"] = {"confirmed": True}
    workspace_id = str(uuid.uuid4())
    volumetric_v2_db.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"IV6-AGG-SCOPE-{workspace_id[:8]}",
            title="Agg active scope",
            template_code=TEMPLATE,
            status="ready_for_quote_preview",
            payload_json=json.dumps(payload),
        )
    )
    await volumetric_v2_db.commit()

    aggregate = await ProductAggregateService(volumetric_v2_db).build_for_workspace(
        TEMPLATE, workspace_id
    )
    assert aggregate is not None
    assert aggregate.components, "RETURN-CANT must emit aluminum/return components"
    modules = {
        c.mini_module_code
        or CHILD_TEMPLATE_TO_MODULE.get(c.source_template_code or "", "")
        for c in aggregate.components
    }
    assert "modelare_cant" in modules
    assert "debitare_fata" not in modules
    assert "sistem_led" not in modules
    bonding = {
        o.operation_code
        for o in aggregate.operations
        if "bonding" in (o.operation_code or "").lower()
    }
    assert not bonding
    if aggregate.commercial_measurements is not None:
        active_meas = [
            m
            for m in aggregate.commercial_measurements.measurements
            if m.resolution_status not in ("not_applicable",)
            and m.module_code
            and m.module_code not in ("modelare_cant", "geometry_svg", None)
        ]
        # Unsold commercial modules must not emit resolved measurements.
        forbidden = {"debitare_fata", "debitare_spate", "sistem_led"}
        for m in aggregate.commercial_measurements.measurements:
            if m.module_code in forbidden:
                assert m.resolution_status == "not_applicable"
