"""Normalize SVG letterGroupFinishAssignments into volumetric quote_input operational fields.

Does not touch CostEngine, pricing, or inventory — only operational handoff + plan gates.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Tuple

from services.volumetric_quote_input_policy import normalize_face_finish_type

ALLOWED_RETURN_DEPTH_MM = frozenset({30, 60, 80, 100})

RETURN_VINYL_PROCESS_ID = "return_vinyl_application"
RETURN_VINYL_DISPLAY_NAME = "Colantare cant"

FACE_VINYL_ASSIGNMENT_FINISH_TYPES = frozenset(
    {
        "oracal",
        "translucent_film",
        "print_laminate",
        "printed_vinyl",
        "printed_laminated_vinyl",
    }
)
RETURN_VINYL_ASSIGNMENT_FINISH_TYPES = frozenset({"oracal_wrapped"})

ORACAL_SERIES_LABELS = {
    "651": "Oracal 651",
    "641": "Oracal 641",
    "8500": "Oracal 8500",
}

FORBIDDEN_INSTRUCTION_TOKENS = frozenset(
    {
        "quantity_m2",
        "eur/mp",
        "assembly_bbox",
        "fallback_weak_estimate",
        "face_vinyl_not_selected",
        "10% rezervă",
    }
)


def _truthy(raw: Any) -> bool:
    if raw is True:
        return True
    if isinstance(raw, str) and raw.strip().lower() in {"true", "1", "yes", "on"}:
        return True
    return False


def _positive_number(raw: Any) -> Optional[float]:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    return value


def _optional_string(raw: Any) -> str:
    return str(raw or "").strip()


def _normalize_oracal_material_label(material_code: str | None) -> str:
    code = _optional_string(material_code)
    if not code:
        return "Autocolant față litere"
    lowered = code.lower().replace("oracal", "").replace("_", " ").strip()
    if lowered in ORACAL_SERIES_LABELS:
        return ORACAL_SERIES_LABELS[lowered]
    if code in ORACAL_SERIES_LABELS:
        return ORACAL_SERIES_LABELS[code]
    if code.isdigit():
        return f"Oracal {code}"
    if code.lower().startswith("oracal"):
        return code
    return f"Oracal {code}"


def _format_color_line(color_code: str | None, color_name: str | None) -> Optional[str]:
    code = _optional_string(color_code)
    name = _optional_string(color_name)
    if code and name:
        return f"{code} {name}"
    if code:
        return code
    if name:
        return name
    return None


def _assignment_confirmed(row: Mapping[str, Any]) -> bool:
    if "confirmedByOperator" not in row:
        return True
    return _truthy(row.get("confirmedByOperator"))


def _iter_confirmed_assignments(product_spec: Mapping[str, Any] | None) -> List[dict[str, Any]]:
    if not isinstance(product_spec, dict):
        return []
    raw = product_spec.get("letterGroupFinishAssignments")
    if not isinstance(raw, list):
        return []
    rows: List[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        if not _assignment_confirmed(item):
            continue
        rows.append(dict(item))
    return rows


def _resolve_group_label(row: Mapping[str, Any], product_spec: Mapping[str, Any] | None) -> str:
    group_id = _optional_string(row.get("groupId"))
    if not group_id:
        return "grup litere"
    groups = product_spec.get("svgLetterGroups") if isinstance(product_spec, dict) else None
    if isinstance(groups, list):
        for entry in groups:
            if not isinstance(entry, dict):
                continue
            if _optional_string(entry.get("groupId")) == group_id:
                label = _optional_string(entry.get("visualLabel"))
                if label:
                    return label
    return group_id


def _face_assignment_applicable(face: Mapping[str, Any] | None) -> bool:
    if not isinstance(face, dict):
        return False
    finish = _optional_string(face.get("finishType")).lower()
    if finish in {"none", "ral_paint", "colored_plexiglas", "raw", "no_finish", "painted"}:
        return False
    return finish in FACE_VINYL_ASSIGNMENT_FINISH_TYPES


def _return_assignment_applicable(return_cant: Mapping[str, Any] | None) -> bool:
    if not isinstance(return_cant, dict):
        return False
    finish = _optional_string(return_cant.get("finishType")).lower()
    return finish in RETURN_VINYL_ASSIGNMENT_FINISH_TYPES


def _normalize_face_assignment(
    face: Mapping[str, Any],
    *,
    group_label: str,
    group_id: str,
) -> dict[str, Any]:
    finish = _optional_string(face.get("finishType")).lower()
    material_code = _optional_string(face.get("materialCode"))
    color_code = _optional_string(face.get("colorCode"))
    color_name = _optional_string(face.get("colorName"))
    material_label = _normalize_oracal_material_label(material_code or "651")

    face_finish_type = "none"
    face_finish_subtype: str | None = None
    # CostEngine gates Oracal face vinyl via face_finish_type=oracal_651 only (no separate
    # 8500 price path). Oracal 8500 / translucent_film keeps operator truth on subtype +
    # face_vinyl_material — same contract as frontend intakeFaceFinishToQuoteCostingType().
    if finish in {"translucent_film"} or material_code == "8500":
        face_finish_type = "oracal_651"
        face_finish_subtype = "oracal_8500"
        material_label = "Oracal 8500"
    elif finish == "print_laminate":
        face_finish_type = "printed_laminated_vinyl"
        material_label = "Autocolant print + laminare"
    elif finish in {"printed_vinyl"}:
        face_finish_type = "printed_vinyl"
        material_label = "Autocolant print"
    elif finish in {"oracal", "translucent_film"} or material_code:
        face_finish_type = "oracal_651"
        material_label = _normalize_oracal_material_label(material_code or "651")
        if material_code == "8500":
            face_finish_subtype = "oracal_8500"

    return {
        "group_id": group_id,
        "group_label": group_label,
        "face_finish_type": face_finish_type,
        "face_finish_subtype": face_finish_subtype,
        "face_vinyl_enabled": True,
        "face_vinyl_material": material_label,
        "face_vinyl_color_code": color_code or None,
        "face_vinyl_color_name": color_name or None,
        "face_vinyl_color": _format_color_line(color_code, color_name),
    }


def _normalize_return_assignment(
    return_cant: Mapping[str, Any],
    *,
    group_label: str,
    group_id: str,
) -> dict[str, Any]:
    material_code = _optional_string(return_cant.get("materialCode")) or "651"
    color_code = _optional_string(return_cant.get("colorCode"))
    color_name = _optional_string(return_cant.get("colorName"))
    depth = _positive_number(return_cant.get("depthMm"))
    depth_mm: int | None = None
    if depth is not None and int(depth) in ALLOWED_RETURN_DEPTH_MM:
        depth_mm = int(depth)

    return {
        "group_id": group_id,
        "group_label": group_label,
        "return_finish_type": "oracal_wrapped",
        "return_vinyl_enabled": True,
        "return_vinyl_material": _normalize_oracal_material_label(material_code),
        "return_vinyl_color_code": color_code or None,
        "return_vinyl_color_name": color_name or None,
        "return_vinyl_color": _format_color_line(color_code, color_name),
        "return_depth_mm": depth_mm,
    }


def _collect_face_groups(
    product_spec: Mapping[str, Any] | None,
) -> List[dict[str, Any]]:
    groups: List[dict[str, Any]] = []
    for row in _iter_confirmed_assignments(product_spec):
        face = row.get("face")
        if not _face_assignment_applicable(face if isinstance(face, dict) else None):
            continue
        group_id = _optional_string(row.get("groupId")) or f"group_{len(groups) + 1}"
        groups.append(
            _normalize_face_assignment(
                face if isinstance(face, dict) else {},
                group_label=_resolve_group_label(row, product_spec),
                group_id=group_id,
            )
        )
    return groups


def _collect_return_groups(
    product_spec: Mapping[str, Any] | None,
) -> List[dict[str, Any]]:
    groups: List[dict[str, Any]] = []
    for row in _iter_confirmed_assignments(product_spec):
        return_cant = row.get("returnCant")
        if not _return_assignment_applicable(return_cant if isinstance(return_cant, dict) else None):
            continue
        group_id = _optional_string(row.get("groupId")) or f"group_{len(groups) + 1}"
        groups.append(
            _normalize_return_assignment(
                return_cant if isinstance(return_cant, dict) else {},
                group_label=_resolve_group_label(row, product_spec),
                group_id=group_id,
            )
        )
    return groups


def _groups_are_uniform(groups: List[dict[str, Any]], keys: Tuple[str, ...]) -> bool:
    if len(groups) <= 1:
        return True
    signatures = []
    for group in groups:
        signatures.append(tuple(group.get(key) for key in keys))
    return len(set(signatures)) == 1


def _apply_primary_group_fields(
    target: MutableMapping[str, Any],
    groups: List[dict[str, Any]],
    *,
    prefix: str,
    uniform_keys: Tuple[str, ...],
    primary_keys: Tuple[str, ...],
) -> None:
    if not groups:
        return
    primary = groups[0]
    for key in primary_keys:
        if primary.get(key) is not None:
            target[key] = primary[key]
    handoff_key = f"letter_group_{prefix}_vinyl_handoff"
    target[handoff_key] = {
        "groups": groups,
        "uniform_all_letters": _groups_are_uniform(groups, uniform_keys),
    }


def normalize_volumetric_quote_input_from_finish_assignments(
    quote_input: Mapping[str, Any] | None,
    *,
    product_spec: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge confirmed SVG finish assignments into quote_input without touching pricing."""
    merged: dict[str, Any] = dict(quote_input or {})
    ps = product_spec if isinstance(product_spec, dict) else {}

    face_groups = _collect_face_groups(ps)
    return_groups = _collect_return_groups(ps)

    if face_groups:
        _apply_primary_group_fields(
            merged,
            face_groups,
            prefix="face",
            uniform_keys=(
                "face_vinyl_material",
                "face_vinyl_color_code",
                "face_vinyl_color_name",
                "face_finish_type",
                "face_finish_subtype",
            ),
            primary_keys=(
                "face_vinyl_enabled",
                "face_finish_type",
                "face_finish_subtype",
                "face_vinyl_material",
                "face_vinyl_color_code",
                "face_vinyl_color_name",
                "face_vinyl_color",
            ),
        )
        if normalize_face_finish_type(merged.get("face_finish_type")) == "none":
            merged["face_finish_type"] = face_groups[0]["face_finish_type"]
        merged["face_vinyl_enabled"] = True

    if return_groups:
        _apply_primary_group_fields(
            merged,
            return_groups,
            prefix="return",
            uniform_keys=(
                "return_vinyl_material",
                "return_vinyl_color_code",
                "return_vinyl_color_name",
                "return_depth_mm",
            ),
            primary_keys=(
                "return_vinyl_enabled",
                "return_finish_type",
                "return_vinyl_material",
                "return_vinyl_color_code",
                "return_vinyl_color_name",
                "return_vinyl_color",
            ),
        )
        merged["return_vinyl_enabled"] = True
        depth_candidates = [
            g.get("return_depth_mm")
            for g in return_groups
            if g.get("return_depth_mm") is not None
        ]
        if depth_candidates:
            merged["return_depth_mm"] = depth_candidates[0]
            merged["depth_mm"] = depth_candidates[0]

    return merged


