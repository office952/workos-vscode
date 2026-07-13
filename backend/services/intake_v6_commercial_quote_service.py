"""Intake V6 commercial quote handoff service namespace."""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.auth import UserResponse
from schemas.intake_v6 import (
	IntakeV6CreateDraftQuoteRequest,
	IntakeV6CreateDraftQuoteResponse,
	IntakeV6QuoteHandoffPreviewResponse,
)
from services.intake_v4_commercial_quote_service import (
	_build_linked_module_lines,
	build_v4_quote_draft_payload,
	build_v4_quote_snapshot_payload,
	client_order_production_flags_for_quote,
)
from services.intake_v6_canonical_readiness_service import (
	collect_canonical_readiness_findings,
	merge_policy_findings,
)
from services.intake_v6_internal_draft_quote_policy_service import evaluate_internal_draft_quote_policy
from services.intake_v6_offer_scope_live_calc_service import merge_workspace_offer_scope_into_quote_input
from services.intake_v6_pricing_input_service import build_v6_pricing_input_preview
from services.intake_v6_workspace_service import _get_record_or_404, _json_loads, _parse_payload
from services.quotes import QuotesService


INTAKE_V6_LINKAGE_JSON_KEY = "intake_v6_linkage_v1"
INTAKE_V6_LINKAGE_CODE_PREFIX = "IV6-"
INTAKE_V6_PRICING_SOURCE = "intake_v6_pricing_input_preview"
INTAKE_V6_SNAPSHOT_POLICY_VERSION = "intake_v6_quote_handoff_v1"


def intake_v6_linkage_code(workspace_id: str) -> str:
	return f"{INTAKE_V6_LINKAGE_CODE_PREFIX}{workspace_id}"


def _raise_blocked(error: str, message: str, blockers: list[str] | None = None) -> None:
	raise HTTPException(
		status_code=422,
		detail={
			"error": error,
			"message": message,
			"blockers": blockers or [error],
			"fatal_blockers": blockers or [error],
		},
	)


async def check_existing_quote_for_intake_v6_workspace(
	db: AsyncSession,
	workspace_id: str,
):
	quotes_service = QuotesService(db)
	existing = await quotes_service.list_by_field("intake_code", intake_v6_linkage_code(workspace_id), limit=1)
	return existing[0] if existing else None


def parse_intake_v6_linkage_from_notes(notes: str | None) -> dict[str, Any] | None:
	if not notes:
		return None
	try:
		payload = json.loads(notes)
	except json.JSONDecodeError:
		return None
	if not isinstance(payload, dict):
		return None
	linkage = payload.get(INTAKE_V6_LINKAGE_JSON_KEY)
	return linkage if isinstance(linkage, dict) else None


def _strip_v6_draft_quote_pricing_fields(quote_data: dict[str, Any]) -> dict[str, Any]:
	normalized = dict(quote_data)
	for field in ("subtotal", "total_before_vat", "vat", "grand_total"):
		normalized[field] = None

	raw_line_items = normalized.get("line_items")
	try:
		parsed_line_items = json.loads(str(raw_line_items or "[]"))
	except json.JSONDecodeError:
		return normalized
	if not isinstance(parsed_line_items, list):
		return normalized

	sanitized_line_items: list[dict[str, Any]] = []
	for item in parsed_line_items:
		if not isinstance(item, dict):
			continue
		sanitized = dict(item)
		sanitized["unit_price"] = None
		sanitized["total"] = None
		sanitized_line_items.append(sanitized)
	normalized["line_items"] = json.dumps(sanitized_line_items)
	return normalized


def _normalize_v6_quote_draft_payload(
	quote_data: dict[str, Any],
	*,
	workspace_id: str,
	workspace_code: str,
	snapshot: dict[str, Any],
	quote_input: dict[str, Any],
	requires_pricing_review: bool,
) -> dict[str, Any]:
	normalized = dict(quote_data)
	normalized["intake_code"] = intake_v6_linkage_code(workspace_id)

	try:
		notes_payload = json.loads(str(normalized.get("notes") or "{}"))
	except json.JSONDecodeError:
		notes_payload = {}
	if not isinstance(notes_payload, dict):
		notes_payload = {}

	legacy_linkage = notes_payload.pop("intake_v4_linkage_v1", {})
	linkage = dict(legacy_linkage if isinstance(legacy_linkage, dict) else {})
	linkage.update(
		{
			"source_module": "intake_v6",
			"source_intake_version": "V6",
			"source_workspace_id": workspace_id,
			"source_workspace_code": workspace_code,
			"requires_pricing_review": requires_pricing_review,
			"pricing_source": INTAKE_V6_PRICING_SOURCE,
			"snapshot": snapshot,
			"snapshot_policy_version": INTAKE_V6_SNAPSHOT_POLICY_VERSION,
			"quote_input_payload": quote_input,
		}
	)
	notes_payload.update(
		{
			"human_summary": (
				f"Draft generat din Intake V6 workspace {workspace_code}. "
				"Totalurile sunt pregatite ca preview V6, dar nu au fost inca scrise pe oferta "
				"ca pret comercial final. Oferta este doar pentru revizie interna si nu poate fi "
				"trimisa clientului, acceptata, transformata in comanda sau trimisa in productie."
			),
			INTAKE_V6_LINKAGE_JSON_KEY: linkage,
		}
	)
	normalized["notes"] = json.dumps(notes_payload, default=str)
	return _strip_v6_draft_quote_pricing_fields(normalized)


