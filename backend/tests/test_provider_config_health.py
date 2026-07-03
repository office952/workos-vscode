from __future__ import annotations

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


@pytest.fixture(autouse=True)
def _reset_smartbill_app_settings(db_fixture):
    async def _clear():
        async with db_fixture.session_maker() as session:
            await session.execute(delete(Integration_settings).where(Integration_settings.provider == "smartbill"))
            await session.commit()

    db_fixture.run(_clear())


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


def test_provider_health_requires_auth(unauth_client):
    resp = unauth_client.get("/api/v1/integrations/providers/smartbill/health")
    assert resp.status_code in (401, 403)


def test_provider_health_disabled(monkeypatch, auth_client):
    _set_env(monkeypatch, SMARTBILL_ENABLED="false")

    resp = auth_client.get("/api/v1/integrations/providers/smartbill/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "disabled"
    assert body["configured"] is False
    assert body["enabled"] is False
    assert body["live_validation"]["performed"] is False


def test_provider_health_missing_token(monkeypatch, auth_client):
    _set_env(
        monkeypatch,
        SMARTBILL_ENABLED="true",
        SMARTBILL_BASE_URL="https://api.smartbill.test",
        SMARTBILL_USERNAME="billing@example.com",
        SMARTBILL_TIMEOUT_SECONDS="5",
        SMARTBILL_LOOKUP_PATH="/fiscal-lookup",
    )

    resp = auth_client.get("/api/v1/integrations/providers/smartbill/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "not_configured"
    assert body["configured"] is False
    assert "SMARTBILL_TOKEN" in body["missing_fields"]


def test_provider_health_complete_config(monkeypatch, auth_client):
    _set_env(
        monkeypatch,
        SMARTBILL_ENABLED="true",
        SMARTBILL_BASE_URL="https://api.smartbill.test",
        SMARTBILL_USERNAME="billing@example.com",
        SMARTBILL_TOKEN="super-secret-token",
        SMARTBILL_TIMEOUT_SECONDS="5",
        SMARTBILL_LOOKUP_PATH="/fiscal-lookup",
    )

    resp = auth_client.get("/api/v1/integrations/providers/smartbill/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "configured"
    assert body["configured"] is True
    assert body["masked"]["base_url_host"] == "api.smartbill.test"
    assert body["masked"]["username_hint"] is not None


def test_provider_health_invalid_timeout(monkeypatch, auth_client):
    _set_env(
        monkeypatch,
        SMARTBILL_ENABLED="true",
        SMARTBILL_BASE_URL="https://api.smartbill.test",
        SMARTBILL_USERNAME="billing@example.com",
        SMARTBILL_TOKEN="super-secret-token",
        SMARTBILL_TIMEOUT_SECONDS="0",
        SMARTBILL_LOOKUP_PATH="/fiscal-lookup",
    )

    resp = auth_client.get("/api/v1/integrations/providers/smartbill/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "invalid_config"


def test_provider_health_invalid_base_url(monkeypatch, auth_client):
    _set_env(
        monkeypatch,
        SMARTBILL_ENABLED="true",
        SMARTBILL_BASE_URL="smartbill-no-scheme",
        SMARTBILL_USERNAME="billing@example.com",
        SMARTBILL_TOKEN="super-secret-token",
        SMARTBILL_TIMEOUT_SECONDS="5",
        SMARTBILL_LOOKUP_PATH="/fiscal-lookup",
    )

    resp = auth_client.get("/api/v1/integrations/providers/smartbill/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "invalid_config"


def test_provider_health_no_secret_leakage(monkeypatch, auth_client):
    secret_token = "super-secret-token"
    _set_env(
        monkeypatch,
        SMARTBILL_ENABLED="true",
        SMARTBILL_BASE_URL="https://api.smartbill.test",
        SMARTBILL_USERNAME="billing@example.com",
        SMARTBILL_TOKEN=secret_token,
        SMARTBILL_TIMEOUT_SECONDS="5",
        SMARTBILL_LOOKUP_PATH="/fiscal-lookup",
    )

    resp = auth_client.get("/api/v1/integrations/providers/smartbill/health")
    assert resp.status_code == 200
    serialized = resp.text.lower()
    assert secret_token.lower() not in serialized
    assert "authorization" not in serialized


def test_provider_health_no_external_call(monkeypatch, auth_client):
    _set_env(monkeypatch, SMARTBILL_ENABLED="false")

    from services import smartbill_client

    def _forbidden_lookup(*args, **kwargs):
        raise AssertionError("health endpoint must not perform provider lookup")

    monkeypatch.setattr(smartbill_client.SmartbillClient, "lookup_company", _forbidden_lookup)

    resp = auth_client.get("/api/v1/integrations/providers/smartbill/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["live_validation"]["status"] == "not_run"


@pytest.mark.asyncio
async def test_provider_health_no_db_mutation(monkeypatch, auth_client, db_session):
    _set_env(monkeypatch, SMARTBILL_ENABLED="false")

    before = await _count_mutation_tables(db_session)
    resp = auth_client.get("/api/v1/integrations/providers/smartbill/health")
    assert resp.status_code == 200
    after = await _count_mutation_tables(db_session)
    assert before == after
