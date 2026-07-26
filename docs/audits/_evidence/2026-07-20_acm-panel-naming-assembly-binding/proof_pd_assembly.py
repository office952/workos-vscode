"""Readonly PD proof for IV6-DB2F86B7 assembly_* + ACM-root cross-template parity."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[4] / "backend"
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")
os.environ.setdefault("JWT_SECRET_KEY", "local-dev-secret-not-for-production")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from services.product_definition_builder_service import ProductDefinitionBuilderService

WS_ID = "a7b0162b-dc91-467f-aa24-c1279fb3a073"
WS_CODE = "IV6-DB2F86B7"
ACM = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"
LETTERS = "TPL-VOLUMETRIC-LETTERS_v2"
OUT = Path(__file__).resolve().parent / "pd-assembly-proof.json"


async def main() -> None:
    engine = create_async_engine(os.environ["DATABASE_URL"], future=True)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as db:
        r = await db.execute(select(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == WS_ID).limit(1))
        rec = r.scalar_one_or_none()
        if rec is None:
            r2 = await db.execute(
                select(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.workspace_code == WS_CODE).limit(1)
            )
            rec = r2.scalar_one_or_none()
        if rec is None:
            OUT.write_text(json.dumps({"ok": False, "error": "workspace_not_found"}, indent=2), encoding="utf-8")
            print("FAIL workspace_not_found")
            return

        svc = ProductDefinitionBuilderService(db)
        letters = await svc.build_preview(LETTERS, workspace_id=rec.id)
        acm = await svc.build_preview(ACM, workspace_id=rec.id)

        def pack(p):
            if p is None:
                return None
            v = p.canonical_values or {}
            prov = {e.key: e.detail for e in p.provenance}
            return {
                "source_payload_type": p.source_context.source_payload_type,
                "assembly_width_mm": v.get("assembly_width_mm"),
                "assembly_height_mm": v.get("assembly_height_mm"),
                "assembly_extent_source": v.get("assembly_extent_source"),
                "envelope_ignored": v.get("assembly_extent_envelope_ignored"),
                "acm_instance_id": (v.get("acm_panel_instance") or {}).get("component_instance_id"),
                "tech": v.get("acm_panel_technical_configuration_status"),
                "composition": v.get("acm_panel_composition_status"),
                "seg_proposal": (v.get("segmented_background_proposal") or {}).get("status"),
                "panel_width_mm": v.get("panel_width_mm"),
                "linked_workspace_template_code": prov.get("linked_workspace_template_code"),
                "read_mode": prov.get("read_mode"),
            }

        letters_p = pack(letters)
        acm_p = pack(acm)
        ok = (
            letters_p is not None
            and acm_p is not None
            and letters_p["assembly_width_mm"] == 2000
            and letters_p["assembly_height_mm"] == 350
            and acm_p["assembly_width_mm"] == 2000
            and acm_p["assembly_height_mm"] == 350
            and acm_p["source_payload_type"] == "workspace_payload"
            and acm_p["read_mode"] == "cross_template_acm_parity"
            and acm_p["linked_workspace_template_code"] == rec.template_code
            and letters_p.get("panel_width_mm") != 2000
        )
        payload = {
            "ok": ok,
            "workspace": {"id": rec.id, "code": rec.workspace_code, "template": rec.template_code},
            "letters": letters_p,
            "acm_root": acm_p,
        }
        OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print("PASS" if ok else "FAIL")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
