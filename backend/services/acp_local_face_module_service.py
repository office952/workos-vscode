"""Normalize / readiness / guarded Aggregate projection for ACP local face modules."""

from __future__ import annotations

import hashlib
from typing import Any, Mapping

from data.product_system.acp_face_treatment_registry_v1 import (
    FACE_TREATMENT_NOT_APPLICABLE,
    READINESS_INACTIVE,
    READINESS_LOCAL_CONFIGURATION_REQUIRED,
    READINESS_NOT_APPLICABLE,
    READINESS_READY_FOR_AGGREGATION,
)
from data.product_system.acp_local_face_modules_v1 import (
    ELECTRICAL_OWNERSHIP_MODE,
    GATE_MANUAL,
    GATE_OWNER_REQUIRED,
    GATE_OWNER_REVIEW,
    INSERT_THICKNESS_OWNER_VARIANT_MM,
    INSERT_THICKNESS_PROVENANCE,
    INTERFACE_APPLIED_VOLUMETRIC,
    MODULE_ACRYLIC_INSERT,
    MODULE_PLAIN_DECORATIVE,
    MODULE_ROUTED_BACKLIT,
    MODULES_CONTRACT_VERSION,
    STATUS_ACTIVE,
    STATUS_CONFIGURED,
    STATUS_INACTIVE,
    STATUS_NOT_CONFIGURED,
    STATUS_NOT_REQUIRED,
    electrical_ownership_policy,
    get_local_face_module,
    module_code_for_treatment,
)

LOCAL_MODULE_SCHEMA = "acp_local_face_module_v1"
APPLIED_INTERFACE_SCHEMA = "acp_applied_component_interface_v1"
ELECTRICAL_SCHEMA = "acp_electrical_configuration_v1"


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _stable_module_id(binding_id: str, module_code: str) -> str:
    digest = hashlib.sha1(f"{module_code}|{binding_id}".encode("utf-8")).hexdigest()[:12]
    return f"mod_{module_code.lower().replace('acp-local-module-', '').replace('acp-', '')}_{digest}"


def _gated_field(status: str = GATE_OWNER_REQUIRED, **extra: Any) -> dict[str, Any]:
    out = {"confirmation_status": status, **extra}
    return out


def empty_routed_module(binding_id: str) -> dict[str, Any]:
    return {
        "schema": LOCAL_MODULE_SCHEMA,
        "module_code": MODULE_ROUTED_BACKLIT,
        "module_instance_id": _stable_module_id(binding_id, MODULE_ROUTED_BACKLIT),
        "status": STATUS_ACTIVE,
        "contract_version": MODULES_CONTRACT_VERSION,
        "backing_material": _gated_field(
            material_code=None,
            thickness_mm=None,
            optical_type=None,
        ),
        "backing_mounting": _gated_field(
            method_code=None,
            overlap_rule=GATE_MANUAL,
            manual_dimensions_status=GATE_OWNER_REQUIRED,
        ),
        "illumination_intent": {
            "enabled": True,
            "lighting_mode": "SHELL_CAVITY",
            "led_configuration_status": GATE_OWNER_REQUIRED,
            "power_configuration_status": GATE_OWNER_REQUIRED,
            "wiring_configuration_status": GATE_OWNER_REQUIRED,
        },
        "service": {"access_status": GATE_OWNER_REQUIRED},
        "provenance": {
            "source": "operator",
            "contract_version": MODULES_CONTRACT_VERSION,
            "resource_authority": "MISSING_OPTICAL_ELECTRICAL_RO",
        },
    }


def empty_insert_module(binding_id: str) -> dict[str, Any]:
    return {
        "schema": LOCAL_MODULE_SCHEMA,
        "module_code": MODULE_ACRYLIC_INSERT,
        "module_instance_id": _stable_module_id(binding_id, MODULE_ACRYLIC_INSERT),
        "status": STATUS_ACTIVE,
        "contract_version": MODULES_CONTRACT_VERSION,
        "insert": {
            "material_code": None,
            "thickness_mm": INSERT_THICKNESS_OWNER_VARIANT_MM,
            "thickness_provenance": INSERT_THICKNESS_PROVENANCE,
            "thickness_status": GATE_OWNER_REVIEW,
            "sole_thickness_admitted": False,
            "fit_mode": None,
            "clearance_status": GATE_OWNER_REQUIRED,
            "protrusion_status": GATE_OWNER_REQUIRED,
            "retention_method": None,
            "retention_status": GATE_OWNER_REQUIRED,
            "backing_configuration_status": GATE_OWNER_REQUIRED,
            "confirmation_status": GATE_OWNER_REQUIRED,
        },
        "illumination_intent": {
            "enabled": True,
            "lighting_mode": "SHELL_CAVITY_OR_INSERT",
            "led_configuration_status": GATE_OWNER_REQUIRED,
            "electrical_configuration_status": GATE_OWNER_REQUIRED,
        },
        "provenance": {
            "source": "operator",
            "contract_version": MODULES_CONTRACT_VERSION,
            "resource_authority": "MISSING_OPTICAL_ELECTRICAL_RO",
        },
    }


