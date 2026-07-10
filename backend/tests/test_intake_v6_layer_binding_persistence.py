from __future__ import annotations

import copy
import json
import uuid

import pytest
from sqlalchemy import select

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from schemas.auth import UserResponse
from services.form_system_contract_backbone_service import build_form_system_contract_map
from services.intake_v6_layer_binding_persistence_service import (
    persist_logo_layer_bindings_from_composition_confirmation,
)
from services.intake_v6_product_composition_recommendation_service import (
    LETTERS_TEMPLATE_CODE,
    LOGO_TEMPLATE_CODE,
    apply_product_composition_recommendation,
    build_product_composition_recommendation,
)
from services.intake_v6_workspace_service import (
    get_intake_v6_workspace,
    save_product_composition_confirmation_for_workspace,
)
from services.linked_template_runtime_segment_extraction_service import (
    extract_linked_template_segments_from_workspace_payload,
)
from services.product_definition_builder_service import ProductDefinitionBuilderService

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

ROOT = "TPL-VOLUMETRIC-LETTERS_v2"
LOGO = LOGO_TEMPLATE_CODE


def _user() -> UserResponse:
    return UserResponse(id="test-user", email="test@example.com", name="Test User", role="admin", last_login=None)


def _layer(key: str, name: str, role: str) -> dict:
    return {
        "layer_key": key,
        "layer_id": key,
        "layer_name": name,
        "auto_role": role,
        "confirmed_role": role,
        "confirmation_state": "confirmed",
        "auto_confidence": "high",
    }


def _gradi_payload(*, with_bindings: list[dict] | None = None) -> dict:
    payload = {
        "product_binding": {"template_code": ROOT},
        "svg_source": {"file_name": "gradi-curat.svg", "file_size_bytes": 27173, "upload_status": "analyzed"},
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                _layer("letters", "Litere GRADI", "face"),
                _layer("logo-stanga", "logo stanga", "printed_artwork"),
                _layer("logo-dreapta", "logo dreapta", "printed_artwork"),
            ],
            "layer_bindings": with_bindings or [],
            "warnings": [],
        },
        "finish_setup": {
            "confirmed": True,
            "face_finish_type": "oracal_651",
            "return_depth_mm": 60,
            "return_finish_type": "white_aluminum",
            "artwork_finishes": [
                {
                    "layer_key": "logo-stanga",
                    "layer_name": "logo stanga",
                    "execution_type": "print_laminate",
                    "color_mode": "polychrome",
                    "return_depth_mm": 60,
                    "confirmed": True,
                },
                {
                    "layer_key": "logo-dreapta",
                    "layer_name": "logo dreapta",
                    "execution_type": "print_laminate",
                    "color_mode": "polychrome",
                    "return_depth_mm": 60,
                    "confirmed": True,
                },
            ],
        },
    }
    apply_product_composition_recommendation(payload)
    return payload


def _linked_template_composition() -> dict:
    return build_form_system_contract_map(ROOT)["linked_template_composition"]


def _logo_composition_items(payload: dict) -> list[dict]:
    recommendation = payload["product_composition_recommendation"]
    return [
        item
        for item in recommendation["composition_items"]
        if item.get("component_role") == "volumetric_logo"
    ]


def _all_composition_items(payload: dict) -> list[dict]:
    return payload["product_composition_recommendation"]["composition_items"]


def _bindings(payload: dict) -> list[dict]:
    return payload["layer_role_setup"]["layer_bindings"]


def _segment_blocker_codes(payload: dict) -> list[str]:
    linked = extract_linked_template_segments_from_workspace_payload(
        root_template_code=ROOT,
        workspace_payload=payload,
        linked_template_composition=_linked_template_composition(),
    )
    codes: list[str] = []
    for segment in linked["segments"]:
        for blocker in segment["product_truth_readiness"]["blockers"]:
            codes.append(blocker["code"])
    return codes


# --- Pure contract tests ---


def test_valid_logo_segments_create_one_binding_each() -> None:
    payload = _gradi_payload()
    items = _all_composition_items(payload)

    persist_logo_layer_bindings_from_composition_confirmation(payload, confirmed=True, confirmed_items=items)

    bindings = _bindings(payload)
    assert len(bindings) == 2
    assert {binding["layer_key"] for binding in bindings} == {"logo-stanga", "logo-dreapta"}


def test_two_segments_may_share_same_template_code() -> None:
    payload = _gradi_payload()
    items = _all_composition_items(payload)

    persist_logo_layer_bindings_from_composition_confirmation(payload, confirmed=True, confirmed_items=items)

    bindings = _bindings(payload)
    assert all(binding["target_template_code"] == LOGO for binding in bindings)


