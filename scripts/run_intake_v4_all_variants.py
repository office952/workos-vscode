"""
Run intake V4 flow with gradi-curat.svg and collect pricing/details for ALL finish variants.
"""
import json
import hashlib
import sys
import os
import httpx
from pathlib import Path
from datetime import datetime

BASE = "http://localhost:8000/api/v1/intake-v4"
SVG_PATH = Path(r"C:\Users\offic\Desktop\workos-essential-audit-20260624\fisiere-teste\gradi-curat.svg")
OUTPUT_PATH = Path(r"C:\Users\offic\Desktop\workos-essential-audit-20260624\scripts\intake_v4_gradi_curat_report.md")

# Dev mode — no auth needed, server returns dev-admin user
HEADERS = {"Content-Type": "application/json"}

# All face finish variants from dossier
FACE_FINISHES = ["oracal_651", "oracal_641", "oracal_8500", "printed_vinyl", "none"]

# All return finish variants from dossier
RETURN_FINISHES = ["white_aluminum", "black_aluminum", "gold_aluminum", "mirror_silver", "ral_paint", "oracal_wrapped"]

# Lighting system variants
LIGHTING_SYSTEMS = ["led_modules", "led_strip"]

# Light colors
LIGHT_COLORS = ["warm", "neutral", "cool"]

# LED module power
LED_POWERS = [0.75, 1.0, 1.44]

# Backing modes
BACKING_MODES = ["none", "forex_10_no_bevel", "forex_10_with_bevel"]

# Mounting systems
MOUNTING_SYSTEMS = ["direct_wall", "steel_bars", "aluminum_bars", "acm_panel"]

# Emblem lighting modes
EMBLEM_MODES = ["area_lit", "excluded"]

# Mounting template materials
MOUNTING_TEMPLATE_MATERIALS = ["forex", "paper"]

# Vinyl roll widths
VINYL_ROLL_WIDTHS = [1000, 1260]


def api_get(client: httpx.Client, path: str) -> dict:
    r = client.get(f"{BASE}{path}")
    if r.status_code >= 400:
        print(f"  GET {path} => {r.status_code}: {r.text[:300]}")
        return {"_error": r.status_code, "_body": r.text[:500]}
    return r.json()


def api_post(client: httpx.Client, path: str, json_data=None, files=None) -> dict:
    if files:
        r = client.post(f"{BASE}{path}", files=files)
    else:
        r = client.post(f"{BASE}{path}", json=json_data)
    if r.status_code >= 400:
        print(f"  POST {path} => {r.status_code}: {r.text[:300]}")
        return {"_error": r.status_code, "_body": r.text[:500]}
    return r.json()


def api_put(client: httpx.Client, path: str, json_data: dict) -> dict:
    r = client.put(f"{BASE}{path}", json=json_data)
    if r.status_code >= 400:
        print(f"  PUT {path} => {r.status_code}: {r.text[:300]}")
        return {"_error": r.status_code, "_body": r.text[:500]}
    return r.json()


def safe_get(d: dict, *keys, default=None):
    """Safely traverse nested dict."""
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k, default)
        else:
            return default
    return d


def build_finish_setup(face_finish: str, return_finish: str, **overrides) -> dict:
    """Build a complete finish setup payload."""
    setup = {
        "face_finish_type": face_finish,
        "face_vinyl_roll_width_mm": 1000,
        "return_finish_type": return_finish,
        "return_depth_mm": 60,
        "illuminated": True,
        "lighting_system_type": "led_modules",
        "light_color": "warm",
        "led_module_power_w": 0.75,
        "backing_mode": "forex_10_no_bevel",
        "mounting_system": "aluminum_bars",
        "emblem_lighting_mode": "area_lit",
        "mounting_template_material_type": "forex",
        "confirmed": True,
        "internal_draft_quote_confirmed": False,
        "letter_group_finishes": [],
    }
    # Remove face_vinyl_roll_width for non-vinyl finishes
    if face_finish in ("none", "printed_vinyl"):
        setup.pop("face_vinyl_roll_width_mm", None)

    setup.update(overrides)
    return setup


