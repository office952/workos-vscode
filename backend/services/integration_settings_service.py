from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.integration_settings import Integration_settings
from services.secret_crypto import (
    SecretCryptoUnavailableError,
    decrypt_secret,
    encrypt_secret,
    mask_username,
)


@dataclass
class SmartbillMaskedConfig:
    provider: str
    source: str
    enabled: bool
    base_url: str | None
    username_present: bool
    username_hint: str | None
    token_present: bool
    lookup_path: str
    timeout_seconds: int
    last_test_status: str
    last_test_at: str | None
    last_test_message: str | None


@dataclass
class SmartbillEffectiveConfig:
    source: str
    enabled: bool
    base_url: str
    username: str
    token: str
    lookup_path: str
    timeout_seconds: float


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _clean_lookup_path(path: str | None) -> str:
    clean = (path or "/fiscal-lookup").strip() or "/fiscal-lookup"
    return clean


def _validate_base_url(base_url: str) -> None:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=422, detail="Invalid base_url. Expected valid http/https URL.")


def _validate_lookup_path(path: str) -> None:
    if not path.startswith("/"):
        raise HTTPException(status_code=422, detail="Invalid lookup_path. Must start with '/'.")


def _validate_timeout(timeout_seconds: int) -> None:
    if timeout_seconds <= 0:
        raise HTTPException(status_code=422, detail="Invalid timeout_seconds. Must be > 0.")


