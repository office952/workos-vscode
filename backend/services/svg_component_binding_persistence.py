"""Unified SVG → Product System component bindings for FinishSetup / ProductDefinition.

Single persistence authority for Intake component-aware assignment.
Extends bindings with optional face_treatment fields (additive, backwards compatible).
No DB migration — JSON document fields on finish_setup.
"""

from __future__ import annotations

import hashlib
from typing import Any

from data.product_system.acp_face_treatment_registry_v1 import (
    FACE_TREATMENT_NOT_APPLICABLE,
    LIVE_ACP_SHELL_TEMPLATE,
    READINESS_CONFIRMED,
    READINESS_INACTIVE,
    READINESS_LOCAL_CONFIGURATION_REQUIRED,
    READINESS_NOT_APPLICABLE,
    READINESS_READY_FOR_AGGREGATION,
    REGISTRY_VERSION,
    get_face_treatment,
    is_shell_local_treatment,
    legacy_light_routed_policy,
)
from services.acp_local_face_module_service import (
    build_local_module_aggregate_projection,
    normalize_acp_electrical_configuration,
    normalize_local_module,
)
from data.product_system.svg_component_binding_contract import (
    ACM_BOXED_SUPPORT,
    FACE_COMPONENT,
    GEOMETRY_ROLE_ACRYLIC_INSERT,
    GEOMETRY_ROLE_CUTOUT_LOGO,
    GEOMETRY_ROLE_CUTOUT_TEXT,
    GEOMETRY_ROLE_DECORATIVE_VECTOR,
    GEOMETRY_ROLE_LETTER_VECTOR_SET,
    GEOMETRY_ROLE_LOGO_VECTOR_SET,
    GEOMETRY_ROLE_SUPPORT_CONTOUR,
    LOGO_PRODUCT,
    STALE_BOND_CASETAT,
)

SVG_COMPONENT_BINDINGS_SCHEMA = "svg_component_bindings_v1"
BINDING_STATUS_CONFIRMED = "CONFIRMED"
BINDING_STATUS_RECONFIRM = "RECONFIRM_REQUIRED"
BINDING_STATUS_DRAFT = "DRAFT"
BINDING_STATUS_INACTIVE = "INACTIVE"

SHELL_LOCAL_GEOMETRY_ROLES = frozenset(
    {
        GEOMETRY_ROLE_CUTOUT_TEXT,
        GEOMETRY_ROLE_CUTOUT_LOGO,
        GEOMETRY_ROLE_ACRYLIC_INSERT,
        GEOMETRY_ROLE_DECORATIVE_VECTOR,
    }
)

LEGACY_SHELL_ROLES = frozenset(
    {
        GEOMETRY_ROLE_LETTER_VECTOR_SET,
        GEOMETRY_ROLE_LOGO_VECTOR_SET,
        GEOMETRY_ROLE_SUPPORT_CONTOUR,
    }
)


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _stable_zone_id(
    *,
    binding_id: str,
    geometry_role: str,
    component_template_code: str,
    selected_geometry: dict[str, Any],
) -> str:
    """Stable local zone identity — not array index, not layer label order."""
    if binding_id.startswith("zone_"):
        return binding_id
    ids = sorted(
        str(x)
        for x in (
            list(_as_list(selected_geometry.get("element_ids")))
            + list(_as_list(selected_geometry.get("layer_ids")))
            + list(_as_list(selected_geometry.get("group_ids")))
        )
        if x
    )
    digest_src = "|".join(
        [
            geometry_role,
            component_template_code,
            ",".join(ids),
            str(selected_geometry.get("source_svg_hash") or ""),
        ]
    )
    digest = hashlib.sha1(digest_src.encode("utf-8")).hexdigest()[:12]
    return f"zone_{geometry_role.lower()}_{digest}"


