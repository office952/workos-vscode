from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from services.integration_settings_service import get_smartbill_effective_config


@dataclass
class SmartbillConfig:
    enabled: bool
    base_url: str
    username: str
    token: str
    timeout_seconds: float
    lookup_path: str


@dataclass
class SmartbillLookupResult:
    status: str
    message: str
    normalized: dict[str, Any] | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class SmartbillConfigHealth:
    provider: str
    source: str
    enabled: bool
    configured: bool
    status: str
    missing_fields: list[str]
    present_fields: dict[str, bool]
    masked: dict[str, str | None]
    settings: dict[str, Any]
    live_validation: dict[str, Any]
    warnings: list[str] = field(default_factory=list)


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _mask_username(value: str) -> str | None:
    text = (value or "").strip()
    if not text:
        return None
    if len(text) <= 2:
        return f"{text[0]}***"
    return f"{text[:2]}***"


def _masked_base_url_host(raw_url: str) -> str | None:
    text = (raw_url or "").strip()
    if not text:
        return None
    parsed = urlparse(text)
    host = parsed.netloc or parsed.path
    host = host.split("@")[ -1 ] if "@" in host else host
    host = host.split("?")[0].strip()
    return host or None


def _raw_smartbill_values() -> dict[str, Any]:
    return {
        "enabled": getattr(settings, "smartbill_enabled", False),
        "base_url": getattr(settings, "smartbill_base_url", ""),
        "username": getattr(settings, "smartbill_username", ""),
        "token": getattr(settings, "smartbill_token", ""),
        "timeout_seconds": getattr(settings, "smartbill_timeout_seconds", 5),
        "lookup_path": getattr(settings, "smartbill_lookup_path", "/fiscal-lookup"),
    }


def get_smartbill_config_health() -> SmartbillConfigHealth:
    raw = _raw_smartbill_values()
    enabled = _as_bool(raw["enabled"])
    base_url = str(raw["base_url"] or "").strip()
    username = str(raw["username"] or "").strip()
    token = str(raw["token"] or "").strip()
    lookup_path = str(raw["lookup_path"] or "").strip() or "/fiscal-lookup"

    missing_fields: list[str] = []
    warnings: list[str] = []

    present_fields = {
        "base_url": bool(base_url),
        "username": bool(username),
        "token": bool(token),
        "lookup_path": bool(lookup_path),
        "timeout_seconds": raw["timeout_seconds"] is not None and str(raw["timeout_seconds"]).strip() != "",
    }

    if not present_fields["base_url"]:
        missing_fields.append("SMARTBILL_BASE_URL")
    if not present_fields["username"]:
        missing_fields.append("SMARTBILL_USERNAME")
    if not present_fields["token"]:
        missing_fields.append("SMARTBILL_TOKEN")

    timeout_seconds: float | None
    try:
        timeout_seconds = float(raw["timeout_seconds"])
    except (TypeError, ValueError):
        timeout_seconds = None

    invalid_config = False
    if timeout_seconds is None or timeout_seconds <= 0:
        invalid_config = True
        warnings.append("SMARTBILL_TIMEOUT_SECONDS must be numeric and > 0.")

    parsed_url = urlparse(base_url) if base_url else None
    if base_url and (not parsed_url or parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc):
        invalid_config = True
        warnings.append("SMARTBILL_BASE_URL must be a valid http/https URL.")

    if lookup_path and not lookup_path.startswith("/"):
        invalid_config = True
        warnings.append("SMARTBILL_LOOKUP_PATH must start with '/'.")

    if not enabled:
        status = "disabled"
        configured = False
    elif invalid_config:
        status = "invalid_config"
        configured = False
    elif missing_fields:
        status = "not_configured"
        configured = False
    else:
        status = "configured"
        configured = True

    return SmartbillConfigHealth(
        provider="smartbill",
        source="env",
        enabled=enabled,
        configured=configured,
        status=status,
        missing_fields=missing_fields,
        present_fields=present_fields,
        masked={
            "base_url_host": _masked_base_url_host(base_url),
            "username_hint": _mask_username(username),
        },
        settings={
            "timeout_seconds": timeout_seconds,
            "lookup_path": lookup_path,
        },
        live_validation={
            "performed": False,
            "status": "not_run",
            "message": "Configuration health does not perform live provider lookup.",
        },
        warnings=warnings,
    )


