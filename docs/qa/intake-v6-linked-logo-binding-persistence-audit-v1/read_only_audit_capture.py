"""Read-only API capture for linked logo binding audit. No writes."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

WORKSPACE_ID = "22ef834d-f2d0-453b-a7a7-118928c98a39"
BASE = "http://127.0.0.1:8000/api/v1/intake-v6"
OUT = Path(__file__).resolve().parent / "captures"


def get(path: str) -> dict:
    url = f"{BASE}{path}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return {
                "method": "GET",
                "url": url,
                "http": resp.status,
                "writes": "NONE",
                "body": json.loads(body) if body else None,
            }
    except urllib.error.HTTPError as exc:
        return {
            "method": "GET",
            "url": url,
            "http": exc.code,
            "writes": "NONE",
            "error": exc.read().decode("utf-8", errors="replace")[:500],
        }


def summarize_workspace(payload: dict | None) -> dict:
    if not isinstance(payload, dict):
        return {}
    layer_setup = payload.get("layer_role_setup") or {}
    finish = payload.get("finish_setup") or {}
    svg = payload.get("svg") or {}
    return {
        "layer_bindings_count": len(layer_setup.get("layer_bindings") or []),
        "layers_count": len(layer_setup.get("layers") or []),
        "logo_layers": [
            {
                "layer_key": layer.get("layer_key"),
                "confirmed_role": layer.get("confirmed_role"),
                "confirmation_state": layer.get("confirmation_state"),
            }
            for layer in (layer_setup.get("layers") or [])
            if (layer.get("confirmed_role") or layer.get("auto_role")) in {"printed_artwork", "logo"}
        ],
        "selected_layer_refs_count": len(svg.get("selected_layer_refs") or []),
        "vector_logo_refs": [
            ref for ref in (svg.get("selected_layer_refs") or []) if ref.get("role") == "vector_logo"
        ],
        "artwork_finishes": [
            {
                "layer_key": row.get("layer_key"),
                "execution_type": row.get("execution_type"),
                "confirmed": row.get("confirmed"),
            }
            for row in (finish.get("artwork_finishes") or [])
        ],
        "product_composition_recommendation": payload.get("product_composition_recommendation"),
        "product_composition_confirmed": payload.get("product_composition_confirmed"),
    }


def sanitize_linked_segments(body: dict | None) -> dict:
    if not isinstance(body, dict):
        return {}
    segments = body.get("linked_template_runtime_segments") or {}
    return {
        "root_template_code": segments.get("root_template_code"),
        "composition_mode": segments.get("composition_mode"),
        "summary": segments.get("summary"),
        "product_truth_readiness_summary": segments.get("product_truth_readiness_summary"),
        "segments": [
            {
                "segment_key": s.get("segment_key"),
                "owning_template_code": s.get("owning_template_code"),
                "binding_status": s.get("binding_status"),
                "binding_reason": s.get("binding_reason"),
                "state": s.get("state"),
                "finish": s.get("finish"),
                "product_truth_readiness": {
                    "status": (s.get("product_truth_readiness") or {}).get("status"),
                    "blockers": (s.get("product_truth_readiness") or {}).get("blockers"),
                },
            }
            for s in (segments.get("segments") or [])
        ],
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    endpoints = [
        (f"/workspaces/{WORKSPACE_ID}", "workspace.json"),
        (f"/workspaces/{WORKSPACE_ID}/linked-template-segments", "linked_segments.json"),
        (f"/workspaces/{WORKSPACE_ID}/runtime-capture-read-model", "runtime_capture.json"),
        (f"/workspaces/{WORKSPACE_ID}/product-truth-promotion-planner", "promotion_planner.json"),
        (f"/workspaces/{WORKSPACE_ID}/product-system-binding", "product_system_binding.json"),
    ]
    index: list[dict] = []
    for path, filename in endpoints:
        result = get(path)
        capture = {k: v for k, v in result.items() if k != "body"}
        if result.get("body") is not None:
            (OUT / filename).write_text(json.dumps(result["body"], indent=2, ensure_ascii=False), encoding="utf-8")
            capture["artifact"] = filename
        index.append(capture)

    ws = get(f"/workspaces/{WORKSPACE_ID}")
    summary = summarize_workspace((ws.get("body") or {}).get("payload"))
    (OUT / "workspace_binding_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    linked = get(f"/workspaces/{WORKSPACE_ID}/linked-template-segments")
    linked_summary = sanitize_linked_segments(linked.get("body"))
    (OUT / "linked_segments_summary.json").write_text(json.dumps(linked_summary, indent=2), encoding="utf-8")

    (OUT / "endpoint_index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(json.dumps({"captures": len(index), "summary": summary, "linked": linked_summary}, indent=2))


if __name__ == "__main__":
    main()