def empty_plain_module(binding_id: str) -> dict[str, Any]:
    return {
        "schema": LOCAL_MODULE_SCHEMA,
        "module_code": MODULE_PLAIN_DECORATIVE,
        "module_instance_id": _stable_module_id(binding_id, MODULE_PLAIN_DECORATIVE),
        "status": STATUS_ACTIVE,
        "contract_version": MODULES_CONTRACT_VERSION,
        "configuration_status": STATUS_NOT_REQUIRED,
        "provenance": {"source": "operator", "contract_version": MODULES_CONTRACT_VERSION},
    }


def empty_applied_interface(binding_id: str, applied_component_code: str) -> dict[str, Any]:
    return {
        "schema": APPLIED_INTERFACE_SCHEMA,
        "module_code": INTERFACE_APPLIED_VOLUMETRIC,
        "interface_instance_id": _stable_module_id(binding_id, INTERFACE_APPLIED_VOLUMETRIC),
        "status": STATUS_ACTIVE,
        "contract_version": MODULES_CONTRACT_VERSION,
        "host_component_template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
        "applied_component_template_code": applied_component_code,
        "placement_reference": "ON_ACP_FACE",
        "mounting_method_status": GATE_OWNER_REQUIRED,
        "cable_passage_status": GATE_OWNER_REQUIRED,
        "electrical_interface_status": GATE_OWNER_REQUIRED,
        "confirmation_status": STATUS_NOT_CONFIGURED,
        "provenance": {"source": "operator", "contract_version": MODULES_CONTRACT_VERSION},
    }


def normalize_local_module(
    raw: Any,
    *,
    binding_id: str,
    treatment_code: str | None,
    geometry_role: str | None,
    component_template_code: str | None,
    status: str | None,
) -> dict[str, Any] | None:
    """Attach/normalize module for a face-treatment binding. Inactive → stub only."""
    module_code = module_code_for_treatment(treatment_code)
    if not module_code:
        return None
    registry = get_local_face_module(module_code)
    if registry is None:
        return None

    binding_status = str(status or "").strip().upper()
    inactive = binding_status == STATUS_INACTIVE

    if module_code == MODULE_ROUTED_BACKLIT:
        base = empty_routed_module(binding_id)
    elif module_code == MODULE_ACRYLIC_INSERT:
        base = empty_insert_module(binding_id)
    elif module_code == MODULE_PLAIN_DECORATIVE:
        base = empty_plain_module(binding_id)
    elif module_code == INTERFACE_APPLIED_VOLUMETRIC:
        base = empty_applied_interface(binding_id, str(component_template_code or ""))
    else:
        return None

    incoming = _as_dict(raw)
    if incoming:
        # Preserve operator-provided nested keys without inventing material codes.
        for key in (
            "backing_material",
            "backing_mounting",
            "illumination_intent",
            "service",
            "insert",
            "status",
            "module_instance_id",
            "interface_instance_id",
            "placement_reference",
            "mounting_method_status",
            "cable_passage_status",
            "electrical_interface_status",
            "confirmation_status",
            "host_component_template_code",
            "applied_component_template_code",
        ):
            if key in incoming and incoming[key] is not None:
                if isinstance(incoming[key], Mapping) and isinstance(base.get(key), dict):
                    merged = dict(base[key])
                    merged.update(dict(incoming[key]))
                    base[key] = merged
                else:
                    base[key] = incoming[key]

    if inactive:
        base["status"] = STATUS_INACTIVE
    elif str(base.get("status") or "").upper() != STATUS_INACTIVE:
        base["status"] = STATUS_ACTIVE

    # Preserve stable ids
    if not base.get("module_instance_id") and module_code != INTERFACE_APPLIED_VOLUMETRIC:
        base["module_instance_id"] = _stable_module_id(binding_id, module_code)
    if module_code == INTERFACE_APPLIED_VOLUMETRIC and not base.get("interface_instance_id"):
        base["interface_instance_id"] = _stable_module_id(binding_id, module_code)

    base["face_treatment_code"] = treatment_code
    base["geometry_role"] = geometry_role
    base["binding_id"] = binding_id
    base["readiness"] = evaluate_module_readiness(base)
    return base


