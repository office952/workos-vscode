#!/usr/bin/env python3
"""Controlled QA Hybrid C+B FK remediation — REQUIRES Owner GO.

OWNER GO: AUTHORIZE_CONTROLLED_QA_FOREIGN_KEY_DEBT_REMEDIATION
APPROVED_STRATEGY: HYBRID_C_PLUS_B

Mutates backend/dev.db only when --apply is passed and preconditions match.
Creates byte-for-byte backup under backend/_qa_backups/ first.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
QA_DB = BACKEND_ROOT / "dev.db"

FAMILY_A_PLANS = (
    (4, 23099),
    (5, 23150),
)
FAMILY_A_ORDERS = (
    (21099, 21099),
    (22099, 22099),
    (23099, 23099),
    (23150, 23150),
    (29991, 29991),
)
FAMILY_B_AUTH = (
    ("employee_resource_authorizations", 22),
    ("operation_employee_authorizations", 41),
    ("employee_workcenter_authorizations", 26),
    ("employee_skill_authorizations", 36),
)
PROTECTED_ORDERS = (880750, 880811, 973019)
PROTECTED_PLANS = (23, 22, 21)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def schema_fingerprint(con: sqlite3.Connection) -> str:
    rows = [
        {"type": r[0], "name": r[1], "sql": r[2]}
        for r in con.execute(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY 1, 2"
        )
    ]
    return hashlib.sha256(
        json.dumps(rows, sort_keys=True, default=str).encode()
    ).hexdigest()


def fk_rows(con: sqlite3.Connection) -> list[tuple]:
    return list(con.execute("PRAGMA foreign_key_check").fetchall())


def fk_fingerprint(rows: list[tuple]) -> str:
    norm = sorted((str(r[0]), int(r[1]), str(r[2]), int(r[3])) for r in rows)
    return hashlib.sha256(json.dumps(norm).encode()).hexdigest()


def transition_fp(con: sqlite3.Connection) -> str:
    rows = con.execute(
        "SELECT transition_id, execution_plan_id, order_id, task_key, "
        "transition_type, previous_employee_id, new_employee_id, source "
        "FROM execution_task_assignment_transitions ORDER BY transition_id"
    ).fetchall()
    return hashlib.sha256(json.dumps(rows, default=str).encode()).hexdigest()


def protected_baseline(con: sqlite3.Connection) -> dict[str, Any]:
    out: dict[str, Any] = {"orders": {}, "plans": {}}
    for oid in PROTECTED_ORDERS:
        out["orders"][oid] = con.execute(
            "SELECT id, code, status, quote_snapshot_v2_id, updated_at "
            "FROM orders WHERE id=?",
            (oid,),
        ).fetchone()
    out["absent_88002"] = con.execute(
        "SELECT id FROM orders WHERE id=88002"
    ).fetchone()
    for pid in PROTECTED_PLANS:
        row = con.execute(
            "SELECT id, order_id, updated_at, tasks_json FROM execution_plan WHERE id=?",
            (pid,),
        ).fetchone()
        assert row is not None
        tasks = json.loads(row[3] or "{}")
        ops = tasks.get("operational_tasks") or []
        out["plans"][pid] = {
            "id": row[0],
            "order_id": row[1],
            "updated_at": row[2],
            "tasks_sha256": hashlib.sha256((row[3] or "").encode()).hexdigest(),
            "ops": len(ops),
            "assigned": sum(
                1 for t in ops if t.get("assigned_employee_id") is not None
            ),
            "unassigned": sum(
                1 for t in ops if t.get("assigned_employee_id") is None
            ),
        }
    out["transition_count"] = con.execute(
        "SELECT COUNT(*) FROM execution_task_assignment_transitions"
    ).fetchone()[0]
    out["transition_fp"] = transition_fp(con)
    out["emp7_auth"] = {
        tbl: con.execute(f"SELECT COUNT(*) FROM {tbl} WHERE employee_id=7").fetchone()[
            0
        ]
        for tbl in (
            "employee_resource_authorizations",
            "operation_employee_authorizations",
            "employee_workcenter_authorizations",
            "employee_skill_authorizations",
        )
    }
    return out


def assert_preconditions(con: sqlite3.Connection) -> list[tuple]:
    rev = con.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    if rev != "s63_execution_task_assignment_transitions":
        raise SystemExit(f"PRECONDITION_MISMATCH alembic={rev}")

    rs_names = (
        "resource_domain_configurations",
        "execution_task_schedules",
        "execution_task_machine_reservations",
        "execution_task_capacity_allocations",
    )
    tables = {
        r[0]
        for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if any(n in tables for n in rs_names):
        raise SystemExit("PRECONDITION_MISMATCH: Resource State tables present")

    rows = fk_rows(con)
    if len(rows) != 11:
        raise SystemExit(f"PRECONDITION_MISMATCH fk_count={len(rows)} rows={rows}")

    expected = {
        ("execution_plan", 4, "quote_snapshots_v2"),
        ("execution_plan", 5, "quote_snapshots_v2"),
        ("employee_resource_authorizations", 22, "employees"),
        ("orders", 21099, "quote_snapshots_v2"),
        ("orders", 22099, "quote_snapshots_v2"),
        ("orders", 23099, "quote_snapshots_v2"),
        ("orders", 23150, "quote_snapshots_v2"),
        ("orders", 29991, "quote_snapshots_v2"),
        ("operation_employee_authorizations", 41, "employees"),
        ("employee_workcenter_authorizations", 26, "employees"),
        ("employee_skill_authorizations", 36, "employees"),
    }
    got = {(r[0], int(r[1]), r[2]) for r in rows}
    if got != expected:
        raise SystemExit(f"PRECONDITION_MISMATCH inventory got={got}")

    if con.execute("SELECT id FROM employees WHERE id=9").fetchone():
        raise SystemExit("PRECONDITION_MISMATCH: employee 9 present")

    for pid, snap in FAMILY_A_PLANS:
        row = con.execute(
            "SELECT source_quote_snapshot_v2_id FROM execution_plan WHERE id=?",
            (pid,),
        ).fetchone()
        if not row or row[0] != snap:
            raise SystemExit(f"PRECONDITION_MISMATCH plan {pid}: {row}")
        if con.execute(
            "SELECT id FROM quote_snapshots_v2 WHERE id=?", (snap,)
        ).fetchone():
            raise SystemExit(f"PRECONDITION_MISMATCH snapshot {snap} exists")

    for oid, snap in FAMILY_A_ORDERS:
        row = con.execute(
            "SELECT quote_snapshot_v2_id FROM orders WHERE id=?", (oid,)
        ).fetchone()
        if not row or row[0] != snap:
            raise SystemExit(f"PRECONDITION_MISMATCH order {oid}: {row}")
        if con.execute(
            "SELECT id FROM quote_snapshots_v2 WHERE id=?", (snap,)
        ).fetchone():
            raise SystemExit(f"PRECONDITION_MISMATCH snapshot {snap} exists")

    for tbl, pk in FAMILY_B_AUTH:
        row = con.execute(
            f"SELECT id, employee_id FROM {tbl} WHERE id=?", (pk,)
        ).fetchone()
        if not row or row[1] != 9:
            raise SystemExit(f"PRECONDITION_MISMATCH {tbl} id={pk}: {row}")

    base = protected_baseline(con)
    if base["transition_count"] != 7:
        raise SystemExit(
            f"PRECONDITION_MISMATCH transitions={base['transition_count']}"
        )
    if base["plans"][23]["ops"] != 13 or base["plans"][23]["assigned"] != 1:
        raise SystemExit("PRECONDITION_MISMATCH plan 23 ops/assigned")
    if base["absent_88002"] is not None:
        raise SystemExit("PRECONDITION_MISMATCH order 88002 present")

    return rows


def apply_hybrid(con: sqlite3.Connection) -> dict[str, Any]:
    before = protected_baseline(con)
    before_fp = before["transition_fp"]
    details: dict[str, Any] = {"family_a": [], "family_b": []}

    con.execute("BEGIN IMMEDIATE")
    try:
        for pid, snap in FAMILY_A_PLANS:
            cur = con.execute(
                "UPDATE execution_plan SET source_quote_snapshot_v2_id=NULL "
                "WHERE id=? AND source_quote_snapshot_v2_id=?",
                (pid, snap),
            )
            if cur.rowcount != 1:
                raise SystemExit(
                    f"ROLLBACK: plan nullify id={pid} rowcount={cur.rowcount}"
                )
            details["family_a"].append(
                {
                    "table": "execution_plan",
                    "pk": pid,
                    "nullified_fk": "source_quote_snapshot_v2_id",
                    "was": snap,
                }
            )

        for oid, snap in FAMILY_A_ORDERS:
            cur = con.execute(
                "UPDATE orders SET quote_snapshot_v2_id=NULL "
                "WHERE id=? AND quote_snapshot_v2_id=?",
                (oid, snap),
            )
            if cur.rowcount != 1:
                raise SystemExit(
                    f"ROLLBACK: order nullify id={oid} rowcount={cur.rowcount}"
                )
            details["family_a"].append(
                {
                    "table": "orders",
                    "pk": oid,
                    "nullified_fk": "quote_snapshot_v2_id",
                    "was": snap,
                }
            )

        for tbl, pk in FAMILY_B_AUTH:
            cur = con.execute(
                f"DELETE FROM {tbl} WHERE id=? AND employee_id=9", (pk,)
            )
            if cur.rowcount != 1:
                raise SystemExit(
                    f"ROLLBACK: {tbl} id={pk} delete rowcount={cur.rowcount}"
                )
            details["family_b"].append({"table": tbl, "pk": pk, "employee_id": 9})

        post_fk = fk_rows(con)
        if post_fk:
            raise SystemExit(f"ROLLBACK: fk_check still dirty: {post_fk}")

        after = protected_baseline(con)
        if after["transition_count"] != 7:
            raise SystemExit(
                f"ROLLBACK: transitions became {after['transition_count']}"
            )
        if after["transition_fp"] != before_fp:
            raise SystemExit("ROLLBACK: transition fingerprint changed")
        if after["orders"] != before["orders"]:
            raise SystemExit("ROLLBACK: protected orders changed")
        if after["plans"] != before["plans"]:
            raise SystemExit("ROLLBACK: protected plans changed")
        if after["emp7_auth"] != before["emp7_auth"]:
            raise SystemExit("ROLLBACK: emp7 auth changed")
        if after["absent_88002"] != before["absent_88002"]:
            raise SystemExit("ROLLBACK: 88002 presence changed")

        if len(details["family_a"]) != 7 or len(details["family_b"]) != 4:
            raise SystemExit("ROLLBACK: affected row count mismatch")

        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise

    details["family_a_nullified"] = 7
    details["family_b_deleted"] = 4
    details["fk_after"] = 0
    details["transitions_after"] = 7
    details["transition_fp_after"] = before_fp
    return details


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Mutate QA DB (requires Owner GO and stopped writers)",
    )
    args = parser.parse_args()

    if not QA_DB.exists():
        raise SystemExit(f"QA DB missing: {QA_DB}")

    stamp = time.strftime("%Y%m%d_%H%M%S")
    backup_dir = BACKEND_ROOT / "_qa_backups" / "controlled_fk_hybrid_c_plus_b" / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / "dev.db.pre_hybrid_c_plus_b.bak"

    # Byte-for-byte file copy (writers must be stopped)
    try:
        shutil.copy2(QA_DB, backup_path)
    except OSError as exc:
        raise SystemExit(
            f"STOP: cannot copy QA DB (is backend still open?): {exc}"
        ) from exc

    # Also copy sidecars if present
    for side in (QA_DB.with_suffix(".db-wal"), QA_DB.with_suffix(".db-shm")):
        if side.exists():
            shutil.copy2(side, backup_dir / side.name)

    qa_sha = sha256_file(QA_DB)
    bak_sha = sha256_file(backup_path)
    if qa_sha != bak_sha:
        raise SystemExit("STOP: backup SHA != source SHA")

    # Verify backup opens RO
    bcon = sqlite3.connect(f"file:{backup_path.resolve().as_posix()}?mode=ro", uri=True)
    bcon.execute("PRAGMA query_only=ON")
    bak_schema = schema_fingerprint(bcon)
    bcon.close()

    con = sqlite3.connect(str(QA_DB))
    con.execute("PRAGMA foreign_keys=ON")
    qa_schema = schema_fingerprint(con)
    if qa_schema != bak_schema:
        con.close()
        raise SystemExit("STOP: backup schema fingerprint mismatch")

    report: dict[str, Any] = {
        "strategy": "HYBRID_C_PLUS_B",
        "qa_path": str(QA_DB),
        "backup_path": str(backup_path),
        "qa_sha_before": qa_sha,
        "backup_sha": bak_sha,
        "schema_fp": qa_schema,
        "apply": bool(args.apply),
    }

    try:
        pre_fk = assert_preconditions(con)
        report["fk_before_count"] = len(pre_fk)
        report["fk_before_fp"] = fk_fingerprint(pre_fk)
        report["protected_before"] = protected_baseline(con)
        report["alembic"] = con.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()[0]

        if not args.apply:
            report["status"] = "PRECONDITION_OK_DRY_RUN"
            print(json.dumps(report, indent=2, default=str))
            return 0

        details = apply_hybrid(con)
        report["transaction"] = details
        report["fk_after_count"] = len(fk_rows(con))
        report["protected_after"] = protected_baseline(con)
        report["protected_baseline_diff"] = (
            "NONE"
            if report["protected_before"] == report["protected_after"]
            else "DRIFT"
        )
        if report["protected_baseline_diff"] != "NONE":
            raise SystemExit("POSTCHECK: protected baseline drift after commit")
        if report["fk_after_count"] != 0:
            raise SystemExit("POSTCHECK: fk_check non-zero after commit")
    finally:
        con.close()

    report["qa_sha_after"] = sha256_file(QA_DB)
    report["status"] = "APPLIED"
    out = backup_dir / "apply_report.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))
    print("REPORT", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
