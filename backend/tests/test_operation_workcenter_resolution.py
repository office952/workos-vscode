"""DEC-010 — ORR workcenter resolution (deterministic, fail-closed)."""

from __future__ import annotations

from schemas.product_aggregate import (
    ProductAggregate,
    ProductAggregateOperation,
    ProductAggregateTaskContract,
    ProductAggregateTaskRule,
)
from services.operation_workcenter_resolution_service import (
    apply_workcenter_resolution_to_aggregate,
    resolve_workcenter_for_operation,
)


def _mappings() -> list[dict]:
    return [
        {
            "operation_code": "prepress",
            "allowed_workcenter_codes": ["WC_PREPRESS"],
            "product_system_aliases": ["vector_prep", "file_prep"],
        },
        {
            "operation_code": "cnc_cutting",
            "allowed_workcenter_codes": ["WC_CNC_ROUTING"],
            "product_system_aliases": ["face_cnc_cut", "back_cut"],
        },
        {
            "operation_code": "montaj_led",
            "allowed_workcenter_codes": ["WC_LED_ASSEMBLY", "WC_ASSEMBLY"],
            "product_system_aliases": ["led_install_letters", "electrical_letters"],
        },
        {
            "operation_code": "file_preparation",
            "allowed_workcenter_codes": [],
            "product_system_aliases": [],
        },
        {
            "operation_code": "qc_letters",
            "allowed_workcenter_codes": ["WC_ASSEMBLY"],
            "product_system_aliases": [],
        },
    ]


def test_direct_and_alias_resolve_deterministically():
    m = _mappings()
    direct = resolve_workcenter_for_operation("qc_letters", m)
    assert direct.status == "resolved"
    assert direct.workcenter_code == "WC_ASSEMBLY"
    assert "operation_resource_requirements:direct" in (direct.mapping_source or "")

    alias = resolve_workcenter_for_operation("vector_prep", m)
    assert alias.status == "resolved"
    assert alias.workcenter_code == "WC_PREPRESS"
    assert alias.matched_alias == "vector_prep"
    assert "alias=vector_prep" in (alias.mapping_source or "")


def test_ambiguous_fail_closed():
    r = resolve_workcenter_for_operation("led_install_letters", _mappings())
    assert r.status == "ambiguous"
    assert r.workcenter_code is None
    assert r.warning and "WORKCENTER_MAPPING_AMBIGUOUS" in r.warning


def test_empty_allow_list_not_required():
    r = resolve_workcenter_for_operation("file_preparation", _mappings())
    assert r.status == "not_required"
    assert r.workcenter_code is None
    assert r.warning == "WORKCENTER_NOT_REQUIRED"


def test_source_missing_null():
    r = resolve_workcenter_for_operation("unknown_op_xyz", _mappings())
    assert r.status == "source_missing"
    assert r.workcenter_code is None


def test_inactive_machine_still_stamps_wc_with_warning():
    r = resolve_workcenter_for_operation(
        "qc_letters",
        _mappings(),
        active_workcenter_codes={"WC_OTHER"},
    )
    assert r.workcenter_code == "WC_ASSEMBLY"
    assert r.status == "resolved"
    assert r.warning == "WORKCENTER_NO_ACTIVE_MACHINE"


def test_no_label_substring_fallback():
    # Label-like strings must not invent WC.
    r = resolve_workcenter_for_operation("CNC Cutting Station", _mappings())
    assert r.status == "source_missing"
    assert r.workcenter_code is None


def test_aggregate_stamp_clears_legacy_template_wc_without_orr():
    agg = ProductAggregate(
        template_id=1,
        template_code="TPL-VOLUMETRIC-LETTERS",
        operations=[
            ProductAggregateOperation(
                operation_code="mystery_op",
                label="Mystery",
                workcenter="WC_GUESSED_FROM_TEMPLATE",
                priced=True,
            ),
            ProductAggregateOperation(
                operation_code="vector_prep",
                label="Vector",
                workcenter=None,
                priced=True,
            ),
        ],
        task_contract=ProductAggregateTaskContract(
            task_rules=[
                ProductAggregateTaskRule(
                    task_name="vector_prep",
                    task_type="process",
                    priced_operation="vector_prep",
                    sequence=1,
                )
            ]
        ),
    )
    stamped = apply_workcenter_resolution_to_aggregate(agg, _mappings())
    by = {op.operation_code: op for op in stamped.operations}
    assert by["mystery_op"].workcenter is None
    assert by["mystery_op"].workcenter_resolution_status == "source_missing"
    assert by["vector_prep"].workcenter == "WC_PREPRESS"
    assert by["vector_prep"].workcenter_resolution_status == "resolved"


def test_mapping_codes_unique_in_fixture_registry():
    codes = [m["operation_code"] for m in _mappings()]
    assert len(codes) == len(set(codes))
