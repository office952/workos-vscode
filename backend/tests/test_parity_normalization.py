"""Normalization pure function tests."""

from __future__ import annotations

from parity.normalization import (
    normalize_code,
    normalize_dict,
    normalize_for_comparison,
    normalize_string_list,
    values_equal,
)


def test_normalize_string_list_sorts_and_dedupes():
    assert normalize_string_list([" sk_b ", "SK_A", "sk_a", "SK_B"]) == ["SK_A", "SK_B"]


def test_normalize_dict_key_order_independent():
    left = normalize_dict({"b": 1, "a": 2})
    right = normalize_dict({"a": 2, "b": 1})
    assert left == right


def test_normalize_code_uppercases():
    assert normalize_code("wc_cnc") == "WC_CNC"


def test_none_and_empty_list_not_auto_equal_without_rule():
    assert normalize_for_comparison(None) is None
    assert normalize_for_comparison([]) == []
    assert not values_equal(None, [])


def test_values_equal_for_duplicate_competence_order():
    assert values_equal(["SK_A", "SK_B"], ["SK_B", "SK_A"])
