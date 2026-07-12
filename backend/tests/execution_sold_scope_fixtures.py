"""Shared fixtures for execution sold-scope filtering tests."""

from __future__ import annotations

from schemas.order_snapshot_v2 import OrderSnapshotV2
from schemas.product_aggregate import (
    ProductAggregate,
    ProductAggregateOperation,
    ProductAggregateTaskContract,
    ProductAggregateTaskRule,
)
from schemas.product_definition import (
    ProductDefinitionOperationRole,
    ProductDefinitionPreview,
    ProductDefinitionSourceContext,
)
from schemas.quote_snapshot_v2 import QuoteSnapshotOfferScope
from tests.test_quote_snapshot_v2_accept_gate import _commercial_preview, _internal_preview

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


def offer_scope(
    *,
    mode: str = "component_subset",
    sold: list[str] | None = None,
    runtime: list[str] | None = None,
    use_legacy: bool = False,
) -> QuoteSnapshotOfferScope:
    sold_modules = sold or []
    runtime_modules = runtime if runtime is not None else sold_modules
    return QuoteSnapshotOfferScope(
        mode=mode,  # type: ignore[arg-type]
        sold_modules=sold_modules,
        resolved_runtime_sold_modules=runtime_modules,
        use_legacy=use_legacy,
    )


def sample_product_definition() -> ProductDefinitionPreview:
    return ProductDefinitionPreview(
        template_code=TEMPLATE,
        source_context=ProductDefinitionSourceContext(template_code=TEMPLATE),
        operation_roles=[
            ProductDefinitionOperationRole(
                operation_code="face_cnc_cut",
                label="Face CNC Cut",
                workcenter="WC_CNC",
            ),
            ProductDefinitionOperationRole(
                operation_code="electrical_letters",
                label="Electrical Wiring",
                workcenter="WC_ELECTRICAL",
            ),
        ],
    )


def sold_scope_dossier_aggregate() -> ProductAggregate:
    """Dossier-shaped aggregate with mini_module_code on rules and operations."""
    rules = [
        ProductAggregateTaskRule(
            task_name="vector_prep",
            task_type="file_preparation",
            priced_operation="vector_prep",
            sequence=1,
        ),
        ProductAggregateTaskRule(
            task_name="cnc_face_cut",
            task_type="cnc_routing",
            priced_operation="face_cnc_cut",
            mini_module_code="debitare_fata",
            sequence=2,
        ),
        ProductAggregateTaskRule(
            task_name="return_profile_forming",
            task_type="edge_bending",
            priced_operation="side_forming",
            mini_module_code="modelare_cant",
            sequence=3,
        ),
        ProductAggregateTaskRule(
            task_name="return_face_bonding",
            task_type="volumetric_letter_assembly",
            priced_operation="return_face_bonding",
            mini_module_code="asamblare",
            sequence=4,
        ),
        ProductAggregateTaskRule(
            task_name="cnc_back_cut",
            task_type="cnc_routing",
            priced_operation="back_cut",
            mini_module_code="debitare_spate",
            sequence=5,
        ),
        ProductAggregateTaskRule(
            task_name="vinyl_application",
            task_type="vinyl_cutting",
            priced_operation="vinyl_application",
            mini_module_code="colantare_fata",
            sequence=6,
        ),
        ProductAggregateTaskRule(
            task_name="painting",
            task_type="volumetric_letter_assembly",
            priced_operation="painting",
            mini_module_code="finisaje",
            sequence=7,
        ),
        ProductAggregateTaskRule(
            task_name="led_installation",
            task_type="led_assembly",
            priced_operation="led_install_letters",
            mini_module_code="sistem_led",
            sequence=8,
        ),
        ProductAggregateTaskRule(
            task_name="electrical_wiring",
            task_type="led_wiring",
            priced_operation="electrical_letters",
            mini_module_code="electrica_litere",
            sequence=9,
        ),
        ProductAggregateTaskRule(
            task_name="mounting_template",
            task_type="cnc_routing",
            priced_operation="mounting_template_cnc_cut",
            mini_module_code="sablon_montaj",
            sequence=10,
        ),
        ProductAggregateTaskRule(
            task_name="linked_logo_apply",
            task_type="vinyl_cutting",
            priced_operation="vinyl_application",
            mini_module_code="colantare_fata",
            sequence=11,
            trigger_condition="linked_segment:logo_instance_001",
        ),
    ]
    operations = [
        ProductAggregateOperation(
            operation_code="vector_prep",
            label="Vector Prep",
            workcenter="WC_PREPRESS",
        ),
        ProductAggregateOperation(
            operation_code="face_cnc_cut",
            label="Face CNC Cut",
            workcenter="WC_CNC",
            mini_module_code="debitare_fata",
        ),
        ProductAggregateOperation(
            operation_code="side_forming",
            label="Side Forming",
            workcenter="WC_FORMING",
            mini_module_code="modelare_cant",
        ),
        ProductAggregateOperation(
            operation_code="return_face_bonding",
            label="Return Face Bonding",
            workcenter="WC_ASSEMBLY",
            mini_module_code="asamblare",
        ),
        ProductAggregateOperation(
            operation_code="back_cut",
            label="Back Cut",
            workcenter="WC_CNC",
            mini_module_code="debitare_spate",
        ),
        ProductAggregateOperation(
            operation_code="vinyl_application",
            label="Vinyl Application",
            workcenter="WC_VINYL",
            mini_module_code="colantare_fata",
        ),
        ProductAggregateOperation(
            operation_code="painting",
            label="Painting",
            workcenter="WC_PAINT",
            mini_module_code="finisaje",
        ),
        ProductAggregateOperation(
            operation_code="led_install_letters",
            label="LED Install",
            workcenter="WC_LED",
            mini_module_code="sistem_led",
        ),
        ProductAggregateOperation(
            operation_code="electrical_letters",
            label="Electrical",
            workcenter="WC_ELECTRICAL",
            mini_module_code="electrica_litere",
        ),
        ProductAggregateOperation(
            operation_code="mounting_template_cnc_cut",
            label="Mounting Template",
            workcenter="WC_CNC",
            mini_module_code="sablon_montaj",
        ),
        ProductAggregateOperation(
            operation_code="logo_vinyl",
            label="Logo Vinyl",
            workcenter="WC_VINYL",
            component_ref="linked_segment:logo_instance_001::comp_face",
            provenance="linked_module",
            mini_module_code="colantare_fata",
        ),
    ]
    return ProductAggregate(
        template_code=TEMPLATE,
        template_id=1,
        operations=operations,
        task_contract=ProductAggregateTaskContract(task_rules=rules),
    )


def snapshot_with_scope(
    *,
    offer_scope: QuoteSnapshotOfferScope | None,
    aggregate: ProductAggregate | None = None,
    quote_id: int = 1,
    quote_snapshot_v2_id: int = 1,
) -> OrderSnapshotV2:
    return OrderSnapshotV2(
        quote_id=quote_id,
        quote_snapshot_v2_id=quote_snapshot_v2_id,
        snapshot_code="OSN2-SCOPE-001",
        content_hash="scopehashscopehashscopehashscopehash",
        product_definition_snapshot=sample_product_definition(),
        product_aggregate_snapshot=aggregate or sold_scope_dossier_aggregate(),
        commercial_price_proposal_snapshot=_commercial_preview(total=1500.0),
        estimated_internal_cost_snapshot=_internal_preview(total=620.0),
        accepted_commercial_total=1500.0,
        accepted_currency="RON",
        estimated_internal_total=620.0,
        offer_scope_snapshot=offer_scope,
    )