async def get_quote_handoff_preview_for_workspace(
	db: AsyncSession,
	workspace_id: str,
	*,
	client_analysis_hash: str | None = None,
) -> IntakeV6QuoteHandoffPreviewResponse:
	record = await _get_record_or_404(db, workspace_id)
	payload_raw = _json_loads(record.payload_json, {})
	payload = _parse_payload(payload_raw if isinstance(payload_raw, dict) else {})
	pricing_preview = build_v6_pricing_input_preview(
		workspace_id=workspace_id,
		payload=payload,
		template_code=record.template_code,
		payload_raw=payload_raw if isinstance(payload_raw, dict) else {},
	)
	canonical_findings = await collect_canonical_readiness_findings(
		db,
		workspace_id=workspace_id,
		template_code=record.template_code,
	)
	policy = evaluate_internal_draft_quote_policy(
		record,
		payload,
		pricing_preview=pricing_preview,
		client_analysis_hash=client_analysis_hash,
		include_hash_sync=bool(client_analysis_hash),
	)
	merged = merge_policy_findings(policy=policy, findings=canonical_findings)
	legacy_blockers = [*merged["fatal_blockers"], *merged["review_warnings"]]
	return IntakeV6QuoteHandoffPreviewResponse(
		workspace_id=workspace_id,
		workspace_readiness_status=record.readiness_status,
		handoff_allowed=merged["can_create_internal_draft_quote"],
		status_label=merged["status_label"],
		blockers=legacy_blockers,
		can_create_internal_draft_quote=merged["can_create_internal_draft_quote"],
		requires_operator_confirmation=policy.requires_operator_confirmation,
		operator_confirmation_complete=policy.operator_confirmation_complete,
		fatal_blockers=merged["fatal_blockers"],
		review_warnings=merged["review_warnings"],
		client_send_allowed=merged["client_send_allowed"],
		accept_allowed=merged["accept_allowed"],
		convert_to_order_allowed=merged["convert_to_order_allowed"],
		production_allowed=merged["production_allowed"],
		preview_only=True,
	)


