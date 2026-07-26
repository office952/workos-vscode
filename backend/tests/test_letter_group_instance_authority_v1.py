"""LetterGroupInstance authority — identity, lifecycle, projection, quantities, placement."""

from __future__ import annotations

from services.letter_group_instance_authority import (
    build_volumetric_letters_commercial_quantities,
    coalesce_letter_group_authority_for_finish,
    hydrate_instances_from_legacy,
    project_instances_to_legacy_finishes,
    read_letter_group_instances,
)


def _legacy_row(group_key: str, *, confirmed: bool = False, **extra):
    return {
        "group_key": group_key,
        "layer_name": group_key,
        "source_fill_color": "#ff0000",
        "face_area_m2": 0.1,
        "perimeter_m": 1.2,
        "element_count": 3,
        "face_finish_type": "oracal_651",
        "face_oracal_code": "030",
        "return_finish_type": "oracal_651",
        "return_depth_mm": 60,
        "backing_mode": "closed_back",
        "confirmed": confirmed,
        **extra,
    }


def test_hydrate_once_from_legacy_mints_uuid():
    finish = {
        "illuminated": True,
        "lighting_system_type": "led_modules",
        "letter_led_module_count": 12,
        "letter_group_finishes": [_legacy_row("pseudo:a"), _legacy_row("pseudo:b")],
    }
    instances = hydrate_instances_from_legacy(finish, svg_hash="abc")
    assert len(instances) == 2
    ids = {i["instance_id"] for i in instances}
    assert len(ids) == 2
    assert all(len(i["instance_id"]) >= 32 for i in instances)
    assert instances[0]["lighting"]["illuminated"] is True
    assert instances[0]["lighting"]["led_module_count"] is None  # workspace total remains qty fallback
    # Second hydrate from instances must not remint
    finish2 = {**finish, "letter_group_instances": instances}
    again = hydrate_instances_from_legacy(finish2)
    assert [i["instance_id"] for i in again] == [i["instance_id"] for i in instances]


def test_omit_instances_does_not_wipe():
    prior = hydrate_instances_from_legacy(
        {"letter_group_finishes": [_legacy_row("pseudo:a", confirmed=True)]}
    )
    existing = {
        "letter_group_instances": prior,
        "letter_group_finishes": project_instances_to_legacy_finishes(prior),
    }
    out = coalesce_letter_group_authority_for_finish(
        {"confirmed": True},  # omit instances + finishes
        existing,
    )
    assert read_letter_group_instances(out)[0]["instance_id"] == prior[0]["instance_id"]
    assert out["letter_group_finishes"][0]["group_key"] == "pseudo:a"


def test_instance_wins_over_stale_legacy():
    prior = hydrate_instances_from_legacy(
        {"letter_group_finishes": [_legacy_row("pseudo:a", confirmed=True, face_oracal_code="030")]}
    )
    prior[0]["materials"]["face_oracal_code"] = "070"
    existing = {"letter_group_instances": prior}
    out = coalesce_letter_group_authority_for_finish(
        {
            "letter_group_finishes": [_legacy_row("pseudo:a", confirmed=True, face_oracal_code="999")],
            # no instances in payload — must preserve prior instances, not rehydrate from stale legacy
        },
        existing,
    )
    assert out["letter_group_instances"][0]["materials"]["face_oracal_code"] == "070"
    assert out["letter_group_finishes"][0]["face_oracal_code"] == "070"


def test_one_way_projection_no_circular_fields():
    prior = hydrate_instances_from_legacy({"letter_group_finishes": [_legacy_row("pseudo:a")]})
    legacy = project_instances_to_legacy_finishes(prior)
    assert "instance_id" not in legacy[0]
    assert "lighting" not in legacy[0]
    assert "provenance" not in legacy[0]


def test_uuid_stable_on_reorder():
    rows = [_legacy_row("pseudo:a"), _legacy_row("pseudo:b")]
    first = hydrate_instances_from_legacy({"letter_group_finishes": rows})
    by_key = {i["group_key"]: i["instance_id"] for i in first}
    reordered = coalesce_letter_group_authority_for_finish(
        {"letter_group_instances": [first[1], first[0]]},
        {"letter_group_instances": first},
    )
    assert {i["group_key"]: i["instance_id"] for i in reordered["letter_group_instances"]} == by_key


