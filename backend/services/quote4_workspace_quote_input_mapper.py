"""Step 7E.1 — workspace → canonical quote_input mapping (pure, no DB writes).

Maps real Intake V6 workspace payload fields to volumetric quote_input.
Does not invent values; documents source path and alias transforms explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

FieldStatus = Literal["present", "missing", "alias", "derived", "blocker"]

DEFAULT_VOLUM_ALUMINUM_MODULE_CODE = "TPL-VOLUM-ALUMINIU_v1"


@dataclass
class FieldProvenance:
    key: str
    value: Any
    source_path: str
    status: FieldStatus = "present"
    transform: str | None = None
    note: str | None = None


@dataclass
class WorkspaceQuoteInputMapping:
    quote_input: dict[str, Any] = field(default_factory=dict)
    field_provenance: list[FieldProvenance] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    aliases_applied: list[dict[str, str]] = field(default_factory=list)
    finish_groups_summary: dict[str, Any] = field(default_factory=dict)


def _positive_number(raw: Any) -> float | None:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    return value


def _optional_string(raw: Any) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip()
    return text if text else None


def _get_dict(root: Any, key: str) -> dict[str, Any]:
    val = root.get(key) if isinstance(root, dict) else None
    return val if isinstance(val, dict) else {}


def _resolve_letter_face_area_m2(quote_geometry: dict[str, Any], finish_setup: dict[str, Any]) -> tuple[Any, str, str | None]:
    """Return (value, source_path, transform_note)."""
    if quote_geometry.get("letter_face_area_m2") is not None:
        return quote_geometry["letter_face_area_m2"], "quote_geometry.letter_face_area_m2", None
    if quote_geometry.get("face_area_m2") is not None:
        return (
            quote_geometry["face_area_m2"],
            "quote_geometry.face_area_m2",
            "face_area_m2→letter_face_area_m2",
        )
    groups = finish_setup.get("letter_group_finishes")
    if isinstance(groups, list) and groups:
        total = 0.0
        counted = 0
        for row in groups:
            if not isinstance(row, dict):
                continue
            area = _positive_number(row.get("face_area_m2"))
            if area is not None:
                total += area
                counted += 1
        if counted > 0:
            return round(total, 6), "finish_setup.letter_group_finishes[].face_area_m2 (sum)", "sum→letter_face_area_m2"
    return None, "quote_geometry.letter_face_area_m2", None


def _resolve_width_height(
    quote_geometry: dict[str, Any], client: dict[str, Any]
) -> tuple[dict[str, tuple[Any, str, str | None]], list[str]]:
    """Prefer quote_geometry over client for volumetric SVG-derived dimensions."""
    resolved: dict[str, tuple[Any, str, str | None]] = {}
    aliases: list[str] = []
    for key in ("width_mm", "height_mm"):
        geom_val = quote_geometry.get(key)
        client_val = client.get(key)
        if geom_val is not None and geom_val != "":
            transform = f"quote_geometry.{key}→{key}" if client_val in (None, "") else None
            if transform:
                aliases.append(transform)
            resolved[key] = (geom_val, f"quote_geometry.{key}", transform)
        elif client_val is not None and client_val != "":
            resolved[key] = (client_val, f"client.{key}", None)
        else:
            resolved[key] = (None, f"quote_geometry.{key}|client.{key}", None)
    return resolved, aliases


def _derive_volum_aluminum_module_code(
    finish_setup: dict[str, Any],
    module_link_codes: list[str] | None,
) -> tuple[str | None, str, str | None]:
    explicit = _optional_string(finish_setup.get("volum_aluminum_module_template_code"))
    if explicit:
        return explicit, "finish_setup.volum_aluminum_module_template_code", None
    links = module_link_codes or []
    for code in links:
        if code and "VOLUM" in code.upper() and "ALUMIN" in code.upper():
            return code, "product_template_module_links.module_template_code", "registry_link→volum_aluminum_module_template_code"
    if DEFAULT_VOLUM_ALUMINUM_MODULE_CODE in links:
        return DEFAULT_VOLUM_ALUMINUM_MODULE_CODE, "product_template_module_links", "default_module_link"
    return None, "finish_setup.volum_aluminum_module_template_code|product_template_module_links", None


def _finish_groups_status(finish_setup: dict[str, Any]) -> dict[str, Any]:
    groups = finish_setup.get("letter_group_finishes")
    if not isinstance(groups, list):
        return {"total": 0, "confirmed": 0, "unconfirmed": 0, "blocker": "letter_group_finishes_missing"}
    confirmed = sum(1 for g in groups if isinstance(g, dict) and g.get("confirmed") is True)
    total = len(groups)
    if total > 0 and confirmed == 0:
        return {
            "total": total,
            "confirmed": confirmed,
            "unconfirmed": total - confirmed,
            "blocker": "finish_groups_unconfirmed",
        }
    if total > 0 and confirmed < total:
        return {
            "total": total,
            "confirmed": confirmed,
            "unconfirmed": total - confirmed,
            "blocker": "finish_groups_partially_unconfirmed",
        }
    return {
        "total": total,
        "confirmed": confirmed,
        "unconfirmed": total - confirmed,
        "blocker": None,
    }


def _map_face_finish_type(raw: str | None) -> str | None:
    if not raw:
        return None
    lowered = raw.lower()
    if lowered.startswith("oracal"):
        return "oracal"
    if lowered == "white_aluminum":
        return "oracal_wrapped"
    return raw


def workspace_letter_group_to_product_spec_assignment(group: dict[str, Any]) -> dict[str, Any]:
    """Map Intake V6 workspace letter_group_finishes row → product_spec letterGroupFinishAssignments shape."""
    group_id = _optional_string(group.get("group_key")) or _optional_string(group.get("layer_name")) or "unknown"
    face_finish = _map_face_finish_type(_optional_string(group.get("face_finish_type")))
    return_finish = _map_face_finish_type(_optional_string(group.get("return_finish_type")))
    assignment: dict[str, Any] = {
        "groupId": group_id,
        "confirmedByOperator": group.get("confirmed") is True,
        "face": {
            "finishType": face_finish or "none",
            "materialCode": _optional_string(group.get("face_oracal_code")),
            "colorCode": _optional_string(group.get("face_oracal_code")),
            "colorName": _optional_string(group.get("face_oracal_name")),
        },
        "returnCant": {
            "finishType": return_finish or "none",
            "depthMm": group.get("return_depth_mm"),
            "materialCode": _optional_string(group.get("return_oracal_code")),
            "colorCode": _optional_string(group.get("return_oracal_code")),
            "colorName": _optional_string(group.get("return_oracal_name")),
        },
    }
    return assignment


def build_product_spec_proposal(
    workspace_payload: dict[str, Any],
    *,
    include_unconfirmed_groups: bool = False,
) -> dict[str, Any]:
    """Build proposed intake_requests.product_spec_json from workspace (no persist)."""
    finish_setup = _get_dict(workspace_payload, "finish_setup")
    quote_geometry = _get_dict(workspace_payload, "quote_geometry")
    svg_source = _get_dict(workspace_payload, "svg_source")

    groups_raw = finish_setup.get("letter_group_finishes")
    assignments: list[dict[str, Any]] = []
    if isinstance(groups_raw, list):
        for row in groups_raw:
            if not isinstance(row, dict):
                continue
            if not include_unconfirmed_groups and row.get("confirmed") is not True:
                continue
            assignments.append(workspace_letter_group_to_product_spec_assignment(row))

    letter_face, _, _ = _resolve_letter_face_area_m2(quote_geometry, finish_setup)
    spec: dict[str, Any] = {
        "letterGroupFinishAssignments": assignments,
        "svgLetterGroups": [],
        "letter_count": quote_geometry.get("letter_count"),
        "letter_perimeter_m": quote_geometry.get("letter_perimeter_m"),
        "letter_face_area_m2": letter_face,
        "width_mm": quote_geometry.get("width_mm"),
        "height_mm": quote_geometry.get("height_mm"),
        "return_depth_mm": finish_setup.get("return_depth_mm"),
        "face_finish_type": finish_setup.get("face_finish_type"),
        "illuminated": finish_setup.get("illuminated"),
        "lighting_system_type": finish_setup.get("lighting_system_type"),
        "selected_psu_watts": finish_setup.get("selected_psu_watts"),
        "vector_file": svg_source.get("file_name"),
    }
    return {k: v for k, v in spec.items() if v is not None}


def map_workspace_to_quote_input(
    workspace_payload: dict[str, Any],
    *,
    quantity: int | None = None,
    module_link_codes: list[str] | None = None,
) -> WorkspaceQuoteInputMapping:
    """Map workspace payload to canonical volumetric quote_input with provenance."""
    result = WorkspaceQuoteInputMapping()
    finish_setup = _get_dict(workspace_payload, "finish_setup")
    quote_geometry = _get_dict(workspace_payload, "quote_geometry")
    svg_source = _get_dict(workspace_payload, "svg_source")
    client = _get_dict(workspace_payload, "client")

    result.finish_groups_summary = _finish_groups_status(finish_setup)
    if result.finish_groups_summary.get("blocker"):
        result.blockers.append(str(result.finish_groups_summary["blocker"]))

    def add_field(key: str, value: Any, source: str, status: FieldStatus = "present", transform: str | None = None, note: str | None = None) -> None:
        result.field_provenance.append(
            FieldProvenance(key=key, value=value, source_path=source, status=status, transform=transform, note=note)
        )
        if value is not None and value != "":
            result.quote_input[key] = value
        elif status == "missing":
            result.missing_fields.append(key)

    # quantity
    qty = quantity
    qty_source = "quotes.line_items[].quantity"
    if qty is None:
        qty = quote_geometry.get("letter_count")
        qty_source = "quote_geometry.letter_count"
    if qty is not None:
        add_field("quantity", int(qty), qty_source)
    else:
        add_field("quantity", None, qty_source, status="missing")

    # dimensions
    dim_resolved, dim_aliases = _resolve_width_height(quote_geometry, client)
    for alias in dim_aliases:
        result.aliases_applied.append({"field": alias.split("→")[1], "transform": alias})
    for key, (val, src, transform) in dim_resolved.items():
        if val is not None:
            add_field(key, val, src, status="alias" if transform else "present", transform=transform)
        else:
            add_field(key, None, src, status="missing")

    # geometry
    for key in ("letter_count", "letter_perimeter_m"):
        val = quote_geometry.get(key)
        if val is not None:
            add_field(key, val, f"quote_geometry.{key}")
        else:
            add_field(key, None, f"quote_geometry.{key}", status="missing")

    letter_face, face_src, face_transform = _resolve_letter_face_area_m2(quote_geometry, finish_setup)
    if letter_face is not None:
        add_field("letter_face_area_m2", letter_face, face_src, status="alias" if face_transform else "present", transform=face_transform)
        if face_transform:
            result.aliases_applied.append({"field": "letter_face_area_m2", "transform": face_transform})
    else:
        add_field("letter_face_area_m2", None, face_src, status="missing")

    depth = finish_setup.get("return_depth_mm") or quote_geometry.get("return_depth_mm")
    if depth is not None:
        src = "finish_setup.return_depth_mm" if finish_setup.get("return_depth_mm") is not None else "quote_geometry.return_depth_mm"
        add_field("return_depth_mm", depth, src)
        add_field("depth_mm", depth, src, transform="return_depth_mm→depth_mm")
    else:
        add_field("return_depth_mm", None, "finish_setup.return_depth_mm", status="missing")

    vector_file = svg_source.get("file_name")
    if vector_file:
        add_field("vector_file", vector_file, "svg_source.file_name")
    else:
        add_field("vector_file", None, "svg_source.file_name", status="missing")

    # LED / PSU
    for key in (
        "illuminated",
        "lighting_system_type",
        "led_module_count",
        "selected_psu_watts",
        "required_psu_watts",
        "psu_allocation_status",
        "estimated_led_watts",
    ):
        val = finish_setup.get(key)
        if val is not None and val != "":
            add_field(key, val, f"finish_setup.{key}")
        elif key in ("selected_psu_watts", "lighting_system_type"):
            add_field(key, None, f"finish_setup.{key}", status="missing")

    # mounting
    for key in ("mounting_system", "mounting_template_enabled"):
        val = finish_setup.get(key)
        if val is not None and val != "":
            add_field(key, val, f"finish_setup.{key}")

    # finish types
    for key in ("face_finish_type", "return_finish_type"):
        val = finish_setup.get(key)
        if val is not None:
            add_field(key, val, f"finish_setup.{key}")

    # volum aluminum module
    vol_code, vol_src, vol_transform = _derive_volum_aluminum_module_code(finish_setup, module_link_codes)
    if vol_code:
        add_field(
            "volum_aluminum_module_template_code",
            vol_code,
            vol_src,
            status="derived" if vol_transform else "present",
            transform=vol_transform,
        )
        if vol_transform:
            result.aliases_applied.append({"field": "volum_aluminum_module_template_code", "transform": vol_transform})
    else:
        add_field("volum_aluminum_module_template_code", None, vol_src, status="missing")
        result.blockers.append("volum_aluminum_module_template_code_missing")

    # nested finish_setup for aggregate overlay (existing adapter reads this)
    if finish_setup:
        result.quote_input["finish_setup"] = finish_setup

    # structura_suport inactive for direct_wall — informational, not a blocker
    mounting = _optional_string(finish_setup.get("mounting_system"))
    if mounting == "direct_wall":
        result.field_provenance.append(
            FieldProvenance(
                key="structura_suport",
                value="inactive",
                source_path="finish_setup.mounting_system=direct_wall",
                status="present",
                note="structura_suport correctly inactive for direct_wall mounting",
            )
        )

    return result


def build_proposed_line_items_enrichment(
    existing_line_items: list[dict[str, Any]] | None,
    quote_input: dict[str, Any],
    *,
    template_code: str,
    workspace_id: str,
) -> dict[str, Any]:
    """Propose line_items wrapper enrichment without mutating DB."""
    base = list(existing_line_items or [])
    if not base:
        base = [{"productCode": template_code, "quantity": quote_input.get("quantity", 1), "unit_price": 0, "total": 0}]
    enriched = []
    for item in base:
        row = dict(item)
        row["quote_input"] = quote_input
        row["template_code"] = template_code
        row["workspace_id"] = workspace_id
        enriched.append(row)
    return {
        "shape": "line_items_with_quote_input",
        "items": enriched,
        "note": "Proposal only — embed quote_input in line_items for orchestrator handoff",
    }


def build_intake_linkage_repair_plan(
    *,
    quote_id: int,
    quote_intake_id: int | None,
    quote_intake_code: str | None,
    workspace_id: str,
    workspace_code: str,
    template_code: str,
    client_name: str,
    quantity: int,
    existing_intake_row: dict[str, Any] | None,
    product_spec_proposal: dict[str, Any],
) -> dict[str, Any]:
    """Plan intake_requests + quote.intake_id repair without executing."""
    intake_code_candidate = None
    if existing_intake_row and existing_intake_row.get("code"):
        intake_code_candidate = existing_intake_row["code"]

    plan: dict[str, Any] = {
        "quote_id": quote_id,
        "current_quote_intake_id": quote_intake_id,
        "current_quote_intake_code": quote_intake_code,
        "workspace_id": workspace_id,
        "workspace_code": workspace_code,
        "intake_requests_row_needed": quote_intake_id is None or existing_intake_row is None,
        "quote_intake_id_update_needed": quote_intake_id is None,
        "proposed_intake_requests_row": None,
        "proposed_quote_updates": {},
        "risk_notes": [],
    }

    if existing_intake_row:
        plan["existing_intake_requests_row"] = existing_intake_row
        if not existing_intake_row.get("product_spec_json"):
            plan["proposed_intake_requests_updates"] = {
                "product_spec_json": product_spec_proposal,
                "confirmed_template_code": template_code,
                "status": "ready_for_quote",
                "quantity": quantity,
            }
            plan["risk_notes"].append("Backfill product_spec_json on existing intake_requests row — no new row needed if id link restored")
        else:
            plan["risk_notes"].append("Existing intake_requests row has product_spec_json — merge/review before overwrite")
    else:
        plan["proposed_intake_requests_row"] = {
            "code": intake_code_candidate or f"IR-QUOTE4-{workspace_code}",
            "client_name": client_name or "Unknown",
            "product_family": "litere_volumetrice",
            "status": "ready_for_quote",
            "quantity": quantity,
            "confirmed_template_code": template_code,
            "product_spec_json": product_spec_proposal,
            "notes": f"Step 7E.1 repair linkage for quote {quote_id} ← workspace {workspace_id}",
        }
        plan["risk_notes"].append("New intake_requests row requires owner GO — not a seed/migration")

    plan["proposed_quote_updates"] = {
        "intake_id": existing_intake_row.get("id") if existing_intake_row else "<new_intake_requests.id>",
        "intake_code": quote_intake_code or f"IV6-{workspace_id}",
        "line_items": "<enriched with quote_input — see proposed_line_items>",
    }
    plan["risk_notes"].append("intake_code IV6-{uuid} is workspace code, not intake_requests.code — both may coexist")
    return plan


def audit_wc_assembly_rate(workcenter_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Read-only WC_ASSEMBLY / assembly workcenter audit."""
    by_code = {str(r.get("code")): r for r in workcenter_rows if r.get("code")}
    wc = by_code.get("WC_ASSEMBLY")
    assembly_like = [
        r for r in workcenter_rows
        if r.get("code") and "ASSEMBLY" in str(r.get("code")).upper()
    ]
    active_with_rate = [
        r for r in workcenter_rows
        if r.get("rate_per_hour") is not None and float(r.get("rate_per_hour") or 0) > 0
    ]

    proposal = None
    if wc is None:
        proposal = {
            "action": "add_workcenter_rate_row",
            "code": "WC_ASSEMBLY",
            "label": "Ansamblare",
            "rate_basis": "per_hour",
            "status": "needs_owner_input",
            "note": "Row missing from workcenter_rates — add via Pricing Registry admin, not seed",
        }
    elif wc.get("rate_per_hour") is None or float(wc.get("rate_per_hour") or 0) <= 0:
        proposal = {
            "action": "update_workcenter_rate",
            "code": "WC_ASSEMBLY",
            "current_rate_per_hour": wc.get("rate_per_hour"),
            "current_status": wc.get("status"),
            "note": "Set positive rate_per_hour via Pricing Registry — do not invent commercial value in script",
        }

    return {
        "wc_assembly_exists": wc is not None,
        "wc_assembly_rate_valid": bool(wc and wc.get("rate_per_hour") and float(wc["rate_per_hour"]) > 0),
        "wc_assembly_row": wc,
        "assembly_like_workcenters": assembly_like,
        "workcenters_with_positive_rate_count": len(active_with_rate),
        "all_workcenter_rates_null": len(active_with_rate) == 0,
        "proposed_fix": proposal,
        "do_not_apply": True,
    }


