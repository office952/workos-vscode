"""W2-PREREQUISITE-VOLUM-TRUTH — volum aluminum module technical truth."""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.intake_v4 import IntakeV4FinishSetup
from services.intake_v6_volum_aluminum_module_truth_service import (
	VOLUMETRIC_LETTERS_TEMPLATE,
	resolve_volum_aluminum_module_template_code,
	resolve_volum_aluminum_module_for_template,
	is_volum_aluminum_module_applicable,
	apply_volum_resolution_to_finish_dict,
)
from services.product_definition_builder_service import ProductDefinitionBuilderService

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

VOLUM_AL = "TPL-VOLUM-ALUMINIU_v1"


class _Link:
	def __init__(self, code: str, trigger: str = "volum_aluminum_module_template_code") -> None:
		self.module_template_code = code
		self.trigger_field = trigger


def _finish(**overrides) -> dict:
	data = {
		"return_depth_mm": 60,
		"return_finish_type": "white_aluminum",
		"volum_aluminum_module_template_code": None,
	}
	data.update(overrides)
	return data


def test_not_applicable_for_inactive_return_finish() -> None:
	assert is_volum_aluminum_module_applicable(
		template_code=VOLUMETRIC_LETTERS_TEMPLATE,
		finish_setup=_finish(return_finish_type="none"),
	) is False


def test_applicable_for_volumetric_letters_with_cant() -> None:
	assert is_volum_aluminum_module_applicable(
		template_code=VOLUMETRIC_LETTERS_TEMPLATE,
		finish_setup=_finish(),
	) is True


def test_unique_product_system_link_resolves_deterministically() -> None:
	res = resolve_volum_aluminum_module_template_code(
		template_code=VOLUMETRIC_LETTERS_TEMPLATE,
		finish_setup=_finish(),
		module_links=[_Link(VOLUM_AL)],
	)
	assert res.resolved_code == VOLUM_AL
	assert res.source == "product_system_unique_link"


def test_multiple_links_require_operator_selection() -> None:
	res = resolve_volum_aluminum_module_template_code(
		template_code=VOLUMETRIC_LETTERS_TEMPLATE,
		finish_setup=_finish(),
		module_links=[_Link("TPL-VOLUM-ALUMINIU_v1"), _Link("TPL-VOLUM-ALUMINIU_v2")],
	)
	assert res.resolved_code is None
	assert res.source == "missing_requires_operator"
	assert "volum_aluminum_module_selection_required" in res.blockers


def test_stale_incompatible_explicit_code_is_cleared() -> None:
	finish = _finish(volum_aluminum_module_template_code="TPL-UNKNOWN_v9")
	res = resolve_volum_aluminum_module_template_code(
		template_code=VOLUMETRIC_LETTERS_TEMPLATE,
		finish_setup=finish,
		module_links=[_Link(VOLUM_AL)],
	)
	assert res.resolved_code is None
	assert res.source == "cleared_stale_incompatible"
	audit = apply_volum_resolution_to_finish_dict(finish, res)
	assert finish["volum_aluminum_module_template_code"] is None
	assert audit["previous"] == "TPL-UNKNOWN_v9"


def test_not_applicable_clears_persisted_code() -> None:
	finish = _finish(volum_aluminum_module_template_code=VOLUM_AL, return_finish_type="none")
	res = resolve_volum_aluminum_module_template_code(
		template_code=VOLUMETRIC_LETTERS_TEMPLATE,
		finish_setup=finish,
		module_links=[_Link(VOLUM_AL)],
	)
	assert res.source == "cleared_not_applicable"
	apply_volum_resolution_to_finish_dict(finish, res)
	assert finish["volum_aluminum_module_template_code"] is None


@pytest.mark.asyncio
async def test_product_definition_consumes_resolved_volum_truth(volumetric_v2_db: AsyncSession) -> None:
	from models.intake_v6_workspace import IntakeV6WorkspaceRecord
	from services.intake_v6_workspace_service import _json_loads
	import json

	workspace_id = "volum-truth-test-ws"
	payload = {
		"product_binding": {"template_code": VOLUMETRIC_LETTERS_TEMPLATE},
		"client": {"width_mm": 1000, "height_mm": 600},
		"quote_geometry": {
			"letter_count": 5,
			"letter_perimeter_m": 12.0,
			"letter_face_area_m2": 1.0,
			"width_mm": 1000,
			"height_mm": 600,
		},
		"finish_setup": _finish(
			face_finish_type="plexiglas_clear",
			backing_mode="closed_back",
			mounting_system="direct_wall",
		),
	}
	record = IntakeV6WorkspaceRecord(
		id=workspace_id,
		workspace_code="IV6-VOLUM-TEST",
		title="Volum truth test",
		template_code=VOLUMETRIC_LETTERS_TEMPLATE,
		payload_json=json.dumps(payload),
	)
	volumetric_v2_db.add(record)
	await volumetric_v2_db.commit()

	from services.intake_v6_volum_aluminum_module_truth_service import (
		apply_volum_aluminum_module_truth_to_workspace_payload,
	)

	payload_raw = _json_loads(record.payload_json, {})
	await apply_volum_aluminum_module_truth_to_workspace_payload(
		volumetric_v2_db,
		template_code=VOLUMETRIC_LETTERS_TEMPLATE,
		payload_raw=payload_raw,
	)
	assert payload_raw["finish_setup"]["volum_aluminum_module_template_code"] == VOLUM_AL
	record.payload_json = json.dumps(payload_raw)
	await volumetric_v2_db.commit()

	pd = await ProductDefinitionBuilderService(volumetric_v2_db).build_preview(
		VOLUMETRIC_LETTERS_TEMPLATE,
		workspace_id=workspace_id,
	)
	assert pd is not None
	assert "volum_aluminum_module_template_code" not in pd.validation.missing_required_fields
	graph = pd.composition
	assert graph is not None
	assert any(node.node_role == "volum_aluminum" for node in graph.nodes)


@pytest.mark.asyncio
async def test_canonical_snapshot_preserves_volum_graph_when_truth_present(volumetric_v2_db: AsyncSession) -> None:
	from models.intake_v6_workspace import IntakeV6WorkspaceRecord
	from services.quote_snapshot_v2_service import QuoteSnapshotV2Service
	import json

	workspace_id = "volum-truth-snapshot-ws"
	payload = {
		"product_binding": {"template_code": VOLUMETRIC_LETTERS_TEMPLATE},
		"client": {"width_mm": 1000, "height_mm": 600},
		"quote_geometry": {
			"letter_count": 5,
			"letter_perimeter_m": 12.0,
			"letter_face_area_m2": 1.0,
		},
		"finish_setup": _finish(volum_aluminum_module_template_code=VOLUM_AL),
	}
	record = IntakeV6WorkspaceRecord(
		id=workspace_id,
		workspace_code="IV6-VOLUM-SNAP",
		title="Volum snapshot test",
		template_code=VOLUMETRIC_LETTERS_TEMPLATE,
		payload_json=json.dumps(payload),
	)
	volumetric_v2_db.add(record)
	await volumetric_v2_db.commit()

	snapshot = await QuoteSnapshotV2Service(volumetric_v2_db).build_preview(
		VOLUMETRIC_LETTERS_TEMPLATE,
		workspace_id=workspace_id,
	)
	assert snapshot is not None
	graph = snapshot.product_aggregate_snapshot.composition_graph if snapshot.product_aggregate_snapshot else None
	assert graph is not None
	assert any(node.node_role == "volum_aluminum" for node in graph.nodes)
