"""Resolve effective Intake V4 finish truth from per-layer groups (not stale globals)."""

from __future__ import annotations

from collections import Counter
from typing import Any, Literal, Mapping

from schemas.intake_v4 import IntakeV4ArtworkFinish, IntakeV4FinishSetup, IntakeV4LetterGroupFinish
from services.intake_v4_backing_mode_service import (
    finish_has_explicit_layer_backing_modes,
    resolve_backing_mode_from_finish,
)
from services.mounting_scope_service import hydrate_mounting_scope_fields, is_mounting_preparation_active
from services.mounting_solution_service import (
    ALLOWED_MOUNTING_SOLUTION_TEMPLATE_CODES,
    hydrate_mounting_solution_fields,
    read_mounting_solution,
)

INTAKE_V4_DEFAULT_RETURN_FINISH_TYPE = "white_aluminum"

_RETURN_FINISH_OPERATOR_LABELS: dict[str, str] = {
    "white_aluminum": "Alb",
    "black_aluminum": "Negru",
    "gold_aluminum": "Auriu",
    "mirror_silver": "Argintiu",
    "standard_aluminum": "Argintiu",
    "oracal_wrapped": "Oracal 651",
    "colantat": "Oracal 651",
    "oracal": "Oracal 651",
    "ral_paint": "Vopsit RAL",
    "vopsit_ral": "Vopsit RAL",
    "painted": "Vopsit RAL",
    "paint": "Vopsit RAL",
    "ral": "Vopsit RAL",
    "mixed": "mixt",
    "same_as_face": "La fel ca fața (legacy)",
    "none": "Cant / volum nespecificat (legacy)",
    "unspecified": "Cant / volum nespecificat (legacy)",
}

_FACE_VINYL_FINISHES = frozenset(
    {
        "oracal_651",
        "oracal_8500",
        "oracal_641",
        "print_laminate",
        "printed_vinyl",
        "printed_laminated_vinyl",
        "oracal",
        "651",
        "8500",
    }
)
_FACE_PRINT_LAMINATE = frozenset(
    {"print_laminate", "print_translucent", "printed_vinyl", "printed_laminated_vinyl", "printed_vinyl_on_face"}
)
_PRINT_ARTWORK_EXECUTION = frozenset(
    {"print_laminate", "print_translucent", "printed_vinyl", "printed_laminated_vinyl", "printed_vinyl_on_face"}
)
_LAMINATION_ARTWORK_EXECUTION = frozenset(
    {"print_laminate", "print_on_vinyl_laminated", "printed_laminated_vinyl"}
)
_NON_PRINT_ARTWORK_EXECUTION = frozenset(
    {
        "vinyl_cut",
        "cut_vinyl",
        "ignore",
        "none_raw_plexi",
        "translucent_vinyl",
    }
)
_FINISH_TARGET_VALUES = frozenset({"face", "cant", "artwork", "back", "all"})


def _token(value: str | None, default: str) -> str:
    raw = (value or default).strip().lower()
    return raw or default.strip().lower()


def format_intake_v4_return_finish_operator_label(
    token: str | None,
    default: str = INTAKE_V4_DEFAULT_RETURN_FINISH_TYPE,
) -> str:
    """Map internal return_finish_type tokens to operator-facing labels."""
    key = _token(token, default)
    return _RETURN_FINISH_OPERATOR_LABELS.get(key) or key.replace("_", " ")


def _group_dict_face_finish(group: dict[str, Any], default_face_finish: str) -> str:
    return _token(group.get("face_finish_type"), default_face_finish)


def _group_model_face_finish(group: IntakeV4LetterGroupFinish, default_face_finish: str) -> str:
    return _token(group.face_finish_type, default_face_finish)


def face_vinyl_required(face_finish: str) -> bool:
    token = face_finish.strip().lower()
    if token in {"none", "colored_plexiglas"}:
        return False
    return token in _FACE_VINYL_FINISHES


def face_finish_is_print_laminate(face_finish: str) -> bool:
    return face_finish.strip().lower() in _FACE_PRINT_LAMINATE


def artwork_print_execution(execution_type: str | None) -> bool:
    return _token(execution_type, "needs_decision") in _PRINT_ARTWORK_EXECUTION


