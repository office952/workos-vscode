from __future__ import annotations

import pytest

from schemas.intake_v4 import IntakeV4LayerRoleSetup, IntakeV4LayerRoleLayer
from services.intake_v4_layer_role_service import (
    _SELECTED_LAYER_ROLE_MAP,
    derive_selected_layer_refs_from_setup,
    selected_layer_refs_runtime_state,
    sync_selected_layer_refs_on_payload,
)


def _layer(
    *,
    layer_key: str,
    layer_id: str | None = None,
    confirmed_role: str | None = None,
    confirmation_state: str = "confirmed",
    auto_role: str | None = None,
) -> IntakeV4LayerRoleLayer:
    return IntakeV4LayerRoleLayer(
        layer_key=layer_key,
        layer_id=layer_id if layer_id is not None else layer_key,
        layer_name=layer_key,
        auto_role=auto_role if auto_role is not None else (confirmed_role or "unknown"),
        auto_confidence="high",
        confirmed_role=confirmed_role,
        confirmation_state=confirmation_state,
    )


def _setup(*layers: IntakeV4LayerRoleLayer, confirmation_status: str = "complete") -> IntakeV4LayerRoleSetup:
    return IntakeV4LayerRoleSetup(
        confirmation_status=confirmation_status,
        layers=list(layers),
        warnings=[],
    )


def test_face_derives_vector_litere() -> None:
    refs = derive_selected_layer_refs_from_setup(_setup(_layer(layer_key="a", confirmed_role="face")))
    assert len(refs) == 1
    assert refs[0].role == "vector_litere"


def test_printed_artwork_derives_vector_logo() -> None:
    refs = derive_selected_layer_refs_from_setup(
        _setup(_layer(layer_key="logo-1", confirmed_role="printed_artwork"))
    )
    assert len(refs) == 1
    assert refs[0].role == "vector_logo"


def test_legacy_logo_alias_derives_vector_logo() -> None:
    refs = derive_selected_layer_refs_from_setup(_setup(_layer(layer_key="logo-1", confirmed_role="logo")))
    assert len(refs) == 1
    assert refs[0].role == "vector_logo"


def test_unknown_role_does_not_derive_ref() -> None:
    refs = derive_selected_layer_refs_from_setup(
        _setup(
            _layer(layer_key="face-1", confirmed_role="face"),
            _layer(layer_key="x-1", confirmed_role="mounting_hole"),
        )
    )
    assert len(refs) == 1
    assert refs[0].layer_id == "face-1"


def test_ignored_role_does_not_derive_ref() -> None:
    refs = derive_selected_layer_refs_from_setup(
        _setup(
            _layer(layer_key="face-1", confirmed_role="face"),
            _layer(layer_key="hole-1", confirmed_role="face", confirmation_state="ignored"),
        )
    )
    assert len(refs) == 1


def test_unconfirmed_role_does_not_derive_ref() -> None:
    runtime = selected_layer_refs_runtime_state(
        _setup(
            _layer(layer_key="face-1", confirmed_role="face", confirmation_state="pending"),
            confirmation_status="partial",
        )
    )
    assert runtime["status"] == "unconfirmed"
    assert runtime["refs"] == []


def test_mixed_four_letters_two_logos() -> None:
    layers = [
        _layer(layer_key=f"letter-{idx}", confirmed_role="face")
        for idx in range(1, 5)
    ] + [
        _layer(layer_key="logo-left", confirmed_role="printed_artwork"),
        _layer(layer_key="logo-right", confirmed_role="printed_artwork"),
    ]
    refs = derive_selected_layer_refs_from_setup(_setup(*layers))
    assert [ref.role for ref in refs] == [
        "vector_litere",
        "vector_litere",
        "vector_litere",
        "vector_litere",
        "vector_logo",
        "vector_logo",
    ]
    assert [ref.layer_id for ref in refs] == [
        "letter-1",
        "letter-2",
        "letter-3",
        "letter-4",
        "logo-left",
        "logo-right",
    ]


def test_duplicate_layer_id_is_ambiguous() -> None:
    runtime = selected_layer_refs_runtime_state(
        _setup(
            _layer(layer_key="a", layer_id="dup", confirmed_role="face"),
            _layer(layer_key="b", layer_id="dup", confirmed_role="face"),
        )
    )
    assert runtime["status"] == "ambiguous"


def test_sync_persists_refs_and_preserves_unrelated_svg_metadata() -> None:
    setup = _setup(_layer(layer_key="face-1", confirmed_role="face"))
    payload: dict = {"svg": {"analysis_version": "1.10.0", "other": {"keep": True}}}
    sync_selected_layer_refs_on_payload(payload, setup)
    assert payload["svg"]["analysis_version"] == "1.10.0"
    assert payload["svg"]["other"] == {"keep": True}
    assert payload["svg"]["selected_layer_refs"] == [
        {
            "layer_id": "face-1",
            "role": "vector_litere",
            "source": "operator_confirmed_layer_role",
            "confirmed": True,
        }
    ]


def test_sync_is_idempotent() -> None:
    setup = _setup(_layer(layer_key="face-1", confirmed_role="face"))
    payload: dict = {"svg": {}}
    sync_selected_layer_refs_on_payload(payload, setup)
    first = payload["svg"]["selected_layer_refs"]
    sync_selected_layer_refs_on_payload(payload, setup)
    assert payload["svg"]["selected_layer_refs"] == first


def test_sync_removes_derived_ref_when_role_removed() -> None:
    setup = _setup(_layer(layer_key="face-1", confirmed_role="face"))
    payload: dict = {"svg": {}}
    sync_selected_layer_refs_on_payload(payload, setup)
    assert payload["svg"]["selected_layer_refs"]

    empty_setup = _setup(
        _layer(layer_key="face-1", confirmed_role="face", confirmation_state="ignored")
    )
    sync_selected_layer_refs_on_payload(payload, empty_setup)
    assert payload["svg"]["selected_layer_refs"] == []


def test_complete_setup_with_no_eligible_roles_persists_empty_array() -> None:
    setup = _setup(
        _layer(layer_key="hole-1", confirmed_role="mounting_hole"),
    )
    payload: dict = {"svg": {"analysis_version": "1.10.0"}}
    sync_selected_layer_refs_on_payload(payload, setup)
    assert payload["svg"]["selected_layer_refs"] == []


def test_unconfirmed_setup_does_not_persist_refs() -> None:
    setup = _setup(
        _layer(layer_key="face-1", confirmed_role="face", confirmation_state="pending"),
        confirmation_status="partial",
    )
    payload: dict = {"svg": {"selected_layer_refs": [{"layer_id": "stale"}]}}
    sync_selected_layer_refs_on_payload(payload, setup)
    assert payload.get("svg") is None or payload.get("svg", {}).get("selected_layer_refs") in {None, []}


def test_role_map_includes_printed_artwork_and_legacy_logo() -> None:
    assert _SELECTED_LAYER_ROLE_MAP["face"] == "vector_litere"
    assert _SELECTED_LAYER_ROLE_MAP["printed_artwork"] == "vector_logo"
    assert _SELECTED_LAYER_ROLE_MAP["logo"] == "vector_logo"