def collect_variant_data(client: httpx.Client, ws_id: str, finish_setup: dict, label: str) -> dict:
    """Set finish, then collect material breakdown + pricing + production preview."""
    print(f"  Variant: {label}")
    # 1. Set finish
    ws = api_put(client, f"/workspaces/{ws_id}/finish-setup", finish_setup)
    if "_error" in ws:
        return {"label": label, "error": ws["_body"]}

    # 2. Material breakdown
    mb = api_get(client, f"/workspaces/{ws_id}/material-breakdown")

    # 3. Cost draft (volumetric face/back prep)
    cd = api_get(client, f"/workspaces/{ws_id}/volumetric-face-back-prep/cost-draft")

    # 4. Production handoff preview
    ph = api_get(client, f"/workspaces/{ws_id}/production-handoff-preview")

    # 5. Template form contract
    tfc = api_get(client, f"/workspaces/{ws_id}/template-form-contract")

    return {
        "label": label,
        "finish_setup": finish_setup,
        "material_breakdown": mb,
        "cost_draft": cd,
        "production_handoff": ph,
        "template_form_contract": tfc,
    }


def format_material_breakdown(mb: dict) -> str:
    """Format material breakdown for report."""
    if "_error" in mb:
        return f"  Error: {mb.get('_body', 'unknown')}\n"

    lines = []

    # Material rows
    mat_rows = mb.get("material_quantity_rows") or mb.get("material_rows") or []
    if mat_rows:
        lines.append("| Material | Qty | Unit | Unit Cost | Total | Currency |")
        lines.append("|----------|-----|------|-----------|-------|----------|")
        for row in mat_rows:
            name = row.get("display_name") or row.get("material_key") or row.get("label", "?")
            qty = row.get("quantity") or row.get("qty", "?")
            unit = row.get("unit", "?")
            unit_cost = row.get("unit_cost") or row.get("unit_price", "?")
            total = row.get("total_cost") or row.get("material_cost") or row.get("line_total", "?")
            currency = row.get("currency", "EUR")
            lines.append(f"| {name} | {qty} | {unit} | {unit_cost} | {total} | {currency} |")

    # Nesting material rows
    nesting_rows = mb.get("nesting_material_rows") or []
    if nesting_rows:
        lines.append("")
        lines.append("**Nesting Materials:**")
        lines.append("| Material | Qty | Unit | Unit Cost | Total | Currency |")
        lines.append("|----------|-----|------|-----------|-------|----------|")
        for row in nesting_rows:
            name = row.get("display_name") or row.get("material_key") or row.get("label", "?")
            qty = row.get("quantity") or row.get("qty", "?")
            unit = row.get("unit", "?")
            unit_cost = row.get("unit_cost") or row.get("unit_price", "?")
            total = row.get("total_cost") or row.get("material_cost") or row.get("line_total", "?")
            currency = row.get("currency", "EUR")
            lines.append(f"| {name} | {qty} | {unit} | {unit_cost} | {total} | {currency} |")

    # CNC/operation rows
    cnc_rows = mb.get("cnc_operation_rows") or mb.get("operation_rows") or []
    if cnc_rows:
        lines.append("")
        lines.append("**Operations:**")
        lines.append("| Operation | Qty | Unit | Rate | Total | Currency |")
        lines.append("|-----------|-----|------|------|-------|----------|")
        for row in cnc_rows:
            name = row.get("display_name") or row.get("operation_key") or row.get("label", "?")
            qty = row.get("quantity") or row.get("qty", "?")
            unit = row.get("unit", "?")
            rate = row.get("rate") or row.get("unit_price", "?")
            total = row.get("total_cost") or row.get("estimated_cost") or row.get("line_total", "?")
            currency = row.get("currency", "EUR")
            lines.append(f"| {name} | {qty} | {unit} | {rate} | {total} | {currency} |")

    # Edge cant rows
    cant_rows = mb.get("edge_cant_operation_rows") or []
    if cant_rows:
        lines.append("")
        lines.append("**Edge/Cant Operations:**")
        lines.append("| Operation | Qty | Unit | Rate | Total | Currency |")
        lines.append("|-----------|-----|------|------|-------|----------|")
        for row in cant_rows:
            name = row.get("display_name") or row.get("operation_key") or row.get("label", "?")
            qty = row.get("quantity") or row.get("qty", "?")
            unit = row.get("unit", "?")
            rate = row.get("rate") or row.get("unit_price", "?")
            total = row.get("total_cost") or row.get("estimated_cost") or row.get("line_total", "?")
            currency = row.get("currency", "EUR")
            lines.append(f"| {name} | {qty} | {unit} | {rate} | {total} | {currency} |")

    # Totals
    totals = mb.get("totals") or {}
    if totals:
        lines.append("")
        lines.append(f"**Totals:** material={totals.get('material_cost_total', '?')} | "
                     f"operations={totals.get('operation_cost_total', '?')} | "
                     f"grand={totals.get('grand_total', '?')} {totals.get('currency', 'EUR')}")

    # Warnings
    warnings = mb.get("warnings") or []
    if warnings:
        lines.append("")
        lines.append("**Warnings:**")
        for w in warnings:
            if isinstance(w, dict):
                lines.append(f"- [{w.get('severity', '?')}] {w.get('code', '?')}: {w.get('message', '?')}")
            else:
                lines.append(f"- {w}")

    return "\n".join(lines) if lines else "  (no data)\n"