def _is_finish_type_active(token: str | None) -> bool:
    normalized = str(token or "").strip().lower()
    return bool(normalized) and normalized not in {"none", "no_finish"}


def _is_return_finish_active(token: str | None) -> bool:
    normalized = str(token or "").strip().lower()
    return bool(normalized) and normalized not in {
        "none",
        "no_return",
        "without_return",
        "unspecified",
    }


def _is_backing_mode_active(token: str | None) -> bool:
    normalized = str(token or "").strip().lower()
    return bool(normalized) and normalized != "none"


def _artwork_row_has_decisive_execution(row: IntakeV4ArtworkFinish) -> bool:
    execution = str(row.execution_type or "needs_decision").strip().lower()
    return execution not in {"", "needs_decision", "ignore"}


def derive_artwork_print_required_from_execution(execution_type: str | None) -> bool | None:
    """Map operator execution_type to canonical row-level print_required at persist."""
    token = str(execution_type or "").strip().lower()
    if not token or token == "needs_decision":
        return None
    if token in _PRINT_ARTWORK_EXECUTION or token in {"print", "print_on_vinyl_laminated"}:
        return True
    if token in _NON_PRINT_ARTWORK_EXECUTION:
        return False
    return None


def derive_artwork_lamination_required_from_execution(execution_type: str | None) -> bool | None:
    """Map operator execution_type to canonical row-level lamination_required at persist."""
    token = str(execution_type or "").strip().lower()
    if not token or token == "needs_decision":
        return None
    if token in _LAMINATION_ARTWORK_EXECUTION:
        return True
    if token in _NON_PRINT_ARTWORK_EXECUTION or token in {
        "print",
        "print_translucent",
        "printed_vinyl",
        "printed_vinyl_on_face",
    }:
        return False
    return None


def hydrate_artwork_finish_boolean_fields(
    artwork: list[IntakeV4ArtworkFinish],
) -> list[IntakeV4ArtworkFinish]:
    """Persist explicit booleans from operator execution_type; clear stale values when undecided."""
    hydrated: list[IntakeV4ArtworkFinish] = []
    for row in artwork:
        derived_print = derive_artwork_print_required_from_execution(row.execution_type)
        derived_lamination = derive_artwork_lamination_required_from_execution(row.execution_type)
        hydrated.append(
            row.model_copy(
                update={
                    "print_required": derived_print,
                    "lamination_required": derived_lamination,
                }
            )
        )
    return hydrated


def derive_finish_target_from_zones(setup: Mapping[str, Any]) -> str | None:
    """Derive finish_target from active finish zones implied by operator layer selections."""
    groups = setup.get("letter_group_finishes") if isinstance(setup.get("letter_group_finishes"), list) else []
    artwork = setup.get("artwork_finishes") if isinstance(setup.get("artwork_finishes"), list) else []

    face_active = _is_finish_type_active(setup.get("face_finish_type"))
    cant_active = _is_return_finish_active(setup.get("return_finish_type"))
    back_active = _is_backing_mode_active(setup.get("backing_mode"))

    for group in groups:
        if not isinstance(group, Mapping):
            continue
        if _is_finish_type_active(group.get("face_finish_type")):
            face_active = True
        if _is_return_finish_active(group.get("return_finish_type")):
            cant_active = True
        if _is_backing_mode_active(group.get("backing_mode")):
            back_active = True

    artwork_active = False
    for row in artwork:
        if not isinstance(row, Mapping):
            continue
        if _is_return_finish_active(row.get("return_finish_type")):
            cant_active = True
        if _is_backing_mode_active(row.get("backing_mode")):
            back_active = True
        execution = str(row.get("execution_type") or "needs_decision").strip().lower()
        if execution not in {"", "needs_decision", "ignore"}:
            artwork_active = True

    zones: list[str] = []
    if face_active:
        zones.append("face")
    if cant_active:
        zones.append("cant")
    if artwork_active:
        zones.append("artwork")
    if back_active:
        zones.append("back")

    if not zones:
        return None
    if len(zones) == 1:
        return zones[0]
    return "all"


def hydrate_finish_target_fields(setup: Mapping[str, Any]) -> dict[str, Any]:
    """Persist finish_target from active finish zones when operator setup implies a target."""
    derived = derive_finish_target_from_zones(setup)
    if derived in _FINISH_TARGET_VALUES:
        return {"finish_target": derived}
    return {"finish_target": None}


