"""
Phase 6 — ProductSystem Execution Preview Service (S27).

Read-only service that builds a ProductSystemExecutionPreview envelope
for a given order_id by resolving:
  order → template_code → product_templates → production_operations → task_templates
  → LinkageValidator.validate_template_linkage(template_id)

Safety guarantees:
  - No DB writes. No mutations. No side effects.
  - Idempotent: same input + same registry state → same output.
  - Pure read-only composition of existing data.

Forbidden imports (spec §24 FP-02):
  - cost_engine_service
  - quote_orchestrator
  - ExecutionPlanService
  - MaterialRate
  - execution_plan_service
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from data_models.execution_preview import (
    GeneratedOperation,
    GeneratedTaskRequirement,
    MissingLink,
    ProductSystemExecutionPreview,
    TraceSource,
)
from data_models.linkage_contracts import LinkageValidationResult
from services.product_system_linkage_validator import (
    ProductSystemLinkageValidator,
    TemplateInactiveError,
    TemplateNotFoundError,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class OrderNotFoundError(Exception):
    """Raised when order_id does not exist in orders table."""

    def __init__(self, order_id: int):
        super().__init__(f"Order {order_id} not found")
        self.order_id = order_id


class TemplateCodeNotFoundError(Exception):
    """Raised when template_code from order cannot be resolved."""

    def __init__(self, template_code: str):
        super().__init__(f"Template code '{template_code}' not found")
        self.template_code = template_code


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_json_parse(raw: Any, default: Any) -> Any:
    """Parse JSON safely without silent fallbacks."""
    if raw is None:
        return default
    if isinstance(raw, (list, dict)):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return default
    return default


def _normalize_skill_ids(raw: Any) -> List[str]:
    """Normalize required_skill_ids from DB row to List[str]."""
    if isinstance(raw, list):
        return [str(s) for s in raw if s]
    if isinstance(raw, str):
        cleaned = raw.strip("{}")
        if cleaned:
            return [s.strip() for s in cleaned.split(",") if s.strip()]
    return []


def _normalize_depends_on(raw: Any) -> List[str]:
    """Normalize depends_on_operation_ids from DB row to List[str]."""
    if isinstance(raw, list):
        return [str(s) for s in raw if s]
    if isinstance(raw, str):
        cleaned = raw.strip("{}")
        if cleaned:
            return [s.strip() for s in cleaned.split(",") if s.strip()]
    return []


def _normalize_estimated_duration(raw: Any) -> Dict[str, Any]:
    """Normalize estimated_duration from DB row to Dict."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    if isinstance(raw, (int, float)):
        return {"value": raw, "unit": "minutes"}
    return {"value": 0, "unit": "minutes"}


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ProductSystemExecutionPreviewService:
    """
    Read-only service that builds a ProductSystemExecutionPreview envelope.

    No writes. No mutations. Pure read.
    """

    def __init__(self, db: AsyncSession):
        self._db = db
        self._linkage_validator = ProductSystemLinkageValidator(db)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def preview_for_execution(
        self, order_id: int
    ) -> ProductSystemExecutionPreview:
        """
        Generate the execution preview envelope for a given order.

        Resolution chain:
          order_id → orders row → snapshot_line_items → template_code
          → product_templates (by template_code, active=true)
          → production_operations (by template_id)
          → task_templates (by template_id)
          → LinkageValidator.validate_template_linkage(template_id)

        Returns: ProductSystemExecutionPreview (always, even if incomplete)
        Raises: OrderNotFoundError, TemplateCodeNotFoundError, TemplateNotFoundError, TemplateInactiveError
        Side effects: NONE (pure read)
        """
        # 1. Read order
        order_row = await self._get_order(order_id)
        order_code = str(order_row["code"])

        # 2. Extract template_code from order snapshot
        template_code = self._extract_template_code(order_row)

        # 3. Resolve template
        template_row = await self._resolve_template_by_code(template_code)
        template_id = int(template_row["id"])

        # 4. Read production_operations
        operations_rows = await self._get_production_operations(template_id)

        # 5. Read task_templates
        task_rows = await self._get_task_templates(template_id)

        # 6. Run linkage validation
        linkage_result = await self._linkage_validator.validate_template_linkage(template_id)

        # 7. Build generated_operations
        generated_operations = self._build_operations(operations_rows)

        # 8. Build generated_task_requirements
        generated_task_requirements = self._build_task_requirements(task_rows)

        # 9. Compute missing_links
        operation_ids_set = {op.operation_id for op in generated_operations}
        missing_links = self._compute_missing_links(
            task_rows, operation_ids_set
        )

        # 10. Build trace_source
        trace_source = self._build_trace_source(linkage_result)

        # 11. Build blockers/warnings from linkage result
        blockers = [blk.model_dump() for blk in linkage_result.blockers]
        warnings = [wrn.model_dump() for wrn in linkage_result.warnings]

        return ProductSystemExecutionPreview(
            order_id=order_id,
            order_code=order_code,
            template_code=template_code,
            template_version=template_row.get("version"),
            generated_operations=generated_operations,
            generated_task_requirements=generated_task_requirements,
            missing_links=missing_links,
            blockers=blockers,
            warnings=warnings,
            trace_source=trace_source,
        )

    # ------------------------------------------------------------------
    # Internal: DB reads (read-only)
    # ------------------------------------------------------------------

    async def _get_order(self, order_id: int) -> Dict[str, Any]:
        """Read order by id. Raises OrderNotFoundError if not found."""
        sql = text(
            "SELECT id, code, snapshot_line_items, snapshot_version "
            "FROM orders WHERE id = :order_id LIMIT 1"
        )
        result = await self._db.execute(sql, {"order_id": order_id})
        row = result.mappings().first()
        if not row:
            raise OrderNotFoundError(order_id)
        return dict(row)

    def _extract_template_code(self, order_row: Dict[str, Any]) -> str:
        """Extract template_code from order's snapshot_line_items."""
        snapshot_raw = order_row.get("snapshot_line_items")
        snapshot = _safe_json_parse(snapshot_raw, {})

        # Try product_definition.product_code first
        if isinstance(snapshot, dict):
            product_def = snapshot.get("product_definition")
            if isinstance(product_def, dict):
                code = product_def.get("product_code")
                if isinstance(code, str) and code.strip():
                    return code.strip()
                # Try template_code field
                tpl_code = product_def.get("template_code")
                if isinstance(tpl_code, str) and tpl_code.strip():
                    return tpl_code.strip()

            # Try top-level template_code
            top_code = snapshot.get("template_code")
            if isinstance(top_code, str) and top_code.strip():
                return top_code.strip()

            # Try line_items array
            line_items = snapshot.get("line_items")
            if isinstance(line_items, list) and len(line_items) > 0:
                first_item = line_items[0]
                if isinstance(first_item, dict):
                    item_code = first_item.get("template_code")
                    if isinstance(item_code, str) and item_code.strip():
                        return item_code.strip()
                    product_code = first_item.get("product_code")
                    if isinstance(product_code, str) and product_code.strip():
                        return product_code.strip()

        raise TemplateCodeNotFoundError(
            f"Cannot extract template_code from order {order_row.get('id')} snapshot"
        )

    async def _resolve_template_by_code(self, template_code: str) -> Dict[str, Any]:
        """Resolve template_code to product_templates row."""
        sql = text(
            "SELECT id, template_code, family_name, active "
            "FROM product_templates WHERE template_code = :template_code LIMIT 1"
        )
        result = await self._db.execute(sql, {"template_code": template_code})
        row = result.mappings().first()
        if not row:
            raise TemplateCodeNotFoundError(template_code)
        row_dict = dict(row)
        if not row_dict.get("active", True):
            raise TemplateInactiveError(
                int(row_dict["id"]), str(row_dict["template_code"])
            )
        return row_dict

    async def _get_production_operations(self, template_id: int) -> List[Dict[str, Any]]:
        """Read all production_operations for a given template_id."""
        sql = text(
            "SELECT operation_id, task_type, sequence_index, "
            "depends_on_operation_ids, component_id, description "
            "FROM production_operations WHERE template_id = :template_id "
            "ORDER BY sequence_index ASC"
        )
        result = await self._db.execute(sql, {"template_id": template_id})
        return [dict(r) for r in result.mappings().all()]

    async def _get_task_templates(self, template_id: int) -> List[Dict[str, Any]]:
        """Read all task_templates for a given template_id."""
        sql = text(
            "SELECT task_template_id, source_operation_id, task_type, "
            "required_skill_ids, required_workcenter_id, "
            "required_machine_type, required_machine_id, "
            "material_requirements, estimated_duration "
            "FROM task_templates WHERE template_id = :template_id "
            "ORDER BY id ASC"
        )
        result = await self._db.execute(sql, {"template_id": template_id})
        return [dict(r) for r in result.mappings().all()]

    # ------------------------------------------------------------------
    # Internal: builders (pure, no I/O)
    # ------------------------------------------------------------------

    def _build_operations(
        self, operations_rows: List[Dict[str, Any]]
    ) -> List[GeneratedOperation]:
        """Map production_operations rows to GeneratedOperation list."""
        result: List[GeneratedOperation] = []
        for row in operations_rows:
            result.append(
                GeneratedOperation(
                    operation_id=str(row["operation_id"]),
                    task_type=str(row["task_type"]),
                    sequence_index=int(row["sequence_index"]),
                    depends_on_operation_ids=_normalize_depends_on(
                        row.get("depends_on_operation_ids")
                    ),
                    component_id=row.get("component_id"),
                    description=row.get("description"),
                )
            )
        return result

    def _build_task_requirements(
        self, task_rows: List[Dict[str, Any]]
    ) -> List[GeneratedTaskRequirement]:
        """Map task_templates rows to GeneratedTaskRequirement list."""
        result: List[GeneratedTaskRequirement] = []
        for row in task_rows:
            material_reqs = _safe_json_parse(row.get("material_requirements"), [])
            if not isinstance(material_reqs, list):
                material_reqs = []

            result.append(
                GeneratedTaskRequirement(
                    task_template_id=str(row["task_template_id"]),
                    source_operation_id=str(row["source_operation_id"]),
                    task_type=str(row["task_type"]),
                    required_skill_ids=_normalize_skill_ids(
                        row.get("required_skill_ids")
                    ),
                    required_workcenter_id=row.get("required_workcenter_id"),
                    required_machine_type=row.get("required_machine_type"),
                    required_machine_id=row.get("required_machine_id"),
                    material_requirements=material_reqs,
                    estimated_duration=_normalize_estimated_duration(
                        row.get("estimated_duration")
                    ),
                )
            )
        return result

    def _compute_missing_links(
        self,
        task_rows: List[Dict[str, Any]],
        operation_ids_set: set,
    ) -> List[MissingLink]:
        """Compute missing_links from task_template fields."""
        missing: List[MissingLink] = []

        for row in task_rows:
            task_id = str(row.get("task_template_id", ""))

            # Check source_operation_id resolves
            source_op = row.get("source_operation_id")
            if source_op and str(source_op) not in operation_ids_set:
                missing.append(
                    MissingLink(
                        field="source_operation_id",
                        task_template_id=task_id,
                        reason=f"source_operation_id '{source_op}' not found in production_operations",
                        available_today=True,
                    )
                )

            # Check required_skill_ids not empty for non-exempt types
            skill_ids = _normalize_skill_ids(row.get("required_skill_ids"))
            task_type = str(row.get("task_type", ""))
            skill_exempt = task_type in (
                "file_preparation", "measurement", "quality_control"
            )
            if not skill_ids and not skill_exempt:
                missing.append(
                    MissingLink(
                        field="required_skill_ids",
                        task_template_id=task_id,
                        reason="Empty required_skill_ids for non-exempt task_type",
                        available_today=True,
                    )
                )

            # Check workcenter/machine assignment for non-exempt types
            workcenter_exempt = task_type in (
                "file_preparation", "measurement", "mounting",
                "installation", "quality_control"
            )
            wc = row.get("required_workcenter_id")
            mt = row.get("required_machine_type")
            mid = row.get("required_machine_id")
            has_wc = bool(wc and str(wc).strip())
            has_machine = bool(mt and str(mt).strip()) or bool(mid and str(mid).strip())
            if not has_wc and not has_machine and not workcenter_exempt:
                missing.append(
                    MissingLink(
                        field="required_workcenter_id",
                        task_template_id=task_id,
                        reason="NULL workcenter and no machine assignment for non-exempt task_type",
                        available_today=True,
                    )
                )

            # Check material_requirements (warning-level, not blocker)
            if not settings.registry_materials_live:
                # Materials not live — missing link but not available today
                mat_reqs = _safe_json_parse(row.get("material_requirements"), [])
                if not isinstance(mat_reqs, list):
                    mat_reqs = []
                # Only flag if task_type typically consumes materials
                material_consuming_types = {
                    "cnc_routing", "laser_cutting", "print_large_format",
                    "laminating", "vinyl_cutting", "edge_bending",
                    "plexi_cutting", "welding", "led_assembly",
                }
                if task_type in material_consuming_types and not mat_reqs:
                    missing.append(
                        MissingLink(
                            field="material_requirements",
                            task_template_id=task_id,
                            reason="Empty material_requirements for material-consuming task_type",
                            available_today=False,
                        )
                    )

        return missing

    def _build_trace_source(
        self, linkage_result: LinkageValidationResult
    ) -> TraceSource:
        """Build trace_source from linkage validation result."""
        return TraceSource(
            registries_consulted=linkage_result.registries_consulted,
            registries_unavailable=linkage_result.registries_unavailable,
            template_resolved_at=linkage_result.timestamp,
            linkage_validation_run=True,
            linkage_blockers_count=len(linkage_result.blockers),
            linkage_warnings_count=len(linkage_result.warnings),
        )