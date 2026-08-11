"""Runtime company commercial settings — canonical VAT % and EUR/RON rate.

WORKOS_FX_COMMERCIAL_AUTHORITY_CLOSURE_V1:
  - Money-affecting consumers must use require_configured_eur_to_ron_rate (fail-closed).
  - DEFAULT_EUR_TO_RON_RATE is NOT a live commercial fallback.
  - Settings GET must not persist FX and must not ALTER TABLE.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from models.company_commercial_settings import CompanyCommercialSettings
from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

DEFAULT_VAT_PCT = 21.0
# Demo seed / UI placeholder / explicit bootstrap only — never live commercial fallback.
DEFAULT_EUR_TO_RON_RATE = 5.0
_MIN_VAT_PCT = 0.0
_MAX_VAT_PCT = 100.0
_MIN_EUR_TO_RON_RATE = 0.0001
_MAX_EUR_TO_RON_RATE = 9999.9999

EUR_TO_RON_RATE_MISSING = "eur_to_ron_rate_missing"
EUR_TO_RON_RATE_INVALID = "eur_to_ron_rate_invalid"
EUR_TO_RON_COLUMN_UNAVAILABLE = "eur_to_ron_column_unavailable"
COMPANY_COMMERCIAL_SETTINGS_ROW_MISSING = "company_commercial_settings_row_missing"


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


async def eur_to_ron_column_present(db: AsyncSession) -> bool:
    """Read-only schema probe — never ALTER TABLE."""
    bind = db.get_bind()
    if bind is None:
        return True
    dialect = bind.dialect.name
    try:
        if dialect == "sqlite":
            result = await db.execute(text("PRAGMA table_info(company_commercial_settings)"))
            columns = {row[1] for row in result.fetchall()}
            return "eur_to_ron_rate" in columns
        # Non-SQLite: assume model/migration alignment; OperationalError handled at query time.
        return True
    except Exception:
        logger.exception("Failed to probe company_commercial_settings.eur_to_ron_rate column")
        return False


async def ensure_eur_to_ron_column_explicit(db: AsyncSession) -> bool:
    """Explicit maintenance/bootstrap only — NOT called from Settings/money GET.

    Returns True if column exists after the call. SQLite-only ALTER when missing.
    """
    if await eur_to_ron_column_present(db):
        return True
    bind = db.get_bind()
    if bind is None or bind.dialect.name != "sqlite":
        return False
    await db.execute(
        text(
            "ALTER TABLE company_commercial_settings "
            "ADD COLUMN eur_to_ron_rate FLOAT"
        )
    )
    await db.commit()
    logger.info("Explicit bootstrap: added company_commercial_settings.eur_to_ron_rate")
    return True


class CompanyCommercialSettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _require_fx_column(self) -> None:
        if not await eur_to_ron_column_present(self.db):
            raise ValueError(EUR_TO_RON_COLUMN_UNAVAILABLE)

    async def get_or_create(self) -> CompanyCommercialSettings:
        """Ensure a settings row exists. Does NOT invent or persist FX 5.0. No ALTER."""
        await self._require_fx_column()
        try:
            result = await self.db.execute(
                select(CompanyCommercialSettings).order_by(CompanyCommercialSettings.id.asc())
            )
        except (OperationalError, ProgrammingError) as exc:
            # Controlled failure for ancient DBs missing the column despite probe.
            raise ValueError(EUR_TO_RON_COLUMN_UNAVAILABLE) from exc
        row = result.scalars().first()
        if row is not None:
            return row
        row = CompanyCommercialSettings(
            default_vat_pct=DEFAULT_VAT_PCT,
            eur_to_ron_rate=None,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def get_settings(self) -> Dict[str, Any]:
        """Editor/read model — FX may be null when not configured. No write-on-read FX."""
        row = await self.get_or_create()
        rate = getattr(row, "eur_to_ron_rate", None)
        rate_out: float | None
        if rate is None:
            rate_out = None
        else:
            try:
                rate_out = float(rate)
            except (TypeError, ValueError):
                rate_out = None
        return {
            "default_vat_pct": float(row.default_vat_pct),
            "eur_to_ron_rate": rate_out,
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


async def resolve_configured_eur_to_ron_rate(
    db: AsyncSession,
) -> tuple[float | None, str | None]:
    """Fail-closed FX resolve for money consumers. No write. No ALTER. No default 5.0."""
    if not await eur_to_ron_column_present(db):
        return None, EUR_TO_RON_COLUMN_UNAVAILABLE
    try:
        result = await db.execute(
            select(CompanyCommercialSettings).order_by(CompanyCommercialSettings.id.asc()).limit(1)
        )
    except (OperationalError, ProgrammingError):
        return None, EUR_TO_RON_COLUMN_UNAVAILABLE
    row = result.scalars().first()
    if row is None:
        return None, COMPANY_COMMERCIAL_SETTINGS_ROW_MISSING
    rate = getattr(row, "eur_to_ron_rate", None)
    if rate is None:
        return None, EUR_TO_RON_RATE_MISSING
    try:
        value = float(rate)
    except (TypeError, ValueError):
        return None, EUR_TO_RON_RATE_INVALID
    if value <= 0:
        return None, EUR_TO_RON_RATE_INVALID
    return round(value, 4), None


async def require_configured_eur_to_ron_rate(db: AsyncSession) -> float:
    """Canonical money FX authority — raises ValueError with stable error codes."""
    rate, err = await resolve_configured_eur_to_ron_rate(db)
    if rate is None:
        raise ValueError(err or EUR_TO_RON_RATE_MISSING)
    return float(rate)


async def get_eur_to_ron_rate(db: AsyncSession) -> float:
    """Deprecated alias — fail-closed. Prefer require_configured_eur_to_ron_rate."""
    return await require_configured_eur_to_ron_rate(db)
