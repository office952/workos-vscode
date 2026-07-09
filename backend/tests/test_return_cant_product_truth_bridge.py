from __future__ import annotations

import asyncio
import copy
from pathlib import Path

import pytest

from schemas.intake_v4 import PILOT_V4_TEMPLATE_CODE
from seeds.seed_build4_templates import seed_build4_templates
from seeds.seed_tpl_volumetric_letters_dossier import seed_tpl_volumetric_letters_dossier
from seeds.seed_tpl_volumetric_letters_v2 import seed_tpl_volumetric_letters_v2
from services.return_cant_product_truth_bridge import (
    apply_return_cant_runtime_product_truth_bridge,
    build_return_cant_runtime_product_truth,
    clear_return_cant_runtime_product_truth,
)

FIXTURE_SVG = Path(__file__).parent / "fixtures" / "intake_v3" / "multi_layer_ten_layers.svg"


def _base_payload() -> dict:
    return {
        "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "pseudo:maria",
                    "layer_id": "pseudo:maria",
                    "layer_name": "maria",
                    "auto_role": "face",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                },
                {
                    "layer_key": "logo-1",
                    "layer_id": "logo-1",
                    "layer_name": "logo 1",
                    "auto_role": "printed_artwork",
                    "confirmed_role": "printed_artwork",
                    "confirmation_state": "confirmed",
                },
            ],
            "warnings": [],
        },
        "quote_geometry": {
            "letter_perimeter_m": 18.5,
            "geometry_source": "nest2_face_parts_outer",
            "confirmed": True,
        },
        "finish_setup": {
            "return_finish_type": "white_aluminum",
            "return_depth_mm": 60,
            "return_oracal_code": None,
            "return_oracal_name": None,
            "confirmed": True,
            "letter_group_finishes": [],
            "artwork_finishes": [],
        },
    }


def _instance(payload: dict, key: str) -> dict:
    subtree = build_return_cant_runtime_product_truth(payload)
    return subtree["components"]["return_cant"]["instances"][key]


def test_helper_derives_letter_group_instance() -> None:
    payload = _base_payload()
    payload["finish_setup"]["letter_group_finishes"] = [
        {
            "group_key": "pseudo:maria",
            "layer_name": "maria",
            "return_finish_type": "white_aluminum",
            "return_depth_mm": 60,
            "confirmed": True,
        }
    ]

    instance = _instance(payload, "letter_group:pseudo:maria")

    assert instance["instance_key"] == "letter_group:pseudo:maria"
    assert instance["source_kind"] == "letter_group"
    assert instance["source_ref"]["group_key"] == "pseudo:maria"
    assert instance["layer_group_ids"] == ["pseudo:maria"]
    assert instance["material_profile"]["width_mm"] == 60
    assert instance["finish_variant"] == {
        "type": "stock_color",
        "stock_color_label": "Alb",
    }
    assert instance["pricing_keys"] == {
        "material_profile_width": "MAT-PROFIL-LATERAL-LITERE-60MM",
    }


def test_helper_derives_artwork_layer_instance() -> None:
    payload = _base_payload()
    payload["finish_setup"]["artwork_finishes"] = [
        {
            "layer_key": "logo-1",
            "layer_name": "logo 1",
            "return_finish_type": "oracal_651",
            "return_depth_mm": 80,
            "return_oracal_code": "651-070",
            "return_oracal_name": "Black",
            "confirmed": True,
        }
    ]

    instance = _instance(payload, "artwork_layer:logo-1")

    assert instance["instance_key"] == "artwork_layer:logo-1"
    assert instance["source_kind"] == "artwork_layer"
    assert instance["source_ref"]["layer_key"] == "logo-1"
    assert instance["layer_group_ids"] == ["logo-1"]
    assert instance["pricing_keys"] == {
        "vinyl_material": "MAT-ORACAL-651",
        "vinyl_application_labor": "RETURN_CANT_VINYL_APPLICATION_LABOR",
        "material_profile_width": "MAT-PROFIL-LATERAL-LITERE-80MM",
    }
    assert instance["finish_variant"]["type"] == "vinyl_application"
    assert instance["finish_variant"]["vinyl"]["series"] == "Oracal 651"