async def get_smartbill_config_health_for_db(db: AsyncSession) -> SmartbillConfigHealth:
    effective = await get_smartbill_effective_config(db)
    enabled = bool(effective.enabled)
    base_url = (effective.base_url or "").strip()
    username = (effective.username or "").strip()
    token = (effective.token or "").strip()
    lookup_path = (effective.lookup_path or "/fiscal-lookup").strip() or "/fiscal-lookup"

    missing_fields: list[str] = []
    warnings: list[str] = []

    present_fields = {
        "base_url": bool(base_url),
        "username": bool(username),
        "token": bool(token),
        "lookup_path": bool(lookup_path),
        "timeout_seconds": effective.timeout_seconds is not None,
    }

    if not present_fields["base_url"]:
        missing_fields.append("SMARTBILL_BASE_URL")
    if not present_fields["username"]:
        missing_fields.append("SMARTBILL_USERNAME")
    if not present_fields["token"]:
        missing_fields.append("SMARTBILL_TOKEN")

    timeout_seconds: float | None = effective.timeout_seconds
    invalid_config = False
    if timeout_seconds is None or timeout_seconds <= 0:
        invalid_config = True
        warnings.append("SMARTBILL_TIMEOUT_SECONDS must be numeric and > 0.")

    parsed_url = urlparse(base_url) if base_url else None
    if base_url and (not parsed_url or parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc):
        invalid_config = True
        warnings.append("SMARTBILL_BASE_URL must be a valid http/https URL.")

    if lookup_path and not lookup_path.startswith("/"):
        invalid_config = True
        warnings.append("SMARTBILL_LOOKUP_PATH must start with '/'.")

    if not enabled:
        status = "disabled"
        configured = False
    elif invalid_config:
        status = "invalid_config"
        configured = False
    elif missing_fields:
        status = "not_configured"
        configured = False
    else:
        status = "configured"
        configured = True

    return SmartbillConfigHealth(
        provider="smartbill",
        source=effective.source,
        enabled=enabled,
        configured=configured,
        status=status,
        missing_fields=missing_fields,
        present_fields=present_fields,
        masked={
            "base_url_host": _masked_base_url_host(base_url),
            "username_hint": _mask_username(username),
        },
        settings={
            "timeout_seconds": timeout_seconds,
            "lookup_path": lookup_path,
        },
        live_validation={
            "performed": False,
            "status": "not_run",
            "message": "Configuration health does not perform live provider lookup.",
        },
        warnings=warnings,
    )


def load_smartbill_config() -> SmartbillConfig:
    enabled = _as_bool(getattr(settings, "smartbill_enabled", False))
    base_url = str(getattr(settings, "smartbill_base_url", "") or "").strip()
    username = str(getattr(settings, "smartbill_username", "") or "").strip()
    token = str(getattr(settings, "smartbill_token", "") or "").strip()
    lookup_path = str(getattr(settings, "smartbill_lookup_path", "/fiscal-lookup") or "/fiscal-lookup").strip()

    timeout_raw = getattr(settings, "smartbill_timeout_seconds", 6.0)
    try:
        timeout_seconds = float(timeout_raw)
    except (TypeError, ValueError):
        timeout_seconds = 6.0
    if timeout_seconds <= 0:
        timeout_seconds = 6.0

    return SmartbillConfig(
        enabled=enabled,
        base_url=base_url,
        username=username,
        token=token,
        timeout_seconds=timeout_seconds,
        lookup_path=lookup_path,
    )


def normalize_tax_id(raw_tax_id: str, country: str = "RO") -> str | None:
    value = (raw_tax_id or "").strip().upper().replace(" ", "")
    if not value:
        return None

    country_clean = (country or "RO").strip().upper()
    if country_clean != "RO":
        return None

    if value.startswith("RO"):
        digits = "".join(ch for ch in value[2:] if ch.isdigit())
    else:
        digits = "".join(ch for ch in value if ch.isdigit())

    if not digits or len(digits) < 2 or len(digits) > 12:
        return None

    return f"RO{digits}"


