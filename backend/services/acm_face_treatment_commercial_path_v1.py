"""ACM / Bond Axis B — face-treatment local commercial path.

Typed domain ``acm_face_treatments_v1`` with ``routed_cutouts[]`` and
``acrylic_inserts[]``. Orthogonal to applied_content XOR (Axis A).

Does not invent optical/LED catalogs or rates. Does not revive LIGHT-ROUTED.
Does not create volumetric applied_content composition links.
"""

from __future__ import annotations

from typing import Any, Literal, Mapping, MutableMapping
from uuid import uuid4

from data.product_system.acp_face_treatment_registry_v1 import (
    FACE_TREATMENT_ACRYLIC_INSERT,
    FACE_TREATMENT_ROUTED_BACKLIT,
    GEOMETRY_ROLE_ACRYLIC_INSERT,
    GEOMETRY_ROLE_CUTOUT_LOGO,
    GEOMETRY_ROLE_CUTOUT_TEXT,
    LIVE_ACP_SHELL_TEMPLATE,
)
from data.product_system.acp_local_face_modules_v1 import (
    INSERT_THICKNESS_OWNER_VARIANT_MM,
    INSERT_THICKNESS_PROVENANCE,
    MODULE_ACRYLIC_INSERT,
    MODULE_ROUTED_BACKLIT,
)
from services.acm_boxed_support_composition_v1 import PANEL_QUANTITY_KEYS
from services.acp_local_face_module_service import (
    empty_insert_module,
    empty_routed_module,
    evaluate_module_readiness,
    normalize_local_module,
)

DOMAIN_SCHEMA = "acm_face_treatments_v1"
DOMAIN_VERSION = 1
BAG_KEY = "acm_face_treatments"

UI_BADGE_RELIEF_PLEXI_10MM = "RELIEF_PLEXI_10MM"

STATUS_DRAFT = "draft"
STATUS_CONFIRMED = "confirmed"
STATUS_INACTIVE = "inactive"

COEXISTENCE_NONE = "none"
COEXISTENCE_ROUTED_ONLY = "routed_only"
COEXISTENCE_INSERT_ONLY = "insert_only"
COEXISTENCE_BOTH = "both"

CoexistenceMode = Literal["none", "routed_only", "insert_only", "both"]

BLOCKER_UNKNOWN_GEOMETRY_ROLE = "FACE_TREATMENT_UNKNOWN_GEOMETRY_ROLE"
BLOCKER_UNKNOWN_TREATMENT = "FACE_TREATMENT_UNKNOWN_CODE"
BLOCKER_OPTICAL_CATALOG_MISSING = "FACE_TREATMENT_OPTICAL_CATALOG_MISSING"
BLOCKER_ILLUMINATION_RATES_MISSING = "FACE_TREATMENT_ILLUMINATION_RATES_MISSING"
WARN_INSERT_THICKNESS_NOT_SOLE = "INSERT_THICKNESS_NOT_SOLE_ADMITTED"
WARN_LEGACY_LIGHT_ROUTED_NOT_AUTHORITY = "LEGACY_LIGHT_ROUTED_NOT_AUTHORITY"
WARN_PANEL_ONLY_NO_FACE_TREATMENTS = "ACM_PANEL_ONLY_NO_FACE_TREATMENTS"

# Treatment quantity keys — never share commercial keys with panel sheet.
ROUTED_QUANTITY_KEYS = frozenset(
    {
        "routed_cut_length_m",
        "routed_cutout_count",
        "optical_backing_area_m2",
    }
)
INSERT_QUANTITY_KEYS = frozenset(
    {
        "acrylic_insert_count",
        "acrylic_insert_area_m2",
        "acrylic_insert_thickness_mm",
    }
)
TREATMENT_QUANTITY_KEYS = ROUTED_QUANTITY_KEYS | INSERT_QUANTITY_KEYS

RESOURCE_AUTHORITY = "MISSING_OPTICAL_ELECTRICAL_RO"


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


