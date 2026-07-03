"""
BUILD 8 — Output Blocks Renderer Service.

Renders Output Blocks from product_blueprint_dossier.output_blocks_json
as a read-only preview. No persistence, no mutation, no side effects.

Rules:
  - Read-only
  - No persist
  - Auth protected (enforced at router level)
  - Deterministic
  - No side effects
  - No AuditLog (no mutation)
  - No Quote creation/modification
  - No Order creation/modification
  - No ProductTemplate mutation
  - No BlueprintDossier mutation
  - No Inventory mutation
  - No ExecutionTask creation
  - No CostEngine formula calculation
  - No commercial price calculation
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.product_blueprint_dossier import ProductBlueprintDossier
from models.product_templates import Product_templates
from models.product_families import Product_families
from services.output_blocks_contract import (
    ALLOWED_BLOCK_TYPES,
    ALLOWED_AUDIENCES,
    ALLOWED_DOCUMENT_TYPES,
    ALLOWED_APPROVAL_STATUSES,
    validate_output_blocks,
)
from services.output_blocks_source_resolver import OutputBlocksSourceResolver

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

class RenderPreviewResult:
    """Structured result from a render preview operation."""

    def __init__(
        self,
        *,
        persisted: bool = False,
        template_id: Optional[int] = None,
        dossier_id: Optional[int] = None,
        document_type: str = "",
        audience: str = "",
        render_mode: str = "preview",
        blocks: Optional[List[Dict[str, Any]]] = None,
        warnings: Optional[List[str]] = None,
        blockers: Optional[List[str]] = None,
        trace: Optional[Dict[str, Any]] = None,
    ):
        self.persisted = persisted
        self.template_id = template_id
        self.dossier_id = dossier_id
        self.document_type = document_type
        self.audience = audience
        self.render_mode = render_mode
        self.blocks = blocks or []
        self.warnings = warnings or []
        self.blockers = blockers or []
        self.trace = trace or {
            "source": "output-blocks-render-preview",
            "no_persist": True,
            "changed_entities": [],
            "live_changes_affect_accepted_orders": False,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "persisted": self.persisted,
            "template_id": self.template_id,
            "dossier_id": self.dossier_id,
            "document_type": self.document_type,
            "audience": self.audience,
            "render_mode": self.render_mode,
            "blocks": self.blocks,
            "warnings": self.warnings,
            "blockers": self.blockers,
            "trace": self.trace,
        }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class OutputBlocksRendererService:
    """Renders Output Blocks as a read-only preview."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def render_preview(
        self,
        *,
        template_id: Optional[int] = None,
        dossier_id: Optional[int] = None,
        document_type: str = "offer",
        audience: str = "client",
        block_types: Optional[List[str]] = None,
        quote_context: Optional[Dict[str, Any]] = None,
        render_mode: str = "preview",
    ) -> RenderPreviewResult:
        """Render output blocks preview.

        Read-only. No persist. No mutation.
        """
        warnings: List[str] = []
        blockers: List[str] = []

        # --- Validate inputs ---
        if document_type and document_type not in ALLOWED_DOCUMENT_TYPES:
            blockers.append(f"invalid_document_type:{document_type}")
            return RenderPreviewResult(
                template_id=template_id,
                dossier_id=dossier_id,
                document_type=document_type,
                audience=audience,
                render_mode=render_mode,
                blockers=blockers,
            )

        if audience and audience not in ALLOWED_AUDIENCES:
            blockers.append(f"invalid_audience:{audience}")
            return RenderPreviewResult(
                template_id=template_id,
                dossier_id=dossier_id,
                document_type=document_type,
                audience=audience,
                render_mode=render_mode,
                blockers=blockers,
            )

        if block_types:
            for bt in block_types:
                if bt not in ALLOWED_BLOCK_TYPES:
                    blockers.append(f"invalid_block_type:{bt}")
            if blockers:
                return RenderPreviewResult(
                    template_id=template_id,
                    dossier_id=dossier_id,
                    document_type=document_type,
                    audience=audience,
                    render_mode=render_mode,
                    blockers=blockers,
                )

        # --- Load template ---
        template_obj = None
        if template_id:
            query = select(Product_templates).where(Product_templates.id == template_id)
            result = await self.db.execute(query)
            template_obj = result.scalar_one_or_none()

        if not template_obj and template_id:
            blockers.append("template_not_found")
            return RenderPreviewResult(
                template_id=template_id,
                dossier_id=dossier_id,
                document_type=document_type,
                audience=audience,
                render_mode=render_mode,
                blockers=blockers,
            )

        # --- Load dossier ---
        dossier_obj = None
        if dossier_id:
            query = select(ProductBlueprintDossier).where(
                ProductBlueprintDossier.id == dossier_id
            )
            result = await self.db.execute(query)
            dossier_obj = result.scalar_one_or_none()
        elif template_id:
            # Find dossier by template_id
            query = select(ProductBlueprintDossier).where(
                ProductBlueprintDossier.template_id == template_id
            )
            result = await self.db.execute(query)
            dossier_obj = result.scalar_one_or_none()

        if not dossier_obj:
            blockers.append("dossier_not_found")
            return RenderPreviewResult(
                template_id=template_id,
                dossier_id=dossier_id,
                document_type=document_type,
                audience=audience,
                render_mode=render_mode,
                blockers=blockers,
            )

        actual_dossier_id = dossier_obj.id

        # --- Parse output_blocks_json ---
        raw_blocks = dossier_obj.output_blocks_json
        if not raw_blocks:
            warnings.append("output_blocks_json is empty in dossier")
            return RenderPreviewResult(
                template_id=template_id,
                dossier_id=actual_dossier_id,
                document_type=document_type,
                audience=audience,
                render_mode=render_mode,
                blocks=[],
                warnings=warnings,
                blockers=blockers,
            )

        # Parse JSON
        try:
            parsed = json.loads(raw_blocks) if isinstance(raw_blocks, str) else raw_blocks
        except (json.JSONDecodeError, TypeError):
            blockers.append("output_blocks_json_invalid_json")
            return RenderPreviewResult(
                template_id=template_id,
                dossier_id=actual_dossier_id,
                document_type=document_type,
                audience=audience,
                render_mode=render_mode,
                blockers=blockers,
            )

        # Extract blocks list
        if isinstance(parsed, dict):
            blocks_list = parsed.get("blocks", [])
        elif isinstance(parsed, list):
            blocks_list = parsed
        else:
            blockers.append("output_blocks_json_invalid_structure")
            return RenderPreviewResult(
                template_id=template_id,
                dossier_id=actual_dossier_id,
                document_type=document_type,
                audience=audience,
                render_mode=render_mode,
                blockers=blockers,
            )

        # --- Validate blocks ---
        validation_result = validate_output_blocks(parsed)
        if not validation_result.is_valid:
            for err in validation_result.errors:
                blockers.append(f"validation:{err.field}:{err.error}")
            return RenderPreviewResult(
                template_id=template_id,
                dossier_id=actual_dossier_id,
                document_type=document_type,
                audience=audience,
                render_mode=render_mode,
                blockers=blockers,
                warnings=warnings,
            )

        # --- Prepare source data ---
        template_data = self._template_to_source_dict(template_obj) if template_obj else {}
        family_data = await self._load_family_data(template_obj)
        dossier_data = self._dossier_to_source_dict(dossier_obj)

        # --- Filter blocks by requested types/audience/document_type ---
        filtered_blocks = self._filter_blocks(
            blocks_list,
            block_types=block_types,
            audience=audience,
            document_type=document_type,
        )

        # --- Render each block ---
        rendered_blocks: List[Dict[str, Any]] = []
        for block in filtered_blocks:
            rendered = self._render_single_block(
                block=block,
                template_data=template_data,
                family_data=family_data,
                dossier_data=dossier_data,
                quote_context=quote_context or {},
            )
            if rendered is not None:
                rendered_blocks.append(rendered)
            else:
                # Block was hidden (hide_block behavior)
                warnings.append(
                    f"block '{block.get('block_id', '')}' hidden due to missing variables"
                )

        return RenderPreviewResult(
            template_id=template_id,
            dossier_id=actual_dossier_id,
            document_type=document_type,
            audience=audience,
            render_mode=render_mode,
            blocks=rendered_blocks,
            warnings=warnings,
            blockers=blockers,
        )

    def _filter_blocks(
        self,
        blocks: List[Dict[str, Any]],
        *,
        block_types: Optional[List[str]] = None,
        audience: str = "",
        document_type: str = "",
    ) -> List[Dict[str, Any]]:
        """Filter blocks by requested criteria."""
        filtered = []
        for block in blocks:
            if not isinstance(block, dict):
                continue
            # Filter by block_types if specified
            if block_types:
                if block.get("block_type") not in block_types:
                    continue
            # Filter by audience if specified
            if audience and block.get("audience") != audience:
                continue
            # Filter by document_type if specified
            if document_type and block.get("document_type") != document_type:
                continue
            filtered.append(block)
        return filtered

    def _render_single_block(
        self,
        *,
        block: Dict[str, Any],
        template_data: Dict[str, Any],
        family_data: Dict[str, Any],
        dossier_data: Dict[str, Any],
        quote_context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Render a single block. Returns None if block should be hidden."""
        block_id = block.get("block_id", "")
        block_type = block.get("block_type", "")
        title = block.get("title", "")
        approval_status = block.get("approval_status", "draft")
        template_text = block.get("template_text", "")
        variables = block.get("variables", [])

        block_warnings: List[str] = []
        block_blockers: List[str] = []

        # Check deprecated status
        if approval_status == "deprecated":
            block_warnings.append("block_deprecated")

        # Check unapproved client-facing
        block_audience = block.get("audience", "")
        block_doc_type = block.get("document_type", "")
        if (
            block_audience == "client"
            and block_doc_type in ("offer", "contract")
            and approval_status not in ("approved", "approved_for_client")
        ):
            block_warnings.append("client_facing_block_not_approved")

        # Resolve variables
        resolver = OutputBlocksSourceResolver(
            template_data=template_data,
            family_data=family_data,
            dossier_data=dossier_data,
            quote_context=quote_context,
        )
        resolve_result = resolver.resolve_variables(variables if isinstance(variables, list) else [])

        # Check for hide_block behavior
        for blocker in resolve_result.blockers:
            if "hide_block" in blocker:
                return None  # Block hidden

        block_warnings.extend(resolve_result.warnings)
        block_blockers.extend(resolve_result.blockers)

        # Render template text with resolved variables
        rendered_text = template_text
        if template_text and resolve_result.variables_used:
            rendered_text = self._substitute_variables(
                template_text, resolve_result.variables_used
            )

        return {
            "block_id": block_id,
            "block_type": block_type,
            "title": title,
            "approval_status": approval_status,
            "rendered_text": rendered_text,
            "variables_used": resolve_result.variables_used,
            "warnings": block_warnings,
            "blockers": block_blockers,
        }

    def _substitute_variables(
        self, template_text: str, variables_used: List[Dict[str, Any]]
    ) -> str:
        """Replace {{variable_name}} placeholders with resolved values."""
        result = template_text
        for var in variables_used:
            name = var.get("name", "")
            value = var.get("value")
            resolved = var.get("resolved", False)
            if name and resolved and value is not None:
                placeholder = "{{" + name + "}}"
                result = result.replace(placeholder, str(value))
        return result

    @staticmethod
    def _template_to_source_dict(template_obj) -> Dict[str, Any]:
        """Convert ORM template to source dict."""
        components = None
        if template_obj.components_json:
            try:
                components = json.loads(template_obj.components_json) if isinstance(
                    template_obj.components_json, str
                ) else template_obj.components_json
            except (json.JSONDecodeError, TypeError):
                components = None

        operations = None
        if template_obj.operations_json:
            try:
                operations = json.loads(template_obj.operations_json) if isinstance(
                    template_obj.operations_json, str
                ) else template_obj.operations_json
            except (json.JSONDecodeError, TypeError):
                operations = None

        materials = None
        if template_obj.required_materials_json:
            try:
                materials = json.loads(template_obj.required_materials_json) if isinstance(
                    template_obj.required_materials_json, str
                ) else template_obj.required_materials_json
            except (json.JSONDecodeError, TypeError):
                materials = None

        return {
            "id": template_obj.id,
            "template_code": template_obj.template_code,
            "family_id": template_obj.family_id,
            "family_name": template_obj.family_name,
            "description": template_obj.description or "",
            "components": components,
            "operations": operations,
            "required_materials": materials,
            "estimated_hours": template_obj.estimated_hours,
            "base_labor_rate": template_obj.base_labor_rate,
            "base_margin_pct": template_obj.base_margin_pct,
            "active": template_obj.active,
            "notes": template_obj.notes or "",
        }

    async def _load_family_data(self, template_obj) -> Dict[str, Any]:
        """Load family data for the template."""
        if not template_obj or not template_obj.family_id:
            return {}
        try:
            query = select(Product_families).where(
                Product_families.id == int(template_obj.family_id)
            )
            result = await self.db.execute(query)
            family_obj = result.scalar_one_or_none()
            if family_obj:
                return {
                    "family_id": str(family_obj.id),
                    "label": family_obj.name if hasattr(family_obj, "name") else "",
                    "name": family_obj.name if hasattr(family_obj, "name") else "",
                }
        except (ValueError, TypeError):
            pass
        return {
            "family_id": template_obj.family_id,
            "label": template_obj.family_name or "",
            "name": template_obj.family_name or "",
        }

    @staticmethod
    def _dossier_to_source_dict(dossier_obj) -> Dict[str, Any]:
        """Convert ORM dossier to source dict."""
        result: Dict[str, Any] = {
            "id": dossier_obj.id,
            "template_id": dossier_obj.template_id,
            "template_code": dossier_obj.template_code,
            "dossier_version": dossier_obj.dossier_version,
            "status": dossier_obj.status,
        }

        # Parse JSON fields
        json_fields = [
            "production_notes_json",
            "qc_checkpoints_json",
            "risks_json",
            "sections_json",
        ]
        for field_name in json_fields:
            raw = getattr(dossier_obj, field_name, None)
            key = field_name.replace("_json", "")
            if raw:
                try:
                    result[key] = json.loads(raw) if isinstance(raw, str) else raw
                except (json.JSONDecodeError, TypeError):
                    result[key] = None
            else:
                result[key] = None

        return result