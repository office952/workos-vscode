"""ACM / Bond Axis B — face-treatment commercial path coexistence + honesty."""

from __future__ import annotations

import pytest
import pytest_asyncio

from data.product_system.acp_face_treatment_registry_v1 import (
    FACE_TREATMENT_ACRYLIC_INSERT,
    FACE_TREATMENT_ROUTED_BACKLIT,
    GEOMETRY_ROLE_ACRYLIC_INSERT,
    GEOMETRY_ROLE_CUTOUT_TEXT,
)
from data.product_system.acp_local_face_modules_v1 import (
    INSERT_THICKNESS_OWNER_VARIANT_MM,
    MODULE_ACRYLIC_INSERT,
    MODULE_ROUTED_BACKLIT,
)
from seeds.seed_acm_bond_materials import seed_acm_bond_materials
from seeds.seed_acm_boxed_mounting_owner_rates import seed_acm_boxed_mounting_owner_rates
from seeds.seed_acm_owner_confirmed_prices import seed_acm_owner_confirmed_prices
from seeds.seed_tpl_acm_boxed_mounting_support_v1 import (
    TEMPLATE_CODE,
    seed_tpl_acm_boxed_mounting_support_v1,
)
from services.acm_boxed_support_composition_v1 import (
    PANEL_QUANTITY_KEYS,
    resolve_acm_boxed_composition,
)
from services.acm_face_treatment_commercial_path_v1 import (
    BAG_KEY,
    BLOCKER_OPTICAL_CATALOG_MISSING,
    COEXISTENCE_BOTH,
    COEXISTENCE_INSERT_ONLY,
    COEXISTENCE_NONE,
    COEXISTENCE_ROUTED_ONLY,
    DOMAIN_SCHEMA,
    TREATMENT_QUANTITY_KEYS,
    UI_BADGE_RELIEF_PLEXI_10MM,
    build_cpp_eic_commercial_gate,
    build_quantity_matrix,
    confirm_face_treatments,
    normalize_face_treatments,
    project_for_aggregate,
    project_for_product_definition,
    read_face_treatments,
    readiness_finding_for_template,
    scenario_matrix,
)
from services.acm_quote_input_helpers import merge_acm_boxed_mounting_derived_fields
from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.product_definition_builder_service import ProductDefinitionBuilderService
from services.product_e2e_readiness_service import ProductE2EReadinessService
from services.product_truth_job_confirm_service import (
    apply_pinned_bags_onto_payload,
    extract_typed_bags_from_finish,
)

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]


def _routed_raw(**extra):
    base = {"geometry_role": GEOMETRY_ROLE_CUTOUT_TEXT, "status": "draft"}
    base.update(extra)
    return base


def _insert_raw(**extra):
    base = {"geometry_role": GEOMETRY_ROLE_ACRYLIC_INSERT, "status": "draft"}
    base.update(extra)
    return base


def test_identities_frozen():
    d = normalize_face_treatments(
        {"routed_cutouts": [_routed_raw()], "acrylic_inserts": [_insert_raw()]}
    )
    assert d["schema"] == DOMAIN_SCHEMA
    assert d["routed_cutouts"][0]["face_treatment_code"] == FACE_TREATMENT_ROUTED_BACKLIT
    assert d["routed_cutouts"][0]["module_code"] == MODULE_ROUTED_BACKLIT
    assert d["acrylic_inserts"][0]["face_treatment_code"] == FACE_TREATMENT_ACRYLIC_INSERT
    assert d["acrylic_inserts"][0]["module_code"] == MODULE_ACRYLIC_INSERT
    assert d["acrylic_inserts"][0]["ui_badge"] == UI_BADGE_RELIEF_PLEXI_10MM
    assert d["acrylic_inserts"][0]["confirmed_fields"]["thickness_mm"] == INSERT_THICKNESS_OWNER_VARIANT_MM
    assert d["acrylic_inserts"][0]["confirmed_fields"]["sole_thickness_admitted"] is False