def format_cost_draft(cd: dict) -> str:
    """Format face/back prep cost draft."""
    if "_error" in cd:
        return f"  Error: {cd.get('_body', 'unknown')}\n"

    lines = []

    # Material costs
    mat_costs = cd.get("material_cost_rows") or []
    if mat_costs:
        lines.append("| Material | Qty | Unit | Unit Cost | Total | Currency |")
        lines.append("|----------|-----|------|-----------|-------|----------|")
        for row in mat_costs:
            name = row.get("display_name") or row.get("material_code", "?")
            qty = row.get("quantity", "?")
            unit = row.get("unit", "?")
            uc = row.get("unit_cost", "?")
            total = row.get("total_cost") or row.get("line_total", "?")
            cur = row.get("currency", "EUR")
            lines.append(f"| {name} | {qty} | {unit} | {uc} | {total} | {cur} |")

    # Operation costs
    op_costs = cd.get("operation_cost_rows") or []
    if op_costs:
        lines.append("")
        lines.append("**Operation Costs:**")
        lines.append("| Operation | Qty | Unit | Rate | Total | Currency |")
        lines.append("|-----------|-----|------|------|-------|----------|")
        for row in op_costs:
            name = row.get("display_name") or row.get("operation_code", "?")
            qty = row.get("quantity", "?")
            unit = row.get("unit", "?")
            rate = row.get("rate", "?")
            total = row.get("total_cost") or row.get("line_total", "?")
            cur = row.get("currency", "EUR")
            lines.append(f"| {name} | {qty} | {unit} | {rate} | {total} | {cur} |")

    # Task drafts
    tasks = cd.get("task_drafts") or []
    if tasks:
        lines.append("")
        lines.append("**Task Drafts:**")
        for t in tasks:
            lines.append(f"- {t.get('task_key', '?')}: {t.get('title', '?')} "
                        f"(est. {t.get('estimated_minutes', '?')} min)")

    # Totals
    totals = cd.get("totals") or {}
    if totals:
        lines.append("")
        lines.append(f"**Cost Draft Totals:** material={totals.get('material_total', '?')} | "
                     f"operation={totals.get('operation_total', '?')} | "
                     f"grand={totals.get('grand_total', '?')} {totals.get('currency', 'EUR')}")

    # Warnings
    warnings = cd.get("warnings") or []
    if warnings:
        lines.append("")
        lines.append("**Warnings:**")
        for w in warnings:
            if isinstance(w, dict):
                lines.append(f"- [{w.get('severity', '?')}] {w.get('code', '?')}: {w.get('message', '?')}")
            else:
                lines.append(f"- {w}")

    return "\n".join(lines) if lines else "  (no data)\n"


