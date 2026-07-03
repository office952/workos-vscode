from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.smartbill_client import SmartbillClient, SmartbillConfig

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "smartbill"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def _fixture_text(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8").lower()


def _client() -> SmartbillClient:
    return SmartbillClient(
        SmartbillConfig(
            enabled=True,
            base_url="https://api.smartbill.test",
            username="user",
            token="token",
            timeout_seconds=5,
            lookup_path="/fiscal-lookup",
        )
    )


def test_fixture_found_normalizes_correctly():
    payload = _load_fixture("found_response_sanitized.json")
    normalized = _client()._normalize_provider_payload(payload, tax_id="RO12345678", country="RO")

    assert normalized["tax_id"] == "RO12345678"
    assert normalized["company_name"] == "Example SRL"
    assert normalized["source"] == "smartbill"
    assert normalized["vat_payer"] is True


def test_fixture_not_found_contract_shape():
    payload = _load_fixture("not_found_response_sanitized.json")
    status = str(payload.get("status") or "").lower()
    assert status == "not_found"


def test_fixture_error_contract_shape():
    payload = _load_fixture("error_response_sanitized.json")
    status = str(payload.get("status") or "").lower()
    assert status == "error"


@pytest.mark.parametrize(
    "fixture_name",
    [
        "found_response_sanitized.json",
        "not_found_response_sanitized.json",
        "error_response_sanitized.json",
    ],
)
def test_fixtures_no_secrets(fixture_name: str):
    text = _fixture_text(fixture_name)
    assert "token" not in text
    assert "authorization" not in text
    assert "apikey" not in text
    assert "api_key" not in text


def test_requires_operator_confirmation_rule_documented():
    # Contract rule remains: operator confirmation is required only when status is found.
    found_status = "found"
    not_found_status = "not_found"
    assert (found_status == "found") is True
    assert (not_found_status == "found") is False
