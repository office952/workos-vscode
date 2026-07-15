"""Confidentiality metadata tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from parity.confidentiality import sanitize_safe_metadata, validate_safe_metadata
from parity.contracts import ParityResultContract
from parity.enums import ComparisonResult, DiscrepancyStatus, ParityDomain, ParitySeverity


def test_allowed_metadata_passes():
    metadata = validate_safe_metadata({"consumer_id": "mobile_available", "classification": "test"})
    assert metadata["consumer_id"] == "mobile_available"


def test_prohibited_top_level_key_rejected():
    with pytest.raises(ValueError):
        validate_safe_metadata({"salary": 1000})


def test_nested_prohibited_key_rejected():
    with pytest.raises(ValueError):
        validate_safe_metadata({"details": {"jwt": "secret-token"}})


def test_sanitize_removes_prohibited_keys():
    cleaned = sanitize_safe_metadata(
        {
            "consumer_id": "shop_floor",
            "private_notes": "hidden",
            "raw_snapshot": {"tasks": [1, 2, 3]},
        }
    )
    assert cleaned == {"consumer_id": "shop_floor"}


def test_contract_rejects_secret_metadata():
    with pytest.raises(ValidationError):
        ParityResultContract(
            domain=ParityDomain.COMPETENCE,
            entity_type="employee",
            entity_id="1",
            canonical_source="a",
            transitional_source="b",
            canonical_result=[],
            transitional_result=[],
            comparison_result=ComparisonResult.MATCH,
            severity=ParitySeverity.INFORMATIONAL,
            fingerprint="fp",
            observed_at="2026-07-15T09:00:00Z",
            metadata={"password": "x"},
        )
