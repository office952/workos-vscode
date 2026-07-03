import asyncio

from core.database import db_manager
from services.intake_v6_modular_form_contract_service import get_intake_v6_modular_form_contract_service
from services.intake_v6_assembly_preview_service import build_intake_v6_assembly_draft_preview
from services.product_aggregate_service import ProductAggregateService
from services.product_definition_builder_service import ProductDefinitionBuilderService
from seeds.seed_tpl_volumetric_logo_v1 import seed_tpl_volumetric_logo_v1
from schemas.intake_v4 import IntakeV4LayerBindingContract, IntakeV4LayerRoleSetup, IntakeV4ProductBinding, IntakeV4WorkspacePayload


def _payload(bindings: list[IntakeV4LayerBindingContract], template_code: str) -> IntakeV4WorkspacePayload:
    return IntakeV4WorkspacePayload(
        product_binding=IntakeV4ProductBinding(template_code=template_code),
        layer_role_setup=IntakeV4LayerRoleSetup(
            confirmation_status="complete",
            layers=[],
            layer_bindings=bindings,
            warnings=[],
        ),
    )


def _binding(layer_key: str, *, role: str, target_template_code: str | None = None, binding_status: str = "confirmed") -> IntakeV4LayerBindingContract:
    return IntakeV4LayerBindingContract(
        layer_key=layer_key,
        suggested_semantic_role=role,
        confirmed_semantic_role=role,
        target_template_code=target_template_code,
        binding_status=binding_status,
    )


def test_seed_logo_templates_and_aggregate_live():
    async def scenario():
        await db_manager.init_db()
        try:
            await db_manager.create_tables()
            stats = await seed_tpl_volumetric_logo_v1()
            rerun_stats = await seed_tpl_volumetric_logo_v1()
            async with db_manager.async_session_maker() as session:
                aggregate = await ProductAggregateService(session).build("TPL-VOLUMETRIC-LOGO_v1")
                product_definition = await ProductDefinitionBuilderService(session).build_preview("TPL-VOLUMETRIC-LOGO_v1")
            return stats, rerun_stats, aggregate, product_definition
        finally:
            await db_manager.close_db()

    stats, rerun_stats, aggregate, product_definition = asyncio.run(scenario())

    assert stats["template_code"] == "TPL-VOLUMETRIC-LOGO_v1"
    assert rerun_stats["created_templates"] == 0
    assert rerun_stats["created_dossiers"] == 0
    assert rerun_stats["created_links"] == 0
    assert aggregate is not None
    assert aggregate.template_code == "TPL-VOLUMETRIC-LOGO_v1"
    assert len(aggregate.components) >= 6
    assert len(aggregate.modules.required) == 6
    assert [module.child_template_code for module in aggregate.modules.required] == [
        "TPL-VOLUMETRIC-LOGO-FACE_v1",
        "TPL-VOLUMETRIC-LOGO-FINISH_v1",
        "TPL-VOLUMETRIC-LOGO-RETURN_v1",
        "TPL-VOLUMETRIC-LOGO-BACK_v1",
        "TPL-VOLUMETRIC-LOGO-LIGHTING_v1",
        "TPL-VOLUMETRIC-LOGO-MOUNTING_v1",
    ]
    assert [component.component_id for component in aggregate.components] == [
        "comp_logo_face",
        "comp_logo_finish",
        "comp_logo_return",
        "comp_logo_back",
        "comp_logo_lighting",
        "comp_logo_mounting",
    ]
    assert product_definition is not None
    assert product_definition.template_code == "TPL-VOLUMETRIC-LOGO_v1"


def test_logo_modular_form_contract_stays_ok_after_seed():
    contract = get_intake_v6_modular_form_contract_service().get_for_template("TPL-VOLUMETRIC-LOGO_v1")

    assert contract is not None
    assert contract.summary.active_module_count >= 6


def test_logo_only_assembly_preview_produces_volumetric_logo_component():
    payload = _payload([
        _binding("logo-only", role="logo", target_template_code="TPL-VOLUMETRIC-LOGO_v1", binding_status="confirmed"),
    ], "TPL-VOLUMETRIC-LOGO_v1")

    assembly, _warnings = build_intake_v6_assembly_draft_preview(workspace_id="ws_logo_only", payload=payload)

    assert assembly.assembly_type == "logo_only"
    assert len(assembly.component_instances) == 1
    assert assembly.component_instances[0].component_type == "volumetric_logo"


def test_letters_logo_assembly_preview_keeps_both_components():
    payload = _payload([
        _binding("maria", role="face"),
        _binding("logo-left", role="logo", target_template_code="TPL-VOLUMETRIC-LOGO_v1", binding_status="confirmed"),
    ], "TPL-VOLUMETRIC-LETTERS_v2")

    assembly, _warnings = build_intake_v6_assembly_draft_preview(workspace_id="ws_letters_logo", payload=payload)

    assert assembly.assembly_type == "letters_logo"
    assert {component.component_type for component in assembly.component_instances} == {"volumetric_letters", "volumetric_logo"}