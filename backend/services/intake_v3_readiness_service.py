"""Intake V3 readiness evaluation — in-memory contract skeleton (no DB, no quote/order/plan)."""

from __future__ import annotations

from data_models.intake_v3_contracts import (
    BLOCKER_MISSING_DIMENSIONS,
    BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH,
    BLOCKER_MISSING_FINISH_ASSIGNMENT,
    BLOCKER_MISSING_RETURN_DEPTH,
    BLOCKER_UNCONFIRMED_LETTER_MODEL,
    INTAKE_V3_CONTRACT_VERSION,
    OWNER_OPERATIONAL_RULE_DETAILS,
    REFERENCE_TASK_ORDER_NO_SHARED_SUPPORT,
)
from schemas.intake_v3 import (
    FinishAssignment,
    IntakeV3Workspace,
    ReadinessIssue,
    ReadinessReport,
)
from services.intake_v3_finish_material_service import (
    derive_material_intent,
    material_intent_warnings,
    validate_finish_assignment,
)
from services.intake_v3_vector_model_service import validate_confirmed_production_model


def _positive(value: float | int | None) -> bool:
    try:
        return value is not None and float(value) > 0
    except (TypeError, ValueError):
        return False


def _issue(
    *,
    code: str,
    severity: str,
    section: str,
    message: str,
    target_field: str | None = None,
    action_label: str | None = None,
) -> ReadinessIssue:
    return ReadinessIssue(
        code=code,
        severity=severity,  # type: ignore[arg-type]
        section=section,
        message=message,
        target_field=target_field,
        action_label=action_label,
    )


def _dimensions_present(workspace: IntakeV3Workspace) -> bool:
    req = workspace.client_request
    if _positive(req.width_mm) and _positive(req.height_mm):
        return True
    asset = workspace.vector_asset
    if asset and _positive(asset.declared_width_mm) and _positive(asset.declared_height_mm):
        return True
    return False


def _letter_model_confirmed(workspace: IntakeV3Workspace) -> bool:
    model = workspace.confirmed_production_model
    if model is None:
        return False
    if model.confirmation_status != "confirmed":
        return False
    if model.letter_model is not None and not model.letter_model.count_confirmed:
        return False
    return model.letter_count > 0


def _collect_finish_issues(
    workspace: IntakeV3Workspace,
) -> tuple[list[ReadinessIssue], list[ReadinessIssue]]:
    from services.intake_v3_layer_finish_assignment_service import (
        collect_layer_finish_issues,
        uses_native_layer_finish,
    )

    payload = workspace.model_dump(mode="json")
    if uses_native_layer_finish(payload):
        layer_blockers, layer_warnings = collect_layer_finish_issues(payload)
        blockers = [
            _issue(
                code=item.code,
                severity="blocker",
                section="finisaje",
                message=item.message,
                target_field=item.target_field,
                action_label="Corectează finisaje pe layer",
            )
            for item in layer_blockers
        ]
        warnings = [
            _issue(
                code=item.code,
                severity="warning",
                section="finisaje",
                message=item.message,
                target_field=item.target_field,
            )
            for item in layer_warnings
        ]
        return blockers, warnings

    finish = workspace.finish_assignment
    if finish is None:
        return [], []
    validation = validate_finish_assignment(workspace)
    blockers = [
        _issue(
            code=item.code,
            severity="blocker",
            section="finisaje",
            message=item.message,
            target_field=item.target_field,
            action_label="Corectează finisaje",
        )
        for item in validation.blockers
    ]
    warnings = [
        _issue(
            code=item.code,
            severity="warning",
            section="finisaje",
            message=item.message,
            target_field=item.target_field,
        )
        for item in validation.warnings
    ]
    return blockers, warnings


def _collect_lighting_issues(workspace: IntakeV3Workspace) -> tuple[list[ReadinessIssue], list[ReadinessIssue]]:
    from services.intake_v3_lighting_plan_service import collect_lighting_issues, lighting_plan_required

    payload = workspace.model_dump(mode="json")
    if not lighting_plan_required(payload):
        return [], []

    layer_blockers, layer_warnings = collect_lighting_issues(payload)
    blockers = [
        _issue(
            code=item.code,
            severity="blocker",
            section="iluminare",
            message=item.message,
            target_field=item.target_field,
            action_label="Completează iluminare & surse",
        )
        for item in layer_blockers
    ]
    warnings = [
        _issue(
            code=item.code,
            severity="warning",
            section="iluminare",
            message=item.message,
            target_field=item.target_field,
        )
        for item in layer_warnings
    ]
    return blockers, warnings


def _vector_model_issues(workspace: IntakeV3Workspace) -> tuple[list[ReadinessIssue], list[ReadinessIssue]]:
    """Map vector model validation to readiness blockers/warnings."""
    model = workspace.confirmed_production_model
    if model is None:
        return [], []
    validation = validate_confirmed_production_model(model, raw=workspace.raw_svg_analysis)
    blockers = [
        _issue(
            code=item.code,
            severity="blocker",
            section="litere",
            message=item.message,
            target_field=item.target_field,
            action_label="Corectează model litere",
        )
        for item in validation.blockers
        if item.code != BLOCKER_UNCONFIRMED_LETTER_MODEL
    ]
    warnings = [
        _issue(
            code=item.code,
            severity="warning",
            section="vector" if item.code.startswith("RAW_") or "RAW" in item.code else "litere",
            message=item.message,
            target_field=item.target_field,
        )
        for item in validation.warnings
    ]
    return blockers, warnings