def empty_face_treatments_domain() -> dict[str, Any]:
    return {
        "schema": DOMAIN_SCHEMA,
        "version": DOMAIN_VERSION,
        "host_template_code": LIVE_ACP_SHELL_TEMPLATE,
        "status": STATUS_DRAFT,
        "routed_cutouts": [],
        "acrylic_inserts": [],
        "coexistence": COEXISTENCE_NONE,
        "orthogonal_to_applied_content_xor": True,
        "ui_badges": {},
        "provenance": {
            "source": "operator",
            "axis": "B",
            "resource_authority": RESOURCE_AUTHORITY,
            "legacy_light_routed": "PARALLEL_LEGACY_COST_PATH — not authority",
        },
        "commercial": {
            "panel_sheet_owner": "acm_shell",
            "double_sheet_guard": "treatments_must_not_bill_panel_sheet",
            "optical_pricing_status": "BLOCKED",
            "optical_blocker": BLOCKER_OPTICAL_CATALOG_MISSING,
            "illumination_pricing_status": "BLOCKED",
            "illumination_blocker": BLOCKER_ILLUMINATION_RATES_MISSING,
        },
        "readiness": {
            "overall": "NOT_APPLICABLE",
            "optional_absent_ok": True,
            "blockers": [],
            "warnings": [],
        },
    }


