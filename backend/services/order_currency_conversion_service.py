"""Quote → order commercial currency handoff (EUR rounded, RON via Settings rate)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

BASE_CURRENCY_DEFAULT = "RON"
COMMERCIAL_CURRENCY_EUR = "EUR"


@dataclass(frozen=True)
class CommercialCurrencyHandoff:
    commercial_currency: str
    base_currency: str
    commercial_total_eur: Optional[float]
    commercial_total_eur_raw: float
    exchange_rate_eur_ron: Optional[float]
    base_total_ron: float
    base_total_net: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def round_commercial_total_eur(amount: float) -> int:
    """Commercial EUR totals round to whole euros for order acceptance."""
    return int(round(float(amount)))


def round_money(amount: float, decimals: int = 2) -> float:
    return round(float(amount), decimals)


def normalize_currency_code(raw: Optional[str], *, default: str = BASE_CURRENCY_DEFAULT) -> str:
    value = (raw or default).strip().upper()
    if value == "LEI":
        return "RON"
    return value or default


def validate_eur_to_ron_rate(rate: Optional[float]) -> float:
    if rate is None:
        raise ValueError("eur_to_ron_rate_missing")
    try:
        value = float(rate)
    except (TypeError, ValueError):
        raise ValueError("eur_to_ron_rate_invalid") from None
    if value <= 0:
        raise ValueError("eur_to_ron_rate_invalid")
    return value


def convert_quote_totals_to_order_base(
    *,
    gross_amount: float,
    net_amount: Optional[float],
    source_currency: str,
    eur_to_ron_rate: Optional[float],
    base_currency: str = BASE_CURRENCY_DEFAULT,
) -> CommercialCurrencyHandoff:
    """Convert priced quote totals into order base currency totals."""
    src = normalize_currency_code(source_currency)
    base = normalize_currency_code(base_currency)
    gross_raw = float(gross_amount)
    net_raw = float(net_amount) if net_amount is not None else None

    if src == COMMERCIAL_CURRENCY_EUR and base == BASE_CURRENCY_DEFAULT:
        rate = validate_eur_to_ron_rate(eur_to_ron_rate)
        rounded_eur = round_commercial_total_eur(gross_raw)
        base_gross = round_money(rounded_eur * rate)
        base_net = None
        if net_raw is not None:
            rounded_net_eur = round_commercial_total_eur(net_raw)
            base_net = round_money(rounded_net_eur * rate)
        return CommercialCurrencyHandoff(
            commercial_currency=COMMERCIAL_CURRENCY_EUR,
            base_currency=base,
            commercial_total_eur=float(rounded_eur),
            commercial_total_eur_raw=gross_raw,
            exchange_rate_eur_ron=rate,
            base_total_ron=base_gross,
            base_total_net=base_net,
        )

    # Same-currency or non-EUR→RON path: preserve numeric totals in base currency.
    return CommercialCurrencyHandoff(
        commercial_currency=src,
        base_currency=base,
        commercial_total_eur=None,
        commercial_total_eur_raw=gross_raw,
        exchange_rate_eur_ron=None,
        base_total_ron=round_money(gross_raw),
        base_total_net=round_money(net_raw) if net_raw is not None else None,
    )


def extract_currency_from_quote_snapshot(snapshot: Any) -> str:
    """Read commercial currency from QuoteCalculationSnapshot or dict."""
    if snapshot is None:
        return BASE_CURRENCY_DEFAULT
    if hasattr(snapshot, "cost_result"):
        cr = snapshot.cost_result
        if cr is not None and hasattr(cr, "currency"):
            return normalize_currency_code(getattr(cr, "currency", None))
    if isinstance(snapshot, dict):
        cr = snapshot.get("cost_result")
        if isinstance(cr, dict):
            return normalize_currency_code(cr.get("currency"))
    return BASE_CURRENCY_DEFAULT
