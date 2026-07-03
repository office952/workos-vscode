from __future__ import annotations

from services.template_architecture_scope import (
    OWNER_VALID_EXECUTION_RUNTIME_TEMPLATE_CODES,
    OWNER_VALID_QUOTE_RUNTIME_TEMPLATE_CODES,
    STRUCTURE_PREMOUNT_TEMPLATE_CODE,
    VOLUMETRIC_V2_TEMPLATE_CODE,
    resolve_runtime_template_code,
    template_matches_runtime_scope,
)


def test_resolve_runtime_template_code_maps_svg_analyzer_alias_to_v2() -> None:
    assert resolve_runtime_template_code("TPL-VOLUMETRIC-LETTERS") == VOLUMETRIC_V2_TEMPLATE_CODE.upper()
    assert resolve_runtime_template_code("tpl-volumetric-letters_v2") == VOLUMETRIC_V2_TEMPLATE_CODE.upper()


def test_quote_scope_accepts_svg_analyzer_alias_but_not_structure_template() -> None:
    assert template_matches_runtime_scope(
        "TPL-VOLUMETRIC-LETTERS",
        OWNER_VALID_QUOTE_RUNTIME_TEMPLATE_CODES,
    )
    assert not template_matches_runtime_scope(
        STRUCTURE_PREMOUNT_TEMPLATE_CODE,
        OWNER_VALID_QUOTE_RUNTIME_TEMPLATE_CODES,
    )


def test_execution_scope_keeps_structure_template_available() -> None:
    assert template_matches_runtime_scope(
        STRUCTURE_PREMOUNT_TEMPLATE_CODE,
        OWNER_VALID_EXECUTION_RUNTIME_TEMPLATE_CODES,
    )