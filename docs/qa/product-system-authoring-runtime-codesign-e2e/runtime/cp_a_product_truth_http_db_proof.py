"""CP-A live proof: HTTP ConfirmJobProductTruth → SQLite persist → new-session reload.

Usage (from repo root, BE on 8000 or 8011):
  cd backend
  .\\.venv\\Scripts\\python.exe ..\\docs\\qa\\product-system-authoring-runtime-codesign-e2e\\runtime\\cp_a_product_truth_http_db_proof.py

Writes evidence JSON next to this script. Never activates TPL-VOLUM-ALUMINIU_v1.
"""

from __future__ import annotations

import copy
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RUNTIME = Path(__file__).resolve().parent
REPO = RUNTIME.parents[3]
DB_PATH = REPO / "backend" / "dev.db"
TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
AUTH = {"Authorization": "Bearer __DEV_BYPASS_TOKEN__", "Content-Type": "application/json"}
PORTS = (8000, 8011)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pick_base() -> str:
    last_err: Exception | None = None
    for port in PORTS:
        base = f"http://127.0.0.1:{port}"
        try:
            req = urllib.request.Request(
                f"{base}/api/v1/auth/me", headers={"Authorization": AUTH["Authorization"]}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    return base
        except Exception as exc:  # noqa: BLE001
            last_err = exc
    raise RuntimeError(f"No healthy BE on {PORTS}: {last_err}")


def http(
    method: str, base: str, path: str, body: dict[str, Any] | None = None
) -> dict[str, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{base}{path}", data=data, headers=AUTH, method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return {
                "status": resp.status,
                "body": json.loads(raw) if raw else {},
                "ok": True,
            }
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"raw": raw}
        return {"status": e.code, "body": parsed, "ok": False}


def db_read_snapshot(workspace_id: str) -> dict[str, Any]:
    """Fresh sqlite3 connection — proves not in-memory-only service state."""
    conn = sqlite3.connect(str(DB_PATH))
    try:
        row = conn.execute(
            "SELECT template_code, payload_json, updated_at FROM intake_v6_workspaces WHERE id=?",
            (workspace_id,),
        ).fetchone()
        if not row:
            return {"found": False}
        payload = json.loads(row[1] or "{}")
        pt = payload.get("product_truth") if isinstance(payload.get("product_truth"), dict) else {}
        snap = (
            pt.get("confirmed_snapshot_v1")
            if isinstance(pt.get("confirmed_snapshot_v1"), dict)
            else None
        )
        meta = snap.get("metadata") if isinstance(snap, dict) and isinstance(snap.get("metadata"), dict) else {}
        return {
            "found": True,
            "template_code": row[0],
            "updated_at": row[2],
            "has_confirmed_snapshot_v1": snap is not None,
            "revision": meta.get("revision"),
            "content_hash": meta.get("content_hash"),
            "confirmation_state": meta.get("confirmation_state"),
            "pinned_bag_keys": list((snap or {}).get("pinned_typed_bags") or {}.keys())
            if isinstance(snap, dict)
            else [],
            "snapshot_metadata": meta,
            "audit_trail_len": len((snap or {}).get("audit_trail") or [])
            if isinstance(snap, dict)
            else 0,
        }
    finally:
        conn.close()


def db_read_snapshot_session2(workspace_id: str) -> dict[str, Any]:
    """Second independent connection (new session)."""
    return db_read_snapshot(workspace_id)


