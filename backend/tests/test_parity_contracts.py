"""Parity contract foundation tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from parity.contracts import (
    PARITY_EVENT_CONTRACT_VERSION,
    PARITY_METRIC_CATALOG,
    PARITY_RESULT_CONTRACT_VERSION,
    ParityActorReference,
    ParityEntityReference,
    ParityEventV1,
    ParityResultContract,
    ParitySourceReference,
    ReconciliationSheetContract,
)
from parity.enums import (
    ComparisonResult,
    DiscrepancyStatus,
    ExplicitMappingClassification,
    ParityDomain,
    ParityEventType,
    ParityMetricName,
    ParitySeverity,
)


def _sample_result(**overrides) -> ParityResultContract:
    base = {
        "domain": ParityDomain.COMPETENCE,
        "entity_type": "employee",
        "entity_id": "4",
        "employee_id": 4,
        "canonical_source": "registry",
        "transitional_source": "legacy_json",
        "canonical_result": ["SK_PRINT_OPERATOR"],
        "transitional_result": ["SK_ASSEMBLY"],
        "comparison_result": ComparisonResult.VALUE_CONFLICT,
        "severity": ParitySeverity.HIGH,
        "status": DiscrepancyStatus.OPEN,
        "fingerprint": "parity_fp_v1:abc",
        "observed_at": datetime(2026, 7, 15, 9, 0, tzinfo=timezone.utc),
        "metadata": {"consumer_id": "employees_page"},
    }
    base.update(overrides)
    return ParityResultContract(**base)


def test_parity_result_requires_contract_version():
    with pytest.raises(ValidationError):
        ParityResultContract(
            contract_version="parity_result/v0",
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
            observed_at=datetime.now(timezone.utc),
        )


def test_parity_result_round_trip_json():
    result = _sample_result()
    payload = result.model_dump(mode="json")
    restored = ParityResultContract.model_validate(payload)
    assert restored.contract_version == PARITY_RESULT_CONTRACT_VERSION
    assert restored.domain == ParityDomain.COMPETENCE
    assert restored.metadata["consumer_id"] == "employees_page"


def test_parity_result_rejects_prohibited_metadata():
    with pytest.raises(ValidationError):
        _sample_result(metadata={"salary": 1000})


def test_parity_event_v1_from_result():
    result = _sample_result()
    event = ParityEventV1.from_parity_result(
        event_type=ParityEventType.COMPETENCE_PARITY_DIFFERENCE,
        result=result,
        actor=ParityActorReference(employee_id=4),
    )
    assert event.event_version == PARITY_EVENT_CONTRACT_VERSION
    assert event.entity == ParityEntityReference(
        entity_type="employee",
        entity_id="4",
        employee_id=4,
        operation_code=None,
        resource_id=None,
    )
    assert event.sources == ParitySourceReference(
        canonical_source="registry",
        transitional_source="legacy_json",
    )
    assert event.comparison_result == ComparisonResult.VALUE_CONFLICT


def test_metric_catalog_has_twenty_entries():
    assert len(PARITY_METRIC_CATALOG) == 20
    assert ParityMetricName.MAXIMUM_ACTIVE_SEVERITY in PARITY_METRIC_CATALOG


def test_reconciliation_sheet_contract_round_trip():
    sheet = ReconciliationSheetContract(
        employee_id=4,
        display_name="Employee Four",
        explicit_mappings=[
            {
                "operation_code": "assembly",
                "classification": ExplicitMappingClassification.ADAUGARE_FARA_COMPETENTA,
            }
        ],
        required_confirmations=["manager_ack"],
    )
    payload = sheet.model_dump(mode="json")
    restored = ReconciliationSheetContract.model_validate(payload)
    assert restored.employee_id == 4
    assert restored.explicit_mappings[0].classification == ExplicitMappingClassification.ADAUGARE_FARA_COMPETENTA


def test_all_enums_are_strings():
    assert ParityDomain.COMPETENCE == "competence"
    assert ComparisonResult.MATCH == "match"
    assert ParitySeverity.CRITICAL == "critical"
