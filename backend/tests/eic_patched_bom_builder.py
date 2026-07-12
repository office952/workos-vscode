"""Test helper: workspace-aware Cost BOM builder with fixed rates (EIC tests)."""

from __future__ import annotations

from typing import Any

from services.aggregate_cost_bom_adapter import AggregateCostBomAdapter
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