def _clone_svg_layer_prereqs(workspace_id: str) -> dict[str, Any]:
    """Copy SVG + layer_role_setup from a ready VL fixture so finish-setup can persist bags.

    Confirm itself does not need this; finish-setup (seed + stale edit) does.
    """
    conn = sqlite3.connect(str(DB_PATH))
    try:
        src = conn.execute(
            """
            SELECT id, payload_json FROM intake_v6_workspaces
            WHERE template_code = ?
              AND payload_json LIKE '%layer_role_setup%'
              AND payload_json LIKE '%acm_panel_instance%'
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (TEMPLATE,),
        ).fetchone()
        if not src:
            return {"ok": False, "error": "no_source_fixture_with_layer_roles_and_acm"}
        src_id, src_raw = src
        src_payload = json.loads(src_raw)
        dst_row = conn.execute(
            "SELECT payload_json FROM intake_v6_workspaces WHERE id=?",
            (workspace_id,),
        ).fetchone()
        if not dst_row:
            return {"ok": False, "error": "dest_workspace_missing"}
        dst = json.loads(dst_row[0] or "{}")
        keys = (
            "layer_role_setup",
            "svg_source",
            "svg",
            "svg_source_text",
            "svg_analysis_json",
            "path_geometry_summary",
            "quote_geometry",
            "layer_role_review",
        )
        copied = []
        for key in keys:
            if key in src_payload:
                dst[key] = copy.deepcopy(src_payload[key])
                copied.append(key)
        conn.execute(
            "UPDATE intake_v6_workspaces SET payload_json=? WHERE id=?",
            (json.dumps(dst, ensure_ascii=False), workspace_id),
        )
        conn.commit()
        return {"ok": True, "source_workspace_id": src_id, "copied_keys": copied}
    finally:
        conn.close()


def seed_bags_via_finish_setup(base: str, workspace_id: str) -> dict[str, Any]:
    # GET workspace to preserve existing finish_setup fields where possible
    ws = http("GET", base, f"/api/v1/intake-v6/workspaces/{workspace_id}")
    if not ws["ok"]:
        return ws
    payload = ws["body"].get("payload") or {}
    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
    finish = dict(finish)
    finish["letter_group_instances"] = [
        {
            "schema": "volumetric_letter_group_instance_v1",
            "instance_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "group_key": "pseudo:cpa-proof",
            "confirmed": True,
        }
    ]
    finish["component_placements"] = [
        {
            "schema": "component_placement_v1",
            "placement_id": "cpa-pl-1",
            "source_instance_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "target_kind": "acm_panel",
            "target_instance_id": "cpa-acm-1",
        }
    ]
    finish["acm_panel_instance"] = {
        "schema": "acm_panel_component_instance_v1",
        "component_instance_id": "cpa-acm-1",
        "component_template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
        "association_status": "confirmed",
    }
    finish["acm_panel_domain_action"] = "upsert"
    finish["confirmed"] = False
    return http(
        "PUT",
        base,
        f"/api/v1/intake-v6/workspaces/{workspace_id}/finish-setup",
        finish,
    )


def edit_finish_to_stale(base: str, workspace_id: str) -> dict[str, Any]:
    ws = http("GET", base, f"/api/v1/intake-v6/workspaces/{workspace_id}")
    if not ws["ok"]:
        return ws
    payload = ws["body"].get("payload") or {}
    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
    finish = dict(finish)
    letters = list(finish.get("letter_group_instances") or [])
    if letters and isinstance(letters[0], dict):
        letters[0] = dict(letters[0])
        letters[0]["confirmed"] = False
        letters[0]["group_key"] = "pseudo:cpa-proof-edited"
    else:
        letters = [
            {
                "schema": "volumetric_letter_group_instance_v1",
                "instance_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                "group_key": "pseudo:cpa-proof-edited",
                "confirmed": False,
            }
        ]
    finish["letter_group_instances"] = letters
    finish["acm_panel_domain_action"] = "preserve"
    return http(
        "PUT",
        base,
        f"/api/v1/intake-v6/workspaces/{workspace_id}/finish-setup",
        finish,
    )


def main() -> int:
    evidence: dict[str, Any] = {
        "proof": "CP-A_product_truth_http_db_persist_reload",
        "started_at": _utcnow(),
        "head_expected": "705a701a6e48f2bee1f638e44031f32f6d19d751",
        "db_path": str(DB_PATH),
        "template_code": TEMPLATE,
        "steps": {},
        "verdict": "FAIL",
    }
    out_path = RUNTIME / f"cp_a_http_db_proof_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    try:
        base = _pick_base()
        evidence["base_url"] = base
        evidence["auth"] = {
            "header": "Authorization: Bearer __DEV_BYPASS_TOKEN__",
            "router_dependency": "Depends(get_current_user) on /api/v1/intake-v6",
            "confirm_route": "POST /api/v1/intake-v6/workspaces/{id}/product-truth/confirm-job",
            "status_route": "GET /api/v1/intake-v6/workspaces/{id}/product-truth/job-status",
            "me": http("GET", base, "/api/v1/auth/me"),
        }

        # 1) Create dedicated fixture workspace
        created = http(
            "POST",
            base,
            "/api/v1/intake-v6/workspaces",
            {
                "title": f"CP-A Product Truth HTTP/DB Proof {_utcnow()}",
                "template_code": TEMPLATE,
                "client_name": "CP-A Proof Client",
                "job_title": "CP-A confirm persist",
                "source": "cp_a_product_truth_http_db_proof",
            },
        )
        evidence["steps"]["create_workspace"] = {
            "status": created["status"],
            "ok": created["ok"],
            "body_keys": list(created["body"].keys()) if isinstance(created["body"], dict) else [],
        }
        if not created["ok"]:
            evidence["error"] = created
            out_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
            print(f"FAIL create workspace -> {out_path}")
            return 2

        workspace_id = created["body"]["id"]
        workspace_code = created["body"].get("workspace_code")
        evidence["workspace_id"] = workspace_id
        evidence["workspace_code"] = workspace_code
        evidence["template_code_observed"] = created["body"].get("template_code")

        # Prove HTTP create landed in target sqlite file
        db_after_create = db_read_snapshot(workspace_id)
        evidence["steps"]["db_after_create"] = db_after_create
        if not db_after_create.get("found"):
            evidence["error"] = "workspace not found in target dev.db - BE may use different DATABASE_URL"
            out_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
            print(f"FAIL db bind -> {out_path}")
            return 3

        # 2) Clone SVG/layer prereqs (finish-setup gate), then seed typed bags via HTTP
        cloned = _clone_svg_layer_prereqs(workspace_id)
        evidence["steps"]["clone_svg_layer_prereqs"] = cloned
        if not cloned.get("ok"):
            evidence["error"] = cloned
            out_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
            print(f"FAIL clone prereqs -> {out_path}")
            return 4

        seeded = seed_bags_via_finish_setup(base, workspace_id)
        evidence["steps"]["seed_finish_bags"] = {
            "status": seeded["status"],
            "ok": seeded["ok"],
            "detail": seeded["body"].get("detail") if not seeded["ok"] else None,
        }
        if not seeded["ok"]:
            evidence["error"] = seeded
            out_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
            print(f"FAIL seed bags -> {out_path}")
            return 4

        # 3) Baseline job-status
        status0 = http(
            "GET", base, f"/api/v1/intake-v6/workspaces/{workspace_id}/product-truth/job-status"
        )
        evidence["steps"]["job_status_before"] = status0

        # 4) First confirm
        confirm1 = http(
            "POST",
            base,
            f"/api/v1/intake-v6/workspaces/{workspace_id}/product-truth/confirm-job",
            {
                "expected_revision": 0,
                "root_template_code": TEMPLATE,
            },
        )
        evidence["steps"]["confirm_first"] = confirm1
        if not confirm1["ok"]:
            evidence["error"] = "first confirm failed"
            out_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
            print(f"FAIL confirm -> {out_path}")
            return 5

        meta1 = (confirm1["body"].get("metadata") or {})
        revision_id = meta1.get("revision")
        content_hash = meta1.get("content_hash")
        evidence["revision_id"] = revision_id
        evidence["content_hash"] = content_hash

        # 5) Immediate DB read (fresh connection)
        time.sleep(0.05)
        db1 = db_read_snapshot(workspace_id)
        evidence["steps"]["db_after_confirm_session1"] = db1

        # 6) New session re-read
        db2 = db_read_snapshot_session2(workspace_id)
        evidence["steps"]["db_after_confirm_session2"] = db2

        persist_ok = (
            db1.get("found")
            and db1.get("has_confirmed_snapshot_v1")
            and db1.get("confirmation_state") == "confirmed"
            and db1.get("revision") == revision_id
            and db1.get("content_hash") == content_hash
            and db2.get("content_hash") == content_hash
            and confirm1["body"].get("write_performed") is True
        )
        evidence["steps"]["persist_reload_ok"] = persist_ok

        # 7) HTTP job-status after confirm
        status1 = http(
            "GET", base, f"/api/v1/intake-v6/workspaces/{workspace_id}/product-truth/job-status"
        )
        evidence["steps"]["job_status_after_confirm"] = status1

        # 8) Idempotent reconfirm
        confirm_idem = http(
            "POST",
            base,
            f"/api/v1/intake-v6/workspaces/{workspace_id}/product-truth/confirm-job",
            {
                "expected_revision": int(revision_id),
                "root_template_code": TEMPLATE,
            },
        )
        evidence["steps"]["confirm_idempotent"] = confirm_idem
        idem_ok = (
            confirm_idem["ok"]
            and confirm_idem["body"].get("idempotent_noop") is True
            and confirm_idem["body"].get("write_performed") is False
            and (confirm_idem["body"].get("metadata") or {}).get("revision") == revision_id
        )
        evidence["steps"]["idempotent_ok"] = idem_ok

        # 9) 409 revision_mismatch
        conflict_rev = http(
            "POST",
            base,
            f"/api/v1/intake-v6/workspaces/{workspace_id}/product-truth/confirm-job",
            {
                "expected_revision": 0,
                "root_template_code": TEMPLATE,
            },
        )
        evidence["steps"]["conflict_revision_mismatch"] = conflict_rev
        rev409_ok = (
            conflict_rev["status"] == 409
            and isinstance(conflict_rev["body"].get("detail"), dict)
            and conflict_rev["body"]["detail"].get("error") == "revision_mismatch"
        )
        evidence["steps"]["revision_mismatch_409_ok"] = rev409_ok

        # 10) 409 draft_hash_mismatch
        conflict_draft = http(
            "POST",
            base,
            f"/api/v1/intake-v6/workspaces/{workspace_id}/product-truth/confirm-job",
            {
                "expected_revision": int(revision_id),
                "expected_draft_hash": "sha256:deadbeef_cpa_proof",
                "root_template_code": TEMPLATE,
            },
        )
        evidence["steps"]["conflict_draft_hash_mismatch"] = conflict_draft
        draft409_ok = (
            conflict_draft["status"] == 409
            and isinstance(conflict_draft["body"].get("detail"), dict)
            and conflict_draft["body"]["detail"].get("error") == "draft_hash_mismatch"
        )
        evidence["steps"]["draft_hash_mismatch_409_ok"] = draft409_ok

        # 11) 409 content_hash_mismatch
        conflict_content = http(
            "POST",
            base,
            f"/api/v1/intake-v6/workspaces/{workspace_id}/product-truth/confirm-job",
            {
                "expected_revision": int(revision_id),
                "expected_content_hash": "sha256:deadbeef_content_cpa",
                "root_template_code": TEMPLATE,
            },
        )
        evidence["steps"]["conflict_content_hash_mismatch"] = conflict_content
        content409_ok = (
            conflict_content["status"] == 409
            and isinstance(conflict_content["body"].get("detail"), dict)
            and conflict_content["body"]["detail"].get("error") == "content_hash_mismatch"
        )
        evidence["steps"]["content_hash_mismatch_409_ok"] = content409_ok

        # 12) Stale after edit
        edited = edit_finish_to_stale(base, workspace_id)
        evidence["steps"]["edit_finish"] = {
            "status": edited["status"],
            "ok": edited["ok"],
        }
        status_stale = http(
            "GET", base, f"/api/v1/intake-v6/workspaces/{workspace_id}/product-truth/job-status"
        )
        evidence["steps"]["job_status_after_edit"] = status_stale
        db_stale = db_read_snapshot(workspace_id)
        evidence["steps"]["db_after_edit"] = db_stale
        stale_ok = (
            edited["ok"]
            and status_stale["ok"]
            and status_stale["body"].get("is_stale") is True
            and (status_stale["body"].get("metadata") or {}).get("confirmation_state")
            == "stale_after_edit"
            and status_stale["body"].get("commercial_freeze_allowed") is False
            and db_stale.get("confirmation_state") == "stale_after_edit"
            # pin retained
            and db_stale.get("has_confirmed_snapshot_v1") is True
            and db_stale.get("content_hash") == content_hash
        )
        evidence["steps"]["stale_after_edit_ok"] = stale_ok

        # Verdict
        all_ok = all(
            [
                persist_ok,
                idem_ok,
                rev409_ok,
                draft409_ok,
                content409_ok,
                stale_ok,
                status1["ok"]
                and status1["body"].get("has_job_revision") is True
                and status1["body"].get("commercial_freeze_allowed") is True,
            ]
        )
        evidence["verdict"] = "PASS" if all_ok else "PARTIAL"
        evidence["finished_at"] = _utcnow()
        evidence["summary"] = {
            "persist_reload_ok": persist_ok,
            "idempotent_ok": idem_ok,
            "revision_mismatch_409_ok": rev409_ok,
            "draft_hash_mismatch_409_ok": draft409_ok,
            "content_hash_mismatch_409_ok": content409_ok,
            "stale_after_edit_ok": stale_ok,
            "revision_id": revision_id,
            "content_hash": content_hash,
        }

        out_path.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
        # Stable pointer
        latest = RUNTIME / "cp_a_http_db_proof_latest.json"
        latest.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
        print(json.dumps({"verdict": evidence["verdict"], "out": str(out_path), **evidence["summary"]}, indent=2))
        return 0 if all_ok else 1
    except Exception as exc:  # noqa: BLE001
        evidence["error"] = repr(exc)
        evidence["finished_at"] = _utcnow()
        out_path.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
        print(f"FAIL exception {exc!r} -> {out_path}", file=sys.stderr)
        return 10


if __name__ == "__main__":
    raise SystemExit(main())
