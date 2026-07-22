"""ACM boxed support composition Decision A — XOR letters|logo + optional frame."""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import select

from models.product_template_module_links import ProductTemplateModuleLink
from seeds.seed_acm_bond_materials import seed_acm_bond_materials
from seeds.seed_acm_boxed_mounting_owner_rates import seed_acm_boxed_mounting_owner_rates
from seeds.seed_acm_owner_confirmed_prices import seed_acm_owner_confirmed_prices
from seeds.seed_tpl_acm_boxed_mounting_support_v1 import (
    TEMPLATE_CODE,
    seed_tpl_acm_boxed_mounting_support_v1,
)
from services.acm_boxed_support_composition_v1 import (
    APPLIED_CONTENT_LETTERS,
    APPLIED_CONTENT_LOGO,
    APPLIED_CONTENT_TRIGGER_FIELD,
    BLOCKER_APPLIED_CONTENT_XOR,
    BLOCKER_LOGO_BRANCH_CANDIDATE,
    LETTERS_PACK_TEMPLATE_CODES,
    LOGO_ROOT,
    resolve_acm_boxed_composition,
    validate_applied_content_xor,
)
from services.acm_quote_input_helpers import merge_acm_boxed_mounting_derived_fields
from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.estimated_internal_cost_service import EstimatedInternalCostService
from services.product_aggregate_service import ProductAggregateService
from services.product_definition_builder_service import ProductDefinitionBuilderService
from services.product_definition_composition_contract import build_product_definition_composition
from services.product_e2e_readiness_service import ProductE2EReadinessService

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]


def _standalone_quote_input(**extra):
    base = {
        "template_code": TEMPLATE_CODE,
        "panel_width_mm": 1200,
        "panel_height_mm": 800,
        "acm_thickness_mm": 3,
        "return_depth_mm": 60,
        "rear_lip_mm": 25,
        "fold_sides": "all",
        "quantity": 1,
    }
    base.update(extra)
    return base


@pytest_asyncio.fixture
async def acm_composition_db(volumetric_v2_db):
    import json

    from models.product_templates import Product_templates
    from seeds.seed_inventory_materials_stubs import seed_inventory_material_stubs

    session = volumetric_v2_db
    existing_logo = (
        await session.execute(
            select(Product_templates).where(Product_templates.template_code == LOGO_ROOT)
        )
    ).scalar_one_or_none()
    if existing_logo is None:
        session.add(
            Product_templates(
                template_code=LOGO_ROOT,
                family_id="logo_volumetric",
                family_name="Logo volumetric",
                description="Candidate logo root fixture for ACM composition XOR",
                components_json=json.dumps([]),
                operations_json=json.dumps([]),
                required_materials_json=json.dumps([]),
                active=True,
            )
        )
        await session.commit()

    await seed_inventory_material_stubs()
    await seed_acm_bond_materials()
    await seed_acm_owner_confirmed_prices()
    await seed_acm_boxed_mounting_owner_rates()
    await seed_tpl_acm_boxed_mounting_support_v1()
    return volumetric_v2_db


def test_xor_rejects_letters_and_logo_together() -> None:
    result = validate_applied_content_xor(
        applied_content=APPLIED_CONTENT_LETTERS,
        letters_active=True,
        logo_active=True,
    )
    assert result["ok"] is False
    assert BLOCKER_APPLIED_CONTENT_XOR in result["blockers"]


def test_logo_branch_honestly_blocked() -> None:
    result = resolve_acm_boxed_composition({"applied_content": APPLIED_CONTENT_LOGO})
    assert BLOCKER_LOGO_BRANCH_CANDIDATE in result["xor"]["blockers"]
    assert result["xor"]["logo_branch_status"] == "honestly_blocked_candidate"


def test_frame_optional_operator_explicit_no_threshold() -> None:
    off = resolve_acm_boxed_composition({"applied_content": "none"})
    assert off["metal_frame"]["enabled"] is False
    assert off["metal_frame"]["automatic_threshold_applied"] is False

    on = resolve_acm_boxed_composition(
        {
            "applied_content": "letters",
            "finish_setup": {
                "mounting_solution": {
                    "configuration": {"internal_frame_enabled": True},
                }
            },
        }
    )
    assert on["metal_frame"]["enabled"] is True
    assert on["metal_frame"]["selection_source"] == "operator_explicit"


def test_standalone_composition_letters_emits_pack_edges() -> None:
    composition = build_product_definition_composition(
        root_template_code=TEMPLATE_CODE,
        payload={"applied_content": APPLIED_CONTENT_LETTERS, "quote_geometry": {}},
        source_payload_type="template_preview",
        standalone_root=True,
    )
    child_codes = {n.template_code for n in composition.nodes if n.parent_node_id}
    assert set(LETTERS_PACK_TEMPLATE_CODES).issubset(child_codes)
    assert LOGO_ROOT not in child_codes
    assert composition.compatibility_status in {"compatible", "partial"}


