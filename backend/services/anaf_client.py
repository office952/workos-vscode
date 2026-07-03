from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import httpx

from core.config import settings
from services.smartbill_client import normalize_tax_id


DEFAULT_ANAF_TVA_URL = "https://webservicesp.anaf.ro/api/PlatitorTvaRest/v9/tva"


@dataclass
class AnafConfig:
    enabled: bool
    tva_url: str
    timeout_seconds: float
    cache_ttl_seconds: float
    rate_limit_seconds: float


@dataclass
class AnafLookupResult:
    status: str
    message: str
    normalized: dict[str, Any] | None = None
    warnings: list[str] = field(default_factory=list)


_cache: dict[str, tuple[float, AnafLookupResult]] = {}
_rate_lock = asyncio.Lock()
_last_request_at: float = 0.0


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def load_anaf_config() -> AnafConfig:
    enabled = _as_bool(getattr(settings, "anaf_enabled", True))
    tva_url = str(getattr(settings, "anaf_tva_url", DEFAULT_ANAF_TVA_URL) or DEFAULT_ANAF_TVA_URL).strip()

    timeout_raw = getattr(settings, "anaf_timeout_seconds", 6.0)
    try:
        timeout_seconds = float(timeout_raw)
    except (TypeError, ValueError):
        timeout_seconds = 6.0
    if timeout_seconds <= 0:
        timeout_seconds = 6.0

    cache_ttl_raw = getattr(settings, "anaf_cache_ttl_seconds", 86400)
    try:
        cache_ttl_seconds = float(cache_ttl_raw)
    except (TypeError, ValueError):
        cache_ttl_seconds = 86400.0
    if cache_ttl_seconds < 0:
        cache_ttl_seconds = 0.0

    rate_limit_raw = getattr(settings, "anaf_rate_limit_seconds", 1.0)
    try:
        rate_limit_seconds = float(rate_limit_raw)
    except (TypeError, ValueError):
        rate_limit_seconds = 1.0
    if rate_limit_seconds <= 0:
        rate_limit_seconds = 1.0

    return AnafConfig(
        enabled=enabled,
        tva_url=tva_url,
        timeout_seconds=timeout_seconds,
        cache_ttl_seconds=cache_ttl_seconds,
        rate_limit_seconds=rate_limit_seconds,
    )


def _cui_digits(tax_id: str) -> str | None:
    normalized = normalize_tax_id(tax_id, country="RO")
    if not normalized:
        return None
    digits = "".join(ch for ch in normalized if ch.isdigit())
    return digits or None