def test_letter_segments_do_not_create_logo_bindings() -> None:
    payload = _gradi_payload()
    letter_only = [
        item
        for item in _all_composition_items(payload)
        if item.get("component_role") == "volumetric_letters"
    ]

    persist_logo_layer_bindings_from_composition_confirmation(payload, confirmed=True, confirmed_items=letter_only)

    assert _bindings(payload) == []


def test_unresolved_refs_do_not_create_bindings() -> None:
    payload = _gradi_payload()
    items = [
        {
            "composition_item_id": "logo",
            "template_code": LOGO,
            "component_role": "volumetric_logo",
            "source_layer_ids": ["missing-logo-ref"],
        }
    ]

    persist_logo_layer_bindings_from_composition_confirmation(payload, confirmed=True, confirmed_items=items)

    assert _bindings(payload) == []


def test_duplicate_segment_input_creates_single_row() -> None:
    payload = _gradi_payload()
    items = [
        {
            "composition_item_id": "logo",
            "template_code": LOGO,
            "component_role": "volumetric_logo",
            "source_layer_ids": ["logo-stanga", "logo-stanga", "logo-dreapta"],
        }
    ]

    persist_logo_layer_bindings_from_composition_confirmation(payload, confirmed=True, confirmed_items=items)

    bindings = _bindings(payload)
    assert len(bindings) == 2
    assert [binding["layer_key"] for binding in bindings] == ["logo-dreapta", "logo-stanga"]


def test_stable_ordering_is_preserved() -> None:
    payload = _gradi_payload()
    items = _all_composition_items(payload)

    persist_logo_layer_bindings_from_composition_confirmation(payload, confirmed=True, confirmed_items=items)

    assert [binding["layer_key"] for binding in _bindings(payload)] == ["logo-dreapta", "logo-stanga"]


def test_no_binding_written_before_confirmation() -> None:
    payload = _gradi_payload()
    items = _all_composition_items(payload)

    persist_logo_layer_bindings_from_composition_confirmation(payload, confirmed=False, confirmed_items=items)

    assert _bindings(payload) == []


def test_idempotent_reconfirmation() -> None:
    payload = _gradi_payload()
    items = _all_composition_items(payload)

    persist_logo_layer_bindings_from_composition_confirmation(payload, confirmed=True, confirmed_items=items)
    first = copy.deepcopy(_bindings(payload))
    persist_logo_layer_bindings_from_composition_confirmation(payload, confirmed=True, confirmed_items=items)

    assert _bindings(payload) == first


def test_existing_unrelated_layer_role_setup_data_unchanged() -> None:
    payload = _gradi_payload()
    layers_before = copy.deepcopy(payload["layer_role_setup"]["layers"])
    items = _all_composition_items(payload)

    persist_logo_layer_bindings_from_composition_confirmation(payload, confirmed=True, confirmed_items=items)

    assert payload["layer_role_setup"]["layers"] == layers_before


def test_existing_finishes_remain_unchanged() -> None:
    payload = _gradi_payload()
    finishes_before = copy.deepcopy(payload["finish_setup"]["artwork_finishes"])
    items = _all_composition_items(payload)

    persist_logo_layer_bindings_from_composition_confirmation(payload, confirmed=True, confirmed_items=items)

    assert payload["finish_setup"]["artwork_finishes"] == finishes_before


def test_confirmed_binding_removes_missing_binding_blocker() -> None:
    payload = _gradi_payload()
    items = _all_composition_items(payload)

    before = _segment_blocker_codes(payload)
    assert "LINKED_TEMPLATE_BINDING_MISSING" in before

    persist_logo_layer_bindings_from_composition_confirmation(payload, confirmed=True, confirmed_items=items)

    after = _segment_blocker_codes(payload)
    assert "LINKED_TEMPLATE_BINDING_MISSING" not in after


def test_missing_finish_blocker_remains_independent() -> None:
    payload = _gradi_payload()
    payload["finish_setup"]["artwork_finishes"][0]["confirmed"] = False
    items = _all_composition_items(payload)

    persist_logo_layer_bindings_from_composition_confirmation(payload, confirmed=True, confirmed_items=items)

    linked = extract_linked_template_segments_from_workspace_payload(
        root_template_code=ROOT,
        workspace_payload=payload,
        linked_template_composition=_linked_template_composition(),
    )
    logo_stanga = next(segment for segment in linked["segments"] if segment["segment_key"] == "logo-stanga")
    codes = [blocker["code"] for blocker in logo_stanga["product_truth_readiness"]["blockers"]]
    assert "LINKED_TEMPLATE_BINDING_MISSING" not in codes
    assert "LINKED_SEGMENT_FINISH_MISSING" in codes


