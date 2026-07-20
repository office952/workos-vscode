"""Product E2E Readiness Check — static VL inactive child, NOT_TESTED != PASS, no writes."""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import select

from models.product_templates import Product_templates
from schemas.product_e2e_readiness import ProductE2EReadinessResult
from services.product_e2e_readiness_service import ProductE2EReadinessService
from services.product_truth_job_confirm_service import (
    assert_commercial_freeze_allowed,
    commercial_freeze_allowed,
)
from tests.test_product_aggregate_volumetric_v2 import (
    CHILD_ALUMINUM,
    TEMPLATE_CODE,
    _seed_volumetric_v2_fixture,
)


@pytest_asyncio.fixture
async def volumetric_v2_db(db_session):
    await _seed_volumetric_v2_fixture(db_session)
    return db_session


@pytest.mark.asyncio
async def test_static_vl_detects_inactive_required_child(volumetric_v2_db):
    session = volumetric_v2_db
    child = (
        await session.execute(
            select(Product_templates).where(Product_templates.template_code == CHILD_ALUMINUM).limit(1)
        )
    ).scalar_one()
    child.active = False
    await session.commit()

    service = ProductE2EReadinessService(session)
    result = await service.run_static(TEMPLATE_CODE)

    assert isinstance(result, ProductE2EReadinessResult)
    assert result.mode == "static"
    assert result.write_performed is False
    assert result.no_write is True
    assert result.verdict == "BLOCKED"
    assert result.e2e_ready is False

    inactive = [
        f
        for f in result.findings
        if f.component_template_code == CHILD_ALUMINUM
        and f.status == "BLOCKED"
        and f.evidence.get("conflict_code") == "required_inactive_child"
    ]
    assert inactive, "expected required inactive TPL-VOLUM-ALUMINIU_v1 finding"
    assert "required_inactive_child" in result.known_conflicts


@pytest.mark.asyncio
async def test_static_not_tested_is_never_pass(volumetric_v2_db):
    service = ProductE2EReadinessService(volumetric_v2_db)
    result = await service.run_static(TEMPLATE_CODE)

    not_tested = [f for f in result.findings if f.status == "NOT_TESTED"]
    assert not_tested, "static check must emit NOT_TESTED for unproven stages"

    for finding in not_tested:
        assert finding.status == "NOT_TESTED"
        assert finding.status != "PASS"

    for node in result.systems:
        system_findings = [f for f in result.findings if f.system == node.system]
        if system_findings and all(f.status == "NOT_TESTED" for f in system_findings):
            assert node.status == "NOT_TESTED"
            assert node.status != "PASS"

    assert result.e2e_ready is False
    assert result.verdict != "RUNTIME_READY"


@pytest.mark.asyncio
async def test_static_performs_no_writes(volumetric_v2_db):
    session = volumetric_v2_db
    before = (
        await session.execute(
            select(Product_templates).where(Product_templates.template_code == CHILD_ALUMINUM).limit(1)
        )
    ).scalar_one()
    before_active = before.active
    before_updated = before.updated_at

    service = ProductE2EReadinessService(session)
    result = await service.run_static(TEMPLATE_CODE)
    assert result.write_performed is False
    assert result.no_write is True

    after = (
        await session.execute(
            select(Product_templates).where(Product_templates.template_code == CHILD_ALUMINUM).limit(1)
        )
    ).scalar_one()
    assert after.active == before_active
    assert after.updated_at == before_updated


@pytest.mark.asyncio
async def test_runtime_dry_run_missing_workspace_blocks(volumetric_v2_db):
    service = ProductE2EReadinessService(volumetric_v2_db)
    result = await service.run_runtime_dry_run(
        TEMPLATE_CODE,
        workspace_id="ws-does-not-exist-readiness",
        dry_run=True,
    )
    assert result.write_performed is False
    assert result.no_write is True
    assert result.mode == "runtime_dry_run"
    assert result.e2e_ready is False
    assert result.verdict == "BLOCKED"
    assert any(
        f.evidence.get("conflict_code") == "no_confirmed_runtime_fixture" for f in result.findings
    )


def test_assert_commercial_freeze_allowed_helper():
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        assert_commercial_freeze_allowed({})
    assert exc.value.status_code == 422
    assert exc.value.detail["error"] == "product_truth_not_confirmed_or_stale"
    assert commercial_freeze_allowed({}) is False