def any_letter_group_face_vinyl_required(
    letter_groups: list[Any],
    default_face_finish: str,
) -> bool:
    if not letter_groups:
        return face_vinyl_required(default_face_finish)
    return any(
        face_vinyl_required(_group_dict_face_finish(group, default_face_finish))
        for group in letter_groups
        if isinstance(group, dict)
    )


def any_letter_group_face_print_laminate(
    letter_groups: list[Any],
    default_face_finish: str,
) -> bool:
    if not letter_groups:
        return face_finish_is_print_laminate(default_face_finish)
    return any(
        face_finish_is_print_laminate(_group_dict_face_finish(group, default_face_finish))
        for group in letter_groups
        if isinstance(group, dict)
    )


def _collect_return_finish_tokens(
    letter_groups: list[Any],
    artwork_finishes: list[Any],
    default_return_finish: str,
) -> list[str]:
    tokens: list[str] = []
    for group in letter_groups:
        if not isinstance(group, dict):
            continue
        raw = group.get("return_finish_type")
        if raw:
            tokens.append(_token(str(raw), default_return_finish))
    for row in artwork_finishes:
        if not isinstance(row, dict):
            continue
        raw = row.get("return_finish_type")
        if raw:
            tokens.append(_token(str(raw), default_return_finish))
    return tokens


def resolve_effective_return_finish_label(
    letter_groups: list[Any],
    artwork_finishes: list[Any],
    default_return_finish: str,
) -> str:
    tokens = _collect_return_finish_tokens(letter_groups, artwork_finishes, default_return_finish)
    if not tokens:
        return _token(default_return_finish, INTAKE_V4_DEFAULT_RETURN_FINISH_TYPE)
    unique = set(tokens)
    if len(unique) == 1:
        return tokens[0]
    return "mixed"


def resolve_effective_return_depth_mm(
    letter_groups: list[Any],
    artwork_finishes: list[Any],
    global_depth_mm: float | int | None,
) -> float | int | None:
    depths: list[float] = []
    for group in letter_groups:
        if not isinstance(group, dict):
            continue
        depth = group.get("return_depth_mm")
        if depth is not None:
            try:
                parsed = float(depth)
            except (TypeError, ValueError):
                continue
            if parsed > 0:
                depths.append(parsed)
    for row in artwork_finishes:
        if not isinstance(row, dict):
            continue
        depth = row.get("return_depth_mm")
        if depth is not None:
            try:
                parsed = float(depth)
            except (TypeError, ValueError):
                continue
            if parsed > 0:
                depths.append(parsed)
    if depths:
        return max(depths)
    return global_depth_mm


def _dominant_token(values: list[str | None], fallback: str | None) -> str | None:
    cleaned = [str(v).strip() for v in values if v is not None and str(v).strip()]
    if not cleaned:
        return fallback
    return Counter(cleaned).most_common(1)[0][0]


def dump_intake_v4_finish_setup_for_persist(setup: IntakeV4FinishSetup) -> dict[str, Any]:
    """JSON dict for workspace persist — omit trimmed global backing mirror keys."""
    dumped = setup.model_dump(mode="json")
    finish_dict = setup.model_dump(mode="json")
    if finish_has_explicit_layer_backing_modes(finish_dict):
        dumped.pop("backing_mode", None)
        dumped.pop("back_bevel_enabled", None)
    return dumped


def strip_global_backing_mirror_from_finish_dict(finish: dict[str, Any] | None) -> None:
    """In-place removal of legacy global backing mirror when per-layer backing exists."""
    if not isinstance(finish, dict):
        return
    if finish_has_explicit_layer_backing_modes(finish):
        finish.pop("backing_mode", None)
        finish.pop("back_bevel_enabled", None)


def _apply_finish_setup_updates(setup: IntakeV4FinishSetup, updates: dict[str, Any]) -> IntakeV4FinishSetup:
    """Apply normalize updates; allow explicit null for trimmed global mirror fields."""
    if not updates:
        return setup
    filtered: dict[str, Any] = {}
    for key, value in updates.items():
        if value is not None or key in {
            "backing_mode",
            "back_bevel_enabled",
            "mounting_system",
            "mounting_bar_profile",
            "mounting_solution",
            "finish_target",
        }:
            filtered[key] = value
    return setup.model_copy(update=filtered)


