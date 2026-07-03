from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from services.anaf_client import AnafClient, AnafConfig, _normalize_found_entry


SAMPLE_ANAF_FOUND = {
    "date_generale": {
        "data": "2026-06-09",
        "cui": 14399840,
        "denumire": "EXAMPLE INTERNATIONAL SA",
        "adresa": "MUNICIPIUL BUCURESTI, SECTOR 2, STR. GARA HERESTRAU, NR.6",
        "telefon": "",
        "nrRegCom": "J2002000372404",
        "stare_inregistrare": "INREGISTRAT din data 29.08.2006",
        "statusRO_e_Factura": False,
    },
    "inregistrare_scop_Tva": {"scpTVA": True, "perioade_TVA": []},
    "stare_inactiv": {"statusInactivi": False},
    "inregistrare_RTVAI": {"statusTvaIncasare": False},
    "inregistrare_SplitTVA": {"statusSplitTVA": False},
    "adresa_domiciliu_fiscal": {
        "ddenumire_Localitate": "Sector 2 Mun. Bucuresti",
        "ddenumire_Strada": "Str. Gara Herestrau",
        "dnumar_Strada": "6",
        "ddenumire_Judet": "MUNICIPIUL BUCURESTI",
        "ddetalii_Adresa": "Cladirea Globalworth Square",
        "dcod_Postal": "",
    },
}


def test_normalize_found_entry_maps_core_fields():
    normalized, warnings = _normalize_found_entry(
        SAMPLE_ANAF_FOUND,
        tax_id="RO14399840",
        country="RO",
    )

    assert normalized["tax_id"] == "RO14399840"
    assert normalized["company_name"] == "EXAMPLE INTERNATIONAL SA"
    assert normalized["registration_number"] == "J2002000372404"
    assert normalized["city"] == "Sector 2 Mun. Bucuresti"
    assert normalized["county"] == "MUNICIPIUL BUCURESTI"
    assert normalized["vat_payer"] is True
    assert normalized["source"] == "anaf"
    assert "Str. Gara Herestrau" in (normalized["address"] or "")
    assert any("e-Factura" in warning for warning in warnings)


@pytest.mark.asyncio
async def test_anaf_client_lookup_found(monkeypatch):
    class _FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"found": [SAMPLE_ANAF_FOUND], "notFound": []}

    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args, **kwargs):
            return False

        async def post(self, *args, **kwargs):
            return _FakeResponse()

    monkeypatch.setattr("services.anaf_client.httpx.AsyncClient", _FakeAsyncClient)

    client = AnafClient(
        AnafConfig(
            enabled=True,
            tva_url="https://example.test/anaf",
            timeout_seconds=5,
            cache_ttl_seconds=0,
            rate_limit_seconds=0,
        )
    )
    result = await client.lookup_company(country="RO", tax_id="14399840")

    assert result.status == "found"
    assert result.normalized is not None
    assert result.normalized["company_name"] == "EXAMPLE INTERNATIONAL SA"


@pytest.mark.asyncio
async def test_anaf_client_lookup_not_found(monkeypatch):
    class _FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"found": [], "notFound": [99999999]}

    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args, **kwargs):
            return False

        async def post(self, *args, **kwargs):
            return _FakeResponse()

    monkeypatch.setattr("services.anaf_client.httpx.AsyncClient", _FakeAsyncClient)

    client = AnafClient(
        AnafConfig(
            enabled=True,
            tva_url="https://example.test/anaf",
            timeout_seconds=5,
            cache_ttl_seconds=0,
            rate_limit_seconds=0,
        )
    )
    result = await client.lookup_company(country="RO", tax_id="99999999")

    assert result.status == "not_found"
    assert result.normalized is None