def _iso_or_none(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat()


async def _get_row(db: AsyncSession) -> Integration_settings | None:
    return (
        await db.execute(
            select(Integration_settings).where(Integration_settings.provider == "smartbill").limit(1)
        )
    ).scalars().first()


async def record_smartbill_test_result(
    db: AsyncSession,
    *,
    user_id: str,
    success: bool,
    message: str,
    warnings: list[str] | None = None,
) -> None:
    row = await _get_row(db)
    if row is None:
        return

    warning_suffix = ""
    if warnings:
        warning_suffix = f" Warnings: {'; '.join(warnings)}"

    row.last_test_status = "success" if success else "failed"
    row.last_test_message = f"{message}{warning_suffix}".strip()
    row.last_test_at = datetime.now(timezone.utc)
    row.updated_by = user_id
    await db.commit()


def _row_to_masked(row: Integration_settings) -> SmartbillMaskedConfig:
    username_plain = ""
    if row.username_secret:
        try:
            username_plain = decrypt_secret(row.username_secret)
        except Exception:
            username_plain = ""

    return SmartbillMaskedConfig(
        provider="smartbill",
        source="app_settings",
        enabled=bool(row.enabled),
        base_url=(row.base_url or "").strip() or None,
        username_present=bool(row.username_secret),
        username_hint=mask_username(username_plain) if username_plain else None,
        token_present=bool(row.token_secret),
        lookup_path=_clean_lookup_path(row.lookup_path),
        timeout_seconds=int(row.timeout_seconds or 5),
        last_test_status=(row.last_test_status or "not_run").strip() or "not_run",
        last_test_at=_iso_or_none(row.last_test_at),
        last_test_message=(row.last_test_message or None),
    )


def _env_effective() -> SmartbillEffectiveConfig:
    base_url = str(getattr(settings, "smartbill_base_url", "") or "").strip()
    username = str(getattr(settings, "smartbill_username", "") or "").strip()
    token = str(getattr(settings, "smartbill_token", "") or "").strip()
    lookup_path = _clean_lookup_path(str(getattr(settings, "smartbill_lookup_path", "/fiscal-lookup") or "/fiscal-lookup"))

    timeout_raw = getattr(settings, "smartbill_timeout_seconds", 5)
    try:
        timeout_seconds = float(timeout_raw)
    except (TypeError, ValueError):
        timeout_seconds = 5.0

    has_any_env = bool(
        _as_bool(getattr(settings, "smartbill_enabled", False))
        or base_url
        or username
        or token
    )

    return SmartbillEffectiveConfig(
        source="env" if has_any_env else "none",
        enabled=_as_bool(getattr(settings, "smartbill_enabled", False)),
        base_url=base_url,
        username=username,
        token=token,
        lookup_path=lookup_path,
        timeout_seconds=timeout_seconds,
    )


def _masked_from_env() -> SmartbillMaskedConfig:
    effective = _env_effective()
    return SmartbillMaskedConfig(
        provider="smartbill",
        source="env",
        enabled=effective.enabled,
        base_url=effective.base_url or None,
        username_present=bool(effective.username),
        username_hint=mask_username(effective.username) if effective.username else None,
        token_present=bool(effective.token),
        lookup_path=effective.lookup_path,
        timeout_seconds=int(effective.timeout_seconds),
        last_test_status="not_run",
        last_test_at=None,
        last_test_message=None,
    )


async def get_smartbill_settings(db: AsyncSession) -> SmartbillMaskedConfig:
    row = await _get_row(db)
    if row:
        return _row_to_masked(row)
    return _masked_from_env()


async def get_smartbill_effective_config(db: AsyncSession) -> SmartbillEffectiveConfig:
    row = await _get_row(db)
    if row:
        username_plain = ""
        token_plain = ""
        if row.username_secret:
            try:
                username_plain = decrypt_secret(row.username_secret)
            except Exception:
                username_plain = ""
        if row.token_secret:
            try:
                token_plain = decrypt_secret(row.token_secret)
            except Exception:
                token_plain = ""

        timeout_seconds = float(row.timeout_seconds or 5)

        return SmartbillEffectiveConfig(
            source="app_settings",
            enabled=bool(row.enabled),
            base_url=(row.base_url or "").strip(),
            username=username_plain,
            token=token_plain,
            lookup_path=_clean_lookup_path(row.lookup_path),
            timeout_seconds=timeout_seconds,
        )

    return _env_effective()


async def upsert_smartbill_settings(db: AsyncSession, payload: dict[str, Any], user_id: str) -> SmartbillMaskedConfig:
    row = await _get_row(db)
    if row is None:
        row = Integration_settings(provider="smartbill")
        db.add(row)

    enabled = _as_bool(payload.get("enabled", row.enabled if row.enabled is not None else False))
    base_url = str(payload.get("base_url", row.base_url or "") or "").strip()
    lookup_path = _clean_lookup_path(str(payload.get("lookup_path", row.lookup_path or "/fiscal-lookup") or "/fiscal-lookup"))

    timeout_raw = payload.get("timeout_seconds", row.timeout_seconds if row.timeout_seconds is not None else 5)
    try:
        timeout_seconds = int(timeout_raw)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Invalid timeout_seconds. Must be an integer.")

    _validate_lookup_path(lookup_path)
    _validate_timeout(timeout_seconds)
    if base_url:
        _validate_base_url(base_url)

    username_input = payload.get("username", None)
    token_input = payload.get("token", None)
    clear_token = _as_bool(payload.get("clear_token", False))

    try:
        if isinstance(username_input, str) and username_input.strip():
            row.username_secret = encrypt_secret(username_input.strip())
        elif username_input is None:
            pass
        elif isinstance(username_input, str) and not username_input.strip():
            # empty username means no change, explicit clear can be added later if needed
            pass

        if clear_token:
            row.token_secret = None
        elif isinstance(token_input, str) and token_input.strip():
            row.token_secret = encrypt_secret(token_input.strip())
        elif token_input is None:
            pass
        elif isinstance(token_input, str) and not token_input.strip():
            # empty token is treated as no change to avoid accidental wipe
            pass
    except SecretCryptoUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    row.enabled = enabled
    row.base_url = base_url or None
    row.lookup_path = lookup_path
    row.timeout_seconds = timeout_seconds
    row.config_source = "app_settings"
    row.updated_by = user_id

    if row.last_test_status is None:
        row.last_test_status = "not_run"

    await db.commit()
    await db.refresh(row)
    return _row_to_masked(row)


async def clear_smartbill_token(db: AsyncSession, user_id: str) -> SmartbillMaskedConfig:
    row = await _get_row(db)
    if row is None:
        row = Integration_settings(provider="smartbill")
        db.add(row)

    row.token_secret = None
    row.updated_by = user_id
    row.config_source = "app_settings"

    await db.commit()
    await db.refresh(row)
    return _row_to_masked(row)


def _effective_is_locally_valid(effective: SmartbillEffectiveConfig) -> tuple[str, list[str]]:
    warnings: list[str] = []

    if not effective.enabled:
        return "disabled", warnings

    if not effective.base_url:
        warnings.append("SMARTBILL_BASE_URL missing")
    if not effective.username:
        warnings.append("SMARTBILL_USERNAME missing")
    if not effective.token:
        warnings.append("SMARTBILL_TOKEN missing")

    if effective.base_url:
        parsed = urlparse(effective.base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            warnings.append("SMARTBILL_BASE_URL invalid")

    if effective.lookup_path and not effective.lookup_path.startswith("/"):
        warnings.append("SMARTBILL_LOOKUP_PATH invalid")

    if effective.timeout_seconds <= 0:
        warnings.append("SMARTBILL_TIMEOUT_SECONDS invalid")

    if warnings:
        if any("invalid" in warning for warning in warnings):
            return "invalid_config", warnings
        return "not_configured", warnings

    return "configured", warnings


async def test_smartbill_config_local(db: AsyncSession, user_id: str) -> dict[str, Any]:
    effective = await get_smartbill_effective_config(db)
    status, warnings = _effective_is_locally_valid(effective)

    await record_smartbill_test_result(
        db,
        user_id=user_id,
        success=status == "configured",
        message="Local configuration validation passed." if status == "configured" else "Local validation failed.",
        warnings=warnings,
    )

    return {
        "provider": "smartbill",
        "source": effective.source,
        "status": status,
        "ok": status == "configured",
        "mode": "local_config_validation",
        "message": "Local configuration validation only. Live provider lookup not executed.",
        "warnings": warnings,
    }