async def create_guarded_draft_quote_from_intake_v6_workspace(
	db: AsyncSession,
	workspace_id: str,
	request: IntakeV6CreateDraftQuoteRequest,
	current_user: UserResponse,
) -> IntakeV6CreateDraftQuoteResponse:
	record = await _get_record_or_404(db, workspace_id)
	payload_raw = _json_loads(record.payload_json, {})
	payload = _parse_payload(payload_raw if isinstance(payload_raw, dict) else {})

	pricing_preview = build_v6_pricing_input_preview(
		workspace_id=workspace_id,
		payload=payload,
		template_code=record.template_code,
		payload_raw=payload_raw if isinstance(payload_raw, dict) else {},
	)
	policy = evaluate_internal_draft_quote_policy(
		record,
		payload,
		pricing_preview=pricing_preview,
		client_analysis_hash=request.client_analysis_hash,
		include_hash_sync=True,
	)
	canonical_findings = await collect_canonical_readiness_findings(
		db,
		workspace_id=workspace_id,
		template_code=record.template_code,
	)
	merged = merge_policy_findings(policy=policy, findings=canonical_findings)

	if not request.confirm_internal_draft_quote:
		_raise_blocked(
			"INTERNAL_DRAFT_CONFIRMATION_REQUIRED",
			"Operator must confirm internal draft quote readiness before creation.",
			["operator_confirmation_missing"],
		)

	if not payload.finish_setup or not payload.finish_setup.internal_draft_quote_confirmed:
		_raise_blocked(
			"INTERNAL_DRAFT_CONFIRMATION_REQUIRED",
			"Persisted operator confirmation for internal draft quote is missing.",
			["operator_confirmation_missing"],
		)

	if merged["fatal_blockers"]:
		_raise_blocked(
			"INTERNAL_DRAFT_QUOTE_BLOCKED",
			"Workspace V6 is not ready for internal draft quote creation.",
			merged["fatal_blockers"],
		)

	existing = await check_existing_quote_for_intake_v6_workspace(db, workspace_id)
	if existing is not None:
		_raise_blocked(
			"DUPLICATE_QUOTE_FOR_WORKSPACE",
			f"Quote already linked to Intake V6 workspace {workspace_id}.",
			["DUPLICATE_QUOTE_FOR_WORKSPACE"],
		)

	requires_pricing_review = True if merged["review_warnings"] else False
	payload_raw = _json_loads(record.payload_json, {})
	if not isinstance(payload_raw, dict):
		payload_raw = {}
	quote_input = merge_workspace_offer_scope_into_quote_input(
		payload_raw,
		dict(pricing_preview.quote_input_payload),
	)
	linked_modules = await _build_linked_module_lines(
		db,
		payload=payload,
		quote_input=quote_input,
	)
	if linked_modules:
		quote_input["parent_mounting_system"] = quote_input.get("mounting_system")
		quote_input["metal_support_required"] = True
		quote_input["linked_support_pricing_mode"] = "separate_quote_line"
		quote_input["support_module_template_code"] = linked_modules[0].get("module_template_code")
		quote_input["mounting_system"] = "direct_wall"
		quote_input["linked_modules"] = linked_modules

	snapshot = build_v4_quote_snapshot_payload(
		workspace_id=record.id,
		workspace_code=record.workspace_code,
		payload=payload,
		pricing_preview=pricing_preview,
		current_user=current_user,
		decision_reason=request.decision_reason,
		review_warnings=merged["review_warnings"],
		source_module="intake_v6",
		linked_modules=linked_modules,
	)
	snapshot["policy_version"] = INTAKE_V6_SNAPSHOT_POLICY_VERSION
	snapshot["pricing_source"] = INTAKE_V6_PRICING_SOURCE
	if isinstance(snapshot.get("owner_decision"), dict):
		snapshot["owner_decision"]["approval_source"] = "intake_v6_confirm_step"
	quote_data = build_v4_quote_draft_payload(
		record=record,
		payload=payload,
		snapshot=snapshot,
		quote_input=quote_input,
		requires_pricing_review=requires_pricing_review,
	)
	quote_data = _normalize_v6_quote_draft_payload(
		quote_data,
		workspace_id=record.id,
		workspace_code=record.workspace_code,
		snapshot=snapshot,
		quote_input=quote_input,
		requires_pricing_review=requires_pricing_review,
	)

	quotes_service = QuotesService(db)
	try:
		quote_obj = await quotes_service.create(quote_data)
	except Exception as exc:
		_raise_blocked("QUOTE_PERSISTENCE_FAILED", f"Quote persistence failed: {exc}")

	if quote_obj is None:
		_raise_blocked("QUOTE_PERSISTENCE_FAILED", "Quote persistence returned no object.")

	downstream = client_order_production_flags_for_quote(review_warnings=merged["review_warnings"])
	return IntakeV6CreateDraftQuoteResponse(
		quote_created=True,
		quote_id=quote_obj.id,
		quote_code=quote_obj.code,
		quote_status=quote_obj.status,
		source_module="intake_v6",
		source_workspace_id=workspace_id,
		quote_input_payload=quote_input,
		snapshot_attached=True,
		requires_pricing_review=requires_pricing_review,
		client_send_allowed=downstream["client_send_allowed"],
		accept_allowed=downstream["accept_allowed"],
		convert_to_order_allowed=downstream["convert_to_order_allowed"],
		production_allowed=downstream["production_allowed"],
		order_created=False,
		execution_plan_created=False,
		inventory_mutated=False,
	)


async def create_or_reuse_guarded_draft_quote_from_intake_v6_workspace(
	db: AsyncSession,
	workspace_id: str,
	request: IntakeV6CreateDraftQuoteRequest,
	current_user: UserResponse,
) -> IntakeV6CreateDraftQuoteResponse:
	existing = await check_existing_quote_for_intake_v6_workspace(db, workspace_id)
	if existing is not None:
		return IntakeV6CreateDraftQuoteResponse(
			quote_created=False,
			quote_id=existing.id,
			quote_code=existing.code,
			quote_status=existing.status,
			source_module="intake_v6",
			source_workspace_id=workspace_id,
			quote_input_payload={},
			snapshot_attached=True,
			requires_pricing_review=True,
			client_send_allowed=False,
			accept_allowed=False,
			convert_to_order_allowed=False,
			production_allowed=False,
			order_created=False,
			execution_plan_created=False,
			inventory_mutated=False,
		)

	return await create_guarded_draft_quote_from_intake_v6_workspace(
		db,
		workspace_id,
		request,
		current_user,
	)
