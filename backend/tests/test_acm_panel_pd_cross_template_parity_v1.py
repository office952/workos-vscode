"""ACM-root PD cross-template AcmPanel parity (read-only)."""

from __future__ import annotations

import json
import uuid

import pytest
import pytest_asyncio

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from seeds.seed_tpl_acm_boxed_mounting_support_v1 import (
    TEMPLATE_CODE as ACM_TEMPLATE,
    seed_tpl_acm_boxed_mounting_support_v1,
)
from services.product_definition_builder_service import ProductDefinitionBuilderService

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

LETTERS = "TPL-VOLUMETRIC-LETTERS_v2"


def _letters_hosted_acm_payload() -> dict:
    return {
        "analysis_ready": True,
        "finish_setup": {
            "acm_panel_instance": {
                "schema": "acm_panel_component_instance_v1",
                "component_instance_id": "acm_cc_fixture",
                "association_status": "proposed",
                "technical_configuration_status": "proposed",
                "composition_status": "unconfirmed",
                "capabilities": {
                    "active": ["boxed_returns", "segmented_panels"],
                    "inactive": ["led_system"],
                },
                "geometry": {
                    "width_mm": 1000,
                    "height_mm": 350,
                    "panels": [
                        {
                            "panel_id": "panel_1",
                            "order": 1,
                            "width_mm": 1000,
                            "height_mm": 350,
                            "position": {"x_mm": 0, "y_mm": 0},
                        },
                        {
                            "panel_id": "panel_2",
                            "order": 2,
                            "width_mm": 1000,
                            "height_mm": 350,
                            "position": {"x_mm": 1000, "y_mm": 0},
                        },
                    ],
                },
            },
            "segmented_background": {
                "schema": "acm_segmented_background_v1",
                "status": "PROPOSED",
                "operator_confirmed": False,
                "assembly_id": "asm_1",
                "panels": [
                    {
                        "panel_id": "panel_1",
                        "order": 1,
                        "width_mm": 1000,
                        "height_mm": 350,
                        "position": {"x_mm": 0, "y_mm": 0},
                    },
                    {
                        "panel_id": "panel_2",
                        "order": 2,
                        "width_mm": 1000,
                        "height_mm": 350,
                        "position": {"x_mm": 1000, "y_mm": 0},
                    },
                ],
                "joints": [],
                "assembly_dimensions": {"width_mm": 2000, "height_mm": 350},
            },
        },
    }


@pytest_asyncio.fixture
async def acm_pd_db(volumetric_v2_db):
    await seed_tpl_acm_boxed_mounting_support_v1()
    return volumetric_v2_db


@pytest.mark.asyncio
async def test_acm_root_cross_template_parity_projects_assembly(acm_pd_db):
    workspace_id = str(uuid.uuid4())
    acm_pd_db.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"WS-XT-{workspace_id[:8]}",
            title="Letters-hosted AcmPanel",
            template_code=LETTERS,
            status="draft",
            payload_json=json.dumps(_letters_hosted_acm_payload()),
        )
    )
    await acm_pd_db.commit()

    preview = await ProductDefinitionBuilderService(acm_pd_db).build_preview(
        ACM_TEMPLATE,
        workspace_id=workspace_id,
    )
    assert preview is not None
    assert preview.source_context.source_payload_type == "workspace_payload"
    values = preview.canonical_values
    assert values["assembly_width_mm"] == 2000
    assert values["assembly_height_mm"] == 350
    assert values.get("acm_panel_instance", {}).get("component_instance_id") == "acm_cc_fixture"
    assert values.get("acm_panel_technical_configuration_status") == "proposed"
    assert values.get("segmented_background_proposal", {}).get("status") == "PROPOSED"

    prov = {p.key: p.detail for p in preview.provenance}
    assert prov.get("linked_workspace_template_code") == LETTERS
    assert prov.get("read_mode") == "cross_template_acm_parity"


@pytest.mark.asyncio
async def test_acm_root_mismatch_without_acm_instance_stays_template_only(acm_pd_db):
    workspace_id = str(uuid.uuid4())
    acm_pd_db.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"WS-NO-{workspace_id[:8]}",
            title="Letters without AcmPanel",
            template_code=LETTERS,
            status="draft",
            payload_json=json.dumps({"finish_setup": {"face_finish_type": "plexiglas_clear"}}),
        )
    )
    await acm_pd_db.commit()

    preview = await ProductDefinitionBuilderService(acm_pd_db).build_preview(
        ACM_TEMPLATE,
        workspace_id=workspace_id,
    )
    assert preview is not None
    assert preview.source_context.source_payload_type == "template_only"
    assert "assembly_width_mm" not in preview.canonical_values
    prov_keys = {p.key for p in preview.provenance}
    assert "read_mode" not in prov_keys
