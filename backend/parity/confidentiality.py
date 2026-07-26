"""Safe metadata validation for parity contracts."""

from __future__ import annotations

from typing import Any

PROHIBITED_METADATA_KEYS: frozenset[str] = frozenset(
    {
        "salary",
        "salariu",
        "internal_cost",
        "cost_intern",
        "contract",
        "contract_content",
        "private_notes",
        "note_private",
        "document_content",
        "raw_snapshot",
        "full_snapshot",
        "jwt",
        "token",
        "password",
        "secret",
        "api_key",
        "hr_payload",
        "full_hr_payload",
        "colleague_comparison",
        "coleg_comparison",
    }
)

ALLOWED_METADATA_KEYS: frozenset[str] = frozenset(
    {
        "consumer_id",
        "writer_id",
        "surface_id",
        "classification",
        "comparison_note",
        "domain_hint",
        "operation_family",
        "resource_code",
        "workcenter_code",
        "skill_code",
        "occurrence_count",
        "resolution_hint",
    }
)


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace("-", "_")


def _contains_prohibited_key(key: str) -> bool:
    normalized = _normalize_key(key)
    if normalized in PROHIBITED_METADATA_KEYS:
        return True
    for prohibited in PROHIBITED_METADATA_KEYS:
        if prohibited in normalized:
            return True
    return False


def _scrub_value(value: Any) -> Any:
    if isinstance(value, dict):
        return sanitize_safe_metadata(value)
    if isinstance(value, list):
        return [sanitize_safe_metadata(item) if isinstance(item, dict) else item for item in value]
    return value


def sanitize_safe_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    """Elimină chei interzise; păstrează doar chei permise sau non-prohibited simple."""
    if not metadata:
        return {}
    cleaned: dict[str, Any] = {}
    for raw_key, raw_value in metadata.items():
        key = _normalize_key(str(raw_key))
        if _contains_prohibited_key(key):
            continue
        if key in ALLOWED_METADATA_KEYS or not _contains_prohibited_key(key):
            cleaned[key] = _scrub_value(raw_value)
    return cleaned


def validate_safe_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    """Validează metadata — respinge payload-uri cu chei interzise."""
    if not metadata:
        return {}
    for raw_key in metadata.keys():
        if _contains_prohibited_key(str(raw_key)):
            raise ValueError(f"prohibited metadata key: {raw_key}")
        if isinstance(metadata[raw_key], dict):
            validate_safe_metadata(metadata[raw_key])
    return sanitize_safe_metadata(metadata)
