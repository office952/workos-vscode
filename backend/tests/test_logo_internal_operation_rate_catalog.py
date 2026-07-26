"""Logo artwork internal operation rate catalog (print + laminate only)."""

from __future__ import annotations

import pytest

from data.internal_cost_rules_volumetric_v2 import (
    LOGO_ARTWORK_INTERNAL_OPERATION_RATE_BY_CODE,
    LOGO_ARTWORK_INTERNAL_OPERATION_RATES,
    VOLUMETRIC_V2_OPERATION_RULES,
)
from schemas.aggregate_cost_bom import CostBomCostableOperation
from services.estimated_internal_cost_service import _resolve_logo_operation_internal_rate
from services.template_architecture_scope import VOLUMETRIC_LOGO_TEMPLATE_CODE


def test_catalog_contains_print_and_laminate_once() -> None:
    codes = [rate.operation_code for rate in LOGO_ARTWORK_INTERNAL_OPERATION_RATES]
    assert codes.count("logo_face_print") == 1
    assert codes.count("logo_face_laminate") == 1


def test_catalog_rates_use_ron_m2_and_35() -> None:
    for rate in LOGO_ARTWORK_INTERNAL_OPERATION_RATES:
        assert rate.unit == "m2"
        assert rate.currency == "RON"
        assert rate.internal_unit_cost == pytest.approx(35.0)
        assert rate.status == "active"
        assert "commercial" not in rate.source
        assert "workcenter" not in rate.source


def test_application_rule_absent_from_logo_catalog() -> None:
    assert "logo_finish_application" not in LOGO_ARTWORK_INTERNAL_OPERATION_RATE_BY_CODE


def test_duplicate_operation_codes_rejected_at_import() -> None:
    assert len(LOGO_ARTWORK_INTERNAL_OPERATION_RATE_BY_CODE) == len(LOGO_ARTWORK_INTERNAL_OPERATION_RATES)


def test_letters_operation_rules_do_not_include_logo_codes() -> None:
    letter_codes = {rule.line_code for rule in VOLUMETRIC_V2_OPERATION_RULES}
    assert "logo_face_print" not in letter_codes
    assert "logo_face_laminate" not in letter_codes
    assert "logo_finish_application" not in letter_codes


def _canonical_finish_op(operation_code: str, instance: str = "logo_instance_001") -> CostBomCostableOperation:
    return CostBomCostableOperation(
        operation_code=operation_code,
        component_ref=f"comp_logo_finish::{instance}",
        source_template_code=VOLUMETRIC_LOGO_TEMPLATE_CODE,
        provenance="linked_module",
    )


def test_print_exact_code_resolves_to_35() -> None:
    rate, rule_code, source = _resolve_logo_operation_internal_rate(
        "logo_face_print",
        op=_canonical_finish_op("logo_face_print"),
    )
    assert rate == pytest.approx(35.0)
    assert rule_code == "INT_LOGO_FACE_PRINT_M2"
    assert "logo_face_print" in source


def test_laminate_exact_code_resolves_to_35() -> None:
    rate, rule_code, source = _resolve_logo_operation_internal_rate(
        "logo_face_laminate",
        op=_canonical_finish_op("logo_face_laminate"),
    )
    assert rate == pytest.approx(35.0)
    assert rule_code == "INT_LOGO_FACE_LAMINATE_M2"
    assert "logo_face_laminate" in source


def test_application_remains_unresolved() -> None:
    rate, rule_code, source = _resolve_logo_operation_internal_rate(
        "logo_finish_application",
        op=_canonical_finish_op("logo_finish_application"),
    )
    assert rate is None
    assert rule_code == "INT_LOGO_OP_RATE_MISSING"
    assert "missing" in source


def test_unknown_logo_op_remains_unresolved() -> None:
    rate, rule_code, _ = _resolve_logo_operation_internal_rate(
        "logo_face_cnc_cut",
        op=CostBomCostableOperation(
            operation_code="logo_face_cnc_cut",
            component_ref="comp_logo_face::logo_instance_001",
            source_template_code=VOLUMETRIC_LOGO_TEMPLATE_CODE,
            provenance="linked_module",
        ),
    )
    assert rate is None
    assert rule_code == "INT_LOGO_OP_RATE_MISSING"


def test_letters_rule_code_does_not_resolve_logo_print() -> None:
    rate, _, _ = _resolve_logo_operation_internal_rate("finisaje_ops")
    assert rate is None


def test_comp_logo_face_does_not_resolve_print_rate() -> None:
    rate, rule_code, source = _resolve_logo_operation_internal_rate(
        "logo_face_print",
        op=CostBomCostableOperation(
            operation_code="logo_face_print",
            component_ref="comp_logo_face::logo_instance_001",
            source_template_code=VOLUMETRIC_LOGO_TEMPLATE_CODE,
            provenance="linked_module",
        ),
    )
    assert rate is None
    assert rule_code == "INT_LOGO_OP_RATE_MISSING"
    assert "non_canonical" in source


def test_linked_segment_does_not_resolve_print_rate() -> None:
    rate, rule_code, source = _resolve_logo_operation_internal_rate(
        "logo_face_print",
        op=CostBomCostableOperation(
            operation_code="logo_face_print",
            component_ref="linked_segment::logo_instance_001",
            source_template_code=VOLUMETRIC_LOGO_TEMPLATE_CODE,
            provenance="dossier",
            status="mapping_only",
        ),
    )
    assert rate is None
    assert "non_canonical" in source


def test_mapping_only_finish_row_does_not_resolve_laminate_rate() -> None:
    rate, _, source = _resolve_logo_operation_internal_rate(
        "logo_face_laminate",
        op=CostBomCostableOperation(
            operation_code="logo_face_laminate",
            component_ref="comp_logo_finish::logo_instance_001",
            source_template_code=VOLUMETRIC_LOGO_TEMPLATE_CODE,
            provenance="dossier",
            status="mapping_only",
        ),
    )
    assert rate is None
    assert "non_canonical" in source


def test_neutral_instance_ids_preserved_in_canonical_resolution() -> None:
    for instance in ("logo_instance_001", "logo_instance_002"):
        rate, _, _ = _resolve_logo_operation_internal_rate(
            "logo_face_print",
            op=_canonical_finish_op("logo_face_print", instance),
        )
        assert rate == pytest.approx(35.0)
