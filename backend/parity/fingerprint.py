"""Deterministic fingerprint generation for parity discrepancies."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from parity.normalization import normalize_code, normalize_for_comparison, normalize_id


FINGERPRINT_ALGORITHM = "sha256"
FINGERPRINT_PREFIX = "parity_fp_v1"


@dataclass(frozen=True)
class FingerprintInput:
    domain: str
    entity_type: str
    entity_id: str
    employee_id: int | str | None = None
    operation_code: str | None = None
    resource_id: str | None = None
    canonical_value: Any = None
    transitional_value: Any = None


def hash_normalized_value(value: Any) -> str:
    normalized = normalize_for_comparison(value)
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_fingerprint_payload(input_data: FingerprintInput) -> dict[str, Any]:
    return {
        "prefix": FINGERPRINT_PREFIX,
        "domain": normalize_code(input_data.domain),
        "entity_type": normalize_code(input_data.entity_type),
        "entity_id": str(normalize_id(input_data.entity_id) or input_data.entity_id or ""),
        "employee_id": normalize_id(input_data.employee_id),
        "operation_code": normalize_code(input_data.operation_code),
        "resource_id": normalize_code(input_data.resource_id),
        "canonical_value_hash": hash_normalized_value(input_data.canonical_value),
        "transitional_value_hash": hash_normalized_value(input_data.transitional_value),
    }


def compute_fingerprint(input_data: FingerprintInput) -> str:
    payload = build_fingerprint_payload(input_data)
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"{FINGERPRINT_PREFIX}:{digest}"


def is_same_discrepancy(left: str, right: str) -> bool:
    return left == right
