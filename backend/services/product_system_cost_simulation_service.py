"""
ProductSystem Cost Simulation Service — Build 7.

Provides read-only cost simulation without persisting any entity.
Reuses existing QuoteOrchestrator + CostEngine + ProductReadinessService.

Rules:
  - No Quote creation.
  - No Order creation.
  - No ProductTemplate mutation.
  - No Dossier mutation.
  - No Inventory mutation.
  - No ExecutionTask creation.
  - No AuditLog (no mutation to log).
  - Deterministic for same input + same registry state.
  - Auth protected (enforced at router level).
"""

from __future__ import annotations

import logging
from dataclasses import asdict, fields, is_dataclass
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from data_models.product_contracts import QuotePricing
from services.intake_product_spec_loader import load_intake_product_spec
from services.product_readiness_service import ProductReadinessService
from services.product_templates import Product_templatesService
from services.company_commercial_settings_service import get_default_vat_pct
from services.quote_orchestrator import QuoteOrchestrator
from services.volumetric_material_rate_resolver import is_volumetric_template_code
from services.aggregate_cost_bom_price_bridge import is_aggregate_cost_template
from services.volumetric_quote_ready_policy import evaluate_volumetric_quote_ready

logger = logging.getLogger(__name__)


class CostSimulationResult:
    """Structured result from a cost simulation run."""

    def __init__(
        self,
        *,
        template_id: int,
        template_code: str = "",
        cost_engine_version: str = "v1",
        persisted: bool = False,
        readiness: Optional[Dict[str, Any]] = None,
        cost_result: Optional[Dict[str, Any]] = None,
        component_breakdown: Optional[list] = None,
        linked_module_results: Optional[list] = None,
        warnings: Optional[list] = None,
        blockers: Optional[list] = None,
        status: str = "simulated",
        blocked_reasons: Optional[list] = None,
        trace: Optional[Dict[str, Any]] = None,
    ):
        self.simulation_id = None
        self.persisted = persisted
        self.template_id = template_id
        self.template_code = template_code
        self.cost_engine_version = cost_engine_version
        self.readiness = readiness or {}
        self.cost_result = cost_result or {}
        self.component_breakdown = component_breakdown or []
        self.linked_module_results = linked_module_results or []
        self.warnings = warnings or []
        self.blockers = blockers or []
        self.status = status
        self.blocked_reasons = blocked_reasons or []
        self.trace = trace or {
            "source": "product-system-cost-simulation",
            "no_persist": True,
            "used_template_snapshot": True,
            "used_costengine_formulas": True,
            "changed_entities": [],
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "persisted": self.persisted,
            "template_id": self.template_id,
            "template_code": self.template_code,
            "cost_engine_version": self.cost_engine_version,
            "readiness": self.readiness,
            "cost_result": self.cost_result,
            "component_breakdown": self.component_breakdown,
            "linked_module_results": self.linked_module_results,
            "warnings": self.warnings,
            "blockers": self.blockers,
            "status": self.status,
            "blocked_reasons": self.blocked_reasons,
            "trace": self.trace,
        }