def _trim_global_backing_mirror_from_layers(
    setup: IntakeV4FinishSetup,
    groups: list[IntakeV4LetterGroupFinish],
    artwork: list[IntakeV4ArtworkFinish],
    updates: dict[str, Any],
) -> None:
    """Per-layer backing is authoritative — hydrate missing rows, drop global mirror."""
    finish_dict = setup.model_dump(mode="json")
    if not finish_has_explicit_layer_backing_modes(finish_dict):
        return

    global_mode = resolve_backing_mode_from_finish(finish_dict) or "forex_10_no_bevel"

    if groups:
        updates["letter_group_finishes"] = [
            group.model_copy(update={"backing_mode": global_mode})
            if group.backing_mode is None
            else group
            for group in groups
        ]
    if artwork:
        updates["artwork_finishes"] = [
            row.model_copy(update={"backing_mode": global_mode})
            if row.backing_mode is None
            else row
            for row in artwork
        ]

    updates["backing_mode"] = None
    updates["back_bevel_enabled"] = None


def normalize_intake_v4_finish_setup(setup: IntakeV4FinishSetup) -> IntakeV4FinishSetup:
    """Sync job-level finish fields from per-layer truth when groups/artwork exist."""
    groups = list(setup.letter_group_finishes or [])
    artwork = list(setup.artwork_finishes or [])
    updates: dict[str, Any] = {}

    finish_dict = setup.model_dump(mode="json")
    has_explicit_layer_backing = finish_has_explicit_layer_backing_modes(finish_dict)

    if not has_explicit_layer_backing or not (groups or artwork):
        if setup.backing_mode == "forex_10_with_bevel":
            updates["back_bevel_enabled"] = True
        elif setup.backing_mode in {"none", "forex_10_no_bevel"}:
            updates["back_bevel_enabled"] = False

    if setup.selected_psu_watts is None and setup.psu_configuration:
        psu_values = [int(w) for w in setup.psu_configuration if isinstance(w, int) and w > 0]
        if psu_values:
            updates["selected_psu_watts"] = max(psu_values)

    updates.update(hydrate_mounting_scope_fields(setup.model_dump(mode="json")))
    updates.update(hydrate_mounting_solution_fields(setup.model_dump(mode="json")))

    if groups:
        updates["face_finish_type"] = _dominant_token(
            [g.face_finish_type for g in groups],
            setup.face_finish_type,
        )
        updates["return_finish_type"] = _dominant_token(
            [g.return_finish_type for g in groups],
            setup.return_finish_type,
        )
        depths = [g.return_depth_mm for g in groups if g.return_depth_mm is not None]
        if depths:
            updates["return_depth_mm"] = max(float(d) for d in depths)
    elif artwork:
        updates["return_finish_type"] = _dominant_token(
            [a.return_finish_type for a in artwork],
            setup.return_finish_type,
        )
        depths = [a.return_depth_mm for a in artwork if a.return_depth_mm is not None]
        if depths:
            updates["return_depth_mm"] = max(float(d) for d in depths)

    if artwork:
        updates["artwork_finishes"] = hydrate_artwork_finish_boolean_fields(artwork)

    merged_setup = _apply_finish_setup_updates(setup, updates)
    updates.update(hydrate_finish_target_fields(merged_setup.model_dump(mode="json")))

    _trim_global_backing_mirror_from_layers(
        merged_setup,
        list(merged_setup.letter_group_finishes or []),
        list(merged_setup.artwork_finishes or []),
        updates,
    )

    return _apply_finish_setup_updates(merged_setup, updates)


ArtworkRuntimeBooleanField = Literal["print_required", "lamination_required"]
MountingScopeValue = Literal[
    "none",
    "preparation_only",
    "preparation_and_site_installation",
    "no_mounting",
    "mounting_included",
    "mounting_external",
    "to_be_decided",
]

_ARTWORK_RUNTIME_BLOCKER_BY_FIELD: dict[ArtworkRuntimeBooleanField, str] = {
    "print_required": "PRINT_REQUIRED_UNKNOWN",
    "lamination_required": "LAMINATION_REQUIRED_UNKNOWN",
}