class SmartbillClient:
    def __init__(self, config: SmartbillConfig):
        self.config = config

    @classmethod
    def from_settings(cls) -> "SmartbillClient":
        return cls(load_smartbill_config())

    @classmethod
    async def from_db_or_env(cls, db: AsyncSession) -> "SmartbillClient":
        effective = await get_smartbill_effective_config(db)
        return cls(
            SmartbillConfig(
                enabled=effective.enabled,
                base_url=effective.base_url,
                username=effective.username,
                token=effective.token,
                timeout_seconds=effective.timeout_seconds,
                lookup_path=effective.lookup_path,
            )
        )

    def is_configured(self) -> bool:
        return bool(
            self.config.enabled
            and self.config.base_url
            and self.config.username
            and self.config.token
        )

    def _build_url(self) -> str:
        base = self.config.base_url.rstrip("/")
        path = self.config.lookup_path
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{base}{path}"

    @staticmethod
    def _to_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _pick_first(payload: dict[str, Any], keys: list[str]) -> str | None:
        for key in keys:
            value = payload.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return None

    async def _request_lookup(self, *, country: str, tax_id: str) -> httpx.Response:
        timeout = httpx.Timeout(self.config.timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await client.post(
                self._build_url(),
                json={
                    "provider": "smartbill",
                    "country": country,
                    "tax_id": tax_id,
                },
                auth=httpx.BasicAuth(self.config.username, self.config.token),
            )

    def _normalize_provider_payload(self, raw_data: dict[str, Any], *, tax_id: str, country: str) -> dict[str, Any]:
        candidate = raw_data.get("company") if isinstance(raw_data.get("company"), dict) else raw_data

        company_name = self._pick_first(
            candidate,
            ["company_name", "name", "companyName", "denumire"],
        )
        if not company_name:
            raise ValueError("Missing provider company_name")

        registration_number = self._pick_first(
            candidate,
            ["registration_number", "registrationNumber", "reg_com", "regCom", "trade_registry"],
        )

        address = self._pick_first(candidate, ["address", "address_line", "street_address"])
        city = self._pick_first(candidate, ["city", "locality", "oras"])
        county = self._pick_first(candidate, ["county", "state", "judet"])

        vat_payer = self._to_bool(
            candidate.get("vat_payer", candidate.get("vatPayer", candidate.get("is_vat_payer")))
        )

        provider_tax_id = self._pick_first(candidate, ["tax_id", "taxId", "cui", "vat_code", "vatCode"])
        normalized_tax_id = normalize_tax_id(provider_tax_id or tax_id, country=country) or tax_id

        return {
            "tax_id": normalized_tax_id,
            "company_name": company_name,
            "registration_number": registration_number,
            "address": address,
            "city": city,
            "county": county,
            "country": country,
            "vat_payer": vat_payer,
            "source": "smartbill",
        }

    async def lookup_company(self, *, country: str, tax_id: str) -> SmartbillLookupResult:
        if not self.is_configured():
            return SmartbillLookupResult(
                status="not_configured",
                message="SmartBill lookup is not configured in backend environment.",
                warnings=["No live fiscal lookup was performed."],
            )

        try:
            response = await self._request_lookup(country=country, tax_id=tax_id)
        except httpx.TimeoutException:
            return SmartbillLookupResult(
                status="provider_timeout",
                message="SmartBill request timed out.",
                warnings=["Provider timeout during fiscal lookup."],
            )
        except httpx.HTTPError:
            return SmartbillLookupResult(
                status="provider_error",
                message="SmartBill request failed.",
                warnings=["Provider request failed before receiving a response."],
            )

        if response.status_code == 429:
            return SmartbillLookupResult(
                status="rate_limited",
                message="SmartBill rate limit reached.",
                warnings=["Please retry later."],
            )
        if response.status_code == 404:
            return SmartbillLookupResult(
                status="not_found",
                message="Company not found for provided tax id.",
                warnings=[],
            )
        if response.status_code in {408, 504}:
            return SmartbillLookupResult(
                status="provider_timeout",
                message="SmartBill request timed out.",
                warnings=["Provider timeout during fiscal lookup."],
            )
        if response.status_code >= 500:
            return SmartbillLookupResult(
                status="provider_error",
                message=f"SmartBill provider error ({response.status_code}).",
                warnings=["Provider returned server-side error."],
            )
        if response.status_code >= 400:
            return SmartbillLookupResult(
                status="provider_error",
                message=f"SmartBill provider rejected the request ({response.status_code}).",
                warnings=["Provider returned non-success response."],
            )

        try:
            payload = response.json()
        except ValueError:
            return SmartbillLookupResult(
                status="provider_error",
                message="SmartBill response is not valid JSON.",
                warnings=["Provider returned invalid response payload."],
            )

        if not isinstance(payload, dict):
            return SmartbillLookupResult(
                status="provider_error",
                message="SmartBill response has invalid payload shape.",
                warnings=["Provider returned non-object payload."],
            )

        raw_status = str(payload.get("status") or "").strip().lower()
        if raw_status in {"not_found", "notfound", "missing"}:
            return SmartbillLookupResult(
                status="not_found",
                message="Company not found for provided tax id.",
                warnings=[],
            )

        try:
            normalized = self._normalize_provider_payload(payload, tax_id=tax_id, country=country)
        except ValueError:
            return SmartbillLookupResult(
                status="provider_error",
                message="SmartBill response missing mandatory company fields.",
                warnings=["Provider payload could not be normalized."],
            )

        return SmartbillLookupResult(
            status="found",
            message="Company found via SmartBill provider.",
            normalized=normalized,
            warnings=[],
        )
