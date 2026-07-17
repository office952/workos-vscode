"""Ownership + runtime decoupling contract tests."""

from __future__ import annotations

from data.offer_scope_canonical_map import (
    CANONICAL_TO_RUNTIME,
    SLICE1_DEFERRED_CANONICAL,
)
from services.letters_finish_mounting_ownership_contract import (
    MOUNTING_RUNTIME_MAP_UNCHANGED,
    OWNER_GATES_NOT_APPROVED,
    derive_metal_support_required_alias,
    diagnose_mounting_ownership_conflicts,
    ownership_contract_summary,
)
from services.letters_finish_mounting_runtime_decoupling import (
    LEGACY_FINISAJE_AGGREGATE_ALIAS,
    expand_legacy_finisaje_runtime_modules,
)


def test_sold_finish_mounting_remain_deferred():
    assert "FINISH" in SLICE1_DEFERRED_CANONICAL
    assert "MOUNTING" in SLICE1_DEFERRED_CANONICAL


def test_mounting_runtime_map_narrowed():
    assert CANONICAL_TO_RUNTIME["MOUNTING"] == MOUNTING_RUNTIME_MAP_UNCHANGED
    assert CANONICAL_TO_RUNTIME["MOUNTING"] == frozenset(
        {"structura_suport", "sablon_montaj"}
    )
    assert CANONICAL_TO_RUNTIME["FINISH"] == frozenset({"finisaje"})
    assert "finisaje" not in CANONICAL_TO_RUNTIME["MOUNTING"]
    assert "ambalare_livrare_montaj" not in CANONICAL_TO_RUNTIME["MOUNTING"]


def test_owner_gates_decoupling_approved_sold_blocked():
    summary = ownership_contract_summary()
    assert set(summary["owner_gates_not_approved"]) == OWNER_GATES_NOT_APPROVED
    assert "SOLD_CHIP_ACTIVATION_OWNER_GATE" in OWNER_GATES_NOT_APPROVED
    assert "MOUNTING_MAP_NARROWING_OWNER_GATE" not in OWNER_GATES_NOT_APPROVED
    assert "MINI_MODULE_SPLIT_OWNER_GATE" not in OWNER_GATES_NOT_APPROVED
    assert summary["behavioral_change"] is True
    assert summary["finisaje_module_removed"] is False
    assert summary["sold_finish_status"] == "DEFERRED"
    assert summary["sold_mounting_status"] == "DEFERRED"
    assert summary["sold_packaging"] == "NOT_PLANNED"


def test_legacy_finisaje_expand_is_read_path_only():
    expanded = expand_legacy_finisaje_runtime_modules({"finisaje"})
    assert expanded == LEGACY_FINISAJE_AGGREGATE_ALIAS
    assert "sablon_montaj" in expanded
    assert "ambalare_livrare_montaj" in expanded


def test_mounting_field_roles_canonical():
    fields = ownership_contract_summary()["mounting_fields"]
    assert fields["mounting_scope"] == "canonical_commercial_prep_intent"
    assert fields["mounting_system"] == "canonical_mounting_method_v1"
    assert fields["mounting_solution"] == "canonical_support_composition"
    assert fields["metal_support_required"] == "derived_compatibility_alias"
    assert fields["mounting_method"] == "target_future_name_only"


def test_derive_alias_from_canonical_only():
    assert derive_metal_support_required_alias(mounting_system="direct_wall") is False
    assert derive_metal_support_required_alias(mounting_system="steel_bars") is True
    assert (
        derive_metal_support_required_alias(
            mounting_system="direct_wall",
            mounting_solution={"kind": "product_system_template", "template_code": "TPL-X"},
        )
        is True
    )


def test_alias_contradiction_is_warning_not_rewrite():
    diags = diagnose_mounting_ownership_conflicts(
        mounting_system="direct_wall",
        mounting_solution=None,
        metal_support_required=True,
    )
    assert len(diags) == 1
    assert diags[0]["severity"] == "compatibility_warning"
    assert diags[0]["canonical_wins"] is True
    assert diags[0]["code"] == "MOUNTING_ALIAS_TRUE_WITHOUT_SUPPORT_INTENT"


def test_alias_false_with_bars_warns():
    diags = diagnose_mounting_ownership_conflicts(
        mounting_system="aluminum_bars",
        metal_support_required=False,
    )
    assert any(d["code"] == "MOUNTING_ALIAS_FALSE_WITH_SUPPORT_INTENT" for d in diags)
