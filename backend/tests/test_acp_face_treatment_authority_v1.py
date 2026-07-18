"""ACP face-treatment authority + FinishSetup persistence foundation."""

from __future__ import annotations

from data.product_system.acp_face_treatment_registry_v1 import (
    FACE_TREATMENT_ACRYLIC_INSERT,
    FACE_TREATMENT_APPLIED_VOLUMETRIC,
    FACE_TREATMENT_NOT_APPLICABLE,
    FACE_TREATMENT_ROUTED_BACKLIT,
    READINESS_INACTIVE,
    READINESS_LOCAL_CONFIGURATION_REQUIRED,
    READINESS_NOT_APPLICABLE,
    get_face_treatment,
    legacy_light_routed_policy,
    list_face_treatments,
)
from schemas.intake_v4 import IntakeV4FinishSetup
from services.svg_component_binding_persistence import (
    build_face_treatment_readiness_summary,
    build_svg_component_instances,
    normalize_svg_component_bindings,
    persist_normalized_bindings_on_finish,
    sync_support_selection_from_bindings,
    validate_bindings_for_new_selection,
)


def _support_binding() -> dict:
    return {
        "binding_id": "bind_support_cc_shell",
        "geometry_role": "SUPPORT_CONTOUR",
        "component_template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
        "selection_mode": "CLOSED_CONTOUR",
        "selected_geometry": {
            "layer_ids": [],
            "group_ids": [],
            "element_ids": ["cc_shell"],
            "geometry_hashes": ["h_shell"],
            "source_svg_hash": "svg1",
        },
        "configuration": {"fold_count": 2, "l1_mm": 60, "l2_mm": 25},
        "status": "CONFIRMED",
    }


def _letters_binding() -> dict:
    return {
        "binding_id": "bind_letters_L1",
        "geometry_role": "LETTER_VECTOR_SET",
        "component_template_code": "TPL-VOLUMETRIC-FACE_v1",
        "selection_mode": "LAYER_OR_GROUP",
        "selected_geometry": {
            "layer_ids": ["layer_letters"],
            "group_ids": [],
            "element_ids": [],
            "geometry_hashes": [],
            "source_svg_hash": "svg1",
        },
        "configuration": {},
        "status": "CONFIRMED",
        "face_treatment_code": FACE_TREATMENT_APPLIED_VOLUMETRIC,
    }


def _cutout_binding() -> dict:
    return {
        "binding_id": "bind_cutout_text_z1",
        "geometry_role": "CUTOUT_TEXT",
        "component_template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
        "selection_mode": "LAYER_OR_GROUP",
        "selected_geometry": {
            "layer_ids": ["layer_cutout"],
            "group_ids": [],
            "element_ids": ["el_cutout"],
            "geometry_hashes": ["h_cut"],
            "source_svg_hash": "svg1",
        },
        "configuration": {},
        "status": "CONFIRMED",
        "face_treatment_code": FACE_TREATMENT_ROUTED_BACKLIT,
        "confirmation_status": "CONFIRMED",
    }


def _insert_binding() -> dict:
    return {
        "binding_id": "bind_insert_z2",
        "geometry_role": "ACRYLIC_INSERT",
        "component_template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
        "selection_mode": "LAYER_OR_GROUP",
        "selected_geometry": {
            "layer_ids": ["layer_insert"],
            "group_ids": [],
            "element_ids": ["el_insert"],
            "geometry_hashes": ["h_ins"],
            "source_svg_hash": "svg1",
        },
        "configuration": {},
        "status": "CONFIRMED",
        "face_treatment_code": FACE_TREATMENT_ACRYLIC_INSERT,
        "confirmation_status": "CONFIRMED",
    }


def test_registry_lists_active_treatments_and_separates_concepts() -> None:
    codes = {t["code"] for t in list_face_treatments()}
    assert FACE_TREATMENT_ROUTED_BACKLIT in codes
    assert FACE_TREATMENT_ACRYLIC_INSERT in codes
    routed = get_face_treatment(FACE_TREATMENT_ROUTED_BACKLIT)
    assert routed is not None
    assert "CUTOUT_TEXT" in routed["allowed_geometry_roles"]
    assert routed["requires_local_module"] is True
    # Geometry role is not a treatment code
    assert get_face_treatment("CUTOUT_TEXT") is None


def test_legacy_light_routed_not_v6_authority() -> None:
    policy = legacy_light_routed_policy()
    assert policy["intake_v6_composition_authority"] is False
    assert policy["face_treatment_authority"] is False
    assert policy["status"] == "PARALLEL_LEGACY_COST_PATH"


