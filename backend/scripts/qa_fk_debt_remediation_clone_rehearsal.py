#!/usr/bin/env python3
"""QA foreign-key debt remediation — isolated clone rehearsal.

Classification:
  NOT_EXECUTED_ON_QA
  ISOLATED_CLONE_VERIFIED (when exit 0)
  OWNER_GO_REQUIRED for real QA remediation

Does NOT mutate backend/dev.db. Copies via sqlite3 backup API only.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

# Ensure backend root is importable when launched as scripts/*.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.schema_ownership import RESOURCE_STATE_TABLES

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
QA_DB = BACKEND_ROOT / "dev.db"

# Canonical FK orphan package (PRE_R5 inventory)
FAMILY_A_ORDERS = (21099, 22099, 23099, 23150, 29991)
FAMILY_A_PLANS = (4, 5)
FAMILY_B_AUTH = (
    ("employee_resource_authorizations", 22),
    ("operation_employee_authorizations", 41),
    ("employee_workcenter_authorizations", 26),
    ("employee_skill_authorizations", 36),
)

# Exact gate-scoped dependents required before deleting plans 4/5 / orders
# (discovered on QA 2026-08-05; asserted at runtime — abort on mismatch).
EXPECTED_HELP_IDS = tuple(range(1, 24))
EXPECTED_PARTICIPANT_IDS = (1, 2, 3)
EXPECTED_GATE_TRANSITION_IDS = (1, 2, 3, 4, 5)  # plans 4 and 5
EXPECTED_STOCK_IDS = (1, 2, 3, 4)
EXPECTED_REALITY_IDS = (1, 2)  # 29991, 23099
EXPECTED_EXTRA_PLAN_IDS = (1,)  # order 29991 soft child; snapshot FK null

PROTECTED_ORDERS = (880750, 880811, 973019)
PROTECTED_PLANS = (23, 22, 21)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
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
    return _sha256_bytes(json.dumps(rows, sort_keys=True, default=str).encode())


def open_ro(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def open_rw(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path))
    con.execute("PRAGMA foreign_keys=ON")
    return con


def backup_db(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    src_con = sqlite3.connect(f"file:{src.resolve().as_posix()}?mode=ro", uri=True)
    src_con.execute("PRAGMA query_only=ON")
    dst_con = sqlite3.connect(str(dst))
    src_con.backup(dst_con)
    dst_con.close()
    src_con.close()


def fk_rows(con: sqlite3.Connection) -> list[tuple]:
    return list(con.execute("PRAGMA foreign_key_check").fetchall())


def fk_fingerprint(rows: list[tuple]) -> str:
    norm = sorted((str(r[0]), int(r[1]), str(r[2]), int(r[3])) for r in rows)
    return _sha256_bytes(json.dumps(norm).encode())


def transition_fingerprint(con: sqlite3.Connection) -> str:
    rows = con.execute(
        "SELECT transition_id, execution_plan_id, order_id, task_key, "
        "transition_type, previous_employee_id, new_employee_id, source "
        "FROM execution_task_assignment_transitions ORDER BY transition_id"
    ).fetchall()
    return _sha256_bytes(json.dumps(rows, default=str).encode())


def protected_transition_fingerprint(con: sqlite3.Connection) -> str:
    rows = con.execute(
        "SELECT transition_id, execution_plan_id, order_id, task_key, "
        "transition_type, previous_employee_id, new_employee_id, source "
        "FROM execution_task_assignment_transitions "
        "WHERE execution_plan_id IN (21,22,23) ORDER BY transition_id"
    ).fetchall()
    return _sha256_bytes(json.dumps(rows, default=str).encode())


def capture_protected_baseline(con: sqlite3.Connection) -> dict[str, Any]:
    out: dict[str, Any] = {"orders": {}, "plans": {}, "absent_88002": None}
    for oid in PROTECTED_ORDERS:
        row = con.execute(
            "SELECT id, code, status, quote_snapshot_v2_id, updated_at "
            "FROM orders WHERE id=?",
            (oid,),
        ).fetchone()
        out["orders"][oid] = row
    out["absent_88002"] = con.execute(
        "SELECT id FROM orders WHERE id=88002"
    ).fetchone()
    for pid in PROTECTED_PLANS:
        row = con.execute(
            "SELECT id, order_id, updated_at, tasks_json FROM execution_plan WHERE id=?",
            (pid,),
        ).fetchone()
        assert row is not None, f"missing protected plan {pid}"
        tasks = json.loads(row[3] or "{}")
        ops = tasks.get("operational_tasks") or []
        assigned = [t for t in ops if t.get("assigned_employee_id") is not None]
        unassigned = [t for t in ops if t.get("assigned_employee_id") is None]
        led = [
            t
            for t in ops
            if "led_install" in str(t.get("task_id") or "").lower()
            or "LED" in str(t.get("operation_code") or t.get("name") or "")
        ]
        out["plans"][pid] = {
            "id": row[0],
            "order_id": row[1],
            "updated_at": row[2],
            "tasks_sha256": _sha256_bytes((row[3] or "").encode()),
            "ops_count": len(ops),
            "assigned": len(assigned),
            "unassigned": len(unassigned),
            "led_employee_ids": [t.get("assigned_employee_id") for t in led],
        }
    out["transition_count"] = con.execute(
        "SELECT COUNT(*) FROM execution_task_assignment_transitions"
    ).fetchone()[0]
    out["transition_fp"] = transition_fingerprint(con)
    out["protected_transition_fp"] = protected_transition_fingerprint(con)
    out["protected_transition_count"] = con.execute(
        "SELECT COUNT(*) FROM execution_task_assignment_transitions "
        "WHERE execution_plan_id IN (21,22,23)"
    ).fetchone()[0]
    # employee 7 auth counts
    out["emp7_auth"] = {}
    for tbl in (
        "employee_resource_authorizations",
        "operation_employee_authorizations",
        "employee_workcenter_authorizations",
        "employee_skill_authorizations",
    ):
        out["emp7_auth"][tbl] = con.execute(
            f"SELECT COUNT(*) FROM {tbl} WHERE employee_id=7"
        ).fetchone()[0]
    # quote snapshot refs for protected orders
    out["protected_snapshots"] = {}
    for oid in PROTECTED_ORDERS:
        sid = con.execute(
            "SELECT quote_snapshot_v2_id FROM orders WHERE id=?", (oid,)
        ).fetchone()[0]
        exists = con.execute(
            "SELECT id FROM quote_snapshots_v2 WHERE id=?", (sid,)
        ).fetchone()
        out["protected_snapshots"][oid] = {"snapshot_id": sid, "exists": bool(exists)}
    return out


def assert_expected_orphan_inventory(con: sqlite3.Connection) -> list[tuple]:
    rows = fk_rows(con)
    if len(rows) != 11:
        raise SystemExit(f"EXPECTED 11 FK violations, got {len(rows)}: {rows}")
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
        raise SystemExit(f"FK inventory mismatch:\n got={got}\n exp={expected}")
    return rows


def assert_dependent_pks(con: sqlite3.Connection) -> None:
    help_ids = tuple(
        r[0]
        for r in con.execute(
            "SELECT id FROM execution_task_help_requests "
            "WHERE execution_plan_id=4 ORDER BY id"
        )
    )
    part_ids = tuple(
        r[0]
        for r in con.execute(
            "SELECT id FROM execution_task_participants "
            "WHERE execution_plan_id=4 ORDER BY id"
        )
    )
    tr_ids = tuple(
        r[0]
        for r in con.execute(
            "SELECT id FROM execution_task_assignment_transitions "
            "WHERE execution_plan_id IN (4,5) ORDER BY id"
        )
    )
    stock_ids = tuple(
        r[0]
        for r in con.execute(
            "SELECT id FROM stock_movements WHERE order_id=23099 ORDER BY id"
        )
    )
    reality_ids = tuple(
        r[0]
        for r in con.execute(
            "SELECT id FROM execution_reality "
            "WHERE order_id IN (23099,29991) ORDER BY id"
        )
    )
    plan1 = tuple(
        r[0] for r in con.execute("SELECT id FROM execution_plan WHERE id=1")
    )
    checks = [
        ("help", help_ids, EXPECTED_HELP_IDS),
        ("participants", part_ids, EXPECTED_PARTICIPANT_IDS),
        ("gate_transitions", tr_ids, EXPECTED_GATE_TRANSITION_IDS),
        ("stock", stock_ids, EXPECTED_STOCK_IDS),
        ("reality", reality_ids, EXPECTED_REALITY_IDS),
        ("plan1", plan1, EXPECTED_EXTRA_PLAN_IDS),
    ]
    for name, got, exp in checks:
        if got != exp:
            raise SystemExit(f"Dependent PK mismatch {name}: got={got} exp={exp}")


def prove_pure_seven_delete_blocked(clone: Path) -> dict[str, Any]:
    """Copy clone → temp; try deleting only the 7 FK rows; expect failure."""
    tmp = clone.with_name(clone.stem + "_pure7_probe.db")
    shutil.copy2(clone, tmp)
    con = open_rw(tmp)
    con.execute("BEGIN IMMEDIATE")
    err: str | None = None
    try:
        con.execute("DELETE FROM execution_plan WHERE id IN (4,5)")
        con.execute(
            "DELETE FROM orders WHERE id IN (21099,22099,23099,23150,29991)"
        )
        for tbl, pk in FAMILY_B_AUTH:
            con.execute(f"DELETE FROM {tbl} WHERE id=?", (pk,))
        con.execute("COMMIT")
    except sqlite3.IntegrityError as exc:
        con.execute("ROLLBACK")
        err = str(exc)
    finally:
        con.close()
        tmp.unlink(missing_ok=True)
    return {
        "pure_seven_delete_blocked": err is not None,
        "error": err,
    }


def apply_expanded_option_d(con: sqlite3.Connection) -> dict[str, int]:
    """Single transaction: exact PK deletes for Family A deps + orphans + Family B."""
    assert_expected_orphan_inventory(con)
    assert_dependent_pks(con)
    # preconditions
    if con.execute("SELECT id FROM employees WHERE id=9").fetchone():
        raise SystemExit("employees.id=9 unexpectedly present")
    for sid in FAMILY_A_ORDERS:
        if con.execute(
            "SELECT id FROM quote_snapshots_v2 WHERE id=?", (sid,)
        ).fetchone():
            raise SystemExit(f"snapshot parent {sid} unexpectedly present")

    counts: dict[str, int] = {}
    con.execute("BEGIN IMMEDIATE")
    try:
        # Family A prerequisites (gate-scoped exact PKs)
        cur = con.execute(
            "DELETE FROM execution_task_help_requests WHERE id BETWEEN 1 AND 23 "
            "AND execution_plan_id=4"
        )
        counts["help_requests"] = cur.rowcount
        if counts["help_requests"] != 23:
            raise SystemExit(f"help delete count {counts['help_requests']}")

        cur = con.execute(
            "DELETE FROM execution_task_participants WHERE id IN (1,2,3) "
            "AND execution_plan_id=4"
        )
        counts["participants"] = cur.rowcount
        if counts["participants"] != 3:
            raise SystemExit(f"participant delete count {counts['participants']}")

        cur = con.execute(
            "DELETE FROM execution_task_assignment_transitions "
            "WHERE id IN (1,2,3,4,5) AND execution_plan_id IN (4,5)"
        )
        counts["gate_transitions"] = cur.rowcount
        if counts["gate_transitions"] != 5:
            raise SystemExit(f"gate transition delete count {counts['gate_transitions']}")

        cur = con.execute(
            "DELETE FROM stock_movements WHERE id IN (1,2,3,4) AND order_id=23099"
        )
        counts["stock_movements"] = cur.rowcount
        if counts["stock_movements"] != 4:
            raise SystemExit(f"stock delete count {counts['stock_movements']}")

        cur = con.execute(
            "DELETE FROM execution_reality WHERE id IN (1,2) "
            "AND order_id IN (23099,29991)"
        )
        counts["execution_reality"] = cur.rowcount
        if counts["execution_reality"] != 2:
            raise SystemExit(f"reality delete count {counts['execution_reality']}")

        # Extra soft child plan for order 29991 (not in FK check; required for order delete hygiene)
        cur = con.execute(
            "DELETE FROM execution_plan WHERE id=1 AND order_id=29991 "
            "AND source_quote_snapshot_v2_id IS NULL"
        )
        counts["extra_plan_1"] = cur.rowcount
        if counts["extra_plan_1"] != 1:
            raise SystemExit(f"plan1 delete count {counts['extra_plan_1']}")

        # Family A orphan rows (the 7 FK violators)
        cur = con.execute(
            "DELETE FROM execution_plan WHERE id IN (4,5) "
            "AND order_id IN (23099,23150)"
        )
        counts["family_a_plans"] = cur.rowcount
        if counts["family_a_plans"] != 2:
            raise SystemExit(f"family A plan delete count {counts['family_a_plans']}")

        cur = con.execute(
            "DELETE FROM orders WHERE id IN (21099,22099,23099,23150,29991) "
            "AND quote_snapshot_v2_id IN (21099,22099,23099,23150,29991)"
        )
        counts["family_a_orders"] = cur.rowcount
        if counts["family_a_orders"] != 5:
            raise SystemExit(f"family A order delete count {counts['family_a_orders']}")

        # Family B
        b_total = 0
        for tbl, pk in FAMILY_B_AUTH:
            cur = con.execute(
                f"DELETE FROM {tbl} WHERE id=? AND employee_id=9", (pk,)
            )
            if cur.rowcount != 1:
                raise SystemExit(f"{tbl} id={pk} delete count {cur.rowcount}")
            b_total += cur.rowcount
        counts["family_b_auth"] = b_total

        post = fk_rows(con)
        if post:
            raise SystemExit(f"FK check still dirty after deletes: {post}")

        # protected quick assert inside txn
        if (
            con.execute(
                "SELECT COUNT(*) FROM execution_task_assignment_transitions "
                "WHERE execution_plan_id=23"
            ).fetchone()[0]
            != 1
        ):
            raise SystemExit("plan 23 transition missing after remediation")

        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    return counts


def apply_hybrid_option_c_plus_b(con: sqlite3.Connection) -> dict[str, int]:
    """Alternative: nullify Family A snapshot FKs + delete Family B."""
    assert_expected_orphan_inventory(con)
    counts: dict[str, int] = {}
    con.execute("BEGIN IMMEDIATE")
    try:
        cur = con.execute(
            "UPDATE execution_plan SET source_quote_snapshot_v2_id=NULL "
            "WHERE id IN (4,5) AND source_quote_snapshot_v2_id IN (23099,23150)"
        )
        counts["nullify_plans"] = cur.rowcount
        cur = con.execute(
            "UPDATE orders SET quote_snapshot_v2_id=NULL "
            "WHERE id IN (21099,22099,23099,23150,29991) "
            "AND quote_snapshot_v2_id IN (21099,22099,23099,23150,29991)"
        )
        counts["nullify_orders"] = cur.rowcount
        b_total = 0
        for tbl, pk in FAMILY_B_AUTH:
            cur = con.execute(
                f"DELETE FROM {tbl} WHERE id=? AND employee_id=9", (pk,)
            )
            if cur.rowcount != 1:
                raise SystemExit(f"{tbl} id={pk} delete count {cur.rowcount}")
            b_total += cur.rowcount
        counts["family_b_auth"] = b_total
        post = fk_rows(con)
        if post:
            raise SystemExit(f"hybrid FK still dirty: {post}")
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    return counts


def alembic_upgrade_clone(clone: Path) -> None:
    env = os.environ.copy()
    env["APP_ENV"] = "test"
    env["ENVIRONMENT"] = "test"
    env["DATABASE_URL"] = f"sqlite+aiosqlite:///{clone.resolve().as_posix()}"
    # alembic.ini sqlalchemy.url empty — env.py reads DATABASE_URL
    cmd = [
        str(BACKEND_ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "alembic",
        "upgrade",
        "s64_resource_state_persistence",
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(BACKEND_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(
            f"alembic upgrade failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )


def rs_zero_proof(con: sqlite3.Connection) -> dict[str, int]:
    out: dict[str, int] = {}
    tables = {
        r[0]
        for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    for name in sorted(RESOURCE_STATE_TABLES):
        if name not in tables:
            out[name] = -1
        else:
            out[name] = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
    return out


def runtime_smoke(clone: Path, port: int) -> dict[str, Any]:
    """Start isolated uvicorn against clone; read-only health + order/plan reads."""
    py = BACKEND_ROOT / ".venv" / "Scripts" / "python.exe"
    env = os.environ.copy()
    env["APP_ENV"] = "test"
    env["ENVIRONMENT"] = "test"
    env["DATABASE_URL"] = f"sqlite+aiosqlite:///{clone.resolve().as_posix()}"
    env["JWT_SECRET_KEY"] = "clone-rehearsal-secret-not-for-production"
    log_dir = REPO_ROOT / ".workos-dev-logs"
    log_dir.mkdir(exist_ok=True)
    out_log = log_dir / f"fk-rehearsal-be-{port}.out.log"
    err_log = log_dir / f"fk-rehearsal-be-{port}.err.log"
    with out_log.open("w", encoding="utf-8") as out_f, err_log.open(
        "w", encoding="utf-8"
    ) as err_f:
        proc = subprocess.Popen(
            [
                str(py),
                "-m",
                "uvicorn",
                "main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=str(BACKEND_ROOT),
            env=env,
            stdout=out_f,
            stderr=err_f,
        )
    result: dict[str, Any] = {
        "pid": proc.pid,
        "port": port,
        "db": str(clone),
        "served_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), text=True
        ).strip(),
    }
    try:
        import urllib.request

        health_ok = False
        body = ""
        for _ in range(40):
            time.sleep(0.5)
            if proc.poll() is not None:
                result["startup"] = "FAILED"
                result["exit"] = proc.returncode
                result["err_tail"] = err_log.read_text(encoding="utf-8", errors="replace")[
                    -2000:
                ]
                return result
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/health", timeout=2
                ) as resp:
                    body = resp.read().decode()
                    health_ok = resp.status == 200
                    break
            except Exception:
                continue
        result["startup"] = "OK" if health_ok else "TIMEOUT"
        result["health_body"] = body
        # FK pragma via direct sqlite on same file while server runs
        c = open_ro(clone)
        result["foreign_keys"] = c.execute("PRAGMA foreign_keys").fetchone()[0]
        result["fk_check_count"] = len(fk_rows(c))
        # protected reads
        o = c.execute(
            "SELECT id, code, status FROM orders WHERE id=880750"
        ).fetchone()
        p = c.execute(
            "SELECT id, order_id FROM execution_plan WHERE id=23"
        ).fetchone()
        e7 = c.execute(
            "SELECT COUNT(*) FROM employee_resource_authorizations WHERE employee_id=7"
        ).fetchone()[0]
        result["read_order_880750"] = o
        result["read_plan_23"] = p
        result["read_emp7_resource_auth_count"] = e7
        # Phase B readiness style: no RS config rows
        rs = rs_zero_proof(c)
        result["rs_counts"] = rs
        c.close()
        # optional HTTP order route if present
        for path in (
            "/api/orders/880750",
            "/orders/880750",
            "/api/v1/orders/880750",
        ):
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}{path}", timeout=2
                ) as resp:
                    result["http_order_probe"] = {
                        "path": path,
                        "status": resp.status,
                    }
                    break
            except Exception as exc:
                result.setdefault("http_order_probes", []).append(
                    {"path": path, "error": type(exc).__name__}
                )
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    return result


def remediation_result_fingerprint(con: sqlite3.Connection) -> str:
    payload = {
        "fk": fk_rows(con),
        "orders_gone": [
            r[0]
            for r in con.execute(
                "SELECT id FROM orders WHERE id IN (21099,22099,23099,23150,29991)"
            )
        ],
        "plans_gone": [
            r[0]
            for r in con.execute(
                "SELECT id FROM execution_plan WHERE id IN (1,4,5)"
            )
        ],
        "emp9_auth": {
            tbl: con.execute(
                f"SELECT COUNT(*) FROM {tbl} WHERE employee_id=9"
            ).fetchone()[0]
            for tbl, _ in FAMILY_B_AUTH
        },
        "transition_count": con.execute(
            "SELECT COUNT(*) FROM execution_task_assignment_transitions"
        ).fetchone()[0],
        "protected": capture_protected_baseline(con),
    }
    return _sha256_bytes(json.dumps(payload, sort_keys=True, default=str).encode())


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="qa_fk_remediation_rehearsal_"))
    # Prefer repo-local ignored location if present
    preferred = BACKEND_ROOT / "_qa_backups" / "fk_debt_remediation_rehearsal"
    preferred.mkdir(parents=True, exist_ok=True)
    work = preferred / time.strftime("%Y%m%d_%H%M%S")
    work.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "classification": [
            "NOT_EXECUTED_ON_QA",
            "ISOLATED_CLONE_VERIFIED_PENDING",
            "OWNER_GO_REQUIRED",
        ],
        "work_dir": str(work),
        "qa_path": str(QA_DB),
    }

    # Source identity via backup (handles locked QA file)
    source_copy = work / "qa_source_backup.db"
    backup_db(QA_DB, source_copy)
    report["qa_sha_via_backup"] = _sha256_file(source_copy)

    src = open_ro(source_copy)
    report["qa_alembic"] = src.execute(
        "SELECT version_num FROM alembic_version"
    ).fetchone()[0]
    report["qa_schema_fp"] = schema_fingerprint(src)
    pre_fk = assert_expected_orphan_inventory(src)
    report["fk_before_count"] = len(pre_fk)
    report["fk_before_fp"] = fk_fingerprint(pre_fk)
    report["fk_before_rows"] = [
        {"table": r[0], "rowid": r[1], "parent": r[2], "fkid": r[3]} for r in pre_fk
    ]
    baseline_before = capture_protected_baseline(src)
    report["protected_baseline_before"] = baseline_before
    assert_dependent_pks(src)
    src.close()

    # Clone for expanded D
    clone = work / "clone_expanded_d.db"
    shutil.copy2(source_copy, clone)
    report["clone_initial_sha"] = _sha256_file(clone)
    if report["clone_initial_sha"] != report["qa_sha_via_backup"]:
        raise SystemExit("clone SHA != source backup SHA")

    # Pre-remediation snapshot for rollback rehearsal
    pre_remediation = work / "clone_pre_remediation.db"
    shutil.copy2(clone, pre_remediation)

    pure = prove_pure_seven_delete_blocked(clone)
    report["pure_seven_probe"] = pure
    if not pure["pure_seven_delete_blocked"]:
        raise SystemExit("expected pure 7-row delete to be blocked by RESTRICT")

    # Apply expanded D
    con = open_rw(clone)
    report["fk_pragma_on"] = con.execute("PRAGMA foreign_keys").fetchone()[0]
    counts = apply_expanded_option_d(con)
    report["expanded_d_counts"] = counts
    report["fk_after_count"] = len(fk_rows(con))
    baseline_after = capture_protected_baseline(con)
    report["protected_baseline_after"] = baseline_after

    # Protected plan/order identity must match; global transition count will drop
    for oid in PROTECTED_ORDERS:
        if baseline_before["orders"][oid] != baseline_after["orders"][oid]:
            raise SystemExit(f"protected order drift {oid}")
    for pid in PROTECTED_PLANS:
        b = baseline_before["plans"][pid]
        a = baseline_after["plans"][pid]
        for k in (
            "id",
            "order_id",
            "updated_at",
            "tasks_sha256",
            "ops_count",
            "assigned",
            "unassigned",
            "led_employee_ids",
        ):
            if b[k] != a[k]:
                raise SystemExit(f"protected plan drift {pid}.{k}: {b[k]} -> {a[k]}")
    if baseline_before["absent_88002"] != baseline_after["absent_88002"]:
        raise SystemExit("88002 presence drift")
    if (
        baseline_before["protected_transition_fp"]
        != baseline_after["protected_transition_fp"]
    ):
        raise SystemExit("protected transition fingerprint drift")
    if baseline_before["emp7_auth"] != baseline_after["emp7_auth"]:
        raise SystemExit("emp7 auth drift")
    if baseline_after["transition_count"] != 2:
        raise SystemExit(
            f"expected global transitions 2 after gate cleanup, got "
            f"{baseline_after['transition_count']}"
        )
    report["protected_baseline_diff"] = "NONE_FOR_PROTECTED_SCOPE"
    report["global_transition_count_change"] = {
        "before": baseline_before["transition_count"],
        "after": baseline_after["transition_count"],
        "note": "5 gate-plan transitions removed; protected plans 21/23 unchanged",
    }
    result_fp_1 = remediation_result_fingerprint(con)
    report["remediation_result_fp_1"] = result_fp_1
    alembic_rev = con.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    if alembic_rev != "s63_execution_task_assignment_transitions":
        raise SystemExit(f"unexpected pre-migration rev {alembic_rev}")
    con.close()

    # Hybrid alternative on separate clone (evidence for Owner decision)
    hybrid_clone = work / "clone_hybrid_c_plus_b.db"
    shutil.copy2(source_copy, hybrid_clone)
    hcon = open_rw(hybrid_clone)
    report["hybrid_counts"] = apply_hybrid_option_c_plus_b(hcon)
    report["hybrid_fk_after"] = len(fk_rows(hcon))
    h_base = capture_protected_baseline(hcon)
    report["hybrid_preserves_global_transitions"] = h_base["transition_count"] == 7
    report["hybrid_transition_fp_unchanged"] = (
        h_base["transition_fp"] == baseline_before["transition_fp"]
    )
    hcon.close()

    # s63 → s64 on remediated expanded-D clone
    alembic_upgrade_clone(clone)
    con = open_rw(clone)
    rev = con.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    report["clone_alembic_after_upgrade"] = rev
    if rev != "s64_resource_state_persistence":
        raise SystemExit(f"upgrade did not land on s64: {rev}")
    rs = rs_zero_proof(con)
    report["rs_counts"] = rs
    if any(v != 0 for v in rs.values()):
        raise SystemExit(f"RS tables not empty: {rs}")
    if len(fk_rows(con)) != 0:
        raise SystemExit("FK dirty after s64")
    # protected still stable post-migration
    post_mig = capture_protected_baseline(con)
    for pid in PROTECTED_PLANS:
        if (
            post_mig["plans"][pid]["tasks_sha256"]
            != baseline_after["plans"][pid]["tasks_sha256"]
        ):
            raise SystemExit("tasks_json changed by s64")
    con.close()

    # Runtime smoke on post-s64 clone (isolated port)
    report["runtime_smoke"] = runtime_smoke(clone, port=8017)
    if report["runtime_smoke"].get("startup") != "OK":
        raise SystemExit(f"runtime smoke failed: {report['runtime_smoke']}")
    if report["runtime_smoke"].get("fk_check_count") != 0:
        raise SystemExit("runtime smoke FK check non-zero")

    # Rollback rehearsal: restore pre-remediation copy
    restored = work / "clone_rollback_restored.db"
    shutil.copy2(pre_remediation, restored)
    report["rollback_sha_match"] = _sha256_file(restored) == _sha256_file(
        pre_remediation
    )
    rcon = open_ro(restored)
    report["rollback_fk_count"] = len(assert_expected_orphan_inventory(rcon))
    report["rollback_sha_equals_pre"] = _sha256_file(restored) == report[
        "clone_initial_sha"
    ]
    rcon.close()

    # Determinism: re-apply expanded D on fresh clone from source
    det = work / "clone_determinism_2.db"
    shutil.copy2(source_copy, det)
    dcon = open_rw(det)
    apply_expanded_option_d(dcon)
    result_fp_2 = remediation_result_fingerprint(dcon)
    dcon.close()
    report["remediation_result_fp_2"] = result_fp_2
    report["remediation_deterministic"] = result_fp_1 == result_fp_2

    # QA source unchanged: re-backup and compare
    source_after = work / "qa_source_backup_after.db"
    backup_db(QA_DB, source_after)
    report["qa_sha_after"] = _sha256_file(source_after)
    report["qa_mutations"] = (
        0 if report["qa_sha_after"] == report["qa_sha_via_backup"] else "NONZERO"
    )

    report["classification"] = [
        "NOT_EXECUTED_ON_QA",
        "ISOLATED_CLONE_VERIFIED",
        "OWNER_GO_REQUIRED",
    ]
    report["verdict"] = {
        "QA_FK_DEBT_REMEDIATION_PLANNING": "PASS",
        "ISOLATED_CLONE_REHEARSAL": "VERIFIED",
        "VIOLATIONS_BEFORE": 11,
        "VIOLATIONS_AFTER": 0,
        "RECOMMENDED_EXECUTION_STRATEGY": "EXPANDED_OPTION_D_WITH_EXACT_DEPENDENT_PKS",
        "ALTERNATIVE_STRATEGY": "HYBRID_OPTION_C_FAMILY_A_PLUS_OPTION_D_FAMILY_B",
        "REAL_QA_REMEDIATION": "NOT_AUTHORIZED",
        "R5": "NOT_AUTHORIZED",
    }

    out_json = work / "rehearsal_report.json"
    out_json.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    # also copy summary to scripts-adjacent evidence path under _qa_backups only
    print(json.dumps(report["verdict"], indent=2))
    print("REPORT", out_json)
    print("WORK_DIR", work)
    if report["qa_mutations"] != 0:
        raise SystemExit("QA SHA changed during rehearsal — STOP")
    if not report["remediation_deterministic"]:
        raise SystemExit("remediation not deterministic")
    if not report["rollback_sha_match"]:
        raise SystemExit("rollback rehearsal failed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
