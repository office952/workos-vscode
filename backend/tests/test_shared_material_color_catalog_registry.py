from __future__ import annotations

import inspect

from services.shared_material_color_catalog_registry import (
    build_inventory_key_preview,
    get_compatible_cnc_operations,
    get_material_variant,
    is_cnc_processable,
    list_material_series,
    list_material_variants,
    resolve_oracal_variant,
    resolve_ral_variant,
)
import services.shared_material_color_catalog_registry as registry_module


def test_registry_contains_oracal_641_651_8500() -> None:
    codes = {item.series_code for item in list_material_series()}

    assert {"ORACAL_641", "ORACAL_651", "ORACAL_8500"}.issubset(codes)


def test_oracal_641_white_and_651_white_are_distinct_variants() -> None:
    var_641 = resolve_oracal_variant("641", "WHITE")
    var_651 = resolve_oracal_variant("651", "WHITE")

    assert var_641 is not None
    assert var_651 is not None
    assert var_641.material_variant_code == "ORACAL_641_WHITE"
    assert var_651.material_variant_code == "ORACAL_651_WHITE"
    assert var_641.material_variant_code != var_651.material_variant_code


def test_oracal_8500_white_resolves_to_translucent_variant() -> None:
    variant = resolve_oracal_variant("8500", "WHITE")

    assert variant is not None
    assert variant.material_variant_code == "ORACAL_8500_WHITE_TRANSLUCENT"
    assert variant.family_code == "TRANSLUCENT_VINYL"
    assert variant.finish_surface == "translucent"


def test_unknown_oracal_color_resolves_to_unknown_variant() -> None:
    variant = resolve_oracal_variant("651", None)

    assert variant is not None
    assert variant.material_variant_code == "ORACAL_651_UNKNOWN"


def test_ral_9005_matte_resolves_to_paint_variant() -> None:
    variant = resolve_ral_variant("9005", "matte")

    assert variant is not None
    assert variant.material_variant_code == "RAL_9005_MATTE_PAINT"


def test_ral_is_not_vinyl() -> None:
    variant = resolve_ral_variant("7016", "matte")

    assert variant is not None
    assert variant.family_code == "PAINT"
    assert variant.series_code == "RAL_PAINT"
    assert variant.family_code != "VINYL"
    assert not variant.series_code.startswith("ORACAL")


def test_inventory_key_preview_rules() -> None:
    oracal_pending = build_inventory_key_preview("ORACAL_651_WHITE")
    oracal_roll = build_inventory_key_preview("ORACAL_651_WHITE", roll_id="ROLL-42")
    plexi_pending = build_inventory_key_preview("PLEXIGLAS_3MM_OPAL")

    assert oracal_pending.preview_key == "ORACAL_651_WHITE::ROLL_PENDING"
    assert oracal_pending.stock_identity_status == "roll_pending"
    assert oracal_roll.preview_key == "ORACAL_651_WHITE::ROLL::ROLL-42"
    assert oracal_roll.stock_identity_status == "roll_assigned"
    assert plexi_pending.preview_key == "PLEXIGLAS_3MM_OPAL::BATCH_PENDING"
    assert plexi_pending.stock_identity_status == "batch_pending"


def test_cnc_hooks_are_exposed_for_processable_variants() -> None:
    assert is_cnc_processable("PLEXIGLAS_3MM_OPAL") is True
    assert "CNC_CUT_PLEXIGLAS_3MM" in get_compatible_cnc_operations("PLEXIGLAS_3MM_OPAL")
    assert "CANAL_PLAT_GHIDAJ" in get_compatible_cnc_operations("PLEXIGLAS_3MM_OPAL")
    assert is_cnc_processable("FOREX_10MM_WHITE") is True
    assert "CNC_FLAT_RECESS_FOREX_BACK_SEAT" in get_compatible_cnc_operations("FOREX_10MM_WHITE")
    assert is_cnc_processable("ORACAL_651_WHITE") is False
    assert is_cnc_processable("RAL_9005_MATTE_PAINT") is False


def test_no_duplicate_material_variant_code() -> None:
    variants = list_material_variants()
    codes = [item.material_variant_code for item in variants]

    assert len(codes) == len(set(codes))


def test_no_duplicate_inventory_key_base_for_different_variants() -> None:
    variants = list_material_variants()
    keys = [build_inventory_key_preview(item.material_variant_code).preview_key for item in variants]

    assert len(keys) == len(set(keys))


def test_registry_is_read_only_by_convention() -> None:
    source = inspect.getsource(registry_module)

    assert "sqlalchemy" not in source
    assert "routers." not in source
    assert "seed_" not in source
    assert "alembic" not in source


def test_get_material_variant_returns_expected_variant() -> None:
    variant = get_material_variant("ORACAL_641_BLACK")

    assert variant is not None
    assert variant.material_code == "ORACAL_641"
    assert variant.color_code == "BLACK"