def test_missing_stable_key_does_not_invent_instance_key() -> None:
    payload = _base_payload()
    payload["finish_setup"]["letter_group_finishes"] = [{"return_finish_type": "white_aluminum"}]
    payload["finish_setup"]["artwork_finishes"] = [{"return_finish_type": "ral_paint"}]

    subtree = build_return_cant_runtime_product_truth(payload)

    assert subtree["components"]["return_cant"]["instances"] == {}


def test_quote_geometry_perimeter_is_evidence_only() -> None:
    payload = _base_payload()
    payload["finish_setup"]["letter_group_finishes"] = [
        {
            "group_key": "pseudo:maria",
            "return_finish_type": "white_aluminum",
            "return_depth_mm": 60,
        }
    ]

    instance = _instance(payload, "letter_group:pseudo:maria")

    assert instance["geometry"]["perimeter_source"] == "evidence_only"
    assert instance["geometry"]["evidence_perimeter_m"] == 18.5
    assert "confirmed_perimeter_m" not in instance["geometry"]
    assert instance["confirmation_state"] == "blocked"
    assert "RETURN_CANT_PERIMETER_EVIDENCE_ONLY" in instance["blockers"]
    assert "RETURN_CANT_CONFIRMED_PERIMETER_MISSING" in instance["blockers"]
    assert "RETURN_CANT_COMPONENT_CONFIRMATION_MISSING" in instance["blockers"]


def test_paint_application_emits_final_pricing_keys_by_width() -> None:
    payload = _base_payload()
    payload["finish_setup"]["letter_group_finishes"] = [
        {
            "group_key": "pseudo:maria",
            "return_finish_type": "ral_paint",
            "return_depth_mm": 100,
            "return_oracal_code": "RAL 3020",
            "return_oracal_name": "Traffic red",
        }
    ]

    instance = _instance(payload, "letter_group:pseudo:maria")

    assert instance["finish_variant"]["type"] == "paint_application"
    assert instance["pricing_keys"] == {
        "ral_paint_labor": "RETURN_CANT_RAL_PAINT_LABOR",
        "material_profile_width": "MAT-PROFIL-LATERAL-LITERE-100MM",
        "ral_paint_material_by_width": "MAT-VOPSEA-RAL-CANT-100MM",
    }


def test_stock_color_does_not_emit_vinyl_or_paint_pricing_keys() -> None:
    payload = _base_payload()
    payload["finish_setup"]["artwork_finishes"] = [
        {
            "layer_key": "logo-1",
            "return_finish_type": "black_aluminum",
            "return_depth_mm": 30,
        }
    ]

    instance = _instance(payload, "artwork_layer:logo-1")

    assert instance["pricing_keys"] == {
        "material_profile_width": "MAT-PROFIL-LATERAL-LITERE-30MM",
    }
    assert instance["finish_variant"]["stock_color_label"] == "Negru"


def test_apply_bridge_is_idempotent_and_keeps_legacy_path_unwritten() -> None:
    payload = _base_payload()
    payload["finish_setup"]["letter_group_finishes"] = [
        {
            "group_key": "pseudo:maria",
            "return_finish_type": "white_aluminum",
            "return_depth_mm": 60,
        }
    ]
    payload["components"] = {"returnCant": {"depthMm": 60}}
    original_without_product_truth = copy.deepcopy(payload)

    apply_return_cant_runtime_product_truth_bridge(payload)
    first = copy.deepcopy(payload["product_truth"])
    apply_return_cant_runtime_product_truth_bridge(payload)

    assert payload["product_truth"] == first
    assert payload["components"] == original_without_product_truth["components"]
    assert "returnCant" not in payload["product_truth"]["components"]


