import asyncio
import json
from types import SimpleNamespace

from schemas.intake_v4 import (
    IntakeV4LayerBindingContract,
    IntakeV4MaterialBreakdownResponse,
    IntakeV4MaterialQuantityRow,
    IntakeV4NestingPreviewBoundary,
    IntakeV4NestingPreviewPartRow,
    IntakeV4NestingPreviewResponse,
    IntakeV4LayerRoleSetup,
    IntakeV4CncOperationRow,
    IntakeV4ProductBinding,
    IntakeV4WorkspacePayload,
)
from schemas.intake_v6_assembly import AssemblyDraft, ComponentInstance, OperationCandidate, OperationCandidateMeasure
from services.intake_v6_assembly_preview_service import (
    build_intake_v6_assembly_draft_preview,
    build_intake_v6_assembly_preview_bundle,
    compile_intake_v6_operation_candidates_preview,
    compile_intake_v6_consolidated_tasks_preview,
)
from services.intake_v6_production_preview_service import build_v6_task_preview_response
from services.intake_v6_modular_form_contract_service import get_intake_v6_modular_form_contract_service
from services.template_architecture_scope import resolve_runtime_template_code
from services import intake_v6_workspace_service as workspace_service


def _payload(bindings: list[IntakeV4LayerBindingContract]) -> IntakeV4WorkspacePayload:
    return IntakeV4WorkspacePayload(
        product_binding=IntakeV4ProductBinding(template_code="TPL-VOLUMETRIC-LETTERS_v2"),
        layer_role_setup=IntakeV4LayerRoleSetup(
            confirmation_status="complete",
            layers=[],
            layer_bindings=bindings,
            warnings=[],
        ),
    )


def _payload_from_layers(layers: list[dict[str, str]]) -> IntakeV4WorkspacePayload:
    return IntakeV4WorkspacePayload(
        product_binding=IntakeV4ProductBinding(template_code="TPL-VOLUMETRIC-LETTERS_v2"),
        layer_role_setup=IntakeV4LayerRoleSetup.model_validate(
            {
                "confirmation_status": "missing",
                "layers": layers,
                "warnings": ["additional_template_binding_confirmation_required"],
            }
        ),
    )


def _breakdown(
    *,
    material_rows: list[IntakeV4MaterialQuantityRow] | None = None,
    parts: list[IntakeV4NestingPreviewPartRow] | None = None,
    operation_rows: list[IntakeV4CncOperationRow] | None = None,
) -> IntakeV4MaterialBreakdownResponse:
    return IntakeV4MaterialBreakdownResponse(
        workspace_id="ws_test",
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        material_rows=material_rows or [],
        operation_rows=operation_rows or [],
        nesting_preview=IntakeV4NestingPreviewResponse(
            disclaimer="test preview",
            boundary=IntakeV4NestingPreviewBoundary(),
            parts=parts or [],
        ),
    )


def _binding(
    layer_key: str,
    *,
    role: str,
    target_template_code: str | None = None,
    binding_status: str = "confirmed",
) -> IntakeV4LayerBindingContract:
    return IntakeV4LayerBindingContract(
        layer_key=layer_key,
        suggested_semantic_role=role,
        confirmed_semantic_role=role,
        target_template_code=target_template_code,
        binding_status=binding_status,
    )


def test_assembly_preview_letters_only():
    payload = _payload([
        _binding("maria", role="face"),
        _binding("soare", role="face"),
    ])

    assembly, warnings = build_intake_v6_assembly_draft_preview(workspace_id="ws_letters", payload=payload)

    assert assembly.assembly_type == "letters_only"
    assert len(assembly.component_instances) == 1
    assert assembly.component_instances[0].component_type == "volumetric_letters"
    assert warnings == []


