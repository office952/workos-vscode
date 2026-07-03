from __future__ import annotations

import pytest
from sqlalchemy import delete, func, select

from models.clients import Clients
from services.client_fiscal_persistence import (
    build_client_create_payload_from_fiscal,
    build_client_update_payload_from_fiscal,
    classify_client_matches,
)
from services.clients import ClientsService
from services.client_fiscal_persistence import (
    build_client_create_payload_from_fiscal,
    build_client_update_payload_from_fiscal,
    classify_client_matches,
)
from services.clients import ClientsService


FISCAL_NORMALIZED = {
    "tax_id": "RO12345678",
    "company_name": "Example SRL",
    "registration_number": "J40/0000/2020",
    "address": "Strada Exemplu 1",
    "city": "Bucuresti",
    "county": "Bucuresti",
    "country": "RO",
    "vat_payer": True,
    "source": "anaf",
}


@pytest.fixture(autouse=True)
def _clear_clients(db_fixture):
    async def _run():
        async with db_fixture.session_maker() as session:
            await session.execute(delete(Clients))
            await session.commit()

    db_fixture.run(_run())


def test_build_create_payload_requires_name_and_tax_id():
    with pytest.raises(ValueError):
        build_client_create_payload_from_fiscal(normalized={"tax_id": "RO12345678", "company_name": ""})


def test_build_update_payload_does_not_overwrite_with_empty_values():
    existing = Clients(
        id=1,
        name="Existing SRL",
        identity_type="fiscal",
        cui="RO12345678",
        address="Adresa existenta",
        city="Cluj-Napoca",
    )
    updates = build_client_update_payload_from_fiscal(
        normalized={
            "tax_id": "RO12345678",
            "company_name": "Example SRL",
            "address": "",
            "city": "—",
        },
        existing=existing,
    )
    assert updates["name"] == "Example SRL"
    assert "address" not in updates
    assert "city" not in updates


def test_classify_client_matches():
    assert classify_client_matches([]) == "none"
    assert classify_client_matches([Clients(id=1, name="A", identity_type="fiscal")]) == "single"
    assert classify_client_matches(
        [
            Clients(id=1, name="A", identity_type="fiscal"),
            Clients(id=2, name="B", identity_type="fiscal"),
        ]
    ) == "conflict"


@pytest.mark.asyncio
async def test_find_by_normalized_tax_id_matches_variants(db_session):
    service = ClientsService(db_session)
    await service.create(
        {
            "name": "Variant Client SRL",
            "identity_type": "fiscal",
            "cui": "12345678",
            "address": "Strada 1",
            "city": "Bucuresti",
        }
    )

    matches = await service.find_by_normalized_tax_id("RO12345678")
    assert len(matches) == 1
    assert matches[0].name == "Variant Client SRL"


@pytest.mark.asyncio
async def test_create_client_after_fiscal_lookup_and_operator_confirmation(db_session):
    service = ClientsService(db_session)
    payload = build_client_create_payload_from_fiscal(normalized=FISCAL_NORMALIZED)
    created = await service.create(payload)

    assert created is not None
    assert created.name == "Example SRL"
    assert created.cui == "RO12345678"
    assert created.identity_type == "fiscal"


@pytest.mark.asyncio
async def test_update_existing_client_after_confirmation_without_empty_overwrite(db_session):
    service = ClientsService(db_session)
    existing = await service.create(
        {
            "name": "Existing SRL",
            "identity_type": "fiscal",
            "cui": "RO12345678",
            "address": "Adresa veche",
            "city": "Iasi",
        }
    )
    assert existing is not None

    updates = service.build_update_payload_from_fiscal(
        existing,
        {
            **FISCAL_NORMALIZED,
            "address": "",
            "city": "Bucuresti",
        },
    )
    updated = await service.update(existing.id, updates)
    assert updated is not None
    assert updated.name == "Example SRL"
    assert updated.address == "Adresa veche"
    assert updated.city == "Bucuresti"


@pytest.mark.asyncio
async def test_create_rejects_duplicate_cui(db_session):
    service = ClientsService(db_session)
    await service.create(build_client_create_payload_from_fiscal(normalized=FISCAL_NORMALIZED))

    with pytest.raises(ValueError, match="already exists"):
        await service.create(build_client_create_payload_from_fiscal(normalized=FISCAL_NORMALIZED))


@pytest.mark.asyncio
async def test_lookup_by_tax_id_reports_conflict(db_session):
    service = ClientsService(db_session)
    await service.create({"name": "Client A", "identity_type": "fiscal", "cui": "RO12345678"})
    db_session.add(Clients(name="Client B", identity_type="fiscal", cui="12345678"))
    await db_session.commit()

    matches = await service.find_by_normalized_tax_id("RO12345678")
    assert classify_client_matches(matches) == "conflict"


def test_lookup_by_tax_id_endpoint_none(auth_client):
    resp = auth_client.get("/api/v1/entities/clients/by-tax-id", params={"tax_id": "RO99999999"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "none"
    assert body["matches"] == []


def test_lookup_by_tax_id_endpoint_invalid(auth_client):
    resp = auth_client.get("/api/v1/entities/clients/by-tax-id", params={"tax_id": "INVALID"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "invalid_input"


@pytest.mark.asyncio
async def test_fiscal_lookup_does_not_auto_create_client(monkeypatch, auth_client, db_session):
    def _fake_anaf_from_settings():
        class _FakeAnafClient:
            async def lookup_company(self, *, country: str, tax_id: str, query_date=None):
                return type(
                    "Result",
                    (),
                    {
                        "status": "found",
                        "message": "Company found via ANAF provider.",
                        "normalized": {**FISCAL_NORMALIZED, "tax_id": tax_id},
                        "warnings": [],
                    },
                )()

        return _FakeAnafClient()

    monkeypatch.setattr("services.fiscal_lookup_service.AnafClient.from_settings", _fake_anaf_from_settings)

    before = await db_session.scalar(select(func.count(Clients.id)))

    resp = auth_client.post(
        "/api/v1/intake-assist/fiscal-lookup",
        json={"provider": "anaf", "country": "RO", "tax_id": "12345678"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "found"

    after = await db_session.scalar(select(func.count(Clients.id)))
    assert before == after