def test_apply_bridge_mutates_only_product_truth_subtree() -> None:
    payload = _base_payload()
    payload["finish_setup"]["letter_group_finishes"] = [
        {
            "group_key": "pseudo:maria",
            "return_finish_type": "white_aluminum",
            "return_depth_mm": 60,
        }
    ]
    expected = copy.deepcopy(payload)

    apply_return_cant_runtime_product_truth_bridge(payload)

    expected["product_truth"] = payload["product_truth"]
    assert payload == expected


def test_clear_bridge_removes_only_return_cant_component() -> None:
    payload = _base_payload()
    payload["product_truth"] = {
        "components": {
            "face": {"version": "v1"},
            "return_cant": {"version": "v1", "instances": {"x": {}}},
        }
    }

    clear_return_cant_runtime_product_truth(payload)

    assert payload["product_truth"] == {"components": {"face": {"version": "v1"}}}


@pytest.fixture(scope="module")
def seeded_db(db_fixture):
    db_fixture.patch_global_db_manager()
    db_fixture.run(seed_build4_templates())
    db_fixture.run(seed_tpl_volumetric_letters_dossier())
    db_fixture.run(seed_tpl_volumetric_letters_v2())
    return db_fixture


@pytest.fixture
def v4_client(seeded_db):
    from core.database import get_db
    from dependencies.auth import get_current_user
    from fastapi.testclient import TestClient
    from main import app
    from schemas.auth import UserResponse

    async def _override_get_db():
        async with seeded_db.session_maker() as session:
            yield session

    async def _override_get_current_user():
        return UserResponse(
            id="test-user-id",
            email="test@example.com",
            name="Test Admin",
            role="admin",
            last_login=None,
        )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    app.dependency_overrides.clear()


def _confirm_layer_roles(v4_client, workspace_id: str, svg_path: Path = FIXTURE_SVG) -> dict:
    svg_bytes = svg_path.read_bytes()
    upload = v4_client.post(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/svg",
        files={"file": (svg_path.name, svg_bytes, "image/svg+xml")},
    )
    assert upload.status_code == 200, upload.text
    layers = upload.json()["layer_role_setup"]["layers"]
    updates = [
        {
            "layer_key": layer["layer_key"],
            "confirmed_role": layer["auto_role"] if layer["auto_role"] != "unknown" else "face",
            "confirmation_state": "confirmed",
        }
        for layer in layers
    ]
    confirmed = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/layer-roles",
        json={"layers": updates},
    )
    assert confirmed.status_code == 200, confirmed.text
    return confirmed.json()["payload"]["layer_role_setup"]


def _put_analysis_bundle(v4_client, workspace_id: str, *, layer_role_setup: dict | None = None) -> None:
    svg_text = FIXTURE_SVG.read_text(encoding="utf-8")
    if layer_role_setup is None:
        layer_role_setup = _confirm_layer_roles(v4_client, workspace_id)
    saved = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/analysis-bundle",
        json={
            "file_name": FIXTURE_SVG.name,
            "file_size_bytes": len(svg_text.encode("utf-8")),
            "svg_text": svg_text,
            "svg_analysis_json": {
                "schemaVersion": "1.10.0",
                "layers": [
                    {
                        "id": layer["layer_key"],
                        "name": layer.get("layer_name") or layer["layer_key"],
                        "perimeterMl": 10.0,
                        "filledAreaSqm": 1.2,
                    }
                    for layer in layer_role_setup.get("layers", [])
                    if layer.get("confirmation_state") != "ignored"
                ],
                "parts": {"count": 10, "nestableCount": 8},
                "geometry": {"perimeterMl": 10.0},
            },
            "layer_role_setup": layer_role_setup,
        },
    )
    assert saved.status_code == 200, saved.text


