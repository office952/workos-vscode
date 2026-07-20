"""Non-destructive proof: VL static readiness BLOCKED → publish hard-blocked.

Usage (from repo root):
  cd backend
  .\\.venv\\Scripts\\python.exe ..\\docs\\qa\\product-system-authoring-runtime-codesign-e2e\\runtime\\job_truth_publication_proof.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[4] / "backend"
sys.path.insert(0, str(BACKEND))

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.database import Base
import models  # noqa: F401
from models.product_templates import Product_templates
from schemas.product_template_publication import ProductTemplatePublicationTransitionRequest
from services.product_e2e_readiness_service import ProductE2EReadinessService
from services.product_template_publication_service import ProductTemplatePublicationService
from tests.test_product_aggregate_volumetric_v2 import (
    CHILD_ALUMINUM,
    TEMPLATE_CODE,
    _seed_volumetric_v2_fixture,
)


async def main() -> int:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with Session() as session:
        await _seed_volumetric_v2_fixture(session)
        child = (
            await session.execute(
                select(Product_templates).where(Product_templates.template_code == CHILD_ALUMINUM)
            )
        ).scalar_one()
        child.active = False
        await session.commit()

        readiness = await ProductE2EReadinessService(session).run_static(TEMPLATE_CODE)
        print(f"STATIC_VERDICT={readiness.verdict} e2e_ready={readiness.e2e_ready}")
        print(f"KNOWN_CONFLICTS={readiness.known_conflicts}")
        assert readiness.verdict == "BLOCKED"
        assert readiness.e2e_ready is False

        pub = ProductTemplatePublicationService(session)
        state = await pub.get_state(TEMPLATE_CODE)
        print(
            f"PUBLICATION_EFFECTIVE={state.effective_status} "
            f"active_is_not_published={state.active_is_not_published}"
        )
        assert state.active_is_not_published is True

        try:
            await pub.transition(
                TEMPLATE_CODE,
                ProductTemplatePublicationTransitionRequest(action="publish", actor="proof"),
            )
            print("PUBLISH=UNEXPECTED_OK")
            return 2
        except HTTPException as exc:
            print(f"PUBLISH_BLOCKED_STATUS={exc.status_code}")
            print(f"PUBLISH_BLOCKED_DETAIL={exc.detail}")
            assert exc.status_code == 409
            assert exc.detail["error"] == "publication_blocked_by_e2e_readiness"

        print("JOB_CONFIRM=covered_by_pytest_test_product_truth_job_confirm_v1")
        print("PROOF_OK")
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
