"""Controlled gradi-curat E2E handoff probe — stop at first blocker. No product-code changes."""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8001"
AUTH = {"Authorization": "Bearer __DEV_BYPASS_TOKEN__"}
SVG_PATH = Path(r"C:\Users\offic\Desktop\fisiere-teste-svg\gradi-curat.svg")
EVIDENCE = Path(r"C:\w\psiso\docs\qa\gradi-curat-e2e")
BUNDLE_META = EVIDENCE / "analysis_bundle_payload.json"

handoffs: list[dict] = []
runtime_writes: list[dict] = []
ids: dict = {}


def record(step: str, **kwargs) -> None:
    row = {"step": step, "ts": datetime.now(timezone.utc).isoformat(), **kwargs}
    handoffs.append(row)
    print(json.dumps({"step": step, "status": kwargs.get("status"), "note": kwargs.get("note")}, default=str))


def save() -> None:
    (EVIDENCE / "handoff_matrix.json").write_text(json.dumps(handoffs, indent=2, default=str), encoding="utf-8")
    (EVIDENCE / "runtime_state_summary.json").write_text(
        json.dumps(
            {
                "ids": ids,
                "runtime_writes": runtime_writes,
                "base": BASE,
                "captured_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    (EVIDENCE / "http_summaries.json").write_text(
        json.dumps([h for h in handoffs if h.get("http")], indent=2, default=str),
        encoding="utf-8",
    )


def main() -> None:
    svg_bytes = SVG_PATH.read_bytes()
    sha = hashlib.sha256(svg_bytes).hexdigest().upper()
    svg_text = svg_bytes.decode("utf-8")
    bundle_meta = json.loads(BUNDLE_META.read_text(encoding="utf-8"))
    assert bundle_meta["sha256"] == sha, "bundle sha mismatch vs desktop SVG"

    client = httpx.Client(base_url=BASE, headers=AUTH, timeout=60.0)

    # Health
    r = client.get("/docs")
    record(
        "RUNTIME_HEALTH",
        status="PASS" if r.status_code == 200 else "BLOCKED",
        http={"method": "GET", "path": "/docs", "status_code": r.status_code},
        note="backend docs reachable",
    )
    if r.status_code != 200:
        save()
        return

    # A. SVG ingestion via analysis-bundle path requires workspace first.
    # First create workspace (write 1).
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    code_title = f"GRADI-CURAT-E2E-DIAG-{stamp}"
    create_body = {
        "title": code_title,
        "template_code": "TPL-VOLUMETRIC-LETTERS_v2",
        "selected_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
        "analyzer_mode": "analyzer_first",
        "client_name": "Gradi Curat E2E Diagnostic",
        "source": "gradi_curat_e2e_diagnostic_v1",
    }
    r = client.post("/api/v1/intake-v6/workspaces", json=create_body)
    http_sum = {
        "method": "POST",
        "path": "/api/v1/intake-v6/workspaces",
        "status_code": r.status_code,
        "body_keys": list(r.json().keys()) if r.headers.get("content-type", "").startswith("application/json") else None,
        "error_text": r.text[:800] if r.status_code >= 400 else None,
    }
    if r.status_code not in (200, 201):
        record(
            "A_SVG_INGESTION_PREREQ_WORKSPACE",
            status="BLOCKED",
            input=create_body,
            expected="workspace created",
            actual=http_sum,
            http=http_sum,
            note="cannot proceed to analysis-bundle without workspace",
            persisted=False,
        )
        save()
        return

    ws = r.json()
    ws_id = ws.get("id") or ws.get("workspace_id") or (ws.get("workspace") or {}).get("id")
    ids["workspace_id"] = ws_id
    ids["workspace_title"] = code_title
    ids["template_code"] = "TPL-VOLUMETRIC-LETTERS_v2"
    runtime_writes.append({"op": "POST workspaces", "workspace_id": ws_id, "status": r.status_code})
    record(
        "A0_WORKSPACE_CREATE",
        status="PASS",
        identity={"workspace_id": ws_id},
        input=create_body,
        expected="201/200 workspace",
        actual={"workspace_id": ws_id, "status_code": r.status_code},
        http=http_sum,
        persisted=True,
        manual_intervention=False,
        note="root template letters v2; composition logos expected via analysis",
    )

    # A. analysis-bundle
    put_body = {
        "file_name": "gradi-curat.svg",
        "file_size_bytes": len(svg_bytes),
        "svg_text": svg_text,
        "svg_analysis_json": bundle_meta["svg_analysis_json"],
        "layer_role_setup": bundle_meta["layer_role_setup"],
    }
    r = client.put(f"/api/v1/intake-v6/workspaces/{ws_id}/analysis-bundle", json=put_body)
    http_sum = {
        "method": "PUT",
        "path": f"/api/v1/intake-v6/workspaces/{ws_id}/analysis-bundle",
        "status_code": r.status_code,
        "error_text": r.text[:1200] if r.status_code >= 400 else None,
    }
    if r.status_code != 200:
        record(
            "A_SVG_FILE_TO_ANALYZER_INGESTION",
            status="BLOCKED",
            identity={"workspace_id": ws_id},
            route="/api/v1/intake-v6/workspaces/{id}/analysis-bundle",
            input={
                "file_name": "gradi-curat.svg",
                "file_size_bytes": len(svg_bytes),
                "sha256": sha,
                "layer_count": len(bundle_meta["layer_role_setup"]["layers"]),
            },
            expected="200 persisted analysis + quote_geometry",
            actual=http_sum,
            http=http_sum,
            persisted=False,
            note="first blocker at SVG analysis-bundle persist",
        )
        (EVIDENCE / "first_blocker_evidence.json").write_text(
            json.dumps({"handoff": "A", "http": http_sum}, indent=2), encoding="utf-8"
        )
        save()
        return

    ws_after = r.json()
    workspace_obj = ws_after.get("workspace") if isinstance(ws_after.get("workspace"), dict) else ws_after
    qg = (workspace_obj or {}).get("quote_geometry") or ws_after.get("quote_geometry")
    svg_src = (workspace_obj or {}).get("svg_source") or ws_after.get("svg_source")
    composition = (workspace_obj or {}).get("product_composition_recommendation") or ws_after.get(
        "product_composition_recommendation"
    )
    runtime_writes.append({"op": "PUT analysis-bundle", "workspace_id": ws_id, "status": r.status_code})
    (EVIDENCE / "workspace_after_analysis_bundle.json").write_text(
        json.dumps(
            {
                "workspace_id": ws_id,
                "svg_source": svg_src,
                "quote_geometry_keys": list(qg.keys()) if isinstance(qg, dict) else qg,
                "quote_geometry": qg,
                "product_composition_recommendation": composition,
                "layer_role_setup": (workspace_obj or {}).get("layer_role_setup")
                or ws_after.get("layer_role_setup"),
                "response_top_keys": list(ws_after.keys()),
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    record(
        "A_SVG_FILE_TO_ANALYZER_INGESTION",
        status="PASS",
        identity={"workspace_id": ws_id, "svg_sha256": sha},
        route="/api/v1/intake-v6/workspaces/{id}/analysis-bundle",
        input={"file_name": "gradi-curat.svg", "sha256": sha, "size": len(svg_bytes)},
        expected="persisted svg_source + analysis + quote_geometry",
        actual={
            "svg_source": svg_src,
            "has_quote_geometry": isinstance(qg, dict) and bool(qg),
            "composition_present": composition is not None,
        },
        http={"method": "PUT", "path": http_sum["path"], "status_code": 200},
        persisted=True,
        manual_intervention=False,
    )

    # B. geometry → intake fields via pricing-input-preview
    r = client.get(f"/api/v1/intake-v6/workspaces/{ws_id}/pricing-input-preview")
    http_sum = {
        "method": "GET",
        "path": f"/api/v1/intake-v6/workspaces/{ws_id}/pricing-input-preview",
        "status_code": r.status_code,
        "error_text": r.text[:1200] if r.status_code >= 400 else None,
    }
    preview = r.json() if r.status_code == 200 else None
    (EVIDENCE / "pricing_input_preview.json").write_text(
        json.dumps(preview if preview is not None else http_sum, indent=2, default=str),
        encoding="utf-8",
    )
    if r.status_code != 200:
        record(
            "B_SVG_GEOMETRY_TO_INTAKE_V6_FIELDS",
            status="BLOCKED",
            identity={"workspace_id": ws_id},
            route="/pricing-input-preview",
            expected="quote_input_payload with geometry metrics",
            actual=http_sum,
            http=http_sum,
            persisted=False,
        )
        (EVIDENCE / "first_blocker_evidence.json").write_text(
            json.dumps({"handoff": "B", "http": http_sum}, indent=2), encoding="utf-8"
        )
        save()
        return

    qi = preview.get("quote_input_payload") or preview.get("quote_input") or {}
    record(
        "B_SVG_GEOMETRY_TO_INTAKE_V6_FIELDS",
        status="PASS" if qi else "PASS_WITH_WARNING",
        identity={"workspace_id": ws_id},
        route="/pricing-input-preview",
        input="workspace after analysis-bundle",
        expected="vector_file + letter_* geometry mapped",
        actual={
            "quote_input_keys": list(qi.keys()) if isinstance(qi, dict) else type(qi).__name__,
            "vector_file": (qi or {}).get("vector_file") if isinstance(qi, dict) else None,
            "letter_count": (qi or {}).get("letter_count") if isinstance(qi, dict) else None,
            "letter_perimeter_m": (qi or {}).get("letter_perimeter_m") if isinstance(qi, dict) else None,
            "letter_face_area_m2": (qi or {}).get("letter_face_area_m2") if isinstance(qi, dict) else None,
            "width_mm": (qi or {}).get("width_mm") if isinstance(qi, dict) else None,
            "height_mm": (qi or {}).get("height_mm") if isinstance(qi, dict) else None,
            "preview_top_keys": list(preview.keys()),
        },
        http={"method": "GET", "status_code": 200},
        persisted=False,
        manual_intervention=False,
        note="preview is read model; finish_setup still required for commercial readiness",
    )

    # C. Intake → ProductDefinition
    # Try known endpoints
    pd_paths = [
        f"/api/v1/intake-v6/workspaces/{ws_id}/product-definition",
        f"/api/v1/intake-v6/workspaces/{ws_id}/product-definition-preview",
        f"/api/v1/product-definitions/from-intake-v6/{ws_id}",
        f"/api/v1/intake-v6/workspaces/{ws_id}/readiness",
    ]
    pd_hits = []
    for path in pd_paths:
        rr = client.get(path)
        pd_hits.append({"path": path, "status_code": rr.status_code, "snippet": rr.text[:400]})
    (EVIDENCE / "product_definition_probe.json").write_text(json.dumps(pd_hits, indent=2), encoding="utf-8")

    # Also GET full workspace for readiness / blockers
    r = client.get(f"/api/v1/intake-v6/workspaces/{ws_id}")
    full = r.json() if r.status_code == 200 else {"status_code": r.status_code, "text": r.text[:800]}
    (EVIDENCE / "workspace_full_after_b.json").write_text(json.dumps(full, indent=2, default=str), encoding="utf-8")

    # Check finish_setup / readiness fields
    ws_body = full.get("workspace") if isinstance(full.get("workspace"), dict) else full
    finish = (ws_body or {}).get("finish_setup") if isinstance(ws_body, dict) else None
    readiness = None
    for key in ("readiness", "quote_readiness", "product_truth", "blockers"):
        if isinstance(ws_body, dict) and key in ws_body:
            readiness = {**(readiness or {}), key: ws_body.get(key)}

    # Try product system binding / compile endpoints used by UI
    more_paths = [
        f"/api/v1/intake-v6/workspaces/{ws_id}/product-system-binding",
        f"/api/v1/intake-v6/workspaces/{ws_id}/task-preview",
        f"/api/v1/intake-v6/workspaces/{ws_id}/material-breakdown",
        f"/api/v1/intake-v6/workspaces/{ws_id}/commercial-price-proposal",
        f"/api/v1/intake-v6/workspaces/{ws_id}/estimated-internal-cost",
    ]
    more_hits = []
    for path in more_paths:
        rr = client.get(path)
        more_hits.append(
            {
                "path": path,
                "status_code": rr.status_code,
                "snippet": rr.text[:600],
            }
        )
    (EVIDENCE / "downstream_read_probes.json").write_text(json.dumps(more_hits, indent=2), encoding="utf-8")

    # Determine if ProductDefinition can compile without finish — inspect preview for blockers
    blockers = []
    if not finish or (isinstance(finish, dict) and not finish.get("confirmed")):
        blockers.append("finish_setup_not_confirmed")

    # Composition confirmation
    composition_confirmed = (ws_body or {}).get("product_composition_confirmed") if isinstance(ws_body, dict) else None
    composition_rec = (ws_body or {}).get("product_composition_recommendation") if isinstance(ws_body, dict) else None
    if composition_rec and not composition_confirmed:
        blockers.append("product_composition_not_confirmed")

    # Attempt product definition compile if endpoint exists among hits
    pd_ok = next((h for h in pd_hits if h["status_code"] == 200), None)
    if pd_ok:
        record(
            "C_INTAKE_V6_TO_PRODUCT_DEFINITION",
            status="PASS_WITH_WARNING" if blockers else "PASS",
            identity={"workspace_id": ws_id},
            route=pd_ok["path"],
            expected="ProductDefinition compile from workspace",
            actual={"blockers": blockers, "finish_setup": finish, "composition_confirmed": composition_confirmed},
            persisted=False,
            note="PD endpoint returned 200; check blockers before commercial",
        )
    else:
        # Try building via pricing preview readiness flags
        ready_flags = {
            k: preview.get(k)
            for k in preview.keys()
            if "ready" in k.lower() or "block" in k.lower() or "missing" in k.lower()
        }
        record(
            "C_INTAKE_V6_TO_PRODUCT_DEFINITION",
            status="BLOCKED" if blockers else "NOT_REACHED",
            identity={"workspace_id": ws_id},
            route="product-definition endpoints + workspace state",
            expected="compile ProductDefinition without inventing finishes",
            actual={
                "pd_probe_hits": pd_hits,
                "blockers": blockers,
                "finish_setup": finish,
                "composition_recommendation": composition_rec,
                "composition_confirmed": composition_confirmed,
                "preview_ready_flags": ready_flags,
                "downstream": more_hits,
            },
            persisted=False,
            manual_intervention="would require operator finish_setup / composition confirmation / owner decisions",
            note="stop before inventing illuminated/finish/ACM values",
        )
        (EVIDENCE / "first_blocker_evidence.json").write_text(
            json.dumps(
                {
                    "handoff": "C",
                    "blockers": blockers,
                    "classification": "OWNER_DECISION" if "composition" in str(blockers) or True else "INTAKE_CONTRACT",
                    "required_operator_inputs": [
                        "illuminated yes/no",
                        "face finish / oracal / ral per letter group",
                        "return finish / depth confirmation",
                        "backing mode",
                        "linked logo execution confirmation",
                        "composition confirmation items",
                        "quantity / location / installation if required",
                    ],
                    "required_owner_decisions": [
                        "confirm letters-root + linked logo composition as sold product",
                        "illumination commercial policy for this job",
                        "whether ACM mounting is in scope (default NO for this file)",
                    ],
                    "workspace_id": ws_id,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        # Mark remaining handoffs NOT_REACHED
        for step in [
            "D_PRODUCT_DEFINITION_TO_PRODUCT_AGGREGATE",
            "E_PRODUCT_AGGREGATE_TO_COMMERCIAL_PRICE_PROPOSAL",
            "F_PRODUCT_AGGREGATE_TO_ESTIMATED_INTERNAL_COST",
            "G_PRICING_TO_QUOTE_SNAPSHOT_V2",
            "H_QUOTE_ACCEPT_TO_ORDER_SNAPSHOT_V2",
            "I_ORDER_TO_EXECUTION_PLAN_V2_PREVIEW",
            "J_EXECUTION_PLAN_PREVIEW_TO_PERSIST",
            "K_PLAN_TO_TASK_MATERIALIZATION",
            "L_TASKS_TO_SESSIONS_REALITY",
            "M_INVENTORY_DEDUCTION_TO_MATERIAL_ACTUAL",
            "N_SESSIONS_TO_LABOR_MINUTES",
            "O_REALITY_TO_POST_JOB_RECONCILIATION",
            "P_RECONCILIATION_TO_PROFITABILITY_COVERAGE",
        ]:
            record(step, status="NOT_REACHED", identity={"workspace_id": ws_id}, note="stopped at first blocker C")
        save()
        return

    save()


if __name__ == "__main__":
    main()