def test_assembly_preview_logo_only():
    payload = _payload([
        _binding("logo_left", role="logo", target_template_code="TPL-VOLUMETRIC-LOGO_v1", binding_status="suggested"),
    ])

    assembly, warnings = build_intake_v6_assembly_draft_preview(workspace_id="ws_logo", payload=payload)

    assert assembly.assembly_type == "logo_only"
    assert len(assembly.component_instances) == 1
    assert assembly.component_instances[0].component_type == "volumetric_logo"
    assert assembly.component_instances[0].binding_status == "suggested"
    assert assembly.component_instances[0].required_fields_status == "partial"
    assert "runtime_target_not_product_template_live" in warnings[0]


def test_assembly_preview_letters_and_logo():
    payload = _payload([
        _binding("maria", role="face"),
        _binding("logo_left", role="logo", target_template_code="TPL-VOLUMETRIC-LOGO_v1", binding_status="suggested"),
    ])

    assembly, _warnings = build_intake_v6_assembly_draft_preview(workspace_id="ws_mix", payload=payload)

    assert assembly.assembly_type == "letters_logo"
    assert {component.component_type for component in assembly.component_instances} == {
        "volumetric_letters",
        "volumetric_logo",
    }


def test_assembly_preview_falls_back_to_layers_when_bindings_missing():
    payload = _payload_from_layers(
        [
            {
                "layer_key": "pseudo:maria",
                "layer_id": "pseudo:maria",
                "layer_name": "pseudo maria (blue)",
                "auto_role": "face",
                "auto_confidence": "high",
                "confirmation_state": "pending",
            },
            {
                "layer_key": "logo-stanga",
                "layer_id": "logo-stanga",
                "layer_name": "logo stanga",
                "auto_role": "printed_artwork",
                "auto_confidence": "high",
                "confirmation_state": "pending",
            },
        ]
    )

    assembly, warnings = build_intake_v6_assembly_draft_preview(workspace_id="IR-MR18L96M", payload=payload)

    assert assembly.assembly_type == "letters_logo"
    assert {component.component_type for component in assembly.component_instances} == {
        "volumetric_letters",
        "volumetric_logo",
    }
    assert "runtime_target_not_product_template_live" in warnings[0]


def test_bundle_consolidates_letters_and_logo_face_plexi_3mm():
    payload = _payload([
        _binding("maria", role="face"),
        _binding("logo_left", role="logo", target_template_code="TPL-VOLUMETRIC-LOGO_v1", binding_status="suggested"),
    ])

    assembly, _warnings = build_intake_v6_assembly_draft_preview(workspace_id="IR-MR18L96M", payload=payload)
    breakdown = _breakdown(
        material_rows=[
            IntakeV4MaterialQuantityRow(
                material_key="plexiglas_face",
                display_name="Plexi face",
                category="material",
                quantity=1.6,
                unit="m2",
                quantity_source="real",
                quantity_quality="estimated",
                quantity_with_waste=1.6,
                material_code="MAT-ACP-FATA-LITERE",
                material_name="Plexi 3mm",
                quantity_basis="sheet_nesting_role_split_quote_estimate",
                base_quantity=1.6,
            )
        ],
        parts=[
            IntakeV4NestingPreviewPartRow(
                part_id="part_letters_1",
                source_layer_name="maria",
                layer_role="face",
                part_kind="face_part",
                material_intent="face",
                nestable=True,
                counts_as_material_piece=True,
                area_sqm=1.0,
                counted_in_material_lines=["plexiglas_face"],
            ),
            IntakeV4NestingPreviewPartRow(
                part_id="part_logo_1",
                source_layer_name="logo_left",
                layer_role="face",
                part_kind="face_part",
                material_intent="face",
                nestable=True,
                counts_as_material_piece=True,
                area_sqm=0.6,
                counted_in_material_lines=["plexiglas_face"],
            ),
        ],
        operation_rows=[
            IntakeV4CncOperationRow(
                key="cnc_face_cutting_plexiglas_3mm",
                display_name="CNC face",
                operation_type="cutting",
                material_key="plexiglas_3mm",
                thickness_mm=3.0,
                quantity=25.0,
                unit="ml",
                basis_key="cut",
                basis_label="cut",
                machine_type="cnc_router",
                workcenter_code="WC_CNC_ROUTING",
                operational_operation_code="cnc_cutting",
            )
        ],
    )
    candidates, warnings = compile_intake_v6_operation_candidates_preview(assembly, payload, breakdown)
    tasks, task_warnings = compile_intake_v6_consolidated_tasks_preview(candidates)

    assert assembly.assembly_type == "letters_logo"
    assert len(candidates) == 2
    assert len(tasks) == 1
    assert set(tasks[0].consolidated_from_components) == {"cmp_volumetric_letters", "cmp_volumetric_logo"}
    assert tasks[0].total_area == 1.6
    assert any(
        candidate.provenance.get("warning") == "runtime_target_not_product_template_live"
        for candidate in candidates
    )
    assert task_warnings == []


