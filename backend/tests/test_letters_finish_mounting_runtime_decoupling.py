"""Runtime decoupling proofs — map narrowing, leakage, legacy expand, snapshot versions."""

from __future__ import annotations

from data.offer_scope_canonical_map import CANONICAL_TO_RUNTIME, runtime_modules_for_canonical
from schemas.active_scope_snapshot import (
    ACTIVE_SCOPE_SNAPSHOT_VERSION,
    ACTIVE_SCOPE_SNAPSHOT_VERSION_V1,
    ACTIVE_SCOPE_SNAPSHOT_VERSION_V2,
    KNOWN_ACTIVE_SCOPE_SNAPSHOT_VERSIONS,
)
from services.execution_sold_scope_reader_service import (
    EXECUTION_PRICED_OP_RUNTIME_ALIASES,
    _normalize_sold_runtime_modules,
)
from services.letters_finish_mounting_runtime_decoupling import (
    LEGACY_FINISAJE_AGGREGATE_ALIAS,
    expand_legacy_finisaje_runtime_modules,
    full_letters_composition_modules,
    mounting_template_enabled,
)


def test_mounting_map_excludes_surface_finish_and_packaging():
    mounting = runtime_modules_for_canonical(["MOUNTING"])
    assert mounting == {"structura_suport", "sablon_montaj"}
    assert "finisaje" not in mounting
    assert "ambalare_livrare_montaj" not in mounting
    assert CANONICAL_TO_RUNTIME["FINISH"] == frozenset({"finisaje"})


def test_full_letters_composition_activates_packaging_not_via_mounting():
    comps = full_letters_composition_modules(finish={"mounting_template_enabled": False})
    assert "finisaje" in comps
    assert "ambalare_livrare_montaj" in comps
    assert "sablon_montaj" not in comps
    comps_tpl = full_letters_composition_modules(finish={"mounting_template_enabled": True})
    assert "sablon_montaj" in comps_tpl


def test_template_enabled_helper():
    assert mounting_template_enabled({"mounting_template_enabled": True}) is True
    assert mounting_template_enabled({"mounting_template_enabled": False}) is False
    assert mounting_template_enabled({}) is False


def test_legacy_finisaje_expand_covers_template_and_packaging():
    expanded = expand_legacy_finisaje_runtime_modules({"finisaje", "debitare_fata"})
    assert LEGACY_FINISAJE_AGGREGATE_ALIAS <= expanded
    assert "debitare_fata" in expanded


def test_snapshot_writer_is_v2_and_readers_know_v1():
    assert ACTIVE_SCOPE_SNAPSHOT_VERSION == ACTIVE_SCOPE_SNAPSHOT_VERSION_V2
    assert ACTIVE_SCOPE_SNAPSHOT_VERSION_V1 in KNOWN_ACTIVE_SCOPE_SNAPSHOT_VERSIONS
    assert ACTIVE_SCOPE_SNAPSHOT_VERSION_V2 in KNOWN_ACTIVE_SCOPE_SNAPSHOT_VERSIONS


def test_execution_normalize_expands_v1_finisaje_only():
    v1 = _normalize_sold_runtime_modules(
        frozenset({"finisaje"}),
        snapshot_version=ACTIVE_SCOPE_SNAPSHOT_VERSION_V1,
    )
    assert "sablon_montaj" in v1
    assert "ambalare_livrare_montaj" in v1

    v2_precise = _normalize_sold_runtime_modules(
        frozenset({"finisaje"}),
        snapshot_version=ACTIVE_SCOPE_SNAPSHOT_VERSION_V2,
    )
    # v2 with only finisaje and no split codes still expands for safety on mixed freeze.
    assert "sablon_montaj" in v2_precise

    v2_split = _normalize_sold_runtime_modules(
        frozenset({"finisaje", "sablon_montaj"}),
        snapshot_version=ACTIVE_SCOPE_SNAPSHOT_VERSION_V2,
    )
    assert v2_split == frozenset({"finisaje", "sablon_montaj"})


def test_execution_op_aliases_are_precise():
    assert EXECUTION_PRICED_OP_RUNTIME_ALIASES["painting"] == "finisaje"
    assert EXECUTION_PRICED_OP_RUNTIME_ALIASES["mounting_template_cnc_cut"] == "sablon_montaj"
    assert EXECUTION_PRICED_OP_RUNTIME_ALIASES["packaging_letters"] == "ambalare_livrare_montaj"
