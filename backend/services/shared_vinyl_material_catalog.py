"""Shared Oracal / vinyl material catalog — ProductSystem foundation.

Owner technical datasheets (internal) + ORAFOL official references.
Templates consume profiles by application, not hardcoded series in forms.

This module does NOT mutate Pricing Registry, Color Registry, or CostEngine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final, Mapping

# Legacy fallback purchase tiers (EUR/m², excl. TVA) — prefer DB via resolve_vinyl_price().
ORACAL_641_OWNER_EUR_PER_M2: Final[float] = 6.5
ORACAL_651_OWNER_EUR_PER_M2: Final[float] = 9.0
ORACAL_8500_OWNER_EUR_PER_M2: Final[float] = 20.0


def resolve_vinyl_price(
    prices: dict[str, float] | None,
    series: str,
) -> float:
    """Resolve vinyl price from DB prices dict, fallback to legacy constants."""
    code_map = {"651": "MAT-ORACAL-651", "641": "MAT-ORACAL-641", "8500": "MAT-ORACAL-8500"}
    fallback_map = {"651": ORACAL_651_OWNER_EUR_PER_M2, "641": ORACAL_641_OWNER_EUR_PER_M2, "8500": ORACAL_8500_OWNER_EUR_PER_M2}
    if prices:
        code = code_map.get(series)
        if code and code in prices:
            return prices[code]
    return fallback_map.get(series, ORACAL_651_OWNER_EUR_PER_M2)

OWNER_ORACAL_PRICE_SOURCE_PREFIX = "intake_v4_owner_oracal"


class VinylMaterialType(StrEnum):
    STANDARD_VINYL = "standard_vinyl"
    PREMIUM_VINYL = "premium_vinyl"
    TRANSLUCENT_VINYL = "translucent_vinyl"
    PRINT_LAMINATE = "print_laminate"


class VinylApplication(StrEnum):
    FACE_LETTERS_STANDARD = "face_letters_standard"
    FACE_LETTERS_PREMIUM = "face_letters_premium"
    PANEL_STANDARD = "panel_standard"
    PANEL_PREMIUM = "panel_premium"
    GENERIC_SHORT_MEDIUM_MARKING = "generic_short_medium_marking"
    GENERIC_OUTDOOR_MARKING = "generic_outdoor_marking"
    RETURN_CANT_VOLUM_WRAPPING = "return_cant_volum_wrapping"
    LIGHTBOX_FACE_TRANSLUCENT = "lightbox_face_translucent"
    BACKLIT_SIGN_FACE = "backlit_sign_face"
    ILLUMINATED_ACRYLIC_FACE = "illuminated_acrylic_face"
    ILLUMINATED_LETTER_FACE = "illuminated_letter_face"


class VinylPaletteSource(StrEnum):
    COLOR_REGISTRY_651 = "color_registry:651"
    COLOR_REGISTRY_8500 = "color_registry:8500"
    SHARED_651_PALETTE = "shared_651_palette_manual_entry"
    MANUAL_ONLY = "manual_only"
    NONE = "none"


class VinylPricingSource(StrEnum):
    OWNER_CONFIRMED_INTERIM = "owner_confirmed_interim"
    PRICING_REGISTRY = "pricing_registry"
    MISSING = "missing"


class VinylDatasheetSource(StrEnum):
    OWNER_UPLOADED_PDF = "owner_uploaded_pdf"
    ORAFOL_OFFICIAL = "orafol_official"


ORACAL_COMMON_APPLICATION_WARNINGS: Final[tuple[str, ...]] = (
    "Surfaces must be clean, dry, and free of dust, grease, and contaminants.",
    "Freshly painted or lacquered surfaces must dry and cure for at least 3 weeks before application.",
    "Compatibility with paints and lacquers must be tested before application.",
    "ORAFOL information is advisory; user must verify material suitability for the specific application.",
)


@dataclass(frozen=True)
class VinylMaterialProfile:
    material_key: str
    brand: str
    series: str
    display_name: str
    technical_name: str
    material_type: VinylMaterialType
    surface: str
    adhesive_type: str
    thickness_micron: int
    release_paper_gsm: int
    application_temperature_min_c: int
    temperature_resistance_min_c: int
    temperature_resistance_max_c: int
    temperature_resistance_substrate: str
    adhesive_power_n_per_25mm: float
    adhesive_power_notes: str | None = None
    shelf_life_years: int = 2
    service_life_years_by_variant: Mapping[str, int] = field(default_factory=dict)
    allowed_applications: frozenset[VinylApplication] = frozenset()
    recommended_templates: frozenset[str] = frozenset()
    palette_source: VinylPaletteSource = VinylPaletteSource.NONE
    price_eur_per_sqm: float | None = None
    pricing_source: VinylPricingSource = VinylPricingSource.MISSING
    stock_material_key: str | None = None
    registry_code: str | None = None
    breakdown_material_code: str | None = None
    technical_datasheet_filename: str | None = None
    official_datasheet_url: str | None = None
    official_product_page_url: str | None = None
    datasheet_sources: frozenset[VinylDatasheetSource] = frozenset()
    notes: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ORACAL_COMMON_APPLICATION_WARNINGS


def _owner_price_source(series: str) -> str:
    return f"{OWNER_ORACAL_PRICE_SOURCE_PREFIX}_{series}"


_ORACAL_641_PROFILE = VinylMaterialProfile(
    material_key="oracal_641",
    brand="Oracal",
    series="641",
    display_name="Oracal 641 — Economy Cal",
    technical_name="ORACAL 641 Economy Cal",
    material_type=VinylMaterialType.STANDARD_VINYL,
    surface="glossy or matt",
    adhesive_type="polyacrylate, permanent",
    thickness_micron=75,
    release_paper_gsm=135,
    application_temperature_min_c=10,
    temperature_resistance_min_c=-40,
    temperature_resistance_max_c=80,
    temperature_resistance_substrate="aluminium",
    adhesive_power_n_per_25mm=16.0,
    adhesive_power_notes="FINAT TM 1, after 24h, stainless steel",
    shelf_life_years=2,
    service_life_years_by_variant={
        "black_white": 4,
        "transparent_coloured": 3,
        "metallic": 3,
    },
    allowed_applications=frozenset(
        {
            VinylApplication.FACE_LETTERS_STANDARD,
            VinylApplication.PANEL_STANDARD,
            VinylApplication.GENERIC_SHORT_MEDIUM_MARKING,
        }
    ),
    recommended_templates=frozenset({"TPL-VOLUMETRIC-LETTERS", "TPL-CNC-CUTTING-SERVICE"}),
    palette_source=VinylPaletteSource.SHARED_651_PALETTE,
    price_eur_per_sqm=ORACAL_641_OWNER_EUR_PER_M2,
    pricing_source=VinylPricingSource.OWNER_CONFIRMED_INTERIM,
    stock_material_key=None,
    registry_code="MAT_ORACAL_641",
    breakdown_material_code="MAT-ORACAL-641",
    technical_datasheet_filename="fisa-tehnica-d-ORACAL641.pdf",
    official_datasheet_url=(
        "https://www.orafol.com/products/europe/en/technical-data-sheet/"
        "oracal-641-economy-cal-3550-technical-data-sheet-europe-en.pdf"
    ),
    official_product_page_url="https://www.orafol.com/en/europe/products/oracal-641-economy-cal",
    datasheet_sources=frozenset({VinylDatasheetSource.OWNER_UPLOADED_PDF, VinylDatasheetSource.ORAFOL_OFFICIAL}),
    notes=(
        "Soft PVC film for short/medium-term outdoor markings, inscriptions, decorations.",
        "641 pricing must not be calculated as 651.",
        "UI may reuse 651 color palette for picker; manual code entry when 641 not in color registry.",
    ),
)

_ORACAL_651_PROFILE = VinylMaterialProfile(
    material_key="oracal_651",
    brand="Oracal",
    series="651",
    display_name="Oracal 651 — Intermediate Cal",
    technical_name="ORACAL 651 Intermediate Cal",
    material_type=VinylMaterialType.PREMIUM_VINYL,
    surface="glossy or matt",
    adhesive_type="solvent polyacrylate, permanent",
    thickness_micron=70,
    release_paper_gsm=137,
    application_temperature_min_c=8,
    temperature_resistance_min_c=-40,
    temperature_resistance_max_c=80,
    temperature_resistance_substrate="aluminium",
    adhesive_power_n_per_25mm=18.0,
    adhesive_power_notes="FINAT TM 1, after 24h, stainless steel",
    shelf_life_years=2,
    service_life_years_by_variant={
        "black_white": 5,
        "transparent_coloured_metallic": 4,
        "brilliant_blue": 3,
    },
    allowed_applications=frozenset(
        {
            VinylApplication.FACE_LETTERS_PREMIUM,
            VinylApplication.RETURN_CANT_VOLUM_WRAPPING,
            VinylApplication.PANEL_PREMIUM,
            VinylApplication.GENERIC_OUTDOOR_MARKING,
        }
    ),
    recommended_templates=frozenset(
        {"TPL-VOLUMETRIC-LETTERS", "TPL-LIGHTBOX", "TPL-CNC-CUTTING-SERVICE"}
    ),
    palette_source=VinylPaletteSource.COLOR_REGISTRY_651,
    price_eur_per_sqm=ORACAL_651_OWNER_EUR_PER_M2,
    pricing_source=VinylPricingSource.OWNER_CONFIRMED_INTERIM,
    stock_material_key=None,
    registry_code="MAT_ORACAL_651",
    breakdown_material_code="MAT-ORACAL-651",
    technical_datasheet_filename="fisa-tehnica-d-ORACAL651.pdf",
    official_datasheet_url=(
        "https://www.orafol.com/products/europe/en/technical-data-sheet/"
        "oracal-651-intermediate-cal-id3534-technical-data-sheet-europe-en.pdf"
    ),
    official_product_page_url="https://www.orafol.com/en/europe/products/oracal-651-intermediate-cal",
    datasheet_sources=frozenset({VinylDatasheetSource.OWNER_UPLOADED_PDF, VinylDatasheetSource.ORAFOL_OFFICIAL}),
    notes=(
        "Blended polymeric PVC for outdoor markings; glossy suitable for thermal transfer (resin ribbons).",
        "German General Type Approval ABG D5292 acc. §22a StVZO.",
        "Default Oracal for return/cant volum wrapping (oracal_wrapped).",
        "651 must not be priced as 8500.",
    ),
)

_ORACAL_8500_PROFILE = VinylMaterialProfile(
    material_key="oracal_8500",
    brand="Oracal",
    series="8500",
    display_name="Oracal 8500 — Translucent Cal",
    technical_name="ORACAL 8500 Translucent Cal",
    material_type=VinylMaterialType.TRANSLUCENT_VINYL,
    surface="reduced gloss / semi-gloss translucent",
    adhesive_type="solvent polyacrylate, permanent",
    thickness_micron=80,
    release_paper_gsm=137,
    application_temperature_min_c=8,
    temperature_resistance_min_c=-40,
    temperature_resistance_max_c=90,
    temperature_resistance_substrate="acrylic glass",
    adhesive_power_n_per_25mm=18.0,
    adhesive_power_notes="18 N/25 mm on glass; 16 N/25 mm on acrylic glass (FINAT TM 1, after 24h)",
    shelf_life_years=2,
    service_life_years_by_variant={
        "black_white": 7,
        "coloured": 7,
        "metallic": 5,
    },
    allowed_applications=frozenset(
        {
            VinylApplication.LIGHTBOX_FACE_TRANSLUCENT,
            VinylApplication.BACKLIT_SIGN_FACE,
            VinylApplication.ILLUMINATED_ACRYLIC_FACE,
            VinylApplication.ILLUMINATED_LETTER_FACE,
        }
    ),
    recommended_templates=frozenset({"TPL-VOLUMETRIC-LETTERS", "TPL-LIGHTBOX"}),
    palette_source=VinylPaletteSource.COLOR_REGISTRY_8500,
    price_eur_per_sqm=ORACAL_8500_OWNER_EUR_PER_M2,
    pricing_source=VinylPricingSource.OWNER_CONFIRMED_INTERIM,
    stock_material_key=None,
    registry_code="MAT_ORACAL_8500_TRANSLUCENT",
    breakdown_material_code="MAT-ORACAL-8500",
    technical_datasheet_filename="fisa-tehnica-d-ORACAL8500.pdf",
    official_datasheet_url=(
        "https://www.orafol.com/products/europe/en/technical-data-sheet/"
        "oracal-8500-translucent-cal-3710-technical-data-sheet-europe-en.pdf"
    ),
    official_product_page_url="https://www.orafol.com/en/europe/products/oracal-8500-translucent-cal",
    datasheet_sources=frozenset({VinylDatasheetSource.OWNER_UPLOADED_PDF, VinylDatasheetSource.ORAFOL_OFFICIAL}),
    notes=(
        "Translucent PVC for backlit signs and internally illuminated faces on acrylic, glass, banner.",
        "8500 must not be priced as 651.",
        "Preferred for translucent / illuminated applications.",
    ),
)

_ORACAL_PROFILES_BY_SERIES: Final[dict[str, VinylMaterialProfile]] = {
    "641": _ORACAL_641_PROFILE,
    "651": _ORACAL_651_PROFILE,
    "8500": _ORACAL_8500_PROFILE,
}

_ORACAL_PROFILES_BY_KEY: Final[dict[str, VinylMaterialProfile]] = {
    p.material_key: p for p in _ORACAL_PROFILES_BY_SERIES.values()
}

_FACE_FINISH_TO_SERIES: Final[dict[str, str]] = {
    "oracal_641": "641",
    "641": "641",
    "oracal_651": "651",
    "oracal": "651",
    "651": "651",
    "oracal_8500": "8500",
    "8500": "8500",
}


def list_oracal_vinyl_profiles() -> tuple[VinylMaterialProfile, ...]:
    return tuple(_ORACAL_PROFILES_BY_SERIES.values())


def get_oracal_profile_by_series(series: str | None) -> VinylMaterialProfile | None:
    token = str(series or "").strip()
    if not token:
        return None
    return _ORACAL_PROFILES_BY_SERIES.get(token)


def get_vinyl_material_profile(material_key_or_series: str | None) -> VinylMaterialProfile | None:
    token = str(material_key_or_series or "").strip().lower()
    if not token:
        return None
    if token in _ORACAL_PROFILES_BY_KEY:
        return _ORACAL_PROFILES_BY_KEY[token]
    if token in _ORACAL_PROFILES_BY_SERIES:
        return _ORACAL_PROFILES_BY_SERIES[token]
    return None


def resolve_oracal_series_from_face_finish(face_finish: str | None) -> str | None:
    token = str(face_finish or "").strip().lower()
    return _FACE_FINISH_TO_SERIES.get(token)


def resolve_oracal_profile_from_face_finish(face_finish: str | None) -> VinylMaterialProfile | None:
    series = resolve_oracal_series_from_face_finish(face_finish)
    if series is None:
        return None
    return get_oracal_profile_by_series(series)


def resolve_owner_oracal_price_eur_per_sqm(series: str) -> tuple[float, str, str] | None:
    """Return (price, currency, price_source_key) for owner-confirmed Oracal tiers."""
    profile = get_oracal_profile_by_series(series)
    if profile is None or profile.price_eur_per_sqm is None:
        return None
    if profile.pricing_source != VinylPricingSource.OWNER_CONFIRMED_INTERIM:
        return None
    return (float(profile.price_eur_per_sqm), "EUR", _owner_price_source(profile.series))


def is_vinyl_application_allowed(series: str, application: VinylApplication | str) -> bool:
    profile = get_oracal_profile_by_series(series)
    if profile is None:
        return False
    try:
        app = VinylApplication(application)
    except ValueError:
        return False
    return app in profile.allowed_applications


def profiles_for_vinyl_application(application: VinylApplication | str) -> tuple[VinylMaterialProfile, ...]:
    try:
        app = VinylApplication(application)
    except ValueError:
        return ()
    return tuple(p for p in list_oracal_vinyl_profiles() if app in p.allowed_applications)
