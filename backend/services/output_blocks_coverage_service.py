"""
BUILD 9 — Output Blocks Coverage Diagnostics Service.

Reports which product templates/families have output_blocks_json populated
in their blueprint dossier, and which are missing.

Rules:
  - Read-only — no persist, no mutation
  - No template modification
  - No dossier modification
  - Reports coverage status only
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.product_templates import Product_templates
from models.product_blueprint_dossier import ProductBlueprintDossier

logger = logging.getLogger(__name__)


class OutputBlocksCoverageService:
    """Reports output blocks coverage across product templates."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_coverage(self) -> Dict[str, Any]:
        """Get output blocks coverage diagnostics.

        Returns:
            Dict with coverage stats and per-template details.
        """
        # Load all templates
        tpl_query = select(Product_templates)
        tpl_result = await self.db.execute(tpl_query)
        templates = tpl_result.scalars().all()

        # Load all dossiers
        dos_query = select(ProductBlueprintDossier)
        dos_result = await self.db.execute(dos_query)
        dossiers = dos_result.scalars().all()

        # Index dossiers by template_id
        dossier_map: Dict[int, ProductBlueprintDossier] = {}
        for d in dossiers:
            dossier_map[d.template_id] = d

        # Build coverage report
        covered: List[Dict[str, Any]] = []
        missing: List[Dict[str, Any]] = []
        partial: List[Dict[str, Any]] = []

        for tpl in templates:
            tpl_id = tpl.id
            tpl_code = tpl.template_code or ""
            tpl_desc = tpl.description or ""

            dossier = dossier_map.get(tpl_id)

            if not dossier:
                missing.append({
                    "template_id": tpl_id,
                    "template_code": tpl_code,
                    "description": tpl_desc,
                    "reason": "no_dossier",
                })
                continue

            # Check output_blocks_json
            output_blocks_raw = dossier.output_blocks_json
            if not output_blocks_raw:
                missing.append({
                    "template_id": tpl_id,
                    "template_code": tpl_code,
                    "description": tpl_desc,
                    "dossier_id": dossier.id,
                    "reason": "output_blocks_json_empty",
                })
                continue

            # Parse and check block count
            try:
                blocks = json.loads(output_blocks_raw) if isinstance(output_blocks_raw, str) else output_blocks_raw
            except (json.JSONDecodeError, TypeError):
                missing.append({
                    "template_id": tpl_id,
                    "template_code": tpl_code,
                    "description": tpl_desc,
                    "dossier_id": dossier.id,
                    "reason": "output_blocks_json_invalid",
                })
                continue

            if not isinstance(blocks, list) or len(blocks) == 0:
                missing.append({
                    "template_id": tpl_id,
                    "template_code": tpl_code,
                    "description": tpl_desc,
                    "dossier_id": dossier.id,
                    "reason": "output_blocks_json_empty_list",
                })
                continue

            # Check if all blocks have required fields
            block_count = len(blocks)
            complete_blocks = 0
            for block in blocks:
                if isinstance(block, dict) and block.get("block_id") and block.get("title"):
                    complete_blocks += 1

            if complete_blocks == block_count:
                covered.append({
                    "template_id": tpl_id,
                    "template_code": tpl_code,
                    "description": tpl_desc,
                    "dossier_id": dossier.id,
                    "block_count": block_count,
                })
            else:
                partial.append({
                    "template_id": tpl_id,
                    "template_code": tpl_code,
                    "description": tpl_desc,
                    "dossier_id": dossier.id,
                    "block_count": block_count,
                    "complete_blocks": complete_blocks,
                    "reason": "some_blocks_incomplete",
                })

        total = len(templates)
        return {
            "total_templates": total,
            "covered_count": len(covered),
            "partial_count": len(partial),
            "missing_count": len(missing),
            "coverage_pct": round((len(covered) / total * 100) if total > 0 else 0, 1),
            "covered": covered,
            "partial": partial,
            "missing": missing,
        }