def build_workspace_payload_patches(workspace_payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Propose canonical-key sync patches on workspace payload (document only)."""
    patches: list[dict[str, Any]] = []
    quote_geometry = _get_dict(workspace_payload, "quote_geometry")
    client = _get_dict(workspace_payload, "client")
    finish_setup = _get_dict(workspace_payload, "finish_setup")

    for key in ("width_mm", "height_mm"):
        if quote_geometry.get(key) is not None and client.get(key) in (None, ""):
            patches.append({
                "path": f"client.{key}",
                "proposed_value": quote_geometry[key],
                "source": f"quote_geometry.{key}",
                "reason": "PD form binding reads client.width_mm — sync from SVG geometry",
            })

    if quote_geometry.get("letter_face_area_m2") is None and quote_geometry.get("face_area_m2") is not None:
        patches.append({
            "path": "quote_geometry.letter_face_area_m2",
            "proposed_value": quote_geometry["face_area_m2"],
            "source": "quote_geometry.face_area_m2",
            "reason": "Canonical key letter_face_area_m2 required by aggregate cost path",
        })

    if finish_setup.get("volum_aluminum_module_template_code") is None:
        patches.append({
            "path": "finish_setup.volum_aluminum_module_template_code",
            "proposed_value": DEFAULT_VOLUM_ALUMINUM_MODULE_CODE,
            "source": "product_template_module_links.module_template_code",
            "reason": "Required module link TPL-VOLUM-ALUMINIU_v1 — derive from registry, not hardcode blind",
            "requires_owner_confirm": True,
        })

    return patches
