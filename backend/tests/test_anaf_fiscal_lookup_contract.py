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


class _FakeAnafClient:
    def __init__(self, status: str):
        self.status = status

    async def lookup_company(self, *, country: str, tax_id: str, query_date=None):
        if self.status == "found":
            return _FakeLookupResult(
                status="found",
                message="Company found via ANAF provider.",
                normalized={
                    "tax_id": tax_id,
                    "company_name": "Example ANAF SRL",
                    "registration_number": "J40/1111/2020",
                    "address": "Strada ANAF 1",
                    "city": "Bucuresti",
                    "county": "Bucuresti",
                    "country": country,
                    "vat_payer": True,
                    "source": "anaf",
                },
                warnings=["Contribuabilul nu apare in Registrul RO e-Factura la data interogarii."],
            )
        if self.status == "not_found":
            return _FakeLookupResult(status="not_found", message="Company not found for provided tax id.", warnings=[])
        if self.status == "provider_timeout":
            return _FakeLookupResult(status="provider_timeout", message="ANAF request timed out.", warnings=["Provider timeout."])
        return _FakeLookupResult(status="provider_error", message="ANAF request failed.", warnings=["Provider error."])


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
                    "company_name": "Example SmartBill SRL",
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
        return _FakeLookupResult(status="not_configured", message="SmartBill lookup is not configured in backend environment.")


def _fake_anaf_from_settings(status: str):
    def _factory():
        return _FakeAnafClient(status)

    return _factory


def _fake_smartbill_from_db_or_env(status: str):
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
        json={"provider": "anaf", "country": "RO", "tax_id": "RO12345678"},
    )
    assert resp.status_code in (401, 403)


