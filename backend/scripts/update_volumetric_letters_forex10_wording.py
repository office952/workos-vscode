"""Idempotent local DB wording update for TPL-VOLUMETRIC-LETTERS (Forex 10 mm backing).

Updates display/reference text only — no material code renames, no formula/pricing changes.

Safe targets:
  - product_templates.template_code = 'TPL-VOLUMETRIC-LETTERS'
  - inventory_materials.code = 'MAT-SPATE-PVC-LITERE'
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS"
MAT_BACK_CODE = "MAT-SPATE-PVC-LITERE"

TARGET_DESCRIPTION = (
    "Litere volumetrice 3D — față plexiglas 3mm PMMA - opal (opțional vinyl/oracal), "
    "bordură profil aluminiu, spate Forex 10 mm. LED pe spate. "
    "Premontaj opțional: perete / structură metalică / panou ACM casetat "
    "(suport separat de spatele literei)."
)

TARGET_NOTES = (
    "Input params: text, font/vector_file, height_mm, depth_mm, "
    "quantity, face_material, side_material, back_material, "
    "illumination(none/frontlit/backlit/halo), mounting_type, "
    "paint_finish, indoor_outdoor. "
    "Straturi producție (ref. docs/production/volumetric-letters-production-layers.md): "
    "față plexiglas 3mm PMMA - opal tăiat; opțional vinyl/print/oracal; șanfren față opțional/configurabil. "
    "Bordură: profil aluminiu, adâncime configurabilă. "
    "Spate litere: Forex 10 mm (nu PVC/aluminiu generic); șanfren spate opțional/configurabil. "
    "LED: module montate pe spate Forex; cablaj + sursă în strat electric. "
    "Premontaj opțional: structură metalică sau panou Alucobond/ACM casetat — "
    "panoul ACM este suport de montaj, nu spatele literei."
)

COMPONENT_NAMES: dict[str, str] = {
    "comp_face_litere": "Față litere — plexiglas 3mm PMMA - opal (CNC/laser)",
    "comp_lateral_litere": "Laterale litere — profil aluminiu (bordură)",
    "comp_spate_litere": "Spate litere — Forex 10 mm",
    "comp_led_litere": "Iluminare LED — montaj pe spate Forex",
    "comp_finisaj_litere": "Finisare — vopsire, asamblare, QC",
}

OPERATION_NAMES: dict[str, str] = {
    "back_cut": "Tăiere spate Forex 10 mm",
}

MATERIAL_LABELS: dict[str, str] = {
    "MAT-ACP-FATA-LITERE": "Față plexiglas 3mm PMMA - opal; opțional vinyl/oracal/print",
    MAT_BACK_CODE: "Forex 10 mm spate litere (cod MAT-SPATE-PVC-LITERE)",
}

MATERIAL_DISPLAY_NAME = "Forex 10 mm spate litere (cod operațional MAT-SPATE-PVC-LITERE)"
MATERIAL_CATEGORY = "forex"
MATERIAL_SOURCE_NOTES_APPEND = (
    "Wording ref: spate literă = Forex 10 mm (cod istoric MAT-SPATE-PVC-LITERE). "
    "Panou ACM/Alucobond casetat = premontaj/suport, nu spate literă."
)

MARKER = "[forex10-wording-v1]"


def _backend_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve_db_path(cli_db: str | None) -> Path:
    if cli_db:
        p = Path(cli_db)
        if not p.is_absolute():
            p = (_backend_dir() / p).resolve()
        if not p.exists():
            raise FileNotFoundError(f"DB not found: {p}")
        return p

    env_url = os.environ.get("DATABASE_URL", "")
    m = re.search(r"sqlite(?:\+aiosqlite)?:///+([^?]+)", env_url)
    if m:
        raw = m.group(1).replace("/", os.sep)
        p = Path(raw)
        if not p.is_absolute():
            p = (_backend_dir() / p).resolve()
        if p.exists():
            return p

    for candidate in ("dev.db", "local_dev.db"):
        p = (_backend_dir() / candidate).resolve()
        if p.exists():
            return p

    raise FileNotFoundError(
        "Could not resolve SQLite DB. Pass --db or set DATABASE_URL, "
        "or place dev.db/local_dev.db under backend/."
    )


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _parse_json(raw: Any) -> Any:
    if raw is None:
        return None
    if isinstance(raw, (list, dict)):
        return raw
    if isinstance(raw, str):
        return json.loads(raw) if raw.strip() else None
    return None


def _set_label_fields(row: dict[str, Any], label: str) -> bool:
    changed = False
    for key in ("label", "name"):
        if key in row and row.get(key) != label:
            row[key] = label
            changed = True
        elif key not in row and key == "name":
            row["name"] = label
            changed = True
    return changed


def _patch_components(components: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    changes: list[str] = []
    out = deepcopy(components)
    for comp in out:
        cid = str(comp.get("component_id") or "")
        if cid in COMPONENT_NAMES and comp.get("name") != COMPONENT_NAMES[cid]:
            changes.append(f"component {cid}.name")
            comp["name"] = COMPONENT_NAMES[cid]
        for op in comp.get("operations") or []:
            if not isinstance(op, dict):
                continue
            code = str(op.get("code") or "")
            if code in OPERATION_NAMES:
                if _set_label_fields(op, OPERATION_NAMES[code]):
                    changes.append(f"component {cid}.operations[{code}]")
        for mat in comp.get("materials") or []:
            if not isinstance(mat, dict):
                continue
            code = str(mat.get("materialCode") or mat.get("material_code") or "")
            if code in MATERIAL_LABELS:
                if _set_label_fields(mat, MATERIAL_LABELS[code]):
                    changes.append(f"component {cid}.materials[{code}]")
    return out, changes


def _patch_flat_ops(ops: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    changes: list[str] = []
    out = deepcopy(ops)
    for op in out:
        if not isinstance(op, dict):
            continue
        code = str(op.get("code") or "")
        if code in OPERATION_NAMES and _set_label_fields(op, OPERATION_NAMES[code]):
            changes.append(f"flat op {code}")
    return out, changes


def _patch_flat_mats(mats: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    changes: list[str] = []
    out = deepcopy(mats)
    for mat in out:
        if not isinstance(mat, dict):
            continue
        code = str(mat.get("materialCode") or mat.get("material_code") or "")
        if code in MATERIAL_LABELS and _set_label_fields(mat, MATERIAL_LABELS[code]):
            changes.append(f"flat mat {code}")
    return out, changes


def _merge_notes(existing: str | None) -> str:
    merged = TARGET_NOTES
    if existing:
        for token in ("[save-smoke-ok]",):
            if token in existing and token not in merged:
                merged = merged.rstrip() + f" {token}"
    return merged


def _notes_ok(notes: str | None) -> bool:
    n = (notes or "").lower()
    return (
        "forex 10 mm" in n
        and "șanfren" in n
        and "premontaj" in n
        and "panoul acm" in n
    )


def _already_applied(description: str | None, notes: str | None, components: list | None) -> bool:
    if description != TARGET_DESCRIPTION:
        return False
    if not _notes_ok(notes):
        return False
    if not components:
        return False
    for comp in components:
        cid = str(comp.get("component_id") or "")
        if COMPONENT_NAMES.get(cid) and comp.get("name") != COMPONENT_NAMES[cid]:
            return False
    return True


def _summarize_template(row: sqlite3.Row, components: list | None) -> dict[str, Any]:
    spate = None
    if components:
        for c in components:
            if c.get("component_id") == "comp_spate_litere":
                spate = {
                    "name": c.get("name"),
                    "materials": [
                        {
                            "code": m.get("materialCode") or m.get("material_code"),
                            "name": m.get("name"),
                            "label": m.get("label"),
                        }
                        for m in (c.get("materials") or [])
                        if isinstance(m, dict)
                    ],
                }
    notes = row["notes"] or ""
    return {
        "id": row["id"],
        "template_code": row["template_code"],
        "description": row["description"],
        "notes_excerpt": notes[:220] + ("…" if len(notes) > 220 else ""),
        "notes_has_chamfer": "șanfren" in notes.lower(),
        "notes_has_premount": "premontaj" in notes.lower(),
        "comp_spate_litere": spate,
    }


def run(db_path: Path, apply: bool) -> dict[str, Any]:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, template_code, description, notes,
                   components_json, operations_json, required_materials_json
            FROM product_templates
            WHERE template_code = ?
            """,
            (TEMPLATE_CODE,),
        )
        tpl = cur.fetchone()
        if tpl is None:
            raise RuntimeError(f"Template missing: {TEMPLATE_CODE}")

        cur.execute(
            """
            SELECT id, code, name, category, source_notes, unit_cost, status
            FROM inventory_materials
            WHERE code = ?
            """,
            (MAT_BACK_CODE,),
        )
        mat = cur.fetchone()
        if mat is None:
            raise RuntimeError(f"Material missing: {MAT_BACK_CODE}")

        components_before = _parse_json(tpl["components_json"]) or []
        ops_before = _parse_json(tpl["operations_json"]) or []
        mats_before = _parse_json(tpl["required_materials_json"]) or []

        report: dict[str, Any] = {
            "db_path": str(db_path),
            "apply": apply,
            "template_id": int(tpl["id"]),
            "material_id": int(mat["id"]),
            "before": {
                "template": _summarize_template(tpl, components_before),
                "material": {
                    "code": mat["code"],
                    "name": mat["name"],
                    "category": mat["category"],
                    "unit_cost": mat["unit_cost"],
                    "status": mat["status"],
                },
            },
            "backup": {
                "description": tpl["description"],
                "notes": tpl["notes"],
                "components_json": components_before,
            },
        }

        components_after, comp_changes = _patch_components(components_before)
        ops_after, op_changes = _patch_flat_ops(ops_before)
        mats_after, mat_json_changes = _patch_flat_mats(mats_before)
        all_changes = comp_changes + op_changes + mat_json_changes

        desc_changed = (tpl["description"] or "") != TARGET_DESCRIPTION
        target_notes = _merge_notes(tpl["notes"])
        notes_changed = (tpl["notes"] or "") != target_notes
        if desc_changed:
            all_changes.append("description")
        if notes_changed:
            all_changes.append("notes")

        mat_name_changed = mat["name"] != MATERIAL_DISPLAY_NAME
        mat_cat_changed = (mat["category"] or "") != MATERIAL_CATEGORY
        source_notes = mat["source_notes"] or ""
        need_notes_append = MARKER not in source_notes
        if mat_name_changed:
            all_changes.append("inventory_materials.name")
        if mat_cat_changed:
            all_changes.append("inventory_materials.category")
        if need_notes_append:
            all_changes.append("inventory_materials.source_notes")

        report["changes_planned"] = all_changes
        report["idempotent_skip"] = (
            not all_changes
            or _already_applied(tpl["description"], tpl["notes"], components_after)
        ) and not mat_name_changed and not mat_cat_changed and not need_notes_append

        if apply and all_changes:
            now = datetime.now(timezone.utc).isoformat()
            new_source_notes = source_notes
            if need_notes_append:
                new_source_notes = (source_notes.rstrip() + " " + MATERIAL_SOURCE_NOTES_APPEND + MARKER).strip()

            cur.execute(
                """
                UPDATE product_templates
                SET description = ?,
                    notes = ?,
                    components_json = ?,
                    operations_json = ?,
                    required_materials_json = ?,
                    updated_at = ?
                WHERE id = ? AND template_code = ?
                """,
                (
                    TARGET_DESCRIPTION,
                    target_notes,
                    json.dumps(components_after, ensure_ascii=False),
                    json.dumps(ops_after, ensure_ascii=False),
                    json.dumps(mats_after, ensure_ascii=False),
                    now,
                    int(tpl["id"]),
                    TEMPLATE_CODE,
                ),
            )
            cur.execute(
                """
                UPDATE inventory_materials
                SET name = ?,
                    category = ?,
                    source_notes = ?,
                    updated_at = ?
                WHERE id = ? AND code = ?
                """,
                (
                    MATERIAL_DISPLAY_NAME,
                    MATERIAL_CATEGORY,
                    new_source_notes,
                    now,
                    int(mat["id"]),
                    MAT_BACK_CODE,
                ),
            )
            conn.commit()
            report["rows_updated"] = {
                "product_templates": cur.rowcount if cur.rowcount else 1,
                "inventory_materials": 1,
            }
        else:
            report["rows_updated"] = {}

        cur.execute(
            """
            SELECT id, template_code, description, notes, components_json
            FROM product_templates WHERE template_code = ?
            """,
            (TEMPLATE_CODE,),
        )
        tpl_after = cur.fetchone()
        components_final = _parse_json(tpl_after["components_json"]) or []
        cur.execute(
            "SELECT code, name, category, source_notes FROM inventory_materials WHERE code = ?",
            (MAT_BACK_CODE,),
        )
        mat_after = cur.fetchone()

        report["after"] = {
            "template": _summarize_template(tpl_after, components_final),
            "material": dict(mat_after) if mat_after else None,
        }
        return report
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=None, help="SQLite DB path (default: env or backend/dev.db)")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist changes (default: dry-run preview only)",
    )
    args = parser.parse_args()

    try:
        db_path = _resolve_db_path(args.db)
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e)}, indent=2, ensure_ascii=False))
        return 2

    try:
        report = run(db_path, apply=bool(args.apply))
    except RuntimeError as e:
        print(json.dumps({"error": str(e), "db_path": str(db_path)}, indent=2, ensure_ascii=False))
        return 1

    payload = json.dumps(report, indent=2, ensure_ascii=False)
    try:
        print(payload)
    except UnicodeEncodeError:
        print(json.dumps(report, indent=2, ensure_ascii=True))
    if report.get("error"):
        return 1
    if not args.apply:
        print("\nDry-run only. Re-run with --apply to persist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
