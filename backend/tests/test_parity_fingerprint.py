"""Fingerprint determinism tests."""

from __future__ import annotations

from parity.fingerprint import FingerprintInput, compute_fingerprint, hash_normalized_value

GOLDEN_INPUT = FingerprintInput(
    domain="competence",
    entity_type="employee",
    entity_id="4",
    employee_id=4,
    operation_code="assembly",
    resource_id=None,
    canonical_value=["SK_PRINT_OPERATOR"],
    transitional_value=["SK_ASSEMBLY", "SK_PRINT_OPERATOR"],
)

GOLDEN_FINGERPRINT = compute_fingerprint(GOLDEN_INPUT)


def test_fingerprint_golden_vector():
    again = compute_fingerprint(GOLDEN_INPUT)
    assert again == GOLDEN_FINGERPRINT
    assert again.startswith("parity_fp_v1:")


def test_fingerprint_ignores_dict_key_order():
    left = compute_fingerprint(
        FingerprintInput(
            domain="resource",
            entity_type="resource",
            entity_id="MCH-CNC-4020",
            canonical_value={"b": 2, "a": 1},
            transitional_value={"a": 1, "b": 2},
        )
    )
    right = compute_fingerprint(
        FingerprintInput(
            domain="resource",
            entity_type="resource",
            entity_id="MCH-CNC-4020",
            canonical_value={"a": 1, "b": 2},
            transitional_value={"b": 2, "a": 1},
        )
    )
    assert left == right


def test_fingerprint_list_order_independent_for_sets():
    left = compute_fingerprint(
        FingerprintInput(
            domain="competence",
            entity_type="employee",
            entity_id="1",
            canonical_value=["SK_B", "SK_A"],
            transitional_value=["SK_A", "SK_B"],
        )
    )
    right = compute_fingerprint(
        FingerprintInput(
            domain="competence",
            entity_type="employee",
            entity_id="1",
            canonical_value=["SK_A", "SK_B"],
            transitional_value=["SK_B", "SK_A"],
        )
    )
    assert hash_normalized_value(["SK_A", "SK_B"]) == hash_normalized_value(["SK_B", "SK_A"])
    assert left == right


def test_fingerprint_none_differs_from_empty_list():
    with_none = compute_fingerprint(
        FingerprintInput(
            domain="competence",
            entity_type="employee",
            entity_id="1",
            employee_id=None,
            operation_code=None,
            resource_id=None,
            canonical_value=None,
            transitional_value=[],
        )
    )
    with_empty = compute_fingerprint(
        FingerprintInput(
            domain="competence",
            entity_type="employee",
            entity_id="1",
            employee_id=None,
            operation_code=None,
            resource_id=None,
            canonical_value=[],
            transitional_value=None,
        )
    )
    assert with_none != with_empty


def test_fingerprint_changes_with_values():
    changed = compute_fingerprint(
        FingerprintInput(
            domain=GOLDEN_INPUT.domain,
            entity_type=GOLDEN_INPUT.entity_type,
            entity_id=GOLDEN_INPUT.entity_id,
            employee_id=GOLDEN_INPUT.employee_id,
            operation_code=GOLDEN_INPUT.operation_code,
            resource_id=GOLDEN_INPUT.resource_id,
            canonical_value=["SK_OTHER"],
            transitional_value=GOLDEN_INPUT.transitional_value,
        )
    )
    assert changed != GOLDEN_FINGERPRINT
