"""CP-A live proof: HTTP confirm → DB persist → reload (real sqlite, not memory).

Creates a disposable workspace on live dev.db, confirms via ASGI HTTP,
re-reads via new DB session + job-status route. Does not activate aluminiu.

Usage (from backend/):
  $env:DATABASE_URL='sqlite+aiosqlite:///C:/w/psiso/backend/dev.db'
  $env:JWT_SECRET_KEY='local-dev-secret-not-for-production'
  $env:APP_ENV='development'; $env:ENVIRONMENT='development'
  .\\.venv\\Scripts\\python.exe ..\\docs\\qa\\product-system-authoring-runtime-codesign-e2e\\runtime\\cp_a_live_http_db_confirm_proof.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[4] / "backend"
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///C:/w/psiso/backend/dev.db")
os.environ.setdefault("JWT_SECRET_KEY", "local-dev-secret-not-for-production")

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from dependencies.auth import get_current_user
from main import app
from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from schemas.auth import UserResponse

OUT = Path(__file__).resolve().parent / "cp_a_live_http_db_confirm_evidence.json"
DISPOSABLE_CODE = f"IV6-CLOSURE-{uuid.uuid4().hex[:8].upper()}"
# Real VL fixture used as payload shape donor (bags injected for confirm).
SOURCE_WORKSPACE_ID = "528598d4-f4da-45c2-94db-f9ac1fbeb15b"


def _clone_payload_with_bags(source: dict) -> dict:
    payload = json.loads(json.dumps(source))
    fs = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
    fs = dict(fs)
    fs["letter_group_instances"] = [
        {
            "schema": "volumetric_letter_group_instance_v1",
            "instance_id": "11111111-1111-1111-1111-111111111111",
            "group_key": "pseudo:closure",
            "confirmed": True,
        }
    ]
    fs["component_placements"] = [
        {
            "schema": "component_placement_v1",
            "placement_id": "pl-closure-1",
            "source_instance_id": "11111111-1111-1111-1111-111111111111",
            "target_kind": "acm_panel",
            "target_instance_id": "acm-closure-1",
        }
    ]
    fs["acm_panel_instance"] = {
        "schema": "acm_panel_component_instance_v1",
        "component_instance_id": "acm-closure-1",
        "component_template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
        "association_status": "confirmed",
    }
    payload["finish_setup"] = fs
    # Drop any prior confirmed snapshot so first confirm is clean.
    pt = payload.get("product_truth") if isinstance(payload.get("product_truth"), dict) else {}
    pt = dict(pt)
    pt.pop("confirmed_snapshot_v1", None)
    payload["product_truth"] = pt
    return payload


def _parse_payload(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        return json.loads(raw)
    return {}


async def _override_user():
    return UserResponse(
        id="closure-proof-user",
        email="closure@local",
        name="Closure Proof",
        role="admin",
    )


async def main() -> int:
    db_url = os.environ["DATABASE_URL"]
    engine = create_async_engine(db_url)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    evidence: dict = {
        "db_url": db_url,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "workspace_code": DISPOSABLE_CODE,
    }
    wid = str(uuid.uuid4())

    async with Session() as session:
        donor = (
            await session.execute(
                select(IntakeV6WorkspaceRecord).where(
                    IntakeV6WorkspaceRecord.id == SOURCE_WORKSPACE_ID
                )
            )
        ).scalar_one()
        donor_payload = _parse_payload(donor.payload_json)
        cloned = _clone_payload_with_bags(donor_payload)
        evidence["source_workspace_id"] = SOURCE_WORKSPACE_ID
        session.add(
            IntakeV6WorkspaceRecord(
                id=wid,
                workspace_code=DISPOSABLE_CODE,
                title="CLOSURE CP-A disposable",
                template_code="TPL-VOLUMETRIC-LETTERS_v2",
                status="draft",
                payload_json=json.dumps(cloned),
                readiness_status="not_ready",
            )
        )
        await session.commit()
        evidence["workspace_id"] = wid
        evidence["insert_ok"] = True

    app.dependency_overrides[get_current_user] = _override_user
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r1 = await client.post(
                f"/api/v1/intake-v6/workspaces/{wid}/product-truth/confirm-job",
                json={
                    "expected_revision": 0,
                    "root_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
                },
            )
            evidence["confirm_1_status"] = r1.status_code
            evidence["confirm_1_body"] = (
                r1.json()
                if "application/json" in (r1.headers.get("content-type") or "")
                else r1.text
            )
            if r1.status_code != 200:
                OUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
                print("CONFIRM_1_FAIL", r1.status_code, evidence["confirm_1_body"])
                return 2

            body1 = r1.json()
            rev = body1["metadata"]["revision"]
            content_hash = body1["metadata"]["content_hash"]
            evidence["revision"] = rev
            evidence["content_hash"] = content_hash
            evidence["write_performed"] = body1.get("write_performed")
            evidence["idempotent_noop_1"] = body1.get("idempotent_noop")

            async with Session() as session2:
                row = (
                    await session2.execute(
                        select(IntakeV6WorkspaceRecord).where(
                            IntakeV6WorkspaceRecord.id == wid
                        )
                    )
                ).scalar_one()
                payload = _parse_payload(row.payload_json)
                snap = (payload.get("product_truth") or {}).get(
                    "confirmed_snapshot_v1", {}
                )
                meta = snap.get("metadata") or {}
                evidence["db_reload_revision"] = meta.get("revision")
                evidence["db_reload_content_hash"] = meta.get("content_hash")
                evidence["db_reload_state"] = meta.get("confirmation_state")
                evidence["db_pinned_bag_keys"] = list(
                    (snap.get("pinned_typed_bags") or {}).keys()
                )
                assert meta.get("revision") == rev
                assert meta.get("content_hash") == content_hash
                assert meta.get("confirmation_state") == "confirmed"

            st = await client.get(
                f"/api/v1/intake-v6/workspaces/{wid}/product-truth/job-status"
            )
            evidence["job_status_http"] = st.status_code
            evidence["job_status_body"] = st.json()
            assert st.status_code == 200
            assert st.json().get("has_job_revision") is True
            assert st.json()["metadata"]["revision"] == rev

            r2 = await client.post(
                f"/api/v1/intake-v6/workspaces/{wid}/product-truth/confirm-job",
                json={
                    "expected_revision": rev,
                    "root_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
                },
            )
            evidence["confirm_2_status"] = r2.status_code
            evidence["confirm_2_body"] = r2.json()
            assert r2.status_code == 200
            assert r2.json().get("idempotent_noop") is True
            assert r2.json()["metadata"]["revision"] == rev

            async with Session() as session3:
                row = (
                    await session3.execute(
                        select(IntakeV6WorkspaceRecord).where(
                            IntakeV6WorkspaceRecord.id == wid
                        )
                    )
                ).scalar_one()
                payload = _parse_payload(row.payload_json)
                fs = dict(payload.get("finish_setup") or {})
                fs["closure_edit_marker"] = "edited-after-confirm"
                payload["finish_setup"] = fs
                from services.product_truth_job_confirm_service import (
                    mark_job_revision_stale_if_confirmed,
                )

                mutated = mark_job_revision_stale_if_confirmed(payload)
                row.payload_json = json.dumps(payload)
                await session3.commit()
                evidence["stale_mark_mutated"] = mutated

            st2 = await client.get(
                f"/api/v1/intake-v6/workspaces/{wid}/product-truth/job-status"
            )
            evidence["job_status_after_edit"] = st2.json()
            assert st2.status_code == 200
            assert st2.json().get("is_stale") is True or (
                st2.json().get("metadata") or {}
            ).get("confirmation_state") in ("stale_after_edit", "stale")

            r409 = await client.post(
                f"/api/v1/intake-v6/workspaces/{wid}/product-truth/confirm-job",
                json={
                    "expected_revision": 999,
                    "root_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
                },
            )
            evidence["confirm_wrong_rev_status"] = r409.status_code
            evidence["confirm_wrong_rev_body"] = (
                r409.json()
                if "application/json" in (r409.headers.get("content-type") or "")
                else r409.text
            )
            assert r409.status_code == 409

            async with Session() as session4:
                n = (
                    await session4.execute(
                        text(
                            "SELECT COUNT(*) FROM intake_v6_workspaces WHERE id = :id"
                        ),
                        {"id": wid},
                    )
                ).scalar()
                evidence["db_row_count"] = n

        evidence["verdict"] = "PASS"
        evidence["finished_at"] = datetime.now(timezone.utc).isoformat()
        OUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print("CP_A_PROOF_OK")
        print(f"workspace_id={wid}")
        print(f"revision={rev}")
        print(f"content_hash={content_hash}")
        print(f"evidence={OUT}")
        return 0
    except Exception as exc:
        evidence["verdict"] = "FAIL"
        evidence["error"] = f"{type(exc).__name__}: {exc}"
        OUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print("CP_A_PROOF_FAIL", evidence["error"])
        return 1
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
