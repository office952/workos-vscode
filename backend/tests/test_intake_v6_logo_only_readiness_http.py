"""HTTP proof: Logo-only candidate readiness stays non-offerable on Intake V6.

Uses disposable test-DB workspace rows + real public routes.
Does not activate Logo root, change policy, or mutate production seeds.
"""

from __future__ import annotations

import json

import pytest
from sqlalchemy import delete

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from services.template_usage_mode_policy import (
    TPL_VOLUMETRIC_LOGO_V1,
    is_candidate_only_template,
    is_root_offerable_template,
)

LOGO = TPL_VOLUMETRIC_LOGO_V1
WORKSPACE_ID = "logo-only-http-readiness-ws"
WORKSPACE_CODE = "IV6-LOGO-ONLY-HTTP-READY"
SVG_HASH = "a" * 64


def _logo_only_base_payload() -> dict:
    return {
        "product_binding": {
            "template_code": LOGO,
            "template_label": "Logo volumetric",
            "product_family": "litere_volumetrice",
        },
        "svg_source": {
            "file_name": "logo-only-http.svg",
            "file_size_bytes": 943,
            "file_hash": SVG_HASH,
            "upload_status": "analyzed",
        },
        "svg_analysis_json": {
            "schemaVersion": "1.10.0",
            "layers": [
                {
                    "id": "logo-dreapta",
                    "name": "logo dreapta",
                    "perimeterMl": 4.2,
                    "filledAreaSqm": 0.35,
                }
            ],
            "parts": {"count": 1, "nestableCount": 1},
            "geometry": {"perimeterMl": 4.2},
        },
        "quote_geometry": {
            "letter_count": 0,
            "letter_perimeter_m": 4.2,
            "face_area_m2": 0.35,
            "confirmed": True,
        },
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "logo-dreapta",
                    "layer_id": "logo-dreapta",
                    "layer_name": "logo dreapta",
                    "auto_role": "printed_artwork",
                    "auto_confidence": "high",
                    "confirmed_role": "printed_artwork",
                    "confirmation_state": "confirmed",
                }
            ],
            "warnings": [],
        },
        "product_composition_recommendation": {
            "status": "ok",
            "composition_type": "logo_only",
            "composition_items": [],
        },
        "product_composition_confirmed": {"confirmed": True},
    }


def _finish_setup_body(*, artwork_confirmed: bool) -> dict:
    return {
        "letter_group_finishes": [],
        "artwork_finishes": [
            {
                "layer_key": "logo-dreapta",
                "layer_name": "logo dreapta",
                "execution_type": "print_laminate",
                "color_mode": "polychrome",
                "confirmed": artwork_confirmed,
            }
        ],
        "confirmed": True,
    }


@pytest.fixture
def logo_only_http_workspace(db_fixture):
    """Disposable workspace + Logo template row in isolated test DB only."""
    from seeds.seed_tpl_volumetric_logo_v1 import seed_tpl_volumetric_logo_v1
    from tests.test_product_aggregate_volumetric_v2 import _seed_volumetric_v2_fixture

    async def _seed():
        async with db_fixture.session_maker() as session:
            await _seed_volumetric_v2_fixture(session)
            await session.commit()

        # Existing seed helper writes through patched db_manager (test DB only).
        await seed_tpl_volumetric_logo_v1()

        async with db_fixture.session_maker() as session:
            await session.execute(
                delete(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == WORKSPACE_ID)
            )
            await session.execute(
                delete(IntakeV6WorkspaceRecord).where(
                    IntakeV6WorkspaceRecord.workspace_code == WORKSPACE_CODE
                )
            )
            session.add(
                IntakeV6WorkspaceRecord(
                    id=WORKSPACE_ID,
                    workspace_code=WORKSPACE_CODE,
                    title="Logo-only HTTP readiness disposable",
                    template_code=LOGO,
                    status="draft",
                    payload_json=json.dumps(_logo_only_base_payload()),
                    # Intentionally wrong: PUT finish-setup must recompute via HTTP path.
                    readiness_status="ready_for_quote_preview",
                    created_by_user_id="test-user-id",
                    updated_by_user_id="test-user-id",
                )
            )
            await session.commit()

    db_fixture.run(_seed())
    return WORKSPACE_ID


