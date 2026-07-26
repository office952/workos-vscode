"""CP-F proof: static BLOCKED (inactive aluminiu) + runtime dry_run no_write DB checksum.

Usage (from repo root):
  cd backend
  .\\.venv\\Scripts\\python.exe ..\\docs\\qa\\product-system-authoring-runtime-codesign-e2e\\runtime\\cp_f_readiness_no_write_proof.py

Writes evidence JSON beside this script. Never activates aluminiu. Never commits.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[4] / "backend"
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND))

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.database import Base
import models  # noqa: F401
from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from models.product_template_module_links import ProductTemplateModuleLink
from models.product_templates import Product_templates
from services.product_e2e_readiness_service import ProductE2EReadinessService
from tests.test_product_aggregate_volumetric_v2 import (
    CHILD_ALUMINUM,
    TEMPLATE_CODE,
    _seed_volumetric_v2_fixture,
)

TABLES = (
    "product_templates",
    "product_template_module_links",
    "intake_v6_workspaces",
)


async def _row_counts(session: AsyncSession) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in TABLES:
        try:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            counts[table] = int(result.scalar_one())
        except Exception:
            counts[table] = -1
    return counts


async def _fingerprint(session: AsyncSession) -> str:
    """Deterministic content fingerprint of key catalog + workspace rows."""
    parts: list[str] = []

    tpl_rows = (
        await session.execute(
            select(
                Product_templates.template_code,
                Product_templates.active,
                Product_templates.publication_status,
                Product_templates.updated_at,
            ).order_by(Product_templates.template_code)
        )
    ).all()
    for row in tpl_rows:
        parts.append(f"tpl|{row[0]}|{row[1]}|{row[2]}|{row[3]}")

    link_rows = (
        await session.execute(
            select(
                ProductTemplateModuleLink.parent_template_code,
                ProductTemplateModuleLink.module_template_code,
                ProductTemplateModuleLink.active,
                ProductTemplateModuleLink.relation_type,
            ).order_by(
                ProductTemplateModuleLink.parent_template_code,
                ProductTemplateModuleLink.module_template_code,
            )
        )
    ).all()
    for row in link_rows:
        parts.append(f"link|{row[0]}|{row[1]}|{row[2]}|{row[3]}")

    ws_count = (
        await session.execute(select(func.count()).select_from(IntakeV6WorkspaceRecord))
    ).scalar_one()
    parts.append(f"ws_count|{int(ws_count)}")

    payload = "\n".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


async def _snapshot(session: AsyncSession, label: str) -> dict:
    return {
        "label": label,
        "at": datetime.now(timezone.utc).isoformat(),
        "row_counts": await _row_counts(session),
        "sha256": await _fingerprint(session),
    }


async def main() -> int:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    evidence: dict = {
        "proof": "cp_f_readiness_no_write",
        "template_code": TEMPLATE_CODE,
        "child_inactive": CHILD_ALUMINUM,
        "aluminiu_activated": False,
    }

    async with Session() as session:
        await _seed_volumetric_v2_fixture(session)
        child = (
            await session.execute(
                select(Product_templates).where(Product_templates.template_code == CHILD_ALUMINUM)
            )
        ).scalar_one()
        child.active = False
        await session.commit()

        before = await _snapshot(session, "before_static_and_runtime")
        evidence["db_before"] = before

        readiness = ProductE2EReadinessService(session)
        static = await readiness.run_static(TEMPLATE_CODE)
        runtime = await readiness.run_runtime_dry_run(
            TEMPLATE_CODE,
            workspace_id="ws-cp-f-missing-fixture",
            dry_run=True,
        )

        after = await _snapshot(session, "after_static_and_runtime")
        evidence["db_after"] = after

        evidence["static"] = {
            "verdict": static.verdict,
            "e2e_ready": static.e2e_ready,
            "no_write": static.no_write,
            "write_performed": static.write_performed,
            "build_closure_status": static.build_closure_status,
            "template_publication_status": static.template_publication_status,
            "known_conflicts": static.known_conflicts,
        }
        evidence["runtime_dry_run"] = {
            "verdict": runtime.verdict,
            "e2e_ready": runtime.e2e_ready,
            "no_write": runtime.no_write,
            "write_performed": runtime.write_performed,
            "build_closure_status": runtime.build_closure_status,
            "template_publication_status": runtime.template_publication_status,
            "workspace_id": runtime.workspace_id,
        }

        assert static.verdict == "BLOCKED", static.verdict
        assert static.template_publication_status == "BLOCKED"
        assert static.build_closure_status in ("PASS", "PASS_WITH_WARNINGS")
        assert static.no_write is True and static.write_performed is False
        assert runtime.no_write is True and runtime.write_performed is False
        assert before["sha256"] == after["sha256"], (before, after)
        assert before["row_counts"] == after["row_counts"], (before, after)

        evidence["build_pass_while_template_publication_blocked"] = True
        evidence["db_unchanged"] = True
        evidence["PROOF_OK"] = True

    out = EVIDENCE_DIR / "cp_f_readiness_no_write_evidence.json"
    out.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"STATIC_VERDICT={evidence['static']['verdict']}")
    print(f"BUILD_CLOSURE={evidence['static']['build_closure_status']}")
    print(f"TEMPLATE_PUBLICATION={evidence['static']['template_publication_status']}")
    print(f"DB_BEFORE_SHA={before['sha256']}")
    print(f"DB_AFTER_SHA={after['sha256']}")
    print(f"DB_BEFORE_COUNTS={before['row_counts']}")
    print(f"DB_AFTER_COUNTS={after['row_counts']}")
    print(f"EVIDENCE={out}")
    print("PROOF_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
