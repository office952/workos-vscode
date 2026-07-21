"""Separate calculation preview boundaries for TPL-VOLUM-ALUMINIU_v1."""

from __future__ import annotations

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from schemas.volum_aluminiu_separate_calc_preview import VolumAluminiuSeparateCalcPreviewRequest
from services.volum_aluminiu_component_contract import TEMPLATE_CODE
from services.volum_aluminiu_separate_calc_preview_service import (
    VolumAluminiuSeparateCalcPreviewService,
)
from tests.test_product_aggregate_volumetric_v2 import _seed_volumetric_v2_fixture


def _payload_with_confirmation(*, perimeter: float = 12.5) -> dict:
    return {
        "quote_geometry": {"letter_perimeter_m": 18.5},
        "layer_role_setup": {
            "layers": [
                {
                    "layer_key": "pseudo:maria",
                    "layer_id": "pseudo:maria",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                }
            ]
        },
        "finish_setup": {
            "return_finish_type": "white_aluminum",
            "return_depth_mm": 60,
            "letter_group_finishes": [
                {
                    "group_key": "pseudo:maria",
                    "return_finish_type": "white_aluminum",
                    "return_depth_mm": 60,
                }
            ],
            "return_cant_component_confirmation": {
                "instances": {
                    "letter_group:pseudo:maria": {
                        "confirmed_perimeter_m": perimeter,
                        "confirmed_perimeter_source": "operator_confirmed",
                        "confirmation_source": "operator_component_confirmation",
                    }
                }
            },
        },
    }


def test_preview_fails_without_confirmation() -> None:
    service = VolumAluminiuSeparateCalcPreviewService()
    body = VolumAluminiuSeparateCalcPreviewRequest(
        payload={
            "quote_geometry": {"letter_perimeter_m": 18.5},
            "layer_role_setup": {
                "layers": [
                    {
                        "layer_key": "pseudo:maria",
                        "layer_id": "pseudo:maria",
                        "confirmed_role": "face",
                        "confirmation_state": "confirmed",
                    }
                ]
            },
            "finish_setup": {
                "return_finish_type": "white_aluminum",
                "return_depth_mm": 60,
                "letter_group_finishes": [
                    {
                        "group_key": "pseudo:maria",
                        "return_finish_type": "white_aluminum",
                        "return_depth_mm": 60,
                    }
                ],
            },
        }
    )
    out = service.build_preview(TEMPLATE_CODE, body)
    assert out.persist is False
    assert out.publication_blocked is True
    assert out.activation_required is False
    assert out.separate_calculation == "FAIL"
    assert out.quantity["ok"] is False
    assert out.commercial is None


def test_preview_pass_with_confirmed_perimeter_is_idempotent() -> None:
    service = VolumAluminiuSeparateCalcPreviewService()
    body = VolumAluminiuSeparateCalcPreviewRequest(payload=_payload_with_confirmation())
    first = service.build_preview(TEMPLATE_CODE, body)
    second = service.build_preview(TEMPLATE_CODE, body)

    assert first.separate_calculation == "PASS"
    assert first.quantity["quantity_m"] == 12.5
    assert first.commercial is not None
    assert first.commercial["ok"] is True
    assert first.commercial["basis_type"] == "ml"
    assert first.commercial["quantity"] == 12.5
    assert first.internal_cost is not None
    assert first.internal_cost["basis_type"] == "ml"
    assert first.publication_blocked is True
    assert first.model_dump() == second.model_dump()


def test_preview_rejects_unknown_template() -> None:
    service = VolumAluminiuSeparateCalcPreviewService()
    out = service.build_preview("TPL-OTHER", VolumAluminiuSeparateCalcPreviewRequest())
    assert out.separate_calculation == "FAIL"
    assert "TEMPLATE_NOT_VOLUM_ALUMINIU" in out.blockers


@pytest_asyncio.fixture
async def volumetric_v2_db(db_session):
    await _seed_volumetric_v2_fixture(db_session)
    return db_session


@pytest.mark.asyncio
async def test_http_separate_calc_preview_endpoint(volumetric_v2_db):
    from core.database import get_db
    from dependencies.auth import get_current_user
    from main import app
    from schemas.auth import UserResponse

    async def _override_get_db():
        yield volumetric_v2_db

    async def _override_user():
        return UserResponse(
            id="test-user-id",
            email="test@example.com",
            name="Test Admin",
            role="admin",
            last_login=None,
        )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_user
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            blocked = client.post(
                f"/api/v1/product-system/templates/{TEMPLATE_CODE}/separate-calculation-preview",
                json={"payload": {"quote_geometry": {"letter_perimeter_m": 9.0}}},
            )
            assert blocked.status_code == 200, blocked.text
            assert blocked.json()["separate_calculation"] == "FAIL"
            assert blocked.json()["persist"] is False

            ok = client.post(
                f"/api/v1/product-system/templates/{TEMPLATE_CODE}/separate-calculation-preview",
                json={"payload": _payload_with_confirmation(perimeter=4.0)},
            )
            assert ok.status_code == 200, ok.text
            body = ok.json()
            assert body["separate_calculation"] == "PASS"
            assert body["quantity"]["quantity_m"] == 4.0
            assert body["publication_blocked"] is True

            unsupported = client.post(
                "/api/v1/product-system/templates/TPL-VOLUMETRIC-LETTERS_v2/separate-calculation-preview",
                json={"payload": {}},
            )
            assert unsupported.status_code == 422
    finally:
        app.dependency_overrides.clear()
