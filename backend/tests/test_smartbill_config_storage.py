from __future__ import annotations

import os

import pytest
from sqlalchemy import delete, func, select

from core.config import settings
from models.clients import Clients
from models.integration_settings import Integration_settings
from models.intake_requests import Intake_requests
from models.orders import Orders
from models.quotes import Quotes

SMARTBILL_ENV_KEYS = [
    "SMARTBILL_ENABLED",
    "SMARTBILL_BASE_URL",
    "SMARTBILL_USERNAME",
    "SMARTBILL_TOKEN",
    "SMARTBILL_TIMEOUT_SECONDS",
    "SMARTBILL_LOOKUP_PATH",
]

os.environ.setdefault("INTEGRATION_SECRET_KEY", "pytest-integration-secret")


def _clear_smartbill_settings_cache() -> None:
    for attr in [
        "smartbill_enabled",
        "smartbill_base_url",
        "smartbill_username",
        "smartbill_token",
        "smartbill_timeout_seconds",
        "smartbill_lookup_path",
    ]:
        settings.__dict__.pop(attr, None)


def _set_env(monkeypatch, **values):
    for key in SMARTBILL_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    _clear_smartbill_settings_cache()


async def _clear_app_settings_row(db_session):
    await db_session.execute(delete(Integration_settings).where(Integration_settings.provider == "smartbill"))
    await db_session.commit()


async def _count_mutation_tables(db_session):
    clients_count = await db_session.scalar(select(func.count(Clients.id)))
    intake_count = await db_session.scalar(select(func.count(Intake_requests.id)))
    quotes_count = await db_session.scalar(select(func.count(Quotes.id)))
    orders_count = await db_session.scalar(select(func.count(Orders.id)))
    return (
        int(clients_count or 0),
        int(intake_count or 0),
        int(quotes_count or 0),
        int(orders_count or 0),
    )


def test_smartbill_config_get_requires_auth(unauth_client):
    resp = unauth_client.get("/api/v1/integrations/providers/smartbill/config")
    assert resp.status_code in (401, 403)


def test_smartbill_config_put_requires_auth(unauth_client):
    resp = unauth_client.put(
        "/api/v1/integrations/providers/smartbill/config",
        json={"enabled": True, "base_url": "https://api.smartbill.test", "lookup_path": "/fiscal-lookup", "timeout_seconds": 5},
    )
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_smartbill_put_and_get_masked_config(auth_client, db_session):
    await _clear_app_settings_row(db_session)

    put_resp = auth_client.put(
        "/api/v1/integrations/providers/smartbill/config",
        json={
            "enabled": True,
            "base_url": "https://api.smartbill.test",
            "username": "office@firma.ro",
            "token": "super-secret-token",
            "lookup_path": "/fiscal-lookup",
            "timeout_seconds": 5,
        },
    )
    assert put_resp.status_code == 200
    put_body = put_resp.json()
    assert put_body["token_present"] is True
    assert "token" not in put_body

    row = (
        await db_session.execute(select(Integration_settings).where(Integration_settings.provider == "smartbill").limit(1))
    ).scalars().first()
    assert row is not None
    assert row.token_secret is not None
    assert "super-secret-token" not in (row.token_secret or "")
    assert row.token_secret.startswith("enc:v1:")

    get_resp = auth_client.get("/api/v1/integrations/providers/smartbill/config")
    assert get_resp.status_code == 200
    get_body = get_resp.json()
    assert get_body["source"] == "app_settings"
    assert get_body["token_present"] is True
    assert "token" not in get_body
    assert "authorization" not in get_resp.text.lower()


@pytest.mark.asyncio
async def test_put_without_token_preserves_existing_secret(auth_client, db_session):
    await _clear_app_settings_row(db_session)

    first = auth_client.put(
        "/api/v1/integrations/providers/smartbill/config",
        json={
            "enabled": True,
            "base_url": "https://api.smartbill.test",
            "username": "office@firma.ro",
            "token": "token-one",
            "lookup_path": "/fiscal-lookup",
            "timeout_seconds": 5,
        },
    )
    assert first.status_code == 200

    row_before = (
        await db_session.execute(select(Integration_settings).where(Integration_settings.provider == "smartbill").limit(1))
    ).scalars().first()
    assert row_before is not None
    token_cipher_before = row_before.token_secret

    second = auth_client.put(
        "/api/v1/integrations/providers/smartbill/config",
        json={
            "enabled": True,
            "base_url": "https://api.smartbill.test",
            "username": "office2@firma.ro",
            "lookup_path": "/fiscal-lookup",
            "timeout_seconds": 5,
        },
    )
    assert second.status_code == 200
    assert second.json()["token_present"] is True

    row_after = (
        await db_session.execute(select(Integration_settings).where(Integration_settings.provider == "smartbill").limit(1))
    ).scalars().first()
    assert row_after is not None
    assert row_after.token_secret == token_cipher_before


