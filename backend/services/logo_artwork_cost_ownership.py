"""Canonical cost ownership for workspace-linked logo artwork rows."""

from __future__ import annotations

from typing import Any

from services.template_architecture_scope import VOLUMETRIC_LOGO_TEMPLATE_CODE

SEGMENT_NAMESPACE_SEP = "::"
LINKED_SEGMENT_COMPONENT_REF_PREFIX = "linked_segment"
CANONICAL_ARTWORK_COMPONENT = "comp_logo_finish"
CANONICAL_FACE_COMPONENT = "comp_logo_face"

LOGO_ARTWORK_MATERIAL_CODES = frozenset(
    {
        "print_media",
        "laminate_media",
    }
)
LOGO_ARTWORK_OPERATION_CODES = frozenset(
    {
        "logo_face_print",
        "logo_face_laminate",
        "logo_finish_application",
    }
)
FACE_OWNED_MATERIAL_CODES = frozenset({"logo_face_material"})
FACE_OWNED_OPERATION_CODES = frozenset({"logo_face_cnc_cut"})


def _text(value: Any) -> str:
    return str(value or "").strip()


def segment_key_from_component_ref(component_ref: str | None) -> str | None:
    ref = _text(component_ref)
    if SEGMENT_NAMESPACE_SEP not in ref:
        return None
    return ref.split(SEGMENT_NAMESPACE_SEP, 1)[1]


def base_component_from_ref(component_ref: str | None) -> str:
    ref = _text(component_ref)
    if SEGMENT_NAMESPACE_SEP in ref:
        return ref.split(SEGMENT_NAMESPACE_SEP, 1)[0]
    if ref.startswith(f"{LINKED_SEGMENT_COMPONENT_REF_PREFIX}{SEGMENT_NAMESPACE_SEP}"):
        return LINKED_SEGMENT_COMPONENT_REF_PREFIX
    return ref


def is_linked_logo_template_row(*, source_template_code: str | None, component_ref: str | None) -> bool:
    if _text(source_template_code) != VOLUMETRIC_LOGO_TEMPLATE_CODE:
        return False
    return SEGMENT_NAMESPACE_SEP in _text(component_ref) or _text(component_ref).startswith(
        f"{LINKED_SEGMENT_COMPONENT_REF_PREFIX}{SEGMENT_NAMESPACE_SEP}"
    )


def is_mapping_only_row(*, provenance: str | None, status: str | None, component_ref: str | None) -> bool:
    if _text(status) == "mapping_only":
        return True
    if _text(provenance) == "dossier":
        return True
    base = base_component_from_ref(component_ref)
    return base == LINKED_SEGMENT_COMPONENT_REF_PREFIX


def canonical_artwork_component_ref(segment_key: str) -> str:
    return f"{CANONICAL_ARTWORK_COMPONENT}{SEGMENT_NAMESPACE_SEP}{segment_key}"


def canonical_face_component_ref(segment_key: str) -> str:
    return f"{CANONICAL_FACE_COMPONENT}{SEGMENT_NAMESPACE_SEP}{segment_key}"


def is_canonical_logo_artwork_material_row(
    *,
    material_code: str,
    component_ref: str | None,
    provenance: str | None,
    status: str | None,
    source_template_code: str | None,
) -> bool:
    if material_code not in LOGO_ARTWORK_MATERIAL_CODES:
        return True
    if not is_linked_logo_template_row(
        source_template_code=source_template_code,
        component_ref=component_ref,
    ):
        return True
    if is_mapping_only_row(provenance=provenance, status=status, component_ref=component_ref):
        return False
    segment_key = segment_key_from_component_ref(component_ref)
    if not segment_key:
        return False
    return _text(component_ref) == canonical_artwork_component_ref(segment_key)