def evaluate_module_readiness(module: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(module, Mapping):
        return {"overall": READINESS_NOT_APPLICABLE, "warnings": [], "blockers": [], "gates": []}
    if str(module.get("status") or "").upper() == STATUS_INACTIVE:
        return {
            "overall": READINESS_INACTIVE,
            "warnings": [],
            "blockers": [],
            "gates": [],
            "actionable": False,
        }

    code = str(module.get("module_code") or "")
    gates: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    def note(path: str, status: str) -> None:
        if status in {GATE_OWNER_REQUIRED, GATE_MANUAL, GATE_OWNER_REVIEW, STATUS_NOT_CONFIGURED}:
            gates.append({"path": path, "status": status})

    if code == MODULE_ROUTED_BACKLIT:
        bm = _as_dict(module.get("backing_material"))
        mm = _as_dict(module.get("backing_mounting"))
        ill = _as_dict(module.get("illumination_intent"))
        note("backing_material", str(bm.get("confirmation_status") or GATE_OWNER_REQUIRED))
        note("backing_mounting", str(mm.get("confirmation_status") or GATE_OWNER_REQUIRED))
        note("illumination.led", str(ill.get("led_configuration_status") or GATE_OWNER_REQUIRED))
        note("illumination.power", str(ill.get("power_configuration_status") or GATE_OWNER_REQUIRED))
        overall = READINESS_LOCAL_CONFIGURATION_REQUIRED if gates else READINESS_READY_FOR_AGGREGATION
        if gates:
            warnings.append(
                {
                    "code": "ACP_ROUTED_MODULE_OWNER_GATES",
                    "message": "Routed backlit module active; optical/electrical values owner-gated.",
                }
            )
        return {
            "overall": overall,
            "material": GATE_OWNER_REQUIRED,
            "geometry": STATUS_CONFIGURED,
            "mounting": GATE_OWNER_REQUIRED,
            "illumination": GATE_OWNER_REQUIRED,
            "electrical": GATE_OWNER_REQUIRED,
            "warnings": warnings,
            "blockers": [],
            "gates": gates,
            "actionable": bool(gates),
        }

    if code == MODULE_ACRYLIC_INSERT:
        ins = _as_dict(module.get("insert"))
        ill = _as_dict(module.get("illumination_intent"))
        note("insert.thickness", str(ins.get("thickness_status") or GATE_OWNER_REVIEW))
        note("insert.clearance", str(ins.get("clearance_status") or GATE_OWNER_REQUIRED))
        note("insert.protrusion", str(ins.get("protrusion_status") or GATE_OWNER_REQUIRED))
        note("insert.retention", str(ins.get("retention_status") or GATE_OWNER_REQUIRED))
        note("illumination", str(ill.get("led_configuration_status") or GATE_OWNER_REQUIRED))
        warnings.append(
            {
                "code": "ACP_INSERT_MODULE_OWNER_GATES",
                "message": (
                    f"Insert thickness {ins.get('thickness_mm')} mm is "
                    f"{INSERT_THICKNESS_PROVENANCE} — not sole admitted thickness."
                ),
            }
        )
        return {
            "overall": READINESS_LOCAL_CONFIGURATION_REQUIRED,
            "geometry": STATUS_CONFIGURED,
            "insert_material": GATE_OWNER_REQUIRED,
            "fit": GATE_OWNER_REQUIRED,
            "retention": GATE_OWNER_REQUIRED,
            "illumination": GATE_OWNER_REQUIRED,
            "electrical": GATE_OWNER_REQUIRED,
            "warnings": warnings,
            "blockers": [],
            "gates": gates,
            "actionable": True,
        }

    if code == MODULE_PLAIN_DECORATIVE:
        return {
            "overall": READINESS_READY_FOR_AGGREGATION,
            "warnings": [],
            "blockers": [],
            "gates": [],
            "actionable": False,
        }

    if code == INTERFACE_APPLIED_VOLUMETRIC:
        for path in (
            "mounting_method_status",
            "cable_passage_status",
            "electrical_interface_status",
        ):
            note(path, str(module.get(path) or GATE_OWNER_REQUIRED))
        return {
            "overall": READINESS_LOCAL_CONFIGURATION_REQUIRED if gates else READINESS_READY_FOR_AGGREGATION,
            "warnings": [
                {
                    "code": "ACP_APPLIED_INTERFACE_OWNER_GATES",
                    "message": "Applied component remains separate; host interface gated.",
                }
            ]
            if gates
            else [],
            "blockers": [],
            "gates": gates,
            "actionable": bool(gates),
        }

    return {"overall": READINESS_NOT_APPLICABLE, "warnings": [], "blockers": [], "gates": []}


def normalize_acp_electrical_configuration(
    raw: Any,
    *,
    bindings: list[Mapping[str, Any]] | None = None,
    service_corner: str | None = None,
) -> dict[str, Any]:
    base = {
        "schema": ELECTRICAL_SCHEMA,
        "ownership_mode": ELECTRICAL_OWNERSHIP_MODE,
        "contract_version": MODULES_CONTRACT_VERSION,
        "service_corner": service_corner,
        "zone_intents": [],
        "led_configuration_status": GATE_OWNER_REQUIRED,
        "psu_configuration_status": GATE_OWNER_REQUIRED,
        "wiring_configuration_status": GATE_OWNER_REQUIRED,
        "electrical_test_status": GATE_OWNER_REQUIRED,
        "policy": electrical_ownership_policy(),
    }
    incoming = _as_dict(raw)
    if incoming:
        for key in (
            "service_corner",
            "led_configuration_status",
            "psu_configuration_status",
            "wiring_configuration_status",
            "electrical_test_status",
            "zone_intents",
        ):
            if key in incoming and incoming[key] is not None:
                base[key] = incoming[key]
    intents: list[dict[str, Any]] = []
    for b in bindings or []:
        mod = _as_dict(b.get("local_module_configuration"))
        if str(mod.get("status") or "").upper() == STATUS_INACTIVE:
            continue
        ill = _as_dict(mod.get("illumination_intent"))
        if ill.get("enabled") is True:
            intents.append(
                {
                    "binding_id": b.get("binding_id"),
                    "local_zone_id": b.get("local_zone_id"),
                    "module_code": mod.get("module_code"),
                    "requires_illumination": True,
                    "lighting_mode": ill.get("lighting_mode"),
                }
            )
    if intents:
        base["zone_intents"] = intents
    if not base.get("service_corner") and service_corner:
        base["service_corner"] = service_corner
    return base


def build_local_module_aggregate_projection(
    modules: list[Mapping[str, Any]] | None,
    *,
    electrical: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Guarded Aggregate projection — identity + readiness + process intents, no quantities."""
    active: list[dict[str, Any]] = []
    for mod in modules or []:
        if not isinstance(mod, Mapping):
            continue
        if str(mod.get("status") or "").upper() == STATUS_INACTIVE:
            continue
        registry = get_local_face_module(str(mod.get("module_code") or ""))
        readiness = evaluate_module_readiness(mod)
        active.append(
            {
                "module_instance_id": mod.get("module_instance_id") or mod.get("interface_instance_id"),
                "module_code": mod.get("module_code"),
                "binding_id": mod.get("binding_id"),
                "geometry_role": mod.get("geometry_role"),
                "face_treatment_code": mod.get("face_treatment_code"),
                "readiness": readiness.get("overall"),
                "gates": readiness.get("gates") or [],
                "process_intent": list((registry or {}).get("process_intents_guarded") or []),
                "quantity_status": "GUARDED",
                "notes": [
                    "No invented plexiglas/LED/PSU quantities.",
                    "Optical/electrical resource options missing — owner gates retained.",
                ],
            }
        )
    if not active and not electrical:
        return None
    return {
        "kind": "acp_local_face_modules",
        "contract_version": MODULES_CONTRACT_VERSION,
        "modules": active,
        "electrical": dict(electrical) if isinstance(electrical, Mapping) else None,
        "electrical_ownership": ELECTRICAL_OWNERSHIP_MODE,
        "quantity_status": "GUARDED",
        "blockers": [],
    }