def _pick_text(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _compose_fiscal_address(fiscal_address: dict[str, Any] | None, fallback: str | None) -> str | None:
    if not fiscal_address:
        return fallback

    parts = [
        _pick_text(fiscal_address, "ddenumire_Strada"),
        _pick_text(fiscal_address, "dnumar_Strada"),
        _pick_text(fiscal_address, "ddetalii_Adresa"),
        _pick_text(fiscal_address, "ddenumire_Localitate"),
        _pick_text(fiscal_address, "ddenumire_Judet"),
        _pick_text(fiscal_address, "dcod_Postal"),
    ]
    composed = ", ".join(part for part in parts if part)
    return composed or fallback


def _normalize_found_entry(
    entry: dict[str, Any],
    *,
    tax_id: str,
    country: str,
) -> tuple[dict[str, Any], list[str]]:
    general = entry.get("date_generale") if isinstance(entry.get("date_generale"), dict) else {}
    vat_info = entry.get("inregistrare_scop_Tva") if isinstance(entry.get("inregistrare_scop_Tva"), dict) else {}
    inactive_info = entry.get("stare_inactiv") if isinstance(entry.get("stare_inactiv"), dict) else {}
    fiscal_address = (
        entry.get("adresa_domiciliu_fiscal") if isinstance(entry.get("adresa_domiciliu_fiscal"), dict) else None
    )

    company_name = _pick_text(general, "denumire")
    if not company_name:
        raise ValueError("Missing ANAF company name")

    warnings: list[str] = []
    if inactive_info.get("statusInactivi") is True:
        warnings.append("Contribuabil marcat inactiv la data interogarii.")
    if general.get("statusRO_e_Factura") is False:
        warnings.append("Contribuabilul nu apare in Registrul RO e-Factura la data interogarii.")

    registration_state = _pick_text(general, "stare_inregistrare") or ""
    if registration_state and "INREGISTRAT" not in registration_state.upper():
        warnings.append(f"Stare inregistrare ANAF: {registration_state}.")

    normalized = {
        "tax_id": normalize_tax_id(_pick_text(general, "cui") or tax_id, country=country) or tax_id,
        "company_name": company_name,
        "registration_number": _pick_text(general, "nrRegCom"),
        "address": _compose_fiscal_address(fiscal_address, _pick_text(general, "adresa")),
        "city": _pick_text(fiscal_address or {}, "ddenumire_Localitate"),
        "county": _pick_text(fiscal_address or {}, "ddenumire_Judet"),
        "country": country,
        "vat_payer": bool(vat_info.get("scpTVA")),
        "source": "anaf",
    }
    return normalized, warnings


def _cache_key(cui_digits: str, query_date: str) -> str:
    return f"{cui_digits}:{query_date}"


async def _respect_rate_limit(rate_limit_seconds: float) -> None:
    global _last_request_at

    async with _rate_lock:
        now = time.monotonic()
        wait_for = rate_limit_seconds - (now - _last_request_at)
        if wait_for > 0:
            await asyncio.sleep(wait_for)
        _last_request_at = time.monotonic()


class AnafClient:
    def __init__(self, config: AnafConfig):
        self.config = config

    @classmethod
    def from_settings(cls) -> "AnafClient":
        return cls(load_anaf_config())

    def is_enabled(self) -> bool:
        return bool(self.config.enabled and self.config.tva_url)

    async def lookup_company(self, *, country: str, tax_id: str, query_date: date | None = None) -> AnafLookupResult:
        if not self.is_enabled():
            return AnafLookupResult(
                status="not_configured",
                message="ANAF lookup is disabled in backend environment.",
                warnings=["Set ANAF_ENABLED=true to use ANAF fiscal lookup."],
            )

        cui_digits = _cui_digits(tax_id)
        if not cui_digits:
            return AnafLookupResult(
                status="invalid_input",
                message="Invalid tax_id format. Expected RO CUI (with or without RO prefix).",
                warnings=["ANAF lookup input validation failed."],
            )

        effective_date = query_date or date.today()
        date_text = effective_date.isoformat()
        cache_key = _cache_key(cui_digits, date_text)

        if self.config.cache_ttl_seconds > 0:
            cached = _cache.get(cache_key)
            if cached is not None:
                cached_at, cached_result = cached
                if time.monotonic() - cached_at <= self.config.cache_ttl_seconds:
                    return cached_result

        await _respect_rate_limit(self.config.rate_limit_seconds)

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(self.config.timeout_seconds)) as client:
                response = await client.post(
                    self.config.tva_url,
                    json=[{"cui": int(cui_digits), "data": date_text}],
                    headers={"Content-Type": "application/json"},
                )
        except httpx.TimeoutException:
            return AnafLookupResult(
                status="provider_timeout",
                message="ANAF request timed out.",
                warnings=["Provider timeout during fiscal lookup."],
            )
        except httpx.HTTPError:
            return AnafLookupResult(
                status="provider_error",
                message="ANAF request failed.",
                warnings=["Provider request failed before receiving a response."],
            )

        if response.status_code == 429:
            return AnafLookupResult(
                status="rate_limited",
                message="ANAF rate limit reached.",
                warnings=["Please retry later."],
            )
        if response.status_code in {408, 504}:
            return AnafLookupResult(
                status="provider_timeout",
                message="ANAF request timed out.",
                warnings=["Provider timeout during fiscal lookup."],
            )
        if response.status_code >= 500:
            return AnafLookupResult(
                status="provider_error",
                message=f"ANAF provider error ({response.status_code}).",
                warnings=["Provider returned server-side error."],
            )
        if response.status_code >= 400:
            return AnafLookupResult(
                status="provider_error",
                message=f"ANAF provider rejected the request ({response.status_code}).",
                warnings=["Provider returned non-success response."],
            )

        try:
            payload = response.json()
        except ValueError:
            return AnafLookupResult(
                status="provider_error",
                message="ANAF response is not valid JSON.",
                warnings=["Provider returned invalid response payload."],
            )

        if not isinstance(payload, dict):
            return AnafLookupResult(
                status="provider_error",
                message="ANAF response has invalid payload shape.",
                warnings=["Provider returned non-object payload."],
            )

        found = payload.get("found")
        if not isinstance(found, list):
            found = []

        if not found:
            result = AnafLookupResult(
                status="not_found",
                message="Company not found for provided tax id.",
                warnings=[],
            )
            if self.config.cache_ttl_seconds > 0:
                _cache[cache_key] = (time.monotonic(), result)
            return result

        first = found[0]
        if not isinstance(first, dict):
            return AnafLookupResult(
                status="provider_error",
                message="ANAF response entry has invalid shape.",
                warnings=["Provider payload could not be normalized."],
            )

        try:
            normalized, warnings = _normalize_found_entry(first, tax_id=tax_id, country=country)
        except ValueError:
            return AnafLookupResult(
                status="provider_error",
                message="ANAF response missing mandatory company fields.",
                warnings=["Provider payload could not be normalized."],
            )

        result = AnafLookupResult(
            status="found",
            message="Company found via ANAF provider.",
            normalized=normalized,
            warnings=warnings,
        )
        if self.config.cache_ttl_seconds > 0:
            _cache[cache_key] = (time.monotonic(), result)
        return result
