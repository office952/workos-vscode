"""Canonical template variant contract for TPL-VOLUMETRIC-LETTERS_v2.

In-code authority — not dossier-backed. Promoted from FALLBACK_DOSSIER_VARIANTS.
"""

from __future__ import annotations

from typing import Any

RETURN_DEPTH_ALLOWED = frozenset({30, 60, 80, 100})
PSU_WATTS_ALLOWED = frozenset({60, 100, 160, 200})

CANONICAL_TEMPLATE_VARIANTS_V2: list[dict[str, Any]] = [
    {
        "variant_key": "back_bevel_enabled",
        "name": "Sanfren spate Forex",
        "allowed_values": [False, True],
        "default_value": False,
        "description": "Forex back bevel option owned by the volumetric template.",
    },
    {
        "variant_key": "face_finish_type",
        "name": "Finisaj fata plexi",
        "allowed_values": [
            "none",
            "oracal_651",
            "oracal_641",
            "oracal_8500",
            "printed_vinyl",
            "printed_laminated_vinyl",
        ],
        "default_value": "none",
        "description": "Canonical face finish variants from template contract.",
    },
    {
        "variant_key": "mounting_template_enabled",
        "name": "Sablon montaj Forex",
        "allowed_values": [True, False],
        "default_value": True,
        "description": "Template-owned mounting template decision.",
    },
    {
        "variant_key": "mounting_system",
        "name": "Sistem montaj / premontaj",
        "allowed_values": ["direct_wall", "steel_bars", "aluminum_bars", "acm_panel"],
        "default_value": "direct_wall",
        "description": "Template-owned mounting system decision.",
    },
    {
        "variant_key": "mounting_bar_profile",
        "name": "Profil bare premontaj",
        "allowed_values": ["30x30x1.5"],
        "default_value": "30x30x1.5",
        "description": "Template-owned mounting bar profile.",
    },
    {
        "variant_key": "return_depth_mm",
        "name": "Adancime cant / profil lateral",
        "allowed_values": sorted(RETURN_DEPTH_ALLOWED),
        "default_value": 60,
        "description": "Variant-priced return profile depth.",
    },
    {
        "variant_key": "selected_psu_watts",
        "name": "Putere sursa LED",
        "allowed_values": sorted(PSU_WATTS_ALLOWED),
        "default_value": 100,
        "description": "Single template-owned PSU wattage variant for pricing.",
    },
    {
        "variant_key": "return_finish_type",
        "name": "Finisaj cant / volum",
        "allowed_values": [
            "white_aluminum",
            "black_aluminum",
            "gold_aluminum",
            "mirror_silver",
            "ral_paint",
            "oracal_wrapped",
        ],
        "default_value": "white_aluminum",
        "description": "Cant/return finish material.",
    },
    {
        "variant_key": "lighting_system_type",
        "name": "Sistem iluminare LED",
        "allowed_values": ["led_modules", "led_strip"],
        "default_value": "led_modules",
        "description": "LED system type.",
    },
    {
        "variant_key": "light_color",
        "name": "Culoare lumina LED",
        "allowed_values": ["warm", "neutral", "cool"],
        "default_value": "warm",
        "description": "LED light color temperature.",
    },
    {
        "variant_key": "led_module_power_w",
        "name": "Putere modul LED",
        "allowed_values": [0.75, 1.0, 1.44],
        "default_value": 0.75,
        "description": "LED module wattage for power/PSU sizing.",
    },
    {
        "variant_key": "mounting_template_material_type",
        "name": "Material sablon montaj",
        "allowed_values": ["forex", "paper"],
        "default_value": "forex",
        "description": "Mounting template material.",
    },
    {
        "variant_key": "face_vinyl_roll_width_mm",
        "name": "Latime rola vinyl fata",
        "allowed_values": [1000, 1260],
        "default_value": 1000,
        "description": "Vinyl roll width for face finish application.",
    },
    {
        "variant_key": "emblem_lighting_mode",
        "name": "Mod iluminare emblema",
        "allowed_values": ["area_lit", "excluded"],
        "default_value": "area_lit",
        "description": "Emblem lighting mode.",
    },
]
