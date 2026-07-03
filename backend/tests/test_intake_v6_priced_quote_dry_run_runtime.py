from __future__ import annotations

import json
import uuid

import pytest

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from services.intake_v6_priced_quote_dry_run_service import (
    V6_PRICED_DRY_RUN_BLOCKED,
    V6_PRICED_DRY_RUN_READY,
    build_intake_v6_priced_quote_dry_run,
)

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


def _runtime_payload() -> dict:
    return {
        "analysis_ready": True,
        "intake_request_code": "IR-RUNTIME",
        "product_binding": {"template_code": TEMPLATE},
        "svg_source": {"file_name": "letters.svg", "file_size_bytes": 2048},
        "client": {"width_mm": 1200, "height_mm": 400},
        "quote_geometry": {
            "letter_count": 5,
            "letter_perimeter_m": 12.5,
            "letter_face_area_m2": 1.2,
            "face_area_m2": 1.2,
        },
        "finish_setup": {
            "face_finish_type": "plexiglas_clear",
            "return_depth_mm": 60,
            "return_finish_type": "ral",
            "volum_aluminum_module_template_code": "TPL-VOLUM-ALUMINIU_v1",
            "backing_mode": "forex_10_no_bevel",
            "mounting_system": "direct_wall",
            "mounting_template_enabled": False,
            "lighting_system_type": "front_lit",
            "illuminated": True,
            "led_module_count": 20,
            "selected_psu_watts": 60,
        },
    }


async def _seed_workspace(db, payload: dict) -> str:
    workspace_id = str(uuid.uuid4())
    db.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"IV6-RUNTIME-{workspace_id[:8]}",
            title="Runtime dry-run test workspace",
            template_code=TEMPLATE,
            status="draft",
            payload_json=json.dumps(payload),
        )
    )
    await db.commit()
    return workspace_id


@pytest.mark.asyncio
async def test_runtime_dry_run_uses_real_commercial_classifier_without_type_error(volumetric_v2_db) -> None:
    workspace_id = await _seed_workspace(volumetric_v2_db, _runtime_payload())

    result = await build_intake_v6_priced_quote_dry_run(volumetric_v2_db, workspace_id)

    assert result["pricing_status"] in {V6_PRICED_DRY_RUN_READY, V6_PRICED_DRY_RUN_BLOCKED}
    assert result["pricing_source"] == "intake_v6_backend_priced_dry_run"
    assert result["commercial_proposal_trace"]["available"] is True
    assert isinstance(result["commercial_line_items"], list)
    assert result["dry_run_only"] is True


@pytest.mark.asyncio
async def test_runtime_dry_run_missing_payload_returns_structured_blocked_result(volumetric_v2_db) -> None:
    workspace_id = await _seed_workspace(
        volumetric_v2_db,
        {"intake_request_code": "IR-RUNTIME-MISSING", "product_binding": {"template_code": TEMPLATE}},
    )

    result = await build_intake_v6_priced_quote_dry_run(volumetric_v2_db, workspace_id)

    assert result["pricing_status"] == V6_PRICED_DRY_RUN_BLOCKED
    assert isinstance(result["blockers"], list)
    assert result["commercial_totals"]["total_gross"] is None
    assert result["dry_run_only"] is True


@pytest.mark.asyncio
async def test_runtime_dry_run_returns_ready_or_structured_blocked_for_valid_pricing_input(volumetric_v2_db) -> None:
    workspace_id = await _seed_workspace(volumetric_v2_db, _runtime_payload())

    result = await build_intake_v6_priced_quote_dry_run(
        volumetric_v2_db,
        workspace_id,
        pricing_mode="write_priced_quote",
    )

    assert result["pricing_status"] in {V6_PRICED_DRY_RUN_READY, V6_PRICED_DRY_RUN_BLOCKED}
    assert result["persistence"] == {
        "creates_quote": False,
        "updates_quote": False,
        "writes_quote_totals": False,
        "creates_quote_snapshot": False,
        "creates_order": False,
    }
    if result["pricing_status"] == V6_PRICED_DRY_RUN_BLOCKED:
        assert result["blockers"]
    else:
        assert result["commercial_totals"]["total_gross"] > 0