class ProductSystemCostSimulationService:
    """Read-only cost simulation service.

    Reuses QuoteOrchestrator.build_snapshot() logic without persisting.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def simulate(
        self,
        template_id: int,
        quantity: int = 1,
        quote_input: Optional[Dict[str, Any]] = None,
        pricing: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None,
        simulation_context: Optional[Dict[str, Any]] = None,
        intake_id: Optional[int] = None,
        product_spec: Optional[Dict[str, Any]] = None,
    ) -> CostSimulationResult:
        """Run a cost simulation for a given template.

        Args:
            template_id: Product template ID.
            quantity: Number of units.
            quote_input: Per-quote formula inputs (width, height, path_length, etc.).
            pricing: Commercial parameters (margin_pct, discount_pct, vat_pct).
            options: Reserved for future variant selection.
            simulation_context: Metadata about the simulation request.

        Returns:
            CostSimulationResult with cost breakdown and readiness info.
        """
        quote_input = quote_input or {}
        pricing_dict = pricing or {}
        simulation_context = simulation_context or {}

        # --- Step 1: Load template ---
        template_service = Product_templatesService(self.db)
        template_obj = await template_service.get_by_id(template_id)

        if not template_obj:
            return CostSimulationResult(
                template_id=template_id,
                status="error",
                blockers=["template_not_found"],
                blocked_reasons=["template_not_found"],
                trace={
                    "source": "product-system-cost-simulation",
                    "no_persist": True,
                    "used_template_snapshot": False,
                    "used_costengine_formulas": False,
                    "changed_entities": [],
                    "error": "template_not_found",
                },
            )

        from services.active_template_scope import template_active_for_quote

        template_code = str(template_obj.template_code or "").strip()
        if not template_active_for_quote(
            template_code, db_active=template_obj.active
        ):
            return CostSimulationResult(
                template_id=template_id,
                status="error",
                blockers=["template_not_active_for_quote", "template_inactive"],
                blocked_reasons=["template_not_active_for_quote"],
                trace={
                    "source": "product-system-cost-simulation",
                    "no_persist": True,
                    "used_template_snapshot": False,
                    "used_costengine_formulas": False,
                    "changed_entities": [],
                    "error": "template_not_active_for_quote",
                    "template_code": template_code,
                },
            )

        # Convert ORM object to dict for orchestrator consumption
        template_dict = self._template_to_dict(template_obj)
        template_code = template_dict.get("template_code", "")

        # --- Step 2: Evaluate readiness (read-only) ---
        spec = product_spec
        if spec is None and intake_id is not None:
            spec = await load_intake_product_spec(self.db, intake_id)

        readiness_service = ProductReadinessService(self.db)
        try:
            readiness_result = await readiness_service.evaluate(
                template_id, product_spec=spec
            )
            readiness_dict = readiness_result.to_dict()
            readiness_summary = {
                "ready_for_quote": readiness_result.ready_for_quote,
                "overall_status": readiness_result.overall_status,
                "blockers": (
                    readiness_result.technical_readiness.blockers
                    + readiness_result.costengine_readiness.blockers
                ),
                "warnings": (
                    readiness_result.technical_readiness.warnings
                    + readiness_result.costengine_readiness.warnings
                    + readiness_result.document_output_readiness.warnings
                    + readiness_result.visual_prompt_readiness.warnings
                    + readiness_result.execution_preparation_readiness.warnings
                ),
            }
        except Exception as exc:
            logger.warning("Cost simulation: readiness evaluation failed: %s", exc)
            readiness_dict = {}
            readiness_summary = {
                "ready_for_quote": False,
                "overall_status": "unknown",
                "blockers": [f"readiness_evaluation_failed:{str(exc)}"],
                "warnings": [],
            }

        # --- Step 3: Build orchestrator with registry rates ---
        orchestrator = await QuoteOrchestrator.create_with_registry(self.db)

        # --- Step 4: Build user_config for ProductSystemService ---
        user_config: Dict[str, Any] = {
            "product_id": template_code,
            "quantity": quantity,
            "dimensions": {
                "width_mm": quote_input.get("width_mm", 0),
                "height_mm": quote_input.get("height_mm", 0),
                "depth_mm": quote_input.get("depth_mm", 0),
            },
        }

        # --- Step 5: Build pricing (VAT from Settings — ignore client vat_pct) ---
        settings_vat_pct = await get_default_vat_pct(self.db)
        quote_pricing = QuotePricing(
            margin_pct=float(pricing_dict.get("margin_pct", 0)),
            discount_pct=float(pricing_dict.get("discount_pct", 0)),
            vat_pct=settings_vat_pct,
        )

        aggregate_price_context = None
        if is_aggregate_cost_template(template_code):
            from services.aggregate_cost_bom_price_bridge import prepare_aggregate_price_context

            aggregate_price_context = await prepare_aggregate_price_context(
                self.db,
                template_code,
                quote_input=quote_input,
            )

        # --- Step 6: Run orchestrator (read-only — no persist) ---
        try:
            snapshot = orchestrator.build_snapshot(
                product_template=template_dict,
                user_config=user_config,
                pricing=quote_pricing,
                quote_input=quote_input,
                aggregate_price_context=aggregate_price_context,
            )
        except Exception as exc:
            logger.exception(
                "Cost simulation build_snapshot failed for template_id=%s",
                template_id,
            )
            return CostSimulationResult(
                template_id=template_id,
                template_code=template_code,
                status="error",
                blockers=["cost_simulation_failed"],
                blocked_reasons=[f"{type(exc).__name__}: {exc}"],
                trace={
                    "source": "product-system-cost-simulation",
                    "no_persist": True,
                    "used_template_snapshot": True,
                    "used_costengine_formulas": False,
                    "changed_entities": [],
                    "error": str(exc),
                },
            )

        # --- Step 7: Extract results ---
        cost_result_dict = self._cost_result_to_dict(snapshot.cost_result)
        cost_engine_version = getattr(snapshot, "cost_engine_version", "v1")
        component_breakdown = getattr(snapshot, "component_breakdown", None) or []
        cost_warnings = getattr(snapshot, "cost_warnings", None) or []

        # Merge warnings from readiness + cost engine
        all_warnings = list(readiness_summary.get("warnings", []))
        for w in cost_warnings:
            if isinstance(w, dict):
                all_warnings.append(f"{w.get('kind', 'WARNING')}@{w.get('path', '')}")
            else:
                all_warnings.append(str(w))

        # Add cost validation warnings
        if cost_result_dict.get("validation", {}).get("warnings"):
            all_warnings.extend(cost_result_dict["validation"]["warnings"])

        cost_blockers = list(snapshot.blocked_reasons or [])
        if cost_result_dict.get("validation", {}).get("missing_cost_data"):
            cost_blockers.extend(cost_result_dict["validation"]["missing_cost_data"])

        quote_gate = None
        if is_volumetric_template_code(template_code):
            quote_gate = evaluate_volumetric_quote_ready(
                template_code=template_code,
                template_active=bool(template_obj.active),
                readiness_dict=readiness_dict,
                cost_blockers=cost_blockers,
                cost_warnings=[str(w) for w in cost_warnings if w],
                quote_input=quote_input,
                product_spec=spec,
            )
            readiness_summary["quote_gate"] = quote_gate.to_dict()
            readiness_summary["simulate_ready"] = quote_gate.simulate_ready
            readiness_summary["can_create_commercial_quote"] = (
                quote_gate.can_create_commercial_quote
            )

        all_blockers = list(readiness_summary.get("blockers", []))
        all_blockers.extend(cost_blockers)

        status = "simulated"
        if snapshot.status == "blocked":
            status = "blocked"
        elif snapshot.status == "priced":
            status = "simulated"

        linked_module_results = await self._simulate_linked_modules(
            template_service=template_service,
            linked_modules=quote_input.get("linked_modules") if isinstance(quote_input.get("linked_modules"), list) else [],
            quantity=quantity,
            pricing=pricing_dict,
            simulation_context=simulation_context,
        )
        if linked_module_results:
            parent_total = float(cost_result_dict.get("total_cost") or 0)
            linked_total = sum(
                float((module.get("cost_result") or {}).get("total_cost") or 0)
                for module in linked_module_results
                if isinstance(module, dict)
            )
            cost_result_dict["parent_total_cost"] = parent_total
            cost_result_dict["linked_modules_total_cost"] = linked_total
            cost_result_dict["composite_total_cost"] = parent_total + linked_total
            cost_result_dict["total_cost"] = parent_total + linked_total
            for index, module in enumerate(linked_module_results):
                if not isinstance(module, dict):
                    continue
                for blocker in module.get("blocked_reasons") or []:
                    all_blockers.append(f"linked_module[{index}]:{blocker}")
                for warning in module.get("warnings") or []:
                    all_warnings.append(f"linked_module[{index}]:{warning}")
                if module.get("status") in {"blocked", "error"}:
                    status = "blocked"

        return CostSimulationResult(
            template_id=template_id,
            template_code=template_code,
            cost_engine_version=cost_engine_version,
            persisted=False,
            readiness=readiness_summary,
            cost_result=cost_result_dict,
            component_breakdown=component_breakdown,
            linked_module_results=linked_module_results,
            warnings=all_warnings,
            blockers=all_blockers,
            status=status,
            blocked_reasons=list(snapshot.blocked_reasons or []),
            trace={
                "source": "product-system-cost-simulation",
                "no_persist": True,
                "used_template_snapshot": True,
                "used_costengine_formulas": True,
                "changed_entities": [],
                "simulation_context": simulation_context,
                "linked_modules_count": len(linked_module_results),
            },
        )

    async def _simulate_linked_modules(
        self,
        *,
        template_service: Product_templatesService,
        linked_modules: list[Any],
        quantity: int,
        pricing: Dict[str, Any],
        simulation_context: Dict[str, Any],
    ) -> list[Dict[str, Any]]:
        results: list[Dict[str, Any]] = []
        for raw_module in linked_modules:
            if not isinstance(raw_module, dict):
                continue
            module_code = str(raw_module.get("module_template_code") or "").strip()
            module_input = raw_module.get("input_payload") if isinstance(raw_module.get("input_payload"), dict) else {}
            if not module_code:
                results.append({"status": "error", "blocked_reasons": ["linked_module_template_code_missing"]})
                continue
            module_template = await template_service.get_by_field("template_code", module_code)
            if module_template is None:
                results.append(
                    {
                        "module_template_code": module_code,
                        "status": "error",
                        "blocked_reasons": ["linked_module_template_not_found"],
                    }
                )
                continue
            child_input = dict(module_input)
            child_input.pop("linked_modules", None)
            child = await self.simulate(
                module_template.id,
                quantity=quantity,
                quote_input=child_input,
                pricing=pricing,
                options={},
                simulation_context={
                    **simulation_context,
                    "source": "linked_module_simulation",
                    "parent_source": simulation_context.get("source"),
                    "module_template_code": module_code,
                },
            )
            child_dict = child.to_dict()
            child_dict["relation_type"] = raw_module.get("relation_type")
            child_dict["pricing_mode"] = raw_module.get("pricing_mode")
            child_dict["execution_mode"] = raw_module.get("execution_mode")
            child_dict["input_payload"] = child_input
            results.append(child_dict)
        return results

    @staticmethod
    def _cost_result_to_dict(cost_result) -> Dict[str, Any]:
        """Safely convert cost_result to dict.

        Handles dataclass instances (production) and plain objects/dicts (testing).
        """
        if cost_result is None:
            return {}
        if is_dataclass(cost_result) and not isinstance(cost_result, type):
            return asdict(cost_result)
        to_dict = getattr(cost_result, "to_dict", None)
        if callable(to_dict):
            converted = to_dict()
            if isinstance(converted, dict):
                return converted
        # Fallback: extract known fields manually
        known_fields = [
            "is_valid", "currency", "materials_cost", "labour_cost",
            "machine_cost", "external_cost", "overhead_cost", "total_cost",
            "estimated_time_minutes", "breakdown", "validation",
        ]
        result: Dict[str, Any] = {}
        for field_name in known_fields:
            val = getattr(cost_result, field_name, None)
            if val is not None:
                # Handle nested validation object
                if field_name == "validation" and hasattr(val, "missing_cost_data"):
                    result[field_name] = {
                        "missing_cost_data": getattr(val, "missing_cost_data", []),
                        "warnings": getattr(val, "warnings", []),
                    }
                else:
                    result[field_name] = val
        return result

    @staticmethod
    def _template_to_dict(template_obj) -> Dict[str, Any]:
        """Convert ORM template object to dict for orchestrator."""
        return {
            "id": template_obj.id,
            "template_code": template_obj.template_code,
            "family_id": template_obj.family_id,
            "family_name": template_obj.family_name,
            "description": template_obj.description,
            "components_json": template_obj.components_json,
            "operations_json": template_obj.operations_json,
            "required_materials_json": template_obj.required_materials_json,
            "estimated_hours": template_obj.estimated_hours,
            "base_labor_rate": template_obj.base_labor_rate,
            "base_margin_pct": template_obj.base_margin_pct,
            "active": template_obj.active,
            "notes": template_obj.notes,
        }