"""TPL-ACM-BOXED-MOUNTING-SUPPORT_v1 — template seed and composition tests."""

from __future__ import annotations

import asyncio
import json

import pytest

from seeds.seed_tpl_acm_boxed_mounting_support_v1 import (
    ACM_COMPONENT_IDS,
    ACM_OPERATION_CODES,
    TEMPLATE_CODE,
    seed_tpl_acm_boxed_mounting_support_v1,
)
from services.mounting_solution_service import (
    ACM_BOXED_MOUNTING_TEMPLATE_CODE,
    ALLOWED_MOUNTING_SOLUTION_TEMPLATE_CODES,
    build_linked_module_input_from_solution,
    hydrate_mounting_solution_from_legacy,
    is_mounting_solution_composition_active,
    normalize_acm_mounting_configuration,
)
from services.product_aggregate_service import ProductAggregateService
from services.template_usage_mode_policy import (
    TPL_ACM_BOXED_MOUNTING_SUPPORT_V1,
    get_template_usage_mode_policy,
    is_root_offerable_template,
)


def test_template_usage_policy_root_offerable_and_linked_child() -> None:
    policy = get_template_usage_mode_policy(TPL_ACM_BOXED_MOUNTING_SUPPORT_V1)
    assert policy is not None
    assert policy.root_offerable is True
    assert policy.linked_child_allowed is True
    assert is_root_offerable_template(TEMPLATE_CODE) is True


def test_acm_in_allowed_mounting_solution_codes() -> None:
    assert ACM_BOXED_MOUNTING_TEMPLATE_CODE in ALLOWED_MOUNTING_SOLUTION_TEMPLATE_CODES
    assert "TPL-ACM-CASSETTED-PANEL" not in ALLOWED_MOUNTING_SOLUTION_TEMPLATE_CODES


def test_legacy_acm_panel_hydrates_canonical_solution() -> None:
    hydrated = hydrate_mounting_solution_from_legacy({"mounting_system": "acm_panel"})
    assert hydrated is not None
    assert hydrated["template_code"] == ACM_BOXED_MOUNTING_TEMPLATE_CODE
    assert hydrated["configuration"]["acm_thickness_mm"] == 3


def test_normalize_acm_configuration_merges_defaults() -> None:
    config = normalize_acm_mounting_configuration(
        {
            "panel_width_mm": 2000,
            "panel_height_mm": 1000,
            "return_depth_mm": 60,
            "fold_sides": "all",
        }
    )
    assert config["panel_width_mm"] == 2000
    assert config["acm_thickness_mm"] == 3
    assert config["fold_sides"] == "all"


def test_normalize_acm_configuration_preserves_four_mm_for_explicit_block() -> None:
    config = normalize_acm_mounting_configuration({"acm_thickness_mm": 4})
    assert config["acm_thickness_mm"] == 4


def test_build_linked_module_input_acm_branch() -> None:
    module_input = build_linked_module_input_from_solution(
        solution={
            "template_code": ACM_BOXED_MOUNTING_TEMPLATE_CODE,
            "configuration": {"panel_width_mm": 1200, "panel_height_mm": 800, "return_depth_mm": 60},
        },
        quote_input={"width_mm": 1200, "height_mm": 800},
        defaults={"quantity": 1},
    )
    assert module_input["panel_width_mm"] == 1200
    assert module_input["panel_area_m2"] == pytest.approx(0.96, rel=1e-3)
    assert module_input["fold_length_m"] == pytest.approx(4.0, rel=1e-3)


def test_preparation_only_with_acm_solution_is_active() -> None:
    setup = {
        "mounting_scope": "preparation_only",
        "mounting_solution": {
            "template_code": ACM_BOXED_MOUNTING_TEMPLATE_CODE,
            "configuration": normalize_acm_mounting_configuration({}),
        },
    }
    assert is_mounting_solution_composition_active(setup) is True


@pytest.fixture(scope="module")
def acm_boxed_mounting_seeded_db(db_fixture):
    from seeds.seed_build4_templates import seed_build4_templates
    from seeds.seed_tpl_volumetric_letters_dossier import seed_tpl_volumetric_letters_dossier
    from seeds.seed_tpl_volumetric_letters_v2 import seed_tpl_volumetric_letters_v2

    asyncio.get_event_loop().run_until_complete(seed_build4_templates())
    asyncio.get_event_loop().run_until_complete(seed_tpl_volumetric_letters_dossier())
    asyncio.get_event_loop().run_until_complete(seed_tpl_volumetric_letters_v2())
    asyncio.get_event_loop().run_until_complete(seed_tpl_acm_boxed_mounting_support_v1())
    return db_fixture


def test_seed_creates_active_template_with_components(acm_boxed_mounting_seeded_db) -> None:
    async def scenario():
        async with acm_boxed_mounting_seeded_db.session_maker() as session:
            stats = await seed_tpl_acm_boxed_mounting_support_v1()
            aggregate = await ProductAggregateService(session).build(TEMPLATE_CODE)
            return stats, aggregate

    stats, aggregate = asyncio.get_event_loop().run_until_complete(scenario())
    assert stats["template_action"] in {"created", "updated"}
    assert stats["active"] is True
    assert aggregate is not None
    assert aggregate.template_code == TEMPLATE_CODE
    assert len(aggregate.components) == len(ACM_COMPONENT_IDS)
    op_codes = {op.operation_code for op in aggregate.operations}
    for code in ACM_OPERATION_CODES:
        assert code in op_codes