def format_production_handoff(ph: dict) -> str:
    """Format production handoff preview."""
    if "_error" in ph:
        return f"  Error: {ph.get('_body', 'unknown')}\n"

    lines = []

    # Template alignment
    ta = ph.get("template_alignment") or {}
    if ta:
        lines.append(f"**Template:** {ta.get('template_code', '?')} | "
                     f"status={ta.get('status', '?')} | "
                     f"contract_warnings={ta.get('contract_warning_count', 0)}")

    # Material jobs
    jobs = ph.get("material_jobs") or []
    if jobs:
        lines.append("")
        lines.append("**Material Jobs:**")
        for j in jobs:
            lines.append(f"- {j.get('job_key', '?')}: {j.get('display_name', '?')} "
                        f"({j.get('quantity', '?')} {j.get('unit', '?')})")

    # Operation groups
    groups = ph.get("operation_groups") or []
    if groups:
        lines.append("")
        lines.append("**Operation Groups:**")
        for g in groups:
            ops = g.get("operation_codes") or g.get("operations") or []
            lines.append(f"- {g.get('group_key', '?')}: {g.get('title', '?')} — ops: {ops}")

    # Issues
    issues = ph.get("issues") or []
    if issues:
        lines.append("")
        lines.append("**Issues:**")
        for i in issues:
            if isinstance(i, dict):
                lines.append(f"- [{i.get('severity', '?')}] {i.get('code', '?')}: {i.get('message', '?')}")
            else:
                lines.append(f"- {i}")

    return "\n".join(lines) if lines else "  (no data)\n"