def _normalize_provenance(raw: Any, selected_geometry: dict[str, Any]) -> dict[str, Any]:
    if isinstance(raw, dict):
        out = dict(raw)
    elif isinstance(raw, str) and raw.strip():
        out = {"source": "legacy_string", "legacy_note": raw.strip()}
    else:
        out = {"source": "operator"}
    hashes = [str(x) for x in _as_list(selected_geometry.get("geometry_hashes")) if x]
    if hashes and not out.get("geometry_hash"):
        out["geometry_hash"] = hashes[0]
    if selected_geometry.get("source_svg_hash") and not out.get("svg_hash"):
        out["svg_hash"] = selected_geometry.get("source_svg_hash")
    out.setdefault("face_treatment_registry_version", REGISTRY_VERSION)
    return out


def normalize_binding(raw: dict[str, Any]) -> dict[str, Any]:
    """Additive normalize — missing face_treatment does not invalidate legacy bindings."""
    b = dict(raw)
    role = str(b.get("geometry_role") or "").strip()
    code = str(b.get("component_template_code") or "").strip()
    geom = _as_dict(b.get("selected_geometry"))
    binding_id = str(b.get("binding_id") or "").strip()
    if not binding_id:
        ids = [str(x) for x in _as_list(geom.get("element_ids")) if x]
        ids.extend(str(x) for x in _as_list(geom.get("layer_ids")) if x)
        digest = hashlib.sha1(f"{role}|{code}|{','.join(ids)}".encode("utf-8")).hexdigest()[:10]
        binding_id = f"bind_{role.lower() or 'geom'}_{digest}"
    b["schema"] = SVG_COMPONENT_BINDINGS_SCHEMA
    b["binding_id"] = binding_id
    b["geometry_role"] = role
    b["component_template_code"] = code
    b["selected_geometry"] = {
        "layer_ids": [str(x) for x in _as_list(geom.get("layer_ids")) if x],
        "group_ids": [str(x) for x in _as_list(geom.get("group_ids")) if x],
        "element_ids": [str(x) for x in _as_list(geom.get("element_ids")) if x],
        "geometry_hashes": [str(x) for x in _as_list(geom.get("geometry_hashes")) if x],
        "source_svg_hash": geom.get("source_svg_hash"),
    }
    b["local_zone_id"] = str(b.get("local_zone_id") or "").strip() or _stable_zone_id(
        binding_id=binding_id,
        geometry_role=role,
        component_template_code=code,
        selected_geometry=b["selected_geometry"],
    )
    b["provenance"] = _normalize_provenance(b.get("provenance"), b["selected_geometry"])

    treatment_raw = b.get("face_treatment_code")
    if treatment_raw is None or str(treatment_raw).strip() == "":
        # Legacy roles: treatment optional / NOT_APPLICABLE — never invent routed/insert.
        if role in LEGACY_SHELL_ROLES:
            b["face_treatment_code"] = FACE_TREATMENT_NOT_APPLICABLE
        else:
            b["face_treatment_code"] = None
    else:
        b["face_treatment_code"] = str(treatment_raw).strip()

    status = str(b.get("status") or BINDING_STATUS_DRAFT).strip() or BINDING_STATUS_DRAFT
    b["status"] = status
    confirmation = str(b.get("confirmation_status") or status).strip()
    b["confirmation_status"] = confirmation

    if b.get("face_treatment_code") in {None, "", FACE_TREATMENT_NOT_APPLICABLE}:
        b["local_configuration_status"] = b.get("local_configuration_status") or "NOT_APPLICABLE"
        b.pop("local_module_configuration", None)
    else:
        row = get_face_treatment(b.get("face_treatment_code"))
        if row and row.get("requires_local_module"):
            b["local_configuration_status"] = (
                b.get("local_configuration_status") or row.get("local_configuration_status_default") or "NOT_CONFIGURED"
            )
        else:
            b["local_configuration_status"] = b.get("local_configuration_status") or "NOT_REQUIRED"
        module = normalize_local_module(
            b.get("local_module_configuration"),
            binding_id=binding_id,
            treatment_code=str(b.get("face_treatment_code") or "") or None,
            geometry_role=role,
            component_template_code=code,
            status=status,
        )
        if module:
            b["local_module_configuration"] = module
            mod_ready = (module.get("readiness") or {}).get("overall")
            if mod_ready:
                b["local_configuration_status"] = mod_ready

    b["face_treatment_contract_version"] = REGISTRY_VERSION
    return b


