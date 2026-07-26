"""Read-only extractor for audit workspace capture."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CAPTURE = ROOT / "docs/qa/intake-v6-functional-handoff-audit-v1/captures/workspace.json"
HANDOFF = ROOT / "docs/qa/intake-v6-functional-handoff-audit-v1/captures/quote_handoff.json"
PD = ROOT / "docs/qa/intake-v6-functional-handoff-audit-v1/captures/product_definition.json"


def main() -> int:
    ws = json.loads(CAPTURE.read_text(encoding="utf-8-sig"))
    payload = ws.get("payload") or {}
    fs = payload.get("finish_setup") or {}
    lrs = payload.get("layer_role_setup") or {}
    comps = payload.get("components") or {}
    rc = comps.get("return_cant") or {}

    summary = {
        "workspace_id": ws.get("id"),
        "workspace_code": ws.get("workspace_code"),
        "template_code": ws.get("template_code"),
        "status": ws.get("status"),
        "finish_setup": {
            "confirmed": fs.get("confirmed"),
            "internal_draft_quote_confirmed": fs.get("internal_draft_quote_confirmed"),
            "return_depth_mm": fs.get("return_depth_mm"),
            "return_finish_type": fs.get("return_finish_type"),
            "face_finish_type": fs.get("face_finish_type"),
        },
        "letter_group_finishes": [
            {
                "group_key": g.get("group_key"),
                "return_depth_mm": g.get("return_depth_mm"),
                "return_finish_type": g.get("return_finish_type"),
                "face_finish_type": g.get("face_finish_type"),
                "confirmed": g.get("confirmed"),
            }
            for g in (fs.get("letter_group_finishes") or [])
        ],
        "artwork_finishes": [
            {
                "layer_key": a.get("layer_key"),
                "execution_type": a.get("execution_type"),
                "print_required": a.get("print_required"),
                "lamination_required": a.get("lamination_required"),
                "confirmed": a.get("confirmed"),
                "artwork_decision": a.get("artwork_decision"),
            }
            for a in (fs.get("artwork_finishes") or [])
        ],
        "layer_role_setup": {
            "confirmation_status": lrs.get("confirmation_status"),
            "complete": lrs.get("complete"),
        },
        "selected_layer_refs": (payload.get("svg") or {}).get("selected_layer_refs"),
        "components_return_cant": rc,
        "quote_handoff": json.loads(HANDOFF.read_text(encoding="utf-8-sig")) if HANDOFF.exists() else None,
    }
    if PD.exists():
        pd = json.loads(PD.read_text(encoding="utf-8-sig"))
        if isinstance(pd, dict):
            components = pd.get("components")
            if isinstance(components, dict):
                summary["product_definition_return_cant"] = components.get("return_cant")
            else:
                summary["product_definition_return_cant"] = components
        else:
            summary["product_definition_return_cant"] = pd

    out = Path(__file__).resolve().parent.parent / "captures" / "workspace_field_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
