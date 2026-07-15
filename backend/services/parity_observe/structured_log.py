"""Structured parity observation logging — dev/test only."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from parity.confidentiality import sanitize_safe_metadata
from parity.contracts import PARITY_EVENT_CONTRACT_VERSION
from parity.enums import ComparisonResult, ParityDomain, ParitySeverity

logger = logging.getLogger("workos.parity.observe")

_in_memory_observations: list[dict[str, Any]] = []


def reset_in_memory_observations() -> None:
    _in_memory_observations.clear()


def get_in_memory_observations() -> list[dict[str, Any]]:
    return list(_in_memory_observations)


def emit_parity_observation(
    *,
    event_type: str,
    domain: ParityDomain,
    comparison_result: ComparisonResult,
    severity: ParitySeverity,
    fingerprint: str,
    employee_id: int | None = None,
    operation_code: str | None = None,
    resource_id: str | None = None,
    canonical_source: str | None = None,
    transitional_source: str | None = None,
    consumer: str,
    projection_scope: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    payload = {
        "event_type": event_type,
        "contract_version": PARITY_EVENT_CONTRACT_VERSION,
        "fingerprint": fingerprint,
        "domain": domain.value,
        "severity": severity.value,
        "comparison_result": comparison_result.value,
        "employee_id": employee_id,
        "operation_code": operation_code,
        "resource_id": resource_id,
        "canonical_source": canonical_source,
        "transitional_source": transitional_source,
        "projection_scope": projection_scope,
        "consumer": consumer,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": sanitize_safe_metadata(metadata or {}),
    }
    _in_memory_observations.append(payload)
    logger.info("parity_observe %s", json.dumps(payload, ensure_ascii=True, sort_keys=True))
