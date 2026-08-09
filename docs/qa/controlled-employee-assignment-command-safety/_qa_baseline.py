"""Read-only QA baseline for assignment command safety GO. Never mutates."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[3] / "backend" / "dev.db"
TASK = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:led_install_letters"


def main() -> None:
    c = sqlite3.connect(DB)
    plan = c.execute(
        "SELECT id, order_id, order_code, tasks_json FROM execution_plan WHERE id = 23"
    ).fetchone()
    out: dict = {"db": str(DB), "plan_23": None}
    if plan:
        tj = json.loads(plan[3] or "{}")
        ops = [t for t in (tj.get("operational_tasks") or []) if isinstance(t, dict)]
        assigned = [t for t in ops if t.get("assigned_employee_id") is not None]
        led = next((t for t in ops if t.get("task_id") == TASK), None)
        out["plan_23"] = {
            "id": plan[0],
            "order_id": plan[1],
            "order_code": plan[2],
            "operational_tasks": len(ops),
            "assigned_count": len(assigned),
            "unassigned_count": len(ops) - len(assigned),
            "led_install": {
                "task_id": TASK,
                "assigned_employee_id": (led or {}).get("assigned_employee_id"),
                "workcenter": (led or {}).get("workcenter"),
            },
            "assigned_tasks": [
                {
                    "task_id": t.get("task_id"),
                    "assigned_employee_id": t.get("assigned_employee_id"),
                }
                for t in assigned
            ],
        }
    out["assignment_transitions"] = c.execute(
        "SELECT count(*) FROM execution_task_assignment_transitions"
    ).fetchone()[0]
    out["machine_runs"] = c.execute("SELECT count(*) FROM machine_runs").fetchone()[0]
    out["alembic"] = c.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    session_tables = [
        r[0]
        for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%session%'"
        ).fetchall()
    ]
    out["session_tables"] = session_tables
    for t in session_tables:
        out[f"count_{t}"] = c.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    # machine assignment-ish
    for t in ("execution_task_machine_assignments", "task_machine_assignments"):
        try:
            out[t] = c.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        except sqlite3.Error:
            pass
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