def test_multiple_treatments_coexist_no_global_xor() -> None:
    bindings = [_support_binding(), _letters_binding(), _cutout_binding(), _insert_binding()]
    blockers = validate_bindings_for_new_selection(bindings)
    assert blockers == []
    normalized = normalize_svg_component_bindings(bindings)
    assert len(normalized) == 4
    zones = {b["local_zone_id"] for b in normalized}
    assert len(zones) == 4
    assert all(z.startswith("zone_") for z in zones)


def test_unknown_treatment_rejected() -> None:
    bad = _cutout_binding()
    bad["face_treatment_code"] = "FACE-TREATMENT-FAKE"
    blockers = validate_bindings_for_new_selection([_support_binding(), bad])
    assert any("Unknown face_treatment_code" in b for b in blockers)


def test_light_routed_binding_rejected() -> None:
    blockers = validate_bindings_for_new_selection(
        [
            {
                "binding_id": "x",
                "geometry_role": "SUPPORT_CONTOUR",
                "component_template_code": "TPL-ACP-LIGHT-ROUTED",
                "status": "CONFIRMED",
                "selected_geometry": {
                    "element_ids": ["a"],
                    "layer_ids": [],
                    "group_ids": [],
                    "geometry_hashes": [],
                    "source_svg_hash": None,
                },
            }
        ]
    )
    assert any("LIGHT-ROUTED" in b for b in blockers)


def test_old_payload_missing_treatment_compatible() -> None:
    legacy = _support_binding()
    assert "face_treatment_code" not in legacy
    blockers = validate_bindings_for_new_selection([legacy])
    assert blockers == []
    norm = normalize_svg_component_bindings([legacy])[0]
    assert norm["face_treatment_code"] == FACE_TREATMENT_NOT_APPLICABLE
    readiness = build_face_treatment_readiness_summary({"svg_component_bindings": [legacy]})
    # Shell-only NOT_APPLICABLE does not invent warnings
    assert readiness["warnings"] == []


def test_finish_setup_round_trip_preserves_treatments() -> None:
    raw = {
        "svg_component_bindings": [
            _support_binding(),
            _letters_binding(),
            _cutout_binding(),
            _insert_binding(),
        ]
    }
    finish = persist_normalized_bindings_on_finish(raw)
    finish = sync_support_selection_from_bindings(finish)
    model = IntakeV4FinishSetup.model_validate(finish)
    dumped = model.model_dump(mode="json")
    codes = {b["face_treatment_code"] for b in dumped["svg_component_bindings"]}
    assert FACE_TREATMENT_ROUTED_BACKLIT in codes
    assert FACE_TREATMENT_ACRYLIC_INSERT in codes
    assert dumped["svg_support_selection"]["contour_id"] == "cc_shell"
    # Stable zone ids survive dump
    zones_before = {b["local_zone_id"] for b in finish["svg_component_bindings"]}
    zones_after = {b["local_zone_id"] for b in dumped["svg_component_bindings"]}
    assert zones_before == zones_after


def test_pd_instances_nest_shell_treatments_letters_separate() -> None:
    finish = persist_normalized_bindings_on_finish(
        {
            "svg_component_bindings": [
                _support_binding(),
                _letters_binding(),
                _cutout_binding(),
                _insert_binding(),
            ]
        }
    )
    instances = build_svg_component_instances(finish)
    by_role = {i["geometry_role"]: i for i in instances}
    assert "LETTER_VECTOR_SET" in by_role
    assert "SUPPORT_CONTOUR" in by_role
    shell_fts = by_role["SUPPORT_CONTOUR"]["face_treatment_instances"]
    ft_codes = {f["face_treatment_code"] for f in shell_fts}
    assert FACE_TREATMENT_ROUTED_BACKLIT in ft_codes
    assert FACE_TREATMENT_ACRYLIC_INSERT in ft_codes
    # Applied letters are not nested under ACP shell
    assert FACE_TREATMENT_APPLIED_VOLUMETRIC not in ft_codes
    for ft in shell_fts:
        if ft["face_treatment_code"] == FACE_TREATMENT_ROUTED_BACKLIT:
            assert ft["readiness"] == READINESS_LOCAL_CONFIGURATION_REQUIRED
            assert ft["local_configuration_status"] == "NOT_CONFIGURED"


def test_inactive_treatment_zero_warnings() -> None:
    inactive = _cutout_binding()
    inactive["status"] = "INACTIVE"
    inactive["confirmation_status"] = "INACTIVE"
    summary = build_face_treatment_readiness_summary(
        {"svg_component_bindings": [_support_binding(), inactive]}
    )
    assert summary["warnings"] == []
    assert any(i["readiness"] == READINESS_INACTIVE for i in summary["items"])


