"""Runtime company commercial settings — canonical VAT % and EUR/RON rate."""

from __future__ import annotations

import logging
from typing import Any, Dict

from models.company_commercial_settings import CompanyCommercialSettings
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

DEFAULT_VAT_PCT = 21.0
DEFAULT_EUR_TO_RON_RATE = 5.0
_MIN_VAT_PCT = 0.0
_MAX_VAT_PCT = 100.0
_MIN_EUR_TO_RON_RATE = 0.0001
_MAX_EUR_TO_RON_RATE = 9999.9999


def validate_vat_pct(value: float) -> float:
    """Validate VAT percent; 0 is allowed."""
    try:
        pct = float(value)
    except (TypeError, ValueError):
        raise ValueError("default_vat_pct must be a number")
    if pct < _MIN_VAT_PCT or pct > _MAX_VAT_PCT:
        raise ValueError("default_vat_pct must be between 0 and 100")
    return pct


def validate_eur_to_ron_rate(value: float) -> float:
    try:
        rate = float(value)
    except (TypeError, ValueError):
        raise ValueError("eur_to_ron_rate must be a number")
    if rate < _MIN_EUR_TO_RON_RATE or rate > _MAX_EUR_TO_RON_RATE:
        raise ValueError("eur_to_ron_rate must be greater than 0")
    return round(rate, 4)


async def _ensure_eur_to_ron_column(db: AsyncSession) -> None:
    """Dev-safe bootstrap when SQLite table predates eur_to_ron_rate column."""
    bind = db.get_bind()
    if bind is None or bind.dialect.name != "sqlite":
        return
    result = await db.execute(text("PRAGMA table_info(company_commercial_settings)"))
    columns = {row[1] for row in result.fetchall()}
    if "eur_to_ron_rate" in columns:
        return
    await db.execute(
        text(
            "ALTER TABLE company_commercial_settings "
            "ADD COLUMN eur_to_ron_rate FLOAT"
        )
    )
    await db.commit()
    logger.info("Bootstrapped company_commercial_settings.eur_to_ron_rate column")


class CompanyCommercialSettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self) -> CompanyCommercialSettings:
        await _ensure_eur_to_ron_column(self.db)
        result = await self.db.execute(
            select(CompanyCommercialSettings).order_by(CompanyCommercialSettings.id.asc())
        )
        row = result.scalars().first()
        if row is not None:
            if getattr(row, "eur_to_ron_rate", None) is None:
                row.eur_to_ron_rate = DEFAULT_EUR_TO_RON_RATE
                await self.db.commit()
                await self.db.refresh(row)
            return row
        row = CompanyCommercialSettings(
            default_vat_pct=DEFAULT_VAT_PCT,
            eur_to_ron_rate=DEFAULT_EUR_TO_RON_RATE,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def get_settings(self) -> Dict[str, Any]:
        row = await self.get_or_create()
        rate = getattr(row, "eur_to_ron_rate", None)
        return {
            "default_vat_pct": float(row.default_vat_pct),
            "eur_to_ron_rate": float(rate if rate is not None else DEFAULT_EUR_TO_RON_RATE),
        }

    async def update_settings(
        self,
        *,
        default_vat_pct: float | None = None,
        eur_to_ron_rate: float | None = None,
    ) -> Dict[str, Any]:
        row = await self.get_or_create()
        if default_vat_pct is not None:
            row.default_vat_pct = validate_vat_pct(default_vat_pct)
        if eur_to_ron_rate is not None:
            row.eur_to_ron_rate = validate_eur_to_ron_rate(eur_to_ron_rate)
        await self.db.commit()
        await self.db.refresh(row)
        return await self.get_settings()

    async def update_default_vat_pct(self, value: float) -> Dict[str, Any]:
        return await self.update_settings(default_vat_pct=value)

    async def update_eur_to_ron_rate(self, value: float) -> Dict[str, Any]:
        return await self.update_settings(eur_to_ron_rate=value)


async def get_default_vat_pct(db: AsyncSession) -> float:
    """Return active company VAT % from runtime settings."""
    svc = CompanyCommercialSettingsService(db)
    row = await svc.get_or_create()
    return float(row.default_vat_pct)


async def get_eur_to_ron_rate(db: AsyncSession) -> float:
    """Return active EUR/RON rate from runtime settings."""
    svc = CompanyCommercialSettingsService(db)
    settings = await svc.get_settings()
    return float(settings["eur_to_ron_rate"])
