from __future__ import annotations

from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from services.anaf_client import AnafClient, AnafLookupResult
from services.smartbill_client import SmartbillClient, SmartbillLookupResult

FiscalProvider = Literal["anaf", "smartbill", "auto"]
ResolvedFiscalProvider = Literal["anaf", "smartbill"]


def _should_fallback_to_smartbill(anaf_result: AnafLookupResult) -> bool:
    return anaf_result.status in {"provider_timeout", "provider_error", "rate_limited", "not_configured"}


async def run_fiscal_lookup(
    *,
    provider: FiscalProvider,
    country: str,
    tax_id: str,
    db: AsyncSession,
) -> tuple[AnafLookupResult | SmartbillLookupResult, ResolvedFiscalProvider]:
    if provider == "smartbill":
        client = await SmartbillClient.from_db_or_env(db)
        result = await client.lookup_company(country=country, tax_id=tax_id)
        return result, "smartbill"

    anaf_client = AnafClient.from_settings()
    anaf_result = await anaf_client.lookup_company(country=country, tax_id=tax_id)

    if provider == "anaf":
        return anaf_result, "anaf"

    if anaf_result.status == "found" or not _should_fallback_to_smartbill(anaf_result):
        return anaf_result, "anaf"

    smartbill_client = await SmartbillClient.from_db_or_env(db)
    smartbill_result = await smartbill_client.lookup_company(country=country, tax_id=tax_id)
    if smartbill_result.status == "found":
        return smartbill_result, "smartbill"

    if smartbill_result.status == "not_configured":
        return anaf_result, "anaf"

    combined_warnings = [*anaf_result.warnings, *smartbill_result.warnings]
    return SmartbillLookupResult(
        status=smartbill_result.status,
        message=smartbill_result.message,
        normalized=smartbill_result.normalized,
        warnings=combined_warnings,
    ), "smartbill"
