"""Local/dev cleanup for accidental Product 001/007 template contamination.

Safety rules:
- SQLite local_dev.db only
- backup DB file before mutations
- delete only inactive PRODUCT_001 / PRODUCT_007 style rows
- never delete if referenced by product_families.default_template_id
- idempotent by design
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Candidate:
    id: int
    template_code: str
    family_name: str | None
    active: int | None
    created_at: str | None
    updated_at: str | None
    ref_count: int


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _find_candidates(conn: sqlite3.Connection) -> list[Candidate]:
    cur = conn.cursor()
    cur.execute(
        """
        select id, template_code, family_name, active, created_at, updated_at
        from product_templates
        where upper(template_code) in ('PRODUCT_001', 'PRODUCT-001', 'PRODUCT_007', 'PRODUCT-007')
        order by id
        """
    )
    rows = cur.fetchall()

    candidates: list[Candidate] = []
    for row in rows:
        template_id = int(row["id"])
        cur.execute(
            """
            select count(*) as cnt
            from product_families
            where default_template_id = ?
            """,
            (template_id,),
        )
        ref_count = int(cur.fetchone()["cnt"])
        candidates.append(
            Candidate(
                id=template_id,
                template_code=str(row["template_code"]),
                family_name=row["family_name"],
                active=row["active"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                ref_count=ref_count,
            )
        )
    return candidates


def _is_deletable(c: Candidate) -> bool:
    return int(c.active or 0) == 0 and c.ref_count == 0


def _backup_db(db_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"local_dev_before_product_template_cleanup_{stamp}.db"
    shutil.copy2(db_path, backup_path)
    return backup_path


def run(db_path: Path, apply: bool) -> dict[str, Any]:
    if not db_path.exists():
        raise FileNotFoundError(f"DB file not found: {db_path}")

    conn = _connect(db_path)
    try:
        candidates = _find_candidates(conn)
        deletable = [c for c in candidates if _is_deletable(c)]
        blocked = [c for c in candidates if not _is_deletable(c)]

        report: dict[str, Any] = {
            "db_path": str(db_path),
            "apply": apply,
            "found": [asdict(c) for c in candidates],
            "deletable": [asdict(c) for c in deletable],
            "blocked": [asdict(c) for c in blocked],
            "deleted_ids": [],
            "backup_path": None,
        }

        if apply and deletable:
            backup_path = _backup_db(db_path, db_path.parent / "backups")
            report["backup_path"] = str(backup_path)
            cur = conn.cursor()
            for c in deletable:
                cur.execute("delete from product_templates where id = ?", (c.id,))
                report["deleted_ids"].append(c.id)
            conn.commit()

        return report
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="local_dev.db", help="Path to sqlite DB file")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply cleanup (without this flag script runs in dry-run mode)",
    )
    args = parser.parse_args()

    report = run(Path(args.db), apply=bool(args.apply))
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