def _put_finish(auth_client, workspace_id: str, *, artwork_confirmed: bool):
    return auth_client.put(
        f"/api/v1/intake-v6/workspaces/{workspace_id}/finish-setup",
        json=_finish_setup_body(artwork_confirmed=artwork_confirmed),
    )


def _get_workspace(auth_client, workspace_id: str):
    return auth_client.get(f"/api/v1/intake-v6/workspaces/{workspace_id}")


def _get_quote_handoff_preview(auth_client, workspace_id: str):
    return auth_client.get(
        f"/api/v1/intake-v6/workspaces/{workspace_id}/quote-handoff-preview",
        params={"client_analysis_hash": SVG_HASH},
    )


def test_http_logo_only_unconfirmed_artwork_stays_not_offerable(auth_client, logo_only_http_workspace):
    assert is_candidate_only_template(LOGO) is True
    assert is_root_offerable_template(LOGO) is False

    response = _put_finish(auth_client, logo_only_http_workspace, artwork_confirmed=False)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["readiness_status"] == "logo_only_candidate_not_offerable"
    assert body["readiness_status"] != "ready_for_quote_preview"
    assert body["payload"]["product_binding"]["template_code"] == LOGO
    assert body["payload"]["finish_setup"]["artwork_finishes"][0]["confirmed"] is False

    fetched = _get_workspace(auth_client, logo_only_http_workspace)
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["readiness_status"] == "logo_only_candidate_not_offerable"

    handoff = _get_quote_handoff_preview(auth_client, logo_only_http_workspace)
    assert handoff.status_code == 200, handoff.text
    handoff_body = handoff.json()
    assert handoff_body["workspace_readiness_status"] == "logo_only_candidate_not_offerable"
    assert handoff_body["handoff_allowed"] is False
    assert handoff_body["can_create_internal_draft_quote"] is False


def test_http_logo_only_confirmed_artwork_stays_not_offerable(
    auth_client, logo_only_http_workspace, db_fixture
):
    assert is_candidate_only_template(LOGO) is True
    assert is_root_offerable_template(LOGO) is False

    response = _put_finish(auth_client, logo_only_http_workspace, artwork_confirmed=True)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["readiness_status"] == "logo_only_candidate_not_offerable"
    assert body["readiness_status"] != "ready_for_quote_preview"
    assert body["payload"]["finish_setup"]["artwork_finishes"][0]["confirmed"] is True

    fetched = _get_workspace(auth_client, logo_only_http_workspace)
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["readiness_status"] == "logo_only_candidate_not_offerable"
    assert fetched.json()["readiness_status"] != "ready_for_quote_preview"

    handoff = _get_quote_handoff_preview(auth_client, logo_only_http_workspace)
    assert handoff.status_code == 200, handoff.text
    handoff_body = handoff.json()
    assert handoff_body["workspace_readiness_status"] == "logo_only_candidate_not_offerable"
    assert handoff_body["handoff_allowed"] is False
    assert handoff_body["can_create_internal_draft_quote"] is False

    async def _assert_availability_non_offerable():
        from services.product_template_availability_service import ProductTemplateAvailabilityService

        async with db_fixture.session_maker() as session:
            items = await ProductTemplateAvailabilityService(session).list_availability()
            logo_items = [i for i in items.items if i.template_code == LOGO]
            assert logo_items, "disposable Logo seed must appear in availability"
            assert logo_items[0].quote_offerable is False
            assert logo_items[0].capabilities.root_offerable is False

    db_fixture.run(_assert_availability_non_offerable())