def resolve_volumetric_operational_quote_input(
    quote_input: Mapping[str, Any] | None,
    *,
    product_spec: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return normalize_volumetric_quote_input_from_finish_assignments(
        quote_input,
        product_spec=product_spec,
    )


def has_return_vinyl_application(
    quote_input: Mapping[str, Any] | None,
    *,
    product_spec: Mapping[str, Any] | None = None,
) -> bool:
    qi = resolve_volumetric_operational_quote_input(quote_input, product_spec=product_spec)
    if _truthy(qi.get("return_vinyl_enabled")):
        return True
    finish = _optional_string(qi.get("return_finish_type")).lower()
    if finish in RETURN_VINYL_ASSIGNMENT_FINISH_TYPES:
        return True
    return bool(_collect_return_groups(product_spec if isinstance(product_spec, dict) else {}))


def _face_material_label(quote_input: Mapping[str, Any]) -> str:
    explicit = _optional_string(quote_input.get("face_vinyl_material"))
    if explicit:
        return explicit
    face = normalize_face_finish_type(quote_input.get("face_finish_type"))
    if face == "oracal_651":
        subtype = _optional_string(quote_input.get("face_finish_subtype"))
        if subtype == "oracal_8500":
            return "Oracal 8500"
        return "Oracal 651"
    if face == "printed_vinyl":
        return "Autocolant print"
    if face == "printed_laminated_vinyl":
        return "Autocolant print + laminare"
    return "Autocolant față litere"


def _return_material_label(quote_input: Mapping[str, Any]) -> str:
    explicit = _optional_string(quote_input.get("return_vinyl_material"))
    if explicit:
        return explicit
    return "Oracal 651"


def _face_color_line(quote_input: Mapping[str, Any]) -> Optional[str]:
    explicit = _optional_string(quote_input.get("face_vinyl_color"))
    if explicit:
        return explicit
    return _format_color_line(
        quote_input.get("face_vinyl_color_code"),
        quote_input.get("face_vinyl_color_name"),
    )


def _return_color_line(quote_input: Mapping[str, Any]) -> Optional[str]:
    explicit = _optional_string(quote_input.get("return_vinyl_color"))
    if explicit:
        return explicit
    return _format_color_line(
        quote_input.get("return_vinyl_color_code"),
        quote_input.get("return_vinyl_color_name"),
    )


def _group_scope_lines(handoff: Mapping[str, Any] | None, *, material_key: str, color_key: str) -> List[str]:
    if not isinstance(handoff, dict):
        return []
    groups = handoff.get("groups")
    if not isinstance(groups, list) or not groups:
        return []
    if handoff.get("uniform_all_letters") is True:
        return ["Se aplică pe toate literele."]
    lines: List[str] = []
    for group in groups:
        if not isinstance(group, dict):
            continue
        label = _optional_string(group.get("group_label")) or _optional_string(group.get("group_id"))
        material = _optional_string(group.get(material_key))
        color = _optional_string(group.get(color_key))
        detail = material
        if color:
            detail = f"{material} — {color}" if material else color
        if detail:
            lines.append(f"- {label}: {detail}")
    return lines


def build_face_vinyl_operator_instructions(
    quote_input: Mapping[str, Any] | None,
    *,
    product_spec: Mapping[str, Any] | None = None,
) -> str:
    qi = resolve_volumetric_operational_quote_input(quote_input, product_spec=product_spec)
    material = _face_material_label(qi)
    color = _face_color_line(qi)
    scope_lines = _group_scope_lines(
        qi.get("letter_group_face_vinyl_handoff")
        if isinstance(qi.get("letter_group_face_vinyl_handoff"), dict)
        else None,
        material_key="face_vinyl_material",
        color_key="face_vinyl_color",
    )

    sections: List[str] = []
    sections.append("CE FAC ACUM")
    sections.append("")
    sections.append(
        "Colantezi fețele din plexiglas ale literelor cu autocolantul selectat, "
        "după debitarea fețelor și înainte de lipirea cantului."
    )
    sections.append("")
    sections.append("DATE TEHNICE")
    sections.append("")
    sections.append(f"Material autocolant: {material}")
    if color:
        sections.append(f"Culoare: {color}")
    if scope_lines:
        sections.append("")
        sections.append("APLICARE")
        sections.append("")
        sections.extend(scope_lines)
    sections.append("")
    sections.append("PAȘI DE LUCRU")
    sections.append("")
    steps = [
        "Verifică autocolantul și culoarea înainte de aplicare.",
        "Curăță fețele din plexiglas înainte de colantare.",
        "Aplică autocolantul pe fețele literelor, curat și aliniat.",
        "Evită bulele, cutele și tensiunile în material.",
        "Finisează marginile după forma fiecărei litere.",
        "Verifică aspectul final înainte de lipirea cantului.",
    ]
    for index, step in enumerate(steps, start=1):
        sections.append(f"{index}. {step}")
    return "\n".join(sections)


def build_return_vinyl_operator_instructions(
    quote_input: Mapping[str, Any] | None,
    *,
    product_spec: Mapping[str, Any] | None = None,
) -> str | None:
    qi = resolve_volumetric_operational_quote_input(quote_input, product_spec=product_spec)
    if not has_return_vinyl_application(qi, product_spec=product_spec):
        return None

    depth = _positive_number(qi.get("return_depth_mm") or qi.get("depth_mm"))
    if depth is None:
        return None

    material = _return_material_label(qi)
    color = _return_color_line(qi)
    scope_lines = _group_scope_lines(
        qi.get("letter_group_return_vinyl_handoff")
        if isinstance(qi.get("letter_group_return_vinyl_handoff"), dict)
        else None,
        material_key="return_vinyl_material",
        color_key="return_vinyl_color",
    )

    sections: List[str] = []
    sections.append("CE FAC ACUM")
    sections.append("")
    sections.append(
        "Colantezi cantul/lateralul literelor cu autocolantul selectat pe banda de aluminiu, "
        "înainte de modelarea cantului."
    )
    sections.append("")
    sections.append("DATE TEHNICE")
    sections.append("")
    sections.append("Material cant: aluminiu 0.6 mm")
    sections.append(f"Adâncime cant: {int(depth)} mm")
    sections.append(f"Autocolant: {material}")
    if color:
        sections.append(f"Culoare: {color}")
    if scope_lines:
        sections.append("")
        sections.append("APLICARE")
        sections.append("")
        if any("toate" in line.lower() for line in scope_lines):
            sections.extend(scope_lines)
        else:
            sections.append("Pe grupuri:")
            sections.extend(scope_lines)
    sections.append("")
    sections.append("PAȘI DE LUCRU")
    sections.append("")
    steps = [
        "Verifică adâncimea cantului și culoarea autocolantului.",
        "Aplică autocolantul pe banda de aluminiu înainte de modelare.",
        "Menține aplicarea dreaptă, fără bule și fără cute.",
        "Protejează suprafața colantată în timpul modelării.",
        "După modelare, verifică dacă folia este lipită corect pe toată lungimea.",
        "Predă canturile numerotate către masa de asamblare.",
    ]
    for index, step in enumerate(steps, start=1):
        sections.append(f"{index}. {step}")
    return "\n".join(sections)


def instructions_contain_forbidden_tokens(text: str | None) -> List[str]:
    if not text:
        return []
    lowered = text.lower()
    return sorted(token for token in FORBIDDEN_INSTRUCTION_TOKENS if token in lowered)
