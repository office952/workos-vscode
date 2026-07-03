"""Set CostEngine template costing base currency (moneda_implicita).

Owner-approved: template costing base currency = EUR for Product 001 / BUILD 4.

Idempotent: skips when moneda_implicita is already EUR.
No FX service — only updates the singleton CostEngine config row.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from core.database import db_manager
from services.cost_engine_config import CostEngineConfigService

logger = logging.getLogger(__name__)

TEMPLATE_COSTING_BASE_CURRENCY = "EUR"


async def seed_cost_engine_template_base_currency() -> Dict[str, Any]:
    """Patch moneda_implicita to EUR when not already set."""
    async with db_manager.async_session_maker() as session:
        svc = CostEngineConfigService(session)
        cfg = await svc.get_or_create()
        previous = str(cfg.moneda_implicita or "").strip().upper() or "RON"
        target = TEMPLATE_COSTING_BASE_CURRENCY

        if previous == target:
            logger.info(
                "CostEngine base currency already %s — skipped", target
            )
            return {
                "action": "SKIPPED_ALREADY_APPLIED",
                "currency": target,
                "previous": previous,
            }

        await svc.update({"moneda_implicita": target})
        logger.info(
            "CostEngine base currency patched: %s -> %s", previous, target
        )
        return {
            "action": "PATCHED",
            "currency": target,
            "previous": previous,
        }