def test_finish_setup_save_persists_product_truth_runtime_bridge(v4_client) -> None:
    create = v4_client.post(
        "/api/v1/intake-v4/workspaces",
        json={"title": "Return cant product truth", "template_code": PILOT_V4_TEMPLATE_CODE},
    )
    assert create.status_code == 201, create.text
    workspace_id = create.json()["id"]
    layer_role_setup = {
        "confirmation_status": "complete",
        "layers": [
            {
                "layer_key": "pseudo:maria",
                "layer_id": "pseudo:maria",
                "layer_name": "maria",
                "auto_role": "face",
                "auto_confidence": "high",
                "confirmed_role": "face",
                "confirmation_state": "confirmed",
            },
            {
                "layer_key": "logo-1",
                "layer_id": "logo-1",
                "layer_name": "logo 1",
                "auto_role": "printed_artwork",
                "auto_confidence": "high",
                "confirmed_role": "printed_artwork",
                "confirmation_state": "confirmed",
            },
        ],
        "warnings": [],
    }
    _put_analysis_bundle(v4_client, workspace_id, layer_role_setup=layer_role_setup)

    saved = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
        json={
            "return_finish_type": "white_aluminum",
            "return_depth_mm": 60,
            "confirmed": True,
            "letter_group_finishes": [
                {
                    "group_key": "pseudo:maria",
                    "layer_name": "maria",
                    "return_finish_type": "white_aluminum",
                    "return_depth_mm": 60,
                    "confirmed": True,
                }
            ],
            "artwork_finishes": [
                {
                    "layer_key": "logo-1",
                    "layer_name": "logo 1",
                    "return_finish_type": "ral_paint",
                    "return_depth_mm": 80,
                    "return_oracal_code": "RAL 3020",
                    "return_oracal_name": "Traffic red",
                    "confirmed": True,
                }
            ],
        },
    )
    assert saved.status_code == 200, saved.text

    payload = saved.json()["payload"]
    container = payload["product_truth"]["components"]["return_cant"]
    assert container["version"] == "v1"
    assert set(container["instances"].keys()) == {"letter_group:pseudo:maria", "artwork_layer:logo-1"}
    assert payload.get("components") is None or "returnCant" not in payload.get("components", {})


def test_svg_replacement_clears_stale_return_cant_product_truth(v4_client) -> None:
    create = v4_client.post(
        "/api/v1/intake-v4/workspaces",
        json={"title": "Return cant clear stale", "template_code": PILOT_V4_TEMPLATE_CODE},
    )
    assert create.status_code == 201, create.text
    workspace_id = create.json()["id"]
    layer_role_setup = {
        "confirmation_status": "complete",
        "layers": [
            {
                "layer_key": "pseudo:maria",
                "layer_id": "pseudo:maria",
                "layer_name": "maria",
                "auto_role": "face",
                "auto_confidence": "high",
                "confirmed_role": "face",
                "confirmation_state": "confirmed",
            }
        ],
        "warnings": [],
    }
    _put_analysis_bundle(v4_client, workspace_id, layer_role_setup=layer_role_setup)
    save = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
        json={
            "return_finish_type": "white_aluminum",
            "return_depth_mm": 60,
            "confirmed": True,
            "letter_group_finishes": [
                {
                    "group_key": "pseudo:maria",
                    "layer_name": "maria",
                    "return_finish_type": "white_aluminum",
                    "return_depth_mm": 60,
                    "confirmed": True,
                }
            ],
        },
    )
    assert save.status_code == 200, save.text
    assert "return_cant" in save.json()["payload"]["product_truth"]["components"]

    replacement_svg = Path(__file__).parent / "fixtures" / "intake_v3" / "multi_layer_ten_layers.svg"
    upload = v4_client.post(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/svg",
        files={"file": (replacement_svg.name, replacement_svg.read_bytes(), "image/svg+xml")},
    )
    assert upload.status_code == 200, upload.text
    payload = upload.json()["workspace"]["payload"]
    assert payload.get("finish_setup") is None
    product_truth = payload.get("product_truth")
    assert not isinstance(product_truth, dict) or "return_cant" not in product_truth.get("components", {})