def test_legacy_letter_readiness_not_applicable() -> None:
    letter = _letters_binding()
    del letter["face_treatment_code"]
    norm = normalize_svg_component_bindings([letter])[0]
    assert norm["face_treatment_code"] == FACE_TREATMENT_NOT_APPLICABLE
    from services.svg_component_binding_persistence import evaluate_face_treatment_readiness

    r = evaluate_face_treatment_readiness(norm)
    assert r["readiness"] == READINESS_NOT_APPLICABLE


def test_stable_zone_id_independent_of_array_order() -> None:
    a = normalize_svg_component_bindings([_cutout_binding(), _insert_binding()])
    b = normalize_svg_component_bindings([_insert_binding(), _cutout_binding()])
    zones_a = {x["binding_id"]: x["local_zone_id"] for x in a}
    zones_b = {x["binding_id"]: x["local_zone_id"] for x in b}
    assert zones_a == zones_b


def test_incompatible_role_treatment_rejected() -> None:
    bad = _cutout_binding()
    bad["face_treatment_code"] = FACE_TREATMENT_ACRYLIC_INSERT
    blockers = validate_bindings_for_new_selection([bad])
    assert any("incompatible with geometry_role" in b for b in blockers)


# --- HTTP FinishSetup round-trip (auth_client) ---

import json

import pytest
from sqlalchemy import delete

from models.intake_v6_workspace import IntakeV6WorkspaceRecord

WS_FACE_ID = "acp-face-treatment-foundation-ws"
WS_FACE_CODE = "IV6-ACP-FACE-FT"
SVG_HASH = "c" * 64


def _complete_roles_payload() -> dict:
    return {
        "product_binding": {
            "template_code": "TPL-VOLUMETRIC-LETTERS_v2",
            "template_label": "Litere volumetrice",
            "product_family": "litere_volumetrice",
        },
        "svg_source": {
            "file_name": "LITERE-ACP-MIXED-FACE.svg",
            "file_size_bytes": 1200,
            "file_hash": SVG_HASH,
            "upload_status": "analyzed",
        },
        "svg_analysis_json": {
            "schemaVersion": "1.10.0",
            "layers": [
                {"id": "layer_letters", "name": "litere", "perimeterMl": 2.0, "filledAreaSqm": 0.1},
                {"id": "layer_cutout", "name": "decupat", "perimeterMl": 1.0, "filledAreaSqm": 0.05},
                {"id": "layer_insert", "name": "insert", "perimeterMl": 0.5, "filledAreaSqm": 0.02},
            ],
            "parts": {"count": 3, "nestableCount": 3},
            "geometry": {"perimeterMl": 3.5},
            "closedContourCandidates": {"candidate_count": 1, "unit_ambiguity": False},
        },
        "quote_geometry": {
            "letter_count": 2,
            "letter_perimeter_m": 3.0,
            "face_area_m2": 0.15,
            "confirmed": True,
        },
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "layer_letters",
                    "layer_id": "layer_letters",
                    "layer_name": "litere",
                    "auto_role": "face",
                    "auto_confidence": "high",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                },
                {
                    "layer_key": "layer_cutout",
                    "layer_id": "layer_cutout",
                    "layer_name": "decupat",
                    "auto_role": "face",
                    "auto_confidence": "medium",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                },
                {
                    "layer_key": "layer_insert",
                    "layer_id": "layer_insert",
                    "layer_name": "insert",
                    "auto_role": "face",
                    "auto_confidence": "medium",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                },
            ],
            "warnings": [],
        },
    }


def _mixed_face_finish_body() -> dict:
    return {
        "confirmed": False,
        "illuminated": True,
        "svg_component_bindings": [
            {
                **_support_binding(),
                "selected_geometry": {
                    "layer_ids": [],
                    "group_ids": [],
                    "element_ids": ["cc_shell"],
                    "geometry_hashes": ["h_shell"],
                    "source_svg_hash": SVG_HASH,
                },
            },
            {
                **_letters_binding(),
                "selected_geometry": {
                    "layer_ids": ["layer_letters"],
                    "group_ids": [],
                    "element_ids": [],
                    "geometry_hashes": [],
                    "source_svg_hash": SVG_HASH,
                },
            },
            {
                **_cutout_binding(),
                "selected_geometry": {
                    "layer_ids": ["layer_cutout"],
                    "group_ids": [],
                    "element_ids": ["el_cutout"],
                    "geometry_hashes": ["h_cut"],
                    "source_svg_hash": SVG_HASH,
                },
            },
            {
                **_insert_binding(),
                "selected_geometry": {
                    "layer_ids": ["layer_insert"],
                    "group_ids": [],
                    "element_ids": ["el_insert"],
                    "geometry_hashes": ["h_ins"],
                    "source_svg_hash": SVG_HASH,
                },
            },
        ],
        "mounting_solution": {
            "kind": "product_system_template",
            "template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
            "configuration": {
                "panel_width_mm": 2000.0,
                "panel_height_mm": 700.0,
                "dimension_source": "svg_support_selection",
            },
        },
    }


