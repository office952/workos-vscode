"""Test helper: workspace-aware Cost BOM builder with fixed rates (EIC tests)."""

from __future__ import annotations

from typing import Any

from services.aggregate_cost_bom_adapter import AggregateCostBomAdapter
from services.estimated_internal_cost_service import (
    _is_linked_logo_bom_material,
    _is_linked_logo_bom_operation,
)
from services.product_aggregate_service import ProductAggregateService
from services.product_definition_builder_service import ProductDefinitionBuilderService


class PatchedAggregateCostBomBuilder:
    """Mirrors AggregateCostBomBuilderService orchestration with injected test rates."""

    def __init__(
        self,
        db,
        *,
        material_rates: dict[str, float],
        inventory_catalog: dict[str, dict],
        workcenter_rates: dict[str, float] | None = None,
    ) -> None:
        self._db = db
        self._material_rates = material_rates
        self._inventory_catalog = inventory_catalog
        self._workcenter_rates = workcenter_rates or {"WC_CNC_ROUTING": 120.0}
        self._adapter = AggregateCostBomAdapter()

    async def build_preview(
        self,
        template_code: str,
        *,
        workspace_id: str | None = None,
        quote_input: dict[str, Any] | None = None,
    ):
        pd_builder = ProductDefinitionBuilderService(self._db)
        aggregate_svc = ProductAggregateService(self._db)

        pd = await pd_builder.build_preview(template_code, workspace_id=workspace_id)
        if pd is None:
            return None
        if workspace_id:
            aggregate = await aggregate_svc.build_for_workspace(template_code, workspace_id)
        else:
            aggregate = await aggregate_svc.build(template_code)
        if aggregate is None:
            return None

        return self._adapter.build(
            product_definition=pd,
            aggregate=aggregate,
            quote_input=quote_input,
            material_rates=self._material_rates,
            workcenter_rates=self._workcenter_rates,
            material_currencies={code: "RON" for code in self._material_rates},
            inventory_catalog=self._inventory_catalog,
        )


class FilteredLogoBomBuilder(PatchedAggregateCostBomBuilder):
    """Test-only partial-state helper: filter linked-logo BOM rows without changing production BOM."""

    def __init__(
        self,
        db,
        *,
        material_rates: dict[str, float],
        inventory_catalog: dict[str, dict],
        workcenter_rates: dict[str, float] | None = None,
        allowed_logo_operation_codes: frozenset[str] | None = None,
        allowed_logo_material_codes: frozenset[str] | None = None,
    ) -> None:
        super().__init__(
            db,
            material_rates=material_rates,
            inventory_catalog=inventory_catalog,
            workcenter_rates=workcenter_rates,
        )
        self._allowed_logo_ops = allowed_logo_operation_codes
        self._allowed_logo_mats = allowed_logo_material_codes

    async def build_preview(
        self,
        template_code: str,
        *,
        workspace_id: str | None = None,
        quote_input: dict[str, Any] | None = None,
    ):
        bom = await super().build_preview(
            template_code,
            workspace_id=workspace_id,
            quote_input=quote_input,
        )
        if bom is None:
            return bom
        if self._allowed_logo_ops is not None:
            bom.costable_operations = [
                op
                for op in bom.costable_operations
                if not _is_linked_logo_bom_operation(op) or op.operation_code in self._allowed_logo_ops
            ]
        if self._allowed_logo_mats is not None:
            bom.costable_materials = [
                mat
                for mat in bom.costable_materials
                if not _is_linked_logo_bom_material(mat) or mat.material_code in self._allowed_logo_mats
            ]
        return bom