def test_standalone_composition_xor_hostile_payload_blocked() -> None:
    composition = build_product_definition_composition(
        root_template_code=TEMPLATE_CODE,
        payload={"applied_content": APPLIED_CONTENT_LETTERS, "force_letters_and_logo": True},
        source_payload_type="template_preview",
        standalone_root=True,
    )
    assert BLOCKER_APPLIED_CONTENT_XOR in composition.blockers
    assert composition.compatibility_status == "blocked"


@pytest.mark.asyncio
async def test_seed_creates_applied_content_outbound_links(acm_composition_db) -> None:
    session = acm_composition_db
    rows = (
        await session.execute(
            select(ProductTemplateModuleLink).where(
                ProductTemplateModuleLink.parent_template_code == TEMPLATE_CODE,
                ProductTemplateModuleLink.trigger_field == APPLIED_CONTENT_TRIGGER_FIELD,
                ProductTemplateModuleLink.active.is_(True),
            )
        )
    ).scalars().all()
    by_child = {r.module_template_code: r for r in rows}
    for code in LETTERS_PACK_TEMPLATE_CODES:
        assert code in by_child
        assert by_child[code].pricing_mode == "separate_quote_line"
    assert LOGO_ROOT in by_child
    assert by_child[LOGO_ROOT].usage_mode == "linked_child"


@pytest.mark.asyncio
async def test_aggregate_panel_bom_excludes_applied_content_children(acm_composition_db) -> None:
    session = acm_composition_db
    aggregate = await ProductAggregateService(session).build(TEMPLATE_CODE)
    assert aggregate is not None
    # Composition edges visible as optional modules
    optional_codes = {m.child_template_code for m in aggregate.modules.optional}
    assert set(LETTERS_PACK_TEMPLATE_CODES).issubset(optional_codes)
    assert LOGO_ROOT in optional_codes
    # Panel materials remain ACM-owned — no letter face material folded in
    letter_mats = [
        m
        for m in aggregate.materials
        if m.source_template_code in LETTERS_PACK_TEMPLATE_CODES
    ]
    assert letter_mats == []
    bond_rows = [
        m for m in aggregate.materials if m.material_code == "MAT-ACM-BOND-PANEL"
    ]
    assert bond_rows


@pytest.mark.asyncio
async def test_cpp_eic_panel_only_unchanged_line_count(acm_composition_db) -> None:
    session = acm_composition_db
    quote_input = _standalone_quote_input(applied_content="none")
    cpp = await CommercialPriceProposalService(session).build_preview(
        TEMPLATE_CODE, quote_input=quote_input
    )
    assert cpp is not None
    acm_lines = [line for line in cpp.commercial_price_lines if line.code.startswith("acm_")]
    assert len(acm_lines) == 6

    eic = await EstimatedInternalCostService(session).build_preview(
        TEMPLATE_CODE, quote_input=quote_input
    )
    assert eic is not None
    # Anti-hourly: composition extension must not introduce hourly contamination.
    assert eic.hourly_contamination_detected == []


@pytest.mark.asyncio
async def test_merge_preserves_applied_content_and_frame(acm_composition_db) -> None:
    merged = merge_acm_boxed_mounting_derived_fields(
        _standalone_quote_input(
            applied_content="letters",
            metal_frame_enabled=True,
        )
    )
    assert merged["applied_content"] == "letters"
    assert merged["metal_frame_enabled"] is True
    assert merged["panel_area_m2"] == pytest.approx(0.96, rel=1e-3)


@pytest.mark.asyncio
async def test_pd_standalone_preview_still_builds(acm_composition_db) -> None:
    session = acm_composition_db
    pd = await ProductDefinitionBuilderService(session).build_preview(TEMPLATE_CODE)
    assert pd is not None
    assert pd.composition is not None
    assert pd.composition.composition_mode == "standalone_root"
    assert {m.module_code for m in pd.selected_modules} == {"structura_suport"}


@pytest.mark.asyncio
async def test_readiness_reports_acm_xor_and_logo_honesty(acm_composition_db) -> None:
    session = acm_composition_db
    result = await ProductE2EReadinessService(session).run_static(TEMPLATE_CODE)
    check_ids = {f.check_id for f in result.findings}
    assert "components.acm_applied_content_xor_contract" in check_ids
    assert "components.acm_logo_branch_honesty" in check_ids
    logo_finding = next(
        f for f in result.findings if f.check_id == "components.acm_logo_branch_honesty"
    )
    # Optional capability: honesty warning must not BLOCK base shell publication.
    assert logo_finding.status == "PASS_WITH_WARNINGS"
    assert logo_finding.blocking is False
    assert logo_finding.evidence.get("optional_capability") is True