def test_fiscal_lookup_invalid_input(auth_client):
    resp = auth_client.post(
        "/api/v1/intake-assist/fiscal-lookup",
        json={"provider": "anaf", "country": "RO", "tax_id": "INVALID"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "invalid_input"
    assert body["available"] is False
    assert body["normalized"] is None


@pytest.mark.asyncio
async def test_fiscal_lookup_anaf_found_normalized(monkeypatch, auth_client):
    monkeypatch.setattr(
        "services.fiscal_lookup_service.AnafClient.from_settings",
        _fake_anaf_from_settings("found"),
    )

    resp = auth_client.post(
        "/api/v1/intake-assist/fiscal-lookup",
        json={"provider": "anaf", "country": "RO", "tax_id": "12345678"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "anaf"
    assert body["status"] == "found"
    assert body["available"] is True
    assert body["normalized"]["tax_id"] == "RO12345678"
    assert body["normalized"]["company_name"] == "Example ANAF SRL"
    assert body["normalized"]["source"] == "anaf"
    assert body["requires_operator_confirmation"] is True
    assert body["warnings"]


@pytest.mark.asyncio
async def test_fiscal_lookup_auto_defaults_to_anaf(monkeypatch, auth_client):
    monkeypatch.setattr(
        "services.fiscal_lookup_service.AnafClient.from_settings",
        _fake_anaf_from_settings("found"),
    )

    resp = auth_client.post(
        "/api/v1/intake-assist/fiscal-lookup",
        json={"country": "RO", "tax_id": "12345678"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "anaf"
    assert body["status"] == "found"


@pytest.mark.asyncio
async def test_fiscal_lookup_auto_does_not_fallback_on_not_found(monkeypatch, auth_client):
    smartbill_called = {"value": False}

    class _TrackingSmartbillClient:
        async def lookup_company(self, *, country: str, tax_id: str):
            smartbill_called["value"] = True
            return _FakeLookupResult(
                status="found",
                message="Company found via SmartBill provider.",
                normalized={
                    "tax_id": tax_id,
                    "company_name": "Should Not Be Used SRL",
                    "registration_number": "J40/9999/2020",
                    "address": "Strada SmartBill 1",
                    "city": "Bucuresti",
                    "county": "Bucuresti",
                    "country": country,
                    "vat_payer": True,
                    "source": "smartbill",
                },
                warnings=[],
            )

    async def _tracking_factory(cls, db):
        return _TrackingSmartbillClient()

    monkeypatch.setattr(
        "services.fiscal_lookup_service.AnafClient.from_settings",
        _fake_anaf_from_settings("not_found"),
    )
    monkeypatch.setattr(
        "services.fiscal_lookup_service.SmartbillClient.from_db_or_env",
        classmethod(_tracking_factory),
    )

    resp = auth_client.post(
        "/api/v1/intake-assist/fiscal-lookup",
        json={"provider": "auto", "country": "RO", "tax_id": "12345678"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "anaf"
    assert body["status"] == "not_found"
    assert body["normalized"] is None
    assert smartbill_called["value"] is False


@pytest.mark.asyncio
async def test_fiscal_lookup_auto_keeps_anaf_found_with_vat_warnings(monkeypatch, auth_client):
    smartbill_called = {"value": False}

    class _TrackingSmartbillClient:
        async def lookup_company(self, *, country: str, tax_id: str):
            smartbill_called["value"] = True
            return _FakeLookupResult(status="found", message="unused", normalized=None, warnings=[])

    async def _tracking_factory(cls, db):
        return _TrackingSmartbillClient()

    monkeypatch.setattr(
        "services.fiscal_lookup_service.AnafClient.from_settings",
        _fake_anaf_from_settings("found"),
    )
    monkeypatch.setattr(
        "services.fiscal_lookup_service.SmartbillClient.from_db_or_env",
        classmethod(_tracking_factory),
    )

    resp = auth_client.post(
        "/api/v1/intake-assist/fiscal-lookup",
        json={"provider": "auto", "country": "RO", "tax_id": "12345678"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "anaf"
    assert body["status"] == "found"
    assert body["normalized"]["source"] == "anaf"
    assert body["warnings"]
    assert smartbill_called["value"] is False


@pytest.mark.asyncio
async def test_fiscal_lookup_auto_falls_back_to_smartbill(monkeypatch, auth_client):
    monkeypatch.setattr(
        "services.fiscal_lookup_service.AnafClient.from_settings",
        _fake_anaf_from_settings("provider_timeout"),
    )
    monkeypatch.setattr(
        "services.fiscal_lookup_service.SmartbillClient.from_db_or_env",
        _fake_smartbill_from_db_or_env("found"),
    )

    resp = auth_client.post(
        "/api/v1/intake-assist/fiscal-lookup",
        json={"provider": "auto", "country": "RO", "tax_id": "12345678"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "smartbill"
    assert body["status"] == "found"
    assert body["normalized"]["source"] == "smartbill"


@pytest.mark.asyncio
async def test_fiscal_lookup_smartbill_provider(monkeypatch, auth_client):
    monkeypatch.setattr(
        "services.fiscal_lookup_service.SmartbillClient.from_db_or_env",
        _fake_smartbill_from_db_or_env("found"),
    )

    resp = auth_client.post(
        "/api/v1/intake-assist/fiscal-lookup",
        json={"provider": "smartbill", "country": "RO", "tax_id": "12345678"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "smartbill"
    assert body["status"] == "found"
    assert body["normalized"]["source"] == "smartbill"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    ["not_found", "provider_timeout", "provider_error"],
)
async def test_fiscal_lookup_anaf_status_mapping(monkeypatch, auth_client, status):
    monkeypatch.setattr(
        "services.fiscal_lookup_service.AnafClient.from_settings",
        _fake_anaf_from_settings(status),
    )

    resp = auth_client.post(
        "/api/v1/intake-assist/fiscal-lookup",
        json={"provider": "anaf", "country": "RO", "tax_id": "RO12345678"},
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
        "services.fiscal_lookup_service.AnafClient.from_settings",
        _fake_anaf_from_settings("found"),
    )

    before = await _count_mutation_tables(db_session)

    resp = auth_client.post(
        "/api/v1/intake-assist/fiscal-lookup",
        json={"provider": "anaf", "country": "RO", "tax_id": "RO12345678"},
    )
    assert resp.status_code == 200

    after = await _count_mutation_tables(db_session)
    assert before == after