def artwork_finish_runtime_boolean_state(
    setup: IntakeV4FinishSetup | dict[str, Any] | None,
    field_name: ArtworkRuntimeBooleanField,
) -> dict[str, Any]:
    blocker_code = _ARTWORK_RUNTIME_BLOCKER_BY_FIELD[field_name]
    source_path = f"finish_setup.artwork_finishes[].{field_name}"
    if setup is None:
        return {
            "status": "missing",
            "blocker_code": blocker_code,
            "rows": [],
            "source_path": source_path,
        }

    normalized_setup = setup
    if isinstance(setup, dict):
        normalized_setup = IntakeV4FinishSetup.model_validate(setup)

    artwork_rows = list(normalized_setup.artwork_finishes or [])
    if not artwork_rows:
        return {
            "status": "missing",
            "blocker_code": blocker_code,
            "rows": [],
            "source_path": source_path,
        }

    persisted_rows: list[dict[str, Any]] = []
    setup_confirmed = normalized_setup.confirmed is True
    for row in artwork_rows:
        value = getattr(row, field_name, None)
        if value is None:
            return {
                "status": "missing",
                "blocker_code": blocker_code,
                "rows": persisted_rows,
                "source_path": source_path,
            }

        row_confirmed = row.confirmed is True or setup_confirmed
        persisted_rows.append(
            {
                "layer_key": row.layer_key,
                "value": value,
                "confirmed": row_confirmed,
            }
        )
        if not row_confirmed:
            return {
                "status": "unconfirmed",
                "blocker_code": blocker_code,
                "rows": persisted_rows,
                "source_path": source_path,
            }

    return {
        "status": "confirmed",
        "blocker_code": None,
        "rows": persisted_rows,
        "source_path": source_path,
    }


def mounting_scope_runtime_state(
    setup: IntakeV4FinishSetup | dict[str, Any] | None,
) -> dict[str, Any]:
    source_path = "finish_setup.mounting_scope"
    if setup is None:
        return {
            "status": "missing",
            "blocker_code": "MOUNTING_SCOPE_MISSING",
            "value": None,
            "source_path": source_path,
        }

    normalized_setup = setup
    if isinstance(setup, dict):
        normalized_setup = IntakeV4FinishSetup.model_validate(setup)

    mounting_scope = getattr(normalized_setup, "mounting_scope", None)
    if not mounting_scope:
        return {
            "status": "missing",
            "blocker_code": "MOUNTING_SCOPE_MISSING",
            "value": None,
            "source_path": source_path,
        }
    if normalized_setup.confirmed is not True:
        return {
            "status": "unconfirmed",
            "blocker_code": "MOUNTING_SCOPE_MISSING",
            "value": mounting_scope,
            "source_path": source_path,
        }
    return {
        "status": "confirmed",
        "blocker_code": None,
        "value": mounting_scope,
        "source_path": source_path,
    }


def mounting_solution_runtime_state(
    setup: IntakeV4FinishSetup | dict[str, Any] | None,
) -> dict[str, Any]:
    """Canonical mounting truth — legacy mounting_system/support_type do not satisfy this gate."""
    source_path = "finish_setup.mounting_solution"
    finish_dict: dict[str, Any] | None
    if setup is None:
        finish_dict = None
    elif isinstance(setup, dict):
        finish_dict = setup
    else:
        finish_dict = setup.model_dump(mode="json")

    if not is_mounting_preparation_active(finish_dict):
        return {
            "status": "not_required",
            "blocker_code": None,
            "value": None,
            "source_path": source_path,
        }

    if setup is None:
        return {
            "status": "missing",
            "blocker_code": "MOUNTING_SOLUTION_MISSING",
            "value": None,
            "source_path": source_path,
        }

    normalized_setup = setup
    if isinstance(setup, dict):
        normalized_setup = IntakeV4FinishSetup.model_validate(setup)

    if normalized_setup.confirmed is not True:
        return {
            "status": "unconfirmed",
            "blocker_code": "MOUNTING_SOLUTION_MISSING",
            "value": None,
            "source_path": source_path,
        }

    solution = read_mounting_solution(normalized_setup.model_dump(mode="json"))
    if not solution:
        return {
            "status": "missing",
            "blocker_code": "MOUNTING_SOLUTION_MISSING",
            "value": None,
            "source_path": source_path,
        }

    template_code = str(solution.get("template_code") or "").strip()
    if template_code not in ALLOWED_MOUNTING_SOLUTION_TEMPLATE_CODES:
        return {
            "status": "blocked",
            "blocker_code": "MOUNTING_SOLUTION_INVALID",
            "value": solution,
            "source_path": source_path,
        }

    return {
        "status": "confirmed",
        "blocker_code": None,
        "value": solution,
        "source_path": source_path,
    }


