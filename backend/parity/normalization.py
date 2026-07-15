"""Deterministic value normalization for parity comparisons."""

from __future__ import annotations

import json
from typing import Any


def normalize_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text


def normalize_code(value: Any) -> str | None:
    text = normalize_optional_string(value)
    if text is None:
        return None
    return text.upper()


def normalize_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return bool(value)


def normalize_id(value: Any) -> int | str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value if value > 0 else None
    text = normalize_optional_string(value)
    if text is None:
        return None
    if text.isdigit():
        parsed = int(text)
        return parsed if parsed > 0 else None
    return text


def normalize_string_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        text = values.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                values = parsed
            else:
                return [text]
        except (TypeError, ValueError):
            return [text]
    if not isinstance(values, (list, tuple, set, frozenset)):
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for item in values:
        code = normalize_code(item) if isinstance(item, str) or item is not None else None
        if code and code not in seen:
            seen.add(code)
            normalized.append(code)
    return sorted(normalized)


def normalize_string_set(values: Any) -> frozenset[str]:
    return frozenset(normalize_string_list(values))


def normalize_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, Any] = {}
    for raw_key, raw_value in value.items():
        key = _normalize_dict_key(str(raw_key))
        normalized[key] = _normalize_dict_value(raw_value)
    return {key: normalized[key] for key in sorted(normalized.keys())}


def _normalize_dict_key(key: str) -> str:
    return key.strip().lower().replace("-", "_")


def _normalize_dict_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return normalize_dict(value)
    if isinstance(value, (list, tuple, set, frozenset)):
        if all(isinstance(item, (str, int, float, bool)) or item is None for item in value):
            return normalize_string_list(value)
        return [ _normalize_dict_value(item) for item in value ]
    return str(value).strip()


def normalize_for_comparison(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        return normalize_code(value)
    if isinstance(value, dict):
        return normalize_dict(value)
    if isinstance(value, (list, tuple, set, frozenset)):
        if not value:
            return []
        if all(isinstance(item, (str, int)) for item in value):
            return normalize_string_list(value)
        return normalize_dict({"items": list(value)})
    return normalize_optional_string(value)


def values_equal(canonical: Any, transitional: Any) -> bool:
    return normalize_for_comparison(canonical) == normalize_for_comparison(transitional)


def empty_normalized(value: Any) -> bool:
    normalized = normalize_for_comparison(value)
    if normalized is None:
        return True
    if normalized == []:
        return True
    if normalized == {}:
        return True
    return False