def test_consolidation_separates_different_thickness():
    candidates = [
        OperationCandidate(
            candidate_id="opc_letters",
            assembly_id="asm_sep",
            component_id="cmp_letters",
            source_template_code="TPL-VOLUMETRIC-LETTERS_v2",
            operation_type="face_cnc_cut",
            process_type="cnc_sheet_cutting",
            material_family="plexiglass",
            material_code="PLEXI_FACE",
            thickness_mm=3.0,
            finish_code="face_standard",
            color_code="opal",
            machine_type="cnc_router",
            workcenter="WC_CNC",
            setup_group_key="cnc_router|plexi|3mm|opal",
            dependency_group="pre_assembly_faces",
            geometry_refs=["geom:letters"],
            quantity=OperationCandidateMeasure(unit="sqm", value=1.0),
            estimated_time=OperationCandidateMeasure(unit="min", value=10.0),
            consolidation_allowed=True,
            provenance={},
        ),
        OperationCandidate(
            candidate_id="opc_logo",
            assembly_id="asm_sep",
            component_id="cmp_logo",
            source_template_code="TPL-VOLUMETRIC-LOGO_v1",
            operation_type="logo_face_cut",
            process_type="cnc_sheet_cutting",
            material_family="plexiglass",
            material_code="PLEXI_FACE",
            thickness_mm=5.0,
            finish_code="face_standard",
            color_code="opal",
            machine_type="cnc_router",
            workcenter="WC_CNC",
            setup_group_key="cnc_router|plexi|5mm|opal",
            dependency_group="pre_assembly_faces",
            geometry_refs=["geom:logo"],
            quantity=OperationCandidateMeasure(unit="sqm", value=1.0),
            estimated_time=OperationCandidateMeasure(unit="min", value=10.0),
            consolidation_allowed=True,
            provenance={},
        ),
    ]

    tasks, warnings = compile_intake_v6_consolidated_tasks_preview(candidates)

    assert len(tasks) == 2
    assert all("total_area_missing" in warning for warning in warnings)


def test_missing_material_candidate_requires_separation_reason():
    candidate = OperationCandidate(
        candidate_id="opc_missing",
        assembly_id="asm_missing",
        component_id="cmp_missing",
        source_template_code="TPL-VOLUMETRIC-LOGO_v1",
        operation_type="logo_face_cut",
        process_type="cnc_sheet_cutting",
        material_family=None,
        material_code=None,
        thickness_mm=None,
        finish_code=None,
        color_code=None,
        machine_type=None,
        workcenter=None,
        setup_group_key=None,
        dependency_group="pre_assembly_faces",
        geometry_refs=[],
        quantity=OperationCandidateMeasure(unit="sqm", value=None),
        estimated_time=OperationCandidateMeasure(unit="min", value=None),
        consolidation_allowed=False,
        separation_reason="missing_material_code",
        provenance={},
    )

    tasks, warnings = compile_intake_v6_consolidated_tasks_preview([candidate])

    assert len(tasks) == 1
    assert tasks[0].separation_notes == ["missing_material_code"]
    assert "missing_material_code" in warnings[0]


