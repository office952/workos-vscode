"""Intake V3 finish variation summary — preview notes only, no CostEngine or runtime tasks."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Literal

from schemas.intake_v3 import (
    ConfirmedProductionModel,
    IntakeV3FinishVariationItem,
    IntakeV3FinishVariationMaterialNote,
    IntakeV3FinishVariationOperationNote,
    IntakeV3FinishVariationSummary,
    IntakeV3LetterFinishAssignment,
    IntakeV3LetterGroupFinishAssignment,
)
from services.intake_v3_finish_assignment_service import resolve_effective_finish_for_letter

SourceType = Literal["global", "group", "letter"]


def _confirmed_model_from_payload(payload: dict[str, Any]) -> ConfirmedProductionModel | None:
    raw = payload.get("confirmed_production_model")
    if not isinstance(raw, dict):
        return None
    try:
        model = ConfirmedProductionModel.model_validate(raw)
    except Exception:
        return None
    if model.confirmation_status != "confirmed":
        return None
    return model


def _letter_ids_from_payload(payload: dict[str, Any]) -> list[str]:
    model = _confirmed_model_from_payload(payload)
    if model is None:
        return []
    if model.letter_model and model.letter_model.letters:
        return [letter.letter_id for letter in model.letter_model.letters]
    return [f"L-{i:02d}" for i in range(1, model.letter_count + 1)]


def _enabled_groups(payload: dict[str, Any]) -> list[IntakeV3LetterGroupFinishAssignment]:
    groups: list[IntakeV3LetterGroupFinishAssignment] = []
    for item in payload.get("letter_group_finish_assignments") or []:
        if isinstance(item, dict):
            group = IntakeV3LetterGroupFinishAssignment.model_validate(item)
            if group.enabled:
                groups.append(group)
    return groups


def _enabled_letter_overrides(payload: dict[str, Any]) -> list[IntakeV3LetterFinishAssignment]:
    letters: list[IntakeV3LetterFinishAssignment] = []
    for item in payload.get("letter_finish_assignments") or []:
        if isinstance(item, dict):
            letter = IntakeV3LetterFinishAssignment.model_validate(item)
            if letter.enabled:
                letters.append(letter)
    return letters


def _resolve_letter_source(
    letter_id: str,
    groups: list[IntakeV3LetterGroupFinishAssignment],
    letters: list[IntakeV3LetterFinishAssignment],
) -> tuple[SourceType, str, str]:
    for item in letters:
        if item.target_letter_id == letter_id:
            return "letter", item.assignment_id, item.target_letter_id
    for group in groups:
        if letter_id in group.target_letter_ids:
            return "group", group.assignment_id, group.label or group.assignment_id
    return "global", "__global__", "Default / global"


def _finish_text(spec: dict[str, Any] | None, *, role: str) -> str:
    if not spec:
        return "none"
    finish_type = spec.get("finish_type") or "none"
    material = spec.get("material_code") or spec.get("material") or ""
    color_name = spec.get("color_name") or ""
    color_code = spec.get("color_code") or ""
    color = color_name or color_code
    parts = [part for part in (material, finish_type, color) if part]
    if role == "backing":
        thickness = spec.get("thickness_mm")
        if thickness:
            parts.append(f"{thickness}mm")
    return " ".join(parts) if parts else finish_type


def group_letters_by_effective_finish(
    payload: dict[str, Any],
) -> dict[tuple[SourceType, str], list[str]]:
    groups = _enabled_groups(payload)
    letters = _enabled_letter_overrides(payload)
    buckets: dict[tuple[SourceType, str], list[str]] = defaultdict(list)
    for letter_id in _letter_ids_from_payload(payload):
        source_type, source_id, _ = _resolve_letter_source(letter_id, groups, letters)
        buckets[(source_type, source_id)].append(letter_id)
    return dict(buckets)


def summarize_finish_material_variations(
    payload: dict[str, Any],
) -> list[IntakeV3FinishVariationMaterialNote]:
    counts: dict[tuple[str, str, str, str, str], int] = defaultdict(int)
    for letter_id in _letter_ids_from_payload(payload):
        effective = resolve_effective_finish_for_letter(payload, letter_id)
        for role, spec_key in (
            ("face", "face_finish"),
            ("return", "return_finish"),
            ("backing", "backing_finish"),
        ):
            spec = effective.get(spec_key) or {}
            if role == "backing" and not spec.get("material"):
                continue
            if role in {"face", "return"} and (spec.get("finish_type") or "none") == "none":
                continue
            key = (
                role,
                spec.get("material_code") or spec.get("material") or "",
                spec.get("material_family") or "",
                spec.get("finish_type") or "none",
                spec.get("color_name") or spec.get("color_code") or "",
            )
            counts[key] += 1

    notes: list[IntakeV3FinishVariationMaterialNote] = []
    for (role, material_code, material_family, finish_type, color_label), count in sorted(
        counts.items(), key=lambda item: (-item[1], item[0][0], item[0][1])
    ):
        notes.append(
            IntakeV3FinishVariationMaterialNote(
                role=role,
                material_code=material_code or None,
                material_family=material_family or None,
                finish_type=finish_type,
                color_label=color_label or None,
                affected_letter_count=count,
                note=(
                    f"{material_code or finish_type} {color_label}".strip()
                    + f" — {role} — {count} letter(s)"
                ),
            )
        )
    return notes


def summarize_finish_operation_variations(
    payload: dict[str, Any],
) -> list[IntakeV3FinishVariationOperationNote]:
    flags = {
        "face_vinyl_application": False,
        "return_wrapping": False,
        "return_painting": False,
        "backing_variation": False,
    }
    backing_materials: set[str] = set()
    for letter_id in _letter_ids_from_payload(payload):
        effective = resolve_effective_finish_for_letter(payload, letter_id)
        if effective.get("face_vinyl_active"):
            flags["face_vinyl_application"] = True
        if effective.get("return_vinyl_active"):
            flags["return_wrapping"] = True
        if effective.get("return_painted_active"):
            flags["return_painting"] = True
        backing = effective.get("backing_finish") or {}
        if backing.get("material"):
            backing_materials.add(str(backing.get("material")))

    if len(backing_materials) > 1:
        flags["backing_variation"] = True

    notes: list[IntakeV3FinishVariationOperationNote] = []
    if flags["face_vinyl_application"]:
        notes.append(
            IntakeV3FinishVariationOperationNote(
                operation_code="face_vinyl_application",
                present=True,
                note="Face vinyl application variation present across letters.",
            )
        )
    if flags["return_wrapping"]:
        notes.append(
            IntakeV3FinishVariationOperationNote(
                operation_code="return_wrapping",
                present=True,
                note="Return wrapping / return vinyl variation present across letters.",
            )
        )
    if flags["return_painting"]:
        notes.append(
            IntakeV3FinishVariationOperationNote(
                operation_code="return_painting",
                present=True,
                note="Return painting variation present across letters.",
            )
        )
    else:
        notes.append(
            IntakeV3FinishVariationOperationNote(
                operation_code="return_painting",
                present=False,
                note="Return painting variation absent.",
            )
        )
    if flags["backing_variation"]:
        notes.append(
            IntakeV3FinishVariationOperationNote(
                operation_code="backing_variation",
                present=True,
                note="Backing material variation present across letters.",
            )
        )
    return notes


def build_finish_variation_pricing_notes(summary: IntakeV3FinishVariationSummary) -> list[str]:
    if not summary.has_variations:
        return ["Global finish applies to all letters — grouped finish review not required."]
    notes = [
        "Finish variations require grouped material/labor review before final quote.",
        (
            f"{summary.group_assignment_count} group assignment(s) and "
            f"{summary.letter_override_count} letter override(s) affect pricing input preview."
        ),
    ]
    if summary.default_letter_count:
        notes.append(
            f"{summary.default_letter_count} letter(s) still use the default/global finish."
        )
    return notes


def build_finish_variation_handoff_notes(summary: IntakeV3FinishVariationSummary) -> list[str]:
    if not summary.has_variations:
        return ["Handoff preview uses global finish only — group labels optional."]
    notes = [
        "Production handoff preview must keep group labels and letter IDs visible for operators.",
    ]
    group_labels = [item.label for item in summary.variations if item.source_type == "group"]
    if group_labels:
        notes.append(f"Group labels in scope: {', '.join(group_labels)}.")
    if summary.letter_override_count:
        notes.append(
            f"{summary.letter_override_count} letter override(s) must remain visible in handoff notes."
        )
    return notes


def build_finish_variation_summary(payload: dict[str, Any]) -> IntakeV3FinishVariationSummary:
    letter_ids = _letter_ids_from_payload(payload)
    groups = _enabled_groups(payload)
    letters = _enabled_letter_overrides(payload)
    buckets = group_letters_by_effective_finish(payload)

    variations: list[IntakeV3FinishVariationItem] = []
    for (source_type, source_id), bucket_letter_ids in sorted(
        buckets.items(),
        key=lambda item: ({"global": 0, "group": 1, "letter": 2}[item[0][0]], item[0][1]),
    ):
        sample_id = sorted(bucket_letter_ids)[0]
        effective = resolve_effective_finish_for_letter(payload, sample_id)
        _, _, label = _resolve_letter_source(sample_id, groups, letters)
        face = effective.get("face_finish") or {}
        ret = effective.get("return_finish") or {}
        backing = effective.get("backing_finish") or {}
        operations = [
            op.operation_code
            for op in summarize_finish_operation_variations(payload)
            if op.present
        ]
        materials = [
            note.note
            for note in summarize_finish_material_variations(payload)
            if note.role in {"face", "return", "backing"}
        ][:3]
        variations.append(
            IntakeV3FinishVariationItem(
                variation_id=f"var-{source_type}-{source_id}",
                source_type=source_type,
                label=label,
                letter_ids=sorted(bucket_letter_ids),
                letter_count=len(bucket_letter_ids),
                face_finish_summary=_finish_text(face, role="face"),
                return_finish_summary=_finish_text(ret, role="return"),
                backing_finish_summary=_finish_text(backing, role="backing"),
                operations=operations,
                materials=materials,
                notes=(
                    f"{len(bucket_letter_ids)} letter(s) from {source_type} source "
                    f"({label})."
                ),
            )
        )

    default_letter_count = len(buckets.get(("global", "__global__"), []))
    has_variations = bool(groups or letters)
    assignment_mode = payload.get("finish_assignment_status") or "global_only"
    if groups and letters:
        assignment_mode = "mixed"
    elif groups:
        assignment_mode = "group_overrides"
    elif letters:
        assignment_mode = "letter_overrides"
    else:
        assignment_mode = "global_only"

    material_notes = summarize_finish_material_variations(payload)
    operation_notes = summarize_finish_operation_variations(payload)
    summary = IntakeV3FinishVariationSummary(
        has_variations=has_variations,
        assignment_mode=assignment_mode,
        total_letters=len(letter_ids),
        default_letter_count=default_letter_count,
        group_assignment_count=len(groups),
        letter_override_count=len(letters),
        variations=variations,
        material_notes=material_notes,
        operation_notes=operation_notes,
        pricing_preview_notes=[],
        handoff_preview_notes=[],
        warnings=["FINISH_ASSIGNMENT_VARIATIONS_PRESENT"] if has_variations else [],
    )
    summary.pricing_preview_notes = build_finish_variation_pricing_notes(summary)
    summary.handoff_preview_notes = build_finish_variation_handoff_notes(summary)
    return summary
