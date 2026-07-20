"""Runtime/DB proof for ConfirmJobProductTruth + readiness (no destructive writes beyond confirm pin).

Usage (from backend/):
  .\\.venv\\Scripts\\python.exe ..\\docs\\audits\\_evidence\\2026-07-20_product-system-confirmed-job-truth-e2e\\runtime_proof.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

# .../docs/audits/_evidence/<dir>/runtime_proof.py → repo root is parents[4]
REPO = Path(__file__).resolve().parents[4]
BACKEND = REPO / "backend"
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from services.product_truth_job_confirm_service import (
    commercial_freeze_allowed,
    confirm_job_product_truth,
    draft_hash_for_payload,
    get_job_revision_metadata,
)
from services.product_e2e_readiness_service import ProductE2EReadinessService


async def main() -> int:
    db_path = BACKEND / "dev.db"
    url = f"sqlite+aiosqlite:///{db_path.as_posix()}"
    engine = create_async_engine(url)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        readiness = ProductE2EReadinessService(db)
        static = await readiness.run_static("TPL-VOLUMETRIC-LETTERS_v2")
        print("STATIC_VERDICT", static.verdict, "e2e_ready", static.e2e_ready)
        print("STATIC_CONFLICTS", static.known_conflicts[:8])

        result = await db.execute(
            select(IntakeV6WorkspaceRecord)
            .where(IntakeV6WorkspaceRecord.archived_at.is_(None))
            .order_by(IntakeV6WorkspaceRecord.updated_at.desc())
            .limit(40)
        )
        records = list(result.scalars().all())
        chosen = None
        for rec in records:
            try:
                payload = json.loads(rec.payload_json or "{}")
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
            letters = finish.get("letter_group_instances") or []
            acm = finish.get("acm_panel_instance")
            if letters or acm:
                chosen = (rec, payload)
                if letters and acm:
                    break

        if chosen is None:
            print("NO_FIXTURE", "no workspace with letter or acm bags")
            await engine.dispose()
            return 2

        rec, payload = chosen
        print("FIXTURE", rec.id, rec.workspace_code, rec.template_code)
        print(
            "BAGS",
            "letters",
            len(payload.get("finish_setup", {}).get("letter_group_instances") or []),
            "acm",
            bool(payload.get("finish_setup", {}).get("acm_panel_instance")),
        )

        meta = get_job_revision_metadata(payload)
        expected = int(meta["revision"]) if meta else 0
        draft_hash = draft_hash_for_payload(payload)
        # Dry confirm in-memory only (do not persist) — prove pin shape
        payload_copy = json.loads(json.dumps(payload))
        response, pinned_payload = confirm_job_product_truth(
            workspace_id=rec.id,
            workspace_code=rec.workspace_code,
            payload_raw=payload_copy,
            expected_revision=expected,
            expected_draft_hash=draft_hash,
            expected_content_hash=None,
            root_template_code=rec.template_code,
            root_template_version=None,
            actor_id="runtime-proof",
        )
        print("CONFIRM", json.dumps({
            "write_performed": response["write_performed"],
            "idempotent_noop": response["idempotent_noop"],
            "revision": response["metadata"]["revision"],
            "content_hash": response["metadata"]["content_hash"],
            "state": response["metadata"]["confirmation_state"],
            "freeze_allowed": commercial_freeze_allowed(pinned_payload),
        }, indent=2))

        # Idempotent second call
        response2, _ = confirm_job_product_truth(
            workspace_id=rec.id,
            workspace_code=rec.workspace_code,
            payload_raw=pinned_payload,
            expected_revision=response["metadata"]["revision"],
            expected_draft_hash=None,
            expected_content_hash=None,
            root_template_code=rec.template_code,
            root_template_version=None,
            actor_id="runtime-proof",
        )
        print("IDEMPOTENT", response2["idempotent_noop"], response2["write_performed"])

        # Note: intentionally NOT committing to live DB in this proof script
        # to avoid mutating owner fixtures without explicit GO. HTTP confirm
        # path is covered by tests + operator UI.
        print("PERSIST", "skipped_in_proof_script_no_destructive_db_write")

    await engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