@pytest.mark.parametrize(
    "routed_n,insert_n,expected",
    [
        (0, 0, COEXISTENCE_NONE),
        (1, 0, COEXISTENCE_ROUTED_ONLY),
        (0, 1, COEXISTENCE_INSERT_ONLY),
        (1, 1, COEXISTENCE_BOTH),
    ],
)
def test_coexistence_matrix(routed_n, insert_n, expected):
    d = normalize_face_treatments(
        {
            "routed_cutouts": [_routed_raw() for _ in range(routed_n)],
            "acrylic_inserts": [_insert_raw() for _ in range(insert_n)],
        }
    )
    assert d["coexistence"] == expected
    assert d["orthogonal_to_applied_content_xor"] is True
    assert d["readiness"]["panel_only_blocked_by_absent_treatments"] is False


def test_quantity_keys_do_not_overlap_panel_sheet():
    overlap = PANEL_QUANTITY_KEYS & TREATMENT_QUANTITY_KEYS
    assert not overlap
    d = normalize_face_treatments(
        {"routed_cutouts": [_routed_raw()], "acrylic_inserts": [_insert_raw()]}
    )
    qty = build_quantity_matrix(d)
    assert qty["double_sheet_guard_ok"] is True
    assert qty["key_overlap_with_panel"] == []
    agg = project_for_aggregate(d)
    assert agg["owns_panel_sheet"] is False
    assert agg["materials"] == []


def test_cpp_eic_optical_honestly_blocked():
    d = normalize_face_treatments({"routed_cutouts": [_routed_raw()]})
    gate = build_cpp_eic_commercial_gate(d)
    assert gate["treatment_commercial_lines_allowed"] is False
    assert BLOCKER_OPTICAL_CATALOG_MISSING in gate["blockers"]

    panel_only = build_cpp_eic_commercial_gate(normalize_face_treatments(None))
    assert panel_only["treatment_commercial_lines_allowed"] is False
    assert panel_only["blockers"] == []


def test_orthogonal_to_applied_content_xor():
    """Face treatments do not alter XOR validation."""
    xor = resolve_acm_boxed_composition({"applied_content": "letters"})
    assert xor["xor"]["ok"] is True
    d = normalize_face_treatments(
        {
            "routed_cutouts": [_routed_raw()],
            "acrylic_inserts": [_insert_raw()],
        }
    )
    assert d["coexistence"] == COEXISTENCE_BOTH
    # XOR still letters-only when face treatments both present
    payload = {
        "applied_content": "letters",
        "finish_setup": {BAG_KEY: d},
    }
    xor2 = resolve_acm_boxed_composition(payload)
    assert xor2["xor"]["applied_content"] == "letters"
    assert read_face_treatments(payload)["coexistence"] == COEXISTENCE_BOTH


def test_confirm_and_pd_projection():
    confirmed = confirm_face_treatments(
        {"routed_cutouts": [_routed_raw()], "acrylic_inserts": [_insert_raw()]}
    )
    assert confirmed["status"] == "confirmed"
    assert confirmed["routed_cutouts"][0]["status"] == "confirmed"
    pd = project_for_product_definition(confirmed)
    assert pd["acm_face_treatments"]["coexistence"] == COEXISTENCE_BOTH
    assert pd["acm_face_treatment_quantity_matrix"]["double_sheet_guard_ok"] is True
    assert len(pd["acp_local_face_module_instances_from_face_treatments"]) == 2


def test_typed_bag_pin_roundtrip():
    domain = normalize_face_treatments({"acrylic_inserts": [_insert_raw()]})
    payload = {"finish_setup": {BAG_KEY: domain, "letter_group_instances": []}}
    bags = extract_typed_bags_from_finish(payload)
    assert BAG_KEY in bags
    assert bags[BAG_KEY]["coexistence"] == COEXISTENCE_INSERT_ONLY
    # Simulate pin
    pinned_payload = {
        "finish_setup": {"letter_group_instances": []},
        "product_truth": {
            "confirmed_snapshot_v1": {
                "pinned_typed_bags": bags,
                "metadata": {"contract_version": "job_revision_v1", "revision": 1},
            }
        },
    }
    restored = apply_pinned_bags_onto_payload(pinned_payload)
    assert restored["finish_setup"][BAG_KEY]["coexistence"] == COEXISTENCE_INSERT_ONLY


