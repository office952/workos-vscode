from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from sqlalchemy import delete, func, select

from models.clients import Clients
from models.integration_settings import Integration_settings
from models.intake_requests import Intake_requests
from models.orders import Orders
from models.quotes import Quotes


@dataclass
class _FakeLookupResult:
    status: str
    message: str
    normalized: dict | None = None
    warnings: list[str] = field(default_factory=list)


class _FakeSmartbillClient:
    def __init__(self, status: str):
        self.status = status

    async def lookup_company(self, *, country: str, tax_id: str):
        if self.status == "found":
            return _FakeLookupResult(
                status="found",
                message="Company found via SmartBill provider.",
                normalized={
                    "tax_id": tax_id,
                    "company_name": "Example SRL",
                    "registration_number": "J40/0000/2020",
                    "address": "Strada Exemplu 1",
                    "city": "Bucuresti",
                    "county": "Bucuresti",
                    "country": country,
                    "vat_payer": True,
                    "source": "smartbill",
                },
                warnings=[],
            )
        if self.status == "not_found":
            return _FakeLookupResult(status="not_found", message="Company not found for provided tax id.", warnings=[])
        if self.status == "provider_timeout":
            return _FakeLookupResult(status="provider_timeout", message="SmartBill request timed out.", warnings=["Provider timeout."])
        if self.status == "provider_error":
            return _FakeLookupResult(status="provider_error", message="SmartBill request failed.", warnings=["Provider error."])
        if self.status == "rate_limited":
            return _FakeLookupResult(status="rate_limited", message="SmartBill rate limit reached.", warnings=["Retry later."])
        return _FakeLookupResult(status="not_configured", message="SmartBill lookup is not configured in backend environment.")


def _fake_from_db_or_env(status: str):
    async def _factory(cls, db):
        return _FakeSmartbillClient(status)

    return classmethod(_factory)


def _count_mutation_tables(db_session):
    async def _run():
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

    return _run()


@pytest.fixture(autouse=True)
def _reset_smartbill_app_settings(db_fixture):
    async def _clear():
        async with db_fixture.session_maker() as session:
            await session.execute(delete(Integration_settings).where(Integration_settings.provider == "smartbill"))
            await session.commit()

    db_fixture.run(_clear())


def test_fiscal_lookup_requires_auth(unauth_client, monkeypatch):
    monkeypatch.setattr("dependencies.auth.dev_auth_allowed", lambda: False)
    resp = unauth_client.post(
        "/api/v1/intake-assist/fiscal-lookup",
        json={"provider": "smartbill", "country": "RO", "tax_id": "RO12345678"},
    )
    assert resp.status_code in (401, 403)


def test_fiscal_lookup_invalid_input(auth_client):
    resp = auth_client.post(
        "/api/v1/intake-assist/fiscal-lookup",
        json={"provider": "smartbill", "country": "RO", "tax_id": "INVALID"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "invalid_input"
    assert body["available"] is False
    assert body["normalized"] is None


@pytest.mark.asyncio
async def test_fiscal_lookup_configured_found_normalized(monkeypatch, auth_client):
    monkeypatch.setattr(
        "services.fiscal_lookup_service.SmartbillClient.from_db_or_env",
        _fake_from_db_or_env("found"),
    )

    resp = auth_client.post(
        "/api/v1/intake-assist/fiscal-lookup",
        json={"provider": "smartbill", "country": "RO", "tax_id": "12345678"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "smartbill"
    assert body["status"] == "found"
    assert body["available"] is True
    assert body["normalized"]["tax_id"] == "RO12345678"
    assert body["normalized"]["company_name"] == "Example SRL"
    assert body["requires_operator_confirmation"] is True
    serialized = str(body)
    assert "smartbill_token" not in serialized.lower()
    assert "smartbill_username" not in serialized.lower()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    ["not_found", "provider_timeout", "provider_error", "rate_limited"],
)
async def test_fiscal_lookup_provider_status_mapping(monkeypatch, auth_client, status):
    monkeypatch.setattr(
        "services.fiscal_lookup_service.SmartbillClient.from_db_or_env",
        _fake_from_db_or_env(status),
    )

    resp = auth_client.post(
        "/api/v1/intake-assist/fiscal-lookup",
        json={"provider": "smartbill", "country": "RO", "tax_id": "RO12345678"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == status
    assert body["available"] is False
    assert body["normalized"] is None
    assert body["requires_operator_confirmation"] is False


@pytest.mark.asyncio
async def test_fiscal_lookup_no_automatic_mutation(monkeypatch, auth_client, db_session):
    monkeypatch.setattr(
        "services.fiscal_lookup_service.SmartbillClient.from_db_or_env",
        _fake_from_db_or_env("found"),
    )

    before = await _count_mutation_tables(db_session)

    resp = auth_client.post(
        "/api/v1/intake-assist/fiscal-lookup",
        json={"provider": "smartbill", "country": "RO", "tax_id": "RO12345678"},
    )
    assert resp.status_code == 200

    after = await _count_mutation_tables(db_session)
    assert before == after
