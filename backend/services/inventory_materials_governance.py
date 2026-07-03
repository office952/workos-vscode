from __future__ import annotations

import unicodedata
from typing import Any, Optional


CANONICAL_CATEGORIES: list[str] = [
    "Placi",
    "Profile metalice",
    "Parti electrice",
    "Folii",
    "Consumabile",
]

RECOMMENDED_SUBCATEGORIES: dict[str, list[str]] = {
    "Profile metalice": [
        "Otel / teava rectangulara",
        "Otel / teava rotunda",
        "Otel / cornier",
        "Otel / platbanda",
        "Aluminiu / profil litera volumetrica",
        "Aluminiu / profil caseta luminoasa",
        "Aluminiu / profil rama",
        "Aluminiu / profil sistem textil/banner",
    ],
    "Folii": ["Oracal 651", "Oracal 641", "Oracal 8500 translucent", "Printabil", "Laminare"],
    "Placi": ["ACM / Alucobond / Dibond", "Plexiglas", "Forex", "HIPS / alte placi"],
    "Parti electrice": ["LED modules", "surse alimentare", "cabluri / conectori"],
    "Consumabile": ["adezivi", "suruburi / prinderi", "distantieri / kit montaj", "consumabile generale"],
}

SOURCE_REVIEW_STATUSES: list[str] = ["missing", "needs_review", "reviewed", "stale", "accepted_override"]

INTELLIGENCE_POLICY: dict[str, Any] = {
    "canonical_categories": CANONICAL_CATEGORIES,
    "recommended_subcategories": RECOMMENDED_SUBCATEGORIES,
    "required_pricing_fields": ["unit", "unit_cost", "currency", "vat_percent", "valid_from"],
    "price_governed_fields": ["unit_cost", "currency", "vat_percent", "valid_from"],
    "source_review_policy": {
        "statuses": SOURCE_REVIEW_STATUSES,
        "accepted_override_requires_notes": True,
    },
    "product_system_gate_rules": {
        "requires_ready_for_pricing": True,
        "requires_active_status": True,
        "rejects_archived": True,
        "requires_category_normalized": True,
        "requires_unit": True,
        "requires_source_review_ok": True,
        "informational_only": True,
    },
    "stale_source_days": 90,
    "warnings": [
        "Material Registry unit_cost remains acquisition/production cost.",
        "Commercial markup policy is a separate layer.",
        "ProductSystem gate is informational and does not activate Product 001.",
    ],
    "category_policy": {
        "accepted": CANONICAL_CATEGORIES,
        "recommended_subcategories": RECOMMENDED_SUBCATEGORIES,
    },
    "source_review": {
        "stale_after_days": 90,
        "override_token": "source_review:accepted",
    },
    "productsystem_gate": {
        "informational_only": True,
        "activates_product_001": False,
        "connects_cost_engine": False,
    },
}


def normalize_category(value: Optional[str]) -> str:
    normalized = unicodedata.normalize("NFD", (value or "").lower())
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").strip()


def get_canonical_category(value: Optional[str]) -> Optional[str]:
    raw = (value or "").strip()
    if raw and raw in CANONICAL_CATEGORIES:
        return raw
    normalized = normalize_category(value)
    if not normalized:
        return None
    if any(token in normalized for token in ("plac", "acm", "dibond", "plexi", "forex")):
        return "Placi"
    if any(token in normalized for token in ("profil", "otel", "aluminiu", "teava", "cornier")):
        return "Profile metalice"
    if any(token in normalized for token in ("electric", "led", "aliment", "cablu", "conector")):
        return "Parti electrice"
    if any(token in normalized for token in ("folie", "oracal", "laminare", "print")):
        return "Folii"
    if any(token in normalized for token in ("consum", "adeziv", "surub", "prinder", "kit")):
        return "Consumabile"
    if normalized.startswith("dev_smoke_"):
        return "Consumabile"
    return None


def infer_recommended_subcategory(
    *,
    code: str,
    name: str,
    category: Optional[str],
    canonical_category: Optional[str],
) -> Optional[str]:
    hay = f"{code} {name} {category or ''}".lower()
    if not canonical_category:
        return None
    if canonical_category == "Folii":
        if "8500" in hay:
            return "Oracal 8500 translucent"
        if "651" in hay:
            return "Oracal 651"
        if "641" in hay:
            return "Oracal 641"
        if "lamin" in hay:
            return "Laminare"
        if "print" in hay:
            return "Printabil"
    if canonical_category == "Placi":
        if any(token in hay for token in ("acm", "dibond", "alucobond")):
            return "ACM / Alucobond / Dibond"
        if "plexi" in hay:
            return "Plexiglas"
        if "forex" in hay:
            return "Forex"
        if "hips" in hay:
            return "HIPS / alte placi"
    if canonical_category == "Profile metalice":
        if "rectang" in hay:
            return "Otel / teava rectangulara"
        if "rotund" in hay:
            return "Otel / teava rotunda"
        if "cornier" in hay:
            return "Otel / cornier"
        if "platband" in hay:
            return "Otel / platbanda"
        if "caseta" in hay:
            return "Aluminiu / profil caseta luminoasa"
        if "rama" in hay:
            return "Aluminiu / profil rama"
        if any(token in hay for token in ("textil", "banner")):
            return "Aluminiu / profil sistem textil/banner"
        if "litera" in hay:
            return "Aluminiu / profil litera volumetrica"
    if canonical_category == "Parti electrice":
        if "led" in hay:
            return "LED modules"
        if any(token in hay for token in ("sursa", "aliment")):
            return "surse alimentare"
        if any(token in hay for token in ("cablu", "conector")):
            return "cabluri / conectori"
    if canonical_category == "Consumabile":
        if "adeziv" in hay:
            return "adezivi"
        if any(token in hay for token in ("surub", "prinder")):
            return "suruburi / prinderi"
        if any(token in hay for token in ("distanti", "kit")):
            return "distantieri / kit montaj"
    return None