@pytest.mark.asyncio
async def test_clear_token_endpoint(auth_client, db_session):
    await _clear_app_settings_row(db_session)

    auth_client.put(
        "/api/v1/integrations/providers/smartbill/config",
        json={
            "enabled": True,
            "base_url": "https://api.smartbill.test",
            "username": "office@firma.ro",
            "token": "token-one",
            "lookup_path": "/fiscal-lookup",
            "timeout_seconds": 5,
        },
    )

    clear_resp = auth_client.delete("/api/v1/integrations/providers/smartbill/secret/token")
    assert clear_resp.status_code == 200
    assert clear_resp.json()["token_present"] is False


@pytest.mark.asyncio
async def test_invalid_config_inputs_rejected(auth_client, db_session):
    await _clear_app_settings_row(db_session)

    bad_url = auth_client.put(
        "/api/v1/integrations/providers/smartbill/config",
        json={"enabled": True, "base_url": "bad-url", "lookup_path": "/fiscal-lookup", "timeout_seconds": 5},
    )
    assert bad_url.status_code == 422

    bad_timeout = auth_client.put(
        "/api/v1/integrations/providers/smartbill/config",
        json={"enabled": True, "base_url": "https://api.smartbill.test", "lookup_path": "/fiscal-lookup", "timeout_seconds": 0},
    )
    assert bad_timeout.status_code == 422

    bad_lookup = auth_client.put(
        "/api/v1/integrations/providers/smartbill/config",
        json={"enabled": True, "base_url": "https://api.smartbill.test", "lookup_path": "fiscal", "timeout_seconds": 5},
    )
    assert bad_lookup.status_code == 422


@pytest.mark.asyncio
async def test_effective_config_uses_app_settings_when_present(auth_client, db_session):
    await _clear_app_settings_row(db_session)

    auth_client.put(
        "/api/v1/integrations/providers/smartbill/config",
        json={
            "enabled": True,
            "base_url": "https://api.smartbill.app",
            "username": "app@firma.ro",
            "token": "token-app",
            "lookup_path": "/fiscal-lookup",
            "timeout_seconds": 7,
        },
    )

    health = auth_client.get("/api/v1/integrations/providers/smartbill/health")
    assert health.status_code == 200
    body = health.json()
    assert body["source"] == "app_settings"
    assert body["configured"] is True


@pytest.mark.asyncio
async def test_effective_config_env_fallback_when_app_settings_missing(monkeypatch, auth_client, db_session):
    await _clear_app_settings_row(db_session)
    _set_env(
        monkeypatch,
        SMARTBILL_ENABLED="true",
        SMARTBILL_BASE_URL="https://api.smartbill.env",
        SMARTBILL_USERNAME="env@firma.ro",
        SMARTBILL_TOKEN="env-token",
        SMARTBILL_LOOKUP_PATH="/fiscal-lookup",
        SMARTBILL_TIMEOUT_SECONDS="5",
    )

    cfg = auth_client.get("/api/v1/integrations/providers/smartbill/config")
    assert cfg.status_code == 200
    cfg_body = cfg.json()
    assert cfg_body["source"] == "env"
    assert cfg_body["token_present"] is True

    health = auth_client.get("/api/v1/integrations/providers/smartbill/health")
    assert health.status_code == 200
    health_body = health.json()
    assert health_body["source"] == "env"


@pytest.mark.asyncio
async def test_response_and_health_no_secret_leakage(auth_client, db_session):
    await _clear_app_settings_row(db_session)

    secret = "super-secret-token"
    auth_client.put(
        "/api/v1/integrations/providers/smartbill/config",
        json={
            "enabled": True,
            "base_url": "https://api.smartbill.test",
            "username": "office@firma.ro",
            "token": secret,
            "lookup_path": "/fiscal-lookup",
            "timeout_seconds": 5,
        },
    )

    cfg = auth_client.get("/api/v1/integrations/providers/smartbill/config")
    assert secret.lower() not in cfg.text.lower()

    health = auth_client.get("/api/v1/integrations/providers/smartbill/health")
    assert secret.lower() not in health.text.lower()
    assert "authorization" not in health.text.lower()


@pytest.mark.asyncio
async def test_config_endpoints_do_not_mutate_domain_tables(auth_client, db_session):
    await _clear_app_settings_row(db_session)

    before = await _count_mutation_tables(db_session)

    cfg_get = auth_client.get("/api/v1/integrations/providers/smartbill/config")
    assert cfg_get.status_code == 200

    cfg_put = auth_client.put(
        "/api/v1/integrations/providers/smartbill/config",
        json={
            "enabled": True,
            "base_url": "https://api.smartbill.test",
            "username": "office@firma.ro",
            "token": "token-one",
            "lookup_path": "/fiscal-lookup",
            "timeout_seconds": 5,
        },
    )
    assert cfg_put.status_code == 200

    cfg_test = auth_client.post("/api/v1/integrations/providers/smartbill/test-connection", json={})
    assert cfg_test.status_code == 200

    after = await _count_mutation_tables(db_session)
    assert before == after
