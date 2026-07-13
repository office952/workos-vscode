"""Intake V6 pricing input preview namespace."""

from __future__ import annotations

from typing import Any

from services.intake_v6_offer_scope_live_calc_service import (
	coerce_payload_raw,
	merge_workspace_offer_scope_into_quote_input,
)
from services.intake_v6_product_pricing_adapter_registry import (
	build_v6_pricing_input_preview_for_template,
)


def build_v6_pricing_input_preview(
	*,
	workspace_id: str,
	payload: Any,
	template_code: str | None = None,
	payload_raw: dict[str, Any] | None = None,
) -> Any:
	preview = build_v6_pricing_input_preview_for_template(
		workspace_id=workspace_id,
		payload=payload,
		template_code=template_code,
	)
	raw = coerce_payload_raw(payload, payload_raw)
	quote_input = merge_workspace_offer_scope_into_quote_input(
		raw,
		dict(getattr(preview, "quote_input_payload", {}) or {}),
	)
	if hasattr(preview, "model_copy"):
		preview = preview.model_copy(update={"quote_input_payload": quote_input})
	elif isinstance(preview, dict):
		updated = dict(preview)
		updated["quote_input_payload"] = quote_input
		preview = updated

	from services.intake_v6_canonical_readiness_service import apply_readiness_spine_to_pricing_preview

	if hasattr(preview, "model_copy"):
		return apply_readiness_spine_to_pricing_preview(
			preview,
			payload=raw,
			template_code=template_code,
		)
	return preview
