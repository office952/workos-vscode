"""Template Lifecycle Control System V1 — inspector / readiness / validate."""

from __future__ import annotations

import pytest
import pytest_asyncio

from seeds.seed_tpl_acm_boxed_mounting_support_v1 import (
    TEMPLATE_CODE as ACM_CODE,
    seed_tpl_acm_boxed_mounting_support_v1,
)
from services.template_lifecycle_control_service import (
    ACTIVATION_REQUIRED_STAGES,
    TemplateLifecycleControlService,
    reverse_svg_bindable_map,
)

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

LETTERS = "TPL-VOLUMETRIC-LETTERS_v2"
LOGO = "TPL-VOLUMETRIC-LOGO_v1"


@pytest_asyncio.fixture
async def lifecycle_seeded_db(volumetric_v2_db):
    await seed_tpl_acm_boxed_mounting_support_v1()
    return volumetric_v2_db


@pytest.mark.asyncio
async def test_inspect_letters_has_standard_stages(lifecycle_seeded_db) -> None:
    svc = TemplateLifecycleControlService(lifecycle_seeded_db)
    result = await svc.inspect(LETTERS)
    readiness = result.readiness
    stage_codes = [s.stage for s in readiness.stages]
    assert readiness.template_code == LETTERS
    assert readiness.schema_version == "template_lifecycle_control_v1"
    for required in ACTIVATION_REQUIRED_STAGES:
        assert required in stage_codes
    assert readiness.readiness_score >= 0
    assert "product_templates" in readiness.derived_from
    # Must not invent a parallel registry authority
    assert all("parallel registry" not in e.lower() for e in readiness.derived_from)


@pytest.mark.asyncio
async def test_letters_detects_step1_and_support_wiring(lifecycle_seeded_db) -> None:
    svc = TemplateLifecycleControlService(lifecycle_seeded_db)
    readiness = await svc.build_readiness(LETTERS)
    by_stage = {s.stage: s for s in readiness.stages}
    assert by_stage["PRODUCT_TEMPLATE"].status == "PASS"
    assert by_stage["INTAKE_STEP_1"].status in {"WIRED", "PASS", "VALIDATED", "CONFIGURED"}
    assert by_stage["INTAKE_STEP_2"].status in {"WIRED", "PASS", "VALIDATED", "CONFIGURED"}
    assert by_stage["CPP"].status == "OWNER_GATE_REQUIRED"
    assert by_stage["TASK_MATERIALIZATION"].status == "OWNER_GATE_REQUIRED"
    assert any(g.code == "CPP_FORMULA_OWNER_GATE" for g in readiness.owner_gates)
    assert any(c.code == "STALE_BOND_CASETAT" for c in readiness.legacy_conflicts)


@pytest.mark.asyncio
async def test_second_template_acm_generic_inspect(lifecycle_seeded_db) -> None:
    svc = TemplateLifecycleControlService(lifecycle_seeded_db)
    readiness = await svc.build_readiness(ACM_CODE)
    assert readiness.template_code == ACM_CODE
    assert readiness.template_status in {"ACTIVE", "CANDIDATE"}
    assert len(readiness.stages) >= 15
    impact = await svc.build_impact(ACM_CODE)
    assert impact.template_code == ACM_CODE
    assert LETTERS in (impact.reverse_dependencies.get("product_templates_using_this") or []) or LETTERS in (
        impact.impact.affected_product_templates or []
    )


@pytest.mark.asyncio
async def test_logo_candidate_owner_gate_when_seeded(lifecycle_seeded_db) -> None:
    svc = TemplateLifecycleControlService(lifecycle_seeded_db)
    readiness = await svc.build_readiness(LOGO)
    if readiness.lifecycle_status == "BLOCKED" and any(
        b.code == "TEMPLATE_MISSING" for s in readiness.stages for b in s.blockers
    ):
        pytest.skip("Logo template not seeded in volumetric_v2 fixture")
    assert readiness.template_status in {"CANDIDATE", "ACTIVE"}
    assert any(
        g.code in {"CANDIDATE_ROOT_ACTIVATION", "CPP_FORMULA_OWNER_GATE"} for g in readiness.owner_gates
    )


@pytest.mark.asyncio
async def test_missing_template_blocked(lifecycle_seeded_db) -> None:
    svc = TemplateLifecycleControlService(lifecycle_seeded_db)
    readiness = await svc.build_readiness("TPL-DOES-NOT-EXIST_v9")
    assert readiness.lifecycle_status == "BLOCKED"
    assert any(b.code == "TEMPLATE_MISSING" for s in readiness.stages for b in s.blockers)


@pytest.mark.asyncio
async def test_validate_active_templates(lifecycle_seeded_db) -> None:
    svc = TemplateLifecycleControlService(lifecycle_seeded_db)
    result = await svc.validate(active_only=True)
    assert result.checked >= 1
    codes = {i.template_code for i in result.items}
    assert LETTERS in codes


def test_reverse_svg_bindable_map_includes_acm_parents() -> None:
    reverse = reverse_svg_bindable_map()
    assert ACM_CODE in reverse
    assert LETTERS in reverse[ACM_CODE]


@pytest.mark.asyncio
async def test_optional_inactive_support_does_not_require_active(lifecycle_seeded_db) -> None:
    """available != active: optional SUPPORT_CONTOUR must not force required blockers alone."""
    svc = TemplateLifecycleControlService(lifecycle_seeded_db)
    readiness = await svc.build_readiness(LETTERS)
    component_stage = next(s for s in readiness.stages if s.stage == "COMPONENT_TEMPLATES")
    assert component_stage.status != "BLOCKED" or not any(
        "optional" in b.message.lower() for b in component_stage.blockers
    )
