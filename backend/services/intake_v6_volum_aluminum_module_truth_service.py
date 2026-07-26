"""Intake V6 volum aluminum module technical truth — Product System resolution + persist."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from services.intake_v4_product_system_service import list_template_module_links, resolve_product_template_or_raise
from services.return_cant_finish_truth_service import INACTIVE_RETURN_FINISH_TYPES

VOLUM_ALUMINUM_TRIGGER_FIELD = "volum_aluminum_module_template_code"
MODELARE_CANT_MODULE = "modelare_cant"
VOLUMETRIC_LETTERS_TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"

ResolutionSource = Literal[
	"not_applicable",
	"operator_explicit",
	"product_system_unique_link",
	"missing_requires_operator",
	"missing_no_module_links",
	"cleared_stale_incompatible",
	"cleared_not_applicable",
]


@dataclass(frozen=True)
class VolumAluminumModuleResolution:
	applicable: bool
	resolved_code: str | None
	source: ResolutionSource
	module_link_codes: tuple[str, ...] = ()
	blockers: list[str] = field(default_factory=list)
	warnings: list[str] = field(default_factory=list)


def _positive_number(value: Any) -> float | None:
	try:
		number = float(value)
	except (TypeError, ValueError):
		return None
	return number if number > 0 else None


def _read_string(value: Any) -> str | None:
	if value is None:
		return None
	text = str(value).strip()
	return text or None


def is_volum_aluminum_module_applicable(
	*,
	template_code: str,
	finish_setup: dict[str, Any] | None,
) -> bool:
	"""Cant/lateral aluminum module applies to volumetric letter products with active cant truth."""
	code = _read_string(template_code) or ""
	if code != VOLUMETRIC_LETTERS_TEMPLATE:
		return False
	finish = finish_setup if isinstance(finish_setup, dict) else {}
	return_finish = _read_string(finish.get("return_finish_type"))
	if not return_finish or return_finish.lower() in INACTIVE_RETURN_FINISH_TYPES:
		return False
	if _positive_number(finish.get("return_depth_mm")) is None:
		return False
	return True


def _volum_module_links(module_links: list[Any]) -> list[Any]:
	items: list[Any] = []
	for link in module_links:
		trigger = _read_string(getattr(link, "trigger_field", None))
		module_code = _read_string(getattr(link, "module_template_code", None)) or ""
		if trigger == VOLUM_ALUMINUM_TRIGGER_FIELD:
			items.append(link)
			continue
		upper = module_code.upper()
		if "VOLUM" in upper and "ALUMIN" in upper:
			items.append(link)
	return items


def resolve_volum_aluminum_module_template_code(
	*,
	template_code: str,
	finish_setup: dict[str, Any] | None,
	module_links: list[Any],
) -> VolumAluminumModuleResolution:
	applicable = is_volum_aluminum_module_applicable(
		template_code=template_code,
		finish_setup=finish_setup,
	)
	finish = finish_setup if isinstance(finish_setup, dict) else {}
	explicit = _read_string(finish.get(VOLUM_ALUMINUM_TRIGGER_FIELD))
	candidates = _volum_module_links(module_links)
	candidate_codes = tuple(
		_read_string(getattr(link, "module_template_code", None))
		for link in candidates
		if _read_string(getattr(link, "module_template_code", None))
	)

	if not applicable:
		if explicit:
			return VolumAluminumModuleResolution(
				applicable=False,
				resolved_code=None,
				source="cleared_not_applicable",
				module_link_codes=candidate_codes,
				warnings=["volum_aluminum_module_not_applicable_for_current_product_truth"],
			)
		return VolumAluminumModuleResolution(
			applicable=False,
			resolved_code=None,
			source="not_applicable",
			module_link_codes=candidate_codes,
		)

	if not candidate_codes:
		return VolumAluminumModuleResolution(
			applicable=True,
			resolved_code=None,
			source="missing_no_module_links",
			module_link_codes=(),
			blockers=["volum_aluminum_module_link_missing"],
		)

	valid_codes = set(candidate_codes)
	if explicit:
		if explicit in valid_codes:
			return VolumAluminumModuleResolution(
				applicable=True,
				resolved_code=explicit,
				source="operator_explicit",
				module_link_codes=candidate_codes,
			)
		return VolumAluminumModuleResolution(
			applicable=True,
			resolved_code=None,
			source="cleared_stale_incompatible",
			module_link_codes=candidate_codes,
			blockers=["volum_aluminum_module_template_incompatible_with_product_system"],
			warnings=[f"cleared_stale_volum_aluminum_module_template_code={explicit}"],
		)

	if len(candidate_codes) == 1:
		return VolumAluminumModuleResolution(
			applicable=True,
			resolved_code=candidate_codes[0],
			source="product_system_unique_link",
			module_link_codes=candidate_codes,
		)

	return VolumAluminumModuleResolution(
		applicable=True,
		resolved_code=None,
		source="missing_requires_operator",
		module_link_codes=candidate_codes,
		blockers=["volum_aluminum_module_selection_required"],
	)


async def resolve_volum_aluminum_module_for_template(
	db: AsyncSession,
	*,
	template_code: str,
	finish_setup: dict[str, Any] | None,
) -> VolumAluminumModuleResolution:
	template = await resolve_product_template_or_raise(db, template_code)
	module_links = await list_template_module_links(db, template)
	return resolve_volum_aluminum_module_template_code(
		template_code=template.template_code,
		finish_setup=finish_setup,
		module_links=module_links,
	)


def apply_volum_resolution_to_finish_dict(
	finish_setup: dict[str, Any] | None,
	resolution: VolumAluminumModuleResolution,
) -> dict[str, Any]:
	"""Mutate finish_setup in place; return provenance metadata for payload audit."""
	finish = finish_setup if isinstance(finish_setup, dict) else {}
	previous = _read_string(finish.get(VOLUM_ALUMINUM_TRIGGER_FIELD))
	if resolution.resolved_code:
		finish[VOLUM_ALUMINUM_TRIGGER_FIELD] = resolution.resolved_code
	elif resolution.source.startswith("cleared") or resolution.source == "not_applicable":
		finish[VOLUM_ALUMINUM_TRIGGER_FIELD] = None
	return {
		"previous": previous,
		"resolved": resolution.resolved_code,
		"source": resolution.source,
		"applicable": resolution.applicable,
		"module_link_codes": list(resolution.module_link_codes),
		"blockers": list(resolution.blockers),
		"warnings": list(resolution.warnings),
	}


async def apply_volum_aluminum_module_truth_to_workspace_payload(
	db: AsyncSession,
	*,
	template_code: str,
	payload_raw: dict[str, Any],
) -> dict[str, Any]:
	"""Resolve and persist volum aluminum module template code on workspace payload."""
	finish = payload_raw.get("finish_setup")
	if not isinstance(finish, dict):
		finish = {}
		payload_raw["finish_setup"] = finish
	resolution = await resolve_volum_aluminum_module_for_template(
		db,
		template_code=template_code,
		finish_setup=finish,
	)
	audit = apply_volum_resolution_to_finish_dict(finish, resolution)
	payload_raw.setdefault("_volum_aluminum_module_truth_v1", audit)
	return audit
