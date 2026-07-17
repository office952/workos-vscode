"""Owner read-only Product / Price / Tasking proof — volumetric letters."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
import pytest_asyncio

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from services.owner_readonly_volumetric_proof_service import build_owner_readonly_volumetric_proof
from services.product_process_resolve_input_adapter import PROCESS_GRAPH_SOURCE_MODULAR
from tests.test_product_aggregate_volumetric_v2 import TEMPLATE_CODE, _seed_volumetric_v2_fixture

METAL_SOLUTION = {
    "kind": "product_system_template",
    "template_code": "TPL-METAL-PREMOUNT-STRUCTURE_v1",
    "configuration": {"bar_material": "steel", "bar_count": 2},
}


def _payload(*, cable: float = 12.5) -> dict:
    return {
        "schema_version": "1.0.0",
        "product_binding": {"template_code": TEMPLATE_CODE},
        "svg_source": {"file_name": "owner-proof.svg", "file_size_bytes": 1200},
        "svg_analysis_json": {
            "schemaVersion": "1.10.0",
            "geometry": {
                "letter_perimeter_m": 8.2,
                "real_letters_count": 5,
                "letter_count": 5,
                "letter_face_area_m2": 0.45,
            },
        },
        "quote_geometry": {
            "width_mm": 1200,
            "height_mm": 400,
            "letter_count": 5,
            "letter_perimeter_m": 8.2,
            "letter_face_area_m2": 0.45,
            "real_letters_count": 5,
            "confirmed": True,
        },
        "finish_setup": {
            "face_finish_type": "oracal_651",
            "return_finish_type": "oracal_wrapped",
            "return_depth_mm": 60,
            "illuminated": True,
            "lighting_system_type": "led_modules",
            "mounting_system": "steel_bars",
            "mounting_solution": METAL_SOLUTION,
            "mains_cable_length_m": cable,
            "service_screw_finish": "NATURAL",
            "mounting_template_enabled": False,
            "confirmed": True,
        },
        "product_composition_confirmed": {"confirmed": True},
    }


@pytest_asyncio.fixture
async def volumetric_v2_db(db_session):
    await _seed_volumetric_v2_fixture(db_session)
    return db_session


async def _seed_workspace(db, *, cable: float = 12.5) -> str:
    workspace_id = str(uuid.uuid4())
    db.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"IV6-OWNER-PROOF-{workspace_id[:8]}",
            title="Owner readonly proof",
            template_code=TEMPLATE_CODE,
            status="ready_for_quote_preview",
            payload_json=json.dumps(_payload(cable=cable)),
        )
    )
    await db.commit()
    return workspace_id


@pytest.mark.asyncio
async def test_owner_proof_full_chain_metal_bars(volumetric_v2_db):
    ws = await _seed_workspace(volumetric_v2_db, cable=12.5)
    proof = await build_owner_readonly_volumetric_proof(
        volumetric_v2_db,
        template_code=TEMPLATE_CODE,
        workspace_id=ws,
    )
    assert proof is not None
    assert proof.safety.no_write is True
    assert proof.safety.no_task_materialization is True
    assert proof.safety.no_new_tasking_system is True
    assert proof.safety.resolver_is_not_task_engine is True

    assert proof.intake_selection.mains_cable_length_m == 12.5
    assert proof.product_definition.canonical_values.get("mains_cable_length_m") == 12.5
    assert proof.product_definition.canonical_values.get("return_finish_type") == "oracal_wrapped"

    assert proof.process_graph.process_graph_source == PROCESS_GRAPH_SOURCE_MODULAR
    assert proof.process_graph.process_count > 0
    assert proof.process_graph.edge_count > 0
    assert "APPLY_CANT_VINYL" in proof.task_rules_projection.task_names
    assert "INSTALL_CABLE_CHANNEL" in proof.task_rules_projection.task_names
    assert proof.task_rules_projection.authority == "existing_task_rules"
    assert proof.task_rules_projection.depends_on_preserved is True

    assert proof.live_materials.wire_supply.present is True
    assert proof.live_materials.wire_supply.quantity == 12.5
    assert proof.live_materials.wire_supply.quantity_source == "typed_mains_cable_length_m"
    assert proof.live_materials.wire_supply.material_code == "MAT-CABLU-MYYUP-2X15"
    assert proof.live_materials.cable_channel_commercial_guarded is True

    assert proof.execution_preview_4c.present is True
    assert proof.execution_preview_4c.no_write is True
    assert proof.execution_preview_4c.candidate_count > 0
    assert proof.execution_preview_4c.process_depends_on_edges > 0

    assert proof.chain_ok is True
    assert proof.verification_path.proof_api.endswith(f"workspace_id={ws}")


@pytest.mark.asyncio
async def test_owner_proof_cable_25_vs_2_5_changes_materials_not_task_set(volumetric_v2_db):
    ws_low = await _seed_workspace(volumetric_v2_db, cable=2.5)
    ws_high = await _seed_workspace(volumetric_v2_db, cable=25.0)
    low = await build_owner_readonly_volumetric_proof(
        volumetric_v2_db, template_code=TEMPLATE_CODE, workspace_id=ws_low
    )
    high = await build_owner_readonly_volumetric_proof(
        volumetric_v2_db, template_code=TEMPLATE_CODE, workspace_id=ws_high
    )
    assert low is not None and high is not None
    assert low.task_rules_projection.task_names == high.task_rules_projection.task_names
    assert low.live_materials.wire_supply.quantity == 2.5
    assert high.live_materials.wire_supply.quantity == 25.0


@pytest.mark.asyncio
async def test_owner_proof_rejects_unknown_workspace(volumetric_v2_db):
    proof = await build_owner_readonly_volumetric_proof(
        volumetric_v2_db,
        template_code=TEMPLATE_CODE,
        workspace_id=str(uuid.uuid4()),
    )
    assert proof is None


def test_owner_proof_service_ast_no_writes():
    root = Path(__file__).resolve().parents[1]
    text = (root / "services/owner_readonly_volumetric_proof_service.py").read_text(encoding="utf-8")
    assert "session.commit" not in text
    assert "db.add(" not in text
    assert "materialize_tasks" not in text
    assert "ExecutionPlan(" not in text