def test_confirmed_orphan_preserved_on_key_drop():
    prior = hydrate_instances_from_legacy(
        {
            "letter_group_finishes": [
                _legacy_row("pseudo:keep", confirmed=True),
                _legacy_row("pseudo:gone", confirmed=True),
            ]
        }
    )
    keep_only = [i for i in prior if i["group_key"] == "pseudo:keep"]
    out = coalesce_letter_group_authority_for_finish(
        {"letter_group_instances": keep_only},
        {"letter_group_instances": prior},
    )
    keys = {i["group_key"] for i in out["letter_group_instances"]}
    assert keys == {"pseudo:keep", "pseudo:gone"}
    gone = next(i for i in out["letter_group_instances"] if i["group_key"] == "pseudo:gone")
    assert gone["instance_id"] == next(i["instance_id"] for i in prior if i["group_key"] == "pseudo:gone")


def test_split_ambiguity_new_keys_get_new_uuids():
    """Split: old key gone, two new keys → new UUIDs; confirmed orphan kept."""
    prior = hydrate_instances_from_legacy(
        {"letter_group_finishes": [_legacy_row("pseudo:old", confirmed=True)]}
    )
    new_a = {**prior[0], "group_key": "pseudo:a", "instance_id": ""}
    new_b = {**prior[0], "group_key": "pseudo:b", "instance_id": ""}
    # Clear ids to simulate FE minting for new keys
    del new_a["instance_id"]
    del new_b["instance_id"]
    out = coalesce_letter_group_authority_for_finish(
        {"letter_group_instances": [new_a, new_b]},
        {"letter_group_instances": prior},
    )
    ids = [i["instance_id"] for i in out["letter_group_instances"]]
    assert len(set(ids)) == 3  # a, b, orphan old
    assert prior[0]["instance_id"] in ids
    assert prior[0]["instance_id"] not in {
        i["instance_id"] for i in out["letter_group_instances"] if i["group_key"] in {"pseudo:a", "pseudo:b"}
    }


def test_new_group_gets_new_uuid():
    prior = hydrate_instances_from_legacy({"letter_group_finishes": [_legacy_row("pseudo:a")]})
    incoming = [
        prior[0],
        {
            **prior[0],
            "group_key": "pseudo:new",
            "instance_id": "",
        },
    ]
    del incoming[1]["instance_id"]
    out = coalesce_letter_group_authority_for_finish(
        {"letter_group_instances": incoming},
        {"letter_group_instances": prior},
    )
    by_key = {i["group_key"]: i["instance_id"] for i in out["letter_group_instances"]}
    assert by_key["pseudo:a"] == prior[0]["instance_id"]
    assert by_key["pseudo:new"] != prior[0]["instance_id"]
    assert len(by_key["pseudo:new"]) >= 32


def test_lighting_instance_authority_not_overwritten_by_global():
    prior = hydrate_instances_from_legacy(
        {
            "illuminated": True,
            "letter_led_module_count": 10,
            "letter_group_finishes": [_legacy_row("pseudo:a"), _legacy_row("pseudo:b")],
        }
    )
    prior[0]["lighting"] = {
        "illuminated": True,
        "lighting_system_type": "led_modules",
        "light_color": "white",
        "led_module_count": 4,
        "selected_psu_watts": None,
    }
    prior[1]["lighting"] = {
        "illuminated": False,
        "lighting_system_type": None,
        "light_color": None,
        "led_module_count": None,
        "selected_psu_watts": None,
    }
    # Incoming omits lighting — must preserve per-instance
    stripped = [{k: v for k, v in i.items() if k != "lighting"} for i in prior]
    out = coalesce_letter_group_authority_for_finish(
        {"letter_group_instances": stripped, "illuminated": True, "letter_led_module_count": 99},
        {"letter_group_instances": prior},
    )
    a = next(i for i in out["letter_group_instances"] if i["group_key"] == "pseudo:a")
    b = next(i for i in out["letter_group_instances"] if i["group_key"] == "pseudo:b")
    assert a["lighting"]["led_module_count"] == 4
    assert b["lighting"]["illuminated"] is False


