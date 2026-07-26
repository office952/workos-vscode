"""CPP 7G prefers ProductAggregate commercial measurements (Letters slice)."""

from __future__ import annotations

import json
import uuid

import pytest
import pytest_asyncio

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.product_aggregate_service import ProductAggregateService

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


def _quote_input() -> dict:
    return {
        "analysis_ready": True,
        "svg_source": {"file_name": "letters-slice.svg"},
        "client": {"width_mm": 1200, "height_mm": 400},
        "quote_geometry": {
            "letter_count": 5,
            "letter_perimeter_m": 12.5,
            "letter_face_area_m2": 1.2,
        },
        "finish_setup": {
            "face_finish_type": "plexiglas_clear",
            "return_depth_mm": 60,
            "return_finish_type": "ral",
            "volum_aluminum_module_template_code": "TPL-VOLUM-ALUMINIU_v1",
            "backing_mode": "closed_back",
            "mounting_system": "direct_wall",
            "lighting_system_type": "front_lit",
            "illuminated": True,
            "led_module_count": 24,
            "letter_led_module_count": 24,
            "selected_psu_watts": 100,
            "mounting_template_enabled": True,
            "mounting_template_area_m2": 2.5,
            "mounting_template_material_type": "forex",
            "letter_group_finishes": [{"group_key": "default", "confirmed": True}],
        },
    }


@pytest_asyncio.fixture
async def cpp_service(volumetric_v2_db):
    yield CommercialPriceProposalService(volumetric_v2_db)


@pytest.mark.asyncio
async def test_aggregate_emits_non_monetary_measurements(volumetric_v2_db, cpp_service):
    workspace_id = str(uuid.uuid4())
    volumetric_v2_db.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"WS-LCM-{workspace_id[:8]}",
            title="Letters commercial measurement fixture",
            template_code=TEMPLATE,
            payload_json=json.dumps(_quote_input()),
            status="draft",
        )
    )
    await volumetric_v2_db.commit()

    aggregate = await ProductAggregateService(volumetric_v2_db).build_for_workspace(
        TEMPLATE, workspace_id
    )
    assert aggregate is not None
    bundle = aggregate.commercial_measurements
    assert bundle is not None
    assert bundle.contract_version == "letters_commercial_measurement_v1"
    face = next(m for m in bundle.measurements if m.line_code == "debitare_fata")
    assert face.quantity == 12.5
    assert face.unit == "ml"
    dumped = bundle.model_dump()
    blob = json.dumps(dumped)
    assert "unit_price" not in blob
    assert "planned_minutes" not in blob
    assert "actual_minutes" not in blob

    preview = await cpp_service.build_preview(TEMPLATE, workspace_id=workspace_id)
    assert preview is not None
    face_line = next(l for l in preview.commercial_price_lines if l.code == "debitare_fata")
    assert face_line.quantity == 12.5
    assert any("product_aggregate.commercial_measurements" in w for w in face_line.warnings)
    assert not any("COMPATIBILITY_WORKSPACE_PATH" in w for w in face_line.warnings)
    assert "rate_per_hour" not in preview.model_dump_json()