def test_operation_candidate_uses_real_material_mapping_when_available():
    payload = _payload([
        _binding("maria", role="face"),
    ])
    assembly, _warnings = build_intake_v6_assembly_draft_preview(workspace_id="ws_real_material", payload=payload)
    breakdown = _breakdown(
        material_rows=[
            IntakeV4MaterialQuantityRow(
                material_key="plexiglas_face",
                display_name="Plexi face",
                category="material",
                quantity=1.2,
                unit="m2",
                quantity_source="real",
                quantity_quality="estimated",
                quantity_with_waste=1.2,
                material_code="MAT-ACP-FATA-LITERE",
                material_name="Plexi 3mm",
                quantity_basis="sheet_nesting_role_split_quote_estimate",
                base_quantity=1.2,
            )
        ],
        operation_rows=[
            IntakeV4CncOperationRow(
                key="cnc_face_cutting_plexiglas_3mm",
                display_name="CNC face",
                operation_type="cutting",
                material_key="plexiglas_3mm",
                thickness_mm=3.0,
                quantity=25.0,
                unit="ml",
                basis_key="cut",
                basis_label="cut",
                machine_type="cnc_router",
                workcenter_code="WC_CNC_ROUTING",
                operational_operation_code="cnc_cutting",
            )
        ],
    )

    candidates, warnings = compile_intake_v6_operation_candidates_preview(assembly, payload, breakdown)

    assert len(candidates) == 1
    assert candidates[0].material_code == "MAT-ACP-FATA-LITERE"
    assert candidates[0].thickness_mm == 3.0
    assert candidates[0].machine_type == "cnc_router"
    assert candidates[0].workcenter == "WC_CNC_ROUTING"
    assert candidates[0].geometry_source == "layer_key_fallback"
    assert warnings == ["candidate:opc_cmp_volumetric_letters_face:geometry_fallback_used"]


def test_operation_candidate_geometry_propagates_total_area_to_consolidated_task():
    payload = _payload([
        _binding("maria", role="face"),
        _binding("logo_left", role="logo", target_template_code="TPL-VOLUMETRIC-LOGO_v1", binding_status="suggested"),
    ])
    assembly, _warnings = build_intake_v6_assembly_draft_preview(workspace_id="ws_geo", payload=payload)
    breakdown = _breakdown(
        material_rows=[
            IntakeV4MaterialQuantityRow(
                material_key="plexiglas_face",
                display_name="Plexi face",
                category="material",
                quantity=1.2,
                unit="m2",
                quantity_source="real",
                quantity_quality="estimated",
                quantity_with_waste=1.2,
                material_code="MAT-ACP-FATA-LITERE",
                material_name="Plexi 3mm",
                quantity_basis="sheet_nesting_role_split_quote_estimate",
                base_quantity=1.2,
            ),
            IntakeV4MaterialQuantityRow(
                material_key="artwork_logo-left_print_vinyl",
                display_name="Logo print",
                category="material",
                quantity=0.4,
                unit="m2",
                quantity_source="real",
                quantity_quality="estimated",
                quantity_with_waste=0.4,
                material_code="MAT-VINYL-PRINT",
                material_name="Print vinyl",
                quantity_basis="print_area_quote_estimate",
                base_quantity=0.4,
            ),
        ],
        parts=[
            IntakeV4NestingPreviewPartRow(
                part_id="part_letters_1",
                source_layer_name="maria",
                layer_role="face",
                part_kind="face_part",
                material_intent="face",
                nestable=True,
                counts_as_material_piece=True,
                area_sqm=1.2,
                counted_in_material_lines=["plexiglas_face"],
            ),
            IntakeV4NestingPreviewPartRow(
                part_id="part_logo_1",
                source_layer_name="logo_left",
                layer_role="printed_artwork",
                part_kind="artwork_part",
                nestable=False,
                counts_as_material_piece=False,
                area_sqm=0.4,
                counted_in_material_lines=["artwork_*_print_vinyl"],
            ),
        ],
        operation_rows=[
            IntakeV4CncOperationRow(
                key="cnc_face_cutting_plexiglas_3mm",
                display_name="CNC face",
                operation_type="cutting",
                material_key="plexiglas_3mm",
                thickness_mm=3.0,
                quantity=25.0,
                unit="ml",
                basis_key="cut",
                basis_label="cut",
                machine_type="cnc_router",
                workcenter_code="WC_CNC_ROUTING",
                operational_operation_code="cnc_cutting",
            ),
            IntakeV4CncOperationRow(
                key="artwork_logo-left_print_service",
                display_name="Print",
                operation_type="print_vinyl",
                quantity=0.4,
                unit="m2",
                basis_key="print",
                basis_label="print",
                workcenter_code="LARGE_FORMAT_PRINT",
            ),
        ],
    )

    candidates, _warnings = compile_intake_v6_operation_candidates_preview(assembly, payload, breakdown)
    tasks, task_warnings = compile_intake_v6_consolidated_tasks_preview(candidates)

    assert candidates[0].geometry_refs == ["part_letters_1"]
    assert candidates[0].geometry_source == "nesting_preview_parts"
    assert candidates[0].total_area == 1.2
    assert len(tasks) == 2
    letters_task = next(task for task in tasks if task.material_code == "MAT-ACP-FATA-LITERE")
    assert letters_task.total_area == 1.2
    assert any("candidate:opc_cmp_volumetric_logo_face:logo_template_not_product_system_live" == warning for warning in _warnings)
    assert any("candidate:opc_cmp_volumetric_logo_face:candidate_not_consolidated_missing_material" == warning for warning in _warnings)
    assert task_warnings == ["candidate:opc_cmp_volumetric_logo_face:candidate_not_consolidated_missing_material"]


