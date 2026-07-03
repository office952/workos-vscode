"""Tests for shared Oracal vinyl material catalog foundation."""

from __future__ import annotations

from services.intake_v4_oracal_face_pricing_service import (
    INTAKE_V4_ORACAL_641_EUR_PER_M2,
    INTAKE_V4_ORACAL_651_EUR_PER_M2,
    INTAKE_V4_ORACAL_8500_EUR_PER_M2,
    resolve_intake_v4_owner_oracal_face_price,
    resolve_intake_v4_oracal_profile_for_face_finish,
)
from services.shared_vinyl_material_catalog import (
    ORACAL_641_OWNER_EUR_PER_M2,
    ORACAL_651_OWNER_EUR_PER_M2,
    ORACAL_8500_OWNER_EUR_PER_M2,
    VinylApplication,
    get_oracal_profile_by_series,
    get_vinyl_material_profile,
    is_vinyl_application_allowed,
    list_oracal_vinyl_profiles,
    profiles_for_vinyl_application,
    resolve_owner_oracal_price_eur_per_sqm,
)


def test_list_oracal_profiles_returns_641_651_8500() -> None:
    profiles = list_oracal_vinyl_profiles()
    series = {p.series for p in profiles}
    assert series == {"641", "651", "8500"}


def test_oracal_641_profile_metadata() -> None:
    profile = get_oracal_profile_by_series("641")
    assert profile is not None
    assert profile.material_key == "oracal_641"
    assert profile.thickness_micron == 75
    assert profile.application_temperature_min_c == 10
    assert profile.price_eur_per_sqm == 6.5
    assert profile.official_product_page_url is not None
    assert "orafol.com" in profile.official_product_page_url


def test_oracal_651_profile_metadata() -> None:
    profile = get_oracal_profile_by_series("651")
    assert profile is not None
    assert profile.thickness_micron == 70
    assert profile.application_temperature_min_c == 8
    assert profile.price_eur_per_sqm == 9.0


def test_oracal_8500_profile_metadata() -> None:
    profile = get_oracal_profile_by_series("8500")
    assert profile is not None
    assert profile.thickness_micron == 80
    assert profile.application_temperature_min_c == 8
    assert profile.price_eur_per_sqm == 20.0


def test_owner_prices_centralized() -> None:
    assert ORACAL_641_OWNER_EUR_PER_M2 == 6.5
    assert ORACAL_651_OWNER_EUR_PER_M2 == 9.0
    assert ORACAL_8500_OWNER_EUR_PER_M2 == 20.0


def test_resolve_owner_price_tuple() -> None:
    price_651 = resolve_owner_oracal_price_eur_per_sqm("651")
    assert price_651 == (9.0, "EUR", "intake_v4_owner_oracal_651")


def test_8500_allowed_for_backlit_applications() -> None:
    for app in (
        VinylApplication.LIGHTBOX_FACE_TRANSLUCENT,
        VinylApplication.BACKLIT_SIGN_FACE,
        VinylApplication.ILLUMINATED_ACRYLIC_FACE,
        VinylApplication.ILLUMINATED_LETTER_FACE,
    ):
        assert is_vinyl_application_allowed("8500", app)


def test_651_allowed_for_return_cant_wrapping() -> None:
    assert is_vinyl_application_allowed("651", VinylApplication.RETURN_CANT_VOLUM_WRAPPING)


def test_641_not_allowed_for_backlit() -> None:
    assert not is_vinyl_application_allowed("641", VinylApplication.BACKLIT_SIGN_FACE)


def test_unknown_series_fails_closed() -> None:
    assert get_oracal_profile_by_series("999") is None
    assert get_vinyl_material_profile("oracal_999") is None
    assert resolve_owner_oracal_price_eur_per_sqm("999") is None


def test_profiles_for_application_8500_backlit() -> None:
    profiles = profiles_for_vinyl_application(VinylApplication.BACKLIT_SIGN_FACE)
    assert len(profiles) == 1
    assert profiles[0].series == "8500"


def test_intake_v4_pricing_adapter_preserves_prices() -> None:
    assert INTAKE_V4_ORACAL_641_EUR_PER_M2 == 6.5
    assert INTAKE_V4_ORACAL_651_EUR_PER_M2 == 9.0
    assert INTAKE_V4_ORACAL_8500_EUR_PER_M2 == 20.0
    assert resolve_intake_v4_owner_oracal_face_price("641") == (6.5, "EUR", "intake_v4_owner_oracal_641")
    assert resolve_intake_v4_owner_oracal_face_price("8500") == (20.0, "EUR", "intake_v4_owner_oracal_8500")


def test_intake_v4_face_finish_profile_adapter() -> None:
    profile = resolve_intake_v4_oracal_profile_for_face_finish("oracal_8500")
    assert profile is not None
    assert profile.series == "8500"
    assert profile.price_eur_per_sqm == 20.0
