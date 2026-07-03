from __future__ import annotations

from typing import Any

from models.clients import Clients
from services.smartbill_client import normalize_tax_id

EMPTY_LOOKUP_MARKERS = {"—", "-", "n/a", "na"}


def normalized_tax_id_variants(tax_id: str) -> tuple[str | None, set[str]]:
    normalized = normalize_tax_id(tax_id, country="RO")
    if not normalized:
        return None, set()
    digits = "".join(ch for ch in normalized if ch.isdigit())
    variants = {normalized}
    if digits:
        variants.add(digits)
        variants.add(f"RO{digits}")
    return normalized, variants


def normalize_stored_client_cui(raw_cui: str | None) -> str | None:
    if raw_cui is None:
        return None
    return normalize_tax_id(str(raw_cui).strip(), country="RO")


def _clean_lookup_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.lower() in EMPTY_LOOKUP_MARKERS:
        return None
    return text


def build_client_create_payload_from_fiscal(*, normalized: dict[str, Any]) -> dict[str, Any]:
    tax_id = _clean_lookup_text(normalized.get("tax_id"))
    company_name = _clean_lookup_text(normalized.get("company_name"))
    if not tax_id:
        raise ValueError("Missing valid tax_id for client create.")
    if not company_name:
        raise ValueError("Missing company_name for client create.")

    payload: dict[str, Any] = {
        "name": company_name,
        "identity_type": "fiscal",
        "cui": tax_id,
    }
    address = _clean_lookup_text(normalized.get("address"))
    city = _clean_lookup_text(normalized.get("city"))
    if address:
        payload["address"] = address
    if city:
        payload["city"] = city
    return payload


def build_client_update_payload_from_fiscal(
    *,
    normalized: dict[str, Any],
    existing: Clients,
) -> dict[str, Any]:
    updates: dict[str, Any] = {}

    company_name = _clean_lookup_text(normalized.get("company_name"))
    if company_name:
        updates["name"] = company_name

    tax_id = _clean_lookup_text(normalized.get("tax_id"))
    if tax_id:
        updates["cui"] = tax_id

    if existing.identity_type != "fiscal":
        updates["identity_type"] = "fiscal"

    address = _clean_lookup_text(normalized.get("address"))
    if address:
        updates["address"] = address

    city = _clean_lookup_text(normalized.get("city"))
    if city:
        updates["city"] = city

    return updates


def classify_client_matches(matches: list[Clients]) -> str:
    if not matches:
        return "none"
    if len(matches) == 1:
        return "single"
    return "conflict"
