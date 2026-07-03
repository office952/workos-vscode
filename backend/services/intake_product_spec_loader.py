"""Load and validate intake product_spec_json for readiness/quote gates."""

from __future__ import annotations

import json
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.intake_requests import Intake_requests
from validators.intake_product_spec import validate_intake_product_spec


async def load_intake_product_spec(
    db: AsyncSession,
    intake_id: Optional[int],
) -> Optional[dict[str, Any]]:
    if intake_id is None:
        return None
    row = (
        await db.execute(select(Intake_requests).where(Intake_requests.id == intake_id).limit(1))
    ).scalars().first()
    if row is None or not row.product_spec_json:
        return None
    try:
        raw = json.loads(row.product_spec_json)
    except Exception:
        return None
    if not isinstance(raw, dict):
        return None
    return validate_intake_product_spec(raw)
