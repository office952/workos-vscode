"""Read-only DB proof for Wave 3 materialization (local evidence only)."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

DB = Path(r"C:\w\psiso\backend\dev.db")
OUT = Path(r"C:\w\psiso\docs\qa\workos-wave3-controlled-materialization-v1\db_readback.json")


def main() -> None:
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    tables = [r[0] for r in cur.execute("select name from sqlite_master where type='table'")]
    plan_table = next((t for t in tables if t.lower() in {"executionplan", "execution_plan", "execution_plans"}), None)
    reality_table = next((t for t in tables if "reality" in t.lower()), None)
    report: dict = {"tables_sample": sorted(tables)[:40], "plan_table": plan_table, "reality_table": reality_table}

    for oid in (880811, 973019, 88002, 880750):
        o = cur.execute(
            "select id, code, status, snapshot_v2_json from orders where id=?",
            (oid,),
        ).fetchone()
        entry: dict = {"order_id": oid}
        if o is None:
            entry["order"] = None
            report[str(oid)] = entry
            continue
        snap = o["snapshot_v2_json"] or ""
        sha = hashlib.sha256(snap.encode("utf-8")).hexdigest() if snap else None
        accepted = None
        if snap:
            try:
                accepted = json.loads(snap).get("accepted_commercial_total")
            except Exception:
                accepted = None
        entry["order"] = {
            "code": o["code"],
            "accepted_commercial_total": accepted,
            "snapshot_sha256": sha,
            "snapshot_sha_prefix": sha[:16] if sha else None,
            "snapshot_sha_suffix": sha[-8:] if sha else None,
        }
        if plan_table:
            cols = [r[1] for r in cur.execute(f"pragma table_info({plan_table})")]
            p = cur.execute(
                f"select * from {plan_table} where order_id=?",
                (oid,),
            ).fetchone()
            if p is None:
                entry["plan"] = None
            else:
                tasks_raw = p["tasks_json"] if "tasks_json" in cols else None
                env = json.loads(tasks_raw) if tasks_raw else {}
                ops = env.get("operational_tasks") or []
                planned = env.get("planned_tasks") or []
                vinyl = next(
                    (
                        t
                        for t in ops
                        if "vinyl_application" in str(t.get("task_id") or "")
                    ),
                    None,
                )
                deps = list((vinyl or {}).get("depends_on_task_ids") or [])
                entry["plan"] = {
                    "id": p["id"],
                    "source_snapshot_code": p["source_snapshot_code"] if "source_snapshot_code" in cols else None,
                    "source_quote_snapshot_v2_id": p["source_quote_snapshot_v2_id"]
                    if "source_quote_snapshot_v2_id" in cols
                    else None,
                    "execution_tasks_created": env.get("execution_tasks_created"),
                    "planned_tasks": len(planned),
                    "planned_operations": len(env.get("planned_operations") or []),
                    "operational_tasks": len(ops),
                    "materialization_audit": env.get("materialization_audit"),
                    "assigned_employee_nonzero": sum(1 for t in ops if t.get("assigned_employee_id")),
                    "machine_code_nonzero": sum(
                        1 for t in ops if t.get("machine_code") or t.get("assigned_machine_code")
                    ),
                    "all_minutes_null": all(t.get("estimated_time_minutes") is None for t in ops)
                    if ops
                    else None,
                    "unique_task_ids": len({t.get("task_id") for t in ops}),
                    "vinyl_deps": deps,
                    "foil_depends_bonding_and_assembly": (
                        any("return_face_bonding" in d for d in deps)
                        and any("assembly_letters" in d for d in deps)
                    ),
                    "operational_task_ids": [t.get("task_id") for t in ops],
                }
        if reality_table:
            entry["reality_rows"] = cur.execute(
                f"select count(*) from {reality_table} where order_id=?",
                (oid,),
            ).fetchone()[0]
        report[str(oid)] = entry

    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = {
        k: {
            "accepted": (v.get("order") or {}).get("accepted_commercial_total"),
            "sha_prefix": (v.get("order") or {}).get("snapshot_sha_prefix"),
            "ops": (v.get("plan") or {}).get("operational_tasks"),
            "created": (v.get("plan") or {}).get("execution_tasks_created"),
            "reality": v.get("reality_rows"),
            "foil_ok": (v.get("plan") or {}).get("foil_depends_bonding_and_assembly"),
            "assign": (v.get("plan") or {}).get("assigned_employee_nonzero"),
            "machines": (v.get("plan") or {}).get("machine_code_nonzero"),
        }
        for k, v in report.items()
        if k.isdigit()
    }
    print(json.dumps(summary, indent=2))
    con.close()


if __name__ == "__main__":
    main()
