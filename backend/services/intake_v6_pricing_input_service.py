"""Intake V6 pricing input preview namespace."""

from __future__ import annotations

from typing import Any

from services.intake_v6_product_pricing_adapter_registry import (
	build_v6_pricing_input_preview_for_template,
)


def build_v6_pricing_input_preview(
	*,
	workspace_id: str,
	payload: Any,
	template_code: str | None = None,
) -> Any:
	return build_v6_pricing_input_preview_for_template(
		workspace_id=workspace_id,
		payload=payload,
		template_code=template_code,
	)