def evaluate_intake_v3_readiness(workspace: IntakeV3Workspace) -> ReadinessReport:
    """Evaluate readiness from an in-memory Intake V3 workspace. No DB I/O."""
    blockers: list[ReadinessIssue] = []
    warnings: list[ReadinessIssue] = []
    completion: dict[str, float] = {
        "context": 0.0,
        "vector": 0.0,
        "litere": 0.0,
        "finisaje": 0.0,
        "materiale": 0.0,
        "iluminare": 0.0,
        "handoff": 0.0,
    }

    if workspace.client_request.client_name.strip():
        completion["context"] = 0.5
    if workspace.client_request.request_code.strip():
        completion["context"] = min(1.0, completion["context"] + 0.5)

    if workspace.vector_asset and workspace.vector_asset.upload_status != "missing":
        completion["vector"] = 0.5
    if workspace.raw_svg_analysis and workspace.raw_svg_analysis.closed_contour_count > 0:
        completion["vector"] = 1.0

    if not _dimensions_present(workspace):
        blockers.append(
            _issue(
                code=BLOCKER_MISSING_DIMENSIONS,
                severity="blocker",
                section="context",
                message="Dimensiunile lucrării (lățime și înălțime) sunt obligatorii.",
                target_field="client_request.width_mm",
                action_label="Completează dimensiuni",
            )
        )
    else:
        completion["context"] = max(completion["context"], 1.0)

    if not _letter_model_confirmed(workspace):
        blockers.append(
            _issue(
                code=BLOCKER_UNCONFIRMED_LETTER_MODEL,
                severity="blocker",
                section="litere",
                message="Modelul de litere nu este confirmat de operator.",
                target_field="confirmed_production_model.confirmation_status",
                action_label="Confirmă model litere",
            )
        )
    else:
        completion["litere"] = 1.0
        vector_blockers, vector_warnings = _vector_model_issues(workspace)
        blockers.extend(vector_blockers)
        warnings.extend(vector_warnings)

    raw = workspace.raw_svg_analysis
    confirmed = workspace.confirmed_production_model
    if (
        raw
        and confirmed
        and confirmed.is_confirmed
        and not any(w.code == "RAW_CONFIRMED_LETTER_COUNT_MISMATCH" for w in warnings)
        and raw.closed_contour_count > 0
        and raw.closed_contour_count != confirmed.letter_count
    ):
        warnings.append(
            _issue(
                code="RAW_CONFIRMED_LETTER_COUNT_MISMATCH",
                severity="warning",
                section="vector",
                message=(
                    "Analiza brută și modelul confirmat diferă la număr de contururi/litere — "
                    "operatorul a confirmat modelul de producție."
                ),
                target_field="confirmed_production_model.letter_count",
            )
        )

    finish = workspace.finish_assignment
    if finish is not None:
        finish_blockers, finish_warnings = _collect_finish_issues(workspace)
        blockers.extend(finish_blockers)
        warnings.extend(finish_warnings)
        if not finish_blockers and finish.confirmed_by_operator:
            completion["finisaje"] = 1.0
        elif finish.active_groups():
            completion["finisaje"] = 0.5

    if workspace.confirmed_production_model and workspace.finish_assignment:
        derived_intent = derive_material_intent(workspace)
        for warn in material_intent_warnings(derived_intent):
            if not any(w.code == warn.code for w in warnings):
                warnings.append(
                    _issue(
                        code=warn.code,
                        severity="warning",
                        section="materiale",
                        message=warn.message,
                        target_field=warn.target_field,
                    )
                )
        if derived_intent.estimate_status in {"partial", "complete"}:
            completion["materiale"] = max(completion["materiale"], 0.5)
        if workspace.material_intent.estimate_status == "complete":
            completion["materiale"] = 1.0
    elif workspace.material_intent.estimate_status == "complete":
        completion["materiale"] = 1.0
    elif workspace.material_intent.estimate_status == "partial":
        completion["materiale"] = 0.5

    lighting_blockers, lighting_warnings = _collect_lighting_issues(workspace)
    blockers.extend(lighting_blockers)
    warnings.extend(lighting_warnings)
    from services.intake_v3_lighting_plan_service import lighting_plan_required

    payload = workspace.model_dump(mode="json")
    if not lighting_blockers and lighting_plan_required(payload):
        plan = workspace.lighting_plan
        if plan and plan.is_confirmed:
            completion["iluminare"] = 1.0
        elif plan:
            completion["iluminare"] = 0.5
    elif not lighting_plan_required(payload):
        completion["iluminare"] = 1.0

    can_quote = len(blockers) == 0
    status = "draft"
    if blockers:
        status = "blocked_for_quote"
    elif can_quote:
        status = "ready_for_quote"

    next_action: str | None = None
    if blockers:
        next_action = blockers[0].action_label or blockers[0].message
    elif can_quote:
        next_action = "Trimite la ofertare"

    return ReadinessReport(
        status=status,  # type: ignore[arg-type]
        blockers=blockers,
        warnings=warnings,
        completion_by_section=completion,
        can_create_quote=can_quote,
        can_create_order=False,
        can_generate_production_handoff=can_quote and _letter_model_confirmed(workspace),
        next_action=next_action,
        contract_version=INTAKE_V3_CONTRACT_VERSION,
    )


def build_reference_production_handoff_seed() -> list[str]:
    """Return owner reference task order labels for documentation/preview seeds."""
    return list(REFERENCE_TASK_ORDER_NO_SHARED_SUPPORT)


def owner_operational_rule_summaries() -> list[dict[str, object]]:
    """Expose owner operational rules for docs/tests without execution enforcement."""
    return [dict(rule) for rule in OWNER_OPERATIONAL_RULE_DETAILS]
