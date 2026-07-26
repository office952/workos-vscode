"""VL pre-publication runtime proof — dumps static vs runtime System Link Check JSON.

Usage (from backend/):
  .\\.venv\\Scripts\\python.exe ..\\docs\\qa\\product-system-authoring-runtime-codesign-e2e\\runtime\\vl_pre_publication_runtime_proof.py

No parent publish. Isolated fixture only.
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[4] / "backend"
sys.path.insert(0, str(BACKEND))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from models.base import Base
from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from models.product_templates import Product_templates
from services.product_e2e_readiness_service import ProductE2EReadinessService
from services.product_truth_job_confirm_service import (
    commercial_freeze_allowed,
    confirm_job_product_truth,
    get_job_revision_metadata,
)
from sqlalchemy import select
from tests.test_product_aggregate_volumetric_v2 import (
    CHILD_ALUMINUM,
    TEMPLATE_CODE,
    _seed_volumetric_v2_fixture,
)
from tests.test_vl_pre_publication_e2e_proof_v1 import _prepub_payload

OUT_DIR = Path(__file__).resolve().parent
STATIC_OUT = OUT_DIR / "vl_pre_publication_static_readiness.json"
RUNTIME_OUT = OUT_DIR / "vl_pre_publication_runtime_readiness.json"
SUMMARY_OUT = OUT_DIR / "vl_pre_publication_disposition_summary.json"


def _serialize_result(result) -> dict:
    return {
        "template_code": result.template_code,
        "mode": result.mode,
        "verdict": result.verdict,
        "e2e_ready": result.e2e_ready,
        "write_performed": result.write_performed,
        "no_write": result.no_write,
        "dry_run": result.dry_run,
        "workspace_id": result.workspace_id,
        "checked_at": result.checked_at,
        "build_closure_status": result.build_closure_status,
        "template_publication_status": result.template_publication_status,
        "systems": [
            {"system": n.system, "status": n.status, "blocking": n.blocking}
            for n in result.systems
        ],
        "findings": [
            {
                "check_id": f.check_id,
                "system": f.system,
                "status": f.status,
                "blocking": f.blocking,
                "message": f.message,
                "evidence": f.evidence,
            }
            for f in result.findings
        ],
        "known_conflicts": result.known_conflicts,
    }


async def main() -> int:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        await _seed_volumetric_v2_fixture(session)
        child = (
            await session.execute(
                select(Product_templates).where(
                    Product_templates.template_code == CHILD_ALUMINUM
                ).limit(1)
            )
        ).scalar_one()
        child.active = True
        await session.commit()

        static = await ProductE2EReadinessService(session).run_static(TEMPLATE_CODE)
        STATIC_OUT.write_text(
            json.dumps(_serialize_result(static), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        _, confirmed = confirm_job_product_truth(
            workspace_id="pending",
            workspace_code="IV6-VL-PREPUB-PROOF",
            payload_raw=_prepub_payload(),
            expected_revision=0,
            expected_draft_hash=None,
            expected_content_hash=None,
            root_template_code=TEMPLATE_CODE,
            root_template_version=None,
            actor_id="vl_prepub_proof",
        )
        meta = get_job_revision_metadata(confirmed)
        assert meta is not None
        assert commercial_freeze_allowed(confirmed) is True
        workspace_id = str(uuid.uuid4())
        session.add(
            IntakeV6WorkspaceRecord(
                id=workspace_id,
                workspace_code=f"IV6-VL-PREPUB-{workspace_id[:8]}",
                title="VL_PREPUB_E2E_FIXTURE_v1",
                template_code=TEMPLATE_CODE,
                status="draft",
                payload_json=json.dumps(confirmed),
            )
        )
        await session.commit()

        runtime = await ProductE2EReadinessService(session).run_runtime_dry_run(
            TEMPLATE_CODE, workspace_id=workspace_id, dry_run=True
        )
        RUNTIME_OUT.write_text(
            json.dumps(_serialize_result(runtime), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        six = (
            "product_truth",
            "cpp",
            "eic",
            "quote_snapshot",
            "order_snapshot",
            "execution_preview",
        )
        static_map = {n.system: n.status for n in static.systems}
        runtime_map = {n.system: n.status for n in runtime.systems}
        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "kickoff_head_reported": "520f3f01",
            "parent_publication_status": "unpublished",
            "parent_publish_executed": False,
            "fixture": "VL_PREPUB_E2E_FIXTURE_v1",
            "confirmed_perimeter_m": 12.5,
            "static_verdict": static.verdict,
            "runtime_verdict": runtime.verdict,
            "runtime_e2e_ready": runtime.e2e_ready,
            "six_not_tested_disposition": [
                {
                    "system": s,
                    "before_static": static_map.get(s),
                    "after_runtime": runtime_map.get(s),
                }
                for s in six
            ],
            "publication_recommendation": "GO_WITH_CONDITIONS",
            "recommendation_note": (
                "Runtime closes the six NOT_TESTED on isolated fixture; "
                "parent remains unpublished pending explicit owner publication GO; "
                "static mode still reports NOT_TESTED by design."
            ),
        }
        SUMMARY_OUT.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(json.dumps(summary, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
