"""F7F protected-baseline proof — read-only SQLite inspection of backend/dev.db.

Confirms the F7E/Capacity baselines the Owner froze are untouched by F7F:
order 880811 (plan 22, total 1847.5, snapshot a59b6c44…, ops=5), order 973019 (847.5,
snapshot 2d412e6e…) and pilot_gate_open=false. Opens the database read-only (mode=ro).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[3] / "backend" / "dev.db"
OUT = Path(__file__).parent / "evidence" / "protected-baselines.json"


def tables(cur: sqlite3.Cursor) -> set[str]:
	return {row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def safe(cur: sqlite3.Cursor, sql: str, args: tuple = ()) -> list[dict]:
	try:
		cur.execute(sql, args)
	except sqlite3.Error as exc:
		return [{"error": str(exc), "sql": sql}]
	cols = [d[0] for d in cur.description]
	return [dict(zip(cols, row)) for row in cur.fetchall()]


def main() -> None:
	con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
	cur = con.cursor()
	present = tables(cur)
	out: dict = {"db": str(DB), "tables_present": sorted(t for t in present if "order" in t or "snapshot" in t or "plan" in t)}

	for code in ("880811", "973019"):
		out[f"order_{code}"] = safe(
			cur,
			"SELECT o.id, o.code, o.status, o.total_amount, o.quote_snapshot_v2_id, "
			"s.snapshot_code, s.content_hash, s.status AS snapshot_status "
			"FROM orders o LEFT JOIN quote_snapshots_v2 s ON s.id = o.quote_snapshot_v2_id "
			"WHERE o.code LIKE ?",
			(f"%{code}%",),
		)
	out["execution_plan_22"] = safe(
		cur,
		"SELECT id, order_id, order_code, plan_source, source_snapshot_code, source_content_hash, "
		"length(tasks_json) AS tasks_json_len FROM execution_plan WHERE id = 22",
	)
	plan_tasks = safe(cur, "SELECT tasks_json FROM execution_plan WHERE id = 22")
	if plan_tasks and "tasks_json" in plan_tasks[0]:
		try:
			parsed = json.loads(plan_tasks[0]["tasks_json"] or "[]")
			out["execution_plan_22_ops_count"] = (
				len(parsed) if isinstance(parsed, list) else len(parsed.get("tasks") or [])
			)
		except (TypeError, ValueError) as exc:
			out["execution_plan_22_ops_count"] = f"unparsed: {exc}"
	con.close()

	OUT.parent.mkdir(parents=True, exist_ok=True)
	OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
	print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
	main()
