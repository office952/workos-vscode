"""Tests for Intake V6 product pricing adapter registry."""

from __future__ import annotations

from services.intake_v6_product_pricing_adapter_registry import (
	default_intake_v6_product_pricing_adapter,
	list_intake_v6_product_pricing_adapters,
	resolve_intake_v6_product_pricing_adapter,
)


def test_resolve_volumetric_adapter_by_canonical_and_alias() -> None:
	by_v2 = resolve_intake_v6_product_pricing_adapter("TPL-VOLUMETRIC-LETTERS_v2")
	by_legacy = resolve_intake_v6_product_pricing_adapter("TPL-VOLUMETRIC-LETTERS")
	assert by_v2 is not None
	assert by_legacy is by_v2
	assert by_v2.display_name == "Litere volumetrice"


def test_resolve_normalizes_template_code() -> None:
	adapter = resolve_intake_v6_product_pricing_adapter("  tpl-volumetric-letters  ")
	assert adapter is not None
	assert adapter.template_code == "TPL-VOLUMETRIC-LETTERS_v2"


def test_resolve_unknown_template_returns_none() -> None:
	assert resolve_intake_v6_product_pricing_adapter("TPL-UNKNOWN") is None
	assert resolve_intake_v6_product_pricing_adapter(None) is None
	assert resolve_intake_v6_product_pricing_adapter("") is None


def test_list_registered_adapters_includes_pilot() -> None:
	adapters = list_intake_v6_product_pricing_adapters()
	assert len(adapters) >= 1
	assert adapters[0].pricing_source == "intake_v6_pricing_input_preview"


def test_unknown_template_uses_default_volumetric_adapter() -> None:
	assert resolve_intake_v6_product_pricing_adapter("TPL-UNKNOWN") is None
	default = default_intake_v6_product_pricing_adapter()
	assert default.template_code == "TPL-VOLUMETRIC-LETTERS_v2"
	assert default.pricing_source == "intake_v6_pricing_input_preview"
