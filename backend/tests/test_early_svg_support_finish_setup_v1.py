"""Early SUPPORT_CONTOUR FinishSetup association before layer roles are complete."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import delete

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from schemas.intake_v6 import IntakeV6FinishSetup
from services.intake_v6_workspace_service import is_early_svg_component_association

WS_ID = "early-support-finish-ws"
WS_CODE = "IV6-EARLY-SUPPORT"
SVG_HASH = "b" * 64


def _partial_roles_payload() -> dict:
    return {
        "product_binding": {
            "template_code": "TPL-VOLUMETRIC-LETTERS_v2",
            "template_label": "Litere volumetrice",
            "product_family": "litere_volumetrice",
        },
        "svg_source": {
            "file_name": "LITERE-VOLUMETRICE-ACP.svg",
            "file_size_bytes": 1200,
            "file_hash": SVG_HASH,
            "upload_status": "analyzed",
        },
        "svg_analysis_json": {
            "schemaVersion": "1.10.0",
            "layers": [
                {"id": "pseudo:fill-green", "name": "verde", "perimeterMl": 2.0, "filledAreaSqm": 0.1},
                {"id": "logo_instance_001", "name": "Logo 1", "perimeterMl": 1.0, "filledAreaSqm": 0.05},
            ],
            "parts": {"count": 2, "nestableCount": 2},
            "geometry": {"perimeterMl": 3.0},
            "closedContourCandidates": {"candidate_count": 1, "unit_ambiguity": True},
        },
        "quote_geometry": {
            "letter_count": 2,
            "letter_perimeter_m": 3.0,
            "face_area_m2": 0.15,
            "confirmed": False,
        },
        "layer_role_setup": {
            "confirmation_status": "partial",
            "layers": [
                {
                    "layer_key": "pseudo:fill-green",
                    "layer_id": "pseudo:fill-green",
                    "layer_name": "verde",
                    "auto_role": "face",
                    "auto_confidence": "high",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                },
                {
                    "layer_key": "logo_instance_001",
                    "layer_id": "logo_instance_001",
                    "layer_name": "Logo 1",
                    "auto_role": "printed_artwork",
                    "auto_confidence": "high",
                    "confirmed_role": None,
                    "confirmation_state": "pending",
                },
            ],
            "warnings": [],
        },
    }


def _support_finish_body() -> dict:
    return {
        "confirmed": False,
        "svg_component_bindings": [
            {
                "schema": "svg_component_bindings_v1",
                "binding_id": "bind_acm_early",
                "geometry_role": "SUPPORT_CONTOUR",
                "component_template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                "selection_mode": "CLOSED_CONTOUR",
                "selected_geometry": {
                    "layer_ids": [],
                    "group_ids": [],
                    "element_ids": ["cc_b121cd92"],
                    "geometry_hashes": ["b121cd92"],
                    "source_svg_hash": SVG_HASH,
                },
                "configuration": {},
                "status": "CONFIRMED",
                "svg_support_element_id": "cc_b121cd92",
            }
        ],
        "svg_support_selection": {
            "status": "confirmed",
            "role": "ALUCOBOND_CASED_PANEL",
            "contour_id": "cc_b121cd92",
            "svg_support_element_id": "cc_b121cd92",
            "geometry_hash": "b121cd92",
            "svg_source_hash": SVG_HASH,
            "unit_ambiguity": True,
            "panel_geometry": {
                "width_mm": 2000.0,
                "height_mm": 700.0,
                "area_mm2": 1400000.0,
                "perimeter_mm": 5400.0,
            },
        },
        "mounting_solution": {
            "kind": "product_system_template",
            "template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
            "configuration": {
                "panel_width_mm": 2000.0,
                "panel_height_mm": 700.0,
                "dimension_source": "svg_support_selection",
                "unit_ambiguity": True,
            },
        },
    }


@pytest.fixture
def early_support_workspace(db_fixture):
    from tests.test_product_aggregate_volumetric_v2 import _seed_volumetric_v2_fixture

    async def _seed():
        async with db_fixture.session_maker() as session:
            await _seed_volumetric_v2_fixture(session)
            await session.execute(
                delete(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == WS_ID)
            )
            session.add(
                IntakeV6WorkspaceRecord(
                    id=WS_ID,
                    workspace_code=WS_CODE,
                    title="Early support FinishSetup",
                    template_code="TPL-VOLUMETRIC-LETTERS_v2",
                    status="draft",
                    payload_json=json.dumps(_partial_roles_payload()),
                    readiness_status="draft",
                    created_by_user_id="test-user-id",
                    updated_by_user_id="test-user-id",
                )
            )
            await session.commit()

    db_fixture.run(_seed())
    return WS_ID


def test_early_association_detects_support_contour_binding() -> None:
    req = IntakeV6FinishSetup.model_validate(
        {
            "confirmed": False,
            "svg_component_bindings": [
                {
                    "schema": "svg_component_bindings_v1",
                    "binding_id": "bind_acm",
                    "geometry_role": "SUPPORT_CONTOUR",
                    "component_template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                    "selection_mode": "CLOSED_CONTOUR",
                    "selected_geometry": {
                        "layer_ids": [],
                        "group_ids": [],
                        "element_ids": ["cc_outer"],
                        "geometry_hashes": ["abc"],
                        "source_svg_hash": "hash1",
                    },
                    "configuration": {},
                    "status": "CONFIRMED",
                }
            ],
        }
    )
    assert is_early_svg_component_association(req) is True


def test_early_association_false_when_finish_confirmed() -> None:
    req = IntakeV6FinishSetup.model_validate(
        {
            "confirmed": True,
            "svg_component_bindings": [
                {
                    "geometry_role": "SUPPORT_CONTOUR",
                    "component_template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                    "status": "CONFIRMED",
                }
            ],
        }
    )
    assert is_early_svg_component_association(req) is False


def test_early_association_false_without_support() -> None:
    req = IntakeV6FinishSetup.model_validate(
        {
            "confirmed": False,
            "svg_component_bindings": [
                {
                    "geometry_role": "LETTER_VECTOR_SET",
                    "component_template_code": "TPL-VOLUMETRIC-FACE_v1",
                    "status": "DRAFT",
                }
            ],
        }
    )
    assert is_early_svg_component_association(req) is False


def test_early_association_from_svg_support_selection() -> None:
    req = IntakeV6FinishSetup.model_validate(
        {
            "confirmed": False,
            "svg_support_selection": {
                "status": "confirmed",
                "role": "ALUCOBOND_CASED_PANEL",
                "contour_id": "cc_outer",
            },
        }
    )
    assert is_early_svg_component_association(req) is True


def test_http_early_support_binding_persists_when_layer_roles_partial(
    auth_client, early_support_workspace
) -> None:
    """Regression: Contur suport must not 422 with layer_roles_incomplete."""
    resp = auth_client.put(
        f"/api/v1/intake-v6/workspaces/{early_support_workspace}/finish-setup",
        json=_support_finish_body(),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    finish = (body.get("payload") or {}).get("finish_setup") or {}
    bindings = finish.get("svg_component_bindings") or []
    assert any(
        b.get("geometry_role") == "SUPPORT_CONTOUR"
        and b.get("component_template_code") == "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"
        for b in bindings
        if isinstance(b, dict)
    )
    selection = finish.get("svg_support_selection") or {}
    assert selection.get("contour_id") == "cc_b121cd92"
    assert float((selection.get("panel_geometry") or {}).get("width_mm") or 0) == 2000.0
    composition = (body.get("payload") or {}).get("product_composition_recommendation") or {}
    roles = [
        item.get("component_role")
        for item in (composition.get("composition_items") or [])
        if isinstance(item, dict)
    ]
    assert "support_panel" in roles


def test_http_non_support_finish_still_blocked_when_roles_incomplete(
    auth_client, early_support_workspace
) -> None:
    resp = auth_client.put(
        f"/api/v1/intake-v6/workspaces/{early_support_workspace}/finish-setup",
        json={"confirmed": False, "illuminated": True},
    )
    assert resp.status_code == 422
    detail = resp.json().get("detail") or {}
    assert detail.get("error") == "layer_roles_incomplete"
