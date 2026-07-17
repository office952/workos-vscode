"""Legacy POST /entities/quotes/price retirement — no calculation, no financial write.

Active customer commercial authority remains Intake V6 → CommercialPriceProposal 7G.
"""

from __future__ import annotations

from typing import Any

LEGACY_QUOTE_PRICE_RETIRED_ERROR = "legacy_quote_price_retired"

LEGACY_QUOTE_PRICE_RETIRED_MESSAGE_RO = (
    "Flux comercial retras. Folosește Intake V6 pentru calculul ofertei."
)

LEGACY_QUOTE_PRICE_RETIRED_DETAIL: dict[str, Any] = {
    "error": LEGACY_QUOTE_PRICE_RETIRED_ERROR,
    "message": LEGACY_QUOTE_PRICE_RETIRED_MESSAGE_RO,
    "active_authority": "commercial_price_proposal_7g",
    "operator_path": "/intake-v6",
    "calculation_performed": False,
    "financial_write": False,
}


def raise_legacy_quote_price_retired() -> None:
    from fastapi import HTTPException

    raise HTTPException(status_code=410, detail=LEGACY_QUOTE_PRICE_RETIRED_DETAIL)