@pytest.fixture
def face_treatment_workspace(db_fixture):
    from tests.test_product_aggregate_volumetric_v2 import _seed_volumetric_v2_fixture

    async def _seed():
        async with db_fixture.session_maker() as session:
            await _seed_volumetric_v2_fixture(session)
            await session.execute(
                delete(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == WS_FACE_ID)
            )
            session.add(
                IntakeV6WorkspaceRecord(
                    id=WS_FACE_ID,
                    workspace_code=WS_FACE_CODE,
                    title="ACP face treatment foundation",
                    template_code="TPL-VOLUMETRIC-LETTERS_v2",
                    status="draft",
                    payload_json=json.dumps(_complete_roles_payload()),
                    readiness_status="draft",
                    created_by_user_id="test-user-id",
                    updated_by_user_id="test-user-id",
                )
            )
            await session.commit()

    db_fixture.run(_seed())
    return WS_FACE_ID


def test_http_mixed_face_finish_setup_save_and_refresh(auth_client, face_treatment_workspace) -> None:
    """Runtime foundation: save mixed-face bindings; GET preserves identities + readiness."""
    put = auth_client.put(
        f"/api/v1/intake-v6/workspaces/{face_treatment_workspace}/finish-setup",
        json=_mixed_face_finish_body(),
    )
    assert put.status_code == 200, put.text
    finish = (put.json().get("payload") or {}).get("finish_setup") or {}
    bindings = finish.get("svg_component_bindings") or []
    by_role = {b["geometry_role"]: b for b in bindings if isinstance(b, dict)}
    assert "SUPPORT_CONTOUR" in by_role
    assert "LETTER_VECTOR_SET" in by_role
    assert "CUTOUT_TEXT" in by_role
    assert "ACRYLIC_INSERT" in by_role
    assert by_role["CUTOUT_TEXT"]["face_treatment_code"] == FACE_TREATMENT_ROUTED_BACKLIT
    assert by_role["ACRYLIC_INSERT"]["face_treatment_code"] == FACE_TREATMENT_ACRYLIC_INSERT
    assert by_role["CUTOUT_TEXT"]["local_zone_id"].startswith("zone_")
    zone_cut = by_role["CUTOUT_TEXT"]["local_zone_id"]
    zone_ins = by_role["ACRYLIC_INSERT"]["local_zone_id"]

    get = auth_client.get(f"/api/v1/intake-v6/workspaces/{face_treatment_workspace}")
    assert get.status_code == 200, get.text
    finish2 = (get.json().get("payload") or {}).get("finish_setup") or {}
    bindings2 = {b["geometry_role"]: b for b in (finish2.get("svg_component_bindings") or [])}
    assert bindings2["CUTOUT_TEXT"]["local_zone_id"] == zone_cut
    assert bindings2["ACRYLIC_INSERT"]["local_zone_id"] == zone_ins
    assert bindings2["CUTOUT_TEXT"]["face_treatment_code"] == FACE_TREATMENT_ROUTED_BACKLIT

    from services.svg_component_binding_persistence import (
        build_face_treatment_readiness_summary,
        build_svg_component_instances,
    )

    instances = build_svg_component_instances(finish2)
    shell = next(i for i in instances if i.get("geometry_role") == "SUPPORT_CONTOUR")
    ft_codes = {f["face_treatment_code"] for f in shell.get("face_treatment_instances") or []}
    assert FACE_TREATMENT_ROUTED_BACKLIT in ft_codes
    assert FACE_TREATMENT_ACRYLIC_INSERT in ft_codes
    readiness = build_face_treatment_readiness_summary(finish2)
    assert any(
        w.get("code") == "FACE_TREATMENT_LOCAL_MODULE_REQUIRED" for w in readiness.get("warnings") or []
    )
    # no global XOR — all four roles present after refresh
    assert len(bindings2) >= 4
