"""TPL-VOLUMETRIC-LETTERS operation keys alignment pack — read-only contract tests."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import func, select

from schemas.intake_v4 import PILOT_V4_TEMPLATE_CODE
from seeds.seed_build4_templates import seed_build4_templates
from services.intake_v4_task_generation_dry_run_service import (
    build_intake_v4_task_generation_dry_run,
)
from services.tpl_volumetric_operation_keys_service import (
    DOSSIER_OPERATION_KEYS,
    HANDOFF_GROUP_CANONICAL_KEYS,
    TPL_VOLUMETRIC_OPERATION_KEYS,
    evaluate_handoff_group_alignment,
    enrich_task_candidate_alignment,
    get_mapping_catalog,
    list_critical_operation_keys,
    resolve_canonical_keys_from_catalog,
    summarize_template_operation_alignment,
)

_DEFAULT_PRICING = {
    "MAT-ORACAL-651": {"unit_cost": 5.0, "currency": "EUR", "source": "inventory_materials"},
    "MAT-ACP-FATA-LITERE": {"unit_cost": 10.0, "currency": "EUR", "source": "inventory_materials"},
    "MAT-SPATE-PVC-LITERE": {"unit_cost": 16.0, "currency": "EUR", "source": "inventory_materials"},
    "MAT-PROFIL-LATERAL-LITERE-60MM": {"unit_cost": 3.0, "currency": "EUR", "source": "inventory_materials"},
    "MAT-LED-MODULE": {"unit_cost": 0.5, "currency": "EUR", "source": "inventory_materials"},
    "MAT-LED-PSU-12V-100W": {"unit_cost": 16.0, "currency": "EUR", "source": "inventory_materials"},
}


@pytest.fixture
def seeded_db(db_fixture):
    asyncio.get_event_loop().run_until_complete(seed_build4_templates())
    return db_fixture


def _complete_payload(*, confirmed: bool = True, illuminated: bool = False) -> dict:
    nesting = {
        "sheets": [
            {
                "configId": "sheet_1300x900",
                "sheetsUsed": 2,
                "usedSheetAreaSqm": 2.34,
                "placedItemsCount": 2,
                "unplacedItemsCount": 0,
                "placements": [
                    {
                        "partId": "letter-face-a",
                        "sourceLayerName": "litere-volumetrice-1",
                        "placedWidthMm": 800,
                        "placedHeightMm": 500,
                    },
                    {
                        "partId": "letter-back-a",
                        "sourceLayerName": "litere-backing",
                        "placedWidthMm": 400,
                        "placedHeightMm": 400,
                    },
                ],
            }
        ],
        "rolls": [
            {
                "rollWidthMm": 1000,
                "jobs": [{"usedRollAreaSqm": 8.0, "placedItemsCount": 3, "unplacedItemsCount": 0}],
            }
        ],
    }
    return {
        "schema_version": "1.0.0",
        "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
        "svg_source": {
            "file_name": "test.svg",
            "file_size_bytes": 100,
            "file_hash": "a" * 64,
            "upload_status": "analyzed",
        },
        "svg_analysis_json": {
            "schemaVersion": "1.10.0",
            "nesting": nesting,
            "parts": {
                "items": [
                    {"id": "letter-face-a", "source": {"layerName": "litere-volumetrice-1"}},
                    {
                        "id": "letter-back-a",
                        "derivedPartKind": "back-cover-plate",
                        "source": {"layerName": "litere-backing"},
                    },
                ]
            },
            "layers": [
                {
                    "id": "litere-volumetrice-1",
                    "name": "litere-volumetrice-1",
                    "perimeterMl": 10.0,
                    "filledAreaSqm": 1.5,
                }
            ],
        },
        "quote_geometry": {
            "letter_perimeter_m": 10.0,
            "face_area_m2": 1.5,
            "backing_area_m2": 1.2,
            "return_material_perimeter_ml": 10.0,
        },
        "path_geometry_summary": {
            "parse_status": "parsed",
            "face_area_m2": 1.5,
            "backing_area_m2": 1.2,
            "return_material_perimeter_ml": 10.0,
        },
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "litere-volumetrice-1",
                    "layer_name": "litere-volumetrice-1",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                },
                {
                    "layer_key": "litere-backing",
                    "layer_name": "litere-backing",
                    "confirmed_role": "backing",
                    "confirmation_state": "confirmed",
                },
            ],
        },
        "finish_setup": {
            "face_finish_type": "oracal_651",
            "return_finish_type": "oracal_wrapped",
            "return_depth_mm": 60,
            "illuminated": illuminated,
            "face_vinyl_roll_width_mm": 1000,
            "letter_group_finishes": [
                {
                    "group_key": "litere-volumetrice-1",
                    "layer_name": "litere-volumetrice-1",
                    "face_finish_type": "oracal_651",
                    "return_finish_type": "oracal_wrapped",
                    "return_depth_mm": 60,
                    "face_vinyl_roll_width_mm": 1000,
                }
            ],
            "confirmed": confirmed,
            **({"psu_configuration": [100], "lighting_system_type": "led_modules"} if illuminated else {}),
        },
    }


async def _run_dry_run(workspace_id: str, payload_dict: dict):
    from services.intake_v4_workspace_service import _parse_payload

    payload = _parse_payload(payload_dict)
    with patch(
        "services.inventory_materials_admin_service.load_material_pricing_dict",
        new_callable=AsyncMock,
    ) as mock_pricing:
        mock_pricing.return_value = _DEFAULT_PRICING
        return await build_intake_v4_task_generation_dry_run(
            None,  # type: ignore[arg-type]
            workspace_id,
            payload_dict,
            payload,
        )


class TestCanonicalRegistry:
    def test_registry_contains_critical_operations(self):
        critical = list_critical_operation_keys()
        for key in (
            "preflight_svg_review",
            "cnc_face_cutting",
            "cnc_backing_cutting",
            "return_side_bonding",
            "letter_assembly",
        ):
            assert key in critical
            assert key in TPL_VOLUMETRIC_OPERATION_KEYS

    def test_each_operation_has_label_station_role(self):
        for key, spec in TPL_VOLUMETRIC_OPERATION_KEYS.items():
            assert spec.label, f"{key} missing label"
            assert spec.station_hint, f"{key} missing station_hint"
            assert spec.role_hint, f"{key} missing role_hint"

    def test_dossier_keys_referenced_in_registry(self):
        for key in DOSSIER_OPERATION_KEYS:
            mapped = [
                s.dossier_operation_key
                for s in TPL_VOLUMETRIC_OPERATION_KEYS.values()
                if s.dossier_operation_key == key
            ]
            assert mapped, f"dossier key {key} not referenced in canonical registry"

    def test_mapping_catalog_export(self):
        catalog = get_mapping_catalog()
        assert catalog["template_code"] == "TPL-VOLUMETRIC-LETTERS"
        assert len(catalog["mapping_table"]) >= len(HANDOFF_GROUP_CANONICAL_KEYS)


class TestHandoffGroupMapping:
    def test_cnc_cutting_alignment_with_material_jobs(self):
        keys, info = evaluate_handoff_group_alignment(
            "cnc_cutting",
            active=True,
            active_material_job_keys={"face_plexiglas_cutting", "forex_backing_cutting"},
        )
        assert "cnc_face_cutting" in keys
        assert "cnc_backing_cutting" in keys
        assert info.status in ("aligned", "partial")

    def test_vinyl_print_finish_mapping(self):
        keys, info = evaluate_handoff_group_alignment(
            "vinyl_print_finish",
            active=True,
            active_material_job_keys={"oracal_vinyl_cutting"},
        )
        assert "vinyl_cutting" in keys
        assert info.status in ("aligned", "partial")

    def test_return_forming_and_bonding(self):
        forming_keys, _ = evaluate_handoff_group_alignment(
            "return_forming",
            active=True,
            active_material_job_keys={"return_profile_material"},
        )
        assert "return_side_forming" in forming_keys

        bonding_keys, _ = evaluate_handoff_group_alignment(
            "return_bonding",
            active=True,
            active_material_job_keys={"return_profile_material", "face_plexiglas_cutting"},
        )
        assert "return_side_bonding" in bonding_keys

    def test_led_electrical_mapping(self):
        keys, _ = evaluate_handoff_group_alignment(
            "led_electrical",
            active=True,
            active_material_job_keys={"led_modules_install", "psu_electrical"},
        )
        assert "led_module_install" in keys
        assert "electrical_wiring" in keys

    def test_inactive_group_not_applicable(self):
        _, info = evaluate_handoff_group_alignment("assembly", active=False)
        assert info.status == "not_applicable"

    def test_assembly_partial_when_active(self):
        _, info = evaluate_handoff_group_alignment(
            "assembly",
            active=True,
            active_material_job_keys={"face_plexiglas_cutting", "forex_backing_cutting"},
        )
        assert info.status == "partial"
        assert info.provisional


class TestTaskCandidateAlignment:
    def test_cnc_face_cutting_aligned_not_provisional(self):
        fields = enrich_task_candidate_alignment(
            task_key="cnc_face_cutting",
            operation_key="face_cnc_cut",
            provisional=False,
        )
        assert fields["canonical_operation_key"] == "cnc_face_cutting"
        assert fields["template_alignment_status"] == "aligned"
        assert fields["dossier_backed"] is True
        assert fields["provisional"] is False

    def test_assembly_stays_provisional(self):
        fields = enrich_task_candidate_alignment(
            task_key="letter_assembly",
            operation_key="assembly_letters",
            provisional=True,
        )
        assert fields["canonical_operation_key"] == "letter_assembly"
        assert fields["template_alignment_status"] == "partial"
        assert fields["provisional"] is True
        assert fields["provisional_reason"]

    def test_mounting_missing_when_no_data(self):
        spec = TPL_VOLUMETRIC_OPERATION_KEYS["mounting_structure_preparation"]
        assert spec.requires_mounting_data
        assert spec.can_generate_task_candidate is False


class TestDryRunIntegration:
    @pytest.mark.asyncio
    async def test_dry_run_includes_canonical_operation_key(self):
        result = await _run_dry_run("ws-align-1", _complete_payload())
        cnc = next(c for c in result.task_candidates if c.task_key == "cnc_face_cutting")
        assert cnc.canonical_operation_key == "cnc_face_cutting"
        assert cnc.template_alignment_status == "aligned"
        assert cnc.future_execution_task_type == "cnc_routing"

    @pytest.mark.asyncio
    async def test_dry_run_reduces_provisional_for_confirmed_ops(self):
        result = await _run_dry_run("ws-align-2", _complete_payload())
        confirmed = [c for c in result.task_candidates if c.task_key == "cnc_face_cutting"]
        assert confirmed
        assert confirmed[0].provisional is False

    @pytest.mark.asyncio
    async def test_dry_run_keeps_provisional_for_assembly(self):
        result = await _run_dry_run("ws-align-3", _complete_payload())
        assembly = next(c for c in result.task_candidates if c.task_key == "letter_assembly")
        assert assembly.provisional is True
        assert assembly.provisional_reason

    @pytest.mark.asyncio
    async def test_dry_run_summary_includes_alignment(self):
        result = await _run_dry_run("ws-align-4", _complete_payload())
        alignment = result.summary.get("template_operation_alignment") or {}
        assert "aligned_count" in alignment
        assert "partial_count" in alignment
        assert alignment.get("blocks_real_task_generation") is True

    @pytest.mark.asyncio
    async def test_led_tasks_canonical_keys(self):
        result = await _run_dry_run("ws-align-5", _complete_payload(illuminated=True))
        led = next(c for c in result.task_candidates if c.task_key == "led_module_install")
        assert led.canonical_operation_key == "led_module_install"
        wiring = next(c for c in result.task_candidates if c.task_key == "psu_electrical_wiring")
        assert wiring.canonical_operation_key == "electrical_wiring"


class TestReadinessAlignmentSummary:
    def test_combined_catalog_cnc_code_resolves_all_canonical_operations(self):
        keys = resolve_canonical_keys_from_catalog("face_and_backing_cnc_cut")
        assert "cnc_face_cutting" in keys
        assert "cnc_backing_cutting" in keys

    def test_critical_partial_blocks_real_generation(self):
        summary = summarize_template_operation_alignment(
            task_candidates=[
                {
                    "task_key": "letter_assembly",
                    "canonical_operation_key": "letter_assembly",
                    "template_alignment_status": "partial",
                    "provisional": True,
                    "critical_for_execution": True,
                }
            ],
        )
        assert summary.blocks_real_task_generation is True
        assert "letter_assembly" in summary.provisional_critical_tasks

    def test_aligned_non_critical_does_not_add_critical_missing(self):
        summary = summarize_template_operation_alignment(
            handoff_groups=[
                {"template_alignment": {"status": "aligned"}},
            ],
            task_candidates=[
                {
                    "task_key": "cnc_face_cutting",
                    "canonical_operation_key": "cnc_face_cutting",
                    "template_alignment_status": "aligned",
                    "provisional": False,
                }
            ],
        )
        assert summary.critical_missing_count == 0


class TestNoExecutionPlanWrites:
    @pytest.mark.asyncio
    async def test_dry_run_does_not_create_execution_plan(self, seeded_db):
        from models.execution_plan import ExecutionPlan

        await _run_dry_run("ws-no-exec", _complete_payload())
        async with seeded_db.session_maker() as session:
            count = await session.scalar(select(func.count()).select_from(ExecutionPlan))
        assert count == 0

    @pytest.mark.asyncio
    async def test_dry_run_flags_unchanged(self):
        result = await _run_dry_run("ws-flags", _complete_payload())
        assert result.creates_execution_tasks is False
        assert result.can_generate_tasks is False
        assert result.stock_consumption is False