def normalize_svg_component_bindings(bindings: list[Any] | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in bindings or []:
        if isinstance(item, dict) and item.get("component_template_code"):
            out.append(normalize_binding(item))
    return out


def read_svg_component_bindings(finish: dict[str, Any] | None) -> list[dict[str, Any]]:
    finish = finish or {}
    raw = finish.get("svg_component_bindings")
    if not isinstance(raw, list):
        return []
    return normalize_svg_component_bindings(raw)


def validate_bindings_for_new_selection(bindings: list[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    support_count = 0
    normalized = normalize_svg_component_bindings(bindings)
    for b in normalized:
        code = str(b.get("component_template_code") or "").strip()
        role = str(b.get("geometry_role") or "")
        treatment = b.get("face_treatment_code")
        if code == STALE_BOND_CASETAT:
            blockers.append("TPL-BOND-CASETAT is legacy and cannot be used for new selection.")
        if code == legacy_light_routed_policy()["template_code"]:
            blockers.append(
                "TPL-ACP-LIGHT-ROUTED is PARALLEL_LEGACY_COST_PATH and cannot be used as "
                "Intake V6 face-treatment / SVG binding authority."
            )
        if role == GEOMETRY_ROLE_SUPPORT_CONTOUR and str(b.get("status") or "") in {
            BINDING_STATUS_CONFIRMED,
            BINDING_STATUS_DRAFT,
        }:
            support_count += 1
        if role == GEOMETRY_ROLE_SUPPORT_CONTOUR and code == FACE_COMPONENT:
            blockers.append("SUPPORT_CONTOUR cannot bind to letters face component.")
        if role == GEOMETRY_ROLE_LETTER_VECTOR_SET and code == ACM_BOXED_SUPPORT:
            blockers.append("LETTER_VECTOR_SET cannot bind to Alucobond support component.")
        if role in SHELL_LOCAL_GEOMETRY_ROLES and code not in {ACM_BOXED_SUPPORT, LIVE_ACP_SHELL_TEMPLATE}:
            blockers.append(f"{role} must bind to {ACM_BOXED_SUPPORT} (ACP shell ownership).")
        if treatment and treatment != FACE_TREATMENT_NOT_APPLICABLE:
            row = get_face_treatment(str(treatment))
            if row is None:
                blockers.append(f"Unknown face_treatment_code: {treatment}")
            else:
                allowed_roles = set(row.get("allowed_geometry_roles") or [])
                allowed_comps = set(row.get("allowed_component_template_codes") or [])
                if role and allowed_roles and role not in allowed_roles:
                    blockers.append(
                        f"face_treatment {treatment} incompatible with geometry_role {role}."
                    )
                if code and allowed_comps and code not in allowed_comps:
                    blockers.append(
                        f"face_treatment {treatment} incompatible with component {code}."
                    )
    if support_count > 1:
        blockers.append("V1 allows at most one SUPPORT_CONTOUR / ACP shell binding.")
    return blockers


def sync_support_selection_from_bindings(finish: dict[str, Any]) -> dict[str, Any]:
    """Ensure svg_support_selection mirrors confirmed SUPPORT_CONTOUR binding (legacy adapters)."""
    bindings = read_svg_component_bindings(finish)
    # Must require SUPPORT_CONTOUR — do not pick cutout/insert ACM bindings.
    support = next(
        (b for b in bindings if str(b.get("geometry_role") or "") == GEOMETRY_ROLE_SUPPORT_CONTOUR),
        None,
    )
    if not support:
        return finish
    status = str(support.get("status") or "").strip()
    geom = _as_dict(support.get("selected_geometry"))
    config = _as_dict(support.get("configuration"))
    if status == BINDING_STATUS_RECONFIRM:
        finish["svg_support_selection"] = {
            "schema": "svg_support_selection_v1",
            "status": "reconfirm_required",
            "contour_id": (geom.get("element_ids") or [None])[0],
            "geometry_hash": (geom.get("geometry_hashes") or [None])[0],
            "svg_source_hash": geom.get("source_svg_hash"),
        }
        return finish
    if status != BINDING_STATUS_CONFIRMED:
        return finish
    existing = _as_dict(finish.get("svg_support_selection"))
    element_ids = [str(x) for x in _as_list(geom.get("element_ids")) if x]
    hashes = [str(x) for x in _as_list(geom.get("geometry_hashes")) if x]
    contour_id = element_ids[0] if element_ids else support.get("contour_id") or existing.get("contour_id")
    finish["svg_support_selection"] = {
        "schema": "svg_support_selection_v1",
        "status": "confirmed",
        "role": "ALUCOBOND_CASED_PANEL",
        "contour_id": contour_id,
        "svg_support_element_id": support.get("svg_support_element_id")
        or existing.get("svg_support_element_id")
        or contour_id,
        "geometry_hash": hashes[0]
        if hashes
        else support.get("geometry_hash") or existing.get("geometry_hash"),
        "svg_source_hash": geom.get("source_svg_hash")
        or support.get("svg_source_hash")
        or existing.get("svg_source_hash"),
        "panel_geometry": support.get("panel_geometry")
        or config.get("panel_geometry")
        or existing.get("panel_geometry"),
        "casing_profile": {
            "fold_count": config.get("fold_count"),
            "l1_mm": config.get("l1_mm"),
            "l2_mm": config.get("l2_mm"),
            "finished_depth_mm": config.get("finished_depth_mm") or config.get("l1_mm"),
        }
        if config.get("fold_count") is not None
        else support.get("casing_profile") or existing.get("casing_profile"),
        "service_corner": config.get("service_corner")
        or support.get("service_corner")
        or existing.get("service_corner"),
        "internal_frame_enabled": bool(
            config.get(
                "internal_frame_enabled",
                support.get("internal_frame_enabled", existing.get("internal_frame_enabled")),
            )
        ),
        "candidate_explanation": support.get("candidate_explanation")
        or existing.get("candidate_explanation")
        or [],
        "unit_ambiguity": bool(support.get("unit_ambiguity", existing.get("unit_ambiguity"))),
        "confirmed_at": support.get("confirmed_at") or existing.get("confirmed_at"),
        "component_template_code": ACM_BOXED_SUPPORT,
        "geometry_role": GEOMETRY_ROLE_SUPPORT_CONTOUR,
    }
    finish["svg_component_bindings"] = bindings
    return finish


def hydrate_bindings_from_legacy_support(finish: dict[str, Any]) -> list[dict[str, Any]]:
    """If only svg_support_selection exists, project a SUPPORT_CONTOUR binding for read compatibility."""
    existing = read_svg_component_bindings(finish)
    if existing:
        return existing
    selection = _as_dict(finish.get("svg_support_selection"))
    if selection.get("schema") != "svg_support_selection_v1":
        return []
    status_raw = str(selection.get("status") or "")
    if status_raw == "confirmed" and selection.get("role") == "ALUCOBOND_CASED_PANEL":
        status = BINDING_STATUS_CONFIRMED
    elif status_raw == "proposed" and selection.get("role") == "ALUCOBOND_CASED_PANEL":
        status = BINDING_STATUS_DRAFT
    elif status_raw == "reconfirm_required":
        status = BINDING_STATUS_RECONFIRM
    else:
        return []
    casing = _as_dict(selection.get("casing_profile"))
    return normalize_svg_component_bindings(
        [
            {
                "schema": SVG_COMPONENT_BINDINGS_SCHEMA,
                "binding_id": f"bind_support_{selection.get('contour_id') or 'legacy'}",
                "geometry_role": GEOMETRY_ROLE_SUPPORT_CONTOUR,
                "component_template_code": ACM_BOXED_SUPPORT,
                "selection_mode": "CLOSED_CONTOUR",
                "selected_geometry": {
                    "layer_ids": [],
                    "group_ids": [],
                    "element_ids": [selection.get("contour_id")] if selection.get("contour_id") else [],
                    "geometry_hashes": [selection.get("geometry_hash")]
                    if selection.get("geometry_hash")
                    else [],
                    "source_svg_hash": selection.get("svg_source_hash"),
                },
                "configuration": {
                    "fold_count": casing.get("fold_count"),
                    "l1_mm": casing.get("l1_mm"),
                    "l2_mm": casing.get("l2_mm"),
                    "finished_depth_mm": casing.get("finished_depth_mm"),
                    "service_corner": selection.get("service_corner"),
                    "internal_frame_enabled": bool(selection.get("internal_frame_enabled")),
                },
                "panel_geometry": selection.get("panel_geometry"),
                "status": status,
                "face_treatment_code": FACE_TREATMENT_NOT_APPLICABLE,
                "provenance": "legacy_svg_support_selection",
            }
        ]
    )


def evaluate_face_treatment_readiness(binding: dict[str, Any]) -> dict[str, Any]:
    """Per-binding face-treatment readiness (foundation — no BOM/tasking)."""
    status = str(binding.get("status") or "").strip()
    confirmation = str(binding.get("confirmation_status") or status).strip()
    treatment = binding.get("face_treatment_code")
    role = str(binding.get("geometry_role") or "")

    if status in {BINDING_STATUS_INACTIVE, BINDING_STATUS_DRAFT} and role in SHELL_LOCAL_GEOMETRY_ROLES:
        # Inactive local treatments: zero warnings / no projection pressure.
        return {
            "readiness": READINESS_INACTIVE,
            "warnings": [],
            "blockers": [],
            "actionable": False,
        }

    if treatment in {None, "", FACE_TREATMENT_NOT_APPLICABLE}:
        return {
            "readiness": READINESS_NOT_APPLICABLE,
            "warnings": [],
            "blockers": [],
            "actionable": False,
        }

    row = get_face_treatment(str(treatment))
    if row is None:
        return {
            "readiness": "UNKNOWN_TREATMENT",
            "warnings": [],
            "blockers": [f"unknown_face_treatment:{treatment}"],
            "actionable": True,
        }

    if confirmation not in {BINDING_STATUS_CONFIRMED, READINESS_CONFIRMED}:
        return {
            "readiness": confirmation or READINESS_INACTIVE,
            "warnings": [],
            "blockers": [],
            "actionable": False,
        }

    if row.get("requires_local_module"):
        local_status = str(binding.get("local_configuration_status") or "NOT_CONFIGURED")
        if local_status in {"NOT_CONFIGURED", "LOCAL_CONFIGURATION_REQUIRED"}:
            return {
                "readiness": READINESS_LOCAL_CONFIGURATION_REQUIRED,
                "warnings": [
                    {
                        "code": "FACE_TREATMENT_LOCAL_MODULE_REQUIRED",
                        "message": (
                            f"Treatment {treatment} confirmed; technical local module "
                            "not configured yet (V1 foundation)."
                        ),
                        "binding_id": binding.get("binding_id"),
                        "local_zone_id": binding.get("local_zone_id"),
                    }
                ],
                "blockers": [],
                "actionable": True,
            }

    return {
        "readiness": READINESS_READY_FOR_AGGREGATION,
        "warnings": [],
        "blockers": [],
        "actionable": False,
    }


def build_face_treatment_instance(binding: dict[str, Any]) -> dict[str, Any] | None:
    """PD face_treatment_instance — identity only, no materials/processes."""
    treatment = binding.get("face_treatment_code")
    if treatment in {None, "", FACE_TREATMENT_NOT_APPLICABLE}:
        return None
    if not is_shell_local_treatment(str(treatment)) and str(binding.get("geometry_role") or "") not in {
        GEOMETRY_ROLE_LETTER_VECTOR_SET,
        GEOMETRY_ROLE_LOGO_VECTOR_SET,
    }:
        # Shell-local treatments only nested under ACP; applied volumetric stays on letter instance.
        if str(binding.get("component_template_code") or "") != ACM_BOXED_SUPPORT:
            return None
    status = str(binding.get("status") or "")
    if status == BINDING_STATUS_INACTIVE:
        return None
    if status not in {BINDING_STATUS_CONFIRMED, BINDING_STATUS_RECONFIRM, BINDING_STATUS_DRAFT}:
        return None
    geom = _as_dict(binding.get("selected_geometry"))
    ids = [str(x) for x in _as_list(geom.get("element_ids")) if x]
    ids.extend(str(x) for x in _as_list(geom.get("layer_ids")) if x)
    readiness = evaluate_face_treatment_readiness(binding)
    module = _as_dict(binding.get("local_module_configuration"))
    out = {
        "instance_id": binding.get("binding_id"),
        "zone_id": binding.get("local_zone_id"),
        "geometry_role": binding.get("geometry_role"),
        "face_treatment_code": treatment,
        "source_geometry_ids": ids,
        "confirmation_status": binding.get("confirmation_status") or status,
        "local_configuration_status": binding.get("local_configuration_status") or "NOT_CONFIGURED",
        "readiness": readiness.get("readiness"),
        "provenance": _as_dict(binding.get("provenance")),
        "component_template_code": binding.get("component_template_code"),
    }
    if module:
        out["local_module_instance"] = {
            "module_instance_id": module.get("module_instance_id") or module.get("interface_instance_id"),
            "module_code": module.get("module_code"),
            "status": module.get("status"),
            "readiness": (module.get("readiness") or {}).get("overall"),
            "gates": (module.get("readiness") or {}).get("gates") or [],
            "configuration": {
                k: module.get(k)
                for k in (
                    "backing_material",
                    "backing_mounting",
                    "illumination_intent",
                    "insert",
                    "service",
                    "placement_reference",
                    "mounting_method_status",
                    "cable_passage_status",
                    "electrical_interface_status",
                )
                if module.get(k) is not None
            },
        }
    return out


def build_svg_component_instances(finish: dict[str, Any] | None) -> list[dict[str, Any]]:
    """ProductDefinition projection: component instances + nested ACP face treatments."""
    finish = finish or {}
    bindings = read_svg_component_bindings(finish) or hydrate_bindings_from_legacy_support(finish)
    instances: list[dict[str, Any]] = []
    shell_treatments: list[dict[str, Any]] = []
    shell_instance_index: int | None = None

    for b in bindings:
        status = str(b.get("status") or "")
        role = str(b.get("geometry_role") or "")
        code = str(b.get("component_template_code") or "").strip()
        if not code or code == STALE_BOND_CASETAT:
            continue

        # Shell-local face treatments nest under the SUPPORT_CONTOUR instance — not separate products.
        if role in SHELL_LOCAL_GEOMETRY_ROLES and code == ACM_BOXED_SUPPORT:
            if status == BINDING_STATUS_INACTIVE:
                continue
            ft = build_face_treatment_instance(b)
            if ft:
                shell_treatments.append(ft)
            continue

        if status not in {BINDING_STATUS_CONFIRMED, BINDING_STATUS_RECONFIRM}:
            continue

        geom = _as_dict(b.get("selected_geometry"))
        ids = [str(x) for x in _as_list(geom.get("element_ids")) if x]
        ids.extend(str(x) for x in _as_list(geom.get("layer_ids")) if x)
        readiness = evaluate_face_treatment_readiness(b)
        instance: dict[str, Any] = {
            "component_template_code": code,
            "geometry_role": role,
            "selection_mode": b.get("selection_mode"),
            "selected_geometry_ids": ids,
            "geometry_hashes": list(_as_list(geom.get("geometry_hashes"))),
            "source_svg_hash": geom.get("source_svg_hash"),
            "configuration": _as_dict(b.get("configuration")),
            "status": status,
            "binding_id": b.get("binding_id"),
            "local_zone_id": b.get("local_zone_id"),
            "face_treatment_code": b.get("face_treatment_code"),
            "face_treatment_readiness": readiness.get("readiness"),
            "confirmation_status": b.get("confirmation_status") or status,
            "provenance": _as_dict(b.get("provenance")),
        }
        if code == FACE_COMPONENT or role == GEOMETRY_ROLE_LETTER_VECTOR_SET:
            instance["legacy_layer_role"] = "face"
            ft = build_face_treatment_instance(b)
            if ft:
                instance["face_treatment_instances"] = [ft]
        if code == LOGO_PRODUCT or role == GEOMETRY_ROLE_LOGO_VECTOR_SET:
            instance["legacy_layer_role"] = "printed_artwork"
            ft = build_face_treatment_instance(b)
            if ft:
                instance["face_treatment_instances"] = [ft]
        if role == GEOMETRY_ROLE_SUPPORT_CONTOUR and code == ACM_BOXED_SUPPORT:
            instance["face_treatment_instances"] = []  # filled after loop
            shell_instance_index = len(instances)
        instances.append(instance)

    if shell_instance_index is not None:
        instances[shell_instance_index]["face_treatment_instances"] = shell_treatments
    elif shell_treatments:
        # Treatments without shell contour still project as identity under synthetic shell host.
        instances.append(
            {
                "component_template_code": ACM_BOXED_SUPPORT,
                "geometry_role": GEOMETRY_ROLE_SUPPORT_CONTOUR,
                "status": BINDING_STATUS_DRAFT,
                "binding_id": "bind_support_host_for_face_treatments",
                "face_treatment_instances": shell_treatments,
                "note": "face_treatments_without_confirmed_support_contour",
            }
        )

    return instances


def build_face_treatment_readiness_summary(finish: dict[str, Any] | None) -> dict[str, Any]:
    """Lifecycle foundation projection — per treatment, inactive = zero warnings."""
    finish = finish or {}
    bindings = read_svg_component_bindings(finish) or hydrate_bindings_from_legacy_support(finish)
    items: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for b in bindings:
        role = str(b.get("geometry_role") or "")
        treatment = b.get("face_treatment_code")
        if role not in SHELL_LOCAL_GEOMETRY_ROLES and treatment in {
            None,
            "",
            FACE_TREATMENT_NOT_APPLICABLE,
        }:
            continue
        readiness = evaluate_face_treatment_readiness(b)
        if readiness.get("readiness") == READINESS_INACTIVE:
            items.append(
                {
                    "binding_id": b.get("binding_id"),
                    "local_zone_id": b.get("local_zone_id"),
                    "geometry_role": role,
                    "face_treatment_code": treatment,
                    "readiness": READINESS_INACTIVE,
                }
            )
            continue
        entry = {
            "binding_id": b.get("binding_id"),
            "local_zone_id": b.get("local_zone_id"),
            "geometry_role": role,
            "face_treatment_code": treatment,
            "component_template_code": b.get("component_template_code"),
            "readiness": readiness.get("readiness"),
            "local_configuration_status": b.get("local_configuration_status"),
        }
        items.append(entry)
        for w in readiness.get("warnings") or []:
            warnings.append(w)
    return {
        "schema": "face_treatment_readiness_v1",
        "registry_version": REGISTRY_VERSION,
        "items": items,
        "warnings": warnings,
        "legacy_light_routed": legacy_light_routed_policy(),
        "shell_template": ACM_BOXED_SUPPORT,
    }


def persist_normalized_bindings_on_finish(finish: dict[str, Any]) -> dict[str, Any]:
    """Normalize bindings in-place on a finish dict (save path)."""
    finish = dict(finish)
    finish["svg_component_bindings"] = read_svg_component_bindings(finish)
    service_corner = None
    mounting = _as_dict(finish.get("mounting_solution"))
    cfg = _as_dict(mounting.get("configuration"))
    service_corner = (
        cfg.get("service_corner")
        or finish.get("power_supply_service_corner")
        or _as_dict(finish.get("svg_support_selection")).get("service_corner")
    )
    finish["acp_electrical_configuration"] = normalize_acp_electrical_configuration(
        finish.get("acp_electrical_configuration"),
        bindings=finish["svg_component_bindings"],
        service_corner=str(service_corner) if service_corner else None,
    )
    return finish


def collect_local_modules_from_finish(finish: dict[str, Any] | None) -> list[dict[str, Any]]:
    modules: list[dict[str, Any]] = []
    for b in read_svg_component_bindings(finish):
        mod = _as_dict(b.get("local_module_configuration"))
        if mod.get("module_code"):
            modules.append(mod)
    return modules


def build_acp_local_modules_aggregate_from_finish(finish: dict[str, Any] | None) -> dict[str, Any] | None:
    finish = finish or {}
    modules = collect_local_modules_from_finish(finish)
    electrical = finish.get("acp_electrical_configuration")
    return build_local_module_aggregate_projection(modules, electrical=_as_dict(electrical) or None)
