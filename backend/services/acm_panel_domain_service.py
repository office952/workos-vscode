"""ACM panel domain write semantics: preserve | upsert | clear.

finish_setup is Intake transport. acm_panel_instance is the reusable component instance.
SUPPORT_CONTOUR is an adapter role for the letters-on-support consumer — not universal ACM identity.
"""

from __future__ import annotations

from typing import Any, Mapping


DOMAIN_ACTIONS = frozenset({"preserve", "upsert", "clear"})
ACM_TEMPLATE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _binding_role(raw: Any) -> str:
    if isinstance(raw, Mapping):
        return str(raw.get("geometry_role") or "").strip().upper()
    return ""


def _has_support_role_confirmed(payload_or_finish_context: Mapping[str, Any] | None) -> bool:
    """Layer roles live on workspace payload, not finish — caller may pass layer_role_setup."""
    setup = _as_dict(payload_or_finish_context)
    layers = _as_list(setup.get("layers"))
    for layer in layers:
        if not isinstance(layer, Mapping):
            continue
        role = str(layer.get("confirmed_role") or "").strip().lower()
        state = str(layer.get("confirmation_state") or "").strip().lower()
        if role == "support_panel" and state == "confirmed":
            return True
    return False


def _merge_production_geometry_preserve(
    finish_d: dict[str, Any],
    existing: Mapping[str, Any],
) -> dict[str, Any]:
    """Keep component-owned production_geometry when incoming instance omits the bundle."""
    incoming_inst = finish_d.get("acm_panel_instance")
    existing_inst = existing.get("acm_panel_instance")
    if isinstance(incoming_inst, dict) and isinstance(existing_inst, Mapping):
        if "production_geometry" not in incoming_inst and existing_inst.get("production_geometry"):
            merged = dict(incoming_inst)
            merged["production_geometry"] = existing_inst.get("production_geometry")
            finish_d["acm_panel_instance"] = merged
    # Nested mirrors
    for nest_key in ("svg_support_selection",):
        inc_sel = finish_d.get(nest_key)
        ex_sel = existing.get(nest_key)
        if isinstance(inc_sel, dict) and isinstance(ex_sel, Mapping):
            inc_i = inc_sel.get("acm_panel_instance")
            ex_i = ex_sel.get("acm_panel_instance")
            if isinstance(inc_i, dict) and isinstance(ex_i, Mapping):
                if "production_geometry" not in inc_i and ex_i.get("production_geometry"):
                    mi = dict(inc_i)
                    mi["production_geometry"] = ex_i.get("production_geometry")
                    sel = dict(inc_sel)
                    sel["acm_panel_instance"] = mi
                    finish_d[nest_key] = sel
    return finish_d


def coalesce_acm_panel_domain_for_finish(
    incoming_finish: Mapping[str, Any] | None,
    existing_finish: Mapping[str, Any] | None,
    *,
    layer_role_setup: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply acm_panel_domain_action semantics.

    - upsert: accept incoming ACM shell fields
    - clear: wipe ACM shell (even if existing)
    - preserve / omit: keep existing SUPPORT/selection/mounting/instance when
      incoming bindings-only would drop them and support role still confirmed
    """
    finish_d = dict(incoming_finish or {})
    existing = _as_dict(existing_finish)
    action = str(finish_d.get("acm_panel_domain_action") or "").strip().lower()
    if action not in DOMAIN_ACTIONS:
        # Infer: full ACM upsert if selection/instance present; else preserve if shell exists.
        if finish_d.get("acm_panel_instance") is not None or (
            isinstance(finish_d.get("svg_support_selection"), Mapping)
            and str(_as_dict(finish_d.get("svg_support_selection")).get("status") or "").lower()
            in {"proposed", "confirmed"}
        ):
            action = "upsert"
        else:
            action = "preserve"
        finish_d["acm_panel_domain_action"] = action

    if action == "clear":
        finish_d["acm_panel_instance"] = None
        finish_d["svg_support_selection"] = {
            "schema": "svg_support_selection_v1",
            "status": "none",
            "role": None,
        }
        finish_d["mounting_solution"] = None
        bindings = [
            b
            for b in _as_list(finish_d.get("svg_component_bindings"))
            if isinstance(b, Mapping)
            and _binding_role(b) != "SUPPORT_CONTOUR"
            and str(b.get("component_template_code") or "") != ACM_TEMPLATE
        ]
        finish_d["svg_component_bindings"] = bindings
        return finish_d

    if action == "upsert":
        # Preserve top-level instance when FE upsert omits it (Review autosave without hydrate).
        if finish_d.get("acm_panel_instance") in (None, {}) and existing.get("acm_panel_instance"):
            finish_d["acm_panel_instance"] = existing.get("acm_panel_instance")
        # Preserve production_geometry binding when FE upsert omits it (inspector patches).
        finish_d = _merge_production_geometry_preserve(finish_d, existing)
        return finish_d

    # preserve
    support_still_wanted = _has_support_role_confirmed(layer_role_setup)
    existing_bindings = _as_list(existing.get("svg_component_bindings"))
    existing_support = [
        b
        for b in existing_bindings
        if isinstance(b, Mapping)
        and (
            _binding_role(b) == "SUPPORT_CONTOUR"
            or str(b.get("component_template_code") or "") == ACM_TEMPLATE
        )
    ]
    incoming_bindings = _as_list(finish_d.get("svg_component_bindings"))
    incoming_has_support = any(
        isinstance(b, Mapping) and _binding_role(b) == "SUPPORT_CONTOUR" for b in incoming_bindings
    )

    if support_still_wanted and existing_support and not incoming_has_support:
        # Merge SUPPORT back — do not blind-preserve when clear was intended (handled above).
        non_support = [
            b
            for b in incoming_bindings
            if isinstance(b, Mapping) and _binding_role(b) != "SUPPORT_CONTOUR"
        ]
        finish_d["svg_component_bindings"] = non_support + existing_support

    if support_still_wanted:
        if finish_d.get("svg_support_selection") in (None, {}) and existing.get("svg_support_selection"):
            finish_d["svg_support_selection"] = existing.get("svg_support_selection")
        if finish_d.get("mounting_solution") in (None, {}) and existing.get("mounting_solution"):
            finish_d["mounting_solution"] = existing.get("mounting_solution")
        if finish_d.get("acm_panel_instance") in (None, {}) and existing.get("acm_panel_instance"):
            finish_d["acm_panel_instance"] = existing.get("acm_panel_instance")

    # Autosave / analysis-bundle races omit acm_panel_instance even when support role
    # was rewritten — keep existing component instance unless action was clear.
    if finish_d.get("acm_panel_instance") in (None, {}) and existing.get("acm_panel_instance"):
        finish_d["acm_panel_instance"] = existing.get("acm_panel_instance")

    return finish_d
