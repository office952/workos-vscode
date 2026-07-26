"""Read-only extractor for functional handoff audit captures."""
from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "captures"


def load(name: str) -> dict:
    return json.loads((BASE / f"{name}.json").read_text(encoding="utf-8-sig"))


def main() -> None:
    ws = load("workspace")
    p = ws.get("payload") or {}
    lrs = p.get("layer_role_setup") or {}
    print("layer_ids:")
    for layer in lrs.get("layers") or []:
        print(
            f"  {layer.get('layer_key')}: id={layer.get('layer_id')!r} "
            f"role={layer.get('confirmed_role')} state={layer.get('confirmation_state')}"
        )
    print("selected_layer_refs:", (p.get("svg") or {}).get("selected_layer_refs"))
    pd = load("product_definition")
    val = pd.get("validation") or {}
    print("PD readiness:", val.get("readiness_status"))
    print("PD missing:", val.get("missing_fields"))
    print("PD blockers:", val.get("blockers"))
    pa = load("product_aggregate")
    ops = pa.get("operations") or []
    print("aggregate ops:", len(ops), "materials:", len(pa.get("materials") or []))
    print("task_rules:", len((pa.get("task_contract") or {}).get("task_rules") or []))
    for op in ops[:6]:
        print(" op:", op.get("operation_code"), op.get("component_id"), op.get("workcenter_code"))
    qh = load("quote_handoff")
    print("handoff can_submit:", qh.get("can_submit"))
    print("handoff blockers:", qh.get("blockers") or qh.get("blocking_reasons"))


if __name__ == "__main__":
    main()
