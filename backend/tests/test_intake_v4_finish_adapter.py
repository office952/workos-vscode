"""Intake V4 finish adapter + operation catalog task preview (Sprint 1)."""

from __future__ import annotations

from schemas.intake_v3 import FinishAssignment, OperationFlags
from schemas.intake_v4 import IntakeV4FinishSetup, IntakeV4LetterGroupFinish
from services.intake_v4_finish_adapter import (
    derive_operation_flags_from_v4_finish,
    finish_assignment_from_v4_setup,
)
from services.intake_v4_production_preview_service import build_v4_task_preview_response
from schemas.intake_v4 import IntakeV4ClientRequest, IntakeV4ProductBinding, IntakeV4WorkspacePayload


def _setup_with_groups(**group_kwargs) -> IntakeV4FinishSetup:
    return IntakeV4FinishSetup(
        illuminated=True,
        letter_group_finishes=[
            IntakeV4LetterGroupFinish(
                group_key="g1",
                layer_name="litere-1",
                **group_kwargs,
            )
        ],
    )


class TestIntakeV4FinishAdapter:
    def test_face_none_skips_vinyl_flag(self):
        setup = _setup_with_groups(face_finish_type="none", return_finish_type="standard_aluminum")
        finish = finish_assignment_from_v4_setup(setup)
        flags = derive_operation_flags_from_v4_finish(finish)
        assert flags.face_vinyl_application_required is False

    def test_face_oracal_651_enables_vinyl_flag(self):
        setup = _setup_with_groups(face_finish_type="oracal_651", return_finish_type="oracal_wrapped")
        finish = finish_assignment_from_v4_setup(setup)
        flags = derive_operation_flags_from_v4_finish(finish)
        assert flags.face_vinyl_application_required is True

    def test_return_wrapped_enables_return_vinyl_flag(self):
        setup = _setup_with_groups(face_finish_type="none", return_finish_type="oracal_wrapped")
        finish = finish_assignment_from_v4_setup(setup)
        flags = derive_operation_flags_from_v4_finish(finish)
        assert flags.return_vinyl_application_required is True

    def test_multi_group_or_flags(self):
        setup = IntakeV4FinishSetup(
            illuminated=True,
            letter_group_finishes=[
                IntakeV4LetterGroupFinish(
                    group_key="g1",
                    face_finish_type="none",
                    return_finish_type="standard_aluminum",
                ),
                IntakeV4LetterGroupFinish(
                    group_key="g2",
                    face_finish_type="oracal_651",
                    return_finish_type="oracal_wrapped",
                ),
            ],
        )
        finish = finish_assignment_from_v4_setup(setup)
        assert finish is not None
        assert finish.assignment_mode == "group"
        assert len(finish.groups) == 2
        flags = derive_operation_flags_from_v4_finish(finish)
        assert flags.face_vinyl_application_required is True
        assert flags.return_vinyl_application_required is True


class TestIntakeV4TaskPreviewCatalog:
    def _payload(self, setup: IntakeV4FinishSetup | None) -> IntakeV4WorkspacePayload:
        return IntakeV4WorkspacePayload(
            client=IntakeV4ClientRequest(),
            product_binding=IntakeV4ProductBinding(template_code="TPL-VOLUMETRIC-LETTERS"),
            finish_setup=setup,
            svg_analysis_json={"layers": []},
            quote_geometry={"letter_count": 10, "letter_perimeter_m": 12.5},
        )

    def test_preview_uses_operation_catalog(self):
        setup = _setup_with_groups(face_finish_type="oracal_651", return_finish_type="oracal_wrapped")
        response = build_v4_task_preview_response(
            workspace_id="ws-1",
            template_code="TPL-VOLUMETRIC-LETTERS",
            payload=self._payload(setup),
        )
        assert response.preview_engine == "v3_operation_catalog"
        codes = {item.operation_code for item in response.items}
        assert "face_vinyl_application_final" in codes
        assert "return_vinyl_application_workbench" in codes
        assert all(item.source == "operation_catalog" for item in response.items)

    def test_face_none_deactivates_face_vinyl_seed(self):
        setup = _setup_with_groups(face_finish_type="none", return_finish_type="standard_aluminum")
        response = build_v4_task_preview_response(
            workspace_id="ws-1",
            template_code="TPL-VOLUMETRIC-LETTERS",
            payload=self._payload(setup),
        )
        face = next(i for i in response.items if i.operation_code == "face_vinyl_application_final")
        assert face.active is False

    def test_non_illuminated_deactivates_led_seed(self):
        setup = _setup_with_groups(face_finish_type="oracal_651", return_finish_type="oracal_wrapped")
        setup.illuminated = False
        response = build_v4_task_preview_response(
            workspace_id="ws-1",
            template_code="TPL-VOLUMETRIC-LETTERS",
            payload=self._payload(setup),
        )
        led = next(i for i in response.items if i.operation_code == "led_installation_wiring_and_light_test")
        assert led.active is False
        assert led.inactive_reason == "non_illuminated"

    def test_operation_flags_exposed(self):
        setup = _setup_with_groups(face_finish_type="oracal_651", return_finish_type="oracal_wrapped")
        response = build_v4_task_preview_response(
            workspace_id="ws-1",
            template_code="TPL-VOLUMETRIC-LETTERS",
            payload=self._payload(setup),
        )
        flags = OperationFlags.model_validate(response.operation_flags or {})
        assert flags.face_vinyl_application_required is True

    def test_operator_task_labels_replace_colantare_cant_wording(self):
        setup = _setup_with_groups(face_finish_type="oracal_651", return_finish_type="oracal_wrapped")
        response = build_v4_task_preview_response(
            workspace_id="ws-1",
            template_code="TPL-VOLUMETRIC-LETTERS",
            payload=self._payload(setup),
        )
        workbench = next(
            i for i in response.items if i.operation_code == "return_vinyl_application_workbench"
        )
        face = next(i for i in response.items if i.operation_code == "face_vinyl_application_final")
        assert "Colantare cant" not in workbench.label
        assert "Oracal 651" in workbench.label
        assert "cant / volum" in workbench.label.lower()
        assert face.label == "Aplicare autocolant pe fețele literelor"
