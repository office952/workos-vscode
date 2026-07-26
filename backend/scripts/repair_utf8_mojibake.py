"""Dry-run / apply confirmed UTF-8 mojibake repairs for local/dev WorkOS data.

Usage:
  python scripts/repair_utf8_mojibake.py --dry-run
  python scripts/repair_utf8_mojibake.py --backup
  python scripts/repair_utf8_mojibake.py --apply-sources
  python scripts/repair_utf8_mojibake.py --apply-db

Does NOT repair frozen commercial snapshot columns unless --include-frozen is set
(owner gate required). Never commits DB files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from core.utf8_text_integrity import (  # noqa: E402
    TextClass,
    has_suspicious_mojibake,
    repair_source_text,
    walk_repair_json,
)

DEFAULT_DB = BACKEND / "dev.db"
EVIDENCE_DIR = REPO / "docs" / "qa" / "utf8-romanian-diacritics-2026-07-17"

# Authoritative operator-visible sources (mixed clean/corrupt).
SOURCE_FILES: Sequence[Path] = (
    BACKEND / "seeds" / "seed_build4_templates.py",
    BACKEND / "services" / "intake_v6_workspace_service.py",
    BACKEND / "tests" / "test_volumetric_operation_unit_pricing.py",
    BACKEND / "tests" / "test_volumetric_lighting_gate.py",
    BACKEND / "tests" / "test_volumetric_qc_internal_only.py",
    BACKEND / "tests" / "test_volumetric_finish_mounting_pricing.py",
    REPO / "frontend" / "src" / "pages" / "ProductSystem.tsx",
    REPO / "frontend" / "src" / "lib" / "intakeV6" / "intakeV6WorkspaceCache.ts",
)

# Local/dev repair targets (non-frozen).
DB_TARGETS = (
    ("product_templates", "id", ("family_name", "description", "components_json", "operations_json", "required_materials_json", "notes")),
    ("execution_plan", "id", ("tasks_json",)),
)

# Frozen commercial truth — owner gate before apply.
FROZEN_TARGETS = (
    ("quote_snapshots_v2", "id", ("snapshot_json",)),
    ("orders", "id", ("snapshot_v2_json", "readiness_snapshot", "snapshot_line_items")),
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def backup_db(db_path: Path) -> Dict[str, Any]:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = EVIDENCE_DIR / f"dev.db.backup-{ts}"
    shutil.copy2(db_path, dest)
    meta = {
        "original_db_path": str(db_path.resolve()),
        "backup_path": str(dest.resolve()),
        "timestamp_utc": ts,
        "sha256_original": _sha256(db_path),
        "sha256_backup": _sha256(dest),
        "bytes": db_path.stat().st_size,
    }
    meta_path = EVIDENCE_DIR / f"db-backup-{ts}.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def dry_run_sources() -> List[dict]:
    rows: List[dict] = []
    for path in SOURCE_FILES:
        if not path.exists():
            rows.append({"path": str(path), "status": "missing"})
            continue
        original = path.read_text(encoding="utf-8")
        fixed, audit = repair_source_text(original)
        rows.append(
            {
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "repairs": len(audit),
                "changed": fixed != original,
                "samples": audit[:8],
            }
        )
    return rows


def apply_sources() -> List[dict]:
    applied: List[dict] = []
    for path in SOURCE_FILES:
        if not path.exists():
            continue
        original = path.read_text(encoding="utf-8")
        fixed, audit = repair_source_text(original)
        if fixed != original:
            path.write_text(fixed, encoding="utf-8")
            applied.append({"path": str(path.relative_to(REPO)).replace("\\", "/"), "repairs": len(audit)})
    return applied


def _maybe_json(value: str) -> Tuple[Any, bool]:
    text = value.strip()
    if text.startswith("{") or text.startswith("["):
        try:
            return json.loads(value), True
        except json.JSONDecodeError:
            return value, False
    return value, False


def dry_run_table(con: sqlite3.Connection, table: str, pk: str, columns: Sequence[str]) -> List[dict]:
    out: List[dict] = []
    info = {r[1] for r in con.execute(f"pragma table_info({table})")}
    if table not in {r[0] for r in con.execute("select name from sqlite_master where type='table'")}:
        return [{"table": table, "status": "missing"}]
    for col in columns:
        if col not in info:
            continue
        rows = con.execute(
            f"SELECT {pk}, {col} FROM {table} WHERE typeof({col})='text' AND ("
            f"{col} LIKE '%Ã%' OR {col} LIKE '%Ä%' OR {col} LIKE '%È%' OR {col} LIKE '%â€%' OR {col} LIKE '%Â%')"
        ).fetchall()
        for row_id, value in rows:
            if not isinstance(value, str) or not has_suspicious_mojibake(value):
                continue
            parsed, is_json = _maybe_json(value)
            if is_json:
                fixed, audit = walk_repair_json(parsed)
                if not audit:
                    continue
                out.append(
                    {
                        "table": table,
                        "pk": row_id,
                        "column": col,
                        "confidence": "MOJIBAKE_SINGLE_PASS_CONFIRMED",
                        "repair_passes": 1,
                        "string_repairs": len(audit),
                        "samples": audit[:6],
                        "proposed_json": True,
                    }
                )
            else:
                from core.utf8_text_integrity import safe_repair_text

                repaired, classification = safe_repair_text(value)
                if repaired == value:
                    out.append(
                        {
                            "table": table,
                            "pk": row_id,
                            "column": col,
                            "confidence": classification.text_class.value,
                            "old": value[:200],
                            "proposed": None,
                            "ambiguity_status": "skip",
                        }
                    )
                    continue
                out.append(
                    {
                        "table": table,
                        "pk": row_id,
                        "column": col,
                        "confidence": classification.text_class.value,
                        "repair_passes": classification.passes,
                        "old": value,
                        "proposed": repaired,
                        "ambiguity_status": "ok",
                    }
                )
    return out


def apply_table(con: sqlite3.Connection, table: str, pk: str, columns: Sequence[str]) -> int:
    changes = 0
    info = {r[1] for r in con.execute(f"pragma table_info({table})")}
    for col in columns:
        if col not in info:
            continue
        rows = con.execute(f"SELECT {pk}, {col} FROM {table} WHERE typeof({col})='text'").fetchall()
        for row_id, value in rows:
            if not isinstance(value, str) or not has_suspicious_mojibake(value):
                continue
            parsed, is_json = _maybe_json(value)
            if is_json:
                fixed, audit = walk_repair_json(parsed)
                if not audit:
                    continue
                new_value = json.dumps(fixed, ensure_ascii=False)
                con.execute(f"UPDATE {table} SET {col}=? WHERE {pk}=?", (new_value, row_id))
                changes += 1
            else:
                from core.utf8_text_integrity import safe_repair_text

                repaired, classification = safe_repair_text(value)
                if (
                    classification.text_class
                    in (
                        TextClass.MOJIBAKE_SINGLE_PASS_CONFIRMED,
                        TextClass.MOJIBAKE_DOUBLE_PASS_CONFIRMED,
                    )
                    and repaired != value
                ):
                    con.execute(f"UPDATE {table} SET {col}=? WHERE {pk}=?", (repaired, row_id))
                    changes += 1
    return changes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--backup", action="store_true")
    parser.add_argument("--apply-sources", action="store_true")
    parser.add_argument("--apply-db", action="store_true")
    parser.add_argument("--include-frozen", action="store_true", help="OWNER GATE: also rewrite frozen snapshots")
    args = parser.parse_args()

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    report: Dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "db": str(args.db.resolve()) if args.db.exists() else None,
    }

    if args.backup:
        if not args.db.exists():
            print("DB missing", args.db)
            return 1
        report["backup"] = backup_db(args.db)
        print("BACKUP", json.dumps(report["backup"], indent=2))

    if args.dry_run or not any([args.apply_sources, args.apply_db, args.backup]):
        report["sources"] = dry_run_sources()
        if args.db.exists():
            con = sqlite3.connect(args.db)
            non_frozen: List[dict] = []
            for table, pk, cols in DB_TARGETS:
                non_frozen.extend(dry_run_table(con, table, pk, cols))
            frozen: List[dict] = []
            for table, pk, cols in FROZEN_TARGETS:
                frozen.extend(dry_run_table(con, table, pk, cols))
            report["db_non_frozen"] = non_frozen
            report["db_frozen_gated"] = frozen
            report["frozen_owner_gate_required"] = len(frozen) > 0
            con.close()
        out = EVIDENCE_DIR / "dry-run-report.json"
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print("DRY_RUN_WRITTEN", out)
        print("sources_changed", sum(1 for r in report.get("sources", []) if r.get("changed")))
        print("db_non_frozen_rows", len(report.get("db_non_frozen", [])))
        print("db_frozen_rows_gated", len(report.get("db_frozen_gated", [])))

    if args.apply_sources:
        applied = apply_sources()
        report["sources_applied"] = applied
        print("SOURCES_APPLIED", len(applied))
        for row in applied:
            print(" ", row)

    if args.apply_db:
        if not args.db.exists():
            print("DB missing", args.db)
            return 1
        con = sqlite3.connect(args.db)
        total = 0
        for table, pk, cols in DB_TARGETS:
            n = apply_table(con, table, pk, cols)
            print(f"UPDATED {table}: {n}")
            total += n
        if args.include_frozen:
            for table, pk, cols in FROZEN_TARGETS:
                n = apply_table(con, table, pk, cols)
                print(f"UPDATED_FROZEN {table}: {n}")
                total += n
        else:
            print("FROZEN_SKIPPED (owner gate) — pass --include-frozen to rewrite snapshots")
        con.commit()
        con.close()
        report["db_rows_updated"] = total
        (EVIDENCE_DIR / "apply-db-report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
