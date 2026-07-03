"""Intake V6 product pricing input adapter registry (spike).

Maps template_code → pricing-input builder so priced-quote and preview services
do not accumulate per-template branches. See docs/architecture/INTAKE_V6_MODULARIZATION_AUDIT.md.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from services.intake_v6_response_normalization import normalize_intake_v6_model

PricingInputBuilder = Callable[..., Any]


def _normalize_template_code(code: str) -> str:
	return code.strip().upper()


def _build_volumetric_pricing_preview(*, workspace_id: str, payload: Any, **_kwargs: Any) -> Any:
	from services.intake_v4_pricing_input_service import build_v4_pricing_input_preview

	return normalize_intake_v6_model(
		build_v4_pricing_input_preview(workspace_id=workspace_id, payload=payload)
	)


@dataclass(frozen=True)
class IntakeV6ProductPricingAdapter:
	template_code: str
	template_code_aliases: tuple[str, ...] = ()
	display_name: str = ""
	builder: PricingInputBuilder = _build_volumetric_pricing_preview
	pricing_source: str = "intake_v6_pricing_input_preview"


REGISTERED_PRICING_ADAPTERS: tuple[IntakeV6ProductPricingAdapter, ...] = (
	IntakeV6ProductPricingAdapter(
		template_code="TPL-VOLUMETRIC-LETTERS_v2",
		template_code_aliases=("TPL-VOLUMETRIC-LETTERS",),
		display_name="Litere volumetrice",
		builder=_build_volumetric_pricing_preview,
		pricing_source="intake_v6_pricing_input_preview",
	),
)

_ADAPTER_BY_TEMPLATE_CODE: dict[str, IntakeV6ProductPricingAdapter] = {}


def _ensure_adapter_index() -> None:
	if _ADAPTER_BY_TEMPLATE_CODE:
		return
	for adapter in REGISTERED_PRICING_ADAPTERS:
		_ADAPTER_BY_TEMPLATE_CODE[_normalize_template_code(adapter.template_code)] = adapter
		for alias in adapter.template_code_aliases:
			_ADAPTER_BY_TEMPLATE_CODE[_normalize_template_code(alias)] = adapter


def resolve_intake_v6_product_pricing_adapter(
	template_code: str | None,
) -> IntakeV6ProductPricingAdapter | None:
	code = (template_code or "").strip()
	if not code:
		return None
	_ensure_adapter_index()
	return _ADAPTER_BY_TEMPLATE_CODE.get(_normalize_template_code(code))


def default_intake_v6_product_pricing_adapter() -> IntakeV6ProductPricingAdapter:
	_ensure_adapter_index()
	return REGISTERED_PRICING_ADAPTERS[0]


def build_v6_pricing_input_preview_for_template(
	*,
	workspace_id: str,
	payload: Any,
	template_code: str | None = None,
) -> Any:
	adapter = resolve_intake_v6_product_pricing_adapter(template_code) or default_intake_v6_product_pricing_adapter()
	return adapter.builder(workspace_id=workspace_id, payload=payload, template_code=template_code)


def list_intake_v6_product_pricing_adapters() -> tuple[IntakeV6ProductPricingAdapter, ...]:
	return REGISTERED_PRICING_ADAPTERS