def test_merge_quote_input_preserves_face_treatments():
    domain = normalize_face_treatments({"routed_cutouts": [_routed_raw()]})
    merged = merge_acm_boxed_mounting_derived_fields(
        {
            "template_code": TEMPLATE_CODE,
            "panel_width_mm": 1200,
            "panel_height_mm": 800,
            "acm_thickness_mm": 3,
            "return_depth_mm": 60,
            "fold_sides": "all",
            "finish_setup": {BAG_KEY: domain},
        }
    )
    assert merged[BAG_KEY]["coexistence"] == COEXISTENCE_ROUTED_ONLY
    assert merged["face_treatment_coexistence"] == COEXISTENCE_ROUTED_ONLY
    assert merged["panel_area_m2"] > 0


def test_readiness_panel_only_not_blocked():
    finding = readiness_finding_for_template({})
    assert finding["check_id"] == "components.acm_face_treatment_commercial_path"
    assert finding["blocking"] is False
    assert finding["status"] == "PASS"
    assert finding["evidence"]["optional_absent_ok"] is True


def test_scenario_matrix_covers_four():
    rows = scenario_matrix()
    names = {r["name"] for r in rows}
    assert names == {"panel_only", "routed_only", "insert_only", "both"}
    both = next(r for r in rows if r["name"] == "both")
    assert both["cpp_eic"]["treatment_commercial_lines_allowed"] is False
    assert both["aggregate"]["double_sheet_guard_ok"] is True


@pytest_asyncio.fixture
async def acm_ft_db(volumetric_v2_db):
    from seeds.seed_inventory_materials_stubs import seed_inventory_material_stubs

    await seed_inventory_material_stubs()
    await seed_acm_bond_materials()
    await seed_acm_owner_confirmed_prices()
    await seed_acm_boxed_mounting_owner_rates()
    await seed_tpl_acm_boxed_mounting_support_v1()
    return volumetric_v2_db


@pytest.mark.asyncio
async def test_pd_standalone_includes_face_treatments(acm_ft_db):
    from services.product_definition_builder_service import _build_acm_standalone_canonical_values

    domain = normalize_face_treatments(
        {"routed_cutouts": [_routed_raw()], "acrylic_inserts": [_insert_raw()]}
    )
    values = _build_acm_standalone_canonical_values(
        {
            "template_code": TEMPLATE_CODE,
            "panel_width_mm": 1200,
            "panel_height_mm": 800,
            "acm_thickness_mm": 3,
            "return_depth_mm": 60,
            "fold_sides": "all",
            "finish_setup": {BAG_KEY: domain},
        }
    )
    assert values[BAG_KEY]["coexistence"] == COEXISTENCE_BOTH
    assert values["acm_face_treatments_aggregate_projection"]["owns_panel_sheet"] is False
    assert values["acm_face_treatment_cpp_eic_gate"]["treatment_commercial_lines_allowed"] is False

    session = acm_ft_db
    pd = await ProductDefinitionBuilderService(session).build_preview(TEMPLATE_CODE)
    assert pd is not None


@pytest.mark.asyncio
async def test_readiness_service_exposes_face_treatment_check(acm_ft_db):
    session = acm_ft_db
    result = await ProductE2EReadinessService(session).run_static(TEMPLATE_CODE)
    check_ids = {f.check_id for f in result.findings}
    assert "components.acm_face_treatment_commercial_path" in check_ids


@pytest.mark.asyncio
async def test_panel_cpp_unaffected_by_face_treatments(acm_ft_db):
    """Panel CPP still emits acm_* lines; treatments do not invent optical lines."""
    session = acm_ft_db
    domain = normalize_face_treatments(
        {"routed_cutouts": [_routed_raw()], "acrylic_inserts": [_insert_raw()]}
    )
    quote_input = {
        "template_code": TEMPLATE_CODE,
        "panel_width_mm": 1000,
        "panel_height_mm": 700,
        "acm_thickness_mm": 3,
        "return_depth_mm": 60,
        "fold_sides": "all",
        "quantity": 1,
        "finish_setup": {BAG_KEY: domain},
    }
    preview = await CommercialPriceProposalService(session).build_preview(
        TEMPLATE_CODE, quote_input=quote_input
    )
    assert preview is not None
    codes = [line.code for line in preview.commercial_price_lines]
    acm_codes = [c for c in codes if c and str(c).startswith("acm_")]
    assert len(acm_codes) == 6
    assert not any(c and "plexiglas" in str(c).lower() for c in codes)
    assert not any(c and "optical" in str(c).lower() for c in codes)