def main():
    print(f"=== Intake V4 Full Variant Report: gradi-curat.svg ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    if not SVG_PATH.exists():
        print(f"ERROR: SVG file not found at {SVG_PATH}")
        sys.exit(1)

    svg_bytes = SVG_PATH.read_bytes()
    svg_sha256 = hashlib.sha256(svg_bytes).hexdigest()
    print(f"SVG file: {SVG_PATH.name} ({len(svg_bytes)} bytes, sha256={svg_sha256[:16]}...)")

    report_lines = []
    report_lines.append(f"# Intake V4 — gradi-curat.svg — Full Variant Report")
    report_lines.append(f"")
    report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"**SVG file:** `{SVG_PATH.name}` ({len(svg_bytes):,} bytes)")
    report_lines.append(f"**SHA-256:** `{svg_sha256}`")
    report_lines.append(f"")

    with httpx.Client(timeout=30.0) as client:
        # ---- STEP 1: Create workspace ----
        print("1. Creating workspace...")
        ws = api_post(client, "/workspaces", json_data={
            "title": f"Gradi-Curat Full Variant Audit {datetime.now().strftime('%H%M%S')}",
            "template_code": "TPL-VOLUMETRIC-LETTERS",
        })
        if "_error" in ws:
            print(f"FATAL: Cannot create workspace: {ws}")
            sys.exit(1)

        ws_id = ws.get("workspace_id") or ws.get("id")
        print(f"   workspace_id = {ws_id}")
        report_lines.append(f"**Workspace ID:** `{ws_id}`")
        report_lines.append(f"**Template:** `TPL-VOLUMETRIC-LETTERS`")
        report_lines.append(f"")

        # ---- STEP 2: Upload SVG ----
        print("2. Uploading SVG...")
        with open(SVG_PATH, "rb") as f:
            svg_resp = api_post(client, f"/workspaces/{ws_id}/svg",
                                files={"file": (SVG_PATH.name, f, "image/svg+xml")})
        if "_error" in svg_resp:
            print(f"WARNING: SVG upload issue: {svg_resp}")

        # Extract analysis results
        analysis = svg_resp.get("svg_analysis") or svg_resp.get("analysis") or svg_resp
        layers = svg_resp.get("layer_role_setup") or svg_resp.get("layers") or {}

        report_lines.append(f"---")
        report_lines.append(f"## SVG Analysis")
        report_lines.append(f"")
        report_lines.append(f"```json")
        report_lines.append(json.dumps(svg_resp, indent=2, default=str)[:5000])
        report_lines.append(f"```")
        report_lines.append(f"")

        print(f"   SVG uploaded. Keys: {list(svg_resp.keys())[:10]}")

        # ---- STEP 2b: Confirm layer roles ----
        print("2b. Confirming layer roles...")
        # Extract layers from the SVG upload response or workspace state
        layer_setup = svg_resp.get("layer_role_setup") or {}
        layer_list = layer_setup.get("layers") or []
        if not layer_list:
            # fallback: get from workspace state
            ws_tmp = api_get(client, f"/workspaces/{ws_id}")
            payload = ws_tmp.get("payload") or {}
            pgs = payload.get("path_geometry_summary") or {}
            layer_list = pgs.get("layers") or pgs.get("drawable_layers") or []

        # Build layer role confirmations — confirm all as "face"
        layer_updates = []
        for layer in layer_list:
            lk = layer.get("layer_key") or layer.get("layer_id")
            if lk:
                layer_updates.append({
                    "layer_key": lk,
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                })
                print(f"   Confirming layer '{lk}' as 'face'")

        if layer_updates:
            lr_resp = api_put(client, f"/workspaces/{ws_id}/layer-roles", {"layers": layer_updates})
            if "_error" in lr_resp:
                print(f"   WARNING: layer role confirm failed: {lr_resp}")
            else:
                print(f"   Layer roles confirmed OK")
        else:
            print(f"   WARNING: No layers found to confirm!")

        # ---- STEP 2c: Save analysis bundle ----
        print("2c. Saving analysis bundle (svg_analysis_json + geometry)...")

        # Build svg_analysis_json from path_geometry_summary
        ws_tmp = api_get(client, f"/workspaces/{ws_id}")
        payload_tmp = ws_tmp.get("payload") or {}
        pgs = payload_tmp.get("path_geometry_summary") or {}
        pgs_layers = pgs.get("layers") or pgs.get("drawable_layers") or []

        # Build layer analysis entries
        analysis_layers = []
        for pl in pgs_layers:
            analysis_layers.append({
                "id": pl.get("layer_key") or pl.get("layer_id"),
                "name": pl.get("layer_name") or pl.get("display_name") or pl.get("layer_key"),
                "perimeterMl": pl.get("perimeter_mm", 0),
                "filledAreaSqm": (pl.get("area_mm2", 0) or 0) / 1_000_000,
            })

        total_perimeter_mm = pgs.get("perimeter_mm_approx", 0)
        total_area_mm2 = pgs.get("area_mm2_approx", 0)
        total_path_count = sum(pl.get("path_count", 0) for pl in pgs_layers)
        total_contours = sum(pl.get("closed_contour_count", 0) for pl in pgs_layers)

        svg_analysis_json = {
            "schemaVersion": "1.10.0",
            "layers": analysis_layers,
            "parts": {
                "count": total_contours or total_path_count or 6,
                "nestableCount": total_contours or total_path_count or 6,
            },
            "geometry": {
                "perimeterMl": total_perimeter_mm,
            },
            "document": {
                "widthMm": pgs.get("bbox_w_mm", 0),
                "heightMm": pgs.get("bbox_h_mm", 0),
                "filledAreaSqm": (total_area_mm2 or 0) / 1_000_000,
            },
        }

        # Build layer_role_setup for the bundle
        lr_setup_layers = []
        for pl in pgs_layers:
            lk = pl.get("layer_key") or pl.get("layer_id")
            lr_setup_layers.append({
                "layer_key": lk,
                "layer_id": pl.get("layer_id"),
                "layer_name": pl.get("layer_name") or pl.get("display_name"),
                "auto_role": "face",
                "auto_confidence": "high",
                "confirmed_role": "face",
                "confirmation_state": "confirmed",
                "path_count": pl.get("path_count", 0),
                "dominant_fill": (pl.get("color_evidence") or {}).get("dominant_fill"),
            })

        svg_text = SVG_PATH.read_text(encoding="utf-8", errors="replace")

        bundle_req = {
            "file_name": SVG_PATH.name,
            "file_size_bytes": len(svg_bytes),
            "svg_text": svg_text,
            "svg_analysis_json": svg_analysis_json,
            "layer_role_setup": {
                "confirmation_status": "complete",
                "layers": lr_setup_layers,
            },
        }

        ab_resp = api_put(client, f"/workspaces/{ws_id}/analysis-bundle", bundle_req)
        if "_error" in ab_resp:
            print(f"   WARNING: analysis bundle save failed: {ab_resp}")
        else:
            print(f"   Analysis bundle saved OK")

        # ---- STEP 3: Get workspace state to see geometry ----
        print("3. Getting workspace state...")
        ws_state = api_get(client, f"/workspaces/{ws_id}")
        report_lines.append(f"## Workspace State (after SVG)")
        report_lines.append(f"")
        report_lines.append(f"```json")
        report_lines.append(json.dumps(ws_state, indent=2, default=str)[:5000])
        report_lines.append(f"```")
        report_lines.append(f"")

        # ---- STEP 4: Get template form contract (dossier) ----
        print("4. Getting template form contract...")
        tfc = api_get(client, f"/workspaces/{ws_id}/template-form-contract")
        report_lines.append(f"## Template Form Contract")
        report_lines.append(f"")
        report_lines.append(f"```json")
        report_lines.append(json.dumps(tfc, indent=2, default=str)[:8000])
        report_lines.append(f"```")
        report_lines.append(f"")

        # ---- STEP 5: Run all FACE FINISH x RETURN FINISH combinations ----
        print()
        print("=" * 60)
        print("5. Running ALL finish variant combinations...")
        print("=" * 60)

        report_lines.append(f"---")
        report_lines.append(f"## Finish Variant Combinations")
        report_lines.append(f"")

        all_variants = []

        # Main combinations: face_finish x return_finish
        for face in FACE_FINISHES:
            for ret in RETURN_FINISHES:
                label = f"face={face} | return={ret}"
                setup = build_finish_setup(face, ret)
                data = collect_variant_data(client, ws_id, setup, label)
                all_variants.append(data)

        # Lighting variants (with default face/return)
        for ls in LIGHTING_SYSTEMS:
            for lc in LIGHT_COLORS:
                label = f"lighting={ls} | color={lc}"
                setup = build_finish_setup("oracal_651", "white_aluminum",
                                           lighting_system_type=ls, light_color=lc)
                data = collect_variant_data(client, ws_id, setup, label)
                all_variants.append(data)

        # LED power variants
        for pw in LED_POWERS:
            label = f"led_power={pw}W"
            setup = build_finish_setup("oracal_651", "white_aluminum",
                                       led_module_power_w=pw)
            data = collect_variant_data(client, ws_id, setup, label)
            all_variants.append(data)

        # Backing mode variants
        for bm in BACKING_MODES:
            label = f"backing={bm}"
            setup = build_finish_setup("oracal_651", "white_aluminum",
                                       backing_mode=bm)
            data = collect_variant_data(client, ws_id, setup, label)
            all_variants.append(data)

        # Mounting system variants
        for ms in MOUNTING_SYSTEMS:
            label = f"mounting={ms}"
            setup = build_finish_setup("oracal_651", "white_aluminum",
                                       mounting_system=ms)
            data = collect_variant_data(client, ws_id, setup, label)
            all_variants.append(data)

        # Emblem lighting modes
        for em in EMBLEM_MODES:
            label = f"emblem_lighting={em}"
            setup = build_finish_setup("oracal_651", "white_aluminum",
                                       emblem_lighting_mode=em)
            data = collect_variant_data(client, ws_id, setup, label)
            all_variants.append(data)

        # Mounting template material
        for mtm in MOUNTING_TEMPLATE_MATERIALS:
            label = f"mounting_template={mtm}"
            setup = build_finish_setup("oracal_651", "white_aluminum",
                                       mounting_template_material_type=mtm)
            data = collect_variant_data(client, ws_id, setup, label)
            all_variants.append(data)

        # Vinyl roll width
        for vrw in VINYL_ROLL_WIDTHS:
            label = f"vinyl_roll_width={vrw}mm"
            setup = build_finish_setup("oracal_651", "white_aluminum",
                                       face_vinyl_roll_width_mm=vrw)
            data = collect_variant_data(client, ws_id, setup, label)
            all_variants.append(data)

        # ---- STEP 6: Write all variants to report ----
        print()
        print(f"Total variants collected: {len(all_variants)}")

        for i, v in enumerate(all_variants, 1):
            label = v.get("label", f"Variant {i}")
            report_lines.append(f"### {i}. {label}")
            report_lines.append(f"")

            if "error" in v:
                report_lines.append(f"**ERROR:** {v['error']}")
                report_lines.append(f"")
                continue

            # Finish setup summary
            fs = v.get("finish_setup", {})
            report_lines.append(f"**Config:** face=`{fs.get('face_finish_type')}` | "
                               f"return=`{fs.get('return_finish_type')}` | "
                               f"depth={fs.get('return_depth_mm')}mm | "
                               f"lighting=`{fs.get('lighting_system_type')}` | "
                               f"color=`{fs.get('light_color')}` | "
                               f"led_power={fs.get('led_module_power_w')}W | "
                               f"backing=`{fs.get('backing_mode')}` | "
                               f"mounting=`{fs.get('mounting_system')}`")
            report_lines.append(f"")

            # Material breakdown
            mb = v.get("material_breakdown", {})
            report_lines.append(f"#### Material Breakdown")
            report_lines.append(f"")
            report_lines.append(format_material_breakdown(mb))
            report_lines.append(f"")

            # Cost draft
            cd = v.get("cost_draft", {})
            report_lines.append(f"#### Face/Back Prep Cost Draft")
            report_lines.append(f"")
            report_lines.append(format_cost_draft(cd))
            report_lines.append(f"")

            # Production handoff
            ph = v.get("production_handoff", {})
            report_lines.append(f"#### Production Handoff Preview")
            report_lines.append(f"")
            report_lines.append(format_production_handoff(ph))
            report_lines.append(f"")

        # ---- STEP 7: Summary table ----
        report_lines.append(f"---")
        report_lines.append(f"## Summary Table")
        report_lines.append(f"")
        report_lines.append(f"| # | Variant | Material Total | Operation Total | Grand Total | Warnings |")
        report_lines.append(f"|---|---------|---------------|-----------------|-------------|----------|")

        for i, v in enumerate(all_variants, 1):
            label = v.get("label", "?")
            mb = v.get("material_breakdown", {})
            totals = mb.get("totals") or {}
            mat_total = totals.get("material_cost_total", "?")
            op_total = totals.get("operation_cost_total", "?")
            grand = totals.get("grand_total", "?")
            warnings = mb.get("warnings") or []
            warn_count = len(warnings)
            report_lines.append(f"| {i} | {label} | {mat_total} | {op_total} | {grand} | {warn_count} |")

        # ---- Write report ----
        report_text = "\n".join(report_lines)
        OUTPUT_PATH.write_text(report_text, encoding="utf-8")
        print(f"\nReport written to: {OUTPUT_PATH}")
        print(f"Report size: {len(report_text):,} bytes")


if __name__ == "__main__":
    main()