def test_geometry_fallback_marks_candidate():
    payload = _payload([
        _binding("maria", role="face"),
    ])
    assembly, _warnings = build_intake_v6_assembly_draft_preview(workspace_id="ws_fallback", payload=payload)

    candidates, warnings = compile_intake_v6_operation_candidates_preview(assembly, payload, None)

    assert candidates[0].geometry_source == "layer_key_fallback"
    assert "geometry_fallback_used" in candidates[0].warnings
    assert any("geometry_fallback_used" in warning for warning in warnings)


def test_same_material_and_thickness_consolidates_total_area_sum():
    candidates = [
        OperationCandidate(
            candidate_id="opc_letters",
            assembly_id="asm_same",
            component_id="cmp_letters",
            source_template_code="TPL-VOLUMETRIC-LETTERS_v2",
            operation_type="face_cnc_cut",
            process_type="cnc_sheet_cutting",
            material_family="plexiglass",
            material_code="PLEXI_FACE",
            thickness_mm=3.0,
            finish_code="face_standard",
            color_code="opal",
            machine_type="cnc_router",
            workcenter="WC_CNC",
            setup_group_key="cnc_router|plexi|3mm|opal",
            dependency_group="pre_assembly_faces",
            geometry_refs=["geom:letters"],
            geometry_source="nesting_preview_parts",
            quantity=OperationCandidateMeasure(unit="sqm", value=1.0),
            total_area=1.0,
            total_perimeter=2.0,
            estimated_time=OperationCandidateMeasure(unit="min", value=10.0),
            consolidation_allowed=True,
            provenance={},
        ),
        OperationCandidate(
            candidate_id="opc_logo",
            assembly_id="asm_same",
            component_id="cmp_logo",
            source_template_code="TPL-VOLUMETRIC-LOGO_v1",
            operation_type="logo_face_cut",
            process_type="cnc_sheet_cutting",
            material_family="plexiglass",
            material_code="PLEXI_FACE",
            thickness_mm=3.0,
            finish_code="face_standard",
            color_code="opal",
            machine_type="cnc_router",
            workcenter="WC_CNC",
            setup_group_key="cnc_router|plexi|3mm|opal",
            dependency_group="pre_assembly_faces",
            geometry_refs=["geom:logo"],
            geometry_source="nesting_preview_parts",
            quantity=OperationCandidateMeasure(unit="sqm", value=0.5),
            total_area=0.5,
            total_perimeter=1.0,
            estimated_time=OperationCandidateMeasure(unit="min", value=5.0),
            consolidation_allowed=True,
            provenance={},
        ),
    ]

    tasks, _warnings = compile_intake_v6_consolidated_tasks_preview(candidates)

    assert len(tasks) == 1
    assert tasks[0].total_area == 1.5
    assert tasks[0].total_perimeter == 3.0