def is_canonical_logo_artwork_operation_row(
    *,
    operation_code: str,
    component_ref: str | None,
    provenance: str | None,
    status: str | None,
    source_template_code: str | None,
) -> bool:
    if operation_code not in LOGO_ARTWORK_OPERATION_CODES:
        return True
    if not is_linked_logo_template_row(
        source_template_code=source_template_code,
        component_ref=component_ref,
    ):
        return True
    if is_mapping_only_row(provenance=provenance, status=status, component_ref=component_ref):
        return False
    segment_key = segment_key_from_component_ref(component_ref)
    if not segment_key:
        return False
    return _text(component_ref) == canonical_artwork_component_ref(segment_key)


def is_canonical_logo_face_material_row(
    *,
    material_code: str,
    component_ref: str | None,
    provenance: str | None,
    status: str | None,
    source_template_code: str | None,
) -> bool:
    if material_code not in FACE_OWNED_MATERIAL_CODES:
        return True
    if not is_linked_logo_template_row(
        source_template_code=source_template_code,
        component_ref=component_ref,
    ):
        return True
    if is_mapping_only_row(provenance=provenance, status=status, component_ref=component_ref):
        return False
    segment_key = segment_key_from_component_ref(component_ref)
    if not segment_key:
        return False
    return _text(component_ref) == canonical_face_component_ref(segment_key)


def is_canonical_logo_face_operation_row(
    *,
    operation_code: str,
    component_ref: str | None,
    provenance: str | None,
    status: str | None,
    source_template_code: str | None,
) -> bool:
    if operation_code not in FACE_OWNED_OPERATION_CODES:
        return True
    if not is_linked_logo_template_row(
        source_template_code=source_template_code,
        component_ref=component_ref,
    ):
        return True
    if is_mapping_only_row(provenance=provenance, status=status, component_ref=component_ref):
        return False
    segment_key = segment_key_from_component_ref(component_ref)
    if not segment_key:
        return False
    return _text(component_ref) == canonical_face_component_ref(segment_key)


def include_material_in_composed_aggregate(
    *,
    material_code: str,
    component_ref: str | None,
    provenance: str | None,
    status: str | None,
    source_template_code: str | None,
) -> bool:
    if not is_linked_logo_template_row(
        source_template_code=source_template_code,
        component_ref=component_ref,
    ):
        return True
    if is_mapping_only_row(provenance=provenance, status=status, component_ref=component_ref):
        return False
    if material_code in LOGO_ARTWORK_MATERIAL_CODES:
        return is_canonical_logo_artwork_material_row(
            material_code=material_code,
            component_ref=component_ref,
            provenance=provenance,
            status=status,
            source_template_code=source_template_code,
        )
    if material_code in FACE_OWNED_MATERIAL_CODES:
        return is_canonical_logo_face_material_row(
            material_code=material_code,
            component_ref=component_ref,
            provenance=provenance,
            status=status,
            source_template_code=source_template_code,
        )
    if is_mapping_only_row(provenance=provenance, status=status, component_ref=component_ref):
        return False
    return True


def include_operation_in_composed_aggregate(
    *,
    operation_code: str,
    component_ref: str | None,
    provenance: str | None,
    status: str | None,
    source_template_code: str | None,
) -> bool:
    if not is_linked_logo_template_row(
        source_template_code=source_template_code,
        component_ref=component_ref,
    ):
        return True
    if is_mapping_only_row(provenance=provenance, status=status, component_ref=component_ref):
        return False
    if operation_code in LOGO_ARTWORK_OPERATION_CODES:
        return is_canonical_logo_artwork_operation_row(
            operation_code=operation_code,
            component_ref=component_ref,
            provenance=provenance,
            status=status,
            source_template_code=source_template_code,
        )
    if operation_code in FACE_OWNED_OPERATION_CODES:
        return is_canonical_logo_face_operation_row(
            operation_code=operation_code,
            component_ref=component_ref,
            provenance=provenance,
            status=status,
            source_template_code=source_template_code,
        )
    if is_mapping_only_row(provenance=provenance, status=status, component_ref=component_ref):
        return False
    return True