def test_placement_acm_and_standalone():
    finish_acm = {
        "letter_group_finishes": [_legacy_row("pseudo:a")],
        "acm_panel_instance": {"component_instance_id": "acm-1"},
    }
    out_acm = coalesce_letter_group_authority_for_finish(finish_acm, None)
    assert out_acm["component_placements"][0]["target_kind"] == "acm_panel"
    assert out_acm["component_placements"][0]["target_instance_id"] == "acm-1"

    finish_none = {"letter_group_finishes": [_legacy_row("pseudo:a")]}
    out_none = coalesce_letter_group_authority_for_finish(finish_none, None)
    assert out_none["component_placements"][0]["target_kind"] == "none"


def test_placement_wall_frame_totem_faces():
    instances = hydrate_instances_from_legacy(
        {"letter_group_finishes": [_legacy_row(f"pseudo:{k}") for k in ("w", "f", "a", "b")]}
    )
    placements = [
        {
            "schema": "component_placement_v1",
            "placement_id": "p1",
            "source_instance_id": instances[0]["instance_id"],
            "target_kind": "wall",
            "target_instance_id": None,
            "target_face": None,
            "mounting_method": None,
        },
        {
            "schema": "component_placement_v1",
            "placement_id": "p2",
            "source_instance_id": instances[1]["instance_id"],
            "target_kind": "metal_frame",
            "target_instance_id": "frame-1",
            "target_face": None,
            "mounting_method": "screw",
        },
        {
            "schema": "component_placement_v1",
            "placement_id": "p3",
            "source_instance_id": instances[2]["instance_id"],
            "target_kind": "totem_face",
            "target_instance_id": "totem-1",
            "target_face": "A",
            "mounting_method": None,
        },
        {
            "schema": "component_placement_v1",
            "placement_id": "p4",
            "source_instance_id": instances[3]["instance_id"],
            "target_kind": "totem_face",
            "target_instance_id": "totem-1",
            "target_face": "B",
            "mounting_method": None,
        },
    ]
    out = coalesce_letter_group_authority_for_finish(
        {"letter_group_instances": instances, "component_placements": placements},
        None,
    )
    kinds = {p["placement_id"]: p for p in out["component_placements"]}
    assert kinds["p1"]["target_kind"] == "wall"
    assert kinds["p2"]["target_kind"] == "metal_frame"
    assert kinds["p3"]["target_face"] == "A"
    assert kinds["p4"]["target_face"] == "B"


def test_quantity_builder_sole_source_fields():
    finish = {
        "letter_group_finishes": [
            _legacy_row("pseudo:a", face_area_m2=0.2, perimeter_m=1.0),
            _legacy_row("pseudo:b", face_area_m2=0.3, perimeter_m=2.0),
        ],
        "letter_led_module_count": 8,
    }
    instances = hydrate_instances_from_legacy(finish)
    finish["letter_group_instances"] = instances
    qty = build_volumetric_letters_commercial_quantities(
        quote_geometry={"letter_perimeter_m": 9.5},
        finish_setup=finish,
    )
    assert qty["source"] == "letter_group_instance_authority"
    assert qty["letter_face_area_m2"] == 0.5
    assert qty["letter_perimeter_m"] == 9.5  # CPP outer from geometry
    assert qty["led_module_count"] == 8
    assert qty["cost_engine_legacy"] is True


def test_no_hash_in_instance_id():
    instances = hydrate_instances_from_legacy(
        {"letter_group_finishes": [_legacy_row("pseudo:a")]},
        svg_hash="deadbeef" * 4,
    )
    assert "deadbeef" not in instances[0]["instance_id"]
    assert instances[0]["artwork_reference"]["source_svg_hash"] == "deadbeef" * 4
