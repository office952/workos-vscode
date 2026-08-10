"""Post-freeze commercial VAT rate resolver.

Owner locks (WORKOS_VAT_SNAPSHOT_BOUNDARY_INTEGRITY_V1):
  FROZEN_VAT_SOURCE_CANDIDATE = notes.commercial_adjustment_trace.vat_percent
  LIVE_SETTINGS_VAT_AFTER_FREEZE = FORBIDDEN
  MISSING_FROZEN_VAT = FAIL_CLOSED / provenance-incomplete
  NOT guess (never invent % from quote.vat amount; never hardcode DEFAULT_VAT_PCT)
"""

from __future__ import annotations

from typing import Any, NamedTuple

from schemas.commercial_price_proposal import CommercialProductBreakdown

FROZEN_VAT_PROVENANCE_INCOMPLETE = "FROZEN_VAT_PROVENANCE_INCOMPLETE"
PROVENANCE_NOTES_TRACE = "notes.commercial_adjustment_trace.vat_percent"
PROVENANCE_NOTES_PRICED_WRITE = (
	"notes.intake_v6_linkage_v1.intake_v6_priced_quote_write_v1."
	"commercial_adjustment_trace.vat_percent"
)
PROVENANCE_CPP_BREAKDOWN = (
	"commercial_price_proposal_snapshot.commercial_product_breakdown.vat_rate_percent"
)

INTAKE_V6_LINKAGE_JSON_KEY = "intake_v6_linkage_v1"
PRICED_QUOTE_WRITE_KEY = "intake_v6_priced_quote_write_v1"


class FrozenVatResolution(NamedTuple):
	vat_rate: float
	provenance: str


class FrozenVatMissingError(Exception):
	"""Frozen commercial artifact has no recoverable VAT rate."""

	def __init__(self, message: str | None = None) -> None:
		self.code = FROZEN_VAT_PROVENANCE_INCOMPLETE
		super().__init__(
			message
			or (
				"Frozen commercial VAT rate provenance incomplete — "
				"notes.commercial_adjustment_trace.vat_percent missing "
				"(live Settings VAT forbidden after freeze)."
			)
		)


def _as_valid_vat_percent(raw: Any) -> float | None:
	if raw is None:
		return None
	try:
		value = float(raw)
	except (TypeError, ValueError):
		return None
	if value < 0.0 or value > 100.0:
		return None
	return value


def _notes_dict(notes: dict[str, Any] | None) -> dict[str, Any]:
	return notes if isinstance(notes, dict) else {}


def _vat_from_adjustment_trace(trace: Any) -> float | None:
	if not isinstance(trace, dict):
		return None
	return _as_valid_vat_percent(trace.get("vat_percent"))


def resolve_frozen_commercial_vat_rate(
	*,
	notes: dict[str, Any] | None,
	cpp: Any | None = None,
) -> FrozenVatResolution:
	"""Resolve frozen VAT % for post-freeze offer / pricing-review.

	Priority:
	1. notes.commercial_adjustment_trace.vat_percent (Owner primary)
	2. nested priced-write commercial_adjustment_trace.vat_percent
	3. CPP commercial_product_breakdown.vat_rate_percent (supplementary)
	4. FAIL_CLOSED
	"""
	notes_obj = _notes_dict(notes)

	top_trace = notes_obj.get("commercial_adjustment_trace")
	top_rate = _vat_from_adjustment_trace(top_trace)
	if top_rate is not None:
		return FrozenVatResolution(vat_rate=top_rate, provenance=PROVENANCE_NOTES_TRACE)

	linkage = notes_obj.get(INTAKE_V6_LINKAGE_JSON_KEY)
	if isinstance(linkage, dict):
		priced_write = linkage.get(PRICED_QUOTE_WRITE_KEY)
		if isinstance(priced_write, dict):
			nested_rate = _vat_from_adjustment_trace(
				priced_write.get("commercial_adjustment_trace")
			)
			if nested_rate is not None:
				return FrozenVatResolution(
					vat_rate=nested_rate,
					provenance=PROVENANCE_NOTES_PRICED_WRITE,
				)

	breakdown = getattr(cpp, "commercial_product_breakdown", None) if cpp is not None else None
	cpp_rate = _as_valid_vat_percent(
		getattr(breakdown, "vat_rate_percent", None) if breakdown is not None else None
	)
	if cpp_rate is not None:
		return FrozenVatResolution(vat_rate=cpp_rate, provenance=PROVENANCE_CPP_BREAKDOWN)

	raise FrozenVatMissingError()


def stamp_commercial_adjustment_trace_vat(
	notes: dict[str, Any] | None,
	*,
	vat_percent: float,
	currency: str | None = None,
) -> dict[str, Any]:
	"""Ensure notes carry the frozen VAT % used for authoritative totals."""
	notes_obj = dict(_notes_dict(notes))
	existing = notes_obj.get("commercial_adjustment_trace")
	trace = dict(existing) if isinstance(existing, dict) else {}
	trace["vat_percent"] = float(vat_percent)
	if currency is not None:
		trace["currency"] = currency
	notes_obj["commercial_adjustment_trace"] = trace
	return notes_obj


def stamp_cpp_supplementary_vat_rate(
	cpp: Any,
	*,
	vat_percent: float,
	policy_source: str = "company_commercial_settings.default_vat_pct",
) -> Any:
	"""Stamp existing CPP breakdown VAT fields on NEW freezes only (not schema).

	Notes remain the Owner primary authority; this is supplementary self-containment.
	"""
	if cpp is None:
		return cpp
	rate = _as_valid_vat_percent(vat_percent)
	if rate is None:
		return cpp
	breakdown = getattr(cpp, "commercial_product_breakdown", None)
	if breakdown is None:
		breakdown = CommercialProductBreakdown(
			vat_rate_percent=rate,
			vat_policy_source=policy_source,
		)
	else:
		breakdown = breakdown.model_copy(
			update={
				"vat_rate_percent": rate,
				"vat_policy_source": policy_source,
			}
		)
	if hasattr(cpp, "model_copy"):
		return cpp.model_copy(update={"commercial_product_breakdown": breakdown})
	# Mutable fallback for non-pydantic test doubles
	try:
		cpp.commercial_product_breakdown = breakdown
	except Exception:
		pass
	return cpp