def test_v6_task_preview_response_includes_read_only_assembly_previews():
    payload = _payload([
        _binding("maria", role="face"),
        _binding("logo_left", role="logo", target_template_code="TPL-VOLUMETRIC-LOGO_v1", binding_status="suggested"),
    ])
    bundle = build_intake_v6_assembly_preview_bundle(
        workspace_id="IR-MR18L96M",
        payload=payload,
    )

    response = build_v6_task_preview_response(
        workspace_id="IR-MR18L96M",
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        payload=payload,
        assembly_preview_bundle=bundle,
    )

    assert response.assembly_draft_preview is not None
    assert response.assembly_draft_preview.assembly_type == "letters_logo"
    assert len(response.operation_candidates_preview) == 2
    assert len(response.consolidated_tasks_preview) == 2
    assert any("runtime_target_not_product_template_live" in warning for warning in response.consolidation_warnings)


def test_v6_task_preview_response_leaves_assembly_preview_empty_without_bundle():
    payload = _payload([
        _binding("maria", role="face"),
        _binding("logo_left", role="logo", target_template_code="TPL-VOLUMETRIC-LOGO_v1", binding_status="suggested"),
    ])

    response = build_v6_task_preview_response(
        workspace_id="IR-MR18L96M",
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        payload=payload,
    )

    assert response.assembly_draft_preview is None
    assert response.operation_candidates_preview == []
    assert response.consolidated_tasks_preview == []
    assert response.consolidation_warnings == []


