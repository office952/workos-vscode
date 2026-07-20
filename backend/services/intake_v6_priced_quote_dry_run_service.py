"""Backend-only Intake V6 priced quote dry-run.

No quote creation, no quote update, no snapshot, no order, no V4 draft payload.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.company_commercial_settings_service import get_default_vat_pct, get_eur_to_ron_rate
from services.estimated_internal_cost_service import EstimatedInternalCostService
from services.intake_v6_material_breakdown_service import get_material_breakdown_for_workspace
from services.intake_v6_offer_scope_live_calc_service import (
	merge_workspace_offer_scope_into_quote_input,
)
from services.intake_v6_pricing_input_service import build_v6_pricing_input_preview
from services.intake_v6_workspace_service import _get_record_or_404, _json_loads, _parse_payload

V6_PRICED_DRY_RUN_SOURCE = "intake_v6_backend_priced_dry_run"
V6_PRICED_DRY_RUN_READY = "V6_PRICED_DRY_RUN_READY"
V6_PRICED_DRY_RUN_BLOCKED = "V6_PRICED_DRY_RUN_BLOCKED"
V6_PRICED_DRY_RUN_SOURCE_MISSING = "V6_PRICED_DRY_RUN_SOURCE_MISSING"
V6_PRICED_DRY_RUN_ZERO_TOTAL = "V6_PRICED_DRY_RUN_ZERO_TOTAL"
V6_OFFICIAL_COMMERCIAL_AUTHORITY = "commercial_price_proposal_7g"
TD_W3_V6_DIAG_COST_PLUS = "TD-W3-V6-DIAG-COST-PLUS-001"

# Optional/future commercial owner decisions — surfaced as warnings, not dry-run blockers.
# Montaj is removed from this set at runtime when site installation is commercially required.
V6_OPTIONAL_COMMERCIAL_OWNER_DECISION_CODES = frozenset(
	{
		"AMBALARE_COMMERCIAL_RULE",
		"MONTAJ_COMMERCIAL_RULE",
	}
)


def _round_money(value: float) -> float:
	return round(float(value), 2)


def _positive_number(raw: Any) -> float | None:
	try:
		value = float(raw)
	except (TypeError, ValueError):
		return None
	if value <= 0:
		return None
	return value


def _blocker(code: str, message: str) -> dict[str, str]:
	return {"code": code, "message": message}


def _empty_totals(*, vat_rate: float | None = None) -> dict[str, Any]:
	return {
		"subtotal_net": None,
		"vat_rate": vat_rate,
		"vat_amount": None,
		"total_gross": None,
		"currency": "RON",
	}


def _read_number(raw: Any) -> float | None:
	try:
		value = float(raw)
	except (TypeError, ValueError):
		return None
	if not value == value:
		return None
	return value


def _read_commercial_inputs(
	payload_raw: dict[str, Any],
	quote_input: dict[str, Any],
	*,
	settings_vat_percent: float,
) -> dict[str, float]:
	finish_setup = payload_raw.get("finish_setup") if isinstance(payload_raw.get("finish_setup"), dict) else {}
	commercial_inputs = (
		finish_setup.get("commercial_inputs")
		if isinstance(finish_setup.get("commercial_inputs"), dict)
		else {}
	)

	def pick(key: str, fallback: float) -> float:
		for source in (commercial_inputs, quote_input):
			value = _read_number(source.get(key)) if isinstance(source, dict) else None
			if value is not None:
				return value
		return fallback

	return {
		"markup_percent": pick("markup_percent", 35.0),
		"discount_percent": pick("discount_percent", 0.0),
		"vat_percent": float(settings_vat_percent),
		"manual_adjustment_ron": pick("manual_adjustment_ron", 0.0),
	}


def _build_cost_plus_totals(
	*,
	internal_cost_total: float,
	eur_to_ron_rate: float,
	commercial_inputs: dict[str, float],
) -> dict[str, Any]:
	production_base = _round_money(internal_cost_total * eur_to_ron_rate)
	markup_percent = commercial_inputs["markup_percent"]
	discount_percent = commercial_inputs["discount_percent"]
	vat_percent = commercial_inputs["vat_percent"]
	manual_adjustment_ron = commercial_inputs["manual_adjustment_ron"]
	markup_value = _round_money(production_base * markup_percent / 100)
	subtotal_before_discount = _round_money(production_base + markup_value + manual_adjustment_ron)
	discount_value = _round_money(subtotal_before_discount * discount_percent / 100)
	subtotal_net = _round_money(subtotal_before_discount - discount_value)
	vat_amount = _round_money(subtotal_net * vat_percent / 100)
	total_gross = _round_money(subtotal_net + vat_amount)
	return {
		"subtotal_net": subtotal_net,
		"vat_rate": vat_percent,
		"vat_amount": vat_amount,
		"total_gross": total_gross,
		"currency": "RON",
		"cost_plus_trace": {
			"internal_cost_total": _round_money(internal_cost_total),
			"internal_cost_currency": "EUR",
			"eur_to_ron_rate": eur_to_ron_rate,
			"production_base_ron": production_base,
			"markup_percent": markup_percent,
			"markup_value": markup_value,
			"manual_adjustment_ron": _round_money(manual_adjustment_ron),
			"discount_percent": discount_percent,
			"discount_value": discount_value,
		},
	}


def _material_trace(material_breakdown: Any | None, material_warning: str | None) -> dict[str, Any]:
	if material_breakdown is None:
		return {"available": False, "warning": material_warning}
	totals = getattr(material_breakdown, "totals", None)
	return {
		"available": True,
		"workspace_id": getattr(material_breakdown, "workspace_id", None),
		"template_code": getattr(material_breakdown, "template_code", None),
		"estimated_cost_total": getattr(totals, "estimated_cost_total", None),
		"material_cost_total": getattr(totals, "material_cost_total", None),
		"currency": getattr(totals, "currency", None),
		"contains_estimates": getattr(totals, "contains_estimates", None),
		"contains_missing_prices": getattr(totals, "contains_missing_prices", None),
	}


def _estimated_internal_cost_trace(preview: Any | None) -> dict[str, Any]:
	if preview is None:
		return {"available": False}
	return {
		"available": True,
		"source": getattr(preview, "source", None),
		"status": getattr(preview, "status", None),
		"estimated_total_internal_cost": getattr(preview, "estimated_total_internal_cost", None),
		"estimated_material_cost": getattr(preview, "estimated_material_cost", None),
		"estimated_operation_cost": getattr(preview, "estimated_operation_cost", None),
		"currency": getattr(preview, "currency", None),
		"blockers": [
			{"code": b.code, "message": b.message, "module_code": b.module_code}
			for b in getattr(preview, "internal_blockers", []) or []
		],
		"provenance": [
			entry.model_dump(mode="json")
			for entry in (getattr(preview, "provenance", []) or [])
		],
	}


def _official_totals_from_7g(*, subtotal: float, vat_rate: float) -> dict[str, Any]:
	vat_amount = _round_money(subtotal * vat_rate / 100)
	return {
		"subtotal_net": _round_money(subtotal),
		"vat_rate": vat_rate,
		"vat_amount": vat_amount,
		"total_gross": _round_money(subtotal + vat_amount),
		"currency": "RON",
	}


def _pricing_trace(pricing_preview: Any) -> dict[str, Any]:
	quote_input = getattr(pricing_preview, "quote_input_payload", {}) or {}
	return {
		"workspace_id": getattr(pricing_preview, "workspace_id", None),
		"template_code": getattr(pricing_preview, "template_code", None),
		"is_ready_for_quote": getattr(pricing_preview, "is_ready_for_quote", False),
		"adapter_status": getattr(pricing_preview, "adapter_status", None),
		"adapter_blockers": list(getattr(pricing_preview, "adapter_blockers", []) or []),
		"adapter_warnings": list(getattr(pricing_preview, "adapter_warnings", []) or []),
		"production_counts": dict(getattr(pricing_preview, "production_counts", {}) or {}),
		"finish_summary": dict(getattr(pricing_preview, "finish_summary", {}) or {}),
		"quote_input_keys": sorted(str(key) for key in quote_input.keys()),
	}


def _commercial_line_items(commercial_preview: Any) -> list[dict[str, Any]]:
	items: list[dict[str, Any]] = []
	for line in getattr(commercial_preview, "commercial_price_lines", []) or []:
		items.append(
			{
				"code": line.code,
				"label": line.label,
				"module_code": line.module_code,
				"component_code": line.component_code,
				"basis_type": line.basis_type,
				"quantity": line.quantity,
				"unit": line.unit,
				"commercial_unit_price": line.commercial_unit_price,
				"subtotal": line.subtotal,
				"pricing_rule_code": line.pricing_rule_code,
				"source": line.source,
				"owner_decision_required": line.owner_decision_required,
				"warnings": list(line.warnings or []),
				"segment_key": getattr(line, "segment_key", None),
				"layer_identity": getattr(line, "layer_identity", None),
				"linked_template_code": getattr(line, "linked_template_code", None),
				"registry_pricing_code": getattr(line, "registry_pricing_code", None),
				"source_currency": getattr(line, "source_currency", None),
				"cpp_currency": getattr(line, "cpp_currency", None),
				"currency_conversion_rate": getattr(line, "currency_conversion_rate", None),
				"currency_conversion_source": getattr(line, "currency_conversion_source", None),
			}
		)
	return items


def _build_acm_panel_commercial_preview(
	*,
	quote_input: dict[str, Any],
	payload_raw: dict[str, Any],
	line_items: list[dict[str, Any]],
) -> dict[str, Any] | None:
	"""Provisional AcmPanel pricing projection over CPP lines (no second pricing system)."""
	from services.acm_commercial_geometry import (
		ACM_COMMERCIAL_GEOMETRY_VERSION,
		apply_acm_commercial_geometry,
		build_acm_panel_authority_summary,
	)
	from services.acm_panel_pd_projection import coalesce_acm_panel_instance_from_finish
	from services.acm_quote_input_helpers import merge_acm_boxed_mounting_derived_fields

	merged_payload: dict[str, Any] = dict(payload_raw or {})
	if quote_input:
		# Prefer workspace finish_setup; overlay quote_input for derived keys.
		qi = dict(quote_input)
		if isinstance(merged_payload.get("finish_setup"), dict) and "finish_setup" not in qi:
			qi["finish_setup"] = merged_payload["finish_setup"]
		merged = merge_acm_boxed_mounting_derived_fields(qi)
	else:
		merged = merge_acm_boxed_mounting_derived_fields(merged_payload)

	finish = merged.get("finish_setup") if isinstance(merged.get("finish_setup"), dict) else {}
	if coalesce_acm_panel_instance_from_finish(finish) is None and coalesce_acm_panel_instance_from_finish(
		merged_payload.get("finish_setup") if isinstance(merged_payload.get("finish_setup"), dict) else {}
	) is None:
		return None

	apply_acm_commercial_geometry(merged)
	# Authority must read workspace finish (segmented / instance), not only quote_input merge.
	authority_finish = (
		merged_payload.get("finish_setup")
		if isinstance(merged_payload.get("finish_setup"), dict)
		else finish
	)
	authority = build_acm_panel_authority_summary(
		{
			**merged_payload,
			"finish_setup": authority_finish or {},
			"acm_commercial_geometry": merged.get("acm_commercial_geometry"),
		}
	)
	geom = merged.get("acm_commercial_geometry") if isinstance(merged.get("acm_commercial_geometry"), dict) else {}

	acm_lines = [line for line in line_items if str(line.get("code") or "").startswith("acm_")]
	hourly = [
		line
		for line in acm_lines
		if str(line.get("basis_type") or "").lower() in {"hour", "hourly", "per_hour"}
		or str(line.get("unit") or "").lower() in {"h", "hour", "ore", "eur/h", "eur/hour"}
	]
	warnings = list(authority.get("warnings") or [])
	warnings.extend(list(merged.get("acm_commercial_geometry_warnings") or []))
	if hourly:
		warnings.append("hourly_commercial_line_detected")
	blockers = list(authority.get("blockers") or [])

	estimated_total = 0.0
	preview_lines: list[dict[str, Any]] = []
	for line in acm_lines:
		amount = line.get("subtotal")
		try:
			amount_f = float(amount) if amount is not None else None
		except (TypeError, ValueError):
			amount_f = None
		if amount_f is not None:
			estimated_total += amount_f
		preview_lines.append(
			{
				"code": line.get("code"),
				"label": line.get("label"),
				"quantity": line.get("quantity"),
				"unit": line.get("unit"),
				"rate": line.get("commercial_unit_price"),
				"amount": amount_f,
				"source": line.get("source"),
				"status": "provisional",
				"warnings": list(line.get("warnings") or []),
				"basis_type": line.get("basis_type"),
			}
		)

	currency = "EUR"
	if acm_lines and acm_lines[0].get("source_currency"):
		currency = str(acm_lines[0].get("source_currency"))
	elif acm_lines and acm_lines[0].get("cpp_currency"):
		currency = str(acm_lines[0].get("cpp_currency"))

	prod = (
		merged.get("acm_panel_production_geometry_metrics")
		if isinstance(merged.get("acm_panel_production_geometry_metrics"), dict)
		else {}
	)
	path_status = str(
		geom.get("path_measurement_status")
		or prod.get("measurement_status")
		or merged.get("acm_path_quantity_status")
		or ""
	)
	if path_status in {
		"unavailable",
		"stale",
		"invalid",
		"semantic_mapping_required",
		"measured_with_warnings",
	}:
		if path_status == "unavailable":
			warnings.append("quantity_unavailable")
		elif path_status == "stale":
			warnings.append("production_geometry_stale")
		elif path_status == "semantic_mapping_required":
			warnings.append("semantic_mapping_required")
		elif path_status == "measured_with_warnings":
			warnings.append("measured_with_warnings")
		# Path incomplete / provisional — keep final/offer/exec blocked.
		if "final_price_unavailable" not in blockers:
			blockers.append("final_price_unavailable")
		if "offer_ferm_unavailable" not in blockers:
			blockers.append("offer_ferm_unavailable")
		authority = {
			**authority,
			"final_eligibility": False,
			"offer_eligibility": False,
			"execution_eligibility": False,
		}
	if path_status == "proxy_rectangular":
		warnings.append("cut_v_quantity_source=proxy_rectangular")
	if path_status in {
		"commercial_deduced",
		"commercial_deduced_with_assumptions",
	}:
		warnings.append("cut_v_quantity_source=commercial_deduction")

	return {
		"status": authority.get("status") or "unavailable",
		"currency": currency,
		"estimated_total": round(estimated_total, 4) if preview_lines else None,
		"lines": preview_lines,
		"geometry_summary": {
			"assembly_width_mm": geom.get("assembly_width_mm") or merged.get("assembly_width_mm"),
			"assembly_height_mm": geom.get("assembly_height_mm") or merged.get("assembly_height_mm"),
			"envelope_width_mm": geom.get("envelope_width_mm"),
			"envelope_height_mm": geom.get("envelope_height_mm"),
			"face_area_m2": geom.get("commercial_face_area_m2") or merged.get("commercial_face_area_m2"),
			"cut_length_m": geom.get("commercial_cut_length_m") or merged.get("commercial_cut_length_m"),
			"fold_length_m": geom.get("commercial_fold_length_m") or merged.get("commercial_fold_length_m"),
			"v_groove_l1_ml": geom.get("v_groove_l1_ml") or prod.get("total_v_groove_l1_ml"),
			"v_groove_l2_ml": geom.get("v_groove_l2_ml") or prod.get("total_v_groove_l2_ml"),
			"v_groove_total_ml": geom.get("v_groove_total_ml") or prod.get("total_v_groove_ml"),
			"assembly_exterior_perimeter_m": geom.get("assembly_exterior_perimeter_m"),
			"panel_count": geom.get("panel_count"),
			"joint_count": geom.get("joint_count"),
			"envelope_ignored_for_multi_panel": geom.get("envelope_ignored_for_multi_panel"),
			"path_measurement_status": path_status or None,
			"path_measurement_source": geom.get("path_measurement_source")
			or prod.get("measurement_source")
			or merged.get("acm_path_quantity_source"),
		},
		"production_geometry_metrics": prod or None,
		"material_reference": {
			"preferred_sku": "MAT-ACM-BOND-3MM",
			"legacy_alias": "MAT-ACP-3MM",
			"legacy_excluded_from_duplicate": True,
		},
		"rate_version": ACM_COMMERCIAL_GEOMETRY_VERSION,
		"authority_summary": authority,
		"warnings": list(dict.fromkeys(str(w) for w in warnings)),
		"blockers": list(dict.fromkeys(str(b) for b in blockers)),
		"final_eligibility": bool(authority.get("final_eligibility")),
		"offer_eligibility": bool(authority.get("offer_eligibility")),
		"execution_eligibility": bool(authority.get("execution_eligibility")),
		"line_count": len(preview_lines),
		"hourly_commercial_detected": bool(hourly),
	}


def _optional_commercial_owner_codes(payload_raw: dict[str, Any], commercial_preview: Any) -> frozenset[str]:
	"""Packaging stays optional; montaj is optional only when site install is not required."""
	from services.commercial_price_proposal_service import _site_install_commercially_required

	codes = {"AMBALARE_COMMERCIAL_RULE"}
	site_required = False
	if commercial_preview is not None:
		summary = getattr(commercial_preview, "input_summary", None) or {}
		if isinstance(summary, dict) and summary.get("site_install_required") is True:
			site_required = True
	if not site_required:
		site_required = _site_install_commercially_required(payload_raw if isinstance(payload_raw, dict) else {})
	if not site_required:
		codes.add("MONTAJ_COMMERCIAL_RULE")
	return frozenset(codes)


def _enrich_quote_input_linked_logo_geometry(
	payload_raw: dict[str, Any],
	quote_input: dict[str, Any],
) -> dict[str, Any]:
	"""Copy linked-logo geometry/finish fields omitted by the pricing-input adapter."""
	out = dict(quote_input or {})
	raw_geometry = payload_raw.get("quote_geometry") if isinstance(payload_raw.get("quote_geometry"), dict) else {}
	geometry = dict(out.get("quote_geometry") or {})
	for key in (
		"artwork_boxes",
		"artwork_return_layers",
		"artwork_area_m2",
		"artwork_piece_count",
		"artwork_return_perimeter_ml",
	):
		if (key not in geometry or geometry.get(key) in (None, [], {})) and key in raw_geometry:
			geometry[key] = raw_geometry[key]
	if geometry:
		out["quote_geometry"] = geometry

	raw_finish = payload_raw.get("finish_setup") if isinstance(payload_raw.get("finish_setup"), dict) else {}
	finish = dict(out.get("finish_setup") or {})
	for key in (
		"artwork_finishes",
		"letter_led_module_count",
		"emblem_led_module_count",
		"emblem_lighting_mode",
		"mounting_solution",
		"mounting_scope",
		"site_installation_included",
		"light_color",
		"led_module_count",
		"total_led_module_count",
	):
		if (key not in finish or finish.get(key) in (None, [], {})) and key in raw_finish:
			finish[key] = raw_finish[key]
	letter_led = _positive_number(finish.get("letter_led_module_count"))
	emblem_led = _positive_number(finish.get("emblem_led_module_count"))
	total_led = _positive_number(finish.get("led_module_count") or finish.get("total_led_module_count"))
	if letter_led is None and total_led is not None and emblem_led is not None and total_led >= emblem_led:
		finish["letter_led_module_count"] = round(total_led - emblem_led, 4)
	if finish:
		out["finish_setup"] = finish
	return out


async def resolve_intake_v6_canonical_quote_input(
	db: AsyncSession,
	workspace_id: str | int,
) -> tuple[str, dict[str, Any]] | None:
	"""Rebuild full V6 quote_input for canonical 7G/7H compose — same path as priced dry-run."""
	workspace_id_str = str(workspace_id)
	record = await _get_record_or_404(db, workspace_id_str)
	payload_raw = _json_loads(record.payload_json, {})
	if not isinstance(payload_raw, dict):
		payload_raw = {}
	payload = _parse_payload(payload_raw)
	pricing_preview = build_v6_pricing_input_preview(
		workspace_id=workspace_id_str,
		payload=payload,
		template_code=record.template_code,
		payload_raw=payload_raw,
	)
	quote_input = merge_workspace_offer_scope_into_quote_input(
		payload_raw,
		dict(getattr(pricing_preview, "quote_input_payload", {}) or {}),
	)
	quote_input = _enrich_quote_input_linked_logo_geometry(payload_raw, quote_input)
	return record.template_code, quote_input


async def build_intake_v6_priced_quote_dry_run(
	db: AsyncSession,
	workspace_id: str | int,
	*,
	pricing_mode: str = "dry_run",
) -> dict[str, Any]:
	workspace_id_str = str(workspace_id)
	record = await _get_record_or_404(db, workspace_id_str)
	payload_raw = _json_loads(record.payload_json, {})
	if not isinstance(payload_raw, dict):
		payload_raw = {}
	payload = _parse_payload(payload_raw)
	composition_recommendation = (
		payload_raw.get("product_composition_recommendation")
		if isinstance(payload_raw.get("product_composition_recommendation"), dict)
		else None
	)
	composition_confirmation = (
		payload_raw.get("product_composition_confirmed")
		if isinstance(payload_raw.get("product_composition_confirmed"), dict)
		else None
	)
	composition_confirmed = bool(composition_confirmation and composition_confirmation.get("confirmed") is True)

	pricing_preview = build_v6_pricing_input_preview(
		workspace_id=workspace_id_str,
		payload=payload,
		template_code=record.template_code,
		payload_raw=payload_raw,
	)
	quote_input = merge_workspace_offer_scope_into_quote_input(
		payload_raw,
		dict(getattr(pricing_preview, "quote_input_payload", {}) or {}),
	)
	quote_input = _enrich_quote_input_linked_logo_geometry(payload_raw, quote_input)
	settings_vat_percent = float(await get_default_vat_pct(db))
	commercial_inputs = _read_commercial_inputs(
		payload_raw,
		quote_input,
		settings_vat_percent=settings_vat_percent,
	)

	warnings = list(getattr(pricing_preview, "adapter_warnings", []) or [])
	blockers: list[dict[str, str]] = []
	if composition_recommendation and not composition_confirmed:
		blockers.append(
			_blocker(
				"PRODUCT_COMPOSITION_NOT_CONFIRMED",
				"Operatorul trebuie sa confirme compozitia produsului propusa de analyzer inainte de priced dry-run ready.",
			)
		)
	if not getattr(pricing_preview, "is_ready_for_quote", False):
		for code in getattr(pricing_preview, "adapter_blockers", []) or []:
			blockers.append(_blocker(str(code), "V6 backend pricing input is not ready for dry-run."))
		if not blockers:
			blockers.append(
				_blocker(
					V6_PRICED_DRY_RUN_SOURCE_MISSING,
					"V6 backend pricing input is not ready for priced quote dry-run.",
				)
			)

	material_breakdown = None
	material_warning = None
	try:
		material_breakdown = await get_material_breakdown_for_workspace(db, workspace_id_str)
	except Exception as exc:  # pragma: no cover - defensive trace, pricing preview may still explain blocker
		material_warning = f"material_breakdown_unavailable:{type(exc).__name__}"
		warnings.append(material_warning)

	commercial_preview = await CommercialPriceProposalService(db).build_preview(
		record.template_code,
		workspace_id=workspace_id_str,
		quote_input=quote_input,
		currency="RON",
	)
	internal_preview = await EstimatedInternalCostService(db).build_preview(
		record.template_code,
		workspace_id=workspace_id_str,
		quote_input=quote_input,
		currency="RON",
	)
	if commercial_preview is None:
		blockers.append(
			_blocker(
				V6_PRICED_DRY_RUN_SOURCE_MISSING,
				"CommercialPriceProposal preview is unavailable for this V6 template.",
			)
		)
		vat_rate = None
		line_items: list[dict[str, Any]] = []
		subtotal = None
	else:
		warnings.extend(list(commercial_preview.warnings or []))
		for blocker in commercial_preview.commercial_blockers:
			blockers.append(_blocker(blocker.code, blocker.message))
		for decision in commercial_preview.unknown_owner_decisions:
			optional_codes = _optional_commercial_owner_codes(payload_raw, commercial_preview)
			if decision.code in optional_codes:
				warnings.append(
					decision.detail
					or f"Optional owner commercial decision pending for {decision.label}."
				)
				continue
			blockers.append(
				_blocker(
					decision.code,
					decision.detail or f"Owner commercial decision required for {decision.label}.",
				)
			)
		if commercial_preview.forbidden_hourly_usage_detected:
			blockers.append(
				_blocker(
					"FORBIDDEN_HOURLY_COMMERCIAL_USAGE",
					"Commercial dry-run detected forbidden hourly pricing basis.",
				)
			)
		subtotal = _positive_number(commercial_preview.subtotal_commercial)
		line_items = _commercial_line_items(commercial_preview)
		vat_rate = settings_vat_percent

	if commercial_preview is not None and commercial_preview.status != "ready":
		blockers.append(
			_blocker(
				"V6_PRICED_DRY_RUN_COMMERCIAL_REVIEW_NOT_READY",
				f"CommercialPriceProposal status is {commercial_preview.status}; dry-run cannot be treated as ready.",
			)
		)

	internal_totals = getattr(getattr(material_breakdown, "totals", None), "estimated_cost_total", None)
	internal_cost_total = _positive_number(internal_totals)
	eic_internal_total = _positive_number(
		getattr(internal_preview, "estimated_total_internal_cost", None) if internal_preview else None
	)

	pricing_authority: str | None = None
	diagnostic_cost_plus: dict[str, Any] | None = None

	if blockers:
		totals = _empty_totals(vat_rate=vat_rate)
	elif subtotal is None or subtotal <= 0:
		blockers.append(
			_blocker(
				V6_PRICED_DRY_RUN_ZERO_TOTAL,
				"CommercialPriceProposal produced no official subtotal; V6 cannot expose a synthetic commercial total.",
			)
		)
		totals = _empty_totals(vat_rate=vat_rate)
	else:
		totals = _official_totals_from_7g(subtotal=subtotal, vat_rate=float(vat_rate or 0))
		pricing_authority = V6_OFFICIAL_COMMERCIAL_AUTHORITY

	if internal_cost_total is not None or eic_internal_total is not None:
		eur_to_ron_rate = float(await get_eur_to_ron_rate(db))
		diagnostic_base = internal_cost_total if internal_cost_total is not None else eic_internal_total
		if diagnostic_base is not None:
			diagnostic_cost_plus = _build_cost_plus_totals(
				internal_cost_total=diagnostic_base,
				eur_to_ron_rate=eur_to_ron_rate,
				commercial_inputs=commercial_inputs,
			)
			diagnostic_cost_plus["diagnostic_only"] = True
			diagnostic_cost_plus["td_id"] = TD_W3_V6_DIAG_COST_PLUS
			diagnostic_cost_plus["canonical_authority"] = V6_OFFICIAL_COMMERCIAL_AUTHORITY

	pricing_status = V6_PRICED_DRY_RUN_BLOCKED if blockers else V6_PRICED_DRY_RUN_READY
	acm_panel_commercial_preview = _build_acm_panel_commercial_preview(
		quote_input=quote_input,
		payload_raw=payload_raw if isinstance(payload_raw, dict) else {},
		line_items=line_items,
	)
	if acm_panel_commercial_preview is not None:
		for w in acm_panel_commercial_preview.get("warnings") or []:
			warnings.append(f"acm_panel:{w}")

	return {
		"pricing_status": pricing_status,
		"pricing_authority": pricing_authority,
		"commercial_authority_status": "ready" if pricing_authority else "blocked",
		"workspace_id": workspace_id_str,
		"workspace_code": record.workspace_code,
		"intake_code": getattr(payload, "intake_request_code", None),
		"template_code": record.template_code,
		"product_composition_recommendation": composition_recommendation,
		"product_composition_confirmed": composition_confirmation,
		"composition_items": (composition_recommendation or {}).get("composition_items", []),
		"pricing_source": V6_PRICED_DRY_RUN_SOURCE,
		"pricing_mode": pricing_mode,
		"commercial_totals": totals,
		"commercial_line_items": line_items,
		"acm_panel_commercial_preview": acm_panel_commercial_preview,
		"internal_cost_trace": _material_trace(material_breakdown, material_warning),
		"estimated_internal_cost_trace": _estimated_internal_cost_trace(internal_preview),
		"diagnostic_cost_plus_trace": diagnostic_cost_plus,
		"pricing_input_trace": _pricing_trace(pricing_preview),
		"commercial_proposal_trace": {
			"available": commercial_preview is not None,
			"source": getattr(commercial_preview, "source", None),
			"status": getattr(commercial_preview, "status", None),
			"quote_ready_for_commercial_review": getattr(
				commercial_preview,
				"quote_ready_for_commercial_review",
				False,
			),
			"subtotal_commercial": getattr(commercial_preview, "subtotal_commercial", None),
			"provenance": [
				entry.model_dump(mode="json")
				for entry in (getattr(commercial_preview, "provenance", []) or [])
			],
			"official_authority": pricing_authority,
			"diagnostic_cost_plus_td": TD_W3_V6_DIAG_COST_PLUS if diagnostic_cost_plus else None,
		},
		"warnings": list(dict.fromkeys(str(warning) for warning in warnings)),
		"blockers": blockers,
		"can_write_quote_totals": False,
		"can_create_quote_snapshot": False,
		"dry_run_only": True,
		"persistence": {
			"creates_quote": False,
			"updates_quote": False,
			"writes_quote_totals": False,
			"creates_quote_snapshot": False,
			"creates_order": False,
		},
	}
