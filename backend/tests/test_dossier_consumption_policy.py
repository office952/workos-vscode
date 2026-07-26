from __future__ import annotations

import pytest

from models.product_blueprint_dossier import ProductBlueprintDossier
from services.dossier_consumption_policy import (
    DOSSIER_APPROVED_STATUS,
    DOSSIER_BEHAVIOR_FIELDS_AGGREGATE,
    evaluate_dossier_consumption,
)


def _dossier(
    *,
    status: str = "approved",
    template_code: str = "TPL-VOLUMETRIC-LETTERS_v2",
    dossier_id: int = 1,
) -> ProductBlueprintDossier:
    return ProductBlueprintDossier(
        id=dossier_id,
        template_id=10,
        template_code=template_code,
        dossier_version=1,
        status=status,
    )


def test_policy_allows_approved_matching_template() -> None:
    decision = evaluate_dossier_consumption(
        _dossier(),
        canonical_template_code="TPL-VOLUMETRIC-LETTERS_V2",
        consumer_surface="aggregate",
        behavior_bearing_fields=DOSSIER_BEHAVIOR_FIELDS_AGGREGATE,
    )
    assert decision.consume is True
    assert decision.reason == "approved_dossier_consumed"
    assert decision.dossier_status == DOSSIER_APPROVED_STATUS


@pytest.mark.parametrize("status", ["draft", "needs_review", "blocked", "deprecated"])
def test_policy_rejects_unapproved_status(status: str) -> None:
    decision = evaluate_dossier_consumption(
        _dossier(status=status),
        canonical_template_code="TPL-VOLUMETRIC-LETTERS_v2",
        consumer_surface="aggregate",
        behavior_bearing_fields=DOSSIER_BEHAVIOR_FIELDS_AGGREGATE,
    )
    assert decision.consume is False
    assert decision.reason == "dossier_not_approved"


def test_policy_rejects_template_identity_mismatch() -> None:
    decision = evaluate_dossier_consumption(
        _dossier(template_code="TPL-OTHER_v1"),
        canonical_template_code="TPL-VOLUMETRIC-LETTERS_v2",
        consumer_surface="intake_contract",
        behavior_bearing_fields=("variants_json",),
    )
    assert decision.consume is False
    assert decision.reason == "template_identity_mismatch"


def test_policy_missing_dossier_is_explicit() -> None:
    decision = evaluate_dossier_consumption(
        None,
        canonical_template_code="TPL-VOLUMETRIC-LETTERS_v2",
        consumer_surface="output_blocks",
        behavior_bearing_fields=("output_blocks_json",),
    )
    assert decision.consume is False
    assert decision.reason == "dossier_missing"
