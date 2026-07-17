"""Owner-gated local/dev frozen snapshot UTF-8 restoration.

Encoding restoration only — preserves commercial/structural fingerprint.
Requires explicit --include-frozen. Default dry-run does not mutate.

Usage:
  python scripts/restore_frozen_snapshot_utf8.py --dry-run
  python scripts/restore_frozen_snapshot_utf8.py --backup
  python scripts/restore_frozen_snapshot_utf8.py --apply --include-frozen
  python scripts/restore_frozen_snapshot_utf8.py --verify
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
from typing import Any, Dict, List, Optional, Sequence, Tuple

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from core.utf8_text_integrity import (  # noqa: E402
    TextClass,
    fingerprint_hash,
    has_suspicious_mojibake,
    structural_commercial_fingerprint,
    walk_repair_json,
)

DEFAULT_DB = BACKEND / "dev.db"
EVIDENCE_DIR = REPO / "docs" / "qa" / "utf8-romanian-diacritics-2026-07-17"

FROZEN_TARGETS: Sequence[Tuple[str, str, Sequence[str]]] = (
    ("quote_snapshots_v2", "id", ("snapshot_json",)),
    ("orders", "id", ("snapshot_v2_json", "readiness_snapshot", "snapshot_line_items")),
)

OWNER_GO = "FROZEN SNAPSHOT UTF8 RESTORATION — GO"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_commercial_summary(obj: Any) -> Dict[str, Any]:
    """Pull common commercial identity fields when present (best-effort, read-only)."""
    keys_of_interest = (
        "snapshot_code",
        "snapshot_version",
        "quote_id",
        "order_id",
        "status",
        "template_code",
        "product_template_code",
        "net_total",
        "vat_total",
        "gross_total",
        "total_net",
        "total_vat",
        "total_gross",
        "subtotal",
        "vat",
        "total",
        "currency",
    )
    found: Dict[str, Any] = {}

    def walk(node: Any, path: str = "$") -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if k in keys_of_interest and not isinstance(v, (dict, list)):
                    found[f"{path}.{k}"] = v
                walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node[:50]):
                walk(v, f"{path}[{i}]")

    walk(obj)
    return found


def classify_row(audit: List[dict]) -> str:
    if not audit:
        return "CLEAN"
    classes = {a.get("class") for a in audit}
    if classes <= {
        TextClass.MOJIBAKE_SINGLE_PASS_CONFIRMED.value,
        TextClass.MOJIBAKE_DOUBLE_PASS_CONFIRMED.value,
    }:
        return "CONFIRMED_SAFE"
    if TextClass.AMBIGUOUS.value in classes or TextClass.UNRECOVERABLE.value in classes:
        return "AMBIGUOUS"
    return "SKIPPED"


def inventory_frozen(con: sqlite3.Connection) -> List[dict]:
    rows_out: List[dict] = []
    for table, pk, columns in FROZEN_TARGETS:
        info = {r[1] for r in con.execute(f"pragma table_info({table})")}
        # enrich quote snapshot meta when available
        extra_cols = []
        if table == "quote_snapshots_v2":
            for c in ("snapshot_code", "snapshot_version", "quote_id", "status"):
                if c in info:
                    extra_cols.append(c)
        if table == "orders":
            for c in ("quote_id", "status", "order_code"):
                if c in info:
                    extra_cols.append(c)

        for col in columns:
            if col not in info:
                continue
            select_cols = ", ".join([pk, col] + extra_cols)
            q = f"SELECT {select_cols} FROM {table} WHERE typeof({col})='text'"
            for row in con.execute(q):
                row_id = row[0]
                value = row[1]
                meta = {extra_cols[i]: row[2 + i] for i in range(len(extra_cols))}
                if not isinstance(value, str) or not value.strip():
                    continue
                if not (value.strip().startswith("{") or value.strip().startswith("[")):
                    if has_suspicious_mojibake(value):
                        rows_out.append(
                            {
                                "table": table,
                                "pk": row_id,
                                "column": col,
                                "meta": meta,
                                "classification": "AMBIGUOUS",
                                "reason": "non_json_text_with_suspicion",
                                "string_repairs": 0,
                                "samples": [],
                            }
                        )
                    continue
                try:
                    parsed = json.loads(value)
                except json.JSONDecodeError:
                    rows_out.append(
                        {
                            "table": table,
                            "pk": row_id,
                            "column": col,
                            "meta": meta,
                            "classification": "UNRECOVERABLE",
                            "reason": "invalid_json",
                            "string_repairs": 0,
                        }
                    )
                    continue

                if not has_suspicious_mojibake(value):
                    continue

                fixed, audit = walk_repair_json(parsed)
                classification = classify_row(audit)
                payload_bytes = value.encode("utf-8")
                rows_out.append(
                    {
                        "table": table,
                        "pk": row_id,
                        "column": col,
                        "meta": meta,
                        "classification": classification,
                        "string_repairs": len(audit),
                        "repair_passes": max((a.get("passes") or 1) for a in audit) if audit else 0,
                        "confidence": audit[0]["class"] if audit else "CLEAN",
                        "samples": [
                            {
                                "path": a["path"],
                                "before": a["old"],
                                "after": a["new"],
                                "class": a["class"],
                                "passes": a["passes"],
                            }
                            for a in audit[:12]
                        ],
                        "all_paths": [a["path"] for a in audit],
                        "payload_sha256_before": _sha256_bytes(payload_bytes),
                        "fingerprint_before": fingerprint_hash(parsed),
                        "fingerprint_after_preview": fingerprint_hash(fixed),
                        "fingerprint_match_preview": fingerprint_hash(parsed) == fingerprint_hash(fixed),
                        "commercial_summary_before": extract_commercial_summary(parsed),
                        "commercial_summary_after_preview": extract_commercial_summary(fixed),
                    }
                )
    return rows_out


def backup_db(db_path: Path) -> Dict[str, Any]:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = EVIDENCE_DIR / f"dev.db.frozen-backup-{ts}"
    shutil.copy2(db_path, dest)
    # verify open
    con = sqlite3.connect(dest)
    tables = [r[0] for r in con.execute("select name from sqlite_master where type='table'")]
    con.close()
    meta = {
        "original_db_path": str(db_path.resolve()),
        "backup_path": str(dest.resolve()),
        "timestamp_utc": ts,
        "bytes": db_path.stat().st_size,
        "sha256_original": _sha256_file(db_path),
        "sha256_backup": _sha256_file(dest),
        "backup_open_ok": "quote_snapshots_v2" in tables and "orders" in tables,
        "owner_go": OWNER_GO,
    }
    (EVIDENCE_DIR / f"frozen-db-backup-{ts}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def apply_confirmed(con: sqlite3.Connection, inventory: List[dict]) -> List[dict]:
    applied: List[dict] = []
    for item in inventory:
        if item["classification"] != "CONFIRMED_SAFE":
            continue
        if not item.get("fingerprint_match_preview", False):
            raise RuntimeError(
                f"SEMANTIC_OR_STRUCTURAL_DRIFT preview for {item['table']} pk={item['pk']} col={item['column']}"
            )
        table, pk, col, row_id = item["table"], "id", item["column"], item["pk"]
        value = con.execute(f"SELECT {col} FROM {table} WHERE id=?", (row_id,)).fetchone()[0]
        parsed = json.loads(value)
        before_fp = fingerprint_hash(parsed)
        before_sha = _sha256_bytes(value.encode("utf-8"))
        fixed, audit = walk_repair_json(parsed)
        after_fp = fingerprint_hash(fixed)
        if before_fp != after_fp:
            raise RuntimeError(f"SEMANTIC_OR_STRUCTURAL_DRIFT on apply {table}/{row_id}/{col}")
        new_value = json.dumps(fixed, ensure_ascii=False)
        con.execute(f"UPDATE {table} SET {col}=? WHERE id=?", (new_value, row_id))
        applied.append(
            {
                "table": table,
                "pk": row_id,
                "column": col,
                "string_repairs": len(audit),
                "paths": [a["path"] for a in audit],
                "payload_sha256_before": before_sha,
                "payload_sha256_after": _sha256_bytes(new_value.encode("utf-8")),
                "fingerprint": before_fp,
                "fingerprint_unchanged": True,
                "commercial_summary": extract_commercial_summary(fixed),
                "samples": [
                    {"path": a["path"], "before": a["old"], "after": a["new"]} for a in audit[:8]
                ],
            }
        )
    return applied


def verify_post(con: sqlite3.Connection) -> Dict[str, Any]:
    inv = inventory_frozen(con)
    repairable = [r for r in inv if r["classification"] == "CONFIRMED_SAFE"]
    ambiguous = [r for r in inv if r["classification"] in ("AMBIGUOUS", "UNRECOVERABLE", "SKIPPED")]
    return {
        "remaining_confirmed_safe": len(repairable),
        "remaining_ambiguous": ambiguous,
        "idempotent": len(repairable) == 0,
        "inventory_after": inv,
    }


def lineage_check(con: sqlite3.Connection) -> Dict[str, Any]:
    """Build 1 continuity: quote 3 / QSN2-2026-0002 / order 92402 labels align."""
    qrow = con.execute(
        "SELECT id, snapshot_code, quote_id, snapshot_json FROM quote_snapshots_v2 WHERE snapshot_code=? OR quote_id=3",
        ("QSN2-2026-0002",),
    ).fetchall()
    orow = con.execute(
        "SELECT id, quote_id, snapshot_v2_json FROM orders WHERE id=92402"
    ).fetchone()
    result: Dict[str, Any] = {"quote_rows": [], "order_92402": None, "aligned_labels": None}

    def labels(payload: dict) -> List[str]:
        out: List[str] = []
        pd = payload.get("product_definition_snapshot") or {}
        for key in ("material_roles", "operation_roles"):
            for item in pd.get(key) or []:
                if isinstance(item, dict) and isinstance(item.get("label"), str):
                    out.append(item["label"])
        return out

    quote_labels: Optional[List[str]] = None
    for r in qrow:
        payload = json.loads(r[3])
        labs = labels(payload)
        result["quote_rows"].append(
            {
                "id": r[0],
                "snapshot_code": r[1],
                "quote_id": r[2],
                "label_count": len(labs),
                "has_mojibake": has_suspicious_mojibake(r[3]),
                "sample_labels": labs[:6],
            }
        )
        if r[1] == "QSN2-2026-0002" or r[2] == 3:
            quote_labels = labs

    if orow:
        op = json.loads(orow[2]) if orow[2] else {}
        olabs = labels(op)
        result["order_92402"] = {
            "id": orow[0],
            "quote_id": orow[1],
            "label_count": len(olabs),
            "has_mojibake": has_suspicious_mojibake(orow[2] or ""),
            "sample_labels": olabs[:6],
        }
        if quote_labels is not None:
            result["aligned_labels"] = quote_labels == olabs
            result["quote_vs_order_diff"] = sorted(set(quote_labels) ^ set(olabs))[:20]
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--backup", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--include-frozen", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    if not args.db.exists():
        print("DB missing", args.db)
        return 1

    con = sqlite3.connect(args.db)
    report: Dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "owner_go": OWNER_GO,
        "db": str(args.db.resolve()),
        "scope": "local_dev_frozen_snapshots_only",
    }

    inv = inventory_frozen(con)
    confirmed = [r for r in inv if r["classification"] == "CONFIRMED_SAFE"]
    ambiguous = [r for r in inv if r["classification"] != "CONFIRMED_SAFE"]
    drift = [r for r in confirmed if not r.get("fingerprint_match_preview")]

    report["inventory"] = inv
    report["confirmed_safe_count"] = len(confirmed)
    report["ambiguous_or_other"] = ambiguous
    report["fingerprint_drift_preview"] = drift

    if args.dry_run or not any([args.backup, args.apply, args.verify]):
        out = EVIDENCE_DIR / "frozen-snapshot-dry-run.json"
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        fp_doc = {
            "generated_at_utc": report["generated_at_utc"],
            "rows": [
                {
                    "table": r["table"],
                    "pk": r["pk"],
                    "column": r["column"],
                    "meta": r.get("meta"),
                    "payload_sha256_before": r.get("payload_sha256_before"),
                    "fingerprint_before": r.get("fingerprint_before"),
                    "fingerprint_after_preview": r.get("fingerprint_after_preview"),
                    "fingerprint_match_preview": r.get("fingerprint_match_preview"),
                    "commercial_summary_before": r.get("commercial_summary_before"),
                    "string_repairs": r.get("string_repairs"),
                }
                for r in confirmed
            ],
        }
        (EVIDENCE_DIR / "frozen-snapshot-commercial-fingerprint.json").write_text(
            json.dumps(fp_doc, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print("DRY_RUN", out)
        print("confirmed_safe", len(confirmed), "ambiguous", len(ambiguous), "drift", len(drift))
        if drift:
            print("STOP: SEMANTIC_OR_STRUCTURAL_DRIFT in preview")
            con.close()
            return 2

    if args.backup:
        meta = backup_db(args.db)
        report["backup"] = meta
        print("BACKUP", json.dumps(meta, indent=2))
        if not meta.get("backup_open_ok") or meta["sha256_original"] != meta["sha256_backup"]:
            print("BACKUP_OR_ROLLBACK_BLOCKED")
            con.close()
            return 3

    if args.apply:
        if not args.include_frozen:
            print("Refusing apply without --include-frozen (owner gate)")
            con.close()
            return 4
        if drift:
            print("STOP: SEMANTIC_OR_STRUCTURAL_DRIFT")
            con.close()
            return 2
        if ambiguous:
            print("NOTE: ambiguous/non-confirmed rows will be skipped:", len(ambiguous))
        applied = apply_confirmed(con, confirmed)
        con.commit()
        post = verify_post(con)
        lineage = lineage_check(con)
        result = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "owner_go": OWNER_GO,
            "applied_count": len(applied),
            "applied": applied,
            "skipped": ambiguous,
            "verify": post,
            "lineage_build1": lineage,
            "backup": report.get("backup"),
        }
        (EVIDENCE_DIR / "frozen-snapshot-repair-result.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print("APPLIED", len(applied), "idempotent", post["idempotent"])
        print("LINEAGE aligned_labels", lineage.get("aligned_labels"))
        if not post["idempotent"]:
            print("FAIL: remaining confirmed repairs after apply")
            con.close()
            return 5

    if args.verify:
        post = verify_post(con)
        lineage = lineage_check(con)
        print(json.dumps({"verify": post, "lineage": lineage}, indent=2, ensure_ascii=False)[:4000])
        if not post["idempotent"]:
            con.close()
            return 5

    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