def support_type_runtime_state(
    setup: IntakeV4FinishSetup | dict[str, Any] | None,
) -> dict[str, Any]:
    source_path = "finish_setup.support_type"
    if setup is None:
        return {
            "status": "missing",
            "blocker_code": "SUPPORT_TYPE_MISSING",
            "value": None,
            "source_path": source_path,
        }

    normalized_setup = setup
    if isinstance(setup, dict):
        normalized_setup = IntakeV4FinishSetup.model_validate(setup)

    support_type = str(getattr(normalized_setup, "support_type", "") or "").strip()
    if not support_type:
        return {
            "status": "missing",
            "blocker_code": "SUPPORT_TYPE_MISSING",
            "value": None,
            "source_path": source_path,
        }
    if normalized_setup.confirmed is not True:
        return {
            "status": "unconfirmed",
            "blocker_code": "SUPPORT_TYPE_MISSING",
            "value": support_type,
            "source_path": source_path,
        }
    return {
        "status": "confirmed",
        "blocker_code": None,
        "value": support_type,
        "source_path": source_path,
    }


_RETURN_ORACAL = frozenset({"oracal_wrapped", "colantat", "oracal"})
_RETURN_RAL = frozenset({"ral_paint", "vopsit_ral", "ral", "painted", "paint"})


def _return_requires_oracal_color(return_finish: str) -> bool:
    return _token(return_finish, "").strip() in _RETURN_ORACAL


def _return_requires_ral_color(return_finish: str) -> bool:
    return _token(return_finish, "").strip() in _RETURN_RAL


def list_finish_setup_color_fatal_blockers(setup: IntakeV4FinishSetup | None) -> list[str]:
    """Fatal when Oracal/RAL color selection is required but missing."""
    if setup is None:
        return []
    blockers: list[str] = []
    default_face = _token(setup.face_finish_type, "oracal_651")
    default_return = _token(setup.return_finish_type, INTAKE_V4_DEFAULT_RETURN_FINISH_TYPE)
    groups = list(setup.letter_group_finishes or [])
    if groups:
        for group in groups:
            face = _group_model_face_finish(group, default_face)
            if face_vinyl_required(face) and not (group.face_oracal_code or "").strip():
                blockers.append(f"missing_face_oracal_color:{group.group_key}")
            ret = _token(group.return_finish_type, default_return)
            if _return_requires_oracal_color(ret) and not (group.return_oracal_code or "").strip():
                blockers.append(f"missing_return_oracal_color:{group.group_key}")
            if _return_requires_ral_color(ret) and not (group.return_oracal_code or "").strip():
                blockers.append(f"missing_ral_color:{group.group_key}")
    else:
        if face_vinyl_required(default_face):
            blockers.append("missing_face_oracal_color:global")
        ret = default_return
        if _return_requires_oracal_color(ret) and not (setup.return_oracal_code or "").strip():
            blockers.append("missing_return_oracal_color:global")
        if _return_requires_ral_color(ret) and not (setup.return_oracal_code or "").strip():
            blockers.append("missing_ral_color:global")

    for row in setup.artwork_finishes or []:
        ret = _token(row.return_finish_type, default_return)
        if _return_requires_oracal_color(ret) and not (row.return_oracal_code or "").strip():
            blockers.append(f"missing_return_oracal_color:artwork:{row.layer_key}")
        if _return_requires_ral_color(ret) and not (row.return_oracal_code or "").strip():
            blockers.append(f"missing_ral_color:artwork:{row.layer_key}")
    return blockers


def letter_groups_require_face_vinyl(setup: IntakeV4FinishSetup | None) -> bool:
    if setup is None:
        return False
    default = _token(setup.face_finish_type, "oracal_651")
    groups = [g.model_dump(mode="json") for g in (setup.letter_group_finishes or [])]
    if groups:
        return any_letter_group_face_vinyl_required(groups, default)
    return face_vinyl_required(default)
