"""Small response normalizers for Intake V6 services that reuse V4 pure calculators."""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel

TModel = TypeVar("TModel", bound=BaseModel)

_STRING_REPLACEMENTS = (
    ("Intake V4", "Intake V6"),
    ("intake_v4", "intake_v6"),
    ("IntakeV4", "IntakeV6"),
    ("IV4-", "IV6-"),
    ("v4_", "v6_"),
)


def normalize_intake_v6_value(value: Any) -> Any:
    if isinstance(value, str):
        normalized = value
        for old, new in _STRING_REPLACEMENTS:
            normalized = normalized.replace(old, new)
        return normalized
    if isinstance(value, list):
        return [normalize_intake_v6_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(normalize_intake_v6_value(item) for item in value)
    if isinstance(value, dict):
        return {
            normalize_intake_v6_value(key): normalize_intake_v6_value(item)
            for key, item in value.items()
        }
    return value


def normalize_intake_v6_model(model: TModel) -> TModel:
    data = normalize_intake_v6_value(model.model_dump(mode="python"))
    return model.__class__.model_validate(data)
