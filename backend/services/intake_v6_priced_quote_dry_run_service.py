"""Backend-only Intake V6 priced quote dry-run.

No quote creation, no quote update, no snapshot, no order, no V4 draft payload.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.company_commercial_settings_service import get_default_vat_pct, get_eur_to_ron_rate
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

# Optional/future commercial owner decisions — surfaced as warnings, not dry-run blockers.
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
			}
		)
	return items


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
			if decision.code in V6_OPTIONAL_COMMERCIAL_OWNER_DECISION_CODES:
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
	eur_to_ron_rate = float(await get_eur_to_ron_rate(db))

	if internal_cost_total is not None:
		cost_plus_totals = _build_cost_plus_totals(
			internal_cost_total=internal_cost_total,
			eur_to_ron_rate=eur_to_ron_rate,
			commercial_inputs=commercial_inputs,
		)
		totals = {
			"subtotal_net": cost_plus_totals["subtotal_net"],
			"vat_rate": cost_plus_totals["vat_rate"],
			"vat_amount": cost_plus_totals["vat_amount"],
			"total_gross": cost_plus_totals["total_gross"],
			"currency": "RON",
		}
		warnings.append("official_v6_pricing_uses_cost_plus_from_material_breakdown")
	elif subtotal is None:
		blockers.append(
			_blocker(
				V6_PRICED_DRY_RUN_ZERO_TOTAL,
				"Backend dry-run produced zero totals; this cannot be treated as official V6 quote price.",
			)
		)
		totals = _empty_totals(vat_rate=vat_rate)
	else:
		vat_amount = _round_money(subtotal * float(vat_rate or 0) / 100)
		totals = {
			"subtotal_net": _round_money(subtotal),
			"vat_rate": float(vat_rate or 0),
			"vat_amount": vat_amount,
			"total_gross": _round_money(subtotal + vat_amount),
			"currency": "RON",
		}

	pricing_status = V6_PRICED_DRY_RUN_BLOCKED if blockers else V6_PRICED_DRY_RUN_READY
	return {
		"pricing_status": pricing_status,
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
		"internal_cost_trace": _material_trace(material_breakdown, material_warning),
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
			"cost_plus_inputs": {
				"commercial_inputs": commercial_inputs,
				"internal_cost_total": internal_cost_total,
				"internal_cost_currency": getattr(getattr(material_breakdown, "totals", None), "currency", None),
				"eur_to_ron_rate": eur_to_ron_rate,
			},
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