def test_suggested_binding_upgrades_to_confirmed_on_reconfirm() -> None:
    payload = _gradi_payload(
        with_bindings=[
            {
                "layer_key": "logo-stanga",
                "target_template_code": LOGO,
                "binding_status": "suggested",
                "suggested_semantic_role": "printed_artwork",
            }
        ]
    )
    items = _all_composition_items(payload)

    persist_logo_layer_bindings_from_composition_confirmation(payload, confirmed=True, confirmed_items=items)

    bindings = {binding["layer_key"]: binding for binding in _bindings(payload)}
    assert bindings["logo-stanga"]["binding_status"] == "confirmed"
    assert bindings["logo-dreapta"]["binding_status"] == "confirmed"


# --- Persistence integration tests ---


@pytest.mark.asyncio
async def test_composition_confirmation_writes_layer_bindings(db_session) -> None:
    workspace_id = str(uuid.uuid4())
    payload = _gradi_payload()
    db_session.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"WS-BIND-{workspace_id[:8]}",
            title="Binding persistence workspace",
            template_code=ROOT,
            status="draft",
            payload_json=json.dumps(payload),
        )
    )
    await db_session.commit()

    response = await save_product_composition_confirmation_for_workspace(
        db_session,
        workspace_id,
        confirmed=True,
        items=_all_composition_items(payload),
        current_user=_user(),
    )

    saved = json.loads(
        (
            await db_session.execute(
                select(IntakeV6WorkspaceRecord.payload_json).where(IntakeV6WorkspaceRecord.id == workspace_id)
            )
        ).scalar_one()
    )
    bindings = saved["layer_role_setup"]["layer_bindings"]
    assert len(bindings) == 2
    assert saved["product_composition_confirmed"]["confirmed"] is True
    response_bindings = (response.payload.get("layer_role_setup") or {}).get("layer_bindings") or []
    assert len(response_bindings) == 2


@pytest.mark.asyncio
async def test_binding_survives_workspace_reload(db_session) -> None:
    workspace_id = str(uuid.uuid4())
    payload = _gradi_payload()
    db_session.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"WS-RELOAD-{workspace_id[:8]}",
            title="Binding reload workspace",
            template_code=ROOT,
            status="draft",
            payload_json=json.dumps(payload),
        )
    )
    await db_session.commit()

    await save_product_composition_confirmation_for_workspace(
        db_session,
        workspace_id,
        confirmed=True,
        items=_all_composition_items(payload),
        current_user=_user(),
    )

    reloaded = await get_intake_v6_workspace(db_session, workspace_id)
    layer_setup = reloaded.payload.get("layer_role_setup") or {}
    bindings = layer_setup.get("layer_bindings") or []
    assert {binding["layer_key"] for binding in bindings} == {"logo-stanga", "logo-dreapta"}
    assert all(binding["binding_status"] == "confirmed" for binding in bindings)


@pytest.mark.asyncio
async def test_product_definition_consumes_persisted_binding(volumetric_v2_db) -> None:
    workspace_id = str(uuid.uuid4())
    payload = _gradi_payload()
    persist_logo_layer_bindings_from_composition_confirmation(
        payload,
        confirmed=True,
        confirmed_items=_all_composition_items(payload),
    )
    payload["product_composition_confirmed"] = {"confirmed": True, "items": _all_composition_items(payload)}

    volumetric_v2_db.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"WS-PD-{workspace_id[:8]}",
            title="PD binding workspace",
            template_code=ROOT,
            status="draft",
            payload_json=json.dumps(payload),
        )
    )
    await volumetric_v2_db.commit()

    preview = await ProductDefinitionBuilderService(volumetric_v2_db).build_preview(ROOT, workspace_id=workspace_id)
    assert preview is not None
    linked = preview.linked_template_runtime_segments
    assert linked is not None
    segments = {segment["segment_key"]: segment for segment in linked["segments"]}
    assert segments["logo-stanga"]["binding_status"] == "confirmed"
    assert segments["logo-dreapta"]["binding_status"] == "confirmed"
    assert segments["logo-stanga"]["owning_template_code"] == LOGO
    for segment in segments.values():
        codes = [blocker["code"] for blocker in segment["product_truth_readiness"]["blockers"]]
        assert "LINKED_TEMPLATE_BINDING_MISSING" not in codes


def test_recommendation_does_not_write_bindings() -> None:
    payload = {
        "svg_source": {"file_name": "gradi-curat.svg", "upload_status": "analyzed"},
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                _layer("logo-stanga", "logo stanga", "printed_artwork"),
            ],
            "layer_bindings": [],
        },
    }
    build_product_composition_recommendation(payload)
    apply_product_composition_recommendation(payload)

    assert _bindings(payload) == []
