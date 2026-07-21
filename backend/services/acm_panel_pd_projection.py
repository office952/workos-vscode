"""Project AcmPanel finish_setup fields into ProductDefinition canonical_values.

Read-only projection — does not invent confirmed state or a second instance owner.
"""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping

from services.acm_assembly_extent import inject_assembly_extent_keys
from services.acm_face_treatment_commercial_path_v1 import (
    BAG_KEY as FACE_TREATMENT_BAG_KEY,
    project_for_aggregate as project_face_treatments_for_aggregate,
    project_for_product_definition as project_face_treatments_for_pd,
    read_face_treatments,
)


def coalesce_acm_panel_instance_from_finish(finish: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Same coalesce order as Letters PD / FE resolveAcmPanelInstance."""
    finish_d = finish if isinstance(finish, Mapping) else {}
    acm_instance = finish_d.get("acm_panel_instance")
    if not isinstance(acm_instance, dict):
        sel_probe = finish_d.get("svg_support_selection")
        if isinstance(sel_probe, dict) and isinstance(sel_probe.get("acm_panel_instance"), dict):
            acm_instance = sel_probe.get("acm_panel_instance")
        else:
            ms = finish_d.get("mounting_solution")
            cfg = ms.get("configuration") if isinstance(ms, dict) else None
            if isinstance(cfg, dict) and isinstance(cfg.get("acm_panel_instance"), dict):
                acm_instance = cfg.get("acm_panel_instance")
    if isinstance(acm_instance, dict) and acm_instance.get("schema") == "acm_panel_component_instance_v1":
        if str(acm_instance.get("component_instance_id") or "").strip():
            return acm_instance
    return None


def workspace_has_real_acm_panel(payload: Mapping[str, Any] | None) -> bool:
    if not isinstance(payload, Mapping):
        return False
    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), Mapping) else {}
    return coalesce_acm_panel_instance_from_finish(finish) is not None


def project_segmented_into_values(
    values: MutableMapping[str, Any],
    finish: Mapping[str, Any],
) -> None:
    from services.acm_segmented_background_service import (
        project_segmented_background_for_aggregate,
        project_segmented_background_for_product_definition,
        read_segmented_background_from_finish,
    )

    segmented = read_segmented_background_from_finish(finish)
    if segmented is None:
        return
    pd_segmented = project_segmented_background_for_product_definition(segmented)
    if pd_segmented is not None:
        values["segmented_background"] = pd_segmented
        agg_segmented = project_segmented_background_for_aggregate(segmented)
        if agg_segmented is not None:
            values["segmented_background_aggregate_projection"] = agg_segmented
    status_seg = str(segmented.get("status") or "").upper()
    if status_seg in {"PROPOSED", "INACTIVE", "REJECTED"}:
        values["segmented_background_proposal"] = {
            "schema": segmented.get("schema"),
            "status": status_seg,
            "assembly_id": segmented.get("assembly_id"),
            "detection": segmented.get("detection"),
            "operator_confirmed": False,
            "downstream_effects": False,
            "host_component_template_code": segmented.get("host_component_template_code"),
            "panels": segmented.get("panels") or [],
            "joints": segmented.get("joints") or [],
            "assembly_dimensions": segmented.get("assembly_dimensions"),
            "element_bindings": segmented.get("element_bindings") or [],
            "meta": segmented.get("meta") if isinstance(segmented.get("meta"), dict) else {},
            "materials": [],
            "processes": [],
            "task_rules": [],
            "future_task_intent_authority": "INFORMATIONAL_ONLY",
        }


def project_acm_instance_into_values(
    values: MutableMapping[str, Any],
    acm_instance: Mapping[str, Any],
) -> None:
    values["acm_panel_instance"] = acm_instance
    values["acm_panel_association_status"] = acm_instance.get("association_status")
    values["acm_panel_technical_configuration_status"] = acm_instance.get(
        "technical_configuration_status"
    )
    values["acm_panel_composition_status"] = acm_instance.get("composition_status")
    values["acm_panel_capabilities"] = acm_instance.get("capabilities")
    values["support_type"] = "alucobond_cased"
    values["acp_panel_active"] = str(acm_instance.get("association_status") or "") in {
        "proposed",
        "confirmed",
    }
    values["acp_panel_technical_confirmed"] = (
        str(acm_instance.get("technical_configuration_status") or "") == "confirmed"
    )


def project_svg_support_selection_into_values(
    values: MutableMapping[str, Any],
    finish: Mapping[str, Any],
) -> None:
    selection = finish.get("svg_support_selection")
    if not isinstance(selection, dict) or selection.get("schema") != "svg_support_selection_v1":
        return
    status = str(selection.get("status") or "").strip()
    role = str(selection.get("role") or "").strip()
    if role != "ALUCOBOND_CASED_PANEL" or status not in {"proposed", "confirmed"}:
        return
    values["svg_support_selection"] = selection
    if selection.get("svg_support_element_id"):
        values["svg_support_element_id"] = selection.get("svg_support_element_id")
    geom = selection.get("panel_geometry")
    if isinstance(geom, dict):
        values["panel_geometry"] = geom
    casing = selection.get("casing_profile")
    if isinstance(casing, dict):
        values["casing_profile"] = casing
        auth = selection.get("field_authority") if isinstance(selection.get("field_authority"), dict) else {}
        values["casing_profile_field_authority"] = auth
    if selection.get("service_corner"):
        values["service_corner"] = selection.get("service_corner")
    values["internal_frame_enabled"] = bool(selection.get("internal_frame_enabled"))
    values["support_type"] = "alucobond_cased"
    values["acp_panel_active"] = True
    values["acp_panel_selection_status"] = status
    tech = str(values.get("acm_panel_technical_configuration_status") or "")
    if status == "confirmed" and tech == "confirmed":
        values["acp_panel_technical_confirmed"] = True


def project_face_treatments_into_values(
    values: MutableMapping[str, Any],
    finish: Mapping[str, Any] | None,
    payload: Mapping[str, Any] | None = None,
) -> None:
    """Axis B — project acm_face_treatments_v1 into PD canonical values (no panel sheet)."""
    source = payload if isinstance(payload, Mapping) else finish
    if isinstance(finish, Mapping) and finish.get(FACE_TREATMENT_BAG_KEY) is not None:
        source = {"finish_setup": finish}
    domain = read_face_treatments(source if isinstance(source, Mapping) else None)
    projection = project_face_treatments_for_pd(domain)
    values[FACE_TREATMENT_BAG_KEY] = projection["acm_face_treatments"]
    values["acm_face_treatment_quantity_matrix"] = projection["acm_face_treatment_quantity_matrix"]
    values["acm_face_treatment_ops_intents"] = projection["acm_face_treatment_ops_intents"]
    values["acm_face_treatment_cpp_eic_gate"] = projection["acm_face_treatment_cpp_eic_gate"]
    values["face_treatment_coexistence"] = domain.get("coexistence")
    agg = project_face_treatments_for_aggregate(domain)
    if agg is not None:
        values["acm_face_treatments_aggregate_projection"] = agg
    modules = projection.get("acp_local_face_module_instances_from_face_treatments") or []
    if modules:
        existing = list(values.get("acp_local_face_module_instances") or [])
        # Avoid duplicate module_instance_id when SVG bindings already projected modules.
        seen = {
            str(m.get("module_instance_id") or m.get("interface_instance_id") or "")
            for m in existing
            if isinstance(m, Mapping)
        }
        for mod in modules:
            mid = str(mod.get("module_instance_id") or mod.get("interface_instance_id") or "")
            if mid and mid in seen:
                continue
            existing.append(mod)
            if mid:
                seen.add(mid)
        values["acp_local_face_module_instances"] = existing


def project_acm_finish_into_canonical(
    values: MutableMapping[str, Any],
    finish: Mapping[str, Any] | None,
) -> list[str]:
    """Project AcmPanel + segmented + assembly_* into values. Returns assembly warnings."""
    finish_d = finish if isinstance(finish, Mapping) else {}
    project_segmented_into_values(values, finish_d)
    inst = coalesce_acm_panel_instance_from_finish(finish_d)
    if inst is not None:
        project_acm_instance_into_values(values, inst)
    project_svg_support_selection_into_values(values, finish_d)
    project_face_treatments_into_values(values, finish_d)
    return inject_assembly_extent_keys(values, finish=finish_d, acm_instance=inst)