def _normalize_routed_entry(raw: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(raw, Mapping):
        return None
    role = str(raw.get("geometry_role") or GEOMETRY_ROLE_CUTOUT_TEXT).strip()
    if role not in {GEOMETRY_ROLE_CUTOUT_TEXT, GEOMETRY_ROLE_CUTOUT_LOGO}:
        return None
    entry_id = str(raw.get("id") or raw.get("instance_id") or "").strip() or _new_id("routed")
    binding_id = str(raw.get("binding_id") or f"bind_{entry_id}").strip()
    status = str(raw.get("status") or STATUS_DRAFT).strip().lower()
    if status not in {STATUS_DRAFT, STATUS_CONFIRMED, STATUS_INACTIVE}:
        status = STATUS_DRAFT
    module_raw = raw.get("local_module_configuration") or raw.get("module")
    module = normalize_local_module(
        module_raw,
        binding_id=binding_id,
        treatment_code=FACE_TREATMENT_ROUTED_BACKLIT,
        geometry_role=role,
        component_template_code=LIVE_ACP_SHELL_TEMPLATE,
        status="ACTIVE" if status != STATUS_INACTIVE else "INACTIVE",
    )
    if module is None:
        module = empty_routed_module(binding_id)
        module["face_treatment_code"] = FACE_TREATMENT_ROUTED_BACKLIT
        module["geometry_role"] = role
        module["binding_id"] = binding_id
        module["readiness"] = evaluate_module_readiness(module)
    confirmed_fields = _as_dict(raw.get("confirmed_fields"))
    return {
        "id": entry_id,
        "face_treatment_code": FACE_TREATMENT_ROUTED_BACKLIT,
        "module_code": MODULE_ROUTED_BACKLIT,
        "geometry_role": role,
        "binding_id": binding_id,
        "status": status,
        "label": str(raw.get("label") or "").strip() or None,
        "confirmed_fields": {
            "cut_length_m": confirmed_fields.get("cut_length_m"),
            "cutout_count": confirmed_fields.get("cutout_count"),
            "backing_area_m2": confirmed_fields.get("backing_area_m2"),
            # External artwork: consume confirmed only — never parse here.
            "external_artwork_ref": confirmed_fields.get("external_artwork_ref"),
        },
        "local_module_configuration": module,
        "quantity_ownership": "routed_local_module",
        "owns_panel_sheet": False,
        "commercial_line_status": "BLOCKED_OPTICAL_CATALOG",
    }


def _normalize_insert_entry(raw: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(raw, Mapping):
        return None
    role = str(raw.get("geometry_role") or GEOMETRY_ROLE_ACRYLIC_INSERT).strip()
    if role != GEOMETRY_ROLE_ACRYLIC_INSERT:
        return None
    entry_id = str(raw.get("id") or raw.get("instance_id") or "").strip() or _new_id("insert")
    binding_id = str(raw.get("binding_id") or f"bind_{entry_id}").strip()
    status = str(raw.get("status") or STATUS_DRAFT).strip().lower()
    if status not in {STATUS_DRAFT, STATUS_CONFIRMED, STATUS_INACTIVE}:
        status = STATUS_DRAFT
    module_raw = raw.get("local_module_configuration") or raw.get("module")
    module = normalize_local_module(
        module_raw,
        binding_id=binding_id,
        treatment_code=FACE_TREATMENT_ACRYLIC_INSERT,
        geometry_role=role,
        component_template_code=LIVE_ACP_SHELL_TEMPLATE,
        status="ACTIVE" if status != STATUS_INACTIVE else "INACTIVE",
    )
    if module is None:
        module = empty_insert_module(binding_id)
        module["face_treatment_code"] = FACE_TREATMENT_ACRYLIC_INSERT
        module["geometry_role"] = role
        module["binding_id"] = binding_id
        module["readiness"] = evaluate_module_readiness(module)
    confirmed_fields = _as_dict(raw.get("confirmed_fields"))
    thickness = confirmed_fields.get("thickness_mm")
    if thickness is None:
        ins = _as_dict(module.get("insert"))
        thickness = ins.get("thickness_mm", INSERT_THICKNESS_OWNER_VARIANT_MM)
    try:
        thickness_f = float(thickness)
    except (TypeError, ValueError):
        thickness_f = INSERT_THICKNESS_OWNER_VARIANT_MM
    # RELIEF_PLEXI_10MM is a UI badge for the ~10 mm owner variant — not a second product.
    ui_badge = None
    if abs(thickness_f - INSERT_THICKNESS_OWNER_VARIANT_MM) < 0.01:
        ui_badge = UI_BADGE_RELIEF_PLEXI_10MM
    return {
        "id": entry_id,
        "face_treatment_code": FACE_TREATMENT_ACRYLIC_INSERT,
        "module_code": MODULE_ACRYLIC_INSERT,
        "geometry_role": role,
        "binding_id": binding_id,
        "status": status,
        "label": str(raw.get("label") or "").strip() or None,
        "ui_badge": ui_badge,
        "confirmed_fields": {
            "thickness_mm": thickness_f,
            "thickness_provenance": confirmed_fields.get(
                "thickness_provenance", INSERT_THICKNESS_PROVENANCE
            ),
            "sole_thickness_admitted": False,
            "insert_area_m2": confirmed_fields.get("insert_area_m2"),
            "insert_count": confirmed_fields.get("insert_count"),
            "external_artwork_ref": confirmed_fields.get("external_artwork_ref"),
        },
        "local_module_configuration": module,
        "quantity_ownership": "acrylic_insert_local_module",
        "owns_panel_sheet": False,
        "commercial_line_status": "BLOCKED_OPTICAL_CATALOG",
        "product_identity_note": (
            "Insert and 'relief plexi ~10 mm' share FACE-TREATMENT-ACRYLIC-INSERT; "
            "RELIEF_PLEXI_10MM is UI badge only."
        ),
    }


def compute_coexistence(
    routed: list[Mapping[str, Any]],
    inserts: list[Mapping[str, Any]],
) -> CoexistenceMode:
    active_routed = [
        r for r in routed if str(r.get("status") or "").lower() != STATUS_INACTIVE
    ]
    active_inserts = [
        i for i in inserts if str(i.get("status") or "").lower() != STATUS_INACTIVE
    ]
    has_r = len(active_routed) > 0
    has_i = len(active_inserts) > 0
    if has_r and has_i:
        return COEXISTENCE_BOTH
    if has_r:
        return COEXISTENCE_ROUTED_ONLY
    if has_i:
        return COEXISTENCE_INSERT_ONLY
    return COEXISTENCE_NONE


def normalize_face_treatments(raw: Any) -> dict[str, Any]:
    """Normalize operator/PT payload into acm_face_treatments_v1."""
    base = empty_face_treatments_domain()
    if not isinstance(raw, Mapping):
        base["readiness"]["warnings"] = [WARN_PANEL_ONLY_NO_FACE_TREATMENTS]
        return base

    routed: list[dict[str, Any]] = []
    for item in _as_list(raw.get("routed_cutouts")):
        entry = _normalize_routed_entry(_as_dict(item))
        if entry is not None:
            routed.append(entry)

    inserts: list[dict[str, Any]] = []
    for item in _as_list(raw.get("acrylic_inserts")):
        entry = _normalize_insert_entry(_as_dict(item))
        if entry is not None:
            inserts.append(entry)

    status = str(raw.get("status") or STATUS_DRAFT).strip().lower()
    if status not in {STATUS_DRAFT, STATUS_CONFIRMED, STATUS_INACTIVE}:
        status = STATUS_DRAFT

    coexistence = compute_coexistence(routed, inserts)
    warnings: list[str] = [WARN_LEGACY_LIGHT_ROUTED_NOT_AUTHORITY]
    blockers: list[str] = []

    if coexistence == COEXISTENCE_NONE:
        warnings.append(WARN_PANEL_ONLY_NO_FACE_TREATMENTS)
    if inserts:
        warnings.append(WARN_INSERT_THICKNESS_NOT_SOLE)

    # Active treatments always face optical/illumination commercial blockers.
    if coexistence != COEXISTENCE_NONE:
        blockers.append(BLOCKER_OPTICAL_CATALOG_MISSING)
        if coexistence in {COEXISTENCE_ROUTED_ONLY, COEXISTENCE_BOTH}:
            blockers.append(BLOCKER_ILLUMINATION_RATES_MISSING)

    ui_badges: dict[str, Any] = {}
    relief_ids = [i["id"] for i in inserts if i.get("ui_badge") == UI_BADGE_RELIEF_PLEXI_10MM]
    if relief_ids:
        ui_badges[UI_BADGE_RELIEF_PLEXI_10MM] = {
            "insert_ids": relief_ids,
            "meaning": "display_badge_for_owner_10mm_variant",
            "product_code": FACE_TREATMENT_ACRYLIC_INSERT,
        }

    overall = "NOT_APPLICABLE"
    if coexistence == COEXISTENCE_NONE:
        overall = "NOT_APPLICABLE"
    elif status == STATUS_CONFIRMED and not blockers:
        overall = "READY_FOR_AGGREGATION"
    elif coexistence != COEXISTENCE_NONE:
        overall = "LOCAL_CONFIGURATION_REQUIRED"

    base.update(
        {
            "status": status,
            "routed_cutouts": routed,
            "acrylic_inserts": inserts,
            "coexistence": coexistence,
            "ui_badges": ui_badges,
            "readiness": {
                "overall": overall,
                "optional_absent_ok": True,
                "blockers": blockers,
                "warnings": warnings,
                # Absent optional treatments must not block panel-only commercial path.
                "panel_only_blocked_by_absent_treatments": False,
            },
        }
    )
    if isinstance(raw.get("provenance"), Mapping):
        prov = dict(base["provenance"])
        prov.update(dict(raw["provenance"]))
        base["provenance"] = prov
    return base


def read_face_treatments(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Read acm_face_treatments from finish_setup / product_truth pin / top-level."""
    if not isinstance(payload, Mapping):
        return normalize_face_treatments(None)

    # Prefer pinned typed bag when present.
    pt = _as_dict(payload.get("product_truth"))
    snap = _as_dict(pt.get("confirmed_snapshot_v1"))
    bags = _as_dict(snap.get("pinned_typed_bags"))
    if BAG_KEY in bags and bags.get(BAG_KEY) is not None:
        return normalize_face_treatments(bags.get(BAG_KEY))

    finish = _as_dict(payload.get("finish_setup"))
    if BAG_KEY in finish:
        return normalize_face_treatments(finish.get(BAG_KEY))
    if BAG_KEY in payload:
        return normalize_face_treatments(payload.get(BAG_KEY))

    # Nested under acm_panel_instance (optional host)
    acm = _as_dict(finish.get("acm_panel_instance"))
    if BAG_KEY in acm:
        return normalize_face_treatments(acm.get(BAG_KEY))

    return normalize_face_treatments(None)


def confirm_face_treatments(raw: Any) -> dict[str, Any]:
    """Mark domain confirmed (operator). Optical commercial blockers remain honest."""
    domain = normalize_face_treatments(raw)
    if domain["coexistence"] == COEXISTENCE_NONE:
        domain["status"] = STATUS_CONFIRMED
        domain["readiness"]["overall"] = "NOT_APPLICABLE"
        return domain
    domain["status"] = STATUS_CONFIRMED
    for entry in domain["routed_cutouts"]:
        if entry.get("status") != STATUS_INACTIVE:
            entry["status"] = STATUS_CONFIRMED
    for entry in domain["acrylic_inserts"]:
        if entry.get("status") != STATUS_INACTIVE:
            entry["status"] = STATUS_CONFIRMED
    # Recompute readiness after confirm.
    return normalize_face_treatments(domain)


def build_quantity_matrix(domain: Mapping[str, Any] | None) -> dict[str, Any]:
    """Quantity ownership matrix — panel keys excluded; optical qty gated."""
    d = normalize_face_treatments(domain) if not isinstance(domain, Mapping) or domain.get("schema") != DOMAIN_SCHEMA else dict(domain)
    if d.get("schema") != DOMAIN_SCHEMA:
        d = normalize_face_treatments(domain)

    routed_rows: list[dict[str, Any]] = []
    for entry in d.get("routed_cutouts") or []:
        if str(entry.get("status") or "").lower() == STATUS_INACTIVE:
            continue
        cf = _as_dict(entry.get("confirmed_fields"))
        routed_rows.append(
            {
                "id": entry.get("id"),
                "keys": {
                    "routed_cut_length_m": cf.get("cut_length_m"),
                    "routed_cutout_count": cf.get("cutout_count"),
                    "optical_backing_area_m2": cf.get("backing_area_m2"),
                },
                "status": "GUARDED" if cf.get("cut_length_m") is None else "CONFIRMED_PARTIAL",
                "owns_panel_sheet": False,
            }
        )

    insert_rows: list[dict[str, Any]] = []
    for entry in d.get("acrylic_inserts") or []:
        if str(entry.get("status") or "").lower() == STATUS_INACTIVE:
            continue
        cf = _as_dict(entry.get("confirmed_fields"))
        insert_rows.append(
            {
                "id": entry.get("id"),
                "keys": {
                    "acrylic_insert_count": cf.get("insert_count"),
                    "acrylic_insert_area_m2": cf.get("insert_area_m2"),
                    "acrylic_insert_thickness_mm": cf.get("thickness_mm"),
                },
                "status": "GUARDED" if cf.get("insert_area_m2") is None else "CONFIRMED_PARTIAL",
                "owns_panel_sheet": False,
                "ui_badge": entry.get("ui_badge"),
            }
        )

    overlap = sorted(PANEL_QUANTITY_KEYS & TREATMENT_QUANTITY_KEYS)
    return {
        "schema": "acm_face_treatment_quantity_matrix_v1",
        "panel_quantity_keys": sorted(PANEL_QUANTITY_KEYS),
        "treatment_quantity_keys": sorted(TREATMENT_QUANTITY_KEYS),
        "key_overlap_with_panel": overlap,
        "double_sheet_guard_ok": len(overlap) == 0,
        "routed": routed_rows,
        "acrylic_inserts": insert_rows,
        "coexistence": d.get("coexistence"),
    }


def build_ops_intents(domain: Mapping[str, Any] | None) -> dict[str, Any]:
    """Guarded process intents — identity only; no invented CNC rates."""
    if isinstance(domain, Mapping) and domain.get("schema") == DOMAIN_SCHEMA:
        d = normalize_face_treatments(domain)
    elif isinstance(domain, Mapping) and BAG_KEY in domain:
        d = read_face_treatments(domain)
    else:
        d = normalize_face_treatments(domain)
    intents: list[dict[str, Any]] = []
    for entry in d.get("routed_cutouts") or []:
        if str(entry.get("status") or "").lower() == STATUS_INACTIVE:
            continue
        intents.append(
            {
                "owner": MODULE_ROUTED_BACKLIT,
                "entry_id": entry.get("id"),
                "process_intents": [
                    "cnc_route_acp_face",
                    "cut_plexiglas_backing",
                    "mount_plexiglas_backing",
                    "led_cavity_intent",
                    "electrical_test_intent",
                ],
                "rate_status": "BLOCKED",
                "blocker": BLOCKER_OPTICAL_CATALOG_MISSING,
            }
        )
    for entry in d.get("acrylic_inserts") or []:
        if str(entry.get("status") or "").lower() == STATUS_INACTIVE:
            continue
        intents.append(
            {
                "owner": MODULE_ACRYLIC_INSERT,
                "entry_id": entry.get("id"),
                "process_intents": [
                    "cnc_route_acp_insert_pocket",
                    "cut_plexiglas_insert",
                    "fit_insert",
                    "retain_insert",
                    "illumination_intent",
                ],
                "rate_status": "BLOCKED",
                "blocker": BLOCKER_OPTICAL_CATALOG_MISSING,
            }
        )
    return {
        "schema": "acm_face_treatment_ops_intents_v1",
        "intents": intents,
        "shell_owns_panel_ops": True,
        "no_double_panel_ops": True,
    }


def build_cpp_eic_commercial_gate(domain: Mapping[str, Any] | None) -> dict[str, Any]:
    """Honest CPP/EIC gate for face treatments — never invent optical rates."""
    d = normalize_face_treatments(domain) if not (
        isinstance(domain, Mapping) and domain.get("schema") == DOMAIN_SCHEMA
    ) else dict(domain)
    coexistence = d.get("coexistence") or COEXISTENCE_NONE
    treatment_lines_allowed = False
    blockers: list[str] = []
    if coexistence != COEXISTENCE_NONE:
        blockers = [
            BLOCKER_OPTICAL_CATALOG_MISSING,
            BLOCKER_ILLUMINATION_RATES_MISSING,
        ]
    return {
        "schema": "acm_face_treatment_cpp_eic_gate_v1",
        "panel_cpp_path": "unchanged_acm_panel_commercial_geometry",
        "treatment_commercial_lines_allowed": treatment_lines_allowed,
        "coexistence": coexistence,
        "blockers": blockers,
        "policy": (
            "Panel-only ACM CPP/EIC remains valid. Face-treatment optical/electrical "
            "lines stay BLOCKED until owner optical catalog GO. Do not invent rates."
        ),
        "resource_authority": RESOURCE_AUTHORITY,
    }


def project_for_product_definition(domain: Mapping[str, Any] | None) -> dict[str, Any]:
    """PD projection — instances + quantity matrix + ops + commercial gate."""
    d = normalize_face_treatments(domain) if not (
        isinstance(domain, Mapping) and domain.get("schema") == DOMAIN_SCHEMA
    ) else normalize_face_treatments(domain)
    modules = []
    for entry in (d.get("routed_cutouts") or []) + (d.get("acrylic_inserts") or []):
        if str(entry.get("status") or "").lower() == STATUS_INACTIVE:
            continue
        mod = entry.get("local_module_configuration")
        if isinstance(mod, Mapping):
            modules.append(dict(mod))
    return {
        "acm_face_treatments": d,
        "acm_face_treatment_quantity_matrix": build_quantity_matrix(d),
        "acm_face_treatment_ops_intents": build_ops_intents(d),
        "acm_face_treatment_cpp_eic_gate": build_cpp_eic_commercial_gate(d),
        "acp_local_face_module_instances_from_face_treatments": modules,
    }


def project_for_aggregate(domain: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Aggregate projection — identity + intents; never folds panel sheet materials."""
    d = normalize_face_treatments(domain) if not (
        isinstance(domain, Mapping) and domain.get("schema") == DOMAIN_SCHEMA
    ) else normalize_face_treatments(domain)
    if d.get("coexistence") == COEXISTENCE_NONE:
        return {
            "kind": "acm_face_treatments",
            "schema": DOMAIN_SCHEMA,
            "coexistence": COEXISTENCE_NONE,
            "optional_absent_ok": True,
            "materials": [],
            "operations": [],
            "notes": ["No face treatments — panel-only path unaffected."],
        }
    qty = build_quantity_matrix(d)
    ops = build_ops_intents(d)
    gate = build_cpp_eic_commercial_gate(d)
    return {
        "kind": "acm_face_treatments",
        "schema": DOMAIN_SCHEMA,
        "coexistence": d.get("coexistence"),
        "routed_count": len([r for r in (d.get("routed_cutouts") or []) if r.get("status") != STATUS_INACTIVE]),
        "insert_count": len([i for i in (d.get("acrylic_inserts") or []) if i.get("status") != STATUS_INACTIVE]),
        "quantity_matrix": qty,
        "ops_intents": ops,
        "cpp_eic_gate": gate,
        "materials": [],  # optical materials blocked — do not invent
        "operations": [],
        "owns_panel_sheet": False,
        "double_sheet_guard_ok": qty.get("double_sheet_guard_ok"),
        "notes": [
            "Face treatments projected without ACM panel sheet materials.",
            "Optical/electrical commercial lines BLOCKED pending owner catalog.",
        ],
    }


def merge_face_treatments_into_payload(
    payload: MutableMapping[str, Any] | Mapping[str, Any],
    domain: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Ensure finish_setup.acm_face_treatments is present and normalized."""
    out = dict(payload)
    finish = _as_dict(out.get("finish_setup"))
    source = domain if domain is not None else finish.get(BAG_KEY) or out.get(BAG_KEY)
    normalized = normalize_face_treatments(source)
    finish[BAG_KEY] = normalized
    out["finish_setup"] = finish
    out[BAG_KEY] = normalized
    out["face_treatment_coexistence"] = normalized.get("coexistence")
    return out


def readiness_finding_for_template(payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Scoped readiness evidence for Product E2E Readiness — non-blocking for panel-only."""
    domain = read_face_treatments(payload)
    coexistence = domain.get("coexistence")
    blockers = list((domain.get("readiness") or {}).get("blockers") or [])
    # Commercial optical blockers are warnings for publication KEEP_DRAFT —
    # they must not block panel-only configuration.
    status = "PASS"
    if coexistence == COEXISTENCE_NONE:
        status = "PASS"
        message = (
            "ACM face-treatment commercial path present; no treatments selected "
            "(panel-only allowed)."
        )
    elif blockers:
        status = "PASS_WITH_WARNINGS"
        message = (
            f"Face treatments coexistence={coexistence}; optical/illumination "
            "commercial lines honestly BLOCKED (missing catalog)."
        )
    else:
        status = "PASS"
        message = f"Face treatments coexistence={coexistence}; commercial path ready."

    return {
        "check_id": "components.acm_face_treatment_commercial_path",
        "status": status,
        "message": message,
        "blocking": False,
        "evidence": {
            "schema": DOMAIN_SCHEMA,
            "coexistence": coexistence,
            "routed_codes": [FACE_TREATMENT_ROUTED_BACKLIT],
            "insert_codes": [FACE_TREATMENT_ACRYLIC_INSERT],
            "module_routed": MODULE_ROUTED_BACKLIT,
            "module_insert": MODULE_ACRYLIC_INSERT,
            "ui_badge_relief": UI_BADGE_RELIEF_PLEXI_10MM,
            "orthogonal_to_xor": True,
            "optional_absent_ok": True,
            "optical_blockers": blockers,
            "panel_only_blocked_by_absent_treatments": False,
            "publication": "KEEP_DRAFT",
        },
    }


def scenario_matrix() -> list[dict[str, Any]]:
    """Canonical coexistence scenarios for tests / evidence."""
    scenarios = []
    for name, routed_n, insert_n in (
        ("panel_only", 0, 0),
        ("routed_only", 1, 0),
        ("insert_only", 0, 1),
        ("both", 1, 1),
    ):
        raw: dict[str, Any] = {
            "routed_cutouts": [
                {"geometry_role": GEOMETRY_ROLE_CUTOUT_TEXT, "status": STATUS_DRAFT}
                for _ in range(routed_n)
            ],
            "acrylic_inserts": [
                {"geometry_role": GEOMETRY_ROLE_ACRYLIC_INSERT, "status": STATUS_DRAFT}
                for _ in range(insert_n)
            ],
        }
        domain = normalize_face_treatments(raw)
        scenarios.append(
            {
                "name": name,
                "coexistence": domain["coexistence"],
                "quantity": build_quantity_matrix(domain),
                "ops": build_ops_intents(domain),
                "cpp_eic": build_cpp_eic_commercial_gate(domain),
                "aggregate": project_for_aggregate(domain),
            }
        )
    return scenarios