def test_workspace_service_attaches_rich_assembly_preview_bundle(monkeypatch):
    payload = _payload([
        _binding("maria", role="face"),
        _binding("logo-left", role="logo", target_template_code="TPL-VOLUMETRIC-LOGO_v1", binding_status="suggested"),
    ])
    payload_raw = payload.model_dump(mode="json")
    rich_bundle = build_intake_v6_assembly_preview_bundle(
        workspace_id="IR-MR18L96M",
        payload=payload,
        breakdown=_breakdown(
            material_rows=[
                IntakeV4MaterialQuantityRow(
                    material_key="plexiglas_face",
                    display_name="Plexi face",
                    category="material",
                    quantity=1.2,
                    unit="m2",
                    quantity_source="real",
                    quantity_quality="estimated",
                    quantity_with_waste=1.2,
                    material_code="MAT-ACP-FATA-LITERE",
                    material_name="Plexi 3mm",
                    quantity_basis="sheet_nesting_role_split_quote_estimate",
                    base_quantity=1.2,
                ),
                IntakeV4MaterialQuantityRow(
                    material_key="artwork_logo-left_print_vinyl",
                    display_name="Logo print",
                    category="material",
                    quantity=0.4,
                    unit="m2",
                    quantity_source="real",
                    quantity_quality="estimated",
                    quantity_with_waste=0.4,
                    material_code="MAT-VINYL-PRINT",
                    material_name="Print vinyl",
                    quantity_basis="print_area_quote_estimate",
                    base_quantity=0.4,
                ),
            ],
            parts=[
                IntakeV4NestingPreviewPartRow(
                    part_id="part_letters_1",
                    source_layer_name="maria",
                    layer_role="face",
                    part_kind="face_part",
                    material_intent="face",
                    nestable=True,
                    counts_as_material_piece=True,
                    area_sqm=1.2,
                    counted_in_material_lines=["plexiglas_face"],
                ),
                IntakeV4NestingPreviewPartRow(
                    part_id="part_logo_1",
                    source_layer_name="logo-left",
                    layer_role="printed_artwork",
                    part_kind="artwork_part",
                    nestable=False,
                    counts_as_material_piece=False,
                    area_sqm=0.4,
                    counted_in_material_lines=["artwork_*_print_vinyl"],
                ),
            ],
            operation_rows=[
                IntakeV4CncOperationRow(
                    key="cnc_face_cutting_plexiglas_3mm",
                    display_name="CNC face",
                    operation_type="cutting",
                    material_key="plexiglas_3mm",
                    thickness_mm=3.0,
                    quantity=25.0,
                    unit="ml",
                    basis_key="cut",
                    basis_label="cut",
                    machine_type="cnc_router",
                    workcenter_code="WC_CNC_ROUTING",
                    operational_operation_code="cnc_cutting",
                ),
                IntakeV4CncOperationRow(
                    key="artwork_logo-left_print_service",
                    display_name="Print",
                    operation_type="print_vinyl",
                    quantity=0.4,
                    unit="m2",
                    basis_key="print",
                    basis_label="print",
                    workcenter_code="LARGE_FORMAT_PRINT",
                ),
            ],
        ),
    )

    async def fake_get_record_or_404(_db, _workspace_id):
        return SimpleNamespace(payload_json=json.dumps(payload_raw))

    async def fake_resolve_product_template_or_raise(_db, _template_code):
        return SimpleNamespace(template_code=_template_code)

    async def fake_build_bundle_from_payload_raw(*, db, workspace_id, payload, payload_raw):
        return rich_bundle

    monkeypatch.setattr(workspace_service, "_get_record_or_404", fake_get_record_or_404)
    monkeypatch.setattr(workspace_service, "resolve_product_template_or_raise", fake_resolve_product_template_or_raise)
    monkeypatch.setattr(
        workspace_service,
        "build_intake_v6_assembly_preview_bundle_from_payload_raw",
        fake_build_bundle_from_payload_raw,
    )

    response = asyncio.run(
        workspace_service.get_task_preview_for_workspace(
            db=object(),
            workspace_id="IR-MR18L96M",
        )
    )

    assert response.preview_engine.endswith("+v6_assembly_preview")
    assert response.assembly_draft_preview is not None
    assert response.assembly_draft_preview.assembly_type == "letters_logo"
    assert len(response.operation_candidates_preview) == 2
    assert response.operation_candidates_preview[0].material_code == "MAT-ACP-FATA-LITERE"
    assert response.operation_candidates_preview[1].material_code == "MAT-VINYL-PRINT"
    assert len(response.consolidated_tasks_preview) == 2
    assert all(
        "logo_template_not_product_system_live" not in candidate.warnings
        for candidate in response.operation_candidates_preview
    )
    assert all("runtime_target_not_product_template_live" not in warning for warning in response.consolidation_warnings)


def test_logo_template_runtime_code_is_recognized():
    assert resolve_runtime_template_code("TPL-VOLUMETRIC-LOGO_v1") == "TPL-VOLUMETRIC-LOGO_V1"
    assert resolve_runtime_template_code("TPL-VOLUMETRIC-LOGO") == "TPL-VOLUMETRIC-LOGO_V1"


def test_logo_modular_form_contract_exists_as_preview_supported():
    contract = get_intake_v6_modular_form_contract_service().get_for_template("TPL-VOLUMETRIC-LOGO_v1")

    assert contract is not None
    assert contract.summary.template_code == "TPL-VOLUMETRIC-LOGO_v1"
    assert contract.summary.active_module_count >= 6
    assert any(module.module_code == "logo_face" for module in contract.modules)
    assert any(module.module_code == "logo_return" for module in contract.modules)
    assert any(module.module_code == "logo_back" for module in contract.modules)
    assert any("Preview-supported only" in warning for warning in contract.summary.warnings)